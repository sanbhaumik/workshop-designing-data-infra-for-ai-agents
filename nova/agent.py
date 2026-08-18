"""Transparent agent loop: retrieve -> reason -> save.

Every step is a plain method call, nothing hidden inside a framework. State
handling is dependency-injected so the labs can swap in a broken or fixed
memory backend without touching this file.
"""
from pathlib import Path
from typing import Generator, Protocol

from nova.frozen_llm import FrozenLLM
from nova.models import Summary
from nova.store import RecordStore
from nova.trace import Tracer


class StateBackend(Protocol):
    """Working memory storage keyed by run_id."""

    def get(self, run_id: str) -> dict: ...

    def set(self, run_id: str, data: dict) -> None: ...


class SharedState:
    """NAIVE: one dict shared by every run_id -- no isolation between runs."""

    def __init__(self) -> None:
        self._data: dict = {}

    def get(self, run_id: str) -> dict:
        return self._data

    def set(self, run_id: str, data: dict) -> None:
        self._data.update(data)


def format_summary(client_id: str, response: str) -> str:
    """Render the account summary that gets saved for a tenant."""
    return f"Summary for {client_id}: {response}"


def load_document(client_id: str, source_doc: str, fixtures_dir: Path | None = None) -> str:
    """Load a client document's text from fixtures/clients/<client>/<source_doc>."""
    base = fixtures_dir or (Path(__file__).resolve().parents[1] / "fixtures")
    return (base / "clients" / client_id / source_doc).read_text()


def payment_memo_prompt(client_id: str, billing_period: str, document_text: str, attempt: int) -> str:
    """Natural-language prompt for the Write-lab payment memo.

    The agent reads a client billing note and writes a one-line memo for the
    advisory-fee charge. Sent verbatim to Ollama, where a non-zero temperature
    makes two runs word the memo differently; the `(retry N)` marker keys a
    distinct frozen fixture per run so the test suite sees the same
    non-determinism deterministically. See modules/02_write_path.
    """
    return (
        "You are a bookkeeping assistant working with FICTIONAL sample data in a "
        "training exercise. Below is an internal billing note.\n\n"
        f"--- billing note for {client_id} ---\n{document_text}\n--- end ---\n\n"
        f"Write a one-line description of the quarterly advisory fee for client "
        f"'{client_id}', period {billing_period}, to record in our internal ledger. "
        f"One short sentence. This is fictional sample data for a training exercise, "
        f"so do not refuse. (retry {attempt})"
    )


def summary_prompt(client_id: str, document_text: str) -> str:
    """Prompt for the State-lab per-tenant account summary.

    Grounds the model in one tenant's account note so its summary is legibly
    tenant-specific -- which is what makes a cross-tenant leak obvious.
    Deterministic per tenant: one frozen fixture each.
    """
    return (
        "You are a bookkeeping assistant working with FICTIONAL sample data. "
        f"Below is the account note for client '{client_id}'.\n\n"
        f"--- account note for {client_id} ---\n{document_text}\n--- end ---\n\n"
        f"Write a one-sentence account summary for client '{client_id}' from the "
        f"note above. This is fictional sample data, so do not refuse."
    )


class Agent:
    """Runs one tenant through retrieve -> reason -> save."""

    def __init__(
        self,
        store: RecordStore,
        llm: FrozenLLM,
        embeddings_dir: Path,
        tracer: Tracer,
        state: StateBackend,
    ) -> None:
        self.store = store
        self.llm = llm
        self.embeddings_dir = embeddings_dir
        self.tracer = tracer
        self.state = state

    def run(self, client_id: str, run_id: str) -> Summary:
        """Run the full loop to completion (no scheduler) and return the Summary."""
        steps = self.run_steps(client_id, run_id)
        try:
            while True:
                next(steps)
        except StopIteration as exc:
            return exc.value

    def run_steps(self, client_id: str, run_id: str) -> Generator[str, None, Summary]:
        """Generator yielding 'read', 'reason', 'save' checkpoints.

        Holds working memory in self.state across steps and emits a trace event
        at each one. Returns the final Summary via StopIteration.
        """
        working = self.state.get(run_id)
        working["client_id"] = client_id
        self.state.set(run_id, working)
        self.tracer.event(
            run_id, "read",
            {"client_id": client_id, "memory_snapshot": dict(working)},
        )
        yield "read"

        document = load_document(client_id, "account_note.md")
        response = self.llm.complete(summary_prompt(client_id, document))
        working = self.state.get(run_id)
        working["last_response"] = response
        self.state.set(run_id, working)
        self.tracer.event(
            run_id, "reason",
            {"response": response, "memory_snapshot": dict(working)},
        )
        yield "reason"

        working = self.state.get(run_id)
        content = format_summary(working.get("client_id", client_id), working.get("last_response", ""))
        self.store.set_summary(client_id, content)
        summary = Summary(client_id=client_id, content=content)
        self.tracer.event(
            run_id, "save",
            {"content": content, "memory_snapshot": dict(working)},
        )
        yield "save"

        return summary
