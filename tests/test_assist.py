from wordle_arena.assist import play_with_help
from wordle_arena.engines import RandomRankingEngine
from wordle_arena.resolver import Resolver


def test_assist_suggests_guesses_until_the_game_is_solved(monkeypatch, capsys):
    answers = iter(["", "bad", "YXYXY", "rosas", "GGGGG"])  # "" plays the suggestion; "bad" is asked again.
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    play_with_help(Resolver(RandomRankingEngine(), ["SERIO", "ROSAS", "GATOS"]))
    out = capsys.readouterr().out
    assert "The answer is not valid." in out
    assert out.endswith("Solved.\n")
