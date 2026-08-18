"""Module 02 — Write Problems: run the agent and watch it file twice.

Runs the NovaBridge obligation agent TWICE for the same client (a retry). You
see each step the agent takes. Because the agent is non-deterministic, the two
runs produce differently-worded obligations for the SAME real commitment -- and
the naive identity guard files both with the regulator.

The model is a real local LLM (Ollama) and the filings land in a real database
(Postgres by DATABASE_URL, else a local SQLite file). Config via env:
    NOVA_LLM=ollama|frozen     DATABASE_URL=postgresql://...

Run this directly: `python modules/02_write_path/naive.py`
"""
import sys
from pathlib import Path

# Make `nova` and this folder's your_fix importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from nova.agent import extraction_prompt, load_document
from nova.cli import run_guarded, truncate
from nova.effects import FILED, RegulatoryFilingSystem
from nova.llm import get_llm
from nova.store import get_store
from your_fix import obligation_identity

CLIENT_ID = "alpha"
SOURCE_DOC = "engagement_letter.md"


def run_agent(console: Console, llm, filing: RegulatoryFilingSystem, attempt: int) -> str:
    """Run the agent once, narrating each step, and file the obligation.

    Returns the obligation text this run produced.
    """
    console.rule(f"[bold]Agent run #{attempt}[/bold]  (client: {CLIENT_ID})")

    document = load_document(CLIENT_ID, SOURCE_DOC)
    console.print(f"  [cyan]1. RETRIEVE[/cyan]  loaded document: {SOURCE_DOC} ({len(document)} chars)")

    obligation_text = llm.complete(extraction_prompt(CLIENT_ID, SOURCE_DOC, document, attempt))
    console.print("  [cyan]2. REASON[/cyan]    the model extracted an obligation:")
    console.print(f"             [yellow]{obligation_text}[/yellow]")

    key = obligation_identity(CLIENT_ID, SOURCE_DOC, obligation_text)
    console.print(f"  [cyan]3. IDENTITY[/cyan]  idempotency key = {key[:16]}…")

    outcome = filing.submit(key, CLIENT_ID, obligation_text)
    style = "green" if outcome == FILED else "magenta"
    console.print(f"  [cyan]4. FILE[/cyan]      → regulator responded: [{style}]{outcome}[/{style}]")
    console.print()
    return obligation_text


def main() -> None:
    console = Console()
    llm = get_llm()
    store = get_store()
    store.init_schema()
    store.reset_demo()
    filing = RegulatoryFilingSystem(store)

    console.print(
        Panel(
            "NovaBridge extracts a regulatory obligation for client 'alpha' and files it\n"
            "with the regulator. We run it TWICE — the same way a retry would.",
            title="Write Problems — the agent runs twice",
        )
    )
    console.print()

    text_1 = run_agent(console, llm, filing, attempt=1)
    text_2 = run_agent(console, llm, filing, attempt=2)

    console.print("[bold]Same obligation, two wordings the agent produced:[/bold]")
    console.print(f"  run #1: [yellow]{text_1}[/yellow]")
    console.print(f"  run #2: [yellow]{text_2}[/yellow]")
    console.print()

    table = Table(title="What the regulator actually received  (SELECT * FROM filings)")
    table.add_column("#")
    table.add_column("outcome")
    table.add_column("obligation text filed")
    for i, attempt in enumerate(filing.attempts, start=1):
        table.add_row(str(i), attempt.outcome, truncate(attempt.obligation_text, 60))
    console.print(table)

    n = len(filing.filings())
    console.print(f"\n[bold]{n} filing(s) reached the regulator for one real obligation.[/bold]")
    if n > 1:
        console.print(
            "[bold red]CORRUPTION: the same obligation was filed twice. A UNIQUE "
            "constraint on the text would NOT have caught this — the two filings have "
            "different text. The identity key was derived from the model's variable "
            "output instead of the agent's stable intent.[/bold red]"
        )


if __name__ == "__main__":
    run_guarded(main)
