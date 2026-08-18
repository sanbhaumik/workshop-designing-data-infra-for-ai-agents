"""External side effects for the agent.

`PaymentGateway` stands in for an external payment processor: every `charge()`
actually moves money. It is deliberately dumb -- it does NOT dedup, because the
outside world does not know your intent. It is NOT your database; it keeps its
own ledger of what really happened.

That separation is the whole lesson of the Write lab: a UNIQUE constraint on
your own `charges` table protects your records, but it cannot un-charge a card.
Idempotency has to be enforced *before* the irreversible effect.
"""
from dataclasses import dataclass, field


@dataclass
class Charge:
    """One charge that actually reached the payment processor."""

    client_id: str
    amount: int
    memo: str


@dataclass
class PaymentGateway:
    """In-memory stand-in for an external, irreversible payment processor."""

    ledger: list[Charge] = field(default_factory=list)

    def charge(self, client_id: str, amount: int, memo: str) -> Charge:
        """Charge the client. This always executes -- the money moves. No dedup."""
        charge = Charge(client_id=client_id, amount=amount, memo=memo)
        self.ledger.append(charge)
        return charge

    def charges_for(self, client_id: str) -> list[Charge]:
        """Return every charge the processor actually applied for a client."""
        return [c for c in self.ledger if c.client_id == client_id]

    def total_charged(self, client_id: str) -> int:
        """Total amount actually charged to a client (double-charges included)."""
        return sum(c.amount for c in self.charges_for(client_id))
