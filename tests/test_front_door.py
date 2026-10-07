"""Tests for the front door: the walk-in's Next line, help organized by
task, office tour, office init asking which projects the office watches,
and office start's own words for a bundle whose forecast overlaps an open
session.

bale is never needed. The walk-in's sessions and the bundle refusals run
against the fake bales the out-and-in and return-trip suites built from
captured bale output; the tour runs against nothing at all, and its tests
prove it: a fake bale first on the PATH records every call, and the tour
must make none. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import os
import pathlib
import pty
import re
import select
import signal
import subprocess
import sys
import time
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, filled_profile, verbs_catalog  # noqa: E402
from test_start import FakePackBale, git_repo, on_a_terminal  # noqa: E402
from test_land import LandCase, bundle_file, response_tarball  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)


def last_line(text):
    return text.rstrip("\n").splitlines()[-1]


# --- the Next line, as a pure function ------------------------------------------------

def folder(n, name, lane=None):
    return {"name": name, "number": n, "fields": {"lane": [lane]} if lane else {}, "rel": f"desk/{name}"}


def groups(**kw):
    g = {"flying": [], "open": [], "ready": [], "parked": {}, "candidates": [], "no_status": [],
         "misplaced": [], "unreadable": [], "ready_errors": [], "cleared": {}}
    g.update(kw)
    return g


def out_session(sid, label="alpha", folders=("desk/2026-10-05-fix-login",), held=False, created="2026-10-05T10:00:00Z"):
    return {"sid": sid, "label": label, "folders": list(folders), "held": held, "created": created}


PROJECTS = [{"name": "alpha"}]


class TestNextMove(unittest.TestCase):
    """Each state names its one command, and the states win in order."""

    def move(self, skew="current", founded=True, out=(), g=None, projects=PROJECTS, slips=0):
        return ob.next_move(skew, founded, list(out), g or groups(), projects, slips)

    def test_skew_comes_first(self):
        busy = groups(ready=[folder(1, "2026-10-05-fix-login")])
        self.assertEqual(self.move("behind", out=[out_session("2026-10-05-a-001")], g=busy)[0], "office upgrade")
        self.assertEqual(self.move("ahead", g=busy)[0], "office status")
        self.assertIn("migrated past", self.move("ahead")[1])
        self.assertEqual(self.move("unreadable")[0], "office status")

    def test_a_session_out_outranks_an_unfounded_office_and_the_desk(self):
        cmd, why = self.move(founded=False, out=[out_session("2026-10-05-fix-login-001")],
                             g=groups(ready=[folder(1, "x")]))
        self.assertEqual(cmd, "office land 2026-10-05-fix-login-001")
        self.assertIn("out in alpha (desk/2026-10-05-fix-login)", why)
        self.assertIn("when its response is in your downloads, land finds it", why)

    def test_the_founding_session_lands_from_the_office_with_no_folder(self):
        cmd, why = self.move(founded=False, out=[out_session("2026-10-05-home-founding-001", label=ob.OFFICE_LABEL,
                                                             folders=())])
        self.assertEqual(cmd, "office land 2026-10-05-home-founding-001")
        self.assertIn("out in this office (no folder records it)", why)

    def test_the_first_of_several_out_is_named_and_the_rest_counted(self):
        cmd, why = self.move(out=[out_session("2026-10-05-held-001", held=True), out_session("2026-10-05-b-001")])
        self.assertEqual(cmd, "office land 2026-10-05-held-001")
        self.assertIn("bale held it in alpha", why)
        self.assertIn("land asks for the corrected response; 1 more out after it", why)

    def test_unfounded_with_no_founding_folder_names_found(self):
        cmd, why = self.move(founded=False, g=groups(ready=[folder(1, "x")]))
        self.assertEqual(cmd, "office found")
        self.assertIn("unfounded, and no founding folder is on the desk", why)

    def test_the_first_ready_folder_with_its_project(self):
        g = groups(ready=[folder(3, "2026-10-05-fix-login", "alpha: src"), folder(4, "2026-10-05-other")])
        cmd, why = self.move(g=g)
        self.assertEqual(cmd, "office start 2026-10-05-fix-login --on alpha")
        self.assertIn("folder 3 is ready and first on the desk", why)
        self.assertIn("1 more ready after it", why)
        # A lane naming no project of this office leaves where to start to ask.
        g = groups(ready=[folder(3, "2026-10-05-fix-login", "gamma: src")])
        self.assertEqual(self.move(g=g)[0], "office start 2026-10-05-fix-login")

    def test_an_open_folder_no_session_carries(self):
        cmd, why = self.move(g=groups(open=[folder(2, "2026-10-05-fix-login", "alpha: src")]))
        self.assertEqual(cmd, "office start 2026-10-05-fix-login --on alpha")
        self.assertIn("office close 2026-10-05-fix-login instead when its job is done", why)

    def test_no_projects_comes_after_a_ready_job(self):
        ready = groups(ready=[folder(1, "2026-10-05-x")])
        self.assertEqual(self.move(g=ready, projects=None)[0], "office start 2026-10-05-x")
        for projects in (None, []):
            self.assertEqual(self.move(projects=projects)[0], "office projects add")

    def test_slips_piling_up_become_a_job_unless_one_is_waiting(self):
        cmd, why = self.move(slips=ob.SLIPS_PILING)
        self.assertTrue(cmd.startswith("office open triage-the-suggestion-box --title"), cmd)
        self.assertIn(f"{ob.SLIPS_PILING} slips", why)
        self.assertEqual(self.move(slips=ob.SLIPS_PILING - 1)[0], "office open")
        waiting = groups(candidates=[folder(5, "2026-10-05-triage-the-suggestion-box")])
        self.assertEqual(self.move(slips=9, g=waiting)[0], "office desk")

    def test_folders_that_wait_then_nothing(self):
        g = groups(parked={"waiting for folder 1": [(folder(2, "y"), [])]}, candidates=[folder(3, "z")])
        cmd, why = self.move(g=g)
        self.assertEqual(cmd, "office desk")
        self.assertIn("1 parked, 1 candidate(s)", why)
        self.assertEqual(self.move(g=groups(no_status=[{"name": "old"}]))[0], "office desk")
        cmd, why = self.move()
        self.assertEqual(cmd, "office open")
        self.assertIn("nothing waits on you", why)


# --- the Next line on a real walk-in ---------------------------------------------------

class TestNextOnTheWalkIn(LandCase):
    def walk_in(self):
        return self.run_office(check=0).stdout

    def test_the_walk_in_ends_with_it_and_writes_nothing_down(self):
        out = self.walk_in()
        self.assertEqual(last_line(out), f"Next: office start {self.name} --on alpha  (folder 1 is ready and first on "
                                         "the desk; start asks for the goal and sends a session out)")
        self.assertIn("From here: office start", out)
        # Worked out on every walk-in, never written down: the office is
        # as it was, and nothing in it holds the line.
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertNotIn(b"Next: office", b"".join(p.read_bytes() for p in self.root.rglob("*")
                                                    if p.is_file() and ".git" not in p.parts))

    def test_a_session_out_is_landed_next(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        self.assertEqual(last_line(self.walk_in()),
                         f"Next: office land {sid}  (it is out in alpha ({self.folder}); when its response is in "
                         "your downloads, land finds it)")

    def test_a_held_session_says_land_asks_for_the_corrected_response(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, validation="fail")
        self.run_office("land", check=1)
        line = last_line(self.walk_in())
        self.assertTrue(line.startswith(f"Next: office land {sid}  (bale held it in alpha"), line)
        self.assertIn("land asks for the corrected response", line)

    def test_once_landed_the_open_folder_is_next(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        self.run_office("land", "--not-now", check=0)
        line = last_line(self.walk_in())
        self.assertEqual(line, f"Next: office start {self.name} --on alpha  (folder 1 is open and no session is out "
                               f"for it; office close {self.name} instead when its job is done)")
        self.run_office("close", "fix-login", check=0)
        self.assertTrue(last_line(self.walk_in()).startswith("Next: office open  (nothing waits on you"))

    def test_an_unfounded_office_lands_its_founding_session_first(self):
        fresh = self.e.init("fresh")
        pack = subprocess.run(["bale", "pack", "Found it", "--slug", "fresh-founding", "--include", "floor-plan",
                               "--write", "profile.md", "--no-readme", "--json"],
                              cwd=fresh, env=self.e.env, capture_output=True, text=True)
        self.assertEqual(pack.returncode, 0, pack.stderr)
        sid = re.search(r'"sid": "([^"]+)"', pack.stdout).group(1)
        out = self.e.run(cwd=fresh, check=0).stdout
        self.assertIn("UNFOUNDED", out)
        self.assertEqual(last_line(out), f"Next: office land {sid}  (it is out in this office (no folder records "
                                         "it); when its response is in your downloads, land finds it)")

    def test_with_no_office_anywhere_the_tour_is_next(self):
        (self.e.home / ".config/office-src/default-office").unlink()
        outside = self.e.tmp / "elsewhere"
        outside.mkdir()
        out = self.e.run(cwd=outside, check=0).stdout
        self.assertTrue(last_line(out).startswith("Next: office tour"), out)


# --- help by task ----------------------------------------------------------------------

TASKS = ["Walk in and look around", "Capture a thought or a friction", "Start a job, and finish one",
         "Plan work too big for one folder", "Send a session out", "Bring one back", "Look after the office"]
TWO_WORD = ("blueprint-open", "blueprint-ratify", "rider-add", "rider-carry", "rider-consumed", "agenda-add",
            "watches-check")


class TestHelpByTask(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)

    def help(self, *args):
        return self.e.run(*args, check=0).stdout

    def test_help_groups_the_verbs_by_what_you_want_to_do(self):
        out = self.help("help")
        at = [out.index(t) for t in TASKS]
        self.assertEqual(at, sorted(at), "the task groups are out of order")
        self.assertIn("New here? office tour", out)
        for upside in ("never type a session id", "never\nassemble an include list", "never forget a landing step"):
            self.assertIn(upside, out)
        self.assertIn("OFFICE_DEBUG=1 shows", out)
        self.assertIn("Any bale command still works by hand beside the office", out)
        # Each verb sits under its task.
        send, back, care = (out.index(t) for t in ("Send a session out", "Bring one back", "Look after the office"))
        self.assertTrue(send < out.index("office start [FOLDER]") < back < out.index("office land [SID]") < care)
        self.assertEqual(self.help("--help"), out)

    def test_every_built_verb_explains_itself_with_an_example_and_needs_no_office(self):
        verbs = [n for n, v in verbs_catalog()["verbs"].items() if v["kind"] == "script" and v["built"]]
        self.assertIn("tour", verbs)
        for name in verbs + ["version"]:
            # A two-word verb's key is hyphenated: blueprint-open is
            # office blueprint open, and office help blueprint open.
            words = name.split("-") if name in TWO_WORD else [name]
            proc = self.e.run(*words, "--help")
            self.assertEqual(proc.returncode, 0, f"{name}: {proc.stderr}")
            text = proc.stdout
            self.assertIn(f"usage: office {' '.join(words)}", text, name)
            examples = text.split("Examples:\n", 1)
            self.assertEqual(len(examples), 2, f"{name} --help has no Examples")
            self.assertRegex(examples[1], rf"(?m)^  (office {' '.join(words)}\b|office --version)", name)
            self.assertEqual(self.help("help", *words), text, name)
            if name in TWO_WORD:
                self.assertEqual(self.help("help", name), text, name)

    def test_start_and_land_name_the_bale_commands_they_run(self):
        self.assertIn("Under the hood: bale pack --json (or bale open", self.help("start", "--help"))
        self.assertIn("Under the hood: bale apply TARBALL (bale retry", self.help("land", "--help"))

    def test_help_for_no_such_verb_refuses(self):
        proc = self.e.run("help", "frobnicate")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("knows no verb frobnicate", proc.stderr)


# --- office tour -----------------------------------------------------------------------

def run_on_a_pty(argv, cwd, env, steps, limit=60):
    """Run on a pty; steps is a list of (marker, action) where action is
    bytes to type or a signal number to send. Returns (code, screen)."""
    pid, fd = pty.fork()
    if pid == 0:
        try:
            os.chdir(cwd)
            os.execve(argv[0], argv, env)
        finally:
            os._exit(127)
    seen = b""

    def read_until(marker, wait):
        nonlocal seen
        deadline = time.time() + wait
        while (marker is None or marker not in seen) and time.time() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    return False
                if not chunk:
                    return False
                seen += chunk
        return marker is None or marker in seen

    for marker, action in steps:
        if not read_until(marker, limit):
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
            raise AssertionError(f"never saw {marker!r}:\n{seen.decode(errors='replace')}")
        if isinstance(action, int):
            os.kill(pid, action)
        elif action is not None:
            os.write(fd, action)
    read_until(None, 20)
    # A child still running now is a hang: kill it and fail, rather than
    # hold the whole suite on waitpid.
    deadline = time.time() + 10
    done, status = os.waitpid(pid, os.WNOHANG)
    while done == 0 and time.time() < deadline:
        time.sleep(0.1)
        done, status = os.waitpid(pid, os.WNOHANG)
    if done == 0:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
        os.close(fd)
        raise AssertionError(f"still running after its last step:\n{seen.decode(errors='replace')}")
    os.close(fd)
    return os.waitstatus_to_exitcode(status), seen.decode(errors="replace")


class TourCase(unittest.TestCase):
    """A machine with a real office (the default) and a fake bale that
    records every call, so the tour's isolation can be read off."""

    def setUp(self):
        self.e = Env(self)
        self.fake = FakePackBale(self.e.tmp)
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.tmpdir = self.e.tmp / "tmpdir"
        self.tmpdir.mkdir()
        self.e.env["TMPDIR"] = str(self.tmpdir)
        self.real = self.e.init("real")
        self.e.run(cwd=self.real, check=0)        # a walk-in, so there is a record to keep
        self.fake.calls.unlink(missing_ok=True)   # init's survey asked bale its version; the tour must not
        self.before = self.snapshot()

    def snapshot(self):
        state = self.e.home / ".local/state"
        return {
            "head": self.e.git(self.real, "rev-parse", "HEAD"),
            "status": self.e.git(self.real, "status", "--porcelain"),
            "default": (self.e.home / ".config/office-src/default-office").read_text(),
            "config": sorted(str(p.relative_to(self.e.home)) for p in (self.e.home / ".config").rglob("*")),
            "state": {str(p.relative_to(self.e.home)): p.read_bytes() for p in state.rglob("*") if p.is_file()},
            "home": sorted(p.name for p in self.e.home.iterdir()),
        }

    def assert_untouched(self):
        self.assertEqual(self.snapshot(), self.before)
        self.assertEqual(list(self.tmpdir.iterdir()), [], "the tour office was left behind")
        self.assertEqual(self.fake.argvs(), [], "the tour ran bale")


class TestTourPiped(TourCase):
    def test_it_walks_through_the_verbs_and_leaves_nothing(self):
        proc = self.e.run("tour", cwd=self.real)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = proc.stdout
        for n, title in enumerate(["walk in", "capture a thought", "start a job", "look at the desk", "this week",
                                   "send a session out, and bring it back (shown, not run)"], 1):
            self.assertIn(f"== Step {n} of 6: {title} ==", out)
        for shown in ("  $ office\n", "  $ office note 'the electrician can come Thursday'",
                      "  $ office open fix-the-gate --title 'Fix the garden gate' --size small", "  $ office desk",
                      "  $ office week", "  $ office land\n"):
            self.assertIn(shown, out)
        # Each step says what the command did and why you would type it.
        self.assertEqual(out.count("What it did:"), 5)
        self.assertEqual(out.count("Why you would type it:"), 5)
        self.assertEqual(out.count("(not run: the tour never runs bale)"), 2)
        # The commands acted on the tour office, never the real one.
        self.assertIn("    The tour office, ", out)
        self.assertNotIn(f"The real office, {self.real}", out)
        self.assertRegex(out, r"    Next: office start \d{4}-\d{2}-\d{2}-fix-the-porch-light  \(folder 1 is ready")
        self.assertIn("GAP: nothing recorded", out)
        self.assertIn("waiting for folder 1 (queued): Fix the porch light", out)
        self.assertIn("opened desk/", out)
        self.assertIn("The tour office is deleted (", out)
        self.assertTrue(last_line(out).startswith("Next: office  (walk into your own office"), out)
        self.assert_untouched()

    def test_piped_it_never_plays_and_refuses_to_be_told_to(self):
        proc = self.e.run("tour", "--play", cwd=self.real)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("needs a terminal", proc.stderr)
        self.assertIn("contradict", self.e.run("tour", "--play", "--no-play").stderr)
        self.assert_untouched()

    def test_without_an_office_it_suggests_building_one(self):
        (self.e.home / ".config/office-src/default-office").unlink()
        elsewhere = self.e.tmp / "elsewhere"
        elsewhere.mkdir()
        proc = self.e.run("tour", cwd=elsewhere, check=0)
        self.assertTrue(last_line(proc.stdout).startswith("Next: office init  (build a real office"), proc.stdout)
        self.assertFalse((self.e.home / ".config/office-src/default-office").exists())
        self.assertEqual(list(self.tmpdir.iterdir()), [])


class TestTourOnATerminal(TourCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane
    def argv(self, *extra):
        return [str(self.e.office_bin), "tour", *extra]

    def test_an_interrupt_deletes_the_office_and_says_so(self):
        code, seen = run_on_a_pty(self.argv(), self.real, self.e.env,
                                  [(b"[return: the next step; q: end the tour]", b"\n"),
                                   (b"== Step 1 of 6", None),
                                   (b"Why you would type it: it is the front door", b"\x03")])
        self.assertEqual(code, 130, seen)
        self.assertIn("the tour was interrupted; deleting the tour office at", seen)
        self.assert_untouched()

    def test_a_termination_deletes_it_too(self):
        code, seen = run_on_a_pty(self.argv(), self.real, self.e.env,
                                  [(b"[return: the next step; q: end the tour]", signal.SIGTERM)])
        self.assertEqual(code, 143, seen)
        self.assertIn("the tour was stopped; deleting the tour office", seen)
        self.assert_untouched()

    def test_q_ends_it_early_and_deletes_the_office(self):
        code, seen = run_on_a_pty(self.argv(), self.real, self.e.env,
                                  [(b"[return: the next step; q: end the tour]", b"q\n")])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("== Step 1 of 6", seen)
        self.assertIn("The tour office is deleted", seen)
        self.assert_untouched()

    def test_play_opens_a_shell_in_the_tour_office(self):
        code, seen = run_on_a_pty(self.argv("--no-pause"), self.real, self.e.env, [
            (b"Play in the tour office yourself before it goes?", b"y\n"),
            (b"(office tour)", b"office where; office note played; echo tour-shell-$((6*7))\n"),
            (b"tour-shell-42", b"exit\n"),
        ])
        self.assertEqual(code, 0, seen)
        where = re.search(r"(\S*office-tour\.\w+/office)\r?\n", seen)
        self.assertIsNotNone(where, seen)
        self.assertIn("noted 1 line(s)", seen)
        self.assertIn("The tour office is deleted", seen)
        self.assert_untouched()
        self.assertFalse((self.e.home / ".bash_history").exists())


# --- office init asks which projects the office watches ---------------------------------

class TestInitProjects(unittest.TestCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane
    def setUp(self):
        self.e = Env(self)
        self.alpha = git_repo(self.e.home / "alpha")
        self.beta = git_repo(self.e.home / "beta-src")

    def projects(self, root):
        return tomllib.loads((root / "floor-plan/manifest.toml").read_text()).get("projects")

    def test_the_flag_twin_adds_each_and_stdout_stays_the_next_line(self):
        root = self.e.home / "home"
        proc = self.e.run("init", str(root), "--project", str(self.alpha), "--project", f"tools={self.beta}",
                          "--no-founding", check=0)
        self.assertEqual(proc.stdout.splitlines(), ["Next: office found  (it asks the profile's questions and sends "
                                                    "the founding session out)"])
        self.assertEqual(self.projects(root), {"alpha": {"path": str(self.alpha)}, "tools": {"path": str(self.beta)}})
        self.assertEqual(self.e.git(root, "log", "--format=%s").splitlines(),
                         ["office projects: add tools", "office projects: add alpha", "office init: home (office-src "
                          + (REPO / "VERSION").read_text().strip() + ")"])
        self.assertEqual(self.e.git(root, "status", "--porcelain"), "")

    def test_a_project_that_does_not_check_builds_nothing(self):
        plain = self.e.home / "plain"
        plain.mkdir()
        for spec, why in ((str(plain), "not a git repo"), (str(self.e.home / "gone"), "no such directory")):
            root = self.e.home / "w"
            proc = self.e.run("init", str(root), "--project", str(self.alpha), "--project", spec)
            self.assertEqual(proc.returncode, 1, spec)
            self.assertIn(why, proc.stderr)
            self.assertIn("nothing was built", proc.stderr)
            self.assertFalse(root.exists())
        proc = self.e.run("init", str(self.e.home / "w"), "--project", f"x={self.alpha}", "--project", f"x={self.beta}")
        self.assertIn("the name x is given twice", proc.stderr)
        self.assertFalse((self.e.home / "w").exists())

    def test_piped_it_asks_nothing(self):
        root = self.e.init("piped")
        self.assertIsNone(self.projects(root))

    def test_on_a_terminal_it_asks_until_a_plain_return(self):
        root = self.e.home / "asked"
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "init", str(root), "--no-founding"],
                                   self.e.home, self.e.env, [
            (b"A project this office watches: the path to its repo (--project PATH) [return skips]:", "?"),
            (b".bale/ directory) or is set up", str(self.alpha)),
            # After the path, where the repo is: a plain return, this machine.
            (b"Where the repo is: this machine, or an ssh host (--host) [return skips]:", ""),
            (b"Name for it in this office (--name) [alpha]:", ""),
            (b"(--ride) [return ends the list]:", ""),
            (b"(--after-land) [return ends the list]:", "./install.sh"),
            (b"Another (--after-land) [return ends the list]:", ""),
            (b"Another project's path (--project PATH)", str(self.e.home / "gone")),
            (b"Where the repo is: this machine, or an ssh host (--host) [return skips]:", ""),
            # A wrong path is said and asked again at once, before any name.
            (b"no such directory on this machine", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("[gone]", seen)
        self.assertIn("this office watches 1 project(s)", seen)
        self.assertEqual(self.projects(root), {"alpha": {"path": str(self.alpha), "after_land": ["./install.sh"]}})
        self.assertIn("Next: office found", seen)

    def test_projects_add_checks_the_path_before_asking_more(self):
        root = self.e.init("added")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "add"], root, self.e.env, [
            (b"Path to the project's git repo (--path):", str(self.e.home / "gone")),
            (b"Where the repo is: this machine, or an ssh host (--host) [return skips]:", ""),
            (b"no such directory on this machine", str(self.beta)),
            (b"Where the repo is: this machine, or an ssh host (--host) [return skips]:", ""),
            (b"Name for it in this office (--name) [beta-src]:", ""),
            (b"(--ride) [return ends the list]:", ""),
            (b"(--after-land) [return ends the list]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertEqual(seen.count("Name for it in this office"), 1, seen)
        self.assertEqual(self.projects(root), {"beta-src": {"path": str(self.beta)}})

    def test_no_projects_skips_the_question_on_a_terminal(self):
        root = self.e.home / "quiet"
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "init", str(root), "--no-projects", "--no-founding"],
                                   self.e.home, self.e.env, [])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("A project this office watches", seen)
        self.assertIsNone(self.projects(root))


# --- a bundle whose forecast overlaps an open session -------------------------------------

class TestBundleForecast(unittest.TestCase):
    def test_it_is_read_the_way_bale_pack_reads_it(self):
        f = ob.bundle_forecast
        self.assertEqual(f(["Goal", "--slug", "s", "--write", "src", "docs", "--write=README.md"]),
                         (["src", "docs", "README.md"], None))
        self.assertEqual(f(["Goal", "--slug", "s", "--include", "lib", "tests"]), (["lib", "tests"], None))
        self.assertEqual(f(["Goal", "--slug", "s"]), (None, None))
        self.assertEqual(f(["Goal", "--slug", "s", "--read-only", "--include", "x"]), ([], None))
        self.assertEqual(f(["Goal", "--write", "src", "--supersedes", "2026-10-05-a-001", "--slug", "s"]),
                         (["src"], "2026-10-05-a-001"))
        for bad in (["Goal", "--write"], ["Goal", "--frobnicate", "x"], ["Goal", "extra", "words"]):
            with self.assertRaises(ValueError, msg=bad):
                f(bad)


class TestStartABundleThatOverlaps(LandCase):
    def bundle(self, stem, *argv):
        return bundle_file(self.e.tmp / "b", stem, ["Fix it, from a bundle", "--slug", stem.split("-", 3)[-1], *argv,
                                                    "--constraint", ob.PROJECT_CONSTRAINT])

    def test_the_office_says_it_in_its_own_words_before_bale_runs(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        b = self.bundle("2026-10-05-clash", "--write", "src/a.py", "docs")
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", str(b), check=1)
        self.assertIn("the bundle 2026-10-05-clash.bale-bundle forecasts src/a.py, docs", proc.stderr)
        self.assertIn(f"{sid} is open in alpha ({self.folder}); its forecast (src) overlaps this one at src/a.py",
                      proc.stderr)
        self.assertIn(f"land it first (office land {sid})", proc.stderr)
        self.assertIn("or ask the planner for a bundle whose forecast does not overlap it", proc.stderr)
        self.assertEqual(self.fake.calls_of("open"), [], "bale was asked after all")

    def test_what_does_not_overlap_goes_out(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        for stem, argv in (("2026-10-05-docs", ["--write", "docs"]), ("2026-10-05-ro", ["--read-only"]),
                           ("2026-10-05-split", ["--write", "src", "--supersedes", sid])):
            b = self.bundle(stem, *argv)
            proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", str(b))
            self.assertNotIn("overlaps this one", proc.stderr, stem)
        self.assertEqual(len(self.fake.calls_of("open")), 3)

    def test_a_bare_name_cannot_be_read_first_so_bales_words_stand(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        bundle_file(self.downloads, "2026-10-05-bare", ["Fix it", "--slug", "bare", "--write", "src"])
        proc = self.run_office("start", "fix-login", "--on", "alpha", "2026-10-05-bare.bale-bundle", check=1)
        # bale open --check says it before anything is written (0.13.0).
        self.assertIn("start stopped before anything was written", proc.stderr)
        self.assertIn(f"intersects 1 open session(s): {sid}", proc.stderr)
        self.assertEqual(self.fake.calls_of("open"), [])
        self.assertEqual(len(self.fake.calls_of("open-check")), 1)

    def test_office_bundles_take_turns_on_the_notepad(self):
        sid = self.start("fix-login", "--in-office", "--goal", "g")
        self.run_office("open", "other-job", check=0)
        b = bundle_file(self.e.tmp / "b", "2026-10-05-office", ["Plan", "--slug", "plan", "--write", "notepad"])
        proc = self.run_office("start", "other-job", "--in-office", "--bundle", str(b), check=1)
        self.assertIn(f"{sid} is open in this office ({self.folder})", proc.stderr)
        self.assertIn("office sessions take turns on the notepad", proc.stderr)
        self.assertIn("or ask the planner for a read-only bundle", proc.stderr)
        self.assertEqual(self.fake.calls_of("open"), [])


if __name__ == "__main__":
    unittest.main()
