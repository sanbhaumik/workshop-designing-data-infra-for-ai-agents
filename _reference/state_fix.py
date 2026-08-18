"""Reference solution for Module 03 — validates test_state.py.

Not shipped to participants and never merged into your_fix.py.
"""


class IsolatedState:
    """Namespaces working memory by run_id so concurrent runs never see each other's data."""

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def get(self, run_id: str) -> dict:
        return self._data.setdefault(run_id, {})

    def set(self, run_id: str, data: dict) -> None:
        self._data[run_id] = data
