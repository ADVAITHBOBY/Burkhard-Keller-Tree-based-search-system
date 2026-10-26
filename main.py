"""Command line interface for the BK-Tree spell search.

Examples:
    python main.py helo                  # one-off query (max distance 2)
    python main.py helo wrld -d 1        # several queries, max distance 1
    python main.py helo --add            # search, then add the word to the dictionary
    python main.py                       # interactive mode (type :help inside)
"""

import argparse
import time
from pathlib import Path

from bktree import BKTree

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_WORDS = DATA_DIR / "words.txt"
DEFAULT_CUSTOM = DATA_DIR / "custom_words.txt"

HELP_TEXT = """Commands:
  <word>         search for similar words
  :d <number>    change the max edit distance, e.g.  :d 1
  :add <word>    add a word to the dictionary
  :help          show this help
  :quit          exit  (Ctrl-D also works)"""


# ----------------------------------------------------------------- dictionary
def load_tree(words_path, custom_path=None) -> BKTree:
    """Load the base dictionary plus any words the user added earlier."""
    tree = BKTree.from_file(str(words_path))
    if custom_path and Path(custom_path).exists():
        with open(custom_path, "r", encoding="utf-8") as fh:
            tree.add_many(fh)
    return tree


def add_word(tree: BKTree, custom_path, word: str) -> str:
    """Add a word to the tree and save it to the custom dictionary file.
    Returns a message describing what happened."""
    word = word.strip().lower()
    if not word.isalpha():
        return f"'{word}' was not added: use letters only, one word at a time."
    if not tree.add(word):
        return f"'{word}' is already in the dictionary."

    path = Path(custom_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    needs_newline = path.exists() and path.stat().st_size > 0 and not path.read_bytes().endswith(b"\n")
    with open(path, "a", encoding="utf-8") as fh:
        if needs_newline:
            fh.write("\n")
        fh.write(word + "\n")
    return f"Added '{word}' to the dictionary (saved in {path.name})."


# --------------------------------------------------------------------- search
def show(tree: BKTree, query: str, max_distance: int, limit: int) -> bool:
    """Print the search results. Returns True if the query is an exact
    dictionary word, False otherwise."""
    start = time.perf_counter()
    matches = tree.search(query, max_distance)
    elapsed_ms = (time.perf_counter() - start) * 1000
    in_dictionary = any(dist == 0 for _, dist in matches)

    print(f"\nQuery: '{query}'  (max distance {max_distance}, {elapsed_ms:.2f} ms)")
    print("  Status: found in the dictionary" if in_dictionary
          else "  Status: NOT in the dictionary")
    if not matches:
        print("  no similar words found")
        return in_dictionary
    for word, dist in matches[:limit]:
        print(f"  {word:<20} distance {dist}")
    if len(matches) > limit:
        print(f"  ... and {len(matches) - limit} more")
    return in_dictionary


def non_negative_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{text}' is not a whole number")
    if value < 0:
        raise argparse.ArgumentTypeError("distance cannot be negative")
    return value


# ----------------------------------------------------------- interactive mode
def interactive(tree: BKTree, distance: int, limit: int, custom_path) -> None:
    print("Interactive mode. Type a word to search, or :help for commands.")
    while True:
        try:
            line = input(f"[d={distance}]> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue

        if line.startswith(":"):
            command, _, arg = line[1:].partition(" ")
            command, arg = command.lower(), arg.strip()
            if command in {"q", "quit", "exit"}:
                break
            elif command in {"d", "distance"}:
                try:
                    new_distance = non_negative_int(arg)
                except argparse.ArgumentTypeError as err:
                    print(f"  {err}. Example:  :d 2")
                else:
                    distance = new_distance
                    print(f"  Max distance set to {distance}.")
            elif command == "add":
                print("  " + add_word(tree, custom_path, arg))
            elif command == "help":
                print(HELP_TEXT)
            else:
                print(f"  Unknown command ':{command}'. Type :help for the list.")
            continue

        if len(line.split()) > 1:
            print("  Please enter one word at a time.")
            continue

        in_dictionary = show(tree, line, distance, limit)

        # Offer to add the word if it isn't already a dictionary word.
        if line.isalpha() and not in_dictionary:
            try:
                answer = input(f"Add '{line.lower()}' to the dictionary? [y/N] ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if answer in {"y", "yes"}:
                print("  " + add_word(tree, custom_path, line))


# ----------------------------------------------------------------------- main
def main() -> None:
    parser = argparse.ArgumentParser(description="BK-Tree fuzzy word search")
    parser.add_argument("queries", nargs="*", help="words to look up (leave empty for interactive mode)")
    parser.add_argument("-d", "--distance", type=non_negative_int, default=2,
                        help="max edit distance (default 2)")
    parser.add_argument("-n", "--limit", type=int, default=10, help="max results to show (default 10)")
    parser.add_argument("-w", "--words", default=str(DEFAULT_WORDS),
                        help="base dictionary file, one word per line")
    parser.add_argument("-c", "--custom", default=str(DEFAULT_CUSTOM),
                        help="file where words you add are saved (default data/custom_words.txt)")
    parser.add_argument("-a", "--add", action="store_true",
                        help="also add the queried words to the dictionary")
    args = parser.parse_args()

    tree = load_tree(args.words, args.custom)
    print(f"Loaded {len(tree)} words (tree depth {tree.depth()}).")

    if args.queries:
        for query in args.queries:
            show(tree, query, args.distance, args.limit)
            if args.add:
                print("  " + add_word(tree, args.custom, query))
        return

    interactive(tree, args.distance, args.limit, args.custom)


if __name__ == "__main__":
    main()
