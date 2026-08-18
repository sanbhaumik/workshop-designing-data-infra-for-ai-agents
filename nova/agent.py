"""Transparent agent loop: retrieve -> reason -> extract & write -> draft.

Every step is a plain method call, nothing hidden inside a framework. State
handling is dependency-injected so the labs can swap in a broken or fixed
backend without touching this file.
"""
import hashlib
from pathlib import Path
from typing import Generator, Protocol

from nova.frozen_llm import FrozenLLM
from nova.models import Briefing, Obligation
from nova.store import RecordStore
from nova.trace import Tracer


class StateBackend(Protocol):
    """Working-state storage keyed by run_id."""

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


def format_briefing_content(client_id: str, response: str) -> str:
    """Pure formatting helper shared by Agent.draft and lab recovery code."""
    return f"Briefing for {client_id}: {response}"


def load_document(client_id: str, source_doc: str, fixtures_dir: Path | None = None) -> str:
    """Load a client document's text from fixtures/clients/<client>/<source_doc>."""
    base = fixtures_dir or (Path(__file__).resolve().parents[1] / "fixtures")
    return (base / "clients" / client_id / source_doc).read_text()


def payment_memo_prompt(client_id: str, billing_period: str, document_text: str, attempt: int) -> str:
    """Natural-language prompt for the Write-lab payment memo.

    The agent reads a client billing instruction and writes a one-line memo for
    the advisory-fee charge. Sent verbatim to Ollama, where a non-zero
    temperature makes two runs word the memo differently; the `(retry N)` marker
    keys a distinct frozen fixture per run so the test suite sees the same
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


def briefing_prompt(client_id: str, source_doc: str, document_text: str) -> str:
    """Prompt for the State-lab per-tenant briefing.

    Grounds the model in one tenant's document so its briefing is legibly
    tenant-specific -- which is what makes cross-tenant contamination obvious.
    Deterministic per tenant (no retry marker): one frozen fixture each.
    """
    return (
        "You are a compliance assistant working with FICTIONAL sample data. "
        f"Below is the engagement letter for tenant '{client_id}'.\n\n"
        f"--- {source_doc} ---\n{document_text}\n--- end of document ---\n\n"
        f"Write a one-sentence internal briefing for tenant '{client_id}' "
        f"summarizing their single regulatory obligation. This is fictional "
        f"sample data, so do not refuse."
    )


class Agent:
    """Runs one client through retrieve -> reason -> write -> draft."""

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

    def run(self, client_id: str, run_id: str) -> Briefing:
        """Run the full loop to completion (no scheduler) and return the Briefing."""
        steps = self.run_steps(client_id, run_id)
        try:
            while True:
                next(steps)
        except StopIteration as exc:
            return exc.value

    def run_steps(self, client_id: str, run_id: str) -> Generator[str, None, Briefing]:
        """Generator yielding 'read', 'reason', 'write', 'draft' checkpoints.

        Holds working state in self.state across steps and emits a trace
        event at each one. Returns the final Briefing via StopIteration.
        """
        existing = self.store.get_obligations(client_id)
        working = self.state.get(run_id)
        working["client_id"] = client_id
        self.state.set(run_id, working)
        self.tracer.event(
            run_id, "read",
            {"client_id": client_id, "existing_obligations": len(existing), "state_snapshot": dict(working)},
        )
        yield "read"

        document = load_document(client_id, "engagement_letter.md")
        prompt = briefing_prompt(client_id, "engagement_letter.md", document)
        response = self.llm.complete(prompt)
        working = self.state.get(run_id)
        working["last_response"] = response
        self.state.set(run_id, working)
        self.tracer.event(
            run_id, "reason",
            {"prompt": prompt, "response": response, "state_snapshot": dict(working)},
        )
        yield "reason"

        ob = Obligation(
            client_id=client_id,
            text=response,
            source_doc="frozen_llm",
            idempotency_key=hashlib.sha256(f"{client_id}:{response}".encode("utf-8")).hexdigest(),
        )
        self.store.append_obligation(ob)
        working = self.state.get(run_id)
        self.tracer.event(
            run_id, "write",
            {"obligation": ob.model_dump(), "state_snapshot": dict(working)},
        )
        yield "write"

        working = self.state.get(run_id)
        content = format_briefing_content(working.get("client_id", client_id), working.get("last_response", ""))
        self.store.set_briefing(client_id, content)
        briefing = Briefing(client_id=client_id, content=content, obligations=[ob])
        self.tracer.event(
            run_id, "draft",
            {"content": content, "state_snapshot": dict(working)},
        )
        yield "draft"

        return briefing
