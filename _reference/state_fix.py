"""Reference solution for Module 03 — validates test_state.py.

Not shipped to participants and never merged into your_fix.py.
"""
from nova.agent import Agent, format_briefing_content
from nova.models import Briefing


class IsolatedState:
    """Namespaces state by run_id so concurrent runs never see each other's data."""

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def get(self, run_id: str) -> dict:
        return self._data.setdefault(run_id, {})

    def set(self, run_id: str, data: dict) -> None:
        self._data[run_id] = data


def run_recoverable(agent: Agent, client_id: str, run_id: str, kill_after: str | None = None) -> Briefing | None:
    """Recover a run that was killed mid-way, without redoing completed work.

    A checkpoint marker is saved into `agent.state` after every step that
    completes. On a later call for the same run_id, if the write already
    happened, skip re-running the generator entirely and finish the draft
    from what's already recorded.
    """
    working = agent.state.get(run_id)
    if working.get("last_checkpoint") == "write":
        return Briefing(
            client_id=client_id,
            content=format_briefing_content(working.get("client_id", client_id), working.get("last_response", "")),
            obligations=agent.store.get_obligations(client_id),
        )

    for checkpoint in agent.run_steps(client_id, run_id):
        working = agent.state.get(run_id)
        working["last_checkpoint"] = checkpoint
        agent.state.set(run_id, working)
        if checkpoint == kill_after:
            return None

    working = agent.state.get(run_id)
    return Briefing(
        client_id=client_id,
        content=format_briefing_content(working.get("client_id", client_id), working.get("last_response", "")),
        obligations=agent.store.get_obligations(client_id),
    )
