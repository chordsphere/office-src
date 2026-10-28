"""Tests for clean delivery (office-src 0.25.0), session 3 of the
front-door arc: landing and delivery hold the audience line by default.

1. The letterhead refuses the em dash, the en dash and the ellipsis in an
   office that has one, each named; a lift is never silent.
2. A repository's own pull-request template is exempt from the phrasing
   rule, as the repository holds it; what is added or changed is not.
3. The voice page: the letterhead's templates, its arrival, office
   status and office upgrade.
4. Every commit deliver pushes is shown whole and carries the declared
   author; the author is asked once and kept; office land reviews what
   landed against the letterhead and refuses nothing.
5. The push guard refuses every ref but the one delivery branch, tags
   and bale's refs included, whatever the push's form; an older guard is
   named and replaced.
6. A project with an audience is worked from a guarded clone on this
   machine; a host declared for it is where it validates.

Most are units; one command test per outcome. Every remote a test
pushes to is a bare repository the test made. Run with the rest of the
suite:

    tests/run.sh test_clean_delivery
"""

import os
import pathlib
import re
import subprocess
import sys
import tarfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import LandCase, response_tarball  # noqa: E402
from test_project_on_host import HOST  # noqa: E402
from test_audience_line import AudienceCase, SID, SID2, WORDS, git  # noqa: E402

import office_deliver as odl  # noqa: E402
import office_host as ohost  # noqa: E402
import office_letterhead as olh  # noqa: E402

RULES = REPO / "share" / "letterhead.toml"
EM, EN, ELL = "—", "–", "…"
# The first push guard, as 0.17.0 wrote it: the mark and no version line.
OLD_GUARD = """#!/bin/sh
# office push guard (office-src): a push to this project's audience goes through
# office deliver, which pushes one delivery branch and nothing else.
audience='origin'
audience_url='{url}'
remote="$1"; url="$2"
if [ "$remote" != "$audience" ] && [ "$url" != "$audience_url" ]; then exit 0; fi
if [ -n "${{OFFICE_DELIVERY:-}}" ]; then exit 0; fi
echo "[office] refused: by hand" >&2
exit 1
"""


def repo_with(root, files, env):
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q", "-b", "main", env=env)
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    git(root, "add", "-A", env=env)
    git(root, "commit", "-qm", "Initial commit", env=env)
    return root


# --- 1. the dashes ---------------------------------------------------------------------------------

class TestTheDashes(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.letterhead = self.e.tmp / "office" / "letterhead"
        self.letterhead.mkdir(parents=True)
        self.repo = repo_with(self.e.tmp / "r", {"ok.txt": "fine\n"}, self.e.env)

    def rules(self):
        return olh.apply_letterhead(olh.load_rules_toml(RULES), self.letterhead, "letterhead")

    def test_the_catalog_names_three_and_applies_them_only_with_a_letterhead(self):
        rules = olh.load_rules_toml(RULES)
        self.assertEqual(rules["character_catalog"], [["em dash", EM], ["en dash", EN], ["ellipsis", ELL]])
        self.assertEqual(rules["characters"], [])
        self.assertTrue(RULES.read_text().isascii())
        nowhere = olh.apply_letterhead(olh.load_rules_toml(RULES), self.e.tmp / "no-such-office" / "letterhead")
        self.assertEqual(nowhere["characters"], [])
        self.assertIsNone(nowhere["letterhead"])
        self.assertEqual(len(self.rules()["characters"]), 3)

    def test_each_refusal_names_the_file_the_line_and_the_character(self):
        (self.repo / "w.md").write_text(f"one {EM} two\nthree {EN} four\nfive{ELL}\nplain\n")
        hits, told = olh.check(str(self.repo), self.rules())
        self.assertEqual(olh.render(hits), [
            f"w.md:1: character: the em dash (U+2014) in: one {EM} two",
            f"w.md:2: character: the en dash (U+2013) in: three {EN} four",
            f"w.md:3: character: the ellipsis (U+2026) in: five{ELL}",
        ])
        self.assertIn("the letterhead refuses the em dash (U+2014), the en dash (U+2013) and the ellipsis "
                      "(U+2026) by default (letterhead)", told)
        # Outside an office with a letterhead they are not refused.
        hits, _ = olh.check(str(self.repo), olh.load_rules_toml(RULES))
        self.assertEqual(hits, [])

    def test_a_lift_by_name_is_said_and_a_name_that_is_none_refuses_to_run(self):
        (self.letterhead / "forbidden.txt").write_text("# the list\nAcme Internal\nlift: Em  Dash\n")
        rules = self.rules()
        self.assertEqual([n for n, _ in rules["characters"]], ["en dash", "ellipsis"])
        self.assertEqual(rules["lifted"], [["em dash", "letterhead/forbidden.txt:3"]])
        self.assertEqual(rules["forbidden"], ["Acme Internal"])
        (self.repo / "w.md").write_text(f"a {EM} b {ELL}\n")
        hits, told = olh.check(str(self.repo), rules)
        self.assertEqual([h[3] for h in hits], ["the ellipsis (U+2026)"])
        self.assertIn("the letterhead lifts the em dash (letterhead/forbidden.txt:3), so it is not refused", told)
        (self.letterhead / "forbidden.txt").write_text("lift: hyphen\n")
        with self.assertRaises(olh.CheckError) as cm:
            self.rules()
        self.assertIn("letterhead/forbidden.txt:1: a lift names one of the characters", str(cm.exception))
        self.assertIn("not 'hyphen'", str(cm.exception))

    def test_the_rules_travel_to_a_host_as_json_with_the_characters(self):
        import json
        (self.repo / "w.md").write_text(f"x {EN} y\n")
        proc = subprocess.run([sys.executable, "-", "--rules-json", json.dumps(self.rules()), "."], cwd=self.repo,
                              capture_output=True, text=True, env=self.e.env,
                              input=(REPO / "lib" / "office_letterhead.py").read_text())
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("w.md:1: character: the en dash (U+2013)", proc.stdout)

    def test_the_command_refuses_them_in_an_office_with_a_letterhead(self):
        root = self.e.init()
        (self.repo / "w.md").write_text(f"done {EM} mostly\n")
        proc = self.e.run("letterhead", "check", str(self.repo), cwd=root, check=0)
        self.assertNotIn("character", proc.stdout)  # no letterhead yet: not refused
        (root / "letterhead").mkdir()
        proc = self.e.run("letterhead", "check", str(self.repo), cwd=root)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn(f"w.md:1: character: the em dash (U+2014) in: done {EM} mostly", proc.stdout)
        self.assertIn("by default", proc.stderr)


# --- 2. the pull-request template -------------------------------------------------------------------

TEMPLATE = "## Summary of changes:\n\n<!-- What changed, and why. -->\n\n## Key takeaways:\n"


class TestThePullRequestTemplate(unittest.TestCase):
    def test_the_places_git_hosts_read_one_from(self):
        for path in ("pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md", "docs/pull_request_template.md",
                     ".github/pull_request_template/feature.md", "PULL_REQUEST_TEMPLATE/bug.txt",
                     ".gitlab/merge_request_templates/Default.md", ".azuredevops/pull_request_template.md",
                     ".vsts/pull_request_template/branches/main.md", "pull_request_template"):
            self.assertTrue(olh.is_pr_template(path), path)
        for path in ("src/pull_request_template.md", ".github/ISSUE_TEMPLATE/bug.md", "README.md",
                     ".github/pull_request_template/deep/x.md", ".gitlab/issue_templates/a.md",
                     ".github/pull_request_template/notes.py"):
            self.assertFalse(olh.is_pr_template(path), path)

    def test_its_lines_as_the_repo_holds_them_are_exempt_from_the_phrasing_rule_alone(self):
        e = Env(self)
        repo = repo_with(e.tmp / "r", {".github/pull_request_template.md": TEMPLATE, "a.txt": "a\n"}, e.env)
        words = e.tmp / "words.md"
        words.write_text("# Delivery\n\n## Summary of changes:\n\nIn summary, it works.\n\n## Key takeaways: none\n"
                         "## Key takeaways:\n")
        hits, told = olh.check(str(repo), olh.load_rules_toml(RULES), words=[str(words)])
        shown = olh.render(hits)
        # The template's lines as it holds them: not held to phrasing.
        self.assertFalse(any(":3:" in s for s in shown), shown)
        self.assertFalse(any(":8:" in s for s in shown), shown)
        # What the words add is.
        self.assertTrue(any(":5: phrasing: 'In summary'" in s for s in shown), shown)
        self.assertTrue(any("2 line(s) are the repository's pull-request template's" in t
                            and ".github/pull_request_template.md at HEAD" in t for t in told), told)
        # Every other rule still reads a template's line.
        (repo / ".github" / "pull_request_template.md").write_text(TEMPLATE + f"Made with {'cla' + 'ude'}\n")
        git(repo, "commit", "-qam", "template", env=e.env)
        words.write_text(f"Made with {'cla' + 'ude'}\n")
        hits, _ = olh.check(str(repo), olh.load_rules_toml(RULES), words=[str(words)])
        self.assertEqual([x[2] for x in hits], ["names"])
        # A rev that does not resolve reads HEAD; no git repo, no exemption.
        lines, paths, rev = olh.pr_template_lines(str(repo), "refs/remotes/origin/main")
        self.assertEqual((paths, rev), ([".github/pull_request_template.md"], "HEAD"))


class TestTheTemplateAtDelivery(AudienceCase):
    def test_deliver_reads_the_template_as_the_audience_holds_it_and_refuses_a_dash_by_name(self):
        cow = self.e.tmp / "cow"
        git(self.e.tmp, "clone", "-q", str(self.audience), str(cow), env=self.e.env)
        (cow / ".github").mkdir()
        (cow / ".github" / "pull_request_template.md").write_text(TEMPLATE)
        git(cow, "add", "-A", env=self.e.env)
        git(cow, "commit", "-qm", "Add a template", env=self.e.env)
        git(cow, "push", "-q", "origin", "main", env=self.e.env)
        filled = WORDS.replace("One route and its test.", "## Summary of changes:\n\nOne route and its test.\n\n"
                                                           "## Key takeaways:\n\nNone.")
        # The em dash, refused by name, with nothing pushed.
        before = self.audience_refs()
        self.write_words(filled.replace("One route and its test.", f"One route {EM} and its test."))
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertRegex(proc.stdout, r"delivery\.md:\d+: character: the em dash \(U\+2014\) in: One route")
        self.assertEqual(self.audience_refs(), before)
        # The same words without it: the template's lines pass, and the
        # commit is shown whole before the push.
        self.write_words(filled)
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("are the repository's pull-request template's", proc.stdout)
        self.assertRegex(proc.stdout, r"[0-9a-f]{12}, author Zed Zee <z@example.org>, committer Zed Zee <z@example.org>")
        self.assertIn("files: M src/a.py; A src/health.py", proc.stdout)
        self.assertIn("letterhead: clean", proc.stdout)
        log = git(self.audience, "log", "-1", "--format=%an <%ae>|%cn <%ce>", "health-route", env=self.e.env).strip()
        self.assertEqual(log, "Zed Zee <z@example.org>|Zed Zee <z@example.org>")


# --- 3. the voice page ------------------------------------------------------------------------------

class TestTheVoicePage(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_the_templates(self):
        voice = (REPO / "templates" / "letterhead-voice.md").read_text()
        self.assertIn("## In the occupant's words", voice)
        self.assertIn(odl.VOICE_EMPTY_MARK, voice)
        forbidden = (REPO / "templates" / "letterhead-forbidden.txt").read_text()
        for name in ("em dash (U+2014)", "en dash (U+2013)", "ellipsis character (U+2026)", "lift: em dash"):
            self.assertIn(name, forbidden.replace("\n# ", " "))
        self.assertEqual(olh.forbidden_lines(forbidden), [])  # comments only: nothing forbidden, nothing lifted
        self.assertIn("voice.md", (REPO / "templates" / "letterhead-README.md").read_text())
        for name in odl.LETTERHEAD_PAGES.values():
            self.assertTrue((REPO / "templates" / name).read_text().isascii(), name)

    def test_it_arrives_whole_once_and_never_rewrites_a_page(self):
        with self.e.this_process():
            changed, words = odl.letterhead_arrive(self.root)
        self.assertEqual(sorted(changed), ["bale.toml", "floor-plan/manifest.toml", "letterhead/README.md",
                                           "letterhead/forbidden.txt", "letterhead/voice.md"])
        self.assertIn("the letterhead arrives in this office", words[0])
        self.assertIn("[spaces.letterhead]", (self.root / "floor-plan" / "manifest.toml").read_text())
        (self.root / "letterhead" / "forbidden.txt").write_text("Acme\n")
        (self.root / "letterhead" / "voice.md").unlink()
        with self.e.this_process():
            changed, _ = odl.letterhead_arrive(self.root)
        self.assertEqual(changed, ["letterhead/voice.md"])
        self.assertEqual((self.root / "letterhead" / "forbidden.txt").read_text(), "Acme\n")
        self.assertEqual(odl.voice_state(self.root)[0], "empty")
        (self.root / "letterhead" / "voice.md").write_text("# Voice\n\n## In the occupant's words\n\nShort.\n")
        self.assertEqual(odl.voice_state(self.root)[0], "written")

    def test_status_names_its_absence_and_upgrade_adds_it(self):
        (self.root / "letterhead").mkdir()
        (self.root / "letterhead" / "forbidden.txt").write_text("Acme\n")
        self.e.git(self.root, "add", "-A")
        self.e.git(self.root, "commit", "-qm", "a letterhead from an earlier release")
        proc = self.e.run("status", cwd=self.root, check=0)
        self.assertIn("letterhead: refuses the em dash, the en dash and the ellipsis by default; "
                      "letterhead/voice.md is missing: office upgrade adds it from the install's template", proc.stdout)
        proc = self.e.run("upgrade", cwd=self.root, check=0)
        self.assertIn("made letterhead/voice.md from the install's template", proc.stderr)
        self.assertTrue((self.root / "letterhead" / "voice.md").is_file())
        self.assertEqual((self.root / "letterhead" / "forbidden.txt").read_text(), "Acme\n")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertIn("office upgrade", self.e.git(self.root, "log", "-1", "--format=%s"))
        proc = self.e.run("upgrade", cwd=self.root, check=0)
        self.assertIn("nothing to upgrade", proc.stderr)
        self.assertIn("holds no words of the occupant's yet", self.e.run("status", cwd=self.root, check=0).stdout)


# --- 4. the commits, the author, the review at land -------------------------------------------------

class TestTheCommits(unittest.TestCase):
    def test_each_commit_is_read_back_whole_and_its_identity_checked(self):
        e = Env(self)
        repo = repo_with(e.tmp / "r", {"a.txt": "a\n"}, e.env)
        start = git(repo, "rev-parse", "HEAD", env=e.env).strip()
        (repo / "b.txt").write_text("b\n")
        git(repo, "add", "-A", env=e.env)
        ident = dict(e.env, GIT_AUTHOR_NAME="Zed Zee", GIT_AUTHOR_EMAIL="z@example.org",
                     GIT_COMMITTER_NAME="Zed Zee", GIT_COMMITTER_EMAIL="z@example.org")
        git(repo, "commit", "-qm", "Add b\n\nIt is b.", env=ident)
        rules = olh.apply_letterhead(olh.load_rules_toml(RULES), e.tmp / "letterhead")
        with e.this_process():
            shown, hits = odl.read_commits(repo, start, rules)
            self.assertEqual(hits, [])
            (c,) = shown
            self.assertEqual((c["subject"], c["body"], c["author"], c["committer"], c["files"], c["verdict"]),
                             ("Add b", "It is b.", "Zed Zee <z@example.org>", "Zed Zee <z@example.org>",
                              ["A b.txt"], "clean"))
            odl.check_identities(repo, start, "Zed Zee <z@example.org>")
            (repo / "c.txt").write_text("c\n")
            git(repo, "add", "-A", env=e.env)
            git(repo, "commit", "-qm", f"Add c {EN} now", env=dict(ident, GIT_COMMITTER_NAME="Clone Own"))
            with self.assertRaises(odl.DeliverError) as cm:
                odl.check_identities(repo, start, "Zed Zee <z@example.org>")
            self.assertIn("'s committer is Clone Own <z@example.org>, not Zed Zee <z@example.org>",
                          "\n".join(cm.exception.lines))
            (e.tmp / "letterhead").mkdir()
            rules = olh.apply_letterhead(olh.load_rules_toml(RULES), e.tmp / "letterhead")
            shown, hits = odl.read_commits(repo, start, rules)
            self.assertEqual(shown[1]["verdict"][0].split(": ", 1)[1],
                             f"character: the en dash (U+2013) in: Add c {EN} now")


class TestTheAuthorOnATerminal(AudienceCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_a_project_with_no_author_is_asked_once_and_keeps_it(self):
        self.run_office("projects", "set", "proj", "--no-author", check=0)
        git(self.clone, "config", "user.name", "Clone Own", env=self.e.env)
        git(self.clone, "config", "user.email", "own@example.org", env=self.e.env)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "deliver", self.name], self.root, self.e.env, [
            (b"kept for every delivery (--author):", "Clone Own"),
            (b"an author is written as git writes one", "Pat Example <pat@example.org>"),
            (b"Push health-route to origin as shown? (--yes) (y/n) [y]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("the clone's own identity is never used silently: the clone's is Clone Own <own@example.org>", seen)
        self.assertIn('author = "Pat Example <pat@example.org>"', (self.root / "floor-plan" / "manifest.toml").read_text())
        self.assertEqual(self.audience_log().splitlines()[0].split("|")[:2], ["Pat Example <pat@example.org>", "Pat Example"])


class TestTheReviewAtLand(LandCase):
    def test_land_says_what_deliver_would_refuse_and_refuses_nothing(self):
        audience = self.e.tmp / "alpha-audience.git"
        git(self.e.tmp, "init", "-q", "--bare", str(audience), env=self.e.env)
        git(self.proj, "remote", "add", "origin", str(audience), env=self.e.env)
        proc = self.run_office("projects", "set", "alpha", "--audience", "origin", "--author", "Pat <pat@example.org>",
                               "--base", "main", check=0)
        self.assertIn("the letterhead arrives in this office", proc.stderr)
        # The letterhead rides beside a session on a project with an audience.
        start = self.run_office("start", self.name, "--on", "alpha", "--goal", "g", "--write", "src", check=0)
        sid = re.search(r"^Packed (\S+) for ", start.stdout, re.M).group(1)
        self.assertIn("the letterhead (its voice page first: alpha has an audience)", start.stdout)
        tray = pathlib.Path(re.search(r"^Out tray: (.+)$", start.stdout, re.M).group(1))
        names = []
        for t in tray.glob("context-*.tar.gz"):
            with tarfile.open(t) as tf:
                names += tf.getnames()
        self.assertTrue(any(n.endswith("letterhead/voice.md") for n in names), names)
        response_tarball(self.downloads, sid, {"src/a.py": f"fixed {EM} mostly\n"})
        proc = self.run_office("land", sid, "--leave-open", check=0)
        self.assertIn(f"Landed: {sid}", proc.stdout)
        self.assertIn(f"letterhead: office deliver would refuse 1 line(s) of {sid}'s landing", proc.stderr)
        self.assertIn(f"src/a.py:1: character: the em dash (U+2014) in: fixed {EM} mostly", proc.stderr)
        self.assertIn("nothing is refused at land", proc.stderr)
        self.assertTrue((self.proj / "AFTER-LAND-RAN").is_file())


# --- 5. the push guard ---------------------------------------------------------------------------------

class TestThePushGuard(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.audience = self.e.tmp / "aud.git"
        git(self.e.tmp, "init", "-q", "--bare", str(self.audience), env=self.e.env)
        self.clone = repo_with(self.e.tmp / "c", {"f": "x\n"}, self.e.env)
        git(self.clone, "remote", "add", "origin", str(self.audience), env=self.e.env)
        git(self.clone, "tag", "applied/2026-10-16-alpha-report-001", env=self.e.env)
        git(self.clone, "tag", "-a", "-m", "v1", "v1", env=self.e.env)
        git(self.clone, "branch", "bale/2026-10-16-alpha-report-001", env=self.e.env)

    def push(self, *args, delivery=None):
        env = dict(self.e.env, **({ohost.DELIVERY_ENV: delivery} if delivery else {}))
        return subprocess.run(["git", "-C", str(self.clone), "push", *args], capture_output=True, text=True, env=env)

    def refs(self):
        return git(self.audience, "for-each-ref", "--format=%(refname)", env=self.e.env).split()

    def test_nothing_but_the_delivery_branch_reaches_the_audience_whatever_the_form(self):
        with self.e.this_process():
            ohost.install_push_guard(ohost.Place(str(self.clone)), "origin", str(self.audience))
            facts = ohost.git_facts(ohost.Place(str(self.clone)))
        self.assertEqual((facts["guard"], facts["guard_version"]), ("office", ohost.GUARD_VERSION))
        self.assertEqual(ohost.guard_state(facts)[0], "current")
        git(self.clone, "remote", "add", "alias", f"file://{self.audience}/", env=self.e.env)
        forms = [("origin", "--tags"), ("origin", "--all"), ("origin", "--mirror"), ("origin", "v1"),
                 ("origin", "applied/2026-10-16-alpha-report-001"), ("origin", "bale/2026-10-16-alpha-report-001"),
                 ("origin", "main:refs/heads/feature"), ("alias", "main"), (str(self.audience) + "/", "--tags")]
        for args in forms:
            proc = self.push(*args)
            self.assertNotEqual(proc.returncode, 0, args)
            self.assertIn("only office deliver reaches it", proc.stderr, args)
        self.assertEqual(self.refs(), [])
        # Under deliver's variable: the one branch, and no tag or bale ref with it.
        proc = self.push("origin", "main:refs/heads/report", "v1", delivery="report")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("refs/tags/v1 (it is a tag)", proc.stderr)
        proc = self.push("origin", "bale/2026-10-16-alpha-report-001", delivery="bale/2026-10-16-alpha-report-001")
        self.assertIn("which is not a delivery branch", proc.stderr)
        self.assertEqual(self.refs(), [])
        proc = self.push("origin", "main:refs/heads/report", delivery="report")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.refs(), ["refs/heads/report"])
        proc = self.push("origin", ":refs/heads/report", delivery="report")
        self.assertIn("refs/heads/report (it deletes a ref)", proc.stderr)
        self.assertEqual(self.refs(), ["refs/heads/report"])
        # Another remote is not the guard's business.
        other = self.e.tmp / "other.git"
        git(self.e.tmp, "init", "-q", "--bare", str(other), env=self.e.env)
        self.assertEqual(self.push(str(other), "--tags").returncode, 0)

    def test_an_older_guard_is_named_and_replaced(self):
        hook = self.clone / ".git" / "hooks" / "pre-push"
        hook.write_text(OLD_GUARD.format(url=self.audience))
        hook.chmod(0o755)
        with self.e.this_process():
            facts = ohost.git_facts(ohost.Place(str(self.clone)))
            self.assertEqual((facts["guard"], facts["guard_version"]), ("office", 1))
            project = {"name": "alpha", "audience": "origin", "host": None, "path": str(self.clone),
                       "resolved": self.clone, "shell": None, "connect": None, "problem": None}
            state, line = odl.guard_line(project, ohost.Place(str(self.clone)), facts)
            self.assertEqual(state, "older")
            self.assertIn("an older push guard (version 1)", line)
            self.assertIn("office upgrade, or office projects set alpha, replaces it", line)
            changed, line = odl.refresh_guard(project)
            self.assertTrue(changed, line)
            self.assertEqual(ohost.git_facts(ohost.Place(str(self.clone)))["guard_version"], ohost.GUARD_VERSION)
            changed, _ = odl.refresh_guard(project)
            self.assertFalse(changed)
        self.assertNotEqual(self.push("origin", "--tags").returncode, 0)

    def test_status_names_it_and_projects_set_replaces_it(self):
        root = self.e.init()
        (self.clone / ".bale").mkdir()
        self.e.run("projects", "add", "alpha", str(self.clone), "--audience", "origin", cwd=root, check=0)
        hook = self.clone / ".git" / "hooks" / "pre-push"
        hook.write_text(OLD_GUARD.format(url=self.audience))
        proc = self.e.run("status", cwd=root, check=0)
        self.assertIn("guard:      alpha: an older push guard (version 1)", proc.stdout)
        proc = self.e.run("projects", "set", "alpha", cwd=root, check=0)
        self.assertIn("push guard installed", proc.stderr)
        self.assertIn(f"guard_version={ohost.GUARD_VERSION}", hook.read_text())
        self.assertIn("guard:      alpha: the push guard, version", self.e.run("status", cwd=root, check=0).stdout)


# --- 6. the workbench on this machine -----------------------------------------------------------------

class TestTheWorkbenchHere(unittest.TestCase):
    def test_a_host_declared_with_an_audience_is_where_it_validates(self):
        e = Env(self)
        root = e.init()
        audience = e.tmp / "aud.git"
        git(e.tmp, "init", "-q", "--bare", str(audience), env=e.env)
        clone = repo_with(e.tmp / "beta", {"f": "x\n"}, e.env)
        git(clone, "remote", "add", "origin", str(audience), env=e.env)
        (clone / ".bale").mkdir()
        proc = e.run("projects", "add", "beta", str(clone), "--audience", "origin", "--host", HOST,
                     "--connect", "x", cwd=root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("add --worked-on-host to work it there", proc.stderr)
        proc = e.run("projects", "add", "beta", str(clone), "--validates-on", HOST, cwd=root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--validates-on goes with --audience REMOTE", proc.stderr)
        proc = e.run("projects", "add", "beta", str(clone), "--audience", "origin", "--host", HOST, cwd=root, check=0)
        self.assertIn(f"worked on this machine, from a guarded clone, and {HOST} is kept for validation only", proc.stderr)
        self.assertIn("push guard installed", proc.stderr)
        self.assertTrue((clone / ".git" / "hooks" / "pre-push").is_file())
        text = (root / "floor-plan" / "manifest.toml").read_text()
        self.assertIn(f'validates_on = "{HOST}"', text)
        self.assertNotIn("host = ", text)
        self.assertIn(f"validates on: {HOST}, not where it is worked (on this machine)", e.run("projects", cwd=root, check=0).stdout)
        entry = next(p for p in h.read_projects(h.read_toml(root / "floor-plan" / "manifest.toml")) if p["name"] == "beta")
        self.assertEqual((entry["host"], entry["validates_on"]), (None, HOST))
        proc = e.run("projects", "set", "beta", "--no-validates-on", cwd=root, check=0)
        self.assertNotIn("validates_on", (root / "floor-plan" / "manifest.toml").read_text())
        self.assertTrue((root / "letterhead" / "voice.md").is_file())


# --- 0.32.0, the M10 tidy: a ticked checklist line, and the delivery's dates ---------------------------

# A template's checklist, as a repository holds it: unticked. The first
# line is the M10 walkthrough's, which the phrasing rule refuses as the
# occupant's writing; the second holds an em dash, which an office with a
# letterhead refuses; the third a string the office's forbidden list holds.
CHECKLIST = ("## Checklist\n\n"
             "- [ ] I have updated the documentation accordingly.\n"
             f"* [ ] Tests {EM} added or not needed\n"
             "1. [ ] Acme Internal sign-off\n")


class TestATickedTemplateLine(unittest.TestCase):
    """0.32.0: a checklist line is the template's whatever its box holds.
    The template's lines and the words' are compared with the box's state
    folded, so a ticked line is as exempt as the unticked one; words added
    after the box make a changed line, held to everything; names, bale's
    marks and the forbidden list still read a ticked one."""

    def setUp(self):
        self.e = Env(self)
        self.repo = repo_with(self.e.tmp / "r", {".github/pull_request_template.md": CHECKLIST, "a.txt": "a\n"},
                              self.e.env)
        letterhead = self.e.tmp / "office" / "letterhead"
        letterhead.mkdir(parents=True)
        (letterhead / "forbidden.txt").write_text("Acme Internal\n")
        self.rules = olh.apply_letterhead(olh.load_rules_toml(RULES), letterhead, "letterhead")

    def test_the_box_is_folded_and_nothing_else(self):
        key = olh.template_key
        self.assertEqual(key("- [x] I have updated the documentation accordingly.  "),
                         "- [ ] I have updated the documentation accordingly.")
        for ticked, empty in (("- [X] Docs", "- [ ] Docs"), ("  * [x] nested", "  * [ ] nested"),
                              ("+ [x] plus", "+ [ ] plus"), ("1. [x] one", "1. [ ] one"), ("2) [X] two", "2) [ ] two"),
                              ("- [x]", "- [ ]"), ("- [ ] left", "- [ ] left"),
                              ("- [x] - [x] the line's own box only", "- [ ] - [x] the line's own box only")):
            self.assertEqual(key(ticked), empty, ticked)
        # Not a box: only right-stripped.
        for line in ("[x] no bullet", "- [xx] two marks", "- [y] another mark", "-[x] no space", "- [x]tight",
                     "words - [x] later"):
            self.assertEqual(key(line + "  "), line, line)

    def test_a_ticked_line_is_exempt_and_a_changed_one_is_held(self):
        words = self.e.tmp / "words.md"
        words.write_text("## Checklist\n\n"
                         "- [x] I have updated the documentation accordingly.\n"
                         f"* [X] Tests {EM} added or not needed\n"
                         "1. [x] Acme Internal sign-off\n"
                         "- [x] I have updated the documentation accordingly, and the tests.\n")
        hits, told = olh.check(str(self.repo), self.rules, words=[str(words)])
        shown = [(n, kind) for _, n, kind, _, _ in hits]
        # Lines 3 and 4, ticked, are the template's: not held to the
        # phrasing rule or the three characters.
        self.assertNotIn((3, "phrasing"), shown)
        self.assertNotIn((4, "character"), shown)
        # Line 5, ticked: the forbidden list still reads it.
        self.assertIn((5, "forbidden"), shown)
        # Line 6, words added after the box: a changed line, held.
        self.assertIn((6, "phrasing"), shown)
        self.assertEqual(sorted(shown), [(5, "forbidden"), (6, "phrasing")])
        self.assertTrue(any(t.startswith(f"{words}: 4 line(s) are the repository's pull-request template's")
                            for t in told), told)
        # The template unticked reads the same, as it always did.
        words.write_text(CHECKLIST)
        hits, _ = olh.check(str(self.repo), self.rules, words=[str(words)])
        self.assertEqual([(n, kind) for _, n, kind, _, _ in hits], [(5, "forbidden")])

    def test_the_hosted_form_the_module_on_stdin_reads_it_the_same(self):
        import json
        text = "- [x] I have updated the documentation accordingly.\n- [x] I have updated the docs too.\n"
        proc = subprocess.run([sys.executable, "-", "--rules-json", json.dumps(self.rules), "--words-json",
                               json.dumps([["delivery.md", text]]), "."], cwd=self.repo, capture_output=True, text=True,
                              env=self.e.env, input=(REPO / "lib" / "office_letterhead.py").read_text(), timeout=60)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(proc.stdout.splitlines(),
                         ["delivery.md:2: phrasing: 'I have updated the' in: - [x] I have updated the docs too."])
        self.assertIn("delivery.md: 1 line(s) are the repository's pull-request template's", proc.stderr)


class TestTheDeliveryCommitsDates(AudienceCase):
    """0.32.0: a delivery's commits have distinct, ordered dates, each a
    second after the one before, author and committer date alike; the
    question shows each commit's date, and says in one line how many leave
    when the words hold several Commit sections."""

    def test_the_dates_and_the_line_as_units(self):
        dates = odl.commit_dates(3, now=1_800_000_000)
        self.assertEqual([d.split()[0] for d in dates], ["@1800000000", "@1800000001", "@1800000002"])
        for d in dates:
            self.assertRegex(d, r"^@\d+ [+-]\d{4}$")
        self.assertEqual(odl.commit_dates(0), [])
        self.assertIsNone(odl.commits_line(1))
        self.assertEqual(odl.commits_line(3), "3 commits leave in this delivery, dated a second apart, oldest first; "
                                              "one commit per delivery is the usual shape (one Commit section in "
                                              "delivery.md)")

    def test_commit_words_dates_each_commit_a_second_after_the_last(self):
        repo = repo_with(self.e.tmp / "units", {"a.txt": "a\n"}, self.e.env)
        start = git(repo, "rev-parse", "HEAD", env=self.e.env).strip()
        for name in ("b.txt", "c.txt", "d.txt"):
            (repo / name).write_text(name)
        git(repo, "add", "-A", env=self.e.env)
        words = {"commits": [{"subject": "Add b", "body": "", "paths": ["b.txt"]},
                             {"subject": "Add c", "body": "", "paths": ["c.txt"]},
                             {"subject": "Add d", "body": "It is d.", "paths": []}]}
        with self.e.this_process():
            shas = odl.commit_words(repo, words, "Zed Zee <z@example.org>", now=1_800_000_000)
            shown, _ = odl.read_commits(repo, start, olh.load_rules_toml(RULES))
        stamps = git(repo, "log", "--reverse", "--format=%H %at %ct", f"{start}..HEAD", env=self.e.env).split("\n")
        self.assertEqual([s.split() for s in stamps if s],
                         [[sha, str(1_800_000_000 + n), str(1_800_000_000 + n)] for n, sha in enumerate(shas)])
        # The question's rendering reads each date back, author and committer alike.
        self.assertEqual([c["sha"] for c in shown], shas)
        self.assertEqual(len({c["date"] for c in shown}), 3)
        self.assertTrue(all(c["date"] == c["committed"] for c in shown), shown)
        self.assertEqual([c["date"] for c in shown], sorted(c["date"] for c in shown))

    def test_deliver_says_how_many_leave_and_shows_each_date(self):
        self.land_session(SID2, {"docs.md": "# health\n"}, "Document the route")
        self.run_office("sessions", self.name, SID2, check=0)
        self.write_words("# Delivery\n\n## Commit\n\n- paths: docs.md\n\nDocument the health route\n\n"
                         "## Commit\n\nAdd the health route\n\nIts code.\n\n## Review\n\nHealth route\n\nLook.\n")
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("    2 commits leave in this delivery, dated a second apart, oldest first; one commit per "
                      "delivery is the usual shape (one Commit section in delivery.md)\n    commit 1: ", proc.stdout)
        dated = re.findall(r"^      dated (\S+)$", proc.stdout, re.M)
        self.assertEqual(len(dated), 2, proc.stdout)
        stamps = git(self.audience, "log", "--reverse", "--format=%at %ct %aI", "main..health-route",
                     env=self.e.env).split("\n")
        (a1, c1, i1), (a2, c2, i2) = [s.split() for s in stamps if s]
        self.assertEqual((a1, int(a2)), (c1, int(a1) + 1))
        self.assertEqual(c2, a2)
        self.assertEqual(dated, [i1, i2])

    def test_one_commit_is_dated_and_no_line_is_said(self):
        proc = self.run_office("deliver", self.name, "--yes")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertNotIn("commits leave in this delivery", proc.stdout)
        self.assertRegex(proc.stdout, r"\n      dated \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}\n")


# --- the record ----------------------------------------------------------------------------------------

class TestTheRecord(unittest.TestCase):
    def test_the_release_and_the_doctrine(self):
        version = (REPO / "VERSION").read_text().strip()
        # 0.25.0 or later (0.26.0's own record is tests/test_meetings_view.py's).
        self.assertGreaterEqual(h.compare_versions(version, "0.25.0"), 0)
        self.assertIn("## 0.25.0", (REPO / "RELEASES.md").read_text())
        doctrine = (REPO / "doctrine" / "OFFICE.md").read_text()
        for words in ("lift: em dash", "voice page", "pull-request template", "validates_on", "guard_version",
                      "author and committer"):
            self.assertIn(words, doctrine)
        readme = (REPO / "README.md").read_text()
        self.assertIn("0.25.0", readme)


if __name__ == "__main__":
    unittest.main()
