# Notes: 2026-11-11-offer-and-conventions-001, a bundle offered the same by either door, and conventions filed (office-src 0.57.0)

All four items of the brief landed whole, so the seam was not needed.
Release 0.57.0 is additive.

Every changed path is inside the write forecast. No probe ran and no
question was asked. The office context that rode beside the request
(home-office's folder, handbook, floor plan and profile; nisaba-src's
blueprints; the install's templates; twine's contract) was read for
orientation, and nothing from it was copied into the tree.

## Where the brief's cites are now

Line numbers in the tree as shipped, so the next brief can cite them.

- bin/office: `batch_call` 92, `cmd_status` 1430 (its `sort:handbook-check`
  call 1458, `deliver:status-lines` 1462), `ask_start_folder` 4951,
  `offer_bundles` 4969, `resolve_bundle` 5789, `bundle_lands_read` 5827,
  `cmd_start` 5987 (it calls `resolve_bundle` at 6185, `offer_bundles` at
  6198, `bundle_lands_read` at 6204 and `ask_start_folder` at 6218),
  `probe_bare_session` 10555 (its one batch at 10564 to 10566).
- lib/office_home.py: `bundle_stem` 275, `same_bundle` 417 (new),
  `opened_from` 432 (the match at 464), `waiting_bundles` 475, `home_items` 733.
- lib/office_bale.py: `bundle_stems` 638, `bundle_records` 648 (new),
  `bundle_brief_sha256` 676 (new), `browser_copies` 5960, `newest_copy`
  5980, `differing_bundle_copies` 5997 (new).
- lib/office_sort.py: `handbook_parts` 282 (new), `parse_handbook` 299,
  `parse_handbook_conventions` 314 (new), `set_front_sheet` 597,
  `conventions_body` 619, `settled_conventions` 627, `set_conventions` 634,
  `file_conventions` 658 (all four new), `file_handbook` 709,
  `handbook_check` 774, `chapter_problems` 813, `file_notes` 836,
  `conventions_to_file` 951 (new).
- lib/office_deliver.py: `audience_projects` 199, `voice_state` 204,
  `status_lines` 233, `conventions_state` 267 and `conventions_lines` 285
  (new).
- share/bale-consumption.toml: `attempts[].bundle` 162, `.stem` 163,
  `.brief_sha256` 164 (new).
- tests/fakes/land_bale.py: the dossier's bundle record at 389.
- doctrine/OFFICE.md: the core's bullet on what a session writes for the
  office 246 to 256 (banner still at 299); what land files 955 to 957;
  the conventions paragraph past the core 1421 to 1462, its land sentence
  at 1437.

## Decisions

1. **A bundle is told by its stem and its brief's hash.** I built the
   brief's guess. `office_home.same_bundle` says a dossier record is the
   bundle in the downloads when the stems agree once ` (N)` is off both
   and, when the record holds a brief hash, that hash equals the one the
   file's bundle.json names. The hash is the one bale wrote
   (`members.brief.sha256`); the office does not hash the brief itself.
   The 0.4.45 captures in claude/fixtures already carry the key, so it is
   inside the read side's floor.
2. **A record with no hash is read by its stem alone, as at 0.56.0.**
   That covers an older bale that did not write the key (read as a
   missing key, said under OFFICE_DEBUG) and a bundle with no brief (bale
   writes null). It is the cautious reading the brief offered. Its cost:
   two different brief-less bundles under one stem still look like one.
   The record's `manifest_sha256` might tell them apart, but I could not
   check what bale hashes for it, so the office does not read it. A record
   that holds a hash, against a file with no brief, is a different bundle,
   and the file is offered.
3. **`--bundle STEM` says when its copies differ.** It still takes the
   newest copy and says so, as at 0.56.0. When a copy it left carries
   another brief, one more line says so:
   `not every copy is the same bundle: STEM.bale-bundle carries another
   brief than the one taken; office start --bundle PATH takes one by its
   path`. This was exactly the occupant's position on 2026-11-11, so the
   line seemed worth it. It is a line, not a question.
4. **The two doors already met; the tests now hold it.** As the brief
   read, both doors go through `bundle_lands_read`. The new tests pick a
   key from three waiting bundles and get no folder or place question.
   The same LANDS line at `--bundle` gives the same "from the brief"
   lines. The occupant's case is held as it happened (STEM, then a newer
   `STEM (1)` with another brief): bare start offers the newer one by key,
   and the key asks no folder. A true copy is left out, both beside the
   original and alone.
5. **A level-four part ends at the next part's heading.** Deviation from
   the brief's words "ends at the next heading". The pin "a notes.md
   without the part files exactly as it does at 0.56.0" needs this: at
   0.56.0 a front sheet ran to the end of its `### PROJECT`, including
   any other heading inside it. So only `#### Front sheet` and
   `#### Conventions` end a part, and a heading that names neither stays
   in the part it falls in (tests: `test_a_notes_without_the_part_reads_as_at_0_56_0`).
   If you meant any heading, it is a one-line change in
   `office_sort.handbook_parts`.
6. **The floor is one well-formed answer line in the notes.** "At least
   one line under `## Questions and answers`" is read as a
   `- DATE question? answer` line (the lines land files from the
   section). Prose there does not count. The answer need not be about the
   conventions: the office cannot tell what an answer is about. The
   doctrine puts that half of the rule on the session.
7. **Whole replacement, as pinned, and what it can lose.** A merge by
   key would keep one thing whole replacement loses: a convention another
   session settled after this session was packed. This session's chapter
   was read before that one landed, so its set does not carry the new
   line. Land names the line as no longer settled, so it does not go
   unseen, but the occupant has to put it back. I built it as pinned.
   The named lines make the race visible, and it needs two sessions on
   one project settling conventions at once. Duplicate lines within one
   set are kept once and said.
8. **What counts as a line that left.** Every non-blank line the section
   held, except `None settled yet.`. So prose the occupant wrote by hand
   in the section is named too when a set replaces it. Lines are compared
   with their whitespace folded.
9. **A chapter with no section gains it before `## Facts`.** If there is
   no Facts section, it goes after the front sheet, and with neither, at
   the end. `chapter_problems` is unchanged: it never checked the
   section, so a chapter reads clean with it absent, reading
   `None settled yet.`, or holding lines. A test pins all three.
10. **Status's line sits in the audience block, after the guard lines.**
    It reads, for example: `conventions: alpha has none settled
    (handbook/alpha.md reads None settled yet.): a session asks you and
    office land files your answer, or you write them in
    handbook/alpha.md under ## Conventions, one `- ` line each`. The
    parenthesis says which case it is: no chapter, no section, the
    template's words, or a section with no `- ` line. It comes from
    `deliver:status-lines`, so it adds no helper call, counts in no
    problem, and leaves the exit code alone. Its label is one character
    wider than the column the others use. I kept the plain word.
11. **Bare probe: one batch, the same lines.** The folders' read keeps
    its stderr dropped (`-q`, as its `2>/dev/null` did), and the preps'
    stderr still reaches the terminal. A batch that fails reads as no
    rows, as each failed call did. The second read of the preps, made
    when a prep is chosen, stays as 0.56.0 left it: the brief's outcome
    covers the bare path's two reads, not that one.
12. **The core bullet traded words, not lines.** It is still 11 lines,
    and the core is still 298 lines above the banner at 299. "Each fact
    the occupant gave it, or that it learned about a project's shape"
    became "each fact it was given or learned". "The handbook chapter it
    carries before it asks anything" became "its chapter before it
    asks". The phrases tests/test_sort.py pins are verbatim.

13. **The 0.56.0 release test no longer reads VERSION.** Every release
    would break it: it looked up the entry VERSION names and expected
    0.56.0's words there. It now takes the version from the front sheet's
    line for its own session, `- V (session
    2026-11-10-practice-rules-001)`, and checks that entry, so no test
    holds a version literal. 0.57.0's release test does the same for this
    session. Release tests from before 0.56.0 pin their own `## X.Y.Z`
    heading, and I left those alone.

## The suite

Baseline whole suite on the unchanged tree: 1590 tests, all passed, in
17 min 23 s on two CPUs. That run shared the CPUs with my own targeted
runs, so it is slower than the brief's 16 minutes.

After the change, whole suite on the tree as shipped: 1618 tests, all
passed, in 16 min 01 s on two CPUs, with nothing else running. Two earlier
whole runs on the way failed on release tests (decision 13, and my own
release test spelling out the marker test_office refuses). Both are fixed,
and the run above is on the shipped bytes.

New: tests/test_offer_and_conventions.py, 28 tests (3 in
the serial lane). Changed pins: tests/test_sort.py (parse_notes now
carries a `conventions` key) and tests/test_practice_rules.py (the
doctrine's sentence past the core: land files a session's Conventions
after the answer, and no migration writes them; and its release test,
decision 13). The fake bale
(tests/fakes/land_bale.py) records each opened bundle's brief hash on the
dossier, computed from the brief's bytes, so it equals the bundle file's
own.

validation.sh ran twice before shipping, in copies staged as bale stages
them. With the change applied, every check passed; the fast tier with
this session's module named took 83.9 s of its 120 s budget, and the whole
run took 1 min 24 s. On the unchanged tree, every check of the change
failed. Two pass on both by design: `bash -n bin/office` and its exec bit,
which assert what is kept. The new module was also run against the
unchanged lib (with the new fake): 24 of its 28 tests fail there. The
four that pass on both pin what the brief keeps: a key picked from several
reads its LANDS line, a true copy stays out, a brief-less bundle is read
by its stem, and status has no line for a project without an audience.

## Walkthrough

### What changed

- lib/office_home.py: `same_bundle`, and `opened_from` reading each
  record's stem and brief hash. So `waiting_bundles`, the home screen,
  bare start, the walk-in, the other offices' cut and `office withdraw
  --bundle` all read it the same way.
- lib/office_bale.py: `bundle_records` and `bundle_brief_sha256`, plus
  `differing_bundle_copies` for find-download's extra line.
- lib/office_sort.py: the Handbook section's parts (`handbook_parts`,
  `parse_handbook_conventions`), and the Conventions filing:
  `conventions_to_file` for the floor and the empty part,
  `file_conventions` and `set_conventions` for the whole replacement,
  and `file_handbook(..., conventions=)`.
- lib/office_deliver.py: `conventions_state` and `conventions_lines` in
  status's audience block.
- bin/office: `probe_bare_session`'s two reads as one batch.
- share/bale-consumption.toml: `attempts[].bundle.brief_sha256`.
- doctrine/OFFICE.md, templates/handbook-README.md and README.md: the
  words; RELEASES.md, VERSION and claude/context/front-sheet.md: the
  release.
- tests: the new module, the fake's record, and two pins.

### Why

The occupant's N8 of 2026-11-11: `office start --bundle STEM` sent the
fifth sitting's bundle and asked nothing, while bare `office start` left
it out and asked which job. Then 0.56.0's three proposals: land files
the conventions a session settled with him, status shows the projects
with none settled, and bare probe makes one helper start.

### How to explain each piece

- The offer: a bundle leaves the offer only when a session was opened
  from that very bundle. bale records the brief's fingerprint, and the
  office now compares it, not just the file name.
- Conventions: a session that asked you about a project's conventions
  writes the whole set at the end of its notes, and land puts it in the
  chapter, telling you any line that left. Without your answer in the
  notes, land leaves the chapter alone and says why.
- Status: one line per project with an audience and no conventions
  settled, with what settles them.
- Bare probe: one helper start instead of two, the same words.

### Questions a reviewer will ask

- What if bale did not record the hash? The bundle is read by its stem,
  as before (decision 2).
- Can whole replacement lose a convention? Only to a race between two
  sessions, and land names the line that left (decision 7).
- Why does "the next heading" mean the next part's heading? To keep
  0.56.0's filing for notes without the part (decision 5).
- Does a chapter need a migration? No. One without the section gains it
  only when a set is filed.

### A hand test

1. With a bundle you have already started in your downloads, save a
   different bundle of the same slug beside it, so your browser names it
   `NAME (1).bale-bundle`. Run `office start`. You should see the new one
   offered (with "2 copies, the newest offered"), and its key should send
   it without asking which job when its brief has a LANDS line.
2. Run `office start --bundle NAME` instead. You should see one more
   line, saying the older copy carries another brief.
3. In a project session's notes.md, put one answer under
   `## Questions and answers` and a `#### Conventions` with two `- `
   lines under `## Handbook`, `### PROJECT`. Land it. The chapter's
   `## Conventions` should hold the two lines, and land's output should
   say they replaced it. Land a second set without one of them: land
   should name that line as no longer settled.
4. Run `office status` in an office with a project that has an audience
   and no conventions. You should see one `conventions:` line for it,
   and nothing else in the output should change.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: offer-and-conventions

### Commit

Offer a bundle the same by either door, file settled conventions: office-src 0.57.0

A planner's bundle is told from the one a session was opened from by
its brief's hash as well as its stem. A different bundle saved under a
stem an earlier session was opened from is offered by bare office start
and the home screen, and its key sends it with the same answers as
office start --bundle. That door now says when the copies it left
carry another brief. A record with no hash is read by its stem, as
before. office land files a session's #### Conventions as the chapter's
## Conventions, whole, after the occupant's answer only, and names each
line that left. office status names each project with an audience whose
chapter settles none, as a line, not a problem. Bare office probe reads
the folders and the preps in one helper call.

### Review

Offer a bundle the same by either door, file settled conventions: office-src 0.57.0

Look at office_home same_bundle and opened_from, office_bale
bundle_records and bundle_brief_sha256, office_sort handbook_parts,
conventions_to_file and file_conventions, office_deliver
conventions_lines, and bin/office probe_bare_session (notes, decisions
1, 2, 5, 7 and 10). To try it by hand, follow the walkthrough's hand
test. Deliberately untouched: the planner's half of N8 (bale-src), the
offices setting, pages_from_notes, and office ask's LEARNED block.

## Structure

- title: A bundle offered the same by either door, and conventions filed
- size: medium
- goal: office-src 0.57.0: a bundle offered and answered the same by either door, land filing a settled Conventions, status naming a project with none settled, bare probe in one helper call

## Handbook

### office-src

- whether a planner's bundle was opened is read from each dossier record's stem and brief hash (office_home same_bundle, 0.57.0): stems equal once ` (N)` is off both, and when the record holds attempts[].bundle.brief_sha256 it must equal the file's bundle.json members.brief.sha256; a record with no hash is read by its stem alone
- office_bale bundle_records reads attempts[].bundle.stem and .brief_sha256 (declared in share/bale-consumption.toml; already in bale 0.4.45's captures); bundle_brief_sha256 reads a bundle file's own, never hashing the brief itself
- the suite's fake bale records each opened bundle's brief hash on the dossier (tests/fakes/land_bale.py, L["briefs"]), computed from the brief's bytes; checkpoint_sha256 and manifest_sha256 stay null there
- office start --bundle STEM takes the newest copy (office_bale newest_copy) and, since 0.57.0, says when a copy it left carries another brief (differing_bundle_copies)
- a notes.md's `### PROJECT` under `## Handbook` has two level-four parts, `#### Front sheet` and `#### Conventions`, in either order; each ends at the next part's heading, and the facts are the `- ` items above the first (office_sort handbook_parts)
- office land files a `#### Conventions` as the chapter's `## Conventions`, whole, only from notes holding a `- DATE question? answer` line under `## Questions and answers` (office_sort conventions_to_file, file_conventions); it names each line that left, says and leaves the same set, and never empties a section from a part with no `- ` line
- office status's `conventions:` line comes from office_deliver conventions_lines inside deliver:status-lines, after the guard lines; it is never a problem and adds no helper call
- bare office probe reads probe-folders and preps-out in one batch (bin/office probe_bare_session); a chosen prep's lines still read the preps once more
- tests/test_offer_and_conventions.py holds 0.57.0's tests

#### Front sheet

office-src 0.57.0 makes bare `office start` and the home screen offer a
planner's bundle the same way `office start --bundle` does. A bundle
saved under the same name as one you started before is offered when it
is a different bundle, and sent with the same answers. When a session
asks you about a project's conventions and you answer, office land
writes the set into the project's handbook chapter and tells you any
line that left. `office status` names each project with an audience
that has none settled yet. Additive: no migration.

## Proposals

- **What:** office ask's LEARNED block could carry a Conventions part
  too, filed through the same `file_handbook(..., conventions=)` under
  the same floor (the ask's own questions and answers). **Why:** the ask
  is the chat without a folder, and a conventions question is the kind
  of thing the occupant settles in a chat. Today it files facts only,
  and the brief kept it so. **Scope hints:** office_ask's LEARNED parse
  and its call of `osort.file_handbook` (near line 525).
- **What:** read the dossier's `manifest_sha256` beside the brief hash,
  once a probe says what bale hashes for it. **Why:** decision 2: two
  different bundles with no brief under one stem still read as one.
  **Scope hints:** office_bale bundle_records, office_home same_bundle;
  one probe of bale's bundle record.
- **What:** the chosen prep's lines in cmd_probe could take the prep's
  title from the bare path's batch instead of reading the preps again.
  **Why:** decision 11: a chosen prep still reads them twice. **Scope
  hints:** bin/office probe_bare_session and the `--prep` lines after it.
