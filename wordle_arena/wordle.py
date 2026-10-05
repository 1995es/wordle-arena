"""The rules of Wordle in Spanish: the word list, the feedback and the candidates.

The feedback has one character for each letter of the guess:
    G -> green: the hidden word has this letter at this position.
    Y -> yellow: the hidden word has this letter at a different position.
    X -> gray: the hidden word does not have this letter (or more copies of it).
"""

import unicodedata
from collections import Counter
from importlib.resources import files

WORD_LENGTH = 5
MAX_ATTEMPTS = 6
COMMON_WORDS = 1000  # The number of common lemmas that can be the hidden word.
SOLVED = "G" * WORD_LENGTH

type History = list[tuple[str, str]]
"""The (guess, feedback) pairs of a game, from the first to the last."""


def normalize(word: str) -> str:
    """Return the word in uppercase, without accents. Keep the letter Ñ."""
    word = word.strip().upper().replace("Ñ", "\0")
    word = "".join(c for c in unicodedata.normalize("NFD", word) if unicodedata.category(c) != "Mn")
    return word.replace("\0", "Ñ")


def load_words(name: str = "words") -> list[str]:
    """Return the words of a list, without duplicates. Each word has 5 letters.

    The list "words" has all the valid words. The list "common" has the common words for the hidden words.
    """
    text = files("wordle_arena").joinpath(f"data/{name}_es.txt").read_text(encoding="utf-8")
    words = (normalize(line) for line in text.splitlines())
    return list(dict.fromkeys(w for w in words if len(w) == WORD_LENGTH and w.isalpha()))


def score(guess: str, secret: str) -> str:
    """Return the feedback for a guess.

    The greens come first. Then the yellows use the remaining letters, from left to right.
    """
    remaining = Counter(s for g, s in zip(guess, secret, strict=True) if g != s)
    result = []
    for g, s in zip(guess, secret, strict=True):
        if g == s:
            result.append("G")
        elif remaining[g]:
            result.append("Y")
            remaining[g] -= 1
        else:
            result.append("X")
    return "".join(result)


def candidates(words: list[str], history: History) -> list[str]:
    """Return the words that can be the hidden word.

    A word is a candidate if each guess in the history gives the same feedback for it.
    """
    return [w for w in words if all(score(guess, w) == feedback for guess, feedback in history)]


def is_solved(history: History) -> bool:
    """Return True if the last guess is the hidden word."""
    return bool(history) and history[-1][1] == SOLVED


def is_over(history: History) -> bool:
    """Return True if the game is solved or there are no more attempts."""
    return is_solved(history) or len(history) >= MAX_ATTEMPTS
