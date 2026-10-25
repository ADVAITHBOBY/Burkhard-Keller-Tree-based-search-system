"""Command line interface for the BK-Tree spell search.

Examples:
    python main.py helo                      # one-off query
    python main.py helo wrld -d 2            # several queries, edit distance 2
    python main.py                           # interactive mode
"""

import argparse
import time
from pathlib import Path

from bktree import BKTree

DEFAULT_WORDS = Path(__file__).parent / "data" / "words.txt"


def show(tree: BKTree, query: str, max_distance: int, limit: int) -> None:
    start = time.perf_counter()
    matches = tree.search(query, max_distance)
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"\nQuery: '{query}'  (max distance {max_distance}, {elapsed_ms:.2f} ms)")
    if not matches:
        print("  no matches found")
        return
    for word, dist in matches[:limit]:
        print(f"  {word:<20} distance {dist}")
    if len(matches) > limit:
        print(f"  ... and {len(matches) - limit} more")


def main() -> None:
    parser = argparse.ArgumentParser(description="BK-Tree fuzzy word search")
    parser.add_argument("queries", nargs="*", help="words to look up")
    parser.add_argument("-w", "--words", default=str(DEFAULT_WORDS), help="dictionary file (one word per line)")
    parser.add_argument("-d", "--distance", type=int, default=2, help="max edit distance (default 2)")
    parser.add_argument("-n", "--limit", type=int, default=10, help="max results to show (default 10)")
    args = parser.parse_args()

    tree = BKTree.from_file(args.words)
    print(f"Loaded {len(tree)} words (tree depth {tree.depth()}).")

    if args.queries:
        for q in args.queries:
            show(tree, q, args.distance, args.limit)
        return

    print("Interactive mode. Type a word (or 'quit' to exit).")
    while True:
        try:
            q = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q.lower() in {"quit", "exit", "q"}:
            break
        if q:
            show(tree, q, args.distance, args.limit)


if __name__ == "__main__":
    main()
