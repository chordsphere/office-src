#!/usr/bin/env python3
"""Where a sitting stands (0.43.0): its standing block, filed on its folder.

A planner sitting can run for twenty turns, and before 0.43.0 nothing in
the office showed where it stood: the home screen and the walk-in named a
read-only sitting as out, nothing more, and the occupant lost his place
(2026-10-27: "I'm lost and don't know where we are"). So a sitting prints
its standing at the end of any turn where its plan or its place in it
changed, one block kept to the byte as the ARISING block is (doctrine
section 4, continued; values illustrative):

    --- STANDING BEGIN 2026-10-26-walk-me-through-it-sitting-001 ---
    step 2 of 3: find where the work really ran
    - [x] probe the office, the install and the host
    - [>] find where the work really ran
    - [ ] draft the review's words
    waiting on you: run the probe below, then paste what came back
    --- STANDING END ---

The BEGIN line names the sitting's id. The first line inside is `step N
of M: words`; then one `- [x]`, `- [>]` or `- [ ]` line per step, M of
them, exactly one `[>]`, and it is the Nth; last a `waiting on you:`
line, `nothing` when the sitting is working. Of several blocks in one
text the last counts, since a paste of the whole chat holds each one the
sitting printed. A chat may indent the lines or end them with CR: each
line is read and kept with its blanks at either end dropped.

The office files the block on the sitting's folder as one page,
desk/FOLDER/standing.md (PAGE), replaced whole on each filing and
written by the office command alone, never by a session (a sitting lands
nothing; a work session on the folder has its own pages):

    # Where the sitting stands

    - as of: 2026-11-03 14:05
    - sitting: 2026-10-26-walk-me-through-it-sitting-001

    --- STANDING BEGIN 2026-10-26-walk-me-through-it-sitting-001 ---
    ...
    --- STANDING END ---

The time is the office's, in its timezone. A block that does not read is
refused by name, and the page is left as it was. The page is the
folder's, not one sitting's: when a sitting is succeeded it stays until
the successor files its own, its `- sitting:` line saying whose; office
land ending the sitting leaves it as the record of where it ended, and
office close moves it with the folder. Nothing deletes it.

Who files it: `office standing FOLDER [FILE | -]` (bin/office
cmd_standing: a file, stdin, or the clipboard on a terminal), office probe
when the text it reads carries a standing beside the probe block (split
takes it out, so it never runs as a line of the block), and the home
screen's key for a read-only sitting. Who shows it: the home screen's
item for the sitting, the walk-in's In flight line, and office desk under
a folder's next move (words).

The command line (bin/office calls it through pylib):

    office_standing.py check --file FILE [--office ROOT --folder REL]
        read the last block in FILE as the office files it: `sid SID` and
        `words WORDS`, or the refusal on stderr, exit 1; with the folder,
        the block's id must be a session the folder records
    office_standing.py split --file FILE --block-out B --standing-out S
        a probe's text with every standing block taken out (B), and the
        text's last standing block alone (S); prints `standing` or `none`;
        exit 1 when a BEGIN line has no END after it, since what follows
        it cannot be told from the probe's own lines
    office_standing.py write OFFICE FOLDER --file FILE --day DAY --time HH:MM
        check, then write FOLDER/standing.md; prints `sid SID` and `words
        WORDS`; exit 1, the page left as it was, when the block does not
        read
    office_standing.py show OFFICE FOLDER
        the folder's standing in the screens' words, or nothing

Standard library only. Logs to stderr with an [office] prefix; exits 0
when it did what it was asked, 1 on a refusal (the line says why), 2 on
a usage error.
"""

import argparse
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

PAGE = "standing.md"
HEADING = "# Where the sitting stands"
BEGIN_RE = oh.LazyPattern(r"^--- STANDING BEGIN (\S+) ---$")
BEGIN_PREFIX = "--- STANDING BEGIN"
END = "--- STANDING END ---"
STEP_RE = oh.LazyPattern(r"^step (\d+) of (\d+): (\S.*)$")
ITEM_RE = oh.LazyPattern(r"^- \[([ x>])\] (\S.*)$")
WAITING_RE = oh.LazyPattern(r"^waiting on you: (\S.*)$")
AS_OF_RE = oh.LazyPattern(r"^- as of: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})$")
SITTING_RE = oh.LazyPattern(r"^- sitting: (\S+)$")
# What the screens say when the sitting is working and waits on nothing.
NOTHING = "nothing"
MARKS = {"x": "done", ">": "now", " ": "to do"}


class StandingError(oh.HelperError):
    """A block the office does not file, said by name."""


def debug(msg):
    if os.environ.get("OFFICE_DEBUG"):
        print(f"[office] debug: {msg}", file=sys.stderr)


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


def lines_of(text):
    """The text's lines, line ends made LF and each line's blanks at
    either end dropped (a chat may indent a block, and a clipboard on WSL
    ends each line with CR)."""
    return [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def spans(lines):
    """(begin, end) line indexes of each complete standing block, in order,
    and the index of a BEGIN line no END follows (None when every BEGIN
    is closed). A BEGIN line inside an open block starts the block again:
    the earlier one was never closed."""
    out, at = [], None
    for i, line in enumerate(lines):
        if line.startswith(BEGIN_PREFIX):
            at = i
        elif line == END and at is not None:
            out.append((at, i))
            at = None
    return out, at


def read_block(text, recorded=None):
    """The last standing block in text, read: {sid, step, of, words, steps
    [(mark, words)], waiting, lines}, lines being the block from its BEGIN
    line to its END line as the page keeps them. Raises StandingError,
    naming the line, for a text with no complete block and for a block off
    the shape; given recorded (the sessions a folder records), for a block
    whose id is none of them."""
    lines = lines_of(text)
    found, unclosed = spans(lines)
    if not found:
        if unclosed is not None:
            raise StandingError(f"line {unclosed + 1}: a STANDING BEGIN line with no {END} line after it, so the "
                                "block is not whole")
        raise StandingError(f"no standing block: a line `{BEGIN_PREFIX} SID ---` and a line `{END}` around it")
    first, last = found[-1]
    m = BEGIN_RE.match(lines[first])
    if not m or not oh.SID_RE.match(m.group(1)):
        raise StandingError(f"line {first + 1}: not `{BEGIN_PREFIX} SID ---` (SID a session's id): {lines[first]}")
    sid = m.group(1)
    body = lines[first + 1:last]
    if not body:
        raise StandingError(f"line {first + 2}: the block is empty; its first line is `step N of M: words`")
    m = STEP_RE.match(body[0])
    if not m:
        raise StandingError(f"line {first + 2}: the block's first line is `step N of M: words`, not {body[0]!r}")
    step, of, words = int(m.group(1)), int(m.group(2)), m.group(3)
    if len(body) < 2:
        raise StandingError(f"line {first + 2}: the block ends with its step line; its last line is `waiting on "
                            "you: words`")
    m = WAITING_RE.match(body[-1])
    if not m:
        raise StandingError(f"line {last}: the block's last line is `waiting on you: words` (`waiting on you: "
                            f"{NOTHING}` when the sitting is working), not {body[-1]!r}")
    waiting = m.group(1)
    steps = []
    for n, line in enumerate(body[1:-1], first + 3):
        m = ITEM_RE.match(line)
        if not m:
            raise StandingError(f"line {n}: each line between the step line and the waiting line is one step, "
                                f"`- [x] words`, `- [>] words` or `- [ ] words`, not {line!r}")
        steps.append((m.group(1), m.group(2)))
    if of < 1 or len(steps) != of:
        raise StandingError(f"line {first + 2}: the step line says {of} step(s), and the block lists {len(steps)}")
    now = [i for i, (mark, _) in enumerate(steps, 1) if mark == ">"]
    if len(now) != 1:
        raise StandingError(f"exactly one step is `- [>]`, the one the sitting is on; the block marks {len(now)}")
    if now[0] != step:
        raise StandingError(f"line {first + 2}: the step line says step {step}, and the `- [>]` step is the "
                            f"{now[0]}{ordinal(now[0])}")
    if recorded is not None and sid not in recorded:
        raise StandingError(f"the block is {sid}'s, a session the folder does not record (it records: "
                            f"{', '.join(recorded) or 'none'})")
    return {"sid": sid, "step": step, "of": of, "words": words, "steps": steps, "waiting": waiting,
            "lines": lines[first:last + 1]}


def ordinal(n):
    return "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def split(text):
    """(the text with every standing block taken out, the last block's
    text or None) for office probe, whose text may carry a standing beside
    the probe block (the sitting prints both in one fence, the standing
    after the probe). The probe's own lines are kept as they came. Raises
    StandingError for a BEGIN line no END follows: the lines after it
    cannot be told from the probe's."""
    raw = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    found, unclosed = spans([line.strip() for line in raw])
    if unclosed is not None:
        raise StandingError(f"line {unclosed + 1}: a STANDING BEGIN line with no {END} line after it, so where the "
                            "probe block ends cannot be told; nothing ran")
    if not found:
        return text, None
    drop = set()
    for a, b in found:
        drop.update(range(a, b + 1))
    a, b = found[-1]
    standing = "\n".join(raw[a:b + 1]) + "\n"
    rest = "\n".join(line for i, line in enumerate(raw) if i not in drop)
    return rest, standing


def folder_of(office_root, text):
    """The desk folder (its directory name) that records the sitting the
    text's last standing block names (0.44.0): office probe given a text
    that holds a standing and no probe block, and no folder, files it
    there. Raises StandingError when the block does not read, or no folder
    on the desk, or more than one, records its sitting."""
    block = read_block(text)
    rels = [r for r in oh.folders_recording(office_root, block["sid"]) if r.startswith("desk/")]
    if not rels:
        raise StandingError(f"the block is {block['sid']}'s, and no folder on the desk records it")
    if len(rels) > 1:
        raise StandingError(f"the block is {block['sid']}'s, and {len(rels)} folders on the desk record it "
                            f"({', '.join(rels)}); name one")
    return rels[0].split("/", 1)[1]


def page_text(block, day, time):
    """standing.md for a block read_block returned, as of DAY TIME."""
    return "\n".join([HEADING, "", f"- as of: {day} {time}", f"- sitting: {block['sid']}", "", *block["lines"]]) + "\n"


def read_page(path):
    """The standing a folder's page holds: read_block's dict plus as_of
    and sitting (whose page it is), or None when there is no page or it
    does not read (said under OFFICE_DEBUG; a page is the office's and
    reads unless edited by hand)."""
    path = pathlib.Path(path)
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
        block = read_block(text)
    except (OSError, UnicodeDecodeError, StandingError) as exc:
        debug(f"{path} does not read as a standing, so none is shown: {exc}")
        return None
    as_of = sitting = None
    for line in lines_of(text):
        m = AS_OF_RE.match(line)
        if m and as_of is None:
            as_of = m.group(1)
        m = SITTING_RE.match(line)
        if m and sitting is None:
            sitting = m.group(1)
    return dict(block, as_of=as_of, sitting=sitting or block["sid"])


def folder_standing(office_root, rel):
    """The standing filed on a folder (space/name), or None."""
    return read_page(pathlib.Path(office_root) / rel / PAGE)


def words(st, sid=None):
    """A standing in the screens' words: `step 4 of 7: words; waiting on
    you: words (as of DATE TIME)`; given the sitting a screen names (sid),
    one filed by another sitting says whose it is."""
    out = f"step {st['step']} of {st['of']}: {st['words']}; waiting on you: {st['waiting']}"
    when = f"as of {st['as_of']}" if st.get("as_of") else ""
    whose = f"filed by {st['sitting']}" if sid and st.get("sitting") and st["sitting"] != sid else ""
    said = ", ".join(w for w in (when, whose) if w)
    return out + (f" ({said})" if said else "")


def write(office_root, rel, text, day, time):
    """Check the last block in text against the folder's recorded sessions
    and write the folder's page whole. Returns the block. Raises
    StandingError, the page left as it was, for a block that does not
    read, and HelperError for a folder that is not there."""
    md = pathlib.Path(office_root) / rel / "folder.md"
    if not md.is_file():
        raise oh.HelperError(f"{rel} has no folder.md")
    recorded = list(dict.fromkeys(oh.parse_folder(md.read_text(encoding="utf-8"))["sids"]))
    block = read_block(text, recorded)
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day) or not re.fullmatch(r"\d{2}:\d{2}", time):
        raise oh.HelperError(f"--day is YYYY-MM-DD and --time HH:MM, not {day!r} and {time!r}")
    page = md.parent / PAGE
    tmp = page.with_name(f".{PAGE}.tmp")
    tmp.write_text(page_text(block, day, time), encoding="utf-8")
    os.replace(tmp, page)
    return block


# --- the command line ------------------------------------------------------------------

def read_text(path):
    return pathlib.Path(path).read_bytes().decode("utf-8", "replace")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_standing.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("check", help="read the last standing block in a text: sid and words, or why not")
    p.add_argument("--file", required=True); p.add_argument("--office"); p.add_argument("--folder")
    p = sub.add_parser("split", help="a probe's text with its standing blocks taken out, and the last one alone")
    p.add_argument("--file", required=True); p.add_argument("--block-out", required=True)
    p.add_argument("--standing-out", required=True)
    p = sub.add_parser("write", help="file the text's last standing block as FOLDER/standing.md")
    p.add_argument("office"); p.add_argument("folder", help="desk/NAME")
    p.add_argument("--file", required=True); p.add_argument("--day", required=True); p.add_argument("--time", required=True)
    p = sub.add_parser("folder-of", help="the desk folder that records the last standing block's sitting (0.44.0)")
    p.add_argument("office"); p.add_argument("--file", required=True)
    p = sub.add_parser("show", help="a folder's standing in the screens' words, or nothing")
    p.add_argument("office"); p.add_argument("folder", help="desk/NAME")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "check":
            recorded = None
            if a.office and a.folder:
                md = pathlib.Path(a.office) / a.folder / "folder.md"
                recorded = list(dict.fromkeys(oh.parse_folder(md.read_text(encoding="utf-8"))["sids"]))
            block = read_block(read_text(a.file), recorded)
            print(f"sid\t{block['sid']}")
            print(f"words\t{words(block)}")
            return 0
        if a.cmd == "split":
            rest, standing = split(read_text(a.file))
            pathlib.Path(a.block_out).write_text(rest, encoding="utf-8")
            if standing is None:
                print("none")
                return 0
            pathlib.Path(a.standing_out).write_text(standing, encoding="utf-8")
            print("standing")
            return 0
        if a.cmd == "write":
            block = write(a.office, a.folder, read_text(a.file), a.day, a.time)
            print(f"sid\t{block['sid']}")
            print(f"words\t{words(dict(block, as_of=f'{a.day} {a.time}'))}")
            return 0
        if a.cmd == "folder-of":
            print(folder_of(a.office, read_text(a.file)))
            return 0
        if a.cmd == "show":
            st = folder_standing(a.office, a.folder)
            if st is not None:
                print(words(st))
            return 0
    except StandingError as exc:
        log(f"error: the standing block does not read: {exc}")
        return 1
    except (oh.HelperError, OSError) as exc:
        log(f"error: {exc}")
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
