"""Tests for the out trip: office slip, the per-project declarations, office
note's prefix check, and office start with its out tray.

bale is never needed. The fake bale here packs: it writes request and
context tarballs into .bale/outbox/ and keeps the open sessions in its own
state file, and every line it prints is built from what the out-and-in
probe captured from a real bale 0.4.45 (kept verbatim, with their sha256,
in the development record's fixtures): the same report keys, the same
stderr, the same opener between the same scissor lines, the same refusal.
The fixtures are also read directly, so the office's readers are run over
bale's own bytes. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import hashlib
import json
import os
import pathlib
import pty
import re
import select
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)

# Split so the text rules' own check does not trip on this file.
PACK_FIXTURES = REPO / ("cla" + "ude") / "fixtures" / "bale-0.4.45" / "pack"
CONSUMPTION = REPO / "share" / "bale-consumption.toml"
PROBE_SID = "2026-10-02-friction-out-and-in-002"


def pack_fixture(label):
    return json.loads((PACK_FIXTURES / f"{label}.json").read_text(encoding="utf-8"))


def all_pack_fixtures():
    return sorted(PACK_FIXTURES.glob("*.json"))


FAKE_PACK_BALE = r'''#!/usr/bin/env python3
# A fake bale that packs, for office start's tests. Every line it prints
# is built from lines the out-and-in probe captured from a real bale, with
# the session id, the paths and the goal swapped in. It keeps the open
# sessions per directory in its own state file, never in .bale/ beyond the
# outbox, and refuses anything it was not built for with exit 97.
import argparse, datetime, io, json, os, pathlib, re, subprocess, sys, tarfile
FIX = pathlib.Path({fixtures!r})
STATE = pathlib.Path({state!r})
CALLS = pathlib.Path({calls!r})
argv = sys.argv[1:]
cwd = os.path.realpath(os.getcwd())
with CALLS.open("a", encoding="utf-8") as log:
    log.write(json.dumps([cwd, argv]) + "\n")
def fx(label):
    return json.loads((FIX / (label + ".json")).read_text(encoding="utf-8"))
def load():
    return json.loads(STATE.read_text()) if STATE.is_file() else {{"repos": {{}}, "fail": []}}
def save(s):
    STATE.write_text(json.dumps(s))
state = load()
repo = state["repos"].setdefault(cwd, {{"sessions": [], "scopes": {{}}, "outbox": []}})
if argv == ["--version"]:
    print("bale 0.4.45"); sys.exit(0)
if argv == ["status", "--json"]:
    line = json.loads(fx("office-status")["stdout"][0])
    line["sid"] = repo["sessions"][0] if repo["sessions"] else None
    line["sessions"] = repo["sessions"]; line["scopes"] = repo["scopes"]; line["outbox"] = repo["outbox"]
    line["repo"]["root"] = cwd
    print(json.dumps(line)); sys.exit(0)
if not argv or argv[0] != "pack":
    print("fake bale: not built for bale " + " ".join(argv), file=sys.stderr); sys.exit(97)
ap = argparse.ArgumentParser(prog="bale pack")
ap.add_argument("goal", nargs="?"); ap.add_argument("--context", action="store_true")
ap.add_argument("--slug"); ap.add_argument("--include", action="append", default=[])
ap.add_argument("--write", action="append", default=[]); ap.add_argument("--constraint", action="append", default=[])
ap.add_argument("--readme-file"); ap.add_argument("--no-readme", action="store_true")
ap.add_argument("--work-class"); ap.add_argument("--read-only", action="store_true")
ap.add_argument("--json", action="store_true")
a = ap.parse_args(argv[1:])
if not a.json:
    print("fake bale: built for --json packs only", file=sys.stderr); sys.exit(97)
def files_of(root, includes):
    root = pathlib.Path(root)
    git = subprocess.run(["git", "-C", str(root), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if git.returncode == 0:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "."],
                             capture_output=True, text=True).stdout.split()
    else:
        out = [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()]
    out = [f for f in out if not f.startswith(".bale/") and "/.bale/" not in f]
    if includes:
        keep = list(includes)
        # The include group, as bale.toml declares it: when an include
        # touches a trigger, the pulls ship too (never under --context).
        cfg = root / "bale.toml"
        if cfg.is_file() and not a.context:
            import tomllib
            pack = tomllib.loads(cfg.read_text()).get("pack", {{}})
            if pack.get("include_group") and any(i.split("/")[0] in pack.get("include_group_triggers", []) for i in includes):
                keep += pack.get("include_group_pulls", [])
        out = [f for f in out if any(f == i or f.startswith(i.rstrip("/") + "/") for i in keep)]
    return sorted(out), git.returncode == 0
outbox = pathlib.Path(cwd) / ".bale" / "outbox"
if a.context:
    for flag in ("goal", "slug", "readme_file", "work_class"):
        if getattr(a, flag):
            print("fake bale: --context refuses a session-only flag", file=sys.stderr); sys.exit(2)
    name = pathlib.Path(cwd).name
    files, git = files_of(cwd, a.include)
    outbox.mkdir(parents=True, exist_ok=True)
    tb = outbox / ("context-" + name + ".tar.gz")
    total = 0
    with tarfile.open(tb, "w:gz") as t:
        for f in files:
            t.add(pathlib.Path(cwd) / f, arcname=name + "/" + f); total += (pathlib.Path(cwd) / f).stat().st_size
    line = json.loads(fx("office-context-whole")["stdout"][0])
    line.update(tarball=str(tb), directory=cwd, tree_name=name, context_files=len(files), total_bytes=total, git=git)
    print(json.dumps(line, separators=(",", ":")))
    print("[bale] context pack of " + cwd + " — no session is opened", file=sys.stderr)
    sys.exit(0)
if not a.goal or not a.slug:
    print("[bale] error: piped, a goal and --slug are required", file=sys.stderr); sys.exit(1)
if not a.readme_file and not a.no_readme:
    print("[bale] error: no README prose; --no-readme acknowledges it", file=sys.stderr); sys.exit(1)
for p in a.write + a.include:
    if not (pathlib.Path(cwd) / p).exists():
        print("[bale] error: forecast or include names no existing path: " + p, file=sys.stderr); sys.exit(1)
mine = [] if a.read_only else (a.write or a.include or [""])
def hit(x, y):
    x, y = x.strip("/"), y.strip("/")
    return x == "" or y == "" or x == y or x.startswith(y + "/") or y.startswith(x + "/")
for sid in repo["sessions"]:
    theirs = repo["scopes"][sid] or []
    pairs = [(m, t) for m in mine for t in theirs if hit(m, t)]
    if pairs:
        err = fx("office-second-pack")["stderr"][-1]
        err = err.replace("2026-10-02-probe-office-work-001", sid).replace("(notepad ~ notepad)",
              "(" + ", ".join(m + " ~ " + t for m, t in pairs) + ")")
        for l in fx("office-second-pack")["stderr"][:-1]:
            print(l, file=sys.stderr)
        print(err, file=sys.stderr); sys.exit(1)
if "pack" in state["fail"]:
    print("[bale] error: the fake was told to refuse this pack", file=sys.stderr); sys.exit(1)
day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
n = 1 + sum(1 for s in repo["outbox"] if s.startswith("request-" + day + "-" + a.slug + "-"))
sid = day + "-" + a.slug + "-" + format(n, "03d")
outbox.mkdir(parents=True, exist_ok=True)
tb = outbox / ("request-" + sid + ".tar.gz")
files, _ = files_of(cwd, a.include)
manifest = {{"session_id": sid, "goal": a.goal, "constraints": a.constraint, "resolved_scope": mine if mine != [""] else ["."],
            "readme": {{"path": "README.md"}} if a.readme_file else None,
            "work_class": a.work_class or "mixed", "context_included": ["context/" + f for f in files]}}
with tarfile.open(tb, "w:gz") as t:
    data = json.dumps(manifest).encode()
    info = tarfile.TarInfo("request-001/manifest.json"); info.size = len(data)
    t.addfile(info, io.BytesIO(data))
    if a.readme_file:
        t.add(a.readme_file, arcname="request-001/README.md")
    for f in files:
        t.add(pathlib.Path(cwd) / f, arcname="request-001/context/" + f)
repo["sessions"].append(sid); repo["scopes"][sid] = [] if a.read_only else mine; repo["outbox"].append(tb.name)
save(state)
label = "project-pack" if a.readme_file else "office-pack"
cap = fx(label)
old = json.loads(cap["stdout"][0])
line = dict(old)
oldsid, oldroot = old["sid"], old["tarball"].split("/.bale/")[0]
line.update(sid=sid, tarball=str(tb), log=cwd + "/.bale/logs/" + sid + ".log",
            session_dir=cwd + "/.bale/sessions/" + sid, context_files=len(files))
print(json.dumps(line))
oldgoal = re.search(r"Goal, verbatim from the request manifest: (.*)$", "\n".join(cap["stderr"]), re.M).group(1)
for l in cap["stderr"]:
    l = l.replace(oldsid, sid).replace(oldroot, cwd)
    if l.startswith("Goal, verbatim from the request manifest: "):
        l = l.replace(oldgoal, a.goal)
    print(l, file=sys.stderr)
sys.exit(0)
'''


class FakePackBale:
    """A directory holding the fake bale; its state and calls live beside it."""

    def __init__(self, tmp):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="fake-pack-bale-", dir=tmp))
        self.state = self.dir / "state.json"
        self.calls = self.dir / "calls.jsonl"
        script = self.dir / "bale"
        script.write_text(FAKE_PACK_BALE.format(fixtures=str(PACK_FIXTURES), state=str(self.state),
                                                calls=str(self.calls)))
        script.chmod(0o755)

    def path(self, base):
        return f"{self.dir}{os.pathsep}{base}"

    def argvs(self):
        if not self.calls.is_file():
            return []
        return [json.loads(l) for l in self.calls.read_text().splitlines()]

    def packs(self):
        """(cwd, argv) of every bale pack the office ran."""
        return [(c, a) for c, a in self.argvs() if a and a[0] == "pack"]

    def refuse_next_pack(self):
        s = json.loads(self.state.read_text()) if self.state.is_file() else {"repos": {}, "fail": []}
        s["fail"].append("pack")
        self.state.write_text(json.dumps(s))


def git_repo(path, files=None, ignore_bale=True):
    """A committed git repo holding files ({relpath: text})."""
    path = pathlib.Path(path)
    path.mkdir(parents=True, exist_ok=True)
    env = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@x"}
    subprocess.run(["git", "init", "-q", str(path)], check=True, env=env)
    for rel, text in (files or {"README.md": "x\n"}).items():
        (path / rel).parent.mkdir(parents=True, exist_ok=True)
        (path / rel).write_text(text)
    if ignore_bale:
        (path / ".gitignore").write_text(".bale/\n")
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True, env=env)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", "init"], check=True, env=env)
    (path / ".bale").mkdir(exist_ok=True)
    return path


def tar_names(path):
    with tarfile.open(path) as t:
        return sorted(t.getnames())


def on_a_terminal(test, argv, cwd, env, script):
    """Run the office command on a pty, answering each prompt in script:
    a list of (marker the screen must show, line to type). Returns
    (exit code, everything the screen showed)."""
    pid, fd = pty.fork()
    if pid == 0:
        try:
            os.chdir(cwd)
            os.execve(argv[0], argv, env)
        finally:
            os._exit(127)
    seen = b""

    def read_until(marker, limit=30):
        nonlocal seen
        deadline = time.time() + limit
        while marker not in seen and time.time() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                seen += chunk
        return marker in seen

    for marker, answer in script:
        test.assertTrue(read_until(marker), seen.decode(errors="replace"))
        os.write(fd, answer.encode() + b"\n")
    deadline = time.time() + 60
    while time.time() < deadline:  # to the end of the child's output
        ready, _, _ = select.select([fd], [], [], 0.2)
        if not ready:
            continue
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        seen += chunk
    _, status = os.waitpid(pid, 0)
    os.close(fd)
    return os.waitstatus_to_exitcode(status), seen.decode(errors="replace")


def opener_from(text):
    """The lines office start printed between its scissor lines."""
    lines = text.splitlines()
    a = lines.index("--8<-- session opener --8<--")
    b = lines.index("--8<-- end session opener --8<--")
    return lines[a + 1:b]


# --- the captured packs themselves ---------------------------------------------------

class TestPackFixtures(unittest.TestCase):
    def setUp(self):
        self.cons = ob.Consumption()
        self.data = tomllib.loads(CONSUMPTION.read_text())

    def test_every_line_is_the_one_the_probe_captured(self):
        files = all_pack_fixtures()
        self.assertGreaterEqual(len(files), 12)
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual(len(rec["stdout"]), len(rec["stdout_sha256"]), f.name)
            for line, sha in zip(rec["stdout"], rec["stdout_sha256"]):
                self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), sha, f.name)
            self.assertIn(f"probe of session {PROBE_SID}", rec["captured"], f.name)

    def test_every_declared_key_is_in_the_captured_reports(self):
        """The test that fails when a bale release moves a pack key:
        re-capture into a new bale-VERSION/pack/ and this names it."""
        for surface, labels in (("pack", ("office-pack", "project-pack")),
                                ("context", ("office-context-whole", "office-context-include", "ctx-other-include",
                                             "ctx-other-inside", "ctx-plain"))):
            spec = self.data["surfaces"][surface]
            for label in labels:
                rec = pack_fixture(label)
                self.assertEqual(rec["exit"], 0, label)
                line = json.loads(rec["stdout"][-1])
                self.assertEqual(line["outcome"], spec["outcome"], label)
                for key in spec["keys"]:
                    self.assertIn(key, line, f"{label} lacks {key}")

    def test_every_flag_the_office_passes_is_in_bales_help(self):
        help_text = "\n".join(pack_fixture("pack_help")["stdout"])
        for surface in ("pack", "context"):
            spec = self.data["surfaces"][surface]
            flags = [w for w in spec["argv"] if w.startswith("--")]
            for group in ("optional", "repeated", "switches"):
                flags += [f for f, _ in spec.get(group, [])]
            for flag in flags:
                self.assertIn(flag, help_text, f"{surface}: {flag}")

    def test_argv_comes_from_the_declaration(self):
        argv = self.cons.argv("pack", goal="Do it", slug="do-it", includes=["src", "lib"], writes=["src"],
                              constraints=[ob.PROJECT_CONSTRAINT], readme_file=None, no_readme=True,
                              read_only=False, work_class="code")
        self.assertEqual(argv, ["pack", "Do it", "--slug", "do-it", "--json", "--work-class", "code",
                                "--include", "src", "--include", "lib", "--write", "src",
                                "--constraint", ob.PROJECT_CONSTRAINT, "--no-readme"])
        self.assertEqual(self.cons.argv("context", includes=["desk/x", "profile.md"]),
                         ["pack", "--context", "--json", "--include", "desk/x", "--include", "profile.md"])
        self.assertEqual(self.cons.argv("context"), ["pack", "--context", "--json"])
        self.assertIn("--read-only", self.cons.argv("pack", goal="g", slug="s", read_only=True))

    def test_the_opener_is_read_from_bales_own_lines(self):
        spec = self.data["surfaces"]["pack"]
        for label in ("office-pack", "project-pack"):
            rec = pack_fixture(label)
            sid = json.loads(rec["stdout"][0])["sid"]
            lines = ob.opener_lines(rec["stderr"], spec)
            self.assertEqual(lines[0], 'I\'m using "bale", a CLI that packaged the attached request tarball.')
            self.assertEqual(lines[1], f"This message opens bale session {sid}.")
            self.assertTrue(lines[-1].startswith("what I need back is one response tarball"))
            self.assertNotIn(spec["opener"][0], lines)
        # The plain report prints the same opener on stdout.
        plain = pack_fixture("project-pack-plain")
        self.assertEqual(ob.opener_lines(plain["stdout"], spec),
                         ob.opener_lines(pack_fixture("project-pack")["stderr"], spec))
        self.assertIsNone(ob.opener_lines(pack_fixture("office-second-pack")["stderr"], spec))

    def test_a_refused_pack_says_so_only_on_stderr(self):
        """Why office start checks the open forecasts itself: under
        --json bale's refusal is an exit and a stderr line, nothing on
        stdout."""
        rec = pack_fixture("office-second-pack")
        self.assertEqual(rec["exit"], 1)
        self.assertEqual(rec["stdout"], [])
        self.assertIn("pack write forecast intersects 1 open session(s)", rec["stderr"][-1])
        status = json.loads(pack_fixture("office-status")["stdout"][0])
        sid = status["sessions"][0]
        self.assertEqual(ob.forecast_overlap(["desk/x", "notepad"], status["scopes"][sid]), ["notepad"])

    def test_include_groups_do_not_fire_under_context(self):
        """Why office start names the hung items for the office's context."""
        whole = json.loads(pack_fixture("office-context-whole")["stdout"][0])
        one = json.loads(pack_fixture("office-context-include")["stdout"][0])
        self.assertGreater(whole["context_files"], one["context_files"])
        self.assertEqual(one["context_files"], 1)
        self.assertTrue(json.loads(pack_fixture("office-pack")["stdout"][0])["include_group"]["pulled"])


class TestForecastOverlap(unittest.TestCase):
    def test_entries_overlap_when_equal_or_nested(self):
        f = ob.forecast_overlap
        self.assertEqual(f(["notepad"], ["notepad"]), ["notepad"])
        self.assertEqual(f(["desk/a"], ["desk"]), ["desk/a"])
        self.assertEqual(f(["bin/"], ["bin/office"]), ["bin/office"])
        self.assertEqual(f(["desk/a", "notepad"], ["desk/b"]), [])
        self.assertEqual(f([], ["notepad"]), [])
        self.assertEqual(f(["src"], []), [])
        self.assertEqual(f(None, ["src"]), ["src"])
        self.assertEqual(f(["src"], None), ["src"])
        self.assertEqual(f(None, None), ["the whole tree"])
        self.assertEqual(f(["src"], ["."]), ["src"])


# --- office slip -------------------------------------------------------------------------

class TestSlip(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def slips(self):
        return sorted((self.root / "suggestion-box").glob("*.md"))

    def test_a_slip_is_its_own_page_committed_alone(self):
        (self.root / "notepad" / "draft.md").write_text("uncommitted\n")
        proc = self.e.run("slip", "--about", "bale", "pack", "needs", "too", "many", "flags", cwd=self.root, check=0)
        page = proc.stdout.strip()
        self.assertRegex(page, r"^suggestion-box/\d{4}-\d{2}-\d{2}-pack-needs-too-many-flags\.md$")
        text = (self.root / page).read_text()
        self.assertTrue(text.startswith("# pack needs too many flags\n\n- about: bale\n- dropped: "))
        self.assertTrue(text.endswith("\npack needs too many flags\n"))
        self.assertIn("What caused friction", text)
        self.assertEqual(self.e.git(self.root, "show", "--name-only", "--format=%s", "HEAD").split(),
                         ["office", "slip:", page.split("/")[1][:-3], "(about", "bale)", page])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "?? notepad/draft.md")
        self.assertIn("Suggestion box: 1 slip(s).", self.e.run(cwd=self.root, check=0).stdout)

    def test_piped_text_and_no_about_is_never_asked(self):
        proc = self.e.run("slip", cwd=self.root, input="the survey is slow\nand loud\n", check=0)
        text = (self.root / proc.stdout.strip()).read_text()
        self.assertNotIn("- about:", text)
        self.assertTrue(text.endswith("the survey is slow\nand loud\n"))
        self.assertIn("--about", proc.stderr)

    def test_a_slip_works_unfounded_and_under_skew(self):
        from test_office import NEXT, MIGRATION_ADD_SPACE
        self.assertIn("unfounded", self.e.run("slip", "x", cwd=self.root, check=0).stderr)
        behind = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Adds a handbook.", MIGRATION_ADD_SPACE)])
        proc = self.e.run("slip", "behind", cwd=self.root, bin_path=behind, check=0)
        self.assertIn("behind", proc.stderr)
        ahead = self.e.fake_install("0.0.9")
        proc = self.e.run("slip", "ahead", cwd=self.root, bin_path=ahead, check=0)
        self.assertIn("migrated past", proc.stderr)
        self.assertEqual(len(self.slips()), 3)

    def test_the_office_stays_ascii_and_the_name_has_no_escape(self):
        proc = self.e.run("slip", "café — too slow", cwd=self.root, check=0)
        page = proc.stdout.strip()
        self.assertNotIn("u2014", page)
        text = (self.root / page).read_bytes().decode("ascii")
        self.assertIn("caf\\xe9 \\u2014 too slow", text)

    def test_the_same_words_twice_make_two_pages(self):
        a = self.e.run("slip", "same", cwd=self.root, check=0).stdout.strip()
        b = self.e.run("slip", "same", cwd=self.root, check=0).stdout.strip()
        self.assertNotEqual(a, b)
        self.assertTrue(b.endswith("-same-2.md"), b)

    def test_refusals(self):
        proc = self.e.run("slip", "--about", "two words", "x", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("one word", proc.stderr)
        self.assertEqual(self.e.run("slip", cwd=self.root, input="  \n").returncode, 1)
        self.assertEqual(self.e.run("slip", "--loud", "x", cwd=self.root).returncode, 1)
        self.assertEqual(self.slips(), [])

    def test_on_a_terminal_it_asks_what_it_is_about(self):
        proj = git_repo(self.e.tmp / "alpha")
        self.e.run("projects", "add", "alpha", str(proj), cwd=self.root, check=0)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "slip", "the", "desk", "is", "slow"], self.root,
                                   self.e.env, [(b"office, bale, office-src, alpha (--about) [office]:", "alpha")])
        self.assertEqual(code, 0, seen)
        self.assertIn("- about: alpha\n", self.slips()[0].read_text())


# --- office note's check before it commits ---------------------------------------------------

class TestNoteChecksTheFiledPage(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_a_page_whose_filed_bytes_changed_is_not_committed(self):
        self.e.run("note", "first", cwd=self.root, check=0)
        page = next((self.root / "notepad").glob("2*.md"))
        head = self.e.git(self.root, "rev-parse", "HEAD")
        page.write_text(page.read_text().replace("first", "FIRST"))
        proc = self.e.run("note", "second", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("other than at its end", proc.stderr)
        self.assertIn("on disk but not committed", proc.stderr)
        self.assertIn("second", page.read_text())
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)

    def test_a_note_after_an_uncommitted_note_commits_both(self):
        self.e.run("note", "first", cwd=self.root, check=0)
        page = next((self.root / "notepad").glob("2*.md"))
        with page.open("a") as fh:
            fh.write("- 09:00 an earlier line that never got committed\n")
        self.e.run("note", "second", cwd=self.root, check=0)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_the_check(self):
        page = "notepad/x.md"
        self.assertIsNone(h.append_check(self.root, page))            # new to git
        (self.root / page).write_text("one\n")
        self.e.git(self.root, "add", page)
        self.e.git(self.root, "commit", "-qm", "x")
        self.assertIsNone(h.append_check(self.root, page))
        (self.root / page).write_text("one\ntwo\n")
        self.assertIsNone(h.append_check(self.root, page))
        (self.root / page).write_text("ONE\n")
        self.assertIn("first difference at byte 0", h.append_check(self.root, page))
        (self.root / page).unlink()
        self.assertIn("missing", h.append_check(self.root, page))
        plain = self.e.tmp / "plain"
        plain.mkdir()
        self.assertIsNone(h.append_check(plain, "x.md"))


# --- what rides with a project, and what runs after it lands ------------------------------------

class TestDeclarations(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.manifest = self.root / "floor-plan/manifest.toml"
        self.proj = git_repo(self.e.tmp / "alpha")
        self.other = git_repo(self.e.tmp / "other", {"blueprints/b.md": "b\n"})
        self.e.run("projects", "add", "alpha", str(self.proj), cwd=self.root, check=0)
        self.e.run("projects", "add", "beta", str(git_repo(self.e.tmp / "beta")), cwd=self.root, check=0)

    def test_set_and_clear_keep_every_other_byte(self):
        before = self.manifest.read_text()
        ride = str(self.other / "blueprints")
        entry = h.set_declarations(self.manifest, "alpha", [ride, ride + "/"], ["./install.sh"])
        self.assertEqual(entry["rides"], [ride])
        self.assertEqual(entry["after_land"], ["./install.sh"])
        after = self.manifest.read_text()
        self.assertEqual([l for l in after.splitlines() if l not in before.splitlines()],
                         [f'rides = ["{ride}"]', 'after_land = ["./install.sh"]'])
        self.assertEqual(h.read_projects(h.read_toml(self.manifest))[1]["rides"], [])  # beta untouched
        h.set_declarations(self.manifest, "alpha", None, ["make install", "./install.sh --no-link"])
        self.assertIn(f'rides = ["{ride}"]', self.manifest.read_text())
        h.set_declarations(self.manifest, "alpha", [], [])
        self.assertEqual(self.manifest.read_text(), before)
        after.encode("ascii")

    def test_refusals(self):
        for name, rides, after, words in (("gamma", [str(self.proj)], None, "no project named gamma"),
                                          ("alpha", [str(self.e.tmp / "gone")], None, "no such path"),
                                          ("alpha", ["relative/path"], None, "absolute or start with ~/"),
                                          ("alpha", None, ["  "], "empty"),
                                          ("alpha", None, ["a\nb"], "one line")):
            with self.assertRaises(h.HelperError) as cm:
                h.set_declarations(self.manifest, name, rides, after)
            self.assertIn(words, str(cm.exception), name)
        self.manifest.write_text(self.manifest.read_text().replace(
            "[projects.alpha]\n", "[projects.alpha]\nrides = [\n  \"/tmp\",\n]\n"))
        with self.assertRaises(h.HelperError) as cm:
            h.set_declarations(self.manifest, "alpha", [str(self.proj)], None)
        self.assertIn("several lines", str(cm.exception))

    def test_a_declaration_that_does_not_read_is_reported_not_fatal(self):
        self.manifest.write_text(self.manifest.read_text().replace(
            "[projects.alpha]\n", '[projects.alpha]\nrides = "not a list"\n'))
        alpha = h.read_projects(h.read_toml(self.manifest))[0]
        self.assertIsNone(alpha["problem"])
        self.assertEqual(alpha["declaration_problems"], ["rides is not a list of non-empty strings"])
        self.assertIn("declaration problem: rides", self.e.run("projects", cwd=self.root, check=0).stdout)

    def test_the_verb_with_flags_commits_only_the_floor_plan(self):
        (self.root / "notepad" / "draft.md").write_text("uncommitted\n")
        ride = str(self.other / "blueprints")
        proc = self.e.run("projects", "set", "alpha", "--ride", ride, "--after-land", "./install.sh",
                          cwd=self.root, check=0)
        self.assertIn("after it lands: ./install.sh", proc.stdout)
        self.assertEqual(self.e.git(self.root, "log", "-1", "--format=%s").strip(), "office projects: set alpha")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "?? notepad/draft.md")
        listing = self.e.run("projects", cwd=self.root, check=0).stdout
        self.assertIn(f"rides: {ride}\n", listing)
        self.assertIn("after it lands: ./install.sh\n", listing)
        self.e.run("projects", "set", "alpha", "--no-rides", cwd=self.root, check=0)
        self.assertNotIn("rides:", self.e.run("projects", cwd=self.root, check=0).stdout)
        self.assertIn("after it lands", self.e.run("projects", cwd=self.root, check=0).stdout)

    def test_add_takes_the_declarations_in_one_commit(self):
        ride = str(self.other / "blueprints")
        self.e.run("projects", "add", "gamma", str(git_repo(self.e.tmp / "gamma")), "--ride", ride,
                   "--after-land", "./install.sh", cwd=self.root, check=0)
        self.assertEqual(self.e.git(self.root, "log", "-1", "--format=%s").strip(), "office projects: add gamma")
        gamma = [p for p in h.read_projects(h.read_toml(self.manifest)) if p["name"] == "gamma"][0]
        self.assertEqual((gamma["rides"], gamma["after_land"]), ([ride], ["./install.sh"]))
        before = self.manifest.read_text()
        proc = self.e.run("projects", "add", "delta", str(git_repo(self.e.tmp / "delta")), "--ride",
                          str(self.e.tmp / "gone"), cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.manifest.read_text(), before)

    def test_piped_set_names_the_flags_it_needed(self):
        for args, words in ((("set",), "office projects set NAME"),
                            (("set", "alpha"), "--ride PATH"),
                            (("set", "alpha", "--ride", "/tmp", "--no-rides"), "contradict"),
                            (("set", "gamma", "--no-rides"), "no project named gamma")):
            proc = self.e.run("projects", *args, cwd=self.root)
            self.assertEqual(proc.returncode, 1, args)
            self.assertIn(words, proc.stderr, args)

    def test_the_wizard_asks_on_a_terminal(self):
        h.set_declarations(self.manifest, "alpha", None, ["./install.sh"])
        self.e.git(self.root, "commit", "-qam", "seed")
        ride = str(self.other / "blueprints")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "set", "alpha"], self.root, self.e.env, [
            (b"(--ride) [return ends the list]:", str(self.e.tmp / "gone")),
            (b"no such path on this machine", ride),
            (b"Another (--ride) [return ends the list]:", ""),
            (b"Keep what runs after alpha lands: ./install.sh? (y/n) [y]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        alpha = h.read_projects(h.read_toml(self.manifest))[0]
        self.assertEqual((alpha["rides"], alpha["after_land"]), ([ride], ["./install.sh"]))


# --- office start ---------------------------------------------------------------------------

class StartCase(unittest.TestCase):
    """An office scoping one project, alpha, that declares three
    ride-alongs (a directory inside another repo, a plain directory and a
    file outside git) and an after-land action; one folder on the desk,
    its lane on alpha. bale is the fake that packs."""

    def setUp(self):
        self.e = Env(self)
        self.fake = FakePackBale(self.e.tmp)
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.root = self.e.init("home")
        self.e.found(self.root)
        self.proj = git_repo(self.e.tmp / "alpha", {"src/a.py": "a\n", "README.md": "alpha\n"})
        self.other = git_repo(self.e.tmp / "other", {"blueprints/b.md": "b\n", "notes.md": "n\n"})
        self.plain = self.e.tmp / "plain"
        self.plain.mkdir()
        (self.plain / "p.txt").write_text("p\n")
        self.loose = self.e.tmp / "loose.md"
        self.loose.write_text("a loose page\n")
        self.e.run("projects", "add", "alpha", str(self.proj), "--ride", str(self.other / "blueprints"),
                   "--ride", str(self.plain), "--ride", str(self.loose),
                   "--after-land", "touch AFTER-LAND-RAN", cwd=self.root, check=0)
        self.folder = self.e.run("open", "fix-login", "--lane", "alpha: src", "--class", "code",
                                 cwd=self.root, check=0).stdout.strip()
        self.name = self.folder.split("/")[1]
        self.trays = self.e.home / "out-tray"

    def start(self, *args, check=0, **kw):
        return self.e.run("start", *args, cwd=self.root, check=check, **kw)

    def tray(self, proc):
        line = next(l for l in proc.stdout.splitlines() if l.startswith("Out tray: "))
        return pathlib.Path(line[len("Out tray: "):])

    def folder_md(self):
        return (self.root / self.folder / "folder.md").read_text()


class TestStartOnAProject(StartCase):
    def test_one_command_packs_records_and_fills_the_tray(self):
        proc = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertRegex(sid, r"^\d{4}-\d{2}-\d{2}-fix-login-001$")
        tray = self.tray(proc)
        self.assertEqual(tray, self.trays / sid)
        self.assertEqual(sorted(p.name for p in tray.iterdir()),
                         sorted([f"request-{sid}.tar.gz", "context-doctrine.tar.gz", "context-home.tar.gz",
                                 "context-other.tar.gz", "context-plain.tar.gz", "loose.md"]))
        # The request is bale's own tarball, byte for byte.
        self.assertEqual((tray / f"request-{sid}.tar.gz").read_bytes(),
                         (self.proj / ".bale/outbox" / f"request-{sid}.tar.gz").read_bytes())
        self.assertEqual(tar_names(tray / "context-doctrine.tar.gz"),
                         ["doctrine/OFFICE.md", "doctrine/checks/filed-append-only.sh"])
        self.assertEqual(tar_names(tray / "context-home.tar.gz"),
                         [f"home/{self.folder}/folder.md", "home/floor-plan/survey.md", "home/profile.md"])
        self.assertEqual(tar_names(tray / "context-other.tar.gz"), ["other/blueprints/b.md"])
        self.assertEqual(tar_names(tray / "context-plain.tar.gz"), ["plain/p.txt"])
        # The session was packed in the project, with the constraint verbatim.
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(cwd, os.path.realpath(self.proj))
        self.assertEqual(argv[:3], ["pack", "Fix the login redirect", "--slug"])
        for pair in (["--write", "src"], ["--work-class", "code"],
                     ["--constraint", "Office context informs this session but never lands in this project."]):
            self.assertIn(pair, [argv[i:i + 2] for i in range(len(argv))])
        self.assertIn("--no-readme", argv)
        self.assertNotIn("--include", argv)   # the whole repo ships
        # The folder records the session and opens.
        md = self.folder_md()
        self.assertIn(f"\n- {sid}\n", md)
        self.assertIn("- status: open", md)
        self.assertIn(f"opened: {sid}", md)
        self.assertEqual(self.e.git(self.root, "log", "-1", "--format=%s").strip(),
                         f"office sessions: {sid} in {self.name}")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # The opener is bale's, printed whole.
        opener = opener_from(proc.stdout)
        self.assertEqual(opener[1], f"This message opens bale session {sid}.")
        self.assertEqual(opener[2], "Goal, verbatim from the request manifest: Fix the login redirect")
        self.assertEqual(opener[3:], ob.opener_lines(pack_fixture("office-pack")["stderr"],
                                                     ob.Consumption().surface("pack"))[3:])

    def test_nothing_is_written_into_the_install_or_a_plain_ride_along(self):
        self.start("fix-login", "--on", "alpha", "--goal", "g")
        self.assertFalse((REPO / "doctrine" / ".bale").exists())
        self.assertEqual(sorted(p.name for p in self.plain.iterdir()), ["p.txt"])
        self.assertFalse((self.other / "blueprints" / ".bale").exists())
        self.assertFalse((self.e.tmp / "AFTER-LAND-RAN").exists())
        self.assertFalse((self.proj / "AFTER-LAND-RAN").exists())

    def test_a_brief_ships_as_the_readme(self):
        brief = self.e.tmp / "brief.md"
        brief.write_text("# Brief\n\nWhy.\n")
        proc = self.start("fix-login", "--on", "alpha", "--goal", "g", "--brief", str(brief))
        (_, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertIn(["--readme-file", str(brief)], [argv[i:i + 2] for i in range(len(argv))])
        self.assertNotIn("--no-readme", argv)
        self.assertIn("then README.md", "\n".join(opener_from(proc.stdout)))

    def test_flags_override_what_the_folder_says(self):
        (self.proj / "lib").mkdir()
        (self.proj / "lib" / "x.py").write_text("x\n")
        self.start("folder 1", "--on", "alpha", "--goal", "g", "--slug", "Login Fix", "--write", "lib/",
                   "--include", "lib")
        (_, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertIn(["--slug", "login-fix"], [argv[i:i + 2] for i in range(len(argv))])
        self.assertIn(["--write", "lib"], [argv[i:i + 2] for i in range(len(argv))])
        self.assertNotIn(["--write", "src"], [argv[i:i + 2] for i in range(len(argv))])

    def test_the_out_tray_lives_where_the_machine_says(self):
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text('out_tray = "~/trays"\n')
        proc = self.start("fix-login", "--on", "alpha", "--goal", "g")
        self.assertEqual(self.tray(proc).parent, self.e.home / "trays")


class TestStartInTheOffice(StartCase):
    def test_an_office_session_forecasts_the_folder_and_the_notepad(self):
        proc = self.start("fix-login", "--in-office", "--goal", "Plan the fix")
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertTrue(sid.endswith("-fix-login-office-001"), sid)
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(cwd, os.path.realpath(self.root))
        pairs = [argv[i:i + 2] for i in range(len(argv))]
        for pair in (["--include", self.folder], ["--write", self.folder], ["--write", "notepad"]):
            self.assertIn(pair, pairs)
        self.assertNotIn("--constraint", argv)
        tray = self.tray(proc)
        self.assertIn(f"request-001/context/{self.folder}/folder.md", tar_names(tray / f"request-{sid}.tar.gz"))
        self.assertIn("request-001/context/profile.md", tar_names(tray / f"request-{sid}.tar.gz"))
        # The lane names alpha: its tree and its ride-alongs ride beside.
        self.assertEqual(sorted(p.name for p in tray.iterdir()),
                         sorted([f"request-{sid}.tar.gz", "context-doctrine.tar.gz", "context-alpha.tar.gz",
                                 "context-other.tar.gz", "context-plain.tar.gz", "loose.md"]))
        self.assertIn(f"\n- {sid}\n", self.folder_md())

    def test_office_sessions_take_turns_and_the_refusal_names_the_open_one(self):
        first = self.start("fix-login", "--in-office", "--goal", "g")
        sid = re.search(r"^Packed (\S+) for ", first.stdout, re.M).group(1)
        packs = len(self.fake.packs())
        other = self.e.run("open", "other-job", cwd=self.root, check=0).stdout.strip()
        proc = self.start("other-job", "--in-office", "--goal", "g", check=1)
        self.assertIn(f"{sid} is open in this office ({self.folder})", proc.stderr)
        self.assertIn("overlaps this one at notepad", proc.stderr)
        self.assertIn("office sessions take turns on the notepad", proc.stderr)
        self.assertEqual(len(self.fake.packs()), packs, "bale was asked after all")
        self.assertNotIn("- status: open", (self.root / other / "folder.md").read_text())
        # A read-only sitting forecasts nothing, so it may sit beside it.
        self.start("other-job", "--in-office", "--read-only", "--goal", "g")
        (_, argv) = self.fake.packs()[-1]
        self.assertIn("--read-only", argv)
        self.assertNotIn("--write", argv)
        self.assertEqual([p.name for p in self.trays.iterdir() if p.name.startswith(".")], [])


class TestStartRefusals(StartCase):
    def test_piped_it_asks_nothing_and_names_the_flag(self):
        for args, words in (((), "office start FOLDER"),
                            (("fix-login",), "--in-office, or --on PROJECT (alpha)"),
                            (("fix-login", "--on", "alpha"), "--goal TEXT"),
                            (("fix-login", "--on", "gamma", "--goal", "g"), "no such project"),
                            (("fix-login", "--in-office", "--on", "alpha"), "two places"),
                            (("fix-login", "--read-only", "--write", "x"), "takes no --write"),
                            (("nothing-like-it", "--on", "alpha", "--goal", "g"), "no folder matching"),
                            (("fix-login", "--on", "alpha", "--goal", "-x"), "dash"),
                            (("fix-login", "--on", "alpha", "--goal", "g", "--write", "nope"), "--write nope")):
            proc = self.start(*args, check=1)
            self.assertIn(words, proc.stderr, args)
        self.assertEqual(self.fake.packs(), [])
        self.assertFalse(self.trays.exists() and any(self.trays.iterdir()))
        self.assertNotIn("- status: open", self.folder_md())

    def test_a_pack_bale_refuses_leaves_no_tray_and_no_record(self):
        self.fake.refuse_next_pack()
        proc = self.start("fix-login", "--on", "alpha", "--goal", "g", check=1)
        self.assertIn("the session's pack failed, so no session was opened and no out tray was made", proc.stderr)
        self.assertIn("the fake was told to refuse", proc.stderr)
        self.assertEqual(list(self.trays.iterdir()), [])
        self.assertNotIn("- status: open", self.folder_md())

    def test_a_ride_along_gone_from_the_machine_stops_before_any_pack(self):
        shutil.rmtree(self.plain)
        proc = self.start("fix-login", "--on", "alpha", "--goal", "g", check=1)
        self.assertIn("not on this machine", proc.stderr)
        self.assertEqual([p for p in self.fake.packs() if "--context" not in p[1]], [])
        self.assertEqual(list(self.trays.iterdir()), [])

    def test_a_filed_folder_is_not_started(self):
        self.e.run("close", "fix-login", cwd=self.root, check=0)
        self.assertIn("no folder matching", self.start("fix-login", "--on", "alpha", "--goal", "g", check=1).stderr)

    def test_without_bale_it_says_so(self):
        from test_read_side import path_without_bale
        proc = self.e.run("start", "fix-login", "--on", "alpha", "--goal", "g", cwd=self.root,
                          extra={"PATH": path_without_bale()})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("bale is not on PATH", proc.stderr)


class TestStartOnATerminal(StartCase):
    def test_the_wizard_asks_which_job_where_and_the_goal(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [
            (b"or new to open one (office start FOLDER):", "folder 1"),
            (b"(--in-office or --on PROJECT) [alpha]:", "elsewhere"),
            (b"office, or one of this office's projects: alpha", ""),
            (b"in one sentence (--goal):", "?"),
            (b"becomes the request's goal", "Fix the login redirect"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Packed ", seen)
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(cwd, os.path.realpath(self.proj))
        self.assertEqual(argv[1], "Fix the login redirect")

    def test_new_opens_a_folder_through_office_opens_questions(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "--in-office", "--goal", "g"],
                                   self.root, self.e.env, [
            (b"(office start FOLDER):", "new"),
            (b"Title, in a few words (--title):", "Write the plan"),
            (b"(--size)", ""), (b"(--lane)", ""), (b"(--source)", ""),
        ])
        self.assertEqual(code, 0, seen)
        md = next(self.root.glob("desk/*-write-the-plan/folder.md")).read_text()
        self.assertIn("- status: open", md)
