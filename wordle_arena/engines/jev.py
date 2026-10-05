"""The ranking engine that uses Jev, the System One model of TypeSafe."""

from typesafe_sdk import Choice, RetryPolicy, TypeSafeClient

from wordle_arena.engines.base import Pick, Price, RankingEngine
from wordle_arena.prompt import QUESTION, game_state
from wordle_arena.wordle import History

PRICE = Price(input=0.042, output=0.0)  # Output tokens are free.
MAX_OPTIONS = 255  # The TypeSafe limit of options in one Choice question.


class JevRankingEngine(RankingEngine):
    """Ask Jev which candidate is most probably the hidden word.

    One Choice question accepts a maximum of MAX_OPTIONS options. If there are more candidates, the
    engine asks one question for each group of candidates, in one request. Then it asks a
    final question with the best words of each group.
    """

    name = "jev"

    def __init__(self, client: TypeSafeClient | None = None) -> None:
        """Use the client, or make a client without retries. The resolver does the retries."""
        self.client = client or TypeSafeClient(retry=RetryPolicy(max_retries=0))

    def pick(self, candidates: list[str], history: History) -> Pick:
        """Return the candidate with the highest probability."""
        state = game_state(history)
        groups = [candidates[i : i + MAX_OPTIONS] for i in range(0, len(candidates), MAX_OPTIONS)]
        responses = [self._ask(state, groups)]
        if len(groups) > 1:
            keep = MAX_OPTIONS // len(groups)
            ranked = (sorted(p, key=p.get, reverse=True) for p in _probabilities(responses[0]))
            responses.append(self._ask(state, [[w for words in ranked for w in words[:keep]]]))
        best = _probabilities(responses[-1])[0]
        input_tokens = sum(r.usage.input_tokens or 0 for r in responses)
        output_tokens = sum(r.usage.output_tokens or 0 for r in responses)
        return Pick(max(best, key=best.get), PRICE.usage(len(responses), input_tokens, output_tokens))

    def _ask(self, state: dict, groups: list[list[str]]):
        """Ask one Choice question for each group, in one request."""
        questions = {
            f"group_{i}": Choice(instructions=QUESTION, criteria=dict.fromkeys(group))
            for i, group in enumerate(groups)
        }
        return self.client.system_one(state=state, questions=questions)


def _probabilities(response) -> list[dict[str, float]]:
    """Return the probabilities of each group, in the order of the groups."""
    return [response.choices[f"group_{i}"].probabilities for i in range(len(response.choices))]
