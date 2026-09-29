#!/usr/bin/env python3
"""Helpers for the office command.

The office command is bash; the parts that need a real parser (TOML,
Markdown sections, version ordering, fact diffs) live here. Standard
library only. Every subcommand prints its result on stdout, logs to
stderr with an [office] prefix, and exits 0 on success, 1 on a refusal
the caller should report, 2 on a usage or internal error, and 3 where a
subcommand documents a second outcome (an incomplete profile, an unmet
renovation declaration, include-group drift), and 4 when record-session
finds the id already recorded.
"""

import argparse
import datetime as dt
import pathlib
import re
import sys
import tomllib

VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
MIGRATION_KINDS = ("script", "renovation")


class HelperError(Exception):
    """A problem the caller should see as one clear line."""


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


# --- versions -------------------------------------------------------------

def parse_version(text):
    m = VERSION_RE.match(text.strip())
    if not m:
        raise HelperError(f"not a version (want MAJOR.MINOR.PATCH): {text!r}")
    return tuple(int(p) for p in m.groups())


def compare_versions(a, b):
    pa, pb = parse_version(a), parse_version(b)
    return (pa > pb) - (pa < pb)


# --- floor plan -----------------------------------------------------------

def read_toml(path):
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        raise HelperError(f"missing file: {path}")
    except tomllib.TOMLDecodeError as exc:
        raise HelperError(f"{path}: not valid TOML ({exc})")


def office_stamp(manifest):
    """The office's version stamp, tolerating older shapes.

    migrated_to may be absent in an office that predates it; built_from
    then stands in. An office with neither has no stamp at all, which is
    the one thing the tool cannot work around.
    """
    office = manifest.get("office", {})
    built = office.get("built_from")
    migrated = office.get("migrated_to", built)
    if migrated is None:
        raise HelperError("floor plan has no version stamp ([office] built_from)")
    parse_version(migrated)
    return {"built_from": built or migrated, "migrated_to": migrated}


def space_paths(manifest, prop):
    """Paths of spaces whose `prop` is set. `hung` may also be a list of
    paths inside the space, which are returned instead of the space."""
    out = []
    for name, space in sorted(manifest.get("spaces", {}).items()):
        value = space.get(prop, False)
        if value is True:
            out.append(space.get("path", name))
        elif isinstance(value, list):
            out.extend(str(v) for v in value)
    return out


def render_flag_or_list(value):
    """A space property as the floor plan writes it. `hung` and `filed`
    take the same two shapes: true or false for the whole space, or a
    list of paths inside it. Anything else is a catalog defect."""
    if isinstance(value, list):
        return "[" + ", ".join(f'"{v}"' for v in value) + "]"
    if value is True or value is False:
        return "true" if value else "false"
    raise HelperError(f"a space property must be true, false or a list of paths, not {value!r}")


def render_manifest(spaces_catalog, name, version, built_at, timezone):
    """The floor plan a new office starts with: its stamp and the base
    spaces from the install's catalog."""
    lines = [
        "# Floor plan of this office. The office command finds an office by",
        "# this file and reads it on every run. Only office upgrade writes",
        "# migrated_to. The founding session sets the timezone; renovation",
        "# sessions change the spaces. Nothing else should change it.",
        "",
        "[office]",
        f'name = "{name}"',
        f'built_from = "{version}"',
        f'migrated_to = "{version}"',
        f'built_at = "{built_at}"',
        f'timezone = "{timezone}"',
    ]
    for key, space in spaces_catalog.get("spaces", {}).items():
        if not space.get("base", False):
            continue
        lines += ["", f"[spaces.{key}]", f'path = "{space["path"]}"']
        for prop in ("hung", "filed"):
            lines.append(f"{prop} = {render_flag_or_list(space.get(prop, False))}")
    return "\n".join(lines) + "\n"


def set_migrated_to(path, version):
    """Rewrite migrated_to inside [office], keeping every other byte."""
    parse_version(version)
    text = pathlib.Path(path).read_text(encoding="ascii")
    out, in_office, done = [], False, False
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("["):
            if in_office and not done:
                out.append(f'migrated_to = "{version}"\n')
                done = True
            in_office = stripped == "[office]"
        elif in_office and re.match(r"migrated_to\s*=", stripped):
            line, done = f'migrated_to = "{version}"\n', True
        out.append(line)
    if in_office and not done:
        out.append(f'migrated_to = "{version}"\n')
        done = True
    if not done:
        raise HelperError(f"{path}: no [office] table to stamp")
    pathlib.Path(path).write_text("".join(out), encoding="ascii")


# --- profile --------------------------------------------------------------

HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


def profile_sections(text):
    sections, current = {}, None
    for line in text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            current = m.group(1)
            sections[current] = []
        elif current is not None:
            sections[current].append(line)
    return {k: "\n".join(v) for k, v in sections.items()}


def section_is_filled(body):
    """A section is filled when, with comments removed, it holds text and
    no line still starts with TODO. A stub's placeholders fail both ways."""
    visible = COMMENT_RE.sub("", body).strip()
    if not visible:
        return False
    return not any(l.strip().startswith("TODO") for l in visible.splitlines())


def check_profile(profile_path, shape):
    """Return (missing, blank) lists of required section headings."""
    required = [s["heading"] for s in shape.get("section", [])]
    if not required:
        raise HelperError("profile shape lists no sections")
    try:
        text = pathlib.Path(profile_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return required, []
    found = profile_sections(text)
    missing = [h for h in required if h not in found]
    blank = [h for h in required if h in found and not section_is_filled(found[h])]
    return missing, blank


# --- survey ---------------------------------------------------------------

SURVEY_TIME_KEY = "survey.surveyed_at"


def read_facts(path):
    """Facts arrive as section<TAB>key<TAB>value lines, in order."""
    facts = []
    for n, line in enumerate(pathlib.Path(path).read_text(encoding="utf-8",
                                                          errors="replace").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            raise HelperError(f"facts line {n} is not section<TAB>key<TAB>value: {line!r}")
        facts.append(tuple(p.strip() for p in parts))
    return facts


def ascii_clean(text):
    return text.encode("ascii", "replace").decode("ascii")


def facts_from_page(text):
    """Recover facts from a survey page this module wrote."""
    facts, section = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            if section.startswith("Changes since"):
                section = None
            continue
        if section is None or not line.startswith("- "):
            continue
        m = re.match(r"^- ([^:]+): ?(.*)$", line)
        if m:
            facts[f"{section.lower()}.{m.group(1).strip()}"] = m.group(2).strip()
    return facts


def diff_facts(old, new):
    changes = []
    for key in sorted(set(old) | set(new)):
        if key == SURVEY_TIME_KEY:
            continue
        if key not in old:
            changes.append(f"added {key}: {new[key]}")
        elif key not in new:
            changes.append(f"removed {key} (was: {old[key]})")
        elif old[key] != new[key]:
            changes.append(f"changed {key}: {old[key]} to {new[key]}")
    return changes


def render_survey(facts, previous_text):
    new = {f"{s.lower()}.{k}": ascii_clean(v) for s, k, v in facts}
    if previous_text is None:
        changes, first = [], True
    else:
        changes, first = diff_facts(facts_from_page(previous_text), new), False
    lines = [
        "# Site survey",
        "",
        "Written by office survey and overwritten on every run. Never edit by",
        "hand; rerun it instead. Facts only: what the machine has, not what",
        "anyone should do about it.",
    ]
    section = None
    for s, k, v in facts:
        if s != section:
            lines += ["", f"## {s}", ""]
            section = s
        lines.append(f"- {ascii_clean(k)}: {ascii_clean(v)}")
    lines += ["", "## Changes since the previous survey", ""]
    if first:
        lines.append("First survey of this office.")
    elif not changes:
        lines.append("None.")
    else:
        lines += [f"- {c}" for c in changes]
    return "\n".join(lines) + "\n", changes, first


def survey_age(page_text, now=None):
    facts = facts_from_page(page_text)
    stamp = facts.get(SURVEY_TIME_KEY)
    if not stamp:
        raise HelperError("survey page has no surveyed_at line")
    when = dt.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    now = now or dt.datetime.now(dt.timezone.utc)
    return stamp, now - when


def describe_age(delta):
    hours = int(delta.total_seconds() // 3600)
    if hours < 48:
        return f"{hours} hours old"
    return f"{hours // 24} days old"


# --- migrations -----------------------------------------------------------

def load_migrations(directory, install_version):
    """Every migration the install ships, validated and in order."""
    out = []
    for path in sorted(pathlib.Path(directory).glob("*.toml")):
        data = read_toml(path)
        version = str(data.get("version", ""))
        parse_version(version)
        if path.stem != version:
            raise HelperError(f"{path.name}: version {version} does not match its file name")
        if compare_versions(version, install_version) > 0:
            raise HelperError(f"{path.name}: migration is newer than the install ({install_version})")
        kind = data.get("kind")
        if kind not in MIGRATION_KINDS:
            raise HelperError(f"{path.name}: kind must be one of {', '.join(MIGRATION_KINDS)}")
        summary = str(data.get("summary", "")).strip()
        if not summary:
            raise HelperError(f"{path.name}: summary is required (it becomes the commit text)")
        entry = {"version": version, "kind": kind, "summary": summary}
        if kind == "script":
            script = str(data.get("script", "")).strip()
            if not script or not (path.parent / script).is_file():
                raise HelperError(f"{path.name}: script kind needs a script file beside it")
            entry["action"] = script
        else:
            goal = str(data.get("goal", "")).strip()
            if not goal:
                raise HelperError(f"{path.name}: renovation kind needs a goal")
            entry["action"] = goal
            entry["landed"] = landed_declaration(path.name, data.get("landed"))
        out.append(entry)
    out.sort(key=lambda e: parse_version(e["version"]))
    return out


LANDED_KEYS = ("paths", "profile_sections")


def landed_declaration(name, table):
    """What must be true in the office once a renovation has landed.

    office upgrade checks this on a re-run and stamps the office only
    when it holds, so no session ever edits the version stamp. At least
    one of the keys must be given: a renovation nothing can verify
    would have to be taken on trust, which is what the stamp rule is
    there to prevent."""
    if not isinstance(table, dict):
        raise HelperError(f"{name}: renovation kind needs a [landed] table "
                          f"({' and/or '.join(LANDED_KEYS)})")
    unknown = sorted(set(table) - set(LANDED_KEYS))
    if unknown:
        raise HelperError(f"{name}: unknown [landed] keys: {', '.join(unknown)}")
    out = {}
    for key in LANDED_KEYS:
        value = table.get(key, [])
        if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
            raise HelperError(f"{name}: [landed] {key} must be a list of non-empty strings")
        out[key] = [v.strip() for v in value]
    if not any(out.values()):
        raise HelperError(f"{name}: [landed] declares nothing to check")
    return out


def describe_landed(landed):
    parts = []
    if landed["paths"]:
        parts.append("these paths exist: " + ", ".join(landed["paths"]))
    if landed["profile_sections"]:
        parts.append("the profile has these sections written: " + ", ".join(landed["profile_sections"]))
    return "; ".join(parts)


def unmet_landed(landed, root):
    """The parts of a renovation's declaration that do not hold yet."""
    root = pathlib.Path(root)
    unmet = [f"missing path: {p}" for p in landed["paths"] if not (root / p).exists()]
    if landed["profile_sections"]:
        try:
            found = profile_sections((root / "profile.md").read_text(encoding="utf-8"))
        except FileNotFoundError:
            found = {}
        for heading in landed["profile_sections"]:
            if heading not in found:
                unmet.append(f"missing profile section: {heading}")
            elif not section_is_filled(found[heading]):
                unmet.append(f"blank profile section: {heading}")
    return unmet


def pending_migrations(directory, office_version, install_version):
    return [m for m in load_migrations(directory, install_version)
            if compare_versions(m["version"], office_version) > 0]


def skew(office_version, install_version, directory):
    """ahead: the office was migrated past this install.
    behind: breaking releases the office has not taken.
    current: nothing to do (additive releases need nothing)."""
    if compare_versions(office_version, install_version) > 0:
        return "ahead", []
    pending = pending_migrations(directory, office_version, install_version)
    return ("behind" if pending else "current"), pending


# --- the office's include group (bale.toml) --------------------------------

def include_group(manifest, root=None):
    """The [pack] include group that makes every pack from the office
    ship its hung items. Triggers are the office's spaces, so any pack
    whose includes touch the office engages it; pulls are the hung
    items. bale refuses a pack whose engaged group names a pull that
    does not exist, so with a root only existing paths are kept, and
    the caller hears about each one left out."""
    triggers, pulls, skipped = [], [], []
    for _key, space in sorted(manifest.get("spaces", {}).items()):
        path = space.get("path", _key)
        if root is None or (pathlib.Path(root) / path).exists():
            triggers.append(path)
        else:
            skipped.append(f"trigger {path}")
    for path in space_paths(manifest, "hung"):
        if root is None or (pathlib.Path(root) / path).exists():
            pulls.append(path)
        else:
            skipped.append(f"pull {path}")
    return {"name": "hung", "triggers": triggers, "pulls": pulls, "skipped": skipped}


def toml_list(items):
    return "[" + ", ".join(f'"{i}"' for i in items) + "]"


def render_bale_toml(group, pack_only=False):
    head = [
        "# bale's per-repo settings for this office, written by office-src.",
        "# The include group makes every pack from this office ship the hung",
        "# items: when a pack's includes touch any space, bale pulls them in.",
        "# A renovation that adds a space or hangs an item updates both lists;",
        "# office status reports when they no longer match the floor plan.",
        "",
    ]
    body = [
        "[pack]",
        f'include_group = "{group["name"]}"',
        f"include_group_triggers = {toml_list(group['triggers'])}",
        f"include_group_pulls = {toml_list(group['pulls'])}",
    ]
    return "\n".join(([] if pack_only else head) + body) + "\n"


def include_group_drift(manifest, bale_toml_path, root):
    """Differences between bale.toml's group and the floor plan."""
    path = pathlib.Path(bale_toml_path)
    if not path.is_file():
        return ["no bale.toml: packs from this office do not pull the hung items"]
    pack = read_toml(path).get("pack", {})
    want = include_group(manifest, root)
    out = []
    if not pack.get("include_group"):
        return ["bale.toml has no [pack] include group: packs do not pull the hung items"]
    for key, label in (("include_group_triggers", "triggers"), ("include_group_pulls", "pulls")):
        have, need = set(pack.get(key, [])), set(want[label])
        out += [f"{label}: missing {p}" for p in sorted(need - have)]
        out += [f"{label}: extra {p}" for p in sorted(have - need)]
    out += [f"not on disk, so left out: {s}" for s in want["skipped"]]
    return out


# --- sessions in folders ----------------------------------------------------

SID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*-\d{3}$")
PACK_SID_KEYS = ("session_id", "sid")


def sid_from_pack_report(text):
    """The minted session id in a `bale pack --json` report.

    Reads the named keys first. If neither is there, a single top-level
    string that looks like a session id is taken, with a warning, so a
    renamed key degrades loudly instead of recording nothing."""
    import json
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        raise HelperError("no pack report on stdin (did bale pack fail, or run without --json?)")
    try:
        report = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise HelperError(f"the last line on stdin is not a JSON pack report ({exc})")
    if not isinstance(report, dict):
        raise HelperError("the pack report is not a JSON object")
    for key in PACK_SID_KEYS:
        value = report.get(key)
        if isinstance(value, str) and SID_RE.match(value):
            return value
    found = [v for v in report.values() if isinstance(v, str) and SID_RE.match(v)]
    if len(set(found)) == 1:
        log(f"warning: the pack report has no {' or '.join(PACK_SID_KEYS)} key; "
            f"took the one session-id-shaped value, {found[0]}")
        return found[0]
    raise HelperError("could not find the session id in the pack report; keys seen: "
                      + ", ".join(sorted(report)))


def section_bounds(lines, heading):
    """Index of a `## heading` line and of the line that ends its section."""
    start = next((i for i, l in enumerate(lines) if l.rstrip() == f"## {heading}"), None)
    if start is None:
        return None, None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    return start, end


def record_session(folder_md, sid, words=None):
    """Add a session id to a folder's Sessions section. Returns False
    when the id is already there. The folder keeps the id and the
    occupant's few words, never what bale records about the session."""
    if not SID_RE.match(sid):
        raise HelperError(f"not a session id: {sid!r}")
    path = pathlib.Path(folder_md)
    lines = path.read_text(encoding="utf-8").splitlines()
    start, end = section_bounds(lines, "Sessions")
    if start is None:
        raise HelperError(f"{path}: no '## Sessions' section to record into")
    if any(re.match(rf"^- {re.escape(sid)}\b", l) for l in lines[start:end]):
        return False
    body = lines[start + 1:end]
    while body and not body[-1].strip():
        body.pop()
    if body and not body[-1].startswith("- "):
        body.append("")  # a list after prose needs a blank line to render as one
    entry = f"- {sid}" + (f": {ascii_escape(words)[0]}" if words else "")
    tail = [""] + lines[end:] if end < len(lines) else []
    new = lines[:start + 1] + body + [entry] + tail
    path.write_text("\n".join(new) + "\n", encoding="utf-8")
    return True


def folder_summary(folder_md, template_md):
    """(next move, number of sessions) for one folder. A Next section
    still holding the template's words has no next move written."""
    lines = pathlib.Path(folder_md).read_text(encoding="utf-8").splitlines()
    tlines = pathlib.Path(template_md).read_text(encoding="utf-8").splitlines()
    ts, te = section_bounds(tlines, "Next")
    placeholder = {l.strip() for l in tlines[ts + 1:te] if l.strip()} if ts is not None else set()
    start, end = section_bounds(lines, "Next")
    nxt = "(no Next section)"
    if start is not None:
        written = [l.strip() for l in lines[start + 1:end] if l.strip() and l.strip() not in placeholder]
        nxt = written[0].lstrip("-* ").strip() if written else "(not written yet)"
    s, e = section_bounds(lines, "Sessions")
    sessions = 0 if s is None else sum(1 for l in lines[s + 1:e] if SID_RE.match(l[2:].split(":")[0].strip()) and l.startswith("- "))
    return nxt, sessions


# --- text that lands in an office -------------------------------------------

def ascii_escape(text):
    """Lossless ASCII: anything outside ASCII becomes a \\uXXXX escape, so
    an office stays ASCII and the occupant's words stay recoverable."""
    out = text.encode("ascii", "backslashreplace").decode("ascii")
    escaped = sum(1 for ch in text if ord(ch) > 127)
    return out, escaped


def render_template(text, values):
    def sub(m):
        key = m.group(1)
        if key not in values:
            raise HelperError(f"template needs a value for {{{{{key}}}}}")
        return values[key]
    return re.sub(r"\{\{([a-z_]+)\}\}", sub, text)


def recent_notes(notepad, count):
    """The last lines written by office note, oldest first, dated."""
    out = []
    for page in sorted(pathlib.Path(notepad).glob("*.md")):
        date = page.stem[:10]
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            continue
        for line in page.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("- "):
                out.append(f"{date} {line[2:]}")
    return out[-count:] if count > 0 else []


# --- the week -------------------------------------------------------------

DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
PLAN_ONE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) (.+)$")
PLAN_SERIES_RE = re.compile(r"^- every (mon|tue|wed|thu|fri|sat|sun|day|weekday) (\d{2}:\d{2}) (.+)$", re.I)
RECORD_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2})(?: (\d{2}:\d{2}))? (.+)$")


def read_bullets(path):
    p = pathlib.Path(path)
    if not p.is_file():
        return None
    return [(n, l.rstrip()) for n, l in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1)
            if l.startswith("- ")]


def week_report(calendar, today, now_hhmm, tz):
    """This week's plan against its record. Returns (lines, gap count).

    calendar/plan.md holds what should happen: one-offs as
    `- YYYY-MM-DD HH:MM title`, series as `- every DAY HH:MM title`
    (DAY is mon..sun, day or weekday). calendar/record.md holds what
    happened: `- YYYY-MM-DD [HH:MM] title: what happened`. A planned
    item in the past with no record that day starting with its title is
    a gap. Bullets that fit neither shape are reported, never dropped."""
    today = dt.date.fromisoformat(today)
    monday = today - dt.timedelta(days=today.weekday())
    week = [monday + dt.timedelta(days=i) for i in range(7)]
    lines = [f"week of {week[0]} to {week[-1]}, times in {tz}"]
    plan = read_bullets(pathlib.Path(calendar) / "plan.md")
    record = read_bullets(pathlib.Path(calendar) / "record.md") or []
    unreadable = []
    items = []
    if plan is None:
        lines.append("calendar/plan.md does not exist yet: nothing is planned")
        plan = []
    for n, line in plan:
        m = PLAN_ONE_RE.match(line)
        if m:
            d = dt.date.fromisoformat(m.group(1))
            if d in week:
                items.append((d, m.group(2), m.group(3).strip()))
            continue
        m = PLAN_SERIES_RE.match(line)
        if m:
            which = m.group(1).lower()
            for d in week:
                if which == "day" or (which == "weekday" and d.weekday() < 5) or which == DAYS[d.weekday()]:
                    items.append((d, m.group(2), m.group(3).strip()))
            continue
        unreadable.append(f"plan.md line {n}: {line}")
    records = []
    for n, line in record:
        m = RECORD_RE.match(line)
        if not m:
            unreadable.append(f"record.md line {n}: {line}")
            continue
        records.append((dt.date.fromisoformat(m.group(1)), m.group(2) or "", m.group(3).strip()))
    used, gaps = set(), 0
    for d, hhmm, title in sorted(items):
        match = next((i for i, r in enumerate(records)
                      if r[0] == d and i not in used and r[2].lower().startswith(title.lower())), None)
        if match is not None:
            used.add(match)
            state = "recorded"
        elif (d, hhmm) < (today, now_hhmm):
            state = "GAP: nothing recorded"
            gaps += 1
        else:
            state = "planned"
        lines.append(f"{DAYS[d.weekday()].title()} {d} {hhmm} {title} [{state}]")
    if not items:
        lines.append("nothing planned this week")
    extra = [r for i, r in enumerate(records) if i not in used and r[0] in week]
    for d, hhmm, text in extra:
        lines.append(f"{DAYS[d.weekday()].title()} {d} {hhmm or '--:--'} {text} [recorded, not planned]")
    lines += [f"unreadable {u}" for u in unreadable]
    lines.append(f"gaps: {gaps}")
    return lines, gaps


# --- command line ---------------------------------------------------------

def cmd_vercmp(a):
    print(compare_versions(a.left, a.right))


def cmd_stamp(a):
    stamp = office_stamp(read_toml(a.manifest))
    print(stamp[a.field])


def cmd_get(a):
    data = read_toml(a.manifest)
    node = data
    for part in a.key.split("."):
        if not isinstance(node, dict) or part not in node:
            if a.default is not None:
                print(a.default)
                return
            raise HelperError(f"{a.manifest}: no key {a.key}")
        node = node[part]
    print(node)


def cmd_spaces(a):
    manifest = read_toml(a.manifest)
    for p in space_paths(manifest, a.prop):
        print(p)


def cmd_render_manifest(a):
    sys.stdout.write(render_manifest(read_toml(a.catalog), a.name, a.version,
                                     a.built_at, a.timezone))


def cmd_base_spaces(a):
    for key, space in read_toml(a.catalog).get("spaces", {}).items():
        if space.get("base", False):
            print(space["path"])


def cmd_set_migrated(a):
    set_migrated_to(a.manifest, a.version)


def cmd_profile_check(a):
    missing, blank = check_profile(a.profile, read_toml(a.shape))
    if not missing and not blank:
        print("complete")
        return 0
    for h in missing:
        print(f"missing: {h}")
    for h in blank:
        print(f"blank: {h}")
    return 3


def cmd_survey_render(a):
    prev = pathlib.Path(a.previous)
    previous_text = prev.read_text(encoding="utf-8", errors="replace") if prev.is_file() else None
    page, changes, first = render_survey(read_facts(a.facts), previous_text)
    pathlib.Path(a.out).write_text(page, encoding="ascii")
    if first:
        print("first survey of this office")
    elif not changes:
        print("no changes since the previous survey")
    else:
        for c in changes:
            print(c)


def cmd_survey_age(a):
    page = pathlib.Path(a.page)
    if not page.is_file():
        print("never surveyed")
        return 0
    stamp, delta = survey_age(page.read_text(encoding="utf-8", errors="replace"))
    print(f"{stamp} ({describe_age(delta)})")


def cmd_skew(a):
    state, pending = skew(a.office_version, a.install_version, a.migrations)
    print(state)
    for m in pending:
        landed = describe_landed(m["landed"]) if m["kind"] == "renovation" else ""
        print(f"{m['version']}\t{m['kind']}\t{m['action']}\t{m['summary']}\t{landed}")


def cmd_landed(a):
    for m in load_migrations(a.migrations, a.install_version):
        if m["version"] == a.version:
            if m["kind"] != "renovation":
                raise HelperError(f"migration {a.version} is not a renovation")
            unmet = unmet_landed(m["landed"], a.root)
            for line in unmet:
                print(line)
            return 3 if unmet else 0
    raise HelperError(f"no migration {a.version} in {a.migrations}")


def cmd_render_bale_toml(a):
    group = include_group(read_toml(a.manifest), a.root)
    for skip in group["skipped"]:
        log(f"warning: {skip} is not on disk, so the include group leaves it out")
    sys.stdout.write(render_bale_toml(group, a.pack_only))


def cmd_include_group_check(a):
    drift = include_group_drift(read_toml(a.manifest), a.bale_toml, a.root)
    for line in drift:
        print(line)
    return 3 if drift else 0


def cmd_pack_sid(a):
    print(sid_from_pack_report(sys.stdin.read()))


def cmd_record_session(a):
    if not record_session(a.folder_md, a.sid, a.words):
        print("already recorded")
        return 4
    print("recorded")


def cmd_folder_summary(a):
    nxt, sessions = folder_summary(a.folder_md, a.template)
    print(f"{nxt}\t{sessions}")


def cmd_ascii_escape(a):
    # Bytes in, decoded as UTF-8 whatever the locale says; a byte that is
    # not UTF-8 survives as a \\xNN escape rather than being dropped.
    out, escaped = ascii_escape(sys.stdin.buffer.read().decode("utf-8", "backslashreplace"))
    if escaped:
        log(f"kept {escaped} non-ASCII character(s) as backslash escapes; offices hold ASCII only")
    sys.stdout.write(out)


def cmd_render_template(a):
    values = dict(kv.split("=", 1) for kv in a.values)
    sys.stdout.write(render_template(pathlib.Path(a.template).read_text(encoding="utf-8"), values))


def cmd_recent_notes(a):
    for line in recent_notes(a.notepad, a.count):
        print(line)


def cmd_week(a):
    lines, gaps = week_report(a.calendar, a.today, a.now, a.tz)
    print("\n".join(lines))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_helper.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("vercmp"); p.add_argument("left"); p.add_argument("right")
    p.set_defaults(fn=cmd_vercmp)
    p = sub.add_parser("stamp"); p.add_argument("manifest")
    p.add_argument("field", choices=("built_from", "migrated_to")); p.set_defaults(fn=cmd_stamp)
    p = sub.add_parser("get"); p.add_argument("manifest"); p.add_argument("key")
    p.add_argument("--default"); p.set_defaults(fn=cmd_get)
    p = sub.add_parser("spaces"); p.add_argument("manifest")
    p.add_argument("prop", choices=("hung", "filed")); p.set_defaults(fn=cmd_spaces)
    p = sub.add_parser("render-manifest"); p.add_argument("catalog")
    for f in ("name", "version", "built_at", "timezone"):
        p.add_argument(f"--{f.replace('_', '-')}", dest=f, required=True)
    p.set_defaults(fn=cmd_render_manifest)
    p = sub.add_parser("base-spaces"); p.add_argument("catalog"); p.set_defaults(fn=cmd_base_spaces)
    p = sub.add_parser("set-migrated"); p.add_argument("manifest"); p.add_argument("version")
    p.set_defaults(fn=cmd_set_migrated)
    p = sub.add_parser("profile-check"); p.add_argument("profile"); p.add_argument("shape")
    p.set_defaults(fn=cmd_profile_check)
    p = sub.add_parser("survey-render"); p.add_argument("--facts", required=True)
    p.add_argument("--previous", required=True); p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_survey_render)
    p = sub.add_parser("survey-age"); p.add_argument("page"); p.set_defaults(fn=cmd_survey_age)
    p = sub.add_parser("skew"); p.add_argument("office_version"); p.add_argument("install_version")
    p.add_argument("migrations"); p.set_defaults(fn=cmd_skew)

    p = sub.add_parser("landed"); p.add_argument("version"); p.add_argument("migrations")
    p.add_argument("install_version"); p.add_argument("root"); p.set_defaults(fn=cmd_landed)
    p = sub.add_parser("render-bale-toml"); p.add_argument("manifest"); p.add_argument("--root")
    p.add_argument("--pack-only", action="store_true"); p.set_defaults(fn=cmd_render_bale_toml)
    p = sub.add_parser("include-group-check"); p.add_argument("manifest"); p.add_argument("bale_toml")
    p.add_argument("root"); p.set_defaults(fn=cmd_include_group_check)
    p = sub.add_parser("pack-sid"); p.set_defaults(fn=cmd_pack_sid)
    p = sub.add_parser("record-session"); p.add_argument("folder_md"); p.add_argument("sid")
    p.add_argument("--words"); p.set_defaults(fn=cmd_record_session)
    p = sub.add_parser("folder-summary"); p.add_argument("folder_md"); p.add_argument("template")
    p.set_defaults(fn=cmd_folder_summary)
    p = sub.add_parser("ascii-escape"); p.set_defaults(fn=cmd_ascii_escape)
    p = sub.add_parser("render-template"); p.add_argument("template"); p.add_argument("values", nargs="*")
    p.set_defaults(fn=cmd_render_template)
    p = sub.add_parser("recent-notes"); p.add_argument("notepad"); p.add_argument("count", type=int)
    p.set_defaults(fn=cmd_recent_notes)
    p = sub.add_parser("week"); p.add_argument("calendar"); p.add_argument("--today", required=True)
    p.add_argument("--now", required=True); p.add_argument("--tz", required=True); p.set_defaults(fn=cmd_week)

    args = ap.parse_args(argv)
    try:
        return args.fn(args) or 0
    except HelperError as exc:
        log(f"error: {exc}")
        return 1
    except OSError as exc:
        log(f"error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
