# bale 0.4.45 in home-office, as the drafting-table-pages probe found it

Captured by the probe of session 2026-10-05-drafting-table-pages-001 on
the machine office-src is built on (WSL2, bale 0.4.45), on 2026-10-05 at
00:26 UTC, in the machine's real office, home-office, with stdin closed.
Each JSON file is one bale invocation, in the land and unlock sets'
shape: argv, cwd, stdin, exit code, stdout lines exactly as printed with
each line's sha256 (printed by the probe and re-verified on the paste),
the stderr lines, and where it was captured. These are the first captures
of an office's own registry; the earlier sets ran in office-src, in an
idle test office, and in throwaway repos.

- status_json: `bale status --json`. One session open, the read-only
  sitting 2026-10-03-plan-4b-sitting-001, scope `[]`; two applied, the
  latest 2026-10-04-bale-src-slips-001 (stale in staging); `config.project`
  is the office's own bale.toml.
- stats_sid_2026-10-04-bale-src-slips-001_json: the slips session's
  dossier: applied, work class doc, forecast `desk/2026-10-03-continue-plan`
  and `suggestion-box`, sixteen change paths, validation PASS with six
  claims all agreeing, opened from a bundle.
- stats_sid_2026-10-03-plan-4b-sitting-001_json: the sitting's dossier:
  `in_flight: true`, outcome opened, scope `[]`, opened from a bundle. Its
  record says `read_only: false` although its scope is empty; the office
  reads read-only from the scope, as land's unlock captures found bale
  itself does.

What git showed beside them (the probe's other sections, not bale's
output): bale commits a session's work as `[bale SID] summary`, merges it
as `Merge bale SID` tagged `applied/SID`, and sweeps its telemetry as
`[bale sweep SID] applied` (or `closed-read-only`). office moves names the
session that wrote a pending desk move from the first of these.

tests/test_desk_verbs.py replays them: the office's registry as captured,
and, where a test needs a session open that no captured office had open,
this status line with only its sessions and scopes set to the test's.
These files are never edited.
