"""Tests for office-src 0.44.0: answers from the artifact.

One class (or a unit class and a verb class) per item of the brief
(2026-11-03-answers-from-the-artifact-002):

1. a question start or land would ask is not asked when an artifact or an
   office record answers it: the one waiting bundle, the one response in
   the downloads, the folder's lane piped, a brief's RIDES lines, a LANDS
   line naming a project no office here scopes;
2. machine.toml lists the offices on this machine, and each office's home
   screen and walk-in show what waits for the others, a key running the
   verb there;
3. every line the office hands the occupant is an office line: a
   clarification's Next line and tail, and bale's verbs in office words;
4. a bailout's Next line (the half this release left: office start
   --handoff is a proposal, and the line says so);
5. one copy runs a probe: the run line in its purpose header, and the
   home screen's r key;
6. a standing alone on the clipboard reaches the office through office
   probe, and the standing key shows from a sitting's first turn;
7. the briefs and the doctrine say the planner's half.

The worlds are the suite's own: tests/test_land.py's LandCase (an office
scoping alpha, a fake bale), tests/test_standing.py's SittingCase (a
sitting out in the office), tests/test_probe.py's blocks. The two offices
of item 2 are invented (home and works), built in the test's own temporary
tree, and every config the office reads is the test's (the suite's Env
points HOME and XDG_CONFIG_HOME away). The terminal classes run in the
serial lane. Run with the rest of the suite:

    tests/run.sh test_from_the_artifact
"""

import os
import pathlib
import re
import sys
import tempfile
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import LandCase, bundle_file, response_tarball, git_repo  # noqa: E402
from test_probe import probe_block  # noqa: E402
from test_standing import SittingCase, standing  # noqa: E402
from test_home_screen import home, bundle_argv, downloads_set  # noqa: E402

import office_bale as ob  # noqa: E402
import office_helper as oh  # noqa: E402
import office_home as hs  # noqa: E402
import office_probe as op  # noqa: E402


def flat(text):
    """A screen's text with its wrapping undone, for a line a test pins."""
    return " ".join(text.split())


def machine_file(case):
    return case.e.home / ".config/office-src/machine.toml"


# --- 1. a question asked only when nothing answers it ------------------------------------------

class TestTheRidesLine(unittest.TestCase):
    def test_paths_none_and_a_line_that_does_not_read(self):
        self.assertEqual(oh.brief_rides("# Brief\n"), (None, []))
        self.assertEqual(oh.brief_rides("--- RIDES none ---\n"), ([], []))
        rides, problems = oh.brief_rides("--- RIDES lib/a.py ---\n--- RIDES docs/* ---\n--- RIDES lib/a.py ---\n")
        self.assertEqual((rides, problems), (["lib/a.py", "docs/*"], []))
        rides, problems = oh.brief_rides("--- RIDES ---\n--- RIDES none ---\n--- RIDES src ---\n")
        self.assertEqual(rides, ["src"])
        self.assertEqual(len(problems), 2)
        self.assertIn("line 1: not `--- RIDES PATH ---`", problems[0])
        self.assertIn("RIDES none and names paths beside it", problems[1])

    def test_a_marker_in_a_fence_or_a_notepad_page_is_quoted_text(self):
        text = ("```\n--- RIDES src ---\n```\n--- NOTEPAD PAGE BEGIN notepad/x.md ---\n--- RIDES docs ---\n"
                "--- NOTEPAD PAGE END ---\n")
        self.assertEqual(oh.brief_rides(text), (None, []))


class TestAnswersFromTheArtifact(LandCase):
    def two_out(self):
        a = self.start("fix-login", "--on", "alpha", "--goal", "g")
        b = self.start("fix-login", "--on", "alpha", "--goal", "again", "--write", "docs")
        return a, b

    def test_piped_land_takes_the_one_session_whose_response_is_in_the_downloads(self):
        a, b = self.two_out()
        response_tarball(self.downloads, b, {"docs/d.md": "x\n"})
        downloads_set(self)
        proc = self.run_office("land", check=0)
        self.assertIn(f"from the downloads: response-{b}.tar.gz is here, so {b} lands (office land SID names "
                      "another)", proc.stderr)
        self.assertIn(f"Landed: {b} is applied in alpha", proc.stdout)
        self.assertTrue(self.fake.is_open(self.proj, a))

    def test_with_responses_for_both_piped_it_still_names_one(self):
        a, b = self.two_out()
        response_tarball(self.downloads, a, {"src/a.py": "x\n"})
        response_tarball(self.downloads, b, {"docs/d.md": "x\n"})
        downloads_set(self)
        proc = self.run_office("land", check=1)
        self.assertIn("2 sessions are out, 2 with a response in your downloads; name one: office land SID", proc.stderr)
        self.assertEqual(self.fake.calls_of("apply"), [])

    def test_piped_start_takes_where_from_the_folders_lane(self):
        proc = self.run_office("start", "fix-login", "--goal", "Fix it", check=0)
        self.assertIn("from the folder: the work lands on alpha, the project the folder's lane names "
                      "(--in-office sends it to the office instead)", proc.stderr)
        self.assertRegex(proc.stdout, r"Packed \S+ for desk/")

    def test_piped_where_nothing_answers_still_refuses_naming_the_flags(self):
        self.run_office("open", "no-lane", check=0)
        proc = self.run_office("start", "no-lane", "--goal", "g", check=1)
        self.assertIn("say where the work lands: --in-office, or --on PROJECT (alpha); nothing answers it (no "
                      "bundle's paths, no lane), and piped input is never asked", proc.stderr)

    def rider(self, title, rides):
        self.run_office("rider", "add", title, "--source", "a test", "--rides", rides, "--text", title, check=0)

    def number(self):
        return re.search(r"^- number: (\d+)$", self.folder_md(), re.M).group(1)

    def test_a_briefs_rides_lines_name_the_riders_piped(self):
        self.rider("Mend the docs", "docs/d.md")
        self.rider("Tidy the source", "src/*")
        brief = f"# Brief\n\n--- LANDS alpha, folder {self.number()} ---\n--- RIDES docs/d.md ---\n"
        b = bundle_file(self.downloads, "2026-11-03-rides", bundle_argv("rides-pass"), brief=brief)
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn("from the brief: rider 1, Mend the docs, rides docs/d.md (its RIDES line names docs/d.md): "
                      "carried with this session (--carry none leaves it on the riders page)", proc.stderr)
        self.assertIn("rider 1 carried into", proc.stderr)
        self.assertNotIn("rider 2 carried", proc.stderr)
        self.assertIn("Mend the docs", self.folder_md())

    def test_rides_none_carries_none_and_carry_still_wins(self):
        self.rider("Tidy the source", "src/*")
        brief = f"# Brief\n\n--- LANDS alpha, folder {self.number()} ---\n--- RIDES none ---\n"
        b = bundle_file(self.downloads, "2026-11-03-none", bundle_argv("none-pass"), brief=brief)
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn("from the brief: RIDES none, so no rider is carried (--carry N carries one)", proc.stderr)
        self.assertNotIn("carried into", proc.stderr)

    def test_a_lands_line_no_office_here_scopes_is_one_line_and_no_refusal(self):
        brief = "# Brief\n\n--- LANDS gamma, a new folder ---\n"
        b = bundle_file(self.downloads, "2026-11-03-gamma", bundle_argv("gamma-pass"), brief=brief)
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn("from the brief: the bundle lands on gamma, which no office on this machine scopes "
                      "(machine.toml's offices); office projects add gamma PATH scopes it here, and office withdraw "
                      "--bundle 2026-11-03-gamma takes it out of the offer", flat(proc.stderr))
        self.assertNotIn("Packed", proc.stdout)
        self.assertEqual(self.fake.calls_of("open"), [])


class TestTheOneBundleOnATerminal(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_bare_start_takes_the_one_bundle_waiting(self):
        downloads_set(self)
        brief = "# Brief\n\n--- LANDS alpha, a new folder ---\n"
        bundle_file(self.downloads, "2026-11-03-one", bundle_argv("one-pass"), brief=brief)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [])
        self.assertEqual(code, 0, seen)
        self.assertIn("from the downloads: one bundle waits, 2026-11-03-one; starting it (a plain office start "
                      "FOLDER starts a job instead)", flat(seen))
        self.assertNotIn("The bundle to start, by its key", seen)
        self.assertRegex(seen, r"Packed \d{4}-\d{2}-\d{2}-one-pass-001 for desk/")


# --- 2. the offices on this machine ---------------------------------------------------------------

class TestTheOfficesList(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="offices-list-"))
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)
        self.mf = self.tmp / "cfg" / "machine.toml"

    def office(self, name, title=None):
        root = self.tmp / name
        (root / "floor-plan").mkdir(parents=True)
        (root / "floor-plan/manifest.toml").write_text(f'[office]\nname = "{title or ""}"\n')
        return root

    def test_appended_once_named_and_a_root_gone_said_and_skipped(self):
        a, b = self.office("one", "Home"), self.office("two")
        self.assertIsNone(oh.machine_offices(self.mf))
        self.mf.parent.mkdir(parents=True)
        self.mf.write_text('downloads = ["~/Downloads"]\n\n[clipboard]\ncommand = "x"\n')
        self.assertEqual(oh.add_machine_office(self.mf, a), f'offices = ["{a}"]')
        self.assertIsNone(oh.add_machine_office(self.mf, a), "listed once")
        oh.add_machine_office(self.mf, b)
        text = self.mf.read_text()
        self.assertIn('downloads = ["~/Downloads"]', text)
        self.assertIn("[clipboard]\ncommand = \"x\"\n", text, "every other line as it was")
        self.assertEqual(oh.machine_offices(self.mf), [str(a), str(b)])
        __import__("shutil").rmtree(b)
        found, skipped = oh.listed_offices(self.mf)
        self.assertEqual(found, [(str(a), "Home")])
        self.assertIn("is no longer an office", skipped[0])
        self.assertEqual(oh.machine_offices(self.mf), [str(a), str(b)], "never removed by the office")
        with self.assertRaises(oh.HelperError):
            oh.add_machine_office(self.mf, self.tmp / "nothing")

    def test_a_list_spread_over_lines_is_replaced_whole(self):
        a, b = self.office("one"), self.office("two")
        self.mf.parent.mkdir(parents=True)
        self.mf.write_text(f'offices = [\n  "{a}",\n]\nout_tray = "~/t"\n')
        oh.add_machine_office(self.mf, b)
        self.assertEqual(self.mf.read_text(), f'offices = ["{a}", "{b}"]\nout_tray = "~/t"\n')

    def test_the_name_is_the_floor_plans_else_the_directorys(self):
        self.office("plain")
        self.mf.parent.mkdir(parents=True)
        oh.add_machine_office(self.mf, self.tmp / "plain")
        self.assertEqual(oh.listed_offices(self.mf)[0], [(str(self.tmp / "plain"), "plain")])


class TwoOfficesCase(LandCase):
    """LandCase's office (home, scoping alpha) and a second office on the
    same machine, works, scoping beta, both listed in machine.toml."""

    def setUp(self):
        super().setUp()
        self.works = self.e.init("works")
        self.e.found(self.works)
        self.beta = git_repo(self.e.tmp / "beta", {"lib/b.py": "b\n", "README.md": "beta\n"})
        self.e.run("projects", "add", "beta", str(self.beta), cwd=self.works, check=0)
        self.wfolder = self.e.run("open", "beta-job", "--lane", "beta: lib", cwd=self.works, check=0).stdout.strip()
        mf = machine_file(self)
        text = mf.read_text() if mf.is_file() else ""
        mf.parent.mkdir(parents=True, exist_ok=True)
        if "downloads" not in text:
            mf.write_text(f'downloads = ["{self.downloads}"]\n' + text)
        oh.add_machine_office(mf, self.root)
        oh.add_machine_office(mf, self.works)

    def in_works(self, *args, check=None):
        return self.e.run(*args, cwd=self.works, check=check)

    def start_in_works(self):
        proc = self.in_works("start", "beta-job", "--on", "beta", "--goal", "g", check=0)
        return re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)


class TestTheOfficesOnThisMachine(TwoOfficesCase):
    def test_init_and_default_list_the_office_and_the_survey_names_them(self):
        listed = oh.machine_offices(machine_file(self))
        self.assertIn(os.path.realpath(self.root), listed)
        self.assertIn(os.path.realpath(self.works), listed)
        survey = (self.works / "floor-plan/survey.md").read_text()
        self.assertRegex(survey, r"offices: .*home \(.*\)")
        third = self.e.init("third", "--no-default")
        self.assertIn(os.path.realpath(third), oh.machine_offices(machine_file(self)), "listed, the default or not")

    def test_the_walk_in_shows_a_response_for_the_other_office_with_its_line(self):
        sid = self.start_in_works()
        response_tarball(self.downloads, sid, {"lib/b.py": "fixed\n"})
        page = self.run_office(check=0).stdout
        self.assertIn("The other offices on this machine:", page)
        at = page.index("The other offices on this machine:")
        self.assertLess(page.index("Suggestion box:"), at, "after this office's own sections")
        self.assertIn(f"works ({os.path.realpath(self.works)}):", page)
        self.assertIn("(beta, in works): a response for it was saved", page)
        line = f"OFFICE_ROOT={os.path.realpath(self.works)} office land {sid}"
        self.assertIn(line, page)
        self.assertLess(page.index(line), page.rindex("Next:"))

    def test_the_home_screens_key_runs_the_verb_there(self):
        sid = self.start_in_works()
        response_tarball(self.downloads, sid, {"lib/b.py": "fixed\n"})
        out, menu = home(self, "--machine-file", str(machine_file(self)))
        self.assertIn(f"works ({os.path.realpath(self.works)}):", out)
        row = next(r for r in menu if r[1] == hs.ELSEWHERE)
        self.assertEqual(row[2:], [os.path.realpath(self.works), "land", sid])
        self.assertRegex(out, rf"\[{row[0]}\] Land \S+ \(beta, in works\): a response for it was saved")
        # The verb the key runs, as the home screen runs it.
        proc = self.e.run(*row[3:], cwd=self.e.tmp, extra={"OFFICE_ROOT": row[2]}, check=0)
        self.assertIn(f"Landed: {sid} is applied in beta", proc.stdout)

    def test_a_bundle_landing_on_the_other_offices_project_leaves_this_offer(self):
        brief = "# Brief\n\n--- LANDS beta, a new folder ---\n"
        b = bundle_file(self.downloads, "2026-11-03-for-works", bundle_argv("works-pass", write="lib"), brief=brief)
        out, menu = home(self, "--machine-file", str(machine_file(self)))
        mine = out[:out.index("works (")]
        self.assertNotIn("2026-11-03-for-works", mine)
        self.assertIn("Start the planner's bundle 2026-11-03-for-works in works (it lands on beta;", out)
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn(f"from the brief: the bundle lands on beta, which works scopes ({os.path.realpath(self.works)}), "
                      f"not this office; OFFICE_ROOT={os.path.realpath(self.works)} office start --bundle", flat(proc.stderr))
        self.assertIn("nothing was started here, and nothing written", proc.stderr)

    def test_a_bundle_the_other_office_opened_leaves_every_offer(self):
        brief = "# Brief\n\n--- LANDS the office, a new folder ---\n"
        b = bundle_file(self.downloads, "2026-11-03-opened", ["Plan it", "--slug", "opened-plan", "--read-only"],
                        brief=brief)
        self.in_works("start", "--bundle", str(b), check=0)
        out, _ = home(self, "--machine-file", str(machine_file(self)))
        self.assertNotIn("2026-11-03-opened", out[:out.index("works (")])
        self.assertIn("End the sitting opened-plan (the office, in works), once it is over", out)

    def test_an_office_that_cannot_be_read_is_one_line(self):
        page = self.run_office(check=0).stdout
        self.assertIn("nothing waits on you there", page)
        (self.works / "floor-plan/manifest.toml").write_text("not = [toml\n")
        out, _ = home(self, "--machine-file", str(machine_file(self)))
        self.assertNotIn("works (", out, "a root whose floor plan does not read is skipped, said under OFFICE_DEBUG")


# --- 3. the office's words over bale's --------------------------------------------------------------

class TestOfficeWords(unittest.TestCase):
    PLAN = {"sid": "2026-11-03-fix-login-001", "repo": "/w/alpha", "tarball": "response-x.tar.gz",
            "folders": ["desk/fix-login"], "folder_keys": {"desk/fix-login": "3"}, "label": "alpha"}

    def test_each_verb_bale_named_once_in_order_with_its_office_line(self):
        printed = ["  discard:   bale revert X", "bale retry 'r.tar.gz'", "bale retry r.tar.gz --sid X",
                   "then `bale relay X -`", "(`bale unlock` and repack)", "bale amend-checkpoint X", "bale handoff r"]
        self.assertEqual(ob.office_words(printed, self.PLAN), [
            "bale retry -> office land 2026-11-03-fix-login-001 --response FILE",
            "bale relay -> office relay 2026-11-03-fix-login-001 FILE",
            "bale revert -> no office line: type it in /w/alpha",
            "bale unlock -> office withdraw 2026-11-03-fix-login-001, for a session never worked; office land "
            "2026-11-03-fix-login-001, for a sitting",
            "bale handoff -> " + ob.handoff_line(self.PLAN),
            "bale amend-checkpoint -> no office line: type it in /w/alpha"])
        self.assertEqual(ob.office_words(["[bale] applied", "nothing to do"], self.PLAN), [])

    def test_a_clarifications_next_line_is_office_relay(self):
        _, nxt = ob.outcome_words(self.PLAN, "clarification")
        self.assertEqual(nxt, "office relay 2026-11-03-fix-login-001 ANSWER-FILE, with the planner's answer saved "
                              "here as ANSWER-FILE (office relay carries it to bale relay in /w/alpha)")
        hosted = dict(self.PLAN, place={"path": "/srv/alpha", "host": "box"})
        self.assertIn("bale relay in /srv/alpha, through box's shell)", ob.outcome_words(hosted, "clarification")[1])
        self.assertNotIn("(cd ", nxt)


class TestTheLandingsOfficeWords(LandCase):
    def test_a_hold_says_bales_verbs_in_office_words_before_the_offices_own(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "broken\n"}, validation="fail")
        proc = self.run_office("land", check=1)
        out = proc.stdout
        self.assertIn(f"In office words:\n  bale retry -> office land {sid} --response FILE\n  bale revert -> no office "
                      f"line: type it in {self.proj}", out.replace(os.path.realpath(self.proj), str(self.proj)))
        self.assertLess(out.index("In office words:"), out.index("Held: bale held"))
        self.assertLess(out.index("bale retry"), out.index("In office words:"), "bale's own lines first, as printed")

    def test_a_clarification_ends_on_office_relay_and_its_tail_says_it(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, kind="clarification")
        proc = self.run_office("land", check=0)
        out = proc.stdout
        self.assertIn(f"Next: office relay {sid} ANSWER-FILE, with the planner's answer saved here as ANSWER-FILE "
                      "(office relay carries it to bale relay in ", out)
        self.assertNotIn(f"&& bale relay {sid}", out)
        whole = out[out.index("For the planner, whole:"):]
        tail = whole[whole.index(f"--- OFFICE land {sid} ---"):whole.index("--- OFFICE END ---")]
        self.assertIn(f"folder: 1, fix-login (desk/{self.name}, open)\nanswer: office relay {sid} ANSWER-FILE\n", tail)
        self.assertNotIn("next:", tail)
        self.assertLess(whole.index("BALE EXCHANGE END"), whole.index("--- OFFICE land"),
                        "bale's block whole, the tail after its END marker")

    def test_the_doctrine_says_it_past_the_banner(self):
        doctrine = (REPO / "doctrine/OFFICE.md").read_text().splitlines()
        self.assertTrue(doctrine[298].startswith("> **PAST THE CORE.**"))
        past = flat("\n".join(doctrine[299:]))
        self.assertIn("Every line the office prints for the occupant to type is an office line (0.44.0)", past)
        self.assertIn("bale's own lines are the record, kept where bale printed them", past)
        self.assertNotIn("0.44.0", flat("\n".join(doctrine[:299])))


# --- 4. a bailout's line (left: office start --handoff is proposed) --------------------------------

class TestABailoutsLine(unittest.TestCase):
    def test_the_line_says_there_is_no_office_line_yet_and_where_bales_goes(self):
        plan = dict(TestOfficeWords.PLAN)
        words, nxt = ob.outcome_words(plan, "bailout")
        self.assertIn("Bailed: the worker handed 2026-11-03-fix-login-001 off; nothing landed.", words)
        self.assertEqual(nxt, "no office line yet: type bale handoff 'response-x.tar.gz' in /w/alpha; it packs the fresh "
                              "session the handoff asks for, and office sessions 3 SID records it in the folder")
        self.assertNotIn("bale printed the handoff step above", words)


# --- 5. one copy runs a probe -----------------------------------------------------------------------

class TestTheRunLine(unittest.TestCase):
    def test_the_line_and_its_parts(self):
        header = ["# PROBE x: what.", "# office: probe 21 --project alpha --sid 2026-11-03-x-001", "# Read-only."]
        line, got = op.run_line(header)
        self.assertEqual(line, "# office: probe 21 --project alpha --sid 2026-11-03-x-001")
        self.assertEqual(got, {"folder": "21", "project": "alpha", "sid": "2026-11-03-x-001"})
        self.assertEqual(op.run_line(["# office: probe plan-it"])[1], {"folder": "plan-it", "project": None, "sid": None})
        self.assertEqual(op.run_line(["# PROBE x: what.", "# Read-only."]), (None, None))

    def test_a_line_that_does_not_read_is_refused_by_name(self):
        for bad in ("# office: probe", "# office: probe 21 --yes", "# office: probe 21 --sid a --sid b"):
            with self.assertRaises(op.ProbeError) as got:
                op.run_line([bad])
            self.assertIn("run line", got.exception.lines[0])

    def test_the_r_key_shows_only_while_a_probe_could_run(self):
        _, menu = hs.render_page([], [], 0, probe_ready=True)
        self.assertIn(("r", "office", ["probe"]), menu)
        lines, menu = hs.render_page([], [], 0)
        self.assertNotIn("r", [k for k, _, _ in menu])
        lines, _ = hs.render_page([], [], 0, probe_ready=True)
        self.assertIn("[r] run the probe on the clipboard", "\n".join(lines))


class TestOneCopyRunsAProbe(SittingCase):
    def header(self, line):
        return ["# PROBE fix-login: what the machine says, in one line.", line, "# Why: the session needs it.",
                "# Read-only: writes nothing anywhere; stdout is the only output.",
                "# Bound: probe() gets 10 seconds of wall clock."]

    def probe(self, line, *more, check=0):
        block = self.e.tmp / "probe.sh"
        block.write_text(probe_block(header=self.header(line)))
        return self.e.run("probe", "-", "--yes", *more, cwd=self.root, check=check, input=block.read_text())

    def test_the_line_says_the_folder_and_the_project(self):
        proc = self.probe(f"# office: probe {self.number()} --project alpha")
        self.assertIn(f"from the block: probe {self.number()} --project alpha", proc.stderr)
        self.assertIn(f"# office: probe {self.number()} --project alpha", proc.stderr, "shown with the header")
        self.assertIn("=== PROBE END fix-login ===", proc.stdout)
        self.assertIn(f"for {self.sit} (desk/{self.plan}, the read-only sitting open in the office)", proc.stderr)

    def test_a_flag_typed_wins_and_a_part_that_is_not_there_is_read_as_without_it(self):
        proc = self.probe(f"# office: probe {self.number()} --project alpha", "--project", "office")
        self.assertIn("--project office, as typed, stands over the block's --project alpha", proc.stderr)
        self.assertIn("runs in the office root", proc.stderr)
        proc = self.probe("# office: probe 99 --project alpha --sid 2026-11-03-not-open-001")
        self.assertIn("the block's run line names folder 99, which the desk does not hold; the folder is read as "
                      "without it", proc.stderr)
        self.assertIn(f"desk/{self.plan} records the one session open", proc.stderr)
        self.assertIn("names --sid 2026-11-03-not-open-001, which is not a session", proc.stderr)
        self.assertIn("the session is read as without it", proc.stderr)
        self.assertIn("=== PROBE END fix-login ===", proc.stdout)
        # A project the office does not scope is read as without it: here
        # the lane names none, so piped it is the question's refusal.
        proc = self.probe(f"# office: probe {self.number()} --project gamma", check=1)
        self.assertIn("names --project gamma, which this office does not scope; where it runs is read as without it",
                      proc.stderr)
        self.assertIn("say where the probe runs: --project NAME", proc.stderr)

    def test_the_home_screen_offers_r_while_the_sitting_is_out(self):
        self.downloads.mkdir(exist_ok=True)
        _, menu = home(self)
        self.assertIn(["r", "office", "probe"], menu)


# --- 6. the standing reaches the office on its own ---------------------------------------------------

class TestTheStandingAlone(SittingCase):
    def test_a_standing_and_no_probe_is_filed_and_nothing_runs(self):
        proc = self.e.run("probe", "-", cwd=self.root, check=0, input="```\n" + standing(self.sit) + "```\n")
        self.assertIn(f"filed {self.sit}'s standing on desk/{self.plan}, from stdin", proc.stderr)
        self.assertIn(f"stdin holds a standing and no probe: filed on desk/{self.plan}; nothing to run", proc.stderr)
        self.assertTrue(self.page.read_text().endswith(standing(self.sit)))
        self.assertNotIn("PROBE", proc.stdout)

    def test_the_standing_key_shows_from_the_first_turn(self):
        self.downloads.mkdir(exist_ok=True)
        self.assertFalse(self.page.exists())
        out, menu = home(self)
        self.assertIn("stands now, from the sitting's last standing block on the clipboard", out)
        self.assertIn(["standing", self.number()], [r[2:] for r in menu])


class TestTheStandingFromTheClipboard(SittingCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_bare_office_probe_files_the_standing_on_the_clipboard(self):
        clip = self.e.tmp / "clipboard.txt"
        clip.write_text(standing(self.sit))
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'paste_command = "cat {clip}"\n')
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "probe"], self.root, self.e.env, [])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"the clipboard holds a standing and no probe: filed on desk/{self.plan}; nothing to run",
                      flat(seen))
        self.assertNotIn("Run it?", seen)


# --- 7. the planner's half ------------------------------------------------------------------------

class TestThePlannersHalf(unittest.TestCase):
    def test_the_two_briefs_say_what_the_sitting_owes(self):
        for name in ("sitting-brief.md", "prep-brief.md"):
            text = flat((REPO / "templates" / name).read_text())
            owes = text[text.index("## What the sitting owes"):]
            self.assertIn("is an office line", owes, name)
            self.assertIn("never bale's verbs", owes, name)
            self.assertIn("# office: probe", owes, name)
            self.assertIn("--- RIDES PATH ---", owes, name)
        self.assertIn("never `bale open`", flat((REPO / "templates/sitting-brief.md").read_text()))

    def test_the_doctrines_marker_set_gains_rides_and_the_run_line(self):
        doctrine = (REPO / "doctrine/OFFICE.md").read_text().splitlines()
        past = "\n".join(doctrine[299:])
        self.assertIn("  --- RIDES lib/alpha.py ---\n  --- RIDES docs/* ---\n  --- RIDES none ---\n", past)
        self.assertIn("  # office: probe 21 --project alpha --sid 2026-10-27-alpha-plan-sitting-001\n", past)
        self.assertEqual(op.RUN_LINE_PREFIX, "# office: probe ")
        self.assertEqual(oh.RIDES_MARK_PREFIX, "--- RIDES ")


if __name__ == "__main__":
    unittest.main()
