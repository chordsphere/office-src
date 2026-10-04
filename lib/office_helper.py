#!/usr/bin/env python3
"""Helpers for the office command.

The office command is bash; the parts that need a real parser (TOML,
Markdown sections, version ordering, fact diffs) live here. Standard
library only. Every subcommand prints its result on stdout, logs to
stderr with an [office] prefix, and exits 0 on success, 1 on a refusal
the caller should report, 2 on a usage or internal error, and 3 where a
subcommand documents a second outcome (an incomplete profile, an unmet
renovation declaration, include-group drift, a catalog defect, a
project in the floor plan that cannot be read, a folder whose facts
disagree, a filed page changed other than at its end, a sitting's page
refused or malformed), and 4
when record-session finds the id already recorded.
"""

import argparse
import datetime as dt
import fnmatch
import os
import pathlib
import re
import subprocess
import sys
import tarfile
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
        "# sessions change the spaces; office projects add and set write",
        "# the [projects] table. Nothing else should change it.",
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
# The office-src version the survey recorded (gather_facts in bin/office).
SURVEY_OFFICE_SRC_KEY = "office-src.version"


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


# --- the install's catalogs (share/verbs.toml, share/spaces.toml) -----------
#
# Two catalogs, one check, shared by the test suite (which refuses a
# catalog that breaks it) and office status (which reports the installed
# one). The verbs catalog carries the rule that no session kind without a
# declared landing may run unattended; the space catalog has two
# list-valued properties with different meanings, and nothing else
# cross-checks them.

VERB_KINDS = ("script", "office-session", "project-session")
SESSION_KINDS = ("office-session", "project-session")
TRIGGERS = ("manual", "before-sitting", "after-sitting", "after-build",
            "on-hold", "on-correctable-hold", "schedule")
VERB_KEYS = ("lands", "attended", "trigger")
PLACEHOLDER_RE = re.compile(r"\{[^{}]*\}")


def is_path_entry(entry):
    """A writes or lands entry is a path (or a path pattern) when, with its
    {placeholders} taken out, nothing in it is whitespace: "desk/{folder}"
    and "{project}" are paths; "the new office" is prose."""
    if not isinstance(entry, str) or not entry.strip():
        return False
    return not any(ch.isspace() for ch in PLACEHOLDER_RE.sub("", entry))


def falls_inside(lands, writes):
    """Does a lands path fall inside a writes path? Equal, or under it, one
    segment at a time; a writes segment that is only a placeholder stands
    for any segment, and placeholders elsewhere compare by position."""
    def segments(p):
        return [PLACEHOLDER_RE.sub("{}", s) for s in p.strip("/").split("/") if s]
    ls, ws = segments(lands), segments(writes)
    if len(ws) > len(ls):
        return False
    return all(w == "{}" or w == l for w, l in zip(ws, ls))


def string_list(value):
    return isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value)


def verb_catalog_problems(catalog):
    """(problems, unchecked) for a verbs catalog.

    problems: every defect, one line each, a catalog with any of them is
    refused. unchecked: the lands entries the check could not place,
    because every writes entry of that verb is prose; they are reported,
    never counted as defects."""
    problems, unchecked = [], []
    verbs = catalog.get("verbs")
    if not isinstance(verbs, dict) or not verbs:
        return ["no [verbs] table"], []
    for name, verb in sorted(verbs.items()):
        if not isinstance(verb, dict):
            problems.append(f"{name}: not a table")
            continue
        kind = verb.get("kind")
        if kind not in VERB_KINDS:
            problems.append(f"{name}: kind must be one of {', '.join(VERB_KINDS)}, not {kind!r}")
        if not isinstance(verb.get("built"), bool):
            problems.append(f"{name}: built must be true or false")
        for key in VERB_KEYS:
            if key not in verb:
                problems.append(f"{name}: no {key} key")
        writes = verb.get("writes", [])
        if not string_list(writes):
            problems.append(f"{name}: writes must be a list of non-empty strings")
            writes = []
        lands = verb.get("lands", [])
        if not string_list(lands):
            if "lands" in verb:
                problems.append(f"{name}: lands must be a list of non-empty strings")
            lands = []
        attended = verb.get("attended")
        if "attended" in verb and not isinstance(attended, bool):
            problems.append(f"{name}: attended must be true or false")
        trigger = verb.get("trigger")
        if "trigger" in verb:
            if not string_list(trigger) or not trigger:
                problems.append(f"{name}: trigger must be a non-empty list of strings")
            else:
                for t in trigger:
                    if t not in TRIGGERS:
                        problems.append(f"{name}: trigger {t!r} is not one of {', '.join(TRIGGERS)}")
        if kind in SESSION_KINDS and attended is False and not lands:
            problems.append(f"{name}: an unattended session kind with no declared landing; "
                            f"declare lands or set attended = true")
        path_writes = [w for w in writes if is_path_entry(w)]
        for entry in lands:
            if not is_path_entry(entry):
                problems.append(f"{name}: lands entry {entry!r} is prose, not a path or a pattern")
            elif not path_writes:
                unchecked.append(f"{name}: lands {entry!r} could not be placed; every writes entry is prose")
            elif not any(falls_inside(entry, w) for w in path_writes):
                problems.append(f"{name}: lands {entry!r} falls inside none of writes {path_writes}")
    return problems, unchecked


def glob_or_page(entry, space_path):
    """A filed or hung list entry names a page inside the space, or a glob
    (as git reads one) over pages inside it."""
    return (isinstance(entry, str) and entry.startswith(space_path + "/")
            and len(entry) > len(space_path) + 1 and not any(ch.isspace() for ch in entry))


def space_catalog_problems(catalog):
    """Every defect in a spaces catalog, one line each: a filed or hung
    value that is not true, false or a list of pages or globs inside the
    space; and a hung path that is also filed (a hung filed page would
    ship into every session and be append-only at once, which is a
    deliberate line, not a default)."""
    problems = []
    spaces = catalog.get("spaces")
    if not isinstance(spaces, dict) or not spaces:
        return ["no [spaces] table"]
    for name, space in sorted(spaces.items()):
        if not isinstance(space, dict) or not isinstance(space.get("path"), str) or not space["path"].strip():
            problems.append(f"{name}: needs a path")
            continue
        path = space["path"].rstrip("/")
        values = {}
        for prop in ("hung", "filed"):
            value = space.get(prop, False)
            if isinstance(value, bool):
                values[prop] = value
            elif isinstance(value, list):
                bad = [v for v in value if not glob_or_page(v, path)]
                for v in bad:
                    problems.append(f"{name}: {prop} entry {v!r} is not a page or a glob inside {path}/")
                values[prop] = [v for v in value if v not in bad]
            else:
                problems.append(f"{name}: {prop} must be true, false or a list of paths, not {value!r}")
                values[prop] = False
        hung, filed = values["hung"], values["filed"]
        if hung is True and filed is True:
            problems.append(f"{name}: the whole space is hung and filed at once")
        elif hung is True and isinstance(filed, list):
            for f in filed:
                problems.append(f"{name}: filed {f!r} is inside a space hung whole")
        elif isinstance(hung, list) and filed is True:
            for h in hung:
                problems.append(f"{name}: hung {h!r} is inside a space filed whole")
        elif isinstance(hung, list) and isinstance(filed, list):
            for h in hung:
                for f in filed:
                    if h == f or fnmatch.fnmatchcase(h, f) or fnmatch.fnmatchcase(f, h):
                        problems.append(f"{name}: hung {h!r} is also filed ({f!r})")
    return problems


# --- sessions in folders ----------------------------------------------------

SID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*-\d{3}$")
# bale's key contract for `bale pack --json` (the format_pack_json
# docstring in bale's bin/bale_report.py) names the session id `sid`, a
# stable key; share/bale-consumption.toml records the read.
PACK_SID_KEY = "sid"


def sid_from_pack_report(text):
    """The minted session id in a `bale pack --json` report: its `sid`
    key, which bale's pack contract names. Anything else refuses and
    names the keys it saw, so a moved key fails loudly, never by guess."""
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
    value = report.get(PACK_SID_KEY)
    if isinstance(value, str) and SID_RE.match(value):
        return value
    if PACK_SID_KEY in report:
        raise HelperError(f"the pack report's {PACK_SID_KEY} is not a session id: {value!r}")
    raise HelperError(f"the pack report has no {PACK_SID_KEY} key, which bale's pack contract names; "
                      "keys seen: " + ", ".join(sorted(report)))


def folder_session_lines(folder_md):
    """(sid, words) for each id line in a folder's Sessions section, in
    order. Lines that are not `- SID[: words]` are not sessions."""
    lines = pathlib.Path(folder_md).read_text(encoding="utf-8").splitlines()
    start, end = section_bounds(lines, "Sessions")
    out = []
    if start is None:
        return out
    for line in lines[start + 1:end]:
        if not line.startswith("- "):
            continue
        sid, _, words = line[2:].partition(":")
        if SID_RE.match(sid.strip()):
            out.append((sid.strip(), words.strip()))
    return out


# --- projects this office scopes ------------------------------------------

PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def expand_project_path(path):
    """A [projects] path on this machine: absolute, or ~-relative to the
    running user's home. Anything else is refused, because a relative
    path would mean something different from every directory."""
    if path.startswith("~/") or path == "~":
        return pathlib.Path(os.path.expanduser(path))
    if path.startswith("/"):
        return pathlib.Path(path)
    raise HelperError(f"a project path must be absolute or start with ~/, not {path!r}")


def read_projects(manifest):
    """The floor plan's [projects] table as a list of entries sorted by
    name, or None when the office has no table (it scopes nothing).

    Each entry is a dict: name, path (as written), resolved (a Path, or
    None) and problem (None, or why the entry cannot be read). A broken
    entry is reported, never dropped."""
    table = manifest.get("projects")
    if table is None:
        return None
    if not isinstance(table, dict):
        raise HelperError("the floor plan's projects is not a table")
    out = []
    for name, entry in sorted(table.items()):
        item = {"name": name, "path": None, "resolved": None, "problem": None,
                "rides": [], "after_land": [], "declaration_problems": []}
        if not PROJECT_NAME_RE.match(name):
            item["problem"] = "the name must be letters, digits, dash or underscore"
        elif not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            item["problem"] = 'no path = "..." in its entry'
        else:
            item["path"] = entry["path"]
            try:
                item["resolved"] = expand_project_path(entry["path"])
            except HelperError as exc:
                item["problem"] = str(exc)
        if isinstance(entry, dict):
            # The two declarations are optional; a table without them is
            # valid, and one that does not read is reported beside the
            # project, never taken as empty and never fatal to the reads.
            for key in DECLARATION_KEYS:
                value = entry.get(key, [])
                if string_list(value):
                    item[key] = list(value)
                else:
                    item["declaration_problems"].append(f"{key} is not a list of non-empty strings")
        out.append(item)
    return out


# --- what rides with a project, and what runs after it lands ------------------
#
# Two optional keys in a project's [projects.NAME] table, set through
# `office projects` (a wizard, with flag twins) and never by hand or in
# the project's own repo: what rides is office context, and a project's
# audience must not see the office's choices.
#
#   rides       paths on this machine whose context rides beside every
#               session on the project: a directory inside another repo,
#               a whole repo, or a file; absolute or ~/
#   after_land  commands run in the project's repo after one of its
#               sessions lands (office land runs them, in order, once bale
#               has applied the session; never after a HOLD)

DECLARATION_KEYS = ("rides", "after_land")


def check_ride(path):
    """(stored, resolved) for a path that rides with a project: absolute
    or ~/, and on this machine now."""
    text = path.strip()
    if not text:
        raise HelperError("a path that rides is empty")
    stored = text.rstrip("/") or "/"
    resolved = expand_project_path(stored)
    if not resolved.exists():
        raise HelperError(f"no such path on this machine: {stored}")
    return stored, resolved


def check_after_land(command):
    """A command run in the project's repo after a session lands: one
    non-empty line."""
    text = command.strip()
    if not text:
        raise HelperError("an after-land action is empty")
    if "\n" in text or "\r" in text:
        raise HelperError(f"an after-land action is one line: {command!r}")
    return text


def table_span(lines, name):
    """(start, end) of [projects.NAME] in the floor plan's lines: the
    header's index and the index of the next table header (or the end).
    None when the table is not there."""
    header = f"[projects.{name}]"
    start = next((i for i, l in enumerate(lines) if l.strip() == header), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
    return start, end


def set_declarations(manifest_path, name, rides=None, after_land=None):
    """Write a project's declarations, keeping every other byte of the
    floor plan. A list replaces the key's value; [] removes the key;
    None leaves it as it is. Returns the project's entry as it reads
    back. Refuses a project the table does not list, a key written over
    several lines (not the shape this writes), and a value that does
    not check."""
    if not PROJECT_NAME_RE.match(name):
        raise HelperError(f"a project name must be letters, digits, dash or underscore: {name!r}")
    want = {}
    if rides is not None:
        seen = []
        for r in rides:
            stored, _ = check_ride(r)
            if stored not in seen:
                seen.append(stored)
        want["rides"] = seen
    if after_land is not None:
        want["after_land"] = [check_after_land(c) for c in after_land]
    path = pathlib.Path(manifest_path)
    text = path.read_text(encoding="ascii")
    lines = text.splitlines()
    span = table_span(lines, name)
    projects = read_projects(read_toml(path)) or []
    if span is None or name not in [p["name"] for p in projects]:
        raise HelperError(f"no project named {name} in this office's [projects] "
                          f"(it lists: {', '.join(p['name'] for p in projects) or 'none'}); "
                          "office projects add NAME PATH adds one")
    start, end = span
    body = lines[start + 1:end]
    for key, value in want.items():
        at = [i for i, l in enumerate(body) if re.match(rf"^\s*{key}\s*=", l)]
        for i in at:
            if not body[i].rstrip().endswith("]"):
                raise HelperError(f"[projects.{name}] writes {key} over several lines, which office projects "
                                  "does not rewrite; put it on one line first")
        new_line = f"{key} = [" + ", ".join(toml_basic_string(v) for v in value) + "]"
        if at:
            body[at[0]] = new_line
            for i in reversed(at[1:]):
                del body[i]
            if not value:
                del body[at[0]]
        elif value:
            # After the last key line, before the blank lines that end
            # the table.
            last = max((i for i, l in enumerate(body) if l.strip() and not l.lstrip().startswith("#")), default=-1)
            body.insert(last + 1, new_line)
    new = lines[:start + 1] + body + lines[end:]
    out = "\n".join(new) + ("\n" if text.endswith("\n") or not text else "")
    path.write_text(out, encoding="ascii")
    entry = next(p for p in read_projects(read_toml(path)) if p["name"] == name)
    for key, value in want.items():
        if entry[key] != value:
            raise HelperError(f"{path}: {key} did not read back as written; the floor plan needs a look")
    return entry


def describe_declarations(entry):
    """Lines for office projects: what rides and what runs after landing,
    each ride-along checked on this machine."""
    out = []
    for r in entry["rides"]:
        try:
            resolved = expand_project_path(r)
            where = "" if resolved.exists() else "  (NOT ON THIS MACHINE)"
        except HelperError as exc:
            where = f"  ({exc})"
        out.append(f"rides: {r}{where}")
    for c in entry["after_land"]:
        out.append(f"after it lands: {c}")
    out += [f"declaration problem: {p}" for p in entry["declaration_problems"]]
    return out


def check_project_dir(resolved):
    """(ok, text): is the path the top of a git repo that bale has run in
    (a .bale/ directory) or is set up for (a bale.toml)? The text says
    which it found, or what is wrong. Existence checks only: nothing
    inside .bale/ is read."""
    p = pathlib.Path(resolved)
    if not p.exists():
        return False, f"no such directory on this machine: {p}"
    if not p.is_dir():
        return False, f"not a directory: {p}"
    try:
        top = subprocess.run(["git", "-C", str(p), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"could not ask git about {p}: {exc}"
    if top.returncode != 0:
        return False, f"not a git repo: {p}"
    if pathlib.Path(top.stdout.strip()).resolve() != p.resolve():
        return False, f"{p} is inside the git repo at {top.stdout.strip()}; name the repo's top instead"
    has_dir, has_toml = (p / ".bale").is_dir(), (p / "bale.toml").is_file()
    if not has_dir and not has_toml:
        return False, (f"{p} is a git repo bale has not run in: no .bale/ directory and no bale.toml "
                       "(bale pack there once, or bale config init)")
    found = " and ".join(x for x, y in ((".bale/", has_dir), ("bale.toml", has_toml)) if y)
    missing = " and ".join(x for x, y in ((".bale/", has_dir), ("bale.toml", has_toml)) if not y)
    return True, f"a git repo with {found}" + (f", no {missing}" if missing else "")


def toml_basic_string(text):
    """A TOML basic string that keeps the floor plan ASCII: quotes,
    backslashes and control characters escaped, anything outside ASCII
    as a \\uXXXX escape, which a TOML reader turns back into the same
    character."""
    out = []
    for ch in text:
        o = ord(ch)
        if ch in ('"', "\\"):
            out.append("\\" + ch)
        elif o < 0x20 or o == 0x7F:
            out.append(f"\\u{o:04X}")
        elif o > 0x7F:
            out.append(f"\\u{o:04X}" if o <= 0xFFFF else f"\\U{o:08X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def add_project(manifest_path, name, path):
    """Append [projects.NAME] with its path to the floor plan, keeping
    every other byte. Returns (stored path, what the check found).

    A relative path is resolved against the working directory and stored
    absolute. Refuses a bad name, a name already listed, a path another
    entry already names, and a path that is not a repo bale runs in."""
    if not PROJECT_NAME_RE.match(name):
        raise HelperError(f"a project name must be letters, digits, dash or underscore: {name!r}")
    if not path.strip():
        raise HelperError("the project path is empty")
    stored = path if (path.startswith("/") or path.startswith("~/")) else str(pathlib.Path(os.path.abspath(path)))
    stored = stored.rstrip("/") or "/"
    resolved = expand_project_path(stored)
    manifest = read_toml(manifest_path)
    existing = read_projects(manifest) or []
    for item in existing:
        if item["name"] == name:
            raise HelperError(f"{name} is already in this office's [projects], at {item['path']}")
        if item["resolved"] is not None and item["resolved"].resolve() == resolved.resolve():
            raise HelperError(f"{stored} is already in this office's [projects], as {item['name']}")
    ok, found = check_project_dir(resolved)
    if not ok:
        raise HelperError(found)
    text = pathlib.Path(manifest_path).read_text(encoding="ascii")
    block = []
    if not text.endswith("\n"):
        block.append("")
    if manifest.get("projects") is None:
        block += ["", "# The projects this office scopes on this machine: a name and the path",
                  "# of its repo, absolute or ~-relative, and what rides with each and runs",
                  "# after it lands. office projects add and set write them."]
    block += ["", f"[projects.{name}]", f"path = {toml_basic_string(stored)}"]
    pathlib.Path(manifest_path).write_text(text + "\n".join(block) + "\n", encoding="ascii")
    return stored, found


def project_spec(spec, taken=()):
    """(name, stored path, what the check found) for one `[NAME=]PATH`
    office init was given: the name defaults to the directory's name made
    a slug, a relative path is resolved against the working directory, and
    the path must be the top of a git repo bale runs in. Refuses a bad
    name, a name in taken, or a path that does not check, before anything
    is built."""
    name, sep, path = spec.partition("=")
    if not sep or not PROJECT_NAME_RE.match(name):
        name, path = "", spec
    path = path.strip()
    if not path:
        raise HelperError(f"--project {spec!r}: no path")
    stored = path if (path.startswith("/") or path.startswith("~/") or path == "~") else str(pathlib.Path(os.path.abspath(path)))
    stored = stored.rstrip("/") or "/"
    resolved = expand_project_path(stored)
    if not name:
        name = re.sub(r"-+", "-", re.sub(r"[^a-z0-9]", "-", resolved.name.lower())).strip("-")
    if not PROJECT_NAME_RE.match(name or "-"):
        raise HelperError(f"--project {spec!r}: no name can be made from the path; give one as NAME=PATH")
    if name in taken:
        raise HelperError(f"--project {spec!r}: the name {name} is given twice; give one as NAME=PATH")
    ok, found = check_project_dir(resolved)
    if not ok:
        raise HelperError(f"--project {spec!r}: {found}")
    return name, stored, found


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


# --- the desk's fields, statuses and history ----------------------------------
#
# A folder carries its facts as field lines under its title, one field
# per line, written by the office command only (doctrine section 5; the
# drafting-table blueprint's section 2). Every vocabulary a verb reads is
# closed and lives here, so the wizard offers it, a flag is checked
# against it and office status checks what the folders say.

# In the order the field block writes them.
FIELD_KEYS = ("number", "status", "queued", "class", "size", "lane", "source",
              "blueprint", "linked", "after", "serializes after", "consumer")
# The fields a folder may carry more than once, one line each.
MULTI_FIELDS = ("linked", "after", "serializes after", "consumer")
SIZES = ("small", "medium", "high")
# bale's work classes, as bale pack's --work-class takes them; the read
# side joins a folder to bale's telemetry by it.
WORK_CLASSES = ("code", "doc", "contract-doc", "meta", "mixed")
DESK_STATUSES = ("candidate", "queued", "open")
CABINET_STATUSES = ("done", "absorbed", "split", "retired")
STATUSES = DESK_STATUSES + CABINET_STATUSES
# The History verbs, a closed set. `candidate` is the line office open
# --candidate writes, the one state the blueprint's set had no verb for.
# `ended` is the line office land writes when it ends a read-only sitting
# (bale unlock); it changes no status.
HISTORY_VERBS = ("candidate", "queued", "opened", "ratified", "gated", "cleared", "grown",
                 "re-scoped", "corrected", "ruled", "carried", "consumed", "done",
                 "absorbed", "split", "retired", "reopened", "note", "ended")
# The state-changing verbs and the status each leaves the folder in:
# candidate -> queued -> open -> done; any desk status -> absorbed,
# split or retired; done -> reopened -> open.
STATE_VERBS = {"candidate": "candidate", "queued": "queued", "opened": "open",
               "reopened": "open", "done": "done", "absorbed": "absorbed",
               "split": "split", "retired": "retired"}

ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
FOLDER_REF_RE = re.compile(r"^(?:folder\s+|#)?(\d+)$", re.I)
GATE_RE = re.compile(r"^(folder|agenda|blueprint|ruling)\s+(\S+)$", re.I)
FIELD_LINE_RE = re.compile(r"^- ([a-z][a-z ]*?): (.*)$")
HISTORY_LINE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) ([a-z-]+):(?: (.*))?$")
RATIFIED_RE = re.compile(r"^- (\S+) ratified (\d{4}-\d{2}-\d{2})(?:, except: (.*))?$")

# What each field means, for the wizard's `?` and office open --help.
FIELD_HELP = {
    "title": "the folder's name in words, its first line. The slug, its directory name after the "
             "date, is made from the title when you do not give one.",
    "number": "the folder's short citation, `folder N`. Minted by office open as one more than the "
              "highest number on the desk and in the filing cabinet; never reused, never typed.",
    "status": "where the job stands: candidate, queued, open (desk); done, absorbed, split, retired "
              "(filing cabinet). Written by the verbs, never asked.",
    "queued": "the day the job entered the desk, in the office's timezone. Written by office open.",
    "class": "bale's work class for the job's sessions: " + ", ".join(WORK_CLASSES)
             + ". The read side joins the folder to bale's telemetry by it.",
    "size": "how big the job is: " + ", ".join(SIZES) + ". The desk puts small jobs first when "
            "nothing else orders them.",
    "lane": "the project and the paths the job will touch, as `project: paths`, e.g. "
            "`office-src: bin/, lib/`. The folder's forecast in waiting.",
    "source": "where the job came from, in one form: `proposal SID #n`, `rider N`, `ruling ID`, "
              "`blueprint ID`, a notepad page (`notepad/...`), or a person (whose words go in Asked).",
    "blueprint": "the blueprint the folder belongs to, by its id, YYYY-MM-DD-slug.",
    "linked": "a folder this one relates to without waiting for it: `folder N`.",
    "after": "do not open this before X is done. X is `folder N` (a bare number means a folder), "
             "`blueprint ID`, `agenda N` or `ruling ID`. Give it more than once for more gates.",
    "serializes after": "may run before or after folder N, never beside it (their forecasts "
                        "overlap); when both are ready, folder N goes first. `folder N`.",
    "consumer": "parked for a named consumer that will carry it: `blueprint ID` or `folder N`.",
    "sid": "a bale session id, YYYY-MM-DD-slug-NNN, as bale pack reports it.",
}


def one_line(value, key):
    text = " ".join(str(value).split())
    if not text:
        raise HelperError(f"{key} is empty")
    return ascii_escape(text)[0]


def normalize_gate(value, key, kinds):
    """`folder N` (a bare number is a folder), `agenda N`, `blueprint ID`
    or `ruling ID`, whichever of those `kinds` the field takes."""
    text = " ".join(str(value).split())
    m = FOLDER_REF_RE.match(text)
    if m and "folder" in kinds:
        return f"folder {int(m.group(1))}"
    m = GATE_RE.match(text)
    if m:
        kind, ref = m.group(1).lower(), m.group(2)
        if kind in kinds:
            if kind in ("folder", "agenda") and ref.isdigit():
                return f"{kind} {int(ref)}"
            if kind in ("blueprint", "ruling") and ID_RE.match(ref):
                return f"{kind} {ref}"
    forms = {"folder": "folder N", "agenda": "agenda N", "blueprint": "blueprint YYYY-MM-DD-slug",
             "ruling": "ruling YYYY-MM-DD-slug"}
    raise HelperError(f"{key} takes " + " or ".join(forms[k] for k in kinds) + f", not {text!r}")


def normalize_field(key, value):
    """A field's value as a folder writes it, or HelperError saying what
    the field takes (the words the wizard and the flag refusal print)."""
    text = " ".join(str(value).split())
    if key == "size":
        if text.lower() in SIZES:
            return text.lower()
        raise HelperError(f"size is one of {', '.join(SIZES)}, not {text!r}")
    if key == "class":
        if text.lower() in WORK_CLASSES:
            return text.lower()
        raise HelperError(f"class is one of {', '.join(WORK_CLASSES)} (bale's work classes), not {text!r}")
    if key == "status":
        if text in STATUSES:
            return text
        raise HelperError(f"status is one of {', '.join(STATUSES)}, not {text!r}")
    if key == "after":
        return normalize_gate(text, key, ("folder", "blueprint", "agenda", "ruling"))
    if key in ("serializes after", "linked"):
        return normalize_gate(text, key, ("folder",))
    if key == "consumer":
        return normalize_gate(text, key, ("blueprint", "folder"))
    if key == "blueprint":
        bare = text[len("blueprint "):].strip() if text.lower().startswith("blueprint ") else text
        if ID_RE.match(bare):
            return bare
        raise HelperError(f"blueprint takes a blueprint id, YYYY-MM-DD-slug, not {text!r}")
    if key == "sid":
        if SID_RE.match(text):
            return text
        raise HelperError(f"not a session id (YYYY-MM-DD-slug-NNN): {text!r}")
    if key in ("title", "lane", "source"):
        return one_line(text, key)
    raise HelperError(f"no field named {key!r}")


def parse_folder(text):
    """Everything a verb reads from a folder.md: its title, its field
    lines (key -> [values], in order), its History (date, verb, text)
    and the History lines that do not read, and its session ids.

    Fields are the `- key: value` lines between the title and the first
    section whose key is one of FIELD_KEYS; a folder from before the
    field block has none, and every reader takes that as unknown, never
    as a value."""
    lines = text.splitlines()
    title = lines[0][2:].strip() if lines and lines[0].startswith("# ") else None
    first = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
    fields = {}
    for line in lines[1:first]:
        m = FIELD_LINE_RE.match(line)
        if m and m.group(1) in FIELD_KEYS:
            fields.setdefault(m.group(1), []).append(m.group(2).strip())
    history, unreadable = [], []
    start, end = section_bounds(lines, "History")
    has_history = start is not None
    if start is not None:
        for line in lines[start + 1:end]:
            if not line.startswith("- "):
                continue
            m = HISTORY_LINE_RE.match(line)
            if m:
                history.append((m.group(1), m.group(2), (m.group(3) or "").strip()))
            else:
                unreadable.append(line)
    sids, ratified = [], {}
    start, end = section_bounds(lines, "Sessions")
    if start is not None:
        for line in lines[start + 1:end]:
            m = RATIFIED_RE.match(line)
            if m and SID_RE.match(m.group(1)):
                ratified[m.group(1)] = (m.group(2), m.group(3))
                continue
            if line.startswith("- "):
                sid = line[2:].partition(":")[0].strip()
                if SID_RE.match(sid):
                    sids.append(sid)
    return {"title": title, "fields": fields, "history": history, "history_unreadable": unreadable,
            "has_history": has_history,
            "has_status_line": "status" in fields, "sids": sids, "ratified": ratified}


def folder_number(fields):
    """(number or None, problem or None) from a folder's number line."""
    values = fields.get("number")
    if not values:
        return None, None
    if len(values) > 1:
        return None, f"{len(values)} number lines"
    if not values[0].isdigit() or int(values[0]) < 1:
        return None, f"number line is not a number: {values[0]!r}"
    return int(values[0]), None


def read_folders(root):
    """Every folder on the desk and in the filing cabinet, desk first,
    each by name: a dict with space, name, rel (space/name), path (its
    folder.md), problem (None, or why it cannot be read) and, when it
    reads, the parse_folder keys plus number, number_problem, status and
    last_state (date, verb, text of the last state-changing History
    line, or None)."""
    out = []
    for space in ("desk", "filing-cabinet"):
        base = pathlib.Path(root) / space
        if not base.is_dir():
            continue
        for d in sorted(p for p in base.iterdir() if p.is_dir()):
            f = {"space": space, "name": d.name, "rel": f"{space}/{d.name}", "path": d / "folder.md",
                 "problem": None}
            try:
                f.update(parse_folder(f["path"].read_text(encoding="utf-8")))
            except FileNotFoundError:
                f["problem"] = "no folder.md"
            except (OSError, UnicodeDecodeError) as exc:
                f["problem"] = f"folder.md cannot be read ({exc.__class__.__name__}: {exc})"
            if f["problem"] is None:
                f["number"], f["number_problem"] = folder_number(f["fields"])
                f["status"] = (f["fields"].get("status") or [None])[0]
                states = [h for h in f["history"] if h[1] in STATE_VERBS]
                f["last_state"] = states[-1] if states else None
            out.append(f)
    return out


def cite(folder):
    """How a folder is cited: `folder N`, or by its directory name when
    it has no number (a folder from before numbers are never numbered)."""
    return f"folder {folder['number']}" if folder.get("number") else folder["name"]


def next_number(root):
    """(one more than the highest number on the desk and in the filing
    cabinet, the folders skipped for having no number line). A number
    line that does not read refuses: minting past it could reuse it."""
    highest, unnumbered = 0, []
    for f in read_folders(root):
        if f["problem"]:
            unnumbered.append(f"{f['rel']} ({f['problem']})")
            continue
        if f["number_problem"]:
            raise HelperError(f"{f['rel']}/folder.md: {f['number_problem']}; no number is minted "
                              "until it reads (office status lists every folder's problems)")
        if f["number"] is None:
            unnumbered.append(f["rel"])
        else:
            highest = max(highest, f["number"])
    return highest + 1, unnumbered


def folders_by_number(folders):
    out = {}
    for f in folders:
        if not f["problem"] and f.get("number"):
            out.setdefault(f["number"], []).append(f)
    return out


def append_line_to_section(lines, heading, entry):
    """lines with entry added as the last line of the section, before its
    trailing blank lines; None when the folder has no such section."""
    start, end = section_bounds(lines, heading)
    if start is None:
        return None
    body = lines[start + 1:end]
    while body and not body[-1].strip():
        body.pop()
    if body and not body[-1].startswith("- "):
        body.append("")  # a list after prose needs a blank line to render as one
    tail = [""] + lines[end:] if end < len(lines) else []
    return lines[:start + 1] + body + [entry] + tail


def history_line(day, verb, text):
    if verb not in HISTORY_VERBS:
        raise HelperError(f"{verb!r} is not a History verb ({', '.join(HISTORY_VERBS)})")
    dt.date.fromisoformat(day)
    text = one_line(text, "the History line's text")
    return f"- {day} {verb}: {text}"


def folder_event(folder_md, day, verb, text, status=None):
    """Append one History line and, when status is given, set the status
    line to it: the only two edits a verb makes to a folder's facts.

    A folder from before the field block has no status line and no
    History section, and gets neither: nothing is added to a folder that
    lacks it. Returns (old status or None, history written: bool)."""
    path = pathlib.Path(folder_md)
    lines = path.read_text(encoding="utf-8").splitlines()
    old = None
    if status is not None:
        if status not in STATUSES:
            raise HelperError(f"not a status: {status!r}")
        first = next((i for i, l in enumerate(lines) if l.startswith("## ")), len(lines))
        for i in range(1, first):
            m = FIELD_LINE_RE.match(lines[i])
            if m and m.group(1) == "status":
                old = m.group(2).strip()
                lines[i] = f"- status: {status}"
                break
    new = append_line_to_section(lines, "History", history_line(day, verb, text))
    wrote = new is not None
    path.write_text("\n".join(new if wrote else lines) + "\n", encoding="utf-8")
    return old, wrote


def record_session_opening(folder_md, sid, day, words=None):
    """record_session, and with the first sid a folder records, the
    `opened` History line and status open, when the folder is a
    candidate or queued. Returns (recorded, what changed, in words)."""
    before = parse_folder(pathlib.Path(folder_md).read_text(encoding="utf-8"))
    if not record_session(folder_md, sid, words):
        return False, None
    status = (before["fields"].get("status") or [None])[0]
    if before["sids"] or status not in ("candidate", "queued"):
        return True, None
    folder_event(folder_md, day, "opened", sid, status="open")
    return True, f"status {status} -> open; History: {day} opened: {sid}"


def ratify_session(folder_md, sid, day, except_text=None):
    """Write `- SID ratified DAY[, except: TEXT]` right under the sid's
    line in Sessions: the planner's half of a session whose worker
    flagged judgment calls, one line per session."""
    if not SID_RE.match(sid):
        raise HelperError(f"not a session id: {sid!r}")
    dt.date.fromisoformat(day)
    path = pathlib.Path(folder_md)
    lines = path.read_text(encoding="utf-8").splitlines()
    start, end = section_bounds(lines, "Sessions")
    if start is None:
        raise HelperError(f"{path}: no '## Sessions' section")
    at = None
    for i in range(start + 1, end):
        m = RATIFIED_RE.match(lines[i])
        if m and m.group(1) == sid:
            raise HelperError(f"{sid} is already ratified in this folder: {lines[i][2:]}")
        if lines[i].startswith("- ") and lines[i][2:].partition(":")[0].strip() == sid:
            at = i
    if at is None:
        raise HelperError(f"{sid} is not recorded in this folder; record it first: office sessions FOLDER {sid}")
    entry = f"- {sid} ratified {day}"
    if except_text is not None:
        entry += f", except: {one_line(except_text, '--except')}"
    lines.insert(at + 1, entry)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return entry[2:]


# --- office status's checks over the desk and the filed pages ------------------

def folder_check(root):
    """(problems, counts) over every folder: a status outside the
    vocabulary or in the wrong space, a status its History's last
    state-changing line does not agree with, a History line that does
    not read or uses a verb outside the set, and number lines that do
    not read or are minted twice. A folder with no status line is from
    before the field block: counted, never a problem."""
    folders = read_folders(root)
    problems, counts = [], {"folders": len(folders), "no_status": 0}
    for number, same in sorted(folders_by_number(folders).items()):
        if len(same) > 1:
            problems.append(f"folder {number} is minted twice: " + ", ".join(f["rel"] for f in same))
    for f in folders:
        if f["problem"]:
            problems.append(f"{f['rel']}: {f['problem']}")
            continue
        if f["number_problem"]:
            problems.append(f"{f['rel']}: {f['number_problem']}")
        for line in f["history_unreadable"]:
            problems.append(f"{f['rel']}: a History line that is not `- YYYY-MM-DD verb: text`: {line}")
        for day, verb, _ in f["history"]:
            if verb not in HISTORY_VERBS:
                problems.append(f"{f['rel']}: History verb {verb!r} ({day}) is not one of the set")
        if len(f["fields"].get("status", [])) > 1:
            problems.append(f"{f['rel']}: {len(f['fields']['status'])} status lines")
        status = f["status"]
        if status is None:
            counts["no_status"] += 1
            continue
        if status not in STATUSES:
            problems.append(f"{f['rel']}: status {status!r} is not one of {', '.join(STATUSES)}")
            continue
        home = "desk" if status in DESK_STATUSES else "filing-cabinet"
        if f["space"] != home:
            problems.append(f"{f['rel']}: status {status} belongs in {home}/")
        last = f["last_state"]
        if last is None:
            problems.append(f"{f['rel']}: status {status}, and no History line says how it got there")
        elif STATE_VERBS[last[1]] != status:
            problems.append(f"{f['rel']}: status {status}, but its History's last state-changing line is "
                            f"`{last[0]} {last[1]}` ({STATE_VERBS[last[1]]})")
    return problems, counts


def filed_pages(manifest):
    """The pathspecs of the filed pages the floor plan lists, less the
    filing cabinet: a filed folder moves whole and the office command
    adds lines inside its sections, which no byte prefix expresses
    (doctrine section 15), so it keeps its own rule."""
    out = []
    for key, space in sorted(manifest.get("spaces", {}).items()):
        if key == "filing-cabinet":
            continue
        value = space.get("filed", False)
        if value is True:
            out.append(space.get("path", key))
        elif isinstance(value, list):
            out.extend(str(v) for v in value)
    return out


def git_out(root, *args, text=True):
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=text, timeout=120)
    if proc.returncode != 0:
        err = proc.stderr if text else proc.stderr.decode("utf-8", "replace")
        raise HelperError(f"git {' '.join(args[:2])} failed in {root}: {err.strip() or 'no message'}")
    return proc.stdout


def first_difference(old, new):
    n = min(len(old), len(new))
    return next((i for i in range(n) if old[i] != new[i]), n)


def append_problem(old, new):
    """None when new is old with bytes added at its end, else what broke."""
    if new.startswith(old):
        return None
    if len(new) < len(old) and old.startswith(new):
        return f"cut to {len(new)} bytes from {len(old)}"
    return f"changed bytes already filed (first difference at byte {first_difference(old, new)} of {len(old)})"


def append_check(root, rel):
    """None when the page at rel (relative to the repo at root) is new
    to git or grows its committed bytes only at its end, else what
    broke. The check doctrine section 15 asks of a script that appends
    to filed paper, made before it commits: office note runs it, and
    the drafting-table's recording verbs will. A root that is not a git
    repo has nothing filed to compare against, which is not a refusal."""
    root = pathlib.Path(root)
    inside = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                            capture_output=True, text=True, timeout=30)
    if inside.returncode != 0:
        return None
    if subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "-q", "HEAD"],
                      capture_output=True).returncode != 0:
        return None
    shown = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{rel}"], capture_output=True, timeout=60)
    if shown.returncode != 0:
        return None  # not in the last commit: a new page has no base
    disk = root / rel
    if not disk.is_file():
        return "the page is committed but missing from disk"
    return append_problem(shown.stdout, disk.read_bytes())


def filed_history_check(root):
    """(problems, counts): every commit, first-parent, whose diff to a
    filed page does more than append at its end, and every uncommitted
    change that would. The net for a hand edit that went through
    neither bale nor a script (the blueprint's section 5.4)."""
    root = pathlib.Path(root)
    specs = filed_pages(read_toml(root / "floor-plan" / "manifest.toml"))
    counts = {"specs": specs, "commits": 0, "pages": 0}
    if not specs:
        return [], counts
    git_out(root, "rev-parse", "--is-inside-work-tree")
    if subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "-q", "HEAD"],
                      capture_output=True).returncode != 0:
        return [], counts
    log = git_out(root, "log", "--first-parent", "--reverse", "--no-renames", "--raw", "--no-abbrev",
                  "--format=commit %H %ad", "--date=short", "--", *specs)
    entries, commit = [], None
    for line in log.splitlines():
        if line.startswith("commit "):
            _, sha, day = line.split(" ", 2)
            commit = (sha, day)
            counts["commits"] += 1
        elif line.startswith(":") and commit:
            meta, _, path = line.partition("\t")
            parts = meta[1:].split()
            entries.append((commit, parts[2], parts[3], parts[4], path))
    blobs = {}
    wanted = sorted({s for e in entries for s in (e[1], e[2]) if set(s) != {"0"}})
    if wanted:
        batch = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"], input=("\n".join(wanted) + "\n").encode(),
                               capture_output=True, timeout=300)
        data, pos = batch.stdout, 0
        for sha in wanted:
            nl = data.index(b"\n", pos)
            header = data[pos:nl].split()
            if len(header) < 3 or header[1] == b"missing":
                raise HelperError(f"git has no object {sha} in {root}")
            size = int(header[2])
            blobs[sha] = data[nl + 1:nl + 1 + size]
            pos = nl + 1 + size + 1
    problems, pages = [], set()
    for (sha, day), old, new, status, path in entries:
        pages.add(path)
        where = f"{sha[:10]} {day} {path}"
        if status.startswith("D"):
            problems.append(f"{where}: removed a filed page")
        elif status.startswith("M"):
            why = append_problem(blobs[old], blobs[new])
            if why:
                problems.append(f"{where}: {why}")
        elif status.startswith("T"):
            problems.append(f"{where}: changed a filed page's type")
    changed = git_out(root, "diff", "--name-only", "--no-renames", "HEAD", "--", *specs).splitlines()
    for path in changed:
        disk = root / path
        try:
            old = git_out(root, "show", f"HEAD:{path}", text=False)
        except HelperError:
            continue
        if not disk.is_file():
            problems.append(f"uncommitted {path}: a filed page is missing from disk")
            continue
        why = append_problem(old, disk.read_bytes())
        if why:
            problems.append(f"uncommitted {path}: {why}")
    counts["pages"] = len(pages)
    return problems, counts


# --- text that lands in an office -------------------------------------------

def ascii_escape(text):
    """Lossless ASCII: anything outside ASCII becomes a \\uXXXX escape, so
    an office stays ASCII and the occupant's words stay recoverable."""
    out = text.encode("ascii", "backslashreplace").decode("ascii")
    escaped = sum(1 for ch in text if ord(ch) > 127)
    return out, escaped


# --- a sitting's words, filed from the brief that carries them --------------
#
# A read-only sitting lands nothing itself. Its words reach the notepad
# when office start sends out a session whose brief carries them (the
# ruling of sitting 2026-10-02-friction-wave-sitting-001, second page):
# each page sits between two marker lines, and its path, a new page
# named by the sitting, is on the first.
#
#   --- NOTEPAD PAGE BEGIN notepad/2026-10-05-some-sitting-001.md ---
#   ...the page's lines...
#   --- NOTEPAD PAGE END ---
#
# The page is the lines between the markers with a trailing newline,
# kept ASCII as office note keeps it. A page already filed with the same
# bytes is a no-op; a different page at that path is refused and never
# overwritten (filed paper). Bare `--- PAGE BEGIN ---` markers, which
# briefs from before this convention carry for office-src's own record,
# are not these and are never filed.

NOTEPAD_PAGE_BEGIN_RE = re.compile(r"^--- NOTEPAD PAGE BEGIN (.*) ---$")
NOTEPAD_PAGE_END = "--- NOTEPAD PAGE END ---"
SITTING_PAGE_RE = re.compile(r"^notepad/(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")


def sitting_page_path_problem(path):
    """None when path names a new page of a sitting's words, else why not."""
    m = SITTING_PAGE_RE.match(path)
    if not m:
        return (f"{path!r} is not a sitting's page: it must be notepad/DATE-SLUG.md, the slug in "
                "lowercase letters, digits and dashes (doctrine section 5)")
    try:
        dt.date.fromisoformat(m.group(1))
    except ValueError:
        return f"{path!r}: {m.group(1)} is not a date"
    return None


def sitting_pages(text):
    """(pages, problems) from a brief's text: pages is a list of (path,
    bytes), each page's lines between its markers, ASCII-escaped, with a
    trailing newline; problems names every marker that does not pair or
    names no page, and nothing between such markers is taken."""
    pages, problems = [], []
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = NOTEPAD_PAGE_BEGIN_RE.match(line)
        if line == NOTEPAD_PAGE_END:
            problems.append(f"line {i + 1}: a NOTEPAD PAGE END with no BEGIN before it")
            i += 1
            continue
        if not m:
            i += 1
            continue
        path = m.group(1).strip()
        end = None
        for j in range(i + 1, len(lines)):
            if lines[j] == NOTEPAD_PAGE_END:
                end = j
                break
            if NOTEPAD_PAGE_BEGIN_RE.match(lines[j]):
                break
        if end is None:
            problems.append(f"line {i + 1}: NOTEPAD PAGE BEGIN {path} has no END before the next page "
                            "or the end of the brief; nothing of it is filed")
            i += 1
            continue
        why = sitting_page_path_problem(path)
        if why:
            problems.append(f"line {i + 1}: {why}; nothing of it is filed")
        else:
            body, _ = ascii_escape("\n".join(lines[i + 1:end]) + "\n")
            pages.append((path, body.encode("ascii")))
        i = end + 1
    return pages, problems


def file_sitting_pages(root, text):
    """File each page a brief carries into the office at root. Returns a
    list of (state, path, why): filed, same (already filed with these
    bytes), refused (a different page is there; it is never
    overwritten), or malformed (path None)."""
    root = pathlib.Path(root)
    pages, problems = sitting_pages(text)
    out = [("malformed", None, p) for p in problems]
    for path, data in pages:
        target = root / path
        if target.is_file():
            if target.read_bytes() == data:
                out.append(("same", path, None))
            else:
                out.append(("refused", path, "a different page is already filed there; filed paper is never "
                                              "overwritten, so this one was not filed"))
            continue
        if target.exists():
            out.append(("refused", path, "something other than a page is there"))
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        out.append(("filed", path, None))
    return out


def brief_from_request(tarball):
    """The README.md a request tarball shipped (its brief), as text, or
    None when it shipped none."""
    with tarfile.open(tarball) as t:
        for member in t.getmembers():
            if member.isfile() and re.fullmatch(r"[^/]+/README\.md", member.name):
                return t.extractfile(member).read().decode("utf-8", "backslashreplace")
    return None


TEMPLATE_KEY_RE = re.compile(r"\{\{([a-z_]+)\}\}")
# A field line in a template: `- label: {{key}}` and nothing else on it.
TEMPLATE_FIELD_RE = re.compile(r"^- [a-z][a-z ]*: \{\{([a-z_]+)\}\}$")


def template_values(value):
    """A value as the list render_template works with: a string is one
    value, a list is one per line, None or an empty string is unset."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value != "" else []
    return [v for v in value if v is not None and v != ""]


def render_template(text, values):
    """Fill {{key}} placeholders from values (a string, or a list of them).

    A field line, `- label: {{key}}` alone on its line, renders once per
    value and is dropped when the key is unset, so a template can show
    the whole field block and every caller renders it through this one
    call: a field the command cannot fill is left out, never left blank.
    Every other placeholder needs exactly one value."""
    out = []
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\n")
        m = TEMPLATE_FIELD_RE.match(body)
        if m:
            given = template_values(values.get(m.group(1)))
            nl = line[len(body):]
            out += [body.replace("{{" + m.group(1) + "}}", v) + nl for v in given]
            continue

        def sub(mm):
            key = mm.group(1)
            given = template_values(values.get(key)) if key in values else None
            if given is None or (not given and values.get(key) != ""):
                raise HelperError(f"template needs a value for {{{{{key}}}}}")
            if len(given) > 1:
                raise HelperError(f"template takes one value for {{{{{key}}}}}, not {len(given)}")
            return given[0] if given else ""
        out.append(TEMPLATE_KEY_RE.sub(sub, line))
    return "".join(out)


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
    text = page.read_text(encoding="utf-8", errors="replace")
    stamp, delta = survey_age(text)
    recorded = facts_from_page(text).get(SURVEY_OFFICE_SRC_KEY)
    what = describe_age(delta)
    if a.install:
        if recorded is None:
            what += "; records no office-src version"
        elif recorded == a.install:
            what += f"; records office-src {recorded}, as installed"
        else:
            what += f"; records office-src {recorded}, not the installed {a.install}"
    print(f"{stamp} ({what})")


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


def cmd_catalog_check(a):
    """Both catalogs at once: defects on stdout, exit 3 when there are
    any; the lands entries no path could place are reported on stderr,
    so a prose writes is visible without being a refusal."""
    problems, unchecked = verb_catalog_problems(read_toml(a.verbs))
    problems += space_catalog_problems(read_toml(a.spaces))
    for line in unchecked:
        log(f"unchecked: {line}")
    for line in problems:
        print(line)
    return 3 if problems else 0


def cmd_pack_sid(a):
    print(sid_from_pack_report(sys.stdin.read()))


def cmd_projects(a):
    """One line per project: name, path as written, and what the check
    found. Exit 3 when any entry cannot be read; an office with no
    table says so on stdout and exits 0."""
    projects = read_projects(read_toml(a.manifest))
    if projects is None:
        print("this office scopes no projects: its floor plan has no [projects] table "
              "(office projects add NAME PATH adds one)")
        return 0
    if not projects:
        print("this office scopes no projects: its [projects] table lists none "
              "(office projects add NAME PATH adds one)")
        return 0
    width = max(len(p["name"]) for p in projects)
    bad = 0
    for p in projects:
        if p["problem"]:
            ok, text = False, p["problem"]
        else:
            ok, text = check_project_dir(p["resolved"])
        bad += not ok
        print(f"{p['name']:<{width}}  {p['path'] or '(no path)'}  "
              + (f"({text})" if ok else f"CANNOT BE READ: {text}"))
        for line in describe_declarations(p):
            print(f"{'':<{width}}  {line}")
    return 3 if bad else 0


def cmd_project_declare(a):
    """Set one project's declarations: --ride and --after-land replace
    the key's list, --no-rides and --no-after-land clear it, and a key
    with neither is left as it is."""
    rides = [] if a.no_rides else (a.ride or None)
    after = [] if a.no_after_land else (a.after_land or None)
    if a.no_rides and a.ride:
        raise HelperError("--ride and --no-rides contradict each other")
    if a.no_after_land and a.after_land:
        raise HelperError("--after-land and --no-after-land contradict each other")
    entry = set_declarations(a.manifest, a.name, rides, after)
    lines = describe_declarations(entry)
    print(f"{a.name}: " + ("; ".join(lines) if lines else "nothing rides with it and nothing runs after it lands"))


def cmd_project_add(a):
    stored, found = add_project(a.manifest, a.name, a.path)
    print(f"added {a.name}: {stored} ({found})")


def cmd_project_spec(a):
    """One NAME<TAB>PATH line per spec, each checked; refuses at the first
    that does not check, so office init builds nothing."""
    taken = []
    for spec in a.specs:
        name, stored, _ = project_spec(spec, taken)
        taken.append(name)
        print(f"{name}\t{stored}")


def cmd_check_project_dir(a):
    """Whether a path a wizard was just given is the top of a git repo bale
    runs in, checked before it asks anything else: what it found, or the
    reason as an error, for the wizard to ask again."""
    path = a.path.strip()
    stored = path if (path.startswith("/") or path.startswith("~/") or path == "~") else os.path.abspath(path)
    ok, found = check_project_dir(expand_project_path(stored))
    if not ok:
        raise HelperError(found)
    print(found)


def cmd_check_declaration(a):
    """A ride-along path or an after-land action as it would be stored,
    or a refusal saying why, for the wizard to ask again."""
    if a.kind == "ride":
        print(check_ride(a.value)[0])
    else:
        print(check_after_land(a.value))


def cmd_project_facts(a):
    """One project's entry as tab-separated lines a verb decides on:
    path (as written), resolved, then one rides and one after_land line
    per entry. Refuses a project the table does not list or cannot read."""
    projects = read_projects(read_toml(a.manifest)) or []
    entry = next((p for p in projects if p["name"] == a.name), None)
    if entry is None:
        raise HelperError(f"no project named {a.name} in this office's [projects] "
                          f"(it lists: {', '.join(p['name'] for p in projects) or 'none'})")
    if entry["problem"]:
        raise HelperError(f"{a.name}: {entry['problem']}")
    if entry["declaration_problems"]:
        raise HelperError(f"{a.name}: " + "; ".join(entry["declaration_problems"]))
    print(f"path\t{entry['path']}")
    print(f"resolved\t{entry['resolved']}")
    for r in entry["rides"]:
        print(f"rides\t{r}\t{expand_project_path(r)}")
    for c in entry["after_land"]:
        print(f"after_land\t{c}")


def cmd_record_session(a):
    """With --day, the first sid a candidate or queued folder records
    also opens it: the `opened` History line and status open."""
    if a.day is None:
        recorded, change = record_session(a.folder_md, a.sid, a.words), None
    else:
        recorded, change = record_session_opening(a.folder_md, a.sid, a.day, a.words)
    if not recorded:
        print("already recorded")
        return 4
    print("recorded")
    if change:
        print(change)


def cmd_folder_summary(a):
    nxt, sessions = folder_summary(a.folder_md, a.template)
    print(f"{nxt}\t{sessions}")


def cmd_normalize_field(a):
    print(normalize_field(a.key.replace("-", " "), a.value))


def cmd_field_help(a):
    keys = list(FIELD_HELP) if a.key == "all" else [a.key.replace("-", " ")]
    for key in keys:
        if key not in FIELD_HELP:
            raise HelperError(f"no field named {key!r}")
        print(f"{key}: {FIELD_HELP[key]}")


def cmd_next_number(a):
    n, unnumbered = next_number(a.root)
    if unnumbered and os.environ.get("OFFICE_DEBUG") == "1":
        for rel in unnumbered:
            log(f"debug: no number line, so not counted (and never numbered): {rel}")
    print(n)


def cmd_folder_by_number(a):
    m = FOLDER_REF_RE.match(" ".join(a.ref.split()))
    if not m:
        raise HelperError(f"not a folder number: {a.ref!r} (folder N)")
    same = folders_by_number(read_folders(a.root)).get(int(m.group(1)), [])
    if not same:
        raise HelperError(f"no folder {int(m.group(1))} on the desk or in the filing cabinet")
    if len(same) > 1:
        raise HelperError(f"folder {int(m.group(1))} is minted twice: " + ", ".join(f["rel"] for f in same))
    print(same[0]["rel"])


def cmd_folder_facts(a):
    """Tab-separated facts a verb decides on: status, number, whether
    the folder has a History section, how many sids it records."""
    f = parse_folder(pathlib.Path(a.folder_md).read_text(encoding="utf-8"))
    number, problem = folder_number(f["fields"])
    print(f"status\t{(f['fields'].get('status') or [''])[0]}")
    print(f"number\t{number or ''}")
    print(f"history\t{1 if f['has_history'] else 0}")
    print(f"sids\t{len(f['sids'])}")
    # The fields office start derives from: the lane (project: paths),
    # the work class and the title.
    for key in ("lane", "class"):
        print(f"{key}\t{(f['fields'].get(key) or [''])[0]}")
    print(f"title\t{f['title'] or ''}")
    if problem:
        log(f"warning: {a.folder_md}: {problem}")


def cmd_folder_event(a):
    old, wrote = folder_event(a.folder_md, a.day, a.verb, a.text, a.status)
    if a.status is not None:
        print(f"status {old} -> {a.status}" if old is not None
              else "no status line (a folder from before the field block): left as it is")
    print(f"History: {a.day} {a.verb}: {a.text}" if wrote
          else "no History section (a folder from before the field block): no line written")


def cmd_ratify(a):
    print(ratify_session(a.folder_md, a.sid, a.day, a.except_text))


def cmd_folder_check(a):
    problems, counts = folder_check(a.root)
    older = (f"; {counts['no_status']} with no status line, from before the field block"
             if counts["no_status"] else "")
    if not problems:
        print(f"folders:    {counts['folders']} on the desk and in the filing cabinet; every status "
              f"agrees with its History{older}")
        return 0
    print(f"folders:    {len(problems)} problem(s) in {counts['folders']} folders{older}:")
    for p in problems:
        print(f"  {p}")
    return 3


def cmd_filed_check(a):
    problems, counts = filed_history_check(a.root)
    if not counts["specs"]:
        print("filed:      the floor plan lists no filed pages")
        return 0
    listed = ", ".join(counts["specs"])
    if not problems:
        print(f"filed:      every commit to a filed page only appended at its end ({listed}: "
              f"{counts['pages']} file(s), {counts['commits']} commit(s))")
        return 0
    print(f"filed:      {len(problems)} change(s) to filed pages did more than append at the end ({listed}):")
    for p in problems:
        print(f"  {p}")
    return 3


def cmd_append_check(a):
    """Exit 0 when the page only grew at its end (or is new), 3 with the
    reason on stdout when it changed bytes already committed."""
    why = append_check(a.root, a.path)
    if why:
        print(why)
        return 3
    return 0


def cmd_project_names(a):
    """One project name per line, in the floor plan's order; nothing when
    the office scopes none."""
    for p in read_projects(read_toml(a.manifest)) or []:
        print(p["name"])


def cmd_ascii_escape(a):
    # Bytes in, decoded as UTF-8 whatever the locale says; a byte that is
    # not UTF-8 survives as a \\xNN escape rather than being dropped.
    out, escaped = ascii_escape(sys.stdin.buffer.read().decode("utf-8", "backslashreplace"))
    if escaped:
        log(f"kept {escaped} non-ASCII character(s) as backslash escapes; offices hold ASCII only")
    sys.stdout.write(out)


def cmd_file_sitting_pages(a):
    """One line per page: filed, same, refused or malformed, tab-separated
    with the path and why. Exit 3 when any was refused or malformed."""
    if a.request:
        text = brief_from_request(a.request)
    else:
        text = pathlib.Path(a.brief).read_bytes().decode("utf-8", "backslashreplace")
    if text is None:
        return 0
    results = file_sitting_pages(a.root, text)
    for state, path, why in results:
        print("\t".join([state, path or "-"] + ([why] if why else [])))
    return 3 if any(state in ("refused", "malformed") for state, _, _ in results) else 0


def cmd_render_template(a):
    """key=value arguments; a key given more than once is a list, one
    field line per value."""
    values = {}
    for kv in a.values:
        if "=" not in kv:
            raise HelperError(f"render-template takes key=value, not {kv!r}")
        key, value = kv.split("=", 1)
        if key in values:
            values[key] = template_values(values[key]) + template_values(value)
        else:
            values[key] = value
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
    p = sub.add_parser("survey-age"); p.add_argument("page")
    p.add_argument("--install", help="the installed office-src version, to compare with the one the survey records")
    p.set_defaults(fn=cmd_survey_age)
    p = sub.add_parser("skew"); p.add_argument("office_version"); p.add_argument("install_version")
    p.add_argument("migrations"); p.set_defaults(fn=cmd_skew)

    p = sub.add_parser("landed"); p.add_argument("version"); p.add_argument("migrations")
    p.add_argument("install_version"); p.add_argument("root"); p.set_defaults(fn=cmd_landed)
    p = sub.add_parser("render-bale-toml"); p.add_argument("manifest"); p.add_argument("--root")
    p.add_argument("--pack-only", action="store_true"); p.set_defaults(fn=cmd_render_bale_toml)
    p = sub.add_parser("include-group-check"); p.add_argument("manifest"); p.add_argument("bale_toml")
    p.add_argument("root"); p.set_defaults(fn=cmd_include_group_check)
    p = sub.add_parser("catalog-check"); p.add_argument("verbs"); p.add_argument("spaces")
    p.set_defaults(fn=cmd_catalog_check)
    p = sub.add_parser("pack-sid"); p.set_defaults(fn=cmd_pack_sid)
    p = sub.add_parser("projects"); p.add_argument("manifest"); p.set_defaults(fn=cmd_projects)
    p = sub.add_parser("project-add"); p.add_argument("manifest"); p.add_argument("name")
    p.add_argument("path"); p.set_defaults(fn=cmd_project_add)
    p = sub.add_parser("project-declare"); p.add_argument("manifest"); p.add_argument("name")
    p.add_argument("--ride", action="append"); p.add_argument("--no-rides", action="store_true")
    p.add_argument("--after-land", action="append"); p.add_argument("--no-after-land", action="store_true")
    p.set_defaults(fn=cmd_project_declare)
    p = sub.add_parser("check-project-dir"); p.add_argument("path"); p.set_defaults(fn=cmd_check_project_dir)
    p = sub.add_parser("project-spec"); p.add_argument("specs", nargs="+"); p.set_defaults(fn=cmd_project_spec)
    p = sub.add_parser("check-declaration"); p.add_argument("kind", choices=("ride", "after-land"))
    p.add_argument("value"); p.set_defaults(fn=cmd_check_declaration)
    p = sub.add_parser("project-facts"); p.add_argument("manifest"); p.add_argument("name")
    p.set_defaults(fn=cmd_project_facts)
    p = sub.add_parser("record-session"); p.add_argument("folder_md"); p.add_argument("sid")
    p.add_argument("--words"); p.add_argument("--day"); p.set_defaults(fn=cmd_record_session)
    p = sub.add_parser("normalize-field"); p.add_argument("key"); p.add_argument("value")
    p.set_defaults(fn=cmd_normalize_field)
    p = sub.add_parser("field-help"); p.add_argument("key"); p.set_defaults(fn=cmd_field_help)
    p = sub.add_parser("next-number"); p.add_argument("root"); p.set_defaults(fn=cmd_next_number)
    p = sub.add_parser("folder-by-number"); p.add_argument("root"); p.add_argument("ref")
    p.set_defaults(fn=cmd_folder_by_number)
    p = sub.add_parser("folder-facts"); p.add_argument("folder_md"); p.set_defaults(fn=cmd_folder_facts)
    p = sub.add_parser("folder-event"); p.add_argument("folder_md"); p.add_argument("--day", required=True)
    p.add_argument("--verb", required=True); p.add_argument("--text", required=True)
    p.add_argument("--status"); p.set_defaults(fn=cmd_folder_event)
    p = sub.add_parser("ratify"); p.add_argument("folder_md"); p.add_argument("sid")
    p.add_argument("--day", required=True); p.add_argument("--except", dest="except_text")
    p.set_defaults(fn=cmd_ratify)
    p = sub.add_parser("folder-check"); p.add_argument("root"); p.set_defaults(fn=cmd_folder_check)
    p = sub.add_parser("filed-check"); p.add_argument("root"); p.set_defaults(fn=cmd_filed_check)
    p = sub.add_parser("folder-summary"); p.add_argument("folder_md"); p.add_argument("template")
    p.set_defaults(fn=cmd_folder_summary)
    p = sub.add_parser("append-check"); p.add_argument("root"); p.add_argument("path")
    p.set_defaults(fn=cmd_append_check)
    p = sub.add_parser("project-names"); p.add_argument("manifest"); p.set_defaults(fn=cmd_project_names)
    p = sub.add_parser("ascii-escape"); p.set_defaults(fn=cmd_ascii_escape)
    p = sub.add_parser("file-sitting-pages"); p.add_argument("root")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--request", help="a request tarball: the pages its README.md carries")
    g.add_argument("--brief", help="a brief file")
    p.set_defaults(fn=cmd_file_sitting_pages)
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
