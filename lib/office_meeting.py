#!/usr/bin/env python3
"""Meetings as a view over the work (0.26.0).

A meeting is not a job, and it gets no folder of its own. It is a dated
thing that happens, about some projects, and the office's view of the work
done on them. The occupant says it once, in his words (`office meeting`, the
home screen's m key): when it happens and what it concerns. The office
records it in the calendar and asks only when his words do not say when, or
name none of the office's projects; a recurring meeting is one line in the
plan, so it is never asked for again.

The calendar holds it, on the two pages the doctrine names (section 5),
in the office's own line forms, kept to the byte (values illustrative):

    calendar/plan.md, what should happen:
    - 2026-10-30 14:00 alpha review [about: alpha]
    - every mon 09:00 weekly review [about: alpha, beta]

    calendar/record.md, what happened:
    - 2026-10-26 09:00 weekly review: prep out, 2026-10-25-weekly-review-prep-001 [about: alpha, beta]
    - 2026-10-26 09:00 weekly review: held, 2026-10-25-weekly-review-prep-001; arose: in-tray/2026-10-26-update-the-report.md; dropped: in-tray/2026-10-26-call-back.md [about: alpha, beta]

Times are local, in the floor plan's timezone; bale's clock is UTC. A plan
line with no `[about: ...]` (written by hand, before 0.26.0) concerns the
office itself. A record line in any other shape is the occupant's own and
is read by office week, never by this module.

When a meeting is near (from NEAR_BEFORE ahead of it to NEAR_AFTER after it
starts), the home screen offers its prep: a read-only sitting sent through
the planner sitting's code (lib/office_planner.py), its goal the meeting's
words, carrying what landed on its projects since the last meeting that
concerned them (FIRST_WINDOW_DAYS for a first one), each project's handbook
chapter, its folders on the desk, the unsorted drops, and the drops tied to
the last meeting with the folders they became. The same sitting serves
before and during the meeting. Ending it (`office land`) records the meeting
held and files what the sitting wrote down as arising, in the block below,
as drops in the in-tray, tied to the meeting (values illustrative):

    --- ARISING BEGIN 2026-10-25-weekly-review-prep-001 ---

    ### Update the report with the new criteria

    - project: alpha

    The review asked for the new criteria from next week.

    --- ARISING END ---

A drop the occupant makes himself while a meeting's prep is out, from
TIE_BEFORE ahead of the meeting to TIE_AFTER after it starts, is tied to it
too (its record line's `dropped:`).

The command line (bin/office's; each prints on stdout, logs on stderr with
an [office] prefix, and exits 0 on success, 1 on a refusal, 2 on an
internal error, 3 when there is none):

    office_meeting.py read OFFICE --text-file F --today DAY --now HH:MM [--when TEXT]
        what his words say: title, when (canonical, or empty), need (when,
        time, or empty), concern NAME..., note TEXT...
    office_meeting.py record OFFICE --when CANON --title TITLE [--about NAME]...
        the plan line, written (the calendar arriving first when it must):
        line<tab>LINE, then the changed paths
    office_meeting.py near OFFICE --tz ZONE [--now ISO]
        the meetings near now: KEY<tab>STATE<tab>SID<tab>WORDS
    office_meeting.py resolve OFFICE [--want TEXT] --tz ZONE [--now ISO]
        the meeting a prep is for: key<tab>KEY, or choice<tab>KEY<tab>WORDS lines
    office_meeting.py gather OFFICE --key KEY --tz ZONE --day DAY --brief-out F --includes-out F
        the prep's includes and brief; the ride lines on stdout, PATH<tab>WHY
    office_meeting.py prep-out OFFICE --key KEY --sid SID
    office_meeting.py prep-of OFFICE --sid SID       KEY<tab>TITLE, or exit 3
    office_meeting.py arising-check OFFICE --sid SID --file F
    office_meeting.py held OFFICE --sid SID [--file F] --via VIA --day DAY --time HH:MM
    office_meeting.py tie OFFICE --page REL --tz ZONE [--now ISO]

Standard library only.
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
import office_drop as odrop  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = INSTALL / "templates"
SPACE = "calendar"
PLAN = "calendar/plan.md"
RECORD = "calendar/record.md"
PAGE_TEMPLATES = {"plan.md": "calendar-plan.md", "record.md": "calendar-record.md"}
BRIEF_TEMPLATE = "prep-brief.md"
MANIFEST_REL = "floor-plan/manifest.toml"
BALE_TOML_REL = "bale.toml"

# How near a meeting is when the home screen offers its prep: from a day
# before it starts until four hours after (the same sitting serves during
# it, so a prep forgotten until the meeting began is still worth sending).
NEAR_BEFORE = dt.timedelta(hours=24)
NEAR_AFTER = dt.timedelta(hours=4)
# A drop he makes while a prep is out is tied to its meeting from an hour
# before it starts until twelve hours after, or until the sitting ends.
TIE_BEFORE = dt.timedelta(hours=1)
TIE_AFTER = dt.timedelta(hours=12)
# What landed rides from this far back for a first meeting on a project.
FIRST_WINDOW_DAYS = 14
TITLE_LIMIT = 80

# The office itself, as a plan line's about names it.
THE_OFFICE = "the office"
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
DAY_NAMES = {"mon": "Monday", "tue": "Tuesday", "wed": "Wednesday", "thu": "Thursday", "fri": "Friday",
             "sat": "Saturday", "sun": "Sunday", "day": "day", "weekday": "weekday"}

ABOUT = r"(?: \[about: ([^\]]*)\])?"
PLAN_ONE_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) (.+?)" + ABOUT + r"$")
PLAN_SERIES_RE = re.compile(r"^- every (mon|tue|wed|thu|fri|sat|sun|day|weekday) (\d{2}:\d{2}) (.+?)" + ABOUT + r"$")
RECORD_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) ([^:]+?): (prep out|held), "
                       r"(\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*-\d{3})((?:; (?:arose|dropped): [^;\[]*)*)"
                       + ABOUT + r"$")
CANON_ONE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2})$")
CANON_SERIES_RE = re.compile(r"^every (mon|tue|wed|thu|fri|sat|sun|day|weekday) (\d{2}:\d{2})$")
KEY_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}) (.+)$")

ARISING_BEGIN_RE = re.compile(r"^--- ARISING BEGIN (\S+) ---$")
ARISING_END = "--- ARISING END ---"
ARISING_PROJECT_RE = re.compile(r"^- project: (.+)$")
NO_PROJECT = "none"


class MeetingError(oh.HelperError):
    """A refusal, said in the occupant's words."""


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


def zone(name):
    """The office's zone, or UTC when it does not resolve here (said under
    OFFICE_DEBUG; office_tz in bin/office says it loudly)."""
    if name and name != "UTC":
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo(name)
        except Exception as exc:  # ZoneInfoNotFoundError, ValueError: UTC stands
            debug(f"the zone {name!r} does not resolve here ({exc}); times are UTC")
    return dt.timezone.utc


def now_in(tz, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    return now.astimezone(tz)


# --- his words: when, and the title ----------------------------------------------------

DAYNAME_FULL = r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
DAYNAME_ANY = r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tues|tue|wed|thurs|thur|thu|fri|sat|sun)"
DAY_WORDS = {"monday": "mon", "mon": "mon", "tuesday": "tue", "tues": "tue", "tue": "tue", "wednesday": "wed",
             "wed": "wed", "thursday": "thu", "thurs": "thu", "thur": "thu", "thu": "thu", "friday": "fri",
             "fri": "fri", "saturday": "sat", "sat": "sat", "sunday": "sun", "sun": "sun"}
MONTHNAME = r"(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|oct|nov|dec)"
MONTH_WORDS = {"january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4, "apr": 4, "may": 5,
               "june": 6, "jun": 6, "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sept": 9, "sep": 9,
               "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12}
ORD = r"(?:st|nd|rd|th)?"

SERIES_PATTERNS = (
    (re.compile(r"\b(?:every|each)\s+(weekday|day)s?\b", re.I), lambda m: m.group(1).lower()),
    (re.compile(r"\b(?:every|each)\s+(?:week\s+on\s+)?" + DAYNAME_ANY + r"s?\b", re.I),
     lambda m: DAY_WORDS[m.group(1).lower()]),
    (re.compile(r"\bweekly\s+on\s+" + DAYNAME_ANY + r"s?\b", re.I), lambda m: DAY_WORDS[m.group(1).lower()]),
    (re.compile(r"\bdaily\b", re.I), lambda m: "day"),
    (re.compile(r"\b(?:on\s+)?weekdays\b", re.I), lambda m: "weekday"),
    (re.compile(r"\bon\s+" + DAYNAME_FULL + r"s\b", re.I), lambda m: DAY_WORDS[m.group(1).lower()]),
)

DATE_ISO_RE = re.compile(r"\b(?:on\s+)?(\d{4})-(\d{2})-(\d{2})\b", re.I)
DATE_RELATIVE_RE = re.compile(r"\b(today|tonight|tomorrow)\b", re.I)
DATE_DAY_MONTH_RE = re.compile(r"\b(?:on\s+)?(?:the\s+)?(\d{1,2})" + ORD + r"\s+(?:of\s+)?" + MONTHNAME
                               + r"\.?(?:,?\s+(\d{4}))?\b", re.I)
DATE_MONTH_DAY_RE = re.compile(r"\b(?:on\s+)?" + MONTHNAME + r"\.?\s+(\d{1,2})" + ORD + r"(?:,?\s+(\d{4}))?\b", re.I)
DATE_SLASH_RE = re.compile(r"\b(?:on\s+)?(\d{1,2})/(\d{1,2})(?:/(\d{4}|\d{2}))?\b", re.I)
DATE_WEEKDAY_RE = re.compile(r"\b(?:(?:on|next|this)\s+)+" + DAYNAME_ANY + r"\b|\b" + DAYNAME_FULL + r"\b", re.I)

TIME_NOON_RE = re.compile(r"\b(?:at\s+)?(noon|midday)\b", re.I)
TIME_AMPM_RE = re.compile(r"\b(?:at\s+)?(\d{1,2})(?:[:.](\d{2}))?\s*([ap])\.?\s?m\b\.?", re.I)
TIME_CLOCK_RE = re.compile(r"\b(?:at\s+)?([01]?\d|2[0-3]):([0-5]\d)\b", re.I)
TIME_OCLOCK_RE = re.compile(r"\b(?:at\s+)?(\d{1,2})\s+o'?clock\b", re.I)
TIME_BARE_RE = re.compile(r"\bat\s+(\d{1,2})\b(?![:/.\-]\d)", re.I)


def afternoon(hour, notes, said, minute=0):
    """A bare hour from 1 to 6 with no am or pm is taken as the afternoon,
    when meetings happen, and said."""
    if 1 <= hour <= 6:
        notes.append(f"{said} is taken as {hour + 12:02d}:{minute:02d}, the afternoon (say am to mean the morning)")
        return hour + 12
    return hour


def read_when(text, today, now_hhmm):
    """What his words say of when: a dict with kind (one, series, or None),
    date (YYYY-MM-DD), day (mon..sun, day, weekday), time (HH:MM), spans
    (the (start, end) of each phrase taken, for the title) and notes (what
    was taken that he might not mean). today is the office's local date,
    now_hhmm its local time: a time alone is today when it is still to
    come, else tomorrow."""
    today = dt.date.fromisoformat(today) if isinstance(today, str) else today
    out = {"kind": None, "date": None, "day": None, "time": None, "spans": [], "notes": [], "derived": False}
    taken = []

    def free(m):
        return not any(m.start() < e and s < m.end() for s, e in taken)

    def take(m):
        taken.append((m.start(), m.end()))

    for rx, day in SERIES_PATTERNS:
        m = next((m for m in rx.finditer(text) if free(m)), None)
        if m:
            out.update(kind="series", day=day(m))
            take(m)
            break
    if out["kind"] is None:
        out["date"] = read_date(text, today, free, take, out["notes"])
        if out["date"]:
            out["kind"] = "one"
    hour = minute = None
    for rx in (TIME_NOON_RE, TIME_AMPM_RE, TIME_CLOCK_RE, TIME_OCLOCK_RE, TIME_BARE_RE):
        m = next((m for m in rx.finditer(text) if free(m)), None)
        if not m:
            continue
        if rx is TIME_NOON_RE:
            hour, minute = 12, 0
        elif rx is TIME_AMPM_RE:
            h, mm, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3).lower()
            if not 1 <= h <= 12 or mm > 59:
                continue
            hour, minute = (h % 12) + (12 if ap == "p" else 0), mm
        elif rx is TIME_CLOCK_RE:
            h, mm = int(m.group(1)), int(m.group(2))
            # 3:30 is the afternoon, as a bare 3 is; 03:30 is written as a
            # 24-hour clock writes it, and stands.
            hour = afternoon(h, out["notes"], m.group(0).strip(), mm) if len(m.group(1)) == 1 else h
            minute = mm
        else:
            h = int(m.group(1))
            if h > 23:
                continue
            hour, minute = afternoon(h, out["notes"], m.group(0).strip()), 0
        take(m)
        break
    if hour is not None:
        out["time"] = f"{hour:02d}:{minute:02d}"
    if out["kind"] is None and out["time"]:
        # A time alone: the next one, today or tomorrow.
        when = today if out["time"] > now_hhmm else today + dt.timedelta(days=1)
        out.update(kind="one", date=when.isoformat(), derived=True)
        out["notes"].append(f"no day was said, so it is {'today' if when == today else 'tomorrow'}, "
                            f"{when.isoformat()}")
    out["spans"] = sorted(taken)
    return out


def read_date(text, today, free, take, notes):
    """The first date his words say, as YYYY-MM-DD, taking its phrase; None
    when they say none. A date that is no date (the 31st of a short month)
    is said and not taken."""
    found = []
    for rx in (DATE_ISO_RE, DATE_RELATIVE_RE, DATE_DAY_MONTH_RE, DATE_MONTH_DAY_RE, DATE_SLASH_RE, DATE_WEEKDAY_RE):
        m = next((m for m in rx.finditer(text) if free(m)), None)
        if m:
            found.append((m.start(), rx, m))
    for _, rx, m in sorted(found, key=lambda x: x[0]):
        try:
            if rx is DATE_ISO_RE:
                d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            elif rx is DATE_RELATIVE_RE:
                d = today + dt.timedelta(days=1 if m.group(1).lower() == "tomorrow" else 0)
            elif rx is DATE_WEEKDAY_RE:
                word = (m.group(1) or m.group(2)).lower()
                target = DAYS.index(DAY_WORDS[word])
                ahead = (target - today.weekday()) % 7
                if ahead == 0 and re.search(r"\bnext\b", m.group(0), re.I):
                    ahead = 7
                d = today + dt.timedelta(days=ahead)
            else:
                if rx is DATE_DAY_MONTH_RE:
                    day, month, year = int(m.group(1)), MONTH_WORDS[m.group(2).lower()], m.group(3)
                elif rx is DATE_MONTH_DAY_RE:
                    month, day, year = MONTH_WORDS[m.group(1).lower()], int(m.group(2)), m.group(3)
                else:
                    month, day, year = int(m.group(1)), int(m.group(2)), m.group(3)
                if year:
                    y = int(year) + (2000 if len(year) == 2 else 0)
                    d = dt.date(y, month, day)
                else:
                    d = dt.date(today.year, month, day)
                    if d < today - dt.timedelta(days=1):
                        d = dt.date(today.year + 1, month, day)
                        notes.append(f"{m.group(0).strip()} has passed this year, so it is {d.isoformat()}")
        except ValueError:
            notes.append(f"{m.group(0).strip()!r} is not a date, so it is not taken")
            continue
        take(m)
        return d.isoformat()
    return None


def title_of(text, spans):
    """The meeting's words with what said when taken out, as one line kept
    ASCII: the title the plan line carries and the prep's goal. Colons and
    brackets are made commas and parentheses, since the plan and record
    lines read them; a title that comes out empty is `meeting`."""
    keep, last = [], 0
    for s, e in spans:
        keep.append(text[last:s])
        last = e
    keep.append(text[last:])
    words = " ".join(" ".join(keep).split())
    words = re.sub(r"\s+([,.;!?])", r"\1", words)
    words = re.sub(r"([,;])(?:\s*[,;])+", r"\1", words)
    for _ in range(3):
        words = re.sub(r"^(?:[,;.\-]\s*|(?:at|on|every|each|from|in|for|and)\s+)", "", words, flags=re.I)
        words = re.sub(r"(?:\s*[,;\-]|\s+(?:at|on|every|each|from|in|for|and|the))$", "", words, flags=re.I)
    words = words.replace(":", ",").replace("[", "(").replace("]", ")").strip(" ,;.-")
    words = oh.ascii_escape(words)[0]
    if len(words) > TITLE_LIMIT:
        words = words[:TITLE_LIMIT + 1].rsplit(" ", 1)[0].rstrip(" ,;.-") + "..."
    return words or "meeting"


def canon(when):
    """The canonical when: `YYYY-MM-DD HH:MM` or `every DAY HH:MM`; None
    when it lacks the day or the time."""
    if not when["time"]:
        return None
    if when["kind"] == "series" and when["day"]:
        return f"every {when['day']} {when['time']}"
    if when["kind"] == "one" and when["date"]:
        return f"{when['date']} {when['time']}"
    return None


def merge(words, answer):
    """His words' when, with what an answer (--when, or the question) says
    standing over it: a series or a date it says replaces his words', and
    a time it says fills or replaces theirs. A day worked out from a time
    alone (today or tomorrow) is taken only when nothing else gives one."""
    out = dict(words, notes=[n for n in words["notes"]])
    if answer["kind"] == "series":
        out.update(kind="series", day=answer["day"], date=None, derived=False)
    elif answer["kind"] == "one" and not answer["derived"]:
        out.update(kind="one", date=answer["date"], day=None, derived=False)
    if answer["time"]:
        out["time"] = answer["time"]
    if (out["kind"] is None or out["derived"]) and answer["kind"] == "one" and answer["derived"]:
        out.update(kind="one", date=answer["date"], derived=True)
    if out["derived"] and not answer["derived"]:
        out["notes"] = [n for n in out["notes"] if not n.startswith("no day was said")]
    out["notes"] += [n for n in answer["notes"] if not (n.startswith("no day was said") and not out["derived"])]
    return out


def when_words(canonical):
    """A canonical when in words: `Friday 2026-10-30 at 14:00`, `every Monday at 09:00`."""
    m = CANON_SERIES_RE.match(canonical)
    if m:
        return f"every {DAY_NAMES[m.group(1)]} at {m.group(2)}"
    m = CANON_ONE_RE.match(canonical)
    if m:
        d = dt.date.fromisoformat(m.group(1))
        return f"{DAY_NAMES[DAYS[d.weekday()]]} {m.group(1)} at {m.group(2)}"
    return canonical


def concerns_named(text, names):
    return [n for n in names if re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", text, re.I)]


# --- the calendar's pages ----------------------------------------------------------------

def about_list(text):
    return [a.strip() for a in (text or "").split(",") if a.strip()]


def about_suffix(about):
    return f" [about: {', '.join(about)}]" if about else ""


def read_lines(path):
    p = pathlib.Path(path)
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8", errors="replace").splitlines()


def plain_title(text):
    """A plan line's title as the record line can carry it: a colon or a
    bracket written by hand made a comma or a parenthesis, as title_of
    makes them for what office meeting writes."""
    return " ".join(text.replace(":", ",").replace("[", "(").replace("]", ")").split())


def read_plan(root):
    """(meetings, problems): each plan line the office reads, a dict with
    n (its line), series (a DAY, or None), date, time, title, about; the
    problems are the bullets that read as neither shape (office week says
    them too)."""
    lines = read_lines(pathlib.Path(root) / PLAN)
    out, problems = [], []
    for n, line in enumerate(lines or [], 1):
        if not line.startswith("- "):
            continue
        m = PLAN_ONE_RE.match(line.rstrip())
        if m:
            out.append({"n": n, "series": None, "date": m.group(1), "time": m.group(2),
                        "title": plain_title(m.group(3)), "about": about_list(m.group(4))})
            continue
        m = PLAN_SERIES_RE.match(line.rstrip())
        if m:
            out.append({"n": n, "series": m.group(1), "date": None, "time": m.group(2),
                        "title": plain_title(m.group(3)), "about": about_list(m.group(4))})
            continue
        problems.append(f"{PLAN} line {n}: {line}")
    return out, problems


def read_record(root):
    """The record lines the office wrote for meetings, each a dict: n, date,
    time, title, state (prep out, held), sid, arose, dropped, about, key."""
    lines = read_lines(pathlib.Path(root) / RECORD)
    out = []
    for n, line in enumerate(lines or [], 1):
        m = RECORD_RE.match(line.rstrip())
        if not m:
            continue
        lists = {"arose": [], "dropped": []}
        for part in (m.group(6) or "").split("; ")[1:]:
            k, _, v = part.partition(": ")
            lists[k] = [x.strip() for x in v.split(",") if x.strip()]
        out.append({"n": n, "date": m.group(1), "time": m.group(2), "title": m.group(3).strip(),
                    "state": m.group(4), "sid": m.group(5), "arose": lists["arose"], "dropped": lists["dropped"],
                    "about": about_list(m.group(7)), "key": f"{m.group(1)} {m.group(2)} {m.group(3).strip()}"})
    return out


def render_record(r):
    parts = [f"{r['state']}, {r['sid']}"]
    if r["arose"]:
        parts.append("arose: " + ", ".join(r["arose"]))
    if r["dropped"]:
        parts.append("dropped: " + ", ".join(r["dropped"]))
    return f"- {r['date']} {r['time']} {r['title']}: {'; '.join(parts)}{about_suffix(r['about'])}"


def write_record_line(root, r):
    """Write r over its own line (r['n']), or at the end when it has none;
    every other byte of the page kept."""
    path = pathlib.Path(root) / RECORD
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    line = render_record(r)
    if r.get("n"):
        lines[r["n"] - 1] = line
        path.write_text("\n".join(lines), encoding="utf-8")
    else:
        path.write_text(text + ("" if text.endswith("\n") or not text else "\n") + line + "\n", encoding="utf-8")


def occurrences(plan, first, last):
    """Every meeting the plan says happens from the date first to last,
    inclusive: dicts with date, time, title, about, series, key."""
    out = []
    for p in plan:
        if p["series"] is None:
            d = dt.date.fromisoformat(p["date"])
            if first <= d <= last:
                out.append(occurrence(p, d))
            continue
        d = first
        while d <= last:
            if p["series"] == "day" or (p["series"] == "weekday" and d.weekday() < 5) \
                    or p["series"] == DAYS[d.weekday()]:
                out.append(occurrence(p, d))
            d += dt.timedelta(days=1)
    return sorted(out, key=lambda o: (o["date"], o["time"], o["title"]))


def occurrence(p, d):
    return {"date": d.isoformat(), "time": p["time"], "title": p["title"], "about": list(p["about"]),
            "series": p["series"], "key": f"{d.isoformat()} {p['time']} {p['title']}"}


def start_of(o, tz):
    return dt.datetime.combine(dt.date.fromisoformat(o["date"]), dt.time.fromisoformat(o["time"]), tzinfo=tz)


def occurrence_words(o):
    when = when_words(f"{o['date']} {o['time']}")
    series = f", every {DAY_NAMES[o['series']]}" if o.get("series") else ""
    return f"{o['title']} ({when}{series})"


def near(root, tz, now=None):
    """The meetings near now (NEAR_BEFORE before to NEAR_AFTER after they
    start) that are not recorded held, each an occurrence with state `due`
    (no prep out) or `prep out` and its sid; and every prep still out,
    whenever its meeting is."""
    here = now_in(tz, now)
    plan, _ = read_plan(root)
    records = {r["key"]: r for r in read_record(root)}
    out, seen = [], set()
    for o in occurrences(plan, here.date() - dt.timedelta(days=1), here.date() + dt.timedelta(days=2)):
        start = start_of(o, tz)
        if not (start - NEAR_BEFORE <= here <= start + NEAR_AFTER):
            continue
        r = records.get(o["key"])
        if r and r["state"] == "held":
            continue
        out.append(dict(o, state="prep out" if r else "due", sid=r["sid"] if r else ""))
        seen.add(o["key"])
    for r in records.values():
        if r["state"] == "prep out" and r["key"] not in seen:
            out.append({"date": r["date"], "time": r["time"], "title": r["title"], "about": r["about"],
                        "series": None, "key": r["key"], "state": "prep out", "sid": r["sid"]})
    return sorted(out, key=lambda o: (o["date"], o["time"], o["title"]))


def planned(root, key, tz):
    """The occurrence a key names (DATE HH:MM TITLE), when the plan holds
    it: a one-off on that day, or a series that falls on it. None else."""
    m = KEY_RE.match(key.strip())
    if not m:
        return None
    try:
        d = dt.date.fromisoformat(m.group(1))
    except ValueError:
        return None
    plan, _ = read_plan(root)
    for o in occurrences(plan, d, d):
        if o["key"] == " ".join(key.split()):
            return o
    return None


def resolve(root, want, tz, now=None):
    """(occurrence, choices): the meeting a prep is for. want is a key, or
    words that name one near meeting (a part of its title, or its date and
    time); without want, the one near meeting due. With several that fit,
    choices are them all and occurrence is None. Raises MeetingError when
    none fits."""
    if want:
        o = planned(root, want, tz)
        if o:
            r = record_for(root, o["key"])
            if r and r["state"] == "prep out":
                raise MeetingError(f"the prep for {o['key']} is out already ({r['sid']}): office land {r['sid']} ends "
                                   "it when the meeting is over")
            if r:
                raise MeetingError(f"{o['key']} is recorded held already ({RECORD} line {r['n']}); its prep is not "
                                   "sent again")
            return o, []
    due = [o for o in near(root, tz, now) if o["state"] == "due"]
    if want:
        low = want.lower().strip()
        fits = [o for o in due if low in o["key"].lower()]
        if len(fits) == 1:
            return fits[0], []
        if fits:
            return None, fits
        raise MeetingError(f"no meeting the calendar plans is named {want!r}, and none near now fits it: "
                           "office start --prep 'YYYY-MM-DD HH:MM TITLE' names one the plan holds (office week lists "
                           "this week's)")
    if len(due) == 1:
        return due[0], []
    if due:
        return None, due
    raise MeetingError("no meeting is near (from a day before one until four hours after it starts) with its prep "
                       "still to send: office meeting records one; office start --prep 'YYYY-MM-DD HH:MM TITLE' "
                       "sends the prep of any meeting the plan holds")


def prep_of(root, sid):
    """The record line of the meeting whose prep is sid, or None."""
    return next((r for r in read_record(root) if r["sid"] == sid), None)


def record_for(root, key):
    return next((r for r in read_record(root) if r["key"] == key), None)


# --- the calendar arrives, and a meeting is recorded -------------------------------------

def arrive(root):
    """Make the calendar arrive, or finish arriving, with the first meeting
    (as the in-tray arrives with the first drop): its two pages from the
    install's templates, the floor plan's entry as the catalog declares it
    and bale.toml's trigger, each only when missing. Returns (changed
    paths, words for the log)."""
    root = pathlib.Path(root)
    entry = od.catalog_entry(space=SPACE)
    changed, words = [], []
    (root / SPACE).mkdir(exist_ok=True)
    for page, template in PAGE_TEMPLATES.items():
        path = root / SPACE / page
        if not path.exists():
            path.write_text((TEMPLATES / template).read_text(encoding="utf-8"), encoding="utf-8")
            changed.append(f"{SPACE}/{page}")
            words.append(f"the calendar arrives in this office: made {SPACE}/{page} from the install's template")
    if od.add_space_to_floor_plan(root / MANIFEST_REL, entry, SPACE):
        changed.append(MANIFEST_REL)
        words.append(f"the floor plan now lists the {SPACE} space, as the install's catalog declares it")
    added = od.add_include_trigger(root / BALE_TOML_REL, entry["path"])
    if added:
        changed.append(BALE_TOML_REL)
        words.append(f"bale.toml's include group now triggers on {entry['path']}")
    elif added is None:
        words.append(f"bale.toml has no include group to add {entry['path']} to (office status says so)")
    return changed, words


def plan_line(when, title, about):
    m = CANON_SERIES_RE.match(when)
    if m:
        return f"- every {m.group(1)} {m.group(2)} {title}{about_suffix(about)}"
    m = CANON_ONE_RE.match(when)
    if not m:
        raise MeetingError(f"when is YYYY-MM-DD HH:MM or every DAY HH:MM, not {when!r}")
    dt.date.fromisoformat(m.group(1))
    dt.time.fromisoformat(m.group(2))
    return f"- {m.group(1)} {m.group(2)} {title}{about_suffix(about)}"


def record_meeting(root, when, title, about):
    """The plan line for a meeting, written at the end of calendar/plan.md,
    the calendar arriving first when it must. Returns (line, changed paths,
    words). A meeting the plan holds already, at that time with that title,
    is said and not written again."""
    root = pathlib.Path(root)
    title = title_of(title, [])
    line = plan_line(when, title, about)
    changed, words = arrive(root)
    plan, _ = read_plan(root)
    for p in plan:
        same_when = (f"every {p['series']} {p['time']}" if p["series"] else f"{p['date']} {p['time']}") == when
        if same_when and p["title"].lower() == title.lower():
            words.append(f"the plan holds this meeting already ({PLAN} line {p['n']}); nothing more is written")
            return line, changed, words
    path = root / PLAN
    text = path.read_text(encoding="utf-8")
    path.write_text(text + ("" if text.endswith("\n") or not text else "\n") + line + "\n", encoding="utf-8")
    if PLAN not in changed:
        changed.append(PLAN)
    return line, changed, words


def mark_prep_out(root, key, sid, tz):
    """The record line that says the meeting's prep is out, by its sid (a
    calendar that came without its record page, by hand or by an older
    renovation, gets it first). Returns the changed paths."""
    o = planned(root, key, tz)
    if o is None:
        raise MeetingError(f"the plan holds no meeting {key!r}")
    if record_for(root, key):
        raise MeetingError(f"{key} has a record line already; its prep is not sent twice")
    changed, words = ([], []) if (pathlib.Path(root) / RECORD).is_file() else arrive(root)
    for w in words:
        log(w)
    write_record_line(root, {"date": o["date"], "time": o["time"], "title": o["title"], "state": "prep out",
                             "sid": sid, "arose": [], "dropped": [], "about": o["about"]})
    return [c for c in changed if c != RECORD] + [RECORD]


# --- the prep: what rides, and its brief -------------------------------------------------

def concerns_of(about, names):
    """The planner's concerns for a meeting's about: its projects that the
    office scopes, and the office itself (office_planner.OFFICE)."""
    import office_planner as op
    out = [a for a in about if a in names]
    if THE_OFFICE in about or not out:
        out.append(op.OFFICE)
    return out


def last_meeting(records, concern, before):
    """The latest record before the start key `before` (DATE HH:MM) whose
    meeting concerns `concern`, or None."""
    import office_planner as op
    found = None
    for r in records:
        if f"{r['date']} {r['time']}" >= before:
            continue
        on = r["about"] or [THE_OFFICE]
        if (concern == op.OFFICE and THE_OFFICE in on) or concern in on:
            if found is None or (r["date"], r["time"]) > (found["date"], found["time"]):
                found = r
    return found


def where_drop(root, name):
    """(page rel, folder rel or None) for a drop's page by its file name,
    wherever it is now: in the in-tray, or moved whole into a folder's
    drops/ (on the desk or in the filing cabinet); (None, None) when it is
    nowhere."""
    root = pathlib.Path(root)
    if (root / odrop.SPACE / name).is_file():
        return f"{odrop.SPACE}/{name}", None
    for space in ("desk", "filing-cabinet"):
        for p in sorted((root / space).glob(f"*/drops/{name}")):
            folder = p.parent.parent
            return f"{space}/{folder.name}/drops/{name}", f"{space}/{folder.name}"
    return None, None


def gather_prep(root, o, tz, names=None, today=None):
    """What rides with a meeting's prep beside what every sitting carries,
    in order, each an office_planner entry: each project's handbook
    chapter; the folders on the desk on its concerns; what landed on each
    since the last meeting that concerned it (FIRST_WINDOW_DAYS back for a
    first), newest first; and the drops tied to each concern's last
    meeting, with the folders they became. Returns (entries, windows):
    windows says each concern's window, in words."""
    import office_planner as op
    root = pathlib.Path(root)
    names = op.project_names(root) if names is None else names
    concerns = concerns_of(o["about"], names)
    records = read_record(root)
    start = start_of(o, tz)
    out, windows, lasts = [], {}, {}
    for c in concerns:
        if c == op.OFFICE:
            continue
        rel = op.osort.chapter_rel(c)
        if (root / rel).is_file():
            out.append(op.entry(rel, f"{c}'s handbook chapter: what the office knows of {c} that its repo does not say",
                                "chapter"))
    folders = [f for f in oh.read_folders(root) if f["problem"] is None]
    place = lambda f: op.folder_project(f, names) or THE_OFFICE  # noqa: E731
    for f in folders:
        if f["space"] != "desk" or not op.concerns_folder(f, concerns, names):
            continue
        out.append(op.entry(f"{f['rel']}/folder.md",
                            f"{oh.cite(f)}, {f.get('title') or f['name']}: on the desk, {f.get('status') or 'no status line'}, "
                            f"on {place(f)}", "folder"))
    for c in concerns:
        last = last_meeting(records, c, f"{o['date']} {o['time']}")
        lasts[c] = last
        label = THE_OFFICE if c == op.OFFICE else c
        if last:
            since = start_of(last, tz)
            windows[c] = (since, f"since the last meeting on {label}, {last['title']} on {last['date']} {last['time']}")
        else:
            since = start - dt.timedelta(days=FIRST_WINDOW_DAYS)
            windows[c] = (since, f"in the {FIRST_WINDOW_DAYS} days before it (no earlier meeting on {label} is "
                                 "recorded)")
    filed = op.walkthroughs_filed(root, None)
    landed = []
    for f in folders:
        when = filed.get(f["name"])
        if when is None or not op.concerns_folder(f, concerns, names) or not (f["path"].parent / "walkthrough.md").is_file():
            continue
        c = op.folder_project(f, names) or op.OFFICE
        if c not in windows:
            continue
        since, words = windows[c]
        if dt.datetime.fromisoformat(when) < since:
            continue
        landed.append(op.entry(f"{f['rel']}/walkthrough.md",
                               f"what landed on {place(f)} {words}: {oh.cite(f)}'s walkthrough, filed {when[:10]}",
                               "landed", when))
    out += sorted(landed, key=lambda e: e["at"], reverse=True)
    have = {e["path"] for e in out}
    for c in concerns:
        last = lasts.get(c)
        if not last:
            continue
        for kind, pages in (("arose", last["arose"]), ("dropped", last["dropped"])):
            for page in pages:
                rel, folder = where_drop(root, pathlib.PurePosixPath(page).name)
                said = "arose in" if kind == "arose" else "was dropped during"
                if rel is None:
                    debug(f"{page}, tied to {last['key']}, is nowhere in the office now")
                    continue
                if rel not in have:
                    out.append(op.entry(rel, f"a drop that {said} the last meeting on "
                                             f"{THE_OFFICE if c == op.OFFICE else c} ({last['title']}, {last['date']})"
                                             + (f", now in {folder}" if folder else ", still in the in-tray"), "tied"))
                    have.add(rel)
                if folder and f"{folder}/folder.md" not in have:
                    out.append(op.entry(f"{folder}/folder.md", f"the folder that drop became: {folder}", "tied"))
                    have.add(f"{folder}/folder.md")
    return out, {c: w for c, (_, w) in windows.items()}


def concern_words(about):
    named = [a for a in about if a != THE_OFFICE]
    words = ", ".join(named)
    if THE_OFFICE in about or not named:
        words = (words + ", and " if words else "") + "the office itself"
    return words


def render_brief(o, tz_name, day, rides, left, windows):
    import office_planner as op
    ride_lines = [f"- {path}: {why}" for path, why in rides]
    ride_lines += [f"- left out for bale's caps: {e['path']} ({e['why']})" for e in left]
    window_lines = [f"- {THE_OFFICE if c == op.OFFICE else c}: {w}" for c, w in windows.items()]
    template = (TEMPLATES / BRIEF_TEMPLATE).read_text(encoding="utf-8")
    return oh.render_template(template, {
        "day": day, "title": o["title"], "when": when_words(f"{o['date']} {o['time']}"), "tz": tz_name or "UTC",
        "series": f", one of a series (every {DAY_NAMES[o['series']]})" if o.get("series") else "",
        "concerns": concern_words(o["about"]), "windows": "\n".join(window_lines), "rides": "\n".join(ride_lines),
        "first_window": str(FIRST_WINDOW_DAYS),
    })


def write_prep(root, key, tz, tz_name, day, brief_out, includes_out):
    """The prep's brief and includes, written; returns the ride lines."""
    import office_planner as op
    o = planned(root, key, tz)
    if o is None:
        raise MeetingError(f"the plan holds no meeting {key!r}")
    gathered, windows = gather_prep(root, o, tz)
    base_paths, always = op.every_sitting_carries(root, None)
    # The drafting table rides only where the office has one (office_bale
    # start adds it then); the planner's list names it either way.
    if not (pathlib.Path(root) / od.SPACE).is_dir():
        always = [(path, why) for path, why in always if path != f"{od.SPACE}/"]
        base_paths = [p for p in base_paths if p != od.SPACE]
    always = [(f"{SPACE}/", "the calendar: this meeting's line in the plan, and the record of the meetings before it")] \
        + always
    base_paths = [SPACE] + base_paths
    kept, left = op.fit(root, gathered, op.weight(root, base_paths))
    for e in left:
        log(f"left out of this prep for bale's caps: {e['path']} ({e['why']}); the oldest of what landed goes first")
    rides = always + [(e["path"], e["why"]) for e in kept]
    pathlib.Path(includes_out).write_text("".join(p + "\n" for p in [SPACE] + [e["path"] for e in kept]),
                                          encoding="utf-8")
    pathlib.Path(brief_out).write_text(render_brief(o, tz_name, day, rides, left, windows), encoding="utf-8")
    return o, rides


# --- what arose, and the meeting held ----------------------------------------------------

def parse_arising(text, names=()):
    """(sid, items, problems, blocks) from a text that holds an arising
    block: the last complete block counts (a sitting keeps it current, so
    a paste of the whole conversation holds it several times), its BEGIN
    line's session id, each item a dict heading, project (None for none),
    body; problems are the lines that do not read, each named. (None, [],
    [why], 0) when the text holds no block."""
    lines = odrop.normalize_text(text).split("\n")
    blocks, at = [], None
    for i, line in enumerate(lines):
        s = line.strip()
        m = ARISING_BEGIN_RE.match(s)
        if m:
            at = (i, m.group(1))
        elif s == ARISING_END and at is not None:
            blocks.append((at[0], i, at[1]))
            at = None
    if not blocks:
        return None, [], ["no arising block: a line --- ARISING BEGIN SID --- and a line --- ARISING END --- around "
                          "it"], 0
    first, last, sid = blocks[-1]
    items, problems, cur = [], [], None
    for n in range(first + 1, last):
        line = lines[n].rstrip()
        s = line.strip()
        if s.startswith("### "):
            cur = {"heading": " ".join(s[4:].split()), "project": None, "project_line": False, "body": [], "line": n + 1}
            items.append(cur)
            if not cur["heading"]:
                problems.append(f"line {n + 1}: an item's ### line has no words")
            continue
        if cur is None:
            if s:
                problems.append(f"line {n + 1} is outside any item (each starts with a ### line): {s!r}")
            continue
        if not cur["project_line"] and not cur["body"]:
            if not s:
                continue
            m = ARISING_PROJECT_RE.match(s)
            if not m:
                problems.append(f"line {n + 1}: the item {cur['heading']!r} has no `- project:` line after its ### line")
                cur["project_line"] = True
                cur["body"].append(line)
                continue
            p = " ".join(m.group(1).split())
            cur["project"] = None if p.lower() == NO_PROJECT else p
            cur["project_line"] = True
            continue
        cur["body"].append(line)
    for it in items:
        while it["body"] and not it["body"][0].strip():
            it["body"].pop(0)
        while it["body"] and not it["body"][-1].strip():
            it["body"].pop()
        it["body"] = "\n".join(l.strip() if not l.strip() else l for l in it["body"])
        del it["project_line"]
    return sid, items, problems, len(blocks)


def drop_text(item):
    return item["heading"] + (f"\n\n{item['body']}" if item["body"] else "")


def check_arising(text, sid, names=()):
    """(items, said): an arising text read for the prep sid, or MeetingError
    naming what does not read; said is what was taken that he should know."""
    got, items, problems, blocks = parse_arising(text, names)
    if got is None:
        raise MeetingError(problems[0])
    if got != sid:
        raise MeetingError(f"the arising block names {got}, and this sitting is {sid}: it is another sitting's")
    if problems:
        raise MeetingError("the arising block does not read: " + "; ".join(problems))
    said = []
    if blocks > 1:
        said.append(f"the text holds {blocks} arising blocks; the last, the sitting's latest, is taken")
    for it in items:
        if it["project"] and it["project"] != THE_OFFICE and it["project"] not in names:
            said.append(f"{it['heading']!r} names {it['project']!r}, none of this office's projects; kept as given, "
                        "for the sort")
    return items, said


def slug_of(words):
    s = re.sub(r"[^a-z0-9]+", "-", words.lower()).strip("-")
    if len(s) > 40:
        s = s[:41].rsplit("-", 1)[0][:40]
    return s or "arising"


def hold(root, sid, items, via, day, time):
    """The meeting whose prep is sid, recorded held, and each item written
    as a drop (odrop.write_drop: the in-tray arriving first when it must),
    tied to it. Returns (record, changed paths, drops written)."""
    root = pathlib.Path(root)
    r = prep_of(root, sid)
    if r is None:
        raise MeetingError(f"{sid} is no meeting's prep in {RECORD}")
    changed, pages = [], []
    for it in items:
        page, arrived, words = odrop.write_drop(root, drop_text(it), it["project"] or "", via, day, time,
                                                slug_of(it["heading"]))
        for w in words:
            log(w)
        changed += [p for p in arrived if p not in changed]
        changed.append(page)
        pages.append(page)
    r = dict(r, state="held", arose=r["arose"] + pages)
    write_record_line(root, r)
    changed.append(RECORD)
    return r, changed, pages


def tie(root, page, tz, now=None):
    """Tie a drop he made to the meeting whose prep is out and whose time is
    now (TIE_BEFORE ahead of it to TIE_AFTER after it starts): its record
    line's dropped list. Returns the record, or None when no meeting is
    on."""
    here = now_in(tz, now)
    best = None
    for r in read_record(root):
        if r["state"] != "prep out":
            continue
        start = start_of(r, tz)
        if start - TIE_BEFORE <= here <= start + TIE_AFTER:
            if best is None or abs(start - here) < abs(start_of(best, tz) - here):
                best = r
    if best is None:
        return None
    if page not in best["dropped"]:
        best = dict(best, dropped=best["dropped"] + [page])
        write_record_line(root, best)
    return best


# --- the command line --------------------------------------------------------------------

def now_from(a):
    if getattr(a, "now", None):
        stamp = a.now.replace("Z", "+00:00")
        when = dt.datetime.fromisoformat(stamp)
        return when if when.tzinfo else when.replace(tzinfo=dt.timezone.utc)
    return dt.datetime.now(dt.timezone.utc)


def read_text_file(path):
    return pathlib.Path(path).read_bytes().decode("utf-8", "surrogateescape")


def cmd_read(a):
    import office_planner as op
    text = odrop.normalize_text(read_text_file(a.text_file))
    if not text.strip():
        raise MeetingError("the words are empty")
    words = read_when(text, a.today, a.now)
    when = words
    if a.when:
        answer = read_when(a.when, a.today, a.now)
        if not answer["spans"]:
            raise MeetingError(f"--when {a.when!r} says no day and no time this office can read: YYYY-MM-DD HH:MM, "
                               "every DAY HH:MM, or words such as tomorrow at 2pm")
        when = merge(words, answer)
    c = canon(when)
    print(f"title\t{title_of(text, words['spans'])}")
    print(f"when\t{c or ''}")
    print(f"need\t{'' if c else ('time' if when['kind'] and not when['time'] else 'when')}")
    if c:
        print(f"words\t{when_words(c)}")
    for n in concerns_named(text, op.project_names(a.office)):
        print(f"concern\t{n}")
    for note in when["notes"]:
        print(f"note\t{note}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_meeting.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("read", help="what his words say: title, when, need, concern, note")
    p.add_argument("office"); p.add_argument("--text-file", required=True); p.add_argument("--today", required=True)
    p.add_argument("--now", required=True, help="the office's local time, HH:MM"); p.add_argument("--when")
    p = sub.add_parser("record", help="write the plan line")
    p.add_argument("office"); p.add_argument("--when", required=True); p.add_argument("--title", required=True)
    p.add_argument("--about", action="append", default=[])
    for name in ("near", "resolve"):
        p = sub.add_parser(name)
        p.add_argument("office"); p.add_argument("--tz", default=""); p.add_argument("--now")
        if name == "resolve":
            p.add_argument("--want", default="")
    p = sub.add_parser("gather", help="the prep's includes and brief; the ride lines")
    p.add_argument("office"); p.add_argument("--key", required=True); p.add_argument("--tz", default="")
    p.add_argument("--day", default=""); p.add_argument("--brief-out", required=True)
    p.add_argument("--includes-out", required=True)
    p = sub.add_parser("prep-out")
    p.add_argument("office"); p.add_argument("--key", required=True); p.add_argument("--sid", required=True)
    p.add_argument("--tz", default="")
    p = sub.add_parser("prep-of")
    p.add_argument("office"); p.add_argument("--sid", required=True)
    p = sub.add_parser("arising-check")
    p.add_argument("office"); p.add_argument("--sid", required=True); p.add_argument("--file", required=True)
    p = sub.add_parser("held")
    p.add_argument("office"); p.add_argument("--sid", required=True); p.add_argument("--file")
    p.add_argument("--via", required=True); p.add_argument("--day", required=True); p.add_argument("--time", required=True)
    p = sub.add_parser("tie")
    p.add_argument("office"); p.add_argument("--page", required=True); p.add_argument("--tz", default="")
    p.add_argument("--now")
    a = ap.parse_args(argv)
    try:
        root = pathlib.Path(a.office)
        if a.cmd == "read":
            return cmd_read(a)
        if a.cmd == "record":
            line, changed, words = record_meeting(root, a.when, a.title, a.about)
            for w in words:
                log(w)
            print(f"line\t{line}")
            for c in changed:
                print(c)
            return 0
        if a.cmd == "prep-of":
            r = prep_of(root, a.sid)
            if r is None:
                return 3
            print(f"{r['key']}\t{r['title']}\t{r['state']}")
            return 0
        if a.cmd == "arising-check":
            import office_planner as op
            items, said = check_arising(read_text_file(a.file), a.sid, op.project_names(root))
            for s in said:
                log(s)
            print(len(items))
            return 0
        if a.cmd == "held":
            import office_planner as op
            items = []
            if a.file:
                items, _ = check_arising(read_text_file(a.file), a.sid, op.project_names(root))
            r, changed, pages = hold(root, a.sid, items, a.via, a.day, a.time)
            print(f"said\t{held_words(r, pages)}")
            for c in changed:
                print(c)
            return 0
        tz = zone(a.tz)
        if a.cmd == "near":
            for o in near(root, tz, now_from(a)):
                print(f"{o['key']}\t{o['state']}\t{o['sid']}\t{occurrence_words(o)}")
            return 0
        if a.cmd == "resolve":
            o, choices = resolve(root, a.want, tz, now_from(a))
            if o:
                print(f"key\t{o['key']}\t{occurrence_words(o)}")
            for c in choices:
                print(f"choice\t{c['key']}\t{occurrence_words(c)}")
            return 0
        if a.cmd == "gather":
            o, rides = write_prep(root, a.key, tz, a.tz, a.day, a.brief_out, a.includes_out)
            print(f"meeting\t{o['title']}\t{concern_words(o['about'])}")
            for path, why in rides:
                print(f"{path}\t{why}")
            return 0
        if a.cmd == "prep-out":
            for c in mark_prep_out(root, a.key, a.sid, tz):
                print(c)
            return 0
        if a.cmd == "tie":
            r = tie(root, a.page, tz, now_from(a))
            if r is None:
                return 3
            print(f"{RECORD}\t{r['title']} ({r['date']} {r['time']})")
            return 0
    except oh.HelperError as exc:
        log(f"error: {exc}")
        return 1
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        log(f"error: {exc.__class__.__name__}: {exc}")
        return 2
    return 2


def held_words(r, pages):
    head = f"Recorded: {r['title']} ({when_words(r['date'] + ' ' + r['time'])}) happened"
    if not pages:
        return head + "; nothing arose to file."
    return head + f"; {len(pages)} item(s) that arose are drops in the in-tray, tied to it: " + ", ".join(pages) + "."


if __name__ == "__main__":
    sys.exit(main())
