"""Module 02 — Write Problems: your fix.

Edit ONLY this file. `guarded_write` is called once per obligation write in
the conflict scenario exercised by `test_write.py`. Make it safe against two
concurrent runs writing the *same* obligation.
"""
from nova.models import Obligation
from nova.store import RecordStore


def guarded_write(store: RecordStore, ob: Obligation) -> None:
    """Write `ob` to the store without creating a duplicate.

    # TODO: add your guard (idempotency key OR optimistic version check)
    before writing. Right now this is the naive, unguarded body -- it will
    duplicate `ob` if called twice with the same idempotency_key.
    """
    store.append_obligation(ob)
