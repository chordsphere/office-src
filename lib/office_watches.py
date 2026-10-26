#!/usr/bin/env python3
"""The watches: the query catalog, the register and its log, and the check.

A watch is a named re-trigger with no work attached (the drafting-table
blueprint's section 1.4). Its entry lives on drafting-table/watches.md,
a live page a sitting writes; every event on it (opened, fired,
not-fired, re-armed, reworded, closed) is a record on
drafting-table/watch-log.md, a filed page that only grows at its end.
State is never edited into an entry: it is read from the log here.

An entry evaluates either `query NAME`, a condition a script computes,
or `eye`, one someone has to notice. A query is named once, in the
install's share/watch-queries.toml: the bale surface it reads, the value
it extracts, how it compares. An entry names a query and a threshold and
never a command line.

office watches check runs every open query watch over the window since
its last `fired` record, once per place the office reads bale's records
in (its own registry and each project it scopes), and prints one line
per watch and place: fired, not fired, or cannot evaluate; every eye
watch as needs an eye, with the sittings since its last record; and the
standing lines, the catalog's observations, as observed. With --record
it appends a `fired` record for each watch that fired; re-arming,
rewording and closing are a sitting's, and a `not-fired` record is a
sitting's too, when it wants one on the record.

The window. bale's stats --since takes a day, not an instant, and
counts the sessions packed on or after it. So a watch that fired on a
day looks again from the day after: a firing is never counted twice,
and a session packed later on the firing day is not seen by that watch
(a slip for bale-src: --since taking an instant). A watch that never
fired looks from the day it was opened, and one with no opened record
over bale's whole corpus. The days are the office's; bale compares them
with its own UTC stamps.

Every bale read goes through office_bale's Reader: its literal keys, and
Reader.reach for the keys a query names, both held to
share/bale-consumption.toml. Standard library only. The command line
prints on stdout, logs to stderr with an [office] prefix, and exits 0 on
success, 1 on a refusal, 2 on an internal error, and 3 when it ran but a
place could not be read or a record does not read (the lines say which).
"""

import argparse
import datetime as dt
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_drafting as od  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
CATALOG = INSTALL / "share" / "watch-queries.toml"
REGISTER = f"{od.SPACE}/watches.md"
LOG = f"{od.SPACE}/watch-log.md"

VALUE_KINDS = ("share", "sum", "count", "class-rate", "class-basis")
STANDING_KINDS = ("class-rate", "class-basis")
COMPARES = ("above", "at-least")
LOG_VERBS = ("opened", "fired", "not-fired", "re-armed", "reworded", "closed")
LOG_RE = oh.LazyPattern(rf"^- ({od.DATE}) W(\d+) ({'|'.join(LOG_VERBS)}):(?: (.*))?$")
EVALUATES_RE = oh.LazyPattern(r"^query\s+([a-z0-9][a-z0-9-]*)$")
CLASSES = "classes"
CLASS_ROW = "classes.*"
# An eye-watch no sitting has looked at for this many sittings is
# flagged in the digest (the blueprint's section 1.4). A profile house
# rule may one day change it; none is read yet.
EYE_SITTINGS = 3
# The words a check line starts its verdict with, a closed set.
VERDICTS = ("fired", "not fired", "cannot evaluate", "needs an eye", "observed")


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


# --- the catalog -----------------------------------------------------------------

class Catalog:
    """share/watch-queries.toml, read once and checked against the
    consumption manifest: a query that names a key bale's surface is not
    declared to carry is a defect in office-src, refused here."""

    def __init__(self, path=CATALOG, consumption=None):
        import office_bale as ob
        self.path = pathlib.Path(path)
        data = oh.read_toml(self.path)
        self.queries = data.get("queries")
        if not isinstance(self.queries, dict) or not self.queries:
            raise oh.HelperError(f"{self.path}: no [queries] table")
        problems = catalog_problems(self.queries, consumption or ob.Consumption())
        if problems:
            raise oh.HelperError(f"{self.path}: " + "; ".join(problems))

    def get(self, name):
        return self.queries.get(name)

    def standing(self):
        return [(n, q) for n, q in self.queries.items() if q.get("standing")]

    def keys(self):
        """(surface, key) for every key a query reads, parents included
        where a query walks a map (the reader reaches each)."""
        return {(q["surface"], k) for q in self.queries.values() if "needs" not in q for k in query_keys(q)}


def query_keys(q):
    """The key paths a query reads, in the order it reads them."""
    kind = q["value"]
    if kind == "share":
        out = [q["numerator"], q["denominator"]]
    elif kind in ("sum", "count"):
        out = [q["key"]]
    elif kind == "class-rate":
        out = [CLASSES, q["numerator"], q["denominator"]]
    else:  # class-basis
        out = [CLASSES, q["key"], q["checks"], q["agree"]]
    if q.get("evidence"):
        out.append(q["evidence"])
    return out


def catalog_problems(queries, consumption):
    """Every way the catalog breaks its own header, as lines."""
    out = []
    required = {"share": ("numerator", "denominator"), "sum": ("key",), "count": ("key",),
                "class-rate": ("numerator", "denominator"), "class-basis": ("key", "checks", "agree")}
    for name, q in queries.items():
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
            out.append(f"{name}: a query's name is lowercase letters, digits and dashes")
        if not isinstance(q, dict):
            out.append(f"{name}: not a table")
            continue
        if not isinstance(q.get("watch"), int):
            out.append(f"{name}: no watch number")
        if not isinstance(q.get("says"), str) or not q.get("says"):
            out.append(f"{name}: no says")
        if "needs" in q:
            if not isinstance(q["needs"], str) or not q["needs"].strip():
                out.append(f"{name}: needs names the datum bale lacks, in words")
            extra = set(q) - {"watch", "says", "needs"}
            if extra:
                out.append(f"{name}: a query bale cannot answer carries nothing else ({', '.join(sorted(extra))})")
            continue
        if q.get("surface") != "stats":
            out.append(f"{name}: surface is stats (the only surface a query reads yet)")
            continue
        kind = q.get("value")
        if kind not in VALUE_KINDS:
            out.append(f"{name}: value is one of {', '.join(VALUE_KINDS)}")
            continue
        missing = [k for k in required[kind] if not isinstance(q.get(k), str)]
        if missing:
            out.append(f"{name}: a {kind} query needs {', '.join(missing)}")
            continue
        standing = q.get("standing", False)
        if not isinstance(standing, bool):
            out.append(f"{name}: standing is true or false")
        if kind in STANDING_KINDS and not standing:
            out.append(f"{name}: a {kind} value is an observation, so the query is standing")
        if not standing and q.get("compare") not in COMPARES:
            out.append(f"{name}: compare is one of {', '.join(COMPARES)}")
        if standing and "compare" in q:
            out.append(f"{name}: a standing query is observed, never compared")
        if kind in STANDING_KINDS:
            for k in required[kind]:
                if not q[k].startswith(CLASS_ROW + "."):
                    out.append(f"{name}: {k} sits under {CLASS_ROW}")
            if kind == "class-basis":
                for k in ("checks", "agree"):
                    if not q[k].startswith(q["key"] + ".*."):
                        out.append(f"{name}: {k} sits under {q['key']}.*")
        declared = consumption.keys("stats")
        for k in query_keys(q):
            if k not in declared:
                out.append(f"{name}: reads {k!r}, which share/bale-consumption.toml does not declare for stats")
    return out


# --- the register and the log ------------------------------------------------------

def register(lines):
    """(watches, problems) from watches.md: watches is a list of dicts,
    in page order, with number, title, fields (key -> first value),
    line; problems names a heading that is not a watch and a number
    minted twice."""
    out, problems, seen = [], [], set()
    heads = [i for i, l in od.unfenced(lines) if l.startswith("## ")]
    for k, i in enumerate(heads):
        m = od.WATCH_HEAD_RE.match(lines[i])
        if not m:
            problems.append(f"{REGISTER}:{i + 1}: a heading that is not a watch: {lines[i]}")
            continue
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        fields, _ = od.fields_of(lines, i + 1, end)
        n = int(m.group(1))
        if n in seen:
            problems.append(f"{REGISTER}:{i + 1}: W{n} is minted twice")
        seen.add(n)
        out.append({"number": n, "title": m.group(2), "fields": {key: v[0] for key, v in fields.items()},
                    "line": i + 1})
    return out, problems


def events(lines):
    """(events, problems) from watch-log.md: each record in page order as
    (day, number, verb, text, line); problems names a record line (`- `
    outside a fence) that does not read."""
    out, problems = [], []
    for i, line in od.unfenced(lines):
        if not line.startswith("- "):
            continue
        m = LOG_RE.match(line)
        if not m:
            problems.append(f"{LOG}:{i + 1}: not a record (- DATE WN VERB: text, VERB one of "
                            f"{', '.join(LOG_VERBS)}): {line}")
            continue
        out.append((m.group(1), int(m.group(2)), m.group(3), m.group(4) or "", i + 1))
    return out, problems


def state_of(n, evs):
    """What the log says of watch n: closed, its opened, last fired and
    last record days, and its last record."""
    mine = [e for e in evs if e[1] == n]
    return {"closed": any(e[2] == "closed" for e in mine),
            "opened": next((e[0] for e in mine if e[2] == "opened"), None),
            "fired": max((e[0] for e in mine if e[2] == "fired"), default=None),
            "last": mine[-1] if mine else None}


def window(state):
    """(since day or None, words): where a query watch looks from."""
    if state["fired"]:
        since = (dt.date.fromisoformat(state["fired"]) + dt.timedelta(days=1)).isoformat()
        return since, f"since {since}, the day after it last fired"
    if state["opened"]:
        return state["opened"], f"since {state['opened']}, when it was opened"
    return None, "over bale's whole corpus (the log holds no opened or fired record for it)"


def evaluates(entry):
    """('query', NAME), ('eye', None), or (None, why it does not read)."""
    text = (entry["fields"].get("evaluates") or "").strip()
    if text == "eye":
        return "eye", None
    m = EVALUATES_RE.match(text)
    if m:
        return "query", m.group(1)
    return None, (f"its evaluates line reads {text!r}; it is `query NAME` or `eye`" if text
                  else "it has no evaluates line (`query NAME` or `eye`)")


def threshold(entry):
    """(number or 'any', None) or (None, why)."""
    text = (entry["fields"].get("threshold") or "").strip()
    if not text:
        return None, "it has no threshold line"
    if text.split()[0].lower() == "any":
        return "any", None
    try:
        return float(text.split()[0]), None
    except ValueError:
        return None, f"its threshold {text!r} is neither a number nor any"


def standing_entry(entry):
    """A register entry with no re-trigger that evaluates a query is a
    standing line, not a watch (the blueprint's section 1.4)."""
    return (entry["fields"].get("re-trigger") or "").strip().lower() == "none"


# --- sittings, from git ----------------------------------------------------------------

def sitting_key(rel, pages=()):
    """Which sitting a page belongs to: a page named SID-N.md continues
    SID.md (the sitting's later pages), so both are one sitting; and a
    page named SLUG-N.md continues SLUG.md when SLUG.md is a sitting's page
    too (pages: the stems of the notepad's sitting pages), the way the
    planner's sitting_pages joins a sitting's pages by slug (0.31.0: the
    pages office start files are named by the sitting's slug, SLUG.md,
    SLUG-2.md, and were each counted as a sitting of their own)."""
    stem = pathlib.PurePosixPath(rel).stem
    m = re.match(r"^(.*)-(\d+)$", stem)
    if m and (oh.SID_RE.match(m.group(1)) or m.group(1) in pages):
        return m.group(1)
    return stem


def sitting_filings(root):
    """[(when, page, commit, subject, sitting)] for every sitting's page
    in the notepad (notepad/DATE-SLUG.md, the shape office start files,
    a day page notepad/DATE.md aside), by the commit that added it,
    oldest first. None when the office is not a git repo."""
    import subprocess
    root = pathlib.Path(root)
    proc = subprocess.run(["git", "-C", str(root), "log", "--diff-filter=A", "--format=C%x09%H%x09%cI%x09%s",
                           "--name-only", "--", "notepad"], capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        debug(f"no git log of the notepad in {root}: {proc.stderr.strip()}")
        return None
    out, commit = [], None
    for line in proc.stdout.splitlines():
        if line.startswith("C\t"):
            _, sha, when, subject = line.split("\t", 3)
            commit = (dt.datetime.fromisoformat(when), sha, subject)
            continue
        if line.strip() and commit and oh.SITTING_PAGE_RE.match(line.strip()):
            out.append((commit[0], line.strip(), commit[1], commit[2]))
    # Keyed once every page is known, so a later page joins its first
    # whichever commit filed which.
    stems = {pathlib.PurePosixPath(f[1]).stem for f in out}
    out = [(*f, sitting_key(f[1], stems)) for f in out]
    out.sort(key=lambda f: (f[0], f[1]))
    return out


def sittings_after(filings, day, tz):
    """How many sittings filed a page after the day (the office's), each
    sitting counted once however many pages it filed."""
    return len({f[4] for f in filings or [] if f[0].astimezone(tz).date().isoformat() > day})


def zone(name):
    import zoneinfo
    try:
        return zoneinfo.ZoneInfo(name)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        log(f"warning: the timezone {name!r} does not resolve; the watches read days in UTC")
        return dt.timezone.utc


# --- where bale's records are read -------------------------------------------------------

def places(root):
    """[(label, project dict)]: the office's own registry first (when bale
    keeps one there), then each project the office scopes; a project
    that cannot be read is still listed, and says why when read."""
    import office_bale as ob
    out = []
    own = ob.office_registry(root)
    if own is not None:
        out.append((ob.OFFICE_LABEL, {"problem": None, "resolved": own}))
    for p in ob.office_projects(root) or []:
        out.append((p["name"], p))
    return out


# --- measuring ----------------------------------------------------------------------------

def numbers(values):
    return sum(v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool))


def flat_ids(rd, agg, path):
    out = set()
    for v in rd.reach(agg, "stats", path):
        if isinstance(v, list):
            out.update(x for x in v if isinstance(x, str))
    return sorted(out)


def measure(rd, q, agg):
    """{value, shown, evidence} of a share, sum or count query over one
    aggregate line. value is None when there is nothing to measure."""
    kind = q["value"]
    if kind == "share":
        num = numbers(rd.reach(agg, "stats", q["numerator"]))
        den = numbers(rd.reach(agg, "stats", q["denominator"]))
        value = num / den if den else None
        shown = f"{value:.2f} ({num:g} of {den:g})" if den else f"nothing to measure (0 of {den:g})"
    elif kind == "sum":
        value = numbers(rd.reach(agg, "stats", q["key"]))
        shown = f"{value:g}"
    elif kind == "count":
        items = flat_ids(rd, agg, q["key"])
        value = len(items)
        shown = f"{value}"
    else:
        raise oh.HelperError(f"a {kind} query is standing; measure() reads share, sum and count")
    evidence = flat_ids(rd, agg, q["evidence"]) if q.get("evidence") else []
    return {"value": value, "shown": shown, "evidence": evidence}


def crosses(value, limit, compare):
    if value is None:
        return False
    if limit == "any":
        return value > 0
    return value > limit if compare == "above" else value >= limit


def observe(rd, q, agg):
    """A standing query's words over one aggregate: per work class."""
    import office_bale as ob
    classes = rd.reach(agg, "stats", CLASSES)[0] or {}
    if not classes:
        return "no classed sessions in bale's records"
    parts = []
    for name in sorted(classes):
        row = classes[name]
        if q["value"] == "class-rate":
            num = numbers(rd.reach(row, "stats", q["numerator"], at=CLASS_ROW))
            den = numbers(rd.reach(row, "stats", q["denominator"], at=CLASS_ROW))
            parts.append(f"{name} {ob.rate(int(num), int(den))}")
        else:
            bases = rd.reach(row, "stats", q["key"], at=CLASS_ROW)[0] or {}
            words = []
            for basis in sorted(bases):
                at = q["key"] + ".*"
                checks = numbers(rd.reach(bases[basis], "stats", q["checks"], at=at))
                agree = numbers(rd.reach(bases[basis], "stats", q["agree"], at=at))
                words.append(f"{basis} {int(agree)} of {int(checks)} agree")
            parts.append(f"{name}: " + (", ".join(words) if words else "no checks"))
    return "; ".join(parts)


def observe_any(rd, q, agg):
    if q["value"] in STANDING_KINDS:
        return observe(rd, q, agg)
    return measure(rd, q, agg)["shown"]


# --- the check ----------------------------------------------------------------------------

def check(rd, root, tz_name, catalog=None, filings=None):
    """Every line office watches check prints, and what --record would
    append. Returns a dict: lines (watch lines, then standing lines),
    watch_lines, standing_lines, fired ({number: [(label, words)]}),
    problems (records that do not read), bad (places not read), page
    (whether watches.md exists), eyes ({number: sittings since})."""
    import office_bale as ob
    root = pathlib.Path(root)
    tz = zone(tz_name)
    catalog = catalog or Catalog()
    reg_lines = od.read_lines(root / REGISTER)
    have_page = (root / REGISTER).is_file()
    entries, problems = register(reg_lines)
    evs, log_problems = events(od.read_lines(root / LOG))
    problems += log_problems
    known = {e["number"] for e in entries}
    problems += [f"{LOG}:{e[4]}: W{e[1]} is on no entry in {REGISTER}" for e in evs if e[1] not in known]
    where = places(root)
    if filings is None:
        filings = sitting_filings(root)
    watch_lines, standing_lines, fired, bad, eyes = [], [], {}, set(), {}
    observed_by_entry = set()

    def aggregate(label, p, since=None):
        cwd = ob.readable(p)
        return rd.aggregate(cwd, since=since)

    for entry in sorted(entries, key=lambda e: e["number"]):
        n, title = entry["number"], entry["title"]
        st = state_of(n, evs)
        if st["closed"]:
            continue
        how, name = evaluates(entry)
        head = f"W{n} {title}"
        if how is None:
            watch_lines.append(f"{head}: cannot evaluate: {name}")
            continue
        if how == "eye":
            last = st["last"]
            if last is None:
                watch_lines.append(f"{head}: needs an eye: no record of it in the log yet")
                continue
            count = sittings_after(filings, last[0], tz)
            eyes[n] = count
            flag = (f"; unlooked-at for {count} sittings, so the digest flags it" if count >= EYE_SITTINGS else "")
            watch_lines.append(f"{head}: needs an eye: {count} sitting(s) since its last record, "
                               f"{last[0]} {last[2]}{flag}")
            continue
        q = catalog.get(name)
        head = f"W{n} {name}"
        if q is None:
            watch_lines.append(f"{head}: cannot evaluate: share/watch-queries.toml holds no query {name}")
            continue
        if "needs" in q:
            watch_lines.append(f"{head}: cannot evaluate: bale does not stamp {q['needs']} (slip)")
            continue
        if standing_entry(entry) or q.get("standing"):
            # Observed, never fired: a watch kept for its record, or a
            # query that is itself an observation. The catalog's own
            # standing line for the same query is then not printed twice.
            observed_by_entry.add(name)
            for label, p in where:
                try:
                    words = observe_any(rd, q, aggregate(label, p))
                    standing_lines.append(f"W{n} {name} in {label}: observed: {words}")
                except ob.BaleError as exc:
                    bad.add(label)
                    standing_lines.append(f"W{n} {name} in {label}: cannot evaluate: {exc}")
            continue
        limit, why = threshold(entry)
        if limit is None:
            watch_lines.append(f"{head}: cannot evaluate: {why}")
            continue
        since, span = window(st)
        shown_limit = "any" if limit == "any" else f"{limit:g}"
        if not where:
            watch_lines.append(f"{head}: cannot evaluate: this office reads no bale registry: bale keeps none "
                               "in it, and it scopes no projects")
            continue
        for label, p in where:
            try:
                m = measure(rd, q, aggregate(label, p, since))
            except ob.BaleError as exc:
                bad.add(label)
                watch_lines.append(f"{head} in {label}: cannot evaluate: {exc}")
                continue
            hit = crosses(m["value"], limit, q["compare"])
            verdict = "fired" if hit else "not fired"
            watch_lines.append(f"{head} in {label}: {verdict}: {m['shown']} {span}; threshold {shown_limit}")
            if hit:
                words = (", ".join(m["evidence"]) if m["evidence"] else m["shown"])
                fired.setdefault(n, []).append((label, f"{words} ({q['says']}: {m['shown']}, {span})"))
    for name, q in catalog.standing():
        if name in observed_by_entry:
            continue
        for label, p in where:
            try:
                standing_lines.append(f"{name} in {label}: observed: {observe(rd, q, aggregate(label, p))}")
            except ob.BaleError as exc:
                bad.add(label)
                standing_lines.append(f"{name} in {label}: cannot evaluate: {exc}")
    if not where:
        standing_lines.append("the standing lines read nothing: this office reads no bale registry (bale keeps "
                              "none in it, and it scopes no projects)")
    lines = []
    if not have_page:
        lines.append(f"no watches register in this office yet: only a sitting writes watches, on {REGISTER}")
    elif not entries:
        lines.append(f"{REGISTER} holds no watch yet")
    lines += watch_lines + standing_lines + [f"does not read: {p}" for p in problems]
    return {"lines": lines, "watch_lines": watch_lines, "standing_lines": standing_lines, "fired": fired,
            "problems": problems, "bad": sorted(bad), "page": have_page, "eyes": eyes}


def fired_lines(result):
    """The watch lines of a check whose verdict is fired, as printed."""
    return [l for l in result["watch_lines"] if ": fired: " in l]


def fired_records(day, fired):
    """The `fired` records --record appends, one per watch, ASCII."""
    out = []
    for n in sorted(fired):
        parts = "; ".join(f"{label}: {words}" for label, words in fired[n])
        line = f"- {day} W{n} fired: {parts}; recorded by office watches check --record"
        out.append(oh.ascii_escape(line)[0])
    return out


def record(root, day, fired):
    """Append the fired records to watch-log.md, made from its template on
    its first write (and the drafting table with it, if it has not
    arrived). Returns (changed paths, words)."""
    dt.date.fromisoformat(day)
    lines = fired_records(day, fired)
    if not lines:
        return [], ["no watch fired, so nothing was recorded"]
    changed, words = od.arrive(root, ["watch-log.md"])
    page = pathlib.Path(root) / LOG
    body = page.read_text(encoding="utf-8")
    if not body.endswith("\n"):
        body += "\n"
    last = body.rstrip("\n").splitlines()[-1] if body.strip() else ""
    joint = "" if LOG_RE.match(last) else "\n"
    page.write_text(body + joint + "\n".join(lines) + "\n", encoding="utf-8")
    words.append(f"{len(lines)} fired record(s) appended to {LOG}")
    return sorted(set(changed + [LOG])), words


# --- office watches: the register, read --------------------------------------------------

def render_watches(root, show_all=False, catalog=None):
    """(lines, problems): the watches, open ones unless show_all."""
    root = pathlib.Path(root)
    if not (root / REGISTER).is_file():
        return [f"no watches register in this office yet: only a sitting writes watches, on {REGISTER}"], []
    catalog = catalog or Catalog()
    entries, problems = register(od.read_lines(root / REGISTER))
    evs, log_problems = events(od.read_lines(root / LOG))
    problems += log_problems
    closed = [e for e in entries if state_of(e["number"], evs)["closed"]]
    shown = entries if show_all else [e for e in entries if e not in closed]
    out = [f"Watches: {len(entries) - len(closed)} open, {len(closed)} closed"
           + ("" if show_all or not closed else " (office watches --all lists the closed ones too)")]
    if not entries:
        out.append(f"  {REGISTER} holds no watch yet")
    for e in sorted(shown, key=lambda x: x["number"]):
        st = state_of(e["number"], evs)
        how, name = evaluates(e)
        if how == "query":
            q = catalog.get(name)
            what = f"query {name}" + (" (not in the catalog)" if q is None else
                                      f" (bale does not stamp {q['needs']} yet)" if "needs" in q else "")
            what += f", threshold {e['fields'].get('threshold', 'none given')}"
            if standing_entry(e):
                what += ", no re-trigger: a standing line"
        elif how == "eye":
            what = "eye"
        else:
            what = f"does not read: {name}"
        last = st["last"]
        state = "closed" if st["closed"] else "open"
        out.append(f"  W{e['number']}  {e['title']}  [{state}]")
        out.append(f"      evaluates {what}; scope {e['fields'].get('scope', 'not given')}; "
                   f"source {e['fields'].get('source', 'not given')}")
        out.append(f"      last record: " + (f"{last[0]} {last[2]}" + (f": {last[3]}" if last[3] else "")
                                             if last else "none in the log"))
    out += [f"  does not read: {p}" for p in problems]
    return out, problems


# --- the command line ------------------------------------------------------------------

def main(argv=None):
    import office_bale as ob
    ap = argparse.ArgumentParser(prog="office_watches.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("list"); p.add_argument("root"); p.add_argument("--all", action="store_true")
    p = sub.add_parser("check"); p.add_argument("root"); p.add_argument("--day", required=True)
    p.add_argument("--tz", required=True, help="the office's timezone, for the days of sittings")
    p.add_argument("--record", action="store_true", help="append a fired record per watch that fired")
    p.add_argument("--changed", help="with --record: write the paths changed here, one per line")
    p.add_argument("--fired-only", action="store_true",
                   help="print only the lines of the watches that fired (office land's after-build run); "
                        "nothing for an office with no watches register")
    p = sub.add_parser("catalog-check")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "list":
            lines, problems = render_watches(a.root, a.all)
            print("\n".join(lines))
            return 3 if problems else 0
        if a.cmd == "catalog-check":
            cat = Catalog()
            print(f"share/watch-queries.toml: {len(cat.queries)} queries, every key declared")
            return 0
        dt.date.fromisoformat(a.day)
        if a.fired_only and a.record:
            log("error: --fired-only prints and --record records; office land runs the one, a person the other")
            return 2
        if a.fired_only and not (pathlib.Path(a.root) / REGISTER).is_file():
            return 0
        result = check(ob.Reader(), a.root, a.tz)
        if a.fired_only:
            for line in fired_lines(result):
                print(line)
            return 3 if result["bad"] or result["problems"] else 0
        print("\n".join(result["lines"]))
        if a.record:
            changed, words = record(a.root, a.day, result["fired"])
            for w in words:
                log(w)
            if a.changed:
                pathlib.Path(a.changed).write_text("".join(c + "\n" for c in changed), encoding="utf-8")
        return 3 if result["bad"] or result["problems"] else 0
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, ValueError, UnicodeDecodeError) as exc:  # a TOMLDecodeError is a ValueError
        log(f"error: {exc.__class__.__name__}: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
