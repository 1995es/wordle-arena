"""The report: Markdown tables that compare the results of the engines.

Definitions:
    Score: the number of guesses, with 7 for a game that is not solved. Lower is better.
    Decision: a turn in which the engine selects the word. The opener and a single candidate are not
        decisions.
    Hits: the decisions in which the engine selects the hidden word.
    Chance: the hits that a random selection gets on average, that is the sum of 1 / candidates.
    Lift: hits / chance. A lift of 1 is the same as random. A higher lift shows that the engine knows
        which candidates are common Spanish words.
"""

import random
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path

from wordle_arena.records import Game, Turn, load_games
from wordle_arena.wordle import MAX_ATTEMPTS

OUTCOMES = [*range(1, MAX_ATTEMPTS + 1), "X"]
RESAMPLES = 5000


def score(game: Game) -> int:
    """Return the number of guesses of the game, or 7 if the game is not solved."""
    return game.attempts if game.solved else MAX_ATTEMPTS + 1


def decisions(game: Game) -> list[Turn]:
    """Return the turns in which the engine selects the word."""
    return [turn for turn in game.turns[1:] if turn.candidates > 1]


def hits_and_chance(games: Sequence[Game]) -> tuple[int, float]:
    """Return the hits of the games and the hits that a random selection gets on average."""
    turns = [(turn, game.secret) for game in games for turn in decisions(game)]
    return sum(turn.guess == secret for turn, secret in turns), sum(1 / turn.candidates for turn, _ in turns)


def lift(games: Sequence[Game]) -> float:
    """Return hits / chance."""
    hits, chance = hits_and_chance(games)
    return hits / chance if chance else 0.0


def confidence_interval[T](statistic: Callable[[list[T]], float], items: list[T]) -> tuple[float, float]:
    """Return the 95% confidence interval of a statistic. Resample the items with replacement (bootstrap)."""
    rng = random.Random(0)
    values = sorted(statistic(rng.choices(items, k=len(items))) for _ in range(RESAMPLES))
    return values[int(0.025 * RESAMPLES)], values[int(0.975 * RESAMPLES) - 1]


def mean(values: Sequence[float]) -> float:
    """Return the average of the values."""
    return sum(values) / len(values)


def row(cells: list[str]) -> str:
    """Return one row of a Markdown table."""
    return "| " + " | ".join(cells) + " |"


def header(columns: list[str]) -> list[str]:
    """Return the first two rows of a Markdown table."""
    return [row(columns), "|---" * len(columns) + "|"]


def results_table(runs: dict[str, list[Game]]) -> list[str]:
    """Return a table with the solved games, the guesses, the lift, the cost and the time of each engine."""
    columns = ["Engine", "Games", "Solved", "Score", "Avg. guesses (solved)", *map(str, OUTCOMES)]
    lines = header(columns + ["Hits (chance)", "Lift [95% CI]", "Cost (USD)", "Cost/game", "Sec/decision"])
    for engine, games in runs.items():
        wins = [game.attempts for game in games if game.solved]
        counts = Counter(wins) + Counter({"X": len(games) - len(wins)})
        hits, chance = hits_and_chance(games)
        low, high = confidence_interval(lift, games)
        cost = sum(turn.cost_usd for game in games for turn in game.turns)
        seconds = [turn.seconds for game in games for turn in decisions(game)]
        cells = [
            engine,
            str(len(games)),
            f"{len(wins) / len(games):.1%}",
            f"{mean([score(g) for g in games]):.2f}",
        ]
        cells += [f"{mean(wins):.2f}" if wins else "-", *(str(counts[key]) for key in OUTCOMES)]
        cells += [f"{hits} ({chance:.1f})", f"{lift(games):.2f} [{low:.2f}, {high:.2f}]"]
        cells += [f"{cost:.4f}", f"{cost / len(games):.5f}", f"{mean(seconds):.2f}" if seconds else "-"]
        lines.append(row(cells))
    return lines


def paired_table(runs: dict[str, list[Game]], reference: str) -> list[str]:
    """Return a table that compares each engine with the reference engine on the same hidden words."""
    base = {game.secret: score(game) for game in runs[reference]}
    lines = [
        f"Paired comparison with {reference}: the same hidden words. A negative difference is better.",
        "",
    ]
    lines += header(["Engine", "Games", "Better", "Same", "Worse", "Score difference [95% CI]"])
    for engine, games in runs.items():
        if engine == reference:
            continue
        differences = [score(game) - base[game.secret] for game in games if game.secret in base]
        low, high = confidence_interval(mean, differences)
        counts = [
            sum(d < 0 for d in differences),
            sum(d == 0 for d in differences),
            sum(d > 0 for d in differences),
        ]
        cells = [
            engine,
            str(len(differences)),
            *map(str, counts),
            f"{mean(differences):+.2f} [{low:+.2f}, {high:+.2f}]",
        ]
        lines.append(row(cells))
    return lines


def table(paths: list[Path], reference: str = "random") -> str:
    """Return the report of the results files. All files must use the same opener and different engines.

    If one file has the reference engine, the report also compares each engine with it.
    """
    loaded = [load_games(path) for path in paths]
    openers = {game.opener for games in loaded for game in games}
    if len(openers) != 1:
        raise ValueError(f"The files use different openers: {sorted(openers)}. Compare only one opener.")
    runs = {games[0].engine: games for games in loaded}
    if len(runs) != len(loaded):
        raise ValueError("Two files have the same engine. Give one file for each engine.")
    lines = [f"Opener: {openers.pop()}", "", *results_table(runs)]
    if reference in runs and len(runs) > 1:
        lines += ["", *paired_table(runs, reference)]
    return "\n".join(lines)
