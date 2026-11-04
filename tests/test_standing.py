"""Tests for office-src 0.43.0: where a sitting stands.

One class per item of the brief (2026-11-03-m10-standing-001):

1. the standing block, read and filed (office standing FOLDER): units on
   the block's shape, then the verb, piped and on a terminal;
2. office probe files a standing that rides with the probe block;
3. the home screen, the walk-in and office desk show it;
4. the briefs, the doctrine and the verbs catalog say it;
5. office land, ending the sitting, leaves the page;
6. a prep's doctrine stamped on its record line and compared;
7. the two pty harnesses kill a hung child;
8. the probe's stderr masked;
9. office start ends the sitting a brief's ENDS line names, and two
   sittings open on one folder are said;
10. the office's tail printed when land is piped;
11. review state on the tail.

The worlds are the suite's own: tests/test_land.py's LandCase (an office
scoping alpha, a fake bale that packs, opens, lands and unlocks),
tests/test_probe.py's blocks, tests/test_home_screen_offers.py's
AudienceLandCase and tests/test_pull_requests.py's fake gh. The sittings,
folders and hosts are invented. The terminal classes run in the serial
lane. Run with the rest of the suite:

    tests/run.sh test_standing
"""

import datetime as dt
import json
import os
import pathlib
import re
import signal
import sys
import types
import unittest
import unittest.mock as mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, kept_setup  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_desk_verbs import terminal  # noqa: E402
from test_land import LandCase, bundle_file, response_tarball  # noqa: E402
from test_probe import probe_block  # noqa: E402
from test_home_screen_offers import AudienceLandCase  # noqa: E402
from test_pull_requests import REMOTE, FakeGh  # noqa: E402
from test_planner_from_words import install_sha  # noqa: E402

import office_bale as ob  # noqa: E402
import office_helper as oh  # noqa: E402
import office_home as hs  # noqa: E402
import office_meeting as om  # noqa: E402
import office_probe as op  # noqa: E402
import office_review as orev  # noqa: E402
import office_standing as ost  # noqa: E402

SIT = "2026-11-03-plan-it-sitting-001"
STEPS = ("probe the office", "find where the work ran", "draft the words")
WAITING = "run the probe below, then paste what came back"
TOKEN = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"


def standing(sid=SIT, step=2, steps=STEPS, waiting=WAITING, words=None):
    """A standing block in the brief's shape: the Nth step the one it is on."""
    marks = ["x" if i < step else ">" if i == step else " " for i in range(1, len(steps) + 1)]
    return "\n".join([f"--- STANDING BEGIN {sid} ---", f"step {step} of {len(steps)}: {words or steps[step - 1]}",
                      *[f"- [{m}] {s}" for m, s in zip(marks, steps)], f"waiting on you: {waiting}",
                      "--- STANDING END ---"]) + "\n"


class SittingCase(LandCase):
    """LandCase's office with a folder for a planner sitting, plan-it, and
    the sitting out in the office (office start --read-only). The world is
    built once per process and copied for each test (tests/test_office.py
    kept_setup), as LandCase's is."""

    def setUp(self):
        kept_setup(self, "test_standing.SittingCase", SittingCase.build_sitting_world)

    def build_sitting_world(self):
        LandCase.build_world(self)
        self.plan = self.run_office("open", "plan-it", check=0).stdout.strip().split("/")[1]
        self.sit = self.sitting()
        self.page = self.root / "desk" / self.plan / "standing.md"
        self.text = self.e.tmp / "standing.txt"

    def sitting(self, goal="Plan it"):
        out = self.run_office("start", self.plan, "--in-office", "--read-only", "--goal", goal, check=0).stdout
        return re.search(r"^Packed (\S+) for ", out, re.M).group(1)

    def file(self, text, *more, check=0):
        self.text.write_text(text)
        return self.run_office("standing", self.plan, str(self.text), *more, check=check)

    def number(self):
        return re.search(r"^- number: (\d+)$", (self.root / "desk" / self.plan / "folder.md").read_text(), re.M).group(1)


# --- 1. the block, and office standing --------------------------------------------------------

class TestTheBlock(unittest.TestCase):
    def test_the_shape_reads_and_the_last_block_counts(self):
        text = "chat\n```\n" + standing(step=1) + "\nmore chat\n  " + standing().replace("\n", "\r\n  ") + "```\n"
        b = ost.read_block(text, [SIT])
        self.assertEqual((b["sid"], b["step"], b["of"], b["words"], b["waiting"]), (SIT, 2, 3, STEPS[1], WAITING))
        self.assertEqual(b["steps"], [("x", STEPS[0]), (">", STEPS[1]), (" ", STEPS[2])])
        self.assertEqual(b["lines"], standing().rstrip("\n").split("\n"))

    def test_a_block_off_the_shape_is_refused_by_name(self):
        good = standing()
        cases = (
            (good.replace("- [>]", "- [x]"), "exactly one step is `- [>]`"),
            (good.replace("- [ ]", "- [>]"), "the block marks 2"),
            (good.replace("step 2 of 3", "step 3 of 3"), "the step line says step 3, and the `- [>]` step is the 2nd"),
            (good.replace("step 2 of 3", "step 2 of 4"), "says 4 step(s), and the block lists 3"),
            (good.replace("waiting on you:", "waiting:"), "last line is `waiting on you: words`"),
            (good.replace("step 2 of 3:", "now:"), "first line is `step N of M: words`"),
            (good.replace("- [ ] draft", "* draft"), "each line between the step line and the waiting line is one step"),
            (good.replace(SIT, "plan-it"), "not `--- STANDING BEGIN SID ---`"),
            (good.replace("--- STANDING END ---\n", ""), "with no --- STANDING END --- line after it"),
            ("no block here\n", "no standing block"),
        )
        for text, words in cases:
            with self.assertRaises(ost.StandingError, msg=words) as cm:
                ost.read_block(text)
            self.assertIn(words, str(cm.exception))
        with self.assertRaises(ost.StandingError) as cm:
            ost.read_block(good, ["2026-11-03-other-001"])
        self.assertIn(f"the block is {SIT}'s, a session the folder does not record", str(cm.exception))

    def test_the_page_and_the_words(self):
        b = ost.read_block(standing())
        page = ost.page_text(b, "2026-11-03", "14:05")
        self.assertEqual(page, f"# Where the sitting stands\n\n- as of: 2026-11-03 14:05\n- sitting: {SIT}\n\n"
                               + standing())
        st = dict(b, as_of="2026-11-03 14:05", sitting=SIT)
        self.assertEqual(ost.words(st), f"step 2 of 3: {STEPS[1]}; waiting on you: {WAITING} (as of 2026-11-03 14:05)")
        self.assertEqual(ost.words(st, "2026-11-04-next-sitting-001"),
                         f"step 2 of 3: {STEPS[1]}; waiting on you: {WAITING} (as of 2026-11-03 14:05, filed by {SIT})")

    def test_split_takes_every_block_out_of_a_probes_text_and_keeps_the_last(self):
        probe = probe_block()
        text = "```\n" + probe + standing(step=1) + standing() + "```\n"
        rest, st = ost.split(text)
        self.assertEqual(rest, "```\n" + probe + "```\n")
        self.assertEqual(st, standing())
        self.assertEqual(ost.split(probe), (probe, None))
        with self.assertRaises(ost.StandingError):
            ost.split(probe + "--- STANDING BEGIN x ---\nstep 1 of 1: y\n")


class TestOfficeStanding(SittingCase):
    def test_a_block_is_filed_as_the_folders_page_and_committed_alone(self):
        self.text.write_text("the chat's words\n```\n" + standing(self.sit) + "```\n")
        proc = self.run_office("standing", self.plan, str(self.text), check=0)
        self.assertIn(f"filed {self.sit}'s standing on desk/{self.plan}, from file standing.txt: step 2 of 3:", proc.stderr)
        page = self.page.read_text()
        self.assertRegex(page, rf"^# Where the sitting stands\n\n- as of: \d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}}\n"
                               rf"- sitting: {self.sit}\n\n")
        self.assertTrue(page.endswith(standing(self.sit)), page)
        self.assertEqual(self.subjects(1), [f"office standing: {self.sit} in {self.plan}"])
        self.assertEqual(self.e.git(self.root, "show", "--name-only", "--format=", "HEAD").split(),
                         [f"desk/{self.plan}/standing.md"])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # Filed again, the page is replaced whole.
        self.file(standing(self.sit, step=3))
        self.assertEqual(self.page.read_text().count("STANDING BEGIN"), 1)
        self.assertIn("step 3 of 3: draft the words", self.page.read_text())

    def test_a_block_that_does_not_read_or_is_not_the_folders_is_refused_and_the_page_kept(self):
        self.file(standing(self.sit))
        before = self.page.read_bytes()
        for text, words in ((standing(self.sit).replace("- [>]", "- [x]"), "exactly one step is `- [>]`"),
                            (standing("2026-11-03-other-sitting-001"), "a session the folder does not record")):
            proc = self.file(text, check=1)
            self.assertIn(words, proc.stderr)
            self.assertIn(f"desk/{self.plan}/standing.md is as it was", proc.stderr)
            self.assertEqual(self.page.read_bytes(), before)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_from_stdin_and_piped_with_neither_it_names_the_two(self):
        proc = self.run_office("standing", self.plan, "-", input=standing(self.sit), check=0)
        self.assertIn("from stdin", proc.stderr)
        self.assertTrue(self.page.is_file())
        proc = self.run_office("standing", self.plan, check=1)
        self.assertIn("office standing reads the clipboard only on a terminal", proc.stderr)
        proc = self.run_office("standing", check=1)
        self.assertIn("name the sitting's folder: office standing FOLDER", proc.stderr)

    def test_an_open_session_holding_the_page_keeps_the_write_out(self):
        self.run_office("start", self.plan, "--in-office", "--goal", "Tidy it", "--write", f"desk/{self.plan}",
                        check=0)
        proc = self.file(standing(self.sit), check=1)
        self.assertIn("(the one-writer rule), so the standing is not filed beside it", proc.stderr)
        self.assertFalse(self.page.exists())


class TestOfficeStandingOnATerminal(SittingCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_with_neither_it_reads_the_clipboard(self):
        clip = self.e.tmp / "clipboard.txt"
        clip.write_text("```\n" + standing(self.sit) + "```\n")
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'paste_command = "cat {clip}"\n')
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "standing", self.number()], self.root,
                                   self.e.env, [])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"reading the standing from the clipboard (cat {clip})", seen)
        self.assertIn(f"filed {self.sit}'s standing on desk/{self.plan}, from the clipboard", seen)
        self.assertTrue(self.page.read_text().endswith(standing(self.sit)))


# --- 2. office probe files the standing that rides with it --------------------------------------

class TestProbeFilesTheStanding(SittingCase):
    def probe(self, text):
        block = self.e.tmp / "probe.sh"
        block.write_text(text)
        return self.run_office("probe", self.plan, str(block), "--project", "alpha", "--yes", check=0)

    def test_one_paste_carries_both_the_standing_filed_first_and_the_probe_run(self):
        # A step that names office-on must not read as a call of it.
        st = standing(self.sit, steps=("probe the office", "run office-on alpha git log", "draft the words"))
        proc = self.probe("```\n" + probe_block() + st + "```\n")
        self.assertIn(f"filed {self.sit}'s standing on desk/{self.plan}, from the probe's text", proc.stderr)
        self.assertLess(proc.stderr.index("filed "), proc.stderr.index("The probe block, as its purpose header says"))
        self.assertTrue(self.page.read_text().endswith(st))
        # The probe ran as without it: none of the standing's lines ran.
        self.assertIn("=== PROBE END fix-login ===", proc.stdout)
        self.assertNotIn("STANDING", proc.stdout + proc.stderr.replace("filed", ""))
        self.assertNotIn("command not found", proc.stderr)
        self.assertNotIn("office-on for", proc.stderr)
        self.assertEqual(self.subjects(2), [f"office probe: {self.sit} in {self.plan}",
                                            f"office standing: {self.sit} in {self.plan}"])

    def test_no_standing_changes_nothing_and_one_that_does_not_read_is_said(self):
        proc = self.probe(probe_block())
        self.assertNotIn("'s standing on desk/", proc.stderr)
        self.assertNotIn("the standing from", proc.stderr)
        self.assertFalse(self.page.exists())
        proc = self.probe(probe_block() + standing(self.sit).replace("- [>]", "- [x]"))
        self.assertIn("the standing from the probe's text was not filed", proc.stderr)
        self.assertIn("=== PROBE END fix-login ===", proc.stdout)
        self.assertFalse(self.page.exists())


# --- 3. the screens show it -----------------------------------------------------------------

class TestTheScreensShowIt(SittingCase):
    def test_the_walk_in_line_the_desk_and_none_as_before(self):
        walk = self.run_office(check=0).stdout
        line, = [l for l in walk.splitlines() if self.sit in l and "read-only" in l]
        self.assertNotIn("step ", line)
        self.file(standing(self.sit))
        walk = self.run_office(check=0).stdout
        line, = [l for l in walk.splitlines() if self.sit in l and "read-only" in l]
        self.assertRegex(line, rf"\(office land {self.sit} when the sitting is over\); step 2 of 3: {STEPS[1]}; "
                               rf"waiting on you: {WAITING} \(as of \d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}}\)$")
        # Once the sitting is over the folder is on the desk with no session
        # in flight, and office desk shows where it ended under its line.
        self.run_office("land", self.sit, check=0)
        desk = self.run_office("desk", check=0).stdout.splitlines()
        at = next(i for i, l in enumerate(desk) if self.plan in l and "next:" in l)
        self.assertTrue(desk[at + 1].startswith(f"    standing, {self.sit}'s: step 2 of 3: {STEPS[1]}"), desk)

    def test_the_home_screens_item_as_a_unit(self):
        names = types.SimpleNamespace(of=lambda sid: "folder 2, plan-it")
        s = {"sid": SIT, "label": ob.OFFICE_LABEL, "folders": ["desk/x"], "stale": None, "older": False,
             "standing": None}
        self.assertEqual(hs.sitting_item_words(s, names), "End the sitting folder 2, plan-it (the office), once it is over")
        s.update(older=True, standing="step 2 of 3: w; waiting on you: nothing (as of 2026-11-03 14:05)")
        self.assertEqual(hs.sitting_item_words(s, names),
                         "End the sitting folder 2, plan-it (the office), once it is over; step 2 of 3: w; waiting "
                         "on you: nothing (as of 2026-11-03 14:05); an older sitting on this folder, probably over")


class TestTheHomeScreenOnATerminal(SittingCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def screen(self):
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'downloads = ["{self.downloads}"]\n')
        code, seen = on_a_terminal(self, [str(self.e.office_bin)], self.root, self.e.env, [(b"Your key: ", "q")])
        self.assertEqual(code, 0, seen)
        return [" ".join(l.split()) for l in seen.splitlines()]

    def test_the_item_says_where_it_stands_and_a_second_key_files_a_new_one(self):
        lines = self.screen()
        self.assertEqual(len([l for l in lines if "End the sitting" in l]), 1)
        # Since 0.44.0 the key shows from the sitting's first turn, before
        # any standing is filed (tests/test_from_the_artifact.py, item 6).
        self.assertEqual(len([l for l in lines if "File where" in l]), 1)
        self.file(standing(self.sit))
        lines = self.screen()
        item, = [l for l in lines if "End the sitting" in l]
        self.assertIn(f"once it is over; step 2 of 3: {STEPS[1]}; waiting on you: {WAITING} (as of ", item)
        key, = [l for l in lines if "File where" in l]
        self.assertIn("stands now, from the sitting's last standing block on the clipboard", key)


# --- 4. the briefs, the doctrine and the catalog say it --------------------------------------

class TestTheBriefsSayIt(unittest.TestCase):
    def test_the_two_briefs_say_what_the_sitting_owes(self):
        for name in ("sitting-brief.md", "prep-brief.md"):
            text = " ".join((REPO / "templates" / name).read_text().split())
            self.assertIn("prints its standing block", text, name)
            self.assertIn("after the probe block when the turn ends in one", text, name)
            self.assertIn("`office standing FOLDER`", text, name)
            self.assertIn("exactly one `[>]`, the Nth", text, name)
        sitting = " ".join((REPO / "templates/sitting-brief.md").read_text().split())
        self.assertIn("one ENDS line naming this sitting, `--- ENDS SID ---`", sitting)
        # The example in each reads as the office files it.
        for name in ("sitting-brief.md", "prep-brief.md"):
            text = (REPO / "templates" / name).read_text()
            block = text[text.index("--- STANDING BEGIN"):text.index("--- STANDING END ---") + 20]
            ost.read_block(block)

    def test_the_doctrine_pins_it_past_the_banner_and_the_catalog_declares_it(self):
        text = (REPO / "doctrine/OFFICE.md").read_text()
        banner = text.index("> **PAST THE CORE.**")
        for words in ("--- STANDING BEGIN", "--- ENDS 2026-10-27-alpha-plan-sitting-001 ---", "| standing | script (0.43.0)"):
            self.assertGreater(text.index(words), banner, words)
        block = text[text.index("  --- STANDING BEGIN"):text.index("  --- STANDING END ---") + 22]
        ost.read_block(block)
        import tomllib
        v = tomllib.loads((REPO / "share/verbs.toml").read_text())["verbs"]["standing"]
        self.assertEqual((v["kind"], v["surface"], v["writes"]), ("script", "plumbing", ["desk/{folder}/standing.md"]))


# --- 5. land leaves the page ---------------------------------------------------------------

class TestLandLeavesTheStanding(SittingCase):
    def test_ending_the_sitting_leaves_the_page_as_the_record_of_where_it_ended(self):
        self.file(standing(self.sit))
        before = self.page.read_bytes()
        proc = self.run_office("land", self.sit, check=0)
        self.assertIn(f"Ended: the sitting {self.sit} is closed", proc.stdout)
        self.assertEqual(self.page.read_bytes(), before)
        # office close moves it with the folder.
        self.run_office("close", self.plan, check=0)
        self.assertEqual((self.root / "filing-cabinet" / self.plan / "standing.md").read_bytes(), before)


# --- 6. a prep's doctrine ------------------------------------------------------------------

class TestThePrepsDoctrine(LandCase):
    KEY = "2026-10-30 14:00 alpha review"

    def setUp(self):
        super().setUp()
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(re.sub(r'timezone = ".*"', 'timezone = "UTC"', manifest.read_text()))
        self.e.git(self.root, "commit", "-qam", "the office runs on UTC")

    def test_the_record_line_reads_and_renders_it_last(self):
        line = (f"- 2026-10-30 14:00 alpha review: held, {SIT}; arose: in-tray/a.md; doctrine: 0123456789ab "
                "[about: alpha]")
        (self.root / "calendar").mkdir(exist_ok=True)
        (self.root / om.RECORD).write_text(line + "\n")
        r, = om.read_record(self.root)
        self.assertEqual((r["doctrine"], r["arose"]), ("0123456789ab", ["in-tray/a.md"]))
        self.assertEqual(om.render_record(r), line)
        r["doctrine"] = None
        self.assertNotIn("doctrine", om.render_record(r))

    def test_start_stamps_it_and_the_walk_in_compares_it(self):
        self.run_office("meeting", "alpha review on 2026-10-30 at 14:00", check=0)
        sid = re.search(r"^Packed (\S+) for the meeting", self.run_office("start", "--prep", self.KEY, check=0).stdout,
                        re.M).group(1)
        record = (self.root / om.RECORD).read_text()
        self.assertIn(f"prep out, {sid}; doctrine: {install_sha()[:12]} [about: alpha]\n", record)
        self.assertEqual(om.prep_of(self.root, sid)["doctrine"], install_sha()[:12])
        walk = self.run_office(check=0).stdout
        self.assertNotIn("older doctrine", walk)
        (self.root / om.RECORD).write_text(record.replace(install_sha()[:12], "0123456789ab"))
        self.e.git(self.root, "commit", "-qam", "the install moved on")
        line, = [l for l in self.run_office(check=0).stdout.splitlines() if sid in l and "read-only" in l]
        self.assertIn(f"its prep (office land {sid} when the sitting is over); out under an older doctrine: OFFICE.md "
                      f"0123456789ab when it went out, {install_sha()[:12]} the install's now", line)


# --- 7. the pty harnesses kill a hung child ----------------------------------------------------

# A child that lets go of the terminal and never ends: what a question no
# step answers looks like to the harness once its read has finished.
HUNG = ["/bin/sh", "-c", 'exec >/dev/null 2>&1 </dev/null; echo $$ > "$HUNG_PID"; exec sleep 300']


class TestTheHarnessesKillAHungChild(unittest.TestCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def setUp(self):
        import tempfile
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="hung-"))
        self.env = dict(os.environ, HUNG_PID=str(self.dir / "pid"))

    def assertGone(self):
        pid = int((self.dir / "pid").read_text())
        with self.assertRaises(ProcessLookupError):
            os.kill(pid, 0)

    def test_on_a_terminal_fails_the_test_and_the_child_is_gone(self):
        with self.assertRaises(AssertionError) as cm:
            on_a_terminal(self, HUNG, str(self.dir), self.env, [])
        self.assertIn("still running after its last step", str(cm.exception))
        self.assertGone()

    def test_terminal_fails_and_the_child_is_gone(self):
        with self.assertRaises(AssertionError) as cm:
            terminal(self.env, str(self.dir), HUNG, [], limit=2)
        self.assertIn("still running after its last step", str(cm.exception))
        self.assertGone()


# --- 8. the probe's stderr masked ---------------------------------------------------------

class TestTheProbesStderrIsMasked(SittingCase):
    def test_a_token_on_stderr_comes_out_masked_and_the_count_says_which_stream(self):
        block = probe_block().replace('out="$(probe 2>&1)"',
                                      f'echo "fetching with {TOKEN} and https://pat:hunter22@git.example.org/x" >&2\n'
                                      'out="$(probe 2>&1)"')
        f = self.e.tmp / "probe.sh"
        f.write_text(block)
        proc = self.run_office("probe", self.plan, str(f), "--project", "alpha", "--yes", check=0)
        self.assertNotIn(TOKEN, proc.stderr)
        self.assertNotIn("hunter22", proc.stderr)
        self.assertIn("fetching with ghp_xxx and https://pat:xxx@git.example.org/x", proc.stderr)
        self.assertIn("; 1 credential in a URL and 1 GitHub token on stderr were masked (xxx stands for each)",
                      proc.stderr)
        # stderr is shown, never kept: the History counts stdout's lines.
        self.assertIn("[clipboard] probe output not copied", proc.stderr)

    def test_run_probe_keeps_its_shape_for_its_other_callers(self):
        import office_host as ohost
        got = ohost.run_probe(ohost.Place(str(self.e.tmp)), "echo out; echo err >&2\n", screen=open(os.devnull, "wb"))
        self.assertEqual((got[0], got[1], got[2]), (0, "out\n", False))
        self.assertEqual(len(got), 3)


# --- 9. office start ends the predecessor, and two sittings are said -------------------------------

class TestTheEndsLine(SittingCase):
    def bundle(self, ends, stem="2026-11-03-plan-next"):
        brief = f"# Brief\n\nThe next step.\n\n--- LANDS the office, folder {self.number()} ---\n{ends}\n"
        return bundle_file(self.downloads, stem, ["Plan the next step", "--slug", stem[11:], "--read-only"],
                           brief=brief)

    def history(self):
        return [l for l in (self.root / "desk" / self.plan / "folder.md").read_text().splitlines() if " ended: " in l]

    def test_the_reader_as_a_unit(self):
        text = (f"# Brief\n\n--- ENDS {SIT} ---\n```\n--- ENDS 2026-01-01-quoted-001 ---\n```\n"
                "--- ENDS plan-it ---\n--- ENDS 2026-11-03-second-001 ---\n")
        sid, problems = oh.brief_ends(text)
        self.assertEqual(sid, SIT)
        self.assertEqual(len(problems), 2)
        self.assertIn("not `--- ENDS SID ---`", problems[0])
        self.assertIn("a second ENDS line; the first is taken", problems[1])
        self.assertEqual(oh.brief_ends("# Brief\n"), (None, []))

    def test_with_the_flag_start_ends_the_sitting_its_brief_succeeds(self):
        proc = self.run_office("start", "--bundle", str(self.bundle(f"--- ENDS {self.sit} ---")), "--end-predecessor",
                               check=0)
        new = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertIn(f"Ended: the sitting {self.sit} is closed in this office", proc.stdout)
        # After the opener: a refusal of the end never costs the pack.
        self.assertLess(proc.stdout.index("--8<-- end session opener --8<--"), proc.stdout.index("Ended: "))
        self.assertFalse(self.fake.is_open(self.root, self.sit))
        self.assertTrue(self.fake.is_open(self.root, new))
        self.assertEqual(len(self.history()), 1)
        self.assertIn(f"ended: {self.sit}, a read-only sitting, closed by office start, succeeded by {new}",
                      self.history()[0])
        self.assertIn(f"office start: {self.sit} ended in {self.plan}", self.subjects(6))

    def test_piped_with_neither_it_is_said_and_keep_keeps_it(self):
        proc = self.run_office("start", "--bundle", str(self.bundle(f"--- ENDS {self.sit} ---")), check=0)
        self.assertIn(f"this brief succeeds the sitting {self.sit}", proc.stderr)
        self.assertIn(f"not ended, since piped input is never asked (--end-predecessor ends it); office land "
                      f"{self.sit} ends it", proc.stderr)
        self.assertTrue(self.fake.is_open(self.root, self.sit))
        proc = self.run_office("start", "--bundle", str(self.bundle(f"--- ENDS {self.sit} ---", "2026-11-03-b2")),
                               "--keep-predecessor", check=0)
        self.assertIn(f"--keep-predecessor: the sitting {self.sit}, which this brief succeeds, stays open", proc.stderr)
        self.assertTrue(self.fake.is_open(self.root, self.sit))
        self.assertEqual(self.history(), [])

    def test_a_sitting_not_open_and_a_brief_with_none_change_nothing(self):
        proc = self.run_office("start", "--bundle", str(self.bundle("--- ENDS 2026-01-01-long-gone-sitting-001 ---")),
                               "--end-predecessor", check=0)
        self.assertIn("the brief succeeds 2026-01-01-long-gone-sitting-001, which is not open where the office reads, "
                      "so nothing is ended", proc.stderr)
        self.assertIn("Packed ", proc.stdout)
        proc = self.run_office("start", "--bundle", str(self.bundle("", "2026-11-03-b3")), check=0)
        self.assertNotIn("succeed", proc.stderr)
        self.assertTrue(self.fake.is_open(self.root, self.sit))

    def test_two_sittings_on_one_folder_are_said_and_the_probe_offers_the_newest_first(self):
        proc = self.run_office("start", "--bundle", str(self.bundle(f"--- ENDS {self.sit} ---")), "--keep-predecessor",
                               check=0)
        new = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        walk = self.run_office(check=0).stdout.splitlines()
        old_line, = [l for l in walk if self.sit in l and "read-only" in l]
        new_line, = [l for l in walk if new in l and "read-only" in l]
        self.assertTrue(old_line.endswith(f"; {ob.OLDER_SITTING_WORDS}"), old_line)
        self.assertNotIn(ob.OLDER_SITTING_WORDS, new_line)
        f = self.e.tmp / "probe.sh"
        f.write_text(probe_block(slug="nothing-named"))
        proc = self.run_office("probe", self.plan, str(f), "--project", "office", "--yes", check=1)
        self.assertIn(f"({new}, {self.sit}), and the block's slug names none", proc.stderr)

    def test_the_readers_as_units(self):
        md = self.root / "desk" / self.plan / "folder.md"
        a, b = self.sit, "2026-11-04-plan-next-001"
        oh.record_session(md, b, "sitting")
        rel = f"desk/{self.plan}"
        self.assertEqual(ob.older_sittings(self.root, [(b, [rel]), (a, [rel])]), {a})
        self.assertEqual(ob.older_sittings(self.root, [(a, [rel])]), set())
        self.assertEqual(ob.older_sittings(self.root, [(a, ["desk/x"]), ("2026-11-05-y-001", ["desk/x"])]), {a})
        self.assertEqual(op.newest_first([a, b], [a, b]), [b, a])


class TestTheEndsLineOnATerminal(SittingCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_asked_once_default_yes(self):
        brief = f"# Brief\n\n--- LANDS the office, folder {self.number()} ---\n--- ENDS {self.sit} ---\n"
        b = bundle_file(self.downloads, "2026-11-03-plan-next", ["Plan the next step", "--slug", "plan-next",
                                                                 "--read-only"], brief=brief)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "--bundle", str(b), "--no-sort-first"],
                                   self.root, self.e.env,
                                   [(f"End the sitting {self.sit}, which this brief succeeds? (--end-predecessor) "
                                     "(y/n) [y]: ".encode(), "")])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"Ended: the sitting {self.sit} is closed", seen)
        self.assertFalse(self.fake.is_open(self.root, self.sit))


# --- 10 and 11. the tail, piped, with the review state --------------------------------------------

class TestTheTailWhenLandIsPiped(AudienceLandCase):
    def test_the_planners_block_is_printed_whole_with_the_tail_under_one_marked_line(self):
        sid, proc = self.land_one()
        out = proc.stdout
        mark = "The block for the planner, whole, with the office's lines:"
        self.assertEqual(out.count(mark), 1, out)
        after = out[out.index(mark):].splitlines()
        begin = next(i for i, l in enumerate(after) if l.startswith(f"=== RELAY BEGIN {sid} to planner"))
        end = next(i for i, l in enumerate(after) if l.startswith(f"=== RELAY END {sid} to planner"))
        self.assertLess(begin, end)
        self.assertEqual(after[end + 1], f"--- OFFICE land {sid} ---")
        self.assertIn("--- OFFICE END ---", after[end + 1:])
        # bale's own printing of the block is above it, as before.
        self.assertLess(out.index(f"=== RELAY END {sid} to planner"), out.index(mark))

    def test_a_project_with_no_audience_carries_its_folder_line(self):
        self.run_office("projects", "set", "alpha", "--no-audience", check=0)
        sid, proc = self.land_one()
        after = proc.stdout[proc.stdout.index("The block for the planner, whole, with the office's lines:"):]
        self.assertIn(f"--- OFFICE land {sid} ---\nfolder: {self.n}, fix-login (desk/{self.name}, open)\n"
                      "--- OFFICE END ---", after)


class TestReviewStateOnTheTail(AudienceLandCase):
    def setUp(self):
        super().setUp()
        self.gh = FakeGh(self.e.tmp, signed_in=("github.example.org",))

    def name_a_github_host(self):
        # Reading review state reaches no audience: the clone names a GitHub
        # host, and gh (the fake) answers for it; git never reaches it.
        self.e.git(self.proj, "remote", "set-url", "origin", REMOTE)
        self.e.env["GIT_SSH_COMMAND"] = "false"

    def delivered(self, branch="login-fix"):
        md = self.root / self.folder / "folder.md"
        text = md.read_text().rstrip("\n") + "\n- 2026-11-02 delivered: " + oh.delivered_text(
            branch, "origin", "alpha", ["2026-11-01-earlier-001"], "abcdef1", "1234567") + "\n"
        md.write_text(text)
        self.e.git(self.root, "commit", "-qam", "delivered")

    def test_the_lines_as_the_tail_says_them(self):
        self.name_a_github_host()
        environ = dict(self.e.env, **self.gh.env())
        self.assertEqual(orev.tail_lines(self.root, "alpha", self.folder, environ=environ), [])
        self.delivered()
        self.gh.add_pull(12, "login-fix", decision="APPROVED")
        self.gh.add_pull(14, "someone-elses")
        self.assertEqual(orev.tail_lines(self.root, "alpha", self.folder, environ=environ),
                         ["reviews: #12 approved (login-fix)"])
        # gh not there: no line.
        self.assertEqual(orev.tail_lines(self.root, "alpha", self.folder, environ=dict(self.e.env)), [])
        self.assertEqual(orev.tail_lines(self.root, "beta", self.folder, environ=environ), [])

    def test_land_puts_it_after_next(self):
        self.delivered()
        self.gh.add_pull(12, "login-fix", decision="CHANGES_REQUESTED")
        self.e.env.update(self.gh.env())
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        self.name_a_github_host()
        proc = self.run_office("land", sid, check=0)
        after = proc.stdout[proc.stdout.index("The block for the planner, whole"):].splitlines()
        tail = after[after.index(f"--- OFFICE land {sid} ---"):]
        nxt = next(i for i, l in enumerate(tail) if l.startswith("next: "))
        self.assertEqual(tail[nxt + 1], "reviews: #12 changes requested (login-fix)")
        self.assertIn("--- OFFICE END ---", tail[nxt + 2:])


if __name__ == "__main__":
    unittest.main()
