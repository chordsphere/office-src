#!/usr/bin/env python3
"""Helpers for the office command.

The office command is bash; the parts that need a real parser (TOML,
Markdown sections, version ordering, fact diffs) live here. Standard
library only. Every subcommand prints its result on stdout, logs to
stderr with an [office] prefix, and exits 0 on success, 1 on a refusal
the caller should report, 2 on a usage or internal error, and 3 where a
subcommand documents a second outcome (an incomplete profile).
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


def render_manifest(spaces_catalog, name, version, built_at, timezone):
    """The floor plan a new office starts with: its stamp and the base
    spaces from the install's catalog."""
    lines = [
        "# Floor plan of this office. The office command finds an office by",
        "# this file and reads it on every run. office upgrade and renovation",
        "# sessions change it; nothing else should.",
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
        hung = space.get("hung", False)
        if isinstance(hung, list):
            lines.append("hung = [" + ", ".join(f'"{h}"' for h in hung) + "]")
        else:
            lines.append(f"hung = {'true' if hung else 'false'}")
        lines.append(f"filed = {'true' if space.get('filed', False) else 'false'}")
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
        out.append(entry)
    out.sort(key=lambda e: parse_version(e["version"]))
    return out


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
        print(f"{m['version']}\t{m['kind']}\t{m['action']}\t{m['summary']}")


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
