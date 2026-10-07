# bale 0.4.47, as the third-trip probe found it

Captured by the probe of session 2026-10-07-third-trip-001 on the machine
office-src is built on (WSL2, bale 0.4.47), on 2026-10-07. The brief
expected 0.4.46; the request was packed by 0.4.47, and that is what the
probe found installed. Every call that packed, opened, applied or
unlocked ran in a throwaway repo under one temp directory the probe made
and removed (`/tmp/office-probe.XXXXXX`, printed as `TMP`, and kept here
as it printed it), each with a bale.toml naming a scratch directory
(`TMP/dl`) as its `apply.search_paths`. In office-src and home-office it
ran only `bale status --json` and `bale stats ... --json`. bale's
install `user/` directory listed the same before and after.

## What moved, against the 0.4.45 captures

Nothing the office reads. The probe ran every read surface the
consumption manifest declares (status, stats, stats --work-class,
stats --since, both together, a dossier, a miss, the refusal of --since
beside --sid) in office-src and home-office, and pack --json, pack
--context --json, open, apply, the dossier after it and unlock --json in
throwaway repos, and resolved every declared key in each line: every
one is there (the only keys not reached are parse_failure and
filtered_record_version on a found dossier, which bale prints on a miss
alone, and keys under an empty map or list). The opener's scissor lines
(pack: stderr, open: stdout), open's `  tarball:        ` line, apply's
relay markers and the commit subjects (`[bale SID] `, `Merge bale SID`,
`[bale sweep SID] `) are as they were. What 0.4.47 added, all additive:

- `status --json`: a `clipboard` object (command, key, problem,
  shadowed, source).
- the dossier: no new key. The probe's diff named paths the 0.4.45
  captures lack, but each is a value those records held as null (the
  bundle stamps of a session a bundle opened, the validation and closure
  of a session applied since it was captured open).
- `unlock --json`: `message`, `open_sessions`, `reason` on success; and
  on a refusal (exit 1, the error on stderr as before) one JSON line on
  stdout, `outcome: unlock-refused` with a `reason` code
  (unlock/unlock-again.json). The office reads an unlock refusal by its
  exit code and stderr, so nothing changes for it.
- a `clipboard` verb.

One difference is not a key: `stats --json --work-class meta` in
office-src reported no class at all (0.4.45: `meta`, one session),
though office-src's records include meta sessions. The office never
asks the aggregate for one work class, so it reads nothing different;
whether bale now counts meta's read-only sittings elsewhere, the probe
did not show (a question in the notes for bale-src).

So the 0.4.45 captures stay the suite's floor and its fake bales replay
them; these files add only what the office now calls that 0.4.45's
captures do not hold.

## The files

Each JSON file is one bale invocation in the land set's shape: argv,
cwd, stdin, exit code, stdout lines exactly as printed with each line's
sha256, the stderr lines, and where it was captured. The paste came
through a console that showed UTF-8 as CP437 (`ΓÇö` for `—`, `┬º` for
`§`); those characters were restored before the sha256 of each line was
computed on this side. The probe printed no hashes.

- open-check/: `bale open --check` (and once `--dry-run`), the surface
  office start runs before it writes anything (consumption manifest
  `[surfaces.open_check]`), with stdin closed:
  - check-missing: a bare name bale's search cannot find. Exit 1; the
    refusal and every directory searched on stderr; nothing on stdout.
  - check-found, check-absolute: a bare name found in the search
    directory, and the same bundle by its absolute path. Exit 0; the
    rehearsal report on stdout, its first line naming the path bale
    found, its `wrote:` line saying nothing.
  - check-nopath: a bundle forecasting a path that does not exist.
    Exit 1, the forecast-existence gate's words on stderr.
  - check-overlap: a bundle whose forecast overlaps an open session.
    Exit 1, the disjointness gate's words on stderr.
  - check-ro: a read-only bundle. Exit 0.
  - dryrun-found: `--dry-run` of the found bundle (no checkpoint, so the
    dry-run leg is skipped). Exit 0.
  - check-outside: `--check` run outside any repo. Exit 1: bale open
    runs inside the project repository.
  Before and after the checks the repo's git status, its `.bale/` file
  listing and its open sessions were the same.
- unlock/unlock-again.json: `bale unlock SID --json` of a session no
  longer open, 0.4.47's refusal shape (the sid printed as SID).
- anywhere/version.json: `bale --version`.

tests/test_third_trip.py reads these: the open_check surface's argv
and found line are checked against them, and the suite's fake bale
prints `bale open --check` from them. These files are never edited.
