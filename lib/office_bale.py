#!/usr/bin/env python3
"""The office's read side: the reader over bale's records and its renderings.

The office reads bale's records in its projects' repos and renders them;
it never copies them (doctrine section 10). This module is the only place
the office talks to bale. It runs `bale` from the PATH in a project's
directory with stdin closed, reads the one JSON line a --json surface
prints, and returns plain data. It never reads .bale/. The reads write
nothing. Two verbs run bale to make or land something, when the
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
import shutil
import subprocess
import sys
import tarfile
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_drafting as od  # noqa: E402
import office_door as odoor  # noqa: E402

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
    a defect in office-src)."""

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

    def invoke(self, surface, cwd=None, timeout=BALE_TIMEOUT, whole_why=False, **values):
        """Run one declared surface with stdin closed; (proc, shown, where).
        Refuses when bale exits non-zero, carrying bale's last words, or,
        with whole_why, everything from its error line on (a refusal that
        lists what it searched, say)."""
        argv = self.consumption.argv(surface, **values)
        where = str(cwd) if cwd is not None else os.getcwd()
        exe = self.bale()
        if cwd is not None and not pathlib.Path(cwd).is_dir():
            raise BaleError("path", f"no such directory on this machine: {cwd}")
        shown = "bale " + " ".join(argv)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        try:
            proc = self.runner([exe, *argv], cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise BaleError("refused", f"{shown} in {where} did not finish in {timeout}s")
        except OSError as exc:
            raise BaleError("missing", f"could not run {exe}: {exc}")
        debug(f"{shown} in {where}: exit {proc.returncode}, {len(proc.stdout)} bytes on stdout")
        if proc.returncode != 0:
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

    def interact(self, surface, cwd, capture, **values):
        """Run a surface the occupant answers: stdin and stderr stay his
        terminal, so every question bale asks reaches him as bale asks it
        and the office answers none; stdout is copied to ours as it comes
        and kept in the capture file, for the blocks bale prints to carry.
        Returns bale's exit code."""
        spec = self.consumption.surface(surface)
        if not spec.get("interactive"):
            raise BaleError("undeclared", f"bale {surface} is not declared interactive in {self.consumption.path.name}")
        argv = self.consumption.argv(surface, **values)
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
        return proc.wait()

    def unlock(self, cwd, sid):
        """End a read-only sitting: bale unlock SID --json in its repo,
        stdin closed, since bale asks nothing there (the second-trip probe
        found it so, on a terminal and piped). Never cached; what was
        cached about the repo is dropped, since the registry changed."""
        proc, shown, where = self.invoke("unlock", cwd, whole_why=True, sid=sid)
        self.forget(cwd)
        return self.parse("unlock", proc, shown, where)

    def pack(self, surface, cwd, **values):
        """Run one of the surfaces that make something (a session, a
        context tarball): never cached, since each run makes a new one.
        Returns (the report, bale's stderr lines)."""
        proc, shown, where = self.invoke(surface, cwd, timeout=PACK_TIMEOUT, **values)
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

    def installed_version(self):
        """bale's version from `bale --version`, or raise."""
        line = self.run("version")
        m = re.match(self.consumption.surface("version")["pattern"], line)
        if not m:
            raise BaleError("output", f"bale --version printed {line!r}, not `bale X.Y.Z`")
        self._installed = m.group(1)
        return self._installed

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
    """The project's directory, or raise BaleError saying why it cannot
    be read. A path that is not on this machine is an error line: reading
    a project on another machine is an open question (seed Q-2)."""
    if project["problem"]:
        raise BaleError("path", project["problem"])
    if not project["resolved"].is_dir():
        raise BaleError("path", f"no such directory on this machine: {project['resolved']}")
    return project["resolved"]


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
            for sid, read_only in rd.open_sessions(cwd):
                open_count += 1
                folders = naming.get(sid, [])
                flying.update(folders)
                d = rd.dossier(cwd, sid)
                # What ends a sitting the office sent out; never on the
                # Next line, since nothing in the office knows when a
                # sitting is over. A sitting no folder records is not
                # the office's to end.
                ends = f" (office land {sid} when the sitting is over)" if read_only and folders else ""
                if d is None:
                    lines.append(f"{label}: {sid} open, with no record in bale's telemetry yet"
                                 f" -> {', '.join(folders) or 'no folder'}{ends}")
                    continue
                v = session_view(rd, d)
                state = "read-only" if read_only else outcome_word(v)
                age = describe_age(parse_stamp(v["created"]), now)
                lines.append(f"{label}: {sid} {state}, opened {age} ago"
                             f" -> {', '.join(folders) or 'no folder'}{ends}")
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
        return lines
    if not on_desk:
        extra = drafting_lines(groups)
        return lines + ["", "the desk is clear"] + extra
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
    if groups_out is not None:
        groups_out.update(groups)
    if not walk_in and groups["moves"][0]:
        # Each pending move by line, so the desk shows what office moves
        # will do; the words are the sitting's, as it wrote them.
        try:
            moves, _ = od.pending_moves(office_root)
            src = od.move_sources(office_root)
            groups["move_lines"] = [f"  line {m['line']}: {m['day']} {m['text']}  (from {src.get(m['line'], '?')})"
                                    for m in moves]
        except (OSError, oh.HelperError) as exc:
            groups["move_lines"] = [f"  could not be listed: {exc}"]
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
            d = rd.dossier(x["repo"], x["sid"])
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
    """The project a folder's lane names (`project: paths`), when it is
    one this office scopes, else None."""
    lane = (folder.get("fields", {}).get("lane") or [""])[0]
    name = lane.partition(":")[0].strip() if ":" in lane else ""
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


def next_move(skew, founded, out, groups, projects, slips):
    """(command, why) for the walk-in's Next line, from the office's state:
    skew (current, behind, ahead or unreadable), founded (bool), out
    (sessions_to_land's list), groups (classify_desk's), projects (the
    [projects] entries, or None for no table) and slips (a count). A pure
    function, so every state is testable without an office."""
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
    return ("office open", "nothing waits on you; open asks for a new job's title when one comes in, and office "
                           "note TEXT captures a thought")


def next_line(rd, office_root, skew, founded, groups):
    """The walk-in's Next line, read from the office and bale's records."""
    out, problems = sessions_to_land(rd, office_root)
    for p in problems:
        debug(f"the Next line could not read every repo: {p}")
    command, why = next_move(skew, founded, out, groups, office_projects(office_root),
                             count_slips(office_root))
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
            readable(p)
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
    for sid in rd.known_sids(cwd):
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
            agg = rd.aggregate(cwd)
            classes = rd.key(agg, "stats", "classes") or {}
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
    problems = []
    for p in projects:
        ok, text = (False, p["problem"]) if p["problem"] else oh.check_project_dir(p["resolved"])
        if not ok:
            problems.append(f"  {p['name']}: {text}")
    lines.append(f"projects:   {len(projects)} in scope"
                 + (f"; {len(problems)} cannot be read" if problems else "; each is a repo bale runs in"))
    return lines + problems, 0


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
    if not (pathlib.Path(cwd) / ".bale").is_dir():
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


def bundle_places(office_root, paths):
    """[(label, directory, missing paths)] for every place a bundle could
    open in: the office, then each project it scopes that can be read,
    by name. A place whose missing list is empty holds every path."""
    root = pathlib.Path(office_root).resolve()
    places = [("office", root)]
    for p in office_projects(root) or []:
        if not p["problem"] and p["resolved"].is_dir():
            places.append((p["name"], p["resolved"]))
    return [(label, d, [x for x in paths if not (d / x.strip("/")).exists()]) for label, d in places]


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


def open_bundle(rd, pack_dir, bundle):
    """Run bale open for a planner bundle in pack_dir, stdin closed, so
    no question is answered for the occupant; a pre-answered intent in
    the bundle is bale's to honour. Returns sid, tarball and opener. The
    sid is the session bale status lists after the open and did not
    before; the tarball is the report's tarball line, held to the
    request that status lists for that sid."""
    spec = rd.consumption.surface("open")
    before = set(rd.key(rd.status(pack_dir), "status", "sessions") or [])
    proc, shown, where = rd.invoke("open", pack_dir, timeout=PACK_TIMEOUT, whole_why=True, bundle=bundle)
    lines = proc.stdout.splitlines()
    rd.forget(pack_dir)
    st = rd.status(pack_dir)
    new = [x for x in (rd.key(st, "status", "sessions") or []) if x not in before]
    if len(new) != 1:
        raise BaleError("output", f"{shown} exited 0 in {where}, but bale status names {len(new)} newly open "
                                  f"session(s) ({', '.join(new) or 'none'}), so the office cannot tell which it opened")
    sid = new[0]
    name = f"request-{sid}.tar.gz"
    tarball = None
    for line in lines:
        if line.startswith(spec["tarball_line"]):
            tarball = line[len(spec["tarball_line"]):].strip()
    if tarball is None or pathlib.Path(tarball).name != name or name not in (rd.key(st, "status", "outbox") or []):
        raise BaleError("output", f"{shown} opened {sid} in {where}, but its report's tarball line "
                                  f"({tarball or 'none'}) is not the request bale status lists for it ({name})")
    return {"sid": sid, "tarball": tarball, "opener": opener_lines(lines, spec)}


def start(rd, office_root, folder, where, project, goal, slug, includes, writes, read_only,
          brief, work_class, tray_root, bundle=None, leave_out=(), install_files=()):
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
    scratch copy so the install is never written."""
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

    # Where the pack runs, and its forecast.
    warnings = []
    if where == "office":
        pack_dir = office_root
        includes = [folder, *includes]
        if read_only:
            forecast = []
        elif any(w.strip().strip("/") in ("", ".") for w in writes):
            # The whole office (a renovation that declares no narrower
            # forecast): bale's default, the whole tree shipped and
            # forecast, as the renovation's printed pack line was.
            writes, includes, forecast = [], [], None
        else:
            writes = [folder] + (["notepad"] if (office_root / "notepad").is_dir() else []) + list(writes)
            forecast = writes
    else:
        pack_dir = entry["resolved"]
        ok, why = oh.check_project_dir(pack_dir)
        if not ok:
            raise StartError([f"{project} cannot be packed: {why}"])
        forecast = [] if read_only else (list(writes) or list(includes) or None)
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
            places = bundle_places(office_root, named)
            mine = next((m for lab, _, m in places if lab == label), None)
            if mine is None:
                mine = [x for x in named if not (pathlib.Path(pack_dir) / x.strip("/")).exists()]
            if mine:
                raise StartError([f"the bundle {pathlib.Path(bundle).name} names paths that are not in "
                                  f"{place_words(label)}'s tree, so it cannot open there; nothing ran"]
                                 + bundle_nowhere_lines(bundle, named, places, chosen=label))
            bundle_tree_includes, bundle_tree_excludes = (b_inc or None), b_exc
        if argv is None:
            forecast = None
            why = ("it is a name bale's search finds, not a file here" if not pathlib.Path(bundle).exists()
                   else "its pack line could not be read")
            log(f"the office cannot read this bundle's forecast ({why}), so it cannot check it against the "
                "sessions open there; if they overlap, bale's own words below say so")
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
    for p in (writes if not read_only else []):
        if not (pathlib.Path(pack_dir) / p).exists():
            raise StartError([f"--write {p}: no such path in {pack_dir}; a forecast names existing paths "
                              "(a directory covers new files under it)"])
    for p in includes:
        if not (pathlib.Path(pack_dir) / p).exists():
            raise StartError([f"--include {p}: no such path in {pack_dir}"])

    # The predictable refusal, said plainly before bale is asked: two
    # sessions whose forecasts overlap never run beside each other.
    naming = folders_naming(office_root)
    if bundle and argv is None:
        clash = []
    else:
        clash = [c for c in open_overlaps(rd, pack_dir, forecast) if c[0] != bundle_supersedes]
    if clash:
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
        raise StartError(lines)

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
    if sitting:
        digest_before_pack(office_root)
        if not bundle and (office_root / od.SPACE).is_dir() and od.SPACE not in includes:
            includes = [*includes, od.SPACE]

    # The packed trees that may carry a doctrine of their own: the
    # request's (a project session's repo) and, for an office session
    # about a project, the project's tree riding as context.
    if bundle:
        req_tree = pack_dir if argv is not None and where == "project" else None
        req_inc, req_exc = (bundle_tree_includes, bundle_tree_excludes) if req_tree else (None, ())
    else:
        req_tree = pack_dir if where == "project" else None
        req_inc, req_exc = (list(includes) or None), ()
    own = doctrine_in_tree(req_tree, req_inc, req_exc)
    if own is None and where == "office" and entry is not None:
        own = doctrine_in_tree(entry["resolved"], None)
    if own is not None:
        same = doctrine_files(own) == doctrine_files(INSTALL / "doctrine")
        tree_label = project if where == "project" or entry is not None else "the request"

    tray = Tray(tray_root)
    carried = []
    stage = "a context pack"
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
            carried.append(context_into_tray(rd, tray, office_root, [folder, *hung],
                                              f"the office: {folder} and the hung items"))
        elif entry is not None:
            # An office session about a project reads the project's tree.
            carried.append(context_into_tray(rd, tray, entry["resolved"], None, f"{project}'s tree"))
        if sitting and od.SPACE in includes:
            carried.append(f"(the drafting table rides inside the request, its {od.SPACE}/digest.md written "
                           "just before the pack)")
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
            opened = open_bundle(rd, pack_dir, bundle)
        else:
            stage = "the session's pack"
            spec = rd.consumption.surface("pack")
            report, stderr = rd.pack(
                "pack", pack_dir, goal=goal, slug=slug, includes=includes or None,
                writes=None if read_only or forecast is None else (forecast if where == "office" else (list(writes) or None)),
                constraints=[PROJECT_CONSTRAINT] if where == "project" else None,
                readme_file=str(pathlib.Path(brief).resolve()) if brief else None,
                no_readme=not brief, read_only=read_only, work_class=work_class)
            opened = {"sid": rd.key(report, "pack", "sid"), "tarball": rd.key(report, "pack", "tarball"),
                      "opener": opener_lines(stderr, spec)}
    except BaleError as exc:
        tray.discard()
        raise StartError([f"{stage} failed, so no session was opened and no out tray was made: {exc}"])
    except StartError:
        tray.discard()
        raise
    except (OSError, shutil.Error) as exc:
        tray.discard()
        raise StartError([f"{stage} could not be put in the out tray, so no session was opened: {exc}"])
    sid = opened["sid"]
    if not isinstance(sid, str) or not oh.SID_RE.match(sid):
        raise StartError([f"bale packed, but its report's sid is not a session id: {sid!r}; "
                          f"what was gathered is in {tray.dir}"])
    try:
        name = tray.take(opened["tarball"])
        final = tray.finish(sid)
    except (OSError, shutil.Error) as exc:
        raise StartError([f"session {sid} is open, but its out tray could not be finished: {exc}",
                          f"what was gathered is in {tray.dir}; the request is {opened['tarball']}",
                          f"record the session in its folder with: office sessions {pathlib.Path(folder).name} {sid}"])
    kind = "an office session" if where == "office" else project + " session"
    carried.insert(0, f"{name}: the request ({kind}" + (f", from the bundle {pathlib.Path(bundle).name})" if bundle else ")"))
    return {"sid": sid, "tray": str(final), "files": sorted(tray.files), "carried": carried,
            "opener": opened["opener"], "pack_dir": str(pack_dir), "request": str(final / name),
            "warnings": warnings, "sitting": forecast == []}


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


def open_anywhere(rd, office_root):
    """(sessions, problems): every session open in a repo the office
    reads, each a dict: sid, label, project, repo, read_only, folders
    (the folders whose Sessions section names it, space/name)."""
    naming = folders_naming(office_root)
    found, problems = repos(office_root)
    out = []
    for label, p, cwd in found:
        try:
            for sid, ro in rd.open_sessions(cwd):
                out.append({"sid": sid, "label": label, "project": p["name"] if p else None, "repo": str(cwd),
                            "read_only": ro, "folders": naming.get(sid, []),
                            "after_land": list(p["after_land"]) if p and not p["declaration_problems"] else [],
                            "after_land_problem": "; ".join(p["declaration_problems"]) if p else ""})
        except BaleError as exc:
            problems.append(f"{label}: cannot read: {exc}")
    return out, problems


def sessions_out(rd, office_root):
    """(sessions, problems): the sessions the office has out, the open
    ones a folder records, read-only sittings aside (they land nothing)."""
    every, problems = open_anywhere(rd, office_root)
    return [x for x in every if x["folders"] and not x["read_only"]], problems


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


def land_plan(rd, office_root, sid=None, folder=None, response=None, cwd=None):
    """The one session to land and how: a dict (sid, label, project,
    repo, folders, verb apply or retry, tarball, needs_response,
    attempts_before, record, after_land, problems). Raises LandError
    with lines when there is none, or more than one."""
    tarball = None
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
            tarball, want = response, m.group(1)
        if sid and sid != want:
            raise LandError([f"{response} answers {want}, not {sid}"])
        sid = want
    every, problems = open_anywhere(rd, office_root)
    if folder:
        found = [x for x in every if folder in x["folders"]]
        if sid:
            found = [x for x in found if x["sid"] == sid]
        if not found:
            raise LandError([f"no session {sid + ' ' if sid else ''}is out for {folder}: none it records is open "
                             "in this office or a project it scopes (office sessions FOLDER shows how each went)"]
                            + problems)
    elif sid:
        found = [x for x in every if x["sid"] == sid]
        if not found:
            raise LandError([f"{sid} is not open in this office or in any project it scopes, so there is nothing "
                             "to land (office sessions FOLDER shows how it went)"] + problems)
    else:
        found = [x for x in every if x["folders"] and not x["read_only"]]
        if not found:
            raise LandError(["no session is out: none that a folder records is open in this office or in a "
                             "project it scopes (office start sends one out)"] + problems)
    landable = [x for x in found if not x["read_only"]]
    if not landable:
        return sitting_plan(found, tarball, problems)
    if len(landable) > 1:
        raise LandError(["more than one session is out; name one: office land SID"]
                        + [f"  {x['sid']}  ({x['label']}; {', '.join(x['folders']) or 'no folder records it'})"
                           for x in landable])
    x = landable[0]
    d = rd.dossier(x["repo"], x["sid"])
    view = session_view(rd, d) if d is not None else None
    held = bool(view and view["in_flight"] and view["outcome"] == "held")
    plan = dict(x)
    plan.update(verb="retry" if held else "apply", held=held,
                tarball=tarball or f"response-{x['sid']}.tar.gz",
                needs_response=held and tarball is None,
                attempts_before=len(response_attempts(view)) if view else 0,
                office_session=x["label"] == OFFICE_LABEL, problems=problems, record=None)
    if plan["office_session"]:
        for f in x["folders"]:
            plan["record"] = folder_record(office_root, f, x["sid"])
            plan["record"]["folder"] = f
            break
    return plan


def sitting_plan(found, tarball, problems):
    """The plan for ending a read-only sitting, named by its id or its
    folder: land runs bale unlock in its repo, and nothing else. Only a
    sitting a folder records is the office's to end (one started by hand
    in a project is that project's business), and a sitting has no
    response to land."""
    if len(found) > 1:
        raise LandError(["more than one read-only sitting is open for that folder; name one: office land SID"]
                        + [f"  {x['sid']}  ({x['label']})" for x in found])
    x = found[0]
    if not x["folders"]:
        raise LandError([f"{x['sid']} is a read-only session no folder records, so it is not a sitting the office sent "
                         f"out and office land does not end it; bale unlock {x['sid']}, in {x['repo']}, ends it by hand"])
    if tarball is not None:
        raise LandError([f"{x['sid']} is a read-only sitting: it lands nothing, so there is no response to land; "
                         f"office land {x['sid']}, with no response, ends it when the sitting is over"])
    plan = dict(x)
    plan.update(verb="unlock", held=False, tarball=None, needs_response=False, attempts_before=0,
                office_session=x["label"] == OFFICE_LABEL, problems=problems, record=None)
    return plan


def end_sitting(rd, office_root, plan, day):
    """bale unlock for a read-only sitting, then one History line in each
    folder that records it, committed alone. The folder keeps its status:
    a planning folder may outlive one sitting, and closing it is the
    occupant's (office close). Returns (words, told lines)."""
    sid, repo = plan["sid"], plan["repo"]
    try:
        report = rd.unlock(repo, sid)
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
    words = (f"Ended: the sitting {sid} is closed in {plan['label']}; it landed nothing, by design. "
             f"{names} stays as it was: closing a folder is yours (office close FOLDER).")
    return words, told


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
    d = rd.dossier(plan["repo"], plan["sid"])
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
            block = exchange_block(rd.lines("relay", plan["repo"], sid=plan["sid"]), plan["sid"],
                                   rd.consumption.surface("relay"))
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


# --- command line --------------------------------------------------------------------

# bale ran, but office land could not (no bale, no such directory).
LAND_RUN_FAILED = 125


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
            plan = land_plan(rd, a.office, a.sid, a.folder, a.response, a.cwd)
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
            try:
                return rd.interact(plan["verb"], plan["repo"], a.capture, tarball=plan["tarball"])
            except BaleError as exc:
                log(f"error: {exc}")
                return LAND_RUN_FAILED
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
    p = sub.add_parser("start", help="pack a session for a folder and fill its out tray; one JSON line on stdout")
    p.add_argument("office"); p.add_argument("folder", help="desk/NAME")
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
    p = sub.add_parser("bundle-where", help="where a bundle opens by default: DEFAULT<tab>WHY, or nothing")
    p.add_argument("office"); p.add_argument("--bundle", required=True); p.add_argument("--lane")
    p = sub.add_parser("land-out", help="the sessions out: sid, where, folders; one per line")
    p.add_argument("office")
    p = sub.add_parser("land-plan", help="the one session to land and how, as JSON into --plan")
    p.add_argument("office"); p.add_argument("--sid"); p.add_argument("--folder"); p.add_argument("--response")
    p.add_argument("--cwd", help="where a relative response path is read from (default: here)")
    p.add_argument("--plan", required=True)
    p = sub.add_parser("land-end", help="end a read-only sitting: bale unlock, then the folder's History; one JSON line")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--day", required=True)
    p = sub.add_parser("land-prepare", help="take the office's record out of an office session's folder")
    p.add_argument("office"); p.add_argument("--plan", required=True)
    p = sub.add_parser("land-run", help="bale apply or retry, the terminal's; exits with bale's code")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--capture", required=True)
    p = sub.add_parser("land-outcome", help="what happened, from bale's records; one JSON line")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--capture", required=True)
    p.add_argument("--exit", type=int, required=True); p.add_argument("--day", required=True)
    a = ap.parse_args(argv)
    if a.cmd.startswith("land-"):
        return land_main(a)
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
            result = start(Reader(), a.office, a.folder, a.where, a.project, a.goal, a.slug, a.include,
                           a.write, a.read_only, a.brief, a.work_class, a.tray_root, a.bundle, a.leave_out,
                           a.install_file)
        except StartError as exc:
            for line in exc.lines:
                log(f"error: {line}")
            return 1
        except (oh.HelperError, BaleError, OSError) as exc:
            log(f"error: {exc}")
            return 1
        print(json.dumps(result))
        return 0
    try:
        rd = Reader()
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
