# notes: 2026-11-03-answers-from-the-artifact-002 (office-src 0.44.0)

Five of the brief's seven items shipped whole, and item 2 (the offices on
this machine) shipped too; item 4 (`office start FOLDER --handoff
RESPONSE`) is the half I left, as the brief's seam allows. Said first
because it shapes everything below: the bailout's Next line is not an
office line yet, and it says so in plain words.

## Decisions

Each one either a call the brief left to me or a reasoned deviation. The
flagged deviations are marked **deviation**.

1. **Which half shipped (the seam).** Items 1, 2, 3, 5, 6 and 7 shipped;
   item 4 did not. bale handoff builds a request through a second path
   (not pack, not open), so `--handoff` needs a new consumption surface in
   share/bale-consumption.toml, a third branch in office_bale.start (the
   pack, the bundle and now the handoff), the folder-recording and out-tray
   steps run on its report, the fake bale taught both a bailout apply and
   `bale handoff`, and a test of each. That is a session's worth on its
   own, and I would rather leave it whole than ship it half-tested. It is
   Proposal 1 with what I learned.

2. **deviation: a bailout's Next line names bale's line, said as such.**
   The brief wants a bailout's Next line to be item 4's office line. With
   item 4 left there is no office line to name, so the line is
   `no office line yet: type bale handoff RESPONSE in REPO; it packs the
   fresh session the handoff asks for, and office sessions N SID records
   it in the folder` (office_bale.handoff_line). It is the one place the
   occupant is still sent to bale, and it says that in its first words;
   the `In office words:` list says the same for a `bale handoff` bale
   printed. When item 4 lands, handoff_line is the one function to change.

3. **`offices` written by init, default, and the home screen (said once).**
   The worker's call. init and default alone would leave every office
   built before 0.44.0 (both of yours) unlisted until you typed `office
   default PATH` for each, which is exactly the kind of typing N1 is
   about. So the home screen lists the office it opens in when it is not
   listed, with one line (`listed ROOT in machine.toml's offices (its home
   screen opened): ...`). Only the home screen does it, not the piped
   walk-in, so a script or a session reading the page never writes your
   config. init lists the office before its first survey, so the survey's
   new Machine `offices` line is not reported as a change on the next run.

4. **A key for another office: a fourth kind, `elsewhere`, with the root
   as its first word.** The worker's call. The menu line is
   `KEY<tab>elsewhere<tab>ROOT<tab>ARGV...`, and the home screen runs
   `OFFICE_ROOT=ROOT office ARGV` with the same environment scrubbing the
   `office` kind gets. A shell kind would have meant quoting a root into a
   command string; a kind of its own keeps the root a word.

5. **The sort-first offer stays a question.** The worker's call, and the
   sitting's lean: the sort is the in-tray's housekeeping, not the
   bundle's, and nothing in a bundle can know what the in-tray holds the
   day it is opened. offer_sort_first is unchanged.

6. **The bare-start one-bundle rule is a terminal rule; land's is piped
   too.** The brief says "on a terminal" for start and does not limit
   land. Piped bare `office start` still refuses naming the folder (a
   piped start taking a bundle nobody named felt like the wrong surprise
   for a script); piped bare `office land` with several out and one
   response here lands it, since the response's own file name answers
   which.

7. **deviation (small): the LANDS-elsewhere line exits 0 and starts
   nothing.** The brief says it is "not a refusal but a line that names
   the office that does scope it". I made it exit 0, print that office
   and the exact line that starts the bundle there
   (`OFFICE_ROOT=ROOT office start --bundle FILE`), or say no office here
   scopes it (with `office projects add` and `office withdraw --bundle` as
   the two ways out), and write nothing. I did not run the start in the
   other office for you: that would be the office deciding to write in
   another office, which the Pinned rules keep to the verb a key runs.
   This needs machine.toml read, so bundle-lands takes `--machine-file`;
   without it the old "where it lands is asked" line stands.

8. **"Piped, an answer an artifact gives is taken the same way" reached
   ask_where.** Before, ask_where refused piped before looking at the
   bundle's paths or the lane, and cmd_start had a second refusal in front
   of it. Both are gone: piped, the lane's project, a bundle's paths and
   an office with no projects answer it as on a terminal; only a question
   nothing answers refuses (`...; nothing answers it (no bundle's paths,
   no lane), and piped input is never asked`). Every answer ask_where takes
   now begins `from the bundle:`, `from the folder:` or `from the floor
   plan:`; bundle_lands_read's line begins `from the brief:`. I prefixed
   the old words rather than rewording them, so the existing tests'
   substrings still hold.

9. **RIDES matching.** "the riders whose glob matches a RIDES path": a
   rider matches when the RIDES path is its rides line as written, or its
   glob, or a path its glob covers (drafting.glob_touches, the forecast's
   own rule). The project prefix (`office-src: bin/`) is honoured on both
   sides as riders_for_forecast honours it. RIDES lines replace the
   forecast's selection outright, piped or not; `--carry N` and `--carry
   none` still win, as the brief says.

10. **MAX_ITEMS stays nine.** read_key takes one keypress, so a tenth
    numbered key cannot be typed. The standing key is one more item per
    sitting; the other offices' items share the same nine numbers after
    this office's own (theirs are cut first, with a line saying how many
    more wait there). A two-key menu is Proposal 3.

11. **The walk-in reads other offices inside its batch.** The suite pins
    the walk-in to three helper starts (test_land.TestFewerHelperStarts);
    the other offices' read rides in the page's existing batch as
    `home:elsewhere`, and does no bale read at all when no other office is
    listed. The survey's offices fact is computed inside survey-render
    for the same reason (the pack's survey would otherwise start one more
    helper).

12. **The probe's run line: read only when no folder is typed.** With a
    folder typed, office probe settles the folder first and reads the
    clipboard after, exactly as 0.41.0 did; the run line is then not
    consulted. With none, the text is read first. A line that begins
    `# office: probe` and does not read is refused by name (nothing runs):
    a malformed line is the sitting's mistake, and passing it over
    silently would run the block somewhere it did not mean.

13. **The run line's `--sid` that is not open is soft.** probe_py plan
    gains `--sid-soft`: the line's session, when it is not one the probe
    could be for, is said and dropped, and the session is read as without
    it. A typed `--sid` keeps today's refusal.

14. **A standing with no probe block, and no folder given:** filed on the
    one desk folder that records the standing's sitting
    (office_standing.folder_of), strictly (office standing's rules: a
    block that does not read stops). Two folders recording it is a
    refusal naming both.

15. **The prep brief's run line.** No folder records a prep, and office
    probe needs a folder that records the session; so a prep's probe for
    its own session has no FOLDER to name. The prep brief says so plainly
    rather than inventing one. Flagged so the next brief can say whether
    a prep's probe should run at all.

16. **The `In office words:` mapping for unlock.** At a landing the
    session is never a sitting (a sitting goes through land's unlock
    path, where bale's output is not shown above the words), so the line
    names both: `office withdraw SID, for a session never worked; office
    land SID, for a sitting`. bale's clarification output names `bale
    unlock` ("and repack if the gap invalidates the request"), which is
    where it shows.

17. **Existing tests changed with what they pin** (each with a comment
    saying why): test_home_screen's bare-start offer now holds two bundles
    (one alone is taken); test_planner_from_words' terminal bundle test
    takes the one bundle without a key, and its unscoped-LANDS test reads
    the new line; test_start's piped refusals expect the goal's refusal
    once the lane answers where; test_standing's home-screen test counts
    the standing key before any standing is filed; test_return_trip's
    hosted clarification expects office relay's Next line, and its three
    assertions that machine.toml does not exist after a landing now assert
    that land wrote no `downloads` there (office init writes `offices`
    into the file now, so its absence no longer means what they meant).

18. **The response was assembled by hand.** I did not run
    tools/craft_response.py or tools/response_lint.py: I read the parts I
    needed (the feedback block's builder) but not the two files whole,
    and your instruction was to read them before running them. Sizes and
    sha256s were computed by a short script over files/; the manifest
    carries no `feedback` block, since TARBALL.md 5.2.2 says its
    mechanical stream is filled by the lint, never by hand. `python3
    tools/response_lint.py response-002 --emit-feedback-mechanical` adds it
    if you want the telemetry.

## Walkthrough

What changed, in the order you will meet it.

- **office start.** Bare on a terminal with one bundle waiting:
  `from the downloads: one bundle waits, STEM; starting it (a plain office
  start FOLDER starts a job instead)` and it goes. A brief's `--- RIDES
  PATH ---` lines pick the riders; `--- RIDES none ---` carries none.
  Piped, `office start FOLDER --goal TEXT` takes where from the lane. A
  bundle whose LANDS line names another office's project prints that
  office's line and stops.
- **office land.** Bare with several out: the one whose response is in
  the downloads lands (piped too); with responses for several, those are
  keyed first, each saying so. After bale's output: `In office words:`.
  A clarification's Next line is `office relay SID ANSWER-FILE, ...`, and
  the planner's block carries the tail `folder: ...` / `answer: office
  relay SID ANSWER-FILE`. A bailout's line says there is no office line
  yet.
- **office probe.** No folder: the block is read first; its `# office:
  probe FOLDER [--project NAME] [--sid SID]` line answers the rest, said
  `from the block: probe ...`. A typed flag wins, said. A text with only a
  standing files it and runs nothing.
- **The home screen.** `[r] run the probe on the clipboard` while a probe
  could run; the standing key from a sitting's first turn; one section per
  other listed office after this office's own, keys running the verb there;
  a line counting bundles no office here scopes.
- **The walk-in page.** The same other-office sections, after the
  Suggestion box, each item with its `OFFICE_ROOT=ROOT office VERB` line.
- **machine.toml.** `offices = [...]`, appended by init, default and the
  home screen. The survey's Machine section names them.

Questions a reviewer will ask:

- *Does the home screen read work-office's pages?* No: office_home.
  office_section reads ob.repos (the floor plan's project list, which it
  needs to know where the registries are) and bale's status in each
  registry, and the downloads. No folder.md, notepad or handbook. The
  sessions out there are named by slug for that reason, not by folder.
- *Can a key here write in the other office?* Only by running the verb
  there, as if typed there (OFFICE_ROOT=ROOT office ...). Nothing in this
  office's code writes another office's files.
- *Why does a bundle opened by work-office vanish from home-office's
  offer?* cut_by_office runs opened_from against each other listed office
  for the bundles this office's own reading left waiting; a hit there
  removes it everywhere.
- *What if machine.toml lists an office that was deleted?* listed_offices
  skips it with a line (OFFICE_DEBUG on the screens), never edits the file.

A hand test, about ten minutes, with your two offices:

1. `office` in home-office on a terminal: one line says home-office was
   listed (once). Do the same in work-office.
2. `cat ~/.config/office-src/machine.toml`: `offices = [...]` holds both.
3. With a work-office session out and its response in your downloads,
   `office` in home-office: a section headed with work-office's name and
   root names it; its key lands it there. `office` piped (`office | cat`) shows the line instead.
4. With a bundle of work-office's in the downloads that work-office has
   opened, check home-office's `office start` no longer offers it.
5. Ask a sitting for a probe; copy its block once; type `office probe`.
   The first line is `from the block: probe N ...`.
6. Copy only a standing block; type `office probe`: `the clipboard holds a
   standing and no probe: filed on desk/...; nothing to run`.
7. Land a HOLD on purpose (a failing validation): `In office words:` names
   `bale retry -> office land SID --response FILE` above `Held:`.

## Delivery words

office-src 0.44.0: answers from the artifact. A question office start or
office land would ask is now taken from what already answers it, a
bundle's brief, a response's file name, the folder's lane, and said in one
line; piped runs take the same answers. machine.toml lists the offices on
this machine, and each office's home screen and walk-in show what waits
for the others, a key running the verb there. Every line the office hands
you to type is an office line, with bale's verbs translated after a
landing. A probe block's `# office: probe ...` header line lets bare
`office probe` run it from one copy, and a standing alone on the clipboard
is filed. Additive; no migration.

## Structure

- lib/office_home.py grew the cross-office reading (other_offices,
  cut_by_office, office_section, other_sections); it is the screen's
  module and already held the bundle offer, so it sits there. If a third
  reader of other offices appears (status, say), it wants a module of its
  own (lib/office_offices.py).
- The machine.toml list lives in lib/office_helper.py beside the
  downloads key, as the brief asked.
- Nothing was split or moved.

## Handbook

office-src: front sheet

- machine.toml's offices lists the offices on a machine; office init, office default PATH and an office's home screen append to it, and nothing removes from it.
- Another office is read through its bale registries and the downloads alone; a home-screen key runs the verb there with OFFICE_ROOT set.
- A brief's marker lines kept to the byte are LANDS, BRANCH, RATIFIED, ENDS and RIDES; a probe block's purpose header may carry `# office: probe FOLDER [--project NAME] [--sid SID]`.
- office probe with no folder reads the block first; with a folder typed it reads the folder first.
- The home screen's numbered keys stop at nine because a key is one keypress.
- office start --handoff does not exist yet; a bailout's Next line says so.

## Suite

The whole suite, once, on two CPUs: 1289 tests in 833 s (`tests/run.sh`,
the runner's own parallel lanes). That run had 4 failures, all in
tests/test_return_trip.py and all pins of the old behaviour (decision 17's
last two items); I changed those assertions and reran test_return_trip and
the new module (68 tests, OK). Nothing outside tests/test_return_trip.py
changed after the whole run. Before it, the touched modules whole
(test_start, test_land, test_probe, test_standing, test_home_screen,
test_home_screen_offers, test_planner_from_words, test_read_side,
test_desk_verbs, test_office, test_founding_door, test_suite_clock and the
new module) ran green. The fast tier was 53 s before the change.

validation.sh ran on a staged copy (the request's tree, files/ over it,
apply.sh run): plain, every check passed and the fast tier with this
session's classes took 84 s of its 120 s; with `--slow` (the touched
modules whole, test_return_trip among them), every check passed. On the
unmodified tree its VERSION and pinned-words assertions fail, as they
should. The fast tier names only the new module's classes that build no
second office and drive no terminal: with all of it, and the changed
classes of the other modules, it reached 114 s, too close to the budget.

## Proposals

1. **What:** `office start FOLDER --handoff RESPONSE`, the brief's item 4.
   **Why:** the bailout's Next line is the last line the office hands the
   occupant that is bale's. What I learned building toward it: bale
   handoff is a third request-building path, so office_bale.start wants a
   `handoff` branch beside pack and bundle that runs `bale handoff
   TARBALL` where the session's repo is (through the project's shell for
   a hosted one, as the pack runs), reads the new sid from bale status's
   open-set diff exactly as open_bundle does (a handoff, like an open,
   adds one session), and then reuses everything after the pack: the tray,
   record_session with words "from the handoff of SID", the opener. The
   fake bale (tests/fakes/land_bale.py) needs a bailout apply (an attempt
   with outcome bailout, the session closed) and a `handoff` verb that
   packs through the packing fake. share/bale-consumption.toml needs the
   handoff surface declared, with whatever bale 0.4.56's handoff report
   prints; a probe of the real `bale handoff --help` output and one real
   bailout landing would pin its words. **Scope hints:** lib/office_bale.py
   start() and handoff_line(), bin/office cmd_start's flag, the fake,
   share/bale-consumption.toml; the History verb I would pick is `handed
   off`.

2. **What:** a prep's probe. **Why:** office probe needs a folder that
   records the session, and no folder records a prep, so a prep's own
   probe cannot run through the office at all (decision 15). Either the
   calendar's record becomes a place probe reads, or the prep brief says
   to ask through the sitting's folder. **Scope hints:**
   lib/office_probe.py plan's recorded sessions; lib/office_meeting.py
   prep_of.

3. **What:** a home screen past nine keys. **Why:** with a second office
   listed and a standing key per sitting, nine fills; the cut drops the
   other office's items first, with a line, but a busy day will hide some.
   A two-stroke key (`1` then return) or lettered keys for the other
   offices would lift it. **Scope hints:** bin/office read_key and
   home_screen; lib/office_home.py render_page.

4. **What:** office status names the offices listed and any listed root
   that is no longer an office. **Why:** today only the survey's Machine
   section names them, and a root gone is said only under OFFICE_DEBUG on
   the screens. **Scope hints:** bin/office cmd_status; office_helper
   listed_offices.
