"""The command line: run the arena, show the report, or get help for a game that you play."""

import argparse
import random
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from wordle_arena import arena, report
from wordle_arena.assist import play_with_help
from wordle_arena.engines import ENGINES
from wordle_arena.resolver import OPENER, Resolver
from wordle_arena.wordle import load_words, normalize


def main(argv: list[str] | None = None) -> None:
    """Read the API keys from the .env file, then do the command."""
    load_dotenv(find_dotenv(usecwd=True))
    parser = argparse.ArgumentParser(prog="wordle-arena", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="play games with one engine and save the results")
    run.add_argument("engine", choices=ENGINES)
    run.add_argument("--games", type=int, default=200, help="number of games (default: 200)")
    run.add_argument("--seed", type=int, default=42, help="seed to select the hidden words (default: 42)")
    run.add_argument("--workers", type=int, default=1, help="games in parallel (default: 1)")
    run.add_argument("--out", type=Path, help="results file (default: results/<engine>.jsonl)")
    assist = commands.add_parser("assist", help="get the best guesses for a game that you play")
    assist.add_argument("engine", choices=ENGINES)
    for command in (run, assist):
        command.add_argument("--opener", default=OPENER, type=normalize, help=f"first guess ({OPENER})")
    show = commands.add_parser("report", help="show a Markdown table that compares results files")
    show.add_argument("files", nargs="+", type=Path)
    show.add_argument(
        "--reference", default="random", help="engine for the paired comparison (default: random)"
    )
    args = parser.parse_args(argv)

    if args.command == "report":
        print(report.table(args.files, args.reference))
        return
    words = load_words()
    if args.opener not in words:
        parser.error(f"the opener {args.opener} is not in the word list")
    resolver = Resolver(ENGINES[args.engine](), words, args.opener)
    if args.command == "run":
        secrets = random.Random(args.seed).sample(load_words("common"), args.games)
        arena.run(resolver, secrets, args.out or Path("results") / f"{args.engine}.jsonl", args.workers)
    else:
        try:
            play_with_help(resolver)
        except ValueError as error:
            parser.exit(1, f"{error} Make sure that the feedback is correct.\n")
