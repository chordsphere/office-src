"""Tests for the read side: the floor plan's [projects] table and its verb,
the bale consumption manifest, the reader over bale's JSON surfaces, and
the renderings built on it.

bale is never needed. A fake `bale`, first on PATH, replays lines the
read-side probe captured from a real bale (kept verbatim, with their
sha256, in the development record's fixtures) keyed by argv and by the
project directory it runs in, and refuses every other invocation loudly,
so a reader that drifts to a surface the probe never captured fails a
test instead of passing by accident. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import ast
import datetime as dt
import hashlib
import json
import os
import pathlib
import pty
import select
import shutil
import subprocess
import tempfile
import time
import tomllib
import types
import unittest

import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)

# Split so the text rules' own check does not trip on this file.
FIXTURES = REPO / ("cla" + "ude") / "fixtures" / "bale-0.4.45"
CONSUMPTION = REPO / "share" / "bale-consumption.toml"
MISS_SID = "2026-01-01-no-such-session-001"
OPEN_SITTING = "2026-09-29-continue-plan-002"
OPEN_WORKER = "2026-09-30-read-side-001"
APPLIED = ("2026-09-24-office-src-core-001", "2026-09-24-office-src-verbs-002",
           "2026-09-29-drafting-table-space-003", "2026-09-29-verb-table-columns-004")


# The read side's sets: one directory per project the read-side probe ran
# in. pack/ beside them is the out-and-in probe's, read by test_start.py.
READ_SETS = ("anywhere", "office-src", "test-office")


def fixture_records(setname=None):
    sets = [FIXTURES / setname] if setname else [FIXTURES / n for n in READ_SETS]
    out = []
    for d in sets:
        for f in sorted(d.glob("*.json")):
            out.append((f, json.loads(f.read_text(encoding="utf-8"))))
    return out


def fixture_line(setname, argv):
    for _, rec in fixture_records(setname):
        if rec["argv"] == argv:
            return json.loads(rec["stdout"][0])
    raise KeyError(argv)


FAKE_BALE = '''#!/usr/bin/env python3
# A fake bale for the read side's tests: replays lines a probe captured
# from a real bale, keyed by argv and the directory it runs in. Anything
# else is refused with exit 97.
import json, os, pathlib, sys
ROUTES = json.loads({routes!r})
argv = sys.argv[1:]
cwd = os.path.realpath(os.getcwd())
with open({calls!r}, "a", encoding="utf-8") as log:
    log.write(json.dumps([cwd, argv]) + "\\n")
for d in ([ROUTES[cwd]] if cwd in ROUTES else []) + [ROUTES["*"]]:
    for f in sorted(pathlib.Path(d).glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        if rec["argv"] == argv:
            for line in rec["stdout"]:
                print(line)
            for line in rec["stderr"]:
                print(line, file=sys.stderr)
            sys.exit(rec["exit"])
print("fake bale: the probe captured no line for bale " + " ".join(argv) + " in " + cwd, file=sys.stderr)
sys.exit(97)
'''


class FakeBale:
    """A directory holding the fake bale; `routes` maps a project
    directory to the fixture set replayed there."""

    def __init__(self, tmp, routes):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="fake-bale-", dir=tmp))
        self.calls = self.dir / "calls.jsonl"
        table = {os.path.realpath(k): str(FIXTURES / v) for k, v in routes.items()}
        table["*"] = str(FIXTURES / "anywhere")
        script = self.dir / "bale"
        script.write_text(FAKE_BALE.format(routes=json.dumps(table), calls=str(self.calls)))
        script.chmod(0o755)

    def path(self, base):
        return f"{self.dir}{os.pathsep}{base}"

    def argvs(self):
        if not self.calls.is_file():
            return []
        return [json.loads(l)[1] for l in self.calls.read_text().splitlines()]


_NO_BALE = []


def path_without_bale(tmp=None):
    """A PATH holding every tool the real PATH has except bale, as links
    in one directory, so 'bale is not on PATH' is really true. Built once
    per run and removed at exit."""
    if _NO_BALE:
        return _NO_BALE[0]
    d = pathlib.Path(tempfile.mkdtemp(prefix="office-test-no-bale-"))
    import atexit
    atexit.register(shutil.rmtree, d, True)
    for part in os.environ.get("PATH", "/usr/bin:/bin").split(os.pathsep):
        if not part or not os.path.isdir(part):
            continue
        for entry in os.scandir(part):
            if entry.name == "bale" or (d / entry.name).exists():
                continue
            if entry.is_file() and os.access(entry.path, os.X_OK):
                (d / entry.name).symlink_to(entry.path)
    _NO_BALE.append(str(d))
    return str(d)


def make_project(tmp, name, bale_dir=True, bale_toml=False):
    """A git repo bale could run in, empty but for the markers."""
    root = pathlib.Path(tmp) / "projects" / name
    root.mkdir(parents=True)
    env = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    subprocess.run(["git", "init", "-q", str(root)], check=True, env=env)
    if bale_dir:
        (root / ".bale").mkdir()
    if bale_toml:
        (root / "bale.toml").write_text("")
    return root


# --- the fixtures themselves -------------------------------------------------------

class TestFixtures(unittest.TestCase):
    def test_every_line_is_the_one_the_probe_captured(self):
        records = fixture_records()
        self.assertGreaterEqual(len(records), 16)
        for f, rec in records:
            self.assertEqual(len(rec["stdout"]), len(rec["stdout_sha256"]), f)
            for line, sha in zip(rec["stdout"], rec["stdout_sha256"]):
                self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), sha, f.name)
            self.assertIn("probe of session 2026-09-30-read-side-001", rec["captured"])

    def test_the_fixtures_cover_every_surface_the_office_calls(self):
        argvs = [rec["argv"] for _, rec in fixture_records()]
        cons = ob.Consumption()
        self.assertIn(cons.argv("version"), argvs)
        self.assertIn(cons.argv("status"), argvs)
        self.assertIn(cons.argv("stats"), argvs)
        self.assertIn(cons.argv("stats", work_class="mixed"), argvs)
        # --since was probed later, into its own set (watches/).
        later = [json.loads(f.read_text(encoding="utf-8"))["argv"]
                 for f in sorted((FIXTURES / "watches" / "office-src").glob("*.json"))]
        self.assertIn(cons.argv("stats", since="2026-10-01"), later)
        self.assertIn(cons.argv("dossier", sid=OPEN_WORKER), argvs)
        self.assertIn(cons.argv("dossier", sid=MISS_SID), argvs)


class TestFakeBale(unittest.TestCase):
    def test_replays_captured_lines_and_refuses_the_rest(self):
        e = Env(self)
        proj = make_project(e.tmp, "office-src")
        fake = FakeBale(e.tmp, {str(proj): "office-src"})
        env = dict(e.env, PATH=fake.path(e.env["PATH"]))
        ok = subprocess.run(["bale", "status", "--json"], cwd=proj, env=env, capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0)
        self.assertEqual(json.loads(ok.stdout)["outcome"], "status")
        no = subprocess.run(["bale", "status", "--json", "--verbose"], cwd=proj, env=env,
                            capture_output=True, text=True)
        self.assertEqual(no.returncode, 97)
        self.assertIn("captured no line", no.stderr)
        elsewhere = subprocess.run(["bale", "status", "--json"], cwd=e.home, env=env,
                                   capture_output=True, text=True)
        self.assertEqual(elsewhere.returncode, 97)


# --- the consumption manifest ----------------------------------------------------------

def literal_key_reads():
    """(surface, key) for every Reader.key call in the reader's source,
    and the calls whose surface or key is not a literal."""
    tree = ast.parse((REPO / "lib" / "office_bale.py").read_text())
    found, dynamic = set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "key":
            s, k = node.args[1], node.args[2]
            if isinstance(s, ast.Constant) and isinstance(k, ast.Constant):
                found.add((s.value, k.value))
            else:
                dynamic.append(ast.unparse(node))
    return found, dynamic


def resolve(obj, path):
    """Every value a declared key path reaches in one JSON line: list
    elements for a[], map values for a.*, None-valued parents skipped.
    Returns (reached, missing): missing names a parent that lacked it."""
    parts = path.split(".")
    frontier, missing = [obj], []
    for i, part in enumerate(parts):
        name = part.removesuffix("[]")
        nxt = []
        for node in frontier:
            if node is None:
                continue
            if name == "*":
                if isinstance(node, dict):
                    nxt.extend(node.values())
                continue
            if not isinstance(node, dict) or name not in node:
                missing.append(".".join(parts[:i + 1]))
                continue
            value = node[name]
            if part.endswith("[]"):
                nxt.extend(value or [])
            else:
                nxt.append(value)
        frontier = nxt
    return frontier, missing


class TestConsumptionManifest(unittest.TestCase):
    def setUp(self):
        self.data = tomllib.loads(CONSUMPTION.read_text())
        self.cons = ob.Consumption()

    def test_floor_is_the_probed_bale(self):
        self.assertEqual(self.cons.floor, "0.4.45")
        self.assertEqual(fixture_records("anywhere")[0][1]["stdout"], ["bale 0.4.45"])

    def test_every_key_the_reader_reads_is_declared_and_every_declared_key_is_read(self):
        reads, dynamic = literal_key_reads()
        # The one generic read: each JSON line's outcome, checked in Reader.run.
        self.assertEqual(len(dynamic), 1, dynamic)
        self.assertIn("'outcome'", dynamic[0])
        declared = {(s, k) for s, spec in self.data["surfaces"].items() if spec.get("calls", True)
                    for k in spec.get("keys", [])}
        for surface, spec in self.data["surfaces"].items():
            if spec.get("format") != "text" and spec.get("calls", True):
                self.assertIn("outcome", spec["keys"], surface)
                reads.add((surface, "outcome"))
        self.assertEqual(reads - declared, set(), "read but not declared")
        # The watch catalog's queries name their keys as data, read through
        # Reader.reach, which holds each to the manifest the same way
        # (tests/test_watches_digest.py runs them over the captures).
        import office_watches as ow
        self.assertEqual(declared - reads - ow.Catalog().keys(), set(), "declared but never read")

    def test_the_pack_report_key_is_the_one_declared(self):
        """office sessions FOLDER - reads the piped report's sid, the key
        office start reads through the reader; since 0.6.0 the office
        calls the surface itself."""
        self.assertIn(h.PACK_SID_KEY, self.data["surfaces"]["pack"]["keys"])
        self.assertTrue(self.data["surfaces"]["pack"].get("calls", True))
        with self.assertRaises(ob.BaleError):
            self.cons.argv("pack")  # it needs a goal and a slug

    def test_every_declared_key_is_in_the_captured_lines(self):
        """The test that fails when a bale release moves a key: re-capture
        the fixtures from the new bale and this names the key."""
        lines = {"status": [], "stats": [], "dossier": [], "miss": []}
        for _, rec in fixture_records():
            if rec["exit"] != 0 or rec["argv"] == ["--version"]:
                continue
            line = json.loads(rec["stdout"][0])
            kind = {"status": "status", "stats": "stats", "dossier": "dossier"}[line["outcome"]]
            if kind == "dossier" and not line["found"]:
                kind = "miss"
            lines[kind].append(line)
        self.assertTrue(all(lines.values()), {k: len(v) for k, v in lines.items()})
        miss_only = {"parse_failure", "filtered_record_version"}
        for surface in ("status", "stats", "dossier"):
            for key in self.data["surfaces"][surface]["keys"]:
                pool = lines["miss"] if key in miss_only else lines[surface]
                seen = False
                for line in pool:
                    reached, missing = resolve(line, key)
                    self.assertEqual(missing, [], f"{surface} line lacks {key}")
                    seen = seen or bool(reached)
                self.assertTrue(seen, f"no captured {surface} line reaches {key}")

    def test_argv_comes_from_the_declaration(self):
        self.assertEqual(self.cons.argv("dossier", sid="2026-09-30-x-001"),
                         ["stats", "--sid", "2026-09-30-x-001", "--json"])
        self.assertEqual(self.cons.argv("stats"), ["stats", "--json"])
        self.assertEqual(self.cons.argv("stats", work_class="meta"), ["stats", "--json", "--work-class", "meta"])
        self.assertEqual(self.cons.argv("stats", since="2026-10-01"), ["stats", "--json", "--since", "2026-10-01"])
        with self.assertRaises(ob.BaleError):
            self.cons.argv("dossier")
        with self.assertRaises(ob.BaleError):
            self.cons.argv("changelog")

    def test_an_undeclared_key_is_refused_and_a_missing_one_names_the_floor(self):
        rd = ob.Reader()
        with self.assertRaises(ob.BaleError) as cm:
            rd.key({"goal": "x"}, "status", "goal")
        self.assertEqual(cm.exception.kind, "undeclared")
        with self.assertRaises(ob.BaleError) as cm:
            rd.key({}, "status", "outbox")
        self.assertEqual(cm.exception.kind, "key")
        self.assertIn("0.4.45 or later", str(cm.exception))


# --- the reader against the fake bale ----------------------------------------------------

def temp_consumption(tmp, extra):
    """The shipped manifest plus test-only surfaces, to reach captured
    lines the office itself never asks for (the refusal, a text line)."""
    path = pathlib.Path(tmp) / "consumption.toml"
    path.write_text(CONSUMPTION.read_text() + "\n" + extra)
    return ob.Consumption(path)


class ReaderCase(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.proj = make_project(self.e.tmp, "office-src")
        self.idle = make_project(self.e.tmp, "quiet", bale_dir=False, bale_toml=True)
        self.fake = FakeBale(self.e.tmp, {str(self.proj): "office-src", str(self.idle): "test-office"})
        self.path = self.fake.path(self.e.env["PATH"])
        self._old_path = os.environ.get("PATH")
        os.environ["PATH"] = self.path
        self.addCleanup(self.restore_path)

    def restore_path(self):
        os.environ["PATH"] = self._old_path


class TestReader(ReaderCase):
    def test_open_sessions_come_from_status(self):
        rd = ob.Reader()
        self.assertEqual(rd.open_sessions(self.proj), [(OPEN_SITTING, True), (OPEN_WORKER, False)])
        self.assertEqual(rd.open_sessions(self.idle), [])

    def test_known_sids_are_the_outbox_and_the_open_sessions(self):
        sids = ob.Reader().known_sids(self.proj)
        self.assertEqual(len(sids), 8)
        for sid in APPLIED + (OPEN_SITTING, OPEN_WORKER):
            self.assertIn(sid, sids)

    def test_a_dossier_and_an_honest_miss(self):
        rd = ob.Reader()
        v = ob.session_view(rd, rd.dossier(self.proj, APPLIED[2]))
        self.assertEqual((v["outcome"], v["work_class"], v["in_flight"]), ("applied", "mixed", False))
        self.assertEqual(len(ob.response_attempts(v)), 1)
        self.assertEqual(len(v["attempts"][1]["checks"]), 6)
        self.assertIsNone(rd.dossier(self.proj, MISS_SID))

    def test_each_question_is_asked_once(self):
        rd = ob.Reader()
        rd.known_sids(self.proj)
        rd.open_sessions(self.proj)
        self.assertEqual(self.fake.argvs(), [["status", "--json"]])

    def test_bale_missing(self):
        os.environ["PATH"] = path_without_bale(self.e.tmp)
        with self.assertRaises(ob.BaleError) as cm:
            ob.Reader().status(self.proj)
        self.assertEqual(cm.exception.kind, "missing")
        self.assertIn("bale is not on PATH", str(cm.exception))

    def test_a_project_path_missing(self):
        with self.assertRaises(ob.BaleError) as cm:
            ob.Reader().status(self.e.tmp / "gone")
        self.assertEqual(cm.exception.kind, "path")

    def test_a_verb_refusing_carries_bales_words(self):
        cons = temp_consumption(self.e.tmp, '[surfaces.both]\nargv = ["stats", "--sid", "{sid}", '
                                '"--since", "{since}", "--json"]\noutcome = "dossier"\nkeys = ["outcome"]\n')
        with self.assertRaises(ob.BaleError) as cm:
            ob.Reader(cons).run("both", self.proj, sid=APPLIED[0], since="2026-09-01")
        self.assertEqual(cm.exception.kind, "refused")
        self.assertIn("exit 1", str(cm.exception))
        self.assertIn("does not compose with --since", str(cm.exception))

    def test_a_line_that_is_not_json(self):
        cons = temp_consumption(self.e.tmp, '[surfaces.notjson]\nargv = ["--version"]\n'
                                'outcome = "status"\nkeys = ["outcome"]\n')
        with self.assertRaises(ob.BaleError) as cm:
            ob.Reader(cons).run("notjson", self.proj)
        self.assertEqual(cm.exception.kind, "output")

    def test_a_declared_key_bale_does_not_send(self):
        cons = temp_consumption(self.e.tmp, '[surfaces.status2]\nargv = ["status", "--json"]\n'
                                'outcome = "status"\nkeys = ["outcome", "worktrees"]\n')
        rd = ob.Reader(cons)
        line = rd.run("status2", self.proj)
        with self.assertRaises(ob.BaleError) as cm:
            rd.key(line, "status2", "worktrees")
        self.assertEqual(cm.exception.kind, "key")

    def test_the_installed_version(self):
        self.assertEqual(ob.Reader().installed_version(), "0.4.45")


# --- the [projects] table ------------------------------------------------------------------

class TestProjectsTable(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.manifest = self.root / "floor-plan/manifest.toml"

    def test_a_new_office_has_no_table_and_scopes_nothing(self):
        self.assertIsNone(h.read_projects(h.read_toml(self.manifest)))
        self.assertNotRegex(self.manifest.read_text(), r"(?m)^\[projects")

    def test_add_appends_one_entry_and_keeps_every_other_byte(self):
        before = self.manifest.read_text()
        proj = make_project(self.e.tmp, "alpha")
        stored, found = h.add_project(self.manifest, "alpha", str(proj))
        self.assertEqual(stored, str(proj))
        self.assertEqual(found, "a git repo with .bale/, no bale.toml")
        after = self.manifest.read_text()
        self.assertTrue(after.startswith(before))
        after.encode("ascii")
        entries = h.read_projects(h.read_toml(self.manifest))
        self.assertEqual([(p["name"], p["path"], p["problem"]) for p in entries], [("alpha", str(proj), None)])
        beta = make_project(self.e.tmp, "beta", bale_dir=False, bale_toml=True)
        self.assertEqual(h.add_project(self.manifest, "beta", str(beta))[1], "a git repo with bale.toml, no .bale/")
        self.assertEqual(self.manifest.read_text().count("# The projects this office scopes"), 1)
        self.assertEqual([p["name"] for p in h.read_projects(h.read_toml(self.manifest))], ["alpha", "beta"])

    def test_refusals(self):
        proj = make_project(self.e.tmp, "alpha")
        h.add_project(self.manifest, "alpha", str(proj))
        plain = self.e.tmp / "plain"
        plain.mkdir()
        bare = make_project(self.e.tmp, "bare", bale_dir=False)
        (proj / "sub").mkdir()
        for name, path, words in (("alpha", str(bare), "already in"),
                                  ("again", str(proj), "already in"),
                                  ("bad.name", str(bare), "letters, digits"),
                                  ("gone", str(self.e.tmp / "gone"), "no such directory"),
                                  ("plain", str(plain), "not a git repo"),
                                  ("bare", str(bare), "has not run in"),
                                  ("sub", str(proj / "sub"), "inside the git repo")):
            with self.assertRaises(h.HelperError) as cm:
                h.add_project(self.manifest, name, path)
            self.assertIn(words, str(cm.exception), name)

    def test_paths_are_absolute_or_home_relative(self):
        self.assertEqual(h.expand_project_path("~/x"), pathlib.Path(os.path.expanduser("~/x")))
        with self.assertRaises(h.HelperError):
            h.expand_project_path("x/y")
        self.manifest.write_text(self.manifest.read_text() + '\n[projects.rel]\npath = "x/y"\n'
                                 '[projects.nopath]\nwhere = "x"\n')
        entries = {p["name"]: p for p in h.read_projects(h.read_toml(self.manifest))}
        self.assertIn("absolute or start with ~/", entries["rel"]["problem"])
        self.assertIn("no path", entries["nopath"]["problem"])

    def test_a_path_outside_ascii_survives_the_round_trip(self):
        proj = make_project(self.e.tmp, "café")
        h.add_project(self.manifest, "cafe", str(proj))
        self.manifest.read_text().encode("ascii")
        self.assertEqual(h.read_projects(h.read_toml(self.manifest))[0]["path"], str(proj))


class TestProjectsVerb(unittest.TestCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.proj = make_project(self.e.tmp, "office-src")

    def test_listing_with_no_table_says_so(self):
        out = self.e.run("projects", cwd=self.root, check=0).stdout
        self.assertIn("no [projects] table", out)

    def test_add_with_flags_commits_only_the_floor_plan(self):
        (self.root / "notepad" / "draft.md").write_text("uncommitted\n")
        proc = self.e.run("projects", "add", "--name", "office-src", "--path", str(self.proj), cwd=self.root, check=0)
        self.assertIn("added office-src", proc.stdout)
        self.assertIn(".bale/", proc.stdout)
        self.assertEqual(self.e.git(self.root, "log", "-1", "--format=%s").strip(), "office projects: add office-src")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "?? notepad/draft.md")
        out = self.e.run("projects", cwd=self.root, check=0).stdout
        self.assertIn(f"office-src  {self.proj}  (a git repo with .bale/, no bale.toml)", out)

    def test_add_takes_words_too(self):
        self.e.run("projects", "add", "office-src", str(self.proj), cwd=self.root, check=0)
        self.assertIn("[projects.office-src]", (self.root / "floor-plan/manifest.toml").read_text())

    def test_piped_add_never_asks_and_names_the_flags(self):
        proc = self.e.run("projects", "add", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--name NAME --path PATH", proc.stderr)
        proc = self.e.run("projects", "add", "office-src", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("give --path PATH", proc.stderr)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_add_explains_what_it_does_not_know(self):
        proc = self.e.run("projects", "add", "--force", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("usage: office projects", proc.stderr)
        self.assertIn("does not know --force", proc.stderr)

    def test_the_wizard_asks_on_a_terminal(self):
        env = dict(self.e.env)
        pid, fd = pty.fork()
        if pid == 0:  # the child: the office command on a terminal
            try:
                os.chdir(self.root)
                os.execve(str(self.e.office_bin), [str(self.e.office_bin), "projects", "add"], env)
            finally:
                os._exit(127)
        seen = b""

        def read_until(marker, limit=20):
            nonlocal seen
            deadline = time.time() + limit
            while marker not in seen and time.time() < deadline:
                ready, _, _ = select.select([fd], [], [], 0.2)
                if ready:
                    try:
                        chunk = os.read(fd, 1024)
                    except OSError:
                        break
                    if not chunk:
                        break
                    seen += chunk
            return marker in seen

        self.assertTrue(read_until(b"(--path):"), seen)
        os.write(fd, str(self.proj).encode() + b"\n")
        # After the path: this machine, or a host. A plain return, this machine.
        self.assertTrue(read_until(b"(--host) [return skips]:"), seen)
        os.write(fd, b"\n")
        self.assertTrue(read_until(b"(--name) [office-src]:"), seen)
        os.write(fd, b"\n")
        # What rides with it and what runs after it lands: a plain
        # return ends each list, empty.
        self.assertTrue(read_until(b"(--ride) [return ends the list]:"), seen)
        os.write(fd, b"\n")
        self.assertTrue(read_until(b"(--after-land) [return ends the list]:"), seen)
        os.write(fd, b"\n")
        read_until(b"added office-src")
        _, status = os.waitpid(pid, 0)
        os.close(fd)
        self.assertIn(b"added office-src", seen)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0, seen)
        self.assertIn("[projects.office-src]", (self.root / "floor-plan/manifest.toml").read_text())

    def test_a_missing_project_is_reported_not_dropped(self):
        self.e.run("projects", "add", "office-src", str(self.proj), cwd=self.root, check=0)
        shutil.rmtree(self.proj)
        proc = self.e.run("projects", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("office-src", proc.stdout)
        self.assertIn("CANNOT BE READ: no such directory on this machine", proc.stdout)

    def test_a_name_narrows_only_a_rendering(self):
        proc = self.e.run("projects", "office-src", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--ledger", proc.stderr)
        proc = self.e.run("projects", "--ledger", "--versions", cwd=self.root)
        self.assertEqual(proc.returncode, 1)


# --- the renderings ------------------------------------------------------------------------

class _ClassOwner:
    """Env registers its cleanup on a test; a class-wide world registers
    it on the class instead."""

    def __init__(self, cls):
        self.addCleanup = cls.addClassCleanup


def build_world(owner):
    """An office scoping the captured project (and an idle one bale also
    answers for), with a folder that records a closed session, the open
    worker and a sid no project holds. Built with the helpers the verbs
    use, in-process: the verbs themselves are tested above and in
    test_office."""
    e = Env(owner)
    w = types.SimpleNamespace(e=e)
    w.proj = make_project(e.tmp, "office-src")
    w.idle = make_project(e.tmp, "quiet", bale_dir=False, bale_toml=True)
    w.fake = FakeBale(e.tmp, {str(w.proj): "office-src", str(w.idle): "test-office"})
    w.path = w.fake.path(e.env["PATH"])
    e.env["PATH"] = w.path
    w.root = e.init()
    h.add_project(w.root / "floor-plan/manifest.toml", "office-src", str(w.proj))
    w.folder = "desk/2026-09-29-read-side"
    folder = w.root / w.folder
    folder.mkdir(parents=True)
    (folder / "folder.md").write_text(h.render_template(
        (REPO / "templates/folder.md").read_text(), {"title": "read side", "number": "1", "status": "queued",
                                                     "queued": "2026-09-29",
                                                     "history": "2026-09-29 queued: office open"}))
    h.record_session(folder / "folder.md", APPLIED[2], "space and templates")
    h.record_session(folder / "folder.md", OPEN_WORKER)
    h.record_session(folder / "folder.md", MISS_SID, "never ran")
    e.git(w.root, "add", "-A")
    e.git(w.root, "commit", "-qm", "a project and a folder")
    return w


class RenderingCase(unittest.TestCase):
    """One world per class, for the tests that only read it; a test that
    changes it (removes the project, edits the floor plan, records a
    session) calls self.private() first and gets its own."""

    @classmethod
    def setUpClass(cls):
        cls._world = build_world(_ClassOwner(cls))

    def setUp(self):
        self.use(self._world)

    def private(self):
        self.use(build_world(self))

    def use(self, w):
        self.e, self.proj, self.idle, self.fake = w.e, w.proj, w.idle, w.fake
        self.path, self.root, self.folder = w.path, w.root, w.folder
        self.addCleanup(os.environ.__setitem__, "PATH", os.environ.get("PATH", ""))
        os.environ["PATH"] = self.path


class TestInFlight(RenderingCase):
    def test_each_open_session_and_its_folder(self):
        now = dt.datetime(2026, 9, 30, 15, 48, 52, tzinfo=dt.timezone.utc)
        lines, bad = ob.render_in_flight(ob.Reader(), self.root, now)
        self.assertEqual(bad, 0)
        self.assertEqual(lines, [
            f"office-src: {OPEN_SITTING} read-only, opened 17h ago -> no folder",
            f"office-src: {OPEN_WORKER} open, opened 2h ago -> {self.folder}",
        ])

    def test_walking_in_shows_it(self):
        out = self.e.run(cwd=self.root, check=0).stdout
        self.assertIn("In flight:\n", out)
        self.assertRegex(out, rf"  office-src: {OPEN_WORKER} open, opened \d+[mhd] ago -> {self.folder}\n")
        self.assertLess(out.index("In flight:"), out.index("On the desk:"))
        self.assertIn("office projects", out)

    def test_an_idle_project(self):
        self.private()
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(manifest.read_text().replace(f'path = "{self.proj}"', f'path = "{self.idle}"'))
        lines, bad = ob.render_in_flight(ob.Reader(), self.root)
        self.assertEqual((lines, bad), (["none: no session is open in the 1 project(s) this office scopes"], 0))

    def test_no_projects_says_so(self):
        e = Env(self)
        root = e.init("bare")
        out = e.run(cwd=root, check=0).stdout
        self.assertIn("In flight:\n  this office scopes no projects: its floor plan has no [projects] table", out)

    def test_a_missing_project_and_a_missing_bale_never_stop_the_walk_in(self):
        self.private()
        shutil.rmtree(self.proj)
        out = self.e.run(cwd=self.root, check=0).stdout
        self.assertIn("office-src: cannot read: no such directory on this machine", out)
        self.assertIn("On the desk:", out)
        out = self.e.run(cwd=self.root, check=0, extra={"PATH": path_without_bale(self.e.tmp)}).stdout
        self.assertIn("office-src: cannot read:", out)


class TestFolderSessions(RenderingCase):
    def test_outcomes_claims_and_rounds_beside_the_folders_words(self):
        out = self.e.run("sessions", "read-side", cwd=self.root, check=0).stdout
        for want in (f"- {APPLIED[2]}: space and templates\n",
                     "    office-src: applied; opened 2026-09-29, last event 2026-09-29; work class mixed\n",
                     "    attempt 1, apply 2026-09-29: applied, validation PASS; 6 claim(s): agree 6\n",
                     "      [agree] claim pass, verdict pass: catalog filed list and the new templates\n",
                     "    exchange rounds: 0; linkage: probe pre-read\n",
                     f"- {OPEN_WORKER}\n    office-src: open; opened 2026-09-30",
                     "    no response attempt yet\n",
                     f"- {MISS_SID}: never ran\n    not in the records of any project this office scopes\n",
                     f"recorded in this folder: 3 session id(s); found in bale's records: 2; not found: {MISS_SID}\n",
                     "bale version per session: not on bale's dossier"):
            self.assertIn(want, out)

    def test_an_untested_claim_reads_n_a(self):
        self.private()
        self.e.run("sessions", "read-side", APPLIED[0], cwd=self.root, check=0)
        out = self.e.run("sessions", "read-side", cwd=self.root, check=0).stdout
        self.assertIn("4 claim(s): agree 3, n/a 1", out)
        self.assertIn("[n/a] claim untested, verdict skip:", out)

    def test_the_folder_keeps_only_ids_and_words(self):
        before = (self.root / self.folder / "folder.md").read_text()
        self.e.run("sessions", "read-side", cwd=self.root, check=0)
        self.assertEqual((self.root / self.folder / "folder.md").read_text(), before)
        self.assertNotIn("PASS", before)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_bale_missing_is_said_once_and_fails(self):
        proc = self.e.run("sessions", "read-side", cwd=self.root, extra={"PATH": path_without_bale(self.e.tmp)})
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout.count("bale is not on PATH"), 1)
        self.assertIn(f"- {APPLIED[2]}: space and templates", proc.stdout)

    def test_an_office_with_no_projects_lists_the_ids_and_says_why_nothing_more(self):
        self.private()
        manifest = self.root / "floor-plan/manifest.toml"
        text = manifest.read_text()
        manifest.write_text(text[:text.index("\n# The projects this office scopes")] + "\n")
        out = self.e.run("sessions", "read-side", cwd=self.root, check=0).stdout
        self.assertIn(f"- {APPLIED[2]}: space and templates\n", out)
        self.assertIn("no [projects] table (office projects add NAME PATH); no outcomes are rendered\n", out)


class TestLedgerLandedVersions(RenderingCase):
    def test_the_trust_ledger(self):
        out = self.e.run("projects", "--ledger", cwd=self.root, check=0).stdout
        rows = [l.split() for l in out.splitlines()[1:]]
        self.assertIn("holds no grant", out.splitlines()[0])
        self.assertEqual(rows[0][:3], ["class", "sessions", "applied"])
        self.assertEqual(" ".join(rows[1]), "meta 1 0 - (0 of 0) - (0 of 0) - (0 of 0) 0 of 0")
        self.assertEqual(" ".join(rows[2]), "mixed 5 4 0.00 (0 of 4) 1.00 (4 of 4) 0.89 (16 of 18); 2 n/a 0 of 4")
        self.assertEqual(len(rows), 3, out)

    def test_last_landed_by(self):
        out = self.e.run("projects", "--landed", "bin/office", cwd=self.root, check=0).stdout
        self.assertEqual(out, f"office-src: bin/office last landed by {APPLIED[3]} (applied 2026-09-30, mixed); "
                              "4 applied session(s) landed it in all\n")
        out = self.e.run("projects", "office-src", "--landed", "./templates/", cwd=self.root, check=0).stdout
        self.assertIn(f"templates last landed by {APPLIED[2]} (applied 2026-09-29, mixed, 11 path(s) under it); "
                      "2 applied session(s)", out)
        out = self.e.run("projects", "--landed", "migrations/9.9.9.sh", cwd=self.root, check=0).stdout
        self.assertIn("no applied session in bale's records landed migrations/9.9.9.sh", out)
        proc = self.e.run("projects", "--landed", "/etc/passwd", cwd=self.root)
        self.assertEqual(proc.returncode, 1)

    def test_the_version_trail(self):
        out = self.e.run("projects", "--versions", cwd=self.root, check=0).stdout
        releases = [l.split()[1] for l in out.splitlines() if l.startswith("    2026-")]
        self.assertEqual(releases, list(APPLIED))
        self.assertIn("    017e38f93a4c from 2026-09-24: 4 session(s), 4 applied, 0 in flight\n", out)
        self.assertIn("    unstamped from 2026-09-29: 2 session(s), 0 applied, 2 in flight\n", out)
        self.assertIn("bale now: 0.4.45", out)

    def test_an_unknown_project_name(self):
        proc = self.e.run("projects", "nisaba", "--ledger", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("no project named nisaba", proc.stderr)

    def test_an_unreadable_project_fails_loudly(self):
        self.private()
        shutil.rmtree(self.proj)
        for flag in (("--ledger",), ("--versions",), ("--landed", "VERSION")):
            proc = self.e.run("projects", *flag, cwd=self.root)
            self.assertEqual(proc.returncode, 1, flag)
            self.assertIn("office-src: cannot read: no such directory on this machine", proc.stdout)

    def test_every_key_read_while_rendering_is_declared(self):
        rd = ob.Reader()
        ob.render_in_flight(rd, self.root)
        ob.render_folder_sessions(rd, self.root, self.root / self.folder / "folder.md")
        ob.render_ledger(rd, self.root)
        ob.render_landed(rd, self.root, "bin/office")
        ob.render_versions(rd, self.root)
        ob.status_lines(rd, self.root)
        declared = {(s, k) for s, spec in tomllib.loads(CONSUMPTION.read_text())["surfaces"].items()
                    for k in spec.get("keys", [])}
        self.assertTrue(rd.touched)
        self.assertEqual(rd.touched - declared, set())
        # Every call the renderings made is one the manifest builds.
        for argv in self.fake.argvs():
            self.assertTrue(argv[0] in ("status", "stats", "--version"), argv)


class TestStatus(RenderingCase):
    def test_bale_within_the_range_and_the_projects(self):
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn("bale:       0.4.45 at ", out)
        self.assertIn("within the read side's range (bale 0.4.45 or later, share/bale-consumption.toml)", out)
        self.assertIn("projects:   1 in scope; each is a repo bale runs in", out)

    def test_bale_below_the_floor_is_a_line_not_a_refusal(self):
        text = CONSUMPTION.read_text().replace('floor = "0.4.45"', 'floor = "9.9.9"')
        path = self.e.tmp / "later.toml"
        path.write_text(text)
        lines, _ = ob.status_lines(ob.Reader(ob.Consumption(path)), self.root)
        self.assertIn("OUTSIDE the read side's range", lines[0])
        self.assertIn("bale 9.9.9 or later", lines[0])

    def test_no_bale_and_a_missing_project(self):
        self.private()
        shutil.rmtree(self.proj)
        out = self.e.run("status", cwd=self.root, check=0, extra={"PATH": path_without_bale(self.e.tmp)}).stdout
        self.assertIn("bale:       bale is not on PATH", out)
        self.assertIn("projects:   1 in scope; 1 cannot be read", out)
        self.assertIn("  office-src: no such directory on this machine", out)


class TestInstallStaysUnwritten(RenderingCase):
    def test_the_reader_leaves_no_bytecode_in_the_install(self):
        """The reader imports the helper; bin/office runs it with -B so
        an install is never written to, whatever the environment says."""
        inst = self.e.tmp / "install"
        for part in ("bin", "lib", "share", "templates", "doctrine", "migrations", "VERSION"):
            src = REPO / part
            (shutil.copytree if src.is_dir() else shutil.copy2)(
                src, inst / part, **({"ignore": shutil.ignore_patterns("__pycache__")} if src.is_dir() else {}))
        env = dict(self.e.env)
        env.pop("PYTHONDONTWRITEBYTECODE")
        proc = subprocess.run([str(inst / "bin" / "office")], cwd=self.root, env=env,
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"office-src: {OPEN_WORKER} open", proc.stdout)
        self.assertEqual(list(inst.rglob("__pycache__")), [])


if __name__ == "__main__":
    unittest.main()
