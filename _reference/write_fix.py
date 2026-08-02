"""Reference solution for Module 02 — validates test_write.py.

Not shipped to participants and never merged into your_fix.py.
"""
from nova.models import Obligation
from nova.store import RecordStore


def guarded_write(store: RecordStore, ob: Obligation) -> None:
    """Idempotency-key guard: skip the write if this obligation was already recorded."""
    if ob.idempotency_key is not None:
        existing = store.execute(
            "SELECT 1 FROM obligations WHERE client_id = ? AND idempotency_key = ? LIMIT 1",
            (ob.client_id, ob.idempotency_key),
        )
        if existing:
            return
    store.append_obligation(ob)
