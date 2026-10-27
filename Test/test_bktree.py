import random

import pytest

from bktree import BKTree, hamming, levenshtein


# ------------------------------------------------------------------ insertion
def test_empty_tree():
    tree = BKTree()
    assert len(tree) == 0
    assert tree.depth() == 0
    assert tree.search("anything", 3) == []
    assert tree.closest("anything") is None


def test_add_and_len(small_tree):
    assert len(small_tree) == 8


def test_duplicates_are_ignored():
    tree = BKTree()
    assert tree.add("hello") is True
    assert tree.add("hello") is False
    assert tree.add("HELLO") is False  # case-insensitive by default
    assert len(tree) == 1


def test_empty_and_whitespace_words_ignored():
    tree = BKTree()
    assert tree.add("") is False
    assert tree.add("   ") is False
    assert len(tree) == 0


def test_add_many_returns_count_added():
    tree = BKTree()
    assert tree.add_many(["a", "b", "a", "c"]) == 3


def test_case_sensitive_mode():
    tree = BKTree(["Hello", "hello"], case_sensitive=True)
    assert len(tree) == 2
    assert tree.search("Hello", 0) == [("Hello", 0)]


def test_iteration_returns_all_words(small_tree):
    assert sorted(small_tree) == sorted(["book", "books", "cake", "boo", "boon", "cook", "cape", "cart"])


def test_contains(small_tree):
    assert "book" in small_tree
    assert "BOOK" in small_tree
    assert "bok" not in small_tree
    assert 42 not in small_tree


# --------------------------------------------------------------------- search
def test_exact_match(small_tree):
    assert small_tree.search("book", 0) == [("book", 0)]


def test_search_distance_one(small_tree):
    assert small_tree.search("book", 1) == [
        ("book", 0),
        ("boo", 1),
        ("books", 1),
        ("boon", 1),
        ("cook", 1),
    ]


def test_search_misspelled_query(small_tree):
    result = small_tree.search("caqe", 1)
    assert ("cake", 1) in result
    assert ("cape", 1) in result


def test_results_sorted_by_distance_then_alpha(small_tree):
    result = small_tree.search("cak", 2)
    assert result == sorted(result, key=lambda p: (p[1], p[0]))


def test_no_matches(small_tree):
    assert small_tree.search("zzzzzzzz", 1) == []


def test_negative_distance_raises(small_tree):
    with pytest.raises(ValueError):
        small_tree.search("book", -1)


def test_query_is_normalised(small_tree):
    assert small_tree.search("  BOOK ", 0) == [("book", 0)]


def test_suggest_and_closest(small_tree):
    assert small_tree.suggest("bok", max_distance=1, limit=2) == ["boo", "book"]
    assert small_tree.closest("cakes", 2) == ("cake", 1)


def test_depth_is_positive_and_bounded(small_tree):
    assert 1 <= small_tree.depth() <= len(small_tree)


def test_deep_chain_does_not_hit_recursion_limit():
    # Words 'a', 'aa', 'aaa', ... form a long chain; iterative code must cope.
    tree = BKTree("a" * n for n in range(1, 1500))
    assert len(tree) == 1499
    assert tree.search("a" * 750, 0) == [("a" * 750, 0)]


# ------------------------------------------------- correctness vs brute force
@pytest.mark.parametrize("max_distance", [0, 1, 2, 3])
def test_matches_brute_force_on_dictionary(dictionary_words, max_distance):
    rng = random.Random(42)
    sample = rng.sample(dictionary_words, 1000)
    tree = BKTree(sample)
    for _ in range(60):
        base = rng.choice(sample)
        pos = rng.randrange(len(base))
        query = base[:pos] + rng.choice("abcdefghijklmnopqrstuvwxyz") + base[pos + 1:]
        expected = sorted(
            ((w, d) for w in set(sample) for d in [levenshtein(query, w)] if d <= max_distance),
            key=lambda p: (p[1], p[0]),
        )
        assert tree.search(query, max_distance) == expected


def test_random_words_match_brute_force():
    rng = random.Random(7)
    words = {"".join(rng.choices("abc", k=rng.randint(1, 7))) for _ in range(300)}
    tree = BKTree(words)
    for _ in range(100):
        query = "".join(rng.choices("abc", k=rng.randint(1, 7)))
        for n in range(4):
            expected = sorted(
                ((w, levenshtein(query, w)) for w in words if levenshtein(query, w) <= n),
                key=lambda p: (p[1], p[0]),
            )
            assert tree.search(query, n) == expected


# ------------------------------------------------------- custom metric / files
def test_custom_distance_function_hamming():
    tree = BKTree(["cat", "bat", "rat", "car", "dog"], distance_func=hamming)
    assert tree.search("cot", 1) == [("cat", 1), ("dog", 2)][:1]
    assert tree.search("cat", 0) == [("cat", 0)]
    assert [w for w, _ in tree.search("cat", 1)] == ["cat", "bat", "car", "rat"]


def test_from_file_loads_dictionary(dictionary_tree):
    assert len(dictionary_tree) == 1500
    assert "hello" in dictionary_tree


def test_realistic_spelling_corrections(dictionary_tree):
    assert "hello" in dictionary_tree.suggest("helo", 1, limit=20)
    assert "world" in dictionary_tree.suggest("wrold", 2, limit=50)
    assert "computer" in dictionary_tree.suggest("compter", 1, limit=20)
    assert "necessary" in dictionary_tree.suggest("neccessary", 1, limit=20)
