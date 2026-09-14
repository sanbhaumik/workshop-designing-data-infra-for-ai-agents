"""Module 02 — Write Problems: the before/after reveal.

Runs TWO retry scenarios against the payment gateway, with the naive baseline
(charges every time) and with YOUR charge_client_fee:

  Replayed    — the retry replays the SAME memo.
  Regenerated — the agent re-ran and the model REWROTE the memo (same fee).

A fix that guards the effect but keys on the memo passes Replayed and fails
Regenerated. That gap is the whole point of the lab.

Uses the real model (NOVA_LLM) and real database (DATABASE_URL); the shared
database is reset between phases.

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
    store.record_charge(charge_key(client_id, billing_period, memo), client_id, amount)


def _memos(llm, scenario: str) -> tuple[str, str]:
    doc = load_document(CLIENT_ID, SOURCE_DOC)
    first = llm.complete(payment_memo_prompt(CLIENT_ID, PERIOD, doc, 1))
    if scenario == "replayed":
        return first, first  # the same request is retried
    second = llm.complete(payment_memo_prompt(CLIENT_ID, PERIOD, doc, 2))
    return first, second  # the agent re-ran and rewrote the memo


def run_scenario(charge_fn, llm, store, scenario: str) -> int:
    """Run the fee charge + one retry through `charge_fn`; return charges on the card."""
    store.reset_demo()
    gateway = PaymentGateway()
    for memo in _memos(llm, scenario):
        charge_fn(gateway, store, CLIENT_ID, PERIOD, AMOUNT, memo)
    return len(gateway.charges_for(CLIENT_ID))


def _cell(n: int) -> str:
    return "[green]1 — correct[/green]" if n == 1 else f"[red]{n} — double charged[/red]"


def main() -> None:
    console = Console()
    llm = get_llm()
    store = get_store()
    store.init_schema()

    naive_replay = run_scenario(naive_charge, llm, store, "replayed")
    naive_regen = run_scenario(naive_charge, llm, store, "regenerated")
    your_replay = run_scenario(charge_client_fee, llm, store, "replayed")
    your_regen = run_scenario(charge_client_fee, llm, store, "regenerated")

    table = Table(title="Times the gateway charged the client (across one retry)")
    table.add_column("scenario")
    table.add_column("naive (charge every time)")
    table.add_column("your charge_client_fee")
    table.add_row("Replayed — same memo", _cell(naive_replay), _cell(your_replay))
    table.add_row("Regenerated — memo rewritten", _cell(naive_regen), _cell(your_regen))
    console.print(table)
    console.print()

    if your_replay == 1 and your_regen == 1:
        console.print(
            "[bold green]✓ Exactly once.[/bold green] The charge is guarded before the effect "
            "and keyed on intent (client + period), so it survives a retry whether the memo is "
            "replayed or rewritten."
        )
    elif your_replay == 1 and your_regen > 1:
        console.print(
            "[bold yellow]Half fixed — this is the trap.[/bold yellow] You guarded the effect, so "
            "a replayed retry is safe. But you keyed on the agent's memo, and the model rewrote it "
            "on re-run, so the 'same' fee got two keys. Key on the INTENT (client + period)."
        )
    else:
        console.print(
            "[bold yellow]Not fixed yet.[/bold yellow] The gateway still charged twice — guard the "
            "effect: check `store.already_charged(key)` before `gateway.charge(...)`."
        )


if __name__ == "__main__":
    run_guarded(main)
