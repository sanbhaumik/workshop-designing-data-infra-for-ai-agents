"""Module 03 — State, Memory & Recovery: the before/after reveal.

Runs the interleaved two-tenant scenario with the naive shared memory and with
YOUR IsolatedState, and shows Alpha's account summary each way. Before: it
contains Beta's data. After: it's clean.

Uses the real model (NOVA_LLM) and real database (DATABASE_URL). The shared
database is reset between phases.

Run this after you've edited your_fix.py:
    `python modules/03_state/compare.py`
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.table import Table

from nova.agent import Agent, SharedState
from nova.cli import run_guarded, truncate
from nova.llm import get_llm
from nova.scheduler import Scheduler
from nova.store import get_store
from nova.trace import Tracer
from your_fix import IsolatedState

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"

CONTAMINATION_SCRIPT = ["A:read", "A:reason", "B:read", "B:reason", "A:save", "B:save"]


def run_isolation(memory, llm, store, tmp: Path, name: str) -> str:
    """Run the two interleaved tenants sharing `memory`; return Alpha's summary."""
    store.reset_demo()
    tracer = Tracer(tmp / f"{name}.jsonl")
    agent_alpha = Agent(store, llm, FIXTURES / "embeddings", tracer, memory)
    agent_beta = Agent(store, llm, FIXTURES / "embeddings", tracer, memory)
    Scheduler(CONTAMINATION_SCRIPT).run(
        lambda: agent_alpha.run_steps("alpha", "run-a"),
        lambda: agent_beta.run_steps("beta", "run-b"),
    )
    return store.get_summary("alpha").get("content") or ""


def main() -> None:
    console = Console()
    llm = get_llm()
    store = get_store()
    store.init_schema()

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        before_alpha = run_isolation(SharedState(), llm, store, tmp, "iso_before")
        after_alpha = run_isolation(IsolatedState(), llm, store, tmp, "iso_after")

    after_clean = "beta" not in after_alpha.lower() and "alpha" in after_alpha.lower()

    table = Table(title="Tenant Alpha's account summary")
    table.add_column("scenario")
    table.add_column("Alpha's summary content")
    table.add_column("clean?")
    table.add_row("BEFORE — shared memory", truncate(before_alpha, 60), "[red]NO — contains Beta[/red]")
    table.add_row(
        "AFTER — your IsolatedState",
        truncate(after_alpha, 60),
        "[green]YES[/green]" if after_clean else "[red]NO — contains Beta[/red]",
    )
    console.print(table)
    console.print()

    if after_clean:
        console.print(
            "[bold green]✓ Fixed.[/bold green] Memory is namespaced per run/tenant, so "
            "Beta's data can no longer bleed into Alpha's summary."
        )
    else:
        console.print(
            "[bold yellow]Not fixed yet.[/bold yellow] Alpha's summary still contains Beta's "
            "data — make IsolatedState give each run_id its own dict."
        )


if __name__ == "__main__":
    run_guarded(main)
