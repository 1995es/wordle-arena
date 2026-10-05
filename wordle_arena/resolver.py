"""The resolver selects the next guess. It gets its ranking engine through dependency injection."""

import time
from dataclasses import dataclass

from tenacity import retry, stop_after_attempt, wait_exponential

from wordle_arena.engines import Pick, RankingEngine, Usage
from wordle_arena.wordle import History, candidates

OPENER = "SERIO"
MAX_TRIES = 3


@dataclass(frozen=True)
class Guess:
    """The next guess, the number of candidates for it, and the usage and time to select it."""

    word: str
    candidates: int
    usage: Usage = Usage()
    seconds: float = 0.0


class Resolver:
    """Find the candidates, then let the engine select one of them.

    The first guess is always the opener. If only one candidate remains, the resolver plays it.
    The engine does not select these guesses, thus they have no cost.
    """

    def __init__(self, engine: RankingEngine, words: list[str], opener: str = OPENER) -> None:
        """Keep the engine, the valid words and the first guess."""
        self.engine, self.words, self.opener = engine, words, opener

    def guess(self, history: History) -> Guess:
        """Return the next guess for the history."""
        if not history:
            return Guess(self.opener, len(self.words))
        options = candidates(self.words, history)
        if not options:
            raise ValueError("No word agrees with the feedback.")
        if len(options) == 1:
            return Guess(options[0], 1)
        start = time.perf_counter()
        pick = self._pick(options, history)
        return Guess(pick.word, len(options), pick.usage, time.perf_counter() - start)

    @retry(stop=stop_after_attempt(MAX_TRIES), wait=wait_exponential(max=30), reraise=True)
    def _pick(self, options: list[str], history: History) -> Pick:
        """Ask the engine. Try again if the engine fails or selects a word that is not a candidate."""
        pick = self.engine.pick(options, history)
        if pick.word not in options:
            raise ValueError(f"The engine selected {pick.word!r}, but it is not a candidate.")
        return pick
