"""Tests for office-src 0.52.0: a bailout's fresh session goes out from the
office, and a job's session line follows its session. One class or two per
item of the brief (2026-11-07-start-handoff-001):

1. office start FOLDER --handoff [RESPONSE]: the surface bale handoff is
   read through, the office's opener, the Next line a bailout's landing
   names, its refusals before anything runs, and the whole loop through
   the office's own commands (start, a bailout landed, the Next line run,
   the fresh session in the tray with the office's opener, its response
   landed), here and on a host.
2. A merge or undo job's session line: cleared when office withdraw closes
   its session or a bailout ends it, taken by the fresh session when office
   start N --handoff hands that bailout off; the merge line's `sends another
   in its place`.
3. The undo job's close checks its work: a path whose workbench version
   still holds bale's change keeps the job open.
4. The release's record.

bale is never needed: tests/fakes/land_bale.py learned a bailout apply and
bale handoff, built from bale 0.4.56's cmd_handoff as the sitting's probes
read it (no real bailout existed to capture). The worlds are the suite's
own: tests/test_land.py's LandCase, tests/test_return_trip.py's host, and
tests/test_undo_bale.py's UndoCase. Run with the rest of the suite:

    tests/run.sh test_handoff
"""

import io
import json
import os
import pathlib
import re
import shlex
import sys
import tarfile
import tempfile
import tomllib
import unittest
import unittest.mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, h  # noqa: E402
from test_start import opener_from, tar_names  # noqa: E402
from test_land import FakeLandBale, LandCase, response_tarball  # noqa: E402
from test_return_trip import ReturnTripCase  # noqa: E402
from test_project_on_host import HOST  # noqa: E402
from test_undo_bale import UndoCase, flat  # noqa: E402
from test_deliver_merges import DAY  # noqa: E402
from test_audience_line import git  # noqa: E402

import office_bale as ob  # noqa: E402
import office_deliver as odl  # noqa: E402

CONSUMPTION = REPO / "share" / "bale-consumption.toml"


def request_tarball(directory, sid, goal="Fix the login redirect", handoff=b"# Handoff\n", packed="2026-11-07T01:02:03+00:00"):
    """A request tarball shaped as bale handoff writes one: its manifest,
    and handoff.md first in its context."""
    path = pathlib.Path(directory) / f"request-{sid}.tar.gz"
    members = {"request-001/manifest.json": json.dumps({"session_id": sid, "goal": goal,
                                                        "provenance": {"packed_at": packed}}).encode()}
    if handoff is not None:
        members["request-001/context/handoff.md"] = handoff
    with tarfile.open(path, "w:gz") as t:
        for rel, data in members.items():
            info = tarfile.TarInfo(rel)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return path


def next_line(out):
    """The office's Next line: the last one a command printed."""
    return re.findall(r"^Next: (.+)$", out, re.M)[-1]


def handed_off_sid(out):
    return re.search(r"^Handed off \S+: packed (\S+) for ", out, re.M).group(1)


# --- 1. the surface, the line and the opener, as units ----------------------------------------------

class TestTheSurface(unittest.TestCase):
    def test_handoff_is_declared_with_its_contract_and_its_two_rows(self):
        spec = tomllib.loads(CONSUMPTION.read_text())["surfaces"]["handoff"]
        self.assertEqual(spec["argv"], ["handoff", "{tarball}"])
        self.assertEqual(spec["format"], "text")
        self.assertEqual(spec["contract"], "cmd_handoff in bin/bale, bale 0.4.56, read by the probes handoff-ground "
                                           "and handoff-tail of sitting 2026-11-06-office-src-plan-sitting-001")
        self.assertEqual((spec["sid_line"], spec["tarball_line"]), ("  session id:     ", "  tarball:        "))
        # The same row shape bale's open prints (format_summary_block).
        self.assertEqual(spec["tarball_line"], tomllib.loads(CONSUMPTION.read_text())["surfaces"]["open"]["tarball_line"])
        self.assertEqual(ob.Consumption().argv("handoff", tarball="r.tar.gz"), ["handoff", "r.tar.gz"])

    def test_the_rows_are_read_by_their_starts(self):
        spec = ob.Consumption().surface("handoff")
        lines = ["  reading-plan file(s) packed into context:", "    src/a.py", "",
                 "  session id:     2026-11-07-fix-login-002", "  tarball:        /r/.bale/outbox/request-x.tar.gz",
                 "  inherited:      goal", "Send the tarball to the agent."]
        self.assertEqual(ob.report_rows(lines, spec, ("sid", "tarball")),
                         {"sid": "2026-11-07-fix-login-002", "tarball": "/r/.bale/outbox/request-x.tar.gz"})
        self.assertEqual(ob.report_rows(["nothing"], spec, ("sid",)), {"sid": None})

    def test_bales_refusals_get_the_office_line_that_answers_them(self):
        said = ob.handoff_refusal_lines("[bale] error: bale handoff refuses a detached HEAD", "3", "S")
        self.assertIn("office start 3 --handoff RESPONSE --branch NAME", said[0])
        said = ob.handoff_refusal_lines("cannot inherit goal: request manifest not found at /r", "3", "S")
        self.assertIn(".bale/sessions/S/", said[0])
        self.assertIn("office start 3 sends a fresh session", said[0])
        said = ob.handoff_refusal_lines("forecast overlaps open session X (src ~ src)", "3", "S")
        self.assertIn("office withdraw SID", said[0])
        self.assertEqual(ob.handoff_refusal_lines("something else", "3", "S"), [])


class TestTheLine(unittest.TestCase):
    PLAN = {"sid": "2026-11-07-fix-login-001", "repo": "/w/alpha", "tarball": "response-x.tar.gz",
            "folders": ["desk/fix-login"], "folder_keys": {"desk/fix-login": "3"}, "label": "alpha"}

    def test_a_bailouts_next_line_is_office_start_handoff(self):
        words, nxt = ob.outcome_words(self.PLAN, "bailout")
        self.assertIn("Bailed: the worker handed 2026-11-07-fix-login-001 off; nothing landed", words)
        self.assertEqual(nxt, "office start 3 --handoff response-x.tar.gz (bale handoff runs in /w/alpha; it sends "
                              "the fresh session the handoff asks for)")
        self.assertEqual(ob.office_words(["Next: bale handoff 'r'"], self.PLAN), ["bale handoff -> " + nxt])
        # A path that needs quoting is quoted as the shell reads it.
        odd = dict(self.PLAN, tarball="/d/response-x (1).tar.gz")
        self.assertIn("--handoff '/d/response-x (1).tar.gz' (", ob.handoff_line(odd))
        hosted = dict(self.PLAN, place={"path": "/srv/alpha", "host": "box"})
        self.assertIn("(bale handoff runs in /srv/alpha, through box's shell; it sends", ob.handoff_line(hosted))
        for line in (nxt, words):
            self.assertNotIn("no office line", line)


class TestTheOpener(unittest.TestCase):
    def test_it_is_bales_shape_with_the_handoff_first_and_the_constraint(self):
        with tempfile.TemporaryDirectory() as d:
            req = request_tarball(d, "2026-11-07-fix-login-002")
            lines = ob.handoff_opener(req, "2026-11-07-fix-login-001", "desk/2026-11-07-fix-login", True,
                                      "context-home.tar.gz", ob.PROJECT_CONSTRAINT)
            bare = ob.handoff_opener(request_tarball(d, "2026-11-07-x-002", handoff=None, packed=None),
                                     "2026-11-07-x-001", "desk/x", False, "context-home.tar.gz")
        self.assertEqual(lines[:3], ['I\'m using "bale", a CLI that packaged the attached request tarball.',
                                     "This message opens bale session 2026-11-07-fix-login-002.",
                                     "Goal, verbatim from the request manifest: Fix the login redirect"])
        text = "\n".join(lines)
        self.assertIn("Read manifest.json first, then AGENT.md, then context/handoff.md,", text)
        self.assertIn("the handoff the worker of 2026-11-07-fix-login-001 wrote when it bailed out", text)
        self.assertIn("The folder's brief, desk/2026-11-07-fix-login/brief.md, rides in context-home.tar.gz", text)
        self.assertIn("The original pack's constraint, which bale's handoff does not carry over: Office context "
                      "informs this session but never lands in this project.", text)
        self.assertIn("Packed at 2026-11-07T01:02:03+00:00 (UTC).", text)
        self.assertIn("what I need back is one response tarball carrying the finished work.", text)
        self.assertEqual(lines[-1], ob.HANDOFF_OPENER_MARK)
        self.assertIn("the office's", lines[-1])
        # No brief of the folder's, no constraint, no stamp: each line left
        # out, never invented; handoff.md named by its own name.
        text = "\n".join(bare)
        self.assertIn("then AGENT.md, then handoff.md,", text)
        self.assertIn("the handoff carries no README brief of its own", text)
        self.assertNotIn("constraint", text)
        self.assertNotIn("Packed at", text)


# --- 1. the loop through the office ---------------------------------------------------------------

class TestTheHandoffThroughTheOffice(LandCase):
    """start, a bailout landed through office land with its Next line naming
    office start N --handoff, that line run, the fresh session recorded and
    in the tray with the office's opener, and its response landed."""

    def bailed(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        response_tarball(self.downloads, sid, kind="bailout")
        proc = self.run_office("land", sid)
        return sid, proc

    def test_start_bail_land_handoff_land(self):
        sid, proc = self.bailed()
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(f"Bailed: the worker handed {sid} off; nothing landed, and bale closed the session.", proc.stdout)
        nxt = next_line(proc.stdout)
        self.assertTrue(nxt.startswith(f"office start 1 --handoff response-{sid}.tar.gz (bale handoff runs in "), nxt)
        self.assertTrue(nxt.endswith("; it sends the fresh session the handoff asks for)"), nxt)
        self.assertIn(f"  bale handoff -> {nxt}", proc.stdout)
        self.assertNotIn("no office line", proc.stdout)
        self.assertFalse(self.fake.is_open(self.proj, sid))
        self.assertEqual(self.fake.land_state()["attempts"][sid][-1]["outcome"], "bailout")
        # The Next line, as typed (its words before the parenthesis); the
        # response is found in the downloads bale searches here, by name.
        self.downloads_known()
        before = self.subjects(1)
        proc = self.run_office(*shlex.split(nxt.split(" (", 1)[0])[1:])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        fresh = handed_off_sid(proc.stdout)
        self.assertNotEqual(fresh, sid)
        self.assertEqual(fresh.rsplit("-", 1)[0].split("-", 3)[3], sid.rsplit("-", 1)[0].split("-", 3)[3],
                         "bale keeps the slug")
        (cwd, argv, tty), = self.fake.calls_of("handoff")
        self.assertEqual((cwd, argv[0], pathlib.Path(argv[1]).name, tty),
                         (os.path.realpath(self.proj), "handoff", f"response-{sid}.tar.gz", False))
        self.assertTrue(self.fake.is_open(self.proj, fresh))
        # The tray: bale's request (handoff.md in it), the office's context
        # and the doctrine, as a pack's.
        tray = pathlib.Path(re.search(r"^Out tray: (.+)$", proc.stdout, re.M).group(1))
        names = sorted(p.name for p in tray.iterdir())
        self.assertIn(f"request-{fresh}.tar.gz", names)
        self.assertIn("request-001/context/handoff.md", tar_names(tray / f"request-{fresh}.tar.gz"))
        self.assertTrue(any(n.startswith("context-home") for n in names), names)
        self.assertIn(f"request-{fresh}.tar.gz: the request (alpha session, from the handoff of {sid})", proc.stdout)
        # The opener: the office's, in bale's shape.
        opener = opener_from(proc.stdout)
        self.assertEqual(opener[1], f"This message opens bale session {fresh}.")
        self.assertEqual(opener[2], "Goal, verbatim from the request manifest: Fix the login redirect")
        self.assertIn("then AGENT.md, then context/handoff.md,", "\n".join(opener))
        self.assertIn(ob.PROJECT_CONSTRAINT, "\n".join(opener))
        self.assertEqual(opener[-1], ob.HANDOFF_OPENER_MARK)
        self.assertIn("the opener below is the office's: bale handoff prints none", proc.stderr)
        self.assertEqual((tray.parent / (tray.name + ".opener.txt")).read_text().splitlines(), opener)
        self.assertIn(f"When the response comes back: office land {fresh}", proc.stdout)
        # The folder: the session recorded, the handed-off line, one commit.
        md = self.folder_md()
        self.assertIn(f"- {fresh}: from the handoff of {sid}\n", md)
        self.assertRegex(md, rf"- \d{{4}}-\d{{2}}-\d{{2}} handed-off: {fresh} from the handoff of {sid}\n")
        self.assertEqual(self.subjects(1), [f"office start: {fresh} from the handoff of {sid} in {self.name}"])
        self.assertNotEqual(self.subjects(1), before)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # Its response lands as any session's.
        response_tarball(self.downloads, fresh, {"src/a.py": "fixed\n"})
        proc = self.run_office("land", fresh)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"Landed: {fresh} is applied in alpha", proc.stdout)
        self.assertEqual((self.proj / "src/a.py").read_text(), "fixed\n")

    def test_with_no_response_named_the_newest_sessions_is_taken(self):
        sid, _ = self.bailed()
        self.downloads_known()
        proc = self.run_office("start", "1", "--handoff")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"the bailout is {self.downloads / f'response-{sid}.tar.gz'}, the response of {sid}, the newest "
                      "session", proc.stderr)
        self.assertEqual(self.fake.calls_of("handoff")[0][1][1], str(self.downloads / f"response-{sid}.tar.gz"))

    def test_a_name_found_nowhere_here_is_left_to_bales_own_search(self):
        sid, _ = self.bailed()
        proc = self.run_office("start", "1", "--handoff", f"response-{sid}.tar.gz")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"bale's own search finds it in alpha", proc.stderr)
        self.assertEqual(self.fake.calls_of("handoff")[0][1], ["handoff", f"response-{sid}.tar.gz"])

    def test_branch_is_checked_out_before_the_handoff(self):
        sid, _ = self.bailed()
        self.e.git(self.proj, "branch", "side")
        proc = self.run_office("start", "1", "--handoff", str(self.downloads / f"response-{sid}.tar.gz"),
                               "--branch", "side")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.e.git(self.proj, "symbolic-ref", "--short", "HEAD").strip(), "side")


class TestWhatTheHandoffRefuses(LandCase):
    def setUp(self):
        super().setUp()
        self.downloads_known()

    def nothing_written(self, proc, head, code=1):
        self.assertEqual(proc.returncode, code, proc.stdout + proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertEqual(self.fake.calls_of("handoff"), [])

    def test_the_flags_that_make_no_sense_beside_it_by_name(self):
        head = self.e.git(self.root, "rev-parse", "HEAD")
        for extra, named in ((["--merge"], "--merge"), (["--undo-bale"], "--undo-bale"), (["--goal", "g"], "--goal"),
                             (["--brief", "b.md"], "--brief"), (["--write", "src"], "--write"), (["--sort"], "--sort"),
                             (["--prep"], "--prep"), (["--planner"], "--planner"), (["--in-office"], "--in-office"),
                             (["--bundle", "x"], "--bundle"), (["--drop", "x"], "--drop"), (["--carry", "1"], "--carry")):
            proc = self.run_office("start", "1", "--handoff", *extra)
            self.assertEqual(proc.returncode, 1, extra)
            self.assertIn(f"so it takes no {named}", proc.stderr, extra)
            self.assertIn("nothing ran", proc.stderr)
        proc = self.run_office("start", "new", "--handoff")
        self.assertIn("so it takes no new", proc.stderr)
        proc = self.run_office("start", "--handoff")
        self.assertIn("office start FOLDER --handoff [RESPONSE]", proc.stderr)
        self.nothing_written(proc, head)

    def test_a_response_that_is_not_a_bailout_or_not_the_folders(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        head = self.e.git(self.root, "rev-parse", "HEAD")
        normal = response_tarball(self.downloads, sid, {"src/a.py": "x\n"})
        proc = self.run_office("start", "1", "--handoff", str(normal))
        self.assertIn(f"response-{sid}.tar.gz is a normal response for {sid}, not a bailout", proc.stderr)
        self.assertIn(f"office land {sid} lands it", proc.stderr)
        self.nothing_written(proc, head)
        other = response_tarball(self.e.tmp / "elsewhere", "2026-01-02-other-001", kind="bailout")
        proc = self.run_office("start", "1", "--handoff", str(other))
        self.assertIn(f"answers 2026-01-02-other-001, which desk/{self.name} does not record (it records {sid})",
                      proc.stderr)
        self.nothing_written(proc, head)
        bare = response_tarball(self.e.tmp / "elsewhere", sid, kind="bailout", handoff=None, name="no-handoff.tar.gz")
        proc = self.run_office("start", "1", "--handoff", str(bare))
        self.assertIn("carries no handoff.md", proc.stderr)
        self.nothing_written(proc, head)

    def test_a_bailout_not_landed_yet_and_one_not_saved(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", "1", "--handoff")
        self.assertIn(f"no response-{sid}.tar.gz (the response of {sid}, the newest session desk/{self.name} records) "
                      "in ", proc.stderr)
        self.assertIn(str(self.downloads), proc.stderr)
        self.nothing_written(proc, head)
        response_tarball(self.downloads, sid, kind="bailout")
        proc = self.run_office("start", "1", "--handoff")
        self.assertIn(f"{sid} is still open in ", proc.stderr)
        self.assertIn(f"office land {sid} lands its bailout first", proc.stderr)
        self.nothing_written(proc, head)

    def test_a_folder_in_the_filing_cabinet(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, kind="bailout")
        self.run_office("land", sid, check=1)
        self.run_office("close", self.name, "--retired", "bailed", check=0)
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", self.name, "--handoff")
        self.assertIn(f"filing-cabinet/{self.name} is in the filing cabinet: office reopen {self.name} brings it back",
                      proc.stderr)
        self.nothing_written(proc, head)

    def test_bales_refusal_is_said_in_its_words_and_nothing_is_written(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        response_tarball(self.downloads, sid, kind="bailout")
        self.run_office("land", sid, check=1)
        head = self.e.git(self.root, "rev-parse", "HEAD")
        trays = sorted((self.e.home / "out-tray").iterdir())
        # A detached HEAD in the clone: bale's words, and the office's line.
        self.e.git(self.proj, "checkout", "-q", "--detach")
        proc = self.run_office("start", "1", "--handoff")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("bale handoff refuses a detached HEAD", proc.stderr)
        self.assertIn("office start 1 --handoff RESPONSE --branch NAME checks a branch out", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertEqual(sorted((self.e.home / "out-tray").iterdir()), trays)
        self.e.git(self.proj, "checkout", "-q", "-")
        # bale's record of the bailed session gone.
        proc = self.run_office("start", "1", "--handoff", extra={"FAKE_BALE_RECORD_GONE": sid})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("cannot inherit goal: request manifest not found", proc.stderr)
        self.assertIn(f"office start 1 sends a fresh session on the folder's goal instead", flat(proc.stderr))
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        self.assertNotIn("handed-off", self.folder_md())

    def test_a_sitting_is_not_handed_off(self):
        sid = self.start("fix-login", "--in-office", "--read-only", "--goal", "Plan it")
        self.run_office("land", sid, check=0)
        response_tarball(self.downloads, sid, kind="bailout")
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", "1", "--handoff")
        self.assertIn(f"{sid} was a read-only sitting in ", proc.stderr)
        self.assertIn("the office sends another sitting itself (office start --planner)", proc.stderr)
        self.nothing_written(proc, head)


class TestTheHandoffOnAHost(ReturnTripCase):
    def test_bale_handoff_runs_there_and_the_request_comes_back(self):
        self.set_downloads()
        sid = self.start(self.name, "--on", "far", "--goal", "Fix it there", "--write", "src")
        response_tarball(self.downloads, sid, kind="bailout")
        proc = self.run_office("land", sid)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        nxt = next_line(proc.stdout)
        self.assertIn(f"--handoff {self.downloads / f'response-{sid}.tar.gz'} (bale handoff runs in {self.proj}, "
                      f"through {HOST}'s shell; it sends", nxt)
        proc = self.run_office(*shlex.split(nxt.split(" (", 1)[0])[1:])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        fresh = handed_off_sid(proc.stdout)
        # bale handoff ran in far's repo on the host, on the copy carried
        # into the office's temporary directory there, which is gone.
        (cwd, argv, tty), = self.fake.calls_of("handoff")
        self.assertEqual(cwd, os.path.realpath(self.proj))
        self.assertTrue(argv[1].startswith(str(self.ssh.host_tmp(HOST))), argv)
        self.assertFalse(tty)
        self.assertEqual(self.ssh.left_on(HOST), [])
        self.assertTrue(all(c[0] == HOST for c in self.ssh.connections()))
        tray = self.tray_of(proc.stdout)
        outbox = self.proj / ".bale" / "outbox" / f"request-{fresh}.tar.gz"
        self.assertEqual((tray / f"request-{fresh}.tar.gz").read_bytes(), outbox.read_bytes())
        self.assertIn(f"far session, packed on {HOST} and carried back, from the handoff of {sid}", proc.stdout)
        self.assertEqual(opener_from(proc.stdout)[-1], ob.HANDOFF_OPENER_MARK)
        self.assertIn(f"- {fresh}: from the handoff of {sid}", (self.root / self.folder / "folder.md").read_text())
        # Its response lands there.
        response_tarball(self.downloads, fresh, {"src/a.py": "fixed\n"})
        proc = self.run_office("land", fresh)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"Landed: {fresh} is applied in far", proc.stdout)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_a_bailout_named_by_a_name_not_here_is_refused_for_a_host(self):
        self.set_downloads()
        sid = self.start(self.name, "--on", "far", "--goal", "Fix it there", "--write", "src")
        path = response_tarball(self.downloads, sid, kind="bailout")
        self.run_office("land", sid, check=1)
        path.rename(self.e.tmp / path.name)
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", self.name, "--handoff", path.name)
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"a bailout for a project on {HOST} is carried there from this machine", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        self.assertEqual(self.fake.calls_of("handoff"), [])


# --- 2. a job's session line follows its session --------------------------------------------------

class TestTheJobLineAsUnits(unittest.TestCase):
    def folder(self, d, kind):
        f = pathlib.Path(d) / "desk" / "x"
        (f / kind).mkdir(parents=True)
        (f / "folder.md").write_text("# X\n\n- number: 7\n\n## History\n")
        if kind == "merge":
            job = {"project": "proj", "audience": "origin", "kind": "base", "branch": "main", "tip": "a" * 40,
                   "workbench": "b" * 40, "parted": "c" * 40, "day": DAY, "files": ["src/a.py"], "session": "S1"}
            odl.merge_page_path(f).write_text(odl.merge_page_text(job))
        else:
            job = {"project": "proj", "commit": "a" * 40, "subject": "bale: x", "workbench": "b" * 40,
                   "parent": "c" * 40, "day": DAY, "files": [".gitignore"], "session": "S1"}
            odl.undo_page_path(f).write_text(odl.undo_page_text(job))
        for args in (["init", "-q"], ["add", "-A"], ["-c", "user.name=T", "-c", "user.email=t@x", "commit", "-qm", "j"]):
            git(d, *args)
        return f

    def test_withdrawn_bailed_and_handed_off_for_both_kinds(self):
        for kind, flag in (("merge", "--merge"), ("undo", "--undo-bale")):
            with tempfile.TemporaryDirectory() as d:
                f = self.folder(d, kind)
                env = {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "T",
                       "GIT_COMMITTER_EMAIL": "t@x"}
                with unittest.mock.patch.dict(os.environ, env):
                    self.assertEqual(odl.job_session_ended(d, "desk/x", "OTHER", "bailed"), [])
                    lines = odl.job_session_ended(d, "desk/x", "S1", "bailed")
                    self.assertIn(f"no longer names S1, which bailed out of the {kind} job: office start 7 --handoff "
                                  f"hands it off, the fresh session taking the job's line, or office start 7 {flag} "
                                  "sends another in its place", lines[0])
                    job = odl.folder_job(f)
                    self.assertEqual((job["session"], job["bailed"]), (None, "S1"))
                    self.assertIsNone(odl.job_handed_off(d, "desk/x", "OTHER", "S2"))
                    line = odl.job_handed_off(d, "desk/x", "S1", "S2")
                    self.assertIn("names S2 as the " + kind + " session in place of S1; office land S2", line)
                    job = odl.folder_job(f)
                    self.assertEqual((job["session"], job.get("bailed")), ("S2", None))
                    lines = odl.job_session_ended(d, "desk/x", "S2", "withdrawn")
                    self.assertIn(f"no longer names S2, which office withdraw closed: office start 7 {flag} sends "
                                  "another in its place", lines[0])
                    job = odl.folder_job(f)
                    self.assertEqual((job["session"], job.get("bailed")), (None, None))
                    self.assertEqual(git(d, "status", "--porcelain"), "")
                    self.assertIn("no longer the " + kind + " session in x",
                                  git(d, "log", "-1", "--format=%s"))

    def test_the_merge_line_sends_another_in_its_place(self):
        with tempfile.TemporaryDirectory() as d:
            self.folder(d, "merge")
            lines = odl.merge_job_lines(d, "desk/x", "x", "proj", d, "base", "origin", "main", "a" * 40, "b" * 40,
                                        ["src/a.py"], day=DAY)
        self.assertEqual(len(lines), 1)
        self.assertIn("the merge session S1 was sent for this conflict", lines[0])
        self.assertIn("(office start x --merge sends another in its place, if it was withdrawn)", lines[0])


class TestTheJobLineThroughTheOffice(UndoCase):
    """The undo job's session withdrawn, then one bailed and handed off, the
    handoff's landing closing the job: through the office's own commands."""

    def setUp(self):
        super().setUp()
        (self.e.desktop / "bale").unlink()
        self.fake = FakeLandBale(self.e.tmp)
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir()
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.e.env["FAKE_BALE_SEARCH"] = str(self.downloads)
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'downloads = ["{self.downloads}"]\n')

    def send(self):
        proc = self.run_office("start", self.name, "--undo-bale", "--no-refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)

    def test_withdraw_clears_bailout_keeps_handoff_takes_land_closes(self):
        sha = self.refusing_commit()
        self.run_office("deliver", self.name, "--yes")
        n = re.search(r"^- number: (\d+)$", self.folder_md(), re.M).group(1)
        first = self.send()
        proc = self.run_office("withdraw", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"{self.folder}/undo/undo.md no longer names {first}, which office withdraw closed: office start "
                      f"{n} --undo-bale sends another in its place", flat(proc.stderr))
        self.assertIsNone(self.undo_job()["session"])
        self.office_clean()
        second = self.send()
        self.assertEqual(self.undo_job()["session"], second)
        response_tarball(self.downloads, second, kind="bailout")
        proc = self.run_office("land", second)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(f"no longer names {second}, which bailed out of the undo job: office start {n} --handoff hands "
                      "it off", flat(proc.stderr))
        job = self.undo_job()
        self.assertEqual((job["session"], job["bailed"]), (None, second))
        self.office_clean()
        proc = self.run_office("start", n, "--handoff", "--no-refresh")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        fresh = handed_off_sid(proc.stdout)
        self.assertIn(f"names {fresh} as the undo session in place of {second}; office land {fresh} closes the job",
                      flat(proc.stderr))
        self.assertEqual(self.undo_job()["session"], fresh)
        self.office_clean()
        response_tarball(self.downloads, fresh, {".gitignore": "*.pyc\n*.log\n"})
        proc = self.run_office("land", fresh)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"closed {self.folder}'s undo job: the undo session {fresh} took bale's own commit {sha[:7]}",
                      proc.stderr)
        self.assertFalse(self.undo_dir().exists())


# --- 3. the undo's close checks its work ------------------------------------------------------------

class TestTheCloseRule(unittest.TestCase):
    def materials(self, d, before, bales):
        m = pathlib.Path(d) / "undo"
        for side, text in (("before", before), ("bale", bales)):
            if text is not None:
                (m / side).mkdir(parents=True, exist_ok=True)
                (m / side / "f").write_text(text)
        return m

    def test_put_and_took_are_the_lines_that_tell_bales_change(self):
        with tempfile.TemporaryDirectory() as d:
            m = self.materials(d, "*.pyc\n\n}\n", ".bale/\n\n}\n")
            self.assertEqual(odl.bale_change(m, "f"), ([".bale/"], ["*.pyc"]))
        with tempfile.TemporaryDirectory() as d:
            m = self.materials(d, None, "new\n")
            self.assertEqual(odl.bale_change(m, "f"), (["new"], []))
        with tempfile.TemporaryDirectory() as d:
            m = self.materials(d, "a\nb\n", "b\na\n\n")
            self.assertEqual(odl.bale_change(m, "f"), ([], []))

    def test_what_still_holds(self):
        put, took = [".bale/"], ["*.pyc"]
        self.assertTrue(odl.still_holds(put, took, [".bale/", "*.log"]))      # nothing of bale's undone
        self.assertFalse(odl.still_holds(put, took, ["*.pyc", "*.log"]))      # undone
        self.assertFalse(odl.still_holds(put, took, [".bale/", "*.pyc"]))     # bale's line kept, the line back
        self.assertFalse(odl.still_holds(put, took, ["*.log"]))               # bale's line gone
        self.assertTrue(odl.still_holds([], ["x"], None))                     # bale deleted it; still gone
        self.assertFalse(odl.still_holds([], [], ["anything"]))               # nothing to tell it by


class TestTheCloseKeepsTheJobOpen(UndoCase):
    def setUp(self):
        super().setUp()
        (self.e.desktop / "bale").unlink()
        self.fake = FakeLandBale(self.e.tmp)
        self.downloads = self.e.tmp / "Downloads"
        self.downloads.mkdir()
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.e.env["FAKE_BALE_SEARCH"] = str(self.downloads)

    def test_a_session_that_left_bales_change_keeps_the_job_and_says_the_path(self):
        sha = self.refusing_commit()
        self.run_office("deliver", self.name, "--yes")
        n = re.search(r"^- number: (\d+)$", self.folder_md(), re.M).group(1)
        proc = self.run_office("start", self.name, "--undo-bale", "--no-refresh")
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        # The session ships .gitignore with bale's line kept and *.pyc not back.
        response_tarball(self.downloads, sid, {".gitignore": ".bale/\n*.log\n*.tmp\n"})
        proc = self.run_office("land", sid, "--response", str(self.downloads / f"response-{sid}.tar.gz"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        err = flat(proc.stderr)
        self.assertIn(f"the undo session {sid} landed, and the workbench still holds bale's own commit {sha[:7]}'s "
                      f"change in 1 of the job's file(s), so {self.folder}'s undo job stays open and nothing was "
                      "removed:", err)
        self.assertIn(".gitignore: bale's line '.bale/' is still there", err)
        self.assertIn(f"office start {n} --undo-bale sends the undo session again", err)
        self.assertRegex(proc.stdout, rf"Next: office start {n} --undo-bale  \(the undo session landed and the "
                                      r"workbench still holds bale's change")
        # Nothing removed; the session line cleared and kept as earlier.
        self.assertTrue((self.undo_dir() / "bale.diff").is_file())
        job = self.undo_job()
        self.assertEqual((job["session"], job["earlier"]), (None, sid))
        self.assertNotIn(" undone: ", self.folder_md())
        self.office_clean()
        # deliver waits for it and names the same line.
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"office start {self.name} --undo-bale", flat(proc.stderr))

    def test_a_session_that_took_it_out_closes(self):
        self.refusing_commit()
        self.run_office("deliver", self.name, "--yes")
        proc = self.run_office("start", self.name, "--undo-bale", "--no-refresh")
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        # bale's line kept on purpose, *.pyc back: bale's change is not all there.
        response_tarball(self.downloads, sid, {".gitignore": ".bale/\n*.pyc\n*.log\n"})
        proc = self.run_office("land", sid, "--response", str(self.downloads / f"response-{sid}.tar.gz"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"closed {self.folder}'s undo job", proc.stderr)
        self.assertFalse(self.undo_dir().exists())


# --- 4. the record ----------------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_release_the_readme_the_doctrine_and_the_usage_say_it(self):
        version = tuple(int(x) for x in (REPO / "VERSION").read_text().strip().split("."))
        self.assertGreaterEqual(version, (0, 52, 0))
        entry = (REPO / "RELEASES.md").read_text().split("## 0.52.0", 1)[1].split("\n## ", 1)[0]
        for words in ("--handoff", "handed-off", "Additive", "test_handoff.py", "[surfaces.handoff]",
                      "sends another in its place", "still holds"):
            self.assertIn(words, entry)
        readme = flat((REPO / "README.md").read_text())
        doctrine = flat((REPO / "doctrine" / "OFFICE.md").read_text())
        usage = (REPO / "bin" / "office").read_text()
        for text in (readme, doctrine, usage):
            self.assertIn("--handoff", text)
        for text in (readme, doctrine, flat(usage), flat((REPO / "templates" / "sitting-brief.md").read_text()),
                     flat((REPO / "lib" / "office_bale.py").read_text())):
            self.assertNotIn("no office line yet", text)
            self.assertNotIn("until office start --handoff exists", text)
        self.assertIn("office start 14 --handoff", usage)
        self.assertIn("handed-off", h.HISTORY_VERBS)
        self.assertNotIn("handed-off", h.STATE_VERBS)
        doctrine_lines = (REPO / "doctrine" / "OFFICE.md").read_text().splitlines()
        self.assertTrue(doctrine_lines[298].startswith("> **PAST THE CORE.**"))


if __name__ == "__main__":
    unittest.main()
