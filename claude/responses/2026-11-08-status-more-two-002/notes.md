# Notes: 2026-11-08-status-more-two-002, the rest of what the read side was missing (office-src 0.54.0)

Six of the seven items shipped whole, each with its tests: 1 (the asks'
three lines), 2 (the sandbox line in a container), 3 (the listed offices),
4 (the map's paused folders), 5 (a host ride's size) and 6 (a profile's
capability words). Item 7, the tables, is left at the seam the brief
named, and is a proposal below. Every path is inside the forecast, so
there are no departures to admit. There was no context compaction this
session.

The tree I was handed is 0.53.0, the whole tree. Every anchor the brief
named is there, moved as warned: cmd_status 1422, status_lines 2602,
sandbox_status_line 2757, toolchain_lines 2697, next_move 1765,
delivery_move 1710, office_ask asks_out 185 and status_line 217, the
digest's window 82 and render 465, office_map Reading 86 (state 137),
project_row 252, next_lines 475, pack_host_rides 2938,
office_host._RIDE_SCRATCH_SCRIPT 1181, office_helper listed_offices 4375,
offices_fact 3532, named_in_line 3479, catalog_names 3464, VERB_KEYS 555.
The survey's class lines are bin/office 436-462. None is gone. (Numbers
are the 0.53.0 tree's, before this change.)

## Decisions

Numbered so you can ratify or correct each by number.

1. **The ask's Next row.** `office ask --learned`, with the oldest ask's
   name, where it was asked and since when, and how many more are out
   (office_bale ask_move). It sits after delivery_move and before the drop
   rule, as the brief pins. The walk-in's desk call now takes
   `--machine-file` (the asks live in machine.toml's out tray, which the
   desk did not know), and the home screen reads the same list
   (office_bale asks_waiting). On the home screen the Next item for an ask
   would have been a second item with the same key as the ask's own, so
   with_asks puts the ask's own item first, marked as the Next one, and
   it is offered once.
2. **The digest's asks line** is the last line of Since the last sitting,
   not a section of its own: `- asks: N filed or ended: NAME filed (PAGE;
   facts in handbook/P.md; its questions and answers on the page); NAME
   ended with nothing filed (PAGE)`, oldest first, or `- asks: none filed
   or ended`. It reads `git log --grep '^office ask:' BASE..HEAD` with the
   window's own base and keeps only commits whose subject starts with the
   prefix (the grep also matches a later line of a message). The window
   still skips an ask's page, by 0.48.0's decision 11.
3. **The orphan's removal line is `rm -- RECORD [OPENER]`**, quoted paths,
   in a line of its own after the asks line. There is no office verb that
   removes a record without a tray (`--learned none` needs the tray out),
   and an orphan was neither filed nor ended, so nothing of it is in the
   office to lose. Only a record of this office is named; another
   office's record in the shared tray is that office's.
4. **The container's sandbox line is the hosted line's words with `this
   machine` for the host**, read with the same sandbox_argv through
   ohost.sandbox_state (a local process; no host). It is said only when
   the survey's Machine class reads `container` exactly (office_bale
   machine_class reads the page office survey wrote; status never
   surveys). No survey, WSL or a host: nothing, as before.
5. **The listed offices: no unlisting line exists, so status says so.**
   The doctrine's offices paragraph (office_helper, above machine_offices)
   says the office adds to the list and never removes; the occupant edits
   the file. I read the brief's "with the line that unlists it, or saying
   there is none" as exactly that case: `  ROOT: listed, but it is no
   longer an office (no floor-plan/manifest.toml); no office verb unlists
   it: take "ROOT" out of offices in FILE`. If you want a verb for it,
   that changes the doctrine, so it is a proposal below rather than
   something I built. The heading line is printed on every status
   (`offices:    N listed in FILE: NAME (ROOT, this one); ...`, or none
   listed); an office not in the list says `this one is not in the list`.
   I did not offer `office default PATH` as the way to list it, since that
   also changes the machine's default office.
6. **A host ride's size is read before the pack, not beside the copy.**
   This is a deviation from the brief's mechanism, flagged here. The
   brief said "a du beside the copy, in the same connection", but the pack
   round's output comes back only when the whole connection ends, so a du
   there could be said only after the copy had already run. The ride
   facts script, which start already runs in its earlier round on the
   host (the one with status, the paths and the branch), now prints a
   fifth column: du -sk's KiB for a directory outside git, empty for every
   other kind. start logs the size from that read, before anything is
   copied, and makes no new connection; the test counts it. read_ride_facts
   still reads four columns, so nothing older breaks.
7. **The bound is 256 MiB** (office_bale.RIDE_LARGE_KB). That is a guess
   at where a copy-then-tar on a host stops taking seconds. Above it the
   line says LARGE and names `--leave-out 'host:PATH'` (quoted); nothing
   is refused. A size du could not give is said as unknown.
8. **The map's paused folders.** The state cell starts with `paused`, and
   when the folder records a session, `SID not read` (the last one it
   records). The office cannot tell whether that session is still out
   without reading bale, which is what paused forbids, so it names the
   session rather than say "in flight". The desk state follows as before
   (`paused; SID not read; open`). The record page (`office map N`) says
   it in full, with the unpause line.
9. **Words on verbs, not kinds.** The brief said "a verb or kind may
   carry words". verbs.toml has no table for a kind, and a kind's own name
   is already read on its own (decision 5 of 0.53.0), so only verbs carry
   `words`. projects carries `a project on a host`, `projects on a host`,
   `a hosted project` and `hosted projects` (README and the doctrine call
   it a project on a host, or a hosted project); start `the out trip` and
   land `the return trip` (RELEASES' names for 0.15.0 and 0.16.0). A
   phrase match is said with its phrase and its verb: `profile.md line N
   says a project on a host is not built; office-src V builds it (office
   projects, share/verbs.toml): ...`, since `says projects is not built`
   reads wrong. The catalog check takes `words` as optional (it is not in
   VERB_KEYS; OPTIONAL_VERB_KEYS names it), checks its shape and refuses a
   phrase given to two verbs. At one place the longer match now wins,
   where 0.53.0 compared the names' lengths; every 0.53.0 test still
   passes.
10. **Item 7 left at the seam.** The In flight lines and the Projects
    block are pinned line by line across many modules (test_read_side,
    test_home_screen, test_home_screen_offers, test_meetings_view and
    more), so a table there is a rewrite of their pins. Doing that well
    is a session's worth of work on its own, and it would have cut into
    the time I had for verifying the other six. The brief named it the
    half to leave.

## The suite

- Baseline, the unchanged 0.53.0 tree: the fast tier with test_status_more
  and test_read_side, 426 tests, OK, 55 s.
- New: tests/test_status_more_two.py, 31 tests (the Next row's words and
  rank, the home screen's one item, the walk-in's Next line in an office
  with an ask sent, the orphan's line and its rm run for real, another
  office's record left alone, the digest's line with a filed and an ended
  ask, the machine's class, the container's sandbox line and the step it
  names, WSL and no survey saying nothing, the listed offices with this one
  marked, a gone root and an unreadable list, the map's paused row and
  record, the size lines and words, the facts' fifth column and the
  script run here, start's size line with the connection counted, the
  words rule, its stale line, the catalog's optional key and its two
  refusals, the install's words, and status's line for a capability).
  Touched: none of the existing tests needed a change.
- The whole suite on the finished tree: 1526 tests (0.53.0's 1495 and
  the 31 new), OK, 691 s on two CPUs (tests/run.sh, side by side).
- validation.sh runs the fast tier with test_status_more_two,
  test_status_more and test_read_side, and behind `--slow` the whole of
  the eleven modules this change reaches. In a staged copy (0.53.0,
  files/ overlaid, apply.sh run) every check passed: 1m12s without
  `--slow`, 3m21s with it. On the unmodified tree every change-dependent
  check fails, the tests among them (the new module is not there); the
  five that pass there (bash -n, the catalog reading as TOML, the
  doctrine's core bytes and banner, bin/office's exec bit) guard what
  must not move. Nothing was written in the staged tree but the script's
  own logs. No test hard-codes a day or a VERSION, and nothing is named
  `m10_`; the new module's docstring names its release, as 0.53.0's does,
  and the check reads only the code's strings. tests/fast-tier.toml is
  unchanged: no verb was added.

## Walkthrough

### What changed

- The walk-in's Next line and the home screen's first item name an office
  ask that is out, after a waiting job or delivery and before a drop
  (office_bale ask_move, asks_waiting; office_home with_asks).
- The digest's Since the last sitting section says the asks filed or ended
  in its window, each with its page (office_digest asks_filed).
- `office status` names an ask's record whose tray is gone, with the `rm`
  line that removes it (office_ask orphans, orphan_line).
- `office status` gives a project on this machine the sandbox line when the
  survey says this machine is a container (office_bale machine_class).
- `office status` names the offices machine.toml lists, this one marked,
  and a listed root that is no longer an office (office_helper
  offices_status_lines).
- `office map` marks a paused project's folders (office_map paused_words).
- `office start` says a host ride's size before it is copied, and names
  `--leave-out` when it is large (office_host's facts script, office_bale
  ride_size_lines).
- share/verbs.toml may give a verb `words`, which the profile rule reads
  (office_helper catalog_words, match_in_line).

### Why

The read side had six places where the office knew something and did not
say it: an ask left out fell below the desk; a sitting saw nothing of what
asks brought in; a tray deleted by hand left a record nothing removed; a
container got no sandbox line for its own projects; a listed office that
went away was said only under OFFICE_DEBUG; a paused project's folders
looked live; a big ride outside git was copied with no word. And a profile
line that names a capability rather than a verb could never be caught.

### How to explain each piece

- An ask out waits on you as a delivery does, so it ranks with them.
- The digest reads the asks from the commits office ask makes, the same
  way it reads sessions from bale's commits.
- In a container, a project here is where bale's sandbox may not run, so
  it gets the same line a hosted one does.
- The office only ever adds to the offices list; status tells you what to
  take out of it.
- A paused project is read for nothing, so the map names the session it
  cannot read instead of guessing whether it is out.
- The size is read in the round start already makes, before the copy.

### Questions a reviewer will ask

- *Does a hosted status or start make another connection?* No. Status
  makes no new host round (the container line runs here), and start's
  size rides the facts read; the start test counts the one connection that
  carries `du -sk`.
- *Why not a verb that unlists an office?* Decision 5: the doctrine says
  the office never removes from that list.
- *Why name the last recorded session of a paused folder, when it may have
  landed?* Decision 8: nothing else can be said without reading bale, and
  `not read` says exactly that.
- *Is the 256 MiB bound right?* Decision 7: a guess. Tell me where a copy
  on your host starts to drag.

### A hand test

1. `office ask --words "Does it cache?" --project alpha`, then walk in
   (`office | tail -1`): `Next: office ask --learned  (ask-... (alpha) has
   been out since ...`.
2. `rm -rf ~/out-tray/ask-...` (the tray only), then `office status`: an
   `asks:` line naming the record, ending `rm -- ... removes it`. Run that
   rm; status says nothing of it after.
3. `office digest` after filing an ask: its Since the last sitting section
   ends with `- asks: 1 filed or ended: ...`.
4. On the work office's container (survey class `container`), `office
   status` on a project here: its `sandbox:` line, as the hosted one reads.
5. List a directory that is not an office in machine.toml's `offices`:
   `office status` names it with the edit.
6. `office projects set alpha --paused`, then `office map`: alpha's folders
   say `paused`.
7. On a hosted project with a `--ride host:~/some-dir` outside git, `office
   start ...`: the size line on the screen before the pack.
8. Add `- a project on a host is not built yet` to the profile: `office
   status` names it.

## Delivery

- to: the occupant (office-src delivers to no audience; these are the
  workbench's words)
- branch: status-more-two

### Commit

Say the rest of what the read side was missing: office-src 0.54.0

The walk-in's Next line names an office ask that is out, after a waiting
job or delivery and before a drop, and the home screen offers it once as
its first item. The digest lists the asks filed or ended since the last
sitting, with their pages. office status names an ask record whose tray is
gone with the rm line that removes it, the offices machine.toml lists (and
a listed root that is no longer an office, with the edit that unlists it),
and in a container the sandbox line for a project on this machine. The map
marks a paused project's folders. office start says a host ride's size
before it is copied there, and names --leave-out when it is large. A verb
in share/verbs.toml may carry words, the phrases a profile line may name
its capability by.

### Review

Say the rest of what the read side was missing: office-src 0.54.0

Look at office_bale ask_move and its place in next_move, office_home
with_asks, office_digest asks_filed, office_ask orphans, office_bale
machine_class and the container branch of status_lines, office_helper
offices_status_lines and match_in_line, office_map paused_words, and the
facts script's fifth column with ride_size_lines (notes, decisions 1, 5,
6 and 9). To try it by hand, follow the walkthrough's hand test.
Deliberately untouched: the walk-in's In flight lines and the home screen's
Projects block, proposed in the notes.

## Structure

- title: Say the rest of what the read side was missing
- size: medium
- goal: Say the rest of what the read side has been missing: the asks, a container's sandbox, the listed offices, paused folders on the map, a host ride's size, a profile's capability words: office-src 0.54.0

## Handbook

### office-src

- the walk-in's Next line names an office ask out after delivery_move and before a drop (office_bale.ask_move, 0.54.0); the desk call reads the asks through --machine-file (office_bale.asks_waiting), and the home screen's ask item takes the Next item's place (office_home.with_asks)
- the digest's Since the last sitting ends with the asks filed or ended in its window, from `office ask:` commits (office_digest.asks_filed)
- office status names an ask's record whose tray is gone, with `rm -- RECORD [OPENER]` (office_ask.orphans, orphan_line, in ask:out-lines --status)
- in a container (the survey's Machine class, office_bale.machine_class), office status gives a project on this machine the hosted sandbox line, `this machine` for the host
- office status names machine.toml's offices, this one marked, and each listed root that is no longer an office with the edit that unlists it (office_helper.offices_status_lines, helper offices-status); no verb removes one
- a paused project's folder says `paused; SID not read` first in the map's state cell (office_map.paused_words)
- the ride facts script prints a fifth column, du -sk's KiB for a directory outside git; start logs ride_size_lines from it before the pack, LARGE over office_bale.RIDE_LARGE_KB (256 MiB) with --leave-out named
- share/verbs.toml's optional `words` list is read by office_helper.match_in_line beside a verb's name; projects, start and land carry it; a phrase names one verb
- tests/test_status_more_two.py holds 0.54.0's tests

#### Front sheet

office-src 0.54.0 says the rest of what the read side was missing. The
walk-in's Next line names an office ask that is out, and the digest the
asks filed since the last sitting. office status names an ask's record left
without its tray, the offices this machine lists, and in a container the
sandbox line for a project here. The map marks a paused project's folders,
and office start says a host ride's size before it is copied. A verb in
share/verbs.toml may carry words a profile line names it by. Additive: no
migration.

## Proposals

- **What:** item 7, the walk-in's In flight lines and the home screen's
  Projects block in the map's project-first table shape. **Why:** left at
  the seam (decision 10). in_flight's lines come through unread_line for
  an unreadable project, so a table row can take that text; the map's
  office_map.table is the shape to reuse. **Scope hints:** office_bale
  render_in_flight and desk_lines' In flight block, office_home
  render_page's `Projects:` block, and the pins in test_read_side,
  test_home_screen, test_home_screen_offers and test_meetings_view, which
  move whole.
- **What:** a verb that takes a root out of machine.toml's offices
  (`office default --unlist ROOT`, say). **Why:** decision 5: today status
  can only name the edit, because the doctrine says the office never
  removes from the list. Worth it only if you want the office to own that
  list both ways. **Scope hints:** office_helper add_machine_office's
  writer as a model; the doctrine's offices paragraph.
- **What:** the asks' Next row and orphan line on the map and in `office
  desk`. **Why:** the map's Next rows (office_map next_lines) and the desk
  read the same groups but name nothing of the asks, which live outside
  any folder. **Scope hints:** office_map next_lines; render_desk would
  need the machine file, as the walk-in's desk call now has it.
- **What:** a stream of the host's own words during a long host ride's
  copy. **Why:** decision 6: the pack round is captured whole, so even
  with the size said up front, the screen is silent until the copy and
  pack end. **Scope hints:** office_host run_streamed, which the probe
  already uses, for the scratch rides alone.
