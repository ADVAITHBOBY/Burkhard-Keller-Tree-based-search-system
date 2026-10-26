import pytest

from bktree import hamming, levenshtein


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("", "", 0),
        ("abc", "abc", 0),
        ("", "abc", 3),
        ("abc", "", 3),
        ("kitten", "sitting", 3),
        ("flaw", "lawn", 2),
        ("book", "back", 2),
        ("saturday", "sunday", 3),
        ("a", "b", 1),
    ],
)
def test_levenshtein_known_values(a, b, expected):
    assert levenshtein(a, b) == expected


def test_levenshtein_is_symmetric():
    assert levenshtein("intention", "execution") == levenshtein("execution", "intention")


def test_levenshtein_triangle_inequality():
    a, b, c = "spelling", "spilling", "spoiling"
    assert levenshtein(a, c) <= levenshtein(a, b) + levenshtein(b, c)


def test_hamming_basic():
    assert hamming("karolin", "kathrin") == 3
    assert hamming("abc", "abc") == 0


def test_hamming_requires_equal_length():
    with pytest.raises(ValueError):
        hamming("abc", "ab")
