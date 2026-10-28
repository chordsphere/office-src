"""Tests for 0.33.0's first item: an answer of several lines is seen whole
before it goes.

bin/office's ask_words (a new job's words, a planner sitting's) and
ask_paragraph (the profile's questions) take an answer that may run to
several lines, a blank line ending it, and a line already ended cannot be
edited at a terminal's prompt. Now the whole answer is shown back,
numbered, with one question before anything is written or packed: keep it,
redo it, more lines, or a line's number to type that line again. With
VISUAL or EDITOR set and the terminal his, the answer is taken in that
editor instead, as git takes a commit message.

Every test but the last drives a pseudo-terminal and runs in the serial
lane; bale is the fake of tests/test_land.py, and the editor is a script
each test writes in its own temporary directory. Run with the rest of the
suite:

    tests/run.sh test_answer_review
"""

import os
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO  # noqa: E402
from test_land import LandCase  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_founding_door import DoorCase  # noqa: E402

KEEP = b"[keep]: "
AGAIN = b"again (a blank line takes it out): "


def packed_folder(seen):
    return re.search(r"Packed (\S+) for (desk/\S+)\.", seen).group(2)


def an_editor(at, body):
    """An editor script: it keeps a copy of the file it was given (the
    seed) beside itself, then writes body above the seed's lines, as a
    person typing an answer above git's comment lines does. Its last
    argument is the file, so an EDITOR with arguments of its own works."""
    path = pathlib.Path(at) / "an-editor"
    seed = pathlib.Path(at) / "seed-copy"
    path.write_text("#!/bin/sh\n"
                    'for f; do :; done\n'
                    f'cp "$f" "{seed}"\n'
                    f"{{ printf '{body}'; cat \"{seed}\"; }} > \"$f\"\n")
    path.chmod(0o755)
    return path, seed


class TestAnAnswerIsSeenWholeBeforeItGoes(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def session_packs(self):
        """The argv of each session pack the fake bale ran (not the context packs)."""
        return [argv for _, argv, _ in self.fake.calls_of("pack") if "--context" not in argv]

    def new_job(self, steps, *flags):
        return on_a_terminal(self, [str(self.e.office_bin), "start", "new", "--in-office", *flags], self.root,
                             self.e.env, steps)

    def test_a_line_is_typed_again_and_more_lines_follow_before_anything_is_written(self):
        code, seen = self.new_job([
            (b"The job, in your own words", "Fix the logn page\nIt fails on phones.\n"),
            (KEEP, "1"),
            (b"line 1 was: Fix the logn page", None),
            (AGAIN, "Fix the login page"),
            (b"1  Fix the login page", "more"),
            (b"  > ", "Even on tablets.\n"),
            (b"3  Even on tablets.", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Your answer, as it stands:", seen)
        self.assertIn("Keep it? keep, redo, more, or a line's number to type it again (--title gives a title "
                      "instead) [keep]:", seen)
        md = (self.root / packed_folder(seen) / "folder.md").read_text()
        self.assertTrue(md.startswith("# Fix the login page\n"), md[:80])
        for line in ("Fix the login page", "It fails on phones.", "Even on tablets."):
            self.assertIn(line, md)
        self.assertNotIn("logn", md)
        argv, = self.session_packs()
        self.assertNotIn("logn", " ".join(argv))

    def test_redo_asks_again_from_the_first_line_and_only_the_kept_words_go(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "new", "--planner"], self.root,
                                   self.e.env, [
            (b"in your own words (--words)", "Plan the beta release\n"),
            (b"(--words) [keep]: ", "redo\nPlan the alpha release\n"),
            (b"1  Plan the alpha release", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertEqual(seen.count("What you want a planner for, in your own words (--words) [several lines"), 2)
        argv, = self.session_packs()
        self.assertIn("Plan the alpha release", argv)
        self.assertNotIn("beta", " ".join(argv))
        self.assertNotIn("Plan the beta release", (self.root / packed_folder(seen) / "folder.md").read_text())

    def test_question_mark_explains_a_key_it_does_not_take_is_said_and_no_line_left_asks_again(self):
        code, seen = self.new_job([
            (b"The job, in your own words", "Typo\n"),
            (KEEP, "?"),
            (b"every line can be changed.", "9"),
            (b"(1 to 1); ? explains it", "1"),
            (AGAIN, ""),
            (b"an answer is needed here: the question again", "Write the plan\n"),
            (b"1  Write the plan", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("redo asks the question again from its first line", " ".join(seen.split()))
        self.assertTrue((self.root / packed_folder(seen) / "folder.md").read_text().startswith("# Write the plan\n"))

    def test_with_editor_set_the_answer_is_written_there_and_not_shown_back(self):
        editor, seed = an_editor(self.e.tmp, "Fix the login page\\n\\n   It fails on phones.   \\n")
        self.e.env["EDITOR"] = f"{editor} --wait"
        code, seen = self.new_job([])
        self.assertEqual(code, 0, seen)
        self.assertIn("taking your answer in", seen)
        self.assertNotIn("Your answer, as it stands", seen)
        self.assertNotIn("[several lines welcome", seen)
        md = (self.root / packed_folder(seen) / "folder.md").read_text()
        self.assertTrue(md.startswith("# Fix the login page\n"), md[:80])
        self.assertIn("It fails on phones.\n", md)
        self.assertNotIn("It fails on phones.   ", md)
        self.assertNotIn("Your answer goes above these lines", md)
        # The seed: an empty line for the answer, then the question, its
        # help and what the file takes, as comment lines.
        lines = seed.read_text().splitlines()
        self.assertEqual(lines[0], "")
        self.assertEqual(lines[1], "# The job, in your own words (--title gives a title instead)")
        self.assertTrue(all(line.startswith("#") for line in lines[1:]), lines)
        said = " ".join(" ".join(line.lstrip("#").strip() for line in lines).split())
        self.assertIn("The first line becomes the folder's title", said)
        self.assertIn("Lines starting with # are left out, and blank lines too", said)

    def test_an_editor_that_fails_or_comes_back_empty_hands_the_answer_to_the_prompt(self):
        self.e.env["EDITOR"] = "false"
        code, seen = self.new_job([
            (b"exited 1, so your answer is asked here instead", None),
            (b"The job, in your own words", "Write the plan\n"),
            (KEEP, ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Your answer, as it stands:", seen)
        editor, _ = an_editor(self.e.tmp, "")
        # VISUAL wins over EDITOR, except on a dumb terminal, as git reads them.
        self.e.env.update(VISUAL="false", TERM="dumb", EDITOR=str(editor))
        # (A planner sitting: an office session is out already, and office
        # sessions take turns on the notepad.)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "new", "--planner"], self.root,
                                   self.e.env, [
            (b"came back with no answer, and your words are needed here", None),
            (b"in your own words (--words)", "Plan the alpha notes\n"),
            (b"(--words) [keep]: ", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("false exited", seen)

class TestPipedNothingIsAsked(LandCase):
    """Beside the terminal class: piped, no question and no editor."""

    def test_piped_the_editor_never_runs_and_the_flag_twin_takes_the_words(self):
        editor, seed = an_editor(self.e.tmp, "Not these words\\n")
        self.e.env["EDITOR"] = str(editor)
        proc = self.run_office("start", "new", "--in-office", "--words", "Write the plan", check=0)
        self.assertFalse(seed.exists())
        self.assertNotIn("Keep it?", proc.stderr)
        self.assertIn("Packed ", proc.stdout)


class TestTheProfilesAnswersAreSeenWhole(DoorCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_a_line_taken_out_is_gone_and_an_answer_with_none_left_skips(self):
        argv = [str(self.e.office_bin), "init", str(self.root), "--no-projects", "--audiences", "a", "--site", "s",
                "--timezone", "America/Chicago", "--house-rules", "h", "--when-to-open", "w", "--spaces", "x"]
        code, seen = on_a_terminal(self, argv, self.e.home, self.e.env, [
            (b"(--purpose) [several lines welcome", "My own tools.\nAnd my life.\n"),
            (b"(--purpose) [keep]: ", "2"),
            (AGAIN, "\nkeep"),
            (b"(--not-for) [several lines welcome", "Oops\n"),
            (b"(--not-for) [keep]: ", "1\n"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("your answers go to the founding session as you keep them", seen)
        answers = (self.founding_folder() / "answers.md").read_text()
        self.assertIn("> My own tools.", answers)
        for gone in ("And my life.", "Oops"):
            self.assertNotIn(gone, answers)


class TestTheRecord(unittest.TestCase):
    def test_the_doctrine_the_readme_and_the_release_say_it(self):
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        verbs = doctrine.split("## 7. Verbs", 1)[1].split("## 8.", 1)[0]
        self.assertIn("So before anything is written or packed the whole answer is shown back, numbered, with one "
                      "question (0.33.0)", verbs)
        self.assertIn("With VISUAL or EDITOR set and the terminal his, the answer is taken in that editor", verbs)
        readme = " ".join((REPO / "README.md").read_text().split())
        self.assertIn("With `VISUAL` or `EDITOR` set, you write them in that editor instead", readme)
        releases = (REPO / "RELEASES.md").read_text()
        entry = releases.split("## 0.33.0", 1)[1].split("\n## ", 1)[0]
        self.assertIn("test_answer_review.py", entry)

    def test_the_editor_draws_on_stderr_since_start_new_reads_the_words_in_a_substitution(self):
        # office start new runs open's code inside $(...), so stdout is a
        # pipe there: the editor must draw on the terminal stderr is.
        text = (REPO / "bin/office").read_text()
        body = text.split("\nedit_answer() {", 1)[1].split("\n}\n", 1)[0]
        self.assertIn('"$__e_file" >&2', body)
        self.assertIn('can_edit() { [ -n "$(answer_editor)" ] && [ -t 0 ] && [ -t 2 ]; }', text)
        self.assertIn('rel="$(OPEN_FOR_START=1', text)


if __name__ == "__main__":
    unittest.main()
