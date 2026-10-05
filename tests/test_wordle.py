from pathlib import Path

import pytest

from wordle_arena.prompt import GOLDEN_RULE, QUESTION, game_state
from wordle_arena.wordle import COMMON_WORDS, WORD_LENGTH, candidates, load_words, normalize, score


@pytest.mark.parametrize(
    "guess, secret, feedback",
    [
        ("SACOS", "ROSAS", "YYXYG"),  # Repeated S: the first is yellow, the second is green.
        ("RATOS", "ROSAS", "GYXYG"),
        ("GATOS", "ROSAS", "XYXYG"),
        ("PAPAS", "PERRO", "GXXXX"),
        ("SSSSS", "ROSAS", "XXGXG"),  # Greens use the S before the yellows.
        ("AABBB", "CCCAA", "YYXXX"),
        ("ROSAS", "ROSAS", "GGGGG"),
    ],
)
def test_score(guess, secret, feedback):
    assert score(guess, secret) == feedback


def test_normalize_removes_accents_but_keeps_enye():
    assert normalize(" árbol\n") == "ARBOL"
    assert normalize("añejo") == "AÑEJO"


def test_load_words():
    words = load_words()
    assert len(words) == len(set(words)) > 8000
    assert all(len(w) == WORD_LENGTH and w.isupper() for w in words)
    assert {"SERIO", "PERRO", "GATOS", "CASES", "AÑEJO"} <= set(words)


def test_common_words_are_lemmas_in_the_word_list():
    common = load_words("common")
    assert len(common) == COMMON_WORDS
    assert set(common) <= set(load_words())
    assert {"PERRO", "SERIO", "ENERO", "ESTAR", "DESDE", "CERCA"} <= set(common)
    assert not {"GATOS", "CASES", "PUEDE", "ESTOY", "MESES"} & set(common)  # Only forms of other words.


def test_prompt_and_docs_use_the_golden_rule():
    assert game_state([])["hidden_word_rule"] == GOLDEN_RULE
    assert "hidden_word_rule" in QUESTION["the hidden word"]
    methodology = Path(__file__).parents[1] / "docs" / "metodologia.md"
    assert GOLDEN_RULE in methodology.read_text(encoding="utf-8")


def test_candidates_give_the_same_feedback_as_the_secret():
    history = [("RATOS", score("RATOS", "ROSAS"))]
    assert candidates(["ROSAS", "ROJAS", "GATOS", "ROLAS"], history) == ["ROSAS", "ROJAS", "ROLAS"]


def test_candidates_use_gray_letters_to_limit_copies():
    history = [("SACOS", score("SACOS", "ROLAS"))]  # The second S is gray: the secret has only one S.
    assert candidates(["ROLAS", "ROSAS"], history) == ["ROLAS"]


def test_game_state_describes_each_letter():
    state = game_state([("SACOS", "YYXYG")])
    assert state["hidden_word_rule"] == GOLDEN_RULE
    result = state["attempts"][0]["result"]
    assert result[0].startswith("S is yellow")
    assert result[2].startswith("C is gray")
    assert result[4] == "S is green: the hidden word has S at position 5"
