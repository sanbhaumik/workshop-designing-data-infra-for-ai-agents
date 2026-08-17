"""Real local LLM client, backed by a running Ollama server.

Talks to Ollama's HTTP API on localhost using only the standard library, so it
adds no dependency of its own. This is a *real* model call -- unlike FrozenLLM
its output is non-deterministic, which is exactly what the Write lab needs.

Config via environment:
    OLLAMA_HOST   default http://localhost:11434
    OLLAMA_MODEL  default llama3.2:1b
"""
import json
import os
import urllib.error
import urllib.request

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2:1b"


class OllamaError(Exception):
    """Raised when the Ollama server can't be reached or returns an error."""


class OllamaLLM:
    """A real local model. `complete(prompt)` returns freshly generated text."""

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
        temperature: float = 0.8,
    ) -> None:
        self.model = model or os.environ.get("OLLAMA_MODEL", DEFAULT_MODEL)
        self.host = (host or os.environ.get("OLLAMA_HOST", DEFAULT_HOST)).rstrip("/")
        # OLLAMA_TEMPERATURE lets facilitators dial how divergent two runs look.
        self.temperature = float(os.environ.get("OLLAMA_TEMPERATURE", temperature))

    def complete(self, prompt: str) -> str:
        """Generate a completion for `prompt`. Raises OllamaError on failure.

        Uses a non-zero temperature by default so two runs of the same prompt
        produce genuinely different wordings -- the real-model version of the
        Write lab's core phenomenon.
        """
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": self.temperature},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise OllamaError(
                f"could not reach Ollama at {self.host} ({exc}). "
                "Is `ollama serve` running and the model pulled? See setup.sh."
            ) from exc
        return body.get("response", "").strip()
