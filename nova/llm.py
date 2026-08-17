"""LLM factory: pick the backend by the NOVA_LLM environment variable.

    NOVA_LLM=ollama  (default)  -> real local model, used by the lab runners
    NOVA_LLM=frozen             -> fixture-backed FrozenLLM, used by the tests

The pytest suite forces `frozen` so the fail-naive / pass-reference contract
stays deterministic and offline; it never depends on a running model.
"""
import os
from pathlib import Path

from nova.frozen_llm import FrozenLLM
from nova.ollama_llm import OllamaLLM

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def get_llm(fixtures_dir: Path | None = None):
    """Return the LLM backend selected by NOVA_LLM (default 'ollama')."""
    backend = os.environ.get("NOVA_LLM", "ollama").lower()
    if backend == "frozen":
        return FrozenLLM(fixtures_dir or (FIXTURES / "llm_responses"))
    if backend == "ollama":
        return OllamaLLM()
    raise ValueError(f"unknown NOVA_LLM backend {backend!r} (use 'ollama' or 'frozen')")
