# bale 0.4.45, as the read-side probe found it

Captured by the probe of session 2026-09-30-read-side-001 on the machine
office-src is built on, with bale 0.4.45 installed. Each JSON file is one
bale invocation: its argv, exit code, stdout lines exactly as printed,
stderr lines, the sha256 of each stdout line (as the probe printed it,
or computed from the pasted line where the probe printed none), and
where it was captured.

- office-src/: run in the office-src checkout: `status --json`,
  `stats --json` (whole corpus, and per work class), one dossier per
  session in claude/telemetry/ at the time, one honest miss
  (2026-01-01-no-such-session-001), and one refusal (`--since` beside
  `--sid`).
- test-office/: `status --json` in the machine's default office, idle.
- anywhere/: `bale --version`.

tests/test_read_side.py replays these through a fake bale on the PATH,
keyed by argv and the directory it runs in; the fake refuses anything
not captured here. They live in the development record, not in tests/,
because they name the machine and its paths, which office-src itself
never does. A new bale is probed into its own bale-VERSION/ directory;
these files are never edited.
