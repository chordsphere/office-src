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
asks which projects it watches and the profile's questions, and sends
the founding session out through `office start` with your answers in its
brief (`office found` does the same for an office that is still
unfounded). From then on the office is on its own, and office-src
reaches it only through `office upgrade`. Every day: `office` to walk in
(it ends with a Next line naming the one command to type), `office note`
to capture a line, `office slip` to drop a friction slip, `office start` to send a
session out for a folder (it packs the session with bale, or opens a
planner's bundle, records it in the folder and puts everything to attach
in one out tray beside the opener; it surveys the machine first, asks
which of the project's ride-alongs go this time, offers the riders the
pack carries, and asks bale whether a bundle can open before it writes
anything), `office land` to bring
it back (bale applies it in its repo, the office says how it ended, hands
over the relay to carry, runs the project's after-land actions, records
the planner's ratification, closes the founding folder once the founding
has landed, names any watch that fired, and ends saying how each action
went; given a read-only sitting, it ends the sitting), `office open`, `desk`, `close` and `reopen` for folders (numbered,
with statuses, gates and a History, and a desk that orders itself),
`office week` for the calendar, and `office sessions` to record which
sessions worked on a job and see how each one went. `office projects` names the
projects an office scopes, declares what rides beside each one's
sessions and what runs after they land, and shows what bale records
about them: the trust ledger, who last landed a file, the version trail.
For work too big for one folder there is the drafting table, which
arrives in an office with the first verb that writes it: `office
blueprint open`, `ratify` and `close` for an arc, `office moves` to
apply the desk moves a sitting decided, `office rider` and `office
riders` for small work with a named carrier, `office agenda add` for a
question a sitting will rule on, `office rulings` and `office
evidence` to read the ledgers a sitting keeps, `office watches` and
`office watches check` for the watches a sitting set (fired, not fired,
or cannot evaluate, from bale's records), and `office digest`, the one
page a sitting opens on: versions, what happened since the last
sitting, the watches, the standing numbers, the desk, the agenda and the
open blueprints, all computed when it runs. `office start` writes the
digest again just before it packs a sitting and sends the drafting table
with it. Walking in
shows the sessions open in those projects. `office status`, `survey` and
`upgrade` look after the office itself. `office help` lists every verb by
what you want to do, and every verb's `--help` has examples.

## Who uses it, where and when it runs

The occupant, on every machine that has an office. Installed per machine
at ~/.local/share/office-src from the committed tree and run as
`office`. It runs only when called. It runs bale's pack and apply when
the occupant asks (`office start`, `office land`), and bale's unlock to
end a read-only sitting the office sent out, as the occupant's
hands at the terminal, and leaves every question bale asks to him; it
schedules nothing, never hands a session to a model and never carries
pastes.

## Recent changes

- 0.13.0 (session 2026-10-07-third-trip-001): the third trip.
  `office start` asks bale (`bale open --check`) whether a bundle can
  open before it writes anything, so a bundle bale cannot find stops it
  with nothing opened, surveyed or packed; with `new` it asks where the
  work lands, then bale, then opens the folder. A start that opened a
  folder and failed after leaves the folder and prints the one line that
  retries it. `office open` checks the title first, and `office start
  new` offers a folder already on the desk as the one to start. `office
  start` offers the riders its pack carries and carries the ones taken
  into the folder (`--carry N`, `--carry none`). `office land` runs
  `office watches check` after an applied landing and prints what fired,
  and closes the founding folder when the founding lands with the
  profile complete. The walk-in says when the install is behind the
  source it scopes, and the Next line names `./install.sh` right after
  the version cases (an order change, to ratify). A founding answer on a
  terminal takes a paragraph. The suite runs side by side
  (`tests/run.sh`; `--serial` for one process). bale 0.4.47 was checked
  against the consumption manifest: nothing the office reads moved.
  Additive: no migration, no office needs anything done.

- 0.12.0 (session 2026-10-06-founding-door-002): the founding door.
  `office init` asks the profile's questions, one per section, each with
  a flag twin, and the timezone you live in (checked, and written to the
  floor plan when it resolves); keeps the answers in the founding folder;
  and sends the founding session out through `office start` with a brief
  carrying them, so the founding session asks only for what you skipped.
  `office found` is the same door for an unfounded office, and `office
  start` on the founding folder goes through it. `office upgrade` sends a
  renovation out the same way and never twice; `office land` brings it
  back while the office is behind. The Next line names what founds an
  unfounded office. No line writes into the install's doctrine directory
  any more. Additive: no migration, no office needs anything done.

- 0.11.0 (session 2026-10-06-drafting-table-digest-001): the second and
  last half of blueprint session 4b. `share/watch-queries.toml` names
  the seven watch queries once, written from a probe of bale 0.4.45's
  `stats --json --since`. `office watches` lists the watches and their
  state from the log; `office watches check` runs each one over the
  window since it last fired, for the office's own registry and each
  project, and `--record` logs the firings. `office digest` writes the
  sitting-open page; `office start` writes it before every sitting and
  ships the drafting table with it. The Next line names `office moves`
  while desk moves are pending, after a session out and before an
  unfounded office (an order change, to ratify). The consumption
  manifest declares `--since`, the catalog's keys and bale's commit
  subjects. Additive: no migration, no office needs anything done.

- 0.10.0 (session 2026-10-05-drafting-table-pages-001): the first half
  of blueprint session 4b. The drafting table arrives in an office with
  the first verb that writes it (its front page, the floor plan's entry
  and bale.toml's trigger, and each page on its first write, in the same
  commit), so no migration and no renovation session bring it. `office
  moves` applies a sitting's desk moves through open's, close's and the
  gate flags' own code, ticks each, writes minted numbers onto the
  blueprint, and stops at the first line it cannot apply. `office
  blueprint open`, `ratify` (and `office status`'s check that a ratified
  charter never changes) and `close`, which sends the close sitting out
  through `office start`. `office rider add`, `carry`, `consumed` and
  `office riders`; `office agenda add`; `office rulings [ID] [--check]`
  and `office evidence [N]`. The desk resolves blueprint, agenda and
  ruling gates and shows orphaned riders and pending desk moves (the
  walk-in names the session that wrote them); `office desk --blueprint
  ID` shows one arc. The one-writer rule holds every script that mints a
  number or adds to a page. `office slip` titles a slip from a numbered
  list by its words. Additive: no migration, no office needs anything
  done.

- 0.9.0 (session 2026-10-04-friction-second-trip-001): the second trip,
  five frictions the first real round trip found. `office start` shows
  what rides with the project and lets one stay home this once
  (`--leave-out`, `--no-rides`), and carries the doctrine once (twice
  only when the project's own copy differs, the install's named so). It
  surveys the machine before every pack, so the hung survey is never
  stale. `office land SID` ends a read-only sitting the office sent out
  (bale unlock, and an `ended` History line), and the walk-in says so
  beside the sitting. A bundle's where question defaults to the place
  whose tree holds its paths, and a bundle whose paths are nowhere, or
  elsewhere, is refused before bale runs. A timezone that does not
  resolve is named with its remedy (the warning, `office status`, the
  walk-in). `office land` ends with what became of each after-land
  action, and `office status` says when the install is behind the
  working copy it came from. Why 0.8.0's install did not move: 0.8.0
  was applied by hand with `bale apply`, which runs no after-land
  action; nothing in the office failed. Additive: no migration, no
  office needs anything done.

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

- ~~`office start` packs the doctrine from a copy, but the lines `office
  init` and `office upgrade` print still run `bale pack --context` in the
  install's doctrine directory, which writes an outbox there.~~ Struck in
  0.12.0: init and upgrade send their sessions out through `office
  start`, and nothing writes into the install.
- ~~An unfounded office's Next line says `office status`, which names the
  missing profile sections but cannot reprint the founding line `office
  init` printed.~~ Struck in 0.12.0: it names `office start` for the
  founding folder, or `office found`.
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
- ~~`office desk` cannot yet read a gate on a blueprint, an agenda item or
  a ruling: such a folder waits under that name, as not readable until
  the drafting-table verbs land.~~ Struck in 0.10.0: those gates resolve
  through the drafting table (a close report, an agenda item's disposal,
  a ruling's record), and one naming nothing is an error line.
- ~~Blueprint session 4b's second half is still owed.~~ Struck in
  0.11.0: the catalog, the watches verbs, the probe's fixtures and the
  digest are built.
- `office watches check` prints two watches as "cannot evaluate: bale
  does not stamp ... (slip)": watch 15 (`hold-cause-cluster`, a HOLD
  cause class) and watch 17 (`stamp-mismatch-accepts`, a marker telling
  a deliberate checkpoint-amendment accept from an override). Both are
  slips home-office's suggestion box already holds for bale-src. Watch
  24 (`unrelayed-rounds`) is evaluated from the aggregate's list of
  sessions that self-reported a round bale holds no stamp for; the
  per-session count on the dossier is the slip it still waits on, and no
  watch needs it yet. Watch 13's datum was never missing.
- bale's `stats --since` takes a day, not an instant. A watch that fired
  looks again from the day after, so a session packed later on the day
  a watch fired is never seen by that watch (a slip for bale-src:
  `--since` taking an instant). The digest's "since the last sitting"
  is exact, because it reads each session's dossier for its times.
- The digest finds the sessions that closed since a sitting from the
  subjects bale gives its commits (`[bale SID] ...`, `Merge bale SID`,
  `[bale sweep SID] ...`), then reads each one's outcome from its
  dossier. The subjects are bale's habit, not its contract; the
  consumption manifest declares them so a change fails a test (a slip
  for bale-src). A long window (an office with no sitting's page yet)
  reads at most 60 dossiers per project and says how many it left.
- The digest's eye-watch count reads three sittings as "unlooked-at";
  the blueprint lets a profile house rule change the number, and no
  profile line is read for it yet.
- The drafting table arrives with a verb, not by renovation; the
  doctrine's section 5 says so. The renovation kind remains for spaces
  whose arrival needs judgment, and `office upgrade` never brings this
  one.
- A rider consumed in a folder already in the filing cabinet gets its
  dated `consumed` line, but its `status:` field keeps the value it had
  when the folder closed, because a filed folder only gains lines. The
  dated lines are the record; every reader takes the last of them.
- The calendar's two-page format is the tool's first guess; the first
  office with a calendar will tell whether it fits.
- An office built with `--no-founding`, or one whose founding was
  skipped, reports the machine's zone (UTC on chordsphere) until `office
  found` or the founding session sets the zone you live in.
- After-land actions run only through `office land`. A session applied
  by hand with `bale apply` runs none; for office-src that means the
  install stays where it was (0.8.0's did, until `./install.sh` was run
  by hand). `office status`'s `source:` line shows it, and since 0.13.0
  so does the walk-in, with the Next line naming `./install.sh`, when the
  office scopes that working copy (home-office scopes office-src).
- ~~Founding still writes a timezone without checking it resolves.~~
  Struck in 0.12.0: init and found check the zone they write, and name
  the remedy for one that does not resolve. Moving an older floor plan
  to a zone's canonical name is still a hand edit of its timezone line,
  by design for a one-off.
- ~~The founding questions take one line each on a terminal; a longer
  answer is a flag (`--purpose "$(cat purpose.txt)"`), or the founding
  session's conversation.~~ Struck in 0.13.0: a blank line ends an
  answer, so a paragraph is typed as it is.
- `office start` cannot list bale's search directories (no `--json`
  surface does; the slip is in the box), so for a bare bundle name it
  asks bale with `bale open --check`, which says where it searched when
  it cannot find the name. Since 0.13.0 that happens before anything is
  written.
- A rider's glob names no project unless it is written with one
  (`office-src: bin/`), so a bare glob such as `bin/` rides the next
  pack on any project whose forecast touches `bin/`, and a pack
  forecasting a whole repo touches every bare glob. On a terminal each
  is offered, default carry; say no to one that does not belong.
- The office reads bale 0.4.45's captures as its floor and was checked
  against 0.4.47 (session 2026-10-07-third-trip-001). One difference the
  office does not read: `bale stats --json --work-class meta` in
  office-src reported no class on 0.4.47, though it holds meta
  sessions; a question for bale-src in that session's notes.

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
- *I skipped some of the profile's questions. Now what?* The founding
  session asks them. If it never went out, the walk-in's Next line names
  `office start` for the founding folder, which sends it with the
  answers you gave and asks the rest.
- *Why did the install not move when a release landed?* Either it was
  applied by hand with `bale apply` (no after-land action runs), or
  `./install.sh` failed, which `office land`'s last lines now say.
  `office status` shows whether the install is level with its source.
- *How does a planning sitting end?* `office land SID`, from the office,
  when the sitting is over: bale unlock, and a line in the folder. The
  folder stays open until you close it.
- *How does an office get a drafting table?* The first time a verb writes
  one: `office blueprint open`, `office rider add` or `office agenda add`
  (or `office moves`, once a sitting wrote moves). Nothing is made by
  hand, and nothing happens in offices that never use one.
- *A sitting landed with desk moves. What now?* `office moves`. Walking
  in says how many are pending and which session wrote them until it is
  run.

- *What window is the digest's "since the last sitting"?* From the
  commit that filed the latest sitting's page in the notepad
  (`notepad/DATE-SLUG.md`, which `office start` files from a sitting's
  brief) to now. The page names that page and commit, so you can
  disagree with it.
- *Why does a watch say "cannot evaluate" and not "not fired"?* Because
  bale does not record what it would need. Not fired would claim it was
  looked at.

## Public documentation

README.md and doctrine/OFFICE.md in the repo; this sheet points at them
and does not restate them.
