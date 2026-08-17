"""Reference solution for Module 02 — validates test_write.py.

Not shipped to participants and never merged into your_fix.py.
"""
import hashlib


def obligation_identity(client_id: str, source_doc: str, obligation_text: str) -> str:
    """Stable intent identity: key on the inputs the agent committed to before
    generating, not on the variable text it produced.

    Two runs over the same (client_id, source_doc) map to the same key, so the
    regulator is filed with exactly once no matter how the wording differs.
    """
    return hashlib.sha256(f"{client_id}|{source_doc}".encode("utf-8")).hexdigest()
