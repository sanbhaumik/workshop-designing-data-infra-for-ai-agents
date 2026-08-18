"""Module 02 — Write Problems: the before/after reveal.

Runs the retry scenario with the naive baseline (charges every time) and with
YOUR fix, and shows how many times the payment gateway actually charged the
client. Before: 2 charges. After: 1.

Run this after you've edited your_fix.py:
    `python modules/02_write_path/compare.py`
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.table import Table

from nova.agent import load_document, payment_memo_prompt
from nova.cli import run_guarded
from nova.effects import PaymentGateway
from nova.llm import get_llm
from nova.store import get_store
from your_fix import charge_client_fee, charge_key

CLIENT_ID = "alpha"
PERIOD = "Q1-2026"
AMOUNT = 2500
SOURCE_DOC = "billing_instruction.md"


def naive_charge(gateway, store, client_id, billing_period, amount, memo):
    """The shipped baseline: charges the gateway on every call."""
    gateway.charge(client_id, amount, memo)
    store.record_charge(charge_key(client_id, billing_period), client_id, amount)


def run_scenario(charge_fn, llm, store) -> int:
    """Run the agent + retry through `charge_fn`; return how many times the card was charged."""
    store.reset_demo()
    gateway = PaymentGateway()
    doc = load_document(CLIENT_ID, SOURCE_DOC)
    for attempt in (1, 2):
        memo = llm.complete(payment_memo_prompt(CLIENT_ID, PERIOD, doc, attempt))
        charge_fn(gateway, store, CLIENT_ID, PERIOD, AMOUNT, memo)
    return len(gateway.charges_for(CLIENT_ID))


def main() -> None:
    console = Console()
    llm = get_llm()
    store = get_store()
    store.init_schema()

    before = run_scenario(naive_charge, llm, store)
    after = run_scenario(charge_client_fee, llm, store)

    table = Table(title="Times the payment gateway charged the client (across one retry)")
    table.add_column("scenario")
    table.add_column("charges")
    table.add_column("total")
    table.add_column("correct?")
    table.add_row("BEFORE — naive (charge every time)", str(before), f"${before * AMOUNT}", "[red]NO — double charged[/red]")
    table.add_row(
        "AFTER — your charge_client_fee",
        str(after),
        f"${after * AMOUNT}",
        "[green]YES[/green]" if after == 1 else "[red]NO[/red]",
    )
    console.print(table)
    console.print()

    if before > 1 and after == 1:
        console.print(
            "[bold green]✓ Fixed.[/bold green] The retry is now stopped BEFORE the charge, "
            "keyed on intent (client + period). The gateway charges the client exactly once."
        )
    elif after > 1:
        console.print(
            "[bold yellow]Not fixed yet.[/bold yellow] The gateway still charged twice — guard "
            "the effect: check `store.already_charged(key)` before `gateway.charge(...)`."
        )
    else:
        console.print("[bold yellow]Check the BEFORE run.[/bold yellow] It should show two charges.")


if __name__ == "__main__":
    run_guarded(main)
