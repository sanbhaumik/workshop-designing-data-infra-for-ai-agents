"""Module 02 — Write Problems: the before/after reveal.

Runs the same two-agent-run scenario TWICE -- once with the naive baseline
identity (keyed on the model's variable text) and once with YOUR fix (whatever
`obligation_identity` in your_fix.py currently returns) -- and prints both
regulator tables so you can see the double filing collapse to one.

Uses the real model (NOVA_LLM) and the real database (DATABASE_URL). To keep the
two runs from sharing filings, each uses its own logical client id.

Run this after you've edited your_fix.py:
    `python modules/02_write_path/compare.py`
"""
import hashlib
import sys
from pathlib import Path

# Make `nova` and this folder's your_fix importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.table import Table

from nova.agent import extraction_prompt, load_document
from nova.effects import FILED, RegulatoryFilingSystem
from nova.llm import get_llm
from nova.store import get_store
from your_fix import obligation_identity

CLIENT_ID = "alpha"
SOURCE_DOC = "engagement_letter.md"


def naive_identity(client_id: str, source_doc: str, obligation_text: str) -> str:
    """The shipped baseline: keyed on the model's variable output."""
    return hashlib.sha256(obligation_text.encode("utf-8")).hexdigest()


def run_scenario(identity_fn, llm, store, tag: str) -> RegulatoryFilingSystem:
    """Run the agent twice, keying each filing with `identity_fn`.

    `tag` namespaces the idempotency keys and client id so the before and after
    runs never share filings in the shared database.
    """
    filing = RegulatoryFilingSystem(store)
    client = f"{CLIENT_ID}-{tag}"
    document = load_document(CLIENT_ID, SOURCE_DOC)
    for attempt in (1, 2):
        text = llm.complete(extraction_prompt(CLIENT_ID, SOURCE_DOC, document, attempt))
        key = f"{tag}:" + identity_fn(CLIENT_ID, SOURCE_DOC, text)
        filing.submit(key, client, text)
    return filing


def render(console: Console, title: str, filing: RegulatoryFilingSystem) -> int:
    """Print one regulator table and return the number of filings that landed."""
    table = Table(title=title)
    table.add_column("run")
    table.add_column("idempotency key")
    table.add_column("outcome")
    for i, attempt in enumerate(filing.attempts, start=1):
        style = "green" if attempt.outcome == FILED else "magenta"
        table.add_row(str(i), attempt.idempotency_key[:20] + "…", f"[{style}]{attempt.outcome}[/{style}]")
    console.print(table)
    return sum(1 for a in filing.attempts if a.outcome == FILED)


def main() -> None:
    console = Console()
    llm = get_llm()
    store = get_store()
    store.init_schema()
    store.reset_demo()

    before = run_scenario(naive_identity, llm, store, tag="before")
    after = run_scenario(obligation_identity, llm, store, tag="after")

    console.print()
    n_before = render(console, "BEFORE — naive identity (keyed on model output)", before)
    console.print()
    n_after = render(console, "AFTER — your identity (your_fix.py)", after)
    console.print()

    console.print(f"[bold]Before:[/bold] {n_before} filing(s) reached the regulator")
    console.print(f"[bold]After:[/bold]  {n_after} filing(s) reached the regulator")
    console.print()

    if n_before > 1 and n_after == 1:
        console.print(
            "[bold green]✓ Fixed.[/bold green] Two runs with different wording now share "
            "one idempotency key, so the duplicate filing is skipped. The model is still "
            "non-deterministic — you made the identity deterministic."
        )
    elif n_after > 1:
        console.print(
            "[bold yellow]Not fixed yet.[/bold yellow] The AFTER table still shows two "
            "filings — edit `obligation_identity` in your_fix.py so the key does not depend "
            "on obligation_text."
        )
    else:
        console.print(
            "[bold yellow]Check the BEFORE table.[/bold yellow] It should show two filings; "
            "if it doesn't, the two model outputs may have coincidentally matched — run again."
        )


if __name__ == "__main__":
    main()
