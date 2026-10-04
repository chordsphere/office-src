"""Tests for the second trip (0.9.0): the five frictions the first real round
trip through office start and office land found, and the install that did
not move when 0.8.0 landed.

1. A project's ride-alongs ride by default; on a terminal office start shows
   them and lets one stay home for a session (--leave-out, --no-rides), and
   the doctrine rides once when the packed tree carries its own.
2. office start surveys the machine again before every pack.
3. office land SID ends a read-only sitting the office sent out: bale
   unlock, and an `ended` line in the folder's History.
4. For a bundle the office can read, where defaults to the one place whose
   tree holds every path the bundle names; paths no one place holds are
   refused before bale runs.
5. A timezone that does not resolve: the warning, office status and the
   walk-in name the remedy.
6. office land ends by saying what became of each after-land action, and
   office status says when the install is behind its source.

bale is never needed: the fake bale of tests/test_land.py serves every
call, unlock included, from the probes' captured lines. Run with the rest:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import INSTALL_PARTS, REPO, Env, h  # noqa: E402
from test_start import git_repo, on_a_terminal  # noqa: E402
from test_land import FIXTURES, LandCase, bundle_file, response_tarball  # noqa: E402

import office_bale as ob  # noqa: E402

UNLOCK_FIXTURES = FIXTURES / "unlock"
UNLOCK_PROBE = "2026-10-04-friction-second-trip-001"
CONSUMPTION = REPO / "share" / "bale-consumption.toml"
VERSION = (REPO / "VERSION").read_text().strip()


def tray_of(stdout):
    return pathlib.Path(re.search(r"^Out tray: (.*)$", stdout, re.M).group(1))


def sid_of(stdout):
    return re.search(r"^Packed (\S+) for ", stdout, re.M).group(1)


# --- the captured unlocks ---------------------------------------------------------------

class TestUnlockFixtures(unittest.TestCase):
    def setUp(self):
        self.data = tomllib.loads(CONSUMPTION.read_text())

    def fixture(self, label):
        return json.loads((UNLOCK_FIXTURES / f"{label}.json").read_text(encoding="utf-8"))

    def test_every_line_is_the_one_the_probe_captured(self):
        files = sorted(UNLOCK_FIXTURES.glob("*.json"))
        self.assertEqual(len(files), 17)
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual(len(rec["stdout"]), len(rec["stdout_sha256"]), f.name)
            for line, sha in zip(rec["stdout"], rec["stdout_sha256"]):
                self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), sha, f.name)
            self.assertIn(f"probe of session {UNLOCK_PROBE}", rec["captured"], f.name)

    def test_the_declared_keys_are_in_the_captured_lines(self):
        spec = self.data["surfaces"]["unlock"]
        for label in ("unlock-ro-json", "unlock-ro-dirty", "unlock-ro-one-of-two", "ptyunlock-ro-json"):
            line = json.loads(self.fixture(label)["stdout"][-1])
            self.assertEqual(line["outcome"], spec["outcome"], label)
            for key in spec["keys"]:
                obj = line
                for part in key.split("."):
                    self.assertIn(part, obj, f"{label}: {key}")
                    obj = obj[part]
            self.assertEqual(line["closure_reason"], "closed-read-only", label)
            self.assertEqual(line["sweep"]["status"], "committed", label)

    def test_the_office_passes_unlock_nothing_but_the_sid(self):
        """No --reason (bale infers closed-read-only from the empty scope),
        no --force; and unlock asks nothing, so it runs with stdin closed."""
        spec = self.data["surfaces"]["unlock"]
        self.assertEqual(spec["argv"], ["unlock", "{sid}", "--json"])
        for group in ("optional", "repeated", "switches", "interactive"):
            self.assertNotIn(group, spec)
        self.assertEqual(ob.Consumption().argv("unlock", sid="2026-10-04-x-001"),
                         ["unlock", "2026-10-04-x-001", "--json"])
        pty = self.fixture("ptyunlock-ro-json")
        self.assertNotIn("sent", [e[0] for e in pty["events"]])
        help_text = " ".join(json.loads((FIXTURES / "land" / "help-unlock.json").read_text())["stdout"])
        self.assertIn("'closed-read-only' when the", help_text)

    def test_a_second_unlock_is_refused_on_stderr(self):
        again = self.fixture("unlock-ro-again")
        self.assertEqual((again["exit"], again["stdout"]), (1, []))
        self.assertIn("is not open; nothing to unlock", again["stderr"][-1])


# --- 3. ending a sitting ------------------------------------------------------------------

class TestEndASitting(LandCase):
    def test_land_ends_a_sitting_the_office_sent_out(self):
        started = self.run_office("start", "fix-login", "--in-office", "--read-only", "--goal", "Plan the fix", check=0)
        sid = sid_of(started.stdout)
        self.assertIn(f"A read-only sitting lands nothing; when it is over: office land {sid} ends it", started.stdout)
        self.assertNotIn("When the response comes back", started.stdout)
        walk = self.e.run(cwd=self.root, check=0).stdout
        self.assertIn(f"{sid} read-only, opened", walk)
        self.assertIn(f"-> {self.folder} (office land {sid} when the sitting is over)", walk)
        self.assertNotIn(sid, walk.strip().splitlines()[-1], "the Next line never names a sitting")
        proc = self.run_office("land", sid, "--ratified", check=0)
        self.assertIn(f"Ended: the sitting {sid} is closed in this office; it landed nothing, by design.",
                      proc.stdout)
        self.assertIn("closing a folder is yours (office close FOLDER)", proc.stdout)
        self.assertIn("a sitting lands nothing, so nothing is ratified", proc.stderr)
        self.assertIn(f"bale closed {sid} in this office (closed-read-only); its sweep: committed 1 file(s)",
                      proc.stderr)
        (cwd, argv, tty), = self.fake.calls_of("unlock")
        self.assertEqual((cwd, argv, tty), (os.path.realpath(self.root), ["unlock", sid, "--json"], False))
        self.assertEqual(self.fake.calls_of("apply"), [])
        md = self.folder_md()
        self.assertRegex(md, rf"\n- \d{{4}}-\d{{2}}-\d{{2}} ended: {sid}, a read-only sitting, closed by office land\n")
        self.assertIn("- status: open", md)
        self.assertNotIn("ratified", md)
        self.assertEqual(self.subjects(2), [f"office land: {sid} ended in {self.name}",
                                            f"[bale sweep {sid}] closed-read-only"])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertNotIn(sid, self.e.run(cwd=self.root, check=0).stdout)
        self.assertIn("every status agrees with its History", self.run_office("status", check=0).stdout)

    def test_by_its_folder_and_on_a_project(self):
        sid = self.start("fix-login", "--on", "alpha", "--read-only", "--goal", "Read alpha")
        proc = self.run_office("land", "folder 1", check=0)
        self.assertIn(f"Ended: the sitting {sid} is closed in alpha", proc.stdout)
        (cwd, _, _), = self.fake.calls_of("unlock")
        self.assertEqual(cwd, os.path.realpath(self.proj))
        self.assertFalse((self.proj / "AFTER-LAND-RAN").exists(), "a sitting runs no after-land action")
        self.assertIn(f"ended: {sid}", self.folder_md())

    def test_a_response_for_a_sitting_is_refused(self):
        sid = self.start("fix-login", "--in-office", "--read-only", "--goal", "g")
        path = response_tarball(self.downloads, sid, {"notes.md": "x\n"})
        proc = self.run_office("land", str(path), check=1)
        self.assertIn("it lands nothing, so there is no response to land", proc.stderr)
        self.assertEqual(self.fake.calls_of("unlock"), [])

    def test_a_sitting_no_folder_records_is_not_the_offices(self):
        sid = self.start("fix-login", "--on", "alpha", "--read-only", "--goal", "g")
        md = self.root / self.folder / "folder.md"
        md.write_text(md.read_text().replace(f"- {sid}\n", ""))
        self.e.git(self.root, "commit", "-qam", "the record gone, for the test")
        proc = self.run_office("land", sid, check=1)
        self.assertIn("no folder records, so it is not a sitting the office sent out", proc.stderr)
        self.assertIn(f"bale unlock {sid}, in {self.proj}", proc.stderr)
        self.assertEqual(self.fake.calls_of("unlock"), [])
        walk = self.e.run(cwd=self.root, check=0).stdout
        self.assertIn(f"{sid} read-only, opened", walk)
        self.assertNotIn(f"office land {sid}", walk)

    def test_bales_refusal_is_said_and_nothing_is_written(self):
        sid = self.start("fix-login", "--in-office", "--read-only", "--goal", "g")
        before = self.folder_md()
        proc = self.run_office("land", sid, extra={"FAKE_BALE_UNLOCK_FAILS": sid}, check=1)
        self.assertIn(f"bale unlock {sid} did not end the sitting", proc.stderr)
        self.assertIn("refused for the test", proc.stderr)
        self.assertEqual(self.folder_md(), before)
        self.assertTrue(self.fake.is_open(self.root, sid))


# --- 6. after land, said last; the install against its source --------------------------------

class TestAfterLandSaysHowEachWent(LandCase):
    def land(self, check=0):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        return self.run_office("land", check=check)

    def test_each_action_ran_is_the_last_thing_said(self):
        proc = self.land()
        self.assertTrue(proc.stdout.rstrip().endswith(
            f"After land, in {self.proj}:\n  ran (exit 0): touch AFTER-LAND-RAN"), proc.stdout)

    def test_a_failure_names_what_did_not_run_and_the_rerun(self):
        h.set_declarations(self.root / "floor-plan/manifest.toml", "alpha", None, ["false", "touch LATER"])
        self.e.git(self.root, "commit", "-qam", "declare")
        proc = self.land(check=1)
        tail = proc.stdout[proc.stdout.index("After land, in"):]
        self.assertIn("  FAILED (exit 1): false\n", tail)
        self.assertIn("  not run: touch LATER\n", tail)
        self.assertIn(f"  rerun from the failed one: (cd '{self.proj}' && false && touch LATER)\n", tail)

    def test_none_declared_is_said_not_skipped_in_silence(self):
        self.run_office("projects", "set", "alpha", "--no-after-land", check=0)
        proc = self.land()
        self.assertIn("alpha declares no after-land action, so nothing ran", proc.stderr)
        self.assertTrue(proc.stdout.rstrip().endswith("none: alpha declares no after-land action"), proc.stdout)


class TestInstallAgainstItsSource(unittest.TestCase):
    """install.sh stamps INSTALLED with the commit it installed; office
    status compares it with the working copy's HEAD."""

    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init("home")

    def test_a_working_copy_has_no_stamp(self):
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn("source:     none recorded (no INSTALLED stamp", out)

    def test_level_then_behind_with_the_line_that_brings_it_level(self):
        src = self.e.tmp / "office-src"
        src.mkdir()
        for part in INSTALL_PARTS + ("install.sh", "README.md", "RELEASES.md"):
            (shutil.copytree if (REPO / part).is_dir() else shutil.copy2)(REPO / part, src / part)
        for junk in src.rglob("__pycache__"):
            shutil.rmtree(junk)
        self.e.git(src, "init", "-q")
        self.e.git(src, "add", "-A")
        self.e.git(src, "commit", "-qm", "the source")
        inst = self.e.tmp / "inst"
        p = subprocess.run(["bash", str(src / "install.sh"), "--prefix", str(inst), "--no-link"], env=self.e.env,
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(p.returncode, 0, p.stderr)
        office = inst / "bin" / "office"
        commit = self.e.git(src, "rev-parse", "--short", "HEAD").strip()
        out = self.e.run("status", cwd=self.root, bin_path=office, check=0).stdout
        self.assertIn(f"source:     {src} at {commit}, as installed\n", out)
        (src / "VERSION").write_text("9.9.9\n")
        self.e.git(src, "commit", "-qam", "a release that was never installed")
        now = self.e.git(src, "rev-parse", "--short", "HEAD").strip()
        out = self.e.run("status", cwd=self.root, bin_path=office, check=0).stdout
        self.assertIn(f"source:     BEHIND: the install is {commit}, and {src} is now at {now} (office-src 9.9.9); "
                      f"(cd '{src}' && ./install.sh) brings the install level\n", out)


# --- 1. what rides, and the doctrine once ---------------------------------------------------

class RideCase(LandCase):
    def setUp(self):
        super().setUp()
        self.notes = git_repo(self.e.tmp / "notes", {"blueprints/plan.md": "a plan\n" * 400, "other.md": "o\n"})
        self.ride = str(self.notes / "blueprints")
        self.run_office("projects", "set", "alpha", "--ride", self.ride, check=0)


class TestWhatRides(RideCase):
    def test_piped_everything_declared_rides(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", check=0)
        self.assertIn(f"rides with alpha ({self.notes}: blueprints)", proc.stdout)
        self.assertIn("context-notes.tar.gz", [p.name for p in tray_of(proc.stdout).iterdir()])

    def test_leave_out_keeps_one_home_this_once(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--leave-out", self.ride + "/",
                               check=0)
        self.assertIn(f"(left out of this session: {self.ride}, which rides with alpha as declared)", proc.stdout)
        self.assertNotIn("context-notes.tar.gz", [p.name for p in tray_of(proc.stdout).iterdir()])
        self.assertIn(self.ride, self.run_office("projects", check=0).stdout, "the declaration is unchanged")

    def test_no_rides_and_a_name_that_rides_nowhere(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--no-rides", check=0)
        self.assertIn("left out of this session", proc.stdout)
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g2", "--leave-out",
                               str(self.notes / "other.md"), check=1)
        self.assertIn("not one of what rides with alpha", proc.stderr)
        self.assertIn("--no-rides leaves every ride-along out",
                      self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g3", "--no-rides",
                                      "--leave-out", self.ride, check=1).stderr)

    def test_a_bundle_may_leave_one_out_too(self):
        bundle = bundle_file(self.e.tmp / "b", "2026-10-05-fix", ["Fix it", "--slug", "fix-b", "--write", "src",
                                                                  "--constraint", ob.PROJECT_CONSTRAINT])
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", str(bundle), "--no-rides", check=0)
        self.assertIn("left out of this session", proc.stdout)

    def test_on_a_terminal_it_shows_what_rides_and_asks(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "fix-login", "--on", "alpha",
                                          "--goal", "g"], self.root, self.e.env, [
            (b"Which ride with this session: all, none, or the numbers to leave out (--leave-out PATH, --no-rides) "
             b"[all]:", "?"),
            (b"  Each declared ride-along is packed", "7"),
            (b"all, none, or numbers from the list above", "1"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"1. {self.ride}  (", seen)
        self.assertIn("left out of this session", seen)


class TestTheDoctrineRidesOnce(LandCase):
    def give_alpha_the_doctrine(self, change=False):
        shutil.copytree(REPO / "doctrine", self.proj / "doctrine",
                        ignore=shutil.ignore_patterns("__pycache__"))
        if change:
            with (self.proj / "doctrine" / "OFFICE.md").open("a") as f:
                f.write("\nA line the install does not have.\n")
        self.e.git(self.proj, "add", "-A")
        self.e.git(self.proj, "commit", "-qm", "the doctrine, as office-src's tree carries it")

    def tray(self, *extra):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", *extra, check=0)
        return proc, sorted(p.name for p in tray_of(proc.stdout).iterdir())

    def test_the_same_doctrine_rides_inside_the_tree_only(self):
        self.give_alpha_the_doctrine()
        proc, names = self.tray()
        self.assertEqual([n for n in names if "doctrine" in n], [])
        self.assertIn(f"(the doctrine rides once, inside alpha's tree at doctrine/: it is the same as the install's, "
                      f"office-src {VERSION})", proc.stdout)

    def test_a_different_doctrine_gets_the_installs_beside_it_named_so(self):
        self.give_alpha_the_doctrine(change=True)
        proc, names = self.tray()
        self.assertIn("context-doctrine-install.tar.gz", names)
        self.assertIn("the doctrine the office runs on, from the install", proc.stdout)
        self.assertIn("alpha's tree carries a different doctrine/ of its own", proc.stdout)

    def test_a_pack_that_does_not_ship_the_trees_doctrine_carries_the_installs(self):
        self.give_alpha_the_doctrine()
        _, names = self.tray("--include", "src")
        self.assertIn("context-doctrine.tar.gz", names)
        # OFFICE.md alone is not the doctrine: its checks would be missing.
        _, names = self.tray("--include", "src", "--include", "doctrine/OFFICE.md", "--write", "docs")
        self.assertIn("context-doctrine.tar.gz", names)

    def test_the_comparison_ignores_caches(self):
        a, b = self.e.tmp / "a", self.e.tmp / "b"
        for d in (a, b):
            (d / "checks").mkdir(parents=True)
            (d / "OFFICE.md").write_text("same\n")
        (b / "__pycache__").mkdir()
        (b / "__pycache__" / "x.pyc").write_bytes(b"\0")
        self.assertEqual(ob.doctrine_files(a), ob.doctrine_files(b))
        self.assertTrue(ob.ships("doctrine/OFFICE.md", None))
        self.assertTrue(ob.ships("doctrine/OFFICE.md", ["doctrine"]))
        self.assertFalse(ob.ships("doctrine/OFFICE.md", ["src"]))
        self.assertFalse(ob.ships("doctrine/OFFICE.md", None, ["doctrine"]))


# --- 2. the survey before every pack -------------------------------------------------------

class TestSurveyBeforeEveryPack(LandCase):
    def age_the_survey(self, version=None):
        page = self.root / "floor-plan" / "survey.md"
        text = re.sub(r"^- surveyed_at: .*$", "- surveyed_at: 2026-01-01T00:00:00Z", page.read_text(), flags=re.M)
        if version:
            text = re.sub(r"(## office-src\n\n(?:- .*\n)*?- version: ).*", rf"\g<1>{version}", text)
        page.write_text(text)
        self.e.git(self.root, "commit", "-qam", "an old survey, for the test")
        return page

    def test_start_surveys_again_and_commits_the_page_alone(self):
        page = self.age_the_survey(version="0.4.0")
        status = self.run_office("status", check=0).stdout
        self.assertRegex(status, rf"survey:     2026-01-01T00:00:00Z \(\d+ days old; records office-src 0.4.0, not the "
                                 rf"installed {re.escape(VERSION)}\)")
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        self.assertNotIn("2026-01-01T00:00:00Z", page.read_text())
        log = self.e.git(self.root, "log", "--format=%s", "-3").splitlines()
        self.assertEqual(log[0], f"office sessions: {sid} in {self.name}")
        self.assertRegex(log[1], r"^office start: survey: \d+ facts changed$")
        commit = self.e.git(self.root, "log", "-1", "--format=%H", "--grep=office start: survey").strip()
        self.assertEqual(self.e.git(self.root, "show", "--name-only", "--format=", commit).split(),
                         ["floor-plan/survey.md"])
        self.assertIn(f"records office-src {VERSION}, as installed", self.run_office("status", check=0).stdout)

    def test_a_refused_start_commits_no_survey(self):
        self.age_the_survey()
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--write", "nosuch", check=1)
        self.assertIn("--write nosuch: no such path", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_an_open_session_holding_the_page_keeps_it_as_it_is(self):
        self.start("fix-login", "--in-office", "--goal", "Rework the floor plan", "--write", "floor-plan")
        page = self.age_the_survey()
        proc = self.run_office("start", "fix-login", "--in-office", "--read-only", "--goal", "g", check=0)
        self.assertIn("an open session holds floor-plan/survey.md (the one-writer rule), so office start leaves the "
                      "survey as it is: 2026-01-01T00:00:00Z", proc.stderr)
        self.assertIn("2026-01-01T00:00:00Z", page.read_text())


# --- 4. where, from the bundle ---------------------------------------------------------------

class TestWhereFromTheBundle(LandCase):
    def office_bundle(self):
        return bundle_file(self.e.tmp / "b", "2026-10-05-plan", ["Plan from a bundle", "--slug", "plan-b",
                                                                 "--include", "desk", "--include", "notepad",
                                                                 "--read-only"])

    def test_the_default_is_the_place_holding_every_path(self):
        where, why = ob.bundle_where(self.root, self.office_bundle(), "alpha")
        self.assertEqual(where, "office")
        self.assertIn("every path the bundle names (desk, notepad) is in the office's tree", why)
        alpha = bundle_file(self.e.tmp / "b", "2026-10-05-a", ["Fix", "--slug", "a", "--write", "src"])
        self.assertEqual(ob.bundle_where(self.root, alpha, None)[0], "alpha")
        anywhere = bundle_file(self.e.tmp / "b", "2026-10-05-any", ["Read", "--slug", "any", "--read-only"])
        where, why = ob.bundle_where(self.root, anywhere, "alpha")
        self.assertEqual(where, "alpha")
        self.assertIn("because the folder's lane names it", why)
        self.assertEqual(ob.bundle_where(self.root, anywhere, None)[0], "office")
        self.assertIsNone(ob.bundle_where(self.root, "2026-10-05-not-here.bale-bundle", "alpha"))

    def test_paths_no_one_place_holds_are_refused_naming_each(self):
        split = bundle_file(self.e.tmp / "b", "2026-10-05-split", ["Both", "--slug", "s", "--include", "desk",
                                                                   "--write", "src"])
        with self.assertRaises(ob.StartError) as cm:
            ob.bundle_where(self.root, split, "alpha")
        text = "\n".join(cm.exception.lines)
        self.assertIn("  desk: in the office", text)
        self.assertIn("  src: in alpha", text)
        nowhere = bundle_file(self.e.tmp / "b", "2026-10-05-none", ["None", "--slug", "n", "--include", "nosuch"])
        with self.assertRaises(ob.StartError) as cm:
            ob.bundle_where(self.root, nowhere, "alpha")
        text = "\n".join(cm.exception.lines)
        self.assertIn("  nosuch: in nowhere the office can see", text)
        self.assertIn("nosuch exists in neither the office nor any project it scopes", text)

    def test_sent_where_its_paths_are_not_it_is_refused_before_bale(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", str(self.office_bundle()), check=1)
        self.assertIn("names paths that are not in alpha's tree, so it cannot open there; nothing ran", proc.stderr)
        self.assertIn("desk: in the office", proc.stderr)
        self.assertEqual(self.fake.calls_of("open"), [])
        self.assertNotIn("\n- 20", (self.root / self.folder / "folder.md").read_text().split("## Sessions")[1]
                         .split("## ")[0])

    def test_on_a_terminal_a_plain_return_opens_it_where_its_paths_are(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "fix-login", "--bundle",
                                          str(self.office_bundle())], self.root, self.e.env, [
            (b"(--in-office or --on PROJECT) [office]:", "?"),
            (b"  office: the session works in this office", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("The default is office because every path the bundle names (desk, notepad) is in the office's "
                      "tree", re.sub(r"\s+", " ", seen.replace("\r", "")))
        (cwd, _, _), = self.fake.calls_of("open")
        self.assertEqual(cwd, os.path.realpath(self.root))


# --- 5. a timezone that does not resolve -------------------------------------------------------

class TestATimezoneThatDoesNotResolve(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init("home")
        self.e.found(self.root)
        manifest = self.root / "floor-plan" / "manifest.toml"
        text, n = re.subn(r'^timezone = ".*"$', 'timezone = "America/Indianapolis"', manifest.read_text(), flags=re.M)
        self.assertEqual(n, 1)
        manifest.write_text(text)
        self.e.git(self.root, "commit", "-qam", "the occupant's zone, its legacy name")
        self.zones = self.e.tmp / "zoneinfo"
        (self.zones / "America" / "Indiana").mkdir(parents=True)
        (self.zones / "America" / "Indiana" / "Indianapolis").write_bytes(b"TZif fake")
        (self.zones / "posix" / "America" / "Indiana").mkdir(parents=True)
        (self.zones / "posix" / "America" / "Indiana" / "Indianapolis").write_bytes(b"TZif fake")
        self.e.env["TZDIR"] = str(self.zones)

    def test_the_warning_names_the_canonical_spelling(self):
        proc = self.e.run("note", "a line", cwd=self.root, check=0)
        self.assertIn(f"the floor plan's timezone 'America/Indianapolis' is not in {self.zones}, so the office runs on "
                      "UTC; this zone database spells it America/Indiana/Indianapolis:", proc.stderr)
        self.assertIn("tzdata-legacy on Debian and Ubuntu", proc.stderr)

    def test_status_reports_it_as_a_problem_with_the_remedy(self):
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn(f"timezone:   PROBLEM: the floor plan names America/Indianapolis, which is not in {self.zones}, "
                      "so the office runs on UTC\n  this zone database spells it America/Indiana/Indianapolis:", out)

    def test_the_walk_in_says_which_zone_it_uses(self):
        out = self.e.run(cwd=self.root, check=0).stdout
        self.assertRegex(out.splitlines()[1], r"^\w+day \d{4}-\d{2}-\d{2}, \d\d:\d\d UTC \(the floor plan's "
                                              r"America/Indianapolis does not resolve here; office status says what "
                                              r"fixes it\)\. ")

    def test_no_zone_of_that_name_names_the_package(self):
        shutil.rmtree(self.zones / "America")
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn("no zone here is named Indianapolis: install the package that keeps the legacy names "
                      "(tzdata-legacy on Debian and Ubuntu)", out)

    def test_a_zone_that_resolves_is_quiet(self):
        (self.zones / "America" / "Indianapolis").write_bytes(b"TZif fake")
        self.assertIn("timezone:   America/Indianapolis\n", self.e.run("status", cwd=self.root, check=0).stdout)
        self.assertNotIn("timezone", self.e.run("note", "a line", cwd=self.root, check=0).stderr)


if __name__ == "__main__":
    unittest.main()
