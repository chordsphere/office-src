# Notes: 2026-11-05-m10-ask-001, office ask (office-src 0.48.0)

Both halves shipped: items 1 to 6 and items 7 and 8. Nothing went to the
seam. Every path is inside the forecast, so there are no departures to
admit.

## Decisions

Calls the brief left to me, then the deviations, each flagged.

1. **The tray's listing.** `OUT_TRAY/ask-DATE-SLUG/` holds `ask-brief.md`,
   `handbook-PROJECT.md` (when the chapter exists), `letterhead-voice.md`
   and `letterhead-forbidden.txt` (when the office has them), `profile.md`
   and `OFFICE.md`. The chapter and the letterhead pages are renamed so
   that a flat list of attachments still says what each one is. OFFICE.md
   is the whole install doctrine, the same file a session gets. The brief
   tells the chat that the core, down to the banner, is what applies. When
   no chapter exists yet, the brief says so and says the first fact starts
   one.
2. **How the office knows an ask is out.** It's the tray's presence, as
   you suggested, plus one small record next to it:
   `OUT_TRAY/ask-DATE-SLUG.ask.json`, holding the office root, the
   project, the day and time, and the words. The tray alone wasn't
   enough. The tray root belongs to the machine and every office on it
   shares it, so the office needs to know which asks are its own. Filing
   also needs his words back to write the page. The record sits outside
   the tray, the same way the opener's copy does, so "attach every file
   in the tray" stays true. `asks_out` takes a record only when its
   `office` is this office (compared by realpath) and its tray is still
   there.
3. **The opener's words.** "office ask NAME: a quick question from my
   office, with no session behind it. Every file attached is the office's
   context for it. Read ask-brief.md first, answer my question in this
   chat as it says, and end your last answer with the LEARNED block it
   describes." It has no session id and no bale line. A test checks that
   no SID-shaped token and no "bale" appears in it. It prints between
   `--8<-- ask opener --8<--` lines rather than the session opener's
   lines.
4. **The template's words** are templates/ask-brief.md. The block goes
   inside a four-backtick fence so the answer can contain a fence of its
   own. The reader handles both: a fence around the block, and a fence
   inside the Answer, where a `## ` line is not a heading.
5. **Keys.** The home screen gets a fixed `i` key, "a quick question, in
   your words, answered in a chat", which runs `office ask`. Each ask out
   gets one item, `File what ask-... learned (PROJECT): its LEARNED
   block, from the clipboard (office tray ask-... opens its tray again)`,
   which runs `office ask --learned`. I picked `i` because the overflow
   letters after 9 (b, c, e, f, g) are pinned by
   test_folders_and_projects.TestEveryItemHasAKey and
   test_home_screen. A letter after g only changes the fifteenth item
   onward.
6. **Bare `office ask` and the clipboard.** It doesn't ask before filing,
   which matches the sitting's call. It reads the clipboard only when an
   ask is out, and quietly: it uses `paste_command`, falls back to the
   machine's own reader, and never asks for `paste_command`. Asking a
   question doesn't need the clipboard, so there's no reason to ask
   about it there. A clipboard that can't be read, or that holds
   anything other than a block for an ask that is out, just leads to the
   question, said under OFFICE_DEBUG.
7. **No Sort in an ask's block**, as the sitting said. A `## Sort` is
   refused by name: "`## Sort` is no section of an ask's block".
8. **Flagged: no Front sheet either.** `#### Front sheet` under a project
   is refused ("a Front sheet is a session's to write"). file_handbook
   would replace a front sheet whole, and Pinned says filing is
   append-only and nothing filed is rewritten. So an ask files facts and
   nothing else. Tell me if a quick answer should be able to rewrite a
   front sheet.
9. **Flagged: a block naming a project the office doesn't scope is
   refused whole.** Land handles this differently: it files the rest and
   says which facts it dropped. For an ask I check everything before
   anything is written, so one bad heading costs the occupant a re-paste
   and never leaves a half-filed ask. Each refusal gives the line number
   in the text as he gave it.
10. **Flagged: bare_fact also drops the ask's SLUG alone.** For a session
    it drops `(SID)` or `(slug)`. For an ask it now drops
    `(ask-DATE-SLUG)` or `(SLUG)` of that same ask, plus any SID-shaped
    tag as before. A different ask's name is kept, and so is an ask's
    name in a session's filing. file_handbook's dressed and empty lines
    now say "the ask's name" and "office ask" when the tag is an ask.
11. **Flagged, not in the brief: the sittings' window leaves an ask's page
    out.** `notepad/DATE-ask-SLUG.md` matches `SITTING_PAGE_RE`, so
    office_watches.sitting_filings would have counted each ask as a
    sitting. That would have moved the digest's "since the last sitting"
    window and the sittings-since count. It now skips a page that matches
    `ASK_PAGE_RE` and was added by a commit whose subject starts
    `office ask:`. Checking both keeps a real sitting whose slug happens
    to start with `ask-` counted, since its page is added by start or
    land.
12. **Flagged: filing removes the opener's copy and the record as well as
    the tray.** Pinned says the office deletes nothing but the ask's own
    tray. I count the two files beside the tray as part of it: both are
    the ask's, and neither means anything once the ask is filed. Nothing
    else is touched, and nothing is written in the downloads.
13. **The page.** It starts with the notepad template's heading, `#
    DATE: ask NAME, on PROJECT`, and its four lines. Then `## Asked` with
    an `- asked:` line and his words verbatim, then `## Answer` with a
    `- filed:` line and the answer verbatim. That is written whole and
    committed together with the chapters as `office ask: filed NAME (its
    page and facts)`. Then `## Questions and answers` is appended and
    committed alone as `office ask: NAME's questions and answers`. Each
    commit passes append-check first. The page is ASCII-escaped like
    every office page. `--learned none` writes the same page with an
    `- ended:` line instead of an answer.
14. **verbs.toml:** `writes = lands = ["notepad", "handbook"]`, as you
    pinned, which also holds test_office's "lands equal writes" rule for
    scripts. Sending an ask writes nothing in the office. The tray is
    outside the office, as start's is.
15. **The editor's opt-out.** `editor = ""` turns it off and `editor =
    "CMD"` names one over VISUAL and EDITOR, even on a dumb terminal,
    since he named it. With no key, nothing changes. A machine.toml that
    doesn't read gives one warning, and VISUAL and EDITOR decide. bin/office
    `answer_editor_settle` reads the key once per question (through a new
    `helper editor`, exit 3 when not set), because `can_edit` reads
    `answer_editor` in a subshell, which keeps nothing.
    test_answer_review pins `can_edit`'s line, and it is unchanged. The
    log line now names where the editor came from (`machine.toml's
    editor`, `VISUAL` or `EDITOR`) and how to turn it off. REVIEW_HELP
    says both keys.
16. **Flagged, beyond the brief: words after the verb are the question**
    (`office ask does alpha cache?`), as office note takes its text. The
    flag twin `--words` is still there. Giving both is refused.
17. **The doctrine's core.** Section 3's third principle changed within
    its own two lines: "Otherwise the occupant does it or asks (`office
    ask`), leaving a trace." Everything else is past the banner: section
    8's paragraph and the LEARNED block, the verbs table's `ask` row and
    the extended `tray` row, and one sentence on the editor's opt-out in
    section 7. The banner is still line 299, and test_ask checks that.
18. **office help --all** lists `office ask` at the top of "Send a session
    out", with "no session at all" as its first words. No existing group
    fits better, and adding a group would have moved the order that
    test_front_door pins.
19. **Anchors.** Where the brief's line numbers and the 0.47.0 tree
    disagreed, the name won: machine_setting is at bin/office 4418, not
    4140. Everything else the brief named was where it said.
20. **Flagged, a test outside this work:**
    test_folders_and_projects.TestStartsScreenOnATerminal.test_a_bundle_start_that_asks_nothing_prints_twelve_office_lines_at_most
    hard-coded `2026-11-04-screen-pass-001`. The fake bale mints the
    session's day from the UTC clock, so the test only passed on
    2026-11-04. It failed in my baseline run of the unchanged tree
    (1346 tests, that one failure). It now reads the day from the clock,
    as the fake does.
21. **Two pinned tests moved with the change.** The whole run after the
    build found two, both fixed:
    test_land.TestFewerHelperStarts pins office status at one helper
    start and the walk-in at three. My first version read the tray root
    with a `$(...)` next to the batch, so the ask's lines now read
    machine.toml's out_tray inside the batch call (`ask:out-lines
    --machine-file`). test_home_screen.TestTheHomeScreenUnits pins the
    fixed keys' order, and it now has `i` after `o`.

## The suite

- Baseline, the unchanged 0.47.0 tree, whole: 1346 tests in 9m19s on two
  CPUs, one failure (decision 20, the date).
- The fast tier with this session's module (`tests/run.sh --fast
  test_ask`): 389 tests, OK, 57.7 s of the 120 s budget.
- validation.sh in a staging copy (the 0.47.0 tree, files/ overlaid, apply.sh run): every check passed, 56 s without --slow and 3m51s with it (the touched modules whole: test_ask, test_home_screen, test_home_screen_offers, test_start, test_land, test_desk_verbs, test_sort, test_office, test_suite_clock, test_folders_and_projects, test_answer_review, test_watches_digest). On the unchanged tree its five session assertions and the fast tier with test_ask fail, as they should.
- The whole suite with the change, after the two fixes in decision 21: 1369 tests, OK, in 9m32s on two CPUs (the run before those fixes: 1369 tests, two failures, both decision 21's).

## Walkthrough

### What changed

- `office ask` (bin/office cmd_ask; lib/office_ask.py). It takes the
  question in his words, through ask_words on a terminal and `--words`
  or the words after the verb when piped. The project is taken from his
  words, or asked by key when they name none of the office's projects,
  with `--project` and `--in-office` as the twins. It writes one out
  tray with a brief from templates/ask-brief.md and the office's context
  next to it, plus the opener's copy and a record beside the tray. On a
  terminal it opens the tray and puts the opener on the clipboard
  through start's own `start_desktop`.
- `office ask --learned [FILE | - | none [ASK]]` reads the last LEARNED
  block (`read_block`) and checks it names an ask out from this office.
  It writes the notepad page, files the facts through
  office_sort.file_handbook with the ask's name as the tag, appends the
  questions and answers, commits twice, then removes the tray. Bare
  `office ask` files a block on the clipboard for an ask that is out.
- Where an ask out shows: the walk-in (`Asks out:`), office status (one
  `asks:` line), and the home screen (an item per ask, plus the `i`
  key). office tray takes an ask's name, and bare `office tray` offers
  the newest ask the way it offers a session.
- bare_fact and file_handbook's words handle the ask's tag. The sittings'
  window skips an ask's page.
- machine.toml's `editor`.
- The doctrine, README, verbs.toml, fast-tier.toml, RELEASES.md, the
  front sheet and VERSION 0.48.0.

### Why

The M10 report's item 2: an urgent question took five minutes in a plain
chat and would have taken thirty through the office, with none of the
office's benefits kept. The ask keeps those benefits (the chapter, the
voice and the letterhead, the trace) without a pack, a tarball or a land.
The editor's opt-out is 0.33.0's third proposal: before this, the only way
to keep answers at the prompt was to unset VISUAL and EDITOR for the whole
shell.

### How to explain each piece

- The ask is a chat the office prepares and then reads back. The office
  never talks to the model. It writes a tray, and later files a block
  he pastes in. The doctrine's section 7 line (the office never
  dispatches to a model) still holds.
- An ask is out while its tray is there. The record beside the tray only
  says which office the ask belongs to, because offices share the tray
  root.
- Filing goes through land's own code path for facts, so a fact filed by
  an ask looks like a session's, with the ask's name where the session
  id would go.

### Questions a reviewer will ask

- Why does refusing an unknown project refuse the whole block? Because
  nothing is written until everything checks, and one bad heading should
  cost a re-paste, not leave a half-filed ask (decision 9).
- Why not let an ask rewrite a front sheet? Pinned says nothing filed is
  rewritten (decision 8).
- Can an ask's page be mistaken for a sitting's? Not anymore (decision
  11), and test_ask checks it.
- What if he deletes a tray by hand? The ask stops being out, and its
  record is ignored (said under OFFICE_DEBUG). A block for it is refused
  as "not an ask out". Proposals has a line on orphaned records.

### A hand test

1. In an office scoping a project, run `office ask` on a terminal. Type a
   question that names the project, then press return at `[keep]`. The
   tray should open and the opener should land on the clipboard.
2. Attach the tray's files to a fresh chat and paste the opener. Check
   that the chat reads the brief and ends with a LEARNED block inside a
   four-backtick fence.
3. Copy the block and press return on the home screen. The item `File
   what ask-... learned` should be there, and `i` should be among the
   fixed keys. Press the item's key and confirm the notepad page, the
   chapter's facts and the tray's removal are each reported.
4. Put `editor = ""` in ~/.config/office-src/machine.toml, set VISUAL, and
   run `office ask` again. The question should stay at the prompt.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: office-ask

### Commit

Add office ask, the quick path

A question worth a chat and not a session now goes out through office
ask: his words, one out tray with the project's handbook chapter, the
letterhead's pages, the profile and the doctrine beside a brief, and no
pack or land. The chat ends with a LEARNED block, and office ask
--learned files it as a notepad page, facts at the end of the chapters,
and the questions and answers, then removes the tray. The walk-in, office
status, the home screen and office tray show an ask while it is out.
machine.toml's editor turns the answer editor off, or names one over
VISUAL and EDITOR.

### Review

Add office ask, the quick path, and the editor's opt-out

Look at lib/office_ask.py's read_block (each refusal names its line) and
file_block (everything is checked before anything is written), and at
bin/office cmd_ask's two commits and the tray's removal. To try by hand:
send an ask, paste a block back with --learned, and check the page, the
chapter and the tray. Deliberately untouched: office start, office land
and anything of bale's.

## Structure

- title: Add office ask, the quick path, and the editor's opt-out
- size: medium
- goal: Add office ask: a question in the occupant's words answered in a chat with the office's context, its LEARNED block filed, and machine.toml's editor key

## Handbook

### office-src

- an office ask is out while OUT_TRAY/ask-DATE-SLUG exists and its record OUT_TRAY/ask-DATE-SLUG.ask.json names this office; lib/office_ask.py asks_out reads both, and filing removes the tray, the opener's copy and the record
- an ask's notepad page notepad/DATE-ask-SLUG.md has a sitting's page's shape; office_watches.sitting_filings leaves it out by office_helper.ASK_PAGE_RE and a commit subject starting office_helper.ASK_COMMIT_PREFIX ("office ask:")
- a fast-tier entry point must type its verb in the test's own body (self.run_office("VERB"), self.e.run("VERB") or self.VERB(...)); tests/test_suite_clock.py's entry_call does not see through a helper that wraps the call
- the home screen's overflow letters after 9 (b, c, e, f, g) are pinned by tests, so a new fixed key takes a letter after g; 0.48.0's office ask key is i
- bin/office answer_editor_settle reads machine.toml's editor once per ask_words or ask_paragraph question, before can_edit, whose line test_answer_review pins verbatim
- office status is one helper start and the walk-in three (tests/test_land.py TestFewerHelperStarts): a new read of theirs goes into their batch as a call of its own, never a $(...) beside it
- the fake bale mints a session's day from the UTC clock unless FAKE_BALE_DAY is set, so a test that names a session's id should read the day, not write it

#### Front sheet

office-src 0.48.0 adds the quick path. `office ask` takes an urgent
question in your words and writes one out tray for a chat: a brief, the
project's handbook chapter, the letterhead's voice page and forbidden
list, the profile and the doctrine. No session is packed and nothing
lands. When the chat answers, it ends with a LEARNED block. `office ask
--learned` (or the home screen's key, or bare `office ask` with the block
on the clipboard) files it: a notepad page with your words and the
answer, the facts at the end of the project's chapter under the ask's
name, and the questions and answers. Then the tray goes. While an ask is
out, the walk-in, office status and the home screen show it, and `office
tray` reopens its tray. machine.toml's `editor` can now turn the answer
editor off (`""`) or name one over VISUAL and EDITOR. Additive: no
migration.

## Proposals

- **What:** let the walk-in's Next line, office_bale.next_move, name an
  ask that is out. **Why:** today an ask out shows in its own section and
  on the home screen, but the Next line never points at it, so an ask
  left for a day can fall below the desk's moves. **Scope hints:**
  lib/office_bale.py next_move and its tests. It is the read side's, so I
  didn't touch it here.
- **What:** have the digest list the asks filed since the last sitting,
  with their pages. **Why:** a sitting now carries nothing about asks.
  The window skips their pages (decision 11), but the facts and answers
  they filed are things a planner would want to see. **Scope hints:**
  lib/office_digest.py, and the asks' commits by their `office ask:`
  subject.
- **What:** have office status name an orphaned ask record (a record
  whose tray is gone) with the one line that removes it. **Why:** a tray
  deleted by hand leaves `ask-...ask.json` behind, ignored under
  OFFICE_DEBUG, and nothing ever removes it. **Scope hints:**
  lib/office_ask.py asks_out and status_line.
- **What:** decide what share/verbs.toml's declared `chat` kind (built =
  false, lands desk/{folder}/transcript.md, "Q-3, open") is now that the
  ask exists. **Why:** the two overlap. The ask is the chat without a
  folder, and the declaration still reads as the plan for it.
  **Scope hints:** share/verbs.toml, the doctrine's verbs table.
- **What:** sweep the suite for other tests that hard-code a session's
  day. **Why:** decision 20's test only passed on one day, and the
  baseline run was the first place it showed. **Scope hints:** a grep
  for `2026-1[01]-\d\d-[a-z-]+-00\d` under tests/ next to calls that
  pack.
