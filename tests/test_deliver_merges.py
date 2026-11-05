"""Tests for office-src 0.40.0: no delivery ends at a terminal (the gaps of
2026-10-28, A5's last clause, and the proposals of deliver-adds and
wave-one-release). One class per item:

1. When bringing the audience into the workbench conflicts, deliver writes
   the merge's materials into the folder and names `office start N
   --merge`; that session goes out with its brief, and when it lands the
   office makes its resolution a merge commit (office land, or the next
   deliver when land could not), aborting and checking anything else.
2. A review the audience merged as a squash is seen by content
   (base_holds), and a base that holds a later version of the same lines
   is not.
3. A continued delivery is squashed from its range, so a second delivery
   that edits a line the first delivered goes; a branch that moved on the
   audience sends a merge session for its tip, and once that lands the
   next delivery carries what is new alone.
4. A session the base already holds leaves the others list and the
   delivered line, with one line saying so.
5. office letterhead check --added works with --on PROJECT, here and on a
   host.
6. deliver's closing letterhead line says what the check reads.

The world is test_host_refresh's (a bare repo for the audience, a
workbench clone with one session landed the way bale lands one, a fake
bale answering `bale status --json`); the fake ssh stands for a host, and
the packing fake bale of tests/test_start.py packs the merge session. Run
with the rest of the suite:

    tests/run.sh test_deliver_merges
"""

import os
import pathlib
import re
import sys
import tarfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import h  # noqa: E402
from test_audience_line import DOCS_WORDS, SID, SID2, git  # noqa: E402
from test_host_refresh import RefreshCase  # noqa: E402
from test_project_on_host import HOST  # noqa: E402
from test_start import FakePackBale  # noqa: E402
from test_land import FakeLandBale, LandCase, response_tarball  # noqa: E402
from test_audience_line import NOTES  # noqa: E402

import office_deliver as odl  # noqa: E402

SID_M = "2026-10-29-health-route-merge-001"
SID_N = "2026-10-29-health-again-001"
DAY = "2026-10-29"


class MergeCase(RefreshCase):
    """RefreshCase's world, with what these tests share: the audience
    changing src/a.py (the line the landed session changed) and README.md
    (a file the workbench never touched), the folder's merge page read
    back, and a merge session landed the way bale lands one."""

    def conflict_on_the_audience(self):
        return self.coworker({"src/a.py": "x = 5\n", "README.md": "hello, readers\n"}, "Change a on the audience")

    def merge_dir(self):
        return self.root / self.folder / "merge"

    def job(self):
        return odl.read_merge_job(self.root / self.folder)

    def land_the_merge_session(self, resolution, sid=SID_M):
        """The merge session recorded in the folder, named on the job as
        office start --merge names it, and landed in the clone."""
        self.run_office("sessions", self.name, sid, check=0)
        with self.e.this_process():
            odl.merge_sent(self.root, self.folder, sid)
        return self.land_session(sid, resolution, "Resolve the merge")

    def land_merge(self, sid=SID_M):
        with self.e.this_process():
            return odl.land_merge(self.root, "proj", sid, self.folder, DAY)

    def office_clean(self):
        self.assertEqual(git(self.root, "status", "--porcelain", env=self.e.env), "")

    def clone_clean(self):
        self.assertEqual(self.clone_ref("MERGE_HEAD"), "")
        self.assertEqual(git(self.clone, "status", "--porcelain", "-uno", env=self.e.env), "")


# --- 1. the merge session ----------------------------------------------------------------------------

class TestTheMergeSession(MergeCase):
    def test_a_conflict_writes_the_materials_and_names_the_merge_session(self):
        tip = self.conflict_on_the_audience()
        before = self.clone_ref("HEAD")
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        err = " ".join(proc.stderr.split())
        self.assertIn("bringing origin/main into the workbench (main) conflicts in src/a.py; the merge was aborted there, "
                      "and nothing is left half-done in the clone", err)
        self.assertIn(f"the merge's materials are in {self.folder}/merge/", err)
        self.assertIn(f"office start {self.name} --merge sends the merge session that resolves them", err)
        # Never the terminal: no line sends the occupant into the clone.
        self.assertNotIn("by hand", err)
        self.assertNotIn("git merge origin/main on", err)
        # The clone as it was; nothing on the audience.
        self.assertEqual(self.clone_ref("HEAD"), before)
        self.clone_clean()
        self.assertNotIn("refs/heads/health-route", self.audience_refs())
        # The three versions at the file's path, and the audience's log.
        m = self.merge_dir()
        self.assertEqual((m / "parted" / "src" / "a.py").read_text(), "x = 1\n")
        self.assertEqual((m / "workbench" / "src" / "a.py").read_text(), "x = 2\ny = 3\n")
        self.assertEqual((m / "audience" / "src" / "a.py").read_text(), "x = 5\n")
        self.assertFalse((m / "parted" / "README.md").exists())  # only what conflicts
        self.assertIn("Change a on the audience", (m / "log.txt").read_text())
        job = self.job()
        self.assertEqual((job["kind"], job["branch"], job["tip"], job["workbench"], job["files"], job["session"]),
                         ("base", "main", tip, before, ["src/a.py"], None))
        self.assertEqual(job["parted"], git(self.clone, "merge-base", before, tip, env=self.e.env).strip())
        # Committed in the office, on its own.
        self.office_clean()
        self.assertEqual(git(self.root, "log", "-1", "--format=%s", env=self.e.env).strip(),
                         f"office deliver: the merge's materials for {self.name}")
        # Asked again with nothing sent: the same line, and nothing new to commit.
        commits = git(self.root, "rev-list", "--count", "HEAD", env=self.e.env)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertIn(f"office start {self.name} --merge sends", " ".join(proc.stderr.split()))
        self.assertEqual(git(self.root, "rev-list", "--count", "HEAD", env=self.e.env), commits)

    def test_with_the_session_out_the_line_lands_it(self):
        self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        with self.e.this_process():
            odl.merge_sent(self.root, self.folder, SID_M)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"the merge session {SID_M} was sent for this conflict", proc.stderr)
        self.assertIn(f"office land {SID_M} brings it back", " ".join(proc.stderr.split()))
        self.assertEqual(self.job()["session"], SID_M)

    def test_land_makes_the_resolution_a_merge_commit_and_deliver_carries_the_folders_work(self):
        tip = self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        landed = self.land_the_merge_session({"src/a.py": "x = 5\ny = 3\n"})
        was, lines = self.land_merge()
        self.assertTrue(was, lines)
        self.assertTrue(any(l.startswith(f"made the merge session {SID_M}'s resolution a merge commit") for l in lines),
                        lines)
        # The merge commit: the landed tip and the audience's, the session's
        # file and git's own merge of what did not conflict, as the author.
        self.assertEqual(self.clone_ref("HEAD^1"), landed)
        self.assertEqual(self.clone_ref("HEAD^2"), tip)
        self.assertEqual((self.clone / "src" / "a.py").read_text(), "x = 5\ny = 3\n")
        self.assertEqual((self.clone / "README.md").read_text(), "hello, readers\n")
        self.assertEqual(git(self.clone, "log", "-1", "--format=%an <%ae>|%s", env=self.e.env).strip(),
                         f"Zed Zee <z@example.org>|Bring origin/main into the workbench, resolved by {SID_M} "
                         "(office land)")
        self.clone_clean()
        head = self.clone_ref("HEAD")
        self.assertIn(f"- {DAY} merged: origin/main {tip[:7]} into the workbench, {head[:7]}, resolved by {SID_M}\n",
                      self.folder_md())
        self.assertFalse(self.merge_dir().exists())
        self.office_clean()
        # The next delivery squashes from the audience's tip: the folder's
        # own work alone, with the resolution's line.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.audience_ref("health-route^"), tip)
        self.assertEqual(sorted(git(self.audience, "diff", "--name-only", "health-route^", "health-route",
                                    env=self.e.env).split()), ["src/a.py", "src/health.py"])
        self.assertEqual(git(self.audience, "show", "health-route:src/a.py", env=self.e.env), "x = 5\ny = 3\n")
        self.assertIn(f"covering {SID_M}, {SID};", proc.stdout)

    def test_deliver_makes_it_when_land_did_not(self):
        tip = self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        self.land_the_merge_session({"src/a.py": "x = 5\ny = 3\n"})
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"made the merge session {SID_M}'s resolution a merge commit", proc.stderr)
        self.assertEqual(self.clone_ref("HEAD^2"), tip)
        self.assertIn("(office deliver)", git(self.clone, "log", "-1", "--format=%s", env=self.e.env))
        self.assertEqual(self.audience_ref("health-route^"), tip)
        self.assertFalse(self.merge_dir().exists())

    def test_a_conflict_the_session_did_not_resolve_is_aborted_and_checked(self):
        self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        # The session landed something else, and the job names a file that
        # does not conflict: src/a.py is still unmerged, so nothing is made.
        landed = self.land_the_merge_session({"NOTES.md": "n\n"})
        page = self.merge_dir() / "merge.md"
        page.write_text(page.read_text().replace("- file: src/a.py", "- file: NOTES.md"))
        was, lines = self.land_merge()
        self.assertTrue(was)
        self.assertIn("it conflicts outside the files the session resolved, in src/a.py; the merge was aborted there, "
                      "and nothing is left half-done", " ".join(lines))
        self.assertIn(f"office deliver {self.name} makes it once that is put right", " ".join(lines))
        self.assertEqual(self.clone_ref("HEAD"), landed)
        self.clone_clean()
        self.assertTrue(page.is_file())

    def test_an_open_session_keeps_land_from_merging_and_the_line_names_deliver(self):
        self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        landed = self.land_the_merge_session({"src/a.py": "x = 5\ny = 3\n"})
        self.fake_bale(["2026-10-29-next-one-001"])
        was, lines = self.land_merge()
        self.assertTrue(was)
        self.assertIn("1 session(s) are open in the clone (2026-10-29-next-one-001), and a merge is never made under "
                      f"them; office deliver {self.name} makes it once they have landed", " ".join(lines))
        self.assertEqual(self.clone_ref("HEAD"), landed)

    def test_a_folder_in_the_filing_cabinet_gets_no_materials(self):
        with self.e.this_process():
            lines = odl.merge_job_lines(self.root, "filing-cabinet/" + self.name, self.name, "proj", self.clone, "base",
                                        "origin", "main", self.clone_ref("HEAD"), self.clone_ref("HEAD"), ["src/a.py"])
        self.assertIn(f"office reopen {self.name} brings it back to the desk", " ".join(lines))
        self.assertFalse((self.root / "filing-cabinet").joinpath(self.name, "merge").exists())

    def test_not_a_merge_session_is_left_alone(self):
        self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(self.land_merge(SID), (False, []))
        self.assertEqual(self.job()["session"], None)


class TestTheMergeSessionOnAHost(MergeCase):
    hosted = True

    def test_the_materials_come_through_the_shell_and_the_merge_is_made_there(self):
        tip = self.conflict_on_the_audience()
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"office start {self.name} --merge", proc.stderr)
        self.assertEqual((self.merge_dir() / "audience" / "src" / "a.py").read_text(), "x = 5\n")
        self.assertEqual((self.merge_dir() / "workbench" / "src" / "a.py").read_text(), "x = 2\ny = 3\n")
        self.assertEqual(self.ssh.left_on(HOST), [])
        self.land_the_merge_session({"src/a.py": "x = 5\ny = 3\n"})
        self.ssh.reset()
        was, lines = self.land_merge()
        self.assertTrue(was, lines)
        self.assertEqual(self.clone_ref("HEAD^2"), tip)
        self.clone_clean()
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.audience_ref("health-route^"), tip)
        self.assertEqual(self.ssh.left_on(HOST), [])


class TestTheMergeSessionGoesOut(MergeCase):
    """office start N --merge packs the merge session: the job's project,
    goal, forecast and brief (the install's templates/merge-brief.md), the
    materials riding in the folder, the session named on the job."""

    def setUp(self):
        super().setUp()
        self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        (self.e.desktop / "bale").unlink()
        self.fake = FakePackBale(self.e.tmp)
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])

    def test_it_packs_the_job_and_names_the_session_on_it(self):
        proc = self.run_office("start", self.name, "--merge", "--no-refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertTrue(sid.endswith("-merge-001"), sid)
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(cwd, os.path.realpath(self.clone))
        self.assertRegex(argv[1], r"^Resolve the conflicts of bringing origin/main [0-9a-f]{7} into the workbench of "
                                  r"folder \d+, in src/a\.py$")
        pairs = [argv[i:i + 2] for i in range(len(argv))]
        self.assertIn(["--write", "src/a.py"], pairs)
        self.assertIn(["--constraint", "Office context informs this session but never lands in this project."], pairs)
        brief = pathlib.Path(argv[argv.index("--readme-file") + 1]) if "--readme-file" in argv else None
        self.assertIsNotNone(brief)
        self.assertEqual(self.job()["session"], sid)
        self.office_clean()
        # The materials ride in the office's context, with the folder.
        tray = pathlib.Path(next(l for l in proc.stdout.splitlines() if l.startswith("Out tray: "))[len("Out tray: "):])
        with tarfile.open(tray / "context-home.tar.gz") as t:
            names = t.getnames()
        self.assertIn(f"home/{self.folder}/merge/audience/src/a.py", names)
        self.assertIn(f"home/{self.folder}/merge/merge.md", names)

    def test_the_brief_says_what_the_session_is(self):
        with self.e.this_process():
            out = self.e.tmp / "brief.md"
            got = odl.merge_start(self.root, self.name, out)
        text = " ".join(out.read_text().split())
        self.assertEqual(got["writes"], ["src/a.py"])
        # 0.47.0: parted/ and workbench/ hold the conflicting files, audience/
        # the audience's side whole, and the response ships each conflicting
        # file whose resolution differs from the workbench's
        # (tests/test_deliver_fixes.py pins the words).
        for words in ("This is a merge session on proj, and nothing else.", "- src/a.py",
                      f"{self.folder}/merge/ holds everything", "- parted/ and workbench/: each conflicting file",
                      "The response ships each conflicting file whose resolution differs from the workbench's, as it "
                      "should read after the merge, and nothing else",
                      "A merge session writes no Walkthrough, Delivery or Structure section",
                      "its parents are the landed session's commit and origin/main's tip"):
            self.assertIn(words, text)
        self.assertNotIn("{{", text)

    def test_what_it_refuses(self):
        proc = self.run_office("start", self.name, "--merge", "--goal", "something else")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--merge sends the merge session office deliver wrote for a folder", proc.stderr)
        other = self.run_office("open", "other job", "--lane", "proj: docs", check=0).stdout.strip()
        proc = self.run_office("start", other.split("/")[1], "--merge", "--no-refresh")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("holds no merge waiting for a session", proc.stderr)
        self.assertIn(f"office deliver {other.split('/')[1]} writes one", " ".join(proc.stderr.split()))


class TestOfficeLandMakesTheMerge(LandCase):
    """office land, after an applied landing of the session a folder's
    merge job names: the merge commit made before anything reads the
    workbench, the folder's two pages left as the work's, the job gone."""

    def test_land_runs_the_merge_step_and_leaves_the_pages(self):
        h.set_declarations(self.root / "floor-plan" / "manifest.toml", "alpha",
                           audience_keys={"author": "Zed Zee <z@example.org>"})
        self.e.git(self.root, "commit", "-qam", "the author")
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        # The side the merge brings in: a commit the workbench does not have.
        branch = self.e.git(self.proj, "symbolic-ref", "--short", "HEAD").strip()
        self.e.git(self.proj, "checkout", "-q", "-b", "the-audience")
        (self.proj / "README.md").write_text("alpha, read\n")
        self.e.git(self.proj, "commit", "-qam", "Change the readme")
        tip = self.e.git(self.proj, "rev-parse", "HEAD").strip()
        self.e.git(self.proj, "checkout", "-q", branch)
        (self.root / self.folder / "merge").mkdir()
        (self.root / self.folder / "merge" / "merge.md").write_text(odl.merge_page_text({
            "project": "alpha", "audience": "origin", "kind": "base", "branch": "main", "tip": tip,
            "workbench": self.e.git(self.proj, "rev-parse", "HEAD").strip(), "parted": "", "day": DAY,
            "files": ["src/a.py"], "session": sid}))
        self.e.git(self.root, "add", "-A")
        self.e.git(self.root, "commit", "-qm", "the job")
        response_tarball(self.downloads, sid, {"src/a.py": "resolved\n"}, notes=NOTES)
        proc = self.run_office("land", sid, "--leave-open", "--response", str(self.downloads / f"response-{sid}.tar.gz"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"made the merge session {sid}'s resolution a merge commit", proc.stderr)
        self.assertIn("the folder's pages: left as they are (a merge session writes neither", proc.stderr)
        self.assertFalse((self.root / self.folder / "walkthrough.md").exists())
        self.assertEqual(self.e.git(self.proj, "rev-parse", "HEAD^2").strip(), tip)
        self.assertEqual((self.proj / "src" / "a.py").read_text(), "resolved\n")
        self.assertEqual((self.proj / "README.md").read_text(), "alpha, read\n")
        self.assertFalse((self.root / self.folder / "merge").exists())
        self.assertIn(f"resolved by {sid}", self.folder_md())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # The after-land actions ran on the merged workbench.
        self.assertTrue(proc.stdout.rstrip().endswith("ran (exit 0): touch AFTER-LAND-RAN"), proc.stdout)


# --- 2. a review merged as a squash, seen by content ---------------------------------------------------

class HeldCase(MergeCase):
    def second_folder(self, words=DOCS_WORDS):
        other = self.run_office("open", "docs job", "--lane", "proj: docs", "--size", "small", check=0).stdout.strip()
        self.land_session(SID2, {"docs.md": "# health\n"}, "Document the route")
        self.run_office("sessions", other.split("/")[1], SID2, check=0)
        (self.root / other / "delivery.md").write_text(words)
        git(self.root, "add", "-A", env=self.e.env)
        git(self.root, "commit", "-qm", "the second folder's words", env=self.e.env)
        return other, other.split("/")[1]

    def squash_merge_the_review(self, delete=True):
        """The audience's review of health-route merged as a squash, and the
        branch deleted, as a git host does it."""
        cow = self.e.tmp / "squasher"
        git(self.e.tmp, "clone", "-q", str(self.audience), str(cow), env=self.e.env)
        git(cow, "merge", "-q", "--squash", "origin/health-route", env=self.e.env)
        git(cow, "commit", "-qm", "Health route for the API (#1)", env=self.e.env)
        git(cow, "push", "-q", "origin", "main", env=self.e.env)
        if delete:
            git(self.audience, "branch", "-q", "-D", "health-route", env=self.e.env)
        return git(cow, "rev-parse", "HEAD", env=self.e.env).strip()

    def number(self):
        return re.search(r"^- number: (\d+)$", self.folder_md(), re.M).group(1)


class TestASquashMergedReviewIsSeenByContent(HeldCase):
    def test_the_content_test_lets_the_next_delivery_through(self):
        self.run_office("deliver", self.name, "--yes", check=0)
        other, other_name = self.second_folder()
        self.squash_merge_the_review()
        proc = self.run_office("deliver", other_name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("deliver it twice", proc.stderr)
        self.assertIn(f"folder {self.number()}'s session {SID} is on origin/main already (by content:", proc.stderr)
        self.assertEqual(sorted(git(self.audience, "diff", "--name-only", "docs-job^", "docs-job",
                                    env=self.e.env).split()), ["docs.md"])

    def test_the_units_history_first_content_never_held_when_the_squash_would_change_the_base(self):
        self.run_office("deliver", self.name, "--yes", check=0)
        rec = h.delivered_records(self.root / self.folder / "folder.md")[0][1]
        with self.e.this_process():
            git(self.clone, "fetch", "-q", "origin", f"+refs/heads/main:{odl.REF_BASE}", env=self.e.env)
            self.assertEqual(odl.base_holds(self.clone, rec, "origin"), (None, None))
            self.squash_merge_the_review(delete=False)
            git(self.clone, "fetch", "-q", "origin", f"+refs/heads/main:{odl.REF_BASE}", env=self.e.env)
            self.assertEqual(odl.base_holds(self.clone, rec), (None, None))  # no remote: history alone
            self.assertEqual(odl.base_holds(self.clone, rec, "origin"), ("by content", None))
            # A later version of the same lines on the base: not held.
            self.coworker({"src/health.py": 'def health():\n    return "OK"\n'}, "Shout it")
            git(self.clone, "fetch", "-q", "origin", f"+refs/heads/main:{odl.REF_BASE}", env=self.e.env)
            self.assertEqual(odl.base_holds(self.clone, rec, "origin")[0], None)
            # A review merged as a merge commit: by history, the fast path.
            git(self.clone, "update-ref", odl.REF_BASE, rec["delivery"], env=self.e.env)
            self.assertEqual(odl.base_holds(self.clone, rec, "origin"), ("by history", None))
            git(self.clone, "update-ref", "-d", odl.REF_BASE, env=self.e.env)

    def test_a_later_version_on_the_base_refuses_and_says_which_test_failed(self):
        self.run_office("deliver", self.name, "--yes", check=0)
        other, other_name = self.second_folder()
        self.squash_merge_the_review()
        self.coworker({"src/health.py": 'def health():\n    return "OK"\n'}, "Shout it")
        # A session open in the clone keeps the base out of the workbench
        # (0.39.0), so the squash's range is read as it stands.
        self.fake_bale(["2026-10-29-next-one-001"])
        proc = self.run_office("deliver", other_name, "--yes", "--others-too")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        err = " ".join(proc.stderr.split())
        self.assertIn("would deliver it twice", err)
        self.assertRegex(err, rf"main as fetched does not hold folder {self.number()}'s delivery [0-9a-f]{{7}} by history "
                              r"or by content \(its change conflicts with the base's\)")
        self.assertIn("health-route is no longer on the audience", err)


# --- 3. a continued delivery is squashed from its range -------------------------------------------------

class TestAContinuedDeliveryIsSquashedFromItsRange(MergeCase):
    def test_a_second_delivery_that_edits_a_delivered_line_goes(self):
        self.run_office("deliver", self.name, "--yes", check=0)
        first = self.audience_ref("health-route")
        self.land_session(SID_N, {"src/health.py": 'def health():\n    return "fine"\n'}, "Say fine")
        self.run_office("sessions", self.name, SID_N, check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.audience_ref("health-route^"), first)
        self.assertEqual(git(self.audience, "diff", "--name-only", "health-route^", "health-route",
                             env=self.e.env).split(), ["src/health.py"])
        self.assertEqual(git(self.audience, "show", "health-route:src/health.py", env=self.e.env),
                         'def health():\n    return "fine"\n')
        self.assertIn(f"covering {SID_N};", proc.stdout)

    def test_a_branch_that_moved_sends_a_merge_session_for_its_tip(self):
        self.run_office("deliver", self.name, "--yes", check=0)
        reviewed = self.coworker({"src/health.py": '# reviewed\ndef health():\n    return "okay"\n'},
                                 "Answer the review", branch="health-route")
        self.land_session(SID_N, {"src/health.py": 'def health():\n    return "fine"\n'}, "Say fine")
        self.run_office("sessions", self.name, SID_N, check=0)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        err = " ".join(proc.stderr.split())
        self.assertIn("health-route moved on the audience since, and the squash conflicts in src/health.py", err)
        self.assertIn(f"office start {self.name} --merge sends the merge session", err)
        job = self.job()
        self.assertEqual((job["kind"], job["branch"], job["tip"], job["files"]),
                         ("branch", "health-route", reviewed, ["src/health.py"]))
        self.assertEqual((self.merge_dir() / "audience" / "src" / "health.py").read_text(),
                         '# reviewed\ndef health():\n    return "okay"\n')
        self.assertEqual((self.merge_dir() / "workbench" / "src" / "health.py").read_text(),
                         'def health():\n    return "fine"\n')
        self.assertIn("Answer the review", (self.merge_dir() / "log.txt").read_text())
        self.assertEqual(self.audience_ref("health-route"), reviewed)
        # The resolution lands; the branch's tip comes into the workbench,
        # and the next delivery carries what is new alone.
        self.land_the_merge_session({"src/health.py": '# reviewed\ndef health():\n    return "fine"\n'})
        was, lines = self.land_merge()
        self.assertTrue(was, lines)
        self.assertEqual(self.clone_ref("HEAD^2"), reviewed)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.audience_ref("health-route^"), reviewed)
        self.assertEqual(git(self.audience, "diff", "--numstat", "health-route^", "health-route", env=self.e.env),
                         "1\t1\tsrc/health.py\n")
        self.assertEqual(git(self.audience, "show", "health-route:src/health.py", env=self.e.env),
                         '# reviewed\ndef health():\n    return "fine"\n')
        self.assertIn("where the workbench and origin/health-route meet", proc.stdout)
        self.assertIn(f"covering {SID_M}, {SID_N};", proc.stdout)
        self.assertNotIn(f"covering {SID},", proc.stdout)


# --- 4. a session the base holds leaves the others list ------------------------------------------------

class TestAHeldSessionLeavesTheOthersList(HeldCase):
    def test_no_others_too_and_the_delivered_line_names_its_own(self):
        self.run_office("deliver", self.name, "--yes", check=0)
        other, other_name = self.second_folder()
        self.squash_merge_the_review()
        proc = self.run_office("deliver", other_name, "--yes")   # piped, and no --others-too
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("and of other folders", proc.stdout)
        self.assertIn("rides in nothing here", proc.stderr)
        page = (self.root / other / "folder.md").read_text()
        self.assertRegex(page, rf"delivered: docs-job on origin of proj: sessions {SID2}; workbench")
        self.assertIn(f"covering {SID2};", proc.stdout)


# --- 5. office letterhead check --added --on PROJECT -----------------------------------------------------

EM = "—"


class TestTheCheckTakesAddedOnAProject(MergeCase):
    def check_on(self):
        # A commit of the occupant's own (a range's messages are read too,
        # and bale's subjects are its marks).
        start = self.clone_ref("HEAD")
        (self.clone / "src" / "health.py").write_text(f'def health():\n    return "ok"  # fine {EM} really\n')
        git(self.clone, "commit", "-qam", "Say how fine", env=self.e.env)
        proc = self.run_office("letterhead", "check", "--on", "proj", "--added", "--range", f"{start}..HEAD")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout.splitlines(), [f'src/health.py:2: character: the em dash (U+2014) in: return "ok"  '
                                                    f'# fine {EM} really'])
        self.assertRegex(proc.stderr, r"letterhead: the lines [0-9a-f]{40}\.\.HEAD adds to the 1 file\(s\) it changed")
        proc = self.run_office("letterhead", "check", "--on", "proj", "--added", "--all")
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("--added reads the lines a diff adds, and --all the whole tree", proc.stderr)

    def test_here(self):
        self.check_on()


class TestTheCheckTakesAddedOnAHost(TestTheCheckTakesAddedOnAProject):
    hosted = True

    def test_here(self):  # the same, through the shell
        self.check_on()


# --- 6. deliver's closing letterhead line ----------------------------------------------------------------

class TestTheClosingLetterheadLine(MergeCase):
    def test_it_says_what_the_check_reads(self):
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("    letterhead on the lines it adds and the words: clean\n", proc.stdout)
        self.assertNotIn("letterhead on the diff", proc.stdout)


# --- 0.42.0: the merge session's whole loop, through the office's commands ----------------------------

class TestTheWholeLoopThroughTheOffice(MergeCase):
    """0.40.0's third proposal: every step through the office's own command,
    as the occupant types it, never a helper called in-process: deliver
    refuses on a conflicting base and writes the job, office start N --merge
    sends the session, the response lands through office land (which makes
    the merge commit), and deliver again carries the folder's own work. The
    fake bale here packs, lands and answers status as one (tests/test_land.py
    FakeLandBale), so the session office start sends is the one land finds."""

    def setUp(self):
        super().setUp()
        (self.e.desktop / "bale").unlink()
        self.fake = FakeLandBale(self.e.tmp)
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir()
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.e.env["FAKE_BALE_SEARCH"] = str(self.downloads)

    def test_deliver_refuses_start_sends_land_merges_deliver_carries(self):
        tip = self.conflict_on_the_audience()
        # 1. deliver refuses, the job written, the session named.
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"office start {self.name} --merge sends the merge session", " ".join(proc.stderr.split()))
        self.assertNotIn("refs/heads/health-route", self.audience_refs())
        # 2. office start N --merge sends it, and the job names it.
        proc = self.run_office("start", self.name, "--merge", "--no-refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertEqual(self.job()["session"], sid)
        # Asked again while it is out, deliver names the landing.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"office land {sid} brings it back", " ".join(proc.stderr.split()))
        # 3. The response, landed through office land: the merge commit made.
        response_tarball(self.downloads, sid, {"src/a.py": "x = 5\ny = 3\n"})
        proc = self.run_office("land", sid, "--response", str(self.downloads / f"response-{sid}.tar.gz"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"made the merge session {sid}'s resolution a merge commit", proc.stderr)
        self.assertEqual(self.clone_ref("HEAD^2"), tip)
        self.assertEqual(git(self.clone, "log", "-1", "--format=%s", env=self.e.env).strip(),
                         f"Bring origin/main into the workbench, resolved by {sid} (office land)")
        self.assertFalse(self.merge_dir().exists())
        self.assertIn(f"resolved by {sid}", self.folder_md())
        self.office_clean()
        # 4. deliver again: from the audience's tip, the folder's own work.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.audience_ref("health-route^"), tip)
        self.assertEqual(git(self.audience, "show", "health-route:src/a.py", env=self.e.env), "x = 5\ny = 3\n")
        self.assertEqual(sorted(git(self.audience, "diff", "--name-only", "health-route^", "health-route",
                                    env=self.e.env).split()), ["src/a.py", "src/health.py"])
        self.assertIn(f"covering {sid}, {SID};", proc.stdout)


if __name__ == "__main__":
    unittest.main()
