"""Deterministic cooperative scheduler. Simulates concurrency by stepping two
generator-based agent runs through a fixed, scripted interleaving -- no real
threads, no time.sleep, no luck. Identical inputs + script => identical
outcome, every run, on every machine.
"""
from typing import Any, Callable, Generator

RunFactory = Callable[[], Generator[str, None, Any]]


class Scheduler:
    """Steps two runs ("A" and "B") through a fixed sequence of checkpoints."""

    def __init__(self, script: list[str]) -> None:
        """script e.g. ['A:read', 'B:read', 'A:write', 'B:write'] -- the exact
        interleaving to apply, identically, on every run.
        """
        self.script = script

    def run(self, run_a: RunFactory, run_b: RunFactory) -> tuple[Any, Any]:
        """Step both runs to completion following the script.

        Each factory is called once to create its generator. The generator
        must yield a checkpoint label (e.g. "read", "write") at each point it
        is willing to be paused, and `return` its final result.
        """
        generators = {"A": run_a(), "B": run_b()}
        results: dict[str, Any] = {"A": None, "B": None}
        done = {"A": False, "B": False}

        for step in self.script:
            label, checkpoint = step.split(":", 1)
            if done[label]:
                continue
            self._advance_to(generators[label], checkpoint, label, results, done)

        for label, gen in generators.items():
            if not done[label]:
                self._drain(gen, label, results, done)

        return results["A"], results["B"]

    @staticmethod
    def _advance_to(gen, checkpoint: str, label: str, results: dict, done: dict) -> None:
        try:
            while True:
                yielded = next(gen)
                if yielded == checkpoint:
                    return
        except StopIteration as exc:
            results[label] = exc.value
            done[label] = True

    @staticmethod
    def _drain(gen, label: str, results: dict, done: dict) -> None:
        try:
            while True:
                next(gen)
        except StopIteration as exc:
            results[label] = exc.value
            done[label] = True
