"""Module 03 — State, Memory & Recovery: watch the contamination happen.

Two agent runs for DIFFERENT clients (Alpha and Beta) are interleaved by the
scheduler while sharing ONE mutable state object. You watch, step by step, as
Beta's run overwrites the shared state's client -- and then Alpha's run drafts
its briefing from that contaminated state.

Run this directly: `python modules/03_state/naive_state.py`
"""
import sys
import tempfile
from pathlib import Path

# Make `nova` importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from nova.agent import Agent, SharedState
from nova.frozen_llm import FrozenLLM
from nova.scheduler import Scheduler
from nova.store import RecordStore
from nova.trace import Tracer

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"

# run_id -> the client that run is SUPPOSED to be working on.
RUN_OWNER = {"run-a": "alpha", "run-b": "beta"}

CONTAMINATION_SCRIPT = [
    "A:read", "A:reason", "B:read", "B:reason", "A:write", "A:draft", "B:write", "B:draft",
]


def main() -> None:
    console = Console()
    console.print(
        Panel(
            "The scheduler interleaves two agent runs that SHARE one state object:\n"
            "  run-a works for client 'alpha'   •   run-b works for client 'beta'\n"
            "Watch the 'state.client_id' column — when a run acts on a client that\n"
            "isn't its own, the shared state has been contaminated.",
            title="State contamination — the agent runs interleaved",
        )
    )

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
        events = tracer.dump()

    table = Table(title="Interleaved agent steps (shared state)")
    table.add_column("#")
    table.add_column("run")
    table.add_column("owns client")
    table.add_column("step")
    table.add_column("state.client_id")
    table.add_column("")
    for i, evt in enumerate(events, start=1):
        owner = RUN_OWNER.get(evt.run_id, "?")
        state_client = str(evt.data.get("state_snapshot", {}).get("client_id", ""))
        contaminated = state_client and state_client != owner
        flag = "[red]⚠ reading another client's state[/red]" if contaminated else ""
        row_client = f"[red]{state_client}[/red]" if contaminated else state_client
        table.add_row(str(i), evt.run_id, owner, evt.step, row_client, flag)
    console.print(table)

    briefings = Table(title="Final briefings")
    briefings.add_column("client")
    briefings.add_column("briefing content")
    briefings.add_row("alpha", alpha.get("content") or "")
    briefings.add_row("beta", beta.get("content") or "")
    console.print(briefings)

    if "beta" in (alpha.get("content") or "").lower():
        console.print(
            "\n[bold red]CORRUPTION: Alpha's briefing contains Beta's data. At the "
            "'A:write'/'A:draft' steps above, run-a read a shared state whose client_id "
            "had already been overwritten by run-b.[/bold red]"
        )


if __name__ == "__main__":
    main()
