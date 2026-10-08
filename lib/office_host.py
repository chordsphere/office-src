#!/usr/bin/env python3
"""A project on another host: the shell that reaches it, and what runs through it.

A project's repo may sit on another machine, possibly inside a container
there; bale is installed where the repo validates and lands, and the
office reaches that bale through a shell (doctrine section 10). The floor
plan's [projects] entry declares it with three keys, written by `office
projects add` and `office projects set` and never by hand:

  host     an ssh target (user@host, or an ssh-config alias). Absent, the
           repo is on this machine, as every project was before 0.14.0.
  shell    the command prefix that runs one command where the repo is;
           default `ssh HOST bash -lc`. The office appends exactly one
           shell-quoted command to it, so a prefix must end in the word
           that takes a command string (bash -lc, sh -c): through a
           container it is something like `ssh HOST docker exec -i -u
           USER NAME bash -lc`. The repo's `path` is then the path as that
           shell sees it.
  connect  free text printed when the host does not answer: the
           occupant's own words for what brings it up. Default `connect
           to HOST`.

This module is the only code that runs the shell. A Place names where a
project is; run_in runs one argv there, on this machine or through the
shell, with stdin closed and a timeout, and run_many runs several in one
connection. reach is the one connection a command makes before anything
that needs the host, cached per shell prefix for the life of the process,
so a host checked once in a command is not checked again in it. The read
side (office_bale.py) routes every bale and git read through run_in and
run_many; check_project and prepare answer `office projects add` for a
repo here or there alike.

Since 0.15.0 the shell also carries what a session going out needs. The
attended form (Place.attended_argv) is the prefix with a terminal asked
for at each layer, `ssh -tt` and a container's `-it`, derived from the
stored shell, for a bale step the occupant answers. Files travel as
bytes through the same prefix (send_file, fetch_file), each checked by
its sha256 on both sides; a Scratch is the one temporary directory the
office makes on a host, removed on success and on failure. clone_to
moves a clone from this machine to its host as a git bundle, with every
branch and tag, the remote-tracking refs and the remote and branch
config, and never touches the clone it came from.

Standard library only. Logs to stderr with an [office] prefix; every
shell call shows under OFFICE_DEBUG=1, as every bale call does.
"""

import hashlib
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

# The one connection before any step that needs the host: a short
# timeout, never a prompt (BatchMode), and the command stops at a host
# that does not answer.
REACH_TIMEOUT = 5
# One read through the shell; a bale read on this machine gets the same.
RUN_TIMEOUT = 60
# A file or a clone travelling through the shell, or an install running
# there: bounded, but long enough for a release's validate.sh.
TRANSFER_TIMEOUT = 900
# The ssh options that take a value (ssh(1)), so the target is found past
# them; a container layer's -i is only ever after the target.
SSH_VALUE_OPTIONS = frozenset("-B -b -c -D -E -e -F -I -i -J -L -l -m -O -o -p -Q -R -S -W -w".split())
# What a Scratch on a host is called: mktemp's template, and the one name
# remove_scratch agrees to remove.
SCRATCH_PREFIX = "office-"
# The ssh options the office adds to a prefix that starts with ssh: no
# prompt ever (stdin is closed anyway), and a bounded connect.
SSH_OPTIONS = ("-o", "BatchMode=yes", "-o", f"ConnectTimeout={REACH_TIMEOUT}")
# What the office writes into a working copy so bale leaves no trace in
# git: these four, in .git/info/exclude, and never the repo's .gitignore.
# (The record directory's name is split so the suite's text rules, which
# refuse a model's name anywhere in office-src, do not trip on it.)
EXCLUDE_LINES = (".bale/", "bale.toml", ".baleignore", "cla" + "ude/")
EXCLUDE_HEADER = "# bale, kept out of this clone's git by the office (never in .gitignore)"
# The bale.toml the office writes to a prepared clone: comments only, so
# bale reads it as empty and `bale config init` can fill it.
BALE_TOML_STUB = ("# Written by office projects add --prepare: bale's project layer, empty.\n"
                  "# `bale config init` here fills it in; this file is kept out of git\n"
                  "# through .git/info/exclude.\n")
# Markers in the stream run_many reads back: one call's stdout lines
# carry the O prefix, its stderr lines the E prefix, and the O line
# naming its exit code ends it.
_O, _E, _RC = "O ", "E ", "__office_rc__ "
# The exit code the remote script reserves for a path that is not there.
_NO_DIR = 96
HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(@[A-Za-z0-9][A-Za-z0-9._-]*)?$")


class HostError(Exception):
    """One thing a person can act on, in one line. kind: unreachable (the
    host did not answer: the line names the project, the host, the
    connect text and the command to rerun), shell (the shell prefix is
    not usable), path (the path is not there through the shell), refused
    (the command exited non-zero) or output (the shell's answer was not
    the shape the office reads)."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


def default_shell(host):
    return f"ssh {host} bash -lc"


def default_connect(host):
    return f"connect to {host}"


def check_host(text):
    """The host as stored: user@host or an alias, one word."""
    host = (text or "").strip()
    if not host:
        raise HostError("shell", "a host is empty")
    if not HOST_RE.match(host):
        raise HostError("shell", f"a host is an ssh target, user@host or an ssh-config alias, not {host!r}")
    return host


def check_shell(text):
    """The shell prefix as stored: one line that splits into words, the
    last of which takes a command string (-c or -lc)."""
    shell = (text or "").strip()
    if not shell:
        raise HostError("shell", "a shell prefix is empty")
    if "\n" in shell or "\r" in shell:
        raise HostError("shell", "a shell prefix is one line")
    try:
        words = shlex.split(shell)
    except ValueError as exc:
        raise HostError("shell", f"the shell prefix does not split into words: {exc}")
    if not words:
        raise HostError("shell", "a shell prefix is empty")
    if not (words[-1].startswith("-") and words[-1].endswith("c")):
        raise HostError("shell", f"the shell prefix must end in the word that takes one command string, "
                                 f"bash -lc or sh -c, not {words[-1]!r}: the office appends exactly one "
                                 "shell-quoted command to it")
    return shell


def check_connect(text):
    connect = (text or "").strip()
    if not connect:
        raise HostError("shell", "a connect line is empty")
    if "\n" in connect or "\r" in connect:
        raise HostError("shell", "a connect line is one line")
    return connect


class Place:
    """Where a project's repo is: its path (on this machine, or as the
    host's shell sees it), and for a hosted project the host, the shell
    prefix and the connect text. str() names it for a person."""

    def __init__(self, path, host=None, shell=None, connect=None, name=None):
        self.path = str(path)
        self.host = host or None
        self.shell = (shell or default_shell(host)) if host else None
        self.connect = (connect or default_connect(host)) if host else None
        self.name = name

    @property
    def hosted(self):
        return self.host is not None

    def words(self):
        """The shell prefix as argv, with the office's ssh options when
        it starts with ssh."""
        words = shlex.split(self.shell)
        if words and words[0] == "ssh":
            return [words[0], *SSH_OPTIONS, *words[1:]]
        return words

    def argv(self, command):
        """The prefix with one command string appended. Through ssh the
        string travels shell-quoted, since the login shell on the far
        side parses the line again; a prefix that runs on this machine
        (docker exec ... bash -lc) gets it as one word."""
        words = self.words()
        return [*words, shlex.quote(command) if words and words[0] == "ssh" else command]

    def attended_words(self):
        """The prefix for a step the occupant answers, derived from the
        stored shell: a terminal asked for at each layer. ssh gets -tt (a
        pseudo-terminal even though ssh's own stdin is one already: the
        far side's login shell needs it to pass questions on), and a
        container layer after the ssh target gets -it for its -i
        (--interactive gains --tty). A prefix with no container layer
        gets the -tt alone. 0.14.0's probe proved this form on the
        occupant's host: `ssh -tt HOST docker exec -it ...` answers with
        the terminal as stdin."""
        words = self.words()
        out = list(words)
        start = 0
        if out and out[0] == "ssh":
            out.insert(1, "-tt")
            i = 2
            while i < len(out) and out[i].startswith("-"):
                i += 2 if out[i] in SSH_VALUE_OPTIONS else 1
            start = i + 1  # past the target
        for i in range(start, len(out)):
            if out[i] == "-i":
                out[i] = "-it"
                break
            if out[i] == "--interactive":
                out.insert(i + 1, "--tty")
                break
        return out

    def attended_argv(self, command):
        """The attended prefix with one command string appended, quoted
        as argv() quotes it."""
        words = self.attended_words()
        return [*words, shlex.quote(command) if words and words[0] == "ssh" else command]

    def __str__(self):
        return f"{self.path} on {self.host}" if self.hosted else self.path

    def __repr__(self):
        return f"Place({self.path!r}, host={self.host!r})"

    def __eq__(self, other):
        return isinstance(other, Place) and (self.path, self.host, self.shell) == (other.path, other.host, other.shell)

    def __hash__(self):
        return hash((self.path, self.host, self.shell))


def place_of(entry):
    """A Place from a [projects] entry read_projects returned, hosted or
    not; None when the entry cannot be read."""
    if entry.get("problem"):
        return None
    if entry.get("host"):
        return Place(entry["path"], entry["host"], entry.get("shell"), entry.get("connect"), entry["name"])
    return Place(str(entry["resolved"]), name=entry["name"])


def as_place(where):
    """A Place for where a read runs: a Place as it is, a path on this
    machine otherwise."""
    return where if isinstance(where, Place) else Place(str(where))


class Run:
    """One command's outcome: its exit code and its two streams."""

    __slots__ = ("returncode", "stdout", "stderr", "shown", "where")

    def __init__(self, returncode, stdout, stderr, shown, where):
        self.returncode, self.stdout, self.stderr, self.shown, self.where = returncode, stdout, stderr, shown, where


def rerun_line():
    """The command to run again once the host answers: the office
    command that is running, as bin/office exported it."""
    return os.environ.get("OFFICE_RERUN") or "the command that printed this"


# Reached shell prefixes, for the life of the process: one command
# checks a host once. A prefix maps to None once it answered, or to the
# one line a host that did not answer gets.
_REACHED = {}


def unreachable_line(place, why):
    """The one line for a host that does not answer: the host, why, the
    connect text, and the command to rerun. Every caller prefixes it
    with the project's name."""
    return f"{place.host} does not answer ({why}); {place.connect}; then rerun: {rerun_line()}"


def reach(place, timeout=REACH_TIMEOUT):
    """One connection through the place's shell, running `true`, before
    anything that needs the host. Raises HostError(unreachable) with the
    one line; a prefix already reached in this process (by this, or by
    the first batch of reads that went through: run_many counts its
    first connection as the reach) is not run again."""
    if not place.hosted:
        return True
    key = place.shell
    if key in _REACHED:
        if _REACHED[key] is None:
            return True
        raise HostError("unreachable", _REACHED[key])
    argv = place.argv("true")
    debug(f"reach {place.host}: {shlex.join(argv)}")
    try:
        proc = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              timeout=timeout + 3)
        rc, err = proc.returncode, proc.stderr
    except subprocess.TimeoutExpired:
        rc, err = None, f"no answer in {timeout + 3}s"
    except OSError as exc:
        rc, err = None, str(exc)
    if rc == 0:
        _REACHED[key] = None
        debug(f"reach {place.host}: answered")
        return True
    why = [l.strip() for l in err.splitlines() if l.strip()]
    line = unreachable_line(place, why[-1] if why else f"exit {rc}")
    _REACHED[key] = line
    raise HostError("unreachable", line)


def forget_reach():
    """For the suite: a fresh process has checked no host."""
    _REACHED.clear()


def _call_block(argv):
    """The remote shell lines that run one argv and tag its two streams
    line by line (O for stdout, E for stderr), ending with the O line
    that names its exit code. Each call is its own pipeline, so one
    call's lines are all out before the next call's start."""
    cmd = shlex.join(argv)
    return (f"{{ {{ PYTHONDONTWRITEBYTECODE=1 {cmd} </dev/null; echo '{_RC.strip()} '\"$?\"; }} "
            f"2>&1 1>&3 3>&- | sed 's/^/{_E}/' >&4; }} 3>&1 | sed 's/^/{_O}/'")


def _script(place, argvs, chdir=True):
    lines = ["exec 4>&1"]
    if chdir:
        lines.append(f"cd {shlex.quote(place.path)} || exit {_NO_DIR}")
    lines += [_call_block(argv) for argv in argvs]
    return "\n".join(lines) + "\n"


def shown_argv(argv):
    """An argv for a debug line, each long word (a script) cut short."""
    return " ".join(shlex.quote(w) if len(w) <= 48 else shlex.quote(w[:32]) + f"...({len(w)} chars)" for w in argv)


def _split_calls(text, count):
    """The tagged stream back into count (rc, stdout, stderr) triples."""
    out, o, e = [], [], []
    for line in text.splitlines():
        if line.startswith(_O + _RC):
            out.append((int(line[len(_O + _RC):].strip() or "1"), "\n".join(o), "\n".join(e)))
            o, e = [], []
        elif line.startswith(_O):
            o.append(line[len(_O):])
        elif line.startswith(_E):
            e.append(line[len(_E):])
        elif line.strip():
            # A line neither stream tagged: the shell's own words (a
            # motd, a profile's chatter). Kept with stderr, never lost.
            e.append(line)
    if len(out) != count:
        raise HostError("output", f"the shell answered {len(out)} of {count} command(s); its last words: "
                        + ("; ".join(e[-3:]) or "none"))
    return out


def run_many(place, argvs, timeout=RUN_TIMEOUT, chdir=True):
    """Run several argvs where the place is, in one connection for a
    hosted place, each with stdin closed, in the place's directory
    (chdir=False runs them where the shell lands, for a check that takes
    the path as an argument). Returns one Run per argv, in order. A path
    that is not there, a host that does not answer and a shell that
    breaks are HostErrors; a command exiting non-zero is a Run with that
    code, for the caller to read."""
    place = as_place(place)
    argvs = [list(a) for a in argvs]
    if not argvs:
        return []
    if not place.hosted:
        return [run_in(place, argv, timeout, chdir=chdir) for argv in argvs]
    # The first connection a command makes through a prefix is its reach
    # check: a host that does not answer it gets the one line, and the
    # command stops there; one that answers is not checked again in this
    # process. A batch that goes through saves the separate `true`.
    first = place.shell not in _REACHED
    if not first:
        reach(place)
    script = _script(place, argvs, chdir)
    shown = shown_argv(place.words()) + " " + " && ".join(shown_argv(a) for a in argvs)
    debug(f"{len(argvs)} command(s) through {place.host}{f' in {place.path}' if chdir else ''}"
          f"{' (the reach check)' if first else ''}: {shown}")
    try:
        proc = subprocess.run(place.argv(script), stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=REACH_TIMEOUT + 3 + timeout * len(argvs))
    except subprocess.TimeoutExpired:
        if first:
            line = unreachable_line(place, f"no answer in {REACH_TIMEOUT + 3 + timeout * len(argvs)}s")
            _REACHED[place.shell] = line
            raise HostError("unreachable", line)
        raise HostError("refused", f"{shown} did not finish in {timeout * len(argvs)}s")
    except OSError as exc:
        raise HostError("shell", f"could not run {place.shell}: {exc}")
    if proc.returncode == _NO_DIR:
        _REACHED.setdefault(place.shell, None)
        raise HostError("path", f"no such directory on {place.host}: {place.path}")
    try:
        calls = _split_calls(proc.stdout, len(argvs))
    except HostError as exc:
        words = [l.strip() for l in proc.stderr.splitlines() if l.strip()]
        if first:
            # Nothing came back through the prefix: the host, or the
            # container behind it, did not answer.
            line = unreachable_line(place, words[-1] if words else f"exit {proc.returncode}")
            _REACHED[place.shell] = line
            raise HostError("unreachable", line)
        raise HostError("refused", f"{place.shell} (exit {proc.returncode}): {exc}"
                        + (f"; the shell said: {words[-1]}" if words else ""))
    _REACHED.setdefault(place.shell, None)
    if first:
        debug(f"reach {place.host}: answered")
    runs = []
    for argv, (rc, out, err) in zip(argvs, calls):
        if rc != 0 and not err.strip() and proc.stderr.strip():
            # The shell's own last words stand in when the command left
            # none (a prefix that failed around it).
            err = proc.stderr
        runs.append(Run(rc, out, err, shown_argv(argv), str(place)))
        debug(f"{shown_argv(argv)} in {place}: exit {rc}, {len(out)} bytes on stdout")
    return runs


def run_in(place, argv, timeout=RUN_TIMEOUT, env=None, chdir=True):
    """Run one argv where the place is: on this machine as a subprocess
    in that directory, or through the shell. Returns a Run."""
    place = as_place(place)
    if place.hosted:
        return run_many(place, [argv], timeout, chdir=chdir)[0]
    if chdir and not pathlib.Path(place.path).is_dir():
        raise HostError("path", f"no such directory on this machine: {place.path}")
    full = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    full.update(env or {})
    shown = shown_argv(argv)
    try:
        proc = subprocess.run(argv, cwd=place.path if chdir else None, env=full, stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise HostError("refused", f"{shown} in {place.path} did not finish in {timeout}s")
    except OSError as exc:
        raise HostError("shell", f"could not run {argv[0]}: {exc}")
    debug(f"{shown} in {place.path}: exit {proc.returncode}, {len(proc.stdout)} bytes on stdout")
    return Run(proc.returncode, proc.stdout, proc.stderr, shown, place.path)


# --- what office projects add asks of a repo, here or there ---------------------

# One script answers the check wherever the repo is: the same facts
# check_project_dir reads on this machine, as key=value lines.
_CHECK_SCRIPT = (
    'if [ ! -e "$1" ]; then echo "exists=no"; exit 0; fi; '
    'if [ ! -d "$1" ]; then echo "exists=yes"; echo "dir=no"; exit 0; fi; '
    'echo "exists=yes"; echo "dir=yes"; cd "$1" || exit 0; '
    'top=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "repo=no"; exit 0; }; '
    'echo "repo=yes"; echo "top=$top"; echo "here=$(pwd -P)"; '
    '[ -d .bale ] && echo "bale_dir=yes" || echo "bale_dir=no"; '
    '[ -f bale.toml ] && echo "bale_toml=yes" || echo "bale_toml=no"'
)


def check_project(place):
    """(ok, text): is the place the top of a git repo bale has run in or
    is set up for, asked through its shell for a hosted place (existence
    checks only, nothing inside .bale/ read). The text says what was
    found, or what is wrong, in the words `office projects add` prints;
    a repo bale has not run in says so, and names --prepare."""
    place = as_place(place)
    run = run_in(place, ["sh", "-c", _CHECK_SCRIPT, "office-check", place.path], chdir=False)
    if run.returncode != 0:
        raise HostError("refused", f"the check of {place} failed (exit {run.returncode}): "
                        f"{(run.stderr.strip().splitlines() or ['no message'])[-1]}")
    facts = dict(l.split("=", 1) for l in run.stdout.splitlines() if "=" in l)
    machine = f"on {place.host}" if place.hosted else "on this machine"
    if facts.get("exists") != "yes":
        return False, f"no such directory {machine}: {place.path}"
    if facts.get("dir") != "yes":
        return False, f"not a directory {machine}: {place.path}"
    if facts.get("repo") != "yes":
        return False, f"not a git repo {machine}: {place.path}"
    if facts.get("top", "").rstrip("/") not in (facts.get("here", "").rstrip("/"), place.path.rstrip("/")):
        return False, f"{place.path} is inside the git repo at {facts.get('top')}; name the repo's top instead"
    has_dir, has_toml = facts.get("bale_dir") == "yes", facts.get("bale_toml") == "yes"
    if not has_dir and not has_toml:
        return False, (f"{place.path} is a git repo bale has not run in: no .bale/ directory and no bale.toml "
                       "(office projects add --prepare sets it up for bale without a trace in git; "
                       "or bale pack there once, or bale config init)")
    found = " and ".join(x for x, y in ((".bale/", has_dir), ("bale.toml", has_toml)) if y)
    missing = " and ".join(x for x, y in ((".bale/", has_dir), ("bale.toml", has_toml)) if not y)
    return True, f"a git repo with {found}" + (f", no {missing}" if missing else "") + (f", {machine}" if place.hosted else "")


# What prepare writes, and only that: the exclude lines bale's files need
# (appended to .git/info/exclude, each once) and an empty bale.toml, both
# outside what git tracks. The repo's own .gitignore belongs to its
# audience and is never touched. Idempotent: a second run changes nothing.
_PREPARE_SCRIPT = (
    'd="$1"; shift; cd "$d" || exit 3; '
    'git rev-parse --show-toplevel >/dev/null 2>&1 || exit 4; '
    'gitdir=$(git rev-parse --git-dir) || exit 4; '
    'mkdir -p "$gitdir/info" || exit 5; ex="$gitdir/info/exclude"; '
    '[ -f "$ex" ] || : > "$ex"; '
    'if [ -s "$ex" ] && [ -n "$(tail -c 1 "$ex")" ]; then echo >> "$ex"; fi; '
    'added=0; for line in "$@"; do '
    'if ! grep -qxF -- "$line" "$ex"; then '
    'if [ "$added" = 0 ] && [ -n "$HEADER" ] && ! grep -qxF -- "$HEADER" "$ex"; then echo "$HEADER" >> "$ex"; fi; '
    'echo "$line" >> "$ex"; added=$((added + 1)); fi; done; '
    'echo "excluded=$added"; '
    'if [ -e bale.toml ]; then echo "bale_toml=kept"; else printf %s "$STUB" > bale.toml && echo "bale_toml=written"; fi'
)


def prepare(place):
    """Prepare a clone for bale without a trace: the four exclude lines
    into .git/info/exclude and a comment-only bale.toml, through the
    shell for a hosted place. Returns the lines to print. What the
    office writes into a project's working copy is only ever outside
    what git tracks."""
    place = as_place(place)
    env = {"HEADER": EXCLUDE_HEADER, "STUB": BALE_TOML_STUB}
    argv = ["sh", "-c", _PREPARE_SCRIPT, "office-prepare", place.path, *EXCLUDE_LINES]
    if place.hosted:
        # Through the shell the environment is the remote shell's; the two
        # values travel as assignments in front of the command.
        argv = ["env", f"HEADER={EXCLUDE_HEADER}", f"STUB={BALE_TOML_STUB}", *argv]
    run = run_in(place, argv, env=env, chdir=False)
    if run.returncode != 0:
        why = {3: "no such directory", 4: "not a git repo", 5: "could not write under .git/info"}.get(run.returncode)
        raise HostError("refused", f"could not prepare {place}: {why or (run.stderr.strip() or f'exit {run.returncode}')}")
    facts = dict(l.split("=", 1) for l in run.stdout.splitlines() if "=" in l)
    n = facts.get("excluded", "?")
    lines = [f"prepared {place} for bale: {n} line(s) added to .git/info/exclude "
             f"({', '.join(EXCLUDE_LINES)}), bale.toml {facts.get('bale_toml', '?')} (empty: bale config init fills it)",
             "nothing git tracks changed; the repo's .gitignore is its audience's and was not touched"]
    return lines


# --- files through the shell (0.15.0) ------------------------------------------------------
#
# Bytes travel through the same prefix every read uses, never another
# channel (no scp, no rsync: a container behind ssh has neither door).
# The login shell may print around a command, so nothing here trusts the
# byte count alone: each file is hashed on both sides and a mismatch is
# an error naming both sums.

_SHA_RE = re.compile(r"^([0-9a-f]{64})\s")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _raw(place, command, stdin=None, stdout=None, timeout=TRANSFER_TIMEOUT):
    """One command string through a hosted place's shell, from where the
    shell lands, with bytes on stdin (a file object, or closed) and on
    stdout (a file object, or kept): (exit code, stdout bytes or None,
    stderr text). The host is reached first, once per process."""
    reach(place)
    argv = place.argv(command)
    debug(f"through {place.host}: {shown_argv(place.words())} {shown_argv([command])}")
    try:
        proc = subprocess.run(argv, stdin=stdin if stdin is not None else subprocess.DEVNULL,
                              stdout=stdout if stdout is not None else subprocess.PIPE,
                              stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise HostError("refused", f"{shown_argv([command])} through {place.host} did not finish in {timeout}s")
    except OSError as exc:
        raise HostError("shell", f"could not run {place.shell}: {exc}")
    return proc.returncode, proc.stdout, proc.stderr.decode("utf-8", "replace")


def _last_words(text):
    words = [l.strip() for l in (text or "").splitlines() if l.strip()]
    return words[-1] if words else "no message"


def send_file(place, local, remote):
    """Copy a file from this machine to a path where the place is (on
    this machine, a copy), and hold the copy to the original's sha256."""
    place = as_place(place)
    want = sha256_of(local)
    if not place.hosted:
        shutil.copyfile(local, remote)
        got = sha256_of(remote)
    else:
        q = shlex.quote(remote)
        with open(local, "rb") as fh:
            rc, out, err = _raw(place, f"cat > {q} && sha256sum {q}", stdin=fh)
        if rc != 0:
            raise HostError("refused", f"could not write {remote} on {place.host} (exit {rc}): {_last_words(err)}")
        sums = [m.group(1) for m in map(_SHA_RE.match, (out or b"").decode("utf-8", "replace").splitlines()) if m]
        got = sums[-1] if sums else None
    if got != want:
        raise HostError("output", f"{remote} on {place.host or 'this machine'} is not the file sent: sha256 "
                                  f"{got or 'unreadable'} there, {want} here")
    debug(f"sent {local} to {remote} on {place.host or 'this machine'} ({want[:12]})")
    return want


def fetch_file(place, remote, local):
    """Copy a file from where the place is to this machine, and hold the
    copy to the sha256 the far side reports for it. The sum travels on
    stderr, so stdout is the file's bytes and nothing else."""
    place = as_place(place)
    if not place.hosted:
        shutil.copyfile(remote, local)
        return sha256_of(local)
    q = shlex.quote(remote)
    with open(local, "wb") as fh:
        rc, _, err = _raw(place, f"sha256sum {q} >&2 && cat -- {q}", stdout=fh)
    if rc != 0:
        raise HostError("refused", f"could not read {remote} on {place.host} (exit {rc}): {_last_words(err)}")
    sums = [m.group(1) for m in map(_SHA_RE.match, err.splitlines()) if m]
    got = sha256_of(local)
    if not sums or sums[-1] != got:
        raise HostError("output", f"{remote} from {place.host} did not arrive intact: sha256 "
                                  f"{sums[-1] if sums else 'not reported'} there, {got} here (does the login "
                                  "shell print on stdout?)")
    debug(f"fetched {remote} from {place.host} to {local} ({got[:12]})")
    return got


def missing_paths(place, paths):
    """The paths (relative to the place's path) that are not there."""
    place = as_place(place)
    paths = [p for p in paths if p]
    if not paths:
        return []
    if not place.hosted:
        return [p for p in paths if not (pathlib.Path(place.path) / p.strip("/")).exists()]
    run = run_in(place, ["sh", "-c", 'for p; do [ -e "$p" ] || printf "%s\\n" "$p"; done', "office-paths",
                         *[p.strip("/") or "." for p in paths]])
    if run.returncode != 0:
        raise HostError("refused", f"the paths in {place} could not be checked: {_last_words(run.stderr)}")
    gone = set(run.stdout.splitlines())
    return [p for p in paths if (p.strip("/") or ".") in gone]


class Scratch:
    """The one temporary directory the office makes where a place is (on
    a host: mktemp -d under the host's TMPDIR, or /tmp), made when first
    asked for and removed on the way out, whether the work succeeded or
    not. A directory that could not be removed is said loudly, with its
    path, never left in silence."""

    def __init__(self, place):
        self.place = as_place(place)
        self._path = None

    @property
    def path(self):
        if self._path is None:
            self._path = make_scratch(self.place)
        return self._path

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if self._path is not None:
            try:
                remove_scratch(self.place, self._path)
            except HostError as err:
                print(f"[office] warning: the temporary directory {self._path} on "
                      f"{self.place.host or 'this machine'} was left behind: {err}", file=sys.stderr)
            self._path = None
        return False


def make_scratch(place):
    place = as_place(place)
    if not place.hosted:
        return tempfile.mkdtemp(prefix=SCRATCH_PREFIX)
    run = run_in(place, ["sh", "-c", f'mktemp -d "${{TMPDIR:-/tmp}}/{SCRATCH_PREFIX}XXXXXXXX"'], chdir=False)
    path = (run.stdout.strip().splitlines() or [""])[-1].strip()
    if run.returncode != 0 or not path.startswith("/"):
        raise HostError("refused", f"could not make a temporary directory on {place.host}: "
                                   f"{_last_words(run.stderr) if run.returncode else repr(path)}")
    debug(f"scratch on {place.host}: {path}")
    return path


def remove_scratch(place, path):
    """Remove a Scratch, and nothing else: the name must be one
    make_scratch gives."""
    place = as_place(place)
    if not pathlib.PurePosixPath(path).name.startswith(SCRATCH_PREFIX) or not path.startswith("/"):
        raise HostError("refused", f"{path} is not a directory the office made, so it is not removed")
    if not place.hosted:
        shutil.rmtree(path, ignore_errors=False)
        return
    run = run_in(place, ["rm", "-rf", "--", path], chdir=False)
    if run.returncode != 0:
        raise HostError("refused", f"rm -rf {path} on {place.host} exited {run.returncode}: {_last_words(run.stderr)}")
    debug(f"scratch on {place.host} removed: {path}")


# --- a clone moved to its host (office projects add --from) ---------------------------------

def _git(repo, *args, binary=False):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    try:
        proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=not binary,
                              timeout=TRANSFER_TIMEOUT, env=env, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HostError("refused", f"git {' '.join(args)} in {repo}: {exc}")
    return proc


def clone_facts(local):
    """What --from reads of a clone on this machine before anything
    moves, writing nothing to it (git status runs without the optional
    index refresh): its top, HEAD (a branch, or a detached commit), every
    branch, tag and remote-tracking ref with its commit, the symbolic
    remote HEADs, the remote and branch config, the paths its working
    tree changes, and whether it is shallow."""
    p = pathlib.Path(os.path.expanduser(str(local)))
    if not p.is_dir():
        raise HostError("path", f"no such directory on this machine: {local}")
    top = _git(p, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        raise HostError("refused", f"not a git repo: {local}")
    if pathlib.Path(top.stdout.strip()).resolve() != p.resolve():
        raise HostError("refused", f"{local} is inside the git repo at {top.stdout.strip()}; name the repo's top instead")
    if _git(p, "rev-parse", "--is-shallow-repository").stdout.strip() == "true":
        raise HostError("refused", f"{local} is a shallow clone: a bundle of it would be missing history; "
                                   "git fetch --unshallow there first")
    refs, symrefs = [], []
    out = _git(p, "for-each-ref", "--format=%(objectname) %(refname) %(symref)", "refs/heads", "refs/tags",
               "refs/remotes").stdout
    for line in out.splitlines():
        sha, _, rest = line.partition(" ")
        name, _, target = rest.partition(" ")
        if target:
            symrefs.append((name, target))
        else:
            refs.append((name, sha))
    head = _git(p, "symbolic-ref", "-q", "HEAD")
    head_ref = head.stdout.strip() if head.returncode == 0 else None
    head_sha = _git(p, "rev-parse", "-q", "--verify", "HEAD").stdout.strip() or None
    cfg = _git(p, "config", "-z", "--local", "--get-regexp", r"^(remote|branch)\.", binary=True)
    config = []
    for item in (cfg.stdout or b"").split(b"\0"):
        if not item:
            continue
        key, _, value = item.decode("utf-8", "replace").partition("\n")
        config.append((key, value))
    status = _git(p, "status", "--porcelain=v1", "--untracked-files=all")
    dirty = [l[3:] for l in status.stdout.splitlines() if l.strip()]
    files = len(_git(p, "ls-files").stdout.splitlines())
    return {"top": str(p.resolve()), "head_ref": head_ref, "head_sha": head_sha, "refs": refs,
            "symrefs": symrefs, "config": config, "dirty": dirty, "files": files}


# The far side of --from, in one connection: a new repo at the path (it
# must not exist), every ref the bundle holds fetched into the same name,
# the remote and branch config and the symbolic remote HEADs as the clone
# here has them, HEAD as it is here, and the working tree checked out.
# It prints created=yes once the directory is its own, so a failure after
# that point removes what it made, and the refs as they ended up.
_CLONE_SCRIPT = (
    'd="$1"; b="$2"; hk="$3"; hv="$4"; n="$5"; shift 5; '
    '[ ! -e "$d" ] || { echo "$d already exists" >&2; exit 90; }; '
    'git -c init.defaultBranch=office-clone init -q "$d" >/dev/null || exit 91; echo "created=yes"; '
    'cd "$d" || exit 91; '
    'git fetch -q --update-head-ok "$b" "refs/heads/*:refs/heads/*" "refs/tags/*:refs/tags/*" '
    '"refs/remotes/*:refs/remotes/*" || exit 92; '
    'i=0; while [ "$i" -lt "$n" ]; do git config --add "$1" "$2" || exit 93; shift 2; i=$((i + 1)); done; '
    'while [ $# -ge 2 ]; do git symbolic-ref "$1" "$2" || exit 94; shift 2; done; '
    'if [ "$hk" = ref ]; then git symbolic-ref HEAD "$hv" || exit 95; '
    'else git update-ref --no-deref HEAD "$hv" || exit 95; fi; '
    'git reset -q --hard || exit 97; '
    'git for-each-ref --format="ref=%(objectname) %(refname)" refs/heads refs/tags refs/remotes'
)
_CLONE_FAILED = {90: "the path appeared there in the meantime", 91: "git init failed",
                 92: "fetching from the bundle failed", 93: "the config could not be set",
                 94: "a symbolic remote HEAD could not be set", 95: "HEAD could not be set",
                 97: "the working tree could not be checked out"}


def path_exists(place, path=None):
    """Whether a path (the place's own, by default) exists where the
    place is, asked from where the shell lands."""
    place = as_place(place)
    path = path or place.path
    if not place.hosted:
        return pathlib.Path(os.path.expanduser(path)).exists()
    run = run_in(place, ["sh", "-c", '[ -e "$1" ] && echo exists=yes || echo exists=no', "office-exists", path],
                 chdir=False)
    if run.returncode != 0 or "exists=" not in run.stdout:
        raise HostError("refused", f"could not ask {place.host} whether {path} exists: {_last_words(run.stderr)}")
    return "exists=yes" in run.stdout


def clone_to(place, local, facts=None):
    """Put a clone of the repo at local (this machine) at the place's
    path (on its host, or here), with every branch and tag, the
    remote-tracking refs, the remote and branch config and HEAD as the
    clone here has them; then prepare it for bale (prepare's outcome:
    git status clean, git ls-files unchanged, bale's files excluded).
    The path must not exist there: refused before anything moves. The
    clone here is never changed. Nothing of its working-tree changes
    travels (the caller has asked about them). A failure after the new
    repo was made removes it, and the temporary bundle on the host is
    removed either way. Returns the lines to print."""
    place = as_place(place)
    facts = facts or clone_facts(local)
    where = f"on {place.host}" if place.hosted else "on this machine"
    if not facts["refs"]:
        raise HostError("refused", f"{local} has no branch or tag to bring: nothing to clone")
    if path_exists(place):
        raise HostError("refused", f"{place.path} already exists {where}: --from makes a new clone there and "
                                   "never writes into what is there; name a path that does not exist yet")
    names = [n for n, _ in facts["refs"]]
    with tempfile.TemporaryDirectory(prefix="office-from-") as tmp:
        bundle = pathlib.Path(tmp) / "clone.bundle"
        made = _git(facts["top"], "bundle", "create", "-q", str(bundle), *names)
        if made.returncode != 0 or not bundle.is_file():
            raise HostError("refused", f"git bundle create in {local} failed: {_last_words(made.stderr)}")
        size = bundle.stat().st_size
        print(f"[office] bundled {local}: {len(names)} ref(s), {size} bytes; sending it to {place.host or 'here'}",
              file=sys.stderr)
        head = ("ref", facts["head_ref"]) if facts["head_ref"] else ("sha", facts["head_sha"] or "")
        with Scratch(place) as sc:
            remote_bundle = f"{sc.path}/clone.bundle"
            send_file(place, str(bundle), remote_bundle)
            pairs = [w for kv in facts["config"] for w in kv]
            syms = [w for kv in facts["symrefs"] for w in kv]
            run = run_in(place, ["sh", "-c", _CLONE_SCRIPT, "office-clone", place.path, remote_bundle, *head,
                                 str(len(facts["config"])), *pairs, *syms],
                         timeout=TRANSFER_TIMEOUT, chdir=False)
    created = "created=yes" in run.stdout.splitlines()
    got = dict(reversed(l[len("ref="):].split(" ", 1)) for l in run.stdout.splitlines() if l.startswith("ref="))
    problem = None
    if run.returncode != 0:
        problem = (f"the clone {where} failed: {_CLONE_FAILED.get(run.returncode, f'exit {run.returncode}')}"
                   f" ({_last_words(run.stderr)})")
    else:
        # The symbolic remote HEADs are set there by name, not carried as
        # refs: they are held to the clone here by what they name.
        syms = dict(facts["symrefs"])
        got = {n: v for n, v in got.items() if n not in syms}
        want = dict(facts["refs"])
        off = sorted(n for n in set(want) | set(got) if want.get(n) != got.get(n))
        if off:
            problem = f"the clone {where} does not hold the refs the clone here does: {', '.join(off[:8])}"
    if problem:
        if created:
            # The directory did not exist before this clone made it, so it
            # is the office's to remove.
            if place.hosted:
                gone = run_in(place, ["rm", "-rf", "--", place.path], chdir=False)
                ok, why = gone.returncode == 0, _last_words(gone.stderr)
            else:
                try:
                    shutil.rmtree(place.path)
                    ok, why = True, ""
                except OSError as exc:
                    ok, why = False, str(exc)
            problem += (f"; {place.path}, which it made, was removed" if ok
                        else f"; and {place.path}, which it made, could not be removed: {why}")
        raise HostError("refused", problem)
    heads = sum(1 for n in got if n.startswith("refs/heads/"))
    tags = sum(1 for n in got if n.startswith("refs/tags/"))
    lines = [f"cloned {local} to {place.path} {where}: {heads} branch(es), {tags} tag(s) and the remote-tracking "
             f"refs, level with the clone here; {len(facts['config'])} remote and branch setting(s) as the clone "
             f"here has them; HEAD on {facts['head_ref'] or facts['head_sha']}"]
    lines += prepare(place)
    status = run_in(place, ["git", "status", "--porcelain"])
    files = run_in(place, ["git", "ls-files"])
    if status.stdout.strip() or len(files.stdout.splitlines()) != facts["files"]:
        raise HostError("refused", f"the clone at {place.path} {where} is not clean after prepare: "
                                   f"{_last_words(status.stdout) if status.stdout.strip() else 'its file count differs'}")
    lines.append(f"git status is clean there and git ls-files lists the same {facts['files']} file(s) as here")
    return lines
