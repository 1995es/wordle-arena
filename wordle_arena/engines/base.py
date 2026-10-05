"""The interface of the ranking engines, and the usage and cost of each decision."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from wordle_arena.wordle import History


@dataclass(frozen=True)
class Usage:
    """The API calls, the tokens and the cost in USD of one decision."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass(frozen=True)
class Price:
    """The price of a model, in USD for each million tokens."""

    input: float
    output: float

    def usage(self, calls: int, input_tokens: int, output_tokens: int) -> Usage:
        """Return the usage with its cost."""
        cost = (input_tokens * self.input + output_tokens * self.output) / 1_000_000
        return Usage(calls, input_tokens, output_tokens, cost)


@dataclass(frozen=True)
class Pick:
    """The word that an engine selects, and the usage to select it."""

    word: str
    usage: Usage = Usage()


class RankingEngine(ABC):
    """An engine that selects the candidate that is most probably the hidden word."""

    name: str

    @abstractmethod
    def pick(self, candidates: list[str], history: History) -> Pick:
        """Return the best candidate. All the candidates agree with the feedback in the history."""
