# bale 0.4.52, opening a bundle with --json, as the office-probe probe found it

Captured by the probe of session 2026-10-13-office-probe-002 on the
machine office-src is built on (WSL2, bale 0.4.52), on 2026-10-13. It was
a file-based fallback probe (TARBALL.md 4.4), since an open writes: every
call ran in a throwaway git repo under `./probe-output/office-probe-002`
(printed as `TMP`, and kept here as it printed it), with a bale.toml of
its own naming `TMP/dl` as its search path and setting `[clipboard]
command = ""`, so nothing was copied. Its two bundles were made by the
installed bale's own `tools/craft_response.py --bundle`: one with a
brief (`...-office-probe-open`, slug office-probe-open), one without
(`...-office-probe-other`), both forecasting `notes`. bale's install
`user/` directory listed the same before and after, and the repo's
working tree was clean at the end. The global post_pack hook was
declined by bale itself, stdin being closed (its lines are in
open-opened's stderr).

Each JSON file is one bale invocation, in the land set's shape: argv,
cwd, stdin, exit code, stdout lines exactly as printed with each line's
sha256 (computed by the probe on the machine and checked again here on
the paste, which came through as JSON with every non-ASCII character
escaped, so no console code page touched them), the stderr lines, and
where it was captured.

`format_open_json.txt` is the docstring that owns `bale open --json`'s
key contract (bin/bale_report.py, bale 0.4.52), as the probe printed it.
That part of the paste came through a console that showed UTF-8 as CP437;
its four characters (an em dash, the section sign, the multiplication
sign and an ellipsis) were restored by hand.

## In order

- status-before: `bale status --json` in the fresh repo: nothing open.
- check-fresh: `bale open --check --json` of the bundle with a brief:
  exit 0, `outcome` "rehearsed", `rehearsal` "check", every pack key
  null, `bundle` and `members` filled; the rehearsal report on stderr.
- open-opened: `bale open --json` of it: exit 0, `outcome` "opened" with
  the replayed pack's own values (sid 2026-10-13-office-probe-open-001,
  the tarball, the log, the opener as LF-joined text). Everything else,
  the opener's scissor block included, is on stderr.
- status-opened: the session open, its scope `notes`.
- check-desk: `bale open --check --json` of the same bundle while its
  session is open: exit 0, `outcome` "rehearsed", `rehearsal` "check",
  `desk` null. The line is byte for byte check-fresh's: nothing in it
  says the bundle would be a second desk, or on which session. Only
  stderr says so: `[bale] second desk: this bundle opened session SID,
  which is still open; bale open would record desk-2 on it`, and the
  report's `second desk:` row.
- check-desk-plain: the same without `--json`: the same lines, on stdout.
- check-desk-copy: the bundle's browser copy, `NAME (1).bale-bundle`
  (the same bytes): rehearsed as the same second desk; `bundle.stem` is
  the copy's.
- check-other: a different bundle forecasting the same path: exit 1,
  `outcome` "open-refused", `reason` "gate-refused", `cause` the
  forecast-overlap refusal naming the open session; `rehearsal` null.
- open-desk: `bale open --json` of the first bundle again: exit 0,
  `outcome` "second-desk", the joined sid, `desk` "desk-2", `tarball`
  the outbox request, the desk's opener; no session minted.
- open-desk-copy: the browser copy by bare name, found through the
  search path (the live case of 2026-10-12): "second-desk", "desk-3".
- status-desk: still one session open.
- unlock, status-after: the session closed again, nothing open.

## What it settles

- `bale open --check --json`'s `rehearsal` key is the rehearsal's kind
  ("check" or "dry-run"), never which bundle opened a session. What
  says that bale would take a bundle as a second desk is the outcome:
  bale's rehearsal passes ("rehearsed", exit 0) where it would refuse
  any other bundle overlapping the open session ("open-refused",
  "gate-refused"). office start reads the outcome (0.18.0).
- The open --json keys the office declared from the docstring in 0.17.2
  (outcome, sid, tarball, opener) are in the live lines, as is `desk`;
  the suite's fake now replays these lines, the sid and the paths
  swapped in.
