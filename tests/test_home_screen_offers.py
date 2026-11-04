"""Tests for office-src 0.41.0: the next step offered by key (the gaps of
2026-10-28, A1, A7's paused mark, A9, A10 and A14, and 0.40.0's proposal of
the waiting merge session). One class per item of the brief:

1. A folder on a project with an audience stays on the desk after office
   land and closes at delivery; the desk names it landed, not delivered.
2. office land ends with deliver's line, the folder's number filled in.
3. The home screen, the Next line and bare office deliver offer the folders
   whose work landed and is not delivered; bare office probe takes the one
   folder that records a session open.
4. The office's tail on the planner's relay block: the folder, its state,
   the deliver line and land's letterhead review, after bale's END marker.
5. office withdraw --bundle takes a bundle out of the offer, by a rename;
   the offer says when the downloads hold two copies of one stem.
6. office projects set NAME --paused: the renderings read nothing of it and
   office start sends nothing to it.
7. A merge job waiting for its session is offered by key, said on the desk,
   the Next line and in office status.

The worlds are the suite's own: tests/test_land.py's LandCase (an office
scoping alpha, a fake bale that packs and lands), given an audience the way
tests/test_delivery_words.py gives it one, and tests/test_host_refresh.py's
RefreshCase (an audience, a workbench clone with one session landed, a fake
bale answering bale status); tests/test_deliver_merges.py's MergeCase for
the merge job. The terminal classes run in the serial lane. Run with the
rest of the suite:

    tests/run.sh test_home_screen_offers
"""

import datetime as dt
import os
import pathlib
import re
import subprocess
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import LandCase, bundle_file, response_tarball  # noqa: E402
from test_audience_line import SID, git  # noqa: E402
from test_host_refresh import RefreshCase  # noqa: E402
from test_deliver_merges import MergeCase, SID_M  # noqa: E402
from test_home_screen import FakeNames, groups, home, waiting, bundle_argv, downloads_set  # noqa: E402
from test_probe import probe_block  # noqa: E402

import office_bale as ob  # noqa: E402
import office_home as hs  # noqa: E402
import office_helper as oh  # noqa: E402

NOW = dt.datetime(2026, 11, 2, 15, 0, tzinfo=dt.timezone.utc)
SID_OLD = "2026-10-01-health-before-001"


def number_of(md_text):
    return re.search(r"^- number: (\d+)$", md_text, re.M).group(1)


def open_status(case):
    """The folder as office start leaves it: status open, its History said."""
    md = case.root / case.folder / "folder.md"
    text = md.read_text().replace("- status: queued", "- status: open")
    text = text.rstrip("\n") + f"\n- {dt.date.today().isoformat()} opened: {SID}\n"
    md.write_text(text)
    git(case.root, "commit", "-qam", "opened", env=case.e.env)


class AudienceLandCase(LandCase):
    """LandCase's office, alpha given an audience (a bare repo for its git
    host, origin in alpha's clone, an author and a base), as office projects
    set gives one."""

    def setUp(self):
        super().setUp()
        audience = self.e.tmp / "alpha-audience.git"
        git(self.e.tmp, "init", "-q", "--bare", str(audience), env=self.e.env)
        git(self.proj, "remote", "add", "origin", str(audience), env=self.e.env)
        self.run_office("projects", "set", "alpha", "--audience", "origin", "--author", "Pat <pat@example.org>",
                        "--base", "main", check=0)
        self.n = number_of(self.folder_md())

    def land_one(self, *flags, check=0):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        return sid, self.run_office("land", sid, *flags, check=check)


# --- 1. a folder with an audience closes at delivery -------------------------------------------

class TestAFolderWithAnAudienceClosesAtDelivery(AudienceLandCase):
    def test_land_leaves_it_on_the_desk_and_says_why(self):
        sid, proc = self.land_one()
        err = " ".join(proc.stderr.split())
        self.assertIn(f"{self.name} recorded {sid} alone, and it landed applied; alpha has an audience, so the "
                      f"folder stays on the desk until office deliver {self.n} carries the work (office close "
                      f"{self.name} closes it now)", err)
        self.assertTrue((self.root / self.folder).is_dir())
        self.assertIn(f"the folder {self.name}: stays on the desk until office deliver {self.n} carries its work to "
                      "origin", proc.stdout)
        # The desk names it: landed, not delivered, and the line that delivers it.
        desk = self.run_office("desk", check=0).stdout
        self.assertRegex(desk, rf"\[landed {sid} on \d{{4}}-\d{{2}}-\d{{2}}, not delivered; office deliver {self.n}\]")
        self.assertNotIn("[open, no session in flight]", desk)

    def test_close_still_closes_it_and_says_so(self):
        sid, proc = self.land_one("--close")
        self.assertIn(f"--close: {self.name} is closed with the landing, as you said, though alpha has an audience "
                      f"(office deliver {self.n} still carries its work from the filing cabinet)",
                      " ".join(proc.stderr.split()))
        self.assertTrue((self.root / "filing-cabinet" / self.name).is_dir())

    def test_a_project_with_no_audience_is_as_before(self):
        self.run_office("projects", "set", "alpha", "--no-audience", check=0)
        sid, proc = self.land_one()
        self.assertIn(f"{self.name} recorded {sid} alone, and it landed applied; piped, the folder stays open",
                      " ".join(proc.stderr.split()))
        self.assertNotIn("has an audience", proc.stderr)


class TestDeliverClosesTheFolder(RefreshCase):
    def setUp(self):
        super().setUp()
        open_status(self)
        self.n = number_of(self.folder_md())

    def test_a_delivered_folder_closes_with_close_and_says_it_in_lands_words(self):
        self.assertIn(f"[landed {SID} on ", self.run_office("desk", check=0).stdout)
        proc = self.run_office("deliver", self.name, "--yes", "--close")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"the folder {self.name}: closed, done (its work is delivered; office reopen {self.name} brings "
                      "it back)", " ".join(proc.stderr.split()))
        self.assertTrue((self.root / "filing-cabinet" / self.name / "folder.md").is_file())
        self.assertIn(" delivered: health-route on origin of proj: sessions " + SID,
                      (self.root / "filing-cabinet" / self.name / "folder.md").read_text())

    def test_piped_it_stays_and_says_the_line_and_leave_open_keeps_it(self):
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"{self.name}'s work is delivered; piped, the folder stays open: office deliver --close closes "
                      f"it with the delivery, office close {self.name} closes it now", " ".join(proc.stderr.split()))
        self.assertTrue((self.root / self.folder).is_dir())
        # Delivered: the desk no longer names it landed and not delivered.
        self.assertNotIn("not delivered", self.run_office("desk", check=0).stdout)
        # A second folder's run with --leave-open: kept, and said.
        self.coworker({"README.md": "hello again\n"}, "Readme on the audience")
        self.land_session("2026-10-11-health-more-001", {"src/more.py": "m = 1\n"}, "More")
        self.run_office("sessions", self.name, "2026-10-11-health-more-001", check=0)
        proc = self.run_office("deliver", self.name, "--yes", "--leave-open", "--refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"--leave-open: {self.name} stays open (office close {self.name} closes it)", proc.stderr)
        self.assertTrue((self.root / self.folder).is_dir())

    def test_a_session_still_to_deliver_keeps_it_and_is_named(self):
        # A session tagged applied on a commit the base already has rides in
        # no delivery: the folder records it, so it stays, and deliver says which.
        git(self.clone, "tag", f"applied/{SID_OLD}", "origin/main", env=self.e.env)
        self.run_office("sessions", self.name, SID_OLD, check=0)
        proc = self.run_office("deliver", self.name, "--yes", "--close")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"the folder {self.name} stays on the desk: {SID_OLD} landed and is not delivered yet (office "
                      f"deliver {self.n} carries it)", " ".join(proc.stderr.split()))
        self.assertTrue((self.root / self.folder).is_dir())

    def test_the_unit_reads_every_folders_delivered_lines(self):
        folders = [{"problem": None, "history": [("2026-11-01", "delivered", oh.delivered_text(
            "b", "origin", "proj", ["s1", "s2"], "abc1234", "def5678"))]},
                   {"problem": None, "history": [("2026-11-01", "opened", "x")]}]
        self.assertEqual(ob.delivered_by_project(folders), {"proj": {"s1", "s2"}})


# --- 2. land ends with the deliver line -----------------------------------------------------------

class TestLandEndsWithTheDeliverLine(AudienceLandCase):
    def test_the_last_line_is_deliver_with_the_folders_number(self):
        sid, proc = self.land_one()
        last = proc.stdout.rstrip("\n").splitlines()[-1]
        self.assertEqual(last, f"Next: office deliver {self.n}  (the work landed on alpha and is not delivered yet; "
                               "deliver carries it to origin)")

    def test_a_project_with_no_audience_ends_as_before(self):
        self.run_office("projects", "set", "alpha", "--no-audience", check=0)
        sid, proc = self.land_one()
        self.assertNotIn("Next: office deliver", proc.stdout)

    def test_a_merge_sessions_landing_says_deliver_makes_the_merge(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        head = git(self.proj, "rev-parse", "HEAD", env=self.e.env).strip()
        page = self.root / self.folder / "merge" / "merge.md"
        page.parent.mkdir()
        page.write_text("# Merge\n\n" + "".join(f"- {k}: {v}\n" for k, v in (
            ("project", "alpha"), ("audience", "origin"), ("kind", "base"), ("branch", "main"), ("tip", head),
            ("workbench", head), ("day", "2026-11-02"), ("file", "src/a.py"), ("session", sid))))
        git(self.root, "add", "-A", env=self.e.env)
        git(self.root, "commit", "-qm", "a merge job", env=self.e.env)
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        proc = self.run_office("land", sid, check=None)
        self.assertEqual(proc.stdout.rstrip("\n").splitlines()[-1],
                         f"Next: office deliver {self.n}  (the merge session landed; deliver makes the merge commit "
                         "in the workbench and carries the folder's own work)")


# --- 3. the home screen, the Next line, bare deliver and bare probe offer it ------------------------

def undelivered(n, name, sid, day, project="proj", audience="origin"):
    return {"folder": {"name": name, "number": n, "rel": f"desk/{name}", "title": name, "fields": {}},
            "project": project, "audience": audience, "sids": [sid], "sid": sid, "day": day,
            "at": dt.datetime.fromisoformat(day + "T12:00:00+00:00")}


class TestTheOffersAsUnits(unittest.TestCase):
    def test_the_next_line_after_the_moves_and_before_a_drop(self):
        u = [undelivered(4, "b", "2026-11-02-b-001", "2026-11-02"), undelivered(3, "a", "2026-11-01-a-001", "2026-11-01")]
        drops = [{"rel": "in-tray/x.md", "name": "x.md", "project": "proj", "heading": "x"}]
        g = groups(undelivered=u, drops=drops, open=[u[0]["folder"], u[1]["folder"]])
        cmd, why = ob.next_move("current", True, [], g, [{"name": "proj"}], 0)
        self.assertEqual((cmd, why), ("office deliver 4", "folder 4's work landed on proj and is not delivered yet; "
                                                          "deliver carries it to origin; 1 more wait"))
        # The moves come first, and never office start for such a folder.
        self.assertEqual(ob.next_move("current", True, [], dict(g, moves=(1, "a sitting", [])),
                                      [{"name": "proj"}], 0)[0], "office moves")
        self.assertNotIn("office start", ob.next_move("current", True, [], groups(undelivered=u[:1], open=[u[0]["folder"]]),
                                                       [{"name": "proj"}], 0)[0])
        # A merge job waiting goes before them.
        m = {"folder": {"name": "c", "number": 5, "rel": "desk/c", "title": "c"}, "landed": None,
             "job": {"audience": "origin", "branch": "main", "files": ["a", "b"], "day": "2026-11-02"}}
        self.assertEqual(ob.next_move("current", True, [], dict(g, merges=[m]), [{"name": "proj"}], 0),
                         ("office start 5 --merge", "folder 5's merge job waits; start --merge sends the session that "
                                                    "resolves it"))

    def test_the_home_screens_items_after_the_responses_and_before_the_bundles(self):
        u = [undelivered(4, "b", "2026-11-02-b-001", "2026-11-02")]
        m = {"folder": {"name": "c", "number": 5, "rel": "desk/c", "title": "Merge me"}, "landed": None,
             "job": {"audience": "origin", "branch": "main", "files": ["a"], "day": "2026-11-01"}}
        bundles = [{"stem": "2026-11-02-x", "path": pathlib.Path("/d/2026-11-02-x.bale-bundle"), "at": NOW,
                    "copies": 2}]
        items = hs.home_items("current", True, [], groups(undelivered=u, merges=[m]), [{"name": "proj"}], 0, None,
                              bundles, FakeNames(), [], NOW)
        self.assertEqual([i["argv"] for i in items], [["start", "5", "--merge"], ["deliver", "4"],
                                                      ["start", "--bundle", "/d/2026-11-02-x.bale-bundle"]])
        self.assertEqual(items[0]["label"], "Send the merge session for folder 5, Merge me: origin/main conflicts with "
                                            "the workbench in 1 file(s) (office deliver wrote the job on 2026-11-01)")
        self.assertTrue(items[0].get("next"))
        self.assertEqual(items[1]["label"], "Deliver folder 4, b (proj): 2026-11-02-b-001 landed 2026-11-02, not yet "
                                            "delivered")
        self.assertEqual(items[2]["label"], "Start the planner's bundle 2026-11-02-x (saved just now; 2 copies, the "
                                            "newest offered)")


class TestTheOffers(RefreshCase):
    def setUp(self):
        super().setUp()
        open_status(self)
        self.n = number_of(self.folder_md())

    def test_the_walk_in_the_home_screen_and_the_reader(self):
        out = self.run_office(check=0).stdout
        self.assertIn(f"Next: office deliver {self.n}  (folder {self.n}'s work landed on proj and is not delivered "
                      "yet; deliver carries it to origin)", out)
        self.assertRegex(out, rf"\[landed {SID} on \d{{4}}-\d{{2}}-\d{{2}}, not delivered; office deliver {self.n}\]")
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir(exist_ok=True)
        page, menu = home(self)
        self.assertRegex(page, rf"\[1\] Deliver folder {self.n}, health route \(proj\): {SID} landed "
                               r"\d{4}-\d{2}-\d{2}, not yet delivered  \(next\)")
        self.assertEqual(menu[0], ["1", "office", "deliver", self.n])
        proc = subprocess.run([sys.executable, "-B", str(REPO / "lib" / "office_bale.py"), "awaiting-delivery",
                               str(self.root)], env=self.e.env, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stdout, rf"^{self.name}\tfolder {self.n}, health route \(proj\): {SID} landed "
                                      r"\d{4}-\d{2}-\d{2}\n$")
        # Delivered by another folder's line: no longer offered.
        md = self.root / self.folder / "folder.md"
        md.write_text(md.read_text() + "- 2026-11-02 delivered: " + oh.delivered_text(
            "health-route", "origin", "proj", [SID], "abc1234", "def5678") + "\n")
        git(self.root, "commit", "-qam", "delivered", env=self.e.env)
        self.assertNotIn("office deliver", self.run_office(check=0).stdout)


class TestBareDeliverOnATerminal(RefreshCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_the_landed_folders_by_key_and_a_return_lists_every_folder(self):
        open_status(self)
        n = number_of(self.folder_md())
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver"], self.root, self.e.env, [
            (b"return lists every folder [return skips]: ", "1"),
            (b"as shown? (--yes) (y/n) [y]: ", "n"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Landed and not yet delivered:", seen)
        self.assertRegex(seen, rf"\[1\] folder {n}, health route \(proj\): {SID} landed \d{{4}}-\d{{2}}-\d{{2}}")
        self.assertIn("stopped before anything left", seen)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver"], self.root, self.e.env, [
            (b"return lists every folder [return skips]: ", ""),
            (b"Which folder, by its key (office deliver FOLDER)", "q-not-a-folder"),
        ])
        self.assertIn("Folders in desk/:", seen)


class ProbeOffersCase(LandCase):
    def setUp(self):
        super().setUp()
        self.sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        self.block = probe_block()


class TestBareProbe(ProbeOffersCase):
    def test_the_one_folder_with_a_session_open_is_the_probes(self):
        proc = self.run_office("probe", "-", "--yes", input=self.block, check=0)
        self.assertIn(f"desk/{self.name} records the one session open, {self.sid} (on alpha), so the probe is its "
                      "(office probe FOLDER names another)", " ".join(proc.stderr.split()))
        self.assertIn("=== PROBE BEGIN fix-login ===", proc.stdout)

    def test_two_are_named_piped_and_none_is_as_before(self):
        other = self.run_office("open", "docs-job", "--lane", "alpha: docs", check=0).stdout.strip()
        self.start(other.split("/")[1], "--on", "alpha", "--goal", "g", "--write", "docs")
        proc = self.run_office("probe", "-", "--yes", input=self.block, check=1)
        self.assertIn("2 folders on the desk record a session open where probes run", proc.stderr)
        self.assertIn("name one: office probe FOLDER; piped input is never asked", " ".join(proc.stderr.split()))
        with self.e.this_process():
            rows = ob.probe_folders(ob.Reader(), self.root)
        self.assertEqual([r[0] for r in rows], sorted([self.name, other.split("/")[1]]))
        self.assertEqual({r[2] for r in rows}, {"on alpha"})


class TestBareProbeOnATerminal(ProbeOffersCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_several_are_offered_by_key(self):
        other = self.run_office("open", "docs-job", "--lane", "alpha: docs", check=0).stdout.strip()
        osid = self.start(other.split("/")[1], "--on", "alpha", "--goal", "g", "--write", "docs")
        path = self.e.tmp / "probe.sh"
        path.write_text(self.block)
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'paste_command = "cat {path}"\n')
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "probe"], self.root, self.e.env, [
            (b"by its key (office probe FOLDER): ", "2"),
            (b"Run it? y or N (--yes)", "N"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Folders that record a session open where probes run:", seen)
        self.assertIn(f"desk/{other.split('/')[1]}: {osid} (on alpha)", seen)
        self.assertIn("not run: nothing was written", seen)


# --- 4. the office's tail on the planner's relay block ------------------------------------------

def clipboard(case):
    cfg = case.e.home / ".config/office-src"
    cfg.mkdir(parents=True, exist_ok=True)
    clip = case.e.tmp / "clipboard.txt"
    (cfg / "machine.toml").write_text(f'clipboard_command = "tee {clip}"\npaste_command = "cat {clip}"\n')
    return clip


class TestTheRelayTailOnATerminal(AudienceLandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def land_on_a_terminal(self):
        clip = clipboard(self)
        sid = self.start(self.name, "--on", "alpha", "--goal", "g", "--write", "src")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "land", sid], self.root, self.e.env, [
            (b"merge into origin (default)", ""),
        ])
        self.assertEqual(code, 0, seen)
        return sid, clip.read_text(), seen

    def test_the_tail_after_bales_end_marker_with_the_folder_the_line_and_the_review(self):
        sid, copied, seen = self.land_on_a_terminal()
        lines = copied.rstrip("\n").split("\n")
        end = lines.index(next(l for l in lines if l.startswith(f"=== RELAY END {sid} to planner")))
        # bale's block, byte for byte, as bale printed it on the screen.
        self.assertIn("\r\n".join(lines[:end + 1]), seen)
        tail = lines[end + 1:]
        self.assertEqual(tail[:3], [f"--- OFFICE land {sid} ---",
                                    f"folder: {self.n}, fix-login (desk/{self.name}, open; closes at delivery)",
                                    f"next: office deliver {self.n}"])
        self.assertTrue(tail[3].startswith(f"letterhead: {sid}'s landing is clean for delivery"), tail)
        self.assertEqual(tail[-1], "--- OFFICE END ---")
        self.assertEqual(len(tail), 5)
        # The screen ends with the deliver line, after the clipboard's.
        self.assertTrue(seen.rstrip().endswith(f"Next: office deliver {self.n}  (the work landed on alpha and is not "
                                               "delivered yet; deliver carries it to origin)"), seen[-400:])

    def test_no_audience_the_folder_closed_and_nothing_else(self):
        self.run_office("projects", "set", "alpha", "--no-audience", check=0)
        sid, copied, _ = self.land_on_a_terminal()
        tail = copied.rstrip("\n").split("\n")
        tail = tail[[i for i, l in enumerate(tail) if l.startswith("--- OFFICE land")][0]:]
        self.assertEqual(tail, [f"--- OFFICE land {sid} ---",
                                f"folder: {self.n}, fix-login (filing-cabinet/{self.name}, closed, done)",
                                "--- OFFICE END ---"])


# --- 5. a bundle withdrawn from the offer ---------------------------------------------------------

class TestABundleWithdrawn(LandCase):
    def setUp(self):
        super().setUp()
        downloads_set(self)

    def test_every_copy_is_renamed_said_and_offered_no_more(self):
        a = bundle_file(self.downloads, "2026-11-02-docs-pass", bundle_argv("docs-pass", "docs"))
        (self.downloads / "2026-11-02-docs-pass (1).bale-bundle").write_bytes(a.read_bytes())
        rows = waiting(self)
        self.assertEqual([r[1:3] for r in rows], [["2026-11-02-docs-pass", "just now; 2 copies, the newest offered"]])
        out, menu = home(self)
        self.assertIn("Start the planner's bundle 2026-11-02-docs-pass (saved just now; 2 copies, the newest offered)",
                      out)
        self.assertIn(["w", "office", "withdraw"], menu)
        self.assertIn("[w] withdraw a session never worked, or a bundle", out)
        proc = self.run_office("withdraw", "--bundle", "2026-11-02-docs-pass.bale-bundle", "--yes", check=0)
        for name in ("2026-11-02-docs-pass.bale-bundle", "2026-11-02-docs-pass (1).bale-bundle"):
            self.assertIn(f"{self.downloads / name} is now {name}.declined: the home screen and office start no longer "
                          "offer it (rename it back to offer it again)", proc.stdout)
            self.assertTrue((self.downloads / f"{name}.declined").is_file())
            self.assertFalse((self.downloads / name).exists())
        self.assertEqual(waiting(self), [])
        out, menu = home(self)
        self.assertNotIn("docs-pass", out)
        self.assertNotIn(["w", "office", "withdraw"], menu)

    def test_what_it_refuses(self):
        bundle_file(self.downloads, "2026-11-02-src-pass", bundle_argv("src-pass"))
        proc = self.run_office("withdraw", "--bundle", "2026-11-02-nope", "--yes", check=1)
        self.assertIn("no bundle named 2026-11-02-nope is in your downloads (they hold: 2026-11-02-src-pass); nothing "
                      "was renamed", " ".join(proc.stderr.split()))
        proc = self.run_office("withdraw", "--bundle", "2026-11-02-src-pass", check=1)
        self.assertIn("office withdraw --bundle 2026-11-02-src-pass --yes withdraws it", proc.stderr)
        self.run_office("start", "fix-login", "--on", "alpha", "2026-11-02-src-pass.bale-bundle", check=0)
        proc = self.run_office("withdraw", "--bundle", "2026-11-02-src-pass", "--yes", check=1)
        err = " ".join(proc.stderr.split())
        self.assertRegex(err, r"2026-11-02-src-pass was opened by \d{4}-\d{2}-\d{2}-src-pass-\d{3}, so it is not in the "
                              r"offer; the session is office land's, or office withdraw \S+'s if it was never worked")
        self.assertTrue((self.downloads / "2026-11-02-src-pass.bale-bundle").is_file())


class TestABundleWithdrawnOnATerminal(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_bare_withdraw_offers_the_bundle_and_asks_once_default_yes(self):
        downloads_set(self)
        bundle_file(self.downloads, "2026-11-02-docs-pass", bundle_argv("docs-pass", "docs"))
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "withdraw"], self.root, self.e.env, [
            (b"(office withdraw FOLDER, or --bundle STEM): ", "1"),
            (b"Withdraw the bundle 2026-11-02-docs-pass from the offer? (--yes) [y]: ", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("[1] the bundle 2026-11-02-docs-pass, saved just now", seen)
        self.assertTrue((self.downloads / "2026-11-02-docs-pass.bale-bundle.declined").is_file())


# --- 6. a project marked paused -------------------------------------------------------------------

class TestAProjectMarkedPaused(LandCase):
    LINE = "alpha: paused (office projects set alpha --unpaused)"

    def test_set_writes_the_key_and_says_it(self):
        proc = self.run_office("projects", "set", "alpha", "--paused", check=0)
        # 0.46.0: the line says the one thing still read of a paused project.
        self.assertEqual(proc.stdout.strip(), "alpha is paused: the office reads nothing of it and sends nothing to it "
                                              "until office projects set alpha --unpaused (one thing is still read: "
                                              "which of its sessions a bundle in your downloads opened, so that bundle "
                                              "leaves the offer)")
        plan = (self.root / "floor-plan/manifest.toml").read_text()
        self.assertIn("paused = true", plan)
        self.assertEqual(self.subjects(1), ["office projects: set alpha --paused"])
        proc = self.run_office("projects", "set", "alpha", "--unpaused", check=0)
        self.assertIn("alpha is not paused", proc.stdout)
        self.assertNotIn("paused", (self.root / "floor-plan/manifest.toml").read_text())
        proc = self.run_office("projects", "set", "alpha", "--paused", "--no-rides", check=1)
        self.assertIn("--paused goes alone", proc.stderr)

    def test_the_renderings_read_nothing_of_it_and_start_sends_nothing(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        self.run_office("projects", "set", "alpha", "--paused", check=0)
        here = os.path.realpath(self.proj)
        before = len([c for c in self.fake.calls_of("status") if c[0] == here])
        walk = self.run_office(check=0).stdout
        self.assertIn(self.LINE, walk)
        self.assertNotIn("alpha: cannot read", walk)
        self.assertIn(f"  {self.LINE}", self.run_office("status", check=0).stdout)
        self.assertIn(self.LINE, self.run_office("desk", check=0).stdout)
        listing = self.run_office("projects", check=0).stdout
        self.assertIn("(paused: office projects set alpha --unpaused)", listing)
        self.assertIn(self.LINE, self.run_office("projects", "--ledger", check=0).stdout)
        self.assertIn(self.LINE, self.run_office("sessions", self.name, check=None).stdout)
        self.assertEqual(len([c for c in self.fake.calls_of("status") if c[0] == here]), before,
                         "no bale call reads a paused project")
        later = self.run_office("open", "later", "--lane", "alpha: docs", check=0).stdout.strip()
        proc = self.run_office("start", later.split("/")[1], "--on", "alpha", "--goal", "g", check=1)
        self.assertIn("alpha: paused (office projects set alpha --unpaused); nothing was written",
                      " ".join(proc.stderr.split()))
        # A session already out on it still lands.
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        proc = self.run_office("land", sid, check=0)
        self.assertIn(f"Landed: {sid} is applied in alpha", proc.stdout)

    def test_the_key_as_a_unit(self):
        entry = oh.read_projects({"projects": {"a": {"path": "/x", "paused": True}, "b": {"path": "/y"},
                                               "c": {"path": "/z", "paused": "yes"}}})
        self.assertEqual([(p["name"], p["paused"]) for p in entry], [("a", True), ("b", False), ("c", False)])
        self.assertEqual(entry[2]["declaration_problems"], ["paused is true or false, not 'yes'"])
        with self.assertRaises(ob.BaleError) as got:
            ob.rendered(entry[0])
        self.assertEqual(str(got.exception), "a: paused (office projects set a --unpaused)")


# --- 7. the waiting merge session, offered by key -------------------------------------------------

class TestTheWaitingMergeSession(MergeCase):
    def test_offered_on_the_status_the_next_line_the_desk_and_the_home_screen(self):
        open_status(self)
        n = number_of(self.folder_md())
        self.conflict_on_the_audience()
        self.run_office("deliver", self.name, "--yes", "--refresh")
        day = self.job()["day"]
        status = self.run_office("status", check=None).stdout
        self.assertIn(f"folder {n}: merge job waiting, origin/main into the workbench, 1 file(s); office start {n} "
                      "--merge sends the session", status)
        walk = self.run_office(check=0).stdout
        self.assertIn(f"Next: office start {n} --merge  (folder {n}'s merge job waits; start --merge sends the session "
                      "that resolves it)", walk)
        self.assertIn(f"[merge job waiting: origin/main conflicts with the workbench in 1 file(s); office start {n} "
                      "--merge]", walk)
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir(exist_ok=True)
        page, menu = home(self)
        self.assertIn(f"[1] Send the merge session for folder {n}, health route: origin/main conflicts with the "
                      f"workbench in 1 file(s) (office deliver wrote the job on {day})  (next)", page)
        self.assertEqual(menu[0], ["1", "office", "start", n, "--merge"])
        self.assertNotIn("Deliver folder", page)
        # Sent: said nowhere new.
        with self.e.this_process():
            import office_deliver as odl
            odl.merge_sent(self.root, self.folder, SID_M)
        self.assertNotIn("merge job", self.run_office("status", check=None).stdout)
        self.assertNotIn("--merge", self.run_office(check=0).stdout)
        # Landed without the merge made: status says deliver makes it, and the
        # folder is landed and not delivered.
        self.run_office("sessions", self.name, SID_M, check=0)
        self.land_session(SID_M, {"src/a.py": "x = 5\ny = 3\n"}, "Resolve the merge")
        self.assertIn(f"folder {n}: merge session {SID_M} landed; office deliver {n} makes the merge commit",
                      self.run_office("status", check=None).stdout)
        self.assertIn(f"Next: office deliver {n}  ", self.run_office(check=0).stdout)


if __name__ == "__main__":
    unittest.main()
