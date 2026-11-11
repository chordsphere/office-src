"""Tests for office-src 0.56.0, practice-rules: the practice written down,
and two small tools.

One class or more per item of the brief (2026-11-10-practice-rules-001):

1. words to the occupant: house rule 5 in the doctrine's core, and the
   sitting, prep and ask briefs say it where they hand him lines;
2. a fix made only to keep the audience barrier is never named: the voice
   page's head, templates/delivery.md, the merge and undo briefs;
3. a project's conventions over the voice page: the handbook chapter's
   `## Conventions`, the doctrine's order, and the briefs that point at it;
4. one pull request per feature from the audience's base: the sitting
   brief and the doctrine where it says the BRANCH line;
5. the sort and drop briefs: a fact may wrap and is filed whole (the
   sort brief's own pin is tests/test_sort.py's
   TestTheSortBriefSaysWriteFactsBare, its bare sentence kept and the
   clause after it);
6. the chat kind retired beside the ask, Q-3 answered;
7. bare `office probe` and the home screen's r key offer the preps out
   beside the folders;
8. `tests/run.sh --fake-day DAY`: the fake bales' default day.

The worlds are the suite's own: tests/test_prep_and_tidy.py's PrepCase
(a meeting on alpha with its prep out), tests/test_land.py's LandCase,
tests/test_probe.py's probe blocks. No day and no version is written
here: a far day is computed from today, and the release is read from
VERSION. Run with the rest of the suite:

    tests/run.sh test_practice_rules
"""

import datetime
import os
import pathlib
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "fakes"))
from test_office import REPO, Env, FAKE_DAY_VAR  # noqa: E402
from test_prep_and_tidy import PrepCase  # noqa: E402
from test_probe import probe_block  # noqa: E402

import office_helper as oh  # noqa: E402
import office_home as hs  # noqa: E402
import office_letterhead as olh  # noqa: E402
import office_sort as osort  # noqa: E402
import pack_bale  # noqa: E402
import runner  # noqa: E402

TEMPLATES = REPO / "templates"
DOCTRINE = REPO / "doctrine/OFFICE.md"


def flat(text):
    return " ".join(text.split())


def core_and_past():
    """The doctrine's core (above the PAST THE CORE banner) and the rest,
    each flattened; the banner's line is pinned by tests/test_office.py."""
    lines = DOCTRINE.read_text(encoding="ascii").splitlines()
    banner = next(i for i, l in enumerate(lines) if l.startswith("> **PAST THE CORE.**"))
    return flat("\n".join(lines[:banner])), flat("\n".join(lines[banner:]))


def section(text, heading):
    """The flattened words of a `## heading` section of a page."""
    lines = text.splitlines()
    start, end = oh.section_bounds(lines, heading)
    return flat("\n".join(lines[start + 1:end])) if start is not None else None


def today():
    """Today on the UTC clock, as the fakes mint it."""
    return datetime.datetime.now(datetime.timezone.utc).date().isoformat()


def far_day():
    """A day far from today, computed, never written: about five years on."""
    return (datetime.datetime.now(datetime.timezone.utc).date() + datetime.timedelta(days=1789)).isoformat()


# --- 1. words to the occupant ------------------------------------------------------------------

STEP_RULE = ("5. Every step handed to the occupant is the exact command and one plain sentence on what it does and "
             "what he will see; no bale or office term goes unexplained at first use. Machinery is explained when "
             "he asks.")
BRIEF_STEP = ("Every step the sitting hands {who} is the exact command and one plain sentence on what it does and "
              "what he will see; a bale or office term gets its plain meaning the first time it appears, and how the "
              "machinery works is explained when he asks (doctrine section 9, rule 5).")


class TestWordsToTheOccupant(unittest.TestCase):
    def test_the_rule_is_section_nines_fifth_inside_the_core(self):
        core, past = core_and_past()
        nine = core.split("## 9. House rules for every office", 1)[1]
        self.assertIn(STEP_RULE, nine)
        self.assertNotIn(STEP_RULE, past)
        # Rule 4 keeps its friction and its slip; rule 1 points at
        # principle 2 rather than saying it twice.
        self.assertIn("4. Anything that asks the occupant for bookkeeping, setup or moving files is friction: say so "
                      "in a suggestion slip.", nine)
        self.assertIn("1. Every session lands something: at minimum a notepad entry and the folder it touched; "
                      "principle 2 says how a sitting's words land.", nine)

    def test_the_sitting_and_prep_briefs_say_it_where_they_hand_him_lines(self):
        sitting = flat((TEMPLATES / "sitting-brief.md").read_text())
        self.assertIn(BRIEF_STEP.format(who="the occupant") + " Every line the sitting hands the occupant to type is "
                      "an office line", sitting)
        prep = flat((TEMPLATES / "prep-brief.md").read_text())
        self.assertIn(BRIEF_STEP.format(who="him") + " Every line the sitting hands him to type is an office line",
                      prep)

    def test_the_ask_brief_says_it_under_its_rule(self):
        text = (TEMPLATES / "ask-brief.md").read_text()
        rule = section(text, "The rule")
        self.assertIn("Every step you hand him is the exact command, or the exact thing to do, and one plain sentence "
                      "on what it does and what he will see. A bale or office term gets its plain meaning the first "
                      "time it appears; how the office or bale works is explained when he asks, not before.", rule)


# --- 2. a cleanup never named -------------------------------------------------------------------

CLEANUP = "(punctuation, phrasing, naming)"


class TestACleanupIsNeverNamed(unittest.TestCase):
    def test_the_voice_pages_head_says_it_and_his_section_is_untouched(self):
        text = (TEMPLATES / "letterhead-voice.md").read_text()
        head = flat(text.split("## In the occupant's words", 1)[0])
        self.assertIn("A fix made only to keep this page, the forbidden list or the letterhead's check "
                      f"{CLEANUP} is shipped clean and never mentioned: not in a commit, a review or a message.", head)
        his = text.split("## In the occupant's words", 1)[1]
        self.assertEqual(his.strip().splitlines()[0], "<!-- EMPTY: the occupant's words go here, as given, and this "
                                                      "comment goes")
        for words in ("shipped clean", "Conventions", "office-src"):
            self.assertNotIn(words, his)

    def test_the_delivery_page_says_it_above_what_leaves(self):
        page = (TEMPLATES / "delivery.md").read_text()
        self.assertIn(f"A fix made only to keep the letterhead {CLEANUP} is shipped clean and never mentioned: no "
                      "commit, review or message says it was made.", flat(page))
        leaving, _ = oh.delivery_leaving_text(page)
        self.assertNotIn("shipped clean", leaving)

    def test_the_merge_and_undo_briefs_say_it_where_they_say_what_ships(self):
        for name, after in (("merge-brief.md", "on the files as you wrote them."),
                            ("undo-brief.md", "where the tree here lets you.")):
            text = flat((TEMPLATES / name).read_text())
            self.assertIn(f"{after} What you ship leaves with ", text, name)
            self.assertIn(f"only to keep the letterhead {CLEANUP} is shipped clean and never mentioned in what "
                          "leaves, a comment in the file included.", text, name)

    def test_no_template_names_a_cleanup_in_words_that_leave(self):
        # What leaves of the delivery page is its to: line and its Commit
        # and Review sections; the cleanup list reads those words alone.
        leaving, _ = oh.delivery_leaving_text((TEMPLATES / "delivery.md").read_text())
        rules = olh.load_rules_toml(REPO / "share/letterhead.toml")
        patterns = [re.compile(p, re.I) for p in rules["cleanup"]]
        for line in leaving.splitlines():
            self.assertFalse([p.pattern for p in patterns if p.search(line)], line)
        # And the new rule's own words name no character.
        for name in ("letterhead-voice.md", "delivery.md", "merge-brief.md", "undo-brief.md"):
            for sentence in re.findall(r"[^.]*shipped clean[^.]*\.", flat((TEMPLATES / name).read_text())):
                self.assertFalse([p.pattern for p in patterns if p.search(sentence)], (name, sentence))


# --- 3. a project's conventions over the brief ----------------------------------------------------

class TestTheConventionsPlace(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.path = self.tmp / "alpha.md"

    def test_the_chapter_template_holds_it_between_the_front_sheet_and_the_facts(self):
        text = osort.render_chapter("alpha")
        heads = [l for l in text.splitlines() if l.startswith("## ")]
        self.assertEqual(heads, ["## Front sheet", "## Conventions", "## Facts"])
        self.assertEqual(section(text, "Conventions"), "None settled yet.")

    def test_land_keeps_settled_conventions_as_it_files_the_front_sheet_and_the_facts(self):
        self.path.write_text(osort.render_chapter("alpha"))
        settled = ["- commits: Conventional Commits, as CONTRIBUTING.md asks", "- review: one per feature, from main"]
        lines = self.path.read_text().splitlines()
        start, end = oh.section_bounds(lines, "Conventions")
        self.path.write_text("\n".join(lines[:start + 1] + [""] + settled + [""] + lines[end:]) + "\n")
        osort.set_front_sheet(self.path, ["alpha is the app."])
        fact = f"- {today()}: the api serves the page ({today()}-job-001)"
        osort.append_facts(self.path, [fact])
        text = self.path.read_text()
        self.assertIn("## Front sheet\n\nalpha is the app.\n\n## Conventions\n\n" + "\n".join(settled) +
                      "\n\n## Facts\n\n" + fact + "\n", text)
        self.assertEqual(osort.chapter_problems(self.path), [])

    def test_a_chapter_without_the_section_reads_as_whole(self):
        self.path.write_text("# alpha\n\n## Front sheet\n\nalpha.\n\n## Facts\n")
        self.assertEqual(osort.chapter_problems(self.path), [])
        self.assertIsNone(section(self.path.read_text(), "Conventions"))
        # No migration writes one.
        migrations = REPO / "migrations"
        for script in sorted(migrations.glob("*")) if migrations.is_dir() else ():
            if script.is_file():
                self.assertNotIn("Conventions", script.read_text(errors="replace"), script.name)

    def test_the_doctrine_says_the_order_in_the_core_and_in_full_past_it(self):
        core, past = core_and_past()
        self.assertIn("the letterhead lifts one. The project's conventions, its handbook chapter's `## Conventions` "
                      "(0.56.0), win over the voice page for the form of what leaves; the voice page keeps the words.",
                      core)
        # 0.57.0: land files a session's set after the occupant's answer
        # (tests/test_offer_and_conventions.py holds the rest of it).
        self.assertIn("`office land` files a session's `#### Conventions` after the occupant's answer, and only "
                      "then (0.57.0).", past)
        self.assertIn("No migration writes them. Where they speak, they win over the voice page for the form of "
                      "what leaves", past)
        self.assertIn("a project session follows what the repository's own CONTRIBUTING says where it speaks, as the "
                      "project's convention, never the voice page over it", past)

    def test_the_front_pages_and_briefs_point_at_it(self):
        readme = flat((TEMPLATES / "handbook-README.md").read_text())
        self.assertIn("Three parts.", readme)
        self.assertIn("A chapter with none settled reads as none.", readme)
        delivery = flat((TEMPLATES / "delivery.md").read_text())
        self.assertIn("The project's own conventions come first for the form of these words: its handbook chapter's "
                      "`## Conventions`", delivery)
        sitting = flat((TEMPLATES / "sitting-brief.md").read_text())
        self.assertIn("Each session's brief also points at the project's conventions, its handbook chapter's "
                      "`## Conventions`", sitting)
        voice = flat((TEMPLATES / "letterhead-voice.md").read_text().split("## In the occupant's words")[0])
        self.assertIn("they set the form of what leaves that project", voice)


# --- 4. one pull request per feature, and the base branch ----------------------------------------

class TestOnePullRequestPerFeature(unittest.TestCase):
    def test_the_sitting_brief_names_the_branch_and_checks_the_base(self):
        sitting = flat((TEMPLATES / "sitting-brief.md").read_text())
        self.assertIn("each feature is its own session and leaves as its own pull request from the audience's base",
                      sitting)
        self.assertIn("each session's brief names the branch it builds on: a BRANCH line when it must build on a "
                      "branch the clone would not otherwise be on, and none when it builds on the clone's workbench",
                      sitting)
        self.assertIn("Before it sends a session out, the sitting checks that the base holds what that session "
                      "depends on", sitting)

    def test_the_doctrine_says_it_where_it_says_the_branch_line(self):
        _, past = core_and_past()
        branch = past.split("A planner's brief may name the branch its session builds on", 1)[1]
        branch = branch.split("A planner's brief may name the sitting its session succeeds", 1)[0]
        self.assertIn("One feature is one pull request from the audience's base (0.56.0", branch)
        self.assertIn("(`office start --branch NAME` does the same for a session that is not a bundle's)", branch)
        self.assertIn("When the base does not hold it, the sitting holds the session back and says what it waits "
                      "on.", branch)


# --- 5. the wrapped fact, in the drop brief --------------------------------------------------------

class TestTheDropBriefSaysAFactMayWrap(unittest.TestCase):
    def test_the_clause_follows_the_bare_sentence(self):
        brief = flat((TEMPLATES / "drop-brief.md").read_text())
        self.assertIn("Write each fact bare: the fact alone, no date in front and no session id behind, since office "
                      "land adds both. A fact may wrap onto indented lines, as a list item does, and is filed whole.",
                      brief)

    def test_a_sorts_wrapped_fact_is_read_whole(self):
        body = ["- project: alpha", "- folder: new", "- goal: g", "- size: small", "- tell: nobody", "- facts:",
                "- the api answers on port 8080, behind the proxy", "  that the ops team runs", "", "#### Brief", "",
                "b"]
        parsed = osort.parse_sort(f"{today()}-x.md", body)
        self.assertEqual(parsed["facts"], ["the api answers on port 8080, behind the proxy that the ops team runs"])


# --- 6. the chat kind, settled ------------------------------------------------------------------

class TestTheChatKindIsRetired(unittest.TestCase):
    def test_the_catalog_declares_no_chat_and_says_why(self):
        import tomllib
        text = (REPO / "share/verbs.toml").read_text(encoding="utf-8")
        verbs = tomllib.loads(text)["verbs"]
        self.assertNotIn("chat", verbs)
        self.assertIn("ask", verbs)
        self.assertFalse([n for n, v in verbs.items() if any("transcript" in x for x in v["lands"] + v["writes"])])
        self.assertIn("# The chat kind declared here until 0.56.0", text)
        self.assertIn("Q-3 is answered", text)

    def test_q3_is_open_nowhere_and_the_doctrine_says_it_is_answered(self):
        for path in (REPO / "share/verbs.toml", DOCTRINE, REPO / "README.md"):
            self.assertNotIn("Q-3, open", path.read_text(encoding="utf-8"), path.name)
        _, past = core_and_past()
        self.assertIn("(0.56.0: the declared chat kind it overlapped is retired, and Q-3, where a chat lands, is "
                      "answered by the ask's page and facts)", past)
        self.assertIn("a chat about a folder's job is that folder's work session", past)


# --- 7. the preps out, offered beside the folders ----------------------------------------------

class TestBareProbeOffersThePreps(PrepCase):
    def setUp(self):
        super().setUp()
        self.block = probe_block(slug="alpha-review")

    def test_the_one_prep_out_with_no_folders_session_is_the_probes(self):
        proc = self.run_office("probe", "-", "--yes", input=self.block, check=0)
        said = flat(proc.stderr)
        self.assertIn(f"the calendar records the one session open where probes run, the prep for alpha review "
                      f"(about: alpha), {self.prep}: the probe is its", said)
        self.assertIn(f"for {self.prep} (the prep for alpha review", said)
        self.assertIn(f"cwd: {os.path.realpath(self.proj)}", proc.stdout)
        self.assertIn("=== PROBE END alpha-review ===", proc.stdout)

    def test_a_prep_and_a_folders_session_are_named_piped(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        proc = self.run_office("probe", "-", "--yes", input=self.block, check=1)
        said = flat(proc.stderr)
        self.assertIn("2 sessions are open where probes run", said)
        self.assertIn(self.prep, said)
        self.assertIn("name one: office probe FOLDER, or office probe --prep SID; piped input is never asked", said)
        self.assertNotIn("PROBE BEGIN", proc.stdout)
        # Named, each runs as before.
        proc = self.run_office("probe", "--prep", self.prep, "-", "--yes", input=self.block, check=0)
        self.assertIn("=== PROBE END alpha-review ===", proc.stdout)
        self.assertTrue(sid)

    def test_with_no_prep_out_bare_probe_reads_as_it_did(self):
        self.run_office("land", self.prep, "--arising", "none", check=None)
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        proc = self.run_office("probe", "-", "--yes", input=probe_block(), check=0)
        self.assertIn(f"records the one session open, {sid} (on alpha), so the probe is its", flat(proc.stderr))


class TestBareProbeOffersThePrepsOnATerminal(PrepCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_the_prep_is_a_key_beside_the_folder(self):
        from test_start import on_a_terminal
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        path = self.e.tmp / "probe.sh"
        path.write_text(probe_block(slug="alpha-review"))
        cfg = self.e.home / ".config/office-src"
        cfg.mkdir(parents=True, exist_ok=True)
        (cfg / "machine.toml").write_text(f'paste_command = "cat {path}"\n')
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "probe"], self.root, self.e.env, [
            (b"by its key (office probe FOLDER, or --prep SID): ", "1"),
            (b"Run it? y or N (--yes)", "N"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("Sessions open where probes run:", seen)
        listed = [" ".join(l.split()) for l in seen.splitlines() if re.match(r"\s*\[\d+\] ", l)]
        self.assertTrue(listed[0].startswith(f"[1] the prep for alpha review (about: alpha): {self.prep}"), listed)
        self.assertTrue(any(sid in l for l in listed[1:]), listed)
        self.assertIn("not run: nothing was written", seen)


class TestTheHomeScreensProbeKey(unittest.TestCase):
    def test_probe_key_shown_for_a_folders_session_or_a_prep_out(self):
        folder = [{"folders": [f"desk/{today()}-job"]}]
        office_only = [{"folders": [f"filing-cabinet/{today()}-old"]}]
        prep = [{"state": "prep out", "sid": "x-sid"}]
        due = [{"state": "due", "sid": ""}]
        self.assertTrue(hs.probe_key_shown(folder, []))
        self.assertTrue(hs.probe_key_shown([], prep))
        self.assertTrue(hs.probe_key_shown(office_only, prep))
        self.assertFalse(hs.probe_key_shown(office_only, due))
        self.assertFalse(hs.probe_key_shown([], []))
        self.assertFalse(hs.probe_key_shown([], None))


# --- 8. a far fake day --------------------------------------------------------------------------

class TestTheFakeDay(unittest.TestCase):
    def test_read_fake_day_takes_a_day_and_refuses_the_rest(self):
        day = far_day()
        self.assertEqual(runner.read_fake_day(day), day)
        year = day[:4]
        for bad in (f"{year}-13-01", f"{year}-02-30", f"{year}/02/03", "tomorrow", ""):
            with self.assertRaises(ValueError) as cm:
                runner.read_fake_day(bad)
            self.assertIn("--fake-day", str(cm.exception))

    def test_fake_day_env_sets_it_and_never_lets_the_callers_through(self):
        day = far_day()
        base = {"PATH": "/bin", runner.FAKE_DAY_VAR: "the caller's"}
        self.assertEqual(runner.fake_day_env(base, day), {"PATH": "/bin", runner.FAKE_DAY_VAR: day})
        self.assertEqual(runner.fake_day_env(base), {"PATH": "/bin"})
        self.assertEqual(base[runner.FAKE_DAY_VAR], "the caller's")
        self.assertEqual(runner.FAKE_DAY_VAR, FAKE_DAY_VAR)

    def test_a_bad_day_stops_the_run_before_anything_runs(self):
        with mock.patch("sys.stderr") as err, mock.patch.object(runner, "whole_suite") as whole:
            self.assertEqual(runner.main(["--fake-day", "never"]), 2)
        whole.assert_not_called()
        self.assertIn("--fake-day never: not a day", "".join(c.args[0] for c in err.write.call_args_list))

    def test_the_run_hands_it_to_every_job(self):
        day = far_day()
        with mock.patch.object(runner, "whole_suite", return_value=(0, None)) as whole, \
                mock.patch.dict(os.environ, {runner.FAKE_DAY_VAR: "the caller's"}), mock.patch("sys.stdout"):
            self.assertEqual(runner.main(["--fake-day", day]), 0)
            env = whole.call_args.args[2]
            self.assertEqual(env[runner.FAKE_DAY_VAR], day)
            self.assertEqual(runner.main([]), 0)
            self.assertNotIn(runner.FAKE_DAY_VAR, whole.call_args.args[2])
        with tempfile.TemporaryDirectory() as d:
            job = runner.isolated_env(env, pathlib.Path(d) / "j1")
        self.assertEqual(job[runner.FAKE_DAY_VAR], day)

    def test_minting_day_the_tests_own_then_the_runs_then_the_clock(self):
        day, other = far_day(), (datetime.date.fromisoformat(far_day()) + datetime.timedelta(days=3)).isoformat()
        self.assertEqual(pack_bale.minting_day({"FAKE_BALE_DAY": other, FAKE_DAY_VAR: day}), other)
        self.assertEqual(pack_bale.minting_day({FAKE_DAY_VAR: day}), day)
        today = datetime.datetime.now(datetime.timezone.utc).date()
        minted = datetime.date.fromisoformat(pack_bale.minting_day({}))
        self.assertLessEqual(abs((minted - today).days), 1)

    def test_an_env_under_the_runner_hands_it_to_the_fakes(self):
        day = far_day()
        with mock.patch.dict(os.environ, {FAKE_DAY_VAR: day, "OFFICE_TESTS_UNDER_RUNNER": "1"}):
            self.assertEqual(Env(self).env[FAKE_DAY_VAR], day)
        with mock.patch.dict(os.environ, {FAKE_DAY_VAR: day}):
            os.environ.pop("OFFICE_TESTS_UNDER_RUNNER", None)
            self.assertNotIn(FAKE_DAY_VAR, Env(self).env)


class TestAStartMintsOnTheFakeDay(PrepCase):
    """End to end: a start's session id is minted on the run's default day,
    and a test's own FAKE_BALE_DAY still stands over it."""

    def test_the_fake_pack_mints_on_it(self):
        day = far_day()
        self.e.env[FAKE_DAY_VAR] = day
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        self.assertTrue(sid.startswith(day + "-"), sid)
        own = (datetime.date.fromisoformat(day) + datetime.timedelta(days=1)).isoformat()
        self.e.env["FAKE_BALE_DAY"] = own
        other = self.run_office("open", "docs-job", "--lane", "alpha: docs", check=0).stdout.strip()
        sid = self.start(other.split("/")[1], "--on", "alpha", "--goal", "g", "--write", "docs")
        self.assertTrue(sid.startswith(own + "-"), sid)


# --- the release ------------------------------------------------------------------------------

class TestTheRelease(unittest.TestCase):
    def test_the_record_names_this_release(self):
        # The release is the one the front sheet names for this session,
        # not VERSION's (0.57.0): VERSION moves on with every release.
        sheet = (REPO / ("cla" + "ude") / "context" / "front-sheet.md").read_text()
        version = re.search(r"^- (\d+\.\d+\.\d+) \(session 2026-11-10-practice-rules-001\)", sheet, re.M).group(1)
        releases = (REPO / "RELEASES.md").read_text()
        entry = releases.split(f"\n## {version}\n", 1)[1].split("\n## ", 1)[0]
        for words in ("Additive", "practice-rules", "--fake-day", "Conventions", "chat"):
            self.assertIn(words, entry)


if __name__ == "__main__":
    unittest.main()
