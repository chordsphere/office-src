# Notes: 2026-10-22-meetings-view-001 (office-src 0.26.0)

Session 4 of the front-door arc, its last: meetings as a view over the
work. After this lands you say a meeting once, in one sentence
(`office meeting`, or `m` on the home screen), and the office keeps it as
one line in the calendar, asking only what your words leave out. From a
day before it, the home screen offers its prep by key: a read-only
sitting briefed from what landed on the meeting's projects since the last
meeting on them, which stays with you during the meeting. When it is over,
`office land` ends it, records the meeting held and files what arose as
drops in the in-tray, from a file in your downloads or one copy, never
retyped; the next meeting on those projects sees them and the folders they
became. The prep may offer a cleanup of the projects' documentation. And
session 3's two exceptions are fixed (a template's own dashes; the
terminal wizard working a project with an audience here), and the tour's
interrupt test holds however the suite is started. VERSION is 0.26.0, a
minor release with no migration.

The pre-flight check said the goal fits; the runtime did not compact this
session. I sent no probe and no light block: the brief, the tree, the
doctrine and 2b's and session 3's archived notes answered everything, and
where the brief left the mechanism to me I decided and list it first
below. Every changed path is inside the forecast. The brief's LANDS and
RATIFIED lines are `office start`'s to file; nothing here touches them.

I read tools/craft_response.py and tools/response_lint.py before running
them, as 2a, 2b and session 3 did: their docstrings, every import and
every write. Both import the standard library only, open no network
connection and start no process; the crafter writes only into the
response directory, the lint writes nothing.

## Rider 3 first: what made the tour wait

It was the run, not the machine's load. A command started in the
background from a non-interactive shell (`tests/run.sh &`, `nohup ...`,
and a sandbox's background command, which is how 2b, session 3 and I ran
the whole suite) has SIGINT ignored, and every process it starts inherits
that. bash cannot trap a signal it was started with ignored, so the
tour's `trap ... INT` was never set: the Ctrl-C the test types at step 1
was echoed (`^C` is the last thing on the failing screen) and did nothing,
and the tour sat at its pause until the test gave up 30 seconds later. Run
alone, in the foreground, SIGINT was at its default, so it passed. I
reproduced it deterministically: the test alone, started with SIGINT
ignored, fails the same way every time on the untouched tree.

The suite already knew the mechanism: the runner printed a warning at the
start of such a run (`SIGINT is ignored in this run ...`) and `--detach`
restores the signal. The warning went unread in two sandboxes. The fix is
in the test, where the cause is: `run_on_a_pty` (tests/test_front_door.py)
starts the program with SIGINT and SIGQUIT at their defaults, as a
terminal's foreground program has them, and the interrupt test now runs
itself with SIGINT ignored in the test process, so it proves the
background case every time (it fails on the old helper even in the
foreground). What it checks is unchanged: exit 130, "the tour was
interrupted; deleting the tour office", nothing touched, nothing left. The
runner's warning is retired with its cause (tests/runner.py, and its two
tests changed to the new truth; the README's paragraph says why).

## Decisions to ratify

1. **The calendar is a meeting's home.** The doctrine's two pages stay,
   one bullet per line. A meeting's plan line ends with what it concerns,
   `[about: alpha, beta]` (`the office` for the office itself); a line
   without one, written by hand before 0.26.0, concerns the office. The
   record line for a meeting is the office's, pinned to the byte:
   `- DATE HH:MM title: prep out, SID [about: ...]` when its prep goes
   out, rewritten as `held, SID; arose: ...; dropped: ... [about: ...]`
   when the sitting ends. So "the last meeting that concerned them" is
   the latest record line before this meeting whose about names the
   project, and the window starts at that meeting's time. The calendar
   now arrives with the first meeting (as the in-tray with the first
   drop): its two pages from two new templates, the floor plan's entry,
   bale.toml's trigger. `office week` shows a meeting's projects and
   `[prep out]`.
2. **How his words are read.** English words, in lib/office_meeting.py
   `read_when`: a date (2026-10-30, Oct 28, the 28th of October, 11/3 as
   month/day, today, tomorrow, Friday, next Tuesday), a series (every
   Monday, each weekday, daily, weekdays, on Mondays), a time (2pm, 9:30am,
   14:00, noon, at 9). A bare hour from 1 to 6 is the afternoon, and a time
   alone is today or tomorrow, whichever comes next; each such reading is
   said on the screen. The title is his words less the when (a colon or
   bracket made a comma or parenthesis, since the lines read them), and it
   is the prep's goal: "its goal the meeting's words". No notepad write: a
   meeting is a line in the plan, and his words are its title.
3. **What it asks.** When his words say no day or no time, one question
   (`--when` its twin, read the same way, standing over the words); when
   they name none of the office's projects, one question by key, the
   office itself an answer (`--about PROJECT`, repeatable, and
   `--in-office`). An office that scopes no project concerns itself,
   unasked. Piped, each refuses and names its flag, nothing written.
4. **Near, and the first window.** Near is from 24 hours before a meeting
   until 4 hours after it starts (a prep forgotten until the meeting began
   is still worth sending, and the sitting serves during it). A first
   meeting on a project counts what landed in the 14 days before it. Both
   are pinned in the doctrine (section 4, continued) and are constants at
   the top of the module.
5. **The prep belongs to no folder, as the standalone sort does.** 2b's
   planner path records every sitting in a folder (minted or picked), and
   the brief says a meeting gets none, so `office start --prep` reuses the
   planner's gathering (office_planner's entries, its caps, its
   every-sitting list, its landed-walkthrough reading) and packs with no
   folder, as `start --sort` does; the calendar's record line names the
   sitting by its id. `office land SID` ends it: bale's land plan now
   accepts a read-only sitting the calendar records as a prep, and the
   walk-in names it "the meeting X (DATE), its prep". `office withdraw`
   does not offer it, as for every sitting.
6. **What rides with a prep**, in this order, said on the screen and first
   in its brief: the calendar; what every sitting carries (the drafting
   table where there is one, the hung items, the unsorted drops); each
   project's handbook chapter; each desk folder's folder.md on what the
   meeting concerns; each walkthrough land filed since that project's
   window began, newest first, every landed session counting; and the
   drops tied to the last meeting on each project, wherever they are now
   (still in the in-tray, or moved into a folder's drops/), with the
   folder each became. No project's tree rides.
7. **No sort offered before a prep.** The planner sitting offers the
   in-tray's sort first; a prep does not: a meeting is near, the drops
   ride with it, and two out trays is one more thing to carry before a
   meeting. One function if you want it (`offer_sort_first`).
8. **The arising block and the one paste.** Pinned to the byte in the
   doctrine and the prep's brief: `--- ARISING BEGIN SID ---`, items of a
   `### ` line in his words (the drop's first line), a `- project:` line
   (a project, `the office`, or `none`) and the rest verbatim, `---
   ARISING END ---`. The last block in a text counts, since a sitting keeps
   it current and a pasted conversation holds it several times. The sitting
   offers it as a file, `arising-SID.md`; `office land` finds that in the
   downloads (zero pastes), else on a terminal reads the clipboard once he
   has copied it (one paste), else takes `--arising FILE` (`-` stdin,
   `none`). Piped with none, land refuses and names the flag, and a block
   that does not read (another sitting's, a stray line, an item with no
   project line) stops land with the sitting still open. Each item becomes
   a drop through office_drop's own page writer, its via the file, the
   clipboard or stdin.
9. **Ties.** What arose is tied by the record's `arose:`; a drop he makes
   himself while a meeting's prep is out, from an hour before it starts
   until 12 hours after, by `dropped:` (said on the screen; never asked).
   `office drop` reads only the calendar to do it, no bale, so it stays
   instant.
10. **The cleanup.** The prep's brief has a section saying it may author
    one cleanup session for the meeting's projects when their
    documentation is messy, disorganized or too wordy: a planner's bundle
    beside the briefing with its LANDS line, which he sends or deletes;
    offered, never required. The doctrine's `cleanup` row says that is
    the cleanup built, and the scheduled, unattended cleanup of the
    office stays "not yet" (share/verbs.toml keeps `cleanup` unbuilt).
11. **The doctrine's meeting pieces, reconciled (outcome 5):**
    - the verbs table: `meeting` is now the script on his surface (the
      old "office session held open during a meeting" is what `prep`
      does, so it folds into `prep`), and `prep` is built (via
      `start --prep` and the home screen);
    - **clipboards: retired.** No clipboard is made: a series is one line
      in the plan, its running items are the drops tied to it and the
      folders they became, which its next prep carries. The catalog entry
      and template stay, so an office a renovation gave a clipboards/ space
      reads as before; nothing writes it;
    - **calendar: changed and used** (decision 1), and it arrives with the
      first meeting instead of by renovation;
    - **the drop's `tell:`: kept and used.** It still goes on the folder's
      Next; "until the meeting spaces exist" is gone, since the next
      meeting on the folder's project reads that Next in its prep;
    - the withdrawn design's capture verb, rolodex, owed tells and declared
      ride-alongs are not built (the rolodex space stays as it was).
12. **Rider 1.** `TEMPLATE_EXEMPT_KINDS = ("phrasing", "character")` in
    lib/office_letterhead.py, read by `hits_in_text`; names, bale's marks
    and the forbidden list still read a template's line, and a changed
    line is an ordinary one. Its told line and every sentence that named
    the exemption (doctrine sections 2, 5 and 4 continued, the verbs table,
    usage, README) say "or the three characters".
13. **Rider 2.** The wizard keeps its order (path, host, name, audience)
    and asks one question more, by key, only when a project given a host
    on the terminal gets an audience and `--worked-on-host` was not given:
    worked here (the default) or on the host. Here asks the clone's path
    on this machine, checks it as add checks any path (prepared for bale
    when it must be) and that it has the audience's remote, then records
    the host as `validates_on`, as the piped flags do. Asking the audience
    first would have needed the clone's remotes before its path was known.
14. **The home screen.** An `m` key (a meeting, in your words), always
    there; each near meeting whose prep has not gone out right after the
    Next line's move, "Send the prep for alpha review (Friday 2026-10-30 at
    14:00): it briefs you on what landed since the last one"; a prep that
    is out last, beside the sittings, "End the prep for alpha review once
    the meeting is over: land records it held and files what arose". Never
    the Next line: a meeting is not a job.

## Tests

New: tests/test_meetings_view.py, 22 tests (20 in its module job, 2 in the serial lane). Units for his words (the
phrasings, what is said, merging an answer), the calendar's lines,
series, near and the prep's record, office week's lines, the arising
block (the last block, each refusal by line), held and tied drops, the
prep's gathering (the window since the last meeting, a first meeting's
14 days, the tied drop and its folder) and its brief, the home screen's
items and key, and rider 1's exemption; command tests, piped, for a
meeting said in one sentence (the fast tier's entry point for `meeting`)
and the prep out and ended (no folder, what rode, the request, the record
lines, a second prep refused, land refused piped with the sitting still
open, the arising file found in the downloads, a block for another
sitting); and three terminal tests in the serial lane (the meeting's two
questions and land taking one copy from the clipboard; rider 2's wizard).

Changed, each to the new truth and nothing else:

- tests/test_front_door.py: `run_on_a_pty` restores SIGINT and SIGQUIT in
  the child; the interrupt test runs with SIGINT ignored (rider 3).
- tests/runner.py: the ignored-interrupt warning retired with its cause.
- tests/test_return_trip.py: its warning tests are now one test that a run
  started with SIGINT ignored no longer warns.
- tests/test_suite_clock.py: the detach test's one assertion about the
  warning's text dropped; the rest unchanged.
- tests/test_office.py: `meeting` joins `ARRIVAL_LANDS` (it brings the
  calendar and lands the plan); the week test names the meeting the
  calendar arrives with, not a renovation.
- tests/test_clean_delivery.py: its record test takes 0.25.0 or later.
- tests/test_drop.py: the drop row's pin follows the row (a drop is now
  tied to a meeting on now).
- tests/test_home_screen.py: the key list holds `m`.
- tests/fast-tier.toml: `meeting`'s entry point (a verb was added).

No test was dropped.

## Run results (worker's sandbox, two cores)

- The fast tier before (the request's tree, untouched): 52.2 s, 344
  tests, OK. After, the tier alone: 52.3 s, 345 tests (meeting's entry
  point added), OK.
- validation.sh as bale will run it, rehearsed in a staging copy that is
  a git repository (the request's tree committed, `files/` laid over it
  with bin/office's exec bit stripped, apply.sh, the manifest as
  `.bale-manifest.json`): every check passed in 73.7 s, the fast run
  69.8 s for 364 tests (the tier, this session's units, the prep's
  command test, the wizard's terminal test and the tour's interrupt
  test), its claim agreeing; nothing written outside its logs and its
  scratch directory (no `__pycache__`). Its scratch office and repos are
  under a temporary directory outside the staging copy, each a repository
  of its own.
- The same script on the request's tree untouched: every one of this
  session's checks fails (outcomes 1, 3, 2/4/5, rider 1, the record, and
  the fast run, which names tests that do not exist there), so they test
  the change; only the syntax and scratch-office checks pass.
- The whole suite, `validation.sh --slow` in that git staging copy,
  started in the background (SIGINT ignored, the case that failed twice
  before): 906 tests in 928 s, OK, the tour's interrupt test among them.
  An earlier whole run on nearly these bytes (906 tests, 916 s) caught
  two pins of old text, the drop row in tests/test_drop.py and the home
  screen's key list in tests/test_home_screen.py, which I brought to the
  new truth; that run's terminal lane, also started in the background,
  passed the interrupt test too.
- The untouched tree's whole suite, started the same way: the interrupt
  test the only failure, exactly as 2b and session 3 saw it.
- The whole suite's `pass` claim is observed here, not only predicted.

## Paths outside the forecast

None. The five new files are lib/office_meeting.py,
templates/calendar-plan.md, templates/calendar-record.md,
templates/prep-brief.md and tests/test_meetings_view.py, all inside the
forecast.

## Proposals

- **What:** a way to change or take back a meeting by its words (`office
  meeting --drop MEETING`, say), and to record one held that had no prep.
  **Why:** today a meeting leaves the plan only by editing
  calendar/plan.md, and a meeting held without its prep shows as a gap in
  `office week` forever. Neither was in the brief, and both are small.
  **Scope hints:** lib/office_meeting.py `read_plan`, `write_record_line`;
  bin/office `cmd_meeting`.
- **What:** office_planner's `every_sitting_carries` names the drafting
  table on a planner sitting's ride list even in an office that has none
  (bale's start adds it only when it is there). **Why:** seen here; the
  prep filters it, the planner sitting does not. **Scope hints:**
  lib/office_planner.py `every_sitting_carries`, one condition.
- **What:** `on_a_terminal` (tests/test_start.py) could start its program
  with SIGINT at its default too. **Why:** no test it drives sends an
  interrupt today, so nothing fails; a future one would meet rider 3's
  cause again. **Scope hints:** the same three lines as `run_on_a_pty`.

## Handbook

### office-src

- office meeting (bin/office cmd_meeting; lib/office_meeting.py read_when, title_of, record_meeting) writes one line in calendar/plan.md, `- DATE HH:MM title [about: ...]` or `- every DAY HH:MM title [about: ...]`; the calendar arrives with the first meeting (office_meeting.arrive)
- a meeting's prep is office start --prep (bin/office start_prep): packed with no folder, its gathering office_meeting.gather_prep over office_planner's pieces, its brief templates/prep-brief.md; office_meeting.mark_prep_out writes its record line `prep out, SID`
- office land ends a prep as a sitting (office_bale.sitting_plan accepts one the calendar records), reads the arising block first (bin/office land_arising: --arising, arising-SID.md in the downloads, or the clipboard) and records it held (land_held; office_meeting.hold writes each item through office_drop.write_drop)
- office drop ties a drop to a meeting on now with its prep out (office_meeting.tie, the record line's `dropped:`)
- near is office_meeting.NEAR_BEFORE and NEAR_AFTER (24 h, 4 h); a first meeting's window FIRST_WINDOW_DAYS (14); the tie window TIE_BEFORE and TIE_AFTER (1 h, 12 h)
- a pull-request template's own lines are exempt from office_letterhead.TEMPLATE_EXEMPT_KINDS, the phrasing rule and the three characters
- office projects add on a terminal asks where a project given a host and an audience is worked, by key (bin/office workbench_here)
- the tour's interrupt test runs with SIGINT ignored; tests/test_front_door.py run_on_a_pty restores SIGINT and SIGQUIT in the program it starts

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.26.0, a
meeting is a view over the work: say it once in your own words with
`office meeting` (or `m` on your home screen), and from a day before it
your home screen offers its prep, a sitting that briefs you on what landed
on its projects since the last meeting on them and stays with you during
it. When it is over, `office land` records it and files what arose as
drops in your in-tray, from one saved file or one copy, and the next
meeting sees them. A pull-request template's own dashes no longer refuse a
delivery, and a project with an audience is worked on your machine however
you add it. This is the front-door arc's last session.

## Walkthrough

### What changed

- **A meeting, asked once** (bin/office `cmd_meeting`, `usage_meeting`,
  `usage`, `usage_all`, `HELP_VERBS`, `main`; lib/office_meeting.py, new:
  `read_when`, `title_of`, `merge`, `record_meeting`, `arrive`;
  templates/calendar-plan.md and calendar-record.md, new; lib/office_home.py
  `FIXED_KEYS`; lib/office_helper.py `week_report`, `plan_title`;
  share/verbs.toml `[verbs.meeting]`).
- **Its prep, briefed from what landed since the last one** (bin/office
  `start_prep`, `cmd_start`'s `--prep`, `usage_start`; lib/office_meeting.py
  `near`, `resolve`, `gather_prep`, `write_prep`, `mark_prep_out`;
  templates/prep-brief.md, new; lib/office_home.py `home_items`, `home`,
  `Names.of`; lib/office_bale.py `in_flight`; share/verbs.toml
  `[verbs.prep]`).
- **What arises, queued for after** (bin/office `cmd_land`, `land_arising`,
  `land_held`, `usage_land`, `cmd_drop`; lib/office_meeting.py
  `parse_arising`, `check_arising`, `hold`, `tie`; lib/office_bale.py
  `sitting_plan`, `end_sitting`).
- **A cleanup rides along** (templates/prep-brief.md; the doctrine's
  `cleanup` row).
- **The doctrine says what a meeting is now** (doctrine sections 4
  continued, 5 and 7, the front sheet, the verbs and spaces tables).
- **Rider 1** (lib/office_letterhead.py `TEMPLATE_EXEMPT_KINDS`,
  `hits_in_text`; the sentences in lib/office_deliver.py, bin/office, the
  doctrine and README).
- **Rider 2** (bin/office `workbench_here`, `cmd_projects_add`).
- **Rider 3** (tests/test_front_door.py `run_on_a_pty`; tests/runner.py).
- **The record:** README, RELEASES 0.26.0, VERSION, the development
  record's front sheet.

### Why

Your words of message 7, 2026-10-15: "in my mind, a meeting is just an
extension of the work ... i might have a future meeting that should have
knowledge of that session". And your idea of 2026-10-07: a claude session
"to brief me on it, ask any questions before or during the meeting, and
queue any work that arises for after", with "a folder cleanup" that rides
along. The sitting's ratification of session 3, with its two exceptions,
and its ruling on the tour's interrupt test.

### How to explain each piece

- **A meeting:** you tell the office about a meeting in one sentence, and
  it keeps it on a calendar; it asks only what you left out.
- **The prep:** before the meeting, one key gives you a briefing on what
  changed in those projects since the last time you met about them, and
  the same conversation stays open during the meeting for questions.
- **What arises:** anything new from the meeting is written down for you,
  and when the meeting is over it lands in your in-tray as items to sort,
  without retyping.
- **The cleanup:** if the briefing finds the projects' documents messy, it
  can offer a tidy-up job you accept or ignore.
- **The template's dashes:** a review form a repository supplies no longer
  blocks a delivery because of its own punctuation.
- **The wizard:** adding a shared project on the terminal now sets it up
  on your machine by default, as the full command line always did.

### Questions a reviewer will ask

- *Does a meeting make a folder?* No. Its prep is recorded in the calendar;
  only the work that arises becomes folders, through the in-tray.
- *What if I never end the prep?* It stays out and on the home screen with
  an "End the prep" key; drops you make in the 12 hours after the meeting
  starts are tied to it.
- *What if the sitting's block has a mistake?* land says which line does
  not read and leaves the sitting open; fix the file and land again.
- *Can I still work a project on its host?* Yes: choose the host's key in
  the wizard, or `--worked-on-host`.

### A hand test

Run these on your WSL terminal, one line at a time, in a scratch office and
scratch repositories, so nothing real is touched. Where a line names your
downloads directory, it is the first entry of `downloads` in
~/.config/office-src/machine.toml.

1. After this lands (office land runs `./install.sh` for office-src), make
   the scratch project and office:
   `H=/tmp/meetings-hand; rm -rf "$H"; mkdir -p "$H"; git init -q -b main "$H/alpha" && git -C "$H/alpha" commit -q --allow-empty -m "Initial commit"`
   then
   `office init "$H/office" --no-founding --no-default && cd "$H/office" && office projects add alpha "$H/alpha" --prepare`
2. Something that landed before the first meeting, the way office land
   files a walkthrough:
   `office open fix-report --title "Fix the report" --lane alpha && printf '# Walkthrough\n\nThe report adds its totals.\n' > desk/*-fix-report/walkthrough.md && git add desk && git commit -qm "office land: the report's walkthrough"`
3. A meeting in one sentence: type `office meeting`, and at its question
   say a meeting an hour or two from now, naming alpha, for instance
   `alpha review today at 4pm` (any time later today). It should ask
   nothing else and say "Recorded: alpha review, ... at 16:00 (...); it
   concerns alpha." and "the calendar arrives in this office".
4. Type `office`. Under "Waiting on you" there should be "Send the prep for
   alpha review (...): it briefs you on what landed since the last one".
   Press its number. Look at the screen: "What rides with the prep for
   alpha review, and why" lists `desk/...-fix-report/walkthrough.md: what
   landed on alpha in the 14 days before it (no earlier meeting on alpha is
   recorded)`, then "Packed ...-alpha-review-prep-001 for the meeting alpha
   review (its prep; the calendar records it, and no folder)". No new
   folder is on the desk (`ls desk`). You need not open a chat for it.
5. What the sitting would save for you: with S the session id from that
   screen and D your downloads directory,
   `printf -- '--- ARISING BEGIN %s ---\n\n### Update the report with the new criteria\n\n- project: alpha\n\n--- ARISING END ---\n' "$S" > "$D/arising-$S.md"`
6. Type `office` again and press the key "End the prep for alpha review
   once the meeting is over". It should ask nothing, say the sitting is
   closed, and end with "Recorded: alpha review (...) happened; 1 item(s)
   that arose are drops in the in-tray, tied to it: in-tray/...". Check
   with `tail -n 1 calendar/record.md` (held, the session id, `arose:`)
   and `ls in-tray`.
7. The wizard: a bare audience and two clones of it, one standing for the
   host's copy and one for your workbench:
   `git init -q --bare "$H/aud.git" && for c in there here; do git clone -q "$H/aud.git" "$H/$c" 2>/dev/null; git -C "$H/$c" commit -q --allow-empty -m init; touch "$H/$c/bale.toml"; done`
   then `office projects add` and answer: the path `$H/there` (typed out
   in full), the host `me@workhost`, the shell `bash -lc` (it stands for
   ssh here and runs on this machine), a plain return for the connect
   line and for the clone to bring, the name `beta`, a plain return for
   the audience (origin), `Pat Example <pat@example.org>` for the author,
   a plain return for the base. Then it should say "beta has an audience,
   so it is worked from a guarded clone on this machine by default" and
   offer two keys, the first "on this machine ... (the default)": press
   return, and give the path `$H/here`. A plain return for the two lists.
   `office projects` should show beta on this machine, "validates on:
   me@workhost".
8. Clean up: `cd ~ && rm -rf /tmp/meetings-hand "$D"/arising-*-alpha-review-prep-*.md`.

## Delivery

- to: nobody: office-src has no audience

### Commit

Make a meeting a view over the work

office meeting records a meeting said once in the occupant's words: when
it happens and the projects it concerns, one line in the calendar's plan,
asked only what the words leave out; a series is never asked for again,
and no folder is made. The calendar arrives with the first meeting.

From a day before a meeting the home screen offers its prep by key: a
read-only sitting, recorded in the calendar and in no folder, briefed from
what landed on its projects since the last meeting on them, with their
handbook chapters, their folders on the desk, the unsorted drops and the
drops that arose last time. Its brief may offer a cleanup of the projects'
documentation as a planner's bundle.

office land ends the sitting, records the meeting held and files what
arose in it as drops in the in-tray, tied to the meeting, read from a file
in the downloads or one copy; a drop made during the meeting is tied too.

A pull-request template's own lines are exempt from the three characters
as well as the phrasing rule. On a terminal, office projects add works a
project with an audience on this machine by default. The tour's interrupt
test holds in a run started in the background.

## Structure

- title: message day
- size: high
- goal: Carry the occupant's message of 2026-10-12 through the front-door arc, one session at a time
