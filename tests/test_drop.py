"""Tests for the in-tray (0.19.0): office drop and the drop's page, the
in-tray arriving with the first drop, every session office start sends
out carrying the unsorted drops, office start --drop sending one straight
out as a project session, and the walk-in, the desk and the Next line
that read them.

bale is never needed: office start's tests run the fake bale that packs
(tests/test_start.py), whose every line is built from captured bale
output. The clipboard is a command the test names in its own
machine.toml. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import json
import os
import pathlib
import re
import sys
import tarfile
import textwrap
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_start import StartCase, on_a_terminal, opener_from, tar_names  # noqa: E402

import office_bale as ob  # noqa: E402  (lib/ is on sys.path through test_office)
import office_drop as odrop  # noqa: E402

DOCTRINE = REPO / "doctrine" / "OFFICE.md"
BRIEF_TEMPLATE = REPO / "templates" / "drop-brief.md"
MESSAGE = "Could you look at the login page?\nIt shows an error on narrow screens.\n"


def drop_pages(root):
    tray = pathlib.Path(root) / "in-tray"
    return sorted(p for p in tray.glob("*.md") if p.name != "README.md") if tray.is_dir() else []


def fenced(text, after):
    """The first fenced block after the line holding `after`, dedented."""
    rest = text.split(after, 1)[1]
    m = re.search(r"^( *)```\n(.*?)^\1```$", rest, re.M | re.S)
    return textwrap.dedent(m.group(2))


# --- the page, as a unit -----------------------------------------------------------------

class TestThePage(unittest.TestCase):
    def test_the_page_is_pinned_field_by_field(self):
        page, escaped = odrop.render_page(MESSAGE, "alpha", "clipboard", "2026-10-14 09:12")
        self.assertEqual(page, "# Drop: Could you look at the login page?\n\n"
                               "- dropped: 2026-10-14 09:12\n- project: alpha\n- via: clipboard\n- status: unsorted\n\n"
                               "## Text\n\n"
                               "Could you look at the login page?\nIt shows an error on narrow screens.\n")
        self.assertEqual(escaped, 0)
        parsed = odrop.parse_page(page)
        self.assertEqual(parsed["problems"], [])
        self.assertEqual(parsed["fields"], {"dropped": "2026-10-14 09:12", "project": "alpha", "via": "clipboard",
                                            "status": "unsorted"})
        self.assertEqual(parsed["text"], MESSAGE.rstrip("\n"))
        # No project is written as such, and via names a file by its basename.
        page, _ = odrop.render_page(MESSAGE, "  ", "file thread.txt", "2026-10-14 09:12")
        self.assertIn("\n- project: none given\n- via: file thread.txt\n", page)
        self.assertIsNone(odrop.project_text(odrop.parse_page(page)["fields"]))

    def test_line_ends_the_end_and_anything_outside_ascii(self):
        page, escaped = odrop.render_page("café — down\r\nsecond line  \r\n\r\n\n", "the café site",
                                          "stdin", "2026-10-14 09:12")
        page.encode("ascii")
        self.assertTrue(page.startswith("# Drop: caf\\xe9 \\u2014 down\n"))
        self.assertIn("- project: the caf\\xe9 site\n", page)
        self.assertTrue(page.endswith("## Text\n\ncaf\\xe9 \\u2014 down\nsecond line\n"))
        self.assertNotIn("\r", page)
        self.assertEqual(escaped, 3)

    def test_the_heading_is_the_first_line_trimmed_to_sixty(self):
        self.assertEqual(odrop.heading_text("\n\n   Hi   there  \nmore"), "Hi there")
        long = "word " * 30
        head = odrop.heading_text(long)
        self.assertLessEqual(len(head), 60)
        self.assertTrue(head.endswith("..."))
        self.assertEqual(head, "word " * 10 + "word...")
        self.assertEqual(odrop.heading_text("x" * 70), "x" * 57 + "...")
        self.assertEqual(odrop.heading_text("x" * 60), "x" * 60)

    def test_what_no_page_can_hold_is_refused(self):
        for text, via, stamp, words in (("  \n\n", "stdin", "2026-10-14 09:12", "empty"),
                                        ("x", "email", "2026-10-14 09:12", "via is"),
                                        ("x", "stdin", "2026-10-14", "dropped is")):
            with self.assertRaises(h.HelperError) as cm:
                odrop.render_page(text, "", via, stamp)
            self.assertIn(words, str(cm.exception))

    def test_a_page_that_does_not_read_says_why(self):
        page, _ = odrop.render_page(MESSAGE, "alpha", "stdin", "2026-10-14 09:12")
        self.assertEqual(odrop.parse_page(page.replace("- status: unsorted", "- status: lost"))["problems"],
                         ["status is not unsorted or sorted: 'lost'"])
        self.assertIn("it has no via line", odrop.parse_page(page.replace("- via: stdin\n", ""))["problems"])
        self.assertIn("it has no '## Text' section", odrop.parse_page(page.replace("## Text", "## Body"))["problems"])
        self.assertIn("its first line is not '# Drop: ...'", odrop.parse_page("hello\n")["problems"])

    def test_a_project_resolves_by_its_name_in_any_case(self):
        names = ["alpha", "beta-site"]
        self.assertEqual(odrop.resolve_project("alpha", names), "alpha")
        self.assertEqual(odrop.resolve_project("Beta-Site", names), "beta-site")
        self.assertEqual(odrop.resolve_project("alpha: src/", names), "alpha")
        self.assertIsNone(odrop.resolve_project("the website", names))
        self.assertIsNone(odrop.resolve_project(None, names))

    def test_names_pages_and_ages(self):
        e = Env(self)
        root = e.tmp / "office"
        (root / "in-tray").mkdir(parents=True)
        self.assertEqual(odrop.free_name(root, "2026-10-14", "login"), "in-tray/2026-10-14-login.md")
        (root / "in-tray/2026-10-14-login.md").write_text("x")
        self.assertEqual(odrop.free_name(root, "2026-10-14", "login"), "in-tray/2026-10-14-login-2.md")
        self.assertEqual(odrop.resolve_page(root, "in-tray/2026-10-14-login.md"), "in-tray/2026-10-14-login.md")
        self.assertEqual(odrop.resolve_page(root, "2026-10-14-login"), "in-tray/2026-10-14-login.md")
        with self.assertRaises(h.HelperError):
            odrop.resolve_page(root, "README.md")
        with self.assertRaises(h.HelperError):
            odrop.resolve_page(root, "2026-10-14-gone")
        self.assertEqual(odrop.age_days({"dropped": "2026-10-11 09:00"}, "2026-10-14"), 3)
        self.assertIsNone(odrop.age_days({"dropped": "soon"}, "2026-10-14"))

    def test_what_the_tray_and_the_opener_say(self):
        self.assertIn("2 unsorted drop(s) from the in-tray ride beside the request",
                      odrop.carried_words(["a.md", "b.md"], "beside the request"))
        self.assertIn("and 2 more", odrop.carried_words([f"{n}.md" for n in range(7)], "x"))
        self.assertIn("sort the ones you can judge in a Sort section", odrop.opener_line(1))
        self.assertIn("owes them no Sort", odrop.opener_line(1, sitting=True))


# --- office drop, the command -------------------------------------------------------------

class TestDrop(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_a_drop_is_one_page_committed_alone_and_the_in_tray_arrives_with_it(self):
        (self.root / "notepad" / "draft.md").write_text("uncommitted\n")
        proc = self.e.run("drop", "--project", "alpha", cwd=self.root, input=MESSAGE, check=0)
        page = proc.stdout.strip()
        self.assertRegex(page, r"^in-tray/\d{4}-\d{2}-\d{2}-could-you-look-at-the-login-page\.md$")
        self.assertIn("took 2 line(s) from stdin: Could you look at the login page?", proc.stderr)
        text = (self.root / page).read_text(encoding="ascii")
        self.assertTrue(text.startswith("# Drop: Could you look at the login page?\n\n- dropped: "))
        self.assertIn("\n- project: alpha\n- via: stdin\n- status: unsorted\n\n## Text\n\n", text)
        # The arrival rides in the drop's own commit, and nothing else does.
        shown = self.e.git(self.root, "show", "--name-only", "--format=%s", "HEAD").split("\n")
        self.assertEqual(shown[0], f"office drop: {page.split('/')[1][:-3]}")
        self.assertEqual(sorted(l for l in shown[1:] if l),
                         sorted([page, "in-tray/README.md", "floor-plan/manifest.toml", "bale.toml"]))
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "?? notepad/draft.md")
        plan = tomllib.loads((self.root / "floor-plan/manifest.toml").read_text())
        self.assertEqual(plan["spaces"]["in-tray"], {"path": "in-tray", "hung": False, "filed": False})
        self.assertIn("in-tray", tomllib.loads((self.root / "bale.toml").read_text())["pack"]["include_group_triggers"])
        self.assertEqual((self.root / "in-tray/README.md").read_text(),
                         (REPO / "templates/in-tray-README.md").read_text())
        self.assertIn("hung items: bale.toml include group matches the floor plan",
                      self.e.run("status", cwd=self.root, check=0).stdout)

    def test_the_second_drop_is_its_page_alone_and_the_same_words_take_a_counter(self):
        first = self.e.run("drop", cwd=self.root, input="same words\n", check=0).stdout.strip()
        second = self.e.run("drop", cwd=self.root, input="same words\n", check=0).stdout.strip()
        self.assertTrue(second.endswith("-same-words-2.md"), second)
        self.assertNotEqual(first, second)
        self.assertEqual(self.e.git(self.root, "show", "--name-only", "--format=", "HEAD").split(), [second])
        self.assertIn("- project: none given\n", (self.root / second).read_text())

    def test_a_file_and_stdin_say_how_the_text_came(self):
        thread = self.e.tmp / "thread.txt"
        thread.write_text("From the thread\r\nsecond\r\n")
        page = self.e.run("drop", str(thread), "--project", "the website", cwd=self.root, check=0).stdout.strip()
        text = (self.root / page).read_text()
        self.assertIn("- project: the website\n- via: file thread.txt\n", text)
        self.assertTrue(text.endswith("## Text\n\nFrom the thread\nsecond\n"))
        page = self.e.run("drop", "-", cwd=self.root, input="piped words\n", check=0).stdout.strip()
        self.assertIn("- via: stdin\n", (self.root / page).read_text())

    def test_capture_never_refuses_unfounded_or_out_of_step(self):
        from test_office import NEXT, MIGRATION_ADD_SPACE
        self.assertIn("unfounded", self.e.run("drop", cwd=self.root, input="x\n", check=0).stderr)
        behind = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Adds a handbook.", MIGRATION_ADD_SPACE)])
        self.assertIn("behind", self.e.run("drop", cwd=self.root, input="b\n", bin_path=behind, check=0).stderr)
        ahead = self.e.fake_install("0.0.9")
        self.assertIn("migrated past", self.e.run("drop", cwd=self.root, input="a\n", bin_path=ahead, check=0).stderr)
        self.assertEqual(len(drop_pages(self.root)), 3)

    def test_an_empty_text_and_an_unknown_flag_are_the_refusals(self):
        proc = self.e.run("drop", cwd=self.root, input=" \n\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("nothing to drop", proc.stderr)
        self.assertEqual(self.e.run("drop", "--loud", cwd=self.root).returncode, 1)
        self.assertEqual(self.e.run("drop", str(self.e.tmp / "gone.txt"), cwd=self.root).returncode, 1)
        self.assertFalse((self.root / "in-tray").exists())

    def test_status_checks_an_in_tray_that_exists(self):
        self.assertIn("in-tray:    none in this office; it arrives with the first office drop",
                      self.e.run("status", cwd=self.root, check=0).stdout)
        self.e.run("drop", cwd=self.root, input=MESSAGE, check=0)
        self.assertIn("in-tray:    matches the install's catalog; 1 unsorted drop(s)",
                      self.e.run("status", cwd=self.root, check=0).stdout)
        page = drop_pages(self.root)[0]
        page.write_text(page.read_text().replace("- status: unsorted", "- status: maybe"))
        (self.root / "in-tray/notes.txt").write_text("x")
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn("in-tray:    2 problem(s)", out)
        self.assertIn("status is not unsorted or sorted", out)
        self.assertIn("in-tray/notes.txt is not a drop's page", out)


class TestDropOnATerminal(unittest.TestCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        from test_start import git_repo
        self.e.run("projects", "add", "alpha", str(git_repo(self.e.tmp / "alpha")), cwd=self.root, check=0)
        clip = self.e.tmp / "clipboard.txt"
        clip.write_text("Hi,\r\nthe export button does nothing.\r\n")
        machine = self.e.home / ".config" / "office-src" / "machine.toml"
        machine.parent.mkdir(parents=True, exist_ok=True)
        machine.write_text(f'paste_command = "cat {clip}"\n')

    def test_from_the_clipboard_it_says_what_it_took_and_asks_the_project(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "drop"], self.root, self.e.env, [
            (b"by its key, or in any words; a plain return leaves it for the sort (--project) [return skips]:", "?"),
            (b"the drop is taken either way.", "Alpha"),
        ])
        self.assertEqual(code, 0, seen)
        # 0.22.0: each of the office's projects has a key; any words are
        # taken as typed.
        self.assertIn("  [1] alpha", seen)
        self.assertIn("took 2 line(s) from the clipboard: Hi,", seen)
        text = drop_pages(self.root)[0].read_text()
        self.assertIn("- project: Alpha\n- via: clipboard\n", text)
        self.assertTrue(text.endswith("Hi,\nthe export button does nothing.\n"))

    def test_a_clipboard_turned_off_names_the_file_and_stdin_instead(self):
        (self.e.home / ".config" / "office-src" / "machine.toml").write_text('paste_command = ""\n')
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "drop"], self.root, self.e.env, [])
        self.assertEqual(code, 1, seen)
        self.assertIn("turns reading the clipboard off: give the message as a file (office drop FILE) or on stdin "
                      "(office drop -)", " ".join(seen.split()))
        self.assertEqual(drop_pages(self.root), [])

    def test_a_plain_return_leaves_the_project_empty(self):
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "drop"], self.root, self.e.env, [
            (b"(--project) [return skips]:", ""),
        ])
        self.assertEqual(code, 0, seen)
        self.assertIn("- project: none given\n", drop_pages(self.root)[0].read_text())


# --- every session office start sends out carries the unsorted drops ---------------------------

class DropCase(StartCase):
    """StartCase's office (alpha, its ride-alongs, folder 1 on alpha: src)
    with drops in its in-tray."""

    def drop(self, text=MESSAGE, project=None):
        args = ["drop"] + (["--project", project] if project else [])
        return self.e.run(*args, cwd=self.root, input=text, check=0).stdout.strip()

    def sid_of(self, proc):
        return re.search(r"^(?:Packed|Joined) (\S+)", proc.stdout, re.M).group(1)


class TestTheRideAlong(DropCase):
    def test_a_project_session_carries_them_in_the_offices_context(self):
        a = self.drop(project="alpha")
        b = self.drop("Another one\n")
        # Oldest first: by the dropped stamp (to the minute), then by name,
        # as office_drop.drops orders them; the two may straddle a minute.
        first, second = sorted([a, b], key=lambda r: (odrop.read_drop(self.root, r)["dropped"], pathlib.Path(r).name))
        proc = self.start("fix-login", "--on", "alpha", "--goal", "Fix the login redirect")
        tray = self.tray(proc)
        names = tar_names(tray / "context-home.tar.gz")
        self.assertIn(f"home/{a}", names)
        self.assertIn(f"home/{b}", names)
        self.assertNotIn("home/in-tray/README.md", names)
        self.assertIn("2 unsorted drop(s) from the in-tray ride beside the request, in the office's context: "
                      f"{first.split('/')[1]}, {second.split('/')[1]}", proc.stdout)
        opener = opener_from(proc.stdout)
        self.assertEqual(opener[-1], odrop.opener_line(2))
        self.assertEqual(opener[-2], "")
        # The goal is the start's own: the drops change nothing about it.
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(argv[1], "Fix the login redirect")

    def test_an_office_session_carries_them_in_its_request(self):
        a = self.drop()
        proc = self.start("fix-login", "--in-office", "--goal", "Plan the fix")
        sid = self.sid_of(proc)
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertIn(["--include", a], [argv[i:i + 2] for i in range(len(argv))])
        self.assertNotIn(["--write", a], [argv[i:i + 2] for i in range(len(argv))])
        self.assertIn(f"request-001/context/{a}", tar_names(self.tray(proc) / f"request-{sid}.tar.gz"))
        self.assertIn("ride inside the request", proc.stdout)

    def test_a_sitting_reads_them_and_owes_no_sort(self):
        self.drop()
        proc = self.start("fix-login", "--in-office", "--read-only", "--goal", "Plan the wave")
        self.assertEqual(opener_from(proc.stdout)[-1], odrop.opener_line(1, sitting=True))

    def test_none_unsorted_none_ride_and_nothing_is_said(self):
        page = self.root / self.drop()
        page.write_text(page.read_text().replace("- status: unsorted", "- status: sorted"))
        self.e.git(self.root, "commit", "-qam", "sorted by hand, for the test")
        proc = self.start("fix-login", "--on", "alpha", "--goal", "g")
        self.assertNotIn("unsorted drop", proc.stdout)
        self.assertNotIn("in-tray/", "\n".join(tar_names(self.tray(proc) / "context-home.tar.gz")))
        self.assertNotIn("unsorted drop", "\n".join(opener_from(proc.stdout)))


# --- office start --drop: the direct path ----------------------------------------------------

class TestStartDrop(DropCase):
    def test_one_command_mints_the_folder_moves_the_drop_and_sends_it_out(self):
        page = self.drop(project="alpha")
        before = (self.root / page).read_bytes()
        proc = self.start("--drop", page)
        sid = self.sid_of(proc)
        folders = sorted(self.root.glob("desk/*-could-you-look-at-the-login-page"))
        self.assertEqual(len(folders), 1)
        folder = folders[0]
        md = (folder / "folder.md").read_text()
        for line in ("# Could you look at the login page?", "- number: 2", "- size: small", "- lane: alpha",
                     "- source: drop", "- status: open"):
            self.assertIn(line + "\n", md)
        name = pathlib.Path(page).name
        # Moved, bytes as they were; the in-tray is one page lighter.
        self.assertEqual((folder / "drops" / name).read_bytes(), before)
        self.assertFalse((self.root / page).exists())
        history = md.split("## History", 1)[1]
        dropped = re.search(rf"^- \d{{4}}-\d{{2}}-\d{{2}} dropped: drops/{re.escape(name)}, via stdin$", history, re.M)
        opened = re.search(rf"^- \d{{4}}-\d{{2}}-\d{{2}} opened: {sid}$", history, re.M)
        self.assertTrue(dropped and opened, history)
        self.assertLess(dropped.start(), opened.start())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        # Packed on the lane's project, with the goal and the sort brief.
        (cwd, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(cwd, os.path.realpath(self.proj))
        self.assertEqual(argv[1], odrop.DROP_GOAL)
        self.assertIn(["--constraint", ob.PROJECT_CONSTRAINT], [argv[i:i + 2] for i in range(len(argv))])
        tray = self.tray(proc)
        with tarfile.open(tray / f"request-{sid}.tar.gz") as t:
            brief = t.extractfile("request-001/README.md").read().decode()
        self.assertIn(f"--- DROP BEGIN drops/{name} ---\n{before.decode().rstrip()}\n--- DROP END ---\n", brief)
        self.assertIn(f"### {name}`, in the format below", brief)
        self.assertIn("Folder 2,", brief)
        self.assertIn(fenced(DOCTRINE.read_text(), "key on its own line, in this order"), brief)
        # The folder rides as for every session, the drop inside it.
        self.assertIn(f"home/desk/{folder.name}/drops/{name}", tar_names(tray / "context-home.tar.gz"))

    def test_the_lane_flag_names_the_project_a_drop_does_not(self):
        page = self.drop(project="the website")
        before = sorted(p.name for p in (self.root / "desk").iterdir())
        proc = self.start("--drop", page, check=1)
        self.assertIn("names no project this office scopes (alpha): give --lane PROJECT; nothing was written",
                      proc.stderr)
        self.assertEqual(sorted(p.name for p in (self.root / "desk").iterdir()), before)
        self.assertTrue((self.root / page).exists())
        self.assertEqual(self.fake.packs(), [])
        proc = self.start("--drop", pathlib.Path(page).stem, "--lane", "alpha: src", "--size", "medium",
                          "--title", "Fix the narrow login", "--goal", "Fix the login error")
        md = next(self.root.glob("desk/*-fix-the-narrow-login/folder.md")).read_text()
        self.assertIn("- lane: alpha: src\n- source: drop\n", md)
        self.assertIn("- size: medium\n", md)
        (_, argv), = [p for p in self.fake.packs() if "--context" not in p[1]]
        self.assertEqual(argv[1], "Fix the login error")
        self.assertIn(["--write", "src"], [argv[i:i + 2] for i in range(len(argv))])

    def test_refusals_write_nothing(self):
        page = self.drop(project="alpha")
        head = self.e.git(self.root, "rev-parse", "HEAD")
        for args, words in ((("--drop", page, "--in-office"), "no --in-office"),
                            (("--drop", page, "--on", "alpha"), "no --on"),
                            (("--drop", page, "--read-only"), "no --read-only"),
                            (("--drop", page, "--brief", "x.md"), "no --brief"),
                            (("--drop", page, "x.bale-bundle"), "no bundle"),
                            (("fix-login", "--on", "alpha", "--goal", "g", "--lane", "alpha"), "go with --drop"),
                            (("--drop", "in-tray/2026-01-01-gone.md"), "the in-tray has no 2026-01-01-gone.md"),
                            (("--drop", page, "--lane", "gamma"), "--lane gamma names no project"),
                            (("--drop", page, "--size", "huge"), "size is one of")):
            proc = self.start(*args, check=1)
            self.assertIn(words, proc.stderr, args)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        self.assertTrue((self.root / page).exists())
        self.assertEqual(self.fake.packs(), [])

    def test_the_one_writer_rule_names_the_session_that_holds_the_in_tray(self):
        page = self.drop(project="alpha")
        desk = sorted(p.name for p in (self.root / "desk").iterdir())
        (self.root / ".bale").mkdir(exist_ok=True)
        sid = "2026-10-14-tidy-office-001"
        state = json.loads(self.fake.state.read_text()) if self.fake.state.is_file() else {"repos": {}, "fail": []}
        state["repos"][os.path.realpath(self.root)] = {"sessions": [sid], "scopes": {sid: ["in-tray"]}, "outbox": []}
        self.fake.state.write_text(json.dumps(state))
        proc = self.start("--drop", page, check=1)
        self.assertIn(f"{sid} holds in-tray", proc.stderr)
        self.assertIn("the one-writer rule", proc.stderr)
        self.assertTrue((self.root / page).exists())
        self.assertEqual(sorted(p.name for p in (self.root / "desk").iterdir()), desk)

    def test_a_start_whose_session_does_not_go_out_names_the_line_that_retries_it(self):
        page = self.drop(project="alpha")
        name = pathlib.Path(page).name
        self.fake.refuse_next_pack()
        proc = self.start("--drop", page, check=1)
        folder = next(self.root.glob("desk/*-could-you-look-at-the-login-page")).name
        retry = proc.stderr.strip().splitlines()[-1]
        self.assertEqual(retry, f"office start {folder} --drop {name}")
        self.assertTrue((self.root / "desk" / folder / "drops" / name).is_file())
        state = json.loads(self.fake.state.read_text())
        state["fail"] = []
        self.fake.state.write_text(json.dumps(state))
        proc = self.start(*retry.split()[2:])
        sid = self.sid_of(proc)
        md = (self.root / "desk" / folder / "folder.md").read_text()
        self.assertIn(f"opened: {sid}", md)
        self.assertEqual(md.count(" dropped: "), 1)


class TestStartDropOnATerminal(DropCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_a_drop_with_no_project_asks_the_project_by_key_and_nothing_else(self):
        page = self.drop()
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "--drop", page], self.root, self.e.env, [
            (b"Which project the drop is for, by its key (--lane PROJECT):", "gamma"),
            (b"a key from the list above (1 to 1)", "1"),
        ])
        self.assertEqual(code, 0, seen)
        for gone in ("(--size)", "[return: the whole repo]", "Which ride"):
            self.assertNotIn(gone, seen)
        md = next(self.root.glob("desk/*-could-you-look-at-the-login-page/folder.md")).read_text()
        self.assertIn("- size: small\n- lane: alpha\n- source: drop\n", md)
        self.assertIn("- status: open\n", md)


# --- the walk-in, the desk and the Next line --------------------------------------------------

class TestTheDeskAndTheNextLine(DropCase):
    def test_the_walk_in_counts_them_the_desk_lists_them_and_the_next_line_sends_the_oldest(self):
        self.e.run("close", "fix-login", cwd=self.root, check=0)
        walk = self.e.run(cwd=self.root, check=0).stdout
        self.assertNotIn("In-tray:", walk)
        a = self.drop(project="alpha")
        b = self.drop("Second thing\n")
        walk = self.e.run(cwd=self.root, check=0).stdout
        self.assertIn("In-tray: 2 unsorted drop(s), the oldest dropped today (office desk lists them)", walk)
        self.assertEqual(walk.strip().splitlines()[-1].split("  (")[0], f"Next: office start --drop {a}")
        desk = self.e.run("desk", cwd=self.root, check=0).stdout
        self.assertIn("Unsorted drops (in-tray/; office start --drop in-tray/PAGE sends one out):", desk)
        self.assertIn(f"  {pathlib.Path(a).name}  (alpha)  Could you look at the login page?", desk)
        self.assertIn(f"  {pathlib.Path(b).name}  (no project)  Second thing", desk)

class TestTheNextRule(unittest.TestCase):
    """The Next line's drop rule as a pure function: no office needed."""

    def test_the_rule_in_its_place(self):
        alpha = [{"name": "alpha"}, {"name": "beta"}]
        old = {"rel": "in-tray/2026-10-10-old.md", "project": "the website"}
        new = {"rel": "in-tray/2026-10-12-new.md", "project": "Alpha"}
        flying = {"fields": {"lane": ["alpha: src"]}}
        groups = {"moves": (0, "", []), "ready": [], "drops": [old, new], "flying": []}
        cmd, why = ob.next_move("current", True, [], groups, alpha, 0)
        self.assertEqual(cmd, "office start --drop in-tray/2026-10-10-old.md --lane LANE")
        self.assertIn("(alpha, beta)", why)
        groups["drops"] = [new]
        self.assertEqual(ob.next_move("current", True, [], groups, alpha, 0)[0],
                         "office start --drop in-tray/2026-10-12-new.md")
        # A session in flight on that lane holds the drop back.
        groups["flying"] = [flying]
        self.assertIsNone(ob.drop_move(groups["drops"], groups, alpha))
        self.assertEqual(ob.next_move("current", True, [], groups, alpha, 0),
                         ob.next_move("current", True, [], dict(groups, drops=[]), alpha, 0))
        # After the moves, before the founding; quiet with no project.
        groups = {"moves": (1, "a sitting", []), "ready": [], "drops": [new], "flying": []}
        self.assertEqual(ob.next_move("current", True, [], groups, alpha, 0)[0], "office moves")
        groups["moves"] = (0, "", [])
        self.assertEqual(ob.next_move("current", False, [], groups, alpha, 0)[0], "office start --drop in-tray/2026-10-12-new.md")
        self.assertEqual(ob.next_move("current", True, [], groups, [], 0)[0], "office projects add")


# --- the doctrine, the brief and the declarations --------------------------------------------

class TestDoctrineAndDeclarations(unittest.TestCase):
    def setUp(self):
        self.doctrine = DOCTRINE.read_text(encoding="ascii")

    def test_the_core_carries_the_drops_paragraph_under_fifteen_lines(self):
        lines = self.doctrine.splitlines()
        banner = next(i for i, l in enumerate(lines) if l.startswith("> **PAST THE CORE.**"))
        start = next(i for i, l in enumerate(lines) if l.startswith("- A session may carry drops"))
        self.assertLess(start, banner)
        fence = next(i for i in range(start, banner) if lines[i].strip() == "```")
        prose = [l for l in lines[start:fence] if l.strip()]
        self.assertLessEqual(len(prose), 15)

    def test_the_doctrine_and_the_brief_pin_one_sort_format(self):
        core = fenced(self.doctrine, "key on its own line, in this order")
        brief = fenced(BRIEF_TEMPLATE.read_text(), "in\nthis order (values illustrative)")
        self.assertEqual(core, brief)
        keys = re.findall(r"^- ([a-z]+): ", core, re.M)
        self.assertEqual(keys, ["project", "folder", "goal", "size", "tell", "facts"])
        self.assertRegex(core.splitlines()[0], r"^### \d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")
        self.assertIn("\n#### Brief\n", core)

    def test_the_verb_the_space_and_the_page_are_declared(self):
        verbs = tomllib.loads((REPO / "share/verbs.toml").read_text())["verbs"]
        self.assertTrue(verbs["drop"]["built"])
        self.assertEqual(verbs["drop"]["kind"], "script")
        self.assertIn("in-tray/{date}-{slug}.md", verbs["start"]["writes"])
        spaces = tomllib.loads((REPO / "share/spaces.toml").read_text())["spaces"]
        self.assertEqual(spaces["in-tray"], {"path": "in-tray"})
        self.assertIn("| in-tray/ | drops waiting to be sorted | no; arrives with the first drop | no | no |",
                      self.doctrine)
        self.assertIn("| drop | script: capture a message or a thread as one in-tray page, with an optional "
                      "free-text project; while a meeting is on", self.doctrine)
        self.assertIn("dropped", h.HISTORY_VERBS)
        # The release says so, and the readme.
        self.assertGreaterEqual(h.compare_versions((REPO / "VERSION").read_text().strip(), "0.19.0"), 0)
        releases = (REPO / "RELEASES.md").read_text()
        self.assertLess(releases.index("## 0.19.0"), releases.index("## 0.18.0"))
        for words in ("office drop", "office start --drop", "in-tray"):
            self.assertIn(words, releases.split("## 0.19.0", 1)[1].split("## 0.18.0", 1)[0])
            self.assertIn(words, (REPO / "README.md").read_text())
        # The page's shape, as the doctrine states it, is the one the code writes.
        for words in ("`- dropped: DATE TIME`", "`- project:`", "`none given`", "`- via:`", "`- status:`",
                      "`## Text`", "`# Drop: ...`"):
            self.assertIn(words, " ".join(self.doctrine.split()))


if __name__ == "__main__":
    unittest.main()
