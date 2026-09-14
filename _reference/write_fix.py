"""Reference solution for Module 02 — validates test_write.py.

Not shipped to participants and never merged into your_fix.py.

Two design decisions together make the charge exactly-once:
  1. `charge_key` keys on INTENT (client + period), which is stable across a
     retry AND across the model rewriting the memo.
  2. `charge_client_fee` guards the EFFECT: it checks before charging, so the
     card is never touched a second time -- not just the database row.
"""
import hashlib


def charge_key(client_id: str, billing_period: str, memo: str) -> str:
    """Stable idempotency key for one fee: the client and the billing period.

    The memo is deliberately ignored -- it's the agent's output and changes every
    run, so it cannot identify 'the same charge'.
    """
    return hashlib.sha256(f"{client_id}|{billing_period}".encode("utf-8")).hexdigest()


def charge_client_fee(gateway, store, client_id: str, billing_period: str, amount: int, memo: str) -> None:
    """Guard the irreversible effect: skip the charge if this fee was already charged."""
    key = charge_key(client_id, billing_period, memo)
    if store.already_charged(key):
        return  # already charged this fee -- do NOT touch the gateway again
    gateway.charge(client_id, amount, memo)
    store.record_charge(key, client_id, amount)
