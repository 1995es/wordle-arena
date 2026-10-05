"""The ranking engines. Each engine selects the next guess from the candidates."""

from wordle_arena.engines.base import Pick, Price, RankingEngine, Usage
from wordle_arena.engines.baseline import RandomRankingEngine
from wordle_arena.engines.claude import ClaudeRankingEngine
from wordle_arena.engines.jev import JevRankingEngine

ENGINES: dict[str, type[RankingEngine]] = {
    "jev": JevRankingEngine,
    "claude": ClaudeRankingEngine,
    "random": RandomRankingEngine,
}

__all__ = [
    "ENGINES",
    "ClaudeRankingEngine",
    "JevRankingEngine",
    "Pick",
    "Price",
    "RandomRankingEngine",
    "RankingEngine",
    "Usage",
]
