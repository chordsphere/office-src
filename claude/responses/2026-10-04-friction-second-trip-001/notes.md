# Notes: 2026-10-04-friction-second-trip-001 (office-src 0.9.0)

The five frictions are fixed in one additive release, 0.9.0, and item 6 has
an answer: the office's code cannot have left a declared `./install.sh`
unrun without printing a line, so 0.8.0's install stayed put because of
what happened at your terminal. I can't tell from what the probe read which
of two things it was (see item 6). Either way, land's last lines and a new
`office status` line now make it visible.

## What the probe established (2026-10-04, about 01:18 UTC)

- **The install is now 0.8.0.** `INSTALLED` says `commit: c91ebcf`,
  `installed_at: 2026-10-04T00:23:43Z`, so you ran `./install.sh` before
  sending this session out, as the sitting asked. The install's
  `doctrine/OFFICE.md` and the tree's are byte-identical (sha256
  `c16df9cd...`).
- **`after_land = ["./install.sh"]` was declared at 2026-10-03T03:10:08Z**
  (home-office commit `4afe45a`, "office projects: set office-src"). 0.8.0
  was applied at 23:38:40Z the same day (merge `7a6ca4a`, tag
  `applied/2026-10-03-friction-front-door-002`). The action was in place
  more than twenty hours before the landing.
- **The land code 0.7.0 ran is the code 0.8.0 ships.** Function by
  function, between the two `applied/` tags: `run_after_land`,
  `plan_field`, `cmd_land`, `open_anywhere`, `sessions_out`, `land_plan`,
  `land_outcome`, `outcome_words`, `land_main`, `Reader.interact` and
  `read_projects` are byte-identical. So reading today's tree was reading
  what ran that night.
- **No office commit marks the landing.** Folder 1
  (`2026-10-03-friction-front-door`) records the session and nothing after
  it: no ratification, no other line. For a project session, `office land`
  writes nothing in the office unless you ratify, so this proves nothing in
  either direction.
- **Shell history:** two `cd ~/office-src/` + `bale apply` pairs (lines
  1672-1673 and 1725-1726), then `cd ~/office-src/` + `./install.sh`
  (1766-1767). None of the 30 matching lines is `office land`. But none is
  `office start` either, and office start certainly ran at 03:11
  (home-office commits `1364cdf`, `c86c096`), so the history is incomplete
  (a shell that never exited, or a terminal closed without writing it).
  It cannot settle the question.
- **bale unlock**, in a throwaway repo (17 captures, now
  `claude/fixtures/bale-0.4.45/unlock/`): exit 0, one JSON line on stdout
  (`outcome: unlocked`, `closure_reason: closed-read-only` inferred from the
  empty scope, and a `sweep` object), the human lines on stderr. It asks
  nothing on a terminal: the probe's single default return was never
  needed. Its sweep commits the session's telemetry record alone, as
  `[bale sweep SID] closed-read-only`, and leaves an edited tracked file and
  an untracked one exactly as they were. A second unlock of the same sid
  exits 1 with `is not open; nothing to unlock`. That matches the sitting's
  closing commit in office-src, `c91ebcf`, which touched one file, the
  sitting's telemetry record.
- `office status` in home-office: survey 3 days old; the timezone resolves
  (tzdata-legacy). Nothing open in office-src but this session; in
  home-office, the plan-4b sitting (read-only) and the slips session
  (`desk/2026-10-03-continue-plan`, `suggestion-box`), which this release
  touches nothing of.
- The probe's integrity trailer gave 227 lines (matched) and a sha256 that
  my recomputation of the paste does not reproduce. Every captured stdout
  line's own sha256 verified, so the captures are intact. Most likely the
  paste trimmed trailing whitespace in a non-capture line.

## Item 6: why the install did not move

What I checked, in `cmd_land`'s after-land path (identical in 0.7.0):

- After an applied landing, every declared action runs through
  `(cd REPO && bash -c CMD)`. office-src's `install.sh` installs `git
  archive HEAD`, and HEAD is the merged 0.8.0 by the time land reads the
  dossier, so a run that succeeds replaces the install.
- A failing action prints `AFTER-LAND ACTION FAILED (exit N)` and the rerun
  lines. That's loud, but it sits in the middle of the screen, above the
  ratification question.
- Every way of not reaching the actions prints a line. A landing that is
  not applied prints `bale recorded ... nothing runs after it` (or the Held,
  Refused, Questions or Not landed words). A declaration that does not read
  prints a warning. A dossier that cannot be read dies with
  `could not read how SID ended`.
- The one silent path was a project with **no** action declared. That
  wasn't the case here (declared at 03:10).

So the code cannot have skipped `./install.sh` in silence with the
declaration in place. Two explanations fit, and **I can't tell them apart
without guessing**:

(a) 0.8.0 was applied by hand with `bale apply` in `~/office-src`. That
matches how the first two sessions of the wave landed, and the history's
`bale apply` lines. No after-land action ever runs that way.

(b) `office land` ran, and `install.sh` failed, or land stopped before the
actions. Either way the line saying so scrolled away.

You can settle it in one word: did 0.8.0 come back through `office land`,
or `bale apply`? (The bale session log in `~/office-src/.bale/logs/` would
too, but the brief keeps me to bale's `--json` surfaces and markers.)
Nothing in this release depends on the answer.

What I fixed that is the office's:

- **land's last lines say what became of each action**, after the
  ratification question, so it is the last thing on the screen:
  `After land, in REPO:` then `ran (exit 0): CMD`, `FAILED (exit N): CMD`,
  `not run: CMD`, and `rerun from the failed one: (cd REPO && A && B)`.
  The brief asked me to propose this; I built it (flagged below).
- **A project with no after-land action is said, not skipped**:
  `after land: PROJECT declares no after-land action, so nothing ran`, and
  `none: ...` in the last lines.
- **A real bug, found writing the tests:** for a project with no action,
  `plan_field` printed one empty line, and 0.7.0 and 0.8.0 ran it as
  `bash -c ""` and said "after land (1 of 1) ... 1 action(s) ran". It did
  no harm, but the log was false. Fixed.
- **`office status` gains `source:`.** It reads install.sh's `INSTALLED`
  stamp and compares the installed commit with the working copy's HEAD.
  It says `as installed`, or `BEHIND: the install is c91ebcf, and
  ~/office-src is now at 1234567 (office-src 0.9.0); (cd ... &&
  ./install.sh) brings the install level`. Run from a working copy, it says
  there is no stamp. On 10-04 at 00:17 this line would have answered the
  sitting's question at once.

## Decisions to ratify

1. **The doctrine rides once (item 1).** When the packed tree ships every
   file of its `doctrine/` (the pack's includes reach each one and no
   exclude drops any), I compare the whole doctrine directory, caches
   aside. `--include doctrine/OFFICE.md` alone does not count, since the
   checks would be missing. If it is
   identical, the install's copy stays home and the tray listing says
   `(the doctrine rides once, inside office-src's tree ...)`. If it
   differs, the install's copy rides as `context-doctrine-install.tar.gz`,
   described as the doctrine the office runs on. This is the sitting's
   lean. A bundle whose pack line the office can't read carries the
   install's copy as before. The office checks includes and excludes, not
   bale's own `.baleignore`; office-src's has none that touches
   `doctrine/`.
2. **Ride-alongs (item 1).** On a terminal, start lists what rides, with
   `du -sh` sizes, and asks `all, none, or the numbers to leave out`. The
   default is `all`. The flag twins are `--leave-out PATH` (repeatable,
   matched as declared or by resolved path, refused when it matches nothing
   declared) and `--no-rides`, which I added beside it. A bundle takes both,
   since they're the office's own flags, not pack flags. The tray listing
   names each one left out. The declaration never changes.
3. **The survey runs before every pack (item 2)**, as the sitting leaned,
   with its own commit, `office start: survey: N facts changed`. It runs
   once start's checks have passed, just before anything is packed, so a
   refused start commits nothing. `start()` runs it as `office survey
   --before-pack`, a new flag on the survey verb. It never fails a
   start. If an open session's forecast holds
   `floor-plan/survey.md` (the one-writer rule, via `reader writers`), or
   the survey cannot run, start warns, naming the age and recorded version,
   and goes on with the page as it was. `office status` now says
   `records office-src X, as installed` or `..., not the installed Y`.
   Doctrine section 13 amended.
4. **Ending a sitting (item 3).**
   - `office land SID`, or its folder word, on a read-only session runs
     `bale unlock SID --json` with stdin closed. The probe showed unlock
     asks nothing anywhere, so it runs like a read, not through `interact`.
   - It writes `- DAY ended: SID, a read-only sitting, closed by office
     land` in each folder that records it, committed alone. `ended` is a
     new verb in the closed History set; it changes no status.
   - The folder stays as it is. The words say closing it is yours.
   - It refuses a read-only session **no folder records**. That one isn't
     the office's sitting: bale-src's and ironwood's own sittings show in
     the In flight list. The refusal names the `bale unlock` line instead.
   - It refuses a response given for a sitting.
   - Bare `office land` never picks a sitting, unchanged.
   - `--ratified` on a sitting says nothing is ratified.
   - No after-land action runs for a sitting.
   - The In flight line for a sitting a folder records ends `(office land
     SID when the sitting is over)`. The Next line is untouched.
   - A read-only start ends `A read-only sitting lands nothing; when it is
     over: office land SID ends it`, not "When the response comes back".
   - Once bale has unlocked, nothing in land raises. A folder that cannot
     be written, or a report missing a key, is said, and the words still
     come back, since a second `office land` would be refused as not
     open.
   - Doctrine sections 5, 7 (verbs paragraph, table, walk-in paragraph) and
     10 name it, and `share/bale-consumption.toml` declares the surface.
5. **Where, from a bundle (item 4), two deviations from the brief.**
   - The candidates are the office **and every project it scopes**, not
     only the lane's project. A lane-less folder sent a project bundle
     would otherwise default to the office and fail.
   - When **no one place** holds every path, I refuse before asking. The
     brief said to fall back to the lane's project in that case, but bale's
     forecast-existence gate would refuse there anyway, after the office
     had gathered the tray. The refusal lists each path and where it is,
     or `nowhere the office can see`.
   - When several places hold them (a bundle naming no path, say), it's the
     lane's project, then the office, as before.
   - I also refuse a readable bundle sent, by flag or by answer, to a place
     whose tree lacks one of its paths, naming where those paths are. That
     is the first sitting's failure (bale open in office-src for office
     paths), now caught before bale runs.
   - A bare bundle name bale's search finds can't be read, so the lane's
     default stands, as before.
6. **Timezone (item 5).** `office_tz` checks the zone under `TZDIR` when it
   is set (the variable the C library reads), else `/usr/share/zoneinfo`,
   and only files count (`America` is a directory). The remedy is the
   canonical spelling found by the zone's last name, `posix/` and `right/`
   aside, with `tzdata-legacy` as the other way. With no match, it's the
   package. Where it shows up:
   - every verb's warning;
   - a `timezone:` line in `office status`, which is a PROBLEM line with
     the remedy indented under it when the zone does not resolve;
   - the walk-in's header, which reads `21:00 UTC (the floor plan's
     America/Indianapolis does not resolve here; office status says what
     fixes it)`.
   The tests use a fake zone directory through `TZDIR`.
7. **After land (item 6).** As above, plus one exit-code change: a
   declaration that does not read now makes land exit 1, since the session
   landed but its actions did not run. That matches a failing action. It
   was 0.

## Look closely on review

- `start()` in `lib/office_bale.py`: the bundle block now reads the
  bundle's includes, writes and excludes (`bundle_paths`), refuses paths the
  chosen place lacks, and keeps the includes for the doctrine check.
  `bundle_forecast` now shares its argv parser (`bundle_argv_parts`).
- `cmd_land`'s ending: `after_land_summary` is called on every return after
  the actions, including a ratification the helper refuses.
- `ask_rides` uses `eval` to assign an array to the caller's variable name.
  The names are fixed in the script (`leave_out`), never input.
- `refresh_survey` adds one office commit per start. For an office session
  it lands before the pack, so the base-drift stamp covers it.
- A project named `office` would be indistinguishable from the office in
  the where question and in the bundle checks. That was true of the where
  answer before this release too. `office projects add` could refuse the
  name; I left it alone.
- A separate review agent read the diff before I shipped. It found five
  things I then fixed: the survey committing on refused starts, a narrow
  doctrine include, the read-only start's last line, the hint missing on a
  sitting with no telemetry yet, and unlock's aftermath raising. It also
  prompted the `du` timeout on ride sizes and the release note about the
  exit code.
- `install_source_line` trusts install.sh's `INSTALLED` format (`source:`,
  `commit:`). An install made outside git says it cannot compare.
- The old test `test_a_read_only_sitting_has_nothing_to_land` asserted the
  0.8.0 refusal. It is now `test_a_read_only_sitting_is_never_the_session_out`.
  `TestStartOnATerminal`'s wizard test answers the new ride question.
  These are the only edits to earlier tests' expectations. The fake bale in
  `tests/test_land.py` learned `unlock` from the new captures.

## Slips for bale-src (doctrine section 10)

1. **`bale unlock --help` says it "performs no git operations"**, but its
   sweep commits the telemetry record (`[bale sweep SID] closed-read-only`,
   captured). The help should say so.
2. **No after-land hook on bale's side.** The office's after-land actions
   run only when `office land` drives the apply, so a hand `bale apply`
   skips them (item 6). A `post_apply` hook, like the wired `post_pack`,
   would let a project's after-land step survive either door. This is a
   proposal for bale, not something the office can do.

The wave's seventeen slips stand. The slips session files them in
home-office.

## Paths outside the forecast

None. The forecast is the whole repo.

## The suite

The suite is now 379 tests (344 before): 35 new in `tests/test_second_trip.py`,
and the two earlier tests named above changed. It is green here and takes
about fifteen minutes on this container, so `validation.sh` runs it whole,
past the two-minute target, and `validation_will_run` says so. The
session's own checks read the suite's verbose log class by class, so each
item has its own verdict line. I ran `validation.sh` both ways in staging
copies: 

- With the change applied, all sixteen checks pass (the exec bit
  included), and the twelve claims agree.
- On the unmodified tree, the nine session assertions fail (the seven
  class checks find no tests, plus VERSION, the fourth page, the
  captures and the unlock declaration). The syntax check, the suite
  (344 tests), the earlier pages, no-migration and the exec bit pass on
  both, by design.

## Proposals

### Let the walk-in say when office-src's install is behind its source

- **What:** when the office scopes the project its install came from
  (`INSTALLED`'s `source:`), and that repo's HEAD has moved past the
  installed commit, the walk-in names it, or the Next line says
  `(cd ~/office-src && ./install.sh)`.
- **Why:** `office status` now says BEHIND, but nobody runs status every
  day. The walk-in is read every day, and this session exists because the
  gap went unnoticed for a night.
- **Scope hints:** `walk_in` in `bin/office`, `next_move` in
  `lib/office_bale.py` (an order to rule: likely just after "out of step
  with the install").

### Make the after-land step survive a hand apply

- **What:** either a bale `post_apply` hook that runs the project's
  after-land actions (slip 2), or a walk-in line that notices a session a
  folder records was applied since it was sent out, without `office land`.
- **Why:** item 6. Two of the wave's three sessions were applied by hand,
  and the third may have been.
- **Scope hints:** bale-src for the hook. For the office, `in_flight` and
  the dossier's attempts.

### Check the zone at founding

- **What:** founding refuses or warns on a timezone that does not resolve,
  using the same `zone_resolves` and `zone_remedy`.
- **Why:** the brief put it in the founding door. The helpers are ready
  for it.
- **Scope hints:** the founding door session; `bin/office`'s zone helpers.
