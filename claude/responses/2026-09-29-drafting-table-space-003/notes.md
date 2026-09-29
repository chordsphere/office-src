# notes.md: 2026-09-29-drafting-table-space-003

## What the probe established

The nisaba-src context tarball the brief said rode beside the request
did not arrive, so the session opened on a paste-back probe. It found
nisaba-src beside office-src on chordsphere (`../nisaba-src`, git HEAD
f0dee6f, both files clean), and returned `blueprints/drafting-table.md`
whole (1416 lines, sha256 f7bade8e...27277a, the hash I re-derived from
the paste) and `nisaba-seed.md`'s sections 2 and 8. Everything below is
built from that copy of the blueprint. If the file has moved since,
this response was built against f0dee6f.

## What I decided that you did not

**Skeleton file names.** `templates/blueprint.md` and
`templates/close-report.md` as the brief names them, and the eight page
skeletons flat in `templates/` as `drafting-table-README.md`,
`drafting-table-agenda.md`, `drafting-table-rulings.md`,
`drafting-table-evidence.md`, `drafting-table-watches.md`,
`drafting-table-watch-log.md`, `drafting-table-riders.md`,
`drafting-table-moves.md`. Flat rather than a subdirectory because the
suite's office-bound text rules (ASCII, no fingerprints) glob
`templates/*.md` at the top level; a subdirectory would have escaped
them. Each skeleton lands as `drafting-table/<name after the prefix>`.
No template for `digest.md`; the README skeleton says why.

**What `office open` writes into the field block today.** Exactly two
lines under the title, `- status: queued` and `- queued: <date in the
office's zone>`, and one History line, `- <date> queued: office open`.
No `number:`, `class:`, `size:`, `lane:`, `source:` or gate line: the
template carries only the two placeholders, and its prose says the
office command writes the rest when the verbs that mint them arrive.
When session 4 adds `--source`, that line's text is where the source
goes. The Riders section is present and empty (prose only).

**The interface of `filed-append-only.sh`.** One spec per argument:

    filed-append-only.sh [--root DIR] PATH=SIZE:SHA256 ... PATH=new ... PATH=@BASEFILE ...

`PATH=SIZE:SHA256` is the strict case from the blueprint: the first
SIZE bytes of the staged page must hash to SHA256, where SIZE is
measured from the shipped copy and SHA256 is the request's
`base_files` stamp. `PATH=@BASEFILE` measures both from a copy of the
base (handy in tests and when a worker has the shipped copy at hand).
`PATH=new` is a page the session created: it only has to exist. One
`[PASS]`/`[FAIL]` line per spec naming the path and why, a summary
line, exit 0/1, and 2 for a bad spec or a missing hash tool. The file
is a function (`filed_append_only`) above a marker line and a two-line
driver below it; a worker pastes the function into `validation.sh` and
calls it with the specs, or runs the script from the office root. The
suite pins all of it (`tests/test_filed_append_only.py`, 12 tests),
including that the fragment pastes and runs inside another script and
that the check writes nothing.

**Doctrine homes.** No new numbered section, so existing cites stay
stable: the space rules went into a `Drafting table.` paragraph in
section 5 beside the other spaces; the desk-order line into section
5's Folders paragraph (with the field block and History described
there too); the wizard rule and the commandeered-goal line into section
7 after the verb table; the append rule, the page/folder distinction
and the check into section 15.

**The suite's synthetic versions.** `tests/test_office.py` used the
literals 0.3.0, 0.4.0 and 0.2.5 as "a later install". Bumping VERSION
to 0.3.0 made those the current release and broke nine upgrade tests,
so they are now `NEXT`, `AFTER` and `PATCH`, computed from VERSION
(`later(minor, patch)`). Session 2's 0.3.1 and every later bump will
pass through cleanly. `fake_install` also makes a unique directory per
call now, because my new upgrade test builds three installs at the same
version. Look at the diff of that file: 28 lines changed mechanically,
and I spot-checked them.

**`run_migrations` got a comment, not code.** I checked git's pathspec
behaviour before deciding: `git status --porcelain -- 'drafting-table/blueprints/*/close.md'`
expands the glob, and a listed path that does not exist yet matches
nothing and refuses nothing. The list flows through `helper spaces ...
filed` unchanged, so upgrade's reading of it needed only a test
(`test_a_part_filed_space_refuses_writes_to_its_filed_list_only`: a
migration appending to `rulings.md` or to a `close.md` under the glob
is refused and rolled back; one rewriting `agenda.md` lands).

## Where I departed from the blueprint (and the brief's "as written")

- **ASCII.** The suite pins office-bound text to ASCII, so in the
  templates the blueprint's `→` is `->`, `—` is ` - `, `…` is `...`,
  and the evidence occurrence head `## 13 · occurrence — 2026-10-03`
  is `## 13 - occurrence - 2026-10-03` (derived: `## N - derived -
  DATE`). Session 4's reader must take that spelling. I dropped
  `(§2.3)` from the blueprint template's Ordering paragraph and "The
  paragraph MASTER.md §2 kept per arc:" from the close report's
  Residual, both blueprint-internal cites that mean nothing on an
  office page and carry `§`. Everything else in those two templates is
  the blueprint's text.
- **Field block position.** The blueprint's sentence says "below the
  title and the template's existing sentence"; its illustration and the
  brief put the block directly under the title. I followed the
  illustration.
- **Illustrative records stay fenced.** A skeleton is copied into a
  real office, so every example record sits in a fenced block and no
  live line on a skeleton states a fact (the agenda's Disposed list is
  empty, for instance).
- **The `templates/` line in README.md** got the drafting-table files
  and the note that the renovation copies them in.

## The exact doctrine lines landed

Section 5, the table row:

> | drafting-table/ | blueprints for work too big for one folder, and the ledgers around them: rulings, evidence, watches, riders, the agenda | renovation | no | a list |

Section 5, appended to the Folders paragraph:

> Under its title a folder carries its facts as field lines, written by the office command and never by hand: its status and the date it was queued, and, as the verbs that mint them arrive, its number, class, size, lane, source, blueprint and gates. A field the command cannot fill is left out rather than left blank. Its History section is one dated line per event, appended and never rewritten. The order of the desk is computed from what the folders say, and nobody writes one.

Section 5, new paragraph after Letterhead:

> Drafting table. Blueprints for work too big for one folder, one arc each, with the ledgers a planning sitting rules in: the rulings ledger, the evidence ledger, the watches register and its log, the riders page, the agenda, and the desk moves a sitting decided. The space is part live, part filed: the ledgers, the watch log and the close reports are filed paper, and the floor plan lists them. Its templates are the install's; a renovation copies them in when the space arrives. A fact lands once, on the folder, blueprint or ledger record it belongs to, and everything else cites it by id; the same fact restated in two records is a defect. A ruling on the ledger is reopened only by a sitting that names it, and a reopening is a new ruling that supersedes; the earlier record is never touched. The evidence ledger admits only what live traffic earned: a record names a session id or a notepad page, or it is refused. An eye-watch no sitting has looked at is reported, never silently aged. Closed blueprints stay on the table; nothing is condensed.

Section 7, after the verb table:

> A verb is a wizard on a terminal. It walks the occupant through whatever it was not given, and it explains an argument it does not understand rather than refusing it. Every question a verb asks has a flag twin, so the same invocation can be typed in full without being asked anything. With piped input a verb never asks: it refuses what it was not given and names the flag.

> A session whose goal the occupant overrides midway keeps the override words on its notepad page, and the new ask becomes a new folder or blueprint, never an exception counted against the old one.

Section 15, the first paragraph now names the drafting table's ledgers
and close reports as filed paper and says the floor plan lists what is
filed (a whole space or a list of paths). Then, verbatim from blueprint
section 0 rule 1:

> Appending is not rewriting: a filed page grows at its end, and the bytes already filed never change.

followed by:

> A correction, an amendment or a later state is a new record that points back, and the reader renders the current state. That is how the notepad already works, and the drafting table's ledgers work the same way. A filed folder in the filing cabinet keeps the older rule: it moves whole, and only the office command adds lines inside its sections.

> A session that writes a filed page proves it in its validation: for a page that existed when the request was packed, the first bytes of the page as staged, as many as the shipped copy had, hash to what the request stamped for it; a page the session created has no base. The check is `doctrine/checks/filed-append-only.sh`, which rides with the doctrine into every office session, and the worker fills in its paths, sizes and hashes from its own request. A script that appends to filed paper makes the same check before it commits.

Against blueprint section 7's list: section 15 (landed verbatim), one
home per fact (section 5, drafting-table paragraph), reopening only by
a naming sitting and supersession (same), evidence admission (same),
desk computes its order (section 5, Folders), eye-watch reported never
aged (drafting-table paragraph), commandeered sitting re-asks (section
7), the wizard ruling (section 7). The three read-side lines for
sections 10 and 13 are not here, as the brief says.

## Things worth a look at review

- `doctrine/OFFICE.md` section 5's Folders paragraph now describes the
  field block before any verb but `office open` writes one. I kept it
  because the template ships now and an occupant reading a fresh
  folder should find the lines explained; if you would rather the
  doctrine wait for session 4, cut that sentence.
- The `templates/folder.md` prose says "the office command and never
  by hand". `office sessions` already writes into the folder, and
  session 4's verbs will write the fields; a hand edit to `status:`
  is what session 4's status/History check will catch.
- The suite's `test_the_0_2_0_verbs_still_serve_a_folder_without_the_field_block`
  rebuilds a 0.2.0-shaped folder from the new template by cutting the
  block and the two new sections, then runs desk, sessions, close and
  reopen on it. That is my pin for constraint 3.
- `.gitignore` was not in the request, and the suite's own-text check
  reads it; I ran the suite with a local stand-in. It is not in this
  response.

## Proposals

**What.** When session 2 adds the `lands` / `attended` / `trigger`
keys, give `office status` (or the suite) a check that every path the
catalog lists under `filed` for a space is either a page name or a
glob, and that no `hung` path is also `filed` (a hung filed page would
ship into every session and be append-only at once; not wrong, but
worth a deliberate line).
**Why.** The catalog now has two list-valued props with different
semantics and nothing cross-checks them.
**Scope hints.** `share/spaces.toml`, `tests/test_office.py`; after
session 2.

**What.** Session 3's reader should take the ASCII record heads this
session fixed (`## N - occurrence - DATE`, `## N - derived - DATE`,
`## WN - Title`, `### rider N - title`, `-> ` for every pointer arrow)
as the parse contract, and the templates as the fixtures.
**Why.** The blueprint spells them with `·`, `—` and `→`, and the suite
refuses non-ASCII in office-bound text; the templates are now the one
spelling.
**Scope hints.** session 3 and 4; `templates/drafting-table-*.md`.

**What.** For session 4, `office open --filed --sid SID` (a folder born
done) and `office moves` should render the template with the same
`render-template` call `office open` uses now, passing every field they
can fill, so the "left out rather than left blank" rule stays in one
place: the template's placeholders are exactly the fields written.
**Why.** I put `status` and `queued` in as placeholders; adding
`{{number}}` etc. later means either every caller fills them or the
renderer learns to drop a line whose value is empty. The second is a
small change to `render_template` (drop a `- key: {{x}}` line when x is
unset) and would let the template show the whole block.
**Scope hints.** `lib/office_helper.py` `render_template`,
`templates/folder.md`, session 4.
