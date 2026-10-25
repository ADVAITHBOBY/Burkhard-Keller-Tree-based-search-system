"""Compare BK-Tree search against a brute-force scan of the whole dictionary."""

import random
import time

from bktree import BKTree, levenshtein

WORDS_FILE = "data/words.txt"


def mutate(word: str) -> str:
    """Introduce one random typo."""
    if len(word) < 2:
        return word
    i = random.randrange(len(word))
    kind = random.choice(["delete", "insert", "substitute"])
    letter = random.choice("abcdefghijklmnopqrstuvwxyz")
    if kind == "delete":
        return word[:i] + word[i + 1:]
    if kind == "insert":
        return word[:i] + letter + word[i:]
    return word[:i] + letter + word[i + 1:]


def main() -> None:
    random.seed(1)
    tree = BKTree.from_file(WORDS_FILE)
    words = list(tree)
    queries = [mutate(random.choice(words)) for _ in range(500)]

    for n in (1, 2, 3):
        t0 = time.perf_counter()
        for q in queries:
            tree.search(q, n)
        bk = time.perf_counter() - t0

        t0 = time.perf_counter()
        for q in queries:
            [w for w in words if levenshtein(q, w) <= n]
        brute = time.perf_counter() - t0

        print(f"max distance {n}: BK-Tree {bk:.3f}s | brute force {brute:.3f}s | speedup x{brute / bk:.1f}")


if __name__ == "__main__":
    main()
