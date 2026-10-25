"""Distance metrics usable with a BK-Tree.

A BK-Tree relies on the triangle inequality, so only true metrics
(non-negative, symmetric, d(a, b) == 0 iff a == b, triangle inequality)
are valid here. Levenshtein and Hamming both qualify.
"""


def levenshtein(a: str, b: str) -> int:
    """Classic edit distance (insert, delete, substitute), O(len(a)*len(b)) time,
    O(min(len(a), len(b))) memory."""
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a  # make b the shorter string
    if not b:
        return len(a)

    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            current.append(
                min(
                    previous[j] + 1,        # deletion
                    current[j - 1] + 1,     # insertion
                    previous[j - 1] + cost, # substitution
                )
            )
        previous = current
    return previous[-1]


def hamming(a: str, b: str) -> int:
    """Number of differing positions. Strings must be the same length."""
    if len(a) != len(b):
        raise ValueError("Hamming distance requires strings of equal length")
    return sum(ca != cb for ca, cb in zip(a, b))
