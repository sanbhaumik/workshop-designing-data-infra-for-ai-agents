"""Module 02 — Write Problems: watch the 'obvious' table-key fix double-charge.

The NovaBridge agent charges a client's quarterly advisory fee. Agents retry, so
we run it twice. This demo uses the OBVIOUS fix -- rely on the unique key of the
`charges` table -- but applies it the natural way: charge the card, then record
the row. The table dedupes to ONE row, but the payment gateway (the outside
world) charged the client TWICE. A database constraint protects your records,
not the client's card; the guard has to sit BEFORE the irreversible effect.

The model is real (Ollama) unless NOVA_LLM=frozen; the charges land in a real
database (Postgres by DATABASE_URL, else SQLite).

Run this directly: `python modules/02_write_path/naive.py`
"""
import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from nova.agent import load_document, payment_memo_prompt
from nova.cli import run_guarded, truncate
from nova.effects import PaymentGateway
from nova.llm import get_llm
from nova.store import get_store

CLIENT_ID = "alpha"
PERIOD = "Q1-2026"
AMOUNT = 2500
SOURCE_DOC = "billing_instruction.md"


def table_key_charge(gateway, store, client_id: str, billing_period: str, amount: int, memo: str) -> None:
    """The 'obvious' fix: lean on the charges table's unique key.

    Charges the card, THEN records with ON CONFLICT DO NOTHING. The row dedupes,
    but the card does not -- the guard is on the wrong side of the effect.
    """
    key = hashlib.sha256(f"{client_id}|{billing_period}".encode("utf-8")).hexdigest()
    gateway.charge(client_id, amount, memo)          # irreversible effect fires first
    store.record_charge(key, client_id, amount)      # unique key -> only one row survives


def run_agent(console: Console, llm, gateway, store, attempt: int) -> str:
    """Run the agent once (it writes a memo and charges the fee). Return the memo."""
    console.rule(f"[bold]Agent run #{attempt}[/bold]  (client: {CLIENT_ID}, period: {PERIOD})")
    document = load_document(CLIENT_ID, SOURCE_DOC)
    console.print(f"  [cyan]1. RETRIEVE[/cyan]  loaded billing note ({len(document)} chars)")

    memo = llm.complete(payment_memo_prompt(CLIENT_ID, PERIOD, document, attempt))
    console.print("  [cyan]2. REASON[/cyan]    the model wrote a payment memo:")
    console.print(f"             [yellow]{truncate(memo, 90)}[/yellow]")

    console.print(f"  [cyan]3. CHARGE[/cyan]    charging the ${AMOUNT} advisory fee…")
    table_key_charge(gateway, store, CLIENT_ID, PERIOD, AMOUNT, memo)
    console.print()
    return memo


def main() -> None:
    console = Console()
    llm = get_llm()
    store = get_store()
    store.init_schema()
    store.reset_demo()
    gateway = PaymentGateway()

    console.print(
        Panel(
            "NovaBridge charges client 'alpha' a $2,500 quarterly advisory fee.\n"
            "Agents retry, so we run it TWICE — the same way a retry would.",
            title="Write Problems — the agent charges a fee (twice)",
        )
    )
    console.print()

    run_agent(console, llm, gateway, store, attempt=1)
    run_agent(console, llm, gateway, store, attempt=2)

    recorded = store.get_charges(CLIENT_ID)
    charged = gateway.charges_for(CLIENT_ID)

    left = Table(title="What YOU recorded  (SELECT * FROM charges)")
    left.add_column("client")
    left.add_column("amount")
    for row in recorded:
        left.add_row(row["client_id"], f"${row['amount']}")
    console.print(left)

    right = Table(title="What the PAYMENT GATEWAY actually did (the client's card)")
    right.add_column("#")
    right.add_column("client")
    right.add_column("amount")
    for i, c in enumerate(charged, start=1):
        right.add_row(str(i), c.client_id, f"${c.amount}")
    console.print(right)

    console.print(
        f"\n[bold]Your table: {len(recorded)} charge. "
        f"The gateway: {len(charged)} charges (${gateway.total_charged(CLIENT_ID)}).[/bold]"
    )
    if len(charged) > 1:
        console.print(
            "[bold red]DOUBLE CHARGE: the client was billed twice. The unique key on your "
            "`charges` table protected your records — it did NOT un-charge the card. The "
            "irreversible effect fired before the record. Idempotency has to be enforced "
            "before the charge, keyed on intent (client + period).[/bold red]"
        )


if __name__ == "__main__":
    run_guarded(main)
