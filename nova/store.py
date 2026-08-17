"""Record store with two interchangeable backends:

    RecordStore    -- SQLite, used by the deterministic test suite (offline).
    PostgresStore  -- Postgres, used by the live labs (real client/server DB).

Both expose the same method surface, so participant `your_fix.py` code and the
lab runners are identical against either. Pick one with `get_store()`, which
reads `DATABASE_URL` (a `postgres://...` URL selects Postgres; anything else,
or unset, selects a local SQLite file).

Hand-rolled SQL per backend -- no ORM -- so every query stays visible to
learners. The two dialects differ only in the auto-increment column type, the
parameter placeholder, and the `ON CONFLICT` keyword case.
"""
import os
import sqlite3
from pathlib import Path

from nova.models import Obligation

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (client_id TEXT PRIMARY KEY, name TEXT);
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, path TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS obligations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL, text TEXT NOT NULL, source_doc TEXT, idempotency_key TEXT);
CREATE TABLE IF NOT EXISTS briefings (
    client_id TEXT PRIMARY KEY, content TEXT, version INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS filings (
    idempotency_key TEXT PRIMARY KEY, client_id TEXT NOT NULL, obligation_text TEXT NOT NULL);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (client_id TEXT PRIMARY KEY, name TEXT);
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY, client_id TEXT NOT NULL, path TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS obligations (
    id SERIAL PRIMARY KEY,
    client_id TEXT NOT NULL, text TEXT NOT NULL, source_doc TEXT, idempotency_key TEXT);
CREATE TABLE IF NOT EXISTS briefings (
    client_id TEXT PRIMARY KEY, content TEXT, version INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS filings (
    idempotency_key TEXT PRIMARY KEY, client_id TEXT NOT NULL, obligation_text TEXT NOT NULL);
"""

DEMO_TABLES = ("filings", "obligations", "briefings")


class RecordStore:
    """SQLite-backed store. Placeholder '?', used by the test suite."""

    placeholder = "?"

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        """Create all tables if they don't already exist."""
        self._conn.executescript(SQLITE_SCHEMA)
        self._conn.commit()

    def _rows(self, sql: str, params: tuple = ()) -> list[dict]:
        return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def _exec(self, sql: str, params: tuple = ()) -> None:
        self._conn.execute(sql, params)
        self._conn.commit()

    def get_client(self, client_id: str) -> dict:
        """Return the client row as a dict, or {} if it doesn't exist."""
        rows = self._rows("SELECT * FROM clients WHERE client_id = ?", (client_id,))
        return rows[0] if rows else {}

    def append_obligation(self, ob: Obligation) -> None:
        """NAIVE: inserts unconditionally. No dedup, no idempotency check."""
        self._exec(
            "INSERT INTO obligations (client_id, text, source_doc, idempotency_key) "
            "VALUES (?, ?, ?, ?)",
            (ob.client_id, ob.text, ob.source_doc, ob.idempotency_key),
        )

    def get_obligations(self, client_id: str) -> list[Obligation]:
        """Return all obligations recorded for a client, in insertion order."""
        rows = self._rows("SELECT * FROM obligations WHERE client_id = ? ORDER BY id", (client_id,))
        return [Obligation(**r) for r in rows]

    def set_briefing(self, client_id: str, content: str) -> None:
        """NAIVE: last-write-wins, no version check."""
        self._exec(
            "INSERT INTO briefings (client_id, content, version) VALUES (?, ?, 1) "
            "ON CONFLICT(client_id) DO UPDATE SET "
            "content = excluded.content, version = briefings.version + 1",
            (client_id, content),
        )

    def get_briefing(self, client_id: str) -> dict:
        """Return the briefing row as a dict, or {} if it doesn't exist."""
        rows = self._rows("SELECT * FROM briefings WHERE client_id = ?", (client_id,))
        return rows[0] if rows else {}

    def filing_exists(self, idempotency_key: str) -> bool:
        """True if an obligation was already filed under this idempotency key."""
        rows = self._rows("SELECT 1 FROM filings WHERE idempotency_key = ?", (idempotency_key,))
        return bool(rows)

    def insert_filing(self, idempotency_key: str, client_id: str, obligation_text: str) -> None:
        """Record a filing that reached the regulator."""
        self._exec(
            "INSERT INTO filings (idempotency_key, client_id, obligation_text) VALUES (?, ?, ?)",
            (idempotency_key, client_id, obligation_text),
        )

    def get_filings(self, client_id: str | None = None) -> list[dict]:
        """Return distinct filings, optionally filtered by client."""
        if client_id is None:
            return self._rows("SELECT * FROM filings")
        return self._rows("SELECT * FROM filings WHERE client_id = ?", (client_id,))

    def reset_demo(self) -> None:
        """Clear the tables the labs write to, for a clean before/after run."""
        for table in DEMO_TABLES:
            self._exec(f"DELETE FROM {table}")

    def execute(self, sql: str, params: tuple = ()) -> list:
        """Primitive for participant fixes to build on (e.g. version checks)."""
        cur = self._conn.execute(sql, params)
        self._conn.commit()
        return cur.fetchall()

    def close(self) -> None:
        self._conn.close()


class PostgresStore:
    """Postgres-backed store. Placeholder '%s', used by the live labs."""

    placeholder = "%s"

    def __init__(self, dsn: str) -> None:
        import psycopg  # lazy: only needed on the Postgres path
        from psycopg.rows import dict_row

        self.dsn = dsn
        self._conn = psycopg.connect(dsn, row_factory=dict_row, autocommit=True)

    def init_schema(self) -> None:
        """Create all tables if they don't already exist."""
        self._conn.execute(POSTGRES_SCHEMA)

    def _rows(self, sql: str, params: tuple = ()) -> list[dict]:
        return list(self._conn.execute(sql, params).fetchall())

    def _exec(self, sql: str, params: tuple = ()) -> None:
        self._conn.execute(sql, params)

    def get_client(self, client_id: str) -> dict:
        """Return the client row as a dict, or {} if it doesn't exist."""
        rows = self._rows("SELECT * FROM clients WHERE client_id = %s", (client_id,))
        return rows[0] if rows else {}

    def append_obligation(self, ob: Obligation) -> None:
        """NAIVE: inserts unconditionally. No dedup, no idempotency check."""
        self._exec(
            "INSERT INTO obligations (client_id, text, source_doc, idempotency_key) "
            "VALUES (%s, %s, %s, %s)",
            (ob.client_id, ob.text, ob.source_doc, ob.idempotency_key),
        )

    def get_obligations(self, client_id: str) -> list[Obligation]:
        """Return all obligations recorded for a client, in insertion order."""
        rows = self._rows("SELECT * FROM obligations WHERE client_id = %s ORDER BY id", (client_id,))
        return [Obligation(**r) for r in rows]

    def set_briefing(self, client_id: str, content: str) -> None:
        """NAIVE: last-write-wins, no version check."""
        self._exec(
            "INSERT INTO briefings (client_id, content, version) VALUES (%s, %s, 1) "
            "ON CONFLICT (client_id) DO UPDATE SET "
            "content = EXCLUDED.content, version = briefings.version + 1",
            (client_id, content),
        )

    def get_briefing(self, client_id: str) -> dict:
        """Return the briefing row as a dict, or {} if it doesn't exist."""
        rows = self._rows("SELECT * FROM briefings WHERE client_id = %s", (client_id,))
        return rows[0] if rows else {}

    def filing_exists(self, idempotency_key: str) -> bool:
        """True if an obligation was already filed under this idempotency key."""
        rows = self._rows("SELECT 1 FROM filings WHERE idempotency_key = %s", (idempotency_key,))
        return bool(rows)

    def insert_filing(self, idempotency_key: str, client_id: str, obligation_text: str) -> None:
        """Record a filing that reached the regulator."""
        self._exec(
            "INSERT INTO filings (idempotency_key, client_id, obligation_text) VALUES (%s, %s, %s)",
            (idempotency_key, client_id, obligation_text),
        )

    def get_filings(self, client_id: str | None = None) -> list[dict]:
        """Return distinct filings, optionally filtered by client."""
        if client_id is None:
            return self._rows("SELECT * FROM filings")
        return self._rows("SELECT * FROM filings WHERE client_id = %s", (client_id,))

    def reset_demo(self) -> None:
        """Clear the tables the labs write to, for a clean before/after run."""
        self._exec("TRUNCATE " + ", ".join(DEMO_TABLES))

    def execute(self, sql: str, params: tuple = ()) -> list:
        """Primitive for participant fixes to build on (e.g. version checks)."""
        return self._rows(sql, params)

    def close(self) -> None:
        self._conn.close()


def get_store(db_url: str | None = None):
    """Return a store selected by `db_url` / `DATABASE_URL`.

    A `postgres://` or `postgresql://` URL selects Postgres; anything else (or
    unset) selects a local SQLite file at `nova_workshop.db`.
    """
    url = db_url if db_url is not None else os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://") or url.startswith("postgresql://"):
        return PostgresStore(url)
    sqlite_path = url or "nova_workshop.db"
    return RecordStore(Path(sqlite_path))
