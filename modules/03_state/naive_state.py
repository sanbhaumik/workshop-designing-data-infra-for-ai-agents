"""Module 03 — State, Memory & Recovery: watch the contamination happen.

Two agent runs for DIFFERENT clients share one naive, unnamespaced state
object. Alpha's run ends up drafting its briefing from state that Beta's run
already overwrote.

Run this directly: `python modules/03_state/naive_state.py`
"""
import tempfile
from pathlib import Path

from rich.console import Console

from nova.agent import Agent, SharedState
from nova.frozen_llm import FrozenLLM
from nova.scheduler import Scheduler
from nova.store import RecordStore
from nova.trace import Tracer

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"

CONTAMINATION_SCRIPT = [
    "A:read", "A:reason", "B:read", "B:reason", "A:write", "A:draft", "B:write", "B:draft",
]


def main() -> None:
    console = Console()
    with tempfile.TemporaryDirectory() as tmp:
        store = RecordStore(Path(tmp) / "naive_state.db")
        store.init_schema()
        tracer = Tracer(Path(tmp) / "naive_state_trace.jsonl")

        shared_state = SharedState()
        llm = FrozenLLM(FIXTURES / "llm_responses")
        agent_alpha = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_state)
        agent_beta = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_state)

        Scheduler(CONTAMINATION_SCRIPT).run(
            lambda: agent_alpha.run_steps("alpha", "run-a"),
            lambda: agent_beta.run_steps("beta", "run-b"),
        )

        alpha = store.get_briefing("alpha")
        beta = store.get_briefing("beta")

    console.print("[bold]Alpha's briefing:[/bold]", alpha.get("content"))
    console.print("[bold]Beta's briefing:[/bold]", beta.get("content"))
    if "beta" in (alpha.get("content") or "").lower():
        console.print(
            "\n[bold red]CORRUPTION: Alpha's briefing contains Beta's data -- "
            "both agent runs shared one mutable state object.[/bold red]"
        )


if __name__ == "__main__":
    main()
