# Releases

A release is breaking exactly when it ships a migration (migrations/).
Each breaking release's migration carries the plain-language summary
that office upgrade writes into the office's commit.

## 0.52.0

Additive: no migration, nothing to do in any office. The fifteenth serial
session of the plan begun on 2026-10-27: 0.44.0's first proposal (item 4
of its brief, left at its seam), 0.51.0's two proposals, and 0.49.0's
note on bundle plumbing. A folder records a handoff as a new History verb,
`handed-off`; a merge or undo job's page may carry a `bailed` line. Both
read as absent on an older folder.

A bailout's fresh session goes out from the office. `office start N
--handoff [RESPONSE]` runs `bale handoff` where the bailed session ran
(through the project's shell on a host, the bailout carried there first
and removed in the handoff's own connection), stdin closed, and reads which session
it opened from bale status's open set before and after, exactly one more,
held to the report's `session id` and `tarball` rows and to
request-SID.tar.gz in status's outbox. RESPONSE is the bailout, a path or
its name here or in the downloads; none, the response of the folder's
newest session there. Everything after is a pack's: the tray (the office's
context beside the request, the doctrine, what rides), the folder's record
(`- SID: from the handoff of BAILOUT` in Sessions and a `handed-off`
History line, one commit), and the opener on the clipboard last. bale
handoff prints no opener and keeps no constraint, so the office composes
the opener in the shape of bale's, says so in its last line and on the
screen, and names handoff.md first, the folder's brief where it rides and
the original pack's constraint. Refused by name before anything runs: a
response that is not a bailout or carries no handoff.md, one whose session
the folder does not record, is still open or was a sitting, a folder in
the filing cabinet, and `--in-office`, `--merge`, `--undo-bale`,
`--bundle`, `new`, `--drop`, `--goal`, `--brief`, `--write`, `--include`,
`--slug`, `--read-only`, `--sort`, `--prep`, `--planner`, `--words` and
`--carry` beside it; `--branch` checks out first. bale's refusals (a
detached HEAD, the missing record, the gate) are said in bale's words with
the office line that answers each, and nothing is written in the office:
no survey runs before a handoff. A bailout's Next line, and `bale handoff`
in office words, is now `office start N --handoff RESPONSE (bale handoff
runs in REPO; ...)`; the README, the doctrine and the sitting brief no
longer say there is no office line for it. [surfaces.handoff] declares the
verb, its contract (cmd_handoff in bin/bale, bale 0.4.56, read by the
probes handoff-ground and handoff-tail) and its two rows; share/verbs.toml
and the doctrine's session kinds gain `handoff`.

A job's session line follows its session. When office withdraw closes the
session a merge or undo job names, or its bailout lands, the page's line is
cleared, said and committed, and the job is offered again (`office start N
--merge`, or `--undo-bale`); a bailout is kept as the page's `bailed` line,
and `office start N --handoff` puts the fresh session in its place, so
land closes the job for it. The merge line gains the undo line's `office
start N --merge sends another in its place, if it was withdrawn`.

The undo job's close checks its work. Before office land (or deliver)
closes an undo job, each of its paths is read on the workbench and held to
bale's change as the materials record it: the lines bale's commit put
there that the file did not hold before, and those it took away (before/
against bale/; blank lines, and lines both sides hold, never decide). A
path that still holds bale's change (every line bale put still there and
none it took back) keeps the job open, said with the path and the line,
nothing removed: the session line cleared, the session kept as the page's
`earlier` line, and land's last line `office start N --undo-bale`.

0.49.0's note. resolve_hosted_bundle and bundle_lands_read's bare-name
branch are gone from bin/office: since 0.49.0 every bundle start takes is a
file, so neither ran. START_BUNDLE_FOUND stays: it feeds --bundle-found.

Tests: tests/test_handoff.py (the surface, the line, the opener, the
whole loop through the office here and on a host, the refusals, the job
line as units and through the office, the close's rule and its kept-open
job, and the record); tests/fakes/land_bale.py learned a bailout apply and
bale handoff, built from bale's code (no real bailout was there to
capture); tests/test_land.py's response_tarball writes a bailout's
handoff.md; tests/test_from_the_artifact.py pins the new line.

## 0.51.0

Additive: no migration, nothing to do in any office. The fourteenth serial
session of the plan begun on 2026-10-27: 0.40.0's first proposal, as
0.42.0 wrote it up, and 0.47.0's second and third. A folder's merge/ page
is read as before (a `- changed:` line may now say `not copied`); an undo
job, its page and the `undone` History line are new.

No ordinary refusal of a delivery sends you into the clone. When one of
bale's own commits cannot be taken out of a delivery (the workbench's
later work touches the same lines, and the commit did more there than add
lines), `office deliver` pushes nothing, leaves the clone clean, and
writes an undo job into the folder, under undo/: every path the take-out
could not undo (all of them; before, only the first was named), each
before bale's commit, as the commit left it and as the workbench holds it
(before/, bale/, workbench/), bale.diff, the commit's own change to them,
and undo.md, the job's page, committed in the office. Its last line is
`office start N --undo-bale sends the session that takes bale's own change
out of the workbench`; the `by hand on the workbench branch` remedy is
gone from the code, the README and the doctrine.

`office start N --undo-bale` sends that session on the job's project, the
merge session's model: the folder alone (anything else refused, and
`--merge` beside it), the job's paths as the forecast, the goal `Take
bale's own commit SHA7 (SUBJECT) out of the workbench of folder N, in
PATHS`, the brief from the new templates/undo-brief.md, and the session
named on the page, committed alone. Its response ships each path whose
result differs from the workbench's, with bale's change taken out, a `##
Undo` section in its notes and no Walkthrough, Delivery or Structure.

When it lands, `office land` closes the job: a dated `undone` History line
(`bale's own commit SHA7 (SUBJECT) taken out of PATHS by SID`), the
materials removed, both committed in the office, and land's last line is
`office deliver N`. The session's landed commit is the undo; land makes no
commit of its own. Never under another session open in the clone: then
deliver closes it before it plans, and while the session is out deliver
names `office land SID`. The next delivery reads the `undone` line and
takes each of those paths as the workbench holds it when it reverts that
commit (`nothing left to undo: the undo session SID took it out of PATHS
on the workbench`), so the squash leaves without bale's change; later work
on bale's lines in another of its paths writes the job again for those,
naming the session that landed. A folder holds one job at a time, of
either kind, the second refused naming the first; several refusing
commits are met one at a time, newest first. The waiting job is offered
by key wherever a merge job is: the home screen, the Next line, the desk's
line, `office status`'s waiting lines and `office map` (`undo job
waiting: bale's own commit SHA7 conflicts with the workbench in K
file(s); office start N --undo-bale`).

0.47.0's two. A merge job's copy of the audience's other changed files is
capped at MATERIALS_CAP (200) copies, the conflicting files always copied
whole and never counted; every path is still listed on merge.md, those
past the cap marked `(changed, not copied)`, and the page and the brief
say how many were left and that `git show TIP:PATH` in the clone reads
them. An empty response lands: bale 0.4.56 makes the session commit and
the merge with plumbing and tags applied/SID with no check on the change
(the probe empty-landing), the suite's fake bale now lands `changes: []`
the same way, and a merge session whose every resolution is the
workbench's ends in the merge commit through `office land`; the merge
brief says so. make_resolved_merge's exit 13 still names no line.

Tests: tests/test_undo_bale.py (the job, the session, the whole loop
through the office's commands, a host, the offers, the cap, the empty
landing and the record); tests/test_bale_own_commits.py's refusal test
now pins the job's words and every "nothing moved" check.

## 0.50.0

Additive: no migration, nothing to do in any office. The thirteenth serial
session of the plan begun on 2026-10-27: items 3 and 9 of the friction
report of 2026-10-27, 0.39.0's first proposal and 0.42.0's third. What
you see changes for `office projects set`, `office projects`, the map and
`office start`; what is stored gains one spelling and one key, each read as
absent on an older floor plan.

A ride from the project's host. `office projects set NAME --ride
host:PATH` declares a ride on a hosted project's host, PATH as that host's
shell sees it (absolute or `~/`), stored as typed in the same `rides` list:
one spelling in the floor plan, `office projects`, the map's cell, start's
screen and `--leave-out`. It is checked where it lives, through the
project's shell in one connection: a path not there (`no such path on
HOST: PATH`) or a host that does not answer (its connect line) declares
nothing, and a `host:` ride on a project with no host is refused by name.
The listing and the map show it as stored, `rides: host:~/x (on HOST)`, and
reach no host for it. At `office start` it is checked in the round start
already makes on the host, and one gone from the host stops the start
before anything is written. It is packed there by the host's own bale,
`bale pack --context` (never a plain tar): from the repo's top with
`--include` inside a repo there, from a scratch copy there for a directory
outside git (removed in the connection that fetches its tarball), fetched
as it is for a file outside git; every pack rides one connection, and each
tarball comes back into the tray as the request does, named as the same
ride would be from here and said, `context-notes.tar.gz: rides with far
(host:~/notes/blueprints, packed on HOST)`. An office session about the
project (`--about`) rides it the same way. The in-tray's drops, the
doctrine and the office's context are still made here.

The branch on start's screen. Every project session, here or on a host,
bundle or not, says before the pack `PROJECT's clone at WHERE is on
BRANCH` (or `is on a detached HEAD`), read in the round start already makes
there: no connection is added for it.

`office start --branch NAME`. On `--on`, `new` and `--drop` sessions the
flag checks NAME out in the project's clone before the pack, through the
same step a bundle's BRANCH line runs, with the same refusals (a dirty
clone, a session open there, no such branch, several remotes) and words
(`--branch NAME names the branch, and ...`); `--in-office` refuses it as a
BRANCH line refuses there. Over a bundle whose brief names another branch,
the flag stands and is said in one line. And the checkout, whoever asks
for it, fast-forwards a local branch behind its remote-tracking ref (the
clone clean, the local tip an ancestor of the remote one), naming both
tips; one that has diverged, or is ahead, is checked out as it is and said
so. Nothing is forced, and the office still fetches nothing.

The audience URL kept. The audience line has a sixth key, `audience_url`,
for a project on a host only: written when `office projects set` (or
`add`) sets the audience, from the clone's remote as it is read through the
shell at that moment, or by `--audience-url URL` (`--no-audience-url`
clears it; `--no-audience` and `--on-this-machine` clear it too).
Review state reads from it before a hosted project's first review is
recorded; `office projects` shows it. A project on this machine keeps none.
Each hosted project with an audience gets its URL by running, once:

    office projects set NAME --audience REMOTE

Tests: tests/test_host_rides.py, one class per item, the host the fake ssh
and review state FakeGh.

## 0.49.0

Additive: no migration, nothing to do in any office. The twelfth serial
session of the plan begun on 2026-10-27: the desk made readable, four
things met at the terminal on 2026-11-05, and one proposal of 0.48.0's.
What you see changes for `office map`, for every list of folders offered
by key and the desk's folder line, for words past ASCII on every screen,
and for `office start --bundle NAME`. Nothing stored changes.

The map is two tables. `office map` prints the projects first, one row
each under a header row (its name, where it is, its audience or none,
whether it is paused, and what rides with it and what runs after it lands
in one cell, `rides: a, b; after: x; y`), then the folders, one row each
(folder N, its project, its title, its size and its state in a few words:
`in flight 3 days`, `sitting out 2 days, step 8 of 14`, `landed, not
delivered`, `delivered BRANCH`, `review #N STATE`, `open`, `ready`,
`done`). Folders are grouped by project in the floor plan's order, the
office's own last; open ones come before closed ones, newest number
first; of a project's closed folders the newest three show and the rest
fold into one line, `and N more closed: office map --all`, and `office map
--all` shows every one. On a terminal the page is cut to its width, the
titles giving way first, with `...`; piped, every cell is whole. `office
map PROJECT` is that project's rows, nothing folded; `office map N` is the
folder's whole record, as before, with the session's id and the riders.

Every list names the project. Every list of folders offered by key reads
`folder N, TITLE (PROJECT)`, `(the office)` for the office's own, `(no
lane yet)` for one whose lane is still to be asked: start's jobs on the
desk, `Folders in desk/`, the planner's folder, and probe's folders with a
session open. The desk's line says it after the folder's name, `folder N
NAME (PROJECT)  next: ...`.

Your words as you wrote them. A title or words with a curly quote or an
accent show as you typed them on the map, in the pickers, on the desk, the
home screen, the walk-in, status, the bundle offer and a sitting's
standing, where `\u201c` showed before. The pages keep their ASCII:
folder.md, the notepad and the handbook are written as they always were.

The bundle by its name. `office start --bundle NAME` works out the bundle
before it asks anything or writes anything: a path is taken as before;
else NAME and NAME.bale-bundle are tried here, then in your downloads
(machine.toml's downloads), the newest browser copy taken. A name found
nowhere is refused by name, `no NAME.bale-bundle in your downloads (DIRS)
or here; save it there first, or office withdraw --bundle NAME takes it out
of the offer`, instead of going on to "Jobs on the desk". The stem is the
one spelling every line says (`office start --bundle STEM`, as withdraw's
does); a word ending `.bale-bundle` still needs no flag.

Tests: tests/test_desk_readability.py, one class per item. The map's own
tests in tests/test_folders_and_projects.py moved with the shape, and the
bare-name and probe-picker tests in test_land.py and
test_home_screen_offers.py with the bundle's and the pickers'. The suite
was swept for tests that name a session the fake bale mints by a literal
day: one, in tests/test_standing.py, now dates its sittings from the one
minted. tests/test_ask.py's record test, which pinned VERSION to 0.48.0, now
holds it at 0.48.0 or later.

## 0.48.0

Additive: no migration, nothing to do in any office. The eleventh serial
session of the plan begun on 2026-10-27: office ask, the quick path, item
2 of the M10 report, and the editor's opt-out 0.33.0 proposed. What you
see changes for `office ask`, which is new; for the home screen, the
walk-in and `office status` while an ask is out; for `office tray`; and
for every question that takes several lines when machine.toml names an
editor. Everything else is as it was.

The quick path. A question worth a chat and not a session, an urgent one
above all, goes out through `office ask` (the home screen's `i` key): your
words, as `office start new` takes a job's, and the project by key only
when your words name none of the office's projects (`--words`, `--project
NAME` and `--in-office` are the twins; words after the verb are the
question too). The office writes one out tray, `~/out-tray/ask-DATE-SLUG`:
a brief from templates/ask-brief.md (your words verbatim, the project, the
rule that office context informs the answer and never lands in a project,
the voice page's words when the project has an audience, the letterhead
check line, and what to leave at the end), and beside it the project's
handbook chapter, the letterhead's voice page and forbidden list, the
profile and the doctrine. No project tree rides. On a terminal the tray
opens and the opener goes on the clipboard, as start's do, and the
opener's copy is kept beside the tray. No bale verb runs, no session id is
minted, and nothing is written in the office.

Filing what it learned. The chat ends with a LEARNED block (`--- LEARNED
BEGIN ask-DATE-SLUG ---` to `--- LEARNED END ---`: `## Answer`, then, when
there is something in them, `## Handbook` and `## Questions and answers`
in the doctrine's own shapes). `office ask --learned` files it from the
clipboard on a terminal, or from FILE or stdin (`-`); bare `office ask`
with such a block on the clipboard, for an ask that is out, files it
without asking, said in one line. The office writes the ask as a notepad
page, `notepad/DATE-ask-SLUG.md` (your words, then the answer) and commits
it with the facts, each at the end of its project's chapter as `- DATE:
fact (ask-DATE-SLUG)` through office land's own filing; then it appends
the questions and answers to the same page and commits that, each commit
passing the notepad's append check; then the tray, the opener's copy and
the ask's record beside them go. A block that does not read (no Answer, a
section an ask has no business with, a project the office does not scope,
a front sheet, a line off its shape) or that names no ask out from this
office is refused by name, and nothing is written. `office ask --learned
none ASK` ends an ask with its page alone. While an ask is out, the
walk-in lists it under `Asks out`, `office status` says it in one `asks:`
line, and the home screen offers a key that files its block (`File what
ask-... learned`), naming `office tray ask-...`, which opens the tray again
and prints its opener; bare `office tray` offers it when it is the newest.
A fact the chat writes with the ask's name or slug behind it is filed
bare, said, as a session's dressed facts are. The window since the last
sitting (`office digest`) leaves an ask's page out.

The editor's opt-out. machine.toml's `editor` decides where an answer of
several lines is written: `editor = ""` keeps every answer at the prompt
whatever `VISUAL` or `EDITOR` say, and `editor = "CMD"` takes it in CMD
over both. With no key, nothing changes. The review's `?` and the line
that opens the editor say so.

Tests: tests/test_ask.py, one class per item; the fast tier's entry point
for `office ask`. tests/test_folders_and_projects.py's bundle-screen test
reads the session's day from the clock rather than from 2026-11-04.

## 0.47.0

Additive: no migration, nothing to do in any office. The tenth serial
session of the plan begun on 2026-10-27: deliver fixes, three things met
delivering and merging on 2026-11-04, and one proposal of 0.46.0's. What
you see changes for a merge job's materials and its brief, for a
delivery.md whose Review has a title and no body, and for deliver's
question when a folder's lane names no project. Everything else is as it
was.

The audience's side whole. When bringing the audience into the workbench
conflicts, `merge/audience/` now holds the audience's copy of every file
it changed since the two sides parted, not only the conflicting ones, so
the merge session resolving one file can see what the audience did in the
files beside it. `parted/` and `workbench/` stay the conflicting files'.
The job's page lists the conflicting files on its `- file:` lines as
before and, under them, every other file the audience changed on a
`- changed: PATH` line, ` (added)` or ` (deleted)` after the path when it
was (a deleted file has no copy); the merge brief names them too. The
merge commit office land makes is unchanged: the session ships the
conflicting files it resolves, and git's merge carries the rest.

The merge brief's sentence. The brief said to ship every file in the
list, and land takes a file left out as the workbench's, so a conflicting
file whose right resolution is the workbench's version went out as a
change that changes nothing, which bale refuses. It now says: ship every
file whose resolution differs from the workbench's; a file you leave out
keeps the workbench's version, and that is right when the workbench's
version is the resolution (bale admits no file shipped unchanged).

A Review with a title and no body refuses. office deliver refuses the
delivery before anything is made, naming the page and the title's line:
`desk/NAME/delivery.md:LINE: the Review has a title and no body; the body
is what the review's readers see, so write it under the title (a blank
line between)`. `office letterhead check --delivery FILE` says the same
and exits 1, and land's review says it right after it files the page. A
filled pull-request template's own `## ` headings in the Review are still
its words. A build session that keeps such a heading at its own level in
notes.md ends the Delivery section there, so the page land files has a
title and nothing else; templates/delivery.md now says to write them one
level down there, as every heading is.

deliver's question. On a terminal, a folder whose lane names no project
is offered only the projects with an audience, each with its audience
named (`[1] api (audience origin)`); with none, deliver says so and names
`office projects set NAME --audience REMOTE`.

Tests: tests/test_deliver_fixes.py, one class per item;
tests/test_deliver_merges.py's brief test reads the new words.

## 0.46.0

Additive: no migration, nothing to do in any office. The ninth serial
session of the plan begun on 2026-10-27: folders and projects, one map of
both, a folder's fields edited by one verb, and a CLI you can read. What
you see changes for `office map`, `office folder` and `office tray`,
which are new; for a start, deliver or probe that asks which project a
folder is on; for bare `office start` with more than nine bundles waiting
and for start's screen on a terminal; for `office projects set` given a
flag on a terminal; for a bundle opened on a paused project; and on a
home screen with more than nine things waiting. Everything else is as it
was.

One map. `office map` is every project the office scopes on one page:
its facts on one line (here or on its host, its audience line, paused),
what rides with it and what runs after it lands, one line each, then
every folder whose lane names it, on the desk and in the filing cabinet,
newest number first, `folder N  TITLE  (SIZE)  STATE`, the state in the
desk's words (in flight: SID, out since DAY; landed SID on DAY, not
delivered; delivered BRANCH on DAY; review #N STATE; merge job waiting;
ready; parked; closed, done; a sitting's step N of M), its riders by
number under it; then the office, with the folders whose lane names no
project. `office map alpha` is one project's section; `office map 12` is
one folder's whole record: its fields, its sessions as `office sessions`
shows them, its riders, deliveries, reviews and standing, the lines that
act on it next (`office land SID`, `office tray SID`, `office deliver
12`, `office start 12`), and last the lines that change its fields. The
map reads what the desk reads, once, and writes nothing
(lib/office_map.py). The home screen's `a` key runs it.

A folder's fields, edited by one verb. `office folder N` is the one
writer of a folder's fields after `office open`: `--lane PROJECT` (a
project the office scopes) or `--in-office`, `--title`, `--size`,
`--goal`, `--source` and `--class` each replace their line, or write it
where the field block puts it, take the field off the provisional line,
and add one History line per field, `- DATE re-scoped: FIELD from OLD to
NEW (office folder)`; the folder is committed alone, on the desk or in
the filing cabinet. Alone it prints the fields and the line that changes
each. `--in-office` writes the lane `the office`, two words that can
never be a project's name: start, deliver and probe read it as the
office's own work and stop asking. An open session in the office whose
forecast holds the folder keeps the write out (the one-writer rule); a
session out on another project than the new lane names is said, never
refused. The status is never written here.

A lane asked once is kept. When `office start` or `office probe` asks
where a folder's work lands because its lane names no project, or
`office deliver` on a terminal asks which project (it used to refuse and
name `--on`), the answer becomes the folder's lane through `office
folder`'s writer, said: `desk/NAME's lane is PROJECT now, so this is not
asked again (office folder N --lane says otherwise)`. A flag typed for
one run (`--on`, `--in-office`, `--project`) writes nothing; piped, the
flag or the refusal naming it, as before.

The bundle offer and start's screen. Bare `office start` offers the
newest nine bundles by key and one line for the rest: `and N more, oldest
first: office start --bundle FILE starts one by name, office withdraw
--bundle STEM takes one out of the offer`. On a terminal, start's
`[office]` lines are cut to what you read: the `from the ...` lines, the
opener's copy, the tray opened, and last, before the opener, `next:
attach every file in the out tray (PATH) to a fresh chat, then paste the
opener below (office tray SID opens the tray and prints the opener
again)`; the opener now comes after its copy, and the stdout line that
said the same is gone. The rest (the survey, the out tray's files one by
one, bale open --check, the folder opened, the session recorded) is said
under `OFFICE_DEBUG=1`; piped, every line is said as before, for the
scripts and sessions that read the record. A bundle start that asks
nothing prints four or five.

The out tray, opened again. Start keeps the opener it prints beside the
tray, `OUT_TRAY/SID.opener.txt`, outside the tray so every file in it is
still one to attach. `office tray` (the newest session out), `office tray
N` (the folder's newest session) or `office tray SID` opens the tray as
start does (machine.toml's `open_command`; on WSL, Explorer), lists its
files and prints the opener again; it writes nothing. The home screen
offers it, `Open the out tray for folder N, TITLE again (its files and
opener)`, while a session is out whose response is not in your downloads.

`office projects set`. Given a project and any flag, it changes that
flag's group and asks about no other; given none on a terminal, it asks
group by group as before, which `--edit` names (piped, `--edit` refuses).
`--path PATH` re-points a declared project at another clone, checked as
`office projects add` checks one, here or through the project's host
(`--prepare` prepares it); the floor plan's path is rewritten and the
old clone is never touched. `--branch-prefix PREFIX` and
`--no-branch-prefix` write and clear the audience line's fifth key, the
one deliver's branch rule reads.

A bundle opened on a paused project leaves the offer: the home screen and
bare start read a paused project's session list (one status call per
screen) for this one thing, and `office projects set NAME --paused`'s line
says so. Every home-screen item has a key: `1` to `9`, then the letters
no fixed key takes (`b`, `c`, `e`, ...), then capitals; the `and N more`
line is gone.

Tests: tests/test_folders_and_projects.py, one class per item;
tests/test_home_screen.py's page test and tests/test_home_screen_offers.py's
paused line pin the new keys and the new words.

## 0.45.0

Additive: no migration, nothing to do in any office. The eighth serial
session of the plan begun on 2026-10-27: the spanning probe's two defects,
reported on 2026-11-03. A reach is read from a real `office-on` call
alone, and the call's words reach the project's shell as the block's shell
gave them. What you see changes for a probe block that mentions the helper
in text without calling it, and for a call whose words hold a space, a
quote or a `$`; everything else is as it was.

A reach is a call. `office probe` read a block's reaches with a regex over
its text, so `echo "office-on alpha"`, the name in a heredoc, or a word in
any non-comment line that mentioned the helper made the block a spanning
one: planned for the office root, `--project` refused, and a name the
office does not scope refusing the block. Now `office-on` counts as a
reach only where it is a command's first word: at a line's start, or after
`$(`, a backtick, `|`, `||`, `&&`, `;`, `&`, `(` or `{` on the same line,
or after a word that takes a command (`if`, `then`, `else`, `elif`,
`while`, `until`, `do`, `!`, `time`) or a `NAME=value` word; never inside
a quoted string, a comment, a heredoc's body or an `echo`'s text, and
never as part of another word (`./office-on`, `my-office-on`). A quoted or
escaped first word (`'office-on'`, `\office-on`) is not the bare name and
is not a call. A block whose only mention of the helper is text is a
plain block, run where the folder's lane says, as before 0.34.0. The
reader (lib/office_probe.py `calls_of`) is a small scan of the block's
shell syntax, not a regex and not a shell: quotes, backslashes, comments,
heredocs (`<<WORD`, `<<-WORD`, quoted or not), `$( )`, backticks and
groups; a shape it does not read (a command inside `${...}`) reads as
text. `office_probe.py reaches BLOCK` prints what it finds, as before.

The words arrive as given. `office-on PROJECT COMMAND...` handed the words
to the project's shell joined with spaces, so the shell split them again:
`office-on alpha bash -c 'git status; echo x'` ran `bash -c git status`
and then `echo x`, and `grep -n "a b" FILE` arrived as four words. Now
`run_on` quotes each word (shlex.join) as one line for `bash -c`, so
`bash -c SCRIPT` runs SCRIPT whole where the project lives, a word with a
space stays one word, and a quote or a `$` in a word arrives as the
occupant's shell left it. On a host the quoted line goes through the
project's shell exactly as office_host.run_in sends an argv; nothing else
about where or how a call runs changes. One consequence: a shell line
written as one quoted word, `office-on alpha 'pwd -P; git status'`, which
the re-split used to run by accident, is now the name of one command and
fails as such (exit 127); write it `office-on alpha sh -c 'pwd -P; git
status'`. The doctrine (section 4, continued) and the README say both
rules in a sentence each.

Tests: tests/test_spanning_probe.py, one class per rule and a third for
the hosted call through the fake shell; tests/test_three_gaps.py's
spanning block and tests/test_probe.py's masked call write their shell
lines as `sh -c LINE` now.

## 0.44.0

Additive: no migration, nothing to do in any office. The seventh serial
session of the plan begun on 2026-10-27: answers from the artifact. A
question office start or office land would ask is not asked when a
bundle's brief, a response's file name or an office record already
answers it; the offices on this machine are listed, and each office's
home screen shows what waits for the others; every line the office hands
you to type is an office line; and one copy of a probe block runs it.
What you see changes for a bare start or land with something in your
downloads, for a bundle whose brief names its riders or another office's
project, for a landing that ends in a HOLD, a clarification or a
bailout, for bare `office probe`, and on the home screen and the walk-in
when a second office is listed; everything else is as it was.

Answers from the artifact. An answer taken is said in one line, `from
the brief: ...`, `from the folder: ...`, `from the downloads: ...`,
with the flag that says otherwise in parentheses, piped as on a
terminal; only a question nothing answers refuses piped, naming its flag
(`say where the work lands: --in-office, or --on PROJECT (alpha);
nothing answers it (no bundle's paths, no lane), and piped input is
never asked`). So `office start FOLDER --goal TEXT` piped takes where
the work lands from the folder's lane, and from a bundle's paths, as it
did on a terminal. Bare `office start` on a terminal with exactly one
bundle waiting takes it (`from the downloads: one bundle waits, STEM;
starting it (a plain office start FOLDER starts a job instead)`); with
several it offers them by key as before. Bare `office land` with several
sessions out and a response in the downloads for exactly one of them
lands that one, piped or not (`from the downloads: response-SID.tar.gz
is here, so SID lands`); with responses for several, the keys list
those first, each saying its response is in your downloads. A
planner's brief may name the riders its session carries, one line per
ride kept to the byte beside LANDS, BRANCH, RATIFIED and ENDS: `---
RIDES PATH ---` (PATH a rider's path glob, as `office rider add
--rides` takes it) or `--- RIDES none ---`. With RIDES lines start
carries exactly the queued riders whose glob matches one, piped or not,
each said (`from the brief: rider N, TITLE, rides GLOB (its RIDES line
names PATH): carried with this session`); `--carry` and `--carry none`
still win; with none, the forecast's rule as before. A LANDS line naming
a project this office does not scope is no longer a question and a
refusal: start names the office on this machine that scopes it, with
the line that starts it there (`OFFICE_ROOT=ROOT office start --bundle
FILE`), or says that none does, and starts nothing. What leaves the
office (deliver's question, the review's) is never answered from an
artifact.

The offices on this machine. machine.toml gains `offices`, a list of
office roots. `office init` appends the office it builds (the default or
not), `office default PATH` appends PATH, and an office's home screen
appends it the first time it opens there unlisted, said once, so an
office built before 0.44.0 joins the list on its own; a listed root that
is no longer an office is said and skipped by every reader, never
removed. The survey's Machine section names the offices listed
(`offices: NAME (ROOT); NAME (ROOT)`). The home screen and the walk-in,
after this office's own sections, show one section per other listed
office, headed `NAME (ROOT):`: the responses in your downloads for
sessions that office or its projects have out, the bundles that land on
a project only it scopes, and the sittings out there, each a key on the
home screen (`Land SLUG (PROJECT, in NAME): a response for it was saved
AGE in your downloads`) that runs the verb in that office, as if typed
there, and on the walk-in its line, `OFFICE_ROOT=ROOT office land SID`.
Another office is read through its bale registries and the downloads
alone, never its desk, notepad or handbook. A bundle any listed office
opened leaves every office's offer; one landing on a project another
office scopes leaves this office's offer and is offered under that
office; one landing on a project no office here scopes is counted in one
line (`N bundle(s) in your downloads land on projects no office on this
machine scopes: STEM, ...; office withdraw --bundle STEM takes one out
of the offer`). Bare start's offer is cut the same way.

The office's words over bale's. bale's own output at a landing still
rides above the office's words, byte for byte, as bale's record; after
it, before the office's own words, the office prints `In office
words:`, one line per bale verb bale's lines named (`bale retry ->
office land SID --response FILE`, `bale relay -> office relay SID
FILE`, `bale unlock -> office withdraw SID, for a session never worked;
office land SID, for a sitting`, and for revert and amend-checkpoint `no
office line: type it in REPO`); nothing when they named none. A
clarification's Next line is `office relay SID ANSWER-FILE, with the
planner's answer saved here as ANSWER-FILE (office relay carries it to
bale relay in REPO[, through HOST's shell])`, never bale's `(cd REPO &&
bale relay ...)`, and the planner's block gets the office's tail after
bale's END marker: the folder line and `answer: office relay SID
ANSWER-FILE`, so the planner never hands bale's line back. A bailout's
Next line says plainly that the office has no line for it yet (`no
office line yet: type bale handoff RESPONSE in REPO; it packs the fresh
session the handoff asks for, and office sessions N SID records it in
the folder`): `office start FOLDER --handoff RESPONSE`, the brief's item
4, is left for a session of its own.

One copy runs a probe. A probe block's purpose header may carry `#
office: probe FOLDER [--project NAME] [--sid SID]`, kept to the byte.
`office probe` with no folder reads the block first (a file, stdin or
the clipboard) and takes the folder, the project and the session from
the line, said (`from the block: probe 21 --project alpha --sid SID`);
what it leaves out is read as before, a flag typed wins (`--project
office, as typed, stands over the block's --project alpha`), and a line
naming a folder the desk does not hold, a project the office does not
scope or a session not open is one line, that part read as without it.
The line is shown with the header and never run; a line that begins so
and does not read is refused by name. The home screen gains `[r] run
the probe on the clipboard` (`office probe`), shown while a folder on the
desk records a session open where probes run. A text office probe reads
that holds a standing block and no probe block files the standing on
the folder that records its sitting and runs nothing (`the clipboard
holds a standing and no probe: filed on desk/NAME; nothing to run`), so
one verb takes either paste. The home screen's standing key shows for
every read-only sitting a folder records from its first turn, filed or
not; MAX_ITEMS stays nine, since a key is one keypress.

The planner's half. templates/sitting-brief.md and
templates/prep-brief.md say, in What the sitting owes, that the sitting
hands the occupant office lines only, writes the probe block's `#
office: probe ...` line, and may write RIDES lines; the doctrine pins
both past its banner.

What changed and where: bin/office (cmd_probe reads the block first with
no folder, `probe_read_text`, `probe_split_standing`,
`probe_standing_only`; cmd_land's reading of the downloads, the `In
office words:` list and the clarification's tail; `land_tail`'s answer
line; carry_relays' tail on a clarification's block; `ask_where` piped;
`offer_bundles`' one bundle; `bundle_lands_read`'s RIDES, elsewhere and
nowhere lines; `offer_riders`' RIDES; `list_office`, called by init,
default and the home screen; the home screen's `elsewhere` menu kind;
the walk-in's other offices; write_survey's machine file);
lib/office_helper.py (`OFFICES_KEY`, `machine_offices`,
`listed_offices`, `add_machine_office` and the `offices` subcommand;
`brief_rides`, `RIDES_MARK_RE`; survey-render's offices fact);
lib/office_bale.py (`office_words`, `BALE_VERBS`, `relay_next_line`,
`handoff_line`, `plan_repo_words`, `plan_folder_key`; outcome_words'
clarification and bailout lines; bundle_lands' rides, elsewhere and
nowhere; start-riders' `--rides`); lib/office_home.py (the r key,
the standing key from the first turn, `other_offices`, `cut_by_office`,
`office_section`, `other_sections`, `nowhere_line`, the `elsewhere` and
`responses` subcommands, `--machine-file` on page and bundles);
lib/office_probe.py (`run_line`, `RUN_LINE_PREFIX`, `soft_sid` and
plan's `--sid-soft`, the `run-line` and `has-block` subcommands);
lib/office_standing.py (`folder_of`, `folder-of`);
lib/office_drafting.py (`riders_for_rides`); templates/sitting-brief.md
and templates/prep-brief.md; share/verbs.toml (init, default, start,
land, probe); README.md; and the doctrine, past its banner only
(section 4, continued: the RIDES line, the probe's run line, the answers
an artifact gives; section 10: the office's lines over bale's; section
13: the machine's offices). The banner stays at line 299.

Tests: tests/test_from_the_artifact.py (new, 37 tests), one class per
item or a unit class beside its verb class: TestTheRidesLine,
TestAnswersFromTheArtifact and TestTheOneBundleOnATerminal (1);
TestTheOfficesList and TestTheOfficesOnThisMachine, two invented offices
in the test's own tree (2); TestOfficeWords and
TestTheLandingsOfficeWords (3); TestABailoutsLine (4); TestTheRunLine and
TestOneCopyRunsAProbe (5); TestTheStandingAlone and
TestTheStandingFromTheClipboard (6); TestThePlannersHalf (7). Existing
tests changed with what they pin: the bare-start offer test holds two
bundles (one is taken now), the planner's terminal bundle test takes the
one bundle without a key, the unscoped LANDS test reads the new line,
piped start's refusals expect the goal's once the lane answers where, the
standing key's test counts it before any standing, the hosted
clarification's Next line is office relay's, and three return-trip tests
that held machine.toml absent now hold only that land writes no
downloads there (init lists the office in it).

## 0.43.0

Additive: no migration, nothing to do in any office. The sixth serial
session of the plan begun on 2026-10-27: the office shows where a sitting
stands, and a sitting's predecessor no longer stays open beside it. What
you see changes for a read-only sitting that files its standing, for a
planner's bundle whose brief names the sitting it succeeds, for two
sittings open on one folder, for a meeting's prep, for a probe that
prints a credential on stderr, and for a landing run off a terminal;
everything else is as it was.

A sitting files where it stands. The sitting prints its standing block
at the end of any turn where its plan or its place changed (`--- STANDING
BEGIN SID ---`, `step N of M: words`, one `- [x]`, `- [>]` or `- [ ]`
line per step, exactly one `[>]` and it the Nth, `waiting on you: words`,
`--- STANDING END ---`; the last block in a text counts), and `office
standing FOLDER [FILE | -]`, a new plumbing verb, files it on the
sitting's folder as `standing.md`: a heading, `- as of: DATE TIME` in the
office's timezone, `- sitting: SID`, then the block's lines, replaced
whole on each filing and committed alone (`office standing: SID in
NAME`). It reads a file, stdin, or on a terminal the clipboard; piped
with neither it names the two. A block off the shape, or one whose id is
not a session the folder records, is refused by name (`the standing block
does not read: line 6: ...`) and the page is left as it was; an open
session whose forecast holds the page keeps the write out, said. When the
text `office probe` reads carries a standing beside the probe block (the
sitting prints both in one fence, the standing last), probe takes it out
first, so none of its lines runs or reads as an `office-on` call, files
it, says so in one line, and runs the probe as before; one that does not
read is said and not filed, and the probe goes on.

The office shows it. The home screen's item for the sitting ends `; step
N of M: words; waiting on you: words (as of DATE TIME)`, and beside it a
second key, `File where folder N, TITLE stands now, from the sitting's
last standing block on the clipboard`, runs `office standing N`. The
walk-in's In flight line for the sitting carries the same words, and
`office desk` shows `standing, SID's: ...` under a folder's line once its
sitting is no longer in flight. A sitting with no standing filed shows as
before. `office land`, ending the sitting, leaves the page as the record
of where it ended; `office close` moves it with the folder; nothing
deletes it.

office start ends the sitting a brief succeeds. A planner's brief may
carry `--- ENDS SID ---`, read as the LANDS and BRANCH lines are. When
start opens such a bundle, after bale has opened the successor and the
opener is on the clipboard, it ends SID as land ends a sitting (bale
unlock, and `- DATE ended: SID, a read-only sitting, closed by office
start, succeeded by NEW` in each folder that records it, committed as
`office start: SID ended in NAME`), asking once on a terminal, `End the
sitting SID, which this brief succeeds? (--end-predecessor) (y/n) [y]`;
`--end-predecessor` and `--keep-predecessor` are the twins, and piped
with neither it is said with the land line and nothing is ended. An ENDS
line naming a sitting that is not open, not read-only or recorded by no
folder is one line, and the start stands. And whatever a brief says, when
a folder records two or more read-only sittings open, the home screen's
item and the walk-in's line of each but the newest (the one the folder's
Sessions section records last) end `; an older sitting on this folder,
probably over`, and `office probe`, asked which sitting a block is for,
offers the newest first.

A prep's doctrine is stamped and compared. A meeting's prep record line
now ends its lists with `; doctrine: SHORT`, the doctrine it went out
under, and the walk-in's In flight line for the prep compares it with the
install's as it compares a folder's sitting's (`out under an older
doctrine: OFFICE.md OLD when it went out, NEW the install's now`);
nothing refuses. A record line from before 0.43.0 has none and is not
compared.

The probe's stderr is masked. Its stderr is read from a pipe of its own,
beside stdout, and reaches the terminal through a mask of its own, so a
credential in a URL or a GitHub token there comes out as `xxx`; it is
still shown and never kept or copied. When stderr's mask replaced
anything, the count's line names each stream (`1 credential in a URL on
stdout and 1 GitHub token on stderr were masked (xxx stands for each)`).

The office's tail is printed when land is piped, with review state. Off
a terminal nothing is copied, so a landing run from a script or a
session showed the tail to nobody: now, at the end of an applied landing,
land prints each block for the planner whole with the tail after bale's
END marker, under `The block for the planner, whole, with the office's
lines:`. The block comes before the after-land actions' summary, so what became
of each action stays land's last lines, and deliver's Next line on a
project with an audience its very last. On a terminal nothing changes.
The tail gains, after `next:`,
`reviews: #N STATE (BRANCH)` for each review gh reads on a branch the
landed folder delivered to, one per line; none when there is none, when
gh is not there, or when the project has no audience. The read is the
walk-in's: one `gh pr list` for the project, the same timeout, never a
prompt.

What changed and where: lib/office_standing.py (new: `read_block`,
`split`, `page_text`, `read_page`, `folder_standing`, `words`, `write`;
the `check`, `split`, `write` and `show` subcommands); bin/office (the
`standing` verb, `cmd_standing`, `usage_standing` and `file_standing`,
which probe shares; cmd_probe's split before its check; cmd_start's
`--end-predecessor` and `--keep-predecessor` and `start_end_predecessor`,
after the opener; start_prep's `--doctrine` to the record; land_tail's
`reviews:` lines and `print_relays_whole`, piped, before the actions'
summary; the usage texts);
lib/office_helper.py (`brief_ends`, `ENDS_MARK_RE`); lib/office_bale.py
(`OLDER_SITTING_WORDS`, `older_sittings`, `standing_words`,
`desk_standing_lines`, In flight's older, standing and prep doctrine words,
`Doctrines.older_stamp`, `ends_plan` and the `start-ends` subcommand,
`end_sitting`'s `by` and `successor` and land-end's `--by` and
`--successor`); lib/office_home.py (`sitting_item_words`, the standing
key); lib/office_probe.py (`newest_first`, stderr's MaskedScreen,
`mask_parts`, `stream_masks_words`); lib/office_host.py (run_probe's
`err_screen`, a thread copying stderr; its return is as before);
lib/office_meeting.py (the record line's `doctrine`, `mark_prep_out`'s
`doctrine`, prep-out's `--doctrine`); lib/office_review.py (`tail_lines`
and the `tail-lines` subcommand); templates/sitting-brief.md and
templates/prep-brief.md (what the sitting owes: the standing block, and
for a sitting the ENDS line); share/verbs.toml (`standing`, and probe's
writes); README.md; and the doctrine, past its banner only (section 4,
continued: the ENDS line, the standing block beside the ARISING block,
the prep's stamp; the verbs table's standing, probe, start and land
rows). The banner stays at line 299.

Tests: tests/test_standing.py (new, 34 tests), one class per item:
TestTheBlock, TestOfficeStanding and TestOfficeStandingOnATerminal;
TestProbeFilesTheStanding; TestTheScreensShowIt and
TestTheHomeScreenOnATerminal; TestTheBriefsSayIt;
TestLandLeavesTheStanding; TestThePrepsDoctrine;
TestTheHarnessesKillAHungChild; TestTheProbesStderrIsMasked;
TestTheEndsLine and TestTheEndsLineOnATerminal; TestTheTailWhenLandIsPiped;
TestReviewStateOnTheTail. The suite's two pty harnesses that drive a
terminal, tests/test_start.py `on_a_terminal` and tests/test_desk_verbs.py
`terminal`, kill a child still running after their read deadline, with
its process group, and fail the test (`kill_hung`, `wait_briefly`), as
tests/test_front_door.py `run_on_a_pty` does, so a question no test
answers fails one test instead of hanging the terminal lane; no test's
body changed for it. tests/test_meetings_view.py's prep test reads the
record line with its new `doctrine:` part, and tests/test_probe.py
TestTheMaskIsSaid holds the module's new sentence on what the mask
catches. The fast tier gains the verb's
entry point and the block's and the briefs' classes.

## 0.42.0

Additive: no migration, nothing to do in any office. The fifth serial
session of the plan begun on 2026-10-27: pull requests get a protocol,
through gh, held to deliver's standard (shown whole, asked once, recorded
on the folder). gh is optional everywhere: without it every surface does
what it did, and says in one line that gh is not there where it would
have read or opened something. What you see changes after a delivery's
push, on the walk-in, the desk, the home screen and the digest of an
office whose projects have delivered branches, in the survey, and in two
deliver refusals; everything else is as it was.

Deliver opens the review when you say so. After the push, for a branch
with no review yet, when gh is on this machine and signed in to the
audience's GitHub host (github.com, or a host named github.*), deliver
shows the review as gh will open it (the Review section's title and
body, the base, the head, the reviewer when delivery.md's `to:` line
reads as a GitHub login, and the gh line, `gh pr create --repo
HOST/OWNER/REPO --base --head --title --body-file [--reviewer]`) and asks
once, `Open this review on the audience through gh? (--open-review)
(y/n) [n]`. `--open-review` and `--no-open-review` are the twins; piped
with neither, nothing is opened and that is said. On yes it prints
`opened the review: #N URL`, Next names the open review, and the
folder's History gains `- DATE review: BRANCH on AUDIENCE of PROJECT: #N
URL`, a new History verb office status knows, committed alone. gh's
refusal (signed out, no rights, a pull request already open) is said in
gh's words, and the delivery stands. Without gh, signed out, on no, or
on a GitLab host, the review's body goes on the clipboard, said as every
copy is said, and its title and compare URL are printed under Next, so
opening it by hand is one paste. A delivery added to a branch whose
review is open opens nothing and names `the review that carries it: #N
URL` when gh reads it. The office never signs gh in and writes no token,
login or credential.

The office reads review state. For each project with a branch the office
delivered (the folders' `delivered` and `review` lines name them), one
read-only `gh pr list` per project, a 15-second timeout, no prompt: the
walk-in and `office desk` gain a `Reviews:` section after what is in
flight (`proj: #12 approved (health-route, folder 14)`), each review `#N
approved`, `#N changes requested`, `#N review pending`, `#N merged` or
`#N closed`, and for a review that asked for changes a line saying what
answers it; the desk's folder line says `[review #12 approved]` and its
next names the changes asked for first; the home screen's project line
ends `; reviews: ...`; the digest has a `Reviews` section. An open review
always shows, a merged or closed one while its folder is on the desk or
for a week. It is a rendering, recomputed every run and kept nowhere. gh
absent, signed out or the host not answering is one line in the
project's place, never a refusal.

An added delivery is shown from the pull request's base. When a delivery
is added to a branch (adopted, joined or continued) and gh reads the pull
request open on it, the question's branch line shows that request's base
as the delivery's from, and a `from:` line says when it is not the
project's declared `base`; without gh, that line says the base was not
read. The squash is onto the branch's tip either way, and the
`delivered` line is unchanged.

The survey records gh (its version and path, or `not found`) in Tools.

`office letterhead check --delivery FILE` reads a delivery.md as deliver
reads it (its `to:` line and its Commit and Review sections, saying what
it did not read), so a hand check agrees with deliver on a page filed
before 0.35.0, whose filing note names a session; it travels with `--on
PROJECT`. `--words` stays a whole-file read.

The delivery branch's name is held to the letterhead's marks before
anything is fetched: a name the letterhead refuses in a line (a `bale/`
branch, a session id, a forbidden word) is refused with `--branch NAME`,
and a name the folder's slug gives that ends in three digits
(`fix-login-002`) reads as a session id and is refused the same way. A
name you give may end in an issue's number.

A merge session still out stops deliver with its landing line. The
whole loop's test found it: with the merge session open in the clone,
deliver went on to a squash that conflicted and named no office line.
Now it says the session was sent for the folder's merge job and has not
landed, `office land SID brings it back`, as the README already said.

What changed and where: lib/office_review.py (new: `gh_program`, the one
door to gh, through the PATH or `OFFICE_GH_PATH`; `review_offer`,
`open_review`, `record_review`, `review_records`, `open_pull_for`,
`office_reviews`, `project_words`, `review_lines`; the `open`,
`shown-line` and `states` subcommands); lib/office_deliver.py
(`branch_marks` and `check_branch_name` in the plan's steps 3 and 4, the
plan's `review_pr` and `review_pr_told`, run's review offer as a fourth
return value and the run's `review` JSON, Next's title line, the
`delivery-words` subcommand and the check's `--words-json`,
`resolve_landed_job`'s line for a session still out); lib/office_helper.py
(`review` in HISTORY_VERBS); lib/office_bale.py (`read_reviews`,
`desk_folder_line`, the Reviews section in `desk_lines`, `folder_line`'s
`next_first`); lib/office_home.py (`project_rows`' reviews);
lib/office_digest.py (`reviews_section`); bin/office (deliver's
`--open-review` and `--no-open-review`, `deliver_review`,
`deliver_review_words`, the pull request's base in `deliver_show`, gh in
the survey's Tools, `letterhead check --delivery`, the usage texts);
README.md; and the doctrine (boundary 2 in the core gains the review in
its lines, a bullet of section 4's list rewrapped in one line fewer to
keep the banner at 299; past the banner, section 4 continued, the History
verbs and the verbs table's deliver row).

Tests: tests/test_pull_requests.py (new), one class per item:
TestDeliverOpensTheReview and TestOnATerminalItIsAskedOnce;
TestTheOfficeReadsReviewState; TestTheBaseIsThePullRequests;
TestTheSurveyRecordsGh; TestTheCheckReadsADeliveryAsDeliverDoes;
TestTheBranchNameIsHeldToTheMarks; TestTheUnits; gh is the suite's fake
(tests/fakes/gh_fake.py), found through `OFFICE_GH_PATH`, which every
`Env` and every job of the runner set empty. tests/test_deliver_merges.py
TestTheWholeLoopThroughTheOffice runs the merge session's loop through
the office's commands alone.

## 0.41.0

Additive: no migration, nothing to do in any office. The fourth serial
session of the plan begun on 2026-10-27: the next step is offered by key,
so the occupant never types a number he has to look up (the gaps of
2026-10-28, A1, A7's paused mark, A9, A10 and A14, and 0.40.0's proposal
of the waiting merge session). What you see changes for a project with an
audience, for a bundle you will not send, and for a project you pause;
everything else is as it was.

A folder with an audience closes at delivery. `office land` closed a
folder whose one session landed, so a folder on a project with an
audience left the desk before its work was delivered, and its number had
to be guessed for `office deliver N`. Now land leaves it on the desk and
says so in one line (`NAME recorded SID alone, and it landed applied;
PROJECT has an audience, so the folder stays on the desk until office
deliver N carries the work (office close NAME closes it now)`); `--close`
still closes it, and says so. After a successful push, `office deliver`
closes it, done, in land's words (`the folder NAME: closed, done (its
work is delivered; office reopen NAME brings it back)`), once every
applied session the folder records is named by a `delivered` History
line, this delivery's or another folder's, or is held by the base; a
session still to deliver is named and the folder stays. On a terminal it
closes without asking, as land does; piped it stays unless `--close`;
`--leave-open` keeps it. A project with no audience, and an office
session, close at land as before.

Land ends with the deliver line. After an applied landing on a project
with an audience, land's last line, after the relay's clipboard line, is
`Next: office deliver N  (the work landed on PROJECT and is not delivered
yet; deliver carries it to AUDIENCE)`, or, for a merge session, that
deliver makes the merge commit and carries the folder's own work.

What is landed and not delivered is offered. The desk's line for such a
folder says `landed SID on DAY, not delivered; office deliver N`; the
home screen offers `Deliver folder N, TITLE (PROJECT): SID landed DAY,
not yet delivered` by key, newest landing first, after the responses and
before the bundles; the walk-in's Next line names `office deliver N`
after the desk moves and before a drop, and never `office start` for such
a folder; and bare `office deliver` on a terminal offers them first under
`Landed and not yet delivered:` (a plain return lists every folder). All
of it is read from the office's own pages and the project's `applied/SID`
tags with git alone: no fetch, no bale call.

Bare probe takes the one open session's folder. `office probe` with no
folder, when exactly one folder on the desk records a session open where
probes run (a read-only sitting, or a session in the office or on a
project), takes that folder and says so; with several, those folders
alone are offered by key, sittings first.

The office's tail on the planner's relay block. Land's letterhead review
was printed on the terminal and went nowhere else, and the planner asked
for the folder's number and state. Now every block bale printed for the
planner, after an applied landing, carries the office's lines after
bale's END marker (bale's block is byte for byte as bale printed it):
`--- OFFICE land SID ---`, `folder: N, TITLE (desk/NAME, open; closes at
delivery)` (or `desk/NAME, open`, `filing-cabinet/NAME, closed, done`, or
`folder: none`), `next: office deliver N` when land printed it, the
review's lines for a project with an audience, and `--- OFFICE END ---`,
in the clipboard copy and in the whole printing after an unconfirmed one.

A bundle withdrawn from the offer. `office withdraw --bundle STEM`
renames every copy of the stem in the downloads (a browser's `(1)` copies
too) to `NAME.bale-bundle.declined`, said for each, after one question
(default yes; `--yes` piped). The office deletes nothing in the
downloads. A stem no file carries is refused naming the stems there; a
bundle a session opened is refused naming the session. Bare `office
withdraw` offers the sessions never worked and then the bundles no
session opened; the home screen's `w` key shows while either waits
(`withdraw a session never worked, or a bundle`). When the downloads hold
two copies of a stem, the home screen's item and `office start`'s offer
say so: `(saved AGE; 2 copies, the newest offered)`.

A project marked paused. `office projects set NAME --paused` writes
`paused = true` in its entry (`--unpaused` removes it), committed, and
asks nothing else. Every rendering that reads a project's repo (the
walk-in, the home screen, `office desk`, `office status`, `office
sessions`, `office projects` and its renderings, the digest and the
watches) reads nothing of it and says `NAME: paused (office projects set
NAME --unpaused)` where its "cannot read" line would go; `office start`
refuses to send a session to it. A session already out still lands, and
deliver and probe still run.

The waiting merge session, offered by key. A folder whose merge job
names no session is offered `office start N --merge`: on the home screen
(`Send the merge session for folder N, TITLE: AUDIENCE/BRANCH conflicts
with the workbench in K file(s) (office deliver wrote the job on DAY)`),
on the Next line ahead of a landed folder, on the desk's line, and in
`office status` under the folders line. A job whose session landed
without its merge is a landed folder, and status says `office deliver N`
makes the merge commit.

What changed and where: bin/office (land's audience close in
`offer_close`, `folder_cite_key`, `land_where_now`, `land_tail` and the
tail in `carry_relays`, land's Next line, the review's lines kept with
`--out`; deliver's bare offer, `--close` and `--leave-open`,
`deliver_close`; bare probe's folders; `withdraw --bundle` and
`withdraw_bundle`, the combined offer; `projects set --paused` and
`--unpaused`; start's refusal of a paused project; status's merge lines;
the usage texts); lib/office_bale.py (`waiting_on_delivery`,
`applied_tag_times`, `delivered_by_project`, `delivery_move` on the Next
line, `open_words` on the desk, `waiting_lines`, `probe_folders`,
`rendered` and `unread_line` for a paused project, `repos` and
`open_anywhere` with `rendering`, the plan's `audience`; the
`waiting-lines`, `awaiting-delivery` and `probe-folders` subcommands);
lib/office_home.py (the items, `saved_words`, `bundle_copies`,
`withdraw_bundle_check`, `withdraw_bundle`, the `withdraw-bundle`
subcommand, the `w` key's words, the paused row); lib/office_deliver.py
(`still_to_deliver`, the plan's `held_sessions`, land-review's `--out`);
lib/office_helper.py (`paused` in `read_projects`, `set_declarations` and
project-declare, `paused_line`, the listing); lib/office_digest.py and
lib/office_watches.py (a paused project read for nothing); README.md; and
the doctrine (its core's land sentence rewrapped in its lines, and past
the banner).

Tests: tests/test_home_screen_offers.py (new), one class per item:
TestAFolderWithAnAudienceClosesAtDelivery and TestDeliverClosesTheFolder;
TestLandEndsWithTheDeliverLine; TestTheOffersAsUnits, TestTheOffers,
TestBareDeliverOnATerminal, TestBareProbe and TestBareProbeOnATerminal;
TestTheRelayTailOnATerminal; TestABundleWithdrawn and
TestABundleWithdrawnOnATerminal; TestAProjectMarkedPaused;
TestTheWaitingMergeSession.

## 0.40.0

Additive: no migration, nothing to do in any office. The third serial
session of the plan begun on 2026-10-27, and its last word on delivering:
no delivery ends at a terminal. When bringing the audience into the
workbench conflicts, deliver sends a merge session on the folder, and
the session's landed resolution becomes a merge commit; a review the
audience merged as a squash is seen by its content; a continued delivery
is squashed from its range; a session the base already holds leaves the
others list; `office letterhead check --added` works with `--on PROJECT`;
and the question's closing letterhead line says what the check reads.
What you see changes for a project with an audience; everything else is
as it was.

The merge session. 0.39.0 aborted a conflicting merge of the base and
sent you into the clone to merge by hand (the gaps of 2026-10-28, A5's
last clause: the office sends a merge session, never the occupant to a
terminal). Now the abort is followed by the merge's materials, written
into the folder under `merge/`: each conflicting file at its path in
three versions, `parted/` (where the two sides parted), `workbench/` and
`audience/`, `log.txt` (the audience's commits since they parted) and
`merge.md`, the job's page, committed in the office, so they ride with
the folder and move with it when it closes. Deliver's last line is the
one that sends the session, `office start N --merge`. That start packs a
bale session on the folder's project whose goal, forecast (the
conflicting files) and brief (the install's new templates/merge-brief.md)
are the job's, and names the session on the job's page. The brief says
what the session is: the two sides, the files, the commit it brings in,
that its response ships each conflicting file as it should read after the
merge and nothing else, and what every session owes (no Walkthrough,
Delivery or Structure: the folder's pages are the work's; a `## Merge`
section saying what each file kept from each side). When it lands,
`office land` makes the resolution real before anything reads the
workbench: a merge commit in the clone, as the declared author (`Bring
origin/main into the workbench, resolved by SID (office land)`), its
first parent the landed tip and its second the base's tip the job names,
its tree git's own merge of everything that did not conflict with the
session's version of each file the job names (a file the session left
out keeps the workbench's version; a file it deleted is removed). The
office adds nothing of its own: a path still unmerged that the job does
not name, an uncommitted change or a merge in progress aborts the merge
and checks the abort (no MERGE_HEAD, no tracked change left), or never
begins it, and is said with the line that makes it later; a session open
in the clone is never merged under. The next `office deliver N` makes the
merge itself when land could not. The folder's History gains `- DATE
merged: origin/main 3f1a9c2 into the workbench, 7c1e2d3, resolved by
SID`, the materials leave the folder, and the next delivery squashes the
folder's own work from the base's tip. Asked again while the session is
out, deliver names `office land SID` instead of sending another. land
leaves a merge session's folder pages as they are, and says so.

The job lives in the folder, not in a marker line: the brief's design
offered a `--- MERGES AUDIENCE/BASE SHA ---` line read beside LANDS, or
deliver finding the landed job; this release keeps the job's whole state
on its page (`- session: SID` names the session sent), land makes the
merge commit when the session it lands is the one the page names, and
deliver makes it when land could not, so neither needs the brief.

A review merged as a squash, seen by content. A squash leaves neither
the delivery commit nor the workbench commit on the base, so 0.39.0's
`base_holds` refused the next delivery that carried the same sessions,
even with the work on main (deliver-adds' proposal). The history test
stays first; when it fails, the content test squashes the record's
delivery commit onto the base as fetched, in a temporary worktree, and
reads a squash that stages nothing as held. The delivery commit is read
where the delivery is built, or fetched by its branch when it is not
there (`refs/office/audience/held`, removed with the office's other
refs). A base holding a later version of the same lines is not held, and
the refusal stands with its remedy, which is right: the work left twice
would conflict. The refusal says which test failed (`main as fetched does
not hold folder 6's delivery 3f1a9c2 by history or by content (its change
conflicts with the base's)`). No flag says it by hand.

A continued delivery, squashed from its range. A delivery onto a branch
squashed the workbench from where it and the branch parted, so a second
delivery that edited a line the first delivered conflicted with nothing
moved on the audience. Now the range's net change (since the last
delivery there, to the workbench's tip less bale's own commits, bale's
paths out of both ends) is one temporary commit, cherry-picked onto the
branch's tip with git's three-way fallback: only what is new leaves. A
delivery from the base keeps 0.39.0's merge. When the branch moved on the
audience (a reviewer's commit) and the squash conflicts, the merge
session is sent the same way with the branch's tip in the base's place;
its files are what the squash and a merge of the branch's tip into the
workbench conflict in, so the merge land makes conflicts nowhere else.
Once the branch's tip is in the workbench, the next delivery is read from
where the two meet, and the sessions the branch already carries are not
named again.

A session the base holds leaves the others list. After the content (or
history) test lets another folder's record through, the sessions it
covers ride in nothing here: they are left out of `--others-too`'s
question and of the `delivered` line, and one line says so (`folder 6's
session SID is on origin/main already (by content: folder 6's delivery
3f1a9c2) and rides in nothing here`).

The letterhead check. `office letterhead check --added --on PROJECT`
works, here and on a host: the `check` subcommand of lib/office_deliver.py
takes `--added` and passes it to `check_in_project` (wave-one-release's
proposal), and bin/office's refusal is gone. deliver's closing line reads
`letterhead on the lines it adds and the words: clean`, since 0.38.0's
check reads the lines the squash adds, never the diff whole.

What changed and where: lib/office_deliver.py (the merge session's
section: `read_merge_job`, `merge_page_text`, `carry_materials` and its
script, `merge_job_lines`, `make_resolved_merge` and its script,
`resolve_landed_job`, `merge_start`, `merge_sent`, `land_merge`,
`MergeConflict`; `held_by_content`, `base_holds` returning how and why,
`folder_label`, `twice_lines` naming the failed test; `range_commit` and
`unmerged`; plan's step 4c, 6 and 7; the `merge-start`, `merge-sent` and
`land-merge` subcommands, `--added` on `check`; `held_told` in the plan);
templates/merge-brief.md (new); bin/office (start's `--merge`, land's
merge step before its pages, deliver's held lines, the closing letterhead
line, the letterhead check's `--added` with `--on`, the usage texts);
share/verbs.toml (`merge`, a project-session kind; deliver's and land's
writes); README.md; and the doctrine past its core banner (section 4
continued, section 5's History verbs, the verbs table).

Tests: tests/test_deliver_merges.py (new), one class per item:
TestTheMergeSession and TestTheMergeSessionOnAHost (the materials, the
job's page and the line that sends the session; the line that lands a
session already out; land's merge commit, its parents, its tree and its
History line, and the delivery after it; deliver making it when land did
not; a conflict the session did not resolve aborted and checked; a
session open in the clone; the materials and the merge through the
shell), TestTheMergeSessionGoesOut (start --merge's pack, forecast, brief
and context, and its refusals) and TestOfficeLandMakesTheMerge (land's
step on a real landing, the pages left); TestASquashMergedReviewIsSeenByContent
(a squash-merged review let through, the units, a later version refused
with the test named); TestAContinuedDeliveryIsSquashedFromItsRange (a
delivered line edited again; a branch that moved sending a merge session
for its tip, and the delivery after it); TestAHeldSessionLeavesTheOthersList;
TestTheCheckTakesAddedOnAProject and TestTheCheckTakesAddedOnAHost;
TestTheClosingLetterheadLine. tests/test_host_refresh.py's conflict test
names the merge session; tests/test_clean_delivery.py no longer expects
the `--on` refusal; the old closing line's words moved in
tests/test_clean_delivery.py and tests/test_delivery_words.py.

## 0.39.0

Additive: no migration, nothing to do in any office. The second serial
session of the plan begun on 2026-10-27: a clone on a host gets its view
of the audience refreshed through this machine, start and deliver offer
that refresh when the view is behind, deliver brings the base into the
workbench itself when that merge is clean, and prepare writes bale's
sandbox setting where bale's own sandbox cannot run, so an apply in a
container stops asking. What you see changes for a project with an
audience, and for a clone in a container; everything else is as it was.
The merge that conflicts is not here: the office names the files and
says the merge session is the next release's.

A clone's view of its audience, refreshed. A clone on a host often has
no credentials for the audience's git host, so its remote-tracking refs
stayed where they were when it was made (found 2026-10-27: weeks stale;
a hand-written script carried them over as a bundle, and a branch the
audience force-pushed stayed stale until a second one). `office projects
refresh NAME` fetches the audience's branches on this machine, with this
machine's credentials and always with a forcing refspec; for a clone on a
host it reads the clone's refs first, bundles the branches that moved,
thin against what the clone already has, carries the bundle through the
shell and fetches it there with `+refs/heads/*:refs/remotes/AUDIENCE/*`,
removing it in the same connection; for a clone here it is a plain
forced fetch. It fast-forwards the base (`--ff-only` when it is checked
out, clean and no session is open there; the ref moved after an ancestry
check otherwise), says and leaves a base with commits of its own (a
refresh never merges), stops only that step for a dirty tree, says what
moved (`origin/main: 59385bf..3f1a9c2, 14 commits`, `forced`, `new`) or
`nothing moved`, never moves the workbench branch, deletes no ref and
pushes nothing. It leaves one ref in the clone,
`refs/office-refresh/AUDIENCE`, and `office projects` lists under each
project with an audience when it was last refreshed and from where, read
from the clone (one connection per hosted such project; the listing
made none before). There is no `office refresh` short verb:
`office projects refresh` is the one door, and start and deliver offer
it.

The offers. `office start`, for a project with an audience, compares the
clone's view of the base with the audience's (`git ls-remote` here, and
a count in a temporary repo only when they differ) before anything is
packed and before a BRANCH checkout; `office deliver` compares it with
the base it has just fetched. Behind, one line says by how much (`the
clone's view of origin/main is 14 commits behind the audience's`), and on
a terminal each asks once whether to refresh first (default yes;
`--refresh` and `--no-refresh` are the twins); piped with neither, it is
said and the work goes on without. Level or ahead, nothing is said. For
a clone on this machine deliver's own fetch already moves that ref, so
deliver says nothing there.

The clean merge. Deliver's squash ran from where the workbench and the
base parted, so after a review merged on the git host the squash onto
the new main conflicted and the remedy, bring main into the workbench
first, needed a terminal in the clone (the gaps of 2026-10-28, A5). Now,
for a delivery made from the base, when the workbench is behind it and
the clone's view of it is level, deliver merges the base into the
workbench branch in the clone where the work lives (`git merge --no-ff`,
`Bring origin/main into the workbench (office deliver)`, as the declared
author), only when the merge is clean, the clone's tree is clean and no
bale session is open there; each of the three is said when it stops the
merge, and the plan goes on as before. The question's `merged:` line
says it (`brought origin/main into the workbench: merge commit 8c2e1f0
(14 commits of the audience's)`), the folder's History gains `- DATE
merged: origin/main 3f1a9c2 into the workbench, 8c2e1f0` (a new verb in
the closed set office status checks, changing no status), and the squash
runs from the base's tip. A conflict is aborted and the abort checked
(no MERGE_HEAD, no tracked change left), and the delivery refuses naming
the files, with one line saying the merge session is the next release's
and what to do by hand until then. A delivery adding to a branch is not
merged (its squash is the next session's to read from its range), and
`base_holds`, the refusal of work leaving twice, the squash and
`--others-too` are as they were.

bale's sandbox setting. bale's sandbox self-probe refuses in a container
with no unprivileged user namespaces, and every apply there asked to run
unconfined and recorded it (A12). Prepare (`office projects add
--prepare`, `--from`) now tests that condition where the clone is,
through the host's shell for a hosted one, with `unshare -Ur true` (one
user namespace, the least bale's sandbox needs, so the office's test is
never stricter than bale's), and only where it refuses writes
bale.toml's project-layer `[sandbox] enabled = false`, under a comment
naming why and the day; bale then runs unconfined there without asking
and FORCE-logs the key on every run, as its help says. Where the sandbox
runs nothing is written; a `[sandbox]` table already there is left; a
test that cannot run writes nothing. `office projects set NAME --prepare`
runs prepare again on a declared clone, asking nothing, so the clones
added before this release get the setting without being added again.
`office status` names it per hosted project (`proj: sandbox: off by
bale.toml, written 2026-10-29: no unprivileged user namespaces where this
clone is (...)`), read beside `bale --version` in the same connection,
and where the sandbox cannot run and nothing turns it off, it names the
line that writes it.

What changed and where: lib/office_refresh.py (new: the refresh, its
view of a clone, start's compare, the listing's line); lib/office_host.py
(prepare's sandbox step, `sandbox_line`, `sandbox_state` with
`sandbox_argv` and `read_sandbox`, `git_facts_argv` and `read_git_facts`,
prepare and clone_to taking the office's day); lib/office_deliver.py
(plan's step 4b and 4c, `merge_base_in`, `merged_text`, `NeedsRefresh`,
`--refresh`, `--no-refresh` and `--day` on plan; the clone's facts and its
view of the audience in one connection); lib/office_bale.py (status's
sandbox line, `sandbox_status_line`; `--day` on prepare-project and
clone-to); lib/office_helper.py (`merged` in HISTORY_VERBS, the
listing's refreshed line); bin/office (`office projects refresh`, `office
projects set --prepare`, start's `start_offer_refresh` and its two flags,
deliver's planning loop over its two questions and its two flags, the
`merged:` line, the usage texts); share/verbs.toml; README.md; and the
doctrine past its core banner (section 4 continued, the verbs table,
section 5's History verbs, section 10's word on bale's project layer).

Tests: tests/test_host_refresh.py (new), one class per item:
TestTheRefreshVerb and TestTheRefreshVerbOnAHost (what moved, forced and
new, the base fast-forwarded checked out or not, a dirty tree and an
open session stopping only that step, the workbench untouched, the thin
bundle through the shell and its directory gone, the refusals);
TestTheOffers and TestTheOffersOnATerminal (piped said, --refresh,
--no-refresh, the twins refused together, a clone here, start's compare
as a unit, the question on a terminal); TestTheCleanMerge and
TestTheCleanMergeOnAHost (the merge commit as the author, the delivery
from the base's tip carrying the folder's files alone, the History
line, a conflict aborted and refused by name, a dirty clone and an open
session left as they are); TestTheSandboxSetting and
TestTheSandboxSettingOnAHost (written only where the probe refuses, the
office's own table kept, the occupant's table left, a probe that cannot
run, set --prepare through the shell, status's line in bale's
connection); TestTheRecord (the History verb, the listing read from the
clone). The suite's environment gives every test a sandbox that runs
(OFFICE_SANDBOX_PROBE), and tests/test_suite_clock.py names the new
module's top-level siblings. Twenty-two new tests; the suite holds
1146, 1124 at 0.38.0. The whole suite, run in the worker's sandbox,
passed all 1146; the detached run after the landing is yours to record.

## 0.38.0

Additive: no migration, nothing to do in any office. Four sessions
landed beside each other on 0.37.0 as wave 1 of the plan the planning
sitting of 2026-10-27 began (the friction of a work office's first
deliveries, and the gaps found on 2026-10-28), each in the lib/ modules
it owned, and none bumped the version or wrote a release of its own. So
this release carries their four paragraphs as they wrote them, in this
order: deliver's, the probe's, land's filing of a fact and office
sessions'. Then what this session changed itself: every doc line those
four left stale, made true again; two lines on deliver's question, the
rule that chose the branch and the folder whose branch it continues;
`office letterhead check --added`; and a wrapped handbook fact filed
whole.

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

office probe masks a credential in a URL. A probe printed `git remote
-v` in a project whose remote URL held a personal access token, and the
token went to the screen, the clipboard and the paste back to chat
(found 2026-10-28; the token was revoked). Now everything `office probe`
hands back is masked: on your terminal as the block streams, in the
block it puts on your clipboard, and in what it says after. A credential
written into a URL, `scheme://user:SECRET@host`, any scheme, comes back
as `scheme://user:xxx@host`, its user kept so you still know whose it
was; a GitHub token in one of its own shapes (`ghp_`, `gho_`, `ghu_`,
`ghs_`, `ghr_`, `github_pat_`), bare or as a URL's user part, comes back
as `ghp_xxx`. When anything was masked, the line after the output says
how many (`4 line(s) came back between PROBE BEGIN and PROBE END, and
the integrity trailer's count matches; 1 credential in a URL was masked
(xxx stands for it)`); when nothing was, nothing is said. A line is
masked, never dropped, so the block's count and its integrity trailer
still match, and the folder's History line is as it was. The mask is a
seatbelt, not a promise: a probe should still never print a remote URL
with a credential in it (`git remote -v`, `git config --get
remote.NAME.url`), a token of any other shape printed bare is not
caught, and the block's stderr, a fallback's probe-output/ files and the
block's own closing `bale clipboard` copy are not masked.
lib/office_probe.py `mask_text`, `masked_words` and the writer
`MaskedScreen`, which `run` hands `office_host.run_probe` as its screen:
it holds a partial line until its end arrives, so a credential split
between two reads is still caught, and writes each line masked; `run`
masks the text run_probe kept the same way before it reads the block out
of it, and puts the counts in its result as `masked`, which
`count_words` says. lib/office_host.py and bin/office are unchanged.
tests/test_probe.py's TestTheMask, TestTheMaskedRun, TestTheMaskIsSaid
and TestTheMaskOnATerminal, 14 tests: the mask's bounds, a credential
split at every byte between reads, the screen and the block of a run,
`office probe` piped and on a terminal with its clipboard, a spanning
block's `office-on` output, and the words.

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

`office sessions FOLDER` reads past a project it cannot read. When one
project in the floor plan could not be read (a clone where git cannot
read HEAD, a directory gone, a host not answering), the verb searched
every project, hit that one, and reported the folder's sessions as
unreadable or not found (found 2026-10-28: distributions-app's broken
clone stopped `office sessions 10`, and a probe had to do its job). Now
each project is read in its own try, and only when the search for one
of the folder's sessions reaches it. The folder's own project, the one
its lane names, is searched first, then the projects whose records name
the session, then the rest. So a folder's session is found with one
read in the common case, and an unrelated broken clone or a host that
is down is never even opened. A project that cannot be read is said
once, in one line after the sessions (`distributions-app: not read:
WHY`, with bale's or the host's words), and the search goes on. A
session found renders as it always did. The verb stops (exit 3 from the
reader, bin/office's "some of this office's projects could not be
read") only when a session was not found while some project could not
be read, since only then is "not found" in doubt, and its line says so
(`not found in the projects that could be read; distributions-app could
not`). A record bale holds but cannot parse stays that session's own
`cannot read` line, and its project stays in the search for the others.
lib/office_bale.py `project_records`, `folder_lane` and
`PROJECT_WIDE_KINDS` are new; `locate` and `render_folder_sessions`
carry them, and the hosted batch of dossiers now rides the first read
of each host rather than a loop over every host up front, at the same
two connections per host. And a test that no release heading is lost
again: tests/test_land.py TestTheReleasesMatchTheFrontSheet reads
RELEASES.md's `## X.Y.Z` headings and the front sheet's `- X.Y.Z
(session SID)` lines under Recent changes, the older record, and fails
naming any version in one and not the other, so a heading lost in a
whole-file overlay (what 87ce51a did to 0.33.0's) fails the suite on the
next run, a minor or a patch release alike. Tests:
tests/test_sessions_read.py, new (TestOneUnreadableProjectIsALine,
TestTheFoldersOwnProjectFirst, TestLocate, TestAHostThatDoesNotAnswer),
and tests/test_land.py TestTheReleasesMatchTheFrontSheet. Nineteen new
tests.

What this session changed. The docs the four left stale say what the
tool does now: README.md (deliver's summary and its details, the branch
rule among them; the probe's mask; land's filing and its review; the
letterhead check and its cleanup list; office projects' fifth audience
key, read and not yet settable; office sessions' search; the layout's
rows), doctrine/OFFICE.md (the probe's output masked, on its front sheet
and in the verb table; a fact written bare and filed whole, in section
4's bullet, the landing's paragraph and the Handbook's; deliver's
paragraph and its row; the letterhead's cleanup list; the office's one
clock for every date it writes, beside Calendar; office sessions' search
in section 10), bin/office's usage for probe, deliver and letterhead
check, and templates/drop-brief.md, which now says to write each fact
bare as the sort brief does. Deliver's question prints what its plan
already knew: the branch line ends with the rule that chose the branch
(`branch: feature/results-view, from main (delivery.md's branch line
names results-view, behind api's branch prefix feature/)`), and on a
branch another folder of the office delivered to it names that folder
and its day in place of the plain continuing words (`branch:
health-route (adding to the branch desk/6-picklists delivered to on
2026-10-28), from main (...)`); an adoption keeps its sentence. `office
letterhead check --added` passes the module's flag through, with
`--range` or on the index against HEAD; the module refuses it beside
`--all`, and bin/office refuses it with `--on PROJECT` by name, since
the check that travels to a project's repo does not carry it yet. office
sessions' stop says what stopped it (`a session was not found and some
of this office's projects could not be read; the lines above say
which`). And a handbook fact that wraps onto indented lines, as a list
item does, is filed whole: lib/office_sort.py `list_items` joins each
continuation line (two or more spaces, outside a fence) onto the `- `
fact above it with one space, in a Handbook section (`parse_handbook`)
and in a Sort's `facts:` lines (`parse_sort`, which keeps them verbatim
on the drop's page), so a session id that fell on a continuation line is
dropped as one on the first line is. Before, only a wrapped fact's first
line was filed: read that way, 0.37.0's own notes give office-src's
chapter five facts cut off, and wave 1's probe and sessions notes six
each. Those lines stay, the handbook being append-only, and a cut-off
fact does not key as the whole one, so filing such a response again adds
the whole fact beside the cut-off line; mend the chapter by hand once,
if you want to. Tests: tests/test_audience_line.py
TestTheBranchLineSaysWhichRule, tests/test_clean_delivery.py
TestTheHandCheckTakesAdded, tests/test_sort.py
TestAWrappedFactIsFiledWhole and TestLandFilesAFactBare's wrapped fact,
and tests/test_land.py TestTheWaveOneRecord (the four paragraphs above
held to the archived notes they came from, byte for byte); thirteen new
tests. Each of the four paragraphs' counts was true for its session
alone on 0.37.0; the merged tree held 1111 tests before this
session and holds 1124 with it, and the whole suite, run in the
worker's sandbox, passed all 1124; the detached run after the
landing is yours to record.

## 0.37.0

Additive: no migration, nothing to do in any office. A small session
sent ahead of the six that remain of the planning sitting of 2026-10-27:
`office land` passes bale's two per-invocation accepts through, and this
file has its 0.33.0 entry back. What you see changes only when you type
one of the two flags, or when bale refuses for one of their two causes;
every other line of a landing is as it was.

bale's two accepts, through office land. bale apply and bale retry
refuse two things without asking: a blind checkpoint that changed
between the pack and the landing, and a file the response changes whose
base moved since the pack. Each is accepted on one invocation only, by a
flag bale deliberately gives no setting. office land took none of bale's
flags, so after `bale amend-checkpoint` the retry of the same response
had to be run by hand with bale, outside land, and nothing land does
after a landing (the filing, the after-land actions, the closing) ran
for it (found 2026-10-28). Now `office land SID
--accept-checkpoint-change` and `office land SID --accept-base-drift
PATH` (once per path, as bale's is) hand the flags to that landing's
apply or retry, before the tarball, exactly as typed, through the
project's shell for a project on a host. Each is said in its own line
before bale runs (`passing --accept-checkpoint-change to bale retry, as
you typed it: ...`). land never adds one on its own and no setting turns
one on, as bale has none. When bale refuses a moved base, land's Next
line is the office line that accepts it: the paths bale's own re-run
line names, and any accept typed this time said again, since bale
carries none forward. bale refuses a changed checkpoint before it stages
anything, on its error stream, which a landing here does not keep, and
records no attempt, so the office cannot tell that refusal from another:
a retry refused that way names `office land SID
--accept-checkpoint-change` as its Next line, offered on bale's words
above it (where bale's own line does reach the office, through a host's
terminal, the refusal is named outright). A read-only sitting lands
nothing, so an accept on one is refused with nothing ended. The
admissions bale asks for itself (a path outside the forecast, a missing
required check) stay bale's questions on your terminal, as before.
share/bale-consumption.toml declares the two flags on `[surfaces.apply]`
and `[surfaces.retry]`, a switch and a repeated flag placed before the
tarball by a new key, `flags_before`, and its contract lines name the
help they come from; lib/office_bale.py `accept_flags`, `accept_said`,
`accepts_bale_names` and `accept_line`, with `land_plan`, `land_run` and
`outcome_words` carrying them; bin/office `cmd_land` reads the two flags
and `usage_land` says them, as do README.md's land details and the
doctrine's section 4, continued, where it describes the landing.

The 0.33.0 entry, restored. On the tree 0.34.0 was followed directly by
0.32.0, so tests/test_answer_review.py TestTheRecord errored on every
whole run and the history skipped a release. Read against the tag, only
one line was gone: the entry's heading. Its body was still there, at the
end of 0.34.0's entry, read as part of it. git log shows where: 0.34.0's
own work commit (87ce51a, the first commit after 0.33.0's landing to
touch RELEASES.md, whose parent still held the heading) wrote 0.34.0's
entry above the old one with the old heading left out, a blank line
doubled where it had been, and every landing since built on that. bale's
base-drift gate could not see it, since the base had not moved under
that session. The heading is back, and from it to 0.32.0's the entry is
that release's own text, byte for byte, as the tree's history holds it
(`git show applied/2026-10-28-m10-sitting-fixes-001:RELEASES.md`),
checked by sha256, not written again; a test now pins that sha256.

Tests: tests/test_land.py TestLandPassesBalesAccepts (a moved base names
the office line and that line lands it; the checkpoint switch reaches
the retry as typed; a retry refused after `bale amend-checkpoint` names
the office line and that line lands it; a sitting refuses an accept; no
setting turns one on; the units) and TestTheLandFlagsRecord (this
release's record, the releases in order with none skipped, and the
0.33.0 entry's bytes); tests/test_return_trip.py TestTheAcceptsOnAHost
(both accepts through a host's shell, as typed); and
tests/test_land.py's declaration test, which now holds the two accepts
as the only flags apply and retry declare. 0.36.0's version pin in
tests/test_bale_own_commits.py now reads 0.36.0 or later, as the pins
before it do. Ten new tests; the suite holds 1053, 1043 at 0.36.0. The
whole suite, run in the worker's sandbox, passed all 1053; the detached
run after the landing is yours to record.

## 0.36.0

Additive: no migration, nothing to do in any office. Delivering a work
office's folder 6 on 2026-10-28, bale's own commit `bale: ignore .bale/`
(1ee6bc7: `.bale/` added to `.gitignore` where bale was first set up in
the clone) rode in beside the session's work, and the letterhead did not
refuse it. `office deliver` squashed the whole workbench range and took
only bale's names out of the index, so what a bale commit changed in a
file the clone tracks left with the work; and a bale path was not among
the letterhead's marks. Deliver promises no bale commit leaves, and now
keeps it in content as well as in name, two said ways.

What bale's own commits changed stays out. Before the squash, the
commits of bale's own in the delivered range are undone on the
workbench's tip: `git revert`, newest first, each in a temporary commit
made in the worktree and never pushed, and the squash takes the result.
Bale's own commits are the ones bale makes for itself with no session's
work in them, as share/bale-consumption.toml declares them
(`[surfaces.commits] own`, `bale: ` by its start, and the sweeps the
`subjects` table already names; `Consumption.own_commit`); a session's
`[bale SID]` work commit and its `Merge bale SID` landing are the work,
never bale's own. The plan names each one under `taken out:` (its sha,
subject and files), and `office deliver` logs them as it starts. Three
shapes the revert meets: a line of bale's that later work on the
workbench already took out is simply gone (the three-way merge sees both
sides agree); later work on the same lines conflicts, and when adding
lines was all bale did to that file, bale's lines are taken out of the
workbench's version one by one, the file deleted when nothing is left of
one bale created, and the plan says so; anything else, a bale commit that
removed or changed lines that later work also touches, refuses the
delivery by name with the remedy (undo its change by hand on the
workbench branch, and deliver again), with nothing pushed
(lib/office_deliver.py `own_commits`, `take_out_own`,
`lines_added_only`, `plan` step 7). A hosted project's bale commits
come here in the bundle as before and are undone in the mirror: still
three connections.

A bale path is one of the letterhead's marks. `.bale/` and the files
named after it (`.bale-bundle`, `.bale-manifest.json`), `bale.toml` and
`.baleignore` join share/letterhead.toml's marks, so a line that leaves
naming one refuses a delivery whatever put it there: the backstop for a
bale line that reaches the squash some other way (a session's own work
adding it, say, which is not bale's commit). lib/office_host.py's
EXCLUDE_LINES and the marks are held to one list by the suite; bale's
record directory is a name already. The files deliver takes out of the
index stay on the worktree's disk, so the check is now told never to
read them (`never=NEVER_DELIVERED`), and a tracked bale.toml naming
bale's directory refuses nothing; the check says `N file(s) of bale's
never read` when there are any.

The already delivered branch of folder 6 keeps the `.bale/` line it was
given: this release changes what leaves from now on and rewrites nothing
on an audience. The doctrine's section 2 bullet and section 7 paragraph,
README's deliver summary, details and letterhead paragraph, the layout
rows, `office deliver --help` and `office letterhead check --help` say
it. The doctrine's core was one line over its reading pin (301) since
0.34.0; two ragged paragraphs and the section 2 bullet are rewrapped,
content unchanged, and the core reads in 299 lines again.

Tests: tests/test_bale_own_commits.py (15 tests in five classes): the
shapes against the probe's captured subjects, the marks against
EXCLUDE_LINES and plain words, the delivery with the housekeeping commit
in the range (gone and named; a line the audience's file already has; a
line already taken out by hand; later work on the same lines, one by one,
in both of git's conflict shapes; a commit that did more, refused by
name, nothing pushed; the sweep taken out and a second delivery reading
only its own range; the backstop on a work commit's `.bale/` line and on
the words; a tracked bale.toml never read), the same on a host, and the
record. The suite's `AudienceCase` world is unchanged.

## 0.35.0

Additive: no migration, nothing to do in any office. A folder whose
delivery.md `office land` filed could not be delivered without a hand
edit: land wrote a comment under the page's heading naming the session
the page came from, a session id is one of bale's marks, and `office
deliver`'s letterhead check read the page whole, so it refused that line
(found 2026-10-27, delivering a folder whose words came from a build
session's notes). What you see changes in three said ways.

`office deliver` reads the words that leave. The letterhead check reads
what of delivery.md becomes the delivery: its `to:` line and its Commit
and Review sections, each hit still named at its own line of the page.
The page's heading, the comment land files under it and anything else
above the first Commit or Review stay in the office and are not read,
and deliver says how many such lines it left (a line under "letterhead
on the diff and the words: clean"). `office land`'s review
reads the page the same way, so it never names a line deliver would not
refuse. A page filed before this release delivers as it stands, its
comment's session id and all, with no edit and no migration
(lib/office_helper.py `delivery_leaving_text`; lib/office_deliver.py
`delivery_words`, `plan`, `land_review`).

A filled pull-request template's headings stay in the Review. A
delivery.md section now runs to the next Commit or Review heading, so a
template's own `## Summary` (or any `## ` heading of another name) filled
into the Review is part of the review's body. Before, such a heading
ended the Review: the review's body stopped short of it and the
template's lines never left, though the letterhead read them. The words
deliver sends and the words the letterhead reads now come from one
reading of the page (lib/office_helper.py `delivery_sections`,
`parse_delivery`).

The page `office land` files names no session. delivery.md's comment is
now "filed by office land from the build session's notes.md", so the
page holds no word of land's own that any letterhead check would refuse,
`office letterhead check --words` by hand included; walkthrough.md, which
stays in the office, still names its session. The folder's Sessions
section and the office's commit name it as before
(lib/office_helper.py `filing_note`, `file_pages`).

## 0.34.0

Additive: no migration, nothing to do in any office. This release fixes
the three gaps the M10 walkthrough hit on 2026-10-27, when a planner
sitting answered a coworker's review of a pull request on a hosted
project (the work office's folder 6): the answer's delivery could not
reach the review's branch, its bundle could not say which branch to
build on, and its probes could not read the office and the host in one
block. What you see changes in three said ways: `office deliver` adopts
a branch made outside the office when you say so, a bundle's brief names
the branch its session builds on and `office start` checks it out first,
and `office probe` runs a block that spans the office and a project's
host.

`office deliver` adopts a branch made outside the office. A branch the
audience already has that the folder's records do not cover was refused
by name, with "name another": right for a stranger's branch, wrong for
the pull request the review is on, where the answer's commits must go.
Now deliver says such a branch was made outside the office (a pull
request opened by hand, or another folder's) and, on a terminal, asks
once whether to add this delivery to it, default no; `--adopt` is the
twin, and piped, deliver refuses and names it. Adopted, the delivery is
built on the branch as it is on the audience, its own commits kept, and
the range of landed work read is what the branch does not have yet,
from where the workbench and the branch parted, so commits the branch
got by hand from the same clone are not delivered twice. The folder's
`delivered` line ends `; adopted`, the next line names the reviews open
for that branch on the git host (GitHub's pull requests with that head,
GitLab's merge requests with that source branch) and says the Review
section's words are the reply, and the next delivery for the folder adds
to the branch as to one of its own, no flag needed. A branch the folder
delivered to before is never called adopted, and `--adopt` changes
nothing for it (lib/office_deliver.py `plan`, `branch_url`;
lib/office_helper.py `delivered_text`, `delivered_records`).

A planner's bundle names the branch its session builds on. bale opens a
bundle in the clone as it stands, on whatever branch is checked out
there, and its bundle format names no branch; the review's answer was
packed on the clone's main. Now a brief may carry one line, `--- BRANCH
picklists ---`, in the shape of its LANDS line and read where that line
is read (outside fences and notepad pages; a line that does not read, or
a second one, is said and the first taken), and `office start` checks
that branch out in the project's clone, here or through its shell on a
host, before `bale open --check` runs: its local branch, or a new one
tracking the one remote that has it. A clone with uncommitted changes, a
clone with a session open in it (bale lands that session on the branch
checked out, so the clone is not moved under it) and a clone with no such
branch locally or on a remote it has fetched each stop the start with
nothing written and say what to do in the clone; the office fetches
nothing, since the clone's credentials are not its own. A clone already
on the branch is said. A BRANCH line in a bundle that lands in the
office is refused, since the office works on one branch
(lib/office_helper.py `brief_branch`; lib/office_bale.py `bundle_lands`,
`checkout_branch`; bin/office `bundle_lands_read`, `check_start_bundle`).

`office probe` runs a block that spans the office and a project's host.
A probe ran in one place: a project's repo, through its shell, or the
office root; a sitting that needed the office's folder and the hosted
repo in one block had none, and ran its reads by hand. Now a block that
calls `office-on PROJECT COMMAND...` on its own lines runs in the office
root with that helper first on its PATH, written beside the plan for the
one run, and each call runs its command where that project lives, in its
repo here or through its shell in its path on a host, stdin closed, its
output on the block's stream and its exit code returned (97 when the
project cannot be reached, or is not one the block named). The projects
are read from the block before anything runs, each named literally, and
one the office does not scope refuses by name. Such a block takes no
`--project` (`office` alone fits, and is said); its session is the
folder's open in the office, a sitting or an office session, or in a
project it reaches, chosen by the rule a probe of one place uses, so a
sitting's spanning probe is found without `--sid`; a fallback's
`probe-output/` is the office root's, carried as before. The header's
read-only promise covers every command the calls run (lib/office_probe.py
`reaches_of`, `plan_spanning`, `write_on_helper`, `run_on`;
lib/office_host.py `run_probe` takes an environment).

The doctrine says the three in section 4, continued (the BRANCH line
beside the LANDS line, and the adopted branch beside the delivery), in
section 10 (the spanning probe beside the relay), in its front sheet and
in its verb table; README.md says them where the verbs are;
templates/sitting-brief.md names the BRANCH line among what a sitting
owes.

Tests: tests/test_three_gaps.py, a new module (`TestAnAdoptedBranch`:
piped refused by name and `--adopt` adding to the branch, the record and
the next line, a second delivery continuing, the folder's own branch
never adopted, the URLs as units; `TestAnAdoptedBranchOnAHost`;
`TestAnAdoptedBranchOnATerminal`; `TestTheBundlesBranch`: the reading as
a unit, the checkout before bale's rehearsal and a clone already on the
branch, a remote's branch tracked, what stops it with nothing written;
`TestTheBundlesBranchOnAHost`: the checkout through the shell before the
rehearsal; `TestASpanningProbe`: the reaches read from the block's own
lines, the run in the office root and each call where the project lives,
a project the office does not scope, `--project` not fitting, a sitting's
spanning probe and its fallback, the helper as a unit;
`TestASpanningProbeOnAHost`); 17 tests, and the suite holds 1017.
tests/test_audience_line.py's pin on the old refusal holds as written,
since its two phrases are in the new one. The eight touched modules, run
whole in the worker's sandbox, passed their 308 tests; the whole suite's
detached run after the landing is yours to record.

## 0.33.0

Additive: no migration, nothing to do in any office. This release is the
second of eight the planning sitting of 2026-10-27 drew from the M10
walkthrough: three things a planner sitting runs into, each small on its
own. What you see changes in three said ways: an answer of several lines
is shown back to keep before it goes, `office probe` runs a sitting's
probe of a project, and a sitting out under an older doctrine than the
install's says so wherever the sitting is shown.

An answer of several lines is seen whole before it goes. The home
screen's p key, `office start new`, `start --planner` and the profile's
questions take an answer that may run to several lines, a blank line
ending it, and a line already ended could not be edited: the answer went
into the folder, or out in a sitting's brief, as typed. Now, when the
blank line ends it, the whole answer is shown numbered and one question
follows: keep it (a plain return), redo it from its first line, more
lines after the last, or a line's number to type that line again (a
blank one takes it out). Nothing is written or packed until it is kept,
and `?` explains. With VISUAL or EDITOR set and the terminal his, the
answer is taken in that editor instead, as git takes a commit message: a
scratch file seeded with the question and its explanation as comment
lines, read back less them and less blank lines; he saw the whole there,
so nothing is shown back. An editor that fails, or comes back empty where
an answer is needed, is said, and the answer is asked at the prompt. The
editor draws on the terminal stderr is, since office start new reads the
words inside a command substitution. The flag twins (`--words`, the
profile's section flags) are untouched, and piped input is never asked
(bin/office `review_lines` and `edit_answer`, under `ask_words` and
`ask_paragraph`).

`office probe` serves a read-only sitting. A sitting is open in the
office's own registry, never in a project, so a sitting's probe of a
hosted project's repo found no session there and was refused; the
sitting of 2026-10-27 ran six probes by hand through ssh instead. Now a
read-only sitting the folder records, open in the office, is a session a
probe can be for: with `--project NAME` the block runs in that project's
repo, through its shell on a host, under the sitting's id, its
fallback's files carried to the sitting's out tray and its History line
counted against the sitting. The header, the one question, the
one-writer rule and a `probe-output/` already there refusing hold as
before. A folder with a sitting and a session open in the project keeps
the project's session unless the block's slug or `--sid` names the
sitting; without `--project`, a sitting's folder is asked where, or runs
in the office root, as before. A writing office session is not a sitting
and is never offered (lib/office_probe.py `open_sittings` and
`choose_session`).

The doctrine a sitting went out under is stamped and compared.
office-src moved from 0.30.0 to 0.31.0 during that sitting, and the
doctrine's bytes changed; the sitting learned it only because `office
status` was run. Now office start writes the install's doctrine hash,
the sha256 of doctrine/OFFICE.md as it rides (the bytes the rides-once
check reads), in two places: one line in the opening of a planner
sitting's brief, and of a meeting prep's (templates/sitting-brief.md,
templates/prep-brief.md), and the folder's Sessions line for every
sitting it sends from a folder, a bundle's included, `- SID: sitting,
doctrine SHORT` (the first twelve characters). The walk-in's In flight,
the home screen's item that ends a sitting and a new `doctrine:` line in
`office status` read the stamp back, and when it is not the install's
say that the sitting is out under an older doctrine, both short hashes
named, in one line. Nothing refuses: the sitting may finish on the
doctrine it read. A sitting from before this release has no stamp and is
not compared, and a prep, which no folder records, carries the brief's
line only. A brief whose install holds no readable OFFICE.md leaves the
line out and says so (lib/office_bale.py `install_doctrine_hash`,
`Doctrines` and `doctrine_lines`; lib/office_helper.py `sitting_words`
and `session_doctrine`). The doctrine says it in section 4, continued,
where it describes the sitting's brief.

The doctrine also says the answer's review in section 7, beside the
wizard rule, and the probe's sitting in its front sheet and verb table;
README.md says all three where the verbs are.

Tests: tests/test_answer_review.py, a new module
(`TestAnAnswerIsSeenWholeBeforeItGoes`: a line typed again and more
lines, redo, `?` and a key it does not take, no line left, the editor and
its seed, an editor that fails or comes back empty and VISUAL on a dumb
terminal; `TestPipedNothingIsAsked`; `TestTheProfilesAnswersAreSeenWhole`;
the record);
tests/test_probe.py `TestASittingsProbeOfAProject` (the project's repo
under the sitting's id, the out tray, piped and without `--project` as
before, both open, a writing office session, the choice as a unit) and a
hosted case in `TestProbeOnAHost`; tests/test_planner_from_words.py
`TestTheDoctrineASittingWentOutUnder` (the hash's bytes, the brief and
the Sessions line, a read-only start and a project session, the walk-in
and status quiet and then saying it, a sitting from before the stamp,
the words as units, the prep's brief and an unreadable doctrine) and
`TestTheDoctrineOnTheHomeScreen`. The terminal tests that type into these
questions keep their answer with a plain return, and the sitting tests
that pinned a bare Sessions line pin the stamp. `office status` prints
its `doctrine:` line below `skew:`, so the bytecode line keeps its place
above `built from:` (tests/test_office.py `TestTheInstallsBytecodeCache`),
and 0.32.0's record pin in tests/test_walkthrough_tidy.py now reads
0.32.0 or later, as test_probe's has since 0.19.0. The suite holds 1000
tests, 974 at 0.32.0.

## 0.32.0

Additive: no migration, nothing to do in any office. This release is the
first of eight the planning sitting of 2026-10-27 drew from the M10
walkthrough: four small things, none depending on another. What you see
changes in three small, said ways: a ticked box in a repository's
pull-request template no longer refuses a delivery, a delivery of
several commits dates them in order and says so before it asks, and a
drop whose text is an office command line is asked about. The fourth is
this file's own.

A checklist line is the template's whatever its box holds. The
letterhead's exemption for a repository's pull-request template matched
a line exactly, so ticking the box of the template's documentation line
(`- [ ]` to `- [x]`) made it the occupant's line, and the phrasing rule
refused it. The template's lines and the words' are now compared with
the box's state folded (`- [x]`, `- [X]` and `- [ ]` read as one), so a
ticked line is exempt from the phrasing rule and the three characters
as the unticked one is. Names, bale's marks and the forbidden list still read
it, and words added after the box make a changed line, held to all of
it. The hosted form of the check, the module sent on stdin, is the same
module and reads it the same way (lib/office_letterhead.py
`template_key`).

A delivery's commits are dated in order. office deliver made several
commits back to back on git's clock, so they shared one second, a
pattern a reader of the audience's history notices. Now the first is
dated as it is made and each after it one second later, author and
committer date alike (GIT_AUTHOR_DATE and GIT_COMMITTER_DATE, at this
machine's offset). The question shows each commit's date, and before a
delivery of several commits it says in one line how many leave and that
one per delivery is the usual shape. Which commits are made is as it was
(lib/office_deliver.py `commit_dates` and `commits_line`).

A drop that is an office command line is asked about. Copying a command
from a chat replaces what the clipboard held, and office drop took the
command as the message: the in-tray of 2026-10-27 holds a drop whose
whole text is `office drop --project m10-api`. Now a text of one
non-blank line beginning `office ` is asked about once when it comes
from the clipboard, before anything is written: drop it anyway, no by
default, `--anyway` the twin, and a yes writes it. From a file or stdin
it is written as given, and the line saying what the drop took says it
is an office command line. The drop still never refuses a drop it can
write. The doctrine's In-tray paragraph says so (section 5).

The 0.31.0 entry reads whole. Its Tests line ended in two placeholders
its session never filled; they now say what the entry meant, from
tests/test_tidy.py and the suite's record. Release notes are not filed
paper, so this is an edit, said here.

Tests: tests/test_clean_delivery.py `TestATickedTemplateLine` (the box
folded and nothing else; a ticked line exempt and a changed one held;
the hosted form) and `TestTheDeliveryCommitsDates` (the dates and the
line as units; commit_words a second apart; deliver's question with two
commits and with one); tests/test_drop.py `TestADropThatIsAnOfficeCommand`
(piped and from a file, said; anything else a message; the usage and the
doctrine) and `TestADropThatIsAnOfficeCommandOnATerminal` (no, the
default, drops nothing; a yes writes it, and --anyway asks nothing);
tests/test_walkthrough_tidy.py `TestTheReleaseNoteReadsWhole` (the
0.31.0 entry with no placeholder left, its count as tests/test_tidy.py
holds it) and the record's pins. The suite holds 974 tests, 958 at 0.31.0.

## 0.31.0

Additive: no migration, nothing to do in any office. This release is the
tidy after the front-door arc: eight small items the arc's workers
proposed and the queue carried, each a few lines, none depending on
another. What you see changes in four small, said ways: one `office
status` line, one walk-in line and its Next line, the drafting table
arriving with the in-tray's sort, and the doctrine's words; everything
else is as it was.

A sitting's pages are one sitting. office start files a sitting's words
under its slug (SLUG.md, then SLUG-2.md and on), and the watches and the
digest joined only a page named SID-N.md to SID.md, so a sitting of three
pages counted as three. A page SLUG-N.md now joins SLUG.md whenever
SLUG.md is a sitting's page too, as the planner's own reading of a
sitting's pages always joined them (lib/office_watches.py `sitting_key`).

The drafting table on a sitting's list. The digest office start writes
just before a sitting is packed brings the drafting table into an office
that has none, so the table rides with every sitting, a meeting's prep
included. The planner sitting's list named it even where there was none
yet; the prep's list left it out there, though it rode. Both now name it
the same way, and where there is none yet the line says it arrives with
its digest (lib/office_planner.py `every_sitting_carries`).

`office status` names, one `structure:` line each, a folder still
marked provisional though every session it records landed applied (by
bale's applied/ tags, read with git): its Structure never came back, or
came back off its shape and was not filed. Nothing when there is none,
and never a refusal.

A response filed twice adds nothing twice. `office land` and `office
sessions --pages` file a session's Questions and answers into its
folder and its facts into the handbook chapter; filed again from the
same response, a line already there is said and left, a fact from the
same session is the same fact whatever day it was filed, and a front
sheet that already reads as the session's is not written again. Nothing
filed is rewritten.

The drafting table arrives with `office start --sort`. The sort forecasts
the drafting table's moves page; in an office with no drafting table it
had nowhere for its moves to land. Now the table arrives first, as the
in-tray arrives with the first drop: its pages from the install's
templates, the floor plan's entry and bale.toml's trigger, each only
when missing, committed alone, the one-writer rule held over each.

The doctrine's second-desk sentence (section 4, continued) now says what
office start has done since 0.18.0: a second desk is bale's to
recognize, and the office refuses an overlap only where bale would. The
doctrine also says the three changes above where it pins them: the
sort's forecast, status's line, and the walk-in's line and its place in
the Next line's order.

The install's bytecode cache on the walk-in. When the cache 0.30.0 gave
the install is not level for the python3 that runs it (after a Python
upgrade, say), the walk-in says so in `office status`'s words, a
`Bytecode:` line in the walk-in's head, in any office, and the Next
line names install.sh's line right after an install behind its source:
until it runs, every command compiles the helpers from source and takes
about twice as long. Under a cache prefix, and from a working copy,
nothing is said. The home screen's first item follows the Next line.

The letterhead check reads the cache too. office deliver, and office
land's review, ran the check on this machine as a script, whose own code
Python never reads from a cache, so each check compiled office_letterhead's
540 lines. It now runs as a module, the way bin/office's pylib runs every
helper; its output and exits are as they were. The hosted form, the
module sent on stdin, is unchanged.

Tests: tests/test_tidy.py, 16 tests, one class per item; and the
record's pins. The whole suite, run detached after the landing, passed
its 958 tests in 245 seconds on the occupant's machine, where 0.30.0's
run passed 942 in 250.

## 0.30.0

Additive: no migration, nothing to do in any office, and nothing an
office does changes but one new line in `office status`. This release is
about what a helper call spends compiling. Every `office` command runs
its Python helpers with `-B` and never writes the install, so in
everyday use, with no bytecode cache, each call compiled the module it
loaded from source: about 50 ms of CPU for office_helper in the worker's
sandbox, and 150 for office_bale, about half of what a call cost. Now
install.sh compiles them once, as it installs, and every call reads the
compiled code. In the worker's two-core sandbox, each version run from
an install its own install.sh made, `office status` took 0.30 seconds
where it took 0.56, the walk-in 0.40 where 0.92, a start 1.6 where 2.8
and a land 1.3 where 2.9. Installing takes about half a second longer.

The bytecode cache. install.sh compiles lib/ into lib/__pycache__,
beside the sources it copies, with the python3 on the PATH (bytecode is
tagged by its interpreter, so the cache is the machine's own), in its
staging directory before the install takes its place: nothing has to be
writable once it is installed, and no command writes it (`-B` stays).
The caller's PYTHON* settings are kept out of the compile (`python3
-I`), each module is checked by its source's size and time, as Python
always checks it, and a compile that fails is said while the install
goes on without the cache. `office status` says whether the cache is
level, in one line under the install's source line: level with lib/'s
modules, for which interpreter; or which of them compile from source on
every call (after a Python upgrade, or a source changed inside the
install) and the line that brings the cache level, install.sh run again
from its working copy. It is a line, never a refusal: a module whose
compiled code is stale or missing still runs, compiled as it loads.

The landing in one call. `office land`'s three helper calls for the
landing itself (take the office's record out of an office session's
folder, run bale apply or retry with the terminal, read how it ended
from bale's records) are one, `office_bale land`. It says the record's
line itself, in its place between the first two, and writes how the
landing ended to a file of its own, since bale's output is on its
stdout. A plain landing starts nine helpers where it started eleven,
about 150 ms less with the cache.

What the occupant sees is as it was, byte for byte, but for the new
status line: the suite, and 21 commands compared against the unchanged
tree in the suite's world (the landings with both streams interleaved
as a terminal shows them, a held one and its retry, an office session's,
one whose outcome could not be read), with a zone database and without
one. The whole suite took 659 seconds where 0.29.0's took 658 on the
same sandbox (924 tests then, 942 now, none dropped); the runner already
compiled the office's modules into its own cache, so its time barely
moves.

Tests: tests/test_office.py `TestTheInstallsBytecodeCache` (install.sh
into the Env's own prefix: the cache for every module, whatever the
caller's PYTHON* settings; status's line, every helper of a status read
from it with the install read-only, nothing in the install written; a
stale and a missing cache, and install.sh again; a compile that fails; a
copy outside git carrying none of the working copy's cache) and
`TestTheBytecodeLine` (every state of the line, a cache prefix, and the
pyc checks the import system makes); tests/test_land.py
`TestTheLandingInOneCall` (the record's line between the landing line
and bale's; the outcome unread, with the record out and without) and
`TestLandWholeInProcess` (each step as its own process ran it, and the
exit codes bin/office reads); `TestFewerHelperStarts` there counts nine
helpers for a landing. And one test that could fail on a fast machine no
longer does: tests/test_watches_digest.py ran the digest twice and
counted a commit for the second run, but the page is stamped to the
second, so two runs inside one second wrote the same bytes and had
nothing to commit; the test now waits the clock past the first page's
second (under a second) before the second run.

## 0.29.0

Additive: no migration, nothing to do in any office, and nothing an
office does changes. This release is about how many Python helpers an
`office` command starts: `office status` started 17, a walk-in 10, a
plain start on a project 23 and its landing 19 (a landing that sorts
drops and mints their folders about 45), and each start cost about 35 ms
of interpreter and module loading before it read anything, or about 95
in everyday use, where no bytecode cache spares a call from compiling
the module it loads. Now `office status` starts one, a walk-in three,
that start twelve and its landing eleven (the sorting landing about 29),
and a land's twenty-odd `python3 -c` reads of a helper's JSON answer are
four. In the worker's two-core sandbox `office status` took
0.5 seconds where it took 2.3 in everyday use (0.26 where 1.3 with the
suite's bytecode cache), the walk-in 0.85 where 1.5, a start 2.6 where
4.0 and a land 2.7 where 4.2; the whole suite 652 seconds where
0.28.0's took 894 on the same sandbox, the fast tier 56.0 where 64.2,
every test kept and five added.

Several reads in one helper call. `office_helper batch` runs several
subcommands, of office_helper or of a sibling module, in one process,
each exactly as its own call would have run (its module's main, its
argv, its stdout captured at the file descriptor, its exit code kept,
its stderr inherited, discarded or merged as the call's redirection
was), and prints one record per call; bin/office builds the batch with
`batch_call` and reads the records back with `batch_run`, each call's
answer into a variable and its exit code into `VAR_rc`. The reads that
sat side by side in a command, with no write or question between them,
go out as one call: every read `office status` makes, the walk-in's
head and its page, a start's skew, profile and project names and then
its folder's facts, the founding folder, the profile and the out tray,
a land's zone and downloads, its two sort questions and its two
closings' three reads. A read that follows a write, or depends on
another's answer, stays a call of its own after it.

The stamps and the skew in one read. `office_helper skew-report` prints
the two version stamps and then the skew report, where nearly every
command read them as three calls (stamp, skew, stamp again); bin/office
reads it once per command (`skew_read`), a verb's own code run inside
another (land running moves and close) answering from that read until
`office upgrade` writes the stamp. The floor plan's timezone name and a
project's facts are read once per command the same way.

A JSON answer read once. The fields bin/office read back from a helper's
JSON line with one `python3 -c` each (a start's eight, a land's fourteen
plan fields and five outcome fields, the standalone sort's and the
prep's five, a delivery's four, a blueprint's close four) are one
`json_read` each, an interpreter start that prints the fields in the
same records `batch_run` reads; the one-liners that stay single run
with `-B -P -S`, as the helpers do.

What the occupant sees is as it was, byte for byte: every verb's stdout,
stderr and exit code, compared on eighteen commands against the
unchanged tree besides the suite, with two things to know. The walk-in
in an office with a calendar says once that the floor plan names a zone
this machine lacks, where it said it twice (its head, then office week's
own read); and the lines a batched read prints to stderr as it runs (an
error, and only then) come before the stdout lines the command prints
from the batch's answers, where they came between them.

Tests: tests/test_suite_clock.py `TestFewerHelperStarts` (the batch
against each call run alone, its stderr modes and its refusals;
skew-report; bin/office's `batch_run` and `json_read` read into
variables) and tests/test_land.py `TestFewerHelperStarts` (a python3 on
the PATH ahead of the real one counts what a status, a walk-in, a start
and a land start).

## 0.28.0

Additive: no migration, nothing to do in any office, and nothing an
office does changes. This release is about the time the office's Python
helpers take to start: every `office` command starts several (`office
status` 17, a start about 11, a land about 45), and in the worker's
two-core sandbox a small helper call went from 85 ms to 42, the whole
suite from 1,245 seconds to 866 and the fast tier from 85.4 to
64.1, with every test kept and five added.

Imports where they are used. Each lib/ module imported its heavy standard
modules (subprocess, tarfile, tempfile, tomllib, json, shlex, hashlib,
threading, zoneinfo, urllib) and its sibling modules at the top, so a
call that compared two versions loaded the same code as a start. Now a
function imports what it uses where it starts, and the top of a module
holds only what every call needs (argparse, datetime, os, pathlib, re,
sys, and office_helper; office_bale keeps office_host, which most of its
functions read hosted projects through). Three quarters of a helper
call's import time was these modules.

Patterns compiled when first used. The regular expressions a module
holds at its top compiled as it loaded, about 5 ms in office_helper and
9 in office_drafting, and a call uses a few of them; they are
`office_helper.LazyPattern` now, compiled the first time one is used
and answering for the compiled pattern after.

One subcommand's parser. office_helper and office_bale built a parser
for every subcommand (53 and 30) before reading which one the call
named, about 6 and 9 ms; a call that names its subcommand now builds
that one parser (`OneSubcommand`), and a call that names none, a flag or
an unknown name builds them all, so argparse's usage, help and errors
read as they did.

`-S` in `pylib`. bin/office starts its Python without site: lib/ is
standard library only, so nothing it imports is lost, and the start
skips site's work and its search of site-packages. The one standard
module that can reach site-packages is zoneinfo, for the tzdata package
on a machine with no system zoneinfo directory; there the office's zone
names fall back to UTC, said under OFFICE_DEBUG, as they already do for
a name that does not resolve.

Nothing the occupant sees changes: every verb's output, exit code and
side effects are as they were, and the suite is the net. Tests:
tests/test_suite_clock.py holds every lib/ module to the rule (which
modules load at import, what a small read loads, the lazy patterns, the
one-subcommand parser, and `-S` in `pylib`).

## 0.27.0

Additive: no migration, nothing to do in any office, and nothing an
office does changes. This release is about the test suite's time: in
the worker's two-core sandbox the whole suite went from 1,146 to
822 seconds, and the fast tier from 66.2 to 59.6, with
every test kept and eight added.

A case's world, built once. Most of the suite's time was each test
building the same world again before it ran one command of its own: an
office made by `office init`, founded, a project added, a folder opened,
a fake bale beside them. A case whose setUp builds such a world (the
land, start, audience, hosted and watch cases, and the plain office
most of test_office and test_desk_verbs start from) now builds it once
per job, and every test gets a copy at the same path, with what the
setUp set, made before the test and removed after it
(tests/test_office.py `kept_setup`). A world built on an earlier day is
built again.

The fake bales as fixed modules. The fakes that pack, apply and replay
are modules under tests/fakes/, no longer script texts written into
every test's tree and compiled on every call. The `bale` a test puts on
its PATH is a three-line program that imports one with the test's
config, so the runner's bytecode cache holds the fake's code; the land
fake hands `--version`, `status` and its packs to the packing fake in
its own process instead of starting the interpreter again, and loads
what a verb needs where that verb starts. A `bale --version` that took
84 ms takes 24. The land fake reads the directory each capture was made
in from the capture's own `cwd` (the rider from 0.21.0's queue), which
retires the suite rule's largest allowance.

The survey's last reads of the machine, made steerable. `office survey`
looks for the tools it records, and for the bale and office on the
PATH, only in the directories `OFFICE_SURVEY_PATH` lists when it is set,
and takes its container marker from `OFFICE_CONTAINER_MARKER`; unset, it
reads the PATH and `/.dockerenv` exactly as before. Every test's `Env`
and every job of the runner set both empty, so no survey in the suite
runs a program of the machine's for its version (its R, node, bale or
installed office) or searches a WSL machine's Windows directories on the
PATH.

The terminal helper. `on_a_terminal` in tests/test_start.py starts its
program with SIGINT and SIGQUIT at their defaults, as `run_on_a_pty` has
since 0.26.0 (the rider from session 4).

## 0.26.0

Additive: no migration, nothing to do in any office. A meeting is a view
over the work: said once in your words, its prep briefed from what landed
since the last one, what arises in it queued for after as drops, and a
cleanup of its projects' documentation offered by design. A repository's
own pull-request template is exempt from the three characters as well,
the terminal wizard works a project with an audience on this machine by
default, and the tour's interrupt test holds however the suite was
started. Every flag sets its field as before, and piped input is never
asked anything.

A meeting, asked once. `office meeting` (the home screen's `m` key) takes
a meeting in one sentence of yours, "weekly review every Monday at 9
about alpha and beta", and writes one line in the calendar's plan: when
it happens, its title (your words, less when) and the projects it
concerns, `[about: alpha, beta]`. It asks only when your words do not say
when, or name none of the office's projects (the office itself is an
answer); `--words`, `--when`, `--about PROJECT` and `--in-office` are the
twins. A series is one line, never asked for again. No folder is made.
The calendar arrives with the first meeting, from the install's new
templates/calendar-plan.md and calendar-record.md, as the in-tray arrives
with the first drop; times are local, in the floor plan's timezone.

Its prep. From a day before a meeting until four hours after it starts,
the home screen offers its prep by key (`office start --prep [MEETING]`):
a read-only sitting from the office, through the planner sitting's
gathering, its goal the meeting's words and its brief the install's new
templates/prep-brief.md. It carries what landed on the meeting's
projects since the last meeting on them (the 14 days before it, for a
first), every landed session counting, with each project's handbook
chapter, its folders on the desk, the unsorted drops and the drops tied
to the last meeting with the folders they became, each said with why. No
folder records it: the calendar's record line names it, `prep out`. The
same sitting serves during the meeting.

What arises, queued for after. The sitting writes what arises in one
arising block, pinned to the byte in the doctrine, and offers it as a
file, arising-SID.md. `office land SID` reads it (`--arising FILE`, the
downloads, or the clipboard once you copy it; never retyped), ends the
sitting with bale's unlock, rewrites the record line as `held` and files
each item as a drop in the in-tray, tied to the meeting, saying in one
line what it filed. A block that does not read stops land with the
sitting open. A drop you make yourself while the meeting is on with its
prep out is tied to it as well. The next meeting on those projects
carries them, and the folders they became, in its prep. `office week`
shows a meeting's projects and a prep that is out.

A cleanup rides along. The prep's brief tells the sitting it may author
one cleanup session for the meeting's projects when their documentation
is messy, disorganized or too wordy: a planner's bundle beside the
briefing, with its LANDS line, which you send or delete. The scheduled,
unattended cleanup of the office stays "not yet".

The doctrine says what a meeting is now: the verbs table's `meeting` (a
script on your surface) and `prep` (an office session, built) rows, the
calendar paragraph (its arrival, the `[about: ...]` suffix and the
record lines the office writes), the clipboards retired (no clipboard is
made; a series is a line in the plan, its running items drops), and a
Sort's `tell:` kept on the folder's Next, which the next meeting's prep
reads. The withdrawn design's capture verb, rolodex, owed tells and
declared ride-alongs are not built.

A template's own dashes. The lines of a repository's own pull-request
template, as the repository holds them, are exempt from the em dash, the
en dash and the ellipsis too, not only from the phrasing rule; the lines
the words add, and a template line changed, are still checked, and names,
bale's marks and the forbidden list still read every line.

The workbench, on a terminal too. `office projects add` on a terminal,
once a project given a host has an audience, offers by key where it is
worked: on this machine from a guarded clone (the default; it asks the
clone's path here and records the host as `validates_on`), or on the host
(`--worked-on-host`). Answering the questions in order no longer works it
on the host.

The tour's interrupt test. It failed only in a run started in the
background (SIGINT ignored, which every process it starts inherits, and a
shell cannot trap a signal it inherited ignored). The pty helper now
starts the tour with SIGINT and SIGQUIT at their defaults, as a terminal
does, and the test runs itself with SIGINT ignored; the runner's warning
about such runs is retired with the cause.

## 0.25.0

Additive: no migration. Landing and delivery hold the audience line by
default: the letterhead refuses the dashes, a repository's own
pull-request template is exempt from its phrasing rule, a letterhead has
a voice page, every commit deliver pushes is shown whole and carries the
declared author, the push guard covers tags and bale's refs, and a
project with an audience is worked from a guarded clone on this machine.
`office upgrade` brings what this release adds to an office without a
migration (the letterhead's missing pages, the current push guard), and
`office status` names what is missing. Every flag sets its field as
before, and piped input is never asked anything.

The dashes. In an office that has a letterhead, `office letterhead check`
and everything that runs it (office deliver, office land's review) refuse
the em dash (U+2014), the en dash (U+2013) and the ellipsis character
(U+2026), with no line in the office needed; each refusal names the file,
the line and the character by name. The letterhead's forbidden list lifts
one with a line `lift: em dash` (or en dash, or ellipsis); every check
that reads a lift says so, and a lift naming anything else stops the
check. share/letterhead.toml carries the three as a `[characters]` table.

The pull-request template. When the words fill a repository's own
pull-request template, the lines that are the template's as the
repository holds them (at the audience's base, for a delivery; at HEAD
for `office letterhead check --words`) are not held to the phrasing
rule; the lines the words add, and anything a template line is changed
into, are, and every other rule still reads all of them. Which files are
templates is read from the repository, by the places GitHub, GitLab and
Azure DevOps look for one.

The voice page. A letterhead has three pages from the install's new
templates: README.md; voice.md, the occupant's style rule for text that
leaves the office, an empty place plainly marked for his words, which
office-src never writes; and forbidden.txt, whose template names the
three characters as refused by default. The letterhead arrives with the
first project given an audience (`office projects add` or `set
--audience`); a letterhead from an earlier release gets its voice page
from `office upgrade`, and `office status` names it missing, or empty,
with the line that adds it. The letterhead rides beside every session on
a project with an audience, and the doctrine (section 4) has such a
session read the voice page before it writes.

Every commit reviewed, under the declared author. `office deliver` makes
the commits before it asks and shows each whole, as it will be pushed:
its subject and body, its author and committer, the files it touches, and
the letterhead's verdict on it; then asks once. Every commit it makes or
pushes carries the project's declared `author` as both author and
committer, and it checks that on the commits themselves before the push,
which no longer lets a tag follow. A project with an audience and no
declared author is asked for it once on a terminal and keeps it
(`office deliver --author "Name <email>"` is the twin, and sets the
field); piped, deliver refuses and names `--author`. The clone's own
identity is never used. `office land`, on a project with an audience,
reviews what the session landed against the letterhead (the change, and
the folder's delivery.md words) and says in a line what deliver would
refuse, each line named; it refuses nothing.

The push guard. From a clone with a declared audience nothing reaches the
audience but the one delivery branch deliver pushes: no tag (bale's
applied/ tags or any other), no bale branch, no other ref and no
deletion, whatever the push's form (`--tags`, `--all`, `--mirror`, a
refspec, a tag by name), the audience known by its remote's name or by
any URL that is the same repository. Each refusal names office deliver.
The hook carries `guard_version=2`; `office status` names an older guard
(0.17.0's) with the line that replaces it, and `office upgrade` and
`office projects set` (with nothing else to set, piped too) replace it.

The workbench on this machine. `office projects add` for a project with
an audience takes its path as a guarded clone on this machine; a host
declared with it (`--host`, or `--validates-on HOST`) is recorded in the
project's entry as `validates_on`, where it validates, never where it is
worked, and nothing validates there yet (that is S3's, waiting on bale's
remote validation runner). `--worked-on-host` keeps the old shape, and a
host answered on a terminal is that, said. Projects already declared on
a host keep working exactly as they did.

## 0.24.0

Additive: no migration, nothing to do in any office. A planner sitting
goes out from your words with the context the office gathers for it, the
in-tray's sort is offered first when drops wait, the digest lists the
unsorted drops, a planner's bundle says where it lands, and a session you
sent out and will never run is withdrawn by key. Every flag sets its
field as before, and piped input is never asked anything.

A planner sitting from your words. `office start --planner` (the home
screen's `p` key; `office start new --planner` mints its folder, `office
start FOLDER --planner` records it in one on the desk) asks what you want
a planner for, in your words, and sends a read-only sitting out: your
words are its goal, kept in the folder's Asked section, and nothing else
is asked but what the sitting concerns, only when your words name none of
the office's projects and the answer changes what rides (the office
itself is an answer: `--about PROJECT`, `--in-office`). The office gathers
what rides, says why one line each on the screen and first in the
sitting's brief (the install's new templates/sitting-brief.md), and stays
inside bale's caps, leaving out the oldest of what landed first, said:
each concerned project's handbook chapter, the folder.md of each folder on
the desk on it, the walkthrough page of each job that landed on it since
the last sitting, and the last sitting's notepad pages, beside what every
sitting carries (doctrine section 4, continued, pins the set and its
order). Piped, `--words` and the flag twins send the same sitting.

The sort offered first. Before any sitting is packed (from your words,
`--read-only`, or a sitting's bundle), unsorted drops in the in-tray are
said and the in-tray's sort is offered by key. Taken (`--sort-first`), the
sort goes out and the sitting right after it, in the same motion, the
sitting's opener the copy left on the clipboard; declined
(`--no-sort-first`), or piped with neither, the sitting goes alone and
carries the drops, as before.

The digest lists the unsorted drops: digest.md has an In-tray section,
each drop by its page's file name with the project it names, or none.

A planner's bundle says where it lands. A brief may carry one line, kept
to the byte like the RATIFIED lines: `--- LANDS alpha, folder 14 ---`,
`--- LANDS the office, folder 14 ---`, or `--- LANDS alpha, a new folder
---`. `office start --bundle`, bare `office start` and the home screen
then send the bundle without asking where it lands or which job, and say
both in one line; each question comes back, alone and said, only when the
line is absent, does not read, or names a project or a folder the office
does not hold. bale's bundle format is untouched.

A session never worked, withdrawn. `office withdraw` (the home screen's
`w` key, while there is one) names a session you sent out that has no
response in your downloads and no apply begun by its folder, asks once
(`--yes` the twin), runs bale's unlock with bale's reason `abandoned`
where the session is open (through the shell for a hosted project), and
writes a `withdrawn` line in the folder's History. A folder that recorded
that session alone is said with the line that closes it, never closed for
you. share/bale-consumption.toml declares the new `withdraw` surface.

## 0.23.0

Additive: no migration, nothing to do in any office. New work comes in
through one door, a new folder's structure comes back from its session,
the landing asks nothing about ratification, and every clipboard copy the
office claims is true. Every flag sets its field as before, and piped
input is never asked anything.

One door for new work. `office start new` takes the job in your words
(asked on a terminal; `--words TEXT` gives them, piped too), names the
project only when your words name none of the office's, mints the folder
through `office open`'s own code, and sends the session out with its out
tray and opener, in one motion. The home screen's `o` key runs it, and
the Next line names it when nothing else waits. `office open` is plumbing
now (`office help --all` lists it, with every flag it took); `office help`
lists `office start new` in its place. A drop is still a door into the
same path: drop, start, land.

The folder's structure, returned by its session. The title, size and goal
the office works out from your words (and the title and size of a folder
minted for a drop) are named on a new field line, `- provisional: title,
size, goal`; a flag you give is yours and never provisional. Every
session that works a folder writes `## Structure` at the end of its
notes.md, three lines in a pinned form (doctrine sections 3 and 4), and
`office land` files each value over a provisional one, says in one line
what changed, and leaves your words in the Asked section as they are.
`office status` names a provisional line that does not read.

Ratification leaves the landing. `office land` asks nothing about it, on
any path, and a folder is finished when its one session landed applied:
on a terminal land closes it and names the line that reopens it. The
planner's ratification travels in the next brief it writes, one line per
session, `--- RATIFIED SID ---` or `--- RATIFIED SID, except: TEXT ---`,
and `office start` files each in the folder that records the session, on
the desk or in the filing cabinet, as the last line of its Sessions
section, and says so; a session no folder records is said and skipped.
`office land --ratified` and `office sessions --ratified` still record
one by hand; `--not-now` is taken and changes nothing.

A copy the office claims is a copy. On WSL clip.exe is fed UTF-16LE, so
an em dash survives; the office copies after bale has (the opener once
the pack has ended, the relay as land's very last step, after the
after-land actions, a probe's output after the probe's own step), reads
the clipboard back with the machine's paste command, copies once more if
something copied over it, and says the copy is on the clipboard only when
it reads back. Every other outcome (no clipboard command, off a terminal,
no way to read it back, a copy that reads back otherwise) is one line
pointing at the block on the screen, and land prints the block again.
bale's own copy feeds clip.exe UTF-8, which Windows reads in the
console's code page: that half is bale's.

## 0.22.0

Additive: no migration, nothing to do in any office. On a terminal,
`office` is now your home screen, `office help` lists only your own verbs,
and the wizards stop asking you for what a session can work out. Every
verb takes the same flags as before and, piped, behaves as before.

The home screen. `office` on a terminal shows the office, the date and
time, its state and the install's lines as before, then each project the
office scopes on one line (what is in flight on it, or what last landed
and when), then what waits on you, each with a key: the next move first,
then a response in your downloads for a session that is out, a planner's
bundle in your downloads that no session has opened, each unsorted drop
and the sort, the desk moves a sitting decided, an office out of step
with the install, and a read-only sitting, which only you can say is
over. Keys for a new job, sending a session out, bringing one back, a
note, a drop, the desk and help are always there, and `q` leaves. A key
runs the verb's own code with its arguments filled in; when it ends, a
key brings the screen back. Sessions are named by their folders, never by
their ids, and responses and bundles are found in your downloads, so you
never type either. Whether a response has arrived is still bale's to say:
the file is offered, and `office land` asks bale. Whether a bundle was
opened is read from bale's records (a session's attempts carry the stem
of the bundle they came from), never guessed. Off a terminal, piped or
under a test or a session, `office` prints the page and ends with its
Next line, unchanged. The work is lib/office_home.py.

Bare `office start` on a terminal first offers the planner's bundles in
your downloads that no session has opened, newest first, one key each; a
plain return goes on to the jobs on the desk. A bundle saved more than
two weeks ago is not offered (`office start --bundle` still opens it).
bale's own search directories are on none of its --json surfaces, so the
office looks only in its own downloads setting.

Two surfaces of verbs. `office help` lists your own, one line each in
plain words, with what a folder and a project are: the home screen,
`note`, `drop`, `slip`, `open`, `start`, `land`, `desk`, `close`,
`deliver`, `projects add`, `tour` and `init`. The rest is the plumbing
the office and its sessions use, which a session names in full when it
needs you to run one; `office help --all` lists every verb as `office
help` did. share/verbs.toml gives each built script verb a `surface`
(`occupant` or `plumbing`), the catalog check holds every built script
verb to one, and the doctrine's verbs table has a surface column.

The wizards, under one rule: you supply the words, the session supplies
the structure. A verb asks you only for the ask in your words, which
project when the office cannot tell, yes or no on what cannot be undone,
and what only your eyes can check. Removed:

- `office open`: the title, size, lane and source. It asks for the job in
  your words; the first line is the title, the slug comes from it, the
  words go in the folder's Asked section and, as one line, are its goal;
  the size is small and the source the occupant (or the planner's bundle
  for `office start new` with a bundle, which asks nothing). It asks the
  project by key only when your words name none of the office's projects.
  A name another folder took today gets one of its own instead of asking
  for another title.
- `office start`: where the work lands (the folder's lane, or the
  bundle's own paths, said), the goal when the folder has one, the paths
  the session will change, which ride-alongs go this time, and whether to
  carry a rider the forecast touches (it is carried, said).
- `office start --drop`: the size (small); the project is asked by key
  only when the drop names none of the office's.
- `office land`: whether to close a finished folder (closed, said, with
  the line that reopens it; piped, still left open).
- `office slip`: what the slip is about (`--about` still says it).
- the clipboard command: this machine's own reader is taken and kept,
  asked only when there is none.

Choices the office can list are offered by key: the folder for close,
reopen, sessions, deliver and probe, the job for start, the session for
land and relay, the held response's copies in the downloads, the session
a probe is for, a blueprint, and a ratification's notepad page. Each
still takes the name or id typed out. notes.md of session
2026-10-15-home-screen-001 lists every question kept and removed, with
the reason.

One fix on the way: `office relay` asked for the planner's answer on a
terminal into a variable its own question shadowed, so the answer was
lost; every question's locals are now named so none can shadow the
caller's.

The fast tier, in the worker's two-core sandbox: 69.9 and 72.5 seconds
before, 62.8 and 64.8 after, 343 tests each time (the release adds no
test to the tier); with this release's own module beside it, as its
validation runs it, 73 to 77 seconds for 356 and 357. The whole suite,
825 tests, ran in about 1050 seconds there.

## 0.21.0

Additive: no migration, nothing to do in any office, and no verb gains a
flag or a question. The test suite waits less, and no test checks less;
and `office start` no longer sends a sitting out on a stale digest
without a word.

The suite's time was mostly Python compiling the office's own modules
again on every helper call: the command runs its Python with `-B`, so
nothing is ever written beside an install, and nothing compiled was ever
read back either. The runner now compiles `lib/` and `tests/` once per
run into a bytecode cache in its scratch directory and hands it to every
job (`PYTHONPYCACHEPREFIX`), each test's `Env` hands it to the commands
the test runs, and the command runs each of its Python modules as a
module, so even the one it starts with is read from the cache when there
is one. The cache is checked against each source's size and time as
always, nothing but the runner writes it, and it goes with the scratch
directory. In everyday use there is none, and the command behaves as
before.

The serial lane, the one job that runs its tests one after another,
holds only tests that drive a terminal. Seven classes held terminal tests
and others side by side; each is split in two, the terminal tests in a
class of their own named `...OnATerminal` that keeps `serial_group`, the
other 33 tests beside the other modules' jobs. Every test's body is as it
was.

The runner starts the longest jobs first when it knows the last run's
times: each job weighs the sum of its tests' times in the newest finished
detached run under the state directory (that run's `times.tsv`, kept
with its verdict). With none (a first run, a fresh HOME, bale's sandbox)
it runs as before. The run says which order it took in one line, and
`--plan` lists the jobs in that order. No job can read those times: each
has a state directory of its own, so the suite's rule against reading
the machine holds.

In the worker's two-core sandbox the fast tier went from 95 seconds to
about 67 with no earlier run's times and about 61 with them, the serial
lane from 85 tests in 956 seconds to 52 in 384, and the whole suite from
1712 seconds to 1051.

`office start` writes the digest before every sitting it sends out,
bundles included. A bundle named by a bare name is bale's to find (its
search, the downloads), so the office could not read its pack line, could
not tell a read-only sitting, and skipped the digest without saying so:
on 2026-10-13 a sitting went out on a page that predated three landings.
The office now reads the pack line where bale's rehearsal found the
bundle. When it cannot read a bundle's pack line at all, it says so in
one line, naming the digest it left and when that page was written.

## 0.20.1

Additive: no migration, nothing to do in any office, and no verb gains a
flag or a question. The test suite no longer touches the machine it runs
on.

On 2026-10-13 two session openers turned up on the occupant's clipboard
while he was not using the office. They were the suite's: the detached
run that `office land` starts after every landing ran two `office start`
tests on a terminal, and on WSL `office start` puts the opener on the
clipboard with `clip.exe` and opens the out tray with `explorer.exe`
whenever machine.toml names neither, which a test's own HOME never does.
(It started `explorer.exe` too; the test's terminal closed as the command
ended, which most likely stopped it before a window opened.) The same
detached runs failed on one test, and only there: the terminal test of
`office probe`'s paste question expected the clipboard reader the test
had put on the PATH, and the occupant's machine offered its own
`powershell.exe` first. Both came from the office reading the machine:
whether it is WSL (the kernel's version string) and which desktop
programs are on the PATH. Each now comes from one place the environment
can steer: `OFFICE_PROC_VERSION` names the file the WSL check reads, and
`OFFICE_DESKTOP_PATH` the directories the office searches for `clip.exe`,
`explorer.exe` and a clipboard reader. Unset, nothing changes, except
that the log names `clip.exe` and `explorer.exe` by the path they were
found at. The suite sets both for every test: the machine is not WSL, and
the only desktop programs are the ones a test puts in its own desktop
directory. The probe test keeps its assertion and now finds its reader
there. New terminal tests imitate the occupant's machine (WSL, with fake
`clip.exe`, `explorer.exe` and `powershell.exe` first on the PATH) and
show none of them runs, and, pointed at the fakes, that the same steps
reach them. `tests/test_suite_clock.py`'s rule now also fails a test file
that reads the kernel's version or looks a program up on the PATH, and
office source that does either except through those two doors.

## 0.20.0

Additive: no migration and nothing to do in any office. `office land`
brings back what every session's Sort says, `office moves` takes a sorted
drop to its folder, `office start N` sends a folder out with its own goal
and brief, the handbook arrives with the first fact a session gives, and
`office start --sort` sends the drops nothing carried to a session of
their own. A routine ask stays three steps: drop, start, land.

`office land`, after an applied landing and before the after-land
actions, files three more sections of the response's notes.md, after the
folder's two pages, each only when present and each said in a line; and
`office sessions FOLDER SID --pages RESPONSE` does the same
(`--in-tray SID` for the sort, which no folder records).

- `## Sort`: each `### NAME.md` subsection is filed on its page (in the
  in-tray, or the landed folder's drops/) as a `## Sort` section at the
  page's end: `- sorted: DATE, by SID`, then the subsection's fields
  verbatim and in its order, and `### Brief` exactly when it had `####
  Brief`. The page's status becomes `sorted` through
  `office_drop.set_status`, the status line's one writer. A page sorted
  already is said and left; a subsection naming a page that is nowhere,
  or one off the pinned format, is said and skipped. A Sort's `tell:`
  goes on the folder's Next when the page is in a folder.
- `## Questions and answers`: `- DATE question? answer` lines, appended
  to the folder's Questions and answers section after `- from SID:`.
- `## Handbook`: `### PROJECT` subsections of `- ` facts and an optional
  `#### Front sheet`; each fact is appended to the chapter's Facts as `-
  DATE: fact (SID)`, with a Sort's `facts:` lines, and a front sheet
  replaces the chapter's whole. A project none of the office's is said
  and skipped.
- notes.md is read fence-aware: a heading inside a fenced block is never
  a section.
- Then, when a sorted drop waits in the in-tray, or the session was the
  standalone sort and its moves page holds pending lines, land runs
  `office moves` and prints the folders it minted. A HOLD, a refusal or a
  clarification files nothing.

`office moves` applies the in-tray's sorted drops first, oldest first,
then the moves page. `folder: new` mints a folder through `office open`'s
code (title from the heading, slug from the page's name, lane the Sort's
project, size and goal the Sort's, source `drop`); `folder: N` takes
folder N on the desk. The page moves in whole, brief.md is written from
the Brief, the History gains `- DATE dropped: drops/NAME.md, sorted by
SID`, the goal is written when the folder has none, and the `tell:` goes
on its Next. A drop whose project does not resolve, whose folder is in
the filing cabinet or missing, or that an open session's forecast holds,
is said and stays, and the rest go on; the moves page's own one-writer
check and its stop-at-the-first-failure are as before. The walk-in counts
sorted drops waiting as pending desk moves, and `office desk` lists them.

`office open --goal TEXT` writes one more field line, `- goal: TEXT`,
after `source` (the folder template is untouched: the command writes it).
`office start N` offers a folder's goal (a return takes it, piped it is
taken, `--goal` overrides) and sends its brief.md as the session's brief
(`--brief` names another; a bundle keeps its own, said).

The handbook, `handbook/`, arrives with the first fact `office land`
files: handbook/README.md from the new templates/handbook-README.md, the
floor plan's entry as share/spaces.toml declares it (its front page
hung), and bale.toml's `handbook` trigger and `handbook/README.md` pull.
One chapter per project, `handbook/PROJECT.md`, from the reshaped
templates/handbook-chapter.md: `## Front sheet` for the occupant, `##
Facts` for sessions, appended and never rewritten by hand. A chapter
rides with every session whose lane names its project; `office status`
gains a `handbook:` line.

`office start --sort` is the standalone sort, the verb `sort` in
share/verbs.toml (an office session, built via start). It packs from the
office with the goal "Sort the in-tray's drops", the slug `in-tray-sort`
and a brief from the new templates/sort-brief.md (the standing
instructions, every unsorted drop between its DROP markers, the desk as
`office desk` prints it, and the Sort format); it ships every folder's
folder.md and the handbook, and forecasts the notepad and, with a drafting
table, drafting-table/moves.md (made from its template first when
missing). It belongs to no folder: the walk-in shows it in flight as the
in-tray's session, and `office land` finds it. Refused while another sort
is out, while an open session holds the in-tray, and with no drop
unsorted. The Next line names it, after the `--drop` rule, for an
unsorted drop whose project does not resolve once a session has been
recorded since it was dropped, and for three or more unsorted drops with
nothing ready; the `--drop` rule leaves such a drop to it.

The doctrine's core gains one bullet (ten lines): a session records its
light blocks and answers, and the facts it learns, in notes.md, reads the
chapter it carries before it asks, and `office land` files it all.
Sections 4, 5 and 7 say the rest, with the page's Sort section and the
chapter pinned as blocks the templates hold to the same bytes.

## 0.19.0

Additive: no migration and nothing to do in any office. A new verb,
`office drop`, and a new space, the in-tray, which arrives with the first
drop; every session `office start` sends out carries the unsorted drops;
and `office start --drop` sends a dropped message straight out as a
project session. A routine ask is three steps: drop, start, land.

`office drop [FILE | -] [--project TEXT]` captures a message or a thread,
instant and dumb, as one page, `in-tray/DATE-SLUG.md`, committed on its
own.

- The text comes from FILE, from stdin (`-`, or anything piped), or, on a
  terminal with neither, from the clipboard through machine.toml's
  `paste_command` (0.18.0's key, asked once). It says what it took: the
  first line and how many lines.
- It asks one question on a terminal, the project, as free text: the
  office's project names are offered as hints, any words are taken, and a
  plain return leaves it empty. `--project` is the flag twin. Piped, it
  asks nothing. It never refuses a drop it can write.
- The page: `# Drop: ` and the first line (trimmed to 60 characters),
  then `- dropped: DATE TIME`, `- project:` (the words as given, or `none
  given`), `- via:` (`clipboard`, `stdin` or `file NAME`), `- status:
  unsorted`, and `## Text` with the text verbatim. Line ends become LF,
  and anything outside ASCII is kept as a backslash escape, as a note
  keeps it. The slug is made from the first line the way `office slip`
  makes one, with a counter when the name is taken.
- Like `office note` it works in an unfounded office and in one behind
  or ahead of the install, and only warns.
- The in-tray arrives with the first drop, the way the drafting table
  arrives with the first verb that writes it: in-tray/README.md from the
  new template templates/in-tray-README.md, the floor plan's
  `[spaces.in-tray]` entry as share/spaces.toml declares it, and `in-tray`
  added to bale.toml's include-group triggers, all in the drop's own
  commit. It is neither hung nor filed. `office status` gains an
  `in-tray:` line that checks it against the catalog and every page
  against the shape.

`office start` carries every unsorted drop with every session it sends
out: in the pack's includes for an office session (a sitting included,
which reads them and owes no Sort), in the office's context tarball
beside the request for a project session (on a host too), and, for an
office session from a bundle, which the office adds nothing to, as
`context-in-tray.tar.gz` beside it. The out tray's listing says how many
ride and where, and the opener gains one line saying so. The goal is
unchanged.

`office start --drop PAGE` sends one drop straight out as a project
session. PAGE is the drop's page in the in-tray, by path or by name.

- It mints the folder through `office open`'s own code: the title from
  the drop's first line (`--title` overrides), the lane from the drop's
  project when that names one of the office's projects (otherwise asked
  on a terminal, `--lane` the twin, and refused by name when piped), the
  size asked with small as the default (`--size`), and the source `drop`.
  The folder's slug is the drop's.
- It moves the page, bytes as they are, into the folder as
  `drops/DATE-SLUG.md`, and the folder's History gains `- DATE dropped:
  drops/DATE-SLUG.md, via ...` before the `opened` line. `dropped` joins
  the closed set of History verbs and changes no status.
- It packs the session on the lane's project, on its host when it has
  one, with the goal "Sort the dropped message and do what it asks"
  (`--goal` overrides) and a brief from the new templates/drop-brief.md:
  the standing sort instructions, the drop's page between `--- DROP
  BEGIN ... ---` and `--- DROP END ---`, and the Sort format.
- It refuses, naming the session, while an open session in the office's
  registry forecasts the in-tray or the desk, and every other refusal
  comes before anything is written. When its session does not go out
  after the folder is minted, its last line retries it: `office start
  FOLDER --drop NAME`, which finds the page in the folder's drops/.
- A lane may now be the project alone (`alpha`), as `--drop` writes it:
  start, the desk and the Next line read it as that project with no
  paths.

The walk-in gains one line when the in-tray holds unsorted drops: how
many, and the oldest's age in days. `office desk` lists them after the
candidates, each with its project or `no project` and its first line.
The Next line gains one rule, after the pending desk moves and before an
unfounded office: the oldest unsorted drop whose project is one of the
office's, with no session in flight on a folder of that lane, gives
`office start --drop in-tray/PAGE`; the oldest whose project is none of
them, or has none, gives the same line with `--lane LANE` to fill. An
office with no projects skips it.

The doctrine's core gains the paragraph a build session reads (section
4's list): a session may carry drops, reads them before its work, and
sorts the ones it can judge in a `## Sort` section of its notes.md, one
`### DATE-SLUG.md` subsection per drop in a pinned format (project,
folder, goal, size, tell, facts, and a `#### Brief`). Section 5 gains
the in-tray's row and paragraph, section 7 the `drop` verb, `start`'s
carry and `--drop`, the walk-in's line and the Next rule. share/verbs.toml
declares `drop`. The drafting table's arrival helpers now take the space
they arrive, so the in-tray arrives through the same code.

Nothing reads a Sort section yet: `office land` filing it, `office moves`
minting the folders sorted drops ask for, and the standalone sort session
are the next release's.

## 0.18.0

Additive: no migration and nothing to do in any office. A new verb,
`office probe`; `office start` lets bale judge a bundle it would take as
a second desk; and bale 0.4.52's open --json lines are captured for the
suite.

`office probe FOLDER [FILE | -]` runs a worker's probe block where the
folder's project lives and hands the output back, so nobody opens a VPN,
an ssh and a docker exec by hand to paste a block into a container and
the output back out.

- The block comes from FILE, from stdin (`-`), or, given neither, from
  the clipboard, read with machine.toml's new `paste_command`. It sits
  beside `clipboard_command` and `downloads`, and is asked once on a
  terminal with this machine's likely command offered (on WSL,
  PowerShell's Get-Clipboard through powershell.exe). Piped, the verb
  refuses and names the key.
- The project is the folder's lane, or `--project NAME` (asked on a
  terminal when the lane names none; `office` is the office root). The
  session is the folder's recorded session open there; with several,
  the one the block's slug names, else `--sid`.
- A block with no PROBE BEGIN line, or whose purpose header does not
  say it is read-only, is refused by name and nothing runs. Otherwise
  the header is shown and the verb asks once, default no; `--yes` is
  the flag twin, and piped, nothing runs without it.
- The block runs with stdin closed, in the repo here, through the
  project's shell (its plain form, no terminal) on a host, or in the
  office root. One reach. Its output comes back whole; the lines from
  PROBE BEGIN to PROBE END go on the clipboard here with the office's
  own clipboard command, and the office says how many came back and
  whether the integrity trailer's count matches them.
- A `probe-output/` the run leaves (the file-based fallback) is carried
  to the session's out tray, `~/out-tray/SID/probe-output/`, and removed
  where it ran.
- The folder's History gains `- DATE probe: SID, N lines`: `probe` joins
  the closed set of History verbs and changes no status.

`office start --bundle` follows the ruling ratified with this release:
a second desk is bale's to recognize, and the office refuses an overlap
only where bale would. For a bundle the office can read, its own overlap
check still runs, and from bale 0.4.50 start asks `bale open --check
--json` (a new surface, `open_check_json`). bale's `rehearsal` key says
only which rehearsal ran ("check"), never which bundle opened a session,
so the office reads the outcome. "rehearsed" passes a bundle whose
session is still open: the office says what its check saw, prints
bale's own second-desk line, and goes on to join the desk as 0.17.2
does. "open-refused" stops it in the office's words with bale's reason
beside them. Below bale 0.4.50 nothing changes: the overlap is refused
before bale is asked.

The development record gains `fixtures/bale-0.4.52/`: 13 live bale
invocations from a fallback probe in a throwaway repo (open --check
--json fresh, on a second desk and refused for an overlap; open --json
opened and as desk 2 and desk 3; status; unlock), with
`format_open_json`'s docstring. The suite's fake bale replays these
lines for `open --json` and `open --check --json` in place of the lines
0.17.2 built from the docstring.

The doctrine names `office probe` in the front sheet's everyday verbs
and in the verb table, and the walk-in's `Suite:` line under the install
line.

## 0.17.2

Additive: no migration, nothing to do in any office, and no verb gains a
flag or a question. The doctrine reads core-first, `office start`
carries a bundle that bale takes as a second desk, and the walk-in says
when office-src's detached suite did not pass.

doctrine/OFFICE.md opens with a reading card at the top of its front
sheet: one row per kind of session the doctrine reaches (a build session
on a project, a work session in an office, the founding session, a
sitting, a session building office-src), each naming the sections it
reads. What a build session on a project reads (the card, the front
sheet, section 2, section 3, section 4 to the end of its list, and
section 9) sits above a PAST THE CORE banner: 199 of the doc's 1,079
lines, where a build session read all 1,044 before. Everything else sits
below the banner in number order: section 1, the rest of section 4,
sections 5 to 8, and 10 to 15. No section is renumbered and no sentence
changed. Section 4 sits in two places under its own number, and each
moved section leaves a one-line pointer where it was.
`tests/test_office.py`'s TestTheDoctrinesCore holds the shape.

`office start --bundle` still finds the session a bundle leaves open
from bale's registry: the open set before `bale open` against the open
set after. It now also handles the case where bale opens no session.
Since bale 0.4.44, a bundle whose session is still open is taken as a
second desk on that session: bale records the desk, prints that desk's
opener, and mints no sid. That is what happened on 2026-10-12. The
audience-line bundle had opened as 2026-10-08-audience-line-002 on
2026-10-08, and its browser copy went to `bale open` again while the
session was open. The office found nothing newly open and made no tray.

From bale 0.4.50 on, start runs `bale open --json`. Its line says
`opened` or `second-desk`, with the session id, the request tarball and
the opener, and start holds that line to the open-set diff. For a second
desk:

- the folder records the session with the words "a second desk on a
  session already open";
- the out tray carries that session's request;
- the opener printed is the desk's, and any other folder that records
  the session is named;
- the first line says Joined rather than Packed.

Below bale 0.4.50, a start that finds nothing newly open says a second
desk is the likely reason. `share/bale-consumption.toml` declares the
new surface, `open_json`, read from bale 0.4.52's key contract. No
session id is read from a date or from .bale/.

The walk-in shows one `Suite:` line when the latest detached run's
verdict is not OK. It does so only in an office that scopes office-src's
own source, the project the install came from, as the `Install:` line
already knows it. The verdict is `latest/verdict` under
`$XDG_STATE_HOME/office-src/suite/`, else `~/.local/state/office-src/suite/`:

- `FAILED` and `BROKEN` are said as written;
- `RUNNING` is said once it is more than an hour old, with its log;
- a verdict in no shape the runner writes is said as such;
- no run yet, or `OK`, prints nothing.

Nothing else on the walk-in moves, the Next line included.

## 0.17.1

Additive: no migration, nothing to do in any office, and no verb
changed. The suite's clock: validation fits bale's two minutes, the whole
suite runs where nobody waits for it, and no test reads the machine it
runs on.

`tests/run.sh --fast [NAME]...` runs the fast tier, defined once in
`tests/fast-tier.toml`: for every verb `bin/office`'s dispatcher knows,
and the walk-in, one test that runs it, then every test that costs under
half a second, the suite's own rules and the runner's tests; 280 of the
suite's 679 tests. A module, class or test named after `--fast` is added
(a session adds what it touched). The runner holds the tier to the suite
before anything runs, as it holds the whole plan to `unittest discover`:
a name the suite does not have, or a verb with no entry point, stops it
with exit 2. It prints the tier's wall time and exits 1 past its budget,
`budget_seconds = 120`.

`tests/run.sh --detach` copies the tree, starts the whole suite in a
session of its own at a lower priority, with SIGINT restored for the
interrupt tests, and returns at once with one line naming the run's
verdict file under `$XDG_STATE_HOME/office-src/suite/` (by default
`~/.local/state/office-src/suite/`), outside the repo. The verdict is one
line, `RUNNING since ...` until the run ends, then `OK`, `FAILED` or
`BROKEN` with the count, the seconds, the commit tested and, when it
failed, the log to read; `latest` names the newest run and the ten newest
are kept. Meant as office-src's after-land action:
`office projects set office-src --after-land ./install.sh --after-land
"tests/run.sh --detach"` (the flag replaces the list, so name every
action).

Every job of a run, and `--serial`, gets a HOME, TMPDIR and XDG
directories of its own under a scratch directory the runner removes, an
empty git config, no Windows users' homes to scan and none of the
caller's `OFFICE_` settings. Each job's result carries each test's time,
and the run writes them, slowest first, to `times.tsv` beside its logs.

Env, the suite's scratch HOME, gives each test its own TMPDIR
(`self.e.tmpdir`) and downloads (`self.e.downloads`) besides HOME and
XDG_CONFIG_HOME, and `this_process()` lends its environment to a helper
called in-process. The tests that globbed the machine's temporary
directory for what deliver leaves, expanded `~` against the machine's
HOME, named the machine's temporary directory as a path, or committed
under the machine's git identity, now use their Env's, asserting what
they asserted. `tests/test_suite_clock.py` fails the suite on a test file
that names the machine's temporary directory, `expanduser`, `Path.home(`
or `$HOME` outside Env, save the few lines its ALLOWED list names with
their reasons.

The runner's plan test parsed every test file once per test in the
suite; it reads them once, and went from about two minutes to a second.

## 0.17.0

Additive: no migration, nothing to do in any office. The audience line:
a folder's landed work crosses from the project's workbench clone to the
audience's git host as curated commits, and the letterhead becomes a
check rather than a rule on paper.

Three declarations on the projects table, set by `office projects add`
and `set` (the wizard asks them after the host, defaults read from the
clone; `--audience REMOTE`, `--author "Name <email>"`, `--base BRANCH`,
and `--no-audience`, `--no-author`, `--no-base`), shown by `office
projects`: `audience`, the remote in the workbench clone that points at
the audience's git host (checked against the clone's remotes; a project
with none leaves it unset, and deliver refuses it by name); `author`,
the identity the audience expects on the commits (unset, the clone's own
identity, read where the clone is at each delivery); `base`, the audience
branch deliveries branch from (unset, the audience remote's HEAD branch,
read from the clone).

The push guard. Declaring an audience writes a pre-push hook into the
clone's `.git/hooks`, outside what git tracks; `office deliver` installs
it when it is missing. It refuses any push to the audience from the
clone, by the remote's name or its URL, naming `office deliver`; a push
deliver makes names its branch in `OFFICE_DELIVERY`, and the guard lets
that branch alone through. A clone with `core.hooksPath` set or another
pre-push hook is said and left alone.

`office letterhead check [PATH | --on PROJECT] [--all] [--range A..B]
[--words FILE]...`: every line that holds what the letterhead refuses,
as `file:line: what`, exit 1 with a hit, 0 clean; `OFFICE_DEBUG=1` names
every file read. The list is one file in the install,
share/letterhead.toml: model, vendor and product names (each written
with one letter bracketed, so the list never spells what it refuses);
tell-tale phrasing an assistant writes (the suite's four fingerprints
and a dozen more); bale's marks (`[bale `, `Merge bale `, `applied/`,
`bale sweep`, `bale/` as a ref, a session id); and, when the office has
`letterhead/forbidden.txt`, each non-blank, non-comment line of it as a
fixed string (read if it exists, never written). The suite's text rules
read the names and the phrasing from the same file; the brief's names
stay the suite's own. Scope: a range's changed files at B and its commit
messages; else the files a dirty tree changed; else the whole tree with
`--all` or outside a git repo, said so; `--words FILE` as text. Binary
files are skipped by name and by a NUL byte. On a hosted project the
check travels through the shell as python3's program on stdin, writing
nothing there (lib/office_letterhead.py imports nothing of the office).

`office deliver FOLDER [--on PROJECT] [--branch NAME] [--others-too]
[--yes]`, the crossing, each step logged: the project is the folder's
lane's and declares an audience, the folder records an applied session,
a hosted project is reached first; the audience's base is fetched (and
the delivery branch, when an earlier delivery made it: a second delivery
for the same folder adds to it); the landed work since the last delivery
(else since the branch and the base parted) is read and every applied
session in it named by id and folder, sessions of other folders said and
named, with a question on a terminal and `--others-too` piped; the words
come from `desk/FOLDER/delivery.md` (missing, deliver stops and says what
to write where); in a temporary worktree at the audience's tip the work
is squashed on, bale's names taken out of the index, and the diff and the
words go through the letterhead check (one hit refuses, nothing pushed);
the diff's stat, the sessions, the author, the branch (the folder's slug,
or `--branch`) and the words are shown and deliver asks once (`--yes`;
piped, it refuses without it); the words become one commit (several when
delivery.md marks them with `paths:` lines) as the author, and that
commit alone is pushed as the delivery branch, never the workbench
branch; the folder's History gains a dated `delivered` line (branch,
audience, sessions, workbench commit, delivery commit), and the review's
URL is printed where the git host's compare-URL shape is known (GitHub,
github.* and GitLab hosts, the review's title and body in it; on WSL, on
the clipboard), the branch's name otherwise, and whom to send it to when
the words name a reviewer. The push path, pinned by the probe: the
delivery is built and pushed from this machine, where the audience
answers with the occupant's credentials; for a project on a host the
landed commits come here as a thin git bundle through the project's
shell into a temporary bare repo removed after (three connections), and
nothing is left on the host outside the repo. A push from the host is
the known gap. The suite proves it against a bare repo standing in for
the audience: no bale commit, merge, tag, branch, mark or excluded file
on what a delivery pushes.

The folder's two pages. templates/folder.md gains a Walkthrough and a
Delivery section pointing at walkthrough.md and delivery.md in the
folder, from two new templates that ride beside every build session's
request; a build session writes both as the Walkthrough and Delivery
sections at the end of its notes.md, and `office land` files them in the
folder after an applied landing of a project session, when it found the
response on this machine (naming `office sessions FOLDER SID --pages
RESPONSE`, new, when only bale's search knew where it was). The build
verb in share/verbs.toml lands the two pages and ships the templates.
OFFICE.md's principle 6 names both pages; a `delivered` History verb is
added. Existing folders are not rewritten.

`office relay SID [ANSWER-FILE]`, 0.16.0's proposal: carries a planner's
answer to a clarification back to the session's repo as `bale relay SID
-` there, the answer on its stdin through the project's shell for a
hosted project, and finds a bare name here and then in the downloads;
the block bale prints for the worker is printed whole and, on WSL, put
on the clipboard. share/bale-consumption.toml declares the stdin form.

Also: `tests/test_audience_line.py`; the suite's `response_tarball`
takes a notes.md; `office start`'s bundle test expects the templates'
tarball in the tray.

## 0.16.0

Additive: no migration, nothing to do in any office. The return trip from
a host: a session sent to a project on a host comes back with `office
land`, so a hosted project's whole loop runs through `office start` and
`office land`.

`office land` on a hosted project. land checks first that the host
answers: a host that does not stops land before anything is carried,
with the connect line and the line that reruns it (`far's host did not
answer, so it may be out there: ...`). The response is found on this
machine (below), carried into one temporary directory on the host made
in the same connection, checked by sha256, and `bale apply` (or `bale
retry` for a held session) runs in the project's repo there through
`Reader.interact`'s attended form, so bale's questions reach the occupant
and only he answers them; the same command removes the directory once
bale exits, and land removes it after when bale did not finish. How it
ended is read from bale's records there. The relay is printed whole and,
on WSL, put on this machine's clipboard. A clarification's block comes
from `bale relay` run there, in the same connection as the dossier, and
its Next line is one line typed here that pipes the planner's answer to
`bale relay SID -` there. The project's after-land actions run in its
repo there, one connection each, attended on a terminal; a failing one
names the line that reruns it from here. The ratification, the watches
check and the last lines follow as for a local landing. A read-only
sitting there ends with `bale unlock` there. `land_plan` carries the
place (path, host, shell, connect) instead of `repo`, and a display
`where`. Nothing land writes on the host outside the repo is left
behind, on success or failure, and the suite proves it with a fake host
that keeps its own HOME, PATH and TMPDIR.

Where downloads land: machine.toml's `downloads`, a list of directories,
the office's own setting (it never reads bale's config). Asked once on a
terminal the first time a verb needs it, offering this machine's likely
directories (each Windows user's Downloads on WSL, the XDG download
directory, ~/Downloads; `OFFICE_WINDOWS_USERS` names another root for the
Windows homes, or none when empty, which the suite sets so no test
depends on the machine it runs on), `?` explaining it; piped, the verb refuses and
names the key; never asked again. A hosted land finds the response there
by name, the newest of a browser's copies (`response-SID (1).tar.gz`)
winning and named; a path given overrides, and a name given is looked for
in the current directory and then the downloads. After a HOLD with one
copy only, land asks for the corrected one, offering that copy (piped, it
names it). A local land behaves as before unless the downloads hold
several copies of the response's name: then bale gets the newest by its
path, and land says so. `office start` on a hosted project accepts a bare
bundle name again, found the same way (0.15.0 refused it). Two copies
saved at the same moment refuse, naming both.

land offers to close a finished folder. After an applied landing, when
the folder records that session alone and the planner ratified it with
no exception, land offers to close the folder, done, right after the
ratification, default close; `--close` and `--leave-open` are the flag
twins; piped with neither, the folder stays open and land says so. Local
and hosted alike; the founding folder keeps its own rule.

Fewer connections. The reach carries across the reader processes of one
office command (bin/office names a file in `OFFICE_REACHED_FILE`; each
prefix that answered is appended, and the next process reads it), and
the reads a step needs share a connection: start-check's version, status
and repo check; the pack's status, paths and doctrine sums; a bundle's
status and paths; a new temporary directory and the file sent into it;
the directory's removal with the step that used it; open's status after
the open; land's status and dossier, and the outcome's dossier and
relay. In the suite's count a hosted start went from 7 connections to 4
(a brief: 10 to 5; a bundle: 18 to 8), and a hosted land takes 4 plus one
per after-land action. A host that stops answering after its reach was
carried says so in the reach's own line (ssh's exit 255), not as a
refused command.

A home-relative hosted path (`~/x`, which `office projects add` takes for
a host) keeps its meaning through the shell: the office's `cd` and the
repo check expand it as `"$HOME"/x` on the far side, where a quoted `~`
named a directory called `~`.

Two riders. README's Tests section says to run the suite in the
foreground, and `tests/runner.py` warns at the start of a run whose
SIGINT is ignored, naming the terminal tests whose interrupt checks then
fail.

## 0.15.0

Additive: no migration, nothing to do in any office. The out trip to a
host: a session sent to a project on a host. Bringing one back over the
shell is the next release's.

`office start` on a hosted project. A project on a host is packed on its
host, where its bale is and where the session will land; the occupant
sees what a project here shows: the survey, the riders, the ride-alongs
question, the overlap refusal in the office's words, the session
recorded in the folder, and one out tray on this machine with the
request, the doctrine, the office's context and each ride-along, the
opener printed (and on the clipboard on WSL). Before anything is
written, start checks the host once (`reader start-check`): a host that
does not answer stops it with the connect line; a bale below the read
side's floor is refused, naming `office projects level-bale NAME`; the
repo there must be one bale runs in. bale's pack runs through the
project's shell, a `--brief` sent there first, and the request bale
makes is carried back into the tray, checked by its sha256 on both
sides. The office's context, the doctrine and the ride-alongs are made
here, as before. For a bundle, the file travels to the host and `bale
open --check` runs there on that copy before anything is written, then
`bale open`; a bundle for a hosted project is given as a file here, since
bale's search for a bare name would run on the host. Where a bundle's
paths decide where it opens (0.9.0), a hosted project answers through
its shell. The doctrine a hosted tree carries is compared with the
install's by sha256 through the shell. The one temporary directory the
office makes on a host is removed on success and on failure, and the
suite checks it. `office land` on a hosted project still refuses, now
saying "the return trip is not built yet; the session is out and its
response waits".

The attended transport. A bale step the occupant answers runs through
the attended form of the project's shell, derived from the stored
`shell` (no new key): `ssh -tt`, and a container layer's `-i` after the
ssh target becomes `-it` (`--interactive` gains `--tty`), with the
terminal as stdin; `Reader.interact` goes through it, and piped it runs
the plain form with stdin closed, so nothing ever asks. Its capture is
read with CR LF turned to LF.

A clone moved to its host. `office projects add NAME --host TARGET
--path PATH --from CLONE` (on a terminal, asked after the host question,
default none, `?` explains) makes a clone of CLONE at PATH on the host:
every branch and tag, the remote-tracking refs and the symbolic remote
HEADs, the remote and branch config as CLONE has it, HEAD as CLONE's,
carried from this machine as a `git bundle` through the shell (the host
need not reach the audience's git host), checked ref by ref, then
prepared as `--prepare` prepares a clone. PATH must not exist there:
refused before anything moves. Only what is committed travels: a CLONE
with working-tree changes is named, with its changed paths, and add asks
whether to go on (piped, refused unless `--from-dirty-ok`). A shallow
clone is refused. A clone that does not come out level is removed again.
CLONE is never changed or deleted; add says it can be removed once the
occupant is satisfied.

A host's bale brought level. `office projects level-bale NAME` installs
on a hosted project's host the bale this machine runs, the way bale's
releases install: a release-shaped tarball of this machine's install
(`user/`, dot-entries such as `.git` and `.bale`, and caches left out)
carried through the shell, and the host's own `upgrade.sh -y` run on it,
which keeps the host's `<install>/user/` (its global `bale.toml` and
hook store), replaces the rest and runs `install.sh` and `validate.sh`;
a host with no bale on its login PATH gets `~/bale` and its `install.sh
-y`. Nothing is fetched from the network there. It says what was there
and what is there now, reads the version and the `user/` names again
afterwards, refuses a host whose bale is newer, and asks first on a
terminal (`--yes` piped). `office status`'s line for a host behind the
floor now names this step, and a host within range but behind this
machine says so too.

`tests/run.sh` prints each failing test's traceback in its own summary
(its last 40 lines), from the job's result, so a summary carries what a
failure said even when its log under the temp directory is gone.

## 0.14.0

Additive: no migration, nothing to do in any office. A project on
another host: the first half of "a project on another machine". The
office reads and reaches such a project; sending a session to it and
bringing one back is the next release's.

A project declares its host. Three keys on the floor plan's [projects]
entry, written by `office projects add` and `office projects set`
(wizard on a terminal, flag twins) and shown by `office projects`, never
by hand: `host`, an ssh target (user@host, or an ssh-config alias; absent
means the repo is on this machine, as every project was), `shell`, the
command prefix that runs one command where the repo is (default `ssh
HOST bash -lc`, a deviation from the brief's `ssh HOST` to ratify: the
office appends exactly one shell-quoted command, which only lands intact
on the far side through a word that takes a command string, and a login
shell is what finds a bale installed under the user's home; through a
container, something like `ssh HOST docker exec -i -u USER NAME bash
-lc`), and `connect`, the occupant's own words for what brings the host
up (default `connect to HOST`). A hosted project's path is the path as
that shell sees it. The wizard asks, after the path, whether the repo is
on this machine or on a host (a plain return: this machine), then the
shell and the connect line with their defaults shown; `set` offers to
keep them, and `--on-this-machine` takes a project off its host. Piped,
`--host`, `--shell` and `--connect` are the only way.

Reach. Before any step that needs the host, one connection with a short
timeout (ssh's BatchMode and a 5-second connect timeout on every call
the office makes; the first batch of reads a command sends through a
prefix is that check, so an answering host costs no extra connection).
A host that does not answer is one line naming the project, the host,
why, the connect text and the exact command to rerun, and the command
stops there; the walk-in and `office status` print the line in the
project's place and render the rest, and never hang. A host checked
once in a command is not checked again in it.

The read side through the shell. Everything `lib/office_bale.py` reads
from bale's `--json` surfaces, and the commit subjects the digest reads,
runs for a hosted project through its shell in its path, with the same
keys and the same consumption manifest: the walk-in's In flight, `office
sessions FOLDER`, `office projects --ledger / --landed / --versions`,
`office watches check` and the digest all read a hosted project. Each
round of reads travels as one batch in one connection (a status, then
every open session's dossier; an aggregate and a status, then every
class and every dossier), so the walk-in makes two connections per
hosted project and a rendering two or three; `OFFICE_DEBUG=1` shows
every shell call as it shows every bale call. The new module
`lib/office_host.py` holds the seam: the keys, the shell, the reach,
the batch, and the check and the preparing of a clone.

`office status` gets a line per hosted project: whether the host
answers, and that host's bale against the read side's floor
(share/bale-consumption.toml, 0.4.45), with the remedy when it is
behind ("bale X on HOST is older than the read side's floor Y; bring it
up before a session is sent there"). The office's own bale line stays
as it was, and the survey still makes no network call.

Preparing a clone for bale without a trace. `office projects add NAME
PATH` on a git repo bale has not run in offers, on a terminal, to
prepare it (flag twin `--prepare`; piped, it refuses as before and
names the flag): the four paths bale makes (`.bale/`, `bale.toml`,
`.baleignore` and bale's record directory) go into the repo's
`.git/info/exclude`, each once, and an empty, comment-only `bale.toml`
is written for `bale config init` to fill; afterwards the project is on
the table, `git status` is clean, `git ls-files` unchanged, and the
repo's own `.gitignore` untouched. Through a shell, the same outcome.
The doctrine line: what the office writes into a project's working copy
is only ever outside what git tracks.

Until the next release lands, `office start` on a hosted project
refuses before anything is written (at `--on`, and in the where
question, which names the project and asks again), and `office land`
refuses to land a session, or end a sitting, on one.

`office init` hands each project path to add's wizard, which asks where
it is; the helper runs with `-B` as the reader does, since it now
imports office_host. The suite runs no real ssh: a fake `ssh` first on
the PATH asserts the target and the prefix it was handed and runs the
one command locally against a throwaway repo, so the read side's fake
bale answers through it (tests/test_project_on_host.py).

## 0.13.0

Additive: no migration, nothing to do in any office. The third trip:
small pieces around sending a session out and bringing one back.

`office start` asks bale first. For a planner's bundle, start runs `bale
open --check` where the bundle opens before it writes anything (a folder
for `new`, the survey, the out tray, the session): bale finds a bare
name through its own search, runs every gate it runs before an open and
writes nothing, so a name it cannot find, a forecast path that is not
there or a forecast an open session holds stops the start in bale's
words with nothing written. A bundle the office can read is still
refused in the office's own words first. With `new` and a bundle, where
the work lands is asked before the folder is opened, and a project's
bundle is checked before it. When start opened a folder itself and its
session then does not go out, the folder stays and start's last lines
name it and the one line that retries it with the answers given. `office
open` (and `new` through it) checks the title first: a folder already on
the desk is offered to `office start new` as the one to start, and a
plain `office open` asks for another title at once, before size, lane or
source.

`office start` offers the riders the pack carries: the queued riders on
the riders page whose glob its forecast touches (`office riders
--forecast`), offered one by one on a terminal (default: carry), carried
into the folder's Riders section before the pack so they ride in the
request; piped, none is carried and each is named with `--carry N`.
`--carry none` carries none. A rider's glob may name its project first
(`office-src: bin/`), and then only a pack on that project carries it;
`office riders --forecast ... --project NAME` reads it so.

`office land`, after an applied landing, runs `office watches check`
without recording and prints the watches that fired (nothing for an
office with no register; it never fails a landing), and closes the
founding folder, done, when the founding session landed with the profile
complete, saying so (a profile still incomplete leaves it open).

The walk-in names an install behind its source: when the office scopes
the project the install came from and that project's HEAD is not the
installed commit, the header says so in `office status`'s words, and the
Next line names `(cd SOURCE && ./install.sh)`, right after the cases of
an office out of step with the install and before a session out, since
start and land run the install (an order change, to ratify; the
doctrine's Next-line paragraph says it).

A profile question on a terminal takes a paragraph: each line as typed,
a blank line ending it, a blank first line skipping it.

The suite runs side by side: `tests/run.sh` (and the response's
validation) runs each module as its own process, four at a time, the
terminal-driven classes serial in a lane of their own, one log per job;
`--serial` runs it as one process.

bale 0.4.47 checked against the consumption manifest: nothing the office
reads moved, so the 0.4.45 floor and its captures stand; the manifest
says which bale was checked, declares `open --check`, and notes unlock's
new refusal line.

## 0.12.0

Additive: no migration, nothing to do in any office. An office founded
before keeps its profile; one still unfounded gets `office found` on its
Next line. Every older office shape keeps working, and a migration
without the new `writes` key forecasts what a renovation always did.

The founding door: an office comes to exist, and is renovated, through
the door every other session uses.

`office init`, after the skeleton, the first commit, the default and the
projects question, asks the profile's questions: one per section of
`share/profile-shape.toml`, in its order, each worded from the section's
asks line, with `?` explaining what a good answer holds and a plain
return leaving the section for the founding session to ask about. The
Founding section is never asked. Each question has a flag twin
(`--purpose`, `--not-for`, `--audiences`, `--site`, `--house-rules`,
`--when-to-open`, `--spaces`, taken from the shape's new `flag` keys), so a
piped init asks nothing and sends what it was given. The timezone is
asked with Site (`--timezone ZONE`), as the zone the occupant lives in,
defaulting to the machine's when that resolves (TZ, then /etc/timezone,
then /etc/localtime), checked against the zone database with the remedy
named for a zone that does not resolve, and written to the floor plan,
committed alone, when it resolves. Init then opens the founding folder
(founding, source office init, class meta, size small), keeps the answers
in it as `answers.md`, and sends the founding session out through `office
start`, forecasting the folder, the notepad, profile.md and the floor
plan, with a brief carrying the answers verbatim, the sections left to
ask, the timezone and whether it resolved, and the survey's facts. The
printed `bale pack` line is gone, and with it the `(cd INSTALL/doctrine &&
bale pack --context)` that wrote an outbox into the install: the doctrine
rides from the out tray. `--no-founding` builds only.

`office found` is the same door for an office that exists and is
unfounded: it keeps the answers a founding folder holds and asks only for
the rest. `office start` on the founding folder of an unfounded office
goes through it. The Next line of an unfounded office names `office start
FOLDER` for its founding folder, or `office found` when there is none.

`office upgrade`, stopped at a renovation, opens a folder for it
(`upgrade-VERSION`, source office upgrade) and sends the renovation
session out through `office start`, with the migration's goal and a brief
carrying its summary, its `[landed]` declaration in full and its version.
It forecasts the whole office, as the printed line did, unless the
migration declares `writes` (a new optional key). A renovation session
already out is named, never sent twice; `office land` brings it back
while the office is behind (and nothing else), and the Next line names
that landing before `office upgrade`.

## 0.11.0

Additive: no migration, nothing to do in any office. An office that has
no drafting table gets one the first time `office digest` runs, which
`office start` does before it packs a sitting, the same way any verb
that writes the drafting table brings it (0.10.0). Every older office
shape keeps working.

The second and last half of blueprint session 4b: the watches, bale's
stats surface narrowed to a window, and the digest a sitting opens on.

`share/watch-queries.toml`, the watch-query catalog, written from a probe
of the installed bale 0.4.45's `stats --json` and its `--since DATE`
form, in office-src, home-office and every project home-office scopes.
It names each of the seven queries of the blueprint's section 3.2 once:
the surface it reads, the value it extracts, how it compares. Two, the
HOLD cause class (watch 15) and the amendment-accept marker (watch 17),
name the datum bale does not stamp, and are never evaluated. Every key a
query names is declared in the consumption manifest and read through
the reader's one door for catalog keys.

`office watches [--all]` lists the watches on the drafting table's
register with their state, read from the watch log. `office watches
check` runs each open query watch over the window since its last fired
record (from the day after it: bale's `--since` takes a day), once for
the office's own registry and once for each project, and prints fired,
not fired or cannot evaluate per watch and place; every eye watch as
needs an eye with the sittings since its last record; and the standing
lines, claim basis and HOLD rate per work class, as observed. A query
bale cannot answer prints "cannot evaluate: bale does not stamp ...
(slip)", never not fired. `--record` appends a fired record per watch
that fired, after the one-writer rule and the filed-page check, and
commits the log alone.

`office digest` writes `drafting-table/digest.md` and prints it:
versions per project, what happened since the last sitting (from bale's
records and git: the sessions applied, held, bailed and still open, the
folders opened and closed, what was added to the drafting table), the
watches, the standing lines, the desk, the agenda and the open
blueprints. The last sitting is the latest sitting's page in the
notepad, by the commit that filed it, and the page says so. `office
start` runs it just before it packs a sitting (a read-only office
session) and ships the drafting table with it, the way it surveys the
machine before every pack: its own commit, never fatal.

The walk-in's Next line changed order: pending desk moves now come after
a session out and before an unfounded office (`office moves`), so the
line never names a folder a move is about to retire. The 0.8.0 order
was ratified; this step is the plan-4b sitting's, ratified the same way.

The consumption manifest declares `stats`'s `--since` flag and the keys
the catalog reads, and the subjects bale gives the commits it makes
(`[bale SID] ...`, `Merge bale SID`, `[bale sweep SID] ...`), which the
office reads to name the session that wrote a line and to find the
sessions that closed since a sitting. `digest`, `watches` and
`watches-check` are built verbs in `share/verbs.toml`. The probe's
captures join the development record's fixtures.

## 0.10.0

Additive: no migration, nothing to do in any office. The drafting table
is not base and no migration brings it: it arrives in an office the
first time a verb writes it, and an office without one keeps working as
before. Every older office shape keeps working.

The first half of blueprint session 4b: the drafting table's pages
arriving in an office, and the verbs that write and read them.

The drafting table arrives with the first verb that writes it (`office
blueprint open`, `office rider add`, `office agenda add`, or `office
moves` once a sitting wrote the moves page). That verb writes
`drafting-table/README.md` from the install's template, adds the space
to the floor plan as `share/spaces.toml` declares it (so `office status`
and `office upgrade` read its filed list), adds it to bale.toml's
include-group triggers, and makes each page from its template on the
page's first write, all committed with the write that asked for it.
Nothing already there is ever rewritten. `office status` checks a
drafting table that exists against the catalog.

`office moves` applies the desk moves a sitting wrote on
`drafting-table/moves.md`: open a folder, queue a candidate (the one
move nothing else made), gate a folder, or close, absorb, split or retire
one. It runs every pending line in order through the same code as
`office open`, `office close` and the gate flags, ticks each with the
folder it acted on, writes an opened folder's number onto its
blueprint's decomposition line, and commits once. A line that does not
read is named before anything is applied; a line that cannot be applied
stops the run there, with the earlier ones committed. `--dry-run` lists
them.

`office blueprint open`, `ratify` and `close`. Open drafts a blueprint
from the template. Ratify writes the charter's ratified line (`--words
notepad/PAGE` or `--sid SID`) and refuses an empty charter. `office
status` checks every ratified charter's bytes against git from its
ratifying commit on. Close sends out the sitting that closes an arc
through `office start`'s own code, recorded in a folder born for the
close, with the blueprint, its member folders, the ledgers and the close
report's template (from the install) shipped, and the drafting table and
the notepad forecast. Nobody copies a pack line.

`office rider add`, `carry` and `consumed`, and `office riders`
(`--orphans`, `--forecast PATH...`). A rider is on the riders page or in
one folder's Riders section, never both, and its numbers count the page
and every folder. `office agenda add` puts a question on the agenda for
a sitting. `office rulings [ID] [--check]` and `office evidence [N]` read
the ledgers; `--check` resolves every citation on the drafting table and
the desk through the one resolver the desk's gates use.

The desk reads its last gates: a blueprint gate is met when the
blueprint's close report exists, an agenda gate when a sitting disposed
of the item, and a ruling gate when the ruling is on the ledger; one
naming nothing is an error line. Its last two groups are the riders
orphaned in a closed folder and the pending desk moves. The walk-in
says how many moves are pending and which session wrote them (from the
`[bale SID]` commit that wrote each line). `office desk --blueprint ID`
shows one arc's folders in the desk's order.

The one-writer rule now holds every script that mints a number or adds
to a page: moves, rider add, carry and consumed, agenda add, blueprint
open and ratify. Each refuses while a session open in the office's own
registry forecasts what it writes, and names it. The riders page and the
agenda are checked against their committed bytes before each commit.

`office slip` titles and names a slip lifted from a numbered Markdown
list by its words: a leading list marker and emphasis markers are taken
out of the title and the slug, never out of the text.

A real office's own registry, captured by this session's probe, joins
the development record's fixtures, and the one-writer tests read it.

## 0.9.0

Additive: no migration, nothing to do in any office. Every older office
shape keeps working: a project without ride-alongs or after-land actions
starts and lands as before, and an office whose zone resolves walks in
as before.

The second trip: the five frictions the first real round trip through
`office start` and `office land` found, and an answer to why the install
did not move when 0.8.0 landed.

`office start` shows, on a terminal, what rides with the project and the
size of each, and asks which ride with this session: a plain return
rides them all, as declared; `none`, or the numbers to leave out, keep
them home this once and change no declaration. `--leave-out PATH`
(repeatable) and `--no-rides` are the flag twins, and a bundle takes
them too; piped, everything declared rides. The doctrine rides once: a
project whose packed tree carries the same `doctrine/` (office-src's
own) reads it there, and the tray's listing says so; one whose tree
carries a different `doctrine/` gets the install's beside it, as
`context-doctrine-install.tar.gz`, named as the doctrine the office runs
on, so a worker sees which one the office actually runs.

`office start` surveys the machine again before every pack and commits
the page alone (`office start: survey: N facts changed`), so the survey
a session reads first is never older than the session. While an open
session's forecast holds the page (the one-writer rule), or when the
survey cannot run, start leaves it as it is and says how old it is.
`office status` names the survey's age and the office-src version it
records beside the installed one.

`office land SID` on a read-only sitting the office sent out ends it:
`bale unlock SID --json` in the sitting's repo (bale asks nothing, infers
`closed-read-only` from the empty scope, and commits its telemetry
record alone), then an `ended` line in the folder's History, committed
alone. The folder keeps its status: closing it is the occupant's. Land
never picks a sitting by itself, and a read-only session no folder
records is not the office's to end. The walk-in's In flight line for a
sitting says `office land SID` ends it when the sitting is over; the
Next line never names one.

`office start` with a bundle the office can read defaults the where
question to the one place whose tree holds every path the bundle's pack
line names (the office, or one of its projects; when several do, the
lane's project, else the office), and the question's help says why. A
bundle whose paths no one place holds, or that is sent where its paths
are not, is refused before bale runs, naming each path and where it is.

A floor plan's timezone that does not resolve is named with its remedy:
the warning every verb prints, a `timezone:` problem line in `office
status`, and the walk-in's header, which says it is on UTC and why. The
remedy is the canonical spelling when the zone database holds one by the
zone's last name (`America/Indiana/Indianapolis` for
`America/Indianapolis`), and the package that keeps the legacy names
(`tzdata-legacy` on Debian and Ubuntu) otherwise. `TZDIR` names another
zone database, as for the C library.

`office land` ends with what became of each after-land action (ran,
failed, not run, with the line that reruns from the failed one), after
the ratification, so the outcome of an install is the last thing on the
screen; a project with no after-land action is said so rather than
passed over. 0.7.0 and 0.8.0 ran an empty action for such a project and
said "1 action(s) ran"; that is gone. `office status` gains a `source:`
line comparing the install with the working copy it was installed from
(install.sh's INSTALLED stamp): an install that is not the source's HEAD
says BEHIND, with the line that brings it level. One exit code changes:
a landing whose project declarations do not read now exits 1 (the session
landed, its actions did not run), as a failing action already did. Why
0.8.0's install did
not move: it was applied by hand with `bale apply`, which runs no
after-land action; nothing in the office failed.

## 0.8.0

Additive: no migration, nothing to do in any office. Every older office
shape keeps working; an office with no projects, no calendar or an empty
suggestion box walks in the same way, with one more line at the end.

The front door. Walking in now ends with one Next line: the one command
to type now, its arguments filled in, worked out from the office on
every walk-in and never written down. In the order they win: an office
out of step with the install (`office upgrade`), a session out (`office
land SID`; when bale held it, land asks for the corrected response), an
unfounded office (`office status` names what the profile lacks), the
first ready folder (`office start FOLDER`, with `--on PROJECT` when its
lane names one), an open folder no session is out for, no projects
(`office projects add`), five or more slips (a folder to triage them),
folders that only wait (`office desk`), and nothing to do (`office
open`). Whether a session's response has reached the downloads is a fact
no `--json` surface of bale exposes, so the line says the session is out
and that land finds its response.

`office help` groups the verbs by what you want to do (walk in and look
around, capture, start a job, send a session out, bring one back, look
after the office) and says plainly what the office saves a bale user:
never typing a session id, never assembling an include list, never
forgetting a landing step, with bale's own commands still visible
(start's and land's help name them; `OFFICE_DEBUG=1` shows every call).
`office help VERB` is that verb's `--help`, and every verb's help now
carries examples; `status`, `where`, `default` and `version` take
`--help` too.

`office tour` is the toy drawer: a throwaway office in a temporary
directory, with sample folders, a note, a slip and a calendar with a
gap, and six steps through it (walk in, note, open, the desk, the week,
and what start and land do, shown and never run), each saying what the
command did and why you would type it. On a terminal it waits between
steps and offers a shell inside the tour office to play in (`--play`).
It deletes the office at the end, and when stopped or interrupted, and
says so; it never touches a real office, the default office, the walk-in
record or any bale registry, since a stand-in bale that refuses
everything is first on its PATH.

`office init` asks, on a terminal, which projects the office watches,
one at a time through `office projects add`'s own questions until a
plain return; `--project [NAME=]PATH` is the flag twin, checked before
anything is built, and `--no-projects` skips the question. `office
projects add` now checks a path as soon as it is given and asks again,
before the name and the declarations.

`office start` with a bundle refuses, in the office's own words and
before bale runs, a forecast that overlaps an open session, naming the
session, its folder and the overlap, as it does for a pack, whenever it
can read the bundle's pack line; given a bare name bale's search finds,
it says it cannot read the forecast first and leaves the refusal to
bale. A bundle's `--supersedes SID` clears that one session, as bale's
own gate does.

share/verbs.toml declares `tour` (a script, attended, landing nothing:
its office is gone when it ends). The doctrine says what walking in ends
with, how help is organized, what the tour does and that init asks for
projects (its front sheet and sections 4, 7, 10 and 12).

## 0.7.0

Additive: no migration, nothing to do in any office. Every older office
shape keeps working; a project without after-land actions lands the same
way, with nothing run after.

The return trip. `office land` brings a session back in one command: it
finds the session a response answers (the one the office has out, asked
for when there are several, or named by a session id, a folder or a
response file, each a plain word or a flag) and runs `bale apply` in the
repo the session belongs to, a project or the office itself, or `bale
retry` when bale held the session. bale reads the occupant's own
terminal, so every question it asks (an admission, the merge, a hook)
reaches him as bale asks it, and the office answers none. How the
landing ended is read from the session's dossier and said in the
office's words; whatever bale printed to carry (the relay for the
planner; on a HOLD the worker's block first) is printed whole and, on
WSL, put on the clipboard; a clarification's block comes from `bale
relay`. After an applied landing the project's after-land actions run
in its repo, in order, and the first that fails stops the rest loudly,
with the lines that rerun them; then it asks whether the planner
ratified the session's judgment calls (yes, yes except TEXT, or not now;
`--ratified`, `--except`, `--not-now`) and records the answer in the
folder. A HOLD, a refusal or a clarification records nothing as
ratified, runs nothing after, and names the next line. An office
session's folder, which `office start` records the session in after the
pack, is put back as it was packed while bale lands, so bale never
refuses the response over the office's own record, and the record goes
back after as a new append.

`office start --bundle FILE` (or the `.bale-bundle` file as a word)
sends out a session a planning sitting authored: it asks which job and
where the work lands, gathers what rides, runs `bale open` there,
records the session, fills the out tray and prints the opener, as for a
pack. The bundle's pack line is the whole session; the office adds
nothing to it and answers none of its intents, and says when it leaves
out the office's constraint or the folder. A page of a sitting's words
that a brief carries between `--- NOTEPAD PAGE BEGIN notepad/DATE-SLUG.md
---` and `--- NOTEPAD PAGE END ---` is filed in the notepad and committed
alone, the same words twice are left as they are, and a different page
at that path is refused loudly and never overwritten.

share/verbs.toml declares `land`, landing nothing guaranteed (a HOLD
lands nothing), and `start` writing a sitting's page.
share/bale-consumption.toml declares the four surfaces the return trip
runs, `open`, `apply`, `retry` and `relay`, from a probe of bale 0.4.45,
with the markers of the blocks bale prints to carry. The doctrine says
how a read-only sitting's words land and what `office land` does
(sections 3, 4, 5, 7, 9 and 10, and its front sheet).

## 0.6.0

Additive: no migration, nothing to do in any office. A [projects] entry
without the new keys is valid, and every older office shape keeps
working.

The out trip. `office start` sends a session out in one command: it
asks which folder on the desk (or opens a new one through `office
open`'s questions), whether the work lands in the office or on one of
the office's projects, and the goal, and derives the slug, the forecast
and the work class from the folder. On a project it runs `bale pack`
in the project's repo with the constraint "Office context informs this
session but never lands in this project.", and packs the office's
context (the folder and the hung items) as a context tarball beside it;
in the office it packs from the office, forecasting the folder and the
notepad, or nothing with `--read-only`. The doctrine rides from a copy
of the install's doctrine directory, so the install is never written,
and each path a project declares rides as a context tarball too. Every
file to attach lands in one out tray, ~/out-tray/SID; the session id
is recorded in the folder through the same step as `office sessions`;
the opener is printed, and on WSL put on the clipboard while the tray
opens in Explorer (machine.toml in ~/.config/office-src changes either).
A forecast that overlaps an open session's is refused before bale runs,
naming the session and its folder. Every question has a flag; piped,
it asks nothing and names the flag it needed.

`office projects set NAME` declares what rides beside every session on a
project (`--ride PATH`) and what runs in its repo after one lands
(`--after-land CMD`), by wizard on a terminal; `office projects add`
asks and takes the same, and `office projects` shows them. They are
written into the office's floor plan, never the project's repo. This
release declares the after-land actions; the return trip runs them.

`office slip TEXT` drops a friction slip in the suggestion box as its
own page, saying what it is about (`--about`, asked on a terminal: the
office, bale, office-src or a project), committed on its own, and works
in an unfounded office or under skew. `office note` now refuses to
commit a notepad page whose committed bytes changed, as the doctrine
says every script that appends to filed paper does.

share/verbs.toml: lands means what exists after the verb, so `close`
lands the filing cabinet's folder alone and `reopen` the desk's; `slip`
and `start` are declared, and `work` and `build` are built, through
`start`. share/bale-consumption.toml declares the two surfaces
`office start` runs, a session pack and a context pack, from a probe of
bale 0.4.45. The doctrine says the office runs bale's pack and apply
when the occupant asks, and still never schedules, dispatches to a
model or carries pastes (sections 4, 5, 7 and 10, and its front sheet).

## 0.5.0

Additive: no migration, nothing to do in any office. A folder without
the new fields still serves every verb, and nothing numbers a folder
after the fact.

The desk's verbs. `office open` mints each folder a number, one more
than the highest on the desk and in the filing cabinet (a folder from
before this release keeps none and is cited by its name), and writes
the field block from the template in one rendering: the number, the
status, the day it was queued, and each of class, size, lane, source,
blueprint, linked, after, serializes after and consumer it was given,
with a field it was not given left out. `--candidate` opens a candidate;
`--filed --sid SID` files a job born done inside a session. On a
terminal it asks for the title, size, lane and source it was not given,
four answers with a plain return skipping all but the title, and `?`
explains a field; piped, it asks nothing and names the flag it needed.
`office init`, `office projects add`, `office close`, `office reopen`
and `office sessions` ask the same way, and init now asks for the path
it was not given. While a session open in the office's own bale
registry forecasts the desk (or the filing cabinet, for `--filed`),
`office open` refuses and names it: the one-writer rule. An office bale
has never run in has no registry and nothing to refuse.

`office close` takes `--into N`, `--split A,B` and `--retired WHY`
beside plain done, writes the status and History lines, and gives each
successor a line pointing back. `office reopen` writes `reopened` and
status open, and does not reopen a job that lives on elsewhere.
`office sessions` opens a candidate or queued folder with the first
session it records, and `--ratified [--except TEXT]` records the
planner's ratification under the session's line. `office desk` renders
its groups in order: in flight (including the office's own open
sessions), ready (by `serializes after`, then size, then number, each
saying when a gate cleared since the last walk-in), parked under what
each folder waits for, and candidates; a gate on a blueprint, agenda
item or ruling waits as not readable until the drafting-table verbs
land. Walking in shows in flight and the first three ready folders, and
keeps the day of the walk-in on the machine, outside the office.

`office status` checks that every folder's status agrees with its
History and that numbers are minted once, and walks git's history of
every filed page but the filing cabinet for a commit that did more than
append. `office init` refuses to build an office from an install whose
catalogs have a defect; `office status` still reports one and exits 0.
share/verbs.toml lands open, close and reopen on the folder patterns
they write.

## 0.4.0

Additive: no migration, nothing to do in any office. An office without
a [projects] table keeps working and says it scopes no projects.

The read side. An office names the projects it scopes in its floor
plan's new [projects] table, a name and the path of each project's repo
on this machine, written by the new verb: `office projects` lists them
and `office projects add NAME PATH` adds one, a wizard on a terminal
that asks for what it was not given, refuses without it when piped, and
checks the path is the top of a git repo bale runs in (a .bale/
directory or a bale.toml), saying which it found. office init writes no
table; the founding session or the occupant adds the projects.

lib/office_bale.py is the reader: the only code that runs bale, through
its --json surfaces only (status, stats, a session's dossier), in the
project's directory with stdin closed, never reading .bale/ and never
writing. share/bale-consumption.toml is its contract with bale: every
verb, flag and key it reads, written from a probe of bale 0.4.45, which
is the floor. office status reports the installed bale against it, a
line and never a refusal, and whether each project in scope can be
read. On it, the renderings: walking in shows the sessions in flight in
the office's projects, each with the folder that names it; `office
sessions FOLDER` shows each recorded session's outcome, dates, claims
beside verdicts and exchange rounds; `office projects --ledger`,
`--landed PATH` and `--versions` render the trust ledger per work class,
the last applied session that landed a path, and the version trail.
Nothing rendered is ever written into an office. The pack report's
session id is read from its `sid` key, which bale's pack contract names;
the guess at an id-shaped value is gone. The doctrine says that reading
is not copying, that where a report and the records part the records
stand, and that a number that can go stale is computed where it is shown.

## 0.3.1

Additive: no migration, nothing to do in any office.

Every verb in share/verbs.toml declares three more keys: lands, what
is guaranteed to exist after the verb succeeds; attended, whether a
person must be present; and trigger, what may set it off, from a closed
vocabulary (manual, before-sitting, after-sitting, after-build, on-hold,
on-correctable-hold, schedule). The rule they carry: a session kind
with attended = false must declare a landing. The catalog also
registers the session kinds the drafting-table blueprint declares
ahead of the command, sitting, chat, blueprint-close, digest, review,
check and retry, every one built = false; cleanup now ships and writes
drafting-table/riders.md. Nothing in the command consumes the keys yet
beyond the check: they are a registry for the shell and for whoever
spawns sessions. The test suite refuses a catalog that breaks the rule,
names a trigger outside the vocabulary or lands a path outside the
verb's writes, and refuses a space catalog whose filed or hung lists
hold anything but pages or globs inside the space, or a hung page that
is also filed. office status reports both from the installed catalogs
in one more line.

## 0.3.0

Additive: no migration, nothing to do in any office.

The drafting-table gets its contents in the install. The space catalog
files a list of paths inside the space (the rulings and evidence
ledgers, the watch log, every blueprint's close report), the first
space that is part live, part filed; office upgrade's filed-paper check
reads the list. Templates for a blueprint and its close report, and a
page skeleton for each drafting-table page: the front page with its
citation table, the agenda, rulings, evidence, watches, the watch log,
riders and desk moves. A renovation copies them into an office when the
space arrives; nothing copies them yet. The folder template gains a
field block under its title, a Riders section and a History section;
office open writes the status and the queued date, the fields it can
fill without guessing, and the first History line. doctrine/checks/
ships filed-append-only.sh, the check a session pastes into its
validation for every filed page it writes: the page's first bytes, as
many as the shipped copy had, hash to what the request stamped. The
doctrine says what the drafting table is, that appending is not
rewriting, that a fact has one home and is cited by id, and that a verb
is a wizard on a terminal with a flag twin for every question.

## 0.2.0

Breaking: ships migration 0.2.0, a script. Offices built by 0.1.0 gain a
bale.toml whose include group makes every pack from the office ship its
hung items. Run office upgrade in each one; office note works before you
do.

The everyday verbs: note, open, desk, week, close, reopen, and sessions,
which records the ids of the sessions that worked on a folder, read from
a bale pack --json report. office with no verb is walking in. office
init writes bale.toml and prints a scoped founding session that lands
the profile, the occupant's words as a notepad page, and the office's
real timezone. Only office upgrade writes the version stamp: a
renovation migration declares what must be true once it has landed, and
a re-run of office upgrade checks it and stamps the office. office
status reports when bale.toml's include group no longer matches the
floor plan.

## 0.1.0

First release: the doctrine, the templates, the profile's required
shape, the space catalog and verb declarations, office init, survey,
status, upgrade, where and default, and the migration runner. No
migrations.
