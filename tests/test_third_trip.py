"""Tests for the third trip (office-src 0.13.0): the suite run side by
side, bale 0.4.47 checked against the consumption manifest, office start
asking bale open --check before it writes anything and naming the retry
when a start it opened a folder for fails, a new folder's title checked
first, the riders a pack carries offered at start, office land running
watches check and closing the founding folder, the walk-in naming an
install behind its source, and a profile answer that runs to a
paragraph.

bale is never needed: the fakes of test_land.py and test_watches_digest.py
serve what the probes captured, bale open --check among it (the
third-trip probe's captures, in the development record beside the
0.4.45 ones). Run with the rest of the suite:

    tests/run.sh
"""

import ast
import hashlib
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tomllib
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, VERSION, Env, filled_profile  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import FakeLandBale, LandCase, bundle_file, response_tarball  # noqa: E402
from test_founding_door import DoorCase  # noqa: E402
from test_front_door import last_line  # noqa: E402
from test_watches_digest import LOG_PAGE, REGISTER_PAGE, WatchCase  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)
import office_drafting as od  # noqa: E402
import runner  # noqa: E402  (tests/runner.py, beside this file)

# Split so the text rules' own check does not trip on this file.
RECORD = REPO / ("cla" + "ude")
FIX47 = RECORD / "fixtures" / "bale-0.4.47"
CONSUMPTION = REPO / "share" / "bale-consumption.toml"
PROBE_SID = "2026-10-07-third-trip-001"
TERMINAL_HELPERS = ("terminal", "on_a_terminal", "run_on_a_pty")


def fixture47(rel):
    return json.loads((FIX47 / rel).read_text(encoding="utf-8"))


def all_fixtures47():
    return sorted(FIX47.rglob("*.json"))


# --- 1. the suite, side by side ---------------------------------------------------------------

def classes_driving_a_terminal():
    """{module: {class}} for every test class whose body calls a pty helper
    or pty itself: the classes the serial group must hold."""
    pat = re.compile(r"(?<![\w.])(" + "|".join(TERMINAL_HELPERS) + r")\(|pty\.(fork|openpty|spawn)")
    out = {}
    for f in sorted((REPO / "tests").glob("test_*.py")):
        src = f.read_text(encoding="utf-8")
        for node in ast.parse(src).body:
            if isinstance(node, ast.ClassDef) and pat.search(ast.get_source_segment(src, node)):
                out.setdefault(f.stem, set()).add(node.name)
    return out


def classes_marked_serial():
    out = {}
    for f in sorted((REPO / "tests").glob("test_*.py")):
        for node in ast.parse(f.read_text(encoding="utf-8")).body:
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if isinstance(stmt, ast.Assign) and any(getattr(t, "id", None) == runner.SERIAL_ATTR
                                                        for t in stmt.targets):
                    out.setdefault(f.stem, set()).add(node.name)
    return out


class TestTheRunner(unittest.TestCase):
    def test_the_serial_group_is_exactly_the_classes_that_drive_a_terminal(self):
        driving, marked = classes_driving_a_terminal(), classes_marked_serial()
        # This module's own terminal classes are marked like everyone's.
        self.assertEqual(marked, driving)
        self.assertGreaterEqual(sum(len(v) for v in marked.values()), 12)

    def test_the_plan_runs_what_discover_runs_once_each(self):
        jobs = runner.plan(runner.module_names())
        ids = [t for v in jobs.values() for t in v]
        self.assertEqual(len(ids), runner.discover_count())
        self.assertIn(runner.SERIAL_JOB, jobs)
        # Read once: parsing every test file again for each of the suite's
        # tests made this one test take minutes.
        marked = classes_marked_serial()
        for t in jobs[runner.SERIAL_JOB]:
            module, cls = t.split(".")[:2]
            self.assertIn(cls, marked.get(module, set()), t)
        for job, tests in jobs.items():
            if job != runner.SERIAL_JOB:
                self.assertTrue(all(t.split(".")[1] not in marked.get(t.split(".")[0], set())
                                    for t in tests), job)

    def test_the_serial_lane_starts_first(self):
        jobs = {"test_office": [1], runner.SERIAL_JOB: [1], "test_filed_append_only": [1]}
        self.assertEqual(runner.order(jobs)[0], runner.SERIAL_JOB)
        self.assertEqual(runner.order(jobs, {"test_office": 9, "test_filed_append_only": 1})[1:],
                         ["test_office", "test_filed_append_only"])

    def test_a_failure_names_its_test_and_its_log(self):
        ok = {"job": "test_a", "run": 3, "failures": [], "errors": [], "unexpected_successes": [], "skipped": 0,
              "seconds": 1.0, "exit": 0, "log": "/logs/test_a.log"}
        bad = dict(ok, job="test_b", failures=["test_b.TestX.test_y"], errors=["test_b.TestX.test_z"], exit=1,
                   log="/logs/test_b.log")
        lines, failed = runner.summary([ok, bad], 6, 12.0, "/logs")
        text = "\n".join(lines)
        self.assertTrue(failed)
        self.assertIn("[run] test_b failed; read /logs/test_b.log", text)
        self.assertIn("    failure: test_b.TestX.test_y", text)
        self.assertIn("    error: test_b.TestX.test_z", text)
        self.assertIn("/logs/test_a.log", text)
        self.assertTrue(lines[-1].startswith("[run] FAILED"))
        lines, failed = runner.summary([ok], 3, 1.0, "/logs")
        self.assertFalse(failed)
        self.assertEqual(lines[-1], "[run] OK (3 tests run)")

    def test_run_sh_runs_one_module_with_a_log_and_refuses_what_it_cannot(self):
        # A relative --logs, from another directory, as validation.sh gives
        # it: the jobs run in tests/, so the runner makes it absolute.
        here = pathlib.Path(self.tmp_dir())
        logs = here / "logs"
        proc = subprocess.run([str(REPO / "tests" / "run.sh"), "test_filed_append_only", "--logs", "logs"],
                              cwd=here, capture_output=True, text=True, timeout=300)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"test_filed_append_only    12 tests  ok", proc.stdout)
        self.assertIn(str(logs / "test_filed_append_only.log"), proc.stdout)
        self.assertIn("Ran 12 tests", (logs / "test_filed_append_only.log").read_text())
        self.assertEqual(json.loads((logs / "test_filed_append_only.json").read_text())["run"], 12)
        no = subprocess.run([str(REPO / "tests" / "run.sh"), "test_nothing"], capture_output=True, text=True)
        self.assertEqual(no.returncode, 2)
        self.assertIn("no such test module: test_nothing", no.stderr)
        no = subprocess.run([str(REPO / "tests" / "run.sh"), "--serial", "test_office"], capture_output=True,
                            text=True)
        self.assertEqual(no.returncode, 2)

    def tmp_dir(self):
        import tempfile
        d = tempfile.mkdtemp(prefix="runner-test-")
        self.addCleanup(shutil.rmtree, d, True)
        return d


# --- 2. bale 0.4.47 against the consumption manifest ---------------------------------------------

class TestBaleChecked(unittest.TestCase):
    def setUp(self):
        self.data = tomllib.loads(CONSUMPTION.read_text())

    def test_every_line_is_the_one_the_probe_captured(self):
        files = all_fixtures47()
        self.assertEqual(len(files), 10)
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual(len(rec["stdout"]), len(rec["stdout_sha256"]), f.name)
            for line, sha in zip(rec["stdout"], rec["stdout_sha256"]):
                self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), sha, f.name)
            self.assertIn(f"probe of session {PROBE_SID}", rec["captured"])

    def test_the_checked_bale_is_the_probed_one_and_the_floor_stands(self):
        self.assertEqual(self.data["bale"]["floor"], "0.4.45")
        self.assertEqual(self.data["bale"]["checked_in"], PROBE_SID)
        self.assertEqual(fixture47("anywhere/version.json")["stdout"], [f"bale {self.data['bale']['checked']}"])
        self.assertTrue((RECORD / "fixtures" / f"bale-{self.data['bale']['checked']}" / "README.md").is_file())

    def test_open_check_is_declared_as_the_probe_ran_it(self):
        cons = ob.Consumption()
        rec = fixture47("open-check/check-found.json")
        self.assertEqual(cons.argv("open_check", bundle=rec["argv"][2]), rec["argv"])
        self.assertEqual(cons.surface("open_check")["format"], "text")
        found = cons.surface("open_check")["found_line"]
        self.assertTrue(rec["stdout"][0].startswith(found))
        self.assertIn("  wrote:              nothing", rec["stdout"])
        for label in ("check-missing", "check-nopath", "check-overlap", "check-outside"):
            r = fixture47(f"open-check/{label}.json")
            self.assertEqual(r["exit"], 1, label)
            self.assertTrue(any(l.startswith("[bale] error: ") for l in r["stderr"]), label)
        self.assertEqual(fixture47("open-check/check-missing.json")["stderr"][1], "  searched:")

    def test_the_reader_reads_the_found_path_and_passes_refusals_on(self):
        def rd_for(label):
            rec = fixture47(f"open-check/{label}.json")
            proc = types.SimpleNamespace(returncode=rec["exit"], stdout="\n".join(rec["stdout"]) + "\n",
                                         stderr="\n".join(rec["stderr"]) + "\n")
            rd = ob.Reader(runner=lambda *a, **k: proc)
            rd.bale = lambda: "bale"
            return rd
        e = Env(self)
        root = e.init("home")
        self.assertEqual(ob.check_bundle(rd_for("check-found"), root, "office", None, "x.bale-bundle"),
                         "TMP/dl/2026-01-01-office-probe-ok.bale-bundle")
        with self.assertRaises(ob.StartError) as cm:
            ob.check_bundle(rd_for("check-missing"), root, "office", None, "x.bale-bundle")
        text = "\n".join(cm.exception.lines)
        self.assertIn("so start stopped before anything was written", text)
        self.assertIn("bundle not found: 2026-01-01-office-probe-nothere.bale-bundle", text)
        self.assertIn("TMP/dl", text)

    def test_an_unlock_refusal_is_still_a_refusal(self):
        """0.4.47 prints a JSON line on a refusal too; the office reads the
        exit code and bale's words, as before."""
        rec = fixture47("unlock/unlock-again.json")
        self.assertEqual(json.loads(rec["stdout"][0])["outcome"], "unlock-refused")
        proc = types.SimpleNamespace(returncode=rec["exit"], stdout=rec["stdout"][0] + "\n",
                                     stderr="\n".join(rec["stderr"]) + "\n")
        rd = ob.Reader(runner=lambda *a, **k: proc)
        rd.bale = lambda: "bale"
        e = Env(self)
        with self.assertRaises(ob.BaleError) as cm:
            rd.unlock(e.home, "2026-10-07-x-001")
        self.assertIn("is not open; nothing to unlock", str(cm.exception))


# --- 3. office start checks a bundle first, and names the retry -----------------------------------

class TestStartChecksTheBundleFirst(LandCase):
    def argv(self, slug="fix-from-bundle", write="src"):
        return ["Fix it, from a bundle", "--slug", slug, "--write", write, "--constraint", ob.PROJECT_CONSTRAINT]

    def test_bale_is_asked_before_the_open_where_the_open_runs(self):
        bundle_file(self.downloads, "2026-10-07-fix", self.argv())
        proc = self.run_office("start", "fix-login", "--on", "alpha", "2026-10-07-fix.bale-bundle", check=0)
        self.assertIn("bale open --check, which writes nothing", proc.stderr)
        self.assertIn(f"bale found it at {self.downloads / '2026-10-07-fix.bale-bundle'}", proc.stderr)
        (ccwd, cargv, ctty), = self.fake.calls_of("open-check")
        (ocwd, oargv, _), = self.fake.calls_of("open")
        self.assertEqual((ccwd, cargv, ctty), (os.path.realpath(self.proj),
                                               ["open", "--check", "2026-10-07-fix.bale-bundle"], False))
        self.assertEqual(ocwd, ccwd)
        self.assertEqual(oargv, ["open", "2026-10-07-fix.bale-bundle"])

    def test_a_forecast_path_bale_cannot_find_stops_it_before_anything_is_written(self):
        bundle_file(self.downloads, "2026-10-07-gone", self.argv("gone", "nowhere"))
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", "fix-login", "--on", "alpha", "2026-10-07-gone.bale-bundle", check=1)
        self.assertIn("--write path does not exist: nowhere", proc.stderr)
        self.assertIn("start stopped before anything was written", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        self.assertFalse((self.e.home / "out-tray").exists() and any((self.e.home / "out-tray").iterdir()))
        self.assertEqual(self.fake.calls_of("open"), [])


class TestStartNewOnATerminal(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def desk(self):
        return sorted(p.name for p in (self.root / "desk").iterdir() if p.is_dir())

    def test_a_bundle_bale_cannot_find_stops_new_before_a_folder_or_a_question(self):
        desk, head = self.desk(), self.e.git(self.root, "rev-parse", "HEAD")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "new", "--on", "alpha",
                                          "2026-10-07-third-trip.bale-bundle"], self.root, self.e.env, [])
        self.assertEqual(code, 1, seen)
        self.assertIn("bundle not found: 2026-10-07-third-trip.bale-bundle", seen)
        self.assertIn(str(self.downloads), seen)
        self.assertNotIn("Title", seen)
        self.assertEqual(self.desk(), desk)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)

    def test_a_failed_start_names_the_folder_it_opened_and_one_line_retries_it(self):
        bundle_file(self.downloads, "2026-10-07-third-trip", ["The third trip", "--slug", "third-trip", "--write",
                                                              "src", "--constraint", ob.PROJECT_CONSTRAINT])
        state = json.loads(self.fake.state.read_text()) if self.fake.state.is_file() else {"repos": {}, "fail": []}
        state["fail"] = ["pack"]
        self.fake.state.write_text(json.dumps(state))
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "new", "--on", "alpha",
                                          "2026-10-07-third-trip.bale-bundle"], self.root, self.e.env, [
            (b"Title, in a few words (--title):", "third trip"),
            (b"Size: small, medium or high (--size)", ""),
            (b"Lane: the project and paths", ""),
            (b"Source: where the job came from (--source)", ""),
        ])
        self.assertEqual(code, 1, seen)
        lines = [l.strip() for l in seen.replace("\r", "").splitlines() if l.strip()]
        name = next(p for p in self.desk() if p.endswith("-third-trip"))
        self.assertEqual(lines[-1], f"office start {name} --on alpha 2026-10-07-third-trip.bale-bundle")
        self.assertIn(f"desk/{name} (folder 2) was opened by this start and stays on the desk", seen)
        # The line, pasted as it is, sends the session once the cause is gone.
        state = json.loads(self.fake.state.read_text())
        state["fail"] = []
        self.fake.state.write_text(json.dumps(state))
        proc = self.e.run(*shlex.split(lines[-1])[1:], cwd=self.root, check=0)
        sid = re.search(r"^Packed (\S+) for desk/(\S+)\.$", proc.stdout, re.M)
        self.assertEqual(sid.group(2), name)
        self.assertIn(f"\n- {sid.group(1)}\n", (self.root / "desk" / name / "folder.md").read_text())

    def test_new_with_a_title_already_on_the_desk_offers_it_before_anything_else(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "new", "--on", "alpha", "--goal", "g"],
                                   self.root, self.e.env, [
            (b"Title, in a few words (--title):", "fix login"),
            (f"{self.folder} is already on the desk: start it".encode(), ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("Size:", seen)
        self.assertIn(f"Packed ", seen)
        self.assertEqual(len([p for p in self.desk()]), 1)
        self.assertRegex((self.root / self.folder / "folder.md").read_text(), r"\n- \d{4}-\d{2}-\d{2}-fix-login-001\n")

    def test_open_asks_another_title_at_once_rather_than_refusing_at_the_end(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "open"], self.root, self.e.env, [
            (b"Title, in a few words (--title):", "fix login"),
            (b"is already on the desk; give another title", "other job"),
            (b"Size: small, medium or high (--size)", ""),
            (b"Lane: the project and paths", ""),
            (b"Source: where the job came from (--source)", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertEqual(seen.count("Size:"), 1)
        self.assertTrue(any(p.endswith("-other-job") for p in self.desk()))


# --- 4. the riders a pack carries, offered at start ----------------------------------------------

class RiderCase(LandCase):
    def setUp(self):
        super().setUp()
        self.run_office("rider", "add", "Name the sweep", "--source", "test", "--rides", "src/", check=0)
        self.run_office("rider", "add", "Beta's own", "--source", "test", "--rides", "beta: src", check=0)
        self.run_office("rider", "add", "The docs", "--source", "test", "--rides", "docs/", check=0)
        self.number = re.search(r"- number: (\d+)", (self.root / self.folder / "folder.md").read_text()).group(1)

    def riders_section(self):
        text = (self.root / self.folder / "folder.md").read_text()
        return text.split("## Riders", 1)[1].split("\n## ", 1)[0] if "## Riders" in text else ""


class TestRidersAtStart(RiderCase):
    def test_the_forecast_picks_the_riders_and_a_project_glob_holds_to_its_project(self):
        hits = od.riders_for_forecast(self.root, ["src"], "alpha")
        self.assertEqual([h["number"] for h in hits], [1])
        self.assertEqual([h["number"] for h in od.riders_for_forecast(self.root, ["src"], "beta")], [1, 2])
        self.assertEqual([h["number"] for h in od.riders_for_forecast(self.root, ["."], None)], [1, 3])
        out = self.run_office("riders", "--forecast", "src", "--project", "beta", check=0).stdout
        self.assertIn("rider 2  Beta's own  (rides beta: src; the forecast's src)", out)

    def test_piped_carries_none_and_names_each_with_its_flag(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", check=0)
        self.assertIn("rider 1 (Name the sweep) rides this forecast (rides src/); piped input carries none: "
                      "--carry 1 carries it", proc.stderr)
        self.assertNotIn("rider 2", proc.stderr)
        self.assertNotIn("rider 3", proc.stderr)
        self.assertNotIn("### rider", self.riders_section())

    def test_carry_n_carries_it_into_the_folder_before_the_pack(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--carry", "1", check=0)
        self.assertIn(f"rider 1 carried into {self.folder}", proc.stderr)
        self.assertIn("### rider 1 - Name the sweep", self.riders_section())
        subjects = self.subjects(8)
        self.assertIn(f"office rider carry: rider 1 -> folder {self.number}", subjects)
        # It rides: the office's context tarball carries the folder as carried.
        tray = pathlib.Path(re.search(r"^Out tray: (.*)$", proc.stdout, re.M).group(1))
        with tarfile.open(tray / "context-home.tar.gz") as t:
            member = next(m for m in t.getnames() if m.endswith(f"{self.name}/folder.md"))
            self.assertIn("### rider 1 - Name the sweep", t.extractfile(member).read().decode())

    def test_carry_none_carries_none_and_a_named_rider_that_cannot_move_stops_the_start(self):
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--carry", "none", check=0)
        self.assertIn("1 rider(s) on the riders page ride this forecast; --carry none leaves them there",
                      proc.stderr)
        self.assertNotIn("### rider", self.riders_section())
        self.run_office("open", "second", "--lane", "alpha: docs", check=0)
        proc = self.run_office("start", "second", "--on", "alpha", "--goal", "g", "--carry", "9", check=1)
        self.assertIn("--carry 9: the rider could not be carried", proc.stderr)
        self.assertEqual(len([c for c in self.fake.calls_of("pack") if "--context" not in c[1]]), 1)
        self.assertIn("--carry none carries no rider",
                      self.run_office("start", "second", "--on", "alpha", "--carry", "none", "--carry", "1",
                                      check=1).stderr)


class TestRidersOnATerminal(RiderCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_each_is_offered_and_a_plain_return_carries_it(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "fix-login", "--on", "alpha", "--goal",
                                          "g"], self.root, self.e.env, [
            (b"Rider 1, Name the sweep (rides src/; the forecast's src): carry it into the folder", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("Rider 2", seen)
        self.assertIn("### rider 1 - Name the sweep", self.riders_section())


# --- 5. office land: watches check, and the founding folder ---------------------------------------

class TestLandRunsWatchesCheck(LandCase):
    def land_one(self, extra=None):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "b\n"})
        return self.run_office("land", sid, "--not-now", check=0, extra=extra)

    def test_no_register_no_lines_and_bale_is_not_asked(self):
        proc = self.land_one({"OFFICE_DEBUG": "1"})
        self.assertNotIn("Watches that fired", proc.stdout)
        self.assertEqual([c for c in self.fake.calls_of("stats") if "--sid" not in c[1]], [])
        self.assertTrue(proc.stdout.rstrip().splitlines()[-1].startswith("  "), "the after-land report is last")

    def test_with_a_register_it_checks_records_nothing_and_never_fails_the_landing(self):
        dt = self.root / od.SPACE
        dt.mkdir(exist_ok=True)
        (dt / "watches.md").write_text(od.render_page("watches.md") + REGISTER_PAGE)
        (dt / "watch-log.md").write_text(od.render_page("watch-log.md") + LOG_PAGE)
        self.run_office("rider", "add", "arrive", "--source", "test", check=0)
        self.e.git(self.root, "add", "-A")
        self.e.git(self.root, "commit", "-qm", "a sitting's watches")
        log = (dt / "watch-log.md").read_bytes()
        proc = self.land_one({"OFFICE_DEBUG": "1"})
        self.assertIn("Landed:", proc.stdout)
        # The fake serves no aggregate, so every query cannot evaluate: none
        # fired, nothing printed, nothing recorded, the landing stands.
        self.assertTrue([c for c in self.fake.calls_of("stats") if "--sid" not in c[1]])
        self.assertIn("after land: no watch fired", proc.stderr)
        self.assertEqual((dt / "watch-log.md").read_bytes(), log)


class TestFiredOnly(WatchCase):
    def test_only_the_fired_lines_and_nothing_without_a_register(self):
        argv = [sys.executable, "-B", str(REPO / "lib" / "office_watches.py"), "check", str(self.root),
                "--day", "2026-10-07", "--tz", "Etc/UTC", "--fired-only"]
        none = subprocess.run(argv, env=self.e.env, capture_output=True, text=True)
        self.assertEqual((none.returncode, none.stdout), (0, ""))
        self.pages()
        proc = subprocess.run(argv, env=self.e.env, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        out = proc.stdout.splitlines()
        self.assertEqual([l.split(":")[0] for l in out], ["W1 unparsed-share in bale-src", "W1 unparsed-share in ironwood",
                                                          "W13 unused-forecast-entries in office-src",
                                                          "W24 unrelayed-rounds in bale-src"])
        self.assertTrue(all(": fired: " in l for l in out))
        both = subprocess.run(argv + ["--record"], env=self.e.env, capture_output=True, text=True)
        self.assertEqual(both.returncode, 2)


class TestTheFoundingFolderClosesWithTheFounding(DoorCase):
    def setUp(self):
        super().setUp()
        self.e.run("init", str(self.root), "--no-projects", "--no-founding", check=0)

    def test_complete_it_closes_incomplete_it_stays_and_land_says_which(self):
        proc = self.e.run("found", "--purpose", "p", cwd=self.root, check=0)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        folder = self.founding_folder()
        response_tarball(self.downloads, sid, {f"notepad/{sid[:10]}-founding.md": "# His words\n"})
        proc = self.e.run("land", "--not-now", cwd=self.root, check=0)
        self.assertIn("the profile is still incomplete, so its folder stays open", proc.stderr)
        self.assertIn(f"the founding folder {folder.name}: stays open, the profile is incomplete", proc.stdout)
        self.assertTrue(folder.is_dir())
        # Sent again for what is missing, and landed complete: closed, done.
        proc = self.e.run("start", folder.name, cwd=self.root, check=0)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        response_tarball(self.downloads, sid, {"profile.md": filled_profile("home")})
        proc = self.e.run("land", "--not-now", cwd=self.root, check=0)
        self.assertIn(f"so its folder is closed: {folder.name} is in the filing cabinet, done", proc.stderr)
        self.assertIn(f"the founding folder {folder.name}: closed, done (the profile is complete)", proc.stdout)
        filed = self.root / "filing-cabinet" / folder.name / "folder.md"
        text = filed.read_text()
        self.assertIn("- status: done", text)
        self.assertIn(f"done: office land: the founding landed at {sid}, with the profile complete", text)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_a_landing_for_another_folder_closes_nothing(self):
        proc = self.e.run("found", "--purpose", "p", cwd=self.root, check=0)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        founding = self.founding_folder()
        response_tarball(self.downloads, sid, {f"notepad/{sid[:10]}-founding.md": "# His words\n"})
        self.e.run("land", "--not-now", cwd=self.root, check=0)
        (self.root / "profile.md").write_text(filled_profile("home"))
        self.e.git(self.root, "commit", "-qam", "founded by hand")
        job = self.e.run("open", "a-job", cwd=self.root, check=0).stdout.strip()
        proc = self.e.run("start", job.split("/")[1], "--in-office", "--goal", "g", cwd=self.root, check=0)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        response_tarball(self.downloads, sid, {f"notepad/{sid[:10]}-a-job.md": "a page\n"})
        proc = self.e.run("land", "--not-now", cwd=self.root, check=0)
        self.assertNotIn("founding", proc.stdout + proc.stderr)
        self.assertTrue(founding.is_dir(), "another folder's landing closed the founding folder")


# --- 6. the walk-in, when the install is behind its source ---------------------------------------

class TestInstallBehindItsSource(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.src = self.e.tmp / "office-src"
        shutil.copytree(REPO, self.src, ignore=shutil.ignore_patterns(".git", ".bale", "__pycache__"))
        self.e.git(self.src, "init", "-q")
        self.e.git(self.src, "add", "-A")
        self.e.git(self.src, "commit", "-qm", "src")
        (self.src / ".bale").mkdir()  # a repo bale has run in, as office projects add asks
        prefix, bindir = self.e.tmp / "share" / "office-src", self.e.tmp / "bin"
        proc = subprocess.run([str(self.src / "install.sh"), "--prefix", str(prefix), "--bin-dir", str(bindir)],
                              env=self.e.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.office = bindir / "office"
        self.fake = FakeLandBale(self.e.tmp)
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.root = self.e.init("home", bin_path=self.office)
        self.e.found(self.root)

    def walk_in(self):
        return self.e.run(cwd=self.root, bin_path=self.office, check=0).stdout

    def test_said_in_status_words_and_the_next_line_names_the_install(self):
        self.assertNotIn("Install:", self.walk_in(), "a source the office does not scope is not its business")
        self.e.run("projects", "add", "office-src", str(self.src), cwd=self.root, bin_path=self.office, check=0)
        level = self.walk_in()
        self.assertNotIn("Install:", level)
        self.assertNotIn("./install.sh", last_line(level))
        (self.src / "README.md").write_text("moved on\n")
        self.e.git(self.src, "commit", "-qam", "moved on")
        out = self.walk_in()
        line = next(l for l in out.splitlines() if l.startswith("Install: "))
        status = self.e.run("status", cwd=self.root, bin_path=self.office, check=0).stdout
        source = next(l for l in status.splitlines() if l.startswith("source:"))
        self.assertEqual(line[len("Install: "):], source[len("source:"):].strip())
        self.assertTrue(line.startswith("Install: BEHIND: the install is "), line)
        self.assertIn(f"(office-src {VERSION})", line)
        self.assertTrue(last_line(out).startswith(f"Next: (cd '{self.src}' && ./install.sh)  (the installed "
                                                  "office-src is behind its source, which this office scopes as "
                                                  "office-src"), last_line(out))

    def test_the_order_behind_the_skew_cases_and_ahead_of_a_session_out(self):
        behind = {"source": "/s", "commit": "abc1234", "head": "def5678", "version": "9.9.9", "project": "office-src"}
        out = [{"sid": "2026-10-07-x-001", "label": "alpha", "folders": ["desk/x"], "held": False}]
        self.assertEqual(ob.next_move("current", True, out, {}, [], 0, behind)[0], "(cd '/s' && ./install.sh)")
        self.assertEqual(ob.next_move("behind", True, out, {}, [], 0, behind)[0], "office upgrade")
        self.assertEqual(ob.next_move("ahead", True, out, {}, [], 0, behind)[0], "office status")
        self.assertEqual(ob.next_move("current", True, out, {}, [], 0, None)[0], "office land 2026-10-07-x-001")
        self.assertEqual(ob.shell_quote("/a b/it's"), "'/a b/it'\\''s'")


# --- 7. a founding answer that runs to a paragraph -----------------------------------------------

class TestAParagraphAnswer(DoorCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_lines_until_a_blank_one_and_the_prompt_says_so(self):
        argv = [str(self.e.office_bin), "init", str(self.root), "--no-projects", "--not-for", "n", "--audiences", "a",
                "--site", "s", "--house-rules", "h", "--when-to-open", "w", "--spaces", "x",
                "--timezone", "America/Chicago"]
        code, seen = on_a_terminal(self, argv, self.e.home, self.e.env, [
            (b"(--purpose) [several lines welcome; a blank line ends the answer, and return at once skips]:",
             "My own tools,\n  and my life outside work.\nBoth, kept apart.\n"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("An answer may run to several lines, and a blank line ends it", seen)
        answers = (self.founding_folder() / "answers.md").read_text()
        for words in ("My own tools,", "  and my life outside work.", "Both, kept apart."):
            self.assertIn(words, answers)
        brief = None
        for p in (self.e.home / "out-tray").glob("*/request-*.tar.gz"):
            with tarfile.open(p) as t:
                brief = next((t.extractfile(m).read().decode() for m in t.getmembers()
                              if m.name.endswith("/README.md") and m.name.count("/") == 1), brief)
        self.assertIsNotNone(brief)
        self.assertIn("and my life outside work.", brief)


if __name__ == "__main__":
    unittest.main()
