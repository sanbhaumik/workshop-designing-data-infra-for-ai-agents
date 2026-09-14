"""Module 02 — Write Problems: your fix.

Edit ONLY this file. You change two things: WHERE the charge happens (the effect
boundary) and WHAT identifies "the same charge" (`charge_key`).

The agent charges a client's advisory fee through a payment gateway. Agents
retry — a timeout, a transient error — so `charge_client_fee` can be called more
than once for the same fee. It must charge the client at most ONCE.

Right now it charges every time. You'll discover two things the hard way:

  1. A unique key on the `charges` *table* dedupes your row, but it cannot
     un-charge a card. You have to guard the effect BEFORE it happens.
  2. Keying on the agent's memo (its output) looks fine when a retry replays the
     same text — but the model rewrites the memo every run, so the "same" fee
     gets two different keys and the client is charged twice.

There are two tests: a replayed retry and a regenerated retry. Watch which fixes
pass which.
"""
import hashlib


def charge_key(client_id: str, billing_period: str, memo: str) -> str:
    """Return the idempotency key for one fee: what makes two charges 'the same'?"""
    # TODO: key on the fee's INTENT (which client, which period), not on the
    # agent's output. The memo below changes every run, so it can't dedup a retry.
    return hashlib.sha256(memo.encode("utf-8")).hexdigest()  # NAIVE: memo is not identity


def charge_client_fee(gateway, store, client_id: str, billing_period: str, amount: int, memo: str) -> None:
    """Charge the client's advisory fee -- at most once per (client, period)."""
    key = charge_key(client_id, billing_period, memo)
    # TODO: guard the EFFECT. Before charging, check store.already_charged(key)
    # and RETURN without charging if this fee was already applied.
    gateway.charge(client_id, amount, memo)  # NAIVE: charges every time -> retries double-charge
    store.record_charge(key, client_id, amount)
