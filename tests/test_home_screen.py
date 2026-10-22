"""Tests for the home screen (office-src 0.22.0): `office` on a terminal,
the planner's bundles bare `office start` offers, and the wizard rule,
the occupant supplies words and the session supplies structure.

The home screen's work is lib/office_home.py: each project one line (in
flight, or what last landed and when), then what waits on the occupant,
each with a key, and the menu bin/office reads. The units run in this
process; the page and the bundles run as the command runs them, against
the fake bales the return trip built from captured bale output, whose
records say which bundle each session was opened from
(attempts[].bundle.stem) and which session last landed (status's
applied.latest). Two tests drive a terminal, in the serial lane: the home
screen landing a response by its key, and bare office start offering a
bundle by its key and, once it is opened, never again. Off a terminal
`office` is the walk-in, with its Next line, as before; tests/
test_front_door.py and tests/test_read_side.py hold that. Run with the
rest of the suite:

    tests/run.sh test_home_screen
"""

import datetime as dt
import os
import pathlib
import re
import subprocess
import sys
import time
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env  # noqa: E402
from test_start import on_a_terminal  # noqa: E402
from test_land import LandCase, bundle_file, response_tarball  # noqa: E402

import office_home as hs  # noqa: E402  (lib/ is on sys.path through test_office)
import office_bale as ob  # noqa: E402

NOW = dt.datetime(2026, 10, 15, 15, 0, tzinfo=dt.timezone.utc)


def folder(n, name, lane=None, title=None):
    return {"name": name, "number": n, "fields": {"lane": [lane]} if lane else {}, "rel": f"desk/{name}",
            "title": title or name}


def groups(**kw):
    g = {"flying": [], "open": [], "ready": [], "parked": {}, "candidates": [], "no_status": [],
         "misplaced": [], "unreadable": [], "ready_errors": [], "cleared": {}, "moves": (0, "", []),
         "drops": [], "drops_waited": set()}
    g.update(kw)
    return g


class FakeNames:
    """Names as the home screen gives them, without an office."""

    def __init__(self, folders=()):
        self.titles = {f["rel"]: f for f in folders}

    def folder_words(self, rel):
        f = self.titles.get(rel)
        return f"folder {f['number']}, {f['title']}" if f else rel

    def of(self, sid):
        return hs.slug_of(sid)


# --- the units ---------------------------------------------------------------------------

class TestTheHomeScreenUnits(unittest.TestCase):
    def test_ages_in_plain_words(self):
        for secs, words in ((5, "just now"), (60, "1 minute ago"), (125, "2 minutes ago"), (3600, "1 hour ago"),
                            (7300, "2 hours ago"), (86400, "yesterday"), (3 * 86400 + 5, "3 days ago")):
            self.assertEqual(hs.age_words(NOW - dt.timedelta(seconds=secs), NOW), words)

    def test_a_browser_copy_is_the_same_bundle(self):
        self.assertEqual(hs.bundle_stem("2026-10-15-alpha-fix (1).bale-bundle"), "2026-10-15-alpha-fix")
        self.assertEqual(hs.bundle_stem("2026-10-15-alpha-fix.bale-bundle"), "2026-10-15-alpha-fix")
        self.assertEqual(hs.slug_of("2026-10-15-alpha-fix-002"), "alpha-fix")
        self.assertTrue(hs.sid_for_slug("alpha-fix").match("2026-10-16-alpha-fix-001"))
        self.assertFalse(hs.sid_for_slug("alpha-fix").match("2026-10-16-alpha-fix-more-001"))

    def test_a_next_line_becomes_a_menu_entry_and_leaves_his_blank_to_the_verb(self):
        self.assertEqual(hs.command_argv("office land 2026-10-15-x-001"), ("office", ["land", "2026-10-15-x-001"]))
        self.assertEqual(hs.command_argv("office start --drop in-tray/a.md --lane LANE"),
                         ("office", ["start", "--drop", "in-tray/a.md"]))
        self.assertEqual(hs.command_argv("(cd /src && ./install.sh)"), ("shell", ["(cd /src && ./install.sh)"]))

    def test_his_words_make_the_title_the_goal_and_maybe_the_project(self):
        words = "Fix the login page on alpha\nA coworker says it fails on phones.\n"
        got = hs.words_reading(words, ["alpha", "beta"])
        self.assertEqual(got["title"], "Fix the login page on alpha")
        self.assertEqual(got["goal"], "Fix the login page on alpha; A coworker says it fails on phones.")
        self.assertEqual(got["project"], "alpha")
        # Two projects named, or none: the office cannot tell.
        self.assertEqual(hs.words_reading("alpha and beta both", ["alpha", "beta"])["project"], "")
        self.assertEqual(hs.words_reading("the alphabet", ["alpha"])["project"], "")
        self.assertEqual(hs.words_reading("- fix the export\n", [])["goal"], "fix the export")
        long = "word " * 30
        self.assertTrue(hs.words_reading(long, [])["title"].endswith("..."))
        self.assertLessEqual(len(hs.words_reading(long, [])["title"]), 60)
        self.assertEqual(hs.words_reading("caf\u00e9 order", [])["title"], "caf\\xe9 order")
        with self.assertRaises(Exception):
            hs.words_reading("  \n ", [])

    def test_the_bundles_in_the_downloads_newest_copy_and_recent_only(self):
        e = Env(self)
        d = e.downloads
        d.mkdir(parents=True)
        for name, age in (("2026-10-15-a.bale-bundle", 100), ("2026-10-15-a (1).bale-bundle", 50),
                          ("2026-10-01-old.bale-bundle", 20 * 86400), ("notes.txt", 10)):
            p = d / name
            p.write_text("x")
            t = time.time() - age
            os.utime(p, (t, t))
        now = dt.datetime.now(dt.timezone.utc)
        got = hs.downloaded_bundles([str(d), str(e.tmp / "absent")], now)
        self.assertEqual([(b["stem"], b["path"].name) for b in got], [("2026-10-15-a", "2026-10-15-a (1).bale-bundle")])
        self.assertEqual(len(hs.downloaded_bundles([str(d)], now, days=None)), 2)

    def test_the_waiting_list_puts_the_next_move_first_and_never_twice(self):
        out = [{"sid": "2026-10-15-fix-login-001", "label": "alpha", "folders": ["desk/2026-10-15-fix-login"],
                "held": False, "created": "2026-10-15T10:00:00Z"}]
        drops = [{"rel": "in-tray/2026-10-15-ask.md", "name": "2026-10-15-ask.md", "project": "alpha",
                  "heading": "Could you look at the login page"}]
        g = groups(drops=drops, moves=(2, "a sitting", []))
        items = hs.home_items("current", True, out, g, [{"name": "alpha"}], 0, None, [], FakeNames(), [], NOW)
        self.assertEqual(items[0]["argv"], ["land", "2026-10-15-fix-login-001"])
        self.assertTrue(items[0].get("next"))
        self.assertIn("it is out in alpha", items[0]["label"])
        self.assertEqual([i["argv"] for i in items[1:]], [["start", "--drop", "in-tray/2026-10-15-ask.md"], ["moves"]])
        # With nothing out, the oldest drop is the next move: listed once, first.
        items = hs.home_items("current", True, [], g, [{"name": "alpha"}], 0, None, [], FakeNames(), [], NOW)
        self.assertEqual([i["argv"] for i in items], [["moves"], ["start", "--drop", "in-tray/2026-10-15-ask.md"]])
        self.assertTrue(items[0].get("next"))
        # A ready folder is named by its folder, not by a command line.
        ready = folder(3, "2026-10-15-fix-login", "alpha: src", "Fix the login")
        items = hs.home_items("current", True, [], groups(ready=[ready]), [{"name": "alpha"}], 0, None, [],
                              FakeNames([ready]), [], NOW)
        self.assertEqual(items[0]["argv"], ["start", "2026-10-15-fix-login", "--on", "alpha"])
        self.assertTrue(items[0]["label"].startswith("Start folder 3, Fix the login: folder 3 is ready"))
        # Nothing waits: no item, since open and the desk have keys of their own.
        self.assertEqual(hs.home_items("current", True, [], groups(), [{"name": "alpha"}], 0, None, [],
                                       FakeNames(), [], NOW), [])
        # Behind a breaking release, the upgrade is first, said plainly.
        items = hs.home_items("behind", True, [], groups(), [{"name": "alpha"}], 0, None, [], FakeNames(), [], NOW)
        self.assertEqual(items[0]["argv"], ["upgrade"])
        self.assertTrue(items[0]["label"].startswith("Upgrade this office"))

    def test_the_page_and_its_menu(self):
        items = [hs.item(f"thing {n}", ["moves"]) for n in range(11)]
        items[0]["next"] = True
        lines, menu = hs.render_page([("alpha", "nothing landed yet"), ("beta-two", "in flight: x")], items, 0)
        self.assertEqual(lines[:3], ["Projects:", "  alpha     nothing landed yet", "  beta-two  in flight: x"])
        self.assertIn("  [1] thing 0  (next)", lines)
        self.assertIn("  [9] thing 8", lines)
        self.assertNotIn("  [10] thing 9", lines)
        self.assertIn("  and 2 more: office desk lists the drops and the folders", lines)
        keys = [k for k, _, _ in menu]
        self.assertEqual(keys, [str(n) for n in range(1, 10)] + ["o", "p", "m", "s", "n", "d", "k", "h", "q"])
        self.assertNotIn("[l]", "\n".join(lines), "nothing is out, so there is nothing to bring back")
        self.assertTrue(all(len(l) <= 80 for l in lines if l.startswith("  [o]") or l.startswith("  [")))
        _, menu = hs.render_page([], [], 1)
        self.assertIn(("l", "office", ["land"]), menu)
        lines, _ = hs.render_page([], [], 0)
        self.assertIn("  nothing waits on you", lines)

    def test_the_desk_in_one_line(self):
        g = groups(ready=[folder(1, "a")], open=[folder(2, "b")], parked={"waiting for folder 1": [(folder(3, "c"), [])]})
        self.assertEqual(hs.desk_words(g), "On the desk: 1 in flight, 1 ready, 1 parked; [k] shows every job.")
        self.assertEqual(hs.desk_words(groups()), "The desk is clear; [k] shows every job.")

    def test_the_menu_file_holds_one_line_per_key_and_refuses_a_tab(self):
        e = Env(self)
        path = e.tmp / "menu"
        hs.write_menu(path, [("1", "office", ["land", "2026-10-15-x-001"]), ("q", "quit", [])])
        self.assertEqual(path.read_text(), "1\toffice\tland\t2026-10-15-x-001\nq\tquit\n")
        with self.assertRaises(Exception):
            hs.write_menu(path, [("1", "office", ["a\tb"])])


# --- the page and the bundles, as the command runs them -----------------------------------------

def home(case, *extra):
    """office_home.py page for the case's office: (stdout, the menu)."""
    menu = case.e.tmp / "menu"
    proc = subprocess.run([sys.executable, "-B", str(REPO / "lib" / "office_home.py"), "page", str(case.root),
                           "--today", dt.date.today().isoformat(), "--tz", "UTC", "--menu-file", str(menu),
                           "--dir", str(case.downloads), *extra], env=case.e.env, capture_output=True, text=True,
                          timeout=120)
    case.assertEqual(proc.returncode, 0, proc.stderr)
    return proc.stdout, [l.split("\t") for l in menu.read_text().splitlines()]


def waiting(case):
    proc = subprocess.run([sys.executable, "-B", str(REPO / "lib" / "office_home.py"), "bundles", str(case.root),
                           "--dir", str(case.downloads)], env=case.e.env, capture_output=True, text=True, timeout=120)
    case.assertEqual(proc.returncode, 0, proc.stderr)
    return [l.split("\t") for l in proc.stdout.splitlines()]


def bundle_argv(slug, write="src"):
    return [f"Do the {slug} work", "--slug", slug, "--write", write, "--constraint", ob.PROJECT_CONSTRAINT]


class TestThePage(LandCase):
    def test_projects_what_waits_and_every_key_resolved_without_an_id(self):
        out, menu = home(self)
        self.assertIn("Projects:\n  alpha  nothing landed yet\n", out)
        self.assertIn(f"[1] Start folder 1, fix-login: folder 1 is ready and first on the desk", out)
        self.assertEqual(menu[0], ["1", "office", "start", self.name, "--on", "alpha"])
        # Out: in flight on its project, and its response, once saved, waits.
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        out, menu = home(self)
        self.assertRegex(out, r"\n  alpha  in flight: folder 1, fix-login \(went out [^)]+\)\n")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        out, menu = home(self)
        self.assertRegex(out, r"\[1\] Land folder 1, fix-login \(alpha\): a response for it was saved just now in "
                              r"your downloads  \(next\)")
        self.assertEqual(menu[0], ["1", "office", "land", sid])
        self.assertIn(["l", "office", "land"], menu)
        self.assertNotIn(sid, out, "the screen names a session by its folder, never by its id")
        # Landed: what last landed on the project, and when.
        self.run_office("land", "--not-now", check=0)
        out, _ = home(self)
        self.assertRegex(out, r"\n  alpha  last landed: folder 1, fix-login, \d{4}-\d{2}-\d{2} \([^)]+\)\n")

    def test_bundles_no_session_opened_wait_and_an_opened_one_never_does(self):
        bundle_file(self.downloads, "2026-10-15-docs-pass", bundle_argv("docs-pass", "docs"))
        bundle_file(self.downloads, "2026-10-15-src-pass", bundle_argv("src-pass"))
        rows = waiting(self)
        self.assertEqual(sorted(r[1] for r in rows), ["2026-10-15-docs-pass", "2026-10-15-src-pass"])
        self.assertEqual({r[3] for r in rows}, {"Do the docs-pass work", "Do the src-pass work"})
        self.run_office("start", "fix-login", "--on", "alpha", "2026-10-15-src-pass.bale-bundle", check=0)
        self.assertEqual([r[1] for r in waiting(self)], ["2026-10-15-docs-pass"])
        # A browser's second copy of the opened one is the same bundle.
        (self.downloads / "2026-10-15-src-pass (1).bale-bundle").write_bytes(
            (self.downloads / "2026-10-15-src-pass.bale-bundle").read_bytes())
        self.assertEqual([r[1] for r in waiting(self)], ["2026-10-15-docs-pass"])
        out, menu = home(self)
        self.assertRegex(out, r"\[\d\] Start the planner's bundle 2026-10-15-docs-pass \(saved just now\)")
        self.assertIn(["office", "start", "--bundle", str((self.downloads / "2026-10-15-docs-pass.bale-bundle")
                                                        .resolve())], [m[1:] for m in menu])
        # Whether one was opened is read from bale's records: a session with
        # its slug opened from another bundle does not count.
        bundle_file(self.downloads, "2026-10-15-src-pass-v2", bundle_argv("src-pass"))
        self.assertIn("2026-10-15-src-pass-v2", [r[1] for r in waiting(self)])


# --- on a terminal --------------------------------------------------------------------------

def downloads_set(case):
    cfg = case.e.home / ".config/office-src"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "machine.toml").write_text(f'downloads = ["{case.downloads}"]\n')


class TestTheHomeScreenOnATerminal(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_a_key_lands_the_response_and_the_screen_comes_back(self):
        downloads_set(self)
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        code, seen = on_a_terminal(self, [str(self.e.office_bin)], self.root, self.e.env, [
            (b"Your key: ", "1"),
            (b"merge into origin (default)", ""),
            (b"Return brings your home screen back; q leaves: ", ""),
            (b"last landed: folder 1, fix-login", None),
            (b"Your key: ", "q"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("The home office,", seen)
        self.assertIn("Waiting on you:", seen)
        self.assertIn(f"Landed: {sid} is applied in alpha", seen)
        self.assertNotIn("Next: office", seen, "on a terminal there is no line to type")
        self.assertEqual((self.proj / "src/a.py").read_text(), "fixed\n")

    def test_bare_start_offers_the_bundles_no_session_opened_by_key(self):
        downloads_set(self)
        bundle_file(self.downloads, "2026-10-15-src-pass", bundle_argv("src-pass"))
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [
            (b"(--bundle FILE) [return skips]:", "1"),
            (b"Which job, by its key (office start FOLDER):", "1"),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("[1] 2026-10-15-src-pass, saved just now: Do the src-pass work", seen)
        self.assertRegex(seen, r"Packed \d{4}-\d{2}-\d{2}-src-pass-001 for desk/")
        self.assertNotIn("in your words (--goal)", seen, "a bundle carries its own goal")
        # Opened now, by bale's records: offered no more, and start goes
        # straight to the jobs on the desk.
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [
            (b"Which job, by its key (office start FOLDER):", "1"),
            (b"in your words (--goal):", "Fix the login"),
        ])
        # The job's forecast meets the open session's, so the start stops
        # there; what matters here is what it offered first.
        self.assertNotIn("Planner's bundles in your downloads", seen)
        self.assertNotIn("[1] 2026-10-15-src-pass", seen)


class TestTheHeldResponseByKeyOnATerminal(LandCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_after_a_hold_the_copies_in_the_downloads_are_offered_by_key(self):
        """bale held the session; the one copy of its name in the downloads
        is now the corrected response. land lists it by key, with bale's
        own search as the last key, and nobody types a file's name."""
        downloads_set(self)
        sid = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        held = response_tarball(self.downloads, sid, {"src/a.py": "wrong\n"}, validation="fail")
        self.run_office("land", sid, "--not-now", check=1)
        held.unlink()
        response_tarball(self.downloads, sid, {"src/a.py": "fixed\n"})
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "land", sid, "--not-now"], self.root, self.e.env, [
            (b"the corrected response, by its key (--response FILE):", "1"),
            (b"merge into origin (default)", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn(f"[1] response-{sid}.tar.gz, saved just now", seen)
        self.assertIn("[2] the one bale's own search finds first (it may be the held one)", seen)
        self.assertIn(f"Landed: {sid} is applied in alpha", seen)
        self.assertEqual((self.proj / "src/a.py").read_text(), "fixed\n")


if __name__ == "__main__":
    unittest.main()
