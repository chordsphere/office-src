"""Tests for office-src 0.42.0: pull requests through gh (the report of
2026-10-27, its fifth gap; the gaps of 2026-10-28, A6; 0.40.0's first and
third proposals). One class per item:

1. office deliver opens the review when asked, through gh, and records its
   number on the folder; without gh, signed out, on no or piped, the
   review's body goes to the clipboard and its title and URL are printed.
2. The office reads review state: the walk-in, office desk, the home
   screen and the digest say each review on a branch the office delivered.
3. A delivery added to a branch with an open pull request shows the
   request's base as its from.
4. The survey records gh.
6. office letterhead check --delivery reads a delivery.md as deliver does.
7. The delivery branch's name is held to the letterhead's marks before
   anything is fetched.
9. The merge session's whole loop through the office's commands: deliver
   refuses, office start N --merge, office land, deliver again.

(Item 5 is the doctrine's and the README's words; item 8 is a proposal in
the session's notes.) gh is the suite's fake (tests/fakes/gh_fake.py),
found through OFFICE_GH_PATH, the office's one door to it; the audience is
the bare repo of tests/test_audience_line.py, reached as an invented
GitHub Enterprise host through a fake ssh (GIT_SSH_COMMAND), so the remote's
URL names the host the review is opened on. Run with the rest of the suite:

    tests/run.sh test_pull_requests
"""

import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import Env, fake_program, h  # noqa: E402
from test_audience_line import SID, git  # noqa: E402
from test_host_refresh import RefreshCase  # noqa: E402
from test_start import on_a_terminal  # noqa: E402

import office_review as orev  # noqa: E402
import office_deliver as odl  # noqa: E402

GH_HOST = "github.example.org"
REPO_SLUG = f"{GH_HOST}/acme/proj"
REMOTE = f"git@{GH_HOST}:acme/proj.git"
LOGIN = "pat-reviewer"


class FakeGh:
    """A directory holding the suite's fake gh, its state and its calls;
    env() points the office's door at it."""

    def __init__(self, tmp, signed_in=(GH_HOST,)):
        self.dir = tmp / "gh-bin"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state = tmp / "gh-state.json"
        self.calls = tmp / "gh-calls.jsonl"
        self.state.write_text(json.dumps({"hosts": {host: True for host in signed_in}, "pulls": []}))
        fake_program(self.dir / "gh", "gh_fake", config={"state": str(self.state), "calls": str(self.calls)})

    def env(self):
        return {"OFFICE_GH_PATH": str(self.dir)}

    def read(self):
        return json.loads(self.state.read_text())

    def write(self, **changes):
        s = self.read()
        s.update(changes)
        self.state.write_text(json.dumps(s))

    def add_pull(self, number, head, base="main", state="OPEN", decision="", repo=REPO_SLUG, **more):
        s = self.read()
        s["pulls"].append({"repo": repo, "number": number, "url": f"https://{repo}/pull/{number}", "state": state,
                           "reviewDecision": decision, "headRefName": head, "baseRefName": base, "isDraft": False,
                           "closedAt": more.get("closedAt"), "mergedAt": more.get("mergedAt"), "title": "t",
                           "body": "b", "reviewers": []})
        self.state.write_text(json.dumps(s))

    def calls_of(self, *verb):
        if not self.calls.is_file():
            return []
        out = [json.loads(l) for l in self.calls.read_text().splitlines()]
        return [c for c in out if tuple(c["argv"][:len(verb)]) == verb]


class GhCase(RefreshCase):
    """RefreshCase's world (the audience, the workbench clone with one
    session landed, the folder and its words, a fake bale), with the
    audience reached as git@github.example.org:acme/proj.git through a fake
    ssh that serves the bare repo, and the fake gh signed in to that host
    and found through the office's door."""

    def setUp(self):
        super().setUp()
        served = self.e.tmp / "served" / "acme"
        served.mkdir(parents=True)
        (served / "proj.git").symlink_to(self.audience)
        ssh = self.e.tmp / "fake-ssh"
        # git runs: ssh [-o OPT]... [-p PORT] HOST COMMAND; the command is
        # git-upload-pack or git-receive-pack with the repo's path, served
        # from the directory above.
        ssh.write_text("#!/bin/sh\n"
                       'while [ $# -gt 1 ]; do case "$1" in -o|-p) shift 2 ;; -*) shift ;; *) shift; break ;; esac; done\n'
                       f'cd "{served.parent}" && exec sh -c "$1"\n')
        ssh.chmod(0o755)
        self.e.env["GIT_SSH_COMMAND"] = str(ssh)
        git(self.clone, "remote", "set-url", "origin", REMOTE, env=self.e.env)
        self.gh = FakeGh(self.e.tmp)
        self.e.env.update(self.gh.env())

    def deliver(self, *flags, extra=None):
        return self.run_office("deliver", self.name, "--yes", *flags, extra=extra)


# --- 1. deliver opens the review when asked --------------------------------------------------------

class TestDeliverOpensTheReview(GhCase):
    def test_asked_by_flag_gh_opens_it_and_the_folder_records_it(self):
        proc = self.deliver("--open-review")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("health-route", self.audience_refs()[0] + " ".join(self.audience_refs()))
        create, = self.gh.calls_of("pr", "create")
        argv = create["argv"]
        pairs = {argv[i]: argv[i + 1] for i in range(2, len(argv) - 1, 2)}
        self.assertEqual((pairs["--repo"], pairs["--base"], pairs["--head"], pairs["--title"]),
                         (REPO_SLUG, "main", "health-route", "Health route for the API"))
        self.assertNotIn("--reviewer", argv)  # Pat Reviewer is a name, not a login
        self.assertEqual(create["body"].strip(), "One route and its test. The pullsheet code is untouched.")
        url = f"https://{REPO_SLUG}/pull/1"
        self.assertIn(f"opened the review: #1 {url}", proc.stdout)
        self.assertIn(f"the review is open: #1 {url}", proc.stdout)
        self.assertNotIn("open the review: https", proc.stdout)
        # The question's words, shown before it is opened.
        self.assertIn(f"The review, as gh will open it on {GH_HOST}:", proc.stdout)
        self.assertIn("reviewer: none passed to gh (delivery.md's to: line, Pat Reviewer, does not read as a login",
                      proc.stdout)
        self.assertIn(f"gh line:  gh pr create --repo {REPO_SLUG} --base main --head health-route", proc.stdout)
        # The folder's History and the office's commit.
        self.assertRegex(self.folder_md(), rf"- \d{{4}}-\d{{2}}-\d{{2}} review: health-route on origin of proj: #1 "
                                           rf"{re.escape(url)}\n")
        self.assertEqual(git(self.root, "log", "-1", "--format=%s", env=self.e.env).strip(),
                         "office deliver: review #1 for health-route")
        self.assertEqual(git(self.root, "status", "--porcelain", env=self.e.env), "")
        # office status knows the verb.
        self.assertNotIn("is not one of the set", self.run_office("status").stdout)
        # Opened, nothing goes to the clipboard.
        self.assertNotIn("the review's body", proc.stderr)

    def test_a_login_on_the_to_line_is_the_reviewer(self):
        md = (self.root / self.folder / "delivery.md").read_text().replace("- to: Pat Reviewer", f"- to: @{LOGIN}")
        self.write_words(md)
        proc = self.deliver("--open-review")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        create, = self.gh.calls_of("pr", "create")
        self.assertEqual(create["argv"][create["argv"].index("--reviewer") + 1], LOGIN)
        self.assertIn(f"reviewer: {LOGIN} (delivery.md's to: line)", proc.stdout)

    def test_piped_without_the_flag_nothing_is_opened_and_the_words_are_printed(self):
        proc = self.deliver()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.gh.calls_of("pr", "create"), [])
        err = " ".join(proc.stderr.split())
        self.assertIn("the review was not opened: piped, nothing is opened on the audience without its question", err)
        self.assertIn("open the review: https://github.example.org/acme/proj/compare/main...health-route?", proc.stdout)
        self.assertIn("the review's title: Health route for the API", proc.stdout)
        self.assertIn("the review's body is not on the clipboard: off a terminal", err)
        self.assertNotIn(" review: ", self.folder_md())

    def test_no_says_no_and_the_flag_twin_is_honoured(self):
        proc = self.deliver("--no-open-review")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.gh.calls_of("pr", "create"), [])
        self.assertNotIn("piped, nothing is opened", proc.stderr)
        proc = self.run_office("deliver", self.name, "--open-review", "--no-open-review")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--open-review and --no-open-review contradict each other", proc.stderr)

    def test_gh_refusing_is_said_whole_and_the_delivery_stands(self):
        self.gh.write(refuse={"pr create": [1, "GraphQL: Resource not accessible by integration (createPullRequest)"]})
        proc = self.deliver("--open-review")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        err = " ".join(proc.stderr.split())
        self.assertIn("gh did not open the review: GraphQL: Resource not accessible by integration "
                      "(createPullRequest)", err)
        self.assertIn("the delivery stands: health-route is on the audience", err)
        self.assertIn("refs/heads/health-route", self.audience_refs())
        self.assertIn("delivered: health-route", self.folder_md())
        self.assertNotIn(" review: ", self.folder_md())
        self.assertIn("open the review: https://github.example.org/acme/proj/compare/", proc.stdout)

    def test_without_gh_or_signed_out_one_line_says_why(self):
        proc = self.deliver("--open-review", extra={"OFFICE_GH_PATH": ""})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("the review was not opened: gh is not on this machine", proc.stderr)
        self.assertIn("open the review: https://", proc.stdout)

    def test_signed_out_the_office_never_signs_it_in(self):
        self.gh.write(hosts={})
        proc = self.deliver("--open-review")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"gh is not signed in to {GH_HOST}", proc.stderr)
        self.assertIn("the office never signs it in", proc.stderr)
        self.assertEqual(self.gh.calls_of("pr", "create"), [])
        self.assertEqual([c["argv"][:2] for c in json.loads("[" + ",".join(
            self.gh.calls.read_text().splitlines()) + "]")], [["auth", "status"]])

    def test_a_branch_with_a_review_open_opens_nothing_and_names_it(self):
        self.deliver("--open-review")
        # A second session, delivered onto the same branch: the review open
        # there carries it.
        self.land_session("2026-10-10-health-more-001", {"src/health.py": 'def health():\n    return "fine"\n'},
                          "More health")
        self.run_office("sessions", self.name, "2026-10-10-health-more-001", check=0)
        if (self.root / "filing-cabinet" / self.name).is_dir():
            self.run_office("reopen", self.name, check=0)
        proc = self.deliver("--open-review")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len(self.gh.calls_of("pr", "create")), 1)
        self.assertIn(f"the review that carries it: #1 https://{REPO_SLUG}/pull/1", proc.stdout)


class TestOnATerminalItIsAskedOnce(GhCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    QUESTION = b"Open this review on the audience through gh? (--open-review) (y/n) [n]: "

    def test_the_question_defaults_to_no(self):
        argv = [str(self.e.office_bin), "deliver", self.name, "--yes", "--leave-open"]
        code, seen = on_a_terminal(self, argv, self.root, self.e.env, [(self.QUESTION, "")])
        self.assertEqual(code, 0, seen)
        self.assertEqual(self.gh.calls_of("pr", "create"), [])
        self.assertIn("title:    Health route for the API", seen)
        self.assertEqual(seen.count("(--open-review) (y/n)"), 1)
        self.assertIn("the review's body", seen)  # said as every copy is said
        self.assertNotIn(" review: ", self.folder_md())

    def test_yes_opens_it_and_records_it_before_the_folder_closes(self):
        argv = [str(self.e.office_bin), "deliver", self.name, "--yes"]
        code, seen = on_a_terminal(self, argv, self.root, self.e.env, [(self.QUESTION, "y")])
        self.assertEqual(code, 0, seen)
        self.assertEqual(len(self.gh.calls_of("pr", "create")), 1)
        self.assertIn(f"opened the review: #1 https://{REPO_SLUG}/pull/1", seen)
        filed = self.root / "filing-cabinet" / self.name / "folder.md"
        self.assertTrue(filed.is_file(), seen)  # closed at delivery, on a terminal
        self.assertIn(" review: health-route on origin of proj: #1 ", filed.read_text())


# --- 2. the office reads review state -------------------------------------------------------------

class TestTheOfficeReadsReviewState(GhCase):
    def setUp(self):
        super().setUp()
        proc = self.deliver("--open-review", "--leave-open")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.cite = f"folder {h.parse_folder(self.folder_md())['fields']['number'][0]}"

    def decide(self, decision, state="OPEN"):
        s = self.gh.read()
        s["pulls"][0].update(reviewDecision=decision, state=state)
        self.gh.write(pulls=s["pulls"])

    def test_the_walk_in_and_the_desk_say_each_review(self):
        self.decide("APPROVED")
        walk = self.run_office().stdout
        self.assertIn(f"Reviews:\n  proj: #1 approved (health-route, {self.cite})\n", walk)
        desk = self.run_office("desk").stdout
        self.assertIn(f"  proj: #1 approved (health-route, {self.cite})", desk)
        self.assertIn("[review #1 approved]", desk)
        # Reading asks nothing and changes nothing: gh pr list alone.
        verbs = {tuple(c["argv"][:2]) for c in map(json.loads, self.gh.calls.read_text().splitlines())}
        self.assertEqual(verbs, {("auth", "status"), ("pr", "create"), ("pr", "list")})
        self.assertEqual(len(self.gh.read()["pulls"]), 1)

    def test_changes_requested_names_what_answers_it(self):
        self.decide("CHANGES_REQUESTED")
        desk = self.run_office("desk").stdout
        self.assertIn(f"proj: #1 changes requested (health-route, {self.cite})", desk)
        self.assertIn("#1 asked for changes: a session answers them on health-route, and office deliver "
                      f"{self.cite} --branch health-route adds the answer to the review", desk)
        self.assertIn("next: answer review #1's requested changes on health-route; then ", desk)

    def test_merged_and_closed_and_a_filed_folder(self):
        self.decide("", state="MERGED")
        self.assertIn("proj: #1 merged (health-route", self.run_office().stdout)
        self.run_office("close", self.name, check=0)
        # Filed, a merged review is shown for a week after it was merged.
        long_ago = "2020-01-01T00:00:00Z"
        s = self.gh.read()
        s["pulls"][0]["mergedAt"] = long_ago
        self.gh.write(pulls=s["pulls"])
        walk = self.run_office().stdout
        self.assertIn("proj: no review open on a branch the office delivered", walk)
        s["pulls"][0]["mergedAt"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.gh.write(pulls=s["pulls"])
        self.assertIn("proj: #1 merged (health-route", self.run_office().stdout)

    def test_without_gh_or_signed_out_it_is_one_line_never_a_refusal(self):
        proc = self.run_office(extra={"OFFICE_GH_PATH": ""})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("  proj: review state not read: gh is not on this machine\n", proc.stdout)
        self.gh.write(hosts={})
        proc = self.run_office("desk")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("  proj: review state not read: To get started with GitHub CLI, please run:  gh auth login",
                      proc.stdout)

    def test_the_home_screen_row_and_the_digest(self):
        import office_digest as odg
        import office_home as ohome
        self.decide("APPROVED")
        with self.e.this_process():
            got = orev.office_reviews(self.root)
            self.assertEqual(orev.project_words(got[0], cites=False), "#1 approved (health-route)")
            page = odg.reviews_section(self.root)
        self.assertEqual(page, ["## Reviews", "", f"- proj: #1 approved (health-route, {self.cite})"])
        # The home screen's page, as bin/office runs it, off a terminal.
        menu = self.e.tmp / "menu"
        run = subprocess.run(
            [sys.executable, "-B", str(pathlib.Path(ohome.__file__)), "page", str(self.root), "--today", "2026-11-02",
             "--tz", "UTC", "--skew", "current", "--founded", "yes", "--menu-file", str(menu)],
            env=self.e.env, capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertRegex(run.stdout, r"\n  proj  .*; reviews: #1 approved \(health-route\)\n")


# --- 3. an added delivery's base is the pull request's -----------------------------------------------

class TestTheBaseIsThePullRequests(GhCase):
    def setUp(self):
        super().setUp()
        self.coworker({"src/picks.py": "picks = 1\n"}, "Start the picklists", branch="picklists")
        self.gh.add_pull(7, "picklists", base="release")

    def test_adopted_the_question_shows_the_requests_base(self):
        proc = self.deliver("--branch", "picklists", "--adopt", "--no-open-review")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("  from:     release, the base of the pull request #7 on picklists, not proj's declared base "
                      "main\n", proc.stdout)
        self.assertIn(", from release (", proc.stdout)
        self.assertIn(f"the review that carries it: #7 https://{REPO_SLUG}/pull/7", proc.stdout)
        self.assertEqual(self.gh.calls_of("pr", "create"), [])
        # The delivered line is as it was; nothing records a review here.
        self.assertIn("delivered: picklists on origin of proj: sessions", self.folder_md())
        self.assertIn("; adopted\n", self.folder_md())

    def test_without_gh_the_projects_base_and_one_line(self):
        proc = self.deliver("--branch", "picklists", "--adopt", extra={"OFFICE_GH_PATH": ""})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(", from main (", proc.stdout)
        self.assertIn("  from:     main (the pull request's base was not read: gh is not on this machine)\n",
                      proc.stdout)


# --- 4. the survey records gh ------------------------------------------------------------------------

class TestTheSurveyRecordsGh(GhCase):
    def test_found_or_not(self):
        page = self.root / "floor-plan" / "survey.md"
        self.run_office("survey", "--no-commit", check=0)
        self.assertIn("- gh: not found\n", page.read_text())
        self.run_office("survey", "--no-commit", extra={"OFFICE_SURVEY_PATH": str(self.gh.dir)}, check=0)
        self.assertIn(f"- gh: gh version 2.45.0 (2024-03-04) ({self.gh.dir / 'gh'})\n", page.read_text())


# --- 6. letterhead check --delivery reads the page as deliver does -------------------------------------

class TestTheCheckReadsADeliveryAsDeliverDoes(GhCase):
    def test_a_page_filed_before_0_35_0(self):
        page = self.root / self.folder / "delivery.md"
        page.write_text(page.read_text().replace("# Delivery: health route\n",
                                                 f"# Delivery: health route\n\n<!-- filed by office land from "
                                                 f"{SID} -->\n"))
        git(self.root, "commit", "-qam", "a page filed before 0.35.0", env=self.e.env)
        whole = self.run_office("letterhead", "check", "--words", str(page))
        self.assertEqual(whole.returncode, 1, whole.stderr)
        self.assertIn(SID, whole.stdout)
        read = self.run_office("letterhead", "check", "--delivery", str(page))
        self.assertEqual(read.returncode, 0, read.stdout + read.stderr)
        self.assertIn("the to: line and the Commit and Review sections are read", " ".join(read.stderr.split()))
        # Through --on PROJECT too, and a hit in what leaves is a hit.
        phrase = "in sum" + "mary"  # the phrasing rule's, spelled apart so this file is not held to it
        page.write_text(page.read_text().replace("One route and its test.", f"One route, and {phrase} its test."))
        git(self.root, "commit", "-qam", "a hit", env=self.e.env)
        on = self.run_office("letterhead", "check", "--on", "proj", "--delivery", str(page))
        self.assertEqual(on.returncode, 1, on.stdout + on.stderr)
        self.assertIn(phrase, on.stdout)


# --- 7. the branch's name against the marks -------------------------------------------------------------

class TestTheBranchNameIsHeldToTheMarks(GhCase):
    def test_a_name_the_letterhead_refuses_never_leaves(self):
        before = self.audience_refs()
        proc = self.deliver("--branch", f"bale/{SID}")
        self.assertEqual(proc.returncode, 1)
        err = " ".join(proc.stderr.split())
        self.assertIn(f"the delivery branch would be bale/{SID} (--branch names it), and the letterhead refuses its "
                      "name: marks:", err)
        self.assertIn("nothing was fetched or made", err)
        self.assertIn("name another: --branch NAME", err)
        self.assertNotIn("fetching origin's main", err)
        self.assertEqual(self.audience_refs(), before)

    def test_a_slug_ending_in_three_digits_reads_as_a_session_id(self):
        other = self.run_office("open", "health route 002", "--lane", "proj: src", check=0).stdout.strip()
        name = other.split("/")[1]
        self.run_office("sessions", name, SID, check=0)
        (self.root / other / "delivery.md").write_text((self.root / self.folder / "delivery.md").read_text())
        git(self.root, "add", "-A", env=self.e.env)
        git(self.root, "commit", "-qm", "words", env=self.e.env)
        proc = self.run_office("deliver", name, "--yes")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("it ends in three digits, as a session id does", " ".join(proc.stderr.split()))
        # Named by the occupant, the same name is his to give.
        proc = self.run_office("deliver", name, "--yes", "--branch", "health-route-002", "--others-too")
        self.assertNotIn("three digits", proc.stderr)

    def test_the_rule_as_a_unit(self):
        with Env(self).this_process():
            rules = odl.office_rules(self.root)
        self.assertEqual(odl.branch_marks("health-route", rules, "slug"), [])
        self.assertEqual(odl.branch_marks("fix-123", rules, "flag"), [])
        self.assertTrue(odl.branch_marks("fix-123", rules, "slug"))
        self.assertTrue(any(m.startswith("names:") for m in odl.branch_marks("cla" "ude-fix", rules, "flag")))


class TestTheUnits(unittest.TestCase):
    def test_the_door_looks_only_where_the_environment_says(self):
        e = Env(self)
        d = e.tmp / "bin"
        d.mkdir()
        (d / "gh").write_text("#!/bin/sh\n")
        (d / "gh").chmod(0o755)
        self.assertIsNone(orev.gh_program({"OFFICE_GH_PATH": "", "PATH": str(d)}))
        self.assertEqual(orev.gh_program({"OFFICE_GH_PATH": f"{e.tmp}{os.pathsep}{d}"}), str(d / "gh"))
        self.assertEqual(orev.gh_program({"PATH": str(d)}), str(d / "gh"))
        self.assertEqual(e.env["OFFICE_GH_PATH"], "")

    def test_logins_states_and_the_line(self):
        self.assertEqual(orev.login_of("@pat-reviewer"), "pat-reviewer")
        for not_one in ("Pat Reviewer", "pat@example.org", "a--b", "", None, "-x"):
            self.assertIsNone(orev.login_of(not_one), not_one)
        for pr, words in (({"number": 3, "state": "OPEN", "reviewDecision": "APPROVED"}, "#3 approved"),
                          ({"number": 3, "state": "OPEN", "reviewDecision": "CHANGES_REQUESTED"},
                           "#3 changes requested"),
                          ({"number": 3, "state": "OPEN", "reviewDecision": ""}, "#3 review pending"),
                          ({"number": 3, "state": "MERGED"}, "#3 merged"), ({"number": 3, "state": "CLOSED"},
                                                                            "#3 closed")):
            self.assertEqual(orev.state_words(pr), words)
        self.assertEqual(orev.repo_of(REMOTE), (GH_HOST, REPO_SLUG))
        self.assertIsNone(orev.repo_of("git@gitlab.example.org:acme/proj.git"))
        self.assertEqual(orev.number_of(f"https://{REPO_SLUG}/pull/12"), 12)
        text = orev.review_text("health-route", "origin", "proj", 12, f"https://{REPO_SLUG}/pull/12")
        self.assertEqual(orev.REVIEW_RE.match(text).group("number"), "12")
        self.assertIn("review", h.HISTORY_VERBS)
        self.assertEqual(orev.shown_line(orev.create_argv(REPO_SLUG, "main", "x", "A title")),
                         f"gh pr create --repo {REPO_SLUG} --base main --head x --title 'A title' --body-file "
                         "<the review's body> ")


if __name__ == "__main__":
    unittest.main()
