"""Fixture-backed fake model. To participant code it behaves like a model;
underneath it's a dictionary keyed by a hash of the prompt.
"""
import hashlib
import json
import os
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
                "record one with NOVA_LIVE_LLM=1 or add the fixture by hand"
            )
        data = json.loads(path.read_text())
        return data["response"]

    def record_live(self, prompt: str) -> str:
        """Build-time only: call the real model and persist the fixture as JSON.

        Gated behind NOVA_LIVE_LLM=1 and imports the live client lazily so its
        absence never breaks anything at workshop runtime.
        """
        if os.environ.get("NOVA_LIVE_LLM") != "1":
            raise RuntimeError("record_live requires NOVA_LIVE_LLM=1")

        import google.generativeai as genai  # lazy import: optional dependency

        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash")
        response_text = model.generate_content(prompt).text

        self.fixtures_dir.mkdir(parents=True, exist_ok=True)
        path = self.fixtures_dir / f"{_key(prompt)}.json"
        path.write_text(json.dumps({"prompt": prompt, "response": response_text}, indent=2))
        return response_text
