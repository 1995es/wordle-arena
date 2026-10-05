from types import SimpleNamespace

import pytest

from wordle_arena.engines import ClaudeRankingEngine, JevRankingEngine, Price, RandomRankingEngine, Usage
from wordle_arena.engines.jev import MAX_OPTIONS
from wordle_arena.wordle import load_words

HISTORY = [("RATOS", "GYXYG")]


def test_price_gives_cost_in_usd():
    assert Price(input=4.0, output=20.0).usage(1, 1_000, 500) == Usage(1, 1_000, 500, 0.014)


class FakeTypeSafe:
    """Give a higher probability to the words that come first in the preference list."""

    def __init__(self, preference):
        self.preference, self.requests = preference, []

    def system_one(self, state, questions):
        self.requests.append(questions)
        choices = {}
        for name, question in questions.items():
            weights = {w: 1 / (1 + self.preference.index(w)) for w in question.criteria}
            total = sum(weights.values())
            choices[name] = SimpleNamespace(probabilities={w: v / total for w, v in weights.items()})
        usage = SimpleNamespace(input_tokens=1_000_000, output_tokens=10)
        return SimpleNamespace(choices=choices, usage=usage)


def test_jev_picks_most_probable_word():
    client = FakeTypeSafe(["ROSAS", "ROJAS", "ROLAS"])
    pick = JevRankingEngine(client).pick(["ROLAS", "ROJAS", "ROSAS"], HISTORY)
    assert pick.word == "ROSAS"
    assert pick.usage == Usage(1, 1_000_000, 10, 0.042)
    assert len(client.requests) == 1


def test_jev_splits_many_candidates_and_asks_a_final_question():
    words = load_words()[:600]
    client = FakeTypeSafe(list(reversed(words)))
    pick = JevRankingEngine(client).pick(words, HISTORY)
    first, final = client.requests
    assert len(first) == 3 and all(len(q.criteria) <= MAX_OPTIONS for q in first.values())
    assert len(final["group_0"].criteria) <= MAX_OPTIONS
    assert pick.word == words[-1]
    assert pick.usage.calls == 2


def fake_anthropic(text, stop_reason="end_turn"):
    """Return a fake Anthropic client that keeps the request and gives the text as the answer."""
    requests = []

    def create(**request):
        requests.append(request)
        content = [SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=text)]
        usage = SimpleNamespace(input_tokens=1_000, output_tokens=500)
        return SimpleNamespace(stop_reason=stop_reason, content=content, usage=usage)

    return SimpleNamespace(messages=SimpleNamespace(create=create)), requests


def test_claude_picks_the_word_in_its_answer():
    client, requests = fake_anthropic('{"word": "rosas"}')
    pick = ClaudeRankingEngine(client).pick(["ROLAS", "ROSAS"], HISTORY)
    assert pick.word == "ROSAS"
    assert pick.usage == Usage(1, 1_000, 500, pytest.approx(0.014))
    assert requests[0]["model"] == "claude-opus-5-5"
    assert requests[0]["output_config"]["effort"] == "medium"
    assert "ROLAS, ROSAS" in requests[0]["messages"][0]["content"]


def test_claude_fails_when_it_does_not_finish():
    client, _ = fake_anthropic("", stop_reason="refusal")
    with pytest.raises(RuntimeError, match="refusal"):
        ClaudeRankingEngine(client).pick(["ROLAS", "ROSAS"], HISTORY)


def test_random_engine_is_repeatable():
    words = ["ROLAS", "ROSAS", "ROJAS"]
    picks = {RandomRankingEngine(seed=1).pick(words, HISTORY).word for _ in range(5)}
    assert len(picks) == 1 and picks <= set(words)
