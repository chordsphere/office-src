"""Tests for office sessions FOLDER past a project the office cannot read
(0.38.0).

One project that cannot be read is a line, not a stop. Each project's
records are read in their own try, and only when a search for one of the
folder's sessions reaches them: the folder's own project (its lane)
first, then the projects whose records name the session, then the rest.
A project that cannot be read (its directory gone, bale refusing there,
its host not answering) is said once, in one line after the sessions,
and the search goes on through the others. office sessions stops (exit 3
from the reader, bin/office's die) only when a session was not found
while some project could not be read, since only then is "not found" in
doubt.

The sessions verb's other tests are tests/test_read_side.py
TestFolderSessions; this module reuses its fake bale and world pieces,
and tests/test_project_on_host.py's hosted world for a host that does
not answer. A project the fake bale has no captures for stands in for a
broken clone: bale refuses there (the fake's exit 97), the way a real
bale refuses where git cannot read HEAD.
"""

import json
import os
import pathlib
import shutil
import sys
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_read_side import APPLIED, MISS_SID, OPEN_WORKER, FakeBale, make_project  # noqa: E402
from test_project_on_host import DOWN, HostedCase  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)

# The project bale refuses in. Its name sorts before office-src, so in the
# floor plan's order it is reached first, as distributions-app was.
BROKEN = "attic"
FOUND_LINES = (f"- {APPLIED[2]}: space and templates\n",
               "    office-src: applied; opened 2026-09-29, last event 2026-09-29; work class mixed\n",
               "    attempt 1, apply 2026-09-29: applied, validation PASS; 6 claim(s): agree 6\n",
               f"- {OPEN_WORKER}\n    office-src: open; opened 2026-09-30",
               "    no response attempt yet\n")


def folder_page(path, title, lane, sessions):
    """A folder page as office open writes it, with the lane given (None
    for none) and the sessions [(sid, words)] recorded."""
    path.parent.mkdir(parents=True, exist_ok=True)
    values = {"title": title, "number": "1", "status": "queued", "queued": "2026-09-29",
              "history": "2026-09-29 queued: office open"}
    if lane is not None:
        values["lane"] = lane
    path.write_text(h.render_template((REPO / "templates/folder.md").read_text(), values))
    for sid, words in sessions:
        h.record_session(path, sid, words)
    return path


def broken_world(owner):
    """An office scoping the captured project and one bale refuses in,
    with three folders: one with no lane recording a closed session, the
    open worker and a sid no project holds; one with no lane recording
    the two that are found; and one whose lane names office-src recording
    the same two."""
    e = Env(owner)
    w = types.SimpleNamespace(e=e)
    w.proj = make_project(e.tmp, "office-src")
    w.broken = make_project(e.tmp, BROKEN)
    w.fake = FakeBale(e.tmp, {str(w.proj): "office-src"})
    w.path = w.fake.path(e.env["PATH"])
    e.env["PATH"] = w.path
    w.root = e.init()
    for name, where in (("office-src", w.proj), (BROKEN, w.broken)):
        h.add_project(w.root / "floor-plan/manifest.toml", name, str(where))
    both = [(APPLIED[2], "space and templates"), (OPEN_WORKER, "")]
    folder_page(w.root / "desk/2026-09-29-read-side/folder.md", "read side", None,
                both + [(MISS_SID, "never ran")])
    folder_page(w.root / "desk/2026-09-29-all-found/folder.md", "all found", None, both)
    folder_page(w.root / "desk/2026-09-29-in-lane/folder.md", "in lane", "office-src: lib", both)
    e.git(w.root, "add", "-A")
    e.git(w.root, "commit", "-qm", "two projects and three folders")
    return w


class BrokenCase(unittest.TestCase):
    def setUp(self):
        w = broken_world(self)
        self.e, self.proj, self.broken, self.fake, self.root = w.e, w.proj, w.broken, w.fake, w.root
        self.addCleanup(os.environ.__setitem__, "PATH", os.environ.get("PATH", ""))
        os.environ["PATH"] = w.path

    def sessions(self, folder, **kw):
        return self.e.run("sessions", folder, cwd=self.root, **kw)

    def calls_in(self, where):
        """The argvs the fake bale was run with in one directory."""
        if not self.fake.calls.is_file():
            return []
        want = os.path.realpath(where)
        return [argv for cwd, argv in map(json.loads, self.fake.calls.read_text().splitlines()) if cwd == want]


class TestOneUnreadableProjectIsALine(BrokenCase):
    def test_the_sessions_found_render_as_before_and_the_project_is_said_once(self):
        lines, uncertain = ob.render_folder_sessions(ob.Reader(), self.root,
                                                     self.root / "desk/2026-09-29-read-side/folder.md")
        out = "\n".join(lines) + "\n"
        for want in FOUND_LINES:
            self.assertIn(want, out)
        said = [l for l in lines if l.startswith(f"{BROKEN}:")]
        self.assertEqual(len(said), 1, lines)
        self.assertTrue(said[0].startswith(f"{BROKEN}: not read: bale status --json refused in "), said)
        self.assertIn("(exit 97)", said[0])
        # It is said after the sessions, before the folder's tally.
        self.assertGreater(lines.index(said[0]), max(i for i, l in enumerate(lines) if l.startswith("- ")))
        self.assertTrue(lines[lines.index(said[0]) + 1].startswith("recorded in this folder: 3 session id(s)"))
        self.assertNotIn("cannot read", out)

    def test_a_session_not_found_while_a_project_was_unread_is_uncertain_and_stops(self):
        lines, uncertain = ob.render_folder_sessions(ob.Reader(), self.root,
                                                     self.root / "desk/2026-09-29-read-side/folder.md")
        self.assertEqual(uncertain, 1)
        at = lines.index(f"- {MISS_SID}: never ran")
        self.assertEqual(lines[at + 1], f"    not found in the projects that could be read; {BROKEN} could not")
        self.assertIn(f"found in bale's records: 2; not found: {MISS_SID}", "\n".join(lines))
        # Through the verb: the reader's exit 3 is bin/office's stop, and
        # since 0.38.0 its line says it is a session not found.
        proc = self.sessions("read-side")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("a session was not found and some of this office's projects could not be read; the lines "
                      "above say which", proc.stderr)
        for want in FOUND_LINES:
            self.assertIn(want, proc.stdout)
        self.assertEqual(proc.stdout.count(f"{BROKEN}: not read:"), 1)

    def test_every_session_found_is_exit_0_with_the_line_still_said(self):
        proc = self.sessions("all-found", check=0)
        for want in FOUND_LINES:
            self.assertIn(want, proc.stdout)
        self.assertEqual(proc.stdout.count(f"{BROKEN}: not read: bale status --json refused in "), 1)
        self.assertIn("recorded in this folder: 2 session id(s); found in bale's records: 2\n", proc.stdout)
        self.assertNotIn("not found", proc.stdout)

    def test_a_missing_directory_is_the_same_one_line(self):
        shutil.rmtree(self.broken)
        proc = self.sessions("all-found", check=0)
        self.assertIn(f"{BROKEN}: not read: no such directory on this machine: ", proc.stdout)
        self.assertEqual(proc.stdout.count(f"{BROKEN}: not read:"), 1)

    def test_with_every_project_read_a_miss_is_certain_and_said_as_before(self):
        manifest = self.root / "floor-plan/manifest.toml"
        text = manifest.read_text()
        manifest.write_text(text[:text.index(f"[projects.{BROKEN}]")])
        lines, uncertain = ob.render_folder_sessions(ob.Reader(), self.root,
                                                     self.root / "desk/2026-09-29-read-side/folder.md")
        self.assertEqual(uncertain, 0)
        at = lines.index(f"- {MISS_SID}: never ran")
        self.assertEqual(lines[at + 1], "    not in the records of any project this office scopes")
        self.assertFalse([l for l in lines if ": not read: " in l], lines)

    def test_nothing_is_written_into_the_folder(self):
        page = self.root / "desk/2026-09-29-read-side/folder.md"
        before = page.read_bytes()
        self.sessions("read-side")
        self.assertEqual(page.read_bytes(), before)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")


class TestTheFoldersOwnProjectFirst(BrokenCase):
    def test_a_session_in_the_lanes_project_never_opens_another(self):
        proc = self.sessions("in-lane", check=0)
        for want in FOUND_LINES:
            self.assertIn(want, proc.stdout)
        self.assertNotIn(BROKEN, proc.stdout)
        self.assertEqual(self.calls_in(self.broken), [])
        # One status read for the folder, then one dossier per session.
        self.assertEqual(self.calls_in(self.proj), [["status", "--json"],
                                                    ["stats", "--sid", APPLIED[2], "--json"],
                                                    ["stats", "--sid", OPEN_WORKER, "--json"]])

    def test_a_lane_the_office_does_not_scope_searches_as_before(self):
        page = self.root / "desk/2026-09-29-in-lane/folder.md"
        page.write_text(page.read_text().replace("- lane: office-src: lib\n", "- lane: elsewhere: lib\n"))
        self.assertIsNone(ob.folder_lane(page, ob.office_projects(self.root)))
        proc = self.sessions("in-lane", check=0)
        self.assertEqual(proc.stdout.count(f"{BROKEN}: not read:"), 1)
        for want in FOUND_LINES:
            self.assertIn(want, proc.stdout)

    def test_the_lane_is_read_from_the_folder_page(self):
        projects = ob.office_projects(self.root)
        self.assertEqual(ob.folder_lane(self.root / "desk/2026-09-29-in-lane/folder.md", projects), "office-src")
        self.assertIsNone(ob.folder_lane(self.root / "desk/2026-09-29-all-found/folder.md", projects))


# --- locate itself, against a reader that holds plain records --------------------------------

class RecordsReader:
    """The three reads locate makes, from plain records: {directory: sids
    its records hold}. A directory in refuse makes bale refuse there; a
    (directory, sid) in garbled is a record that does not read; a
    directory in refuse_dossier refuses only the dossier. Every read is
    kept in calls, as (what, directory, sid)."""

    def __init__(self, records, refuse=(), garbled=(), refuse_dossier=()):
        # Keyed by real path: the floor plan resolves the paths it holds.
        real = os.path.realpath
        self.records = {real(k): v for k, v in records.items()}
        self.refuse = {real(d) for d in refuse}
        self.garbled = {(real(d), sid) for d, sid in garbled}
        self.refuse_dossier, self.calls = {real(d) for d in refuse_dossier}, []

    @staticmethod
    def hosted(cwd):
        return False

    def prefetch(self, cwd, requests):
        raise AssertionError("a local project is never prefetched")

    def known_sids(self, cwd):
        self.calls.append(("status", pathlib.Path(cwd), None))
        cwd = os.path.realpath(cwd)
        if cwd in self.refuse:
            raise ob.BaleError("refused", f"bale status --json refused in {cwd} (exit 128): git rev-parse HEAD")
        return sorted(self.records[cwd])

    def dossier(self, cwd, sid):
        self.calls.append(("dossier", pathlib.Path(cwd), sid))
        where = os.path.realpath(cwd)
        if where in self.refuse_dossier:
            raise ob.BaleError("refused", f"bale stats refused in {cwd} (exit 1)")
        if (where, sid) in self.garbled:
            raise ob.BaleError("output", f"bale has a record for {sid} in {cwd} but could not parse it")
        return {"sid": sid, "in": cwd} if sid in self.records[where] else None


S1, S2, S9 = "2026-09-01-one-001", "2026-09-01-two-002", "2026-09-01-none-009"


class TestLocate(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.dirs = {}
        for name in ("alpha", "beta", "gamma"):
            self.dirs[name] = make_project(self.e.tmp, name)
        self.projects = [{"name": n, "problem": None, "resolved": d} for n, d in self.dirs.items()]

    def locate(self, rd, sid, lane=None, statuses=None, unread=None):
        statuses = {} if statuses is None else statuses
        unread = {} if unread is None else unread
        p, d, errors = ob.locate(rd, self.projects, sid, statuses, unread, lane)
        return (p and p["name"]), d, errors, unread

    def test_the_lane_is_tried_first_and_alone_when_it_holds_the_sid(self):
        rd = RecordsReader({self.dirs["alpha"]: {S1}, self.dirs["beta"]: set(), self.dirs["gamma"]: {S1}})
        name, d, errors, unread = self.locate(rd, S1, lane="gamma")
        self.assertEqual((name, errors, unread), ("gamma", [], {}))
        self.assertEqual(rd.calls, [("status", self.dirs["gamma"], None), ("dossier", self.dirs["gamma"], S1)])

    def test_then_the_projects_whose_records_name_it_then_the_rest(self):
        rd = RecordsReader({self.dirs["alpha"]: set(), self.dirs["beta"]: set(), self.dirs["gamma"]: {S1}})
        name, *_ = self.locate(rd, S1, lane="alpha")
        self.assertEqual(name, "gamma")
        self.assertEqual([c for c in rd.calls if c[0] == "dossier"],
                         [("dossier", self.dirs["alpha"], S1), ("dossier", self.dirs["gamma"], S1)])

    def test_a_project_bale_refuses_in_is_kept_once_and_the_search_goes_on(self):
        rd = RecordsReader({self.dirs["alpha"]: set(), self.dirs["beta"]: {S1, S2}, self.dirs["gamma"]: set()},
                           refuse={self.dirs["alpha"]})
        statuses, unread = {}, {}
        for sid in (S1, S2):
            name, d, errors, _ = self.locate(rd, sid, statuses=statuses, unread=unread)
            self.assertEqual((name, errors), ("beta", []))
        self.assertEqual(list(unread), ["alpha"])
        self.assertIn("git rev-parse HEAD", unread["alpha"])
        # Asked once, then passed over.
        self.assertEqual([c for c in rd.calls if c[1] == self.dirs["alpha"]], [("status", self.dirs["alpha"], None)])
        name, d, errors, _ = self.locate(rd, S9, statuses=statuses, unread=unread)
        self.assertEqual((name, d, errors), (None, None, []))

    def test_a_dossier_bale_refuses_passes_the_project_over_too(self):
        rd = RecordsReader({self.dirs["alpha"]: set(), self.dirs["beta"]: {S1}, self.dirs["gamma"]: set()},
                           refuse_dossier={self.dirs["alpha"]})
        unread = {}
        name, d, errors, _ = self.locate(rd, S1, unread=unread)
        self.assertEqual((name, errors), ("beta", []))
        self.assertEqual(rd.calls.count(("dossier", self.dirs["alpha"], S1)), 0)  # beta names s1: tried first
        name, d, errors, _ = self.locate(rd, S2, unread=unread)
        self.assertIsNone(name)
        self.assertEqual(list(unread), ["alpha"])

    def test_a_record_that_does_not_read_is_that_sessions_alone(self):
        rd = RecordsReader({self.dirs["alpha"]: {S1, S2}, self.dirs["beta"]: set(), self.dirs["gamma"]: set()},
                           garbled={(self.dirs["alpha"], S1)})
        statuses, unread = {}, {}
        name, d, errors, _ = self.locate(rd, S1, statuses=statuses, unread=unread)
        self.assertIsNone(name)
        self.assertEqual([(p["name"], e.kind) for p, e in errors], [("alpha", "output")])
        self.assertEqual(unread, {})
        name, d, errors, _ = self.locate(rd, S2, statuses=statuses, unread=unread)
        self.assertEqual((name, errors), ("alpha", []))

    def test_a_record_that_does_not_read_is_said_under_its_session_and_is_uncertain(self):
        root = self.e.init()
        for name, d in self.dirs.items():
            h.add_project(root / "floor-plan/manifest.toml", name, str(d))
        page = folder_page(root / "desk/2026-09-29-x/folder.md", "x", None, [(S1, ""), (S2, "")])
        # The reader's own reads: bale is found, so render reaches locate.
        rd = RecordsReader({self.dirs["alpha"]: {S1}, self.dirs["beta"]: set(), self.dirs["gamma"]: set()},
                           garbled={(self.dirs["alpha"], S1)})
        rd.bale = lambda: "bale"
        lines, uncertain = ob.render_folder_sessions(rd, root, page)
        self.assertEqual(lines[:3], [f"- {S1}", f"    cannot read: bale has a record for {S1} in {self.dirs['alpha']} "
                                             "but could not parse it",
                                     "    not found in the projects that could be read; alpha could not"])
        self.assertEqual(lines[3:5], [f"- {S2}", "    not in the records of any project this office scopes"])
        self.assertEqual(uncertain, 1)


# --- a host that does not answer --------------------------------------------------------------

class TestAHostThatDoesNotAnswer(HostedCase):
    def setUp(self):
        super().setUp()
        self.set_host(DOWN, connect="start the VPN client")

    def test_it_is_one_line_and_the_project_here_answers(self):
        proc = self.run_office("sessions", "1", check=0)
        self.assertEqual(proc.stdout.count("far: not read: "), 1, proc.stdout)
        self.assertIn(f"far: not read: {DOWN} does not answer (", proc.stdout)
        self.assertIn("    here: applied; opened", proc.stdout)
        self.assertIn("    here: open; opened", proc.stdout)
        # The host is tried once, and nothing more is asked of it.
        self.assertEqual([c[0] for c in self.ssh.connections()], [DOWN])

    def test_with_the_lane_on_this_machine_the_host_is_never_tried(self):
        page = self.root / self.folder / "folder.md"
        text = page.read_text()
        at = text.index("- queued: ")
        at = text.index("\n", at) + 1
        page.write_text(text[:at] + "- lane: here: src\n" + text[at:])
        proc = self.run_office("sessions", "1", check=0)
        self.assertNotIn("far", proc.stdout)
        self.assertIn("    here: applied; opened", proc.stdout)
        self.assertEqual(self.ssh.connections(), [])


if __name__ == "__main__":
    unittest.main()
