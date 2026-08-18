"""Module 03 — State, Memory & Recovery: your fix.

Edit ONLY this file. Fix `IsolatedState` so each run (each tenant) gets its own
working memory.

Right now `IsolatedState` behaves exactly like the naive `SharedState` in
nova/agent.py: every run_id sees the SAME dict. When two tenants' runs are
interleaved, one tenant's data overwrites the shared memory and leaks into the
other tenant's account summary.
"""


class IsolatedState:
    """Working memory for agent runs. Fix it to namespace by run_id."""

    def __init__(self) -> None:
        self._data: dict = {}

    def get(self, run_id: str) -> dict:
        # TODO: give each run_id its OWN dict instead of one shared dict.
        return self._data

    def set(self, run_id: str, data: dict) -> None:
        # TODO: store this run_id's data on its own, not merged into a shared dict.
        self._data.update(data)
