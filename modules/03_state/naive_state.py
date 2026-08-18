"""Module 03 — State, Memory & Recovery: watch tenant memory leak.

Two agent runs for DIFFERENT tenants (Alpha and Beta) are interleaved by the
scheduler while sharing ONE mutable memory object. You watch, step by step, as
Beta's run overwrites the shared memory's tenant, and then Alpha's run drafts
its briefing from Beta's data -- a cross-tenant data leak.

The briefings land in a real database (Postgres via DATABASE_URL, else a local
SQLite file), so the leaked row is visible in SQL. The model is real (Ollama)
unless NOVA_LLM=frozen. The interleaving is scripted so the leak fires every run.

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
from nova.cli import run_guarded, truncate
from nova.llm import get_llm
from nova.scheduler import Scheduler
from nova.store import get_store
from nova.trace import Tracer

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"

# run_id -> the tenant that run is SUPPOSED to be working on.
RUN_OWNER = {"run-a": "alpha", "run-b": "beta"}

CONTAMINATION_SCRIPT = [
    "A:read", "A:reason", "B:read", "B:reason", "A:write", "A:draft", "B:write", "B:draft",
]


def main() -> None:
    console = Console()
    console.print(
        Panel(
            "The scheduler interleaves two agent runs that SHARE one memory object:\n"
            "  run-a serves tenant 'alpha'   •   run-b serves tenant 'beta'\n"
            "Watch the 'memory.tenant' column — when a run acts on a tenant that\n"
            "isn't its own, the shared memory has been contaminated across tenants.",
            title="State, Memory & Recovery — shared memory across tenants",
        )
    )

    store = get_store()
    store.init_schema()
    store.reset_demo()
    llm = get_llm()

    with tempfile.TemporaryDirectory() as tmp:
        tracer = Tracer(Path(tmp) / "naive_state_trace.jsonl")
        shared_memory = SharedState()
        agent_alpha = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_memory)
        agent_beta = Agent(store, llm, FIXTURES / "embeddings", tracer, shared_memory)

        Scheduler(CONTAMINATION_SCRIPT).run(
            lambda: agent_alpha.run_steps("alpha", "run-a"),
            lambda: agent_beta.run_steps("beta", "run-b"),
        )
        events = tracer.dump()

    alpha = store.get_briefing("alpha")
    beta = store.get_briefing("beta")

    table = Table(title="Interleaved agent steps (shared memory)")
    table.add_column("#")
    table.add_column("run")
    table.add_column("serves tenant")
    table.add_column("step")
    table.add_column("memory.tenant")
    table.add_column("")
    for i, evt in enumerate(events, start=1):
        owner = RUN_OWNER.get(evt.run_id, "?")
        mem_tenant = str(evt.data.get("state_snapshot", {}).get("client_id", ""))
        contaminated = mem_tenant and mem_tenant != owner
        flag = "[red]⚠ acting on another tenant's memory[/red]" if contaminated else ""
        shown = f"[red]{mem_tenant}[/red]" if contaminated else mem_tenant
        table.add_row(str(i), evt.run_id, owner, evt.step, shown, flag)
    console.print(table)

    briefings = Table(title="Final briefings  (SELECT * FROM briefings)")
    briefings.add_column("tenant")
    briefings.add_column("briefing content")
    briefings.add_row("alpha", truncate(alpha.get("content") or "", 64))
    briefings.add_row("beta", truncate(beta.get("content") or "", 64))
    console.print(briefings)

    if "beta" in (alpha.get("content") or "").lower():
        console.print(
            "\n[bold red]CROSS-TENANT LEAK: tenant Alpha's briefing contains tenant "
            "Beta's data. At the 'A:write'/'A:draft' steps above, run-a read a shared "
            "memory whose tenant had already been overwritten by run-b.[/bold red]"
        )
    store.close()


if __name__ == "__main__":
    run_guarded(main)
