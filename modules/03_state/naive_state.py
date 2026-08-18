"""Module 03 — State, Memory & Recovery: watch tenant data leak.

Two agent runs for DIFFERENT tenants (Alpha and Beta) are interleaved by the
scheduler while sharing ONE mutable memory object. You watch, step by step, as
Beta's run overwrites the shared memory, and then Alpha's run saves an account
summary built from Beta's data -- a cross-tenant leak.

The summaries land in a real database (Postgres via DATABASE_URL, else SQLite),
so the leaked row is visible in SQL. The model is real (Ollama) unless
NOVA_LLM=frozen. The interleaving is scripted so the leak fires every run.

Run this directly: `python modules/03_state/naive_state.py`
"""
import sys
import tempfile
from pathlib import Path

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

RUN_OWNER = {"run-a": "alpha", "run-b": "beta"}
CONTAMINATION_SCRIPT = ["A:read", "A:reason", "B:read", "B:reason", "A:save", "B:save"]


def main() -> None:
    console = Console()
    console.print(
        Panel(
            "The scheduler interleaves two agent runs that SHARE one memory object:\n"
            "  run-a serves tenant 'alpha'   •   run-b serves tenant 'beta'\n"
            "Watch the 'memory.tenant' column — when a run acts on a tenant that\n"
            "isn't its own, the shared memory has leaked across tenants.",
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

    alpha = store.get_summary("alpha")
    beta = store.get_summary("beta")

    table = Table(title="Interleaved agent steps (shared memory)")
    table.add_column("#")
    table.add_column("run")
    table.add_column("serves tenant")
    table.add_column("step")
    table.add_column("memory.tenant")
    table.add_column("")
    for i, evt in enumerate(events, start=1):
        owner = RUN_OWNER.get(evt.run_id, "?")
        mem_tenant = str(evt.data.get("memory_snapshot", {}).get("client_id", ""))
        leaked = mem_tenant and mem_tenant != owner
        flag = "[red]⚠ acting on another tenant's memory[/red]" if leaked else ""
        shown = f"[red]{mem_tenant}[/red]" if leaked else mem_tenant
        table.add_row(str(i), evt.run_id, owner, evt.step, shown, flag)
    console.print(table)

    summaries = Table(title="Final account summaries  (SELECT * FROM summaries)")
    summaries.add_column("tenant")
    summaries.add_column("summary content")
    summaries.add_row("alpha", truncate(alpha.get("content") or "", 66))
    summaries.add_row("beta", truncate(beta.get("content") or "", 66))
    console.print(summaries)

    if "beta" in (alpha.get("content") or "").lower():
        console.print(
            "\n[bold red]CROSS-TENANT LEAK: tenant Alpha's account summary contains tenant "
            "Beta's data (Beta's balance!). At the 'A:save' step above, run-a read a shared "
            "memory whose tenant had already been overwritten by run-b.[/bold red]"
        )
    store.close()


if __name__ == "__main__":
    run_guarded(main)
