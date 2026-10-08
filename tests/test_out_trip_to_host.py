"""Tests for the out trip to a host (office-src 0.15.0): the attended
transport through a project's shell, files and a temporary directory on a
host, a clone moved to its host (office projects add --from), a host's
bale brought level (office projects level-bale), office start packing and
opening on a host, and the runner printing a failing test's traceback.
(0.15.0's wording for a land on a host gave way to the return trip:
tests/test_return_trip.py.)

The suite makes no network call and runs no real ssh, rsync or docker:
0.14.0's fake ssh (tests/test_project_on_host.py) is first on the PATH,
and a host here is a directory of its own under the fake (its HOME, PATH
and TMPDIR), so what the office leaves in a host's temporary directory is
seen. The fake bales of test_start.py and test_land.py answer through it.
Run with the rest of the suite:

    tests/run.sh test_out_trip_to_host
"""

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_start import FakePackBale, git_repo, on_a_terminal, tar_names  # noqa: E402
from test_land import LandCase, bundle_file  # noqa: E402
from test_project_on_host import DOWN, HOST, OLD, FakeSsh, git, manifest_of  # noqa: E402

import office_bale as ob  # noqa: E402
import office_host as ohost  # noqa: E402
import runner  # noqa: E402

LIB = REPO / "lib"
LEVEL = "office projects level-bale"


def run_git(repo, *args, env=None):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True,
                          env=env).stdout


class FakeSshCase(unittest.TestCase):
    """The fake ssh first on this process's PATH, with no reach cached."""

    def setUp(self):
        self.e = Env(self)
        self.ssh = FakeSsh(self.e.tmp)
        self.addCleanup(os.environ.__setitem__, "PATH", os.environ.get("PATH", ""))
        os.environ["PATH"] = self.ssh.path(self.e.env["PATH"])
        os.environ["OFFICE_RERUN"] = "office start"
        self.addCleanup(os.environ.pop, "OFFICE_RERUN", None)
        ohost.forget_reach()
        self.addCleanup(ohost.forget_reach)


# --- 1. the attended transport -----------------------------------------------------------------

class TestTheAttendedForm(unittest.TestCase):
    def test_ssh_gets_tt_and_a_container_layer_gets_it(self):
        o = list(ohost.SSH_OPTIONS)
        cases = {
            "ssh me@h bash -lc": ["ssh", "-tt", *o, "me@h", "bash", "-lc"],
            "ssh me@h docker exec -i -u me box bash -lc": ["ssh", "-tt", *o, "me@h", "docker", "exec", "-it",
                                                         "-u", "me", "box", "bash", "-lc"],
            # ssh's own -i (an identity file) is ssh's; the container's
            # -i is the first one past the target.
            "ssh -i key me@h docker exec -i box bash -lc": ["ssh", "-tt", *o, "-i", "key", "me@h", "docker", "exec",
                                                            "-it", "box", "bash", "-lc"],
            "ssh me@h docker exec --interactive box bash -lc": ["ssh", "-tt", *o, "me@h", "docker", "exec",
                                                                "--interactive", "--tty", "box", "bash", "-lc"],
            "docker exec -i box bash -lc": ["docker", "exec", "-it", "box", "bash", "-lc"],
        }
        for shell, want in cases.items():
            place = ohost.Place("/srv/p", "me@h", shell=shell)
            self.assertEqual(place.attended_words(), want, shell)
            # The plain form is untouched by it.
            self.assertNotIn("-tt", place.words())
        place = ohost.Place("/srv/p", "me@h")
        self.assertEqual(place.attended_argv("cd /srv/p && bale apply x")[-1], "'cd /srv/p && bale apply x'")
        local = ohost.Place("/srv/p", "me@h", shell="docker exec -i box bash -lc")
        self.assertEqual(local.attended_argv("cd /srv/p && true")[-1], "cd /srv/p && true")


# A bale that asks one question on its stdin, as apply's walkthrough does.
ASKING_BALE = r'''#!/usr/bin/env python3
import sys
if sys.argv[1:2] == ["apply"]:
    sys.stdout.write("Merge the session? [y/N] "); sys.stdout.flush()
    answer = sys.stdin.readline().strip()
    print("answered:" + (answer or "(nothing: stdin closed)"))
    print("terminal:" + ("yes" if sys.stdin.isatty() else "no"))
    sys.exit(0 if answer else 3)
print("asking fake bale: only apply", file=sys.stderr); sys.exit(97)
'''

INTERACT_DRIVER = r'''import sys
sys.path.insert(0, {lib!r})
import office_bale as ob, office_host as oh
place = oh.Place({path!r}, {host!r}, {shell!r}, name="far")
code = ob.Reader().interact("apply", place, {capture!r}, tarball="response-x.tar.gz")
print("EXIT", code)
'''


class AttendedCase(FakeSshCase):
    def setUp(self):
        super().setUp()
        self.repo = git_repo(self.e.tmp / "far")
        bindir = self.e.tmp / "asking-bale"
        bindir.mkdir()
        (bindir / "bale").write_text(ASKING_BALE)
        (bindir / "bale").chmod(0o755)
        self.env = dict(self.e.env, PATH=self.ssh.path(f"{bindir}{os.pathsep}{self.e.env['PATH']}"))
        self.capture = self.e.tmp / "capture.txt"

    def driver(self, shell=None):
        d = self.e.tmp / "driver.py"
        d.write_text(INTERACT_DRIVER.format(lib=str(LIB), path=str(self.repo), host=HOST,
                                            shell=shell or f"ssh {HOST} bash -lc", capture=str(self.capture)))
        return [sys.executable, "-B", str(d)]


class TestInteractPiped(AttendedCase):
    def test_piped_nothing_asks_and_the_plain_form_runs(self):
        proc = subprocess.run(self.driver(), env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=60)
        self.assertIn("answered:(nothing: stdin closed)", proc.stdout)
        self.assertIn("EXIT 3", proc.stdout)
        calls = self.ssh.connections()
        self.assertTrue(calls)
        self.assertTrue(all("-tt" not in c for c in calls), calls)
        self.assertIn("answered:(nothing", self.capture.read_text())


class TestInteractOnATerminal(AttendedCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_the_occupant_answers_bale_through_the_shell(self):
        code, seen = on_a_terminal(self, self.driver(), self.e.tmp, self.env, [(b"Merge the session? [y/N]", "y")])
        self.assertEqual(code, 0, seen)
        self.assertIn("answered:y", seen)
        self.assertIn("terminal:yes", seen)
        self.assertIn("EXIT 0", seen)
        attended = [c for c in self.ssh.connections() if "-tt" in c]
        self.assertEqual(len(attended), 1, self.ssh.connections())
        self.assertTrue(attended[0][-1].startswith("'cd "), attended[0])
        # The capture is read line by line: no carriage returns kept.
        self.assertNotIn("\r", self.capture.read_text())

    def test_a_container_layer_gets_it(self):
        shell = f"ssh {HOST} docker exec -i -u me box bash -lc"
        # The reach check goes through the plain form, the step through
        # the attended one; the fake takes exactly these two.
        self.ssh.expect([HOST], ["docker", "exec", "-i", "-u", "me", "box", "bash", "-lc"],
                        ["docker", "exec", "-it", "-u", "me", "box", "bash", "-lc"])
        code, seen = on_a_terminal(self, self.driver(shell), self.e.tmp, self.env, [(b"Merge the session?", "yes")])
        self.assertEqual(code, 0, seen)
        self.assertIn("answered:yes", seen)
        attended = [c for c in self.ssh.connections() if "-tt" in c]
        self.assertEqual(len(attended), 1, self.ssh.connections())
        self.assertIn("-it", attended[0])


# --- files and a temporary directory on a host --------------------------------------------------

class TestFilesThroughTheShell(FakeSshCase):
    def test_bytes_go_and_come_back_intact_and_the_scratch_is_removed(self):
        data = bytes(range(256)) * 300 + b"\r\n\0end"
        src = self.e.tmp / "payload.bin"
        src.write_bytes(data)
        place = ohost.Place(str(self.e.tmp), HOST)
        with ohost.Scratch(place) as sc:
            remote = f"{sc.path}/payload.bin"
            self.assertTrue(pathlib.Path(sc.path).name.startswith("office-"))
            self.assertEqual(str(pathlib.Path(sc.path).parent), str(self.ssh.host_tmp(HOST)))
            ohost.send_file(place, str(src), remote)
            back = self.e.tmp / "back.bin"
            ohost.fetch_file(place, remote, str(back))
            self.assertEqual(back.read_bytes(), data)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_a_login_shell_that_prints_on_stdout_is_caught_not_swallowed(self):
        (self.ssh.host_dir(HOST) / "chatter").write_text("Welcome to the host\n")
        src = self.e.tmp / "f.txt"
        src.write_text("the file\n")
        place = ohost.Place(str(self.e.tmp), HOST)
        with ohost.Scratch(place) as sc:
            # The sum comes back on stdout behind the chatter: still read.
            ohost.send_file(place, str(src), f"{sc.path}/f.txt")
            with self.assertRaises(ohost.HostError) as cm:
                ohost.fetch_file(place, f"{sc.path}/f.txt", str(self.e.tmp / "g.txt"))
        self.assertIn("did not arrive intact", str(cm.exception))
        self.assertIn("login shell print on stdout", str(cm.exception))

    def test_the_scratch_is_removed_when_the_work_fails(self):
        place = ohost.Place(str(self.e.tmp), HOST)
        with self.assertRaises(RuntimeError):
            with ohost.Scratch(place) as sc:
                (pathlib.Path(sc.path) / "half").write_text("x")
                raise RuntimeError("the work failed")
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_remove_scratch_removes_only_what_the_office_made(self):
        other = self.ssh.host_tmp(HOST) / "theirs"
        other.mkdir()
        with self.assertRaises(ohost.HostError):
            ohost.remove_scratch(ohost.Place(str(self.e.tmp), HOST), str(other))
        self.assertTrue(other.is_dir())

    def test_missing_paths_through_the_shell(self):
        repo = git_repo(self.e.tmp / "p", {"src/a.py": "a\n"})
        place = ohost.Place(str(repo), HOST)
        self.assertEqual(ohost.missing_paths(place, ["src", "nope", "src/a.py/", "docs/x"]), ["nope", "docs/x"])


# --- 2. a clone moved to its host --------------------------------------------------------------

def a_clone(tmp, env, name="work-clone"):
    """A clone with what --from must carry: branches (one only here), a
    light and an annotated tag, origin's remote-tracking refs and its
    symbolic HEAD, upstream config, HEAD on a feature branch."""
    origin = git_repo(pathlib.Path(tmp) / f"{name}-origin", {"README.md": "theirs\n", "src/a.py": "a\n"},
                      ignore_bale=False)
    clone = pathlib.Path(tmp) / name
    subprocess.run(["git", "clone", "-q", str(origin), str(clone)], check=True, env=env, capture_output=True)
    g = lambda *a: run_git(clone, *a, env=env)  # noqa: E731
    g("checkout", "-q", "-b", "feature/on-origin")
    (clone / "src" / "b.py").write_text("b\n")
    g("add", "-A"); g("commit", "-qm", "b")
    g("push", "-q", "-u", "origin", "feature/on-origin")
    g("checkout", "-q", "-b", "ref/only-here")
    (clone / "notes.md").write_text("here only\n")
    g("add", "-A"); g("commit", "-qm", "here only")
    g("tag", "light-tag")
    g("tag", "-a", "v1", "-m", "annotated")
    g("checkout", "-q", "feature/on-origin")
    return clone


class CloneCase(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.ssh = FakeSsh(self.e.tmp)
        self.e.env["PATH"] = self.ssh.path(self.e.env["PATH"])
        self.root = self.e.init()
        self.clone = a_clone(self.e.tmp, self.e.env)
        self.target = self.e.tmp / "on-the-host" / "work-clone"
        self.before = self.snapshot(self.clone)

    def snapshot(self, repo):
        g = lambda *a: run_git(repo, *a, env=self.e.env)  # noqa: E731
        return {"refs": g("for-each-ref", "--format=%(objectname) %(refname) %(symref)"),
                "head": g("symbolic-ref", "HEAD"), "status": g("status", "--porcelain"),
                "config": g("config", "--local", "--list"), "files": g("ls-files")}

    def run_office(self, *args, **kw):
        self.ssh.reset()
        return self.e.run(*args, cwd=self.root, **kw)


class TestCloneToItsHost(CloneCase):
    def test_add_from_brings_every_branch_and_tag_and_the_remotes_and_prepares_it(self):
        proc = self.run_office("projects", "add", "work", str(self.target), "--host", HOST, "--from", str(self.clone))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        g = lambda *a: run_git(self.target, *a, env=self.e.env)  # noqa: E731
        want = {l.split()[1]: l.split()[0] for l in self.before["refs"].splitlines() if len(l.split()) == 2}
        got = {l.split()[1]: l.split()[0] for l in g("for-each-ref", "--format=%(objectname) %(refname) %(symref)")
               .splitlines() if len(l.split()) == 2}
        self.assertEqual(got, want)
        for ref in ("refs/heads/ref/only-here", "refs/heads/feature/on-origin", "refs/tags/v1", "refs/tags/light-tag",
                    "refs/remotes/origin/feature/on-origin"):
            self.assertIn(ref, got)
        # The symbolic remote HEAD, the remotes and the upstreams, as here.
        self.assertIn("refs/remotes/origin/HEAD refs/remotes/origin/", g("for-each-ref", "--format=%(refname) %(symref)",
                                                                          "refs/remotes/origin/HEAD"))
        self.assertEqual(g("config", "remote.origin.url").strip(),
                         run_git(self.clone, "config", "remote.origin.url", env=self.e.env).strip())
        self.assertEqual(g("config", "branch.feature/on-origin.merge").strip(), "refs/heads/feature/on-origin")
        self.assertEqual(g("symbolic-ref", "HEAD").strip(), "refs/heads/feature/on-origin")
        # Prepared: git status clean, git ls-files the clone's, bale's files excluded.
        self.assertEqual(g("status", "--porcelain"), "")
        self.assertEqual(g("ls-files"), self.before["files"])
        self.assertIn(".bale/", (self.target / ".git" / "info" / "exclude").read_text())
        self.assertTrue((self.target / "bale.toml").is_file())
        # The clone here is not changed, and add says it can go.
        self.assertEqual(self.snapshot(self.clone), self.before)
        self.assertIn(f"{self.clone} was not changed; once you are satisfied with the clone on {HOST}, you can remove "
                      "it (the office never does)", proc.stderr)
        self.assertIn(f"added work: {self.target} (a git repo with bale.toml, no .bale/, on {HOST})", proc.stdout)
        # Nothing left on the host but the clone.
        self.assertEqual(self.ssh.left_on(HOST), [])
        self.assertEqual({c[0] for c in self.ssh.connections()}, {HOST})

    def test_a_path_that_exists_there_is_refused_before_anything_moves(self):
        self.target.mkdir(parents=True)
        (self.target / "theirs.txt").write_text("keep\n")
        proc = self.run_office("projects", "add", "work", str(self.target), "--host", HOST, "--from", str(self.clone))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("already exists on", proc.stderr)
        self.assertEqual(sorted(p.name for p in self.target.iterdir()), ["theirs.txt"])
        self.assertNotIn("[projects.work]", (self.root / "floor-plan/manifest.toml").read_text())
        self.assertFalse(any("cat >" in c[-1] for c in self.ssh.connections()), "a file was sent")

    def test_a_dirty_clone_is_named_and_piped_add_refuses_naming_the_flag(self):
        (self.clone / "src" / "a.py").write_text("changed here\n")
        (self.clone / "scratch.txt").write_text("untracked\n")
        proc = self.run_office("projects", "add", "work", str(self.target), "--host", HOST, "--from", str(self.clone))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("2 changed path(s) in its working tree", proc.stderr)
        self.assertIn("    src/a.py", proc.stderr)
        self.assertIn("    scratch.txt", proc.stderr)
        self.assertIn("--from-dirty-ok", proc.stderr)
        self.assertFalse(self.target.exists())
        proc = self.run_office("projects", "add", "work", str(self.target), "--host", HOST, "--from", str(self.clone),
                               "--from-dirty-ok")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        # Only what is committed travelled.
        self.assertEqual((self.target / "src" / "a.py").read_text(), "a\n")
        self.assertFalse((self.target / "scratch.txt").exists())
        self.assertEqual((self.clone / "src" / "a.py").read_text(), "changed here\n")

    def test_from_goes_with_a_host(self):
        for args in (("--from", str(self.clone)), ("--from-dirty-ok",)):
            proc = self.run_office("projects", "add", "work", str(self.target), *args)
            self.assertEqual(proc.returncode, 1, args)
        self.assertIn("goes with", proc.stderr)
        self.assertEqual(self.ssh.connections(), [])

    def test_a_clone_that_does_not_come_out_level_is_removed(self):
        facts = ohost.clone_facts(self.clone)
        other = run_git(self.clone, "rev-list", "--max-parents=0", "HEAD", env=self.e.env).strip()
        facts["refs"] = [(n, other if n == "refs/tags/light-tag" else s) for n, s in facts["refs"]]
        self.addCleanup(os.environ.__setitem__, "PATH", os.environ.get("PATH", ""))
        os.environ["PATH"] = self.e.env["PATH"]
        ohost.forget_reach()
        self.addCleanup(ohost.forget_reach)
        with self.assertRaises(ohost.HostError) as cm:
            ohost.clone_to(ohost.Place(str(self.target), HOST), self.clone, facts)
        self.assertIn("does not hold the refs", str(cm.exception))
        self.assertIn("was removed", str(cm.exception))
        self.assertFalse(self.target.exists())
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_a_shallow_clone_is_refused(self):
        shallow = self.e.tmp / "shallow"
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{self.clone}", str(shallow)], check=True,
                       env=self.e.env, capture_output=True)
        proc = self.run_office("projects", "add", "work", str(self.target), "--host", HOST, "--from", str(shallow))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("shallow", proc.stderr)
        self.assertFalse(self.target.exists())


class TestCloneWizard(CloneCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_the_wizard_asks_after_the_host_and_explains(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "add"], self.root, self.e.env, [
            (b"Path to the project's git repo (--path):", str(self.target)),
            (b"Where the repo is: this machine, or an ssh host (--host) [return skips]:", HOST),
            (f"(--shell) [ssh {HOST} bash -lc]:".encode(), ""),
            (b"(--connect)", ""),
            (b"Is there a clone on this machine to bring there? Its path (--from) [return skips]:", "?"),
            (b"carried from this machine as a git bundle", str(self.clone)),
            (b"Name for it in this office (--name) [work-clone]:", "work"),
            (b"(--ride) [return ends the list]:", ""),
            (b"(--after-land) [return ends the list]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("added work", seen)
        self.assertEqual(run_git(self.target, "status", "--porcelain", env=self.e.env), "")

    def test_a_dirty_clone_is_asked_about_and_no_moves_nothing(self):
        (self.clone / "src" / "a.py").write_text("changed\n")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "add", "work", str(self.target),
                                          "--host", HOST, "--from", str(self.clone)], self.root, self.e.env, [
            (b"Bring the clone without them? (--from-dirty-ok) (y/n) [n]:", ""),
        ])
        self.assertEqual(code, 1, seen)
        self.assertIn("nothing moved", seen)
        self.assertFalse(self.target.exists())


# --- 3. a host's bale brought level ---------------------------------------------------------------

def fake_install(root, version, user_files=None, extra=None):
    """A bale release install at root: bin/bale answering --version (and
    the read side's status, for office status), bin/VERSION, docs/,
    install.sh and upgrade.sh that do what bale's do (upgrade.sh keeps
    user/, replaces the rest, puts user/ back and runs install.sh -y,
    which records that it ran), and user/ with the files given."""
    root = pathlib.Path(root)
    (root / "bin").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / "bin" / "VERSION").write_text(version + "\n")
    (root / "bin" / "bale").write_text(INSTALL_BALE)
    (root / "docs" / "AGENT.md").write_text(f"docs of {version}\n")
    (root / "install.sh").write_text(INSTALL_SH)
    (root / "upgrade.sh").write_text(UPGRADE_SH)
    for f in ("bin/bale", "install.sh", "upgrade.sh"):
        (root / f).chmod(0o755)
    for rel, text in (user_files or {}).items():
        (root / "user" / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / "user" / rel).write_text(text)
    for rel, text in (extra or {}).items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    return root


INSTALL_BALE = r'''#!/usr/bin/env python3
import json, pathlib, sys
here = pathlib.Path(__file__).resolve().parent
v = (here / "VERSION").read_text().strip()
if sys.argv[1:] == ["--version"]:
    print("bale " + v); sys.exit(0)
print("install fake bale " + v + ": only --version", file=sys.stderr); sys.exit(97)
'''

INSTALL_SH = r'''#!/usr/bin/env bash
# The fake install.sh: records how it ran, as bale's would finish an install.
set -euo pipefail
d="$(cd "$(dirname "$0")" && pwd)"
echo "[install] install dir: $d"
echo "args: $*" > "$d/INSTALL-RAN"
mkdir -p "$HOME/.local/bin"; ln -sf "$d/bin/bale" "$HOME/.local/bin/bale"
echo "[install] install complete"
'''

# The shape of bale's own upgrade.sh (0.4.51, read in this session's
# probe): -y; user/ moved aside, the rest wiped, the release copied in,
# user/ put back, install.sh run.
UPGRADE_SH = r'''#!/usr/bin/env bash
set -euo pipefail
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"; YES=0; T=""
for a in "$@"; do case "$a" in -y|--yes) YES=1 ;; -*) echo "[upgrade] error: unknown flag: $a" >&2; exit 2 ;; *) T="$a" ;; esac; done
[ "$YES" = 1 ] || { echo "[upgrade] proceed? needs a terminal" >&2; exit 0; }
X="$(mktemp -d "${TMPDIR:-/tmp}/bale-upgrade.XXXXXX")"; trap 'rm -rf "$X"' EXIT
tar -xzf "$T" -C "$X"; R="$(dirname "$(dirname "$(find "$X" -path '*/bin/bale' | head -n 1)")")"
B="$INSTALL_DIR.user-backup-$$"
[ ! -d "$INSTALL_DIR/user" ] || mv "$INSTALL_DIR/user" "$B"
find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cp -R "$R"/. "$INSTALL_DIR"/
[ ! -d "$B" ] || mv "$B" "$INSTALL_DIR/user"
echo "[upgrade] upgrade staged"
rm -rf "$X"; trap - EXIT
exec "$INSTALL_DIR/install.sh" -y
'''


class LevelCase(unittest.TestCase):
    """An office scoping one hosted project whose host has its own HOME
    (a bale 0.4.40 install at ~/bale, linked from ~/.local/bin) and PATH;
    this machine's bale is a 0.4.51 release install first on the PATH."""

    there_version = "0.4.40"

    def setUp(self):
        self.e = Env(self)
        self.ssh = FakeSsh(self.e.tmp)
        self.here = fake_install(self.e.tmp / "here" / "bale", "0.4.51", {"bale.toml": "[identity]\nme = 1\n"},
                                 {".git/HEAD": "ref: refs/heads/main\n", ".bale/logs/x.log": "log\n",
                                  "bin/__pycache__/x.pyc": "cache", "tools/craft_response.py": "# tools\n"})
        self.host_home = self.ssh.host_dir(HOST) / "home"
        self.host_home.mkdir()
        if self.there_version:
            self.there = fake_install(self.host_home / "bale", self.there_version,
                                      {"bale.toml": "[apply]\nsearch_paths = []\n", "scripts/hook.sh": "echo hook\n"})
            (self.host_home / ".local" / "bin").mkdir(parents=True)
            (self.host_home / ".local" / "bin" / "bale").symlink_to(self.there / "bin" / "bale")
        (self.ssh.host_dir(HOST) / "path").write_text(f"{self.host_home}/.local/bin:/usr/bin:/bin\n")
        self.e.env["PATH"] = self.ssh.path(f"{self.here / 'bin'}{os.pathsep}{self.e.env['PATH']}")
        self.root = self.e.init()
        self.proj = git_repo(self.e.tmp / "far")
        h.add_project(self.root / "floor-plan/manifest.toml", "far", str(self.proj), h.check_host_keys(HOST))
        self.e.git(self.root, "commit", "-qam", "far")
        self.here_before = sorted(str(p.relative_to(self.here)) for p in self.here.rglob("*"))

    def run_office(self, *args, **kw):
        self.ssh.reset()
        return self.e.run(*args, cwd=self.root, **kw)


class TestLevelBale(LevelCase):
    def test_it_installs_this_machines_bale_keeping_the_hosts_user_and_says_both_versions(self):
        user_before = {p.relative_to(self.there / "user"): p.read_bytes() for p in (self.there / "user").rglob("*")
                       if p.is_file()}
        proc = self.run_office("projects", "level-bale", "far", "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"far: bale on {HOST} was 0.4.40, and is now 0.4.51, this machine's (from {self.here})",
                      proc.stdout)
        self.assertIn("its user/ was kept: bale.toml, scripts", proc.stdout)
        # The release went in through the host's own upgrade.sh, with -y,
        # and install.sh ran.
        self.assertEqual((self.there / "bin" / "VERSION").read_text().strip(), "0.4.51")
        self.assertEqual((self.there / "INSTALL-RAN").read_text().strip(), "args: -y")
        self.assertEqual((self.there / "docs" / "AGENT.md").read_text(), "docs of 0.4.51\n")
        self.assertTrue((self.there / "tools" / "craft_response.py").is_file())
        # Its user/ is as it was; this machine's user/, git, records and
        # caches did not travel.
        self.assertEqual({p.relative_to(self.there / "user"): p.read_bytes() for p in (self.there / "user").rglob("*")
                          if p.is_file()}, user_before)
        for gone in (".git", ".bale", "bin/__pycache__"):
            self.assertFalse((self.there / gone).exists(), gone)
        # This machine's install is untouched; nothing is left in the host's tmp.
        self.assertEqual(sorted(str(p.relative_to(self.here)) for p in self.here.rglob("*")), self.here_before)
        self.assertEqual(self.ssh.left_on(HOST), [])
        # Level now: a second run does nothing.
        proc = self.run_office("projects", "level-bale", "far", "--yes")
        self.assertIn(f"far: bale 0.4.51 on {HOST} is level with this machine's; nothing to do", proc.stdout)

    def test_piped_it_asks_nothing_and_names_yes(self):
        proc = self.run_office("projects", "level-bale", "far")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--yes does it (Replace bale 0.4.40 on", proc.stderr)
        self.assertEqual((self.there / "bin" / "VERSION").read_text().strip(), "0.4.40")

    def test_a_project_on_this_machine_and_a_host_that_is_newer_are_refused(self):
        h.add_project(self.root / "floor-plan/manifest.toml", "here", str(git_repo(self.e.tmp / "here-repo")))
        proc = self.run_office("projects", "level-bale", "here", "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("here is on this machine", proc.stderr)
        (self.there / "bin" / "VERSION").write_text("0.9.0\n")
        proc = self.run_office("projects", "level-bale", "far", "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("is newer than this machine's 0.4.51; the office never moves a bale back", proc.stderr)
        self.assertEqual((self.there / "bin" / "VERSION").read_text().strip(), "0.9.0")

    def test_a_failing_upgrade_says_its_last_words_and_leaves_no_tmp(self):
        (self.there / "upgrade.sh").write_text("#!/usr/bin/env bash\necho '[upgrade] error: the disk is full' >&2\nexit 1\n")
        proc = self.run_office("projects", "level-bale", "far", "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("the install on", proc.stderr)
        self.assertIn("the disk is full", proc.stderr)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_an_upgrade_that_changes_nothing_is_not_called_done(self):
        # An upgrade.sh that, without a terminal, declines and exits 0 (as
        # bale's does when it cannot ask): the version is read again.
        (self.there / "upgrade.sh").write_text("#!/usr/bin/env bash\necho '[upgrade] aborted by user; nothing changed'\n")
        proc = self.run_office("projects", "level-bale", "far", "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("exited 0, but bale there says 0.4.40, not 0.4.51", proc.stderr)


class TestLevelBaleOnAHostWithNone(LevelCase):
    there_version = None

    def test_a_first_install_unpacks_it_as_home_bale(self):
        proc = self.run_office("projects", "level-bale", "far", "--yes")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"far: bale on {HOST} was not installed, and is now 0.4.51", proc.stdout)
        self.assertEqual((self.host_home / "bale" / "bin" / "VERSION").read_text().strip(), "0.4.51")
        self.assertFalse((self.host_home / "bale" / "user").exists())
        self.assertEqual(self.ssh.left_on(HOST), [])


class TestLevelBaleAsked(LevelCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_on_a_terminal_it_asks_naming_both_versions(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "level-bale", "far"], self.root,
                                   self.e.env, [
            (f"Replace bale 0.4.40 on {HOST} with this machine's 0.4.51, keeping its user/ settings? (--yes) "
             "(y/n) [y]:".encode(), "n"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("nothing changed", seen)
        self.assertEqual((self.there / "bin" / "VERSION").read_text().strip(), "0.4.40")


class TestStatusNamesTheStep(LevelCase):
    def test_a_bale_behind_this_machines_is_named_with_the_step(self):
        # This machine's bale for the read side is the 0.4.51 install;
        # office status reads only its version.
        proc = self.run_office("status")
        self.assertIn(f"far: {HOST} answers; bale 0.4.40 on {HOST} is older than the read side's floor 0.4.45; "
                      f"{LEVEL} far brings it level with this machine's bale (0.4.51)", proc.stdout)
        (self.there / "bin" / "VERSION").write_text("0.4.48\n")
        proc = self.run_office("status")
        self.assertIn(f"bale 0.4.48 there, within the read side's range (bale 0.4.45 or later); this machine runs "
                      f"0.4.51, and {LEVEL} far brings it level", proc.stdout)


# --- 4. office start on a hosted project ----------------------------------------------------------

class HostedStartCase(LandCase):
    """LandCase's office (the fake land bale, alpha with its after-land
    action, the folder fix-login on alpha's lane) with alpha's repo also
    declared as `far` on a host the fake ssh reaches."""

    def setUp(self):
        super().setUp()
        self.ssh = FakeSsh(self.e.tmp)
        self.e.env["PATH"] = self.ssh.path(self.e.env["PATH"])
        self.e.run("projects", "add", "far", str(self.proj), "--host", HOST, "--connect", "start the VPN client",
                   cwd=self.root, check=0)

    def only_far(self):
        """The office scopes far alone (alpha's twin would hold the same
        sessions), as 0.14.0's land test does."""
        manifest = self.root / "floor-plan" / "manifest.toml"
        text = manifest.read_text()
        head, _, tail = text.partition("[projects.alpha]")
        rest = tail.split("[projects.far]", 1)[1]
        manifest.write_text(head + "[projects.far]" + rest)
        self.e.git(self.root, "commit", "-qam", "far alone")

    def run_office(self, *args, check=None, **kw):
        self.ssh.reset()
        return self.e.run(*args, cwd=self.root, check=check, **kw)

    def tray_of(self, out):
        return pathlib.Path(re.search(r"^Out tray: (.+)$", out, re.M).group(1))


class TestStartOnAHost(HostedStartCase):
    def test_a_pack_runs_on_the_host_and_the_request_comes_back_to_the_tray(self):
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it there", "--write", "src")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        tray = self.tray_of(proc.stdout)
        names = sorted(p.name for p in tray.iterdir())
        self.assertIn(f"request-{sid}.tar.gz", names)
        self.assertTrue(any(n.startswith("context-") for n in names), names)
        # The request in the tray is the one bale made on the host.
        outbox = self.proj / ".bale" / "outbox" / f"request-{sid}.tar.gz"
        self.assertEqual((tray / f"request-{sid}.tar.gz").read_bytes(), outbox.read_bytes())
        self.assertIn(f"far session, packed on {HOST} and carried back", proc.stdout)
        self.assertIn(f"{HOST} answers, with bale 0.4.45", proc.stderr)
        # bale's pack ran in far's repo, through the host's shell, with the
        # project constraint; the context packs ran here.
        pack = [(c, a) for c, a in self.fake_pack_calls() if a[0] == "pack" and "--context" not in a]
        self.assertEqual(len(pack), 1)
        self.assertEqual(pack[0][0], os.path.realpath(self.proj))
        self.assertIn(ob.PROJECT_CONSTRAINT, pack[0][1])
        self.assertTrue(all(c[0] == HOST for c in self.ssh.connections()))
        self.assertIn(sid, (self.root / self.folder / "folder.md").read_text())
        self.assertIn("--8<-- session opener --8<--", proc.stdout)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def fake_pack_calls(self):
        f = self.fake.dir / "pack-calls.jsonl"
        return [(c, a) for c, a in (json.loads(l) for l in f.read_text().splitlines())] if f.is_file() else []

    def test_the_brief_travels_to_the_host_and_is_removed_after(self):
        brief = self.e.tmp / "brief.md"
        brief.write_text("# The brief\n\nWords for the worker.\n")
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it", "--write", "src",
                               "--brief", str(brief))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        tray = self.tray_of(proc.stdout)
        request = next(tray.glob("request-*.tar.gz"))
        with tarfile.open(request) as t:
            self.assertEqual(t.extractfile("request-001/README.md").read(), brief.read_bytes())
        pack = [a for c, a in self.fake_pack_calls() if a[0] == "pack" and "--context" not in a][0]
        readme = pack[pack.index("--readme-file") + 1]
        self.assertTrue(readme.startswith(str(self.ssh.host_tmp(HOST))), readme)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_an_overlapping_open_session_is_refused_in_the_offices_words(self):
        brief = self.e.tmp / "brief.md"
        brief.write_text("# B\n")
        self.run_office("start", self.name, "--on", "far", "--goal", "Fix it", "--write", "src", "--brief",
                        str(brief), check=0)
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Again", "--write", "src", "--brief",
                               str(brief))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("is open in far", proc.stderr)
        self.assertIn("overlaps this one at src", proc.stderr)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_a_host_that_does_not_answer_stops_start_before_anything_is_written(self):
        self.run_office("projects", "set", "far", "--host", DOWN, "--connect", "start the VPN client", check=0)
        before = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it", "--write", "src")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"far: {DOWN} does not answer", proc.stderr)
        self.assertIn("start the VPN client; then rerun: office start", proc.stderr)
        self.assertIn("nothing was written", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), before)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertFalse((self.e.home / "out-tray").exists() and any((self.e.home / "out-tray").iterdir()))
        self.assertEqual([c[0] for c in self.ssh.connections()], [DOWN])

    def test_a_bale_below_the_floor_is_refused_naming_the_step(self):
        self.run_office("projects", "set", "far", "--host", OLD, check=0)
        before = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it", "--write", "src")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"far: bale 0.4.40 on {OLD} is older than the read side's floor 0.4.45, so no session goes out "
                      f"there; {LEVEL} far brings it level", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), before)

    def test_a_path_that_is_not_on_the_host_is_refused_through_the_shell(self):
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it", "--write", "nope")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"--write nope: no such path in {self.proj} on {HOST}", proc.stderr)
        self.assertEqual(self.ssh.left_on(HOST), [])


class TestABundleOnAHost(HostedStartCase):
    def test_check_and_open_run_on_the_host_with_the_bundle_sent_there(self):
        b = bundle_file(self.downloads, "2026-10-07-fix-there",
                        ["Fix it there", "--slug", "fix-there", "--write", "src", "--constraint", ob.PROJECT_CONSTRAINT],
                        brief="# Brief\n")
        before = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", self.name, "--on", "far", str(b))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        sid = re.search(r"^Packed (\S+) for ", proc.stdout, re.M).group(1)
        self.assertIn("fix-there", sid)
        checks, opens = self.fake.calls_of("open-check"), self.fake.calls_of("open")
        self.assertEqual(len(checks), 1)
        self.assertEqual(len(opens), 1)
        for c in checks + opens:
            self.assertEqual(c[0], os.path.realpath(self.proj))
            self.assertTrue(c[1][-1].startswith(str(self.ssh.host_tmp(HOST))), c)
            self.assertEqual(pathlib.Path(c[1][-1]).name, b.name)
        self.assertIn(f"bale found it at {b} (sent to {HOST} for the check)", proc.stderr)
        self.assertTrue((self.tray_of(proc.stdout) / f"request-{sid}.tar.gz").is_file())
        self.assertNotEqual(self.e.git(self.root, "rev-parse", "HEAD"), before)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_a_bundle_bale_refuses_on_the_host_writes_nothing_here_or_there(self):
        b = bundle_file(self.downloads, "2026-10-07-nopath", ["Fix it", "--slug", "nopath", "--write", "nope"])
        before = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", self.name, "--on", "far", str(b))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("names paths that are not in far's tree", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), before)
        self.assertEqual(self.ssh.left_on(HOST), [])

    def test_a_bare_name_needs_the_downloads_and_piped_names_the_key(self):
        """0.15.0 refused a bare name for a hosted project; since 0.16.0 it is
        found in this machine's downloads (tests/test_return_trip.py), and
        piped with the setting unset, start refuses naming the key."""
        b = bundle_file(self.downloads, "2026-10-07-bare", ["Fix it", "--slug", "bare", "--write", "src"])
        before = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.run_office("start", self.name, "--on", "far", b.name)
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"{b.name}, a bundle for far on {HOST}, is found on this machine by name", proc.stderr)
        self.assertIn("set downloads in ", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), before)
        self.assertEqual(self.fake.calls_of("open"), [])

    def test_a_hosted_place_answers_where_a_bundle_opens(self):
        self.only_far()
        self.addCleanup(os.environ.__setitem__, "PATH", os.environ.get("PATH", ""))
        os.environ["PATH"] = self.e.env["PATH"]
        ohost.forget_reach()
        self.addCleanup(ohost.forget_reach)
        b = bundle_file(self.downloads, "2026-10-07-where", ["Fix it", "--slug", "where", "--write", "src/a.py"])
        default, why = ob.bundle_where(self.root, str(b))
        self.assertEqual(default, "far")
        self.assertIn("is in far's tree, and in no other place", why)
        b = bundle_file(self.downloads, "2026-10-07-nowhere", ["Fix it", "--slug", "nowhere", "--write", "gone"])
        with self.assertRaises(ob.StartError) as cm:
            ob.bundle_where(self.root, str(b))
        self.assertIn("gone: in nowhere the office can see", "\n".join(cm.exception.lines))


# Land on a hosted project (0.15.0 said the return trip was not built):
# tests/test_return_trip.py.


# --- 5. the runner prints a failing test's traceback ----------------------------------------------

class TestTheRunnerSaysWhy(unittest.TestCase):
    def test_the_summary_carries_each_failing_tests_traceback_capped(self):
        tb = "\n".join(f"  frame {i}" for i in range(100)) + "\nAssertionError: the real reason"
        bad = {"job": "test_b", "run": 2, "failures": ["test_b.TestX.test_y"], "errors": ["test_b.TestX.test_z"],
               "unexpected_successes": [], "skipped": 0, "seconds": 1.0, "exit": 1, "log": "/logs/test_b.log",
               "tracebacks": {"test_b.TestX.test_y": tb, "test_b.TestX.test_z": "Traceback:\nOSError: gone"}}
        lines, failed = runner.summary([bad], 2, 1.0, "/logs")
        text = "\n".join(lines)
        self.assertTrue(failed)
        self.assertIn("AssertionError: the real reason", text)
        self.assertIn("OSError: gone", text)
        self.assertIn(f"lines above cut; the whole of it is in /logs/test_b.log", text)
        self.assertLessEqual(sum(1 for l in lines if "frame" in l), runner.TRACEBACK_LINES)

    def test_a_job_writes_its_tracebacks_into_its_result(self):
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="runner-tb-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        mod = tmp / "test_fails_here.py"
        mod.write_text("import unittest\nclass T(unittest.TestCase):\n"
                       "    def test_a(self):\n        self.assertEqual(1, 2, 'one is not two')\n")
        result = tmp / "r.json"
        proc = subprocess.run([sys.executable, "-B", "-c",
                               "import sys; sys.path[:0] = [sys.argv[1], sys.argv[2]]; import runner; "
                               "runner.TESTS = __import__('pathlib').Path(sys.argv[2]); "
                               "sys.exit(runner.run_job('test_fails_here', ['test_fails_here'], sys.argv[3]))",
                               str(REPO / "tests"), str(tmp), str(result)], capture_output=True, text=True, cwd=tmp)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        data = json.loads(result.read_text())
        self.assertIn("one is not two", data["tracebacks"]["test_fails_here.T.test_a"])


# --- what the probe captured from the host's bale --------------------------------------------------

FIX40 = REPO / ("cla" + "ude") / "fixtures" / "bale-0.4.40" / "host"


class TestTheHostsBale(unittest.TestCase):
    def test_every_line_is_the_one_the_probe_captured(self):
        files = sorted(FIX40.glob("*.json"))
        self.assertEqual(len(files), 4)
        for f in files:
            rec = json.loads(f.read_text(encoding="utf-8"))
            stream = "stdout" if "stdout" in rec else "output"
            for line, sha in zip(rec[stream], rec[stream + "_sha256"], strict=True):
                self.assertEqual(hashlib.sha256(line.encode()).hexdigest(), sha, f.name)
            self.assertIn("2026-10-07-out-trip-to-host-004", rec["captured"])

    def test_why_the_floor_refuses_a_session_there(self):
        """0.4.40's open has no --check: office start's rehearsal before it
        writes anything cannot run on it, so start refuses below the floor
        rather than reaching it."""
        load = lambda n: json.loads((FIX40 / n).read_text(encoding="utf-8"))  # noqa: E731
        self.assertEqual(load("version.json")["stdout"], ["bale 0.4.40"])
        usage = load("help-open-head.json")["stdout"][0]
        self.assertTrue(usage.startswith("usage: bale open"))
        self.assertNotIn("--check", usage)
        self.assertNotIn("clipboard", " ".join(load("help.json")["stdout"]).split("options:")[0])
        cons = ob.Consumption()
        self.assertLess(h.compare_versions("0.4.40", cons.floor), 0)

    def test_the_upgrade_surface_is_declared_and_never_a_bale_call(self):
        cons = ob.Consumption()
        spec = cons.surface("upgrade")
        self.assertEqual((spec["script"], spec["flags"], spec["first_install"]), ("upgrade.sh", ["-y"], ["install.sh", "-y"]))
        with self.assertRaises(ob.BaleError):
            cons.argv("upgrade")


# --- 6. the record ---------------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_version_the_releases_the_readme_and_the_doctrine(self):
        self.assertGreaterEqual(h.compare_versions((REPO / "VERSION").read_text().strip(), "0.15.0"), 0)
        releases = (REPO / "RELEASES.md").read_text()
        self.assertLess(releases.index("## 0.15.0"), releases.index("## 0.14.0"))
        readme = " ".join((REPO / "README.md").read_text().split())
        for words in ("--from", "--from-dirty-ok", "level-bale", "packed on its host"):
            self.assertIn(words, readme)
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        packing = doctrine.split("## 4.", 1)[1].split("## 5.", 1)[0].lower()
        self.assertIn("a project on a host is packed on its host", packing)
        reading = doctrine.split("## 10.", 1)[1].split("## 11.", 1)[0]
        for words in ("office projects level-bale", "never upgrade"):
            self.assertIn(words, reading)

    def test_the_fake_hosts_are_the_suites_own(self):
        for p in (REPO / "bin" / "office", *(REPO / "lib").glob("*.py")):
            self.assertNotIn("a-host.example", p.read_text(), p.name)


if __name__ == "__main__":
    unittest.main()
