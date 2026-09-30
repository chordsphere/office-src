# Notes: 2026-09-30-read-side-001, the read side (office-src 0.4.0)

The tree read VERSION 0.3.1, as the brief expected, and every function
the brief names by name (`cmd_sessions`, `record_session`, `walk_in`,
`sid_from_pack_report`, `render_manifest`) was where it said. One probe
ran before any building (pasted back whole: 1644 lines, trailer intact,
every JSON line's sha256 re-verified on this side). Everything below
about bale is what that probe showed on the installed bale 0.4.45, not
the desk's reading of bale-src.

## What the probe established

- **bale 0.4.45**, installed at ~/bale, on PATH as ~/.local/bin/bale. The
  three key contracts the brief named were read whole, as was
  `format_status_json`'s. They all say the same thing about stability:
  existing keys are never renamed or removed, and new keys may be added.
- **The dossier** (`bale stats --sid SID --json`) matches the brief's
  map, with one correction and a few additions. The correction:
  `attempts[].provenance` is `{work_class, packer, packed_at}`. It carries
  **no bale version**. The bale version lives in telemetry's
  `feedback.mechanical.provenance.bale_version`, and the dossier carries
  no `feedback` at all. The additions: `linkage`, `cause`,
  `required_check_overrides`, `base_drift_overrides` and
  `forecast_drift_paths` per attempt. `--since` beside `--sid` is refused
  (exit 1, `[bale] error: --sid renders one session's dossier and does
  not compose with --since ...`), as the brief said. An unknown sid is an
  honest miss: `found: false`, `parse_failure`, `filtered_record_version`
  and no other keys, exit 0.
- **The aggregate** (`bale stats --json [--work-class C]`) holds rates
  and counts per work class, and `members` lists only the sids behind
  the anomaly counts, plus the in-flight, read-only and crash-debris
  sids. **No surface lists every session in a repo.**
- **`bale pack --json`'s key is `sid`**, a stable key in the contract.
  `session_id` was never in it. So `sid_from_pack_report` now reads `sid`
  only, the id-shaped guess is gone, and a report without `sid` refuses
  and names the keys it saw. The front sheet's known problem is struck.
- **bale's help** says stats "takes no lock, writes nothing, never reads
  .bale/", and status "makes no git or filesystem changes". The reader
  calls only these two verbs.

## What `bale status --json` turned out to list

Every open session: `sessions` is the full list of open sids, oldest
first. Each sid's recorded forecast is in `scopes`, where `[]` marks a
read-only session, and its staging state is in `staging.sessions`.
`sid` is the single-open pointer, kept for old consumers, and is the
oldest open sid. The `session` object (lifecycle `state`, `goal`) covers
that one session only. So the in-flight list reads `sessions` and
`scopes`, and takes each session's state and age from its dossier
(`record.outcome`, `record.created_at`). `outbox`, every request tarball
name, is the fullest list of a repo's session ids any `--json` surface
carries, and the reader enumerates a project's sessions from it.

## The consumption manifest's version floor, and why

The floor is `floor = "0.4.45"`, with no ceiling. Every read was probed
on 0.4.45. bale's key contracts are additive, so any later bale serves
the same keys; an older one may not. A ceiling would have `office status`
calling every bale release out of range for no reason. The test that
catches a moved key is `test_every_declared_key_is_in_the_captured_lines`:
re-capture the fixtures from a new bale, and it names the key.
`office status` prints the installed bale against the floor as a line,
never as a refusal.

Every key access goes through `Reader.key`, which refuses any key the
manifest does not declare. The suite also walks the reader's source with
`ast` and holds the manifest to it in both directions: no key is read
without being declared, and none is declared without being read. Every
call's argv is built from the manifest too, so the reader cannot call a
surface the manifest doesn't name.

## Where the ledger, last-landed-by and version-trail renderings went

All three are flags on `office projects`: `--ledger`, `--landed PATH`,
`--versions`, each narrowable with a project name. They are per-project
readings, and `office sessions` is per-folder, so `projects` reads
naturally. The walk-in carries only the In flight list, one line per
open session, placed above On the desk.

## The four slips for bale-src (blueprint section 3.2), confirmed or corrected

1. **Unused forecast entries per applied session (watch 13): corrected,
   not missing.** The aggregate carries `forecast_entries`,
   `forecast_entries_untouched` and `forecast_precision` per work class,
   and the dossier has each attempt's forecast (`scope`) beside its
   applied paths (`change_paths`), so the per-session count is
   computable too. Nothing to file.
2. **A HOLD cause class (watch 15): confirmed missing.** Closest: the
   aggregate's `checkpoint_hold_attempts` and `checkpoint_catch_attempts`
   (the checkpoint objected while the worker's script passed), and a
   per-attempt `cause` key on the dossier (v0.4.41, "the record's value
   verbatim"). `cause` is null on every record here, and its meaning was
   not in the docstrings the probe read. The slip should ask bale-src
   whether `cause` is meant to carry the HOLD class. If it is, the slip
   shrinks to its vocabulary.
3. **A real round's self-report (watch 24): mostly corrected.** The
   aggregate carries `corpus.paste_carried_rounds_total`,
   `corpus.light_blocks_total`, `corpus.clarification_rounds_total`,
   `cross_checks.clarification.{self_reported_sessions, promoted_sessions,
   self_only, ...}` and `members.clarification_self_only`. The last is
   the list of sessions that self-reported a round with no promoted
   stamp, which looks like watch 24's condition exactly. What is still
   missing is the per-session count on the dossier: it carries
   `clarification.rounds` and `linkage {kind, point}`, but not the
   self-reported counts. The slip narrows to that.
4. **A marker telling a deliberate amendment accept from an override
   (watch 17): confirmed missing.** bale has the apply flag
   (`accept_checkpoint_change` appears in bale_apply.py's admissions),
   but no dossier key and no aggregate key reports that it was used.
   Since the flag already exists, the slip is to stamp it.

The probe also turned up three more, which the renderings name where
they show:

5. **The dossier leaves out the bale version per session.** A folder's
   sessions and the version trail print "not on bale's dossier (a slip
   for bale-src)" instead of scraping telemetry.
6. **No `--json` surface lists every session in a repo.** The office
   enumerates `status.outbox` plus the open sessions. An outbox someone
   prunes would hide sessions from the ledger. A `members.sessions` on
   the aggregate would fix it.
7. **`bale status --json` gives a lifecycle state for one open session
   only.** The in-flight list works around it through each session's
   dossier. It is a small slip.

These are the prose Proposals the brief asks for. Nothing was changed in
bale.

## Which of section 3.2's seven queries the aggregate answers today

| watch | query | today |
|---|---|---|
| 1 | `unparsed-share` | yes: `classes.*.unparsed_validated_attempts`, `unparsed_share`, with `--since` |
| 13 | `unused-forecast-entries` | yes: `classes.*.forecast_entries_untouched` over `forecast_entries` (and `forecast_precision`); per session from the dossier |
| 15 | `hold-cause-cluster` | no (slip 2) |
| 17 | `stamp-mismatch-accepts` | no (slip 4) |
| 21 | `claim-basis-split` | yes: `classes.*.claim_basis` `{observed, predicted, unspecified}` each `{checks, agree, agreement_rate}` |
| 22 | `hold-rate-by-class` | yes: `classes.*.held_attempts`, `hold_rate`; applied per class from `closure_mix.applied` under `--work-class` |
| 24 | `unrelayed-rounds` | probably: `cross_checks.clarification.self_only` and `members.clarification_self_only`; confirm on a corpus that has one |

So five of the seven are answerable today, one of them probably. The
probe did **not** capture a `--since` aggregate. Session 4's watch
catalog reads that form first, so its probe should capture one before
the catalog names it.

## What the personal office taught about `[projects]`

It is `~/test-office`: built by office-src 0.2.0, timezone `Etc/UTC`, a
`bale.toml` with the 0.2.0 include group, no `.bale/` (bale has never
run there), an empty desk, and idle under `bale status --json` (its line
is a fixture). It had no `[projects]` table to learn from, so the shape
is the brief's: one table keyed by project name, each entry
`path = "..."`, absolute or `~/`. I wrote the entries as
`[projects.NAME]` sub-tables, which leaves room for a `machine` key if
Q-2 is answered that way. Names are TOML bare keys (letters, digits,
`-`, `_`). The include group is untouched, because projects are other
repos and bale's include groups only pull paths inside the repo being
packed.

One thing to know: **the installed office-src on that machine is still
0.2.0** (`office version` printed it). Sessions 1 and 2 landed in the
repo but were never installed. Until `~/office-src/install.sh` runs,
none of 0.3.0, 0.3.1 or this release is what `office` runs.

## Decisions to ratify

- **The fixtures live in the development record, out of forecast.** The
  captured lines name the machine (`/home/<user>/...`, `packer`) and hold
  `claude/...` paths. The suite's text test forbids both anywhere under
  `tests/`, and the constraint says that test stays green. Scrubbing the
  lines would break "verbatim". Encoding them to dodge the grep would
  defeat the test's purpose. So they sit in
  `claude/fixtures/bale-0.4.45/`, pinned by sha256, and the suite reads
  them there, as it already reads `claude/context/sittings/`.
- **Em dashes.** Blueprint section 4's three doctrine lines are verbatim
  except that each em dash is spelled ` -- `, because OFFICE.md is
  office-bound text and must be ASCII. The section 10 lines sit after
  the settled bale/office paragraph, not inside it, because that
  paragraph is pinned verbatim by the suite. `[projects]` gets a clause
  in section 5's floor-plan sentence and a paragraph in section 10. It
  is not in section 12's Site section, which is profile prose, and one
  home per fact says the floor plan holds the paths.
- **The version trail** reads two ways, because I could not see the
  ledger register's "Version landmark" row. It shows the project's
  releases (applied sessions whose change set held a `VERSION` file at
  any depth, oldest first) and bale's contract-doc epochs (`doc_epochs`:
  which bale docs each run of sessions was packed under). The bale
  version per session would belong here, but it is slip 5. If the
  landmark meant something else, it is one function to change.
- **Records beside records.** The ledger shows bale's aggregate figures
  and, where it computes the same count from the dossiers, prints both
  when they part. First-attempt PASS is computed from the dossiers,
  because the aggregate has no such figure. The office had no written
  count to set beside a rendered one yet. `office sessions` prints "recorded in this
  folder: N; found in bale's records: M", which is the nearest case.
- **Exit codes.** Walking in never fails over the read side; it prints
  the reason in the In flight section. `office sessions FOLDER`,
  `office projects` and its renderings exit 1 when a project could not
  be read (bale missing, path missing), after printing every line they
  could. `office sessions FOLDER` in an office with no `[projects]`
  lists the ids, says why nothing more is rendered, and exits 0.
- **`python3 -B`.** The reader imports the helper, so `office` would
  have written `lib/__pycache__` into the install on every run. bin/office
  runs the reader with `-B`, and a test proves an install stays
  unwritten.

## Paths outside the write forecast

Each is declared in `feedback.self_reported.forecast_departures` too.

- `claude/fixtures/bale-0.4.45/README.md` and the 16 fixture files under
  `claude/fixtures/bale-0.4.45/` (`anywhere/version.json`,
  `test-office/status_json.json`, and 14 under `office-src/`: status,
  stats whole and per class, eight dossiers, the miss and the refusal).
  They are real bale output that names the machine, so they belong in
  the development record, not in `tests/` (see Decisions).
- `claude/INDEX.md`: one row, so the development record's map lists the
  fixtures directory and its lifecycle.

## The suite

175 tests, green twice in a row here. 52 of them are new, in
`tests/test_read_side.py`. The full suite takes about two minutes. The
read side's share is about 35s, after one world is built per class, and
the rest is the existing suite. validation.sh runs it whole, not behind
`--slow`, because it is the check that matters.

validation.sh was run both ways in a copy of the request's tree. With
the change applied, every check passed and all seven claims agree. On
the unmodified tree, the four checks that test this change (the doctrine
lines, the fixtures, the 0.4.0 release, the pack key) fail. The agnostic
grep and the no-bytecode check pass on both, by design: they guard the
brief's constraints rather than detect the change. The in-suite bytecode
test was checked failing with `-B` removed.

## Proposals

### Probe `bale stats --json --since DATE` before writing the watch catalog

- **What:** session 4's first step captures the `--since` aggregate (one
  window that includes an applied session, one that includes none) into
  `claude/fixtures/bale-0.4.45/office-src/`, then adds `optional` to the
  stats surface's argv in the consumption manifest.
- **Why:** blueprint section 3.2's catalog reads "`bale stats` and its
  `--since` form first". This probe captured `--since` only as a
  refusal beside `--sid`, so a watch query written today would grade a
  surface nobody has seen.
- **Scope hints:** share/bale-consumption.toml, the fixtures directory,
  tests/test_read_side.py's coverage test.

### File slips 2, 3, 4, 5 and 6 in bale-src's fold-in registry as one bundle

- **What:** the dossier gains the self-reported round counts and the
  bale version, the aggregate gains a full member list, and `cause` and
  the accept marker get their doctrine.
- **Why:** each one leaves a rendering or a watch printing "not on
  bale's dossier". They are all additive keys under bale's own stability
  rule.
- **Scope hints:** bale-src's `format_session_dossier_json` and
  `format_stats_json`. The office side is one manifest line and one
  rendering line per key once they land.

### Install what is built

- **What:** run `~/office-src/install.sh` on the machine once this
  lands. The install there is 0.2.0.
- **Why:** session 4's desk groups will read through this reader, and
  walking in on the installed 0.2.0 shows none of it.
