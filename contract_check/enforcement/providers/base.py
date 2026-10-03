"""Portable provider contract; provider text remains an unapproved hypothesis."""

from typing import Protocol


class ModelProvider(Protocol):
    def propose(self, question: dict, authorities: list[dict]) -> dict:
        """Return supporting, opposing, and unknowns; never a legal probability."""
