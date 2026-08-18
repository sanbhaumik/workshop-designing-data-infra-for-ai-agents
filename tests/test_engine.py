"""Engine-level tests: models, store, frozen LLM/embeddings, scheduler, agent,
tracer, and the two determinism guarantees (write conflict, state
contamination) each firing on 20/20 runs.
"""
from pathlib import Path

import numpy as np
import pytest

from nova.agent import Agent, SharedState, format_briefing_content
from nova.embeddings import EmbeddingMissing, embed, search
from nova.frozen_llm import FixtureMissing, FrozenLLM
from nova.models import Briefing, ClientDocument, Obligation, TraceEvent
from nova.scheduler import Scheduler
from nova.store import RecordStore
from nova.trace import Tracer

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


# ---------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------


def test_models_construct():
    doc = ClientDocument(client_id="alpha", doc_id="d1", path="fixtures/clients/alpha/x.md")
    ob = Obligation(client_id="alpha", text="do the thing", source_doc="x.md")
    briefing = Briefing(client_id="alpha", content="hello", obligations=[ob])
    evt = TraceEvent(run_id="r1", step="read", data={"k": "v"})
    assert doc.client_id == "alpha"
    assert briefing.obligations[0].text == "do the thing"
    assert evt.step == "read"


# ---------------------------------------------------------------------------
# store
# ---------------------------------------------------------------------------


def test_store_get_client_roundtrip(tmp_path):
    store = RecordStore(tmp_path / "engine.db")
    store.init_schema()
    store.execute("INSERT INTO clients (client_id, name) VALUES (?, ?)", ("alpha", "Alpha Capital"))
    assert store.get_client("alpha") == {"client_id": "alpha", "name": "Alpha Capital"}
    assert store.get_client("nonexistent") == {}


def test_store_append_obligation_is_naive_and_duplicates(tmp_path):
    store = RecordStore(tmp_path / "engine.db")
    store.init_schema()
    ob = Obligation(client_id="alpha", text="file the thing", source_doc="x.md", idempotency_key="k1")
    store.append_obligation(ob)
    store.append_obligation(ob)
    assert len(store.get_obligations("alpha")) == 2  # naive: no dedup


def test_store_set_briefing_is_last_write_wins(tmp_path):
    store = RecordStore(tmp_path / "engine.db")
    store.init_schema()
    store.set_briefing("alpha", "first")
    store.set_briefing("alpha", "second")
    briefing = store.get_briefing("alpha")
    assert briefing["content"] == "second"
    assert briefing["version"] == 2


# ---------------------------------------------------------------------------
# frozen_llm
# ---------------------------------------------------------------------------


def test_frozen_llm_returns_known_response():
    from nova.agent import briefing_prompt, load_document

    llm = FrozenLLM(FIXTURES / "llm_responses")
    doc = load_document("alpha", "engagement_letter.md")
    response = llm.complete(briefing_prompt("alpha", "engagement_letter.md", doc))
    assert "obligation" in response.lower()


def test_frozen_llm_raises_on_unknown_prompt():
    llm = FrozenLLM(FIXTURES / "llm_responses")
    with pytest.raises(FixtureMissing):
        llm.complete("no such prompt has ever been recorded")


# ---------------------------------------------------------------------------
# embeddings
# ---------------------------------------------------------------------------


def test_embed_returns_known_vector():
    vec = embed("alpha docs", FIXTURES / "embeddings")
    assert vec.shape == (4,)


def test_embed_raises_on_unknown_text():
    with pytest.raises(EmbeddingMissing):
        embed("no such text was ever embedded", FIXTURES / "embeddings")


def test_search_returns_best_match_first():
    query = np.array([1.0, 0.0])
    docs = np.array([[0.0, 1.0], [1.0, 0.0], [0.7, 0.7]])
    assert search(query, docs, k=2) == [1, 2]


# ---------------------------------------------------------------------------
# scheduler
# ---------------------------------------------------------------------------


def test_scheduler_follows_script_order():
    order: list[str] = []

    def make_run(label: str):
        def _run():
            order.append(f"{label}:start")
            yield "checkpoint1"
            order.append(f"{label}:mid")
            yield "checkpoint2"
            order.append(f"{label}:end")
            return label

        return _run

    scheduler = Scheduler(
        ["A:checkpoint1", "B:checkpoint1", "A:checkpoint2", "B:checkpoint2"]
    )
    result_a, result_b = scheduler.run(make_run("A"), make_run("B"))

    assert result_a == "A"
    assert result_b == "B"
    assert order == ["A:start", "B:start", "A:mid", "B:mid", "A:end", "B:end"]


# ---------------------------------------------------------------------------
# agent + tracer
# ---------------------------------------------------------------------------


def _build_agent(tmp_path, name: str) -> tuple[Agent, RecordStore]:
    store = RecordStore(tmp_path / f"{name}.db")
    store.init_schema()
    tracer = Tracer(tmp_path / f"{name}_trace.jsonl")
    llm = FrozenLLM(FIXTURES / "llm_responses")
    agent = Agent(store, llm, FIXTURES / "embeddings", tracer, SharedState())
    return agent, store


def test_agent_run_produces_deterministic_briefing(tmp_path):
    from nova.agent import briefing_prompt, load_document

    agent, _ = _build_agent(tmp_path, "agent_run")
    briefing = agent.run("alpha", "run-1")
    doc = load_document("alpha", "engagement_letter.md")
    expected = format_briefing_content("alpha", agent.llm.complete(briefing_prompt("alpha", "engagement_letter.md", doc)))
    assert briefing.client_id == "alpha"
    assert briefing.content == expected
    assert len(briefing.obligations) == 1


def test_tracer_records_all_four_steps(tmp_path):
    agent, _ = _build_agent(tmp_path, "agent_trace")
    agent.run("alpha", "run-1")
    events = agent.tracer.dump()
    steps = [e.step for e in events]
    assert steps == ["read", "reason", "write", "draft"]
    assert all(e.run_id == "run-1" for e in events)


# ---------------------------------------------------------------------------
# determinism: both engineered failures must fire on 100% of runs
# ---------------------------------------------------------------------------

WRITE_CONFLICT_SCRIPT = [
    "A:read", "B:read", "A:reason", "B:reason", "A:write", "B:write", "A:draft", "B:draft",
]

STATE_CONTAMINATION_SCRIPT = [
    "A:read", "A:reason", "B:read", "B:reason", "A:write", "A:draft", "B:write", "B:draft",
]


def _run_write_conflict(tmp_path, i: int) -> int:
    store = RecordStore(tmp_path / f"write_{i}.db")
    store.init_schema()
    tracer = Tracer(tmp_path / f"write_{i}_trace.jsonl")
    llm = FrozenLLM(FIXTURES / "llm_responses")
    agent_a = Agent(store, llm, FIXTURES / "embeddings", tracer, SharedState())
    agent_b = Agent(store, llm, FIXTURES / "embeddings", tracer, SharedState())

    Scheduler(WRITE_CONFLICT_SCRIPT).run(
        lambda: agent_a.run_steps("alpha", "run-a"),
        lambda: agent_b.run_steps("alpha", "run-b"),
    )
    return len(store.get_obligations("alpha"))


def test_write_conflict_is_deterministic_20x(tmp_path):
    counts = [_run_write_conflict(tmp_path, i) for i in range(20)]
    assert counts == [2] * 20  # naive store duplicates the obligation, every time


def _run_state_contamination(tmp_path, i: int) -> str:
    store = RecordStore(tmp_path / f"state_{i}.db")
    store.init_schema()
    tracer = Tracer(tmp_path / f"state_{i}_trace.jsonl")
    llm = FrozenLLM(FIXTURES / "llm_responses")
    shared_state = SharedState()
    agent_alpha = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_state)
    agent_beta = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_state)

    Scheduler(STATE_CONTAMINATION_SCRIPT).run(
        lambda: agent_alpha.run_steps("alpha", "run-a"),
        lambda: agent_beta.run_steps("beta", "run-b"),
    )
    return store.get_briefing("alpha")["content"]


def test_state_contamination_is_deterministic_20x(tmp_path):
    contents = [_run_state_contamination(tmp_path, i) for i in range(20)]
    assert all("beta" in c.lower() for c in contents)  # Alpha's briefing always leaks Beta's data
