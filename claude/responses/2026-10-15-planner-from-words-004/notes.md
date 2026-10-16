# Notes: 2026-10-15-planner-from-words-004 (office-src 0.24.0)

Session 2b of the front-door arc, the -v3 cut. A planner sitting now goes
out from your words: you say what you want a planner for, and the office
gathers what the planner needs, says what rides and why, and offers the
in-tray's sort first when drops wait. The digest lists the unsorted
drops. A planner's brief can say where its session lands and which folder
records it, and then `office start` asks neither. And a session you sent
out and will never run is withdrawn by key, never by its id. VERSION is
0.24.0, a minor release with no migration.

The pre-flight check said the goal fits, on the split the sitting already
made; the runtime did not compact this session. I sent no probe and no
light block: the brief, the tree, 2a's notes (archived at
claude/responses/2026-10-15-one-door-002/notes.md) and `bale help unlock`
in BALE_HELP.md answered everything else, and where the brief left the
mechanism to me I decided, and flag it first below. Every changed path is
inside the forecast. The brief names this session's first RATIFIED line
(`--- RATIFIED 2026-10-15-one-door-002 ---`); `office start` files it, and
nothing in this response touches it.

I read tools/craft_response.py and tools/response_lint.py before running
them, as 2a did: their docstrings and an audit of every import and every
write. Both import the standard library only, open no network connection
and start no process; the crafter writes only into the response directory,
the lint writes nothing.

## Decisions to ratify

1. **The sort offered first goes out in the same motion, not later.** The
   brief left it to me: the sitting goes out right after the sort, or it
   waits on the home screen. I took the same motion, for three reasons.
   Your words of message 8 were "it should offer to pack that first as
   well", both packed in the one sitting down; waiting would have needed
   a new kind of state in the office (a sitting promised but not sent)
   and a new Next-line rule to bring it back, for one key saved later; and
   the sitting loses nothing by going beside the sort, since it carries
   the same drops and owes them no Sort. The two out trays are both
   printed; the sitting's opener is the last copy made, so it is the one
   on the clipboard, and the sort's is printed above it with a line
   saying so. A sort that does not go out is said, and the sitting goes on.
   Offered before any sitting: from your words, `--read-only`, or a bundle
   whose pack line is read-only. Not offered while a sort is out or an
   open session holds the in-tray (each said). Twins: `--sort-first`,
   `--no-sort-first`; piped with neither, the sitting goes alone and the
   line names `--sort-first`. If you would rather it waited, it is one
   function (`offer_sort_first` in bin/office) and a Next-line rule.
2. **The doors.** `office start --planner` is the verb, with `--words` its
   twin, and it composes with 2a's door: `office start new --planner`
   mints the folder from your words through start new's own code
   (provisional as 2a made it), `office start FOLDER --planner` records the
   sitting in a folder on the desk (your words go in its Asked section),
   and bare `office start --planner` on a terminal offers the desk's
   folders by key, a plain return minting a new one. **The home screen's
   `p` key runs `office start new --planner`**: it asks your words and
   nothing else, as the hand test wants. Picking an existing folder is
   `office start --planner` or the folder's name.
3. **What the sitting concerns.** The projects your words name (every one,
   not just one, unlike open's lane), else `--about PROJECT` (repeatable)
   or `--in-office` for the office itself. When your words name none, the
   question is asked only if the answer changes what rides: the office
   gathers the set for each project and for the office itself, and asks
   only when they differ (an office that scopes no project never asks).
   Piped, that case refuses and names both flags. A folder minted for a
   sitting on one project gets that project as its lane; on several, or
   the office, no lane. `--goal` still sets the goal (every flag sets its
   field); `--on`, `--write` and `--brief` are refused with why (a sitting
   is packed in the office, forecasts nothing, and its brief is the
   office's).
4. **What rides, and its order** (pinned in doctrine section 4,
   continued): the sitting's own folder whole, the drafting table with
   the digest first, the hung items and the drops, as every sitting; then
   each concerned project's handbook chapter; the folder.md of each desk
   folder on those projects (for the office: the folders whose lane names
   none of its projects), the sitting's own aside; the walkthrough.md of
   each folder on those projects, desk or filing cabinet, that land filed
   or rewrote since the commit that filed the last sitting's page, newest
   first; and the last sitting's notepad pages. No project's tree rides
   with a sitting from your words (today a sitting on a folder whose lane
   names a project ships that project's whole tree; this one does not:
   digest over dump). A folder that only moved, closed or reopened, is a
   rename to git (`-M`), so it is not counted as landed again.
5. **The last sitting's pages.** A page SLUG-N.md whose SLUG.md is in the
   notepad belongs to that sitting, whichever was filed last; so the
   front-door sitting's two pages ride together. office_watches'
   `sitting_key` only joins SID-N.md to SID.md, and your sittings' pages
   are named without the NNN (front-door-sitting.md, -2.md), so the digest
   and the watches count those as two sittings. I left that as it is
   (not this session's) and propose it below.
6. **bale's caps.** The office keeps what rides under a tenth below bale
   pack's soft caps (9,000 files, 90 MB; bale's are 10,000 and 100 MB),
   counting the rest of the pack too. Over it, the oldest landed page is
   left out first, one at a time, each said on the screen and in the
   brief; nothing else is ever left out, and a set still over is said and
   left to bale's own caps.
7. **The brief.** The office writes the sitting's README.md from a new
   install template, templates/sitting-brief.md: your words verbatim
   (quoted, so no line of yours can read as a marker), what they concern
   and how that was found, what rides and why, and what a sitting owes
   (its pages, RATIFIED and LANDS lines). The same ride lines print on the
   screen before the pack. The session slug is the folder's with
   `-sitting` after it.
8. **The LANDS form, to the byte:** `--- LANDS PLACE, folder N ---` or
   `--- LANDS PLACE, a new folder ---`, PLACE a project's name or `the
   office`, read where the RATIFIED lines are read (one shared reader now,
   `brief_marker_lines` in lib/office_helper.py; the RATIFIED test is
   unchanged and passes). A second line is said and the first taken. A
   flag (`--on`, `--in-office`, a folder given) still sets its field, and
   the line it overrides is said. A folder in the filing cabinet is named
   with `office reopen`, and the question asked. For a bundle given by a
   bare name, the office reads its copy in your downloads when it finds
   one; otherwise it asks as before. **From the next bundle this sitting
   cuts (session 3's), every planner bundle carries one:** for session 3,
   `--- LANDS office-src, folder N ---`, N the folder that records it.
9. **`office withdraw`**, on your surface (`office help` lists it), and
   the home screen's `w` key, shown only while a session is out that can
   be withdrawn. Offered: a session the office has out (a folder records
   it, or the in-tray's sort) with no response-SID.tar.gz in your
   downloads and no attempt after its pack in bale's dossier. Not offered,
   each said with why: a response waiting (land's), an apply begun (held
   or otherwise: bale's revert), a read-only sitting (land ends it). The
   question's default is no (closing cannot be undone); `--yes` is its
   twin and piped needs it. History gains a closed-set verb, `withdrawn`,
   which changes no status, written to every folder that records the
   session. A folder that recorded that session alone is said with
   `office close NAME --retired "withdrawn before it was worked"`, never
   closed.
10. **A new bale surface, `withdraw`**: `bale unlock SID --reason abandoned
    --json`. Not probed live with `--reason`; I declared it from `bale help
    unlock` on the floor (fixtures/bale-0.4.45/land/help-unlock.json lists
    `--reason {abandoned,...}`) and on 0.4.55 (BALE_HELP.md), and its keys
    are the unlock surface's, since bale writes one report for both. The
    suite's fake unlock now takes `--reason` and records the reason it was
    given. The live check is the hand test's withdrawal; if bale's report
    differs there, the office says the key it could not read.
11. **The digest's In-tray section** sits after the desk: each unsorted
    drop by its page's file name, `(project: alpha)` when its words
    resolve to one of the office's projects, the words as given when they
    do not, nothing when it names none, and `- none` when the in-tray is
    empty or absent.
12. **Questions.** Added, each with its flag twin and each only where the
    brief allows: your words for a sitting (`--words`); what it concerns,
    only when it matters (`--about`, `--in-office`); the folder, by key,
    only on bare `office start --planner` (`FOLDER`, `new`); the sort's
    offer (`--sort-first`, `--no-sort-first`); the withdrawal's yes or no
    (`--yes`). Removed: where a LANDS bundle lands and which job.

## Tests

New: tests/test_planner_from_words.py, 27 tests. Five units (the LANDS
form and the shared reader, his words' goal and every project they name,
the caps leaving the oldest landed page first and nothing else, the
digest's In-tray section, the home screen's p and w keys), two gathering
tests on a real office (the set and its order for a project, with a page
filed before and after the last sitting; the office itself), fifteen
piped command tests (a sitting from his words with what rode, in the
request's README.md and its context; the refusals and flag twins; a desk
folder recording one; the sort taken, declined, already out and not a
sitting; the digest in a real office; a bundle that says where, a new
folder in the office, a place or folder the office does not hold, a flag
that overrides; a withdrawal piped, a response waiting, a session bale
held), and five terminal tests in the serial lane (the p key asking only
his words, `office start --planner` with the folder by key and the
project question, the sort offered and taken with the sitting's opener
left on the clipboard, bare `office start` sending a LANDS bundle with no
question, the w key and a withdrawal answered yes and no).

Changed: the fake bale's unlock takes `--reason` (tests/test_land.py);
the home screen's key list has `p` (test_home_screen); `withdraw` joins
the verbs whose writes are prose (test_office's catalog rule: a declined
question writes nothing, so it lands nothing); tests/fast-tier.toml gains
withdraw's entry point (a verb was added); the digest's sections test
holds the eighth section, the In-tray, after the desk, and says none. No
test was dropped; one was renamed
(`test_the_seven_sections_in_order_and_the_page_committed_alone` is now
`test_the_eight_sections_...`).

One thing the terminal tests taught: the pty helper types a whole line,
and a home-screen key is one keypress, so the newline after a key reaches
the next question. The p key's test survives it (the words question asks
again on an empty line); the withdrawal's is driven as `office withdraw`
on its own, after a home screen that shows the w key.

## Run results (worker's sandbox, two cores)

- The fast tier before (the request's tree, untouched): 67.0 s, 343
  tests, OK.
- The fast tier after: 50.5 s, 344 tests (withdraw's entry point added),
  OK; the tier's time is the sandbox's noise.
- The fast tier as validation.sh runs it (this session's units and one
  command test per outcome): 63.7 s and 64.0 s for 354 tests, OK, well
  inside the 120 seconds. With the whole new module it took 134.8 s for
  370 tests, over the budget (its 18 command and terminal tests start and
  land fake-bale sessions, 7 to 15 s each), so validation.sh runs the
  units and five command tests, and the rest run in the whole suite.
- The whole suite, `tests/run.sh`, on the bytes this tarball ships: 867
  tests in 14 min 28 s (868 s), every test OK but one,
  test_front_door.TestTourOnATerminal.test_an_interrupt_deletes_the_office_and_says_so,
  which **fails the same way on the request's tree untouched** in this
  sandbox (840 tests in 14 min 15 s, that test the only failure), and
  passes alone, under an artificial CPU load, and in `tests/run.sh
  test_front_door`. It sends Ctrl-C to the tour at step 1 and the tour
  is still running 30 s later, only when the whole suite runs beside it.
  2a's suite was OK on its machine, so I read it as this sandbox's
  timing and leave it; if it fails on yours, it is not this session's
  (nothing here touches the tour). So the manifest claims the whole
  suite `pass` as a prediction for your machine, not as observed here.
  An earlier whole run on the bytes
  before the digest test's update failed that test too, which is how the
  rename below came about.
- validation.sh in a staged copy (the request's tree, `files/` laid over
  it, apply.sh run, the manifest beside it, the staged tree compared with
  the tree the suite ran on, file for file: identical): every check
  passed, and the fast run's claim agreed with its verdict. The whole
  suite is behind `--slow`.
- The same validation.sh on the request's tree untouched: all six of
  this session's checks fail there (the fast run among them, since
  test_planner_from_words does not exist yet), so they test the change.

## Paths outside the forecast

None. Every changed path is under the request's resolved scope: the three
new files are lib/office_planner.py, templates/sitting-brief.md and
tests/test_planner_from_words.py.

## Proposals

- **What:** office_watches' `sitting_key` could join SLUG-N.md to SLUG.md
  whenever SLUG.md is in the notepad, as the gathering now does, not only
  when SLUG is a session id. **Why:** the sittings' pages are named
  without the NNN (notepad/2026-10-15-front-door-sitting.md and -2.md),
  so the digest's window counts one sitting as two and the eye-watches
  age one sitting too fast. **Scope hints:** lib/office_watches.py
  `sitting_key`; lib/office_planner.py `sitting_pages` has the rule.
- **What:** probe `bale unlock SID --reason abandoned --json` once, in a
  throwaway repo, and keep it beside the 0.4.45 unlock captures. **Why:**
  the `withdraw` surface was declared from `bale help unlock`, not from a
  capture; the hand test checks it live, and a fixture would let the suite
  replay bale's own bytes. **Scope hints:** claude/fixtures/, the
  consumption manifest's withdraw entry; only if the hand test's
  withdrawal says anything unexpected, or at the next bale probe.
- **What:** a withdrawn session's folder could leave the desk's "in
  flight" view at once and show as open with nothing out. **Why:** it
  does already (the session is no longer open in bale), but the folder
  keeps status open; a folder minted for that session alone is said with
  its close line, and nothing more. If you find yourself always closing
  it, the office could offer the close by key. **Scope hints:** bin/office
  `cmd_withdraw`; only if it is seen to be friction.

## Handbook

### office-src

- office start --planner sends a read-only planner sitting from the occupant's words (lib/office_planner.py says what they concern and gathers what rides; templates/sitting-brief.md is its brief); the home screen's p key runs office start new --planner
- offer_sort_first in bin/office offers the in-tray's sort before any sitting and, taken, sends it through start_sort in a subshell before the sitting, the sort's clipboard copy skipped (START_NO_CLIPBOARD)
- a planner brief's `--- LANDS PLACE, folder N ---` line is read by office_helper.brief_lands (the RATIFIED lines' reader, brief_marker_lines) and resolved by office_bale.bundle_lands; bin/office bundle_lands_read applies it before any question
- office withdraw (bin/office cmd_withdraw; office_bale.withdraw_view and withdraw) runs the consumption manifest's withdraw surface, bale unlock SID --reason abandoned --json, and writes the History verb withdrawn
- the digest's In-tray section is office_digest.in_tray_section

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.24.0, a
planner sitting goes out from your words: press `p` on your home screen
(or `office start --planner`), say what you want a planner for, and the
office gathers what the planner needs, the project's handbook chapter, its
folders on the desk, what landed since the last sitting and that sitting's
words, and lists each with why before it goes. When drops wait, it offers
to send the in-tray's sort first, in the same motion. The digest lists the
drops waiting. A planner's bundle that says where it lands goes out
without a question, and a session you sent out and will never run is
withdrawn with `w`, named by its folder. Next in the arc: clean delivery
(session 3), then meetings as a view over the work (session 4).

## Walkthrough

### What changed

- **A planner sitting from your words** (bin/office `cmd_start`,
  `planner_words`, `planner_folder`, `planner_asked`, `planner_gather`,
  `usage_start`, `usage`, `usage_all`; lib/office_planner.py, new;
  templates/sitting-brief.md, new; lib/office_home.py `FIXED_KEYS`).
- **The sort offered first** (bin/office `offer_sort_first`,
  `start_desktop`; lib/office_bale.py `bundle-sitting`).
- **The digest lists the unsorted drops** (lib/office_digest.py
  `in_tray_section`; bin/office `usage_digest`).
- **A planner's bundle says where it lands** (lib/office_helper.py
  `brief_marker_lines`, `brief_lands`; lib/office_bale.py `bundle_brief`,
  `bundle_lands`, `bundle-lands`; bin/office `bundle_lands_read`).
- **A session never worked, withdrawn** (bin/office `cmd_withdraw`,
  `usage_withdraw`, `withdraw_name`, `main`, `HELP_VERBS`;
  lib/office_bale.py `withdraw_view`, `withdraw`, `Reader.unlock`,
  `withdraw-list`, `withdraw`; lib/office_helper.py `HISTORY_VERBS`;
  lib/office_home.py `render_page`, `home`; share/bale-consumption.toml
  `[surfaces.withdraw]`; share/verbs.toml `[verbs.withdraw]`).
- **The record:** the doctrine (the front sheet, section 4 and its
  continuation, sections 5, 7 and 10), README, RELEASES 0.24.0, VERSION,
  the development record's front sheet, tests/fast-tier.toml.

### Why

Your words of 2026-10-15: "When i open a planner session, it should
automatically have relevant context, and if there's anything in the drop
that needs to be sorted, it should offer to pack that first as well." The
last sitting's queue: the digest listing the unsorted drops. Your message
4 of the sitting: why choose the project when the bundle could say it. And
message 5: you opened a session you never ran, and there was no office
way to close it.

### How to explain each piece

- **A planner sitting from your words:** you say what you want to ask the
  planner, and the office packs the papers the planner will need, and
  writes on top what it packed and why.
- **The sort first:** if messages are waiting to be sorted, the office
  offers to send the sorting job out at the same time, before the
  planning one.
- **The digest:** the planner's opening page now lists the messages still
  waiting to be sorted.
- **The LANDS line:** the planner writes on the request where the work
  goes and which folder it belongs to, so nobody asks you.
- **Withdraw:** a job you sent out and changed your mind about is taken
  back, and its folder says so.

### Questions a reviewer will ask

- *Does a planner sitting still read the project's code?* Not wholesale:
  it carries what the office holds about the project (the handbook, the
  folders, what landed). A sitting started on a folder with
  `office start FOLDER --read-only`, as before, still carries the
  project's tree.
- *What if the sort goes out and the sitting fails to pack?* The sort is
  out and stays out; the sitting's folder stays on the desk and the last
  line is the one that retries it.
- *What if the LANDS line names the wrong folder?* Give the folder (or
  `--on`) on the command line: the flag wins, and the office says it did.
- *Can withdraw close a session that has a response?* No: that one is
  offered by `office land`, and withdraw says so.

### A hand test

1. After this lands, run `./install.sh` in ~/office-src.
2. The ratification: open the folder that records session 2a
   (2026-10-15-one-door-002). Its Sessions section ends with
   `- 2026-10-15-one-door-002 ratified 2026-10-15`, filed when you started
   this bundle's first cut. When you started this cut, `office start` said
   that folder "holds its ratification already; left as it is". Check the
   line is there once.
3. In the office, drop something first: `office drop` with a line copied
   from anywhere, any project.
4. Type `office`, press `p`, and say what you want a planner for in a
   sentence that names one of the office's projects; end with a blank
   line. It should ask nothing more than the sort's offer: "1 unsorted
   drop(s) wait in the in-tray", then "Send the in-tray's sort out first,
   then this sitting". Press return (the sort). Two `Packed ...` lines
   follow: the sort's, then the sitting's. Above the sitting's, "What
   rides with the sitting, and why" lists what rode, one line each, and
   the opener on your clipboard is the sitting's (its goal line is your
   words). Open its out tray's request: README.md starts with your words
   and the same list.
5. Withdraw one of them: back on the home screen, press `w`. The sort is
   the one session out that can be withdrawn (a sitting is ended by land,
   never withdrawn), so it is named, "the in-tray's sort", and asked
   once: answer `yes`. It should say "Withdrawn:
   ... bale records it as abandoned" and nothing else. (This is the live
   check of `bale unlock --reason abandoned`; if it says a key could not
   be read, tell the next session the line.) End the sitting with `l` or
   `office land` once you are done with it.
6. A bundle that says where it lands: write a two-line brief to
   /tmp/lands-brief.md, `# Hand test` and `--- LANDS the office, a new
   folder ---`, then make a bundle from it with bale's own crafter:
   `python3 "$(dirname "$(readlink -f "$(command -v bale)")")/../tools/craft_response.py" --bundle lands-test --pack-arg "Hand test: a bundle that says where it lands" --pack-arg=--slug --pack-arg lands-test --pack-arg=--read-only --brief /tmp/lands-brief.md --out-dir ~/Downloads`
   (or wherever your downloads land). Run `office start` with nothing
   after it, press the bundle's key: it should say "the bundle's brief
   says where it lands: in the office, recorded in a new folder ... (its
   LANDS line); neither question is asked", and ask nothing else but the
   sort's offer if a drop waits. End it with `office land`, and close its
   folder (`office close`), since it was only a test.

## Delivery

- to: nobody: office-src has no audience

### Commit

Send planner sittings from the occupant's words, and withdraw unworked sessions

office start --planner sends a read-only sitting whose goal is the
occupant's words, recorded in a folder minted from them or picked by key.
The office gathers what rides (each concerned project's handbook chapter,
its folders on the desk, what landed since the last sitting, the last
sitting's pages), stays inside bale's caps, and lists each piece with why
on the screen and in the sitting's brief. The home screen's p key runs it.

Before any sitting, waiting drops are said and the in-tray's sort is
offered first; taken, the sort and the sitting go out in one motion. The
digest lists the unsorted drops.

A planner's brief may carry a LANDS line naming where its session lands
and which folder records it; office start then asks neither question.

office withdraw closes a session sent out and never worked, named by its
folder and asked once: bale unlock with reason abandoned, and a withdrawn
line in the folder's History.

## Structure

- title: message day
- size: high
- goal: Carry the occupant's message of 2026-10-12 through the front-door arc, one session at a time
