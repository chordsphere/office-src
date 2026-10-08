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

Each job writes one log, <logs>/<job>.log (unittest -v's own output), and
one result, <logs>/<job>.json. The summary names every job, its counts,
its time and its log, and for a failing job the failing tests, each with
its traceback (its last TRACEBACK_LINES lines, where the exception is),
and the log to read: a log under the temp directory can be gone by the
time anyone reads it (WSL empties /tmp on a restart), and the summary is
what a relay carries. --serial is today's run: one process, unittest discover -v,
on the terminal.

Exit: 0 every test passed, 1 a test failed or errored, 2 the runner could
not run or read a job (said on stderr).

Standard library only.
"""

import argparse
import concurrent.futures
import importlib
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unittest

TESTS = pathlib.Path(__file__).resolve().parent
SERIAL_ATTR = "serial_group"
SERIAL_JOB = "serial-terminal"
DEFAULT_JOBS = 4
# A failing test's traceback in the summary: its last lines, the
# exception and the frames nearest it.
TRACEBACK_LINES = 40
_print_lock = threading.Lock()


def say(msg):
    with _print_lock:
        print(f"[run] {msg}", flush=True)


def module_names(tests_dir=TESTS):
    """Every test module discover would load: test*.py at the top of tests/."""
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


def plan(names):
    """{job: [test ids]}: one job per module with tests outside the serial
    group, and the serial group, in module order, as one job."""
    jobs, serial = {}, []
    for name in names:
        s, rest = load_module_tests(name)
        serial += [t.id() for t in s]
        if rest:
            jobs[name] = [t.id() for t in rest]
    if serial:
        jobs[SERIAL_JOB] = serial
    return jobs


def discover_count():
    """How many tests unittest discover -s tests finds: the plan must match."""
    loader = unittest.TestLoader()
    return loader.discover(str(TESTS), top_level_dir=str(TESTS)).countTestCases()


# --- one job, in its own process -------------------------------------------------

def run_job(job, names, result_path):
    """Run one job's tests (the module's, or the serial group's) with
    unittest -v on this process's stdout, and write the result file."""
    serial = job == SERIAL_JOB
    tests = []
    for name in (names if serial else [job]):
        s, rest = load_module_tests(name)
        tests += s if serial else rest
    suite = unittest.TestSuite(tests)
    started = time.monotonic()
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
    res = runner.run(suite)
    out = {"job": job, "run": res.testsRun,
           "failures": [t.id() for t, _ in res.failures],
           "errors": [t.id() for t, _ in res.errors],
           "tracebacks": {t.id(): tb for t, tb in [*res.failures, *res.errors]},
           "unexpected_successes": [t.id() for t in res.unexpectedSuccesses],
           "skipped": len(res.skipped), "seconds": round(time.monotonic() - started, 1)}
    pathlib.Path(result_path).write_text(json.dumps(out) + "\n", encoding="utf-8")
    return 0 if res.wasSuccessful() else 1


# --- the run --------------------------------------------------------------------------

def order(jobs, sizes=None):
    """Longest first: the serial group, then modules by source size (the
    best guess of a module's time before it has run)."""
    sizes = sizes or {}

    def weight(job):
        if job == SERIAL_JOB:
            return float("inf")
        return sizes.get(job, (TESTS / f"{job}.py").stat().st_size if (TESTS / f"{job}.py").exists() else 0)
    return sorted(jobs, key=weight, reverse=True)


def launch(job, names, logs, env):
    log = logs / f"{job}.log"
    result = logs / f"{job}.json"
    argv = [sys.executable, "-B", str(pathlib.Path(__file__).resolve()), "--job", job, "--result", str(result),
            *(["--modules", *names] if job == SERIAL_JOB else [])]
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


def run_serial(env):
    """Today's run: one process, unittest discover, on the terminal."""
    say("one process, as before the side-by-side runner (--serial)")
    started = time.monotonic()
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(TESTS), "-v"],
                          cwd=str(TESTS.parent), env=env)
    say(f"{'OK' if proc.returncode == 0 else 'FAILED'} in {time.monotonic() - started:.0f}s")
    return 0 if proc.returncode == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tests/run.sh", description=(
        "Run office-src's test suite, each module as its own process, a few at a time, with the classes that "
        "drive a terminal (serial_group) one after another in a lane of their own. --serial runs it as one "
        "process instead."))
    ap.add_argument("--serial", action="store_true", help="one process: unittest discover -s tests -v")
    ap.add_argument("--jobs", type=int, default=None,
                    help=f"processes at a time (default {DEFAULT_JOBS}, or OFFICE_TEST_JOBS)")
    ap.add_argument("--logs", default=None, help="directory for the logs (default: a new one under the temp dir)")
    ap.add_argument("--plan", action="store_true", help="print the jobs and their test counts; run nothing")
    ap.add_argument("modules", nargs="*", help="run only these modules (test_x), the serial group's share of them "
                                               "included")
    ap.add_argument("--job", help=argparse.SUPPRESS)
    ap.add_argument("--result", help=argparse.SUPPRESS)
    ap.add_argument("--modules", dest="job_modules", nargs="*", default=None, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)

    if a.job:
        names = a.job_modules if a.job_modules is not None else module_names()
        return run_job(a.job, names, a.result)

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    if a.serial:
        if a.modules:
            print("[run] error: --serial runs the whole suite; drop the module names", file=sys.stderr)
            return 2
        return run_serial(env)

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
        for job in order(jobs):
            print(f"{job}\t{len(jobs[job])}")
        return 0
    n = a.jobs or int(os.environ.get("OFFICE_TEST_JOBS", DEFAULT_JOBS) or DEFAULT_JOBS)
    if n < 1:
        print("[run] error: --jobs takes 1 or more", file=sys.stderr)
        return 2
    # Absolute: each job runs with tests/ as its directory, so a relative
    # path would name a different place there than here.
    logs = (pathlib.Path(a.logs) if a.logs else pathlib.Path(tempfile.mkdtemp(prefix="office-tests."))).resolve()
    logs.mkdir(parents=True, exist_ok=True)
    say(f"{total} tests in {len(jobs)} jobs, {n} at a time"
        + (f"; the serial group ({len(jobs.get(SERIAL_JOB, []))} tests) runs in a lane of its own"
           if SERIAL_JOB in jobs else "") + f"; logs in {logs}")
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(launch, job, names, logs, env) for job in order(jobs)]
        results = [f.result() for f in futures]
    lines, failed = summary(results, total, time.monotonic() - started, logs)
    print("\n".join(lines), flush=True)
    ran = sum(r["run"] for r in results)
    if not failed and ran != total:
        print(f"[run] error: {ran} tests ran, the plan held {total}", file=sys.stderr)
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
