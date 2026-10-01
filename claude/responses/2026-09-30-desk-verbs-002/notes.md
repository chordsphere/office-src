# Notes: 2026-09-30-desk-verbs-002 (blueprint session 4a, the desk's verbs)

office-src 0.5.0, additive. Everything in the brief's "What to build"
landed. Nothing ships outside the forecast. The suite went from 175 tests
to 227, and all of them pass.

## What the probe established

The nisaba-src context tarball did not arrive, so I probed for the
blueprint, as the brief said to. The probe found:

- **The blueprint.** `/home/chordsphere/nisaba-src/blueprints/drafting-table.md`
  at HEAD f0dee6f (master, "[bale sweep 2026-09-29-suite-merge-001]
  applied"). It was last touched by 94fcce3 on 2026-09-29. It has 1416
  lines, and its sha256 is
  f7bade8e5597fa9c404056553061f04246a21d940066beea2745e95efd27277a. The
  paste arrived with CRLF line endings; with them stripped, the hash
  matched exactly. I read §0, §1 (the intro and §1.5–§1.7), §2, the §3
  table, §3.6, §4, §5.3, §5.4, §7 and §8.
- **office-src.** VERSION 0.4.0, HEAD f6fb536 (the read-side sweep).
  Its only uncommitted paths are two untracked telemetry files.
- **The machine.** Bash 5.2.21 on WSL2.

The planner's word from the sitting was "this will fade, right?" It will:
4b is the last session that needs the blueprint carried in.

## Where the brief and the tree differ

- **`office init` had no wizard.** The brief says init has had one
  since 0.1.0. It did not: it refused without a path. It now asks for
  the path and the name, and it gained `--path` as the path's flag twin.
  init, `projects add`, open, close, reopen and sessions now share one
  function, `ask` in bin/office.
- **Function names.** Every name the brief cites exists. The reader's
  In flight is now `in_flight()` in lib/office_bale.py, with
  `render_in_flight()` kept as a thin wrapper.

## The wizard, question by question

`office open` on a terminal asks only for what it was not given, in this
order:

1. `Title, in a few words (--title) [SLUG]:` This is required. When a
   slug was given, a plain return takes the slug.
2. `Size: small, medium or high (--size) [return skips]:`
3. `Lane: the project and paths, as project: paths (--lane) [return skips]:`
4. `Source: where the job came from (--source) [return skips]:`
5. With `--filed` and no `--sid` only: `Session id it was done in (--sid):`,
   which is required.

How the questions behave:

- `?` explains the field.
- An answer the field does not take is explained and asked again.
- A flag value the field does not take (say `--size huge`) is explained,
  then asked on a terminal. Piped, it is refused, naming the flag.
- Class, blueprint, gates, consumer and linked are never asked. One log
  line names their flags, and `office open --help` explains every field.
- When no slug is given, it is made from the title as typed: at most 40
  characters, cut at a word.

The other verbs ask in the same shape:

- **init:** `(--path)`, then `(--name) [basename]`.
- **close, reopen, sessions:** with no folder given, they list the
  folders in the space, then ask `... (office close FOLDER):`.
- **`sessions --ratified` with no SID:** `Session id to ratify (SID):`.

Piped input is never asked anything.

## A folder with no number

The desk prints it by directory name only, where a numbered folder shows
`folder N  NAME`. For example:
`2026-09-29-older  next: ...  (sessions: 0)`.

Minting a number skips it. With `OFFICE_DEBUG=1`, open logs
`no number line, so not counted (and never numbered): desk/NAME`.

Nothing writes a number into it. close, reopen and sessions still update
its status line and History when it has them; a 0.3.0/0.4.0 folder has
both. A 0.2.0 folder has neither, and is moved untouched.

## The exact lines each verb writes

History lines take the form `- YYYY-MM-DD verb: text`, dated in the
office's timezone.

| verb | status line | History line(s) |
|---|---|---|
| `open` | `- status: queued` | `- D queued: office open` |
| `open --candidate` | `- status: candidate` | `- D candidate: office open --candidate` |
| `open --filed --sid SID` | `- status: done` (in filing-cabinet/) | `- D done: office open --filed, done at SID`, plus `- SID` in Sessions |
| `close` | `done` | `- D done: office close` |
| `close --into 14` | `absorbed` | `- D absorbed: into folder 14`; folder 14 gets `- D note: absorbed folder M (NAME)` |
| `close --split 14,15` | `split` | `- D split: into folders 14, 15`; each successor gets `- D note: split from folder M (NAME)` |
| `close --retired WHY` | `retired` | `- D retired: WHY` |
| `reopen` | `open` | `- D reopened: office reopen` |
| `sessions FOLDER SID` | `open`, on the first sid of a candidate or queued folder only | `- D opened: SID` |
| `sessions FOLDER SID --ratified [--except TEXT]` | unchanged | none; Sessions gains `- SID ratified D[, except: TEXT]` directly under the sid's line |

Open also writes the field block in the blueprint's order: number,
status, queued, class, size, lane, source, blueprint, linked, after,
serializes after, consumer. A field it was not given gets no line.
`render_template` now drops an unset `- key: {{x}}` line and renders a
list as one line per value, so the template shows the whole block.

## Gates on things the desk cannot read yet

A folder whose gate names a blueprint, an agenda item or a ruling is
parked under that name. For example:

```
Parked:
  waiting for agenda 7: not readable until the drafting-table verbs land
    folder 6  2026-10-01-gated  next: ...  (sessions: 0)
  parked for its consumer, blueprint 2026-10-01-twine: not readable until the drafting-table verbs land
    folder 8  ...
```

Other gates:

- A gate on a folder that does not exist, a gate line that does not
  read, or a cycle each heads its own `ERROR: ...` group. Its folders
  sit under that heading; none is dropped.
- A gate on an absorbed or split folder follows the successors.
- A gate on a retired folder parks the waiting folder with
  "(retired: WHY); it will not clear by itself".

## The reader and the fixtures

The one-writer rule and the office's own In flight line read
`bale status --json` (its `sessions` and `scopes`) in the office repo.
That is the call the fixtures carry, but captured in a project, not in
an office. So no new surface or key was needed, and
share/bale-consumption.toml is unchanged.

For the refusal tests I could not use a real capture: none exists of an
office with an open session. Instead, tests/test_desk_verbs.py
(`office_status_fixture`) builds one in a temp directory. It takes the
captured office-src status line, changes the values of `sessions` and
`scopes`, and sets it beside the real dossier of 2026-09-30-read-side-001.
claude/fixtures/ is untouched. Once home-office has been founded and
has run a session, a probe capturing `bale status --json` there should
replace this.

Nothing here is a slip for bale-src.

## Calls I made (also in feedback.judgment_calls)

- **What "holds the desk" means.** A forecast holds the desk when an
  entry is `desk`, a directory above it, or the whole tree. An entry
  inside the desk, like one folder's work session (`desk/{folder}`),
  does not hold it. Otherwise every work session would block
  `office open` for its whole life.
- **An unreadable registry warns and mints.** The office may have a
  `.bale/` but bale is missing or refuses. Then open says so loudly and
  mints anyway, because capture comes first. It refuses only on a
  session it can see. Say if you want this to refuse instead.
- **The walk-in day.** "Cleared since the last walk-in" needs
  something remembered. The walk-in keeps its office-local day under
  `$XDG_STATE_HOME/office-src/walk-ins/` (default ~/.local/state), on
  the machine and outside the office. OFFICE.md §7 now says so, since
  "it only reads" was the doctrine. The desk compares days, so a gate
  cleared earlier on the same day still shows.
- **Open folders with no session in flight.** They list in the In
  flight group, marked `[open, no session in flight]`. Otherwise an
  open folder between sessions would fall off the desk.
- **The History verb set.** It gains `candidate`, which the brief asked
  for; the blueprint's closed set had no verb for that state.
- **Plain close from queued.** Closing a queued (or candidate) folder
  writes done. The occupant can finish a job without a session. So the
  state machine is enforced only as status-agrees-with-History, not as
  transitions.
- **What reopen refuses.** It refuses an absorbed, split or retired
  folder, because only done comes back.
- **Naming folders.** A bare number in a gate flag means a folder.
  Every verb accepts `folder N`, or N alone when it matches no name.
- **The filed-page check skips the filing cabinet.** It keeps §15's
  older rule, since filed folders gain lines inside their sections.
  `.keep` counts as a file in that status line's tally.

## What the independent review found, and what I did

A separate agent reviewed the finished work. I fixed seven of its
findings and added a test for each:

- One unreadable folder.md took down the desk and the walk-in. It now
  lists under "Cannot be read".
- A malformed gate line crashed the desk. It is now an error line.
- `--split 2,2`, and a successor that is itself absorbed, split or
  retired, were accepted. Both are refused now.
- A multi-line `--title` could inject field lines. The title is now
  one line.
- close wrote its lines before finding the cabinet slot taken. It now
  checks first and writes nothing.
- A desk whose only folder was in flight said it was clear.
- A non-ASCII title made a slug from its escapes.

Two findings I left as they are:

- **The `lands` semantics in share/verbs.toml.** close lands
  `desk/{folder}`, which no longer exists after it runs. The suite pins
  lands equal to writes for scripts, a rule session 2 shipped as ruled,
  and `sessions` already reads its two patterns as "one of". Proposed
  below.
- **Unchecked transitions.** As above, this is deliberate.

## Validation

`validation.sh` runs the four test modules side by side, which brings
the wall time to the slowest module's: about two minutes here. Run one after
another, the suite takes about 3.5 minutes. In a simulated staging copy
of the request's tree, every check passes. On the unmodified tree, the
change-dependent assertions fail.

## Proposals

### Say what `lands` means for a script that moves a folder

- **What:** Rule what `lands` means for a script that moves or
  alternatively places a folder. Either "one of these" (what sessions
  and open now mean), or a narrower rule that lets close land
  `filing-cabinet/{folder}` alone. Then relax the suite's
  lands-equal-writes pin for those verbs.
- **Why:** verbs.toml defines lands as "guaranteed to exist after".
  After close, `desk/{folder}` does not exist. The review flagged this,
  and the pin keeps it.
- **Scope hints:** share/verbs.toml's header comment,
  `test_the_existing_verbs_took_the_keys_as_ruled`.

### `office note` should check the page's prefix before it commits

- **What:** Make `office note` check the page's prefix in-process
  before it commits, as §15 and the blueprint's §5.4 "In scripts" say
  every appending script does. It is the same code
  `filed_history_check` uses, `append_problem`.
- **Why:** The doctrine says it happens today, and it does not. The
  front sheet now lists this under Known problems.
- **Scope hints:** bin/office `cmd_note`. 4b's `watches check --record`
  will need the same function.

### Let 4b's `office moves` move a candidate to queued

- **What:** Let `office moves` (4b) carry `candidate -> queued`, writing
  a `queued` History line and the status line.
- **Why:** The blueprint gives that transition to moves, and nothing
  else in 0.5.0 makes it. A candidate can be closed or retired, but not
  promoted.
- **Scope hints:** reuse `folder_event` (bin/office) or
  `office_helper.folder_event`.

### Hand the desk's last group slot to 4b

- **What:** 4b adds the orphaned-riders and pending-moves groups to the
  desk's renderer.
- **Why:** The renderer has a marked place after Candidates.
  `classify_desk` and `desk_lines` in lib/office_bale.py are where they
  go. The walk-in's "N desk moves pending" line belongs in `desk_lines`
  with `walk_in=True`.

### Capture a real office registry once home-office runs a session

- **What:** Once home-office has run a session, probe `bale status --json`
  and one dossier there, into claude/fixtures/bale-0.4.45/home-office/.
  Then drop the derived status line in tests/test_desk_verbs.py.
- **Why:** The one-writer rule's tests run on values I set by hand. The
  shape is captured; the office case is not.
