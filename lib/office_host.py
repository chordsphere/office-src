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

import os
import pathlib
import re
import sys

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


def shell_path(path):
    """A path for a shell line on the far side, quoted: a home-relative
    path (~/x, as office projects add takes one for a host) keeps its
    tilde meaning there, "$HOME"/'x', since a quoted ~ is a directory
    named ~."""
    import shlex
    path = str(path)
    if path == "~":
        return '"$HOME"'
    if path.startswith("~/"):
        return '"$HOME"/' + shlex.quote(path[2:])
    return shlex.quote(path)


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
    import shlex
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
        import shlex
        words = shlex.split(self.shell)
        if words and words[0] == "ssh":
            return [words[0], *SSH_OPTIONS, *words[1:]]
        return words

    def argv(self, command):
        """The prefix with one command string appended. Through ssh the
        string travels shell-quoted, since the login shell on the far
        side parses the line again; a prefix that runs on this machine
        (docker exec ... bash -lc) gets it as one word."""
        import shlex
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
        import shlex
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
# Since 0.16.0 the reach carries across the reader processes of one
# office command: bin/office names a file in this variable, every prefix
# that answered is appended to it (one line each; a shell prefix is one
# line), and a later process of the same command reads it before its
# first connection, so a host one step reached is not reached again by
# the next. A host that did not answer is never written: the command
# stops there.
REACHED_ENV = "OFFICE_REACHED_FILE"
_CARRIED = {"loaded": False}
# ssh's own exit code for a connection that failed (ssh(1)): a host that
# stopped answering after the reach was carried says so in the reach's
# one line, not as a refused command.
SSH_CONNECTION_FAILED = 255


def _load_carried():
    """The prefixes earlier processes of this command reached, once per
    process."""
    if _CARRIED["loaded"]:
        return
    _CARRIED["loaded"] = True
    path = os.environ.get(REACHED_ENV)
    if not path:
        return
    try:
        lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return
    except OSError as exc:
        debug(f"the reach carried from earlier steps could not be read ({exc}); each host is reached again")
        return
    for line in lines:
        if line.strip():
            _REACHED.setdefault(line, None)
            debug(f"reach carried from an earlier step of this command: {line}")


def _answered(place):
    """Record that a prefix answered: for this process, and for the next
    processes of the same command."""
    known = _REACHED.get(place.shell, "unset") is None
    _REACHED[place.shell] = None
    path = os.environ.get(REACHED_ENV)
    if known or not path:
        return
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(place.shell + "\n")
    except OSError as exc:
        debug(f"the reach of {place.host} could not be carried to the next step ({exc}); it reaches again")


def _lost(place, why):
    """The one line for a host that stopped answering after it was
    reached, as a HostError(unreachable)."""
    line = unreachable_line(place, why)
    _REACHED[place.shell] = line
    return HostError("unreachable", line)


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
    import shlex
    import subprocess
    if not place.hosted:
        return True
    _load_carried()
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
        _answered(place)
        debug(f"reach {place.host}: answered")
        return True
    why = [l.strip() for l in err.splitlines() if l.strip()]
    line = unreachable_line(place, why[-1] if why else f"exit {rc}")
    _REACHED[key] = line
    raise HostError("unreachable", line)


def forget_reach():
    """For the suite: a fresh process has checked no host."""
    _REACHED.clear()
    _CARRIED["loaded"] = False


def _call_block(argv):
    """The remote shell lines that run one argv and tag its two streams
    line by line (O for stdout, E for stderr), ending with the O line
    that names its exit code. Each call is its own pipeline, so one
    call's lines are all out before the next call's start."""
    import shlex
    cmd = shlex.join(argv)
    return (f"{{ {{ PYTHONDONTWRITEBYTECODE=1 {cmd} </dev/null; echo '{_RC.strip()} '\"$?\"; }} "
            f"2>&1 1>&3 3>&- | sed 's/^/{_E}/' >&4; }} 3>&1 | sed 's/^/{_O}/'")


def _script(place, argvs, chdir=True):
    lines = ["exec 4>&1"]
    if chdir:
        lines.append(f"cd {shell_path(place.path)} || exit {_NO_DIR}")
    lines += [_call_block(argv) for argv in argvs]
    return "\n".join(lines) + "\n"


def shown_argv(argv):
    """An argv for a debug line, each long word (a script) cut short."""
    import shlex
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
    import subprocess
    place = as_place(place)
    argvs = [list(a) for a in argvs]
    if not argvs:
        return []
    if not place.hosted:
        return [run_in(place, argv, timeout, chdir=chdir) for argv in argvs]
    # The first connection a command makes through a prefix is its reach
    # check: a host that does not answer it gets the one line, and the
    # command stops there; one that answers is not checked again in this
    # process (or, since 0.16.0, in an earlier process of the same office
    # command). A batch that goes through saves the separate `true`.
    _load_carried()
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
        _answered(place)
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
        if proc.returncode == SSH_CONNECTION_FAILED and not proc.stdout.strip():
            # It answered earlier in this command and stopped since (the
            # VPN dropped): the reach's one line, connect text and all.
            raise _lost(place, words[-1] if words else f"exit {proc.returncode}")
        raise HostError("refused", f"{place.shell} (exit {proc.returncode}): {exc}"
                        + (f"; the shell said: {words[-1]}" if words else ""))
    _answered(place)
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
    import subprocess
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


# A path a script takes as its first argument (d), with a home-relative
# path's tilde meaning restored on the far side (see shell_path).
_EXPAND_D = 'case "$d" in "~"|"~/"*) d="$HOME${d#"~"}" ;; esac; '


# --- what office projects add asks of a repo, here or there ---------------------

# One script answers the check wherever the repo is: the same facts
# check_project_dir reads on this machine, as key=value lines.
_CHECK_SCRIPT = (
    'case "$1" in "~"|"~/"*) set -- "$HOME${1#"~"}" ;; esac; '
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
    return read_check(place, run_in(place, check_argv(place), chdir=False))


def check_argv(place):
    """The check's one argv, for a batch that carries it beside other
    reads (start's check of a host, since 0.16.0). It takes the path as an
    argument, so it runs from wherever the shell lands."""
    return ["sh", "-c", _CHECK_SCRIPT, "office-check", as_place(place).path]


def read_check(place, run):
    """(ok, text) from the check's Run, as check_project says it."""
    place = as_place(place)
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
    'd="$1"; shift; ' + _EXPAND_D + 'cd "$d" || exit 3; '
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
    import hashlib
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
    import subprocess
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
    err = proc.stderr.decode("utf-8", "replace")
    if proc.returncode == SSH_CONNECTION_FAILED and place.words()[:1] == ["ssh"]:
        raise _lost(place, _last_words(err))
    return proc.returncode, proc.stdout, err


def _last_words(text):
    words = [l.strip() for l in (text or "").splitlines() if l.strip()]
    return words[-1] if words else "no message"


def send_file(place, local, remote):
    """Copy a file from this machine to a path where the place is (on
    this machine, a copy), and hold the copy to the original's sha256."""
    import shlex
    import shutil
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
    import shlex
    import shutil
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


# The paths (arguments, relative to where the shell stands) that are not
# there, one per line.
MISSING_SCRIPT = 'for p; do [ -e "$p" ] || printf "%s\\n" "$p"; done'


def missing_paths(place, paths):
    """The paths (relative to the place's path) that are not there."""
    place = as_place(place)
    paths = [p for p in paths if p]
    if not paths:
        return []
    if not place.hosted:
        return [p for p in paths if not (pathlib.Path(place.path) / p.strip("/")).exists()]
    run = run_in(place, ["sh", "-c", MISSING_SCRIPT, "office-paths", *[p.strip("/") or "." for p in paths]])
    if run.returncode != 0:
        raise HostError("refused", f"the paths in {place} could not be checked: {_last_words(run.stderr)}")
    gone = set(run.stdout.splitlines())
    return [p for p in paths if (p.strip("/") or ".") in gone]


class Scratch:
    """The one temporary directory the office makes where a place is (on
    a host: mktemp -d under the host's TMPDIR, or /tmp), made when first
    asked for and removed on the way out, whether the work succeeded or
    not. A directory that could not be removed is said loudly, with its
    path, never left in silence.

    Since 0.16.0 each end can ride a connection the work makes anyway:
    send() makes the directory in the same connection that carries the
    first file into it, and removal_argv() / removal_words() are the
    removal for the last step's batch or command to carry, after which
    removed_by_step() tells the scratch the explicit removal is not
    needed (it still runs when the step did not finish normally)."""

    def __init__(self, place):
        self.place = as_place(place)
        self._path = None

    @property
    def path(self):
        if self._path is None:
            self._path = make_scratch(self.place)
        return self._path

    @property
    def made(self):
        return self._path is not None

    def send(self, local, name=None):
        """Copy a file from this machine into the scratch under name (its
        own name by default), held to its sha256; on a host whose scratch
        is not made yet, the directory is made in the same connection.
        Returns the file's path there."""
        name = name or pathlib.Path(local).name
        if "/" in name or name in ("", ".", ".."):
            raise HostError("refused", f"{name!r} is not a file name")
        if self._path is not None or not self.place.hosted:
            remote = f"{self.path}/{name}"
            send_file(self.place, local, remote)
            return remote
        self._path, remote = send_into_new_scratch(self.place, local, name)
        return remote

    def removal_words(self):
        """The shell words that remove the scratch where it is, saying so
        loudly on stderr when they cannot: for a command the last step
        runs anyway. Empty when the scratch was never made."""
        import shlex
        if self._path is None:
            return ""
        q = shlex.quote(self._path)
        warn = shlex.quote(f"[office] warning: the temporary directory {self._path} on "
                           f"{self.place.host or 'this machine'} was left behind")
        return f"rm -rf -- {q} || echo {warn} >&2"

    def removal_argv(self):
        """The removal as one argv, for a batch the last step sends."""
        return ["sh", "-c", self.removal_words()] if self._path is not None else None

    def removed_by_step(self):
        """The last step's own connection removed the scratch: nothing is
        left for __exit__ to remove."""
        self._path = None

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


# One connection: a new scratch, and one file sent into it with its sum.
_SEND_NEW = ('d=$(mktemp -d "${TMPDIR:-/tmp}/' + SCRATCH_PREFIX + 'XXXXXXXX") || exit 1; echo "scratch=$d"; '
             'cat > "$d/$1" && sha256sum "$d/$1"')


def send_into_new_scratch(place, local, name):
    """Make a scratch on a host and send one file into it, in one
    connection; (scratch path, the file's path there). The file is held to
    its sha256, as send_file holds one; a failure after the directory was
    made removes it before it raises."""
    import shlex
    want = sha256_of(local)
    with open(local, "rb") as fh:
        rc, out, err = _raw(place, f"sh -c {shlex.quote(_SEND_NEW)} office-send {shlex.quote(name)}", stdin=fh)
    text = (out or b"").decode("utf-8", "replace")
    made = [l[len("scratch="):].strip() for l in text.splitlines() if l.startswith("scratch=")]
    path = made[-1] if made else None
    sums = [m.group(1) for m in map(_SHA_RE.match, text.splitlines()) if m]
    problem = None
    if path is None or not path.startswith("/"):
        problem = HostError("refused", f"could not make a temporary directory on {place.host}: {_last_words(err)}")
        path = None
    elif rc != 0:
        problem = HostError("refused", f"could not write {path}/{name} on {place.host} (exit {rc}): {_last_words(err)}")
    elif (sums[-1] if sums else None) != want:
        problem = HostError("output", f"{path}/{name} on {place.host} is not the file sent: sha256 "
                                      f"{sums[-1] if sums else 'unreadable'} there, {want} here")
    if problem is not None:
        if path is not None:
            try:
                remove_scratch(place, path)
            except HostError as exc:
                print(f"[office] warning: the temporary directory {path} on {place.host} was left behind: {exc}",
                      file=sys.stderr)
        raise problem
    debug(f"scratch on {place.host}: {path}, with {name} sent into it ({want[:12]})")
    return path, f"{path}/{name}"


def run_streamed(place, command, timeout=None):
    """One command string where a place is, its output straight to this
    terminal, for a step the occupant watches (an after-land action):
    through a host's shell on a terminal, the attended form (ssh -tt, a
    container's -it), so a question it asks reaches him; piped, the plain
    form with stdin closed. On this machine, bash -c in the place's
    directory with the terminal's own stdin. Returns the exit code."""
    import subprocess
    place = as_place(place)
    if not place.hosted:
        if not pathlib.Path(place.path).is_dir():
            raise HostError("path", f"no such directory on this machine: {place.path}")
        return subprocess.run(["bash", "-c", command], cwd=place.path, timeout=timeout).returncode
    reach(place)
    full = f"cd {shell_path(place.path)} && {command}"
    attended = sys.stdin.isatty()
    argv = place.attended_argv(full) if attended else place.argv(full)
    debug(f"{shown_argv([command])} in {place}, " + ("attended" if attended else "piped, stdin closed"))
    try:
        proc = subprocess.run(argv, stdin=None if attended else subprocess.DEVNULL, timeout=timeout)
    except OSError as exc:
        raise HostError("shell", f"could not run {place.shell}: {exc}")
    if proc.returncode == SSH_CONNECTION_FAILED and place.words()[:1] == ["ssh"]:
        raise _lost(place, f"exit {proc.returncode}")
    return proc.returncode


def make_scratch(place):
    import tempfile
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
    import shutil
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


# --- the audience line (0.17.0): a clone's git facts, the push guard, a bundle back ------
#
# office deliver carries a folder's landed work from the workbench clone
# to the audience's git host as curated commits. What it needs of the
# clone where the clone is: its remotes and identity (the defaults for
# the audience, author and base declarations), the push guard in its
# .git/hooks, and a bundle of the landed commits carried to the
# occupant's machine, where the audience answers with his credentials.

GUARD_MARK = "office push guard"
# The guard's version, written into the hook as `guard_version=N` (0.25.0).
# A hook with the mark and no version line is the first guard, 0.17.0's,
# which let a tag or another branch through under OFFICE_DELIVERY and
# knew the audience only by its remote's name and recorded URL as
# written. office status names an older guard with the line that replaces
# it; office upgrade and office projects set replace it.
GUARD_VERSION = 2
# The variable office deliver sets on the one push it makes, naming the
# delivery branch: the guard lets that branch through and nothing else.
DELIVERY_ENV = "OFFICE_DELIVERY"
PUSH_GUARD = """#!/bin/sh
# @MARK@ (office-src): a push to this project's audience goes through
# office deliver, which pushes one delivery branch and nothing else: no
# tag (bale's applied/ tags or any other), no bale branch, no other ref,
# whatever the push's form (--tags, --all, --mirror, a refspec, a tag by
# name). Written by office projects add and set, office upgrade and office
# deliver; the office owns this file (.git/hooks is outside what git
# tracks). A push with --no-verify runs no hook at all, this one included.
guard_version=@VERSION@
audience='@AUDIENCE@'
audience_url='@URL@'
remote="$1"; url="$2"
# A URL as the audience's git host knows it: no scheme, no user, no
# port, no trailing .git or slash, in lower case, so https://HOST/ORG/REPO,
# git@HOST:ORG/REPO.git and ssh://git@HOST/ORG/REPO are one audience.
norm() {
  printf '%s' "$1" | sed -e 's#^[A-Za-z][A-Za-z0-9+.-]*://##' -e 's#^[^@/]*@##' \\
    -e 's#^\\([^/:]*\\):[0-9][0-9]*/#\\1/#' -e 's#^\\([^/:]*\\):#\\1/#' -e 's#/*$##' -e 's#\\.git$##' | tr 'A-Z' 'a-z'
}
is_audience=no
[ "$remote" = "$audience" ] && is_audience=yes
if [ "$is_audience" = no ]; then
  pushed="$(norm "$url")"
  for known in "$audience_url" $(git config --get-all "remote.$audience.url" 2>/dev/null) \\
               $(git config --get-all "remote.$audience.pushurl" 2>/dev/null); do
    [ -n "$known" ] && [ "$(norm "$known")" = "$pushed" ] && is_audience=yes
  done
fi
[ "$is_audience" = yes ] || exit 0
delivery="${@ENV@:-}"
refused=0
while read -r local_ref local_sha remote_ref remote_sha; do
  [ -n "$remote_ref" ] || continue
  why=""
  if [ -z "$delivery" ]; then
    why="nothing goes to the audience by hand"
  else
    case "$delivery" in bale/*|refs/*|"") why="OFFICE_DELIVERY names $delivery, which is not a delivery branch" ;; esac
    case "$local_ref" in refs/tags/*) why="${why:-it is a tag}" ;; esac
    case "$remote_ref" in refs/tags/*) why="${why:-it is a tag}" ;; esac
    case "$local_sha" in *[!0]*) ;; *) why="${why:-it deletes a ref}" ;; esac
    [ "$remote_ref" = "refs/heads/$delivery" ] || why="${why:-office deliver pushes refs/heads/$delivery alone}"
  fi
  if [ -n "$why" ]; then
    echo "[office] refused: $remote_ref ($why)" >&2
    refused=$((refused + 1))
  fi
done
if [ -z "$delivery" ] || [ "$refused" -gt 0 ]; then
  echo "[office] refused: $remote is this project's audience, and only office deliver reaches it: office deliver FOLDER carries a folder's landed work as one delivery branch, and nothing else (no tag, no bale branch, no other ref)." >&2
  exit 1
fi
exit 0
"""

_GIT_FACTS_SCRIPT = (
    'd="$1"; ' + _EXPAND_D + 'cd "$d" || exit 3; git rev-parse --git-dir >/dev/null 2>&1 || exit 4; '
    'echo "branch=$(git symbolic-ref -q --short HEAD 2>/dev/null)"; echo "head=$(git rev-parse -q --verify HEAD 2>/dev/null)"; '
    'echo "name=$(git config user.name 2>/dev/null)"; echo "email=$(git config user.email 2>/dev/null)"; '
    'for r in $(git remote); do echo "remote=$r $(git remote get-url "$r" 2>/dev/null)"; '
    'h=$(git symbolic-ref -q --short "refs/remotes/$r/HEAD" 2>/dev/null); [ -z "$h" ] || echo "remote_head=$r ${h#"$r"/}"; done; '
    'echo "hooks_path=$(git config core.hooksPath 2>/dev/null)"; '
    'hook="$(git rev-parse --git-path hooks)/pre-push"; '
    'if [ -f "$hook" ]; then if grep -q "' + GUARD_MARK + '" "$hook"; then '
    "echo \"guard=office $(sed -n \"s/^audience='\\(.*\\)'\\$/\\1/p\" \"$hook\")\"; "
    'echo "guard_version=$(sed -n "s/^guard_version=//p" "$hook" | head -n 1)"; '
    'else echo "guard=other"; fi; else echo "guard=none"; fi; '
    'echo "dirty=$(git status --porcelain 2>/dev/null | wc -l | tr -d " ")"'
)


def git_facts(place):
    """What office projects and office deliver read of a clone where it
    is: branch, head, name, email, remotes {name: url}, remote_heads
    {remote: branch}, hooks_path, guard (none, other, or the audience the
    office's guard names) and dirty (changed paths, a count)."""
    place = as_place(place)
    run = run_in(place, ["sh", "-c", _GIT_FACTS_SCRIPT, "office-git-facts", place.path], chdir=False)
    if run.returncode != 0:
        why = {3: "no such directory", 4: "not a git repo"}.get(run.returncode, _last_words(run.stderr))
        raise HostError("refused", f"could not read the clone at {place}: {why}")
    facts = {"remotes": {}, "remote_heads": {}, "guard": "none", "guard_audience": None}
    for line in run.stdout.splitlines():
        key, _, value = line.partition("=")
        if key == "remote":
            name, _, url = value.partition(" ")
            facts["remotes"][name] = url
        elif key == "remote_head":
            name, _, branch = value.partition(" ")
            facts["remote_heads"][name] = branch
        elif key == "guard":
            kind, _, audience = value.partition(" ")
            facts["guard"] = kind
            facts["guard_audience"] = audience or None
        elif key in ("branch", "head", "name", "email", "hooks_path", "dirty"):
            facts[key] = value
        elif key == "guard_version":
            facts["guard_version"] = int(value) if value.isdigit() else 1
    facts["dirty"] = int(facts.get("dirty") or 0)
    if facts["guard"] == "office":
        # The first guard (0.17.0) wrote no version line.
        facts.setdefault("guard_version", 1)
    return facts


def guard_state(facts):
    """(state, line) for a clone's push guard, from git_facts: current,
    older (a guard an earlier release installed), none, other (a hook the
    office did not write) or unread (core.hooksPath points elsewhere)."""
    if facts.get("hooks_path"):
        return "unread", ("core.hooksPath is set, so the clone's .git/hooks are not the hooks git runs and the "
                          "guard goes unread there")
    kind = facts.get("guard")
    if kind == "office":
        v = facts.get("guard_version", 1)
        if v >= GUARD_VERSION:
            return "current", f"the push guard, version {v}"
        return "older", (f"an older push guard (version {v}), which lets a tag or another branch through under "
                         "office deliver's variable and knows the audience only by its remote's name and URL as "
                         "written")
    if kind == "other":
        return "other", "a pre-push hook the office did not write, so a push to the audience by hand is not refused"
    return "none", "no push guard"


_GUARD_SCRIPT = (
    'd="$1"; ' + _EXPAND_D + 'cd "$d" || exit 3; git rev-parse --git-dir >/dev/null 2>&1 || exit 4; '
    '[ -z "$(git config core.hooksPath 2>/dev/null)" ] || exit 6; '
    'hooks="$(git rev-parse --git-path hooks)"; mkdir -p "$hooks" || exit 5; hook="$hooks/pre-push"; '
    'if [ -f "$hook" ] && ! grep -q "' + GUARD_MARK + '" "$hook"; then exit 7; fi; '
    'printf %s "$HOOK" > "$hook" && chmod +x "$hook" && echo "guard=written $hook"'
)
_GUARD_FAILED = {3: "no such directory", 4: "not a git repo", 5: "could not make the hooks directory",
                 6: "core.hooksPath is set, so this clone's .git/hooks are not the hooks git runs; the guard "
                    "would go unread there (unset it, or guard that directory by hand)",
                 7: "another pre-push hook is already there, and the office does not replace a hook it "
                    "did not write; move it aside, or add the guard's refusal to it by hand"}


def push_guard_text(audience, url):
    """The hook, for one audience. The audience's name and URL are checked
    words (a remote's name; a URL git took), and a quote in either would
    end the shell's string, so one is refused."""
    if "'" in (audience or "") or "'" in (url or ""):
        raise HostError("refused", f"the audience {audience!r} or its URL {url!r} holds a quote, which the guard "
                                   "cannot carry; rename the remote")
    return (PUSH_GUARD.replace("@MARK@", GUARD_MARK).replace("@VERSION@", str(GUARD_VERSION))
            .replace("@AUDIENCE@", audience).replace("@URL@", url or "").replace("@ENV@", DELIVERY_ENV))


def install_push_guard(place, audience, url):
    """Write the push guard into the clone's .git/hooks/pre-push, where it
    is (through the shell for a hosted place): the clone can no longer be
    pushed to the audience by hand. Returns the line to print. Writes
    only outside what git tracks, as prepare does."""
    place = as_place(place)
    env = {"HOOK": push_guard_text(audience, url)}
    argv = ["sh", "-c", _GUARD_SCRIPT, "office-guard", place.path]
    if place.hosted:
        argv = ["env", f"HOOK={env['HOOK']}", *argv]
    run = run_in(place, argv, env=env, chdir=False)
    if run.returncode != 0:
        raise HostError("refused", f"could not install the push guard in {place}: "
                        f"{_GUARD_FAILED.get(run.returncode, run.stderr.strip() or f'exit {run.returncode}')}")
    return (f"push guard installed in {place} (.git/hooks/pre-push): a push to {audience} by hand is refused there; "
            "office deliver pushes a delivery branch alone")


def bundle_to_here(place, local, prerequisites, refs):
    """A git bundle of the refs, thin against the prerequisites, made in
    the clone where it is and carried to local on this machine (through
    the shell, into the office's one temporary directory, removed after).
    Returns local's sha256."""
    place = as_place(place)
    argv = ["git", "bundle", "create", "-q", None, *[f"^{p}" for p in prerequisites], *refs]
    if not place.hosted:
        argv[4] = str(local)
        run = run_in(place, argv, timeout=TRANSFER_TIMEOUT)
        if run.returncode != 0:
            raise HostError("refused", f"git bundle create in {place.path} failed: {_last_words(run.stderr)}")
        return sha256_of(local)
    with Scratch(place) as sc:
        remote = f"{sc.path}/landed.bundle"
        argv[4] = remote
        run = run_in(place, argv, timeout=TRANSFER_TIMEOUT)
        if run.returncode != 0:
            raise HostError("refused", f"git bundle create in {place} failed: {_last_words(run.stderr)}")
        return fetch_file(place, remote, str(local))


def run_feeding(place, argv, local_file, timeout=TRANSFER_TIMEOUT):
    """Run one argv in the place's directory with a file from this
    machine on its stdin (bale relay SID - on a host reads the planner's
    answer that way): a Run. On this machine the file is the process's
    stdin; through the shell its bytes travel on the connection."""
    import shlex
    import subprocess
    place = as_place(place)
    if not place.hosted:
        if not pathlib.Path(place.path).is_dir():
            raise HostError("path", f"no such directory on this machine: {place.path}")
        with open(local_file, "rb") as fh:
            try:
                proc = subprocess.run(argv, cwd=place.path, stdin=fh, capture_output=True, text=True, timeout=timeout,
                                      env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            except subprocess.TimeoutExpired:
                raise HostError("refused", f"{shown_argv(argv)} in {place.path} did not finish in {timeout}s")
            except OSError as exc:
                raise HostError("shell", f"could not run {argv[0]}: {exc}")
        debug(f"{shown_argv(argv)} in {place.path}, fed {local_file}: exit {proc.returncode}")
        return Run(proc.returncode, proc.stdout, proc.stderr, shown_argv(argv), place.path)
    command = f"cd {shell_path(place.path)} && PYTHONDONTWRITEBYTECODE=1 {shlex.join(argv)}"
    with open(local_file, "rb") as fh:
        rc, out, err = _raw(place, command, stdin=fh, timeout=timeout)
    debug(f"{shown_argv(argv)} in {place}, fed {local_file}: exit {rc}")
    return Run(rc, (out or b"").decode("utf-8", "replace"), err, shown_argv(argv), str(place))


# --- a clone moved to its host (office projects add --from) ---------------------------------

def _git(repo, *args, binary=False):
    import subprocess
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
    'd="$1"; b="$2"; hk="$3"; hv="$4"; n="$5"; shift 5; ' + _EXPAND_D +
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
    run = run_in(place, ["sh", "-c", 'd="$1"; ' + _EXPAND_D + '[ -e "$d" ] && echo exists=yes || echo exists=no',
                         "office-exists", path], chdir=False)
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
    import shutil
    import tempfile
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
                gone = run_in(place, ["sh", "-c", 'd="$1"; ' + _EXPAND_D + 'rm -rf -- "$d"', "office-remove",
                                      place.path], chdir=False)
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


# --- a worker's probe block, run where a project is (office probe, 0.18.0) -----------------
#
# A probe is a tool call whose courier is a role (TARBALL.md 4.6), and the
# office is the occupant's hands at the terminal: office probe runs a
# worker's probe block where the folder's project lives, so nobody opens a
# VPN, an ssh and a docker exec by hand to paste one in. The block runs
# with stdin closed, through the plain (non-attended) form of the
# project's shell, since a probe never waits on a terminal (TARBALL.md
# 4.3), in the project's path; its stdout comes back here as it comes, and
# its stderr to this terminal. The file-based fallback (TARBALL.md 4.4)
# leaves a probe-output/ directory where it ran: carry_dir_here brings it
# to this machine and remove_dir_there removes it, since the office leaves
# nothing on a host outside the project's repo and a probe's output is not
# the repo's.

# How long a block may run before the office stops it. A block bounds
# itself (TARBALL.md 4.2); this is the office's backstop for one that
# does not, and OFFICE_PROBE_TIMEOUT (whole seconds) overrides it.
PROBE_TIMEOUT = 1800
PROBE_TIMEOUT_ENV = "OFFICE_PROBE_TIMEOUT"


def probe_timeout(environ=None):
    """The backstop in seconds: OFFICE_PROBE_TIMEOUT when it is a whole
    number above 0, else PROBE_TIMEOUT (a value that is not is said)."""
    environ = os.environ if environ is None else environ
    raw = environ.get(PROBE_TIMEOUT_ENV)
    if raw is None:
        return PROBE_TIMEOUT
    if raw.isdigit() and int(raw) > 0:
        return int(raw)
    print(f"[office] warning: {PROBE_TIMEOUT_ENV}={raw!r} is not a whole number of seconds above 0; "
          f"the block gets {PROBE_TIMEOUT}s", file=sys.stderr)
    return PROBE_TIMEOUT


def probe_command(place, block):
    """The one command string that runs a block where the place is: in its
    directory (exit 96 when that is not there), the block as bash -c's
    script, stdin closed."""
    import shlex
    return (f"cd {shell_path(place.path)} || exit {_NO_DIR}\n"
            f"exec bash -c {shlex.quote(block)} office-probe </dev/null\n")


def run_probe(place, block, screen=None, timeout=None, env=None):
    """Run a probe block where the place is: on this machine, bash in its
    directory; on a host, through the plain form of its shell, after the
    reach. Its stdout is copied to screen (this terminal's stdout) as it
    comes and kept; its stderr goes to this terminal as it is. env adds to
    or overrides this process's environment for a block run on this
    machine (0.34.0: office probe puts office-on on a spanning block's
    PATH). Returns (exit code, stdout text, whether the backstop stopped
    it). A path that is not there and a host that stopped answering are
    HostErrors."""
    import subprocess
    import threading
    place = as_place(place)
    timeout = timeout or probe_timeout()
    command = probe_command(place, block)
    if place.hosted:
        reach(place)
        argv = place.argv(command)
        debug(f"a probe block ({len(block)} bytes) through {place.host} in {place.path}, stdin closed")
    else:
        if not pathlib.Path(place.path).is_dir():
            raise HostError("path", f"no such directory on this machine: {place.path}")
        argv = ["bash", "-c", command]
        debug(f"a probe block ({len(block)} bytes) in {place.path}, stdin closed")
    full = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    full.update(env or {})
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, env=full)
    except OSError as exc:
        raise HostError("shell", f"could not run {argv[0]}: {exc}")
    stopped = {"yes": False}

    def stop():
        stopped["yes"] = True
        proc.kill()

    timer = threading.Timer(timeout, stop)
    timer.start()
    screen = screen if screen is not None else sys.stdout.buffer
    kept = bytearray()
    try:
        fd = proc.stdout.fileno()
        while True:
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            screen.write(chunk)
            screen.flush()
            kept += chunk
    finally:
        timer.cancel()
    code = proc.wait()
    text = kept.decode("utf-8", "replace")
    if code == _NO_DIR and not kept:
        raise HostError("path", f"no such directory {'on ' + place.host if place.hosted else 'on this machine'}: "
                                f"{place.path}")
    if place.hosted and code == SSH_CONNECTION_FAILED and not kept and place.words()[:1] == ["ssh"]:
        raise _lost(place, f"exit {code}")
    debug(f"the probe block in {place}: exit {code}, {len(kept)} bytes on stdout"
          + (f", stopped at {timeout}s" if stopped["yes"] else ""))
    return code, text, stopped["yes"]


def _plain_name(name):
    if not name or "/" in name or name in (".", ".."):
        raise HostError("refused", f"{name!r} is not one directory's name")
    return name


def dir_there(place, name):
    """Whether the directory name (one plain name) is there in the place's
    directory: on this machine a look, on a host one call through its
    shell."""
    place = as_place(place)
    return not missing_paths(place, [_plain_name(name)])


def _count_files(root):
    return sum(1 for p in pathlib.Path(root).rglob("*") if p.is_file() and not p.is_symlink())


_CARRY_SCRIPT = 'echo "files=$(find "$1" -type f | wc -l | tr -d " ")" >&2 && tar -czf - -- "$1"'


def carry_dir_here(place, name, dest):
    """Bring the directory name (one plain name) in the place's directory
    to dest on this machine, which must not exist yet: copied on this
    machine, or carried from a host as one tar stream through its shell,
    the files that arrive held to the count the far side reports. The
    original is left where it is (remove_dir_there removes it once the
    caller has what it carried). Returns the number of files carried."""
    import shlex
    import shutil
    import tarfile
    import tempfile
    place = as_place(place)
    name = _plain_name(name)
    dest = pathlib.Path(dest)
    if dest.exists():
        raise HostError("refused", f"{dest} is there already; nothing was carried over it")
    if not place.hosted:
        shutil.copytree(pathlib.Path(place.path) / name, dest, symlinks=True)
        return _count_files(dest)
    with tempfile.TemporaryDirectory(prefix=SCRATCH_PREFIX) as tmp:
        tgz = pathlib.Path(tmp) / "carried.tar.gz"
        with open(tgz, "wb") as fh:
            rc, _, err = _raw(place, f"cd {shell_path(place.path)} && sh -c {shlex.quote(_CARRY_SCRIPT)} office-carry "
                                     f"{shlex.quote(name)}", stdout=fh)
        if rc != 0:
            raise HostError("refused", f"{name}/ in {place} could not be read (exit {rc}): {_last_words(err)}")
        counts = [l.split("=", 1)[1].strip() for l in err.splitlines() if l.startswith("files=")]
        there = int(counts[-1]) if counts and counts[-1].isdigit() else None
        out = pathlib.Path(tmp) / "x"
        out.mkdir()
        try:
            with tarfile.open(tgz) as t:
                for m in t.getmembers():
                    parts = pathlib.PurePosixPath(m.name).parts
                    if not parts or parts[0] != name or ".." in parts or m.name.startswith("/"):
                        raise HostError("output", f"{name}/ from {place.host} holds {m.name!r}, outside {name}/; "
                                                  "nothing was carried")
                if hasattr(tarfile, "data_filter"):
                    t.extractall(out, filter="data")
                else:
                    t.extractall(out)
        except (tarfile.TarError, OSError) as exc:
            raise HostError("output", f"{name}/ from {place.host} did not arrive as a readable archive: {exc}")
        here = _count_files(out / name)
        if there is None or here != there:
            raise HostError("output", f"{name}/ from {place.host} did not arrive whole: {there if there is not None else 'no'} "
                                      f"file(s) there, {here} here; nothing was carried")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(out / name), str(dest))
    debug(f"carried {name}/ from {place} to {dest}: {here} file(s)")
    return here


def remove_dir_there(place, name):
    """Remove the directory name (one plain name, never a path) from the
    place's directory: on this machine, or through the host's shell."""
    import shutil
    place = as_place(place)
    name = _plain_name(name)
    if not place.hosted:
        shutil.rmtree(pathlib.Path(place.path) / name)
        return
    run = run_in(place, ["rm", "-rf", "--", name])
    if run.returncode != 0:
        raise HostError("refused", f"rm -rf {name} in {place} exited {run.returncode}: {_last_words(run.stderr)}")
    debug(f"removed {name}/ from {place}")
