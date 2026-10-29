"""Tests for office-src 0.36.0: no bale commit leaves in a delivery, in
content any more than in name.

Delivering a work office's folder 6 on 2026-10-28, bale's own commit
`bale: ignore .bale/` (1ee6bc7, .bale/ added to .gitignore where bale was
first set up in the clone) rode in beside the session's work: office
deliver squashed the whole workbench range, took only bale's names out
of the index, and the letterhead had no rule for a bale path. Two
changes, each pinned here:

1. What bale's own commits changed stays out. The commits bale makes for
   itself (its housekeeping commits, `bale: ...`, and its sweeps; never a
   session's work commit or its landing merge) are undone on the
   workbench's tip before the squash, each named in the plan. A line
   later work already took out is simply gone; later work on the same
   lines takes bale's lines out one by one when adding lines was all bale
   did there, and refuses by name otherwise.
2. A bale path is one of the letterhead's marks: a line that leaves
   naming .bale/, bale.toml or .baleignore refuses the delivery, the
   backstop for a bale line that reaches the squash some other way. The
   files taken out of the index are named never read, so bale.toml's own
   words do not refuse a delivery they are not in.

Run with the rest of the suite:

    tests/run.sh test_bale_own_commits
"""

import json
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO  # noqa: E402
from test_read_side import FIXTURES  # noqa: E402
from test_audience_line import AudienceCase, RECORD_DIR, SID, SID2, WORDS, git  # noqa: E402
from test_project_on_host import HOST  # noqa: E402

import office_bale as ob  # noqa: E402
import office_deliver as odl  # noqa: E402
import office_host as ohost  # noqa: E402
import office_letterhead as olh  # noqa: E402

RULES = REPO / "share" / "letterhead.toml"
HOUSEKEEPING = "bale: ignore .bale/"


# --- 1. which commits are bale's own ---------------------------------------------------------------

class TestBalesOwnCommits(unittest.TestCase):
    def setUp(self):
        self.cons = ob.Consumption()

    def test_the_housekeeping_subject_is_the_one_the_probe_captured(self):
        # The convention is pinned to a real capture, as the other shapes
        # are: a bale that renames the commit fails here, not in a delivery.
        captured = json.loads((FIXTURES / "watches" / "git" / "office-src_subjects.json").read_text(encoding="utf-8"))
        subjects = [line.split("\t")[2] for line in captured["stdout"]]
        self.assertIn(HOUSEKEEPING, subjects)
        kinds = {s: self.cons.own_commit(s) for s in subjects}
        own = sorted(s for s, is_own in kinds.items() if is_own)
        self.assertIn(HOUSEKEEPING, own)
        self.assertTrue(all(s == HOUSEKEEPING or s.startswith("[bale sweep ") for s in own), own)
        # Every work commit and every merge is the work, never bale's own.
        self.assertTrue(any(s.startswith("[bale 2026") for s in subjects))
        self.assertTrue(any(s.startswith("Merge bale ") for s in subjects))
        self.assertFalse(any(is_own for s, is_own in kinds.items() if s.startswith(("[bale 2026", "Merge bale "))))
        self.assertFalse(kinds["office-src"])

    def test_the_shapes(self):
        for s in (HOUSEKEEPING, "bale: anything", f"[bale sweep {SID}] applied", f"[bale sweep {SID}] closed-read-only"):
            self.assertTrue(self.cons.own_commit(s), s)
        for s in (f"[bale {SID}] work", f"Merge bale {SID}", "bale:", "bale:x", "Bale: no", "a bale: of hay",
                  "[bale sweep] applied", "Add .bale/ to .gitignore"):
            self.assertFalse(self.cons.own_commit(s), s)
        self.assertEqual(self.cons.surface("commits")["own"], ["bale: "])


# --- 2. a bale path is a mark ----------------------------------------------------------------------

class TestABalePathIsAMark(unittest.TestCase):
    def setUp(self):
        self.compiled = [c for c in olh.compile_rules(olh.load_rules_toml(RULES)) if c[0] == "marks"]

    def hits(self, text):
        return [(n, what) for _, n, kind, what, _ in olh.hits_in_text(text, self.compiled, "f") if kind == "marks"]

    def test_every_name_bale_makes_in_a_working_copy_is_matched_but_the_record_directory(self):
        # office_host.EXCLUDE_LINES and the marks are one list: the record
        # directory is a name already (its spelling is a model's).
        names = olh.load_rules_toml(RULES)["names"]
        for name in ohost.EXCLUDE_LINES:
            if name == RECORD_DIR + "/":
                self.assertTrue(any(re.search(p, name, re.I) for p in names), name)
                continue
            self.assertEqual(len(self.hits(name)), 1, name)

    def test_the_lines_of_the_case_and_the_files_named_after_the_directory(self):
        self.assertEqual(self.hits(".bale/\n"), [(1, ".bale")])
        self.assertEqual(self.hits("x\n# bale's own\n.bale/\nbale.toml\n.baleignore\n"),
                         [(3, ".bale"), (4, "bale.toml"), (5, ".baleignore")])
        for line in ("a planner's x.bale-bundle", "staging/.bale-manifest.json", "see .bale/outbox", "in `.bale`"):
            self.assertEqual(len(self.hits(line)), 1, line)

    def test_plain_words_stay_clean(self):
        for line in ("a bale of hay", "balefully", "the bale tool", "bale.tomlx", "bale/x", "bale pack --json",
                     "office deliver", "my.balefile"):
            self.assertEqual(self.hits(line), [], line)
        # bale's branch mark is untouched by the new ones.
        self.assertEqual([w for _, w in self.hits(f"on bale/{SID}")], [f"bale/{SID[:11]}", SID])


# --- 3. deliver takes what bale's own commits changed out ------------------------------------------

class TestDeliverTakesBalesOwnOut(AudienceCase):
    def bale_ignores(self, text=".bale/\n", append=False):
        """bale's housekeeping commit on the clone's workbench branch, as
        bale makes it where it is first set up."""
        path = self.clone / ".gitignore"
        path.write_text((path.read_text() if append and path.exists() else "") + text)
        git(self.clone, "add", ".gitignore", env=self.e.env)
        git(self.clone, "commit", "-qm", HOUSEKEEPING, env=self.e.env)
        return git(self.clone, "rev-parse", "HEAD", env=self.e.env).strip()

    def by_hand(self, rel, text, subject):
        (self.clone / rel).write_text(text)
        git(self.clone, "add", "-f", rel, env=self.e.env)
        git(self.clone, "commit", "-qm", subject, env=self.e.env)

    def test_the_housekeeping_commit_rides_nowhere_and_is_named(self):
        sha = self.bale_ignores()
        before = self.audience_refs()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # Two of bale's own: this one and the world's sweep, newest first.
        self.assertIn(f"taking what 2 commit(s) of bale's own changed out of the delivery: {sha[:12]} {HOUSEKEEPING}; ",
                      proc.stderr)
        self.assertIn("taken out: what 2 commit(s) of bale's own changed, which never leaves:", proc.stdout)
        self.assertIn(f"    {sha[:12]} {HOUSEKEEPING} (.gitignore)\n    ", proc.stdout)
        self.assertIn(f"[bale sweep {SID}] applied ({RECORD_DIR}/telemetry/{SID}.json)\n", proc.stdout)
        self.assertNotIn(".gitignore", proc.stdout.split("changes:")[1].split("words")[0])
        self.assertNotIn("one by one", proc.stdout)
        # The audience: the work, and no .gitignore at all.
        self.assertEqual(sorted(set(self.audience_refs()) - set(before)), ["refs/heads/health-route"])
        self.assertEqual(self.audience_tree(), ["README.md", "src/a.py", "src/health.py"])
        self.assertEqual(self.audience_subjects(), ["Add the health route", "Initial commit"])
        self.assertNotIn(".bale", git(self.audience, "log", "-p", "health-route", env=self.e.env))
        # The clone: its branch where it was, the temporary commits gone with
        # the worktree, nothing of the office's left.
        self.assertEqual(git(self.clone, "rev-parse", "HEAD", env=self.e.env).strip(), sha)
        self.assertEqual(git(self.clone, "status", "--porcelain", env=self.e.env), "")
        self.assertEqual(git(self.clone, "worktree", "list", env=self.e.env).count("\n"), 1)
        self.assertEqual([r for r in git(self.clone, "for-each-ref", "--format=%(refname)", env=self.e.env).split()
                          if r.startswith("refs/office/")], [])
        self.assertEqual([d for d in self.e.tmpdir.glob("office-deliver*")], [])

    def test_a_line_appended_to_a_file_the_audience_has_leaves_that_file_as_the_audience_has_it(self):
        cow = self.e.tmp / "cow"
        git(self.e.tmp, "clone", "-q", str(self.audience), str(cow), env=self.e.env)
        (cow / ".gitignore").write_text("*.pyc\n")
        git(cow, "add", "-A", env=self.e.env)
        git(cow, "commit", "-qm", "Ignore caches", env=self.e.env)
        git(cow, "push", "-q", "origin", "main", env=self.e.env)
        git(self.clone, "pull", "-q", "--no-rebase", "origin", "main", env=self.e.env)
        self.bale_ignores(append=True)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(git(self.audience, "show", "health-route:.gitignore", env=self.e.env), "*.pyc\n")
        self.assertNotIn(".gitignore", proc.stdout.split("changes:")[1].split("words")[0])

    def test_a_line_later_work_already_took_out_is_simply_gone(self):
        self.by_hand(".gitignore", "*.pyc\n", "Ignore caches")
        sha = self.bale_ignores(append=True)
        self.by_hand(".gitignore", "*.pyc\n", "Stop ignoring it")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"{sha[:12]} {HOUSEKEEPING} (.gitignore): nothing left to undo: later work on the workbench had "
                      "already taken it out", proc.stdout)
        self.assertEqual(git(self.audience, "show", "health-route:.gitignore", env=self.e.env), "*.pyc\n")

    def test_later_work_on_the_same_lines_takes_bales_lines_out_one_by_one(self):
        # bale created .gitignore; a later commit appended to it. git's
        # revert sees a modify/delete conflict; bale's one line goes, the
        # appended one leaves.
        sha = self.bale_ignores()
        self.by_hand(".gitignore", ".bale/\n*.log\n", "Ignore logs")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"{sha[:12]} {HOUSEKEEPING} (.gitignore): its lines taken out of .gitignore one by one, since "
                      "later work on the workbench touches the same place", proc.stdout)
        self.assertEqual(git(self.audience, "show", "health-route:.gitignore", env=self.e.env), "*.log\n")
        self.assertRegex(proc.stdout, r"\.gitignore\s+\|\s+1 \+\n")
        self.assertIn("files: A .gitignore; M src/a.py; A src/health.py", proc.stdout)
        # bale appended to a file; later work appended right after it (a
        # content conflict); the file keeps its line and the later one.
        git(self.clone, "reset", "-q", "--hard", f"applied/{SID}", env=self.e.env)
        self.by_hand(".gitignore", "*.pyc\n", "Ignore caches")
        sha = self.bale_ignores(append=True)
        self.by_hand(".gitignore", "*.pyc\n.bale/\n*.log\n", "Ignore logs")
        proc = self.run_office("deliver", self.name, "--yes", "--branch", "again")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"{sha[:12]} {HOUSEKEEPING} (.gitignore): its lines taken out of .gitignore one by one", proc.stdout)
        self.assertEqual(git(self.audience, "show", "again:.gitignore", env=self.e.env), "*.pyc\n*.log\n")

    def test_a_commit_that_did_more_than_add_lines_refuses_by_name_when_later_work_touches_them(self):
        self.by_hand(".gitignore", "*.pyc\n", "Ignore caches")
        (self.clone / ".gitignore").write_text(".bale/\n")
        git(self.clone, "commit", "-qam", HOUSEKEEPING, env=self.e.env)
        sha = git(self.clone, "rev-parse", "HEAD", env=self.e.env).strip()
        self.by_hand(".gitignore", ".bale/\n*.log\n", "Ignore logs")
        before = self.audience_refs()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"what bale's own commit {sha[:12]} ({HOUSEKEEPING}) changed in .gitignore cannot be taken out of "
                      "the delivery: the workbench branch's later work touches the same lines, and that commit did more "
                      "there than add lines", proc.stderr)
        self.assertIn("undo its change to .gitignore by hand on the workbench branch", proc.stderr)
        self.assertIn("nothing was pushed", proc.stderr)
        self.assertEqual(self.audience_refs(), before)
        self.assertNotIn("delivered:", self.folder_md())
        self.assertEqual(git(self.clone, "status", "--porcelain", env=self.e.env), "")
        self.assertEqual(git(self.clone, "worktree", "list", env=self.e.env).count("\n"), 1)
        self.assertEqual([d for d in self.e.tmpdir.glob("office-deliver*")], [])

    def test_a_sweep_is_bales_own_and_a_second_delivery_never_sees_an_older_one(self):
        # The world's sweep wrote bale's record; it was never delivered
        # (the record directory is excluded) and is now taken out too.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"[bale sweep {SID}] applied ({RECORD_DIR}/telemetry/{SID}.json)", proc.stdout)
        self.assertEqual(self.audience_tree(), ["README.md", "src/a.py", "src/health.py"])
        # A second delivery reads the range since the first: the first
        # range's commits of bale's own are not read again.
        self.bale_ignores()
        self.land_session(SID2, {"docs.md": "d\n"}, "d", record=False)
        self.run_office("sessions", self.name, SID2, check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("taken out: what 1 commit(s) of bale's own changed", proc.stdout)
        self.assertNotIn("bale sweep", proc.stdout.split("Delivery of")[1])
        self.assertEqual(self.audience_tree(), ["README.md", "docs.md", "src/a.py", "src/health.py"])

    def test_the_backstop_a_bale_path_in_a_line_that_leaves_is_refused(self):
        # Not bale's commit: a session's work added the line, so the squash
        # carries it, and the letterhead names it.
        self.land_session(SID2, {".gitignore": "*.pyc\n.bale/\n"}, "Ignore things", record=False)
        self.run_office("sessions", self.name, SID2, check=0)
        before = self.audience_refs()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(".gitignore:2: marks: '.bale' in: .bale/", proc.stdout)
        self.assertIn("the letterhead refuses 1 line(s)", proc.stderr)
        self.assertEqual(self.audience_refs(), before)
        # The words are held to it too.
        git(self.clone, "reset", "-q", "--hard", f"applied/{SID}", env=self.e.env)
        self.write_words(WORDS.replace("The pullsheet code is untouched.", "bale.toml is untouched."))
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("delivery.md:15: marks: 'bale.toml' in: One route and its test. bale.toml is untouched.", proc.stdout)
        self.assertEqual(self.audience_refs(), before)

    def test_a_tracked_file_of_bales_is_never_read_so_its_own_words_refuse_nothing(self):
        # bale.toml tracked on the workbench and naming bale's directory: it
        # is taken out of the index, left on the worktree's disk, and the
        # check is told never to read it.
        (self.clone / ".git" / "info" / "exclude").write_text(".bale/\n")
        self.by_hand("bale.toml", "# bale\n[apply]\nstaging = '.bale/staging'\n", "Configure bale")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("1 file(s) of bale's never read: bale.toml", proc.stdout)
        self.assertEqual(self.audience_tree(), ["README.md", "src/a.py", "src/health.py"])


class TestDeliverTakesBalesOwnOutOnAHost(AudienceCase):
    hosted = True

    def test_the_commit_comes_here_in_the_bundle_and_is_undone_in_the_mirror(self):
        (self.clone / ".gitignore").write_text(".bale/\n")
        git(self.clone, "add", ".gitignore", env=self.e.env)
        git(self.clone, "commit", "-qm", HOUSEKEEPING, env=self.e.env)
        sha = git(self.clone, "rev-parse", "HEAD", env=self.e.env).strip()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"    {sha[:12]} {HOUSEKEEPING} (.gitignore)\n", proc.stdout)
        self.assertEqual(self.audience_tree(), ["README.md", "src/a.py", "src/health.py"])
        # Still three connections: the undoing happens here, in the mirror.
        self.assertEqual(len(self.ssh.connections()), 3, [c[-1][:60] for c in self.ssh.connections()])
        self.assertEqual(self.ssh.left_on(HOST), [])
        self.assertEqual([d for d in self.e.tmpdir.glob("office-deliver*")], [])


# --- 4. the record -----------------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_version_the_release_the_readme_the_doctrine_and_the_front_sheet_say_it(self):
        # 0.36.0 or later (0.37.0 moved past it), as the record pins of the
        # releases before it read.
        version = tuple(int(x) for x in (REPO / "VERSION").read_text().strip().split("."))
        self.assertGreaterEqual(version, (0, 36, 0))
        releases = (REPO / "RELEASES.md").read_text()
        entry = releases.split("## 0.36.0", 1)[1].split("\n## ", 1)[0]
        for word in ("bale: ignore .bale/", "Additive", "take_out_own", "test_bale_own_commits.py", "marks"):
            self.assertIn(word, entry)
        readme = " ".join((REPO / "README.md").read_text().split())
        self.assertIn("what bale's own commits changed is taken out", readme)
        self.assertIn("a bale path (`.bale/`, `bale.toml`, `.baleignore`) is one of the letterhead's marks", readme)
        doctrine = " ".join((REPO / "doctrine" / "OFFICE.md").read_text().split())
        self.assertIn("holding no bale commit, merge, tag or branch, nothing a bale commit of its own changed", doctrine)
        self.assertIn("a bale path named in a line that leaves is one of bale's marks", doctrine)
        sheet = (REPO / RECORD_DIR / "context" / "front-sheet.md").read_text()
        self.assertIn("- 0.36.0 (session 2026-10-28-office-deliver-squashes-the-content-of-004)", sheet)
        # The usage text says it, and the module table names the test.
        text = (REPO / "bin" / "office").read_text()
        self.assertIn("what bale's own commits in that work changed", text)
        self.assertFalse((REPO / "migrations" / "0.36.0.sh").exists())


if __name__ == "__main__":
    unittest.main()
