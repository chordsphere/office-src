# office-src: front sheet

For the occupant, in plain language. Every session that changes the tool
updates this sheet. It replaces "lands in the workshop" wherever earlier
notes say it: there is no separate office for the tool, and this record
is its home.

## What it does

Builds and keeps offices. `office tour` lets you try one first: a
throwaway office in a temp directory, six steps through the verbs, then
deleted. `office init` makes a real one: the spaces, a profile to fill
in, bale.toml, a first survey of the machine and a first commit, then
asks which projects it watches and prints the line that packs the
founding session. From then on the office is on its own, and office-src
reaches it only through `office upgrade`. Every day: `office` to walk in
(it ends with a Next line naming the one command to type), `office note`
to capture a line, `office slip` to drop a friction slip, `office start` to send a
session out for a folder (it packs the session with bale, or opens a
planner's bundle, records it in the folder and puts everything to attach
in one out tray beside the opener), `office land` to bring it back (bale
applies it in its repo, the office says how it ended, hands over the
relay to carry, runs the project's after-land actions and records the
planner's ratification), `office open`, `desk`, `close` and `reopen` for folders (numbered,
with statuses, gates and a History, and a desk that orders itself),
`office week` for the calendar, and `office sessions` to record which
sessions worked on a job and see how each one went. `office projects` names the
projects an office scopes, declares what rides beside each one's
sessions and what runs after they land, and shows what bale records
about them: the trust ledger, who last landed a file, the version trail. Walking in
shows the sessions open in those projects. `office status`, `survey` and
`upgrade` look after the office itself. `office help` lists every verb by
what you want to do, and every verb's `--help` has examples.

## Who uses it, where and when it runs

The occupant, on every machine that has an office. Installed per machine
at ~/.local/share/office-src from the committed tree and run as
`office`. It runs only when called. It runs bale's pack and apply when
the occupant asks (`office start`, `office land`), as the occupant's
hands at the terminal, and leaves every question bale asks to him; it
schedules nothing, never hands a session to a model and never carries
pastes.

## Recent changes

- 0.8.0 (session 2026-10-03-friction-front-door-002): the front door,
  the third and last session of the friction wave. Walking in ends with
  one Next line, worked out each time and never written down: land the
  session out, start the first ready folder, add a project, and so on
  down to nothing to do. `office help` is organized by what you want to
  do and says what the office saves a bale user; every verb's help has
  examples. `office tour` builds a throwaway office, walks through the
  verbs on it (start and land shown, never run), offers a shell to play
  in, and deletes it, touching nothing real and running no bale.
  `office init` asks which projects the office watches (`--project` is
  the flag twin). `office start` refuses a bundle whose forecast overlaps
  an open session in its own words, as it does a pack, whenever it can
  read the bundle. README.md leads with what you want to do. Additive: no
  migration, no office needs anything done.
- 0.7.0 (session 2026-10-03-friction-return-trip-001): the return trip,
  the second session of the friction wave. `office land` brings a
  session back in one command: bale apply (or retry, for a held one) in
  the repo it belongs to, with bale's questions left to the occupant; how
  it ended, from bale's records; the relay printed whole and, on WSL, on
  the clipboard; then, once applied, the project's after-land actions
  (office-src's is `./install.sh`, so nobody remembers it again) and the
  planner's ratification in the folder. An office session's folder
  record no longer meets bale's base check. `office start --bundle`
  sends out a session a sitting authored, and files the sitting's page
  its brief carries in the notepad. Additive: no migration, no office
  needs anything done.
- 0.6.0 (session 2026-10-02-friction-out-and-in-002): the out trip, the
  first session of the friction wave. `office start` packs a session for
  a folder, in the office or on a project, with what rides beside it
  (the doctrine, the office's context for a project session, and each
  project's declared ride-alongs), records the session in the folder,
  and gathers every file to attach in one out tray, ~/out-tray/SID,
  printing the opener (on WSL, on the clipboard too). `office projects
  set` and `add` declare what rides with a project and what runs after
  it lands, in the office's floor plan. `office slip` drops a friction
  slip as its own page. `office note` checks the page's prefix before it
  commits. close and reopen land where the folder ends up. Additive: no
  migration, no office needs anything done.
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

- `office start` packs the doctrine from a copy, but the lines `office
  init` and `office upgrade` print still run `bale pack --context` in the
  install's doctrine directory, which writes an outbox there. The
  founding door (its own session after 4b) hands both to `office start`.
- An unfounded office's Next line says `office status`, which names the
  missing profile sections but cannot reprint the founding line `office
  init` printed; the founding door is where that is fixed.
- The Next line cannot say whether a session's response is already in
  the downloads: bale's `--json` surfaces give a count of search
  directories (`bale status --json`, `config.search_paths`) but not the
  directories or what they hold. It says the session is out and that
  land finds it; a slip for bale-src.
- `office tour` and its play shell were built and tested on Linux; on
  WSL the first `office tour` is their test (the tour turns the
  clipboard and Explorer steps off for itself).
- ~~An office session forecasts its folder, and `office start` records
  the session in that folder after packing, so the folder.md the worker
  was shown is one commit behind; a response that rewrites folder.md
  meets bale's base check at apply.~~ Struck in 0.7.0: `office land`
  puts the folder back as it was packed while bale lands, and records
  the session again after. A folder changed by anything else after the
  record still meets the check, and land says so before bale runs.
- bale's `--json` pack report has no opener; `office start` takes it from
  between the scissor lines bale prints on stderr (a slip for bale-src).
  The same holds for `bale open`, which has no `--json` at all (the
  opener and the request's path are read from its report, the session
  id from `bale status`), and for the relay `bale apply` prints, which
  no `--json` key holds; `office land` takes it from between bale's
  RELAY markers.
  bale's session ids are unique within one repo only; `office start`
  gives an office session's default slug an -office suffix so a folder
  packed in the office and in a project the same day gets two ids.
- On WSL the clipboard and Explorer steps were built without a WSL
  machine to run them on; the first `office start` there is their test,
  and the first `office land` is the relay's.
- A response saved twice by a browser is `response-SID (1).tar.gz`;
  bale's search finds `response-SID.tar.gz` first, so after a HOLD the
  corrected response is named by its path (`office land` asks for it).
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
- ~~The doctrine says a script that appends to filed paper checks the
  page's prefix before it commits; `office note` does not yet.~~ Struck
  in 0.6.0: `office note` checks before it commits.
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
- *Can the tour change my office?* No. It builds its own in a temp
  directory, runs every command against it with its own settings and a
  stand-in bale that refuses everything, and deletes it when it ends or
  is stopped.
- *Who marks a renovation done?* `office upgrade`, by checking what the
  renovation declared. No session edits the version stamp.

## Public documentation

README.md and doctrine/OFFICE.md in the repo; this sheet points at them
and does not restate them.
