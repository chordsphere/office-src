# Notes: 2026-10-03-friction-front-door-002, the front door (office-src 0.8.0)

The tree read VERSION 0.7.0, as the brief said, and both earlier sessions'
notes were where it said. No probe ran, and no light question block or
clarification was needed: the brief settled every intent question this
session met, and the one bale fact the Next line wanted is answered by the
help text bale already ships in the request (below).

## What arrived beside the request (the wave's first dogfooding evidence)

This is the first session `office start` sent out from home-office.
Beside the request came three context tarballs:

- **context-home-office**: `desk/2026-10-03-friction-front-door/folder.md`
  (folder 1, queued, source office-src), `profile.md` and
  `floor-plan/survey.md`. That is the folder and the hung items, as
  designed. Useful: it showed me a real folder and a real profile.
- **context-doctrine**: `doctrine/OFFICE.md` and its check. **Redundant for
  this project**: both are byte-identical to the copies inside the request,
  because office-src's own tree carries the doctrine. Harmless, but on
  every office-src session the doctrine arrives twice.
- **context-nisaba-src**: `blueprints/drafting-table.md`, 78 KB, which the
  brief says this session does not need. It rides because office-src
  declares it. A per-project declaration cannot say "not this time".

Missing: nothing this session needed. Confusing, two things:

- **The hung survey is stale.** It was taken on 2026-09-30 and says
  office-src 0.4.0 is installed, yet this session went out through `office
  start`, which 0.4.0 does not have. A session reading it would believe
  the wrong version. Nothing refreshes the survey before a pack.
- **The folder shipped is the one before the record.** Its Sessions
  section is empty, because `office start` records the session after the
  pack. Expected (session 1 said so), but a worker reading the folder
  sees no trace of its own session.

The folder's lane was empty, so the forecast came from somewhere else
(asked, or typed). The resolved scope is sensible, so whichever it was
worked. Proposals for all of this are at the end.

## The probe the brief named, and why none ran

The brief asked whether any bale `--json` surface says which responses
bale's search would find for an open session, or what its search paths
are. `BALE_HELP.md` answers it without a probe: `bale status --json`
carries `config.search_paths` as a **count** only (the captured
office-src fixture shows `"search_paths": 1`), and no other `--json`
surface lists the directories or what is in them. The one bale surface
that resolves a name through the search without a session is `bale apply
--show-validator NAME`, which prints a script, has no `--json`, and would
cost a bale run per session out on every walk-in. Doctrine section 10
says the office reads bale through its `--json` surfaces only, so I did
not use it. The Next line says the session is out and that land finds
its response, and the gap is a slip (below).

## Decisions to ratify

- **The Next line's order** (the brief left it to me):
  1. skew (behind: `office upgrade`; ahead or unreadable: `office status`),
     because start and land refuse until it is fixed;
  2. a session out (`office land SID`), held ones first, then oldest;
  3. unfounded (`office status`);
  4. the first ready folder (`office start NAME`, `--on PROJECT` when the
     lane names one of the office's projects);
  5. an open folder no session is out for (`office start NAME`, with
     "office close NAME instead when its job is done" in the words);
  6. no projects (`office projects add`);
  7. five or more slips (`office open triage-the-suggestion-box --title
     "Triage the suggestion box" --size small --source "the suggestion
     box"`), unless a folder of that slug is already waiting;
  8. folders that only wait, parked or candidates (`office desk`), and
     folders the desk cannot order;
  9. nothing (`office open`).

  Two deviations from the brief's listing, flagged:
  - **A session out comes before unfounded.** An unfounded office's
    founding session is itself a session out; telling the occupant the
    office is unfounded while the session that founds it waits to land
    would send him the wrong way. The founding session is counted even
    though no folder records it, because anything open in the office's own
    registry is the office's.
  - **No projects comes after a ready or open folder.** An office may
    scope nothing by choice (the doctrine allows it), and a nag above real
    work would never go away. With init now asking for projects, a new
    office usually has some.

  "A folder with no move" I read as "folders on the desk, none of them
  ready": parked and candidates, so the line is `office desk`. If you meant
  a folder whose Next section is unwritten, there is no verb that writes
  it, so the line would have nothing to name.
- **Unfounded says `office status`, not the founding line.** The founding
  pack line is printed once, by init, and nothing reprints it. Building a
  reprint is the founding door's job (out of scope), so the line names the
  command that shows what the profile lacks. It is on the front sheet.
- **One reading for the desk and the Next line.** `reader desk --walk-in`
  takes `--next-file`, `--skew` and `--founded` and writes the line to a
  temp file, so bale is asked each question once per walk-in (the reader's
  cache covers status and dossiers). The walk-in prints it last, after the
  "From here" line, which I kept (with a pointer to help and the tour). A
  Next line that cannot be worked out says so and points at OFFICE_DEBUG.
  With no office at all, the walk-in's Next is `office tour`.
- **Help.** `office help` groups by task in the brief's six groups, opens
  with the tour, and has a paragraph for bale users (the three "nevers",
  and bale staying visible: start's and land's help name the bale commands,
  `OFFICE_DEBUG=1` shows every call). `office help VERB` runs that verb's
  `--help`. Every verb's help has an Examples block. `status`, `where`,
  `default` and `version` gained `--help`; to make that safe, `status` and
  `where` now refuse stray arguments and `default` refuses more than one
  path, where they used to ignore them or misread `--help` as a path.
- **The tour.** Six steps (walk in, note, open, desk, week, then start and
  land shown, never run), each printing the command, its output, "What it
  did" and "Why you would type it". Isolation, beyond what the brief
  listed: OFFICE_ROOT on every command; its own XDG_CONFIG_HOME and
  XDG_STATE_HOME (so no default office or walk-in record is read or
  written); `GIT_CONFIG_GLOBAL=/dev/null` and a fixed git identity, so a
  global `commit.gpgsign` or a missing identity cannot break or touch it;
  a stand-in `bale` first on its PATH that refuses everything (exit 97),
  so even a mistake cannot reach a registry; a machine.toml of its own
  that puts the out tray inside the tour and turns the clipboard and
  Explorer off. It writes the sample profile itself (from the profile
  shape) so the office is founded and the walk-in's Next line demonstrates
  `office start`. The calendar gap is planned for yesterday (the first
  minute of today on a Monday), so it is always in the past and this week.
  Interrupted or terminated it says so and deletes; `q` at a pause ends it
  early and deletes.
- **The play shell is an addition; say if you want it gone.** At the end,
  on a terminal, the tour offers "Play in the tour office yourself before
  it goes?" (default no; `--play` and `--no-play` are the twins; piped it
  never plays and refuses `--play`). It is `bash --rcfile` with the tour's
  environment, a `(office tour)` prompt, and its history kept inside the
  tour; `exit` ends it and the office is deleted. This is the sandbox half
  of the toy drawer, "simply being in the office should feel like a
  space". The small fun: the tour's sample slip is "the tour should come
  with snacks". The fidget drawer itself is not here.
- **init's question.** After the first commit and the default, on a
  terminal, init asks "A project this office watches: the path to its repo
  (--project PATH)", then "Another project's path", each through
  `office projects add`'s own questions (path, name, rides, after-land),
  until a plain return. Each added project is its own commit (`office
  projects: add NAME`), as `projects add` makes. The flag twin is
  `--project PATH` or `--project NAME=PATH`, repeatable; every one is
  checked before anything is built (a new helper subcommand,
  `project-spec`), so a bad one builds nothing. `--no-projects` skips the
  question on a terminal. init's stdout stays the founding line alone.
- **`office projects add` now checks the path as soon as it is given**,
  and asks again with the reason, before asking the name and the
  declarations. Before, a wrong path was found only after all four
  answers. The doctrine already asks for this ("asks again, with the
  reason, when an answer is not one the field takes"). New helper
  subcommand `check-project-dir`.
- **The bundle refusal.** `bundle_forecast` reads the bundle's stored argv
  the way `bale pack` reads it, per `bale help pack`: `--write` and
  `--include` take several paths and repeat, `=`-glued forms count, the
  forecast is `--write`'s paths, else `--include`'s, else the whole tree,
  and `--read-only` is empty. An argv it cannot read as a pack line (an
  unknown flag, a stray positional) is passed through to bale with a line
  saying why, rather than guessed at. A `--supersedes SID` in the bundle
  clears that one session, as bale's gate does. The refusal opens with
  what the bundle forecasts, then the same lines as a pack's. When the
  bundle is a bare name bale finds, the office says it cannot read the
  forecast first, before bale runs. The office-session warning ("does not
  name the folder") now reads the parsed forecast too, so `--write desk`,
  a multi-path `--write` or `--write=...` are read right.
- **Refusal wording changed for packs too.** The 0.6.0 words said "bale
  apply its response, or bale unlock SID". They now say `office land SID`
  first, then `bale unlock SID, in REPO` for an abandoned one. The tests
  that pin the turn-taking sentence still pass.

## Look closely on review

- `cmd_tour`'s traps: INT and TERM/HUP traps print and `exit`, and the
  existing EXIT trap (`cleanup_tmp`) deletes the tour directory. Around the
  play shell the INT trap is `:` (a handler, not an ignore), so commands
  inside the shell can still be interrupted and the tour is not, then the
  exit trap is put back. Tested on a pty for ^C at a pause, SIGTERM at a
  pause, `q`, and the play shell. A ^C while a tour command is running
  waits for that command, then the trap fires. The pause reads with
  `read -t 1` in a loop: the SIGTERM test caught a real race, a signal
  landing between the prompt and bash's `read` waiting until the next
  keystroke, and a one-second read services the trap at once (the
  terminal hands over a line only on return, so nothing typed is lost).
  The tests' pty helper kills and fails a child still running after its
  last step, so a regression there fails instead of holding the suite.
- `init_ask_projects` and the flag loop run `cmd_projects_add` in a
  subshell with OFFICE_ROOT set and stdout sent to stderr, so a failing add
  never kills init and the founding line stays the only stdout line.
- `next_move` is a pure function over the state; `sessions_to_land` is the
  part that reads bale. A dossier that cannot be read keeps the session in
  the list, only its order unknown (logged at debug).
- The existing terminal test of init in `tests/test_desk_verbs.py` now
  answers the project question with a plain return; without that it waits
  forever on the pty. That is the one change to an existing test's
  behavior beyond the catalog pin (`tour` joins the prose writers) and the
  new page in `WORDS_SHA256`.
- The doctrine edits: the front sheet, section 4 (the bundle refusal),
  section 7 (the init row, the tour row, help by task, the Next line in the
  walk-in paragraph), section 10 (init adds projects) and section 12 (init
  asks). The verbatim bale/office paragraph and the append rule are
  untouched.

## Slips for bale-src (doctrine section 10)

1. **No `--json` surface names where bale looks for a response, or whether
   one is there.** `bale status --json` has `config.search_paths` as a
   count. A list of the directories, or for each open session the
   response tarballs the named search would find (the browser's `(1)`
   copies included), would let the walk-in say "its response is in your
   downloads: office land SID" instead of "when it is".

Sessions 1 and 2's eight slips stand as they were.

## Paths outside the write forecast

None. Every path is under the forecast the manifest stamps.

## The suite

The suite is now 344 tests; 38 of them are new, in
`tests/test_front_door.py` (the Next line as a pure function and on real
walk-ins against the return trip's fake bale, help by task, the tour piped
and on a pty, init's projects by flag and on a pty, `projects add`'s path
check, and the bundle refusal). It takes about eight minutes here,
and `validation.sh` runs it whole, past the two-minute target, as
`validation_will_run` says. The tour's tests put a recording fake bale on
the PATH and assert it was never called, that TMPDIR is empty after, and
that the real office, the default office, the config directory and the
walk-in record are byte for byte as they were.

`validation.sh` was run in a staging copy both ways:

- With the change applied (and `apply.sh`'s chmod), all thirteen checks
  pass and the seven claims agree.
- On the unmodified tree, the eight session assertions fail (syntax too,
  since the new test file is not there yet). The suite, the untouched
  earlier pages, the no-migration check and the exec bit pass on both, by
  design.

## Proposals

### Let a project's declarations say what rides only sometimes

- **What:** a per-session way to leave a declared ride-along out (a
  question in start's wizard, "these ride: keep all?", with a flag twin),
  or a declaration that rides only on office sessions about the project.
- **Why:** this session carried nisaba-src's 78 KB blueprint it did not
  need, and the doctrine twice, because office-src declares the first and
  its tree holds the second.
- **Scope hints:** `lib/office_bale.py` `start`, `bin/office` `cmd_start`,
  the `[projects.NAME]` declarations.

### Refresh, or at least flag, a stale survey before a pack

- **What:** `office start` re-runs the survey (or warns, naming the age and
  the office-src version it records) when the hung survey is older than a
  few days or names another office-src version than the install.
- **Why:** the survey that rode with this session says office-src 0.4.0;
  0.7.0 is installed. Hung items are what every session reads first.
- **Scope hints:** `bin/office` `cmd_start` and `write_survey`; doctrine
  section 13.

### The founding door: reprint the founding line

- **What:** with the founding door (already planned after 4b), give the
  unfounded office a command the Next line can name, so it says that
  command instead of `office status`.
- **Why:** the founding line is printed once, by init; an occupant who
  lost it has nothing to type.
- **Scope hints:** `next_move`'s unfounded branch, `founding_line`.

### File the search-path slip with the other eight

- **What:** add the slip above to the bale-src queue.
- **Why:** it is the one fact the Next line has to word around.
- **Scope hints:** bale-src's `format_status_json`.
