# Notes: 2026-10-13-office-drop-003 (office-src 0.19.0)

Everything the brief asked this session to build is here:

- `office drop` and the in-tray;
- every session `office start` sends out carries the unsorted drops;
- `office start --drop`;
- the walk-in's line, the desk's group and the Next rule;
- the doctrine's core paragraph with the pinned Sort format, and section
  5's and section 7's additions;
- the declarations, the README, RELEASES.md, the front sheet, VERSION
  0.19.0, and 32 new tests.

One deviation needs your ratification first: the example values in the
pinned formats (item 1 below). The rest are details the brief left to the
worker, flagged so you can correct any of them.

Before you apply: the probe I ran at the start found
`~/office-src/probe-output/` still there, untracked, as 0.18.0 left it.
This response ships nothing under it, so it only needs removing, from
anywhere: `rm -rf ~/office-src/probe-output`.

## Decisions to ratify

1. **The format examples use neutral values (a flagged deviation).** The
   brief pinned the drop page and the Sort subsection "to the byte". Its
   example values are the work office's: a colleague's name, a project
   of that office and its UI. office-src's own suite forbids exactly
   that. The text rule in tests/test_office.py (OFFICE_SPECIFIC, which
   has a `m10` pattern) keeps the brief's hosts, people and projects out
   of everything the repo holds. The manifest's first constraint says
   the same: office context never lands in this project. So the doctrine
   and templates/drop-brief.md carry the format with every key, every
   line and the order byte for byte as pinned, and illustrative values:
   - `### 2026-10-14-login-error.md`
   - `project: alpha`
   - `goal: Fix the login page's error on narrow screens`
   - `tell: the sender, in reply: fixed in the next release`

   The keys `office land` will read in the next session are unchanged:
   project, folder, goal, size, tell, facts, and `#### Brief`. A test,
   and an assertion in validation.sh, hold the doctrine's block and the
   brief template's block to the same bytes.
2. **The in-tray's base cell is "no; arrives with the first drop".**
   That is the brief's wording. The suite's space-table test only read
   `yes` and `renovation` in that column, so it now also reads `no`
   followed by the verb that brings the space (tests/test_office.py, one
   regex). The drafting table keeps its `renovation`.
3. **A lane may now be the project alone.** `--drop` writes the lane as
   the bare project name (`- lane: alpha`), since a drop says nothing
   about paths. `office start`, the desk's `--on` hint and the Next line
   now read a bare lane that names one of the office's projects as that
   project with no paths. Before, a lane without a colon named no
   project, and start asked where. office_helper's `lane_project`
   already allowed a bare name, so this brings the other two readers in
   line with it. If you would rather have `alpha:`, it is one line in
   `start_drop`.
4. **The retry line is `office start FOLDER --drop NAME`.** If the
   session does not go out after the folder is minted (bale refuses the
   pack, the host drops), the page is already in the folder. start's
   usual retry line would carry a `--brief` pointing at a temporary
   file. So `--drop` given with a folder finds the page in that folder's
   `drops/` and writes the brief again from it, with nothing minted or
   moved. The brief did not name this mode; the start's last line prints
   it.
5. **An office session from a bundle carries the drops beside it.** The
   brief says the drops go "in the pack's includes" for an office
   session, but the office adds nothing to a bundle's pack line (doctrine
   section 4). For that one case they ride as `context-in-tray.tar.gz`
   beside the request. A renovation that ships the whole office already
   holds them, and the tray's line says so.
6. **The opener's line goes after bale's own.** It comes after a blank
   line, as the opener's last line:
   - for a session: "N unsorted drop(s) from the office's in-tray ride
     with this session: read them before the work, and sort the ones you
     can judge in a Sort section of notes.md (doctrine section 4)";
   - for a sitting: "... read them; a sitting owes them no Sort".
7. **The Next rule goes strictly oldest first.** The oldest unsorted
   drop decides the line:
   - its project resolves: `office start --drop in-tray/PAGE`;
   - it does not, or it has none: the same line with `--lane LANE`.

   A drop whose project has a session in flight on a folder of its lane
   is passed over for the next oldest. An office that scopes no project
   skips the rule, since `--drop` needs a project to send the session to.
8. **"Resolves" means the project's name, in any case, alone or before a
   colon.** `Alpha` and `alpha: src` resolve to `alpha`. "the website"
   does not.
9. **Where the folder's names come from.** The folder's slug is the
   drop's (its page name without the date), so the folder and the page
   are named alike. The title is the drop's heading, and `--title`
   overrides it; with `--title` the slug comes from the title, as in
   `office open`.
10. **`--drop` refuses the flags that would contradict it:** `--on`,
    `--in-office`, `--read-only`, `--brief` and a bundle. `--title`,
    `--lane` and `--size` are refused without `--drop`. Everything else
    of start's works as it stands (`--goal`, `--slug`, `--write`,
    `--include`, `--leave-out`, `--no-rides`, `--carry`).
11. **The brief carries the drop's whole page between its markers.** That
    is the heading, the four fields and the text, between `--- DROP BEGIN
    drops/NAME.md ---` and `--- DROP END ---`. They are notepad-style, but
    deliberately not `NOTEPAD PAGE`, which `office start` would file in
    the notepad. A page that itself holds a marker line is refused rather
    than carried ambiguously.
12. **The heading is trimmed to 60 of the text's characters.** It is cut
    at a word and ends with `...` when longer, like a slip's title. The
    escapes are made after the trim, so a heading with accents can run
    past 60 bytes on disk.
13. **0.18.0's release test no longer pins VERSION to exactly 0.18.0.**
    tests/test_probe.py's `test_the_release` asserted equality, which
    fails every later release. It now asserts 0.18.0 or later with
    `compare_versions`, as every other release test does.
14. **VERSION is 0.19.0.** It adds a verb, a space and a flag, with no
    migration.

## Paths outside the forecast

The pack's include set did not reach `templates/`. The brief asks for
the in-tray's "front page from a template" and for start --drop's brief
"from a template in the install, beside the folder template". Both are
new files there:

- `templates/in-tray-README.md`: the in-tray's front page, made by the
  first drop (as `drafting-table-README.md` is by the drafting table's
  first verb).
- `templates/drop-brief.md`: the brief `office start --drop` sends,
  rendered with office_helper's `render_template`.

Nothing else outside the forecast changed. `templates/folder.md` is
untouched, and validation.sh checks its sha256 against HEAD's.

## What the probe established (TARBALL.md 4.5)

The paste-back probe office-drop-003 ran in `~/office-src` on
2026-10-13 (WSL2, bash 5.2.21). All 815 lines came
back, matching the integrity trailer. It established:

- HEAD is ecfbd34, VERSION 0.18.0. The working copy holds two untracked
  paths, `probe-output/` and this session's telemetry stub.
- `templates/` (20 files) and `migrations/` (3 files) at HEAD. I rebuilt
  them from the paste, and every file's sha256 matched the one the probe
  printed.
- Git's blob id for every tracked file outside `claude/` matched my copy
  of the request's tree, so the tree I built and tested against is HEAD
  byte for byte. The one exception is `.gitignore`, which the request
  did not carry; its blob id gave its two lines.
- The only migration is 0.2.0's. A release is breaking only when it
  ships one (migrations/README.md), so 0.19.0, with none, is additive:
  an office that never drops anything never changes.

## Where to look closely

- `bin/office`, `start_drop` (just above `cmd_start`). This is the whole
  direct path. Every refusal comes before the first write:
  - the page and its status;
  - the lane, asked or refused;
  - the size and the title;
  - the one-writer rule over `in-tray` and `desk`;
  - the host's reach.

  Then come `cmd_open` (office open's own code, in a subshell), the move,
  the `dropped` History line, and one commit of the folder and the page's
  removal.
- `lib/office_bale.py`, `start()`: the ride-along block, after the
  sitting's drafting-table include. It picks the place for each kind of
  session, adds the drops to the office's context tarball for a project
  session, and adds the opener line. The returned dict gains `drops`.
- `lib/office_drop.py`: the page (render, parse), the arrival, the
  listing, `tray_check` for `office status`, and the brief. The arrival
  runs the drafting table's own helpers. `catalog_entry`,
  `floor_plan_block` and `add_space_to_floor_plan` in
  lib/office_drafting.py now take `space=` (defaulting to the drafting
  table, so every existing caller is unchanged).
- The doctrine's core: the new last bullet of section 4's list, 13 lines
  of prose, then the format. The banner moved from line 196 to 231. That
  is under the core test's 300, and inside its quarter-of-the-doc rule
  (231 × 4 = 924 against 1,167 lines).

## Tests and the suite's clock

- tests/test_drop.py, 32 tests, all new:
  - the page as units;
  - the verb piped, from a file and from the clipboard on a terminal
    (and with the clipboard turned off);
  - status;
  - the ride-along for a project session, an office session and a
    sitting;
  - `--drop` end to end, its refusals, the one-writer rule, the retry
    line, and the lane and size asked on a terminal;
  - the walk-in, the desk and the Next rule;
  - the doctrine, the brief, the declarations and the release.
- The fast tier gained `drop`'s entry point, the three cheap classes
  (TestThePage, TestTheNextRule, TestDoctrineAndDeclarations) and three
  of the costly ones that guard the most:
  - the project-session ride-along;
  - `--drop` end to end;
  - the one-writer refusal.

  The rest of test_drop waits for `--slow` and the detached run. The
  terminal ones take 5 to 21 seconds each here.
- In this sandbox (two cores), all times measured with the change
  applied unless noted:

  | run | tests | wall clock |
  |---|---|---|
  | fast tier, request's tree, unchanged | 297 | 74.7 s |
  | fast tier, changed tree | 313 | 92.4 s |
  | validation.sh, staging copy | (fast tier plus its checks) | 93 s |

  validation.sh stays inside the 120-second budget. Your machine ran the
  old tier in 70.9 s, so expect roughly 90 s there.
- On the unmodified tree, validation.sh's three change assertions fail,
  as they should. The fourth, `templates/folder.md is untouched`, passes
  on both: it guards a file the brief pinned as unchanged, so passing on
  both is its job.
- The whole suite, here: the request's tree, 733 tests OK in 27.5
  minutes (it shared the cores with my work). The changed tree ran 764
  tests in 24.4 minutes, and one failed: the piped tour test counted one
  "What it did" paragraph per step, and the capture step now has two,
  for note and drop. tests/test_front_door.py now expects six, and
  checks the drop's command line and the in-tray's arrival. Its module
  then ran OK whole (28 tests, and 10 in its share of the serial lane),
  and the fast tier with the tour class beside it was OK, 315 tests in
  94.5 seconds.

## Proposals

- **What:** the digest (the page a sitting opens on) could list the
  unsorted drops, as the walk-in and the desk now do. **Why:** a sitting
  carries them already and owes them no Sort, but the digest is where a
  sitting looks first, and a drop that has waited a week is a sitting's
  business. **Scope hints:** lib/office_digest.py, its desk section;
  `office_drop.unsorted` is the reader.
- **What:** the next session's `office land` can set a drop's status
  from what a Sort says. The page's status line is the only field that
  changes, and only the office command writes it. **Why:** until then a
  sorted drop keeps riding with every session. The front sheet lists
  this as a known problem. **Scope hints:** lib/office_drop.py has
  `parse_page` and the field order. A `set_status(path, "sorted")` beside
  `render_page` keeps the one writer in one module. `resolve_page`
  already finds a page in the in-tray or in a folder's `drops/`.
- **What:** `office drop --title TEXT`, a heading other than the
  message's first line. **Why:** a message that opens "Hi," is titled
  "Hi,", and so is the folder `--drop` mints from it (`office start
  --drop --title` already overrides the folder's). It is not judgment,
  only the occupant's own words, so capture stays dumb. **Scope hints:**
  `cmd_drop` and `render_page`'s heading.

## Walkthrough

### What changed

- `office drop [FILE | -] [--project TEXT]`, a new verb (bin/office,
  lib/office_drop.py). It takes a message or a thread:
  - from a file;
  - from stdin;
  - or, on a terminal with neither, from the clipboard (machine.toml's
    `paste_command`, 0.18.0's key).

  It writes one page in the new in-tray, `in-tray/DATE-SLUG.md`. The page
  is the first line as its heading, then `dropped`, `project` (your
  words, or `none given`), `via` and `status: unsorted`, then the text
  verbatim under `## Text`. It is committed alone. It says what it took
  (the first line and the line count), and it asks one optional
  question, the project, with your projects as hints.
- The in-tray arrives with the first drop: a front page from
  `templates/in-tray-README.md`, the floor plan's entry and bale.toml's
  trigger. `office status` checks it.
- `office start` carries every unsorted drop with every session it sends
  out:
  - in the request, for an office session;
  - in the office's context, for a project session;
  - beside it, for an office bundle.

  The out tray's listing and the opener say how many ride.
- `office start --drop in-tray/PAGE` mints the folder through office
  open's code, with:
  - the title from the drop;
  - the lane from its project, or asked;
  - the size asked, small by default;
  - the source `drop`.

  It moves the page into the folder's `drops/` and writes `- DATE
  dropped: drops/NAME.md, via ...` in the folder's History. Then it sends
  a project session out with the goal "Sort the dropped message and do
  what it asks" and a brief that says: sort first, then do the work.
- The walk-in adds `In-tray: N unsorted drop(s), the oldest K days old`.
  `office desk` lists the drops after the candidates. The Next line names
  `office start --drop` for the oldest drop it can send.
- The doctrine's core tells a build session what it owes the drops it
  carries: a `## Sort` section in notes.md, one subsection per drop, in
  a pinned format. Sections 5 and 7 describe the in-tray, the verb,
  start's carry and `--drop`, the walk-in's line and the Next rule.
- share/verbs.toml declares `drop`, and share/spaces.toml the in-tray.
  The tour's capture step shows a drop.

### Why

The day a message arrives used to cost you a sitting's worth of work
before any work started. You read it, decided what part of which project
it meant, wrote a note, filed it, opened a folder and wrote a brief. Now
you drop it as it is, and a session with the code in front of it does
the deciding. A routine ask is three commands: `office drop`, `office
start --drop`, `office land`. Anything you drop and do not send out
yourself still reaches a session, because every session carries the
unsorted drops and sorts the ones it can.

### How to explain each piece

- office drop: "Copy the message, type `office drop`, say which project
  if you know. It's saved and committed; nothing else happens."
- The in-tray: "Messages waiting to be dealt with, one page each. It
  shows up the first time you drop something."
- The ride-along: "Every session I send out takes the waiting messages
  with it, and whichever ones it understands, it sorts."
- start --drop: "That one message becomes its own job: a folder, the
  message moved into it, and a session that works out what's being asked
  and then does it."
- The Next line: "When a message is waiting and nothing else comes
  first, the last line of the walk-in is the command that sends it out."

### Questions a reviewer will ask

- Does a drop ever get refused? Only when there is nothing to write: an
  empty text, a file that is not there, or an unknown flag. It warns in
  an unfounded office, or one behind or ahead of the install, and writes
  anyway, as a note does.
- Who writes a drop's field lines? Only the office command: `office
  drop` writes them. The next release's `office land` will change
  `status`.
- What if a session is open on the office? `office drop` writes anyway,
  as a note does. Capture is instant. `office start --drop` refuses while
  an open session forecasts the in-tray or the desk, and names it.
- What does a carried drop cost a session? A page or two of reading. Its
  goal is unchanged, and a sitting owes them nothing.
- What if the session does not go out after `--drop` minted the folder?
  The folder stays, with the drop in it, and the last line is `office
  start FOLDER --drop NAME`, which retries it.
- Is anything sorted filed yet? No. That is the next session's job.

### A hand test

1. Install and land as usual. Remove `~/office-src/probe-output` first
   if it is still there.
2. In home-office, copy any short message to the clipboard (two lines,
   say "Could you add a dry-run flag to office drop? / It would help
   testing."). Run `office drop`. Check that:
   - it says `took 2 line(s) from the clipboard: Could you add...`;
   - it asks `Which project it is for, in any words (..., or anything)
     (--project)`. Answer `office-src`;
   - it prints `in-tray/DATE-could-you-add-a-dry-run-flag-to-office.md`.
3. Open that page and check its fields:
   - `# Drop: Could you add a dry-run flag to office drop?`;
   - `- dropped: DATE TIME` in the office's timezone;
   - `- project: office-src`;
   - `- via: clipboard`;
   - `- status: unsorted`;
   - `## Text`, then your two lines, nothing mangled.

   `git log -1 --stat` shows the page, `in-tray/README.md`, the floor
   plan and bale.toml in one commit, since this is the first drop.
4. Walk in (`office`). Check that:
   - a line reads `In-tray: 1 unsorted drop(s), the oldest dropped
     today (office desk lists them)`;
   - with nothing out and no moves pending, the Next line reads `Next:
     office start --drop in-tray/DATE-...md`.
5. Run `office start --drop in-tray/DATE-...md`. It asks the size
   (return takes small), then the paths office-src's session may change
   (return takes the whole repo), then what rides, if office-src declares
   any. Check that:
   - a new folder is on the desk, its lane `office-src`, source `drop`;
   - `in-tray/` holds only its README;
   - the folder holds `drops/DATE-...md`, and its History has `dropped:`
     above `opened:`;
   - the out tray's request has a README.md that begins "Brief: sort the
     dropped message" and carries your page between the DROP markers;
   - the opener's goal line reads "Sort the dropped message and do what
     it asks".

   Close the folder or land the session as you like; it is a real
   session on office-src.
6. Drop a second message with no project, then start any other session.
   Check that:
   - the tray's listing has the line `(1 unsorted drop(s) from the
     in-tray ride ...)`;
   - the opener ends with the drops line.

## Delivery

- to: nobody: office-src has no audience

### Commit

Add office drop and the in-tray, and send a drop straight out

office drop captures a message or a thread as one page in a new space,
the in-tray, with an optional free-text project. The text comes from the
clipboard, a file or stdin. The page holds the first line as its
heading, its dropped, project, via and status lines, and the text
verbatim. It never refuses a text it can write. The in-tray arrives with
the first drop, as the drafting table does with its first verb.

office start carries every unsorted drop with every session it sends
out, in the request or beside it, and says how many in the tray and the
opener. The doctrine tells a session to sort the drops it can judge in a
Sort section of its notes, in a pinned format.

office start --drop sends one drop out as a project session. It mints
the folder through office open's code, moves the page into the folder's
drops/, and packs the session with a brief that says to sort the message
first and do the work second. The walk-in counts the unsorted drops, the
desk lists them, and the Next line names the start for the oldest one.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.
