"""BK-Tree based fuzzy word search."""

from .bktree import BKTree
from .distance import levenshtein, hamming

__all__ = ["BKTree", "levenshtein", "hamming"]
__version__ = "1.0.0"
