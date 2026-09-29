"""Tests for doctrine/checks/filed-append-only.sh, the filed-paper check
a session pastes into its validation.sh (OFFICE.md section 15): the
first base_size bytes of a staged filed page must hash to the base the
request stamped, so a page can only grow at its end.

Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import hashlib
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest

REPO = pathlib.Path(__file__).resolve().parent.parent
CHECK = REPO / "doctrine" / "checks" / "filed-append-only.sh"
FRAGMENT_MARKER = "# --- run as a script ---"

BASE = b"# Rulings\n\n## 2026-09-29-first\n\n- ruled: 2026-09-29\n\n**First.** The text.\n"
BASE_SHA = hashlib.sha256(BASE).hexdigest()
BASE_SPEC = f"drafting-table/rulings.md={len(BASE)}:{BASE_SHA}"


class Office:
    """A scratch office root holding one filed page in its base state."""

    def __init__(self, test):
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="filed-check-"))
        test.addCleanup(shutil.rmtree, self.root, True)
        self.page = self.root / "drafting-table" / "rulings.md"
        self.page.parent.mkdir(parents=True)
        self.page.write_bytes(BASE)
        self.base_copy = self.root.parent / f"{self.root.name}-base.md"
        self.base_copy.write_bytes(BASE)
        test.addCleanup(self.base_copy.unlink)

    def run(self, *specs, cwd=None, root=True):
        args = [str(CHECK)]
        if root:
            args += ["--root", str(self.root)]
        return subprocess.run(args + list(specs), cwd=cwd or self.root, capture_output=True, text=True, timeout=60)


class TestFiledAppendOnly(unittest.TestCase):
    def setUp(self):
        self.o = Office(self)

    def test_ships_executable_with_clean_syntax(self):
        self.assertTrue(os.access(CHECK, os.X_OK), CHECK)
        proc = subprocess.run(["bash", "-n", str(CHECK)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_additions_at_the_end_pass(self):
        self.o.page.write_bytes(BASE + b"\n## 2026-09-30-second\n\n**Second.**\n")
        proc = self.o.run(BASE_SPEC)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("[PASS] filed-append-only: drafting-table/rulings.md: grew by", proc.stdout)
        self.assertIn("1 passed, 0 failed, 1 checked", proc.stdout)

    def test_an_unchanged_page_passes(self):
        proc = self.o.run(BASE_SPEC)
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("unchanged", proc.stdout)

    def test_an_edit_inside_the_base_fails_and_names_the_path(self):
        self.o.page.write_bytes(BASE.replace(b"The text.", b"The TEXT.") + b"\nmore\n")
        proc = self.o.run(BASE_SPEC)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"[FAIL] filed-append-only: drafting-table/rulings.md: the first {len(BASE)} bytes changed", proc.stdout)
        self.assertIn("grows at its end only", proc.stdout)

    def test_a_truncation_fails(self):
        self.o.page.write_bytes(BASE[:20])
        proc = self.o.run(BASE_SPEC)
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn(f"truncated to 20 bytes; the base was {len(BASE)} bytes", proc.stdout)

    def test_a_new_page_with_no_base_passes_and_a_missing_one_fails(self):
        (self.o.root / "drafting-table" / "evidence.md").write_text("# Evidence\n")
        proc = self.o.run("drafting-table/evidence.md=new")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("[PASS] filed-append-only: drafting-table/evidence.md: new filed page", proc.stdout)
        proc = self.o.run("drafting-table/watch-log.md=new")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("[FAIL] filed-append-only: drafting-table/watch-log.md: filed page is missing", proc.stdout)

    def test_a_base_copy_measures_size_and_hash(self):
        self.o.page.write_bytes(BASE + b"tail\n")
        proc = self.o.run(f"drafting-table/rulings.md=@{self.o.base_copy}")
        self.assertEqual(proc.returncode, 0, proc.stdout)
        self.assertIn("grew by 5 bytes", proc.stdout)
        proc = self.o.run("drafting-table/rulings.md=@/nonexistent/base.md")
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("base copy not found", proc.stdout)

    def test_several_specs_report_each_and_fail_together(self):
        (self.o.root / "drafting-table" / "evidence.md").write_text("# Evidence\n")
        self.o.page.write_bytes(BASE[:5])
        proc = self.o.run(BASE_SPEC, "drafting-table/evidence.md=new")
        self.assertEqual(proc.returncode, 1, proc.stdout)
        self.assertIn("[FAIL] filed-append-only: drafting-table/rulings.md: truncated", proc.stdout)
        self.assertIn("[PASS] filed-append-only: drafting-table/evidence.md", proc.stdout)
        self.assertIn("1 passed, 1 failed, 2 checked", proc.stdout)

    def test_runs_from_the_office_root_without_a_root_flag(self):
        proc = self.o.run(BASE_SPEC, root=False)
        self.assertEqual(proc.returncode, 0, proc.stdout)

    def test_bad_specs_are_usage_errors_not_verdicts(self):
        cases = ["drafting-table/rulings.md", "=12:" + BASE_SHA, "drafting-table/rulings.md=12:zz",
                 "drafting-table/rulings.md=many:" + BASE_SHA, "drafting-table/rulings.md=old"]
        for spec in cases:
            proc = self.o.run(spec)
            self.assertEqual(proc.returncode, 2, (spec, proc.stdout))
            self.assertIn("[FAIL] filed-append-only:", proc.stdout)
        proc = self.o.run()
        self.assertEqual(proc.returncode, 2, proc.stdout)
        self.assertIn("no filed paths given", proc.stdout)
        proc = self.o.run("--root", "/nonexistent", BASE_SPEC, root=False)
        self.assertEqual(proc.returncode, 2, proc.stdout)

    def test_the_fragment_above_the_marker_pastes_into_a_validation_script(self):
        """A worker pastes everything above the marker into its
        validation.sh and calls filed_append_only with its specs."""
        text = CHECK.read_text()
        self.assertIn(FRAGMENT_MARKER, text)
        fragment = text.split(FRAGMENT_MARKER, 1)[0]
        self.assertNotIn('filed_append_only "$@"', fragment)
        self.o.page.write_bytes(BASE + b"appended\n")
        script = self.o.root / "validation.sh"
        script.write_text(fragment + f'\nfiled_append_only --root "{self.o.root}" {BASE_SPEC} || exit 1\necho done\n')
        proc = subprocess.run(["bash", str(script), "--verbose"], capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("[PASS]", proc.stdout)
        self.assertIn("done", proc.stdout)

    def test_writes_nothing(self):
        before = sorted(p.relative_to(self.o.root) for p in self.o.root.rglob("*"))
        self.o.run(BASE_SPEC, "drafting-table/evidence.md=new")
        after = sorted(p.relative_to(self.o.root) for p in self.o.root.rglob("*"))
        self.assertEqual(before, after)
        self.assertEqual(self.o.page.read_bytes(), BASE)


if __name__ == "__main__":
    unittest.main()
