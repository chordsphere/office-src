#!/usr/bin/env python3
"""A clone's view of its audience, refreshed (0.39.0): office projects refresh, and its offers at start and deliver.

A clone on a host often has no credentials for its audience's git host
(a container's clone, say, where only the occupant's machine can reach
it), so its remote-tracking refs stay where they were when the clone was
made, and a session builds on what that clone last saw. office projects refresh NAME brings that view
level, the way --from carries a clone (office_host.clone_to):

- The audience's branches are fetched on this machine, with this
  machine's credentials, into a temporary bare repo (the mirror, as office
  deliver's), always with a forcing refspec, so a branch the audience
  force-pushed moves too (the walkthrough of 2026-10-27, item 21).
- For a clone on a host, its refs are read first (one batch through the
  shell), a bundle of the branches that moved is made in the mirror, thin
  against every commit the clone already names, sent through the shell
  into the office's one temporary directory there, and fetched in the
  clone with `+refs/heads/*:refs/remotes/AUDIENCE/*`; the directory is
  removed in the same connection. A branch whose new tip the clone
  already holds (moved back, say) is set by update-ref there. For a clone
  on this machine it is a plain forced fetch from the audience remote.
- The base branch is then fast-forwarded in the clone: --ff-only when it
  is checked out and its tree is clean (and no bale session is open
  there), update-ref after an ancestry check when another branch is
  checked out. A base with commits of its own is said and left: a refresh
  never merges. A dirty tree stops only that step, said.
- What moved is said, one line per branch, or `nothing moved`. The
  workbench branch is never moved (a base checked out with no commits of
  its own is the one branch a fast-forward moves), no ref is deleted, and
  nothing is pushed.
- The refresh leaves one ref in the clone, refs/office-refresh/AUDIENCE,
  naming a small blob that says when and from where; `office projects`
  reads it from the clone itself (refreshed_line). No file of the
  office's records a refresh, and no folder does.

office start and office deliver offer it (compare_line, behind_words):
the clone's view of AUDIENCE/BASE against the audience's BASE as this
machine sees it. Standard library only; every git call and connection
shows under OFFICE_DEBUG=1.
"""

import argparse
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import office_helper as oh  # noqa: E402
import office_host as ohost  # noqa: E402
import office_bale as ob  # noqa: E402

# The ref a refresh leaves in the clone, per audience: a blob of three
# lines (when, from where, by way of which machine). Outside refs/office/,
# which office deliver owns and empties after every delivery.
STAMP_PREFIX = "refs/office-refresh/"
# The refspec every refresh fetches with, here and in the clone: forcing,
# so a branch the audience rewrote is not left stale.
REFSPEC = "+refs/heads/*:refs/remotes/{audience}/*"
SHORT = 7
log = ob.log
debug = ob.debug


class RefreshError(ob.StartError):
    """A refresh cannot go on, said as lines a person can act on."""


def short(sha):
    return (sha or "")[:SHORT]


def stamp_ref(audience):
    return f"{STAMP_PREFIX}{audience}"


def audience_entry(office_root, name):
    """The [projects] entry for name, refused by name when there is no such
    project, it cannot be read, or it declares no audience."""
    projects = {p["name"]: p for p in ob.office_projects(office_root) or []}
    entry = projects.get(name)
    if entry is None:
        raise RefreshError([f"no project named {name} in this office's [projects] (it lists: "
                            f"{', '.join(sorted(projects)) or 'none'})"])
    if entry["problem"]:
        raise RefreshError([f"{name}: {entry['problem']}"])
    if not entry.get("audience"):
        raise RefreshError([f"{name} declares no audience, so there is no view of one to refresh: office projects "
                            f"set {name} --audience REMOTE names the remote in its clone that points at the "
                            "audience's git host"])
    return entry


def git_here(repo, *args, check=True, timeout=ohost.TRANSFER_TIMEOUT, env=None):
    """git in a repo on this machine, through office_host so the call
    shows under OFFICE_DEBUG=1; a failure is a RefreshError naming it."""
    run = ohost.run_in(ohost.Place(str(repo)), ["git", *args], timeout=timeout, env=env)
    if check and run.returncode != 0:
        raise RefreshError([f"git {' '.join(args)} in {repo} failed: {ohost._last_words(run.stderr)}"])
    return run


# --- the clone, where it is -------------------------------------------------------------------

# Where the checked-out branch stands against the audience's base, in the
# clone: level (the base is in it), empty (it is in the base: nothing of
# its own), as git merge-base --is-ancestor's exit codes; the base is the
# one declared, else the branch AUDIENCE/HEAD names.
_ANCESTRY_SCRIPT = (
    'a="$1"; b="$2"; [ -n "$b" ] || b=$(git symbolic-ref -q --short "refs/remotes/$a/HEAD" | sed "s|^$a/||"); '
    't="refs/remotes/$a/$b"; git rev-parse -q --verify "$t^{commit}" >/dev/null || { echo "track=none"; exit 0; }; '
    'git merge-base --is-ancestor "$t" HEAD 2>/dev/null; echo "level=$?"; '
    'git merge-base --is-ancestor HEAD "$t" 2>/dev/null; echo "empty=$?"'
)


def view_argvs(audience, base=None):
    """clone_view's argvs, for a batch that carries them beside other reads
    (office deliver's first connection)."""
    return [["git", "for-each-ref", "--format=%(objectname) %(refname)", f"refs/remotes/{audience}/", "refs/heads/"],
            ["git", "symbolic-ref", "-q", "--short", "HEAD"],
            ["git", "symbolic-ref", "-q", "--short", f"refs/remotes/{audience}/HEAD"],
            ["git", "status", "--porcelain=v1", "-uno"],
            ["git", "remote", "get-url", audience],
            ["sh", "-c", _ANCESTRY_SCRIPT, "office-ancestry", audience, base or ""]]


def read_view(place, audience, runs):
    """clone_view's dict from the Runs of view_argvs."""
    refs, head, rhead, status, url, anc = runs
    if refs.returncode != 0:
        raise RefreshError([f"the clone at {place} could not be read: {ohost._last_words(refs.stderr)}"])
    if url.returncode != 0 or not url.stdout.strip():
        raise RefreshError([f"the clone at {place} has no remote named {audience}: office projects set NAME "
                            "--audience REMOTE names the right one"])
    remote, heads = {}, {}
    rprefix = f"refs/remotes/{audience}/"
    for line in refs.stdout.splitlines():
        sha, _, ref = line.partition(" ")
        if ref.startswith(rprefix):
            name = ref[len(rprefix):]
            if name != "HEAD":
                remote[name] = sha
        elif ref.startswith("refs/heads/"):
            heads[ref[len("refs/heads/"):]] = sha
    rh = rhead.stdout.strip() if rhead.returncode == 0 else ""
    facts = dict(l.split("=", 1) for l in anc.stdout.splitlines() if "=" in l)
    return {"remote": remote, "heads": heads,
            "branch": head.stdout.strip() if head.returncode == 0 and head.stdout.strip() else None,
            "remote_head": rh[len(audience) + 1:] if rh.startswith(audience + "/") else None,
            "dirty": [l[3:] for l in status.stdout.splitlines() if l.strip()],
            "url": url.stdout.strip().splitlines()[-1],
            "level": facts.get("level") == "0", "empty": facts.get("empty") == "0"}


def clone_view(place, audience, base=None):
    """What a refresh, start's compare and deliver's merge read of a clone,
    in one batch (one connection for a hosted place): remote (the audience's
    remote-tracking branches, {branch: sha}), heads ({branch: sha}), branch
    (checked out, or None), remote_head (the branch AUDIENCE/HEAD names),
    dirty (tracked paths changed, a list), url (the audience remote's URL),
    level (the base, the declared one or AUDIENCE/HEAD's, is in the
    checked-out branch) and empty (the checked-out branch is in the base)."""
    return read_view(place, audience, ohost.run_many(place, view_argvs(audience, base)))


def base_of(entry, view):
    """The base branch: the project's declaration, else the branch the
    audience remote's HEAD names in the clone."""
    base = entry.get("base") or view.get("remote_head")
    if not base:
        raise RefreshError([f"{entry['name']}'s clone does not say which branch {entry['audience']} points at (no "
                            f"{entry['audience']}/HEAD), so the base is not known; office projects set "
                            f"{entry['name']} --base BRANCH names it"])
    return base


def fetch_url(place, url):
    """The URL this machine fetches the audience from: the clone's own,
    a relative path on this machine made absolute against the clone."""
    if place.hosted or "://" in url or (":" in url and not url.startswith(("/", "."))) or os.path.isabs(url):
        return url
    return str((pathlib.Path(place.path) / url).resolve())


# --- the audience, here --------------------------------------------------------------------------

def mirror(prefix="office-refresh-"):
    """A temporary bare repo on this machine (the shape of office deliver's
    mirror_here): (its directory, the repo)."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix=prefix)
    repo = pathlib.Path(tmp) / "mirror.git"
    git_here(tmp, "init", "-q", "--bare", str(repo))
    return tmp, repo


def fetch_here(repo, url, audience, branches=None):
    """The audience's branches (all, or the ones named) fetched into the
    mirror's refs/heads, forced, with this machine's credentials; {branch:
    sha} as fetched."""
    specs = [f"+refs/heads/{b}:refs/heads/{b}" for b in branches] if branches else ["+refs/heads/*:refs/heads/*"]
    run = git_here(repo, "fetch", "-q", url, *specs, check=False)
    if run.returncode != 0:
        raise RefreshError([f"{audience} ({url}) did not answer from this machine (git fetch exit {run.returncode}): "
                            f"{ohost._last_words(run.stderr)}; the audience is reached with this machine's "
                            "credentials, so check them (git ls-remote there, by hand)"])
    out = git_here(repo, "for-each-ref", "--format=%(objectname) %(refname)", "refs/heads/").stdout
    return {ref[len("refs/heads/"):]: sha for sha, _, ref in (l.partition(" ") for l in out.splitlines())}


def known(repo, sha):
    return bool(sha) and git_here(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode == 0


def known_commits(repo, shas):
    """The shas that name a commit in the repo, asked in one git call
    (cat-file --batch-check on stdin): a clone may name hundreds."""
    import subprocess
    shas = sorted({s for s in shas if s})
    if not shas:
        return []
    debug(f"git cat-file --batch-check in {repo}: {len(shas)} sha(s)")
    proc = subprocess.run(["git", "-C", str(repo), "cat-file", "--batch-check=%(objectname) %(objecttype)"],
                          input="".join(f"{s}\n" for s in shas), capture_output=True, text=True,
                          timeout=ohost.RUN_TIMEOUT)
    if proc.returncode != 0:
        raise RefreshError([f"git cat-file in {repo} failed: {ohost._last_words(proc.stderr)}"])
    return [l.split()[0] for l in proc.stdout.splitlines() if l.endswith(" commit")]


def ancestor(repo, old, new):
    return known(repo, old) and git_here(repo, "merge-base", "--is-ancestor", old, new, check=False).returncode == 0


def count(repo, old, new):
    return int(git_here(repo, "rev-list", "--count", f"{old}..{new}").stdout.strip() or 0)


def moved_line(repo, audience, branch, old, new):
    """One line for one branch that moved, counted in a repo holding both
    ends: `origin/main: 59385bf..3f1a9c2, 14 commits`."""
    if not old:
        return f"{audience}/{branch}: new, at {short(new)}"
    if ancestor(repo, old, new):
        n = count(repo, old, new)
        return f"{audience}/{branch}: {short(old)}..{short(new)}, {n} commit{'' if n == 1 else 's'}"
    return f"{audience}/{branch}: {short(old)}..{short(new)}, forced ({short(old)} is no longer on it: the audience rewrote it)"


def behind_words(repo, audience, base, clone_sha, audience_sha):
    """The line start and deliver say when the clone's view of the base is
    behind the audience's, counted in a repo that holds the audience's
    base; None when it is level or ahead (nothing is said then)."""
    if not audience_sha or clone_sha == audience_sha:
        return None
    view = f"the clone's view of {audience}/{base}"
    if not clone_sha:
        return f"{view} is missing: the clone has never seen {audience}'s {base}"
    if known(repo, clone_sha):
        if ancestor(repo, clone_sha, audience_sha):
            n = count(repo, clone_sha, audience_sha)
            return f"{view} is {n} commit{'' if n == 1 else 's'} behind the audience's ({short(clone_sha)}, the audience at {short(audience_sha)})"
        if ancestor(repo, audience_sha, clone_sha):
            return None
    return (f"{view} ({short(clone_sha)}) is not on the audience's {base} ({short(audience_sha)}): the audience "
            "rewrote it since the clone last saw it")


# --- the refresh ------------------------------------------------------------------------------------

# The far side of a hosted refresh, in the clone: the bundle (when there is
# one) fetched with the forcing refspec, then every moved branch held to
# its new tip (update-ref where the bundle carried nothing for it: a tip
# the clone already has), each printed as it ended up; then whether the
# local base is an ancestor of the audience's.
_APPLY_SCRIPT = (
    'b="$1"; a="$2"; base="$3"; shift 3; '
    'if [ -n "$b" ]; then git fetch -q "$b" "+refs/heads/*:refs/remotes/$a/*" || exit 2; fi; '
    'while [ $# -ge 2 ]; do '
    'cur=$(git rev-parse -q --verify "refs/remotes/$a/$1"); '
    'if [ "$cur" != "$2" ]; then '
    'if git cat-file -e "$2^{commit}" 2>/dev/null; then git update-ref "refs/remotes/$a/$1" "$2" || exit 3; '
    'else echo "missing=$1"; fi; fi; '
    'echo "ref=$1 $(git rev-parse -q --verify "refs/remotes/$a/$1")"; shift 2; done; '
    'l=$(git rev-parse -q --verify "refs/heads/$base"); '
    'if [ -n "$l" ] && git merge-base --is-ancestor "$l" "refs/remotes/$a/$base" 2>/dev/null; '
    'then echo "base_ancestor=yes"; else echo "base_ancestor=no"; fi'
)
# The stamp: a blob of the refresh's words, and the ref naming it.
_STAMP_SCRIPT = 'h=$(printf %s "$1" | git hash-object -w --stdin) && git update-ref "$2" "$h"'


def stamp_text(audience, url, now=None):
    import socket
    import time
    at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))
    return f"refreshed {at}\nfrom {audience} {url}\nby way of {socket.gethostname() or 'this machine'}\n"


def refresh(office_root, name, rd=None, entry=None):
    """office projects refresh NAME. Returns (lines, moved): the lines to
    print and the branches that moved ({branch: (old, new)})."""
    import shutil
    entry = entry or audience_entry(office_root, name)
    audience = entry["audience"]
    place = ohost.place_of(entry)
    try:
        view = clone_view(place, audience, entry.get("base"))
    except ohost.HostError as exc:
        raise RefreshError([f"{name}: {exc}"])
    base = base_of(entry, view)
    url = fetch_url(place, view["url"])
    where = f"{place.host}" if place.hosted else "this machine"
    lines = []
    tmp, repo = mirror()
    try:
        log(f"fetching {audience}'s branches from {url} on this machine, with its credentials (+refs/heads/*)")
        heads = fetch_here(repo, url, audience)
        moved = {b: (view["remote"].get(b), sha) for b, sha in sorted(heads.items()) if view["remote"].get(b) != sha}
        lines.append(f"{name}: {audience}'s {len(heads)} branch(es) fetched on this machine from {url}, with a forcing "
                     f"refspec ({REFSPEC.format(audience=audience)})")
        said = [moved_line(repo, audience, b, old, new) for b, (old, new) in moved.items()]
        if place.hosted:
            after, base_anc = carry(place, repo, tmp, audience, base, view, moved, lines)
        else:
            run = ohost.run_in(place, ["git", "fetch", "-q", audience, REFSPEC.format(audience=audience)],
                               timeout=ohost.TRANSFER_TIMEOUT)
            if run.returncode != 0:
                raise RefreshError([f"git fetch {audience} in {place} failed: {ohost._last_words(run.stderr)}"])
            after = clone_view(place, audience, base)["remote"]
            local = view["heads"].get(base)
            base_anc = bool(local) and ohost.run_in(
                place, ["git", "merge-base", "--is-ancestor", local, f"refs/remotes/{audience}/{base}"]).returncode == 0
        off = [b for b, (_, new) in moved.items() if after.get(b) != new]
        if off:
            raise RefreshError([f"{name}: the clone at {place} does not hold what the audience has for "
                                f"{', '.join(off)} after the refresh; nothing else was moved"])
        lines += said or ["nothing moved"]
        lines += fast_forward(place, entry, view, base, after.get(base), base_anc, rd)
        stamp = ohost.run_in(place, ["sh", "-c", _STAMP_SCRIPT, "office-stamp", stamp_text(audience, url),
                                     stamp_ref(audience)])
        if stamp.returncode != 0:
            lines.append(f"warning: the refresh's stamp ({stamp_ref(audience)}) could not be written in the clone: "
                         f"{ohost._last_words(stamp.stderr)}; office projects will not say when it was refreshed")
        kept = view["branch"]
        moved_kept = kept == base and any(l.startswith(f"{base}: ") and "fast-forwarded" in l for l in lines)
        lines.append((f"the checked-out branch {kept} was not touched; " if kept and not moved_kept else "")
                     + f"no ref was deleted and nothing was pushed (the clone is on {where})")
        return lines, moved
    except ohost.HostError as exc:
        raise RefreshError([f"{name}: {exc}"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def carry(place, repo, tmp, audience, base, view, moved, lines):
    """The hosted half: a bundle of the moved branches, thin against every
    commit the clone names, sent into the office's temporary directory on
    the host and fetched there; the directory removed in the same
    connection. Returns (the clone's remote-tracking refs after, whether
    its local base is an ancestor of the audience's)."""
    names = [b for b in moved]
    prereqs = known_commits(repo, [*view["remote"].values(), *view["heads"].values()])
    bundle = pathlib.Path(tmp) / "refresh.bundle"
    made = None
    if names:
        made = git_here(repo, "bundle", "create", "-q", str(bundle), *[f"refs/heads/{b}" for b in names],
                        *[f"^{p}" for p in prereqs], check=False)
        if made.returncode != 0 and "empty bundle" not in made.stderr:
            raise RefreshError([f"git bundle create in the mirror failed: {ohost._last_words(made.stderr)}"])
    has_bundle = bool(names) and made is not None and made.returncode == 0 and bundle.is_file()
    pairs = [w for b in names for w in (b, moved[b][1])]
    with ohost.Scratch(place) as sc:
        remote = sc.send(str(bundle)) if has_bundle else ""
        argvs = [["sh", "-c", _APPLY_SCRIPT, "office-refresh", remote, audience, base, *pairs]]
        if sc.made:
            argvs.append(sc.removal_argv())
        runs = ohost.run_many(place, argvs, timeout=ohost.TRANSFER_TIMEOUT)
        if sc.made:
            sc.removed_by_step()
    run = runs[0]
    if run.returncode != 0:
        raise RefreshError([f"the refresh could not be fetched in the clone at {place} (exit {run.returncode}): "
                            f"{ohost._last_words(run.stderr)}; the remote-tracking refs are as git left them"])
    if has_bundle:
        lines.append(f"carried to {place.host} as a bundle of {len(names)} branch(es), {bundle.stat().st_size} bytes, "
                     f"thin against the {len(prereqs)} commit(s) the clone names, checked by sha256, fetched there "
                     f"with {REFSPEC.format(audience=audience)}; the bundle was removed")
    after = dict(view["remote"])
    for line in run.stdout.splitlines():
        if line.startswith("ref="):
            b, _, sha = line[4:].partition(" ")
            after[b] = sha
    return after, "base_ancestor=yes" in run.stdout.splitlines()


def open_sessions(place, rd=None):
    """The sessions bale has open in the clone, by id; [] where bale keeps
    no registry. A BaleError says why they could not be read."""
    rd = rd or ob.Reader()
    if not ob._bale_registry_at(place if place.hosted else place.path, rd):
        return []
    return [sid for sid, _ in rd.open_sessions(place if place.hosted else place.path)]


def fast_forward(place, entry, view, base, new, base_anc, rd=None):
    """The base branch fast-forwarded to the audience's in the clone, or
    why not, as lines. Never a merge, never the workbench (a base checked
    out with commits of its own is not an ancestor, and is left)."""
    audience = entry["audience"]
    local = view["heads"].get(base)
    if not new:
        return [f"{audience} has no branch {base}, so there is no base to fast-forward"]
    if not local:
        return [f"the clone has no local {base} branch; {audience}/{base} is its view of the base"]
    if local == new:
        return [f"{base} is level with {audience}/{base}"]
    if not base_anc:
        return [f"{base} has commits of its own that {audience}/{base} does not, so it was not moved: a refresh "
                "never merges (office deliver brings the base into the workbench when that merge is clean)"]
    if view["branch"] == base:
        if view["dirty"]:
            return [f"{base} is checked out with uncommitted changes ({len(view['dirty'])} path(s)), so it was not "
                    f"fast-forwarded; the remote-tracking refs moved (git merge --ff-only {audience}/{base} there, "
                    "once they are committed or stashed)"]
        try:
            sessions = open_sessions(place, rd)
        except ob.BaleError as exc:
            return [f"{base} is checked out, and the sessions open in the clone could not be read ({exc}), so it "
                    "was not moved under them; the remote-tracking refs moved"]
        if sessions:
            return [f"{base} is checked out with {len(sessions)} session(s) open in the clone ({', '.join(sessions)}), "
                    "which bale lands on the branch checked out there, so it was not moved under them; the "
                    "remote-tracking refs moved"]
        run = ohost.run_in(place, ["git", "merge", "--ff-only", "-q", f"refs/remotes/{audience}/{base}"])
        how = "fast-forwarded (checked out, git merge --ff-only)"
    else:
        run = ohost.run_in(place, ["git", "update-ref", f"refs/heads/{base}", new, local])
        how = "fast-forwarded (update-ref: it is not checked out)"
    if run.returncode != 0:
        return [f"{base} could not be fast-forwarded: {ohost._last_words(run.stderr)}; it is as it was"]
    return [f"{base}: {short(local)}..{short(new)}, {how}"]


# --- start's compare, and what office projects lists ------------------------------------------------

def compare_line(office_root, name):
    """The one line start says before the pack when the clone's view of
    the base is behind the audience's, else None: the audience's base
    asked once on this machine (git ls-remote), and only when it differs,
    fetched into a temporary mirror to count."""
    import shutil
    entry = audience_entry(office_root, name)
    audience = entry["audience"]
    place = ohost.place_of(entry)
    try:
        view = clone_view(place, audience, entry.get("base"))
    except ohost.HostError as exc:
        raise RefreshError([f"{name}: {exc}"])
    base = base_of(entry, view)
    url = fetch_url(place, view["url"])
    import tempfile
    ls = git_here(tempfile.gettempdir(), "ls-remote", url, f"refs/heads/{base}", check=False)
    if ls.returncode != 0:
        raise RefreshError([f"{audience} ({url}) did not answer from this machine (git ls-remote exit {ls.returncode}): "
                            f"{ohost._last_words(ls.stderr)}"])
    there = (ls.stdout.split() or [None])[0]
    if there is None or there == view["remote"].get(base):
        return None
    tmp, repo = mirror()
    try:
        fetch_here(repo, url, audience, [base])
        return behind_words(repo, audience, base, view["remote"].get(base), there)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def refreshed_line(entry):
    """What office projects says of a project with an audience: when its
    clone's view was last refreshed and from where, read from the clone
    (the ref a refresh leaves), or that the office has not refreshed it."""
    audience = entry["audience"]
    place = ohost.place_of(entry)
    try:
        run = ohost.run_in(place, ["sh", "-c", 'git cat-file -p "$1" 2>/dev/null || true', "office-stamp",
                                   stamp_ref(audience)])
    except ohost.HostError as exc:
        return f"refreshed: unread ({exc})"
    words = dict(l.split(" ", 1) for l in run.stdout.splitlines() if " " in l)
    if run.returncode != 0 or "refreshed" not in words:
        return f"refreshed: not by the office yet (office projects refresh {entry['name']} brings its view of {audience} level)"
    by = words.get("by", "").removeprefix("way of ").strip()
    return (f"refreshed: {words['refreshed']} from {words.get('from', audience)}"
            + (f", by way of {by}" if by else "") + f" (read from the clone's {stamp_ref(audience)})")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="office_refresh.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("refresh", help="office projects refresh NAME: the clone's view of its audience brought level")
    p.add_argument("office"); p.add_argument("--project", required=True)
    p = sub.add_parser("compare", help="start's compare: one line when the clone's view of the base is behind")
    p.add_argument("office"); p.add_argument("--project", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "refresh":
            lines, _ = refresh(a.office, a.project)
            for line in lines:
                print(line)
            return 0
        line = compare_line(a.office, a.project)
        if line:
            print(line)
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
