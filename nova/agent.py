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

        prompt = f"client:{client_id}"
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
