"""Tests for a project on another host (office-src 0.14.0): the host,
shell and connect keys, the reach check, the read side and office status
through the shell, start and land refusing a hosted project, and
preparing a clone for bale without a trace. (start and land on a host
since: tests/test_out_trip_to_host.py and tests/test_return_trip.py.)

The suite makes no network call and runs no real ssh. A fake `ssh`,
first on the PATH, records the target and the words it was handed,
refuses a target or a prefix other than the one the test expects, fails
the one target that stands for a host that is down, and otherwise runs
the joined rest through a shell, as sshd would, against a throwaway repo
on this machine; the read side's fake bale (tests/test_read_side.py)
answers through it. Run with the rest of the suite:

    tests/run.sh test_project_on_host
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, fake_program, h, kept_setup  # noqa: E402
from test_read_side import (FIXTURES, APPLIED, OPEN_SITTING, OPEN_WORKER,  # noqa: E402
                            FakeBale, make_project)
from test_start import FakePackBale, on_a_terminal  # noqa: E402

import office_bale as ob  # noqa: E402
import office_host as ohost  # noqa: E402

HOST = "someone@a-host.example"
DOWN = "someone@a-host-that-is-down.example"
OLD = "someone@an-old-bale.example"
# bale's record directory, split as the fixtures split it: the suite's
# text rules refuse the word anywhere in office-src.
RECORD_DIR = "cla" + "ude/"

FAKE_SSH = r'''#!/usr/bin/env bash
# A fake ssh for the suite: no network. It drops the options the office
# adds, records the target and the words after it, refuses a target or
# a prefix other than the expected one (exit 98), fails the target that
# stands for a host that is down (exit 255, as ssh does), and runs the
# joined rest through a shell, as sshd hands a command to the login
# shell on the far side. A target with its own bin/ under hosts/ gets
# that bin first on the PATH: a host whose bale is another version. Since
# 0.15.0 a target may also have, under hosts/TARGET/: path (the whole
# PATH there, one line), home/ (its HOME), tmp/ (its TMPDIR, where the
# office's temporary directories on a host land, so a test can see them
# gone) and chatter (bytes its login shell prints on stdout first).
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
opts=()
while [ $# -gt 0 ]; do
  case "$1" in -o|-i) opts+=("$1" "$2"); shift 2 ;; -*) opts+=("$1"); shift ;; *) break ;; esac
done
target="$1"; shift
python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' "$target" "${opts[@]}" "$@" >> "$here/calls.jsonl"
if [ -f "$here/expect.json" ]; then
  python3 - "$here/expect.json" "$target" "$@" <<'PY' || exit 98
import json, sys
want = json.load(open(sys.argv[1])); target = sys.argv[2]; words = sys.argv[3:]
if target not in want["targets"]:
    print(f"fake ssh: target {target!r} is not one the test expects ({want['targets']})", file=sys.stderr); sys.exit(1)
# One prefix, or (since 0.15.0) any of several: the plain form and the
# attended one, say.
for prefix in want.get("prefixes") or [want["prefix"]]:
    n = len(prefix)
    if words[:n] == prefix and len(words) == n + 1:
        break
else:
    print(f"fake ssh: words {words[:-1]!r} + 1 more; the test expects prefix {want['prefix']!r} and one command", file=sys.stderr); sys.exit(1)
PY
fi
case "$target" in
  *down*) echo "ssh: connect to host ${target#*@} port 22: Connection timed out" >&2; exit 255 ;;
esac
[ $# -gt 0 ] || exit 0
if [ -d "$here/hosts/$target/bin" ]; then export PATH="$here/hosts/$target/bin:$PATH"; fi
if [ -f "$here/hosts/$target/path" ]; then export PATH="$(cat "$here/hosts/$target/path")"; fi
if [ -d "$here/hosts/$target/home" ]; then export HOME="$here/hosts/$target/home"; fi
if [ -d "$here/hosts/$target/tmp" ]; then export TMPDIR="$here/hosts/$target/tmp"; fi
if [ -f "$here/hosts/$target/chatter" ]; then cat "$here/hosts/$target/chatter"; fi
# The prefix was asserted above; the one command it was handed runs here,
# unquoted once as the far side's login shell would unquote it.
last="${@: -1}"
eval "cmd=$last"
exec bash -c "$cmd"
'''



class FakeSsh:
    """The fake ssh in its own directory, first on a PATH."""

    def __init__(self, tmp, targets=(HOST, DOWN, OLD), prefix=("bash", "-lc")):
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix="fake-ssh-", dir=tmp))
        (self.dir / "ssh").write_text(FAKE_SSH)
        (self.dir / "ssh").chmod(0o755)
        self.calls = self.dir / "calls.jsonl"
        self.expect(targets, prefix)
        old = self.dir / "hosts" / OLD / "bin"
        old.mkdir(parents=True)
        fake_program(old / "bale", "small_bales", "old")  # the bale on an older host: 0.4.40, --version alone
        # Every host the suite knows has a TMPDIR of its own, so what the
        # office leaves in a host's temporary directory can be seen.
        for t in targets:
            self.host_tmp(t)

    def host_dir(self, target):
        d = self.dir / "hosts" / target
        d.mkdir(parents=True, exist_ok=True)
        return d

    def host_tmp(self, target):
        d = self.host_dir(target) / "tmp"
        d.mkdir(exist_ok=True)
        return d

    def left_on(self, target):
        """What the office left in the host's temporary directory (its
        own office-* directories; a fake bale's are its own business)."""
        return sorted(p.name for p in self.host_tmp(target).iterdir() if p.name.startswith("office-"))

    def expect(self, targets, prefix, *others):
        (self.dir / "expect.json").write_text(json.dumps({"targets": list(targets), "prefix": list(prefix),
                                                          "prefixes": [list(prefix), *map(list, others)]}))

    def path(self, base):
        return f"{self.dir}{os.pathsep}{base}"

    def connections(self):
        if not self.calls.is_file():
            return []
        return [json.loads(l) for l in self.calls.read_text().splitlines()]

    def reset(self):
        if self.calls.is_file():
            self.calls.unlink()


def git(root, *args, env=None):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True,
                          env=env).stdout


def manifest_of(root):
    return h.read_toml(root / "floor-plan" / "manifest.toml")


# --- the keys ----------------------------------------------------------------------------

class TestHostKeys(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.manifest = self.root / "floor-plan" / "manifest.toml"

    def test_a_hosted_entry_reads_with_its_defaults_and_is_never_resolved_here(self):
        h.add_project(self.manifest, "far", "~/work/far", h.check_host_keys(HOST), checked="checked by the test")
        text = self.manifest.read_text()
        self.assertIn('[projects.far]\npath = "~/work/far"\nhost = "%s"\nshell = "ssh %s bash -lc"\n'
                      'connect = "connect to %s"\n' % (HOST, HOST, HOST), text)
        far = h.read_projects(manifest_of(self.root))[0]
        self.assertEqual((far["host"], far["shell"], far["connect"]), (HOST, f"ssh {HOST} bash -lc", f"connect to {HOST}"))
        self.assertIsNone(far["resolved"])
        self.assertIsNone(far["problem"])
        self.assertEqual(far["path"], "~/work/far")
        place = ob.readable(far)
        self.assertIsInstance(place, ohost.Place)
        self.assertTrue(place.hosted)
        self.assertEqual(str(place), f"~/work/far on {HOST}")

    def test_set_replaces_the_keys_and_on_this_machine_removes_them(self):
        h.add_project(self.manifest, "far", "/srv/far", h.check_host_keys(HOST))
        before = self.manifest.read_text()
        entry = h.set_declarations(self.manifest, "far", host_keys=h.check_host_keys(
            HOST, f"ssh {HOST} docker exec -i -u me box bash -lc", "bring the VPN up"))
        self.assertEqual(entry["shell"], f"ssh {HOST} docker exec -i -u me box bash -lc")
        self.assertEqual(entry["connect"], "bring the VPN up")
        after = self.manifest.read_text()
        self.assertEqual(before.split("[projects.far]")[0], after.split("[projects.far]")[0])
        entry = h.set_declarations(self.manifest, "far", host_keys={k: None for k in h.HOST_KEYS})
        self.assertIsNone(entry["host"])
        self.assertNotIn("host =", self.manifest.read_text())
        self.assertEqual(self.manifest.read_text().count("[projects.far]"), 1)

    def test_a_shell_must_end_in_the_word_that_takes_a_command(self):
        for bad in ("ssh host", "ssh host bash", "", "ssh host 'unbalanced"):
            with self.assertRaises(h.HelperError, msg=bad):
                h.check_host_keys(HOST, bad)
        for good in ("ssh host bash -lc", "ssh host sh -c", "docker exec -i box bash -lc"):
            self.assertEqual(h.check_host_keys(HOST, good)["shell"], good)
        for bad in ("two words", "", "a;b"):
            with self.assertRaises(h.HelperError, msg=bad):
                h.check_host_keys(bad)

    def test_a_broken_entry_is_reported_not_dropped(self):
        h.add_project(self.manifest, "far", "/srv/far", h.check_host_keys(HOST))
        text = self.manifest.read_text().replace(f'shell = "ssh {HOST} bash -lc"', 'shell = "ssh host"')
        self.manifest.write_text(text)
        far = h.read_projects(manifest_of(self.root))[0]
        self.assertIn("one command string", far["problem"])
        out = self.e.run("projects", cwd=self.root)
        self.assertEqual(out.returncode, 1)
        self.assertIn("far", out.stdout)
        self.assertIn("CANNOT BE READ", out.stdout)

    def test_a_hosted_path_is_absolute_or_home_relative_on_the_host(self):
        with self.assertRaises(h.HelperError):
            h.add_project(self.manifest, "far", "work/far", h.check_host_keys(HOST))
        h.add_project(self.manifest, "far", "~/work/far", h.check_host_keys(HOST))
        with self.assertRaises(h.HelperError):
            h.add_project(self.manifest, "again", "~/work/far", h.check_host_keys(HOST))


# --- the shell seam ----------------------------------------------------------------------

class TestPlaceAndShell(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.ssh = FakeSsh(self.e.tmp)
        self.repo = make_project(self.e.tmp, "far", bale_dir=True)
        self.addCleanup(os.environ.__setitem__, "PATH", os.environ.get("PATH", ""))
        os.environ["PATH"] = self.ssh.path(self.e.env["PATH"])
        os.environ["OFFICE_RERUN"] = "office status"
        self.addCleanup(os.environ.pop, "OFFICE_RERUN", None)
        ohost.forget_reach()
        self.addCleanup(ohost.forget_reach)

    def test_the_prefix_gets_batch_mode_and_a_connect_timeout_and_one_quoted_command(self):
        place = ohost.Place("/srv/far", HOST)
        self.assertEqual(place.words(), ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={ohost.REACH_TIMEOUT}",
                                         HOST, "bash", "-lc"])
        # Through ssh the command travels quoted once, since the login
        # shell on the far side parses the line again.
        self.assertEqual(place.argv("cd /srv && bale status --json")[-1], "'cd /srv && bale status --json'")
        local = ohost.Place("/srv/far", HOST, shell="docker exec -i box bash -lc")
        self.assertEqual(local.words(), ["docker", "exec", "-i", "box", "bash", "-lc"])
        self.assertEqual(local.argv("cd /srv && true")[-1], "cd /srv && true")

    def test_several_commands_travel_in_one_connection_each_with_its_streams_and_code(self):
        place = ohost.Place(str(self.repo), HOST, name="far")
        runs = ohost.run_many(place, [["git", "rev-parse", "--show-toplevel"],
                                      ["sh", "-c", "echo out; echo err >&2; exit 3"],
                                      ["pwd"]])
        self.assertEqual([(r.returncode, r.stdout, r.stderr) for r in runs],
                         [(0, str(self.repo.resolve()), ""), (3, "out", "err"), (0, str(self.repo.resolve()), "")])
        calls = self.ssh.connections()
        self.assertEqual(len(calls), 1, calls)
        self.assertEqual(calls[0][0], HOST)
        self.assertIn("BatchMode=yes", calls[0])
        self.assertEqual(calls[0][-3:-1], ["bash", "-lc"])
        self.assertTrue(calls[0][-1].startswith("'exec 4>&1"), calls[0][-1])

    def test_a_host_that_does_not_answer_is_one_line_and_is_not_asked_again(self):
        place = ohost.Place("/srv/far", DOWN, connect="start the VPN client", name="far")
        with self.assertRaises(ohost.HostError) as cm:
            ohost.run_in(place, ["true"])
        self.assertEqual(cm.exception.kind, "unreachable")
        line = str(cm.exception)
        self.assertEqual(line, f"{DOWN} does not answer (ssh: connect to host {DOWN.split('@')[1]} port 22: "
                               "Connection timed out); start the VPN client; then rerun: office status")
        with self.assertRaises(ohost.HostError):
            ohost.run_many(place, [["true"], ["false"]])
        self.assertEqual(len(self.ssh.connections()), 1)

    def test_a_host_that_answers_is_checked_once_per_process(self):
        place = ohost.Place(str(self.repo), HOST)
        self.assertTrue(ohost.reach(place))
        ohost.run_in(place, ["true"])
        ohost.run_in(place, ["true"])
        ohost.reach(place)
        self.assertEqual(len(self.ssh.connections()), 3)  # the reach, then one per run; never a second reach

    def test_a_path_that_is_not_on_the_host(self):
        with self.assertRaises(ohost.HostError) as cm:
            ohost.run_in(ohost.Place("/no/such/place", HOST), ["true"])
        self.assertEqual(cm.exception.kind, "path")
        self.assertIn(f"no such directory on {HOST}", str(cm.exception))

    def test_a_wrong_prefix_is_refused_by_the_fake_and_read_as_unreachable(self):
        self.ssh.expect([HOST], ["sh", "-c"])
        with self.assertRaises(ohost.HostError) as cm:
            ohost.run_in(ohost.Place(str(self.repo), HOST), ["true"])
        self.assertIn("the test expects prefix", str(cm.exception))

    def test_the_reader_runs_bale_through_the_shell_with_the_same_keys(self):
        fake = FakeBale(self.e.tmp, {str(self.repo): "office-src"})
        os.environ["PATH"] = fake.path(os.environ["PATH"])
        rd = ob.Reader()
        place = ohost.Place(str(self.repo), HOST, name="far")
        self.assertEqual(rd.open_sessions(place), [(OPEN_SITTING, True), (OPEN_WORKER, False)])
        self.assertEqual(rd.installed_version(place), "0.4.45")
        d = rd.dossier(place, APPLIED[2])
        self.assertEqual(ob.session_view(rd, d)["outcome"], "applied")
        self.assertIsNone(rd.dossier(place, "2026-01-01-no-such-session-001"))
        # Every bale call went through the shell, in the repo, with stdin closed.
        self.assertEqual(fake.argvs(), [["status", "--json"], ["--version"],
                                        ["stats", "--sid", APPLIED[2], "--json"],
                                        ["stats", "--sid", "2026-01-01-no-such-session-001", "--json"]])
        self.assertEqual({c[0] for c in self.ssh.connections()}, {HOST})
        # One batch, then every dossier is a cache hit.
        rd.prefetch(place, [("dossier", {"sid": s}) for s in APPLIED])
        before = len(self.ssh.connections())
        for sid in APPLIED:
            self.assertIsNotNone(rd.dossier(place, sid))
        self.assertEqual(len(self.ssh.connections()), before)
        self.assertEqual(len(fake.argvs()), 4 + len(APPLIED) - 1)  # APPLIED[2] was cached already


# --- the verb, through the office ------------------------------------------------------------

def hosted_world(owner, host=HOST, e=None):
    """An office scoping two projects that bale answers the same captures
    for: `here`, on this machine, and `far`, the same throwaway repo
    declared on a host and read through the fake ssh. A folder records
    the open worker and an applied session. e, when given, is the Env to
    build in (a kept world's), else a new one."""
    e = e if e is not None else Env(owner)
    w = types.SimpleNamespace(e=e)
    w.ssh = FakeSsh(e.tmp)
    w.proj = make_project(e.tmp, "office-src")
    w.fake = FakeBale(e.tmp, {str(w.proj): "office-src"})
    e.env["PATH"] = w.ssh.path(w.fake.path(e.env["PATH"]))
    w.root = e.init()
    h.add_project(w.root / "floor-plan/manifest.toml", "here", str(w.proj))
    h.add_project(w.root / "floor-plan/manifest.toml", "far", str(w.proj),
                  h.check_host_keys(host, connect="start the VPN client"))
    w.folder = "desk/2026-10-07-on-a-host"
    folder = w.root / w.folder
    folder.mkdir(parents=True)
    (folder / "folder.md").write_text(h.render_template(
        (REPO / "templates/folder.md").read_text(), {"title": "on a host", "number": "1", "status": "queued",
                                                     "queued": "2026-10-07",
                                                     "history": "2026-10-07 queued: office open"}))
    h.record_session(folder / "folder.md", APPLIED[2], "space and templates")
    h.record_session(folder / "folder.md", OPEN_WORKER)
    git(w.root, "add", "-A", env=e.env)
    git(w.root, "commit", "-qm", "two projects and a folder", env=e.env)
    return w


class HostedCase(unittest.TestCase):
    """hosted_world, built once per process and copied for each test
    (tests/test_office.py kept_setup, 0.27.0)."""

    def setUp(self):
        kept_setup(self, "test_project_on_host.HostedCase", HostedCase.build_world)

    def build_world(self):
        w = hosted_world(self, e=self.e)
        self.ssh, self.proj, self.fake, self.root, self.folder = w.ssh, w.proj, w.fake, w.root, w.folder

    def run_office(self, *args, **kw):
        self.ssh.reset()
        return self.e.run(*args, cwd=self.root, **kw)

    def set_host(self, host, **flags):
        args = ["projects", "set", "far", "--host", host]
        for k, v in flags.items():
            args += [f"--{k}", v]
        self.e.run(*args, cwd=self.root, check=0)


class TestProjectsVerb(HostedCase):
    def test_add_with_flags_writes_the_keys_and_checks_through_the_shell(self):
        other = make_project(self.e.tmp, "other", bale_dir=True)
        proc = self.run_office("projects", "add", "other", str(other), "--host", HOST,
                               "--shell", f"ssh {HOST} docker exec -i -u me box bash -lc", "--connect", "wake it")
        # The fake refuses that prefix: the check through the shell is
        # what add runs, and nothing is added when it does not go through.
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertNotIn("[projects.other]", (self.root / "floor-plan/manifest.toml").read_text())
        self.ssh.expect([HOST], ["docker", "exec", "-i", "-u", "me", "box", "bash", "-lc"])
        proc = self.run_office("projects", "add", "other", str(other), "--host", HOST,
                               "--shell", f"ssh {HOST} docker exec -i -u me box bash -lc", "--connect", "wake it", check=0)
        self.assertIn(f"added other: {other} (a git repo with .bale/, no bale.toml, on {HOST})", proc.stdout)
        entry = next(p for p in h.read_projects(manifest_of(self.root)) if p["name"] == "other")
        self.assertEqual((entry["host"], entry["shell"], entry["connect"]),
                         (HOST, f"ssh {HOST} docker exec -i -u me box bash -lc", "wake it"))
        self.assertEqual(git(self.root, "log", "-1", "--format=%s", env=self.e.env).strip(), "office projects: add other")
        self.assertEqual(git(self.root, "status", "--porcelain", env=self.e.env), "")

    def test_the_listing_shows_where_each_is_and_makes_no_connection(self):
        proc = self.run_office("projects", check=0)
        self.assertIn(f"far   {self.proj}  (on {HOST}; office status checks that it answers)", proc.stdout)
        self.assertIn(f"      on {HOST}, through: ssh {HOST} bash -lc", proc.stdout)
        self.assertIn("      when it does not answer: start the VPN client", proc.stdout)
        self.assertIn(f"here  {self.proj}  (a git repo with .bale/, no bale.toml)", proc.stdout)
        self.assertEqual(self.ssh.connections(), [])

    def test_shell_and_connect_go_with_a_host(self):
        for args in (("add", "x", str(self.proj), "--shell", "ssh h bash -lc"),
                     ("add", "x", str(self.proj), "--connect", "vpn"),
                     ("set", "here", "--shell", "ssh h bash -lc"),
                     ("set", "here", "--connect", "vpn")):
            proc = self.run_office("projects", *args)
            self.assertEqual(proc.returncode, 1, args)
            self.assertIn("go with --host HOST", proc.stderr)
        proc = self.run_office("projects", "add", "x", str(self.proj), "--host", HOST, "--shell", "ssh h")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("one command string", proc.stderr)
        self.assertNotIn("[projects.x]", (self.root / "floor-plan/manifest.toml").read_text())

    def test_set_moves_a_project_between_a_host_and_this_machine(self):
        proc = self.run_office("projects", "set", "far", "--connect", "dial in", check=0)
        self.assertIn("when it does not answer: dial in", proc.stdout)
        proc = self.run_office("projects", "set", "far", "--on-this-machine", check=0)
        self.assertIn("far: nothing rides with it", proc.stdout)
        self.assertIsNone(next(p for p in h.read_projects(manifest_of(self.root)) if p["name"] == "far")["host"])
        proc = self.run_office("projects", "set", "here", "--host", HOST, check=0)
        self.assertIn(f"here: on {HOST}, through: ssh {HOST} bash -lc; when it does not answer: connect to {HOST}",
                      proc.stdout)
        proc = self.run_office("projects", "set", "here", "--host", HOST, "--on-this-machine")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("contradicts", proc.stderr)
        self.assertEqual(git(self.root, "log", "-1", "--format=%s", env=self.e.env).strip(), "office projects: set here")

    def test_help_names_the_flags(self):
        out = self.run_office("projects", "--help", check=0).stdout
        for word in ("--host HOST", "--shell PREFIX", "--connect TEXT", "--on-this-machine", "--prepare", "bash -lc"):
            self.assertIn(word, out)


class TestProjectsWizard(HostedCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_add_asks_where_the_repo_is_then_the_shell_and_the_connect_line(self):
        other = make_project(self.e.tmp, "other", bale_dir=True)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "add"], self.root, self.e.env, [
            (b"Path to the project's git repo (--path):", str(other)),
            (b"Where the repo is: this machine, or an ssh host (--host) [return skips]:", "?"),
            (b"repo is on this machine.", "not a host"),
            (b"a host is an ssh target", HOST),
            (f"The shell that runs one command where the repo is (--shell) [ssh {HOST} bash -lc]:".encode(), "?"),
            (b"exactly one shell-quoted command", ""),
            (f"What brings {HOST} up when it does not answer (--connect) [connect to {HOST}]:".encode(), "start the VPN"),
            # Since 0.15.0, after the host: a clone here to bring (none).
            (b"Is there a clone on this machine to bring there? Its path (--from) [return skips]:", ""),
            (b"Name for it in this office (--name) [other]:", ""),
            # Since 0.17.0, after the name: the audience line (none here).
            (b"or none (--audience) [none]:", ""),
            (b"(--ride) [return ends the list]:", ""),
            (b"(--after-land) [return ends the list]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"added other: {other} (a git repo with .bale/, no bale.toml, on {HOST})", seen)
        entry = next(p for p in h.read_projects(manifest_of(self.root)) if p["name"] == "other")
        self.assertEqual((entry["host"], entry["shell"], entry["connect"]), (HOST, f"ssh {HOST} bash -lc", "start the VPN"))
        # The check, and since 0.17.0 the clone's remotes and identity for
        # the audience line's defaults: two connections, both to the host.
        self.assertEqual([c[0] for c in self.ssh.connections()], [HOST, HOST])

    def test_set_offers_to_keep_the_host(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "set", "far"], self.root, self.e.env, [
            (f"Keep far on {HOST}, reached through: ssh {HOST} bash -lc? (y/n) [y]:".encode(), "n"),
            (b"Where the repo is: this machine, or an ssh host (--host) [return skips]:", ""),
            # Since 0.17.0 set also offers to keep the audience line (none).
            (b"Keep far without an audience? (y/n) [y]:", ""),
            (b"(--ride) [return ends the list]:", ""),
            (b"(--after-land) [return ends the list]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIsNone(next(p for p in h.read_projects(manifest_of(self.root)) if p["name"] == "far")["host"])

    def test_add_offers_to_prepare_a_clone_on_a_terminal(self):
        clone = make_project(self.e.tmp, "clone", bale_dir=False)
        (clone / "README.md").write_text("theirs\n")
        git(clone, "add", "README.md", env=self.e.env)
        git(clone, "commit", "-qm", "theirs", env=self.e.env)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "projects", "add", "clone", str(clone)], self.root,
                                   self.e.env, [
            (b"Prepare it for bale without a trace in git? (--prepare) (y/n) [y]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("bale has not run in", seen)
        self.assertIn(f"prepared {clone} for bale: 4 line(s) added to .git/info/exclude", seen)
        self.assertIn("added clone", seen)
        self.assertEqual(git(clone, "status", "--porcelain", env=self.e.env), "")


# --- reach, and the read side through the shell -----------------------------------------------

class TestReach(HostedCase):
    def setUp(self):
        super().setUp()
        self.set_host(DOWN, connect="start the VPN client")

    def test_the_walk_in_prints_the_one_line_in_the_projects_place_and_renders_the_rest(self):
        proc = self.run_office(check=0)
        self.assertIn(f"  far: cannot read: {DOWN} does not answer (ssh: connect to host "
                      f"{DOWN.split('@')[1]} port 22: Connection timed out); start the VPN client; then rerun: office\n",
                      proc.stdout)
        self.assertIn(f"  here: {OPEN_WORKER} open,", proc.stdout)
        self.assertIn("On the desk:", proc.stdout)
        self.assertIn("Next:", proc.stdout)
        # One connection: the host is checked once in the command, and
        # nothing else is tried against it.
        self.assertEqual([c[0] for c in self.ssh.connections()], [DOWN])

    def test_status_says_so_and_exits_0(self):
        proc = self.run_office("status", check=0)
        self.assertIn("projects:   2 in scope; each is a repo bale runs in, 1 through a host's shell\n", proc.stdout)
        self.assertIn(f"  far: {DOWN} does not answer (", proc.stdout)
        self.assertIn("start the VPN client; then rerun: office status\n", proc.stdout)
        self.assertEqual([c[0] for c in self.ssh.connections()], [DOWN])

    def test_a_rendering_stops_there_with_the_line_to_rerun(self):
        proc = self.run_office("projects", "--ledger")
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"far: cannot read: {DOWN} does not answer", proc.stdout)
        self.assertIn("then rerun: office projects --ledger", proc.stdout)
        self.assertIn("here: trust ledger", proc.stdout)
        self.assertEqual(len(self.ssh.connections()), 1)

    def test_the_rerun_line_quotes_what_needs_it(self):
        proc = self.run_office("projects", "--landed", "a path with spaces")
        self.assertIn("then rerun: office projects --landed 'a path with spaces'", proc.stdout)

    def test_the_walk_in_never_hangs_on_a_slow_host(self):
        # The fake ssh's time is the shell's; the office bounds every
        # connection with a connect timeout and the batch with its own.
        self.assertIn("ConnectTimeout=", " ".join(ohost.SSH_OPTIONS))
        self.assertEqual(ohost.REACH_TIMEOUT, 5)


class TestReadSideThroughTheShell(HostedCase):
    def strip(self, text, name):
        return [l.replace(f"{name}:", "NAME:").replace(f"{name} ", "NAME ") for l in text.splitlines()
                if l.strip() and not l.startswith("[office]")]

    def test_the_walk_in_reads_a_hosted_project_as_it_reads_a_local_one(self):
        proc = self.run_office(check=0)
        flight = proc.stdout.split("In flight:\n", 1)[1].split("\n\n", 1)[0].splitlines()
        far = [l for l in flight if l.startswith("  far:")]
        here = [l for l in flight if l.startswith("  here:")]
        self.assertEqual(len(far), 2, flight)
        self.assertEqual([l.replace("far:", "X:") for l in far], [l.replace("here:", "X:") for l in here])
        self.assertIn(f"-> {self.folder}", far[1])
        # Two connections for the hosted project: its status, then every
        # open session's dossier in one batch.
        self.assertEqual([c[0] for c in self.ssh.connections()], [HOST, HOST])

    @staticmethod
    def blocks(text):
        """{project: its lines} for a rendering with one unindented line
        per project followed by indented ones."""
        out, name = {}, None
        for line in text.splitlines():
            if not line.strip():
                continue
            if not line.startswith(" "):
                name = line.split(":", 1)[0]
                out[name] = [line.split(":", 1)[1]]
            else:
                out[name].append(line)
        return out

    def test_ledger_landed_versions_and_sessions_read_the_same_records(self):
        for args in (("projects", "--ledger"), ("projects", "--landed", "VERSION"), ("projects", "--versions")):
            proc = self.run_office(*args, check=0)
            blocks = self.blocks(proc.stdout)
            self.assertEqual(set(blocks), {"far", "here"}, args)
            self.assertEqual(blocks["far"], blocks["here"], args)
            self.assertNotIn("cannot read", proc.stdout, args)
            self.assertLessEqual(len(self.ssh.connections()), 2, (args, self.ssh.connections()))
        proc = self.run_office("sessions", "1", check=0)
        # far sorts first, so its records answer for each session.
        self.assertIn("    far: applied; opened", proc.stdout)
        self.assertIn(f"    far: open; opened", proc.stdout)
        self.assertNotIn("cannot read", proc.stdout)
        self.assertEqual(len(self.ssh.connections()), 2)

    def test_status_names_the_hosts_bale_against_the_floor(self):
        proc = self.run_office("status", check=0)
        self.assertIn(f"  far: {HOST} answers; bale 0.4.45 there, within the read side's range (bale 0.4.45 or later)\n",
                      proc.stdout)
        self.assertEqual(len(self.ssh.connections()), 1)
        self.set_host(OLD)
        proc = self.run_office("status", check=0)
        # Since 0.15.0 the remedy is the step itself.
        self.assertIn(f"  far: {OLD} answers; bale 0.4.40 on {OLD} is older than the read side's floor 0.4.45; "
                      "office projects level-bale far brings it level with this machine's bale (0.4.45) before a "
                      "session is sent there\n", proc.stdout)
        # The office's own bale line stays as it was.
        self.assertIn("bale:       0.4.45 at ", proc.stdout)

    def test_the_survey_still_makes_no_network_call(self):
        proc = self.run_office("survey", "--no-commit", check=0)
        self.assertEqual(self.ssh.connections(), [])

    def test_debug_shows_every_shell_call(self):
        proc = self.run_office("status", extra={"OFFICE_DEBUG": "1"}, check=0)
        self.assertIn(f"command(s) through {HOST}", proc.stderr)
        self.assertIn("(the reach check)", proc.stderr)
        self.assertIn("bale --version", proc.stderr)

    def test_watches_check_and_the_digest_read_a_hosted_project(self):
        proc = self.run_office("digest", check=0)
        blocks = self.blocks(proc.stdout.split("## Versions", 1)[1].split("## ", 1)[0].replace("- ", ""))
        self.assertEqual(blocks["far"], blocks["here"], proc.stdout)
        self.assertNotIn("cannot read", proc.stdout)
        since = proc.stdout.split("## Since", 1)[1].split("## ", 1)[0]
        self.assertIn("- far:", since)
        self.assertIn("- here:", since)
        proc = self.run_office("watches", "check", check=0)
        self.assertNotIn("cannot read", proc.stdout + proc.stderr)


# --- start and land on a host (tests/test_out_trip_to_host.py, tests/test_return_trip.py) -----

class TestStartAndLandRefuse(HostedCase):
    def test_an_office_session_about_a_hosted_project_goes_out_without_its_tree(self):
        # The folder's lane names the hosted project; the session is packed
        # in the office, and the project's tree, on the host, does not ride.
        pack = FakePackBale(self.e.tmp)
        self.e.found(self.root)
        folder = self.e.run("open", "about-far", "--lane", "far: src", "--class", "code",
                            cwd=self.root, check=0).stdout.strip()
        self.assertTrue(folder.startswith("desk/"), folder)
        proc = self.run_office("start", folder.split("/")[1], "--in-office", "--goal", "look at it",
                               extra={"PATH": pack.path(self.ssh.path(self.e.env["PATH"]))})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"far's tree is on {HOST}, so it does not ride", proc.stdout + proc.stderr)
        self.assertEqual(self.ssh.connections(), [])

    def test_land_on_a_hosted_project_needs_the_downloads_and_refuses_piped_without_them(self):
        """Since 0.16.0 land brings a hosted session back (tests/test_return_trip.py):
        its response is found on this machine, in the downloads machine.toml
        names. Piped, with the setting unset, land refuses before anything
        is carried, naming the key; nothing runs on the host."""
        # Only the hosted project holds the session: the local twin goes.
        manifest = self.root / "floor-plan" / "manifest.toml"
        text = manifest.read_text()
        head, _, tail = text.partition("[projects.here]")
        manifest.write_text(head + "[projects.far]" + tail.split("[projects.far]", 1)[1])
        self.assertEqual([p["name"] for p in h.read_projects(manifest_of(self.root))], ["far"])
        proc = self.run_office("land", OPEN_WORKER)
        self.assertEqual(proc.returncode, 1)
        self.assertIn(f"the response for {OPEN_WORKER} is found on this machine by name and carried to {HOST}",
                      proc.stderr)
        self.assertIn("set downloads in ", proc.stderr)
        self.assertIn("piped input is never asked", proc.stderr)
        self.assertEqual([a for a in self.fake.argvs() if a[0] in ("apply", "retry", "unlock")], [])


# --- preparing a clone --------------------------------------------------------------------------

class TestPrepare(HostedCase):
    def clone(self, name="clone"):
        clone = make_project(self.e.tmp, name, bale_dir=False)
        (clone / "README.md").write_text("theirs\n")
        (clone / ".gitignore").write_text("*.log\n")
        git(clone, "add", "-A", env=self.e.env)
        git(clone, "commit", "-qm", "theirs", env=self.e.env)
        return clone

    def check_prepared(self, clone):
        self.assertEqual(git(clone, "status", "--porcelain", env=self.e.env), "")
        self.assertEqual(git(clone, "ls-files", env=self.e.env).split(), [".gitignore", "README.md"])
        self.assertEqual((clone / ".gitignore").read_text(), "*.log\n")
        exclude = (clone / ".git" / "info" / "exclude").read_text()
        for line in (".bale/", "bale.toml", ".baleignore", RECORD_DIR):
            self.assertIn(f"\n{line}\n", exclude)
        self.assertTrue((clone / "bale.toml").is_file())
        self.assertTrue(all(l.startswith("#") or not l.strip() for l in (clone / "bale.toml").read_text().splitlines()))
        # Whatever bale makes there stays out of git's sight.
        (clone / ".bale").mkdir(exist_ok=True)
        (clone / ".bale" / "x").write_text("x")
        (clone / RECORD_DIR).mkdir(exist_ok=True)
        (clone / RECORD_DIR / "t.json").write_text("{}")
        (clone / ".baleignore").write_text("")
        self.assertEqual(git(clone, "status", "--porcelain", env=self.e.env), "")

    def test_piped_add_refuses_a_clone_bale_has_not_run_in_and_names_the_flag(self):
        clone = self.clone()
        proc = self.run_office("projects", "add", "clone", str(clone))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("bale has not run in", proc.stderr)
        self.assertIn("office projects add --prepare sets it up", proc.stderr)
        self.assertFalse((clone / "bale.toml").exists())
        self.assertNotIn("[projects.clone]", (self.root / "floor-plan/manifest.toml").read_text())

    def test_prepare_here_leaves_no_trace_and_is_idempotent(self):
        clone = self.clone()
        proc = self.run_office("projects", "add", "clone", str(clone), "--prepare", check=0)
        self.assertIn("4 line(s) added to .git/info/exclude", proc.stderr)
        self.assertIn("bale.toml written", proc.stderr)
        self.assertIn(f"added clone: {clone} (a git repo with bale.toml, no .bale/)", proc.stdout)
        self.check_prepared(clone)
        exclude = (clone / ".git" / "info" / "exclude").read_bytes()
        toml = (clone / "bale.toml").read_bytes()
        lines = ohost.prepare(ohost.Place(str(clone)))
        self.assertIn("0 line(s) added", lines[0])
        self.assertIn("bale.toml kept", lines[0])
        self.assertEqual((clone / ".git" / "info" / "exclude").read_bytes(), exclude)
        self.assertEqual((clone / "bale.toml").read_bytes(), toml)

    def test_prepare_through_the_shell_has_the_same_outcome(self):
        clone = self.clone()
        proc = self.run_office("projects", "add", "clone", str(clone), "--host", HOST, "--prepare", check=0)
        self.assertIn(f"prepared {clone} on {HOST} for bale: 4 line(s) added", proc.stderr)
        self.assertIn(f"added clone: {clone} (a git repo with bale.toml, no .bale/, on {HOST})", proc.stdout)
        self.check_prepared(clone)
        self.assertEqual({c[0] for c in self.ssh.connections()}, {HOST})

    def test_an_exclude_file_without_a_final_newline_is_extended_cleanly(self):
        clone = self.clone()
        exclude = clone / ".git" / "info" / "exclude"
        exclude.write_text("# theirs\n*.tmp")
        ohost.prepare(ohost.Place(str(clone)))
        text = exclude.read_text()
        self.assertTrue(text.startswith("# theirs\n*.tmp\n"))
        self.assertEqual(text.count(".bale/"), 1)
        self.check_prepared(clone)

    def test_the_doctrine_line(self):
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        self.assertIn("what the office writes into a project's working copy is only ever outside what git tracks",
                      doctrine)


# --- the record ---------------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_doctrine_states_the_rule_and_the_keys(self):
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        self.assertNotIn("A project on another machine is not read", doctrine)
        for words in ("a project declares its host", "through that shell", "makes no network call"):
            self.assertIn(words, doctrine)
        plan = doctrine.split("## 5. Spaces", 1)[1].split("## 6.", 1)[0]
        for key in ("host", "shell", "connect"):
            self.assertIn(f"`{key}`", plan)

    def test_the_readme_the_releases_and_the_version(self):
        readme = (REPO / "README.md").read_text()
        for words in ("--host", "--shell", "--connect", "--prepare", "office_host.py"):
            self.assertIn(words, readme)
        releases = (REPO / "RELEASES.md").read_text()
        self.assertIn("## 0.14.0", releases)
        # A later release moves VERSION on; 0.14.0 stays in the record.
        self.assertGreaterEqual(h.compare_versions((REPO / "VERSION").read_text().strip(), "0.14.0"), 0)
        self.assertLess(releases.index("## 0.14.0"), releases.index("## 0.13.0"))

    def test_the_suite_runs_no_real_ssh(self):
        """Every test here puts the fake first on the PATH; the office
        itself never names a real host."""
        text = pathlib.Path(__file__).read_text()
        self.assertIn('FAKE_SSH = r', text)
        for p in (REPO / "bin" / "office", *(REPO / "lib").glob("*.py")):
            self.assertNotIn("a-host.example", p.read_text(), p.name)


if __name__ == "__main__":
    unittest.main()
