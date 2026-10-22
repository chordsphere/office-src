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
import json
import os
import pathlib
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_drafting as od  # noqa: E402
import office_door as odoor  # noqa: E402
import office_host as ohost  # noqa: E402
import office_drop as odrop  # noqa: E402
import office_sort as osort  # noqa: E402
import office_meeting as om  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
CONSUMPTION = INSTALL / "share" / "bale-consumption.toml"
BALE_TIMEOUT = 60
# A pack copies a tree and runs bale's own checks; give it longer.
PACK_TIMEOUT = 600
# Attempts that carry a response tarball: the ones a trust ledger counts.
RESPONSE_COMMANDS = ("apply", "retry")
OUTBOX_RE = re.compile(r"^request-(.+)\.tar\.gz$")
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
        value was given, in the declared order."""
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
        for flag, word in s.get("optional", []):
            key = word.strip("{}")
            if values.get(key) is not None:
                out += [flag, str(values[key])]
        # A list value: the flag once per element, in order.
        for flag, word in s.get("repeated", []):
            for v in values.get(word.strip("{}")) or []:
                out += [flag, str(v)]
        # A true value: the bare flag.
        for flag, word in s.get("switches", []):
            if values.get(word.strip("{}")):
                out.append(flag)
        return out

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


# --- the reader ------------------------------------------------------------------

class Reader:
    """Runs bale's JSON surfaces and hands back plain data.

    Calls are cached per (directory, argv) for the life of the reader, so
    one rendering asks bale each question once. `touched` collects every
    (surface, key) read, which the suite compares with the manifest."""

    def __init__(self, consumption=None, runner=subprocess.run):
        self.consumption = consumption or Consumption()
        self.runner = runner
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
    out = []
    for a in rd.key(d, "dossier", "attempts") or []:
        blk = rd.key(a, "dossier", "attempts[].bundle")
        if blk:
            stem = rd.key(blk, "dossier", "attempts[].bundle.stem")
            if stem:
                out.append(str(stem))
    return out


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


def in_flight(rd, office_root, now=None):
    """(lines, unreadable, flying): one line per open session in the
    projects the office scopes and in the office's own repo, each mapped
    to the folder that names its sid; flying is the set of folders
    (space/name) some open session is mapped to."""
    now = now or dt.datetime.now(dt.timezone.utc)
    projects = office_projects(office_root)
    naming = folders_naming(office_root)
    sources = [(p["name"], p) for p in projects or []]
    own = office_registry(office_root)
    if own is not None:
        sources.insert(0, (OFFICE_LABEL, {"problem": None, "resolved": own}))
    lines, bad, open_count, flying = [], 0, 0, set()
    if not projects:
        lines.append(no_projects_line(projects))
    for label, p in sources:
        try:
            cwd = readable(p)
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
                # The standalone sort belongs to no folder: it is the
                # in-tray's session (0.20.0); a meeting's prep is the
                # calendar's (0.26.0).
                target = ", ".join(folders) or ("the in-tray (the standalone sort)"
                                                if label == OFFICE_LABEL and osort.is_sort_sid(sid) else
                                                f"the meeting {prep['title']} ({prep['date']} {prep['time']}), its prep"
                                                if prep else "no folder")
                if d is None:
                    lines.append(f"{label}: {sid} open, with no record in bale's telemetry yet -> {target}{ends}")
                    continue
                v = session_view(rd, d)
                state = "read-only" if read_only else outcome_word(v)
                age = describe_age(parse_stamp(v["created"]), now)
                lines.append(f"{label}: {sid} {state}, opened {age} ago -> {target}{ends}")
        except BaleError as exc:
            bad += 1
            lines.append(f"{label}: cannot read: {exc}")
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
SUCCESSOR_RE = re.compile(r"folders?\s+([\d,\s]+)")


def folder_line(f):
    """`folder N  NAME  next: ...  (sessions: N)`, the name alone for a
    folder with no number, and its size when it has one."""
    try:
        nxt, count = oh.folder_summary(f["path"], FOLDER_TEMPLATE)
    except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
        return f"{f['name']}  (folder.md could not be read: {exc})"
    head = f"folder {f['number']}  {f['name']}" if f.get("number") else f["name"]
    size = (f["fields"].get("size") or [None])[0]
    return f"{head}  next: {nxt}  (sessions: {count})" + (f"  {size}" if size else "")


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


def desk_lines(groups, flight_lines, walk_in=False, ready_limit=3):
    """The groups as the screen shows them. Full, for office desk; for
    the walk-in, In flight and the first ready folders."""
    lines = ["In flight:"]
    lines += [f"  {l}" for l in flight_lines]
    lines += [f"  {folder_line(f)}  [open, no session in flight]" for f in groups["open"]]
    parked = sum(len(v) for v in groups["parked"].values())
    errors = sum(1 for h in groups["parked"] if h.startswith("ERROR")) + len(groups["ready_errors"])
    on_desk = (len(groups["flying"]) + len(groups["open"]) + len(groups["ready"]) + parked + len(groups["candidates"])
               + len(groups["no_status"]) + len(groups["misplaced"]) + len(groups["unreadable"]))

    def ready_block(items):
        out = []
        for f in items:
            out.append(f"  {folder_line(f)}")
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
                lines += [f"      and {a}" for a in also]
    if groups["candidates"]:
        lines += ["", "Candidates:"] + [f"  {folder_line(f)}" for f in groups["candidates"]]
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


def render_desk(rd, office_root, today, since=None, walk_in=False, now=None, groups_out=None, blueprint=None):
    """(lines, unreadable projects): office desk, or the walk-in's two
    sections. since is the day of the previous walk-in (default today):
    a ready folder whose gate cleared on or after it says so. groups_out,
    a dict when given, receives the desk's groups (the Next line reads
    them, so the walk-in classifies the desk once)."""
    flight, bad, flying = in_flight(rd, office_root, now)
    table = od.Table(office_root)
    folders = oh.read_folders(office_root)
    if blueprint is not None:
        return blueprint_desk(table, folders, flying, since or today, blueprint, flight), bad
    groups = classify_desk(folders, flying, since or today, table)
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
    return lines, bad


def blueprint_desk(table, folders, flying, since, bid, flight):
    """office desk --blueprint ID: the arc's member folders in the desk's
    own order, computed from their gates, then the members already filed.
    The blueprint states no order; this is the only place it is shown."""
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


def sessions_to_land(rd, office_root):
    """(sessions, problems): the open sessions office land can bring back,
    held ones first, then oldest first. A session counts when a folder
    records it, or when it is open in the office's own registry (a
    founding or a renovation packed by hand before 0.12.0, which no
    folder records); a read-only sitting lands nothing and never counts.
    Each is open_anywhere's dict plus held, created and door (founding or
    renovation when a door's folder records it, else None)."""
    every, problems = open_anywhere(rd, office_root)
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


def sort_move(drops, groups, projects):
    """(command, why) for office start --sort, or None (the rule 3c
    above): an unsorted drop with no project, or one that does not
    resolve, that has waited through one session; or an in-tray of
    SORT_PILE or more unsorted drops with nothing ready on the desk."""
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


def next_move(skew, founded, out, groups, projects, slips, behind=None):
    """(command, why) for the walk-in's Next line, from the office's state:
    skew (current, behind, ahead or unreadable), founded (bool), out
    (sessions_to_land's list), groups (classify_desk's, with the
    in-tray's unsorted drops under "drops" as render_desk adds them),
    projects (the [projects] entries, or None for no table), slips (a
    count) and behind (install_behind's dict when the install is behind a
    source this office scopes, else None). A pure function, so every
    state is testable without an office.

    The order (doctrine section 7, the walk-in): the office out of step with the
    install, then the install behind its source, then a session out,
    the moves, an unsorted drop, the founding, the desk. The install comes before a
    session out because office start and office land run the install:
    behind its source, they would run the old office."""
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
    if groups.get("open"):
        f = groups["open"][0]
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
    command, why = next_move(skew, founded, out, groups, office_projects(office_root),
                             count_slips(office_root), behind)
    return f"Next: {command}  ({why})"


def locate(rd, projects, sid, statuses):
    """(project, dossier) for a sid: first the projects whose outbox or
    open list names it, then every readable project. (None, None) when
    no project's records hold it."""
    readable_projects = []
    for p in projects:
        try:
            cwd = readable(p)
        except BaleError:
            continue
        if p["name"] not in statuses:
            statuses[p["name"]] = rd.known_sids(cwd)
        readable_projects.append((p, cwd))
    ordered = ([pc for pc in readable_projects if sid in statuses[pc[0]["name"]]]
               + [pc for pc in readable_projects if sid not in statuses[pc[0]["name"]]])
    for p, cwd in ordered:
        d = rd.dossier(cwd, sid)
        if d is not None:
            return p, d
    return None, None


def render_folder_sessions(rd, office_root, folder_md):
    """(lines, unreadable): the folder's own Sessions lines, each followed
    by what bale's records say about the session. Nothing rendered here
    is written into the folder."""
    recorded = oh.folder_session_lines(folder_md)
    lines = [f"- {sid}" + (f": {words}" if words else "") for sid, words in recorded]
    if not recorded:
        return ["no session ids are recorded in this folder"], 0
    projects = office_projects(office_root)
    if not projects:
        return lines + [f"{no_projects_line(projects)}; no outcomes are rendered"], 0
    out, bad, found, missing = [], 0, 0, []
    statuses = {}
    try:
        rd.bale()
    except BaleError as exc:
        return lines + [f"  cannot read bale's records: {exc}"], 1
    for p in projects:
        try:
            cwd = readable(p)
            if rd.hosted(cwd):
                # One batch per host: the dossiers of the recorded sessions
                # its records name, so locate below asks nothing more.
                statuses[p["name"]] = rd.known_sids(cwd)
                rd.prefetch(cwd, [("dossier", {"sid": sid}) for sid, _ in recorded if sid in statuses[p["name"]]])
        except BaleError as exc:
            bad += 1
            out.append(f"  {p['name']}: cannot read: {exc}")
    for (sid, words), line in zip(recorded, lines):
        out.append(line)
        try:
            p, d = locate(rd, projects, sid, statuses)
        except BaleError as exc:
            bad += 1
            out.append(f"    cannot read: {exc}")
            continue
        if d is None:
            missing.append(sid)
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
    out.append(f"recorded in this folder: {len(recorded)} session id(s); found in bale's records: {found}"
               + (f"; not found: {', '.join(missing)}" if missing else ""))
    out.append("bale version per session: not on bale's dossier (a slip for bale-src)")
    return out, bad


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
            cwd = readable(p)
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
            bad += 1
            lines.append(f"{p['name']}: cannot read: {exc}")
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
            cwd = readable(p)
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
            bad += 1
            lines.append(f"{p['name']}: cannot read: {exc}")
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
            cwd = readable(p)
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
            bad += 1
            lines.append(f"{p['name']}: cannot read: {exc}")
    return lines, bad


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
    problems, hosted = [], []
    for p in projects:
        if p["problem"]:
            ok, text = False, p["problem"]
        elif hosted_project(p):
            ok, text = True, ""
            hosted.append(p)
        else:
            ok, text = oh.check_project_dir(p["resolved"])
        if not ok:
            problems.append(f"  {p['name']}: {text}")
    lines.append(f"projects:   {len(projects)} in scope"
                 + (f"; {len(problems)} cannot be read" if problems else "; each is a repo bale runs in"
                    + (f", {len(hosted)} through a host's shell" if hosted else "")))
    lines += problems
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
            v = rd.installed_version(place)
            if oh.compare_versions(v, cons.floor) >= 0:
                lines.append(f"  {p['name']}: {p['host']} answers; bale {v} there, within the read side's "
                             f"range (bale {cons.floor} or later)"
                             + (f"; this machine runs {here}, and {level_step(p['name'])} brings it level"
                                if here and oh.compare_versions(v, here) < 0 else ""))
            else:
                lines.append(f"  {p['name']}: {p['host']} answers; bale {v} on {p['host']} is older than the "
                             f"read side's floor {cons.floor}; {level_step(p['name'])} brings it level with "
                             f"this machine's bale{f' ({here})' if here else ''} before a session is sent there")
        except BaleError as exc:
            lines.append(f"  {p['name']}: {exc}" if exc.kind == "unreachable"
                         else f"  {p['name']}: {p['host']} answers, but bale there could not be read: {exc}")
        except oh.HelperError as exc:
            lines.append(f"  {p['name']}: bale's version on {p['host']} could not be compared: {exc}")
    return lines, 0


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


class Tray:
    """The out tray being filled: a staging directory beside its final
    place, renamed to the session id once the session is packed."""

    def __init__(self, root):
        self.root = pathlib.Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)
        self.dir = pathlib.Path(tempfile.mkdtemp(prefix=".filling-", dir=self.root))
        self.files = []

    def take(self, src, name=None):
        name = name or pathlib.Path(src).name
        stem, dot, ext = name.partition(".")
        n = 1
        while (self.dir / name).exists():
            n += 1
            name = f"{stem}-{n}{dot}{ext}"
        shutil.copy2(src, self.dir / name)
        self.files.append(name)
        log(f"out tray: {name}")
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
    matches none refuses, naming what is declared."""
    declared = list(entry["rides"]) if entry is not None else []
    if not leave_out:
        return declared, []
    if not declared:
        raise StartError([f"--leave-out {leave_out[0]}: nothing rides with {project or 'this session'}, "
                          "so there is nothing to leave out"])
    left = []
    for want in leave_out:
        try:
            want_path = pathlib.Path(os.path.expanduser(want)).resolve()
        except (OSError, RuntimeError):
            want_path = None
        hit = [r for r in declared if r == want.rstrip("/")
               or (want_path is not None and oh.expand_project_path(r).resolve() == want_path)]
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


def bundle_lands(office_root, bundle):
    """Where a planner's bundle says its session lands, from the LANDS line
    its brief carries (0.24.0; office_helper.brief_lands): a dict with
    place (office, or a project's name), project (the name, or None for
    the office), folder (the desk folder's directory name, or "new") and
    words (one line saying where it lands and in which folder), each None
    when that half cannot be taken; and said, the lines that say why a
    half cannot (a line that does not read, a project the office does not
    scope, a folder it does not hold on the desk), so its question comes
    back alone. absent is True when the brief carries no LANDS line at all,
    or the bundle cannot be read here."""
    out = {"absent": False, "place": None, "project": None, "folder": None, "folder_words": None,
           "words": None, "said": []}
    name = pathlib.Path(bundle).name
    text = bundle_brief(bundle)
    if text is None:
        out["absent"] = True
        return out
    mark, problems = oh.brief_lands(text)
    out["said"] += [f"the bundle {name}'s brief: {p}" for p in problems]
    if mark is None:
        out["absent"] = not problems
        return out
    root = pathlib.Path(office_root)
    names = [p["name"] for p in office_projects(root) or []]
    if mark["place"] == "office":
        out["place"] = "office"
    elif mark["place"] in names:
        out["place"], out["project"] = "project", mark["place"]
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


def survey_before_pack(office_root):
    """office survey --before-pack in the office: the survey page again,
    committed alone, never fatal (doctrine section 13). Its words go to
    stderr, since stdout is office start's one JSON line."""
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
    env = dict(os.environ, OFFICE_ROOT=str(office_root), PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run([str(INSTALL / "bin" / "office"), "digest", "--before-pack"], env=env,
                              stdin=subprocess.DEVNULL, stdout=sys.stderr, stderr=sys.stderr, timeout=PACK_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"warning: the digest before the pack could not run ({exc}); the sitting reads the page as it was")
        return
    if proc.returncode != 0:
        log(f"warning: the digest before the pack exited {proc.returncode}; the sitting reads the page as it was")


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
SUITE_RUNNING_RE = re.compile(r"^RUNNING since (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\b")


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


def start(rd, office_root, folder, where, project, goal, slug, includes, writes, read_only,
          brief, work_class, tray_root, bundle=None, leave_out=(), install_files=(), checked=False,
          bale_rehearsed=False, bundle_found=None):
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

    bundle_found is the file bale's rehearsal found a bundle at (bale
    open --check, earlier in the same start). A bundle named by a bare
    name is bale's to find, so the office cannot read its pack line where
    it was named; it reads it there instead, and only to tell whether the
    bundle sends out a sitting, so the digest is written before it as
    before any other sitting (0.21.0). Every other check keeps reading
    the bundle where it was named, as before."""
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
    rides, left = ride_choice(entry, project, leave_out)
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
        hosted_round(rd, pack_dir, named, doctrine=True, version=bool(bundle))
    else:
        pack_dir = entry["resolved"]
        ok, why = oh.check_project_dir(pack_dir)
        if not ok:
            raise StartError([f"{project} cannot be packed: {why}"])
        forecast = [] if read_only else (list(writes) or list(includes) or None)
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
    if not (bundle and argv is None):
        lines = overlap_lines(rd, office_root, pack_dir, where, project, forecast, bundle, bundle_supersedes)
        if lines and not (bundle and bale_rehearsed):
            raise StartError(lines)
        if lines:
            debug("the office's overlap check caught this bundle and bale's rehearsal passed it: bale's to judge")

    # Every check has passed: survey the machine again before anything
    # is packed, so the hung survey this session reads is current, and a
    # refused start commits nothing.
    survey_before_pack(office_root)
    # A sitting (a read-only office session, a bundle's included) opens on
    # the digest: written just before the pack, and the drafting table
    # rides with the sitting whenever the office has one. A bundle's pack
    # line is the planner's, so the office adds no include to it; the
    # digest is still written, and rides if the bundle includes the table.
    sitting = where == "office" and forecast == []
    unknown = None
    if where == "office" and bundle and argv is None:
        # The office could not read the bundle's pack line where it was
        # named, so its forecast is unknown here. Until 0.21.0 that left
        # a bare-named sitting without its digest, and said nothing. The
        # line is read where bale's rehearsal found the bundle; when even
        # that cannot be read, the start says why it left the page.
        found_read_only = bundle_read_only(bundle_found)
        if found_read_only is True:
            sitting = True
            debug(f"the bundle {pathlib.Path(bundle).name} is read-only by its pack line at {bundle_found}: "
                  "a sitting, so the digest is written before it")
        elif found_read_only is None:
            unknown = (f"bale found it at {bundle_found}, and its pack line there does not read" if bundle_found
                       else "bale's rehearsal did not say where it found it")
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
    if riding:
        if where == "office" and not bundle:
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
        req_tree = pack_dir if where == "project" else None
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
        if where == "project":
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
        # The session itself, last.
        if bundle:
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
    # The opener says how many drops ride, in one line after bale's own.
    if riding and opened["opener"] is not None:
        opened["opener"] = [*opened["opener"], "", odrop.opener_line(len(riding), sitting=forecast == [])]
    kind = "an office session" if where == "office" else project + " session"
    if hosted:
        kind += f", packed on {pack_dir.host} and carried back"
    if bundle:
        kind += f", from the bundle {pathlib.Path(bundle).name}"
        if opened["second_desk"]:
            kind += ", joined as a second desk: the session was already open"
    carried.insert(0, f"{name}: the request ({kind})")
    return {"sid": sid, "tray": str(final), "files": sorted(tray.files), "carried": carried,
            "opener": opened["opener"], "pack_dir": str(pack_dir), "request": str(final / name),
            "warnings": warnings, "sitting": forecast == [], "second_desk": opened["second_desk"],
            "drops": len(riding)}


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
RESPONSE_NAME_RE = re.compile(r"^response-(.+?)(?: \(\d+\))?\.tar\.gz$")
# The commits that leave office start's record of a session in a folder:
# office sessions recording it, and office land putting it back.
RECORD_SUBJECTS = ("office sessions: {sid} in ", "office land: {sid} recorded again in ")


class LandError(StartError):
    """office land cannot go on, said as lines a person can act on."""


def repos(office_root):
    """([(label, project entry or None, directory)], problem lines): the
    office's own registry, when bale keeps one there, and every project
    it scopes that can be read."""
    out, bad = [], []
    own = office_registry(office_root)
    if own is not None:
        out.append((OFFICE_LABEL, None, own))
    for p in office_projects(office_root) or []:
        try:
            out.append((p["name"], p, readable(p)))
        except BaleError as exc:
            bad.append(f"{p['name']}: cannot read: {exc}")
    return out, bad


def open_anywhere(rd, office_root, sid=None, unreachable=None):
    """(sessions, problems): every session open in a repo the office
    reads, each a dict: sid, label, project, repo, read_only, folders
    (the folders whose Sessions section names it, space/name). For a
    hosted repo the status, and with sid that session's dossier, travel
    in one connection (since 0.16.0); a host that does not answer is a
    problem line and, given the list unreachable, (label, line) in it."""
    naming = folders_naming(office_root)
    found, problems = repos(office_root)
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
                            "after_land_problem": "; ".join(p["declaration_problems"]) if p else ""})
        except BaleError as exc:
            problems.append(f"{label}: cannot read: {exc}")
            if exc.kind == "unreachable" and unreachable is not None:
                unreachable.append((label, str(exc)))
    return out, problems


def landable_out(x):
    """Whether an open session is one the office has out: a folder records
    it, or it is a standalone sort in the office's own registry (0.20.0);
    a read-only sitting lands nothing."""
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
    own = office_registry(office_root)
    if own is None:
        return []
    return [sid for sid in rd.key(rd.status(own), "status", "sessions") or [] if osort.is_sort_sid(sid)]


def responds_to(path):
    """The session a response tarball answers: its manifest's
    responds_to. The tarball is the worker's file, not bale's records."""
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
    words = shlex.split(place.shell)
    inner = shlex.quote(command)
    if words and words[0] == "ssh":
        inner = f'"{inner}"' if not any(c in inner for c in '"$`\\') else shlex.quote(inner)
    return " ".join(shlex.quote(w) for w in words) + " " + inner


def land_plan(rd, office_root, sid=None, folder=None, response=None, cwd=None, downloads=None):
    """The one session to land and how: a dict (sid, label, project,
    repo or place, where, folders, verb apply or retry, tarball,
    needs_response, response_default, needs_downloads, took, attempts_before,
    record, after_land, problems). Raises LandError with lines when there
    is none, or more than one.

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
    if not landable:
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
                office_session=x["label"] == OFFICE_LABEL, problems=problems, record=None, where=str(place))
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


def end_sitting(rd, office_root, plan, day):
    """bale unlock for a read-only sitting, then one History line in each
    folder that records it, committed alone. The folder keeps its status:
    a planning folder may outlive one sitting, and closing it is the
    occupant's (office close). Returns (words, told lines)."""
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
            _, wrote = oh.folder_event(root / rel, day, "ended", f"{sid}, a read-only sitting, closed by office land")
        except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
            told.append(f"{rel}: the end of {sid} could not be written there ({exc}); the sitting is closed in bale")
            continue
        if not wrote:
            told.append(f"{rel} has no History section, so the end of {sid} is not written there")
            continue
        try:
            git(root, "add", "--", rel)
            git(root, "commit", "-q", "-m", f"office land: {sid} ended in {pathlib.Path(folder).name}", "--", rel)
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
        if alone_in(root, folder, sid):
            alone.append(folder)
    where = "the office" if x["label"] == OFFICE_LABEL else x["label"]
    words = (f"Withdrawn: {sid} is closed in {where}, never worked; bale records it as {reason}."
             + ("" if x["folders"] else " No folder recorded it (the in-tray's sort)."))
    return words, told, alone


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


def outcome_words(plan, outcome):
    """(words, next line or None) for where a landing ended, in the
    office's words; bale's own lines above say the rest."""
    sid, where = plan["sid"], plan["label"]
    nothing = "nothing landed, and the session stays open"
    if outcome == "applied":
        return f"Landed: {sid} is applied in {where} (tag applied/{sid}).", None
    if outcome == "held":
        return (f"Held: bale held {sid} in {where}; {nothing}. Carry bale's blocks above, the worker's first.",
                f"office land {sid} --response FILE, with the corrected response (bale retry runs it)")
    if outcome in ("base-drift-refused", "scope-drift-refused", "required-check-refused"):
        what = {"base-drift-refused": "a file it changes moved since the pack",
                "scope-drift-refused": "it changes paths outside the session's forecast",
                "required-check-refused": "its validation leaves out a check the project requires"}[outcome]
        return (f"Refused: bale refused {sid} in {where}: {what}; {nothing}. bale printed the line that admits it "
                "above; the office never runs it for you.", None)
    if outcome == "clarification":
        if plan.get("place"):
            # The answer is a file here; bale relay reads it on stdin there.
            line = printed_line(plan_place(plan), f"cd {ohost.shell_path(plan['place']['path'])} && bale relay {sid} -")
            return (f"Questions: the worker asked before building; {nothing}. The block for the planner is below.",
                    f"{line} < ANSWER-FILE, with the planner's answer saved here as ANSWER-FILE (bale relay "
                    f"reads it from stdin on {plan['place']['host']})")
        return (f"Questions: the worker asked before building; {nothing}. The block for the planner is below.",
                f"(cd {plan['repo']} && bale relay {sid} ANSWER-FILE), with the planner's answer")
    if outcome == "reverted":
        return (f"Reverted: bale's walkthrough discarded {sid}'s branch in {where}; nothing landed. bale's lines "
                "above say what stays open.", None)
    if outcome == "bailout":
        return f"Bailed: the worker handed {sid} off; nothing landed. bale printed the handoff step above.", None
    if outcome == "refused":
        return f"Not landed: bale refused before it recorded an attempt for {sid}; its words are above.", None
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
    words, nxt = outcome_words(plan, outcome)
    applied = outcome == "applied"
    told = put_record_back(office_root, plan, applied, day)
    return {"outcome": outcome, "applied": applied, "words": words, "next": nxt, "told": told,
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
    if not rd.hosted(where):
        try:
            return rd.interact(plan["verb"], where, capture, tarball=plan["tarball"])
        except BaleError as exc:
            log(f"error: {exc}")
            return LAND_RUN_FAILED
    try:
        with ohost.Scratch(where) as scratch:
            remote = scratch.send(plan["tarball"])
            log(f"carried {pathlib.Path(plan['tarball']).name} to {where.host} ({remote}, checked by sha256; "
                "removed when bale is done)")
            return rd.interact(plan["verb"], where, capture, cleanup=scratch, tarball=remote)
    except (BaleError, ohost.HostError) as exc:
        log(f"error: {exc}")
        log(f"error: nothing was applied; the response is still at {plan['tarball']}")
        return LAND_RUN_FAILED


def land_after(plan, index):
    """The project's after-land action number index (1-based), run in its
    repo on its host, its output on this terminal: attended on a terminal,
    piped with stdin closed. Returns its exit code."""
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
            for line in ohost.clone_to(place, a.source):
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
        for line in ohost.prepare(place):
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


def land_main(a):
    """The land-* subcommands: error lines on stderr and exit 1 when the
    office cannot go on; land-run exits with bale's own code."""
    rd = Reader()
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
            plan = land_plan(rd, a.office, a.sid, a.folder, a.response, a.cwd, downloads)
            pathlib.Path(a.plan).write_text(json.dumps(plan), encoding="utf-8")
            return 0
        plan = json.loads(pathlib.Path(a.plan).read_text(encoding="utf-8"))
        if a.cmd == "land-end":
            words, told = end_sitting(rd, a.office, plan, a.day)
            print(json.dumps({"words": words, "told": told}))
            return 0
        if a.cmd == "land-prepare":
            line = take_record_out(a.office, plan)
            pathlib.Path(a.plan).write_text(json.dumps(plan), encoding="utf-8")
            if line:
                print(line)
            return 0
        if a.cmd == "land-run":
            return land_run(rd, plan, a.capture)
        if a.cmd == "land-after":
            return land_after(plan, a.index)
        if a.cmd == "land-after-line":
            print(land_after_line(plan, a.index))
            return 0
        print(json.dumps(land_outcome(rd, a.office, plan, a.exit, a.capture, a.day)))
        return 0
    except StartError as exc:
        for line in exc.lines:
            log(f"error: {line}")
        return 1
    except (oh.HelperError, BaleError, OSError, ValueError) as exc:
        log(f"error: {exc}")
        return 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_bale.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("in-flight"); p.add_argument("office")
    p.add_argument("--now", help="an ISO timestamp to measure ages from (default: now)")
    p = sub.add_parser("folder-sessions"); p.add_argument("office"); p.add_argument("folder_md")
    p = sub.add_parser("ledger"); p.add_argument("office"); p.add_argument("--project")
    p = sub.add_parser("landed"); p.add_argument("office"); p.add_argument("path"); p.add_argument("--project")
    p = sub.add_parser("versions"); p.add_argument("office"); p.add_argument("--project")
    p = sub.add_parser("status-lines"); p.add_argument("office")
    p = sub.add_parser("desk"); p.add_argument("office"); p.add_argument("--today", required=True)
    p.add_argument("--since", help="the day of the previous walk-in (default: today)")
    p.add_argument("--walk-in", action="store_true", help="In flight and the first ready folders only")
    p.add_argument("--next-file", help="write the walk-in's Next line to this file")
    p.add_argument("--skew", choices=("current", "behind", "ahead", "unreadable"), default="current",
                   help="the office's version state, for the Next line")
    p.add_argument("--founded", choices=("yes", "no"), default="yes", help="whether the profile is complete")
    p.add_argument("--blueprint", help="only this blueprint's member folders, in the desk's order")
    p = sub.add_parser("writers"); p.add_argument("office"); p.add_argument("paths", nargs="+")
    p = sub.add_parser("sort-out", help="the standalone sorts open in the office's registry, one id per line")
    p.add_argument("office")
    p = sub.add_parser("start", help="pack a session for a folder and fill its out tray; one JSON line on stdout")
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
    p.add_argument("--bundle-found", default=None,
                   help="the file bale's rehearsal found the bundle at this start (bundle-check's first line), "
                        "read only to tell whether a bundle named by a bare name sends out a sitting")
    p = sub.add_parser("start-check", help="a project on a host answers, its bale is at the floor and its repo is "
                                           "bale's, before start writes anything: HOST<tab>VERSION, or nothing for a "
                                           "project on this machine")
    p.add_argument("office"); p.add_argument("--project", required=True)
    for name, text in (("level-plan", "what office projects level-bale would do: STATE<tab>THERE<tab>HERE<tab>HOST, "
                                      "STATE one of level, behind, ahead, absent"),
                       ("level-bale", "install on the project's host the bale this machine runs, keeping its user/")):
        p = sub.add_parser(name, help=text)
        p.add_argument("office"); p.add_argument("--project", required=True)
    p = sub.add_parser("bundle-check", help="bale open --check where the bundle would open; the path bale found")
    p.add_argument("office"); p.add_argument("--where", choices=("office", "project"), required=True)
    p.add_argument("--project"); p.add_argument("--bundle", required=True)
    p.add_argument("--checked", action="store_true",
                   help="bin/office has checked the project's host this start (start-check)")
    p = sub.add_parser("start-riders", help="the riders a start's pack carries: N<tab>TITLE<tab>RIDES<tab>TOUCHED")
    p.add_argument("office"); p.add_argument("folder", help="desk/NAME")
    p.add_argument("--where", choices=("office", "project"), required=True); p.add_argument("--project")
    p.add_argument("--include", action="append", default=[]); p.add_argument("--write", action="append", default=[])
    p.add_argument("--read-only", action="store_true"); p.add_argument("--bundle")
    p = sub.add_parser("install-lines", help="the walk-in's lines about the install, when this office scopes its "
                                             "source: Install: BEHIND ... when the source moved past the install, "
                                             "Suite: ... when the latest detached run's verdict is not OK; nothing "
                                             "otherwise")
    p.add_argument("office")
    p = sub.add_parser("bundle-where", help="where a bundle opens by default: DEFAULT<tab>WHY, or nothing")
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
        p = sub.add_parser(name, help=text)
        p.add_argument("--path", required=True); p.add_argument("--host"); p.add_argument("--shell")
        p.add_argument("--connect"); p.add_argument("--name")
        if name.startswith("clone-"):
            p.add_argument("--from", dest="source", required=True)
        if name == "install-guard":
            p.add_argument("--audience", required=True); p.add_argument("--url", default="")
    p = sub.add_parser("land-out", help="the sessions out: sid, where, folders; one per line")
    p.add_argument("office")
    p = sub.add_parser("land-plan", help="the one session to land and how, as JSON into --plan")
    p.add_argument("office"); p.add_argument("--sid"); p.add_argument("--folder"); p.add_argument("--response")
    p.add_argument("--cwd", help="where a relative response path is read from (default: here)")
    p.add_argument("--plan", required=True)
    p.add_argument("--downloads", action="append", default=[],
                   help="a directory machine.toml's downloads lists (repeatable)")
    p.add_argument("--no-downloads", action="store_true", help="machine.toml sets no downloads")
    p = sub.add_parser("land-end", help="end a read-only sitting: bale unlock, then the folder's History; one JSON line")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--day", required=True)
    p = sub.add_parser("land-prepare", help="take the office's record out of an office session's folder")
    p.add_argument("office"); p.add_argument("--plan", required=True)
    p = sub.add_parser("land-run", help="bale apply or retry, the terminal's; exits with bale's code")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--capture", required=True)
    for name, text in (("land-after", "a hosted project's after-land action N, run on its host; exits with its code"),
                       ("land-after-line", "the line that reruns the after-land actions from N on")):
        p = sub.add_parser(name, help=text)
        p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--index", type=int, required=True)
    p = sub.add_parser("find-download", help="a file by name in the downloads, the newest of its browser copies: "
                                             "its path, and on stderr which was taken")
    p.add_argument("--name", required=True); p.add_argument("--dir", action="append", default=[])
    p = sub.add_parser("relay", help="bale relay SID - where the session is open, the planner's answer on its stdin")
    p.add_argument("office"); p.add_argument("--sid", required=True); p.add_argument("--answer", required=True)
    p.add_argument("--cwd"); p.add_argument("--downloads", action="append", default=[])
    p = sub.add_parser("land-outcome", help="what happened, from bale's records; one JSON line")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--capture", required=True)
    p.add_argument("--exit", type=int, required=True); p.add_argument("--day", required=True)
    p = sub.add_parser("bundle-lands", help="where a bundle's brief says it lands (its LANDS line): place<tab>office "
                                            "or place<tab>project<tab>NAME, folder<tab>NAME or folder<tab>new, "
                                            "words<tab>LINE, say<tab>WHY, or absent")
    p.add_argument("office"); p.add_argument("--bundle", required=True)
    p = sub.add_parser("bundle-sitting", help="whether a bundle's pack line sends out a sitting: yes, no or unknown")
    p.add_argument("--bundle", required=True)
    p = sub.add_parser("withdraw-list", help="the sessions out that can be withdrawn: SID<tab>LABEL<tab>FOLDERS<tab>"
                                             "CREATED; those that cannot: kept<tab>SID<tab>WHY")
    p.add_argument("office"); p.add_argument("--dir", action="append", default=[])
    p.add_argument("--no-downloads", action="store_true", help="machine.toml sets no downloads")
    p = sub.add_parser("withdraw", help="close a session that was never worked (bale unlock --reason abandoned), "
                                        "then its folders' History; one JSON line")
    p.add_argument("office"); p.add_argument("--sid", required=True); p.add_argument("--day", required=True)
    p.add_argument("--dir", action="append", default=[])
    p.add_argument("--no-downloads", action="store_true", help="machine.toml sets no downloads")
    a = ap.parse_args(argv)
    if a.cmd == "bundle-lands":
        got = bundle_lands(a.office, a.bundle)
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
        for line in got["said"]:
            print(f"say\t{line}")
        return 0
    if a.cmd == "bundle-sitting":
        ro = bundle_read_only(a.bundle)
        print("unknown" if ro is None else ("yes" if ro else "no"))
        return 0
    if a.cmd in ("withdraw-list", "withdraw"):
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
    if a.cmd.startswith("land-"):
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
    if a.cmd == "start-riders":
        try:
            forecast, riders = start_riders(a.office, a.folder, a.where, a.project, a.write, a.include,
                                            a.read_only, a.bundle)
        except (oh.HelperError, OSError, ValueError) as exc:
            log(f"warning: the riders this pack carries could not be read ({exc}); none is offered")
            return 0
        if forecast is None:
            say = log if (pathlib.Path(a.office) / od.SPACE / "riders.md").is_file() else debug
            say("the office cannot read this bundle's forecast, so it offers no riders for it")
        for r in riders:
            print(f"{r['number']}\t{r['title']}\t{r['rides']}\t{', '.join(r['touched'])}")
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
    if a.cmd == "start":
        try:
            result = start(Reader(), a.office, None if a.folder == "-" else a.folder, a.where, a.project, a.goal,
                           a.slug, a.include,
                           a.write, a.read_only, a.brief, a.work_class, a.tray_root, a.bundle, a.leave_out,
                           a.install_file, a.checked, a.bale_rehearsed, a.bundle_found)
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
                                     blueprint=a.blueprint)
            if a.next_file:
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
    for line in lines:
        print(line)
    # The lines already say which project could not be read and why;
    # the exit code tells the caller, which decides how loud to be.
    return 3 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
