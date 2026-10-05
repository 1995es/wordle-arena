import pytest
from tenacity import wait_none

from wordle_arena.engines import Pick, RankingEngine, Usage
from wordle_arena.resolver import Resolver

WORDS = ["SERIO", "ROSAS", "ROJAS", "ROLAS", "GATOS"]


@pytest.fixture(autouse=True)
def no_wait(monkeypatch):
    monkeypatch.setattr(Resolver._pick.retry, "wait", wait_none())


class FakeEngine(RankingEngine):
    """Give the answers in order. An exception in the list is raised."""

    name = "fake"

    def __init__(self, *answers):
        self.answers, self.calls = list(answers), 0

    def pick(self, candidates, history):
        self.calls += 1
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_first_guess_is_the_opener_without_the_engine():
    engine = FakeEngine()
    assert Resolver(engine, WORDS).guess([]).word == "SERIO"
    assert engine.calls == 0


def test_single_candidate_is_played_without_the_engine():
    engine = FakeEngine()
    guess = Resolver(engine, WORDS).guess([("ROLAS", "GGXGG"), ("ROJAS", "GGXGG")])
    assert (guess.word, guess.candidates, guess.usage, engine.calls) == ("ROSAS", 1, Usage(), 0)


def test_engine_selects_among_the_candidates():
    usage = Usage(1, 10, 5, 0.1)
    engine = FakeEngine(Pick("ROLAS", usage))
    guess = Resolver(engine, WORDS).guess([("SERIO", "YXYXY")])
    assert (guess.word, guess.candidates, guess.usage) == ("ROLAS", 3, usage)


def test_engine_errors_are_retried():
    engine = FakeEngine(RuntimeError("API error"), Pick("NOPE"), Pick("ROSAS"))
    assert Resolver(engine, WORDS).guess([("SERIO", "YXYXY")]).word == "ROSAS"
    assert engine.calls == 3


def test_resolver_stops_after_three_failures():
    engine = FakeEngine(*[RuntimeError("API error")] * 4)
    with pytest.raises(RuntimeError):
        Resolver(engine, WORDS).guess([("SERIO", "YXYXY")])
    assert engine.calls == 3


def test_wrong_feedback_gives_an_error():
    with pytest.raises(ValueError, match="No word"):
        Resolver(FakeEngine(), WORDS).guess([("SERIO", "GGGGX")])
