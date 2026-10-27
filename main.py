"""Interactive BK-Tree spell search.

Run:
    python main.py

Then type a word to find similar dictionary words. Type :help for commands.
"""

import time
from pathlib import Path

from bktree import BKTree

# ---- settings you can change ------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
DEFAULT_WORDS = DATA_DIR / "words.txt"          # base dictionary
DEFAULT_CUSTOM = DATA_DIR / "custom_words.txt"  # words you add are saved here
DEFAULT_DISTANCE = 1                            # starting max edit distance
RESULT_LIMIT = 10                               # max results shown per search
# -----------------------------------------------------------------------------

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


def parse_distance(text: str) -> int:
    """Turn text into a max distance. Raises ValueError with a clear message."""
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"'{text}' is not a whole number")
    if value < 0:
        raise ValueError("distance cannot be negative")
    return value


# ----------------------------------------------------------- interactive loop
def interactive(tree: BKTree, distance: int = DEFAULT_DISTANCE,
                limit: int = RESULT_LIMIT, custom_path=DEFAULT_CUSTOM) -> None:
    print("Type a word to search, or :help for commands.")
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
                    distance = parse_distance(arg)
                except ValueError as err:
                    print(f"  {err}. Example:  :d 2")
                else:
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
    tree = load_tree(DEFAULT_WORDS, DEFAULT_CUSTOM)
    print(f"Loaded {len(tree)} words (tree depth {tree.depth()}).")
    interactive(tree, DEFAULT_DISTANCE, RESULT_LIMIT, DEFAULT_CUSTOM)


if __name__ == "__main__":
    main()
