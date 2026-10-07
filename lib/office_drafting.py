#!/usr/bin/env python3
"""The drafting table: its pages arriving in an office, the records on them,
and the one reader every verb that reads them shares.

The space is drafting-table/ in an office (doctrine section 5; the
drafting-table blueprint's sections 1 and 2): blueprints, one arc each,
and the pages around them: the agenda, the rulings and evidence ledgers,
the watches register and its log, the riders page and the desk moves.
Nothing here is base: a drafting table arrives in an office when the first
verb that writes it runs, never by a migration and never by hand. Arrival
makes drafting-table/README.md from the install's template, adds the
space to the floor plan as the install's catalog declares it (so office
status and office upgrade read its filed list), adds it to bale.toml's
include-group triggers, and makes each page from its template on the
page's first write. Nothing already there is ever rewritten.

Every parser here skips fenced code blocks: the pages carry illustrative
records inside ``` fences, and an example is never a record.

The citation grammar (the blueprint's section 1.7) has one resolver,
Table.resolve, used by the desk's gates, office rulings --check and
office evidence. MASTER.md's own citation forms (`row N`, `board N`,
`section 5, this date`, `section 6 entry N`) survive only inside filed
MASTER.md content, which no office holds yet; MASTER_FORMS names them and
nothing resolves them until such content exists (the seam is
Table.resolve_master, which says so).

Standard library only. The command line prints on stdout, logs to stderr
with an [office] prefix, and exits 0 on success, 1 on a refusal, 2 on an
internal error, and 3 when a check found problems (the lines say which).
"""

import argparse
import datetime as dt
import fnmatch
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import tomllib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
CATALOG = INSTALL / "share" / "spaces.toml"
TEMPLATES = INSTALL / "templates"
SPACE = "drafting-table"
BLUEPRINTS = f"{SPACE}/blueprints"
MANIFEST_REL = "floor-plan/manifest.toml"
BALE_TOML_REL = "bale.toml"

# Every page the space can hold, and the template it starts from. The
# digest is derived (office digest writes it whole on every run, from no
# template), and the blueprints have their own templates.
PAGES = {
    "README.md": "drafting-table-README.md",
    "agenda.md": "drafting-table-agenda.md",
    "rulings.md": "drafting-table-rulings.md",
    "evidence.md": "drafting-table-evidence.md",
    "watches.md": "drafting-table-watches.md",
    "watch-log.md": "drafting-table-watch-log.md",
    "riders.md": "drafting-table-riders.md",
    "moves.md": "drafting-table-moves.md",
}
DERIVED_PAGES = ("digest.md",)

# The template's placeholder for a charter nobody has written yet; a
# charter holding only this (and blank lines) is empty.
CHARTER_PLACEHOLDER = ("(not written yet: what the arc is for and what done means, in the asker's words "
                       "where there are words to keep)")

DASH = r"(?:-|—|–|·)"
ARROW = r"(?:->|→)"
DATE = r"\d{4}-\d{2}-\d{2}"
SID_TOKEN_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*-\d{3})\b")
ID_PART = r"\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*"

RIDER_HEAD_RE = re.compile(rf"^### rider (\d+)\s*{DASH}\s*(.+?)\s*$")
POINTER_RE = re.compile(rf"^- rider (\d+)\s*{ARROW}\s*folder (\d+)\s*$")
RIDER_STATUSES = ("queued", "carried", "consumed", "moot", "stands")
RIDER_STATE_RE = re.compile(rf"^- ({DATE}) (queued|carried|consumed|moot|stands):(?: (.*))?$")
FIELD_RE = re.compile(r"^- ([a-z][a-z -]*?): (.*)$")

AGENDA_HEAD_RE = re.compile(rf"^## agenda (\d+)\s*{DASH}\s*(.+?)\s*$")
DISPOSED_RE = re.compile(rf"^- ({DATE}) agenda (\d+)\s*{ARROW}\s*(.+?)\s*$")

RULING_HEAD_RE = re.compile(rf"^## ({ID_PART})(?:\s+{DASH}\s+(derived)\s+{DASH}\s+({DATE}))?\s*$")
ENTRY_HEAD_RE = re.compile(r"^## (\d+)\.\s+(.+?)\s*$")
EVENT_HEAD_RE = re.compile(rf"^## (\d+)\s*{DASH}\s*(occurrence|derived)\s*{DASH}\s*({DATE})\s*$")
ATTRIBUTIONS = ("planner", "worker", "operator", "courier")
WATCH_HEAD_RE = re.compile(rf"^## W(\d+)\s*{DASH}\s*(.+?)\s*$")

RATIFIED_LINE_RE = re.compile(rf"^- ratified: ({DATE})(?:, (.*))?$")
DECOMP_RE = re.compile(rf"^- (.+?)(?:\s+{ARROW}\s+(.+?))?\s*$")
DECOMP_FOLDER_RE = re.compile(r"^folder (\d+)$")

MOVE_RE = re.compile(rf"^- \[( |x|X)\] ({DATE}) (.*?)\s*$")
MOVE_DONE_RE = re.compile(rf"\s+{ARROW}\s+folder (\d+)\s*$")

# MASTER.md's own forms: they survive in filed MASTER.md content and
# nowhere new (the blueprint's section 1.7). Named here so the seam is
# visible; Table.resolve_master is where their mapping goes the day an
# office files MASTER.md content, and nothing calls it before then.
MASTER_FORMS = (
    ("row", re.compile(r"\brow (\d+)\b")),
    ("board", re.compile(r"\bboard (\d+)\b")),
    ("section 5, this date", re.compile(r"(?:§|section )5, (\d{4}-\d{2}-\d{2})")),
    ("section 6 entry", re.compile(r"(?:§|section )6 entry (\d+)")),
)


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


# --- reading pages -----------------------------------------------------------------

def unfenced(lines, start=0, end=None):
    """(index, line) for each line outside ``` fences, between start and
    end. A fence's own lines are never yielded."""
    fence = False
    end = len(lines) if end is None else end
    for i in range(start, end):
        line = lines[i]
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if not fence:
            yield i, line


def read_lines(path):
    """The page's lines, or [] when it does not exist."""
    p = pathlib.Path(path)
    if not p.is_file():
        return []
    return p.read_text(encoding="utf-8").splitlines()


def write_lines(path, lines):
    pathlib.Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def fields_of(lines, start, end):
    """The `- key: value` lines at the head of a record (blank lines
    allowed among them), as key -> [values], and the index where the
    record's prose begins."""
    out, i = {}, start
    while i < end:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = FIELD_RE.match(line)
        if not m:
            break
        out.setdefault(m.group(1), []).append(m.group(2).strip())
        i += 1
    return out, i


def first(fields, key):
    return (fields.get(key) or [None])[0]


def clean_title(text):
    """A title from words as typed: the first non-blank line, a leading
    list marker (`1.`, `2)`, `-`, `*`, `+`) and emphasis markers (`**`,
    `__`, `*`) taken out, whitespace collapsed. The words themselves are
    never changed this way; only a title or a slug is made from them."""
    line = next((l for l in str(text).splitlines() if l.strip()), "")
    line = re.sub(r"^\s*(?:\d+[.)]|[-*+])\s+", "", line)
    line = line.replace("**", "").replace("__", "")
    line = re.sub(r"(?<!\w)\*|\*(?!\w)", "", line)
    return " ".join(line.split())


# --- arrival -----------------------------------------------------------------------

def catalog_entry(catalog=CATALOG):
    spaces = oh.read_toml(catalog).get("spaces", {})
    if SPACE not in spaces:
        raise oh.HelperError(f"the install's catalog ({catalog}) declares no {SPACE} space")
    return spaces[SPACE]


def floor_plan_block(entry):
    return [f"[spaces.{SPACE}]", f'path = "{entry["path"]}"',
            f"hung = {oh.render_flag_or_list(entry.get('hung', False))}",
            f"filed = {oh.render_flag_or_list(entry.get('filed', False))}"]


def add_space_to_floor_plan(manifest, entry):
    """Add [spaces.drafting-table] to the floor plan after its last space,
    every other byte kept. Returns False when the floor plan already has
    it. The result is parsed back: everything the floor plan said before
    must read the same, and the new table must read as the catalog's."""
    path = pathlib.Path(manifest)
    text = path.read_text(encoding="ascii")
    before = tomllib.loads(text)
    if SPACE in before.get("spaces", {}):
        return False
    lines = text.splitlines()
    heads = [i for i, l in enumerate(lines) if re.match(r"^\[spaces\.[^\]]+\]\s*$", l)]
    if heads:
        at = next((i for i in range(heads[-1] + 1, len(lines)) if lines[i].startswith("[")), len(lines))
        # Comments and blank lines just above the next table belong to it.
        while at > heads[-1] + 1 and (not lines[at - 1].strip() or lines[at - 1].startswith("#")):
            at -= 1
    else:
        at = len(lines)
    new = lines[:at] + [""] + floor_plan_block(entry) + lines[at:]
    new_text = "\n".join(new) + "\n"
    after = tomllib.loads(new_text)
    added = after.get("spaces", {}).pop(SPACE, None)
    if after != before or added != {"path": entry["path"], "hung": entry.get("hung", False),
                                     "filed": entry.get("filed", False)}:
        raise oh.HelperError(f"adding the {SPACE} space to {path} would change what else it says; nothing written")
    path.write_text(new_text, encoding="ascii")
    return True


def add_include_trigger(bale_toml, trigger):
    """Add a trigger to bale.toml's include group, every other byte kept.
    Returns True when added, False when already there, None when there is
    no include group to add it to (office status reports that)."""
    path = pathlib.Path(bale_toml)
    if not path.is_file():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("include_group_triggers = "):
            try:
                have = tomllib.loads(line)["include_group_triggers"]
            except (tomllib.TOMLDecodeError, KeyError):
                return None
            if trigger in have:
                return False
            lines[i] = f"include_group_triggers = {oh.toml_list(sorted(have + [trigger]))}"
            write_lines(path, lines)
            return True
    return None


def render_page(name):
    return (TEMPLATES / PAGES[name]).read_text(encoding="utf-8")


def arrive(root, pages=()):
    """Make the drafting table arrive, or finish arriving: README.md, the
    floor plan's entry, bale.toml's trigger, and each named page that does
    not exist yet. Returns (changed paths, words for the log). Nothing that
    exists is rewritten; a page already there is left as it is."""
    root = pathlib.Path(root)
    entry = catalog_entry()
    changed, words = [], []
    (root / SPACE).mkdir(exist_ok=True)
    for name in ("README.md", *pages):
        if name not in PAGES:
            raise oh.HelperError(f"{SPACE}/{name} is not a page the drafting table holds")
        p = root / SPACE / name
        if not p.exists():
            p.write_text(render_page(name), encoding="utf-8")
            changed.append(f"{SPACE}/{name}")
            words.append(f"made {SPACE}/{name} from the install's template")
    if add_space_to_floor_plan(root / MANIFEST_REL, entry):
        changed.append(MANIFEST_REL)
        words.append(f"the floor plan now lists the {SPACE} space, filed as the catalog says: "
                     + ", ".join(entry.get("filed", [])))
    added = add_include_trigger(root / BALE_TOML_REL, entry["path"])
    if added:
        changed.append(BALE_TOML_REL)
        words.append(f"bale.toml's include group now triggers on {entry['path']}")
    elif added is None:
        words.append(f"bale.toml has no include group to add {entry['path']} to (office status says so)")
    if changed and "README.md" in [c.rsplit("/", 1)[-1] for c in changed]:
        words.insert(0, f"the drafting table arrives in this office: {SPACE}/")
    return changed, words


def table_check(root):
    """(lines, problems) for office status: a drafting table that exists,
    against the install's catalog; none, said so."""
    root = pathlib.Path(root)
    entry = catalog_entry()
    manifest = oh.read_toml(root / MANIFEST_REL)
    listed = manifest.get("spaces", {}).get(SPACE)
    here = (root / SPACE).is_dir()
    if not here and listed is None:
        return ["drafting:   none in this office; it arrives with the first verb that writes it "
                "(office blueprint open, rider add, agenda add)"], 0
    problems = []
    if here and listed is None:
        problems.append(f"{SPACE}/ exists but the floor plan does not list it, so its filed pages go "
                        "unchecked; any verb that writes the drafting table adds it")
    if listed is not None:
        for key in ("path", "hung", "filed"):
            want = entry.get(key, False)
            if listed.get(key, False) != want:
                problems.append(f"the floor plan's {SPACE} {key} is {listed.get(key)!r}; the install's catalog "
                                f"says {want!r}")
        if not here:
            problems.append(f"the floor plan lists {SPACE} but there is no {SPACE}/ directory")
    if here and not (root / SPACE / "README.md").is_file():
        problems.append(f"{SPACE}/README.md is missing; any verb that writes the drafting table makes it")
    if here:
        for p in sorted((root / SPACE).iterdir()):
            if p.is_file() and p.name not in PAGES and p.name not in DERIVED_PAGES:
                problems.append(f"{SPACE}/{p.name} is not a page the drafting table holds")
            elif p.is_dir() and p.name != "blueprints":
                problems.append(f"{SPACE}/{p.name}/ is not a part of the drafting table")
    if problems:
        return [f"drafting:   {len(problems)} problem(s) against the install's catalog:"] + \
            [f"  {p}" for p in problems], len(problems)
    t = Table(root)
    return [f"drafting:   matches the install's catalog; {len(t.blueprints())} blueprint(s), "
            f"{len(t.riders())} rider(s), {len(t.agenda()[0])} agenda item(s) open"], 0


# --- the table: every record, read once ---------------------------------------------

class Table:
    """The drafting table and the desk, read lazily, once. Every reader of
    a record goes through here, so the desk, the checks and the listings
    agree on what a record is."""

    def __init__(self, root):
        self.root = pathlib.Path(root)
        self._cache = {}

    def page(self, name):
        if name not in self._cache:
            self._cache[name] = read_lines(self.root / SPACE / name)
        return self._cache[name]

    def folders(self):
        if "folders" not in self._cache:
            self._cache["folders"] = oh.read_folders(self.root)
        return self._cache["folders"]

    def by_number(self):
        return oh.folders_by_number(self.folders())

    # --- blueprints

    def blueprints(self):
        if "blueprints" not in self._cache:
            out = {}
            base = self.root / BLUEPRINTS
            if base.is_dir():
                for d in sorted(p for p in base.iterdir() if p.is_dir()):
                    out[d.name] = blueprint_facts(d)
            self._cache["blueprints"] = out
        return self._cache["blueprints"]

    # --- agenda

    def agenda(self):
        """({N: entry}, {N: disposed line}) from agenda.md."""
        if "agenda" not in self._cache:
            self._cache["agenda"] = agenda_records(self.page("agenda.md"))
        return self._cache["agenda"]

    # --- rulings

    def rulings(self):
        """[record] from rulings.md, in page order. A record is a ruling,
        an amendment (`amends: ID`) or a derivation (`## ID - derived -
        DATE`)."""
        if "rulings" not in self._cache:
            self._cache["rulings"] = records(self.page("rulings.md"), RULING_HEAD_RE, self._ruling)
        return self._cache["rulings"]

    @staticmethod
    def _ruling(m, fields, text, line):
        kind = "derived" if m.group(2) else ("amendment" if fields.get("amends") else "ruling")
        return {"id": m.group(1), "kind": kind, "day": m.group(3) or first(fields, "ruled"), "fields": fields,
                "text": text, "line": line}

    def ruling_ids(self):
        return {r["id"] for r in self.rulings() if r["kind"] != "derived"}

    # --- evidence

    def evidence(self):
        """[record] from evidence.md: entries (`## N. Title`) and events
        (`## N - occurrence - DATE`, `## N - derived - DATE`)."""
        if "evidence" not in self._cache:
            self._cache["evidence"] = evidence_records(self.page("evidence.md"))
        return self._cache["evidence"]

    def watches(self):
        if "watches" not in self._cache:
            self._cache["watches"] = {int(m.group(1)) for _, l in unfenced(self.page("watches.md"))
                                      for m in [WATCH_HEAD_RE.match(l)] if m}
        return self._cache["watches"]

    # --- riders

    def riders(self):
        """Every rider block, on the page and in every folder's Riders
        section: dicts with number, title, fields, states, status, home
        ("page" or a folder's rel), folder (the folder dict) and the
        block's span in its file."""
        if "riders" not in self._cache:
            out = []
            lines = self.page("riders.md")
            out += [dict(r, home="page", folder=None) for r in rider_blocks(lines, 0, len(lines))]
            for f in self.folders():
                if f["problem"]:
                    continue
                flines = f["path"].read_text(encoding="utf-8").splitlines()
                s, e = oh.section_bounds(flines, "Riders")
                if s is None:
                    continue
                out += [dict(r, home=f["rel"], folder=f) for r in rider_blocks(flines, s + 1, e)]
            self._cache["riders"] = out
        return self._cache["riders"]

    def pointers(self):
        """{rider N: folder M} from the page's pointer lines."""
        return {int(m.group(1)): int(m.group(2)) for _, l in unfenced(self.page("riders.md"))
                for m in [POINTER_RE.match(l)] if m}

    def next_rider(self):
        numbers = [r["number"] for r in self.riders()] + list(self.pointers())
        return max(numbers, default=0) + 1

    def orphans(self):
        """Riders in a folder that has gone to the filing cabinet without
        their being consumed (or ruled moot, or left standing)."""
        return [r for r in self.riders() if r["folder"] is not None and r["folder"]["space"] == "filing-cabinet"
                and r["status"] not in ("consumed", "moot", "stands")]

    # --- the citation grammar

    def resolve(self, kind, ref):
        """(state, words) for one citation: state is ok or missing."""
        if kind == "folder":
            same = self.by_number().get(int(ref), [])
            if len(same) == 1:
                return "ok", same[0]["rel"]
            return "missing", (f"folder {ref} is minted twice" if same else f"no folder {ref} on the desk or in the "
                                                                               "filing cabinet")
        if kind == "blueprint":
            return ("ok", f"{BLUEPRINTS}/{ref}") if ref in self.blueprints() else \
                ("missing", f"no blueprint {ref} on the drafting table")
        if kind == "ruling":
            return ("ok", "rulings.md") if ref in self.ruling_ids() else ("missing", f"no ruling {ref} in rulings.md")
        if kind == "evidence":
            return ("ok", "evidence.md") if any(r["kind"] == "entry" and r["number"] == int(ref)
                                                for r in self.evidence()) else \
                ("missing", f"no evidence {ref} in evidence.md")
        if kind == "watch":
            return ("ok", "watches.md") if int(ref) in self.watches() else ("missing", f"no watch W{ref} in watches.md")
        if kind == "rider":
            n = int(ref)
            if any(r["number"] == n for r in self.riders()) or n in self.pointers():
                return "ok", "riders"
            return "missing", f"no rider {ref} on the riders page or in any folder"
        if kind == "agenda":
            entries, disposed = self.agenda()
            n = int(ref)
            return ("ok", "agenda.md") if n in entries or n in disposed else ("missing", f"no agenda {ref} in agenda.md")
        if kind == "notepad":
            return ("ok", ref) if (self.root / ref).is_file() else ("missing", f"no page {ref}")
        raise oh.HelperError(f"no citation kind {kind!r}")

    def resolve_master(self, form, ref):
        """MASTER.md's forms resolve only inside filed MASTER.md content,
        and no office holds any yet: the content-filing sessions bring it,
        and with it the mapping (row N to folder N, section 6 entry N to
        evidence N, ...). Until then nothing calls this."""
        raise oh.HelperError(f"MASTER.md's form {form!r} resolves only inside filed MASTER.md content, "
                             "which this office does not hold")

    def gate(self, gate):
        """Where a drafting-table gate stands, for the desk: (state, words,
        cleared day or None), state met, wait or error. `blueprint ID` is
        met when its close report exists; `agenda N` when a sitting
        disposed of it; `ruling ID` when the ruling's record exists."""
        kind, _, ref = gate.partition(" ")
        if kind == "blueprint":
            b = self.blueprints().get(ref)
            if b is None:
                return "error", f"{gate} names no blueprint on the drafting table", None
            if b["closed"]:
                return "met", f"{gate} closed", b["closed_day"]
            return "wait", f"{gate} (open{', ratified' if b['ratified'] else ', not ratified'}): {b['title']}", None
        if kind == "agenda":
            entries, disposed = self.agenda()
            n = int(ref)
            if n in disposed:
                return "met", f"{gate} ruled ({disposed[n]['to']})", disposed[n]["day"]
            if n in entries:
                return "wait", f"{gate} (awaiting a sitting): {entries[n]['title']}", None
            return "error", f"{gate} names nothing on the agenda", None
        if kind == "ruling":
            for r in self.rulings():
                if r["id"] == ref and r["kind"] != "derived":
                    return "met", f"{gate} ruled", r["day"]
            return "error", f"{gate} names no ruling in rulings.md", None
        raise oh.HelperError(f"not a drafting-table gate: {gate!r}")


def agenda_records(lines):
    """({N: entry}, {N: disposed line}) from agenda.md's lines."""
    entries, disposed = {}, {}
    heads = [(i, AGENDA_HEAD_RE.match(l)) for i, l in unfenced(lines) if l.startswith("## ")]
    for k, (i, m) in enumerate(heads):
        if not m:
            continue
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        fields, body = fields_of(lines, i + 1, end)
        entries[int(m.group(1))] = {"number": int(m.group(1)), "title": m.group(2), "fields": fields,
                                    "text": [l for l in lines[body:end]], "line": i + 1}
    for i, l in unfenced(lines):
        m = DISPOSED_RE.match(l)
        if m:
            disposed[int(m.group(2))] = {"day": m.group(1), "to": m.group(3), "line": i + 1}
    return entries, disposed


def evidence_records(lines):
    """[record] from evidence.md's lines: entries (`## N. Title`) and
    events (`## N - occurrence - DATE`, `## N - derived - DATE`)."""
    out = []
    heads = [i for i, l in unfenced(lines) if l.startswith("## ")]
    for k, i in enumerate(heads):
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        fields, body = fields_of(lines, i + 1, end)
        text = [l for l in lines[body:end]]
        m = ENTRY_HEAD_RE.match(lines[i])
        e = EVENT_HEAD_RE.match(lines[i])
        if m:
            out.append({"number": int(m.group(1)), "kind": "entry", "title": m.group(2), "fields": fields,
                        "text": text, "line": i + 1})
        elif e:
            out.append({"number": int(e.group(1)), "kind": e.group(2), "day": e.group(3), "fields": fields,
                        "text": text, "line": i + 1})
        else:
            out.append({"number": None, "kind": "unreadable", "heading": lines[i], "line": i + 1})
    return out


def rider_numbers(lines):
    """Every rider number riders.md's lines name: its blocks and its
    pointer lines (a rider carried into a folder leaves a pointer)."""
    return ({r["number"] for r in rider_blocks(lines, 0, len(lines))}
            | {int(m.group(1)) for _, l in unfenced(lines) for m in [POINTER_RE.match(l)] if m})


def records(lines, head_re, make):
    """Records on a ledger page: each `## ` heading outside fences that
    head_re reads opens one, which runs to the next `## ` heading."""
    out = []
    heads = [i for i, l in unfenced(lines) if l.startswith("## ")]
    for k, i in enumerate(heads):
        m = head_re.match(lines[i])
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        if not m:
            out.append({"id": None, "kind": "unreadable", "heading": lines[i], "line": i + 1})
            continue
        fields, body = fields_of(lines, i + 1, end)
        out.append(make(m, fields, lines[body:end], i + 1))
    return out


def rider_blocks(lines, start, end):
    """Rider blocks between start and end: from a `### rider N - title`
    heading to the next heading, pointer line or the end. A block's span
    leaves out its trailing blank lines."""
    out = []
    heads = []
    for i, l in unfenced(lines, start, end):
        if RIDER_HEAD_RE.match(l):
            heads.append(i)
    for i in heads:
        stop = next((j for j, l in unfenced(lines, i + 1, end)
                     if l.startswith("#") or POINTER_RE.match(l)), end)
        while stop > i + 1 and not lines[stop - 1].strip():
            stop -= 1
        m = RIDER_HEAD_RE.match(lines[i])
        fields, _ = fields_of(lines, i + 1, stop)
        states = [(mm.group(1), mm.group(2), (mm.group(3) or "").strip()) for l in lines[i + 1:stop]
                  for mm in [RIDER_STATE_RE.match(l)] if mm]
        status = states[-1][1] if states else first(fields, "status")
        out.append({"number": int(m.group(1)), "title": m.group(2), "fields": fields, "states": states,
                    "status": status, "start": i, "end": stop})
    return out


def blueprint_facts(d):
    """What the desk and the verbs read of one blueprint directory."""
    md = d / "blueprint.md"
    facts = {"id": d.name, "dir": d, "title": d.name, "ratified": None, "closed": (d / "close.md").is_file(),
             "closed_day": None, "decomposition": [], "problem": None, "charter": []}
    if not md.is_file():
        facts["problem"] = "no blueprint.md"
        return facts
    lines = md.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].startswith("# "):
        facts["title"] = lines[0][2:].strip()
    s, e = oh.section_bounds(lines, "Charter")
    if s is not None:
        facts["charter"] = lines[s + 1:e]
        for l in lines[s + 1:e]:
            m = RATIFIED_LINE_RE.match(l)
            if m:
                facts["ratified"] = (m.group(1), m.group(2) or "")
    facts["decomposition"] = decomposition(lines)
    if facts["closed"]:
        for l in (d / "close.md").read_text(encoding="utf-8").splitlines():
            m = re.match(rf"^- blueprint: \S+, closed ({DATE})\b", l)
            if m:
                facts["closed_day"] = m.group(1)
                break
    return facts


def decomposition(lines):
    """The Decomposition section's lines, outside fences: dicts with
    index (in the file), n (1-based, the line's number in the section),
    goal, and folder (an int) when the line names its folder."""
    s, e = oh.section_bounds(lines, "Decomposition")
    out = []
    if s is None:
        return out
    for i, l in unfenced(lines, s + 1, e):
        if not l.startswith("- "):
            continue
        m = DECOMP_RE.match(l)
        tail = (m.group(2) or "").strip()
        fm = DECOMP_FOLDER_RE.match(tail)
        out.append({"index": i, "n": len(out) + 1, "goal": m.group(1).strip(), "tail": tail,
                    "folder": int(fm.group(1)) if fm else None})
    return out


def charter_is_empty(charter_lines):
    words = [l.strip() for l in charter_lines
             if l.strip() and not RATIFIED_LINE_RE.match(l) and l.strip() != CHARTER_PLACEHOLDER]
    return not words


# --- riders: add, carry, consumed, list ------------------------------------------------

def rider_block_lines(n, title, source, rides, text, day, status="queued"):
    lines = [f"### rider {n} - {title}", "", f"- source: {source}"]
    if rides:
        lines.append(f"- rides: {rides}")
    lines += [f"- status: {status}", ""]
    if text and text.strip():
        lines += text.rstrip("\n").splitlines() + [""]
    lines.append(f"- {day} queued: office rider add")
    return lines


def normalize_rides(rides=None, carrier=None):
    if rides and carrier:
        raise oh.HelperError("a rider rides a path glob (--rides) or a named folder (--carrier), not both")
    if carrier:
        return oh.normalize_field("linked", carrier)
    if rides:
        text = " ".join(rides.split())
        owner, glob = rides_parts(text)
        if " " in glob:
            raise oh.HelperError(f"--rides takes one path glob, as git reads one (its project first, as a lane "
                                 f"names it, if only that project's packs carry it), not {rides!r}")
        return f"{owner}: {glob}" if owner else glob
    return None


def rider_add(root, day, title, source, rides=None, carrier=None, text=""):
    """Append rider N to the riders page; returns (N, changed paths,
    words). The page is made from its template on its first write."""
    dt.date.fromisoformat(day)
    title = oh.one_line(clean_title(title or text) or title, "the title")
    if len(title) > 72:
        title = title[:69] + "..."
    source = oh.one_line(source, "--source")
    where = normalize_rides(rides, carrier)
    changed, words = arrive(root, ["riders.md"])
    t = Table(root)
    n = t.next_rider()
    page = pathlib.Path(root) / SPACE / "riders.md"
    body = page.read_text(encoding="utf-8")
    if not body.endswith("\n"):
        body += "\n"
    text = oh.ascii_escape(text)[0] if text else ""
    block = rider_block_lines(n, oh.ascii_escape(title)[0], oh.ascii_escape(source)[0], where, text, day)
    page.write_text(body + "\n" + "\n".join(block) + "\n", encoding="utf-8")
    rel = f"{SPACE}/riders.md"
    return n, sorted(set(changed + [rel])), words


def find_rider(t, n):
    found = [r for r in t.riders() if r["number"] == n]
    if not found:
        if n in t.pointers():
            raise oh.HelperError(f"rider {n} points at folder {t.pointers()[n]}, but no folder holds its text")
        raise oh.HelperError(f"no rider {n} on the riders page or in any folder")
    if len(found) > 1:
        raise oh.HelperError(f"rider {n} has {len(found)} homes ("
                             + ", ".join("the riders page" if r["home"] == "page" else r["home"] for r in found)
                             + "); a rider lives in one place, so nothing was written")
    return found[0]


def set_status_line(lines, start, end, status):
    for i in range(start, end):
        m = FIELD_RE.match(lines[i])
        if m and m.group(1) == "status":
            lines[i] = f"- status: {status}"
            return True
    return False


def rider_carry(root, n, folder_ref, day):
    """Move rider N from the page into a desk folder's Riders section,
    leaving one pointer line on the page; returns (changed paths, words)."""
    dt.date.fromisoformat(day)
    t = Table(root)
    r = find_rider(t, n)
    if r["home"] != "page":
        raise oh.HelperError(f"rider {n} is already in {r['home']}; a rider is carried once, from the riders page")
    ok, rel = t.resolve("folder", int(oh.normalize_field("linked", folder_ref).split()[1]))
    if ok != "ok":
        raise oh.HelperError(rel)
    if not rel.startswith("desk/"):
        raise oh.HelperError(f"{rel} is in the filing cabinet; a rider is carried by a folder on the desk")
    number = int(oh.normalize_field("linked", folder_ref).split()[1])
    md = pathlib.Path(root) / rel / "folder.md"
    flines = md.read_text(encoding="utf-8").splitlines()
    if oh.section_bounds(flines, "Riders")[0] is None:
        raise oh.HelperError(f"{rel}/folder.md has no Riders section (a folder from before 0.3.0); nothing was written")
    page = pathlib.Path(root) / SPACE / "riders.md"
    plines = page.read_text(encoding="utf-8").splitlines()
    block = plines[r["start"]:r["end"]]
    set_status_line(block, 0, len(block), "carried")
    block.append(f"- {day} carried: folder {number}")
    s, e = oh.section_bounds(flines, "Riders")
    body = flines[s + 1:e]
    while body and not body[-1].strip():
        body.pop()
    tail = [""] + flines[e:] if e < len(flines) else []
    flines = flines[:s + 1] + body + [""] + block + tail
    write_lines(md, flines)
    oh.folder_event(md, day, "carried", f"rider {n}")
    plines = plines[:r["start"]] + [f"- rider {n} -> folder {number}"] + plines[r["end"]:]
    write_lines(page, plines)
    return [f"{SPACE}/riders.md", f"{rel}/folder.md"], [f"rider {n} moved into {rel}; the page keeps its pointer"]


def rider_consumed(root, n, sid, day):
    """Record that rider N was consumed at a session, in the folder that
    holds it. On the desk the status line follows; in the filing cabinet
    only lines are added (doctrine section 15), so the dated line is the
    record there. Returns (changed paths, words)."""
    dt.date.fromisoformat(day)
    if not oh.SID_RE.match(sid):
        raise oh.HelperError(f"not a session id: {sid!r}")
    t = Table(root)
    r = find_rider(t, n)
    if r["home"] == "page":
        raise oh.HelperError(f"rider {n} is on the riders page, carried by no folder yet; "
                             f"office rider carry {n} --folder N moves it into the folder whose session carries it")
    if r["status"] == "consumed":
        raise oh.HelperError(f"rider {n} is already consumed in {r['home']}: "
                             + next((f"{d} {v}: {x}" for d, v, x in reversed(r["states"]) if v == "consumed"), ""))
    md = r["folder"]["path"]
    lines = md.read_text(encoding="utf-8").splitlines()
    fresh = [x for x in rider_blocks(lines, *oh.section_bounds(lines, "Riders")) if x["number"] == n][0]
    lines.insert(fresh["end"], f"- {day} consumed: {sid}")
    if r["folder"]["space"] == "desk":
        set_status_line(lines, fresh["start"], fresh["end"], "consumed")
    write_lines(md, lines)
    oh.folder_event(md, day, "consumed", f"rider {n} at {sid}")
    return [f"{r['home']}/folder.md"], [f"rider {n} consumed at {sid} in {r['home']}"]


def glob_static_prefix(glob):
    return re.split(r"[*?\[]", glob, maxsplit=1)[0]


def glob_touches(glob, entry):
    """Does a forecast entry (a path, a directory covering what is under
    it, or the whole tree) touch a rider's path glob?"""
    g = glob.strip().strip("/")
    e = entry.strip().strip("/")
    if e in ("", "."):
        return True
    if fnmatch.fnmatchcase(e, g) or e == g:
        return True
    prefix = glob_static_prefix(g)
    if prefix.startswith(e + "/") or prefix == e:
        return True  # the forecast directory holds the rider's path
    if not any(c in g for c in "*?[") and e.startswith(g + "/"):
        return True  # the rider names a directory holding the forecast
    parts = e.split("/")
    return any(fnmatch.fnmatchcase("/".join(parts[:k]), g) for k in range(1, len(parts)))


def rider_line(r, t):
    rides = first(r["fields"], "rides") or "no carrier named"
    where = "the riders page" if r["home"] == "page" else r["home"]
    return f"rider {r['number']}  {r['status'] or 'no status'}  {r['title']}  (rides {rides}; {where})"


# A rides glob may name its project first, the way a lane does
# ("office-src: bin/"): only a pack on that project carries it. A bare
# glob rides a pack anywhere whose forecast touches it.
RIDES_PROJECT_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*):\s*(\S.*)$")


def rides_parts(rides):
    """(project or None, glob) of a rider's rides line."""
    m = RIDES_PROJECT_RE.match(rides.strip())
    return (m.group(1), m.group(2).strip()) if m else (None, rides.strip())


def riders_for_forecast(root, forecast, project=None):
    """The queued riders on the page a pack with this forecast carries:
    [{number, title, rides, touched}] in the page's order. project is
    the project the pack is on (None for a pack in the office); a rider
    whose glob names another project, or names one when the pack is in
    the office, is not carried. An office with no drafting table has no
    riders."""
    if not (pathlib.Path(root) / SPACE).is_dir():
        return []
    hits = []
    for r in Table(root).riders():
        rides = first(r["fields"], "rides")
        if r["home"] != "page" or not rides or rides.startswith("folder "):
            continue
        if r["status"] not in (None, "queued"):
            continue
        owner, glob = rides_parts(rides)
        if owner is not None and owner != project:
            continue
        touched = [e for e in forecast if glob_touches(glob, e)]
        if touched:
            hits.append({"number": r["number"], "title": r["title"], "rides": rides, "touched": touched})
    return hits


def render_riders(root, forecast=(), orphans_only=False, project=None):
    t = Table(root)
    if not (pathlib.Path(root) / SPACE).is_dir():
        return ["no drafting table in this office yet, so no riders (office rider add starts the page)"]
    riders = t.riders()
    if forecast:
        hits = [f"  rider {h['number']}  {h['title']}  (rides {h['rides']}; the forecast's "
                + ", ".join(h["touched"]) + ")" for h in riders_for_forecast(root, forecast, project)]
        head = "Riders a pack with this forecast carries (" + ", ".join(forecast) \
            + (f", on {project}" if project else "") + "):"
        return [head] + (hits or ["  none: no queued rider on the page rides these paths"])
    orphans = t.orphans()
    if orphans_only:
        if not orphans:
            return ["no orphaned riders: every rider in the filing cabinet was consumed, ruled moot or left standing"]
        return ["Orphaned riders (in a closed folder, never consumed):"] + \
            [f"  {rider_line(r, t)}" for r in orphans]
    out = ["On the riders page:"]
    page = [r for r in riders if r["home"] == "page"]
    out += [f"  {rider_line(r, t)}" for r in page] or ["  none"]
    for n, m in sorted(t.pointers().items()):
        out.append(f"  rider {n} -> folder {m}")
    held = [r for r in riders if r["home"] != "page"]
    out += ["", "In folders:"] + ([f"  {rider_line(r, t)}" for r in held] or ["  none"])
    if orphans:
        out += ["", "Orphaned (in a closed folder, never consumed):"] + [f"  {rider_line(r, t)}" for r in orphans]
    return out


# --- the agenda --------------------------------------------------------------------

def agenda_add(root, day, text, source, title=None, waiting=()):
    """Add agenda N above the page's Disposed list; returns (N, changed
    paths, words). Numbers count disposed items too: never reused."""
    dt.date.fromisoformat(day)
    if not str(text).strip():
        raise oh.HelperError("the agenda item's text is empty")
    source = oh.one_line(source, "--source")
    title = oh.one_line(title if title else clean_title(text), "the title")
    if len(title) > 72:
        title = title[:69] + "..."
    gates = [oh.normalize_field("linked", w) for w in waiting]
    changed, words = arrive(root, ["agenda.md"])
    t = Table(root)
    entries, disposed = t.agenda()
    n = max([*entries, *disposed], default=0) + 1
    block = [f"## agenda {n} - {oh.ascii_escape(title)[0]}", "", f"- source: {oh.ascii_escape(source)[0]}"]
    if gates:
        block.append(f"- waiting: {', '.join(gates)}")
    body = oh.ascii_escape(str(text).strip("\n"))[0].splitlines()
    # A one-line question that is its own title is said once.
    if not (len(body) == 1 and body[0].strip() == title):
        block += ["", *body]
    block.append("")
    page = pathlib.Path(root) / SPACE / "agenda.md"
    lines = page.read_text(encoding="utf-8").splitlines()
    at = next((i for i, l in unfenced(lines) if l.rstrip() == "## Disposed"), None)
    if at is None:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += [""] + block
    else:
        lines = lines[:at] + block + lines[at:]
    write_lines(page, lines)
    return n, sorted(set(changed + [f"{SPACE}/agenda.md"])), words


# --- rulings and evidence: read-only ---------------------------------------------------

def bold_lead(text):
    joined = " ".join(l.strip() for l in text if l.strip())
    m = re.search(r"\*\*(.+?)\*\*", joined)
    return m.group(1) if m else (joined[:80] + ("..." if len(joined) > 80 else ""))


def ruling_relations(t):
    """For each ruling id: amendments, derivations, and who supersedes it
    (the back-pointer, derived here and never written)."""
    rel = {}
    for r in t.rulings():
        if r["kind"] == "unreadable":
            continue
        if r["kind"] == "amendment":
            rel.setdefault(first(r["fields"], "amends").split()[0], {}).setdefault("amended", []).append(r)
        elif r["kind"] == "derived":
            rel.setdefault(r["id"], {}).setdefault("derived", []).append(r)
        for s in r["fields"].get("supersedes", []):
            rel.setdefault(s.split()[0], {}).setdefault("superseded_by", []).append(r)
    return rel


def cites(text, kind, ref):
    return re.search(rf"\b{kind} {re.escape(str(ref))}\b", text) is not None


def render_rulings(root, rid=None):
    t = Table(root)
    if not (pathlib.Path(root) / SPACE / "rulings.md").is_file():
        return ["no rulings ledger in this office yet: only a sitting writes rulings, on drafting-table/rulings.md"]
    rel = ruling_relations(t)
    rulings = [r for r in t.rulings() if r["kind"] == "ruling"]
    if rid is None:
        out = [f"Rulings ({len(rulings)}):"]
        for r in rulings:
            extra = []
            info = rel.get(r["id"], {})
            if info.get("amended"):
                extra.append(f"amended {len(info['amended'])}x")
            if info.get("superseded_by"):
                extra.append("superseded by " + ", ".join(x["id"] for x in info["superseded_by"]))
            if info.get("derived"):
                extra.append("derived into " + ", ".join(first(x["fields"], "into") or first(x["fields"], "derived-into")
                                                         or "?" for x in info["derived"]))
            out.append(f"  ruling {r['id']}  {bold_lead(r['text'])}" + (f"  [{'; '.join(extra)}]" if extra else ""))
        bad = [r for r in t.rulings() if r["kind"] == "unreadable"]
        out += [f"  a heading that is not a record: line {r['line']}: {r['heading']}" for r in bad]
        return out
    found = [r for r in t.rulings() if r["id"] == rid and r["kind"] != "derived"]
    if not found:
        raise oh.HelperError(f"no ruling {rid} in rulings.md")
    r = found[0]
    if r["kind"] == "amendment":
        raise oh.HelperError(f"{rid} is an amendment of {first(r['fields'], 'amends')}; office rulings "
                             f"{first(r['fields'], 'amends').split()[0]} shows the ruling with every amendment")
    out = [f"ruling {r['id']}"]
    for key, values in r["fields"].items():
        out += [f"  {key}: {v}" for v in values]
    out += [""] + [f"  {l}" for l in r["text"] if l.strip()]
    info = rel.get(rid, {})
    for a in sorted(info.get("amended", []), key=lambda x: x["day"] or ""):
        out += ["", f"  amended by {a['id']} ({a['day'] or 'undated'}): {bold_lead(a['text'])}"]
    for s in info.get("superseded_by", []):
        scope = next((v for v in s["fields"].get("supersedes", []) if v.split()[0] == rid), "")
        out.append(f"  superseded by ruling {s['id']}" + (f" {scope[len(rid):].strip()}" if scope[len(rid):].strip() else ""))
    for d in info.get("derived", []):
        out.append(f"  derived into {first(d['fields'], 'into') or first(d['fields'], 'derived-into')} ({d['day']})")
    landed = [f"folder {f['number']}" if f.get("number") else f["rel"] for f in t.folders()
              if not f["problem"] and cites(f["path"].read_text(encoding="utf-8"), "ruling", rid)]
    if landed:
        out.append("  folders that cite it: " + ", ".join(landed))
    sids = sorted({m.group(1) for v in r["fields"].get("landed", []) + r["fields"].get("source", [])
                   for m in SID_TOKEN_RE.finditer(v)})
    if sids:
        out.append("  sessions it names: " + ", ".join(sids))
    return out


def evidence_problems(t):
    out, seen, last = [], set(), 0
    entries = {r["number"] for r in t.evidence() if r["kind"] == "entry"}
    for r in t.evidence():
        if r["kind"] == "unreadable":
            out.append(f"line {r['line']}: a heading that is not an entry or an event: {r['heading']}")
            continue
        if r["kind"] == "entry":
            if r["number"] in seen:
                out.append(f"evidence {r['number']} is numbered twice (line {r['line']})")
            elif r["number"] < last:
                out.append(f"evidence {r['number']} is out of order (after {last}, line {r['line']})")
            seen.add(r["number"])
            last = max(last, r["number"])
            sources = " ".join(r["fields"].get("from", []) + r["fields"].get("filed", []))
            if not (SID_TOKEN_RE.search(" ".join(r["fields"].get("from", []))) or "notepad/" in sources):
                out.append(f"evidence {r['number']} names no session (`from:` a sid) and no notepad page: the ledger "
                           "admits only what live traffic earned")
        else:
            if r["number"] not in entries:
                out.append(f"an {r['kind']} record (line {r['line']}) points at evidence {r['number']}, which is not an entry")
            who = first(r["fields"], "attributed-to")
            if r["kind"] == "occurrence" and who not in ATTRIBUTIONS:
                out.append(f"the occurrence of evidence {r['number']} on line {r['line']} is attributed to {who!r}, "
                           f"not one of {', '.join(ATTRIBUTIONS)}")
    return out


def render_evidence(root, n=None):
    t = Table(root)
    if not (pathlib.Path(root) / SPACE / "evidence.md").is_file():
        return ["no evidence ledger in this office yet: only a sitting writes evidence, on drafting-table/evidence.md"], 0
    ev = t.evidence()

    def counts(num):
        c = {}
        for r in ev:
            if r["kind"] == "occurrence" and r["number"] == num:
                who = first(r["fields"], "attributed-to") or "unattributed"
                c[who] = c.get(who, 0) + 1
        return c

    if n is None:
        entries = [r for r in ev if r["kind"] == "entry"]
        out = [f"Evidence ({len(entries)} entries):"]
        for r in entries:
            c = counts(r["number"])
            occ = ", ".join(f"{k} {v}" for k, v in sorted(c.items()))
            derived = [x for x in ev if x["kind"] == "derived" and x["number"] == r["number"]]
            out.append(f"  evidence {r['number']}. {r['title']}  (filed {first(r['fields'], 'filed') or '?'}"
                       + (f"; occurrences: {occ}" if occ else "") + (f"; derived {len(derived)}x" if derived else "") + ")")
        problems = evidence_problems(t)
        if problems:
            out += ["", f"{len(problems)} problem(s):"] + [f"  {p}" for p in problems]
        return out, len(problems)
    entry = [r for r in ev if r["kind"] == "entry" and r["number"] == n]
    if not entry:
        raise oh.HelperError(f"no evidence {n} in evidence.md")
    r = entry[0]
    out = [f"evidence {n}. {r['title']}"]
    for key, values in r["fields"].items():
        out += [f"  {key}: {v}" for v in values]
    out += [""] + [f"  {l}" for l in r["text"] if l.strip()]
    c = counts(n)
    out += ["", "  occurrences: " + (", ".join(f"{k} {v}" for k, v in sorted(c.items())) or "none")]
    for x in ev:
        if x["number"] == n and x["kind"] in ("occurrence", "derived"):
            lead = " ".join(l.strip() for l in x["text"] if l.strip())
            fields = "; ".join(f"{k}: {', '.join(v)}" for k, v in x["fields"].items())
            out.append(f"  {x['day']} {x['kind']}: {fields}" + (f". {lead}" if lead else ""))
    return out, 0


# --- the citation check --------------------------------------------------------------

CITE_RES = (
    ("folder", re.compile(r"\bfolders? (\d+(?:, ?\d+)*)\b")),
    ("blueprint", re.compile(rf"\bblueprint ({ID_PART})\b")),
    ("ruling", re.compile(rf"\bruling ({ID_PART})\b")),
    ("evidence", re.compile(r"\bevidence (\d+)\b")),
    ("watch", re.compile(r"\bwatch W(\d+)\b")),
    ("rider", re.compile(r"\brider (\d+)\b")),
    ("agenda", re.compile(r"\bagenda (\d+)\b")),
    # A notepad page is dated: notepad/DATE.md or notepad/DATE-SLUG.md
    # (a placeholder such as notepad/PAGE.md is no citation).
    ("notepad", re.compile(r"\b(notepad/\d{4}-\d{2}-\d{2}(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?\.md)\b")),
)
WATCH_LOG_RE = re.compile(rf"^- {DATE} W(\d+) ")


def citations_in(lines, rel):
    """(rel, line number, kind, ref) for every citation outside fences."""
    for i, line in unfenced(lines):
        for kind, rx in CITE_RES:
            for m in rx.finditer(line):
                refs = re.split(r", ?", m.group(1)) if kind == "folder" else [m.group(1)]
                for ref in refs:
                    yield rel, i + 1, kind, ref
        if rel.endswith("watch-log.md"):
            m = WATCH_LOG_RE.match(line)
            if m:
                yield rel, i + 1, "watch", m.group(1)
        m = re.match(rf"^- blueprint: ({ID_PART})\s*$", line)
        if m:
            yield rel, i + 1, "blueprint", m.group(1)


def sids_in(lines, rel):
    for i, line in unfenced(lines):
        for m in SID_TOKEN_RE.finditer(line):
            yield rel, i + 1, m.group(1)


def citation_files(root):
    root = pathlib.Path(root)
    out = []
    if (root / SPACE).is_dir():
        out += sorted(p for p in (root / SPACE).rglob("*.md") if p.is_file())
    out += sorted(p for p in (root / "desk").glob("*/folder.md"))
    return out


def check_citations(root, known_sids=None):
    """(problems, counts, unresolved sids): every citation in the drafting
    table and the desk against the grammar. known_sids, when given, is the
    set of session ids the registries this office reads name; a sid
    outside it is listed apart, since a registry the office does not read
    may hold it."""
    t = Table(root)
    root = pathlib.Path(root)
    problems, n, sid_misses = [], 0, []
    for p in citation_files(root):
        rel = str(p.relative_to(root))
        lines = p.read_text(encoding="utf-8").splitlines()
        for _, line, kind, ref in citations_in(lines, rel):
            n += 1
            state, words = t.resolve(kind, ref)
            if state != "ok":
                problems.append(f"{rel}:{line}: {kind} {ref}: {words}")
        if known_sids is not None:
            for _, line, sid in sids_in(lines, rel):
                n += 1
                if sid not in known_sids:
                    sid_misses.append(f"{rel}:{line}: {sid}")
    return problems, n, sid_misses


# --- blueprints ----------------------------------------------------------------------

def blueprint_open(root, day, slug, title, charter=None):
    dt.date.fromisoformat(day)
    slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", slug.lower())).strip("-")
    if not slug:
        raise oh.HelperError("the slug has no letters or digits")
    bid = f"{day}-{slug}"
    d = pathlib.Path(root) / BLUEPRINTS / bid
    if d.exists():
        raise oh.HelperError(f"{BLUEPRINTS}/{bid} already exists; nothing written")
    changed, words = arrive(root)
    text = oh.render_template((TEMPLATES / "blueprint.md").read_text(encoding="utf-8"), {
        "title": oh.one_line(title, "the title"),
        "charter": oh.ascii_escape(charter.strip("\n"))[0] if charter and charter.strip() else CHARTER_PLACEHOLDER,
        "history": f"{day} drafted: office blueprint open"})
    d.mkdir(parents=True)
    (d / "blueprint.md").write_text(text, encoding="utf-8")
    return bid, changed + [f"{BLUEPRINTS}/{bid}/blueprint.md"], words


def blueprint_ratify(root, bid, day, words_page=None, sid=None):
    dt.date.fromisoformat(day)
    if bool(words_page) == bool(sid):
        raise oh.HelperError("ratification names where its words are: --words notepad/PAGE or --sid SID, one of them")
    b = Table(root).blueprints().get(bid)
    if b is None:
        raise oh.HelperError(f"no blueprint {bid} on the drafting table")
    if b["problem"]:
        raise oh.HelperError(f"blueprint {bid}: {b['problem']}")
    if b["closed"]:
        raise oh.HelperError(f"blueprint {bid} is closed (its close.md exists); a closed arc is not ratified")
    if b["ratified"]:
        raise oh.HelperError(f"blueprint {bid} was ratified on {b['ratified'][0]} ({b['ratified'][1]}); a charter "
                             "that must change is a new blueprint whose history opens `supersedes: blueprint "
                             f"{bid}`")
    if charter_is_empty(b["charter"]):
        raise oh.HelperError(f"blueprint {bid}'s charter is empty; write what the arc is for and what done means "
                             "before it is ratified")
    if words_page:
        page = words_page.strip()
        if not re.match(r"^notepad/[A-Za-z0-9._-]+\.md$", page) or not (pathlib.Path(root) / page).is_file():
            raise oh.HelperError(f"--words names the notepad page that carries the words, and {page!r} is not one "
                                 "in this office")
        where, hist = f"words at {page}", page
    else:
        if not oh.SID_RE.match(sid):
            raise oh.HelperError(f"not a session id: {sid!r}")
        where, hist = f"at {sid}", sid
    md = b["dir"] / "blueprint.md"
    lines = md.read_text(encoding="utf-8").splitlines()
    new = oh.append_line_to_section(lines, "Charter", f"- ratified: {day}, {where}")
    if new is None:
        raise oh.HelperError(f"blueprint {bid} has no Charter section")
    new2 = oh.append_line_to_section(new, "History", f"- {day} ratified: {hist}")
    if new2 is None:
        raise oh.HelperError(f"blueprint {bid} has no History section")
    write_lines(md, new2)
    return [f"{BLUEPRINTS}/{bid}/blueprint.md"]


def blueprint_members(t, bid):
    """The folders of an arc: every folder whose blueprint field names it,
    and every folder its decomposition lines name."""
    b = t.blueprints().get(bid)
    rels = []
    for f in t.folders():
        if not f["problem"] and first(f["fields"], "blueprint") == bid:
            rels.append(f["rel"])
    for line in (b["decomposition"] if b else []):
        if line["folder"] is not None:
            state, rel = t.resolve("folder", line["folder"])
            if state == "ok":
                rels.append(rel)
    return sorted(set(rels))


def close_plan(root, bid):
    t = Table(root)
    b = t.blueprints().get(bid)
    if b is None:
        raise oh.HelperError(f"no blueprint {bid} on the drafting table")
    if b["problem"]:
        raise oh.HelperError(f"blueprint {bid}: {b['problem']}")
    if b["closed"]:
        raise oh.HelperError(f"blueprint {bid} is closed already: {BLUEPRINTS}/{bid}/close.md exists")
    members = blueprint_members(t, bid)
    ledgers = [f"{SPACE}/{p}" for p in ("rulings.md", "evidence.md", "watches.md")
               if (pathlib.Path(root) / SPACE / p).is_file()]
    close_folders = [f["rel"] for f in t.folders() if not f["problem"] and f["space"] == "desk"
                     and first(f["fields"], "source") == f"blueprint {bid}"
                     and (f.get("title") or "").startswith("Close blueprint")]
    return {"id": bid, "title": b["title"], "ratified": bool(b["ratified"]), "members": members,
            "ledgers": ledgers, "close_folder": close_folders[0] if close_folders else None,
            "decomposition": [{"n": d["n"], "goal": d["goal"], "folder": d["folder"]} for d in b["decomposition"]]}


def close_brief(plan):
    lines = [f"# Close: {plan['title']}", "",
             f"A sitting scoped to one blueprint, `blueprint {plan['id']}`, sent out by `office blueprint close`. "
             "A close is judgment (the residual, the partition), so it is a session.", "",
             "## What lands", "",
             f"- `drafting-table/blueprints/{plan['id']}/close.md`, written once from the close report's template "
             "(it rides beside this request from the install, as templates/close-report.md), and filed: it is never "
             "edited after this session.",
             "- the sitting's notepad page, `notepad/DATE-SLUG.md`, with the occupant's words verbatim.",
             "- closing the member folders is the office command's: each goes on `drafting-table/moves.md` as a desk "
             "move (`- [ ] DATE close folder N`, `retire folder N why=\"...\"`, ...), and `office moves` applies them "
             "after this session lands.", "",
             "## The arc", "",
             f"- ratified: {'yes' if plan['ratified'] else 'no'}",
             "- member folders: " + (", ".join(plan["members"]) or "none found"),
             "- decomposition:"]
    for d in plan["decomposition"]:
        lines.append(f"  - line {d['n']}: {d['goal']} -> " + (f"folder {d['folder']}" if d["folder"] else "no folder"))
    return "\n".join(lines) + "\n"


def charter_check(root):
    """(lines, problems): every blueprint whose charter was ratified, its
    charter's bytes against git from the ratifying commit on."""
    root = pathlib.Path(root)
    base = root / BLUEPRINTS
    if not base.is_dir():
        return [], 0
    try:
        oh.git_out(root, "rev-parse", "--verify", "-q", "HEAD")
    except oh.HelperError:
        return ["charters:   not checked: the office has no commit yet"], 0
    problems, ratified = [], 0
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        rel = f"{BLUEPRINTS}/{d.name}/blueprint.md"
        log_ = oh.git_out(root, "log", "--reverse", "--format=%H %ad", "--date=short", "--", rel).split("\n")
        commits = [l.split(" ") for l in log_ if l.strip()]
        base_charter, at, last = None, None, None
        for sha, day in commits:
            try:
                text = oh.git_out(root, "show", f"{sha}:{rel}")
            except oh.HelperError:
                continue  # removed in that commit
            charter = last = charter_of(text)
            if base_charter is None:
                if charter is not None and any(RATIFIED_LINE_RE.match(l) for l in charter):
                    base_charter, at = charter, (sha, day)
                continue
            if charter != base_charter:
                problems.append(f"{rel}: commit {sha[:10]} ({day}) changed the charter ratified in {at[0][:10]} "
                                f"({at[1]})")
        disk = d / "blueprint.md"
        now = charter_of(disk.read_text(encoding="utf-8")) if disk.is_file() else None
        if base_charter is None:
            if now is not None and any(RATIFIED_LINE_RE.match(l) for l in now):
                problems.append(f"{rel}: ratified on disk, but no commit holds the ratification yet")
            continue
        ratified += 1
        if now != last:
            problems.append(f"{rel}: uncommitted changes to the charter ratified in {at[0][:10]} ({at[1]})")
    if problems:
        return [f"charters:   {len(problems)} change(s) to ratified charters:"] + [f"  {p}" for p in problems], len(problems)
    if ratified:
        return [f"charters:   {ratified} ratified charter(s), unchanged since ratification"], 0
    return ["charters:   no blueprint's charter is ratified yet"], 0


def charter_of(text):
    lines = text.splitlines()
    s, e = oh.section_bounds(lines, "Charter")
    if s is None:
        return None
    body = lines[s + 1:e]
    while body and not body[-1].strip():
        body.pop()
    return body


# --- desk moves ----------------------------------------------------------------------

MOVE_VERBS = ("open", "queue", "gate", "close", "absorb", "split", "retire")
OPEN_KEYS = {"slug": False, "class": False, "size": False, "lane": False, "source": False, "blueprint": False,
             "line": False, "candidate": False, "after": True, "serializes-after": True, "consumer": True,
             "linked": True}
GATE_KEYS = ("after", "serializes-after", "consumer")


class MoveError(oh.HelperError):
    pass


def parse_move(text, lineno, t):
    """One pending move's words as a dict: verb, folder (for the verbs
    that act on one), keys. Raises MoveError naming what does not read."""
    try:
        words = shlex.split(text, posix=True)
    except ValueError as exc:
        raise MoveError(f"its quoting does not read ({exc})")
    if not words:
        raise MoveError("no verb")
    verb, rest = words[0], words[1:]
    if verb not in MOVE_VERBS:
        raise MoveError(f"{verb!r} is not a move ({', '.join(MOVE_VERBS)})")
    move = {"line": lineno, "verb": verb, "text": text, "keys": {}}
    if verb == "open":
        if not rest or "=" in rest[0]:
            raise MoveError('open takes the title first, in quotes: open "TITLE" key=value ...')
        move["title"] = oh.one_line(rest[0], "the title")
        rest = rest[1:]
        allowed = OPEN_KEYS
    else:
        if len(rest) < 2 or rest[0] != "folder" or not rest[1].isdigit():
            raise MoveError(f"{verb} takes the folder it acts on next: {verb} folder N")
        move["folder"] = int(rest[1])
        rest = rest[2:]
        allowed = {"gate": {k: True for k in GATE_KEYS}, "absorb": {"into": False}, "split": {"into": False},
                   "retire": {"why": False}}.get(verb, {})
    for w in rest:
        key, eq, value = w.partition("=")
        if not eq or key not in allowed:
            raise MoveError(f"{w!r} is not a key {verb} takes" + (f" ({', '.join(allowed)})" if allowed else
                                                                       " (it takes none)"))
        if allowed[key]:
            move["keys"].setdefault(key, []).append(value)
        elif key in move["keys"]:
            raise MoveError(f"{key}= is given twice")
        else:
            move["keys"][key] = value
    k = move["keys"]
    # Every value checked now, so a line that cannot apply is named
    # before anything is applied.
    for key in ("class", "size", "lane", "source", "blueprint"):
        if key in k:
            k[key] = oh.normalize_field(key, k[key])
    for key in ("after", "serializes-after", "consumer", "linked"):
        if key in k:
            k[key] = [oh.normalize_field(key.replace("-", " "), v) for v in k[key]]
    if "candidate" in k and k["candidate"] not in ("yes", "true"):
        raise MoveError("candidate=yes opens the folder as a candidate; nothing else is a value it takes")
    if verb == "gate" and not k:
        raise MoveError("gate names at least one gate: after=, serializes-after= or consumer=")
    if verb in ("absorb", "split") and "into" not in k:
        raise MoveError(f"{verb} names where the job goes: into=\"folder M\"" + (" or into=\"A,B\"" if verb == "split" else ""))
    if verb == "absorb":
        k["into"] = oh.normalize_field("linked", k["into"])
    if verb == "split":
        parts = [p for p in re.split(r"[,\s]+", k["into"].replace("folders", "").replace("folder", "")) if p]
        if len(parts) < 2 or not all(p.isdigit() for p in parts):
            raise MoveError("split into= names two or more folders: into=\"A,B\"")
        k["into"] = ",".join(parts)
    if verb == "retire" and not k.get("why", "").strip():
        raise MoveError('retire says why: why="..."')
    if verb == "open" and "blueprint" in k:
        b = t.blueprints().get(k["blueprint"])
        if b is None:
            raise MoveError(f"blueprint={k['blueprint']} names no blueprint on the drafting table")
        lines = b["decomposition"]
        if "line" in k:
            if not k["line"].isdigit() or not 1 <= int(k["line"]) <= len(lines):
                raise MoveError(f"line={k['line']}: blueprint {k['blueprint']}'s decomposition has {len(lines)} line(s)")
            hit = lines[int(k["line"]) - 1]
        else:
            want = " ".join(move["title"].lower().split())
            same = [d for d in lines if " ".join(d["goal"].lower().split()) == want and d["folder"] is None]
            if len(same) != 1:
                raise MoveError(f"no single decomposition line of blueprint {k['blueprint']} without a folder reads "
                                f"{move['title']!r} ({len(same)} do); name it with line=N")
            hit = same[0]
        if hit["folder"] is not None:
            raise MoveError(f"blueprint {k['blueprint']}'s decomposition line {hit['n']} already names folder {hit['folder']}")
        move["decomposition"] = hit["n"]
    elif "line" in k:
        raise MoveError("line= names a decomposition line, so it goes with blueprint=")
    return move


def pending_moves(root):
    """(moves, errors): every pending line of moves.md, in order, parsed;
    errors name each line that does not read. A line that is neither a
    move nor blank, outside the page's fenced examples and above its
    first move, is the page's prose and is left alone."""
    t = Table(root)
    lines = t.page("moves.md")
    moves, errors = [], []
    for i, l in unfenced(lines):
        if not l.startswith("- ["):
            continue
        m = MOVE_RE.match(l)
        if not m:
            errors.append(f"moves.md line {i + 1} is not `- [ ] YYYY-MM-DD MOVE ...`: {l}")
            continue
        if m.group(1) != " ":
            continue
        try:
            dt.date.fromisoformat(m.group(2))
            mv = parse_move(m.group(3), i + 1, t)
        except ValueError:
            errors.append(f"moves.md line {i + 1}: {m.group(2)} is not a date")
            continue
        except oh.HelperError as exc:
            errors.append(f"moves.md line {i + 1}: {exc}: {l}")
            continue
        mv["day"] = m.group(2)
        moves.append(mv)
    return moves, errors


def tick_move(root, lineno, number, blueprint=None, decomposition=None):
    """Tick a pending line (`- [x] ... -> folder N`) and, for an open
    move of a blueprint, write the folder onto its decomposition line.
    Returns the changed paths."""
    page = pathlib.Path(root) / SPACE / "moves.md"
    lines = page.read_text(encoding="utf-8").splitlines()
    line = lines[lineno - 1]
    if not line.startswith("- [ ] "):
        raise oh.HelperError(f"moves.md line {lineno} is not pending any more: {line}")
    lines[lineno - 1] = "- [x] " + line[len("- [ ] "):].rstrip() + f" -> folder {number}"
    write_lines(page, lines)
    changed = [f"{SPACE}/moves.md"]
    if blueprint:
        md = pathlib.Path(root) / BLUEPRINTS / blueprint / "blueprint.md"
        blines = md.read_text(encoding="utf-8").splitlines()
        d = decomposition_line(blines, decomposition)
        blines[d["index"]] = f"- {d['goal']} -> folder {number}"
        write_lines(md, blines)
        changed.append(f"{BLUEPRINTS}/{blueprint}/blueprint.md")
    return changed


def move_argv(mv):
    """The argv a move is applied with: office open's or office close's
    own flags, or the gates for office moves' gate step."""
    k = mv["keys"]
    if mv["verb"] == "open":
        argv = [k["slug"]] if "slug" in k else []
        argv += ["--title", mv["title"]]
        for key in ("class", "size", "lane", "source", "blueprint"):
            if key in k:
                argv += [f"--{key}", k[key]]
        for key in ("after", "serializes-after", "consumer", "linked"):
            for v in k.get(key, []):
                argv += [f"--{key}", v]
        if "candidate" in k:
            argv.append("--candidate")
        return argv
    if mv["verb"] == "gate":
        return [x for key in GATE_KEYS for v in k.get(key, []) for x in (key, v)]
    me = f"folder {mv['folder']}"
    return {"queue": [], "close": [me], "absorb": [me, "--into", k.get("into", "")],
            "split": [me, "--split", k.get("into", "")], "retire": [me, "--retired", k.get("why", "")]}[mv["verb"]]


def shell_record(mv):
    """One move as office moves reads it: fields split by \x1e, the argv
    by \x1f (neither is whitespace, so an empty field stays a field)."""
    return "\x1e".join([str(mv["line"]), mv["verb"], str(mv.get("folder") or ""), mv["day"],
                        mv["keys"].get("blueprint", "") if mv["verb"] == "open" and "decomposition" in mv else "",
                        str(mv.get("decomposition") or ""), "\x1f".join(move_argv(mv)), mv["text"]])


def rider_home(root, n):
    r = find_rider(Table(root), n)
    if r["home"] == "page":
        raise oh.HelperError(f"rider {n} is on the riders page, carried by no folder yet; "
                             f"office rider carry {n} --folder N moves it into the folder whose session carries it")
    return r["home"]


def decomposition_line(lines, n):
    found = [d for d in decomposition(lines) if d["n"] == n]
    if not found:
        raise oh.HelperError(f"the blueprint has no decomposition line {n}")
    return found[0]


def move_sources(root):
    """{pending line number: where it came from}: the session whose
    commit wrote the line (bale commits a session's work as `[bale SID]
    ...`, the shape share/bale-consumption.toml declares under
    [surfaces.commits]), else the commit, else `not committed`. From git
    blame, once."""
    import office_bale as ob  # here, not above: office_bale imports this module
    shapes = ob.Consumption()
    root = pathlib.Path(root)
    rel = f"{SPACE}/moves.md"
    try:
        out = oh.git_out(root, "blame", "--porcelain", "--", rel)
    except oh.HelperError as exc:
        debug(f"no blame for {rel}: {exc}")
        return {}
    summaries, line_commit, current = {}, {}, None
    for line in out.splitlines():
        m = re.match(r"^([0-9a-f]{40}) \d+ (\d+)", line)
        if m:
            current = m.group(1)
            line_commit[int(m.group(2))] = current
        elif line.startswith("summary ") and current:
            summaries[current] = line[len("summary "):]
    src = {}
    for n, sha in line_commit.items():
        if set(sha) == {"0"}:
            src[n] = "not committed yet"
            continue
        found = shapes.subject_sid(summaries.get(sha, ""))
        src[n] = f"`{found[1]}`" if found and found[0] == "work" else f"commit {sha[:7]}"
    return src


def moves_summary(root):
    """(count, source words, errors) of pending moves, for the desk."""
    if not (pathlib.Path(root) / SPACE / "moves.md").is_file():
        return 0, "", []
    moves, errors = pending_moves(root)
    if not moves and not errors:
        return 0, "", []
    src = move_sources(root)
    by = {}
    for mv in moves:
        by.setdefault(src.get(mv["line"], "an unknown commit"), []).append(mv)
    words = ", ".join(f"{len(v)} from {k}" for k, v in by.items())
    return len(moves), words, errors


# --- the command line --------------------------------------------------------------

def emit(changed, words):
    for w in words:
        log(w)
    for c in changed:
        print(c)


def known_sids(root):
    """Every sid the registries this office reads name, or (None, why)."""
    try:
        import office_bale as ob
        rd = ob.Reader()
        out = set()
        own = ob.office_registry(root)
        places = [own] if own is not None else []
        for p in ob.office_projects(root) or []:
            try:
                places.append(ob.readable(p))
            except ob.BaleError as exc:
                debug(f"{p['name']}: {exc}")
        if not places:
            return None, "this office reads no registry: bale keeps none in it, and it scopes no projects"
        for place in places:
            out.update(rd.known_sids(place))
        return out, None
    except Exception as exc:  # the check reports it; never a crash
        return None, str(exc)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_drafting.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("arrive"); p.add_argument("root"); p.add_argument("--page", action="append", default=[])
    p = sub.add_parser("table-check"); p.add_argument("root")
    p = sub.add_parser("rider-add"); p.add_argument("root"); p.add_argument("--day", required=True)
    p.add_argument("--title", required=True); p.add_argument("--source", required=True)
    p.add_argument("--rides"); p.add_argument("--carrier"); p.add_argument("--text-file")
    p = sub.add_parser("rider-carry"); p.add_argument("root"); p.add_argument("number", type=int)
    p.add_argument("--folder", required=True); p.add_argument("--day", required=True)
    p = sub.add_parser("rider-consumed"); p.add_argument("root"); p.add_argument("number", type=int)
    p.add_argument("sid"); p.add_argument("--day", required=True)
    p = sub.add_parser("riders"); p.add_argument("root"); p.add_argument("--forecast", nargs="+", default=[])
    p.add_argument("--orphans", action="store_true")
    p.add_argument("--project", help="with --forecast: the project the pack is on")
    p = sub.add_parser("next-rider"); p.add_argument("root")
    p = sub.add_parser("agenda-add"); p.add_argument("root"); p.add_argument("--day", required=True)
    p.add_argument("--text-file", required=True); p.add_argument("--source", required=True)
    p.add_argument("--title"); p.add_argument("--waiting", action="append", default=[])
    p = sub.add_parser("rulings"); p.add_argument("root"); p.add_argument("id", nargs="?")
    p.add_argument("--check", action="store_true")
    p = sub.add_parser("evidence"); p.add_argument("root"); p.add_argument("number", nargs="?", type=int)
    p = sub.add_parser("blueprint-open"); p.add_argument("root"); p.add_argument("slug")
    p.add_argument("--day", required=True); p.add_argument("--title", required=True); p.add_argument("--charter-file")
    p = sub.add_parser("blueprint-ratify"); p.add_argument("root"); p.add_argument("id")
    p.add_argument("--day", required=True); p.add_argument("--words"); p.add_argument("--sid")
    p = sub.add_parser("blueprint-close-plan"); p.add_argument("root"); p.add_argument("id")
    p.add_argument("--brief", help="write the close sitting's brief here")
    p = sub.add_parser("blueprints"); p.add_argument("root")
    p = sub.add_parser("charter-check"); p.add_argument("root")
    p = sub.add_parser("moves-plan"); p.add_argument("root"); p.add_argument("--shell", action="store_true")
    p = sub.add_parser("rider-home"); p.add_argument("root"); p.add_argument("number", type=int)
    p = sub.add_parser("moves-tick"); p.add_argument("root"); p.add_argument("line", type=int)
    p.add_argument("number", type=int); p.add_argument("--blueprint"); p.add_argument("--decomposition", type=int)
    p = sub.add_parser("clean-title"); p.add_argument("text")
    a = ap.parse_args(argv)
    try:
        return dispatch(a)
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, ValueError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        log(f"error: {exc.__class__.__name__}: {exc}")
        return 2


def text_from(path):
    return pathlib.Path(path).read_text(encoding="utf-8") if path else ""


def dispatch(a):
    if a.cmd == "arrive":
        emit(*arrive(a.root, a.page))
    elif a.cmd == "table-check":
        lines, problems = table_check(a.root)
        clines, cproblems = charter_check(a.root)
        print("\n".join(lines + clines))
        return 3 if problems or cproblems else 0
    elif a.cmd == "rider-add":
        n, changed, words = rider_add(a.root, a.day, a.title, a.source, a.rides, a.carrier, text_from(a.text_file))
        words.append(f"rider {n} added to {SPACE}/riders.md")
        print(f"rider {n}")
        emit(changed, words)
    elif a.cmd == "rider-carry":
        emit(*rider_carry(a.root, a.number, a.folder, a.day))
    elif a.cmd == "rider-consumed":
        emit(*rider_consumed(a.root, a.number, a.sid, a.day))
    elif a.cmd == "riders":
        print("\n".join(render_riders(a.root, a.forecast, a.orphans, a.project)))
    elif a.cmd == "next-rider":
        print(Table(a.root).next_rider())
    elif a.cmd == "agenda-add":
        n, changed, words = agenda_add(a.root, a.day, text_from(a.text_file), a.source, a.title, a.waiting)
        words.append(f"agenda {n} added to {SPACE}/agenda.md")
        print(f"agenda {n}")
        emit(changed, words)
    elif a.cmd == "rulings":
        if a.check:
            sids, why = known_sids(a.root)
            problems, n, misses = check_citations(a.root, sids)
            if not (pathlib.Path(a.root) / SPACE).is_dir():
                print("no drafting table in this office yet; the desk's citations were checked")
            if problems:
                print(f"{len(problems)} citation(s) of {n} do not resolve:")
                print("\n".join(f"  {p}" for p in problems))
            else:
                print(f"every citation resolves ({n} checked, in the drafting table and on the desk)")
            if sids is None:
                print(f"session ids not checked: {why}")
            elif misses:
                print(f"{len(misses)} session id(s) no registry this office reads names (a project it does not "
                      "scope may hold them):")
                print("\n".join(f"  {m}" for m in misses))
            return 3 if problems or misses else 0
        print("\n".join(render_rulings(a.root, a.id)))
    elif a.cmd == "evidence":
        lines, problems = render_evidence(a.root, a.number)
        print("\n".join(lines))
        return 3 if problems else 0
    elif a.cmd == "blueprint-open":
        bid, changed, words = blueprint_open(a.root, a.day, a.slug, a.title, text_from(a.charter_file) or None)
        words.append(f"blueprint {bid} drafted at {BLUEPRINTS}/{bid}/blueprint.md")
        print(f"blueprint {bid}")
        emit(changed, words)
    elif a.cmd == "blueprint-ratify":
        emit(blueprint_ratify(a.root, a.id, a.day, a.words, a.sid), [f"blueprint {a.id}'s charter is ratified"])
    elif a.cmd == "blueprint-close-plan":
        plan = close_plan(a.root, a.id)
        if a.brief:
            pathlib.Path(a.brief).write_text(close_brief(plan), encoding="utf-8")
        print(json.dumps(plan))
    elif a.cmd == "blueprints":
        for bid, b in Table(a.root).blueprints().items():
            state = "closed" if b["closed"] else ("ratified" if b["ratified"] else "drafted")
            print(f"{bid}\t{state}\t{b['title']}")
    elif a.cmd == "charter-check":
        lines, problems = charter_check(a.root)
        print("\n".join(lines))
        return 3 if problems else 0
    elif a.cmd == "moves-plan":
        moves, errors = pending_moves(a.root)
        if errors:
            print("\n".join(errors))
            return 1
        if a.shell:
            for mv in moves:
                print(shell_record(mv))
        else:
            print(json.dumps(moves))
    elif a.cmd == "rider-home":
        print(rider_home(a.root, a.number))
    elif a.cmd == "moves-tick":
        for c in tick_move(a.root, a.line, a.number, a.blueprint, a.decomposition):
            print(c)
    elif a.cmd == "clean-title":
        print(clean_title(a.text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
