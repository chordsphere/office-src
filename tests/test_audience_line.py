"""Tests for the audience line (office-src 0.17.0): the audience, author
and base declarations and the push guard; office letterhead check and
its one list; office deliver, on a project here and on a host, against a
bare repo standing in for the audience's git host; the folder's two
pages, walkthrough.md and delivery.md, filed by office land and office
sessions --pages; and office relay.

The suite makes no network call and runs no real ssh or docker: a bare
repo on this machine is the audience (a local path as the clone's
origin), 0.14.0's fake ssh (tests/test_project_on_host.py) stands for the
host, and the fake land bale of tests/test_land.py answers bale's verbs.
Nothing a delivery pushes may carry a bale commit, merge, tag, branch,
mark or excluded file; the tests read the audience to prove it. Run with
the rest of the suite:

    tests/run.sh test_audience_line
"""

import json
import os
import pathlib
import re
import subprocess
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import LandCase, response_tarball  # noqa: E402
from test_project_on_host import DOWN, HOST, FakeSsh  # noqa: E402

import office_bale as ob  # noqa: E402
import office_deliver as odl  # noqa: E402
import office_host as ohost  # noqa: E402
import office_letterhead as olh  # noqa: E402

LIB = REPO / "lib"
RULES = REPO / "share" / "letterhead.toml"
# A model's name, split as the suite's text rules require: nothing in
# office-src spells one, this file included.
A_NAME = "cla" + "ude"
# bale's record directory, split the same way.
RECORD_DIR = "cla" + "ude"
SID = "2026-10-09-health-route-001"
SID2 = "2026-10-10-health-docs-001"
SID3 = "2026-10-10-other-job-001"
WORDS = """# Delivery: health route

- to: Pat Reviewer

## Commit

Add the health route

The API answers /health with ok, and the test covers it.

## Review

Health route for the API

One route and its test. The pullsheet code is untouched.
"""
NOTES = """# Notes

What happened.

## Walkthrough

### What changed

The route and its test.

### A hand test

Open /health.

## Delivery

- to: Pat Reviewer

### Commit

Add the health route

The API answers /health with ok.

### Review

Health route for the API

One route and its test.

## Proposals

- **What**: nothing.
"""


def git(root, *args, env=None, check=True):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=check,
                          env=env).stdout


class AudienceCase(unittest.TestCase):
    """An office with one folder on the desk; a bare repo standing in
    for the audience's git host, holding main; a workbench clone of it
    with one applied session landed the way bale lands one (its work on
    bale/SID, merged as `Merge bale SID`, tagged applied/SID, its record
    swept), recorded in the folder; the folder's delivery.md."""

    hosted = False

    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init("home")
        self.e.found(self.root)
        self.audience = self.e.tmp / "audience.git"
        git(self.e.tmp, "init", "-q", "--bare", str(self.audience), env=self.e.env)
        git(self.audience, "symbolic-ref", "HEAD", "refs/heads/main", env=self.e.env)
        seed = self.e.tmp / "seed"
        seed.mkdir()
        git(seed, "init", "-q", "-b", "main", env=self.e.env)
        (seed / "README.md").write_text("hello\n")
        (seed / "src").mkdir()
        (seed / "src" / "a.py").write_text("x = 1\n")
        git(seed, "add", "-A", env=self.e.env)
        git(seed, "commit", "-qm", "Initial commit", env=self.e.env)
        git(seed, "push", "-q", str(self.audience), "main", env=self.e.env)
        self.clone = self.e.tmp / "clone"
        git(self.e.tmp, "clone", "-q", str(self.audience), str(self.clone), env=self.e.env)
        (self.clone / ".bale").mkdir()
        (self.clone / ".bale" / "registry").write_text("")
        (self.clone / "bale.toml").write_text("# bale\n")
        (self.clone / ".git" / "info" / "exclude").write_text(".bale/\nbale.toml\n")
        self.land_session(SID, {"src/a.py": "x = 2\ny = 3\n", "src/health.py": 'def health():\n    return "ok"\n'},
                          "Add the health route")
        if self.hosted:
            self.ssh = FakeSsh(self.e.tmp)
            self.e.env["PATH"] = self.ssh.path(self.e.env["PATH"])
            # Worked on its host, as before 0.25.0: a project with an
            # audience is worked here by default, so the flag says so.
            self.run_office("projects", "add", "proj", str(self.clone), "--host", HOST, "--connect", "start the VPN",
                            "--audience", "origin", "--author", "Zed Zee <z@example.org>", "--worked-on-host", check=0)
        else:
            self.run_office("projects", "add", "proj", str(self.clone), "--audience", "origin",
                            "--author", "Zed Zee <z@example.org>", check=0)
        self.folder = self.run_office("open", "health route", "--lane", "proj: src", "--size", "small",
                                      check=0).stdout.strip()
        self.name = self.folder.split("/")[1]
        self.run_office("sessions", self.name, SID, check=0)
        self.write_words(WORDS)

    def run_office(self, *args, check=None, **kw):
        if self.hosted:
            self.ssh.reset()
        return self.e.run(*args, cwd=self.root, check=check, **kw)

    def write_words(self, text, name="delivery.md"):
        (self.root / self.folder / name).write_text(text)
        git(self.root, "add", "-A", env=self.e.env)
        git(self.root, "commit", "-qm", "words", env=self.e.env)

    def land_session(self, sid, files, summary, record=True):
        """One session landed in the clone the way bale lands one."""
        env = self.e.env
        git(self.clone, "checkout", "-q", "-b", f"bale/{sid}", env=env)
        for rel, text in files.items():
            (self.clone / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.clone / rel).write_text(text)
        git(self.clone, "add", "-A", env=env)
        git(self.clone, "commit", "-qm", f"[bale {sid}] {summary}", env=env)
        git(self.clone, "checkout", "-q", "main", env=env)
        git(self.clone, "merge", "-q", "--no-ff", "-m", f"Merge bale {sid}", f"bale/{sid}", env=env)
        git(self.clone, "tag", f"applied/{sid}", env=env)
        if record:
            # The record under bale's directory, tracked here as a clone
            # from before --prepare would track it: never delivered.
            rec = self.clone / RECORD_DIR / "telemetry" / f"{sid}.json"
            rec.parent.mkdir(parents=True, exist_ok=True)
            rec.write_text("{}\n")
            git(self.clone, "add", "-f", str(rec.relative_to(self.clone)), env=env)
            git(self.clone, "commit", "-qm", f"[bale sweep {sid}] applied", env=env)
        return git(self.clone, "rev-parse", "HEAD", env=env).strip()

    def audience_log(self, branch="health-route"):
        return git(self.audience, "log", "--format=%an <%ae>|%cn|%s|%b", branch, env=self.e.env, check=False)

    def audience_subjects(self, branch="health-route"):
        return git(self.audience, "log", "--format=%s", branch, env=self.e.env).splitlines()

    def audience_refs(self):
        return git(self.audience, "for-each-ref", "--format=%(refname)", env=self.e.env).split()

    def audience_tree(self, branch="health-route"):
        return git(self.audience, "ls-tree", "-r", "--name-only", branch, env=self.e.env).split()

    def folder_md(self):
        return (self.root / self.folder / "folder.md").read_text()


# --- 1. the declarations and the push guard -------------------------------------------------

class TestTheDeclarations(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.manifest = self.root / "floor-plan" / "manifest.toml"

    def test_the_three_keys_read_back_and_are_checked(self):
        h.add_project(self.manifest, "p", "/srv/p", h.check_host_keys(HOST), checked="checked by the test")
        entry = h.set_declarations(self.manifest, "p", audience_keys={"audience": "origin", "author": " Zed  Zee <z@example.org> ",
                                                                      "base": "main"})
        self.assertEqual((entry["audience"], entry["author"], entry["base"]), ("origin", "Zed Zee <z@example.org>", "main"))
        text = self.manifest.read_text()
        self.assertIn('audience = "origin"\nauthor = "Zed Zee <z@example.org>"\nbase = "main"\n', text)
        self.assertEqual(text.count("[projects.p]"), 1)
        entry = h.set_declarations(self.manifest, "p", audience_keys={"author": None})
        self.assertIsNone(entry["author"])
        self.assertEqual(entry["audience"], "origin")
        self.assertNotIn("author =", self.manifest.read_text())
        for key, bad in (("audience", "two words"), ("audience", ""), ("author", "no email"), ("author", "<a@b>"),
                         ("base", "refs/heads/main"), ("base", "a b"), ("base", "x..y"), ("base", "-x")):
            with self.assertRaises(h.HelperError, msg=f"{key}={bad!r}"):
                h.set_declarations(self.manifest, "p", audience_keys={key: bad})
        with self.assertRaises(h.HelperError):
            h.set_declarations(self.manifest, "p", audience_keys={"mirror": "x"})
        self.assertEqual(h.split_author("Zed Zee <z@example.org>"), ("Zed Zee", "z@example.org"))

    def test_a_key_that_does_not_read_is_a_declaration_problem_never_fatal(self):
        h.add_project(self.manifest, "p", "/srv/p", h.check_host_keys(HOST))
        text = self.manifest.read_text().replace("[projects.p]\n", '[projects.p]\nauthor = "nobody"\n')
        self.manifest.write_text(text)
        entry = next(p for p in h.read_projects(h.read_toml(self.manifest)) if p["name"] == "p")
        self.assertIsNone(entry["problem"])
        self.assertIsNone(entry["author"])
        self.assertTrue(any("author" in x for x in entry["declaration_problems"]), entry["declaration_problems"])

    def test_the_wizard_flags_and_the_listing(self):
        clone = self.e.tmp / "c"
        clone.mkdir()
        git(clone, "init", "-q", "-b", "main", env=self.e.env)
        (clone / "f").write_text("x")
        git(clone, "add", "f", env=self.e.env)
        git(clone, "commit", "-qm", "init", env=self.e.env)
        git(clone, "remote", "add", "upstream", "https://github.example.org/org/c.git", env=self.e.env)
        (clone / ".bale").mkdir()
        # --author and --base go with --audience; an audience is one of the
        # clone's remotes.
        proc = self.e.run("projects", "add", "c", str(clone), "--author", "A <a@b.c>", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--author and --base go with --audience", proc.stderr)
        proc = self.e.run("projects", "add", "c", str(clone), "--audience", "origin", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("has no remote named origin (it has: upstream)", proc.stderr)
        self.assertNotIn("[projects.c]", self.manifest.read_text())
        proc = self.e.run("projects", "add", "c", str(clone), "--audience", "upstream", "--base", "main", cwd=self.root, check=0)
        self.assertIn("push guard installed", proc.stderr)
        hook = clone / ".git" / "hooks" / "pre-push"
        self.assertTrue(hook.is_file())
        self.assertTrue(os.access(hook, os.X_OK))
        self.assertIn("audience='upstream'", hook.read_text())
        listing = self.e.run("projects", cwd=self.root, check=0).stdout
        self.assertIn("audience: the remote upstream", listing)
        self.assertIn("author: none declared; office deliver asks for it once", listing)
        self.assertIn("base: main", listing)
        facts = self.e.run("projects", "set", "c", "--author", "Zed <z@example.org>", cwd=self.root, check=0)
        self.assertIn("author: Zed <z@example.org>", facts.stdout)
        proc = self.e.run("projects", "set", "c", "--no-audience", cwd=self.root, check=0)
        self.assertNotIn("audience", proc.stdout)
        self.assertNotIn("audience =", self.manifest.read_text())
        self.assertNotIn("author =", self.manifest.read_text())
        proc = self.e.run("projects", "set", "c", "--base", "dev", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("has no audience; --author and --base go with --audience", proc.stderr)
        facts = self.e.run("projects", cwd=self.root, check=0).stdout
        self.assertNotIn("base:", facts)

    def test_the_push_guard_refuses_a_push_by_hand_and_lets_deliver_through(self):
        audience = self.e.tmp / "aud.git"
        git(self.e.tmp, "init", "-q", "--bare", str(audience), env=self.e.env)
        clone = self.e.tmp / "c"
        clone.mkdir()
        git(clone, "init", "-q", "-b", "main", env=self.e.env)
        (clone / "f").write_text("x")
        git(clone, "add", "f", env=self.e.env)
        git(clone, "commit", "-qm", "init", env=self.e.env)
        git(clone, "remote", "add", "origin", str(audience), env=self.e.env)
        git(clone, "remote", "add", "other", str(self.e.tmp / "nowhere.git"), env=self.e.env)
        (clone / ".bale").mkdir()
        self.e.run("projects", "add", "c", str(clone), "--audience", "origin", cwd=self.root, check=0)
        pushed = subprocess.run(["git", "-C", str(clone), "push", "origin", "main"], capture_output=True, text=True, env=self.e.env)
        self.assertEqual(pushed.returncode, 1)
        self.assertIn("refs/heads/main (nothing goes to the audience by hand)", pushed.stderr)
        self.assertIn("origin is this project's audience, and only office deliver reaches it", pushed.stderr)
        self.assertIn("office deliver FOLDER", pushed.stderr)
        self.assertEqual(git(audience, "for-each-ref", env=self.e.env), "")
        # The same URL under another name is the audience too.
        git(clone, "remote", "add", "alias", str(audience), env=self.e.env)
        pushed = subprocess.run(["git", "-C", str(clone), "push", "alias", "main"], capture_output=True, text=True, env=self.e.env)
        self.assertEqual(pushed.returncode, 1)
        self.assertIn("is this project's audience", pushed.stderr)
        # deliver's push: the named branch alone goes through.
        env = dict(self.e.env, OFFICE_DELIVERY="feature-x")
        pushed = subprocess.run(["git", "-C", str(clone), "push", "origin", "main:refs/heads/other"], capture_output=True, text=True, env=env)
        self.assertEqual(pushed.returncode, 1)
        self.assertIn("refs/heads/other (office deliver pushes refs/heads/feature-x alone)", pushed.stderr)
        pushed = subprocess.run(["git", "-C", str(clone), "push", "origin", "main:refs/heads/feature-x"], capture_output=True, text=True, env=env)
        self.assertEqual(pushed.returncode, 0, pushed.stderr)
        self.assertEqual(git(audience, "for-each-ref", "--format=%(refname)", env=self.e.env).split(), ["refs/heads/feature-x"])
        # A remote that is not the audience is not the guard's business.
        pushed = subprocess.run(["git", "-C", str(clone), "push", "other", "main"], capture_output=True, text=True, env=self.e.env)
        self.assertNotIn("audience", pushed.stderr)
        # Installed again, it is the same file; another hook is never replaced.
        self.assertIn("guard=office", "guard=" + ohost.git_facts(ohost.Place(str(clone)))["guard"])
        self.assertEqual(ohost.git_facts(ohost.Place(str(clone)))["guard_audience"], "origin")
        ohost.install_push_guard(ohost.Place(str(clone)), "origin", str(audience))
        (clone / ".git" / "hooks" / "pre-push").write_text("#!/bin/sh\nexit 0\n")
        with self.assertRaises(ohost.HostError) as cm:
            ohost.install_push_guard(ohost.Place(str(clone)), "origin", str(audience))
        self.assertIn("another pre-push hook is already there", str(cm.exception))
        self.assertEqual(ohost.git_facts(ohost.Place(str(clone)))["guard"], "other")
        git(clone, "config", "core.hooksPath", "/nonexistent", env=self.e.env)
        with self.assertRaises(ohost.HostError) as cm:
            ohost.install_push_guard(ohost.Place(str(clone)), "origin", str(audience))
        self.assertIn("core.hooksPath is set", str(cm.exception))


class TestTheDeclarationsWizard(unittest.TestCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_add_asks_the_three_with_the_clones_defaults(self):
        e = Env(self)
        root = e.init()
        clone = e.tmp / "c"
        clone.mkdir()
        env = dict(e.env, GIT_AUTHOR_NAME="Own Name", GIT_AUTHOR_EMAIL="own@example.org")
        git(clone, "init", "-q", "-b", "main", env=env)
        (clone / "f").write_text("x")
        git(clone, "add", "f", env=env)
        git(clone, "commit", "-qm", "init", env=env)
        git(clone, "config", "user.name", "Own Name", env=env)
        git(clone, "config", "user.email", "own@example.org", env=env)
        git(clone, "remote", "add", "origin", "https://github.example.org/org/c.git", env=env)
        (clone / ".bale").mkdir()
        code, seen = on_a_terminal(self, [str(e.office_bin), "projects", "add", "--path", str(clone)], root, e.env, [
            (b"this machine, or an ssh host (--host)", ""),
            (b"Name for it in this office (--name) [c]:", ""),
            (b"audience's git host, or none (--audience) [origin]:", "?"),
            (b"The name of the remote in the workbench clone", ""),
            (b"a plain return leaves it for office deliver to ask (the clone has Own Name <own@example.org>) (--author) [return skips]:", "nope"),
            (b"an author is written as git writes one", "Zed Zee <z@example.org>"),
            (b"a plain return leaves it origin's HEAD branch (--base) [return skips]:", ""),
            (b"(--ride) [return ends the list]:", ""),
            (b"(--after-land) [return ends the list]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("push guard installed", seen)
        listing = e.run("projects", cwd=root, check=0).stdout
        self.assertIn("audience: the remote origin", listing)
        self.assertIn("author: Zed Zee <z@example.org>", listing)
        self.assertIn("base: the audience's HEAD branch", listing)
        # set keeps it on a plain return, and none takes it off.
        code, seen = on_a_terminal(self, [str(e.office_bin), "projects", "set", "c"], root, e.env, [
            (b"Keep c on this machine? (y/n) [y]:", ""),
            (b"author Zed Zee <z@example.org>, base the audience's HEAD branch? (y/n) [y]:", "n"),
            (b"or none (--audience) [origin]:", "none"),
            (b"(--ride) [return ends the list]:", ""),
            (b"(--after-land) [return ends the list]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("audience: ", e.run("projects", cwd=root, check=0).stdout)


# --- 2. the letterhead check -------------------------------------------------------------------

class TestTheLetterheadCheck(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.repo = self.e.tmp / "r"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main", env=self.e.env)
        (self.repo / "ok.py").write_text("x = 1\n")
        (self.repo / "pic.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(256)))
        (self.repo / "blob.dat").write_bytes(b"\0\0\0binary")
        git(self.repo, "add", "-A", env=self.e.env)
        git(self.repo, "commit", "-qm", "Initial commit", env=self.e.env)
        self.rules = olh.load_rules_toml(RULES)

    def check(self, *args):
        return subprocess.run([sys.executable, "-B", str(LIB / "office_letterhead.py"), "--rules", str(RULES), *args],
                              cwd=self.repo, capture_output=True, text=True, env=self.e.env)

    def test_the_four_kinds_of_hit_and_a_clean_tree(self):
        (self.repo / "new.md").write_text(f"import {A_NAME}\nNote: in summary\n[bale {SID}] x\nfine line\n")
        proc = self.check()
        self.assertEqual(proc.returncode, 1, proc.stderr)
        lines = proc.stdout.splitlines()
        self.assertIn(f"new.md:1: names: '{A_NAME}' in: import {A_NAME}", lines)
        self.assertIn("new.md:2: phrasing: 'Note:' in: Note: in summary", lines)
        self.assertIn("new.md:2: phrasing: 'in summary' in: Note: in summary", lines)
        self.assertIn(f"new.md:3: marks: '[bale ' in: [bale {SID}] x", lines)
        self.assertIn(f"new.md:3: marks: '{SID}' in: [bale {SID}] x", lines)
        self.assertNotIn("new.md:4", proc.stdout)
        self.assertIn("the files the working tree changed (1), as they are", proc.stderr)
        self.assertIn("nothing with a hit leaves the office", proc.stderr)
        (self.repo / "new.md").unlink()
        proc = self.check()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("nothing changed in the working tree, so no file was read", proc.stderr)
        self.assertIn("clean", proc.stderr)

    def test_the_offices_forbidden_words_and_the_whole_tree(self):
        forb = self.e.tmp / "forbidden.txt"
        forb.write_text("# the office's own\n\nAcme Internal\n")
        (self.repo / "ok.py").write_text("x = 'acme internal'\n")
        git(self.repo, "commit", "-qam", "change", env=self.e.env)
        proc = self.check("--all", "--forbidden", str(forb))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ok.py:1: forbidden: 'acme internal'", proc.stdout)
        self.assertIn("the whole tree, 3 file(s)", proc.stderr)
        self.assertIn("1 file(s) read", proc.stderr)  # the png and the blob are skipped
        proc = self.check("--all")
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_a_range_reads_the_files_at_b_and_the_commit_messages(self):
        (self.repo / "ok.py").write_text("x = 1\ny = 2\n")
        git(self.repo, "commit", "-qam", f"Merge bale {SID}", env=self.e.env)
        (self.repo / "ok.py").write_text("x = 1\ny = 2\nz = 3\n")
        git(self.repo, "commit", "-qam", "Add z", env=self.e.env)
        sha = git(self.repo, "rev-parse", "HEAD~1", env=self.e.env).strip()
        proc = self.check("--range", "HEAD~2..HEAD")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"commit {sha[:12]}:1: marks: 'Merge bale '", proc.stdout)
        self.assertIn("the files HEAD~2..HEAD changed (1), at HEAD's version, and its 2 commit message(s)", proc.stderr)
        (self.repo / "ok.py").write_text(f"{A_NAME}\n")  # dirty, and not read by a range
        proc = self.check("--range", "HEAD~1..HEAD")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        proc = self.check("--range", "nonsense")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--range takes A..B", proc.stderr)

    def test_words_are_checked_as_they_are_and_a_plain_directory_is_the_whole_tree(self):
        words = self.e.tmp / "words.md"
        words.write_text(f"Let me know if you need anything.\n")
        proc = self.check("--words", str(words))
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"{words}:1: phrasing: 'Let me know if you need'", proc.stdout)
        plain = self.e.tmp / "plain"
        plain.mkdir()
        (plain / "a.txt").write_text("ok\n")
        proc = subprocess.run([sys.executable, "-B", str(LIB / "office_letterhead.py"), "--rules", str(RULES), str(plain)],
                              capture_output=True, text=True, env=self.e.env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("not a git repo, so the changed set cannot be told", proc.stderr)

    def test_the_rules_travel_as_json_and_the_module_imports_nothing_of_the_office(self):
        text = (LIB / "office_letterhead.py").read_text()
        self.assertNotIn("import office_", text)
        rules = json.dumps({"names": ["x[y]z"], "phrasing": [], "marks": [], "forbidden": ["Acme"], "binary": [".png"]})
        (self.repo / "n.txt").write_text("XyZ and acme\n")
        proc = subprocess.run([sys.executable, "-", "--rules-json", rules, "."], cwd=self.repo, capture_output=True,
                              text=True, env=self.e.env, input=(LIB / "office_letterhead.py").read_text())
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("n.txt:1: forbidden: 'acme'", proc.stdout)
        self.assertIn("n.txt:1: names: 'XyZ'", proc.stdout)

    def test_the_command_reads_the_offices_forbidden_file_and_never_writes_it(self):
        root = self.e.init()
        forbidden = root / "letterhead" / "forbidden.txt"
        (self.repo / "n.txt").write_text("secret sauce\n")
        proc = self.e.run("letterhead", "check", str(self.repo), cwd=root, check=0)
        self.assertFalse(forbidden.exists())
        forbidden.parent.mkdir()
        forbidden.write_text("secret sauce\n")
        proc = self.e.run("letterhead", "check", str(self.repo), cwd=root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("n.txt:1: forbidden: 'secret sauce'", proc.stdout)
        self.assertEqual(forbidden.read_text(), "secret sauce\n")
        self.assertIn("office letterhead check", self.e.run("letterhead", "check", "--help", cwd=root, check=0).stdout)
        self.assertIn("office letterhead check", self.e.run("help", "letterhead", "check", cwd=root, check=0).stdout)

    def test_the_suite_and_the_check_read_one_list(self):
        from test_office import FINGERPRINTS, MODEL_NAMES
        self.assertEqual(MODEL_NAMES, self.rules["names"])
        self.assertEqual(FINGERPRINTS, self.rules["phrasing"])
        self.assertIn("applied/", self.rules["marks"])
        self.assertTrue(any("bale/" in m for m in self.rules["marks"]))


class TestTheLetterheadCheckOnAHost(AudienceCase):
    hosted = True

    def test_on_project_runs_the_check_in_the_repo_there_and_writes_nothing(self):
        (self.clone / "src" / "a.py").write_text(f"import {A_NAME}\n")
        proc = self.run_office("letterhead", "check", "--on", "proj")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(f"src/a.py:1: names: '{A_NAME}'", proc.stdout)
        # The reach, then the check, which travels as python3's program on
        # stdin with the rules as one argument.
        calls = self.ssh.connections()
        self.assertEqual(len(calls), 2, calls)
        self.assertIn("python3 - --rules-json", calls[1][-1])
        self.assertEqual(self.ssh.left_on(HOST), [])
        git(self.clone, "checkout", "-q", "src/a.py", env=self.e.env)
        proc = self.run_office("letterhead", "check", "--on", "proj", "--all")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("the whole tree", proc.stderr)
        proc = self.run_office("letterhead", "check", "--on", "proj", "--words", str(self.root / self.folder / "delivery.md"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--words names a file on this machine", proc.stderr)


# --- 3. office deliver ---------------------------------------------------------------------------

class TestDeliver(AudienceCase):
    def test_the_crossing_pushes_one_curated_commit_and_nothing_of_bales(self):
        before = self.audience_refs()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Delivered: health-route is on origin for proj, 1 commit(s) by Zed Zee <z@example.org> onto main", proc.stdout)
        self.assertIn(f"covering {SID}", proc.stdout)
        self.assertIn("the workbench branch was not pushed", proc.stdout)
        # What was shown before the push.
        self.assertIn("branch:   health-route, from main", proc.stdout)
        self.assertIn("author:   Zed Zee <z@example.org>", proc.stdout)
        self.assertIn(f"sessions: {SID}", proc.stdout)
        self.assertIn("src/health.py | 2 +", proc.stdout)
        self.assertIn("commit 1: Add the health route", proc.stdout)
        self.assertIn("review: Health route for the API", proc.stdout)
        self.assertIn("to: Pat Reviewer", proc.stdout)
        # The audience: one branch more, one commit on it from main, by the
        # author, with the words, and no mark, tag, branch or file of bale's.
        self.assertEqual(sorted(set(self.audience_refs()) - set(before)), ["refs/heads/health-route"])
        log = self.audience_log()
        self.assertEqual(len(re.findall(r"^Zed Zee", log, re.M)), 1)
        first = log.splitlines()[0]
        self.assertEqual(first, "Zed Zee <z@example.org>|Zed Zee|Add the health route|The API answers /health with ok, and the test covers it.")
        parent = git(self.audience, "rev-parse", "health-route^", env=self.e.env).strip()
        self.assertEqual(parent, git(self.audience, "rev-parse", "main", env=self.e.env).strip())
        self.assertEqual(self.audience_tree(), ["README.md", "src/a.py", "src/health.py"])
        for pat in olh.compile_rules({"names": [], "phrasing": [], "marks": self.rules_marks()}):
            self.assertIsNone(pat[2].search(git(self.audience, "log", "--format=%B", "health-route", env=self.e.env)), pat[1])
        self.assertEqual(git(self.audience, "show", "health-route:src/health.py", env=self.e.env), 'def health():\n    return "ok"\n')
        # The folder's History, and what to do next.
        self.assertRegex(self.folder_md(), rf"- \d{{4}}-\d{{2}}-\d{{2}} delivered: health-route on origin of proj: sessions {SID}; workbench [0-9a-f]{{12}}; delivery [0-9a-f]{{12}}\n")
        self.assertIn("Next:", proc.stdout)
        self.assertIn("the branch is health-route, onto main; the review's title: Health route for the API", proc.stdout)
        self.assertIn("send it to: Pat Reviewer", proc.stdout)
        self.assertIn("office deliver: health-route to origin", self.e.git(self.root, "log", "-1", "--format=%s"))
        # The clone: its branch untouched, the office's refs gone, the guard in.
        self.assertEqual(git(self.clone, "symbolic-ref", "--short", "HEAD", env=self.e.env).strip(), "main")
        self.assertEqual([r for r in git(self.clone, "for-each-ref", "--format=%(refname)", env=self.e.env).split()
                          if r.startswith("refs/office/")], [])
        self.assertEqual(git(self.clone, "status", "--porcelain", env=self.e.env), "")
        self.assertTrue((self.clone / ".git" / "hooks" / "pre-push").is_file())
        self.assertEqual([d for d in self.e.tmpdir.glob("office-deliver*")], [])

    def rules_marks(self):
        return olh.load_rules_toml(RULES)["marks"]

    def test_refusals_before_anything_leaves(self):
        before = self.audience_refs()
        # No audience, by name.
        self.run_office("projects", "set", "proj", "--no-audience", check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("proj declares no audience, so nothing of it is delivered: office projects set proj --audience REMOTE", proc.stderr)
        self.run_office("projects", "set", "proj", "--audience", "origin", "--author", "Zed Zee <z@example.org>", check=0)
        # No words: what to write where.
        (self.root / self.folder / "delivery.md").unlink()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"{self.folder}/delivery.md is not written, so there are no words to deliver with", proc.stderr)
        self.assertIn("Delivery section of its notes.md", proc.stderr)
        self.assertIn("templates/delivery.md", proc.stderr)
        # Words that do not read.
        self.write_words("# Delivery\n\n## Review\n\nTitle\n")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("delivery.md: delivery.md has no Commit section", proc.stderr)
        self.write_words(WORDS)
        # A folder with no applied session.
        other = self.run_office("open", "other job", "--lane", "proj: src", check=0).stdout.strip().split("/")[1]
        (self.root / "desk" / other / "delivery.md").write_text(WORDS)
        proc = self.run_office("deliver", other, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"desk/{other} records no session that is applied in proj", proc.stderr)
        # A folder with no lane, and --on that disagrees with a lane.
        bare = self.run_office("open", "no lane", check=0).stdout.strip().split("/")[1]
        proc = self.run_office("deliver", bare, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"{bare} has no lane naming a project, so say which: office deliver {bare} --on PROJECT", proc.stderr)
        proc = self.run_office("deliver", self.name, "--on", "elsewhere", "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("lane names proj, not elsewhere", proc.stderr)
        # Piped without --yes: shown, then refused, nothing left behind.
        proc = self.run_office("deliver", self.name)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("commit 1: Add the health route", proc.stdout)
        self.assertIn(f"nothing left: office deliver {self.name} --yes pushes it; piped input is never asked", proc.stderr)
        self.assertEqual(self.audience_refs(), before)
        self.assertNotIn("delivered:", self.folder_md())
        self.assertEqual([r for r in git(self.clone, "for-each-ref", "--format=%(refname)", env=self.e.env).split()
                          if r.startswith("refs/office/")], [])
        self.assertEqual(git(self.clone, "worktree", "list", env=self.e.env).count("\n"), 1)

    def test_a_letterhead_hit_refuses_with_nothing_pushed(self):
        before = self.audience_refs()
        self.land_session(SID2, {"src/b.py": f"# written with {A_NAME}\n"}, "Add b")
        self.run_office("sessions", self.name, SID2, check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"src/b.py:1: names: '{A_NAME}'", proc.stdout)
        self.assertIn("the letterhead refuses 1 line(s)", proc.stderr)
        self.assertIn("nothing was pushed", proc.stderr)
        self.assertEqual(self.audience_refs(), before)
        self.assertNotIn("delivered:", self.folder_md())
        # The words are checked too.
        git(self.clone, "reset", "-q", "--hard", f"applied/{SID}", env=self.e.env)
        self.write_words(WORDS.replace("One route and its test.", "I hope this helps! One route."))
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("delivery.md:15: phrasing: 'I hope this helps'", proc.stdout)
        self.assertEqual(self.audience_refs(), before)

    def test_other_folders_sessions_ride_in_it_said_and_named(self):
        self.land_session(SID3, {"docs.md": "docs\n"}, "Document it")
        other = self.run_office("open", "other job", "--lane", "proj: docs", check=0).stdout.strip()
        self.run_office("sessions", other.split("/")[1], SID3, check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"the landed work carries sessions of other folders, which ride in the same delivery", proc.stderr)
        self.assertIn(f"{SID3} ({other})", proc.stderr)
        self.assertIn(f"office deliver {self.name} --others-too", proc.stderr)
        self.assertNotIn("refs/heads/health-route", self.audience_refs())
        proc = self.run_office("deliver", self.name, "--yes", "--others-too")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"and of other folders: {SID3} ({other})", proc.stdout)
        self.assertIn(f"covering {SID}, {SID3}", proc.stdout)
        self.assertIn(f"sessions {SID}, {SID3};", self.folder_md())
        self.assertEqual(self.audience_tree(), ["README.md", "docs.md", "src/a.py", "src/health.py"])

    def test_a_second_delivery_adds_to_the_branch_after_the_audience_moved(self):
        self.run_office("deliver", self.name, "--yes", check=0)
        first = git(self.audience, "rev-parse", "health-route", env=self.e.env).strip()
        # A coworker moves main; a second session lands.
        cow = self.e.tmp / "cow"
        git(self.e.tmp, "clone", "-q", str(self.audience), str(cow), env=self.e.env)
        (cow / "README.md").write_text("hello there\n")
        git(cow, "commit", "-qam", "Improve the readme", env=self.e.env)
        git(cow, "push", "-q", "origin", "main", env=self.e.env)
        self.land_session(SID2, {"docs.md": "# health\n"}, "Document the route")
        self.run_office("sessions", self.name, SID2, check=0)
        self.write_words(WORDS.replace("Add the health route", "Document the health route"))
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("(adding to the branch on the audience)", proc.stdout)
        self.assertIn("since the last delivery on health-route", proc.stdout)
        self.assertIn(f"covering {SID2};", proc.stdout)
        self.assertIn(" docs.md | 1 +", proc.stdout)
        self.assertNotIn("src/health.py", proc.stdout.split("changes:")[1].split("words")[0])
        self.assertEqual(self.audience_subjects(), ["Document the health route", "Add the health route", "Initial commit"])
        self.assertEqual(git(self.audience, "rev-parse", "health-route^", env=self.e.env).strip(), first)
        self.assertEqual(self.folder_md().count("delivered:"), 2)
        # Nothing new: refused.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("nothing new to deliver", proc.stderr)
        # A branch on the audience that is not this folder's.
        git(cow, "push", "-q", "origin", "main:refs/heads/theirs", env=self.e.env)
        self.land_session(SID3, {"more.md": "m\n"}, "More")
        self.run_office("sessions", self.name, SID3, check=0)
        proc = self.run_office("deliver", self.name, "--yes", "--branch", "theirs")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("origin already has a branch named theirs, and desk/", proc.stderr)
        self.assertIn("name another: --branch NAME", proc.stderr)
        proc = self.run_office("deliver", self.name, "--yes", "--branch", "health-more")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("refs/heads/health-more", self.audience_refs())
        self.assertEqual(git(self.audience, "ls-tree", "-r", "--name-only", "health-more", env=self.e.env).split(),
                         ["README.md", "docs.md", "more.md", "src/a.py", "src/health.py"])

    def test_several_commits_when_the_words_mark_them(self):
        self.land_session(SID2, {"docs.md": "# health\n"}, "Document the route")
        self.run_office("sessions", self.name, SID2, check=0)
        self.write_words("""# Delivery

## Commit

- paths: docs.md

Document the health route

## Commit

Add the health route

Its code.

## Review

Health route

Look.
""")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("2 commit(s) by Zed Zee", proc.stdout)
        self.assertIn("(takes: docs.md)", proc.stdout)
        self.assertEqual(self.audience_subjects(), ["Add the health route", "Document the health route", "Initial commit"])
        self.assertEqual(git(self.audience, "ls-tree", "-r", "--name-only", "health-route^", env=self.e.env).split(),
                         ["README.md", "docs.md", "src/a.py"])
        self.write_words("# D\n\n## Commit\n\nOne\n\n## Commit\n\nTwo\n\n## Review\n\nT\n")
        self.land_session(SID3, {"x.md": "x\n"}, "x")
        self.run_office("sessions", self.name, SID3, check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Commit 1 of 2 names no paths", proc.stderr)

    def test_a_conflict_with_the_audience_refuses_and_names_the_remedy(self):
        cow = self.e.tmp / "cow"
        git(self.e.tmp, "clone", "-q", str(self.audience), str(cow), env=self.e.env)
        (cow / "src" / "a.py").write_text("x = 99\n")
        git(cow, "commit", "-qam", "Change a", env=self.e.env)
        git(cow, "push", "-q", "origin", "main", env=self.e.env)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("the landed work does not go onto origin's main as it is now: conflicts in src/a.py", proc.stderr)
        self.assertIn("bring main into the workbench branch first", proc.stderr)
        self.assertNotIn("refs/heads/health-route", self.audience_refs())
        self.assertEqual(git(self.clone, "worktree", "list", env=self.e.env).count("\n"), 1)
        self.assertEqual(git(self.clone, "status", "--porcelain", env=self.e.env), "")

    def test_the_author_is_declared_never_the_clones_and_the_base_defaults_from_the_clone(self):
        before = self.audience_refs()
        self.run_office("projects", "set", "proj", "--no-author", check=0)
        git(self.clone, "config", "user.name", "Clone Own", env=self.e.env)
        git(self.clone, "config", "user.email", "own@example.org", env=self.e.env)
        # No author declared: the clone's own identity is never used;
        # piped, refused by name, with nothing made.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("proj declares no author", proc.stderr)
        self.assertIn("the clone's own identity is never used silently (the clone's is Clone Own <own@example.org>)",
                      proc.stderr)
        self.assertIn(f"office deliver {self.name} --author 'Name <email>' declares it and keeps it", proc.stderr)
        self.assertEqual(self.audience_refs(), before)
        # --author sets the field: declared, kept, and every commit carries it.
        proc = self.run_office("deliver", self.name, "--yes", "--author", "Pat Example <pat@example.org>")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("proj's author is Pat Example <pat@example.org>, kept in the floor plan", proc.stderr)
        self.assertIn('author = "Pat Example <pat@example.org>"', (self.root / "floor-plan" / "manifest.toml").read_text())
        self.assertEqual(self.audience_log().splitlines()[0].split("|")[:2], ["Pat Example <pat@example.org>", "Pat Example"])
        self.land_session(SID2, {"docs.md": "d\n"}, "d")
        self.run_office("sessions", self.name, SID2, check=0)
        # The base: declared, it is used; unset, the remote's HEAD; neither, refused.
        self.run_office("projects", "set", "proj", "--base", "nope", check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("did not answer for nope from this machine", proc.stderr)
        self.run_office("projects", "set", "proj", "--no-base", check=0)
        git(self.clone, "remote", "set-head", "origin", "-d", env=self.e.env)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("does not say which branch origin points at (no origin/HEAD)", proc.stderr)
        self.assertIn("office projects set proj --base BRANCH", proc.stderr)

    def test_the_review_url_for_known_hosts(self):
        self.assertEqual(odl.review_url("https://github.example.edu/ORG/REPO", "br", "main"),
                         "https://github.example.edu/ORG/REPO/compare/main...br?expand=1")
        self.assertEqual(odl.review_url("git@github.com:org/repo.git", "br", "main", "T x", "B\ny"),
                         "https://github.com/org/repo/compare/main...br?expand=1&title=T+x&body=B%0Ay")
        self.assertTrue(odl.review_url("https://gitlab.example.org/g/p.git", "br", "main").startswith(
            "https://gitlab.example.org/g/p/-/merge_requests/new?merge_request%5Bsource_branch%5D=br"))
        self.assertIsNone(odl.review_url("https://forge.example.org/o/r.git", "br", "main"))
        self.assertIsNone(odl.review_url(str(self.e.tmp / "audience.git"), "br", "main"))
        self.assertEqual(odl.parse_remote_url("ssh://git@host.example:2222/a/b/c.git"), ("host.example", "a/b", "c"))
        self.assertEqual(odl.branch_from_folder("2026-10-08-audience-line"), "audience-line")
        proc = self.e.run("deliver", "--help", cwd=self.root, check=0)
        self.assertIn("usage: office deliver", proc.stdout)
        # A GitHub-shaped audience: the next line is the URL, the words in it.
        git(self.clone, "remote", "set-url", "origin", "https://github.example.edu/ORG/REPO", env=self.e.env)
        git(self.clone, "remote", "add", "real", str(self.audience), env=self.e.env)
        self.run_office("projects", "set", "proj", "--audience", "real", "--base", "main", check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("the branch is health-route, onto main", proc.stdout)


class TestDeliverOnATerminal(AudienceCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_it_asks_once_and_n_pushes_nothing(self):
        before = self.audience_refs()
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver", self.name], self.root, self.e.env, [
            (b"Push health-route to origin as shown? (--yes) (y/n) [y]:", "n"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("stopped before anything left", seen)
        self.assertEqual(self.audience_refs(), before)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver"], self.root, self.e.env, [
            (b"(office deliver FOLDER)", "health"),
            (b"Push health-route to origin as shown? (--yes) (y/n) [y]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Delivered: health-route is on origin", seen)
        self.assertIn("refs/heads/health-route", self.audience_refs())

    def test_other_folders_sessions_are_asked_about(self):
        self.land_session(SID3, {"docs.md": "docs\n"}, "Document it")
        other = self.run_office("open", "other job", "--lane", "proj: docs", check=0).stdout.strip()
        self.run_office("sessions", other.split("/")[1], SID3, check=0)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver", self.name], self.root, self.e.env, [
            (b"deliver them too? (--others-too) (y/n) [y]:", "n"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"{SID3} ({other})", seen)
        self.assertIn("stopped before anything left", seen)
        self.assertNotIn("refs/heads/health-route", self.audience_refs())


class TestDeliverOnAHost(AudienceCase):
    hosted = True

    def test_the_landed_work_comes_here_as_a_bundle_and_the_push_is_from_here(self):
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"carried the landed work from {HOST}", proc.stderr)
        self.assertIn("checked by sha256", proc.stderr)
        self.assertIn("from this machine", proc.stderr)
        self.assertIn("Delivered: health-route is on origin for proj, 1 commit(s) by Zed Zee <z@example.org> onto main", proc.stdout)
        self.assertEqual(self.audience_log().splitlines()[0].split("|")[:3],
                         ["Zed Zee <z@example.org>", "Zed Zee", "Add the health route"])
        self.assertEqual(self.audience_tree(), ["README.md", "src/a.py", "src/health.py"])
        self.assertEqual([r for r in self.audience_refs() if "bale" in r or "applied" in r], [])
        # The host: three connections (the clone's facts, the bundle made,
        # the bundle read and its directory removed), nothing left in its
        # temporary directory, no push from there; the guard went in with
        # the declaration (projects add --audience, in setUp).
        calls = self.ssh.connections()
        self.assertTrue(all(c[0] == HOST for c in calls), calls)
        self.assertEqual(len(calls), 3, [c[-1][:60] for c in calls])
        self.assertTrue(any("git bundle create" in c[-1] for c in calls))
        self.assertFalse(any("git push" in c[-1] for c in calls))
        self.assertEqual(self.ssh.left_on(HOST), [])
        self.assertTrue((self.clone / ".git" / "hooks" / "pre-push").is_file())
        self.assertEqual([d for d in self.e.tmpdir.glob("office-deliver*")], [])
        self.assertRegex(self.folder_md(), r"delivered: health-route on origin of proj")
        # The second delivery: three connections (facts, the bundle, its read).
        self.land_session(SID2, {"docs.md": "d\n"}, "d")
        self.run_office("sessions", self.name, SID2, check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(self.ssh.connections()), 3, [c[-1][:60] for c in self.ssh.connections()])
        self.assertEqual(git(self.audience, "log", "--format=%s", "health-route", env=self.e.env).count("\n"), 3)

    def test_a_host_that_does_not_answer_stops_it_before_anything_is_fetched(self):
        self.run_office("projects", "set", "proj", "--host", DOWN, check=0)
        before = self.audience_refs()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"{DOWN} does not answer", proc.stderr)
        self.assertIn(f"then rerun: office deliver {self.name} --yes", proc.stderr)
        self.assertEqual([c[0] for c in self.ssh.connections()], [DOWN])
        self.assertEqual(self.audience_refs(), before)


# --- 4. the folder's two pages --------------------------------------------------------------------

class TestThePages(LandCase):
    def test_land_files_them_from_the_responses_notes(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes=NOTES)
        proc = self.run_office("land", sid, "--ratified", "--leave-open", "--response",
                               str(self.downloads / f"response-{sid}.tar.gz"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        folder = self.root / self.folder
        wt = (folder / "walkthrough.md").read_text()
        dl = (folder / "delivery.md").read_text()
        self.assertTrue(wt.startswith("# Walkthrough: fix-login\n\n<!-- filed by office land from " + sid))
        self.assertIn("\n## What changed\n\nThe route and its test.\n", wt)
        self.assertIn("\n## A hand test\n\nOpen /health.\n", wt)
        self.assertNotIn("Proposals", wt)
        self.assertTrue(dl.startswith("# Delivery: fix-login\n"))
        self.assertIn("\n- to: Pat Reviewer\n", dl)
        self.assertIn("\n## Commit\n\nAdd the health route\n\nThe API answers /health with ok.\n", dl)
        self.assertIn("\n## Review\n\nHealth route for the API\n", dl)
        words = h.parse_delivery(dl)
        self.assertEqual(words["to"], "Pat Reviewer")
        self.assertEqual(words["commits"][0]["subject"], "Add the health route")
        self.assertIn(f"filed {self.folder}/walkthrough.md: the walkthrough from {sid}'s notes.md", proc.stderr)
        self.assertIn("the folder's pages: walkthrough.md filed; delivery.md filed", proc.stderr)
        # What became of each after-land action stays land's last lines.
        self.assertTrue(proc.stdout.rstrip().endswith("ran (exit 0): touch AFTER-LAND-RAN"), proc.stdout)
        self.assertIn(f"office land: {sid}'s pages in {self.name}", self.subjects())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_a_response_without_the_sections_says_so_and_sessions_pages_files_later(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        tb = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes="# Notes\n\nOnly notes.\n")
        proc = self.run_office("land", sid, "--not-now", "--leave-open", "--response", str(tb), check=0)
        self.assertIn(f"{sid}'s notes.md carries no walkthrough or delivery section", proc.stderr)
        self.assertIn("office deliver needs delivery.md", proc.stderr)
        self.assertFalse((self.root / self.folder / "delivery.md").exists())
        tb2 = response_tarball(self.e.tmp / "later", sid, {"src/a.py": "fixed\n"}, notes=NOTES)
        proc = self.run_office("sessions", self.name, sid, "--pages", str(tb2), check=0)
        self.assertIn(f"filed {self.folder}/delivery.md", proc.stderr)
        self.assertTrue((self.root / self.folder / "delivery.md").is_file())
        proc = self.run_office("sessions", self.name, sid, "--pages", str(tb2), check=0)
        self.assertIn(f"rewrote {self.folder}/delivery.md", proc.stderr)
        proc = self.run_office("sessions", self.name, sid, "--pages", str(tb2), "--ratified")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--pages goes alone", proc.stderr)
        proc = self.run_office("sessions", self.name, sid, "--pages", "/nonexistent.tar.gz")
        self.assertEqual(proc.returncode, 1)

    def test_a_response_only_bale_found_names_the_line_that_files_them(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        elsewhere = self.e.tmp / "elsewhere"
        response_tarball(elsewhere, sid, {"src/a.py": "fixed\n"}, notes=NOTES)
        env = {"FAKE_BALE_SEARCH": str(elsewhere)}
        proc = self.run_office("land", sid, "--not-now", "--leave-open", extra=env, check=0)
        self.assertIn(f"Landed: {sid}", proc.stdout)
        self.assertIn(f"office sessions {self.name} {sid} --pages FILE files them", proc.stderr)
        self.assertNotIn("pages", proc.stdout.split("After land, in", 1)[1])
        self.assertFalse((self.root / self.folder / "delivery.md").exists())

    def test_the_templates_the_folder_and_what_rides_with_a_build_session(self):
        for name in ("walkthrough.md", "delivery.md"):
            text = (REPO / "templates" / name).read_text()
            self.assertIn("notes.md", text)
        self.assertIn("## Commit", (REPO / "templates" / "delivery.md").read_text())
        self.assertIn("## Review", (REPO / "templates" / "delivery.md").read_text())
        self.assertIn("## A hand test", (REPO / "templates" / "walkthrough.md").read_text())
        headings = re.findall(r"^## (.+)$", (REPO / "templates" / "folder.md").read_text(), re.M)
        self.assertEqual(headings[:7], ["Asked", "Questions and answers", "Correspondence", "Deliverables", "Walkthrough",
                                        "Delivery", "Concerns"])
        self.assertIn("## Walkthrough\n", self.folder_md())
        self.assertIn("## Delivery\n", self.folder_md())
        # The templates ride beside a build session's request, from the install.
        proc = self.run_office("start", self.name, "--on", "alpha", "--goal", "g", "--write", "src", check=0)
        self.assertIn("from the install: templates/walkthrough.md, templates/delivery.md", proc.stdout)
        tray = pathlib.Path(re.search(r"^Out tray: (.+)$", proc.stdout, re.M).group(1))
        import tarfile
        names = []
        for t in tray.glob("context-*.tar.gz"):
            with tarfile.open(t) as tf:
                names += tf.getnames()
        self.assertTrue(any(n.endswith("templates/delivery.md") for n in names), names)
        # An office session gets no templates.
        other = self.run_office("open", "office job", check=0).stdout.strip().split("/")[1]
        proc = self.run_office("start", other, "--in-office", "--goal", "g", check=0)
        self.assertNotIn("templates/delivery.md", proc.stdout)

    def test_an_old_folder_without_the_sections_still_takes_the_pages(self):
        md = self.root / self.folder / "folder.md"
        text = md.read_text()
        start, end = text.index("## Walkthrough"), text.index("## Concerns")
        md.write_text(text[:start] + text[end:])
        self.e.git(self.root, "commit", "-qam", "an older folder")
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        tb = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, notes=NOTES)
        self.run_office("land", sid, "--not-now", "--leave-open", "--response", str(tb), check=0)
        self.assertTrue((self.root / self.folder / "delivery.md").is_file())
        self.assertNotIn("## Walkthrough", md.read_text())


# --- 5. office relay ------------------------------------------------------------------------------

RELAY_BALE = '''#!/usr/bin/env bash
# The suite's bale for office relay: `relay SID -` reads the answer from
# stdin and prints the worker's block when the answer carries the
# marker; everything else goes to the fake land bale behind it.
if [ "$1" = relay ] && [ "$3" = "-" ]; then
  answer="$(cat)"
  printf '%s\\n' "relay $2 $(pwd) $(printf '%s' "$answer" | wc -c | tr -d ' ')" >> "RELAY_CALLS"
  case "$answer" in *"the planner's answer"*) ;; *) echo "[bale] error: relay: the trailer does not match" >&2; exit 1 ;; esac
  echo "[bale] relay: round 2 recorded for $2" >&2
  echo "BALE EXCHANGE BEGIN $2"
  echo "from: planner"
  echo "$answer"
  echo "BALE EXCHANGE END"
  exit 0
fi
exec "NEXT_BALE" "$@"
'''


class TestRelay(LandCase):
    def setUp(self):
        super().setUp()
        d = self.e.tmp / "relay-bale"
        d.mkdir()
        self.relay_calls = d / "calls.txt"
        script = d / "bale"
        script.write_text(RELAY_BALE.replace("RELAY_CALLS", str(self.relay_calls)).replace("NEXT_BALE", str(self.fake.dir / "bale")))
        script.chmod(0o755)
        self.e.env["PATH"] = f"{d}{os.pathsep}{self.e.env['PATH']}"
        self.answer = self.e.tmp / "answer.md"
        self.answer.write_text("BALE EXCHANGE BEGIN x\nthe planner's answer\nBALE EXCHANGE END\n")

    def test_it_runs_bale_relay_in_the_sessions_repo_with_the_answer_on_stdin(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        proc = self.run_office("relay", sid, str(self.answer))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"BALE EXCHANGE BEGIN {sid}\nfrom: planner\n", proc.stdout)
        self.assertIn(f"bale relay {sid} - in {self.proj}, with {self.answer} on its stdin", proc.stderr)
        # (the fake's $(cat) drops the file's last newline from its count)
        self.assertEqual(self.relay_calls.read_text().strip(), f"relay {sid} {os.path.realpath(self.proj)} {self.answer.stat().st_size - 1}")
        # A bare name is found in the downloads; a refusal is bale's words.
        h.set_machine_downloads(self.e.home / ".config" / "office-src" / "machine.toml", [str(self.downloads)])
        (self.downloads / "reply.md").write_text("the planner's answer\n")
        proc = self.run_office("relay", sid, "reply.md", check=0)
        self.assertIn("with " + str(self.downloads / "reply.md") + " on its stdin", proc.stderr)
        (self.downloads / "bad.md").write_text("nothing\n")
        proc = self.run_office("relay", sid, "bad.md")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("the trailer does not match", proc.stderr)
        self.assertIn(f"bale relay {sid} refused", proc.stderr)
        proc = self.run_office("relay", sid, "missing.md")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("missing.md is not in", proc.stderr)
        proc = self.run_office("relay", "2026-01-01-nothing-001", str(self.answer))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("is not open in this office or in any project it scopes", proc.stderr)
        self.assertIn("usage: office relay", self.run_office("relay", "--help", check=0).stdout)


class TestRelayOnAHost(LandCase):
    def setUp(self):
        super().setUp()
        self.ssh = FakeSsh(self.e.tmp)
        d = self.e.tmp / "relay-bale"
        d.mkdir()
        self.relay_calls = d / "calls.txt"
        (d / "bale").write_text(RELAY_BALE.replace("RELAY_CALLS", str(self.relay_calls)).replace("NEXT_BALE", str(self.fake.dir / "bale")))
        (d / "bale").chmod(0o755)
        self.e.env["PATH"] = self.ssh.path(f"{d}{os.pathsep}{self.e.env['PATH']}")
        self.e.run("projects", "add", "far", str(self.proj), "--host", HOST, cwd=self.root, check=0)
        # far alone: alpha, its twin on this machine, would find the same session.
        manifest = self.root / "floor-plan" / "manifest.toml"
        text = manifest.read_text()
        head, _, tail = text.partition("[projects.alpha]")
        manifest.write_text(head + "[projects.far]" + tail.split("[projects.far]", 1)[1])
        self.e.git(self.root, "commit", "-qam", "far alone")
        self.answer = self.e.tmp / "answer.md"
        self.answer.write_text("the planner's answer\n")

    def test_the_answer_is_piped_through_the_shell(self):
        proc = self.e.run("start", self.name, "--on", "far", "--goal", "g", "--write", "src", cwd=self.root, check=0)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.ssh.reset()
        proc = self.e.run("relay", sid, str(self.answer), cwd=self.root)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"BALE EXCHANGE BEGIN {sid}", proc.stdout)
        self.assertIn(f"(through {HOST})", proc.stderr)
        self.assertEqual(self.relay_calls.read_text().strip(), f"relay {sid} {os.path.realpath(self.proj)} {self.answer.stat().st_size - 1}")
        fed = [c for c in self.ssh.connections() if "bale relay" in c[-1]]
        self.assertEqual(len(fed), 1, self.ssh.connections())
        self.assertEqual(self.ssh.left_on(HOST), [])


# --- 6. the record --------------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_version_the_releases_the_readme_the_doctrine_and_the_front_sheet(self):
        version = (REPO / "VERSION").read_text().strip()
        self.assertGreaterEqual(h.compare_versions(version, "0.17.0"), 0)
        self.assertIn("## 0.17.0", (REPO / "RELEASES.md").read_text())
        readme = (REPO / "README.md").read_text()
        for words in ("office deliver", "office letterhead check", "office relay", "--audience", "delivery.md", "walkthrough.md"):
            self.assertIn(words, readme, words)
        doctrine = (REPO / "doctrine/OFFICE.md").read_text()
        for words in ("office deliver", "office letterhead check", "walkthrough.md", "delivery.md", "`audience`", "`author`", "`base`",
                      "push guard"):
            self.assertIn(words, doctrine, words)
        self.assertIn("0.17.0", (REPO / RECORD_DIR / "context" / "front-sheet.md").read_text())
        import tomllib
        cons = tomllib.loads((REPO / "share/bale-consumption.toml").read_text())
        self.assertEqual(cons["surfaces"]["relay_answer"]["argv"], ["relay", "{sid}", "-"])
        verbs = tomllib.loads((REPO / "share/verbs.toml").read_text())["verbs"]
        for name in ("deliver", "letterhead-check", "relay"):
            self.assertTrue(verbs[name]["built"], name)
        self.assertIn("desk/{folder}/delivery.md", verbs["build"]["lands"])
        self.assertIn("delivered", h.HISTORY_VERBS)
        # deliver is the occupant's (office help); the other two are
        # plumbing, listed with every verb (office help --all, 0.22.0).
        proc = subprocess.run([str(REPO / "bin/office"), "help", "--all"], capture_output=True, text=True)
        for words in ("office deliver", "office letterhead check", "office relay"):
            self.assertIn(words, proc.stdout, words)
        self.assertIn("office deliver", subprocess.run([str(REPO / "bin/office"), "help"], capture_output=True,
                                                       text=True).stdout)

    def test_no_name_from_the_brief_is_in_the_tool(self):
        """The brief's hosts, people and projects are probe targets only;
        test_office's text rule holds the whole tree to it, and this
        names the files this release added."""
        from test_office import OFFICE_SPECIFIC
        for rel in ("lib/office_deliver.py", "lib/office_letterhead.py", "share/letterhead.toml", "templates/delivery.md",
                    "templates/walkthrough.md", "tests/test_audience_line.py"):
            text = (REPO / rel).read_text().lower()
            for word in OFFICE_SPECIFIC:
                self.assertNotIn(word, text, f"{rel} names {word!r}")


if __name__ == "__main__":
    unittest.main()
