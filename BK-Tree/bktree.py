"""BK-Tree (Burkhard-Keller tree) implementation.

Each node stores a word and a dict mapping  distance -> child node, where the
distance is measured between the child's word and this node's word.

Search for all words within distance n of a query:
    d = dist(query, node.word)
    report node.word if d <= n
    only descend into children whose edge label k satisfies |k - d| <= n
(this pruning is valid because of the triangle inequality).
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from .distance import levenshtein

DistanceFunc = Callable[[str, str], int]


class _Node:
    __slots__ = ("word", "children")

    def __init__(self, word: str) -> None:
        self.word = word
        self.children: Dict[int, "_Node"] = {}


class BKTree:
    def __init__(
        self,
        words: Optional[Iterable[str]] = None,
        distance_func: DistanceFunc = levenshtein,
        case_sensitive: bool = False,
    ) -> None:
        self._distance = distance_func
        self._case_sensitive = case_sensitive
        self._root: Optional[_Node] = None
        self._size = 0
        if words is not None:
            self.add_many(words)

    # ------------------------------------------------------------------ helpers
    def _normalize(self, word: str) -> str:
        word = word.strip()
        return word if self._case_sensitive else word.lower()

    # ------------------------------------------------------------------- insert
    def add(self, word: str) -> bool:
        """Insert a word. Returns True if added, False if empty or duplicate."""
        word = self._normalize(word)
        if not word:
            return False

        if self._root is None:
            self._root = _Node(word)
            self._size = 1
            return True

        node = self._root
        while True:
            d = self._distance(word, node.word)
            if d == 0:
                return False  # duplicate
            child = node.children.get(d)
            if child is None:
                node.children[d] = _Node(word)
                self._size += 1
                return True
            node = child

    def add_many(self, words: Iterable[str]) -> int:
        """Insert many words. Returns how many were actually added."""
        return sum(1 for w in words if self.add(w))

    @classmethod
    def from_file(cls, path: str, **kwargs) -> "BKTree":
        """Build a tree from a text file with one word per line."""
        with open(path, "r", encoding="utf-8") as fh:
            return cls((line for line in fh), **kwargs)

    # ------------------------------------------------------------------- search
    def search(self, query: str, max_distance: int) -> List[Tuple[str, int]]:
        """Return [(word, distance)] for every stored word within max_distance
        of query, sorted by distance and then alphabetically."""
        if max_distance < 0:
            raise ValueError("max_distance must be >= 0")
        if self._root is None:
            return []

        query = self._normalize(query)
        results: List[Tuple[str, int]] = []
        stack = [self._root]  # iterative: no recursion-depth problems

        while stack:
            node = stack.pop()
            d = self._distance(query, node.word)
            if d <= max_distance:
                results.append((node.word, d))
            low, high = d - max_distance, d + max_distance
            for edge, child in node.children.items():
                if low <= edge <= high:
                    stack.append(child)

        results.sort(key=lambda pair: (pair[1], pair[0]))
        return results

    def suggest(self, query: str, max_distance: int = 2, limit: int = 5) -> List[str]:
        """Convenience wrapper: best `limit` matching words (no distances)."""
        return [w for w, _ in self.search(query, max_distance)[:limit]]

    def closest(self, query: str, max_distance: int = 3) -> Optional[Tuple[str, int]]:
        """Single best match within max_distance, or None."""
        matches = self.search(query, max_distance)
        return matches[0] if matches else None

    # ------------------------------------------------------------ dunder / info
    def __contains__(self, word: object) -> bool:
        if not isinstance(word, str):
            return False
        target = self._normalize(word)
        return any(w == target for w, _ in self.search(word, 0))

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[str]:
        if self._root is None:
            return
        stack = [self._root]
        while stack:
            node = stack.pop()
            yield node.word
            stack.extend(node.children.values())

    def depth(self) -> int:
        """Height of the tree (number of nodes on the longest root-leaf path)."""
        if self._root is None:
            return 0
        best, stack = 0, [(self._root, 1)]
        while stack:
            node, level = stack.pop()
            best = max(best, level)
            stack.extend((c, level + 1) for c in node.children.values())
        return best
