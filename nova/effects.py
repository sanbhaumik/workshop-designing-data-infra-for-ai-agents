"""External side effects for the agent.

`RegulatoryFilingSystem` stands in for an irreversible outbound action: filing
an obligation with a regulator. It is backed by the record store's `filings`
table, so what it did is visible in real SQL (`SELECT * FROM filings`).

It dedupes submissions by an `idempotency_key` you supply, and keeps an
in-memory log of every attempt (filed or skipped) so the lab can narrate what
happened. The system itself is honest infrastructure: whether you get one filing
or two depends entirely on the key you hand it.
"""
from dataclasses import dataclass

FILED = "FILED"
SKIPPED = "SKIPPED (already filed)"


@dataclass
class FilingAttempt:
    """One submission attempt and how the filing system responded."""

    idempotency_key: str
    client_id: str
    obligation_text: str
    outcome: str


class RegulatoryFilingSystem:
    """Store-backed stand-in for an irreversible external filing system."""

    def __init__(self, store) -> None:
        self.store = store
        self.attempts: list[FilingAttempt] = []

    def submit(self, idempotency_key: str, client_id: str, obligation_text: str) -> str:
        """Submit an obligation for filing.

        If `idempotency_key` was already filed, this is a no-op and returns
        SKIPPED. Otherwise it files (a row in `filings`) and returns FILED.
        Every call is recorded in `attempts` regardless of outcome.
        """
        already_filed = self.store.filing_exists(idempotency_key)
        outcome = SKIPPED if already_filed else FILED
        self.attempts.append(FilingAttempt(idempotency_key, client_id, obligation_text, outcome))
        if not already_filed:
            self.store.insert_filing(idempotency_key, client_id, obligation_text)
        return outcome

    def filings(self) -> list[dict]:
        """Return the distinct filings that actually reached the regulator."""
        return self.store.get_filings()
