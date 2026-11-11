# Notes: 2026-11-10-practice-rules-001, the practice written down, and two small tools (office-src 0.56.0)

All eight items of the brief landed whole, so the seam was not needed.
Items 1 to 6 are words: the doctrine, eleven templates and the catalog.
Items 7 and 8 are code: bare `office probe` offers the preps, and
`tests/run.sh --fake-day DAY`. The release is 0.56.0, additive.

Every changed path is inside the write forecast. No probe ran and no
question was asked. The office context that rode beside the request (the
folder, the handbook chapter, the profile, the drafting-table blueprint,
twine's contract and the install's two templates) was read and nothing
from it was copied into the tree.

## Decisions

Each one is a place where I chose a mechanism or departed from the brief's
words. Every departure is flagged here with its reason.

1. **C1 fits inside the core by trading words, not by pointing past it.**
   The core keeps exactly 298 lines above the banner (the banner is still
   line 299). Section 9 gained rule 5 within its own lines. Rule 1 now
   points at principle 2 instead of repeating it ("principle 2 says how a
   sitting's words land"). Rule 4 lost its hand-step sentence, because
   rule 5 now covers every step. The two lines rule 5 still needed, plus
   the two the conventions clause needed in section 4 (decision 3), came
   from the two pointer notes. Each pointer note is now one line: "Section
   1 ... sits past the core banner, first." and "Section 4 continues past
   the core banner, then sections 5 to 8." Both still begin with the words
   tests/test_office.py pins.
2. **Rule 5 drops "say where to run it".** Deviation: the old rule 4 had
   it, and C1's wording does not. A four-line rule 5 would not fit, so the
   rule says what C1 says. The sitting, prep and ask briefs still hand the
   occupant office lines, which run anywhere. Put "where to run it" back
   if you would rather trade another line for it.
3. **C4's order is in the core, and in full past it.** The core's
   letterhead bullet in section 4 now ends: "The project's conventions,
   its handbook chapter's `## Conventions` (0.56.0), win over the voice
   page for the form of what leaves; the voice page keeps the words." A
   build session reads only the core, so that is where the order has to
   be. Section 5's Handbook paragraph says the whole of it: who writes the
   section, that `office land` never does, and what a session does when
   the chapter settles nothing.
4. **The chapter's place is one line, `None settled yet.`** It sits
   between `## Front sheet` and `## Facts`, so facts still grow at the
   end of the file. The chapter block is pinned three ways (the doctrine,
   handbook/README.md's template, and what render_chapter, set_front_sheet
   and append_facts write: tests/test_sort.py
   test_the_chapter_is_one_block_and_the_code_writes_it). A long
   explanatory paragraph would have had to sit inside the illustrative
   block, so the explanation went to the doctrine and the handbook front
   page. An example of settled conventions went into the doctrine's own
   paragraph.
5. **No conventions recorded means: follow the repository's own rule.**
   The brief pins "A chapter without the section reads as none." I read
   "none" as "the office has settled nothing", not as "the voice page
   governs". So with nothing settled, a session follows the repository's
   own CONTRIBUTING where it speaks, never the voice page over it, and
   says in notes.md that the chapter has none. That is C4's friction
   exactly (Conventional Commits in the UI repo). Correct me if you meant
   the voice page to win there.
6. **No filing mechanism for conventions.** Nothing parses or files a
   `## Conventions` section: the occupant writes it, or a session in the
   office does. chapter_problems still checks only the two sections it
   checked before. A proposal below covers filing it from a light block.
7. **C5: `office start --branch NAME` does not make a fresh branch.**
   Deviation from the brief's parenthesis ("a fresh branch from the
   audience's base: `office start --branch NAME`, 0.50.0").
   office_bale.checkout_branch checks out a branch that already exists,
   locally or as one remote's tracking branch, and refuses one that does
   not. The branch made from the audience's base is office deliver's
   delivery branch. So the sitting brief and the doctrine say what is
   there: each feature is its own session; its brief names the branch it
   builds on (a BRANCH line, with `--branch NAME` as the twin for a
   session that is not a bundle's, or none for the workbench); and before
   sending it, the sitting checks with a probe that the base holds what
   the session depends on. If it does not, the session waits. Otherwise
   the delivery would carry the earlier feature's work too (deliver says
   so, but by then it is late).
8. **C2's words name no character.** The rule says "punctuation, phrasing,
   naming" in the voice page's head, delivery.md's head, and the merge and
   undo briefs. In delivery.md the rule sits in the head paragraph, which
   delivery_leaving_text blanks, never in the Commit or Review sections.
   For merge and undo, "what leaves" is the files they ship, so the rule
   says a code comment counts. A test runs the cleanup list over the
   delivery template's leaving words and over every new rule sentence.
9. **The chat kind is retired, not redefined.** A chat with a folder is
   that folder's work session (the `work` verb: answer, draft, probe,
   decide, deliver). It already lands on the folder's own pages. A
   transcript.md would be a second, unread copy. A chat with no folder is
   the ask. So `[verbs.chat]` is gone, and a comment in its place says why
   and answers Q-3: a chat lands as the ask's LEARNED block (its notepad
   page, the handbook's facts, its questions and answers). The doctrine's
   ask row and section 8 say the same. DECLARED_KINDS in
   tests/test_office.py loses chat. **Anchor gone:** the brief says "the
   doctrine's verbs table names both", but at 0.55.0 the table has an ask
   row and no chat row. Undeclared kinds never needed one (the test
   allowed that). So the table change is a parenthesis in the ask row.
   Q-3 was named only in share/verbs.toml in this tree.
10. **The preps offered: one chooser, the old words kept.** The bare path
    moved into `probe_bare_session` in bin/office. It runs before the prep
    lines, so a chosen prep goes through the existing `--prep` code
    unchanged. The order is: folders' sittings, then the preps (a prep is
    a read-only sitting too), then the rest. With no prep out, every line
    is word for word what 0.55.0 said; the existing pins in
    tests/test_home_screen_offers.py hold that. With a prep among the
    rows, the lines say "sessions" and name `office probe --prep SID`.
    The home screen's `r` key shows while a prep is out
    (office_home.probe_key_shown). The screen's meetings already include
    every prep out, whatever its day (office_meeting.near).
11. **The fake day is a new variable, not FAKE_BALE_DAY.** Env does not
    pass the runner's environment through. Tests set and delete
    FAKE_BALE_DAY themselves (tests/test_land.py open_on_the_eighth), so
    reusing it would send such a test back to the clock mid-run. The run's
    default is FAKE_BALE_DEFAULT_DAY instead. The runner sets it only from
    the flag and removes a caller's own (fake_day_env). Env hands it to
    every fake under the runner. pack_bale.minting_day reads the test's
    day first, then the run's, then the clock; land_bale's handoff mints
    through it. --fake-day goes with all four ways to run (whole, --fast,
    --serial, --detach), and modules too.
12. **One more helper start on a bare probe.** Bare `office probe` now
    reads the preps (probe_py preps-out) beside the folders, and a chosen
    prep reads them once more in the prep lines. No suite test counts a
    probe's helper starts. About 50 to 100 ms, and only when no folder is
    named.

## The suite

The baseline whole suite on the unchanged tree: 1559 tests, all passed
(3 jobs). After the change, the whole suite ran under `--fake-day` set
about five years ahead (computed, not written): 1590 tests, all passed
(2 jobs). That run was item 8's own sweep, and it found nothing: no test
reads a session's day from the clock. After that run I rewrapped two
doctrine paragraphs and two brief lines, so the whole suite ran once more
on the tree as shipped: 1590 tests, all passed (2 jobs).

validation.sh ran twice before shipping, in a copy staged as bale stages
it. With the change applied, every check passed; the fast tier with
test_practice_rules and test_sort named took about 68 s of its 120 s
budget. On the unchanged tree, every check of the change failed. Five
checks pass on both, by design: they assert what the brief pins as
untouched or kept (the banner at line 299, the occupant's section of the
voice page byte for byte, migrations/ unchanged, no cleanup named in the
delivery template's leaving words, the two executable bits).

New: tests/test_practice_rules.py, 31 tests (30 in its job, 1 in the
serial lane). Changed pins: tests/test_sort.py (the chapter block's
heading, `in three parts`; the filed chapter now shows `## Conventions`;
TestTheSortBriefSaysWriteFactsBare keeps its sentence and pins the clause
after it) and tests/test_office.py (DECLARED_KINDS without chat; Env
hands on the fake day).

## Walkthrough

### What changed

- doctrine/OFFICE.md: house rule 5 (words to the occupant) inside the
  core; the core's letterhead bullet says the conventions win over the
  voice page for the form; section 5's Handbook paragraph has the third
  part, `## Conventions`, and who writes it; the BRANCH paragraph says
  one pull request per feature and the base check; the prep paragraph
  says bare probe offers the preps; the ask row and section 8 retire the
  chat kind and answer Q-3.
- templates: handbook-chapter.md and handbook-README.md have the
  Conventions place; letterhead-voice.md's head (office-src's part) has
  the cleanup rule and the conventions order; delivery.md's head has
  both; merge-brief.md and undo-brief.md have the cleanup rule;
  sitting-brief.md has words to the occupant, the branch per session,
  the base check and the conventions pointer; prep-brief.md and
  ask-brief.md have words to the occupant; sort-brief.md and
  drop-brief.md say a fact may wrap.
- share/verbs.toml: `[verbs.chat]` retired, with the reason in its place;
  the probe's comment mentions the preps.
- bin/office: probe_bare_session, and cmd_probe's bare path through it;
  usage_probe's FOLDER line.
- lib/office_home.py: probe_key_shown, the r key's rule.
- tests/runner.py and tests/run.sh: --fake-day; tests/fakes/pack_bale.py
  minting_day, used by land_bale.py too; tests/test_office.py's Env.
- README.md, RELEASES.md, VERSION, claude/context/front-sheet.md: the
  release.

### Why

The gaps report of 2026-10-28, section C. The occupant had to ask what a
login shell was (C1). A pull request's body said a cleanup had been made
(C2). Workers followed the voice page over a repository's own
CONTRIBUTING twice (C4). The team wants one pull request per feature from
main (C5). Then two workers' proposals (the wrapped fact, the chat kind)
and 0.55.0's two (the preps on bare probe, the far-day sweep as a flag).

### How to explain each piece

- Rule 5: every step he is handed is the command plus one sentence on
  what it does and what he will see; no term without its meaning;
  machinery only when he asks.
- The cleanup rule: a fix made only to keep the letterhead is made and
  never mentioned. The check refuses the words since 0.38.0; now the
  pages that tell sessions how to write say it too.
- Conventions: one answer per project, in its handbook chapter, settled
  with the reviewer once. They decide the form (commit style, the
  review's shape, which repository), and the voice page keeps the words.
- One pull request per feature: a sitting gives each feature its own
  session and checks the base already holds what the session needs.
- The chat kind: the ask is the chat; a chat about a folder is its work
  session.
- Bare probe: a prep's block runs with one copy and one word now, like a
  folder's.
- --fake-day: the whole suite with every fake session minted on a far
  day, which finds a test that reads the day from the clock.

### Questions a reviewer will ask

- Why not keep "where to run it" in the house rules? Decision 2: the core
  has no line for it. The briefs hand office lines, which run anywhere.
- Why is `None settled yet.` all the chapter says? Decision 4: the block
  is pinned three ways, and the explanation lives in the doctrine and the
  handbook front page.
- Does a chapter made before 0.56.0 need a migration? No. It reads as
  none settled, and chapter_problems is unchanged.
- Why does `--branch NAME` appear as a twin and not as "a fresh branch"?
  Decision 7: it checks out an existing branch only.
- Why retire chat rather than build it? Decision 9: both of its shapes
  already exist.
- Does a test's own FAKE_BALE_DAY still win under --fake-day? Yes
  (TestAStartMintsOnTheFakeDay, and the minting_day units).

### A hand test

1. In an office with a meeting near and its prep out (`office start
   --prep`), copy any probe block that has no run line, then run `office
   probe`. You should see one line saying the calendar records the one
   session open, the prep's name and id, and then the usual header and
   question.
2. Send a session out on a folder too, copy the block again and run
   `office probe`. You should see "Sessions open where probes run:" with
   the prep and the folder, each with a key. Answer the prep's key, then
   say no at "Run it?".
3. Walk in (`office`) on a terminal with only the prep out. The `r` key
   should be in the menu.
4. In office-src's checkout: `tests/run.sh --fake-day 2031-02-03
   test_practice_rules`. The first line should say the fake bales mint
   sessions on that day, and the run should pass.
5. Open handbook/README.md's template and a newly made chapter, for
   example after the first fact on a new project: the chapter shows `##
   Conventions` with `None settled yet.` between its front sheet and its
   facts.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: practice-rules

### Commit

Write down the practice, offer the preps to bare probe: office-src 0.56.0

House rule 5: every step handed to the occupant is the exact command and
one plain sentence on what it does and what he will see, with every term
explained at first use. The sitting, prep and ask briefs say it. A fix
made only to keep the letterhead is never mentioned in what leaves: the
voice page, the delivery page and the merge and undo briefs say so. A
project's handbook chapter has a Conventions place, settled with its
reviewer once, which wins over the voice page for the form of what
leaves. A sitting gives each feature its own session and checks the base
holds what it depends on. The sort and drop briefs say a fact may wrap.
The unbuilt chat kind is retired: the ask is the chat, and Q-3 is
answered. Bare office probe and the home screen's r key offer the preps
out beside the folders. tests/run.sh --fake-day DAY runs the suite with
the fake bales minting every session on DAY.

### Review

Write down the practice, offer the preps to bare probe: office-src 0.56.0

Look at doctrine section 9 and the core's letterhead bullet (the core is
still 298 lines), section 5's conventions paragraph, the BRANCH
paragraph's addition, templates/delivery.md's head, share/verbs.toml
where chat was, bin/office probe_bare_session, office_home
probe_key_shown, tests/runner.py read_fake_day and fake_day_env, and
tests/fakes/pack_bale.py minting_day (notes, decisions 1, 5, 7, 9 and 11).
To try it by hand, follow the walkthrough's hand test. Deliberately
untouched: C3 and C6 (bale's), pages_from_notes, the tables, an
unlisting verb and a streamed ride copy.

## Structure

- title: The practice written down, and two small tools
- size: medium
- goal: Write down the practice: words to the occupant, a cleanup never named, a project's conventions over the brief, one pull request per feature, a wrapped fact, the chat kind settled, and two small tools: office-src 0.56.0

## Handbook

### office-src

- doctrine/OFFICE.md's core is exactly 298 lines above the PAST THE CORE banner (line 299, pinned by tests/test_office.py, tests/test_ask.py, tests/test_handoff.py and tests/test_from_the_artifact.py); a core change trades words within those lines, and 0.56.0 spent the two pointer notes' second lines
- house rule 5 (doctrine section 9) is words to the occupant: the exact command and one plain sentence on what it does and what he will see, no bale or office term unexplained at first use, machinery when he asks
- a handbook chapter's third part is `## Conventions`, between its front sheet and its facts (templates/handbook-chapter.md, `None settled yet.`); it is the occupant's or an office session's to write, office land never writes it, and chapter_problems does not check it
- the chapter block is pinned three ways: the doctrine's block after "in three parts (values illustrative)", templates/handbook-README.md's, and what render_chapter, set_front_sheet and append_facts write (tests/test_sort.py test_the_chapter_is_one_block_and_the_code_writes_it)
- the chat kind is retired from share/verbs.toml (0.56.0): the ask is the chat without a folder, a chat about a folder's job is its work session, and Q-3 is answered by the ask's LEARNED block
- bare office probe chooses through bin/office probe_bare_session: the folders' sittings, then the preps out (office_probe preps_out), then the rest; with no prep out its words are 0.55.0's; the home screen's r key is office_home.probe_key_shown
- tests/run.sh --fake-day DAY sets FAKE_BALE_DEFAULT_DAY for every job (tests/runner.py fake_day_env, never the caller's own), every Env hands it on under the runner, and tests/fakes/pack_bale.py minting_day reads FAKE_BALE_DAY, then it, then the clock; land_bale mints a handoff's id through it
- office start --branch NAME checks out a branch that exists, locally or as one remote's tracking branch; it never makes one (office_bale.checkout_branch)
- tests/test_practice_rules.py holds 0.56.0's tests

#### Front sheet

office-src 0.56.0 writes down the practice. Every step handed to you is
the exact command and one plain sentence on what it does and what you will
see. A fix made only to keep the letterhead is never mentioned. Each
project's handbook chapter has a place for its own conventions, settled
with its reviewer once, and they win over the voice page for the form of
what leaves. A sitting gives each feature its own pull request. Bare
`office probe` and the home screen's `r` key now offer a meeting's prep
too. The chat kind is retired; the ask is the chat. Additive: no
migration.

## Proposals

- **What:** office land could file a settled `## Conventions` section
  from a session's notes.md, for example a `#### Conventions` under the
  project's Handbook heading, written only after a light block's answer.
  **Why:** C4 asks for one answer per project "settled with the reviewer
  once". Today the occupant writes it by hand or through an office
  session, which is a hand step for something a project session learns
  in its own work. **Scope hints:** office_sort parse_handbook and
  file_handbook (beside the Front sheet's whole replacement); the
  doctrine's section 4 Handbook bullet; tests/test_sort.py's chapter pin.
- **What:** office status could name a project with an audience whose
  chapter settles no conventions, one line with what settles them, as
  it names a voice page with no words yet. **Why:** with none settled,
  every session decides the form again from the repository, and says so
  in its notes; a status line makes the gap visible once. **Scope
  hints:** office_sort handbook_lines or chapter_problems' caller;
  office_deliver voice_state's shape.
- **What:** the drafting-table blueprint's watch on Q-3 (its "A chat's
  landing" row, closed by "Q-3 answered") can be ruled closed, and its
  copy of the `chat` declaration retired the same way. **Why:** 0.56.0
  answers Q-3 in office-src's catalog, and the blueprint is the other
  place it is named. **Scope hints:** the blueprint's own repository,
  not office-src.
- **What:** bare `office probe` could read the folders and the preps in
  one helper call (office_helper batch), and the prep lines could take
  the chosen prep's title from that read. **Why:** decision 12: a bare
  probe now starts two helpers where it started one, and a chosen prep
  reads the preps twice. **Scope hints:** bin/office probe_bare_session
  and the prep lines in cmd_probe; batch_call and batch_run.
