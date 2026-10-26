import subprocess
import sys
from pathlib import Path

from bktree import BKTree
from main import add_word, load_tree

ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args, input_text=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "main.py"), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        input=input_text,
        timeout=60,
    )


# ------------------------------------------------------------- one-off queries
def test_cli_finds_correction(tmp_path):
    proc = run_cli("helo", "-d", "1", "-n", "50", "-c", str(tmp_path / "c.txt"))
    assert proc.returncode == 0
    assert "hello" in proc.stdout


def test_cli_no_match(tmp_path):
    proc = run_cli("qqqqqqqq", "-d", "1", "-c", str(tmp_path / "c.txt"))
    assert proc.returncode == 0
    assert "no similar words found" in proc.stdout


def test_cli_distance_option_changes_results(tmp_path):
    custom = str(tmp_path / "c.txt")
    narrow = run_cli("helo", "-d", "0", "-c", custom).stdout
    wide = run_cli("helo", "-d", "2", "-n", "100", "-c", custom).stdout
    assert "no similar words found" in narrow
    assert "distance 2" in wide


def test_cli_rejects_negative_distance(tmp_path):
    proc = run_cli("helo", "-d", "-1", "-c", str(tmp_path / "c.txt"))
    assert proc.returncode != 0
    assert "cannot be negative" in proc.stderr


def test_cli_add_flag_saves_word(tmp_path):
    custom = tmp_path / "c.txt"
    proc = run_cli("flibbertigibbet", "--add", "-c", str(custom))
    assert proc.returncode == 0
    assert "Added 'flibbertigibbet'" in proc.stdout
    assert custom.read_text().split() == ["flibbertigibbet"]


# ------------------------------------------------------------ interactive mode
def test_interactive_change_distance(tmp_path):
    proc = run_cli("-c", str(tmp_path / "c.txt"), input_text=":d 1\nhelo\nn\n:quit\n")
    assert "Max distance set to 1" in proc.stdout
    assert "[d=1]>" in proc.stdout
    assert "max distance 1" in proc.stdout


def test_interactive_bad_distance_is_rejected(tmp_path):
    proc = run_cli("-c", str(tmp_path / "c.txt"), input_text=":d abc\n:d -3\n:quit\n")
    assert proc.stdout.count("Example:  :d 2") == 2
    assert "[d=2]>" in proc.stdout  # unchanged


def test_interactive_add_typed_word_and_find_it_next_run(tmp_path):
    custom = tmp_path / "c.txt"
    proc = run_cli("-c", str(custom), input_text="zzyzxville\ny\n:quit\n")
    assert "Add 'zzyzxville' to the dictionary?" in proc.stdout
    assert "Added 'zzyzxville'" in proc.stdout
    assert custom.read_text().split() == ["zzyzxville"]

    # A fresh run loads the saved word.
    again = run_cli("zzyzxvile", "-d", "1", "-c", str(custom))
    assert "zzyzxville" in again.stdout


def test_interactive_decline_add(tmp_path):
    custom = tmp_path / "c.txt"
    proc = run_cli("-c", str(custom), input_text="zzyzxville\nn\n:quit\n")
    assert "Added" not in proc.stdout
    assert not custom.exists()


def test_interactive_no_prompt_for_existing_word(tmp_path):
    proc = run_cli("-c", str(tmp_path / "c.txt"), input_text="hello\n:quit\n")
    assert "Add '" not in proc.stdout


def test_interactive_add_command_and_help(tmp_path):
    custom = tmp_path / "c.txt"
    proc = run_cli("-c", str(custom), input_text=":add pythonista\n:add two words\n:help\n:bogus\n:quit\n")
    assert "Added 'pythonista'" in proc.stdout
    assert "letters only" in proc.stdout
    assert "Commands:" in proc.stdout
    assert "Unknown command ':bogus'" in proc.stdout


def test_interactive_rejects_multiple_words(tmp_path):
    proc = run_cli("-c", str(tmp_path / "c.txt"), input_text="hello world\n:quit\n")
    assert "one word at a time" in proc.stdout


# -------------------------------------------------------------- helper functions
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


# ------------------------------------------------------ dictionary status line
def test_status_found_for_dictionary_word(tmp_path):
    proc = run_cli("hello", "-d", "1", "-c", str(tmp_path / "c.txt"))
    assert "Status: found in the dictionary" in proc.stdout
    assert "NOT in the dictionary" not in proc.stdout


def test_status_not_found_for_misspelling(tmp_path):
    proc = run_cli("helo", "-d", "1", "-c", str(tmp_path / "c.txt"))
    assert "Status: NOT in the dictionary" in proc.stdout


def test_status_is_case_insensitive(tmp_path):
    proc = run_cli("HELLO", "-d", "0", "-c", str(tmp_path / "c.txt"))
    assert "Status: found in the dictionary" in proc.stdout


def test_status_works_with_distance_zero(tmp_path):
    proc = run_cli("helo", "-d", "0", "-c", str(tmp_path / "c.txt"))
    assert "Status: NOT in the dictionary" in proc.stdout
    assert "no similar words found" in proc.stdout


def test_status_changes_after_adding_word(tmp_path):
    proc = run_cli("-c", str(tmp_path / "c.txt"), input_text="zzyzxville\ny\nzzyzxville\n:quit\n")
    assert "Status: NOT in the dictionary" in proc.stdout
    assert "Status: found in the dictionary" in proc.stdout
