"""The arena: it plays games between the hidden words and a resolver, and saves the results."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from wordle_arena.records import Game, Turn, append_game, load_games
from wordle_arena.resolver import Resolver
from wordle_arena.wordle import is_over, is_solved, score


def play(resolver: Resolver, secret: str) -> Game:
    """Play one game and return its result. The resolver gets only the feedback, not the hidden word."""
    history, turns = [], []
    while not is_over(history):
        guess = resolver.guess(history)
        feedback = score(guess.word, secret)
        history.append((guess.word, feedback))
        seconds = round(guess.seconds, 3)
        turns.append(Turn(guess.word, feedback, guess.candidates, seconds, **asdict(guess.usage)))
    return Game(resolver.engine.name, resolver.opener, secret, is_solved(history), len(history), turns)


def run(resolver: Resolver, secrets: list[str], out: Path, workers: int = 1) -> None:
    """Play one game for each hidden word. Add each result as one JSON line to the file.

    The run skips the hidden words that are already in the file. Thus you can continue a stopped run.
    If a game fails, the run stops. The file keeps all the complete games.
    """
    try:
        done = {game.secret for game in load_games(out)}
    except FileNotFoundError:
        done = set()
    todo = [secret for secret in secrets if secret not in done]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as file, ThreadPoolExecutor(workers) as pool:
        futures = [pool.submit(play, resolver, secret) for secret in todo]
        try:
            for n, future in enumerate(as_completed(futures), start=len(secrets) - len(todo) + 1):
                game = future.result()
                append_game(file, game)
                result = f"solved in {game.attempts}" if game.solved else "not solved"
                print(f"[{n}/{len(secrets)}] {game.secret}: {result}")
        except BaseException:
            pool.shutdown(cancel_futures=True)
            raise
