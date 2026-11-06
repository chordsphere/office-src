"""Tests for office-src 0.51.0: bale's own change is taken out of the
workbench through a session, never by hand (0.40.0's first proposal, as
0.42.0 wrote it up), with 0.47.0's two proposals beside it. One class or
two per item:

1. The undo job. Where take_out_own refused a commit of bale's own that
   did more than add lines where later work touches them, deliver writes
   an undo job into the folder (every path that refused, in three versions
   and the commit's diff), names `office start N --undo-bale`, and pushes
   nothing; one job a folder at a time, of either kind.
2. The session. office start N --undo-bale packs it on the job's project:
   the folder alone, the job's paths as the forecast, the goal composed,
   the brief from templates/undo-brief.md, the session named on the page.
3. The landing. office land closes the job (an `undone` History line, the
   materials gone), and the next delivery takes the paths the session took
   bale's commit out of as the workbench holds them: the whole loop through
   the office's own commands, here and on a host; the waiting job offered
   by key wherever a merge job is.
4. 0.47.0's two: the audience's side capped in a merge job's materials
   (every path still listed, those past the cap marked not copied), and an
   empty response landed (the fake bale lands and tags it as bale 0.4.56
   does), a merge session whose every resolution is the workbench's ending
   in the merge commit.

The world is test_deliver_merges' MergeCase (test_host_refresh's audience,
workbench clone and fake bale answering `bale status --json`). Run with the
rest of the suite:

    tests/run.sh test_undo_bale
"""

import os
import pathlib
import re
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO  # noqa: E402
from test_audience_line import SID, git  # noqa: E402
from test_project_on_host import HOST  # noqa: E402
from test_start import FakePackBale  # noqa: E402
from test_land import FakeLandBale, response_tarball  # noqa: E402
from test_deliver_merges import MergeCase, DAY  # noqa: E402
from test_home_screen import home  # noqa: E402
from test_home_screen_offers import number_of, open_status  # noqa: E402

import office_bale as ob  # noqa: E402
import office_deliver as odl  # noqa: E402
import office_helper as oh  # noqa: E402

HOUSEKEEPING = "bale: ignore .bale/"
SID_U = "2026-10-29-health-route-undo-001"


def flat(text):
    return " ".join(text.split())


class UndoCase(MergeCase):
    """MergeCase's world, with one of bale's own commits on the workbench
    that the take-out cannot undo: .gitignore held `*.pyc`, bale's commit
    made it `.bale/` (more than adding a line), and later work appended
    `*.log` right after bale's line."""

    def by_hand(self, rel, text, subject):
        (self.clone / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.clone / rel).write_text(text)
        git(self.clone, "add", "-f", rel, env=self.e.env)
        git(self.clone, "commit", "-qm", subject, env=self.e.env)
        return git(self.clone, "rev-parse", "HEAD", env=self.e.env).strip()

    def refusing_commit(self, files=None):
        """bale's own commit, and later work on the same lines: files is
        {path: (before, bale's, later)}; its sha."""
        files = files or {".gitignore": ("*.pyc\n", ".bale/\n", ".bale/\n*.log\n")}
        for rel, (before, _, _) in files.items():
            self.by_hand(rel, before, f"Start {rel}")
        for rel, (_, bales, _) in files.items():
            (self.clone / rel).write_text(bales)
            git(self.clone, "add", "-f", rel, env=self.e.env)
        git(self.clone, "commit", "-qm", HOUSEKEEPING, env=self.e.env)
        sha = git(self.clone, "rev-parse", "HEAD", env=self.e.env).strip()
        for rel, (_, bales, later) in files.items():
            if later != bales:
                self.by_hand(rel, later, f"Go on with {rel}")
        return sha

    def undo_dir(self):
        return self.root / self.folder / "undo"

    def undo_job(self):
        return odl.read_undo_job(self.root / self.folder)

    def nothing_moved(self, before_refs, head):
        self.assertEqual(self.audience_refs(), before_refs)
        self.assertNotIn("delivered:", self.folder_md())
        self.assertEqual(self.clone_ref("HEAD"), head)
        self.assertEqual(git(self.clone, "status", "--porcelain", env=self.e.env), "")
        self.assertEqual(git(self.clone, "worktree", "list", env=self.e.env).count("\n"), 1)
        self.assertEqual([r for r in git(self.clone, "for-each-ref", "--format=%(refname)", env=self.e.env).split()
                          if r.startswith("refs/office/")], [])
        self.assertEqual([d for d in self.e.tmpdir.glob("office-deliver*")], [])


# --- 1. the undo job ---------------------------------------------------------------------------------

class TestTheUndoJob(UndoCase):
    def test_a_refusal_writes_the_job_and_names_the_undo_session(self):
        sha = self.refusing_commit()
        before, head = self.audience_refs(), self.clone_ref("HEAD")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        err = flat(proc.stderr)
        self.assertIn(f"what bale's own commit {sha[:12]} ({HOUSEKEEPING}) changed in .gitignore cannot be taken out "
                      "of the delivery", err)
        self.assertIn(f"office start {self.name} --undo-bale sends the session that takes bale's own change out of the "
                      "workbench", err)
        self.assertIn(f"the undo's materials are in {self.folder}/undo/", err)
        self.assertIn("nothing was pushed", err)
        self.assertNotIn("by hand", err)
        self.nothing_moved(before, head)
        # The materials: before, bale's and the workbench's, and the diff.
        u = self.undo_dir()
        self.assertEqual((u / "before" / ".gitignore").read_text(), "*.pyc\n")
        self.assertEqual((u / "bale" / ".gitignore").read_text(), ".bale/\n")
        self.assertEqual((u / "workbench" / ".gitignore").read_text(), ".bale/\n*.log\n")
        diff = (u / "bale.diff").read_text()
        self.assertIn(f"commit {sha}\nSubject: {HOUSEKEEPING}\n", diff)
        self.assertIn("-*.pyc\n+.bale/\n", diff)
        self.assertFalse((u / "log.txt").exists())
        self.assertFalse((u / "parted").exists())
        self.assertFalse((u / "audience").exists())
        job = self.undo_job()
        self.assertEqual((job["project"], job["commit"], job["subject"], job["workbench"], job["files"],
                          job["session"], job["earlier"]),
                         ("proj", sha, HOUSEKEEPING, head, [".gitignore"], None, None))
        self.assertEqual(job["parent"], git(self.clone, "rev-parse", f"{sha}^", env=self.e.env).strip())
        self.assertTrue(odl.is_undo(job))
        self.assertIsNone(odl.read_merge_job(self.root / self.folder))
        # Committed in the office, on its own.
        self.office_clean()
        self.assertEqual(git(self.root, "log", "-1", "--format=%s", env=self.e.env).strip(),
                         f"office deliver: the undo's materials for {self.name}")
        # Asked again with nothing sent: the same line, nothing new committed.
        commits = git(self.root, "rev-list", "--count", "HEAD", env=self.e.env)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertIn(f"office start {self.name} --undo-bale sends", flat(proc.stderr))
        self.assertEqual(git(self.root, "rev-list", "--count", "HEAD", env=self.e.env), commits)

    def test_every_path_that_refuses_is_in_the_job_and_one_bale_only_added_to_is_not(self):
        sha = self.refusing_commit({
            ".gitignore": ("*.pyc\n", ".bale/\n", ".bale/\n*.log\n"),
            "conf/tool.ini": ("[tool]\nmode = a\n", "[tool]\nmode = bale\n", "[tool]\nmode = bale\nlevel = 2\n"),
            # Only lines added by bale, later work right beside them: taken
            # out line by line, so never the session's.
            "conf/extra.txt": ("one\n", "one\nbale's\n", "one\nbale's\nlater\n"),
        })
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"changed in .gitignore, conf/tool.ini cannot be taken out", flat(proc.stderr))
        job = self.undo_job()
        self.assertEqual((job["commit"], sorted(job["files"])), (sha, [".gitignore", "conf/tool.ini"]))
        u = self.undo_dir()
        self.assertEqual((u / "workbench" / "conf" / "tool.ini").read_text(), "[tool]\nmode = bale\nlevel = 2\n")
        self.assertEqual((u / "before" / "conf" / "tool.ini").read_text(), "[tool]\nmode = a\n")
        # bale/ holds every file the commit changed; the others, the job's alone.
        self.assertEqual((u / "bale" / "conf" / "extra.txt").read_text(), "one\nbale's\n")
        self.assertFalse((u / "workbench" / "conf" / "extra.txt").exists())
        self.assertNotIn("extra.txt", (u / "bale.diff").read_text())

    def test_one_job_a_folder_at_a_time(self):
        # A merge job waiting: the undo job is not written beside it.
        self.refusing_commit()
        merge = self.root / self.folder / "merge"
        merge.mkdir()
        (merge / "merge.md").write_text(odl.merge_page_text({
            "project": "proj", "audience": "origin", "kind": "base", "branch": "main", "tip": "a" * 40,
            "workbench": "b" * 40, "parted": "c" * 40, "day": DAY, "files": ["src/a.py"], "session": None}))
        git(self.root, "add", "-A", env=self.e.env)
        git(self.root, "commit", "-qm", "a merge job", env=self.e.env)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"{self.folder}'s merge job (origin/main into the workbench) is waiting, and a folder holds one "
                      f"job at a time, so the undo job was not written: office start {self.name} --merge sends its "
                      "session", flat(proc.stderr))
        self.assertFalse(self.undo_dir().exists())
        # An undo job waiting: the merge job is not written beside it.
        git(self.root, "rm", "-rq", str(merge.relative_to(self.root)), env=self.e.env)
        git(self.root, "commit", "-qm", "no merge job", env=self.e.env)
        self.run_office("deliver", self.name, "--yes")
        self.assertTrue(self.undo_dir().exists())
        with self.e.this_process():
            lines = odl.merge_job_lines(self.root, self.folder, self.name, "proj", self.clone, "base", "origin",
                                        "main", "a" * 40, "b" * 40, ["src/a.py"], day=DAY)
        self.assertEqual(len(lines), 1)
        self.assertIn(f"undo job (bale's own commit {self.undo_job()['commit'][:7]}) is waiting", lines[0])
        self.assertIn(f"office start {self.name} --undo-bale sends its session", lines[0])
        self.assertFalse(merge.exists())

    def test_a_page_that_does_not_read_is_named_and_written_again(self):
        self.refusing_commit()
        self.run_office("deliver", self.name, "--yes")
        page = self.undo_dir() / "undo.md"
        page.write_text("# Undo\n\n- project: proj\n")
        with self.assertRaises(odl.DeliverError) as cm:
            self.undo_job()
        self.assertIn("does not read as an undo job (no commit, subject, workbench line)", cm.exception.lines[0])
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertIn("--undo-bale sends", flat(proc.stderr))
        self.assertEqual(self.undo_job()["files"], [".gitignore"])

    def test_a_folder_in_the_filing_cabinet_is_not_written_into(self):
        with self.e.this_process():
            lines = odl.undo_job_lines(self.root, f"filing-cabinet/{self.name}", self.name, "proj", self.clone,
                                       "a" * 40, HOUSEKEEPING, "b" * 40, [".gitignore"], day=DAY)
        self.assertEqual(len(lines), 1)
        self.assertIn(f"office reopen {self.name} brings it back to the desk", lines[0])


class TestTheUndoneRecord(unittest.TestCase):
    def test_the_history_line_reads_back(self):
        job = {"commit": "0b0a41ec8965" + "0" * 28, "subject": "bale: tidy (the config)",
               "files": [".gitignore", "conf/a b.ini"]}
        text = odl.undone_text(job, SID_U)
        self.assertEqual(text, f"bale's own commit 0b0a41e (bale: tidy (the config)) taken out of .gitignore, "
                               f"conf/a b.ini by {SID_U}")
        got = odl.undone_records([(DAY, "undone", text), (DAY, "merged", "x"), (DAY, "undone", "not one")])
        self.assertEqual(got, {"0b0a41e": [{"paths": [".gitignore", "conf/a b.ini"], "sid": SID_U, "day": DAY}]})
        self.assertIn("undone", oh.HISTORY_VERBS)
        self.assertNotIn("undone", oh.STATE_VERBS)

    def test_the_page_reads_back(self):
        job = {"project": "proj", "commit": "a" * 40, "subject": HOUSEKEEPING, "workbench": "b" * 40,
               "parent": "c" * 40, "day": DAY, "files": [".gitignore", "x y.txt"], "earlier": SID,
               "session": SID_U}
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "undo").mkdir()
            odl.undo_page_path(d).write_text(odl.undo_page_text(job))
            self.assertEqual(odl.read_undo_job(d), job)
            self.assertIn(f"The undo session {SID} landed for this commit before", odl.undo_page_path(d).read_text())
            self.assertEqual(odl.folder_job(d), job)
            # A merge page that does not read beside it blocks nothing: the
            # undo job is the folder's, and the merge page's words name it.
            (pathlib.Path(d) / "merge").mkdir()
            odl.merge_page_path(d).write_text("# Merge\n")
            self.assertEqual(odl.folder_job(d), job)
            self.assertEqual(odl.waiting_merge_lines(d, "desk/x", "x"), [])
            odl.undo_page_path(d).unlink()
            with self.assertRaises(odl.DeliverError):
                odl.folder_job(d)
        self.assertEqual(odl.job_writes(["x/y.py", "top.py"], "/nonexistent"), [])
        self.assertEqual(odl.job_writes(["x/y.py", "x/z.py"], "/nonexistent"), ["x"])


# --- 2. the session -----------------------------------------------------------------------------------

class TestTheUndoSessionGoesOut(UndoCase):
    """office start N --undo-bale packs the undo session: the job's project,
    goal, forecast and brief (the install's templates/undo-brief.md), the
    materials riding in the folder, the session named on the job."""

    def setUp(self):
        super().setUp()
        self.sha = self.refusing_commit()
        self.run_office("deliver", self.name, "--yes")
        (self.e.desktop / "bale").unlink()
        self.fake = FakePackBale(self.e.tmp)
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])

    def test_it_packs_the_job_and_names_the_session_on_it(self):
        proc = self.run_office("start", self.name, "--undo-bale", "--no-refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertTrue(sid.endswith("-undo-001"), sid)
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(cwd, os.path.realpath(self.clone))
        self.assertEqual(argv[1], f"Take bale's own commit {self.sha[:7]} ({HOUSEKEEPING}) out of the workbench of "
                                  f"folder {number_of(self.folder_md())}, in .gitignore")
        pairs = [argv[i:i + 2] for i in range(len(argv))]
        self.assertIn(["--write", ".gitignore"], pairs)
        self.assertIn(["--constraint", "Office context informs this session but never lands in this project."], pairs)
        self.assertIn("--readme-file", argv)
        self.assertEqual(self.undo_job()["session"], sid)
        self.office_clean()
        self.assertEqual(git(self.root, "log", "-1", "--format=%s", env=self.e.env).strip(),
                         f"office start: {sid} sent for the undo in {self.name}")
        tray = pathlib.Path(next(l for l in proc.stdout.splitlines() if l.startswith("Out tray: "))[len("Out tray: "):])
        with tarfile.open(tray / "context-home.tar.gz") as t:
            names = t.getnames()
        for rel in ("undo/undo.md", "undo/bale.diff", "undo/before/.gitignore", "undo/bale/.gitignore",
                    "undo/workbench/.gitignore"):
            self.assertIn(f"home/{self.folder}/{rel}", names)

    def test_the_brief_says_what_the_session_is(self):
        with self.e.this_process():
            out = self.e.tmp / "brief.md"
            got = odl.undo_start(self.root, self.name, out)
        text = flat(out.read_text())
        self.assertEqual((got["project"], got["writes"], got["said"]), ("proj", [".gitignore"], []))
        for words in ("This is an undo session on proj, and nothing else.",
                      f"bale's own commit {self.sha[:12]} ({HOUSEKEEPING})", "- .gitignore",
                      f"{self.folder}/undo/ holds everything", "- before/: each file above as it was before",
                      "- bale.diff: the commit's own change", "No undo session has landed for this commit yet.",
                      "write the file as the workbench's work needs it with bale's change taken out",
                      "The response ships each file whose result differs from the workbench's, and nothing else",
                      "An undo session writes no Walkthrough, Delivery or Structure section",
                      "Write instead a `## Undo` section: for each file, one line on what was bale's and what stayed",
                      "the occupant is never sent into the clone to undo it"):
            self.assertIn(words, text)
        self.assertNotIn("{{", text)
        self.assertNotIn("by hand", text)

    def test_what_it_refuses(self):
        proc = self.run_office("start", self.name, "--undo-bale", "--goal", "something else")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--undo-bale sends the undo session office deliver wrote for a folder, its goal, forecast, brief "
                      "and project the folder's undo job's, so it takes the folder alone: office start FOLDER "
                      "--undo-bale", proc.stderr)
        proc = self.run_office("start", self.name, "--undo-bale", "--merge")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--merge and --undo-bale send two different sessions", proc.stderr)
        other = self.run_office("open", "other job", "--lane", "proj: docs", check=0).stdout.strip()
        proc = self.run_office("start", other.split("/")[1], "--undo-bale", "--no-refresh")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("holds no undo job waiting for a session", proc.stderr)
        self.assertIn(f"office deliver {other.split('/')[1]} writes one", flat(proc.stderr))
        self.assertEqual(self.fake.packs(), [])


# --- 3. the landing, the whole loop, and the offers -------------------------------------------------------

class TestTheWholeLoopThroughTheOffice(UndoCase):
    """Every step through the office's own command, as the occupant types
    it: deliver refuses and writes the job, office start N --undo-bale sends
    the session, deliver while it is out names the landing, office land
    closes the job, and deliver carries the folder's work with bale's change
    out of it. The fake bale packs, lands and answers status as one
    (tests/test_land.py FakeLandBale)."""

    def setUp(self):
        super().setUp()
        (self.e.desktop / "bale").unlink()
        self.fake = FakeLandBale(self.e.tmp)
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir()
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.e.env["FAKE_BALE_SEARCH"] = str(self.downloads)

    def test_deliver_refuses_start_sends_land_closes_deliver_carries(self):
        sha = self.refusing_commit()
        # 1. deliver refuses, the job written.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"office start {self.name} --undo-bale sends the session", flat(proc.stderr))
        self.assertNotIn("refs/heads/health-route", self.audience_refs())
        # 2. office start N --undo-bale sends it, and the job names it.
        proc = self.run_office("start", self.name, "--undo-bale", "--no-refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertEqual(self.undo_job()["session"], sid)
        # Asked again while it is out, deliver names the landing.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"the undo session {sid} was sent for {self.folder}'s undo job", flat(proc.stderr))
        self.assertIn(f"office land {sid} brings it back and closes the job", flat(proc.stderr))
        # 3. The response, landed through office land: the job closed.
        response_tarball(self.downloads, sid, {".gitignore": "*.pyc\n*.log\n"})
        proc = self.run_office("land", sid, "--response", str(self.downloads / f"response-{sid}.tar.gz"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"closed {self.folder}'s undo job: the undo session {sid} took bale's own commit {sha[:7]} out "
                      "of .gitignore on the workbench", proc.stderr)
        self.assertIn("the folder's pages: left as they are (an undo session writes neither", proc.stderr)
        self.assertRegex(proc.stdout, rf"Next: office deliver \S+  \(the undo session landed; deliver takes bale's "
                                      r"own change out with it and carries the folder's own work\)")
        self.assertFalse(self.undo_dir().exists())
        self.assertIn(f" undone: bale's own commit {sha[:7]} ({HOUSEKEEPING}) taken out of .gitignore by {sid}\n",
                      self.folder_md())
        self.office_clean()
        # The session's landed commit is the undo; land made none of its own.
        self.assertEqual(self.clone_ref("HEAD"), self.clone_ref(f"applied/{sid}"))
        # 4. deliver: the folder's work, bale's change out of it.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"{sha[:12]} {HOUSEKEEPING} (.gitignore): nothing left to undo: the undo session {sid} took it "
                      "out of .gitignore on the workbench", proc.stdout)
        self.assertEqual(git(self.audience, "show", "health-route:.gitignore", env=self.e.env), "*.pyc\n*.log\n")
        self.assertNotIn(".bale", git(self.audience, "log", "-p", "health-route", env=self.e.env))
        self.assertIn(f"covering {sid}, {SID};", proc.stdout)

    def test_the_take_out_writes_the_job_again_naming_the_landed_session(self):
        # The session took bale's commit out of .gitignore; later work since
        # touches bale's lines in a second file, so the next delivery writes
        # the job again for that file alone, naming the landed session.
        sha = self.refusing_commit({".gitignore": ("*.pyc\n", ".bale/\n", ".bale/\n*.log\n"),
                                    "conf/tool.ini": ("mode = a\n", "mode = bale\n", "mode = bale\n")})
        self.run_office("deliver", self.name, "--yes")
        self.assertEqual(self.undo_job()["files"], [".gitignore"])
        proc = self.run_office("start", self.name, "--undo-bale", "--no-refresh")
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        response_tarball(self.downloads, sid, {".gitignore": "*.pyc\n*.log\n"})
        self.run_office("land", sid, "--response", str(self.downloads / f"response-{sid}.tar.gz"), check=0)
        self.by_hand("conf/tool.ini", "mode = bale\nlevel = 2\n", "Level two")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        err = flat(proc.stderr)
        self.assertIn(f"the undo session {sid} landed for this commit on", err)
        self.assertIn("took it out of .gitignore; the workbench's later work touches bale's lines in conf/tool.ini "
                      "too, so the job is written again for it", err)
        job = self.undo_job()
        self.assertEqual((job["commit"], job["files"], job["earlier"], job["session"]),
                         (sha, ["conf/tool.ini"], sid, None))


class TestTheUndoOnAHost(UndoCase):
    hosted = True

    def test_the_materials_come_from_the_mirror_and_the_loop_closes_there(self):
        sha = self.refusing_commit()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"office start {self.name} --undo-bale", flat(proc.stderr))
        self.assertEqual((self.undo_dir() / "before" / ".gitignore").read_text(), "*.pyc\n")
        self.assertEqual((self.undo_dir() / "workbench" / ".gitignore").read_text(), ".bale/\n*.log\n")
        self.assertEqual(self.undo_job()["commit"], sha)
        self.assertEqual(self.ssh.left_on(HOST), [])
        self.assertEqual([d for d in self.e.tmpdir.glob("office-deliver*")], [])
        # The session, recorded and named as start names it, landed there.
        self.run_office("sessions", self.name, SID_U, check=0)
        with self.e.this_process():
            odl.undo_sent(self.root, self.folder, SID_U)
        self.land_session(SID_U, {".gitignore": "*.pyc\n*.log\n"}, "Take bale's change out")
        self.ssh.reset()
        with self.e.this_process():
            was, lines = odl.land_undo(self.root, "proj", SID_U, self.folder, DAY)
        self.assertTrue(was, lines)
        self.assertFalse(self.undo_dir().exists())
        self.assertIn(f"{DAY} undone: bale's own commit {sha[:7]}", self.folder_md())
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"nothing left to undo: the undo session {SID_U} took it out of .gitignore", proc.stdout)
        self.assertEqual(git(self.audience, "show", "health-route:.gitignore", env=self.e.env), "*.pyc\n*.log\n")
        self.assertEqual(self.ssh.left_on(HOST), [])


class TestLandClosesOnlyItsOwn(UndoCase):
    def test_not_under_a_session_open_in_the_clone_and_not_for_another(self):
        self.refusing_commit()
        self.run_office("deliver", self.name, "--yes")
        self.run_office("sessions", self.name, SID_U, check=0)
        with self.e.this_process():
            odl.undo_sent(self.root, self.folder, SID_U)
        # Another session's landing: not this job's.
        with self.e.this_process():
            self.assertEqual(odl.land_undo(self.root, "proj", SID, self.folder, DAY), (False, []))
        # Landed, but another session is open in the clone: not closed, and
        # deliver names the line that closes it.
        self.land_session(SID_U, {".gitignore": "*.pyc\n*.log\n"}, "Take bale's change out")
        self.fake_bale(open_sessions=["2026-10-29-other-001"])
        with self.e.this_process():
            was, lines = odl.land_undo(self.root, "proj", SID_U, self.folder, DAY)
        self.assertTrue(was)
        self.assertIn("a job is never closed under them; office deliver", flat(" ".join(lines)))
        self.assertTrue(self.undo_dir().exists())
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("a job is never closed under them", flat(proc.stderr))
        # Once nothing is open, deliver closes it before it plans, and delivers.
        self.fake_bale()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"closed {self.folder}'s undo job", proc.stdout + proc.stderr)
        self.assertFalse(self.undo_dir().exists())
        self.assertEqual(git(self.root, "log", "-3", "--format=%s", env=self.e.env).count(
            f"office deliver: bale's own commit"), 1)

    def test_a_session_that_never_landed_closes_nothing(self):
        self.refusing_commit()
        self.run_office("deliver", self.name, "--yes")
        with self.e.this_process():
            odl.undo_sent(self.root, self.folder, SID_U)
            self.assertEqual(odl.land_undo(self.root, "proj", SID_U, self.folder, DAY), (True, []))
        self.assertTrue(self.undo_dir().exists())


class TestTheWaitingUndoSession(UndoCase):
    def test_offered_on_the_status_the_next_line_the_desk_the_map_and_the_home_screen(self):
        open_status(self)
        n = number_of(self.folder_md())
        sha = self.refusing_commit()
        self.run_office("deliver", self.name, "--yes")
        day = self.undo_job()["day"]
        status = self.run_office("status", check=None).stdout
        self.assertIn(f"folder {n}: undo job waiting, bale's own commit {sha[:7]} out of the workbench, 1 file(s); "
                      f"office start {n} --undo-bale sends the session", status)
        walk = self.run_office(check=0).stdout
        self.assertIn(f"Next: office start {n} --undo-bale  (folder {n}'s undo job waits; start --undo-bale sends the "
                      "session that takes bale's own change out of the workbench)", walk)
        self.assertIn(f"[undo job waiting: bale's own commit {sha[:7]} conflicts with the workbench in 1 file(s); "
                      f"office start {n} --undo-bale]", walk)
        shown = self.run_office("map", str(n), check=0).stdout
        self.assertIn(f"office start {n} --undo-bale", shown)
        self.assertIn("sends the undo session office deliver wrote", shown)
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir(exist_ok=True)
        page, menu = home(self)
        self.assertIn(f"Send the undo session for folder {n}, health route: bale's own commit {sha[:7]} conflicts "
                      f"with the workbench in 1 file(s) (office deliver wrote the job on {day})  (next)", page)
        self.assertEqual(menu[0], ["1", "office", "start", n, "--undo-bale"])
        # Sent: said nowhere new.
        with self.e.this_process():
            odl.undo_sent(self.root, self.folder, SID_U)
        self.assertNotIn("undo job", self.run_office("status", check=None).stdout)
        self.assertNotIn("--undo-bale", self.run_office(check=0).stdout)
        # Landed and not closed: status says deliver closes it.
        self.run_office("sessions", self.name, SID_U, check=0)
        self.land_session(SID_U, {".gitignore": "*.pyc\n*.log\n"}, "Take bale's change out")
        self.assertIn(f"folder {n}: undo session {SID_U} landed; office deliver {n} closes the undo job",
                      self.run_office("status", check=None).stdout)

    def test_the_words_as_units(self):
        m = {"folder": {"name": "c", "number": 5, "rel": "desk/c", "title": "Undo me"}, "landed": None,
             "job": {"commit": "0b0a41ec" + "0" * 32, "subject": HOUSEKEEPING, "files": ["a", "b"],
                     "day": "2026-11-02"}}
        self.assertEqual(ob.job_flag(m["job"]), "--undo-bale")
        self.assertEqual(ob.merge_item_words(m), "Send the undo session for folder 5, Undo me: bale's own commit "
                                                 "0b0a41e conflicts with the workbench in 2 file(s) (office deliver "
                                                 "wrote the job on 2026-11-02)")
        self.assertEqual(ob.open_words(m["folder"], {"merge_by_rel": {"desk/c": m}}),
                         "undo job waiting: bale's own commit 0b0a41e conflicts with the workbench in 2 file(s); "
                         "office start 5 --undo-bale")


# --- 4. 0.47.0's two: the cap, and the empty landing ---------------------------------------------------

class TestTheAudiencesSideIsCapped(MergeCase):
    """The audience changes src/a.py (conflicting) and three files beside
    it; the copy is capped, the conflicting file always copied whole and
    never counted."""

    def setUp(self):
        super().setUp()
        self.tip = self.coworker({"src/a.py": "x = 5\n", "README.md": "hello, readers\n", "docs/one.md": "1\n",
                                  "docs/two.md": "2\n"}, "Change a and three beside it")
        git(self.clone, "fetch", "-q", "origin", env=self.e.env)
        self.workbench = self.clone_ref("HEAD")

    def carry(self, cap):
        dest = self.e.tmp / f"materials-{cap}"
        with self.e.this_process():
            got = odl.carry_materials(self.clone, ("-", self.workbench, self.tip, "-"), ["src/a.py"], dest, cap=cap)
        return dest, got

    def test_the_cap_copies_so_many_and_lists_every_path(self):
        dest, (_, _, changed, uncopied) = self.carry(1)
        self.assertEqual(sorted(p for p, _ in changed), ["README.md", "docs/one.md", "docs/two.md", "src/a.py"])
        self.assertEqual((dest / "audience" / "src" / "a.py").read_text(), "x = 5\n")
        copied = [p for p in ("README.md", "docs/one.md", "docs/two.md") if (dest / "audience" / p).is_file()]
        self.assertEqual(len(copied), 1, copied)
        self.assertEqual(sorted(uncopied + copied), ["README.md", "docs/one.md", "docs/two.md"])
        self.assertFalse((dest / ".n").exists())
        # Cap 0: the conflicting file alone.
        dest, (_, _, _, uncopied) = self.carry(0)
        self.assertEqual(sorted(uncopied), ["README.md", "docs/one.md", "docs/two.md"])
        self.assertEqual(sorted(str(p.relative_to(dest / "audience")) for p in (dest / "audience").rglob("*")
                                if p.is_file()), ["src/a.py"])
        # The default cap copies them all.
        dest, (_, _, _, uncopied) = self.carry(odl.MATERIALS_CAP)
        self.assertEqual(uncopied, [])

    def test_the_page_and_the_brief_say_how_many_were_left_and_how_to_read_them(self):
        job = {"project": "proj", "audience": "origin", "kind": "base", "branch": "main", "tip": self.tip,
               "workbench": self.workbench, "parted": "c" * 40, "day": DAY, "files": ["src/a.py"], "session": None,
               "changed": [("README.md", "changed"), ("docs/one.md", "added"), ("docs/two.md", "added")],
               "uncopied": ["docs/one.md", "docs/two.md"]}
        merge = self.root / self.folder / "merge"
        merge.mkdir()
        odl.merge_page_path(self.root / self.folder).write_text(odl.merge_page_text(job))
        text = (merge / "merge.md").read_text()
        self.assertIn("- changed: README.md\n- changed: docs/one.md (added, not copied)\n"
                      "- changed: docs/two.md (added, not copied)\n", text)
        self.assertIn(f"2 of them are past the cap of {odl.MATERIALS_CAP} copies and marked not copied: audience/ "
                      f"does not hold them, and `git show {self.tip[:12]}:PATH` in the clone reads each one.", flat(text))
        back = odl.read_merge_job(self.root / self.folder)
        self.assertEqual((back["changed"], back["uncopied"]), (job["changed"], job["uncopied"]))
        with self.e.this_process():
            out = self.e.tmp / "brief.md"
            odl.merge_start(self.root, self.name, out)
        brief = flat(out.read_text())
        self.assertIn("- docs/one.md (added, not copied)", brief)
        self.assertIn("the conflicting files always, the others up to a cap. 2 of them are past the cap", brief)
        self.assertIn(f"`git show {self.tip[:12]}:PATH` in the clone reads each one.", brief)
        self.assertNotIn("{{", brief)
        # A path whose own name ends as the mark would is still read back.
        self.assertEqual(odl.changed_line("x (added, not copied)", "changed"),
                         "- changed: x (added, not copied) (changed)")

    def test_a_page_from_before_reads_nothing_uncopied_and_the_brief_says_every_copy_is_there(self):
        self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(self.job()["uncopied"], [])
        self.assertNotIn("not copied", (self.root / self.folder / "merge" / "merge.md").read_text())
        with self.e.this_process():
            out = self.e.tmp / "brief.md"
            odl.merge_start(self.root, self.name, out)
        self.assertIn("None of the files above is past it: each one is copied.", flat(out.read_text()))


class TestAnEmptyLanding(MergeCase):
    """A merge session whose every resolution is the workbench's ships no
    change; bale 0.4.56 lands it and tags it (the probe empty-landing), the
    fake bale does as much, and office land makes the merge commit."""

    def setUp(self):
        super().setUp()
        (self.e.desktop / "bale").unlink()
        self.fake = FakeLandBale(self.e.tmp)
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir()
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.e.env["FAKE_BALE_SEARCH"] = str(self.downloads)

    def test_the_workbenchs_every_version_ends_in_the_merge_commit(self):
        tip = self.conflict_on_the_audience()
        workbench = self.clone_ref("HEAD")
        self.run_office("deliver", self.name, "--yes", "--refresh")
        proc = self.run_office("start", self.name, "--merge", "--no-refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        response_tarball(self.downloads, sid, None)
        proc = self.run_office("land", sid, "--response", str(self.downloads / f"response-{sid}.tar.gz"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # Landed and tagged with no change, as bale lands an empty changes[].
        self.assertEqual(git(self.clone, "diff", "--name-only", f"applied/{sid}^", f"applied/{sid}", env=self.e.env),
                         "")
        self.assertEqual(git(self.clone, "rev-parse", f"applied/{sid}^", env=self.e.env).strip(), workbench)
        # The merge commit: the workbench's version of the conflicting file.
        self.assertIn(f"made the merge session {sid}'s resolution a merge commit", proc.stderr)
        self.assertEqual(self.clone_ref("HEAD^1"), self.clone_ref(f"applied/{sid}"))
        self.assertEqual(self.clone_ref("HEAD^2"), tip)
        self.assertEqual((self.clone / "src" / "a.py").read_text(), "x = 2\ny = 3\n")
        self.assertEqual((self.clone / "README.md").read_text(), "hello, readers\n")
        self.assertFalse(self.merge_dir().exists())
        self.office_clean()

    def test_the_brief_says_an_empty_response_lands(self):
        self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        with self.e.this_process():
            out = self.e.tmp / "brief.md"
            odl.merge_start(self.root, self.name, out)
        self.assertIn("When it is the resolution of every file, the response ships no file at all (`changes: []`): "
                      "bale lands it and tags it applied all the same, and `office land` makes the merge commit from "
                      "the workbench's versions.", flat(out.read_text()))


# --- the record -----------------------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_release_the_readme_the_doctrine_and_the_usage_say_it(self):
        version = tuple(int(x) for x in (REPO / "VERSION").read_text().strip().split("."))
        self.assertGreaterEqual(version, (0, 51, 0))
        entry = (REPO / "RELEASES.md").read_text().split("## 0.51.0", 1)[1].split("\n## ", 1)[0]
        for words in ("--undo-bale", "templates/undo-brief.md", "Additive", "test_undo_bale.py", "undone",
                      "MATERIALS_CAP", "changes: []"):
            self.assertIn(words, entry)
        readme = flat((REPO / "README.md").read_text())
        doctrine = flat((REPO / "doctrine" / "OFFICE.md").read_text())
        usage = (REPO / "bin" / "office").read_text()
        for text in (readme, doctrine, usage):
            self.assertIn("--undo-bale", text)
            self.assertNotIn("by hand on the workbench branch", text)
        self.assertIn("| undo | project session (0.51.0)", doctrine)
        self.assertIn("office start 14 --undo-bale", usage)
        verbs = (REPO / "share" / "verbs.toml").read_text()
        self.assertIn("templates/undo-brief.md, as the brief", verbs)
        self.assertTrue((REPO / "templates" / "undo-brief.md").is_file())
        self.assertNotIn("by hand", flat((REPO / "lib" / "office_deliver.py").read_text()).split(
            "def take_out_own", 1)[1].split("def unmerged", 1)[0])


if __name__ == "__main__":
    unittest.main()
