# BK-Tree Spell Search

Finds dictionary words close to a misspelled word, using a BK-Tree and Levenshtein edit distance.

**How it works:** each node is a word; its children are labelled by their edit distance to it. A search within distance `n` only visits children labelled `d-n` to `d+n` (triangle inequality) and skips the rest.

Burkhard-Keller Tree Advantages:


Compared with a linear search: A BK-Tree can skip entire branches using edit-distance rules instead of checking every word.

Compared with a hash table: A hash table is good for exact matches but is not naturally suited to finding words within a given edit distance.

Compared with a normal binary search tree: A BK-Tree organizes words by edit distance, making approximate matching more suitable.

Main advantage: It efficiently supports spell-checking and similar-word suggestions.


**Time complexity** (N = words, L = word length):

| Operation | Time |
|-----------|------|
| Levenshtein distance | O(L²) |
| Insert one word | O(log N) average, O(N) worst |
| Search (small n) | well below N average, O(N) worst |
| Space | O(N) |

Insert and search are counted in distance computations, each costing O(L²).
<img width="765" height="251" alt="image" src="https://github.com/user-attachments/assets/e0cb9506-025c-4f72-8b76-35dd3227b525" />


**Run:** `python main.py`, then type a word. Commands: `:d 1` set distance, `:add word`, `:help`, `:quit`.
**Test:** `python -m pip install -r requirements.txt`, then `python -m pytest -v`.
**Files:** `bktree/` (tree + distance), `main.py`, `benchmark.py`, `data/words.txt`, `tests/`.

