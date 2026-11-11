#!/usr/bin/env python3
"""The office's read side: the reader over bale's records and its renderings.

The office reads bale's records in its projects' repos and renders them;
it never copies them (doctrine section 10). This module is the only place
the office talks to bale. It runs `bale` from the PATH in a project's
directory with stdin closed, reads the one JSON line a --json surface
prints, and returns plain data; for a project that declares a host, the
same bale calls run through the project's shell in the project's path
(office_host.py), with the same keys and the same consumption manifest,
after one reach check per host and command. It never reads .bale/. The
reads write nothing. Two verbs run bale to make or land something, when the
occupant asks: office start runs bale's pack, or bale open for a
planner's bundle, for a session and the context that rides beside it,
and copies the tarballs bale made into an out tray; office land runs
bale apply, or bale retry for a held session, with the occupant's own
terminal as its stdin, so every question bale asks reaches him and the
office answers none, then reads what happened from bale's records.

share/bale-consumption.toml is the contract with bale: every verb and
flag called here (each call's argv is built from it), every JSON key
read (each read goes through Reader.key, which refuses a key the
manifest does not declare), and the bale version the reads were probed
on. A declared key that bale's line lacks is an error naming that
version, so a bale release that moves a key fails loudly here and in
the test suite, never silently on a walk-in.

Standard library only. The command line prints renderings on stdout,
logs to stderr with an [office] prefix, and exits 0 on success, 1 on a
refusal, 2 on a usage or internal error, and 3 when it rendered but at
least one project could not be read (the rendering says which and why).
"""

import argparse
import datetime as dt
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_host as ohost  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
CONSUMPTION = INSTALL / "share" / "bale-consumption.toml"
BALE_TIMEOUT = 60
# A pack copies a tree and runs bale's own checks; give it longer.
PACK_TIMEOUT = 600
# Attempts that carry a response tarball: the ones a trust ledger counts.
RESPONSE_COMMANDS = ("apply", "retry")
OUTBOX_RE = oh.LazyPattern(r"^request-(.+)\.tar\.gz$")
# A project's release file, at any depth (VERSION, bin/VERSION).
VERSION_FILE = "VERSION"


class BaleError(Exception):
    """One read that could not be done, as one line a person can act on.

    kind: missing (no bale on PATH), path (the project directory is not
    there), refused (bale exited non-zero), output (not the JSON line the
    surface promises), key (a declared key bale's line lacks), undeclared
    (the office asked for a key its consumption manifest does not name:
    a defect in office-src), unreachable (a hosted project's host did not
    answer: one line naming the project, the host, the connect text and
    the command to rerun)."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


# --- the consumption manifest --------------------------------------------------

class Consumption:
    """share/bale-consumption.toml, read once."""

    def __init__(self, path=CONSUMPTION):
        data = oh.read_toml(path)
        try:
            self.floor = data["bale"]["floor"]
            oh.parse_version(self.floor)
            self.surfaces = data["surfaces"]
        except (KeyError, TypeError, oh.HelperError) as exc:
            raise oh.HelperError(f"{path}: not a consumption manifest ({exc})")
        self.path = path

    def surface(self, name):
        if name not in self.surfaces:
            raise BaleError("undeclared", f"bale surface {name!r} is not in {self.path.name}")
        return self.surfaces[name]

    def keys(self, name):
        return set(self.surface(name).get("keys", []))

    def argv(self, name, **values):
        """The argv for a surface, from its declaration: the fixed argv
        with {placeholders} filled, then each declared optional flag whose
        value was given, in the declared order. A surface that declares
        flags_before (0.37.0: apply and retry, whose tarball comes last in
        bale's usage line) has its flags placed before that word of its
        argv instead of after the whole of it."""
        s = self.surface(name)
        if not s.get("calls", True):
            raise BaleError("undeclared", f"the office never calls bale for {name!r}; it only reads its report")

        def fill(word):
            m = re.fullmatch(r"\{([a-z_]+)\}", word)
            if not m:
                return word
            if values.get(m.group(1)) is None:
                raise BaleError("undeclared", f"bale {name} needs a value for {word}")
            return str(values[m.group(1)])

        out = [fill(w) for w in s["argv"]]
        flags = []
        for flag, word in s.get("optional", []):
            key = word.strip("{}")
            if values.get(key) is not None:
                flags += [flag, str(values[key])]
        # A list value: the flag once per element, in order.
        for flag, word in s.get("repeated", []):
            for v in values.get(word.strip("{}")) or []:
                flags += [flag, str(v)]
        # A true value: the bare flag.
        for flag, word in s.get("switches", []):
            if values.get(word.strip("{}")):
                flags.append(flag)
        before = s.get("flags_before")
        if before is None:
            return out + flags
        if before not in s["argv"]:
            raise BaleError("undeclared", f"bale {name}'s flags_before {before!r} is not a word of its argv")
        at = s["argv"].index(before)
        return out[:at] + flags + out[at:]

    def subject_sid(self, subject):
        """(kind, sid) when a commit subject has one of the shapes bale
        gives its commits ([surfaces.commits]): work, merge or sweep;
        None for any other subject. A convention bale follows, declared
        here so a change in it fails a test (a slip for bale-src)."""
        shapes = self.surface("commits").get("subjects", {})
        for kind, shape in shapes.items():
            head, _, tail = shape.partition("{sid}")
            if not subject.startswith(head):
                continue
            rest = subject[len(head):]
            sid, sep, after = rest.partition(tail) if tail else (rest.split(" ", 1)[0], "", "")
            if tail and not sep:
                # A tail that ends the shape (merge: none) is matched at the end.
                continue
            if oh.SID_RE.match(sid):
                return kind, sid
        return None

    def own_commit(self, subject):
        """Whether a commit subject is one bale gives a commit it makes for
        itself, carrying nothing of a session's work (0.36.0): a sweep
        (the session's telemetry record) or one of the housekeeping
        subjects [surfaces.commits] own lists by its start (`bale: ignore
        .bale/`, made where bale is first set up in a working copy). A
        session's work commit and its landing merge are not bale's own:
        what they carry is the work. office deliver takes what bale's own
        commits changed out of a delivery."""
        found = self.subject_sid(subject)
        if found and found[0] == "sweep":
            return True
        starts = self.surface("commits").get("own", [])
        if not isinstance(starts, list) or not all(isinstance(s, str) and s for s in starts):
            raise oh.HelperError(f"{self.path}: [surfaces.commits] own is not a list of non-empty strings")
        return any(subject.startswith(s) for s in starts)


# --- the reader ------------------------------------------------------------------

class Reader:
    """Runs bale's JSON surfaces and hands back plain data.

    Calls are cached per (directory, argv) for the life of the reader, so
    one rendering asks bale each question once. `touched` collects every
    (surface, key) read, which the suite compares with the manifest."""

    def __init__(self, consumption=None, runner=None):
        # runner: what runs a bale call, subprocess.run unless a test hands
        # in its own; named here, not as the default, so a reader that runs
        # nothing loads nothing of subprocess.
        import subprocess
        self.consumption = consumption or Consumption()
        self.runner = runner if runner is not None else subprocess.run
        self.touched = set()
        self._cache = {}
        self._installed = None
        # Hosted places a start has checked in this process (reach, the
        # bale floor, the repo): checked once, however many steps ask.
        self.places_checked = set()
        # What a hosted round read beside bale (office_bale.hosted_round):
        # which paths are missing, the doctrine's sums, keyed by place.
        self.facts = {}
        self.also_runs = []

    # The one door every key read goes through.
    def key(self, obj, surface, path):
        if path not in self.consumption.keys(surface):
            raise BaleError("undeclared", f"the office reads {surface} key {path!r}, which "
                            f"{self.consumption.path.name} does not declare (a defect in office-src)")
        self.touched.add((surface, path))
        name = path.rsplit(".", 1)[-1].removesuffix("[]")
        if not isinstance(obj, dict) or name not in obj:
            raise BaleError("key", f"bale's {surface} line has no key {path!r}; the office's reads were "
                            f"written against bale {self.consumption.floor} or later "
                            f"(installed: {self._installed or 'unknown'})")
        return obj[name]

    # The door for the watch catalog's keys (share/watch-queries.toml):
    # a query names its keys as data, so they cannot be literal reads
    # above; each is held to the manifest here, the same way.
    def reach(self, obj, surface, path, at=None):
        """Every value a declared key path reaches in obj: a[].b is b in
        each element of a, a.*.b is b in every value of the map a. at, a
        prefix of path, says where obj already sits (a class's row is at
        classes.*). A parent that lacks a key is an error naming the bale
        the reads were written against, as Reader.key's is."""
        if path not in self.consumption.keys(surface):
            raise BaleError("undeclared", f"the office reads {surface} key {path!r}, which "
                            f"{self.consumption.path.name} does not declare (a defect in office-src)")
        self.touched.add((surface, path))
        parts = path.split(".")
        if at is not None:
            skip = at.split(".")
            if parts[:len(skip)] != skip:
                raise BaleError("undeclared", f"{path!r} does not sit under {at!r}")
            parts = parts[len(skip):]
        frontier = [obj]
        for part in parts:
            name = part.removesuffix("[]")
            nxt = []
            for node in frontier:
                if node is None:
                    continue
                if name == "*":
                    if isinstance(node, dict):
                        nxt.extend(node.values())
                    continue
                if not isinstance(node, dict) or name not in node:
                    raise BaleError("key", f"bale's {surface} line has no key {path!r}; the office's reads were "
                                    f"written against bale {self.consumption.floor} or later "
                                    f"(installed: {self._installed or 'unknown'})")
                value = node[name]
                if part.endswith("[]"):
                    nxt.extend(value or [])
                else:
                    nxt.append(value)
            frontier = nxt
        return frontier

    def bale(self):
        import shutil
        exe = shutil.which("bale")
        if exe is None:
            raise BaleError("missing", "bale is not on PATH; the read side runs bale's --json surfaces")
        return exe

    @staticmethod
    def hosted(cwd):
        """Whether a read runs through a project's shell."""
        return isinstance(cwd, ohost.Place) and cwd.hosted

    def through_shell(self, place, argvs, timeout):
        """Several argvs through a hosted place's shell in one connection
        (office_host.run_many), each a Run; a host that does not answer,
        a path that is not there and a broken shell are BaleErrors."""
        try:
            return ohost.run_many(place, argvs, timeout)
        except ohost.HostError as exc:
            raise BaleError(exc.kind if exc.kind in ("unreachable", "path") else "refused", str(exc))

    def prefetch(self, cwd, requests, timeout=BALE_TIMEOUT, extra=(), texts=()):
        """Ask several declared reading surfaces at once where that saves
        connections: through a hosted place's shell they travel as one
        batch and land in the cache, so the reads that follow ask bale
        nothing more; on this machine each read is cheap and nothing is
        done. requests is [(surface, values dict)]. A line the batch
        could not parse surfaces when the read for it is made.

        extra (since 0.16.0) is argvs that ride the same connection after
        bale's reads, the office's own (a check of the repo, the doctrine's
        sums, which paths are there, a temporary directory's removal); their
        Runs come back, in order, for the caller to read. texts is
        [(surface, values)] of text surfaces whose every line the caller
        reads (bale relay's block): never cached, their Runs come back keyed
        by surface name. Returns (text runs, extra runs). The connection is
        made even when every read is cached, if extra or texts is not
        empty."""
        if not self.hosted(cwd):
            return {}, []
        wanted = []
        texts = [(surface, self.consumption.argv(surface, **values)) for surface, values in texts]
        for surface, values in requests:
            argv = self.consumption.argv(surface, **values)
            key = (str(cwd), tuple(argv))
            if key not in self._cache and key not in [k for k, _ in wanted]:
                wanted.append((key, (surface, argv)))
        extra = [list(a) for a in extra]
        if not wanted and not texts and not extra:
            return {}, []
        argvs = ([["bale", *argv] for _, (_, argv) in wanted] + [["bale", *argv] for _, argv in texts] + extra)
        runs = self.through_shell(cwd, argvs, timeout)
        for (key, (surface, argv)), run in zip(wanted, runs):
            shown = "bale " + " ".join(argv)
            if run.returncode != 0:
                debug(f"{shown} in {cwd}: exit {run.returncode} in the batch; read on its own for the reason")
                continue
            try:
                self._cache[key] = self.parse(surface, run, shown, str(cwd))
            except BaleError as exc:
                debug(f"{shown} in {cwd}: not cached from the batch ({exc})")
        rest = runs[len(wanted):]
        text_runs = {surface: run for (surface, _), run in zip(texts, rest)}
        return text_runs, rest[len(texts):]

    def invoke(self, surface, cwd=None, timeout=BALE_TIMEOUT, whole_why=False, also=None, accept=(), **values):
        """Run one declared surface with stdin closed; (proc, shown, where).
        Refuses when bale exits non-zero, carrying bale's last words, or,
        with whole_why, everything from its error line on (a refusal that
        lists what it searched, say); an exit code in accept (a surface
        whose refusal is a JSON line the caller reads, since 0.18.0) is
        handed back instead. A hosted place runs it through the
        project's shell, in the project's path. also (a hosted place only)
        is argvs that ride the same connection after bale, whatever bale
        said; their Runs are kept in self.also_runs, and what any of them
        printed with the office's prefix on stderr is passed on."""
        import subprocess
        argv = self.consumption.argv(surface, **values)
        where = str(cwd) if cwd is not None else os.getcwd()
        shown = "bale " + " ".join(argv)
        self.also_runs = []
        if self.hosted(cwd):
            runs = self.through_shell(cwd, [["bale", *argv], *[list(a) for a in also or []]], timeout)
            proc, self.also_runs = runs[0], runs[1:]
            for run in self.also_runs:
                for line in run.stderr.splitlines():
                    if line.startswith("[office] "):
                        print(line, file=sys.stderr)
        else:
            exe = self.bale()
            if cwd is not None and not pathlib.Path(cwd).is_dir():
                raise BaleError("path", f"no such directory on this machine: {cwd}")
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            try:
                proc = self.runner([exe, *argv], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   capture_output=True, text=True, timeout=timeout)
            except subprocess.TimeoutExpired:
                raise BaleError("refused", f"{shown} in {where} did not finish in {timeout}s")
            except OSError as exc:
                raise BaleError("missing", f"could not run {exe}: {exc}")
            debug(f"{shown} in {where}: exit {proc.returncode}, {len(proc.stdout)} bytes on stdout")
        if proc.returncode != 0 and proc.returncode not in accept:
            err = [l for l in proc.stderr.splitlines() if l.strip()]
            why = err[-1] if err else "no message"
            if whole_why and err:
                start = next((i for i, l in enumerate(err) if "error" in l.lower()), max(0, len(err) - 8))
                why = "\n".join(err[start:])
            raise BaleError("refused", f"{shown} refused in {where} (exit {proc.returncode}): {why}")
        return proc, shown, where

    def run(self, surface, cwd=None, **values):
        """Run one declared reading surface and return its parsed JSON
        line, asking bale each question once."""
        argv = self.consumption.argv(surface, **values)
        where = str(cwd) if cwd is not None else os.getcwd()
        cache_key = (where, tuple(argv))
        if cache_key in self._cache:
            return self._cache[cache_key]
        proc, shown, where = self.invoke(surface, cwd, **values)
        result = self.parse(surface, proc, shown, where)
        self._cache[cache_key] = result
        return result

    def forget(self, cwd):
        """Drop what this reader has cached about a directory, after a
        verb that changed what bale records there."""
        where = str(cwd)
        self._cache = {k: v for k, v in self._cache.items() if k[0] != where}

    def lines(self, surface, cwd, **values):
        """Run one declared text surface with stdin closed and return
        every stdout line it printed (a block to carry, a report)."""
        if self.consumption.surface(surface).get("format") != "text":
            raise BaleError("undeclared", f"bale {surface} is not declared as a text surface")
        proc, _, _ = self.invoke(surface, cwd, timeout=PACK_TIMEOUT, whole_why=True, **values)
        return proc.stdout.splitlines()

    def interact(self, surface, cwd, capture, cleanup=None, **values):
        """Run a surface the occupant answers: stdin and stderr stay his
        terminal, so every question bale asks reaches him as bale asks it
        and the office answers none; stdout is copied to ours as it comes
        and kept in the capture file, for the blocks bale prints to carry.
        Returns bale's exit code. cleanup, a hosted place's Scratch (the
        response carried there, since 0.16.0), is removed by the same
        command once bale exits, whatever it said; when bale exited on its
        own (not by a signal, not a lost connection) the scratch is told so,
        and its own removal is not needed."""
        import shlex
        import subprocess
        spec = self.consumption.surface(surface)
        if not spec.get("interactive"):
            raise BaleError("undeclared", f"bale {surface} is not declared interactive in {self.consumption.path.name}")
        argv = self.consumption.argv(surface, **values)
        hosted = self.hosted(cwd)
        if hosted:
            # Through the project's shell: on a terminal, the attended form
            # (ssh -tt, a container's -it), so bale's questions reach the
            # occupant through every layer; piped, the plain form with
            # stdin closed, and nothing ever asks.
            try:
                ohost.reach(cwd)
            except ohost.HostError as exc:
                raise BaleError(exc.kind if exc.kind in ("unreachable", "path") else "refused", str(exc))
            command = (f"cd {ohost.shell_path(cwd.path)} && PYTHONDONTWRITEBYTECODE=1 exec bale "
                       + " ".join(shlex.quote(w) for w in argv))
            gone = cleanup.removal_words() if cleanup is not None else ""
            if gone:
                # Not exec: the shell outlives bale to remove the scratch,
                # and exits with bale's own code.
                command = (f"cd {ohost.shell_path(cwd.path)} && PYTHONDONTWRITEBYTECODE=1 bale "
                           + " ".join(shlex.quote(w) for w in argv) + f"; rc=$?; {gone}; exit $rc")
            attended = sys.stdin.isatty()
            full = cwd.attended_argv(command) if attended else cwd.argv(command)
            debug(f"bale {' '.join(argv)} in {cwd}, " + ("attended through " + ohost.shown_argv(cwd.attended_words())
                                                       if attended else "piped, stdin closed"))
            try:
                proc = subprocess.Popen(full, stdin=None if attended else subprocess.DEVNULL, stdout=subprocess.PIPE)
            except OSError as exc:
                raise BaleError("missing", f"could not run {full[0]}: {exc}")
        else:
            exe = self.bale()
            if not pathlib.Path(cwd).is_dir():
                raise BaleError("path", f"no such directory on this machine: {cwd}")
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            debug(f"bale {' '.join(argv)} in {cwd}, stdin and stderr the terminal's")
            try:
                proc = subprocess.Popen([exe, *argv], cwd=cwd, env=env, stdout=subprocess.PIPE)
            except OSError as exc:
                raise BaleError("missing", f"could not run {exe}: {exc}")
        screen = sys.stdout.buffer
        with open(capture, "wb") as keep:
            fd = proc.stdout.fileno()
            try:
                while True:
                    chunk = os.read(fd, 4096)
                    if not chunk:
                        break
                    screen.write(chunk)
                    screen.flush()
                    keep.write(chunk)
                    keep.flush()
            except KeyboardInterrupt:
                # bale got the same interrupt; let it finish saying so.
                log("interrupted; waiting for bale to stop")
        code = proc.wait()
        if hosted and cleanup is not None and 0 <= code < 128:
            cleanup.removed_by_step()
        if hosted and attended:
            # Through a pseudo-terminal every line ends in CR LF; the
            # capture is read for the blocks bale prints, line by line.
            data = pathlib.Path(capture).read_bytes()
            pathlib.Path(capture).write_bytes(data.replace(b"\r\n", b"\n"))
        return code

    def unlock(self, cwd, sid, surface="unlock"):
        """End a read-only sitting: bale unlock SID --json in its repo,
        stdin closed, since bale asks nothing there (the second-trip probe
        found it so, on a terminal and piped); or, with surface "withdraw"
        (0.24.0), close a session that was never worked with bale's own
        reason, abandoned. Never cached; what was cached about the repo is
        dropped, since the registry changed."""
        proc, shown, where = self.invoke(surface, cwd, whole_why=True, sid=sid)
        self.forget(cwd)
        return self.parse(surface, proc, shown, where)

    def pack(self, surface, cwd, also=None, **values):
        """Run one of the surfaces that make something (a session, a
        context tarball): never cached, since each run makes a new one.
        Returns (the report, bale's stderr lines). also: as invoke's."""
        proc, shown, where = self.invoke(surface, cwd, timeout=PACK_TIMEOUT, also=also, **values)
        return self.parse(surface, proc, shown, where), proc.stderr.splitlines()

    def parse(self, surface, proc, shown, where):
        import json
        lines = [l for l in proc.stdout.splitlines() if l.strip()]
        spec = self.consumption.surface(surface)
        if spec.get("format") == "text":
            if not lines:
                raise BaleError("output", f"{shown} printed nothing in {where}")
            result = lines[-1]
        else:
            if not lines:
                raise BaleError("output", f"{shown} printed no JSON line in {where}")
            try:
                result = json.loads(lines[-1])
            except json.JSONDecodeError as exc:
                raise BaleError("output", f"{shown} in {where}: the last stdout line is not JSON ({exc})")
            want = spec.get("outcome")
            got = self.key(result, surface, "outcome")
            if want is not None and got != want:
                raise BaleError("output", f"{shown} in {where}: outcome {got!r}, the surface promises {want!r}")
        return result

    # --- what the renderings ask for ---------------------------------------

    def installed_version(self, cwd=None):
        """bale's version from `bale --version`, or raise: this machine's
        bale, or, given a hosted place, the one its shell reaches."""
        line = self.run("version", cwd if self.hosted(cwd) else None)
        m = re.match(self.consumption.surface("version")["pattern"], line)
        if not m:
            raise BaleError("output", f"bale --version printed {line!r}, not `bale X.Y.Z`")
        if not self.hosted(cwd):
            self._installed = m.group(1)
        return m.group(1)

    def status(self, cwd):
        return self.run("status", cwd)

    def open_sessions(self, cwd):
        """[(sid, read_only)] for the sessions open in the repo, oldest
        first; read_only from the recorded scope (an empty scope locks
        nothing and lands nothing)."""
        st = self.status(cwd)
        sids = self.key(st, "status", "sessions") or []
        scopes = self.key(st, "status", "scopes") or {}
        return [(sid, scopes.get(sid) == []) for sid in sids]

    def known_sids(self, cwd):
        """Every session id the repo's JSON surfaces name: the requests in
        its outbox and the open sessions. bale's aggregate names members
        of its anomaly counts only, so the outbox is the fullest list a
        --json surface carries (a slip for bale-src)."""
        st = self.status(cwd)
        out = set(self.key(st, "status", "sessions") or [])
        for name in self.key(st, "status", "outbox") or []:
            m = OUTBOX_RE.match(name)
            if m and oh.SID_RE.match(m.group(1)):
                out.add(m.group(1))
        return sorted(out)

    def dossier(self, cwd, sid):
        """One session's dossier, or None when bale's records hold no such
        session. A record bale could not parse is an error, not a miss."""
        d = self.run("dossier", cwd, sid=sid)
        if self.key(d, "dossier", "found"):
            return d
        if self.key(d, "dossier", "parse_failure"):
            raise BaleError("output", f"bale has a record for {sid} in {cwd} but could not parse it")
        if self.key(d, "dossier", "filtered_record_version"):
            raise BaleError("output", f"bale's record for {sid} in {cwd} is a newer record version than it reads")
        return None

    def aggregate(self, cwd, work_class=None, since=None):
        """bale stats --json, the whole corpus or narrowed: to one work
        class, and to the sessions packed on or after the day since (an
        ISO date; bale refuses a timestamp). The window bale says it
        applied is held to the one asked for."""
        if since is not None:
            dt.date.fromisoformat(since)
        agg = self.run("stats", cwd, work_class=work_class, since=since)
        filters = self.key(agg, "stats", "filters")
        applied = self.key(filters, "stats", "filters.since")
        if applied != since:
            raise BaleError("output", f"bale stats in {cwd} reports the window since {applied!r}, "
                                      f"not the {since!r} the office asked for")
        return agg


# --- plain data from a dossier ---------------------------------------------------

def session_view(rd, d):
    """What the renderings show about one session, from its dossier."""
    rec = rd.key(d, "dossier", "record")
    lineage = rd.key(d, "dossier", "lineage")
    closure = rd.key(rec, "dossier", "record.closure")
    view = {
        "sid": rd.key(d, "dossier", "session_id"),
        "created": rd.key(rec, "dossier", "record.created_at"),
        "updated": rd.key(rec, "dossier", "record.updated_at"),
        "outcome": rd.key(rec, "dossier", "record.outcome"),
        "work_class": rd.key(rec, "dossier", "record.work_class"),
        "in_flight": rd.key(rec, "dossier", "record.in_flight"),
        "read_only": rd.key(rec, "dossier", "record.read_only"),
        "unlock_reason": rd.key(closure, "dossier", "record.closure.unlock_reason") if closure else None,
        "superseded_by": rd.key(lineage, "dossier", "lineage.superseded_by"),
        "attempts": [],
    }
    for a in rd.key(d, "dossier", "attempts") or []:
        validation = rd.key(a, "dossier", "attempts[].validation")
        clar = rd.key(a, "dossier", "attempts[].clarification")
        link = rd.key(a, "dossier", "attempts[].linkage")
        checks = []
        if validation:
            for c in rd.key(validation, "dossier", "attempts[].validation.checks") or []:
                checks.append({
                    "check": rd.key(c, "dossier", "attempts[].validation.checks[].check"),
                    "claim": rd.key(c, "dossier", "attempts[].validation.checks[].claim"),
                    "verdict": rd.key(c, "dossier", "attempts[].validation.checks[].verdict"),
                    "agreement": rd.key(c, "dossier", "attempts[].validation.checks[].agreement"),
                })
        view["attempts"].append({
            "at": rd.key(a, "dossier", "attempts[].at"),
            "command": rd.key(a, "dossier", "attempts[].command"),
            "outcome": rd.key(a, "dossier", "attempts[].outcome"),
            "change_paths": rd.key(a, "dossier", "attempts[].change_paths") or [],
            "state": rd.key(validation, "dossier", "attempts[].validation.state") if validation else None,
            "checks": checks,
            "rounds": rd.key(clar, "dossier", "attempts[].clarification.rounds") if clar else None,
            "linkage": (rd.key(link, "dossier", "attempts[].linkage.kind"),
                        rd.key(link, "dossier", "attempts[].linkage.point")) if link else None,
        })
    return view


def applied_latest(rd, cwd):
    """The latest session bale applied in a repo (status's light pointer at
    its applied history), or None when none has landed there: what the
    home screen says last landed on a project (0.22.0)."""
    applied = rd.key(rd.status(cwd), "status", "applied")
    return rd.key(applied, "status", "applied.latest") if applied else None


def bundle_stems(rd, d):
    """The stems of the planner bundles a session was opened from, as its
    dossier records them on its attempts (attempts[].bundle.stem), so
    whether a bundle was opened is read, never guessed (0.22.0)."""
    return [stem for stem, _ in bundle_records(rd, d)]


SHA256_RE = oh.LazyPattern(r"[0-9a-f]{64}")


def bundle_records(rd, d):
    """[(stem, brief_sha256)] of the planner bundles a session was opened
    from, as its dossier records them on its attempts
    (attempts[].bundle.stem and .brief_sha256, 0.57.0): the stem as the
    file was named, and the sha256 of the brief the bundle carried, the
    one its bundle.json names (members.brief.sha256). The hash is None
    when the record holds null (a bundle with no brief) or no such key
    (a bale that did not record it), said under OFFICE_DEBUG; the
    caller then has the stem alone, as before 0.57.0."""
    out = []
    for a in rd.key(d, "dossier", "attempts") or []:
        blk = rd.key(a, "dossier", "attempts[].bundle")
        if not blk:
            continue
        stem = rd.key(blk, "dossier", "attempts[].bundle.stem")
        if not stem:
            continue
        try:
            sha = rd.key(blk, "dossier", "attempts[].bundle.brief_sha256")
        except BaleError as exc:
            if exc.kind != "key":
                raise
            debug(f"the record of the bundle {stem} holds no brief hash ({exc}); it is matched by its stem alone")
            sha = None
        out.append((str(stem), sha if isinstance(sha, str) and SHA256_RE.fullmatch(sha) else None))
    return out


def bundle_brief_sha256(bundle):
    """The sha256 a planner bundle's bundle.json names for its brief
    (members.brief.sha256, 0.57.0), the hash bale records on the session
    opened from it; None when the bundle is not a file here, carries no
    brief, names no well-formed hash, or cannot be read (said under
    OFFICE_DEBUG). bale's bundle format is bale's: the office reads the
    hash bale wrote and never computes its own."""
    import json
    import tarfile
    p = pathlib.Path(bundle) if bundle else None
    if p is None or not p.is_file():
        return None
    try:
        with tarfile.open(p) as t:
            member = t.extractfile("bundle.json")
            meta = json.loads(member.read().decode("utf-8")) if member else {}
    except (OSError, KeyError, tarfile.TarError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        debug(f"could not read the brief hash of {p}: {exc}")
        return None
    brief = (meta.get("members") or {}).get("brief") if isinstance(meta, dict) else None
    sha = brief.get("sha256") if isinstance(brief, dict) else None
    return sha if isinstance(sha, str) and SHA256_RE.fullmatch(sha) else None


def outcome_word(view):
    """The blueprint's words for where a session stands: applied, held,
    bailed, open, superseded; anything else bale says, as bale says it."""
    if view["superseded_by"]:
        return f"superseded by {view['superseded_by']}"
    o = view["outcome"]
    if view["in_flight"]:
        return "held" if o == "held" else ("open" if o in ("opened", "packed") else f"open ({o})")
    if o == "bailout":
        return "bailed"
    if o == "unlocked":
        reason = view["unlock_reason"]
        return "closed read-only" if reason == "closed-read-only" else f"unlocked ({reason or 'no reason recorded'})"
    return o


def response_attempts(view):
    return [a for a in view["attempts"] if a["command"] in RESPONSE_COMMANDS]


def day(stamp):
    return (stamp or "")[:10] or "?"


def parse_stamp(stamp):
    return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def describe_age(then, now):
    secs = max(0, int((now - then).total_seconds()))
    if secs < 3600:
        return f"{secs // 60}m"
    if secs < 86400:
        return f"{secs // 3600}h"
    return f"{secs // 86400}d"


def rate(num, den, bale_rate=None):
    """`0.89 (16 of 18)`, or `- (0 of 0)` on a zero denominator. When
    bale computed the rate, bale's number is the one shown."""
    if not den:
        return f"- ({num} of {den})"
    value = bale_rate if bale_rate is not None else num / den
    return f"{value:.2f} ({num} of {den})"


# --- projects and folders ----------------------------------------------------------

def office_projects(office_root):
    """The office's [projects] entries (None when it has no table)."""
    return oh.read_projects(oh.read_toml(pathlib.Path(office_root) / "floor-plan" / "manifest.toml"))


def no_projects_line(projects):
    if projects is None:
        return ("this office scopes no projects: its floor plan has no [projects] table "
                "(office projects add NAME PATH)")
    return "this office scopes no projects: its [projects] table lists none (office projects add NAME PATH)"


def readable(project):
    """Where the project is read: its directory on this machine, or an
    office_host.Place for a project that declares a host (every bale and
    git read then runs through its shell, in its path, after one reach
    check per host and command). Raises BaleError saying why it cannot
    be read."""
    if project["problem"]:
        raise BaleError("path", project["problem"])
    if project.get("host"):
        return ohost.place_of(project)
    if not project["resolved"].is_dir():
        raise BaleError("path", f"no such directory on this machine: {project['resolved']}")
    return project["resolved"]


def rendered(project):
    """readable() for a rendering (0.41.0): a project marked paused (office
    projects set NAME --paused) is read for nothing, and raises BaleError
    of kind paused whose words are the one line the rendering says in the
    place its "not read" line would go. The verbs that carry work
    already out (land, deliver, probe) read with readable(), and so still
    reach it."""
    if project.get("paused") and not project.get("problem"):
        raise BaleError("paused", oh.paused_line(project["name"]))
    return readable(project)


def unread_line(label, exc):
    """A project a rendering could not read, in one line: the paused line
    for a paused one, else `LABEL: not read: WHY` (0.53.0: one spelling in
    every rendering, office sessions' own; it was `cannot read`
    elsewhere)."""
    return str(exc) if getattr(exc, "kind", None) == "paused" else f"{label}: not read: {exc}"


def hosted_project(project):
    """Whether a [projects] entry declares a host."""
    return bool(project and project.get("host"))


def git_lines(cwd, *args, timeout=120):
    """git's stdout where a project is, here or through its shell; None
    when git refuses (not a repo, no such commit), as the digest reads
    it. A host that does not answer is a BaleError."""
    try:
        run = ohost.run_in(cwd, ["git", *args], timeout)
    except ohost.HostError as exc:
        raise BaleError(exc.kind if exc.kind in ("unreachable", "path") else "refused", str(exc))
    if run.returncode != 0:
        debug(f"git {' '.join(args)} in {cwd}: {run.stderr.strip()}")
        return None
    return run.stdout


def select(projects, name):
    if name is None:
        return projects
    chosen = [p for p in projects if p["name"] == name]
    if not chosen:
        raise oh.HelperError(f"no project named {name} in this office's [projects] "
                             f"(it lists: {', '.join(p['name'] for p in projects) or 'none'})")
    return chosen


def folders_naming(office_root):
    """sid -> the folders (desk/X, filing-cabinet/X) whose Sessions
    section names it."""
    out = {}
    for space in ("desk", "filing-cabinet"):
        for md in sorted((pathlib.Path(office_root) / space).glob("*/folder.md")):
            try:
                lines = oh.folder_session_lines(md)
            except (OSError, UnicodeDecodeError) as exc:
                # The desk names it under Cannot be read; one bad file
                # never takes the rest of the rendering down.
                debug(f"{space}/{md.parent.name}/folder.md cannot be read, so no session maps to it: {exc}")
                continue
            for sid, _ in lines:
                out.setdefault(sid, []).append(f"{space}/{md.parent.name}")
    return out


# --- the renderings ---------------------------------------------------------------------

def office_registry(office_root):
    """The office's own repo when bale keeps a registry there (a .bale/
    directory; an existence check, nothing inside is read), else None.
    An office nobody has packed a session from has none, and nothing in
    it can be open."""
    root = pathlib.Path(office_root)
    if (root / ".bale").is_dir():
        return root
    debug(f"no .bale/ in the office at {root}: bale keeps no registry there, so no session of its own is open")
    return None


# The office's own registry is read with the projects' and labeled so.
OFFICE_LABEL = "this office"

# Two read-only sittings open on one folder (0.43.0; the gaps of
# 2026-10-28, A13): a successor sent while its predecessor stayed open, which
# the occupant went back to. Each screen says it of every sitting on the
# folder but the newest, so the key that ends the right one is plain.
OLDER_SITTING_WORDS = "an older sitting on this folder, probably over"


def older_sittings(office_root, sittings):
    """The ids among sittings ((sid, folders) pairs: the read-only sittings
    open, each with the folders that record it) that are not the newest
    open on a folder they share. The newest is the one the folder's
    Sessions section records last (office start appends each); a folder
    that cannot be read orders by id, whose date comes first. A sitting
    alone on its folders is never older."""
    by_folder = {}
    for sid, folders in sittings:
        for rel in folders:
            if sid not in by_folder.setdefault(rel, []):
                by_folder[rel].append(sid)
    older = set()
    for rel, sids in by_folder.items():
        if len(sids) < 2:
            continue
        try:
            order = [s for s, _ in oh.folder_session_lines(pathlib.Path(office_root) / rel / "folder.md")]
        except (OSError, UnicodeDecodeError) as exc:
            debug(f"{rel}/folder.md cannot be read to order its sittings, so they are ordered by id: {exc}")
            order = []
        newest = max(sids, key=lambda s: (order.index(s) if s in order else -1, s))
        older.update(s for s in sids if s != newest)
    return older


def standing_words(office_root, folders, sid=None):
    """What a screen says of where a sitting stands (0.43.0): the standing
    filed on the first of its folders that has one, in office_standing's
    words, or None when none has."""
    import office_standing as ostand
    for rel in folders:
        st = ostand.folder_standing(office_root, rel)
        if st is not None:
            return ostand.words(st, sid)
    return None


def prep_standing_words(office_root, sid):
    """What a screen says of where a meeting's prep stands (0.55.0): the
    standing filed for it in the calendar (office_standing.prep_standing),
    in office_standing's words, or None."""
    import office_standing as ostand
    st = ostand.prep_standing(office_root, sid)
    return ostand.words(st, sid) if st is not None else None


def in_flight(rd, office_root, now=None):
    """(lines, unreadable, flying): one line per open session in the
    projects the office scopes and in the office's own repo, each mapped
    to the folder that names its sid; flying is the set of folders
    (space/name) some open session is mapped to."""
    import office_sort as osort
    import office_meeting as om
    now = now or dt.datetime.now(dt.timezone.utc)
    projects = office_projects(office_root)
    naming = folders_naming(office_root)
    sources = [(p["name"], p) for p in projects or []]
    own = office_registry(office_root)
    if own is not None:
        sources.insert(0, (OFFICE_LABEL, {"problem": None, "resolved": own}))
    lines, bad, open_count, flying = [], 0, 0, set()
    # A sitting out under a doctrine that is not the install's says so on
    # its own line (0.33.0), read from its folder's Sessions line.
    doctrines = Doctrines(office_root)
    if not projects:
        lines.append(no_projects_line(projects))
    # Each read-only sitting's line, by its index, so the line of every
    # sitting but the newest on a folder says so once all are read (0.43.0).
    sitting_lines = []
    for label, p in sources:
        try:
            cwd = rendered(p)
            opened = rd.open_sessions(cwd)
            rd.prefetch(cwd, [("dossier", {"sid": sid}) for sid, _ in opened])
            for sid, read_only in opened:
                open_count += 1
                folders = naming.get(sid, [])
                flying.update(folders)
                d = rd.dossier(cwd, sid)
                # What ends a sitting the office sent out; never on the
                # Next line, since nothing in the office knows when a
                # sitting is over. A sitting no folder records is not
                # the office's to end.
                prep = om.prep_of(office_root, sid) if label == OFFICE_LABEL and read_only else None
                ends = f" (office land {sid} when the sitting is over)" if read_only and (folders or prep) else ""
                older = doctrines.older(sid) if read_only and folders else None
                if older:
                    ends += f"; {older}"
                # A prep's record line stamps its doctrine (0.43.0), compared
                # as a folder's sitting's is.
                if prep and prep.get("doctrine"):
                    older = doctrines.older_stamp(prep["doctrine"])
                    if older:
                        ends += f"; {older}"
                # Where the sitting stands (0.43.0), from its folder's page;
                # a prep's (0.55.0) from its page in the calendar.
                stands = (standing_words(office_root, folders, sid) if read_only and folders else
                          prep_standing_words(office_root, sid) if prep else None)
                if stands:
                    ends += f"; {stands}"
                # The standalone sort belongs to no folder: it is the
                # in-tray's session (0.20.0); a meeting's prep is the
                # calendar's (0.26.0).
                target = ", ".join(folders) or ("the in-tray (the standalone sort)"
                                                if label == OFFICE_LABEL and osort.is_sort_sid(sid) else
                                                f"the meeting {prep['title']} ({prep['date']} {prep['time']}), its prep"
                                                if prep else "no folder")
                if read_only and folders:
                    sitting_lines.append((len(lines), sid, folders))
                if d is None:
                    lines.append(f"{label}: {sid} open, with no record in bale's telemetry yet -> {target}{ends}")
                    continue
                v = session_view(rd, d)
                state = "read-only" if read_only else outcome_word(v)
                age = describe_age(parse_stamp(v["created"]), now)
                lines.append(f"{label}: {sid} {state}, opened {age} ago -> {target}{ends}")
        except BaleError as exc:
            if exc.kind == "paused":
                lines.append(unread_line(label, exc))
                continue
            bad += 1
            lines.append(unread_line(label, exc))
    older = older_sittings(office_root, [(sid, folders) for _, sid, folders in sitting_lines])
    for at, sid, _ in sitting_lines:
        if sid in older:
            lines[at] += f"; {OLDER_SITTING_WORDS}"
    if open_count == 0 and bad == 0 and projects:
        lines.append(f"none: no session is open in the {len(projects)} project(s) this office scopes"
                     + (", or in the office itself" if own is not None else ""))
    elif open_count == 0 and bad == 0 and own is not None:
        lines.append("none: no session is open in the office itself")
    return lines, bad, flying


def render_in_flight(rd, office_root, now=None):
    """(lines, unreadable projects): the walk-in's In flight section.
    Short on purpose."""
    lines, bad, _ = in_flight(rd, office_root, now)
    return lines, bad


# --- the one-writer rule ---------------------------------------------------------

def forecast_holds(entry, target):
    """Does a forecast entry hold the target path? It does when it is
    the target or a directory above it (the whole tree included). An
    entry inside the target, a session scoped to one folder, does not:
    it cannot mint a number, and blocking every open for the life of a
    folder's session would be friction, not safety."""
    entry = entry.strip().strip("/")
    target = target.strip().strip("/")
    return entry in ("", ".") or entry == target or target.startswith(entry + "/")


def writers_holding(rd, office_root, targets):
    """[(sid, target, forecast)] for each session open in the office's own
    registry whose forecast holds a target: the sessions a script that
    mints a number must not run beside (the blueprint's section 5.4).
    [] when the office has no registry. Raises BaleError when it has one
    that cannot be read."""
    own = office_registry(office_root)
    if own is None:
        return []
    st = rd.status(own)
    sids = rd.key(st, "status", "sessions") or []
    scopes = rd.key(st, "status", "scopes") or {}
    out = []
    for sid in sids:
        forecast = scopes.get(sid) or []
        for target in targets:
            if any(forecast_holds(e, target) for e in forecast):
                out.append((sid, target, forecast))
                break
    return out


# --- the desk ----------------------------------------------------------------------
#
# What `office desk` renders (the blueprint's section 2.3), in order: In
# flight, Ready, Parked, Candidates, then orphaned riders and pending desk
# moves, read from the drafting table. Every folder on the desk lands in
# exactly one group, and a folder whose facts the desk cannot place is
# shown with the reason, never dropped. A gate on a blueprint, an agenda
# item or a ruling resolves through the drafting table's one reader
# (office_drafting.Table.gate).

FOLDER_TEMPLATE = INSTALL / "templates" / "folder.md"
SIZE_RANK = {size: n for n, size in enumerate(oh.SIZES)}
SUCCESSOR_RE = oh.LazyPattern(r"folders?\s+([\d,\s]+)")


def folder_line(f, next_first=None):
    """`folder N  NAME  next: ...  (sessions: N)`, the name alone for a
    folder with no number, and its size when it has one. next_first, when
    given, is said before the folder's own Next (0.42.0: a review that asked
    for changes)."""
    try:
        nxt, count = oh.folder_summary(f["path"], FOLDER_TEMPLATE)
    except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
        return f"{f['name']}  (folder.md could not be read: {exc})"
    if next_first:
        nxt = f"{next_first}; then {nxt}"
    head = f"folder {f['number']}  {f['name']}" if f.get("number") else f["name"]
    lane = (f["fields"].get("lane") or [""])[0]
    head += f" ({oh.folder_project_words(lane, floor_plan_names(f))})"
    size = (f["fields"].get("size") or [None])[0]
    return f"{head}  next: {nxt}  (sessions: {count})" + (f"  {size}" if size else "")


_NAMES_BY_ROOT = {}


def floor_plan_names(f):
    """The project names of the office a folder sits in (its folder.md is
    ROOT/SPACE/NAME/folder.md), read once per office per process while
    its floor plan is unchanged, for the desk's line naming its project
    (0.49.0)."""
    root = pathlib.Path(f["path"]).parent.parent.parent
    try:
        stamp = (root / oh.OFFICE_MANIFEST_REL).stat().st_mtime_ns
    except OSError:
        stamp = None
    key = (str(root), stamp)
    if key not in _NAMES_BY_ROOT:
        _NAMES_BY_ROOT[key] = oh.office_project_names(root)
    return _NAMES_BY_ROOT[key]


def successors(f):
    """The folder numbers an absorbed or split folder's last state line
    points at."""
    last = f.get("last_state")
    m = SUCCESSOR_RE.search(last[2]) if last else None
    return [int(n) for n in re.findall(r"\d+", m.group(1))] if m else []


def gate_state(gate, by_number, seen=(), table=None):
    """Where a gate stands: (state, words, cleared) where state is met,
    wait or error; words name the gate's own status; cleared is the day a
    met gate cleared, when the record says (a folder's History, a
    blueprint's close report, an agenda item's disposal, a ruling's
    date). A blueprint, agenda or ruling gate reads the drafting table."""
    kind, _, ref = gate.partition(" ")
    if kind != "folder":
        if table is None:
            return "error", f"{gate}: the drafting table was not read", None
        try:
            return table.gate(gate)
        except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
            return "error", f"{gate}: the drafting table could not be read ({exc})", None
    n = int(ref)  # read_gates normalized it: `folder N`
    if n in seen:
        return "error", f"{gate} leads back to the folder that waits on it", None
    same = by_number.get(n, [])
    if not same:
        return "error", f"{gate} names no folder on the desk or in the filing cabinet", None
    if len(same) > 1:
        return "error", f"{gate} is minted twice ({', '.join(x['rel'] for x in same)})", None
    t = same[0]
    title = t.get("title") or t["name"]
    status = t["status"]
    last = t["last_state"]
    if status == "done":
        return "met", f"{gate} done", last[0] if last and last[1] == "done" else None
    if status is None and t["space"] == "filing-cabinet":
        return "met", f"{gate} filed", None
    if status in ("absorbed", "split"):
        nexts = successors(t)
        if not nexts:
            return "error", f"{gate} was {status}, and its History names no successor", None
        states = [gate_state(f"folder {m}", by_number, seen + (n,), table) for m in nexts]
        for st in states:
            if st[0] != "met":
                return st[0], f"{gate} ({status} into " + ", ".join(f"folder {m}" for m in nexts) + f"): {st[1]}", None
        days = [st[2] for st in states if st[2]]
        return "met", f"{gate} {status}, and " + ", ".join(f"folder {m}" for m in nexts) + " done", max(days) if days else None
    if status == "retired":
        why = last[2] if last and last[1] == "retired" else "no reason recorded"
        return "wait", f"{gate} (retired: {why}); it will not clear by itself", None
    return "wait", f"{gate} ({status or 'no status line'}): {title}", None


def after_cycles(desk, by_number):
    """Cycles among the after gates of desk folders, each as the list of
    numbers around it."""
    graph = {}
    for f in desk:
        if f["problem"] or not f.get("number"):
            continue
        graph[f["number"]] = [int(g.split()[1]) for g in read_gates(f, "after", [])
                              if g.startswith("folder ")
                              and len(by_number.get(int(g.split()[1]), [])) == 1
                              and by_number[int(g.split()[1])][0]["space"] == "desk"]
    cycles, state = [], {}

    def visit(n, path):
        state[n] = "open"
        for m in graph.get(n, []):
            if state.get(m) == "open":
                cycles.append(path[path.index(m):] + [m])
            elif m not in state:
                visit(m, path + [m])
        state[n] = "done"

    for n in sorted(graph):
        if n not in state:
            visit(n, [n])
    return cycles


def ready_order(ready, errors):
    """Ready folders in order: by `serializes after` (when both are
    ready, the one named goes first), then size, small first, then
    number. A cycle among them is an error line, and its folders follow
    in size and number order."""
    def key(f):
        size = (f["fields"].get("size") or [None])[0]
        return (SIZE_RANK.get(size, len(SIZE_RANK)), f.get("number") or float("inf"), f["name"])
    by_n = {f["number"]: f for f in ready if f.get("number")}
    before = {id(f): set() for f in ready}
    for f in ready:
        for g in read_gates(f, "serializes after", []):
            kind, _, ref = g.partition(" ")
            if kind == "folder" and int(ref) in by_n and by_n[int(ref)] is not f:
                before[id(f)].add(id(by_n[int(ref)]))
    out, left = [], sorted(ready, key=key)
    while left:
        free = [f for f in left if not (before[id(f)] & {id(x) for x in left})]
        if not free:
            errors.append("ERROR: `serializes after` gates in a cycle among ready folders: "
                          + ", ".join(oh.cite(f) for f in left) + "; shown in size and number order")
            out += left
            break
        out.append(free[0])
        left.remove(free[0])
    return out


def read_gates(f, key, errors):
    """A folder's gates of one kind, normalized as office open writes
    them; a line that does not read as a gate is an error line, never a
    guess."""
    out = []
    for g in f["fields"].get(key, []):
        try:
            out.append(oh.normalize_field(key, g))
        except oh.HelperError as exc:
            errors.append(f"ERROR: {oh.cite(f)}: `{key}: {g}` does not read: {exc}")
    return out


def classify_desk(folders, flying, since, table=None):
    """The desk's groups from its folders: a dict of lists, plus the
    error lines the Ready group carries. table, the drafting table's
    reader, resolves the gates that are not folders and gives the
    orphaned riders and the pending desk moves."""
    import office_drafting as od
    by_number = oh.folders_by_number(folders)
    desk = [f for f in folders if f["space"] == "desk"]
    groups = {"flying": [], "open": [], "ready": [], "parked": {}, "candidates": [], "no_status": [],
              "misplaced": [], "unreadable": [], "ready_errors": [], "cleared": {},
              "orphans": [], "moves": (0, "", []), "drafting_error": None}
    if table is not None:
        try:
            groups["orphans"] = table.orphans()
            groups["moves"] = od.moves_summary(table.root)
        except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
            groups["drafting_error"] = f"the drafting table could not be read: {exc}"
    cyclic = {}
    for cycle in after_cycles(desk, by_number):
        words = "ERROR: after gates in a cycle: " + " -> ".join(f"folder {n}" for n in cycle)
        for n in cycle[:-1]:
            cyclic.setdefault(n, words)

    def park(heading, f, also=()):
        groups["parked"].setdefault(heading, []).append((f, [a for a in also if a != heading]))

    for f in desk:
        if f["problem"]:
            groups["unreadable"].append(f)
            continue
        if f["rel"] in flying:
            groups["flying"].append(f)
            continue
        status = f["status"]
        if status is None:
            groups["no_status"].append(f)
        elif status == "open":
            groups["open"].append(f)
        elif status == "candidate":
            groups["candidates"].append(f)
        elif status != "queued":
            groups["misplaced"].append(f)
        elif f.get("number") in cyclic:
            park(cyclic[f["number"]], f)
        else:
            waits, cleared = [], []
            me = (f["number"],) if f.get("number") else ()
            gates = {key: read_gates(f, key, waits) for key in ("after", "consumer", "serializes after")}
            for g in gates["after"]:
                state, words, day = gate_state(g, by_number, me, table)
                if state == "met":
                    if day and day >= since:
                        cleared.append(f"gate cleared: {words} {day}")
                elif state == "error":
                    waits.append(f"ERROR: {oh.cite(f)}: after {words}")
                else:
                    waits.append(f"waiting for {words}")
            for g in gates["consumer"]:
                state, words, _ = gate_state(g, by_number, me, table)
                if state == "error":
                    waits.append(f"ERROR: {oh.cite(f)}: consumer {words}")
                else:
                    waits.append(f"parked for its consumer, {words}")
            for g in gates["serializes after"]:
                kind, _, ref = g.partition(" ")
                same = by_number.get(int(ref), [])
                if not same:
                    waits.append(f"ERROR: {oh.cite(f)}: serializes after {g}, which names no folder")
                elif same[0]["status"] == "open" or same[0]["rel"] in flying:
                    waits.append(f"waiting for {g} to close: it is open, and this one serializes after it, "
                                 "never beside it")
            if waits:
                park(waits[0], f, waits[1:])
            else:
                groups["ready"].append(f)
                if cleared:
                    groups["cleared"][f["rel"]] = cleared
    groups["ready"] = ready_order(groups["ready"], groups["ready_errors"])
    return groups


def desk_folder_line(f, groups):
    """folder_line on the desk and the walk-in (0.42.0): with the reviews
    on the folder's branches after it, `[review #12 approved]`, and a
    review that asked for changes named first in its next."""
    import office_review as orev
    rows = (groups.get("reviews_by_rel") or {}).get(f["rel"])
    if not rows:
        return folder_line(f)
    asked = orev.changes_requested(rows)
    first = f"answer review #{asked['number']}'s requested changes on {asked['branch']}" if asked else None
    return f"{folder_line(f, first)}  [{orev.folder_words(rows)}]"


def read_reviews(office_root, folders, groups):
    """The reviews on the branches this office delivered (0.42.0), read
    through gh into groups: reviews (per project) and reviews_by_rel. A
    rendering, recomputed on every run and cached nowhere; what cannot be
    read is a line in its project's place, never a refusal."""
    import office_review as orev
    try:
        groups["reviews"] = orev.office_reviews(office_root, folders)
    except (OSError, oh.HelperError, orev.GhError) as exc:
        debug(f"the reviews could not be read: {exc}")
        groups["reviews"] = []
    groups["reviews_by_rel"] = orev.by_folder(groups["reviews"])


def desk_standing_lines(f, indent):
    """office desk's line under a folder's next move (0.43.0): where the
    folder's sitting stood when it last filed a standing, whose, and as of
    when; [] when the folder has none. A folder whose sitting is open says
    it on its In flight line instead."""
    import office_standing as ostand
    st = ostand.read_page(pathlib.Path(f["path"]).parent / ostand.PAGE) if f.get("path") else None
    if st is None:
        return []
    return [f"{indent}standing, {st['sitting']}'s: {ostand.words(st)}"]


def desk_lines(groups, flight_lines, walk_in=False, ready_limit=3):
    """The groups as the screen shows them. Full, for office desk; for
    the walk-in, In flight and the first ready folders. office desk shows a
    folder's standing under its line (0.43.0)."""
    import office_review as orev
    folder_line = lambda f: desk_folder_line(f, groups)  # noqa: E731  (0.42.0: the reviews on every line)
    stands = (lambda f, indent: []) if walk_in else desk_standing_lines  # noqa: E731
    lines = ["In flight:"]
    lines += [f"  {l}" for l in flight_lines]
    for f in groups["open"]:
        lines += [f"  {folder_line(f)}  [{open_words(f, groups)}]", *stands(f, "    ")]
    # The reviews on the branches the office delivered (0.42.0), after
    # what is in flight, one line per project.
    reviews = orev.review_lines(groups.get("reviews"))
    if reviews:
        lines += [""] + reviews
    parked = sum(len(v) for v in groups["parked"].values())
    errors = sum(1 for h in groups["parked"] if h.startswith("ERROR")) + len(groups["ready_errors"])
    on_desk = (len(groups["flying"]) + len(groups["open"]) + len(groups["ready"]) + parked + len(groups["candidates"])
               + len(groups["no_status"]) + len(groups["misplaced"]) + len(groups["unreadable"]))

    def ready_block(items):
        out = []
        for f in items:
            out.append(f"  {folder_line(f)}")
            out += stands(f, "    ")
            out += [f"    {c}" for c in groups["cleared"].get(f["rel"], [])]
        return out

    if walk_in:
        counts = [f"{len(groups['ready'])} ready", f"{parked} parked",
                  f"{len(groups['candidates'])} candidate(s)"]
        if groups["flying"] or groups["open"]:
            counts.insert(0, f"{len(groups['flying']) + len(groups['open'])} open")
        if groups["no_status"]:
            counts.append(f"{len(groups['no_status'])} with no status line")
        lines += ["", "On the desk: " + ", ".join(counts) + " (office desk shows every group)"]
        tray_line = in_tray_walk_in_line(groups)
        if not on_desk:
            lines.append("  the desk is clear")
        elif groups["ready"]:
            lines += ready_block(groups["ready"][:ready_limit])
            if len(groups["ready"]) > ready_limit:
                lines.append(f"  and {len(groups['ready']) - ready_limit} more ready")
        else:
            lines.append("  nothing is ready")
        if errors:
            lines.append(f"  {errors} gate error(s): office desk names them")
        lines += drafting_lines(groups, walk_in=True)
        if tray_line:
            lines += ["", tray_line]
        return lines
    if not on_desk:
        extra = drafting_lines(groups)
        return lines + ["", "the desk is clear"] + in_tray_lines(groups) + extra
    if groups["ready"] or groups["ready_errors"]:
        lines += ["", "Ready:"] + [f"  {e}" for e in groups["ready_errors"]] + ready_block(groups["ready"])
    if groups["parked"]:
        lines += ["", "Parked:"]
        for heading in sorted(groups["parked"], key=lambda h: (not h.startswith("ERROR"), h)):
            lines.append(f"  {heading}")
            for f, also in groups["parked"][heading]:
                lines.append(f"    {folder_line(f)}")
                lines += stands(f, "      ")
                lines += [f"      and {a}" for a in also]
    if groups["candidates"]:
        lines += ["", "Candidates:"]
        for f in groups["candidates"]:
            lines += [f"  {folder_line(f)}", *stands(f, "    ")]
    lines += in_tray_lines(groups)
    lines += drafting_lines(groups)
    if groups["no_status"]:
        lines += ["", "No status line (folders from before the field block; the desk cannot order them):"]
        lines += [f"  {folder_line(f)}" for f in groups["no_status"]]
    if groups["misplaced"]:
        lines += ["", "On the desk with a filing-cabinet status (office status names each):"]
        lines += [f"  {folder_line(f)}  [status {f['status']}]" for f in groups["misplaced"]]
    if groups["unreadable"]:
        lines += ["", "Cannot be read:"] + [f"  {f['name']}  ({f['problem']})" for f in groups["unreadable"]]
    return lines


def open_words(f, groups):
    """What an open folder's desk line says in its brackets (0.41.0): its
    merge job waiting for a session, or its work landed and not delivered,
    or that no session is in flight for it."""
    m = (groups.get("merge_by_rel") or {}).get(f["rel"])
    if m is not None and not m["landed"]:
        return f"{job_waiting_words(m['job'])}; {job_start_line(f, m['job'])}"
    u = (groups.get("undelivered_by_rel") or {}).get(f["rel"])
    if u is not None:
        return f"landed {u['sid']} on {u['day']}, not delivered; office deliver {folder_key(f)}"
    return "open, no session in flight"


def in_tray_lines(groups):
    """office desk's group after the candidates: each unsorted drop's page
    name, its project or `no project`, and its first line (0.19.0)."""
    drops = groups.get("drops") or []
    if not drops:
        return []
    return ["", "Unsorted drops (in-tray/; office start --drop in-tray/PAGE sends one out):"] + \
        [f"  {d['name']}  ({d['project'] or 'no project'})  {d['heading']}" for d in drops]


def in_tray_walk_in_line(groups):
    """The walk-in's one line when the in-tray holds unsorted drops: how
    many, and the oldest's age in days; None when it holds none."""
    drops = groups.get("drops") or []
    if not drops:
        return None
    age = groups.get("drops_oldest_age")
    old = "" if age is None else (", the oldest dropped today" if age <= 0 else
                                  f", the oldest {age} day{'s' if age != 1 else ''} old")
    return f"In-tray: {len(drops)} unsorted drop(s){old} (office desk lists them)"


def drafting_lines(groups, walk_in=False):
    """The desk's last two groups, orphaned riders and pending desk
    moves; on the walk-in, one line each, and nothing when there are
    none."""
    out = []
    count, sources, errors = groups.get("moves", (0, "", []))
    orphans = groups.get("orphans", [])
    if groups.get("drafting_error"):
        out += ["", f"Drafting table: {groups['drafting_error']}"] if not walk_in else \
            [f"  {groups['drafting_error']}"]
    if walk_in:
        if count:
            out.append(f"  {count} desk move(s) pending ({sources}): office moves applies them")
        if errors:
            out.append(f"  {len(errors)} line(s) of drafting-table/moves.md do not read: office moves names them")
        if orphans:
            out.append(f"  {len(orphans)} orphaned rider(s), in a closed folder and never consumed: "
                       "office riders --orphans")
        return out
    if orphans:
        out += ["", "Orphaned riders (in a closed folder, never consumed):"]
        out += [f"  rider {r['number']}  {r['title']}  ({r['home']}, {r['status'] or 'no status'})" for r in orphans]
    if count or errors:
        out += ["", f"Pending desk moves ({count}, {sources or 'none readable'}; office moves applies them):"]
        out += [f"  ERROR: {e}" for e in errors]
    return out


def render_desk(rd, office_root, today, since=None, walk_in=False, now=None, groups_out=None, blueprint=None,
                machine_file=None):
    """(lines, unreadable projects): office desk, or the walk-in's two
    sections. since is the day of the previous walk-in (default today):
    a ready folder whose gate cleared on or after it says so. groups_out,
    a dict when given, receives the desk's groups (the Next line reads
    them, so the walk-in classifies the desk once). office desk given
    machine_file (0.55.0) ends with the asks out and each ask's record
    left without its tray (ask_desk_lines)."""
    import office_drafting as od
    import office_drop as odrop
    import office_sort as osort
    flight, bad, flying = in_flight(rd, office_root, now)
    table = od.Table(office_root)
    folders = oh.read_folders(office_root)
    if blueprint is not None:
        return blueprint_desk(table, folders, flying, since or today, blueprint, flight), bad
    groups = classify_desk(folders, flying, since or today, table)
    # What landed and is not delivered, and the merge jobs waiting (0.41.0):
    # read once here, for the desk's lines, the Next line and the home screen.
    try:
        undelivered, merges, unread = waiting_on_delivery(office_root, folders)
    except (OSError, oh.HelperError) as exc:
        debug(f"what is landed and not delivered could not be read for the desk: {exc}")
        undelivered, merges, unread = [], [], []
    for line in unread:
        debug(f"what is landed and not delivered on it could not be read: {line}")
    groups["undelivered"], groups["merges"] = undelivered, merges
    groups["undelivered_by_rel"] = {u["folder"]["rel"]: u for u in undelivered}
    groups["merge_by_rel"] = {m["folder"]["rel"]: m for m in merges}
    read_reviews(office_root, folders, groups)
    # The in-tray's unsorted drops, oldest first (0.19.0): the desk lists
    # them, the walk-in counts them, and the Next line may name one.
    try:
        groups["drops"] = odrop.unsorted(office_root)
        groups["drops_oldest_age"] = odrop.age_days(groups["drops"][0], today) if groups["drops"] else None
    except (OSError, oh.HelperError, ValueError) as exc:
        debug(f"the in-tray could not be read for the desk: {exc}")
        groups["drops"], groups["drops_oldest_age"] = [], None
    # A sorted drop still in the in-tray is a desk move (0.20.0): counted
    # with the moves page's, ahead of them, as office moves applies them.
    try:
        waiting = odrop.sorted_waiting(office_root)
    except (OSError, oh.HelperError, ValueError) as exc:
        debug(f"the in-tray's sorted drops could not be read for the desk: {exc}")
        waiting = []
    if waiting:
        count, sources, errors = groups["moves"]
        groups["moves"] = (count + len(waiting), f"{len(waiting)} sorted drop(s) in the in-tray"
                           + (f", {sources}" if sources else ""), errors)
    # The drops that have waited through a session, for the Next line's
    # sort rule; read from git only when there is a Next line to work out.
    groups["drops_waited"] = osort.drops_waited(office_root, groups["drops"]) if groups_out is not None else set()
    if groups_out is not None:
        groups_out.update(groups)
    if not walk_in and groups["moves"][0]:
        # Each pending move, so the desk shows what office moves will do:
        # the sorted drops first, then the moves page by line, the words
        # the sitting's, as it wrote them.
        groups["move_lines"] = []
        if waiting:
            try:
                names = [p["name"] for p in office_projects(office_root) or []]
                for m in osort.move_plans(office_root, names):
                    where = (f"a new folder on {m['lane']}" if m["kind"] == "new" else
                             f"folder {m['folder']}" if m["kind"] == "into" else "nowhere yet")
                    groups["move_lines"].append(f"  {m['page']}: sorted by {m['sid'] or '?'}, into {where}"
                                                + (f"  (stays: {m['problem']})" if m["problem"] else ""))
            except (OSError, oh.HelperError) as exc:
                groups["move_lines"].append(f"  the sorted drops could not be listed: {exc}")
        try:
            moves, _ = od.pending_moves(office_root)
            src = od.move_sources(office_root) if moves else {}
            groups["move_lines"] += [f"  line {m['line']}: {m['day']} {m['text']}  (from {src.get(m['line'], '?')})"
                                     for m in moves]
        except (OSError, oh.HelperError) as exc:
            groups["move_lines"].append(f"  could not be listed: {exc}")
    lines = desk_lines(groups, flight, walk_in=walk_in)
    if groups.get("move_lines"):
        at = next(i for i, l in enumerate(lines) if l.startswith("Pending desk moves"))
        lines[at + 1:at + 1] = groups["move_lines"]
    if machine_file and not walk_in:
        lines += ask_desk_lines(office_root, machine_file)
    return lines, bad


def ask_desk_lines(office_root, machine_file):
    """office desk's asks (0.55.0), after the desk's own groups, as the
    walk-in's Next line names one since 0.54.0: an Asks out section, one
    line each in the walk-in's words (office_ask.out_line), the oldest
    first, its first line the Next line's ask row; then each record of
    this office's whose tray is gone, with the line that removes it
    (office_ask.orphan_line, office status's since 0.54.0). Nothing when
    there are neither; a tray root that cannot be read is said under
    OFFICE_DEBUG, as asks_waiting says it."""
    import office_ask as oa
    import office_home as hs
    tray_root = hs.tray_root_of(machine_file)
    asks = asks_waiting(office_root, machine_file)
    try:
        orphans = oa.orphans(office_root, tray_root)
    except (OSError, oh.HelperError) as exc:
        debug(f"the asks' records could not be read from {tray_root}, so the desk names no orphan: {exc}")
        orphans = []
    out = []
    if asks:
        move = ask_move({"asks": asks})
        out += ["", f"Asks out (next: {move[0]}; a quick question each, answered in a chat):"]
        out += [f"  {oa.out_line(r)}" for r in asks]
    if orphans:
        out += ["", "Asks whose tray is gone:"]
        out += [f"  {oa.orphan_words(name, record, opener)}" for name, record, opener in orphans]
    return out


def blueprint_desk(table, folders, flying, since, bid, flight):
    """office desk --blueprint ID: the arc's member folders in the desk's
    own order, computed from their gates, then the members already filed.
    The blueprint states no order; this is the only place it is shown."""
    import office_drafting as od
    b = table.blueprints().get(bid)
    if b is None:
        raise oh.HelperError(f"no blueprint {bid} on the drafting table")
    members = set(od.blueprint_members(table, bid))
    groups = classify_desk(folders, flying, since, table)
    keep = lambda f: f["rel"] in members  # noqa: E731
    state = "closed" if b["closed"] else ("ratified " + b["ratified"][0] if b["ratified"] else "not ratified")
    out = [f"blueprint {bid}: {b['title']} ({state})"]
    flying_lines = [l for l in flight if any(m in l for m in members)]
    if flying_lines or any(keep(f) for f in groups["open"]):
        out += ["", "In flight:"] + [f"  {l}" for l in flying_lines]
        out += [f"  {folder_line(f)}  [open, no session in flight]" for f in groups["open"] if keep(f)]
    ready = [f for f in groups["ready"] if keep(f)]
    if ready:
        out += ["", "Ready, in order:"] + [f"  {folder_line(f)}" for f in ready]
    parked = {h: [(f, a) for f, a in fs if keep(f)] for h, fs in groups["parked"].items()}
    parked = {h: fs for h, fs in parked.items() if fs}
    if parked:
        out += ["", "Parked:"]
        for heading in sorted(parked, key=lambda h: (not h.startswith("ERROR"), h)):
            out.append(f"  {heading}")
            out += [f"    {folder_line(f)}" for f, _ in parked[heading]]
    cands = [f for f in groups["candidates"] if keep(f)]
    if cands:
        out += ["", "Candidates:"] + [f"  {folder_line(f)}" for f in cands]
    filed = [f for f in folders if keep(f) and f["space"] == "filing-cabinet"]
    if filed:
        out += ["", "Filed:"] + [f"  {oh.cite(f)}  {f['name']}  [{f.get('status') or 'no status line'}]" for f in filed]
    open_lines = [d for d in b["decomposition"] if d["folder"] is None]
    if open_lines:
        out += ["", "Decomposition lines with no folder yet (a desk move opens each):"]
        out += [f"  line {d['n']}: {d['goal']}" for d in open_lines]
    if len(out) == 1:
        out.append("  no member folders yet")
    return out


# --- the Next line -------------------------------------------------------------------
#
# The walk-in ends with one line naming the one command to type next, its
# arguments filled in. It is computed from the office's state on every
# walk-in and never written down. The states, in the order they win, and
# why that order:
#
#   1. the office ahead of or behind the install, or its stamp unreadable:
#      most verbs refuse until that is fixed, land and start among them;
#      behind with the renovation session office upgrade sent out, landing
#      that session comes first (0.12.0, the renovation door);
#   2. a session out: work already sent, waiting only on its response,
#      and an unfounded office's founding session is one of these, so
#      landing it comes before saying the office is unfounded;
#   3. desk moves pending: until office moves runs them, the desk is not
#      in the order the sitting decided, so the next two states could
#      name a folder a move retires or miss one a move opens (0.11.0;
#      0.8.0's order ratified, this step added by the plan-4b sitting);
#   3a. a merge or undo job waiting for its session, then a folder whose
#      work landed and is not delivered (0.41.0, delivery_move); then an
#      office ask out (0.54.0, ask_move): its LEARNED block waits on the
#      occupant as a delivery does, so it comes before a drop;
#   3b. an unsorted drop (0.19.0): the oldest drop in the in-tray whose
#      project resolves to one of the floor plan's projects, with no
#      session in flight on a folder of that lane, goes straight out as a
#      project session (office start --drop in-tray/PAGE); the oldest one
#      whose project does not resolve, or that has none, gives the same
#      line with --lane left for the occupant to fill. Placed after the
#      moves (a sitting's decisions come first) and before the founding,
#      since a drop is capture waiting and the occupant's count is drop,
#      start, land. An office that scopes no project has nowhere to send
#      a drop, and the rule stays quiet there;
#   3c. the standalone sort (0.20.0): an unsorted drop whose project is
#      none, or none of the office's, that has waited through one session
#      (a session recorded in a folder after the drop was committed), gives
#      office start --sort; so does an in-tray of SORT_PILE or more
#      unsorted drops with nothing ready on the desk. The drop rule leaves
#      such a drop to it. Unlike 3b it needs no project: a sort routes to
#      folders that exist;
#   4. unfounded: the profile is the office's reason to exist. With the
#      founding folder on the desk and no session out for it, the line
#      names office start for that folder (which goes out through the
#      founding door with the answers the folder keeps); with none, office
#      found, which opens one and asks the profile's questions (0.12.0);
#   5. a ready folder: the desk's first, in the desk's own order;
#   6. an open folder with no session out: a job under way that nothing
#      is carrying;
#   7. no projects: setup, which a ready job outranks, since an office may
#      scope none by choice and a nag above real work would be wrong;
#   8. slips piling up: enough of them to be a job of their own;
#   9. folders that wait (parked, candidates): the desk says on what;
#  10. nothing to do.
#
# Whether a response is in the downloads is a bale-shaped fact no --json
# surface of bale exposes (bale status gives only a count of search
# directories), so the line says the session is out and that land finds
# its response; the gap is a slip for bale-src, never a scrape.

SLIPS_PILING = 5
SLIPS_SLUG = "triage-the-suggestion-box"


def sessions_to_land(rd, office_root, rendering=True):
    """(sessions, problems): the open sessions office land can bring back,
    held ones first, then oldest first. A session counts when a folder
    records it, or when it is open in the office's own registry (a
    founding or a renovation packed by hand before 0.12.0, which no
    folder records); a read-only sitting lands nothing and never counts.
    Each is open_anywhere's dict plus held, created and door (founding or
    renovation when a door's folder records it, else None)."""
    import office_door as odoor
    every, problems = open_anywhere(rd, office_root, rendering=rendering)
    try:
        doors = odoor.door_folders(office_root)
    except (OSError, oh.HelperError) as exc:
        debug(f"the door folders could not be read for the Next line: {exc}")
        doors = {}
    out = []
    for x in every:
        if x["read_only"] or not (x["folders"] or x["label"] == OFFICE_LABEL):
            continue
        held, created = False, ""
        try:
            d = rd.dossier(x["place"], x["sid"])
            if d is not None:
                v = session_view(rd, d)
                held, created = bool(v["in_flight"] and v["outcome"] == "held"), v["created"] or ""
        except BaleError as exc:
            # Still out, still landable; only its order is unknown.
            debug(f"{x['sid']}: its dossier could not be read for the Next line's order: {exc}")
        door = next((doors[f] for f in x["folders"] if f in doors), None)
        out.append(dict(x, held=held, created=created, door=door))
    out.sort(key=lambda s: (not s["held"], s["created"] or "~", s["sid"]))
    return out, problems


def lane_project(folder, project_names):
    """The project a folder's lane names (`project: paths`, or the
    project alone, as office start --drop writes it), when it is one this
    office scopes, else None."""
    lane = (folder.get("fields", {}).get("lane") or [""])[0]
    name = lane.partition(":")[0].strip()
    return name if name in project_names else None


def start_command(folder, project_names):
    """`office start NAME`, with --on PROJECT when the folder's lane names
    one of the office's projects; start asks the rest (the goal)."""
    on = lane_project(folder, project_names)
    return f"office start {folder['name']}" + (f" --on {on}" if on else "")


def count_slips(office_root):
    """The pages in the suggestion box (its .keep aside)."""
    box = pathlib.Path(office_root) / "suggestion-box"
    return sum(1 for p in box.glob("*.md") if p.is_file()) if box.is_dir() else 0


def founding_folder(groups):
    """The founding folder among the desk's groups (one whose source is
    office init or office found), the highest-numbered; None when the
    desk holds none."""
    import office_door as odoor
    seen = []
    for key in ("ready", "open", "flying", "candidates", "no_status", "misplaced"):
        seen += list(groups.get(key) or [])
    for fs in (groups.get("parked") or {}).values():
        seen += [f for f, _ in fs]
    found = [f for f in seen if ((f.get("fields") or {}).get("source") or [""])[0] in odoor.FOUNDING_SOURCES]
    if not found:
        return None
    return sorted(found, key=lambda f: (f.get("number") or 0, f["name"]))[-1]


def drop_move(drops, groups, projects):
    """(command, why) for the oldest unsorted drop the Next line can send
    out, or None (the rule 3b above). A drop whose project resolves waits
    while a session is in flight on a folder of that project's lane."""
    import office_drop as odrop
    names = [p["name"] for p in projects or []]
    if not drops or not names:
        return None
    busy = {lane_project(f, set(names)) for f in groups.get("flying", [])} - {None}
    waited = groups.get("drops_waited") or set()
    later = len(drops) - 1
    more = f"; {later} more unsorted after it" if later else ""
    for d in drops:
        resolved = odrop.resolve_project(d.get("project"), names)
        if resolved is None and d["rel"] in waited:
            continue  # it has waited through a session: the sort's (sort_move)
        if resolved is None:
            said = f"names {d['project']!r}, which is none of" if d.get("project") else "names no project of"
            return (f"office start --drop {d['rel']} --lane LANE",
                    f"the oldest unsorted drop in the in-tray {said} this office's projects "
                    f"({', '.join(sorted(names))}): put the one it belongs to for LANE, and start mints its "
                    f"folder, moves the drop in and sends it out to be sorted and done{more}")
        if resolved in busy:
            continue
        return (f"office start --drop {d['rel']}",
                f"the oldest unsorted drop in the in-tray is for {resolved} and no session is in flight there; "
                f"start mints its folder, moves the drop in and sends it out to be sorted and done{more}")
    return None


SORT_PILE = 3


def delivery_move(groups):
    """(command, why) for the Next line's delivery row (0.41.0), or None: a
    merge job waiting for its session first (office start N --merge), then
    the folder whose work landed newest and is not delivered (office
    deliver N)."""
    waiting = [m for m in groups.get("merges") or [] if not m["landed"]]
    if waiting:
        f, job = waiting[0]["folder"], waiting[0]["job"]
        more = f"; {len(waiting) - 1} more wait" if len(waiting) > 1 else ""
        bailed = job_bailed(job)
        if bailed:
            # 0.53.0: the handoff, not a session from scratch.
            return (job_start_line(f, job),
                    f"{oh.cite(f)}'s {'undo' if odl_is_undo(job) else 'merge'} job waits and {bailed} bailed out of "
                    f"it; start --handoff sends the fresh session its handoff asks for{more}")
        if odl_is_undo(job):
            return (f"office start {folder_key(f)} --undo-bale",
                    f"{oh.cite(f)}'s undo job waits; start --undo-bale sends the session that takes bale's own change "
                    f"out of the workbench{more}")
        return (f"office start {folder_key(f)} --merge",
                f"{oh.cite(f)}'s merge job waits; start --merge sends the session that resolves it{more}")
    undelivered = groups.get("undelivered") or []
    if undelivered:
        u = undelivered[0]
        more = f"; {len(undelivered) - 1} more wait" if len(undelivered) > 1 else ""
        return (f"office deliver {folder_key(u['folder'])}",
                f"{oh.cite(u['folder'])}'s work landed on {u['project']} and is not delivered yet; deliver carries "
                f"it to {u['audience']}{more}")
    return None


ASK_LEARNED = "office ask --learned"


def ask_move(groups):
    """(command, why) for the Next line's ask row (0.54.0), or None: the
    oldest office ask out from this office (groups["asks"], office_ask
    asks_out's list, oldest first), which waits on the occupant as a
    delivery does: its chat's LEARNED block is his to file."""
    import office_ask as oa
    asks = groups.get("asks") or []
    if not asks:
        return None
    a = asks[0]
    when = f"{a.get('day', '?')} {a.get('time', '')}".rstrip()
    more = f"; {len(asks) - 1} more out after it" if len(asks) > 1 else ""
    return (ASK_LEARNED,
            f"{a['name']} ({oa.where_words(a)}) has been out since {when}: once its chat ends, --learned files its "
            f"LEARNED block from the clipboard (or from a FILE); office tray {a['name']} opens its tray again{more}")


def asks_waiting(office_root, machine_file):
    """The asks out from this office, for the Next line (0.54.0): office_ask
    asks_out in the out tray machine.toml names (default ~/out-tray); []
    when it cannot be read, said under OFFICE_DEBUG."""
    import office_ask as oa
    import office_home as hs
    tray_root = hs.tray_root_of(machine_file)
    try:
        return oa.asks_out(office_root, tray_root)
    except (OSError, oh.HelperError) as exc:
        debug(f"the asks out could not be read from {tray_root}, so the Next line does not name one: {exc}")
        return []


def sort_move(drops, groups, projects):
    """(command, why) for office start --sort, or None (the rule 3c
    above): an unsorted drop with no project, or one that does not
    resolve, that has waited through one session; or an in-tray of
    SORT_PILE or more unsorted drops with nothing ready on the desk."""
    import office_drop as odrop
    if not drops:
        return None
    names = [p["name"] for p in projects or []]
    waited = groups.get("drops_waited") or set()
    stuck = [d for d in drops if d["rel"] in waited and odrop.resolve_project(d.get("project"), names) is None]
    if stuck:
        d = stuck[0]
        return ("office start --sort",
                f"{d['rel']} names {'no project' if not d.get('project') else repr(d['project'])} this office can "
                f"send it to, and a session has gone out since it was dropped; the sort reads every unsorted drop "
                f"({len(drops)}) and says where each goes")
    if len(drops) >= SORT_PILE and not groups.get("ready"):
        return ("office start --sort",
                f"{len(drops)} unsorted drops wait in the in-tray and nothing is ready on the desk; the sort reads "
                "them all and says where each goes")
    return None


def next_move(skew, founded, out, groups, projects, slips, behind=None, cache=None):
    """(command, why) for the walk-in's Next line, from the office's state:
    skew (current, behind, ahead or unreadable), founded (bool), out
    (sessions_to_land's list), groups (classify_desk's, with the
    in-tray's unsorted drops under "drops" as render_desk adds them),
    projects (the [projects] entries, or None for no table), slips (a
    count), behind (install_behind's dict when the install is behind a
    source this office scopes, else None) and cache (bytecode_behind's
    dict when the install's bytecode cache is not level for this python3,
    else None). A pure function, so every state is testable without an
    office.

    The order (doctrine section 7, the walk-in): the office out of step with the
    install, then the install behind its source, then its bytecode cache
    not level, then a session out, the moves, an unsorted drop, the
    founding, the desk. The install comes before a session out because
    office start and office land run the install: behind its source, they
    would run the old office. Its cache comes next (0.31.0), since the same
    one line brings it level and, until it runs, every command, a land
    included, compiles the helpers from source and takes about twice as
    long; install.sh's line is filled in only where its stamp names the
    source, and with none the line leaves the cache to office status."""
    if skew == "ahead":
        return ("office status", "this office was migrated past the installed office-src; install a newer one "
                                 "(office status names both versions)")
    if skew == "behind":
        reno = [s for s in out if s.get("door") == "renovation"]
        if reno:
            s = reno[0]
            return (f"office land {s['sid']}",
                    f"office upgrade sent this renovation out ({', '.join(s['folders'])}); once it lands, office "
                    "upgrade checks it and stamps the office")
        return ("office upgrade", "this office is behind a breaking release of office-src, and the verbs that "
                                  "change it refuse until it is upgraded")
    if skew != "current":
        return ("office status", "this office's version stamp could not be read; office status says why")
    if behind:
        return (f"(cd {shell_quote(behind['source'])} && ./install.sh)",
                f"the installed office-src is behind its source, which this office scopes as {behind['project']} "
                f"(installed {behind['commit']}; the source is at {behind['head']}, office-src {behind['version']}); "
                "office start and office land run the install, so until it is level they run the old office")
    if cache and cache.get("source"):
        return (f"(cd {shell_quote(cache['source'])} && ./install.sh)",
                f"the installed office-src's bytecode cache is not level for this python3 ({cache['what']}), so "
                "every office command compiles its helpers from source and takes about twice as long; install.sh "
                "compiles them again")
    if out:
        s = out[0]
        where = "this office" if s["label"] == OFFICE_LABEL else s["label"]
        names = ", ".join(s["folders"]) or "no folder records it"
        more = f"; {len(out) - 1} more out after it" if len(out) > 1 else ""
        if s["held"]:
            return (f"office land {s['sid']}",
                    f"bale held it in {where} ({names}); land asks for the corrected response{more}")
        return (f"office land {s['sid']}",
                f"it is out in {where} ({names}); when its response is in your downloads, land finds it{more}")
    count, sources, errors = groups.get("moves", (0, "", []))
    if count or errors:
        unread = f"; {len(errors)} line(s) of drafting-table/moves.md do not read, and moves names them" \
            if errors else ""
        return ("office moves",
                (f"{count} desk move(s) a sitting decided are pending ({sources})" if count else
                 "drafting-table/moves.md holds lines that do not read")
                + "; until they run, the desk is not in the order the sitting decided" + unread)
    # A merge job waiting for its session, then a folder whose work landed
    # and is not delivered (0.41.0): after the moves, before a drop.
    move = delivery_move(groups)
    if move is not None:
        return move
    # An office ask out (0.54.0): after a waiting job or delivery, before a
    # drop, since it waits on the occupant as a delivery does.
    move = ask_move(groups)
    if move is not None:
        return move
    move = drop_move(groups.get("drops") or [], groups, projects) \
        or sort_move(groups.get("drops") or [], groups, projects)
    if move is not None:
        return move
    if not founded:
        f = founding_folder(groups)
        if f is not None:
            return (f"office start {f['name']}",
                    f"the profile is incomplete, so this office is unfounded; {oh.cite(f)} is its founding folder "
                    "and no session is out for it; start sends the founding session out with the answers the "
                    "folder keeps, and asks only for what is missing")
        return ("office found", "the profile is incomplete, so this office is unfounded, and no founding folder is "
                                "on the desk; found asks the profile's questions and sends the founding session out")
    names = {p["name"] for p in projects or []}
    if groups.get("ready"):
        f = groups["ready"][0]
        more = len(groups["ready"]) - 1
        return (start_command(f, names),
                f"{oh.cite(f)} is ready and first on the desk; start asks for the goal and sends a session out"
                + (f"; {more} more ready after it" if more else ""))
    opened = [f for f in groups.get("open") or [] if f["rel"] not in (groups.get("undelivered_by_rel") or {})]
    if opened:
        f = opened[0]
        return (start_command(f, names),
                f"{oh.cite(f)} is open and no session is out for it; office close {f['name']} instead when its "
                "job is done")
    if not projects:
        return ("office projects add", "this office watches no projects yet; add asks for a repo's path and "
                                       "what rides with it")
    waiting = [f for fs in groups.get("parked", {}).values() for f, _ in fs] + list(groups.get("candidates", []))
    on_desk = waiting + list(groups.get("flying", []))
    if slips >= SLIPS_PILING and not any(f["name"].endswith("-" + SLIPS_SLUG) for f in on_desk):
        return (f"office open {SLIPS_SLUG} --title \"Triage the suggestion box\" --size small "
                "--source \"the suggestion box\"",
                f"{slips} slips are in the suggestion box, enough to be a job; a session can sort them from "
                "that folder")
    parked = len(waiting) - len(groups.get("candidates", []))
    candidates = len(groups.get("candidates", []))
    if parked or candidates:
        return ("office desk", f"nothing is ready: {parked} parked, {candidates} candidate(s); the desk says what "
                               "each waits for")
    unplaced = sum(len(groups.get(g, [])) for g in ("no_status", "misplaced", "unreadable"))
    if unplaced:
        return ("office desk", f"{unplaced} folder(s) on the desk that it cannot order; the desk names each and why")
    return ("office start new", "nothing waits on you; start new takes a new job in your words when one comes in "
                                "and sends its session out, and office note TEXT captures a thought")


def next_line(rd, office_root, skew, founded, groups):
    """The walk-in's Next line, read from the office and bale's records."""
    out, problems = sessions_to_land(rd, office_root)
    for p in problems:
        debug(f"the Next line could not read every repo: {p}")
    try:
        behind = install_behind(office_root)
    except (OSError, oh.HelperError) as exc:
        debug(f"the install could not be compared with its source: {exc}")
        behind = None
    try:
        cache = bytecode_behind()
    except (OSError, oh.HelperError) as exc:
        debug(f"the install's bytecode cache could not be checked: {exc}")
        cache = None
    command, why = next_move(skew, founded, out, groups, office_projects(office_root),
                             count_slips(office_root), behind, cache)
    return f"Next: {command}  ({why})"


# A dossier read that fails with one of these kinds failed at the project
# (bale refused there, the directory went, the host stopped answering), so
# the project is not read again in this rendering. Any other kind is bale
# answering about this one session in words that do not read (a record it
# could not parse, say): that session's line, and the project stays in
# the search for the others.
PROJECT_WIDE_KINDS = ("missing", "path", "refused", "unreachable")


def project_records(rd, project, statuses, unread, batch=()):
    """(cwd, the sids its surfaces name) for one project, read once per
    rendering and kept in statuses; None when it cannot be read, its one
    line's words kept in unread (name: why), so it is said once and passed
    over from then on. Through a host's shell the dossiers of the sids in
    batch that its records name ride one more connection, so the reads
    that follow ask it nothing more. Since 0.38.0 a project is read only
    when a search reaches it, so a project no search needs is never
    opened."""
    name = project["name"]
    if name in unread:
        return None
    if name not in statuses:
        try:
            cwd = rendered(project)
            sids = rd.known_sids(cwd)
            if rd.hosted(cwd):
                rd.prefetch(cwd, [("dossier", {"sid": sid}) for sid in batch if sid in sids])
        except BaleError as exc:
            unread[name] = str(exc)
            debug(f"{name}: not read, and passed over for the rest of this rendering: {exc}")
            return None
        statuses[name] = (cwd, sids)
    return statuses[name]


def locate(rd, projects, sid, statuses, unread, lane=None, batch=()):
    """(project, dossier, record_errors) for a sid. The search goes, each
    project read in its own try (project_records): the folder's own
    project (lane, its name) first, so a folder's session is found with
    one read in the common case; then the projects whose outbox or open
    list names the sid; then the rest. A project that cannot be read is
    kept in unread and the search goes on. record_errors is [(project,
    BaleError)] for this sid's own dossier reads that did not read, which
    leave the project in the search for other sids. (None, None, errors)
    when no readable project's records hold it."""
    errors = []

    def dossier_in(p, cwd):
        try:
            return rd.dossier(cwd, sid)
        except BaleError as exc:
            if exc.kind in PROJECT_WIDE_KINDS:
                unread[p["name"]] = str(exc)
                debug(f"{p['name']}: not read, and passed over for the rest of this rendering: {exc}")
            else:
                errors.append((p, exc))
            return None

    first = [p for p in projects if lane is not None and p["name"] == lane]
    for p in first:
        got = project_records(rd, p, statuses, unread, batch)
        if got is not None:
            d = dossier_in(p, got[0])
            if d is not None:
                return p, d, errors
    rest = []
    for p in projects:
        if p in first:
            continue
        got = project_records(rd, p, statuses, unread, batch)
        if got is not None:
            rest.append((p, got))
    ordered = [pg for pg in rest if sid in pg[1][1]] + [pg for pg in rest if sid not in pg[1][1]]
    for p, (cwd, _) in ordered:
        if p["name"] in unread:
            continue
        d = dossier_in(p, cwd)
        if d is not None:
            return p, d, errors
    return None, None, errors


def folder_lane(folder_md, projects):
    """The project the folder's lane names, when this office scopes it;
    None otherwise (no lane, a lane naming no project, or one the office
    does not scope, each a debug line), and the search then has no first
    project."""
    try:
        lane = oh.folder_lane_project(folder_md)
    except (oh.HelperError, OSError, ValueError) as exc:
        debug(f"the folder's lane could not be read, so no project is searched first: {exc}")
        return None
    if lane is None:
        debug("the folder's lane names no project, so no project is searched first")
        return None
    if lane not in {p["name"] for p in projects}:
        debug(f"the folder's lane names {lane}, which this office does not scope; no project is searched first")
        return None
    return lane


def render_folder_sessions(rd, office_root, folder_md):
    """(lines, uncertain): the folder's own Sessions lines, each followed
    by what bale's records say about the session. Nothing rendered here
    is written into the folder.

    Since 0.38.0 one project that cannot be read is a line, not a stop:
    each project is read in its own try, only when a search reaches it,
    the folder's own project (its lane) first; one that cannot be read is
    said once, in one line after the sessions, and the search goes on
    through the others. uncertain counts the recorded sessions not found
    while some project could not be read for them, since only then is
    "not found" in doubt; it is 0 whenever every recorded session was
    found, and main's exit 3 (bin/office's stop) follows it."""
    recorded = oh.folder_session_lines(folder_md)
    lines = [f"- {sid}" + (f": {words}" if words else "") for sid, words in recorded]
    if not recorded:
        return ["no session ids are recorded in this folder"], 0
    projects = office_projects(office_root)
    if not projects:
        return lines + [f"{no_projects_line(projects)}; no outcomes are rendered"], 0
    out, uncertain, found, missing = [], 0, 0, []
    statuses, unread = {}, {}
    try:
        rd.bale()
    except BaleError as exc:
        return lines + [f"  cannot read bale's records: {exc}"], 1
    lane = folder_lane(folder_md, projects)
    batch = [sid for sid, _ in recorded]
    for (sid, words), line in zip(recorded, lines):
        out.append(line)
        p, d, errors = locate(rd, projects, sid, statuses, unread, lane, batch)
        for _, exc in errors:
            out.append(f"    cannot read: {exc}")
        if d is None:
            missing.append(sid)
            could_not = sorted(set(unread) | {e[0]["name"] for e in errors})
            if could_not:
                uncertain += 1
                out.append(f"    not found in the projects that could be read; {', '.join(could_not)} could not")
            else:
                out.append("    not in the records of any project this office scopes")
            continue
        found += 1
        v = session_view(rd, d)
        out.append(f"    {p['name']}: {outcome_word(v)}; opened {day(v['created'])}, last event "
                   f"{day(v['updated'])}; work class {v['work_class']}")
        responses = response_attempts(v)
        if not responses:
            out.append("    no response attempt yet")
        for n, a in enumerate(responses, 1):
            checks = a["checks"]
            tally = {}
            for c in checks:
                tally[c["agreement"]] = tally.get(c["agreement"], 0) + 1
            summary = ", ".join(f"{k} {tally[k]}" for k in sorted(tally)) or "no claims"
            out.append(f"    attempt {n}, {a['command']} {day(a['at'])}: {a['outcome']}, validation "
                       f"{a['state'] or 'not run'}; {len(checks)} claim(s): {summary}")
            for c in checks:
                out.append(f"      [{c['agreement']}] claim {c['claim']}, verdict {c['verdict']}: {c['check']}")
        rounds = [a["rounds"] for a in v["attempts"] if a["rounds"] is not None]
        links = [f"{a['linkage'][0]} {a['linkage'][1]}" for a in v["attempts"] if a["linkage"]]
        out.append(f"    exchange rounds: {rounds[-1] if rounds else 'none recorded'}"
                   + (f"; linkage: {', '.join(links)}" if links else ""))
    # Each project that could not be read, once, in the floor plan's order.
    for p in projects:
        if p["name"] in unread:
            out.append(oh.paused_line(p["name"]) if p.get("paused") else f"{p['name']}: not read: {unread[p['name']]}")
    out.append(f"recorded in this folder: {len(recorded)} session id(s); found in bale's records: {found}"
               + (f"; not found: {', '.join(missing)}" if missing else ""))
    out.append("bale version per session: not on bale's dossier (a slip for bale-src)")
    return out, uncertain


def all_views(rd, cwd):
    """(views of every session the repo's surfaces name, sids with no
    record)."""
    views, unrecorded = [], []
    sids = rd.known_sids(cwd)
    rd.prefetch(cwd, [("dossier", {"sid": sid}) for sid in sids])
    for sid in sids:
        d = rd.dossier(cwd, sid)
        if d is None:
            unrecorded.append(sid)
        else:
            views.append(session_view(rd, d))
    return views, unrecorded


def render_ledger(rd, office_root, name=None):
    """(lines, unreadable): the trust ledger per project and work class.
    It renders the evidence; it holds no grant (seed Q-6 is open)."""
    projects = office_projects(office_root)
    if not projects:
        return [no_projects_line(projects)], 0
    lines, bad = [], 0
    for p in select(projects, name):
        try:
            cwd = rendered(p)
            # Through a host's shell: two connections, the aggregate and
            # the status, then every class's aggregate and every dossier.
            rd.prefetch(cwd, [("stats", {}), ("status", {})])
            agg = rd.aggregate(cwd)
            classes = rd.key(agg, "stats", "classes") or {}
            rd.prefetch(cwd, [("stats", {"work_class": cls}) for cls in sorted(classes)]
                        + [("dossier", {"sid": sid}) for sid in rd.known_sids(cwd)])
            views, unrecorded = all_views(rd, cwd)
            lines.append(f"{p['name']}: trust ledger per work class (renders the evidence; holds no grant)")
            if not classes:
                lines.append("  no classed sessions in bale's records yet")
            header = ("class", "sessions", "applied", "HOLD rate", "first-attempt PASS", "claim agreement", "bailouts")
            rows = [header]
            notes = []
            for cls, row in sorted(classes.items()):
                sessions = rd.key(row, "stats", "classes.*.sessions")
                held = rd.key(row, "stats", "classes.*.held_attempts")
                responses = rd.key(row, "stats", "classes.*.response_attempts")
                checks = rd.key(row, "stats", "classes.*.checks")
                agree = rd.key(row, "stats", "classes.*.checks_agree")
                na = rd.key(row, "stats", "classes.*.checks_na")
                bailed = rd.key(row, "stats", "classes.*.bailout_sessions")
                with_response = rd.key(row, "stats", "classes.*.sessions_with_response_attempt")
                applied = rd.key(rd.key(rd.aggregate(cwd, cls), "stats", "closure_mix"), "stats", "closure_mix.applied")
                members = [v for v in views if v["work_class"] == cls and not v["read_only"]]
                firsts = [response_attempts(v)[0] for v in members if response_attempts(v)]
                passed = sum(1 for a in firsts if a["outcome"] == "applied")
                counted_applied = sum(1 for v in members if v["outcome"] == "applied")
                rows.append((cls, str(sessions), str(applied),
                             rate(held, responses, rd.key(row, "stats", "classes.*.hold_rate")),
                             rate(passed, len(firsts)),
                             rate(agree, checks, rd.key(row, "stats", "classes.*.agreement_rate"))
                             + (f"; {na} n/a" if na else ""),
                             f"{bailed} of {with_response}"))
                if len(members) != sessions:
                    notes.append(f"{cls}: bale's aggregate counts {sessions} session(s); "
                                 f"{len(members)} dossier(s) found for it")
                if counted_applied != applied:
                    notes.append(f"{cls}: bale's closure mix counts {applied} applied; "
                                 f"the dossiers say {counted_applied}")
            widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
            if classes:
                for r in rows:
                    lines.append("  " + "  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip())
            lines += [f"  both counts, records beside records: {n}" for n in notes]
            if unrecorded:
                lines.append(f"  in the outbox with no record: {', '.join(unrecorded)}")
        except BaleError as exc:
            if exc.kind == "paused":
                lines.append(unread_line(p["name"], exc))
                continue
            bad += 1
            lines.append(unread_line(p['name'], exc))
    return lines, bad


def landed_paths(a, path):
    """The attempt's change paths that are the path or under it."""
    return [c for c in a["change_paths"] if c == path or c.startswith(path + "/")]


def render_landed(rd, office_root, path, name=None):
    """(lines, unreadable): for each project, the latest applied session
    whose change set held the path (or a path under it)."""
    path = path.strip().removeprefix("./").rstrip("/")
    if not path or path.startswith("/"):
        raise oh.HelperError("--landed takes a path relative to the project's root, e.g. bin/office")
    projects = office_projects(office_root)
    if not projects:
        return [no_projects_line(projects)], 0
    lines, bad = [], 0
    for p in select(projects, name):
        try:
            cwd = rendered(p)
            views, _ = all_views(rd, cwd)
            hits = []
            for v in views:
                for a in response_attempts(v):
                    if a["outcome"] == "applied" and landed_paths(a, path):
                        hits.append((a["at"], v, landed_paths(a, path)))
            if not hits:
                lines.append(f"{p['name']}: no applied session in bale's records landed {path}")
                continue
            hits.sort(key=lambda h: h[0])
            at, v, paths = hits[-1]
            under = "" if paths == [path] else f", {len(paths)} path(s) under it"
            lines.append(f"{p['name']}: {path} last landed by {v['sid']} (applied {day(at)}, "
                         f"{v['work_class']}{under}); {len(hits)} applied session(s) landed it in all")
        except BaleError as exc:
            if exc.kind == "paused":
                lines.append(unread_line(p["name"], exc))
                continue
            bad += 1
            lines.append(unread_line(p['name'], exc))
    return lines, bad


def render_versions(rd, office_root, name=None):
    """(lines, unreadable): the version trail per project: the applied
    sessions whose change set held a VERSION file, oldest first, and the
    contract-doc epochs bale's aggregate keeps."""
    projects = office_projects(office_root)
    if not projects:
        return [no_projects_line(projects)], 0
    lines, bad = [], 0
    for p in select(projects, name):
        try:
            cwd = rendered(p)
            rd.prefetch(cwd, [("stats", {}), ("status", {})])
            views, _ = all_views(rd, cwd)
            lines.append(f"{p['name']}: version trail")
            releases = []
            for v in views:
                for a in response_attempts(v):
                    held = [c for c in a["change_paths"] if c.rsplit("/", 1)[-1] == VERSION_FILE]
                    if a["outcome"] == "applied" and held:
                        releases.append((a["at"], v["sid"], held))
            lines.append(f"  releases: applied sessions whose change set held a {VERSION_FILE} file")
            for at, sid, held in sorted(releases):
                lines.append(f"    {day(at)}  {sid}  {', '.join(held)}")
            if not releases:
                lines.append("    none in bale's records")
            lines.append("  contract-doc epochs: the bale docs each session was packed under")
            epochs = rd.key(rd.aggregate(cwd), "stats", "doc_epochs") or {}
            for digest, row in sorted(epochs.items(),
                                      key=lambda kv: rd.key(kv[1], "stats", "doc_epochs.*.first_created_at") or ""):
                lines.append(f"    {digest} from {day(rd.key(row, 'stats', 'doc_epochs.*.first_created_at'))}: "
                             f"{rd.key(row, 'stats', 'doc_epochs.*.sessions')} session(s), "
                             f"{rd.key(row, 'stats', 'doc_epochs.*.applied')} applied, "
                             f"{rd.key(row, 'stats', 'doc_epochs.*.in_flight')} in flight")
            if not epochs:
                lines.append("    none in bale's records")
            installed = rd.key(rd.status(cwd), "status", "version")
            lines.append(f"  bale now: {installed}; bale version per session: not on bale's dossier "
                         "(a slip for bale-src)")
        except BaleError as exc:
            if exc.kind == "paused":
                lines.append(unread_line(p["name"], exc))
                continue
            bad += 1
            lines.append(unread_line(p['name'], exc))
    return lines, bad


def applied_sids(cwd):
    """The session ids bale tagged applied in a repo (its applied/SID
    tags, as office deliver reads them), here or through a host's shell.
    A repo with none is an empty set; one git cannot read raises
    BaleError."""
    out = git_lines(cwd, "for-each-ref", "--format=%(refname:short)", "refs/tags/applied/")
    if out is None:
        raise BaleError("refused", f"git cannot list the applied/ tags in {cwd}")
    return {t[len("applied/"):] for t in out.split() if t.startswith("applied/")}


# --- landed and not delivered, and a merge job waiting (0.41.0) ---------------------------
#
# A folder on a project with an audience stays on the desk after office land
# and closes at delivery (the plan's ruling of 2026-10-29), so the desk, the
# walk-in, the home screen, the Next line and bare office deliver know it as
# landed, not delivered, and offer `office deliver N` by key; a folder whose
# merge job (office deliver's merge/merge.md) names no session is offered
# `office start N --merge`. Both are read from the office's own pages and
# the project's applied/SID tags, with git alone, through the shell for a
# hosted project: never a fetch of the audience and never a bale call.


def applied_tag_times(cwd):
    """{sid: when bale tagged it applied} for a repo's applied/SID tags, as
    UTC datetimes, read with git alone (the tag's creator date: the tagger's
    for an annotated tag, else its commit's), here or through a host's
    shell. Raises BaleError when git cannot list them."""
    out = git_lines(cwd, "for-each-ref", "--format=%(refname:short)%09%(creatordate:unix)", "refs/tags/applied/")
    if out is None:
        raise BaleError("refused", f"git cannot list the applied/ tags in {cwd}")
    got = {}
    for line in out.splitlines():
        name, _, stamp = line.partition("\t")
        if not name.startswith("applied/"):
            continue
        try:
            got[name[len("applied/"):]] = dt.datetime.fromtimestamp(int(stamp), dt.timezone.utc)
        except (ValueError, OverflowError):
            got[name[len("applied/"):]] = None
    return got


def delivered_by_project(folders):
    """{project: the sids any folder's `delivered` History lines name for it},
    the desk's and the filing cabinet's, as office deliver's records read
    them (office_helper.delivered_records' reading): a session another
    folder delivered (--others-too) is delivered for every folder that
    records it."""
    out = {}
    for f in folders:
        if f.get("problem"):
            continue
        for _, verb, text in f.get("history") or []:
            if verb != "delivered":
                continue
            m = oh.DELIVERED_RE.match(text)
            if not m:
                continue
            sids = {x.strip() for x in m.group("sessions").split(",") if x.strip() and x.strip() != "none"}
            out.setdefault(m.group("project"), set()).update(sids)
    return out


def office_zone(office_root):
    """The office's timezone (the floor plan's [office] timezone), or None
    (UTC) when it is unset or does not resolve here."""
    try:
        name = (oh.read_toml(pathlib.Path(office_root) / "floor-plan" / "manifest.toml").get("office") or {}) \
            .get("timezone")
        if not name:
            return None
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception as exc:  # an unreadable floor plan or an unknown zone: said, and UTC stands
        debug(f"the office's timezone could not be read for a landing's day: {exc}")
        return None


def folder_merge_job(folder):
    """The folder's job or None: its merge job (office deliver's
    merge/merge.md) or, since 0.51.0, its undo job (undo/undo.md), one at a
    time (odl_is_undo tells them apart); a page that does not read is said
    under OFFICE_DEBUG and is None."""
    import office_deliver as odl
    try:
        return odl.folder_job(pathlib.Path(folder["path"]).parent)
    except (odl.DeliverError, OSError) as exc:
        debug(f"{folder['rel']}: its job does not read ({'; '.join(getattr(exc, 'lines', [str(exc)]))})")
        return None


def odl_is_undo(job):
    """Whether a folder's job is an undo job (0.51.0), not a merge job."""
    import office_deliver as odl
    return odl.is_undo(job)


def job_flag(job):
    """office start's flag that sends a folder's job's session."""
    return "--undo-bale" if odl_is_undo(job) else "--merge"


def job_bailed(job):
    """The session that bailed out of a job waiting for its session (0.53.0:
    the page's `- bailed: SID` line, kept since 0.52.0), or None."""
    return job.get("bailed") if not job.get("session") else None


def job_start_words(job):
    """What office start takes after the folder to send a waiting job's
    session (0.53.0): for a job a session bailed out of, the handoff of its
    response (`--handoff response-SID.tar.gz`, the name a browser saves it
    by, which office start looks for here and then in the downloads), so the
    fresh session starts from the handoff rather than from scratch; else
    the job's own flag."""
    bailed = job_bailed(job)
    return ["--handoff", f"response-{bailed}.tar.gz"] if bailed else [job_flag(job)]


def job_start_line(f, job):
    """The office start line for a waiting job: `office start N WORDS`."""
    return " ".join(["office start", folder_key(f), *job_start_words(job)])


def job_waiting_words(job):
    """A waiting job in a desk line's words (before its office line)."""
    bailed = job_bailed(job)
    after = f"; {bailed} bailed out of it" if bailed else ""
    if odl_is_undo(job):
        return (f"undo job waiting: bale's own commit {job['commit'][:7]} conflicts with the workbench in "
                f"{len(job['files'])} file(s){after}")
    return (f"merge job waiting: {job['audience']}/{job['branch']} conflicts with the workbench in "
            f"{len(job['files'])} file(s){after}")


def waiting_on_delivery(office_root, folders=None, projects=None):
    """(undelivered, merges, unread) for the folders on the desk, read once.

    undelivered, newest landing first: a folder whose lane names a project
    with an audience (not paused) and that records at least one session
    applied there (bale's applied/SID tag) that no folder's `delivered`
    line names, and whose merge job, if it holds one, is not waiting for a
    session; each a dict: folder, project, audience, sids (the sessions to
    deliver, oldest first), sid (the newest of them), at (its tag's time)
    and day (the office's date of it).

    merges: a folder whose merge job names no session yet, or names one
    that is applied (then the folder is landed, not delivered, too, and
    deliver makes the merge); each a dict: folder, job, landed (the
    session's id when it is applied there, else None).

    unread: one line per project whose tags could not be read (or that is
    paused) while a folder waited on it. Nothing is read when no folder on
    the desk could be one."""
    root = pathlib.Path(office_root)
    folders = oh.read_folders(root) if folders is None else folders
    projects = office_projects(root) if projects is None else projects
    by_name = {p["name"]: p for p in projects or []}
    candidates = []
    for f in folders:
        if f.get("problem") or f["space"] != "desk" or not f.get("sids"):
            continue
        lane = oh.lane_project((f["fields"].get("lane") or [""])[0])
        p = by_name.get(lane)
        if p is None or not p.get("audience") or p["problem"] or p["declaration_problems"]:
            continue
        candidates.append((f, p))
    if not candidates:
        return [], [], []
    delivered = delivered_by_project(folders)
    tags, unread = {}, []
    for _, p in candidates:
        if p["name"] in tags:
            continue
        try:
            tags[p["name"]] = applied_tag_times(rendered(p))
        except BaleError as exc:
            tags[p["name"]] = None
            unread.append(unread_line(p["name"], exc))
    zone_ = office_zone(root)
    undelivered, merges = [], []
    for f, p in candidates:
        applied = tags.get(p["name"])
        if applied is None:
            continue
        job = folder_merge_job(f)
        if job is not None:
            landed = job.get("session") if job.get("session") in applied else None
            if job.get("session") and not landed:
                continue  # its session is out: in flight, and said there
            merges.append({"folder": f, "job": job, "landed": landed})
            if not landed:
                continue  # deliver would only name the merge session
        pending = [s for s in f["sids"] if s in applied and s not in delivered.get(p["name"], set())]
        if not pending:
            continue
        newest = max(pending, key=lambda s: (applied[s] or dt.datetime.min.replace(tzinfo=dt.timezone.utc), s))
        at = applied[newest]
        day_ = (at.astimezone(zone_) if zone_ is not None else at).strftime("%Y-%m-%d") if at else "a day git does not say"
        undelivered.append({"folder": f, "project": p["name"], "audience": p["audience"], "sids": pending,
                            "sid": newest, "at": at, "day": day_})
    undelivered.sort(key=lambda u: (u["at"] or dt.datetime.min.replace(tzinfo=dt.timezone.utc), u["folder"]["name"]),
                     reverse=True)
    merges.sort(key=lambda m: (m["job"].get("day") or "", m["folder"]["name"]), reverse=True)
    return undelivered, merges, unread


def probe_folders(rd, office_root):
    """[(name, sid, words)] for bare office probe (0.41.0): each folder on
    the desk that records a session open where probes run (a read-only
    sitting open in the office, a session open in the office, or a session
    open on a project), one row per folder, its first such session; the
    folders whose session is a sitting first, then in the desk's order.
    words say what the session is: `a sitting`, `in the office` or `on
    PROJECT`. A repo that cannot be read is passed over (open_anywhere's
    problems, said under OFFICE_DEBUG)."""
    every, problems = open_anywhere(rd, office_root)
    for line in problems:
        debug(f"bare office probe could not read every repo: {line}")
    rows = {}
    for x in every:
        for rel in x["folders"]:
            if not rel.startswith("desk/"):
                continue
            sitting = x["read_only"] and x["label"] == OFFICE_LABEL
            words = ("a sitting" if sitting else "in the office" if x["label"] == OFFICE_LABEL
                     else f"on {x['label']}")
            row = (not sitting, rel.split("/", 1)[1], x["sid"], words)
            if rel not in rows or row < rows[rel]:
                rows[rel] = row
    return [(name, sid, words) for _, name, sid, words in sorted(rows.values())]


def merge_job_words(m):
    """A waiting job in the home screen's words (after `for folder N,
    TITLE`): AUDIENCE/BRANCH (or, 0.51.0, bale's own commit), the files,
    the day deliver wrote it."""
    job = m["job"]
    k = len(job["files"])
    side = (f"bale's own commit {job['commit'][:7]}" if odl_is_undo(job) else f"{job['audience']}/{job['branch']}")
    return (f"{side} conflicts with the workbench in {k} file(s) (office deliver wrote "
            f"the job on {job.get('day') or 'a day it did not say'})")


def folder_title(f):
    """A folder's title as a screen shows it: as he wrote it (0.49.0,
    office_helper.shown), its directory name when it has none."""
    return oh.shown(f.get("title") or f["name"])


def deliver_item_words(u):
    """The home screen's words for a landed-not-delivered folder."""
    f = u["folder"]
    return (f"Deliver {oh.cite(f)}, {folder_title(f)} ({u['project']}): {u['sid']} landed {u['day']}, not yet "
            "delivered")


def merge_item_words(m):
    f = m["folder"]
    kind = "undo" if odl_is_undo(m["job"]) else "merge"
    bailed = job_bailed(m["job"])
    if bailed:
        return (f"Hand off the {kind} session for {oh.cite(f)}, {folder_title(f)}: {bailed} bailed out; "
                f"{merge_job_words(m)}")
    return f"Send the {kind} session for {oh.cite(f)}, {folder_title(f)}: {merge_job_words(m)}"


def folder_key(f):
    """How a verb's line names a folder: its number, else its name."""
    return str(f["number"]) if f.get("number") else f["name"]


def waiting_lines(office_root):
    """office status's lines under the folders line (0.41.0): one per folder
    on the desk whose merge job waits for its session, or whose merge
    session landed without the merge made; nothing when there is none."""
    _, merges, _ = waiting_on_delivery(office_root)
    lines = []
    for m in merges:
        f, job = m["folder"], m["job"]
        n = folder_key(f)
        bailed = None if m["landed"] else job_bailed(job)
        if bailed:
            # 0.53.0: a job a session bailed out of is offered its handoff.
            kind = "undo" if odl_is_undo(job) else "merge"
            lines.append(f"{oh.cite(f)}: {kind} job waiting, its session {bailed} bailed out; {job_start_line(f, job)} "
                         "sends the fresh session its handoff asks for")
        elif odl_is_undo(job):
            # 0.51.0: the undo job, beside the merge job.
            if m["landed"]:
                lines.append(f"{oh.cite(f)}: undo session {m['landed']} landed; office deliver {n} closes the undo job")
            else:
                lines.append(f"{oh.cite(f)}: undo job waiting, bale's own commit {job['commit'][:7]} out of the "
                             f"workbench, {len(job['files'])} file(s); office start {n} --undo-bale sends the session")
        elif m["landed"]:
            lines.append(f"{oh.cite(f)}: merge session {m['landed']} landed; office deliver {n} makes the merge commit")
        else:
            lines.append(f"{oh.cite(f)}: merge job waiting, {job['audience']}/{job['branch']} into the workbench, "
                         f"{len(job['files'])} file(s); office start {n} --merge sends the session")
    return lines


def provisional_landed(office_root):
    """(lines, 0) for office status (0.31.0): one line for each folder,
    on the desk or in the filing cabinet, whose worked-out fields are still
    marked provisional though every session recorded in it landed applied,
    so its Structure never came back, or came back off its shape and was
    said at its land and not filed. Landed applied is bale's applied/SID
    tag in the office or a project it scopes, read with git alone (no bale
    call), and only when some folder could be such a one. A provisional
    line that does not read is folder-check's to name, not this. A repo
    that cannot be read is said when it leaves a folder undecided. Lines,
    never a refusal; nothing at all when no folder is one."""
    root = pathlib.Path(office_root)
    candidates = []
    for f in oh.read_folders(root):
        if f["problem"] or not f["sids"]:
            continue
        marked = f["fields"].get("provisional") or []
        if len(marked) != 1:
            continue
        try:
            names = oh.provisional_list(marked[0])
        except oh.HelperError:
            continue
        candidates.append((f, names))
    if not candidates:
        return [], 0
    places = []
    own = office_registry(root)
    if own is not None:
        places.append((OFFICE_LABEL, {"problem": None, "resolved": own}))
    places += [(p["name"], p) for p in office_projects(root) or []]
    # The repos on this machine first; a project on a host is asked (one
    # connection) only while a folder's sessions are not all found here.
    applied, unread = set(), []
    for label, p in sorted(places, key=lambda lp: hosted_project(lp[1])):
        if hosted_project(p) and all(all(s in applied for s in f["sids"]) for f, _ in candidates):
            break
        try:
            applied |= applied_sids(rendered(p))
        except BaleError as exc:
            unread.append(f"{label} ({exc})")
    lines = []
    for f, names in candidates:
        if all(sid in applied for sid in f["sids"]):
            n = len(f["sids"])
            lines.append(f"structure:  {oh.cite(f)} ({f['rel']}) still marks {', '.join(names)} provisional, though "
                         f"{'its one session' if n == 1 else f'all {n} of its sessions'} landed applied: its "
                         "Structure never came back, or came back off its shape and was not filed")
        elif unread:
            lines.append(f"structure:  {oh.cite(f)} ({f['rel']}) could not be judged: "
                         + "; ".join(unread) + " could not be read")
    return lines, 0


def status_lines(rd, office_root):
    """(lines, 0): office status's bale and projects lines. A bale
    outside the manifest's range is a line, never a refusal."""
    cons = rd.consumption
    try:
        exe = rd.bale()
        v = rd.installed_version()
        if oh.compare_versions(v, cons.floor) >= 0:
            bale = (f"bale:       {v} at {exe}; within the read side's range "
                    f"(bale {cons.floor} or later, share/{cons.path.name})")
        else:
            bale = (f"bale:       {v} at {exe}; OUTSIDE the read side's range: its reads were written "
                    f"against bale {cons.floor} or later (share/{cons.path.name}); it may fail on a key")
    except BaleError as exc:
        bale = f"bale:       {exc}"
    except oh.HelperError as exc:
        bale = f"bale:       its version could not be compared: {exc}"
    lines = [bale]
    projects = office_projects(office_root)
    if not projects:
        lines.append(f"projects:   none; {no_projects_line(projects)}")
        return lines, 0
    problems, hosted, paused, toolchain = [], [], [], []
    # In a container (0.54.0: the survey's Machine class), a project on this
    # machine is where bale's sandbox may not run, as on a host: its line.
    contained = machine_class(office_root) == "container"
    for p in projects:
        if p.get("paused") and not p["problem"]:
            # Read for nothing (0.41.0): no directory check, no host reached.
            paused.append(f"  {oh.paused_line(p['name'])}")
            continue
        if p["problem"]:
            ok, text = False, p["problem"]
        elif hosted_project(p):
            ok, text = True, ""
            hosted.append(p)
        else:
            ok, text = oh.check_project_dir(p["resolved"])
            if ok:
                # Its toolchain (0.53.0), read under bash -lc as bale's runs are.
                try:
                    toolchain += toolchain_lines(p["name"], ohost.toolchain_state(p["resolved"]))
                except ohost.HostError as exc:
                    toolchain.append(f"  {p['name']}: its toolchain could not be read: {exc}")
                if contained:
                    sandbox = sandbox_status_line(p, ohost.place_of(p))
                    if sandbox:
                        toolchain.append(sandbox)
        if not ok:
            problems.append(f"  {p['name']}: {text}")
    lines.append(f"projects:   {len(projects)} in scope"
                 + (f"; {len(problems)} cannot be read" if problems else "; each is a repo bale runs in"
                    + (f", {len(hosted)} through a host's shell" if hosted else ""))
                 + (f"; {len(paused)} paused" if paused else ""))
    lines += problems + paused + toolchain
    # A project on a host: one reach check, and that host's bale against
    # the read side's floor, with the remedy when it is behind. Never a
    # network call the survey makes (doctrine section 13): this is
    # status, and the line says what it found.
    try:
        here = rd.installed_version()
    except (BaleError, oh.HelperError):
        here = None
    for p in hosted:
        place = ohost.place_of(p)
        try:
            # bale's version and the sandbox setting there, in one connection
            # (0.39.0): the sandbox read rides after bale --version, and the
            # toolchain read (0.53.0) after it.
            proc, shown, where = rd.invoke("version", place, also=[ohost.sandbox_argv(place),
                                                                   ohost.toolchain_argv(place)])
            also = list(rd.also_runs)
            line = rd.parse("version", proc, shown, where)
            m = re.match(cons.surface("version")["pattern"], line)
            if not m:
                raise BaleError("output", f"bale --version printed {line!r}, not `bale X.Y.Z`")
            v = m.group(1)
            sandbox = sandbox_status_line(p, place, also[0] if also else None)
            if oh.compare_versions(v, cons.floor) >= 0:
                lines.append(f"  {p['name']}: {p['host']} answers; bale {v} there, within the read side's "
                             f"range (bale {cons.floor} or later)"
                             + (f"; this machine runs {here}, and {level_step(p['name'])} brings it level"
                                if here and oh.compare_versions(v, here) < 0 else ""))
            else:
                lines.append(f"  {p['name']}: {p['host']} answers; bale {v} on {p['host']} is older than the "
                             f"read side's floor {cons.floor}; {level_step(p['name'])} brings it level with "
                             f"this machine's bale{f' ({here})' if here else ''} before a session is sent there")
            if sandbox:
                lines.append(sandbox)
            if len(also) > 1:
                try:
                    lines += toolchain_lines(p["name"], ohost.read_toolchain(place, also[1]))
                except ohost.HostError as exc:
                    lines.append(f"  {p['name']}: its toolchain could not be read: {exc}")
        except BaleError as exc:
            lines.append(f"  {p['name']}: {exc}" if exc.kind == "unreachable"
                         else f"  {p['name']}: {p['host']} answers, but bale there could not be read: {exc}")
        except oh.HelperError as exc:
            lines.append(f"  {p['name']}: bale's version on {p['host']} could not be compared: {exc}")
    return lines, 0


def toolchain_lines(name, tc):
    """office status's lines on a project's toolchain (0.53.0), from what
    office_host.read_toolchain found where its clone is: one line for each
    tool package.json's engines (or a .nvmrc, for node) asks for that its
    shell finds missing or outside the range, and one for a range the
    office cannot read. A tool that meets its range is said under
    OFFICE_DEBUG only, as is an engines key the office does not ask a shell
    about (office_host.TOOLCHAIN_TOOLS). [] when the clone has neither file."""
    import json
    if tc.empty:
        return []
    out, needs = [], []
    if tc.package is not None:
        try:
            data = json.loads(tc.package)
        except json.JSONDecodeError as exc:
            return [f"  {name}: package.json does not read as JSON ({exc.msg}, line {exc.lineno}), so the office "
                    "cannot say what its scripts need"]
        engines = data.get("engines") if isinstance(data, dict) else None
        if engines is not None and not isinstance(engines, dict):
            out.append(f"  {name}: package.json engines is not a table of tools and ranges, so the office cannot "
                       "read it")
            engines = {}
        for tool, rng in (engines or {}).items():
            if tool not in ohost.TOOLCHAIN_TOOLS:
                debug(f"{name}: package.json engines names {tool} ({rng!r}), which the office does not ask a "
                      f"shell about (it asks for {', '.join(ohost.TOOLCHAIN_TOOLS)})")
                continue
            needs.append((tool, rng, "package.json engines", ohost.parse_range))
    if tc.nvmrc is not None:
        needs.append(("node", tc.nvmrc, ".nvmrc", ohost.nvmrc_range))
    for tool, rng, source, parse in needs:
        shown = rng if isinstance(rng, str) else json.dumps(rng)
        try:
            wanted = parse(rng)
        except ohost.RangeError:
            out.append(f"  {name}: {source} says {tool} {json.dumps(shown)}, which the office cannot read as a "
                       "range, so it does not say whether its shell's meets it")
            continue
        if tool not in tc.found:
            debug(f"{name}: {tool} was not asked of its shell ({source} names it, but the read did not find "
                  f"\"{tool}\" in package.json)")
            continue
        printed = tc.found[tool]
        if printed is None:
            out.append(f"  {name}: needs {tool} {shown} ({source}); its shell finds no {tool}")
            continue
        version = ohost.found_version(printed)
        if version is None:
            out.append(f"  {name}: needs {tool} {shown} ({source}); its shell's {tool} --version printed "
                       f"{json.dumps(printed)}, which names no version")
        elif not ohost.satisfies(version, wanted):
            out.append(f"  {name}: needs {tool} {shown} ({source}); its shell finds {tool} "
                       f"{'.'.join(map(str, version))}")
        else:
            debug(f"{name}: needs {tool} {shown} ({source}); its shell finds {tool} "
                  f"{'.'.join(map(str, version))}, which meets it")
    return out


SURVEY_PAGE = "floor-plan/survey.md"


def machine_class(office_root):
    """The survey's `## Machine` class (`WSL`, `container`, or a host's
    words), or None when the survey is not there or names none: office
    status reads the page office survey wrote, and never surveys."""
    path = pathlib.Path(office_root) / SURVEY_PAGE
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        debug(f"the survey could not be read for the machine's class, so none is assumed: {exc}")
        return None
    return oh.facts_from_page(text).get("machine.class")


def sandbox_status_line(project, place, run=None):
    """office status's line on bale's sandbox for a hosted project (0.39.0),
    or None when there is nothing to say: the setting the office wrote
    (`sandbox: off by bale.toml, written DAY: WHY`), or, where bale's
    sandbox cannot run and bale.toml does not turn it off, the step that
    writes it. run is the sandbox read's Run when it rode another call;
    a read that fails is a line. Since 0.54.0 it is said of a project on
    this machine too when this machine is a container, in the same words,
    the host's name standing as `this machine`."""
    name = project["name"]
    try:
        written, table, refuses, said = (ohost.read_sandbox(place, run) if run is not None
                                         else ohost.sandbox_state(place))
    except ohost.HostError as exc:
        return f"  {name}: sandbox: the setting could not be read: {exc}"
    if written:
        return f"  {name}: sandbox: off by bale.toml, written {written}"
    if refuses and not table:
        return (f"  {name}: sandbox: bale's sandbox cannot run on {place.host if place.hosted else 'this machine'} "
                f"({said or 'the probe refused'}) and "
                f"bale.toml does not turn it off, so every apply there asks; office projects set {name} --prepare "
                "writes the setting")
    return None


# --- sending a session out: office start -------------------------------------------
#
# The office runs bale's pack when the occupant asks (the ruling of
# sitting 2026-09-29-continue-plan-002, fourth page): it is the
# occupant's hands at the terminal. It never schedules, never dispatches
# to a model and never carries pastes. What it does here: checks the
# planned forecast against the sessions open where the pack will run,
# makes every context tarball that rides beside the request, packs the
# session, and gathers every file the occupant attaches into one out
# tray. Context packs come first, because they open nothing: a failure
# there leaves no session open.

# The constraint every project session an office packs carries
# (doctrine section 2), verbatim.
PROJECT_CONSTRAINT = "Office context informs this session but never lands in this project."


class StartError(Exception):
    """office start cannot go on, said as lines a person can act on."""

    def __init__(self, lines):
        super().__init__("\n".join(lines))
        self.lines = lines


def forecast_overlap(mine, theirs):
    """The entries of two forecasts that overlap: equal, or one a
    directory holding the other. None stands for the whole tree (a pack
    with no --write and no --include); [] overlaps nothing."""
    def norm(e):
        return e.strip().strip("/")
    if mine is None and theirs is None:
        return ["the whole tree"]
    if mine is None:
        return [norm(t) for t in theirs]
    if theirs is None:
        return [norm(m) for m in mine]
    out = []
    for m in mine:
        for t in theirs:
            a, b = norm(m), norm(t)
            if a in ("", ".") or b in ("", ".") or a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                out.append(a if len(a) >= len(b) else b)
    return sorted(set(out))


def open_overlaps(rd, cwd, mine):
    """[(sid, their forecast, overlapping entries)] for the sessions open
    in the repo at cwd whose recorded forecast overlaps mine. A repo bale
    has never run in has no registry and nothing open."""
    # bale status answers in a repo it has never run in, too; on this
    # machine the office skips the call when there is no registry.
    if not rd.hosted(cwd) and not (pathlib.Path(cwd) / ".bale").is_dir():
        return []
    st = rd.status(cwd)
    scopes = rd.key(st, "status", "scopes") or {}
    out = []
    for sid in rd.key(st, "status", "sessions") or []:
        theirs = scopes.get(sid)
        if theirs == []:
            continue
        hit = forecast_overlap(mine, theirs)
        if hit:
            out.append((sid, theirs, hit))
    return out


def opener_lines(stderr_lines, spec):
    """The paste-ready opener bale prints between its scissor lines, the
    lines bale itself asks a person to copy; None when bale printed no
    such block. The --json report carries no opener (a slip for
    bale-src), so these markers, declared in the consumption manifest,
    are the one place it is found."""
    begin, end = spec["opener"]
    try:
        a = stderr_lines.index(begin)
        b = stderr_lines.index(end, a + 1)
    except ValueError:
        return None
    return stderr_lines[a + 1:b]


def git_top(path):
    """The top of the git work tree holding path, or None."""
    import subprocess
    p = pathlib.Path(path)
    where = p if p.is_dir() else p.parent
    try:
        proc = subprocess.run(["git", "-C", str(where), "rev-parse", "--show-toplevel"],
                              capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return pathlib.Path(proc.stdout.strip()).resolve() if proc.returncode == 0 else None


def ride_plan(path):
    """How one ride-along reaches the out tray: ("pack", directory,
    include or None) for a context pack run in that directory, or
    ("copy", path, None) for a file outside any repo, copied as it is.
    A directory outside git is packed from a scratch copy ("scratch"),
    so the office writes nothing into it; a path inside a repo is packed
    from the repo's top with --include, whose outbox .bale/ ignores."""
    p = pathlib.Path(path).resolve()
    if not p.exists():
        raise StartError([f"a declared ride-along is not on this machine: {path} "
                          "(office projects set changes what rides)"])
    top = git_top(p)
    if top is None:
        return ("copy", p, None) if p.is_file() else ("scratch", p, None)
    if p == top:
        return ("pack", top, None)
    return ("pack", top, str(p.relative_to(top)))


# --- what rides from a project's host, and the clone's branch (0.50.0) ----------

# The clone's checked-out branch, read where the clone is: the short name,
# or nothing (exit 1) on a detached HEAD.
BRANCH_ARGV = ["git", "symbolic-ref", "--short", "-q", "HEAD"]


def clone_branch_line(project, where, run):
    """The line start's screen says for every project session, before the
    pack: the branch the session builds on (deliver squashes what the
    clone's branch holds since it left the base). None when the read
    failed for a reason other than a detached HEAD, said by the caller."""
    if run.returncode == 0 and run.stdout.strip():
        return f"{project}'s clone at {where} is on {run.stdout.strip()}"
    if run.returncode == 1 and not run.stdout.strip():
        return f"{project}'s clone at {where} is on a detached HEAD"
    return None


def say_clone_branch(project, where, run):
    """Say the clone's branch (log, so start's screen shows it), or why it
    could not be read: never a silent skip, never a refusal."""
    line = clone_branch_line(project, where, run)
    if line is None:
        line = (f"{project}'s clone at {where}: its branch could not be read (git symbolic-ref exited "
                f"{run.returncode}: {ohost._last_words(run.stderr)})")
    log(line)
    return line


def read_host_rides(place, host_rides, run):
    """The facts of each host ride, from the round's run, as (stored,
    fact) pairs; a ride gone from the host stops the start here, before
    anything is written, as one gone from this machine does."""
    try:
        rows = ohost.read_ride_facts(run, [oh.host_ride_path(r) for r in host_rides], place)
    except ohost.HostError as exc:
        raise StartError([f"{place.name or place.host}: {exc}; nothing was written"])
    gone = [r for r, f in zip(host_rides, rows) if f["kind"] == "gone"]
    if gone:
        raise StartError([f"a declared ride-along is not on {place.host}: {g} (office projects set changes what "
                          "rides); nothing was written" for g in gone])
    pairs = list(zip(host_rides, rows))
    for line in ride_size_lines(place, pairs):
        log(line)
    return pairs


# A directory outside git rides from the host as a full copy into a
# scratch there, packed by the host's bale (0.50.0); one past this many
# KiB is said as large on start's screen (0.54.0), with the flag that
# leaves it home this once. Nothing is refused: bale's own caps decide what
# of it the context tarball holds.
RIDE_LARGE_KB = 256 * 1024


def size_words(kb):
    """KiB as a person reads a size: 812 KiB, 41.2 MiB, 3.1 GiB."""
    if kb < 1024:
        return f"{kb} KiB"
    if kb < 1024 * 1024:
        return f"{kb / 1024:.1f} MiB"
    return f"{kb / (1024 * 1024):.1f} GiB"


def ride_size_lines(place, pairs, large=RIDE_LARGE_KB):
    """start's lines (0.54.0) for each host ride that is a directory
    outside git, said before anything is copied: its size, read by the
    same round that read its facts; above large, that it is large and the
    --leave-out that keeps it home this once. A size du could not give is
    said as unknown, never guessed."""
    out = []
    for stored, fact in pairs:
        if fact["kind"] != "dir" or fact["top"] is not None:
            continue
        kb = fact.get("kb")
        if kb is None:
            out.append(f"{stored} is a directory outside git on {place.host}, copied whole into a scratch there "
                       "for its pack; its size could not be read there (du said nothing)")
        elif kb > large:
            out.append(f"{stored} is {size_words(kb)}, a directory outside git on {place.host}: LARGE (over "
                       f"{size_words(large)}), and the whole of it is copied into a scratch there before its pack, "
                       f"so this start takes a while; --leave-out {shell_quote(stored)} leaves it home this once "
                       "(nothing is refused: bale's own caps decide what of it rides)")
        else:
            out.append(f"{stored} is {size_words(kb)}, a directory outside git on {place.host}, copied whole into "
                       "a scratch there for its pack")
    return out


def pack_host_rides(rd, tray, place, rows, project):
    """Pack what rides from the project's host there, with the host's own
    bale (bale pack --context, so bale's filters keep secrets and junk
    out), and carry each tarball back into the tray as the request is
    carried: a path inside a repo there from the repo's top with
    --include (one pack per repo, as here), a directory outside git from
    a scratch copy there (removed in the connection that fetches its
    tarball, and on any failure), a file outside git fetched as it is.
    Every pack travels in one connection. Returns the carried lines."""
    import tempfile
    plans = [(stored, ohost.ride_plan_there(fact)) for stored, fact in rows]
    grouped, scratches, copies = {}, [], []
    for stored, (kind, where, inc) in plans:
        if kind == "pack":
            grouped.setdefault(where, []).append((stored, inc))
        elif kind == "scratch":
            scratches.append((stored, where))
        else:
            copies.append((stored, where))
    argvs = [ohost.bale_in_argv(top, rd.consumption.argv("context", includes=(None if any(i is None for _, i in got)
                                                                               else [i for _, i in got])))
             for top, got in grouped.items()]
    argvs += [ohost.ride_scratch_argv(d, rd.consumption.argv("context", includes=None)) for _, d in scratches]
    made = []  # the scratches made there, removed whatever happens
    carried = []
    try:
        runs = rd.through_shell(place, argvs, PACK_TIMEOUT) if argvs else []
        made += [m for m in (ohost.scratch_said(r) for r in runs[len(grouped):]) if m]
        reports = []
        for run, what in zip(runs, [*[g for g in grouped], *[d for _, d in scratches]]):
            shown = "bale " + " ".join(rd.consumption.argv("context"))
            if run.returncode != 0:
                raise BaleError("refused", f"{shown} refused for {what} on {place.host} (exit {run.returncode}): "
                                           f"{ohost._last_words(run.stderr)}")
            reports.append(rd.parse("context", run, shown, f"{what} on {place.host}"))
        with tempfile.TemporaryDirectory(prefix="office-rides-") as tmp:
            for i, (top, got) in enumerate(grouped.items()):
                report = reports[i]
                name = f"context-{rd.key(report, 'context', 'tree_name')}.tar.gz"
                here = pathlib.Path(tmp) / f"{i}-{name}"
                ohost.fetch_file(place, rd.key(report, "context", "tarball"), str(here))
                carried.append(f"{tray.take(here, name)}: rides with {project} "
                               f"({', '.join(r for r, _ in got)}, packed on {place.host})")
            for j, (stored, d) in enumerate(scratches):
                report = reports[len(grouped) + j]
                name = f"context-{rd.key(report, 'context', 'tree_name')}.tar.gz"
                here = pathlib.Path(tmp) / f"s{j}-{name}"
                scratch = ohost.scratch_said(runs[len(grouped) + j])
                gone = ohost.Scratch(place)
                gone._path = scratch
                ohost.fetch_file(place, rd.key(report, "context", "tarball"), str(here),
                                 after=gone.removal_words() if scratch else None)
                if scratch in made:
                    made.remove(scratch)
                carried.append(f"{tray.take(here, name)}: rides with {project} ({stored}, packed on {place.host} "
                               "from a copy there)")
            for k, (stored, f) in enumerate(copies):
                name = posix_name(f)
                here = pathlib.Path(tmp) / f"c{k}-{name}"
                ohost.fetch_file(place, f, str(here))
                carried.append(f"{tray.take(here, name)}: rides with {project} ({stored}, carried from "
                               f"{place.host} as it is)")
    finally:
        for left in made:
            try:
                ohost.remove_scratch(place, left)
            except ohost.HostError as exc:
                log(f"warning: the temporary directory {left} on {place.host} was left behind: {exc}")
    return carried


def posix_name(path):
    """The last part of a path as a host's shell sees it."""
    return pathlib.PurePosixPath(path).name


class Tray:
    """The out tray being filled: a staging directory beside its final
    place, renamed to the session id once the session is packed."""

    def __init__(self, root):
        import tempfile
        self.root = pathlib.Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix=".filling-", dir=self.root))
        self.files = []

    def take(self, src, name=None):
        import shutil
        name = name or pathlib.Path(src).name
        stem, dot, ext = name.partition(".")
        n = 1
        while (self.dir / name).exists():
            n += 1
            name = f"{stem}-{n}{dot}{ext}"
        shutil.copy2(src, self.dir / name)
        self.files.append(name)
        # Within office start (START_RUNNING) the tray's path and its files
        # are said once, below (0.46.0), so each file's line is a debug line
        # there, piped too since 0.55.0.
        (debug if os.environ.get("START_RUNNING") == "1" else log)(f"out tray: {name}")
        return name

    def finish(self, sid):
        """Name the tray for the session. bale's ids are unique within
        one repo only, so a tray already named so (the same folder's
        session in another repo, the same day) gets the next free
        name rather than failing a session that is already open."""
        final, n = self.root / sid, 1
        while final.exists():
            n += 1
            final = self.root / f"{sid}-{n}"
        self.dir.rename(final)
        self.dir = final
        return final

    def discard(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)


def context_into_tray(rd, tray, directory, includes, what, name=None):
    """One context pack in directory, its tarball copied into the tray
    (as name, when given)."""
    report, _ = rd.pack("context", directory, includes=includes or None)
    tarball = rd.key(report, "context", "tarball")
    name = tray.take(tarball, name or f"context-{rd.key(report, 'context', 'tree_name')}.tar.gz")
    return f"{name}: {what}"


def scratch_context(rd, tray, source, what, name=None):
    """A context pack of a directory outside git, made from a scratch
    copy under the same name, so nothing is written into the original
    (the install's doctrine directory among them)."""
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory(prefix="office-start-") as tmp:
        copy = pathlib.Path(tmp) / pathlib.Path(source).name
        shutil.copytree(source, copy, ignore=shutil.ignore_patterns(".bale", "__pycache__"))
        return context_into_tray(rd, tray, copy, None, what, name)


def install_version_here():
    """The install's VERSION, for a line that names it."""
    try:
        return (INSTALL / "VERSION").read_text(encoding="utf-8").splitlines()[0].strip()
    except (OSError, IndexError):
        return "of unknown version"


def ride_choice(entry, project, leave_out):
    """(rides, left out) for a session: the project's declared ride-alongs
    minus the ones named to stay home this once. A name matches a
    declaration as declared or by the path it resolves to; a name that
    matches none refuses, naming what is declared. A ride on the project's
    host (host:PATH, 0.50.0) resolves nowhere here, so it matches as
    declared (a trailing slash aside), never by a path on this machine."""
    declared = list(entry["rides"]) if entry is not None else []
    if not leave_out:
        return declared, []
    if not declared:
        raise StartError([f"--leave-out {leave_out[0]}: nothing rides with {project or 'this session'}, "
                          "so there is nothing to leave out"])
    left = []
    for want in leave_out:
        try:
            want_path = None if oh.is_host_ride(want) else pathlib.Path(os.path.expanduser(want)).resolve()
        except (OSError, RuntimeError):
            want_path = None
        hit = [r for r in declared if r == (want.rstrip("/") or "/")
               or (want_path is not None and not oh.is_host_ride(r)
                   and oh.expand_project_path(r).resolve() == want_path)]
        if not hit:
            raise StartError([f"--leave-out {want}: not one of what rides with {project} "
                              f"({', '.join(declared)}); office projects {project} lists them"])
        left += [h for h in hit if h not in left]
    return [r for r in declared if r not in left], left


def bundle_pack_argv(bundle):
    """The pack argv a planner bundle stores, when the bundle is a file
    the office can read here (a bare name bale's own search finds is
    not), else None. The office reads it only to say what the bundle
    does; it never adds to it."""
    import json
    import tarfile
    p = pathlib.Path(bundle)
    if not p.is_file():
        return None
    try:
        with tarfile.open(p) as t:
            member = t.extractfile("bundle.json")
            argv = json.loads(member.read().decode("utf-8")).get("pack_argv") if member else None
    except (OSError, KeyError, tarfile.TarError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        debug(f"could not read the pack argv of {p}: {exc}")
        return None
    return argv if isinstance(argv, list) and all(isinstance(a, str) for a in argv) else None


class _ArgvParser(argparse.ArgumentParser):
    """argparse that raises instead of printing and exiting."""

    def error(self, message):
        raise ValueError(message)


def bundle_argv_parts(argv):
    """The parsed pack argv (argparse namespace) of a bundle, read the way
    bale pack reads its flags (bale help pack). Raises ValueError when it
    does not read as a pack line."""
    ap = _ArgvParser(prog="bale pack", add_help=False, allow_abbrev=False)
    ap.add_argument("goal", nargs="?")
    for flag in ("--include", "--write", "--exclude"):
        ap.add_argument(flag, nargs="+", action="append", default=[])
    for flag in ("--slug", "--constraint", "--out-of-scope", "--expects-probe", "--packer", "--work-class",
                 "--supersedes", "--no-include-group", "--max-files", "--max-size", "--max-depth",
                 "--readme-file", "--checkpoint-file"):
        ap.add_argument(flag, action="append", default=[])
    for flag in ("--context", "--edit", "--no-edit", "--no-readme", "--allow-checkpoint-in-scope", "--read-only",
                 "--force", "--verbose", "--json", "--dry-run"):
        ap.add_argument(flag, action="store_true")
    return ap.parse_args(list(argv))


def bundle_paths(argv):
    """(includes, writes, excludes) a bundle's pack argv names, each a
    list of paths relative to the repo it opens in."""
    a = bundle_argv_parts(argv)
    flat = lambda groups: [p for group in groups for p in group]  # noqa: E731
    return flat(a.include), flat(a.write), flat(a.exclude)


def bundle_forecast(argv):
    """(forecast, supersedes) from a bundle's stored pack argv, read the
    way bale pack reads its flags (bale help pack): --write's paths, else
    --include's, else None for the whole tree; [] for --read-only.
    --write and --include take several paths per flag and repeat.
    supersedes is the session a split supersession closes (bale clears
    that one collision), or None. Raises ValueError when the argv does
    not read as a pack line, and the office then says it is passing
    bale's own words through."""
    a = bundle_argv_parts(argv)
    supersedes = a.supersedes[-1] if a.supersedes else None
    if a.read_only:
        return [], supersedes
    writes = [p for group in a.write for p in group]
    includes = [p for group in a.include for p in group]
    return (writes or includes or None), supersedes


def bundle_places(office_root, paths, rd=None):
    """[(label, directory, missing paths)] for every place a bundle could
    open in: the office, then each project it scopes that can be read,
    by name. A place whose missing list is empty holds every path. A
    hosted place this reader's round already asked answers from it."""
    root = pathlib.Path(office_root).resolve()
    out = [("office", root, [x for x in paths if not (root / x.strip("/")).exists()])]
    for p in office_projects(root) or []:
        if p["problem"]:
            continue
        if hosted_project(p):
            # A hosted project's tree is on its host, and answers through
            # its shell (one connection each); one that does not answer
            # holds nothing, as far as the office can tell, and says so.
            place = ohost.place_of(p)
            key = (place, "missing", tuple(x for x in dict.fromkeys(paths) if x))
            if rd is not None and key in rd.facts:
                out.append((p["name"], place, list(rd.facts[key])))
                continue
            try:
                out.append((p["name"], place, ohost.missing_paths(place, paths) if paths else []))
            except ohost.HostError as exc:
                log(f"warning: {p['name']} could not be asked which of the bundle's paths it holds: {exc}")
            continue
        if p["resolved"] is not None and p["resolved"].is_dir():
            d = p["resolved"]
            out.append((p["name"], d, [x for x in paths if not (d / x.strip("/")).exists()]))
    return out


def bundle_where(office_root, bundle, lane=None):
    """Where a bundle opens by default, for office start's where question:
    (default, why), or None when the office cannot read the bundle's pack
    line (a bare name bale's search finds), so the lane's default stands.
    The default is the one place whose tree holds every path the bundle's
    pack line names; when several do, the lane's project, else the office.
    Raises StartError, before bale runs, when no one place holds them all,
    naming the paths and where each is (or that it is nowhere)."""
    argv = bundle_pack_argv(bundle)
    if argv is None:
        return None
    try:
        includes, writes, _ = bundle_paths(argv)
    except ValueError:
        return None
    paths = list(dict.fromkeys(includes + writes))
    places = bundle_places(office_root, paths)
    holders = [label for label, _, missing in places if not missing]
    named = ", ".join(paths)
    if not holders:
        raise StartError(bundle_nowhere_lines(bundle, paths, places))
    if len(holders) == 1:
        where = holders[0]
        return where, (f"every path the bundle names ({named}) is in {place_words(where)}'s tree, and in no other "
                       "place the office scopes")
    pick = lane if lane in holders else ("office" if "office" in holders else holders[0])
    what = f"every path the bundle names ({named})" if paths else "the bundle names no path, so the whole tree, and it"
    because = "the folder's lane names it" if pick == lane else (
        "the folder's lane names no place that holds them" if lane else "the folder's lane names no project")
    return pick, (f"{what} is in several places ({', '.join(place_words(h) for h in holders)}); "
                  f"{place_words(pick)}, because {because}")


def place_words(label):
    return "the office" if label == "office" else label


def bundle_brief(bundle):
    """The brief a planner bundle carries (its planner's member, named in
    bundle.json's members.brief.path), as text; None when the bundle is
    not a file here, carries no brief, or cannot be read (said under
    OFFICE_DEBUG). The office reads it only for the LANDS line."""
    import json
    import tarfile
    p = pathlib.Path(bundle) if bundle else None
    if p is None or not p.is_file():
        return None
    try:
        with tarfile.open(p) as t:
            member = t.extractfile("bundle.json")
            meta = json.loads(member.read().decode("utf-8")) if member else {}
            brief = (meta.get("members") or {}).get("brief")
            rel = brief.get("path") if isinstance(brief, dict) else None
            if not isinstance(rel, str) or not rel:
                return None
            data = t.extractfile(rel)
            return data.read().decode("utf-8", "backslashreplace") if data else None
    except (OSError, KeyError, tarfile.TarError, json.JSONDecodeError, UnicodeDecodeError, AttributeError) as exc:
        debug(f"could not read the brief of {p}: {exc}")
        return None


def bundle_lands(office_root, bundle, machine_file=None):
    """Where a planner's bundle says its session lands, from the LANDS line
    its brief carries (0.24.0; office_helper.brief_lands): a dict with
    place (office, or a project's name), project (the name, or None for
    the office), folder (the desk folder's directory name, or "new") and
    words (one line saying where it lands and in which folder), each None
    when that half cannot be taken; and said, the lines that say why a
    half cannot (a line that does not read, a project the office does not
    scope, a folder it does not hold on the desk), so its question comes
    back alone; and branch (0.34.0), the branch the brief's BRANCH line
    names for the session to build on, or None. absent is True when the
    brief carries no LANDS line and no BRANCH line at all, or the bundle
    cannot be read here."""
    out = {"absent": False, "place": None, "project": None, "folder": None, "folder_words": None,
           "words": None, "said": [], "branch": None, "rides": None, "elsewhere": [], "nowhere": False,
           "lands_on": None}
    name = pathlib.Path(bundle).name
    text = bundle_brief(bundle)
    if text is None:
        out["absent"] = True
        return out
    # The branch the session builds on (0.34.0, office_helper.brief_branch):
    # read beside the LANDS line, since office start acts on both before
    # bale is asked anything.
    out["branch"], branch_problems = oh.brief_branch(text)
    out["said"] += [f"the bundle {name}'s brief: {p}" for p in branch_problems]
    # The riders the session carries (0.44.0, office_helper.brief_rides).
    out["rides"], rides_problems = oh.brief_rides(text)
    out["said"] += [f"the bundle {name}'s brief: {p}" for p in rides_problems]
    mark, problems = oh.brief_lands(text)
    out["said"] += [f"the bundle {name}'s brief: {p}" for p in problems]
    if mark is None:
        out["absent"] = not problems and not branch_problems and out["branch"] is None and out["rides"] is None \
            and not rides_problems
        return out
    root = pathlib.Path(office_root)
    names = [p["name"] for p in office_projects(root) or []]
    if mark["place"] == "office":
        out["place"] = "office"
    elif mark["place"] in names:
        out["place"], out["project"] = "project", mark["place"]
    elif machine_file is not None:
        # Not a refusal (0.44.0): the office that scopes it is named, from
        # machine.toml's offices and each one's floor plan, or that none on
        # this machine does.
        import office_home as hs
        others, _ = hs.other_offices(root, machine_file)
        out["lands_on"] = mark["place"]
        out["elsewhere"] = [(r, n) for r, n in others if mark["place"] in hs.scoped_by(r)]
        out["nowhere"] = not out["elsewhere"]
    else:
        out["said"].append(f"the bundle {name}'s brief says it lands on {mark['place']}, which this office does not "
                           f"scope (it scopes: {', '.join(names) or 'no project'}); where it lands is asked")
    if mark["folder"] == "new":
        out["folder"], out["folder_words"] = "new", "a new folder, opened from the bundle's goal"
    else:
        found = [f for f in oh.read_folders(root) if f["problem"] is None and f.get("number") == mark["folder"]]
        desk = [f for f in found if f["space"] == "desk"]
        if desk:
            f = desk[0]
            out["folder"] = f["name"]
            out["folder_words"] = f"{oh.cite(f)}, {f.get('title') or f['name']} (desk/{f['name']})"
        elif found:
            out["said"].append(f"the bundle {name}'s brief names folder {mark['folder']}, which is in the filing cabinet "
                               f"(filing-cabinet/{found[0]['name']}; office reopen {found[0]['name']} brings it back); "
                               "which job is asked")
        else:
            out["said"].append(f"the bundle {name}'s brief names folder {mark['folder']}, which this office does not "
                               "hold; which job is asked")
    if out["place"] and out["folder"]:
        where = "in the office" if out["place"] == "office" else f"on {out['project']}"
        out["words"] = f"the bundle's brief says where it lands: {where}, recorded in {out['folder_words']}"
    return out


def bundle_nowhere_lines(bundle, paths, places, chosen=None):
    """Why a bundle cannot open where it was sent: each path it names that
    the chosen place (or every place) lacks, and where it is instead."""
    lines = []
    name = pathlib.Path(bundle).name
    holders = {x: [label for label, _, missing in places if x not in missing] for x in paths}
    nowhere = [x for x in paths if not holders[x]]
    if chosen is None:
        lines.append(f"the bundle {name} names paths no one place the office can see holds, so bale would refuse it "
                     "wherever it opened; nothing ran")
    for x in paths:
        if chosen is not None and chosen in holders[x]:
            continue
        where = ", ".join(place_words(h) for h in holders[x]) if holders[x] else "nowhere the office can see"
        lines.append(f"  {x}: in {where}")
    if nowhere:
        lines.append(f"{', '.join(nowhere)} exist{'s' if len(nowhere) == 1 else ''} in neither the office nor any "
                     "project it scopes; ask the planner for a bundle whose paths exist here")
    return lines


DOCTRINE_IGNORE = ("__pycache__", ".bale")


def doctrine_files(directory):
    """{relative path: bytes} of a doctrine directory, caches aside."""
    d = pathlib.Path(directory)
    out = {}
    for f in sorted(d.rglob("*")):
        rel = f.relative_to(d)
        if f.is_file() and not any(part in DOCTRINE_IGNORE for part in rel.parts):
            out[str(rel)] = f.read_bytes()
    return out


def ships(path, includes, excludes=()):
    """Does a pack with these includes (None: the whole tree) and
    excludes ship the path? An entry holds the path when it is the path
    or a directory above it."""
    holds = lambda e, p: (e.strip("/") in ("", ".") or p == e.strip("/")  # noqa: E731
                          or p.startswith(e.strip("/") + "/"))
    if any(holds(e, path) for e in excludes):
        return False
    return includes is None or any(holds(e, path) for e in includes)


def doctrine_in_tree(tree, includes, excludes=()):
    """The doctrine directory a packed tree ships beside the install's,
    or None: tree/doctrine/OFFICE.md, when the pack's includes reach it
    (office-src itself is the case): every file of it, not only
    OFFICE.md, since the install's copy stays home on the strength of it."""
    if tree is None:
        return None
    d = pathlib.Path(tree) / "doctrine"
    if not (d / "OFFICE.md").is_file():
        return None
    # Every file of it, or the session would lack the rest (its checks)
    # if the install's copy stayed home.
    return d if all(ships(f"doctrine/{rel}", includes, excludes) for rel in doctrine_files(d)) else None


# The doctrine a hosted tree holds, as sha256 sums: one line per file,
# caches aside, nothing when the tree has no doctrine/.
_DOCTRINE_SUMS = ('[ -d doctrine ] || exit 0; cd doctrine && find . -type f ! -path "*/__pycache__/*" '
                  '! -path "*/.bale/*" | LC_ALL=C sort | while IFS= read -r f; do sha256sum "$f"; done')


def doctrine_sums(tree, includes, excludes=(), rd=None):
    """{relative path: sha256} of the doctrine a packed tree ships, here
    or on a host (read through its shell, unless this reader's hosted
    round already read it), or None: the same answer doctrine_in_tree
    gives, as sums, so a hosted tree's doctrine is compared with the
    install's without its bytes travelling."""
    if tree is None:
        return None
    if isinstance(tree, ohost.Place) and tree.hosted:
        run = rd.facts.get((tree, "doctrine")) if rd is not None else None
        if run is None:
            run = ohost.run_in(tree, ["sh", "-c", _DOCTRINE_SUMS])
        if run.returncode != 0:
            raise BaleError("refused", f"the doctrine in {tree} could not be read: {run.stderr.strip() or run.returncode}")
        sums = {}
        for line in run.stdout.splitlines():
            sha, _, rel = line.partition("  ")
            if re.fullmatch(r"[0-9a-f]{64}", sha) and rel.startswith("./"):
                sums[rel[2:]] = sha
    else:
        d = doctrine_in_tree(tree, includes, excludes)
        return None if d is None else install_doctrine_sums(d)
    if "OFFICE.md" not in sums:
        return None
    return sums if all(ships(f"doctrine/{rel}", includes, excludes) for rel in sums) else None


def install_doctrine_sums(directory=None):
    import hashlib
    return {rel: hashlib.sha256(data).hexdigest()
            for rel, data in doctrine_files(directory or INSTALL / "doctrine").items()}


# --- the doctrine a sitting went out under (0.33.0) ------------------------------
#
# office start stamps it in two places: one line in the sitting's brief (the
# planner sitting's and a meeting's prep, from the install's templates) and
# the folder's Sessions line (office_helper.sitting_words). The walk-in's In
# flight, the home screen's sitting item and office status say, in one line,
# when a sitting is out under a doctrine that is not the install's; nothing
# refuses, since the sitting may finish on the doctrine it read.

def install_doctrine_hash(directory=None):
    """The sha256 of the install's doctrine/OFFICE.md, as the doctrine
    rides (the same bytes install_doctrine_sums, and so the rides-once
    check, reads), or None when the install holds no OFFICE.md."""
    return install_doctrine_sums(directory).get("OFFICE.md")


def doctrine_brief_words(folder=True):
    """The value of a sitting's brief's doctrine line (the templates'
    `- the doctrine it goes out under:` field): the full hash and the
    release, then, for a sitting a folder records (folder), where the short
    hash is kept and what the walk-in does with it. None, said, when the
    install's OFFICE.md cannot be read: the field line is then left out of
    the brief, as an unset field line is."""
    try:
        sha = install_doctrine_hash()
    except OSError as exc:
        log(f"warning: the install's doctrine could not be read, so the brief carries no doctrine line: {exc}")
        return None
    if not sha:
        log(f"warning: the install at {INSTALL} holds no doctrine/OFFICE.md, so the brief carries no doctrine line")
        return None
    words = f"OFFICE.md sha256 {sha} (office-src {install_version_here()}), the doctrine that rides with it"
    if folder:
        words += (f"; the folder's Sessions line keeps {oh.doctrine_short(sha)}, and the walk-in says so when "
                  "the install's doctrine changes while the sitting is out")
    return words


def session_doctrines(office_root):
    """sid -> the short doctrine hash its Sessions line stamps, across the
    desk and the filing cabinet; a folder that cannot be read is said under
    OFFICE_DEBUG and skipped, as the walk-in's other reads of it are."""
    out = {}
    for space in ("desk", "filing-cabinet"):
        for md in sorted((pathlib.Path(office_root) / space).glob("*/folder.md")):
            try:
                lines = oh.folder_session_lines(md)
            except (OSError, UnicodeDecodeError) as exc:
                debug(f"{space}/{md.parent.name}/folder.md cannot be read for its sittings' doctrine: {exc}")
                continue
            for sid, words in lines:
                short = oh.session_doctrine(words)
                if short:
                    out.setdefault(sid, short)
    return out


class Doctrines:
    """The install's doctrine hash and the stamps the folders hold, each
    read once, when first asked: older(sid) is the one line said of a
    sitting out under another doctrine, or None (the install's, or no
    stamp: a sitting from before 0.33.0 is not compared)."""

    def __init__(self, office_root, install=None):
        self.office_root = office_root
        self._install = install
        self._stamps = None

    @property
    def install(self):
        if self._install is None:
            try:
                self._install = install_doctrine_hash() or ""
            except OSError as exc:
                debug(f"the install's doctrine could not be read, so no sitting's is compared with it: {exc}")
                self._install = ""
        return self._install

    def older(self, sid):
        if self._stamps is None:
            self._stamps = session_doctrines(self.office_root)
        return self.older_stamp(self._stamps.get(sid))

    def older_stamp(self, stamped):
        """The one line for a sitting stamped with this short hash (a
        prep's record line carries its own, 0.43.0), or None."""
        if not stamped or not self.install or stamped == oh.doctrine_short(self.install):
            return None
        return oh.older_doctrine_words(stamped, self.install)


def doctrine_lines(rd, office_root):
    """(lines, 0): office status's doctrine line, the install's OFFICE.md
    by its short hash and release, then one line for each read-only sitting
    open in the office whose Sessions line stamps another doctrine, and
    (0.55.0) for each meeting's prep out whose record line does, as a
    folder's sitting's is compared. bale is asked which sessions are open
    only when a folder or a prep stamps another one."""
    import office_meeting as om
    try:
        install = install_doctrine_hash()
    except OSError as exc:
        return [f"doctrine:   the install's doctrine/OFFICE.md could not be read: {exc}"], 0
    if not install:
        return [f"doctrine:   the install at {INSTALL} holds no doctrine/OFFICE.md"], 0
    head = f"doctrine:   OFFICE.md {oh.doctrine_short(install)}, the install's (office-src {install_version_here()})"
    other = {sid: s for sid, s in session_doctrines(office_root).items() if s != oh.doctrine_short(install)}
    try:
        preps = {r["sid"]: r for r in om.read_record(office_root)
                 if r["state"] == "prep out" and r.get("doctrine") and r["doctrine"] != oh.doctrine_short(install)}
    except (OSError, UnicodeDecodeError) as exc:
        debug(f"the calendar's record could not be read for the preps' doctrine: {exc}")
        preps = {}
    for sid, r in preps.items():
        other.setdefault(sid, r["doctrine"])
    own = office_registry(office_root) if other else None
    if own is None:
        return [head], 0
    try:
        out = [sid for sid, ro in rd.open_sessions(own) if ro and sid in other]
    except BaleError as exc:
        return [head, f"  the sittings out could not be read, so none is compared with it: {exc}"], 0
    return [head] + [f"  {sid}: {prep_words(preps[sid]) if sid in preps else 'a read-only sitting'} "
                     f"{oh.older_doctrine_words(other[sid], install)}" for sid in out], 0


def prep_words(r):
    """A meeting's prep, as office status names it (0.55.0)."""
    return f"the prep for {r['title']} ({r['date']} {r['time']})"


def survey_before_pack(office_root):
    """office survey --before-pack in the office: the survey page again,
    committed alone, never fatal (doctrine section 13). Its words go to
    stderr, since stdout is office start's one JSON line."""
    import subprocess
    env = dict(os.environ, OFFICE_ROOT=str(office_root), PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run([str(INSTALL / "bin" / "office"), "survey", "--before-pack"], env=env,
                              stdin=subprocess.DEVNULL, stdout=sys.stderr, stderr=sys.stderr, timeout=PACK_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"warning: the survey before the pack could not run ({exc}); the session reads the survey as it was")
        return
    if proc.returncode != 0:
        log(f"warning: the survey before the pack exited {proc.returncode}; the session reads the survey as it was")


def digest_before_pack(office_root):
    """office digest --before-pack in the office, before a sitting is
    packed (the blueprint's section 5.1: the digest first, run just
    before the pack): the sitting-open page written again and committed
    alone, never fatal. Its words go to stderr, since stdout is office
    start's one JSON line."""
    import subprocess
    env = dict(os.environ, OFFICE_ROOT=str(office_root), PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run([str(INSTALL / "bin" / "office"), "digest", "--before-pack"], env=env,
                              stdin=subprocess.DEVNULL, stdout=sys.stderr, stderr=sys.stderr, timeout=PACK_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"warning: the digest before the pack could not run ({exc}); the sitting reads the page as it was")
        return
    if proc.returncode != 0:
        log(f"warning: the digest before the pack exited {proc.returncode}; the sitting reads the page as it was")


# How a local branch stands against its remote-tracking ref (0.50.0), read
# in the same connection as the rest of the checkout's reads: $1 the
# branch. Its upstream is the one git records for it, else the one remote
# that has a branch of the name; with neither, or no local branch, nothing
# is printed. Else upstream=, local= and remote= (the two tips) and
# whether the local tip is an ancestor of the remote one (behind, or
# level) and the remote one of the local (ahead, or level).
_UPSTREAM_SCRIPT = (
    'b="$1"; git rev-parse --verify -q "refs/heads/$b" >/dev/null || exit 0; '
    'u=$(git for-each-ref --format="%(upstream)" "refs/heads/$b"); '
    'case "$u" in refs/remotes/*) git rev-parse --verify -q "$u" >/dev/null || u="" ;; *) u="" ;; esac; '
    'if [ -z "$u" ]; then set -- $(git for-each-ref --format="%(refname)" "refs/remotes/*/$b"); '
    '[ $# -eq 1 ] && u="$1"; fi; [ -n "$u" ] || exit 0; '
    'echo "upstream=$u"; echo "local=$(git rev-parse "refs/heads/$b")"; echo "remote=$(git rev-parse "$u")"; '
    'git merge-base --is-ancestor "refs/heads/$b" "$u" && echo "behind=yes" || echo "behind=no"; '
    'git merge-base --is-ancestor "$u" "refs/heads/$b" && echo "ahead=yes" || echo "ahead=no"'
)


def read_upstream(run):
    """_UPSTREAM_SCRIPT's answer: None (no upstream to compare with), or
    {upstream (short), local, remote, state} with state one of level,
    behind (the local tip an ancestor of the remote one: fast-forwardable),
    ahead and diverged."""
    if run.returncode != 0:
        return None
    facts = dict(l.split("=", 1) for l in run.stdout.splitlines() if "=" in l)
    if not facts.get("upstream") or not facts.get("local") or not facts.get("remote"):
        return None
    if facts["local"] == facts["remote"]:
        state = "level"
    elif facts.get("behind") == "yes":
        state = "behind"
    elif facts.get("ahead") == "yes":
        state = "ahead"
    else:
        state = "diverged"
    return {"upstream": facts["upstream"][len("refs/remotes/"):], "local": facts["local"],
            "remote": facts["remote"], "state": state}


def tip(sha):
    return sha[:12]


def checkout_branch(rd, office_root, where, project, branch, checked=False, source="bundle"):
    """Check out the branch a planner's bundle names in its brief (0.34.0,
    `--- BRANCH NAME ---`), or office start's --branch NAME names (0.50.0,
    source "flag"), in the project's clone, here or through its shell on a
    host, before bale packs or opens the session: bale packs the session
    on the branch the clone has checked out, and a session that answers a
    review builds on the review's own branch. Returns the lines to say.

    Nothing is forced. The clone is left as it is, and a StartError names
    why, when the session lands in the office (which works on one
    branch), the clone has uncommitted changes (a checkout would carry
    them), a session is open in the clone (bale lands it on the branch
    checked out there, so moving the clone under it is refused), or no
    branch of that name is in the clone, locally or as one remote's
    tracking branch (the office fetches nothing: the clone's credentials
    are not its own, and the line that fetches is named).

    A local branch behind its remote-tracking ref (0.50.0; the refresh
    moves the remote-tracking ref, never the local branch) is
    fast-forwarded to it once checked out, when the clone is clean and the
    local tip is an ancestor of the remote one, and the line names both
    tips; one that has diverged from it, or is ahead, is checked out as it
    is, and said so. A clone already on the branch is said; behind, it is
    fast-forwarded under the same conditions, and otherwise nothing
    moves."""
    names = (f"the bundle's brief names the branch {branch}" if source == "bundle"
             else f"--branch {branch} names the branch")
    said = ("the branch the bundle's brief names (its BRANCH line)" if source == "bundle"
            else "the branch --branch names")
    if where == "office":
        raise StartError([f"{names} for its session to build on, and the session lands in the office, which "
                          "works on one branch: " + ("a BRANCH line is for a project's bundle" if source == "bundle"
                                                     else "--branch is for a project's session")
                          + "; nothing was written"])
    place = pack_place(office_root, where, project, rd, checked)
    where_words = str(place)  # a Place names its host; a path on this machine is the path
    argvs = [["git", "symbolic-ref", "--short", "-q", "HEAD"],
             ["git", "status", "--porcelain=v1", "-uno"],
             ["git", "rev-parse", "--verify", "-q", f"refs/heads/{branch}"],
             ["git", "for-each-ref", "--format=%(refname)", f"refs/remotes/*/{branch}"],
             ["sh", "-c", _UPSTREAM_SCRIPT, "office-upstream", branch]]
    try:
        head, dirty, local, tracking, upstream = ohost.run_many(place, argvs, timeout=ohost.RUN_TIMEOUT)
    except ohost.HostError as exc:
        raise StartError([f"{project}: the clone could not be read for its branch: {exc}; nothing was written"])
    current = head.stdout.strip() if head.returncode == 0 else None
    up = read_upstream(upstream) if local.returncode == 0 and local.stdout.strip() else None
    changed = [l for l in dirty.stdout.splitlines() if l.strip()]
    if current == branch and (up is None or up["state"] != "behind"):
        return [f"{project}'s clone at {where_words} is on {branch}, {said}; nothing to check out"
                + (stand_words(up) if up else "")]
    if dirty.returncode != 0:
        raise StartError([f"{project}: git status in {where_words} failed: {ohost._last_words(dirty.stderr)}; nothing "
                          "was written"])
    if changed and current == branch:
        # On the branch already, behind its remote-tracking ref, with
        # changes a fast-forward could touch: nothing moves, and no refusal
        # either, since nothing needs checking out.
        return [f"{project}'s clone at {where_words} is on {branch}, {said}, at {tip(up['local'])}, behind "
                f"{up['upstream']} at {tip(up['remote'])}; it is not fast-forwarded over uncommitted changes "
                f"({len(changed)} path(s)), so the session builds on {tip(up['local'])}"]
    if changed:
        raise StartError([f"{names}, and {project}'s clone at {where_words} has "
                          f"uncommitted changes ({len(changed)} path(s): {', '.join(l[3:] for l in changed[:6])}"
                          + (", ..." if len(changed) > 6 else "") + f"), so {branch} is not checked out over them",
                          "commit or stash them there, then start again; nothing was written"])
    # A session open in the clone lands on the branch checked out there.
    try:
        open_there = [sid for sid, _ in rd.open_sessions(place)] if _bale_registry_at(place, rd) else []
    except BaleError as exc:
        raise StartError([f"{project}: the sessions open in its clone could not be read: {exc}; nothing was written"])
    if open_there and current == branch:
        return [f"{project}'s clone at {where_words} is on {branch}, {said}, at {tip(up['local'])}, behind "
                f"{up['upstream']} at {tip(up['remote'])}; it is not fast-forwarded under the {len(open_there)} "
                f"session(s) open in it ({', '.join(open_there)}), so the session builds on {tip(up['local'])}"]
    if open_there:
        raise StartError([f"{names}, and {project}'s clone at {where_words} is on "
                          f"{current or 'a detached HEAD'} with {len(open_there)} session(s) open in it "
                          f"({', '.join(open_there)}), which bale lands on the branch checked out there; it is not "
                          "moved under them",
                          "land or withdraw them first, then start again; nothing was written"])
    remotes = [r for r in tracking.stdout.split() if r.startswith("refs/remotes/")]
    if current == branch:
        argv, how = None, "already checked out"
    elif local.returncode == 0 and local.stdout.strip():
        argv = ["git", "checkout", "-q", branch]
        how = "its local branch"
    elif len(remotes) == 1:
        short = remotes[0][len("refs/remotes/"):]
        argv = ["git", "checkout", "-q", "-b", branch, "--track", short]
        how = f"a new local branch tracking {short}"
    elif remotes:
        raise StartError([f"{names}, which {project}'s clone at {where_words} has "
                          f"on {len(remotes)} remotes and not locally ({', '.join(r[len('refs/remotes/'):] for r in remotes)}); "
                          f"make the local branch there from the right one (git checkout -b {branch} --track REMOTE/{branch}), "
                          "then start again; nothing was written"])
    else:
        raise StartError([f"{names}, and {project}'s clone at {where_words} has no "
                          f"such branch, locally or on a remote it has fetched (it is on {current or 'a detached HEAD'})",
                          f"fetch it there first (git fetch REMOTE {branch}, with the clone's own credentials; the "
                          "office fetches nothing), then start again; nothing was written"])
    ff = up is not None and up["state"] == "behind"
    steps = ([argv] if argv else []) + ([["git", "merge", "--ff-only", "-q", up["remote"]]] if ff else [])
    try:
        run = ohost.run_many(place, [*steps, ["git", "symbolic-ref", "--short", "-q", "HEAD"],
                                     ["git", "rev-parse", "-q", "--verify", "HEAD"]], timeout=ohost.RUN_TIMEOUT)
    except ohost.HostError as exc:
        raise StartError([f"{project}: {branch} could not be checked out in {where_words}: {exc}"])
    failed = next((i for i, r in enumerate(run[:len(steps)]) if r.returncode != 0), None)
    if failed is not None or run[len(steps)].stdout.strip() != branch:
        first = run[failed if failed is not None else 0]
        what = f"git checkout {branch}" if argv and failed in (0, None) else f"git merge --ff-only {up['upstream']}"
        raise StartError([f"{project}: {what} in {where_words} failed (exit {first.returncode}): "
                          f"{ohost._last_words(first.stderr) or run[len(steps)].stdout.strip() or 'no words'}; the "
                          "clone is as git left it, and nothing else was written"])
    now = run[len(steps) + 1].stdout.strip()
    if ff:
        moved = (f"fast-forwarded from {tip(up['local'])} to {tip(now)}, the tip of {up['upstream']}"
                 if now == up["remote"] else
                 f"fast-forwarded from {tip(up['local'])} to {tip(now)} ({up['upstream']} is at {tip(up['remote'])})")
        if argv is None:
            return [f"{project}'s clone at {where_words} is on {branch}, {said}: {moved}"]
        return [f"checked out {branch} in {project}'s clone at {where_words} ({how}, {moved}; it was on "
                f"{current or 'a detached HEAD'}), {said}, so bale "
                + ("opens the bundle on it" if source == "bundle" else "packs the session on it")]
    return [f"checked out {branch} in {project}'s clone at {where_words} ({how}; it was on {current or 'a detached HEAD'}), "
            f"{said}, so bale " + ("opens the bundle on it" if source == "bundle" else "packs the session on it")
            + (stand_words(up) if up else "")]


def stand_words(up):
    """Where a checked-out branch stands against its remote-tracking ref,
    when it is not level: words to append to the checkout's line."""
    if up["state"] == "diverged":
        return (f"; it has diverged from {up['upstream']} ({tip(up['local'])} here, {tip(up['remote'])} there), so "
                "it is checked out as it is: nothing is forced")
    if up["state"] == "ahead":
        return f"; it is ahead of {up['upstream']} ({tip(up['local'])} here, {tip(up['remote'])} there)"
    if up["state"] == "behind":
        return f"; it is behind {up['upstream']} ({tip(up['local'])} here, {tip(up['remote'])} there)"
    return ""


def _bale_registry_at(place, rd):
    """Whether bale keeps a registry where the place is (a .bale/
    directory): read through the shell for a hosted place, where the
    reader's status asks bale anyway, else an existence check here."""
    if isinstance(place, ohost.Place) and place.hosted:
        return True
    return (pathlib.Path(str(place)) / ".bale").is_dir()


def bundle_read_only(bundle):
    """Whether a planner bundle's stored pack line packs a read-only
    session (bale pack --read-only): True or False when the office can read
    the line from the file, None when it cannot (no file named, no such
    file here, or a line that does not read as bale's)."""
    if not bundle:
        return None
    argv = bundle_pack_argv(bundle)
    if argv is None:
        return None
    try:
        forecast, _ = bundle_forecast(argv)
    except ValueError as exc:
        debug(f"the pack line of {bundle} does not read as bale's: {exc}")
        return None
    return forecast == []


def digest_written_at(office_root):
    """The written_at line of the office's digest page (UTC, as office
    digest stamps it), or None when there is no page or no such line."""
    import office_drafting as od
    page = pathlib.Path(office_root) / od.SPACE / "digest.md"
    try:
        text = page.read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"^- written_at: (\S+)", text, re.M)
    return m.group(1) if m else None


def digest_left_line(office_root, name, why):
    """The one line office start says when it sends out an office bundle
    whose pack line it cannot read (why: the reason), so it cannot tell
    whether the bundle is a sitting and leaves the digest as it was: never
    a silent skip (doctrine section 4)."""
    import office_drafting as od
    at = digest_written_at(office_root)
    page = (f"{od.SPACE}/digest.md as it was, written {at}" if at
            else f"{od.SPACE}/digest.md unwritten, as it was")
    return (f"the office cannot read the pack line of the bundle {name} ({why}), so it cannot tell whether it "
            f"sends out a sitting: it leaves {page}; office digest writes it")


def level_step(name):
    """The office step that brings a host's bale level with this
    machine's, as a command line."""
    return f"office projects level-bale {name}"


def check_hosted_place(rd, entry, checked=False):
    """The place a session on a hosted project is packed in, once it has
    answered. The first connection is the reach check (a host that does
    not answer stops the start there, before anything is written, with
    the connect line); its bale is held to the read side's floor (start
    never upgrades a bale, it names the step that does); and the repo
    there is checked as office projects add checks one, unless this
    start checked it already (checked, or once per reader).

    Since 0.16.0 the reach, the version, the status and the repo's check
    travel in one connection; and checked (bin/office ran start-check
    this command, which did all of it) makes no connection here at all:
    the reads a step needs next ride its own batch."""
    name = entry["name"]
    place = ohost.place_of(entry)
    if place in rd.places_checked:
        return place
    if checked:
        rd.places_checked.add(place)
        return place
    try:
        _, (check,) = rd.prefetch(place, [("version", {}), ("status", {})], extra=[ohost.check_argv(place)])
        v = rd.installed_version(place)
    except BaleError as exc:
        raise StartError([f"{name}: {exc}; nothing was written"])
    floor = rd.consumption.floor
    try:
        behind = oh.compare_versions(v, floor) < 0
    except oh.HelperError as exc:
        raise StartError([f"{name}: bale's version on {entry['host']} could not be compared: {exc}"])
    if behind:
        raise StartError([f"{name}: bale {v} on {entry['host']} is older than the read side's floor {floor}, so no "
                          f"session goes out there; {level_step(name)} brings it level with this machine's bale "
                          "(start never upgrades a bale on its own); nothing was written"])
    try:
        ok, why = ohost.read_check(place, check)
    except ohost.HostError as exc:
        raise StartError([f"{name}: {exc}; nothing was written"])
    if not ok:
        raise StartError([f"{name} cannot be packed: {why}"])
    rd.places_checked.add(place)
    return place


def hosted_round(rd, place, paths=(), doctrine=False, extra=(), version=False):
    """The reads a step on a hosted place needs, in one connection (since
    0.16.0): bale status (cached in the reader), with version bale's
    --version too (a bundle's open asks it, 0.17.2), which of the paths are
    not there, and with doctrine the sums of the doctrine its tree holds;
    extra argvs ride after them. Kept in rd.facts for paths_missing_in and
    doctrine_sums, so each answers from this round without connecting.
    Returns the extra Runs."""
    paths = [p for p in dict.fromkeys(paths) if p]
    argvs = []
    if paths:
        argvs.append(["sh", "-c", ohost.MISSING_SCRIPT, "office-paths", *[p.strip("/") or "." for p in paths]])
    if doctrine:
        argvs.append(["sh", "-c", _DOCTRINE_SUMS])
    try:
        _, runs = rd.prefetch(place, [("status", {})] + ([("version", {})] if version else []),
                              extra=[*argvs, *extra])
    except BaleError as exc:
        raise StartError([f"{place.name or place.host}: {exc}"])
    i = 0
    if paths:
        run = runs[i]; i += 1
        if run.returncode != 0:
            raise StartError([f"the paths in {place} could not be checked: {ohost._last_words(run.stderr)}"])
        gone = set(run.stdout.splitlines())
        rd.facts[(place, "missing", tuple(paths))] = [p for p in paths if (p.strip("/") or ".") in gone]
    if doctrine:
        run = runs[i]; i += 1
        rd.facts[(place, "doctrine")] = run
    return runs[i:]


def pack_place(office_root, where, project, rd=None, checked=False):
    """The directory a start packs in: the office, or the project's repo
    (refusing, as start does, a project the office cannot pack); for a
    project on a host, its Place, once it has answered."""
    office_root = pathlib.Path(office_root).resolve()
    if where == "office":
        return office_root
    manifest = oh.read_toml(office_root / "floor-plan" / "manifest.toml")
    projects = {p["name"]: p for p in oh.read_projects(manifest) or []}
    entry = projects.get(project)
    if entry is None:
        raise StartError([f"no project named {project} in this office's [projects] "
                          f"(it lists: {', '.join(sorted(projects)) or 'none'})"])
    if entry["problem"]:
        raise StartError([f"{project}: {entry['problem']}"])
    if hosted_project(entry):
        return check_hosted_place(rd or Reader(), entry, checked)
    ok, why = oh.check_project_dir(entry["resolved"])
    if not ok:
        raise StartError([f"{project} cannot be packed: {why}"])
    return entry["resolved"]


def overlap_lines(rd, office_root, pack_dir, where, project, forecast, bundle=None, supersedes=None):
    """The office's own words for the predictable refusal, or []: the open
    sessions whose forecasts overlap this one (a split's superseded
    session aside), each with the folder that records it, and what clears
    the way."""
    clash = [c for c in open_overlaps(rd, pack_dir, forecast) if c[0] != supersedes]
    if not clash:
        return []
    naming = folders_naming(office_root)
    label = "this office" if where == "office" else project
    lines = [f"the bundle {pathlib.Path(bundle).name} forecasts "
             + (", ".join(forecast) if forecast else "the whole tree")] if bundle else []
    for sid, theirs, hit in clash:
        folders = ", ".join(naming.get(sid, [])) or "no folder records it"
        lines.append(f"{sid} is open in {label} ({folders}); its forecast "
                     f"({', '.join(theirs) if theirs else 'the whole tree'}) overlaps this one at {', '.join(hit)}")
    first = clash[0][0]
    landing = (f"land it first (office land {first}), or close it if it was abandoned "
               f"(bale unlock {first}, in {pack_dir})")
    if where == "office" and any("notepad" in h for _, _, h in clash):
        lines.append("office sessions take turns on the notepad: " + landing
                     + (", or ask the planner for a read-only bundle" if bundle else
                        ", or start this one --read-only"))
    else:
        lines.append(landing + (", or ask the planner for a bundle whose forecast does not overlap it" if bundle
                                else ", or narrow this one's forecast with --write"))
    return lines


def bundle_precheck(rd, office_root, where, project, bundle, checked=False, defer_overlap=False):
    """For a bundle the office can read (a file here), the refusals office
    start says in its own words before bale is asked anything: a path the
    pack line names that is not in the tree it opens in, and an open
    session whose forecast overlaps the bundle's. A bundle it cannot read
    is bale's to judge (check_bundle runs bale open --check next).

    With defer_overlap (a bale whose open --check speaks --json, 0.18.0)
    the overlap is not refused here: its lines are returned, and
    check_bundle refuses them only where bale's own rehearsal refuses
    the bundle. A second desk is bale's to recognize (the ruling of
    2026-10-12, ratified with session 2026-10-13-office-probe-002): a
    bundle whose session is still open overlaps that session's forecast
    by construction, and bale takes it as one more desk. Returns the
    overlap's lines, or []."""
    argv = bundle_pack_argv(bundle)
    if argv is None:
        return []
    pack_dir = pack_place(office_root, where, project, rd, checked)
    try:
        b_inc, b_wr, _ = bundle_paths(argv)
        forecast, supersedes = bundle_forecast(argv)
    except ValueError:
        return []
    named = list(dict.fromkeys(b_inc + b_wr))
    label = "office" if where == "office" else project
    if rd.hosted(pack_dir):
        # One connection: the open sessions, which paths are there, and
        # (0.18.0) bale's version, which says whether its rehearsal
        # speaks --json.
        hosted_round(rd, pack_dir, named, version=True)
    places = bundle_places(office_root, named, rd)
    mine = next((m for lab, _, m in places if lab == label), None)
    if mine is None:
        mine = paths_missing_in(pack_dir, named, rd)
    if mine:
        raise StartError([f"the bundle {pathlib.Path(bundle).name} names paths that are not in "
                          f"{place_words(label)}'s tree, so it cannot open there; nothing ran"]
                         + bundle_nowhere_lines(bundle, named, places, chosen=label))
    lines = overlap_lines(rd, office_root, pack_dir, where, project, forecast, bundle, supersedes)
    if lines and not defer_overlap:
        raise StartError(lines)
    return lines


def check_bundle(rd, office_root, where, project, bundle, checked=False):
    """The path bale found the bundle at (None when its report does not
    say), or StartError: check_bundle_report's found alone."""
    return check_bundle_report(rd, office_root, where, project, bundle, checked)["found"]


def check_bundle_report(rd, office_root, where, project, bundle, checked=False):
    """bale open --check for a bundle, where it would open, before office
    start opens a folder, commits a survey or fills a tray: bale resolves
    a bare name through its own search (cwd first, then its search
    directories), verifies the bundle and runs every gate it runs before
    an open, and writes nothing (the third-trip probe found it so on bale
    0.4.47: a missing name, a forecast path that does not exist and a
    forecast overlapping an open session each refuse, exit 1, with
    nothing written).

    From bale 0.4.50 on (open_json_ok) the rehearsal runs with --json
    ([surfaces.open_check_json]), and its outcome is bale's verdict: a
    bundle the office's own overlap check caught (bundle_precheck) goes
    on when bale's rehearsal passes it, which is how bale takes a bundle
    whose session is still open as a second desk, and is refused in the
    office's words, with bale's reason beside them, when bale's
    rehearsal refuses it too (session 2026-10-13-office-probe-002
    captured both on bale 0.4.52). The rehearsal's `rehearsal` key says
    only which rehearsal ran ("check"), never which bundle opened a
    session; the session is in bale's own lines on stderr, which the
    office passes on to the occupant and never reads for a decision.

    Returns {found: the path bale found the bundle at, or None when its
    report does not say; over: the office's overlap lines bale's
    rehearsal passed, [] when there were none; bale: bale's own
    second-desk lines from that rehearsal}. Raises StartError with
    bale's own words, or the office's where it could read the bundle."""
    pack_dir = pack_place(office_root, where, project, rd, checked)
    over = bundle_precheck(rd, office_root, where, project, bundle, checked, defer_overlap=True)
    as_json = open_json_ok(rd, pack_dir)
    if over and not as_json:
        raise StartError(over)
    surface = "open_check_json" if as_json else "open_check"
    spec = rd.consumption.surface(surface)
    hosted = rd.hosted(pack_dir)
    place = "in the office" if where == "office" else f"on {project}"
    if hosted:
        local = hosted_bundle_file(bundle, pack_dir)
    try:
        with ohost.Scratch(pack_dir) as scratch:
            # On a host, the bundle travels there first, into the office's
            # one temporary directory (made in the same connection), and
            # bale checks that copy; the directory is removed whatever bale
            # says, in the check's own connection.
            asked = send_bundle(pack_dir, local, scratch) if hosted else bundle
            also = [scratch.removal_argv()] if hosted else None
            try:
                proc, shown, _ = rd.invoke(surface, pack_dir, timeout=PACK_TIMEOUT, whole_why=True, also=also,
                                           accept=(1,) if as_json else (), bundle=asked)
            finally:
                if hosted and rd.also_runs:
                    scratch.removed_by_step()
    except (BaleError, ohost.HostError) as exc:
        raise StartError([f"bale cannot open the bundle {bundle} {place} ({pack_dir}), so start stopped before "
                          f"anything was written: {exc}"])
    found, said = None, []
    if as_json:
        try:
            report = rd.parse(surface, proc, shown, str(pack_dir))
            outcome = rd.key(report, "open_check_json", "outcome")
            if outcome == spec["refused"] and proc.returncode == 1:
                reason = rd.key(report, "open_check_json", "reason")
                cause = rd.key(report, "open_check_json", "cause")
            elif outcome == spec["outcome_passed"] and proc.returncode == 0:
                kind = rd.key(report, "open_check_json", "rehearsal")
                if kind != "check":
                    raise BaleError("output", f"{shown} in {pack_dir} rehearsed {kind!r}, not the check it was asked")
                b = rd.key(report, "open_check_json", "bundle")
                found = rd.key(b, "open_check_json", "bundle.path") if isinstance(b, dict) else None
            else:
                raise BaleError("output", f"{shown} in {pack_dir} exited {proc.returncode} with outcome {outcome!r}, "
                                          f"neither {spec['outcome_passed']!r} (exit 0) nor {spec['refused']!r} (exit 1)")
        except BaleError as exc:
            raise StartError([f"bale's rehearsal of the bundle {bundle} {place} ({pack_dir}) did not read, so start "
                              f"stopped before anything was written: {exc}"])
        if proc.returncode == 1:
            # bale's whole refusal, from its error line on (a missing name
            # lists every directory searched); the JSON's cause is its
            # first line, for when stderr carried none.
            err = [l for l in proc.stderr.splitlines() if l.strip()]
            start_at = next((i for i, l in enumerate(err) if "error" in l.lower()), None)
            words = "\n".join(err[start_at:]) if start_at is not None else cause
            if over:
                raise StartError(over + [f"bale's own rehearsal refuses it too ({reason}): {cause}"])
            raise StartError([f"bale cannot open the bundle {bundle} {place} ({pack_dir}), so start stopped before "
                              f"anything was written: {shown} refused it ({reason}): {words}"])
        said = [l for l in proc.stderr.splitlines() if l.startswith(spec["second_desk_line"])]
    else:
        for line in proc.stdout.splitlines():
            if line.startswith(spec["found_line"]):
                found = line[len(spec["found_line"]):].split(" against ", 1)[0].strip()
    if hosted and found is not None:
        found = f"{local} (sent to {pack_dir.host} for the check)"
    debug(f"{shown} in {pack_dir}: passed; bale found the bundle at {found or '(its report does not say)'}"
          + (f"; it passed over the office's overlap ({len(over)} line(s))" if over else ""))
    return {"found": found, "over": over, "bale": said}


def paths_missing_in(pack_dir, paths, rd=None):
    """The paths a pack names that its directory lacks, here or on a
    host (asked through its shell, unless this reader's hosted round
    already asked)."""
    if isinstance(pack_dir, ohost.Place) and pack_dir.hosted:
        key = (pack_dir, "missing", tuple(p for p in dict.fromkeys(paths) if p))
        if rd is not None and key in rd.facts:
            return list(rd.facts[key])
        try:
            return ohost.missing_paths(pack_dir, paths)
        except ohost.HostError as exc:
            raise StartError([f"the paths in {pack_dir} could not be checked: {exc}"])
    return [x for x in paths if not (pathlib.Path(pack_dir) / x.strip("/")).exists()]


def hosted_bundle_file(bundle, place):
    """The bundle file on this machine that travels to a host. bale's own
    search for a bare name runs where bale opens the bundle, on the host,
    where the downloaded file is not; so a bundle for a hosted project is
    named as a file here (its path, or a name in the current directory)."""
    p = pathlib.Path(bundle).expanduser()
    if not p.is_file():
        raise StartError([f"{bundle} is not a file on this machine: a bundle for a project on {place.host} travels "
                          "there from here, so give its path (bale's search for a bare name would run on the host, "
                          "where it is not)"])
    return str(p.resolve())


def send_bundle(place, local, scratch):
    """The bundle copied into the office's temporary directory on the
    host, under its own name (bale reads the name); its path there. The
    directory is made in the same connection when it is not made yet."""
    remote = scratch.send(local)
    log(f"sent {pathlib.Path(local).name} to {place.host} ({remote}, removed when this start is done)")
    return remote


def start_forecast(office_root, folder, where, writes=(), includes=(), read_only=False, bundle=None):
    """The forecast a start's pack carries, as start() works it out: []
    for a read-only session, ["."] for the whole tree, else its paths;
    None when the office cannot read it (a bundle given by a bare name
    bale's search finds, or one whose pack line does not read)."""
    office_root = pathlib.Path(office_root).resolve()
    if bundle:
        argv = bundle_pack_argv(bundle)
        if argv is None:
            return None
        try:
            forecast, _ = bundle_forecast(argv)
        except ValueError:
            return None
        return ["."] if forecast is None else forecast
    if read_only:
        return []
    writes = [w.strip().rstrip("/") or "." for w in writes if w.strip()]
    if where == "office":
        if any(w in ("", ".") for w in writes):
            return ["."]
        return [folder] + (["notepad"] if (office_root / "notepad").is_dir() else []) + writes
    return writes or [i.strip().rstrip("/") for i in includes if i.strip()] or ["."]


def start_riders(office_root, folder, where, project, writes=(), includes=(), read_only=False, bundle=None):
    """(forecast, riders): the queued riders on the drafting table's
    riders page that a start's pack carries (office riders --forecast
    over the pack's forecast), for office start to offer before it packs.
    forecast is None when the office cannot read it, and then no rider
    is offered."""
    import office_drafting as od
    forecast = start_forecast(office_root, folder, where, writes, includes, read_only, bundle)
    if not forecast:
        return forecast, []
    return forecast, od.riders_for_forecast(office_root, forecast, project if where == "project" else None)


# --- the install against its source -----------------------------------------------------

def shell_quote(word):
    """The way bin/office's shq quotes a word: always single quotes."""
    return "'" + word.replace("'", "'\\''") + "'"


def install_source(office_root, install=None):
    """(source, commit, project) when this office scopes the project the
    running install came from: INSTALLED's source: and commit: lines,
    and the name the office's [projects] gives that repo. None otherwise:
    no INSTALLED stamp (a working copy), a stamp without both lines, or a
    source this office does not scope (a hosted project is never the
    source: the install is on this machine)."""
    stamp = pathlib.Path(install or INSTALL) / "INSTALLED"
    if not stamp.is_file():
        return None
    fields = {}
    for line in stamp.read_text(encoding="utf-8", errors="replace").splitlines():
        key, sep, value = line.partition(": ")
        if sep and key not in fields:
            fields[key] = value.strip()
    src, commit = fields.get("source"), fields.get("commit")
    if not src or not commit:
        return None
    try:
        src_real = pathlib.Path(src).resolve()
    except OSError:
        return None
    scoped = [p for p in office_projects(office_root) or []
              if not p["problem"] and p["resolved"] is not None and pathlib.Path(p["resolved"]).resolve() == src_real]
    if not scoped:
        return None
    return src, commit, scoped[0]["name"]


def install_behind(office_root, install=None, source=False):
    """When this office scopes the project the running install came from
    (install_source) and that repo's HEAD is not the installed commit:
    {source, commit, head, version, words, project}, words being the
    sentence office status's source line says (BEHIND: ...). None
    otherwise: no INSTALLED stamp (a working copy), a source this office
    does not scope, a source that is not a git work tree, or one level
    with the install. source, when given, is install_source's answer
    already read (False: read it here)."""
    import subprocess
    found = install_source(office_root, install) if source is False else source
    if found is None:
        return None
    src, commit, project = found

    def git_out(*args):
        try:
            p = subprocess.run(["git", "-C", src, *args], capture_output=True, text=True, timeout=BALE_TIMEOUT,
                               stdin=subprocess.DEVNULL)
        except (OSError, subprocess.TimeoutExpired) as exc:
            debug(f"git {' '.join(args)} in {src}: {exc}")
            return None
        return p.stdout.strip() if p.returncode == 0 else None

    head = git_out("rev-parse", "HEAD")
    if head is None:
        return None
    have = git_out("rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}")
    if have == head:
        return None
    short = git_out("rev-parse", "--short", "HEAD") or head[:7]
    version = (git_out("show", "HEAD:VERSION") or "").splitlines()
    version = version[0] if version else "?"
    words = (f"BEHIND: the install is {commit}, and {src} is now at {short} (office-src {version}); "
             f"(cd {shell_quote(src)} && ./install.sh) brings the install level")
    return {"source": src, "commit": commit, "head": short, "version": version, "words": words,
            "project": project}


def bytecode_behind(install=None):
    """When the running install's bytecode cache is not level with its lib/
    for this python3 and install.sh is what brings it level (0.31.0, the
    walk-in's line and the Next line's, after the install behind its
    source): {words, what, source}, words being office status's bytecode
    line less its label (BEHIND: ... or NONE for this python3 ...), what
    the part before its remedy, source the working copy install.sh was run
    from ("" when its stamp names none). None when the cache is level, for
    a working copy (no install, no cache to keep), and under a cache prefix
    (PYTHONPYCACHEPREFIX: this python3 reads that cache alone, never the
    install's, and install.sh does not write it). Any office, whether or
    not it scopes the source: every office on this install runs slower."""
    install = pathlib.Path(install or INSTALL)
    if getattr(sys, "pycache_prefix", None) is not None:
        return None
    source = oh.installed_source(install)
    if source is None:
        return None
    line, code = oh.bytecode_line(install)
    if code == 0:
        return None
    words = line.split(":", 1)[1].strip()
    return {"words": words, "what": words.split("; ", 1)[0], "source": source}


# --- the detached suite's verdict, on the walk-in ----------------------------------------
#
# tests/run.sh --detach (0.17.1) runs office-src's whole suite in the
# background and writes a one-line verdict under the state directory,
# office-src/suite/<stamp>-<pid>/verdict, with latest naming the newest
# run. A verdict is only as good as someone reading it, and the walk-in is
# where the occupant already looks: when the office scopes the install's
# own source, the walk-in says the latest verdict in one line, and only
# when it is not OK. The shape is tests/runner.py's (detach and
# detached_child); test_read_side holds the two to each other.

# A RUNNING verdict older than this is reported: the whole suite takes
# minutes, so a run that has said RUNNING for an hour has likely died.
SUITE_RUNNING_STALE = dt.timedelta(hours=1)
SUITE_RUNNING_RE = oh.LazyPattern(r"^RUNNING since (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\b")


def suite_state_dir(environ=None):
    """Where tests/runner.py keeps detached runs: office-src/suite under
    XDG_STATE_HOME, else under HOME's .local/state (runner.state_dir)."""
    environ = os.environ if environ is None else environ
    base = environ.get("XDG_STATE_HOME") or os.path.join(environ.get("HOME") or os.path.expanduser("~"),
                                                         ".local", "state")
    return pathlib.Path(base) / "office-src" / "suite"


def suite_verdict_words(line, run_dir, now=None):
    """What the walk-in says of one verdict line, or None when there is
    nothing to say: OK, or RUNNING for less than SUITE_RUNNING_STALE. A
    FAILED or BROKEN verdict is said as written (it names the log to
    read); a RUNNING one past the hour says so with its log; a line in no
    shape the runner writes is said as such, never taken for OK. A pure
    function of its arguments."""
    now = now or dt.datetime.now(dt.timezone.utc)
    line = line.strip()
    if line == "OK" or line.startswith("OK "):
        return None
    if line.startswith(("FAILED ", "BROKEN ")):
        return line
    m = SUITE_RUNNING_RE.match(line)
    if m:
        since = dt.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
        age = now - since
        if age < SUITE_RUNNING_STALE:
            return None
        hours = int(age.total_seconds() // 3600)
        return (f"{line}; still RUNNING after {hours} hour(s), so the run has likely died: "
                f"read {pathlib.Path(run_dir) / 'run.log'}")
    return f"the latest verdict, {pathlib.Path(run_dir) / 'verdict'}, is in no shape the runner writes: {line!r}"


def suite_verdict(office_root, install=None, environ=None, now=None, source=False):
    """The walk-in's Suite line for the latest detached run, or None.
    Only when this office scopes the install's own source (install_source,
    or source when already read), and only when the verdict is not OK
    (suite_verdict_words). No state directory, or one holding no run yet,
    is nothing to say: the suite has not been run detached on this
    machine. A verdict that cannot be read where a run is named is said,
    never skipped."""
    found = install_source(office_root, install) if source is False else source
    if found is None:
        return None
    state = suite_state_dir(environ)
    latest = state / "latest"
    if not state.is_dir() or not (latest.is_symlink() or latest.exists()):
        debug(f"no detached run of the suite at {state}; nothing to say on the walk-in")
        return None
    run_dir = latest.resolve()
    try:
        text = (run_dir / "verdict").read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"the latest detached run's verdict could not be read ({run_dir / 'verdict'}: {exc.strerror or exc})"
    first = text.splitlines()[0] if text.strip() else ""
    if not first.strip():
        return f"the latest detached run's verdict is empty ({run_dir / 'verdict'})"
    return suite_verdict_words(first, run_dir, now)


def open_json_ok(rd, pack_dir):
    """Whether the bale that opens a bundle in pack_dir speaks bale open
    --json with the joined session's tarball on a second desk ([surfaces.
    open_json]'s since, 0.4.50): this machine's bale, or the one a hosted
    place's shell reaches (asked in the start's round, so no connection
    of its own). A version that cannot be read or compared is no."""
    since = rd.consumption.surface("open_json")["since"]
    try:
        v = rd.installed_version(pack_dir if rd.hosted(pack_dir) else None)
        return oh.compare_versions(v, since) >= 0
    except (BaleError, oh.HelperError) as exc:
        debug(f"bale's version where the bundle opens could not be read or compared ({exc}); "
              "bale open runs without --json")
        return False


def open_bundle(rd, pack_dir, bundle, scratch=None, as_json=False):
    """Run bale open for a planner bundle in pack_dir, stdin closed, so
    no question is answered for the occupant; a pre-answered intent in
    the bundle is bale's to honour. Returns sid, tarball, opener and
    second_desk.

    Which session the open leaves the bundle in is read from the registry,
    never from the day of the start and never from .bale/: bale status's
    open set before the open against the open set after. A real open adds
    one session to it. A second desk adds none: since 0.4.44 a bundle whose
    session is still open joins it as one more desk (bale records a desk-2
    attempt on that session and prints a desk-qualified opener) instead of
    minting a sid, which is what happened to the audience-line bundle on
    2026-10-12 (probe of session 2026-10-13-doctrine-core-001). With
    as_json (bale 0.4.50 or later, open_json_ok) bale open --json says
    which it did, outcome "opened" or "second-desk" with the sid, and the
    office holds that line to the diff: an open must add exactly its sid,
    a second desk must add nothing and name a session open before and
    after. Without it (an older bale) the diff alone decides, and a diff
    that shows nothing newly open says the second desk is the likely
    reason. The tarball is the report's (the JSON key, or the human
    report's tarball line), held to the request bale status lists for
    that sid. On a host the status after the open, and the scratch's
    removal, ride the open's own connection."""
    surface = "open_json" if as_json else "open"
    spec = rd.consumption.surface(surface)
    before = set(rd.key(rd.status(pack_dir), "status", "sessions") or [])
    hosted = rd.hosted(pack_dir)
    status_argv = rd.consumption.argv("status")
    also = None
    if hosted:
        also = [["bale", *status_argv]] + ([scratch.removal_argv()] if scratch is not None and scratch.made else [])
    proc, shown, where = rd.invoke(surface, pack_dir, timeout=PACK_TIMEOUT, whole_why=True, also=also, bundle=bundle)
    lines = proc.stdout.splitlines()
    rd.forget(pack_dir)
    if hosted:
        if scratch is not None and scratch.made:
            scratch.removed_by_step()
        run = rd.also_runs[0]
        if run.returncode == 0:
            try:
                rd._cache[(str(pack_dir), tuple(status_argv))] = rd.parse("status", run, "bale status --json",
                                                                           str(pack_dir))
            except BaleError as exc:
                debug(f"bale status after the open did not read from its batch ({exc}); asked on its own")
    st = rd.status(pack_dir)
    after = rd.key(st, "status", "sessions") or []
    new = [x for x in after if x not in before]
    second_desk = False
    if as_json:
        report = rd.parse(surface, proc, shown, where)
        outcome = rd.key(report, "open_json", "outcome")
        sid = rd.key(report, "open_json", "sid")
        tarball = rd.key(report, "open_json", "tarball")
        opener = rd.key(report, "open_json", "opener")
        if outcome not in spec["outcomes"]:
            raise BaleError("output", f"{shown} exited 0 in {where} with outcome {outcome!r}, which is neither of "
                                      f"{' and '.join(spec['outcomes'])}")
        if outcome == "second-desk":
            second_desk = True
            if new or sid not in before or sid not in after:
                raise BaleError("output", f"{shown} says it joined {sid} in {where} as a second desk, but bale "
                                          f"status names {', '.join(new) or 'no'} newly open session(s) and "
                                          f"{sid} {'was' if sid in before else 'was not'} open before, so the "
                                          "office cannot tell which session the bundle is in")
        elif new != [sid]:
            raise BaleError("output", f"{shown} says it opened {sid} in {where}, but bale status names "
                                      f"{len(new)} newly open session(s) ({', '.join(new) or 'none'})")
        if second_desk and tarball is None:
            raise BaleError("output", f"{shown} joined the open session {sid} in {where} as a second desk, but bale "
                                      "has no request tarball for it in the outbox (its summary says so), so there "
                                      "is no request to put in the out tray; bale status shows the session")
        opener = (opener.rstrip("\n").split("\n") if isinstance(opener, str) and opener.strip()
                  else opener_lines(proc.stderr.splitlines(), spec))
    else:
        if len(new) != 1:
            why = ("; a bundle whose session is still open joins it as a second desk instead of opening one "
                   f"(bale {spec['second_desk_since']} on), and bale open --json, which says so, "
                   f"needs bale {rd.consumption.surface('open_json')['since']}: bale's own lines say which, and "
                   "bale status names the open sessions" if not new else "")
            raise BaleError("output", f"{shown} exited 0 in {where}, but bale status names {len(new)} newly open "
                                      f"session(s) ({', '.join(new) or 'none'}), so the office cannot tell which "
                                      f"it opened{why}")
        sid = new[0]
        tarball = None
        for line in lines:
            if line.startswith(spec["tarball_line"]):
                tarball = line[len(spec["tarball_line"]):].strip()
        opener = opener_lines(lines, spec)
    name = f"request-{sid}.tar.gz"
    if tarball is None or pathlib.PurePath(tarball).name != name or name not in (rd.key(st, "status", "outbox") or []):
        raise BaleError("output", f"{shown} {'joined' if second_desk else 'opened'} {sid} in {where}, but its "
                                  f"report's tarball ({tarball or 'none'}) is not the request bale status lists "
                                  f"for it ({name})")
    return {"sid": sid, "tarball": tarball, "opener": opener, "second_desk": second_desk}


# --- a bailout's fresh session: office start N --handoff (0.52.0) ------------------------------------
#
# bale handoff is a third way a request is built, beside pack and open: it
# takes a bailout response, inherits the bailed-on session's goal verbatim and
# its recorded forecast exactly, and packs a fresh session whose request
# carries the worker's handoff.md first. office start N --handoff runs it
# where the bailed session ran (through the project's shell on a host, the
# tarball carried there first), reads the new session from bale status's open
# set before and after (exactly one more, held to the report's rows and to the
# request in status's outbox), and then does everything a pack's start does:
# the tray, the folder's record, the opener. bale handoff prints no opener and
# keeps no constraint, so the office composes the opener from the request, in
# the shape of bale's own, and says it is the office's (handoff_opener).

HANDOFF_RESPONSE_RE = oh.LazyPattern(r"response-\d{3}/manifest\.json")
REQUEST_MANIFEST_RE = oh.LazyPattern(r"request-\d{3}/manifest\.json")


def response_facts(path):
    """(responds_to, response_kind, handoff.md's path inside the response or
    None) of a response tarball: the worker's file, read without bale."""
    import json
    import tarfile
    try:
        with tarfile.open(path) as t:
            members = [m for m in t.getmembers() if m.isfile()]
            m = next((m for m in members if HANDOFF_RESPONSE_RE.fullmatch(m.name)), None)
            if m is None:
                raise StartError([f"{path} holds no response-NNN/manifest.json, so it is not a response tarball"])
            manifest = json.loads(t.extractfile(m).read().decode("utf-8"))
            top = m.name.split("/", 1)[0]
            handoff = next((x.name for x in members if x.name == f"{top}/handoff.md"), None)
    except (OSError, tarfile.TarError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise StartError([f"{path} is not a response tarball the office can read: {exc}"])
    sid = manifest.get("responds_to")
    if not isinstance(sid, str) or not oh.SID_RE.match(sid):
        raise StartError([f"{path}: its manifest's responds_to is not a session id: {sid!r}"])
    return sid, manifest.get("response_kind"), handoff


def handoff_places(office_root, lane=None):
    """[(label, entry or None, where bale reads)] the office reads bale's
    records in, the folder's own project first, the office last: where a
    session the folder records may have run. A project that cannot be read
    is left out, said under OFFICE_DEBUG."""
    out, office = [], pathlib.Path(office_root)
    entries = office_projects(office_root) or []
    for entry in sorted(entries, key=lambda e: e["name"] != lane):
        try:
            out.append((entry["name"], entry, readable(entry)))
        except BaleError as exc:
            debug(f"{entry['name']}: not read for the handoff ({exc})")
    out.append((OFFICE_LABEL, None, office))
    return out


def record_places(rd, places, sid):
    """(found, also) for a session's record in bale's places (0.55.0):
    found is the first place that records sid, in handoff_places' order,
    as (label, entry, where, its view), or None; also is each later place
    that records it too. Past the first, only places on this machine are
    read, never a host's (a host is reached only where a record had to be
    looked for there before 0.55.0), each said under OFFICE_DEBUG; a place
    that cannot be read is passed over, said the same way."""
    found, also = None, []
    for label, entry, where in places:
        if found is not None and entry is not None and hosted_project(entry):
            debug(f"{label}: not read for a second record of {sid} (it is on a host)")
            continue
        try:
            d = rd.dossier(where, sid)
        except BaleError as exc:
            debug(f"{label}: {sid}'s record not read ({exc})")
            continue
        if d is None:
            continue
        if found is None:
            found = (label, entry, where, session_view(rd, d))
        else:
            also.append((label, entry, where, None))
    return found, also


def record_place_words(place):
    """A place handoff_places names, as a line says it: the project's name,
    or `the office`."""
    return "the office" if place[1] is None else place[0]


def handoff_check(rd, office_root, folder_rel, response=None, cwd=None, downloads=None):
    """What office start N --handoff [RESPONSE] sends, read before anything
    runs: a dict of tarball (a path here, or a bare name for bale's own
    search on a project here), bailout (the session it answers), where,
    project, key (how a line names the folder) and said (lines). Raises
    StartError, naming what it looked for, for: no response; a response
    that is not a bailout or carries no handoff.md; one whose session the
    folder does not record, is still open, ended otherwise, or was a
    read-only sitting; a folder in the filing cabinet."""
    root = pathlib.Path(office_root)
    md = root / folder_rel / "folder.md"
    name = pathlib.PurePosixPath(folder_rel).name
    if not folder_rel.startswith("desk/"):
        raise StartError([f"{folder_rel} is in the filing cabinet: office reopen {name} brings it back to the desk, "
                          f"and office start {name} --handoff then sends the fresh session; nothing ran"])
    parsed = oh.parse_folder(md.read_text(encoding="utf-8"))
    key = (parsed["fields"].get("number") or [""])[0] or name
    sids = parsed["sids"]
    here = pathlib.Path(cwd or os.getcwd())
    looked = ", ".join([str(here)] + [str(d) for d in downloads or []])
    said, bare, path = [], None, None
    if response:
        given = pathlib.Path(response).expanduser()
        at = given if given.is_absolute() else here / given
        if at.is_file():
            path = at.resolve()
        elif "/" in response:
            raise StartError([f"--handoff {response}: no such file; nothing ran"])
        else:
            m = RESPONSE_NAME_RE.match(response)
            if not m or not oh.SID_RE.match(m.group(1)):
                raise StartError([f"--handoff {response}: not a file here, and not a response's name "
                                  "(response-SID.tar.gz) to look for; nothing ran"])
            path = find_in(downloads, response, here)
            if path is None:
                path, note = newest_copy(browser_copies(downloads or [], response), response, StartError)
                if note:
                    said.append(note)
            if path is None:
                bare = response
    else:
        if not sids:
            raise StartError([f"{folder_rel} records no session, so there is no bailout of its own to hand off: "
                              f"office start {key} sends its first; nothing ran"])
        newest = sids[-1]
        want = f"response-{newest}.tar.gz"
        path = find_in([], want, here)
        if path is None:
            path, note = newest_copy(browser_copies(downloads or [], want), want, StartError)
            if note:
                said.append(note)
        if path is None:
            raise StartError([f"no {want} (the response of {newest}, the newest session {folder_rel} records) in "
                              f"{looked or 'the downloads'}: save the bailout there, or name it: office start {key} "
                              "--handoff RESPONSE; nothing ran"])
        said.append(f"the bailout is {path}, the response of {newest}, the newest session {folder_rel} records")
    if path is not None:
        bailout, kind, handoff_md = response_facts(path)
        if kind != "bailout":
            raise StartError([f"{path.name} is a {kind or 'kindless'} response for {bailout}, not a bailout: only a "
                              f"bailout is handed off (office land {bailout} lands it); nothing ran"])
        if handoff_md is None:
            raise StartError([f"{path.name} carries no handoff.md, which bale handoff needs (a bailout's handoff is "
                              "what the fresh session reads first): the worker's response is not one bale hands off; "
                              "nothing ran"])
    else:
        bailout = RESPONSE_NAME_RE.match(bare).group(1)
    if bailout not in sids:
        raise StartError([f"{(path.name if path else bare)} answers {bailout}, which {folder_rel} does not record "
                          f"(it records {', '.join(sids) or 'none'}): the folder that records it hands it off; "
                          "nothing ran"])
    lane = (parsed["fields"].get("lane") or [""])[0].split(":", 1)[0].strip() or None
    found, also = record_places(rd, handoff_places(root, lane), bailout)
    if found is not None and also:
        # bale keeps its records per repo, so a second record is a copy (a
        # tree with .bale/ copied whole, say): the first, the folder's lane
        # first, is the one read, and the rest are said (0.55.0).
        said.append(f"{bailout}'s record is in more than one place "
                    f"({', '.join(record_place_words(p) for p in [found, *also])}): "
                    f"the office reads {record_place_words(found)}'s, the folder's lane first")
    if found is None:
        raise StartError([f"{bailout} is in none of the records the office reads (this office's and its projects'), "
                          "so where it ran is unknown and bale handoff has nowhere to run; nothing ran"])
    label, entry, where, view = found
    shown = "the office" if entry is None else label
    if view["in_flight"]:
        raise StartError([f"{bailout} is still open in {shown}: office land {bailout} lands its bailout first (bale "
                          f"closes the session), then office start {key} --handoff sends the fresh one; nothing ran"])
    if view["read_only"]:
        raise StartError([f"{bailout} was a read-only sitting in {shown}: a sitting is not handed off; the office "
                          "sends another sitting itself (office start --planner); nothing ran"])
    if view["outcome"] != "bailout":
        raise StartError([f"{bailout} ended {outcome_word(view)} in {shown}, not as a bailout, so there is nothing "
                          "to hand off; nothing ran"])
    if bare is not None and entry is not None and hosted_project(entry):
        raise StartError([f"{bare} is not in {looked}: a bailout for a project on {entry['host']} is carried there "
                          "from this machine, so give its path, or add the directory it is in to downloads in "
                          "machine.toml; nothing ran"])
    if bare is not None:
        said.append(f"{bare} is not in {looked}; bale's own search finds it in {shown}")
    return {"tarball": str(path) if path is not None else bare, "bailout": bailout,
            "where": "office" if entry is None else "project", "project": None if entry is None else label,
            "key": key, "said": said}


def report_rows(lines, spec, keys):
    """{key: value} of a text report's summary rows, each found by the
    row's start the surface declares (spec[key + "_line"]); a row the
    report lacks is None."""
    out = {}
    for k in keys:
        start = spec[f"{k}_line"]
        out[k] = next((l[len(start):].strip() for l in lines if l.startswith(start)), None)
    return out


def handoff_refusal_lines(text, key, bailout):
    """The office's line beside bale's own words, for the refusals bale
    handoff is known to make (cmd_handoff, bale 0.4.56); [] for another."""
    low = text.lower()
    if "detached" in low:
        return [f"bale handoff stamps the checked-out branch as the session's target: office start {key} --handoff "
                "RESPONSE --branch NAME checks a branch out in the clone first"]
    if "cannot inherit goal" in low:
        return [f"bale inherits the goal from its record of {bailout} (.bale/sessions/{bailout}/ in the repo it was "
                f"packed in), which this clone does not hold; office start {key} sends a fresh session on the "
                "folder's goal instead"]
    if "bailout responses only" in low:
        return [f"office land {bailout} lands a response that is not a bailout"]
    if "forecast" in low or "overlap" in low or "intersect" in low:
        return ["a session open there holds the forecast the handoff inherits: office land SID brings it back, or "
                f"office withdraw SID closes one never worked; then office start {key} --handoff again"]
    return []


def handoff_session(rd, pack_dir, tarball, scratch=None):
    """bale handoff TARBALL in pack_dir, stdin closed. Returns sid, tarball,
    opener (None: bale prints none) and second_desk (False).

    The session it opened is read as open_bundle reads one: bale status's
    open set before and after, which must name exactly one new session; the
    report's `session id` and `tarball` rows ([surfaces.handoff]) must name
    that session and its request, request-SID.tar.gz in status's outbox. On
    a host the status after, and the scratch's removal, ride the handoff's
    own connection."""
    spec = rd.consumption.surface("handoff")
    before = set(rd.key(rd.status(pack_dir), "status", "sessions") or [])
    hosted = rd.hosted(pack_dir)
    status_argv = rd.consumption.argv("status")
    also = None
    if hosted:
        also = [["bale", *status_argv]] + ([scratch.removal_argv()] if scratch is not None and scratch.made else [])
    proc, shown, where = rd.invoke("handoff", pack_dir, timeout=PACK_TIMEOUT, whole_why=True, also=also,
                                   tarball=tarball)
    lines = proc.stdout.splitlines()
    rd.forget(pack_dir)
    if hosted:
        if scratch is not None and scratch.made:
            scratch.removed_by_step()
        run = rd.also_runs[0]
        if run.returncode == 0:
            try:
                rd._cache[(str(pack_dir), tuple(status_argv))] = rd.parse("status", run, "bale status --json",
                                                                           str(pack_dir))
            except BaleError as exc:
                debug(f"bale status after the handoff did not read from its batch ({exc}); asked on its own")
    st = rd.status(pack_dir)
    new = [x for x in (rd.key(st, "status", "sessions") or []) if x not in before]
    rows = report_rows(lines, spec, ("sid", "tarball"))
    if len(new) != 1:
        raise BaleError("output", f"{shown} exited 0 in {where}, but bale status names {len(new)} newly open "
                                  f"session(s) ({', '.join(new) or 'none'}), so the office cannot tell which it opened")
    sid = new[0]
    if rows["sid"] != sid:
        raise BaleError("output", f"{shown} opened {sid} in {where} by bale status, but its report's session id row "
                                  f"says {rows['sid'] or 'nothing'}")
    name = f"request-{sid}.tar.gz"
    tb = rows["tarball"]
    if tb is None or pathlib.PurePath(tb).name != name or name not in (rd.key(st, "status", "outbox") or []):
        raise BaleError("output", f"{shown} opened {sid} in {where}, but its report's tarball ({tb or 'none'}) is not "
                                  f"the request bale status lists for it ({name})")
    return {"sid": sid, "tarball": tb, "opener": None, "second_desk": False}


def request_facts(path):
    """(sid, goal, packed_at or None, handoff.md's path inside the request or
    None) of a request tarball, read from its manifest and its members."""
    import json
    import tarfile
    with tarfile.open(path) as t:
        members = [m for m in t.getmembers() if m.isfile()]
        m = next((m for m in members if REQUEST_MANIFEST_RE.fullmatch(m.name)), None)
        if m is None:
            raise StartError([f"{path} holds no request-NNN/manifest.json"])
        manifest = json.loads(t.extractfile(m).read().decode("utf-8"))
        top = m.name.split("/", 1)[0] + "/"
        handoff = next((x.name[len(top):] for x in members
                        if x.name.startswith(top) and pathlib.PurePosixPath(x.name).name == "handoff.md"), None)
    packed = (manifest.get("provenance") or {}).get("packed_at")
    return manifest.get("session_id"), manifest.get("goal"), packed, handoff


HANDOFF_OPENER_MARK = ("(This opener is the office's: bale handoff prints none, so office-src composed it from the "
                       "request, in the shape of bale's own.)")


def handoff_opener(request, bailout, folder_rel, has_brief, context_name, constraint=None):
    """The session opener for a handoff's fresh session, composed by the
    office in the shape of bale's (the captured ones, fixtures bale-0.4.45):
    its goal and session from the request, handoff.md named as the first
    thing to read, the folder's brief where it rides in the office's
    context, and the constraint the original pack carried, which bale's
    handoff drops. Its last line says it is the office's."""
    sid, goal, packed, handoff = request_facts(request)
    handoff = handoff or "handoff.md"
    if has_brief:
        brief = (f"The folder's brief, {folder_rel}/brief.md, rides in {context_name} beside the request, with the "
                 "folder (its job, goal and History).")
    else:
        brief = (f"The folder, {folder_rel} (its job, goal and History), rides in {context_name} beside the request; "
                 "the handoff carries no README brief of its own.")
    lines = ['I\'m using "bale", a CLI that packaged the attached request tarball.',
             f"This message opens bale session {sid}.",
             f"Goal, verbatim from the request manifest: {goal}",
             "The docs and tools in the tarball are mine, written for this workflow;",
             "AGENT.md and the four docs beside it are my instructions for this",
             f"session. Read manifest.json first, then AGENT.md, then {handoff},",
             f"the handoff the worker of {bailout} wrote when it bailed out: this",
             "session picks the work up from there. AGENT.md says when the other",
             "four docs are needed.",
             brief,
             "tools/craft_response.py and tools/response_lint.py are",
             "stdlib-only formatters with no network access - conveniences over the",
             "docs, which are the contract; read them before you run them, and a",
             "response assembled by hand is just as valid."]
    if constraint:
        lines.append(f"The original pack's constraint, which bale's handoff does not carry over: {constraint}")
    if packed:
        lines.append(f"Packed at {packed} (UTC).")
    lines += ["bale's dates are UTC and can run a day ahead of this chat's date (a timezone gap, not an error); "
              "date what you write from the session id.",
              "If you need something from me, a fact from my machine or a decision,",
              "end that turn with the matching block from TARBALL.md (a probe, a",
              "light question block, or a clarification response) rather than a",
              "question in prose, which tends to get lost. This is a worker session:",
              "what I need back is one response tarball carrying the finished work.",
              HANDOFF_OPENER_MARK]
    return lines


def start(rd, office_root, folder, where, project, goal, slug, includes, writes, read_only,
          brief, work_class, tray_root, bundle=None, leave_out=(), install_files=(), checked=False,
          bale_rehearsed=False, handoff=None):
    """Pack a session for a folder and fill its out tray. Returns a dict:
    sid, tray, files, opener (lines, or None), carried (what each file
    is), warnings. Raises StartError with lines to print when it cannot
    go on. With a bundle, bale open replays the bundle's own pack line in
    place of a pack the office composes: goal, slug, forecast, includes
    and brief are the bundle's, and the office adds nothing to them.
    leave_out names declared ride-alongs (as declared, or the path each
    resolves to) that stay home for this session; a name no declaration
    matches refuses. The install's doctrine rides unless the packed tree
    ships a doctrine of its own: identical, it rides once (inside the
    tree); different, the install's rides too, named as the install's.
    install_files are install-relative files (a template the session
    writes from) that ride as one more context tarball, made from a
    scratch copy so the install is never written.

    A project on a host is packed on its host (0.15.0): bale's own pack,
    or bale open for a bundle, runs there through the project's shell,
    and the request it makes is carried back into the tray; the brief
    and the bundle travel there first, into one temporary directory the
    office removes on success and on failure. The context tarballs and
    the doctrine are made on this machine, as for any project. checked
    says bin/office has already checked the host this start (reach, the
    bale floor, the repo).

    A bundle is a file on this machine (since 0.49.0 bin/office
    resolve_bundle finds a bare name before bale is asked), so its pack
    line is read where it is; one the office cannot read leaves it unable
    to tell a sitting, said in one line (digest_left_line). Until 0.55.0 a
    bundle_found argument named where bale's rehearsal found it, for a
    bare name bale searched for; no start hands bale a bare name now.

    handoff (0.52.0) is handoff_check's dict for office start N --handoff:
    bale handoff runs in place of a pack (handoff_session), with the
    bailout carried to the host first for a hosted project; goal, slug,
    forecast and includes are bale's, inherited from the bailed session,
    so the office's overlap check is bale's gate there, and the survey is
    not run again, so a refusal leaves the office as it was. The office's
    context rides beside the request (for a session in the office too),
    and the opener is the office's (handoff_opener)."""
    import shutil
    import tempfile
    import office_drafting as od
    import office_drop as odrop
    import office_sort as osort
    office_root = pathlib.Path(office_root).resolve()
    manifest = oh.read_toml(office_root / "floor-plan" / "manifest.toml")
    projects = {p["name"]: p for p in oh.read_projects(manifest) or []}
    entry = None
    if project:
        entry = projects.get(project)
        if entry is None:
            raise StartError([f"no project named {project} in this office's [projects] "
                              f"(it lists: {', '.join(sorted(projects)) or 'none'})"])
        problems = [entry["problem"]] if entry["problem"] else []
        problems += entry["declaration_problems"]
        if problems:
            raise StartError([f"{project}: {p}" for p in problems])
        if entry.get("paused") and where == "project":
            # 0.41.0: nothing is sent to a paused project (bin/office says
            # so before anything is written; this is the backstop).
            raise StartError([oh.paused_line(project)])
    rides, left = ride_choice(entry, project, leave_out)
    # What rides from the project's host (0.50.0): checked in the round
    # start makes there anyway, and packed there by the host's bale.
    host_rides = [r for r in rides if oh.is_host_ride(r)]
    rides = [r for r in rides if not oh.is_host_ride(r)]
    ride_place, ride_rows = None, None
    if host_rides:
        if entry is None or not hosted_project(entry):
            # read_projects reports it as a declaration problem, refused
            # above; this is the backstop.
            raise StartError([f"{project}: {', '.join(host_rides)} rides from its host, and it has none"])
        ride_place = ohost.place_of(entry)
    rd.bale()
    # The project's handbook chapter rides with every session whose lane
    # names the project (0.20.0): in the office's context for a project
    # session, in the request for an office session about it.
    chapter = osort.chapter_rel(project) if project else None
    if chapter and not (office_root / chapter).is_file():
        chapter = None

    # Where the pack runs, and its forecast.
    warnings = []
    if where == "office":
        pack_dir = office_root
        # A standalone sort (folder None, 0.20.0) belongs to no folder: it
        # ships what its includes name and forecasts the notepad and its
        # writes.
        includes = [*([folder] if folder else []), *includes]
        if chapter and chapter not in includes and osort.HANDBOOK not in includes:
            includes.append(chapter)
        if read_only:
            forecast = []
        elif any(w.strip().strip("/") in ("", ".") for w in writes):
            # The whole office (a renovation that declares no narrower
            # forecast): bale's default, the whole tree shipped and
            # forecast, as the renovation's printed pack line was.
            writes, includes, forecast = [], [], None
        else:
            writes = ([folder] if folder else []) + (["notepad"] if (office_root / "notepad").is_dir() else []) \
                + list(writes)
            forecast = writes
    elif hosted_project(entry):
        pack_dir = check_hosted_place(rd, entry, checked)
        forecast = [] if read_only else (list(writes) or list(includes) or None)
        # One connection for every read the pack needs before bale runs
        # (since 0.16.0): the status (open sessions), the paths the pack
        # names and the doctrine the tree holds.
        named = [*(writes if not read_only else []), *includes]
        if bundle:
            bargv = bundle_pack_argv(bundle) if pathlib.Path(bundle).expanduser().is_file() else None
            try:
                b_inc, b_wr, _ = bundle_paths(bargv) if bargv is not None else ([], [], [])
            except ValueError:
                b_inc, b_wr = [], []
            named = [*b_inc, *b_wr]
        # The clone's branch (0.50.0) and what rides from the host ride
        # the same connection, after the reads the pack needs.
        extra = [BRANCH_ARGV] + ([ohost.ride_facts_argv([oh.host_ride_path(r) for r in host_rides])]
                                 if host_rides else [])
        runs = hosted_round(rd, pack_dir, named, doctrine=True, version=bool(bundle), extra=extra)
        say_clone_branch(project, pack_dir, runs[0])
        if host_rides:
            ride_rows = read_host_rides(ride_place, host_rides, runs[1])
    else:
        pack_dir = entry["resolved"]
        ok, why = oh.check_project_dir(pack_dir)
        if not ok:
            raise StartError([f"{project} cannot be packed: {why}"])
        forecast = [] if read_only else (list(writes) or list(includes) or None)
        try:
            say_clone_branch(project, pack_dir, ohost.run_in(ohost.Place(str(pack_dir)), BRANCH_ARGV))
        except ohost.HostError as exc:
            log(f"{project}'s clone at {pack_dir}: its branch could not be read ({exc})")
    if host_rides and ride_rows is None:
        # An office session about a hosted project (--about): no round is
        # made on the host for the pack, so the rides' check is one of its
        # own, before anything is written.
        try:
            run = ohost.run_many(ride_place, [ohost.ride_facts_argv([oh.host_ride_path(r) for r in host_rides])],
                                 chdir=False)[0]
        except ohost.HostError as exc:
            raise StartError([f"{project}: what rides from {entry['host']} could not be checked: {exc}; nothing "
                              "was written"])
        ride_rows = read_host_rides(ride_place, host_rides, run)
    hosted = rd.hosted(pack_dir)
    bundle_supersedes, argv = None, None
    if bundle:
        # The bundle's pack line is the whole session, and the office adds
        # nothing to it. Where the office can read that line (the bundle
        # is a file here), it says the predictable refusal in its own
        # words before bale runs, as for a pack; where it cannot, it says
        # why bale's own words are passed through.
        argv = bundle_pack_argv(bundle)
        if argv is not None and where == "project" and PROJECT_CONSTRAINT not in argv:
            warnings.append(f"this bundle's pack line does not carry the office's constraint (\"{PROJECT_CONSTRAINT}\"); "
                            "the office adds nothing to a bundle, so the session goes out without it")
        includes, writes, forecast = [], [], []
        if argv is not None:
            # Every path the bundle's line names must be in the tree it
            # opens in; bale would refuse otherwise, after the office had
            # gathered everything. Said here, naming where each path is.
            try:
                b_inc, b_wr, b_exc = bundle_paths(argv)
            except ValueError:
                b_inc, b_wr, b_exc = [], [], []
            named = list(dict.fromkeys(b_inc + b_wr))
            label = "office" if where == "office" else project
            places = bundle_places(office_root, named, rd)
            mine = next((m for lab, _, m in places if lab == label), None)
            if mine is None:
                mine = paths_missing_in(pack_dir, named, rd)
            if mine:
                raise StartError([f"the bundle {pathlib.Path(bundle).name} names paths that are not in "
                                  f"{place_words(label)}'s tree, so it cannot open there; nothing ran"]
                                 + bundle_nowhere_lines(bundle, named, places, chosen=label))
            bundle_tree_includes, bundle_tree_excludes = (b_inc or None), b_exc
        if argv is None:
            forecast = None
            why = ("it is a name bale's search finds, not a file here" if not pathlib.Path(bundle).exists()
                   else "its pack line could not be read")
            log(f"the office cannot read this bundle's forecast ({why}); bale open --check ran its gates "
                "against the sessions open there before anything was written, and bale's own words say so if "
                "the open refuses")
        else:
            try:
                forecast, bundle_supersedes = bundle_forecast(argv)
            except ValueError as exc:
                argv, forecast = None, None
                log(f"the office cannot read this bundle's pack line as bale would ({exc}), so it cannot check "
                    "its forecast against the sessions open there; if they overlap, bale's own words below say so")
            # A forecast that does not hold the folder (the whole tree, the
            # desk or the folder itself would) cannot land in it.
            if where == "office" and forecast is not None and forecast != [] \
                    and not any(forecast_holds(e, folder) for e in forecast):
                warnings.append(f"this bundle's forecast does not name {folder}, so the session cannot land in "
                                "its folder")
    if bundle and hosted:
        local_bundle = hosted_bundle_file(bundle, pack_dir)
    gone = paths_missing_in(pack_dir, list(dict.fromkeys([*(writes if not read_only else []), *includes])), rd)
    for p in (writes if not read_only else []):
        if p in gone:
            raise StartError([f"--write {p}: no such path in {pack_dir}; a forecast names existing paths "
                              "(a directory covers new files under it)"])
    for p in includes:
        if p in gone:
            raise StartError([f"--include {p}: no such path in {pack_dir}"])

    # The predictable refusal, said plainly before bale is asked: two
    # sessions whose forecasts overlap never run beside each other. A
    # bundle bale's own rehearsal passed this start (bale_rehearsed:
    # office start's bundle check, which refuses the overlap itself
    # wherever bale's rehearsal does) is bale's to judge: a bundle whose
    # session is still open overlaps that session by construction, and
    # bale takes it as a second desk (0.18.0).
    if not (bundle and argv is None) and not handoff:
        lines = overlap_lines(rd, office_root, pack_dir, where, project, forecast, bundle, bundle_supersedes)
        if lines and not (bundle and bale_rehearsed):
            raise StartError(lines)
        if lines:
            debug("the office's overlap check caught this bundle and bale's rehearsal passed it: bale's to judge")

    # Every check has passed: survey the machine again before anything
    # is packed, so the hung survey this session reads is current, and a
    # refused start commits nothing. A handoff runs none (0.52.0): bale may
    # refuse it, and then nothing in the office moves.
    if handoff:
        debug("no survey before a handoff: a refusal leaves the office as it was; the session reads the survey "
              "as it is")
    else:
        survey_before_pack(office_root)
    # A sitting (a read-only office session, a bundle's included) opens on
    # the digest: written just before the pack, and the drafting table
    # rides with the sitting whenever the office has one. A bundle's pack
    # line is the planner's, so the office adds no include to it; the
    # digest is still written, and rides if the bundle includes the table.
    sitting = where == "office" and forecast == []
    unknown = None
    if where == "office" and bundle and argv is None:
        # The office could not read the bundle's pack line, so its forecast
        # is unknown here. Until 0.21.0 that left a sitting without its
        # digest, and said nothing; the start says why it left the page.
        # Since 0.49.0 the bundle is the file office start found (bin/office
        # resolve_bundle), so the line is the file's own, and where bale's
        # rehearsal found it (0.21.0 to 0.54.0, --bundle-found) is that file.
        unknown = (f"its pack line at {bundle} does not read" if pathlib.Path(bundle).is_file()
                   else f"{bundle} is not a file on this machine")
    if sitting:
        digest_before_pack(office_root)
        if not bundle and (office_root / od.SPACE).is_dir() and od.SPACE not in includes:
            includes = [*includes, od.SPACE]
    elif unknown:
        log(digest_left_line(office_root, pathlib.Path(bundle).name, unknown))

    # The ride-along (0.19.0): every unsorted drop in the in-tray rides
    # with every session the office sends out, so a session that can
    # judge one sorts it (doctrine section 4). For an office session the
    # drops are in the pack's includes (or inside the whole tree a
    # renovation ships); for a project session, in the office's context
    # beside the request; for a bundle, which the office adds nothing to,
    # beside it as a context tarball of their own. The goal is unchanged.
    try:
        riding = [d["rel"] for d in odrop.unsorted(office_root)]
    except (OSError, oh.HelperError) as exc:
        riding = []
        warnings.append(f"the in-tray could not be read, so no drop rides with this session: {exc}")
    drops_place = None
    # A handoff's request is bale's (0.52.0): the office's context rides
    # beside it, as a project session's does, wherever it runs.
    beside = where == "project" or bool(handoff)
    if riding:
        if beside:
            drops_place = "beside the request, in the office's context"
        elif where == "office" and not bundle:
            if includes:
                includes = [*includes, *[r for r in riding if r not in includes]]
                drops_place = "inside the request"
            else:
                drops_place = "inside the request, with the whole office"
        elif where == "office":
            drops_place = "beside the request, in context-in-tray.tar.gz (the office adds nothing to a bundle)"
        else:
            drops_place = "beside the request, in the office's context"

    # The packed trees that may carry a doctrine of their own: the
    # request's (a project session's repo) and, for an office session
    # about a project, the project's tree riding as context.
    if bundle:
        req_tree = pack_dir if argv is not None and where == "project" else None
        req_inc, req_exc = (bundle_tree_includes, bundle_tree_excludes) if req_tree else (None, ())
    else:
        # A handoff's request ships the handoff and its reading plan, never
        # the tree, so no doctrine of the tree's rides in it.
        req_tree = pack_dir if where == "project" and not handoff else None
        req_inc, req_exc = (list(includes) or None), ()
    try:
        own = doctrine_sums(req_tree, req_inc, req_exc, rd)
    except (BaleError, ohost.HostError) as exc:
        raise StartError([f"{project}: {exc}"])
    if own is None and where == "office" and entry is not None and not hosted_project(entry):
        own = doctrine_sums(entry["resolved"], None)
    if own is not None:
        same = own == install_doctrine_sums()
        tree_label = project if where == "project" or entry is not None else "the request"

    tray = Tray(tray_root)
    carried = []
    stage = "a context pack"
    scratch = ohost.Scratch(pack_dir)
    try:
        # The doctrine, from a scratch copy: the install is never written.
        # Once is enough: a packed tree that ships the same doctrine
        # carries it; one that ships another gets the install's beside
        # it, named so, since that is the doctrine the office runs on.
        if own is None:
            carried.append(scratch_context(rd, tray, INSTALL / "doctrine", "the doctrine (OFFICE.md and its checks)"))
        elif same:
            carried.append(f"(the doctrine rides once, inside {tree_label}'s tree at doctrine/: it is the same as "
                           f"the install's, office-src {install_version_here()})")
        else:
            carried.append(scratch_context(rd, tray, INSTALL / "doctrine",
                                           f"the doctrine the office runs on, from the install (office-src "
                                           f"{install_version_here()}); {tree_label}'s tree carries a different "
                                           "doctrine/ of its own", name="context-doctrine-install.tar.gz"))
        if install_files:
            with tempfile.TemporaryDirectory(prefix="office-install-files-") as tmp:
                holder = pathlib.Path(tmp) / "office-src-install"
                for rel in install_files:
                    src = INSTALL / rel
                    if not src.is_file():
                        raise StartError([f"the install has no {rel}, which this session writes from"])
                    (holder / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, holder / rel)
                carried.append(scratch_context(rd, tray, holder, "from the install: " + ", ".join(install_files)))
        context_name = None
        if beside:
            # The office's context rides beside the request, never inside
            # it: the folder and the hung items, named, because include
            # groups do not fire under --context.
            hung = [h for h in oh.space_paths(manifest, "hung") if (office_root / h).exists()]
            # The letterhead rides with a session on a project with an
            # audience (0.25.0): its voice page and forbidden list are what
            # text that leaves for that audience is written to.
            letterhead = ["letterhead"] if (entry is not None and entry.get("audience")
                                            and (office_root / "letterhead").is_dir()
                                            and "letterhead" not in hung) else []
            carried.append(context_into_tray(rd, tray, office_root,
                                              [folder, *hung, *([chapter] if chapter and chapter not in hung else []),
                                               *letterhead, *riding],
                                              f"the office: {folder} and the hung items"
                                              + (f", {project}'s handbook chapter" if chapter else "")
                                              + (f", the letterhead (its voice page first: {project} has an audience)"
                                                 if letterhead else "")
                                              + (f", and {len(riding)} unsorted drop(s)" if riding else "")))
            # Its name in the tray, for a handoff's opener (0.52.0).
            context_name = carried[-1].split(":", 1)[0]
        elif riding and bundle:
            # An office bundle: the drops ride beside it, as their own
            # context tarball, since the bundle's pack line is the planner's.
            carried.append(context_into_tray(rd, tray, office_root, riding,
                                              f"{len(riding)} unsorted drop(s) from the in-tray",
                                              name="context-in-tray.tar.gz"))
        elif entry is not None and hosted_project(entry):
            # An office session about a hosted project: its tree is on
            # the host and does not ride until sessions are sent there.
            carried.append(f"({project}'s tree is on {entry['host']}, so it does not ride; the session reads "
                           "what the office holds about it)")
        elif entry is not None:
            # An office session about a project reads the project's tree.
            carried.append(context_into_tray(rd, tray, entry["resolved"], None, f"{project}'s tree"))
        if chapter and bundle and where == "office":
            # An office bundle about a project: its chapter rides beside it,
            # the bundle's pack line being the planner's (0.20.0).
            carried.append(context_into_tray(rd, tray, office_root, [chapter], f"{project}'s handbook chapter",
                                              name="context-handbook.tar.gz"))
        if sitting and od.SPACE in includes:
            carried.append(f"(the drafting table rides inside the request, its {od.SPACE}/digest.md written "
                           "just before the pack)")
        if riding:
            carried.append(odrop.carried_words([pathlib.PurePosixPath(r).name for r in riding], drops_place))
        for ride in left:
            carried.append(f"(left out of this session: {ride}, which rides with {project} as declared)")
        if entry is not None:
            grouped = {}
            for ride in rides:
                kind, place, inc = ride_plan(oh.expand_project_path(ride))
                if kind == "copy":
                    carried.append(f"{tray.take(place)}: rides with {project} ({ride})")
                elif kind == "scratch":
                    carried.append(scratch_context(rd, tray, place, f"rides with {project} ({ride})"))
                else:
                    grouped.setdefault(place, []).append(inc)
            for place, incs in grouped.items():
                whole = None in incs
                carried.append(context_into_tray(rd, tray, place, None if whole else incs,
                                                  f"rides with {project} ({place}"
                                                  + ("" if whole else ": " + ", ".join(incs)) + ")"))
            if ride_rows:
                stage = f"what rides from {ride_place.host}"
                carried += pack_host_rides(rd, tray, ride_place, ride_rows, project)
        # The session itself, last.
        if handoff:
            given = handoff["tarball"]
            if hosted:
                stage = "sending the bailout to " + pack_dir.host
                given = scratch.send(given)
            stage = "the handoff"
            try:
                opened = handoff_session(rd, pack_dir, given, scratch if hosted else None)
            except BaleError as exc:
                raise StartError([f"bale handoff did not open the fresh session, so no session was opened and no out "
                                  f"tray was made: {exc}"]
                                 + handoff_refusal_lines(str(exc), handoff.get("key") or "N", handoff["bailout"]))
        elif bundle:
            stage = "the bundle's open"
            if hosted:
                stage = "sending the bundle to " + pack_dir.host
                asked = send_bundle(pack_dir, local_bundle, scratch)
                stage = "the bundle's open"
            opened = open_bundle(rd, pack_dir, asked if hosted else bundle, scratch if hosted else None,
                                 as_json=open_json_ok(rd, pack_dir))
            if opened["second_desk"]:
                already = [f for f in folders_naming(office_root).get(opened["sid"], []) if f != folder]
                warnings.append(f"bale opened no new session: {opened['sid']}, opened from this bundle earlier and "
                                "still open, took it as a second desk (bale records the desk on that session and "
                                "prints a desk-qualified opener); the tray and the opener below are that desk's, "
                                "and land brings the session back as before"
                                + (f"; {', '.join(already)} records it too" if already else ""))
        else:
            readme = str(pathlib.Path(brief).resolve()) if brief else None
            if hosted and readme:
                # bale on the host reads the brief there: it travels into
                # the office's temporary directory first.
                stage = "sending the brief to " + pack_dir.host
                readme = scratch.send(readme)
            stage = "the session's pack"
            spec = rd.consumption.surface("pack")
            # The scratch's removal rides the pack's own connection.
            gone_too = [scratch.removal_argv()] if hosted and scratch.made else None
            report, stderr = rd.pack(
                "pack", pack_dir, also=gone_too, goal=goal, slug=slug, includes=includes or None,
                writes=None if read_only or forecast is None else (forecast if where == "office" else (list(writes) or None)),
                constraints=[PROJECT_CONSTRAINT] if where == "project" else None,
                readme_file=readme, no_readme=not brief, read_only=read_only, work_class=work_class)
            if gone_too:
                scratch.removed_by_step()
            opened = {"sid": rd.key(report, "pack", "sid"), "tarball": rd.key(report, "pack", "tarball"),
                      "opener": opener_lines(stderr, spec), "second_desk": False}
    except (BaleError, ohost.HostError) as exc:
        tray.discard()
        raise StartError([f"{stage} failed, so no session was opened and no out tray was made: {exc}"])
    except StartError:
        tray.discard()
        raise
    except (OSError, shutil.Error) as exc:
        tray.discard()
        raise StartError([f"{stage} could not be put in the out tray, so no session was opened: {exc}"])
    finally:
        # The office's temporary directory on the host (the brief, the
        # bundle), removed whether the session opened or not.
        scratch.__exit__(None, None, None)
    sid = opened["sid"]
    if not isinstance(sid, str) or not oh.SID_RE.match(sid):
        raise StartError([f"bale packed, but its report's sid is not a session id: {sid!r}; "
                          f"what was gathered is in {tray.dir}"])
    try:
        if hosted:
            # The request bale made on the host, carried back: it rides in
            # the tray like any other, and stays in the repo's outbox there.
            with tempfile.TemporaryDirectory(prefix="office-request-") as tmp:
                here = pathlib.Path(tmp) / pathlib.PurePosixPath(opened["tarball"]).name
                ohost.fetch_file(pack_dir, opened["tarball"], str(here))
                name = tray.take(here)
        else:
            name = tray.take(opened["tarball"])
        final = tray.finish(sid)
    except (OSError, shutil.Error, ohost.HostError) as exc:
        raise StartError([f"session {sid} is open, but its out tray could not be finished: {exc}",
                          f"what was gathered is in {tray.dir}; the request is {opened['tarball']}"
                          + (f" on {pack_dir.host}" if hosted else ""),
                          (f"record the session in its folder with: office sessions {pathlib.Path(folder).name} {sid}"
                           if folder else "no folder records a standalone sort; office land SID brings it back")])
    if handoff:
        # bale handoff prints no opener (0.52.0): the office composes it from
        # the request now in the tray, and says it is the office's.
        try:
            opened["opener"] = handoff_opener(
                final / name, handoff["bailout"], folder,
                bool(folder) and (office_root / folder / "brief.md").is_file(),
                context_name or "the office's context", PROJECT_CONSTRAINT if where == "project" else None)
        except (OSError, StartError, ValueError) as exc:
            why = "; ".join(exc.lines) if isinstance(exc, StartError) else str(exc)
            warnings.append(f"the request in the tray could not be read for the opener ({why}); the session is open, "
                            "and its manifest names its goal")
            opened["opener"] = None
    # The opener says how many drops ride, in one line after bale's own.
    if riding and opened["opener"] is not None:
        opened["opener"] = [*opened["opener"], "", odrop.opener_line(len(riding), sitting=forecast == [])]
    kind = "an office session" if where == "office" else project + " session"
    if hosted:
        kind += f", packed on {pack_dir.host} and carried back"
    if handoff:
        kind += f", from the handoff of {handoff['bailout']}"
    if bundle:
        kind += f", from the bundle {pathlib.Path(bundle).name}"
        if opened["second_desk"]:
            kind += ", joined as a second desk: the session was already open"
    carried.insert(0, f"{name}: the request ({kind})")
    # The doctrine a sitting from the office goes out under (0.33.0): the
    # install's, which rides with it (inside a packed tree that ships the
    # same one, or beside the request), for its folder's Sessions line.
    doctrine = None
    if sitting:
        try:
            doctrine = install_doctrine_hash()
        except OSError as exc:
            warnings.append(f"the install's doctrine could not be read, so the folder's Sessions line does not stamp "
                            f"the doctrine this sitting went out under: {exc}")
    return {"sid": sid, "tray": str(final), "files": sorted(tray.files), "carried": carried,
            "opener": opened["opener"], "pack_dir": str(pack_dir), "request": str(final / name),
            "warnings": warnings, "sitting": forecast == [] and not handoff, "second_desk": opened["second_desk"],
            "drops": len(riding), "doctrine": doctrine, "handoff": handoff["bailout"] if handoff else None}


# --- a host's bale brought level: office projects level-bale ---------------------------
#
# bale is installed per machine, like git, and a hosted project's bale
# lives on its host. The step copies the bale this machine runs to the
# host the way bale's own releases install: a release tarball (the
# install's files, never its user/ directory, its git or its records)
# carried through the project's shell, and the host's own upgrade.sh run
# on it there (it moves <install>/user/ aside, replaces the rest, puts
# user/ back and runs install.sh, which runs validate.sh). A host with no
# bale gets the tarball unpacked as ~/bale and its install.sh run. The
# host fetches nothing from the network. Only when the occupant asks:
# start and land never upgrade a bale.

# The install's layout on the host, read through its shell: where the
# bale on its login PATH lives, whether its upgrade.sh is there, and the
# names (never the contents) under its user/ directory.
_INSTALL_FACTS = (
    'echo "home=$HOME"; [ -e "$HOME/bale" ] && echo "home_bale=yes" || echo "home_bale=no"; '
    'b=$(command -v bale) || { echo "bale=none"; exit 0; }; r=$(readlink -f "$b"); '
    'root=$(dirname "$(dirname "$r")"); echo "bale=$r"; echo "root=$root"; '
    '[ -f "$root/upgrade.sh" ] && echo "upgrade=yes" || echo "upgrade=no"; '
    'if [ -d "$root/user" ]; then (cd "$root/user" && find . -mindepth 1 -maxdepth 2 | LC_ALL=C sort '
    '| sed "s|^\\./|user=|"); fi'
)
# What a release tarball leaves out of an install: the occupant's own
# subtree, and anything that is not bale's (a git work tree, bale's
# records, caches).
_NOT_RELEASE = ("user",)


def local_bale_install():
    """(install root, version) of the bale this machine runs: the
    directory above the bin/ the bale on PATH resolves into, which must
    hold bale's install scripts. Raises BaleError when it is not a
    release install the office can copy."""
    import shutil
    exe = shutil.which("bale")
    if exe is None:
        raise BaleError("missing", "bale is not on PATH on this machine, so there is no bale to bring a host level with")
    root = pathlib.Path(exe).resolve().parent.parent
    for f in ("bin/bale", "install.sh", "upgrade.sh"):
        if not (root / f).is_file():
            raise BaleError("missing", f"this machine's bale ({pathlib.Path(exe).resolve()}) is not in a release "
                                       f"install: {root} has no {f}, so the office has no install to copy")
    return root, Reader().installed_version()


def release_tarball(root, dest):
    """A release-shaped tarball of the install at root, as bale's builds
    shape one (one top-level bale/ directory), holding every file of the
    install except user/, dot-entries at its top (.git, .bale) and
    caches. Returns the number of files."""
    import tarfile
    root = pathlib.Path(root)
    n = 0
    with tarfile.open(dest, "w:gz") as t:
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root)
            top = rel.parts[0]
            if top in _NOT_RELEASE or top.startswith(".") or "__pycache__" in rel.parts or path.suffix == ".pyc":
                continue
            if path.is_dir() and not path.is_symlink():
                continue
            t.add(path, arcname=str(pathlib.PurePosixPath("bale", *rel.parts)), recursive=False)
            n += 1
    return n


def host_install(place):
    """The host's install facts (_INSTALL_FACTS) as a dict, user/ names
    as a list under "user"."""
    try:
        run = ohost.run_in(place, ["sh", "-c", _INSTALL_FACTS], chdir=False)
    except ohost.HostError as exc:
        raise BaleError(exc.kind if exc.kind in ("unreachable", "path") else "refused", str(exc))
    if run.returncode != 0:
        raise BaleError("refused", f"the bale install on {place.host} could not be read: {run.stderr.strip()}")
    facts = {"user": []}
    for line in run.stdout.splitlines():
        key, sep, value = line.partition("=")
        if not sep:
            continue
        if key == "user":
            facts["user"].append(value)
        else:
            facts[key] = value
    return facts


def level_plan(rd, office_root, name):
    """What level-bale would do for a project: a dict with the place,
    this machine's install and version, the host's version (None when it
    has no bale) and facts, and state: level, behind (the host is older:
    the step replaces it), ahead (the host is newer: refused, never a
    downgrade), absent (no bale there: a first install)."""
    projects = {p["name"]: p for p in office_projects(office_root) or []}
    entry = projects.get(name)
    if entry is None:
        raise StartError([f"no project named {name} in this office's [projects] "
                          f"(it lists: {', '.join(sorted(projects)) or 'none'})"])
    if entry["problem"]:
        raise StartError([f"{name}: {entry['problem']}"])
    if not hosted_project(entry):
        raise StartError([f"{name} is on this machine, where bale is the one installed here; {level_step(name)} "
                          "brings a host's bale level with it, for a project on a host"])
    place = ohost.place_of(entry)
    root, here = local_bale_install()
    facts = host_install(place)
    there = None
    if facts.get("bale") not in (None, "none"):
        try:
            there = rd.installed_version(place)
        except BaleError as exc:
            if exc.kind == "unreachable":
                raise
            raise StartError([f"{name}: bale on {place.host} ({facts['bale']}) did not say its version: {exc}"])
    if there is None:
        state = "absent"
    else:
        c = oh.compare_versions(there, here)
        state = "level" if c == 0 else ("behind" if c < 0 else "ahead")
    return {"name": name, "place": place, "root": root, "here": here, "there": there, "facts": facts,
            "state": state}


def level_bale(rd, office_root, name):
    """Install on a project's host the bale this machine runs, keeping
    the host's user/ (its global bale.toml and hook store), and say what
    was there and what is there now. Returns the lines to print; raises
    StartError when it cannot, having changed nothing it can avoid."""
    import tempfile
    plan = level_plan(rd, office_root, name)
    place, here, there, facts = plan["place"], plan["here"], plan["there"], plan["facts"]
    if plan["state"] == "level":
        return [f"{name}: bale {there} on {place.host} is level with this machine's; nothing to do"]
    if plan["state"] == "ahead":
        raise StartError([f"{name}: bale {there} on {place.host} is newer than this machine's {here}; the office "
                          "never moves a bale back. Bring this machine's bale up first, then run this again"])
    if plan["state"] == "behind" and facts.get("upgrade") != "yes":
        raise StartError([f"{name}: bale {there} on {place.host} ({facts.get('root')}) has no upgrade.sh beside it, "
                          "so it is not a release install the office can replace; upgrade it there by hand"])
    if plan["state"] == "absent" and facts.get("home_bale") == "yes":
        raise StartError([f"{name}: there is no bale on the login PATH on {place.host}, but {facts.get('home')}/bale "
                          "exists; the office installs only where nothing is, so look at it there first"])
    lines = []
    with tempfile.TemporaryDirectory(prefix="office-level-") as tmp:
        tarball = pathlib.Path(tmp) / f"bale-v{here}.tar.gz"
        count = release_tarball(plan["root"], tarball)
        log(f"made a release tarball of this machine's bale {here} ({plan['root']}, {count} files, user/ left out)")
        try:
            with ohost.Scratch(place) as scratch:
                remote = f"{scratch.path}/{tarball.name}"
                ohost.send_file(place, str(tarball), remote)
                log(f"sent it to {place.host}; running "
                    + ("the host's own upgrade.sh, which keeps user/ and runs install.sh and validate.sh"
                       if plan["state"] == "behind" else "a first install: unpacked as ~/bale, then its install.sh"))
                spec = rd.consumption.surface("upgrade")
                if plan["state"] == "behind":
                    argv = [f"{facts['root']}/{spec['script']}", *spec["flags"], remote]
                else:
                    first, *flags = spec["first_install"]
                    argv = ["sh", "-c", 't="$1"; s="$2"; shift 2; cd "$HOME" && [ ! -e bale ] && tar -xzf "$t" '
                                        '&& exec "$HOME/bale/$s" "$@"', "office-install", remote, first, *flags]
                run = ohost.run_in(place, argv, timeout=ohost.TRANSFER_TIMEOUT, chdir=False)
        except ohost.HostError as exc:
            raise StartError([f"{name}: bale on {place.host} was not brought level: {exc}"])
    said = [l for l in (run.stdout + "\n" + run.stderr).splitlines() if l.strip()]
    if run.returncode != 0:
        raise StartError([f"{name}: the install on {place.host} exited {run.returncode}; its last words:"]
                         + [f"  {l}" for l in said[-15:]])
    for l in said[-12:]:
        log(f"{place.host}: {l}")
    rd.forget(place)
    try:
        now = rd.installed_version(place)
        after = host_install(place)
    except BaleError as exc:
        raise StartError([f"{name}: the install on {place.host} finished, but bale there could not be read "
                          f"afterwards: {exc}"])
    if now != here:
        raise StartError([f"{name}: the install on {place.host} exited 0, but bale there says {now}, not {here}; "
                          "its words above say why"])
    kept = facts["user"]
    if kept and after["user"] != kept:
        lost = sorted(set(kept) - set(after["user"]))
        raise StartError([f"{name}: bale {now} is on {place.host}, but its user/ is not as it was"
                          + (f": missing {', '.join(lost)}" if lost else "") + f" (look in {facts.get('root')}.user-backup-*)"])
    lines.append(f"{name}: bale on {place.host} was {there or 'not installed'}, and is now {now}, this machine's "
                 f"(from {plan['root']})")
    if kept:
        lines.append(f"  its user/ was kept: {', '.join(n for n in kept if '/' not in n)}")
    else:
        lines.append("  it had no user/ (no global bale.toml); bale config init --global there sets one")
    return lines


# --- bringing a session back: office land -------------------------------------------
#
# The return trip. office land finds the session a response answers,
# runs bale apply (bale retry for a held one) in the repo the session
# belongs to with the occupant's own terminal as its stdin, so bale's
# questions reach him as bale asks them and the office answers none,
# then reads what happened from the session's dossier, never from bale's
# words, and hands back the blocks bale printed for him to carry. The
# shell does the asking and the after-land actions; this does the rest.

# A response tarball's name, and a browser's second copy of it.
RESPONSE_NAME_RE = oh.LazyPattern(r"^response-(.+?)(?: \(\d+\))?\.tar\.gz$")
# The commits that leave office start's record of a session in a folder:
# office sessions recording it, and office land putting it back.
RECORD_SUBJECTS = ("office sessions: {sid} in ", "office land: {sid} recorded again in ")


class LandError(StartError):
    """office land cannot go on, said as lines a person can act on."""


def repos(office_root, rendering=False):
    """([(label, project entry or None, directory)], problem lines): the
    office's own registry, when bale keeps one there, and every project
    it scopes that can be read. rendering (0.41.0) passes over a paused
    project, its line the paused line: the walk-in's Next line and the
    home screen read nothing of it, while a verb (land, withdraw) still
    finds a session out there."""
    out, bad = [], []
    own = office_registry(office_root)
    if own is not None:
        out.append((OFFICE_LABEL, None, own))
    for p in office_projects(office_root) or []:
        try:
            out.append((p["name"], p, rendered(p) if rendering else readable(p)))
        except BaleError as exc:
            bad.append(unread_line(p["name"], exc))
    return out, bad


def open_anywhere(rd, office_root, sid=None, unreachable=None, rendering=False):
    """(sessions, problems): every session open in a repo the office
    reads, each a dict: sid, label, project, repo, read_only, folders
    (the folders whose Sessions section names it, space/name). For a
    hosted repo the status, and with sid that session's dossier, travel
    in one connection (since 0.16.0); a host that does not answer is a
    problem line and, given the list unreachable, (label, line) in it."""
    naming = folders_naming(office_root)
    found, problems = repos(office_root, rendering)
    out = []
    for label, p, cwd in found:
        try:
            if rd.hosted(cwd):
                rd.prefetch(cwd, [("status", {})] + ([("dossier", {"sid": sid})] if sid else []))
            for sid_here, ro in rd.open_sessions(cwd):
                out.append({"sid": sid_here, "label": label, "project": p["name"] if p else None, "repo": str(cwd),
                            "place": cwd, "host": p["host"] if p else None,
                            "read_only": ro, "folders": naming.get(sid_here, []),
                            "after_land": list(p["after_land"]) if p and not p["declaration_problems"] else [],
                            "after_land_problem": "; ".join(p["declaration_problems"]) if p else "",
                            # 0.41.0: land closes an audience project's
                            # folder at delivery, and ends on deliver's line.
                            "audience": (p.get("audience") or None) if p else None})
        except BaleError as exc:
            problems.append(unread_line(label, exc))
            if exc.kind == "unreachable" and unreachable is not None:
                unreachable.append((label, str(exc)))
    return out, problems


def landable_out(x):
    """Whether an open session is one the office has out: a folder records
    it, or it is a standalone sort in the office's own registry (0.20.0);
    a read-only sitting lands nothing."""
    import office_sort as osort
    return not x["read_only"] and bool(x["folders"] or (x["label"] == OFFICE_LABEL and osort.is_sort_sid(x["sid"])))


def sessions_out(rd, office_root):
    """(sessions, problems): the sessions the office has out, the open
    ones a folder records and the standalone sort, read-only sittings
    aside (they land nothing)."""
    every, problems = open_anywhere(rd, office_root)
    return [x for x in every if landable_out(x)], problems


def sorts_out(rd, office_root):
    """The standalone sorts open in the office's own registry: their ids.
    [] when the office has no registry. Raises BaleError when it has one
    that cannot be read."""
    import office_sort as osort
    own = office_registry(office_root)
    if own is None:
        return []
    return [sid for sid in rd.key(rd.status(own), "status", "sessions") or [] if osort.is_sort_sid(sid)]


def responds_to(path):
    """The session a response tarball answers: its manifest's
    responds_to. The tarball is the worker's file, not bale's records."""
    import json
    import tarfile
    try:
        with tarfile.open(path) as t:
            for m in t.getmembers():
                if m.isfile() and re.fullmatch(r"response-\d{3}/manifest\.json", m.name):
                    sid = json.loads(t.extractfile(m).read().decode("utf-8")).get("responds_to")
                    if isinstance(sid, str) and oh.SID_RE.match(sid):
                        return sid
                    raise LandError([f"{path}: its manifest's responds_to is not a session id: {sid!r}"])
    except (OSError, tarfile.TarError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise LandError([f"{path} is not a response tarball the office can read: {exc}"])
    raise LandError([f"{path} holds no response-NNN/manifest.json, so it is not a response tarball"])


def git(root, *args, check=True, binary=False):
    """git in the office, its output as text (bytes with binary=True, for
    a page's exact bytes); a failure is a LandError naming the command."""
    import subprocess
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=not binary, timeout=60)
    if check and proc.returncode != 0:
        err = proc.stderr.decode(errors="replace") if binary else proc.stderr
        raise LandError([f"git {' '.join(args)} failed in {root}: {err.strip() or proc.returncode}"])
    return proc


def folder_record(office_root, folder, sid):
    """How the office's record of sid sits in folder/folder.md, for a
    session packed in the office (whose forecast holds the folder, so a
    response may rewrite it): the commit that wrote the record, and
    whether the folder can be put back as it was packed, because nothing
    else touched it since. A folder in the filing cabinet only gains
    lines, so it is never put back."""
    rel = f"{folder}/folder.md"
    out = {"path": rel, "commit": None, "restorable": False, "why": None}
    for subject in RECORD_SUBJECTS:
        proc = git(office_root, "log", "-n", "1", "--format=%H %s", "--fixed-strings",
                   f"--grep={subject.format(sid=sid)}", "--", rel, check=False)
        line = proc.stdout.strip()
        if line:
            commit = line.split()[0]
            if out["commit"] is None or git(office_root, "merge-base", "--is-ancestor", out["commit"], commit,
                                             check=False).returncode == 0:
                out["commit"] = commit
    if out["commit"] is None:
        return out
    last = git(office_root, "log", "-n", "1", "--format=%H", "--", rel, check=False).stdout.strip()
    dirty = git(office_root, "diff", "--quiet", "HEAD", "--", rel, check=False).returncode != 0
    if folder.startswith("filing-cabinet/"):
        out["why"] = (f"{rel} is in the filing cabinet, whose folders only gain lines, so the office does not take its "
                      f"record of {sid} out while bale lands")
    elif last != out["commit"] or dirty:
        out["why"] = (f"{rel} changed after the office recorded {sid} in it, so the office cannot put it back as it "
                      "was packed")
    else:
        out["restorable"] = True
    if out["why"]:
        out["why"] += ("; if the response rewrites it, bale refuses it as base drift and prints the line that "
                       "lands it over those changes")
    return out


# --- where downloads land (0.16.0) ------------------------------------------------
#
# The office's own setting, machine.toml's downloads (a list of
# directories), asked once by bin/office and never read from bale's
# config. land finds a session's response there by name, and start a
# bundle for a hosted project; a browser that saves a name twice writes
# `STEM (1).EXT`, so every copy of a name is a candidate and the newest by
# modification time wins, named. Two copies with the same time refuse.

def name_parts(name):
    """(stem, extension) of a downloaded file's name: .tar.gz counts as
    one extension, as a response's does."""
    for ext in (".tar.gz", ".bale-bundle"):
        if name.endswith(ext):
            return name[:-len(ext)], ext
    p = pathlib.PurePath(name)
    return (name[:-len(p.suffix)], p.suffix) if p.suffix else (name, "")


def browser_copies(directories, name):
    """[(path, mtime_ns)] of every file named name, or a browser's later
    copy of it (`STEM (N).EXT`), in the directories, newest first. A
    directory that is not there is skipped, said under OFFICE_DEBUG."""
    stem, ext = name_parts(pathlib.PurePath(name).name)
    pattern = re.compile(re.escape(stem) + r"(?: \(\d+\))?" + re.escape(ext))
    out = []
    for d in directories:
        d = pathlib.Path(os.path.expanduser(str(d)))
        try:
            entries = list(d.iterdir())
        except OSError as exc:
            debug(f"the downloads directory {d} cannot be read: {exc}")
            continue
        for f in entries:
            if pattern.fullmatch(f.name) and f.is_file():
                out.append((f.resolve(), f.stat().st_mtime_ns))
    return sorted(out, key=lambda x: (-x[1], str(x[0])))


def newest_copy(copies, name, error=None):
    """(path, note) for the newest of browser_copies: note says which was
    taken when there were several (None when one), and two copies with the
    same modification time at the top refuse, naming both."""
    error = error or LandError
    if not copies:
        return None, None
    if len(copies) > 1 and copies[0][1] == copies[1][1]:
        raise error([f"{copies[0][0]} and {copies[1][0]} were saved at the same moment, so the office cannot tell "
                     f"which copy of {name} is the newest; name the one to take by its path"])
    if len(copies) == 1:
        return copies[0][0], None
    others = ", ".join(p.name for p, _ in copies[1:])
    return copies[0][0], (f"{len(copies)} copies of {name} are in the downloads; took the newest, {copies[0][0]} "
                          f"(left: {others})")


def differing_bundle_copies(taken, copies):
    """The names of the copies (browser_copies) of a planner bundle whose
    brief differs from the one taken (0.57.0): two bundles saved under
    one stem, which office start --bundle STEM says when it takes the
    newest. Empty when the name is not a bundle's, or every copy carries
    the taken one's brief (a true browser copy), or none says (no brief,
    or unreadable: bundle_brief_sha256)."""
    if not str(taken).endswith(".bale-bundle"):
        return []
    mine = bundle_brief_sha256(taken)
    out = []
    for p, _ in copies:
        if p == taken:
            continue
        theirs = bundle_brief_sha256(p)
        if theirs != mine and (theirs or mine):
            out.append(p.name)
    return out


def find_in(directories, name, cwd=None):
    """A bare name, exactly as given, in the current directory and then
    each downloads directory in order (bale's own order for a search):
    its path, or None."""
    for d in ([cwd] if cwd else []) + list(directories or []):
        p = pathlib.Path(os.path.expanduser(str(d))) / name
        if p.is_file():
            return p.resolve()
    return None


def plan_place(plan):
    """Where a land plan's bale runs: the repo's directory, or for a
    hosted project its Place, rebuilt from the plan's place."""
    pl = plan.get("place")
    if pl:
        return ohost.Place(pl["path"], pl["host"], pl["shell"], pl["connect"], pl.get("name"))
    return plan["repo"]


def printed_line(place, command):
    """A command for the occupant to type on this machine that runs
    command where a hosted place is: the stored shell with the command
    quoted for the far side's login shell as well (an ssh prefix hands
    the far side one string)."""
    import shlex
    words = shlex.split(place.shell)
    inner = shlex.quote(command)
    if words and words[0] == "ssh":
        inner = f'"{inner}"' if not any(c in inner for c in '"$`\\') else shlex.quote(inner)
    return " ".join(shlex.quote(w) for w in words) + " " + inner


def land_plan(rd, office_root, sid=None, folder=None, response=None, cwd=None, downloads=None,
              accept_checkpoint_change=False, accept_base_drift=None):
    """The one session to land and how: a dict (sid, label, project,
    repo or place, where, folders, verb apply or retry, tarball,
    needs_response, response_default, needs_downloads, took, attempts_before,
    record, after_land, problems, accept_checkpoint_change,
    accept_base_drift). Raises LandError with lines when there is none, or
    more than one.

    accept_checkpoint_change and accept_base_drift (a list of paths, as
    typed) are bale's two per-invocation accepts (0.37.0), passed to the
    apply or retry this landing runs when the occupant typed them on
    office land, and only then; the plan carries them so land_run hands
    them on and the next line can restate them. A read-only sitting lands
    nothing, so there they are refused, before anything ends.

    downloads is machine.toml's list, or None when it is not set. A
    session on a hosted project (0.16.0) needs its response on this
    machine: a path given, a bare name found here or in the downloads, or
    the newest copy of response-SID.tar.gz there; with the setting unset
    the plan comes back with needs_downloads, and bin/office asks once. Its
    plan carries place (path, host, shell, connect) instead of repo. For a
    local project bale's own search finds the response, as before, unless
    the downloads hold several copies of its name: then the newest is
    passed to bale by its path, and took says so."""
    tarball, bare = None, False
    if response:
        given = pathlib.Path(response).expanduser()
        here = given if given.is_absolute() else pathlib.Path(cwd or os.getcwd()) / given
        if here.is_file():
            tarball = str(here.resolve())
            want = responds_to(here)
        elif "/" in response:
            raise LandError([f"no such file: {response}"])
        else:
            m = RESPONSE_NAME_RE.match(response)
            if not m or not oh.SID_RE.match(m.group(1)):
                raise LandError([f"{response} is not a file here, and not a response tarball's name "
                                 "(response-SID.tar.gz) for bale to find in its search directories"])
            tarball, want, bare = response, m.group(1), True
        if sid and sid != want:
            raise LandError([f"{response} answers {want}, not {sid}"])
        sid = want
    lost = []
    every, problems = open_anywhere(rd, office_root, sid, lost)

    def unanswered(lead):
        # A host that did not answer may hold the session: it stops land
        # here, before anything is carried, with the reach's one line.
        if not lost:
            return None
        return LandError([f"{lead}; and {label}'s host did not answer, so it may be out there: {line}"
                          for label, line in lost] + ["nothing was carried and nothing ran"]
                         + [p for p in problems if not any(p.startswith(f"{label}: ") for label, _ in lost)])

    if folder:
        found = [x for x in every if folder in x["folders"]]
        if sid:
            found = [x for x in found if x["sid"] == sid]
        if not found:
            raise unanswered(f"no session {sid + ' ' if sid else ''}is out for {folder} where the office could read") \
                or LandError([f"no session {sid + ' ' if sid else ''}is out for {folder}: none it records is open "
                              "in this office or a project it scopes (office sessions FOLDER shows how each went)"]
                             + problems)
    elif sid:
        found = [x for x in every if x["sid"] == sid]
        if not found:
            raise unanswered(f"{sid} is not open where the office could read") \
                or LandError([f"{sid} is not open in this office or in any project it scopes, so there is "
                              "nothing to land (office sessions FOLDER shows how it went)"] + problems)
    else:
        found = [x for x in every if landable_out(x)]
        if not found:
            raise unanswered("no session is out where the office could read") \
                or LandError(["no session is out: none that a folder records is open in this office or in a "
                              "project it scopes (office start sends one out)"] + problems)
    landable = [x for x in found if not x["read_only"]]
    accepts = accept_flags(accept_checkpoint_change, accept_base_drift)
    if not landable:
        if accepts:
            ended = found[0]["sid"] if len(found) == 1 else "the sitting"
            raise LandError([f"{ended} is a read-only sitting: it lands nothing, so bale has nothing for "
                             f"{' '.join(accepts)} to accept; nothing was ended (office land {ended}, without "
                             "it, ends it when the sitting is over)"])
        return sitting_plan(found, None if bare else tarball, problems, response if bare else None, office_root)
    if len(landable) > 1:
        raise LandError(["more than one session is out; name one: office land SID"]
                        + [f"  {x['sid']}  ({x['label']}; {', '.join(x['folders']) or 'no folder records it'})"
                           for x in landable])
    x = landable[0]
    d = rd.dossier(x["place"], x["sid"])
    view = session_view(rd, d) if d is not None else None
    held = bool(view and view["in_flight"] and view["outcome"] == "held")
    plan = dict(x)
    place = plan.pop("place", None)  # the plan is written as JSON: repo, or place for a hosted project
    plan.update(verb="retry" if held else "apply", held=held, tarball=None, needs_response=False,
                response_default=None, needs_downloads=False, took=[],
                attempts_before=len(response_attempts(view)) if view else 0,
                office_session=x["label"] == OFFICE_LABEL, problems=problems, record=None, where=str(place),
                accept_checkpoint_change=bool(accept_checkpoint_change),
                accept_base_drift=list(accept_base_drift or []))
    name = f"response-{x['sid']}.tar.gz"
    if x["host"]:
        plan.pop("repo", None)
        plan["place"] = {"path": place.path, "host": place.host, "shell": place.shell, "connect": place.connect,
                         "name": place.name}
        if tarball is not None and not bare:
            plan["tarball"] = tarball
        elif bare:
            found_at = find_in(downloads, tarball, cwd or os.getcwd())
            if found_at is None:
                looked = ", ".join([str(cwd or os.getcwd())] + [str(d) for d in downloads or []])
                raise LandError([f"{tarball} is not in {looked}; a response for a project on {x['host']} is carried "
                                 "there from this machine, so give its path, or add the directory it is in to "
                                 "downloads in machine.toml"])
            plan["tarball"] = str(found_at)
        elif downloads is None:
            plan["needs_downloads"] = True
        else:
            path, note = newest_copy(browser_copies(downloads, name), name)
            if held and (path is None or note is None):
                # After a HOLD the corrected response is asked for, the
                # only copy offered as the answer: it may be the held one.
                plan.update(needs_response=True, response_default=str(path) if path else None)
            elif path is None:
                raise LandError([f"no {name} in the downloads ({', '.join(map(str, downloads)) or 'none listed'}); "
                                 f"a response for a project on {x['host']} is carried there from this machine: "
                                 f"give it: office land {x['sid']} --response FILE"])
            else:
                plan["tarball"] = str(path)
                if note:
                    plan["took"].append(note)
                plan["took"].append(f"{path.name} is the response for {x['sid']}; it travels to {x['host']}")
    else:
        if tarball is not None:
            plan["tarball"] = tarball
        elif downloads:
            path, note = newest_copy(browser_copies(downloads, name), name)
            if note:
                # bale's own search takes the plain name first; after a HOLD
                # the corrected response is usually the (1).
                plan["tarball"] = str(path)
                plan["took"].append(note + "; bale gets it by its path, since its own search takes the plain name first")
        if plan["tarball"] is None:
            plan["tarball"] = name
            plan["needs_response"] = held
    if plan["office_session"]:
        for f in x["folders"]:
            plan["record"] = folder_record(office_root, f, x["sid"])
            plan["record"]["folder"] = f
            break
    # Where the response is on this machine, for the pages office land
    # files from its notes.md after an applied landing (0.17.0): a path
    # the plan already holds, or the bare name found here and then in
    # the downloads; None when only bale's own search knows.
    tb = plan.get("tarball")
    if tb and "/" in str(tb) and pathlib.Path(tb).is_file():
        plan["response_here"] = str(tb)
    else:
        found_at = find_in(downloads, name, cwd or os.getcwd()) if tb else None
        plan["response_here"] = str(found_at) if found_at else None
    return plan


def sitting_plan(found, tarball, problems, bare=None, office_root=None):
    """The plan for ending a read-only sitting, named by its id or its
    folder: land runs bale unlock in its repo (through the shell, for a
    project on a host), and nothing else. Only a sitting a folder records,
    or a meeting's prep the calendar records (0.26.0, which no folder
    does), is the office's to end (one started by hand in a project is
    that project's business), and a sitting has no response to land."""
    import office_meeting as om
    if len(found) > 1:
        raise LandError(["more than one read-only sitting is open for that folder; name one: office land SID"]
                        + [f"  {x['sid']}  ({x['label']})" for x in found])
    x = found[0]
    prep = (office_root is not None and x["label"] == OFFICE_LABEL
            and om.prep_of(office_root, x["sid"]) is not None)
    if not x["folders"] and not prep:
        raise LandError([f"{x['sid']} is a read-only session no folder records, so it is not a sitting the office sent "
                         f"out and office land does not end it; bale unlock {x['sid']}, in {x['place']}, ends it by hand"])
    if tarball is not None or bare is not None:
        raise LandError([f"{x['sid']} is a read-only sitting: it lands nothing, so there is no response to land; "
                         f"office land {x['sid']}, with no response, ends it when the sitting is over"])
    plan = dict(x)
    place = plan.pop("place", None)
    plan.update(verb="unlock", held=False, tarball=None, needs_response=False, response_default=None,
                needs_downloads=False, took=[], attempts_before=0,
                office_session=x["label"] == OFFICE_LABEL, problems=problems, record=None, where=str(place))
    if x["host"]:
        plan.pop("repo", None)
        plan["place"] = {"path": place.path, "host": place.host, "shell": place.shell, "connect": place.connect,
                         "name": place.name}
    return plan


def end_sitting(rd, office_root, plan, day, by="office land", successor=None):
    """bale unlock for a read-only sitting, then one History line in each
    folder that records it, committed alone. The folder keeps its status:
    a planning folder may outlive one sitting, and closing it is the
    occupant's (office close). by names the verb that closed it, and
    successor (0.43.0: office start, ending the sitting a brief succeeds)
    the session sent in its place. Returns (words, told lines)."""
    sid, repo = plan["sid"], plan.get("where") or plan["repo"]
    try:
        report = rd.unlock(plan_place(plan), sid)
    except BaleError as exc:
        raise LandError([f"bale unlock {sid} did not end the sitting: {exc}"])
    # From here the sitting is closed in bale, and a second land would be
    # refused as not open, so nothing below raises: what could not be
    # read or written is said, and the words still come back.
    told = []
    try:
        reason = rd.key(report, "unlock", "closure_reason")
        sweep = rd.key(report, "unlock", "sweep")
        swept = bool(sweep) and rd.key(sweep, "unlock", "sweep.status") == "committed"
        detail = rd.key(sweep, "unlock", "sweep.detail") if sweep else "bale reported no sweep"
    except BaleError as exc:
        reason, swept, detail = "reason unread", False, f"its report could not be read ({exc})"
    told.append(f"bale closed {sid} in {plan['label']} ({reason}); its sweep: {detail}")
    if not swept:
        told.append(f"bale did not commit its record of {sid}; git status in {repo} shows what it left")
    root = pathlib.Path(office_root)
    for folder in plan["folders"]:
        rel = f"{folder}/folder.md"
        try:
            _, wrote = oh.folder_event(root / rel, day, "ended", f"{sid}, a read-only sitting, closed by {by}"
                                       + (f", succeeded by {successor}" if successor else ""))
        except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
            told.append(f"{rel}: the end of {sid} could not be written there ({exc}); the sitting is closed in bale")
            continue
        if not wrote:
            told.append(f"{rel} has no History section, so the end of {sid} is not written there")
            continue
        try:
            git(root, "add", "--", rel)
            git(root, "commit", "-q", "-m", f"{by}: {sid} ended in {pathlib.Path(folder).name}", "--", rel)
        except LandError as exc:
            # The sitting is already closed in bale; the line stands on
            # disk and the occupant hears why it is not committed.
            told.append(f"{rel}: History: {day} ended: {sid}, written but not committed ({' '.join(exc.lines)})")
            continue
        told.append(f"{rel}: History: {day} ended: {sid}")
    names = ", ".join(plan["folders"])
    words = f"Ended: the sitting {sid} is closed in {plan['label']}; it landed nothing, by design."
    if names:
        words += f" {names} stays as it was: closing a folder is yours (office close FOLDER)."
    return words, told


def ends_plan(rd, office_root, request, successor):
    """(plan, said) for the sitting a planner's brief succeeds (0.43.0): the
    `--- ENDS SID ---` line of the request's brief, read as the LANDS line
    is, and when SID is a read-only sitting open where the office reads and
    a folder records it, the plan office land would end it by (sitting_plan),
    for land-end. plan is None when there is nothing to end; said is the
    lines to say either way: a line that does not read, a sitting that is
    not open, not a sitting or recorded by no folder, or the successor
    itself. Nothing here ends anything."""
    text = oh.brief_from_request(request)
    if text is None:
        return None, []
    sid, said = oh.brief_ends(text)
    said = [f"the brief's ENDS line: {p}" for p in said]
    if sid is None:
        return None, said
    if sid == successor:
        return None, said + [f"the brief's ENDS line names {sid}, the session it sent, so nothing is ended"]
    every, problems = open_anywhere(rd, office_root, sid=sid)
    found = [x for x in every if x["sid"] == sid]
    if not found:
        unread = f" ({'; '.join(problems)})" if problems else ""
        return None, said + [f"the brief succeeds {sid}, which is not open where the office reads{unread}, so nothing "
                             "is ended"]
    x = found[0]
    if not x["read_only"]:
        return None, said + [f"the brief succeeds {sid}, which is open and not a read-only sitting, so start does not "
                             f"end it (office land {sid} lands it)"]
    if not x["folders"]:
        return None, said + [f"the brief succeeds {sid}, a read-only session no folder records, so it is not the "
                             "office's to end"]
    return sitting_plan([x], None, problems, office_root=office_root), said


# --- withdrawing a session that was never worked (0.24.0) -------------------------------
#
# A session the office sent out that will never go to a model (the
# occupant opened it, and the plan changed) has only bale's unlock, typed by
# hand with its id in its repo. office withdraw, and the home screen's w
# key, do it for him: the session named by its folder, asked once (closing
# cannot be undone), bale unlock with bale's own reason, abandoned, in the
# repo it is open in (through its shell for a project on a host), and a
# History line in each folder that records it. A session with a response
# waiting, or one bale has started to apply, is never offered: the first is
# land's, the second bale's revert. A read-only sitting is office land's to
# end, as before.

WITHDRAW_REASON = "abandoned"


def withdraw_view(rd, office_root, downloads=None):
    """(offered, kept back, problems): the sessions the office has out that
    can be withdrawn, each open_anywhere's dict plus created; and the ones
    that cannot, each (session dict, why). downloads is machine.toml's list,
    or None when it is not set, and then no response there can be seen."""
    out, problems = sessions_out(rd, office_root)
    offered, kept = [], []
    for x in out:
        try:
            d = rd.dossier(x["place"], x["sid"])
        except BaleError as exc:
            kept.append((x, f"its record cannot be read ({exc}), so whether bale started to apply it is unknown"))
            continue
        view = session_view(rd, d) if d is not None else None
        tried = [a for a in (view["attempts"] if view else []) if a["command"] not in ("pack", "open")]
        if tried:
            kept.append((x, f"bale has started to apply it ({outcome_word(view)}): office land brings it back, and "
                            "bale revert undoes an apply"))
            continue
        name = f"response-{x['sid']}.tar.gz"
        copies = browser_copies(downloads or [], name)
        if copies:
            kept.append((x, f"a response for it is in your downloads ({copies[0][0]}): office land brings it back"))
            continue
        offered.append(dict(x, created=(view["created"] if view else "") or ""))
    offered.sort(key=lambda s: (s["created"] or "~", s["sid"]))
    return offered, kept, problems


def alone_in(office_root, folder, sid):
    """Whether a folder records sid and no other session: one minted for
    that session alone, which a withdrawal leaves with nothing to do."""
    try:
        parsed = oh.parse_folder((pathlib.Path(office_root) / folder / "folder.md").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        debug(f"{folder}/folder.md could not be read: {exc}")
        return False
    return parsed["sids"] == [sid]


def withdraw(rd, office_root, sid, day, downloads=None):
    """Withdraw one session the office has out and that was never worked:
    bale unlock SID --reason abandoned in its repo (through the project's
    shell on a host), then a `withdrawn` History line in each folder that
    records it, committed alone. Returns (words, told lines, alone): alone
    names the folders that recorded this session and no other, each said
    with the line that closes it, never closed here. Raises StartError
    when the session is not one that can be withdrawn, or bale refuses
    (its words whole)."""
    offered, kept, problems = withdraw_view(rd, office_root, downloads)
    mine = [x for x in offered if x["sid"] == sid]
    if not mine:
        why = next((w for x, w in kept if x["sid"] == sid), None)
        if why:
            raise StartError([f"{sid} cannot be withdrawn: {why}"])
        raise StartError([f"{sid} is not a session the office has out (one a folder records, or the in-tray's sort, "
                          "open where the office reads); office withdraw with nothing named lists the ones it can "
                          "withdraw"] + problems)
    x = mine[0]
    try:
        report = rd.unlock(x["place"], sid, surface="withdraw")
    except BaleError as exc:
        raise StartError([f"bale unlock {sid} --reason {WITHDRAW_REASON} did not close it: {exc}"])
    told = []
    try:
        reason = rd.key(report, "withdraw", "closure_reason")
        sweep = rd.key(report, "withdraw", "sweep")
        swept = bool(sweep) and rd.key(sweep, "withdraw", "sweep.status") == "committed"
        detail = rd.key(sweep, "withdraw", "sweep.detail") if sweep else "bale reported no sweep"
    except BaleError as exc:
        reason, swept, detail = "reason unread", False, f"its report could not be read ({exc})"
    told.append(f"bale closed {sid} in {x['label']} ({reason}); its sweep: {detail}")
    if not swept:
        told.append(f"bale did not commit its record of {sid}; git status in {x['repo']} shows what it left")
    root = pathlib.Path(office_root)
    alone = []
    for folder in x["folders"]:
        rel = f"{folder}/folder.md"
        try:
            _, wrote = oh.folder_event(root / rel, day, "withdrawn",
                                       f"{sid}, never worked; closed in bale by office withdraw ({reason})")
        except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
            told.append(f"{rel}: the withdrawal of {sid} could not be written there ({exc}); it is closed in bale")
            continue
        if not wrote:
            told.append(f"{rel} has no History section, so the withdrawal of {sid} is not written there")
        else:
            try:
                git(root, "add", "--", rel)
                git(root, "commit", "-q", "-m", f"office withdraw: {sid} in {pathlib.Path(folder).name}", "--", rel)
                told.append(f"{rel}: History: {day} withdrawn: {sid}")
            except LandError as exc:
                told.append(f"{rel}: History: {day} withdrawn: {sid}, written but not committed ({' '.join(exc.lines)})")
        # A merge or undo job that named the session (0.52.0): its line
        # cleared, and the job offered again.
        told += job_lines_after(root, [folder], sid, "withdrawn")
        if alone_in(root, folder, sid):
            alone.append(folder)
    where = "the office" if x["label"] == OFFICE_LABEL else x["label"]
    words = (f"Withdrawn: {sid} is closed in {where}, never worked; bale records it as {reason}."
             + ("" if x["folders"] else " No folder recorded it (the in-tray's sort)."))
    return words, told, alone


def job_lines_after(office_root, folders, sid, how):
    """office_deliver.job_session_ended for each desk folder that records a
    session which ended without landing (how: withdrawn, bailed): the lines
    to say. A step that cannot run is one line, never a refusal: the
    session is already closed in bale."""
    import office_deliver as odl
    lines = []
    for rel in folders:
        if not rel.startswith("desk/"):
            continue
        try:
            lines += odl.job_session_ended(office_root, rel, sid, how)
        except (oh.HelperError, OSError, StartError) as exc:
            why = "; ".join(exc.lines) if isinstance(exc, StartError) else str(exc)
            lines.append(f"{rel}: whether a job there names {sid} could not be read ({why}); office status says")
    return lines


def take_record_out(office_root, plan):
    """Before bale lands an office session: put the folder back as it was
    packed, so bale finds the bytes it stamped and never has to refuse
    the response as base drift. One commit, that path alone. Returns the
    line to tell the occupant, and records the commit in the plan."""
    rec = plan.get("record")
    if not rec or rec["commit"] is None:
        return None
    if not rec["restorable"]:
        return rec["why"]
    root = pathlib.Path(office_root)
    packed = git(root, "show", f"{rec['commit']}^:{rec['path']}", binary=True).stdout
    (root / rec["path"]).write_bytes(packed)
    name = pathlib.Path(rec["folder"]).name
    git(root, "add", "--", rec["path"])
    git(root, "commit", "-q", "-m", f"office land: {plan['sid']} unrecorded in {name} while it lands", "--",
        rec["path"])
    rec["unrecorded"] = git(root, "rev-parse", "HEAD").stdout.strip()
    return (f"{rec['path']}: the office's record of {plan['sid']}, written after the pack, is out while bale lands "
            "it, so bale finds the folder as it was packed; it goes back after")


def put_record_back(office_root, plan, applied, day):
    """After bale: the folder records the session again, as a new append
    when the response landed a folder.md without it, or as it was before
    land took it out when nothing landed. Returns lines to tell."""
    rec = plan.get("record")
    folders = plan.get("folders") or []
    if not plan.get("office_session") or not folders:
        return []
    root = pathlib.Path(office_root)
    folder = rec["folder"] if rec else folders[0]
    rel = f"{folder}/folder.md"
    name = pathlib.Path(folder).name
    md = root / rel
    if not md.is_file():
        return [f"{rel} is not there after the landing, so the record of {plan['sid']} was not put back"]
    if not applied and rec and rec.get("unrecorded"):
        before = git(root, "show", f"{rec['unrecorded']}^:{rel}", binary=True).stdout
        md.write_bytes(before)
        why = "it did not land"
    elif applied and plan["sid"] not in [s for s, _ in oh.folder_session_lines(md)]:
        why = "the response's folder.md did not carry it"
        merged = merge_record(root, rec, rel, md) if rec and rec.get("unrecorded") else None
        if merged is not None:
            md.write_bytes(merged)
            why += "; the lines the office wrote merged back as they were"
        else:
            oh.record_session_opening(md, plan["sid"], day)
    else:
        return []
    git(root, "add", "--", rel)
    git(root, "commit", "-q", "-m", f"office land: {plan['sid']} recorded again in {name}", "--", rel)
    return [f"{rel}: {plan['sid']} recorded again ({why})"]


def merge_record(root, rec, rel, md):
    """The landed folder.md with the office's record merged back in, the
    lines as the office wrote them (the day it opened stays the day it
    opened): a three-way merge of the folder as packed, as recorded, and
    as landed. None when the two sides touched the same lines, and the
    record goes back as a new append instead."""
    import tempfile
    import subprocess
    with tempfile.TemporaryDirectory(prefix="office-land-") as tmp:
        t = pathlib.Path(tmp)
        (t / "packed").write_bytes(git(root, "show", f"{rec['commit']}^:{rel}", binary=True).stdout)
        (t / "recorded").write_bytes(git(root, "show", f"{rec['unrecorded']}^:{rel}", binary=True).stdout)
        (t / "landed").write_bytes(md.read_bytes())
        proc = subprocess.run(["git", "merge-file", "-p", str(t / "recorded"), str(t / "packed"), str(t / "landed")],
                              capture_output=True, timeout=60)
    if proc.returncode != 0:
        debug(f"{rel}: the record did not merge cleanly onto the landed folder (git merge-file exit {proc.returncode})")
        return None
    return proc.stdout


def relay_blocks(lines, sid, spec):
    """[(addressee, lines)] for each block bale printed for a person to
    carry, markers included, in the order printed."""
    begin, end = (m.format(sid=sid) for m in spec["relay"])
    out, cur = [], None
    for line in lines:
        if cur is None and line.startswith(begin):
            cur = (line[len(begin):].removesuffix(" ===").strip(), [line])
        elif cur is not None:
            cur[1].append(line)
            if line.startswith(end):
                out.append(cur)
                cur = None
    return out


def exchange_block(lines, sid, spec):
    """The paste block bale relay printed, or None."""
    begin, end = (m.format(sid=sid) for m in spec["block"])
    try:
        a = lines.index(begin)
        b = lines.index(end, a + 1)
    except ValueError:
        return None
    return lines[a:b + 1]


# --- bale's two accepts, passed through office land (0.37.0) ------------------------------
#
# bale apply and bale retry refuse two things without a prompt: a blind
# checkpoint that changed between pack and apply, and a changes[] path whose
# base moved since the pack. Each is accepted per invocation only, by a flag
# bale deliberately gives no config key (bale help apply, bale help retry;
# PLANNER.md section 5, step 5 of the bad-oracle correction). office land
# passes either through when the occupant types it, says so before bale
# runs, and never adds one on its own; no setting turns one on. The
# admissions bale asks for itself (an out-of-forecast path, a missing
# required check) stay bale's questions on the occupant's terminal.

ACCEPT_CHECKPOINT_CHANGE = "--accept-checkpoint-change"
ACCEPT_BASE_DRIFT = "--accept-base-drift"


def accept_flags(checkpoint_change=False, base_drift=None):
    """The accepts as argv words, in bale's usage order: the switch, then
    --accept-base-drift PATH once per path, each path as typed."""
    words = [ACCEPT_CHECKPOINT_CHANGE] if checkpoint_change else []
    for path in base_drift or []:
        words += [ACCEPT_BASE_DRIFT, path]
    return words


def accept_said(plan):
    """One line per accept the landing passes to bale, for land to say
    before bale runs; none when the occupant typed none."""
    verb = plan.get("verb", "apply")
    lines = []
    if plan.get("accept_checkpoint_change"):
        lines.append(f"passing {ACCEPT_CHECKPOINT_CHANGE} to bale {verb}, as you typed it: bale runs the session's "
                     "checkpoint as it is committed now, not as it was stamped at the pack, and records that it did")
    for path in plan.get("accept_base_drift") or []:
        lines.append(f"passing {ACCEPT_BASE_DRIFT} {shell_quote(path)} to bale {verb}, as you typed it: the "
                     f"response's bytes land over {path} as it is now, superseding what changed there since the pack")
    return lines


def accepts_bale_names(lines):
    """(checkpoint change, [paths]) that bale's own re-run line names: a
    line of bale's output that runs bale apply or bale retry with either
    accept, read as a shell would read it. ((False, []) when bale printed
    none.)"""
    import shlex
    checkpoint, paths = False, []
    for line in lines:
        text = line.strip()
        if not text.startswith(("bale apply ", "bale retry ")) or "--accept-" not in text:
            continue
        try:
            words = shlex.split(text)
        except ValueError:
            debug(f"bale's line does not read as a command, so its accepts are not taken from it: {text}")
            continue
        for i, word in enumerate(words):
            if word == ACCEPT_CHECKPOINT_CHANGE:
                checkpoint = True
            elif word == ACCEPT_BASE_DRIFT and i + 1 < len(words) and words[i + 1] not in paths:
                paths.append(words[i + 1])
            elif word.startswith(ACCEPT_BASE_DRIFT + "=") and word.split("=", 1)[1] not in paths:
                paths.append(word.split("=", 1)[1])
    return checkpoint, paths


def accept_line(plan, named=(False, [])):
    """The office line that lands the session again with the accepts:
    those this landing passed (bale carries none forward from a refused
    attempt, so each is said again) and those bale's own line names."""
    checkpoint = bool(plan.get("accept_checkpoint_change")) or named[0]
    paths = list(plan.get("accept_base_drift") or [])
    paths += [p for p in named[1] if p not in paths]
    return " ".join(["office", "land", plan["sid"]] + [shell_quote(w) if not w.startswith("--") else w
                                                       for w in accept_flags(checkpoint, paths)])


def plan_repo_words(plan):
    """Where a landing's session is open, for a line the occupant reads:
    the repo, and through which host's shell for a hosted project."""
    if plan.get("place"):
        return f"{plan['place']['path']}, through {plan['place']['host']}'s shell"
    return str(plan.get("repo") or "the session's repo")


def plan_folder_key(plan):
    """How an office line names the folder that records a landing's
    session: its number on the desk, else its name; FOLDER when no folder
    on the desk records it."""
    for rel in plan.get("folders") or []:
        if rel.startswith("desk/"):
            return plan.get("folder_keys", {}).get(rel) or rel.split("/", 1)[1]
    return "FOLDER"


def relay_next_line(plan):
    """A clarification's Next line (0.44.0): office relay, which carries the
    planner's answer to bale relay where the session is open."""
    return (f"office relay {plan['sid']} ANSWER-FILE, with the planner's answer saved here as ANSWER-FILE (office "
            f"relay carries it to bale relay in {plan_repo_words(plan)})")


def handoff_line(plan):
    """A bailout's Next line (0.44.0; an office line since 0.52.0): office
    start N --handoff RESPONSE, which runs bale handoff where the session
    was (through the project's shell for a hosted one), puts the fresh
    session's request in the out tray with the office's opener, and
    records it in the folder. RESPONSE is the bailout as land had it: a
    path, or the name bale's search found."""
    tarball = str(plan.get("tarball") or "RESPONSE")
    shown = tarball if re.fullmatch(r"[A-Za-z0-9_./:@%+=,~-]+", tarball) and not tarball.startswith("~") \
        else shell_quote(tarball)
    return (f"office start {plan_folder_key(plan)} --handoff {shown} (bale handoff runs in {plan_repo_words(plan)}; "
            "it sends the fresh session the handoff asks for)")


# The bale verbs a landing's own output may name (0.44.0), in the order the
# office says them, each with the office line that does it, or None when the
# office has none (the words then say to type it in the repo).
BALE_VERBS = ("retry", "relay", "revert", "unlock", "handoff", "amend-checkpoint")
BALE_VERB_RE = oh.LazyPattern(r"\bbale (retry|relay|revert|unlock|handoff|amend-checkpoint)\b")


def office_words(printed, plan):
    """The `In office words:` list (0.44.0): for each bale verb bale's own
    lines above named, in the order first named, `bale VERB -> ` the
    office line that does it, or `no office line: type it in REPO`. []
    when bale's lines named none: nothing is printed then."""
    named = []
    for line in printed:
        for m in BALE_VERB_RE.finditer(line):
            if m.group(1) not in named:
                named.append(m.group(1))
    sid = plan["sid"]
    lines = []
    for verb in sorted(named, key=BALE_VERBS.index):
        if verb == "retry":
            office = f"office land {sid} --response FILE"
        elif verb == "relay":
            office = f"office relay {sid} FILE"
        elif verb == "unlock":
            office = f"office withdraw {sid}, for a session never worked; office land {sid}, for a sitting"
        elif verb == "handoff":
            office = handoff_line(plan)
        else:
            office = f"no office line: type it in {plan_repo_words(plan)}"
        lines.append(f"bale {verb} -> {office}")
    return lines


def outcome_words(plan, outcome, named=(False, [])):
    """(words, next line or None) for where a landing ended, in the
    office's words; bale's own lines above say the rest. named is what
    bale's own re-run line accepts (accepts_bale_names): after a refusal
    for a changed checkpoint or a moved base, the next line is the office
    line that passes the same accept (0.37.0)."""
    sid, where = plan["sid"], plan["label"]
    nothing = "nothing landed, and the session stays open"
    if outcome == "applied":
        return f"Landed: {sid} is applied in {where} (tag applied/{sid}).", None
    if outcome == "held":
        return (f"Held: bale held {sid} in {where}; {nothing}. Carry bale's blocks above, the worker's first.",
                f"office land {sid} --response FILE, with the corrected response (bale retry runs it)")
    if outcome == "base-drift-refused":
        line = accept_line(plan, named)
        if ACCEPT_BASE_DRIFT not in line:
            line = f"office land {sid} {ACCEPT_BASE_DRIFT} PATH, once for each path bale names above"
        return (f"Refused: bale refused {sid} in {where}: a file it changes moved since the pack; {nothing}. bale "
                "printed its own line that admits it above; the office line below passes the same accept to bale "
                "when you type it, and the office never runs either for you.", line)
    if outcome in ("scope-drift-refused", "required-check-refused"):
        what = {"scope-drift-refused": "it changes paths outside the session's forecast",
                "required-check-refused": "its validation leaves out a check the project requires"}[outcome]
        return (f"Refused: bale refused {sid} in {where}: {what}; {nothing}. bale printed the line that admits it "
                "above; the office never runs it for you.", None)
    if named[0] and outcome not in ("clarification", "reverted", "bailout"):
        return (f"Refused: bale refused {sid} in {where}: its checkpoint changed since the pack; {nothing}. bale "
                "printed its own line that accepts it above; the office line below passes the same accept to bale "
                "when you type it, and the office never runs either for you.", accept_line(plan, named))
    if outcome == "clarification":
        # The office's line (0.44.0), never bale's: office relay carries the
        # answer to bale relay where the session is open.
        return (f"Questions: the worker asked before building; {nothing}. The block for the planner is below.",
                relay_next_line(plan))
    if outcome == "reverted":
        return (f"Reverted: bale's walkthrough discarded {sid}'s branch in {where}; nothing landed. bale's lines "
                "above say what stays open.", None)
    if outcome == "bailout":
        # The office's line for the fresh session the handoff asks for
        # (0.44.0; built in 0.52.0): office start N --handoff runs bale
        # handoff there.
        return (f"Bailed: the worker handed {sid} off; nothing landed, and bale closed the session. The line below "
                "sends the fresh session the handoff asks for.", handoff_line(plan))
    if outcome == "refused":
        words = f"Not landed: bale refused before it recorded an attempt for {sid}; its words are above."
        if plan.get("verb") == "retry" and not plan.get("accept_checkpoint_change"):
            # bale's provenance gate refuses a changed checkpoint before
            # staging, on stderr, which a landing here does not keep, and
            # records no attempt: the office cannot tell this refusal from
            # another, so the line is offered on bale's words (0.37.0). A
            # retry is where it comes, after bale amend-checkpoint.
            return words, (accept_line(plan, (True, [])) + ", if bale's words above say the session's checkpoint "
                           "changed since the pack (after bale amend-checkpoint, say)")
        return words, None
    return f"bale recorded {outcome} for {sid} in {where}; nothing is ratified and nothing runs after it.", None


def land_outcome(rd, office_root, plan, code, capture, day):
    """What happened, from the session's dossier: the attempt this landing
    added, or, when bale exited 0 and added none, a clarification round.
    Puts the folder's record back, and gathers the blocks to carry."""
    spec = rd.consumption.surface("apply")
    where = plan_place(plan)
    relay_run = None
    if rd.hosted(where):
        # One connection: the dossier, and when bale exited 0 (the only
        # way a clarification ends) relay's block beside it.
        texts, _ = rd.prefetch(where, [("dossier", {"sid": plan["sid"]})],
                               texts=[("relay", {"sid": plan["sid"]})] if code == 0 else [])
        relay_run = texts.get("relay")
    d = rd.dossier(where, plan["sid"])
    view = session_view(rd, d) if d is not None else None
    new = response_attempts(view)[plan["attempts_before"]:] if view else []
    if new:
        outcome = new[-1]["outcome"]
    elif code == 0 and view and view["in_flight"]:
        outcome = "clarification"
    else:
        outcome = "refused"
    try:
        printed = pathlib.Path(capture).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        printed = []
    blocks = relay_blocks(printed, plan["sid"], spec)
    if outcome == "clarification":
        try:
            if relay_run is not None:
                if relay_run.returncode != 0:
                    raise BaleError("refused", f"bale relay {plan['sid']} refused in {where} (exit "
                                               f"{relay_run.returncode}): {ohost._last_words(relay_run.stderr)}")
                lines = relay_run.stdout.splitlines()
            else:
                lines = rd.lines("relay", where, sid=plan["sid"])
            block = exchange_block(lines, plan["sid"], rd.consumption.surface("relay"))
        except BaleError as exc:
            block = None
            log(f"bale relay could not re-emit the questions' block: {exc}")
        blocks = [("planner", block)] if block else []
    # The office's lines name a folder by its number (0.44.0).
    plan = dict(plan, folder_keys={f["rel"]: folder_key(f) for f in oh.read_folders(office_root)
                                   if f["problem"] is None and f["rel"] in (plan.get("folders") or [])})
    words, nxt = outcome_words(plan, outcome, accepts_bale_names(printed))
    applied = outcome == "applied"
    told = put_record_back(office_root, plan, applied, day)
    if outcome == "bailout":
        # A merge or undo job that named this session (0.52.0): bale closed
        # it, so the job's line is cleared and the bailout kept for its
        # handoff; the job is offered again.
        told = list(told or []) + job_lines_after(office_root, plan.get("folders") or [], plan["sid"], "bailed")
    return {"outcome": outcome, "applied": applied, "words": words, "next": nxt, "told": told,
            "office_words": office_words(printed, plan),
            "relays": [{"to": to, "lines": lines} for to, lines in blocks],
            "after_land": plan["after_land"] if applied else [],
            "known_outcome": outcome in spec["outcomes"] + ["clarification", "refused"]}


def land_run(rd, plan, capture):
    """bale apply or retry, through land's terminal: in the repo on this
    machine, or on a host with the response carried there first (into the
    office's one temporary directory, made in the same connection, held
    to its sha256) and the directory removed by the command that runs
    bale, whatever bale said. Returns bale's exit code, or LAND_RUN_FAILED
    when bale could not be run."""
    where = plan_place(plan)
    # bale's two accepts, only as the occupant typed them (0.37.0): the
    # surface's switches and repeated flags, placed before the tarball.
    accepts = {"accept_checkpoint_change": bool(plan.get("accept_checkpoint_change")),
               "accept_base_drift": list(plan.get("accept_base_drift") or [])}
    if not rd.hosted(where):
        try:
            return rd.interact(plan["verb"], where, capture, tarball=plan["tarball"], **accepts)
        except BaleError as exc:
            log(f"error: {exc}")
            return LAND_RUN_FAILED
    try:
        with ohost.Scratch(where) as scratch:
            remote = scratch.send(plan["tarball"])
            log(f"carried {pathlib.Path(plan['tarball']).name} to {where.host} ({remote}, checked by sha256; "
                "removed when bale is done)")
            return rd.interact(plan["verb"], where, capture, cleanup=scratch, tarball=remote, **accepts)
    except (BaleError, ohost.HostError) as exc:
        log(f"error: {exc}")
        log(f"error: nothing was applied; the response is still at {plan['tarball']}")
        return LAND_RUN_FAILED


def land_after(plan, index):
    """The project's after-land action number index (1-based), run in its
    repo on its host, its output on this terminal: attended on a terminal,
    piped with stdin closed. Returns its exit code."""
    import shlex
    command = plan["after_land"][index - 1]
    try:
        return ohost.run_streamed(plan_place(plan), f"bash -c {shlex.quote(command)}")
    except ohost.HostError as exc:
        log(f"error: {exc}")
        return LAND_RUN_FAILED


def land_after_line(plan, index):
    """The one line that reruns the after-land actions from number index
    on, typed on this machine: through the project's shell for a hosted
    one, (cd REPO && ...) otherwise."""
    rest = " && ".join(plan["after_land"][index - 1:])
    if plan.get("place"):
        return printed_line(plan_place(plan), f"cd {ohost.shell_path(plan['place']['path'])} && {rest}")
    return f"(cd {shell_quote(plan['repo'])} && {rest})"


# --- office relay: a planner's answer carried back (0.17.0) -------------------------------

def relay_answer(rd, office_root, sid, answer, cwd=None, downloads=None):
    """bale relay SID - where the session is open (a project here or on
    its host, or the office), with the planner's answer, a file on this
    machine, on its stdin. The answer is a path, or a bare name found in
    cwd and then the downloads. Returns (exit code, stdout, stderr); a
    session open nowhere the office reads is a LandError."""
    given = pathlib.Path(answer).expanduser()
    here = given if given.is_absolute() else pathlib.Path(cwd or os.getcwd()) / given
    if here.is_file():
        path = here.resolve()
    elif "/" in answer:
        raise LandError([f"no such file: {answer}"])
    else:
        path = find_in(downloads, answer, cwd or os.getcwd())
        if path is None:
            looked = ", ".join([str(cwd or os.getcwd())] + [str(d) for d in downloads or []])
            raise LandError([f"{answer} is not in {looked}; give the answer file's path"])
    lost = []
    every, problems = open_anywhere(rd, office_root, sid, lost)
    found = [x for x in every if x["sid"] == sid]
    if not found:
        lines = [f"{sid} is not open in this office or in any project it scopes, so there is no thread to answer on"]
        lines += [f"{label}'s host did not answer, so it may be open there: {line}" for label, line in lost]
        raise LandError(lines + problems)
    x = found[0]
    place = x["place"]
    argv = ["bale", *rd.consumption.argv("relay_answer", sid=sid)]
    log(f"bale relay {sid} - in {place}, with {path} on its stdin" + (f" (through {x['host']})" if x["host"] else ""))
    try:
        run = ohost.run_feeding(ohost.as_place(place), argv, str(path))
    except ohost.HostError as exc:
        raise LandError([f"{x['label']}: {exc}"])
    rd.forget(place)
    return run.returncode, run.stdout, run.stderr


# --- command line --------------------------------------------------------------------

# bale ran, but office land could not (no bale, no such directory, a host
# that stopped answering, a response that did not arrive intact).
LAND_RUN_FAILED = 125


NOT_PREPARED = 4


def project_main(a):
    """check-project and prepare-project, for office projects add: the
    place is here or on a host; a host that does not answer is the one
    reach line, and the check's refusal is the reason a wizard asks
    again. Exit 4 names the one refusal --prepare answers."""
    try:
        place = ohost.Place(a.path, a.host, a.shell, a.connect, a.name or a.path)
        if a.cmd == "clone-dirty":
            # The paths a clone's working tree changes, one per line; none
            # when it is clean. They never travel with --from.
            for line in ohost.clone_facts(a.source)["dirty"]:
                print(line)
            return 0
        if a.cmd == "clone-to":
            for line in ohost.clone_to(place, a.source, day=a.day):
                print(line)
            return 0
        if a.cmd == "git-facts":
            # What office projects asks of a clone for the audience
            # line's defaults: one tab-separated line per fact.
            facts = ohost.git_facts(place)
            for key in ("branch", "head", "name", "email", "hooks_path", "guard", "guard_audience"):
                print(f"{key}\t{facts.get(key) or ''}")
            for name, url in facts["remotes"].items():
                print(f"remote\t{name}\t{url}\t{facts['remote_heads'].get(name, '')}")
            return 0
        if a.cmd == "install-guard":
            print(ohost.install_push_guard(place, a.audience, a.url))
            return 0
        if a.cmd == "check-project":
            ok, text = ohost.check_project(place)
            if ok:
                print(text)
                return 0
            log(f"error: {text}")
            return NOT_PREPARED if "bale has not run in" in text else 1
        for line in ohost.prepare(place, day=a.day, name=a.name):
            print(line)
        return 0
    except ohost.HostError as exc:
        log(f"error: {exc}")
        return 1


def level_main(a):
    """level-plan and level-bale: what the step would do (one line,
    STATE<tab>THERE<tab>HERE<tab>HOST), and the step itself."""
    rd = Reader()
    try:
        if a.cmd == "level-plan":
            plan = level_plan(rd, a.office, a.project)
            print(f"{plan['state']}\t{plan['there'] or ''}\t{plan['here']}\t{plan['place'].host}")
            return 0
        for line in level_bale(rd, a.office, a.project):
            print(line)
        return 0
    except StartError as exc:
        for line in exc.lines:
            log(f"error: {line}")
        return 1
    except (oh.HelperError, BaleError, ohost.HostError, OSError) as exc:
        log(f"error: {exc}")
        return 1


def start_check_main(a):
    """start-check: a project on a host answers, its bale is at the floor
    and its repo is one bale runs in, before start writes anything; one
    line naming the host on stdout. A project on this machine passes."""
    rd = Reader()
    try:
        projects = {p["name"]: p for p in office_projects(a.office) or []}
        entry = projects.get(a.project)
        if entry is None or not hosted_project(entry):
            return 0
        if entry["problem"]:
            raise StartError([f"{a.project}: {entry['problem']}"])
        place = check_hosted_place(rd, entry)
        print(f"{place.host}\t{rd.installed_version(place)}")
        return 0
    except StartError as exc:
        for line in exc.lines:
            log(f"error: {line}")
        return 1
    except (oh.HelperError, BaleError, OSError) as exc:
        log(f"error: {exc}")
        return 1


# What `land` exits with (0.30.0): 0 the outcome is written to --outcome;
# 1 the record could not be taken out, and nothing ran (as land-prepare
# refused); LAND_UNREAD when bale ran and how it ended could not be read,
# LAND_UNREAD_RECORD_OUT the same with the office's record still out of its
# folder (bin/office says so, as it did when land-outcome refused).
LAND_UNREAD = 3
LAND_UNREAD_RECORD_OUT = 4


def land_whole(rd, a):
    """The landing in one process (0.30.0): what land-prepare, land-run and
    land-outcome did as three helper starts in a row, with the one line
    bin/office logged between the first two said here, in its words.

    1. Take the office's record out of an office session's folder and
       record the commit in the plan (take_record_out), and say the line
       it returns, as `[office] LINE` on stderr. A refusal here is said and
       exits 1, and nothing else runs.
    2. bale apply or retry through the terminal (land_run): stdin and
       stderr the terminal's, bale's stdout copied to ours as it comes and
       kept in --capture. Its failure is an exit code the outcome reads,
       as land-run's exit was.
    3. What happened, from bale's records (land_outcome), as one JSON line
       written to --outcome: stdout is bale's, so the answer cannot share
       it. A refusal here is said and exits LAND_UNREAD or
       LAND_UNREAD_RECORD_OUT.

    Each step reads the plan from --plan as its own process did, and the
    outcome reads with a fresh Reader and a fresh reach of a hosted place
    (office_host.forget_reach: a host that did not answer during the run is
    asked again, one that did is carried, as the reach file carried it to a
    new process), so nothing the run cached stands in for what bale
    recorded. An error a step does not expect prints its traceback, as the
    step's own interpreter did, and the landing goes on as bin/office went
    on after that step's exit 1."""
    import json
    import traceback

    def read_plan():
        return json.loads(pathlib.Path(a.plan).read_text(encoding="utf-8"))

    try:
        plan = read_plan()
        line = take_record_out(a.office, plan)
        pathlib.Path(a.plan).write_text(json.dumps(plan), encoding="utf-8")
    except StartError as exc:
        for msg in exc.lines:
            log(f"error: {msg}")
        return 1
    except (oh.HelperError, BaleError, OSError, ValueError) as exc:
        log(f"error: {exc}")
        return 1
    # As `line="$(land-prepare)"` then `[ -z "$line" ] || log "$line"` had
    # it: the line without its trailing newlines, and nothing when empty.
    said = (line or "").rstrip("\n")
    if said:
        log(said)

    # bale's accepts this landing passes, each in its own line, before bale
    # runs (0.37.0); none unless the occupant typed one.
    try:
        for msg in accept_said(read_plan()):
            log(msg)
    except (OSError, ValueError) as exc:
        log(f"error: {exc}")
    try:
        code = land_run(rd, read_plan(), a.capture)
    except StartError as exc:
        for msg in exc.lines:
            log(f"error: {msg}")
        code = 1
    except (oh.HelperError, BaleError, OSError, ValueError) as exc:
        log(f"error: {exc}")
        code = 1
    except Exception:
        traceback.print_exc()
        code = 1
    # The code as a process exit carried it (bale killed by a signal is a
    # negative wait status here, and was its low byte through the exit).
    code = (code if isinstance(code, int) else 0) & 0xFF

    unread = LAND_UNREAD_RECORD_OUT if said else LAND_UNREAD
    ohost.forget_reach()
    try:
        outcome = land_outcome(Reader(consumption=rd.consumption), a.office, read_plan(), code, a.capture, a.day)
        pathlib.Path(a.outcome).write_text(json.dumps(outcome) + "\n", encoding="utf-8")
    except StartError as exc:
        for msg in exc.lines:
            log(f"error: {msg}")
        return unread
    except (oh.HelperError, BaleError, OSError, ValueError) as exc:
        log(f"error: {exc}")
        return unread
    except Exception:
        traceback.print_exc()
        return unread
    return 0


def land_main(a):
    """The land-* subcommands and land: error lines on stderr and exit 1
    when the office cannot go on; land exits as land_whole says."""
    import json
    rd = Reader()
    if a.cmd == "land":
        return land_whole(rd, a)
    try:
        if a.cmd == "land-out":
            out, problems = sessions_out(rd, a.office)
            for line in problems:
                log(f"warning: {line}")
            for x in out:
                print(f"{x['sid']}\t{x['label']}\t{', '.join(x['folders'])}")
            return 0
        if a.cmd == "land-plan":
            downloads = None if a.no_downloads else a.downloads
            plan = land_plan(rd, a.office, a.sid, a.folder, a.response, a.cwd, downloads,
                             accept_checkpoint_change=a.accept_checkpoint_change,
                             accept_base_drift=a.accept_base_drift)
            pathlib.Path(a.plan).write_text(json.dumps(plan), encoding="utf-8")
            return 0
        if a.cmd == "start-ends":
            plan, said = ends_plan(rd, a.office, a.request, a.sid)
            for line in said:
                print(f"say\t{line}")
            if plan is not None:
                pathlib.Path(a.plan).write_text(json.dumps(plan), encoding="utf-8")
                print(f"end\t{plan['sid']}\t{plan['label']}\t{', '.join(plan['folders'])}")
            return 0
        plan = json.loads(pathlib.Path(a.plan).read_text(encoding="utf-8"))
        if a.cmd == "land-end":
            words, told = end_sitting(rd, a.office, plan, a.day, by=a.by or "office land", successor=a.successor)
            print(json.dumps({"words": words, "told": told}))
            return 0
        if a.cmd == "land-after":
            return land_after(plan, a.index)
        if a.cmd == "land-after-line":
            print(land_after_line(plan, a.index))
            return 0
        log(f"error: {a.cmd} is not one of the land subcommands (a defect in office-src)")
        return 2
    except StartError as exc:
        for line in exc.lines:
            log(f"error: {line}")
        return 1
    except (oh.HelperError, BaleError, OSError, ValueError) as exc:
        log(f"error: {exc}")
        return 1


def build_parser(only=None):
    """The command's parser; with `only`, a subcommand's name, the parser
    holds that one subcommand (office_helper.OneSubcommand, 0.28.0).
    Returns (parser, found): found is False when `only` names no
    subcommand."""
    ap = argparse.ArgumentParser(prog="office_bale.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    one = oh.OneSubcommand(sub, only) if only is not None else None
    add = one.add_parser if one else sub.add_parser
    p = add("in-flight"); p.add_argument("office")
    p.add_argument("--now", help="an ISO timestamp to measure ages from (default: now)")
    p = add("folder-sessions"); p.add_argument("office"); p.add_argument("folder_md")
    p = add("ledger"); p.add_argument("office"); p.add_argument("--project")
    p = add("landed"); p.add_argument("office"); p.add_argument("path"); p.add_argument("--project")
    p = add("versions"); p.add_argument("office"); p.add_argument("--project")
    p = add("status-lines"); p.add_argument("office")
    p = add("doctrine-lines", help="office status's doctrine line: the install's OFFICE.md by its short hash, and "
                                   "each read-only sitting out under another (0.33.0)")
    p.add_argument("office")
    p = add("provisional-lines", help="office status's structure lines: each folder still provisional though "
                                      "every session it records landed applied; nothing when none is")
    p.add_argument("office")
    # 0.41.0: what is landed and not delivered, a merge job waiting, and the
    # folders a bare probe can mean.
    p = add("waiting-lines", help="office status's lines under the folders line: each folder whose merge job "
                                  "waits, or whose merge session landed without its merge; nothing when none")
    p.add_argument("office")
    p = add("awaiting-delivery", help="bare office deliver's offer: each folder on the desk whose work landed and "
                                      "is not delivered, newest landing first, NAME<tab>WORDS")
    p.add_argument("office")
    p = add("probe-folders", help="bare office probe's folders: each folder on the desk that records a session "
                                  "open where probes run, sittings first, NAME<tab>SID<tab>WORDS")
    p.add_argument("office")
    p = add("desk"); p.add_argument("office"); p.add_argument("--today", required=True)
    p.add_argument("--since", help="the day of the previous walk-in (default: today)")
    p.add_argument("--walk-in", action="store_true", help="In flight and the first ready folders only")
    p.add_argument("--next-file", help="write the walk-in's Next line to this file")
    p.add_argument("--skew", choices=("current", "behind", "ahead", "unreadable"), default="current",
                   help="the office's version state, for the Next line")
    p.add_argument("--founded", choices=("yes", "no"), default="yes", help="whether the profile is complete")
    p.add_argument("--blueprint", help="only this blueprint's member folders, in the desk's order")
    p.add_argument("--machine-file", help="machine.toml, whose out_tray holds the asks out the Next line may name "
                                          "(0.54.0) and office desk lists (0.55.0)")
    p = add("writers"); p.add_argument("office"); p.add_argument("paths", nargs="+")
    p = add("sort-out", help="the standalone sorts open in the office's registry, one id per line")
    p.add_argument("office")
    p = add("start", help="pack a session for a folder and fill its out tray; one JSON line on stdout")
    p.add_argument("office"); p.add_argument("folder", help="desk/NAME, or - for the standalone sort (no folder)")
    p.add_argument("--where", choices=("office", "project"), required=True)
    p.add_argument("--project", default=None, help="the project it is on, or the one an office session is about")
    p.add_argument("--goal", required=True); p.add_argument("--slug", required=True)
    p.add_argument("--include", action="append", default=[]); p.add_argument("--write", action="append", default=[])
    p.add_argument("--read-only", action="store_true"); p.add_argument("--brief")
    p.add_argument("--work-class"); p.add_argument("--tray-root", required=True)
    p.add_argument("--bundle", help="a planner bundle: bale open replays its pack line in place of a pack")
    p.add_argument("--leave-out", action="append", default=[],
                   help="a declared ride-along that stays home for this session (repeatable)")
    p.add_argument("--install-file", action="append", default=[],
                   help="an install-relative file that rides beside the request (repeatable)")
    p.add_argument("--checked", action="store_true",
                   help="bin/office has checked the project's host this start (start-check)")
    p.add_argument("--bale-rehearsed", action="store_true",
                   help="bale open --check --json passed this bundle this start, over the office's own overlap "
                        "check (bundle-check printed `over` lines): bale's to judge, as a second desk")
    p.add_argument("--handoff", default=None,
                   help="office start N --handoff (0.52.0): the bailout response bale handoff takes, as handoff-check "
                        "resolved it (a path, or a bare name for bale's own search)")
    p.add_argument("--handoff-sid", default=None, help="the session the bailout answers, from handoff-check")
    p.add_argument("--handoff-key", default=None, help="how a line names the folder, from handoff-check")
    p = add("handoff-check", help="office start N --handoff's reads before anything runs (0.52.0): tarball<tab>T, "
                                  "bailout<tab>SID, where<tab>office|project, project<tab>NAME, key<tab>N and "
                                  "say<tab>LINE; a refusal on stderr, exit 1")
    p.add_argument("office"); p.add_argument("folder", help="desk/NAME")
    p.add_argument("--response", help="the bailout as given: a path, or a name looked for here and in the downloads")
    p.add_argument("--cwd", help="where a relative response is read from (default: here)")
    p.add_argument("--downloads", action="append", default=[],
                   help="a directory machine.toml's downloads lists (repeatable)")
    p = add("start-check", help="a project on a host answers, its bale is at the floor and its repo is "
                                           "bale's, before start writes anything: HOST<tab>VERSION, or nothing for a "
                                           "project on this machine")
    p.add_argument("office"); p.add_argument("--project", required=True)
    for name, text in (("level-plan", "what office projects level-bale would do: STATE<tab>THERE<tab>HERE<tab>HOST, "
                                      "STATE one of level, behind, ahead, absent"),
                       ("level-bale", "install on the project's host the bale this machine runs, keeping its user/")):
        p = add(name, help=text)
        p.add_argument("office"); p.add_argument("--project", required=True)
    p = add("bundle-check", help="bale open --check where the bundle would open; the path bale found")
    p.add_argument("office"); p.add_argument("--where", choices=("office", "project"), required=True)
    p.add_argument("--project"); p.add_argument("--bundle", required=True)
    p.add_argument("--checked", action="store_true",
                   help="bin/office has checked the project's host this start (start-check)")
    p = add("start-riders", help="the riders a start's pack carries: N<tab>TITLE<tab>RIDES<tab>TOUCHED")
    p.add_argument("office"); p.add_argument("folder", help="desk/NAME")
    p.add_argument("--where", choices=("office", "project"), required=True); p.add_argument("--project")
    p.add_argument("--include", action="append", default=[]); p.add_argument("--write", action="append", default=[])
    p.add_argument("--read-only", action="store_true"); p.add_argument("--bundle")
    p.add_argument("--rides", action="append", default=[],
                   help="a RIDES path from the bundle's brief (0.44.0): the riders it names, not the forecast's")
    p = add("install-lines", help="the walk-in's lines about the install: Install: BEHIND ... when this office "
                                             "scopes its source and the source moved past the install, Bytecode: ... "
                                             "when the install's bytecode cache is not level for this python3, "
                                             "Suite: ... when the office scopes the source and the latest detached "
                                             "run's verdict is not OK; nothing otherwise")
    p.add_argument("office")
    p = add("bundle-where", help="where a bundle opens by default: DEFAULT<tab>WHY, or nothing")
    p.add_argument("office"); p.add_argument("--bundle", required=True); p.add_argument("--lane")
    for name, text in (("git-facts", "a clone's branch, identity, remotes and push guard, here or through a "
                                     "host's shell: one tab-separated line per fact"),
                       ("install-guard", "write the push guard into a clone's .git/hooks/pre-push: --audience "
                                         "REMOTE --url URL"),
                       ("check-project", "is the path the top of a git repo bale runs in, here or through a "
                                         "host's shell; what was found on stdout, else the reason on stderr "
                                         "(exit 4: a repo bale has not run in, which --prepare sets up)"),
                       ("prepare-project", "prepare a clone for bale without a trace in git, here or through "
                                           "a host's shell: the exclude lines and an empty bale.toml"),
                       ("clone-dirty", "the paths the working tree of the clone --from names changes, one per line"),
                       ("clone-to", "put a clone of --from at --path on the host, every branch and tag, then "
                                    "prepare it; the clone here is not changed")):
        p = add(name, help=text)
        p.add_argument("--path", required=True); p.add_argument("--host"); p.add_argument("--shell")
        p.add_argument("--connect"); p.add_argument("--name")
        # The office's date, for the sandbox setting prepare may write (0.39.0).
        p.add_argument("--day")
        if name.startswith("clone-"):
            p.add_argument("--from", dest="source", required=True)
        if name == "install-guard":
            p.add_argument("--audience", required=True); p.add_argument("--url", default="")
    p = add("land-out", help="the sessions out: sid, where, folders; one per line")
    p.add_argument("office")
    p = add("land-plan", help="the one session to land and how, as JSON into --plan")
    p.add_argument("office"); p.add_argument("--sid"); p.add_argument("--folder"); p.add_argument("--response")
    p.add_argument("--cwd", help="where a relative response path is read from (default: here)")
    p.add_argument("--plan", required=True)
    p.add_argument("--downloads", action="append", default=[],
                   help="a directory machine.toml's downloads lists (repeatable)")
    p.add_argument("--no-downloads", action="store_true", help="machine.toml sets no downloads")
    p.add_argument("--accept-checkpoint-change", action="store_true",
                   help="pass bale's --accept-checkpoint-change to the apply or retry (0.37.0; as typed on office land)")
    p.add_argument("--accept-base-drift", action="append", default=[], metavar="PATH",
                   help="pass bale's --accept-base-drift PATH to the apply or retry (repeatable; as typed)")
    p = add("start-ends", help="the sitting a request's brief succeeds (its ENDS line, 0.43.0): say LINE, and "
                               "end SID LABEL FOLDERS with its plan for land-end into --plan")
    p.add_argument("office"); p.add_argument("--request", required=True); p.add_argument("--sid", required=True)
    p.add_argument("--plan", required=True)
    p = add("land-end", help="end a read-only sitting: bale unlock, then the folder's History; one JSON line")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--day", required=True)
    p.add_argument("--by", help="the verb that ends it, for its History line (default office land; 0.43.0)")
    p.add_argument("--successor", help="the session sent in its place, for its History line (0.43.0)")
    p = add("land", help="the landing (0.30.0, once land-prepare, land-run and land-outcome): the office's "
                         "record out of an office session's folder, said; bale apply or retry, the terminal's; "
                         "what happened, from bale's records, one JSON line into --outcome; exit 0, 1 when "
                         "nothing ran, 3 or 4 (the record still out) when how it ended could not be read")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--capture", required=True)
    p.add_argument("--day", required=True); p.add_argument("--outcome", required=True)
    for name, text in (("land-after", "a hosted project's after-land action N, run on its host; exits with its code"),
                       ("land-after-line", "the line that reruns the after-land actions from N on")):
        p = add(name, help=text)
        p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--index", type=int, required=True)
    p = add("find-download", help="a file by name in the downloads, the newest of its browser copies: "
                                             "its path, and on stderr which was taken")
    p.add_argument("--name", required=True); p.add_argument("--dir", action="append", default=[])
    p = add("relay", help="bale relay SID - where the session is open, the planner's answer on its stdin")
    p.add_argument("office"); p.add_argument("--sid", required=True); p.add_argument("--answer", required=True)
    p.add_argument("--cwd"); p.add_argument("--downloads", action="append", default=[])
    p = add("bundle-lands", help="where a bundle's brief says it lands (its LANDS line): place<tab>office "
                                            "or place<tab>project<tab>NAME, folder<tab>NAME or folder<tab>new, "
                                            "words<tab>LINE, branch<tab>NAME (its BRANCH line, 0.34.0), say<tab>WHY, "
                                            "or absent")
    p.add_argument("office"); p.add_argument("--bundle", required=True)
    p.add_argument("--machine-file", help="machine.toml: a LANDS project this office does not scope is looked for "
                                          "in the other offices it lists (0.44.0): elsewhere<tab>ROOT<tab>NAME, or "
                                          "nowhere<tab>PROJECT")
    p = add("bundle-branch", help="check out the branch a bundle's brief names (its BRANCH line) in the project's "
                                             "clone, here or through its shell, before bale opens the bundle; the "
                                             "lines to say on stdout, a refusal on stderr with nothing changed")
    p.add_argument("office"); p.add_argument("--where", choices=("office", "project"), required=True)
    p.add_argument("--project"); p.add_argument("--branch", required=True)
    p.add_argument("--checked", action="store_true",
                   help="bin/office has checked the project's host this start (start-check)")
    p.add_argument("--from-flag", action="store_true",
                   help="the branch is office start's --branch NAME (0.50.0), not a bundle's BRANCH line: said so")
    p = add("bundle-sitting", help="whether a bundle's pack line sends out a sitting: yes, no or unknown")
    p.add_argument("--bundle", required=True)
    p = add("withdraw-list", help="the sessions out that can be withdrawn: SID<tab>LABEL<tab>FOLDERS<tab>"
                                             "CREATED; those that cannot: kept<tab>SID<tab>WHY")
    p.add_argument("office"); p.add_argument("--dir", action="append", default=[])
    p.add_argument("--no-downloads", action="store_true", help="machine.toml sets no downloads")
    p = add("withdraw", help="close a session that was never worked (bale unlock --reason abandoned), "
                                        "then its folders' History; one JSON line")
    p.add_argument("office"); p.add_argument("--sid", required=True); p.add_argument("--day", required=True)
    p.add_argument("--dir", action="append", default=[])
    p.add_argument("--no-downloads", action="store_true", help="machine.toml sets no downloads")
    if one:
        sub.metavar = one.metavar()
    return ap, (one.found if one else True)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    ap, found = build_parser(oh.subcommand_named(argv))
    if not found:
        ap, _ = build_parser()
    a = ap.parse_args(argv)
    if a.cmd == "bundle-lands":
        got = bundle_lands(a.office, a.bundle, a.machine_file)
        if got["absent"]:
            print("absent")
            return 0
        if got["place"] == "office":
            print("place\toffice")
        elif got["place"] == "project":
            print(f"place\tproject\t{got['project']}")
        if got["folder"]:
            print(f"folder\t{got['folder']}")
        if got["words"]:
            print(f"words\t{got['words']}")
        if got["branch"]:
            print(f"branch\t{got['branch']}")
        if got["rides"] == []:
            print("rides-none")
        for path in got["rides"] or []:
            print(f"rides\t{path}")
        for root, name in got.get("elsewhere") or []:
            print(f"elsewhere\t{root}\t{name}\t{got['lands_on']}")
        if got.get("nowhere"):
            print(f"nowhere\t{got['lands_on']}")
        for line in got["said"]:
            print(f"say\t{line}")
        return 0
    if a.cmd == "bundle-branch":
        try:
            for line in checkout_branch(Reader(), a.office, a.where, a.project, a.branch, a.checked,
                                        source="flag" if a.from_flag else "bundle"):
                print(line)
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        except (oh.HelperError, BaleError, ohost.HostError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        return 0
    if a.cmd == "bundle-sitting":
        ro = bundle_read_only(a.bundle)
        print("unknown" if ro is None else ("yes" if ro else "no"))
        return 0
    if a.cmd in ("withdraw-list", "withdraw"):
        import json
        downloads = None if a.no_downloads else a.dir
        rd = Reader()
        try:
            if a.cmd == "withdraw-list":
                offered, kept, problems = withdraw_view(rd, a.office, downloads)
                for line in problems:
                    log(f"warning: {line}")
                for x in offered:
                    print(f"{x['sid']}\t{x['label']}\t{', '.join(x['folders'])}\t{x['created']}")
                for x, why in kept:
                    print(f"kept\t{x['sid']}\t{why}")
                return 0
            words, told, alone = withdraw(rd, a.office, a.sid, a.day, downloads)
            print(json.dumps({"words": words, "told": told, "alone": alone}))
            return 0
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        except (oh.HelperError, BaleError, ohost.HostError, OSError) as exc:
            log(f"error: {exc}")
            return 1
    if a.cmd == "land" or a.cmd.startswith("land-") or a.cmd == "start-ends":
        return land_main(a)
    if a.cmd == "relay":
        try:
            rc, out, err = relay_answer(Reader(), a.office, a.sid, a.answer, a.cwd, a.downloads or None)
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        except (oh.HelperError, BaleError, ohost.HostError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        sys.stderr.write(err)
        sys.stdout.write(out)
        if rc != 0:
            log(f"error: bale relay {a.sid} refused (exit {rc}); its words are above, and nothing was recorded")
            return 1
        return 0
    if a.cmd == "find-download":
        try:
            path, note = newest_copy(browser_copies(a.dir, a.name), a.name, StartError)
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        if path is None:
            log(f"error: no {a.name} in the downloads ({', '.join(a.dir) or 'none listed'})")
            return 1
        if note:
            log(note)
            other = differing_bundle_copies(path, browser_copies(a.dir, a.name))
            if other:
                log(f"not every copy is the same bundle: {', '.join(other)} {'carries' if len(other) == 1 else 'carry'} "
                    "another brief than the one taken; office start --bundle PATH takes one by its path")
        print(path)
        return 0
    if a.cmd in ("check-project", "prepare-project", "clone-dirty", "clone-to", "git-facts", "install-guard"):
        return project_main(a)
    if a.cmd in ("level-plan", "level-bale"):
        return level_main(a)
    if a.cmd == "start-check":
        return start_check_main(a)
    if a.cmd == "bundle-check":
        try:
            checked = check_bundle_report(Reader(), a.office, a.where, a.project, a.bundle, a.checked)
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        except (oh.HelperError, BaleError, ohost.HostError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        # The first line is the path bale found; then, when bale's
        # rehearsal passed a bundle the office's overlap check caught (a
        # second desk, 0.18.0), one `over` line per line of the office's
        # words and one `bale` line per line bale said about the desk.
        print(checked["found"] or "")
        for line in checked["over"]:
            print(f"over\t{line}")
        for line in checked["bale"]:
            print(f"bale\t{line}")
        return 0
    if a.cmd == "start-riders" and a.rides:
        # The brief's RIDES lines (0.44.0) name the riders; the forecast
        # does not choose them.
        import office_drafting as od
        try:
            riders = od.riders_for_rides(a.office, a.rides, a.project if a.where == "project" else None)
        except (oh.HelperError, OSError, ValueError) as exc:
            log(f"warning: the riders the brief's RIDES lines name could not be read ({exc}); none is carried")
            return 0
        for r in riders:
            print(f"{r['number']}\t{r['title']}\t{r['rides']}\t{', '.join(r['touched'])}")
        return 0
    if a.cmd == "start-riders":
        try:
            forecast, riders = start_riders(a.office, a.folder, a.where, a.project, a.write, a.include,
                                            a.read_only, a.bundle)
        except (oh.HelperError, OSError, ValueError) as exc:
            log(f"warning: the riders this pack carries could not be read ({exc}); none is offered")
            return 0
        if forecast is None:
            import office_drafting as od
            say = log if (pathlib.Path(a.office) / od.SPACE / "riders.md").is_file() else debug
            say("the office cannot read this bundle's forecast, so it offers no riders for it")
        for r in riders:
            print(f"{r['number']}\t{r['title']}\t{r['rides']}\t{', '.join(r['touched'])}")
        return 0
    if a.cmd in ("waiting-lines", "awaiting-delivery"):
        # git alone, no bale: no Reader is made (0.41.0).
        try:
            if a.cmd == "waiting-lines":
                lines = waiting_lines(a.office)
            else:
                undelivered, _, unread = waiting_on_delivery(a.office)
                for line in unread:
                    debug(line)
                lines = [f"{u['folder']['name']}\t{oh.cite(u['folder'])}, {folder_title(u['folder'])} "
                         f"({u['project']}): {u['sid']} landed {u['day']}" for u in undelivered]
        except (oh.HelperError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        for line in lines:
            print(line)
        return 0
    if a.cmd == "provisional-lines":
        # git alone, no bale: no Reader is made.
        try:
            lines, _ = provisional_landed(a.office)
        except (oh.HelperError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        for line in lines:
            print(line)
        return 0
    if a.cmd == "install-lines":
        # Each line is read on its own, so one that cannot be read never
        # hides the other; the source is looked up once for both.
        try:
            source = install_source(a.office)
        except (OSError, oh.HelperError) as exc:
            debug(f"the install's source could not be read: {exc}")
            source = None
        try:
            behind = install_behind(a.office, source=source)
        except (OSError, oh.HelperError) as exc:
            debug(f"the install could not be compared with its source: {exc}")
            behind = None
        if behind:
            print(f"Install: {behind['words']}")
        # The install's bytecode cache, not level for this python3 (0.31.0):
        # in office status's words, in any office this install runs.
        try:
            cache = bytecode_behind()
        except (OSError, oh.HelperError) as exc:
            debug(f"the install's bytecode cache could not be checked: {exc}")
            cache = None
        if cache:
            print(f"Bytecode: {cache['words']}")
        try:
            verdict = suite_verdict(a.office, source=source)
        except (OSError, oh.HelperError) as exc:
            verdict = f"the latest detached run's verdict could not be read: {exc}"
        if verdict:
            print(f"Suite: {verdict}")
        return 0
    if a.cmd == "bundle-where":
        try:
            found = bundle_where(a.office, a.bundle, a.lane or None)
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        except (oh.HelperError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        if found is not None:
            print(f"{found[0]}\t{found[1]}")
        return 0
    if a.cmd == "handoff-check":
        try:
            got = handoff_check(Reader(), a.office, a.folder, a.response, a.cwd, a.downloads)
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        except (oh.HelperError, BaleError, ohost.HostError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        for key in ("tarball", "bailout", "where", "project", "key"):
            if got[key] is not None:
                print(f"{key}\t{got[key]}")
        for line in got["said"]:
            print(f"say\t{line}")
        return 0
    if a.cmd == "start":
        import json
        handoff = None
        if a.handoff:
            if not a.handoff_sid:
                log("error: --handoff needs --handoff-sid (a defect in office-src: bin/office passes both)")
                return 2
            handoff = {"tarball": a.handoff, "bailout": a.handoff_sid, "key": a.handoff_key}
        try:
            result = start(Reader(), a.office, None if a.folder == "-" else a.folder, a.where, a.project, a.goal,
                           a.slug, a.include,
                           a.write, a.read_only, a.brief, a.work_class, a.tray_root, a.bundle, a.leave_out,
                           a.install_file, a.checked, a.bale_rehearsed, handoff)
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        except (oh.HelperError, BaleError, ohost.HostError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        print(json.dumps(result))
        return 0
    try:
        rd = Reader()
        if a.cmd == "probe-folders":
            # Each row's label names the folder's project (0.49.0), as
            # every list of folders offered by key does.
            names = oh.office_project_names(a.office)
            by_name = {f["name"]: f for f in oh.read_folders(a.office) if f["space"] == "desk"}
            for name, sid, words in probe_folders(rd, a.office):
                label = oh.folder_label(by_name[name], names) if name in by_name else f"desk/{name}"
                print(f"{name}\t{sid}\t{words}\t{label}")
            return 0
        if a.cmd == "sort-out":
            # The standalone sorts open in this office: one id per line.
            for sid in sorts_out(rd, a.office):
                print(sid)
            return 0
        if a.cmd == "writers":
            # The one-writer rule: exit 3 and one line per session whose
            # forecast holds a path, 0 when none does or there is no
            # registry, 1 when the registry cannot be read.
            held = writers_holding(rd, a.office, a.paths)
            for sid, target, forecast in held:
                print(f"{sid} holds {target} (its forecast: {', '.join(forecast)})")
            return 3 if held else 0
        if a.cmd == "desk":
            for day in (a.today, a.since):
                if day is not None:
                    dt.date.fromisoformat(day)
            groups = {}
            lines, bad = render_desk(rd, a.office, a.today, a.since, a.walk_in, groups_out=groups,
                                     blueprint=a.blueprint, machine_file=None if a.walk_in else a.machine_file)
            if a.next_file:
                # The asks out (0.54.0), for the Next line's ask row.
                if a.machine_file:
                    groups["asks"] = asks_waiting(a.office, a.machine_file)
                # Never fails the walk-in: a Next line that cannot be
                # worked out says so, and why is a debug line away.
                try:
                    line = next_line(rd, a.office, a.skew, a.founded == "yes", groups)
                except (BaleError, oh.HelperError, OSError) as exc:
                    debug(f"the Next line could not be worked out: {exc}")
                    line = "Next: office desk  (the next move could not be worked out; OFFICE_DEBUG=1 office says why)"
                pathlib.Path(a.next_file).write_text(line + "\n", encoding="utf-8")
        elif a.cmd == "in-flight":
            now = parse_stamp(a.now) if a.now else None
            lines, bad = render_in_flight(rd, a.office, now)
        elif a.cmd == "folder-sessions":
            lines, bad = render_folder_sessions(rd, a.office, a.folder_md)
        elif a.cmd == "ledger":
            lines, bad = render_ledger(rd, a.office, a.project)
        elif a.cmd == "landed":
            lines, bad = render_landed(rd, a.office, a.path, a.project)
        elif a.cmd == "versions":
            lines, bad = render_versions(rd, a.office, a.project)
        elif a.cmd == "doctrine-lines":
            lines, bad = doctrine_lines(rd, a.office)
        else:
            lines, bad = status_lines(rd, a.office)
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except BaleError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, ValueError) as exc:
        log(f"error: {exc}")
        return 2
    # Every line reaches a screen with his words as he wrote them (0.49.0):
    # the desk, the walk-in, status, sessions; the pages keep their ASCII.
    for line in lines:
        print(oh.shown(line))
    # The lines already say which project could not be read and why;
    # the exit code tells the caller, which decides how loud to be.
    return 3 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
