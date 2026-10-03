# bale 0.4.45 applying and opening, as the return-trip probe found it

Captured by the probe of session 2026-10-03-friction-return-trip-001 on
the machine office-src is built on (WSL2, bale 0.4.45), on 2026-10-03.
Every call ran in a throwaway repo the probe built under a temp
directory (`/tmp/office-probe.waUkTl`, since removed), each with a
bale.toml naming a scratch directory as its `apply.search_paths`, so no
real repo applied or opened anything and nothing under `~/bale/user`
changed. Each JSON file is one bale invocation, in the pack set's shape:
argv, cwd, stdin, exit code, stdout lines exactly as printed with each
line's sha256 (printed by the probe and re-verified on the paste), the
stderr lines, and where it was captured. A file whose stdin is a
pseudo-terminal also carries `events`: what the probe read and what it
sent, in order, channel by channel (`out`, `err`, the terminal's echo as
`tty`, and `sent`).

- help, help-apply, help-open, help-relay, help-retry, help-unlock: the
  help pages. `apply`, `retry` and `unlock` have `--json`; `open` and
  `relay` do not.
- apply-applied: a response that passes, stdin closed. The walkthrough
  merges by default, then bale prints the relay for the planner between
  `=== RELAY BEGIN <sid> to planner ===` and `=== RELAY END <sid> to
  planner ===`, on stdout.
- apply-appliedj: the same with `--json`: stdout is the one JSON line
  (no relay key), and everything else, the relay included, is on stderr.
- ptyapply-split, ptyapply-whole: the applied case with stdin on a
  pseudo-terminal, stdout piped (split) and on the terminal (whole). The
  walkthrough asks `[Enter/m] merge ... [r] revert` on stdout and reads
  the answer from stdin; piped stdout does not stop it asking.
- apply-hold: validation exits 1. Two relay blocks, the worker's first
  (`to worker`), then the planner's; the session stays open, held.
- pack-drift, apply-drift, apply-driftrestored, ptyapply-driftn,
  ptyapply-drifty: a folder recorded and committed after the pack, the
  way office start records a session, and a response that rewrites the
  folder from its pack-time bytes. bale refuses it as base drift
  (`base-drift-refused`), on a terminal too: there is no prompt, only a
  re-run line with `--accept-base-drift`. With the folder's pack-time
  bytes committed back before the apply (driftrestored), it lands with
  nothing asked.
- apply-outside, ptyapply-outside: a change outside the forecast. Piped,
  refused (`scope-drift-refused`); on a terminal bale asks `admit PATH?
  [y/N]` per path, decline by default.
- apply-clar, relay-clar: a clarification response. apply records the
  round and prints no relay; `bale relay SID` with no file re-emits the
  paste block for the planner on stdout, between `BALE EXCHANGE BEGIN
  <sid>` and `BALE EXCHANGE END`, and records nothing.
- apply-bare, apply-missing, apply-noarg: a bare `response-SID.tar.gz`
  resolved through the search path; a missing one (the refusal names
  every directory searched); and bare `bale apply`, which resolves the
  newest response answering an open session and then declines piped.
- dry-1: `bale pack --dry-run --json` is refused: a pack cannot name its
  session id before it runs.
- open-brief, ptyopen-split, open-ro-bare, open-missing,
  open-extra-flags: `bale open` of a synthetic bundle built with the
  request's `craft_response.py --bundle`, with a brief, read-only by bare
  file name, a missing name, and with extra pack flags (refused: open
  takes none). Its report, the opener between the scissor lines and
  the `tarball:` line, is all on stdout.
- dossier-*, status-*: the records after each case, through `bale stats
  --sid SID --json` and `bale status --json`.

tests/test_land.py reads these: the markers the office declares are
checked against them, the readers run over them verbatim, and the suite's
fake bale builds its output from them. These files are never edited.
