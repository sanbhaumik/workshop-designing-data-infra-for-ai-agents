"""Transparent agent loop: retrieve -> reason -> save.

Every step is a plain method call, nothing hidden inside a framework. Working
memory lives in a plain keyed store; WHICH key each run uses is a decision the
State lab hands to the participant (`state_key`).
"""
from pathlib import Path
from typing import Callable, Generator

from nova.frozen_llm import FrozenLLM
from nova.models import Summary
from nova.store import RecordStore
from nova.trace import Tracer

# state_key(run_id, tenant) -> the key under which this run's memory is stored.
StateKey = Callable[[str, str], str]


class MemoryStore:
    """The agent's working memory: a plain dict addressed by whatever key you
    choose. It does not decide isolation -- `state_key` does. Persists within a
    process, so it also serves as the checkpoint a resumed run reads back."""

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def get(self, key: str) -> dict:
        return self._data.setdefault(key, {})

    def set(self, key: str, value: dict) -> None:
        self._data[key] = value


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
        tracer: Tracer,
        memory: MemoryStore,
        state_key: StateKey,
    ) -> None:
        self.store = store
        self.llm = llm
        self.tracer = tracer
        self.memory = memory
        self.state_key = state_key

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

        Holds working memory in self.memory under `state_key(run_id, tenant)`,
        and emits a trace event at each step. Returns the Summary via StopIteration.
        """
        key = self.state_key(run_id, client_id)

        working = self.memory.get(key)
        working["client_id"] = client_id
        self.memory.set(key, working)
        self.tracer.event(
            run_id, "read",
            {"client_id": client_id, "memory_key": key, "memory_snapshot": dict(working)},
        )
        yield "read"

        document = load_document(client_id, "account_note.md")
        response = self.llm.complete(summary_prompt(client_id, document))
        working = self.memory.get(key)
        working["last_response"] = response
        self.memory.set(key, working)
        self.tracer.event(
            run_id, "reason",
            {"response": response, "memory_key": key, "memory_snapshot": dict(working)},
        )
        yield "reason"

        working = self.memory.get(key)
        content = format_summary(working.get("client_id", client_id), working.get("last_response", ""))
        self.store.set_summary(client_id, content)
        self.tracer.event(
            run_id, "save",
            {"content": content, "memory_key": key, "memory_snapshot": dict(working)},
        )
        yield "save"

        return Summary(client_id=client_id, content=content)

    def save_from_checkpoint(self, client_id: str, run_id: str) -> Summary:
        """Resume a crashed run: save the summary from whatever memory holds under
        this run's key. If the key is the ephemeral run id and that id was reused,
        this restores the WRONG tenant's checkpoint -- the recovery trap."""
        key = self.state_key(run_id, client_id)
        working = self.memory.get(key)
        content = format_summary(working.get("client_id", client_id), working.get("last_response", ""))
        self.store.set_summary(client_id, content)
        self.tracer.event(
            run_id, "resume-save",
            {"content": content, "memory_key": key, "memory_snapshot": dict(working)},
        )
        return Summary(client_id=client_id, content=content)
