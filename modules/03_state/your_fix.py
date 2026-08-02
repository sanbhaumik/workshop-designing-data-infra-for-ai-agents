"""Module 03 — State, Memory & Recovery: your fix.

Edit ONLY this file. Two tasks:

1. `IsolatedState` -- right now it behaves exactly like the naive
   `SharedState` in nova/agent.py: every run_id sees the same dict. Fix
   `get`/`set` so each run_id has its own isolated data.

2. `run_recoverable` -- runs an agent, tolerating a simulated kill partway
   through. Right now, resuming after a kill always calls `agent.run_steps`
   again from scratch, which redoes (and duplicates) any write that already
   happened before the kill. Fix it so a resumed run doesn't redo completed
   work.
"""
from nova.agent import Agent, format_briefing_content
from nova.models import Briefing


class IsolatedState:
    """Task 1: namespace state by run_id.

    Right now this behaves exactly like SharedState -- every run_id sees the
    same dict.
    """

    def __init__(self) -> None:
        self._data: dict = {}

    def get(self, run_id: str) -> dict:
        # TODO: isolate by run_id instead of returning one shared dict
        return self._data

    def set(self, run_id: str, data: dict) -> None:
        # TODO: isolate by run_id instead of mutating one shared dict
        self._data.update(data)


def run_recoverable(agent: Agent, client_id: str, run_id: str, kill_after: str | None = None) -> Briefing | None:
    """Task 2: recover a run that was killed mid-way, without redoing completed work.

    `kill_after` simulates a crash: the run stops right after that checkpoint
    and returns None, as if the process had died. A second call with the same
    run_id (and the same `agent.state` instance) must finish the run
    correctly -- without re-triggering steps that already completed.
    """
    for checkpoint in agent.run_steps(client_id, run_id):
        if checkpoint == kill_after:
            return None
    working = agent.state.get(run_id)
    return Briefing(
        client_id=client_id,
        content=format_briefing_content(working.get("client_id", client_id), working.get("last_response", "")),
        obligations=agent.store.get_obligations(client_id),
    )
