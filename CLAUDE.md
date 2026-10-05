# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A public benchmark that plays the same Spanish Wordle games with different AI engines (TypeSafe Jev, Claude Opus 5.5, a random baseline) and compares solve rate, guesses, cost and time. Python 3.14, Poetry, package `wordle_arena/` at the root. API keys come from `.env` (see `.env.template`).

## Commands

```bash
poetry install
poetry run pytest                                      # all tests (no API calls, no keys needed)
poetry run pytest tests/test_wordle.py::test_score     # one test
poetry run ruff check . && poetry run ruff format --check .
poetry run wordle-arena run random --games 5 --out /tmp/r.jsonl   # free smoke run
poetry run wordle-arena report results/*.jsonl
```

`run jev` and `run claude` call paid APIs. Do not run them unless the user asks; the user runs the paid evaluation.

## Architecture

The design keeps the comparison fair: engines only rank, everything else is shared.

- `wordle.py` owns the rules: `score(guess, secret)` gives the `G/Y/X` feedback (greens first, then yellows left to right), `candidates(words, history)` keeps the words that give the same feedback for every past guess, and `is_solved`/`is_over` end the game. `History` is a list of `(guess, feedback)` pairs.
- `resolver.Resolver` gets a `RankingEngine` by dependency injection. It plays the opener (`SERIO`) on turn 1 and the only candidate when one is left, without calling the engine (so those turns cost nothing). Otherwise it calls `engine.pick(candidates, history)` under a tenacity retry (3 tries); a picked word that is not a candidate is also retried. After 3 failures the error propagates and the whole run stops.
- Engines (`engines/`) subclass `RankingEngine` and return a `Pick(word, Usage)`. The SDK clients are built with retries off because the resolver retries. The APIs do not return prices, so each engine computes cost from tokens with a `Price` (USD per million tokens). To add an engine, subclass `RankingEngine` and register it in `engines/__init__.py:ENGINES` (the CLI choices come from that dict).
- Jev and Claude get the same text from `prompt.py`: the state `game_state(history)` (`hidden_word_rule`, `colors`, `attempts`) and the structured instructions `QUESTION`, which repeat the golden rule (a prompt experiment showed that Jev applies a rule in the instructions better than a rule only in the state). Claude answers one word through a JSON schema; Jev answers a TypeSafe `Choice` and the engine plays the top probability. A `Choice` takes at most `MAX_OPTIONS` (255) options, so with more candidates Jev asks one question per group in one request, then a final question with the best words of each group.
- **Golden rule:** the engines must know the rule that selects the hidden words. `prompt.GOLDEN_RULE` is the only definition of the hidden word: every prompt contains it, `scripts/build_wordlists.py` implements it (lemma = at least one Wiktionary sense without the `form-of` tag; top `COMMON_WORDS` by wordfreq), and `docs/metodologia.md` quotes it verbatim (a test checks this). If you change the rule, change all three and rebuild the lists.
- Two word lists in `wordle_arena/data/`: `words_es.txt` (all valid words = candidates) and `common_es.txt` (1000 common lemmas = hidden words; `cli run` samples secrets from it). `scripts/build_wordlists.py` rebuilds from the RLA-ES Hunspell dictionary (pinned commit), the Spanish Wiktionary (kaikki.org) and wordfreq (`poetry install --with data`). Do not edit the lists by hand; change the script.
- `arena.play` is the only code that knows the secret. `arena.run` appends one JSON line per game and skips secrets already in the file, so a stopped run continues with the same command. `records.py` owns that file format (`Game`/`Turn` dataclasses, `load_games`, `append_game`); `arena` writes it and `report` reads it, and neither imports the other. `report.py` builds two Markdown tables: per-engine results with the score (mean guesses, 7 if not solved) and the lift (hits / chance: does the engine pick the common word more often than random?) and a paired comparison with a reference engine (`--reference`, default `random`), both with bootstrap 95% CIs. It refuses files that use different openers or two files of one engine.
- `assist.py` is the interactive helper (`wordle-arena assist`): it suggests guesses for a game that a person plays. `cli.py` only parses arguments and calls the modules.

## Conventions

- Code and docs in English; docstrings in ASD-STE100 Simplified Technical English.
- Keep code short and readable; ruff line length is 110.
- Tests use fakes (`FakeTypeSafe`, `fake_anthropic`, `FakeEngine`) instead of real clients; keep it that way.
