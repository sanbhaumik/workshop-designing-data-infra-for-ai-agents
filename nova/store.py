"""SQLite record store. Neutral primitives plus deliberately naive convenience
writes that the labs expose as broken.
"""
import sqlite3
from pathlib import Path

from nova.models import Obligation

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    client_id TEXT PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY,
    client_id TEXT NOT NULL,
    path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS obligations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL,
    text TEXT NOT NULL,
    source_doc TEXT,
    idempotency_key TEXT
);

CREATE TABLE IF NOT EXISTS briefings (
    client_id TEXT PRIMARY KEY,
    content TEXT,
    version INTEGER NOT NULL DEFAULT 0
);
"""


class RecordStore:
    """SQLite-backed store for clients, documents, obligations, and briefings."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        """Create all tables if they don't already exist."""
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def get_client(self, client_id: str) -> dict:
        """Return the client row as a dict, or {} if it doesn't exist."""
        row = self._conn.execute(
            "SELECT * FROM clients WHERE client_id = ?", (client_id,)
        ).fetchone()
        return dict(row) if row else {}

    def append_obligation(self, ob: Obligation) -> None:
        """NAIVE: inserts unconditionally. No dedup, no idempotency check."""
        self._conn.execute(
            "INSERT INTO obligations (client_id, text, source_doc, idempotency_key) "
            "VALUES (?, ?, ?, ?)",
            (ob.client_id, ob.text, ob.source_doc, ob.idempotency_key),
        )
        self._conn.commit()

    def set_briefing(self, client_id: str, content: str) -> None:
        """NAIVE: last-write-wins, no version check."""
        self._conn.execute(
            """
            INSERT INTO briefings (client_id, content, version) VALUES (?, ?, 1)
            ON CONFLICT(client_id) DO UPDATE SET
                content = excluded.content,
                version = briefings.version + 1
            """,
            (client_id, content),
        )
        self._conn.commit()

    def get_briefing(self, client_id: str) -> dict:
        """Return the briefing row as a dict, or {} if it doesn't exist."""
        row = self._conn.execute(
            "SELECT * FROM briefings WHERE client_id = ?", (client_id,)
        ).fetchone()
        return dict(row) if row else {}

    def get_obligations(self, client_id: str) -> list[Obligation]:
        """Return all obligations recorded for a client, in insertion order."""
        rows = self._conn.execute(
            "SELECT * FROM obligations WHERE client_id = ? ORDER BY id", (client_id,)
        ).fetchall()
        return [Obligation(**dict(row)) for row in rows]

    def execute(self, sql: str, params: tuple = ()) -> list:
        """Primitive for participant fixes to build on (e.g. version checks)."""
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return cur.fetchall()
