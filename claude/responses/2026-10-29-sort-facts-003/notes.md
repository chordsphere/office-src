# notes: 2026-10-29-sort-facts-003

office-src, wave 1, lib-only. office land now files a handbook fact bare:
a leading `YYYY-MM-DD:` and a trailing `(SID)` that the session wrote
itself are dropped before land adds its own day and session. The bare
form is also what a filing keys on, so a fact filed twice is filed once.
The sort brief now tells the sort session to write facts bare. No VERSION
bump, and no README, RELEASES, doctrine, bin/office or front-sheet
change: the release paragraph and the stale doc lines are below, under
the Walkthrough, for home-screen-offers to roll in.

## Decisions to ratify

1. **Where the strip lives.** A new `bare_fact(fact, sid)` beside
   `fact_line`. `fact_line` calls it, so nothing can file a dressed line
   whatever the caller passes. A new `fact_key(line)` reads a Facts line
   back as `(bare fact, sid)`, and `filed_facts` keys through it. Both
   sides of the comparison are bare, so a doubled line filed before this
   session (`- 2026-10-27: 2026-10-28: fact (SID) (SID)`) keys the same
   as that fact filed bare now. That holds when the planner refiles an
   old response with `office sessions --pages`: nothing is written a
   second time. The doubled line itself stays as it is (item 2), and
   `chapter_problems` still reads it as a Facts line, since it matches
   FACT_LINE_RE.
2. **"An ask's name", as I read it: the filing session's own slug.** The
   brief says a trailing `(SID)` goes "where SID reads as a session id
   ... or as an ask's name". Nothing in the code or the doctrine defines
   an ask's name as a token, so I took it to be the name bale gives the
   ask in the session id, its slug: `(fix-login)` is stripped when
   2026-10-14-fix-login-001 files it, and kept when any other session
   does. The wider reading, any slug-shaped word in parentheses, would
   eat real fact endings such as `(utf-8)`, `(tomllib)` or `(bale)`,
   which this session must leave alone. If you meant something else (a
   folder's name, say), it is a one-line change in `bare_fact`.
3. **The exact patterns.** The leading date is `YYYY-MM-DD:` followed by a
   space or the end, repeated; a date with no colon (`2026-10-28 is the
   day ...`) reads as a sentence and stays. The trailing tag is one
   parenthesised token with no space in it, repeated: a session id by
   `oh.SID_RE`, the same shape bin/office checks, or the ask's name
   above. Both strips loop until nothing changes, so `DATE: DATE: fact
   (SID) (SID)` comes out bare in one call. Whitespace is folded first,
   which `oh.one_line` did anyway.
4. **A fact the same filing gives twice is now filed once.** Before, the
   same fact as a Handbook line and as a Sort's `facts:` line (or listed
   twice) was written twice in one filing. A second filing then skipped
   both. Now the second copy is skipped within the filing too, and land
   says `N given twice, filed once`. It is the brief's "a fact filed
   twice files once", read for one filing as well as for two.
5. **A fact that is nothing but a date and an id is not filed, and land
   says so** (`N fact(s) from SID held nothing but a date and a session
   id, so nothing of them is filed`). Before, it would have been filed as
   its own text. Now there is nothing left of it to file, and saying so
   beats both a silent skip and a HelperError that would stop the whole
   filing.
6. **land says when it dropped something.** When a fact came dressed,
   land's handbook lines add `N fact(s) from SID came with a date or a
   session id of their own, dropped before filing, since office land
   adds both (write facts bare)`. That line names the session, so a
   session still writing dated facts shows up on every landing. It says
   it again on a refiling, which is true each time.
7. **The day is untouched**, as the brief pins: `day` is still the one
   bin/office hands land from the office's clock. No code here reads the
   session id's date.
8. **No word in the chapter template or the handbook README.** Both
   describe the filed form (`dated and naming the session`), which has
   not changed. A reader of the chapter sees nothing new, so the forecast
   stays as packed.

One anchor in the brief differs from the code, and the name wins: a
Sort's `facts:` lines reach `file_handbook` through `file_notes` (where
it gathers `facts_by`, about line 606 at 0.37.0), not through
`file_sort`, which files only the drop's page. This changes nothing,
since both paths end in `file_handbook`, which is where the strip
applies.

## Outside the write forecast

None. Every path is in the forecast: lib/office_sort.py,
templates/sort-brief.md, tests/test_sort.py.

## Places to look closely

- lib/office_sort.py `bare_fact`: the loop and the ask's-name test.
- lib/office_sort.py `file_handbook`: the new counting loop (already,
  twice, dressed, empty) and the words. The old `else` branch is now
  `elif already`, so a filing whose facts were all empty does not claim
  "all 0 fact(s) already there".
- tests/test_sort.py: TestFiling's setUp moved into a module helper,
  `small_office(root)`, shared with the new classes. TestFiling itself
  is unchanged. The sort brief's sentence sits outside every fence, and
  the pinned Sort format block is byte-for-byte as it was
  (TestThePinnedBlocks passes unchanged).

## Validation

- `tests/run.sh --fast` with this session's classes and the two existing
  classes the change runs through (TestThePinnedBlocks, TestFiling):
  passed, observed, 363 tests in 75 s of the 120 s budget.
- tests/test_sort.py whole: passed, observed, 25 tests in 29 s. It is
  behind validation's `--slow`.
- The seven new tests against the unchanged code: all seven fail (two
  error on the missing `bare_fact`; five fail on doubled or unchanged
  lines and on the brief without its sentence). The 18 tests that were
  there pass on both trees.
- The whole suite on the changed tree, run here with four jobs: passed,
  observed, 1060 tests in 800 s.
- validation.sh --slow, rehearsed on a copy of the request's tree with
  files/ laid over it and apply.sh run: every check passed, the fast tier
  in 81 s of its 120 s, and both claims agreed with their verdicts.
  Afterwards the copy differed from the request's tree only in the three
  shipped files, its .validation-logs/ and the placed manifest, and the
  temporary directory was gone. On the unchanged tree the four session
  assertions and the fast tier fail, as they should; the two guards (the
  pinned files untouched, FACT_LINE_RE kept) pass on both trees, since
  the brief pins them.
- One thing the rehearsal caught in my own script, fixed before
  shipping. The first draft pointed TMPDIR inside staging, to keep every
  write there. tests/test_office.py TestInstall copies the whole tree, so
  it copied its own scratch into itself until the fast tier ran out of
  budget. The suite's scratch now goes in one mktemp directory under the
  inherited TMPDIR, named at the top of the output and removed at exit.
  Only the logs stay in staging.

## Proposals

- **What:** office land should file a Handbook fact that wraps onto
  indented continuation lines whole, not just its first line.
  **Why:** `parse_handbook` takes only the lines that start with `- `,
  so a fact wrapped the way markdown wraps a list item loses everything
  after its first line. I ran the 0.37.0 session's own notes.md (the
  response to 2026-10-28-m10-land-flags-005, archived with the others)
  through it, and all five of its office-src facts come back cut off, for
  example
  `office land passes bale's two accepts (--accept-checkpoint-change,`
  and `bale 0.4.56 refuses a changed checkpoint with`. Those truncated
  lines are what land filed in that chapter. This session leaves it
  alone: it is not this goal, the brief pins that nothing else about a
  fact's words changes, and joining continuations would also change the
  keys of responses filed before (a refiling would add the whole fact
  beside the cut-off one). It also bears on this session's own goal: a
  wrapped fact whose `(SID)` falls on a continuation line is not
  stripped, because that line is never read.
  **Scope hints:** lib/office_sort.py `parse_handbook` (join a `  `
  indented line onto the fact above it, outside fences), and perhaps a
  Sort's fact lines in `parse_sort`. Then tests/test_sort.py, and the
  doctrine's "one line each" (section 5, Handbook) as either the rule
  sessions must keep or what land makes of a wrapped fact. Until then,
  the doctrine sentence home-screen-offers writes could say "bare, and
  on one line".
- **What:** the drop brief (templates/drop-brief.md) should say "write
  facts bare" too.
  **Why:** a drop session (`office start --drop`) writes a Sort with
  `facts:` lines exactly as the sort session does. The brief's goal
  names only the sort session, and the drop brief is outside this
  forecast. office land strips both the same way, so this is about
  telling the session, not about what gets filed.
  **Scope hints:** templates/drop-brief.md, the paragraph after its
  pinned Sort format (`facts:` is `none` or one or more lines ...);
  tests/test_drop.py if it pins that text.

## Walkthrough

### What changed

- lib/office_sort.py: `bare_fact` drops a leading `YYYY-MM-DD:` and a
  trailing `(SID)` (or the filing session's own slug in parentheses),
  each as many times as written. `fact_line` makes every fact bare
  before it adds land's day and the session id. `fact_key` and
  `filed_facts` read a filed line back bare. `file_handbook` keys bare,
  files a fact the same filing gives twice only once, and says what it
  dropped and why.
- templates/sort-brief.md: one sentence beside the Handbook words: write
  each fact bare, in the Handbook section and in a Sort's `facts:` lines
  alike, since office land adds the date and the session id.
- tests/test_sort.py: four new classes, seven tests (below), and a shared
  `small_office` helper.

### Why

Sessions were writing facts the way they see them in a chapter,
`DATE: fact (SID)`, and land then added its own day and id, so lines
read `- 2026-10-27: 2026-10-28: ... (sid) (sid)` (the gaps of 2026-10-28,
A8, seen in work-office's m10-api chapter). The fix belongs in land, the
one writer of the line, so the line is right whatever a session writes.
The brief sentence makes sessions stop doing it in the first place.
Keying bare keeps the 0.31.0 promise, that a response filed twice adds
nothing twice, across the change.

### How to explain each piece

- "Land writes the date and the session on every fact. If the session
  wrote them too, land drops the session's copy first, so each line has
  one of each."
- "Only the front date and the end tag go. A date or a session id inside
  the sentence is part of the fact and stays."
- "Old doubled lines are not touched; the handbook is append-only. But
  they count as the clean fact, so refiling an old response does not add
  a second copy."
- "The day is still the office's own clock, not bale's UTC date, on
  purpose."

### Questions a reviewer will ask

- Why not use the date in the session id? Because the office keeps the
  occupant's clock and bale keeps UTC (doctrine section 5, Calendar). The
  four hours a day where they differ are by design; the doctrine will
  say so in one sentence (stale doc lines, below).
- Can a real fact lose words? Only a leading `YYYY-MM-DD:` with its
  colon, and a final parenthesised token that is a session id or this
  session's own slug. `(tomllib)`, `(utf-8)`, `(see README)`, a date with
  no colon and an id mid-sentence all stay; the tests hold each.
- What happens to work-office's m10-api chapter? Nothing. Its doubled
  lines stay until the occupant cleans them by hand, once, if at all
  (stale doc lines, below).
- Why is a fact given twice in one filing filed once now? Decision 4.

### A hand test

1. In a test office, land a session whose notes carry
   `- 2026-10-28: the api answers on port 8080 (SID)` under `## Handbook`,
   `### alpha`. The chapter's new line is `- DAY: the api answers on port
   8080 (SID)`, DAY being the office's today, and land's handbook lines
   say one fact came with a date or a session id and it was dropped.
2. Run `office sessions FOLDER --pages RESPONSE` for the same response:
   the chapter is unchanged, and land says the fact is already there.
3. In a chapter, add by hand a doubled line
   `- 2026-10-27: 2026-10-28: x (SID) (SID)`, commit it, and refile a
   response from SID that gives `x`: nothing is added, and `office
   status` still reads the chapter clean.
4. `office start --sort` with a drop in the in-tray: the brief's Handbook
   paragraph says to write each fact bare.

### Release paragraph

A handbook fact is filed bare. A session that wrote a fact the way it
sees one in a chapter, `2026-10-28: the api answers on port 8080
(2026-10-28-fix-login-001)`, got land's day and session added again, so
the chapter read `- 2026-10-27: 2026-10-28: ... (sid) (sid)` (the gaps of
2026-10-28, A8, in work-office's m10-api chapter). Now `office land`
drops a leading `YYYY-MM-DD:` and a trailing `(SID)` the session wrote,
each as many times as it wrote them, before it adds its own: a trailing
id is a session id, or the filing session's own slug in parentheses
(`(fix-login)` from 2026-10-28-fix-login-001). A date or an id inside
the fact's own sentence stays, and so does any other closing
parenthesis. land says when it dropped something (`N fact(s) from SID
came with a date or a session id of their own, dropped before filing,
since office land adds both (write facts bare)`), and when a fact was
nothing but a date and an id and so is not filed. The fact is keyed
bare too. A doubled line filed before this release still keys as its
bare fact, so refiling an old response adds nothing, and a fact one
filing gives twice (a Handbook line and a Sort's `facts:` line) is filed
once, said as `N given twice, filed once`. Nothing filed is rewritten:
the doubled lines already in a chapter stay, for you to clean by hand
once if you want to. The day on the line is still the office's own clock;
it differs from the session id's UTC date for a few hours of every day,
by design. The sort session's brief now says to write each fact bare.
lib/office_sort.py `bare_fact`, used by `fact_line`, and `fact_key`,
used by `filed_facts`, with `file_handbook` keying and counting through
them; templates/sort-brief.md, one sentence beside its Handbook words.
Tests: tests/test_sort.py TestAFactIsFiledBare (the doubled form and each
half come out bare; a date or an id in the fact's own sentence stays;
filed bare, said, and a second filing adds nothing; a Sort's facts and
the Handbook section file bare together), TestADoubledLineFiledBeforeStays,
TestTheSortBriefSaysWriteFactsBare and TestLandFilesAFactBare (through
office land, the office's day and one session id on each line). Seven new
tests; the suite holds 1060, 1053 at 0.37.0. The whole suite, run in the
worker's sandbox, passed all 1060; the detached run after the landing is
yours to record.

### Stale doc lines

Each line below is made stale by this session and is home-screen-offers'
(or practice-rules') to fix. Quoted as they read at 0.37.0.

- doctrine/OFFICE.md, section 4, the bullet "A session writes what the
  office keeps for it" (about line 251), for practice-rules: "each fact
  the occupant gave it, or that it learned about a project's shape, under
  `## Handbook`, `### PROJECT`, as `- ` lines, with a `#### Front sheet`
  paragraph when what the occupant should know changed." It should say
  to write facts bare, for example: "as `- ` lines, each fact bare (no
  date in front, no session id behind: `office land` adds both),". Mind
  tests/test_sort.py `test_the_cores_new_bullet_is_twelve_lines_at_most`:
  the bullet is ten lines now, and its cap is twelve.
- doctrine/OFFICE.md, the one clock, for practice-rules: section 5,
  Calendar, says "Times are local time in the floor plan's timezone;
  bale's clock is UTC." The brief asks for one sentence naming the
  office's clock for every date the office writes, a fact's day among
  them, for example: "Every date the office writes, a handbook fact's
  among them, is the office's day in the floor plan's timezone; a session
  id carries bale's UTC date, and the two differ for a few hours of every
  day, by design."
- doctrine/OFFICE.md, section 4, continued, the landing paragraph (about
  line 722): "The Handbook: each fact as `- DATE: fact (SID)` at the end
  of its project's chapter, with a Sort's `facts:` lines". It could add
  "the fact bare first, a leading date and a trailing session id the
  session wrote dropped, and a fact filed already from that session left
  as it is".
- README.md, the land details (about line 1006): "its `## Handbook`
  facts, each as `- DATE: fact (SID)` at the end of the project's
  chapter, with a Sort's `facts:` lines". The same addition as the
  doctrine's: "each made bare first (a leading date and a trailing
  session id the session wrote are dropped)".
- templates/drop-brief.md, after its pinned Sort format: "`facts:` is
  `none` or one or more lines for the project's handbook chapter, each
  starting with `- `". A drop session writes `facts:` lines too, so the
  sort brief's sentence belongs here as well (Proposals).
- work-office's handbook, not a doc but stale all the same: the m10-api
  chapter holds the doubled lines A8 found (`- 2026-10-27: 2026-10-28:
  ... (sid) (sid)`). The handbook is append-only and nothing here
  rewrites them; the occupant may clean them by hand once, if at all.
  The truncated facts of the Proposals' first item may be there too.

## Delivery

- to: nobody

### Commit

office land files a handbook fact bare

A session that wrote a fact dated and signed, as a chapter shows one,
got the office's day and its session id added again, so a line read
"- DAY: DAY: fact (SID) (SID)". office land now drops a leading date and
a trailing session id the session wrote before it adds its own, and
compares facts in that bare form, so a fact filed twice is filed once
and lines filed before keep matching. A date or an id inside the fact's
own sentence is left as it is, nothing filed is rewritten, and the day
is still the office's own. The sort session's brief says to write each
fact bare.

### Review

office land: a handbook fact is filed bare

What to look at: how a fact is made bare before it is filed, the
comparison that keeps a fact filed twice from being written twice, and
the one sentence added to the sort brief.

What to try by hand: land a session whose Handbook fact starts with a
date and ends with its session id, and read the chapter's new line;
then file the same response again and see nothing added.

Deliberately untouched: the lines already in a chapter, the day on the
line, and the doctrine and README, whose sentences follow in the next
release.

## Structure

- title: office land files a handbook fact bare
- size: small
- goal: Make office land file a handbook fact bare, stripping a leading date and a trailing session id a session already wrote before it adds its own, keyed so a fact filed twice files once, and tell the sort session to write facts bare

## Handbook

### office-src

- lib/office_sort.py bare_fact is the one place a fact is made bare: fact_line calls it on every line it writes, and fact_key (used by filed_facts) reads a filed line back through it, so a filing's keys and a chapter's keys are both bare.
- bare_fact strips a leading `YYYY-MM-DD:` (colon required, then a space or the end) and a trailing parenthesised token that matches oh.SID_RE or equals the filing session's slug (sid[11:-4]); each repeats, and anything else in parentheses stays.
- file_handbook keys a fact by (bare fact, filing sid): the same fact from another session is filed again, and a fact one filing gives twice is filed once.
- parse_handbook reads only the `- ` lines of a `### PROJECT` subsection, so a fact wrapped onto an indented continuation line is filed as its first line alone; write each fact on one line until that changes.
- tests/test_sort.py small_office(root) writes the floor plan and bale.toml a handbook needs to arrive, for tests that file facts without a command.
