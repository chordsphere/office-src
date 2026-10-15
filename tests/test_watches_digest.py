"""Tests for the second half of blueprint session 4b: the watch-query
catalog (share/watch-queries.toml), office watches and office watches
check [--record], office digest, the digest written before a sitting is
packed, the stats surface's --since form and the commit subjects in the
consumption manifest, and pending desk moves on the Next line.

bale is never needed. The fake bale of the read side's tests replays the
lines the drafting-table-digest probe captured (kept verbatim, with their
sha256, in the development record's fixtures under watches/), one
directory per repo, so each repo the office reads is one coherent
snapshot: its status, its aggregates whole and windowed, and the dossier
of every session it names. Every test works under its own temporary HOME
and sets its own clock where a date matters (git's commit dates); none
reads the machine's zone. Run with the rest of the suite:

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
"""

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_office import REPO, h  # noqa: E402
from test_read_side import FIXTURES, FakeBale, literal_key_reads, resolve  # noqa: E402
from test_desk_verbs import Office, office_status_fixture  # noqa: E402
from test_start import FakePackBale, tar_names  # noqa: E402

import office_bale as ob  # noqa: E402
import office_drafting as od  # noqa: E402
import office_watches as ow  # noqa: E402

WATCHES = FIXTURES / "watches"
REPOS = ("office-src", "home-office", "bale-src", "ironwood", "nisaba-src", "twine-src")
CATALOG = REPO / "share" / "watch-queries.toml"
CONSUMPTION = REPO / "share" / "bale-consumption.toml"
DT = "drafting-table"
HELD_THEN_APPLIED = "2026-10-05-drafting-table-pages-001"
OPEN_HERE = "2026-10-06-drafting-table-digest-001"
SITTING = "2026-10-03-plan-4b-sitting-001"


def records(setname):
    d = WATCHES / setname
    return [(f, json.loads(f.read_text(encoding="utf-8"))) for f in sorted(d.glob("*.json"))]


def line_of(setname, argv):
    for _, rec in records(setname):
        if rec.get("argv") == argv:
            return json.loads(rec["stdout"][0])
    raise KeyError((setname, argv))


def git_capture(name):
    return json.loads((WATCHES / "git" / f"{name}.json").read_text(encoding="utf-8"))


class Replay:
    """A Reader whose bale replays one capture set per directory name,
    for unit tests that need no PATH: the directory's last part names
    the set."""

    def __init__(self):
        self.rd = ob.Reader(runner=self.run)
        self.rd.bale = lambda: "bale"

    def run(self, argv, cwd=None, **kw):
        import types
        name = pathlib.Path(cwd).name if cwd else "anywhere"
        for d in (WATCHES / name, FIXTURES / "anywhere"):
            for f in sorted(d.glob("*.json")) if d.is_dir() else []:
                rec = json.loads(f.read_text(encoding="utf-8"))
                if rec.get("argv") == argv[1:]:
                    return types.SimpleNamespace(returncode=rec["exit"], stdout="\n".join(rec["stdout"]) + "\n",
                                                 stderr="\n".join(rec["stderr"]))
        return types.SimpleNamespace(returncode=97, stdout="", stderr=f"no capture for {argv[1:]} in {name}")


# --- the probe's captures ---------------------------------------------------------------

class TestCaptures(unittest.TestCase):
    def test_every_line_is_the_one_the_probe_captured(self):
        n = 0
        for setname in (*REPOS, "git"):
            for f, rec in records(setname):
                self.assertEqual(len(rec["stdout"]), len(rec["stdout_sha256"]), f)
                for line, sha in zip(rec["stdout"], rec["stdout_sha256"]):
                    self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), sha, f.name)
                    n += 1
                self.assertIn("probe of session 2026-10-06-drafting-table-digest-001", rec["captured"])
        self.assertEqual(n, 79)

    def test_each_repo_is_one_coherent_snapshot(self):
        """Every sid a status line's outbox names has its dossier beside it,
        so the digest's readings replay whole."""
        for setname in ("office-src", "home-office"):
            st = line_of(setname, ["status", "--json"])
            sids = set(st["sessions"]) | {n[len("request-"):-len(".tar.gz")] for n in st["outbox"]}
            for sid in sids:
                d = line_of(setname, ["stats", "--sid", sid, "--json"])
                self.assertTrue(d["found"], sid)
        self.assertEqual(line_of("office-src", ["status", "--json"])["sessions"], [OPEN_HERE])
        self.assertEqual(line_of("home-office", ["status", "--json"])["scopes"], {SITTING: []})

    def test_since_is_a_day_and_bale_says_which(self):
        for setname, days in (("office-src", ("2026-08-01", "2026-10-01", "2026-10-05", "2026-10-06", "2026-10-07")),
                              ("home-office", ("2026-09-30", "2026-10-04", "2026-10-07"))):
            for day in days:
                self.assertEqual(line_of(setname, ["stats", "--json", "--since", day])["filters"]["since"], day)
        self.assertEqual(line_of("office-src", ["stats", "--json", "--since", "2026-10-07"])["corpus"]["sessions"], 0)
        self.assertEqual(line_of("office-src", ["stats", "--json", "--since", "2026-10-06"])["members"]["in_flight"],
                         [OPEN_HERE])
        refused = next(r for _, r in records("office-src") if r.get("argv") == ["stats", "--json", "--since",
                                                                                 "2026-10-06T00:00:00"])
        self.assertEqual(refused["exit"], 1)
        self.assertIn("--since must be an ISO date (YYYY-MM-DD)", refused["stderr"][-1])
        both = line_of("office-src", ["stats", "--json", "--work-class", "code", "--since", "2026-10-01"])
        self.assertEqual(both["filters"], {"work_class": "code", "since": "2026-10-01"})


# --- the consumption manifest ------------------------------------------------------------

class TestConsumption(unittest.TestCase):
    def setUp(self):
        self.cons = ob.Consumption()
        self.data = tomllib.loads(CONSUMPTION.read_text())

    def test_since_is_an_optional_flag_after_the_work_class(self):
        self.assertEqual(self.cons.argv("stats", since="2026-10-01"), ["stats", "--json", "--since", "2026-10-01"])
        self.assertEqual(self.cons.argv("stats", work_class="code", since="2026-10-01"),
                         ["stats", "--json", "--work-class", "code", "--since", "2026-10-01"])
        argvs = [rec["argv"] for s in REPOS for _, rec in records(s)]
        self.assertIn(self.cons.argv("stats", since="2026-10-01"), argvs)
        self.assertIn(self.cons.argv("stats", work_class="code", since="2026-10-01"), argvs)

    def test_every_declared_stats_key_is_in_the_new_captures(self):
        for setname in REPOS:
            line = line_of(setname, ["stats", "--json"])
            for key in self.data["surfaces"]["stats"]["keys"]:
                reached, missing = resolve(line, key)
                self.assertEqual(missing, [], f"{setname} lacks {key}")

    def test_every_key_is_read_literally_or_by_the_catalog_and_none_is_left_over(self):
        reads, dynamic = literal_key_reads()
        declared = {(s, k) for s, spec in self.data["surfaces"].items() if spec.get("calls", True)
                    for k in spec.get("keys", [])}
        catalog = ow.Catalog().keys()
        self.assertEqual(catalog - declared, set(), "the catalog reads a key the manifest does not declare")
        reads |= {(s, "outcome") for s, spec in self.data["surfaces"].items() if spec.get("keys")}
        self.assertEqual(declared - reads - catalog, set(), "declared but never read")

    def test_the_commit_subjects_are_declared_and_read_the_captures(self):
        spec = self.data["surfaces"]["commits"]
        self.assertFalse(spec["calls"])
        with self.assertRaises(ob.BaleError):
            self.cons.argv("commits")
        kinds = {"work": set(), "merge": set(), "sweep": set()}
        for name in ("office-src_subjects",):
            for line in git_capture(name)["stdout"]:
                subject = line.split("\t", 2)[2]
                found = self.cons.subject_sid(subject)
                if subject.startswith(("[bale ", "Merge bale ")):
                    self.assertIsNotNone(found, subject)
                    kinds[found[0]].add(found[1])
                else:
                    self.assertIsNone(found, subject)
        # Every session bale merged left its work commit and its sweep.
        self.assertEqual(kinds["merge"] - kinds["work"], set())
        self.assertEqual(kinds["merge"] - kinds["sweep"], set())
        self.assertIn(HELD_THEN_APPLIED, kinds["merge"])
        # The read-only sittings were swept and never merged.
        self.assertIn("2026-10-02-friction-wave-sitting-001", kinds["sweep"] - kinds["merge"])
        # Every merged session is an applied one, by its dossier.
        for sid in kinds["merge"]:
            self.assertEqual(line_of("office-src", ["stats", "--sid", sid, "--json"])["record"]["outcome"],
                             "applied", sid)

    def test_a_subject_that_only_looks_like_bales(self):
        for s in ("[bale nope] x", "Merge bale", "[bale sweep] applied", "bale: ignore .bale/", "[bale  x-001] y"):
            self.assertIsNone(self.cons.subject_sid(s), s)

    def test_the_aggregate_holds_the_window_it_was_asked_for(self):
        r = Replay()
        agg = r.rd.aggregate(str(WATCHES / "office-src"), since="2026-10-05")
        self.assertEqual(agg["filters"]["since"], "2026-10-05")
        with self.assertRaises(ValueError):
            r.rd.aggregate(str(WATCHES / "office-src"), since="2026-10-06T00:00:00")
        # bale answering for another window is refused, not believed.
        r.rd._cache[(str(WATCHES / "office-src"), ("stats", "--json", "--since", "2026-10-04"))] = \
            line_of("office-src", ["stats", "--json", "--since", "2026-10-05"])
        with self.assertRaises(ob.BaleError) as cm:
            r.rd.aggregate(str(WATCHES / "office-src"), since="2026-10-04")
        self.assertIn("not the '2026-10-04'", str(cm.exception))

    def test_reach_holds_catalog_keys_to_the_manifest(self):
        rd = ob.Reader()
        line = line_of("bale-src", ["stats", "--json"])
        self.assertEqual(len(rd.reach(line, "stats", "members.clarification_self_only")[0]), 9)
        with self.assertRaises(ob.BaleError) as cm:
            rd.reach(line, "stats", "classes.*.unparsed_share")
        self.assertEqual(cm.exception.kind, "undeclared")
        with self.assertRaises(ob.BaleError) as cm:
            rd.reach({"classes": {"code": {}}}, "stats", "classes.*.held_attempts")
        self.assertEqual(cm.exception.kind, "key")
        row = line["classes"]["code"]
        self.assertEqual(rd.reach(row, "stats", "classes.*.held_attempts", at="classes.*"), [22])


# --- the catalog -------------------------------------------------------------------------

class TestCatalog(unittest.TestCase):
    def test_the_seven_queries_of_blueprint_section_3_2(self):
        cat = ow.Catalog()
        self.assertEqual({n: q["watch"] for n, q in cat.queries.items()},
                         {"unparsed-share": 1, "unused-forecast-entries": 13, "hold-cause-cluster": 15,
                          "stamp-mismatch-accepts": 17, "claim-basis-split": 21, "hold-rate-by-class": 22,
                          "unrelayed-rounds": 24})
        self.assertEqual(sorted(n for n, q in cat.queries.items() if "needs" in q),
                         ["hold-cause-cluster", "stamp-mismatch-accepts"])
        self.assertEqual([n for n, _ in cat.standing()], ["claim-basis-split", "hold-rate-by-class"])
        self.assertEqual(cat.queries["hold-cause-cluster"]["needs"], "a HOLD cause class")

    def test_a_catalog_that_breaks_its_header_is_refused(self):
        cons = ob.Consumption()
        bad = {"x": {"watch": 1, "says": "s", "surface": "stats", "value": "share", "numerator": "classes.*.nope",
                     "denominator": "classes.*.validated_attempts", "compare": "above"},
               "Y y": {"watch": "1", "says": "", "needs": "d", "surface": "stats"},
               "z": {"watch": 2, "says": "s", "surface": "stats", "value": "class-rate",
                     "numerator": "classes.*.held_attempts", "denominator": "classes.*.response_attempts"},
               "w": {"watch": 3, "says": "s", "surface": "status", "value": "sum", "key": "x"},
               "v": {"watch": 4, "says": "s", "surface": "stats", "value": "sum", "key": "members",
                     "compare": "sideways"}}
        problems = ow.catalog_problems(bad, cons)
        for words in ("x: reads 'classes.*.nope'", "Y y: a query's name", "Y y: no watch number", "Y y: no says",
                      "Y y: a query bale cannot answer carries nothing else", "z: a class-rate value is an observation",
                      "w: surface is stats", "v: compare is one of"):
            self.assertTrue(any(p.startswith(words) or words in p for p in problems), f"{words} not in {problems}")
        tmp = pathlib.Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "q.toml").write_text(CATALOG.read_text().replace('"classes.*.held_attempts"', '"classes.*.nope_attempts"'))
        with self.assertRaises(h.HelperError) as cm:
            ow.Catalog(tmp / "q.toml")
        self.assertIn("does not declare", str(cm.exception))

    def test_every_query_runs_over_every_captured_aggregate(self):
        r = Replay()
        cat = ow.Catalog()
        runs = 0
        for setname in REPOS:
            for f, rec in records(setname):
                if rec["exit"] != 0 or rec["argv"][:2] != ["stats", "--json"]:
                    continue
                agg = json.loads(rec["stdout"][0])
                for name, q in cat.queries.items():
                    if "needs" in q:
                        continue
                    got = ow.observe(r.rd, q, agg) if q.get("standing") else ow.measure(r.rd, q, agg)
                    self.assertTrue(got, (setname, f.name, name))
                    runs += 1
        self.assertGreaterEqual(runs, 80)

    def test_the_values_the_captures_hold(self):
        r = Replay()
        cat = ow.Catalog()
        agg = lambda s, *a: r.rd.aggregate(str(WATCHES / s), *a)  # noqa: E731
        m = ow.measure(r.rd, cat.get("unparsed-share"), agg("ironwood"))
        self.assertEqual(m["shown"], "0.07 (4 of 55)")
        self.assertEqual(len(m["evidence"]), 4)
        self.assertIn("2026-10-02-loop-rehearsal-007", m["evidence"])
        m = ow.measure(r.rd, cat.get("unparsed-share"), agg("office-src", None, "2026-10-07"))
        self.assertIsNone(m["value"])
        self.assertFalse(ow.crosses(m["value"], "any", "above"))
        m = ow.measure(r.rd, cat.get("unused-forecast-entries"), agg("office-src", None, "2026-10-01"))
        self.assertEqual(m["value"], 4)
        m = ow.measure(r.rd, cat.get("unrelayed-rounds"), agg("bale-src"))
        self.assertEqual(m["value"], 9)
        self.assertEqual(m["evidence"][0], "2026-07-15-status-staging-row-003")
        self.assertEqual(ow.observe(r.rd, cat.get("hold-rate-by-class"), agg("office-src", None, "2026-10-05")),
                         "code 0.50 (1 of 2)")
        self.assertEqual(ow.observe(r.rd, cat.get("claim-basis-split"), agg("office-src", None, "2026-10-05")),
                         "code: observed 11 of 12 agree")
        self.assertEqual(ow.observe(r.rd, cat.get("hold-rate-by-class"), agg("office-src", None, "2026-10-07")),
                         "no classed sessions in bale's records")

    def test_comparing(self):
        for value, limit, compare, want in ((0.0, "any", "above", False), (0.01, "any", "at-least", True),
                                            (3, 3, "at-least", True), (3, 3, "above", False), (None, 0, "at-least", False),
                                            (4, 3.5, "above", True)):
            self.assertEqual(ow.crosses(value, limit, compare), want, (value, limit, compare))


# --- the register and the log --------------------------------------------------------------

REGISTER_PAGE = """
## W1 - Emitter-parser drift

- source: 2026-08-01-x-001 (notes)
- scope: office
- condition: unparsed reconciliation records
- evaluates: query unparsed-share
- threshold: any non-zero share
- re-trigger: any non-zero share since the last fired record

## W13 - Forecast precision

- source: 2026-08-07-board-13b-epoch-ledger-005 (notes)
- scope: office
- evaluates: query unused-forecast-entries
- threshold: 3
- re-trigger: three accruals since the last fired record

## W15 - HOLD clustering

- source: evidence 95
- scope: office
- evaluates: query hold-cause-cluster
- threshold: a third
- re-trigger: a third of HOLDs

## W17 - Amendment accepts

- source: 2026-08-01-x-001
- scope: office
- evaluates: query stamp-mismatch-accepts
- threshold: any
- re-trigger: any

## W22 - HOLD rate per class

- source: 2026-08-01-x-001
- scope: office
- evaluates: query hold-rate-by-class
- re-trigger: none

## W24 - Exchange adoption

- source: 2026-08-01-x-001
- scope: office
- evaluates: query unrelayed-rounds
- threshold: 4
- re-trigger: a fourth

## W25 - Somebody should look

- source: notepad/2026-09-01-sitting.md
- scope: office
- evaluates: eye
- re-trigger: when noticed

## W26 - Closed long ago

- source: 2026-08-01-x-001
- scope: office
- evaluates: query unparsed-share
- threshold: any
- re-trigger: none needed

## W27 - Misspelled

- source: 2026-08-01-x-001
- scope: office
- evaluates: query no-such-query
- threshold: 1
- re-trigger: x
"""

LOG_PAGE = """
- 2026-10-01 W13 opened: by a sitting
- 2026-09-01 W25 opened: by a sitting
- 2026-08-31 W26 closed: ruling 2026-08-31-x
"""


class TestRegisterAndLog(unittest.TestCase):
    def test_entries_fields_and_problems(self):
        lines = (od.render_page("watches.md") + REGISTER_PAGE + "\n## Not a watch\n").splitlines()
        entries, problems = ow.register(lines)
        self.assertEqual([e["number"] for e in entries], [1, 13, 15, 17, 22, 24, 25, 26, 27])
        self.assertEqual(entries[1]["fields"]["evaluates"], "query unused-forecast-entries")
        self.assertEqual(len(problems), 1)
        self.assertIn("a heading that is not a watch: ## Not a watch", problems[0])
        # The template's fenced example is never a watch.
        self.assertEqual(ow.register(od.render_page("watches.md").splitlines()), ([], []))

    def test_events_and_state(self):
        lines = (od.render_page("watch-log.md") + LOG_PAGE + "- 2026-10-02 W13 fired: x\n- 2026-10-03 W13 re-armed: same\n"
                 "- 2026-10-04 W13 burned: no such verb\n").splitlines()
        evs, problems = ow.events(lines)
        self.assertEqual([e[2] for e in evs], ["opened", "opened", "closed", "fired", "re-armed"])
        self.assertEqual(len(problems), 1)
        self.assertIn("burned", problems[0])
        st = ow.state_of(13, evs)
        self.assertEqual((st["closed"], st["opened"], st["fired"], st["last"][2]), (False, "2026-10-01", "2026-10-02",
                                                                                  "re-armed"))
        self.assertTrue(ow.state_of(26, evs)["closed"])
        self.assertEqual(ow.window(st), ("2026-10-03", "since 2026-10-03, the day after it last fired"))
        self.assertEqual(ow.window(ow.state_of(25, evs))[0], "2026-09-01")
        self.assertIsNone(ow.window(ow.state_of(99, evs))[0])

    def test_fields_read(self):
        e = lambda **f: {"fields": f}  # noqa: E731
        self.assertEqual(ow.evaluates(e(evaluates="eye")), ("eye", None))
        self.assertEqual(ow.evaluates(e(evaluates="query unparsed-share")), ("query", "unparsed-share"))
        self.assertIsNone(ow.evaluates(e(evaluates="run bale stats"))[0])
        self.assertIsNone(ow.evaluates(e())[0])
        self.assertEqual(ow.threshold(e(threshold="any non-zero share")), ("any", None))
        self.assertEqual(ow.threshold(e(threshold="3 accruals")), (3.0, None))
        self.assertIsNone(ow.threshold(e(threshold="a third"))[0])
        self.assertTrue(ow.standing_entry(e(**{"re-trigger": "none"})))
        self.assertFalse(ow.standing_entry(e(**{"re-trigger": "none needed"})))

    def test_a_sittings_pages_are_one_sitting(self):
        self.assertEqual(ow.sitting_key("notepad/2026-10-03-plan-4b-sitting-001-3.md"), "2026-10-03-plan-4b-sitting-001")
        self.assertEqual(ow.sitting_key("notepad/2026-10-03-plan-4b-sitting-001.md"), "2026-10-03-plan-4b-sitting-001")
        self.assertEqual(ow.sitting_key("notepad/2026-09-30-founding.md"), "2026-09-30-founding")
        utc = dt.timezone.utc
        f = lambda when, page: (dt.datetime.fromisoformat(when), page, "c", "s", ow.sitting_key(page))  # noqa: E731
        filings = [f("2026-10-04T00:47:21+00:00", "notepad/2026-10-03-plan-4b-sitting-001.md"),
                   f("2026-10-05T00:08:45+00:00", "notepad/2026-10-03-plan-4b-sitting-001-2.md"),
                   f("2026-10-06T19:06:27+00:00", "notepad/2026-10-06-other-sitting-001.md")]
        self.assertEqual(ow.sittings_after(filings, "2026-10-03", utc), 2)
        self.assertEqual(ow.sittings_after(filings, "2026-10-05", utc), 1)
        # 2026-10-05T00:08Z is still the 4th four hours west of UTC (the
        # office's zone in summer; a fixed offset, so no tz database is read).
        self.assertEqual(ow.sittings_after(filings[1:2], "2026-10-04", dt.timezone(dt.timedelta(hours=-4))), 0)

    def test_the_fired_record_is_one_ascii_line_per_watch(self):
        recs = ow.fired_records("2026-10-06", {13: [("office-src", "4 (x: 4, since 2026-10-01)")],
                                               1: [("ironwood", "a, b (s: 0.07)"), ("bale-src", "c (s: 0.08)")]})
        self.assertEqual(recs, ["- 2026-10-06 W1 fired: ironwood: a, b (s: 0.07); bale-src: c (s: 0.08); "
                                "recorded by office watches check --record",
                                "- 2026-10-06 W13 fired: office-src: 4 (x: 4, since 2026-10-01); recorded by office "
                                "watches check --record"])
        for r in recs:
            self.assertRegex(r, ow.LOG_RE)
            self.assertTrue(r.isascii())


# --- the verbs, in an office ------------------------------------------------------------------

def git_at(env, root, when, *args):
    """git with its clock set, for a commit dated when."""
    e = dict(env, GIT_COMMITTER_DATE=when, GIT_AUTHOR_DATE=when)
    return subprocess.run(["git", "-C", str(root), *args], env=e, capture_output=True, text=True, check=True).stdout


def project_repo(tmp, name, env):
    root = pathlib.Path(tmp) / "projects" / name
    root.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(root)], check=True, env=env)
    (root / ".bale").mkdir()
    (root / ".gitignore").write_text(".bale/\n")
    (root / "README.md").write_text("x\n")
    git_at(env, root, "2026-09-24T01:43:47+00:00", "add", "-A")
    git_at(env, root, "2026-09-24T01:43:47+00:00", "commit", "-qm", "the start")
    return root


class WatchCase(unittest.TestCase):
    """A founded office whose projects replay the probe's captures."""

    projects = ("office-src", "ironwood", "bale-src")
    registry = None

    def setUp(self):
        self.o = Office(self)
        self.e = self.o.e
        self.root = self.o.root
        routes = {}
        self.proj = {}
        for name in self.projects:
            p = project_repo(self.e.tmp, name, self.e.env)
            self.proj[name] = p
            routes[str(p)] = f"watches/{name}"
            self.o.run("projects", "add", name, str(p))
        if self.registry:
            (self.root / ".bale").mkdir(exist_ok=True)
            routes[str(self.root)] = self.registry
        self.fake = FakeBale(self.e.tmp, routes)
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])

    def pages(self, register=REGISTER_PAGE, log=LOG_PAGE, sid="2026-10-05-sitting-office-001"):
        d = self.root / DT
        d.mkdir(exist_ok=True)
        (d / "watches.md").write_text(od.render_page("watches.md") + register)
        (d / "watch-log.md").write_text(od.render_page("watch-log.md") + log)
        self.o.run("rider", "add", "arrive", "--source", "test")  # the table arrives through a verb
        self.e.git(self.root, "add", "-A")
        self.e.git(self.root, "commit", "-qm", f"[bale {sid}] a sitting's watches")

    def check(self, *args, code=0):
        return self.o.run("watches", "check", *args, check=code)


class TestWatchesVerb(WatchCase):
    def test_no_register_says_so_and_still_shows_the_standing_lines(self):
        listed = self.o.run("watches")
        self.assertIn("no watches register in this office yet", listed.stdout)
        out = self.check().stdout
        self.assertIn("no watches register in this office yet: only a sitting writes watches", out)
        self.assertIn("hold-rate-by-class in ironwood: observed: code 0.15 (6 of 39)", out)
        self.assertIn("claim-basis-split in office-src: observed: code: observed 23 of 24 agree", out)
        self.assertFalse((self.root / DT).exists(), "a read brought the drafting table")
        self.o.clean()

    def test_the_check_line_by_line(self):
        self.pages()
        out = self.check(code=3).stdout.splitlines()
        whole = "over bale's whole corpus (the log holds no opened or fired record for it)"
        want = [
            f"W1 unparsed-share in bale-src: fired: 0.08 (22 of 284) {whole}; threshold any",
            f"W1 unparsed-share in ironwood: fired: 0.07 (4 of 55) {whole}; threshold any",
            f"W1 unparsed-share in office-src: not fired: 0.00 (0 of 12) {whole}; threshold any",
            "W13 unused-forecast-entries in office-src: fired: 4 since 2026-10-01, when it was opened; threshold 3",
            "W15 hold-cause-cluster: cannot evaluate: bale does not stamp a HOLD cause class (slip)",
            "W17 stamp-mismatch-accepts: cannot evaluate: bale does not stamp a marker telling a deliberate "
            "checkpoint-amendment accept from an override (slip)",
            f"W24 unrelayed-rounds in bale-src: fired: 9 {whole}; threshold 4",
            f"W24 unrelayed-rounds in office-src: not fired: 0 {whole}; threshold 4",
            "W25 Somebody should look: needs an eye: 0 sitting(s) since its last record, 2026-09-01 opened",
            "W27 no-such-query: cannot evaluate: share/watch-queries.toml holds no query no-such-query",
            "W22 hold-rate-by-class in office-src: observed: code 0.33 (1 of 3); mixed 0.00 (0 of 9)",
            "W22 hold-rate-by-class in ironwood: observed: code 0.15 (6 of 39); doc 0.00 (0 of 10); meta - (0 of 0); "
            "mixed 0.00 (0 of 8)",
            "claim-basis-split in ironwood: observed: code: observed 201 of 211 agree, predicted 18 of 21 agree, "
            "unspecified 0 of 10 agree; doc: observed 93 of 94 agree; meta: no checks; mixed: observed 22 of 22 "
            "agree, unspecified 0 of 1 agree",
        ]
        # W22 observes the catalog's hold-rate-by-class: printed once, as W22.
        self.assertFalse([l for l in out if l.startswith("hold-rate-by-class in ")])
        for w in want:
            self.assertIn(w, out)
        # ironwood and bale-src were captured whole only: a window bale's
        # captures do not hold is said, never guessed, and exits 3.
        self.assertTrue(any(l.startswith("W13 unused-forecast-entries in ironwood: cannot evaluate: bale stats --json "
                                         "--since 2026-10-01 refused") for l in out), out)
        self.assertNotIn("W26", "\n".join(out), "a closed watch is not checked")
        for l in out:
            self.assertTrue(any(f": {v}" in l for v in ow.VERDICTS), l)
        # The watches come before the standing lines.
        self.assertLess(max(i for i, l in enumerate(out) if ": observed" not in l),
                        min(i for i, l in enumerate(out) if ": observed" in l))
        self.o.clean()  # a check without --record writes nothing

    def test_record_appends_one_fired_record_per_watch_and_commits_the_log_alone(self):
        self.pages()
        before = (self.root / DT / "watch-log.md").read_bytes()
        proc = self.check("--record", code=3)
        after = (self.root / DT / "watch-log.md").read_bytes()
        self.assertTrue(after.startswith(before), "the log grew other than at its end")
        new = after[len(before):].decode().splitlines()
        self.assertEqual([re.match(r"^- \S+ (W\d+) fired: ", l).group(1) for l in new], ["W1", "W13", "W24"])
        self.assertIn("bale-src: 2026-07-14-packaging-lists-v2-004", new[0])
        self.assertIn("; ironwood: 2026-09-19-foundation-docs-003, 2026-09-19-vendor-pokeemerald-004", new[0])
        self.assertIn("office-src: 4 (forecast entries an applied session's changes never touched: 4, since "
                      "2026-10-01, when it was opened)", new[1])
        self.assertIn("bale-src: 2026-07-15-status-staging-row-003", new[2])
        self.assertEqual(self.e.git(self.root, "log", "-1", "--format=%s"),
                         "office watches check --record: fired records on the watch log\n")
        self.assertEqual(self.e.git(self.root, "show", "--name-only", "--format=", "HEAD").split(),
                         [f"{DT}/watch-log.md"])
        self.o.clean()
        status = self.o.run("status", check=None).stdout
        self.assertNotIn("did more than append", status)
        self.assertIn("3 fired record(s) appended", proc.stderr)
        # Every citation a fired record makes resolves (the watch it names).
        checked = self.o.run("rulings", "--check", check=None).stdout
        n = len(before.decode().splitlines())
        for line in range(n + 1, n + 4):
            self.assertNotIn(f"watch-log.md:{line}:", checked)

    def test_a_watch_that_fired_looks_from_the_day_after(self):
        self.pages(register=REGISTER_PAGE.split("## W15")[0],
                   log="- 2026-10-01 W13 opened: x\n- 2026-10-06 W13 fired: office-src: 4\n")
        out = self.check("--record", code=3)
        self.assertIn("W13 unused-forecast-entries in office-src: not fired: 0 since 2026-10-07, the day after it "
                      "last fired; threshold 3", out.stdout)
        # ironwood and bale-src were captured whole only: said, never guessed.
        self.assertIn("W13 unused-forecast-entries in ironwood: cannot evaluate: bale stats --json --since 2026-10-07 "
                      "refused", out.stdout)
        self.assertNotIn("W13 fired", (self.root / DT / "watch-log.md").read_text().split("2026-10-06 W13 fired")[1])

    def test_nothing_fired_records_nothing(self):
        self.pages(register=REGISTER_PAGE.split("## W13")[0].replace("query unparsed-share", "query unparsed-share"),
                   log="- 2026-10-07 W1 opened: x\n")
        proc = self.o.run("watches", "check", "--record", check=3)
        self.assertIn("no watch fired, so nothing was recorded", proc.stderr)
        self.assertEqual(self.e.git(self.root, "log", "-1", "--format=%s").strip(),
                         "[bale 2026-10-05-sitting-office-001] a sitting's watches")

    def test_an_eye_watch_counts_the_sittings_since_its_last_record(self):
        self.pages(register=REGISTER_PAGE.split("## W26")[0].split("## W25")[1].join(["## W25", ""]),
                   log="- 2026-09-01 W25 opened: x\n")
        np = self.root / "notepad"
        for when, page in (("2026-09-10T12:00:00+00:00", "2026-09-10-plan-a-001.md"),
                           ("2026-09-11T12:00:00+00:00", "2026-09-10-plan-a-001-2.md"),
                           ("2026-09-20T12:00:00+00:00", "2026-09-20-plan-b-001.md"),
                           ("2026-09-25T12:00:00+00:00", "2026-09-25.md"),
                           ("2026-09-30T12:00:00+00:00", "2026-09-30-plan-c-001.md")):
            (np / page).write_text("words\n")
            git_at(self.e.env, self.root, when, "add", "--", f"notepad/{page}")
            git_at(self.e.env, self.root, when, "commit", "-qm", f"office start: the sitting's words from x's brief")
        out = self.check().stdout
        self.assertIn("W25 Somebody should look: needs an eye: 3 sitting(s) since its last record, 2026-09-01 opened; "
                      "unlooked-at for 3 sittings, so the digest flags it", out)

    def test_listing_open_and_all(self):
        self.pages()
        out = self.o.run("watches").stdout
        self.assertIn("Watches: 8 open, 1 closed (office watches --all lists the closed ones too)", out)
        self.assertIn("  W13  Forecast precision  [open]", out)
        self.assertIn("evaluates query unused-forecast-entries, threshold 3; scope office", out)
        self.assertIn("last record: 2026-10-01 opened: by a sitting", out)
        self.assertIn("query hold-cause-cluster (bale does not stamp a HOLD cause class yet)", out)
        self.assertIn("no re-trigger: a standing line", out)
        self.assertNotIn("W26", out)
        self.assertIn("  W26  Closed long ago  [closed]", self.o.run("watches", "--all").stdout)

    def test_a_record_that_does_not_read_is_named_and_exits_3(self):
        self.pages(log=LOG_PAGE + "- 2026-10-02 W99 fired: nobody\n- someday W1 fired: x\n")
        out = self.o.run("watches", check=3).stdout
        self.assertIn("does not read", out)
        checked = self.check(code=3).stdout
        self.assertIn(f"does not read: {DT}/watch-log.md:", checked)
        self.assertIn("W99 is on no entry", checked)

    def test_record_waits_for_an_open_session_holding_the_log(self):
        self.pages()
        reg = office_status_fixture(self.e.tmp, ["2026-10-06-sitting-x-001"], {"2026-10-06-sitting-x-001": [DT]})
        (self.root / ".bale").mkdir(exist_ok=True)
        routes = {str(p): f"watches/{n}" for n, p in self.proj.items()}
        routes[str(self.root)] = str(reg)
        self.e.env["PATH"] = FakeBale(self.e.tmp, routes).path(self.e.env["PATH"].split(os.pathsep, 1)[1])
        proc = self.o.run("watches", "check", "--record", check=1)
        self.assertIn("2026-10-06-sitting-x-001 holds drafting-table/watch-log.md", proc.stderr)
        self.assertIn("the one-writer rule", proc.stderr)
        self.o.clean()
        # A check that records nothing is never held.
        self.assertIn("W13 unused-forecast-entries", self.o.run("watches", "check", check=3).stdout)

    def test_help(self):
        for words in (("watches", "--help"), ("help", "watches"), ("help", "watches", "check"),
                      ("help", "watches-check"), ("watches", "check", "--help"), ("digest", "--help")):
            proc = self.e.run(*words, check=0)
            self.assertIn("Examples:", proc.stdout, words)
        self.assertIn("office watches check --record", self.e.run("help", "watches-check", check=0).stdout)
        self.assertIn("office watches check", self.e.run("help", "--all", check=0).stdout)
        self.assertIn("office digest", self.e.run("help", "--all", check=0).stdout)
        self.assertIn("does not know --loud", self.o.run("watches", "check", "--loud", check=1).stderr)


class TestRegistryWatches(WatchCase):
    """The office's own registry is read beside the projects'."""

    projects = ("office-src",)
    registry = "watches/home-office"

    def test_this_office_is_a_place(self):
        out = self.check().stdout
        self.assertIn("hold-rate-by-class in this office: observed: doc 0.00 (0 of 1); meta - (0 of 0); "
                      "mixed 0.00 (0 of 1)", out)
        self.assertLess(out.index("in this office"), out.index("in office-src"))


# --- the digest -------------------------------------------------------------------------------

class DigestCase(WatchCase):
    projects = ("office-src",)
    registry = "watches/home-office"

    def setUp(self):
        super().setUp()
        p = self.proj["office-src"]
        (p / "VERSION").write_text("0.9.0\n")
        git_at(self.e.env, p, "2026-10-04T02:48:30+00:00", "add", "-A")
        git_at(self.e.env, p, "2026-10-04T02:48:30+00:00", "commit", "-qm",
               "[bale 2026-10-04-friction-second-trip-001] office-src 0.9.0")

    def sitting_page(self, when="2026-10-05T00:08:45+00:00", page=f"notepad/{SITTING}-2.md"):
        (self.root / page).write_text("the sitting's words\n")
        git_at(self.e.env, self.root, when, "add", "--", page)
        git_at(self.e.env, self.root, when, "commit", "-qm", "office start: the sitting's words from x's brief")

    def land(self):
        """What bale left in the project's git when 4b-1 landed."""
        p = self.proj["office-src"]
        (p / "VERSION").write_text("0.10.0\n")
        for when, args in (("2026-10-06T16:37:02+00:00", ["commit", "-qam", f"[bale {HELD_THEN_APPLIED}] 0.10.0"]),
                           ("2026-10-06T16:37:24+00:00", ["commit", "-q", "--allow-empty", "-m",
                                                          f"Merge bale {HELD_THEN_APPLIED}"]),
                           ("2026-10-06T16:37:24+00:00", ["commit", "-q", "--allow-empty", "-m",
                                                          f"[bale sweep {HELD_THEN_APPLIED}] applied"])):
            git_at(self.e.env, p, when, *args)

    def digest(self, code=0):
        return self.o.run("digest", check=code)

    def section(self, text, name):
        return text.split(f"## {name}\n", 1)[1].split("\n## ", 1)[0]


class TestDigest(DigestCase):
    def test_the_seven_sections_in_order_and_the_page_committed_alone(self):
        self.sitting_page()
        self.land()
        proc = self.digest()
        page = (self.root / DT / "digest.md").read_text()
        self.assertEqual(proc.stdout, page)
        heads = re.findall(r"^## (.+)$", page, re.M)
        self.assertEqual(heads, ["Versions", "Since the last sitting", "Watches", "Standing lines", "The desk",
                                 "The agenda", "Open blueprints"])
        self.assertIn("Never edit by hand", page)
        self.assertTrue(page.isascii())
        # The first digest brings the drafting table, in the same commit.
        shown = self.e.git(self.root, "show", "--name-only", "--format=%s", "HEAD").split("\n")
        self.assertEqual(shown[0], "office digest: the sitting-open page")
        self.assertEqual(sorted(x for x in shown[1:] if x), ["bale.toml", f"{DT}/README.md", f"{DT}/digest.md",
                                                              "floor-plan/manifest.toml"])
        self.o.clean()
        status = self.o.run("status", check=None).stdout
        self.assertIn("drafting:   matches the install's catalog", status)

    def test_versions(self):
        self.land()
        v = self.section(self.digest().stdout, "Versions")
        self.assertIn("- bale: 0.4.45 installed (the read side's floor is bale 0.4.45)", v)
        self.assertIn(f"- office-src: release 0.10.0 (VERSION) landed by {HELD_THEN_APPLIED} on 2026-10-06; the "
                      "latest sessions were packed under bale's contract docs 4f31157aa0ed, since 2026-10-05 "
                      "(1 session(s); 3 epoch(s) in all); 1 session(s) not stamped yet", v)
        self.assertIn("not on bale's dossier (a slip for bale-src)", v)

    def test_since_the_last_sitting(self):
        self.sitting_page()
        self.land()
        self.o.open("after-the-sitting")
        self.o.run("rider", "add", "a rider since", "--source", "test")
        s = self.section(self.digest().stdout, "Since the last sitting")
        self.assertIn(f"The window: since 2026-10-05T00:08:45+00:00, when notepad/{SITTING}-2.md was filed by commit",
                      s)
        self.assertIn("the latest sitting's page in the notepad, by the commit that filed it", s)
        self.assertIn(f"- office-src: applied {HELD_THEN_APPLIED}; held {HELD_THEN_APPLIED}; still open {OPEN_HERE}",
                      s)
        self.assertNotIn("2026-10-04-friction-second-trip-001", s, "landed before the window")
        self.assertIn(f"- this office: nothing landed, held, bailed or closed; still open {SITTING} (read-only)", s)
        self.assertRegex(s, r"- folders: opened folder 1 \(\d{4}-\d{2}-\d{2}-after-the-sitting\), queued")
        self.assertIn("riders: 1 (rider 1)", s)

    def test_a_later_sitting_page_moves_the_window(self):
        self.sitting_page()
        self.land()
        self.sitting_page(when="2026-10-06T19:06:27+00:00", page=f"notepad/{SITTING}-3.md")
        s = self.section(self.digest().stdout, "Since the last sitting")
        self.assertIn(f"notepad/{SITTING}-3.md was filed", s)
        self.assertIn(f"- office-src: nothing landed, held, bailed or closed; still open {OPEN_HERE}", s)

    def test_no_sitting_page_counts_from_the_first_commit(self):
        s = self.section(self.digest().stdout, "Since the last sitting")
        self.assertIn("the office's first commit: no sitting's page (notepad/DATE-SLUG.md) is filed", s)

    def test_watches_standing_desk_agenda_blueprints(self):
        self.pages(register=REGISTER_PAGE.split("## W24")[0], log="- 2026-10-01 W13 opened: by a sitting\n")
        self.o.run("agenda", "add", "Which window?", "--source", "test")
        self.o.run("blueprint", "open", "watch-arc", "--title", "An arc")
        self.o.open("ready-one", "--size", "small")
        # home-office was captured with no 2026-10-01 window: W13 cannot be
        # evaluated in this office, the page says so, and the digest exits 3.
        page = self.digest(code=3).stdout
        w = self.section(page, "Watches")
        self.assertIn("- W13 unused-forecast-entries in this office: cannot evaluate: bale stats --json --since "
                      "2026-10-01 refused", w)
        self.assertIn("- W15 hold-cause-cluster: cannot evaluate: bale does not stamp a HOLD cause class (slip)", w)
        self.assertIn("- W13 unused-forecast-entries in office-src: fired: 4 since 2026-10-01", w)
        st = self.section(page, "Standing lines")
        self.assertIn("- W22 hold-rate-by-class in this office: observed:", st)
        self.assertIn("- claim-basis-split in office-src: observed: code: observed 23 of 24 agree", st)
        d = self.section(page, "The desk")
        self.assertIn(f"this office: {SITTING} read-only", d)
        self.assertRegex(d, r"Ready \(1; the first 5 in the desk's order\):\n- folder 1  \S+-ready-one")
        self.assertIn("- agenda 1 - Which window? (source test)", self.section(page, "The agenda"))
        self.assertRegex(self.section(page, "Open blueprints"),
                         r"- blueprint \d{4}-\d{2}-\d{2}-watch-arc: An arc \(not ratified\); members: none yet")
        # Running it again overwrites the page; it never records a firing.
        before = self.e.git(self.root, "rev-list", "--count", "HEAD")
        self.digest(code=3)
        self.assertNotIn("fired", (self.root / DT / "watch-log.md").read_text().split("```")[-1])
        self.assertEqual(int(self.e.git(self.root, "rev-list", "--count", "HEAD")), int(before) + 1)

    def test_an_unreadable_project_is_said_on_the_page_and_exits_3(self):
        shutil.rmtree(self.proj["office-src"])
        proc = self.digest(code=3)
        self.assertIn("- office-src: cannot read: no such directory on this machine", proc.stdout)
        self.assertTrue((self.root / DT / "digest.md").is_file())


class TestDigestBeforeASitting(unittest.TestCase):
    """office start runs the digest before it packs a read-only office
    session, and the drafting table rides inside the request."""

    def setUp(self):
        self.o = Office(self)
        self.e = self.o.e
        self.root = self.o.root
        self.fake = FakePackBale(self.e.tmp)
        self.e.env["PATH"] = self.fake.path(self.e.env["PATH"])
        self.trays = self.e.home / "out-tray"
        self.folder = self.o.open("plan-wave", "--size", "small")

    def start(self, *args, check=0):
        return self.o.run("start", self.folder.split("/", 1)[1], *args, check=check)

    def request(self, out):
        sid = re.search(r"^Packed (\S+) for ", out, re.M).group(1)
        return sid, next(self.trays.glob(f"{sid}/request-*.tar.gz"))

    def test_a_sitting_opens_on_the_digest(self):
        proc = self.start("--in-office", "--read-only", "--goal", "Plan the next wave")
        sid, req = self.request(proc.stdout)
        names = tar_names(req)
        self.assertIn(f"request-001/context/{DT}/digest.md", names)
        self.assertIn(f"request-001/context/{DT}/README.md", names)
        self.assertIn("(the drafting table rides inside the request", proc.stdout)
        subjects = self.e.git(self.root, "log", "--format=%s").splitlines()
        self.assertIn("office start: digest", subjects)
        self.assertLess(subjects.index(f"office sessions: {sid} in {self.folder.split('/', 1)[1]}"),
                        subjects.index("office start: digest"), "the digest is written before the pack")
        self.assertIn("wrote the digest for the sitting", proc.stderr)
        self.o.clean()

    def test_a_scoped_office_session_gets_no_digest(self):
        proc = self.start("--in-office", "--goal", "Write a page")
        _, req = self.request(proc.stdout)
        self.assertFalse(any(n.startswith(f"request-001/context/{DT}/") for n in tar_names(req)))
        self.assertFalse((self.root / DT).exists())
        self.assertNotIn("office start: digest", self.e.git(self.root, "log", "--format=%s"))

    def test_an_open_session_holding_the_table_leaves_the_digest_and_the_start_goes_on(self):
        self.o.run("rider", "add", "bring the table", "--source", "test")
        other = self.o.open("table-work")
        self.o.run("start", other.split("/", 1)[1], "--in-office", "--write", DT, "--goal", "Write the table", check=0)
        proc = self.start("--in-office", "--read-only", "--goal", "Plan")
        self.assertIn("an open session holds the drafting table (the one-writer rule), so office start leaves the "
                      "digest as it is", proc.stderr)
        self.assertFalse((self.root / DT / "digest.md").exists())
        _, req = self.request(proc.stdout)
        self.assertIn(f"request-001/context/{DT}/riders.md", tar_names(req))


# --- the doctrine and the pages ---------------------------------------------------------------

class TestDoctrineAndTemplates(unittest.TestCase):
    def test_the_doctrine_says_what_the_verbs_do(self):
        doctrine = " ".join((REPO / "doctrine/OFFICE.md").read_text().split())
        for words in ("an entry names a query and a threshold, never a command line",
                      "a query bale cannot answer says so, as cannot evaluate, never as not fired",
                      "re-arming, rewording, closing and a not-fired record are a sitting's",
                      "The last sitting is the latest sitting's page in the notepad, by the commit that filed it",
                      "Before it packs a sitting, `office start` writes the digest again",
                      "desk moves a sitting decided that have not run",
                      "its --since form, which takes a day and not an instant",
                      "a query reads only keys the manifest declares",
                      "bale keeps it as a habit and not as a contract"):
            self.assertIn(words, doctrine)
        moves = doctrine.index("desk moves a sitting decided that have not run")
        self.assertLess(doctrine.index("a session out (land it"), moves)
        self.assertLess(moves, doctrine.index("an unfounded office (start its founding folder"))

    def test_the_drafting_tables_front_page_says_what_the_digest_is(self):
        readme = " ".join(od.render_page("README.md").split())
        self.assertNotIn("does not exist yet", readme)
        self.assertIn("`office digest` rewrites it whole on every run", readme)
        self.assertIn("share/watch-queries.toml", od.render_page("watches.md"))
        self.assertIn("`office watches check --record` appends `fired` records", " ".join(
            od.render_page("watch-log.md").split()))

    def test_the_digest_is_a_derived_page_and_the_watch_log_filed(self):
        self.assertIn("digest.md", od.DERIVED_PAGES)
        filed = tomllib.loads((REPO / "share/spaces.toml").read_text())["spaces"][DT]["filed"]
        self.assertIn(f"{DT}/watch-log.md", filed)
        self.assertNotIn(f"{DT}/digest.md", filed)


# --- the Next line --------------------------------------------------------------------------

def groups(**kw):
    g = {"flying": [], "open": [], "ready": [], "parked": {}, "candidates": [], "no_status": [],
         "misplaced": [], "unreadable": [], "ready_errors": [], "cleared": {}, "moves": (0, "", [])}
    g.update(kw)
    return g


class TestNextLineMoves(unittest.TestCase):
    ready = {"name": "2026-10-05-x", "number": 1, "fields": {}, "rel": "desk/2026-10-05-x"}
    out = {"sid": "2026-10-05-x-001", "label": "alpha", "folders": ["desk/x"], "held": False, "created": ""}

    def test_pending_moves_come_after_a_session_out_and_before_unfounded(self):
        moves = groups(moves=(2, "2 from `2026-10-05-sitting-office-001`", []), ready=[self.ready])
        cmd, why = ob.next_move("current", True, [], moves, [{"name": "alpha"}], 0)
        self.assertEqual(cmd, "office moves")
        self.assertIn("2 desk move(s) a sitting decided are pending (2 from `2026-10-05-sitting-office-001`)", why)
        self.assertIn("until they run, the desk is not in the order the sitting decided", why)
        self.assertEqual(ob.next_move("current", True, [self.out], moves, [], 0)[0], "office land 2026-10-05-x-001")
        self.assertEqual(ob.next_move("current", False, [], moves, [], 0)[0], "office moves")
        self.assertEqual(ob.next_move("behind", True, [], moves, [], 0)[0], "office upgrade")
        self.assertEqual(ob.next_move("current", True, [], groups(ready=[self.ready]), [{"name": "alpha"}], 0)[0],
                         "office start 2026-10-05-x")

    def test_lines_that_do_not_read_name_moves_too(self):
        cmd, why = ob.next_move("current", True, [], groups(moves=(0, "", ["line 3: x"])), [], 0)
        self.assertEqual(cmd, "office moves")
        self.assertIn("1 line(s) of drafting-table/moves.md do not read", why)

    def test_the_walk_in_names_it(self):
        o = Office(self)
        o.e.env["PATH"] = FakeBale(o.e.tmp, {}).path(o.e.env["PATH"])
        o.open("first", "--size", "small")
        page = o.root / DT / "moves.md"
        o.run("rider", "add", "arrive", "--source", "test")
        page.write_text(od.render_page("moves.md") + "\n- [ ] 2026-10-05 close folder 1\n")
        o.e.git(o.root, "add", "-A")
        o.e.git(o.root, "commit", "-qm", "[bale 2026-10-05-sitting-office-001] moves")
        walk = o.run().stdout.strip().splitlines()[-1]
        self.assertTrue(walk.startswith("Next: office moves  (1 desk move(s) a sitting decided are pending "
                                        "(1 from `2026-10-05-sitting-office-001`)"), walk)


if __name__ == "__main__":
    unittest.main()
