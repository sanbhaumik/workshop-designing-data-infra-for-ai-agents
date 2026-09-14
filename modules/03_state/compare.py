"""Module 03 — State, Memory & Recovery: the before/after reveal.

Runs TWO scenarios against Alpha's account summary, with the shipped naive key
and with YOUR state_key:

  Live      — Alpha and Beta run at the same time, sharing one MemoryStore.
  Recovery  — Alpha crashes mid-run; Beta reuses the same attempt id; Alpha
              resumes from its checkpoint.

A key that survives the Live column can still leak in the Recovery column. That
gap is the whole point of the lab.

Uses the real model (NOVA_LLM) and real database (DATABASE_URL); the shared
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

from nova.agent import Agent, MemoryStore
from nova.cli import run_guarded, truncate
from nova.llm import get_llm
from nova.scheduler import Scheduler
from nova.store import get_store
from nova.trace import Tracer
from your_fix import state_key

CONTAMINATION_SCRIPT = ["A:read", "A:reason", "B:read", "B:reason", "A:save", "B:save"]

NAIVE_KEY = lambda run_id, tenant: ""  # the shipped naive: one slot for every run


def run_live(key, llm, store, tmp: Path, name: str) -> str:
    """Two interleaved tenants sharing one MemoryStore; return Alpha's summary."""
    store.reset_demo()
    tracer = Tracer(tmp / f"{name}.jsonl")
    memory = MemoryStore()
    agent_alpha = Agent(store, llm, tracer, memory, key)
    agent_beta = Agent(store, llm, tracer, memory, key)
    Scheduler(CONTAMINATION_SCRIPT).run(
        lambda: agent_alpha.run_steps("alpha", "run-a"),
        lambda: agent_beta.run_steps("beta", "run-b"),
    )
    return store.get_summary("alpha").get("content") or ""


def run_recovery(key, llm, store, tmp: Path, name: str) -> str:
    """Alpha crashes after reasoning; Beta reuses the attempt id; Alpha resumes."""
    store.reset_demo()
    tracer = Tracer(tmp / f"{name}.jsonl")
    memory = MemoryStore()
    agent_alpha = Agent(store, llm, tracer, memory, key)
    agent_beta = Agent(store, llm, tracer, memory, key)
    reused_id = "slot-1"

    alpha_run = agent_alpha.run_steps("alpha", reused_id)
    for step in alpha_run:
        if step == "reason":
            break  # crash before save
    agent_beta.run("beta", reused_id)
    agent_alpha.save_from_checkpoint("alpha", reused_id)
    return store.get_summary("alpha").get("content") or ""


def _clean(summary: str) -> bool:
    return "beta" not in summary.lower() and "alpha" in summary.lower()


def _cell(summary: str) -> str:
    return "[green]clean[/green]" if _clean(summary) else "[red]leaks Beta[/red]"


def main() -> None:
    console = Console()
    llm = get_llm()
    store = get_store()
    store.init_schema()

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        naive_live = run_live(NAIVE_KEY, llm, store, tmp, "live_naive")
        naive_rec = run_recovery(NAIVE_KEY, llm, store, tmp, "rec_naive")
        your_live = run_live(state_key, llm, store, tmp, "live_your")
        your_rec = run_recovery(state_key, llm, store, tmp, "rec_your")

    table = Table(title="Tenant Alpha's account summary — does it leak Beta?")
    table.add_column("scenario")
    table.add_column("naive (shipped)")
    table.add_column("your state_key")
    table.add_row("Live — two tenants at once", _cell(naive_live), _cell(your_live))
    table.add_row("Recovery — crash + reused id + resume", _cell(naive_rec), _cell(your_rec))
    console.print(table)
    console.print(f"\nAlpha (your key, recovery): {truncate(your_rec, 70)}")
    console.print()

    if _clean(your_live) and _clean(your_rec):
        console.print(
            "[bold green]✓ Durable.[/bold green] Memory is keyed on the unit of work, so "
            "Alpha finds its own state whether runs overlap live or resume after a crash."
        )
    elif _clean(your_live) and not _clean(your_rec):
        console.print(
            "[bold yellow]Half fixed — this is the trap.[/bold yellow] Isolation holds when "
            "runs are live, but the resumed run loaded another tenant's checkpoint. You keyed "
            "on the ephemeral run/attempt id; key on the UNIT OF WORK (the tenant) instead."
        )
    else:
        console.print(
            "[bold yellow]Not fixed yet.[/bold yellow] Alpha's summary still leaks Beta — "
            "give each unit of work its own memory slot."
        )


if __name__ == "__main__":
    run_guarded(main)
