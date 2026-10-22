# Releases

A release is breaking exactly when it ships a migration (migrations/).
Each breaking release's migration carries the plain-language summary
that office upgrade writes into the office's commit.

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
