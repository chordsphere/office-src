#!/usr/bin/env python3
"""Pull requests through gh (0.42.0): the office's one door to a git host's API.

Until 0.42.0 nothing in the office read a git host's API: every fact about
the audience came from git. This module is where gh, GitHub's own command
line, is run, and the only place: office deliver opens the review through
it when the occupant says so, reads the base of the pull request a
delivery is added to, and the walk-in, the home screen, office desk and
the digest read the state of the reviews on the branches the office
delivered. Three rules hold it:

- gh is optional everywhere. Not found (gh_program), not signed in to the
  audience's host, or the host not answering, a surface says so in one
  line where it would have read or opened something, and does what it did
  before 0.42.0.
- Nothing is opened, changed or closed on the audience without the one
  question (bin/office asks it; open_review runs only after a yes). Reading
  state asks nothing and changes nothing: gh pr list, read-only, one short
  timeout, never a prompt (GH_PROMPT_DISABLED, stdin closed).
- The office writes no token, login or host credential anywhere: gh's
  sign-in is the occupant's own, and the office never asks for it. What
  the office writes is the `review` History line a review it opened leaves
  on the folder (the branch, the number and the URL), and nothing of what
  it reads: review state is a rendering, recomputed on every run and
  cached nowhere (doctrine section 10).

Where gh is looked for is one door, gh_program: the directories
OFFICE_GH_PATH lists when it is set ("" lists none, so gh is not found),
the PATH when it is not. The suite's Env sets it to "" and a test that
wants gh names a directory holding the fake (tests/fakes/gh_fake.py), so
no test runs the machine's own gh.

The command line (bin/office calls it through pylib):

    office_review.py open OFFICE --review FILE --day DAY
        the review a delivery offered (FILE, run()'s review block as JSON)
        opened through gh, the `review` line written on the folder and
        committed; prints `opened the review: #N URL`; exit 1 with gh's
        words when gh refused, the delivery standing
    office_review.py shown-line --review FILE
        the gh line an offer will run, as deliver's question shows it
    office_review.py states OFFICE [--project NAME]
        each project's review lines, as the walk-in and the digest say them

Standard library only. Logs on stderr with an [office] prefix.
"""

import argparse
import datetime as dt
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402

GH = "gh"
GH_PATH_VAR = "OFFICE_GH_PATH"
# Reading state is one short call per project; opening a review waits
# longer, since the host makes the pull request while gh waits.
READ_TIMEOUT = 15
OPEN_TIMEOUT = 60
# A pull request the audience merged or closed is shown this many days
# after it happened for a folder already filed; one whose folder is on the
# desk is shown whatever its age, and an open one always.
RECENT_DAYS = 7
# The most review lines one project's line holds; the rest are counted.
SHOWN = 6
LIST_LIMIT = 200
FIELDS = "number,url,state,reviewDecision,headRefName,baseRefName,isDraft,closedAt,mergedAt"
# The `review` History line (0.42.0), as review_text writes it.
REVIEW_RE = oh.LazyPattern(r"^(?P<branch>\S+) on (?P<audience>\S+) of (?P<project>\S+): #(?P<number>\d+) "
                           r"(?P<url>\S+)$")
# A GitHub login: letters, digits and single hyphens, at most 39, an @ before it allowed.
LOGIN_RE = oh.LazyPattern(r"^@?([A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38})$")
PULL_URL_RE = oh.LazyPattern(r"^https?://([^/\s]+)/([^/\s]+(?:/[^/\s]+)*)/([^/\s]+)/pull/(\d+)/?$")


def debug(msg):
    if os.environ.get("OFFICE_DEBUG") == "1":
        print(f"[office] debug: {msg}", file=sys.stderr)


def log(msg):
    print(f"[office] {msg}", file=sys.stderr)


class GhError(Exception):
    """gh could not be run, or refused: its words, whole."""


# --- the door -------------------------------------------------------------------------------

def gh_program(environ=None):
    """The path of the gh this office runs, or None: the first executable
    file named gh in the directories OFFICE_GH_PATH lists when that is set
    ("" lists none), else in the PATH's. Never a shell lookup, so what the
    environment names is what runs."""
    env = os.environ if environ is None else environ
    dirs = env.get(GH_PATH_VAR)
    if dirs is None:
        dirs = env.get("PATH", "")
    for d in dirs.split(os.pathsep):
        if not d:
            continue
        cand = pathlib.Path(d) / GH
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand)
    return None


def gh_env(environ=None):
    """gh's environment: the caller's, with every prompt, spinner, colour
    and update notice off, so a read never waits on the occupant."""
    env = dict(os.environ if environ is None else environ)
    env.update({"GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1", "GH_SPINNER_DISABLED": "1",
                "NO_COLOR": "1", "CLICOLOR": "0"})
    return env


def run_gh(program, args, timeout=READ_TIMEOUT, environ=None):
    """gh ARGS, its stdin closed; the finished process. GhError when it
    could not run or did not finish in time."""
    import subprocess
    debug(f"gh {' '.join(args)}")
    try:
        return subprocess.run([program, *args], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                              timeout=timeout, env=gh_env(environ))
    except subprocess.TimeoutExpired:
        raise GhError(f"gh did not answer within {timeout}s (gh {args[0]} {args[1] if len(args) > 1 else ''})".rstrip())
    except OSError as exc:
        raise GhError(f"gh could not be run ({program}): {exc}")


def gh_words(proc):
    """What gh said when it refused, in one line: its stderr's non-blank
    lines (its stdout's when stderr is empty), joined; its exit code when
    it said nothing."""
    text = (proc.stderr or "").strip() or (proc.stdout or "").strip()
    words = "; ".join(l.strip() for l in text.splitlines() if l.strip())
    return words or f"gh exited {proc.returncode} and said nothing"


# --- the audience's host, read from its URL -------------------------------------------------

def is_github(host):
    """A GitHub host: github.com, or an enterprise instance named github.*
    (review_url's test, kept as it was)."""
    return "github" in (host or "").lower()


def repo_of(remote_url):
    """(host, HOST/OWNER/REPO as gh's --repo takes it) for a GitHub
    remote's URL; None for any other host, or a URL that does not read."""
    import office_deliver as odl
    parsed = odl.parse_remote_url(remote_url)
    if parsed is None or not is_github(parsed[0]):
        return None
    host, owner, repo = parsed
    return host, f"{host}/{owner}/{repo}"


def number_of(url):
    """A pull request's number from its URL (https://HOST/OWNER/REPO/pull/N), or None."""
    m = PULL_URL_RE.match((url or "").strip())
    return int(m.group(4)) if m else None


def repo_of_pull(url):
    """HOST/OWNER/REPO from a pull request's URL, or None."""
    m = PULL_URL_RE.match((url or "").strip())
    return f"{m.group(1)}/{m.group(2)}/{m.group(3)}" if m else None


def login_of(to):
    """The reviewer's login when delivery.md's to: line reads as one (a
    GitHub login, an @ before it allowed); None for a name, an address or
    several people, which are printed as before and never passed to gh."""
    m = LOGIN_RE.match((to or "").strip())
    return m.group(1) if m else None


def signed_in(program, host, environ=None):
    """(True, None) when gh is signed in to host; (False, gh's words)
    otherwise. gh auth status reads gh's own sign-in, and the office never
    reads or writes it."""
    proc = run_gh(program, ["auth", "status", "--hostname", host], environ=environ)
    if proc.returncode == 0:
        return True, None
    return False, gh_words(proc)


# --- opening the review (deliver, after the push) -------------------------------------------

def review_offer(remote_url, branch, base, title, body, to, environ=None):
    """What office deliver offers after the push for a branch with no review
    yet (0.42.0): {offer, why, ...}. offer is True when gh is here, the
    audience is a GitHub host and gh is signed in to it; the block then
    holds the review as it will be opened (title, body, base, head,
    reviewer, the gh line shown) for bin/office to show and ask. Otherwise
    why says in one line what kept it from being offered, and the review's
    words go to the clipboard instead."""
    out = {"offer": False, "why": None, "title": title, "body": body or "", "base": base, "head": branch,
           "reviewer": login_of(to), "to": to}
    got = repo_of(remote_url)
    if got is None:
        out["why"] = "the audience's git host is not a GitHub host, so gh opens nothing there"
        return out
    host, repo = got
    out.update(host=host, repo=repo)
    program = gh_program(environ)
    if program is None:
        out["why"] = "gh is not on this machine, so the review is not opened from here"
        return out
    try:
        ok, words = signed_in(program, host, environ)
    except GhError as exc:
        out["why"] = f"gh could not say whether it is signed in to {host}: {exc}"
        return out
    if not ok:
        out["why"] = f"gh is not signed in to {host} ({words}); the office never signs it in"
        return out
    out.update(offer=True, gh=program, argv=create_argv(repo, base, branch, title, out["reviewer"]))
    return out


def create_argv(repo, base, head, title, reviewer=None, body_file="BODY"):
    """gh pr create's arguments: the repo by host (--repo HOST/OWNER/REPO,
    so no GH_HOST and no checkout is needed), the base and head, the title,
    the body from a file (never a command-line argument), and the reviewer
    when the words name a login."""
    argv = ["pr", "create", "--repo", repo, "--base", base, "--head", head, "--title", title,
            "--body-file", body_file]
    if reviewer:
        argv += ["--reviewer", reviewer]
    return argv


def shown_line(argv):
    """The gh line as the question shows it: the body file named as what it holds."""
    import shlex
    words = ["gh", *argv]
    if "--body-file" in words:
        i = words.index("--body-file") + 1
        return " ".join(shlex.quote(w) for w in words[:i]) + " <the review's body> " + \
            " ".join(shlex.quote(w) for w in words[i + 1:])
    return " ".join(shlex.quote(w) for w in words)


def open_review(offer, environ=None):
    """Run gh pr create for an offer review_offer made; (number, url). The
    body goes through a temporary file, removed after. GhError with gh's
    words when gh refused (not signed in, no rights, a pull request already
    open on the branch) or could not say where the review is."""
    import tempfile
    program = gh_program(environ) or offer.get("gh")
    if not program:
        raise GhError("gh is not on this machine")
    with tempfile.TemporaryDirectory(prefix="office-review-") as tmp:
        body = pathlib.Path(tmp) / "body.md"
        body.write_text(offer.get("body") or "", encoding="utf-8")
        argv = create_argv(offer["repo"], offer["base"], offer["head"], offer["title"], offer.get("reviewer"),
                           str(body))
        proc = run_gh(program, argv, timeout=OPEN_TIMEOUT, environ=environ)
    if proc.returncode != 0:
        raise GhError(gh_words(proc))
    url = next((l.strip() for l in reversed((proc.stdout or "").splitlines()) if number_of(l.strip())), None)
    if url is None:
        raise GhError(f"gh made no URL of a pull request known ({gh_words(proc)})")
    return number_of(url), url


def review_text(branch, audience, project, number, url):
    """The `review` History line's text (0.42.0), as REVIEW_RE reads it."""
    return f"{branch} on {audience} of {project}: #{number} {url}"


def review_records(folder_md):
    """[(day, record)] for each `review` History line of a folder, oldest
    first: branch, audience, project, number (int) and url."""
    f = oh.parse_folder(pathlib.Path(folder_md).read_text(encoding="utf-8"))
    out = []
    for day, verb, text in f["history"]:
        if verb != "review":
            continue
        m = REVIEW_RE.match(text)
        if m:
            rec = m.groupdict()
            rec["number"] = int(rec["number"])
            out.append((day, rec))
    return out


def record_review(office_root, folder_rel, day, offer, number, url):
    """The `review` line on the folder, committed alone; the line said, or
    why it could not be written (the review stands either way)."""
    import office_bale as ob
    md = pathlib.Path(office_root) / folder_rel / "folder.md"
    text = review_text(offer["head"], offer["audience"], offer["project"], number, url)
    try:
        _, wrote = oh.folder_event(md, day, "review", text)
        if not wrote:
            return f"{folder_rel}/folder.md has no History section, so the review is not recorded there"
        ob.git(office_root, "add", "--", f"{folder_rel}/folder.md")
        ob.git(office_root, "commit", "-q", "-m", f"office deliver: review #{number} for {offer['head']}",
               "--", f"{folder_rel}/folder.md")
    except (OSError, oh.HelperError, ob.LandError) as exc:
        return f"{folder_rel}/folder.md: the review could not be recorded ({exc}); it is open on the audience"
    return f"{folder_rel}/folder.md: History: {day} review: {text}"


# --- reading review state ---------------------------------------------------------------------

def state_words(pr):
    """A pull request's state in the office's words: `#N approved`, `#N
    changes requested`, `#N review pending`, `#N merged` or `#N closed`."""
    n = pr.get("number")
    state = (pr.get("state") or "").upper()
    if state == "MERGED":
        return f"#{n} merged"
    if state == "CLOSED":
        return f"#{n} closed"
    decision = (pr.get("reviewDecision") or "").upper()
    if decision == "APPROVED":
        return f"#{n} approved"
    if decision == "CHANGES_REQUESTED":
        return f"#{n} changes requested"
    return f"#{n} review pending" + (" (a draft)" if pr.get("isDraft") else "")


def list_pulls(program, repo, head=None, state="all", environ=None):
    """The pull requests on repo (HOST/OWNER/REPO) as gh pr list --json
    gives them, every state unless state says one, those whose head is
    head when given. GhError with gh's words when it refused."""
    import json
    argv = ["pr", "list", "--repo", repo, "--state", state, "--limit", str(LIST_LIMIT), "--json", FIELDS]
    if head:
        argv += ["--head", head]
    proc = run_gh(program, argv, environ=environ)
    if proc.returncode != 0:
        raise GhError(gh_words(proc))
    try:
        got = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise GhError(f"gh's answer is not JSON: {exc}")
    if not isinstance(got, list):
        raise GhError("gh's answer is not a list of pull requests")
    return got


def open_pull_for(remote_url, branch, environ=None):
    """(the open pull request whose head is branch, as {number, url, base},
    or None; a line saying why it was not read, or None). For deliver's
    adopted and continued branches (0.42.0, item 3): the request's base is
    the delivery's from."""
    got = repo_of(remote_url)
    if got is None:
        return None, None
    host, repo = got
    program = gh_program(environ)
    if program is None:
        return None, "the pull request's base was not read: gh is not on this machine"
    try:
        pulls = [p for p in list_pulls(program, repo, head=branch, state="open", environ=environ)
                 if p.get("headRefName") == branch]
    except GhError as exc:
        return None, f"the pull request's base was not read from {host}: {exc}"
    if not pulls:
        return None, None
    p = max(pulls, key=lambda x: x.get("number") or 0)
    return {"number": p.get("number"), "url": p.get("url"), "base": p.get("baseRefName")}, None


def remote_url_of(entry):
    """The audience remote's URL for a project on this machine, read from
    its clone (git remote get-url, no network); None for a project on a
    host, which is not reached for a rendering."""
    import office_host as ohost
    if entry.get("host") or entry.get("problem") or not entry.get("audience"):
        return None
    path = entry.get("resolved")
    if not path or not pathlib.Path(path).is_dir():
        return None
    run = ohost.run_in(ohost.Place(str(path)), ["git", "remote", "get-url", entry["audience"]],
                       timeout=ohost.RUN_TIMEOUT)
    return run.stdout.strip() if run.returncode == 0 and run.stdout.strip() else None


def delivered_branches(folders, project, audience):
    """{branch: [folder dict, ...]} for every branch a folder of this office
    delivered to, or opened a review for, on the project's audience."""
    out = {}
    for f in folders:
        if f.get("problem"):
            continue
        try:
            recs = [r for _, r in oh.delivered_records(f["path"])] + [r for _, r in review_records(f["path"])]
        except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
            debug(f"{f['rel']}: its History could not be read for the reviews: {exc}")
            continue
        for rec in recs:
            if rec["project"] == project and rec["audience"] == audience:
                out.setdefault(rec["branch"], [])
                if f not in out[rec["branch"]]:
                    out[rec["branch"]].append(f)
    return out


def recent(pr, now, days=RECENT_DAYS):
    stamp = pr.get("mergedAt") or pr.get("closedAt")
    if not stamp:
        return False
    try:
        when = dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return False
    return (now - when) <= dt.timedelta(days=days)


def project_reviews(entry, folders, now=None, environ=None):
    """One project's reviews: {name, rows, problem}. rows, one per pull
    request on a branch the office delivered: {number, url, words, branch,
    state, decision, folders (rels), cites}; problem, one line, when the
    state was not read (gh absent, not signed in, the host not answering).
    None when the project has no audience or no branch the office
    delivered: nothing to read, and gh is not run."""
    if not entry.get("audience") or entry.get("problem"):
        return None
    branches = delivered_branches(folders, entry["name"], entry["audience"])
    if not branches:
        return None
    now = now or dt.datetime.now(dt.timezone.utc)
    out = {"name": entry["name"], "rows": [], "problem": None}
    url = remote_url_of(entry)
    repo = None
    if url:
        got = repo_of(url)
        if got is None:
            return None  # not a GitHub host: there is no review state gh can read
        repo = got[1]
    else:
        # A project on a host: the repository a recorded review names.
        for fs in branches.values():
            for f in fs:
                for _, rec in review_records(f["path"]):
                    if rec["project"] == entry["name"]:
                        repo = repo_of_pull(rec["url"]) or repo
        if repo is None:
            # Which host the audience is, and whether gh reaches it, is not
            # known here until a review is recorded: the clone is not read
            # through its shell for a rendering, so there is nothing to say.
            debug(f"{entry['name']}: its audience's repository is not known on this machine (its clone is on a "
                  "host, and no review recorded names it), so its review state is not read")
            return None
    program = gh_program(environ)
    if program is None:
        out["problem"] = "review state not read: gh is not on this machine"
        return out
    try:
        pulls = list_pulls(program, repo, environ=environ)
    except GhError as exc:
        out["problem"] = f"review state not read: {exc}"
        return out
    for p in sorted(pulls, key=lambda x: x.get("number") or 0):
        fs = branches.get(p.get("headRefName"))
        if not fs:
            continue
        state = (p.get("state") or "").upper()
        on_desk = any(f["space"] == "desk" for f in fs)
        if state != "OPEN" and not on_desk and not recent(p, now):
            continue
        out["rows"].append({"number": p.get("number"), "url": p.get("url"), "words": state_words(p),
                            "branch": p.get("headRefName"), "state": state,
                            "decision": (p.get("reviewDecision") or "").upper(),
                            "folders": [f["rel"] for f in fs], "cites": [oh.cite(f) for f in fs]})
    out["rows"].sort(key=lambda r: (r["state"] != "OPEN", r["number"] or 0))
    return out


def office_reviews(office_root, folders=None, projects=None, now=None, environ=None):
    """[project_reviews(...)] for each project this office scopes that has
    something to say, in the floor plan's order. A project the rendering
    cannot reach (paused, a problem) is left to the line that already says
    so; this never raises for one project."""
    import office_bale as ob
    folders = oh.read_folders(office_root) if folders is None else folders
    projects = ob.office_projects(office_root) if projects is None else projects
    out = []
    for p in projects or []:
        if p.get("paused"):
            continue
        try:
            got = project_reviews(p, folders, now, environ)
        except (OSError, oh.HelperError, GhError) as exc:
            got = {"name": p["name"], "rows": [], "problem": f"review state not read: {exc}"}
        if got is not None:
            out.append(got)
    return out


def project_words(got, cites=True):
    """One project's reviews in one line: `#12 approved (feature-x, folder
    7); #14 changes requested (fix-y, folder 9)`, or the line saying why
    the state was not read, or that no review is open."""
    if got["problem"]:
        return got["problem"]
    if not got["rows"]:
        return "no review open on a branch the office delivered"
    parts = []
    for r in got["rows"][:SHOWN]:
        where = r["branch"] + (f", {', '.join(r['cites'])}" if cites and r["cites"] else "")
        parts.append(f"{r['words']} ({where})")
    more = len(got["rows"]) - SHOWN
    return "; ".join(parts) + (f"; and {more} more" if more > 0 else "")


def review_lines(reviews):
    """The walk-in's and office desk's Reviews section (0.42.0): one line per
    project, and for a review that asked for changes, what answers it."""
    if not reviews:
        return []
    out = ["Reviews:"]
    for got in reviews:
        out.append(f"  {got['name']}: {project_words(got)}")
        for r in got["rows"]:
            if r["decision"] == "CHANGES_REQUESTED" and r["state"] == "OPEN":
                out.append(f"    #{r['number']} asked for changes: a session answers them on {r['branch']}, and "
                           f"office deliver {r['cites'][0] if r['cites'] else 'FOLDER'} --branch {r['branch']} "
                           "adds the answer to the review")
    return out


def by_folder(reviews):
    """{folder rel: [row, ...]}: the reviews each folder's branches carry."""
    out = {}
    for got in reviews or []:
        for r in got["rows"]:
            for rel in r["folders"]:
                out.setdefault(rel, []).append(r)
    return out


def folder_words(rows):
    """What a folder's desk line says of its reviews: `review #12 approved`."""
    return "; ".join(f"review {r['words']}" for r in rows)


def changes_requested(rows):
    """The first open review among rows that asked for changes, or None."""
    return next((r for r in rows if r["decision"] == "CHANGES_REQUESTED" and r["state"] == "OPEN"), None)


# --- the command line ----------------------------------------------------------------------

def main(argv=None):
    import json
    ap = argparse.ArgumentParser(prog="office_review.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("open", help="open the review a delivery offered, through gh, and record it on the folder")
    p.add_argument("office"); p.add_argument("--review", required=True); p.add_argument("--day", required=True)
    p = sub.add_parser("shown-line", help="the gh line an offer will run, as the question shows it")
    p.add_argument("--review", required=True)
    p = sub.add_parser("states", help="each project's review lines")
    p.add_argument("office"); p.add_argument("--project")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "open":
            offer = json.loads(pathlib.Path(a.review).read_text(encoding="utf-8"))
            try:
                number, url = open_review(offer)
            except GhError as exc:
                log(f"error: gh did not open the review: {exc}")
                log(f"the delivery stands: {offer['head']} is on the audience, and the review is opened by hand")
                return 1
            print(f"opened the review: #{number} {url}")
            log(record_review(a.office, offer["folder"], a.day, offer, number, url))
            return 0
        if a.cmd == "shown-line":
            offer = json.loads(pathlib.Path(a.review).read_text(encoding="utf-8"))
            print(shown_line(create_argv(offer["repo"], offer["base"], offer["head"], offer["title"],
                                         offer.get("reviewer"))))
            return 0
        if a.cmd == "states":
            for got in office_reviews(a.office):
                if a.project and got["name"] != a.project:
                    continue
                print(f"{got['name']}: {project_words(got)}")
            return 0
    except (OSError, ValueError, KeyError, oh.HelperError) as exc:
        log(f"error: {exc}")
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
