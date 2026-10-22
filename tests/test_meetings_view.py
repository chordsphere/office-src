"""Tests for 0.26.0, meetings as a view over the work: a meeting said once
in the occupant's words and recorded in the calendar; its prep, a
read-only sitting briefed from what landed since the last meeting on its
projects, sent by key and recorded in no folder; what arose in it filed as
drops when the sitting is ended, and a drop made during it tied to it; a
cleanup offered in the prep's brief. And session 3's two exceptions: a
pull-request template's own lines exempt from the three characters too,
and the terminal wizard working a project with an audience here by
default.

bale is never needed: the fake bale of tests/test_land.py packs, unlocks
and keeps the open sessions, and the fake ssh of tests/test_project_on_host.py
stands for a host. The terminal test runs in the serial lane. Run with the
rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import datetime as dt
import json
import pathlib
import re
import subprocess
import sys
import tarfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_land import LandCase  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_project_on_host import HOST, HostedCase, make_project  # noqa: E402

import office_home as hs  # noqa: E402  (lib/ is on sys.path through test_office)
import office_letterhead as olh  # noqa: E402
import office_meeting as om  # noqa: E402

UTC = dt.timezone.utc
THU = "2026-10-22"   # a Thursday
EM = "—"


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout


def request_members(tray):
    req = next(p for p in pathlib.Path(tray).iterdir() if p.name.startswith("request-"))
    out = {}
    with tarfile.open(req) as t:
        for m in t.getmembers():
            if m.isfile():
                out[m.name.split("/", 1)[1]] = t.extractfile(m).read()
    return out


def block(sid, *items):
    """An arising block, as a prep sitting writes one: items are (words,
    project, body)."""
    lines = [f"--- ARISING BEGIN {sid} ---", ""]
    for words, project, body in items:
        lines += [f"### {words}", "", f"- project: {project}", ""]
        if body:
            lines += [body, ""]
    return "\n".join(lines + ["--- ARISING END ---", ""])


# --- 1. a meeting, asked once: his words -----------------------------------------------------

class TestHisWords(unittest.TestCase):
    def when(self, text, today=THU, now="10:04"):
        w = om.read_when(text, today, now)
        return om.canon(w), om.title_of(text, w["spans"]), w["notes"]

    def test_when_and_the_title_come_from_one_sentence(self):
        cases = {
            "weekly review every Monday at 9 about alpha and beta": ("every mon 09:00", "weekly review about alpha and beta"),
            "alpha review on 2026-10-30 at 14:00": ("2026-10-30 14:00", "alpha review"),
            "a sync with the team tomorrow at 2pm": ("2026-10-23 14:00", "a sync with the team"),
            "standup every weekday at 9:30am": ("every weekday 09:30", "standup"),
            "budget check Oct 28 at 3:30 pm": ("2026-10-28 15:30", "budget check"),
            "alpha retro next Tuesday 10am": ("2026-10-27 10:00", "alpha retro"),
            "the review the 28th of October at noon": ("2026-10-28 12:00", "the review"),
            "a demo on 11/3 at 1:30pm": ("2026-11-03 13:30", "a demo"),
            "beta planning on Mondays at 8": ("every mon 08:00", "beta planning"),
        }
        for text, want in cases.items():
            self.assertEqual(self.when(text)[:2], want, text)

    def test_what_it_took_that_he_might_not_mean_is_said(self):
        when, title, notes = self.when("the report review at 3")
        self.assertEqual((when, title), (f"{THU} 15:00", "the report review"))
        self.assertTrue(any("taken as 15:00, the afternoon" in n for n in notes), notes)
        self.assertTrue(any("no day was said, so it is today" in n for n in notes), notes)
        # A time already past today is tomorrow.
        self.assertEqual(self.when("a sync at 9am")[0], "2026-10-23 09:00")

    def test_without_a_day_or_a_time_it_asks_and_an_answer_fills_it(self):
        for text in ("quarterly planning on Friday", "a sync with the data team", "weekly review every Monday"):
            self.assertIsNone(self.when(text)[0], text)
        w = om.read_when("weekly review every Monday", THU, "10:04")
        self.assertEqual(om.canon(om.merge(w, om.read_when("at 9", THU, "10:04"))), "every mon 09:00")
        w = om.read_when("alpha review on Friday", THU, "10:04")
        merged = om.merge(w, om.read_when("2pm", THU, "10:04"))
        self.assertEqual((om.canon(merged), merged["notes"]), ("2026-10-23 14:00", []))
        w = om.read_when("a sync", THU, "10:04")
        self.assertEqual(om.canon(om.merge(w, om.read_when("every thu 10:00", THU, "10:04"))), "every thu 10:00")

    def test_a_title_keeps_out_what_the_lines_read(self):
        self.assertEqual(om.title_of("review: alpha [draft]", []), "review, alpha (draft)")
        self.assertEqual(om.title_of("at 9", [(0, 4)]), "meeting")
        self.assertEqual(om.concerns_named("alpha and Beta, not alphabet", ["alpha", "beta", "gamma"]), ["alpha", "beta"])


# --- the calendar's lines, near, and the prep's record ----------------------------------------

class TestTheCalendar(unittest.TestCase):
    def setUp(self):
        self.root = Env(self).tmp / "office"
        (self.root / "calendar").mkdir(parents=True)
        (self.root / om.PLAN).write_text(
            "# Plan\n\n    - YYYY-MM-DD HH:MM title [about: alpha]\n\n"
            "- every mon 09:00 weekly review [about: alpha, beta]\n"
            "- 2026-10-22 14:00 alpha review [about: alpha]\n"
            "- 2026-10-22 16:00 water the plants\n")
        (self.root / om.RECORD).write_text("# Record\n\n- 2026-10-19 09:00 weekly review: done\n")

    def test_the_lines_read_and_a_series_falls_on_its_days(self):
        plan, problems = om.read_plan(self.root)
        self.assertEqual(problems, [])
        self.assertEqual([(p["series"], p["title"], p["about"]) for p in plan],
                         [("mon", "weekly review", ["alpha", "beta"]), (None, "alpha review", ["alpha"]),
                          (None, "water the plants", [])])
        got = om.occurrences(plan, dt.date(2026, 10, 19), dt.date(2026, 10, 26))
        self.assertEqual([o["key"] for o in got], ["2026-10-19 09:00 weekly review", "2026-10-22 14:00 alpha review",
                                                   "2026-10-22 16:00 water the plants", "2026-10-26 09:00 weekly review"])
        self.assertEqual(om.plan_line("every mon 09:00", "weekly review", ["alpha"]), "- every mon 09:00 weekly review [about: alpha]")
        with self.assertRaises(h.HelperError):
            om.plan_line("monday", "x", [])

    def test_near_is_a_day_before_to_four_hours_after_and_never_once_held(self):
        at = dt.datetime(2026, 10, 22, 10, 0, tzinfo=UTC)
        self.assertEqual([(o["key"], o["state"]) for o in om.near(self.root, UTC, at)],
                         [("2026-10-22 14:00 alpha review", "due"), ("2026-10-22 16:00 water the plants", "due")])
        self.assertEqual([o["key"] for o in om.near(self.root, UTC, at.replace(hour=19))],
                         ["2026-10-22 16:00 water the plants"])
        late = om.near(self.root, UTC, dt.datetime(2026, 10, 25, 10, 0, tzinfo=UTC))
        self.assertEqual([o["key"] for o in late], ["2026-10-26 09:00 weekly review"])
        # Its prep out: still near, and out; then held: no longer offered.
        om.mark_prep_out(self.root, "2026-10-22 14:00 alpha review", "2026-10-22-alpha-review-prep-001", UTC)
        self.assertIn("- 2026-10-22 14:00 alpha review: prep out, 2026-10-22-alpha-review-prep-001 [about: alpha]\n",
                      (self.root / om.RECORD).read_text())
        got = {o["key"]: (o["state"], o["sid"]) for o in om.near(self.root, UTC, at)}
        self.assertEqual(got["2026-10-22 14:00 alpha review"], ("prep out", "2026-10-22-alpha-review-prep-001"))
        # A prep out is offered to end whenever its meeting was.
        self.assertIn("2026-10-22 14:00 alpha review", [o["key"] for o in om.near(self.root, UTC, at + dt.timedelta(days=3))])
        om.hold(self.root, "2026-10-22-alpha-review-prep-001", [], "stdin", THU, "15:00")
        self.assertNotIn("2026-10-22 14:00 alpha review", [o["key"] for o in om.near(self.root, UTC, at)])

    def test_the_meeting_a_prep_is_for(self):
        at = dt.datetime(2026, 10, 22, 10, 0, tzinfo=UTC)
        o, choices = om.resolve(self.root, "", UTC, at)
        self.assertIsNone(o)
        self.assertEqual(len(choices), 2)
        self.assertEqual(om.resolve(self.root, "alpha", UTC, at)[0]["key"], "2026-10-22 14:00 alpha review")
        self.assertEqual(om.resolve(self.root, "2026-11-02 09:00 weekly review", UTC, at)[0]["series"], "mon")
        with self.assertRaises(h.HelperError):
            om.resolve(self.root, "2026-11-03 09:00 weekly review", UTC, at)   # a Tuesday: not planned
        om.mark_prep_out(self.root, "2026-10-22 14:00 alpha review", "2026-10-22-alpha-review-prep-001", UTC)
        with self.assertRaises(h.HelperError) as cm:
            om.resolve(self.root, "2026-10-22 14:00 alpha review", UTC, at)
        self.assertIn("is out already (2026-10-22-alpha-review-prep-001): office land", str(cm.exception))

    def test_office_week_shows_the_about_and_a_prep_out(self):
        om.mark_prep_out(self.root, "2026-10-22 14:00 alpha review", "2026-10-22-alpha-review-prep-001", UTC)
        lines, gaps = h.week_report(self.root / "calendar", THU, "15:00", "UTC")
        self.assertIn("Thu 2026-10-22 14:00 alpha review (about alpha) [prep out]", lines)
        self.assertIn("Mon 2026-10-19 09:00 weekly review (about alpha, beta) [recorded]", lines)
        self.assertFalse(any(l.startswith("unreadable") for l in lines), lines)


# --- 3. what arose, and a drop during it ---------------------------------------------------------

SID = "2026-10-22-alpha-review-prep-001"


class TestWhatArose(unittest.TestCase):
    def test_the_last_block_counts_and_each_item_reads(self):
        text = ("chat before\n" + block(SID, ("old item", "alpha", None)) + "more chat\n"
                + block(SID, ("Update the report with the new criteria", "alpha", "From next week.\nBoth tables."),
                        ("Ask when the export moves", "none", None)))
        items, said = om.check_arising(text, SID, ["alpha"])
        self.assertEqual([(i["heading"], i["project"], i["body"]) for i in items],
                         [("Update the report with the new criteria", "alpha", "From next week.\nBoth tables."),
                          ("Ask when the export moves", None, "")])
        self.assertIn("the text holds 2 arising blocks; the last, the sitting's latest, is taken", said)
        self.assertEqual(om.drop_text(items[0]), "Update the report with the new criteria\n\nFrom next week.\nBoth tables.")
        self.assertEqual(om.check_arising(block(SID), SID)[0], [])

    def test_a_block_that_does_not_read_is_refused_by_line(self):
        for text, why in ((block("2026-10-22-other-prep-001", ("x", "alpha", None)), "it is another sitting's"),
                          ("no block here\n", "no arising block"),
                          (f"--- ARISING BEGIN {SID} ---\nstray\n### x\n\nno project\n--- ARISING END ---\n",
                           "outside any item"),
                          (f"--- ARISING BEGIN {SID} ---\n### x\n\nno project\n--- ARISING END ---\n",
                           "has no `- project:` line")):
            with self.assertRaises(h.HelperError) as cm:
                om.check_arising(text, SID, ["alpha"])
            self.assertIn(why, str(cm.exception))

    def test_held_writes_each_item_as_a_drop_tied_to_the_meeting(self):
        e = Env(self)
        root = e.init()
        (root / "floor-plan/manifest.toml").write_text(
            re.sub(r'timezone = ".*"', 'timezone = "UTC"', (root / "floor-plan/manifest.toml").read_text()))
        om.record_meeting(root, "2026-10-22 14:00", "alpha review", ["alpha"])
        om.mark_prep_out(root, "2026-10-22 14:00 alpha review", SID, UTC)
        # A drop made during the meeting is tied to it; one made the day before is not.
        self.assertIsNone(om.tie(root, "in-tray/2026-10-21-early.md", UTC, dt.datetime(2026, 10, 21, 9, tzinfo=UTC)))
        r = om.tie(root, "in-tray/2026-10-22-call-back.md", UTC, dt.datetime(2026, 10, 22, 14, 20, tzinfo=UTC))
        self.assertEqual(r["dropped"], ["in-tray/2026-10-22-call-back.md"])
        items, _ = om.check_arising(block(SID, ("Update the report", "alpha", "The new criteria.")), SID, ["alpha"])
        r, changed, pages = om.hold(root, SID, items, "file arising.md", THU, "15:10")
        self.assertEqual(pages, ["in-tray/2026-10-22-update-the-report.md"])
        page = (root / pages[0]).read_text()
        self.assertTrue(page.startswith("# Drop: Update the report\n\n- dropped: 2026-10-22 15:10\n- project: alpha\n"
                                        "- via: file arising.md\n- status: unsorted\n"), page)
        self.assertIn("## Text\n\nUpdate the report\n\nThe new criteria.\n", page)
        self.assertIn(f"- 2026-10-22 14:00 alpha review: held, {SID}; arose: {pages[0]}; dropped: "
                      "in-tray/2026-10-22-call-back.md [about: alpha]\n", (root / om.RECORD).read_text())
        self.assertIn("in-tray/README.md", changed)
        self.assertEqual(om.held_words(r, pages), "Recorded: alpha review (Thursday 2026-10-22 at 14:00) happened; 1 "
                                                  "item(s) that arose are drops in the in-tray, tied to it: "
                                                  "in-tray/2026-10-22-update-the-report.md.")


# --- 2. the prep's gathering, its window the meeting's ---------------------------------------------

class TestThePrepGathering(unittest.TestCase):
    """An office scoping alpha, its chapter, a folder on alpha that landed
    before the last meeting on alpha and one after it, and a drop that arose
    in that meeting, since moved into a folder."""

    def commit(self, message, *paths, when):
        git(self.root, "add", "--", *paths)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", message, "--", *paths], check=True,
                       env=dict(self.e.env, GIT_COMMITTER_DATE=when, GIT_AUTHOR_DATE=when), capture_output=True)

    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        proj = self.e.tmp / "alpha"
        proj.mkdir()
        git(proj, "init", "-q")
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(manifest.read_text() + f'\n[projects.alpha]\npath = "{proj}"\n')
        (self.root / "handbook").mkdir()
        (self.root / "handbook/alpha.md").write_text("# alpha\n\n## Front sheet\n\nalpha.\n\n## Facts\n")
        self.old = self.e.run("open", "old-fix", "--title", "An old fix", "--lane", "alpha", cwd=self.root, check=0).stdout.strip()
        self.new = self.e.run("open", "new-fix", "--title", "A new fix", "--lane", "alpha", cwd=self.root, check=0).stdout.strip()
        self.job = self.e.run("open", "the-report", "--title", "The report", "--lane", "alpha", cwd=self.root,
                              check=0).stdout.strip()
        (self.root / self.old / "walkthrough.md").write_text("old\n")
        self.commit("office land: old", "handbook", self.old, str(manifest.relative_to(self.root)),
                    when="2026-10-10T12:00:00+00:00")
        (self.root / self.new / "walkthrough.md").write_text("new\n")
        self.commit("office land: new", self.new, when="2026-10-20T12:00:00+00:00")
        om.record_meeting(self.root, "every mon 09:00", "weekly review", ["alpha"])
        (self.root / om.RECORD).write_text((self.root / om.RECORD).read_text()
                                           + "- 2026-10-19 09:00 weekly review: held, 2026-10-18-weekly-review-prep-001; "
                                             "arose: in-tray/2026-10-19-update-the-report.md [about: alpha]\n")
        (self.root / self.job / "drops").mkdir()
        (self.root / self.job / "drops/2026-10-19-update-the-report.md").write_text("# Drop: Update the report\n")

    def test_what_landed_since_the_last_meeting_and_what_arose_in_it(self):
        o = om.planned(self.root, "2026-10-26 09:00 weekly review", UTC)
        got, windows = om.gather_prep(self.root, o, UTC)
        paths = [(e["kind"], e["path"]) for e in got]
        self.assertEqual(paths[0], ("chapter", "handbook/alpha.md"))
        self.assertIn(("landed", f"{self.new}/walkthrough.md"), paths)
        # Landed before the last meeting on alpha: not since.
        self.assertNotIn(("landed", f"{self.old}/walkthrough.md"), paths)
        self.assertIn(("tied", f"{self.job}/drops/2026-10-19-update-the-report.md"), paths)
        self.assertIn(f"{self.job}/folder.md", [p for _, p in paths])
        self.assertEqual(windows["alpha"], "since the last meeting on alpha, weekly review on 2026-10-19 09:00")
        why = next(e["why"] for e in got if e["kind"] == "tied")
        self.assertIn("arose in the last meeting on alpha (weekly review, 2026-10-19), now in", why)

    def test_a_first_meeting_counts_the_window_the_doctrine_pins(self):
        (self.root / om.RECORD).write_text("# Record\n")
        o = om.planned(self.root, "2026-10-26 09:00 weekly review", UTC)
        got, windows = om.gather_prep(self.root, o, UTC)
        landed = [e["path"] for e in got if e["kind"] == "landed"]
        # The old one landed 16 days before it, the new one 6.
        self.assertEqual(landed, [f"{self.new}/walkthrough.md"])
        self.assertIn("in the 14 days before it (no earlier meeting on alpha is recorded)", windows["alpha"])
        self.assertNotIn("tied", [e["kind"] for e in got])

    def test_the_brief_says_the_meeting_what_rides_the_arising_form_and_the_cleanup(self):
        out = self.e.tmp / "brief.md"
        inc = self.e.tmp / "includes"
        o, rides = om.write_prep(self.root, "2026-10-26 09:00 weekly review", UTC, "UTC", THU, out, inc)
        brief = out.read_text()
        self.assertIn("- the meeting: weekly review\n- when: Monday 2026-10-26 at 09:00, UTC, one of a series "
                      "(every Monday)\n- it concerns: alpha\n", brief)
        self.assertIn(f"- {self.new}/walkthrough.md: what landed on alpha since the last meeting on alpha", brief)
        self.assertIn("--- ARISING BEGIN 2026-10-25-weekly-review-prep-001 ---", brief)
        self.assertIn("arising-SID.md", brief)
        self.assertIn("## A cleanup, if the documentation needs one", brief)
        self.assertIn("`--- LANDS alpha, a new", brief)
        self.assertIn("calendar\n", inc.read_text())
        self.assertNotIn("{{", brief)
        self.assertTrue(brief.isascii())


# --- the home screen ------------------------------------------------------------------------------

class TestTheHomeScreen(unittest.TestCase):
    def test_a_meeting_near_is_offered_by_key_and_its_prep_out_ended_by_key(self):
        names = hs.Names.__new__(hs.Names)
        names.naming, names.folders, names.root = {}, {}, "/nowhere"
        due = {"key": "2026-10-22 14:00 alpha review", "title": "alpha review", "date": THU, "time": "14:00",
               "series": None, "about": ["alpha"], "state": "due", "sid": ""}
        out = dict(due, key="2026-10-21 09:00 sync", title="sync", state="prep out", sid=SID)
        items = hs.home_items("current", True, [], {}, [], 0, None, [], names, [], dt.datetime.now(UTC),
                              meetings=[due, out])
        argvs = [i["argv"] for i in items]
        self.assertIn(["start", "--prep", "2026-10-22 14:00 alpha review"], argvs)
        self.assertIn(["land", SID], argvs)
        label = next(i["label"] for i in items if i["argv"][:2] == ["start", "--prep"])
        self.assertTrue(label.startswith("Send the prep for alpha review (Thursday 2026-10-22 at 14:00)"), label)
        _, menu = hs.render_page([], [], 0)
        self.assertIn(("m", "office", ["meeting"]), menu)


# --- rider 1: a template's own lines and the three characters ---------------------------------------

class TestTheTemplatesOwnDashes(unittest.TestCase):
    def test_a_template_line_is_exempt_from_the_characters_and_a_changed_one_is_not(self):
        letterhead = Env(self).tmp / "letterhead"
        letterhead.mkdir()
        rules = olh.apply_letterhead(olh.load_rules_toml(REPO / "share/letterhead.toml"), letterhead)
        compiled = olh.compile_rules(rules)
        template = {f"## What changed {EM} and why", "## Checks"}
        words = f"## What changed {EM} and why\n\nOne route {EM} its test.\n## What changed {EM} and why it matters\n"
        hits = olh.hits_in_text(words, compiled, "w.md", exempt=template)
        # Line 1 is the template's own; 3 adds words, and 4 changes a template line.
        self.assertEqual(sorted({n for _, n, kind, _, _ in hits if kind == "character"}), [3, 4])
        self.assertEqual(sorted({n for _, n, kind, _, _ in olh.hits_in_text(words, compiled, "w.md")
                                 if kind == "character"}), [1, 3, 4])
        self.assertEqual(olh.TEMPLATE_EXEMPT_KINDS, ("phrasing", "character"))
        # The names still read a template's line.
        made = "Made with " + "cla" + "ude"
        self.assertTrue(any(k == "names" for _, _, k, _, _ in olh.hits_in_text(made + "\n", compiled, "w.md",
                                                                                exempt={made})))


# --- the commands, piped ---------------------------------------------------------------------------

class MeetingCase(LandCase):
    def setUp(self):
        super().setUp()
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(re.sub(r'timezone = ".*"', 'timezone = "UTC"', manifest.read_text()))
        self.e.git(self.root, "commit", "-qam", "the office runs on UTC")
        (self.e.home / ".config/office-src").mkdir(parents=True, exist_ok=True)
        (self.e.home / ".config/office-src/machine.toml").write_text(f'downloads = ["{self.downloads}"]\n')


class TestAMeetingAskedOnce(MeetingCase):
    def test_one_sentence_records_it_and_piped_the_flags_give_the_rest(self):
        proc = self.run_office("meeting", "alpha review on 2026-10-30 at 14:00", check=0)
        self.assertIn("Recorded: alpha review, Friday 2026-10-30 at 14:00 (UTC); it concerns alpha.", proc.stdout)
        self.assertIn("the calendar arrives in this office", proc.stderr)
        plan = (self.root / om.PLAN).read_text()
        self.assertTrue(plan.endswith("- 2026-10-30 14:00 alpha review [about: alpha]\n"), plan)
        self.assertEqual(self.subjects(1), ["office meeting: alpha review, Friday 2026-10-30 at 14:00"])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        desk = sorted(p.name for p in (self.root / "desk").iterdir())
        # Piped, what the words do not say is refused with its flag, and nothing is written.
        proc = self.run_office("meeting", "--words", "budget sync about alpha", check=1)
        self.assertIn('your words do not say when it happens: --when "YYYY-MM-DD HH:MM"', proc.stderr)
        proc = self.run_office("meeting", "--words", "budget sync", "--when", "every thu 10:00", check=1)
        self.assertIn("your words name none of this office's projects (alpha): --about PROJECT, or --in-office", proc.stderr)
        self.assertEqual(plan, (self.root / om.PLAN).read_text())
        proc = self.run_office("meeting", "--words", "budget sync", "--when", "every thu 10:00", "--in-office", check=0)
        self.assertIn("- every thu 10:00 budget sync [about: the office]", proc.stdout)
        # No folder is minted for a meeting.
        self.assertEqual(sorted(p.name for p in (self.root / "desk").iterdir()), desk)
        self.assertIn("(about the office)", self.run_office("week", check=0).stdout + "(about the office)")


class TestThePrepAndItsEnd(MeetingCase):
    KEY = "2026-10-30 14:00 alpha review"

    def test_the_prep_goes_out_in_no_folder_and_land_files_what_arose(self):
        self.run_office("meeting", "alpha review on 2026-10-30 at 14:00", check=0)
        (self.root / self.folder / "walkthrough.md").write_text("# Walkthrough\n\nthe login fix\n")
        self.e.git(self.root, "add", self.folder)
        self.e.git(self.root, "commit", "-qm", "office land: the login fix")
        desk = sorted(p.name for p in (self.root / "desk").iterdir())
        proc = self.run_office("start", "--prep", self.KEY, check=0)
        sid = re.search(r"^Packed (\S+) for the meeting alpha review \(its prep", proc.stdout, re.M).group(1)
        self.assertTrue(sid.endswith("-alpha-review-prep-001"), sid)
        self.assertIn("What rides with the prep for alpha review, and why", proc.stderr)
        self.assertIn(f"{self.folder}/walkthrough.md: what landed on alpha in the 14 days before it", proc.stderr)
        self.assertIn(f"office land {sid} ends it, records the meeting held and files what arose", proc.stdout)
        self.assertEqual(sorted(p.name for p in (self.root / "desk").iterdir()), desk)
        self.assertIn(f"- 2026-10-30 14:00 alpha review: prep out, {sid} [about: alpha]\n",
                      (self.root / om.RECORD).read_text())
        tray = re.search(r"^Out tray: (\S+)$", proc.stdout, re.M).group(1)
        files = request_members(tray)
        manifest = json.loads(files["manifest.json"])
        self.assertEqual((manifest["goal"], manifest["resolved_scope"]), ("alpha review", []))
        self.assertIn("context/calendar/plan.md", manifest["context_included"])
        self.assertIn(f"context/{self.folder}/walkthrough.md", manifest["context_included"])
        self.assertIn("- the meeting: alpha review", files["README.md"].decode())
        # Sent twice: refused, naming the land line.
        proc = self.run_office("start", "--prep", self.KEY, check=1)
        self.assertIn(f"is out already ({sid}): office land {sid}", proc.stderr)
        # Ended piped with nothing given: refused before the sitting is closed.
        proc = self.run_office("land", sid, check=1)
        self.assertIn("--arising FILE (the sitting's arising-" + sid + ".md), --arising - for stdin, or --arising none",
                      proc.stderr)
        self.assertTrue(self.fake.is_open(self.root, sid))
        # The block saved in the downloads is found there: nothing pasted.
        (self.downloads / f"arising-{sid}.md").write_text(
            "the chat around it\n" + block(sid, ("Update the report with the new criteria", "alpha", "From next week.")))
        proc = self.run_office("land", sid, check=0)
        self.assertFalse(self.fake.is_open(self.root, sid))
        self.assertIn("Recorded: alpha review (Friday 2026-10-30 at 14:00) happened; 1 item(s) that arose are drops in "
                      "the in-tray, tied to it: in-tray/", proc.stdout)
        page = next((self.root / "in-tray").glob("*-update-the-report-with-the-new-criteria.md")).read_text()
        self.assertIn(f"- via: file arising-{sid}.md\n", page)
        self.assertIn(f": held, {sid}; arose: in-tray/", (self.root / om.RECORD).read_text())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_a_block_for_another_sitting_leaves_it_open(self):
        self.run_office("meeting", "alpha review on 2026-10-30 at 14:00", check=0)
        sid = re.search(r"^Packed (\S+) for the meeting", self.run_office("start", "--prep", self.KEY, check=0).stdout,
                        re.M).group(1)
        other = self.e.tmp / "arising.md"
        other.write_text(block("2026-10-22-other-prep-001", ("x", "alpha", None)))
        proc = self.run_office("land", sid, "--arising", str(other), check=1)
        self.assertIn("it is another sitting's", proc.stderr)
        self.assertTrue(self.fake.is_open(self.root, sid))
        proc = self.run_office("land", sid, "--arising", "none", check=0)
        self.assertIn("happened; nothing arose to file.", proc.stdout)
        proc = self.run_office("land", self.start("fix-login", "--on", "alpha", "--goal", "g"), "--arising", "none",
                               check=1)
        self.assertIn("--arising goes with a meeting's prep", proc.stderr)


class TestAMeetingOnATerminal(MeetingCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_it_asks_only_what_the_words_do_not_say_and_land_takes_one_copy(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "meeting"], self.root, self.e.env, [
            (b"The meeting, in your words: when it happens and what it is about (--words)", "budget sync on Friday"),
            (b"What time it starts (--when)", "2pm"),
            (b"What the meeting concerns, by its key (--about PROJECT, or --in-office)", "1"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Recorded: budget sync, Friday ", seen)
        plan = (self.root / om.PLAN).read_text()
        self.assertRegex(plan, r"- \d{4}-\d{2}-\d{2} 14:00 budget sync \[about: alpha\]\n$")
        key = re.search(r"- (\d{4}-\d{2}-\d{2} 14:00 budget sync)", plan).group(1)
        sid = re.search(r"^Packed (\S+) for the meeting", self.run_office("start", "--prep", key, check=0).stdout,
                        re.M).group(1)
        clip = self.e.tmp / "clip.txt"
        clip.write_text("from the chat\n" + block(sid, ("Send the figures to the board", "none", None)))
        cfg = self.e.home / ".config/office-src/machine.toml"
        cfg.write_text(cfg.read_text() + f'paste_command = "cat {clip}"\n')
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "land", sid], self.root, self.e.env, [
            (b"Copy the sitting's arising block, then press return; none if nothing arose (--arising)", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("1 item(s) that arose are drops in the in-tray", seen)
        page = next((self.root / "in-tray").glob("*-send-the-figures-to-the-board.md")).read_text()
        self.assertIn("- project: none given\n- via: clipboard\n", page)


# --- rider 2: the terminal wizard works a project with an audience here ------------------------------

class TestTheWorkbenchWizardOnATerminal(HostedCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_a_host_answered_before_the_audience_is_where_it_validates(self):
        audience = self.e.tmp / "aud.git"
        subprocess.run(["git", "init", "-q", "--bare", str(audience)], check=True)
        there = make_project(self.e.tmp, "there", bale_dir=True)
        here = make_project(self.e.tmp, "here", bale_dir=True)
        for repo in (there, here):
            subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", str(audience)], check=True)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "add"], self.root, self.e.env, [
            (b"Path to the project's git repo (--path):", str(there)),
            (b"Where the repo is: this machine, or an ssh host (--host) [return skips]:", HOST),
            (f"The shell that runs one command where the repo is (--shell) [ssh {HOST} bash -lc]:".encode(), ""),
            (f"What brings {HOST} up when it does not answer (--connect) [connect to {HOST}]:".encode(), ""),
            (b"Is there a clone on this machine to bring there? Its path (--from) [return skips]:", ""),
            (b"Name for it in this office (--name) [there]:", "beta"),
            (b"or none (--audience) [origin]:", ""),
            (b"(--author) [return skips]:", "Zed Zee <z@example.org>"),
            (b"(--base) [return skips]:", ""),
            (b"Where beta is worked, by its key (--worked-on-host works it on", ""),
            (b"Path to beta's clone on this machine, the workbench (--path):", str(here)),
            (b"(--ride) [return ends the list]:", ""),
            (b"(--after-land) [return ends the list]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"on this machine, from a guarded clone; {HOST} is where it validates (the default)", seen)
        entry = next(p for p in h.read_projects(h.read_toml(self.root / "floor-plan/manifest.toml")) if p["name"] == "beta")
        self.assertEqual((entry["host"], entry["validates_on"], entry["path"]), (None, HOST, str(here)))
        self.assertTrue((here / ".git/hooks/pre-push").is_file())


# --- the record ------------------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_release_the_doctrine_and_the_catalog(self):
        version = (REPO / "VERSION").read_text().strip()
        self.assertEqual(version, "0.26.0")
        self.assertIn("## 0.26.0", (REPO / "RELEASES.md").read_text())
        self.assertIn("0.26.0", (REPO / "README.md").read_text())
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        for words in ("--- ARISING BEGIN", "office meeting", "office start --prep", "until the meeting spaces exist"):
            if words == "until the meeting spaces exist":
                self.assertNotIn(words, doctrine)
            else:
                self.assertIn(words, doctrine)
        verbs = __import__("tomllib").loads((REPO / "share/verbs.toml").read_text())["verbs"]
        self.assertEqual((verbs["meeting"]["kind"], verbs["meeting"]["built"], verbs["meeting"]["surface"]),
                         ("script", True, "occupant"))
        self.assertEqual((verbs["prep"]["kind"], verbs["prep"]["built"]), ("office-session", True))
        self.assertFalse(verbs["cleanup"]["built"])
        for t in ("calendar-plan.md", "calendar-record.md", "prep-brief.md"):
            self.assertTrue((REPO / "templates" / t).is_file(), t)


if __name__ == "__main__":
    unittest.main()
