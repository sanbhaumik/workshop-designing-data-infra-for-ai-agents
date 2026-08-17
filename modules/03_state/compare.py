"""Module 03 — State, Memory & Recovery: the before/after reveal.

Runs both of the lab's scenarios with the naive baseline and with YOUR fix
(whatever your_fix.py currently contains), and prints the results side by side:

  1. Isolation — does Alpha's briefing stay free of Beta's data?
  2. Recovery  — after a crash mid-run and a resume, how many obligations land?

Run this after you've edited your_fix.py:
    `python modules/03_state/compare.py`
"""
import sys
import tempfile
from pathlib import Path

# Make `nova` and this folder's your_fix importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.table import Table

from nova.agent import Agent, SharedState
from nova.frozen_llm import FrozenLLM
from nova.scheduler import Scheduler
from nova.store import RecordStore
from nova.trace import Tracer
from your_fix import IsolatedState, run_recoverable

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"

CONTAMINATION_SCRIPT = [
    "A:read", "A:reason", "B:read", "B:reason", "A:write", "A:draft", "B:write", "B:draft",
]


def _new_agent(tmp: Path, name: str, state) -> tuple[Agent, RecordStore]:
    store = RecordStore(tmp / f"{name}.db")
    store.init_schema()
    tracer = Tracer(tmp / f"{name}.jsonl")
    llm = FrozenLLM(FIXTURES / "llm_responses")
    return Agent(store, llm, FIXTURES / "embeddings", tracer, state), store


# ---------------------------------------------------------------------------
# Scenario 1 — isolation
# ---------------------------------------------------------------------------


def run_isolation(state, tmp: Path, name: str) -> str:
    """Run the two interleaved clients sharing `state`; return Alpha's briefing."""
    llm = FrozenLLM(FIXTURES / "llm_responses")
    store = RecordStore(tmp / f"{name}.db")
    store.init_schema()
    tracer = Tracer(tmp / f"{name}.jsonl")
    agent_alpha = Agent(store, llm, FIXTURES / "embeddings", tracer, state)
    agent_beta = Agent(store, llm, FIXTURES / "embeddings", tracer, state)
    Scheduler(CONTAMINATION_SCRIPT).run(
        lambda: agent_alpha.run_steps("alpha", "run-a"),
        lambda: agent_beta.run_steps("beta", "run-b"),
    )
    return store.get_briefing("alpha").get("content") or ""


# ---------------------------------------------------------------------------
# Scenario 2 — recovery
# ---------------------------------------------------------------------------


def naive_run_recoverable(agent: Agent, client_id: str, run_id: str, kill_after: str | None = None):
    """Baseline: on resume, re-runs the whole agent from scratch (redoing writes)."""
    for checkpoint in agent.run_steps(client_id, run_id):
        if checkpoint == kill_after:
            return None
    return True


def run_recovery(recover_fn, tmp: Path, name: str) -> int:
    """Crash the run after 'write', resume it, and count Alpha's obligations."""
    agent, store = _new_agent(tmp, name, SharedState())
    recover_fn(agent, "alpha", "run-recover", kill_after="write")  # crash
    recover_fn(agent, "alpha", "run-recover")  # resume
    return len(store.get_obligations("alpha"))


def main() -> None:
    console = Console()

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        before_alpha = run_isolation(SharedState(), tmp, "iso_before")
        after_alpha = run_isolation(IsolatedState(), tmp, "iso_after")
        before_obs = run_recovery(naive_run_recoverable, tmp, "rec_before")
        after_obs = run_recovery(run_recoverable, tmp, "rec_after")

    # --- isolation ---
    iso = Table(title="1. Isolation — Alpha's briefing")
    iso.add_column("scenario")
    iso.add_column("Alpha's briefing content")
    iso.add_column("clean?")
    iso.add_row("BEFORE — shared state", before_alpha, "[red]NO — contains Beta[/red]")
    after_clean = "beta" not in after_alpha.lower() and "alpha" in after_alpha.lower()
    iso.add_row(
        "AFTER — your IsolatedState",
        after_alpha,
        "[green]YES[/green]" if after_clean else "[red]NO — contains Beta[/red]",
    )
    console.print(iso)

    # --- recovery ---
    rec = Table(title="2. Recovery — obligations after crash + resume")
    rec.add_column("scenario")
    rec.add_column("obligations for one run")
    rec.add_column("correct?")
    rec.add_row("BEFORE — re-run from scratch", str(before_obs), "[red]NO — duplicated[/red]")
    rec.add_row(
        "AFTER — your run_recoverable",
        str(after_obs),
        "[green]YES[/green]" if after_obs == 1 else "[red]NO — duplicated[/red]",
    )
    console.print(rec)
    console.print()

    if after_clean and after_obs == 1:
        console.print(
            "[bold green]✓ Both fixed.[/bold green] State is namespaced per run "
            "(no cross-client bleed), and a resumed run reuses its checkpoint instead "
            "of redoing the write."
        )
    else:
        todo = []
        if not after_clean:
            todo.append("Task 1: make IsolatedState namespace by run_id")
        if after_obs != 1:
            todo.append("Task 2: make run_recoverable skip work already completed")
        console.print("[bold yellow]Not fully fixed yet.[/bold yellow] " + "  •  ".join(todo))


if __name__ == "__main__":
    main()
