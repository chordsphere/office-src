"""Tests for the suite's clock (office-src 0.17.1): the rule that no test
reads the running machine, the fast tier tests/fast-tier.toml declares,
the runner's isolated jobs and per-test times, and the detached run of the
whole suite.

The rule. Env (tests/test_office.py) is the one place a test's HOME,
TMPDIR, XDG_CONFIG_HOME, downloads and desktop are said; the runner gives
every job, and the --serial run, a HOME and TMPDIR of its own besides. A
test file that names the machine's own temporary directory, expands ~,
reads HOME itself, reads the kernel's version (the WSL check) or looks a
program up on the PATH, outside Env, fails TestNoTestReadsTheMachine,
unless the line is one of ALLOWED, each with its reason: text a fake host
runs under its own HOME and TMPDIR. (The paths a probe printed, which the
land fake swaps out of what it replays, are read from each fixture's own
cwd since 0.27.0, so no test file names them.) An allowance that no longer matches anything fails too,
so the list cannot outlive what it excuses.

The office's own source is held to the same two reads (0.20.1), since a
test of the command reads whatever the command reads: bin/office and
lib/ read the kernel's version only as OFFICE_PROC_VERSION's default, and
every program they look up on the PATH is one the runner declares
(runner.DECLARED_TOOLS: git, python3, a shell, the coreutils, iconv),
the suite's fake (FAKED), or a desktop program found through the one door
the Env steers (bin/office desktop_tool, lib/office_helper.py
desktop_which), never through a lookup of its own; SOURCE_ALLOWED holds
the lookups by a variable, each with its reason. So the next session that
adds a lookup of something.exe meets TestTheOfficeReadsTheDesktopThroughItsDoors.

Every pattern here is written with one letter bracketed (t[m]p), the way
share/letterhead.toml writes its names, so this file never spells what it
refuses and is held to its own rule. Run with the rest of the suite:

    tests/run.sh test_suite_clock
"""

import ast
import inspect
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import FAKES, REPO, WSL_KERNEL, Env, fake_program, h  # noqa: E402

import runner  # noqa: E402

TESTS = REPO / "tests"

# What a test file may not name outside Env: what each pattern catches.
RULE = (
    ("the machine's temporary directory", re.compile(r"(?<![\w$}])/t[m]p(?![\w-])")),
    ("expand[u]ser", re.compile(r"\bexpand[u]ser\b")),
    ("Path.ho[m]e(", re.compile(r"\bPath\.ho[m]e\(")),
    ("$H[O]ME", re.compile(r"\$\{?H[O]ME\b")),
    ("gettemp[d]ir(", re.compile(r"\bgettemp[d]ir\(")),
    ("H[O]ME read from the environment", re.compile(r"""(?:environ(?:\.get\(|\[)|getenv\()\s*["']H[O]ME["']""")),
    # 0.20.1: the WSL check's file, and a program looked up on the PATH (a
    # WSL machine's holds clip.exe, explorer.exe and powershell.exe).
    ("the kernel's version, /pr[o]c/version", re.compile(r"/pr[o]c/version\b")),
    ("a program looked up on the PATH", re.compile(r"\bshutil\.wh[i]ch\(|\bcommand\s+-[v]\b|\btype\s+-[P]\b")),
)

# (module, the span allowed, why). The span is blanked before the rule
# reads the line; nothing else on the line is excused.
ALLOWED = (
    ("test_out_trip_to_host", r"\$H[O]ME/\.local/bin",
     "the fake host's own upgrade.sh: the fake ssh runs it with the host's HOME, under the case's temporary tree"),
    ("test_out_trip_to_host", r"\$\{TMPDIR:-/t[m]p\}",
     "the same script's scratch directory, under the TMPDIR the fake ssh gives every host it knows"),
    ("test_return_trip", r'echo "\$H[O]ME" > AFTER-LAND-HOME',
     "an after-land action the fake host runs, to prove it ran with the host's own HOME"),
    ("test_return_trip", r'\\"\$H[O]ME\\"',
     "the text office writes for a host's shell, compared as text: nothing here expands it"),
)


def env_lines(path):
    """The line numbers of class Env, where the rule's words belong."""
    src = path.read_text(encoding="utf-8")
    for node in ast.parse(src).body:
        if isinstance(node, ast.ClassDef) and node.name == "Env":
            return set(range(node.lineno, node.end_lineno + 1))
    return set()


def breaches(paths, allowed=ALLOWED):
    """(every breach as 'file:line: what: text', the allowances that matched
    nothing) over the given test files."""
    out, used = [], set()
    for path in paths:
        exempt = env_lines(path) if path.name == "test_office.py" else set()
        mine = [(i, re.compile(span)) for i, (mod, span, _) in enumerate(allowed) if mod == path.stem]
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if n in exempt:
                continue
            for i, pat in mine:
                if pat.search(line):
                    used.add(i)
                    line = pat.sub(lambda m: " " * len(m.group(0)), line)
            for what, pat in RULE:
                if pat.search(line):
                    out.append(f"{path.name}:{n}: {what}: {line.strip()}")
    stale = [allowed[i] for i in range(len(allowed)) if i not in used and allowed[i][0] in {p.stem for p in paths}]
    return out, stale


# --- the office's own source: the kernel's version and the PATH, through their doors (0.20.1) ---

# What the office looks up on the PATH that is the suite's own: a fake in
# the test's tree, first on its PATH. (name, why)
FAKED = (
    ("bale", "the suite's fake bale (tests/fakes/, run by a program in the test's own tree), first on the PATH of "
             "every test that runs one; tests/test_read_side.py takes it away to say bale is missing"),
)

# (source file's name, the span allowed, why): lookups by a variable, and
# the doors themselves. Blanked before the rule reads the line, as ALLOWED.
SOURCE_ALLOWED = (
    ("office", r'command -[v] "\$t" >/dev/null 2>&1 \|\| die "\$t is required',
     "require_tools itself: each name its callers give it is checked as a lookup of its own"),
    ("office", r'command -[v] "\$name" 2>/dev/null',
     "survey_which, the survey's door (0.27.0): its Tools facts (bale, git, python3, R, quarto, node) and which "
     "bale and office the PATH runs, looked up on the PATH only when OFFICE_SURVEY_PATH is unset; every Env and "
     "every job sets it to \"\", so no test reaches this line"),
    ("office_helper", r"shutil\.wh[i]ch\(name, path=dirs\)",
     "desktop_which, the door itself: it searches OFFICE_DESKTOP_PATH, which every Env points at its own desktop"),
    ("office_helper", r'(?<![\w.])wh[i]ch\((?:"powershell\.exe"|tool)\)',
     "paste_candidate's lookups, through desktop_which unless a unit test hands it a which of its own"),
)

# A lookup on the PATH, and the name it looks up: bash's command -[v] and
# type -[P] (and the names require_tools is given), Python's shutil.wh[i]ch
# and a bare wh[i]ch(. A name with a $ in it is a variable.
BASH_LOOKUP = re.compile(r"(?<![\w-])(?:command\s+-[v]|type\s+-[Pp])\s+([^\s;|&)]+)")
BASH_REQUIRE = re.compile(r"^\s*require_tools\s+([^;|&]+)")
PY_LOOKUP = re.compile(r"(?<![\w])(?:shutil\.)?wh[i]ch\(\s*([^,)]+)")


def source_files():
    return [REPO / "bin" / "office", *sorted((REPO / "lib").glob("*.py"))]


def lookups(path, text, allowed=SOURCE_ALLOWED):
    """(every lookup as (line, name, the line's text) with name None for a
    variable, the allowances that matched) over one source file's text;
    comment lines are not read."""
    mine = [(i, re.compile(span)) for i, (name, span, _) in enumerate(allowed) if name == path.stem]
    out, used = [], set()
    for n, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        for i, pat in mine:
            if pat.search(line):
                used.add(i)
                line = pat.sub(lambda m: " " * len(m.group(0)), line)
        if path.suffix == ".py":
            found = [m.group(1).strip() for m in PY_LOOKUP.finditer(line)]
            names = [f[1:-1] if f[:1] in "\"'" and f[-1:] == f[:1] else None for f in found]
        else:
            names = [m.group(1) for m in BASH_LOOKUP.finditer(line)]
            r = BASH_REQUIRE.match(line)
            if r:
                names += r.group(1).split()
            names = [None if "$" in w else w.strip("\"'") for w in names]
        out += [(n, name, line.strip()) for name in names]
    return out, used


def lookup_breaches(paths, allowed=SOURCE_ALLOWED, declared=None, faked=None):
    """(every lookup of a program that is neither declared nor faked nor a
    variable the allowances excuse, as 'file:line: name: text'; the
    allowances that matched nothing)."""
    declared = set(runner.DECLARED_TOOLS if declared is None else declared)
    faked = {name for name, _ in (FAKED if faked is None else faked)}
    out, used = [], set()
    for path in paths:
        found, matched = lookups(path, path.read_text(encoding="utf-8"), allowed)
        used |= matched
        for n, name, line in found:
            if name is None or name not in declared | faked:
                out.append(f"{path.name}:{n}: {name or 'a variable'}: {line}")
    stems = {p.stem for p in paths}
    stale = [allowed[i] for i in range(len(allowed)) if i not in used and allowed[i][0] in stems]
    return out, stale


def office_functions(*names):
    """bin/office's definitions of the named shell functions, to run alone."""
    src = (REPO / "bin" / "office").read_text(encoding="utf-8")
    out = []
    for name in names:
        m = re.search(rf"^{name}\(\) \{{\n.*?^\}}\n", src, re.M | re.S)
        assert m, f"bin/office defines no {name}"
        out.append(m.group(0))
    return "".join(out)


def entry_call(verb):
    """A call of the command with verb as its first word (help and
    version by any of their spellings), or with no word for the walk-in."""
    if verb == runner.WALK_IN:
        return r"(?:\.run|run_office)\((?:\s*\)|\s*cwd=|\s*check=)"
    spellings = {"version": ("version", "--version", "-V"), "help": ("help", "--help", "-h")}.get(verb, (verb,))
    word = "(?:" + "|".join(re.escape(s) for s in spellings) + ")"
    return (rf'(?:(?:\.run|run_office|\.office)\(\s*"{word}"|office"\),\s*"{word}"'
            rf'|\bself(?:\.\w+)?\.{word}\()')


def test_files():
    """Every test module, and the fake programs' modules they run
    (tests/fakes/, 0.27.0): a fake runs under the test's Env too."""
    return sorted(TESTS.glob("test*.py")) + sorted((TESTS / "fakes").glob("*.py"))


class TestNoTestReadsTheMachine(unittest.TestCase):
    def test_no_test_file_names_the_machines_own_outside_env(self):
        found, stale = breaches(test_files())
        self.assertEqual(found, [], "a test names the running machine's own; give it the Env's (self.e.home, "
                                    "self.e.tmpdir, self.e.downloads, Env.this_process()) instead")
        self.assertEqual(stale, [], "an allowance matches nothing any more; take it out of ALLOWED")

    def test_the_rule_catches_each_way_of_reaching_the_machine(self):
        d = pathlib.Path(Env(self).tmp)
        lines = ['x = pathlib.Path("/t' 'mp").glob("a*")', 'os.path.expand' 'user("~/x")', 'pathlib.Path.ho' 'me()',
                 's = "$H' 'OME/bin"', 's = "${H' 'OME}"', 'tempfile.gettemp' 'dir()', 'os.environ["H' 'OME"]',
                 'os.environ.get("H' 'OME")', 'os.getenv("H' 'OME")', 'run(["ls", "/t' 'mp"])',
                 'wsl = "microsoft" in open("/pr' 'oc/version").read()', 'exe = shutil.wh' 'ich("clip.exe")',
                 'run(["sh", "-c", "comm' 'and -v powershell.exe"])', 'run(["bash", "-c", "type -' 'P xclip"])']
        f = d / "test_probe_rule.py"
        f.write_text("\n".join(lines) + "\n")
        found, _ = breaches([f], allowed=())
        self.assertEqual([b.split(":")[1] for b in found], [str(n) for n in range(1, len(lines) + 1)], found)
        # What only looks like it: a path under another directory, a
        # variable's own tmp, the Env's attributes.
        f.write_text('a = "$target/t' 'mp"\nb = self.e.tmp / "x"\nc = "/t' 'mpfs"\nd = self.e.home\n'
                     'e = self.e.desktop / "clip.exe"\nf = h.desktop_wh' 'ich("clip.exe")\n')
        self.assertEqual(breaches([f], allowed=())[0], [])

    def test_env_is_the_one_place_and_an_allowance_excuses_its_span_alone(self):
        d = pathlib.Path(Env(self).tmp)
        f = d / "test_office.py"
        f.write_text('class Env:\n    p = "/t' 'mp"\n\nq = "/t' 'mp"\n')
        self.assertEqual([b.split(":")[1] for b in breaches([f], allowed=())[0]], ["4"])
        g = d / "test_land.py"
        g.write_text('a = "/t' 'mp/office-probe.ab12/x"\nb = "/t' 'mp/office-probe.ab12/x", "/t' 'mp"\n')
        # The allowance test_land held until 0.27.0, as an example.
        allowed = (("test_land", r"/t[m]p/office-probe\.\w+", "a probe's paths, as the fixtures hold them"),)
        found, stale = breaches([g], allowed=allowed)
        self.assertEqual([b.split(":")[1] for b in found], ["2"])
        self.assertEqual(stale, [])
        g.write_text("nothing here\n")
        self.assertEqual([a[0] for a in breaches([g], allowed=allowed)[1]], ["test_land"])

    def test_env_gives_each_test_its_own_home_tmpdir_config_and_downloads(self):
        a, b = Env(self), Env(self)
        for e in (a, b):
            for key in ("HOME", "TMPDIR", "XDG_CONFIG_HOME"):
                self.assertTrue(pathlib.Path(e.env[key]).is_relative_to(e.tmp), key)
            self.assertTrue(pathlib.Path(e.env["TMPDIR"]).is_dir())
            self.assertTrue(e.downloads.is_relative_to(e.home))
            self.assertEqual(e.env["OFFICE_WINDOWS_USERS"], "")
            self.assertNotIn("XDG_DOWNLOAD_DIR", e.env)
            self.assertEqual((e.env["OFFICE_PROC_VERSION"], e.env["OFFICE_DESKTOP_PATH"]), ("", str(e.desktop)))
            self.assertTrue(e.desktop.is_relative_to(e.tmp))
        self.assertNotEqual(a.env["HOME"], b.env["HOME"])
        # A command run through it makes its temporary files there.
        out = subprocess.run(["sh", "-c", 'mktemp -d "${TMPDIR:?}/x.XXXXXX"'], env=a.env, capture_output=True,
                             text=True, check=True).stdout.strip()
        self.assertTrue(pathlib.Path(out).is_relative_to(a.tmpdir), out)

    def test_this_process_lends_the_env_and_gives_it_back(self):
        import tempfile
        e = Env(self)
        before = (dict(os.environ), tempfile.tempdir)
        with e.this_process():
            self.assertEqual(h.expand_project_path("~/x"), e.home / "x")
            self.assertTrue(pathlib.Path(tempfile.mkdtemp()).is_relative_to(e.tmpdir))
            self.assertEqual(os.environ["XDG_CONFIG_HOME"], e.env["XDG_CONFIG_HOME"])
        self.assertEqual((dict(os.environ), tempfile.tempdir), before)

    def test_every_job_runs_with_a_home_and_tmpdir_of_its_own(self):
        e = Env(self)
        base = {"PATH": "/usr/bin:/bin", "HOME": "/home/someone", "TMPDIR": "/var/x", "XDG_DOWNLOAD_DIR": "/d",
                "XDG_CONFIG_HOME": "/home/someone/.config", "OFFICE_ROOT": "/home/someone/office",
                "OFFICE_DEBUG": "1", "OFFICE_TEST_JOBS": "2", "LC_ALL": "C.UTF-8",
                "OFFICE_DESKTOP_PATH": "/mnt/c/WINDOWS/system32", "OFFICE_PROC_VERSION": "/x/version",
                "OFFICE_SURVEY_PATH": "/usr/local/bin", "OFFICE_CONTAINER_MARKER": "/x/marker"}
        env = runner.isolated_env(base, e.tmp / "job")
        for key in ("HOME", "TMPDIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME",
                    "GIT_CONFIG_GLOBAL"):
            self.assertTrue(pathlib.Path(env[key]).is_relative_to(e.tmp / "job"), key)
            self.assertTrue(pathlib.Path(env[key]).exists(), key)
        self.assertEqual(pathlib.Path(env["GIT_CONFIG_GLOBAL"]).read_text(), "")
        for gone in ("XDG_DOWNLOAD_DIR", "OFFICE_ROOT", "OFFICE_DEBUG"):
            self.assertNotIn(gone, env)
        self.assertEqual((env["PATH"], env["LC_ALL"], env["OFFICE_TEST_JOBS"], env["OFFICE_WINDOWS_USERS"],
                          env["GIT_CONFIG_NOSYSTEM"]), ("/usr/bin:/bin", "C.UTF-8", "2", "", "1"))
        self.assertEqual(env["OFFICE_TESTS_UNDER_RUNNER"], "1")
        # Not WSL, and no desktop program anywhere: a job never writes the
        # clipboard or opens a file manager, whatever the caller said.
        self.assertEqual((env["OFFICE_PROC_VERSION"], env["OFFICE_DESKTOP_PATH"]), ("", ""))
        self.assertEqual(runner.DESKTOP_VARS, {"OFFICE_PROC_VERSION": "", "OFFICE_DESKTOP_PATH": ""})
        # No tool for the survey to find, and no container marker (0.27.0).
        self.assertEqual((env["OFFICE_SURVEY_PATH"], env["OFFICE_CONTAINER_MARKER"]), ("", ""))
        self.assertEqual(runner.SURVEY_VARS, {"OFFICE_SURVEY_PATH": "", "OFFICE_CONTAINER_MARKER": ""})
        # This very test runs in such a job when the runner runs it: its
        # TMPDIR (and HOME beside it) is the runner's scratch, not the one
        # the runner was started with. Under bare unittest discover there
        # is no runner to say, and nothing to check.
        if os.environ.get("OFFICE_TESTS_UNDER_RUNNER"):
            self.assertIn("office-tests-scratch.", os.environ.get("TMPDIR", ""))


# A plain Linux kernel's version string, beside test_office's WSL one, for
# the files a test points OFFICE_PROC_VERSION at.
LINUX_KERNEL = "Linux version 6.8.0-45-generic (buildd@lcy02) (gcc 13.2.0) #45-Ubuntu SMP\n"


def fake_windows(d):
    """A directory of fake Windows programs, as WSL puts them on the PATH:
    clip.exe, explorer.exe and powershell.exe, each exiting 0, and one
    file that is not executable."""
    d.mkdir(parents=True)
    for name in ("clip.exe", "explorer.exe", "powershell.exe"):
        (d / name).write_text("#!/bin/sh\nexit 0\n")
        (d / name).chmod(0o755)
    (d / "notes.exe").write_text("not a program\n")
    return d


class TestTheDesktopDoors(unittest.TestCase):
    """The two reads the desktop steps make, each from one place the
    environment steers: whether this machine is WSL (OFFICE_PROC_VERSION)
    and where its desktop programs are (OFFICE_DESKTOP_PATH), on both sides
    of the office: bin/office (on_wsl, desktop_tool) and the helper
    (machine_is_wsl, desktop_which, paste_candidate)."""

    def setUp(self):
        self.e = Env(self)
        self.windows = fake_windows(self.e.tmp / "windows")
        self.wsl = self.e.tmp / "wsl-version"
        self.wsl.write_text(WSL_KERNEL)
        self.linux = self.e.tmp / "linux-version"
        self.linux.write_text(LINUX_KERNEL)
        # The office's view with the fake Windows programs on the PATH, as
        # on a WSL machine; the Env's desktop is still the only door.
        self.on_path = dict(self.e.env, PATH=f"{self.windows}{os.pathsep}{self.e.env['PATH']}")

    def bash(self, call, env):
        return subprocess.run(["bash", "-c", office_functions("on_wsl", "desktop_tool") + call], env=env,
                              capture_output=True, text=True, timeout=30)

    def test_the_env_says_not_wsl_and_holds_an_empty_desktop_first_on_the_path(self):
        self.assertEqual(self.e.env["OFFICE_PROC_VERSION"], "")
        self.assertEqual(self.e.env["OFFICE_DESKTOP_PATH"], str(self.e.desktop))
        self.assertTrue(self.e.desktop.is_relative_to(self.e.tmp))
        self.assertEqual(list(self.e.desktop.iterdir()), [])
        self.assertEqual(self.e.env["PATH"].split(os.pathsep)[0], str(self.e.desktop))
        with self.e.this_process():
            self.assertFalse(h.machine_is_wsl())
            self.assertIsNone(h.desktop_which("clip.exe"))
        # Even with WSL's programs on the PATH, the office finds none.
        self.assertIsNone(h.desktop_which("clip.exe", self.on_path))
        self.assertEqual(self.bash("desktop_tool clip.exe", self.on_path).returncode, 1)
        self.assertEqual(self.bash("on_wsl", dict(self.e.env, OFFICE_PROC_VERSION=str(self.wsl))).returncode, 0)

    def test_the_wsl_check_reads_the_one_file_the_environment_names(self):
        for source, wsl in ((self.wsl, True), (self.linux, False), ("", False), (self.e.tmp / "absent", False)):
            env = dict(self.e.env, OFFICE_PROC_VERSION=str(source))
            self.assertEqual(h.machine_is_wsl(env), wsl, source)
            self.assertEqual(self.bash("on_wsl", env).returncode, 0 if wsl else 1, source)

    def test_a_desktop_program_is_found_only_where_the_door_looks(self):
        empty = self.e.tmp / "empty"
        empty.mkdir()
        for dirs, found in ((f"{empty}{os.pathsep}{os.pathsep}{self.windows}", self.windows / "clip.exe"),
                            (str(empty), None), ("", None)):
            env = dict(self.on_path, OFFICE_DESKTOP_PATH=dirs)
            self.assertEqual(h.desktop_which("clip.exe", env), str(found) if found else None, dirs)
            proc = self.bash("desktop_tool clip.exe", env)
            self.assertEqual((proc.returncode, proc.stdout), (0, f"{found}\n") if found else (1, ""), dirs)
        # Unset, the door is the PATH; a file that is not a program is no program.
        env = {k: v for k, v in self.on_path.items() if k != "OFFICE_DESKTOP_PATH"}
        self.assertEqual(h.desktop_which("explorer.exe", env), str(self.windows / "explorer.exe"))
        self.assertEqual(self.bash("desktop_tool explorer.exe", env).stdout, f"{self.windows / 'explorer.exe'}\n")
        self.assertIsNone(h.desktop_which("notes.exe", env))
        self.assertEqual(self.bash("desktop_tool notes.exe", env).returncode, 1)

    def test_the_paste_candidate_takes_both_reads_from_the_environment(self):
        wsl = dict(self.on_path, OFFICE_PROC_VERSION=str(self.wsl))
        # The Env's own view of an imitated WSL machine: nothing offered.
        self.assertIsNone(h.paste_candidate(environ=wsl))
        # Its desktop holding a reader: that reader, not the machine's PowerShell.
        (self.e.desktop / "wl-paste").write_text("#!/bin/sh\n")
        (self.e.desktop / "wl-paste").chmod(0o755)
        self.assertEqual(h.paste_candidate(environ=wsl), "wl-paste --no-newline")
        # Pointed at the Windows programs, it is WSL's line; not WSL, the reader's.
        self.assertEqual(h.paste_candidate(environ=dict(wsl, OFFICE_DESKTOP_PATH=str(self.windows))), h.WSL_PASTE)
        both = f"{self.windows}{os.pathsep}{self.e.desktop}"
        self.assertEqual(h.paste_candidate(environ=dict(wsl, OFFICE_DESKTOP_PATH=both,
                                                        OFFICE_PROC_VERSION=str(self.linux))),
                         "wl-paste --no-newline")
        # The command's own call reads the same two (office probe asks the helper).
        (self.e.desktop / "wl-paste").unlink()
        machine = self.e.home / ".config" / "office-src" / "machine.toml"
        proc = subprocess.run([sys.executable, "-B", str(REPO / "lib" / "office_helper.py"), "paste-command",
                               str(machine), "--candidate"], env=wsl, capture_output=True, text=True, timeout=30)
        self.assertEqual((proc.returncode, proc.stdout), (3, ""), proc.stderr)


def recording_tool(d, name, line):
    """A program d/name that prints line to --version and records that it
    ran, as d/ran-NAME; returns d."""
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(f"#!/bin/sh\necho ran >> '{d / ('ran-' + name)}'\necho '{line}'\n")
    (d / name).chmod(0o755)
    return d


class TestTheSurveysDoors(unittest.TestCase):
    """The survey's own reads of the machine (0.27.0), each from one place
    the environment steers, as the desktop's are: the tools it records and
    the bale and office the PATH runs (OFFICE_SURVEY_PATH, through
    survey_which) and the container marker (OFFICE_CONTAINER_MARKER,
    through container_marker)."""

    def setUp(self):
        self.e = Env(self)
        self.tools = recording_tool(self.e.tmp / "tools", "node", "v20.0.0")
        (self.tools / "quarto").write_text("not a program\n")
        self.elsewhere = recording_tool(self.e.tmp / "elsewhere", "node", "v18.0.0")

    def bash(self, call, env):
        return subprocess.run(["bash", "-c", "VERSION_TIMEOUT=5\n" + office_functions(
            "survey_which", "container_marker", "tool_version") + call], env=env,
            capture_output=True, text=True, timeout=30)

    def test_the_env_and_every_job_look_for_no_tool_and_no_marker(self):
        self.assertEqual((self.e.env["OFFICE_SURVEY_PATH"], self.e.env["OFFICE_CONTAINER_MARKER"]), ("", ""))
        # Even with a tool first on the PATH, the Env's survey finds none and runs none.
        env = dict(self.e.env, PATH=f"{self.tools}{os.pathsep}{self.e.env['PATH']}")
        proc = self.bash('tool_version node; echo; survey_which git || echo "git: none"; container_marker || echo no',
                         env)
        self.assertEqual(proc.stdout, "not found\ngit: none\nno\n", proc.stderr)
        self.assertFalse((self.tools / "ran-node").exists())

    def test_a_tool_is_found_only_where_the_door_looks_and_the_found_one_runs(self):
        env = dict(self.e.env, PATH=f"{self.elsewhere}{os.pathsep}{self.e.env['PATH']}",
                   OFFICE_SURVEY_PATH=f"{self.e.tmp / 'empty'}{os.pathsep}{os.pathsep}{self.tools}")
        proc = self.bash("tool_version node; echo; tool_version quarto; echo; survey_which node", env)
        self.assertEqual(proc.stdout, f"v20.0.0 ({self.tools / 'node'})\nnot found\n{self.tools / 'node'}\n",
                         proc.stderr)
        self.assertTrue((self.tools / "ran-node").exists())
        self.assertFalse((self.elsewhere / "ran-node").exists())
        # Unset, the door is the PATH, as the survey read it before 0.27.0.
        env.pop("OFFICE_SURVEY_PATH")
        proc = self.bash("tool_version node", env)
        self.assertEqual(proc.stdout, f"v18.0.0 ({self.elsewhere / 'node'})", proc.stderr)

    def test_the_container_marker_is_the_one_file_the_environment_names(self):
        marker = self.e.tmp / "marker"
        marker.write_text("")
        for value, container in ((str(marker), True), ("", False), (str(self.e.tmp / "absent"), False)):
            env = dict(self.e.env, OFFICE_CONTAINER_MARKER=value)
            self.assertEqual(self.bash("container_marker", env).returncode, 0 if container else 1, value)

    def test_the_survey_reads_the_machine_only_through_its_doors(self):
        body = re.search(r"^gather_facts\(\) \{\n.*?^\}\n", (REPO / "bin" / "office").read_text(encoding="utf-8"),
                         re.M | re.S).group(0)
        self.assertNotIn("comm" "and -v", body)
        self.assertNotIn("/.dock" "erenv", body)
        self.assertIn("container_marker", body)
        self.assertIn("survey_which bale", body)
        self.assertIn("survey_which office", body)


class TestTheOfficeReadsTheDesktopThroughItsDoors(unittest.TestCase):
    def test_the_kernels_version_is_read_once_on_each_side_as_a_default(self):
        found = {}
        for path in source_files():
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if "/pr" "oc/version" in line:
                    self.assertIn("OFFICE_PROC_VERSION", line, f"{path.name}:{n} reads the kernel's version itself; "
                                                                "ask on_wsl or machine_is_wsl")
                    found.setdefault(path.name, []).append(n)
        self.assertEqual(sorted(found), ["office", "office_helper.py"], found)
        self.assertTrue(all(len(v) == 1 for v in found.values()), found)

    def test_every_program_the_office_looks_up_is_declared_faked_or_behind_the_door(self):
        found, stale = lookup_breaches(source_files())
        self.assertEqual(found, [], "the office looks a program up on the PATH that the runner does not declare "
                                    "(tests/runner.py DECLARED_TOOLS) and the suite does not fake: a desktop "
                                    "program goes through desktop_tool or desktop_which, which the Env steers")
        self.assertEqual(stale, [], "an allowance matches nothing any more; take it out of SOURCE_ALLOWED")
        self.assertTrue({"git", "python3", "bash", "timeout", "iconv"} <= set(runner.DECLARED_TOOLS))

    def test_the_source_rule_catches_each_way_of_looking_a_program_up(self):
        d = Env(self).tmp
        office = d / "office"
        bad = ['x="$(comm' 'and -v clip.exe)"', "type -" "P explorer.exe", 'comm' 'and -v "$tool" >/dev/null',
               "  require_tools git wl-paste", "if comm" "and -v xclip >/dev/null; then :; fi"]
        good = ["# comm" "and -v clip.exe, in a comment", 'clip="$(desktop_tool clip.exe)"',
                "comm" "and -v git >/dev/null", "  require_tools git python3 timeout", "comm" "and -v bale"]
        office.write_text("\n".join(bad + good) + "\n")
        found, _ = lookup_breaches([office], allowed=())
        self.assertEqual([b.split(":")[1] for b in found], ["1", "2", "3", "4", "5"], found)
        self.assertIn("office:4: wl-paste:", found[3])
        helper = d / "office_helper.py"
        helper.write_text("a = shutil.wh" "ich('powershell.exe')\nb = wh" "ich(name)\n"
                          "c = desktop_wh" "ich('clip.exe')\nd = shutil.wh" "ich('git')\n")
        found, _ = lookup_breaches([helper], allowed=())
        self.assertEqual([b.split(":")[1] for b in found], ["1", "2"], found)
        # An allowance excuses its span alone, and one that matches nothing is stale.
        found, stale = lookup_breaches([office], allowed=(("office", r"type -[P] explorer\.exe", "why"),))
        self.assertNotIn("2", [b.split(":")[1] for b in found])
        self.assertEqual(stale, [])
        self.assertEqual(lookup_breaches([helper], allowed=(("office_helper", r"nothing", "why"),))[1],
                         [("office_helper", r"nothing", "why")])


class TestTheFastTier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tier = runner.load_tier()
        cls.verbs = runner.dispatcher_verbs()
        cls.jobs = runner.plan(runner.module_names())
        cls.ids = {i for v in cls.jobs.values() for i in v}

    def test_the_tier_holds_together(self):
        self.assertEqual(runner.tier_problems(self.tier, self.ids, self.verbs), [])
        self.assertEqual(self.tier["budget_seconds"], 120)

    def test_every_verb_the_command_dispatches_has_an_entry_point(self):
        self.assertGreaterEqual(len(self.verbs), 30)
        for verb in ("walk-in", "init", "start", "land", "deliver", "letterhead", "version", "help", "tour"):
            self.assertIn(verb, self.verbs)
        self.assertEqual(set(self.tier["entry_points"]), self.verbs)

    def test_each_entry_point_test_runs_its_verb(self):
        """Each named test is one test, by its id, whose own source calls
        the command with the verb as its first word, through the suite's
        helpers (e.run("land", ...), run_office, an Office's run), a helper
        named for the verb (self.start(...), self.o.open(...)) or a
        command line ([.../office, "version"]): the tier cannot claim a
        verb its tests never type. The walk-in is the command with no
        word at all."""
        for verb, names in self.tier["entry_points"].items():
            for test_id in names:
                self.assertIn(test_id, self.ids, "an entry point is one test, by its id")
                module, cls, method = test_id.split(".")
                src = inspect.getsource(getattr(getattr(__import__(module), cls), method))
                self.assertRegex(src, entry_call(verb), f"{test_id} never runs {verb}")

    def test_the_entry_call_pattern_tells_a_run_from_a_mention(self):
        self.assertRegex('self.e.run("land", sid)', entry_call("land"))
        self.assertRegex('proc = run_office("deliver", self.name)', entry_call("deliver"))
        self.assertRegex('subprocess.run([str(REPO / "bin/office"), "help"])', entry_call("help"))
        self.assertRegex('o.run(cwd=self.root)', entry_call("walk-in"))
        self.assertRegex('walk = o.run().stdout', entry_call("walk-in"))
        self.assertRegex('proc = self.start("fix", "--on", "alpha")', entry_call("start"))
        self.assertRegex('folder = self.o.open("--title", "x")', entry_call("open"))
        for mention in ('verbs["land"]', 'self.assertIn("land", text)', 'e.run("landed")', 'self.landing()',
                        'tarfile.open(tb)'):
            self.assertNotRegex(mention, entry_call("land"))

    def test_the_tier_is_a_part_of_the_suite_and_holds_this_module(self):
        held = runner.tier_ids(self.tier, self.ids)
        self.assertLess(len(held), len(self.ids) / 2)
        self.assertTrue(all(i in held for i in self.ids if i.startswith("test_suite_clock.")))

    def test_a_tier_that_names_a_missing_test_or_misses_a_verb_says_so(self):
        tier = {"budget_seconds": 1, "entry_points": {"walk-in": ["test_x.T.test_a"], "gone": ["test_x.T"]},
                "also": ["test_y"]}
        problems = runner.tier_problems(tier, {"test_x.T.test_a"}, {"walk-in", "land"})
        self.assertIn("the verb land has no entry point in the fast tier (add a test that runs it)", problems)
        self.assertIn("the fast tier names an entry point for gone, which bin/office does not dispatch", problems)
        self.assertIn("also.tests: test_y is no test, class or module of the suite", problems)
        self.assertEqual(len(problems), 3, problems)
        self.assertEqual(runner.matching("test_x", {"test_x.T.a", "test_xy.T.a"}), {"test_x.T.a"})

    def test_a_tier_file_that_does_not_read_is_named(self):
        d = Env(self).tmp
        for text, words in (("budget_seconds = 0\n", "budget_seconds"),
                            ("budget_seconds = 5\n", "[entry_points]"),
                            ("budget_seconds = 5\n[entry_points]\nland = []\n", "entry_points.land"),
                            ("budget_seconds = [\n", "fast-tier.toml")):
            (d / "fast-tier.toml").write_text(text)
            with self.assertRaises(ValueError) as cm:
                runner.load_tier(d / "fast-tier.toml")
            self.assertIn(words, str(cm.exception))

    def test_the_dispatcher_is_read_or_refused(self):
        d = Env(self).tmp
        (d / "office").write_text('main() {\n  case "$verb" in\n    init) cmd_init "$@" ;;\n'
                                  '    help|--help|-h) cmd_help "$@" ;;\n    *) usage ;;\n  esac\n}\n')
        self.assertEqual(runner.dispatcher_verbs(d / "office"), {"walk-in", "init", "help"})
        (d / "office").write_text("echo nothing\n")
        with self.assertRaises(ValueError):
            runner.dispatcher_verbs(d / "office")

    def test_run_sh_fast_plans_the_tier_and_refuses_a_name_it_does_not_know(self):
        plan = subprocess.run([str(TESTS / "run.sh"), "--fast", "--plan"], capture_output=True, text=True,
                              timeout=120)
        self.assertEqual(plan.returncode, 0, plan.stderr)
        counted = sum(int(l.split("\t")[1]) for l in plan.stdout.splitlines())
        self.assertEqual(counted, sum(1 for _ in runner.tier_ids(self.tier, self.ids)) + self.duplicates())
        more = subprocess.run([str(TESTS / "run.sh"), "--fast", "--plan", "test_filed_append_only"],
                              capture_output=True, text=True, timeout=120)
        self.assertEqual(more.returncode, 0, more.stderr)
        self.assertIn("test_filed_append_only\t12", more.stdout)
        no = subprocess.run([str(TESTS / "run.sh"), "--fast", "test_nothing.T"], capture_output=True, text=True,
                            timeout=120)
        self.assertEqual(no.returncode, 2)
        self.assertIn("test_nothing.T, named after --fast, is no test, class or module of the suite", no.stderr)

    def duplicates(self):
        """Tier tests that run twice (an imported class runs again in the
        module that imports it, as under discover)."""
        held = runner.tier_ids(self.tier, self.ids)
        planned = [i for v in self.jobs.values() for i in v if i in held]
        return len(planned) - len(set(planned))


# A tiny repo for the runner to run: tests/ with the real runner and one
# module, so a detached run, a timed job and a budget can be watched end
# to end in seconds.
TINY_TEST = """import os, unittest
class T(unittest.TestCase):
    def test_quick(self):
        self.assertEqual(os.environ.get("OFFICE_TESTS_UNDER_RUNNER"), "1")
    def test_fails_when_asked(self):
        self.assertFalse(os.path.exists(os.path.join(os.path.dirname(__file__), "FAIL")))
"""


def tiny_repo(root, fail=False):
    (root / "tests").mkdir(parents=True)
    for name in ("run.sh", "runner.py"):
        shutil.copy2(TESTS / name, root / "tests" / name)
    (root / "tests" / "test_tiny.py").write_text(TINY_TEST)
    if fail:
        (root / "tests" / "FAIL").write_text("")
    return root


def wait_for(path, pattern, seconds=90):
    """The text of path once it matches pattern, or the last text read."""
    deadline, text = time.monotonic() + seconds, ""
    while time.monotonic() < deadline:
        text = path.read_text() if path.is_file() else ""
        if re.search(pattern, text):
            return text
        time.sleep(0.2)
    return text


class TestTheRunnersClock(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)

    def run_sh(self, root, *args, extra=None, timeout=120):
        env = dict(self.e.env, XDG_STATE_HOME=str(self.e.tmp / "state"), **(extra or {}))
        return subprocess.run([str(root / "tests" / "run.sh"), *args], cwd=root, env=env, capture_output=True,
                              text=True, timeout=timeout)

    def test_a_job_records_each_tests_time_and_the_run_writes_them_slowest_first(self):
        root = tiny_repo(self.e.tmp / "repo")
        logs = self.e.tmp / "logs"
        proc = self.run_sh(root, "--logs", str(logs))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        data = json.loads((logs / "test_tiny.json").read_text())
        self.assertEqual(sorted(data["durations"]), ["test_tiny.T.test_fails_when_asked", "test_tiny.T.test_quick"])
        rows = [l.split("\t") for l in (logs / "times.tsv").read_text().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertGreaterEqual(float(rows[0][1]), float(rows[1][1]))
        self.assertIn(f"each test's time, slowest first: {logs / 'times.tsv'}", proc.stdout)
        # Each job's HOME and TMPDIR were the runner's own, and are gone.
        scratch = re.search(r"HOME and TMPDIR under (\S+)", proc.stdout).group(1)
        self.assertFalse(pathlib.Path(scratch).exists())

    def test_detach_returns_at_once_with_one_line_and_the_verdict_follows(self):
        root = tiny_repo(self.e.tmp / "repo")
        started = time.monotonic()
        proc = self.run_sh(root, "--detach", timeout=60)
        took = time.monotonic() - started
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertLess(took, 30)
        self.assertEqual(len(proc.stdout.splitlines()), 1, proc.stdout)
        m = re.fullmatch(r"\[run\] the whole suite is running detached \(pid \d+\); its verdict will be in (\S+), "
                         r"its log in (\S+)\n", proc.stdout)
        self.assertIsNotNone(m, proc.stdout)
        verdict, log = pathlib.Path(m.group(1)), pathlib.Path(m.group(2))
        state = self.e.tmp / "state" / "office-src" / "suite"
        self.assertTrue(verdict.is_relative_to(state))
        self.assertFalse(verdict.is_relative_to(root))
        self.assertEqual((state / "latest").resolve(), verdict.parent.resolve())
        text = wait_for(verdict, r"^(OK|FAILED|BROKEN) ")
        self.assertRegex(text, r"^OK \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ: 2 tests passed in \d+s, not a git checkout\n$",
                         log.read_text() if log.is_file() else "no log")
        self.assertEqual(len(text.splitlines()), 1)
        self.assertIn("[run] OK (2 tests run)", log.read_text())
        self.assertTrue(wait_for_gone(verdict.parent / "tree"), "the copy was not removed")
        self.assertTrue(wait_for_exit(int(re.search(r"pid (\d+)", proc.stdout).group(1))))
        self.assertTrue((verdict.parent / "logs" / "test_tiny.log").is_file())

    def test_a_failing_detached_run_says_so_in_its_verdict(self):
        root = tiny_repo(self.e.tmp / "repo", fail=True)
        proc = self.run_sh(root, "--detach", timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        verdict = pathlib.Path(re.search(r"verdict will be in (\S+),", proc.stdout).group(1))
        text = wait_for(verdict, r"^(OK|FAILED|BROKEN) ")
        self.assertRegex(text, r"^FAILED \S+: 1 of 2 tests failed, in \d+s, not a git checkout; read \S+run\.log\n$")
        self.assertTrue(wait_for_exit(int(re.search(r"pid (\d+)", proc.stdout).group(1))))

    def test_detach_runs_with_sigint_restored_and_refuses_what_it_does_not_take(self):
        root = tiny_repo(self.e.tmp / "repo")
        for args in (("--detach", "test_tiny"), ("--detach", "--plan"), ("--detach", "--fast")):
            proc = self.run_sh(root, *args)
            self.assertEqual(proc.returncode, 2, args)
        self.assertFalse((self.e.tmp / "state").exists())

    def test_old_runs_are_pruned_and_latest_is_kept(self):
        state = self.e.tmp / "suite"
        state.mkdir()
        for i in range(13):
            (state / f"202610{i + 1:02d}T000000Z-{i}").mkdir()
        (state / "notes").mkdir()
        gone = runner.prune(state, keep=10)
        self.assertEqual(sorted(gone), [f"202610{i + 1:02d}T000000Z-{i}" for i in range(3)])
        self.assertTrue((state / "notes").is_dir())
        runner.point_latest(state, state / "20261013T000000Z-12")
        runner.point_latest(state, state / "20261012T000000Z-11")
        self.assertEqual(os.readlink(state / "latest"), "20261012T000000Z-11")

    def test_the_fast_tier_fails_past_its_budget(self):
        root = tiny_repo(self.e.tmp / "repo")
        (root / "bin").mkdir()
        (root / "bin" / "office").write_text('main() {\n  case "$verb" in\n    init) cmd_init "$@" ;;\n  esac\n}\n')
        tier = root / "tests" / "fast-tier.toml"
        tier.write_text('budget_seconds = 1\n[entry_points]\nwalk-in = ["test_tiny.T.test_quick"]\n'
                        'init = ["test_tiny.T.test_quick"]\n')
        slow = root / "tests" / "test_tiny.py"
        slow.write_text(slow.read_text().replace("def test_quick(self):\n",
                                                 "def test_quick(self):\n        import time; time.sleep(1.5)\n"))
        proc = self.run_sh(root, "--fast")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertRegex(proc.stdout, r"the fast tier took \d+\.\ds of wall clock, 1 of the suite's 2 tests; "
                                      r"its budget is 1s")
        self.assertIn("the fast tier ran over its budget", proc.stderr)
        tier.write_text(tier.read_text().replace("budget_seconds = 1", "budget_seconds = 100"))
        proc = self.run_sh(root, "--fast")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        # A verb the dispatcher gains with no entry point stops the tier.
        (root / "bin" / "office").write_text('main() {\n  case "$verb" in\n    init) cmd_init "$@" ;;\n'
                                             '    land) cmd_land "$@" ;;\n  esac\n}\n')
        proc = self.run_sh(root, "--fast")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("the verb land has no entry point in the fast tier", proc.stderr)


def wait_for_exit(pid, seconds=30):
    """True once the process has exited (gone, or a zombie nobody reaped)."""
    deadline = time.monotonic() + seconds
    stat = pathlib.Path(f"/proc/{pid}/stat")
    while time.monotonic() < deadline:
        try:
            if stat.read_text().rsplit(")", 1)[1].split()[0] == "Z":
                return True
        except (OSError, IndexError):
            return True
        time.sleep(0.2)
    return False


def wait_for_gone(path, seconds=30):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not path.exists():
            return True
        time.sleep(0.2)
    return False


# --- the order jobs start in, and the run's bytecode cache (0.21.0) ----------------------------

def finished_run(state, name, verdict, rows):
    """A detached run directory under state as the runner leaves one: its
    verdict line and its logs/times.tsv (test, seconds, job per row)."""
    run = state / name
    (run / "logs").mkdir(parents=True)
    (run / "verdict").write_text(verdict + "\n")
    if rows is not None:
        (run / "logs" / "times.tsv").write_text("".join(f"{t}\t{s}\t{j}\n" for t, s, j in rows))
    return run


class TestTheOrderJobsStartIn(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.state = self.e.tmp / "state" / "office-src" / "suite"
        self.state.mkdir(parents=True)

    def test_with_no_earlier_run_it_is_as_before(self):
        self.assertEqual(runner.last_times(self.state), ({}, None))
        self.assertEqual(runner.last_times(self.e.tmp / "no-such-state"), ({}, None))
        jobs = {"test_office": ["a"], runner.SERIAL_JOB: ["b"], "test_filed_append_only": ["c"]}
        self.assertEqual(runner.order(jobs, times={}), runner.order(jobs))
        self.assertEqual(runner.order(jobs, times={})[0], runner.SERIAL_JOB)
        self.assertIn("no earlier run's times here", runner.order_line(None))
        self.assertIn("as before", runner.order_line(None))

    def test_the_times_are_the_newest_finished_runs(self):
        finished_run(self.state, "20261010T000000Z-1", "OK 2026-10-10T00:20:00Z: 2 tests passed in 9s, at x",
                     [("t.A.a", 1.0, "t"), ("t.A.b", 2.0, "t")])
        failed = finished_run(self.state, "20261011T000000Z-2", "FAILED 2026-10-11T00:20:00Z: 1 of 2 tests failed",
                              [("t.A.a", 5.0, "t"), ("not a row", "x", "y"), ("t.A.b", "slow", "t"),
                               ("s.B.c", 7.5, runner.SERIAL_JOB)])
        finished_run(self.state, "20261012T000000Z-3", "BROKEN 2026-10-12T00:20:00Z: the runner could not run",
                     [("t.A.a", 99.0, "t")])
        finished_run(self.state, "20261013T000000Z-4", "RUNNING since 2026-10-13T00:00:00Z", None)
        (self.state / "notes").mkdir()
        times, source = runner.last_times(self.state)
        self.assertEqual(source, failed)
        self.assertEqual(times, {"t": {"t.A.a": 5.0}, runner.SERIAL_JOB: {"s.B.c": 7.5}})
        self.assertEqual(runner.order_line(source),
                         f"jobs start longest first, by the last run's times ({failed / 'logs' / 'times.tsv'})")

    def test_longest_first_by_those_times(self):
        times = {runner.SERIAL_JOB: {"s.T.a": 30.0, "s.T.b": 30.0},
                 "test_x": {"test_x.T.a": 100.0},
                 "test_y": {"test_y.T.a": 1.0, "test_y.T.b": 2.0}}
        jobs = {runner.SERIAL_JOB: ["s.T.a"],               # one of its two tests moved out
                "test_x": ["test_x.T.a"],
                "test_y": ["test_y.T.a", "test_y.T.b", "test_y.T.new"],  # a test the last run never timed
                "test_z": ["s.T.b"]}                         # the moved test, timed in the lane
        weights = runner.job_weights(jobs, times)
        self.assertEqual(weights, {runner.SERIAL_JOB: 30.0, "test_x": 100.0, "test_y": 1.0 + 2.0 + 30.0,
                                   "test_z": 30.0})
        self.assertEqual(runner.order(jobs, times=times), ["test_x", "test_y", runner.SERIAL_JOB, "test_z"])
        # The serial lane is weighed like any job: it no longer goes first
        # when the times say another job is longer.
        self.assertNotEqual(runner.order(jobs, times=times)[0], runner.order(jobs)[0])

    def test_run_sh_plans_and_runs_in_that_order_and_says_so(self):
        root = tiny_repo(self.e.tmp / "repo")
        # A second module, larger on disk but quick: by size it would go first.
        (root / "tests" / "test_big.py").write_text("import unittest\n# " + "x" * 4000 + "\n"
                                                    "class B(unittest.TestCase):\n    def test_b(self):\n"
                                                    "        pass\n")
        env = dict(self.e.env, XDG_STATE_HOME=str(self.e.tmp / "state"))

        def run_sh(*args):
            return subprocess.run([str(root / "tests" / "run.sh"), *args], cwd=root, env=env, capture_output=True,
                                  text=True, timeout=120)
        plan = run_sh("--plan")
        self.assertEqual([l.split("\t")[0] for l in plan.stdout.splitlines()], ["test_big", "test_tiny"], plan.stderr)
        run = finished_run(self.state, "20261013T000000Z-9", "OK 2026-10-13T00:10:00Z: 3 tests passed in 9s",
                           [("test_tiny.T.test_quick", 40.0, "test_tiny"), ("test_big.B.test_b", 0.1, "test_big")])
        plan = run_sh("--plan")
        self.assertEqual([l.split("\t")[0] for l in plan.stdout.splitlines()], ["test_tiny", "test_big"], plan.stderr)
        proc = run_sh("--jobs", "1", "--logs", str(self.e.tmp / "logs"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn(f"[run] jobs start longest first, by the last run's times ({run / 'logs' / 'times.tsv'})",
                      proc.stdout)
        started = [l.split()[-1] for l in proc.stdout.splitlines() if l.startswith("[run] started ")]
        self.assertEqual(started, ["test_tiny", "test_big"])

    def test_a_job_never_sees_the_times(self):
        finished_run(self.state, "20261013T000000Z-9", "OK 2026-10-13T00:10:00Z: 1 tests passed in 9s",
                     [("t.A.a", 1.0, "t")])
        caller = dict(self.e.env, XDG_STATE_HOME=str(self.e.tmp / "state"))
        self.assertEqual(runner.last_times(runner.state_dir(caller))[0], {"t": {"t.A.a": 1.0}})
        job = runner.isolated_env(caller, self.e.tmp / "job")
        self.assertEqual(runner.last_times(runner.state_dir(job)), ({}, None))
        # This very test, when the runner runs it: its own state directory
        # holds no run, whatever the machine's holds.
        if os.environ.get("OFFICE_TESTS_UNDER_RUNNER"):
            self.assertEqual(runner.last_times(runner.state_dir(os.environ)), ({}, None))


    def test_the_readme_and_the_front_sheet_say_how(self):
        readme = " ".join((REPO / "README.md").read_text().split())
        tests = readme.split("## Tests", 1)[1].split(" ## ", 1)[0]
        for words in ("longest first", "times.tsv", "as before", "bytecode cache", "PYTHONPYCACHEPREFIX",
                      "OnATerminal", "drive a terminal"):
            self.assertIn(words, tests)
        sheet = (REPO / ("cla" + "ude") / "context" / "front-sheet.md").read_text()
        clock = " ".join(sheet.split("## The suite's clock", 1)[1].split("\n## ", 1)[0].split())
        for words in ("bytecode cache", "OnATerminal", "longest first", "pylib"):
            self.assertIn(words, clock)


class TestTheRunsBytecodeCache(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.src = self.e.tmp / "src"
        self.src.mkdir()
        (self.src / "mod_a.py").write_text("WORD = 'compiled'\n")
        (self.src / "broken.py").write_text("def (:\n")
        self.prefix = self.e.tmp / "pycache"

    def test_it_compiles_once_where_the_interpreter_looks_and_links_the_standard_library(self):
        n = runner.seed_bytecode(self.prefix, [self.src])
        self.assertEqual(n, 1)  # broken.py is skipped, and said
        pyc = runner.cached_pyc(self.prefix, self.src / "mod_a.py")
        self.assertTrue(pyc.is_file())
        self.assertTrue(pyc.is_relative_to(self.prefix))
        env = dict(self.e.env, PYTHONPYCACHEPREFIX=str(self.prefix))
        where = subprocess.run([sys.executable, "-B", "-c", "import importlib.util, json, sys; "
                                "print(importlib.util.cache_from_source(sys.argv[1])); print(json.__cached__)",
                                str(self.src / "mod_a.py")], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(where.returncode, 0, where.stderr)
        mine, stdlib = where.stdout.splitlines()
        self.assertEqual(pathlib.Path(mine), pyc)
        # The standard library's own compiled code, linked into the cache,
        # since the interpreter looks nowhere else once a prefix is set.
        self.assertTrue(pathlib.Path(stdlib).is_relative_to(self.prefix), stdlib)
        self.assertTrue(pathlib.Path(stdlib).is_symlink(), stdlib)

    def test_the_cache_is_read_and_never_written_by_what_runs(self):
        runner.seed_bytecode(self.prefix, [self.src])
        before = sorted(str(p.relative_to(self.prefix)) for p in self.prefix.rglob("*"))
        # Proof it is read: the source changed, same size and time, so the
        # cache stands for it and its compiled word is what runs.
        src = self.src / "mod_a.py"
        stat = src.stat()
        src.write_text("WORD = 'from src'\n")
        os.utime(src, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        env = dict(self.e.env, PYTHONPYCACHEPREFIX=str(self.prefix), PYTHONDONTWRITEBYTECODE="1")
        out = subprocess.run([sys.executable, "-B", "-c", "import sys; sys.path.insert(0, sys.argv[1]); "
                              "import mod_a; print(mod_a.WORD)", str(self.src)], env=env, capture_output=True,
                             text=True, timeout=60)
        self.assertEqual(out.stdout, "compiled\n", out.stderr)
        # And the office command, run under the cache, writes nothing to it.
        office_cache = self.e.tmp / "office-cache"
        runner.seed_bytecode(office_cache, [REPO / "lib"])
        listed = sorted(str(p.relative_to(office_cache)) for p in office_cache.rglob("*"))
        proc = subprocess.run([str(REPO / "bin" / "office"), "help"], env=dict(self.e.env, PYTHONPYCACHEPREFIX=str(
            office_cache)), cwd=self.e.home, capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(sorted(str(p.relative_to(office_cache)) for p in office_cache.rglob("*")), listed)
        self.assertEqual(sorted(str(p.relative_to(self.prefix)) for p in self.prefix.rglob("*")), before)

    def test_every_job_gets_the_runs_cache_and_never_the_callers(self):
        base = dict(self.e.env, PYTHONPYCACHEPREFIX=str(self.e.tmp / "callers"))
        self.assertNotIn("PYTHONPYCACHEPREFIX", runner.isolated_env(base, self.e.tmp / "j1"))
        self.assertEqual(runner.isolated_env(base, self.e.tmp / "j2", self.prefix)["PYTHONPYCACHEPREFIX"],
                         str(self.prefix))
        # Under the runner, every Env hands the run's cache to the commands
        # its test runs; under plain unittest there is none to hand on.
        if os.environ.get("OFFICE_TESTS_UNDER_RUNNER"):
            self.assertEqual(self.e.env.get("PYTHONPYCACHEPREFIX"), os.environ.get("PYTHONPYCACHEPREFIX"))
            self.assertIn("office-tests-scratch.", self.e.env.get("PYTHONPYCACHEPREFIX", ""))
        else:
            self.assertNotIn("PYTHONPYCACHEPREFIX", self.e.env)

    def test_the_fakes_are_compiled_into_it_and_a_fake_program_reads_them_there(self):
        # 0.27.0: the fake bales are modules under tests/fakes/, compiled
        # with the rest, and the program a test writes is three lines that
        # import one and run it with the test's config.
        runner.seed_bytecode(self.prefix)
        for source in sorted(FAKES.glob("*.py")):
            self.assertTrue(runner.cached_pyc(self.prefix, source).is_file(), source.name)
        env = dict(self.e.env, PYTHONPYCACHEPREFIX=str(self.prefix), PYTHONDONTWRITEBYTECODE="1")
        where = subprocess.run([sys.executable, "-S", "-c", "import sys; sys.path.insert(0, sys.argv[1]); "
                                "import pack_bale; print(pack_bale.__cached__)", str(FAKES)], env=env,
                               capture_output=True, text=True, timeout=60)
        self.assertEqual(pathlib.Path(where.stdout.strip()), runner.cached_pyc(self.prefix, FAKES / "pack_bale.py"),
                         where.stderr)
        (self.e.tmp / "bin").mkdir()
        program = fake_program(self.e.tmp / "bin" / "bale", "small_bales", "old")
        self.assertTrue(program.read_text().startswith("#!"))
        self.assertLessEqual(len(program.read_text().splitlines()), 6)
        for argv, code, out in ((["--version"], 0, "bale 0.4.40\n"), (["status"], 97, "")):
            proc = subprocess.run([str(program), *argv], env=env, capture_output=True, text=True, timeout=60)
            self.assertEqual((proc.returncode, proc.stdout), (code, out), proc.stderr)
        # The config travels as plain values, and the function's return is the exit.
        calls = self.e.tmp / "calls.jsonl"
        fake_program(self.e.tmp / "bin" / "replay", "replay_bale", config={"routes": {"*": str(self.e.tmp)},
                                                                            "calls": str(calls)})
        proc = subprocess.run([str(self.e.tmp / "bin" / "replay"), "x"], env=env, cwd=self.e.tmp,
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 97, proc.stderr)
        self.assertIn("the probe captured no line for bale x", proc.stderr)
        self.assertEqual(json.loads(calls.read_text())[1], ["x"])

    def test_the_command_runs_a_module_as_its_script_would(self):
        """bin/office's pylib: __name__ is __main__, sys.argv[0] the module's
        path, the arguments as given, lib/ first on sys.path and no current
        directory on it (a json.py there is not what json imports)."""
        lib = self.e.tmp / "install" / "lib"
        lib.mkdir(parents=True)
        (lib / "office_probe_mod.py").write_text(
            "import json, sys\n"
            "print(__name__); print(sys.argv[0]); print(sys.argv[1:]); print(sys.path[0]); print(json.dumps(1))\n"
            "sys.exit(3)\n")
        cwd = self.e.tmp / "elsewhere"
        cwd.mkdir()
        (cwd / "json.py").write_text("raise SystemExit('the current directory was on sys.path')\n")
        proc = subprocess.run(["bash", "-c", office_functions("pylib") + 'pylib "$OFFICE_SRC/lib/office_probe_mod.py" '
                               '"a b" c'], env=dict(self.e.env, OFFICE_SRC=str(lib.parent)), cwd=cwd,
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual(proc.stdout.splitlines(), ["__main__", str(lib / "office_probe_mod.py"), "['a b', 'c']",
                                                    str(lib), "1"])


class TestTheRecord(unittest.TestCase):
    def test_the_version_the_releases_and_the_readme(self):
        version = (REPO / "VERSION").read_text().strip()
        releases = (REPO / "RELEASES.md").read_text()
        self.assertTrue(releases.split("\n## ", 1)[1].startswith(version), "RELEASES.md's newest entry is VERSION")
        readme = " ".join((REPO / "README.md").read_text().split())
        tests = readme.split("## Tests", 1)[1].split(" ## ", 1)[0]
        for words in ("tests/run.sh --fast", "tests/run.sh --detach", "fast-tier.toml", "two minutes",
                      "verdict"):
            self.assertIn(words, tests)
        sheet = (REPO / ("cla" + "ude") / "context" / "front-sheet.md").read_text()
        clock = sheet.split("## The suite's clock", 1)[1].split("\n## ", 1)[0]
        for words in ("--fast", "--slow", "Env", "test_suite_clock.py", "--detach", "120 seconds"):
            self.assertIn(words, clock)
        self.assertIn(f"- {version} (session", sheet)
