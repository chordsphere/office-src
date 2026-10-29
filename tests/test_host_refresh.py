"""Tests for office-src 0.39.0: a hosted clone's view of its audience, and
bale's sandbox setting (the M10 friction report of 2026-10-27, items 8 and
21; the gaps of 2026-10-28, A5 and A12). One class per item:

1. office projects refresh NAME: the audience's branches fetched here with
   a forcing refspec, carried to a hosted clone as a thin bundle, the base
   fast-forwarded when it can be, what moved said.
2. office start and office deliver offer it when the clone's view of the
   base is behind (--refresh and --no-refresh the twins; piped, said).
3. office deliver brings the base into the workbench when that merge is
   clean; a conflict is aborted, checked and refused by name.
4. prepare writes bale.toml's [sandbox] enabled = false only where bale's
   sandbox cannot run; office projects set NAME --prepare re-runs it, and
   office status names it.
5. The record: the folder's `merged` History line, and office projects'
   refreshed line read from the clone.

The suite makes no network call and runs no real ssh: a bare repo on this
machine is the audience, the fake ssh of tests/test_project_on_host.py
stands for the host, and a fake bale here answers `bale status --json`
for the sessions open in a clone. Run with the rest of the suite:

    tests/run.sh test_host_refresh
"""

import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, h  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_audience_line import AudienceCase, git  # noqa: E402
from test_project_on_host import HOST, FakeSsh  # noqa: E402

import office_host as ohost  # noqa: E402
import office_refresh as orf  # noqa: E402

LIB = REPO / "lib"
REFUSING_PROBE = "echo 'unshare: write failed /proc/self/uid_map: Operation not permitted' >&2; exit 1"


def status_line(open_sessions=()):
    """The one JSON line `bale status --json` prints, with the sessions
    open in the repo (the keys the read side reads, as bale 0.4.52 prints
    them; tests/fixtures' status-before.json)."""
    return json.dumps({"outcome": "status", "version": "0.4.56", "sid": None,
                       "repo": {"root": ".", "branch": "main", "tree_clean": True, "tree_change_count": 0,
                                "bale_initialised": True},
                       "session": {"state": "idle", "goal": None, "expects_probe": None, "clarification": None},
                       "staging": {"present": False, "path": ".bale/staging", "sessions": {}, "stale": []},
                       "outbox": [], "applied": {"count": 0, "latest": None}, "sessions": list(open_sessions),
                       "scopes": {s: ["src"] for s in open_sessions}, "integration_lock": None})


class RefreshCase(AudienceCase):
    """AudienceCase's world (the audience, the workbench clone on main with
    one session landed, the folder and its words), with a fake bale first on
    the PATH answering `bale status --json` (no session open unless a test
    says so), and a coworker who pushes to the audience."""

    def setUp(self):
        super().setUp()
        self.fake_bale()

    def fake_bale(self, open_sessions=()):
        bale = self.e.desktop / "bale"
        bale.write_text("#!/bin/sh\n"
                        'if [ "$1 $2" = "status --json" ]; then cat <<\'JSON\'\n'
                        f"{status_line(open_sessions)}\nJSON\nexit 0; fi\n"
                        'if [ "$1" = "--version" ]; then echo "bale 0.4.56"; exit 0; fi\n'
                        'echo "fake bale: $*" >&2; exit 97\n')
        bale.chmod(0o755)

    def coworker(self, files, message, branch="main", force=False):
        """A commit pushed to the audience's branch by someone else (the
        review merged on the git host, say); its sha."""
        cow = self.e.tmp / "cow"
        if not cow.is_dir():
            git(self.e.tmp, "clone", "-q", str(self.audience), str(cow), env=self.e.env)
        git(cow, "fetch", "-q", "origin", env=self.e.env)
        exists = git(cow, "rev-parse", "-q", "--verify", f"origin/{branch}", env=self.e.env, check=False).strip()
        git(cow, "checkout", "-q", "-B", branch, f"origin/{branch}" if exists else "origin/main", env=self.e.env)
        for rel, text in files.items():
            (cow / rel).parent.mkdir(parents=True, exist_ok=True)
            (cow / rel).write_text(text)
        git(cow, "add", "-A", env=self.e.env)
        if force:
            git(cow, "commit", "-q", "--amend", "-m", message, env=self.e.env)
        else:
            git(cow, "commit", "-qm", message, env=self.e.env)
        git(cow, "push", "-q", *(["-f"] if force else []), "origin", branch, env=self.e.env)
        return git(cow, "rev-parse", "HEAD", env=self.e.env).strip()

    def clone_ref(self, ref):
        return git(self.clone, "rev-parse", "-q", "--verify", ref, env=self.e.env, check=False).strip()

    def audience_ref(self, ref):
        return git(self.audience, "rev-parse", ref, env=self.e.env).strip()


# --- 1. office projects refresh NAME -------------------------------------------------------------

class TestTheRefreshVerb(RefreshCase):
    def test_it_fetches_forced_says_what_moved_and_never_moves_the_workbench(self):
        workbench = self.clone_ref("HEAD")
        self.coworker({"feat.txt": "one\n"}, "Start the feature", branch="feat")
        first = self.run_office("projects", "refresh", "proj", check=0)
        self.assertRegex(first.stdout, r"origin/feat: new, at [0-9a-f]{7}")
        self.assertIn("nothing moved", self.run_office("projects", "refresh", "proj", check=0).stdout)
        # The audience moves on: two commits on main, and feat force-pushed.
        self.coworker({"README.md": "hello, readers\n"}, "Merge the picklists review")
        tip = self.coworker({"NOTES.md": "notes\n"}, "Note it")
        rewritten = self.coworker({"feat.txt": "two\n"}, "Start the feature again", branch="feat", force=True)
        proc = self.run_office("projects", "refresh", "proj", check=0)
        self.assertRegex(proc.stdout, r"origin/main: [0-9a-f]{7}\.\.[0-9a-f]{7}, 2 commits\n")
        self.assertRegex(proc.stdout, r"origin/feat: [0-9a-f]{7}\.\.[0-9a-f]{7}, forced \([0-9a-f]{7} is no longer on "
                                      r"it: the audience rewrote it\)")
        self.assertIn("with a forcing refspec (+refs/heads/*:refs/remotes/origin/*)", proc.stdout)
        self.assertEqual(self.clone_ref("refs/remotes/origin/main"), tip)
        self.assertEqual(self.clone_ref("refs/remotes/origin/feat"), rewritten)
        # main is the workbench here, with the landed session on it: it has
        # commits of its own, so it is said and left, never merged.
        self.assertIn("main has commits of its own that origin/main does not, so it was not moved: a refresh never "
                      "merges", proc.stdout)
        self.assertEqual(self.clone_ref("HEAD"), workbench)
        self.assertIn("the checked-out branch main was not touched; no ref was deleted and nothing was pushed",
                      proc.stdout)
        self.assertEqual(git(self.clone, "status", "--porcelain", env=self.e.env), "")

    def test_the_base_is_fast_forwarded_checked_out_or_not(self):
        # The workbench on a branch of its own; main where the clone saw it.
        git(self.clone, "checkout", "-q", "-b", "work", env=self.e.env)
        git(self.clone, "branch", "-f", "main", "origin/main", env=self.e.env)
        tip = self.coworker({"README.md": "hello again\n"}, "Merge a review")
        proc = self.run_office("projects", "refresh", "proj", check=0)
        self.assertRegex(proc.stdout, r"main: [0-9a-f]{7}\.\.[0-9a-f]{7}, fast-forwarded \(update-ref: it is not "
                                      r"checked out\)")
        self.assertEqual(self.clone_ref("refs/heads/main"), tip)
        self.assertIn("the checked-out branch work was not touched", proc.stdout)
        # Checked out and clean, with no session open: --ff-only.
        git(self.clone, "checkout", "-q", "main", env=self.e.env)
        tip = self.coworker({"README.md": "and again\n"}, "Merge another review")
        proc = self.run_office("projects", "refresh", "proj", check=0)
        self.assertIn("fast-forwarded (checked out, git merge --ff-only)", proc.stdout)
        self.assertEqual(self.clone_ref("HEAD"), tip)
        self.assertEqual((self.clone / "README.md").read_text(), "and again\n")
        # A dirty tree stops only the checkout step; an open session stops it too.
        self.coworker({"README.md": "a third time\n"}, "Merge a third")
        (self.clone / "src" / "a.py").write_text("x = 9\n")
        proc = self.run_office("projects", "refresh", "proj", check=0)
        self.assertIn("main is checked out with uncommitted changes (1 path(s)), so it was not fast-forwarded",
                      proc.stdout)
        self.assertNotEqual(self.clone_ref("HEAD"), self.clone_ref("refs/remotes/origin/main"))
        git(self.clone, "checkout", "-q", "--", "src/a.py", env=self.e.env)
        self.fake_bale(["2026-10-29-open-one-001"])
        proc = self.run_office("projects", "refresh", "proj", check=0)
        self.assertIn("main is checked out with 1 session(s) open in the clone (2026-10-29-open-one-001)", proc.stdout)
        self.assertNotEqual(self.clone_ref("HEAD"), self.clone_ref("refs/remotes/origin/main"))

    def test_what_it_refuses_by_name(self):
        plain = self.e.tmp / "plain"
        git(self.e.tmp, "clone", "-q", str(self.audience), str(plain), env=self.e.env)
        self.run_office("projects", "add", "plain", str(plain), "--prepare", check=0)
        proc = self.run_office("projects", "refresh", "plain")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("plain declares no audience, so there is no view of one to refresh", proc.stderr)
        proc = self.run_office("projects", "refresh", "nosuch")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("no project named nosuch", proc.stderr)
        proc = self.run_office("projects", "refresh")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("name the project: office projects refresh NAME; piped input is never asked", proc.stderr)
        self.assertEqual(self.run_office("projects", "refresh", "proj", "--yes").returncode, 0)


class TestTheRefreshVerbOnAHost(RefreshCase):
    hosted = True

    def test_a_thin_bundle_travels_and_is_fetched_there_with_a_forcing_refspec(self):
        workbench = self.clone_ref("HEAD")
        tip = self.coworker({"README.md": "hello, readers\n"}, "Merge the picklists review")
        proc = self.run_office("projects", "refresh", "proj", check=0)
        self.assertRegex(proc.stdout, r"origin/main: [0-9a-f]{7}\.\.[0-9a-f]{7}, 1 commit\n")
        self.assertRegex(proc.stdout, rf"carried to {HOST} as a bundle of 1 branch\(es\), \d+ bytes, thin against the "
                                      r"\d+ commit\(s\) the clone names, checked by sha256, fetched there with "
                                      r"\+refs/heads/\*:refs/remotes/origin/\*; the bundle was removed")
        self.assertEqual(self.clone_ref("refs/remotes/origin/main"), tip)
        self.assertEqual(self.clone_ref("HEAD"), workbench)
        # The audience was fetched here, never from the host; the office's
        # temporary directory there is gone; the stamp is in the clone.
        applied = [c[-1] for c in self.ssh.connections() if "office-refresh" in c[-1]]
        self.assertTrue(applied)
        self.assertFalse(any("audience.git" in c[-1] and "fetch" in c[-1] for c in self.ssh.connections()))
        self.assertEqual(self.ssh.left_on(HOST), [])
        self.assertIn("refreshed ", git(self.clone, "cat-file", "-p", "refs/office-refresh/origin", env=self.e.env))
        # Nothing moved: no bundle at all.
        proc = self.run_office("projects", "refresh", "proj", check=0)
        self.assertIn("nothing moved", proc.stdout)
        self.assertNotIn("carried to", proc.stdout)


# --- 2. the offers at start and deliver -----------------------------------------------------------

class TestTheOffers(RefreshCase):
    """A clone on a host, whose view of the audience does not move unless
    the office carries it (a clone on this machine moves its own with the
    fetch deliver makes there; start's compare is the same for both)."""

    hosted = True

    def test_deliver_piped_says_it_and_goes_on(self):
        self.coworker({"README.md": "hello, readers\n"}, "Merge a review")
        self.coworker({"NOTES.md": "n\n"}, "And a note")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stderr, r"the clone's view of origin/main is 2 commits behind the audience's \([0-9a-f]{7}, "
                                      r"the audience at [0-9a-f]{7}\); not refreshed \(piped: office deliver "
                                      rf"{self.name} --refresh, or office projects refresh proj\)")
        self.assertNotEqual(self.clone_ref("refs/remotes/origin/main"), self.audience_ref("main"))

    def test_deliver_refresh_and_no_refresh(self):
        self.coworker({"README.md": "hello, readers\n"}, "Merge a review")
        proc = self.run_office("deliver", self.name, "--yes", "--no-refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("1 commit behind the audience's", proc.stderr)
        self.assertIn("not refreshed (--no-refresh)", proc.stderr)
        self.assertEqual(self.run_office("deliver", self.name, "--refresh", "--no-refresh").returncode, 1)
        self.coworker({"NOTES.md": "n\n"}, "And a note")
        self.land_session("2026-10-10-health-docs-001", {"docs.md": "d\n"}, "Document it")
        self.run_office("sessions", self.name, "2026-10-10-health-docs-001", check=0)
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(": refreshed (office projects refresh proj)", proc.stderr)
        self.assertEqual(self.clone_ref("refs/remotes/origin/main"), self.audience_ref("main"))

    def test_a_clone_here_moves_its_own_view_and_is_merged_without_asking(self):
        self.ssh.reset()
        self.run_office("projects", "set", "proj", "--on-this-machine", check=0)
        self.coworker({"README.md": "hello, readers\n"}, "Merge a review")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("the clone's view of", proc.stderr)
        self.assertIn("merged:   brought origin/main into the workbench", proc.stdout)

    def test_level_says_nothing(self):
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("the clone's view of", proc.stderr)
        self.assertNotIn("merged:", proc.stdout)

    def test_starts_compare_as_a_unit(self):
        with self.e.this_process():
            self.assertIsNone(orf.compare_line(self.root, "proj"))
            self.coworker({"README.md": "x\n"}, "Merge a review")
            self.coworker({"NOTES.md": "y\n"}, "Note")
            line = orf.compare_line(self.root, "proj")
            self.assertRegex(line, r"^the clone's view of origin/main is 2 commits behind the audience's")
            with self.assertRaises(orf.RefreshError):
                orf.compare_line(self.root, "nosuch")


class TestTheOffersOnATerminal(RefreshCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane
    hosted = True

    def test_deliver_asks_once_default_yes(self):
        self.coworker({"README.md": "hello, readers\n"}, "Merge a review")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver", self.name], self.root, self.e.env, [
            (b"(office projects refresh proj)? (--refresh) (y/n) [y]:", ""),
            (b"Push health-route to origin as shown? (--yes) (y/n) [y]:", "n"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("1 commit behind the audience's", seen)
        self.assertIn(": refreshed (office projects refresh proj)", seen)
        self.assertEqual(self.clone_ref("refs/remotes/origin/main"), self.audience_ref("main"))
        self.assertIn("merged:   brought origin/main into the workbench: merge commit", seen)


# --- 3. the clean merge ------------------------------------------------------------------------------

class TestTheCleanMerge(RefreshCase):
    def test_a_clean_merge_is_made_said_recorded_and_the_squash_runs_from_the_tip(self):
        tip = self.coworker({"README.md": "hello, readers\n"}, "Merge the picklists review")
        before = self.clone_ref("HEAD")
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stdout, r"merged:   brought origin/main into the workbench: merge commit [0-9a-f]{7} "
                                      r"\(1 commit of the audience's\)")
        # The merge is a real merge commit in the clone, as the author.
        head = self.clone_ref("HEAD")
        self.assertEqual(self.clone_ref("HEAD^1"), before)
        self.assertEqual(self.clone_ref("HEAD^2"), tip)
        self.assertEqual(git(self.clone, "log", "-1", "--format=%an <%ae>|%cn <%ce>|%s", env=self.e.env).strip(),
                         "Zed Zee <z@example.org>|Zed Zee <z@example.org>|Bring origin/main into the workbench "
                         "(office deliver)")
        # The delivery starts at the audience's tip and carries the folder's
        # work alone: README.md's change is the audience's, not the delivery's.
        self.assertEqual(self.audience_ref("health-route^"), tip)
        changed = git(self.audience, "diff", "--name-only", "health-route^", "health-route", env=self.e.env).split()
        self.assertEqual(sorted(changed), ["src/a.py", "src/health.py"])
        self.assertIn("since where the workbench branch and origin/main parted", proc.stdout)
        # One dated merged line in the folder's History, committed.
        self.assertRegex(self.folder_md(), rf"- \d{{4}}-\d{{2}}-\d{{2}} merged: origin/main {tip[:7]} into the "
                                           rf"workbench, {head[:7]}\n")
        self.assertEqual(git(self.root, "status", "--porcelain", env=self.e.env), "")

    def test_a_conflict_is_aborted_checked_and_refused_by_name(self):
        self.coworker({"src/a.py": "x = 5\n"}, "Change a on the audience")
        before = self.clone_ref("HEAD")
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("bringing origin/main into the workbench (main) conflicts in src/a.py; the merge was aborted there, "
                      "and nothing is left half-done in the clone", proc.stderr)
        self.assertIn("the office does not resolve a conflict in this release (a merge session, a bale session with "
                      "both sides in context, is the next release's); until then, by hand in the clone: git merge "
                      "origin/main on main, resolve and commit, then deliver again", proc.stderr)
        self.assertEqual(self.clone_ref("HEAD"), before)
        self.assertEqual(self.clone_ref("MERGE_HEAD"), "")
        self.assertEqual(git(self.clone, "status", "--porcelain", "-uno", env=self.e.env), "")
        self.assertNotIn("merged:", self.folder_md())
        self.assertNotIn("health-route", self.audience_refs())

    def test_a_dirty_clone_or_an_open_session_is_not_merged_and_the_plan_goes_on(self):
        self.coworker({"README.md": "hello, readers\n"}, "Merge a review")
        self.run_office("projects", "refresh", "proj", check=0)
        (self.clone / "src" / "a.py").write_text("x = 7\n")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("the workbench (main) is behind origin/main", proc.stderr)
        self.assertIn("and the clone has uncommitted changes (1 path(s): src/a.py), so origin/main was not merged into "
                      "it; the squash runs from where they parted, as before", proc.stderr)
        self.assertNotIn("merged:", self.folder_md())

    def test_a_merge_that_cannot_start_is_said_and_nothing_changes(self):
        # An untracked file where the audience now has one: git merge
        # refuses before it starts, so there is nothing to abort.
        self.coworker({"NEW.md": "the audience's\n"}, "Add a page")
        (self.clone / "NEW.md").write_text("the clone's own, untracked\n")
        before = self.clone_ref("HEAD")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("and git merge origin/main could not start in the clone (", proc.stderr)
        self.assertIn("so nothing changed there; the squash runs from where they parted, as before", proc.stderr)
        self.assertEqual(self.clone_ref("HEAD"), before)
        self.assertEqual((self.clone / "NEW.md").read_text(), "the clone's own, untracked\n")

    def test_an_open_session_keeps_the_workbench_as_it_is(self):
        self.coworker({"README.md": "hello, readers\n"}, "Merge a review")
        self.fake_bale(["2026-10-29-next-one-001"])
        before = self.clone_ref("HEAD")
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("and 1 session(s) are open in the clone (2026-10-29-next-one-001), so origin/main was not merged "
                      "under them", proc.stderr)
        self.assertEqual(self.clone_ref("HEAD"), before)


class TestTheCleanMergeOnAHost(RefreshCase):
    hosted = True

    def test_the_merge_runs_in_the_hosted_clone_and_the_bundle_carries_it(self):
        tip = self.coworker({"README.md": "hello, readers\n"}, "Merge the picklists review")
        proc = self.run_office("deliver", self.name, "--yes", "--refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("brought origin/main into the workbench: merge commit", proc.stdout)
        self.assertEqual(self.clone_ref("HEAD^2"), tip)
        self.assertEqual(self.audience_ref("health-route^"), tip)
        self.assertEqual(sorted(git(self.audience, "diff", "--name-only", "health-route^", "health-route",
                                    env=self.e.env).split()), ["src/a.py", "src/health.py"])
        self.assertEqual(self.ssh.left_on(HOST), [])


# --- 4. bale's sandbox setting --------------------------------------------------------------------

class TestTheSandboxSetting(RefreshCase):
    def fresh_clone(self, name):
        c = self.e.tmp / name
        git(self.e.tmp, "clone", "-q", str(self.audience), str(c), env=self.e.env)
        return c

    def test_it_is_written_only_where_the_probe_refuses(self):
        runs = self.fresh_clone("runs")
        proc = self.run_office("projects", "add", "runs", str(runs), "--prepare", check=0)
        self.assertIn("bale's sandbox runs there (true succeeds), so bale.toml says nothing of it", proc.stderr)
        self.assertEqual((runs / "bale.toml").read_text(), ohost.BALE_TOML_STUB)
        refuses = self.fresh_clone("refuses")
        proc = self.e.run("projects", "add", "refuses", str(refuses), "--prepare", cwd=self.root,
                          extra={"OFFICE_SANDBOX_PROBE": REFUSING_PROBE}, check=0)
        self.assertIn("bale's sandbox cannot run there (no unprivileged user namespaces", proc.stderr)
        self.assertIn("bale runs its response scripts unconfined there without asking at every apply, and "
                      "FORCE-logs the key on every run", proc.stderr)
        text = (refuses / "bale.toml").read_text()
        self.assertTrue(text.startswith(ohost.BALE_TOML_STUB))
        self.assertRegex(text, r"\n# office sandbox: written \d{4}-\d{2}-\d{2}: no unprivileged user namespaces where "
                               r"this clone is \(.*refused: unshare: write failed /proc/self/uid_map: Operation not "
                               r"permitted\)\n")
        self.assertTrue(text.endswith("\n[sandbox]\nenabled = false\n"))
        self.assertIn("office projects set refuses --prepare", text)
        self.assertEqual(git(refuses, "status", "--porcelain", env=self.e.env), "")
        # Again: the office's own table is kept, never written twice.
        with self.e.this_process():
            import os
            os.environ["OFFICE_SANDBOX_PROBE"] = REFUSING_PROBE
            lines = ohost.prepare(str(refuses), day="2026-10-29", name="refuses")
        self.assertIn("already holds the office's [sandbox] enabled = false, kept as it is", lines[-1])
        self.assertEqual((refuses / "bale.toml").read_text(), text)

    def test_a_table_of_the_occupants_is_left_and_a_probe_that_cannot_run_writes_nothing(self):
        c = self.fresh_clone("own")
        (c / "bale.toml").write_text("[sandbox]\nenabled = true\n")
        (c / ".git" / "info" / "exclude").write_text("bale.toml\n")
        with self.e.this_process():
            import os
            os.environ["OFFICE_SANDBOX_PROBE"] = REFUSING_PROBE
            lines = ohost.prepare(str(c), day="2026-10-29")
            self.assertIn("bale.toml already has a [sandbox] table, which the office leaves as it is", lines[-1])
            os.environ["OFFICE_SANDBOX_PROBE"] = "no-such-program-here"
            c2 = self.fresh_clone("noprobe")
            lines = ohost.prepare(str(c2), day="2026-10-29")
            self.assertIn("bale's sandbox could not be tested there", lines[-1])
        self.assertEqual((c / "bale.toml").read_text(), "[sandbox]\nenabled = true\n")
        self.assertEqual((c2 / "bale.toml").read_text(), ohost.BALE_TOML_STUB)


class TestTheSandboxSettingOnAHost(RefreshCase):
    hosted = True

    def refusing_host(self):
        """The host's own unshare refuses, as the M10 container's does."""
        bin_ = self.ssh.host_dir(HOST) / "bin"
        bin_.mkdir(exist_ok=True)
        (bin_ / "unshare").write_text("#!/bin/sh\necho 'unshare: write failed /proc/self/uid_map: Operation not "
                                      "permitted' >&2\nexit 1\n")
        (bin_ / "unshare").chmod(0o755)

    def test_set_prepare_writes_it_there_and_status_names_it_in_its_one_connection(self):
        self.refusing_host()
        extra = {"OFFICE_SANDBOX_PROBE": ""}  # the office's own probe, unshare -Ur true, on the host
        proc = self.e.run("status", cwd=self.root, extra=extra, check=0)
        self.assertIn("  proj: sandbox: bale's sandbox cannot run on someone@a-host.example (unshare: write failed "
                      "/proc/self/uid_map: Operation not permitted) and bale.toml does not turn it off, so every apply "
                      "there asks; office projects set proj --prepare writes the setting", proc.stdout)
        self.ssh.reset()
        proc = self.e.run("projects", "set", "proj", "--prepare", cwd=self.root, extra=extra, check=0)
        self.assertIn("bale's sandbox cannot run there (no unprivileged user namespaces: unshare -Ur true refused",
                      proc.stderr)
        text = (self.clone / "bale.toml").read_text()
        self.assertTrue(text.endswith("[sandbox]\nenabled = false\n"), text)
        self.ssh.reset()
        proc = self.e.run("status", cwd=self.root, extra=extra, check=0)
        self.assertRegex(proc.stdout, r"  proj: sandbox: off by bale.toml, written \d{4}-\d{2}-\d{2}: no unprivileged "
                                      r"user namespaces where this clone is \(unshare -Ur true refused: unshare: write "
                                      r"failed")
        # bale's version and the sandbox read share the host's one connection
        # for the bale line; the guard line reads the clone in its own.
        status_calls = [c for c in self.ssh.connections() if "office-sandbox" in c[-1]]
        self.assertEqual(len(status_calls), 1)
        self.assertIn("--version", status_calls[0][-1])

    def test_where_the_sandbox_runs_status_says_nothing_of_it(self):
        proc = self.run_office("status", check=0)
        self.assertNotIn("sandbox:", proc.stdout)


# --- 5. the record ----------------------------------------------------------------------------------

class TestTheRecord(RefreshCase):
    def test_merged_is_a_history_verb_and_status_takes_the_line(self):
        self.assertIn("merged", h.HISTORY_VERBS)
        self.assertNotIn("merged", h.STATE_VERBS)
        self.coworker({"README.md": "hello, readers\n"}, "Merge a review")
        self.run_office("deliver", self.name, "--yes", "--refresh", check=0)
        self.assertIn(" merged: origin/main ", self.folder_md())
        proc = self.run_office("status", check=0)
        self.assertNotIn("History verb 'merged'", proc.stdout + proc.stderr)
        self.assertIn(self.folder.split("/")[1], self.folder)

    def test_the_listing_reads_the_refresh_from_the_clone(self):
        proc = self.run_office("projects", check=0)
        self.assertIn("refreshed: not by the office yet (office projects refresh proj brings its view of origin "
                      "level)", proc.stdout)
        self.run_office("projects", "refresh", "proj", check=0)
        proc = self.run_office("projects", check=0)
        self.assertRegex(proc.stdout, r"refreshed: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z from origin \S+audience\.git, "
                                      r"by way of \S+ \(read from the clone's refs/office-refresh/origin\)")
        # No file of the office's records it.
        self.assertEqual(git(self.root, "status", "--porcelain", env=self.e.env), "")


if __name__ == "__main__":
    unittest.main()
