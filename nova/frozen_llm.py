"""Fixture-backed fake model. To participant code it behaves like a model;
underneath it's a dictionary keyed by a hash of the prompt.

The fixtures are real outputs recorded once from the local Ollama model. To
re-record after a prompt change, run against a live Ollama (see git history for
the recorder) or set NOVA_LLM=ollama.
"""
import hashlib
import json
from pathlib import Path


class FixtureMissing(Exception):
    """Raised when no recorded response exists for a given prompt."""


def _key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


class FrozenLLM:
    """Returns a pre-recorded response looked up by sha256(prompt)."""

    def __init__(self, fixtures_dir: Path) -> None:
        self.fixtures_dir = Path(fixtures_dir)

    def complete(self, prompt: str) -> str:
        """Return the frozen response for `prompt`. Raises FixtureMissing if absent."""
        key = _key(prompt)
        path = self.fixtures_dir / f"{key}.json"
        if not path.exists():
            raise FixtureMissing(
                f"no frozen response for prompt hash {key!r} (expected {path}); "
                "re-record fixtures against a live Ollama, or run with NOVA_LLM=ollama"
            )
        data = json.loads(path.read_text())
        return data["response"]
