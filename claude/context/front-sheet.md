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
to capture a line, `office slip` to drop a friction slip, `office drop`
to drop a message or a thread in the in-tray (from the clipboard, a file
or stdin, with the project in any words), `office start` to send a
session out for a folder (it packs the session with bale, or opens a
planner's bundle, records it in the folder and puts everything to attach
in one out tray beside the opener; it surveys the machine first, asks
which of the project's ride-alongs go this time, offers the riders the
pack carries, and asks bale whether a bundle can open before it writes
anything), `office land` to bring
it back (bale applies it in its repo, the office says how it ended, hands
over the relay to carry, runs the project's after-land actions, records
the planner's ratification, files the folder's walkthrough and delivery
pages from the response, closes the founding folder once the founding
has landed, names any watch that fired, and ends saying how each action
went; given a read-only sitting, it ends the sitting; for a project on
another machine it does all of this there, the response carried over;
and it offers to close a folder whose one session landed and was
ratified), `office relay` to carry a planner's answer to a clarification
back to the session's repo, `office probe` to run a worker's probe block
where a folder's project lives (on its host, in its container), after
showing its header and asking once, with the output back on your
terminal and the block on your clipboard, `office deliver` to carry a folder's landed
work to its project's audience as curated commits on a branch named from
the folder (the words from the folder's delivery.md, the letterhead
check run first, one question before anything leaves, the delivery
recorded in the folder), `office letterhead check` for what the
letterhead refuses in any tree, `office open`, `desk`, `close` and `reopen` for folders (numbered,
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

## The suite's clock

For the worker first. bale gives a session's validation two minutes
(TARBALL.md 7.6), and the whole suite takes far longer (679 tests; about
18 minutes on a two-core sandbox, 4 jobs at a time). So, since 0.17.1:

- Every validation.sh runs the fast tier, `tests/run.sh --fast`, plus
  what the session touched, named after it (`tests/run.sh --fast
  test_land.TestLandWhichSession test_x.TestY.test_z`; a module, a class
  or a test), and asserts its own wall time under 120 seconds. The tier
  is `tests/fast-tier.toml` and nowhere else: one test per verb
  `bin/office` dispatches (and the walk-in), then the tests that cost
  under half a second. `--fast` stops before running anything when a
  verb has no entry point there or a name is not in the suite, prints
  its wall time, and fails past `budget_seconds`. Add a module whole only
  when it is cheap; `times.tsv` beside every run's logs says what each
  test costs.
- The whole suite stays reachable from validation.sh behind `--slow`,
  and the worker runs it in the sandbox before shipping and reports its
  count, result and wall time in notes.md.
- No test reads the machine it runs on. A test's HOME, TMPDIR,
  XDG_CONFIG_HOME and downloads are its Env's (`self.e.home`,
  `self.e.tmpdir`, `self.e.downloads`; `Env.this_process()` for a helper
  called in-process, which lends the Env's whole environment, git
  identity included). The runner gives every job its own HOME and
  TMPDIR besides, so a test that leans on the machine (its git identity,
  its temporary directory) fails in the sandbox, not on the occupant's
  box. `tests/test_suite_clock.py` fails the suite on any test file that
  names the machine's temporary directory, `expanduser`, `Path.home(` or
  `$HOME` outside Env; its ALLOWED list holds the few that are text a
  fake host runs or paths a probe printed, each with its reason.
- After every landing, office-src's after-land actions start the whole
  suite detached (`tests/run.sh --detach`): one line naming the verdict
  file under `~/.local/state/office-src/suite/`, and nobody waits.
  `latest/verdict` there is the last run's one line: `RUNNING since`,
  `OK`, `FAILED` or `BROKEN`, with the count, the time and the commit.
  Since 0.17.2, walking into an office that scopes office-src's source
  shows it as one `Suite:` line whenever it is not `OK`, including a
  `RUNNING` more than an hour old. A worker on office-src can ask for it
  in a probe.

## Recent changes

- 0.19.0 (session 2026-10-13-office-drop-003): `office drop`, the in-tray,
  and the drops riding with every session; `office start --drop`.
  - `office drop` takes a message or a thread from the clipboard, a file
    or stdin and keeps it as one page, `in-tray/DATE-SLUG.md`, committed
    on its own. It says what it took, asks the project as free text on a
    terminal (a plain return skips it), never refuses a drop it can
    write, and only warns in an unfounded or out-of-step office. The
    page: `# Drop: ` and the first line, then `dropped`, `project` (or
    `none given`), `via` and `status: unsorted`, then `## Text`, verbatim
    and ASCII. The in-tray arrives with the first drop: its front page,
    the floor plan's entry and bale.toml's trigger, in that drop's commit.
  - Every session `office start` sends out carries the unsorted drops:
    in the request for an office session, in the office's context for a
    project session, beside a bundle as `context-in-tray.tar.gz`. The out
    tray and the opener say how many ride.
  - `office start --drop in-tray/PAGE` mints the folder through `office
    open`'s code (title from the drop, lane from its project or asked,
    size small unless you say, source `drop`), moves the page into the
    folder's `drops/` with a `dropped` History line, and sends a project
    session out whose brief says: sort it first, then do the work. Drop,
    start, land.
  - The walk-in counts the unsorted drops and says how old the oldest
    is; `office desk` lists them; the Next line names `office start
    --drop` for the oldest it can send. `office status` checks the
    in-tray.
  - The doctrine's core tells a build session what it owes the drops it
    carries: a `## Sort` section in its notes.md, in a pinned format.
  - Additive: no migration.
- 0.18.0 (session 2026-10-13-office-probe-002): `office probe`, the
  second-desk ruling, and bale 0.4.52's live open --json lines.
  - `office probe FOLDER` runs a worker's probe block where the folder's
    project lives: in its repo, through its shell on a host (no terminal
    asked for, stdin closed), or in the office root. The block comes from
    a file, stdin, or the clipboard (machine.toml's new `paste_command`,
    asked once). It shows the block's header and asks once; a block that
    is not a probe, or whose header does not say it is read-only, is
    refused by name. The output comes back whole, the block goes on the
    clipboard here, a fallback's `probe-output/` is carried to the
    session's out tray and removed where it ran, and the folder's History
    gains `- DATE probe: SID, N lines`.
  - `office start --bundle`: a second desk is bale's to recognize. From
    bale 0.4.50 a bundle the office can read whose forecast overlaps an
    open session goes to `bale open --check --json`. Where bale's
    rehearsal passes it (its own session, still open), start goes on and
    joins the desk; where bale refuses, the office refuses in its own
    words with bale's reason beside them. bale's `rehearsal` key does not
    say which bundle opened a session; the outcome is what the office
    reads.
  - fixtures/bale-0.4.52/: 13 live captures of open --json and open
    --check --json, which the suite's fake replays.
  - The doctrine names `office probe` and the walk-in's `Suite:` line.
  - Additive: no migration.
- 0.17.2 (session 2026-10-13-doctrine-core-001): the doctrine's core, the
  second desk and the suite's verdict on the walk-in.
  - doctrine/OFFICE.md opens with a reading card naming what each kind
    of session reads. A build session's read sits above a PAST THE CORE
    banner: 199 lines, against the 1,044 it read before. No section is
    renumbered and no word changed; section 4 is split across the banner
    under its own number.
  - `office start --bundle` handles a bundle whose session is still
    open. bale 0.4.44 and later take it as a second desk and open
    nothing, which is why the audience-line start of 2026-10-12 made no
    tray. Start now records the joined session, fills the tray and
    prints the desk's opener, reading `bale open --json` from bale
    0.4.50.
  - Walking into an office that scopes office-src's source shows one
    `Suite:` line when the latest `tests/run.sh --detach` verdict is not
    OK.
  - Additive: no migration.
- 0.17.1 (session 2026-10-12-suite-clock-001): the suite's clock. The
  fast tier (`tests/run.sh --fast`, `tests/fast-tier.toml`, 280 of the
  suite's 679 tests, 55 seconds on a two-core sandbox, 91 with this
  session's additions), the detached whole run (`tests/run.sh
  --detach`), per-test times in every run (`times.tsv`), a HOME and
  TMPDIR of its own for every job, and the rule that no test reads the
  machine, kept by `tests/test_suite_clock.py`. Env gives TMPDIR and
  downloads; eight tests that leaned on the machine now use their Env.
  The runner's plan test no longer re-reads every test file per test
  (113 seconds to under 2). No verb changed. Additive: no migration, no
  office needs anything done; add `tests/run.sh --detach` to
  office-src's after-land actions.
- 0.17.0 (session 2026-10-08-audience-line-002): the audience line.
  Three declarations on the projects table, `audience` (the remote in the
  workbench clone that points at the audience's git host), `author` (the
  identity the audience expects on the commits; unset, the clone's own)
  and `base` (the audience branch deliveries branch from; unset, the
  remote's HEAD branch), set by `office projects add` and `set`, wizard
  and flags, and shown by `office projects`; declaring an audience puts
  the push guard in the clone's .git/hooks, which refuses a push to the
  audience by hand and lets only `office deliver`'s branch through.
  `office letterhead check` names every line that holds what the
  letterhead refuses (names, phrasing, bale's marks, the office's
  forbidden words), on a tree here, a range, a file, or a project's repo
  on its host; the list is share/letterhead.toml, which the suite's text
  rules read too. `office deliver FOLDER` carries the folder's landed
  work to the audience: the base fetched, the applied sessions named by
  folder, the words from delivery.md, the squash in a temporary worktree,
  the letterhead check on the diff and the words, one question, one
  curated commit (several when delivery.md marks them) as the author,
  that branch pushed and nothing else, a `delivered` History line, the
  review's URL. Built and pushed from this machine (the probe found the
  work host's credential cache empty), the landed commits of a hosted
  project carried here as a bundle. The folder's two pages,
  walkthrough.md and delivery.md, from two new templates that ride with
  every build session: the session writes them at the end of its
  notes.md and `office land` files them (`office sessions --pages` when
  land could not). `office relay SID ANSWER-FILE` carries a planner's
  answer to bale relay where the session is open. Additive: no
  migration, no office needs anything done.
- 0.16.0 (session 2026-10-08-return-trip-to-host-001): the return trip
  from a host. `office land` on a project on a host checks that the host
  answers (the connect line and the rerun line when it does not, before
  anything is carried), finds the response on this machine, carries it to
  the host checked by sha256, runs `bale apply` or `retry` in the repo
  there with your terminal, reads how it ended there, prints the relay
  here (clipboard on WSL), runs the after-land actions there, and ends a
  sitting with `bale unlock` there; nothing is left on the host outside
  the repo. Where downloads land is the office's own setting,
  `downloads` in `~/.config/office-src/machine.toml`, asked once on a
  terminal and never again; land finds a response there by name and
  start a bundle for a hosted project, the newest of a browser's copies
  winning and named, and a local land uses it to pick the newest of
  several copies. land offers to close a folder whose one session landed
  applied and was ratified with no exception (default close; `--close`,
  `--leave-open`; piped it stays open). One start or land reaches a host
  once, and reads share connections: a hosted start in the suite went
  from 7 connections to 4 (a bundle, 18 to 8); a hosted land takes 4
  plus one per after-land action. A `~/` path on a host now works through
  the shell. The README says to run the suite in the foreground, and the
  runner warns when SIGINT is ignored. Additive: no migration, no office
  needs anything done.
- 0.15.0 (session 2026-10-07-out-trip-to-host-004): the out trip to a
  host. `office start` on a project on a host packs the session there:
  it checks first that the host answers (the connect line when it does
  not), that its bale is at the floor (naming `office projects
  level-bale` when it is not) and that the repo is bale's; bale's pack,
  or `bale open --check` and `bale open` for a bundle, runs through the
  project's shell, the brief or the bundle sent there first, and the
  request comes back into the out tray here, checked by sha256. The
  temporary directory it makes on the host is removed either way. A
  bundle for a hosted project is named by its path here. `office projects
  add --from CLONE` brings a clone on this machine to the host as the
  project's repo: every branch and tag, the remotes as the clone has
  them, carried as a git bundle, then prepared; the clone here is left
  alone, and a dirty one is named and asked about (`--from-dirty-ok`
  piped). `office projects level-bale NAME` installs this machine's bale
  on the host through the host's own `upgrade.sh -y`, keeping its
  `user/`; `office status` names it when a host's bale is behind. A bale
  step the occupant answers runs through `ssh -tt` and a container's
  `-it`, derived from the stored shell. `office land` on a hosted
  session says the return trip is not built yet and the response waits.
  `tests/run.sh` prints each failing test's traceback in its summary.
  Additive: no migration, no office needs anything done.
- 0.14.0 (session 2026-10-07-project-on-host-003): a project on another
  host, the first half of "a project on another machine". A [projects]
  entry may declare `host` (an ssh target), `shell` (the prefix that
  runs one command where the repo is, default `ssh HOST bash -lc`,
  through a container when the repo sits inside one) and `connect` (the
  occupant's words for what brings the host up), written by `office
  projects add` and `set`, wizard and flags. The read side runs every
  bale and git read of such a project through that shell, batched per
  round, so the walk-in, `office sessions`, the ledger, landed and
  versions renderings, watches check and the digest all read it; one
  reach check per host and command, bounded, and a host that does not
  answer is one line in the project's place with the connect text and
  the command to rerun. `office status` says whether each host answers
  and which bale is there against the floor. `office projects add
  --prepare` (offered on a terminal) sets a clone up for bale without a
  trace in git: the four paths bale makes go into `.git/info/exclude`,
  an empty `bale.toml` is written, and the repo's `.gitignore` is never
  touched. `office start` and `office land` refuse a hosted project
  until the next release. New module lib/office_host.py; the suite's
  fake ssh runs no network.
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

- A Sort section a session writes is not filed yet: `office land` reads
  nothing of it in 0.19.0, and a carried drop stays `unsorted` in the
  in-tray until the next release files it (and `office moves` mints the
  folders sorted drops ask for). Until then, a drop a session sorted
  keeps riding with later sessions; `office start --drop` is the way to
  take one out of the in-tray now.
- A drop's heading is its first line, so a message that opens with a
  greeting ("Hi,") is titled by the greeting, and so is the folder
  `office start --drop` mints from it. `--title` names it better.
- `office probe`'s WSL paste command, PowerShell's Get-Clipboard through
  powershell.exe with its output made UTF-8, is offered from memory, not
  from a probe that ran it: the first `office probe` there with the block
  on the clipboard is its test. Correct it at the question, or later in
  machine.toml.
- The doctrine's section 4 (past the core) still says a bundle the
  office can read is refused for an overlap the same way a pack is.
  Since 0.18.0 that holds only below bale 0.4.50; from 0.4.50 bale's
  rehearsal decides. The session that changed it was held to the
  doctrine's two named sentences, so the sentence waits for the next
  session that may change the doctrine.
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
- ~~A response saved twice by a browser is `response-SID (1).tar.gz`;
  bale's search finds `response-SID.tar.gz` first, so after a HOLD the
  corrected response is named by its path (`office land` asks for it).~~
  Changed in 0.16.0: with machine.toml's `downloads` set, land takes the
  newest copy of the name and says which (for a project here it passes
  bale that path). It still asks after a HOLD when the downloads hold one
  copy only, since that copy may be the held one; and until the setting
  is there, a local land is as before.
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
- A bundle that the office can read (a path, not a bare name), whose
  forecast overlaps a session the same bundle opened, is refused in the
  office's own words as an overlap (doctrine section 4), though bale
  would take it as a second desk. Today a second desk reaches bale only
  by bare name. Whether the office should let it through is a planner's
  ruling (proposed in session 2026-10-13-doctrine-core-001's notes). The
  office cannot tell which bundle opened a session without reading
  .bale/.
- `bale open --json`, which start reads from bale 0.4.50 on, was read
  from bale 0.4.52's key contract (its docstring) by a read-only probe;
  no live line is captured yet. The suite's fake follows that contract.
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
- ~~A session goes out to a project on another host (0.15.0), but does
  not come back yet.~~ Struck in 0.16.0: `office land` brings it back
  over the shell. The attended form it uses (`ssh -tt`, a container's
  `-it`) and the whole hosted landing are tested against the suite's fake
  ssh only; the 0.14.0 probe proved the attended form on the work host,
  and the first hosted `office land` (a work project's first landing) is
  the landing's real test. Built on the host's bale 0.4.51 read from the
  packing bale's help (the same version), not probed there again. The host's bale was 0.4.40 when 0.15.0 was built,
  below the floor; `office projects level-bale` is the step, and it ran
  against the suite's fakes only: the host's own 0.4.40 `upgrade.sh` was
  not read (0.4.51's was), so its first real run is its test. If that
  `upgrade.sh` does not take `-y`, it refuses before it changes anything.
- ~~A bundle for a hosted project must be given by its path.~~ Changed in
  0.16.0: a bare name is found in machine.toml's `downloads` (the office's
  own setting, asked once), since the office still cannot list bale's
  search directories (the same slip as above) and does not read bale's
  config.
- ~~A clarification on a hosted project goes back by a line land prints,
  `SHELL '...bale relay SID -' < ANSWER-FILE`, which you run here with the
  planner's answer saved as a file; no office verb carries it yet.~~
  Struck in 0.17.0: `office relay SID ANSWER-FILE` carries it, here or
  through the shell.
- A delivery is pushed from this machine, never from the host: the
  0.17.0 probe found the work host's credential helper (`cache`) empty,
  so a push from the clone there would prompt for a token on every
  delivery. The landed commits come here as a bundle through the shell
  and the audience answers with this machine's credentials. A push from
  the host is the known gap; a `mirror` declaration (a clone here that
  already holds the audience's history, sparing the temporary repo its
  fetch) is a follow-up if a project's history grows large. The whole
  crossing is tested against a bare repo on this machine as the audience
  and the suite's fake ssh as the host; the first real `office deliver`
  on a work project is its test on the real git host.
- The review's URL is known for GitHub-shaped hosts (github.com and
  instances named github.*) and GitLab; any other host gets the branch's
  name and the review's title to paste.
- The letterhead check's phrasing list is a seed; the office's own
  `letterhead/forbidden.txt` (a later space) is where the occupant's
  words go, and a false hit on a project's text is answered by changing
  the text or the list.
- ~~Each step of a hosted start is its own connection.~~ Since 0.16.0 one
  start or land reaches a host once and its reads share connections; a
  hosted start still makes about four (a bundle, eight, since its check
  runs in its own process before anything is written and the bundle
  travels twice), each a login shell (about 2.5 s on the work host). The
  first hosted land on a machine makes one more, reading its plan again
  after the downloads question.
- Through a login shell on a host, each connection costs what the
  user's profile costs (seconds, where this was built); the read side
  batches each round of reads into one connection, and a walk-in makes
  two per hosted project. ssh connection sharing (ControlMaster) would
  cut the handshake, not the login; the office does not set it.
- The fast tier's time was measured only in a two-core sandbox (55
  seconds; 91 with the 0.17.1 session's own additions). The first
  office-src apply on WSL is its test there; validation.sh prints the
  number, and `--fast` fails past 120 seconds. `tests/run.sh --detach`
  ran end to end in the sandbox, not yet from `office land`: the first
  landing after the after-land line is added is its test.

## Questions likely to come up

- *Where does a message I dropped go?* Into the in-tray, as its own page,
  until a session sorts it. Every session you send out carries it;
  `office start --drop in-tray/PAGE` sends it out on its own, and the
  walk-in's Next line names that line for the oldest one it can send.
- *Does dropping need a project?* No. The project helps the session that
  sorts it, and lets `office start --drop` go without asking; with none,
  start asks for the lane on a terminal.
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
- *My project's repo is on a work host, inside a container. How do I get
  it there and send a session to it?* `office projects add NAME --host
  USER@HOST --shell "ssh USER@HOST docker exec -i -u USER BOX bash -lc"
  --path ~/development/NAME --from ~/work/NAME` brings your clone there
  (with the VPN up), `office projects level-bale NAME` puts this
  machine's bale there, and `office start JOB --on NAME` sends sessions.
  The clone here can go once you are happy with the one there.
- *Where does `office land` look for a response?* For a project here,
  bale's own search finds it by name, as always; with `downloads` set in
  `~/.config/office-src/machine.toml` and several copies of the name
  there, land passes bale the newest and says which. For a project on a
  host, the path you give, or the newest copy in those downloads; the
  first time it needs them on a terminal it asks where they are and
  keeps the answer.
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

- *Did the whole suite pass after the last landing?* `cat
  ~/.local/state/office-src/suite/latest/verdict`: one line, `OK`,
  `FAILED` (with the log to read) or `BROKEN`, or `RUNNING since` while it
  runs. Nothing waits for it, and nothing reports it yet.
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
