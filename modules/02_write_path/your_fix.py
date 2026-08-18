"""Module 02 — Write Problems: your fix.

Edit ONLY this file. You change one function: `charge_client_fee`.

The agent charges a client's advisory fee through a payment gateway. Agents
retry (a timeout, a transient error), so `charge_client_fee` can be called more
than once for the same fee. It must charge the client at most ONCE.

The catch you'll discover in the lab: putting a unique key on the `charges`
table makes the *record* idempotent, but it does not un-charge the card. The
gateway is the outside world. You have to stop the charge *before* it happens.
"""
import hashlib


def charge_key(client_id: str, billing_period: str) -> str:
    """A stable idempotency key for one fee: the client and the billing period.

    This is the agent's INTENT -- it's the same on every retry, unlike the memo
    text the model writes, which changes each run.
    """
    return hashlib.sha256(f"{client_id}|{billing_period}".encode("utf-8")).hexdigest()


def charge_client_fee(gateway, store, client_id: str, billing_period: str, amount: int, memo: str) -> None:
    """Charge the client's advisory fee -- at most once per (client, period)."""
    key = charge_key(client_id, billing_period)
    # TODO: before charging, check whether this fee was already charged
    # (store.already_charged(key)) and RETURN without charging if it was.
    # Right now this charges the gateway every time it's called -- so a retry
    # charges the client twice, even though the `charges` table only keeps one row.
    gateway.charge(client_id, amount, memo)
    store.record_charge(key, client_id, amount)
