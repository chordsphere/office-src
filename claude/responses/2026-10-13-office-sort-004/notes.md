# Notes: 2026-10-13-office-sort-004 (office-src 0.20.0)

All five parts of the brief are built in one session: `office land` files
a session's Sort, Questions and answers and Handbook; `office moves`
applies sorted drops; `office open --goal` and `office start N` with a
goal and a brief; the handbook; `office start --sort`. The doctrine, the
declarations, the templates, README, RELEASES, the front sheet and
VERSION follow. The suite went from 765 tests to 783 (18 new, in
tests/test_sort.py). Run results are at the end of this note, above the
two pages.

The pre-flight check said it fits, with room to spare. I did not need the
split the brief offered (parts 1 to 3 against 4 and 5).

No light block was sent. No probe was needed: the tree answered what the
brief listed as unverified. `office moves` reads drafting-table/moves.md
through `office_drafting.pending_moves`, line shape `- [ ] DATE MOVE ...`.
`office open` takes the flags its usage lists.

## Where the tree and the brief differ, and the decisions to ratify

Every point below is a deviation or a choice the brief left open. Each
has its reason.

1. **How the standalone sort is known: by its slug.** No folder records
   the sort, so the office needs some way to tell it apart from other
   sessions open in its own registry. Its slug is fixed, `in-tray-sort`,
   so its id is `DATE-in-tray-sort-NNN` (`office_sort.is_sort_sid`).
   That is how the walk-in and `office desk` show it in flight
   ("-> the in-tray (the standalone sort)"). `office land` with no
   argument finds it the same way (`landable_out`), and the "another
   sort is out" refusal reads the registry for it. The office records
   nothing about the sort on its own pages, which keeps the folder rule:
   a folder holds session ids, never copies of bale's records.
2. **`goal` is a field written after the template's block, not one of
   `FIELD_KEYS`.** `tests/test_desk_verbs` pins the folder template's
   field block to `FIELD_KEYS`, and the brief says the template stays
   untouched. So `goal` lives in a new `LATE_FIELDS`, and a new
   `FIELD_ORDER` (FIELD_KEYS with goal after source) is what
   `parse_folder` and the field-line inserts read. `office open --goal`
   writes the line through a new `folder_set_field`, which only writes a
   field the folder does not already have. `office moves` writes it the
   same way for `folder: N`.
3. **All filing now happens before the after-land actions, including the
   two pages.** The brief puts the three new sections after Walkthrough
   and Delivery, and puts the moves before the after-land actions. So
   the old `file_pages_after_land` (which ran after the ratification) is
   now `land_files`, called right after an applied landing: pages, then
   Sort, then Q&A, then Handbook. `land_moves` runs right after it. The
   after-land summary is still land's last lines; a test holds that.
   When only bale's own search found the response, land says one line,
   for any session: `office sessions FOLDER SID --pages FILE`, or the
   new `office sessions --in-tray SID --pages FILE` for the sort. Before
   this, that line was said only for project sessions.
4. **When land runs `office moves`.** It runs when a sorted drop is
   waiting in the in-tray, exactly as the brief says. It also runs when
   the landed session was a standalone sort whose moves page has pending
   lines. Without that second trigger, the hand test's closes would not
   run at landing whenever every drop had been sorted into folders.
5. **`office moves` order and one-writer handling.** It applies the
   in-tray's sorted drops first, oldest first, then the moves page.
   - Each drop gets its own one-writer check through a new `held`, which
     names the session and never ends the command. A drop that cannot
     move is said ("stays in the in-tray: ...") and the rest go on.
   - The moves page's own check runs before anything is applied. If a
     session holds the page, the sorted drops still move and are
     committed, and then the command refuses as before, exit 1, naming
     the session. The existing one-writer test holds that.
   - With no sorted drops, the commit subject is unchanged ("office
     moves: N desk move(s) from drafting-table/moves.md"). With sorted
     drops it says how many came from each source.
6. **What "waited through one session" means:** a session was recorded
   in some folder (an `office sessions: SID in ...` commit) after the
   commit that added the drop's page (`office_sort.drops_waited`, two
   git reads). These are git facts, not clock arithmetic. The sort
   itself records no folder, so it does not count. The walk-in reads it
   only when it works out the Next line.
7. **The Next line's sort rule** sits right after the `--drop` rule, as
   3c in office_bale's list and in doctrine section 7.
   - The `--drop` rule now skips an unresolved drop that has waited. If
     it did not, its `--lane LANE` line would always win, and the sort
     rule could never fire for that drop.
   - The sort rule also fires in an office that scopes no project. A
     sort routes to folders that exist, so it does not need one.
   - The pile is three unsorted drops (`SORT_PILE`) with nothing ready
     on the desk.
8. **The Sort subsection is read strictly.** It needs exactly the six
   keys, in order. `folder:` takes `new`, `N` or `folder N`, and
   `folder: new` needs a `#### Brief`. `facts:` takes `none`, or an
   empty value followed by `- ` lines, or (leniently) one inline fact. A
   subsection that is off the format is said and not filed: the office
   reads this format and the doctrine pins it to the byte. The two brief
   templates and doctrine section 5 now say where fact lines go (after
   an empty `- facts:` line), outside the pinned blocks. The pinned
   format left that ambiguous.
9. **Questions and answers:** only lines of the form `- DATE ...` are
   filed. Any other lines are counted and said as left out. The line
   that names the session is `- from SID:`. A session no folder records
   (the sort) gets its Q&A said and not filed.
10. **Handbook:** a `### PROJECT` heading, or a Sort's project, must
    resolve to one of the floor plan's projects, using 0.19.0's
    `resolve_project` (any case, or the name before a colon). Anything
    else is said and skipped, so no chapter is ever made for a project
    the office does not scope. When one landing brings a Sort's facts
    and a Handbook section for the same project, they go into the
    chapter in one write: the Sort's facts first, then the Handbook's.
11. **Re-filing is not idempotent for Q&A and facts.** Filing the same
    response twice (say, `office sessions ... --pages` after a landing
    that filed already) does not sort a page twice. It does append the
    Q&A lines and the facts again. Deduplicating needs a rule for what
    counts as "the same fact", so I proposed it below and did not guess.
12. **Where `tell:` lines land.** A Sort filed on a page that is already
    in the landed folder's drops/ (the `office start --drop` path) puts
    its `tell:` on that folder's Next straight away. For an in-tray page,
    the `tell:` goes on when `office moves` places the page. The line
    reads `- tell: TEXT (drops/NAME.md)`, so `office desk` shows
    "next: tell: ...". `nobody` writes nothing.
13. **brief.md for `folder: N`.** When the folder already has a brief.md
    with different text, it is rewritten, and the log says so (git keeps
    the old one). When the text is the same, it is kept. A desk folder
    is live paper, the same as walkthrough.md.
14. **`office start --sort` details:**
    - It takes no other argument or flag, and it refuses when no drop is
      unsorted.
    - Its work class is `meta`.
    - "Every folder's folder.md" means the desk's and the filing
      cabinet's, so the session can see history when a drop is about a
      closed job.
    - The unsorted drops ride in the request as well as in the brief,
      like every office session's. Duplication is the price of keeping
      one rule.
    - When the office has a drafting table but no moves.md yet, the page
      arrives through the drafting table's own arrival code. It is
      committed alone, before the pack, because a forecast must name a
      path that exists.
15. **templates/handbook-chapter.md is reshaped** into the pinned shape
    (`# {{project}}`, Front sheet, Facts). Nothing used the old one. The
    new templates are sort-brief.md and handbook-README.md.
    in-tray-README.md gained the page's Sort section. An office that
    already has an in-tray keeps its own front page, because arrival
    never rewrites one.
16. **Chapters riding with bundles.** For a project session, the chapter
    rides in the office's context tarball, from a bundle too. For an
    office session from a bundle, it rides beside the bundle as
    `context-handbook.tar.gz`, since the office adds nothing to a
    bundle's pack line.
17. **Pinned blocks, held to the same bytes:**
    - doctrine section 5's two new fenced blocks (the page's Sort
      section, the chapter) are held against in-tray-README.md and
      handbook-README.md;
    - the Sort format is held across the doctrine, drop-brief.md and
      sort-brief.md;
    - and the code is held to the blocks: a test sorts a real page and
      builds a real chapter and compares the bytes.
    validation.sh checks the three pairs with `cmp`.
18. The core grew by one bullet of ten lines (the brief allowed twelve).
    The banner is now at line 241. Doctrine sections 4, 5 and 7 carry the
    rest.
19. VERSION is **0.20.0**: additive, no migration.

## Paths outside the forecast

None. Every changed path is under the request's `resolved_scope`
(bin, lib, share, templates, doctrine, tests, claude, README.md,
RELEASES.md, VERSION).

## Something the request did not carry

`.gitignore` was not in the request's context, and
`test_office.TestText.test_names_no_model_and_no_office` reads it
(OWN_FILES). Without it, the baseline fast tier failed that one test in
the sandbox. I put a local stand-in in place for my runs only. It is not
in this response and it changes nothing in the repo.

## Tests

- New: tests/test_sort.py, 18 tests.
  - Units: notes parsing (fence-aware), Sort-format refusals, the pinned
    blocks against the code, filing in a hand-built office, the Next
    rule as a pure function, the doctrine and the declarations.
  - End to end on the fake bale: a build session's Sort, Q&A and
    Handbook filed, with its drop minted into a folder; office moves
    with drops that stay and drops that go; the one-writer stop;
    `office open --goal` with `office start N`'s goal and brief; the
    standalone sort out and back, closes and a retire on its moves page
    included; a sort only bale found, filed with `office sessions
    --in-tray`; the sort's refusals.
- Fast tier: five cheap test_sort classes plus one costly test, the
  sorted-drop path's one-writer stop in `office moves`. Why that one,
  and not the costlier round trip, is in the run results below.
- No test reads the machine: Env throughout, plus tempfile under the
  job's TMPDIR, as test_desk_verbs does.

## Run results (worker's sandbox, two cores)

| run | tests | result | wall clock |
|---|---|---|---|
| fast tier, the request's tree | 313 | one failure: the missing `.gitignore` above | 101.8 s |
| fast tier, the changed tree | 325 | OK | 109.7 s (budget 120) |
| validation.sh, a staging copy (request tree plus files/ and apply.sh) | fast tier plus its checks | PASS, every claim agreed | 107 s in all; its fast tier 106.4 s |
| validation.sh's checks on the request's tree, fast tier left out | | syntax, pinned blocks and session assertions FAIL, as they should | |
| the whole suite, the changed tree | 783 | OK | about 29 minutes (4 jobs at a time) |

Reading the fast tier: this sandbox runs it about 15% slower than your
machine. 0.19.0's 313 tests took 92.4 s in its own worker's sandbox and
101.8 s here. So 109.7 s here should be roughly 95 s for you, inside the
120-second budget.

What I left out of the fast tier: the standalone sort's round trip. It
cost 51 s inside the tier (60 s in the whole suite), and it pushed the
tier to 116.6 s. Its place went to the cheaper test that guards the
sorted-drop path of `office moves` (the one-writer stop, 12 s). The round
trip, the landing that files a build session's notes, and the rest of
test_sort run behind `--slow` and in the detached run.

## Proposals

- **What:** deduplicate re-filed Q&A lines and facts when the same
  session's notes are filed twice. **Why:** `office sessions --pages`
  after a landing that already filed appends them again (decision 11).
  **Scope hints:** `office_sort.file_notes`. A fact or Q&A line already
  present with the same SID is the natural test.
- **What:** the digest lists the unsorted drops (0.19.0's proposal).
  **Why:** a sitting opens on the digest, and drops are now a large part
  of what waits. **Scope hints:** lib/office_digest.py needs a new
  section and its pins. That is more than a line, so I proposed it and
  did not take it.
- **What:** `office drop --title` (0.19.0's proposal). **Why:** the
  heading is the first line of the text, which for a pasted thread is
  often a greeting. **Scope hints:** `office_drop.render_page` and
  cmd_drop. It is more than a line, so it is proposed.
- **What:** the drafting table arrives with `office start --sort` when
  the office has none. **Why:** today a sort in an office without a
  drafting table cannot write closes, and its brief tells it to say them
  in notes. Doctrine already says the table arrives with the first verb
  that writes it, so the sort could be that verb. **Scope hints:**
  start_sort in bin/office, one `drafting arrive --page moves.md` call.
- **What:** the meeting spaces, and `tell:` beyond the folder's Next.
  This is out of scope here and stays the brief's. **Why:** the Next
  line is a stopgap carrier for who-to-tell.

## Walkthrough

### What changed

- `office land` (bin/office `land_files`, `file_notes`, `land_moves`;
  lib/office_sort.py `file_notes`): after an applied landing and before
  the after-land actions, it files the response's notes.md in this
  order: the folder's two pages, then the Sort (onto each drop's page),
  the Questions and answers (into the folder), and the Handbook (into
  the chapters). Then it runs `office moves` when a sorted drop is
  waiting, and prints the folders it minted.
- `office moves` (bin/office `cmd_moves`, `move_sorted_drop`;
  lib/office_sort.py `move_plans`, `place`): it applies the in-tray's
  sorted drops first, then the moves page. A drop sorted `new` gets a
  folder minted through `office open`. A drop sorted `N` goes to folder
  N. In both cases the folder gets the page, its brief.md, a History
  line, its goal and a `tell:` line.
- `office open --goal` and `office start N` (bin/office, lib/office_helper
  `LATE_FIELDS`, `folder_set_field`): a goal line on the folder. Start
  offers the goal and sends the folder's brief.md as the brief.
- The handbook (lib/office_sort.py `handbook_arrive`, `file_handbook`,
  `handbook_check`; templates/handbook-README.md and
  handbook-chapter.md): it arrives with the first fact, one chapter per
  project, and the chapter rides with that project's sessions
  (lib/office_bale.py `start`). It also gets an `office status` line.
- `office start --sort` (bin/office `start_sort`; lib/office_bale.py
  `start` with no folder, `sorts_out`, `landable_out`, `sort_move`;
  templates/sort-brief.md): the standalone sort. Its Next rule is in
  office_bale.
- lib/office_drop.py: `set_status`, the status line's one writer. The
  page's text now stops above a filed Sort section. `sorted_waiting`.
- Doctrine core bullet and sections 4, 5 and 7; share/verbs.toml (`sort`,
  plus the amended start, land, moves); README; RELEASES; front sheet;
  VERSION 0.20.0.

### Why

The occupant's count for a routine ask is three steps: drop, start,
land. 0.19.0 made drop and start real. This release makes land bring
back what each Sort decided: the drop gets its folder, the folder gets
its goal and brief, and the facts go into the handbook so nobody is
asked twice. It also gives the drops nothing carried a session of their
own.

### How to explain each piece

- A session never writes the office. It writes notes, and `office land`
  files them.
- A sorted drop in the in-tray is just another desk move. `office moves`
  makes it, the same way it makes a sitting's.
- A folder now remembers its goal and its brief. Starting it later asks
  nothing new.
- The handbook is the office's private notes per project. Front sheet
  for you, facts for sessions, appended only.
- `office start --sort` is the in-tray's own session. It belongs to no
  folder and comes back with `office land` like any other session.

### Questions a reviewer will ask

- *Why a slug rather than a record?* So the office never writes a
  bale-shaped fact. The registry already says which sessions are open,
  and the slug says which one is the sort.
- *What if a Sort is malformed?* It is said and nothing is filed for it.
  The page stays unsorted, so the next session that carries it can sort
  it again.
- *What if the sorted folder is in the filing cabinet?* The page stays
  and that is said. Reopening is your move or a sitting's.
- *Can the moves run while a session holds the desk?* That drop's move
  stops and names the session. The other drops still go on. The moves
  page refuses as before.

### A hand test

This is also the folders cleanup. It is run in home-office after
`./install.sh` (start and land run the install).

1. `office` (walk in). It shows: `In-tray: N unsorted drop(s)`. If the
   0.19.0 hand test's drop is gone, `office drop` a fresh one with no
   project (plain return at the project question) first. Then check
   `ls drafting-table/`. If there is no drafting table, run
   `office digest` once: it makes the table arrive, and the sort can
   then write closes on its moves page.
2. `office start --sort`. It shows: `Packed DATE-in-tray-sort-001 for
   the in-tray (the standalone sort; no folder records it)`, an out tray
   holding the request and the doctrine, and the opener. If the office
   had no moves.md yet, the log line before that reads "office start
   --sort: the drafting table's moves page arrives", and it is a commit
   of its own.
3. `office` again. It shows: `this office: DATE-in-tray-sort-001 ...
   -> the in-tray (the standalone sort)` in flight, and `Next: office
   land DATE-in-tray-sort-001`. `office start --sort` now refuses: "a
   sort is out already".
4. Attach the tray and paste the opener. The session reads the drops and
   the desk, writes its Sort, and appends to drafting-table/moves.md,
   one per line:
   - `- [ ] DATE close folder N` for each of folders 1 to 6 and 8 to 10;
   - `- [ ] DATE retire folder 12 why="queued on 2026-10-12 beside folder
     11, which 0.17.0's landing closed done"`.
   These are the line shapes its brief states: `close folder N`,
   `absorb folder N into="folder M"`, `retire folder N why="..."`.
5. `office land DATE-in-tray-sort-001` (or plain `office land`, which
   finds it). It shows:
   - `Landed: ... is applied in this office`;
   - then `Sort: 1 subsection(s) in ...'s notes.md, 1 filed`;
   - then `office moves`: the sorted drop placed first, then lines 1..N
     of the moves page, each ticked `-> folder N`, and
     `Folders office moves minted:` when the drop was `folder: new`;
   - and "no folder records ..., so there is nothing to ratify in".
6. `office desk`. It shows folders 7, 13 and 14 and whatever the drop
   opened. Folders 1 to 6 and 8 to 10 are in the filing cabinet as done,
   and 12 is there as retired. `office status` shows `folders: ... every
   status agrees`, and `handbook:` when the sort gave a fact.
7. When the drop opened a folder, `office start N` on it sends it out
   with no goal question asked: the log says "the goal is the folder's
   own" when piped, or offers it as the default on a terminal. The log
   also says the brief is the folder's brief.md.

## Delivery

- to: nobody: office-src has no audience

### Commit

Bring back what a sort says, and sort the drops nothing carried

office land now files three more sections of a session's notes after
the folder's two pages. The Sort goes onto each drop's page and marks it
sorted. The questions and answers go into the folder. The handbook facts
go into the project's chapter. When a drop was sorted, land then runs
office moves, which mints the folder a drop asks for (or takes the
folder it names), moves the page in with its brief, goal and who to
tell, and then applies the moves page.

office open takes --goal, and office start offers a folder's goal and
sends its brief.md, so a folder made from a drop goes out without being
asked again. The handbook arrives with the first fact, one chapter per
project, and a chapter rides with its project's sessions. office start
--sort sends the drops nothing carried to a session of their own: it
belongs to no folder, sees every folder and the desk, and can write the
desk's other moves, closes among them.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.
