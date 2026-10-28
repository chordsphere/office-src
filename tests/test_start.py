"""Tests for the out trip: office slip, the per-project declarations, office
note's prefix check, and office start with its out tray.

bale is never needed. The fake bale here packs: it writes request and
context tarballs into .bale/outbox/ and keeps the open sessions in its own
state file, and every line it prints is built from what the out-and-in
probe captured from a real bale 0.4.45 (kept verbatim, with their sha256,
in the development record's fixtures): the same report keys, the same
stderr, the same opener between the same scissor lines, the same refusal.
The fixtures are also read directly, so the office's readers are run over
bale's own bytes. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import hashlib
import json
import os
import pathlib
import pty
import re
import select
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, WSL_KERNEL, Env, fake_program, h, kept_setup  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)

# Split so the text rules' own check does not trip on this file.
PACK_FIXTURES = REPO / ("cla" + "ude") / "fixtures" / "bale-0.4.45" / "pack"
CONSUMPTION = REPO / "share" / "bale-consumption.toml"
PROBE_SID = "2026-10-02-friction-out-and-in-002"


def pack_fixture(label):
    return json.loads((PACK_FIXTURES / f"{label}.json").read_text(encoding="utf-8"))


def all_pack_fixtures():
    return sorted(PACK_FIXTURES.glob("*.json"))




class FakePackBale:
    """A directory holding the fake bale that packs (tests/fakes/pack_bale.py);
    its state and calls live beside it."""

    def __init__(self, tmp):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="fake-pack-bale-", dir=tmp))
        self.state = self.dir / "state.json"
        self.calls = self.dir / "calls.jsonl"
        fake_program(self.dir / "bale", "pack_bale", config=self.config(self.state, self.calls))

    @staticmethod
    def config(state, calls):
        """The packing fake's config: its fixtures, its state file and its calls file."""
        return {"fixtures": str(PACK_FIXTURES), "state": str(state), "calls": str(calls)}

    def path(self, base):
        return f"{self.dir}{os.pathsep}{base}"

    def argvs(self):
        if not self.calls.is_file():
            return []
        return [json.loads(l) for l in self.calls.read_text().splitlines()]

    def packs(self):
        """(cwd, argv) of every bale pack the office ran."""
        return [(c, a) for c, a in self.argvs() if a and a[0] == "pack"]

    def refuse_next_pack(self):
        s = json.loads(self.state.read_text()) if self.state.is_file() else {"repos": {}, "fail": []}
        s["fail"].append("pack")
        self.state.write_text(json.dumps(s))


def git_repo(path, files=None, ignore_bale=True):
    """A committed git repo holding files ({relpath: text})."""
    path = pathlib.Path(path)
    path.mkdir(parents=True, exist_ok=True)
    env = {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull, "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@x", "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@x"}
    subprocess.run(["git", "init", "-q", str(path)], check=True, env=env)
    for rel, text in (files or {"README.md": "x\n"}).items():
        (path / rel).parent.mkdir(parents=True, exist_ok=True)
        (path / rel).write_text(text)
    if ignore_bale:
        (path / ".gitignore").write_text(".bale/\n")
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True, env=env)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", "init"], check=True, env=env)
    (path / ".bale").mkdir(exist_ok=True)
    return path


def tar_names(path):
    with tarfile.open(path) as t:
        return sorted(t.getnames())


def on_a_terminal(test, argv, cwd, env, script):
    """Run the office command on a pty, answering each prompt in script:
    a list of (marker the screen must show, line to type, or None to type
    nothing). Returns
    (exit code, everything the screen showed).

    The program starts as a terminal's foreground program does, with
    SIGINT and SIGQUIT at their defaults (0.27.0), as run_on_a_pty in
    tests/test_front_door.py has started the tour since 0.26.0: a run
    started in the background from a non-interactive shell ignores both,
    and without this every program a test drives here would inherit that,
    so a trap it sets on an interrupt could never fire."""
    pid, fd = pty.fork()
    if pid == 0:
        try:
            for sig in (signal.SIGINT, signal.SIGQUIT):
                signal.signal(sig, signal.SIG_DFL)
            os.chdir(cwd)
            os.execve(argv[0], argv, env)
        finally:
            os._exit(127)
    seen = b""

    def read_until(marker, limit=30):
        nonlocal seen
        deadline = time.time() + limit
        while marker not in seen and time.time() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                seen += chunk
        return marker in seen

    for marker, answer in script:
        test.assertTrue(read_until(marker), seen.decode(errors="replace"))
        if answer is not None:  # None: the marker is only waited for (0.22.0)
            os.write(fd, answer.encode() + b"\n")
    deadline = time.time() + 60
    while time.time() < deadline:  # to the end of the child's output
        ready, _, _ = select.select([fd], [], [], 0.2)
        if not ready:
            continue
        try:
            chunk = os.read(fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        seen += chunk
    _, status = os.waitpid(pid, 0)
    os.close(fd)
    return os.waitstatus_to_exitcode(status), seen.decode(errors="replace")


def opener_from(text):
    """The lines office start printed between its scissor lines."""
    lines = text.splitlines()
    a = lines.index("--8<-- session opener --8<--")
    b = lines.index("--8<-- end session opener --8<--")
    return lines[a + 1:b]


def recording_windows(d, clipboard_text="", clip_sets_clipboard=False):
    """A directory of fake Windows programs, as WSL puts the real ones on
    the PATH: clip.exe, explorer.exe and powershell.exe. Each appends one
    line to d/calls (its name, its arguments, the directory it ran in);
    clip.exe keeps what it was fed in d/clip.exe.in, and powershell.exe
    prints clipboard_text, as Get-Clipboard would. With clip_sets_clipboard
    (0.23.0) clip.exe also does what the real one does with what it is fed,
    read as UTF-16LE: it becomes the clipboard powershell.exe prints, so a
    copy the office reads back is held to what was fed. Returns (d,
    d/calls)."""
    d.mkdir(parents=True)
    calls = d / "calls"
    record = f'printf \'%s %s (in %s)\\n\' "$(basename "$0")" "$*" "$PWD" >> {calls}\n'
    clip = f"cat > {d / 'clip.exe.in'}\n"
    if clip_sets_clipboard:
        clip += f"iconv -f UTF-16LE -t UTF-8 < {d / 'clip.exe.in'} > {d / 'clipboard.txt'}\n"
    bodies = {"clip.exe": clip, "explorer.exe": "",
              "powershell.exe": f"cat {d / 'clipboard.txt'}\n"}
    (d / "clipboard.txt").write_text(clipboard_text)
    for name, body in bodies.items():
        (d / name).write_text("#!/bin/sh\n" + record + body)
        (d / name).chmod(0o755)
    return d, calls


def imitate_wsl(e, path_first):
    """The env of e with this machine made WSL to the office (a WSL
    kernel's version string in a file of the test's own) and path_first
    first on the PATH, as WSL puts the Windows directories there. The
    Env's desktop is left as it is."""
    kernel = e.tmp / "proc-version"
    kernel.write_text(WSL_KERNEL)
    return dict(e.env, OFFICE_PROC_VERSION=str(kernel), PATH=f"{path_first}{os.pathsep}{e.env['PATH']}")


# --- the captured packs themselves ---------------------------------------------------

class TestPackFixtures(unittest.TestCase):
    def setUp(self):
        self.cons = ob.Consumption()
        self.data = tomllib.loads(CONSUMPTION.read_text())

    def test_every_line_is_the_one_the_probe_captured(self):
        files = all_pack_fixtures()
        self.assertGreaterEqual(len(files), 12)
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual(len(rec["stdout"]), len(rec["stdout_sha256"]), f.name)
            for line, sha in zip(rec["stdout"], rec["stdout_sha256"]):
                self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), sha, f.name)
            self.assertIn(f"probe of session {PROBE_SID}", rec["captured"], f.name)

    def test_every_declared_key_is_in_the_captured_reports(self):
        """The test that fails when a bale release moves a pack key:
        re-capture into a new bale-VERSION/pack/ and this names it."""
        for surface, labels in (("pack", ("office-pack", "project-pack")),
                                ("context", ("office-context-whole", "office-context-include", "ctx-other-include",
                                             "ctx-other-inside", "ctx-plain"))):
            spec = self.data["surfaces"][surface]
            for label in labels:
                rec = pack_fixture(label)
                self.assertEqual(rec["exit"], 0, label)
                line = json.loads(rec["stdout"][-1])
                self.assertEqual(line["outcome"], spec["outcome"], label)
                for key in spec["keys"]:
                    self.assertIn(key, line, f"{label} lacks {key}")

    def test_every_flag_the_office_passes_is_in_bales_help(self):
        help_text = "\n".join(pack_fixture("pack_help")["stdout"])
        for surface in ("pack", "context"):
            spec = self.data["surfaces"][surface]
            flags = [w for w in spec["argv"] if w.startswith("--")]
            for group in ("optional", "repeated", "switches"):
                flags += [f for f, _ in spec.get(group, [])]
            for flag in flags:
                self.assertIn(flag, help_text, f"{surface}: {flag}")

    def test_argv_comes_from_the_declaration(self):
        argv = self.cons.argv("pack", goal="Do it", slug="do-it", includes=["src", "lib"], writes=["src"],
                              constraints=[ob.PROJECT_CONSTRAINT], readme_file=None, no_readme=True,
                              read_only=False, work_class="code")
        self.assertEqual(argv, ["pack", "Do it", "--slug", "do-it", "--json", "--work-class", "code",
                                "--include", "src", "--include", "lib", "--write", "src",
                                "--constraint", ob.PROJECT_CONSTRAINT, "--no-readme"])
        self.assertEqual(self.cons.argv("context", includes=["desk/x", "profile.md"]),
                         ["pack", "--context", "--json", "--include", "desk/x", "--include", "profile.md"])
        self.assertEqual(self.cons.argv("context"), ["pack", "--context", "--json"])
        self.assertIn("--read-only", self.cons.argv("pack", goal="g", slug="s", read_only=True))

    def test_the_opener_is_read_from_bales_own_lines(self):
        spec = self.data["surfaces"]["pack"]
        for label in ("office-pack", "project-pack"):
            rec = pack_fixture(label)
            sid = json.loads(rec["stdout"][0])["sid"]
            lines = ob.opener_lines(rec["stderr"], spec)
            self.assertEqual(lines[0], 'I\'m using "bale", a CLI that packaged the attached request tarball.')
            self.assertEqual(lines[1], f"This message opens bale session {sid}.")
            self.assertTrue(lines[-1].startswith("what I need back is one response tarball"))
            self.assertNotIn(spec["opener"][0], lines)
        # The plain report prints the same opener on stdout.
        plain = pack_fixture("project-pack-plain")
        self.assertEqual(ob.opener_lines(plain["stdout"], spec),
                         ob.opener_lines(pack_fixture("project-pack")["stderr"], spec))
        self.assertIsNone(ob.opener_lines(pack_fixture("office-second-pack")["stderr"], spec))

    def test_a_refused_pack_says_so_only_on_stderr(self):
        """Why office start checks the open forecasts itself: under
        --json bale's refusal is an exit and a stderr line, nothing on
        stdout."""
        rec = pack_fixture("office-second-pack")
        self.assertEqual(rec["exit"], 1)
        self.assertEqual(rec["stdout"], [])
        self.assertIn("pack write forecast intersects 1 open session(s)", rec["stderr"][-1])
        status = json.loads(pack_fixture("office-status")["stdout"][0])
        sid = status["sessions"][0]
        self.assertEqual(ob.forecast_overlap(["desk/x", "notepad"], status["scopes"][sid]), ["notepad"])

    def test_include_groups_do_not_fire_under_context(self):
        """Why office start names the hung items for the office's context."""
        whole = json.loads(pack_fixture("office-context-whole")["stdout"][0])
        one = json.loads(pack_fixture("office-context-include")["stdout"][0])
        self.assertGreater(whole["context_files"], one["context_files"])
        self.assertEqual(one["context_files"], 1)
        self.assertTrue(json.loads(pack_fixture("office-pack")["stdout"][0])["include_group"]["pulled"])


class TestForecastOverlap(unittest.TestCase):
    def test_entries_overlap_when_equal_or_nested(self):
        f = ob.forecast_overlap
        self.assertEqual(f(["notepad"], ["notepad"]), ["notepad"])
        self.assertEqual(f(["desk/a"], ["desk"]), ["desk/a"])
        self.assertEqual(f(["bin/"], ["bin/office"]), ["bin/office"])
        self.assertEqual(f(["desk/a", "notepad"], ["desk/b"]), [])
        self.assertEqual(f([], ["notepad"]), [])
        self.assertEqual(f(["src"], []), [])
        self.assertEqual(f(None, ["src"]), ["src"])
        self.assertEqual(f(["src"], None), ["src"])
        self.assertEqual(f(None, None), ["the whole tree"])
        self.assertEqual(f(["src"], ["."]), ["src"])


# --- office slip -------------------------------------------------------------------------

class SlipCase(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def slips(self):
        return sorted((self.root / "suggestion-box").glob("*.md"))


class TestSlip(SlipCase):
    # No test here drives a terminal, so the class runs beside the other jobs, not in the serial lane (0.21.0).
    def test_a_slip_is_its_own_page_committed_alone(self):
        (self.root / "notepad" / "draft.md").write_text("uncommitted\n")
        proc = self.e.run("slip", "--about", "bale", "pack", "needs", "too", "many", "flags", cwd=self.root, check=0)
        page = proc.stdout.strip()
        self.assertRegex(page, r"^suggestion-box/\d{4}-\d{2}-\d{2}-pack-needs-too-many-flags\.md$")
        text = (self.root / page).read_text()
        self.assertTrue(text.startswith("# pack needs too many flags\n\n- about: bale\n- dropped: "))
        self.assertTrue(text.endswith("\npack needs too many flags\n"))
        self.assertIn("What caused friction", text)
        self.assertEqual(self.e.git(self.root, "show", "--name-only", "--format=%s", "HEAD").split(),
                         ["office", "slip:", page.split("/")[1][:-3], "(about", "bale)", page])
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "?? notepad/draft.md")
        self.assertIn("Suggestion box: 1 slip(s).", self.e.run(cwd=self.root, check=0).stdout)

    def test_piped_text_and_no_about_is_never_asked(self):
        proc = self.e.run("slip", cwd=self.root, input="the survey is slow\nand loud\n", check=0)
        text = (self.root / proc.stdout.strip()).read_text()
        self.assertNotIn("- about:", text)
        self.assertTrue(text.endswith("the survey is slow\nand loud\n"))
        self.assertIn("--about", proc.stderr)

    def test_a_slip_works_unfounded_and_under_skew(self):
        from test_office import NEXT, MIGRATION_ADD_SPACE
        self.assertIn("unfounded", self.e.run("slip", "x", cwd=self.root, check=0).stderr)
        behind = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Adds a handbook.", MIGRATION_ADD_SPACE)])
        proc = self.e.run("slip", "behind", cwd=self.root, bin_path=behind, check=0)
        self.assertIn("behind", proc.stderr)
        ahead = self.e.fake_install("0.0.9")
        proc = self.e.run("slip", "ahead", cwd=self.root, bin_path=ahead, check=0)
        self.assertIn("migrated past", proc.stderr)
        self.assertEqual(len(self.slips()), 3)

    def test_the_office_stays_ascii_and_the_name_has_no_escape(self):
        proc = self.e.run("slip", "café — too slow", cwd=self.root, check=0)
        page = proc.stdout.strip()
        self.assertNotIn("u2014", page)
        text = (self.root / page).read_bytes().decode("ascii")
        self.assertIn("caf\\xe9 \\u2014 too slow", text)

    def test_the_same_words_twice_make_two_pages(self):
        a = self.e.run("slip", "same", cwd=self.root, check=0).stdout.strip()
        b = self.e.run("slip", "same", cwd=self.root, check=0).stdout.strip()
        self.assertNotEqual(a, b)
        self.assertTrue(b.endswith("-same-2.md"), b)

    def test_refusals(self):
        proc = self.e.run("slip", "--about", "two words", "x", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("one word", proc.stderr)
        self.assertEqual(self.e.run("slip", cwd=self.root, input="  \n").returncode, 1)
        self.assertEqual(self.e.run("slip", "--loud", "x", cwd=self.root).returncode, 1)
        self.assertEqual(self.slips(), [])


class TestSlipOnATerminal(SlipCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane
    def test_on_a_terminal_it_asks_only_for_his_words(self):
        """0.22.0: what a slip is about is the session's to judge when it
        reads the box; --about still says it."""
        proj = git_repo(self.e.tmp / "alpha")
        self.e.run("projects", "add", "alpha", str(proj), cwd=self.root, check=0)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "slip", "the", "desk", "is", "slow"], self.root,
                                   self.e.env, [])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("(--about)", seen)
        self.assertNotIn("- about: alpha", self.slips()[0].read_text())
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "slip"], self.root, self.e.env,
                                   [(b"What caused friction, in a line or two (office slip TEXT):", "the week is slow")])
        self.assertEqual(code, 0, seen)
        self.assertNotIn("(--about)", seen)
        self.assertEqual(len(self.slips()), 2)


# --- office note's check before it commits ---------------------------------------------------

class TestNoteChecksTheFiledPage(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_a_page_whose_filed_bytes_changed_is_not_committed(self):
        self.e.run("note", "first", cwd=self.root, check=0)
        page = next((self.root / "notepad").glob("2*.md"))
        head = self.e.git(self.root, "rev-parse", "HEAD")
        page.write_text(page.read_text().replace("first", "FIRST"))
        proc = self.e.run("note", "second", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("other than at its end", proc.stderr)
        self.assertIn("on disk but not committed", proc.stderr)
        self.assertIn("second", page.read_text())
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)

    def test_a_note_after_an_uncommitted_note_commits_both(self):
        self.e.run("note", "first", cwd=self.root, check=0)
        page = next((self.root / "notepad").glob("2*.md"))
        with page.open("a") as fh:
            fh.write("- 09:00 an earlier line that never got committed\n")
        self.e.run("note", "second", cwd=self.root, check=0)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_the_check(self):
        page = "notepad/x.md"
        self.assertIsNone(h.append_check(self.root, page))            # new to git
        (self.root / page).write_text("one\n")
        self.e.git(self.root, "add", page)
        self.e.git(self.root, "commit", "-qm", "x")
        self.assertIsNone(h.append_check(self.root, page))
        (self.root / page).write_text("one\ntwo\n")
        self.assertIsNone(h.append_check(self.root, page))
        (self.root / page).write_text("ONE\n")
        self.assertIn("first difference at byte 0", h.append_check(self.root, page))
        (self.root / page).unlink()
        self.assertIn("missing", h.append_check(self.root, page))
        plain = self.e.tmp / "plain"
        plain.mkdir()
        self.assertIsNone(h.append_check(plain, "x.md"))


# --- what rides with a project, and what runs after it lands ------------------------------------

class DeclarationsCase(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.manifest = self.root / "floor-plan/manifest.toml"
        self.proj = git_repo(self.e.tmp / "alpha")
        self.other = git_repo(self.e.tmp / "other", {"blueprints/b.md": "b\n"})
        self.e.run("projects", "add", "alpha", str(self.proj), cwd=self.root, check=0)
        self.e.run("projects", "add", "beta", str(git_repo(self.e.tmp / "beta")), cwd=self.root, check=0)


class TestDeclarations(DeclarationsCase):
    # No test here drives a terminal, so the class runs beside the other jobs, not in the serial lane (0.21.0).
    def test_set_and_clear_keep_every_other_byte(self):
        before = self.manifest.read_text()
        ride = str(self.other / "blueprints")
        entry = h.set_declarations(self.manifest, "alpha", [ride, ride + "/"], ["./install.sh"])
        self.assertEqual(entry["rides"], [ride])
        self.assertEqual(entry["after_land"], ["./install.sh"])
        after = self.manifest.read_text()
        self.assertEqual([l for l in after.splitlines() if l not in before.splitlines()],
                         [f'rides = ["{ride}"]', 'after_land = ["./install.sh"]'])
        self.assertEqual(h.read_projects(h.read_toml(self.manifest))[1]["rides"], [])  # beta untouched
        h.set_declarations(self.manifest, "alpha", None, ["make install", "./install.sh --no-link"])
        self.assertIn(f'rides = ["{ride}"]', self.manifest.read_text())
        h.set_declarations(self.manifest, "alpha", [], [])
        self.assertEqual(self.manifest.read_text(), before)
        after.encode("ascii")

    def test_refusals(self):
        for name, rides, after, words in (("gamma", [str(self.proj)], None, "no project named gamma"),
                                          ("alpha", [str(self.e.tmp / "gone")], None, "no such path"),
                                          ("alpha", ["relative/path"], None, "absolute or start with ~/"),
                                          ("alpha", None, ["  "], "empty"),
                                          ("alpha", None, ["a\nb"], "one line")):
            with self.assertRaises(h.HelperError) as cm:
                h.set_declarations(self.manifest, name, rides, after)
            self.assertIn(words, str(cm.exception), name)
        self.manifest.write_text(self.manifest.read_text().replace(
            "[projects.alpha]\n", f"[projects.alpha]\nrides = [\n  \"{self.e.tmp}\",\n]\n"))
        with self.assertRaises(h.HelperError) as cm:
            h.set_declarations(self.manifest, "alpha", [str(self.proj)], None)
        self.assertIn("several lines", str(cm.exception))

    def test_a_declaration_that_does_not_read_is_reported_not_fatal(self):
        self.manifest.write_text(self.manifest.read_text().replace(
            "[projects.alpha]\n", '[projects.alpha]\nrides = "not a list"\n'))
        alpha = h.read_projects(h.read_toml(self.manifest))[0]
        self.assertIsNone(alpha["problem"])
        self.assertEqual(alpha["declaration_problems"], ["rides is not a list of non-empty strings"])
        self.assertIn("declaration problem: rides", self.e.run("projects", cwd=self.root, check=0).stdout)

    def test_the_verb_with_flags_commits_only_the_floor_plan(self):
        (self.root / "notepad" / "draft.md").write_text("uncommitted\n")
        ride = str(self.other / "blueprints")
        proc = self.e.run("projects", "set", "alpha", "--ride", ride, "--after-land", "./install.sh",
                          cwd=self.root, check=0)
        self.assertIn("after it lands: ./install.sh", proc.stdout)
        self.assertEqual(self.e.git(self.root, "log", "-1", "--format=%s").strip(), "office projects: set alpha")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "?? notepad/draft.md")
        listing = self.e.run("projects", cwd=self.root, check=0).stdout
        self.assertIn(f"rides: {ride}\n", listing)
        self.assertIn("after it lands: ./install.sh\n", listing)
        self.e.run("projects", "set", "alpha", "--no-rides", cwd=self.root, check=0)
        self.assertNotIn("rides:", self.e.run("projects", cwd=self.root, check=0).stdout)
        self.assertIn("after it lands", self.e.run("projects", cwd=self.root, check=0).stdout)

    def test_add_takes_the_declarations_in_one_commit(self):
        ride = str(self.other / "blueprints")
        self.e.run("projects", "add", "gamma", str(git_repo(self.e.tmp / "gamma")), "--ride", ride,
                   "--after-land", "./install.sh", cwd=self.root, check=0)
        self.assertEqual(self.e.git(self.root, "log", "-1", "--format=%s").strip(), "office projects: add gamma")
        gamma = [p for p in h.read_projects(h.read_toml(self.manifest)) if p["name"] == "gamma"][0]
        self.assertEqual((gamma["rides"], gamma["after_land"]), ([ride], ["./install.sh"]))
        before = self.manifest.read_text()
        proc = self.e.run("projects", "add", "delta", str(git_repo(self.e.tmp / "delta")), "--ride",
                          str(self.e.tmp / "gone"), cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.manifest.read_text(), before)

    def test_piped_set_names_the_flags_it_needed(self):
        for args, words in ((("set",), "office projects set NAME"),
                            (("set", "alpha"), "--ride PATH"),
                            (("set", "alpha", "--ride", str(self.e.tmp), "--no-rides"), "contradict"),
                            (("set", "gamma", "--no-rides"), "no project named gamma")):
            proc = self.e.run("projects", *args, cwd=self.root)
            self.assertEqual(proc.returncode, 1, args)
            self.assertIn(words, proc.stderr, args)


class TestDeclarationsOnATerminal(DeclarationsCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane
    def test_the_wizard_asks_on_a_terminal(self):
        h.set_declarations(self.manifest, "alpha", None, ["./install.sh"])
        self.e.git(self.root, "commit", "-qam", "seed")
        ride = str(self.other / "blueprints")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "set", "alpha"], self.root, self.e.env, [
            (b"Keep alpha on this machine? (y/n) [y]:", ""),
            # Since 0.17.0 set also offers to keep the audience line (none).
            (b"Keep alpha without an audience? (y/n) [y]:", ""),
            (b"(--ride) [return ends the list]:", str(self.e.tmp / "gone")),
            (b"no such path on this machine", ride),
            (b"Another (--ride) [return ends the list]:", ""),
            (b"Keep what runs after alpha lands: ./install.sh? (y/n) [y]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        alpha = h.read_projects(h.read_toml(self.manifest))[0]
        self.assertEqual((alpha["rides"], alpha["after_land"]), ([ride], ["./install.sh"]))


# --- office start ---------------------------------------------------------------------------

class StartCase(unittest.TestCase):
    """An office scoping one project, alpha, that declares three
    ride-alongs (a directory inside another repo, a plain directory and a
    file outside git) and an after-land action; one folder on the desk,
    its lane on alpha. bale is the fake that packs. The world is built
    once per process and copied for each test (tests/test_office.py
    kept_setup, 0.27.0)."""

    def setUp(self):
        kept_setup(self, "test_start.StartCase", StartCase.build_world)

    def build_world(self):
        self.fake = FakePackBale(self.e.tmp)
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.root = self.e.init("home")
        self.e.found(self.root)
        self.proj = git_repo(self.e.tmp / "alpha", {"src/a.py": "a\n", "README.md": "alpha\n"})
        self.other = git_repo(self.e.tmp / "other", {"blueprints/b.md": "b\n", "notes.md": "n\n"})
        self.plain = self.e.tmp / "plain"
        self.plain.mkdir()
        (self.plain / "p.txt").write_text("p\n")
        self.loose = self.e.tmp / "loose.md"
        self.loose.write_text("a loose page\n")
        self.e.run("projects", "add", "alpha", str(self.proj), "--ride", str(self.other / "blueprints"),
                   "--ride", str(self.plain), "--ride", str(self.loose),
                   "--after-land", "touch AFTER-LAND-RAN", cwd=self.root, check=0)
        self.folder = self.e.run("open", "fix-login", "--lane", "alpha: src", "--class", "code",
                                 cwd=self.root, check=0).stdout.strip()
        self.name = self.folder.split("/")[1]
        self.trays = self.e.home / "out-tray"

    def start(self, *args, check=0, **kw):
        return self.e.run("start", *args, cwd=self.root, check=check, **kw)

    def tray(self, proc):
        line = next(l for l in proc.stdout.splitlines() if l.startswith("Out tray: "))
        return pathlib.Path(line[len("Out tray: "):])

    def folder_md(self):
        return (self.root / self.folder / "folder.md").read_text()


class TestStartOnAProject(StartCase):
    def test_one_command_packs_records_and_fills_the_tray(self):
        proc = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertRegex(sid, r"^\d{4}-\d{2}-\d{2}-fix-login-001$")
        tray = self.tray(proc)
        self.assertEqual(tray, self.trays / sid)
        # Since 0.17.0 a build session also gets the install's two page
        # templates (context-office-src-install.tar.gz).
        self.assertEqual(sorted(p.name for p in tray.iterdir()),
                         sorted([f"request-{sid}.tar.gz", "context-doctrine.tar.gz", "context-home.tar.gz",
                                 "context-office-src-install.tar.gz", "context-other.tar.gz", "context-plain.tar.gz",
                                 "loose.md"]))
        # The request is bale's own tarball, byte for byte.
        self.assertEqual((tray / f"request-{sid}.tar.gz").read_bytes(),
                         (self.proj / ".bale/outbox" / f"request-{sid}.tar.gz").read_bytes())
        self.assertEqual(tar_names(tray / "context-doctrine.tar.gz"),
                         ["doctrine/OFFICE.md", "doctrine/checks/filed-append-only.sh"])
        self.assertEqual(tar_names(tray / "context-home.tar.gz"),
                         [f"home/{self.folder}/folder.md", "home/floor-plan/survey.md", "home/profile.md"])
        self.assertEqual(tar_names(tray / "context-other.tar.gz"), ["other/blueprints/b.md"])
        self.assertEqual(tar_names(tray / "context-plain.tar.gz"), ["plain/p.txt"])
        # The session was packed in the project, with the constraint verbatim.
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(cwd, os.path.realpath(self.proj))
        self.assertEqual(argv[:3], ["pack", "Fix the login redirect", "--slug"])
        for pair in (["--write", "src"], ["--work-class", "code"],
                     ["--constraint", "Office context informs this session but never lands in this project."]):
            self.assertIn(pair, [argv[i:i + 2] for i in range(len(argv))])
        self.assertIn("--no-readme", argv)
        self.assertNotIn("--include", argv)   # the whole repo ships
        # The folder records the session and opens.
        md = self.folder_md()
        self.assertIn(f"\n- {sid}\n", md)
        self.assertIn("- status: open", md)
        self.assertIn(f"opened: {sid}", md)
        self.assertEqual(self.e.git(self.root, "log", "-1", "--format=%s").strip(),
                         f"office sessions: {sid} in {self.name}")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # The opener is bale's, printed whole.
        opener = opener_from(proc.stdout)
        self.assertEqual(opener[1], f"This message opens bale session {sid}.")
        self.assertEqual(opener[2], "Goal, verbatim from the request manifest: Fix the login redirect")
        self.assertEqual(opener[3:], ob.opener_lines(pack_fixture("office-pack")["stderr"],
                                                     ob.Consumption().surface("pack"))[3:])

    def test_nothing_is_written_into_the_install_or_a_plain_ride_along(self):
        self.start("fix-login", "--on", "alpha", "--goal", "g")
        self.assertFalse((REPO / "doctrine" / ".bale").exists())
        self.assertEqual(sorted(p.name for p in self.plain.iterdir()), ["p.txt"])
        self.assertFalse((self.other / "blueprints" / ".bale").exists())
        self.assertFalse((self.e.tmp / "AFTER-LAND-RAN").exists())
        self.assertFalse((self.proj / "AFTER-LAND-RAN").exists())

    def test_a_brief_ships_as_the_readme(self):
        brief = self.e.tmp / "brief.md"
        brief.write_text("# Brief\n\nWhy.\n")
        proc = self.start("fix-login", "--on", "alpha", "--goal", "g", "--brief", str(brief))
        (_, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertIn(["--readme-file", str(brief)], [argv[i:i + 2] for i in range(len(argv))])
        self.assertNotIn("--no-readme", argv)
        self.assertIn("then README.md", "\n".join(opener_from(proc.stdout)))

    def test_flags_override_what_the_folder_says(self):
        (self.proj / "lib").mkdir()
        (self.proj / "lib" / "x.py").write_text("x\n")
        self.start("folder 1", "--on", "alpha", "--goal", "g", "--slug", "Login Fix", "--write", "lib/",
                   "--include", "lib")
        (_, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertIn(["--slug", "login-fix"], [argv[i:i + 2] for i in range(len(argv))])
        self.assertIn(["--write", "lib"], [argv[i:i + 2] for i in range(len(argv))])
        self.assertNotIn(["--write", "src"], [argv[i:i + 2] for i in range(len(argv))])

    def test_the_out_tray_lives_where_the_machine_says(self):
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text('out_tray = "~/trays"\n')
        proc = self.start("fix-login", "--on", "alpha", "--goal", "g")
        self.assertEqual(self.tray(proc).parent, self.e.home / "trays")


class TestStartInTheOffice(StartCase):
    def test_an_office_session_forecasts_the_folder_and_the_notepad(self):
        proc = self.start("fix-login", "--in-office", "--goal", "Plan the fix")
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertTrue(sid.endswith("-fix-login-office-001"), sid)
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(cwd, os.path.realpath(self.root))
        pairs = [argv[i:i + 2] for i in range(len(argv))]
        for pair in (["--include", self.folder], ["--write", self.folder], ["--write", "notepad"]):
            self.assertIn(pair, pairs)
        self.assertNotIn("--constraint", argv)
        tray = self.tray(proc)
        self.assertIn(f"request-001/context/{self.folder}/folder.md", tar_names(tray / f"request-{sid}.tar.gz"))
        self.assertIn("request-001/context/profile.md", tar_names(tray / f"request-{sid}.tar.gz"))
        # The lane names alpha: its tree and its ride-alongs ride beside.
        self.assertEqual(sorted(p.name for p in tray.iterdir()),
                         sorted([f"request-{sid}.tar.gz", "context-doctrine.tar.gz", "context-alpha.tar.gz",
                                 "context-other.tar.gz", "context-plain.tar.gz", "loose.md"]))
        self.assertIn(f"\n- {sid}\n", self.folder_md())

    def test_office_sessions_take_turns_and_the_refusal_names_the_open_one(self):
        first = self.start("fix-login", "--in-office", "--goal", "g")
        sid = re.search(r"^Packed (\S+) for ", first.stdout, re.M).group(1)
        packs = len(self.fake.packs())
        other = self.e.run("open", "other-job", cwd=self.root, check=0).stdout.strip()
        proc = self.start("other-job", "--in-office", "--goal", "g", check=1)
        self.assertIn(f"{sid} is open in this office ({self.folder})", proc.stderr)
        self.assertIn("overlaps this one at notepad", proc.stderr)
        self.assertIn("office sessions take turns on the notepad", proc.stderr)
        self.assertEqual(len(self.fake.packs()), packs, "bale was asked after all")
        self.assertNotIn("- status: open", (self.root / other / "folder.md").read_text())
        # A read-only sitting forecasts nothing, so it may sit beside it.
        self.start("other-job", "--in-office", "--read-only", "--goal", "g")
        (_, argv) = self.fake.packs()[-1]
        self.assertIn("--read-only", argv)
        self.assertNotIn("--write", argv)
        self.assertEqual([p.name for p in self.trays.iterdir() if p.name.startswith(".")], [])


class TestStartRefusals(StartCase):
    def test_piped_it_asks_nothing_and_names_the_flag(self):
        for args, words in (((), "office start FOLDER"),
                            (("fix-login",), "--in-office, or --on PROJECT (alpha)"),
                            (("fix-login", "--on", "alpha"), "--goal TEXT"),
                            (("fix-login", "--on", "gamma", "--goal", "g"), "no such project"),
                            (("fix-login", "--in-office", "--on", "alpha"), "two places"),
                            (("fix-login", "--read-only", "--write", "x"), "takes no --write"),
                            (("nothing-like-it", "--on", "alpha", "--goal", "g"), "no folder matching"),
                            (("fix-login", "--on", "alpha", "--goal", "-x"), "dash"),
                            (("fix-login", "--on", "alpha", "--goal", "g", "--write", "nope"), "--write nope")):
            proc = self.start(*args, check=1)
            self.assertIn(words, proc.stderr, args)
        self.assertEqual(self.fake.packs(), [])
        self.assertFalse(self.trays.exists() and any(self.trays.iterdir()))
        self.assertNotIn("- status: open", self.folder_md())

    def test_a_pack_bale_refuses_leaves_no_tray_and_no_record(self):
        self.fake.refuse_next_pack()
        proc = self.start("fix-login", "--on", "alpha", "--goal", "g", check=1)
        self.assertIn("the session's pack failed, so no session was opened and no out tray was made", proc.stderr)
        self.assertIn("the fake was told to refuse", proc.stderr)
        self.assertEqual(list(self.trays.iterdir()), [])
        self.assertNotIn("- status: open", self.folder_md())

    def test_a_ride_along_gone_from_the_machine_stops_before_any_pack(self):
        shutil.rmtree(self.plain)
        proc = self.start("fix-login", "--on", "alpha", "--goal", "g", check=1)
        self.assertIn("not on this machine", proc.stderr)
        self.assertEqual([p for p in self.fake.packs() if "--context" not in p[1]], [])
        self.assertEqual(list(self.trays.iterdir()), [])

    def test_a_filed_folder_is_not_started(self):
        self.e.run("close", "fix-login", cwd=self.root, check=0)
        self.assertIn("no folder matching", self.start("fix-login", "--on", "alpha", "--goal", "g", check=1).stderr)

    def test_without_bale_it_says_so(self):
        from test_read_side import path_without_bale
        proc = self.e.run("start", "fix-login", "--on", "alpha", "--goal", "g", cwd=self.root,
                          extra={"PATH": path_without_bale()})
        self.assertEqual(proc.returncode, 1)
        self.assertIn("bale is not on PATH", proc.stderr)


class TestTheTerminalHelperOnATerminal(unittest.TestCase):
    """on_a_terminal starts its program as a terminal's foreground program
    starts (0.27.0): SIGINT and SIGQUIT at their defaults, whatever this
    process ignores, as a run in the background ignores both."""
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_the_program_starts_with_sigint_and_sigquit_at_their_defaults(self):
        e = Env(self)
        script = e.tmp / "dispositions"
        script.write_text(f"#!{sys.executable}\nimport signal\n"
                          # Python takes over SIGINT at its start only when it was not ignored.
                          "print('SIGINT', 'default' if signal.getsignal(signal.SIGINT) in "
                          "(signal.SIG_DFL, signal.default_int_handler) else 'not')\n"
                          "print('SIGQUIT', 'default' if signal.getsignal(signal.SIGQUIT) == signal.SIG_DFL else 'not')\n")
        script.chmod(0o755)
        saved = {sig: signal.signal(sig, signal.SIG_IGN) for sig in (signal.SIGINT, signal.SIGQUIT)}
        try:
            code, screen = on_a_terminal(self, [str(script)], e.tmp, e.env, [])
        finally:
            for sig, handler in saved.items():
                signal.signal(sig, handler)
        self.assertEqual(code, 0, screen)
        self.assertIn("SIGINT default", screen)
        self.assertIn("SIGQUIT default", screen)


class TestStartOnATerminal(StartCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane
    def downloads_set(self):
        """This machine's downloads, set and empty: no bundle to offer."""
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (self.e.home / "Downloads").mkdir(exist_ok=True)
        (cfg / "machine.toml").write_text(f'downloads = ["{self.e.home / "Downloads"}"]\n')

    def test_the_wizard_asks_which_job_by_key_and_the_goal_in_his_words(self):
        """0.22.0: which job, by key; where the work lands is the folder's
        lane, said and not asked; the goal is his words; what rides, rides
        as declared, said and not asked."""
        self.downloads_set()
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [
            (b"Which job, by its key (office start FOLDER):", "1"),
            (b"in your words (--goal):", "?"),
            (b"becomes the request's goal", "Fix the login redirect"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Packed ", seen)
        self.assertIn("[1] folder 1, fix-login", seen)
        self.assertIn("[2] a new job, in your own words", seen)
        self.assertIn("the work lands on alpha, the project the folder's lane names", seen)
        self.assertIn("what rides with alpha, as declared:", seen)
        for gone in ("Where the work lands", "Which ride", "Paths in"):
            self.assertNotIn(gone, seen)
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(cwd, os.path.realpath(self.proj))
        self.assertEqual(argv[1], "Fix the login redirect")

    def test_new_opens_a_folder_from_his_words_and_asks_no_goal_again(self):
        self.downloads_set()
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "--in-office"],
                                   self.root, self.e.env, [
            (b"(office start FOLDER):", "2"),
            (b"The job, in your own words", "Write the plan\n"),
            (b"[keep]: ", ""),  # 0.33.0: the answer is shown whole, and a plain return keeps it
        ])
        self.assertEqual(code, 0, seen)
        md = next(self.root.glob("desk/*-write-the-plan/folder.md")).read_text()
        self.assertIn("- status: open", md)
        self.assertIn("- goal: Write the plan", md)
        self.assertNotIn("(--goal)", seen)
        self.assertNotIn("Which project", seen)
        (_, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(argv[1], "Write the plan")


# --- the desktop the suite never touches (0.20.1) -----------------------------------------------------

class TestStartOnAnImitatedWsl(StartCase):
    """office start on a terminal, on a machine that is WSL to the office
    and holds clip.exe and explorer.exe on its PATH, as a WSL machine
    does. Under the suite's Env, neither runs: the Env's desktop is the
    only place the office looks for them, and it holds none. Pointed at
    the fakes, the same start reaches both, so the imitation is the real
    path: the opener fed to clip.exe as UTF-16, explorer.exe opened in
    the out tray.

    The command runs under a stand-in for the occupant's shell, which
    holds the terminal's session and outlives it. Run as the session's
    leader itself (as on_a_terminal runs a command), the office's exit
    hangs up the terminal and the program it started in the background
    dies before it runs: most likely why the suite, before 0.20.1,
    started explorer.exe on a WSL machine and no window opened."""
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def setUp(self):
        super().setUp()
        self.windows, self.calls = recording_windows(self.e.tmp / "windows", clip_sets_clipboard=True)
        # The shell: runs the command, then lingers up to three seconds
        # while a program the command started has not said it ran.
        self.shell = self.e.tmp / "shell"
        self.shell.write_text(f'#!/bin/sh\n"$@"; s=$?\nn=0\nwhile [ $n -lt 30 ] && '
                              f'! grep -q "^explorer.exe" {self.calls} 2>/dev/null; do sleep 0.1; n=$((n + 1)); done\n'
                              f'exit $s\n')
        self.shell.chmod(0o755)

    def start_on_a_terminal(self, env):
        return on_a_terminal(self, [str(self.shell), str(self.e.office_bin), "start", "fix-login", "--on", "alpha",
                                    "--goal", "Fix the login redirect"], self.root, env, [])

    def test_under_the_suites_env_no_clipboard_is_written_and_no_file_manager_opens(self):
        code, seen = self.start_on_a_terminal(imitate_wsl(self.e, self.windows))
        self.assertEqual(code, 0, seen)
        self.assertIn("Packed ", seen)
        self.assertFalse(self.calls.exists(), self.calls.read_text() if self.calls.exists() else "")
        self.assertNotIn("is on the clipboard", seen)
        # A copy not made is said, never skipped silently (0.23.0).
        self.assertIn("the opener is not on the clipboard: this machine names no clipboard command", seen)
        self.assertNotIn("opened the out tray", seen)

    def test_pointed_at_the_fakes_the_same_start_reaches_both(self):
        env = dict(imitate_wsl(self.e, self.windows), OFFICE_DESKTOP_PATH=str(self.windows))
        code, seen = self.start_on_a_terminal(env)
        self.assertEqual(code, 0, seen)
        screen = seen.replace("\r\n", "\n")
        # 0.23.0: the copy is read back (Get-Clipboard, through the fake
        # powershell.exe) and held to the opener before it is claimed.
        self.assertIn(f"the opener is on the clipboard ({self.windows / 'clip.exe'}; read back and checked)", screen)
        self.assertIn(f"opened the out tray with {self.windows / 'explorer.exe'}", screen)
        fed = (self.windows / "clip.exe.in").read_bytes().decode("utf-16-le")
        self.assertEqual(fed.splitlines(), opener_from(screen))
        tray = pathlib.Path(re.search(r"^Out tray: (\S+)$", screen, re.M).group(1))
        lines = sorted(self.calls.read_text().splitlines())
        self.assertEqual(lines[0], f"clip.exe  (in {os.path.realpath(self.root)})")
        self.assertEqual(lines[1], f"explorer.exe . (in {os.path.realpath(tray)})")

