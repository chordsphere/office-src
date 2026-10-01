# office-src: front sheet

For the occupant, in plain language. Every session that changes the tool
updates this sheet. It replaces "lands in the workshop" wherever earlier
notes say it: there is no separate office for the tool, and this record
is its home.

## What it does

Builds and keeps offices. `office init` makes one: the spaces, a profile
to fill in, bale.toml, a first survey of the machine and a first commit,
then prints the line that packs the founding session. From then on the
office is on its own, and office-src reaches it only through `office
upgrade`. Every day: `office` to walk in, `office note` to capture a
line, `office open`, `desk`, `close` and `reopen` for folders (numbered,
with statuses, gates and a History, and a desk that orders itself),
`office week` for the calendar, and `office sessions` to record which
sessions worked on a job and see how each one went. `office projects` names the
projects an office scopes and shows what bale records about them: the
trust ledger, who last landed a file, the version trail. Walking in
shows the sessions open in those projects. `office status`, `survey` and
`upgrade` look after the office itself.

## Who uses it, where and when it runs

The occupant, on every machine that has an office. Installed per machine
at ~/.local/share/office-src from the committed tree and run as
`office`. It runs only when called; it schedules nothing and never runs
or carries a session.

## Recent changes

- 0.5.0 (session 2026-09-30-desk-verbs-002): the desk's verbs. Folders
  are numbered (`folder N`) by `office open`, which asks on a terminal
  for the title, size, lane and source it was not given, explains a
  field on `?`, and takes every field as a flag; `--candidate`, and
  `--filed --sid SID` for a job born done. Statuses and History lines
  from `office close` (done, `--into`, `--split`, `--retired`),
  `office reopen` and `office sessions` (the first session opens the
  folder; `--ratified [--except]`). `office desk` shows in flight,
  ready in order, parked under what each waits for, and candidates;
  walking in shows in flight and the first three ready. `office open`
  refuses while an open session in the office's own bale registry
  holds the desk. `office status` checks folders against their History
  and filed pages against git; `office init` refuses a defective
  install. Additive: no migration, no office needs anything done, and
  older folders are never numbered.
- 0.4.0 (session 2026-09-30-read-side-001): the read side. The floor
  plan's `[projects]` table and `office projects` (list, `add`, and the
  `--ledger`, `--landed PATH` and `--versions` renderings); the reader,
  `lib/office_bale.py`, which runs bale's `--json` surfaces and nothing
  else; `share/bale-consumption.toml`, every bale verb, flag and key the
  office reads, written from a probe of bale 0.4.45; the walk-in's In
  flight list; `office sessions FOLDER` with outcomes, claims beside
  verdicts and exchange rounds; `office status` lines for bale and the
  projects; OFFICE.md's section 10 and 13 lines. The pack report's id
  is read from `sid`, its contract's key, with no guessing. The suite's
  bale is a fake replaying the probe's captured lines, kept in
  `claude/fixtures/`. Additive: no migration, no office needs anything
  done.
- 0.3.1 (session 2026-09-29-verb-table-columns-004): every verb in
  `share/verbs.toml` declares `lands`, `attended` and `trigger`, and the
  catalog registers the blueprint's session kinds (`sitting`, `chat`,
  `blueprint-close`, `digest`, `review`, `check`, `retry`), all
  `built = false`. The rule, no declared landing means no unattended
  spawn, is refused by the suite and reported by `office status`, which
  also reports a hung page that is also filed (session 1's rider,
  consumed here). Nothing consumes the keys yet beyond the check.
  Additive: no migration, no office needs anything done.
- 0.3.0 (session 2026-09-29-drafting-table-space-003): the
  drafting-table's contents in the install: the catalog files a list of
  paths inside the space and `office upgrade` reads it; templates for a
  blueprint, its close report and every drafting-table page; the folder
  template's field block, Riders and History, with `office open` writing
  the status and the queued date; `doctrine/checks/filed-append-only.sh`
  for sessions that write filed pages; and the doctrine lines the space
  needs, the append rule, one home per fact, and wizards over flags.
  Additive: no migration, no office needs anything done. Nothing is
  copied into an office yet; that is the renovation's job, and the
  verbs come in the sessions after this one.
- 0.2.0 (session 2026-09-24-office-src-verbs-002): the everyday verbs and
  walking in; folders record session ids from `bale pack --json`; init
  writes bale.toml so every pack ships the hung items; the founding
  session is scoped and lands the profile, the occupant's words and the
  real timezone in one trip; only `office upgrade` writes the version
  stamp. Breaking: offices built by 0.1.0 get bale.toml from migration
  0.2.0. No office existed yet, so nothing needed upgrading.
- 0.1.0 (session 2026-09-24-office-src-core-001): the doctrine,
  templates, profile shape, init, survey, status, upgrade, install.

## Known problems

- The doctrine's ride-along context pack (`bale pack --context` run in
  the install) has not been run for real yet; the first founding line
  will be its first run.
- bale does not stamp everything the read side and the watches want.
  Slips for bale-src, from the 0.4.0 probe (session
  2026-09-30-read-side-001's notes): no HOLD cause class; no marker
  telling a deliberate checkpoint-amendment accept from an override;
  the session dossier leaves out the bale version each session ran
  under, and the self-reported round counts; no `--json` surface lists
  every session in a repo (the office enumerates the outbox); and
  `bale status` gives a lifecycle state for one open session only. The
  renderings say "not on bale's dossier" where they would show one.
- The version trail is read two ways (applied sessions that landed a
  VERSION file, and bale's contract-doc epochs), pending a ruling on
  what the blueprint's "version landmark" meant.
- The doctrine says a script that appends to filed paper checks the
  page's prefix before it commits; `office note` does not yet. `office
  status` now catches a rewrite after the fact.
- `office desk` cannot yet read a gate on a blueprint, an agenda item or
  a ruling: such a folder waits under that name, as not readable until
  the drafting-table verbs land.
- The calendar's two-page format is the tool's first guess; the first
  office with a calendar will tell whether it fits.
- Offices on WSL report the machine's zone (UTC on chordsphere) until
  the founding session sets the real one.

## Questions likely to come up

- *Does upgrading office-src change my offices?* Their tools at once.
  Their files only through `office upgrade`, and only for breaking
  releases.
- *Can a verb or an upgrade rewrite my notes?* No. Notes are appended,
  folders are moved as they are, and upgrade rolls back a migration that
  touches the notepad or the filing cabinet.
- *Why does `office note` still work when everything else refuses?*
  Capture is instant and dumb. It warns about an unfounded or out-of-date
  office and writes anyway.
- *Who marks a renovation done?* `office upgrade`, by checking what the
  renovation declared. No session edits the version stamp.

## Public documentation

README.md and doctrine/OFFICE.md in the repo; this sheet points at them
and does not restate them.
