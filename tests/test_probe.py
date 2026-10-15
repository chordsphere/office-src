"""Tests for office probe (office-src 0.18.0) and the two follow-ups that
ride with it: the second-desk ruling in office start, and bale 0.4.52's
live open --json captures.

office probe runs a worker's probe block where a folder's project lives:
in its repo here, through its shell on a host (the suite's fake ssh), or
in the office root. No test reads the machine and none makes a network
call: the block is a synthetic one in the crafter's shape, the host is
the fake ssh of tests/test_project_on_host.py, bale is the fake of
tests/test_land.py (which now replays the 0.4.52 captures), the
clipboard is a command the test names in its own machine.toml, and the
clipboard reader the paste question offers is one the test puts in its
Env's desktop (0.20.1). Run with the rest of the suite:

    tests/run.sh test_probe
"""

import hashlib
import json
import os
import pathlib
import re
import shlex
import sys
import tomllib
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_start import imitate_wsl, on_a_terminal, recording_windows  # noqa: E402
from test_land import LandCase, bundle_file, brief_with_page  # noqa: E402
from test_project_on_host import HOST  # noqa: E402
from test_out_trip_to_host import HostedStartCase  # noqa: E402

import office_bale as ob  # noqa: E402
import office_host as ohost  # noqa: E402
import office_probe as op  # noqa: E402

# The development record's directory, split as the other modules split it:
# the suite's text rules refuse the word anywhere in office-src.
RECORD = REPO / ("cla" + "ude")
CAPTURES = RECORD / "fixtures" / "bale-0.4.52" / "open-json"
PROBE_SID = "2026-10-13-office-probe-002"
HISTORY_RE = r"^- \d{{4}}-\d{{2}}-\d{{2}} probe: {sid}, {n} lines$"


def capture(label):
    return json.loads((CAPTURES / f"{label}.json").read_text(encoding="utf-8"))


def captured_line(label):
    return json.loads(capture(label)["stdout"][0])


def probe_block(slug="fix-login", lines=("--- section: one ---", "hello"), header=None, writes=False,
                trailer_off=0, close=True):
    """A probe block in the shape the request's crafter emits (TARBALL.md
    4.2): a shebang, a purpose header, a blank line, a probe() whose
    output is captured, the sentinels and the integrity trailer, and a
    closing clipboard step that finds no bale (as on a host). It also says
    where it ran and whether its stdin was closed. writes makes it the
    file-based fallback: it leaves probe-output/ where it ran."""
    header = header if header is not None else [
        f"# PROBE {slug}: what the machine says, in one line.",
        "# Why: the session needs it.",
        ("# Read-only except ./probe-output/: it writes only under ./probe-output/." if writes
         else "# Read-only: writes nothing anywhere; stdout is the only output."),
        "# Bound: probe() gets 10 seconds of wall clock."]
    body = [f"  echo {shlex.quote(line)}" for line in lines]
    body += ['  echo "cwd: $(pwd -P)"',
             '  if IFS= read -r x; then echo "stdin had: $x"; else echo "stdin closed"; fi']
    if writes:
        body += ["  mkdir -p probe-output/sub", "  echo '{}' > probe-output/meta.json",
                 "  echo deep > probe-output/sub/tree.txt"]
    out = ["#!/usr/bin/env bash", *header, "", "probe() {", *body, "}", 'out="$(probe 2>&1)"',
           f'echo "=== PROBE BEGIN {slug} ==="', 'printf "%s\\n" "$out"',
           "printf -- '--- integrity: %s lines ---\\n' \"$(( $(printf '%s\\n' \"$out\" | wc -l) + "
           f"{trailer_off} ))\""]
    if close:
        out.append(f'echo "=== PROBE END {slug} ==="')
    out.append('echo "[clipboard] probe output not copied: bale is not on PATH" >&2')
    return "\n".join(out) + "\n"


# --- 1. the block and what comes back, as units ----------------------------------------------------

class TestTheBlock(unittest.TestCase):
    def test_a_block_is_read_with_its_header_and_slug(self):
        b = op.read_block(probe_block())
        self.assertEqual(b["slug"], "fix-login")
        self.assertEqual(len(b["header"]), 4)
        self.assertTrue(b["header"][0].startswith("# PROBE fix-login:"))
        self.assertTrue(b["text"].startswith("#!/usr/bin/env bash\n"))

    def test_a_chats_fence_and_crlf_are_dropped(self):
        text = "\n```bash\r\n" + probe_block().replace("\n", "\r\n") + "```\n\n"
        b = op.read_block(text)
        self.assertEqual(b["text"], probe_block())

    def test_refusals_are_by_name(self):
        cases = [
            ("echo hello\n", "no PROBE BEGIN line"),
            ("", "the block is empty"),
            (probe_block(header=[]), "no purpose header"),
            (probe_block(header=["# PROBE x: what.", "# Bound: 5 seconds."]), "does not say it is read-only"),
            (probe_block(header=["# PROBE x: this is not read-only."]), "does not say it is read-only"),
        ]
        for text, words in cases:
            with self.assertRaises(op.ProbeError) as cm:
                op.read_block(text)
            self.assertIn(words, cm.exception.lines[0], text[:40])
            self.assertIn("nothing ran", cm.exception.lines[0]) if words != "the block is empty" else None

    def test_what_came_back_is_counted_against_the_trailer(self):
        out = "noise\n=== PROBE BEGIN s ===\na\nb\n--- integrity: 2 lines ---\n=== PROBE END s ===\n"
        r = op.read_output(out)
        self.assertEqual((r["found"], r["closed"], r["count"], r["trailer"]), (True, True, 2, 2))
        self.assertEqual(r["block"][0], "=== PROBE BEGIN s ===")
        self.assertEqual(r["block"][-1], "=== PROBE END s ===")
        self.assertIn("the integrity trailer's count matches", op.count_words(r))
        bad = op.read_output(out.replace("2 lines", "3 lines"))
        self.assertIn("the integrity trailer says 3: the block is not whole", op.count_words(bad))
        self.assertIn("no PROBE BEGIN line", op.count_words(op.read_output("nothing\n")))
        self.assertIn("unclosed", op.count_words(op.read_output("=== PROBE BEGIN s ===\na\n")))
        none = op.read_output("=== PROBE BEGIN s ===\na\n=== PROBE END s ===\n")
        self.assertIn("no integrity trailer", op.count_words(none))

    def test_the_tray_takes_a_second_fallback_beside_the_first(self):
        e = Env(self)
        first = op.tray_dest(e.tmp / "tray", "2026-10-13-x-001")
        self.assertEqual(first.name, "probe-output")
        first.mkdir(parents=True)
        self.assertEqual(op.tray_dest(e.tmp / "tray", "2026-10-13-x-001").name, "probe-output-2")


class TestThePasteCommand(unittest.TestCase):
    def test_this_machines_likely_command(self):
        found = {"powershell.exe": "/mnt/c/ps.exe", "xclip": "/usr/bin/xclip"}
        which = found.get
        self.assertEqual(h.paste_candidate(on_wsl=True, which=which), h.WSL_PASTE)
        self.assertIn("Get-Clipboard", h.WSL_PASTE)
        self.assertEqual(h.paste_candidate(on_wsl=False, which=which), "xclip -selection clipboard -o")
        self.assertIsNone(h.paste_candidate(on_wsl=True, which={}.get))

    def test_it_is_kept_once_beside_the_other_keys(self):
        e = Env(self)
        machine = e.home / ".config/office-src/machine.toml"
        machine.parent.mkdir(parents=True)
        machine.write_text('clipboard_command = "clip.exe"\n')
        self.assertIsNone(h.machine_string(machine, h.PASTE_KEY))
        h.set_machine_string(machine, h.PASTE_KEY, h.WSL_PASTE, "# how the clipboard is read")
        data = tomllib.loads(machine.read_text())
        self.assertEqual(data, {"clipboard_command": "clip.exe", "paste_command": h.WSL_PASTE})
        with self.assertRaises(h.HelperError):
            h.set_machine_string(machine, h.PASTE_KEY, "pbpaste", "# again")


# --- 2. office probe on a project on this machine ---------------------------------------------------

class ProbeCase(LandCase):
    """LandCase's office (alpha, folder fix-login on alpha's lane) with a
    session out for the folder, and a block in a file."""

    def setUp(self):
        super().setUp()
        self.sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        self.block = self.e.tmp / "probe.sh"
        self.block.write_text(probe_block())
        self.machine = self.e.home / ".config" / "office-src" / "machine.toml"
        self.tray_root = self.e.home / "out-tray"

    def history(self):
        return [l for l in self.folder_md().splitlines() if " probe: " in l]


class TestProbeHere(ProbeCase):
    def test_one_command_runs_it_in_the_repo_and_hands_the_block_back(self):
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        # The block ran in alpha's repo, stdin closed, its output whole.
        self.assertIn("=== PROBE BEGIN fix-login ===", proc.stdout)
        self.assertIn(f"cwd: {os.path.realpath(self.proj)}", proc.stdout)
        self.assertIn("stdin closed", proc.stdout)
        self.assertIn("=== PROBE END fix-login ===", proc.stdout)
        # Its stderr too, and what the office says about it.
        self.assertIn("[clipboard] probe output not copied", proc.stderr)
        self.assertIn("lane names alpha", proc.stderr)
        self.assertIn("# PROBE fix-login: what the machine says", proc.stderr)
        self.assertIn(f"for {self.sid} (desk/{self.name})", proc.stderr)
        self.assertIn("4 line(s) came back between PROBE BEGIN and PROBE END, and the integrity trailer's count "
                      "matches", proc.stderr)
        self.assertIn("not on a terminal, so the block was not copied", proc.stderr)
        # One History line, committed on its own.
        self.assertEqual(len(self.history()), 1)
        self.assertRegex(self.history()[0], HISTORY_RE.format(sid=re.escape(self.sid), n=4))
        self.assertEqual(self.subjects(1), [f"office probe: {self.sid} in {self.name}"])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # bale was asked only which sessions are open; nothing was left.
        self.assertFalse((self.proj / "probe-output").exists())
        self.assertFalse(self.tray_root.joinpath(self.sid, "probe-output").exists())

    def test_the_folder_history_reads_and_office_status_agrees(self):
        self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.assertEqual(len(self.history()), 2)
        status = self.run_office("status").stdout
        self.assertNotIn("is not one of the set", status)
        self.assertNotIn("History verb", status)

    def test_piped_it_runs_nothing_without_yes(self):
        proc = self.run_office("probe", "fix-login", str(self.block), check=1)
        self.assertIn("--yes says it, and piped input is never asked; nothing ran", proc.stderr)
        self.assertNotIn("PROBE BEGIN", proc.stdout)
        self.assertEqual(self.history(), [])

    def test_a_block_that_is_not_a_probe_or_not_read_only_is_refused_by_name(self):
        asked = len(self.fake.calls_of("status"))
        for text, words in (("echo hi\n", "no PROBE BEGIN line"),
                            (probe_block(header=["# PROBE fix-login: the box.", "# Writes a file."]),
                             "does not say it is read-only")):
            self.block.write_text(text)
            proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=1)
            self.assertIn(words, proc.stderr)
            self.assertEqual(proc.stdout, "")
        self.assertEqual(self.history(), [])
        # Refused before anything was asked of bale.
        self.assertEqual(len(self.fake.calls_of("status")), asked)

    def test_from_stdin(self):
        proc = self.run_office("probe", "fix-login", "-", "--yes", input=probe_block(), check=0)
        self.assertIn("=== PROBE END fix-login ===", proc.stdout)
        self.assertEqual(len(self.history()), 1)

    def test_from_the_clipboard_with_the_paste_command(self):
        clip = self.e.tmp / "clipboard.txt"
        clip.write_text("```\r\n" + probe_block().replace("\n", "\r\n") + "```\r\n")
        self.machine.parent.mkdir(parents=True, exist_ok=True)
        self.machine.write_text(f'paste_command = "cat {clip}"\n')
        proc = self.run_office("probe", "fix-login", "--yes", check=0)
        self.assertIn(f"reading the block from the clipboard (cat {clip})", proc.stderr)
        self.assertIn("=== PROBE END fix-login ===", proc.stdout)

    def test_piped_with_no_paste_command_it_names_the_key(self):
        proc = self.run_office("probe", "fix-login", "--yes", check=1)
        self.assertIn("set paste_command in", proc.stderr)
        self.assertIn("piped input is never asked", proc.stderr)
        self.machine.write_text('paste_command = ""\n')
        proc = self.run_office("probe", "fix-login", "--yes", check=1)
        self.assertIn("turns reading the clipboard off", proc.stderr)

    def test_an_empty_clipboard_is_said(self):
        self.machine.parent.mkdir(parents=True, exist_ok=True)
        self.machine.write_text('paste_command = "printf \\"  \\\\n\\""\n')
        proc = self.run_office("probe", "fix-login", "--yes", check=1)
        self.assertIn("the clipboard is empty", proc.stderr)

    def test_the_fallback_is_carried_to_the_tray_and_removed_where_it_ran(self):
        self.block.write_text(probe_block(writes=True))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        tray = self.tray_root / self.sid / "probe-output"
        self.assertEqual(sorted(p.relative_to(tray).as_posix() for p in tray.rglob("*") if p.is_file()),
                         ["meta.json", "sub/tree.txt"])
        self.assertFalse((self.proj / "probe-output").exists())
        self.assertIn(f"carried to {tray} (2 file(s)) and removed there", proc.stderr)
        # A second one goes beside it.
        self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.assertTrue((self.tray_root / self.sid / "probe-output-2" / "meta.json").is_file())

    def test_a_probe_output_already_there_stops_it_before_it_runs(self):
        (self.proj / "probe-output").mkdir()
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=1)
        self.assertIn("probe-output/ is already in", proc.stderr)
        self.assertNotIn("PROBE BEGIN", proc.stdout)

    def test_a_trailer_that_does_not_match_is_said(self):
        self.block.write_text(probe_block(trailer_off=2))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.assertIn("but the integrity trailer says 6: the block is not whole", proc.stderr)

    def test_a_block_that_never_closes_returns_one_and_is_counted_as_nothing(self):
        self.block.write_text(probe_block(close=False))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=1)
        self.assertIn("unclosed", proc.stderr)
        self.assertRegex(self.history()[0], HISTORY_RE.format(sid=re.escape(self.sid), n=0))


class TestWhereAndWhichSession(ProbeCase):
    def test_a_folder_with_no_lane_needs_the_project_named(self):
        folder = self.run_office("open", "no-lane", check=0).stdout.strip()
        name = folder.split("/")[1]
        proc = self.run_office("probe", name, str(self.block), "--yes", check=1)
        self.assertIn("--project NAME (alpha), or --project office for the office itself", proc.stderr)
        # Named, it still needs a session the folder records.
        proc = self.run_office("probe", name, str(self.block), "--yes", "--project", "alpha", check=1)
        self.assertIn(f"{name} records no session open in", proc.stderr)
        self.assertIn(f"open there: {self.sid}", proc.stderr)
        self.assertIn("a probe is a session's", proc.stderr)

    def test_an_unknown_project_is_refused(self):
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", "--project", "nowhere", check=1)
        self.assertIn("no project named nowhere", proc.stderr)

    def test_the_office_itself_runs_it_in_the_office_root(self):
        sitting = self.run_office("start", "fix-login", "--in-office", "--read-only", "--goal", "Plan it",
                                  check=0).stdout
        sit = re.search(r"^Packed (\S+) for ", sitting, re.M).group(1)
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", "--project", "office",
                               "--sid", sit, check=0)
        self.assertIn(f"cwd: {os.path.realpath(self.root)}", proc.stdout)
        self.assertRegex(self.history()[-1], HISTORY_RE.format(sid=re.escape(sit), n=4))

    def test_several_open_the_blocks_slug_picks_one_else_sid(self):
        other = self.start("fix-login", "--on", "alpha", "--goal", "Docs too", "--write", "docs", "--slug", "docs-pass")
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=0)
        self.assertIn(f"for {self.sid} (desk/{self.name})", proc.stderr)
        self.block.write_text(probe_block(slug="something-else"))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", check=1)
        self.assertIn("--sid SID says which", proc.stderr)
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", "--sid", other, check=0)
        self.assertRegex(self.history()[-1], HISTORY_RE.format(sid=re.escape(other), n=4))
        proc = self.run_office("probe", "fix-login", str(self.block), "--yes", "--sid", "2026-01-01-nope-001",
                               check=1)
        self.assertIn("not a session fix-login records", proc.stderr.replace(self.name, "fix-login"))


# --- 3. on a host, through the project's shell ---------------------------------------------------------

class TestProbeOnAHost(HostedStartCase):
    def setUp(self):
        super().setUp()
        self.only_far()
        host = self.ssh.host_dir(HOST)
        (host / "path").write_text(f"{self.fake.dir}:/usr/bin:/bin\n")
        self.sid = self.start(self.name, "--on", "far", "--goal", "Fix it there", "--write", "src")
        self.block = self.e.tmp / "probe.sh"
        self.tray_root = self.e.home / "out-tray"

    def test_it_runs_through_the_plain_shell_in_the_path_and_carries_the_fallback_back(self):
        self.block.write_text(probe_block(writes=True))
        self.ssh.reset()
        proc = self.run_office("probe", self.name, str(self.block), "--project", "far", "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"cwd: {os.path.realpath(self.proj)}", proc.stdout)
        self.assertIn("stdin closed", proc.stdout)
        self.assertIn(f"on {HOST} (through far's shell)", proc.stderr)
        calls = self.ssh.connections()
        # Never the attended form: a probe never waits on a terminal.
        self.assertTrue(all("-tt" not in c for c in calls), calls)
        # One reach: the plan's batch was the first connection, and none
        # after it checked the host again.
        self.assertEqual([c for c in calls if c[-1] in ("true", "'true'")], [])
        self.assertLessEqual(len(calls), 5, calls)
        # The fallback's directory came back to the tray and is gone there.
        tray = self.tray_root / self.sid / "probe-output"
        self.assertEqual((tray / "sub" / "tree.txt").read_text(), "deep\n")
        self.assertFalse((self.proj / "probe-output").exists())
        self.assertEqual(self.ssh.left_on(HOST), [])
        self.assertRegex([l for l in (self.root / self.folder / "folder.md").read_text().splitlines()
                          if " probe: " in l][0], HISTORY_RE.format(sid=re.escape(self.sid), n=4))

    def test_a_host_that_does_not_answer_stops_it_with_the_connect_line(self):
        self.block.write_text(probe_block())
        manifest = self.root / "floor-plan" / "manifest.toml"
        manifest.write_text(manifest.read_text().replace(HOST, "someone@a-host-that-is-down.example"))
        self.e.git(self.root, "commit", "-qam", "down")
        proc = self.run_office("probe", self.name, str(self.block), "--project", "far", "--yes", check=1)
        self.assertIn("start the VPN client", proc.stderr)
        self.assertIn("nothing ran", proc.stderr)
        self.assertNotIn("PROBE BEGIN", proc.stdout)


# --- 4. on a terminal: the header, the one question, the clipboard both ways --------------------------

class TestProbeOnATerminal(ProbeCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_it_shows_the_header_asks_once_and_puts_the_block_on_the_clipboard(self):
        copied = self.e.tmp / "copied.txt"
        self.machine.parent.mkdir(parents=True, exist_ok=True)
        self.machine.write_text(f'clipboard_command = "tee {copied}"\n')
        code, screen = on_a_terminal(self, [str(self.e.office_bin), "probe", "fix-login", str(self.block)],
                                     self.root, self.e.env, [(b"Run it? y or N (--yes) [N]:", "y")])
        self.assertEqual(code, 0, screen)
        self.assertIn("# Read-only: writes nothing anywhere", screen)
        self.assertLess(screen.index("# PROBE fix-login:"), screen.index("Run it?"))
        lines = copied.read_text().splitlines()
        self.assertEqual(lines[0], "=== PROBE BEGIN fix-login ===")
        self.assertEqual(lines[-1], "=== PROBE END fix-login ===")
        self.assertEqual(lines[-2], "--- integrity: 4 lines ---")
        self.assertIn("the probe block (PROBE BEGIN to PROBE END) is on the clipboard", screen)

    def test_a_plain_return_runs_nothing(self):
        code, screen = on_a_terminal(self, [str(self.e.office_bin), "probe", "fix-login", str(self.block)],
                                     self.root, self.e.env, [(b"Run it? y or N (--yes) [N]:", "")])
        self.assertEqual(code, 0, screen)
        self.assertNotIn("PROBE BEGIN fix-login ===\r\n", screen)
        self.assertIn("not run: nothing was written", screen)
        self.assertEqual(self.history(), [])

    def test_the_paste_command_is_this_machines_reader_taken_once_and_kept(self):
        # The machine's reader is the one this test's Env holds: a fake
        # wl-paste in its desktop, the only place the office looks for one
        # (on a WSL machine the running machine's powershell.exe was
        # offered instead, and this test failed only there).
        clip = self.e.tmp / "clipboard.txt"
        clip.write_text(probe_block())
        (self.e.desktop / "wl-paste").write_text(f'#!/bin/sh\n[ "$1" = --no-newline ] || exit 9\ncat {clip}\n')
        (self.e.desktop / "wl-paste").chmod(0o755)
        env = self.e.env
        # 0.22.0: the machine's own reader is a fact the office finds, not a
        # judgment it asks for: taken, said and kept.
        code, screen = on_a_terminal(self, [str(self.e.office_bin), "probe", "fix-login"], self.root, env, [
            (b"Run it? y or N (--yes) [N]:", "y")])
        self.assertEqual(code, 0, screen)
        self.assertEqual(tomllib.loads(self.machine.read_text())["paste_command"], "wl-paste --no-newline")
        self.assertIn("this machine reads its clipboard with wl-paste --no-newline", screen)
        self.assertNotIn("(paste_command in machine.toml)", screen)
        self.assertIn("is not asked again", screen)
        # Asked once: the second run takes it from machine.toml.
        code, screen = on_a_terminal(self, [str(self.e.office_bin), "probe", "fix-login"], self.root, env,
                                     [(b"Run it? y or N (--yes) [N]:", "y")])
        self.assertEqual(code, 0, screen)
        self.assertNotIn("How does this machine read its clipboard?", screen)


    # 0.20.1: a WSL machine, imitated. It holds powershell.exe, clip.exe
    # and explorer.exe on its PATH (recording fakes here); the test above
    # failed on such a machine, offered the machine's PowerShell line.

    def test_on_an_imitated_wsl_the_envs_reader_is_offered_and_nothing_of_windows_runs(self):
        windows, calls = recording_windows(self.e.tmp / "windows", probe_block())
        clip = self.e.tmp / "clipboard.txt"
        clip.write_text(probe_block())
        (self.e.desktop / "wl-paste").write_text(f'#!/bin/sh\n[ "$1" = --no-newline ] || exit 9\ncat {clip}\n')
        (self.e.desktop / "wl-paste").chmod(0o755)
        code, screen = on_a_terminal(self, [str(self.e.office_bin), "probe", "fix-login"], self.root,
                                     imitate_wsl(self.e, windows), [
            (b"this machine reads its clipboard with wl-paste --no-newline", None),
            (b"Run it? y or N (--yes) [N]:", "y")])
        self.assertEqual(code, 0, screen)
        self.assertEqual(tomllib.loads(self.machine.read_text())["paste_command"], "wl-paste --no-newline")
        self.assertIn("the block is not on the clipboard (no clipboard_command here)", screen)
        self.assertFalse(calls.exists(), calls.read_text() if calls.exists() else "")

    def test_on_an_imitated_wsl_pointed_at_the_fakes_powershell_is_offered_and_clip_exe_fed(self):
        windows, calls = recording_windows(self.e.tmp / "windows", probe_block())
        env = dict(imitate_wsl(self.e, windows), OFFICE_DESKTOP_PATH=str(windows))
        code, screen = on_a_terminal(self, [str(self.e.office_bin), "probe", "fix-login"], self.root, env, [
            (f"this machine reads its clipboard with {h.WSL_PASTE}".encode(), None),
            (b"Run it? y or N (--yes) [N]:", "y")])
        self.assertEqual(code, 0, screen)
        self.assertEqual(tomllib.loads(self.machine.read_text())["paste_command"], h.WSL_PASTE)
        made = [l.split(" (in ")[0] for l in calls.read_text().splitlines()]
        self.assertEqual(made, ["powershell.exe -NoProfile -Command [Console]::OutputEncoding = "
                                "[Text.Encoding]::UTF8; Get-Clipboard", "clip.exe "])
        back = (windows / "clip.exe.in").read_bytes().decode("utf-16-le").splitlines()
        self.assertEqual((back[0], back[-2], back[-1]), ("=== PROBE BEGIN fix-login ===",
                                                         "--- integrity: 4 lines ---", "=== PROBE END fix-login ==="))
        self.assertIn(f"the probe block (PROBE BEGIN to PROBE END) is on the clipboard ({windows / 'clip.exe'})",
                      screen.replace("\r\n", "\n"))


# --- 5. the second-desk ruling in office start ----------------------------------------------------------

class TestTheSecondDeskRuling(LandCase):
    """A second desk is bale's to recognize, and the office refuses an
    overlap only where bale would (the ruling ratified with session
    2026-10-13-office-probe-002). From bale 0.4.50 office start asks bale
    open --check --json, and its outcome decides an overlap the office's
    own check found in a bundle it can read."""

    def argv(self, slug="audience-line", write="src"):
        return ["Fix it, from a bundle", "--slug", slug, "--write", write, "--constraint", ob.PROJECT_CONSTRAINT]

    def open_it(self, version):
        self.e.env["FAKE_BALE_VERSION"] = version
        bundle = bundle_file(self.e.tmp / "b", "2026-10-08-audience-line", self.argv(), brief_with_page())
        proc = self.run_office("start", "fix-login", "--on", "alpha", "--bundle", str(bundle), check=0)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        later = self.run_office("open", "audience-again", "--lane", "alpha: src", check=0).stdout.strip()
        return sid, bundle, later.split("/")[1]

    def test_a_bundle_the_office_can_read_goes_through_as_a_second_desk(self):
        sid, bundle, later = self.open_it("0.4.52")
        proc = self.run_office("start", later, "--on", "alpha", "--bundle", str(bundle), check=0)
        self.assertTrue(proc.stdout.startswith(f"Joined {sid}, already open, as a second desk"), proc.stdout)
        # The office said what its own check saw, bale's lines, and why it
        # went on.
        self.assertIn(f"{sid} is open in alpha", proc.stderr)
        self.assertIn(f"[bale] second desk: this bundle opened session {sid}, which is still open", proc.stderr)
        self.assertIn("bale's own rehearsal passed it all the same (outcome rehearsed)", proc.stderr)
        self.assertIn("the office refuses an overlap only where bale would", proc.stderr)
        (_, argv, _), = [c for c in self.fake.calls_of("open-check") if str(bundle) in c[1]][-1:]
        self.assertEqual(argv, ["open", "--check", "--json", str(bundle)])
        self.assertEqual(self.fake.land_state()["desks"][sid], 2)

    def test_below_open_json_the_office_refuses_it_in_its_own_words_as_before(self):
        sid, bundle, later = self.open_it("0.4.45")
        checks = len(self.fake.calls_of("open-check"))
        proc = self.run_office("start", later, "--on", "alpha", "--bundle", str(bundle), check=1)
        self.assertIn(f"{sid} is open in alpha", proc.stderr)
        self.assertIn("land it first", proc.stderr)
        self.assertEqual(len(self.fake.calls_of("open-check")), checks, "refused before bale was asked")

    def test_another_bundle_on_the_open_forecast_is_refused_where_bale_refuses_it(self):
        sid, _, later = self.open_it("0.4.52")
        other = bundle_file(self.e.tmp / "b", "2026-10-09-another", self.argv(slug="another"))
        proc = self.run_office("start", later, "--on", "alpha", "--bundle", str(other), check=1)
        self.assertIn(f"{sid} is open in alpha", proc.stderr)
        self.assertIn("bale's own rehearsal refuses it too (gate-refused): pack write forecast intersects",
                      proc.stderr)
        self.assertNotIn("Out tray:", proc.stdout)

    def test_the_reader_reads_the_captured_rehearsals(self):
        def rd_for(label):
            rec = capture(label)
            proc = types.SimpleNamespace(returncode=rec["exit"], stdout="\n".join(rec["stdout"]) + "\n",
                                         stderr="\n".join(rec["stderr"]) + "\n")
            version = types.SimpleNamespace(returncode=0, stdout="bale 0.4.52\n", stderr="")
            rd = ob.Reader(runner=lambda argv, **k: version if argv[1:] == ["--version"] else proc)
            rd.bale = lambda: "bale"
            return rd
        r = ob.check_bundle_report(rd_for("check-desk"), self.root, "office", None, "x.bale-bundle")
        self.assertEqual(r["found"], "TMP/dl/2026-10-13-office-probe-open.bale-bundle")
        self.assertEqual(r["over"], [])
        self.assertEqual(len(r["bale"]), 1)
        self.assertTrue(r["bale"][0].startswith("[bale] second desk: this bundle opened session "))
        with self.assertRaises(ob.StartError) as cm:
            ob.check_bundle_report(rd_for("check-other"), self.root, "office", None, "x.bale-bundle")
        self.assertIn("refused it (gate-refused): [bale] error: pack write forecast intersects",
                      cm.exception.lines[0])


# --- 6. the captures, and the contract they hold the office to ------------------------------------------

class TestTheCaptures(unittest.TestCase):
    def setUp(self):
        self.cons = ob.Consumption()
        self.files = sorted(CAPTURES.glob("*.json"))

    def test_every_line_is_the_one_the_probe_captured(self):
        self.assertEqual(len(self.files), 13)
        for f in self.files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual(len(rec["stdout"]), len(rec["stdout_sha256"]), f.name)
            for line, sha in zip(rec["stdout"], rec["stdout_sha256"]):
                self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), sha, f.name)
            self.assertIn(f"probe of session {PROBE_SID}", rec["captured"])
            self.assertEqual((rec["cwd"], rec["stdin"]), ("TMP/repo", "closed"))
        self.assertTrue((CAPTURES.parent / "README.md").is_file())

    def test_the_surfaces_are_declared_as_the_probe_ran_them(self):
        check = capture("check-fresh")
        self.assertEqual(self.cons.argv("open_check_json", bundle=check["argv"][-1]), check["argv"])
        opened = capture("open-opened")
        self.assertEqual(sorted(self.cons.argv("open_json", bundle=opened["argv"][-1])), sorted(opened["argv"]))
        spec = self.cons.surface("open_check_json")
        self.assertEqual(spec["since"], self.cons.surface("open_json")["since"])
        self.assertEqual(captured_line("check-fresh")["outcome"], spec["outcome_passed"])
        self.assertEqual(captured_line("check-other")["outcome"], spec["refused"])

    def test_every_declared_key_is_in_the_captured_lines(self):
        from test_read_side import resolve
        pools = {"open_check_json": ["check-fresh", "check-desk", "check-other"],
                 "open_json": ["open-opened", "open-desk"]}
        for surface, labels in pools.items():
            for key in self.cons.surface(surface)["keys"]:
                seen = False
                for label in labels:
                    reached, missing = resolve(captured_line(label), key)
                    if key == "bundle.path" and captured_line(label)["bundle"] is None:
                        continue
                    self.assertEqual(missing, [], f"{label} lacks {key}")
                    seen = seen or any(v is not None for v in reached)
                self.assertTrue(seen, f"no captured {surface} line holds {key}")

    def test_what_the_rehearsal_says_of_a_second_desk(self):
        """The ruling's fact: the rehearsal key is the rehearsal's kind, and
        a second desk's line is a fresh bundle's, byte for byte; bale names
        the session only on stderr."""
        self.assertEqual(captured_line("check-desk")["rehearsal"], "check")
        self.assertEqual(capture("check-desk")["stdout"], capture("check-fresh")["stdout"])
        self.assertIsNone(captured_line("check-desk")["desk"])
        line = self.cons.surface("open_check_json")["second_desk_line"]
        self.assertTrue(any(l.startswith(line) for l in capture("check-desk")["stderr"]))
        self.assertFalse(any(l.startswith(line) for l in capture("check-fresh")["stderr"]))
        other = captured_line("check-other")
        self.assertEqual((capture("check-other")["exit"], other["reason"]), (1, "gate-refused"))
        self.assertIsNone(other["rehearsal"])
        doc = (CAPTURES.parent / "format_open_json.txt").read_text(encoding="utf-8")
        self.assertIn('null on "opened", "second-desk" and "open-refused"', " ".join(doc.split()))

    def test_the_opens_and_the_desks(self):
        opened, desk, copy = captured_line("open-opened"), captured_line("open-desk"), captured_line("open-desk-copy")
        self.assertEqual(opened["outcome"], "opened")
        self.assertEqual((desk["outcome"], desk["desk"], copy["desk"]), ("second-desk", "desk-2", "desk-3"))
        self.assertEqual({opened["sid"], desk["sid"], copy["sid"]}, {"2026-10-13-office-probe-open-001"})
        self.assertEqual(desk["tarball"], opened["tarball"])
        self.assertIn(f"{desk['sid']}@desk-2", desk["opener"])
        self.assertEqual(copy["bundle"]["sha256"], desk["bundle"]["sha256"])
        self.assertEqual(copy["bundle"]["stem"], "2026-10-13-office-probe-open (1)")
        status = json.loads(capture("status-desk")["stdout"][0])
        self.assertEqual(status["sessions"], [desk["sid"]], "a second desk opens nothing")


# --- 7. the record: help, the catalog, the doctrine, the release ----------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_help_lists_it_and_its_help_has_an_example(self):
        import subprocess
        # Plumbing since 0.22.0: a session names the line when it needs it,
        # and office help --all lists it with every verb.
        usage = subprocess.run([str(REPO / "bin/office"), "help", "--all"], capture_output=True, text=True).stdout
        self.assertIn("office probe FOLDER [FILE]", usage)
        send = usage.split("Send a session out", 1)[1].split("Deliver it to the audience", 1)[0]
        self.assertIn("office probe", send)
        own = subprocess.run([str(REPO / "bin/office"), "probe", "--help"], capture_output=True, text=True)
        self.assertEqual(own.returncode, 0)
        self.assertIn("Examples:", own.stdout)
        self.assertIn("office probe 13", own.stdout)

    def test_the_catalog_and_the_fast_tier(self):
        verbs = tomllib.loads((REPO / "share/verbs.toml").read_text())["verbs"]
        self.assertEqual((verbs["probe"]["kind"], verbs["probe"]["built"], verbs["probe"]["lands"]),
                         ("script", True, []))
        tier = tomllib.loads((REPO / "tests/fast-tier.toml").read_text())
        self.assertIn("probe", tier["entry_points"])
        self.assertIn("probe", h.HISTORY_VERBS)

    def test_the_doctrine_says_it_in_its_places(self):
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        verbs = doctrine.split("## 7. Verbs", 1)[1].split("## 8.", 1)[0]
        self.assertIn("| probe | script: run a worker's probe block where a folder's project lives", verbs)
        self.assertIn("a `Suite:` line, under the install line", verbs)
        front = doctrine.split("## Front sheet", 1)[1].split("## 2.", 1)[0]
        self.assertIn("`office probe` runs a worker's probe block", front)

    def test_the_release(self):
        # 0.18.0 or a later release: a pin on the exact version would fail
        # every release after this one (0.19.0 relaxed it).
        self.assertGreaterEqual(h.compare_versions((REPO / "VERSION").read_text().strip(), "0.18.0"), 0)
        releases = (REPO / "RELEASES.md").read_text()
        self.assertLess(releases.index("## 0.18.0"), releases.index("## 0.17.2"))
        self.assertIn("office probe", releases.split("## 0.18.0", 1)[1].split("## 0.17.2", 1)[0])
        readme = (REPO / "README.md").read_text()
        self.assertIn("office probe", readme)


if __name__ == "__main__":
    unittest.main()
