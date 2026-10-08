"""Tests for the return trip from a host (office-src 0.16.0): office land
on a project on a host, machine.toml's downloads setting (asked once,
found by name, the newest of a browser's copies winning), land offering to
close a finished folder, one command reaching a host once, and the
runner's warning about an ignored SIGINT.

The suite makes no network call and runs no real ssh, rsync or docker:
0.14.0's fake ssh (tests/test_project_on_host.py) is first on the PATH,
and the host here keeps its own HOME, PATH and TMPDIR under the fake, so
what the office leaves in the host's temporary directory is seen, and an
after-land action is seen running there. The fake land bale of
tests/test_land.py answers through it, in the project's repo. Run with the
rest of the suite:

    tests/run.sh test_return_trip
"""

import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import LandCase, bundle_file, response_tarball  # noqa: E402
from test_project_on_host import DOWN, HOST, FakeSsh, make_project  # noqa: E402
from test_out_trip_to_host import HostedStartCase  # noqa: E402

import office_bale as ob  # noqa: E402
import office_host as ohost  # noqa: E402
import runner  # noqa: E402

LIB = REPO / "lib"


def older(path, seconds):
    """Set a file's modification time seconds into the past."""
    t = time.time() - seconds
    os.utime(path, (t, t))
    return path


class ReturnTripCase(HostedStartCase):
    """HostedStartCase's office with far alone (alpha's repo, on the fake
    host), far's after-land actions declared, the host's own HOME, PATH and
    TMPDIR, and this machine's downloads set to the case's downloads
    directory."""

    def setUp(self):
        super().setUp()
        self.only_far()
        h.set_declarations(self.root / "floor-plan/manifest.toml", "far", None,
                           ["touch AFTER-LAND-RAN", 'echo "$HOME" > AFTER-LAND-HOME'])
        self.e.git(self.root, "commit", "-qam", "far's after-land actions")
        host = self.ssh.host_dir(HOST)
        self.host_home = host / "home"
        self.host_home.mkdir(exist_ok=True)
        # The host's whole PATH: the fake bale and the system's tools, and
        # nothing else of this machine's.
        (host / "path").write_text(f"{self.fake.dir}:/usr/bin:/bin\n")
        self.machine = self.e.home / ".config" / "office-src" / "machine.toml"

    def set_downloads(self, *dirs):
        h.set_machine_downloads(self.machine, [str(d) for d in (dirs or (self.downloads,))])

    def applied_calls(self, verb="apply"):
        return self.fake.calls_of(verb)


# --- 1. office land on a hosted project ---------------------------------------------------------

class TestLandOnAHost(ReturnTripCase):
    def test_one_command_lands_it_there_and_leaves_nothing_on_the_host(self):
        self.set_downloads()
        sid = self.start(self.name, "--on", "far", "--goal", "Fix it there", "--write", "src")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        proc = self.run_office("land", sid, "--ratified")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"Landed: {sid} is applied in far (tag applied/{sid}).", proc.stdout)
        self.assertEqual((self.proj / "src/a.py").read_text(), "fixed\n")
        # bale applied a copy carried into the office's temporary directory
        # on the host, in far's repo there.
        (cwd, argv, tty), = self.applied_calls()
        self.assertEqual(cwd, os.path.realpath(self.proj))
        self.assertEqual(argv[0], "apply")
        self.assertTrue(argv[1].startswith(str(self.ssh.host_tmp(HOST))), argv)
        self.assertEqual(pathlib.Path(argv[1]).name, f"response-{sid}.tar.gz")
        self.assertFalse(tty)
        self.assertIn(f"carried response-{sid}.tar.gz to {HOST}", proc.stderr)
        # The relay came back whole; the after-land actions ran in the
        # repo there, with the host's own HOME.
        self.assertIn(f"=== RELAY BEGIN {sid} to planner ===", proc.stdout)
        self.assertIn(f"=== RELAY END {sid} to planner ===", proc.stdout)
        self.assertTrue((self.proj / "AFTER-LAND-RAN").is_file())
        self.assertEqual((self.proj / "AFTER-LAND-HOME").read_text().strip(), str(self.host_home))
        self.assertIn(f"after land (1 of 2), in {self.proj} on {HOST}: touch AFTER-LAND-RAN", proc.stderr)
        self.assertIn(f"After land, in {self.proj} on {HOST}:", proc.stdout)
        self.assertIn("ran (exit 0): touch AFTER-LAND-RAN", proc.stdout)
        # The ratification, as for a local landing.
        self.assertIn(f"- {sid} ratified ", (self.root / self.folder / "folder.md").read_text())
        # Nothing the office made is left on the host, and nothing asked.
        self.assertEqual(self.ssh.left_on(HOST), [])
        calls = self.ssh.connections()
        self.assertTrue(calls and all(c[0] == HOST for c in calls), calls)
        self.assertTrue(all("-tt" not in c for c in calls), calls)
        self.assertFalse(self.fake.is_open(self.proj, sid))

    def test_a_host_that_does_not_answer_stops_land_before_anything_is_carried(self):
        self.set_downloads()
        sid = self.start(self.name, "--on", "far", "--goal", "Fix it", "--write", "src")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        self.run_office("projects", "set", "far", "--host", DOWN, "--connect", "start the VPN client", check=0)
        before = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("land", sid)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("far's host did not answer, so it may be out there", proc.stderr)
        self.assertIn(f"{DOWN} does not answer", proc.stderr)
        self.assertIn(f"start the VPN client; then rerun: office land {sid}", proc.stderr)
        self.assertIn("nothing was carried and nothing ran", proc.stderr)
        self.assertEqual([c[0] for c in self.ssh.connections()], [DOWN])
        self.assertEqual(self.applied_calls(), [])
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), before)

    def test_a_hold_then_the_newest_copy_is_retried_there_and_named(self):
        self.set_downloads()
        sid = self.start(self.name, "--on", "far", "--goal", "g", "--write", "src")
        held = older(response_tarball(self.downloads, sid, {"src/a.py": "broken\n"}, validation="fail"), 60)
        proc = self.run_office("land", sid, check=1)
        self.assertIn(f"Held: bale held {sid} in far", proc.stdout)
        self.assertIn(f"=== RELAY BEGIN {sid} to worker ===", proc.stdout)
        self.assertIn(f"Next: office land {sid} --response FILE", proc.stdout)
        self.assertFalse((self.proj / "AFTER-LAND-RAN").exists())
        # With only the held copy in the downloads, piped land asks for the
        # corrected one by name, and names the copy it saw.
        proc = self.run_office("land", sid, check=1)
        self.assertIn(f"office land {sid} --response FILE", proc.stderr)
        self.assertIn(f"the downloads hold one copy, {held}, which may be the held one", proc.stderr)
        # The browser saves the corrected one as (1): the newest wins.
        fixed = response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"}, name=f"response-{sid} (1).tar.gz")
        proc = self.run_office("land", sid, check=0)
        self.assertIn(f"2 copies of response-{sid}.tar.gz are in the downloads; took the newest, {fixed}", proc.stderr)
        retry = self.applied_calls("retry")
        self.assertEqual(len(retry), 1)
        self.assertEqual(pathlib.Path(retry[0][1][1]).name, fixed.name)
        self.assertIn(f"Landed: {sid}", proc.stdout)
        self.assertTrue((self.proj / "AFTER-LAND-RAN").is_file())
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_a_clarification_hands_back_the_block_bale_relay_prints_there(self):
        self.set_downloads()
        sid = self.start(self.name, "--on", "far", "--goal", "g", "--write", "src")
        response_tarball(self.downloads, sid, kind="clarification")
        proc = self.run_office("land", sid, check=0)
        self.assertIn("Questions: the worker asked before building", proc.stdout)
        self.assertIn(f"BALE EXCHANGE BEGIN {sid}\n", proc.stdout)
        self.assertIn("BALE EXCHANGE END\n", proc.stdout)
        # The answer is carried there on stdin, by one line typed here.
        nxt = re.search(r"^Next: (.*)$", proc.stdout, re.M).group(1)
        self.assertTrue(nxt.startswith(f"ssh {HOST} bash -lc "), nxt)
        self.assertIn(f"bale relay {sid} -", nxt)
        self.assertIn("< ANSWER-FILE", nxt)
        (cwd, _, _), = self.fake.calls_of("relay")
        self.assertEqual(cwd, os.path.realpath(self.proj))
        self.assertTrue(self.fake.is_open(self.proj, sid))
        self.assertFalse((self.proj / "AFTER-LAND-RAN").exists())
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_a_sitting_there_ends_with_bale_unlock_there(self):
        sid = self.start(self.name, "--on", "far", "--read-only", "--goal", "Plan it there")
        proc = self.run_office("land", sid, check=0)
        self.assertIn(f"Ended: the sitting {sid} is closed in far", proc.stdout)
        (cwd, argv, _), = self.fake.calls_of("unlock")
        self.assertEqual((cwd, argv), (os.path.realpath(self.proj), ["unlock", sid, "--json"]))
        self.assertIn(f"ended: {sid}", (self.root / self.folder / "folder.md").read_text())
        # A sitting carries nothing, so the downloads were never needed.
        self.assertFalse(self.machine.exists())

    def test_a_response_given_by_path_or_by_name(self):
        sid = self.start(self.name, "--on", "far", "--goal", "g", "--write", "src")
        elsewhere = self.e.tmp / "elsewhere"
        path = response_tarball(elsewhere, sid, {"src/a.py": "by path\n"}, name="whatever.tar.gz")
        # A path needs no downloads setting.
        proc = self.run_office("land", str(path), check=0)
        self.assertIn(f"Landed: {sid}", proc.stdout)
        self.assertFalse(self.machine.exists())
        # A bare name: the current directory first, then the downloads.
        self.set_downloads()
        sid2 = self.start(self.name, "--on", "far", "--goal", "again", "--write", "docs")
        response_tarball(self.downloads, sid2, {"docs/d.md": "by name\n"})
        proc = self.e.run("land", "--response", f"response-{sid2}.tar.gz", cwd=elsewhere,
                          extra={"OFFICE_ROOT": str(self.root)}, check=0)
        self.assertIn(f"Landed: {sid2}", proc.stdout)
        self.assertEqual((self.proj / "docs/d.md").read_text(), "by name\n")

    def test_no_response_in_the_downloads_says_where_it_looked_and_carries_nothing(self):
        self.set_downloads()
        sid = self.start(self.name, "--on", "far", "--goal", "g", "--write", "src")
        proc = self.run_office("land", sid, check=1)
        self.assertIn(f"no response-{sid}.tar.gz in the downloads ({self.downloads})", proc.stderr)
        self.assertIn(f"office land {sid} --response FILE", proc.stderr)
        self.assertEqual(self.applied_calls(), [])
        self.assertEqual(len(self.ssh.connections()), 1, self.ssh.connections())


# --- 2. where downloads land ---------------------------------------------------------------------

class TestTheDownloadsKey(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="office-downloads-"))
        self.addCleanup(__import__("shutil").rmtree, self.tmp, True)

    def test_it_is_written_once_ahead_of_any_table_and_reads_back(self):
        m = self.tmp / "cfg" / "machine.toml"
        self.assertIsNone(h.machine_downloads(m))
        m.parent.mkdir()
        m.write_text('out_tray = "~/trays"\n\n[later]\nkey = 1\n')
        self.assertIsNone(h.machine_downloads(m))
        odd = self.tmp / 'with "quotes" and \\ and é'
        h.set_machine_downloads(m, [str(odd), "~/Downloads"])
        data = tomllib.loads(m.read_text())
        self.assertEqual(data["downloads"], [str(odd), "~/Downloads"])
        self.assertEqual(data["out_tray"], "~/trays")
        self.assertEqual(data["later"], {"key": 1})
        self.assertLess(m.read_text().index("downloads ="), m.read_text().index("[later]"))
        self.assertEqual(h.machine_downloads(m), [str(odd), os.path.expanduser("~/Downloads")])
        # Asked once: it is never written over.
        with self.assertRaises(h.HelperError):
            h.set_machine_downloads(m, ["/elsewhere"])
        fresh = self.tmp / "new" / "machine.toml"
        h.set_machine_downloads(fresh, ["/a"])
        self.assertEqual(h.machine_downloads(fresh), ["/a"])

    def test_a_value_that_is_not_a_list_of_directories_is_named(self):
        m = self.tmp / "machine.toml"
        m.write_text('downloads = "~/Downloads"\n')
        with self.assertRaises(h.HelperError) as cm:
            h.machine_downloads(m)
        self.assertIn('downloads = ["~/Downloads"]', str(cm.exception))

    def test_the_candidates_are_this_machines_likely_directories(self):
        home = self.tmp / "home"
        (home / "Downloads").mkdir(parents=True)
        users = self.tmp / "Users"
        (users / "someone" / "Downloads").mkdir(parents=True)
        (users / "Public" / "Downloads").mkdir(parents=True)
        (users / "nobody").mkdir()
        xdg = self.tmp / "saved-here"
        xdg.mkdir()
        (home / ".config").mkdir()
        (home / ".config" / "user-dirs.dirs").write_text(f'XDG_DOWNLOAD_DIR="{xdg}"\n')
        got = h.download_candidates(home, {}, users)
        self.assertEqual(got, [str(users / "someone" / "Downloads"), str(xdg), str(home / "Downloads")])
        self.assertEqual(h.download_candidates(self.tmp / "nohome", {}, self.tmp / "none"), [])
        # The suite steers the root through the environment; empty is none.
        self.assertEqual(h.download_candidates(home, {"OFFICE_WINDOWS_USERS": str(users)})[0],
                         str(users / "someone" / "Downloads"))
        self.assertEqual(h.download_candidates(home, {"OFFICE_WINDOWS_USERS": ""}), [str(xdg), str(home / "Downloads")])

    def test_the_suite_never_scans_the_running_machines_windows_homes(self):
        self.assertEqual(Env(self).env["OFFICE_WINDOWS_USERS"], "")

    def test_the_newest_of_a_browsers_copies_wins_and_a_tie_refuses(self):
        a, b = self.tmp / "a", self.tmp / "b"
        a.mkdir(); b.mkdir()
        plain = a / "response-2026-10-08-x-001.tar.gz"
        plain.write_text("1")
        older(plain, 30)
        copy = b / "response-2026-10-08-x-001 (1).tar.gz"
        copy.write_text("2")
        (a / "response-2026-10-08-x-0011.tar.gz").write_text("not a copy")
        (a / "response-2026-10-08-x-001 (x).tar.gz").write_text("not a copy")
        copies = ob.browser_copies([a, b, self.tmp / "missing"], "response-2026-10-08-x-001.tar.gz")
        self.assertEqual([p for p, _ in copies], [copy.resolve(), plain.resolve()])
        path, note = ob.newest_copy(copies, "response-2026-10-08-x-001.tar.gz")
        self.assertEqual(path, copy.resolve())
        self.assertIn("2 copies of response-2026-10-08-x-001.tar.gz are in the downloads; took the newest", note)
        self.assertEqual(ob.newest_copy(copies[1:], "n"), (plain.resolve(), None))
        t = time.time()
        os.utime(plain, (t, t)); os.utime(copy, (t, t))
        with self.assertRaises(ob.LandError) as cm:
            ob.newest_copy(ob.browser_copies([a, b], plain.name), plain.name)
        self.assertIn("saved at the same moment", cm.exception.lines[0])
        self.assertEqual(ob.name_parts("x.bale-bundle"), ("x", ".bale-bundle"))
        self.assertEqual(ob.name_parts("response-s.tar.gz"), ("response-s", ".tar.gz"))

    def test_the_office_never_reads_bales_config(self):
        for p in (REPO / "bin" / "office", *(REPO / "lib").glob("*.py")):
            text = p.read_text()
            self.assertNotIn("search_paths", text, p.name)
            self.assertNotIn("user/bale.toml", text, p.name)


class TestDownloadsOnALocalLand(LandCase):
    def test_a_local_land_takes_the_newest_of_several_copies_by_its_path(self):
        h.set_machine_downloads(self.e.home / ".config/office-src/machine.toml", [str(self.downloads)])
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        older(response_tarball(self.downloads, sid, {"src/a.py": "old\n"}), 60)
        new = response_tarball(self.downloads, sid, {"src/a.py": "new\n"}, name=f"response-{sid} (1).tar.gz")
        proc = self.run_office("land", sid, check=0)
        (_, argv, _), = self.fake.calls_of("apply")
        self.assertEqual(argv, ["apply", str(new.resolve())])
        self.assertIn("took the newest", proc.stderr)
        self.assertIn("bale gets it by its path, since its own search takes the plain name first", proc.stderr)
        self.assertEqual((self.proj / "src/a.py").read_text(), "new\n")

    def test_one_copy_or_no_setting_leaves_the_name_to_bales_search(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        self.run_office("land", sid, check=0)
        (_, argv, _), = self.fake.calls_of("apply")
        self.assertEqual(argv, ["apply", f"response-{sid}.tar.gz"])
        self.assertFalse((self.e.home / ".config/office-src/machine.toml").exists())


class TestDownloadsOnStart(ReturnTripCase):
    def test_a_bare_bundle_name_for_a_hosted_project_is_found_in_the_downloads(self):
        self.set_downloads()
        argv = ["Fix it there", "--slug", "fix-there", "--write", "src", "--constraint", ob.PROJECT_CONSTRAINT]
        older(bundle_file(self.downloads, "2026-10-08-fix-there", argv, brief="# Old\n"), 60)
        newer = bundle_file(self.downloads / "copies", "2026-10-08-fix-there", argv, brief="# New\n")
        newer = newer.rename(self.downloads / "2026-10-08-fix-there (1).bale-bundle")
        proc = self.run_office("start", self.name, "--on", "far", "2026-10-08-fix-there.bale-bundle")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"took the newest, {newer.resolve()}", proc.stderr)
        self.assertIn(f"is {newer.resolve()} on this machine; it travels to {HOST} for bale", proc.stderr)
        opened = self.fake.calls_of("open")
        self.assertEqual(len(opened), 1)
        self.assertEqual(pathlib.Path(opened[0][1][-1]).name, newer.name)
        self.assertEqual(self.ssh.left_on(HOST), [])


# --- 3. land offers to close a finished folder ---------------------------------------------------

class TestTheCloseOffer(LandCase):
    """Local, piped: the offer's rule and its flag twins."""

    def landed(self, *flags, files=None):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, files or {"src/a.py": "fixed\n"})
        return sid, self.run_office("land", sid, *flags, check=0)

    def test_piped_a_finished_folder_stays_open_and_land_says_so(self):
        sid, proc = self.landed("--ratified")
        self.assertIn(f"{self.name} recorded {sid} alone, and the planner ratified it with no exception; piped, "
                      "the folder stays open: office land --close closes it with the landing", proc.stderr)
        self.assertTrue((self.root / self.folder).is_dir())

    def test_close_closes_it_with_the_landing(self):
        sid, proc = self.landed("--ratified", "--close")
        self.assertFalse((self.root / self.folder).exists())
        md = (self.root / "filing-cabinet" / self.name / "folder.md").read_text()
        self.assertIn("- status: done", md)
        self.assertIn(f"done: office land: {sid} landed and was ratified, the folder's only session", md)
        self.assertIn(f"the folder {self.name}: closed, done", proc.stdout)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_leave_open_leaves_it_and_contradictions_refuse(self):
        _, proc = self.landed("--ratified", "--leave-open")
        self.assertIn(f"--leave-open: {self.name} stays open", proc.stderr)
        self.assertTrue((self.root / self.folder).is_dir())
        self.assertIn("contradict", self.run_office("land", "--close", "--leave-open", check=1).stderr)

    def test_it_is_not_offered_for_an_exception_or_a_second_session(self):
        sid, proc = self.landed("--ratified", "--except", "the slug", "--close")
        self.assertIn(f"--close: {self.name} stays open, since {sid} was ratified with an exception", proc.stderr)
        self.assertTrue((self.root / self.folder).is_dir())
        sid2, proc = self.landed("--ratified", "--close", files={"src/a.py": "again\n"})
        self.assertIn(f"it records 1 other session(s) as well ({sid})", proc.stderr)
        self.assertTrue((self.root / self.folder).is_dir())

    def test_nothing_landed_closes_nothing(self):
        sid = self.start(self.name, "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, {"src/a.py": "broken\n"}, validation="fail")
        proc = self.run_office("land", sid, "--ratified", "--close", check=1)
        self.assertIn("nothing landed, so no folder is closed", proc.stderr)
        self.assertTrue((self.root / self.folder).is_dir())

    def test_the_rule_reads_the_folder(self):
        md = self.e.tmp / "folder.md"
        sid, other = "2026-10-08-a-001", "2026-10-08-b-001"
        base = "# J\n\n## Sessions\n\nThe ids.\n\n- {lines}\n\n## History\n"
        md.write_text(base.format(lines=f"{sid}\n- {sid} ratified 2026-10-08"))
        self.assertEqual(h.finished_folder(md, sid), (True, None))
        md.write_text(base.format(lines=f"{sid}"))
        self.assertIn("is not ratified", h.finished_folder(md, sid)[1])
        md.write_text(base.format(lines=f"{other}\n- {sid}\n- {sid} ratified 2026-10-08"))
        self.assertIn("other session", h.finished_folder(md, sid)[1])
        md.write_text(base.format(lines=f"{other}"))
        self.assertIn("does not record", h.finished_folder(md, sid)[1])


class TestLandOnAHostOnATerminal(ReturnTripCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_the_downloads_are_asked_once_bale_asks_through_the_shell_and_the_folder_closes(self):
        mine = self.e.home / "Downloads"
        mine.mkdir()
        sid = self.start(self.name, "--on", "far", "--goal", "Fix it there", "--write", "src")
        response_tarball(mine, sid, {"src/a.py": "fixed\n"})
        # One Windows home of the suite's own, beside HOME's Downloads; the
        # answer is a path, so nothing hangs on the list's order.
        users = self.e.tmp / "windows-users"
        (users / "someone" / "Downloads").mkdir(parents=True)
        env = dict(self.e.env, OFFICE_WINDOWS_USERS=str(users))
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "land", sid], self.root, env, [
            (b"(downloads in machine.toml) [1]:", "?"),
            (b"Where this machine's browser saves", str(mine)),
            (b"merge into origin (default)", ""),
            (b"(--ratified, --except TEXT, --not-now) [not now]:", "yes"),
            (b"close the folder, done, or leave it open (--close, --leave-open) [close]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Where do downloads land on this machine?", seen)
        self.assertIn(f"1. {users / 'someone' / 'Downloads'}", seen)
        self.assertIn(f"2. {mine}", seen)
        self.assertNotIn("3. ", seen.split("Where do downloads land", 1)[1].split("[1]:", 1)[0])
        self.assertIn(f"Landed: {sid} is applied in far", seen)
        self.assertEqual(h.machine_downloads(self.machine), [str(mine)])
        # bale's walkthrough asked on the occupant's terminal, through ssh
        # -tt, and so did each after-land action; nothing else asked.
        (_, _, tty), = self.applied_calls()
        self.assertTrue(tty)
        attended = [c[-1] for c in self.ssh.connections() if "-tt" in c]
        self.assertEqual(len(attended), 3, self.ssh.connections())
        self.assertIn("bale apply", attended[0])
        self.assertTrue(all("bash -c" in c for c in attended[1:]), attended)
        self.assertTrue((self.root / "filing-cabinet" / self.name).is_dir())
        self.assertEqual(self.ssh.left_on(HOST), [])
        # Never asked again: the next land reads the key.
        other = self.run_office("open", "docs-job", "--lane", "far: docs", check=0).stdout.strip()
        sid2 = self.start(other.split("/")[1], "--on", "far", "--goal", "g", "--write", "docs")
        response_tarball(mine, sid2, {"docs/d.md": "x\n"})
        proc = self.run_office("land", sid2, check=0)
        self.assertNotIn("Where do downloads land", proc.stderr)
        self.assertIn(f"Landed: {sid2}", proc.stdout)


# --- 4. fewer connections ----------------------------------------------------------------------------

class TestOneCommandReachesAHostOnce(ReturnTripCase):
    def reaches(self):
        """The connections that only checked the host (`true`)."""
        return [c for c in self.ssh.connections() if c[-1] in ("true", "'true'")]

    def test_a_hosted_start_and_land_make_few_connections_and_reach_once(self):
        self.set_downloads()
        brief = self.e.tmp / "brief.md"
        brief.write_text("# The brief\n")
        self.ssh.reset()
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it", "--write", "src",
                               "--brief", str(brief))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        start_calls = self.ssh.connections()
        # start-check (version, status, the repo's check); the pack's reads
        # (status, the paths, the doctrine); the brief sent into a new
        # temporary directory; the pack with its removal; the request back.
        self.assertLessEqual(len(start_calls), 5, start_calls)
        self.assertEqual(self.reaches(), [])
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        self.ssh.reset()
        self.run_office("land", sid, "--not-now", check=0)
        land_calls = self.ssh.connections()
        # The plan's reads (status, dossier); the response sent into a new
        # temporary directory; bale with the removal; the outcome's dossier
        # (and relay); one per after-land action (two here).
        self.assertLessEqual(len(land_calls), 4 + 2, land_calls)
        self.assertEqual(self.reaches(), [])
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_the_reach_carries_across_processes_through_the_named_file(self):
        reached = self.e.tmp / "reached"
        reached.write_text("")
        env = dict(self.e.env, OFFICE_REACHED_FILE=str(reached), OFFICE_RERUN="office land")
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import office_host as o; "
                "p = o.Place(sys.argv[2], sys.argv[3]); o.reach(p); print(o.run_in(p, ['pwd']).stdout)")
        for _ in range(2):
            proc = subprocess.run([sys.executable, "-B", "-c", code, str(LIB), str(self.proj), HOST], env=env,
                                  capture_output=True, text=True, timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(reached.read_text(), f"ssh {HOST} bash -lc\n")
        # One `true` in the first process, none in the second.
        self.assertEqual(len(self.reaches()), 1, self.ssh.connections())

    def test_a_host_that_stops_answering_after_the_reach_says_so_in_the_reachs_words(self):
        reached = self.e.tmp / "reached"
        reached.write_text(f"ssh {DOWN} bash -lc\n")
        self.addCleanup(os.environ.__setitem__, "PATH", os.environ.get("PATH", ""))
        os.environ["PATH"] = self.e.env["PATH"]
        for k, v in (("OFFICE_REACHED_FILE", str(reached)), ("OFFICE_RERUN", "office land")):
            self.addCleanup(os.environ.pop, k, None)
            os.environ[k] = v
        ohost.forget_reach()
        self.addCleanup(ohost.forget_reach)
        place = ohost.Place(str(self.proj), DOWN, connect="start the VPN client")
        with self.assertRaises(ohost.HostError) as cm:
            ohost.run_many(place, [["true"]])
        self.assertEqual(cm.exception.kind, "unreachable")
        self.assertIn("start the VPN client; then rerun: office land", str(cm.exception))


class TestAHomeRelativePathOnAHost(unittest.TestCase):
    def test_a_tilde_path_keeps_its_meaning_through_the_shell(self):
        self.assertEqual(ohost.shell_path("~/work/far"), "\"$HOME\"/work/far")
        self.assertEqual(ohost.shell_path("~"), "\"$HOME\"")
        self.assertEqual(ohost.shell_path("/srv/a b"), "'/srv/a b'")
        e = Env(self)
        ssh = FakeSsh(e.tmp)
        home = ssh.host_dir(HOST) / "home"
        repo = make_project(home, "far", bale_dir=True)
        self.addCleanup(os.environ.__setitem__, "PATH", os.environ.get("PATH", ""))
        os.environ["PATH"] = ssh.path(e.env["PATH"])
        ohost.forget_reach()
        self.addCleanup(ohost.forget_reach)
        place = ohost.Place("~/projects/far", HOST)
        run = ohost.run_in(place, ["pwd"])
        self.assertEqual(os.path.realpath(run.stdout.strip()), os.path.realpath(repo))
        self.assertTrue(ohost.check_project(place)[0])
        self.assertTrue(ohost.path_exists(place))
        self.assertFalse(ohost.path_exists(place, "~/projects/nope"))
        ohost.prepare(place)
        self.assertIn("bale.toml", (repo / ".git" / "info" / "exclude").read_text())
        self.assertTrue((repo / "bale.toml").is_file())
        # Nothing was made under a directory literally named ~.
        self.assertFalse((home / "~").exists())


# --- 5. the riders: the runner's warning, the README's line ---------------------------------------

class TestTheRunnerWarnsOfAnIgnoredInterrupt(unittest.TestCase):
    def test_ignored_sigint_names_the_interrupt_tests(self):
        lines = runner.sigint_warning(signal.SIG_IGN)
        text = "\n".join(lines)
        self.assertIn("SIGINT is ignored", text)
        for name in runner.INTERRUPT_TESTS:
            self.assertIn(name, text)
        self.assertIn("in the foreground", text)
        self.assertIsNone(runner.sigint_warning(signal.SIG_DFL))

    def test_the_named_tests_exist(self):
        for name in runner.INTERRUPT_TESTS:
            module, cls, test = name.split(".")
            self.assertTrue(hasattr(getattr(__import__(module), cls), test), name)

    def test_a_run_started_with_sigint_ignored_warns(self):
        proc = subprocess.run([sys.executable, "-B", "-c",
                               "import signal, subprocess, sys; signal.signal(signal.SIGINT, signal.SIG_IGN); "
                               "sys.exit(subprocess.run([sys.executable, '-B', sys.argv[1], 'no_such_module']).returncode)",
                               str(REPO / "tests" / "runner.py")], capture_output=True, text=True, timeout=60)
        self.assertIn("[run] warning: SIGINT is ignored", proc.stderr)

    def test_the_readme_says_to_run_the_suite_in_the_foreground(self):
        readme = " ".join((REPO / "README.md").read_text().split())
        tests = readme.split("## Tests", 1)[1].split("\n## ", 1)[0]
        self.assertIn("in the foreground", tests)


# --- 6. the record ------------------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_version_the_releases_the_readme_and_the_doctrine(self):
        self.assertEqual((REPO / "VERSION").read_text().strip(), "0.16.0")
        releases = (REPO / "RELEASES.md").read_text()
        self.assertLess(releases.index("## 0.16.0"), releases.index("## 0.15.0"))
        readme = " ".join((REPO / "README.md").read_text().split())
        for words in ("downloads", "--close", "--leave-open", "lands there"):
            self.assertIn(words, readme)
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        packing = doctrine.split("## 4.", 1)[1].split("## 5.", 1)[0]
        for words in ("downloads", "lands on its host", "close"):
            self.assertIn(words, packing)
        reading = doctrine.split("## 10.", 1)[1].split("## 11.", 1)[0]
        self.assertIn("never reads bale's config", reading)

    def test_the_consumption_manifest_says_where_the_landing_surfaces_run(self):
        text = (REPO / "share" / "bale-consumption.toml").read_text()
        cons = ob.Consumption()
        for name in ("apply", "retry", "relay", "unlock"):
            self.assertIn("contract", cons.surface(name))
        self.assertIn("2026-10-08-return-trip-to-host-001", text)


if __name__ == "__main__":
    unittest.main()
