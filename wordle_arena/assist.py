"""The assistant: it suggests guesses for a game that you play (for example, today's Wordle)."""

import re

from wordle_arena.resolver import Resolver
from wordle_arena.wordle import WORD_LENGTH, is_over, is_solved, normalize


def play_with_help(resolver: Resolver) -> None:
    """Suggest a guess. Then read the word that you played and its feedback. Do again until the end."""
    history = []
    while not is_over(history):
        guess = resolver.guess(history)
        word = ask(
            f"Play {guess.word} ({guess.candidates} candidates). Word played [{guess.word}]: ",
            f"[A-ZÑ]{{{WORD_LENGTH}}}",
            guess.word,
        )
        history.append((word, ask("Feedback (G = green, Y = yellow, X = gray): ", f"[GYX]{{{WORD_LENGTH}}}")))
    print("Solved." if is_solved(history) else "No more attempts.")


def ask(prompt: str, pattern: str, default: str = "") -> str:
    """Read an answer that agrees with the pattern. An empty answer gives the default."""
    while not re.fullmatch(pattern, answer := normalize(input(prompt)) or default):
        print("The answer is not valid. Try again.")
    return answer
