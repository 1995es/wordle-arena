"""The game description for the AI engines. All engines get the same text."""

from wordle_arena.wordle import COMMON_WORDS, WORD_LENGTH, History

GOLDEN_RULE = (
    "The hidden word is a common Spanish lemma. A lemma is a word that has at least one meaning of its own "
    "in the Spanish Wiktionary, not only as a form of another word. Thus the hidden word can be a noun, an "
    "adjective, a verb in the infinitive, an adverb, a pronoun, a preposition, a conjunction, an "
    "interjection or a number. It is never only a plural, a feminine form or a conjugated form of another "
    "word. "
    f"It is one of the {COMMON_WORDS:,} most frequent Spanish lemmas with {WORD_LENGTH} letters. "
    "The guesses can be any word of the dictionary, also plurals, feminine forms and conjugated verbs. "
    "Names are not valid words."
)
"""The definition of the hidden word. docs/metodologia.md quotes this text, and common_es.txt applies it."""

COLORS = (
    "Every letter of a guess is colored: green means the hidden word has that letter in that same position; "
    "yellow means the hidden word contains that letter, but in a different position; gray means the hidden "
    "word does not contain that letter (if the letter appears twice in the guess and one copy is green or "
    "yellow, a gray copy means there are no more copies). Accents are ignored; Ñ is its own letter."
)

QUESTION = {
    "task": "Select the option that is most likely to be the hidden word of this Spanish Wordle game.",
    "the hidden word": "It follows `hidden_word_rule`: it is a common Spanish lemma, a word with a meaning "
    "of its own.",
    "never select": "An option that is only a plural (CASAS), only a feminine form of an adjective, or only "
    "a conjugated verb form (COMEN, DIGAS, SALIO), because such a word cannot be the hidden word.",
    "can select": "An option that is also a word of its own, even if it looks like a verb form or a plural: "
    "CERCA (adverb), JUEGO (noun).",
    "options": "Every option agrees with the colors of all the `attempts`. The options have no accents.",
}
"""The instructions of the question. The rule is in the instructions, because a model applies the
instructions better than a rule that is only in the state."""


def describe(letter: str, position: int, mark: str) -> str:
    """Return the feedback of one letter in words."""
    if mark == "G":
        return f"{letter} is green: the hidden word has {letter} at position {position}"
    if mark == "Y":
        return f"{letter} is yellow: the hidden word contains {letter}, but not at position {position}"
    return f"{letter} is gray: the hidden word has no (more) {letter}"


def game_state(history: History) -> dict:
    """Return the rule of the hidden word, the colors, and each attempt with the feedback of each letter."""
    attempts = [
        {
            "attempt": n,
            "guess": guess,
            "result": [
                describe(letter, i, mark)
                for i, (letter, mark) in enumerate(zip(guess, feedback, strict=True), 1)
            ],
        }
        for n, (guess, feedback) in enumerate(history, start=1)
    ]
    return {"hidden_word_rule": GOLDEN_RULE, "colors": COLORS, "attempts": attempts}
