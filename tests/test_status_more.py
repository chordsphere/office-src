"""Tests for office-src 0.53.0: what office status says that it did not.

1. A project's toolchain (the M10 friction report of 2026-10-27, item 10):
   for a project whose clone has a package.json with engines (or a
   .nvmrc), office status reads what the project's own login shell finds
   for each tool and says one line for a tool missing or outside its
   range, and one for a range it cannot read. On a host the read rides
   status's one connection.
2. The profile's stale line (item 16): office status names a profile line
   that says a verb or kind is not built when share/verbs.toml says the
   install builds it, and never edits the profile.

The suite runs no real ssh and no real node: the fake ssh of
tests/test_project_on_host.py stands for the host, a two-line script
stands for node, and a test's own ~/.bash_profile is the login-shell hook
the friction report describes. Run with the rest of the suite:

    tests/run.sh test_status_more
"""

import os
import pathlib
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, Env, h  # noqa: E402
from test_project_on_host import HOST  # noqa: E402
from test_host_refresh import RefreshCase, git  # noqa: E402

import office_bale as ob  # noqa: E402
import office_host as ohost  # noqa: E402

VERSION = (REPO / "VERSION").read_text().strip()


def fake_tool(directory, name, printed):
    """A program called name in directory that prints one line for
    --version, as node, npm and the rest do."""
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(f"#!/bin/sh\necho '{printed}'\n")
    (directory / name).chmod(0o755)


# --- 1. the range reader ------------------------------------------------------------------------

class TestTheRangeReader(unittest.TestCase):
    def meets(self, rng, version):
        return ohost.satisfies(ohost.found_version(version), ohost.parse_range(rng))

    def test_npm_ranges_read_as_npm_reads_them(self):
        cases = [(">=24", "22.11.0", False), (">=24", "24.0.0", True), (">= 18", "18.0.0", True),
                 (">24", "24.9.0", False), (">24", "25.0.0", True), ("<=24", "24.9.9", True), ("<24", "24.0.0", False),
                 ("24", "24.3.1", True), ("24", "25.0.0", False), ("24.x", "24.0.1", True), ("v20.1", "20.1.7", True),
                 ("=20.1.0", "20.1.1", False), ("^18.0.0", "18.5.1", True), ("^18.0.0", "19.0.0", False),
                 ("^0.2.3", "0.2.9", True), ("^0.2.3", "0.3.0", False), ("^0.0.3", "0.0.4", False),
                 ("~1.2", "1.2.9", True), ("~1.2", "1.3.0", False), ("~1", "1.9.0", True),
                 ("1.2.3 - 2.3", "2.3.9", True), ("1.2.3 - 2.3", "2.4.0", False), ("1.2.3 - 2.3.4", "2.3.4", True),
                 (">=18 <21", "20.9.9", True), (">=18 <21", "21.0.0", False), ("18.x || 20.x", "20.1.0", True),
                 ("18.x || 20.x", "19.1.0", False), ("*", "1.0.0", True), ("", "3.0.0", True)]
        for rng, version, want in cases:
            with self.subTest(rng=rng, version=version):
                self.assertEqual(self.meets(rng, version), want)

    def test_what_it_cannot_read_is_an_error_never_a_guess(self):
        for rng in ("latest", "1.2.3-beta.1", ">=x.y", "lts/*", ">=24 garbage!", None, 24):
            with self.subTest(rng=rng), self.assertRaises(ohost.RangeError):
                ohost.parse_range(rng)

    def test_a_nvmrc_reads_a_version_and_refuses_an_alias(self):
        self.assertTrue(ohost.satisfies((24, 3, 0), ohost.nvmrc_range("24\n")))
        self.assertFalse(ohost.satisfies((22, 3, 0), ohost.nvmrc_range("v24.1")))
        for alias in ("lts/*", "node", "stable", "lts/iron", ""):
            with self.subTest(alias=alias), self.assertRaises(ohost.RangeError):
                ohost.nvmrc_range(alias)

    def test_the_version_a_tool_prints(self):
        self.assertEqual(ohost.found_version("v22.11.0"), (22, 11, 0))
        self.assertEqual(ohost.found_version("bun 1.1.38"), (1, 1, 38))
        self.assertIsNone(ohost.found_version("command not found"))


class TestTheToolchainLines(unittest.TestCase):
    def lines(self, package=None, nvmrc=None, found=None):
        return ob.toolchain_lines("proj", ohost.Toolchain(package, nvmrc, found))

    def test_a_tool_missing_or_outside_its_range_is_one_line_each(self):
        package = '{"engines": {"node": ">=24", "npm": "^10", "pnpm": ">=9"}}'
        self.assertEqual(self.lines(package, found={"node": "v22.11.0", "npm": "10.9.0", "pnpm": None}), [
            "  proj: needs node >=24 (package.json engines); its shell finds node 22.11.0",
            "  proj: needs pnpm >=9 (package.json engines); its shell finds no pnpm",
        ])

    def test_a_nvmrc_is_read_for_node(self):
        self.assertEqual(self.lines(nvmrc="24", found={"node": "v22.11.0"}),
                         ["  proj: needs node 24 (.nvmrc); its shell finds node 22.11.0"])
        self.assertEqual(self.lines(nvmrc="lts/*", found={"node": "v22.11.0"}),
                         ['  proj: .nvmrc says node "lts/*", which the office cannot read as a range, so it does not '
                          "say whether its shell's meets it"])

    def test_a_range_it_cannot_read_is_said_as_such(self):
        self.assertEqual(self.lines('{"engines": {"node": "latest"}}', found={"node": "v24.1.0"}),
                         ['  proj: package.json engines says node "latest", which the office cannot read as a range, '
                          "so it does not say whether its shell's meets it"])

    def test_what_meets_its_range_and_what_it_does_not_ask_are_said_under_debug_only(self):
        package = '{"engines": {"node": ">=24", "vscode": "^1.80.0"}}'
        with mock.patch.dict(os.environ, {"OFFICE_DEBUG": "1"}), mock.patch("sys.stderr") as err:
            self.assertEqual(self.lines(package, found={"node": "v24.19.0"}), [])
        said = "".join(c.args[0] for c in err.write.call_args_list)
        self.assertIn("proj: needs node >=24 (package.json engines); its shell finds node 24.19.0, which meets it", said)
        self.assertIn("package.json engines names vscode ('^1.80.0'), which the office does not ask a shell about",
                      said)

    def test_no_engines_no_files_and_a_package_that_does_not_read(self):
        self.assertEqual(self.lines(), [])
        self.assertEqual(self.lines('{"name": "x"}'), [])
        self.assertEqual(self.lines('{"engines": ['), [
            "  proj: package.json does not read as JSON (Expecting value, line 1), so the office cannot say what "
            "its scripts need"])
        self.assertEqual(self.lines('{"engines": ">=24"}'), [
            "  proj: package.json engines is not a table of tools and ranges, so the office cannot read it"])


class TestTheToolchainRead(unittest.TestCase):
    """The read itself, run here as the hosted form runs it (sh -c), in a
    clone of the test's own with a fake node first on the PATH."""

    def setUp(self):
        self.e = Env(self)
        self.clone = self.e.tmp / "clone"
        self.clone.mkdir()
        self.bin = self.e.tmp / "bin"
        fake_tool(self.bin, "node", "v22.11.0")

    def read(self):
        place = ohost.Place(self.clone, host="someone@example.org")  # the hosted form: sh -c, path as argument
        argv = ohost.toolchain_argv(place)
        self.assertEqual(argv[:2], ["sh", "-c"])
        with self.e.this_process(), mock.patch.dict(os.environ, {"PATH": f"{self.bin}{os.pathsep}{self.e.env['PATH']}"}):
            run = ohost.run_in(ohost.Place(self.e.tmp), argv, chdir=False)
        return ohost.read_toolchain(place, run)

    def test_a_clone_with_neither_file_reads_empty(self):
        self.assertTrue(self.read().empty)

    def test_it_asks_only_for_the_tools_package_json_names_and_carries_the_files(self):
        text = '{\n  "engines": {"node": ">=24"},\n  "scripts": {"x": "y"}\n}'  # no newline at its end
        (self.clone / "package.json").write_text(text)
        (self.clone / ".nvmrc").write_text("v24.1.0\nignored\n")
        tc = self.read()
        self.assertEqual(tc.found, {"node": "v22.11.0"})
        self.assertEqual(tc.nvmrc, "v24.1.0")
        self.assertEqual(tc.package.rstrip("\n"), text)

    def test_a_login_shell_printing_around_it_is_skipped(self):
        run = ohost.Run(0, "Welcome to the box\n--office-toolchain-- none node\n--office-toolchain-- nvmrc\n24\n",
                        "", "", "here")
        tc = ohost.read_toolchain("here", run)
        self.assertEqual((tc.found, tc.nvmrc, tc.package), ({"node": None}, "24", None))

    def test_a_read_that_fails_names_where(self):
        with self.assertRaisesRegex(ohost.HostError, "the toolchain at here could not be read: no such dir"):
            ohost.read_toolchain("here", ohost.Run(3, "", "no such dir\n", "", "here"))


class TestToolchainInStatus(RefreshCase):
    """office status on a project on this machine: the read runs under
    bash -lc, so the test's ~/.bash_profile is what puts a node on its PATH,
    as nvm's hook does on the occupant's machine."""

    def setUp(self):
        super().setUp()
        self.hook = self.e.home / "tools"

    def login_path(self, *dirs):
        """~/.bash_profile sets the login shell's whole PATH: the dirs and
        nothing of the machine's, so no node of this machine's is found."""
        (self.e.home / ".bash_profile").write_text(f'PATH="{os.pathsep.join(str(d) for d in dirs)}"\nexport PATH\n')

    def package(self, engines):
        import json
        (self.clone / "package.json").write_text(json.dumps({"name": "proj", "engines": engines}, indent=2) + "\n")

    def test_a_node_below_the_range_is_one_line(self):
        fake_tool(self.hook, "node", "v22.11.0")
        self.login_path(self.hook)
        self.package({"node": ">=24"})
        out = self.run_office("status", check=0).stdout
        self.assertIn("  proj: needs node >=24 (package.json engines); its shell finds node 22.11.0\n", out)
        self.assertLess(out.index("projects:   1 in scope"), out.index("  proj: needs node"))

    def test_a_node_its_login_shell_does_not_find(self):
        self.hook.mkdir()
        self.login_path(self.hook)
        self.package({"node": ">=24"})
        out = self.run_office("status", check=0).stdout
        self.assertIn("  proj: needs node >=24 (package.json engines); its shell finds no node\n", out)

    def test_a_node_that_meets_it_is_said_under_debug_only(self):
        fake_tool(self.hook, "node", "v24.19.0")
        self.login_path(self.hook)
        self.package({"node": ">=24"})
        proc = self.run_office("status", check=0)
        self.assertNotIn("needs node", proc.stdout)
        proc = self.run_office("status", check=0, extra={"OFFICE_DEBUG": "1"})
        self.assertNotIn("needs node", proc.stdout)
        self.assertIn("proj: needs node >=24 (package.json engines); its shell finds node 24.19.0, which meets it",
                      proc.stderr)

    def test_a_clone_with_no_package_json_says_nothing(self):
        out = self.run_office("status", check=0).stdout
        self.assertNotIn("needs ", out)
        self.assertNotIn("toolchain", out)


class TestToolchainInStatusOnAHost(RefreshCase):
    hosted = True

    def test_the_host_shell_s_node_is_read_in_status_s_one_connection(self):
        fake_tool(self.ssh.host_dir(HOST) / "bin", "node", "v22.11.0")
        (self.clone / "package.json").write_text('{"engines": {"node": ">=24"}}\n')
        proc = self.run_office("status", check=0)
        self.assertIn("  proj: needs node >=24 (package.json engines); its shell finds node 22.11.0\n", proc.stdout)
        # bale's version, the sandbox read and the toolchain read share one
        # connection; status makes no other for them.
        carrying = [c for c in self.ssh.connections() if "office-toolchain" in c[-1]]
        self.assertEqual(len(carrying), 1)
        self.assertIn("--version", carrying[0][-1])
        self.assertIn("office-sandbox", carrying[0][-1])
        self.assertEqual(len([c for c in self.ssh.connections() if "--version" in c[-1]]), 1)

    def test_a_node_there_that_meets_it_says_nothing(self):
        fake_tool(self.ssh.host_dir(HOST) / "bin", "node", "v24.19.0")
        (self.clone / "package.json").write_text('{"engines": {"node": ">=24"}}\n')
        self.assertNotIn("needs node", self.run_office("status", check=0).stdout)


# --- 2. the profile's stale line ---------------------------------------------------------------------

class TestTheProfileRule(unittest.TestCase):
    CATALOG = {"verbs": {"handoff": {"kind": "project-session", "built": True},
                         "renovate": {"kind": "office-session", "built": False},
                         "land": {"kind": "script", "built": True},
                         "letterhead-check": {"kind": "script", "built": True}}}

    def named(self, line):
        return h.named_in_line(line, h.catalog_names(self.CATALOG))

    def test_a_kind_is_built_when_a_verb_of_it_is(self):
        names = h.catalog_names(self.CATALOG)
        self.assertTrue(names["project-session"])
        self.assertFalse(names["office-session"])

    def test_the_forms_that_name_a_verb_or_kind(self):
        cases = [("office land is not built yet", "land"), ("`handoff` isn't built", "handoff"),
                 ("`office letterhead-check --x` is not built", "letterhead-check"),
                 ("handoff sessions are not built", "handoff"), ("the letterhead check verb", "letterhead-check"),
                 ("project sessions on the host: not built yet", "project-session"),
                 ("an office-session kind", "office-session"),
                 # a verb's bare word is an ordinary word
                 ("the return trip (land on a host) is not built", None), ("a desk is not built", None),
                 ("office landing is not built", None)]
        for line, want in cases:
            with self.subTest(line=line):
                self.assertEqual(self.named(line), want)

    def test_the_leftmost_name_is_the_one_said(self):
        self.assertEqual(self.named("office land waits: handoff sessions are not built"), "land")

    def test_the_phrases_that_say_not_built(self):
        for line in ("not built", "Not yet built", "not built yet", "isn't built", "isn\u2019t built",
                     "hasn't been built", "not been built", "still unbuilt"):
            with self.subTest(line=line):
                self.assertTrue(h.NOT_BUILT_RE.search(line))
        for line in ("built", "rebuilt", "not a builtin", "built-in, not yet tested"):
            with self.subTest(line=line):
                self.assertFalse(h.NOT_BUILT_RE.search(line))

    def test_only_what_the_install_builds_is_said(self):
        profile = Env(self).tmp / "profile.md"
        profile.write_text("# Profile\n\n## Site\n\n- hosts: project sessions there are not built yet\n"
                           "- office renovate is not built\n- the shed is not built\n- office land runs here\n")
        self.assertEqual(h.stale_profile_lines(profile, self.CATALOG, "9.9.9"), [
            "  profile.md line 5 says project-session is not built; office-src 9.9.9 builds it (share/verbs.toml): "
            "- hosts: project sessions there are not built yet"])


class TestTheProfileLineInStatus(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.e.found(self.root)

    def test_status_names_the_line_and_leaves_the_profile_as_it_is(self):
        profile = self.root / "profile.md"
        text = profile.read_text().replace("## Site\n\nWritten at the founding sitting.\n",
                                           "## Site\n\nWritten at the founding sitting.\n\n"
                                           "- handoff sessions, sent from a bailout, are not "
                                           "built yet\n- office renovate is not built yet\n")
        self.assertNotEqual(text, profile.read_text())
        profile.write_text(text)
        git(self.root, "commit", "-qam", "the occupant's own line", env=self.e.env)
        head = git(self.root, "rev-parse", "HEAD", env=self.e.env)
        n = text.splitlines().index("- handoff sessions, sent from a bailout, are not built yet") + 1
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn(f"profile:    complete\n  profile.md line {n} says handoff is not built; office-src {VERSION} "
                      "builds it (share/verbs.toml): - handoff sessions, sent from a bailout, are not built "
                      "yet\nsurvey:", out)
        self.assertNotIn("renovate is not built", out)  # renovate is not built: its line is true
        self.assertEqual(profile.read_text(), text)
        self.assertEqual(git(self.root, "rev-parse", "HEAD", env=self.e.env), head)
        self.assertEqual(git(self.root, "status", "--porcelain", env=self.e.env), "")

    def test_a_profile_with_no_such_line_says_nothing_more(self):
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn("profile:    complete\nsurvey:", out)



# --- 8. the handoff offered for a bailed job -------------------------------------------------------

BAILED = "2026-11-07-the-merge-001"


def job_waiting(kind, bailed=None, number=5):
    """A merge or undo job waiting for its session, as waiting_on_delivery
    reads one, with the session that bailed out of it when given."""
    today = __import__("datetime").date.today().isoformat()
    job = ({"project": "proj", "commit": "a" * 40, "subject": "bale: x", "files": ["a"], "day": today, "session": None}
           if kind == "undo" else
           {"project": "proj", "audience": "origin", "branch": "main", "files": ["a"], "day": today, "session": None})
    if bailed:
        job["bailed"] = bailed
    return {"folder": {"name": "c", "number": number, "rel": "desk/c", "title": "Merge me", "space": "desk"},
            "landed": None, "job": job}


class TestTheHandoffOfferedAsUnits(unittest.TestCase):
    def test_a_bailed_job_offers_the_handoff_and_names_the_response(self):
        for kind in ("merge", "undo"):
            with self.subTest(kind=kind):
                m = job_waiting(kind, BAILED)
                self.assertEqual(ob.job_start_words(m["job"]), ["--handoff", f"response-{BAILED}.tar.gz"])
                self.assertEqual(ob.job_start_line(m["folder"], m["job"]),
                                 f"office start 5 --handoff response-{BAILED}.tar.gz")
                self.assertTrue(ob.job_waiting_words(m["job"]).endswith(f"; {BAILED} bailed out of it"))

    def test_a_job_with_no_bailout_or_with_its_session_keeps_its_flag(self):
        self.assertEqual(ob.job_start_words(job_waiting("merge")["job"]), ["--merge"])
        self.assertEqual(ob.job_start_words(job_waiting("undo")["job"]), ["--undo-bale"])
        sent = job_waiting("merge", BAILED)["job"]
        sent["session"] = "2026-11-08-the-merge-002"
        self.assertIsNone(ob.job_bailed(sent))

    def test_the_walk_in_s_next_line(self):
        from test_home_screen import groups
        cmd, why = ob.delivery_move(groups(merges=[job_waiting("merge", BAILED)]))
        self.assertEqual(cmd, f"office start 5 --handoff response-{BAILED}.tar.gz")
        self.assertEqual(why, f"folder 5's merge job waits and {BAILED} bailed out of it; start --handoff sends the "
                              "fresh session its handoff asks for")
        self.assertEqual(ob.delivery_move(groups(merges=[job_waiting("undo")]))[0], "office start 5 --undo-bale")

    def test_the_desk_line(self):
        m = job_waiting("merge", BAILED)
        words = ob.open_words(m["folder"], {"merge_by_rel": {"desk/c": m}})
        self.assertTrue(words.endswith(f"{BAILED} bailed out of it; office start 5 --handoff response-{BAILED}.tar.gz"),
                        words)

    def test_the_home_screen_s_item(self):
        import office_home as hs
        from test_home_screen import FakeNames, groups
        import datetime as dt
        items = hs.home_items("current", True, [], groups(merges=[job_waiting("undo", BAILED)]), [{"name": "proj"}], 0,
                              None, [], FakeNames(), [], dt.datetime.now(dt.timezone.utc))
        self.assertEqual(items[0]["argv"], ["start", "5", "--handoff", f"response-{BAILED}.tar.gz"])
        self.assertTrue(items[0]["label"].startswith(f"Hand off the undo session for folder 5, Merge me: {BAILED} "
                                                     "bailed out; bale's own commit aaaaaaa"), items[0]["label"])

    def test_the_map_s_next_rows(self):
        import types
        import office_map as om
        m = job_waiting("merge", BAILED)
        reading = types.SimpleNamespace(out_on=lambda f: [], groups={"merge_by_rel": {"desk/c": m}})
        line = om.next_lines(reading, m["folder"])[0]
        self.assertRegex(line, rf"^  office start 5 --handoff response-{BAILED}\.tar\.gz +hands off {BAILED}, which "
                               r"bailed out of the merge job$")


class TestTheHandoffOfferedInStatus(RefreshCase):
    """office status's line and the walk-in's for a merge job whose session
    bailed out (the page's `- bailed:` line, as 0.52.0 keeps it)."""

    def setUp(self):
        super().setUp()
        import office_deliver as odl
        import datetime as dt
        head = git(self.clone, "rev-parse", "HEAD", env=self.e.env).strip()
        (self.root / self.folder / "merge").mkdir()
        (self.root / self.folder / "merge" / "merge.md").write_text(odl.merge_page_text({
            "project": "proj", "audience": "origin", "kind": "base", "branch": "main", "tip": head,
            "workbench": head, "parted": "", "day": dt.date.today().isoformat(), "files": ["src/a.py"],
            "session": None, "bailed": BAILED}))
        git(self.root, "add", "-A", env=self.e.env)
        git(self.root, "commit", "-qm", "a merge job a session bailed out of", env=self.e.env)
        self.n = self.folder_md_number()

    def folder_md_number(self):
        import re
        text = (self.root / self.folder / "folder.md").read_text()
        return re.search(r"^- number: (\d+)$", text, re.M).group(1)

    def test_status_and_the_walk_in_offer_the_handoff(self):
        line = f"office start {self.n} --handoff response-{BAILED}.tar.gz"
        out = self.run_office("status", check=0).stdout
        self.assertIn(f"folder {self.n}: merge job waiting, its session {BAILED} bailed out; {line} sends the fresh "
                      "session its handoff asks for\n", out)
        self.assertNotIn(f"office start {self.n} --merge", out)
        out = self.run_office(check=0).stdout
        self.assertIn(f"Next: {line}", out)
        self.assertNotIn(f"office start {self.n} --merge", out)

if __name__ == "__main__":
    unittest.main()
