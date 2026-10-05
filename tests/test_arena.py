import json

import pytest

from wordle_arena import arena, report
from wordle_arena.engines import RandomRankingEngine
from wordle_arena.records import Game, Turn, append_game, load_games
from wordle_arena.resolver import Resolver

WORDS = ["SERIO", "ROSAS", "ROJAS", "ROLAS", "GATOS", "PATOS"]


@pytest.fixture
def resolver():
    return Resolver(RandomRankingEngine(), WORDS)


def test_play_solves_the_game_and_records_each_turn(resolver):
    game = arena.play(resolver, "ROJAS")
    assert game.solved and game.attempts == len(game.turns)
    assert game.turns[0] == Turn("SERIO", "YXYXY", len(WORDS))
    assert game.turns[-1].feedback == "GGGGG"


def test_run_saves_each_game_and_continues_a_stopped_run(resolver, tmp_path, capsys):
    out = tmp_path / "results" / "random.jsonl"
    arena.run(resolver, ["ROSAS", "GATOS"], out)
    arena.run(resolver, ["ROSAS", "GATOS", "PATOS"], out, workers=2)
    secrets = [json.loads(line)["secret"] for line in out.read_text().splitlines()]
    assert sorted(secrets) == ["GATOS", "PATOS", "ROSAS"]
    assert "[3/3] PATOS" in capsys.readouterr().out


def test_load_games_reads_the_games_that_play_writes(resolver, tmp_path):
    out = tmp_path / "random.jsonl"
    arena.run(resolver, ["ROSAS"], out)
    assert load_games(out) == [arena.play(resolver, "ROSAS")]


def make_game(secret, guesses, candidates, engine="fake"):
    """Return a game with the guesses. The candidates are the numbers of candidates for each guess."""
    turns = [
        Turn(g, "GGGGG" if g == secret else "XXXXX", n) for g, n in zip(guesses, candidates, strict=True)
    ]
    return Game(engine, "SERIO", secret, guesses[-1] == secret, len(guesses), turns)


def test_score_counts_a_lost_game_as_seven():
    assert report.score(make_game("ROSAS", ["SERIO", "ROSAS"], [100, 10])) == 2
    assert report.score(make_game("ROSAS", ["SERIO"] * 6, [100] * 6)) == 7


def test_lift_compares_hits_with_chance():
    # The opener and the single candidate are not decisions. Chance is 1/4 + 1/2 + 1/4 = 1.
    games = [
        make_game("ROSAS", ["SERIO", "ROJAS", "ROSAS"], [100, 4, 2]),
        make_game("GATOS", ["SERIO", "GATOS"], [100, 4]),
        make_game("PATOS", ["SERIO", "PATOS"], [100, 1]),
    ]
    assert report.hits_and_chance(games) == (2, 1.0)
    assert report.lift(games) == 2.0


def test_report_compares_engines_with_the_reference(resolver, tmp_path):
    arena.run(resolver, WORDS[1:], tmp_path / "random.jsonl")
    smart = [make_game(secret, ["SERIO", secret], [100, 5], engine="smart") for secret in WORDS[1:]]
    with (tmp_path / "smart.jsonl").open("w") as file:
        for game in smart:
            append_game(file, game)
    lines = report.table([tmp_path / "random.jsonl", tmp_path / "smart.jsonl"]).splitlines()
    assert lines[0] == "Opener: SERIO"
    assert lines[4].startswith("| random | 5 | 100.0% |")
    assert lines[5].startswith("| smart | 5 | 100.0% | 2.00 | 2.00 |")
    assert "| 5 (1.0) | 5.00 [5.00, 5.00] |" in lines[5]
    assert lines[-1].startswith("| smart | 5 | ")
    assert "Paired comparison with random" in report.table(
        [tmp_path / "smart.jsonl", tmp_path / "random.jsonl"]
    )


def test_report_rejects_two_files_of_one_engine(resolver, tmp_path):
    for name in ("a", "b"):
        arena.run(resolver, ["ROSAS"], tmp_path / f"{name}.jsonl")
    with pytest.raises(ValueError, match="same engine"):
        report.table(sorted(tmp_path.glob("*.jsonl")))


def test_report_rejects_different_openers(tmp_path):
    for opener in ("SERIO", "GATOS"):
        arena.run(Resolver(RandomRankingEngine(), WORDS, opener), ["ROSAS"], tmp_path / f"{opener}.jsonl")
    with pytest.raises(ValueError, match="different openers"):
        report.table(sorted(tmp_path.glob("*.jsonl")))
