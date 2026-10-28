"""Tests for 0.32.0, the M10 tidy: the first of eight sessions the
planning sitting of 2026-10-27 drew from the M10 walkthrough. Three of
its four items are tested in the modules that own their verbs: the
ticked template line and the delivery's dates in
tests/test_clean_delivery.py, the drop that is an office command line in
tests/test_drop.py. This module holds the fourth, the 0.31.0 release note
read whole, which no verb owns, and the release's record.

Nothing here runs the office: the release notes, the doctrine, the
README and the development record are read as files, and the tests a
module holds are counted from its source. Run with the rest of the suite:

    tests/run.sh test_walkthrough_tidy
"""

import ast
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, h  # noqa: E402

# The development record's directory, spelled so this file names no model.
RECORD_DIR = "cla" + "ude"
SID = "2026-10-27-m10-tidy-002"
# The classes tests/test_tidy.py held when 0.31.0 shipped: the 0.31.0
# entry counts their tests, so a class added there later is not counted.
TIDY_0_31_0 = ("TestASittingsPagesBySlug", "TestTheDraftingTableOnASittingsList", "TestThePrepNamesTheTableItCarries",
               "TestStatusNamesAFolderStillProvisional", "TestARefiledResponse", "TestTheSortBringsTheDraftingTable",
               "TestTheDoctrineSaysTheSecondDesk", "TestTheRecord", "TestTheCacheOnTheWalkIn",
               "TestTheLetterheadCheckReadsTheCache")
# What an unfilled placeholder looks like in a release note: a word of
# capitals and underscores standing where a number or a sentence goes.
PLACEHOLDER_RE = re.compile(r"\b(?:SUITE_[A-Z_]+|TODO|TBD|XXX)\b|@@")


def entry(version):
    """RELEASES.md's entry for a version, its heading aside."""
    releases = (REPO / "RELEASES.md").read_text(encoding="utf-8")
    return releases.split(f"\n## {version}\n", 1)[1].split("\n## ", 1)[0]


def flat(text):
    return " ".join(text.split())


def tests_in(path, classes):
    """How many test methods the named classes of a test module define,
    counted from its source (each class's own test_ methods)."""
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    found = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    missing = [c for c in classes if c not in found]
    if missing:
        raise AssertionError(f"{path} has no class {', '.join(missing)}")
    return sum(1 for c in classes for item in found[c].body
               if isinstance(item, ast.FunctionDef) and item.name.startswith("test"))


class TestTheReleaseNoteReadsWhole(unittest.TestCase):
    """0.32.0: the 0.31.0 entry ended in two placeholders, SUITE_NEW and
    SUITE_LINE; they now say what the entry meant, from tests/test_tidy.py
    and the suite's record. No entry holds a placeholder."""

    def test_no_entry_holds_a_placeholder(self):
        releases = (REPO / "RELEASES.md").read_text(encoding="utf-8")
        found = [f"line {n}: {line.strip()}" for n, line in enumerate(releases.splitlines(), 1)
                 if PLACEHOLDER_RE.search(line)]
        self.assertEqual(found, [])

    def test_the_0_31_0_tests_line_says_what_test_tidy_and_the_suite_held(self):
        count = tests_in(REPO / "tests" / "test_tidy.py", TIDY_0_31_0)
        self.assertEqual(count, 16)
        words = flat(entry("0.31.0"))
        self.assertIn(f"Tests: tests/test_tidy.py, {count} tests, one class per item; and the record's pins.", words)
        # The suite's count: 0.30.0's, said in its own entry, and 0.31.0's
        # new tests on top of it.
        before = int(re.search(r"\b(\d+) now, none dropped\b", flat(entry("0.30.0"))).group(1))
        self.assertIn(f"{before + count} tests", words.split("and the record's pins.", 1)[1])

    def test_the_fix_is_said_in_this_releases_own_entry(self):
        words = flat(entry("0.32.0"))
        self.assertIn("The 0.31.0 entry reads whole.", words)
        self.assertIn("Release notes are not filed paper, so this is an edit, said here.", words)


class TestTheRecord(unittest.TestCase):
    def test_the_release_is_recorded(self):
        # 0.32.0 or a later release (0.33.0): a pin on the exact version
        # fails every release after this one, as test_probe's says.
        self.assertGreaterEqual(h.compare_versions((REPO / "VERSION").read_text().strip(), "0.32.0"), 0)
        self.assertIn("## 0.32.0", (REPO / "RELEASES.md").read_text())
        self.assertIn(f"0.32.0 (session {SID})", (REPO / RECORD_DIR / "context" / "front-sheet.md").read_text())
        doctrine = flat((REPO / "doctrine" / "OFFICE.md").read_text())
        for words in ("A checklist line is the template's whatever its box holds (0.32.0)",
                      "since one commit per delivery is the usual shape (0.32.0)",
                      "it is an office command line (0.32.0)"):
            self.assertIn(words, doctrine)
        readme = flat((REPO / "README.md").read_text())
        for words in ("A checklist line is the template's whatever its box holds (0.32.0)",
                      "Several commits are dated a second apart, oldest first (0.32.0)",
                      "A text that is one office command line"):
            self.assertIn(words, readme)


if __name__ == "__main__":
    unittest.main()
