#!/usr/bin/env python3
"""The audience line's crossing: office deliver, from a folder's landed work to the audience's git host.

A project's workbench clone is where bale lands: its branch carries
bale's own commits, merges and tags, and a coworker should never review
it. The audience reads the project on its git host, named by the
project's `audience` declaration (the remote in the clone that points
there). office deliver carries a folder's landed work across that line
as curated commits:

- The delivery is built on the occupant's machine, where the audience
  answers with his credentials (the probe of 2026-10-08-audience-line-002
  found the work host's credential cache empty, so nothing reaches the
  audience from there without a prompt). For a project on this machine
  the clone itself is the repo it is built in; for a project on a host
  the landed commits come here as a thin git bundle (made in the clone
  there, carried through the project's shell) into a temporary bare
  repo, the mirror, removed when the delivery is done.
- The audience's `base` branch (and the delivery branch, when an earlier
  delivery made it) is fetched first, into refs the office owns
  (refs/office/audience/...), never over the clone's own remote-tracking
  refs. A branch the audience already has that this folder's records do
  not cover was made outside the office (a pull request opened by hand,
  say); it is adopted only when the occupant says so (0.34.0: `--adopt`,
  or yes to the question on a terminal), and the delivery is then added
  to it, so a review's answer lands on the review's own branch. Adopted
  once, the folder records it, and the next delivery continues on it as
  on any branch of its own. A branch another folder of this office
  delivered to is the office's, and a delivery continues on it with no
  --adopt; a squash that would carry work another folder delivered onto
  a branch of its own is refused, since that work would leave twice.
- The delivery branch is chosen by one rule, and the plan says which
  chose it (branch_why): --branch; else delivery.md's `branch:` line;
  else the clone's checked-out branch, when the audience has it and it
  is not the base (office start checks out the branch a brief names);
  else the folder's slug. A project's branch_prefix goes before the
  words' short name and the slug.
- In a temporary worktree at the audience's tip, the landed work is
  squashed on (git merge --squash), less what bale's own commits changed
  (0.36.0: the commits bale makes for itself, with no session's work in
  them, its housekeeping `bale: ignore .bale/` and its sweeps, are undone
  on the workbench's tip first, in temporary commits that never leave;
  take_out_own), bale's files are taken out of the index, the lines the
  squash adds (never the files it touches whole: a line already on the
  audience is not the delivery's, and is told, not refused) and the
  folder's delivery words go through the letterhead check (the
  office's letterhead: its forbidden list, and the dashes and the
  ellipsis it refuses by default, and, in the words alone, a cleanup's
  name; the lines of the repository's own
  pull-request template, as the audience holds it, are not held to the
  phrasing rule or the three characters; a bale path named in a line that
  leaves is one of bale's marks, 0.36.0), and the words become one commit
  (several when delivery.md marks them) authored and committed as the
  project's declared `author` (0.25.0: asked once on a terminal and
  kept when none is declared; the clone's own identity is never used).
- Before the question each commit is read back whole (its subject and
  body, author and committer, the files it touches) with the
  letterhead's verdict on it, so what is shown is what will be pushed.
- Those commits alone are pushed, as refs/heads/BRANCH, once each one's
  author and committer is checked against the declared author, with the
  branch named in OFFICE_DELIVERY so the push guard in a clone lets it
  through and nothing else. The workbench branch is never pushed.
- The folder gets a dated `delivered` History line naming the branch,
  the sessions covered, the workbench commit and the delivery commit,
  and deliver prints what the occupant does next: the review's URL when
  the git host's compare-URL shape is known, the branch's name otherwise,
  and whom the words name as reviewer.
- No delivery ends at a terminal (0.40.0): when bringing the audience into
  the workbench conflicts, the merge's materials are written into the
  folder and the merge session named (office start N --merge), and its
  landed resolution is made a merge commit (land_merge, or the next plan);
  a delivery onto a branch takes its range's net change (range_commit); a
  review merged as a squash is seen by content (held_by_content).

Two steps, so bin/office can ask once in between: plan() does everything
up to the question (fetch, carry, squash, check, commit) and writes a
plan; run() checks the commits' identity, pushes and records; abandon()
removes what plan() made. Standard library only; every git call shows
under OFFICE_DEBUG=1.

The rest of the audience line's office side lives here too (0.25.0):
the letterhead's arrival and its pages (letterhead_arrive), what office
status says of the letterhead and each audience clone's push guard
(status_lines), what office upgrade brings (upgrade_additive), and the
review office land makes of a landed session (land_review).
"""

import argparse
import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_host as ohost  # noqa: E402
import office_bale as ob  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
RULES = INSTALL / "share" / "letterhead.toml"
TEMPLATES = INSTALL / "templates"
LETTERHEAD = "letterhead"
FORBIDDEN_REL = "letterhead/forbidden.txt"
VOICE_REL = "letterhead/voice.md"
# The letterhead's pages and the install's templates they arrive from.
LETTERHEAD_PAGES = {"README.md": "letterhead-README.md", "voice.md": "letterhead-voice.md",
                    "forbidden.txt": "letterhead-forbidden.txt"}
# The voice page's empty place, as the template marks it: while it is
# there the page holds none of the occupant's words.
VOICE_EMPTY_MARK = "<!-- EMPTY:"
MANIFEST_REL = "floor-plan/manifest.toml"
BALE_TOML_REL = "bale.toml"
# The refs the office owns in a repo it delivers from, deleted when the
# delivery is done or abandoned.
REF_BASE = "refs/office/audience/base"
REF_BRANCH = "refs/office/audience/branch"
REF_WORKBENCH = "refs/office/workbench"
REF_DELIVERY = "refs/office/delivery"
# 0.40.0: another folder's delivery commit, fetched by its branch for the
# content test when the repo the delivery is built in does not hold it.
REF_HELD = "refs/office/audience/held"
OFFICE_REFS = (REF_BASE, REF_BRANCH, REF_WORKBENCH, REF_DELIVERY, REF_HELD)
# What never travels to an audience: the names bale makes in a working
# copy, taken out of the delivery's index whatever the clone tracks.
NEVER_DELIVERED = tuple(x.rstrip("/") for x in ohost.EXCLUDE_LINES)
STAT_LINES = 40
log = ob.log
debug = ob.debug


class DeliverError(ob.StartError):
    """office deliver cannot go on, said as lines a person can act on."""


class NeedsRefresh(DeliverError):
    """The clone's view of the audience's base is behind (0.39.0): on a
    terminal bin/office asks once whether to refresh it, and plans again
    with the answer (--refresh or --no-refresh)."""

    def __init__(self, lines, project):
        super().__init__(lines)
        self.project = project


class NeedsAuthor(DeliverError):
    """The project declares no author: a fact only the occupant knows,
    asked once on a terminal (bin/office) and kept; refused piped."""

    def __init__(self, lines, project, clone_identity):
        super().__init__(lines)
        self.project = project
        self.clone_identity = clone_identity


# --- the office's letterhead -----------------------------------------------------------------

def office_rules(office_root):
    """The letterhead check's rules as this office makes them: the
    install's list, and, when the office has a letterhead, its forbidden
    list and the characters it refuses by default, less what it lifts."""
    import office_letterhead as olh
    rules = olh.load_rules_toml(RULES)
    return olh.apply_letterhead(rules, pathlib.Path(office_root) / LETTERHEAD, LETTERHEAD)


def letterhead_arrive(root):
    """Make the letterhead arrive, or finish arriving: its front page, its
    voice page and its forbidden list from the install's templates, each
    only when missing (a page there is never rewritten), the floor plan's
    entry as the catalog declares it, and bale.toml's trigger. Returns
    (changed paths, words)."""
    import office_drafting as od  # here, not at the top: the drafting table's module is large
    root = pathlib.Path(root)
    entry = od.catalog_entry(space=LETTERHEAD)
    changed, words = [], []
    arrived = not (root / LETTERHEAD).is_dir()
    (root / LETTERHEAD).mkdir(exist_ok=True)
    for page, template in LETTERHEAD_PAGES.items():
        path = root / LETTERHEAD / page
        if path.exists():
            continue
        path.write_text((TEMPLATES / template).read_text(encoding="utf-8"), encoding="utf-8")
        changed.append(f"{LETTERHEAD}/{page}")
        words.append(f"made {LETTERHEAD}/{page} from the install's template" + (
            ", its place for the occupant's words empty and marked" if page == "voice.md" else ""))
    if od.add_space_to_floor_plan(root / MANIFEST_REL, entry, LETTERHEAD):
        changed.append(MANIFEST_REL)
        words.append(f"the floor plan now lists the {LETTERHEAD} space, as the install's catalog declares it")
    added = od.add_include_trigger(root / BALE_TOML_REL, entry["path"])
    if added:
        changed.append(BALE_TOML_REL)
        words.append(f"bale.toml's include group now triggers on {entry['path']}")
    if arrived and changed:
        words.insert(0, f"the letterhead arrives in this office: {LETTERHEAD}/ (it refuses the em dash, the en dash "
                        "and the ellipsis by default; its voice page waits for the occupant's words)")
    return changed, words


def audience_projects(office_root):
    """The office's projects that declare an audience and read."""
    return [p for p in ob.office_projects(office_root) or [] if p.get("audience") and not p["problem"]]


def voice_state(root):
    """(state, line) for the voice page: absent, empty (the template's
    marked place still there) or written."""
    path = pathlib.Path(root) / VOICE_REL
    if not path.is_file():
        return "absent", f"{VOICE_REL} is missing: office upgrade adds it from the install's template"
    if VOICE_EMPTY_MARK in path.read_text(encoding="utf-8", errors="replace"):
        return "empty", f"{VOICE_REL} holds no words of the occupant's yet (its place is marked empty)"
    return "written", f"{VOICE_REL} holds the occupant's words"


def guard_line(project, place, facts):
    """(state, line) for one audience clone's push guard, with the line
    that replaces an older one or installs a missing one."""
    state, what = ohost.guard_state(facts)
    name = project["name"]
    if facts.get("guard") == "office" and facts.get("guard_audience") not in (None, project["audience"]):
        return "older", (f"{name}: the push guard in {place} names the audience {facts['guard_audience']}, not "
                         f"{project['audience']}: office projects set {name} replaces it")
    if state == "current":
        return state, f"{name}: {what} in {place}"
    if state == "older":
        return state, f"{name}: {what} in {place}: office upgrade, or office projects set {name}, replaces it"
    if state == "none":
        return state, (f"{name}: {what} in {place}, so a push to {project['audience']} by hand is not refused: "
                       f"office upgrade, or office projects set {name}, installs it")
    return state, f"{name}: {what} ({place})"


def status_lines(office_root):
    """office status's letterhead and push-guard lines, read-only. A
    clone that cannot be read (a host that does not answer) is a line."""
    import office_letterhead as olh
    root = pathlib.Path(office_root)
    lines = []
    audience = audience_projects(root)
    if (root / LETTERHEAD).is_dir():
        _, voice = voice_state(root)
        lifted = []
        try:
            lifted = office_rules(root)["lifted"]
        except olh.CheckError as exc:
            lines.append(f"letterhead: PROBLEM: {exc}")
        lines.append("letterhead: refuses the em dash, the en dash and the ellipsis by default"
                     + (f", lifting {', '.join(n for n, _ in lifted)}" if lifted else "") + f"; {voice}")
    elif audience:
        lines.append(f"letterhead: none, and {', '.join(p['name'] for p in audience)} "
                     f"{'has an audience' if len(audience) == 1 else 'have audiences'}: office upgrade brings it "
                     "(its voice page and forbidden list from the install's templates)")
    else:
        lines.append("letterhead: none; it arrives with the first project given an audience")
    for p in audience:
        place = ohost.place_of(p)
        try:
            facts = ohost.git_facts(place)
        except ohost.HostError as exc:
            lines.append(f"guard:      {p['name']}: the clone could not be read: {exc}")
            continue
        lines.append(f"guard:      {guard_line(p, place, facts)[1]}")
    return lines


def refresh_guard(project, place=None, facts=None):
    """Install the push guard where it is missing or older (never over a
    hook the office did not write). Returns (changed, line)."""
    place = place or ohost.place_of(project)
    try:
        facts = facts or ohost.git_facts(place)
        state, line = guard_line(project, place, facts)
        if state == "current":
            return False, line
        if state in ("other", "unread"):
            return False, line
        url = facts["remotes"].get(project["audience"])
        if not url:
            return False, (f"{project['name']}: the clone at {place} has no remote named {project['audience']}, so "
                           f"no guard was written: office projects set {project['name']} --audience REMOTE")
        return True, ohost.install_push_guard(place, project["audience"], url)
    except ohost.HostError as exc:
        return False, f"{project['name']}: the push guard was not refreshed: {exc}"


def upgrade_additive(office_root):
    """What office upgrade brings that needs no migration (0.25.0): the
    letterhead, in an office with a project given an audience and none
    yet; the voice page (and the forbidden list's template) in a
    letterhead from an earlier release; the push guard in every audience
    clone that has none or an older one. Returns (changed office paths,
    lines). Nothing of the occupant's is rewritten."""
    root = pathlib.Path(office_root)
    changed, lines = [], []
    if (root / LETTERHEAD).is_dir() or audience_projects(root):
        c, w = letterhead_arrive(root)
        changed += c
        lines += w
    for p in audience_projects(root):
        done, line = refresh_guard(p)
        if done:
            lines.append(line)
    return changed, lines


def declare_author(office_root, project, author):
    """Declare a project's author and commit the floor plan alone, as
    office projects set --author does. Returns the line to say."""
    root = pathlib.Path(office_root)
    author = oh.check_author(author)
    before = next((p for p in ob.office_projects(root) or [] if p["name"] == project), None)
    if before is None:
        raise DeliverError([f"no project named {project} in this office's [projects]"])
    if before.get("author") == author:
        return f"{project}'s author is {author}, as declared"
    oh.set_declarations(root / MANIFEST_REL, project, audience_keys={"author": author})
    ob.git(root, "add", "--", MANIFEST_REL)
    ob.git(root, "commit", "-q", "-m", f"office deliver: {project}'s author", "--", MANIFEST_REL)
    if before.get("author"):
        return f"{project}'s author is now {author} (it was {before['author']}), kept in the floor plan"
    return f"{project}'s author is {author}, kept in the floor plan: deliveries are authored and committed as it"


def g(repo, *args, check=True, timeout=ohost.RUN_TIMEOUT, env=None):
    """git in a repo on this machine, through office_host so every call
    shows under OFFICE_DEBUG=1; a failure is a DeliverError naming it."""
    run = ohost.run_in(ohost.Place(str(repo)), ["git", *args], timeout=timeout, env=env)
    if check and run.returncode != 0:
        raise DeliverError([f"git {' '.join(args)} in {repo} failed: {ohost._last_words(run.stderr)}"])
    return run


# --- the audience's git host ---------------------------------------------------------------

def parse_remote_url(url):
    """(host, owner, repo) from a remote's URL (https://HOST/OWNER/REPO.git,
    git@HOST:OWNER/REPO.git, ssh://git@HOST/OWNER/REPO), or None."""
    url = (url or "").strip()
    m = re.match(r"^(?:https?|ssh|git)://(?:[^@/]+@)?([^/:]+)(?::\d+)?/(.+?)(?:\.git)?/?$", url)
    if not m:
        m = re.match(r"^(?:[^@]+@)?([^:/]+):(.+?)(?:\.git)?/?$", url)
    if not m:
        return None
    host, path = m.group(1), m.group(2)
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2:
        return None
    return host, "/".join(parts[:-1]), parts[-1]


def review_url(url, branch, base, title=None, body=None):
    """The URL that opens the review on the audience's git host, when the
    host's shape is known (a GitHub host, github.com or an enterprise
    instance named github.*, or a GitLab host): the compare page with the
    branch, and the review's title and body as the page takes them. None
    when the shape is not known."""
    import urllib.parse
    parsed = parse_remote_url(url)
    if parsed is None:
        return None
    host, owner, repo = parsed
    low = host.lower()
    if "github" in low:
        query = {"expand": "1"}
        if title:
            query["title"] = title
        if body:
            query["body"] = body
        return f"https://{host}/{owner}/{repo}/compare/{base}...{branch}?" + urllib.parse.urlencode(query)
    if "gitlab" in low:
        query = {"merge_request[source_branch]": branch, "merge_request[target_branch]": base}
        if title:
            query["merge_request[title]"] = title
        if body:
            query["merge_request[description]"] = body
        return f"https://{host}/{owner}/{repo}/-/merge_requests/new?" + urllib.parse.urlencode(query)
    return None


def branch_url(url, branch):
    """The URL that lists the reviews open for a branch on the audience's
    git host (0.34.0), for a delivery added to a branch made outside the
    office, whose review is already open: GitHub's pull requests with
    that head, GitLab's merge requests with that source branch. None when
    the host's shape is not known."""
    import urllib.parse
    parsed = parse_remote_url(url)
    if parsed is None:
        return None
    host, owner, repo = parsed
    low = host.lower()
    if "github" in low:
        return f"https://{host}/{owner}/{repo}/pulls?" + urllib.parse.urlencode({"q": f"is:pr head:{branch}"})
    if "gitlab" in low:
        return f"https://{host}/{owner}/{repo}/-/merge_requests?" + urllib.parse.urlencode(
            {"scope": "all", "source_branch": branch})
    return None


def branch_from_folder(folder_name):
    """The delivery branch's default name: the folder's slug, its date
    stripped (2026-10-08-audience-line -> audience-line)."""
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", folder_name)
    return oh.check_base(slug)


# --- the plan --------------------------------------------------------------------------------

def find_folder(office_root, folder):
    """(space/name, folder.md path) for a folder on the desk or in the
    filing cabinet, by its directory name."""
    root = pathlib.Path(office_root)
    for space in ("desk", "filing-cabinet"):
        md = root / space / folder / "folder.md"
        if md.is_file():
            return f"{space}/{folder}", md
    raise DeliverError([f"no folder named {folder} on the desk or in the filing cabinet"])


def sids_in_subjects(consumption, subjects):
    """The session ids bale's commit subjects name, in order of first
    appearance, with the kinds seen for each."""
    out = {}
    for subject in subjects:
        found = consumption.subject_sid(subject)
        if found:
            kind, sid = found
            out.setdefault(sid, set()).add(kind)
    return out


def own_commits(consumption, repo, range_spec):
    """[(sha, subject)] for the commits of bale's own in a range (0.36.0),
    newest first, as the consumption manifest names them
    (Consumption.own_commit): what they changed never leaves in a
    delivery. A merge is never one; a session's work commit is the work."""
    out = g(repo, "log", "--format=%H%x00%s", "--no-merges", range_spec).stdout
    found = []
    for line in out.splitlines():
        sha, _, subject = line.partition("\0")
        if sha and consumption.own_commit(subject):
            found.append((sha, subject))
    return found


def identity_of(author):
    """(git -c flags, environment) that make a commit carry the author as
    both author and committer, over any GIT_AUTHOR_* in the environment:
    the audience sees the author, and nobody else."""
    name, email = oh.split_author(author)
    cfg = ["-c", f"user.name={name}", "-c", f"user.email={email}"]
    env = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
           "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email}
    return cfg, env


def lines_added_only(worktree, sha, path):
    """(the lines a commit added to a path, whether it created the path)
    when adding lines is all the commit did there, nothing removed or
    changed; None when it did more, or when nothing it did there reads as
    lines (a binary file). What a pure addition left in a file can be
    taken out line by line, wherever later work moved it."""
    diff = g(worktree, "show", "--format=", "--no-color", "-U0", sha, "--", path).stdout
    added, created, in_hunk = [], False, False
    for line in diff.splitlines():
        if line.startswith("@@"):
            in_hunk = True
            continue
        if not in_hunk or line.startswith("\\"):
            # The file header (and the no-newline marker): "+++ " there is
            # a header line, inside a hunk an added line is content.
            created = created or line.startswith("new file")
            continue
        if line.startswith("+"):
            added.append(line[1:])
        elif line.startswith("-"):
            return None
    return (added, created) if added else None


def take_out_own(worktree, own, author):
    """In a worktree at the workbench's tip, undo what each of bale's own
    commits changed (0.36.0): git revert, newest first, each in a
    temporary commit of its own that never leaves (so the next is undone
    on the result of the one before), and the squash is made from the
    result. A line bale added that later work already took out is simply
    gone (the revert's three-way merge sees both sides agree). Where
    later work on the workbench touches the same lines, the revert
    conflicts; when all bale's commit did to that file was add lines,
    those lines are taken out of the workbench's version one by one
    (lines_added_only), and the file is deleted when nothing is left of
    one bale created; anything else refuses by name, since what bale's
    own commits changed must stay out and the office does not guess
    around a conflict. Returns (the cleaned tip's sha, what was taken
    out: one dict per commit with its sha, subject, files and how)."""
    cfg, env = identity_of(author)
    taken = []
    for sha, subject in own:
        files = g(worktree, "diff-tree", "--root", "-r", "--no-commit-id", "--name-only", sha).stdout.split()
        how = "undone"
        reverted = g(worktree, "revert", "--no-commit", sha, check=False, env=env)
        if reverted.returncode != 0:
            conflicted = g(worktree, "diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
            if not conflicted:
                g(worktree, "revert", "--abort", check=False)
                raise DeliverError([f"what bale's own commit {sha[:12]} ({subject}) changed could not be undone for the "
                                    f"delivery: git revert exit {reverted.returncode}: {ohost._last_words(reverted.stderr)}",
                                    "nothing was pushed, and the delivery was not made"])
            by_line = []
            for path in conflicted:
                pure = lines_added_only(worktree, sha, path)
                if pure is None:
                    g(worktree, "revert", "--abort", check=False)
                    raise DeliverError([f"what bale's own commit {sha[:12]} ({subject}) changed in {path} cannot be taken "
                                        "out of the delivery: the workbench branch's later work touches the same lines, "
                                        "and that commit did more there than add lines, so the office will not guess "
                                        "which lines are bale's",
                                        f"undo its change to {path} by hand on the workbench branch (a commit of your "
                                        "own, which the next delivery reads as the work's), and deliver again; nothing "
                                        "was pushed"])
                added, created = pure
                current = g(worktree, "show", f"HEAD:{path}").stdout
                kept = current.splitlines()
                for line in added:
                    if line in kept:
                        del kept[len(kept) - 1 - kept[::-1].index(line)]
                if not kept and created:
                    g(worktree, "rm", "-q", "-f", "--", path)
                else:
                    text = "\n".join(kept) + ("\n" if kept and current.endswith("\n") else "")
                    (pathlib.Path(worktree) / path).write_text(text, encoding="utf-8")
                    g(worktree, "add", "--", path)
                by_line.append(path)
            g(worktree, "revert", "--quit", check=False)
            how = (f"its lines taken out of {', '.join(by_line)} one by one, since later work on the workbench "
                   "touches the same place")
        if g(worktree, "diff", "--cached", "--quiet", "HEAD", check=False).returncode == 0:
            how = "nothing left to undo: later work on the workbench had already taken it out"
        else:
            g(worktree, *cfg, "commit", "-q", "-m", f"office deliver: what {sha[:12]} changed, taken out", env=env)
        taken.append({"sha": sha, "subject": subject, "files": files, "how": how})
        debug(f"bale's own commit {sha[:12]} ({subject}): {how}")
    return g(worktree, "rev-parse", "HEAD").stdout.strip(), taken


def unmerged(worktree):
    """The paths git left unmerged in a worktree, in its order."""
    return [p for p in g(worktree, "diff", "--name-only", "--diff-filter=U", check=False).stdout.splitlines() if p]


def range_commit(worktree, since, squashed, author):
    """(parent, top): two temporary commits that never leave (0.40.0), whose
    one difference is a range's net change: the parent's tree is since's,
    the top's the cleaned tip's (squashed), bale's paths taken out of both
    (NEVER_DELIVERED), each tree written through an index of its own so the
    worktree's is never touched. Cherry-picked onto a branch's tip, the top
    carries what the range changed and nothing the branch already has."""
    import tempfile
    _, identity = identity_of(author)
    trees = []
    with tempfile.TemporaryDirectory(prefix="office-deliver-index-") as tmp:
        for n, rev in enumerate((since, squashed)):
            index = {"GIT_INDEX_FILE": str(pathlib.Path(tmp) / f"index-{n}")}
            g(worktree, "read-tree", rev, env=index)
            # -f: this index matches neither the worktree's HEAD nor its disk.
            g(worktree, "rm", "-r", "-q", "-f", "--cached", "--ignore-unmatch", "--", *NEVER_DELIVERED, env=index)
            trees.append(g(worktree, "write-tree", env=index).stdout.strip())
    parent = g(worktree, "commit-tree", trees[0], "-m", "office deliver: where the range starts",
               env=identity).stdout.strip()
    top = g(worktree, "commit-tree", trees[1], "-p", parent, "-m", "office deliver: the range, squashed",
            env=identity).stdout.strip()
    debug(f"the range {since[:12]}..{squashed[:12] if len(squashed) == 40 else squashed} as one temporary commit "
          f"{top[:12]} on {parent[:12]}")
    return parent, top


def own_lines(taken):
    """What the plan says of each commit of bale's own it took out, one
    line each: its sha, subject and files, and how when the plain revert
    was not the whole of it."""
    return [f"{t['sha'][:12]} {t['subject']} ({', '.join(t['files']) or 'no file'})"
            + ("" if t["how"] == "undone" else f": {t['how']}") for t in taken]


def mirror_here(prefix="office-deliver-"):
    """A temporary bare repo on this machine, the mirror a hosted
    project's delivery is built in."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix=prefix)
    repo = pathlib.Path(tmp) / "mirror.git"
    g(tmp, "init", "-q", "--bare", str(repo))
    return tmp, repo


def delivery_words(delivery_md, label=None):
    """((label, text), unread): a folder's delivery.md as the letterhead
    reads it, at deliver and at land's review alike (0.35.0): the lines
    whose words leave, each at its own line of the page, and the count of
    the page's other non-blank lines, which stay in the office
    (office_helper.delivery_leaving_text says which). label defaults to
    the page's path, so a hit is named as it always was."""
    path = pathlib.Path(delivery_md)
    text, unread = oh.delivery_leaving_text(path.read_text(encoding="utf-8", errors="replace"))
    return (label or str(path), text), unread


def named_branch(given, words_branch, project, prefix):
    """(branch, why, rule) for a delivery branch the occupant or the words
    name, the first two of the branch rule (the gaps of 2026-10-28, A3):
    --branch NAME as given; else delivery.md's `branch:` line, the
    project's branch_prefix before it unless the name holds a slash.
    (None, None, None) when neither names one: the clone's branch or the
    folder's slug decides, once the audience can be asked (plan step 4)."""
    if given:
        return oh.check_base(given), "--branch names it", "flag"
    if words_branch:
        name, put = oh.prefixed_branch(words_branch, prefix)
        why = f"delivery.md's branch line names {words_branch}"
        if put:
            why += f", behind {project}'s branch prefix {prefix}"
        elif prefix:
            why += f" (it holds a slash, so {project}'s branch prefix {prefix} is not put before it)"
        return name, why, "words"
    return None, None, None


def slug_branch(folder, project, prefix, clone_said=None):
    """(branch, why) for the last of the branch rule: the folder's slug,
    the project's branch_prefix before it; clone_said says why the clone's
    checked-out branch was not the one."""
    slug = branch_from_folder(folder)
    name, put = oh.prefixed_branch(slug, prefix)
    why = "the folder's slug" + (f", behind {project}'s branch prefix {prefix}" if put else "")
    return name, why + (f" ({clone_said})" if clone_said else "")


# A folder's slug that ends in a three-digit counter (fix-login-002) reads
# as a session id's tail, the slug and NNN bale mints, once it leaves as a
# branch name with the date the slug lost before it (0.42.0).
SLUG_COUNTER_RE = oh.LazyPattern(r"-[0-9]{3}$")


def branch_marks(name, rules, rule):
    """What the letterhead would refuse in a delivery branch's name, one
    line each (0.42.0): the name read as the words are read (the office's
    forbidden strings, names, phrasing, bale's marks and the cleanup list),
    and, for a name the folder's slug chose (rule "slug"), a slug ending in
    three digits, which reads as a session id. [] when the name may leave.
    A name the occupant gave (--branch, the words' branch line) or the
    clone's checked-out branch is held to the letterhead alone: an issue's
    number at its end is his to name."""
    import office_letterhead as olh
    out = []
    for _, _, kind, what, _ in olh.hits_in_text(name, olh.compile_rules(rules, words=True), "branch"):
        out.append(f"{kind}: {what}")
    if rule == "slug" and SLUG_COUNTER_RE.search(name):
        out.append("marks: it ends in three digits, as a session id does (YYYY-MM-DD-slug-NNN)")
    return out


def check_branch_name(name, rules, rule, why):
    """Refuse a delivery branch whose name the letterhead would refuse
    anywhere else (branch_marks), before anything is fetched or made for it;
    the remedy is --branch NAME."""
    found = branch_marks(name, rules, rule)
    if found:
        # The flag's and the words' name is checked before any fetch; the
        # clone's and the slug's once the audience has said whether it has
        # the clone's branch, with nothing made in the clone or pushed.
        done = "nothing was fetched or made" if rule in ("flag", "words") else "nothing was made or pushed"
        raise DeliverError([f"the delivery branch would be {name} ({why}), and the letterhead refuses its name: "
                            + "; ".join(found) + f"; {done}",
                            "name another: --branch NAME (or a `- branch: NAME` line in delivery.md)"])


def other_deliveries(office_root, rel, project, audience):
    """[(folder, day, record)] for every `delivered` History line another
    folder of this office keeps for this project and audience, on the desk
    and in the filing cabinet, oldest first by day (oh.delivered_records
    per folder page). A page that cannot be read is said, never skipped
    silently: a delivery it records is not known to this plan."""
    root = pathlib.Path(office_root)
    out = []
    for space in ("desk", "filing-cabinet"):
        for md in sorted((root / space).glob("*/folder.md")):
            where = f"{space}/{md.parent.name}"
            if where == rel:
                continue
            try:
                records = oh.delivered_records(md)
            except (OSError, UnicodeDecodeError, oh.HelperError) as exc:
                log(f"warning: {where}/folder.md cannot be read, so what it delivered is not known to this "
                    f"delivery: {exc}")
                continue
            out += [(where, day, rec) for day, rec in records
                    if rec["project"] == project and rec["audience"] == audience]
    return sorted(out, key=lambda x: x[1])


def commit_known(repo, sha):
    """Whether a commit (an abbreviated sha from a History line) is in the
    repo the delivery is built in."""
    return g(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode == 0


def is_ancestor(repo, sha, of):
    return commit_known(repo, sha) and g(repo, "merge-base", "--is-ancestor", sha, of, check=False).returncode == 0


def held_by_content(repo, rec, where):
    """(held, why not) for the content test (0.40.0): the delivery commit's
    change squashed onto the audience's base as fetched, in a temporary
    worktree, stages nothing: a review merged as a squash put that change on
    the base. A squash that conflicts or stages anything is not held (a base
    holding a later version of the same lines is not held, rightly: the work
    left twice would conflict). The delivery commit is read where the
    delivery is built, or fetched by its branch from the audience when it is
    not there; when it is nowhere the office can read, the test cannot run,
    and why is said."""
    import shutil
    import tempfile
    sha = rec["delivery"]
    if not commit_known(repo, sha):
        g(repo, "fetch", "-q", where, f"+refs/heads/{rec['branch']}:{REF_HELD}", check=False,
          timeout=ohost.TRANSFER_TIMEOUT)
        if not commit_known(repo, sha):
            return False, (f"its delivery commit {sha[:7]} is not where the delivery is built and {rec['branch']} on the "
                           "audience does not hold it, so its content could not be read")
    tmp = tempfile.mkdtemp(prefix="office-deliver-held-")
    wt = pathlib.Path(tmp) / "held"
    try:
        g(repo, "worktree", "add", "-q", "--detach", str(wt), REF_BASE)
        squashed = g(wt, "merge", "--squash", "--no-commit", sha, check=False, timeout=ohost.TRANSFER_TIMEOUT)
        if squashed.returncode != 0:
            return False, "its change conflicts with the base's"
        if g(wt, "diff", "--cached", "--quiet", check=False).returncode != 0:
            return False, None
        return True, None
    finally:
        g(repo, "worktree", "remove", "--force", str(wt), check=False)
        shutil.rmtree(tmp, ignore_errors=True)
        g(repo, "worktree", "prune", check=False)


def base_holds(repo, rec, where=None):
    """(how, why not): whether the audience's base, as fetched, already
    holds a delivery a record names. By history first, the fast path: its
    workbench commit or its delivery commit is on the base (a review merged
    as a merge commit or a fast-forward). Else by content (0.40.0, a review
    merged as a squash): held_by_content. how is "by history", "by content"
    or None; why says what kept the content test from running, if it could
    not."""
    if any(is_ancestor(repo, rec[k], REF_BASE) for k in ("workbench", "delivery")):
        return "by history", None
    if where is None:
        return None, None
    held, why = held_by_content(repo, rec, where)
    return ("by content", None) if held else (None, why)


def folder_label(office_root, rel):
    """A folder as the occupant cites it: folder N when it has a number,
    else space/name."""
    try:
        fields = oh.parse_folder((pathlib.Path(office_root) / rel / "folder.md").read_text(encoding="utf-8"))["fields"]
        number, _ = oh.folder_number(fields)
    except (OSError, UnicodeDecodeError, oh.HelperError):
        number = None
    return f"folder {number}" if number else rel


def twice_lines(folder, base, branch, continuing, since_why, twice, gone, labels=None):
    """The refusal of a squash that would carry work another folder
    already delivered (the gaps of 2026-10-28, A4): the sessions by name,
    the folder and branch that delivered them, which test the base failed
    (0.40.0: by history or by content, and why the content could not be
    read when it could not), and the remedy, continuing on that branch (or
    why it cannot be, when the audience no longer has it)."""
    labels = labels or {}
    onto = f"this delivery onto {branch}" if continuing else f"a new branch from {base}"
    named = "; ".join(f"{', '.join(carried)} ({where} delivered {'it' if len(carried) == 1 else 'them'} to "
                      f"{rec['branch']} on {day})" for where, day, rec, carried, _ in twice)
    lines = [f"the landed work since {since_why} carries work another folder of this office already delivered, which "
             f"is on the audience under its own review, so {onto} would deliver it twice: {named}"]
    for where, _, rec, _, why in twice:
        lines.append(f"{base} as fetched does not hold {labels.get(where, where)}'s delivery {rec['delivery'][:7]} by "
                     "history or by content" + (f" ({why})" if why else ""))
    for b in dict.fromkeys(t[2]["branch"] for t in twice):
        if b in gone:
            lines.append(f"{b} is no longer on the audience (merged and deleted, it may be), and {base} does not hold "
                         "its work as it was delivered (a review merged with changes to the same lines is not held), "
                         "so the office cannot tell the work is there; nothing was pushed")
        else:
            lines.append(f"office deliver {folder} --branch {b} continues on that branch instead, so this delivery is "
                         "added to the review already open there; nothing was pushed")
    return lines


def unread_line(label, unread):
    """What the check says of delivery.md's lines it did not read, since a
    line skipped without a word is a silent skip."""
    return (f"{label}: the to: line and the Commit and Review sections are read, the words that leave; its "
            f"{unread} other line(s) (the page's heading, office land's filing note, anything else above the first "
            "Commit or Review) stay in the office and are not read")


# The far side of the clean merge (0.39.0), in the clone where the work
# lives: the base merged into the checked-out workbench branch as a real
# merge commit, with the message the office writes, as the declared author
# (the environment in front of the command); on a conflict the files are
# named, the merge is aborted, and the abort is checked (no MERGE_HEAD, no
# tracked change left), so nothing is left half-done.
_MERGE_SCRIPT = (
    'm="$1"; t="$2"; '
    'if err=$(git merge -q --no-ff --no-edit -m "$m" "$t" 2>&1 >/dev/null); then '
    'echo "merged=$(git rev-parse HEAD)"; echo "brought=$(git rev-list --count HEAD^1..HEAD^2)"; exit 0; fi; '
    # A merge that never started (an untracked file in its way, say) left
    # nothing to abort: its words, and exit 8.
    'if ! git rev-parse -q --verify MERGE_HEAD >/dev/null; then printf "%s\\n" "$err" | tail -n 2 >&2; exit 8; fi; '
    'git diff --name-only --diff-filter=U | sed "s/^/conflict=/"; '
    'git merge --abort || exit 5; '
    'if git rev-parse -q --verify MERGE_HEAD >/dev/null; then exit 6; fi; '
    '[ -z "$(git status --porcelain=v1 -uno)" ] || exit 7; exit 4'
)
MERGE_MESSAGE = "Bring {audience}/{base} into the workbench (office deliver)"


def merge_base_in(place, view, name, audience, base, base_sha, author, rd=None):
    """Bring the audience's base into the workbench in the clone, when the
    workbench is behind it and the merge is clean (0.39.0); view is the
    clone's (orf.clone_view), read with the base. Returns
    (merged, told): merged is {sha, brought, base} when a merge commit was
    made, else None; told says why not, when there is something to say.
    A conflict raises DeliverError, with nothing left half-done there."""
    import office_refresh as orf
    track = f"refs/remotes/{audience}/{base}"
    if view["level"] or view["empty"]:
        # Level with the base already, or nothing of its own on it: no merge.
        return None, []
    wb = view["branch"]
    behind = f"the workbench ({wb}) is behind {audience}/{base} ({base_sha[:12]})"
    if view["dirty"]:
        return None, [f"{behind}, and the clone has uncommitted changes ({len(view['dirty'])} path(s): "
                      f"{', '.join(view['dirty'][:6])}), so {audience}/{base} was not merged into it; the squash runs "
                      "from where they parted, as before"]
    try:
        sessions = orf.open_sessions(place, rd)
    except ob.BaleError as exc:
        return None, [f"{behind}, and the sessions open in the clone could not be read ({exc}), so "
                      f"{audience}/{base} was not merged under them; the squash runs from where they parted, as before"]
    if sessions:
        return None, [f"{behind}, and {len(sessions)} session(s) are open in the clone ({', '.join(sessions)}), so "
                      f"{audience}/{base} was not merged under them; the squash runs from where they parted, as before"]
    _, identity = identity_of(author)
    message = MERGE_MESSAGE.format(audience=audience, base=base)
    argv = ["env", *[f"{k}={v}" for k, v in identity.items()], "sh", "-c", _MERGE_SCRIPT, "office-merge", message, track]
    try:
        run = ohost.run_in(place, argv, timeout=ohost.TRANSFER_TIMEOUT)
    except ohost.HostError as exc:
        raise DeliverError([f"{name}: {exc}"])
    facts = [l.split("=", 1) for l in run.stdout.splitlines() if "=" in l]
    if run.returncode == 0:
        got = dict(facts)
        log(f"brought {audience}/{base} into the workbench ({wb}) in the clone at {place}: merge commit "
            f"{got.get('merged', '')[:12]}, as {author}")
        return {"sha": got.get("merged", ""), "brought": int(got.get("brought") or 0), "base": base_sha}, []
    conflicts = [v for k, v in facts if k == "conflict"]
    if run.returncode == 8:
        return None, [f"{behind}, and git merge {audience}/{base} could not start in the clone "
                      f"({ohost._last_words(run.stderr)}), so nothing changed there; the squash runs from where they "
                      "parted, as before"]
    if run.returncode == 4:
        # 0.40.0: the plan writes the merge's materials and names the merge
        # session (merge_job_lines); the occupant is never sent to the clone.
        raise MergeConflict([f"the landed work does not go onto {audience}'s {base} as it is now: bringing "
                             f"{audience}/{base} into the workbench ({wb}) conflicts in "
                             f"{', '.join(conflicts[:12]) or 'files git did not name'}; the merge was aborted there, "
                             "and nothing is left half-done in the clone"], conflicts)
    state = {5: "git merge --abort failed", 6: "MERGE_HEAD is still there after git merge --abort",
             7: "tracked changes are left after git merge --abort"}.get(run.returncode, f"exit {run.returncode}")
    raise DeliverError([f"bringing {audience}/{base} into the workbench in the clone at {place} conflicted "
                        f"({', '.join(conflicts[:12]) or 'files not named'}), and {state}: "
                        f"{ohost._last_words(run.stderr)}; look at the clone (git status there) before anything else, "
                        "and deliver again once it is clean"])


def merged_text(audience, base, merged, sid=None):
    """The folder's History text for a clean merge (0.39.0), and for a merge
    session's resolution made a merge commit (0.40.0: sid names it)."""
    return (f"{audience}/{base} {merged['base'][:7]} into the workbench, {merged['sha'][:7]}"
            + (f", resolved by {sid}" if sid else ""))


# --- the merge session (0.40.0) ----------------------------------------------------------------
#
# When bringing a side of the audience into the workbench conflicts (the base,
# at deliver's step 4c; or the delivery branch's tip, when a continued
# delivery's squash conflicts at step 7), the office does not resolve it and
# does not send the occupant to a terminal. It leaves the clone clean, writes
# the merge's materials into the folder, under merge/ (each conflicting file
# in its three versions, parted/, workbench/ and audience/, at its path, and
# log.txt, the audience's commits since the two sides parted), with a page,
# merge/merge.md, that names the job; and its Next line is `office start N
# --merge`, which sends a bale session on the folder with both sides in
# context (templates/merge-brief.md). When that session lands, office land
# makes the merge real: a merge commit in the workbench whose first parent is
# the landed session's tip and whose second is the side it brings in, its
# tree git's own merge of what did not conflict and, for each file the job
# names, the session's landed version (the office takes the session's
# resolution and adds nothing of its own). office deliver makes it instead
# when land could not (a session open in the clone, a host that did not
# answer). The page is the job's whole state: it is there until the merge
# commit is made, and `- session: SID` names the session sent for it.

MERGE_DIR = "merge"
MERGE_PAGE = "merge.md"
MERGE_SIDES = ("parted", "workbench", "audience")
MERGE_FIELD_RE = oh.LazyPattern(r"^- (project|audience|kind|branch|tip|workbench|parted|day|file|session): (.+?)\s*$")
MERGE_KINDS = ("base", "branch")
RESOLVED_MESSAGE = "Bring {audience}/{branch} into the workbench, resolved by {sid} (office {verb})"


class MergeConflict(DeliverError):
    """Bringing a side of the audience into the workbench conflicts: the
    files, for the merge session's materials (lines say it as before)."""

    def __init__(self, lines, conflicts):
        super().__init__(lines)
        self.conflicts = conflicts


def merge_page_path(folder_dir):
    return pathlib.Path(folder_dir) / MERGE_DIR / MERGE_PAGE


def read_merge_job(folder_dir):
    """The merge job a folder holds (merge/merge.md), as a dict: project,
    audience, kind (base or branch), branch, tip, workbench, parted, day,
    files (a list) and session (or None); None when the folder holds none.
    A page that does not read as a job raises DeliverError naming it."""
    path = merge_page_path(folder_dir)
    if not path.is_file():
        return None
    job = {"files": [], "session": None}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = MERGE_FIELD_RE.match(line)
        if not m:
            continue
        if m.group(1) == "file":
            job["files"].append(m.group(2))
        else:
            job[m.group(1)] = m.group(2)
    missing = [k for k in ("project", "audience", "kind", "branch", "tip", "workbench") if not job.get(k)]
    if missing or job["kind"] not in MERGE_KINDS or not job["files"]:
        raise DeliverError([f"{path} does not read as a merge job (" + (f"no {', '.join(missing)} line" if missing
                            else "no file line" if not job["files"] else f"kind {job['kind']}") + "); office deliver "
                            "writes it again when the merge conflicts"])
    return job


def merge_page_text(job):
    """merge/merge.md: what the job is, in words, then its field lines (read
    back by read_merge_job)."""
    side = f"{job['audience']}/{job['branch']}"
    lines = [f"# Merge: {side} into the workbench", "",
             f"office deliver wrote this page on {job['day']} when bringing {side} into the workbench conflicted in "
             f"{len(job['files'])} file(s). Beside it are each file's three versions, at its path: parted/ (where the "
             "two sides parted), workbench/ (the workbench's) and audience/ (the audience's), and log.txt, the "
             "audience's commits since they parted. `office start N --merge` sends the merge session that resolves "
             "them, and `office land` makes its resolution a merge commit in the workbench; the office never "
             "resolves a conflict itself.", ""]
    for key in ("project", "audience", "kind", "branch", "tip", "workbench", "parted", "day"):
        if job.get(key):
            lines.append(f"- {key}: {job[key]}")
    lines += [f"- file: {f}" for f in job["files"]]
    if job.get("session"):
        lines.append(f"- session: {job['session']}")
    return "\n".join(lines) + "\n"


# The materials, made where the commits are (the clone, through its shell for
# a clone on a host, or the repo the delivery is built in) and carried here as
# one tar stream on stdout: each file at each of the three commits (a side
# that does not have the file has no copy of it), and the audience's log
# since the parting point. "-" for the parted commit is the merge base of the
# other two; the commits it read are said on stderr.
_MATERIALS_SCRIPT = (
    'w=$(git rev-parse --verify -q "$2^{commit}") || exit 4; a=$(git rev-parse --verify -q "$3^{commit}") || exit 4; '
    'p="$1"; [ "$p" != - ] || p=$(git merge-base "$w" "$a") || exit 5; l="$4"; [ "$l" != - ] || l="$p"; shift 4; '
    'echo "workbench=$w" >&2; echo "parted=$p" >&2; '
    'd=$(mktemp -d "${TMPDIR:-/tmp}/' + ohost.SCRATCH_PREFIX + 'merge-XXXXXXXX") || exit 1; '
    'for s in "parted $p" "workbench $w" "audience $a"; do n=${s%% *}; c=${s#* }; '
    'for f; do if git cat-file -e "$c:$f" 2>/dev/null; then '
    'mkdir -p "$d/$n/$(dirname -- "$f")" && git cat-file blob "$c:$f" > "$d/$n/$f" || { rm -rf "$d"; exit 2; }; '
    'fi; done; done; '
    'git log --format="%h %ad %an: %s" --date=short "$l..$a" > "$d/log.txt" || { rm -rf "$d"; exit 3; }; '
    'tar -cf - -C "$d" .; rc=$?; rm -rf "$d"; exit $rc'
)


def carry_materials(where, commits, files, dest):
    """The merge's materials into dest (made anew): commits is (parted or
    "-", workbench, audience, log from or "-"), read in where, a Place (a
    clone, here or on its host) or a repo on this machine. Returns the
    parted and workbench commits as the script resolved them. A tar member
    outside the three sides and log.txt refuses, and nothing is written."""
    import shlex
    import shutil
    import subprocess
    import tarfile
    import tempfile
    place = where if isinstance(where, ohost.Place) else ohost.Place(str(where))
    args = [*commits, *files]
    with tempfile.TemporaryDirectory(prefix="office-deliver-merge-") as tmp:
        tar = pathlib.Path(tmp) / "materials.tar"
        with open(tar, "wb") as fh:
            if place.hosted:
                command = (f"cd {ohost.shell_path(place.path)} && sh -c {shlex.quote(_MATERIALS_SCRIPT)} office-merge "
                           + " ".join(shlex.quote(a) for a in args))
                rc, _, err = ohost._raw(place, command, stdout=fh)
            else:
                debug(f"the merge's materials, read in {place.path}: {ohost.shown_argv(args)}")
                try:
                    proc = subprocess.run(["sh", "-c", _MATERIALS_SCRIPT, "office-merge", *args], cwd=place.path,
                                          stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.PIPE,
                                          timeout=ohost.TRANSFER_TIMEOUT)
                except (OSError, subprocess.TimeoutExpired) as exc:
                    raise DeliverError([f"the merge's materials could not be read in {place}: {exc}"])
                rc, err = proc.returncode, proc.stderr.decode("utf-8", "replace")
        if rc != 0:
            raise DeliverError([f"the merge's materials could not be read in {place} (exit {rc}): "
                                f"{ohost._last_words(err)}"])
        said = dict(l.split("=", 1) for l in err.splitlines() if l.startswith(("workbench=", "parted=")))
        out = pathlib.Path(tmp) / "out"
        out.mkdir()
        try:
            with tarfile.open(tar) as t:
                for m in t.getmembers():
                    parts = [p for p in pathlib.PurePosixPath(m.name).parts if p != "."]
                    if not parts:
                        continue
                    if m.name.startswith("/") or ".." in parts or not (m.isdir() or m.isfile()) \
                            or not (parts[0] in MERGE_SIDES or parts == ["log.txt"]):
                        raise DeliverError([f"the merge's materials from {place} hold {m.name!r}, outside the three "
                                            "sides and log.txt; nothing was written"])
                if hasattr(tarfile, "data_filter"):
                    t.extractall(out, filter="data")
                else:
                    t.extractall(out)
        except (tarfile.TarError, OSError) as exc:
            raise DeliverError([f"the merge's materials from {place} did not arrive as a readable archive: {exc}"])
        dest = pathlib.Path(dest)
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(out), str(dest))
    return said.get("parted", ""), said.get("workbench", "")


def commit_folder_paths(office_root, message, *rels):
    """git add -A and commit the paths alone in the office (a removed path
    is committed as removed; a path neither on disk nor tracked is no
    path to commit)."""
    root = pathlib.Path(office_root)
    rels = [r for r in rels if (root / r).exists() or ob.git(root, "ls-files", "--", r).stdout.strip()]
    if not rels:
        return
    ob.git(office_root, "add", "-A", "--", *rels)
    if ob.git(office_root, "diff", "--cached", "--quiet", "--", *rels, check=False).returncode != 0:
        ob.git(office_root, "commit", "-q", "-m", message, "--", *rels)


def merge_job_lines(office_root, rel, folder, project, where, kind, audience, side, tip, workbench, conflicts,
                    day=None, parted="-", log_from="-"):
    """What deliver says when bringing a side of the audience into the
    workbench conflicts (0.40.0): the job written into the folder with its
    materials, and the one office line that sends the merge session; or,
    when the same job already has a session out, the line that lands it.
    The clone was left clean before this is called. Returns the lines."""
    import time
    folder_dir = pathlib.Path(office_root) / rel
    side_name = f"{audience}/{side}"
    if not rel.startswith("desk/"):
        # Filed paper only grows: the materials are written on the desk.
        return [f"{rel} is in the filing cabinet, where the merge's materials are not written: office reopen {folder} "
                f"brings it back to the desk, and office deliver {folder} then writes them and names the merge "
                "session; nothing was pushed"]
    try:
        old = read_merge_job(folder_dir)
    except DeliverError:
        old = None
    if old and old.get("session") and old["kind"] == kind and old["branch"] == side and old["tip"] == tip \
            and old["workbench"] == workbench and sorted(old["files"]) == sorted(conflicts):
        return [f"the merge session {old['session']} was sent for this conflict ({rel}/{MERGE_DIR}/ holds its "
                f"materials) and has not landed: office land {old['session']} brings it back and makes its "
                f"resolution the merge commit, then office deliver {folder} delivers; nothing was pushed"]
    try:
        parted, workbench_read = carry_materials(where, (parted, workbench, tip, log_from), conflicts,
                                                 folder_dir / MERGE_DIR)
        job = {"project": project, "audience": audience, "kind": kind, "branch": side, "tip": tip,
               "workbench": workbench_read or workbench, "parted": parted, "day": day or time.strftime("%Y-%m-%d"),
               "files": list(conflicts), "session": None}
        merge_page_path(folder_dir).write_text(merge_page_text(job), encoding="utf-8")
        commit_folder_paths(office_root, f"office deliver: the merge's materials for {folder}", f"{rel}/{MERGE_DIR}")
    except (DeliverError, ohost.HostError, ob.LandError, OSError) as exc:
        why = "; ".join(exc.lines) if isinstance(exc, DeliverError) else str(exc)
        return [f"the merge's materials could not be written into {rel}/{MERGE_DIR}/ ({why}): office deliver "
                f"{folder} tries again; nothing was pushed"]
    log(f"wrote the merge's materials into {rel}/{MERGE_DIR}/: {len(conflicts)} file(s) in three versions "
        f"(parted, workbench, {audience}) and {audience}'s log since they parted, committed in the office")
    return [f"the merge's materials are in {rel}/{MERGE_DIR}/ (each file as the two sides parted, the workbench's "
            f"and {side_name}'s, and {audience}'s log since they parted)",
            f"office start {folder} --merge sends the merge session that resolves them, a bale session on {project} "
            "with both sides in context; office land makes its resolution a merge commit in the workbench, and "
            f"office deliver {folder} then delivers the folder's own work; nothing was pushed"]


# The merge commit for a landed merge session's resolution, in the clone
# where the work lives, as the declared author (the environment in front):
# the side's tip merged into the checked-out branch with --no-commit, each
# file the job names taken as the checked-out branch holds it (the session's
# landed version; a file it does not hold is removed), and committed only
# when nothing else is unmerged. Anything else is aborted and the abort
# checked (no MERGE_HEAD, no tracked change left), so nothing is left
# half-done. Exit 13: the session has not landed in this clone (no applied/
# tag); 9: the tip is not in the clone; 0 with held=: the tip is in the
# workbench already.
_RESOLVED_SCRIPT = (
    'm="$1"; t="$2"; s="$3"; shift 3; '
    'ab() { git merge --abort || exit 5; if git rev-parse -q --verify MERGE_HEAD >/dev/null; then exit 6; fi; '
    '[ -z "$(git status --porcelain=v1 -uno)" ] || exit 7; exit "$1"; }; '
    'git rev-parse -q --verify "refs/tags/applied/$s^{commit}" >/dev/null || exit 13; '
    'git cat-file -e "$t^{commit}" 2>/dev/null || exit 9; '
    'if git merge-base --is-ancestor "$t" HEAD; then echo "held=$(git rev-parse HEAD)"; exit 0; fi; '
    'git merge-base --is-ancestor "refs/tags/applied/$s" HEAD || exit 10; '
    'if git rev-parse -q --verify MERGE_HEAD >/dev/null; then exit 12; fi; '
    '[ -z "$(git status --porcelain=v1 -uno)" ] || exit 11; '
    'err=$(git merge -q --no-ff --no-commit "$t" 2>&1 >/dev/null); '
    'if ! git rev-parse -q --verify MERGE_HEAD >/dev/null; then printf "%s\\n" "$err" | tail -n 2 >&2; exit 8; fi; '
    'for p; do if git cat-file -e "HEAD:$p" 2>/dev/null; then git checkout -q HEAD -- "$p" || ab 14; '
    'else git rm -q -f --ignore-unmatch -- "$p" >/dev/null || ab 14; fi; done; '
    'left=$(git diff --name-only --diff-filter=U); '
    'if [ -n "$left" ]; then printf "%s\\n" "$left" | sed "s/^/conflict=/"; ab 4; fi; '
    'git commit -q -m "$m" >/dev/null 2>&1 || ab 15; '
    'echo "merged=$(git rev-parse HEAD)"; echo "brought=$(git rev-list --count HEAD^1..HEAD^2)"'
)


def make_resolved_merge(place, job, author, verb):
    """The landed merge session's resolution made a merge commit in the
    clone (_RESOLVED_SCRIPT). Returns (merged, lines): merged is {sha,
    brought, base (the tip brought in), held} when the workbench now holds
    the tip (held: it did already, no commit was made), None when the
    session has not landed there (said in no line); lines say what
    happened or why not, each ending in an office line."""
    sid = job["session"]
    side = f"{job['audience']}/{job['branch']}"
    _, identity = identity_of(author)
    message = RESOLVED_MESSAGE.format(audience=job["audience"], branch=job["branch"], sid=sid, verb=verb)
    argv = ["env", *[f"{k}={v}" for k, v in identity.items()], "sh", "-c", _RESOLVED_SCRIPT, "office-merge",
            message, job["tip"], sid, *job["files"]]
    run = ohost.run_in(place, argv, timeout=ohost.TRANSFER_TIMEOUT)
    facts = [l.split("=", 1) for l in run.stdout.splitlines() if "=" in l]
    got = dict(facts)
    if run.returncode == 13:
        debug(f"the merge session {sid} has not landed in {place}: no applied/{sid} there")
        return None, []
    if run.returncode == 0 and got.get("held"):
        return {"sha": got["held"], "brought": 0, "base": job["tip"], "held": True}, [
            f"the workbench already holds {side} {job['tip'][:7]}, so no merge commit was made for {sid}"]
    if run.returncode == 0:
        log(f"made the merge session {sid}'s resolution a merge commit in the clone at {place}: "
            f"{got.get('merged', '')[:12]}, bringing {side} {job['tip'][:12]}, as {author}")
        return {"sha": got.get("merged", ""), "brought": int(got.get("brought") or 0), "base": job["tip"],
                "held": False}, []
    conflicts = [v for k, v in facts if k == "conflict"]
    why = {
        9: f"{side}'s tip {job['tip'][:12]} is not in the clone (office projects refresh {job['project']} brings "
           "the audience's branches there)",
        10: f"applied/{sid} is not on the clone's checked-out branch",
        11: "the clone has uncommitted changes",
        12: "a merge is in progress in the clone (MERGE_HEAD is there)",
        8: f"git merge could not start ({ohost._last_words(run.stderr)})",
        4: f"it conflicts outside the files the session resolved, in {', '.join(conflicts[:12])}; the merge was "
           "aborted there, and nothing is left half-done",
        14: "a resolved file could not be taken from the landed session; the merge was aborted there",
        15: "git commit refused the merge; it was aborted there",
    }.get(run.returncode)
    if why is None:
        state = {5: "git merge --abort failed", 6: "MERGE_HEAD is still there after git merge --abort",
                 7: "tracked changes are left after git merge --abort"}.get(run.returncode, f"exit {run.returncode}")
        raise DeliverError([f"the merge session {sid}'s resolution could not be made a merge commit in the clone at "
                            f"{place}, and {state}: {ohost._last_words(run.stderr)}; look at the clone (git status "
                            "there) before anything else"])
    return None, [f"the merge session {sid}'s resolution was not made a merge commit in the clone at {place}: {why}"]


def resolve_landed_job(office_root, rel, folder, place, author, day, verb, sid=None, rd=None):
    """A folder's merge job whose session has landed, made a merge commit
    (office land, right after the landing; office deliver, before it plans,
    when land could not). sid given: only the job that session was sent
    for. Never under a session open in the clone. Returns (merged or None,
    lines to say); the merged History line is written and the job's
    materials removed from the folder, committed together."""
    import shutil
    import office_refresh as orf
    folder_dir = pathlib.Path(office_root) / rel
    try:
        job = read_merge_job(folder_dir)
    except DeliverError as exc:
        # A page that does not read holds no job to make: said, and the next
        # conflict writes it again (merge_job_lines).
        for line in exc.lines:
            log(f"warning: {line}")
        return None, []
    if job is None or not job.get("session") or (sid and job["session"] != sid):
        return None, []
    try:
        sessions = orf.open_sessions(place, rd)
    except ob.BaleError as exc:
        return None, [f"the merge session {job['session']}'s resolution was not made a merge commit: the sessions "
                      f"open in the clone could not be read ({exc}); office deliver {folder} makes it"]
    if job["session"] in sessions:
        # Sent and still out: nothing has landed to make a merge of. Deliver
        # stops here and names the landing (0.42.0: the whole loop's test
        # found that, with the session open in the clone, deliver went on to
        # a squash that conflicts and named no office line for it).
        debug(f"the merge session {job['session']} is still open in the clone")
        if verb != "deliver":
            return None, []
        return None, [f"the merge session {job['session']} was sent for {rel}'s merge job ({rel}/{MERGE_DIR}/ holds "
                      f"its materials) and has not landed: office land {job['session']} brings it back and makes "
                      f"its resolution the merge commit, then office deliver {folder} delivers; nothing was pushed"]
    if sessions:
        return None, [f"the merge session {job['session']}'s resolution was not made a merge commit: "
                      f"{len(sessions)} session(s) are open in the clone ({', '.join(sessions)}), and a merge is never "
                      f"made under them; office deliver {folder} makes it once they have landed"]
    try:
        merged, lines = make_resolved_merge(place, job, author, verb)
    except ohost.HostError as exc:
        return None, [f"the merge session {job['session']}'s resolution was not made a merge commit: {exc}; "
                      f"office deliver {folder} makes it"]
    if merged is None:
        return None, [l + f"; office deliver {folder} makes it once that is put right" for l in lines]
    told = list(lines)
    if not merged["held"]:
        text = merged_text(job["audience"], job["branch"], merged, job["session"])
        try:
            _, wrote = oh.folder_event(folder_dir / "folder.md", day, "merged", text)
            if wrote:
                told.append(f"{rel}/folder.md: History: {day} merged: {text}")
        except (OSError, oh.HelperError) as exc:
            told.append(f"{rel}/folder.md: the merge could not be recorded ({exc}); it is in the clone")
        merged["line"] = (f"made the merge session {job['session']}'s resolution a merge commit: {merged['sha'][:7]}, "
                          f"bringing {job['audience']}/{job['branch']} {job['tip'][:7]} into the workbench")
        told.insert(0, merged["line"])
    shutil.rmtree(folder_dir / MERGE_DIR, ignore_errors=True)
    try:
        commit_folder_paths(office_root, f"office {verb}: {job['audience']}/{job['branch']} into the workbench for "
                            f"{folder}, resolved by {job['session']}", f"{rel}/folder.md", f"{rel}/{MERGE_DIR}")
    except (ob.LandError, OSError) as exc:
        told.append(f"{rel}: the merge's record could not be committed ({exc}); git status in the office shows it")
    return merged, told


def merge_start(office_root, folder, brief_out):
    """What office start N --merge sends (0.40.0): the folder's merge job's
    project, the goal, the forecast (each file the job names that the
    workbench holds, else its directory, else the whole repo) and the
    brief, written to brief_out from the install's templates/merge-brief.md.
    Returns a dict: project, goal, writes, said (lines)."""
    rel, md = find_folder(office_root, folder)
    if not rel.startswith("desk/"):
        raise DeliverError([f"{rel} is in the filing cabinet: office reopen {folder} brings it back to the desk, and "
                            f"office start {folder} --merge sends the merge session then"])
    job = read_merge_job(md.parent)
    if job is None:
        raise DeliverError([f"{rel} holds no merge waiting for a session ({rel}/{MERGE_DIR}/{MERGE_PAGE} is not "
                            f"there): office deliver {folder} writes one when bringing the audience into the workbench "
                            "conflicts"])
    parsed = oh.parse_folder(md.read_text(encoding="utf-8"))
    number = (parsed["fields"].get("number") or [""])[0]
    title = parsed["title"] or folder
    side = f"{job['audience']}/{job['branch']}"
    here = md.parent / MERGE_DIR
    writes = []
    for f in job["files"]:
        if (here / "workbench" / f).is_file():
            writes.append(f)
        else:
            parent = str(pathlib.PurePosixPath(f).parent)
            if parent in (".", ""):
                writes = []
                break
            writes.append(parent)
    else:
        writes = list(dict.fromkeys(writes))
    if job.get("session"):
        said = [f"{rel}'s merge job named {job['session']} as its session; this one takes its place, and office land "
                "makes the merge commit for this one"]
    else:
        said = []
    files = job["files"]
    goal = (f"Resolve the conflicts of bringing {side} {job['tip'][:7]} into the workbench of "
            + (f"folder {number}" if number else rel) + f", in {', '.join(files[:3])}"
            + (f" and {len(files) - 3} more" if len(files) > 3 else ""))
    template = (TEMPLATES / "merge-brief.md").read_text(encoding="utf-8")
    values = {"title": title, "folder": f"folder {number}" if number else rel, "rel": rel, "project": job["project"],
              "side": side, "tip": job["tip"][:12], "workbench": job["workbench"][:12],
              "parted": (job.get("parted") or "")[:12] or "their merge base",
              "where": ("the audience's base branch" if job["kind"] == "base"
                        else "the branch this folder's work is delivered on, which moved on the audience since "
                             "the last delivery"),
              "files": "\n".join(f"- {f}" for f in files), "materials": f"{rel}/{MERGE_DIR}/"}
    pathlib.Path(brief_out).write_text(oh.render_template(template, values), encoding="utf-8")
    return {"project": job["project"], "goal": goal, "writes": writes, "said": said, "rel": rel}


def merge_sent(office_root, rel, sid):
    """The session office start --merge sent, named on the job's page and
    committed alone. Returns the line to say."""
    folder_dir = pathlib.Path(office_root) / rel
    job = read_merge_job(folder_dir)
    if job is None:
        raise DeliverError([f"{rel} holds no merge job, so {sid} was not named on one"])
    job["session"] = sid
    merge_page_path(folder_dir).write_text(merge_page_text(job), encoding="utf-8")
    commit_folder_paths(office_root, f"office start: {sid} sent for the merge in {rel.split('/')[-1]}",
                        f"{rel}/{MERGE_DIR}/{MERGE_PAGE}")
    return f"{rel}/{MERGE_DIR}/{MERGE_PAGE} names {sid} as the merge session; office land {sid} makes its resolution " \
           "a merge commit in the workbench"


def land_merge(office_root, project, sid, folder_rel, day):
    """office land's step after an applied landing (0.40.0): when the
    folder's merge job names this session, its resolution made the merge
    commit. Returns (is a merge session, lines)."""
    root = pathlib.Path(office_root)
    try:
        job = read_merge_job(root / folder_rel)
    except DeliverError as exc:
        return False, [f"warning: {l}" for l in exc.lines]
    if job is None or job.get("session") != sid:
        return False, []
    entry = next((p for p in ob.office_projects(root) or [] if p["name"] == project), None)
    if entry is None or entry["problem"] or not entry.get("author"):
        why = "no such project" if entry is None else entry["problem"] or f"{project} declares no author"
        return True, [f"the merge session {sid}'s resolution was not made a merge commit: {why}; office deliver "
                      f"{folder_rel.split('/')[-1]} makes it once that is put right"]
    try:
        _, lines = resolve_landed_job(root, folder_rel, folder_rel.split("/")[-1], ohost.place_of(entry),
                                      entry["author"], day, "land", sid=sid)
    except DeliverError as exc:
        return True, [f"error: {l}" for l in exc.lines]
    return True, lines


def plan(consumption, office_root, folder, branch=None, project_name=None, others_ok=False, interactive=False,
         author_given=None, adopt=False, refresh=None, day=None):
    """Everything a delivery needs before the one question, written as a
    dict for run(): the project and its audience, author and base; the
    sessions covered and whose folders they belong to; the words; the
    worktree with the squash staged, what bale's own commits changed taken
    out of it (own, own_lines; 0.36.0); the diff's stat; the letterhead
    check's hits. Raises DeliverError when it cannot go on, having
    removed what it made."""
    import shlex
    import tempfile
    import time
    import office_letterhead as olh
    import office_refresh as orf
    office_root = pathlib.Path(office_root).resolve()
    rel, md = find_folder(office_root, folder)
    parsed = oh.parse_folder(md.read_text(encoding="utf-8"))
    title = parsed["title"] or folder
    # 1. The project: the folder's lane's, or the one named.
    projects = {p["name"]: p for p in ob.office_projects(office_root) or []}
    lane = oh.folder_lane_project(md)
    if project_name and lane and project_name != lane:
        raise DeliverError([f"{folder}'s lane names {lane}, not {project_name}; a folder is delivered on its lane's project"])
    name = lane or project_name
    if not name:
        raise DeliverError([f"{folder} has no lane naming a project, so say which: office deliver {folder} --on PROJECT "
                            f"({', '.join(sorted(projects)) or 'this office scopes no project'})"])
    entry = projects.get(name)
    if entry is None:
        raise DeliverError([f"no project named {name} in this office's [projects] (it lists: {', '.join(sorted(projects)) or 'none'})"])
    if entry["problem"]:
        raise DeliverError([f"{name}: {entry['problem']}"])
    if entry["declaration_problems"]:
        raise DeliverError([f"{name}: {p}" for p in entry["declaration_problems"]])
    audience = entry.get("audience")
    if not audience:
        raise DeliverError([f"{name} declares no audience, so nothing of it is delivered: office projects set {name} "
                            "--audience REMOTE names the remote in its clone that points at the audience's git host"])
    place = ohost.place_of(entry)
    if not place.hosted and not pathlib.Path(place.path).is_dir():
        raise DeliverError([f"no such directory on this machine: {place.path}"])
    # 2. The words, before anything travels: missing, deliver stops here.
    delivery_md = md.parent / oh.PAGE_FILES["delivery"]
    if not delivery_md.is_file():
        raise DeliverError([f"{rel}/delivery.md is not written, so there are no words to deliver with: the build "
                            "session writes them as the Delivery section of its notes.md (the install's "
                            "templates/delivery.md says the shape) and office land files them there; or write "
                            f"{rel}/delivery.md yourself from that template (a Commit section: the subject, a blank "
                            "line, the body; a Review section: the title, a blank line, the body; a `- to:` line "
                            "naming the reviewer)"])
    try:
        words = oh.parse_delivery(delivery_md.read_text(encoding="utf-8"))
    except oh.HelperError as exc:
        raise DeliverError([f"{rel}/delivery.md: {exc}"])
    # 3. The clone, where it is: the reach, its remotes, identity and guard;
    # and since 0.39.0 its view of the audience (its remote-tracking
    # branches, and where the checked-out branch stands against the base),
    # in the same connection.
    try:
        runs = ohost.run_many(place, [ohost.git_facts_argv(place), *orf.view_argvs(audience, entry.get("base"))])
        facts = ohost.read_git_facts(place, runs[0])
    except ohost.HostError as exc:
        raise DeliverError([f"{name}: {exc}"])
    url = facts["remotes"].get(audience)
    if not url:
        raise DeliverError([f"{name}'s clone at {place} has no remote named {audience} (it has: "
                            f"{', '.join(sorted(facts['remotes'])) or 'none'}); office projects set {name} --audience "
                            "REMOTE names the right one"])
    author_told = []
    if author_given:
        # The flag sets the field: declared and kept, as office projects
        # set --author does.
        try:
            author_told.append(declare_author(office_root, name, author_given))
        except (oh.HelperError, ob.LandError) as exc:
            raise DeliverError([f"--author: {exc}"])
        entry = dict(entry, author=oh.check_author(author_given))
    author = entry.get("author")
    if not author:
        clone_identity = (f"{facts['name']} <{facts['email']}>" if facts.get("name") and facts.get("email") else None)
        raise NeedsAuthor([f"{name} declares no author, so the identity its audience expects on the commits is not "
                           "known, and the clone's own identity is never used silently"
                           + (f" (the clone's is {clone_identity})" if clone_identity else ""),
                           f"office deliver {folder} --author 'Name <email>' declares it and keeps it (office projects "
                           f"set {name} --author does too); piped input is never asked"], name, clone_identity)
    base = entry.get("base") or facts["remote_heads"].get(audience)
    if not base:
        raise DeliverError([f"{name}'s clone does not say which branch {audience} points at (no {audience}/HEAD), "
                            f"so the base is not known; office projects set {name} --base BRANCH names it"])
    # The delivery branch, by the branch rule (the gaps of 2026-10-28, A3):
    # --branch; else the words' branch line, behind the project's prefix;
    # else the clone's checked-out branch when the audience has it and it
    # is not the base (step 4, which can ask the audience); else the
    # folder's slug, behind the prefix. branch_why says which rule chose.
    prefix = entry.get("branch_prefix")
    try:
        branch, branch_why, branch_rule = named_branch(branch, words.get("branch"), name, prefix)
    except oh.HelperError as exc:
        raise DeliverError([f"the delivery branch: {exc}"])
    if branch is not None and branch == base:
        raise DeliverError([f"the delivery branch would be {branch}, which is the base itself; name another: --branch NAME"])
    # 0.42.0: the name is held to the letterhead's marks before anything is
    # fetched or made: a name the letterhead refuses in a line never leaves
    # as a branch either.
    import office_letterhead as olh_
    try:
        name_rules = office_rules(office_root)
    except (olh_.CheckError, OSError) as exc:
        raise DeliverError([f"the letterhead check could not run: {exc}"])
    if branch is not None:
        check_branch_name(branch, name_rules, branch_rule, branch_why)
    guard_lines = []
    if facts["guard"] == "none":
        try:
            guard_lines.append(ohost.install_push_guard(place, audience, url))
        except ohost.HostError as exc:
            guard_lines.append(f"warning: the push guard could not be installed in {place}: {exc}")
    elif facts["guard"] == "other":
        guard_lines.append(f"warning: {place} has a pre-push hook that is not the office's push guard, so a push to "
                           f"{audience} by hand is not refused there")
    # 4. The repo the delivery is built in: the clone here, or a mirror.
    temp_dir, repo, wt_root, worktree = None, None, None, None
    try:
        if place.hosted:
            temp_dir, repo = mirror_here()
        else:
            repo = pathlib.Path(place.path)
        for ref in OFFICE_REFS:
            g(repo, "update-ref", "-d", ref, check=False)
        # The audience's base, and the branch when an earlier delivery made it.
        where = audience if not place.hosted else url
        log(f"fetching {audience}'s {base} from {url}")
        fetched = g(repo, "fetch", "-q", where, f"+refs/heads/{base}:{REF_BASE}", check=False, timeout=ohost.TRANSFER_TIMEOUT)
        if fetched.returncode != 0:
            raise DeliverError([f"{audience} ({url}) did not answer for {base} from this machine (git fetch exit "
                                f"{fetched.returncode}): {ohost._last_words(fetched.stderr)}; the audience is reached "
                                "with this machine's credentials, so check them (git ls-remote there, by hand)"])
        def fetch_branch(name_):
            return g(repo, "fetch", "-q", where, f"+refs/heads/{name_}:{REF_BRANCH}", check=False,
                     timeout=ohost.TRANSFER_TIMEOUT).returncode == 0

        on_branch = None
        if branch is None:
            # The clone's checked-out branch: office start checks out the
            # branch a brief's BRANCH line names, so it is the branch the
            # session was built on, when the audience has it (A4).
            checked_out, clone_said = facts.get("branch") or None, None
            if checked_out:
                try:
                    checked_out = oh.check_base(checked_out)
                except oh.HelperError:
                    clone_said, checked_out = f"the clone's branch {checked_out} is not a name git pushes", None
            if not checked_out:
                clone_said = clone_said or "the clone has no branch checked out"
            elif checked_out == base:
                clone_said = f"the clone's branch is {base}, the base"
            elif fetch_branch(checked_out):
                branch, on_branch, branch_rule = checked_out, True, "clone"
                branch_why = (f"the clone has {checked_out} checked out and {audience} has it: the branch the "
                              "session was built on")
            else:
                clone_said = f"the clone's branch {checked_out} is not on {audience}"
            if branch is None:
                try:
                    branch, branch_why = slug_branch(folder, name, prefix, clone_said)
                except oh.HelperError as exc:
                    raise DeliverError([f"the delivery branch from the folder's slug: {exc}; name one: --branch NAME"])
                branch_rule = "slug"
            if branch == base:
                raise DeliverError([f"the delivery branch would be {branch}, which is the base itself; name another: "
                                    "--branch NAME"])
            # The clone's branch or the slug, once the audience has said
            # which (0.42.0): held to the marks before the base is brought
            # in or anything is made.
            check_branch_name(branch, name_rules, branch_rule, branch_why)
        if on_branch is None:
            on_branch = fetch_branch(branch)
        continuing = on_branch
        # 4b. The clone's view of the audience (0.39.0): its AUDIENCE/BASE
        # against the base as fetched here. Behind, it is said in one line,
        # and refreshed when the occupant says so (--refresh, or yes on a
        # terminal: bin/office asks and plans again); piped with neither
        # flag, it is said and the plan goes on without. Ahead or level:
        # nothing is said.
        base_sha = g(repo, "rev-parse", REF_BASE).stdout.strip()
        try:
            # A clone on this machine is the repo the base was just fetched
            # into, from its own remote by name, and git moved its
            # AUDIENCE/BASE with that fetch: its view is read again here. A
            # hosted clone's view is the one read with its facts.
            view = (orf.read_view(place, audience, runs[1:]) if place.hosted
                    else orf.clone_view(place, audience, base))
        except orf.RefreshError as exc:
            raise DeliverError(exc.lines)
        view_told, base_merge = [], None
        behind = orf.behind_words(repo, audience, base, view["remote"].get(base), base_sha)
        if behind:
            if refresh is None and interactive:
                raise NeedsRefresh([behind], name)
            if refresh:
                try:
                    view_told, _ = orf.refresh(office_root, name, entry=entry)
                    view = orf.clone_view(place, audience, base)
                except (orf.RefreshError, ohost.HostError) as exc:
                    raise DeliverError(getattr(exc, "lines", None) or [str(exc)])
                view_told.insert(0, f"{behind}: refreshed (office projects refresh {name})")
                if not place.hosted:
                    # A base checked out and fast-forwarded is the workbench.
                    facts["head"] = g(repo, "rev-parse", "HEAD").stdout.strip()
            else:
                view_told.append(f"{behind}; not refreshed" + (" (--no-refresh)" if refresh is False else
                                 f" (piped: office deliver {folder} --refresh, or office projects refresh {name})"))
        # 4c. The clean merge (0.39.0): a delivery made from the base
        # (not one continuing on a branch) squashes from where the workbench
        # and the base parted; when the workbench is behind the base, the
        # base is brought into it first, in the clone where the work lives,
        # as a real merge commit, when that merge is clean and the tree is
        # clean, so the range read below carries the folder's own work and
        # the squash runs from the base's tip. A conflict refuses here, the
        # merge aborted and checked; base_holds, twice_lines and the squash
        # are as they were.
        # 0.40.0: a merge session that landed, whose resolution office land
        # could not make a merge commit (a session open in the clone, a host
        # that did not answer), is made one here first, so what follows reads
        # the workbench with the side it brings in.
        on = day or time.strftime("%Y-%m-%d")
        resolved, told_ = resolve_landed_job(office_root, rel, folder, place, author, on, "deliver")
        view_told += told_
        if resolved and not resolved["held"]:
            view = orf.clone_view(place, audience, base)
            if not place.hosted:
                facts["head"] = resolved["sha"]
        elif told_ and resolved is None:
            # The job's session landed and its merge could not be made: the
            # delivery waits for it, since what it would squash is not the
            # folder's own work alone.
            raise DeliverError(told_)
        if not continuing and view["remote"].get(base) == base_sha and view["branch"]:
            try:
                base_merge, told_ = merge_base_in(place, view, name, audience, base, base_sha, author)
            except MergeConflict as exc:
                if not exc.conflicts:
                    raise DeliverError(exc.lines + [f"git named no file, so no merge session can be sent for it: "
                                                    f"office deliver {folder} tries again"])
                raise DeliverError(exc.lines + merge_job_lines(
                    office_root, rel, folder, name, place, "base", audience, base, base_sha,
                    view["heads"].get(view["branch"]) or "HEAD", exc.conflicts, day=on))
            view_told += told_
            if base_merge:
                if not place.hosted:
                    facts["head"] = base_merge["sha"]
                text = merged_text(audience, base, base_merge)
                try:
                    _, wrote = oh.folder_event(md, on, "merged", text)
                    if wrote:
                        ob.git(office_root, "add", "--", f"{rel}/folder.md")
                        ob.git(office_root, "commit", "-q", "-m", f"office deliver: {audience}/{base} into the "
                               f"workbench for {folder}", "--", f"{rel}/folder.md")
                        base_merge["history"] = f"{rel}/folder.md: History: {on} merged: {text}"
                except (OSError, oh.HelperError, ob.LandError) as exc:
                    base_merge["history"] = f"{rel}/folder.md: the merge could not be recorded ({exc}); it is in the clone"
                base_merge["line"] = (f"brought {audience}/{base} into the workbench: merge commit {base_merge['sha'][:7]} "
                                  f"({base_merge['brought']} commit{'' if base_merge['brought'] == 1 else 's'} of the "
                                  "audience's)")
        elif not continuing and view["remote"].get(base) != base_sha and behind:
            view_told.append(f"the workbench is not brought level with {audience}/{base} while the clone's view of it "
                             "is behind: the squash runs from where they parted, as before")
        # 5. The landed work: the clone's HEAD here, or carried as a bundle.
        applied = []
        if place.hosted:
            script = ('d=$(mktemp -d "${TMPDIR:-/tmp}/' + ohost.SCRATCH_PREFIX + 'XXXXXXXX") || exit 1; '
                      'b=$(git merge-base "refs/remotes/$1/$2" HEAD 2>/dev/null); '
                      'if [ -n "$b" ]; then git bundle create -q "$d/landed.bundle" "^$b" HEAD || exit 2; '
                      'else git bundle create -q "$d/landed.bundle" HEAD || exit 2; fi; echo "scratch=$d"; echo "prereq=$b"')
            try:
                runs = ohost.run_many(place, [
                    ["git", "for-each-ref", "--format=%(refname:short)", "refs/tags/applied/"],
                    ["sh", "-c", script, "office-bundle", audience, base],
                ], timeout=ohost.TRANSFER_TIMEOUT)
            except ohost.HostError as exc:
                raise DeliverError([f"{name}: {exc}"])
            tags, made = runs
            applied = [t.removeprefix("applied/") for t in tags.stdout.split() if t.startswith("applied/")]
            if made.returncode != 0:
                raise DeliverError([f"the landed work could not be bundled in {place} (exit {made.returncode}): "
                                    f"{ohost._last_words(made.stderr)}"])
            scratch = next((l[len("scratch="):] for l in made.stdout.splitlines() if l.startswith("scratch=")), None)
            if not scratch:
                raise DeliverError([f"the bundle's directory on {place.host} was not named; nothing was carried"])
            local_bundle = pathlib.Path(temp_dir) / "landed.bundle"
            try:
                command = (f"sha256sum {shlex.quote(scratch + '/landed.bundle')} >&2 && cat -- "
                           f"{shlex.quote(scratch + '/landed.bundle')}; rc=$?; rm -rf -- {shlex.quote(scratch)} "
                           f"|| echo '[office] warning: the temporary directory {scratch} on {place.host} was left behind' >&2; exit $rc")
                with open(local_bundle, "wb") as fh:
                    rc, _, err = ohost._raw(place, command, stdout=fh)
                if rc != 0:
                    raise DeliverError([f"the bundle could not be read from {place.host} (exit {rc}): {ohost._last_words(err)}"])
                sums = [m.group(1) for m in map(ohost._SHA_RE.match, err.splitlines()) if m]
                got = ohost.sha256_of(local_bundle)
                if not sums or sums[-1] != got:
                    raise DeliverError([f"the bundle from {place.host} did not arrive intact: sha256 "
                                        f"{sums[-1] if sums else 'not reported'} there, {got} here"])
            except ohost.HostError as exc:
                raise DeliverError([f"{name}: {exc}"])
            log(f"carried the landed work from {place.host} ({local_bundle.stat().st_size} bytes, checked by sha256)")
            verified = g(repo, "bundle", "verify", str(local_bundle), check=False)
            if verified.returncode != 0:
                raise DeliverError([f"the bundle of {name}'s landed work does not apply onto {audience}'s {base} as "
                                    f"fetched here: {ohost._last_words(verified.stderr)}; the clone's {audience}/{base} "
                                    "may no longer be on the audience's history (was it rewritten there?)"])
            g(repo, "fetch", "-q", str(local_bundle), f"+HEAD:{REF_WORKBENCH}")
        else:
            if not facts.get("head"):
                raise DeliverError([f"{place.path} has no commit on HEAD; nothing to deliver"])
            g(repo, "update-ref", REF_WORKBENCH, facts["head"])
            tags = g(repo, "for-each-ref", "--format=%(refname:short)", "refs/tags/applied/")
            applied = [t.removeprefix("applied/") for t in tags.stdout.split() if t.startswith("applied/")]
        workbench = g(repo, "rev-parse", REF_WORKBENCH).stdout.strip()
        # 6. The sessions covered: since the last delivery's workbench
        # commit when there was one, else since the branch and the base
        # parted.
        records = oh.delivered_records(md)
        # Another folder of this office that delivered to the branch made it
        # (the gaps of 2026-10-28, A4): the delivery continues on it with no
        # --adopt, the range starting at that folder's last delivery there.
        elsewhere = other_deliveries(office_root, rel, name, audience)
        own_on = any(rec["branch"] == branch for _, rec in records)
        joined = [x for x in elsewhere if x[2]["branch"] == branch] if continuing and not own_on else []
        if joined:
            where_, day_, _ = joined[-1]
            branch_why += f"; {where_} delivered to it on {day_}, so this delivery continues on it"
        log(f"the delivery branch is {branch}: {branch_why}")
        # A branch the audience has that no record of this office's covers
        # was made outside the office: adopted when the occupant says so
        # (--adopt; on a terminal bin/office asks, and the plan goes on so
        # the question shows the delivery whole), refused by name piped.
        adopting = continuing and not own_on and not joined
        if adopting and not (adopt or interactive):
            raise DeliverError([f"{audience} already has a branch named {branch}, and {rel} records no delivery on it, "
                                "nor does any other folder of this office, so it was made outside the office (a pull "
                                f"request opened by hand, say); it is the branch because {branch_why}",
                                f"office deliver {folder} --branch {branch} --adopt adds this delivery to it, as a "
                                "review's answer goes onto the review's own branch; or name another: --branch NAME; "
                                "piped input is never asked"])
        # 0.42.0: a delivery added to a branch the audience has (adopted,
        # joined or continued) reads the open pull request on that branch
        # through gh, when gh is here: its base is the delivery's from in the
        # question, said when it is not the project's declared base. The
        # squash is onto the branch's tip either way.
        review_pr, review_pr_told = None, None
        if continuing:
            import office_review as orev
            review_pr, review_pr_told = orev.open_pull_for(url, branch)
        since, since_why = None, None
        for _, rec in reversed(records):
            if rec["branch"] == branch and g(repo, "cat-file", "-e", f"{rec['workbench']}^{{commit}}", check=False).returncode == 0 \
                    and g(repo, "merge-base", "--is-ancestor", rec["workbench"], workbench, check=False).returncode == 0:
                since, since_why = rec["workbench"], f"the last delivery on {branch} ({rec['delivery'][:12]})"
                break
        if since is None and joined:
            for where_, _, rec in reversed(joined):
                if is_ancestor(repo, rec["workbench"], workbench):
                    since, since_why = rec["workbench"], f"{where_}'s last delivery on {branch} ({rec['delivery'][:12]})"
                    break
        if since is None and (adopting or joined):
            # What the adopted branch does not have yet: the workbench since
            # it and the branch parted (the branch's own commits, pushed by
            # hand from the clone, are then not delivered twice).
            mb = g(repo, "merge-base", REF_BRANCH, workbench, check=False)
            since = mb.stdout.strip() if mb.returncode == 0 and mb.stdout.strip() else None
            since_why = f"where the workbench branch and {audience}/{branch} parted" if since else None
        if since is None:
            mb = g(repo, "merge-base", REF_BASE, workbench, check=False)
            since = mb.stdout.strip() if mb.returncode == 0 and mb.stdout.strip() else None
            since_why = f"where the workbench branch and {audience}/{base} parted" if since else "the whole history"
        # 0.40.0: a merge session that brought the branch's tip into the
        # workbench (a continued delivery's conflict) made the workbench and
        # the branch meet there: the delivery is read from that meeting point,
        # a commit of the branch's own (never one the base holds), so the
        # resolution leaves with what is new and nothing the branch has
        # already. The sessions the branch already carries are not named
        # again.
        already_here = set()
        if continuing and since is not None:
            mb = g(repo, "merge-base", REF_BRANCH, workbench, check=False).stdout.strip()
            if mb and mb != since and not is_ancestor(repo, mb, since) and not is_ancestor(repo, mb, REF_BASE):
                since, since_why = mb, (f"where the workbench and {audience}/{branch} meet ({mb[:12]}, the branch's "
                                        "tip a merge session brought into the workbench)")
                already_here = {s for _, rec in records if rec["branch"] == branch for s in rec["sessions"]} \
                    | {s for _, _, rec in joined for s in rec["sessions"]}
        range_spec = f"{since}..{workbench}" if since else workbench
        if since == workbench:
            raise DeliverError([f"nothing new to deliver: the workbench is at {workbench[:12]}, which is {since_why}"])
        subjects = g(repo, "log", "--format=%s", range_spec).stdout.splitlines()
        commits = g(repo, "rev-list", "--count", range_spec).stdout.strip()
        found = sids_in_subjects(consumption, subjects)
        naming = ob.folders_naming(office_root)
        folder_sids = [s for s in parsed["sids"] if s in applied]
        if not folder_sids:
            raise DeliverError([f"{rel} records no session that is applied in {name} ({', '.join(parsed['sids']) or 'it records none'}; "
                                f"applied there: {', '.join(applied) or 'none'}); office sessions {folder} shows them"])
        covered = [s for s in found if s in applied and s not in already_here]
        mine = [s for s in covered if s in parsed["sids"]]
        if not mine and not records:
            raise DeliverError([f"the landed work since {since_why} ({commits} commit(s)) carries none of {rel}'s applied "
                                f"sessions ({', '.join(folder_sids)}); its sessions are not on the workbench branch's "
                                "history since the base"])
        # Work another folder already delivered (its record's sessions name
        # a session the range carries) is on the audience under its own
        # review: a squash that carries it again delivers it twice, refused
        # by name unless the base already holds it, by history or (0.40.0)
        # by content. A record on the branch this delivery continues on is
        # that branch's own history.
        twice, held, held_told = [], set(), []
        for where_, day_, rec in elsewhere:
            if continuing and rec["branch"] == branch:
                continue
            carried = [s for s in covered if s in rec["sessions"]]
            if not carried:
                continue
            how, why = base_holds(repo, rec, where)
            if how:
                # 0.40.0: the base holds that delivery, so the squash adds
                # nothing of those sessions: they ride in nothing here, are
                # not asked for with --others-too and are not named as
                # delivered again.
                held.update(carried)
                who = folder_label(office_root, where_)
                held_told.append(f"{who}'s session{'s' if len(carried) > 1 else ''} {', '.join(carried)} "
                                 f"{'are' if len(carried) > 1 else 'is'} on {audience}/{base} already ({how}: "
                                 f"{who}'s delivery {rec['delivery'][:7]}) and ride{'' if len(carried) > 1 else 's'} "
                                 "in nothing here")
            else:
                twice.append((where_, day_, rec, carried, why))
        if twice:
            gone = [b for b in dict.fromkeys(t[2]["branch"] for t in twice)
                    if g(repo, "ls-remote", "--exit-code", "--heads", where, f"refs/heads/{b}", check=False,
                         timeout=ohost.TRANSFER_TIMEOUT).returncode == 2]
            raise DeliverError(twice_lines(folder, base, branch, continuing, since_why, twice, gone,
                                           labels={t[0]: folder_label(office_root, t[0]) for t in twice}))
        mine = [s for s in mine if s not in held]
        others = {}
        for s in covered:
            if s in parsed["sids"] or s in held:
                continue
            others[s] = [f for f in naming.get(s, []) if f != rel] or ["no folder"]
        # 7. The worktree at the audience's tip, the landed work squashed
        # on, less what bale's own commits in the range changed (0.36.0):
        # those are undone on the workbench's tip first, in temporary
        # commits made in the worktree and never pushed, and the squash
        # takes the result. A commit of bale's own that cannot be undone
        # refuses the delivery by name (take_out_own).
        start = REF_BRANCH if continuing else REF_BASE
        start_sha = g(repo, "rev-parse", start).stdout.strip()
        wt_root = pathlib.Path(tempfile.mkdtemp(prefix="office-deliver-wt-")) if not place.hosted else pathlib.Path(temp_dir)
        worktree = wt_root / "worktree"
        g(repo, "worktree", "add", "-q", "--detach", str(worktree), start)
        own = own_commits(consumption, repo, range_spec)
        squashed, taken = REF_WORKBENCH, []
        if own:
            log(f"taking what {len(own)} commit(s) of bale's own changed out of the delivery: "
                + "; ".join(f"{sha[:12]} {subject}" for sha, subject in own))
            g(worktree, "checkout", "-q", "--detach", REF_WORKBENCH)
            squashed, taken = take_out_own(worktree, own, author)
            g(worktree, "checkout", "-q", "--detach", start_sha)
        if continuing and since:
            # 0.40.0: a delivery onto a branch takes the range's net change
            # alone (since..the cleaned tip, bale's paths out of both ends),
            # as one temporary commit cherry-picked onto the branch's tip with
            # git's three-way fallback, so only what is new since the last
            # delivery there leaves; squashing from where the workbench and
            # the branch parted made a second delivery that edits a line the
            # first delivered conflict with nothing moved on the audience.
            # A conflict sends a merge session for the branch's tip.
            _, top = range_commit(worktree, since, squashed, author)
            merged = g(worktree, "cherry-pick", "--no-commit", top, check=False, timeout=ohost.TRANSFER_TIMEOUT,
                       env=identity_of(author)[1])
            if merged.returncode != 0:
                conflicts = unmerged(worktree)
                g(worktree, "cherry-pick", "--abort", check=False)
                if not conflicts:
                    raise DeliverError([f"the landed work since {since_why} could not be applied onto {audience}'s "
                                        f"{branch}: {ohost._last_words(merged.stderr)}; nothing was pushed",
                                        f"office deliver {folder} tries again"])
                # What bringing the branch's tip into the workbench conflicts
                # in, beside what the squash did: the files the merge session
                # resolves, so the merge office land makes is the one that
                # conflicts nowhere else.
                g(worktree, "reset", "-q", "--hard", start_sha, check=False)
                trial = g(worktree, "merge", "-q", "--no-ff", "--no-commit", workbench, check=False,
                          timeout=ohost.TRANSFER_TIMEOUT, env=identity_of(author)[1])
                if trial.returncode != 0:
                    conflicts = sorted(set(conflicts) | set(unmerged(worktree)))
                g(worktree, "merge", "--abort", check=False)
                conflicts = [c for c in conflicts if not any(c == n or c.startswith(n + "/") for n in NEVER_DELIVERED)]
                lines = [f"the landed work since {since_why} does not go onto {audience}'s {branch} as it is now: "
                         f"{branch} moved on the audience since, and the squash conflicts in "
                         f"{', '.join(conflicts[:12]) or 'files git did not name'}; nothing is left half-done"]
                if not conflicts:
                    raise DeliverError(lines + [f"office deliver {folder} tries again"])
                raise DeliverError(lines + merge_job_lines(
                    office_root, rel, folder, name, repo, "branch", audience, branch, start_sha, workbench,
                    conflicts, day=on, log_from=g(repo, "rev-parse", REF_BASE).stdout.strip()))
            g(worktree, "cherry-pick", "--quit", check=False)
        else:
            merged = g(worktree, "merge", "--squash", "--no-commit", squashed, check=False,
                       timeout=ohost.TRANSFER_TIMEOUT)
            if merged.returncode != 0:
                # From the base: merge_base_in did not bring the base in (a
                # dirty clone, an open session, a view behind; view_told says
                # which), so the squash ran from where the two parted. What
                # kept the base out is said, then the office line that brings
                # it in, and sends a merge session if that merge conflicts.
                conflicts = unmerged(worktree)
                raise DeliverError([f"the landed work does not go onto {audience}'s {base} as it is now: "
                                    + (f"conflicts in {', '.join(conflicts[:12])}" if conflicts
                                       else ohost._last_words(merged.stderr)) + "; nothing was pushed",
                                    *view_told,
                                    f"office deliver {folder} brings {audience}/{base} into the workbench first once "
                                    f"nothing stops that merge (office projects refresh {name} when the clone's view "
                                    "of it is behind), and sends a merge session when the merge conflicts"])
        g(worktree, "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", *NEVER_DELIVERED)
        if g(worktree, "diff", "--cached", "--quiet", check=False).returncode == 0:
            raise DeliverError([f"nothing new to deliver: the landed work makes no change on {audience}'s "
                                f"{branch if continuing else base}"])
        stat = g(worktree, "diff", "--cached", "--stat=100").stdout.rstrip().splitlines()
        shown_stat = stat if len(stat) <= STAT_LINES else stat[:STAT_LINES - 1] + [f"  ... {len(stat) - STAT_LINES + 1} more line(s)", stat[-1]]
        # 8. The letterhead check: the lines the staged squash adds against
        # the delivery's start (git diff --cached; the gaps of 2026-10-28,
        # A2), never the files it touches whole: a line a file already had
        # is told, one line per file, and never refuses. The words are read
        # with the cleanup list too (C2), the lines of the repository's
        # pull-request template as the audience holds it (at the delivery's
        # start) aside from the phrasing rule and the three characters
        # (0.26.0). The words are what of
        # delivery.md leaves (0.35.0, delivery_words): the page's heading
        # and office land's filing note stay in the office, so a page
        # office land filed is never refused for a line of its own. The
        # files taken out of the index above are still on the worktree's
        # disk, so they are named never read (0.36.0): a bale path is one
        # of the letterhead's marks now, and bale.toml names its own.
        try:
            rules = office_rules(office_root)
            words_text, unread = delivery_words(delivery_md)
            hits, told = olh.check(str(worktree), rules, words_text=[words_text], never=NEVER_DELIVERED,
                                   template_rev=start_sha, added=True, added_base=start_sha)
        except (olh.CheckError, OSError) as exc:
            raise DeliverError([f"the letterhead check could not run: {exc}"])
        if unread:
            told.insert(0, unread_line(f"{rel}/delivery.md", unread))
        out = {
            "folder": rel, "folder_name": folder, "title": title, "project": name, "audience": audience, "url": url,
            "author": author, "base": base, "branch": branch, "continuing": continuing, "adopting": adopting,
            # Additive (the gaps of 2026-10-28): which rule chose the branch
            # (flag, words, clone or slug) and why, in one sentence, and the
            # other folder whose branch this delivery continues on, if any.
            "branch_why": branch_why, "branch_rule": branch_rule,
            "joined": {"folder": joined[-1][0], "day": joined[-1][1]} if joined else None,
            "place": {"path": place.path, "host": place.host, "shell": place.shell, "connect": place.connect, "name": name}
            if place.hosted else None,
            "repo": str(repo), "temp_dir": temp_dir, "wt_root": str(wt_root), "worktree": str(worktree),
            "workbench": workbench, "since": since, "since_why": since_why, "commits": int(commits or 0),
            "sessions": mine, "others": others, "folder_sessions": folder_sids, "words": words,
            "others_lines": [f"{s} ({', '.join(f)})" for s, f in others.items()],
            "own": taken, "own_lines": own_lines(taken),
            "stat": shown_stat, "hits": olh.render(hits), "check_told": told, "guard": guard_lines,
            "delivery_md": str(delivery_md), "office_root": str(office_root), "start": start_sha,
            "author_told": author_told, "commits_shown": [],
            # Additive (0.39.0): the clone's view of the audience, said and
            # refreshed, and the clean merge of the base into the workbench.
            "view_told": view_told, "merged": base_merge,
            # Additive (0.40.0): the sessions another folder delivered that
            # the base holds, by history or by content, one line per record:
            # they ride in nothing here.
            "held_told": held_told,
            # Additive (0.41.0): those sessions by id, for the folder's close
            # at delivery (a session the base holds is delivered).
            "held_sessions": sorted(held),
            "commits_line": commits_line(len(words["commits"])) or "",
            # Additive (0.42.0): the open pull request on the branch this
            # delivery is added to ({number, url, base}, read through gh),
            # or None; and the line saying why it was not read.
            "review_pr": review_pr, "review_pr_told": review_pr_told,
        }
        if hits:
            # Nothing with a hit leaves: the worktree goes, the hits stay
            # in the plan for bin/office to print.
            abandon(out)
            out["abandoned"] = True
            return out
        if others and not others_ok and not interactive:
            abandon(out)
            raise DeliverError(["the landed work carries sessions of other folders, which ride in the same delivery "
                                "(the office does not split one branch's history by folder): "
                                + "; ".join(f"{s} ({', '.join(f)})" for s, f in others.items()),
                                f"office deliver {folder} --others-too delivers them with it; piped input is never asked"])
        # 9. The commits, made now, so the question shows each one whole
        # as it will be pushed, with the letterhead's verdict on it (a
        # hook in the clone that changed a message is seen here).
        commit_words(worktree, words, author)
        shown, commit_hits = read_commits(worktree, start_sha, rules)
        out["commits_shown"] = shown
        if commit_hits:
            out["hits"] = olh.render(commit_hits)
            abandon(out)
            out["abandoned"] = True
        return out
    except Exception:
        # Whatever stopped the plan, what it made here is removed.
        partial = {"repo": str(repo) if repo else None, "temp_dir": temp_dir,
                   "worktree": str(worktree or ""), "wt_root": str(wt_root or "")}
        abandon(partial, quiet=True)
        raise


def abandon(plan_, quiet=False):
    """Remove what plan() made on this machine: the worktree, the office's
    refs in the repo, the temporary mirror. Never raises."""
    import shutil
    told = []
    repo = plan_.get("repo")
    worktree = plan_.get("worktree")
    try:
        if repo and worktree and pathlib.Path(worktree).exists():
            g(repo, "worktree", "remove", "--force", worktree, check=False)
        if worktree and pathlib.Path(worktree).exists():
            shutil.rmtree(worktree, ignore_errors=True)
        if repo and pathlib.Path(repo).exists():
            g(repo, "worktree", "prune", check=False)
            for ref in OFFICE_REFS:
                g(repo, "update-ref", "-d", ref, check=False)
        for key in ("wt_root", "temp_dir"):
            d = plan_.get(key)
            if d and pathlib.Path(d).name.startswith("office-deliver"):
                shutil.rmtree(d, ignore_errors=True)
                told.append(f"removed {d}")
    except Exception as exc:  # noqa: BLE001 - said, never raised: the delivery is over either way
        if not quiet:
            log(f"warning: what the delivery made could not all be removed: {exc}")
    return told


def commit_dates(count, now=None):
    """The dates a delivery's commits carry, oldest first (0.32.0): the
    first at now, each after it one second later than the one before, so
    several commits read in their order and never as a burst made in one
    second. Each is git's raw form, `@SECONDS +HHMM`, at this machine's
    offset for that instant, as git would have stamped it."""
    import time
    start = int(time.time() if now is None else now)
    out = []
    for n in range(count):
        at = start + n
        offset = time.localtime(at).tm_gmtoff // 60
        sign = "+" if offset >= 0 else "-"
        out.append(f"@{at} {sign}{abs(offset) // 60:02d}{abs(offset) % 60:02d}")
    return out


def commits_line(count):
    """The one line the question says before a delivery of several
    commits (0.32.0); None for one, the usual shape."""
    if count <= 1:
        return None
    return (f"{count} commits leave in this delivery, dated a second apart, oldest first; one commit per delivery is "
            "the usual shape (one Commit section in delivery.md)")


def commit_words(worktree, words, author, now=None):
    """The delivery's commit(s) in the worktree, from the words: one per
    Commit section, each but the last taking the paths it names, dated by
    commit_dates (author and committer date alike). Returns the commits'
    shas, oldest first."""
    import tempfile
    # Both halves of the identity, and over any GIT_AUTHOR_* in the
    # environment: the audience sees the author, and nobody else.
    cfg, identity = identity_of(author)
    dates = commit_dates(len(words["commits"]), now)
    shas = []
    for n, c in enumerate(words["commits"]):
        message = c["subject"] + ("\n\n" + c["body"] if c["body"] else "") + "\n"
        with tempfile.NamedTemporaryFile("w", prefix="office-deliver-msg-", suffix=".txt", delete=False, encoding="utf-8") as fh:
            fh.write(message)
            msg = fh.name
        try:
            argv = [*cfg, "commit", "-q", "-F", msg]
            if c["paths"]:
                argv += ["--", *c["paths"]]
            run = g(worktree, *argv, check=False,
                    env=dict(identity, GIT_AUTHOR_DATE=dates[n], GIT_COMMITTER_DATE=dates[n]))
            if run.returncode != 0:
                raise DeliverError([f"commit {n + 1} of {len(words['commits'])} ({c['subject']!r}) could not be made: "
                                    f"{ohost._last_words(run.stderr)}"
                                    + (f"; its paths: {', '.join(c['paths'])}" if c["paths"] else "")])
        finally:
            os.unlink(msg)
        shas.append(g(worktree, "rev-parse", "HEAD").stdout.strip())
    if g(worktree, "diff", "--cached", "--quiet", check=False).returncode != 0:
        raise DeliverError(["the Commit sections' paths left changes uncommitted, which cannot be: the last section "
                            "takes the rest, so this is a defect in office deliver; the delivery was not pushed"])
    return shas


def read_commits(worktree, start, rules):
    """Each commit since start in the worktree, oldest first, as the
    question shows it: sha, subject, body, author, committer, their dates
    (0.32.0; git's strict ISO form), the files it touches (status and path)
    and the letterhead's verdict on it (its message, and the lines it adds
    to the files it changed, at its version: never a file whole). Returns
    (shown, hits across them)."""
    import office_letterhead as olh
    log_ = g(worktree, "log", "--reverse", "--format=%H%x00%an <%ae>%x00%cn <%ce>%x00%aI%x00%cI%x00%B%x1e",
             f"{start}..HEAD").stdout
    shown, all_hits = [], []
    for rec in log_.split("\x1e"):
        if not rec.strip():
            continue
        sha, author, committer, dated, committed, message = rec.lstrip("\n").split("\0", 5)
        subject, _, body = message.strip("\n").partition("\n")
        files = g(worktree, "diff-tree", "--root", "-r", "--no-commit-id", "--name-status", "-M", sha).stdout.splitlines()
        try:
            hits, _ = olh.check(str(worktree), rules, range_spec=f"{sha}^..{sha}", added=True)
        except olh.CheckError as exc:
            raise DeliverError([f"the letterhead check could not run on commit {sha[:12]}: {exc}"])
        all_hits += hits
        shown.append({"sha": sha, "subject": subject, "body": body.strip("\n"), "author": author,
                      "committer": committer, "date": dated, "committed": committed,
                      "files": [f.replace("\t", " ", 1).replace("\t", " -> ") for f in files],
                      "verdict": "clean" if not hits else olh.render(hits)})
    return shown, all_hits


def check_identities(worktree, start, author):
    """Every commit since start carries the declared author as both its
    author and its committer; a refusal names each one that does not."""
    want = oh.check_author(author)
    wrong = []
    out = g(worktree, "log", "--format=%H%x00%an <%ae>%x00%cn <%ce>", f"{start}..HEAD").stdout
    for line in out.splitlines():
        sha, a, c = line.split("\0")
        for role, who in (("author", a), ("committer", c)):
            if who != want:
                wrong.append(f"commit {sha[:12]}'s {role} is {who}, not {want}")
    if wrong:
        raise DeliverError(wrong + ["nothing was pushed: every commit office deliver pushes carries the project's "
                                    "declared author as both author and committer"])


def run(office_root, plan_, day):
    """Check the commits plan() made, push, record. Returns (words, told,
    next lines, the review's offer: what bin/office does about the review,
    0.42.0)."""
    worktree, repo = plan_["worktree"], plan_["repo"]
    hosted = plan_.get("place") is not None
    if not pathlib.Path(worktree).is_dir():
        raise DeliverError([f"the delivery's worktree is gone ({worktree}); plan it again: office deliver {plan_['folder_name']}"])
    try:
        shown = plan_.get("commits_shown") or []
        head = g(worktree, "rev-parse", "HEAD").stdout.strip()
        if not shown or shown[-1]["sha"] != head:
            raise DeliverError([f"the delivery's worktree is not at the commits shown ({head[:12]}); nothing was "
                                f"pushed: plan it again, office deliver {plan_['folder_name']}"])
        check_identities(worktree, plan_["start"], plan_["author"])
        shas = [c["sha"] for c in shown]
        g(repo, "update-ref", REF_DELIVERY, shas[-1])
        where = plan_["url"] if hosted else plan_["audience"]
        env = {ohost.DELIVERY_ENV: plan_["branch"]}
        log(f"pushing {plan_['branch']} to {plan_['audience']} ({plan_['url']}): {len(shas)} commit(s), from this machine")
        pushed = g(repo, "push", "-q", "--no-follow-tags", where, f"{REF_DELIVERY}:refs/heads/{plan_['branch']}",
                   check=False, timeout=ohost.TRANSFER_TIMEOUT, env=env)
        if pushed.returncode != 0:
            raise DeliverError([f"the push to {plan_['audience']} was refused (git push exit {pushed.returncode}): "
                                f"{ohost._last_words(pushed.stderr)}; nothing changed on the audience",
                                f"the delivery commit is kept nowhere: deliver again once the cause is fixed "
                                "(a branch that moved on the audience since the fetch is the usual one)"])
    finally:
        abandon(plan_)
    told = list(plan_.get("guard") or []) + list(plan_.get("author_told") or [])
    md = pathlib.Path(office_root) / plan_["folder"] / "folder.md"
    adopting = bool(plan_.get("adopting"))
    text = oh.delivered_text(plan_["branch"], plan_["audience"], plan_["project"], plan_["sessions"] + sorted(plan_["others"]),
                             plan_["workbench"][:12], shas[-1][:12], adopted=adopting)
    recorded = False
    try:
        _, wrote = oh.folder_event(md, day, "delivered", text)
        if wrote:
            ob.git(office_root, "add", "--", f"{plan_['folder']}/folder.md")
            ob.git(office_root, "commit", "-q", "-m", f"office deliver: {plan_['branch']} to {plan_['audience']} for "
                   f"{plan_['folder_name']}", "--", f"{plan_['folder']}/folder.md")
            told.append(f"{plan_['folder']}/folder.md: History: {day} delivered: {text}")
            recorded = True
        else:
            told.append(f"{plan_['folder']}/folder.md has no History section, so the delivery is not recorded there")
    except (OSError, oh.HelperError, ob.LandError) as exc:
        told.append(f"{plan_['folder']}/folder.md: the delivery could not be recorded ({exc}); the branch is on the audience")
    review = plan_["words"]["review"]
    joined = plan_.get("joined")
    nxt = []
    # 0.42.0: what deliver does about the review once the branch is there.
    # A branch with a review already open (joined, adopted, or one this
    # folder continues whose pull request gh read) opens nothing and names
    # the review that carries it; a fresh branch gets an offer: gh opens the
    # review on the occupant's yes (bin/office shows it and asks once), and
    # without gh, signed out, on no, or on a host gh does not reach, the
    # review's body goes to the clipboard and its title and URL are printed,
    # so the hand step is one paste. offer is that block, for bin/office.
    offer = {"offer": False, "why": None, "folder": plan_["folder"], "project": plan_["project"],
             "audience": plan_["audience"], "head": plan_["branch"], "base": plan_["base"],
             "title": review["title"], "body": review["body"] or "", "carried_by": None}
    pr = plan_.get("review_pr")
    if joined and not adopting:
        # Another folder of this office delivered to the branch, so its
        # review is open there already: this delivery is added to it.
        url = (pr or {}).get("url") or branch_url(plan_["url"], plan_["branch"])
        said = (f"{joined['folder']} delivered to {plan_['branch']} on {joined['day']}, so the review open there "
                "carries this delivery too, and the words in delivery.md's Review section are what to reply with")
        if pr:
            nxt.append(f"the review that carries it: #{pr['number']} {pr['url']}")
            offer["carried_by"] = pr
        else:
            nxt.append(f"open the review: {url}" if url else
                       f"open the review already open on the audience's git host ({plan_['url']}) for the branch "
                       f"{plan_['branch']}")
        nxt.append(f"({said})")
    elif adopting:
        # The review is the one already open on the branch (made outside
        # the office): this delivery is added to it, and the review's words
        # are the reply, not a new review's form.
        url = branch_url(plan_["url"], plan_["branch"])
        if pr:
            nxt.append(f"the review that carries it: #{pr['number']} {pr['url']}")
            nxt.append(f"(this delivery is added to {plan_['branch']}, so that review carries it, and the words in "
                       "delivery.md's Review section are what to reply with)")
            offer["carried_by"] = pr
        elif url:
            nxt.append(f"open the review: {url}")
            nxt.append(f"(the reviews whose branch is {plan_['branch']}; this delivery is added to that branch, so the "
                       "review already open there carries it, and the words in delivery.md's Review section are "
                       "what to reply with)")
        else:
            nxt.append(f"open the review already open on the audience's git host ({plan_['url']}) for the branch "
                       f"{plan_['branch']}: this delivery is added to it; reply with the words in delivery.md's "
                       f"Review section: {review['title']}")
    elif pr:
        # A branch of this folder's own whose review is open: it carries the
        # delivery, and nothing is opened again.
        nxt.append(f"the review that carries it: #{pr['number']} {pr['url']}")
        nxt.append(f"(this delivery is added to {plan_['branch']}, so that review carries it, and the words in "
                   "delivery.md's Review section are what to reply with)")
        offer["carried_by"] = pr
    else:
        import office_review as orev
        made = orev.review_offer(plan_["url"], plan_["branch"], plan_["base"], review["title"], review["body"],
                                 plan_["words"].get("to"))
        offer.update({k: v for k, v in made.items() if k not in ("title", "body", "head", "base")})
        url = review_url(plan_["url"], plan_["branch"], plan_["base"], review["title"], review["body"])
        offer["compare_url"] = url
        if url:
            nxt.append(f"open the review: {url}")
            nxt.append(f"the review's title: {review['title']}")
        else:
            nxt.append(f"open the review on the audience's git host ({plan_['url']}): the branch is {plan_['branch']}, "
                       f"onto {plan_['base']}; the review's title: {review['title']}")
    if plan_["words"].get("to"):
        nxt.append(f"send it to: {plan_['words']['to']}")
    how = (" (added to the branch, adopted: it was made outside the office)" if adopting
           else f" (added to the branch {joined['folder']} delivered to)" if joined
           else " (added to the branch)" if plan_["continuing"] else "")
    words = (f"Delivered: {plan_['branch']} is on {plan_['audience']} for {plan_['project']}, {len(shas)} commit(s) by "
             f"{plan_['author']} onto {plan_['base']}" + how
             + f", covering {', '.join(plan_['sessions'] + sorted(plan_['others'])) or 'no session by name'}; "
             f"the workbench branch was not pushed." + ("" if recorded else " The folder does not record it."))
    return words, told, nxt, offer


def still_to_deliver(office_root, plan_):
    """The folder's applied sessions (plan's folder_sessions: its Sessions
    lines whose session is applied in the project) that are still to
    deliver after this delivery (0.41.0): every session no folder's
    `delivered` line names for the project (this delivery's line included,
    and another folder's, as delivered_by_project reads them, so a session
    another folder delivered with --others-too is delivered here too) and
    the base does not hold (plan's held_sessions). [] means the folder's
    work is delivered, and office deliver closes it."""
    import office_bale as ob_
    done = ob_.delivered_by_project(oh.read_folders(office_root)).get(plan_["project"], set())
    done |= set(plan_.get("sessions") or []) | set(plan_.get("others") or {})
    held = set(plan_.get("held_sessions") or [])
    return [s for s in plan_.get("folder_sessions") or [] if s not in done and s not in held]


# --- office letterhead check --on PROJECT: the check in a project's repo, here or there ------

# The letterhead check on this machine runs office_letterhead as a module,
# the way bin/office's pylib runs every helper (0.31.0), not as a script: a
# script's own code is compiled from its source on every run and never read
# from a cache, so `python3 -B lib/office_letterhead.py` compiled its 540
# lines on every check, where a module run through runpy reads the compiled
# code install.sh wrote into lib/__pycache__. -B still writes nothing; -P
# keeps the current directory (the project's tree here) off sys.path, as a
# script's run kept it off, and -S starts without site, as pylib does; the
# module runs as __main__, so its last line calls main as it did. A hosted
# project's check is unchanged: the module travels as the program python3
# reads from stdin.
PYLIB_PROGRAM = ('import runpy, sys; sys.path.insert(0, sys.argv.pop(1)); '
                 'runpy.run_module(sys.argv.pop(1), run_name="__main__", alter_sys=True)')


def letterhead_argv(install, args):
    """The argv that runs the letterhead check with args from the install's
    lib/, as pylib runs a helper (PYLIB_PROGRAM)."""
    return [sys.executable, "-B", "-P", "-S", "-c", PYLIB_PROGRAM, str(pathlib.Path(install) / "lib"),
            "office_letterhead", *args]


def check_in_project(office_root, project, scope_all=False, range_spec=None, words=(), files_only=False,
                     never=(), words_text=(), template_rev=None, added=False):
    """Run the letterhead check in a project's repo where it is. On a
    host the module travels as the program python3 reads from stdin and
    the rules as one JSON argument, through the project's shell, writing
    nothing there; the hits come back on stdout. words_text, (label,
    text) pairs, travel as one argument too, so words reach a host. added
    reads the lines the range adds, not its files whole (--added), as
    office deliver reads a delivery. Returns (exit code, stdout, stderr)."""
    import json
    import shlex
    import office_letterhead as olh
    office_root = pathlib.Path(office_root).resolve()
    projects = {p["name"]: p for p in ob.office_projects(office_root) or []}
    entry = projects.get(project)
    if entry is None:
        raise DeliverError([f"no project named {project} in this office's [projects] (it lists: "
                            f"{', '.join(sorted(projects)) or 'none'})"])
    if entry["problem"]:
        raise DeliverError([f"{project}: {entry['problem']}"])
    place = ohost.place_of(entry)
    try:
        rules = office_rules(office_root)
    except olh.CheckError as exc:
        raise DeliverError([f"the letterhead check could not run: {exc}"])
    flags = (["--all"] if scope_all else []) + (["--range", range_spec] if range_spec else []) \
        + (["--files-only"] if files_only else []) + [x for n in never for x in ("--never", n)] \
        + (["--words-json", json.dumps([list(w) for w in words_text])] if words_text else []) \
        + (["--template-rev", template_rev] if template_rev else []) + (["--added"] if added else [])
    if not place.hosted:
        argv = letterhead_argv(INSTALL, ["--rules-json", json.dumps(rules), *flags,
                                         *[w for f in words for w in ("--words", str(f))], str(place.path)])
        run = ohost.run_in(ohost.Place(place.path), argv, timeout=ohost.TRANSFER_TIMEOUT)
        return run.returncode, run.stdout, run.stderr
    if words:
        raise DeliverError(["--words names a file on this machine, and --on names a project on a host; check the "
                            "words here (office letterhead check --words FILE) and the tree there (--on PROJECT)"])
    command = (f"cd {ohost.shell_path(place.path)} && PYTHONDONTWRITEBYTECODE=1 python3 - --rules-json "
               f"{shlex.quote(json.dumps(rules))} {' '.join(shlex.quote(f) for f in flags)} .")
    try:
        with open(INSTALL / "lib" / "office_letterhead.py", "rb") as fh:
            rc, out, err = ohost._raw(place, command, stdin=fh)
    except ohost.HostError as exc:
        raise DeliverError([f"{project}: {exc}"])
    return rc, (out or b"").decode("utf-8", "replace"), err


# --- office land's review: what deliver would refuse, said early (0.25.0) ----------------------

REVIEW_SHOWN = 12


def land_review(office_root, project, sid, folder_rel=None):
    """The letterhead's review of what a session landed on a project with
    an audience: the lines its landing added (applied/SID's first parent
    to it, bale's own files aside, never its commit messages, which never
    travel; the files' other lines were there before, and deliver does not
    refuse them either) and the folder's delivery.md words, read as office
    deliver reads them. Lines to say; it refuses nothing, and a review
    that cannot run is a line, never a failed landing. [] for a project
    with no audience."""
    root = pathlib.Path(office_root)
    entry = next((p for p in ob.office_projects(root) or [] if p["name"] == project), None)
    if entry is None or not entry.get("audience") or entry["problem"]:
        return []
    words_text = []
    if folder_rel:
        md = root / folder_rel / oh.PAGE_FILES["delivery"]
        if md.is_file():
            # Read as deliver reads it (0.35.0): what of the page leaves.
            label_text, _ = delivery_words(md, label=f"{folder_rel}/{md.name}")
            words_text.append(label_text)
    template_rev = f"refs/remotes/{entry['audience']}/{entry['base']}" if entry.get("base") \
        else f"refs/remotes/{entry['audience']}/HEAD"
    tag = f"applied/{sid}"
    try:
        rc, out, err = check_in_project(root, project, range_spec=f"{tag}^1..{tag}", files_only=True,
                                        never=NEVER_DELIVERED, words_text=words_text, template_rev=template_rev,
                                        added=True)
    except DeliverError as exc:
        return [f"letterhead: the review of {sid}'s landing could not run: {'; '.join(exc.lines)}"]
    what = "the change it landed" + (" and the delivery words" if words_text else " (no delivery words filed yet)")
    if rc == 0:
        return [f"letterhead: {sid}'s landing is clean for delivery: {what}, as office deliver reads them"]
    if rc != 1:
        last = [l for l in (err or "").splitlines() if l.strip()]
        return [f"letterhead: the review of {sid}'s landing could not run: {last[-1] if last else f'exit {rc}'}"]
    hits = [l for l in out.splitlines() if l.strip()]
    lines = [f"letterhead: office deliver would refuse {len(hits)} line(s) of {sid}'s landing ({what}); nothing is "
             f"refused at land, and a fix can ride the next session on {project}:"]
    lines += [f"  {h}" for h in hits[:REVIEW_SHOWN]]
    if len(hits) > REVIEW_SHOWN:
        lines.append(f"  ... and {len(hits) - REVIEW_SHOWN} more: office letterhead check --on {project} --range "
                     f"{tag}^1..{tag} shows them all")
    return lines


# --- command line ------------------------------------------------------------------------------

def main(argv=None):
    import json
    ap = argparse.ArgumentParser(prog="office_deliver.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan", help="everything up to the question; the plan as JSON into --plan")
    p.add_argument("office"); p.add_argument("folder", help="the folder's directory name")
    p.add_argument("--plan", required=True); p.add_argument("--branch"); p.add_argument("--on", dest="project")
    p.add_argument("--others-too", action="store_true", help="deliver other folders' sessions riding in the work")
    p.add_argument("--adopt", action="store_true",
                   help="add the delivery to a branch the audience has that this folder's records do not cover "
                        "(made outside the office)")
    p.add_argument("--author", help="the project's author, declared and kept, as office projects set --author does")
    p.add_argument("--interactive", action="store_true",
                   help="bin/office asks about other folders' sessions: keep the worktree and report them")
    p.add_argument("--refresh", dest="refresh", action="store_true", default=None,
                   help="refresh the clone's view of the audience when it is behind (0.39.0)")
    p.add_argument("--no-refresh", dest="refresh", action="store_false",
                   help="do not refresh it; say it is behind and go on")
    p.add_argument("--day", help="the office's date, for the History line of a clean merge")
    p = sub.add_parser("run", help="commit, push and record, from a plan")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--day", required=True)
    p = sub.add_parser("abandon", help="remove what a plan made")
    p.add_argument("office"); p.add_argument("--plan", required=True)
    p = sub.add_parser("check", help="office letterhead check --on PROJECT: the check in the project's repo, here or there")
    p.add_argument("office"); p.add_argument("--project", required=True); p.add_argument("--all", action="store_true")
    p.add_argument("--range", dest="range_spec"); p.add_argument("--words", action="append", default=[])
    # 0.40.0: the lines a diff adds, as deliver reads a delivery, in the
    # project's repo too (check_in_project took it since 0.38.0; the
    # subcommand did not, so bin/office refused the pair).
    p.add_argument("--added", action="store_true", help="the lines the range (or the index) adds, not its files whole")
    p.add_argument("--words-json", help="[[label, text], ...]: words that travel as one argument (--delivery's)")
    p = sub.add_parser("delivery-words", help="office letterhead check --delivery: each delivery.md as deliver reads "
                                              "it, as one JSON [[label, text], ...] on stdout (0.42.0)")
    p.add_argument("pages", nargs="+")
    p = sub.add_parser("declare-author", help="declare a project's author and commit the floor plan")
    p.add_argument("office"); p.add_argument("--project", required=True); p.add_argument("--author", required=True)
    p = sub.add_parser("status-lines", help="office status's letterhead and push-guard lines")
    p.add_argument("office")
    p = sub.add_parser("upgrade", help="what office upgrade brings with no migration: the letterhead's pages and "
                                       "the push guards")
    p.add_argument("office")
    p = sub.add_parser("arrive", help="make the letterhead arrive, or finish arriving; the changed paths on stdout")
    p.add_argument("office")
    p = sub.add_parser("guard", help="install or refresh one project's push guard where it is missing or older")
    p.add_argument("office"); p.add_argument("--project", required=True)
    p = sub.add_parser("land-review", help="office land's letterhead review of a landed session")
    p.add_argument("office"); p.add_argument("--project", required=True); p.add_argument("--sid", required=True)
    p.add_argument("--folder")
    p.add_argument("--out", help="also write the review's lines to this file, one per line (0.41.0)")
    p = sub.add_parser("review-url", help="the review's URL for a remote's URL, a branch and a base, or nothing")
    p.add_argument("url"); p.add_argument("branch"); p.add_argument("base")
    # The merge session (0.40.0).
    p = sub.add_parser("merge-start", help="office start N --merge: the folder's merge job as tab-separated lines "
                                           "(project, goal, write, say), its brief written to --brief-out")
    p.add_argument("office"); p.add_argument("folder"); p.add_argument("--brief-out", required=True)
    p = sub.add_parser("merge-sent", help="name the session office start --merge sent on the folder's merge job")
    p.add_argument("office"); p.add_argument("folder", help="space/name"); p.add_argument("--sid", required=True)
    p = sub.add_parser("land-merge", help="office land: a landed merge session's resolution made the merge commit; "
                                          "prints `merge` on stdout when the session was one")
    p.add_argument("office"); p.add_argument("--project", required=True); p.add_argument("--sid", required=True)
    p.add_argument("--folder", required=True); p.add_argument("--day", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "merge-start":
            got = merge_start(a.office, a.folder, a.brief_out)
            print(f"project\t{got['project']}")
            print(f"goal\t{got['goal']}")
            for w in got["writes"]:
                print(f"write\t{w}")
            for line in got["said"]:
                print(f"say\t{line}")
            return 0
        if a.cmd == "merge-sent":
            log(merge_sent(a.office, a.folder, a.sid))
            return 0
        if a.cmd == "land-merge":
            was, lines = land_merge(a.office, a.project, a.sid, a.folder, a.day)
            for line in lines:
                log(line)
            if was:
                print("merge")
            return 0
        if a.cmd == "review-url":
            url = review_url(a.url, a.branch, a.base)
            print(url or "")
            return 0
        if a.cmd == "delivery-words":
            pairs = []
            for page in a.pages:
                (label, text), unread = delivery_words(page)
                if unread:
                    log(unread_line(label, unread))
                pairs.append([label, text])
            print(json.dumps(pairs))
            return 0
        if a.cmd == "check":
            words_text = [(str(l), str(x)) for l, x in json.loads(a.words_json)] if a.words_json else ()
            rc, out, err = check_in_project(a.office, a.project, a.all, a.range_spec, a.words, words_text=words_text,
                                            added=a.added)
            sys.stdout.write(out)
            sys.stderr.write(err)
            return rc
        if a.cmd == "declare-author":
            log(declare_author(a.office, a.project, a.author))
            return 0
        if a.cmd == "status-lines":
            for line in status_lines(a.office):
                print(line)
            return 0
        if a.cmd == "upgrade":
            changed, lines = upgrade_additive(a.office)
            for line in lines:
                log(line)
            for path in changed:
                print(path)
            return 0
        if a.cmd == "arrive":
            changed, lines = letterhead_arrive(a.office)
            for line in lines:
                log(line)
            for path in changed:
                print(path)
            return 0
        if a.cmd == "guard":
            entry = next((p for p in audience_projects(a.office) if p["name"] == a.project), None)
            if entry is None:
                log(f"{a.project} declares no audience, so it has no push guard")
                return 0
            _, line = refresh_guard(entry)
            log(line)
            return 0
        if a.cmd == "land-review":
            lines = land_review(a.office, a.project, a.sid, a.folder)
            for line in lines:
                log(line)
            if a.out:
                # 0.41.0: the same lines, for the office's tail on the
                # planner's relay block (bin/office carry_relays).
                pathlib.Path(a.out).write_text("".join(l + "\n" for l in lines), encoding="utf-8")
            return 0
        if a.cmd == "plan":
            try:
                out = plan(ob.Consumption(), a.office, a.folder, a.branch, a.project, a.others_too, a.interactive,
                           a.author, a.adopt, a.refresh, a.day)
            except NeedsRefresh as exc:
                if not a.interactive:
                    raise
                # On a terminal bin/office says the line, asks once, and plans
                # again with --refresh or --no-refresh.
                pathlib.Path(a.plan).write_text(json.dumps({"need_refresh": exc.project, "behind": exc.lines[0]}),
                                                encoding="utf-8")
                return 5
            except NeedsAuthor as exc:
                if not a.interactive:
                    raise
                # On a terminal bin/office asks the one question and plans again.
                pathlib.Path(a.plan).write_text(json.dumps({"need_author": exc.project,
                                                            "clone_identity": exc.clone_identity}), encoding="utf-8")
                return 4
            pathlib.Path(a.plan).write_text(json.dumps(out), encoding="utf-8")
            if out.get("abandoned"):
                # A flag that set the author set it whatever comes next: said.
                for line in out.get("author_told") or []:
                    log(line)
                for line in out["hits"]:
                    print(line)
                log(f"error: the letterhead refuses {len(out['hits'])} line(s) (above); nothing was pushed, and the "
                    "delivery was not made: fix the lines in the project (or the words in "
                    f"{out['delivery_md']}) and deliver again")
                return 1
            return 0
        plan_ = json.loads(pathlib.Path(a.plan).read_text(encoding="utf-8"))
        if a.cmd == "abandon":
            for line in abandon(plan_):
                debug(line)
            log("nothing was pushed, and nothing the delivery made is left")
            return 0
        words, told, nxt, offer = run(a.office, plan_, a.day)
        try:
            pending = still_to_deliver(a.office, plan_)
        except (OSError, oh.HelperError) as exc:
            # Never fails the delivery: the folder stays where it is.
            log(f"whether {plan_['folder']}'s work is all delivered could not be read ({exc}); it stays where it is")
            pending = None
        print(json.dumps({"words": words, "told": told, "next": nxt, "folder": plan_["folder"],
                          "pending": pending, "review": offer}))
        return 0
    except ob.StartError as exc:
        for line in exc.lines:
            log(f"error: {line}")
        return 1
    except (oh.HelperError, ob.BaleError, ohost.HostError, OSError, ValueError) as exc:
        log(f"error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
