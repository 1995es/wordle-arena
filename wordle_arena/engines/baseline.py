"""The baseline engine: it selects a random candidate."""

import random

from wordle_arena.engines.base import Pick, RankingEngine
from wordle_arena.wordle import History


class RandomRankingEngine(RankingEngine):
    """Select a random candidate. This engine shows the minimum result that an AI engine must improve.

    The same seed and history always give the same word, also when games run in parallel.
    """

    name = "random"

    def __init__(self, seed: int = 0) -> None:
        """Keep the seed."""
        self.seed = seed

    def pick(self, candidates: list[str], history: History) -> Pick:
        """Return a random candidate."""
        return Pick(random.Random(f"{self.seed}:{history}").choice(candidates))
