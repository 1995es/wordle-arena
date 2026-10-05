"""Build the two word lists of the benchmark from public sources.

1. wordle_arena/data/words_es.txt: all the Spanish words with 5 letters. These words are the candidates.
   The source is the Hunspell dictionary es_ES of the RLA-ES project, from the LibreOffice repository.
   The script expands each dictionary entry with its affixes: plurals, feminine forms and verb forms.
2. wordle_arena/data/common_es.txt: the 1000 most frequent lemmas of the first list. These words are the
   hidden words. This list applies the golden rule (see docs/metodologia.md and wordle_arena/prompt.py):
   a lemma is a word that has at least one meaning of its own in the Spanish Wiktionary, not only
   "form of" another word. For example PERRO, CERCA and ENERO are lemmas; PERROS, PUEDE and CASES are not.
   The source of the meanings is the Spanish Wiktionary, as extracted by kaikki.org (wiktextract).
   The source of the frequencies is wordfreq.

The script does not use names: it ignores the dictionary entries that start with an uppercase letter,
and it uses only the Wiktionary entries of a lexical part of speech (not names, prefixes or abbreviations).

Run: poetry install --with data && poetry run python scripts/build_wordlists.py
"""

import gzip
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

from wordfreq import zipf_frequency

from wordle_arena.wordle import COMMON_WORDS, WORD_LENGTH, normalize

COMMIT = "762abe74008b94b2ff06db6f4024b59a8254c467"  # RLA-ES v2.9
SOURCE = f"https://raw.githubusercontent.com/LibreOffice/dictionaries/{COMMIT}/es/es_ES"
WIKTIONARY = "https://kaikki.org/dictionary/downloads/es/es-extract.jsonl.gz"
LEXICAL = {"noun", "adj", "verb", "adv", "pron", "prep", "conj", "intj", "num"}
DATA = Path(__file__).parents[1] / "wordle_arena" / "data"
MAX_DEPTH = 2  # Hunspell applies a maximum of two suffixes.


def download(extension: str) -> list[str]:
    """Download one file of the dictionary and return its lines. Remove the emoji variation selector."""
    with urllib.request.urlopen(f"{SOURCE}.{extension}") as response:
        return response.read().decode("utf-8").replace("️", "").splitlines()


def parse_rules(lines: list[str]) -> dict[str, list[tuple]]:
    """Return the affix rules of each flag, as (kind, strip, add, next flags, condition)."""
    rules = defaultdict(list)
    for parts in map(str.split, lines):
        if len(parts) >= 5 and parts[0] in ("PFX", "SFX"):
            kind, flag, strip, add, condition = parts[:5]
            add, _, next_flags = add.partition("/")
            pattern = re.compile(f"^{condition}" if kind == "PFX" else f"{condition}$")
            rules[flag].append((kind, strip.strip("0"), add.strip("0"), next_flags, pattern))
    return rules


def expand(word: str, flags: str, rules: dict[str, list[tuple]], depth: int = 0) -> set[str]:
    """Return the word and all the words that its affixes make. Prefixes also combine with suffixes."""
    suffixed, prefixes = {word}, []
    for kind, strip, add, next_flags, condition in (rule for flag in flags for rule in rules.get(flag, [])):
        if not condition.search(word):
            continue
        if kind == "PFX":
            prefixes.append((strip, add))
        elif word.endswith(strip):
            new = word[: len(word) - len(strip)] + add
            suffixed |= expand(new, next_flags, rules, depth + 1) if depth + 1 < MAX_DEPTH else {new}
    prefixed = {add + w[len(strip) :] for strip, add in prefixes for w in suffixed if w.startswith(strip)}
    return suffixed | prefixed


def five_letters(word: str) -> str | None:
    """Return the normalized word if it has 5 letters, or None."""
    word = normalize(word)
    return word if len(word) == WORD_LENGTH and word.isalpha() else None


def wiktionary_lemmas() -> dict[str, set[str]]:
    """Return the lemmas with 5 letters, as {normalized word: spellings with accents}.

    A lemma has at least one meaning (sense) without the tag "form-of".
    """
    lemmas = defaultdict(set)
    with urllib.request.urlopen(WIKTIONARY) as response, gzip.open(response, "rt", encoding="utf-8") as lines:
        for entry in map(json.loads, lines):
            word = entry.get("word", "")
            if entry.get("lang_code") != "es" or entry.get("pos") not in LEXICAL or not word.islower():
                continue
            own_meaning = any("form-of" not in sense.get("tags", []) for sense in entry.get("senses", []))
            if own_meaning and (normalized := five_letters(word)):
                lemmas[normalized].add(word)
    return lemmas


def main() -> None:
    """Build the two lists and write them to the data folder."""
    rules = parse_rules(download("aff"))
    entries = [line.partition("/")[::2] for line in download("dic")[1:]]
    entries = [(stem.strip(), flags.split()[0] if flags.strip() else "") for stem, flags in entries]
    entries = [(stem, flags) for stem, flags in entries if stem and stem[0].islower()]

    words = {w for stem, flags in entries for form in expand(stem, flags, rules) if (w := five_letters(form))}
    lemmas = wiktionary_lemmas()
    frequency = {
        w: max(zipf_frequency(s, "es") for s in spellings) for w, spellings in lemmas.items() if w in words
    }
    common = sorted(frequency, key=lambda w: (-frequency[w], w))[:COMMON_WORDS]

    (DATA / "words_es.txt").write_text("\n".join(sorted(words)) + "\n", encoding="utf-8")
    (DATA / "common_es.txt").write_text("\n".join(common) + "\n", encoding="utf-8")
    print(f"{len(words)} words, {len(common)} common words (minimum zipf {frequency[common[-1]]:.2f}).")


if __name__ == "__main__":
    main()
