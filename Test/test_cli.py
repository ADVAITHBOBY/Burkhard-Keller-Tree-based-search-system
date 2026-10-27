import subprocess
import sys
from pathlib import Path

import pytest

from bktree import BKTree
from main import DEFAULT_WORDS, add_word, interactive, load_tree, parse_distance

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def session(monkeypatch, capsys, tmp_path):
    """Run the interactive loop with scripted input and return what it printed.
    Added words go to a temporary file, never to the real data folder."""
    custom = tmp_path / "custom.txt"

    def run(lines, distance=2):
        feed = iter(lines)

        def fake_input(prompt=""):
            print(prompt, end="")
            try:
                return next(feed)
            except StopIteration:
                raise EOFError

        monkeypatch.setattr("builtins.input", fake_input)
        tree = load_tree(DEFAULT_WORDS, custom)
        interactive(tree, distance, 10, custom)
        return capsys.readouterr().out

    run.custom = custom
    return run


# ---------------------------------------------------------------- searching
def test_finds_correction(session):
    out = session(["helo", "n"], distance=1)
    assert "hello" in out


def test_no_similar_words(session):
    out = session(["qqqqqqqq", "n"], distance=1)
    assert "no similar words found" in out


def test_distance_zero_only_exact(session):
    out = session(["helo", "n"], distance=0)
    assert "no similar words found" in out
    assert "Status: NOT in the dictionary" in out


def test_rejects_multiple_words(session):
    out = session(["hello world", ":quit"])
    assert "one word at a time" in out


def test_blank_lines_are_ignored(session):
    out = session(["", "   ", ":quit"])
    assert "Query:" not in out


# ----------------------------------------------------- dictionary status line
def test_status_found_for_dictionary_word(session):
    out = session(["hello", ":quit"], distance=1)
    assert "Status: found in the dictionary" in out
    assert "NOT in the dictionary" not in out


def test_status_not_found_for_misspelling(session):
    out = session(["helo", "n"], distance=1)
    assert "Status: NOT in the dictionary" in out


def test_status_is_case_insensitive(session):
    out = session(["HELLO", ":quit"], distance=0)
    assert "Status: found in the dictionary" in out


# ------------------------------------------------------------- :d command
def test_change_distance(session):
    out = session([":d 1", "helo", "n"])
    assert "Max distance set to 1" in out
    assert "[d=1]>" in out
    assert "max distance 1" in out


def test_bad_distance_is_rejected(session):
    out = session([":d abc", ":d -3", ":quit"])
    assert out.count("Example:  :d 2") == 2
    assert "[d=2]>" in out  # unchanged
    assert "[d=-3]" not in out


def test_parse_distance():
    assert parse_distance("3") == 3
    assert parse_distance("0") == 0
    with pytest.raises(ValueError):
        parse_distance("-1")
    with pytest.raises(ValueError):
        parse_distance("two")


# ------------------------------------------------------ adding words
def test_add_typed_word_and_find_it_later(session):
    out = session(["zzyzxville", "y", "zzyzxville", ":quit"])
    assert "Add 'zzyzxville' to the dictionary?" in out
    assert "Added 'zzyzxville'" in out
    assert "Status: found in the dictionary" in out  # second search
    assert session.custom.read_text().split() == ["zzyzxville"]

    # A fresh session (new tree) still knows the word.
    later = session(["zzyzxvile", ":quit"], distance=1)
    assert "zzyzxville" in later


def test_decline_add(session):
    out = session(["zzyzxville", "n", ":quit"])
    assert "Added" not in out
    assert not session.custom.exists()


def test_no_prompt_for_existing_word(session):
    out = session(["hello", ":quit"])
    assert "Add '" not in out


def test_add_command_help_and_unknown(session):
    out = session([":add pythonista", ":add two words", ":help", ":bogus", ":quit"])
    assert "Added 'pythonista'" in out
    assert "letters only" in out
    assert "Commands:" in out
    assert "Unknown command ':bogus'" in out


def test_quit_aliases(session):
    for word in (":q", ":quit", ":exit"):
        out = session(["hello", word, "this line is never read"])
        assert "this line is never read" not in out


# --------------------------------------------------------- helper functions
def test_add_word_function(tmp_path):
    tree = BKTree(["apple"])
    custom = tmp_path / "sub" / "c.txt"
    assert "Added 'banana'" in add_word(tree, custom, "  Banana ")
    assert "banana" in tree
    assert "already in the dictionary" in add_word(tree, custom, "banana")
    assert "letters only" in add_word(tree, custom, "b4nana")
    assert custom.read_text() == "banana\n"


def test_add_word_repairs_missing_trailing_newline(tmp_path):
    custom = tmp_path / "c.txt"
    custom.write_text("alpha")  # no trailing newline
    add_word(BKTree(), custom, "beta")
    assert custom.read_text().split() == ["alpha", "beta"]


def test_load_tree_merges_custom_words(tmp_path):
    base = tmp_path / "base.txt"
    base.write_text("apple\nbanana\n")
    custom = tmp_path / "custom.txt"
    custom.write_text("cherry\n")
    tree = load_tree(base, custom)
    assert len(tree) == 3 and "cherry" in tree
    assert len(load_tree(base, tmp_path / "missing.txt")) == 2


# ------------------------------------------------- real program, end to end
def test_program_starts_and_searches():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "main.py")],
        input="hello\n:quit\n",
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )
    assert proc.returncode == 0
    assert "Loaded 1500 words" in proc.stdout
    assert "Status: found in the dictionary" in proc.stdout
