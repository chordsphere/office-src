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
  refs.
- In a temporary worktree at the audience's tip, the landed work is
  squashed on (git merge --squash), bale's files are taken out of the
  index, the diff and the folder's delivery words go through the
  letterhead check, and the words become one commit (several when
  delivery.md marks them) authored as the project's `author`.
- That commit alone is pushed, as refs/heads/BRANCH, with the branch
  named in OFFICE_DELIVERY so the push guard in a clone lets it through
  and nothing else. The workbench branch is never pushed.
- The folder gets a dated `delivered` History line naming the branch,
  the sessions covered, the workbench commit and the delivery commit,
  and deliver prints what the occupant does next: the review's URL when
  the git host's compare-URL shape is known, the branch's name otherwise,
  and whom the words name as reviewer.

Two steps, so bin/office can ask once in between: plan() does everything
up to the question (fetch, carry, squash, check) and writes a plan;
run() commits, pushes and records; abandon() removes what plan() made.
Standard library only; every git call shows under OFFICE_DEBUG=1.
"""

import argparse
import json
import os
import pathlib
import re
import shlex
import shutil
import sys
import tempfile
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_host as ohost  # noqa: E402
import office_bale as ob  # noqa: E402
import office_letterhead as olh  # noqa: E402

INSTALL = pathlib.Path(__file__).resolve().parent.parent
RULES = INSTALL / "share" / "letterhead.toml"
FORBIDDEN_REL = "letterhead/forbidden.txt"
# The refs the office owns in a repo it delivers from, deleted when the
# delivery is done or abandoned.
REF_BASE = "refs/office/audience/base"
REF_BRANCH = "refs/office/audience/branch"
REF_WORKBENCH = "refs/office/workbench"
REF_DELIVERY = "refs/office/delivery"
OFFICE_REFS = (REF_BASE, REF_BRANCH, REF_WORKBENCH, REF_DELIVERY)
# What never travels to an audience: the names bale makes in a working
# copy, taken out of the delivery's index whatever the clone tracks.
NEVER_DELIVERED = tuple(x.rstrip("/") for x in ohost.EXCLUDE_LINES)
STAT_LINES = 40
log = ob.log
debug = ob.debug


class DeliverError(ob.StartError):
    """office deliver cannot go on, said as lines a person can act on."""


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


def mirror_here(prefix="office-deliver-"):
    """A temporary bare repo on this machine, the mirror a hosted
    project's delivery is built in."""
    tmp = tempfile.mkdtemp(prefix=prefix)
    repo = pathlib.Path(tmp) / "mirror.git"
    g(tmp, "init", "-q", "--bare", str(repo))
    return tmp, repo


def plan(consumption, office_root, folder, branch=None, project_name=None, others_ok=False, interactive=False):
    """Everything a delivery needs before the one question, written as a
    dict for run(): the project and its audience, author and base; the
    sessions covered and whose folders they belong to; the words; the
    worktree with the squash staged; the diff's stat; the letterhead
    check's hits. Raises DeliverError when it cannot go on, having
    removed what it made."""
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
    # 3. The clone, where it is: the reach, its remotes, identity and guard.
    try:
        facts = ohost.git_facts(place)
    except ohost.HostError as exc:
        raise DeliverError([f"{name}: {exc}"])
    url = facts["remotes"].get(audience)
    if not url:
        raise DeliverError([f"{name}'s clone at {place} has no remote named {audience} (it has: "
                            f"{', '.join(sorted(facts['remotes'])) or 'none'}); office projects set {name} --audience "
                            "REMOTE names the right one"])
    author = entry.get("author")
    if not author:
        if facts.get("name") and facts.get("email"):
            author = oh.check_author(f"{facts['name']} <{facts['email']}>")
        else:
            raise DeliverError([f"{name}'s clone at {place} has no git identity to author the delivery as; office "
                                f"projects set {name} --author 'Name <email>' names the one the audience expects"])
    base = entry.get("base") or facts["remote_heads"].get(audience)
    if not base:
        raise DeliverError([f"{name}'s clone does not say which branch {audience} points at (no {audience}/HEAD), "
                            f"so the base is not known; office projects set {name} --base BRANCH names it"])
    branch = oh.check_base(branch) if branch else branch_from_folder(folder)
    if branch == base:
        raise DeliverError([f"the delivery branch would be {branch}, which is the base itself; name another: --branch NAME"])
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
        on_branch = g(repo, "fetch", "-q", where, f"+refs/heads/{branch}:{REF_BRANCH}", check=False,
                      timeout=ohost.TRANSFER_TIMEOUT).returncode == 0
        continuing = on_branch
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
        if continuing and not any(rec["branch"] == branch for _, rec in records):
            raise DeliverError([f"{audience} already has a branch named {branch}, and {rel} records no delivery on it, "
                                "so it is not this folder's to add to; name another: --branch NAME"])
        since, since_why = None, None
        for _, rec in reversed(records):
            if rec["branch"] == branch and g(repo, "cat-file", "-e", f"{rec['workbench']}^{{commit}}", check=False).returncode == 0 \
                    and g(repo, "merge-base", "--is-ancestor", rec["workbench"], workbench, check=False).returncode == 0:
                since, since_why = rec["workbench"], f"the last delivery on {branch} ({rec['delivery'][:12]})"
                break
        if since is None:
            mb = g(repo, "merge-base", REF_BASE, workbench, check=False)
            since = mb.stdout.strip() if mb.returncode == 0 and mb.stdout.strip() else None
            since_why = f"where the workbench branch and {audience}/{base} parted" if since else "the whole history"
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
        covered = [s for s in found if s in applied]
        mine = [s for s in covered if s in parsed["sids"]]
        others = {}
        for s in covered:
            if s in parsed["sids"]:
                continue
            others[s] = [f for f in naming.get(s, []) if f != rel] or ["no folder"]
        if not mine and not records:
            raise DeliverError([f"the landed work since {since_why} ({commits} commit(s)) carries none of {rel}'s applied "
                                f"sessions ({', '.join(folder_sids)}); its sessions are not on the workbench branch's "
                                "history since the base"])
        # 7. The worktree at the audience's tip, the landed work squashed on.
        start = REF_BRANCH if continuing else REF_BASE
        wt_root = pathlib.Path(tempfile.mkdtemp(prefix="office-deliver-wt-")) if not place.hosted else pathlib.Path(temp_dir)
        worktree = wt_root / "worktree"
        g(repo, "worktree", "add", "-q", "--detach", str(worktree), start)
        merged = g(worktree, "merge", "--squash", "--no-commit", REF_WORKBENCH, check=False, timeout=ohost.TRANSFER_TIMEOUT)
        if merged.returncode != 0:
            conflicts = g(worktree, "diff", "--name-only", "--diff-filter=U", check=False).stdout.split()
            raise DeliverError([f"the landed work does not go onto {audience}'s {branch if continuing else base} as it "
                                f"is now: " + (f"conflicts in {', '.join(conflicts[:12])}" if conflicts
                                               else ohost._last_words(merged.stderr)),
                                f"bring {base} into the workbench branch first (merge or rebase there, then land), "
                                "and deliver again"])
        g(worktree, "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", *NEVER_DELIVERED)
        if g(worktree, "diff", "--cached", "--quiet", check=False).returncode == 0:
            raise DeliverError([f"nothing new to deliver: the landed work makes no change on {audience}'s "
                                f"{branch if continuing else base}"])
        stat = g(worktree, "diff", "--cached", "--stat=100").stdout.rstrip().splitlines()
        shown_stat = stat if len(stat) <= STAT_LINES else stat[:STAT_LINES - 1] + [f"  ... {len(stat) - STAT_LINES + 1} more line(s)", stat[-1]]
        # 8. The letterhead check: the diff as staged, and the words.
        rules = olh.load_rules_toml(RULES)
        forbidden = office_root / FORBIDDEN_REL
        if forbidden.is_file():
            rules["forbidden"] = olh.forbidden_lines(forbidden.read_text(encoding="utf-8", errors="replace"))
        try:
            hits, told = olh.check(str(worktree), rules, words=[str(delivery_md)])
        except olh.CheckError as exc:
            raise DeliverError([f"the letterhead check could not run: {exc}"])
        out = {
            "folder": rel, "folder_name": folder, "title": title, "project": name, "audience": audience, "url": url,
            "author": author, "base": base, "branch": branch, "continuing": continuing,
            "place": {"path": place.path, "host": place.host, "shell": place.shell, "connect": place.connect, "name": name}
            if place.hosted else None,
            "repo": str(repo), "temp_dir": temp_dir, "wt_root": str(wt_root), "worktree": str(worktree),
            "workbench": workbench, "since": since, "since_why": since_why, "commits": int(commits or 0),
            "sessions": mine, "others": others, "folder_sessions": folder_sids, "words": words,
            "others_lines": [f"{s} ({', '.join(f)})" for s, f in others.items()],
            "stat": shown_stat, "hits": olh.render(hits), "check_told": told, "guard": guard_lines,
            "delivery_md": str(delivery_md), "office_root": str(office_root),
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


def commit_words(worktree, words, author):
    """The delivery's commit(s) in the worktree, from the words: one per
    Commit section, each but the last taking the paths it names. Returns
    the commits' shas, oldest first."""
    name, email = oh.split_author(author)
    # Both halves of the identity, and over any GIT_AUTHOR_* in the
    # environment: the audience sees the author, and nobody else.
    cfg = ["-c", f"user.name={name}", "-c", f"user.email={email}"]
    identity = {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email,
                "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email}
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
            run = g(worktree, *argv, check=False, env=identity)
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


def run(office_root, plan_, day):
    """Commit, push, record. Returns (words, told, next lines)."""
    worktree, repo = plan_["worktree"], plan_["repo"]
    hosted = plan_.get("place") is not None
    if not pathlib.Path(worktree).is_dir():
        raise DeliverError([f"the delivery's worktree is gone ({worktree}); plan it again: office deliver {plan_['folder_name']}"])
    try:
        shas = commit_words(worktree, plan_["words"], plan_["author"])
        g(repo, "update-ref", REF_DELIVERY, shas[-1])
        where = plan_["url"] if hosted else plan_["audience"]
        env = {ohost.DELIVERY_ENV: plan_["branch"]}
        log(f"pushing {plan_['branch']} to {plan_['audience']} ({plan_['url']}): {len(shas)} commit(s), from this machine")
        pushed = g(repo, "push", "-q", where, f"{REF_DELIVERY}:refs/heads/{plan_['branch']}", check=False,
                   timeout=ohost.TRANSFER_TIMEOUT, env=env)
        if pushed.returncode != 0:
            raise DeliverError([f"the push to {plan_['audience']} was refused (git push exit {pushed.returncode}): "
                                f"{ohost._last_words(pushed.stderr)}; nothing changed on the audience",
                                f"the delivery commit is kept nowhere: deliver again once the cause is fixed "
                                "(a branch that moved on the audience since the fetch is the usual one)"])
    finally:
        abandon(plan_)
    told = list(plan_.get("guard") or [])
    md = pathlib.Path(office_root) / plan_["folder"] / "folder.md"
    text = oh.delivered_text(plan_["branch"], plan_["audience"], plan_["project"], plan_["sessions"] + sorted(plan_["others"]),
                             plan_["workbench"][:12], shas[-1][:12])
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
    url = review_url(plan_["url"], plan_["branch"], plan_["base"], review["title"], review["body"])
    nxt = []
    if url:
        nxt.append(f"open the review: {url}")
        nxt.append("(the review's title and body ride in that URL; the git host fills its form from them)")
    else:
        nxt.append(f"open the review on the audience's git host ({plan_['url']}): the branch is {plan_['branch']}, "
                   f"onto {plan_['base']}; the review's title: {review['title']}")
    if plan_["words"].get("to"):
        nxt.append(f"send it to: {plan_['words']['to']}")
    words = (f"Delivered: {plan_['branch']} is on {plan_['audience']} for {plan_['project']}, {len(shas)} commit(s) by "
             f"{plan_['author']} onto {plan_['base']}" + (" (added to the branch)" if plan_["continuing"] else "")
             + f", covering {', '.join(plan_['sessions'] + sorted(plan_['others'])) or 'no session by name'}; "
             f"the workbench branch was not pushed." + ("" if recorded else " The folder does not record it."))
    return words, told, nxt


# --- office letterhead check --on PROJECT: the check in a project's repo, here or there ------

def check_in_project(office_root, project, scope_all=False, range_spec=None, words=()):
    """Run the letterhead check in a project's repo where it is. On a
    host the module travels as the program python3 reads from stdin and
    the rules as one JSON argument, through the project's shell, writing
    nothing there; the hits come back on stdout. Returns (exit code,
    stdout, stderr)."""
    office_root = pathlib.Path(office_root).resolve()
    projects = {p["name"]: p for p in ob.office_projects(office_root) or []}
    entry = projects.get(project)
    if entry is None:
        raise DeliverError([f"no project named {project} in this office's [projects] (it lists: "
                            f"{', '.join(sorted(projects)) or 'none'})"])
    if entry["problem"]:
        raise DeliverError([f"{project}: {entry['problem']}"])
    place = ohost.place_of(entry)
    rules = olh.load_rules_toml(RULES)
    forbidden = office_root / FORBIDDEN_REL
    if forbidden.is_file():
        rules["forbidden"] = olh.forbidden_lines(forbidden.read_text(encoding="utf-8", errors="replace"))
    flags = (["--all"] if scope_all else []) + (["--range", range_spec] if range_spec else [])
    if not place.hosted:
        argv = [sys.executable, "-B", str(INSTALL / "lib" / "office_letterhead.py"), "--rules-json", json.dumps(rules),
                *flags, *[w for f in words for w in ("--words", str(f))], place.path]
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


# --- command line ------------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_deliver.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan", help="everything up to the question; the plan as JSON into --plan")
    p.add_argument("office"); p.add_argument("folder", help="the folder's directory name")
    p.add_argument("--plan", required=True); p.add_argument("--branch"); p.add_argument("--on", dest="project")
    p.add_argument("--others-too", action="store_true", help="deliver other folders' sessions riding in the work")
    p.add_argument("--interactive", action="store_true",
                   help="bin/office asks about other folders' sessions: keep the worktree and report them")
    p = sub.add_parser("run", help="commit, push and record, from a plan")
    p.add_argument("office"); p.add_argument("--plan", required=True); p.add_argument("--day", required=True)
    p = sub.add_parser("abandon", help="remove what a plan made")
    p.add_argument("office"); p.add_argument("--plan", required=True)
    p = sub.add_parser("check", help="office letterhead check --on PROJECT: the check in the project's repo, here or there")
    p.add_argument("office"); p.add_argument("--project", required=True); p.add_argument("--all", action="store_true")
    p.add_argument("--range", dest="range_spec"); p.add_argument("--words", action="append", default=[])
    p = sub.add_parser("review-url", help="the review's URL for a remote's URL, a branch and a base, or nothing")
    p.add_argument("url"); p.add_argument("branch"); p.add_argument("base")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "review-url":
            url = review_url(a.url, a.branch, a.base)
            print(url or "")
            return 0
        if a.cmd == "check":
            rc, out, err = check_in_project(a.office, a.project, a.all, a.range_spec, a.words)
            sys.stdout.write(out)
            sys.stderr.write(err)
            return rc
        if a.cmd == "plan":
            out = plan(ob.Consumption(), a.office, a.folder, a.branch, a.project, a.others_too, a.interactive)
            pathlib.Path(a.plan).write_text(json.dumps(out), encoding="utf-8")
            if out.get("abandoned"):
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
        words, told, nxt = run(a.office, plan_, a.day)
        print(json.dumps({"words": words, "told": told, "next": nxt}))
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
