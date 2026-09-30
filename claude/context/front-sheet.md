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
line, `office open`, `desk`, `close` and `reopen` for folders, `office
week` for the calendar, and `office sessions` to record which sessions
worked on a job. `office status`, `survey` and `upgrade` look after the
office itself.

## Who uses it, where and when it runs

The occupant, on every machine that has an office. Installed per machine
at ~/.local/share/office-src from the committed tree and run as
`office`. It runs only when called; it schedules nothing and never runs
or carries a session.

## Recent changes

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
- Which key of `bale pack --json` carries the session id was not read
  from bale's key contract. `office sessions` reads `session_id`, then
  `sid`, then a single id-shaped value with a warning, and refuses loudly
  when it finds none.
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
