"""The suite's fake gh (0.42.0): GitHub's command line as the office runs it,
answering from a state file, never a network.

A test never runs this file. tests/test_pull_requests.py FakeGh writes a
program named gh in a directory of the test's own (tests/test_office.py
fake_program) and points OFFICE_GH_PATH at it, so the office finds it
through its one door (lib/office_review.py gh_program) and no test runs
the machine's own gh. Its config is {"state": file, "calls": file}; every
call is recorded as one JSON line, the argv, and, for pr create, the body
file's text as gh read it.

The state file is JSON: {"hosts": {HOST: true}} for the hosts gh is signed
in to, "pulls": [{repo, number, url, state, reviewDecision, headRefName,
baseRefName, isDraft, closedAt, mergedAt, title, body, reviewers}], and
optionally "refuse": {verb: [exit, stderr]} to make one verb refuse ("pr
create", "pr list", "auth status").

What it answers, as gh 2.45 does:
- --version: `gh version 2.45.0 (2024-03-04)` and the release URL.
- auth status --hostname HOST: exit 0 and a line when signed in; exit 1
  and gh's words when not.
- pr create --repo HOST/OWNER/REPO --base B --head H --title T --body-file F
  [--reviewer L]: the URL of a new pull request on stdout; exit 1 with gh's
  words when one is open already for H, exit 4 when not signed in.
- pr list --repo R --state S --limit N --json FIELDS [--head H]: the JSON
  array of the pull requests on R in that state (all, open, closed or
  merged), those whose head is H when given, newest first, with only the
  fields asked for.
Anything else exits 97, as the fake bales do.
"""

import json
import pathlib
import sys

VERSION = "gh version 2.45.0 (2024-03-04)\nhttps://github.com/cli/cli/releases/tag/v2.45.0"
NOT_SIGNED_IN = "To get started with GitHub CLI, please run:  gh auth login\nAlternatively, populate the GH_TOKEN environment variable with a GitHub API authentication token."


def flag(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def main(cfg, argv):
    state_path = pathlib.Path(cfg["state"])
    state = json.loads(state_path.read_text()) if state_path.is_file() else {}
    state.setdefault("hosts", {})
    state.setdefault("pulls", [])
    record = {"argv": argv}

    def save():
        state_path.write_text(json.dumps(state, indent=1))

    def done(code, out="", err=""):
        with open(cfg["calls"], "a") as fh:
            fh.write(json.dumps(record) + "\n")
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
        return code

    if argv == ["--version"]:
        return done(0, VERSION)
    verb = " ".join(argv[:2])
    refuse = (state.get("refuse") or {}).get(verb)
    if refuse:
        return done(refuse[0], "", refuse[1])
    if verb == "auth status":
        host = flag(argv, "--hostname", "github.com")
        if state["hosts"].get(host):
            return done(0, "", f"{host}\n  Logged in to {host} account a-login (keyring)")
        return done(1, "", "You are not logged into any GitHub hosts. To log in, run: gh auth login")
    if verb == "pr create":
        repo = flag(argv, "--repo")
        host = repo.split("/")[0] if repo and repo.count("/") >= 2 else "github.com"
        if not state["hosts"].get(host):
            return done(4, "", NOT_SIGNED_IN)
        head, base = flag(argv, "--head"), flag(argv, "--base")
        body_file = flag(argv, "--body-file")
        body = pathlib.Path(body_file).read_text() if body_file else ""
        record["body"] = body
        for p in state["pulls"]:
            if p["repo"] == repo and p["headRefName"] == head and p["state"] == "OPEN":
                return done(1, "", f'a pull request for branch "{head}" into branch "{p["baseRefName"]}" already '
                                   f'exists:\n{p["url"]}')
        number = max([p["number"] for p in state["pulls"] if p["repo"] == repo] or [0]) + 1
        url = f"https://{repo}/pull/{number}"
        state["pulls"].append({"repo": repo, "number": number, "url": url, "state": "OPEN", "reviewDecision": "",
                               "headRefName": head, "baseRefName": base, "isDraft": False, "closedAt": None,
                               "mergedAt": None, "title": flag(argv, "--title"), "body": body,
                               "reviewers": [flag(argv, "--reviewer")] if flag(argv, "--reviewer") else []})
        save()
        return done(0, f"\nCreating pull request for {head} into {base} in {repo.split('/', 1)[1]}\n\n{url}")
    if verb == "pr list":
        repo = flag(argv, "--repo")
        host = repo.split("/")[0] if repo and repo.count("/") >= 2 else "github.com"
        if not state["hosts"].get(host):
            return done(4, "", NOT_SIGNED_IN)
        want = (flag(argv, "--state", "open") or "open").upper()
        head = flag(argv, "--head")
        fields = (flag(argv, "--json") or "number").split(",")
        rows = [p for p in state["pulls"] if p["repo"] == repo and (want == "ALL" or p["state"] == want)
                and (head is None or p["headRefName"] == head)]
        rows.sort(key=lambda p: -p["number"])
        return done(0, json.dumps([{f: p.get(f) for f in fields} for p in rows]))
    return done(97, "", f"fake gh: {' '.join(argv)}")
