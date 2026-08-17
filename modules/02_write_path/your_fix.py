"""Module 02 — Write Problems: your fix.

Edit ONLY this file. You change one function: `obligation_identity`.

Background: the agent files each obligation with an external regulator (an
irreversible side effect). Before filing, the runner asks this function for an
idempotency key. If two runs produce the same key, the second filing is
skipped. If they produce different keys, the regulator receives two filings for
the same obligation.

The catch: the agent is non-deterministic. Two runs over the SAME client and
SAME document produce differently-worded `obligation_text`. So a key derived
from the text changes every run -- and the guard fails.
"""
import hashlib


def obligation_identity(client_id: str, source_doc: str, obligation_text: str) -> str:
    """Return a STABLE idempotency key identifying this obligation."""
    # TODO: Two runs of the agent produce DIFFERENT obligation_text for the
    # SAME underlying obligation. Derive the key from the agent's INTENT -- the
    # inputs it committed to before generating (client_id, source_doc) -- NOT
    # from obligation_text, which changes every run.
    #
    # Right now this keys on the variable text, so every run gets a different
    # key and the regulator is filed with twice.
    return hashlib.sha256(obligation_text.encode("utf-8")).hexdigest()