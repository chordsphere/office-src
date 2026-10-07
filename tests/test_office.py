"""Tests for office-src: the helper as units, the office command end to
end, the migration runner through synthetic migrations, the installer,
and the text rules for what lands in an office.

Every test works under its own temporary HOME; nothing touches the real
home directory, config or offices. Run with:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import datetime as dt
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "lib"))
import office_helper as h  # noqa: E402

VERSION = (REPO / "VERSION").read_text().strip()
INSTALL_PARTS = ("bin", "lib", "share", "templates", "doctrine", "migrations", "VERSION")


def later(minor, patch=0):
    """A synthetic release past this install. The upgrade tests name
    their future releases relative to VERSION, so a real release bump
    never turns a test's 'later install' into the current one."""
    major, mi, _ = h.parse_version(VERSION)
    return f"{major}.{mi + minor}.{patch}"


NEXT, AFTER = later(1), later(2)   # the next two synthetic breaking releases
PATCH = later(0, 5)                # a synthetic additive release past this one


def filled_profile(name="test"):
    """A profile with every required section written."""
    shape = tomllib.loads((REPO / "share/profile-shape.toml").read_text())
    parts = [f"# Profile: {name}", ""]
    for s in shape["section"]:
        parts += [f"## {s['heading']}", "", "Written at the founding sitting.", ""]
    return "\n".join(parts)


class Env:
    """A scratch HOME with a git identity and no global git config."""

    def __init__(self, test):
        self.tmp = pathlib.Path(tempfile.mkdtemp(prefix="office-test-"))
        test.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": str(self.home / ".gitconfig-empty"),
            "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com",
            "PYTHONDONTWRITEBYTECODE": "1",
            "LC_ALL": "C.UTF-8",
        }
        (self.home / ".gitconfig-empty").write_text("")
        self.office_bin = REPO / "bin" / "office"

    def run(self, *args, cwd=None, extra=None, bin_path=None, check=None, input=None):
        env = dict(self.env)
        env.update(extra or {})
        proc = subprocess.run([str(bin_path or self.office_bin), *args], cwd=cwd or self.home,
                              env=env, capture_output=True, text=True, timeout=120,
                              input=input if input is not None else "")
        if check is not None and proc.returncode != check:
            raise AssertionError(f"office {' '.join(args)} exited {proc.returncode}, wanted {check}\n"
                                 f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
        return proc

    def git(self, root, *args):
        return subprocess.run(["git", "-C", str(root), *args], env=self.env,
                              capture_output=True, text=True, check=True).stdout

    def init(self, name="sample", *flags, **kw):
        """An office built by office init with --no-founding, unless flags
        are given: the suite's offices are built, never founded through
        the founding door, save in the tests of that door."""
        root = self.home / name
        self.run("init", str(root), *(flags or ("--no-founding",)), check=0, **kw)
        return root

    def found(self, root):
        (root / "profile.md").write_text(filled_profile())
        self.git(root, "commit", "-qam", "found")

    def fake_install(self, version, migrations=()):
        """A copy of this install at another version with synthetic
        migrations: (version, kind, action, summary, script_body[, extra
        TOML]). The real migrations are left out, so the synthetic
        release line is all the runner sees."""
        inst = pathlib.Path(tempfile.mkdtemp(prefix=f"install-{version}-", dir=self.tmp))
        for part in INSTALL_PARTS:
            src = REPO / part
            (shutil.copytree if src.is_dir() else shutil.copy2)(src, inst / part)
        for f in (inst / "migrations").iterdir():
            if f.name != "README.md":
                f.unlink()
        (inst / "VERSION").write_text(version + "\n")
        for v, kind, action, summary, body, *extra in migrations:
            key = "script" if kind == "script" else "goal"
            (inst / "migrations" / f"{v}.toml").write_text(
                f'version = "{v}"\nkind = "{kind}"\nsummary = "{summary}"\n{key} = "{action}"\n'
                + (extra[0] if extra else ""))
            if body is not None:
                (inst / "migrations" / action).write_text(body)
        return inst / "bin" / "office"


# --- helper units -----------------------------------------------------------

class TestVersions(unittest.TestCase):
    def test_compare_is_numeric_not_lexical(self):
        self.assertEqual(h.compare_versions("0.10.0", "0.9.0"), 1)
        self.assertEqual(h.compare_versions("1.0.0", "1.0.0"), 0)
        self.assertEqual(h.compare_versions("0.1.0", "0.1.1"), -1)

    def test_rejects_malformed(self):
        for bad in ("1.0", "v1.0.0", "1.0.0-rc1", ""):
            with self.assertRaises(h.HelperError):
                h.parse_version(bad)

    def test_version_file_is_valid(self):
        h.parse_version(VERSION)


class TestFloorPlan(unittest.TestCase):
    def setUp(self):
        self.catalog = tomllib.loads((REPO / "share/spaces.toml").read_text())

    def test_render_parses_and_stamps(self):
        text = h.render_manifest(self.catalog, "w", "0.1.0", "2026-09-24T00:00:00Z", "UTC")
        data = tomllib.loads(text)
        self.assertEqual(h.office_stamp(data), {"built_from": "0.1.0", "migrated_to": "0.1.0"})
        base = {k for k, v in self.catalog["spaces"].items() if v.get("base")}
        self.assertEqual(set(data["spaces"]), base)
        text.encode("ascii")

    def test_filed_and_hung_paths(self):
        data = tomllib.loads(h.render_manifest(self.catalog, "w", "0.1.0", "x", "UTC"))
        self.assertEqual(sorted(h.space_paths(data, "filed")), ["filing-cabinet", "notepad"])
        self.assertIn("profile.md", h.space_paths(data, "hung"))
        self.assertIn("floor-plan/survey.md", h.space_paths(data, "hung"))

    def test_filed_takes_a_list_like_hung(self):
        """The drafting-table is part live, part filed: the catalog lists
        its filed paths, and a floor plan carrying that list yields them
        from space_paths the way a hung list does."""
        table = self.catalog["spaces"]["drafting-table"]
        self.assertIsInstance(table["filed"], list)
        self.assertNotIn("base", table)
        for p in table["filed"]:
            self.assertTrue(p.startswith("drafting-table/"), p)
        self.assertIn("drafting-table/rulings.md", table["filed"])
        self.assertIn("drafting-table/blueprints/*/close.md", table["filed"])
        plan = tomllib.loads(h.render_manifest(self.catalog, "w", "0.1.0", "x", "UTC"))
        plan["spaces"]["drafting-table"] = table
        filed = h.space_paths(plan, "filed")
        self.assertIn("notepad", filed)
        for p in table["filed"]:
            self.assertIn(p, filed)
        self.assertNotIn("drafting-table", filed)

    def test_render_manifest_writes_a_filed_list(self):
        catalog = {"spaces": {"ledgers": {"path": "ledgers", "base": True,
                                          "filed": ["ledgers/a.md", "ledgers/b/*.md"]}}}
        data = tomllib.loads(h.render_manifest(catalog, "w", "0.1.0", "x", "UTC"))
        self.assertEqual(data["spaces"]["ledgers"]["filed"], ["ledgers/a.md", "ledgers/b/*.md"])
        self.assertIs(data["spaces"]["ledgers"]["hung"], False)
        self.assertEqual(h.render_flag_or_list(True), "true")
        self.assertEqual(h.render_flag_or_list([]), "[]")
        with self.assertRaises(h.HelperError):
            h.render_flag_or_list("yes")

    def test_older_shape_without_migrated_to_is_tolerated(self):
        self.assertEqual(h.office_stamp({"office": {"built_from": "0.1.0"}})["migrated_to"], "0.1.0")
        self.assertEqual(h.office_stamp({"office": {"built_from": "0.1.0"}, "extra": {}})["built_from"], "0.1.0")

    def test_no_stamp_refuses(self):
        with self.assertRaises(h.HelperError):
            h.office_stamp({"office": {"name": "x"}})

    def test_set_migrated_keeps_every_other_byte(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d, "m.toml")
            original = '# keep me\n[office]\nbuilt_from = "0.1.0"\nmigrated_to = "0.1.0"\n\n[spaces.desk]\npath = "desk"\n'
            p.write_text(original)
            h.set_migrated_to(p, "0.3.0")
            self.assertEqual(p.read_text(), original.replace('migrated_to = "0.1.0"', 'migrated_to = "0.3.0"'))

    def test_set_migrated_adds_the_key_to_an_older_shape(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d, "m.toml")
            p.write_text('[office]\nbuilt_from = "0.1.0"\n[spaces.desk]\npath = "desk"\n')
            h.set_migrated_to(p, "0.2.0")
            data = tomllib.loads(p.read_text())
            self.assertEqual(data["office"]["migrated_to"], "0.2.0")
            self.assertEqual(data["spaces"]["desk"]["path"], "desk")


class TestProfile(unittest.TestCase):
    def setUp(self):
        self.shape = tomllib.loads((REPO / "share/profile-shape.toml").read_text())
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)

    def check(self, text):
        p = self.dir / "profile.md"
        p.write_text(text)
        return h.check_profile(p, self.shape)

    def test_template_is_a_stub(self):
        missing, blank = self.check((REPO / "templates/profile.md").read_text())
        self.assertEqual(missing, [])
        self.assertEqual(blank, [s["heading"] for s in self.shape["section"]])

    def test_filled_is_complete(self):
        self.assertEqual(self.check(filled_profile()), ([], []))

    def test_none_written_out_counts(self):
        text = filled_profile().replace("Written at the founding sitting.", "None. This office has no extra rules.")
        self.assertEqual(self.check(text), ([], []))

    def test_comment_only_section_is_blank(self):
        text = filled_profile().replace("## Site\n\nWritten at the founding sitting.", "## Site\n\n<!-- hint -->")
        self.assertEqual(self.check(text), ([], ["Site"]))

    def test_leftover_todo_is_blank(self):
        text = filled_profile().replace("## Audiences\n\nWritten", "## Audiences\n\nTODO: finish\nWritten")
        self.assertEqual(self.check(text), ([], ["Audiences"]))

    def test_missing_section_and_missing_file(self):
        text = filled_profile().replace("## Founding", "## Something else")
        self.assertEqual(self.check(text), (["Founding"], []))
        missing, _ = h.check_profile(self.dir / "absent.md", self.shape)
        self.assertEqual(len(missing), len(self.shape["section"]))


class TestSurveyRender(unittest.TestCase):
    FACTS = [("Survey", "surveyed_at", "2026-09-24T00:00:00Z"), ("Tools", "git", "2.43"),
             ("Tools", "node", "v24")]

    def test_first_survey(self):
        page, changes, first = h.render_survey(self.FACTS, None)
        self.assertTrue(first)
        self.assertIn("First survey of this office.", page)
        page.encode("ascii")

    def test_rerun_reports_changes_but_not_the_timestamp(self):
        page, _, _ = h.render_survey(self.FACTS, None)
        new = [("Survey", "surveyed_at", "2026-09-25T00:00:00Z"), ("Tools", "git", "2.44"),
               ("Tools", "R", "4.5")]
        page2, changes, first = h.render_survey(new, page)
        self.assertFalse(first)
        self.assertEqual(changes, ["added tools.R: 4.5", "changed tools.git: 2.43 to 2.44",
                                   "removed tools.node (was: v24)"])
        self.assertIn("- changed tools.git: 2.43 to 2.44", page2)

    def test_previous_changes_section_is_not_read_as_facts(self):
        page, _, _ = h.render_survey(self.FACTS, None)
        page2, _, _ = h.render_survey(self.FACTS[:2], page)
        _, changes, _ = h.render_survey(self.FACTS[:2], page2)
        self.assertEqual(changes, [])

    def test_non_ascii_is_replaced(self):
        page, _, _ = h.render_survey([("Tools", "x", "caf\u00e9 \u2014 ok")], None)
        page.encode("ascii")

    def test_age(self):
        page, _, _ = h.render_survey(self.FACTS, None)
        now = dt.datetime(2026, 9, 27, tzinfo=dt.timezone.utc)
        stamp, delta = h.survey_age(page, now)
        self.assertEqual(h.describe_age(delta), "3 days old")


class TestMigrationPlanning(unittest.TestCase):
    def setUp(self):
        self.dir = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)

    def add(self, name, body, script=None):
        (self.dir / name).write_text(textwrap.dedent(body))
        if script:
            (self.dir / script).write_text("true\n")

    def test_order_and_pending(self):
        self.add("0.10.0.toml", 'version = "0.10.0"\nkind = "script"\nsummary = "b"\nscript = "b.sh"\n', "b.sh")
        self.add("0.9.0.toml", 'version = "0.9.0"\nkind = "renovation"\nsummary = "a"\ngoal = "g"\n[landed]\npaths = ["x"]\n')
        self.assertEqual([m["version"] for m in h.load_migrations(self.dir, "0.10.0")], ["0.9.0", "0.10.0"])
        self.assertEqual([m["version"] for m in h.pending_migrations(self.dir, "0.9.0", "0.10.0")], ["0.10.0"])

    def test_skew_states(self):
        self.add("0.2.0.toml", 'version = "0.2.0"\nkind = "script"\nsummary = "s"\nscript = "a.sh"\n', "a.sh")
        self.assertEqual(h.skew("0.3.0", "0.2.0", self.dir)[0], "ahead")
        self.assertEqual(h.skew("0.1.0", "0.2.0", self.dir)[0], "behind")
        self.assertEqual(h.skew("0.2.0", "0.2.0", self.dir)[0], "current")
        self.assertEqual(h.skew("0.2.0", "0.2.5", self.dir)[0], "current")

    def test_invalid_migrations_refuse(self):
        cases = {
            "0.2.0.toml": 'version = "0.2.1"\nkind = "script"\nsummary = "s"\nscript = "a.sh"\n',
        }
        self.add("0.2.0.toml", cases["0.2.0.toml"], "a.sh")
        with self.assertRaises(h.HelperError):
            h.load_migrations(self.dir, "1.0.0")
        for body in ('version = "0.2.0"\nkind = "script"\nsummary = ""\nscript = "a.sh"\n',
                     'version = "0.2.0"\nkind = "magic"\nsummary = "s"\n',
                     'version = "0.2.0"\nkind = "script"\nsummary = "s"\nscript = "gone.sh"\n',
                     'version = "0.2.0"\nkind = "renovation"\nsummary = "s"\n',
                     'version = "0.2.0"\nkind = "renovation"\nsummary = "s"\ngoal = "g"\n',
                     'version = "0.2.0"\nkind = "renovation"\nsummary = "s"\ngoal = "g"\n[landed]\npaths = []\n',
                     'version = "0.2.0"\nkind = "renovation"\nsummary = "s"\ngoal = "g"\n[landed]\nchecks = ["x"]\n'):
            self.add("0.2.0.toml", body)
            with self.assertRaises(h.HelperError, msg=body):
                h.load_migrations(self.dir, "1.0.0")
        self.add("0.2.0.toml", 'version = "0.2.0"\nkind = "script"\nsummary = "s"\nscript = "a.sh"\n')
        with self.assertRaises(h.HelperError):
            h.load_migrations(self.dir, "0.1.0")

    def test_this_install_ships_valid_migrations(self):
        h.load_migrations(REPO / "migrations", VERSION)


# --- the office command -------------------------------------------------------

class TestInit(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)

    def test_builds_commits_and_with_no_founding_names_what_founds_it(self):
        root = self.e.home / "sample"
        proc = self.e.run("init", str(root), "--no-founding", check=0)
        self.assertEqual(proc.stdout, "Next: office found  (it asks the profile's questions and sends the founding "
                                      "session out)\n")
        self.assertNotIn("bale pack", proc.stdout + proc.stderr)
        for sp in ("desk", "filing-cabinet", "notepad", "suggestion-box", "drawer"):
            self.assertTrue((root / sp).is_dir(), sp)
        for sp in ("handbook", "calendar", "rolodex", "clipboards", "letterhead"):
            self.assertFalse((root / sp).exists(), sp)
        self.assertEqual(list((root / "desk").iterdir()), [root / "desk" / ".keep"])
        manifest = tomllib.loads((root / "floor-plan/manifest.toml").read_text())
        self.assertEqual(manifest["office"]["built_from"], VERSION)
        self.assertEqual(manifest["office"]["migrated_to"], VERSION)
        self.assertIn("First survey of this office.", (root / "floor-plan/survey.md").read_text())
        self.assertIn("## Purpose", (root / "profile.md").read_text())
        self.assertEqual(len(self.e.git(root, "log", "--oneline").splitlines()), 1)
        self.assertEqual(self.e.git(root, "status", "--porcelain"), "")
        self.assertEqual((self.e.home / ".config/office-src/default-office").read_text().strip(), str(root))
        # The install is never written: no outbox in its doctrine.
        self.assertFalse((REPO / "doctrine" / ".bale").exists())

    def test_no_founding_takes_no_answers(self):
        proc = self.e.run("init", str(self.e.home / "w"), "--no-founding", "--purpose", "x")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("--no-founding sends no founding session, so it takes none of the profile's answers (--purpose)",
                      proc.stderr)
        self.assertFalse((self.e.home / "w").exists())

    def test_never_copies_tool_files_into_the_office(self):
        root = self.e.init()
        files = self.e.git(root, "ls-files").split()
        for f in files:
            self.assertFalse(f.startswith(("bin/", "lib/", "templates/", "doctrine/", "migrations/", "share/")), f)
            self.assertNotEqual(pathlib.Path(f).name, "OFFICE.md")

    def test_refusals(self):
        root = self.e.init()
        cases = {
            str(self.e.home): "home directory",
            str(root): "already an office",
            str(root / "desk" / "inner"): "inside the office",
        }
        busy = self.e.home / "busy"
        busy.mkdir()
        (busy / "x").write_text("x")
        cases[str(busy)] = "not empty"
        repo = self.e.home / "proj"
        repo.mkdir()
        self.e.git(repo, "init", "-q")
        cases[str(repo / "office")] = "inside the git repo"
        for path, why in cases.items():
            proc = self.e.run("init", path)
            self.assertEqual(proc.returncode, 1, path)
            self.assertIn(why, proc.stderr, path)

    def test_refuses_without_a_git_identity_before_building(self):
        self.e.env = {k: v for k, v in self.e.env.items() if not k.startswith(("GIT_AUTHOR", "GIT_COMMITTER"))}
        (self.e.home / ".gitconfig-empty").write_text("[user]\n\tuseConfigOnly = true\n")
        proc = self.e.run("init", str(self.e.home / "w"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("identity", proc.stderr)
        self.assertFalse((self.e.home / "w").exists())

    def test_second_office_does_not_steal_the_default(self):
        first = self.e.init("one")
        self.e.init("two")
        self.assertEqual(self.e.run("default", check=0).stdout.strip(), str(first))


class TestFindingTheOffice(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_walks_up_from_a_subdirectory(self):
        sub = self.root / "desk" / "a" / "b"
        sub.mkdir(parents=True)
        self.assertEqual(self.e.run("where", cwd=sub, check=0).stdout.strip(), str(self.root))

    def test_env_override_and_default_fallback(self):
        other = self.e.init("other", extra=None)
        self.assertEqual(self.e.run("where", cwd=self.root, extra={"OFFICE_ROOT": str(other)}, check=0).stdout.strip(), str(other))
        outside = self.e.tmp / "elsewhere"
        outside.mkdir()
        proc = self.e.run("where", cwd=outside, check=0)
        self.assertEqual(proc.stdout.strip(), str(self.root))
        self.assertIn("default", proc.stderr)

    def test_no_office_and_no_default(self):
        (self.e.home / ".config/office-src/default-office").unlink()
        outside = self.e.tmp / "elsewhere"
        outside.mkdir()
        proc = self.e.run("where", cwd=outside)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("office default PATH", proc.stderr)

    def test_default_refuses_a_non_office(self):
        proc = self.e.run("default", str(self.e.tmp))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not an office", proc.stderr)

    def test_unknown_verb_refuses(self):
        proc = self.e.run("frobnicate", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("unknown verb", proc.stderr)


class TestStatusAndSurvey(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_status_unfounded_then_founded(self):
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn("INCOMPLETE; this office is unfounded", out)
        self.assertIn("blank: Purpose", out)
        self.assertIn("skew:       none", out)
        self.e.found(self.root)
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn("profile:    complete", out)

    def test_unfounded_warning_on_survey(self):
        proc = self.e.run("survey", cwd=self.root, check=0)
        self.assertIn("unfounded", proc.stderr)
        self.e.found(self.root)
        self.assertNotIn("unfounded", self.e.run("survey", cwd=self.root, check=0).stderr)

    def test_rerun_reports_no_changes_and_commits_only_the_page(self):
        (self.root / "desk" / "scratch.md").write_text("mine\n")
        proc = self.e.run("survey", cwd=self.root, check=0)
        self.assertEqual(proc.stdout.strip(), "no changes since the previous survey")
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "?? desk/scratch.md")
        self.assertIn("office survey: 0 facts changed", self.e.git(self.root, "log", "-1", "--format=%s"))

    def test_office_survey_steps(self):
        steps = self.root / "drawer" / "survey"
        steps.mkdir()
        (steps / "crontab.sh").write_text("#!/usr/bin/env bash\necho 'jobs: 3'\necho 'a loose line'\n")
        (steps / "crontab.sh").chmod(0o755)
        (steps / "slow.sh").write_text("#!/usr/bin/env bash\nsleep 5\n")
        (steps / "slow.sh").chmod(0o755)
        (steps / "idle.sh").write_text("echo nope\n")
        proc = self.e.run("survey", cwd=self.root, extra={"OFFICE_STEP_TIMEOUT": "1"}, check=0)
        page = (self.root / "floor-plan/survey.md").read_text()
        self.assertIn("## Office step: crontab.sh", page)
        self.assertIn("- jobs: 3", page)
        self.assertIn("- line 2: a loose line", page)
        self.assertIn("timed out after 1s", page)
        self.assertIn("- skipped: not executable", page)
        self.assertIn("added office step: crontab.sh.jobs: 3", proc.stdout)

    def test_no_commit_flag(self):
        head = self.e.git(self.root, "rev-parse", "HEAD")
        self.e.run("survey", "--no-commit", cwd=self.root, check=0)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)


# --- versioning and upgrade ---------------------------------------------------

MIGRATION_ADD_SPACE = "mkdir -p handbook && printf 'front page\\n' > handbook/README.md\n"


class TestUpgrade(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def stamp(self):
        return tomllib.loads((self.root / "floor-plan/manifest.toml").read_text())["office"]

    def test_nothing_to_do_when_current(self):
        proc = self.e.run("upgrade", cwd=self.root, check=0)
        self.assertIn("nothing to upgrade", proc.stderr)

    def test_additive_release_needs_nothing(self):
        office = self.e.fake_install(PATCH)
        out = self.e.run("status", cwd=self.root, bin_path=office, check=0).stdout
        self.assertIn("skew:       none", out)
        self.e.run("survey", cwd=self.root, bin_path=office, check=0)

    def test_behind_refuses_and_names_upgrade(self):
        office = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Adds a handbook.", MIGRATION_ADD_SPACE)])
        proc = self.e.run("survey", cwd=self.root, bin_path=office)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("run: office upgrade", proc.stderr)
        self.assertIn(f"{NEXT}: Adds a handbook.", proc.stderr)
        self.assertIn("BEHIND", self.e.run("status", cwd=self.root, bin_path=office, check=0).stdout)

    def test_ahead_refuses_outright(self):
        office = self.e.fake_install("0.0.9")
        for verb in ("survey", "upgrade"):
            proc = self.e.run(verb, cwd=self.root, bin_path=office)
            self.assertEqual(proc.returncode, 1, verb)
            self.assertIn("past the installed office-src 0.0.9", proc.stderr)
        self.assertIn("AHEAD", self.e.run("status", cwd=self.root, bin_path=office, check=0).stdout)

    def test_script_migrations_land_as_one_commit(self):
        office = self.e.fake_install(AFTER, [
            (NEXT, "script", f"{NEXT}.sh", "Adds a handbook.", MIGRATION_ADD_SPACE),
            (AFTER, "script", f"{AFTER}.sh", "Adds a drafting table.", "mkdir -p drafting-table && : > drafting-table/.keep\n"),
        ])
        before = len(self.e.git(self.root, "log", "--oneline").splitlines())
        self.e.run("upgrade", cwd=self.root, bin_path=office, check=0)
        self.assertEqual(len(self.e.git(self.root, "log", "--oneline").splitlines()), before + 1)
        msg = self.e.git(self.root, "log", "-1", "--format=%B")
        self.assertIn(f"office upgrade: {VERSION} to {AFTER}", msg)
        self.assertIn(f"- {NEXT}: Adds a handbook.", msg)
        self.assertIn(f"- {AFTER}: Adds a drafting table.", msg)
        self.assertEqual(self.stamp()["migrated_to"], AFTER)
        self.assertEqual(self.stamp()["built_from"], VERSION)
        self.assertTrue((self.root / "handbook/README.md").is_file())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertIn("nothing to upgrade", self.e.run("upgrade", cwd=self.root, bin_path=office, check=0).stderr)

    def test_dry_run_changes_nothing(self):
        office = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Adds a handbook.", MIGRATION_ADD_SPACE)])
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.e.run("upgrade", "--dry-run", cwd=self.root, bin_path=office, check=0)
        self.assertIn("dry run passed", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        self.assertFalse((self.root / "handbook").exists())
        self.assertEqual(self.stamp()["migrated_to"], VERSION)

    def test_filed_paper_is_never_rewritten(self):
        (self.root / "notepad" / "2026-09-24-words.md").write_text("verbatim\n")
        self.e.git(self.root, "add", "-A")
        self.e.git(self.root, "commit", "-qm", "words")
        office = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Tidies the notepad.",
                                                "printf 'tidied\\n' > notepad/2026-09-24-words.md\n")])
        head = self.e.git(self.root, "rev-parse", "HEAD")
        proc = self.e.run("upgrade", cwd=self.root, bin_path=office)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("touched filed paper", proc.stderr)
        self.assertIn("was not touched", proc.stderr)
        self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        self.assertEqual((self.root / "notepad" / "2026-09-24-words.md").read_text(), "verbatim\n")

    def test_a_part_filed_space_refuses_writes_to_its_filed_list_only(self):
        """The drafting-table files a list of paths, not the whole space.
        upgrade's filed-paper check reads the list, glob included: a
        migration that grows a ledger or a close report is refused and
        rolled back; one that writes a live page in the same space lands."""
        catalog = tomllib.loads((REPO / "share/spaces.toml").read_text())["spaces"]["drafting-table"]
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(manifest.read_text() + '\n[spaces.drafting-table]\npath = "drafting-table"\nhung = false\n'
                            f'filed = {h.render_flag_or_list(catalog["filed"])}\n')
        table = self.root / "drafting-table"
        (table / "blueprints" / "2026-09-29-arc").mkdir(parents=True)
        (table / "rulings.md").write_text("# Rulings\n")
        (table / "agenda.md").write_text("# Agenda\n")
        (table / "blueprints" / "2026-09-29-arc" / "close.md").write_text("# Close\n")
        self.e.git(self.root, "add", "-A")
        self.e.git(self.root, "commit", "-qm", "a drafting table")
        head = self.e.git(self.root, "rev-parse", "HEAD")
        for path in ("drafting-table/rulings.md", "drafting-table/blueprints/2026-09-29-arc/close.md"):
            office = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Grows a ledger.",
                                                 f"printf 'more\\n' >> {path}\n")])
            proc = self.e.run("upgrade", cwd=self.root, bin_path=office)
            self.assertEqual(proc.returncode, 1, path)
            self.assertIn("touched filed paper", proc.stderr, path)
            self.assertIn(path, proc.stderr)
            self.assertEqual(self.e.git(self.root, "rev-parse", "HEAD"), head)
        office = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Rewrites the agenda.",
                                             "printf 'live\\n' > drafting-table/agenda.md\n")])
        self.e.run("upgrade", cwd=self.root, bin_path=office, check=0)
        self.assertEqual(self.stamp()["migrated_to"], NEXT)
        self.assertEqual((table / "agenda.md").read_text(), "live\n")
        self.assertEqual((table / "rulings.md").read_text(), "# Rulings\n")

    def test_failing_migration_leaves_the_office_alone(self):
        office = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Breaks.", "mkdir -p x && exit 3\n")])
        proc = self.e.run("upgrade", cwd=self.root, bin_path=office)
        self.assertEqual(proc.returncode, 1)
        self.assertFalse((self.root / "x").exists())
        self.assertEqual(self.stamp()["migrated_to"], VERSION)

    def test_dirty_office_refuses(self):
        office = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Adds a handbook.", MIGRATION_ADD_SPACE)])
        (self.root / "desk" / "wip.md").write_text("wip\n")
        proc = self.e.run("upgrade", cwd=self.root, bin_path=office)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("uncommitted changes", proc.stderr)

    # The renovation door (a renovation sent out through office start, and
    # the re-run that stamps it) is tests/test_founding_door.py's, where a
    # fake bale packs and applies.

    def test_a_renovation_must_declare_what_landing_means(self):
        office = self.e.fake_install(NEXT, [
            (NEXT, "renovation", "Do something.", "Something.", None),
        ])
        proc = self.e.run("status", cwd=self.root, bin_path=office)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("[landed]", proc.stderr)

    def test_the_real_0_2_0_migration_gives_an_old_office_its_include_group(self):
        """The first real exercise of the runner: an office shaped the
        way 0.1.0 built it (no bale.toml, stamped 0.1.0) upgrades to
        this release in one commit, and capture works before it does."""
        (self.root / "bale.toml").unlink()
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(manifest.read_text().replace(f'"{VERSION}"', '"0.1.0"'))
        self.e.git(self.root, "commit", "-qam", "as 0.1.0 built it")
        proc = self.e.run("survey", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("0.2.0: Adds bale.toml", proc.stderr)
        proc = self.e.run("note", "still works when behind", cwd=self.root, check=0)
        self.assertIn("behind", proc.stderr)
        self.e.run("upgrade", cwd=self.root, check=0)
        self.assertEqual(self.stamp()["migrated_to"], "0.2.0")
        self.assertEqual(self.stamp()["built_from"], "0.1.0")
        group = tomllib.loads((self.root / "bale.toml").read_text())["pack"]
        self.assertEqual(group["include_group"], "hung")
        self.assertEqual(sorted(group["include_group_pulls"]), ["floor-plan/survey.md", "profile.md"])
        self.assertIn("- 0.2.0: Adds bale.toml", self.e.git(self.root, "log", "-1", "--format=%B"))
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.assertIn("matches the floor plan", self.e.run("status", cwd=self.root, check=0).stdout)


# --- the everyday verbs ---------------------------------------------------------

class TestCapture(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def page(self):
        pages = sorted((self.root / "notepad").glob("????-??-??.md"))
        self.assertEqual(len(pages), 1, pages)
        return pages[0]

    def test_note_appends_dated_lines_and_commits_only_the_page(self):
        (self.root / "desk" / "wip.md").write_text("mine\n")
        self.e.run("note", "called", "the bank", cwd=self.root, check=0)
        self.e.run("note", cwd=self.root, check=0, input="line one\n\nline two\n")
        text = self.page().read_text()
        self.assertRegex(text, r"(?m)^- \d\d:\d\d called the bank$")
        self.assertRegex(text, r"(?m)^- \d\d:\d\d line one\n- \d\d:\d\d line two\n\Z")
        self.assertTrue(text.startswith(f"# {self.page().stem}: notes\n"))
        self.assertEqual(self.e.git(self.root, "status", "--porcelain").strip(), "?? desk/wip.md")
        self.assertIn("office note:", self.e.git(self.root, "log", "-1", "--format=%s"))

    def test_note_works_unfounded_and_only_warns(self):
        proc = self.e.run("note", "first thought", cwd=self.root, check=0)
        self.assertIn("unfounded", proc.stderr)

    def test_note_works_when_behind_and_when_ahead(self):
        behind = self.e.fake_install(NEXT, [(NEXT, "script", f"{NEXT}.sh", "Adds a handbook.", MIGRATION_ADD_SPACE)])
        proc = self.e.run("note", "behind", cwd=self.root, bin_path=behind, check=0)
        self.assertIn("behind", proc.stderr)
        ahead = self.e.fake_install("0.0.9")
        proc = self.e.run("note", "ahead", cwd=self.root, bin_path=ahead, check=0)
        self.assertIn("past office-src", proc.stderr)
        self.assertIn("ahead", self.page().read_text())

    def test_note_keeps_the_office_ascii_without_losing_words(self):
        proc = self.e.run("note", "caf\u00e9 \u2014 ok", cwd=self.root, check=0)
        line = self.page().read_text().splitlines()[-1]
        self.assertTrue(line.isascii(), line)
        self.assertIn("caf\\xe9 \\u2014 ok", line)
        self.assertIn("backslash escapes", proc.stderr)

    def test_empty_note_refuses(self):
        proc = self.e.run("note", "   ", cwd=self.root)
        self.assertEqual(proc.returncode, 1)

    def test_note_uses_the_office_timezone(self):
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(re.sub(r'timezone = ".*"', 'timezone = "Pacific/Kiritimati"', manifest.read_text()))
        self.e.run("note", "far east", cwd=self.root, check=0)
        want = subprocess.run(["date", "+%F"], env={"TZ": "Pacific/Kiritimati"}, capture_output=True, text=True).stdout.strip()
        self.assertEqual(self.page().stem, want)


class TestFolders(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.e.found(self.root)

    def open(self, *args, **kw):
        return self.e.run("open", *args, cwd=self.root, check=0, **kw).stdout.strip()

    def test_open_makes_a_dated_folder_from_the_template(self):
        folder = self.open("Fix Login!", "--title", "Fix the login page")
        self.assertRegex(folder, r"^desk/\d{4}-\d{2}-\d{2}-fix-login$")
        text = (self.root / folder / "folder.md").read_text()
        self.assertTrue(text.startswith("# Fix the login page\n"))
        self.assertIn("## Sessions", text)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_open_writes_only_the_fields_it_can_fill(self):
        """The field block carries the minted number, status and the
        queued date, all known at open, and no line for a field it was
        not given: a blank size would be a wrong fact, not a missing one."""
        folder = self.open("job")
        text = (self.root / folder / "folder.md").read_text()
        day = pathlib.Path(folder).name[:10]
        self.assertTrue(text.startswith(f"# job\n\n- number: 1\n- status: queued\n- queued: {day}\n\n"), text[:80])
        fields = re.findall(r"^- ([a-z ]+): ", text.split("\n## ", 1)[0], re.M)
        self.assertEqual(fields, ["number", "status", "queued"])
        self.assertNotIn("{{", text)
        self.assertIn("\n## Riders\n", text)
        self.assertTrue(text.endswith(f"\n## History\n\nOne event per line, dated, appended and never rewritten: what happened\n"
                                      f"to this folder and when. The status line above always agrees with the\n"
                                      f"last state-changing line here.\n\n- {day} queued: office open\n"), text[-300:])
        self.assertEqual(re.findall(r"^- \d{4}-\d{2}-\d{2} (\w+):", text, re.M), ["queued"])

    def test_the_0_2_0_verbs_still_serve_a_folder_without_the_field_block(self):
        """A folder opened by 0.2.0 has no field block, no Riders and no
        History; desk, sessions, close and reopen keep working on it."""
        folder = self.open("old")
        f = self.root / folder / "folder.md"
        text = f.read_text()
        head, rest = text.split("\n## Asked", 1)
        text = "# old\n\nOne job.\n\n## Asked" + rest.split("\n## Riders", 1)[0]
        f.write_text(text.replace("What happens next, and who moves.", "- Ship it."))
        self.e.git(self.root, "commit", "-qam", "as 0.2.0 wrote it")
        self.assertNotIn("- status:", f.read_text())
        self.assertIn("next: Ship it.  (sessions: 0)", self.e.run("desk", cwd=self.root, check=0).stdout)
        self.e.run("sessions", "old", "2026-09-25-old-001", cwd=self.root, check=0)
        self.assertIn("next: Ship it.  (sessions: 1)", self.e.run("desk", cwd=self.root, check=0).stdout)
        listing = self.e.run("sessions", "old", cwd=self.root, check=0).stdout
        self.assertEqual(listing.splitlines()[0], "- 2026-09-25-old-001")
        self.assertIn("scopes no projects", listing)
        self.e.run("close", "old", cwd=self.root, check=0)
        self.e.run("reopen", "old", cwd=self.root, check=0)
        self.assertIn("- 2026-09-25-old-001", f.read_text())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_open_seeds_a_thread_from_stdin(self):
        folder = self.open("house-hunt", "--thread", input="From: agent\nThe house on Elm is back.\n")
        thread = (self.root / folder / "thread.md").read_text()
        self.assertIn("The house on Elm is back.", thread)

    def test_open_refuses_a_duplicate(self):
        self.open("job")
        proc = self.e.run("open", "job", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("already on the desk", proc.stderr)

    def test_desk_lists_next_moves(self):
        self.assertIn("the desk is clear", self.e.run("desk", cwd=self.root, check=0).stdout)
        folder = self.open("job")
        out = self.e.run("desk", cwd=self.root, check=0).stdout
        self.assertIn("next: (not written yet)", out)
        f = self.root / folder / "folder.md"
        f.write_text(f.read_text().replace("What happens next, and who moves.", "- Ask Sam for the logs."))
        self.assertIn("next: Ask Sam for the logs.", self.e.run("desk", cwd=self.root, check=0).stdout)

    def test_close_and_reopen_move_without_rewriting(self):
        """The bytes move as they are; the only edits are the status line
        and one History line each, appended to the History section."""
        folder = self.open("job")
        name = pathlib.Path(folder).name
        day = name[:10]
        f = self.root / folder / "folder.md"
        f.write_text(f.read_text().replace("## Asked\n", "## Asked\n\nWork in progress.\n"))
        self.e.git(self.root, "commit", "-qam", "work")
        before = f.read_text()
        self.e.run("close", "job", cwd=self.root, check=0)
        filed = self.root / "filing-cabinet" / name / "folder.md"
        self.assertEqual(filed.read_text(), before.replace("- status: queued", "- status: done")
                         + f"- {day} done: office close\n")
        self.assertFalse((self.root / folder).exists())
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")
        self.e.run("reopen", name, cwd=self.root, check=0)
        self.assertEqual(f.read_text(), before.replace("- status: queued", "- status: open")
                         + f"- {day} done: office close\n- {day} reopened: office reopen\n")
        log = self.e.git(self.root, "log", "--follow", "--format=%s", "--", f"desk/{name}/folder.md")
        self.assertIn("office open:", log)
        self.assertIn("office close:", log)

    def test_close_refuses_ambiguity_and_absence(self):
        self.open("job-one")
        self.open("job-two")
        proc = self.e.run("close", "job", cwd=self.root)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("matches 2 folders", proc.stderr)
        proc = self.e.run("close", "nothing", cwd=self.root)
        self.assertEqual(proc.returncode, 1)


class TestSessions(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()
        self.e.found(self.root)
        self.folder = self.e.run("open", "job", cwd=self.root, check=0).stdout.strip()

    def test_records_from_a_pack_report_and_never_twice(self):
        report = 'noise\n{"outcome": "packed", "sid": "2026-09-24-job-001", "tarball": "x", "goal": "not copied"}\n'
        self.e.run("sessions", "job", "-", "-m", "first pass", cwd=self.root, check=0, input=report)
        proc = self.e.run("sessions", "job", "-", cwd=self.root, check=0, input=report)
        self.assertIn("already recorded", proc.stderr)
        text = (self.root / self.folder / "folder.md").read_text()
        sessions = text.split("## Sessions\n", 1)[1].split("\n## ", 1)[0]
        self.assertEqual(sessions.count("2026-09-24-job-001"), 1)
        self.assertIn("- 2026-09-24-job-001: first pass\n", text)
        self.assertNotIn("not copied", text)
        listing = self.e.run("sessions", "job", cwd=self.root, check=0).stdout
        self.assertTrue(listing.startswith("- 2026-09-24-job-001: first pass\n"), listing)
        self.assertIn("scopes no projects", listing)
        self.assertEqual(self.e.git(self.root, "status", "--porcelain"), "")

    def test_records_in_a_filed_folder_and_by_plain_id(self):
        self.e.run("close", "job", cwd=self.root, check=0)
        self.e.run("sessions", "job", "2026-09-25-job-002", cwd=self.root, check=0)
        self.assertIn("2026-09-25-job-002", (self.root / "filing-cabinet" / pathlib.Path(self.folder).name / "folder.md").read_text())

    def test_bad_reports_refuse(self):
        for report in ("", "not json\n", '{"tarball": "x"}\n', '{"session_id": "2026-09-24-job-001"}\n'):
            proc = self.e.run("sessions", "job", "-", cwd=self.root, input=report)
            self.assertEqual(proc.returncode, 1, report)
        proc = self.e.run("sessions", "job", "not-a-sid", cwd=self.root)
        self.assertEqual(proc.returncode, 1)


class TestPackReport(unittest.TestCase):
    def test_the_contracts_sid_key_and_nothing_guessed(self):
        """bale's pack contract (format_pack_json) names the id `sid`; a
        report without it refuses and names the keys it saw."""
        self.assertEqual(h.sid_from_pack_report('[bale] packed\n{"outcome": "packed", "sid": "2026-09-24-a-b-001"}'),
                         "2026-09-24-a-b-001")
        for report, words in (('{"session_id": "2026-09-24-a-001"}', "keys seen: session_id"),
                              ('{"id": "2026-09-24-a-001", "n": 3}', "no sid key"),
                              ('{"sid": "not-an-id"}', "not a session id")):
            with self.assertRaises(h.HelperError) as cm:
                h.sid_from_pack_report(report)
            self.assertIn(words, str(cm.exception))


class TestWeek(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_no_calendar_names_the_renovation(self):
        out = self.e.run("week", cwd=self.root, check=0).stdout
        self.assertIn("no calendar", out)
        self.assertIn("renovation", out)

    def test_plan_against_record(self):
        cal = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, cal)
        (cal / "plan.md").write_text("# Plan\n\n- every weekday 09:30 Standup\n- 2026-09-25 14:00 Dentist\n"
                                     "- 2026-10-02 10:00 Next week\n- sometime soon lunch\n")
        (cal / "record.md").write_text("- 2026-09-21 09:30 Standup: held\n- 2026-09-22 Standup: short\n"
                                       "- 2026-09-23 18:00 Called the agent\n")
        lines, gaps = h.week_report(cal, "2026-09-24", "12:00", "UTC")
        text = "\n".join(lines)
        self.assertIn("week of 2026-09-21 to 2026-09-27", text)
        self.assertIn("Mon 2026-09-21 09:30 Standup [recorded]", text)
        self.assertIn("Wed 2026-09-23 09:30 Standup [GAP: nothing recorded]", text)
        self.assertIn("Thu 2026-09-24 09:30 Standup [GAP: nothing recorded]", text)
        self.assertIn("Fri 2026-09-25 09:30 Standup [planned]", text)
        self.assertIn("Fri 2026-09-25 14:00 Dentist [planned]", text)
        self.assertNotIn("Next week", text)
        self.assertIn("Called the agent [recorded, not planned]", text)
        self.assertIn("unreadable plan.md line", text)
        self.assertEqual(gaps, 2)

    def test_week_reads_the_office_calendar(self):
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(manifest.read_text() + '\n[spaces.calendar]\npath = "calendar"\nhung = true\nfiled = false\n')
        (self.root / "calendar").mkdir()
        out = self.e.run("week", cwd=self.root, check=0).stdout
        self.assertIn("week of", out)
        self.assertIn("plan.md does not exist yet", out)


class TestWalkingIn(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_walking_in_shows_the_room(self):
        self.e.run("open", "job", cwd=self.root, check=0)
        self.e.run("note", "a thought", cwd=self.root, check=0)
        (self.root / "suggestion-box" / "slow-survey.md").write_text("# slow\n")
        out = self.e.run(cwd=self.root, check=0).stdout
        for want in ("The sample office", "UNFOUNDED", "current with office-src", "In flight:",
                     "this office scopes no projects", "On the desk:",
                     "-job  next: (not written yet)", "no calendar", "a thought", "Suggestion box: 1 slip(s).",
                     "From here: office start, office land, office note"):
            self.assertIn(want, out)

    def test_walking_in_from_anywhere_uses_the_default(self):
        outside = self.e.tmp / "elsewhere"
        outside.mkdir()
        out = self.e.run(cwd=outside, check=0).stdout
        self.assertIn(f"The sample office, {self.root}", out)

    def test_walking_in_with_no_office_shows_help(self):
        (self.e.home / ".config/office-src/default-office").unlink()
        outside = self.e.tmp / "elsewhere"
        outside.mkdir()
        out = self.e.run(cwd=outside, check=0).stdout
        self.assertIn("usage: office", out)
        self.assertIn("office init PATH builds one", out)


class TestIncludeGroup(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_init_writes_a_group_of_spaces_and_hung_items(self):
        group = tomllib.loads((self.root / "bale.toml").read_text())["pack"]
        manifest = tomllib.loads((self.root / "floor-plan/manifest.toml").read_text())
        self.assertEqual(sorted(group["include_group_triggers"]), sorted(s["path"] for s in manifest["spaces"].values()))
        self.assertEqual(sorted(group["include_group_pulls"]), sorted(h.space_paths(manifest, "hung")))
        for path in group["include_group_triggers"] + group["include_group_pulls"]:
            self.assertTrue((self.root / path).exists(), path)
        self.assertNotIn(".", group["include_group_triggers"])
        (self.root / "bale.toml").read_text().encode("ascii")

    def test_status_reports_drift(self):
        manifest = self.root / "floor-plan/manifest.toml"
        manifest.write_text(manifest.read_text() + '\n[spaces.calendar]\npath = "calendar"\nhung = true\nfiled = false\n')
        (self.root / "calendar").mkdir()
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn("bale.toml differs from the floor plan", out)
        self.assertIn("pulls: missing calendar", out)


# --- the install's catalogs ---------------------------------------------------------

# The kinds share/verbs.toml declares ahead of the command, as a registry
# for the shell and for whoever spawns sessions. Blueprint section 6 of
# the drafting-table declares them; the verbs session builds them.
DECLARED_KINDS = ("sitting", "chat", "cleanup", "review", "check", "retry")
# The drafting table's scripts (blueprint session 4b), whose lands follow
# the blueprint's section 3 table rather than the earlier verbs' lands =
# writes: the verb that writes the drafting table first also brings its
# front page, the floor plan's entry and bale.toml's trigger, which it
# writes and never guarantees (they exist already after the first).
DRAFTING_LANDS = {
    "moves": ["drafting-table/moves.md"],
    "blueprint-open": ["drafting-table/blueprints/{id}/blueprint.md"],
    "blueprint-ratify": ["drafting-table/blueprints/{id}/blueprint.md"],
    "rider-add": ["drafting-table/riders.md"],
    "rider-carry": ["desk/{folder}/folder.md", "drafting-table/riders.md"],
    "rider-consumed": ["desk/{folder}/folder.md", "filing-cabinet/{folder}/folder.md"],
    "riders": [], "agenda-add": ["drafting-table/agenda.md"], "rulings": [], "evidence": [],
    "watches": [], "watches-check": [], "digest": ["drafting-table/digest.md"],
}
# Blueprint section 3's attended and trigger columns for the drafting
# table's scripts that are not attended and manual alone.
DRAFTING_RUNS = {
    "moves": (False, ["after-sitting", "manual"]),
    "watches-check": (False, ["before-sitting", "after-build", "manual"]),
    "digest": (False, ["before-sitting", "manual"]),
}


def verbs_catalog():
    return tomllib.loads((REPO / "share/verbs.toml").read_text(encoding="utf-8"))


def spaces_catalog():
    return tomllib.loads((REPO / "share/spaces.toml").read_text())


class TestCatalogs(unittest.TestCase):
    """The rule: a session kind with attended = false must declare a
    landing. The suite refuses a shipped catalog that breaks it, and the
    same helper walks the space catalog for a hung page that is also
    filed. office status reports both from the installed catalogs."""

    def test_every_verb_declares_the_three_keys(self):
        for name, verb in verbs_catalog()["verbs"].items():
            for key in ("lands", "attended", "trigger"):
                self.assertIn(key, verb, f"{name} has no {key}")
            self.assertIsInstance(verb["lands"], list, name)
            self.assertIsInstance(verb["attended"], bool, name)
            self.assertTrue(verb["trigger"], f"{name} has an empty trigger")
            for t in verb["trigger"]:
                self.assertIn(t, h.TRIGGERS, f"{name}: {t}")
            self.assertIn(verb["kind"], h.VERB_KINDS, name)

    def test_the_shipped_verbs_catalog_holds(self):
        """No offender in the shipped catalog; the only lands the check
        cannot place against a path are init's, whose writes is prose."""
        problems, unchecked = h.verb_catalog_problems(verbs_catalog())
        self.assertEqual(problems, [])
        self.assertEqual(sorted(u.split(":")[0] for u in unchecked), ["init", "init"])
        self.assertEqual(sorted(verbs_catalog()["verbs"]["init"]["lands"]), ["floor-plan/manifest.toml", "profile.md"])

    def test_the_rule_refuses_an_unattended_kind_with_no_landing(self):
        verbs = verbs_catalog()
        verbs["verbs"]["cleanup"]["lands"] = []
        problems, _ = h.verb_catalog_problems(verbs)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("cleanup: an unattended session kind with no declared landing", problems[0])
        # attended = true lifts the rule, whatever lands says.
        verbs["verbs"]["cleanup"]["attended"] = True
        self.assertEqual(h.verb_catalog_problems(verbs)[0], [])
        # A script may be unattended with no landing: it spawns nothing.
        verbs = verbs_catalog()
        verbs["verbs"]["digest"]["lands"] = []
        self.assertEqual(h.verb_catalog_problems(verbs)[0], [])

    def test_the_check_refuses_bad_keys_and_a_landing_outside_writes(self):
        verbs = verbs_catalog()
        v = verbs["verbs"]
        v["note"]["trigger"] = ["manual", "weekly"]
        v["open"]["lands"] = ["notepad/{date}.md"]
        v["close"]["lands"] = ["the moved folder"]
        del v["week"]["attended"]
        v["desk"]["attended"] = "yes"
        v["survey"]["trigger"] = []
        v["where"]["kind"] = "cron"
        problems, _ = h.verb_catalog_problems(verbs)
        want = ["note: trigger 'weekly'", "open: lands 'notepad/{date}.md' falls inside none of writes ['desk/{folder}', 'filing-cabinet/{folder}']",
                "close: lands entry 'the moved folder' is prose", "week: no attended key", "desk: attended must be",
                "survey: trigger must be a non-empty list", "where: kind must be one of"]
        for w in want:
            self.assertTrue(any(w in p for p in problems), f"{w!r} not reported in {problems}")
        self.assertEqual(len(problems), len(want), problems)
        self.assertEqual(h.verb_catalog_problems({})[0], ["no [verbs] table"])

    def test_placeholders_and_prefixes(self):
        self.assertTrue(h.falls_inside("notepad/{date}-{slug}.md", "notepad"))
        self.assertTrue(h.falls_inside("desk/{name}/folder.md", "desk/{folder}"))
        self.assertTrue(h.falls_inside("{project}", "{project}"))
        self.assertTrue(h.falls_inside("floor-plan/manifest.toml", "{spaces being changed}"))
        self.assertFalse(h.falls_inside("notepad", "notepad/{date}.md"))
        self.assertFalse(h.falls_inside("desktop/a", "desk"))
        self.assertTrue(h.is_path_entry("desk/{member folders}"))
        self.assertFalse(h.is_path_entry("the new office"))
        self.assertFalse(h.is_path_entry(""))

    def test_the_existing_verbs_took_the_keys_as_ruled(self):
        """Blueprint section 6: every script attended, manual, lands equal
        to writes ([] when read-only) except sessions, which a harness
        also runs; build attended until a build kind with a landing is
        proven by hand. The ruling of the fourth page relaxes the pin for
        verbs that move a folder: lands means exists after, so close
        lands the cabinet alone and reopen the desk alone. tour writes a
        throwaway office it deletes before it ends, so it lands nothing."""
        v = verbs_catalog()["verbs"]
        prose = {"init", "found", "upgrade", "default", "start", "land", "tour"}
        moves = {"close": ["filing-cabinet/{folder}"], "reopen": ["desk/{folder}"]}
        for name, verb in v.items():
            if verb["kind"] != "script" or name in DECLARED_KINDS:
                continue
            if name in DRAFTING_LANDS:
                # Blueprint section 3's table: moves runs with nobody
                # there after a sitting; the rest are attended, manual.
                self.assertEqual(verb["lands"], DRAFTING_LANDS[name], name)
                attended, trigger = DRAFTING_RUNS.get(name, (True, ["manual"]))
                self.assertEqual(verb["attended"], attended, name)
                self.assertEqual(verb["trigger"], trigger, name)
                self.assertTrue(verb["built"], name)
                continue
            if name == "sessions":
                self.assertFalse(verb["attended"])
                self.assertEqual(verb["trigger"], ["manual", "after-build"])
            else:
                self.assertTrue(verb["attended"], name)
                self.assertEqual(verb["trigger"], ["manual"], name)
            if name in moves:
                self.assertEqual(verb["lands"], moves[name], name)
                self.assertEqual(sorted(verb["writes"]), ["desk/{folder}", "filing-cabinet/{folder}"], name)
            elif name not in prose:
                self.assertEqual(verb["lands"], verb["writes"], name)
        self.assertEqual(v["start"]["lands"], ["desk/{folder}/folder.md"])
        # office found lands the answers it keeps; the floor plan changes
        # only when the zone does, and the session is office start's.
        self.assertEqual(v["found"]["lands"], ["desk/{folder}/answers.md"])
        # A HOLD lands nothing, so land guarantees nothing.
        self.assertEqual(v["land"]["lands"], [])
        # The tour's office is gone when it ends.
        self.assertEqual(v["tour"]["lands"], [])
        self.assertTrue(v["tour"]["built"])
        for name in ("founding", "work", "prep", "meeting", "renovate", "build"):
            self.assertTrue(v[name]["attended"], name)
        self.assertEqual(v["build"]["lands"], [])

    def test_the_declared_kinds_are_registered_and_not_built(self):
        v = verbs_catalog()["verbs"]
        for name in DECLARED_KINDS:
            self.assertIn(name, v)
            self.assertFalse(v[name]["built"], name)
        self.assertEqual(v["sitting"]["lands"], ["notepad/{date}-{slug}.md"])
        self.assertEqual(v["cleanup"]["attended"], False)
        self.assertEqual(v["cleanup"]["trigger"], ["after-build", "after-sitting", "schedule"])
        self.assertIn("drafting-table/riders.md", v["cleanup"]["ships"])
        self.assertIn("drafting-table/riders.md", v["cleanup"]["writes"])
        self.assertEqual(v["blueprint-close"]["kind"], "office-session")
        for name in ("review", "check", "retry"):
            self.assertEqual(v[name]["kind"], "project-session", name)
            self.assertEqual(v[name]["lands"], [], name)
            self.assertTrue(v[name]["attended"], name)
        self.assertEqual(v["review"]["trigger"], ["on-hold"])
        self.assertEqual(v["retry"]["trigger"], ["on-correctable-hold"])
        # 4b-1 declared moves, the blueprint, rider and agenda verbs,
        # riders, rulings and evidence; 4b-2 the watches verbs and the
        # digest, which leaves the declared kinds a script, built.
        for name in ("watches", "watches-check", "digest"):
            self.assertEqual(v[name]["kind"], "script", name)
            self.assertTrue(v[name]["built"], name)

    def test_the_shipped_spaces_catalog_holds(self):
        """The rider from session 1: filed and hung are both lists of
        paths with different meanings. Today's catalog has no hung page
        that is also filed; this is the calibration point."""
        self.assertEqual(h.space_catalog_problems(spaces_catalog()), [])

    def test_a_hung_filed_page_is_refused(self):
        spaces = spaces_catalog()
        spaces["spaces"]["drafting-table"]["hung"] = ["drafting-table/rulings.md"]
        problems = h.space_catalog_problems(spaces)
        self.assertEqual(problems, ["drafting-table: hung 'drafting-table/rulings.md' is also filed ('drafting-table/rulings.md')"])
        spaces["spaces"]["drafting-table"]["hung"] = ["drafting-table/blueprints/arc/close.md"]
        self.assertIn("is also filed ('drafting-table/blueprints/*/close.md')", h.space_catalog_problems(spaces)[0])
        spaces = spaces_catalog()
        spaces["spaces"]["notepad"]["hung"] = True
        self.assertEqual(h.space_catalog_problems(spaces), ["notepad: the whole space is hung and filed at once"])
        spaces = spaces_catalog()
        spaces["spaces"]["floor-plan"]["filed"] = True
        self.assertEqual(h.space_catalog_problems(spaces), ["floor-plan: hung 'floor-plan/survey.md' is inside a space filed whole"])

    def test_a_filed_or_hung_entry_must_be_a_page_or_glob_inside_the_space(self):
        spaces = spaces_catalog()
        spaces["spaces"]["drafting-table"]["filed"] += ["notepad/x.md", "drafting-table/a page.md", "drafting-table/"]
        spaces["spaces"]["handbook"]["hung"] = "README.md"
        problems = h.space_catalog_problems(spaces)
        self.assertEqual(len(problems), 4, problems)
        for want in ("filed entry 'notepad/x.md'", "filed entry 'drafting-table/a page.md'", "filed entry 'drafting-table/'",
                     "handbook: hung must be true, false or a list"):
            self.assertTrue(any(want in p for p in problems), want)
        self.assertEqual(h.space_catalog_problems({"spaces": {}}), ["no [spaces] table"])

    def test_catalog_check_subcommand(self):
        with tempfile.TemporaryDirectory() as d:
            verbs, spaces = pathlib.Path(d, "verbs.toml"), pathlib.Path(d, "spaces.toml")
            shutil.copy(REPO / "share/verbs.toml", verbs)
            shutil.copy(REPO / "share/spaces.toml", spaces)
            cmd = [sys.executable, "-B", str(REPO / "lib/office_helper.py"), "catalog-check", str(verbs), str(spaces)]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(proc.stdout, "")
            self.assertIn("unchecked: init: lands", proc.stderr)
            verbs.write_text(verbs.read_text().replace('trigger = ["after-build", "after-sitting", "schedule"]',
                                                       'trigger = ["after-build", "nightly"]'))
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 3)
            self.assertIn("cleanup: trigger 'nightly'", proc.stdout)
            verbs.write_text("not toml [")
            self.assertEqual(subprocess.run(cmd, capture_output=True, text=True).returncode, 1)


class TestStatusReportsTheCatalogs(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.root = self.e.init()

    def test_status_says_the_installed_catalogs_hold(self):
        out = self.e.run("status", cwd=self.root, check=0).stdout
        self.assertIn("catalogs:   every unattended session kind declares a landing; no hung page is filed", out)

    def test_status_reports_an_offender_in_the_install(self):
        """An office on a broken install hears about it: the check reads
        the install's catalogs, never the office."""
        office = self.e.fake_install(PATCH)
        verbs = office.parent.parent / "share" / "verbs.toml"
        text = verbs.read_text(encoding="utf-8")
        self.assertIn('\nlands = ["desk/{folder}/folder.md"]\nattended = false\n', text)
        verbs.write_text(text.replace('\nlands = ["desk/{folder}/folder.md"]\nattended = false\n', '\nlands = []\nattended = false\n'),
                         encoding="utf-8")
        spaces = office.parent.parent / "share" / "spaces.toml"
        spaces.write_text(spaces.read_text().replace('path = "notepad"\nbase = true\nfiled = true',
                                                     'path = "notepad"\nbase = true\nhung = true\nfiled = true'))
        proc = self.e.run("status", cwd=self.root, bin_path=office, check=0)
        self.assertIn(f"catalogs:   DEFECT in the install at {office.parent.parent}", proc.stdout)
        self.assertIn("  cleanup: an unattended session kind with no declared landing", proc.stdout)
        self.assertIn("  notepad: the whole space is hung and filed at once", proc.stdout)
        verbs.write_text("[verbs\n")
        proc = self.e.run("status", cwd=self.root, bin_path=office, check=0)
        self.assertIn("catalogs:   could not be checked", proc.stdout)


# --- office-src's own development record -----------------------------------------

SITTINGS = REPO / "claude/context/sittings"
# Each sitting's page is write-once: its sha256 as landed, by session id.
WORDS_SHA256 = {
    "2026-09-23-office-construction-001": "9c804c7dae8ee5056e571720bdc5defc42acd6a497fcc0299d87286aad930a64",
    "2026-09-29-continue-plan-002": "6d1097bb8986ebafdc8902db26019d3ce1f0ba2eaa174917b08345cc850f5c4a",
    # A sitting that outlives its first page continues on -2, -3.
    "2026-09-29-continue-plan-002-2": "b5a3f09fd59ac66f3fd0023a98a23dd0d13ac35188a4dce6a01624ee1ca18c78",
    "2026-09-29-continue-plan-002-3": "6e1e0c056307d3606da8a3d595d973fd15280833d980324574966fc87fc69eaf",
    "2026-09-29-continue-plan-002-4": "da1fbbc5514918a2d57aadb7affdd052d8a008560e749c32219d551e775d3c6d",
    "2026-10-02-friction-wave-sitting-001": "97a2df5f66da24b7a75a13024da98403e9aa4229865014e5c993410de592ddf2",
    "2026-10-02-friction-wave-sitting-001-2": "2db9f41b29aa1adaac51fa6a4f06aec8f0eb397f05493862f405138c0b24c13e",
    "2026-10-02-friction-wave-sitting-001-3": "b48fdc2ecde43007c680b59f4d75c165dc63a9eef6c70eb95367bd38dda7c44a",
    # The last sitting page office-src receives: from sitting
    # 2026-10-03-plan-4b-sitting-001 on, a sitting's words go to the
    # office's notepad through the pages its bundles carry.
    "2026-10-02-friction-wave-sitting-001-4": "b215511da03ba2ad32462e3600f5862b0a5f135291058af4a347fcf070eb81f5",
}


class TestDevelopmentRecord(unittest.TestCase):
    def test_the_planner_words_pages_are_byte_exact(self):
        import hashlib
        for sid, sha in WORDS_SHA256.items():
            self.assertEqual(hashlib.sha256((SITTINGS / f"{sid}.md").read_bytes()).hexdigest(), sha, sid)

    def test_every_sitting_page_is_pinned(self):
        self.assertEqual(sorted(p.stem for p in SITTINGS.glob("*.md")), sorted(WORDS_SHA256))

    def test_the_record_is_never_installed(self):
        text = (REPO / "install.sh").read_text()
        shipped = re.search(r"^SHIPPED=\((.*)\)$", text, re.M).group(1).split()
        self.assertNotIn("cla" + "ude", shipped)
        self.assertTrue(all(not s.startswith("cla" + "ude") for s in shipped))


# --- install -------------------------------------------------------------------

class TestInstall(unittest.TestCase):
    def setUp(self):
        self.e = Env(self)
        self.src = self.e.tmp / "office-src"
        shutil.copytree(REPO, self.src, ignore=shutil.ignore_patterns(".git", ".bale", "__pycache__"))
        self.e.git(self.src, "init", "-q")
        self.e.git(self.src, "add", "-A")
        self.e.git(self.src, "commit", "-qm", "src")
        self.prefix = self.e.tmp / "share" / "office-src"
        self.bindir = self.e.tmp / "bin"

    def install(self, *extra):
        return subprocess.run([str(self.src / "install.sh"), "--prefix", str(self.prefix),
                               "--bin-dir", str(self.bindir), *extra],
                              env=self.e.env, capture_output=True, text=True, timeout=60)

    def test_installs_links_and_knows_its_version(self):
        proc = self.install()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(f"office-src {VERSION}", proc.stdout)
        stamp = (self.prefix / "INSTALLED").read_text()
        self.assertIn(f"version: {VERSION}", stamp)
        self.assertTrue((self.bindir / "office").is_symlink())
        self.assertFalse((self.prefix / "tests").exists())
        out = subprocess.run([str(self.bindir / "office"), "version"], env=self.e.env,
                             capture_output=True, text=True).stdout
        self.assertIn(str(self.prefix), out)

    def test_installed_command_builds_an_office_reading_the_install(self):
        self.assertEqual(self.install().returncode, 0)
        self.e.run("init", str(self.e.home / "w"), "--no-founding", bin_path=self.bindir / "office", check=0)
        out = self.e.run("status", cwd=self.e.home / "w", bin_path=self.bindir / "office", check=0).stdout
        self.assertIn(f"install:    office-src {VERSION} at {self.prefix}", out)

    def test_reinstall_replaces_and_uncommitted_work_is_left_out(self):
        self.assertEqual(self.install().returncode, 0)
        (self.prefix / "stray").write_text("x")
        (self.src / "VERSION").write_text("9.9.9\n")
        proc = self.install()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("uncommitted changes", proc.stderr)
        self.assertFalse((self.prefix / "stray").exists())
        self.assertEqual((self.prefix / "VERSION").read_text().strip(), VERSION)

    def test_refuses_a_prefix_that_is_not_an_install(self):
        self.prefix.mkdir(parents=True)
        (self.prefix / "keep").write_text("mine")
        proc = self.install()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not an office-src install", proc.stderr)
        self.assertTrue((self.prefix / "keep").exists())


# --- text rules ------------------------------------------------------------------

# Split so this file does not trip its own checks.
MODEL_NAMES = ["cla" + "ude", "anth" + "ropic", "open" + "ai", "chat" + "gpt", "gem" + "ini", "g" + "pt-", "copi" + "lot", "ll" + "ama"]
OFFICE_SPECIFIC = ["med" + "gen", "zago" + "odma", "mm" + "ge", "iu" + "pui", "github." + "iu", "i" + "u health",
                   "sh" + "iny", "chord" + "sphere", "m10" + "_"]
FINGERPRINTS = [r"^\s*note:", r"^\s*important:", r"in summary", r"why this file exists"]


def office_bound_text():
    """Text that lands in an office or ships with every office session:
    the doctrine and its checks, and every template."""
    return [REPO / "doctrine/OFFICE.md", *sorted((REPO / "doctrine/checks").glob("*.sh")),
            *sorted((REPO / "templates").glob("*.md"))]


OWN_DIRS = ("bin", "lib", "share", "templates", "doctrine", "migrations", "tests")
OWN_FILES = ("VERSION", "README.md", "RELEASES.md", "install.sh", ".gitignore")


def own_text():
    """Everything office-src's repo holds, except this file. Named
    explicitly rather than walked from the root, because a validation
    staging copy puts its own files beside the tree."""
    skip = pathlib.Path(__file__).resolve()
    out = [REPO / f for f in OWN_FILES]
    for d in OWN_DIRS:
        out += [p for p in sorted((REPO / d).rglob("*"))
                if p.is_file() and "__pycache__" not in p.relative_to(REPO).parts and p.resolve() != skip]
    return out


class TestText(unittest.TestCase):
    def test_office_bound_text_is_ascii(self):
        for p in office_bound_text():
            for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                self.assertTrue(line.isascii(), f"{p.name}:{n}: {line!r}")

    def test_office_bound_text_has_no_fingerprints(self):
        for p in office_bound_text():
            for n, line in enumerate(p.read_text().splitlines(), 1):
                for pat in FINGERPRINTS:
                    self.assertIsNone(re.search(pat, line, re.I), f"{p.name}:{n}: {line!r}")

    def test_names_no_model_and_no_office(self):
        self.assertGreaterEqual(len(own_text()), 20)
        for p in own_text():
            text = p.read_text(encoding="utf-8", errors="replace").lower()
            for word in MODEL_NAMES + OFFICE_SPECIFIC:
                self.assertNotIn(word, text, f"{p.relative_to(REPO)} names {word!r}")

    def test_profile_template_matches_the_shape(self):
        shape = tomllib.loads((REPO / "share/profile-shape.toml").read_text())
        headings = re.findall(r"^## (.+)$", (REPO / "templates/profile.md").read_text(), re.M)
        self.assertEqual(headings, [s["heading"] for s in shape["section"]])
        doctrine = (REPO / "doctrine/OFFICE.md").read_text()
        for s in shape["section"]:
            self.assertIn(f"- {s['heading']}:", doctrine)

    def test_doctrine_space_table_matches_the_catalog(self):
        catalog = tomllib.loads((REPO / "share/spaces.toml").read_text())["spaces"]
        doctrine = (REPO / "doctrine/OFFICE.md").read_text()
        spaces = doctrine.split("## 5. Spaces", 1)[1].split("## 6.", 1)[0]
        rows = re.findall(r"^\| ([a-z.-]+/?) \| [^|]+ \| (yes|renovation) \|", spaces, re.M)
        table = {path.rstrip("/"): base == "yes" for path, base in rows}
        self.assertEqual(table, {s["path"]: bool(s.get("base")) for s in catalog.values()})

    def test_doctrine_verb_table_covers_the_declarations(self):
        """Every verb the catalog declares has a row in the doctrine's verb
        table, except a kind declared ahead of the command (DECLARED_KINDS),
        which may wait for its row until it is built: a built verb with no
        doctrine row is a defect either way. Every row names a declared
        verb."""
        verbs = verbs_catalog()["verbs"]
        doctrine = (REPO / "doctrine/OFFICE.md").read_text()
        cells = re.findall(r"^\| ([a-z, -]+) \|", doctrine, re.M)
        # A two-word verb (blueprint open) is hyphenated in the catalog.
        named = {n.strip().replace(" ", "-") for cell in cells for n in cell.split(",")}
        for name, verb in verbs.items():
            if name in DECLARED_KINDS and not verb["built"] and name not in named:
                continue
            self.assertIn(name, named, f"{name} has no row in the doctrine's verb table")
        for name in named - {"verb", "path"}:
            self.assertIn(name, verbs, f"the doctrine's verb table names {name}, which the catalog does not declare")

    def test_help_lists_every_built_script_verb(self):
        verbs = verbs_catalog()["verbs"]
        usage = subprocess.run([str(REPO / "bin/office"), "help"], capture_output=True, text=True).stdout
        for name, v in verbs.items():
            if v["kind"] == "script" and v["built"]:
                self.assertIn(name.replace("-", " "), usage, name)
        # A kind declared ahead of the command is not in the help.
        self.assertNotIn("office sitting", usage)

    def test_bale_office_line_is_verbatim(self):
        line = ("The line between bale and office. Test: is this about a session or about a job? "
                "bale records everything from pack to close inside one repo, including lineage between sessions. "
                "The office records the person and the job across repos and time: why a session was opened, "
                "the planner's words, what was decided, what is next, which sessions belong to which job. "
                "A folder points at session ids; it never copies what bale records. "
                "Where bale lacks a session-shaped fact, that is a slip for bale-src, not an office workaround. "
                "Two bale doctrine limits bind: bale is \"not a master-changelog system\" (AGENT.md section 7), "
                "and a dashboard \"renders the stats; it never owns them\" (PLANNER.md section 17).")
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        self.assertIn(line, doctrine)

    def test_append_rule_is_verbatim_and_names_its_check(self):
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        self.assertIn("Appending is not rewriting: a filed page grows at its end, and the bytes "
                      "already filed never change.", doctrine)
        self.assertIn("doctrine/checks/filed-append-only.sh", doctrine)
        self.assertTrue((REPO / "doctrine/checks/filed-append-only.sh").is_file())

    def test_shell_syntax(self):
        for p in (REPO / "bin/office", REPO / "install.sh", *sorted((REPO / "doctrine/checks").glob("*.sh"))):
            proc = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
