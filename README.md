# BK-Tree Spell Search

Finds dictionary words close to a misspelled word, using a BK-Tree and Levenshtein edit distance.

**How it works:** each node is a word; its children are labelled by their edit distance to it. A search within distance `n` only visits children labelled `d-n` to `d+n` (triangle inequality) and skips the rest.

**Time complexity** (N = words, L = word length):

| Operation | Time |
|-----------|------|
| Levenshtein distance | O(L²) |
| Insert one word | O(log N) average, O(N) worst |
| Search (small n) | well below N average, O(N) worst |
| Space | O(N) |

Insert and search are counted in distance computations, each costing O(L²).

**Run:** `python main.py`, then type a word. Commands: `:d 1` set distance, `:add word`, `:help`, `:quit`.
**Test:** `python -m pip install -r requirements.txt`, then `python -m pytest -v`.
**Files:** `bktree/` (tree + distance), `main.py`, `benchmark.py`, `data/words.txt`, `tests/`.
<img width="794" height="197" alt="image" src="https://github.com/user-attachments/assets/210c6838-db79-492d-9411-377dc3498d03" />
