#!/usr/bin/env python3
"""The suite, side by side: tests/run.sh's engine.

The test modules share nothing (each test builds its own temporary HOME,
offices, installs and fake bales), and almost all of a run is git and
bin/office subprocesses waiting on each other, so each module runs as its
own process, a few at a time. The classes that drive a pseudo-terminal
(the tour, the wizards, the terminal starts) name themselves with a class
attribute, serial_group = "terminal", and run one after another in one
process of their own, its own lane beside the modules, since their
waits are timing-sensitive.

Every test discover would run is run, as many times as discover would
run it (an imported TestCase class runs again in the module that imports
it, as under discover): each
module's tests are loaded with unittest's own loadTestsFromModule, the
way discover loads them, and split into the serial group and the rest.
The plan's count is held to discover's before anything runs.

The suite's clock (0.17.1). Four ways to run it:

- the whole suite (no flag), side by side, as above;
- --fast, the fast tier: the tests tests/fast-tier.toml names, held to
  the same plan and to discover the same way, plus any module, class or
  test named after it (a session adds what it touched). Every verb the
  command's dispatcher knows (bin/office, main) has a test there that runs
  its entry point, and a verb with none stops the run before anything
  starts. The tier prints its wall time and fails past its budget
  (budget_seconds in the file, 120: bale's two minutes for validation);
- --detach, the whole suite in the background for after a landing: a copy
  of the tree is taken, the run starts in a session of its own at a lower
  priority and the command returns at once, printing one line that names
  the run's directory, outside the repo, under the state directory
  (XDG_STATE_HOME, else ~/.local/state, then office-src/suite/), where its
  log and its one-line verdict file are written; latest names the newest;
- --serial, one process, unittest discover -v, on the terminal.

Nothing a test runs reads the running machine's home or temporary
directory: every job, and the --serial run, is given a HOME, a TMPDIR and
XDG directories of its own under one scratch directory the runner makes
and removes, an empty global git config, no Windows users' homes to scan
for downloads, a machine that is not WSL and has no desktop program (so
no test writes the clipboard or opens a file manager), and none of the
caller's OFFICE_ settings (isolated_env). tests/test_suite_clock.py holds
the test files, and the office's own source, to the same rule.

Each job writes one log, <logs>/<job>.log (unittest -v's own output), and
one result, <logs>/<job>.json, which carries each test's time; the run
writes every test's time, slowest first, to <logs>/times.tsv.

The order the jobs start in (0.21.0). With four at a time, a long job
started last is the run's tail. So when the runner knows the last run's
times, it starts the longest jobs first: each job weighs the sum of its
tests' times in the newest finished detached run under the state
directory (its logs/times.tsv, kept there with its verdict), a test that
run did not time weighing the median of those it did. When it knows none
(a first run, a fresh HOME, bale's sandbox), it runs as before: the
serial group first, then the modules by source size. The runner reads
those times before any job starts; no job can, since each has a state
directory of its own (isolated_env), so the suite's rule against reading
the machine holds wherever the times are kept. The run says which order
it took, in one line.

The bytecode cache (0.21.0). Most of a test's time was Python compiling
the office's own modules again on every helper call: the command runs
them with -B, so nothing is written beside an install, and nothing was
ever read back either. The runner compiles lib/ and tests/ once per run
into a cache in its scratch directory (PYTHONPYCACHEPREFIX, with links to
the interpreter's own compiled standard library, which a prefix would
otherwise hide), and every job and every command a test runs reads it
there. The cache is checked against each source's size and time as
always, so a copy or an edit compiles afresh; nothing writes to it but
the runner, and it goes with the scratch directory. The summary
names every job, its counts, its time and its log, and for a failing job
the failing tests, each with its traceback (its last TRACEBACK_LINES
lines, where the exception is), and the log to read: a log under the temp
directory can be gone by the time anyone reads it (WSL empties /tmp on a
restart), and the summary is what a relay carries.

Exit: 0 every test passed (and the fast tier within its budget), 1 a test
failed or errored (or the fast tier ran over its budget), 2 the runner
could not run or read a job (said on stderr).

Standard library only.
"""

import argparse
import concurrent.futures
import datetime
import importlib
import json
import os
import pathlib
import py_compile
import re
import shutil
import signal
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
import tomllib
import traceback
import unittest

TESTS = pathlib.Path(__file__).resolve().parent
SERIAL_ATTR = "serial_group"
SERIAL_JOB = "serial-terminal"
DEFAULT_JOBS = 4
# A failing test's traceback in the summary: its last lines, the
# exception and the frames nearest it.
TRACEBACK_LINES = 40
# A run started with SIGINT ignored (a background job from a non-interactive
# shell: `tests/run.sh &`) hands that to every process it starts. Until
# 0.26.0 that failed the tour's interrupt test, and the runner warned of it;
# the pty helper that test drives now starts its program with SIGINT at its
# default, as a terminal does (tests/test_front_door.py run_on_a_pty), so a
# run in the background needs no warning. --detach still restores it.
# The fast tier: one file, beside the tests it names.
TIER_FILE = "fast-tier.toml"
# The no-argument call of the command, the walk-in, named in the tier's
# entry points beside the verbs.
WALK_IN = "walk-in"
# What a detached run keeps, newest first; older run directories go.
DETACHED_KEEP = 10
# A detached run's priority, below the occupant's own work.
DETACHED_NICE = 10
# The caller's settings a job keeps: the job count. Every other OFFICE_
# variable (OFFICE_ROOT, OFFICE_DEBUG, ...) would point a test at the
# running machine's office or change what the command prints.
KEEP_OFFICE_VARS = ("OFFICE_TEST_JOBS",)
# The programs a job takes from the running machine's PATH: git, python3,
# a shell and the coreutils, and iconv (the C library's, which turns text
# to UTF-16 for clip.exe). Everything else a test runs is in its own tree:
# the fake bale and the fake ssh first on its PATH, a fake desktop program
# in its Env's desktop. tests/test_suite_clock.py holds the office's source
# to this list: a program the office looks up on the PATH is one of these,
# the suite's fake, or a desktop program found through the one door the
# Env steers (bin/office desktop_tool, lib/office_helper.py desktop_which).
COREUTILS = (
    "arch", "b2sum", "base32", "base64", "basename", "basenc", "cat", "chcon", "chgrp", "chmod", "chown",
    "chroot", "cksum", "comm", "cp", "csplit", "cut", "date", "dd", "df", "dir", "dircolors", "dirname", "du",
    "echo", "env", "expand", "expr", "factor", "false", "fmt", "fold", "groups", "head", "hostid", "id",
    "install", "join", "kill", "link", "ln", "logname", "ls", "md5sum", "mkdir", "mkfifo", "mknod", "mktemp",
    "mv", "nice", "nl", "nohup", "nproc", "numfmt", "od", "paste", "pathchk", "pinky", "pr", "printenv",
    "printf", "ptx", "pwd", "readlink", "realpath", "rm", "rmdir", "runcon", "seq", "sha1sum", "sha224sum",
    "sha256sum", "sha384sum", "sha512sum", "shred", "shuf", "sleep", "sort", "split", "stat", "stdbuf", "stty",
    "sum", "sync", "tac", "tail", "tee", "test", "timeout", "touch", "tr", "true", "truncate", "tsort", "tty",
    "uname", "unexpand", "uniq", "users", "vdir", "wc", "who", "whoami", "yes",
)
DECLARED_TOOLS = ("git", "python3", "bash", "sh", "iconv") + COREUTILS
# What every job is told of the desktop it runs on (bin/office on_wsl and
# desktop_tool read these): not WSL, and no desktop program anywhere. An
# Env gives each test a desktop directory of its own in their place.
DESKTOP_VARS = {"OFFICE_PROC_VERSION": "", "OFFICE_DESKTOP_PATH": ""}
# What every job is told of the tools the survey records (0.27.0; bin/office
# survey_which and container_marker read these): no directory to look in,
# so no survey runs a program of the machine's for its version, and no
# container marker. An Env sets the same.
SURVEY_VARS = {"OFFICE_SURVEY_PATH": "", "OFFICE_CONTAINER_MARKER": ""}
# The variable that names the run's bytecode cache to every job, and so
# to every command a test runs (tests/test_office.py Env passes it on).
PYCACHE_VAR = "PYTHONPYCACHEPREFIX"
# A finished detached run, by the first word of its verdict: its times are
# whole. RUNNING has none yet, and BROKEN may have none.
FINISHED_VERDICTS = ("OK", "FAILED")
_print_lock = threading.Lock()


def say(msg):
    with _print_lock:
        print(f"[run] {msg}", flush=True)


def module_names(tests_dir=None):
    """Every test module discover would load: test*.py at the top of tests/."""
    tests_dir = TESTS if tests_dir is None else tests_dir
    return sorted(p.stem for p in tests_dir.glob("test*.py") if p.is_file())


def flatten(suite):
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            yield from flatten(t)
        else:
            yield t


def is_serial(test):
    return getattr(type(test), SERIAL_ATTR, None) is not None


def load_module_tests(name):
    """(serial tests, the rest) of one module, loaded as discover loads it."""
    if str(TESTS) not in sys.path:
        sys.path.insert(0, str(TESTS))
    mod = importlib.import_module(name)
    tests = list(flatten(unittest.defaultTestLoader.loadTestsFromModule(mod)))
    return [t for t in tests if is_serial(t)], [t for t in tests if not is_serial(t)]


def plan(names, keep=None):
    """{job: [test ids]}: one job per module with tests outside the serial
    group, and the serial group, in module order, as one job. keep, when
    given, is the set of test ids to run (the fast tier); a module none of
    whose tests it holds gets no job."""
    jobs, serial = {}, []
    for name in names:
        s, rest = load_module_tests(name)
        serial += [t.id() for t in s if keep is None or t.id() in keep]
        rest = [t.id() for t in rest if keep is None or t.id() in keep]
        if rest:
            jobs[name] = rest
    if serial:
        jobs[SERIAL_JOB] = serial
    return jobs


def discover_ids():
    """The id of every test unittest discover -s tests finds, as often as
    it finds it."""
    loader = unittest.TestLoader()
    return [t.id() for t in flatten(loader.discover(str(TESTS), top_level_dir=str(TESTS)))]


def discover_count():
    """How many tests unittest discover -s tests finds: the plan must match."""
    return len(discover_ids())


# --- the fast tier ---------------------------------------------------------------------

def load_tier(path=None):
    """The fast tier as tests/fast-tier.toml declares it: {"budget_seconds":
    int, "entry_points": {verb: [name, ...]}, "also": [name, ...]}, where a
    name is a module, a class (module.Class) or a test's id. A file that
    does not read, or does not have that shape, is a ValueError naming
    what is wrong."""
    path = pathlib.Path(path) if path else TESTS / TIER_FILE
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc
    budget = data.get("budget_seconds")
    if not isinstance(budget, int) or budget <= 0:
        raise ValueError(f"{path}: budget_seconds is a whole number of seconds above 0, not {budget!r}")
    entry = data.get("entry_points")
    if not isinstance(entry, dict) or not entry:
        raise ValueError(f"{path}: [entry_points] maps each verb to the tests that run it")
    for verb, names in entry.items():
        if not isinstance(names, list) or not names or not all(isinstance(n, str) and n for n in names):
            raise ValueError(f"{path}: entry_points.{verb} is a list of one or more test names, not {names!r}")
    also = data.get("also", {}).get("tests", [])
    if not isinstance(also, list) or not all(isinstance(n, str) and n for n in also):
        raise ValueError(f"{path}: also.tests is a list of test names, not {also!r}")
    return {"budget_seconds": budget, "entry_points": entry, "also": also}


def dispatcher_verbs(office=None):
    """Every verb bin/office's main() dispatches, by its first spelling
    (version|--version|-V is version), and the walk-in: the entry points
    the fast tier must exercise. A dispatcher this cannot find is a
    ValueError, so a change to main()'s shape stops the tier rather than
    emptying it."""
    office = pathlib.Path(office) if office else TESTS.parent / "bin" / "office"
    text = office.read_text(encoding="utf-8")
    try:
        body = re.split(r"(?m)^main\(\) \{", text, maxsplit=1)[1]
        cases = body.split('case "$verb" in', 1)[1].split("\n  esac", 1)[0]
    except IndexError:
        raise ValueError(f"{office}: no main() with a case \"$verb\" in it, so the verbs cannot be read") from None
    verbs = {m.group(1).split("|")[0] for m in re.finditer(r"^\s+([A-Za-z][\w|-]*)\)\s*cmd_\w+", cases, re.M)}
    if not verbs:
        raise ValueError(f"{office}: main()'s case \"$verb\" names no verb")
    return {WALK_IN} | verbs


def matching(name, ids):
    """The ids a name stands for: the test of that id, or every test of
    that module or class (the ids under name + '.')."""
    return {i for i in ids if i == name or i.startswith(name + ".")}


def tier_problems(tier, ids, verbs):
    """What is wrong with the tier against the suite's ids and the
    dispatcher's verbs, one line each; [] when it is sound."""
    out = []
    for verb in sorted(verbs - set(tier["entry_points"])):
        out.append(f"the verb {verb} has no entry point in the fast tier (add a test that runs it)")
    for verb in sorted(set(tier["entry_points"]) - verbs):
        out.append(f"the fast tier names an entry point for {verb}, which bin/office does not dispatch")
    for where, names in [*((f"entry_points.{v}", n) for v, n in tier["entry_points"].items()),
                         ("also.tests", tier["also"])]:
        for name in names:
            if not matching(name, ids):
                out.append(f"{where}: {name} is no test, class or module of the suite")
    return out


def tier_ids(tier, ids):
    """Every test id the tier holds."""
    names = [n for v in tier["entry_points"].values() for n in v] + tier["also"]
    return set().union(*(matching(n, ids) for n in names)) if names else set()


# --- what every job is given in place of the machine ----------------------------------

def isolated_env(base, root, pycache=None):
    """The environment a job (or the --serial run) runs under, made under
    root: its own HOME (with an empty global git config), TMPDIR and XDG
    config, data, state and cache directories; no Windows users' homes to
    scan for downloads (OFFICE_WINDOWS_USERS empty), a machine that is not
    WSL with no desktop program on it (DESKTOP_VARS), a survey that looks
    for no tool and no container marker (SURVEY_VARS), and no XDG variable
    of the caller's (XDG_DOWNLOAD_DIR among them); none of the caller's
    OFFICE_ settings but the job count. PATH and the locale stay: the suite
    needs the programs DECLARED_TOOLS names, and reads nothing else
    through them. pycache, when given, is the run's bytecode cache
    (seed_bytecode), named in PYTHONPYCACHEPREFIX; a caller's own
    PYTHONPYCACHEPREFIX never reaches a job."""
    root = pathlib.Path(root)
    home, tmp = root / "home", root / "tmp"
    dirs = {"XDG_CONFIG_HOME": home / ".config", "XDG_DATA_HOME": home / ".local" / "share",
            "XDG_STATE_HOME": home / ".local" / "state", "XDG_CACHE_HOME": home / ".cache"}
    for d in (home, tmp, *dirs.values()):
        d.mkdir(parents=True, exist_ok=True)
    gitconfig = home / ".gitconfig-empty"
    gitconfig.write_text("", encoding="utf-8")
    env = {k: v for k, v in base.items()
           if not k.startswith("XDG_") and not (k.startswith("OFFICE_") and k not in KEEP_OFFICE_VARS)
           and k != PYCACHE_VAR}
    if pycache is not None:
        env[PYCACHE_VAR] = str(pycache)
    env.update({k: str(v) for k, v in dirs.items()})
    env.update({"HOME": str(home), "TMPDIR": str(tmp), "OFFICE_WINDOWS_USERS": "", **DESKTOP_VARS, **SURVEY_VARS,
                "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": str(gitconfig),
                "PYTHONDONTWRITEBYTECODE": "1", "OFFICE_TESTS_UNDER_RUNNER": "1"})
    return env


# --- the run's bytecode cache ------------------------------------------------------

def cached_pyc(prefix, source):
    """Where the interpreter looks for source's compiled code under the
    cache prefix: the source's directory mirrored under it, as
    importlib.util.cache_from_source does with sys.pycache_prefix."""
    source = pathlib.Path(source).resolve()
    return pathlib.Path(prefix) / source.parent.relative_to(source.anchor) / \
        f"{source.stem}.{sys.implementation.cache_tag}.pyc"


def seed_bytecode(prefix, dirs=None):
    """Make the run's bytecode cache at prefix and return how many modules
    it compiled: every .py at the top of each of dirs (default: lib/,
    tests/ and tests/fakes/, the fake programs' modules, 0.27.0) compiled
    once, and a link to the compiled code the interpreter
    already holds for its standard library and for the modules it loads as
    it starts (site's), since a cache prefix is the only place it looks
    once one is set. A module that does not compile is skipped and said
    (its job says why again when it imports it); a cache that cannot be
    made at all raises OSError, and the caller runs without one."""
    prefix = pathlib.Path(prefix)
    prefix.mkdir(parents=True, exist_ok=True)
    tag = sys.implementation.cache_tag

    def link(source_dir, pyc):
        # As the interpreter names the source (cache_from_source joins the
        # prefix and the source's directory as found, unresolved).
        dest = prefix / pathlib.Path(source_dir).relative_to(pathlib.Path(source_dir).anchor) / pyc.name
        if not dest.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.symlink_to(pyc)

    # The tree's own modules first: a link below never stands in for one.
    compiled = 0
    for d in (dirs if dirs is not None else (TESTS.parent / "lib", TESTS, TESTS / "fakes")):
        for source in sorted(pathlib.Path(d).glob("*.py")):
            try:
                cfile = cached_pyc(prefix, source)
                if cfile.is_symlink():
                    cfile.unlink()
                py_compile.compile(str(source), cfile=str(cfile), doraise=True)
                compiled += 1
            except (py_compile.PyCompileError, OSError) as exc:
                why = f"{exc.exc_type_name}: {exc.exc_value}" if isinstance(exc, py_compile.PyCompileError) else exc
                say(f"warning: {source.name} was not compiled into the run's cache ({why})")
    stdlib = {sysconfig.get_paths().get(k) for k in ("stdlib", "platstdlib")} - {None}
    for root in sorted(stdlib):
        for pyc in pathlib.Path(root).rglob(f"__pycache__/*.{tag}.pyc"):
            link(pyc.parent.parent, pyc)
    for mod in list(sys.modules.values()):
        source, cached = getattr(mod, "__file__", None), getattr(mod, "__cached__", None)
        if source and cached and source.endswith(".py") and os.path.isfile(cached):
            link(os.path.dirname(source), pathlib.Path(cached))
    return compiled


def run_cache(scratch):
    """The run's bytecode cache under scratch, or None when it cannot be
    made (said, and the run goes on without it, as before 0.21.0). A tree
    with no lib/ of the office's (the runner's own tests run it on one) has
    nothing for a cache to save, and gets none."""
    if not any((TESTS.parent / "lib").glob("*.py")):
        return None
    prefix = pathlib.Path(scratch) / "pycache"
    try:
        n = seed_bytecode(prefix)
    except OSError as exc:
        say(f"warning: no bytecode cache this run ({exc}); every module compiles as it is imported")
        return None
    say(f"the office's modules, the tests and their fakes, {n} in all, compiled once into {prefix}")
    return prefix


# --- the last run's times --------------------------------------------------------

def last_times(state):
    """(times, run directory) from the newest finished detached run under
    the state directory: times is {job: {test id: seconds}}, read from that
    run's logs/times.tsv (write_times' rows). ({}, None) when there is no
    such run (a first run, a fresh HOME, bale's sandbox) or its times do
    not read; a line that does not read is skipped."""
    state = pathlib.Path(state)
    try:
        runs = sorted((p for p in state.iterdir() if p.is_dir() and not p.is_symlink()
                       and re.fullmatch(r"\d{8}T\d{6}Z-\d+", p.name)), reverse=True)
    except OSError:
        return {}, None
    for run in runs:
        try:
            verdict = (run / "verdict").read_text(encoding="utf-8").split(" ", 1)[0]
            rows = (run / "logs" / "times.tsv").read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        if verdict not in FINISHED_VERDICTS:
            continue
        times = {}
        for row in rows:
            parts = row.split("\t")
            if len(parts) != 3:
                continue
            try:
                times.setdefault(parts[2], {})[parts[0]] = float(parts[1])
            except ValueError:
                continue
        if times:
            return times, run
    return {}, None


def job_weights(jobs, times):
    """{job: expected seconds} from the last run's times: the sum of its
    tests' times in the same job, else in any job (a test that moved, a
    class an import runs twice), else the median of every time known."""
    anywhere = {}
    for per in times.values():
        for test, secs in per.items():
            anywhere[test] = max(secs, anywhere.get(test, 0.0))
    known = sorted(anywhere.values())
    median = known[len(known) // 2] if known else 0.0
    return {job: sum(times.get(job, {}).get(t, anywhere.get(t, median)) for t in tests)
            for job, tests in jobs.items()}


# --- one job, in its own process -------------------------------------------------

class TimedResult(unittest.TextTestResult):
    """unittest -v's result, keeping each test's wall time by its id (in
    test_seconds: unittest's own `durations` is the runner's flag for its
    slowest-tests report, a different thing)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_seconds = {}
        self._started = {}

    def startTest(self, test):
        self._started[id(test)] = time.monotonic()
        super().startTest(test)

    def stopTest(self, test):
        began = self._started.pop(id(test), None)
        if began is not None:
            # An id run twice (an imported class) keeps the sum of its runs.
            self.test_seconds[test.id()] = round(self.test_seconds.get(test.id(), 0) + time.monotonic() - began, 3)
        super().stopTest(test)


def run_job(job, names, result_path, keep=None):
    """Run one job's tests (the module's, or the serial group's; only
    those in keep when it is given) with unittest -v on this process's
    stdout, and write the result file."""
    serial = job == SERIAL_JOB
    tests = []
    for name in (names if serial else [job]):
        s, rest = load_module_tests(name)
        tests += s if serial else rest
    if keep is not None:
        tests = [t for t in tests if t.id() in keep]
    suite = unittest.TestSuite(tests)
    started = time.monotonic()
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2, resultclass=TimedResult)
    res = runner.run(suite)
    out = {"job": job, "run": res.testsRun,
           "failures": [t.id() for t, _ in res.failures],
           "errors": [t.id() for t, _ in res.errors],
           "tracebacks": {t.id(): tb for t, tb in [*res.failures, *res.errors]},
           "unexpected_successes": [t.id() for t in res.unexpectedSuccesses],
           "skipped": len(res.skipped), "seconds": round(time.monotonic() - started, 1),
           "durations": getattr(res, "test_seconds", {})}
    pathlib.Path(result_path).write_text(json.dumps(out) + "\n", encoding="utf-8")
    return 0 if res.wasSuccessful() else 1


# --- the run --------------------------------------------------------------------------

def order(jobs, sizes=None, times=None):
    """Longest first. With the last run's times (last_times), by each job's
    weight from them (job_weights), the serial group weighed like any job,
    ties by name. Without them, as before: the serial group, then modules
    by source size (the best guess of a module's time before it has run)."""
    if times:
        weights = job_weights(jobs, times)
        return sorted(jobs, key=lambda job: (-weights[job], job))
    sizes = sizes or {}

    def weight(job):
        if job == SERIAL_JOB:
            return float("inf")
        return sizes.get(job, (TESTS / f"{job}.py").stat().st_size if (TESTS / f"{job}.py").exists() else 0)
    return sorted(jobs, key=weight, reverse=True)


def launch(job, names, logs, env, keep_file=None):
    log = logs / f"{job}.log"
    result = logs / f"{job}.json"
    argv = [sys.executable, "-B", str(pathlib.Path(__file__).resolve()), "--job", job, "--result", str(result),
            *(["--modules", *names] if job == SERIAL_JOB else []),
            *(["--keep", str(keep_file)] if keep_file else [])]
    say(f"started {job}")
    started = time.monotonic()
    with log.open("w", encoding="utf-8") as fh:
        proc = subprocess.run(argv, cwd=str(TESTS), env=env, stdin=subprocess.DEVNULL, stdout=fh,
                              stderr=subprocess.STDOUT)
    took = time.monotonic() - started
    try:
        data = json.loads(result.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        data = {"job": job, "run": 0, "failures": [], "errors": [], "unexpected_successes": [], "skipped": 0,
                "seconds": round(took, 1), "broken": f"no result ({exc}); exit {proc.returncode}"}
    data["exit"] = proc.returncode
    data["log"] = str(log)
    bad = len(data["failures"]) + len(data["errors"]) + len(data["unexpected_successes"])
    word = "broken" if data.get("broken") else ("FAILED" if bad or proc.returncode else "ok")
    say(f"{job}: {data['run']} tests, {word}, {data['seconds']}s")
    return data


def summary(results, total, took, logs):
    lines = ["", f"[run] the suite, side by side: {len(results)} jobs, {total} tests, {took:.0f}s; logs in {logs}"]
    width = max(len(r["job"]) for r in results) if results else 4
    for r in sorted(results, key=lambda r: r["job"]):
        bad = r["failures"] + r["errors"] + r["unexpected_successes"]
        state = "BROKEN" if r.get("broken") else ("FAILED" if bad or r["exit"] else "ok")
        lines.append(f"  {r['job']:<{width}}  {r['run']:>4} tests  {state:<6}  {r['seconds']:>7}s  {r['log']}")
    failing = [r for r in results if r.get("broken") or r["failures"] or r["errors"] or r["unexpected_successes"]
               or r["exit"]]
    for r in failing:
        lines.append(f"[run] {r['job']} failed; read {r['log']}")
        if r.get("broken"):
            lines.append(f"    {r['broken']}")
        for kind in ("failures", "errors", "unexpected_successes"):
            for t in r[kind]:
                lines.append(f"    {kind[:-1] if kind != 'unexpected_successes' else 'unexpected success'}: {t}")
                lines += traceback_lines((r.get("tracebacks") or {}).get(t), r["log"])
    lines.append("[run] " + ("FAILED" if failing else "OK") + f" ({sum(r['run'] for r in results)} tests run)")
    return lines, bool(failing)


def traceback_lines(tb, log):
    """A failing test's traceback for the summary, indented, capped at
    its last TRACEBACK_LINES lines with a line saying where the rest is;
    nothing when the job's result carries none."""
    if not tb:
        return []
    body = tb.rstrip("\n").splitlines()
    out = []
    if len(body) > TRACEBACK_LINES:
        out.append(f"      [{len(body) - TRACEBACK_LINES} lines above cut; the whole of it is in {log}]")
        body = body[-TRACEBACK_LINES:]
    return out + [f"      {l}" for l in body]


def write_times(results, path):
    """Every test's time, slowest first, as test<TAB>seconds<TAB>job: where
    a run's minutes went. Returns the path, or None when no job carried
    times (said by the caller)."""
    rows = [(t, s, r["job"]) for r in results for t, s in (r.get("durations") or {}).items()]
    if not rows:
        return None
    rows.sort(key=lambda row: -row[1])
    path = pathlib.Path(path)
    path.write_text("".join(f"{t}\t{s:.2f}\t{j}\n" for t, s, j in rows), encoding="utf-8")
    return path


def run_serial(env):
    """Today's run: one process, unittest discover, on the terminal (env is
    isolated_env's, the run's bytecode cache in it when there is one)."""
    say("one process, as before the side-by-side runner (--serial)")
    started = time.monotonic()
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(TESTS), "-v"],
                          cwd=str(TESTS.parent), env=env)
    say(f"{'OK' if proc.returncode == 0 else 'FAILED'} in {time.monotonic() - started:.0f}s")
    return 0 if proc.returncode == 0 else 1


def run_jobs(jobs, names, n, logs, env, scratch, keep_file=None, times=None, pycache=None):
    """Run the plan, longest first (order), each job under its own isolated
    environment in scratch, reading the run's bytecode cache when there is
    one, and print the summary. Returns (exit, outcome): outcome has the
    tests run, the number of tests that failed or errored and the seconds
    the run took."""
    started = time.monotonic()

    def one(i, job):
        # A neutral name, not the job's: a test's paths live under it, and
        # a test may assert a word (a module's subject) is absent from what
        # a command printed, paths included.
        return launch(job, names, logs, isolated_env(env, scratch / f"j{i}", pycache), keep_file)

    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(one, i, job) for i, job in enumerate(order(jobs, times=times), 1)]
        results = [f.result() for f in futures]
    took = time.monotonic() - started
    total = sum(len(v) for v in jobs.values())
    lines, failed = summary(results, total, took, logs)
    times = write_times(results, logs / "times.tsv")
    lines.insert(-1, f"[run] each test's time, slowest first: {times}" if times
                 else "[run] no job recorded its tests' times")
    print("\n".join(lines), flush=True)
    ran = sum(r["run"] for r in results)
    bad = sum(len(r["failures"]) + len(r["errors"]) + len(r["unexpected_successes"]) for r in results)
    broken = [r["job"] for r in results if r.get("broken")]
    outcome = {"run": ran, "planned": total, "bad": bad, "broken": broken, "seconds": round(took)}
    if not failed and ran != total:
        print(f"[run] error: {ran} tests ran, the plan held {total}", file=sys.stderr)
        return 2, outcome
    return (1 if failed else 0), outcome


def remove_scratch(scratch):
    """Remove the run's scratch directory, saying so when it cannot."""
    try:
        shutil.rmtree(scratch)
    except OSError as exc:
        print(f"[run] warning: the scratch directory {scratch} was not removed ({exc}); remove it by hand",
              file=sys.stderr)


# --- the detached run --------------------------------------------------------------

def state_dir(environ=None):
    """Where detached runs keep their logs and verdicts: office-src/suite
    under XDG_STATE_HOME, else under ~/.local/state. Outside every repo."""
    environ = os.environ if environ is None else environ
    base = environ.get("XDG_STATE_HOME") or os.path.join(environ.get("HOME") or os.path.expanduser("~"),
                                                         ".local", "state")
    return pathlib.Path(base) / "office-src" / "suite"


def source_line(repo):
    """What the run tests, in a few words: the commit the tree is at, and
    whether it had changes not committed; 'not a git checkout' else."""
    try:
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short=12", "HEAD"], capture_output=True,
                              text=True, timeout=30)
        dirty = subprocess.run(["git", "-C", str(repo), "status", "--porcelain"], capture_output=True, text=True,
                               timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"source not read ({exc})"
    if head.returncode != 0:
        return "not a git checkout"
    return f"at {head.stdout.strip()}" + (", with uncommitted changes" if dirty.stdout.strip() else "")


def write_verdict(run_dir, line):
    """The run's verdict file, one line, replaced whole (never half-written)."""
    tmp = run_dir / ".verdict.tmp"
    tmp.write_text(line.rstrip("\n") + "\n", encoding="utf-8")
    os.replace(tmp, run_dir / "verdict")


def point_latest(state, run_dir):
    """state/latest names the newest run, replaced whole."""
    tmp = state / ".latest.tmp"
    if tmp.is_symlink() or tmp.exists():
        tmp.unlink()
    tmp.symlink_to(run_dir.name)
    os.replace(tmp, state / "latest")


def prune(state, keep=DETACHED_KEEP):
    """Remove all but the newest keep run directories; the names removed."""
    runs = sorted((p for p in state.iterdir() if p.is_dir() and not p.is_symlink()
                   and re.fullmatch(r"\d{8}T\d{6}Z-\d+", p.name)), reverse=True)
    gone = []
    for old in runs[keep:]:
        shutil.rmtree(old, ignore_errors=True)
        gone.append(old.name)
    return gone


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def detach(jobs_flag, environ=None):
    """Start the whole suite in the background and return at once: a
    copy of the tree (the run tests what was there now, whatever happens
    to the checkout after), a run directory under the state directory with
    the verdict RUNNING in it, and the copy's runner started in a session
    of its own with no terminal, stdin, or output of the caller's. Prints
    one line. 0 once started, 2 when it could not start."""
    environ = dict(os.environ if environ is None else environ)
    repo = TESTS.parent
    state = state_dir(environ)
    run_dir = state / f"{utc_now():%Y%m%dT%H%M%SZ}-{os.getpid()}"
    try:
        run_dir.mkdir(parents=True)
        source = source_line(repo)
        (run_dir / "source").write_text(f"{repo} {source}\n", encoding="utf-8")
        shutil.copytree(repo, run_dir / "tree", symlinks=True,
                        ignore=shutil.ignore_patterns(".git", ".bale", "__pycache__"))
        write_verdict(run_dir, f"RUNNING since {utc_now():%Y-%m-%dT%H:%M:%SZ}: the whole suite, {source}")
        argv = [sys.executable, "-B", str(run_dir / "tree" / "tests" / "runner.py"), "--detached-child",
                str(run_dir), *(["--jobs", str(jobs_flag)] if jobs_flag else [])]
        with (run_dir / "run.log").open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(argv, cwd=str(run_dir), env=environ, stdin=subprocess.DEVNULL, stdout=log,
                                    stderr=subprocess.STDOUT, start_new_session=True, close_fds=True)
        point_latest(state, run_dir)
    except OSError as exc:
        print(f"[run] error: the detached run could not start in {run_dir}: {exc}", file=sys.stderr)
        return 2
    print(f"[run] the whole suite is running detached (pid {proc.pid}); its verdict will be in "
          f"{run_dir / 'verdict'}, its log in {run_dir / 'run.log'}", flush=True)
    return 0


def detached_child(run_dir, jobs_flag):
    """The detached run itself, in the copy: SIGINT back to its default (a
    run started from a background job inherits it ignored, and the
    interrupt tests would fail for that), a lower priority, the whole suite
    with its logs in the run directory, then the verdict, the copy
    removed and old runs pruned."""
    run_dir = pathlib.Path(run_dir)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    try:
        os.nice(DETACHED_NICE)
    except OSError as exc:
        say(f"running at the caller's priority ({exc})")
    source = (run_dir / "source").read_text(encoding="utf-8").split(" ", 1)[-1].strip() \
        if (run_dir / "source").is_file() else "source not recorded"
    say(f"detached run in {run_dir}, {source}")
    started = time.monotonic()
    try:
        code, outcome = whole_suite(run_dir / "logs", jobs_flag)
    except Exception:
        traceback.print_exc()
        code, outcome = 2, None
    took = round(time.monotonic() - started)
    stamp = f"{utc_now():%Y-%m-%dT%H:%M:%SZ}"
    log = run_dir / "run.log"
    if code == 0:
        verdict = f"OK {stamp}: {outcome['run']} tests passed in {took}s, {source}"
    elif code == 1 and outcome:
        verdict = (f"FAILED {stamp}: {outcome['bad']} of {outcome['run']} tests failed"
                   + (f", job(s) {', '.join(outcome['broken'])} broken" if outcome["broken"] else "")
                   + f", in {took}s, {source}; read {log}")
    else:
        verdict = f"BROKEN {stamp}: the runner could not run the suite (exit {code}) after {took}s, {source}; read {log}"
    write_verdict(run_dir, verdict)
    say(f"verdict: {verdict}")
    shutil.rmtree(run_dir / "tree", ignore_errors=True)
    if (run_dir / "tree").exists():
        say(f"warning: the copy {run_dir / 'tree'} was not removed; remove it by hand")
    for name in prune(run_dir.parent):
        say(f"removed an older run: {run_dir.parent / name}")
    return code


# --- the entry -------------------------------------------------------------------------

def whole_suite(logs, jobs_flag, env=None):
    """The whole suite, side by side, its plan held to discover's count."""
    env = dict(os.environ if env is None else env, PYTHONDONTWRITEBYTECODE="1")
    names = module_names()
    try:
        jobs = plan(names)
    except Exception:
        print("[run] error: the suite could not be loaded to plan the run:", file=sys.stderr)
        traceback.print_exc()
        return 2, None
    total = sum(len(v) for v in jobs.values())
    found = discover_count()
    if found != total:
        print(f"[run] error: the plan holds {total} tests and unittest discover finds {found}; "
              "run --serial and report this", file=sys.stderr)
        return 2, None
    return start_jobs(jobs, names, jobs_flag, logs, env)


def start_jobs(jobs, names, jobs_flag, logs, env, keep_file_ids=None, what="the suite"):
    n = jobs_flag or int(os.environ.get("OFFICE_TEST_JOBS", DEFAULT_JOBS) or DEFAULT_JOBS)
    if n < 1:
        print("[run] error: --jobs takes 1 or more", file=sys.stderr)
        return 2, None
    total = sum(len(v) for v in jobs.values())
    # Absolute: each job runs with tests/ as its directory, so a relative
    # path would name a different place there than here.
    logs = (pathlib.Path(logs) if logs else pathlib.Path(tempfile.mkdtemp(prefix="office-tests."))).resolve()
    logs.mkdir(parents=True, exist_ok=True)
    keep_file = None
    if keep_file_ids is not None:
        keep_file = logs / "keep.txt"
        keep_file.write_text("".join(f"{i}\n" for i in sorted(keep_file_ids)), encoding="utf-8")
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="office-tests-scratch."))
    say(f"{what}: {total} tests in {len(jobs)} jobs, {n} at a time"
        + (f"; the serial group ({len(jobs.get(SERIAL_JOB, []))} tests) runs in a lane of its own"
           if SERIAL_JOB in jobs else "") + f"; logs in {logs}; each job's HOME and TMPDIR under {scratch}")
    times, source = last_times(state_dir(env))
    say(order_line(source))
    try:
        return run_jobs(jobs, names, n, logs, env, scratch, keep_file, times, run_cache(scratch))
    finally:
        remove_scratch(scratch)


def order_line(source):
    """The run's one line on the order its jobs start in: the last run's
    times it read (source, a run directory), or none."""
    if source is not None:
        return f"jobs start longest first, by the last run's times ({source / 'logs' / 'times.tsv'})"
    return ("no earlier run's times here (a first run, a fresh HOME or a sandbox): the serial lane starts "
            "first, then the modules by size, as before")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tests/run.sh", description=(
        "Run office-src's test suite, each module as its own process, a few at a time, with the classes that "
        "drive a terminal (serial_group) one after another in a lane of their own. --fast runs the fast tier "
        "(tests/fast-tier.toml) within its budget, --detach the whole suite in the background, --serial the "
        "whole suite as one process."))
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--serial", action="store_true", help="one process: unittest discover -s tests -v")
    mode.add_argument("--fast", action="store_true",
                      help="the fast tier, plus the modules, classes or tests named after it; fails past the "
                           "tier's budget")
    mode.add_argument("--detach", action="store_true",
                      help="the whole suite in the background: prints one line naming its verdict file and "
                           "returns at once")
    ap.add_argument("--jobs", type=int, default=None,
                    help=f"processes at a time (default {DEFAULT_JOBS}, or OFFICE_TEST_JOBS)")
    ap.add_argument("--logs", default=None, help="directory for the logs (default: a new one under the temp dir)")
    ap.add_argument("--plan", action="store_true", help="print the jobs and their test counts; run nothing")
    ap.add_argument("modules", nargs="*", help="run only these modules (test_x), the serial group's share of them "
                                               "included; with --fast, modules, classes or tests added to the tier")
    ap.add_argument("--job", help=argparse.SUPPRESS)
    ap.add_argument("--result", help=argparse.SUPPRESS)
    ap.add_argument("--modules", dest="job_modules", nargs="*", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--keep", help=argparse.SUPPRESS)
    ap.add_argument("--detached-child", help=argparse.SUPPRESS)
    a = ap.parse_args(argv)

    if a.job:
        names = a.job_modules if a.job_modules is not None else module_names()
        keep = set(pathlib.Path(a.keep).read_text(encoding="utf-8").split()) if a.keep else None
        return run_job(a.job, names, a.result, keep)
    if a.detached_child:
        return detached_child(a.detached_child, a.jobs)

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if a.detach:
        if a.modules or a.plan or a.logs:
            print("[run] error: --detach runs the whole suite and keeps its logs under the state directory; "
                  "drop the module names, --plan and --logs", file=sys.stderr)
            return 2
        return detach(a.jobs)
    if a.serial:
        if a.modules:
            print("[run] error: --serial runs the whole suite; drop the module names", file=sys.stderr)
            return 2
        scratch = pathlib.Path(tempfile.mkdtemp(prefix="office-tests-scratch."))
        try:
            return run_serial(isolated_env(env, scratch / "j1", run_cache(scratch)))
        finally:
            remove_scratch(scratch)
    if a.fast:
        return fast(a, env)
    if not a.modules and not a.plan:
        code, _ = whole_suite(a.logs, a.jobs, env)
        return code

    names = module_names()
    if a.modules:
        unknown = [m for m in a.modules if m not in names]
        if unknown:
            print(f"[run] error: no such test module: {', '.join(unknown)} (they are: {', '.join(names)})",
                  file=sys.stderr)
            return 2
        names = [n for n in names if n in a.modules]
    try:
        jobs = plan(names)
    except Exception:
        print("[run] error: the suite could not be loaded to plan the run:", file=sys.stderr)
        traceback.print_exc()
        return 2
    total = sum(len(v) for v in jobs.values())
    if not a.modules:
        found = discover_count()
        if found != total:
            print(f"[run] error: the plan holds {total} tests and unittest discover finds {found}; "
                  "run --serial and report this", file=sys.stderr)
            return 2
    if a.plan:
        for job in order(jobs, times=last_times(state_dir(env))[0]):
            print(f"{job}\t{len(jobs[job])}")
        return 0
    code, _ = start_jobs(jobs, names, a.jobs, a.logs, env)
    return code


def fast(a, env):
    """--fast: the tier, held to the dispatcher, the plan and discover,
    plus what was named after it; its wall time printed and held to its
    budget."""
    started = time.monotonic()
    names = module_names()
    try:
        tier = load_tier()
        verbs = dispatcher_verbs()
        everything = plan(names)
    except ValueError as exc:
        print(f"[run] error: the fast tier cannot be read: {exc}", file=sys.stderr)
        return 2
    except Exception:
        print("[run] error: the suite could not be loaded to plan the run:", file=sys.stderr)
        traceback.print_exc()
        return 2
    ids = {i for v in everything.values() for i in v}
    problems = tier_problems(tier, ids, verbs)
    unknown = [m for m in a.modules if not matching(m, ids)]
    problems += [f"{m}, named after --fast, is no test, class or module of the suite" for m in unknown]
    if problems:
        print("[run] error: the fast tier does not hold together:", file=sys.stderr)
        for p in problems:
            print(f"[run]   {p}", file=sys.stderr)
        return 2
    keep = tier_ids(tier, ids).union(*(matching(m, ids) for m in a.modules))
    jobs = plan(names, keep)
    total = sum(len(v) for v in jobs.values())
    found = sum(1 for i in discover_ids() if i in keep)
    if found != total:
        print(f"[run] error: the fast tier's plan holds {total} tests and unittest discover finds {found} of "
              "them; run --serial and report this", file=sys.stderr)
        return 2
    if a.plan:
        for job in order(jobs, times=last_times(state_dir(env))[0]):
            print(f"{job}\t{len(jobs[job])}")
        return 0
    if a.modules:
        say(f"added to the fast tier: {' '.join(a.modules)}")
    code, outcome = start_jobs(jobs, names, a.jobs, a.logs, env, keep, what="the fast tier")
    took = time.monotonic() - started
    budget = tier["budget_seconds"]
    if outcome is None:
        return code
    say(f"the fast tier took {took:.1f}s of wall clock, {outcome['run']} of the suite's "
        f"{sum(len(v) for v in everything.values())} tests; its budget is {budget}s")
    if took > budget:
        print(f"[run] FAILED: the fast tier ran over its budget: {took:.1f}s > {budget}s "
              f"(tests/{TIER_FILE}; the slowest tests are in its logs' times.tsv)", file=sys.stderr)
        return 1 if code == 0 else code
    return code


if __name__ == "__main__":
    sys.exit(main())
