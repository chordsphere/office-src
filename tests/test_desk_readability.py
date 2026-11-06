"""Tests for office-src 0.49.0: the desk made readable.

One class per item of the brief (2026-11-06-desk-readability-001), a unit
class beside a verb class where the item has a unit worth pinning:

1. office map is two tables: the projects, one row each, then the folders,
   one row each, grouped by project with the office's own last, open
   before closed, newest number first; a project's closed folders past
   the newest three fold into one line, --all unfolds them, office map
   PROJECT folds nothing; on a terminal the page is cut to its width (the
   title gives way first), piped every cell is whole; it writes nothing;
2. every list of folders offered by key names the project
   (`folder N, TITLE (PROJECT)`), and the desk's line says it after the
   folder's name;
3. the occupant's words show as he wrote them: folder.md keeps the escape,
   the map, a picker and the desk show the character;
4. office start --bundle NAME resolves the name before anything is asked
   or written: the stem with or without its extension found in the
   downloads, and a name found nowhere refused by name, exit 1, nothing
   asked, piped and on a terminal.

Item 5, the sweep for tests that hard-code a session's day, is the tests
it changed (notes.md lists them). The worlds are the suite's own:
tests/test_land.py's LandCase (an office scoping alpha, its fake bale,
folder 1 on the desk with its lane on alpha). Every project and folder
here is invented. The terminal classes run in the serial lane. Run with
the rest of the suite:

    tests/run.sh test_desk_readability
"""

import os
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_start import on_a_terminal, git_repo  # noqa: E402
from test_land import LandCase, bundle_file  # noqa: E402
from test_home_screen import downloads_set  # noqa: E402

import office_helper as oh  # noqa: E402
import office_map as om  # noqa: E402

# A title with words past ASCII, as he might type one: curly quotes and an
# accent.
QUOTED = "Fix the \u201clogin\u201d caf\u00e9 page"


def rows_of(out, header):
    """The table under the header line that starts with header: its lines,
    up to the first blank one."""
    lines = out.splitlines()
    i = next(n for n, line in enumerate(lines) if line.startswith(header))
    end = next((n for n in range(i, len(lines)) if not lines[n].strip()), len(lines))
    return lines[i:end]


class ReadableCase(LandCase):
    def head(self):
        return self.e.git(self.root, "rev-parse", "HEAD").strip()

    def closed_on_alpha(self, n):
        """n folders opened on alpha and closed, oldest first: their
        numbers."""
        numbers = []
        for i in range(n):
            rel = self.run_office("open", f"old-job-{i}", "--lane", "alpha", check=0).stdout.strip()
            self.run_office("close", rel.split("/")[1], check=0)
            numbers.append(int(oh.parse_folder((self.root / "filing-cabinet" / rel.split("/")[1] / "folder.md")
                                               .read_text())["fields"]["number"][0]))
        return numbers


# --- 1. two tables --------------------------------------------------------------------------

class TestTheTablesAsAUnit(unittest.TestCase):
    def test_aligned_under_a_header_and_the_title_gives_way_first(self):
        rows = [["folder 1", "alpha", "A rather long title for a job", "small", "open"],
                ["folder 12", "the office", "Short", "-", "in flight 3 days"]]
        whole = om.table(om.FOLDER_HEADER, rows)
        self.assertEqual(whole[0], "FOLDER     PROJECT     TITLE                          SIZE   STATE")
        self.assertEqual(whole[1], "folder 1   alpha       A rather long title for a job  small  open")
        self.assertEqual(whole[2], "folder 12  the office  Short                          -      in flight 3 days")
        cut = om.table(om.FOLDER_HEADER, rows, width=66, give=om.FOLDER_GIVE)
        self.assertTrue(all(len(line) <= 66 for line in cut), cut)
        self.assertIn("  A rather long t...  small  open", cut[1])
        # Past every column's floor the table runs on rather than lose more.
        self.assertEqual(len(om.table(om.FOLDER_HEADER, rows, width=40, give=om.FOLDER_GIVE)[2]), 64)
        self.assertTrue(cut[2].endswith("in flight 3 days"), "the state is whole while the title can give way")

    def test_a_fold_line_sits_under_its_column_and_is_never_cut(self):
        out = om.table(("A", "B", "C"), [["x", "y", "zzzz"], "and 4 more closed: office map --all"], width=8,
                       under=2)
        self.assertEqual(out[-1], "      and 4 more closed: office map --all")

    def test_a_projects_row_says_its_rides_and_after_land_in_one_cell(self):
        p = {"name": "alpha", "path": "~/alpha", "host": None, "problem": None, "audience": None, "paused": False,
             "rides": ["~/beta/notes.md", "~/beta/plan.md"], "after_land": ["./install.sh", "make test"]}
        self.assertEqual(om.project_row(p), ["alpha", "here (~/alpha)", "none", "no",
                                             "rides: ~/beta/notes.md, ~/beta/plan.md; after: ./install.sh; make test"])
        p.update(host="me@box", audience="origin", author="Pat <p@x.org>", base="main", paused=True, rides=[],
                 after_land=[], declaration_problems=["rides: ~/gone is not there"])
        self.assertEqual(om.project_row(p), ["alpha", "on me@box (~/alpha)", "origin, author Pat <p@x.org>, base main",
                                             "yes", "declaration problem: rides: ~/gone is not there"])


class TestTheMapsTwoTables(ReadableCase):
    def test_projects_then_folders_open_before_closed_and_the_rest_folded(self):
        git_repo(self.e.tmp / "beta", {"README.md": "beta\n"})
        self.run_office("projects", "add", "beta", str(self.e.tmp / "beta"), check=0)
        closed = self.closed_on_alpha(5)
        self.run_office("open", "tidy-notes", "--title", "Tidy the notes", "--lane", "the office", check=0)
        sid = self.start("fix-login", "--on", "alpha", "--goal", "g")
        before = self.head()
        out = self.run_office("map", check=0).stdout
        projects = rows_of(out, "PROJECT ")
        self.assertRegex(projects[0], r"^PROJECT +WHERE +AUDIENCE +PAUSED +RIDES AND AFTER-LAND$")
        self.assertRegex(projects[1], rf"^alpha +here \({re.escape(str(self.proj))}\) +none +no +after: touch "
                                      r"AFTER-LAND-RAN$")
        self.assertRegex(projects[2], r"^beta +here \(.*\) +none +no +none$")
        folders = rows_of(out, "FOLDER ")
        self.assertRegex(folders[0], r"^FOLDER +PROJECT +TITLE +SIZE +STATE$")
        # alpha's open folder first, then its newest three closed, the rest
        # folded under the title column; then the office's own.
        self.assertRegex(folders[1], r"^folder 1 +alpha +fix-login +- +in flight (just now|\d+ (minutes?|hours?|days?))$")
        self.assertNotIn(sid, out, "the session's id stays in office map N")
        for line, n in zip(folders[2:5], sorted(closed, reverse=True)[:3]):
            self.assertRegex(line, rf"^folder {n} +alpha +old-job-\d +- +done$")
        title_at = folders[0].index("TITLE")
        self.assertEqual(folders[5], " " * title_at + "and 2 more closed: office map --all")
        self.assertRegex(folders[6], r"^folder \d+ +the office +Tidy the notes +- +ready$")
        self.assertEqual(len(folders), 7)
        self.assertTrue(out.rstrip("\n").endswith("office map N shows one folder's whole record and the lines that "
                                                   "change it."))
        # --all: every closed folder, nothing folded.
        every = rows_of(self.run_office("map", "--all", check=0).stdout, "FOLDER ")
        self.assertEqual(len(every), 1 + 1 + 5 + 1)
        self.assertNotIn("more closed", "\n".join(every))
        # One project: its rows in both tables, nothing folded.
        only = self.run_office("map", "alpha", check=0).stdout
        self.assertEqual(len(rows_of(only, "PROJECT ")), 2)
        self.assertEqual(len(rows_of(only, "FOLDER ")), 1 + 1 + 5)
        self.assertNotIn("beta", only)
        self.assertNotIn("Tidy the notes", only)
        self.assertEqual(self.head(), before, "the map writes nothing")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "")

    def test_a_lane_naming_no_project_here_is_said_in_its_row(self):
        self.run_office("open", "elsewhere", "--lane", "gamma: src", check=0)
        out = self.run_office("map", check=0).stdout
        self.assertRegex(out, r"\nfolder 2 +gamma, not a project here +elsewhere +- +ready\n")

    def test_all_goes_with_the_map_never_a_folders_record(self):
        proc = self.run_office("map", "--all", "1", check=1)
        self.assertIn("--all goes with the map or a project", proc.stderr)
        proc = self.run_office("map", "--wide", check=1)
        self.assertIn("office map does not know --wide; it takes --all, a project or a folder", proc.stderr)


class TestTheMapOnATerminal(ReadableCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_cut_to_the_terminal_and_whole_piped(self):
        long_title = "Cut the start-up of every helper the office runs, imports first and then the rest"
        self.run_office("folder", "1", "--title", long_title, check=0)
        env = dict(self.e.env, COLUMNS="60")
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "map"], self.root, env, [])
        self.assertEqual(code, 0, seen)
        screen = seen.replace("\r\n", "\n")
        folders = rows_of(screen, "FOLDER ")
        self.assertTrue(all(len(line) <= 60 for line in folders), folders)
        self.assertRegex(folders[1], r"^folder 1 +alpha +Cut the start-up.*\.\.\. +- +ready$")
        piped = self.run_office("map", extra={"COLUMNS": "60"}, check=0).stdout
        self.assertIn(f"  {long_title}  ", piped, "piped, every cell is whole")


# --- 2. every list of folders names its project ----------------------------------------------

class TestTheFolderLabelAsAUnit(unittest.TestCase):
    def test_the_project_the_office_no_lane_yet_and_a_lane_not_scoped(self):
        f = {"name": "2026-11-01-fix", "number": 4, "title": "Fix it", "fields": {"lane": ["alpha: src"]}}
        self.assertEqual(oh.folder_label(f, ["alpha"]), "folder 4, Fix it (alpha)")
        f["fields"]["lane"] = ["the office"]
        self.assertEqual(oh.folder_label(f, ["alpha"]), "folder 4, Fix it (the office)")
        f["fields"] = {}
        self.assertEqual(oh.folder_label(f, ["alpha"]), "folder 4, Fix it (no lane yet)")
        self.assertEqual(oh.folder_label(f, []), "folder 4, Fix it (the office)")
        f["fields"]["lane"] = ["gamma"]
        self.assertEqual(oh.folder_label(f, ["alpha"]), "folder 4, Fix it (gamma, not a project here)")
        self.assertEqual(oh.folder_label({"name": "old-one", "fields": {}}, ["alpha"]), "old-one (no lane yet)")


class TestTheDeskLineNamesTheProject(ReadableCase):
    def test_after_the_name_the_rest_as_it_was(self):
        self.run_office("open", "tidy-notes", "--lane", "the office", check=0)
        out = self.run_office("desk", check=0).stdout
        self.assertRegex(out, rf"\n  folder 1  {self.name} \(alpha\)  next: \(not written yet\)  \(sessions: 0\)")
        self.assertRegex(out, r"\n  folder 2  \S+-tidy-notes \(the office\)  next: ")


class TestThePickersNameTheProject(ReadableCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_jobs_on_the_desk_and_folders_in_desk(self):
        downloads_set(self)
        self.run_office("open", "tidy-notes", "--title", "Tidy the notes", "--lane", "the office", check=0)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [
            (b"Which job, by its key (office start FOLDER)", "zz-none"),
        ])
        screen = seen
        self.assertIn("Jobs on the desk:", screen)
        self.assertIn("[1] folder 1, fix-login (alpha)", screen)
        self.assertIn("[2] folder 2, Tidy the notes (the office)", screen)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "close"], self.root, self.e.env, [
            (b"Which folder, by its key (office close FOLDER)", "zz-none"),
        ])
        screen = seen
        self.assertIn("Folders in desk/:", screen)
        self.assertIn("[1] folder 1, fix-login (alpha)", screen)
        self.assertIn("[2] folder 2, Tidy the notes (the office)", screen)


# --- 3. his words as he wrote them -----------------------------------------------------------

class TestShownAsAUnit(unittest.TestCase):
    def test_the_inverse_of_the_escape_and_typed_backslashes_kept(self):
        for text in (QUOTED, "an emoji \U0001f600 too", "plain", ""):
            self.assertEqual(oh.shown(oh.ascii_escape(text)[0]), text)
        # Escapes ascii_escape never writes are his own typing.
        self.assertEqual(oh.shown(r"C:\x41 and \u0041 and \ud800"), r"C:\x41 and \u0041 and \ud800")
        self.assertEqual(oh.shown(r"a \\u201c"), "a \\\u201c")


class TestTheWordsAsHeWroteThem(ReadableCase):
    def setUp(self):
        super().setUp()
        self.rel = self.run_office("open", "fix-quote", "--title", QUOTED, "--lane", "alpha", check=0).stdout.strip()
        self.md = self.root / self.rel / "folder.md"

    def test_the_page_keeps_the_escape_and_the_map_and_desk_show_the_character(self):
        text = self.md.read_text(encoding="utf-8")
        self.assertTrue(text.isascii())
        self.assertIn(r"# Fix the \u201clogin\u201d caf\xe9 page", text)
        out = self.run_office("map", check=0).stdout
        self.assertRegex(out, rf"\nfolder 2 +alpha +{re.escape(QUOTED)} +- +ready\n")
        self.assertTrue(self.run_office("map", "2", check=0).stdout.startswith(f"folder 2  {QUOTED}  ("))
        # The desk's line: his words in its Next, as a session writes them.
        self.md.write_text(text.replace("## Next\n\nWhat happens next, and who moves.\n",
                                        "## Next\n\n- ask \\u201cPat\\u201d first\n"), encoding="utf-8")
        self.e.git(self.root, "commit", "-qam", "next")
        desk = self.run_office("desk", check=0).stdout
        self.assertIn("(alpha)  next: ask \u201cPat\u201d first  (sessions: 0)", desk)
        self.assertTrue(self.md.read_text(encoding="utf-8").isascii(), "only the screen is unescaped")


class TestTheWordsInAPicker(ReadableCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_the_jobs_on_the_desk_show_the_character(self):
        downloads_set(self)
        self.run_office("open", "fix-quote", "--title", QUOTED, "--lane", "alpha", check=0)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start"], self.root, self.e.env, [
            (b"Which job, by its key (office start FOLDER)", "zz-none"),
        ])
        self.assertIn(f"[2] folder 2, {QUOTED} (alpha)", seen)


# --- 4. office start --bundle NAME, resolved and refused by name -----------------------------

class BundleCase(ReadableCase):
    STEM = "2026-11-03-fix-from-bundle"

    def argv(self):
        return ["Fix it, from a bundle", "--slug", "fix-from-bundle", "--write", "src"]


class TestTheBundleByName(BundleCase):
    def test_the_stem_found_in_the_downloads_with_or_without_its_extension(self):
        downloads_set(self)
        path = bundle_file(self.downloads, self.STEM, self.argv())
        self.run_office("start", "fix-login", "--on", "alpha", "--bundle", self.STEM, check=0)
        (_, argv, _), = self.fake.calls_of("open")
        self.assertEqual(argv, ["open", str(path.resolve())], "bale is handed the file the office found")
        other = self.run_office("open", "docs-job", "--lane", "alpha: docs", check=0).stdout.strip()
        stem2 = "2026-11-03-docs-from-bundle"
        path2 = bundle_file(self.downloads, stem2, ["Docs, from a bundle", "--slug", "docs-from-bundle",
                                                    "--write", "docs"])
        self.run_office("start", other.split("/")[1], "--on", "alpha", "--bundle", f"{stem2}.bale-bundle", check=0)
        self.assertEqual(self.fake.calls_of("open")[-1][1], ["open", str(path2.resolve())])

    def test_a_name_found_nowhere_is_refused_by_name_and_nothing_is_asked_or_written(self):
        downloads_set(self)
        before = self.head()
        proc = self.run_office("start", "--bundle", "2026-11-03-not-saved", check=1)
        self.assertIn(f"[office] error: no 2026-11-03-not-saved.bale-bundle in your downloads ({self.downloads}) or "
                      "here; save it there first, or office withdraw --bundle 2026-11-03-not-saved takes it out of the "
                      "offer", proc.stderr)
        self.assertNotIn("Jobs on the desk", proc.stderr)
        self.assertEqual(self.fake.calls_of("open-check"), [])
        self.assertEqual(self.fake.calls_of("open"), [])
        self.assertEqual(self.head(), before)
        # A word ending .bale-bundle is the same name, without the flag.
        proc = self.run_office("start", "fix-login", "2026-11-03-not-saved.bale-bundle", check=1)
        self.assertIn("no 2026-11-03-not-saved.bale-bundle in your downloads", proc.stderr)

    def test_with_no_downloads_set_the_refusal_names_the_setting(self):
        proc = self.run_office("start", "--bundle", "2026-11-03-not-saved", check=1)
        self.assertIn("no 2026-11-03-not-saved.bale-bundle in your downloads (none set: downloads in "
                      f"{self.e.home}/.config/office-src/machine.toml) or here", proc.stderr)

    def test_a_file_here_by_its_stem(self):
        path = bundle_file(self.root, self.STEM, self.argv())
        self.run_office("start", "fix-login", "--on", "alpha", "--bundle", self.STEM, check=0)
        self.assertEqual(self.fake.calls_of("open")[-1][1], ["open", str(path.resolve())])


class TestTheBundleByNameOnATerminal(BundleCase):
    serial_group = "terminal"  # drives a pseudo-terminal: tests/run.sh runs it in the serial lane

    def test_refused_before_the_jobs_on_the_desk(self):
        downloads_set(self)
        code, seen = on_a_terminal(self, [str(self.e.office_bin), "start", "--bundle", "2026-11-03-not-saved"],
                                   self.root, self.e.env, [])
        screen = seen
        self.assertEqual(code, 1, screen)
        self.assertIn("no 2026-11-03-not-saved.bale-bundle in your downloads", screen)
        self.assertNotIn("Jobs on the desk", screen)
        self.assertNotIn("Which job", screen)


if __name__ == "__main__":
    unittest.main()
