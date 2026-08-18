"""Reference solution for Module 02 — validates test_write.py.

Not shipped to participants and never merged into your_fix.py.
"""
import hashlib


def charge_key(client_id: str, billing_period: str) -> str:
    """Stable idempotency key for one fee: the client and the billing period."""
    return hashlib.sha256(f"{client_id}|{billing_period}".encode("utf-8")).hexdigest()


def charge_client_fee(gateway, store, client_id: str, billing_period: str, amount: int, memo: str) -> None:
    """Guard the irreversible effect: skip the charge if this fee was already charged."""
    key = charge_key(client_id, billing_period)
    if store.already_charged(key):
        return  # already charged this fee -- do NOT touch the gateway again
    gateway.charge(client_id, amount, memo)
    store.record_charge(key, client_id, amount)
