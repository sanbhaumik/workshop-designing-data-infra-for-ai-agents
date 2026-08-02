"""Module 02 — Write Problems: watch the corruption happen.

Two agent runs for the SAME client race through the naive record store. The
naive store has no idempotency check, so the same obligation gets written
twice; and no version check, so one run's briefing silently overwrites the
other's.

Run this directly: `python modules/02_write_path/naive.py`
"""
import tempfile
from pathlib import Path

from rich.console import Console
from rich.table import Table

from nova.agent import Agent, SharedState
from nova.frozen_llm import FrozenLLM
from nova.scheduler import Scheduler
from nova.store import RecordStore
from nova.trace import Tracer

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"
CLIENT_ID = "alpha"

CONFLICT_SCRIPT = [
    "A:read", "B:read", "A:reason", "B:reason", "A:write", "B:write", "A:draft", "B:draft",
]


def build_agent(store: RecordStore, tracer: Tracer) -> Agent:
    llm = FrozenLLM(FIXTURES / "llm_responses")
    return Agent(store, llm, FIXTURES / "embeddings", tracer, SharedState())


def main() -> None:
    console = Console()
    with tempfile.TemporaryDirectory() as tmp:
        store = RecordStore(Path(tmp) / "naive_write.db")
        store.init_schema()
        tracer = Tracer(Path(tmp) / "naive_write_trace.jsonl")

        agent_a = build_agent(store, tracer)
        agent_b = build_agent(store, tracer)

        Scheduler(CONFLICT_SCRIPT).run(
            lambda: agent_a.run_steps(CLIENT_ID, "run-a"),
            lambda: agent_b.run_steps(CLIENT_ID, "run-b"),
        )

        obligations = store.get_obligations(CLIENT_ID)
        briefing = store.get_briefing(CLIENT_ID)

    table = Table(title=f"Obligations for '{CLIENT_ID}' after two concurrent runs")
    table.add_column("id")
    table.add_column("text")
    table.add_column("idempotency_key")
    for ob in obligations:
        table.add_row(str(ob.id), ob.text, ob.idempotency_key or "")
    console.print(table)

    console.print(f"\n[bold]{len(obligations)} obligation row(s) written for one true obligation.[/bold]")
    if len(obligations) > 1:
        console.print(
            "[bold red]CORRUPTION: the same obligation was written twice -- "
            "the naive store has no idempotency guard.[/bold red]"
        )

    console.print(f"\n[bold]Final briefing (version {briefing.get('version')}):[/bold] {briefing.get('content')}")
    console.print(
        "[bold red]Only one run's briefing survived -- the other was silently "
        "overwritten (last-write-wins).[/bold red]"
    )


if __name__ == "__main__":
    main()
