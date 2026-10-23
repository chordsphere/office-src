#!/usr/bin/env python3
"""The founding door and the renovation door: what office init, office
found and office upgrade hand to office start.

An office comes to exist, and is renovated, through the same door every
other session uses: a folder on the desk, and office start sending a
session out for it with a brief. This module holds the parts of that
which are not the shell's: the profile's questions as data (one per
section of share/profile-shape.toml, in its order), the occupant's
answers kept in the founding folder as answers.md (his words, verbatim),
the founding session's brief composed from them, the renovation
session's brief composed from its migration, and the founding and
renovation folders found again on the desk.

The answers travel between the shell and this module as a directory
holding one file per answered section, named by the section's flag
(purpose, not-for, ...), plus `timezone` and its two companions; a
section with no file was left to the founding session. A directory, not
a delimited stream, because an answer given as a flag may hold any
character.

Everything written into an office is ASCII: the occupant's words keep
anything else as backslash escapes (office_helper.ascii_escape), so they
stay recoverable. Run with -B: an install is never written to.
"""

import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

# A founding folder is the desk folder one of these opened; a renovation
# folder is the one office upgrade opened for a migration's version.
FOUNDING_SOURCES = ("office init", "office found")
RENOVATION_SOURCE = "office upgrade"
ANSWERS_FILE = "answers.md"
LEFT_LINE = "Left to the founding session: a plain return at the question, or no flag."
NOT_ASKED_LINE = "Not asked: the founding session writes it (the date and its own session id)."
TZ_LINE_RE = oh.LazyPattern(r"^Timezone: (\S+) \((resolves here|does not resolve here)(?:: (.*))?\)\s*$")
ANSWERED_RE = oh.LazyPattern(r"^Answered (\d{4}-\d{2}-\d{2}) through (office \w+)\.\s*$")


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


# --- the profile's questions -----------------------------------------------------

def flag_of(heading):
    """The flag twin a section without one in the shape gets: its heading,
    lower case, words joined by dashes."""
    return re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")


def sections(shape):
    """The shape's sections in order, each a dict: heading, flag, asks,
    hint, asked. Refuses a shape whose flags collide, or take a name
    office init or found already uses for something else."""
    out, seen = [], {}
    for s in shape.get("section", []):
        heading = str(s["heading"]).strip()
        flag = str(s.get("flag") or flag_of(heading)).strip()
        if not re.fullmatch(r"[a-z][a-z0-9-]*", flag):
            raise oh.HelperError(f"profile shape: section {heading!r} has a flag that is not a word: {flag!r}")
        if flag in seen:
            raise oh.HelperError(f"profile shape: sections {seen[flag]!r} and {heading!r} share the flag --{flag}")
        if flag in RESERVED_FLAGS:
            raise oh.HelperError(f"profile shape: section {heading!r}'s flag --{flag} is already one of "
                                 "office init's own")
        seen[flag] = heading
        out.append({"heading": heading, "flag": flag, "asks": str(s.get("asks", "")).strip(),
                    "hint": str(s.get("hint", "")).strip(), "asked": bool(s.get("asked", True))})
    if not out:
        raise oh.HelperError("profile shape: no sections")
    return out


# init's and found's own flags, which no section may take.
RESERVED_FLAGS = ("name", "path", "project", "no-projects", "no-default", "no-founding", "timezone", "goal", "help")


def question(s):
    """The question for a section, worded from its asks line."""
    asks = s["asks"].rstrip(".")
    return f"{s['heading']}: {asks[:1].lower() + asks[1:]}" if asks else s["heading"]


def explanation(s):
    """What `?` prints for a section: the asks line, the hint, and what a
    plain return does."""
    parts = [s["asks"], s["hint"], "No section of a profile may be blank, and an answer here can be a sentence or "
             "a paragraph on one line; a plain return leaves this section for the founding session to ask about."]
    return " ".join(p for p in parts if p)


# --- the answers, kept in the founding folder ---------------------------------------

def read_answer_dir(directory, shape_sections):
    """{flag: text} and {flag: 'DAY through VIA'} for the sections a
    directory holds, and the timezone facts (a dict, empty when none)."""
    d = pathlib.Path(directory)
    answers, when = {}, {}
    for s in shape_sections:
        f = d / s["flag"]
        if s["asked"] and f.is_file():
            text = f.read_text(encoding="utf-8", errors="backslashreplace").strip()
            if text:
                answers[s["flag"]] = text
                w = d / (s["flag"] + ".answered")
                if w.is_file():
                    when[s["flag"]] = w.read_text(encoding="utf-8").strip()
    tz = {}
    if (d / "timezone").is_file() and (d / "timezone").read_text(encoding="utf-8").strip():
        tz["zone"] = (d / "timezone").read_text(encoding="utf-8").strip()
        tz["resolves"] = (d / "timezone.resolves").is_file() and \
            (d / "timezone.resolves").read_text(encoding="utf-8").strip() == "yes"
        rem = d / "timezone.remedy"
        tz["remedy"] = rem.read_text(encoding="utf-8").strip() if rem.is_file() else ""
        w = d / "timezone.answered"
        tz["answered"] = w.read_text(encoding="utf-8").strip() if w.is_file() else ""
    return answers, when, tz


def quoted(text):
    """The occupant's words as a block quote, every line kept: a quoted
    line can never be read as a page marker or a heading."""
    return "\n".join(">" if not line.strip() else f"> {line.rstrip()}" for line in text.splitlines())


def unquoted(lines):
    return "\n".join(line[2:] if line.startswith("> ") else line[1:] for line in lines).strip()


def render_answers(name, shape_sections, answers, when, tz, day, zone_label, via):
    """answers.md: the profile's questions and the occupant's answers,
    verbatim, one section per heading, in the shape's order."""
    lines = [
        "# The profile's questions, answered",
        "",
        f"The occupant's answers to the profile's questions for the {name} office,",
        f"asked by {via} on {day} ({zone_label}), one question per section of the",
        "profile's required shape, in its order. Each answer is quoted as it was",
        "given. The founding session writes the profile from them and asks only",
        "about the sections left to it here; office found asks those again and",
        "keeps the rest. Written by the office command, never by hand.",
    ]
    for s in shape_sections:
        lines += ["", f"## {s['heading']}", ""]
        if not s["asked"]:
            lines.append(NOT_ASKED_LINE)
            continue
        lines.append(f"Asked: {s['asks']}")
        lines.append("")
        if s["flag"] in answers:
            lines.append(f"Answered {when.get(s['flag']) or f'{day} through {via}'}.")
            lines.append("")
            lines.append(quoted(answers[s["flag"]]))
        else:
            lines.append(LEFT_LINE)
        if s["heading"] == "Site":
            lines.append("")
            lines.append(timezone_line(tz))
    text = "\n".join(lines) + "\n"
    return oh.ascii_escape(text)[0]


def timezone_line(tz):
    if not tz:
        return "Timezone: left to the founding session."
    if tz["resolves"]:
        return f"Timezone: {tz['zone']} (resolves here)"
    return f"Timezone: {tz['zone']} (does not resolve here: {tz['remedy'] or 'no remedy found'})"


def parse_answers(text, shape_sections):
    """({flag: text}, {flag: 'DAY through VIA'}, tz) from an answers.md
    this module wrote. A section it cannot place is ignored, and one
    whose answer is missing is left to be asked."""
    by_heading = {s["heading"]: s for s in shape_sections}
    answers, when, tz = {}, {}, {}
    current, quote = None, []

    def close():
        if current is not None and current["asked"] and quote:
            answers[current["flag"]] = unquoted(quote)
    for line in text.splitlines():
        if line.startswith("## "):
            close()
            current, quote = by_heading.get(line[3:].strip()), []
            continue
        if current is None:
            continue
        if line.startswith(">"):
            quote.append(line)
            continue
        m = ANSWERED_RE.match(line)
        if m:
            when[current["flag"]] = f"{m.group(1)} through {m.group(2)}"
            continue
        m = TZ_LINE_RE.match(line)
        if m:
            tz = {"zone": m.group(1), "resolves": m.group(2) == "resolves here", "remedy": m.group(3) or "",
                  "answered": ""}
    close()
    return answers, {f: w for f, w in when.items() if f in answers}, tz


def load_into(folder_dir, directory, shape_sections):
    """Copy the answers a founding folder keeps into the answer directory,
    for every section the directory does not already answer (a flag given
    now wins over a kept answer). Returns the headings it kept."""
    kept_file = pathlib.Path(folder_dir) / ANSWERS_FILE
    if not kept_file.is_file():
        return []
    answers, when, tz = parse_answers(kept_file.read_text(encoding="utf-8", errors="backslashreplace"),
                                      shape_sections)
    d = pathlib.Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    kept = []
    for s in shape_sections:
        f = s["flag"]
        if f in answers and not (d / f).is_file():
            (d / f).write_text(answers[f] + "\n", encoding="utf-8")
            if f in when:
                (d / (f + ".answered")).write_text(when[f] + "\n", encoding="utf-8")
            kept.append(s["heading"])
    if tz and not (d / "timezone").is_file():
        (d / "timezone").write_text(tz["zone"] + "\n", encoding="utf-8")
        (d / "timezone.resolves").write_text(("yes" if tz["resolves"] else "no") + "\n", encoding="utf-8")
        (d / "timezone.remedy").write_text(tz["remedy"] + "\n", encoding="utf-8")
        kept.append("the timezone")
    return kept


# --- finding a door's folder ------------------------------------------------------------

def door_folders(root):
    """{rel: kind} for every folder on the desk a door opened: founding
    or renovation."""
    out = {}
    for f in oh.read_folders(root):
        if f["space"] != "desk" or f["problem"]:
            continue
        source = (f["fields"].get("source") or [""])[0]
        if source in FOUNDING_SOURCES:
            out[f["rel"]] = "founding"
        elif source == RENOVATION_SOURCE:
            out[f["rel"]] = "renovation"
    return out


def renovation_slug(version):
    return "upgrade-" + flag_of(version)


def find_door_folder(root, kind, version=None):
    """The desk folder a door opened for this kind (and, for a
    renovation, this migration's version), the highest-numbered when
    there are several; None when the desk holds none."""
    found = []
    for f in oh.read_folders(root):
        if f["space"] != "desk" or f["problem"]:
            continue
        source = (f["fields"].get("source") or [""])[0]
        if kind == "founding" and source in FOUNDING_SOURCES:
            found.append(f)
        elif kind == "renovation" and source == RENOVATION_SOURCE and \
                f["name"].endswith("-" + renovation_slug(version)):
            found.append(f)
    if not found:
        return None
    found.sort(key=lambda f: (f.get("number") or 0, f["name"]))
    return found[-1]["rel"]


# --- the founding session's brief -----------------------------------------------------

def survey_lines(root):
    """The survey's facts about the machine, as the page states them:
    its Machine, Timezone and Tools sections and the office-src install."""
    page = pathlib.Path(root) / "floor-plan" / "survey.md"
    if not page.is_file():
        return ["- (no survey page: office survey writes one)"]
    facts = oh.facts_from_page(page.read_text(encoding="utf-8", errors="replace"))
    out = []
    for prefix in ("survey.", "machine.", "timezone.", "tools.", "office-src."):
        for key, value in facts.items():
            if key.startswith(prefix):
                out.append(f"- {key}: {value}")
    return out or ["- (the survey page holds no facts)"]


def founding_brief(root, folder, name, shape_sections, answers, when, tz, day, zone_label, install_version,
                   floor_zone, floor_zone_resolves, zone_written):
    """The founding session's brief: what it is, which office, the
    occupant's answers verbatim under the sections they answer, what was
    left to ask, the timezone and whether it resolved, the machine."""
    asked = [s for s in shape_sections if s["asked"]]
    left = [s["heading"] for s in asked if s["flag"] not in answers]
    answered_on = [re.sub(r"^(\S+) through ", r"on \1, through ", w)
                   for w in sorted(set(when.values()))] or [f"on {day}, through the office command"]
    manifest = oh.read_toml(pathlib.Path(root) / "floor-plan" / "manifest.toml")
    projects = oh.read_projects(manifest) or []
    number = None
    md = pathlib.Path(root) / folder / "folder.md"
    if md.is_file():
        number, _ = oh.folder_number(oh.parse_folder(md.read_text(encoding="utf-8")).get("fields", {}))
    cite = f"folder {number}" if number else folder
    lines = [
        f"# Brief: founding the {name} office",
        "",
        f"The brief for the founding session of the {name} office, composed by the",
        f"office command (office-src {install_version}) on {day} ({zone_label}) and sent",
        f"out through office start, in the office, for {cite} ({folder}). The",
        "session is scoped: it may write profile.md, the notepad and the floor",
        "plan, and its folder, as every office session may. Leave the version",
        "stamp alone.",
        "",
        "## What this session is",
        "",
        "The founding. Spawning an office is a conversation, not a form (doctrine",
        "section 12), and the occupant has already answered the profile's",
        "questions (" + "; and ".join(answered_on) + "). His answers are below,",
        "verbatim, under the sections they answer. So:",
        "",
        "1. Write profile.md from the answers, section by section, keeping his",
        "   words where they serve. Every required section must end up with text",
        "   outside comments and no line starting with TODO; a section with no",
        "   restriction says so in writing.",
        "2. Ask only for what was left to you: " + (", ".join(left) if left else "nothing was left") + ".",
        "   A light question block if it fits (at most three questions, each with",
        "   a default he can ratify with \"as assumed\"), a clarification if not.",
        "   Push back where an answer contradicts another one or the doctrine;",
        "   otherwise do not ask again what he already answered.",
        "3. Write the Founding section yourself: the founding date and this",
        "   session's id, and that the profile's questions were answered",
        f"   {'; and '.join(answered_on)}, the answers kept in {folder}/{ANSWERS_FILE}.",
        "4. File the occupant's words as a notepad page (doctrine section 5), named",
        "   for the day and the founding (notepad/DATE-founding.md): the answers",
        "   below, verbatim, as his words given through the office command, and",
        "   his words from this conversation.",
        "5. The timezone, as the section below says.",
        "",
        "## Which office",
        "",
        f"- name: {name}",
        f"- root: {pathlib.Path(root)}",
        f"- built from office-src: {oh.office_stamp(manifest)['built_from']}",
        f"- founding folder: {folder} ({cite})",
        "- projects it watches: " + (", ".join(f"{p['name']} ({p['path']})" for p in projects) if projects
                                     else "none yet (office projects add adds one)"),
        "",
        "## The occupant's answers",
    ]
    for s in shape_sections:
        lines += ["", f"### {s['heading']}", ""]
        if not s["asked"]:
            lines.append("Not asked: you write it (item 3 above).")
            continue
        lines.append(f"Asked: {s['asks']}")
        lines.append("")
        if s["flag"] in answers:
            lines.append(quoted(answers[s["flag"]]))
        else:
            lines.append("Left to you: he gave no answer at the question. Ask about it.")
    lines += ["", "## The timezone", ""]
    if not tz:
        lines += [
            "He was not asked, or gave no zone. The floor plan's [office] timezone",
            f"names {floor_zone}, the machine's, which "
            + ("resolves here" if floor_zone_resolves else "does not resolve here") + ".",
            "Ask him which zone he lives in rather than trusting the machine clock,",
            "check that it resolves in this machine's zone database, and set it in",
            "the floor plan's [office] timezone and in the profile's Site section.",
        ]
    elif tz["resolves"]:
        lines += [
            f"He lives in {tz['zone']}, which resolves here.",
            ("The office command wrote it to the floor plan's [office] timezone when he"
             " answered, so the office's dates are his from the founding folder on."
             if zone_written else
             f"The floor plan's [office] timezone already names it."),
            "Write it in the profile's Site section; the floor plan needs nothing more.",
        ]
    else:
        lines += [
            f"He named {tz['zone']}, which does not resolve here: {tz['remedy'] or 'no remedy was found'}.",
            f"The floor plan's [office] timezone still names {floor_zone}"
            + (" (which resolves here)." if floor_zone_resolves else " (which does not resolve here either)."),
            "Settle it with him: the spelling this zone database holds, or the",
            "package that brings his spelling back. Then set the zone that resolves",
            "in the floor plan's [office] timezone and in the profile's Site section.",
        ]
    lines += ["", "## The machine, from the survey", "",
              "The survey's facts at the moment the brief was composed (office start",
              "surveys again before it packs, and the page rides as a hung item):", ""]
    lines += survey_lines(root)
    text = "\n".join(lines) + "\n"
    return oh.ascii_escape(text)[0]


# --- the renovation session's brief --------------------------------------------------

def migration_entry(migrations, install_version, version):
    for m in oh.load_migrations(migrations, install_version):
        if m["version"] == version:
            if m["kind"] != "renovation":
                raise oh.HelperError(f"migration {version} is not a renovation")
            return m
    raise oh.HelperError(f"no migration {version} in {migrations}")


def landed_text(migrations, version):
    """The migration's [landed] table as its file declares it, verbatim:
    from its header to the next table or the end of the file."""
    text = (pathlib.Path(migrations) / f"{version}.toml").read_text(encoding="utf-8")
    out, inside = [], False
    for line in text.splitlines():
        if line.strip().startswith("["):
            if inside:
                break
            inside = line.strip() == "[landed]"
        if inside:
            out.append(line)
    return "\n".join(out).rstrip()


def renovation_goal(m):
    """The renovation session's goal: the migration's own, with what done
    means and the stamp rule, as office upgrade's pack line carried it."""
    return (f"Renovate this office for office-src {m['version']}: {m['action']} Done means "
            f"{oh.describe_landed(m['landed'])}. Leave the version stamp alone; office upgrade checks this and "
            "stamps the office.")


def renovation_brief(root, folder, m, landed_block, unmet, day, zone_label, install_version):
    manifest = oh.read_toml(pathlib.Path(root) / "floor-plan" / "manifest.toml")
    stamp = oh.office_stamp(manifest)
    name = manifest.get("office", {}).get("name", "(unnamed)")
    forecast = (", ".join(m["writes"]) + " (the migration declares it), and the folder and the notepad"
                if m["writes"] else "the whole office (the migration declares no narrower forecast)")
    lines = [
        f"# Brief: renovating the {name} office for office-src {m['version']}",
        "",
        f"The brief for a renovation session, composed by office upgrade (office-src",
        f"{install_version}) on {day} ({zone_label}) and sent out through office start, in",
        f"the office, for {folder}.",
        "",
        "## What this session is",
        "",
        f"A renovation. Migration {m['version']} of office-src needs judgment, so office",
        "upgrade ran every migration before it, stopped at this one, and sent this",
        "session out to do its work. Do what the goal names. Leave the version",
        "stamp (the floor plan's migrated_to) alone: only office upgrade writes it.",
        "When this session has landed, the occupant runs office upgrade again; it",
        "checks the declaration below and stamps the office when it holds.",
        "",
        f"It forecasts {forecast}.",
        "",
        "## The migration",
        "",
        f"- version: {m['version']}",
        f"- summary: {m['summary']}",
        f"- goal: {m['action']}",
        "",
        "Its [landed] declaration, in full:",
        "",
        "```toml",
        landed_block,
        "```",
        "",
        f"In words: {oh.describe_landed(m['landed'])}.",
        "",
        f"What does not hold yet, as office upgrade checked it on {day}:",
        "",
    ]
    lines += [f"- {u}" for u in unmet] or ["- (nothing was reported)"]
    lines += [
        "",
        "## Which office",
        "",
        f"- name: {name}",
        f"- root: {pathlib.Path(root)}",
        f"- built from office-src {stamp['built_from']}, migrated to {stamp['migrated_to']}",
        f"- the install: office-src {install_version}",
    ]
    return oh.ascii_escape("\n".join(lines) + "\n")[0]


# --- command line ------------------------------------------------------------------

def cmd_sections(a):
    for s in sections(oh.read_toml(a.shape)):
        print("\t".join([s["flag"], "1" if s["asked"] else "0", s["heading"], question(s), explanation(s)]))
    return 0


def cmd_load(a):
    for heading in load_into(a.folder_dir, a.into, sections(oh.read_toml(a.shape))):
        print(heading)
    return 0


def cmd_write_answers(a):
    secs = sections(oh.read_toml(a.shape))
    answers, when, tz = read_answer_dir(a.answers, secs)
    target = pathlib.Path(a.folder_dir) / ANSWERS_FILE
    target.write_text(render_answers(a.name, secs, answers, when, tz, a.day, a.zone_label, a.via), encoding="ascii")
    left = [s["heading"] for s in secs if s["asked"] and s["flag"] not in answers]
    print(f"{len(answers)}\t{', '.join(left)}")
    return 0


def cmd_founding_brief(a):
    secs = sections(oh.read_toml(a.shape))
    answers, when, tz = read_answer_dir(a.answers, secs)
    text = founding_brief(a.root, a.folder, a.name, secs, answers, when, tz, a.day, a.zone_label,
                          a.install_version, a.floor_zone, a.floor_zone_resolves == "yes", a.zone_written == "yes")
    pathlib.Path(a.out).write_text(text, encoding="ascii")
    return 0


def cmd_renovation(a):
    m = migration_entry(a.migrations, a.install_version, a.version)
    if a.what == "goal":
        print(renovation_goal(m))
    elif a.what == "writes":
        for w in m["writes"] or ["."]:
            print(w)
    else:
        unmet = oh.unmet_landed(m["landed"], a.root)
        text = renovation_brief(a.root, a.folder, m, landed_text(a.migrations, a.version), unmet, a.day,
                                a.zone_label, a.install_version)
        pathlib.Path(a.out).write_text(text, encoding="ascii")
    return 0


def cmd_door_folder(a):
    rel = find_door_folder(a.root, a.kind, a.version)
    if rel:
        print(rel)
    return 0


def cmd_set_timezone(a):
    oh.set_office_key(a.manifest, "timezone", a.zone)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_door.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sections"); p.add_argument("shape"); p.set_defaults(fn=cmd_sections)
    p = sub.add_parser("load-answers"); p.add_argument("folder_dir"); p.add_argument("--into", required=True)
    p.add_argument("--shape", required=True); p.set_defaults(fn=cmd_load)
    p = sub.add_parser("write-answers"); p.add_argument("folder_dir"); p.add_argument("--answers", required=True)
    for k in ("shape", "name", "day", "zone-label", "via"):
        p.add_argument("--" + k, required=True)
    p.set_defaults(fn=cmd_write_answers)
    p = sub.add_parser("founding-brief"); p.add_argument("root"); p.add_argument("--folder", required=True)
    for k in ("answers", "shape", "name", "day", "zone-label", "install-version", "floor-zone", "out"):
        p.add_argument("--" + k, required=True)
    p.add_argument("--floor-zone-resolves", choices=("yes", "no"), required=True)
    p.add_argument("--zone-written", choices=("yes", "no"), required=True)
    p.set_defaults(fn=cmd_founding_brief)
    p = sub.add_parser("renovation"); p.add_argument("what", choices=("goal", "writes", "brief"))
    p.add_argument("root"); p.add_argument("--version", required=True); p.add_argument("--migrations", required=True)
    p.add_argument("--install-version", required=True); p.add_argument("--folder", default="")
    p.add_argument("--day", default=""); p.add_argument("--zone-label", default=""); p.add_argument("--out")
    p.set_defaults(fn=cmd_renovation)
    p = sub.add_parser("door-folder"); p.add_argument("root"); p.add_argument("kind", choices=("founding", "renovation"))
    p.add_argument("--version"); p.set_defaults(fn=cmd_door_folder)
    p = sub.add_parser("set-timezone"); p.add_argument("manifest"); p.add_argument("zone")
    p.set_defaults(fn=cmd_set_timezone)
    a = ap.parse_args(argv)
    if a.cmd == "renovation" and a.what == "brief" and not (a.out and a.folder and a.day):
        ap.error("renovation brief needs --out, --folder and --day")
    if a.cmd == "door-folder" and a.kind == "renovation" and not a.version:
        ap.error("door-folder renovation needs --version")
    try:
        return a.fn(a)
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, UnicodeError) as exc:
        log(f"error: {exc.__class__.__name__}: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
