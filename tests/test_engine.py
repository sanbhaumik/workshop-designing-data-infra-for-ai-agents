"""Engine-level tests: models, store, frozen LLM/embeddings, scheduler, agent,
tracer, and the state-contamination determinism guarantee (fires 20/20 runs).
"""
from pathlib import Path

import numpy as np
import pytest

from nova.agent import Agent, SharedState, format_summary, load_document, summary_prompt
from nova.embeddings import EmbeddingMissing, embed, search
from nova.frozen_llm import FixtureMissing, FrozenLLM
from nova.models import ClientDocument, Summary, TraceEvent
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
    summary = Summary(client_id="alpha", content="hello")
    evt = TraceEvent(run_id="r1", step="read", data={"k": "v"})
    assert doc.client_id == "alpha"
    assert summary.content == "hello"
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


def test_store_set_summary_is_last_write_wins(tmp_path):
    store = RecordStore(tmp_path / "engine.db")
    store.init_schema()
    store.set_summary("alpha", "first")
    store.set_summary("alpha", "second")
    summary = store.get_summary("alpha")
    assert summary["content"] == "second"
    assert summary["version"] == 2


# ---------------------------------------------------------------------------
# frozen_llm
# ---------------------------------------------------------------------------


def test_frozen_llm_returns_known_response():
    llm = FrozenLLM(FIXTURES / "llm_responses")
    doc = load_document("alpha", "account_note.md")
    response = llm.complete(summary_prompt("alpha", doc))
    assert len(response) > 10


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

    scheduler = Scheduler(["A:checkpoint1", "B:checkpoint1", "A:checkpoint2", "B:checkpoint2"])
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


def test_agent_run_produces_deterministic_summary(tmp_path):
    agent, _ = _build_agent(tmp_path, "agent_run")
    summary = agent.run("alpha", "run-1")
    doc = load_document("alpha", "account_note.md")
    expected = format_summary("alpha", agent.llm.complete(summary_prompt("alpha", doc)))
    assert summary.client_id == "alpha"
    assert summary.content == expected


def test_tracer_records_all_three_steps(tmp_path):
    agent, _ = _build_agent(tmp_path, "agent_trace")
    agent.run("alpha", "run-1")
    events = agent.tracer.dump()
    steps = [e.step for e in events]
    assert steps == ["read", "reason", "save"]
    assert all(e.run_id == "run-1" for e in events)


# ---------------------------------------------------------------------------
# determinism: the cross-tenant leak must fire on 100% of runs
# ---------------------------------------------------------------------------

CONTAMINATION_SCRIPT = ["A:read", "A:reason", "B:read", "B:reason", "A:save", "B:save"]


def _run_contamination(tmp_path, i: int) -> str:
    store = RecordStore(tmp_path / f"state_{i}.db")
    store.init_schema()
    tracer = Tracer(tmp_path / f"state_{i}_trace.jsonl")
    llm = FrozenLLM(FIXTURES / "llm_responses")
    shared_memory = SharedState()
    agent_alpha = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_memory)
    agent_beta = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_memory)

    Scheduler(CONTAMINATION_SCRIPT).run(
        lambda: agent_alpha.run_steps("alpha", "run-a"),
        lambda: agent_beta.run_steps("beta", "run-b"),
    )
    return store.get_summary("alpha")["content"]


def test_state_contamination_is_deterministic_20x(tmp_path):
    contents = [_run_contamination(tmp_path, i) for i in range(20)]
    assert all("beta" in c.lower() for c in contents)  # Alpha's summary always leaks Beta's data
