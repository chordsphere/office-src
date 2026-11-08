#!/usr/bin/env python3
"""office ask (0.48.0): the quick path, a question answered in a chat.

An urgent question is worth a chat and not a session: the occupant once
answered one in five minutes in a chat of his own, and it would have
taken thirty through the office, with none of the office's benefits kept.
So `office ask` takes the question in his words, as office start new
takes a job's, and writes one small out tray for a chat: a brief from the
install's templates/ask-brief.md (his words verbatim, the project, the
rule of the doctrine's section 2, the voice page's words when the project
has an audience, what to leave at the end) and beside it what the office
holds that a quick answer wants: the project's handbook chapter, the
letterhead's voice page and forbidden list, the profile and the
doctrine. No project tree rides, no bale verb runs, no session id is
minted: the ask's name, ask-DATE-SLUG, is the office's own.

The chat ends with one block the office reads, kept to the byte as the
ARISING and STANDING blocks are (values illustrative):

    --- LEARNED BEGIN ask-2026-10-26-picklist-endpoint ---

    ## Answer

    <the answer, in a paragraph, as he would keep it>

    ## Handbook

    ### alpha

    - the picklist endpoint reads its options from the schema's enum

    ## Questions and answers

    - 2026-10-26 does the endpoint cache? no, every call reads the schema

    --- LEARNED END ---

`## Answer` is needed; the other two are the doctrine's own shapes
(section 4) and each is there only when it holds something. Of several
blocks in one text the last counts; a fence around it is fine, and so is
a fence inside the answer. A block that does not read is refused by name
before anything is written.

Filing it (`office ask --learned`) writes the ask as a notepad page,
notepad/DATE-ask-SLUG.md (his words, then the Answer verbatim), files the
Handbook facts at the end of each project's chapter as `- DATE: fact
(ask-DATE-SLUG)`, the ask's name in a session's place, through office
land's own filing (lib/office_sort.py file_handbook), and then appends the
Questions and answers lines to the same page (an ask has no folder).
Then the tray goes.

What is out: an ask is out while its tray is there. The tray's root is
machine.toml's out_tray (default ~/out-tray), shared by every office on
the machine, so beside each tray the office keeps a small record,
ask-DATE-SLUG.ask.json (the office it came from, the project, when it
was asked, his words), outside the tray as the opener's copy is, so every
file in the tray is still one to attach. Filing removes the tray, the
opener's copy and the record, and nothing else.

The command line (bin/office calls it through pylib):

    office_ask.py send OFFICE --tray-root DIR --words-file FILE --slug SLUG
                       --day DAY --time HH:MM [--project NAME]
        write the tray and the record: name, tray, file and opener lines,
        KEY<TAB>VALUE
    office_ask.py out OFFICE --tray-root DIR
        the asks out from this office, oldest first:
        NAME<TAB>PROJECT (or -)<TAB>DAY TIME<TAB>TRAY
    office_ask.py out-lines OFFICE (--tray-root DIR | --machine-file FILE) [--status]
        the same in the walk-in's words (or office status's one line, and
        since 0.54.0 one more for each record whose tray is gone, with the
        line that removes it); nothing when none is out; with
        --machine-file, the tray root is its out_tray (default ~/out-tray)
    office_ask.py name-of --file FILE
        the name in the text's last LEARNED block (exit 3: no block)
    office_ask.py file OFFICE --tray-root DIR --file FILE --day DAY --time HH:MM
        read the last block, check it is an ask out from this office, write
        its page and file its facts: name, page, path and say lines
    office_ask.py none OFFICE --tray-root DIR --name NAME --day DAY --time HH:MM
        end an ask with its page alone (office ask --learned none)
    office_ask.py qa OFFICE --name NAME --file FILE
        append the block's Questions and answers to the ask's page: page and
        count lines, or `none`
    office_ask.py close --tray-root DIR --name NAME
        remove the ask's tray, its opener's copy and its record

Standard library only. Logs on stderr with an [office] prefix; exits 0
when it did what it was asked, 1 on a refusal (the line says why), 2 on
a usage error, 3 where a subcommand above says so.
"""

import argparse
import os
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = INSTALL / "templates"
DOCTRINE = INSTALL / "doctrine" / "OFFICE.md"
BRIEF_TEMPLATE = "ask-brief.md"
NOTEPAD_TEMPLATE = "notepad-page.md"
BRIEF = "ask-brief.md"
RECORD_SUFFIX = ".ask.json"
OPENER_SUFFIX = ".opener.txt"
BEGIN_PREFIX = "--- LEARNED BEGIN"
BEGIN_RE = oh.LazyPattern(r"^--- LEARNED BEGIN (\S+) ---$")
END = "--- LEARNED END ---"
SECTIONS = ("Answer", "Handbook", "Questions and answers")
# The out tray's files beside the brief: (name in the tray, path in the
# office or None for the install's doctrine, what it is, in the brief's
# words). The chapter's name is the project's.
LETTERHEAD_FILES = (("letterhead-voice.md", "letterhead/voice.md",
                     "the letterhead's voice page: the occupant's style rule for text that leaves the office"),
                    ("letterhead-forbidden.txt", "letterhead/forbidden.txt",
                     "the letterhead's forbidden list: what never leaves the office, one string per line"))


class AskError(oh.HelperError):
    """An ask, or a block, the office does not take, said by name."""


def debug(msg):
    if os.environ.get("OFFICE_DEBUG"):
        print(f"[office] debug: {msg}", file=sys.stderr)


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


# --- names and places --------------------------------------------------------------------

def page_rel(name):
    """The notepad page of the ask named name: notepad/DATE-ask-SLUG.md."""
    m = oh.ASK_NAME_RE.match(name)
    if not m:
        raise AskError(f"not an ask's name (ask-DATE-SLUG): {name!r}")
    return f"notepad/{m.group(1)}-ask-{m.group(2)}.md"


def record_path(tray_root, name):
    return pathlib.Path(tray_root) / (name + RECORD_SUFFIX)


def opener_path(tray_root, name):
    return pathlib.Path(tray_root) / (name + OPENER_SUFFIX)


def same_place(a, b):
    return os.path.realpath(str(a)) == os.path.realpath(str(b))


def name_for(office_root, tray_root, day, slug):
    """ask-DAY-SLUG, or ask-DAY-SLUG-N when that name is taken: a tray, a
    record or an opener's copy of that name in the tray root, or a page of
    it in this office's notepad."""
    slug = slug or "ask"
    base = f"ask-{day}-{slug}"
    if not oh.ASK_NAME_RE.match(base):
        raise AskError(f"the ask's name would be {base!r}, which is not ask-DATE-SLUG")
    n, name = 1, base
    while ((pathlib.Path(tray_root) / name).exists() or record_path(tray_root, name).exists()
           or opener_path(tray_root, name).exists() or (pathlib.Path(office_root) / page_rel(name)).exists()):
        n += 1
        name = f"{base}-{n}"
    return name


def read_record(path):
    import json
    try:
        rec = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        debug(f"{path} does not read as an ask's record, so it is left out: {exc}")
        return None
    if not isinstance(rec, dict) or not oh.ASK_NAME_RE.match(str(rec.get("name", ""))):
        debug(f"{path} is not an ask's record, so it is left out")
        return None
    return rec


def asks_out(office_root, tray_root):
    """The asks out from this office, oldest first: each record whose
    office is this one and whose tray is still there, with its tray's
    path under "tray"."""
    root = pathlib.Path(tray_root)
    if not root.is_dir():
        return []
    out = []
    for path in sorted(root.glob("ask-*" + RECORD_SUFFIX)):
        rec = read_record(path)
        if rec is None or not same_place(rec.get("office", ""), office_root):
            continue
        tray = root / rec["name"]
        if not tray.is_dir():
            debug(f"{rec['name']}'s tray is gone from {root}, so it is not out")
            continue
        out.append(dict(rec, tray=str(tray)))
    out.sort(key=lambda r: (str(r.get("day", "")), str(r.get("time", "")), r["name"]))
    return out


def orphans(office_root, tray_root):
    """The records this office left whose tray is gone (0.54.0): a tray
    deleted by hand leaves its ask-DATE-SLUG.ask.json, and its opener's
    copy, behind, and nothing else removes them. [(name, record path,
    opener path or None)], by name. A record of another office's is that
    office's, and is left out."""
    root = pathlib.Path(tray_root)
    if not root.is_dir():
        return []
    out = []
    for path in sorted(root.glob("ask-*" + RECORD_SUFFIX)):
        rec = read_record(path)
        if rec is None or not same_place(rec.get("office", ""), office_root):
            continue
        if (root / rec["name"]).is_dir():
            continue
        opener = opener_path(root, rec["name"])
        out.append((rec["name"], path, opener if opener.is_file() else None))
    return out


def orphan_line(name, record, opener=None):
    """office status's line for a record whose tray is gone, with the one
    line that removes it (the record, and the opener's copy when it is
    there): the ask was neither filed nor ended, so nothing of it is in the
    office, and the record is all that says it was sent."""
    import shlex
    paths = " ".join(shlex.quote(str(p)) for p in (record, opener) if p is not None)
    return (f"asks:       {name}'s tray is gone from {pathlib.Path(record).parent}, and its record is left behind "
            f"(nothing of it was filed); rm -- {paths} removes it")


def where_words(rec):
    return rec["project"] if rec.get("project") else "the office"


def out_line(rec):
    """One ask out, as the walk-in says it."""
    name = rec["name"]
    return (f"{name} ({where_words(rec)}), asked {rec.get('day', '?')} {rec.get('time', '')}".rstrip()
            + f": office ask --learned FILE files what it learned; office tray {name} opens its tray again")


def status_line(asks):
    names = ", ".join(f"{r['name']} ({where_words(r)})" for r in asks)
    return (f"asks:       {len(asks)} out: {names}; office ask --learned files each one's LEARNED block, "
            "office ask --learned none NAME ends one with nothing filed")


def home_words(rec):
    """The home screen's words for an ask out: the key files its block."""
    name = rec["name"]
    return (f"File what {name} learned ({where_words(rec)}): its LEARNED block, from the clipboard "
            f"(office tray {name} opens its tray again)")


# --- sending one out ---------------------------------------------------------------------

def voice_words(office_root, project):
    """The brief's paragraph on the letterhead, for a project with an
    audience: the voice page's words when it holds them, else the state
    office status reads (lib/office_deliver.py voice_state)."""
    import office_deliver as odel
    if not project:
        return "The office itself has no audience, so nothing here is written for one."
    if not project.get("audience"):
        return f"{project['name']} declares no audience, so nothing here is written for one."
    state, line = odel.voice_state(office_root)
    head = (f"{project['name']} has an audience ({project['audience']}): before you write anything for it, read "
            "the letterhead's voice page, letterhead-voice.md, and the forbidden list, letterhead-forbidden.txt, "
            "and write to them.")
    if state != "written":
        return f"{head} The voice page {('is missing' if state == 'absent' else 'holds no words of his yet')} ({line})."
    import office_sort as osort
    lines = pathlib.Path(office_root, odel.VOICE_REL).read_text(encoding="utf-8", errors="replace").splitlines()
    body = osort.section(lines, "In the occupant's words")
    body = osort.trimmed(body if body is not None else lines)
    quoted = "\n".join(f"> {l}".rstrip() for l in body)
    return f"{head} The voice page's words, as he gave them:\n\n{quoted}"


def send(office_root, tray_root, words, slug, day, time, project_name=None):
    """Write the ask's out tray and its record. Returns {name, tray,
    files, opener}."""
    import json
    root = pathlib.Path(office_root)
    words = words.replace("\r\n", "\n").replace("\r", "\n").rstrip()
    if not words.strip():
        raise AskError("the question is empty: your words are the ask")
    project = None
    if project_name:
        found = [p for p in oh.read_projects(oh.read_toml(root / "floor-plan" / "manifest.toml")) or []
                 if p["name"] == project_name]
        if not found:
            raise AskError(f"{project_name} is none of this office's projects (office projects lists them)")
        project = found[0]
    name = name_for(root, tray_root, day, slug)
    tray = pathlib.Path(tray_root) / name
    tray.mkdir(parents=True)
    files = []

    def copy(dest, src, what):
        shutil.copyfile(src, tray / dest)
        files.append((dest, what))

    chapter_line = ""
    read_first = "Read the profile before you answer."
    if project:
        rel = f"handbook/{project['name']}.md"
        if (root / rel).is_file():
            copy(f"handbook-{project['name']}.md", root / rel,
                 f"{project['name']}'s handbook chapter: what the office knows of it, read first")
            read_first = ("Read the handbook chapter before you answer, and ask him nothing it already says.")
        else:
            chapter_line = (f"No handbook chapter for {project['name']} rides: nothing is filed about it yet, and "
                            "the first fact you leave starts its chapter.")
    for dest, rel, what in LETTERHEAD_FILES:
        if (root / rel).is_file():
            copy(dest, root / rel, what)
    if (root / "profile.md").is_file():
        copy("profile.md", root / "profile.md", "the office's profile: why it exists, its audiences and its house "
                                                "rules, which hold here before anything else")
    copy("OFFICE.md", DOCTRINE, "the office's doctrine: its core, to the banner marked PAST THE CORE, is what holds "
                                "for an answer")
    listing = "\n".join(f"- {dest}: {what}" for dest, what in files)
    about = (f"It is on {project['name']}, one of this office's projects." if project
             else "It is on the office itself, no project.")
    brief = oh.render_template((TEMPLATES / BRIEF_TEMPLATE).read_text(encoding="utf-8"), {
        "name": name, "about": about, "day": day, "time": time,
        "words": "\n".join(f"> {l}".rstrip() for l in words.split("\n")),
        "files": listing + (f"\n\n{chapter_line}" if chapter_line else ""),
        "voice": voice_words(root, project), "read_first": read_first,
    })
    (tray / BRIEF).write_text(brief, encoding="utf-8")
    files.insert(0, (BRIEF, "this brief"))
    opener = (f"office ask {name}: a quick question from my office, with no session behind it. Every file "
              f"attached is the office's context for it. Read {BRIEF} first, answer my question in this chat as "
              "it says, and end your last answer with the LEARNED block it describes.")
    record = {"office": str(root.resolve()), "name": name, "project": project["name"] if project else None,
              "day": day, "time": time, "words": words}
    record_path(tray_root, name).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return {"name": name, "tray": str(tray), "files": [f for f, _ in files], "opener": opener}


# --- the block ---------------------------------------------------------------------------

def spans(lines):
    """(begin, end) indexes of each complete block, in order, and the index
    of a BEGIN line no END follows (None when every BEGIN is closed)."""
    out, at = [], None
    for i, line in enumerate(lines):
        bare = line.strip()
        if bare.startswith(BEGIN_PREFIX):
            at = i
        elif bare == END and at is not None:
            out.append((at, i))
            at = None
    return out, at


def dedent(lines):
    """lines less the indent every line with words on it shares (a chat
    may indent a whole block); a line's own indent past that is kept."""
    widths = [len(l) - len(l.lstrip(" \t")) for l in lines if l.strip()]
    cut = min(widths) if widths else 0
    return [l[cut:] if l.strip() else "" for l in lines]


def name_of(text):
    """The name the text's last complete block carries, or None."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    found, _ = spans(lines)
    if not found:
        return None
    m = BEGIN_RE.match(lines[found[-1][0]].strip())
    return m.group(1) if m else None


def read_block(text, project_names=()):
    """The text's last LEARNED block, read: {name, answer (lines), handbook
    [(project, facts)], qa (lines)}. Raises AskError naming the line (of
    the text as given) for a text with no whole block and for a block off
    its shape."""
    import office_drop as odrop
    import office_sort as osort
    lines = [l.rstrip() for l in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    found, unclosed = spans(lines)
    if not found:
        if unclosed is not None:
            raise AskError(f"line {unclosed + 1}: a LEARNED BEGIN line with no {END} line after it, so the block "
                           "is not whole")
        raise AskError(f"no LEARNED block: a line `{BEGIN_PREFIX} ask-DATE-SLUG ---` and a line `{END}` around it")
    first, last = found[-1]
    m = BEGIN_RE.match(lines[first].strip())
    if not m or not oh.ASK_NAME_RE.match(m.group(1)):
        raise AskError(f"line {first + 1}: not `{BEGIN_PREFIX} ask-DATE-SLUG ---` (an ask's name): "
                       f"{lines[first].strip()}")
    name = m.group(1)
    body = dedent(lines[first + 1:last])
    at = first + 2   # the text's line number of body[0]

    heads = [h for h in osort.headings(body) if h[1] == 2]
    lead = [i for i, l in enumerate(body[:heads[0][0] if heads else len(body)]) if l.strip()]
    if lead:
        raise AskError(f"line {at + lead[0]}: a line before the block's first section (## Answer): "
                       f"{body[lead[0]].strip()}")
    seen = {}
    for n, (i, _, title) in enumerate(heads):
        if title not in SECTIONS:
            raise AskError(f"line {at + i}: `## {title}` is no section of an ask's block; it holds "
                           f"{', '.join('## ' + s for s in SECTIONS)} and nothing else")
        if title in seen:
            raise AskError(f"line {at + i}: a second `## {title}`; each section is there once")
        stop = heads[n + 1][0] if n + 1 < len(heads) else len(body)
        seen[title] = (i + 1, body[i + 1:stop])
    if "Answer" not in seen:
        raise AskError(f"line {first + 1}: the block has no `## Answer` section, and the answer is what the "
                       "notepad page keeps")
    answer = osort.trimmed(seen["Answer"][1])
    if not answer:
        raise AskError(f"line {at + seen['Answer'][0] - 1}: `## Answer` is empty")

    handbook = []
    if "Handbook" in seen:
        start, sub = seen["Handbook"]
        names = list(project_names)
        parts = [h for h in osort.headings(sub) if h[1] <= 3]
        lead = [i for i, l in enumerate(sub[:parts[0][0] if parts else len(sub)]) if l.strip()]
        if lead:
            raise AskError(f"line {at + start + lead[0]}: under `## Handbook` each project's facts sit under "
                           f"`### PROJECT`; this line is above the first: {sub[lead[0]].strip()}")
        for n, (i, level, title) in enumerate(parts):
            stop = parts[n + 1][0] if n + 1 < len(parts) else len(sub)
            if level != 3:
                raise AskError(f"line {at + start + i}: under `## Handbook` a project is `### PROJECT`, not "
                               f"{'#' * level} {title}")
            proj = odrop.resolve_project(title, names)
            if proj is None:
                raise AskError(f"line {at + start + i}: `### {title}` is none of this office's projects "
                               f"({', '.join(names) or 'it scopes none'}); a fact is filed in a project's chapter")
            inside = osort.fenced(sub)
            for j in range(i + 1, stop):
                line = sub[j]
                if not line.strip() or inside[j]:
                    continue
                if line.startswith("#"):
                    raise AskError(f"line {at + start + j}: an ask files facts alone, `- ` lines; "
                                   f"{line.strip()!r} is not one (a Front sheet is a session's to write)")
                if not (line.startswith("- ") or osort.is_continuation(line)):
                    raise AskError(f"line {at + start + j}: each fact is a `- ` line, bare: {line.strip()}")
            facts = [f for f in osort.list_items(sub[i + 1:stop]) if f]
            if facts:
                handbook.append((proj, facts))

    qa = []
    if "Questions and answers" in seen:
        start, sub = seen["Questions and answers"]
        inside = osort.fenced(sub)
        for j, line in enumerate(sub):
            if not line.strip():
                continue
            if inside[j] or not osort.QA_LINE_RE.match(line):
                raise AskError(f"line {at + start + j}: each line under `## Questions and answers` is `- DATE "
                               f"question? answer`: {line.strip()}")
            qa.append(line.rstrip())
    return {"name": name, "answer": answer, "handbook": handbook, "qa": qa}


# --- filing ------------------------------------------------------------------------------

def the_ask_out(office_root, tray_root, name):
    """The record of the ask named name, out from this office; AskError
    naming the asks that are out when it is not one of them."""
    out = asks_out(office_root, tray_root)
    for rec in out:
        if rec["name"] == name:
            return rec
    if (pathlib.Path(office_root) / page_rel(name)).exists():
        raise AskError(f"{name} is filed already, as {page_rel(name)}; nothing is filed twice")
    there = ", ".join(r["name"] for r in out) or "none"
    raise AskError(f"{name} is not an ask out from this office (out: {there}); office ask sends one out")


def page_text(rec, day, time, answer=None):
    """The ask's notepad page, whole: the notepad's heading and its words,
    then his words verbatim, then the Answer verbatim (or the line that
    says none was filed). ASCII, as every office page is."""
    title = f"ask {rec['name']}, on {where_words(rec)}"
    head = oh.render_template((TEMPLATES / NOTEPAD_TEMPLATE).read_text(encoding="utf-8"),
                              {"date": rec.get("day") or day, "title": title})
    parts = [head.rstrip("\n"), "", "## Asked", "",
             f"- asked: {rec.get('day', day)} {rec.get('time', '')}".rstrip()
             + f", through office ask, on {where_words(rec)}", "", *rec["words"].split("\n"), "", "## Answer", ""]
    if answer is None:
        parts += [f"- ended: {day} {time}, with nothing filed (office ask --learned none)"]
    else:
        parts += [f"- filed: {day} {time}, from the chat's LEARNED block", "", *answer]
    return oh.ascii_escape("\n".join(parts) + "\n")[0]


def file_block(office_root, tray_root, text, day, time):
    """File the text's last block. Returns (name, page rel, changed paths,
    said lines). Everything is checked before anything is written."""
    import office_sort as osort
    root = pathlib.Path(office_root)
    names = [p["name"] for p in oh.read_projects(oh.read_toml(root / "floor-plan" / "manifest.toml")) or []]
    block = read_block(text, names)
    rec = the_ask_out(root, tray_root, block["name"])
    page = page_rel(block["name"])
    (root / "notepad").mkdir(exist_ok=True)
    (root / page).write_text(page_text(rec, day, time, block["answer"]), encoding="ascii")
    changed, said = [page], [f"wrote {page}: your words and the answer"]
    for project, facts in block["handbook"]:
        paths, words = osort.file_handbook(root, project, facts, None, block["name"], day)
        changed += [p for p in paths if p not in changed]
        said += words
    if not block["handbook"]:
        said.append("no Handbook section, so no fact is filed")
    return block["name"], page, changed, said


def end_with_none(office_root, tray_root, name, day, time):
    root = pathlib.Path(office_root)
    rec = the_ask_out(root, tray_root, name)
    page = page_rel(name)
    (root / "notepad").mkdir(exist_ok=True)
    (root / page).write_text(page_text(rec, day, time), encoding="ascii")
    return page


def append_qa(office_root, name, text):
    """The block's Questions and answers lines appended to the ask's page,
    under a heading of their own. Returns how many."""
    root = pathlib.Path(office_root)
    names = [p["name"] for p in oh.read_projects(oh.read_toml(root / "floor-plan" / "manifest.toml")) or []]
    block = read_block(text, names)
    if block["name"] != name:
        raise AskError(f"the block is {block['name']}'s, not {name}'s")
    if not block["qa"]:
        return 0
    path = root / page_rel(name)
    if not path.is_file():
        raise AskError(f"{page_rel(name)} is not there to take the questions and answers")
    lines = ["", "## Questions and answers", "", *[oh.ascii_escape(q)[0] for q in block["qa"]]]
    with path.open("a", encoding="ascii") as f:
        f.write("\n".join(lines) + "\n")
    return len(block["qa"])


def close(tray_root, name):
    """Remove the ask's tray, its opener's copy and its record: the ask's
    own, and nothing else. Returns what was removed."""
    if not oh.ASK_NAME_RE.match(name):
        raise AskError(f"not an ask's name: {name!r}")
    gone = []
    tray = pathlib.Path(tray_root) / name
    if tray.is_dir():
        shutil.rmtree(tray)
        gone.append(str(tray))
    for path in (opener_path(tray_root, name), record_path(tray_root, name)):
        if path.is_file():
            path.unlink()
            gone.append(str(path))
    return gone


# --- the command line --------------------------------------------------------------------

def read_text(path):
    return pathlib.Path(path).read_bytes().decode("utf-8", "replace")


def build_parser():
    ap = argparse.ArgumentParser(prog="office_ask.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("send", help="write an ask's out tray and its record")
    p.add_argument("office"); p.add_argument("--tray-root", required=True); p.add_argument("--words-file", required=True)
    p.add_argument("--slug", default=""); p.add_argument("--day", required=True); p.add_argument("--time", required=True)
    p.add_argument("--project")
    p = sub.add_parser("out", help="the asks out from this office: NAME, PROJECT, WHEN, TRAY")
    p.add_argument("office"); p.add_argument("--tray-root", required=True)
    p = sub.add_parser("out-lines", help="the asks out, in the walk-in's words (--status: office status's line)")
    p.add_argument("office"); p.add_argument("--status", action="store_true")
    where = p.add_mutually_exclusive_group(required=True)
    where.add_argument("--tray-root"); where.add_argument("--machine-file", help="the tray root from its out_tray")
    p = sub.add_parser("name-of", help="the name in a text's last LEARNED block (exit 3: none)")
    p.add_argument("--file", required=True)
    p = sub.add_parser("file", help="file a text's last LEARNED block: the page, then the facts")
    p.add_argument("office"); p.add_argument("--tray-root", required=True); p.add_argument("--file", required=True)
    p.add_argument("--day", required=True); p.add_argument("--time", required=True)
    p = sub.add_parser("none", help="end an ask with its notepad page alone")
    p.add_argument("office"); p.add_argument("--tray-root", required=True); p.add_argument("--name", required=True)
    p.add_argument("--day", required=True); p.add_argument("--time", required=True)
    p = sub.add_parser("qa", help="append the block's Questions and answers to the ask's page")
    p.add_argument("office"); p.add_argument("--name", required=True); p.add_argument("--file", required=True)
    p = sub.add_parser("close", help="remove the ask's tray, its opener's copy and its record")
    p.add_argument("--tray-root", required=True); p.add_argument("--name", required=True)
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        if a.cmd == "send":
            got = send(a.office, a.tray_root, read_text(a.words_file), a.slug, a.day, a.time, a.project)
            print(f"name\t{got['name']}")
            print(f"tray\t{got['tray']}")
            for f in got["files"]:
                print(f"file\t{f}")
            print(f"opener\t{got['opener']}")
            return 0
        if a.cmd == "out":
            for r in asks_out(a.office, a.tray_root):
                print("\t".join([r["name"], r.get("project") or "-", f"{r.get('day', '')} {r.get('time', '')}".strip(),
                                 r["tray"]]))
            return 0
        if a.cmd == "out-lines":
            # From machine.toml (the walk-in's and status's batch read it
            # here, with no helper call of its own), else as given.
            import office_home as hs
            tray_root = a.tray_root or hs.tray_root_of(a.machine_file)
            out = asks_out(a.office, tray_root)
            if a.status:
                # office status's line, then (0.54.0) one for each record
                # whose tray is gone, with the line that removes it.
                if out:
                    print(status_line(out))
                for name, record, opener in orphans(a.office, tray_root):
                    print(orphan_line(name, record, opener))
            elif out:
                for r in out:
                    print(f"  {out_line(r)}")
            return 0
        if a.cmd == "name-of":
            found = name_of(read_text(a.file))
            if found is None:
                return 3
            print(found)
            return 0
        if a.cmd == "file":
            name, page, changed, said = file_block(a.office, a.tray_root, read_text(a.file), a.day, a.time)
            print(f"name\t{name}")
            print(f"page\t{page}")
            for p in changed:
                print(f"path\t{p}")
            for s in said:
                print(f"say\t{s}")
            return 0
        if a.cmd == "none":
            print(f"page\t{end_with_none(a.office, a.tray_root, a.name, a.day, a.time)}")
            return 0
        if a.cmd == "qa":
            n = append_qa(a.office, a.name, read_text(a.file))
            if not n:
                print("none")
                return 0
            print(f"page\t{page_rel(a.name)}")
            print(f"count\t{n}")
            return 0
        if a.cmd == "close":
            for g in close(a.tray_root, a.name):
                print(f"gone\t{g}")
            return 0
    except AskError as exc:
        log(f"error: {exc}")
        return 1
    except (oh.HelperError, OSError) as exc:
        log(f"error: {exc}")
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
