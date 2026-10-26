import sys
from pathlib import Path

import pytest

# Make the project root importable when running `pytest` from anywhere.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bktree import BKTree  # noqa: E402

WORDS_FILE = ROOT / "data" / "words.txt"


@pytest.fixture
def small_tree():
    return BKTree(["book", "books", "cake", "boo", "boon", "cook", "cape", "cart"])


@pytest.fixture(scope="session")
def dictionary_words():
    with open(WORDS_FILE, encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip()]


@pytest.fixture(scope="session")
def dictionary_tree():
    return BKTree.from_file(str(WORDS_FILE))
