"""Tests for office-src 0.55.0, prep-and-tidy: a meeting's prep filed,
compared and probed; three said lines; and the clean-ups.

One class or more per item of the brief (2026-11-08-prep-and-tidy-003):

1. office standing --prep files a prep's standing as
   calendar/standing-SID.md, and the walk-in and the home screen show it;
2. the home screen's prep item and office status's doctrine lines compare
   a prep's doctrine stamp;
3. office probe --prep runs a prep's probe through the office, the
   calendar's record line standing for a folder's Sessions;
4 and 5. the probe block's calls checked at plan time: in
   tests/test_spanning_probe.py, TestTheCallsAreReadBeforeTheBlockRuns;
6. office drop reads the clipboard again after a no, on a terminal;
7. office slip's last line says the box and its count;
8. office desk and the map name the asks out, and the desk an ask's
   record left without its tray;
10. start's unreadable-bundle line names the bundle's file;
11. the fake bale answers a dossier only in the repo that packed it, and
    office start N --handoff says a record found in more than one place;
14. start's background lines are OFFICE_DEBUG lines, piped too.

Items 9 (README's branch_prefix sentence), 12 (the sweep for a hard-coded
day) and 13 (the spanning tests' move) change other modules' text; their
pins are tests/test_land.py's TestTheWaveOneRecord.test_where_the_release_is_said and the moved
classes themselves.

The worlds are the suite's own: tests/test_land.py's LandCase,
tests/test_probe.py's ProbeCase and blocks, tests/test_standing.py's
standing blocks, tests/test_ask.py's AskCase. The meetings, sittings and
asks are invented. The terminal classes run in the serial lane. Run with
the rest of the suite:

    tests/run.sh test_prep_and_tidy
"""

import os
import pathlib
import re
import shutil
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import Env  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import LandCase, response_tarball  # noqa: E402
from test_probe import probe_block  # noqa: E402
from test_standing import standing  # noqa: E402
from test_ask import AskCase  # noqa: E402
from test_planner_from_words import install_sha  # noqa: E402

import office_bale as ob  # noqa: E402
import office_home as hs  # noqa: E402
import office_meeting as om  # noqa: E402
import office_probe as op  # noqa: E402
import office_standing as ost  # noqa: E402

KEY = "2026-10-30 14:00 alpha review"
STEPS = ("brief him on what landed", "keep the arising block")


class PrepCase(LandCase):
    """LandCase's office on UTC, with a meeting on alpha and its prep out
    (office start --prep): self.prep is the prep's id."""

    def setUp(self):
        super().setUp()
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(re.sub(r'timezone = ".*"', 'timezone = "UTC"', manifest.read_text()))
        self.e.git(self.root, "commit", "-qam", "the office runs on UTC")
        self.run_office("meeting", "alpha review on 2026-10-30 at 14:00", check=0)
        out = self.run_office("start", "--prep", KEY, check=0).stdout
        self.prep = re.search(r"^Packed (\S+) for the meeting", out, re.M).group(1)
        self.page = self.root / "calendar" / f"standing-{self.prep}.md"
        self.text = self.e.tmp / "standing.txt"

    def block(self, sid=None, step=1):
        return standing(sid or self.prep, step=step, steps=STEPS, waiting="nothing")

    def file(self, text, *more, check=0):
        self.text.write_text(text)
        return self.run_office("standing", "--prep", *more, str(self.text), check=check)


# --- 1. a prep's standing, filed in the calendar ------------------------------------------------

class TestAPrepsStanding(PrepCase):
    def test_it_is_filed_as_the_calendars_page_and_committed_alone(self):
        proc = self.file(self.block())
        self.assertIn(f"filed {self.prep}'s standing as calendar/standing-{self.prep}.md (the prep for alpha review), "
                      f"from file standing.txt: step 1 of 2: {STEPS[0]}; waiting on you: nothing (as of ", proc.stderr)
        text = self.page.read_text()
        self.assertTrue(text.startswith(f"{ost.HEADING}\n\n- as of: "), text)
        self.assertIn(f"\n- sitting: {self.prep}\n\n--- STANDING BEGIN {self.prep} ---\n", text)
        self.assertTrue(text.endswith(self.block()), text)
        self.assertEqual(self.subjects(1), [f"office standing: {self.prep}, the prep for alpha review"])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # The block's own id names it; --prep SID names it too, and the
        # page is replaced whole.
        self.file(self.block(step=2), self.prep)
        self.assertTrue(self.page.read_text().endswith(self.block(step=2)))
        # Nothing was filed on a folder: no folder records a prep.
        self.assertEqual(list((self.root / "desk").glob("*/standing.md")), [])

    def test_a_block_the_calendar_does_not_record_as_a_prep_is_refused_by_name(self):
        other = "2026-10-29-plan-it-sitting-001"
        proc = self.file(self.block(other), check=1)
        self.assertIn(f"the calendar records no meeting's prep {other} (calendar/record.md)", proc.stderr)
        proc = self.file(self.block(other), self.prep, check=1)
        self.assertIn(f"the block is {other}'s, a session the calendar's record of the prep for alpha review does "
                      f"not record (it records: {self.prep})", proc.stderr)
        proc = self.file(self.block().replace("- [>]", "- [x]"), check=1)
        self.assertIn("exactly one step is `- [>]`", proc.stderr)
        self.assertFalse(self.page.exists())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_piped_from_stdin_and_never_the_clipboard(self):
        proc = self.run_office("standing", "--prep", "-", input=self.block(), check=0)
        self.assertIn("from stdin:", proc.stderr)
        self.assertTrue(self.page.is_file())
        proc = self.run_office("standing", "--prep", check=1)
        self.assertIn("give the block as a file (office standing --prep FILE) or on stdin (office standing --prep -)",
                      proc.stderr)

    def test_the_walk_in_line_says_where_the_prep_stands(self):
        line, = [l for l in self.run_office(check=0).stdout.splitlines() if self.prep in l and "read-only" in l]
        self.assertNotIn("step ", line)
        self.file(self.block())
        line, = [l for l in self.run_office(check=0).stdout.splitlines() if self.prep in l and "read-only" in l]
        self.assertRegex(line, rf"its prep \(office land {self.prep} when the sitting is over\); step 1 of 2: "
                               rf"{STEPS[0]}; waiting on you: nothing \(as of \d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}}\)$")

    def test_land_ending_the_prep_leaves_the_page(self):
        self.file(self.block())
        before = self.page.read_bytes()
        self.run_office("land", self.prep, "--arising", "none", check=None)
        self.assertEqual(om.prep_of(self.root, self.prep)["state"], "held")
        self.assertEqual(self.page.read_bytes(), before)

    def test_the_units(self):
        self.assertEqual(ost.prep_rel(self.prep), f"calendar/standing-{self.prep}.md")
        with self.assertRaises(ost.oh.HelperError):
            ost.prep_rel("not-a-sid")
        with self.e.this_process():
            self.assertIsNone(ost.prep_standing(self.root, self.prep))
            self.assertIsNone(ob.prep_standing_words(self.root, self.prep))
            block, rec, rel = ost.write_prep(self.root, None, self.block(), "2026-10-30", "13:05")
            self.assertEqual((block["sid"], rec["title"], rel), (self.prep, "alpha review", ost.prep_rel(self.prep)))
            self.assertEqual(ob.prep_standing_words(self.root, self.prep),
                             f"step 1 of 2: {STEPS[0]}; waiting on you: nothing (as of 2026-10-30 13:05)")
            self.assertEqual(ost.place_of(self.root, self.block()), ("prep", self.prep))
            with self.assertRaises(ost.StandingError) as cm:
                ost.place_of(self.root, self.block("2026-10-29-plan-it-sitting-001"))
            self.assertIn("and the calendar records no meeting's prep 2026-10-29-plan-it-sitting-001",
                          str(cm.exception))


# --- 1 and 2. the home screen's prep item -------------------------------------------------------

class TestThePrepItemAsAUnit(unittest.TestCase):
    def test_it_says_its_doctrine_and_where_it_stands_as_a_sittings_item_does(self):
        m = {"title": "alpha review", "sid": "2026-10-29-alpha-review-prep-001"}
        bare = "End the prep for alpha review once the meeting is over: land records it held and files what arose"
        self.assertEqual(hs.prep_item_words(m), bare)
        m.update(stale="out under an older doctrine: OFFICE.md 0123456789ab when it went out, abcdefabcdef the "
                       "install's now",
                 standing="step 1 of 2: brief him; waiting on you: nothing (as of 2026-10-30 13:05)")
        self.assertEqual(hs.prep_item_words(m),
                         f"{bare}; it is out under an older doctrine: OFFICE.md 0123456789ab when it went out, "
                         "abcdefabcdef the install's now; step 1 of 2: brief him; waiting on you: nothing (as of "
                         "2026-10-30 13:05)")


class TestThePrepItemOnATerminal(PrepCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def screen(self):
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'downloads = ["{self.downloads}"]\n')
        code, seen = on_a_terminal(self, [str(self.e.office_bin)], self.root, self.e.env, [(b"Your key: ", "q")])
        self.assertEqual(code, 0, seen)
        return [" ".join(l.split()) for l in seen.splitlines()]

    def test_the_item_says_where_it_stands_its_doctrine_and_a_second_key_files_a_new_one(self):
        lines = self.screen()
        item, = [l for l in lines if "End the prep for alpha review" in l]
        self.assertNotIn("step ", item)
        self.assertNotIn("older doctrine", item)
        key, = [l for l in lines if "File where the prep for alpha review stands now" in l]
        self.assertIn("from the sitting's last standing block on the clipboard", key)
        self.file(self.block())
        record = (self.root / om.RECORD).read_text()
        (self.root / om.RECORD).write_text(record.replace(install_sha()[:12], "0123456789ab"))
        self.e.git(self.root, "commit", "-qam", "the install moved on")
        item, = [l for l in self.screen() if "End the prep for alpha review" in l]
        self.assertIn("files what arose; it is out under an older doctrine: OFFICE.md 0123456789ab when it went out, "
                      f"{install_sha()[:12]} the install's now; step 1 of 2: {STEPS[0]}; waiting on you: nothing (as "
                      "of ", item)


class TestThePrepsSecondKey(PrepCase):
    def test_the_second_key_runs_office_standing_prep_with_the_preps_id(self):
        with self.e.this_process():
            groups = {"moves": (0, "", []), "drops": [], "ready": [], "undelivered": [], "merges": []}
            names = types.SimpleNamespace(of=lambda sid: sid, folders={})
            meetings = [{"state": "prep out", "sid": self.prep, "title": "alpha review", "key": KEY}]
            items = hs.home_items("current", True, [], groups, [], 0, None, [], names, None, None, (), meetings)
        argvs = [i["argv"] for i in items]
        self.assertIn(["land", self.prep], argvs)
        self.assertIn(["standing", "--prep", self.prep], argvs)
        self.assertEqual(argvs.index(["standing", "--prep", self.prep]), argvs.index(["land", self.prep]) + 1)


class TestStatusComparesAPrepsDoctrine(PrepCase):
    def doctrine_lines(self):
        out = self.run_office("status", check=None).stdout.splitlines()
        at = next(i for i, l in enumerate(out) if l.startswith("doctrine:"))
        lines = [out[at]]
        for l in out[at + 1:]:
            if not l.startswith("  "):
                break
            lines.append(l)
        return lines

    def test_a_prep_out_under_another_doctrine_is_one_line_under_it(self):
        self.assertEqual(len(self.doctrine_lines()), 1, self.doctrine_lines())
        record = (self.root / om.RECORD).read_text()
        (self.root / om.RECORD).write_text(record.replace(install_sha()[:12], "0123456789ab"))
        self.e.git(self.root, "commit", "-qam", "the install moved on")
        head, line = self.doctrine_lines()
        self.assertEqual(line, f"  {self.prep}: the prep for alpha review (2026-10-30 14:00) out under an older "
                               f"doctrine: OFFICE.md 0123456789ab when it went out, {install_sha()[:12]} the "
                               "install's now")
        # Held, it is no longer out, and nothing is said of it.
        self.run_office("land", self.prep, "--arising", "none", check=None)
        self.assertEqual(len(self.doctrine_lines()), 1)


# --- 3. a prep's probe, through the office ---------------------------------------------------------

class TestAPrepsProbe(PrepCase):
    def setUp(self):
        super().setUp()
        self.probe_file = self.e.tmp / "probe.sh"
        self.probe_file.write_text(probe_block(slug="alpha-review"))

    def test_it_runs_where_its_meetings_one_concern_lives_under_the_preps_id(self):
        proc = self.run_office("probe", "--prep", str(self.probe_file), "--yes", check=0)
        self.assertIn(f"the calendar records one prep out, {self.prep}, the prep for alpha review (about: alpha): the "
                      "probe is its", proc.stderr)
        self.assertIn("from the calendar: the meeting concerns alpha, so the probe runs where alpha lives", proc.stderr)
        self.assertIn(f"for {self.prep} (the prep for alpha review, the read-only sitting open in the office)",
                      proc.stderr)
        self.assertIn(f"cwd: {os.path.realpath(self.proj)}", proc.stdout)
        self.assertIn("=== PROBE END alpha-review ===", proc.stdout)
        self.assertIn(f"no folder records the prep for alpha review, so no History line is written for this probe "
                      f"({self.prep}, 4 lines)", proc.stderr)
        self.assertFalse([s for s in self.subjects(3) if s.startswith("office probe:")])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # --project office runs it in the office root, under the same id.
        proc = self.run_office("probe", "--prep", self.prep, str(self.probe_file), "--project", "office", "--yes",
                               check=0)
        self.assertIn(f"cwd: {os.path.realpath(self.root)}", proc.stdout)
        self.assertIn(f"for {self.prep} (the prep for alpha review)", proc.stderr)

    def test_its_run_line_names_it_and_a_standing_beside_it_is_filed_in_the_calendar(self):
        header = ["# PROBE alpha-review: what the machine says, in one line.", "# Why: the prep needs it.",
                  f"# office: probe --prep {self.prep} --project office",
                  "# Read-only: writes nothing anywhere; stdout is the only output."]
        text = probe_block(slug="alpha-review", header=header) + self.block()
        proc = self.run_office("probe", "-", "--yes", input=text, check=0)
        self.assertIn(f"from the block: probe --prep {self.prep} --project office", proc.stderr)
        self.assertIn(f"cwd: {os.path.realpath(self.root)}", proc.stdout)
        self.assertIn(f"filed {self.prep}'s standing as calendar/standing-{self.prep}.md", proc.stderr)
        self.assertTrue(self.page.read_text().endswith(self.block()))
        self.assertNotIn("STANDING", proc.stdout)
        # A run line naming a prep that is not one is said.
        with self.assertRaises(op.ProbeError):
            op.run_line(["# office: probe --prep not-a-sid"])
        self.assertEqual(op.run_line([f"# office: probe --prep {self.prep}"])[1],
                         {"folder": None, "project": None, "sid": self.prep, "prep": self.prep})

    def test_a_standing_alone_with_no_folder_is_filed_as_the_preps(self):
        proc = self.run_office("probe", "-", "--yes", input=self.block(), check=0)
        self.assertIn(f"holds a standing and no probe: filed as calendar/standing-{self.prep}.md; nothing to run",
                      proc.stderr)
        self.assertTrue(self.page.is_file())

    def test_a_held_prep_and_none_out_are_refused_before_anything_runs(self):
        self.run_office("land", self.prep, "--arising", "none", check=None)
        proc = self.run_office("probe", "--prep", str(self.probe_file), "--yes", check=1)
        self.assertIn("no meeting's prep is out (calendar/record.md records none)", proc.stderr)
        proc = self.run_office("probe", "--prep", self.prep, str(self.probe_file), "--yes", check=1)
        self.assertIn(f"--prep {self.prep}: the calendar records no meeting's prep out by that id", proc.stderr)
        self.assertNotIn("PROBE BEGIN", proc.stdout)
        with self.e.this_process():
            with self.assertRaises(op.ProbeError) as cm:
                op.recorder(self.root, prep=self.prep)
            self.assertIn("is recorded held, so its prep is over", str(cm.exception))
            with self.assertRaises(op.ProbeError):
                op.recorder(self.root, prep="2026-10-29-plan-it-sitting-001")

    def test_where_a_prep_runs_as_units(self):
        with self.e.this_process():
            self.assertEqual(op.prep_where(self.root, self.prep), ("alpha", "alpha"))
            self.assertEqual(op.preps_out(self.root), [(self.prep, "alpha review", ["alpha"])])
            who = op.recorder(self.root, prep=self.prep)
            self.assertEqual((who["rel"], who["name"], who["recorded"]),
                             (om.RECORD, "the prep for alpha review", [self.prep]))
            record = (self.root / om.RECORD).read_text()
            (self.root / om.RECORD).write_text(record.replace("[about: alpha]", "[about: alpha, the office]"))
            self.assertEqual(op.prep_where(self.root, self.prep), ("", "alpha, the office"))
            (self.root / om.RECORD).write_text(record.replace(" [about: alpha]", ""))
            self.assertEqual(op.prep_where(self.root, self.prep), ("office", "the office"))

    def test_a_meeting_on_several_concerns_names_project_piped(self):
        record = (self.root / om.RECORD).read_text()
        (self.root / om.RECORD).write_text(record.replace("[about: alpha]", "[about: alpha, the office]"))
        self.e.git(self.root, "commit", "-qam", "the meeting is on the office too")
        proc = self.run_office("probe", "--prep", str(self.probe_file), "--yes", check=1)
        self.assertIn("say where the probe runs: --project NAME (alpha), or --project office for the office itself; "
                      "the meeting concerns several (alpha, the office)", proc.stderr)


# --- 6. office drop reads the clipboard again after a no ------------------------------------------

class DropClipboardCase(unittest.TestCase):
    """An office whose clipboard holds an office command line."""

    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.clip = self.e.tmp / "clipboard.txt"
        self.clip.write_text("office drop --project alpha\n")
        machine = self.e.home / ".config" / "office-src" / "machine.toml"
        machine.parent.mkdir(parents=True, exist_ok=True)
        machine.write_text(f'paste_command = "cat {self.clip}"\n')

    def pages(self):
        tray = self.root / "in-tray"
        return sorted(p for p in tray.glob("*.md") if p.name != "README.md") if tray.is_dir() else []


class TestDropReadsTheClipboardAgain(DropClipboardCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_r_reads_it_again_once_the_message_is_copied(self):
        # The clipboard holds the command at the first read and the message
        # after it, as when he copies the message once he is asked.
        counter, message = self.e.tmp / "reads", self.e.tmp / "message.txt"
        message.write_text("The login page errors on narrow screens.\n")
        script = self.e.tmp / "paste.sh"
        script.write_text(f'if [ -e "{counter}" ]; then cat "{message}"; else : > "{counter}"; cat "{self.clip}"; fi\n')
        machine = self.e.home / ".config" / "office-src" / "machine.toml"
        machine.write_text(f'paste_command = "sh {script}"\n')
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "drop"], self.root, self.e.env, [
            (b"Drop it anyway? (--anyway) (y/n) [n]:", ""),
            (b"then r reads the clipboard again; a plain return ends here (office drop) [return skips]:", "r"),
        ])
        self.assertEqual(code, 0, seen)
        flat = " ".join(seen.split())
        self.assertIn("nothing dropped: the clipboard held an office command line", flat)
        self.assertIn("took 1 line(s) from the clipboard: The login page errors on narrow screens.", flat)
        (page,) = self.pages()
        self.assertTrue(page.read_text().endswith("## Text\n\nThe login page errors on narrow screens.\n"))
        self.assertIn("- via: clipboard\n", page.read_text())

    def test_a_plain_return_ends_with_nothing_dropped(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "drop"], self.root, self.e.env, [
            (b"Drop it anyway? (--anyway) (y/n) [n]:", ""),
            (b"a plain return ends here (office drop) [return skips]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertEqual(self.pages(), [])



class TestDropPiped(DropClipboardCase):
    def test_piped_it_never_asks(self):
        proc = self.e.run("drop", cwd=self.root, input="office drop --project alpha\n", check=0)
        self.assertNotIn("reads the clipboard again", proc.stderr)
        self.assertEqual(len(self.pages()), 1)


# --- 7. office slip says the box ------------------------------------------------------------------

class TestSlipSaysTheBox(unittest.TestCase):
    def test_its_last_line_names_the_box_and_how_many_slips_it_holds(self):
        e = Env(self)
        root = e.init()
        before = len(list((root / "suggestion-box").glob("*.md")))
        proc = e.run("slip", "the desk does not say why a folder waits", cwd=root, check=0)
        self.assertEqual(proc.stderr.splitlines()[-1],
                         f"[office] the suggestion box, {root}/suggestion-box, holds {before + 1} slip(s)")
        self.assertTrue((root / proc.stdout.strip()).is_file())
        proc = e.run("slip", "--about", "bale", cwd=root, input="pack needs too many flags\n", check=0)
        self.assertEqual(proc.stderr.splitlines()[-1],
                         f"[office] the suggestion box, {root}/suggestion-box, holds {before + 2} slip(s)")


# --- 8. the asks on the desk and the map ----------------------------------------------------------

class TestTheAsksOnTheDeskAndTheMap(AskCase):
    def test_the_desk_and_the_map_name_the_ask_out(self):
        self.assertNotIn("Asks out", self.run_office("desk", check=0).stdout)
        self.assertNotIn("Asks out", self.run_office("map", check=0).stdout)
        name, _ = self.sent()
        desk = self.run_office("desk", check=0).stdout.splitlines()
        at = desk.index("Asks out (next: office ask --learned; a quick question each, answered in a chat):")
        self.assertRegex(desk[at + 1], rf"^  {re.escape(name)} \(alpha\), asked \d{{4}}-\d{{2}}-\d{{2}} \d{{2}}:\d{{2}}: "
                                       rf"office ask --learned FILE files what it learned; office tray "
                                       rf"{re.escape(name)} opens its tray again$")
        page = self.run_office("map", check=0).stdout.splitlines()
        at = page.index("Asks out (outside any folder; the walk-in's Next line names the oldest):")
        self.assertRegex(page[at + 1], rf"^  office ask --learned +files {re.escape(name)}'s LEARNED block \(alpha, "
                                       r"asked \d{4}-\d{2}-\d{2} \d{2}:\d{2}\)$")
        self.assertRegex(page[at + 2], rf"^  office tray {re.escape(name)} +opens its tray again and prints its opener$")
        self.assertEqual(page[-1], "office map N shows one folder's whole record and the lines that change it.")
        self.assertIn("Asks out", self.run_office("map", "alpha", check=0).stdout)

    def test_the_desk_names_a_record_whose_tray_is_gone_with_the_line_that_removes_it(self):
        name, _ = self.sent()
        shutil.rmtree(self.tray_root / name)
        desk = self.run_office("desk", check=0).stdout.splitlines()
        self.assertNotIn("Asks out", "\n".join(desk))
        at = desk.index("Asks whose tray is gone:")
        line = desk[at + 1]
        self.assertTrue(line.startswith(f"  {name}'s tray is gone from {self.tray_root}"), line)
        self.assertTrue(line.endswith(" removes it") and "; rm -- " in line, line)
        self.assertIn(str(self.tray_root / f"{name}.ask.json"), line)

    def test_the_map_s_rows_as_a_unit(self):
        import office_map as omap
        a = {"name": "ask-2026-01-02-why", "project": "alpha", "day": "2026-01-02", "time": "09:00"}
        b = {"name": "ask-2026-01-03-how", "project": None, "day": "2026-01-03", "time": "10:00"}
        self.assertEqual(omap.ask_lines([]), [])
        lines = omap.ask_lines([a, b])
        self.assertEqual(lines[1], "Asks out (outside any folder; the walk-in's Next line names the oldest):")
        width = len("office tray ask-2026-01-03-how")
        self.assertEqual(lines[2], f"  {'office ask --learned'.ljust(width)}  files ask-2026-01-02-why's LEARNED block "
                                   "(alpha, asked 2026-01-02 09:00)")
        self.assertEqual(lines[5], "  office tray ask-2026-01-03-how  opens its tray again and prints its opener")
        self.assertEqual(len(omap.ask_lines([a, b], project="alpha")), 4)
        self.assertEqual(omap.ask_lines([b], project="alpha"), [])


# --- 10. the bundle's own file, read where it is -----------------------------------------------------

class TestTheBundlePlumbingIsGone(unittest.TestCase):
    def test_start_takes_no_bundle_found_and_bin_office_keeps_none(self):
        import inspect
        self.assertNotIn("bundle_found", inspect.signature(ob.start).parameters)
        here = pathlib.Path(__file__).resolve().parent.parent
        script = (here / "bin" / "office").read_text()
        for gone in ("START_BUNDLE_FOUND", "--bundle-found", "bundle_here", "START_SCREEN"):
            self.assertNotIn(gone, script)
        self.assertNotIn('"--bundle-found"', (here / "lib" / "office_bale.py").read_text())


class TestNoModuleDefinesANameTwice(unittest.TestCase):
    """A second top-level def of a name a module already has replaces the
    first for every caller, silently: 0.55.0's handoff helper was first
    named place_words, which office_bale already defined for the bundle's
    places, and every bundle line said `a's tree` for `alpha's tree` until
    the suite caught it. One rule, over every module in lib/."""

    def test_each_top_level_function_and_class_is_defined_once(self):
        import ast
        import collections
        here = pathlib.Path(__file__).resolve().parent.parent
        for path in sorted((here / "lib").glob("*.py")):
            body = ast.parse(path.read_text(encoding="utf-8")).body
            names = collections.Counter(n.name for n in body
                                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
            self.assertEqual([n for n, k in names.items() if k > 1], [], path.name)


# --- 11. a dossier is its repo's, and a record in two places is said --------------------------------

class TestADossierIsItsReposOwn(LandCase):
    def setUp(self):
        super().setUp()
        self.downloads_known()

    def test_an_office_session_on_an_alpha_folder_is_still_open_in_the_office_not_in_alpha(self):
        sid = self.start("fix-login", "--in-office", "--goal", "Plan the login fix")
        response_tarball(self.downloads, sid, kind="bailout")
        proc = self.run_office("start", "1", "--handoff", check=1)
        # The folder's lane is alpha, so alpha is read first; only the office
        # holds the record, as a real bale's per-repo records say.
        self.assertIn(f"{sid} is still open in the office:", proc.stderr)
        self.assertNotIn(f"{sid} is still open in alpha", proc.stderr)
        self.assertNotIn("more than one place", proc.stderr)

    def test_a_project_session_is_alpha_s_and_not_the_office_s(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        response_tarball(self.downloads, sid, kind="bailout")
        proc = self.run_office("start", "1", "--handoff", check=1)
        self.assertIn(f"{sid} is still open in alpha:", proc.stderr)
        with self.e.this_process():
            rd = ob.Reader()
            self.assertIsNotNone(rd.dossier(self.proj, sid))
            self.assertIsNone(rd.dossier(self.root, sid))

    def test_a_record_in_two_places_is_said_and_the_first_is_read(self):
        record = {"session_id": "S"}

        class Reader:
            def __init__(self, holds):
                self.holds, self.asked = holds, []

            def dossier(self, where, sid):
                self.asked.append(where)
                return record if where in self.holds else None

        places = [("alpha", {"name": "alpha"}, "A"), ("far", {"name": "far", "host": "h"}, "F"),
                  ("beta", {"name": "beta"}, "B"), (ob.OFFICE_LABEL, None, "O")]
        view = types.SimpleNamespace()
        old = ob.session_view
        ob.session_view = lambda rd, d: view
        try:
            rd = Reader({"A", "F", "O"})
            found, also = ob.record_places(rd, places, "S")
            self.assertEqual(found, ("alpha", {"name": "alpha"}, "A", view))
            self.assertEqual([p[0] for p in also], [ob.OFFICE_LABEL])
            # Past the first, a host is never reached.
            self.assertEqual(rd.asked, ["A", "B", "O"])
            self.assertEqual([ob.record_place_words(p) for p in [found, *also]], ["alpha", "the office"])
            rd = Reader({"F"})
            found, also = ob.record_places(rd, places, "S")
            self.assertEqual((found[0], also), ("far", []))
            self.assertEqual(rd.asked, ["A", "F", "B", "O"])
            self.assertEqual(ob.record_places(Reader(set()), places, "S"), (None, []))
        finally:
            ob.session_view = old


# --- 14. start's background lines are OFFICE_DEBUG lines ---------------------------------------------

class TestStartsBackgroundLinesPiped(LandCase):
    def test_piped_they_are_said_under_office_debug_only(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", check=0)
        self.assertRegex(proc.stdout, r"^Packed \S+ for ", proc.stderr)
        for line in ("[office] out tray: ", "[office] recorded ", "[office] surveyed this machine again",
                     "[office] committed floor-plan/survey.md"):
            self.assertNotIn(line, proc.stderr)

    def test_under_office_debug_they_are_debug_lines(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", check=0,
                               extra={"OFFICE_DEBUG": "1"})
        self.assertIn("[office] debug: out tray: request-", proc.stderr)
        self.assertIn("[office] debug: recorded ", proc.stderr)


if __name__ == "__main__":
    unittest.main()
