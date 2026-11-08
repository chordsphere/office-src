"""Tests for office-src 0.54.0: the rest of what the read side was missing.

1. The asks' three lines: the walk-in's Next line (and the home screen's
   Next item) names an office ask that is out, after the desk's moves and
   a waiting job or delivery and before a drop; the digest lists the asks
   filed or ended since the last sitting, with their pages, from their
   `office ask:` commits; office status names a record whose tray is gone
   with the one line that removes it.
2. The sandbox line in a container: when the survey's `## Machine` class
   reads `container`, a project on this machine gets the hosted project's
   sandbox line, read here with the same argv.
3. The listed offices: office status names machine.toml's offices, the one
   it runs in marked, and a listed root that is no longer an office, with
   the line that unlists it.
4. The map's paused folders: a folder whose project is paused says so on
   its own line, and a session out there is still named.
5. A host ride's size: before a directory outside git is copied on the
   host for its pack, start's screen says its size; above a bound it says
   so and names --leave-out host:PATH. Nothing is refused.
6. A profile's capability words: share/verbs.toml may give a verb an
   optional `words` list, read by named_in_line beside its name.
7. The tables: the walk-in's In flight lines and the home screen's
   Projects block take the map's project-first table shape.

No test here hard-codes a day or a VERSION. Run with the rest of the suite:

    tests/run.sh test_status_more_two
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_ask import AskCase, learned  # noqa: E402
from test_land import LandCase  # noqa: E402
from test_host_rides import HOST, HostRideCase  # noqa: E402
from test_home_screen import FakeNames, groups  # noqa: E402
from test_host_refresh import REFUSING_PROBE, RefreshCase  # noqa: E402

import office_ask as oa  # noqa: E402
import office_bale as ob  # noqa: E402
import office_home as hs  # noqa: E402
import office_host as ohost  # noqa: E402

VERSION = (REPO / "VERSION").read_text().strip()


def an_ask(name="ask-2026-01-02-why", project="alpha", day="2026-01-02", time="09:00"):
    """An ask out as office_ask asks_out returns one."""
    return {"name": name, "project": project, "day": day, "time": time, "tray": f"/trays/{name}"}


# --- 1. the asks' three lines ---------------------------------------------------------------------

class TestTheAskOnTheNextLine(unittest.TestCase):
    """next_move's ask row, as a pure function: its rank and its words."""

    def move(self, **kw):
        return ob.next_move("current", True, [], groups(**kw), [{"name": "alpha"}], 0)

    def test_an_ask_out_is_named_with_its_filing_verb(self):
        cmd, why = self.move(asks=[an_ask(), an_ask("ask-2026-01-03-how", None, "2026-01-03")])
        self.assertEqual(cmd, "office ask --learned")
        self.assertEqual(why, "ask-2026-01-02-why (alpha) has been out since 2026-01-02 09:00: once its chat ends, "
                              "--learned files its LEARNED block from the clipboard (or from a FILE); office tray "
                              "ask-2026-01-02-why opens its tray again; 1 more out after it")

    def test_it_ranks_after_the_moves_and_a_delivery_and_before_a_drop_and_the_desk(self):
        from test_status_more import job_waiting
        ask = [an_ask()]
        self.assertEqual(self.move(asks=ask, moves=(1, "the moves page", []))[0], "office moves")
        self.assertEqual(self.move(asks=ask, merges=[job_waiting("merge")])[0], "office start 5 --merge")
        drop = {"rel": "in-tray/2026-01-01-x.md", "project": "alpha"}
        ready = {"name": "fix", "rel": "desk/fix", "number": 3, "title": "Fix", "space": "desk"}
        self.assertEqual(self.move(asks=ask, drops=[drop], ready=[ready])[0], "office ask --learned")
        # With no ask out, the drop has the row it had.
        self.assertEqual(self.move(drops=[drop], ready=[ready])[0], "office start --drop in-tray/2026-01-01-x.md")

    def test_no_ask_no_row(self):
        self.assertIsNone(ob.ask_move(groups()))
        self.assertIsNone(ob.ask_move(groups(asks=[])))

    def test_the_home_screen_offers_the_ask_once_as_its_next_item(self):
        import datetime as dt
        g = groups(asks=[an_ask(), an_ask("ask-2026-01-03-how", None, "2026-01-03")])
        items = hs.home_items("current", True, [], g, [{"name": "alpha"}], 0, None, [], FakeNames(), [],
                              dt.datetime.now(dt.timezone.utc))
        asks = [hs.item(oa.home_words(a), ["ask", "--learned"]) for a in g["asks"]]
        got = hs.with_asks(items, asks)
        self.assertEqual([i["argv"] for i in got].count(["ask", "--learned"]), 2)
        self.assertTrue(got[0].get("next"))
        self.assertEqual(got[0]["label"], oa.home_words(g["asks"][0]))
        self.assertFalse(got[-1].get("next"))
        # A Next move that is not the ask leaves the asks' items where they were.
        other = [dict(hs.item("Start something", ["start", "3"]), next=True)]
        self.assertEqual(hs.with_asks(other, asks), [*other, *asks])


class TestTheAsksInTheOffice(AskCase):
    """The walk-in's Next line, office status's orphan line and the digest's
    asks line, in an office with an ask sent through office ask."""

    def test_the_walk_in_s_next_line_names_the_ask_out(self):
        name, _ = self.sent()
        page = self.e.run(cwd=self.root, check=0).stdout
        self.assertRegex(page, rf"\nNext: office ask --learned  \({re.escape(name)} \(alpha\) has been out since "
                               r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}: once its chat ends")
        self.file_text(learned(name))
        self.assertNotIn("Next: office ask --learned", self.e.run(cwd=self.root, check=0).stdout)

    def test_status_names_a_record_whose_tray_is_gone_and_its_line_removes_it(self):
        name, _ = self.sent()
        shutil.rmtree(self.tray_root / name)
        out = self.run_office("status", check=None).stdout
        line = next((l for l in out.splitlines() if l.startswith(f"asks:       {name}'s tray is gone")), None)
        self.assertIsNotNone(line, out)
        self.assertNotIn("out:", line)
        record, opener = self.tray_root / f"{name}.ask.json", self.tray_root / f"{name}.opener.txt"
        self.assertTrue(record.is_file())
        remove = line.split("; ", 1)[1]
        self.assertTrue(remove.startswith("rm -- ") and remove.endswith(" removes it"), remove)
        self.assertIn(str(record), remove)
        if opener.is_file():
            self.assertIn(str(opener), remove)
        subprocess.run(["sh", "-c", remove[:-len(" removes it")]], check=True)
        self.assertFalse(record.exists())
        self.assertFalse(opener.exists())
        self.assertNotIn("asks:", self.run_office("status", check=None).stdout)

    def test_a_record_of_another_office_is_not_this_office_s_to_name(self):
        name, _ = self.sent()
        shutil.rmtree(self.tray_root / name)
        with self.e.this_process():
            self.assertEqual([n for n, _, _ in oa.orphans(self.root, self.tray_root)], [name])
            self.assertEqual(oa.orphans(self.e.tmp / "elsewhere", self.tray_root), [])
            self.assertEqual(oa.orphans(self.root, self.e.tmp / "no-such-trays"), [])

    def test_the_digest_lists_the_asks_filed_since_the_last_sitting_with_their_pages(self):
        name, _ = self.sent()
        self.file_text(learned(name, handbook={"alpha": ["the picklist endpoint reads the schema's enum"]},
                               qa=["- 2026-01-02 does it cache? no"]))
        ended, _ = self.sent("Is the beta queue drained nightly?", "--project", "alpha")
        self.ask("--learned", "none", ended)
        self.run_office("digest", check=None)
        page = (self.root / "drafting-table" / "digest.md").read_text()
        line = next(l for l in page.splitlines() if l.startswith("- asks:"))
        self.assertTrue(line.startswith("- asks: 2 filed or ended: "), line)
        self.assertIn(f"{name} filed ({oa.page_rel(name)}; facts in handbook/alpha.md; its questions and "
                      "answers on the page)", line)
        self.assertIn(f"{ended} ended with nothing filed ({oa.page_rel(ended)})", line)
        self.assertLess(line.index(name), line.index(ended))
        # The line sits in the window's section, after the drafting table's.
        since = page.split("## Since the last sitting", 1)[1].split("\n## ", 1)[0]
        self.assertIn(line, since)


class TestTheDigestsAsksLineAsAUnit(unittest.TestCase):
    def test_no_ask_and_no_git(self):
        import office_digest as odg
        e = Env(self)
        repo = e.tmp / "office"
        repo.mkdir()
        self.assertEqual(odg.asks_filed(repo, None), "- asks: could not be read (git log refused here)")
        subprocess.run(["git", "init", "-q", str(repo)], check=True, env=e.env)
        (repo / "a").write_text("a\n")
        subprocess.run(["git", "-C", str(repo), "add", "a"], check=True, env=e.env)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "a commit\n\noffice ask: in its body only"],
                       check=True, env=e.env)
        self.assertEqual(odg.asks_filed(repo, None), "- asks: none filed or ended")



# --- 2. the sandbox line in a container ---------------------------------------------------------------

def survey_says(root, cls):
    """The office's survey page with its Machine class set to cls, as office
    survey writes it (the page made with only that section when the office
    has none)."""
    page = pathlib.Path(root) / ob.SURVEY_PAGE
    text = page.read_text() if page.is_file() else "# Site survey\n\n## Machine\n\n- class: none\n"
    if not re.search(r"^- class: ", text, re.M):
        text = text.replace("## Machine\n\n", "## Machine\n\n- class: none\n", 1)
    page.write_text(re.sub(r"^- class: .*$", f"- class: {cls}", text, count=1, flags=re.M))


class TestTheMachinesClass(unittest.TestCase):
    def test_it_is_the_survey_s_fact_and_none_without_a_survey(self):
        e = Env(self)
        root = e.tmp / "office"
        (root / "floor-plan").mkdir(parents=True)
        self.assertIsNone(ob.machine_class(root))
        survey_says(root, "container")
        self.assertEqual(ob.machine_class(root), "container")
        survey_says(root, "WSL")
        self.assertEqual(ob.machine_class(root), "WSL")


class TestTheSandboxLineInAContainer(RefreshCase):
    """office status on a project on this machine: the line a hosted project
    gets when the survey says this machine is a container, and none when it
    does not."""

    def status(self):
        return self.e.run("status", cwd=self.root, extra={"OFFICE_SANDBOX_PROBE": REFUSING_PROBE}, check=0).stdout

    def test_in_a_container_the_hosted_line_is_said_of_this_machine(self):
        survey_says(self.root, "container")
        out = self.status()
        self.assertIn("  proj: sandbox: bale's sandbox cannot run on this machine (unshare: write failed "
                      "/proc/self/uid_map: Operation not permitted) and bale.toml does not turn it off, so every apply "
                      "there asks; office projects set proj --prepare writes the setting\n", out)
        self.assertLess(out.index("projects:   1 in scope"), out.index("  proj: sandbox:"))
        # The step it names writes the setting, and the line says so after.
        self.e.run("projects", "set", "proj", "--prepare", cwd=self.root,
                   extra={"OFFICE_SANDBOX_PROBE": REFUSING_PROBE}, check=0)
        self.assertRegex(self.status(), r"  proj: sandbox: off by bale.toml, written \d{4}-\d{2}-\d{2}: no "
                                        r"unprivileged user namespaces where this clone is")

    def test_on_wsl_or_with_no_survey_a_project_here_gets_no_sandbox_line(self):
        survey_says(self.root, "WSL")
        self.assertNotIn("sandbox:", self.status())
        (self.root / ob.SURVEY_PAGE).unlink()
        self.assertNotIn("sandbox:", self.status())

    def test_where_the_sandbox_runs_nothing_is_said(self):
        survey_says(self.root, "container")
        out = self.e.run("status", cwd=self.root, extra={"OFFICE_SANDBOX_PROBE": "true"}, check=0).stdout
        self.assertNotIn("sandbox:", out)


# --- 3. the listed offices ------------------------------------------------------------------------------

class TestTheListedOfficesInStatus(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init("home")
        self.other = self.e.init("work")
        self.machine = self.e.home / ".config" / "office-src" / "machine.toml"

    def offices(self):
        out = self.e.run("status", cwd=self.root, check=None).stdout
        return [l for l in out.splitlines() if l.startswith("offices:") or l.startswith("  ") and "listed, but" in l]

    def list_them(self, *roots):
        self.machine.parent.mkdir(parents=True, exist_ok=True)
        self.machine.write_text("offices = [" + ", ".join(f'"{r}"' for r in roots) + "]\n")

    def test_each_listed_office_is_named_and_this_one_is_marked(self):
        self.list_them(self.root, self.other)
        here, there = os.path.realpath(self.root), os.path.realpath(self.other)
        lines = self.offices()
        self.assertEqual(len(lines), 1, lines)
        self.assertRegex(lines[0], rf"^offices:    2 listed in {re.escape(str(self.machine))}: \S+ "
                                   rf"\({re.escape(here)}, this one\); \S+ \({re.escape(there)}\)$")

    def test_a_root_that_is_no_longer_an_office_is_named_with_the_edit_that_unlists_it(self):
        gone = self.e.tmp / "gone"
        gone.mkdir()
        self.list_them(self.root, gone)
        lines = self.offices()
        self.assertTrue(lines[0].startswith(f"offices:    1 listed in {self.machine}: "), lines)
        self.assertEqual(lines[1], f'  {gone}: listed, but it is no longer an office (no floor-plan/manifest.toml); '
                                   f'no office verb unlists it: take "{gone}" out of offices in {self.machine}')
        # The machine file is the occupant's: status reads it, never edits it.
        self.assertEqual(self.machine.read_text(), f'offices = ["{self.root}", "{gone}"]\n')

    def test_this_office_unlisted_and_none_set(self):
        self.list_them(self.other)
        self.assertTrue(self.offices()[0].endswith("; this one is not in the list"), self.offices())
        self.machine.write_text('downloads = ["~/Downloads"]\n')
        self.assertEqual(self.offices(), [f"offices:    none listed ({self.machine}'s offices is not set; office "
                                          "default PATH, office init and the home screen list an office)"])

    def test_a_list_that_does_not_read_is_said(self):
        self.machine.parent.mkdir(parents=True, exist_ok=True)
        self.machine.write_text('offices = "~/home"\n')
        self.assertTrue(h.offices_status_lines(self.machine, self.root)[0].startswith(
            "offices:    machine.toml's offices does not read: "))


# --- 4. the map's paused folders ------------------------------------------------------------------------

class TestTheMapsPausedFolders(LandCase):
    def test_a_paused_project_s_folder_says_so_and_names_its_session(self):
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        out = self.run_office("map", check=0).stdout
        row = next(l for l in out.splitlines() if "fix-login" in l or "Fix" in l and l.startswith("folder "))
        self.assertIn("in flight", row)
        self.assertNotIn("paused", row)
        self.run_office("projects", "set", "alpha", "--paused", check=0)
        out = self.run_office("map", check=0).stdout
        rows = [l for l in out.splitlines() if l.startswith("folder ")]
        self.assertEqual(len(rows), 1, out)
        # Its desk state stays (open: no session is read in flight), after it.
        self.assertTrue(rows[0].endswith(f"  paused; {sid} not read; open"), rows[0])
        record = self.run_office("map", rows[0].split()[1], check=0).stdout
        self.assertIn(f"alpha is paused, so nothing of it is read (office projects set alpha --unpaused); the last "
                      f"session this folder records, {sid}, is not read while it is", record)
        self.run_office("projects", "set", "alpha", "--unpaused", check=0)
        self.assertNotIn("paused", self.run_office("map", check=0).stdout.split("FOLDER", 1)[1])

    def test_a_folder_of_a_project_not_paused_or_of_the_office_says_nothing_of_it(self):
        import types
        import office_map as om
        reading = types.SimpleNamespace(names=["alpha", "beta"], paused={"beta"})
        folder = lambda lane, sids=(): {"rel": "desk/x", "fields": {"lane": [lane]}, "sids": list(sids)}  # noqa: E731
        self.assertIsNone(om.paused_words(reading, folder("alpha: src")))
        self.assertIsNone(om.paused_words(reading, folder("office")))
        self.assertEqual(om.paused_words(reading, folder("beta: src"), short=True), "paused")
        self.assertEqual(om.paused_words(reading, folder("beta", ["2026-01-02-x-001"]), short=True),
                         "paused; 2026-01-02-x-001 not read")


# --- 5. a host ride's size -------------------------------------------------------------------------------

class TestTheRideSizeLines(unittest.TestCase):
    PLACE = ohost.Place("~/proj", host="me@box")

    def fact(self, kind="dir", top=None, kb=None):
        return {"path": "~/x", "kind": kind, "top": top, "real": "/h/x", "kb": kb}

    def test_a_directory_outside_git_says_its_size_and_above_the_bound_that_it_is_large(self):
        lines = ob.ride_size_lines(self.PLACE, [("host:~/loose", self.fact(kb=812)),
                                                ("host:~/big data", self.fact(kb=3 * 1024 * 1024))], large=1024)
        self.assertEqual(lines[0], "host:~/loose is 812 KiB, a directory outside git on me@box, copied whole into a "
                                   "scratch there for its pack")
        self.assertEqual(lines[1], "host:~/big data is 3.0 GiB, a directory outside git on me@box: LARGE (over 1.0 "
                                   "MiB), and the whole of it is copied into a scratch there before its pack, so this "
                                   "start takes a while; --leave-out 'host:~/big data' leaves it home this once "
                                   "(nothing is refused: bale's own caps decide what of it rides)")

    def test_what_is_not_copied_whole_says_nothing_and_an_unread_size_is_said(self):
        self.assertEqual(ob.ride_size_lines(self.PLACE, [("host:~/r", self.fact(top="/h/r", kb=5)),
                                                         ("host:~/f", self.fact(kind="file"))]), [])
        self.assertIn("its size could not be read there (du said nothing)",
                      ob.ride_size_lines(self.PLACE, [("host:~/d", self.fact())])[0])

    def test_the_sizes_words(self):
        self.assertEqual([ob.size_words(k) for k in (0, 1023, 1024, 1536, 1024 * 1024 * 2)],
                         ["0 KiB", "1023 KiB", "1.0 MiB", "1.5 MiB", "2.0 GiB"])
        self.assertGreater(ob.RIDE_LARGE_KB, 0)

    def test_the_facts_carry_the_size_in_a_fifth_column_and_four_still_read(self):
        run = ohost.Run(0, "dir\t~/a\t\t/h/a\t2048\nfile\t~/b\t\t/h/b\t\ndir\t~/c\t/h/r\t/h/r/c\n", "", "", "h")
        rows = ohost.read_ride_facts(run, ["~/a", "~/b", "~/c"])
        self.assertEqual([r["kb"] for r in rows], [2048, None, None])

    def test_the_script_measures_only_a_directory_outside_git(self):
        e = Env(self)
        loose = e.tmp / "loose"
        loose.mkdir()
        (loose / "a.bin").write_bytes(b"x" * 300_000)
        repo = e.tmp / "repo"
        subprocess.run(["git", "init", "-q", str(repo)], check=True, env=e.env)
        (repo / "d").mkdir()
        with e.this_process():
            run = ohost.run_in(ohost.Place(e.tmp), ohost.ride_facts_argv([str(loose), str(repo / "d")]), chdir=False)
        rows = ohost.read_ride_facts(run, [str(loose), str(repo / "d")])
        self.assertGreaterEqual(rows[0]["kb"], 290)
        self.assertIsNone(rows[1]["kb"])


class TestTheRideSizeAtStart(HostRideCase):
    def test_start_says_it_before_the_copy_in_the_round_it_already_makes(self):
        self.run_office("projects", "set", "far", "--ride", "host:~/loose", check=0)
        self.ssh.reset()
        proc = self.run_office("start", self.name, "--on", "far", "--goal", "Fix it there", "--write", "src")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        said = re.search(rf"host:~/loose is \d+ KiB, a directory outside git on {re.escape(HOST)}, copied whole into "
                         r"a scratch there for its pack", proc.stderr)
        self.assertIsNotNone(said, proc.stderr)
        self.assertIn(f"context-loose.tar.gz: rides with far (host:~/loose, packed on {HOST} from a copy there)",
                      proc.stdout)
        # The size rides the facts read, in the one round start already
        # makes before the pack; no connection of its own.
        calls = [c[-1] for c in self.ssh.connections()]
        measuring = [c for c in calls if "du -sk" in c]
        self.assertEqual(len(measuring), 1, [c[:120] for c in calls])
        self.assertIn("office-rides", measuring[0])
        self.assertIn("symbolic-ref", measuring[0])


# --- 6. a profile's capability words ---------------------------------------------------------------------

class TestTheCapabilityWords(unittest.TestCase):
    CATALOG = {"verbs": {"projects": {"kind": "script", "built": True, "words": ["a project on a host",
                                                                                 "hosted projects"]},
                         "land": {"kind": "script", "built": True, "words": ["the return trip"]},
                         "renovate": {"kind": "office-session", "built": False, "words": ["a renovation"]}}}

    def match(self, line):
        return h.match_in_line(line, h.catalog_names(self.CATALOG), h.catalog_words(self.CATALOG))

    def test_a_phrase_names_its_verb_and_the_name_forms_still_do(self):
        self.assertEqual(self.match("- a project on a host is not built yet"), ("projects", "a project on a host"))
        self.assertEqual(self.match("Hosted\n projects are not built"), ("projects", "hosted projects"))
        self.assertEqual(self.match("office land is not built"), ("land", None))
        self.assertEqual(self.match("the return trip (land on a host) is not built"), ("land", "the return trip"))
        self.assertIsNone(self.match("a project on a hostel is not built"))
        # Without words, the 0.53.0 rule exactly.
        self.assertIsNone(h.named_in_line("the return trip is not built", h.catalog_names(self.CATALOG)))
        self.assertEqual(h.named_in_line("the return trip is not built", h.catalog_names(self.CATALOG),
                                         h.catalog_words(self.CATALOG)), "land")

    def test_the_leftmost_and_at_one_place_the_longer_wins(self):
        self.assertEqual(self.match("office land waits: a project on a host is not built"), ("land", None))
        catalog = {"verbs": {"a": {"kind": "script", "built": True, "words": ["the trip"]},
                             "b": {"kind": "script", "built": True, "words": ["the trip home"]}}}
        self.assertEqual(h.match_in_line("the trip home is not built", h.catalog_names(catalog),
                                         h.catalog_words(catalog)), ("b", "the trip home"))

    def test_the_stale_line_says_the_words_and_the_verb(self):
        profile = Env(self).tmp / "profile.md"
        profile.write_text("# Profile\n\n- a project on a host is not built yet\n- a renovation is not built\n")
        self.assertEqual(h.stale_profile_lines(profile, self.CATALOG, "9.9.9"), [
            "  profile.md line 3 says a project on a host is not built; office-src 9.9.9 builds it (office "
            "projects, share/verbs.toml): - a project on a host is not built yet"])

    def test_the_catalog_takes_words_as_optional_and_checks_their_shape(self):
        base = {"kind": "script", "built": True, "surface": "occupant", "writes": [], "lands": [],
                "attended": True, "trigger": ["manual"]}
        self.assertEqual(h.verb_catalog_problems({"verbs": {"x": dict(base)}})[0], [])
        self.assertEqual(h.verb_catalog_problems({"verbs": {"x": dict(base, words=["a thing"])}})[0], [])
        self.assertNotIn("words", h.VERB_KEYS)
        for bad in ([], "a thing", ["a thing", ""], [3]):
            with self.subTest(bad=bad):
                problems = h.verb_catalog_problems({"verbs": {"x": dict(base, words=bad)}})[0]
                self.assertEqual(problems, ["x: words must be a non-empty list of phrases (the ones a profile line "
                                            "may name it by), or left out"])
        twice = {"verbs": {"x": dict(base, words=["A thing"]), "y": dict(base, words=["a  thing"])}}
        self.assertEqual(h.verb_catalog_problems(twice)[0],
                         ["y: words 'a  thing' is x's already; a phrase names one verb"])

    def test_the_install_s_hosted_verbs_carry_the_docs_words(self):
        catalog = h.read_toml(REPO / "share/verbs.toml")
        words = h.catalog_words(catalog)
        self.assertIn("a project on a host", words["projects"])
        self.assertEqual(words["land"], ["the return trip"])
        self.assertEqual(words["start"], ["the out trip"])
        self.assertEqual(h.verb_catalog_problems(catalog)[0], [])


class TestTheCapabilityWordsInStatus(unittest.TestCase):
    def test_status_names_a_line_that_names_only_a_capability(self):
        e = Env(self)
        root = e.init()
        e.found(root)
        profile = root / "profile.md"
        text = profile.read_text().replace("## Site\n\nWritten at the founding sitting.\n",
                                           "## Site\n\nWritten at the founding sitting.\n\n"
                                           "- a project on a host is not built yet\n")
        self.assertNotEqual(text, profile.read_text())
        profile.write_text(text)
        n = text.splitlines().index("- a project on a host is not built yet") + 1
        out = e.run("status", cwd=root, check=0).stdout
        self.assertIn(f"  profile.md line {n} says a project on a host is not built; office-src {VERSION} builds it "
                      "(office projects, share/verbs.toml): - a project on a host is not built yet\n", out)
        self.assertEqual(profile.read_text(), text)

if __name__ == "__main__":
    unittest.main()
