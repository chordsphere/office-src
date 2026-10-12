"""Tests for the suite's clock (office-src 0.17.1): the rule that no test
reads the running machine, the fast tier tests/fast-tier.toml declares,
the runner's isolated jobs and per-test times, and the detached run of the
whole suite.

The rule. Env (tests/test_office.py) is the one place a test's HOME,
TMPDIR, XDG_CONFIG_HOME and downloads are said; the runner gives every
job, and the --serial run, a HOME and TMPDIR of its own besides. A test
file that names the machine's own temporary directory, expands ~ or reads
HOME itself, outside Env, fails TestNoTestReadsTheMachine, unless the line
is one of ALLOWED, each with its reason: text a fake host runs under its
own HOME and TMPDIR, or paths a probe printed that the fixtures replay.
An allowance that no longer matches anything fails too, so the list
cannot outlive what it excuses.

Every pattern here is written with one letter bracketed (t[m]p), the way
share/letterhead.toml writes its names, so this file never spells what it
refuses and is held to its own rule. Run with the rest of the suite:

    tests/run.sh test_suite_clock
"""

import ast
import inspect
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402

import runner  # noqa: E402

TESTS = REPO / "tests"

# What a test file may not name outside Env: what each pattern catches.
RULE = (
    ("the machine's temporary directory", re.compile(r"(?<![\w$}])/t[m]p(?![\w-])")),
    ("expand[u]ser", re.compile(r"\bexpand[u]ser\b")),
    ("Path.ho[m]e(", re.compile(r"\bPath\.ho[m]e\(")),
    ("$H[O]ME", re.compile(r"\$\{?H[O]ME\b")),
    ("gettemp[d]ir(", re.compile(r"\bgettemp[d]ir\(")),
    ("H[O]ME read from the environment", re.compile(r"""(?:environ(?:\.get\(|\[)|getenv\()\s*["']H[O]ME["']""")),
)

# (module, the span allowed, why). The span is blanked before the rule
# reads the line; nothing else on the line is excused.
ALLOWED = (
    ("test_land", r"/t[m]p/office-probe\.\w+",
     "the directories a probe's bale ran in on the machine it captured from, as the fixtures hold them: the fake "
     "bale swaps them out of the text it replays, and nothing reads them"),
    ("test_out_trip_to_host", r"\$H[O]ME/\.local/bin",
     "the fake host's own upgrade.sh: the fake ssh runs it with the host's HOME, under the case's temporary tree"),
    ("test_out_trip_to_host", r"\$\{TMPDIR:-/t[m]p\}",
     "the same script's scratch directory, under the TMPDIR the fake ssh gives every host it knows"),
    ("test_return_trip", r'echo "\$H[O]ME" > AFTER-LAND-HOME',
     "an after-land action the fake host runs, to prove it ran with the host's own HOME"),
    ("test_return_trip", r'\\"\$H[O]ME\\"',
     "the text office writes for a host's shell, compared as text: nothing here expands it"),
)


def env_lines(path):
    """The line numbers of class Env, where the rule's words belong."""
    src = path.read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == "Env":
            return set(range(node.lineno, node.end_lineno + 1))
    return set()


def breaches(paths, allowed=ALLOWED):
    """(every breach as 'file:line: what: text', the allowances that matched
    nothing) over the given test files."""
    out, used = [], set()
    for path in paths:
        exempt = env_lines(path) if path.name == "test_office.py" else set()
        mine = [(i, re.compile(span)) for i, (mod, span, _) in enumerate(allowed) if mod == path.stem]
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if n in exempt:
                continue
            for i, pat in mine:
                if pat.search(line):
                    used.add(i)
                    line = pat.sub(lambda m: " " * len(m.group(0)), line)
            for what, pat in RULE:
                if pat.search(line):
                    out.append(f"{path.name}:{n}: {what}: {line.strip()}")
    stale = [allowed[i] for i in range(len(allowed)) if i not in used and allowed[i][0] in {p.stem for p in paths}]
    return out, stale


def entry_call(verb):
    """A call of the command with verb as its first word (help and
    version by any of their spellings), or with no word for the walk-in."""
    if verb == runner.WALK_IN:
        return r"(?:\.run|run_office)\((?:\s*\)|\s*cwd=|\s*check=)"
    spellings = {"version": ("version", "--version", "-V"), "help": ("help", "--help", "-h")}.get(verb, (verb,))
    word = "(?:" + "|".join(re.escape(s) for s in spellings) + ")"
    return (rf'(?:(?:\.run|run_office|\.office)\(\s*"{word}"|office"\),\s*"{word}"'
            rf'|\bself(?:\.\w+)?\.{word}\()')


def test_files():
    return sorted(TESTS.glob("test*.py"))


class TestNoTestReadsTheMachine(unittest.TestCase):
    def test_no_test_file_names_the_machines_own_outside_env(self):
        found, stale = breaches(test_files())
        self.assertEqual(found, [], "a test names the running machine's own; give it the Env's (self.e.home, "
                                    "self.e.tmpdir, self.e.downloads, Env.this_process()) instead")
        self.assertEqual(stale, [], "an allowance matches nothing any more; take it out of ALLOWED")

    def test_the_rule_catches_each_way_of_reaching_the_machine(self):
        d = pathlib.Path(Env(self).tmp)
        lines = ['x = pathlib.Path("/t' 'mp").glob("a*")', 'os.path.expand' 'user("~/x")', 'pathlib.Path.ho' 'me()',
                 's = "$H' 'OME/bin"', 's = "${H' 'OME}"', 'tempfile.gettemp' 'dir()', 'os.environ["H' 'OME"]',
                 'os.environ.get("H' 'OME")', 'os.getenv("H' 'OME")', 'run(["ls", "/t' 'mp"])']
        f = d / "test_probe_rule.py"
        f.write_text("\n".join(lines) + "\n")
        found, _ = breaches([f], allowed=())
        self.assertEqual([b.split(":")[1] for b in found], [str(n) for n in range(1, len(lines) + 1)], found)
        # What only looks like it: a path under another directory, a
        # variable's own tmp, the Env's attributes.
        f.write_text('a = "$target/t' 'mp"\nb = self.e.tmp / "x"\nc = "/t' 'mpfs"\nd = self.e.home\n')
        self.assertEqual(breaches([f], allowed=())[0], [])

    def test_env_is_the_one_place_and_an_allowance_excuses_its_span_alone(self):
        d = pathlib.Path(Env(self).tmp)
        f = d / "test_office.py"
        f.write_text('class Env:\n    p = "/t' 'mp"\n\nq = "/t' 'mp"\n')
        self.assertEqual([b.split(":")[1] for b in breaches([f], allowed=())[0]], ["4"])
        g = d / "test_land.py"
        g.write_text('a = "/t' 'mp/office-probe.ab12/x"\nb = "/t' 'mp/office-probe.ab12/x", "/t' 'mp"\n')
        found, stale = breaches([g], allowed=ALLOWED)
        self.assertEqual([b.split(":")[1] for b in found], ["2"])
        self.assertEqual(stale, [])
        g.write_text("nothing here\n")
        self.assertEqual([a[0] for a in breaches([g], allowed=ALLOWED)[1]], ["test_land"])

    def test_env_gives_each_test_its_own_home_tmpdir_config_and_downloads(self):
        a, b = Env(self), Env(self)
        for e in (a, b):
            for key in ("HOME", "TMPDIR", "XDG_CONFIG_HOME"):
                self.assertTrue(pathlib.Path(e.env[key]).is_relative_to(e.tmp), key)
            self.assertTrue(pathlib.Path(e.env["TMPDIR"]).is_dir())
            self.assertTrue(e.downloads.is_relative_to(e.home))
            self.assertEqual(e.env["OFFICE_WINDOWS_USERS"], "")
            self.assertNotIn("XDG_DOWNLOAD_DIR", e.env)
        self.assertNotEqual(a.env["HOME"], b.env["HOME"])
        # A command run through it makes its temporary files there.
        out = subprocess.run(["sh", "-c", 'mktemp -d "${TMPDIR:?}/x.XXXXXX"'], env=a.env, capture_output=True,
                             text=True, check=True).stdout.strip()
        self.assertTrue(pathlib.Path(out).is_relative_to(a.tmpdir), out)

    def test_this_process_lends_the_env_and_gives_it_back(self):
        import tempfile
        e = Env(self)
        before = (dict(os.environ), tempfile.tempdir)
        with e.this_process():
            self.assertEqual(h.expand_project_path("~/x"), e.home / "x")
            self.assertTrue(pathlib.Path(tempfile.mkdtemp()).is_relative_to(e.tmpdir))
            self.assertEqual(os.environ["XDG_CONFIG_HOME"], e.env["XDG_CONFIG_HOME"])
        self.assertEqual((dict(os.environ), tempfile.tempdir), before)

    def test_every_job_runs_with_a_home_and_tmpdir_of_its_own(self):
        e = Env(self)
        base = {"PATH": "/usr/bin:/bin", "HOME": "/home/someone", "TMPDIR": "/var/x", "XDG_DOWNLOAD_DIR": "/d",
                "XDG_CONFIG_HOME": "/home/someone/.config", "OFFICE_ROOT": "/home/someone/office",
                "OFFICE_DEBUG": "1", "OFFICE_TEST_JOBS": "2", "LC_ALL": "C.UTF-8"}
        env = runner.isolated_env(base, e.tmp / "job")
        for key in ("HOME", "TMPDIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME",
                    "GIT_CONFIG_GLOBAL"):
            self.assertTrue(pathlib.Path(env[key]).is_relative_to(e.tmp / "job"), key)
            self.assertTrue(pathlib.Path(env[key]).exists(), key)
        self.assertEqual(pathlib.Path(env["GIT_CONFIG_GLOBAL"]).read_text(), "")
        for gone in ("XDG_DOWNLOAD_DIR", "OFFICE_ROOT", "OFFICE_DEBUG"):
            self.assertNotIn(gone, env)
        self.assertEqual((env["PATH"], env["LC_ALL"], env["OFFICE_TEST_JOBS"], env["OFFICE_WINDOWS_USERS"],
                          env["GIT_CONFIG_NOSYSTEM"]), ("/usr/bin:/bin", "C.UTF-8", "2", "", "1"))
        self.assertEqual(env["OFFICE_TESTS_UNDER_RUNNER"], "1")
        # This very test runs in such a job when the runner runs it: its
        # TMPDIR (and HOME beside it) is the runner's scratch, not the one
        # the runner was started with. Under bare unittest discover there
        # is no runner to say, and nothing to check.
        if os.environ.get("OFFICE_TESTS_UNDER_RUNNER"):
            self.assertIn("office-tests-scratch.", os.environ.get("TMPDIR", ""))


class TestTheFastTier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tier = runner.load_tier()
        cls.verbs = runner.dispatcher_verbs()
        cls.jobs = runner.plan(runner.module_names())
        cls.ids = {i for v in cls.jobs.values() for i in v}

    def test_the_tier_holds_together(self):
        self.assertEqual(runner.tier_problems(self.tier, self.ids, self.verbs), [])
        self.assertEqual(self.tier["budget_seconds"], 120)

    def test_every_verb_the_command_dispatches_has_an_entry_point(self):
        self.assertGreaterEqual(len(self.verbs), 30)
        for verb in ("walk-in", "init", "start", "land", "deliver", "letterhead", "version", "help", "tour"):
            self.assertIn(verb, self.verbs)
        self.assertEqual(set(self.tier["entry_points"]), self.verbs)

    def test_each_entry_point_test_runs_its_verb(self):
        """Each named test is one test, by its id, whose own source calls
        the command with the verb as its first word, through the suite's
        helpers (e.run("land", ...), run_office, an Office's run), a helper
        named for the verb (self.start(...), self.o.open(...)) or a
        command line ([.../office, "version"]): the tier cannot claim a
        verb its tests never type. The walk-in is the command with no
        word at all."""
        for verb, names in self.tier["entry_points"].items():
            for test_id in names:
                self.assertIn(test_id, self.ids, "an entry point is one test, by its id")
                module, cls, method = test_id.split(".")
                src = inspect.getsource(getattr(getattr(__import__(module), cls), method))
                self.assertRegex(src, entry_call(verb), f"{test_id} never runs {verb}")

    def test_the_entry_call_pattern_tells_a_run_from_a_mention(self):
        self.assertRegex('self.e.run("land", sid)', entry_call("land"))
        self.assertRegex('proc = run_office("deliver", self.name)', entry_call("deliver"))
        self.assertRegex('subprocess.run([str(REPO / "bin/office"), "help"])', entry_call("help"))
        self.assertRegex('o.run(cwd=self.root)', entry_call("walk-in"))
        self.assertRegex('walk = o.run().stdout', entry_call("walk-in"))
        self.assertRegex('proc = self.start("fix", "--on", "alpha")', entry_call("start"))
        self.assertRegex('folder = self.o.open("--title", "x")', entry_call("open"))
        for mention in ('verbs["land"]', 'self.assertIn("land", text)', 'e.run("landed")', 'self.landing()',
                        'tarfile.open(tb)'):
            self.assertNotRegex(mention, entry_call("land"))

    def test_the_tier_is_a_part_of_the_suite_and_holds_this_module(self):
        held = runner.tier_ids(self.tier, self.ids)
        self.assertLess(len(held), len(self.ids) / 2)
        self.assertTrue(all(i in held for i in self.ids if i.startswith("test_suite_clock.")))

    def test_a_tier_that_names_a_missing_test_or_misses_a_verb_says_so(self):
        tier = {"budget_seconds": 1, "entry_points": {"walk-in": ["test_x.T.test_a"], "gone": ["test_x.T"]},
                "also": ["test_y"]}
        problems = runner.tier_problems(tier, {"test_x.T.test_a"}, {"walk-in", "land"})
        self.assertIn("the verb land has no entry point in the fast tier (add a test that runs it)", problems)
        self.assertIn("the fast tier names an entry point for gone, which bin/office does not dispatch", problems)
        self.assertIn("also.tests: test_y is no test, class or module of the suite", problems)
        self.assertEqual(len(problems), 3, problems)
        self.assertEqual(runner.matching("test_x", {"test_x.T.a", "test_xy.T.a"}), {"test_x.T.a"})

    def test_a_tier_file_that_does_not_read_is_named(self):
        d = Env(self).tmp
        for text, words in (("budget_seconds = 0\n", "budget_seconds"),
                            ("budget_seconds = 5\n", "[entry_points]"),
                            ("budget_seconds = 5\n[entry_points]\nland = []\n", "entry_points.land"),
                            ("budget_seconds = [\n", "fast-tier.toml")):
            (d / "fast-tier.toml").write_text(text)
            with self.assertRaises(ValueError) as cm:
                runner.load_tier(d / "fast-tier.toml")
            self.assertIn(words, str(cm.exception))

    def test_the_dispatcher_is_read_or_refused(self):
        d = Env(self).tmp
        (d / "office").write_text('main() {\n  case "$verb" in\n    init) cmd_init "$@" ;;\n'
                                  '    help|--help|-h) cmd_help "$@" ;;\n    *) usage ;;\n  esac\n}\n')
        self.assertEqual(runner.dispatcher_verbs(d / "office"), {"walk-in", "init", "help"})
        (d / "office").write_text("echo nothing\n")
        with self.assertRaises(ValueError):
            runner.dispatcher_verbs(d / "office")

    def test_run_sh_fast_plans_the_tier_and_refuses_a_name_it_does_not_know(self):
        plan = subprocess.run([str(TESTS / "run.sh"), "--fast", "--plan"], capture_output=True, text=True,
                              timeout=120)
        self.assertEqual(plan.returncode, 0, plan.stderr)
        counted = sum(int(l.split("\t")[1]) for l in plan.stdout.splitlines())
        self.assertEqual(counted, sum(1 for _ in runner.tier_ids(self.tier, self.ids)) + self.duplicates())
        more = subprocess.run([str(TESTS / "run.sh"), "--fast", "--plan", "test_filed_append_only"],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(more.returncode, 0, more.stderr)
        self.assertIn("test_filed_append_only\t12", more.stdout)
        no = subprocess.run([str(TESTS / "run.sh"), "--fast", "test_nothing.T"], capture_output=True, text=True,
                            timeout=120)
        self.assertEqual(no.returncode, 2)
        self.assertIn("test_nothing.T, named after --fast, is no test, class or module of the suite", no.stderr)

    def duplicates(self):
        """Tier tests that run twice (an imported class runs again in the
        module that imports it, as under discover)."""
        held = runner.tier_ids(self.tier, self.ids)
        planned = [i for v in self.jobs.values() for i in v if i in held]
        return len(planned) - len(set(planned))


# A tiny repo for the runner to run: tests/ with the real runner and one
# module, so a detached run, a timed job and a budget can be watched end
# to end in seconds.
TINY_TEST = """import os, unittest
class T(unittest.TestCase):
    def test_quick(self):
        self.assertEqual(os.environ.get("OFFICE_TESTS_UNDER_RUNNER"), "1")
    def test_fails_when_asked(self):
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(__file__), "FAIL")))
"""


def tiny_repo(root, fail=False):
    (root / "tests").mkdir(parents=True)
    for name in ("run.sh", "runner.py"):
        shutil.copy2(TESTS / name, root / "tests" / name)
    (root / "tests" / "test_tiny.py").write_text(TINY_TEST)
    if fail:
        (root / "tests" / "FAIL").write_text("")
    return root


def wait_for(path, pattern, seconds=90):
    """The text of path once it matches pattern, or the last text read."""
    deadline, text = time.monotonic() + seconds, ""
    while time.monotonic() < deadline:
        text = path.read_text() if path.is_file() else ""
        if re.search(pattern, text):
            return text
        time.sleep(0.2)
    return text


class TestTheRunnersClock(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)

    def run_sh(self, root, *args, extra=None, timeout=120):
        env = dict(self.e.env, XDG_STATE_HOME=str(self.e.tmp / "state"), **(extra or {}))
        return subprocess.run([str(root / "tests" / "run.sh"), *args], cwd=root, env=env, capture_output=True,
                              text=True, timeout=timeout)

    def test_a_job_records_each_tests_time_and_the_run_writes_them_slowest_first(self):
        root = tiny_repo(self.e.tmp / "repo")
        logs = self.e.tmp / "logs"
        proc = self.run_sh(root, "--logs", str(logs))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads((logs / "test_tiny.json").read_text())
        self.assertEqual(sorted(data["durations"]), ["test_tiny.T.test_fails_when_asked", "test_tiny.T.test_quick"])
        rows = [l.split("\t") for l in (logs / "times.tsv").read_text().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertGreaterEqual(float(rows[0][1]), float(rows[1][1]))
        self.assertIn(f"each test's time, slowest first: {logs / 'times.tsv'}", proc.stdout)
        # Each job's HOME and TMPDIR were the runner's own, and are gone.
        scratch = re.search(r"HOME and TMPDIR under (\S+)", proc.stdout).group(1)
        self.assertFalse(pathlib.Path(scratch).exists())

    def test_detach_returns_at_once_with_one_line_and_the_verdict_follows(self):
        root = tiny_repo(self.e.tmp / "repo")
        started = time.monotonic()
        proc = self.run_sh(root, "--detach", timeout=60)
        took = time.monotonic() - started
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertLess(took, 30)
        self.assertEqual(len(proc.stdout.splitlines()), 1, proc.stdout)
        m = re.fullmatch(r"\[run\] the whole suite is running detached \(pid \d+\); its verdict will be in (\S+), "
                         r"its log in (\S+)\n", proc.stdout)
        self.assertIsNotNone(m, proc.stdout)
        verdict, log = pathlib.Path(m.group(1)), pathlib.Path(m.group(2))
        state = self.e.tmp / "state" / "office-src" / "suite"
        self.assertTrue(verdict.is_relative_to(state))
        self.assertFalse(verdict.is_relative_to(root))
        self.assertEqual((state / "latest").resolve(), verdict.parent.resolve())
        text = wait_for(verdict, r"^(OK|FAILED|BROKEN) ")
        self.assertRegex(text, r"^OK \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ: 2 tests passed in \d+s, not a git checkout\n$",
                         log.read_text() if log.is_file() else "no log")
        self.assertEqual(len(text.splitlines()), 1)
        self.assertIn("[run] OK (2 tests run)", log.read_text())
        self.assertTrue(wait_for_gone(verdict.parent / "tree"), "the copy was not removed")
        self.assertTrue(wait_for_exit(int(re.search(r"pid (\d+)", proc.stdout).group(1))))
        self.assertTrue((verdict.parent / "logs" / "test_tiny.log").is_file())

    def test_a_failing_detached_run_says_so_in_its_verdict(self):
        root = tiny_repo(self.e.tmp / "repo", fail=True)
        proc = self.run_sh(root, "--detach", timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        verdict = pathlib.Path(re.search(r"verdict will be in (\S+),", proc.stdout).group(1))
        text = wait_for(verdict, r"^(OK|FAILED|BROKEN) ")
        self.assertRegex(text, r"^FAILED \S+: 1 of 2 tests failed, in \d+s, not a git checkout; read \S+run\.log\n$")
        self.assertTrue(wait_for_exit(int(re.search(r"pid (\d+)", proc.stdout).group(1))))

    def test_detach_runs_with_sigint_restored_and_refuses_what_it_does_not_take(self):
        self.assertIn("--detach", "\n".join(runner.sigint_warning(__import__("signal").SIG_IGN)))
        root = tiny_repo(self.e.tmp / "repo")
        for args in (("--detach", "test_tiny"), ("--detach", "--plan"), ("--detach", "--fast")):
            proc = self.run_sh(root, *args)
            self.assertEqual(proc.returncode, 2, args)
        self.assertFalse((self.e.tmp / "state").exists())

    def test_old_runs_are_pruned_and_latest_is_kept(self):
        state = self.e.tmp / "suite"
        state.mkdir()
        for i in range(13):
            (state / f"202610{i + 1:02d}T000000Z-{i}").mkdir()
        (state / "notes").mkdir()
        gone = runner.prune(state, keep=10)
        self.assertEqual(sorted(gone), [f"202610{i + 1:02d}T000000Z-{i}" for i in range(3)])
        self.assertTrue((state / "notes").is_dir())
        runner.point_latest(state, state / "20261013T000000Z-12")
        runner.point_latest(state, state / "20261012T000000Z-11")
        self.assertEqual(os.readlink(state / "latest"), "20261012T000000Z-11")

    def test_the_fast_tier_fails_past_its_budget(self):
        root = tiny_repo(self.e.tmp / "repo")
        (root / "bin").mkdir()
        (root / "bin" / "office").write_text('main() {\n  case "$verb" in\n    init) cmd_init "$@" ;;\n  esac\n}\n')
        tier = root / "tests" / "fast-tier.toml"
        tier.write_text('budget_seconds = 1\n[entry_points]\nwalk-in = ["test_tiny.T.test_quick"]\n'
                        'init = ["test_tiny.T.test_quick"]\n')
        slow = root / "tests" / "test_tiny.py"
        slow.write_text(slow.read_text().replace("def test_quick(self):\n",
                                                 "def test_quick(self):\n        import time; time.sleep(1.5)\n"))
        proc = self.run_sh(root, "--fast")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertRegex(proc.stdout, r"the fast tier took \d+\.\ds of wall clock, 1 of the suite's 2 tests; "
                                      r"its budget is 1s")
        self.assertIn("the fast tier ran over its budget", proc.stderr)
        tier.write_text(tier.read_text().replace("budget_seconds = 1", "budget_seconds = 100"))
        proc = self.run_sh(root, "--fast")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # A verb the dispatcher gains with no entry point stops the tier.
        (root / "bin" / "office").write_text('main() {\n  case "$verb" in\n    init) cmd_init "$@" ;;\n'
                                             '    land) cmd_land "$@" ;;\n  esac\n}\n')
        proc = self.run_sh(root, "--fast")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("the verb land has no entry point in the fast tier", proc.stderr)


def wait_for_exit(pid, seconds=30):
    """True once the process has exited (gone, or a zombie nobody reaped)."""
    deadline = time.monotonic() + seconds
    stat = pathlib.Path(f"/proc/{pid}/stat")
    while time.monotonic() < deadline:
        try:
            if stat.read_text().rsplit(")", 1)[1].split()[0] == "Z":
                return True
        except (OSError, IndexError):
            return True
        time.sleep(0.2)
    return False


def wait_for_gone(path, seconds=30):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not path.exists():
            return True
        time.sleep(0.2)
    return False


class TestTheRecord(unittest.TestCase):
    def test_the_version_the_releases_and_the_readme(self):
        version = (REPO / "VERSION").read_text().strip()
        releases = (REPO / "RELEASES.md").read_text()
        self.assertTrue(releases.split("\n## ", 1)[1].startswith(version), "RELEASES.md's newest entry is VERSION")
        readme = " ".join((REPO / "README.md").read_text().split())
        tests = readme.split("## Tests", 1)[1].split(" ## ", 1)[0]
        for words in ("tests/run.sh --fast", "tests/run.sh --detach", "fast-tier.toml", "two minutes",
                      "verdict"):
            self.assertIn(words, tests)
        sheet = (REPO / ("cla" + "ude") / "context" / "front-sheet.md").read_text()
        clock = sheet.split("## The suite's clock", 1)[1].split("\n## ", 1)[0]
        for words in ("--fast", "--slow", "Env", "test_suite_clock.py", "--detach", "120 seconds"):
            self.assertIn(words, clock)
        self.assertIn(f"- {version} (session", sheet)
