# bale 0.4.45 closing read-only sessions, as the second-trip probe found it

Captured by the probe of session 2026-10-04-friction-second-trip-001 on
the machine office-src is built on (WSL2, Ubuntu 24.04.2, bale 0.4.45),
on 2026-10-04 at about 01:18 UTC. Every call ran in a throwaway repo the
probe built under a temp directory (`/tmp/office-probe.DPIe0v`, since
removed): a git repo with `notes/a.md`, a `.gitignore` naming `.bale/`,
and a `bale.toml` holding only a comment. No real repo opened or closed
anything. Each JSON file is one bale invocation, in the land set's
shape: argv, cwd, stdin, exit code, stdout lines exactly as printed with
each line's sha256 (printed by the probe and re-verified on the paste),
the stderr lines, and where it was captured. The file whose stdin is a
pseudo-terminal also carries `events`, as in land/.

- pack-ro-*: `bale pack GOAL --slug SLUG --include notes --read-only
  --no-readme --json`, stdin closed: the read-only sessions the cases
  below close.
- status-ro-open: `bale status --json` with one read-only session open:
  its scope is `[]`.
- unlock-ro-json: `bale unlock SID --json`, stdin closed. Exit 0; stdout
  is one JSON line, outcome `unlocked`, `closure_reason`
  `closed-read-only` (inferred from the empty scope), and a `sweep` key:
  bale committed the session's telemetry record,
  `claude/telemetry/SID.json`, as one commit
  `[bale sweep SID] closed-read-only`, and nothing else. The human
  summary is on stderr.
- status-ro-unlocked, dossier-ro-unlocked: the records after it: nothing
  open; the dossier's record says `outcome: unlocked`, `in_flight:
  false`, `read_only: true`, `closure.unlock_reason: closed-read-only`,
  and an `unlock` attempt follows the `pack` one.
- unlock-ro-again: the same sid again. Exit 1, nothing on stdout, and
  `[bale] error: session SID is not open; nothing to unlock.` on stderr.
- unlock-ro-plain: without `--json`: the same lines, all on stdout.
- ptyunlock-ro-json: stdin and stderr a pseudo-terminal, stdout piped.
  bale asked nothing (the probe's one plain return was never sent); the
  JSON line went to stdout and the human lines to the terminal.
- unlock-ro-dirty: an edited tracked file and an untracked one beside
  the session. bale's sweep committed the telemetry record only; `git
  status` afterwards still showed ` M notes/a.md` and `?? notes/b.md`.
- unlock-ro-one-of-two, status-ro-one-left, unlock-ro-other: two
  read-only sessions open; unlocking one by sid leaves the other open.

What git showed after each unlock (the probe's notes, not bale's output):
a new HEAD `[bale sweep SID] closed-read-only` touching only
`claude/telemetry/SID.json` (72 lines added), and a clean tree except
for the occupant's own uncommitted work.

tests/test_land.py reads these: the unlock surface the office declares
is checked against them, and the suite's fake bale prints their lines
with the session id and the paths swapped in. These files are never
edited.
