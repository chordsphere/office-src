# Notes: 2026-10-29-deliver-adds-001

Wave 1's deliver-adds, lib halves only, all five items: office deliver
holds a delivery to the lines it adds, chooses its branch by one rule
and says which, continues on a branch another folder of the office
delivered to, refuses a squash that would deliver another folder's work
twice, and refuses words that name a cleanup. The eight forecast paths
and nothing else; no VERSION, README, RELEASES, doctrine, bin/office or
front-sheet change. The release paragraph and the stale-doc lines are
under the Walkthrough, as the brief asks.

## What I decided, for you to ratify

1. **The diff reader lives in the letterhead module, and refusal reads
   added lines only.** `office_letterhead.changed_in_diff` (name-status
   of a diff, `-M`, deletions aside), `added_line_numbers` (the `-U0`
   hunk headers, path literal), `git_lines` and `held_line` sit beside
   `changed_in_tree`, and `check()` gains `added=` and `added_base=`.
   With `added` and no range it reads the index against `added_base`
   (deliver passes the delivery's start); with a range, what the range
   adds. A modified file's new text is read, and only hits on line
   numbers the diff added are hits; a new, renamed, copied or
   type-changed file is all added lines, as the brief says. One thing to
   look at: to tell what the pre-existing lines hold, the rest of the
   file is read too, but only to tell, never to refuse. I read "files are
   never read whole" as "never refused whole"; if you meant the told line
   to come from the diff alone, the count would have to go (the diff does
   not carry the other lines). Lines are numbered by newline alone, as
   git numbers them, so a form feed inside a line does not shift a hit
   (`str.splitlines` would have).
2. **Every read in a delivery uses it, land's review too.** plan's step
   8 (`added=True, added_base=start_sha`), each commit's read-back
   (`read_commits`, `SHA^..SHA` with `added=True`) and office land's
   review (`land_review` passes `added=True` through `check_in_project`,
   which sends `--added` to a host with the module on stdin). The brief
   named step 8; I took the other two because read_commits read each
   commit's files whole (the same A2 refusal one step later) and land's
   review promises to read "as office deliver reads them", so a review
   that read whole would warn about lines deliver no longer refuses.
3. **The hand check is unchanged; the module gained `--added`.**
   `office letterhead check` on a tree, a range or `--words` reads what
   it read before (the existing tests pin it). The module's own `--added`
   (with `--range`, or on the index against HEAD; refused beside `--all`)
   is what land's review sends to a host, and bin/office does not pass
   it, so the occupant cannot type it yet. A README line for it is below,
   for home-screen-offers if it wires the flag.
4. **The told line.** `src/views/UploadView.vue: 6 line(s) the file
   already had hold the em dash (U+2014); not this delivery's, not
   refused`: the check's own label for a character, `kind 'match'` for a
   pattern, up to four distinct things named and the rest counted. It
   reaches the screen today through `check_told`, which bin/office
   prints under "letterhead on the diff and the words". The scope line
   now reads `the lines the index adds against START to the N file(s) it
   changed, ...` and a count line follows (`K added line(s) read in N
   file(s); a line a file already had is never a hit`).
5. **The cleanup list: `[cleanup]`, words only.** share/letterhead.toml
   gains a section read by `load_rules_toml` like the others (required,
   so a missing section fails loudly) and named in
   `WORDS_ONLY_SECTIONS`; `compile_rules(rules, words=True)` adds it, and
   check() compiles twice, files without it and words (delivery words,
   `--words` files, commit messages) with it. The hit's kind is
   `cleanup`, and render says `names a cleanup` (KIND_LABELS); every
   other kind renders as before. Patterns: em dash and en dash (a space,
   a hyphen or nothing between, singular or plural), ellipsis and
   ellipses, and a fourth tell, flagged: the three code points written as
   `U+2013`, `U+2014`, `U+2026`, since "replaced U+2014 with commas"
   names the same cleanup. A lift does not lift it (a lift names a
   character). One risk worth knowing: a project whose real work is
   typography cannot say so in its words, and the forbidden list has no
   way to lift a pattern; I left that as it is, since the brief pins the
   list.
6. **The branch rule, and `branch_why`.** `named_branch` takes the first
   two rules (`--branch NAME` as given; else delivery.md's `branch:`
   line, the prefix before it unless the name holds a slash) before
   anything travels; step 4, once the base is fetched, tries the clone's
   checked-out branch (fetched into refs/office/audience/branch; skipped
   when detached, when it is the base, or when the audience lacks it) and
   falls to the slug, behind the prefix. Each says why in one sentence,
   in the plan's new `branch_why` and `branch_rule` (`flag`, `words`,
   `clone`, `slug`) and in an `[office] the delivery branch is BRANCH:
   WHY` log line, so it reaches the screen now. When the slug wins, the
   sentence says what the clone had (`(the clone's branch workbench is
   not on origin)`, `(the clone's branch is main, the base)`). The
   clone's branch with no folder's record is still "made outside the
   office" and needs `--adopt` or the terminal's yes, as 0.34.0 built;
   what changed is that `--adopt` with no `--branch` now acts on it, the
   A4 report's "--adopt changed nothing".
7. **`branch_prefix`, the fifth audience key.** `check_branch_prefix`
   keeps one trailing slash (`feature`, `feature/` and `feature//` are
   all kept `feature/`) and checks each part as a branch name;
   `prefixed_branch` is the one place the prefix goes on. read_projects
   reads it (a bad one is a declaration problem, never fatal),
   set_declarations writes it, `describe_audience` adds a `branch
   prefix:` line when one is set. Because helper's `project-declare` and
   `check-audience-key` loop over AUDIENCE_KEYS, the helper itself now
   takes `--branch-prefix`/`--no-branch-prefix` and `branch_prefix`; no
   verb of bin/office routes it, so until home-screen-offers lands nobody
   can declare it from the office, as the brief says.
8. **The words' branch line.** parse_delivery returns `branch` (None when
   absent), checked by check_base, and a bad line refuses at deliver's
   words step by name. The line sits above the first section with `to:`,
   so delivery_leaving_text leaves it unread like the page's heading, and
   it counts in "its N other line(s)": the branch name is not held to the
   letterhead yet, which the brief gives to m10-pull-requests.
9. **Another folder's branch (A4, rule 3).** `other_deliveries` gathers
   every other folder's `delivered` records for the same project and
   audience, desk and filing cabinet, oldest first (a folder page that
   cannot be read is a warning line, never skipped silently: a delivery
   it records would be unknown). When the chosen branch is on the
   audience, this folder has no record on it and another folder does, the
   delivery continues: `continuing` true, `adopting` false, the range from
   that folder's last delivery there whose workbench commit is an
   ancestor, else where the workbench and the branch parted.
   `branch_why` gains `; desk/6-x delivered to it on 2026-10-28, so this
   delivery continues on it`, and the plan's new `joined` field names the
   folder and day. Beyond the brief, flagged: run()'s Next lines name the
   review already open on that branch (branch_url, as for an adoption)
   rather than a new review's form, and the Delivered line says `(added
   to the branch desk/6-x delivered to)`; the other folder's review is
   open there, so a compare page would mislead. The adopt refusal's words
   changed from "...or is another folder's" to "...nor does any other
   folder of this office...; it is the branch because WHY".
10. **Work delivered twice (A4, rule 4), and what "the base holds it"
    means.** After the sessions are read, any other folder's record whose
    sessions the range carries refuses, unless the record is on the
    branch this delivery continues on (that work is the branch's own) or
    the base holds it. Two flagged departures from the brief's wording:
    the check runs for a continued delivery onto a different branch too,
    not only a new one from the base (the same work would leave twice);
    and "the base holds it" is the record's workbench commit **or its
    delivery commit** being an ancestor of refs/office/audience/base. The
    brief named the workbench commit, but a workbench commit never
    reaches the audience in the ordinary flow, so that test alone would
    almost never be true; a review merged with a merge commit or fast
    forward puts the delivery commit there. A review merged as a squash
    leaves neither, and the office cannot see it from history, so that
    case refuses. When the refusal names a branch that is gone from the
    audience (one `git ls-remote` per branch, on the refusal path only),
    the remedy line says so instead of offering `--branch` onto a branch
    that is not there. `--others-too` never admits it; sessions of other
    folders no record covers stay as they were.

## Why no probe

Every fact the work needed is in the tree the request carries, and the
suite builds the shapes (an audience, a workbench, a second folder, a
merged or deleted branch) in throwaway worlds. The one fact I could not
check here is how the occupant's audiences merge reviews (merge commit,
rebase or squash), which decides how often rule 4's "the base holds it"
can see a merged delivery; decision 10 and the first Proposal say what
follows from each.

## Paths, and the forecast

Every path is inside the forecast: lib/office_deliver.py,
lib/office_letterhead.py, lib/office_helper.py, share/letterhead.toml,
templates/delivery.md, tests/test_clean_delivery.py,
tests/test_delivery_words.py, tests/test_audience_line.py. No new file;
nothing a sibling forecasts (office_probe, office_sort, office_bale and
their tests) is touched. Nothing of the office context lands.

## Things you should know

- Every file:line the brief cites matched 0.37.0 as shipped, function
  and line alike.
- **Found in the code, not this session's to fix:** a continued delivery
  squashes the whole workbench onto the branch with a three-way merge
  from where they parted, so a second delivery that edits a line the
  first one delivered conflicts ("the landed work does not go onto
  origin's BRANCH as it is now"), even with nothing on the audience
  moved. I hit it writing a test and wrote the test around it; proposed
  below.
- When the base holds another folder's delivery, its session still rides
  as another folder's and needs `--others-too`, as before; nothing of it
  is added by the squash (the test checks the stat).
- The files deliver takes out of the index are still named never read:
  in the added-lines read the index no longer lists them, so the check
  takes them from the tree's status as before
  (test_bale_own_commits pins the line, and passes unchanged).
- The told lines and the branch line reach the screen with no bin/office
  change: `check_told` is printed already, and the branch sentence is a
  log line. `branch_why`, `branch_rule` and `joined` are additive plan
  fields for home-screen-offers to print.
- Cost: one `git diff -U0` per modified file per read (step 8, each
  commit's read-back, land's review), where before it was one read of
  the file. Fine at a delivery's size; a delivery of hundreds of files
  would feel it.

## Validation, as it ran here

The request carries the whole tree, so the suite ran in this sandbox
(python 3.13, git 2.43) on the change and on the unchanged tree.

- The eight modules that read deliver or the letterhead, whole
  (test_audience_line, test_clean_delivery, test_delivery_words,
  test_three_gaps, test_bale_own_commits, test_tidy, test_office and the
  serial terminal lane): 267 tests, all passed, on the changed tree; the
  same set but test_office, 120 tests, passed on the unchanged tree
  before I began.
- The whole suite once on the changed tree: 1071 tests in 32 jobs, all
  passed (827 s).
- The new classes (seven, 18 tests) fail on the unchanged tree, as they
  should, each on the missing behavior (8 failures, 10 errors).
- validation.sh, rehearsed in a staging copy (the request's tree,
  `files/` over it, the manifest as `.bale-manifest.json`): every check
  passed and every claim agrees; the fast tier with this session's
  classes took 87 s of its 120 s (374 tests), the whole script 88 s.
  With `--slow` the five deliver modules whole passed too (3 min 52 s in
  all). On the unchanged tree the three behavior assertions and the fast
  tier fail, and the untouched-files pin passes on both trees, as a pin
  on files nobody touched should.

## Proposals

- **What:** a way for the office to know a review was merged as a
  squash, so rule 4 lets the next delivery through. **Why:** a squash
  merge leaves no commit of the delivery on the base, so the refusal
  holds even after the work is on main; with a deleted branch the
  occupant has no remedy but to wait for a fix. A flag that says so
  (`office deliver N --merged-into-base`, recorded in the History) or a
  content test (the squash would add nothing to the paths that record's
  sessions changed) would do. **Scope hints:** lib/office_deliver.py
  `base_holds` and `twice_lines`; bin/office; after home-screen-offers.
- **What:** squash a continued delivery from its range, not from where
  the workbench and the branch parted. **Why:** found writing a test: a
  second delivery that edits a line the first delivered conflicts with
  nothing moved on the audience. Applying the range's net diff onto the
  branch tip (a temporary squashed commit cherry-picked with a
  three-way fallback) would carry only what is new. **Scope hints:**
  plan's step 7 in lib/office_deliver.py; m10-host-refresh holds the
  conflict path and could take it.
- **What:** drop a session the base already holds from the "other
  folders" list. **Why:** after rule 4 lets such a session through, the
  squash adds nothing of it, yet `--others-too` is still asked for and
  the folder's History names it as delivered again. **Scope hints:** the
  `others` dict in plan's step 6.

## Walkthrough

### What changed

- **Deliver holds a delivery to the lines it adds**
  (lib/office_letterhead.py `changed_in_diff`, `added_line_numbers`,
  `git_lines`, `held_line`, `hits_in_lines`, and `check(added=,
  added_base=)` with the module's `--added`; lib/office_deliver.py plan's
  step 8, `read_commits`, `land_review`, `check_in_project(added=)`).
- **The words never name a cleanup** (share/letterhead.toml `[cleanup]`;
  lib/office_letterhead.py `WORDS_ONLY_SECTIONS`, `compile_rules(words=)`,
  `KIND_LABELS`, `render`).
- **The delivery branch by one rule** (lib/office_deliver.py
  `named_branch`, `slug_branch`, plan's steps 3 and 4, the `branch_why`
  and `branch_rule` fields and their log line; lib/office_helper.py
  `branch_prefix` in AUDIENCE_KEYS, `check_branch_prefix`,
  `prefixed_branch`, `BRANCH_LINE_RE`, parse_delivery's `branch`,
  `describe_audience`; templates/delivery.md's sentence).
- **Another folder's branch, and its work never twice**
  (lib/office_deliver.py `other_deliveries`, `commit_known`,
  `is_ancestor`, `base_holds`, `twice_lines`, plan's step 6, the
  `joined` field, run()'s Next lines).
- tests: test_clean_delivery `TestTheLinesADeliveryAdds`,
  `TestDeliverReadsTheLinesItAdds`; test_audience_line `TestTheBranchRule`,
  `TestABranchAnotherFolderDeliveredTo`, `TestWorkAnotherFolderDelivered`
  (with `BranchCase`); test_delivery_words `TestTheWordsNeverNameACleanup`,
  `TestDeliverRefusesWordsThatNameACleanup`.

### Why

The gaps of 2026-10-28. A2: a delivery was refused for six refused
characters a file already held on the audience's own main, and a whole
session went to cleaning them. A3: branches came from the folder's slug
when every branch on the audience is `feature/...`, and the occupant
renamed one on the host by hand. A4: a folder that built on another
folder's delivered branch could not add to it, and the only branch on
offer would have carried the other folder's eleven commits again. C2: a
review's words said the dashes were replaced, which tells the audience
what the letterhead exists to keep from it.

### How to explain each piece

- The added lines: "deliver checks what this delivery writes. A line the
  file already had, already on the audience, is told in one line per
  file and stops nothing."
- The branch: "the branch is `--branch` if you give one, else the
  `branch:` line in the delivery words, else the branch the clone has
  checked out when the audience has it, else the folder's name; a
  project's prefix goes before the short names. The plan says which."
- Another folder's branch: "if another folder delivered to that branch,
  this delivery adds to it, no `--adopt`; it is the office's branch."
- Twice: "if the work since the base carries something another folder
  already delivered, deliver stops and names the branch to continue on,
  unless the base has it already."
- The cleanup words: "the words that leave never say a fix was made
  only for the letterhead; the check refuses those words in commits and
  in the review, never in files."

### Questions a reviewer will ask

- *Can a pre-existing refused line still leave?* It is already on the
  audience; the delivery does not add it, so it leaves nothing new. A
  line the delivery changes is an added line and is held.
- *What if two folders deliver to the same branch at once?* Each plan
  fetches the branch; the second push is refused if the first moved it
  ("a branch that moved on the audience since the fetch"), as before.
- *Why does the base test look at the delivery commit and not only the
  workbench's?* A workbench commit never reaches the audience; the
  delivery commit does, when the review is merged with a merge commit or
  a fast forward.
- *Why is the cleanup list never read in files?* A project's own text
  may name the characters (office-src's README does), and only the words
  describe the delivery.
- *Can the occupant set the prefix now?* Not from the office: the key is
  read and checked; `office projects set NAME --branch-prefix` arrives
  with home-screen-offers.

### A hand test

1. On a project whose audience's main has a file holding a refused
   character on a line, land a session that changes another line of it,
   and run `office deliver N`. The question shows, under "letterhead on
   the diff and the words: clean", `PATH: K line(s) the file already had
   hold ...; not this delivery's, not refused`, and nothing stops.
2. In that folder's delivery.md, add `- branch: results-view` under the
   `- to:` line, and give the project a prefix by hand in the floor plan
   (`branch_prefix = "feature/"` in its `[projects.NAME]` entry, and
   commit it). `office deliver N` logs `the delivery branch is
   feature/results-view: delivery.md's branch line names results-view,
   behind NAME's branch prefix feature/`. Answer `n`.
3. With a second folder whose session landed after the first folder's
   delivery: `office deliver M` (its own slug) refuses, naming the first
   folder's session, folder and branch, and the line `office deliver M
   --branch BRANCH`; that line delivers, `(adding to the branch on the
   audience)`, with no `--adopt`.
4. Put "the em dashes were replaced" in a Review body: deliver refuses
   `delivery.md:L: names a cleanup: 'em dashes' in: ...`, nothing pushed.

### Release paragraph

office deliver reads what a delivery adds, names its branch by one rule,
continues on a branch another folder delivered to, and refuses words
that name a cleanup. What you see: a delivery is refused only for a line
it adds, a commit message or its words; a file it touches that already
held a refused character on other lines gets one line under the
question's letterhead verdict (`src/views/UploadView.vue: 6 line(s) the
file already had hold the em dash (U+2014); not this delivery's, not
refused`) and nothing stops (found 2026-10-28: a delivery was refused
for six em dashes written weeks earlier, already on the audience's own
main, and a whole session went to removing them). The delivery branch
is chosen in one order, and `[office] the delivery branch is BRANCH:
WHY` says which rule chose it: `--branch NAME`; else a `- branch: NAME`
line in delivery.md beside `- to:` (a short name the session supplies,
like `results-view`); else the branch the clone has checked out, when
the audience has it and it is not the base (office start checks out the
branch a brief's BRANCH line names, so it is the one the session built
on); else the folder's slug. A project's `branch_prefix` in the floor
plan (`feature/`, kept with one trailing slash) goes before the words'
short name and the slug, never before a `--branch` name, the clone's
branch or a name that holds a slash; no verb sets it yet. A branch
another folder of the office delivered to is the office's: a delivery
continues on it with no `--adopt`, from that folder's last delivery
there, and the next line names the review already open on it. A branch
no folder's record names keeps 0.34.0's meaning, and `--adopt` now acts
on the clone's branch with no `--branch` (it changed nothing before). A
delivery whose range carries a session another folder already delivered
is refused by name, with the folder, the branch and the day, and
`office deliver N --branch THAT-BRANCH` as the remedy, unless the
audience's base holds that delivery (its workbench or delivery commit is
on the base; a review merged as a squash leaves neither, so that case
refuses, and a branch gone from the audience is said rather than
offered); `--others-too` does not admit it. And the words that leave,
the commit messages and delivery.md's words, are refused for naming a
cleanup made only to keep the letterhead (`delivery.md:L: names a
cleanup: 'em dashes' in: ...`), since such a fix is shipped clean and
never mentioned; files are never held to it, office-src's own text
included. What changed: lib/office_letterhead.py reads a diff's added
lines (`changed_in_diff`, `added_line_numbers`, `git_lines`,
`held_line`, `check(added=, added_base=)`, and `--added` on the module)
and keeps a words-only list (`WORDS_ONLY_SECTIONS`,
`compile_rules(words=)`, the `cleanup` kind rendered `names a cleanup`);
share/letterhead.toml gains `[cleanup]` (em dash, en dash, ellipsis and
their code points); lib/office_deliver.py's plan reads the staged
squash's added lines, as each commit's read-back and office land's
review now do, chooses the branch (`named_branch`, `slug_branch`, the
plan's new `branch_why`, `branch_rule` and `joined` fields), reads the
other folders' records (`other_deliveries`) to continue on their branch
or refuse their work twice (`base_holds`, `twice_lines`), and run()'s
Next lines name the open review for a continued branch;
lib/office_helper.py has `branch_prefix` as the audience line's fifth key
(`check_branch_prefix`, `prefixed_branch`) and parse_delivery returns the
words' `branch`; templates/delivery.md says the line in one sentence.
The tests: tests/test_clean_delivery.py `TestTheLinesADeliveryAdds` and
`TestDeliverReadsTheLinesItAdds`, tests/test_audience_line.py
`TestTheBranchRule`, `TestABranchAnotherFolderDeliveredTo` and
`TestWorkAnotherFolderDelivered`, and tests/test_delivery_words.py
`TestTheWordsNeverNameACleanup` and
`TestDeliverRefusesWordsThatNameACleanup`, 18 tests in seven classes.

### Stale docs, for home-screen-offers

Each quote is the text as 0.37.0 holds it.

- README.md, the deliver summary (around line 404): "A branch the
  audience already has that the folder never delivered to, a pull
  request opened by hand, is adopted when you say so (`--adopt`, or yes
  on a terminal; 0.34.0)": a branch another folder delivered to is now
  continued with no question.
- README.md, deliver's details, the fetch bullet (around line 1218): "A
  branch the audience has that the folder's records do not cover was
  made outside the office (a pull request opened by hand, or another
  folder's)": "or another folder's" is no longer true; add rule 3 and
  rule 4 here. The brief's sentence belongs here too: a branch renamed on
  the host is told to the office by `office deliver N --branch NEW
  --adopt` on the next delivery.
- README.md, the words bullet (around line 1230): "and `- to: NAME` for
  the reviewer": add `- branch: NAME`.
- README.md, the squash bullet (around line 1255): "and the diff and the
  words go through the letterhead check": now the lines the squash adds,
  a line a file already had told, never refused; and the words held to
  the cleanup list.
- README.md, the shown-whole bullet (around line 1284): "and the branch
  (named from the folder's slug, or `--branch NAME`)": the branch rule,
  the prefix and `branch_why`.
- README.md, land's review (around line 1334): "(the files its landing
  changed, bale's own aside, ...)": the lines its landing added.
- README.md, the letterhead check's list (around line 1353): "What it
  refuses is one list in the install, share/letterhead.toml: the names
  of models, vendors and products; tell-tale phrasing ...": add the
  cleanup list, read in words and commit messages only. If
  `office letterhead check` gains the module's `--added`, a line for it:
  `--added` reads the lines a range (or the index) adds, not the files
  whole, as office deliver reads a delivery; a line a file already had
  is told, never a hit.
- README.md, `office projects` (around line 1519): "A project with an
  audience declares three more, the audience line's": `--branch-prefix
  PREFIX` joins them once the flag is built.
- README.md, layout rows (around lines 1571 to 1573): office_deliver.py's
  row ("since 0.34.0 a branch made outside the office adopted when the
  occupant says so"), office_letterhead.py's ("the characters an office's
  letterhead refuses and lifts, and a repository's pull-request
  templates") and letterhead.toml's ("names, phrasing and bale's marks
  ... and the characters") each want this release's clause.
- doctrine/OFFICE.md section 4, deliver's paragraph (around line 773):
  "runs the letterhead check on the diff and the words": the added lines.
  And (around line 800): "A branch the audience already has that the
  folder's records do not cover was made outside the office, a pull
  request opened by hand or another folder's (0.34.0)": rules 3 and 4.
- doctrine/OFFICE.md, the letterhead's paragraph (around line 998): the
  three characters are described; the cleanup list for words is not.
- doctrine/OFFICE.md, the verb table (lines 1296 and 1297): deliver's
  row, "a branch the audience has that the folder never delivered to
  (made outside the office) adopted when the occupant says so", and
  letterhead check's row, which names the dashes and the template
  exemption but not the cleanup list.
- bin/office usage_deliver: "--branch NAME    the delivery branch's name
  (default: the folder's slug)" and "--adopt ... that this folder never
  delivered to (made outside the office)".
- bin/office usage_letterhead_check: "What it refuses is one list in the
  install, share/letterhead.toml (model, vendor and product names; ...":
  the cleanup list in words.

## Delivery

- to: nobody

### Commit

Deliver reads what a delivery adds and names its branch by one rule

The letterhead check at deliver read every file the squash touched
whole, so a refused character on a line the file already had, already on
the audience's own main, refused the delivery. It now reads the lines
the staged squash adds, each at its line in the new file, as do each
commit's read-back and the review at land; a file's other lines are told
in one line per file and refuse nothing.

The delivery branch is chosen in one order and the plan says which rule
chose it: the --branch flag; a branch line in the delivery words; the
clone's checked-out branch when the audience has it and it is not the
base; the folder's slug. A project's branch prefix, a new key of the
audience line, goes before the short names. A branch another folder of
the office delivered to is continued with no adoption, from that
folder's last delivery there, and a squash that would carry work
another folder already delivered is refused by name with the branch to
continue on, unless the base already holds it.

The words that leave are also refused for naming a cleanup made only to
keep the letterhead, a new list read against words and commit messages
alone, never files.

### Review

Deliver reads what a delivery adds; one branch rule; no work twice

What to look at: lib/office_letterhead.py's diff reader and check's
added mode, lib/office_deliver.py plan's steps 3, 4, 6 and 8 with the
new helpers beside them, and the fifth audience key and the words'
branch line in lib/office_helper.py.

What to try by hand: the walkthrough's hand test, on a project whose
audience's main already holds a refused character in a file the
session touches.

Deliberately untouched: the screen's text and the new flag for the
branch prefix, which the next serial session adds; a review merged as a
squash, which the office cannot see in history, so a delivery carrying
its work still refuses; a continued delivery's squash, which still
merges from where the workbench and the branch parted.

## Structure

- title: Deliver reads what a delivery adds
- size: medium
- goal: office deliver holds a delivery to the lines it adds, chooses the delivery branch by one declared rule (flag, words, the clone's branch, the slug; a project's branch prefix before the short names) and says which, continues on a branch another folder of the office delivered to, refuses a squash that would deliver another folder's work twice unless the base holds it, and refuses words that name a cleanup

## Handbook

### office-src

- office deliver's letterhead check reads the lines the staged squash adds against the delivery's start (office_letterhead.check with added=True, added_base=START), never the files it touches whole; a modified file's other lines are read only to tell what they hold, one `held_line` per file, and never refuse. Each commit's read-back (read_commits) and office land's review (land_review, through check_in_project's `--added`) read added lines the same way.
- Line numbers in the added-lines read are git's (office_letterhead.git_lines splits at a newline alone); hits_in_text still numbers by str.splitlines, so the two differ on a file holding a form feed or a line separator.
- share/letterhead.toml's `[cleanup]` list is words-only (office_letterhead.WORDS_ONLY_SECTIONS): compile_rules leaves it out unless called with words=True, and check() compiles it for delivery words, `--words` files and commit messages alone; its hits are kind `cleanup`, rendered `names a cleanup`. Never apply it to office-src's own text, which names the three characters.
- The delivery branch rule lives in office_deliver: named_branch (`--branch`, then delivery.md's `branch:` line) before anything travels, then the clone's checked-out branch when the audience has it and it is not the base, then slug_branch; the plan's `branch_why`, `branch_rule` (flag, words, clone, slug) and the log line `the delivery branch is BRANCH: WHY` say which.
- `branch_prefix` is the audience line's fifth key (office_helper.AUDIENCE_KEYS); office_helper.prefixed_branch is the one place it goes on, never before a name holding a slash. The helper's project-declare and check-audience-key take it through their loop over AUDIENCE_KEYS; bin/office does not route it yet.
- office_deliver.other_deliveries reads every other folder's `delivered` records for the same project and audience; a record on the chosen branch makes the delivery continue there (the plan's `joined`), and a record whose sessions the range carries refuses the delivery (twice_lines) unless base_holds: its workbench or delivery commit is an ancestor of refs/office/audience/base. A squash merge is invisible to base_holds.
- A continued delivery squashes the whole workbench onto the branch by a three-way merge from where they parted, so a second delivery that edits a line the first delivered conflicts; tests that continue a branch change different lines.
