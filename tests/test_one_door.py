"""Tests for 0.23.0, one door: new work from the occupant's words through
office start new, the folder's provisional fields and the Structure a
session sends back, ratification out of the landing and into the next
brief, and a clipboard copy the office claims only when it is true.

bale is never needed: the fake bale of tests/test_land.py packs, applies
and keeps the open sessions. The terminal tests drive a pseudo-terminal
and run in the serial lane. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_land import LandCase, response_tarball  # noqa: E402
from test_start import WSL_KERNEL, on_a_terminal, opener_from, recording_windows  # noqa: E402

import office_sort as osort  # noqa: E402  (lib/ is on sys.path through test_office)

TEMPLATES = REPO / "templates"


def office_lines_on_ratification(text):
    """The office's own lines that speak of ratification (bale's relay
    block names itself the ratification relay; that is bale's)."""
    return [l for l in text.splitlines() if l.startswith("[office]") and "ratif" in l]
WORDS = "Fix the login page\nIt fails on narrow screens."


def a_folder(path, title="Fix the login page", fields=None, sessions=(), asked=None):
    """A folder.md from the install's template: the field block given,
    the sessions recorded one line each, and his words in Asked."""
    values = {"title": title, "number": "3", "status": "queued", "queued": "2026-10-14",
              "history": "2026-10-14 queued: office open"}
    values.update(fields or {})
    late = {k: values.pop(k) for k in ("goal", "provisional") if k in values}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(h.render_template((TEMPLATES / "folder.md").read_text(), values))
    for key, value in late.items():
        h.folder_set_field(path, key, value)
    for sid in sessions:
        h.record_session(path, sid)
    if asked:
        h.record_asked(path, asked, "The occupant, at office open")
    return path


class TestTheReadings(unittest.TestCase):
    """The pieces each piece of the door reads and writes, in this process."""

    def setUp(self):
        self.tmp = Env(self).tmp

    def test_provisional_names_only_the_three_fields_in_their_order(self):
        self.assertEqual(h.normalize_field("provisional", "goal, Title"), "title, goal")
        for bad in ("colour", "size, size", ""):
            with self.assertRaises(h.HelperError):
                h.normalize_field("provisional", bad)

    def test_status_names_a_provisional_line_that_does_not_read(self):
        root = self.tmp / "office"
        a_folder(root / "desk/2026-10-14-a/folder.md", fields={"provisional": "title"})
        md = a_folder(root / "desk/2026-10-14-b/folder.md", fields={"number": "4"})
        md.write_text(md.read_text().replace("- queued: 2026-10-14\n", "- queued: 2026-10-14\n- provisional: colour\n"))
        md = a_folder(root / "desk/2026-10-14-c/folder.md", fields={"number": "5"})
        md.write_text(md.read_text().replace("- queued: 2026-10-14\n", "- queued: 2026-10-14\n- provisional: goal\n"))
        problems, _ = h.folder_check(root)
        self.assertEqual([p for p in problems if "provisional" in p], [
            "desk/2026-10-14-b: the provisional line does not read: provisional names fields from title, size, "
            "goal, not 'colour'",
            "desk/2026-10-14-c: provisional marks goal, and the folder carries no goal line"])

    def test_a_brief_carries_ratifications_kept_to_the_byte(self):
        brief = "\n".join([
            "# Brief", "",
            "--- RATIFIED 2026-10-15-alpha-login-001 ---",
            "--- RATIFIED 2026-10-15-alpha-docs-002, except: the slug rule; fixed in this session ---",
            "```", "--- RATIFIED 2026-10-15-quoted-003 ---", "```",
            "--- NOTEPAD PAGE BEGIN notepad/2026-10-15-sitting.md ---",
            "--- RATIFIED 2026-10-15-in-a-page-004 ---",
            "--- NOTEPAD PAGE END ---",
            "--- RATIFIED alpha ---",
            "--- RATIFIED 2026-10-15-alpha-login-001 ---", ""])
        marks, problems = h.brief_ratifications(brief)
        self.assertEqual(marks, [("2026-10-15-alpha-login-001", None),
                                 ("2026-10-15-alpha-docs-002", "the slug rule; fixed in this session")])
        self.assertEqual(len(problems), 2, problems)
        self.assertIn("--- RATIFIED alpha ---", problems[0])
        self.assertIn("ratified twice", problems[1])

    def test_a_ratification_from_a_brief_adds_a_line_and_rewrites_nothing(self):
        md = a_folder(self.tmp / "filing-cabinet/2026-10-14-a/folder.md",
                      sessions=("2026-10-14-alpha-login-001", "2026-10-15-alpha-login-002"))
        before = md.read_bytes()
        said = h.ratify_session(md, "2026-10-14-alpha-login-001", "2026-10-16", at_end=True)
        self.assertEqual(said, "2026-10-14-alpha-login-001 ratified 2026-10-16")
        after = md.read_bytes()
        self.assertIsNone(h.insertion_problem(before, after))
        sessions = after.decode().split("## Sessions\n")[1].split("\n## ")[0].rstrip().splitlines()
        self.assertEqual(sessions[-3:], ["- 2026-10-14-alpha-login-001", "- 2026-10-15-alpha-login-002",
                                         "- 2026-10-14-alpha-login-001 ratified 2026-10-16"])
        with self.assertRaises(h.AlreadyRatified):
            h.ratify_session(md, "2026-10-14-alpha-login-001", "2026-10-17", at_end=True)
        self.assertEqual(md.read_bytes(), after)

    def test_a_folder_is_finished_when_its_one_session_landed(self):
        md = a_folder(self.tmp / "desk/2026-10-14-a/folder.md", sessions=("2026-10-14-alpha-login-001",))
        self.assertEqual(h.finished_folder(md, "2026-10-14-alpha-login-001"), (True, None))
        h.record_session(md, "2026-10-15-alpha-login-002")
        ok, why = h.finished_folder(md, "2026-10-15-alpha-login-002")
        self.assertFalse(ok)
        self.assertIn("1 other session(s)", why)

    def test_a_structure_files_over_the_provisional_fields_and_keeps_his_own(self):
        md = a_folder(self.tmp / "desk/2026-10-14-a/folder.md",
                      fields={"size": "small", "goal": "Fix the login page; It fails on narrow screens.",
                              "provisional": "title, goal"},
                      asked=WORDS)
        asked = md.read_text().split("## Asked")[1].split("## Questions")[0]
        wrote, said = h.file_structure(md, [("title", "Fix the login page on narrow screens"),
                                           ("size", "medium"),
                                           ("goal", "Fix the login page's layout on narrow screens")])
        self.assertTrue(wrote)
        text = md.read_text()
        self.assertTrue(text.startswith("# Fix the login page on narrow screens\n"))
        self.assertIn("- goal: Fix the login page's layout on narrow screens\n", text)
        self.assertIn("- size: small\n", text)  # his own, never provisional: kept
        self.assertNotIn("provisional", text)
        self.assertEqual(text.split("## Asked")[1].split("## Questions")[0], asked)
        self.assertEqual(said, ["title 'Fix the login page' -> 'Fix the login page on narrow screens'",
                                "size kept: 'small' is the folder's own",
                                "goal 'Fix the login page; It fails on narrow screens.' -> "
                                "\"Fix the login page's layout on narrow screens\""])
        self.assertEqual(h.folder_check(self.tmp)[0], [])

    def test_a_structure_off_the_format_is_said_and_never_filed(self):
        ok = osort.parse_notes("## Structure\n\n- title: a\n- size: small\n- goal: b\n")["structure"]
        self.assertEqual(ok, {"pairs": [("title", "a"), ("size", "small"), ("goal", "b")], "problems": []})
        bad = osort.parse_notes("## Structure\n\n- size: small\n- title: a\n- goal: b\n")["structure"]
        self.assertEqual(bad["problems"], ["its lines are not title, size, goal, one each and in that order"])
        prose = osort.parse_notes("## Structure\n\nThe title is fine.\n")["structure"]
        self.assertIn("a line that is not `- KEY: VALUE`: The title is fine.", prose["problems"])


NOTES = """# Notes

## Structure

- title: Fix the login page on narrow screens
- size: medium
- goal: Fix the login page's layout on narrow screens

## Walkthrough

### What changed

- the login page.

## Delivery

- to: nobody
"""


class TestOneDoor(LandCase):
    """office start new, piped: the words and where the work lands given,
    nothing asked; and what follows from it at the landing and the next
    start."""

    def new_job(self, *more, words=WORDS):
        proc = self.run_office("start", "new", "--words", words, "--on", "alpha", *more, check=0)
        sid = re.search(r"^Packed (\S+) for desk/(\S+)\.$", proc.stdout, re.M)
        return sid.group(1), self.root / "desk" / sid.group(2) / "folder.md", proc

    def test_new_work_from_his_words_goes_out_in_one_motion(self):
        sid, md, proc = self.new_job()
        text = md.read_text()
        self.assertTrue(text.startswith("# Fix the login page\n"), text)
        self.assertIn("- lane: alpha\n- source: the occupant\n"
                      "- goal: Fix the login page; It fails on narrow screens.\n"
                      "- provisional: title, size, goal\n", text)
        self.assertIn("> Fix the login page\n> It fails on narrow screens.\n", text)
        self.assertIn(f"- {sid}\n", text)
        self.assertIn("Goal, verbatim from the request manifest: Fix the login page; It fails on narrow screens.",
                      "\n".join(opener_from(proc.stdout)))
        self.assertIn("the opener is not on the clipboard: off a terminal the office copies nothing", proc.stderr)
        self.assertEqual(h.folder_check(self.root)[0], [])

    def test_piped_it_asks_nothing_and_names_its_flags_before_anything_is_written(self):
        desk = sorted(p.name for p in (self.root / "desk").iterdir())
        proc = self.run_office("start", "new", check=1)
        self.assertIn("office start new takes the job in your words: --words TEXT", proc.stderr)
        proc = self.run_office("start", "new", "--words", WORDS, check=1)
        self.assertIn("say where the work lands: --in-office, or --on PROJECT (alpha)", proc.stderr)
        proc = self.run_office("start", self.name, "--words", WORDS, check=1)
        self.assertIn("--words opens a new job from your words, so it takes no folder", proc.stderr)
        self.assertEqual(sorted(p.name for p in (self.root / "desk").iterdir()), desk)

    def test_the_landing_files_the_structure_and_asks_nothing_of_ratification(self):
        sid, md, _ = self.new_job()
        tb = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes=NOTES)
        proc = self.run_office("land", sid, "--response", str(tb), check=0)
        rel = md.parent.relative_to(self.root)
        self.assertIn(f"Structure: {rel}: title 'Fix the login page' -> 'Fix the login page on narrow screens'; "
                      "size 'small' -> 'medium'; goal 'Fix the login page; It fails on narrow screens.' -> "
                      "\"Fix the login page's layout on narrow screens\"", proc.stderr)
        text = md.read_text()
        self.assertTrue(text.startswith("# Fix the login page on narrow screens\n"))
        self.assertIn("- size: medium\n", text)
        self.assertNotIn("provisional", text)
        self.assertIn("> Fix the login page\n> It fails on narrow screens.\n", text)
        self.assertEqual(office_lines_on_ratification(proc.stdout + proc.stderr), [])
        self.assertIn(f"recorded {sid} alone, and it landed applied; piped, the folder stays open", proc.stderr)

    def test_a_briefs_ratification_is_filed_wherever_the_folder_is(self):
        first = self.start(self.name, "--on", "alpha", "--goal", "Fix the login redirect")
        response_tarball(self.downloads, first, {"src/a.py": "fixed\n"})
        self.run_office("land", first, "--close", check=0)
        cabinet = self.root / "filing-cabinet" / self.name / "folder.md"
        self.assertTrue(cabinet.is_file())
        before = cabinet.read_bytes()
        brief = self.e.tmp / "brief.md"
        brief.write_text(f"# Brief\n\nThe next job.\n\n--- RATIFIED {first} ---\n"
                         "--- RATIFIED 2026-01-01-nobody-001, except: nothing; it never ran ---\n")
        second, md, proc = self.new_job("--brief", str(brief), "--write", "README.md", words="Tidy the docs")
        day = re.search(rf"^- {first} ratified (\S+)$", cabinet.read_text(), re.M)
        self.assertIsNotNone(day, cabinet.read_text())
        self.assertIsNone(h.insertion_problem(before, cabinet.read_bytes()))
        self.assertIn(f"filed the planner's ratification from {second}'s brief in filing-cabinet/{self.name}: "
                      f"{first} ratified {day.group(1)}", proc.stderr)
        self.assertIn("the brief ratifies 2026-01-01-nobody-001, which no folder records; nothing was filed for it",
                      proc.stderr)
        self.assertIn(f"office start: the planner's ratifications from {second}'s brief", self.subjects(3))
        # The same ratification again is said and left: one line per session.
        _, _, proc = self.new_job("--brief", str(brief), "--write", "docs", words="Tidy the docs again")
        self.assertIn(f"the brief ratifies {first}, and filing-cabinet/{self.name} holds its ratification already",
                      proc.stderr)
        self.assertEqual(cabinet.read_text().count(" ratified "), 1)


class TestOneDoorOnATerminal(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def machine(self, text):
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(text)

    def test_his_words_through_the_one_door(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "new"], self.root, self.e.env, [
            (b"The job, in your own words", "Write the alpha release notes"),
            (b"", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("your words name alpha, one of this office's projects: the folder's lane", seen)
        self.assertIn("the work lands on alpha, the project the folder's lane names", seen)
        self.assertIn("Packed ", seen)
        self.assertNotIn("Which project", seen)
        self.assertNotIn("Where the work lands", seen)

    def test_the_landing_asks_nothing_and_its_copy_is_checked_last(self):
        clip = self.e.tmp / "clipboard.txt"
        self.machine(f'clipboard_command = "tee {clip}"\npaste_command = "cat {clip}"\n')
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "x\n"})
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "land"], self.root, self.e.env, [
            (b"merge into origin (default)", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertEqual(office_lines_on_ratification(seen.replace("\r\n", "\n")), [])
        self.assertNotIn("Did the planner ratify", seen)
        self.assertIn(f"recorded {sid} alone, and it landed applied: the job is finished, so the folder is closed "
                      f"(office reopen {self.name} brings it back", seen)
        said = f"the block for the planner is on the clipboard (tee {clip}; read back and checked)"
        self.assertIn(said, seen)
        # The office's copy is the last thing land does.
        self.assertGreater(seen.index(said), seen.index("After land, in"))
        self.assertTrue(clip.read_text().startswith(f"=== RELAY BEGIN {sid} to planner ==="))

    def test_a_copy_that_reads_back_otherwise_is_said_and_the_block_printed_again(self):
        clip = self.e.tmp / "clipboard.txt"
        self.machine(f'clipboard_command = "tee {clip}"\npaste_command = "printf something-else"\n')
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "x\n"})
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "land", "--leave-open"], self.root, self.e.env, [
            (b"merge into origin (default)", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("the block for the planner is NOT on the clipboard as printed", seen)
        self.assertNotIn("is on the clipboard", seen)
        tail = seen.split("The block for the planner, whole, to copy from here:")[1]
        self.assertIn(f"=== RELAY BEGIN {sid} to planner ===", tail)

    def test_on_wsl_the_copy_keeps_its_em_dash(self):
        windows, _ = recording_windows(self.e.tmp / "windows", clip_sets_clipboard=True)
        kernel = self.e.tmp / "proc-version"
        kernel.write_text(WSL_KERNEL)
        env = dict(self.e.env, OFFICE_PROC_VERSION=str(kernel), OFFICE_DESKTOP_PATH=str(windows),
                   PATH=f"{windows}:{self.e.env['PATH']}")
        goal = "Fix the login — it fails on narrow screens"
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", self.name, "--on", "alpha",
                                          "--goal", goal], self.root, env, [])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"the opener is on the clipboard ({windows / 'clip.exe'}; read back and checked)", seen)
        held = (windows / "clipboard.txt").read_text(encoding="utf-8")
        self.assertIn("—", held)
        self.assertEqual(held.splitlines(), opener_from(seen.replace("\r\n", "\n")))


if __name__ == "__main__":
    unittest.main()
