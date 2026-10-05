"""The ranking engine that uses Claude Opus 5.5, the large language model of Anthropic."""

import json

from anthropic import Anthropic

from wordle_arena.engines.base import Pick, Price, RankingEngine
from wordle_arena.prompt import QUESTION, game_state
from wordle_arena.wordle import History, normalize

MODEL = "claude-opus-5-5"
EFFORT = "medium"
PRICE = Price(input=4.0, output=20.0)  # Output tokens include the thinking tokens.
SCHEMA = {
    "type": "object",
    "properties": {"word": {"type": "string"}},
    "required": ["word"],
    "additionalProperties": False,
}


class ClaudeRankingEngine(RankingEngine):
    """Ask Claude which candidate is most probably the hidden word.

    Claude gets the same game state and question as Jev. Claude replies with one word in JSON.
    """

    name = MODEL

    def __init__(self, client: Anthropic | None = None) -> None:
        """Use the client, or make a client without retries. The resolver does the retries."""
        self.client = client or Anthropic(max_retries=0)

    def pick(self, candidates: list[str], history: History) -> Pick:
        """Return the candidate that Claude selects."""
        state = json.dumps(game_state(history), ensure_ascii=False, indent=2)
        question = json.dumps(QUESTION, ensure_ascii=False, indent=2)
        prompt = f"{state}\n\n{question}\n\nOptions: {', '.join(candidates)}"
        response = self.client.messages.create(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": prompt}],
        )
        if response.stop_reason != "end_turn":
            raise RuntimeError(f"Claude stopped with the reason {response.stop_reason!r}.")
        text = next(block.text for block in response.content if block.type == "text")
        usage = PRICE.usage(1, response.usage.input_tokens, response.usage.output_tokens)
        return Pick(normalize(json.loads(text)["word"]), usage)
