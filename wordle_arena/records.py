"""The results files: each line is one game in JSON. The arena writes the files and the report reads them."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True)
class Turn:
    """One guess, its feedback, the number of candidates, and the time and usage to select the guess."""

    guess: str
    feedback: str
    candidates: int
    seconds: float = 0.0
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass(frozen=True)
class Game:
    """One game of an engine: the hidden word, the result and each turn."""

    engine: str
    opener: str
    secret: str
    solved: bool
    attempts: int
    turns: list[Turn]


def load_games(path: Path) -> list[Game]:
    """Return the games in a results file."""
    games = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    return [Game(**game | {"turns": [Turn(**turn) for turn in game["turns"]]}) for game in games]


def append_game(file: TextIO, game: Game) -> None:
    """Write the game as one line at the end of the file."""
    file.write(json.dumps(asdict(game), ensure_ascii=False) + "\n")
    file.flush()
