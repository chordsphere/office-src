"""Tests for rides from a project's host, the workbench branch named and set
at start, and a hosted project's audience URL kept (office-src 0.50.0).

  1. a ride may be a path on the project's host: `office projects set NAME
     --ride host:PATH`, checked there through the project's shell, shown as
     stored and marked as the host's, packed there by the host's bale at
     office start and carried back into the tray as the request is;
  2. start's screen names the clone's branch for every project session,
     read in the round start already makes;
  3. office start --branch NAME checks NAME out before the pack, with the
     BRANCH line's refusals, and a local branch behind its remote-tracking
     ref is fast-forwarded to it (a diverged one is checked out as it is);
  4. the audience line's sixth key, audience_url, kept for a hosted project
     so review state reads before its first review.

A host here is the fake ssh of tests/test_project_on_host.py: a directory of
its own (its HOME and TMPDIR) under the fake, its commands run on this
machine, so a host path written `~/...` is not a path here. Review state
reads through FakeGh (tests/test_pull_requests.py). Run with the rest of the
suite:

    tests/run.sh test_host_rides
"""

import json
import os
import pathlib
import re
import sys
import tarfile
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import h  # noqa: E402
from test_start import git_repo  # noqa: E402
from test_land import LandCase, bundle_file  # noqa: E402
from test_out_trip_to_host import HostedStartCase  # noqa: E402
from test_project_on_host import DOWN, HOST  # noqa: E402
from test_pull_requests import REMOTE, GhCase  # noqa: E402

import office_bale as ob  # noqa: E402
import office_host as ohost  # noqa: E402
import office_map as om  # noqa: E402
import office_review as orev  # noqa: E402


def tray_of(out):
    return pathlib.Path(re.search(r"^Out tray: (.+)$", out, re.M).group(1))


def run_of(rc, out="", err=""):
    return ohost.Run(rc, out, err, "shown", "where")


# --- 1. the spelling, read and rendered (units) --------------------------------------------------

class TestTheSpelling(unittest.TestCase):
    def test_host_path_is_stored_as_typed_and_checked_by_its_form(self):
        self.assertEqual(h.check_ride("host:~/notes/", HOST, "far"), ("host:~/notes", None))
        self.assertEqual(h.check_ride(" host:/srv/plans ", HOST, "far"), ("host:/srv/plans", None))
        self.assertEqual(h.check_ride("host:~", HOST, "far"), ("host:~", None))
        for bad in ("host:notes", "host:", "host:~me/x"):
            with self.assertRaises(h.HelperError, msg=bad):
                h.check_ride(bad, HOST, "far")
        with self.assertRaises(h.HelperError) as cm:
            h.check_ride("host:~/notes", None, "alpha")
        self.assertIn("host:~/notes rides from the project's host, and alpha has none", str(cm.exception))
        # A path that is neither host: nor absolute nor ~/ refuses as before.
        with self.assertRaises(h.HelperError):
            h.check_ride("notes", HOST, "far")
        self.assertTrue(h.is_host_ride("host:~/x"))
        self.assertFalse(h.is_host_ride("~/host:x"))
        self.assertEqual(h.host_ride_path("host:~/x"), "~/x")

    def test_the_renderings_mark_it_as_the_hosts_and_reach_nothing(self):
        self.assertEqual(h.ride_words("host:~/x", HOST), f"host:~/x (on {HOST})")
        self.assertEqual(h.ride_words("~/x", HOST), "~/x")
        entry = {"name": "far", "path": "~/far", "host": HOST, "shell": "ssh x bash -lc", "connect": "c",
                 "problem": None, "audience": None, "paused": False, "rides": ["host:~/x"], "after_land": [],
                 "declaration_problems": []}
        lines = h.describe_declarations(entry)
        self.assertIn(f"rides: host:~/x (on {HOST})", lines)
        self.assertFalse(any("NOT ON THIS MACHINE" in l for l in lines), lines)
        self.assertEqual(om.project_row(entry)[-1], f"rides: host:~/x (on {HOST})")

    def test_a_host_ride_on_a_project_here_is_a_declaration_problem(self):
        got = h.read_projects({"projects": {"alpha": {"path": "/srv/alpha", "rides": ["host:~/x"]},
                                            "far": {"path": "~/far", "host": HOST, "rides": ["host:~/x"]}}})
        alpha, far = got
        self.assertEqual(len(alpha["declaration_problems"]), 1)
        self.assertIn("rides from the project's host, and alpha has none", alpha["declaration_problems"][0])
        self.assertEqual(far["declaration_problems"], [])
        self.assertEqual(far["rides"], ["host:~/x"])

    def test_how_one_is_packed_there_from_its_facts(self):
        plan = ohost.ride_plan_there
        self.assertEqual(plan({"kind": "dir", "top": "/h/r", "real": "/h/r/docs/a"}), ("pack", "/h/r", "docs/a"))
        self.assertEqual(plan({"kind": "dir", "top": "/h/r", "real": "/h/r"}), ("pack", "/h/r", None))
        self.assertEqual(plan({"kind": "file", "top": "/h/r", "real": "/h/r/x.md"}), ("pack", "/h/r", "x.md"))
        self.assertEqual(plan({"kind": "dir", "top": None, "real": "/h/loose"}), ("scratch", "/h/loose", None))
        self.assertEqual(plan({"kind": "file", "top": None, "real": "/h/n.md"}), ("copy", "/h/n.md", None))

    def test_the_facts_read_back_or_refuse(self):
        rows = ohost.read_ride_facts(run_of(0, "dir\t~/a\t/h/r\t/h/r/a\ngone\t~/b\t\t\n"), ["~/a", "~/b"])
        self.assertEqual([(r["kind"], r["top"], r["real"]) for r in rows], [("dir", "/h/r", "/h/r/a"),
                                                                         ("gone", None, None)])
        with self.assertRaises(ohost.HostError):
            ohost.read_ride_facts(run_of(0, "dir\t~/a\t/h/r\t/h/r/a\n"), ["~/a", "~/b"])
        with self.assertRaises(ohost.HostError):
            ohost.read_ride_facts(run_of(2, "", "sh: broken"), ["~/a"])

    def test_leave_out_matches_a_host_ride_as_declared(self):
        entry = {"rides": ["host:~/notes", "/srv/notes"]}
        self.assertEqual(ob.ride_choice(entry, "far", ["host:~/notes/"]), (["/srv/notes"], ["host:~/notes"]))
        with self.assertRaises(ob.StartError):
            ob.ride_choice(entry, "far", ["~/notes"])

    def test_the_clones_branch_line(self):
        self.assertEqual(ob.clone_branch_line("far", "/r on h", run_of(0, "main\n")), "far's clone at /r on h is on main")
        self.assertEqual(ob.clone_branch_line("far", "/r", run_of(1)), "far's clone at /r is on a detached HEAD")
        self.assertIsNone(ob.clone_branch_line("far", "/r", run_of(128, "", "fatal: not a git repository")))

    def test_where_a_branch_stands_against_its_upstream(self):
        up = "upstream=refs/remotes/origin/x\nlocal=aaa\nremote=bbb\n"
        self.assertEqual(ob.read_upstream(run_of(0, up + "behind=yes\nahead=no\n"))["state"], "behind")
        self.assertEqual(ob.read_upstream(run_of(0, up + "behind=no\nahead=yes\n"))["state"], "ahead")
        self.assertEqual(ob.read_upstream(run_of(0, up + "behind=no\nahead=no\n"))["state"], "diverged")
        level = ob.read_upstream(run_of(0, "upstream=refs/remotes/origin/x\nlocal=a\nremote=a\nbehind=yes\nahead=yes\n"))
        self.assertEqual((level["state"], level["upstream"]), ("level", "origin/x"))
        self.assertIsNone(ob.read_upstream(run_of(0, "")))

    def test_an_audience_url_is_one_word(self):
        self.assertEqual(h.check_audience_url(" git@h:a/b.git "), "git@h:a/b.git")
        for bad in ("", "a b", "x\ny"):
            with self.assertRaises(h.HelperError):
                h.check_audience_url(bad)
        self.assertIn("audience_url", h.AUDIENCE_KEYS)


# --- 1. declared, checked where it lives ----------------------------------------------------------

class HostRideCase(HostedStartCase):
    """HostedStartCase's office, far alone, with a home on the host holding
    what rides from it: a repo (notes, with blueprints/ inside it), a
    directory outside git (loose/) and a file outside git (plan.md)."""

    def setUp(self):
        super().setUp()
        self.only_far()
        self.home = self.ssh.host_dir(HOST) / "home"
        self.home.mkdir(exist_ok=True)
        self.notes = git_repo(self.home / "notes", {"blueprints/plan.md": "a plan\n", "other.md": "o\n"})
        (self.home / "loose").mkdir()
        (self.home / "loose" / "a.txt").write_text("loose a\n")
        (self.home / "loose" / ".bale").mkdir()
        (self.home / "loose" / ".bale" / "secret").write_text("bale's own\n")
        (self.home / "plan.md").write_text("the plan, alone\n")

    def manifest_text(self):
        return (self.root / "floor-plan" / "manifest.toml").read_text()

    def fake_pack_calls(self):
        f = self.fake.dir / "pack-calls.jsonl"
        return [tuple(json.loads(l)) for l in f.read_text().splitlines()] if f.is_file() else []


class TestDeclaredOnTheHost(HostRideCase):
    def test_set_checks_it_through_the_shell_in_one_connection_and_lists_it_as_stored(self):
        proc = self.run_office("projects", "set", "far", "--ride", "host:~/notes/blueprints/", "--ride", "host:~/plan.md")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('rides = ["host:~/notes/blueprints", "host:~/plan.md"]', self.manifest_text())
        checks = [c for c in self.ssh.connections() if "office-rides" in c[-1]]
        self.assertEqual(len(checks), 1, self.ssh.connections())
        self.assertEqual(len(self.ssh.connections()), 1, "the declaration's one connection, and no other")
        listing = self.run_office("projects", check=0).stdout
        self.assertIn(f"rides: host:~/notes/blueprints (on {HOST})", listing)
        self.assertNotIn("NOT ON THIS MACHINE", listing)
        self.assertEqual(self.ssh.connections(), [], "the listing reaches no host for a ride")
        self.assertIn(f"rides: host:~/notes/blueprints (on {HOST}), host:~/plan.md (on {HOST})",
                      self.run_office("map", check=0).stdout)

    def test_a_path_gone_from_the_host_or_a_host_down_declares_nothing(self):
        before = self.manifest_text()
        proc = self.run_office("projects", "set", "far", "--ride", "host:~/gone")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"no such path on {HOST}: ~/gone", proc.stderr)
        self.assertEqual(self.manifest_text(), before)
        self.run_office("projects", "set", "far", "--host", DOWN, "--connect", "start the VPN client", check=0)
        before = self.manifest_text()
        proc = self.run_office("projects", "set", "far", "--ride", "host:~/notes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"{DOWN} does not answer", proc.stderr)
        self.assertIn("start the VPN client", proc.stderr)
        self.assertEqual(self.manifest_text(), before)

    def test_a_project_here_refuses_it_by_name_and_off_its_host_it_is_named(self):
        alpha = git_repo(self.e.tmp / "alpha2", {"a.md": "a\n"})
        self.run_office("projects", "add", "here", str(alpha), check=0)
        proc = self.run_office("projects", "set", "here", "--ride", "host:~/notes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("host:~/notes rides from the project's host, and here has none", proc.stderr)
        self.run_office("projects", "set", "far", "--ride", "host:~/notes", check=0)
        proc = self.run_office("projects", "set", "far", "--on-this-machine")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("far rides host:~/notes from its host", proc.stderr)


# --- 1. packed on the host, carried back ----------------------------------------------------------

class TestPackedOnTheHost(HostRideCase):
    def declare(self, *rides):
        args = [a for r in rides for a in ("--ride", r)]
        self.run_office("projects", "set", "far", *args, check=0)

    def test_each_kind_is_packed_by_the_hosts_bale_and_rides_in_the_tray(self):
        self.declare("host:~/notes/blueprints", "host:~/loose", "host:~/plan.md")
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it there", "--write", "src")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = proc.stdout
        self.assertIn(f"context-notes.tar.gz: rides with far (host:~/notes/blueprints, packed on {HOST})", out)
        self.assertIn(f"context-loose.tar.gz: rides with far (host:~/loose, packed on {HOST} from a copy there)", out)
        self.assertIn(f"plan.md: rides with far (host:~/plan.md, carried from {HOST} as it is)", out)
        tray = tray_of(out)
        self.assertEqual((tray / "plan.md").read_text(), "the plan, alone\n")
        with tarfile.open(tray / "context-loose.tar.gz") as t:
            names = t.getnames()
        self.assertTrue(any(n.endswith("a.txt") for n in names), names)
        self.assertFalse(any("secret" in n for n in names), names)
        # bale pack --context ran on the host for each: in the notes repo's
        # top with --include, in a scratch copy for loose/.
        contexts = [(cwd, argv) for cwd, argv in self.fake_pack_calls() if "--context" in argv]
        notes = [a for c, a in contexts if c == os.path.realpath(self.notes)]
        self.assertEqual(len(notes), 1, contexts)
        self.assertEqual(notes[0][notes[0].index("--include") + 1], "blueprints")
        scratch = [c for c, a in contexts if c.startswith(os.path.realpath(self.ssh.host_tmp(HOST)))]
        self.assertEqual(len(scratch), 1, contexts)
        # The scratch is gone, and nothing else is left on the host.
        self.assertEqual(self.ssh.left_on(HOST), [])
        # The office's own context and the doctrine stay made here.
        self.assertIn("the doctrine", out)

    def test_the_check_rides_the_round_start_makes_and_the_branch_is_read_there(self):
        self.declare("host:~/notes")
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it", "--write", "src")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        calls = [c[-1] for c in self.ssh.connections()]
        checks = [c for c in calls if "office-rides" in c]
        self.assertEqual(len(checks), 1, [c[:120] for c in calls])
        self.assertIn("status", checks[0])
        self.assertIn("symbolic-ref", checks[0])
        branch = self.e.git(self.proj, "symbolic-ref", "--short", "HEAD").strip()
        self.assertIn(f"far's clone at {self.proj} on {HOST} is on {branch}", proc.stderr)

    def test_one_gone_from_the_host_stops_the_start_before_anything_is_written(self):
        self.declare("host:~/loose")
        import shutil
        shutil.rmtree(self.home / "loose")
        before = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it", "--write", "src")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"a declared ride-along is not on {HOST}: host:~/loose", proc.stderr)
        self.assertEqual([a for c, a in self.fake_pack_calls() if a[0] == "pack"], [])
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), before)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_an_office_session_about_the_project_rides_it_the_same_way(self):
        self.declare("host:~/notes")
        folder = self.e.run("open", "plan-far", "--lane", "far", cwd=self.root, check=0).stdout.strip()
        proc = self.run_office("start", folder.split("/")[1], "--in-office", "--read-only", "--goal", "Plan far")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"context-notes.tar.gz: rides with far (host:~/notes, packed on {HOST})", proc.stdout)
        self.assertIn(f"(far's tree is on {HOST}, so it does not ride", proc.stdout)
        # Its check is one connection of its own, before anything is packed.
        checks = [c[-1] for c in self.ssh.connections() if "office-rides" in c[-1]]
        self.assertEqual(len(checks), 1)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_leave_out_and_no_rides_take_it_as_any_ride(self):
        self.declare("host:~/notes", "host:~/plan.md")
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it", "--write", "src",
                               "--leave-out", "host:~/notes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("(left out of this session: host:~/notes, which rides with far as declared)", proc.stdout)
        self.assertNotIn("context-notes.tar.gz", proc.stdout)
        self.assertIn("plan.md: rides with far", proc.stdout)
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Again", "--write", "docs", "--no-rides")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("rides with far (host:", proc.stdout)
        self.assertNotIn("office-rides", " ".join(c[-1] for c in self.ssh.connections()))


# --- 2 and 3. the branch named, and set, at start ---------------------------------------------------

class TestTheBranchAtStart(LandCase):
    def branch_of(self):
        return self.e.git(self.proj, "symbolic-ref", "--short", "HEAD").strip()

    def tip(self, ref):
        return self.e.git(self.proj, "rev-parse", ref).strip()

    def upstream(self):
        """An audience for alpha's clone, with ff-br on it, fetched."""
        bare = self.e.tmp / "upstream.git"
        self.e.git(self.e.tmp, "init", "-q", "--bare", str(bare))
        self.e.git(self.proj, "remote", "add", "origin", str(bare))
        self.e.git(self.proj, "push", "-q", "origin", "HEAD:refs/heads/ff-br")
        self.e.git(self.proj, "fetch", "-q", "origin")
        return bare

    def push_ahead(self, bare, branch="ff-br"):
        """A commit on the audience's branch from elsewhere; its sha."""
        other = self.e.tmp / "other"
        if not other.is_dir():
            self.e.git(self.e.tmp, "clone", "-q", str(bare), str(other))
        self.e.git(other, "fetch", "-q", "origin")
        self.e.git(other, "checkout", "-q", "-B", branch, f"origin/{branch}")
        (other / "new.md").write_text(f"{len(list(other.iterdir()))}\n")
        self.e.git(other, "add", "-A")
        self.e.git(other, "-c", "user.name=O", "-c", "user.email=o@x", "commit", "-qm", "ahead")
        self.e.git(other, "push", "-q", "origin", branch)
        self.e.git(self.proj, "fetch", "-q", "origin")
        return self.e.git(other, "rev-parse", "HEAD").strip()

    def test_the_screen_names_the_branch_for_every_project_session(self):
        branch = self.branch_of()
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"alpha's clone at {os.path.realpath(self.proj)} is on {branch}", proc.stderr)
        self.e.git(self.proj, "checkout", "-q", "--detach")
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g2", "--write", "docs")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("is on a detached HEAD", proc.stderr)
        # An office session names none: the office is not a clone.
        proc = self.run_office("start", "fix-login", "--in-office", "--read-only", "--goal", "Plan")
        self.assertNotIn("'s clone at", proc.stderr)

    def test_branch_checks_it_out_before_the_pack(self):
        was = self.branch_of()
        self.e.git(self.proj, "branch", "review-br")
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--branch", "review-br")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"checked out review-br in alpha's clone at {os.path.realpath(self.proj)} (its local branch; it "
                      f"was on {was}), the branch --branch names, so bale packs the session on it", proc.stderr)
        self.assertIn(f"is on review-br", proc.stderr)
        self.assertEqual(self.branch_of(), "review-br")
        self.assertIn("Packed ", proc.stdout)

    def test_branch_refuses_as_the_branch_line_does_with_nothing_written(self):
        was = self.branch_of()
        before = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--branch", "nowhere")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--branch nowhere names the branch, and alpha's clone at", proc.stderr)
        self.assertIn("has no such branch, locally or on a remote it has fetched", proc.stderr)
        self.assertIn("nothing was written", proc.stderr)
        self.e.git(self.proj, "branch", "review-br")
        (self.proj / "src" / "a.py").write_text("dirty\n")
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--branch", "review-br")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("has uncommitted changes (1 path(s): src/a.py), so review-br is not checked out over them",
                      proc.stderr)
        self.e.git(self.proj, "checkout", "-q", "--", "src/a.py")
        proc = self.run_office("start", "fix-login", "--in-office", "--goal", "g", "--branch", "review-br")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("the session lands in the office, which works on one branch: --branch is for a project's "
                      "session; nothing was written", proc.stderr)
        self.assertEqual(self.branch_of(), was)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), before)
        self.assertEqual(self.fake.calls_of("open"), [])

    def test_the_flag_stands_over_a_bundles_branch_line_and_is_said(self):
        self.e.git(self.proj, "branch", "brief-br")
        self.e.git(self.proj, "branch", "flag-br")
        brief = "# Brief\n\n--- LANDS alpha, folder 1 ---\n--- BRANCH brief-br ---\n"
        b = bundle_file(self.downloads, "2026-10-28-review", ["Answer it", "--slug", "review", "--write", "src",
                                                              "--constraint", ob.PROJECT_CONSTRAINT], brief=brief)
        proc = self.run_office("start", "--bundle", str(b), "--branch", "flag-br")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("the bundle's brief names the branch brief-br (its BRANCH line); --branch flag-br says "
                      "otherwise, and stands", proc.stderr)
        self.assertIn("checked out flag-br in alpha's clone", proc.stderr)
        self.assertEqual(self.branch_of(), "flag-br")

    def test_a_local_branch_behind_its_remote_tracking_ref_is_fast_forwarded(self):
        bare = self.upstream()
        self.e.git(self.proj, "branch", "--track", "ff-br", "origin/ff-br")
        old = self.tip("ff-br")
        new = self.push_ahead(bare)
        self.assertEqual(self.tip("origin/ff-br"), new)
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--branch", "ff-br")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"(its local branch, fast-forwarded from {old[:12]} to {new[:12]}, the tip of origin/ff-br;",
                      proc.stderr)
        self.assertEqual((self.branch_of(), self.tip("ff-br")), ("ff-br", new))

    def test_a_diverged_local_branch_is_checked_out_as_it_is_and_said(self):
        bare = self.upstream()
        self.e.git(self.proj, "branch", "--track", "ff-br", "origin/ff-br")
        self.e.git(self.proj, "checkout", "-q", "ff-br")
        (self.proj / "mine.md").write_text("mine\n")
        self.e.git(self.proj, "add", "-A")
        self.e.git(self.proj, "-c", "user.name=T", "-c", "user.email=t@x", "commit", "-qm", "mine")
        mine = self.tip("ff-br")
        self.e.git(self.proj, "checkout", "-q", "-")
        theirs = self.push_ahead(bare)
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--goal", "g", "--branch", "ff-br")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"it has diverged from origin/ff-br ({mine[:12]} here, {theirs[:12]} there), so it is checked "
                      "out as it is: nothing is forced", proc.stderr)
        self.assertEqual((self.branch_of(), self.tip("ff-br")), ("ff-br", mine))


class TestTheBranchOnAHost(HostedStartCase):
    def test_branch_runs_through_the_shell_and_the_line_names_the_host(self):
        self.only_far()
        self.e.git(self.proj, "branch", "far-br")
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "g", "--write", "src", "--branch", "far-br")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"checked out far-br in far's clone at {self.proj} on {HOST}", proc.stderr)
        self.assertIn(f"far's clone at {self.proj} on {HOST} is on far-br", proc.stderr)
        self.assertTrue(all(c[0] == HOST for c in self.ssh.connections()))
        self.assertEqual(self.ssh.left_on(HOST), [])


# --- 4. the audience URL, kept for a hosted project -------------------------------------------------

class TestTheAudienceURL(HostedStartCase):
    def setUp(self):
        super().setUp()
        self.only_far()
        self.e.git(self.proj, "remote", "add", "origin", REMOTE)

    def test_set_with_the_audience_keeps_it_and_the_flags_set_and_clear_it(self):
        proc = self.run_office("projects", "set", "far", "--audience", "origin")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        manifest = self.root / "floor-plan" / "manifest.toml"
        self.assertIn(f'audience_url = "{REMOTE}"', manifest.read_text())
        self.assertIn(f"audience URL: {REMOTE}", self.run_office("projects", check=0).stdout)
        proc = self.run_office("projects", "set", "far", "--audience-url", "git@elsewhere:a/b.git")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('audience_url = "git@elsewhere:a/b.git"', manifest.read_text())
        proc = self.run_office("projects", "set", "far", "--no-audience-url")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("audience_url", manifest.read_text())
        self.assertIn("audience URL: not kept", self.run_office("projects", check=0).stdout)

    def test_a_project_here_keeps_none(self):
        alpha = git_repo(self.e.tmp / "here", {"a.md": "a\n"})
        self.e.git(alpha, "remote", "add", "origin", REMOTE)
        self.run_office("projects", "add", "here", str(alpha), "--audience", "origin", check=0)
        self.assertNotIn("audience_url", (self.root / "floor-plan" / "manifest.toml").read_text())
        proc = self.run_office("projects", "set", "here", "--audience-url", REMOTE)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("an audience URL is kept for a project on a host only", proc.stderr)


class TestReviewStateFromTheKeptURL(GhCase):
    def test_a_hosted_project_reads_its_review_before_one_is_recorded(self):
        proc = self.deliver()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        folders = h.read_folders(self.root)
        entry = next(p for p in ob.office_projects(self.root) if p["name"] == "proj")
        (branch,) = orev.delivered_branches(folders, "proj", entry["audience"])
        self.gh.add_pull(1, branch)
        hosted = dict(entry, host=HOST, resolved=None, audience_url=None)
        with self.e.this_process():
            self.assertIsNone(orev.project_reviews(hosted, folders))
            self.assertEqual(orev.remote_url_of(dict(hosted, audience_url=REMOTE)), REMOTE)
            got = orev.project_reviews(dict(hosted, audience_url=REMOTE), folders)
        self.assertEqual([r["number"] for r in got["rows"]], [1])
        self.assertIsNone(got["problem"])


if __name__ == "__main__":
    unittest.main()
