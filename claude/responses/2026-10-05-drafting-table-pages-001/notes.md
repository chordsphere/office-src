# Notes: 2026-10-05-drafting-table-pages-001 (office-src 0.10.0)

## The HOLD, and this correction

The first response was held. Five tests errored, every one of them in
`test_second_trip.TestATimezoneThatDoesNotResolve`, and all in its
`setUp`. Nothing in 0.10.0 touches that class. It broke because your
machine's own zone changed: the probe's survey showed `timezone.system`
going from Etc/UTC to America/Indianapolis after 0.9.0 landed.

`office init` takes the machine's zone (`/etc/timezone`). So on your
machine the test's new office already says America/Indianapolis, the
test's rewrite of that line changes nothing, and its `git commit -am`
exits 1 with nothing to commit. I reproduced it here by setting this
machine's `/etc/timezone` to America/Indianapolis: the same five errors.

The fix is in the test: its setUp commit allows an empty commit (`git
commit --allow-empty -am`), so the class tests the same thing on either
kind of machine. `office init` reading the machine's zone is right and
stays. I re-ran the whole suite in a fresh staging copy with this
machine's zone set as yours is; the result is under "The suite" below.
`tests/test_second_trip.py` is the one path this correction adds.

4b-1 is built as one additive release, 0.10.0. The drafting table now
arrives in an office the first time a verb writes it. Every piece the
brief listed is in: `office moves`; the blueprint verbs; the rider,
agenda, rulings and evidence verbs; the desk's last two groups and its
drafting-table gates; `office status`'s charter and drafting-table
checks; the one-writer rule on every minting or appending script; and
the `office slip` title fix. The pre-flight said it fit one session, so
I didn't offer the brief's split. Nothing was written outside the
forecast (`resolved_scope` is `["."]`).

## What the probe established (2026-10-05, 00:26 UTC)

- **The blueprint arrived** as context (`nisaba-src/blueprints/drafting-table.md`).
  I built from it, not from memory.
- **office-src**: VERSION 0.9.0, installed (`INSTALLED`: commit `181f29e`,
  installed 2026-10-04T02:48:35Z, source `~/office-src`). The tree is
  clean except this session's telemetry record. The only session open
  is this one, scope `["."]`.
- **home-office**: one session is open, the read-only plan-4b sitting
  (scope `[]`). Two sessions are applied, the latest
  `2026-10-04-bale-src-slips-001`. There is no `drafting-table/`. Folder
  4, `2026-10-04-drafting-table-pages`, is this session's. The floor plan
  lists the seven base spaces, then the projects' comment and the
  `[projects]` tables, which is the shape the arrival code inserts into.
  bale.toml's triggers are the seven base spaces.
- **How bale writes history**: the session's work is committed as
  `[bale SID] summary`, merged as `Merge bale SID` tagged `applied/SID`,
  and swept as `[bale sweep SID] applied`. `git blame` of a slip page
  names the `[bale SID]` commit. `office moves` and the desk use exactly
  that to name the session that wrote a pending move.
- **Three captures**, verified line by line against the probe's
  sha256s, are now `claude/fixtures/bale-0.4.45/home-office/` with a
  README: `status --json` and the dossiers of the slips session and the
  sitting. They are the first captures of an office's own registry.
- The sitting's dossier says `record.read_only: false` although its
  scope is `[]`. This is the slip home-office already holds
  (`2026-10-03-4-the-dossier-s-record-read-only-is.md`), now confirmed
  on a real office. The office reads read-only from the scope, as
  before.

## Decisions to ratify

1. **How the drafting table arrives: the brief's third reading, as
   leaned.** The first verb that writes the space makes it. That means
   `drafting-table/README.md` from the template, the floor plan's
   `[spaces.drafting-table]` copied from the catalog (so status's and
   upgrade's filed checks read its filed list), and `drafting-table`
   added to bale.toml's include-group triggers (otherwise status reports
   drift). Each page is made from its template on its first write. All
   of it lands in the same commit as the write that asked for it, and
   nothing that exists is ever rewritten. No migration, so the release
   is additive.
   - **The contradiction I found, and how I resolved it.** Doctrine
     section 5 said "the others are added by a renovation session" and
     "a renovation copies them in when the space arrives". I changed both
     to say the drafting table arrives with a verb, and recorded it as a
     front-sheet known problem.
   - **The floor plan's own header** says only renovation sessions and
     `office projects` change it. `office projects add` is already a
     script that writes it, so I took that as precedent. New offices'
     header now names the drafting table's arrival. Existing offices'
     headers are not touched.
   - **`office upgrade` and the `renovate` kind are unchanged.** Upgrade
     never brings this space.
   - **The insert is checked by parsing.** Arrival puts the new table
     after the last `[spaces.*]` table and before the comment that
     precedes `[projects]`. It then parses the result and refuses if
     anything else would read differently.
2. **`templates/blueprint.md` is now a real template** (`{{charter}}` and
   `{{history}}`). The illustrative decomposition, ratified and history
   lines are gone from it. The ratified-line rule moved to the drafting
   table's README template. A charter nobody has written is one
   placeholder line (`office_drafting.CHARTER_PLACEHOLDER`), and ratify
   refuses a charter that holds only that.
3. **The move grammar.**
   - The verbs are `open "TITLE" key=value...`, `queue folder N`,
     `gate folder N after=/serializes-after=/consumer=`, `close folder
     N`, `absorb folder N into=`, `split folder N into="A,B"` and
     `retire folder N why=`. Values are quoted the way a shell quotes
     them (shlex).
   - Every applied line is ticked `-> folder N` with the folder it acted
     on, not only opens, so a ticked line always says what it touched.
   - An `open` with `blueprint=` must find its decomposition line,
     either by its goal word for word or by `line=N`. Otherwise the line
     is refused before anything runs. That is strict; the alternative
     was opening a member folder silently unconnected to the
     decomposition.
   - The moves template now lists the whole grammar, since sittings read
     the page.
4. **How `office moves` applies.**
   - It parses every pending line first, so a line that does not read
     stops the run with nothing applied. Then it applies in order and
     stops at the first line that cannot apply, naming it. The lines
     before it stay applied and are committed.
   - It applies through the verbs' own code: `cmd_open`, `cmd_close` and
     a new `helper folder-gate`, each in a subshell with stdin closed.
     `commit_paths` gained a deferral, `DEFER_COMMITS`, so a run is one
     commit (`office moves: N desk move(s) from drafting-table/moves.md`),
     not one per verb.
   - A move's History text names its line and the day the sitting
     decided it, and for a blueprint member, the decomposition line too.
5. **`blueprint close`.**
   - It sends the close sitting out through `cmd_start` itself.
   - The close gets its own folder: `close-SLUG`, titled `Close blueprint
     ID`, with `source: blueprint ID`, `blueprint: ID`, class meta and
     size small. A folder like that already on the desk is reused.
   - It ships the blueprint, its member folders (the `blueprint:` field
     plus decomposition lines naming a folder) and whichever of
     rulings, evidence and watches exist.
   - It forecasts the folder, the notepad and `drafting-table`, and
     passes a generated brief saying what lands.
   - The close report's template rides as one more context tarball,
     made from a scratch copy of the install. To allow that, `office
     start` grew an internal `START_INSTALL_FILES` and the reader's start
     grew `--install-file`. Neither is a user-facing flag.
   - `blueprint-close` leaves `DECLARED_KINDS` and is `built = true`.
6. **Riders.**
   - An orphan is a rider in any filing-cabinet folder (done, absorbed,
     split or retired) that is not consumed, moot or standing, not only
     one in a done folder. A rider stranded in a retired folder is just
     as lost.
   - `rider consumed` on a cabinet folder only adds lines (doctrine
     section 15), so its `status:` field keeps its old value. The dated
     lines are the record and every reader takes the last one. This is
     on the front sheet.
   - A title left out of `rider add` is the text's first line, cleaned
     like a slip's.
7. **Agenda.**
   - Entries go above `## Disposed`, so this is not an append. I added
     `helper append-check --insertion`: exactly one run of bytes
     inserted, nothing else changed. `agenda add` runs it before the
     commit; `rider add` runs the plain append check.
   - Numbers count disposed items too, so they are never reused.
   - A one-line question that is its own title is written once, not
     twice.
8. **Rulings.**
   - A derivation is written `## ID - derived - DATE` with `- into:`,
     mirroring evidence. The blueprint names the field
     (`derived-into:`) but not how a derivation record names its
     ruling. The rulings template now says this, and both `into` and
     `derived-into` are read.
   - `office rulings --check` exits 1 when a citation does not resolve.
   - Session ids are checked against what the office's own registry and
     its readable projects list (outboxes and open sessions), and are
     reported apart, because a repo the office does not scope may hold
     them.
   - A notepad citation is a dated page (`notepad/DATE[-SLUG].md`), so
     the templates' `notepad/PAGE.md` placeholders are not flagged.
9. **Gates.** A drafting-table gate naming nothing (no such blueprint,
   agenda item or ruling) is an error line, as blueprint 2.3 says.
   - A gate on a ruling that has not been minted yet is therefore an
     error, not a wait. Ruling ids are minted by the sitting that writes
     them, so a folder cannot name one in advance.
   - I changed `test_desk_verbs`' expectation for agenda 7 and the
     twine-courier blueprint from "not readable yet" to these error
     lines.
10. **Help.** The new verbs have their own group, "Plan work too big for
    one folder (the drafting table)", between "Start a job" and "Send a
    session out". Two-word verbs answer `office help blueprint open` and
    `office help blueprint-open` alike, and their verbs.toml keys are
    hyphenated. I taught the help test and the doctrine-table test to
    read them that way.
11. **`office desk --blueprint ID`**, which the blueprint template's
    Ordering section has always named, is built. It shows the arc's
    members in the desk's order, the members already filed, and the
    decomposition lines with no folder yet.
12. **The Next line is unchanged**, as the brief preferred. The proposal
    below says where pending moves would go.
13. **An unreadable registry warns and proceeds** for every new script,
    as `office open` already does. Capture-like scripts never stop on a
    registry they cannot read.

## Look closely on review

- **`cmd_moves`'s loop** (bin/office). Each move runs in a subshell
  reading the plan from fd 3, with fields separated by `\x1e` and
  arguments by `\x1f`. Tabs would have collapsed empty fields. A die
  inside `cmd_open`/`cmd_close` ends only that subshell, and the loop
  records the stopped line.
- **`DEFER_COMMITS` in `commit_paths`.** Any verb run while it is set
  writes paths instead of committing. It is set only inside `cmd_moves`
  and cleared before its own commit.
- **`charter_check`** walks `git log --reverse` per blueprint. The
  first commit whose charter has a ratified line is the base. Every
  later commit that changes the charter is a problem, and so is an
  uncommitted change against the last commit.
- **`rider_blocks`.** A block runs from `### rider N - title` to the
  next heading, the next pointer line or the section's end. A rider body
  containing a line starting with `#` would end it early. Proposal text
  does not have such lines, but the rule is worth knowing.
- **Two title cleaners.** The slip fix is `title_words`, a sed in
  bin/office, as the brief's "two lines in `cmd_slip`" asked.
  `office_drafting.clean_title` does the same in Python for riders and
  agenda items. Both are tested on the quoted case.
- **The `[bale SID]` commit convention.** The office now relies on it
  (git blame of moves.md) without bale declaring it anywhere. It reads
  git, not `.bale/`, but it is a dependency `share/bale-consumption.toml`
  does not name. See the slip below.

## Slips for bale-src

- **New:** bale's commit subjects (`[bale SID] ...`, `Merge bale SID`,
  `[bale sweep SID] ...`) are a convention, not a contract. Nothing
  declares them, and no `--json` surface says which session's commit
  wrote a path. `office moves` and the walk-in name the session that
  wrote a pending desk move from the subject. Either declaring the
  subject shape, or a dossier key listing a session's commits, would
  make that a reading of bale's records rather than of its habits.
- **Confirmed, already in home-office's box:** the dossier's
  `record.read_only` is false for a session packed with an empty scope
  (the plan-4b sitting, captured).
- **Still waiting from 0.9.0's notes, not re-filed:** `bale unlock
  --help` and the sweep commit; no after-land hook on bale's side.

## Paths outside the forecast

None. The forecast is the whole repo.

## The suite

`validation.sh` runs the whole suite, as the brief asks, and says so in
`validation_will_run`. On the machine I built on, the 407 tests took
about twenty minutes in a staging copy, all passing. The suite already
took about fifteen before this session: nine modules, each building
real offices in git.

After the HOLD I ran the corrected validation.sh again, in a fresh
staging copy of the packed tree with this machine's `/etc/timezone` and
`/etc/localtime` set to America/Indianapolis, as yours are. Every check
passed, and all 407 tests passed in about sixteen minutes. That is well past
TARBALL.md 7.6's two-minute target. I followed the brief over the
budget rather than gating it behind `--slow`;
`VALIDATION_SKIP_SUITE=1` skips it loudly for a quick run of the other
checks.

- **New:** `tests/test_drafting_table.py`, 27 tests. They cover arrival
  (including on a home-office-shaped floor plan, byte for byte), every
  rider, agenda and blueprint verb with its refusals, `blueprint close`
  through the fake packing bale, `moves` (all seven moves, a line that
  does not read, a line that cannot apply, attribution, dry run), the
  desk's three drafting-table gates (waiting, met and cleared, error),
  `desk --blueprint`, rulings and evidence rendering and the check, the
  one-writer rule on five scripts, a terminal run of `rider add`, and
  the slip title.
- **Changed:** `test_office.py` (`DECLARED_KINDS` loses
  `blueprint-close`, the new verbs' keys are checked against blueprint
  section 3's table, two-word verbs in help and in the doctrine table),
  `test_front_door.py` (the new help group, two-word help), and
  `test_desk_verbs.py`. In that file the derived status line now comes
  from home-office's capture rather than a project's. A new test
  replays home-office's registry exactly as captured: the read-only
  sitting holds nothing, and In flight shows it with the line that
  ends it.
- **Not dropped:** the derived line itself, despite the 4a proposal
  "drop the derived status line". Every refusal test needs a session
  open whose forecast holds the desk or the drafting table, and no
  captured office registry has one. So the line is now home-office's,
  with only `sessions` and `scopes` set by the test. If you want it gone
  entirely, the next probe of home-office has to catch an office session
  in flight.

## Proposals

### Put pending desk moves on the Next line

- **What:** In `next_move`, after "a session out" and before
  "unfounded": `office moves` while any move is pending.
- **Why:** Until the moves run, the desk's order is not the one the
  sitting decided. The Next line could name `office start` on a folder
  a pending move retires, or skip the folder a move just opened. I left
  the order as 0.8.0 ruled it, per the brief.
- **Scope hints:** `lib/office_bale.py` `next_move` (groups already
  carries `moves`), its docstring order, and doctrine section 7's
  Next-line paragraph.

### Let `office start` offer the riders a pack would carry

- **What:** When `office start` packs on a project, run `office riders
  --forecast` over the pack's forecast. On a terminal it would offer to
  carry each matching rider into the folder (`rider carry`) before the
  pack, so the rider rides in the request.
- **Why:** `--forecast` exists now and nothing calls it but a sitting by
  hand. The blueprint's "the pack line can carry them" is the office's
  job once start writes the pack.
- **Scope hints:** `bin/office` `cmd_start`; `lib/office_drafting.py`
  `render_riders`; after 4b-2, which also touches start's neighbours.

### Declare the `[bale SID]` commit subject in the consumption manifest

- **What:** Until bale-src answers the slip above, name the subject
  shape the office reads in `share/bale-consumption.toml`, as a
  non-calling entry like the relay markers, with a test against the
  probe's captured subjects.
- **Why:** That is how every other bale shape the office reads is held
  to a version. Today a change in bale's commit subjects would turn the
  attribution into "commit abc1234" with no test failing.
- **Scope hints:** `share/bale-consumption.toml`,
  `office_drafting.move_sources`, `tests/test_read_side.py`'s
  consumption checks.
