"""Facilitator tooling: regenerate fixtures/traces/incident_047.json.

Runs the same state-contamination scenario as Module 03's naive_state.py,
with tracing on, and writes the full event trace as a single JSON array so
`modules/04_provenance/walk_trace.py` can walk it.

Run this directly: `python scripts/generate_trace.py`
"""
import json
import sys
import tempfile
from pathlib import Path

# Make `nova` importable when run directly (e.g. `python scripts/generate_trace.py`).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nova.agent import Agent, SharedState
from nova.frozen_llm import FrozenLLM
from nova.scheduler import Scheduler
from nova.store import RecordStore
from nova.trace import Tracer

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"
TRACE_PATH = FIXTURES / "traces" / "incident_047.json"

CONTAMINATION_SCRIPT = ["A:read", "A:reason", "B:read", "B:reason", "A:save", "B:save"]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        store = RecordStore(Path(tmp) / "trace_gen.db")
        store.init_schema()
        tracer = Tracer(Path(tmp) / "incident_047_raw.jsonl")

        shared_state = SharedState()
        llm = FrozenLLM(FIXTURES / "llm_responses")
        agent_alpha = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_state)
        agent_beta = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_state)

        Scheduler(CONTAMINATION_SCRIPT).run(
            lambda: agent_alpha.run_steps("alpha", "run-047-a"),
            lambda: agent_beta.run_steps("beta", "run-047-b"),
        )

        events = [e.model_dump() for e in tracer.dump()]

    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRACE_PATH.write_text(json.dumps(events, indent=2))
    print(f"wrote {len(events)} events to {TRACE_PATH}")


if __name__ == "__main__":
    main()
