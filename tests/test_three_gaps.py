"""Tests for office-src 0.34.0: the three gaps the M10 walkthrough hit on
2026-10-27, read from folder 6 of the work office (its review's answer).

1. office deliver adopts a branch the audience already has that the
   folder never delivered to (made outside the office: a pull request
   opened by hand), with --adopt or a yes on a terminal, so a review's
   answer adds commits to the review's own branch.
2. A planner's bundle names the branch its session builds on, as one
   `--- BRANCH NAME ---` line in its brief, and office start checks that
   branch out in the project's clone, here or through its shell on a
   host, before bale open --check runs.
3. office probe runs a block that spans the office and a project's host:
   a block that calls `office-on PROJECT COMMAND` runs in the office root
   with that helper on its PATH, and each call runs its command where the
   project lives, through its shell on a host. Since 0.55.0 those tests
   live with the spanning probe's others, in tests/test_spanning_probe.py
   (spanning_block, TestASpanningProbe, TestASpanningProbeOnAHost); this
   module keeps the first two.

The suite makes no network call and runs no real ssh: a bare repo on this
machine is the audience, the fake ssh of tests/test_project_on_host.py
stands for the host, and the fake land bale answers bale's verbs. Run with
the rest of the suite:

    tests/run.sh test_three_gaps
"""

import os
import pathlib
import shlex
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import LandCase, bundle_file  # noqa: E402
from test_audience_line import AudienceCase, SID, SID2, WORDS, git  # noqa: E402
from test_out_trip_to_host import HostedStartCase  # noqa: E402
from test_project_on_host import HOST  # noqa: E402

import office_bale as ob  # noqa: E402
import office_deliver as odl  # noqa: E402
import office_helper as oh  # noqa: E402

LIB = REPO / "lib"


# --- 1. office deliver adopts a branch made outside the office ----------------------------------

class TestAnAdoptedBranch(AudienceCase):
    """The audience has a branch this folder never delivered to: a pull
    request a coworker or the occupant opened by hand. Before 0.34.0
    deliver refused it and named another branch; the review's answer,
    landed in the clone, could not reach the review."""

    def pull_request_branch(self, branch="picklists"):
        """A coworker's branch on the audience, from main, with one commit
        of its own: the pull request's branch, made outside the office."""
        cow = self.e.tmp / "cow"
        git(self.e.tmp, "clone", "-q", str(self.audience), str(cow), env=self.e.env)
        git(cow, "checkout", "-q", "-b", branch, env=self.e.env)
        (cow / "PR.md").write_text("the pull request\n")
        git(cow, "add", "-A", env=self.e.env)
        git(cow, "commit", "-qm", "Open the pull request", env=self.e.env)
        git(cow, "push", "-q", "origin", branch, env=self.e.env)
        return git(cow, "rev-parse", "HEAD", env=self.e.env).strip()

    def test_piped_it_is_refused_by_name_and_adopt_adds_the_delivery_to_it(self):
        tip = self.pull_request_branch()
        before = self.audience_refs()
        proc = self.run_office("deliver", self.name, "--yes", "--branch", "picklists")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("origin already has a branch named picklists, and desk/", proc.stderr)
        self.assertIn("made outside the office", proc.stderr)
        self.assertIn(f"office deliver {self.name} --branch picklists --adopt adds this delivery to it", proc.stderr)
        self.assertIn("piped input is never asked", proc.stderr)
        self.assertEqual(self.audience_refs(), before)
        self.assertNotIn("delivered:", self.folder_md())
        # --adopt: the delivery goes onto the branch as it is on the
        # audience, its own commit kept, this folder's work on top.
        proc = self.run_office("deliver", self.name, "--yes", "--branch", "picklists", "--adopt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("branch:   picklists (adding to the branch on the audience, which was made outside the office: "
                      "this folder records no delivery on it), from main", proc.stdout)
        self.assertIn("since where the workbench branch and origin/picklists parted", proc.stdout)
        self.assertIn("Delivered: picklists is on origin for proj, 1 commit(s) by Zed Zee <z@example.org> onto main "
                      "(added to the branch, adopted: it was made outside the office)", proc.stdout)
        self.assertEqual(self.audience_subjects("picklists"), ["Add the health route", "Open the pull request", "Initial commit"])
        self.assertEqual(git(self.audience, "rev-parse", "picklists^", env=self.e.env).strip(), tip)
        self.assertEqual(self.audience_tree("picklists"), ["PR.md", "README.md", "src/a.py", "src/health.py"])
        self.assertEqual(sorted(set(self.audience_refs()) - set(before)), [])
        # The folder records the adoption; the next line names the review
        # already open for the branch, not a new review's form.
        self.assertRegex(self.folder_md(), r"delivered: picklists on origin of proj: sessions \S+; workbench [0-9a-f]{12}; "
                                           r"delivery [0-9a-f]{12}; adopted\n")
        day, rec = oh.delivered_records(self.root / self.folder / "folder.md")[-1]
        self.assertTrue(rec["adopted"])
        self.assertIn("open the review already open on the audience's git host", proc.stdout)
        self.assertIn("for the branch picklists: this delivery is added to it", proc.stdout)
        self.assertIn("reply with the words in delivery.md's Review section: Health route for the API", proc.stdout)
        # A second delivery continues on the adopted branch as on its own,
        # with no --adopt needed and nothing of the first delivered twice.
        self.land_session(SID2, {"docs.md": "# health\n"}, "Document the route")
        self.run_office("sessions", self.name, SID2, check=0)
        self.write_words(WORDS.replace("Add the health route", "Document the health route"))
        proc = self.run_office("deliver", self.name, "--yes", "--branch", "picklists")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("(adding to the branch on the audience), from main", proc.stdout)
        self.assertIn("since the last delivery on picklists", proc.stdout)
        self.assertNotIn("adopted", proc.stdout)
        self.assertEqual(self.audience_subjects("picklists"),
                         ["Document the health route", "Add the health route", "Open the pull request", "Initial commit"])
        self.assertFalse(oh.delivered_records(self.root / self.folder / "folder.md")[-1][1]["adopted"])
        # The clone and the machine are as a delivery leaves them.
        self.assertEqual([r for r in git(self.clone, "for-each-ref", "--format=%(refname)", env=self.e.env).split()
                          if r.startswith("refs/office/")], [])
        self.assertEqual([d for d in self.e.tmpdir.glob("office-deliver*")], [])

    def test_a_branch_of_the_folders_own_is_not_adopted_and_adopt_changes_nothing_for_it(self):
        self.run_office("deliver", self.name, "--yes", check=0)
        self.land_session(SID2, {"docs.md": "d\n"}, "d")
        self.run_office("sessions", self.name, SID2, check=0)
        proc = self.run_office("deliver", self.name, "--yes", "--adopt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("(adding to the branch on the audience), from main", proc.stdout)
        self.assertNotIn("adopted", proc.stdout)
        self.assertEqual(self.folder_md().count("; adopted"), 0)

    def test_the_branch_url_for_known_hosts(self):
        self.assertEqual(odl.branch_url("https://github.example.edu/ORG/REPO", "picklists"),
                         "https://github.example.edu/ORG/REPO/pulls?q=is%3Apr+head%3Apicklists")
        self.assertEqual(odl.branch_url("git@gitlab.example.org:g/p.git", "br"),
                         "https://gitlab.example.org/g/p/-/merge_requests?scope=all&source_branch=br")
        self.assertIsNone(odl.branch_url(str(self.e.tmp / "audience.git"), "br"))
        # The History line's reader and writer agree, with and without the mark.
        text = oh.delivered_text("br", "origin", "proj", [SID], "a" * 12, "b" * 12, adopted=True)
        self.assertTrue(text.endswith("; delivery bbbbbbbbbbbb; adopted"))
        self.assertEqual(oh.delivered_text("br", "origin", "proj", [SID], "a" * 12, "b" * 12).count("adopted"), 0)
        self.assertIn("--adopt", self.e.run("deliver", "--help", cwd=self.root, check=0).stdout)
        # run() picks the branch's listing for an adopted delivery and the
        # compare page otherwise, from the same remote URL.
        self.assertIn("/pulls?", odl.branch_url("https://github.com/o/r", "br"))
        self.assertIn("/compare/main...br", odl.review_url("https://github.com/o/r", "br", "main"))


class TestAnAdoptedBranchOnAHost(AudienceCase):
    hosted = True

    def test_the_mirror_adopts_the_branch_the_same_way(self):
        tip = TestAnAdoptedBranch.pull_request_branch(self)
        proc = self.run_office("deliver", self.name, "--yes", "--branch", "picklists")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--branch picklists --adopt adds this delivery to it", proc.stderr)
        proc = self.run_office("deliver", self.name, "--yes", "--branch", "picklists", "--adopt")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"carried the landed work from {HOST}", proc.stderr)
        self.assertIn("adopted: it was made outside the office", proc.stdout)
        self.assertEqual(self.audience_subjects("picklists"), ["Add the health route", "Open the pull request", "Initial commit"])
        self.assertEqual(git(self.audience, "rev-parse", "picklists^", env=self.e.env).strip(), tip)
        self.assertFalse(any("git push" in c[-1] for c in self.ssh.connections()))
        self.assertEqual(self.ssh.left_on(HOST), [])
        self.assertIn("; adopted", self.folder_md())


class TestAnAdoptedBranchOnATerminal(AudienceCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_it_asks_once_default_no_and_y_adopts(self):
        TestAnAdoptedBranch.pull_request_branch(self)
        before = self.audience_subjects("picklists")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver", self.name, "--branch", "picklists"],
                                   self.root, self.e.env, [
            (b"add this delivery to it? (--adopt) (y/n) [n]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("made outside the office", seen)
        self.assertIn("stopped before anything left", seen)
        self.assertEqual(self.audience_subjects("picklists"), before)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver", self.name, "--branch", "picklists"],
                                   self.root, self.e.env, [
            (b"add this delivery to it? (--adopt) (y/n) [n]:", "y"),
            (b"Push picklists to origin as shown? (--yes) (y/n) [y]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Delivered: picklists is on origin", seen)
        self.assertIn("adopted: it was made outside the office", seen)
        self.assertEqual(self.audience_subjects("picklists")[0], "Add the health route")
        # On a terminal the folder closes at delivery once its work is
        # delivered (0.41.0): its record is in the filing cabinet.
        self.assertIn(f"the folder {self.name}: closed, done (its work is delivered", " ".join(seen.split()))
        filed = self.root / "filing-cabinet" / self.name / "folder.md"
        self.assertIn("; adopted", filed.read_text())


# --- 2. a planner's bundle names the branch its session builds on --------------------------------

class TestTheBundlesBranch(LandCase):
    """The bundle's brief carries `--- BRANCH NAME ---`; office start checks
    that branch out in alpha's clone before bale open --check, or stops
    with nothing written and says what to do in the clone."""

    def bundle(self, lines, stem="2026-10-28-review", write="src"):
        brief = f"# Brief\n\nAnswer the review.\n\n--- LANDS alpha, folder 1 ---\n{lines}\n"
        return bundle_file(self.downloads, stem, ["Answer the review", "--slug", "review", "--write", write,
                                                  "--constraint", ob.PROJECT_CONSTRAINT], brief=brief)

    def branch_of(self, repo):
        return self.e.git(repo, "symbolic-ref", "--short", "HEAD").strip()

    def test_the_reading_as_a_unit(self):
        self.assertEqual(oh.brief_branch("# B\n\n--- BRANCH picklists ---\n"), ("picklists", []))
        self.assertEqual(oh.brief_branch("# B\n\n--- BRANCH feature/x-1 ---\n"), ("feature/x-1", []))
        self.assertEqual(oh.brief_branch("# B\n\nno line\n"), (None, []))
        branch, problems = oh.brief_branch("--- BRANCH a ---\n--- BRANCH b ---\n--- BRANCH ---\n--- BRANCH refs/heads/x ---\n")
        self.assertEqual(branch, "a")
        self.assertEqual(len(problems), 3)
        self.assertIn("a second BRANCH line", problems[0])
        self.assertIn("not `--- BRANCH NAME ---`", problems[1])
        # Inside a fence or a notepad page it is quoted text, not a marker.
        self.assertEqual(oh.brief_branch("```\n--- BRANCH a ---\n```\n"), (None, []))
        got = ob.bundle_lands(self.root, self.bundle("--- BRANCH review-br ---", stem="2026-10-28-u"))
        self.assertEqual((got["branch"], got["place"], got["folder"]), ("review-br", "project", self.name))
        got = ob.bundle_lands(self.root, bundle_file(self.downloads, "2026-10-28-v", ["g", "--write", "src"],
                                                     brief="# B\n\n--- BRANCH only ---\n"))
        self.assertEqual((got["branch"], got["absent"], got["place"]), ("only", False, None))

    def test_the_branch_is_checked_out_before_bale_opens_the_bundle(self):
        was = self.branch_of(self.proj)
        self.e.git(self.proj, "branch", "review-br")
        b = self.bundle("--- BRANCH review-br ---")
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn("the bundle's brief names the branch its session builds on: review-br (its BRANCH line)", proc.stderr)
        self.assertIn(f"checked out review-br in alpha's clone at {os.path.realpath(self.proj)} (its local branch; it was on {was}), "
                      "the branch the bundle's brief names (its BRANCH line), so bale opens the bundle on it", proc.stderr)
        self.assertIn("Packed ", proc.stdout)
        self.assertEqual(self.branch_of(self.proj), "review-br")
        (cwd, argv, tty), = self.fake.calls_of("open")
        self.assertEqual(cwd, os.path.realpath(self.proj))
        # A second start on the same branch (a disjoint forecast, beside the
        # first session): nothing to check out, said, whatever is open.
        b = self.bundle("--- BRANCH review-br ---", stem="2026-10-28-again", write="docs")
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn("alpha's clone at", proc.stderr)
        self.assertIn("is on review-br, the branch the bundle's brief names (its BRANCH line); nothing to check out", proc.stderr)
        self.assertEqual(self.branch_of(self.proj), "review-br")

    def test_a_remotes_branch_is_tracked_and_nothing_else_is_fetched(self):
        # The pull request's branch is on the audience alone, fetched already.
        upstream = self.e.tmp / "upstream.git"
        self.e.git(self.e.tmp, "init", "-q", "--bare", str(upstream))
        self.e.git(self.proj, "remote", "add", "origin", str(upstream))
        self.e.git(self.proj, "push", "-q", "origin", "HEAD:refs/heads/pr-branch")
        self.e.git(self.proj, "fetch", "-q", "origin")
        b = self.bundle("--- BRANCH pr-branch ---")
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn("checked out pr-branch in alpha's clone", proc.stderr)
        self.assertIn("(a new local branch tracking origin/pr-branch;", proc.stderr)
        self.assertEqual(self.branch_of(self.proj), "pr-branch")
        self.assertEqual(self.e.git(self.proj, "config", "branch.pr-branch.remote").strip(), "origin")

    def test_what_stops_it_with_nothing_written(self):
        was = self.branch_of(self.proj)
        before = self.e.git(self.root, "rev-parse", "HEAD")
        folders = sorted(p.name for p in (self.root / "desk").iterdir())
        # No such branch anywhere the clone knows.
        b = self.bundle("--- BRANCH nowhere ---", stem="2026-10-28-a")
        proc = self.run_office("start", "--bundle", str(b), check=1)
        self.assertIn("has no such branch, locally or on a remote it has fetched", proc.stderr)
        self.assertIn("git fetch REMOTE nowhere", proc.stderr)
        self.assertIn("the office fetches nothing", proc.stderr)
        self.assertIn("nothing was written: no folder, no survey, no out tray, no session", proc.stderr)
        self.assertEqual(self.fake.calls_of("open"), [])
        # Uncommitted changes in the clone.
        self.e.git(self.proj, "branch", "review-br")
        (self.proj / "src" / "a.py").write_text("dirty\n")
        b = self.bundle("--- BRANCH review-br ---", stem="2026-10-28-b")
        proc = self.run_office("start", "--bundle", str(b), check=1)
        self.assertIn("has uncommitted changes (1 path(s): src/a.py), so review-br is not checked out over them", proc.stderr)
        self.assertIn("commit or stash them there, then start again", proc.stderr)
        self.e.git(self.proj, "checkout", "-q", "--", "src/a.py")
        # A session open in the clone.
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix it", "--write", "docs")
        b = self.bundle("--- BRANCH review-br ---", stem="2026-10-28-c")
        proc = self.run_office("start", "--bundle", str(b), check=1)
        self.assertIn(f"with 1 session(s) open in it ({sid}), which bale lands on the branch checked out there; it is "
                      "not moved under them", proc.stderr)
        self.assertIn("land or withdraw them first", proc.stderr)
        # The clone and the office are untouched by any refusal.
        self.assertEqual(self.branch_of(self.proj), was)
        self.assertEqual(self.e.git(self.proj, "status", "--porcelain"), "")
        self.assertEqual(sorted(p.name for p in (self.root / "desk").iterdir()), folders)
        # A bundle that lands in the office takes no BRANCH line.
        b = bundle_file(self.downloads, "2026-10-28-d", ["Plan it", "--slug", "plan", "--read-only"],
                        brief="# B\n\n--- LANDS the office, folder 1 ---\n--- BRANCH review-br ---\n")
        proc = self.run_office("start", "--bundle", str(b), check=1)
        self.assertIn("the session lands in the office, which works on one branch: a BRANCH line is for a project's "
                      "bundle; nothing was written", proc.stderr)
        # A line that does not read is said, and the start goes on without it.
        b = self.bundle("--- BRANCH refs/heads/x ---", stem="2026-10-28-e")
        proc = self.run_office("start", "--bundle", str(b), check=0)
        self.assertIn("not `--- BRANCH NAME ---`", proc.stderr)
        self.assertNotIn("checked out", proc.stderr)
        self.assertEqual(self.branch_of(self.proj), was)


class TestTheBundlesBranchOnAHost(HostedStartCase):
    def test_the_checkout_runs_through_the_shell_before_the_rehearsal(self):
        self.only_far()
        was = self.e.git(self.proj, "symbolic-ref", "--short", "HEAD").strip()
        self.e.git(self.proj, "branch", "review-br")
        brief = "# Brief\n\n--- LANDS far, folder 1 ---\n--- BRANCH review-br ---\n"
        b = bundle_file(self.e.tmp / "dl", "2026-10-28-far-review", ["Answer it", "--slug", "far-review", "--write", "src",
                                                                    "--constraint", ob.PROJECT_CONSTRAINT], brief=brief)
        proc = self.run_office("start", "--bundle", str(b))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"checked out review-br in far's clone at {self.proj} on {HOST} (its local branch; it was on {was})",
                      proc.stderr)
        self.assertEqual(self.e.git(self.proj, "symbolic-ref", "--short", "HEAD").strip(), "review-br")
        calls = self.ssh.connections()
        self.assertTrue(all(c[0] == HOST for c in calls), calls)
        checkout = [i for i, c in enumerate(calls) if "git checkout" in c[-1]]
        opened = [i for i, c in enumerate(calls) if "open" in c[-1] and "--check" in c[-1]]
        self.assertEqual(len(checkout), 1, [c[-1][:80] for c in calls])
        self.assertTrue(opened and checkout[0] < opened[0], [c[-1][:80] for c in calls])
        self.assertEqual(self.ssh.left_on(HOST), [])
