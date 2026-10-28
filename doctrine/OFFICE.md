# OFFICE.md

How every office works. This doc ships with every office session. It
lives in the office-src install and is never copied into an office, so
upgrading the install changes it for every office at once. Each office
says why it exists, and what it adds to these rules, in its own profile
(profile.md at the office root).

## Front sheet

Reading card. Find the row for the session you are, read the sections
it names, and stop. What a build session on a project reads is the
core: it sits above the banner marked PAST THE CORE, in reading order,
and everything else sits below it, its section numbers unchanged.

| Kind of session | Reads |
|---|---|
| A build session on a project, the common case | this card and the front sheet below it; section 2, the audience line and its three boundaries; section 3, the principles, whose sixth is the pages at the end of notes.md (the walkthrough, the delivery and the folder's structure); section 4 to the end of its list, how a session is packed, what the doctrine tarball beside its request is, and what it owes the drops it carries; and section 9, the house rules |
| A work session in an office | the build row, then section 5 for the spaces it writes (the table, then those spaces' paragraphs), section 6, what every office session ships, and section 15, filed paper and its check |
| The founding session | the work row, then section 12, the profile |
| A sitting | the work row, the drafting table being the space it writes; then the rest of section 4, and sections 7, the verbs, and 8, when to open a session |
| A session building office-src | the whole doc, since the tool implements it |

An office is where you go to begin work on the projects in its scope. It
holds what only you and your sessions may read, organized like a physical
office so that anyone, you or a session, can guess where something lives.
Projects hold what their audience may read. When a session is packed, the
office supplies all the context that is not the project's own.

You keep one office per set of house rules. A job gets a folder on the
desk. A folder holds the conversation that started the job, the questions
and your answers, drafts, copies of messages you sent, and the ids of the
sessions that worked on it. When the job is done, the folder goes to the
filing cabinet, and it comes back with its history if the job reopens.

Every office has a profile: why it exists, what it is not for, who may
read its projects, where it lives and where it must never go, its own
house rules, when a session is worth opening there, and how it was
founded. An office whose profile is incomplete is unfounded and says so.

The office command builds and keeps offices. `office init` builds one,
surveys the machine, asks which projects it watches, asks the profile's
questions, and sends the founding session out through `office start`
with the answers in its brief; `office found` does the same for an
office that exists and is unfounded. `office tour` builds a throwaway office
to try the verbs on, walks through them, and deletes it. `office` on its
own is walking in. On a terminal it is the home screen: each project the
office scopes, one line each, then what waits on the occupant, each thing
with a key that runs it, so he never types a session id or a file name.
Off a terminal it is the page: what is on the desk, this week, the last
notes, the suggestion box, what you can do from here, and, last, the one
command to type next. The
everyday verbs take seconds and need no session: `office note` captures a
line, `office slip` drops a friction slip in the suggestion box, `office
drop` drops a message or a thread in the in-tray, to be sorted by a
session that has the code in context, `office desk` shows what is
in flight, what is ready and in what order, and what waits on what,
`office week` shows this week against what happened, `office close` and
`office reopen` move a folder to the filing cabinet and back. `office
survey` rewrites the page of machine facts. `office status` says whether
the office matches the installed tool. `office upgrade` brings an office
up to a new release, one commit per office. `office projects` lists the
projects in the office's scope, declares what rides with each and what
runs after its sessions land, and renders what bale records about them.
`office probe` runs a worker's probe block where a folder's project lives,
on its host when it has one, after showing the block's header and asking
once, and hands the output back with the block on the clipboard; a
read-only sitting's probe of a project (`--project NAME`) runs there too,
under the sitting's id.

`office start` sends a session out, and it is the one door for new work:
`office start new` takes the job in the occupant's words, names the
project only when his words do not, mints the folder (`office open`'s own
code, now plumbing) and sends its session out in one motion. Given a job
on the desk, it offers the planner's bundles in the downloads that no
session has opened, asks which job, works out where the work lands from
the folder (asking only when it cannot tell) and takes the folder's goal
or asks for one in his words, then runs bale's pack (or opens a planner's
bundle), records the session in the folder, files the planner's
ratifications the brief carries, and puts every file to attach in one out
tray beside the opener to paste. `office land` brings it back: it runs
bale's apply in the repo the session belongs to, says how it ended, files
what the session's notes.md sends back (the folder's structure among it),
after an applied landing runs the project's after-land actions and closes
a folder whose one session landed, ends by saying what became of each
action, and puts what bale printed for you to carry on the clipboard last
of all; it asks nothing about ratification. Given a read-only sitting it
sent out, it ends the sitting with bale's unlock instead. `office start
--planner` sends a planner sitting from the occupant's words: his words
its goal, what rides gathered by the office and said, and the in-tray's
sort offered first when drops wait; a planner's bundle whose brief names
where it lands (its LANDS line) goes out asking neither where nor which
job; `office withdraw` closes a session he sent out and will never run,
named by its folder and asked once; and `office meeting` records a meeting
from his words, once, its prep, a sitting briefed from what landed since
the last one, sent by key when it is near (`office start --prep`), and
what arises in it reaching the in-tray as drops. The
office runs bale when you ask, as your hands at the terminal; bale asks its
own questions and only you answer them. It never schedules a session,
never hands one to a model and never carries pastes. bale carries the
session.

> Section 1, what an office is, sits past the core banner, ahead of
> the rest of section 4; its number is unchanged.

## 2. The audience line and three boundaries

The line: a project holds what its audience may read, whatever its
medium. The office holds what only the occupant and their sessions may
read. The profile names each office's audiences, so a session knows who
may read what it writes into a project.

Three boundaries hold that line, each with a guard.

1. What never enters a session. Guard: the house rules in the profile.
   Some offices sit next to data that must never be shipped; their
   profile says which, and a session honors it before anything else.
2. What leaves the office, into a project or to a person. Guards: the
   letterhead, where an office has one, for anything that goes out: its
   voice page, the occupant's style rule in his words (section 4 says
   who reads it), and its check, `office letterhead check`, which names
   every line that holds what the letterhead refuses (the names of
   models, vendors and products; tell-tale phrasing an assistant writes,
   a repository's own pull-request template's lines aside; bale's own
   marks; the office's forbidden words, letterhead/forbidden.txt; and by
   default the em dash, the en dash and the ellipsis, the template's lines
   aside again, section 5);
   `office deliver`, the one way a project's landed work reaches its
   audience's git host: a branch of curated commits in the occupant's
   words, made from the audience's base, holding no bale commit, merge,
   tag or branch and no file bale's exclude list names, checked by the
   letterhead, each commit shown whole and asked once, every one carrying
   the project's declared author as author and committer, and never the
   workbench branch itself; the push guard in the clone, which lets
   nothing reach the audience but that one delivery branch (no tag, no
   bale branch, no other ref); `office land`'s review, which says what
   deliver would refuse and refuses nothing; and the rule that office
   context informs a session but never lands in a project. Every project
   session an office packs carries that rule as a constraint: "Office context
   informs this session but never lands in this project." Deliberation,
   candid notes and private versions stay in the office even when a
   session read them to do the work.
3. Where each repo is pushed. Guard: the profile's site section. An
   office repo is never pushed where a project's audience can read it.

## 3. Principles

1. Capture is instant and dumb. Structuring is slow and smart, and
   happens later in batch.
2. Every session lands something: at minimum a notepad entry and the
   folder it touched. A read-only sitting lands nothing itself: its words
   reach the notepad when `office start` sends out a session whose brief
   carries the sitting's page, whether that session is an office session
   or a project session.
3. A session is worth opening only when the job needs it (section 8).
   Otherwise the occupant does the work and leaves a one-line trace.
4. What every session needs is hung. Hanging is a property of an item,
   not a place (section 6).
5. A space earns its place through use. A space unused after a few weeks
   of real work is removed; new spaces arrive when real work asks for
   them.
6. Nearly every job produces two deliverables: the thing, which lives in
   a project, and the message about the thing, which leaves through the
   letterhead with a copy in the folder. The folder holds the message as
   two pages a build session writes, at the end of its notes.md, and
   `office land` files: walkthrough.md, what changed, why, how to explain
   each piece, the questions a reviewer will ask and a hand test for what
   only eyes can check, which stays in the office; and delivery.md, the
   words the work leaves with, the commit and the review request in the
   occupant's voice and whom to send it to, which `office deliver` reads.
   In the same place a session writes a third section for the folder
   itself, `## Structure`: the folder's title, size and goal as the
   session judged them once it knew the job, in the form section 4
   pins, which `office land` files over the values the office worked out
   and marked provisional. The occupant's own words are never touched.

## 4. How a session is packed

A session is packed where it lands.

- A session that lands only in the office is packed from the office. It
  ships what its verb names, the hung items, and this doctrine.
- A session that lands in a project is packed from the project. The
  office's context (the folder, the hung items, whatever the verb names)
  rides beside the request as a context tarball made with
  `bale pack --context --include ...` from the office root, and the pack
  carries the constraint from section 2.
- This doctrine rides as a context tarball made from the install's
  doctrine directory: `bale pack --context` run on a copy of it, so the
  install is never written. bale's include groups only pull paths inside
  the repo being packed, and this doc lives in the install, not in the
  office.
- Whatever a project declares rides too: each path in its `rides` (a
  directory inside another repo, a whole repo, or a file) becomes a
  context tarball beside every session on that project (section 10).
- A project on a host is packed on its host. bale is installed per
  machine, and the bale that packs a session is the one that will land
  it, beside the repo: bale's pack (or its open, for a bundle) runs
  there through the project's shell (section 10), and the request it
  makes is carried back to the out tray on the occupant's machine. The
  office's context tarball, the doctrine and the ride-alongs are made on
  the occupant's machine, as for any project, and ride beside it. A
  brief or a bundle travels to the host first; whatever the office
  writes on a host outside the project's repo is removed again, whether
  the start succeeded or not. One start reaches the host once, and the
  reads it needs there share a connection.
- A session may carry drops: pages from the office's in-tray, each a
  message or a thread the occupant dropped with `office drop`, waiting
  to be sorted (section 5). Every session `office start` sends out
  carries the unsorted ones, in its request or in the office's context
  beside it, and the opener says how many. A session that carries drops
  reads them before its work, and sorts the ones it can judge (its own
  project's at least) in a `## Sort` section of its notes.md: one
  `### DATE-SLUG.md` subsection per drop, named by the page's file name
  wherever the page sits (the in-tray, or a folder's drops/), in the
  format below. It leaves the rest to the office, and the drops change
  nothing about its goal. A read-only sitting reads them and owes no
  Sort. The office reads this format, so it is kept to the byte, every
  key on its own line, in this order (values illustrative):

  ```
  ### 2026-10-14-login-error.md

  - project: alpha
  - folder: new
  - goal: Fix the login page's error on narrow screens
  - size: small
  - tell: the sender, in reply: fixed in the next release
  - facts: none

  #### Brief

  <the next session's brief, written from the thread>
  ```

  `folder:` is `new` or a folder number; `tell:` is `nobody` or who and
  what; `facts:` is `none` or one or more lines for the project's
  handbook chapter, each starting with `- `; `#### Brief` is present
  when `folder:` is `new` and may be present otherwise.
- A session that writes text for a project with an audience reads the
  office's letterhead first, as it reads the profile: the voice page,
  letterhead/voice.md (an empty, marked place means no words yet), and
  the forbidden list, which ride beside its request (0.25.0). What it
  writes for the audience holds no em dash, en dash or ellipsis unless
  the letterhead lifts one.
- A session writes what the office keeps for it at the end of its
  notes.md, and `office land` files it, so a project session never
  writes the office: each light block it sent and the occupant's answer
  under `## Questions and answers`, one `- DATE question? answer` line
  each; each fact the occupant gave it, or that it learned about a
  project's shape, under `## Handbook`, `### PROJECT`, as `- ` lines,
  with a `#### Front sheet` paragraph when what the occupant should know
  changed. It reads the handbook chapter it carries before it asks
  anything, so nothing is asked twice. A Sort's `tell:` lands on its
  folder's Next.
- Every session that works a folder writes `## Structure` at the end of
  its notes.md (principle 6): the folder's title, size and goal as it
  judged them, three lines, each key on its own line, in this order and
  nothing else (values illustrative):

  ```
  ## Structure

  - title: Fix the login page on narrow screens
  - size: small
  - goal: Fix the login page's layout on narrow screens
  ```

  `size:` is small, medium or high; each value is one line. `office land`
  files a value over a field the folder marks provisional (the office
  worked it out from the occupant's words, it did not hear it) and keeps
  every other: a field he gave, or a flag set, is his, and a field the
  folder does not carry stays absent. It says in one line what changed. A section off this
  shape is said and nothing of it is filed.

> Section 4 continues past the core banner, from "`office start`
> does all of this", and sections 5 to 8 follow it there.

## 9. House rules for every office

These hold in every office. Each office adds its own in its profile.

1. Every session lands something: at minimum a notepad entry and the
   folder it touched. A planning sitting's words travel in the briefs of
   the sessions it authors, and `office start` files them in the notepad
   when it sends one of those sessions out.
2. Every session that lands a change to something the handbook describes
   updates the front sheet of that chapter in plain language.
3. Nothing goes on a rolodex card that would embarrass the occupant if
   the person read it.
4. Anything that asks the occupant for bookkeeping, setup or moving files
   is friction. Say so in a suggestion slip. When a hand step cannot be
   avoided, give it as one line and say where to run it.

> Sections 10 to 15 sit past the core banner, after section 8.

---

> **PAST THE CORE.** Everything above this banner (the reading card,
> the front sheet, sections 2 and 3, section 4 to the end of its
> list, and section 9) is what a build session on a project
> reads. Everything below it (section 1, the rest of section 4,
> sections 5 to 8 and 10 to 15) is read when the reading card's
> row for the session names it, and a session building office-src
> reads it all.

---

## 1. What an office is

An office holds what only its occupant and their sessions may read, and
the context around the work: why a job was taken on, the correspondence
that produced it, deliberation, candid notes, the rolodex, private
versions of things. It is organized like a physical office because a
predictable layout is what lets a session find what it needs without
being told.

The work itself mostly lives elsewhere. A project exists when a thing has
an audience or must run somewhere: code, a report, a user guide, a
filled-in comparison of houses that sold nearby. Projects are their own
repos. The office is where a job starts (a folder) and where everything
around the work lives. A thing whose only audience is the occupant can
live in its folder; the office is in git, so it has history.

The occupant's work in an office is creating, making judgment calls and
directing traffic. Anything that asks the occupant for bookkeeping is a
design flaw and goes in the suggestion box.

## 4. How a session is packed, continued

`office start` does all of this for a folder in one command. It packs
the session from the office or from the project (on the project's host,
when it has one), makes every context
tarball that rides beside it, and copies them with the request into one
out tray, a directory on the machine outside every office, named by the
session's id; the occupant attaches its files and pastes the opener it
prints. An office session forecasts its folder and the notepad, so
office sessions take turns; `--read-only` packs a sitting that forecasts
nothing. Before it packs a sitting, `office start` writes the digest
again (section 5), committed alone, and the drafting table rides inside
the sitting's request, the digest first among its pages; an open session
holding the drafting table, or a digest that cannot be written, leaves
the page as it was and never stops the start. A bundle named by a bare
name is read where bale's rehearsal found it, to tell whether it is a
sitting; one whose pack line the office cannot read at all leaves the
page as it was, said in one line with the time the page was written,
since a silent skip would send a sitting out on a stale page. A session whose forecast overlaps one already open is refused
before bale is asked, and the open session, its folder and the overlap are
named. A second desk is bale's to recognize, and the office refuses an
overlap only where bale would (0.18.0): a bundle whose pack line the
office can read is checked the same way, and bale's own rehearsal runs
before anything is written; a bundle bale would take as a second desk on
an open session is sent on, the overlap the office saw said beside bale's
words, and one bale's rehearsal refuses is refused in the office's words
with bale's reason beside them (a bale whose rehearsal does not answer in
JSON is refused on the office's reading alone). Where the office cannot
read the pack line (a bare name bale's search finds), it says so and
bale's own words stand. For a project on a host a
bundle is a file on the occupant's machine: its path, or a bare name the
office finds in the downloads (below), since bale's own search would run
on the host. A session a
planning sitting authored arrives as a bundle (a .bale-bundle file):
`office start --bundle FILE` hands it to bale's open in the place the
occupant names, the office or the job's project, and gathers what rides
the same way. The bundle's own pack line is the whole session, its goal,
forecast and brief, and the office adds nothing to it and answers none of
its intents; it says so when the line leaves out something the office
would have carried, such as the constraint of section 2.

A planner's brief names where its session lands and the folder that
records it (0.24.0), in one line kept to the byte as the RATIFIED lines
are and read where they are read, anywhere in the brief outside a fenced
block and outside a notepad page (values illustrative):

  ```
  --- LANDS alpha, folder 14 ---
  --- LANDS the office, folder 14 ---
  --- LANDS alpha, a new folder ---
  ```

The place is a project the office scopes, or `the office`; the folder is
`folder N` on the desk, or `a new folder`, which `office start` mints from
the bundle's goal as it mints one for any bundle. bale's bundle format is
untouched: the line lives in the brief, the planner's member, so bale's
open and its gates see nothing new. `office start --bundle`, bare `office
start` and the home screen send such a bundle without asking where it
lands or which job, and say both in one line. Each question comes back,
alone, only when the line is absent, does not read, names a project the
office does not scope, or names a folder the office does not hold on the
desk (one in the filing cabinet is named, with the line that reopens it);
each case is said in a line and never guessed past. A flag still sets
its field (`--on`, `--in-office`, a folder given), and the line it
overrides is said. A brief carries one LANDS line; a second is said and
the first taken. Every planner bundle carries one from office-src 0.24.0
on.

A planner sitting from the occupant's words (0.24.0): `office start
--planner`, the home screen's p key. He says what he wants a planner for,
in his words, and a read-only sitting goes out from the office, recorded
in a folder: one minted from his words through start new's code, its
title, size and goal provisional as section 5 says (`office start new
--planner`, and the p key), or one on the desk he picks by key or names
(`office start FOLDER --planner`), which keeps his words in its Asked
section. His words are the sitting's goal. Nothing else is asked: no
title, no separate goal, no size, no include list; what the sitting
concerns is asked only when his words name none of the office's projects
and the answer changes what rides, and "the office itself" is an answer
(`--about PROJECT`, once per project, and `--in-office` are its flag
twins; piped, a sitting whose words name no project and whose answer
matters refuses and names them). Its brief is the office's, from the
install's templates/sitting-brief.md: his words verbatim, what they
concern and how that was found, and what rides and why, one line each, in
the order to read them, where the planner reads first; the screen shows
the same lines before the pack. Its opening names the doctrine it goes out
under, in one line (0.33.0): the sha256 of the install's
doctrine/OFFICE.md as the doctrine rides with it (the bytes the rides-once
check reads), with its release; and `office start` stamps the same
doctrine in the folder's Sessions line, `- SID: sitting, doctrine SHORT`
(its first twelve characters), for every sitting it sends from a folder,
a bundle's included, whose brief is the planner's and so carries no such
line. The walk-in's In flight, the home screen's item that ends a sitting
and `office status` read the stamp back, and when it is not the install's
(office-src moved on while the sitting was out) say that the sitting is
out under an older doctrine, naming both short hashes, in one line.
Nothing refuses: the sitting may finish on the doctrine it read. What
rides, in this order:

1. the sitting's own folder, whole, the drafting table with its digest
   written first, the hung items and the unsorted drops, as every
   sitting carries them;
2. for each project his words concern, its handbook chapter;
3. the folder.md of each folder on the desk on those projects (for the
   office itself, the folders whose lane names none of its projects),
   the sitting's own aside;
4. what landed on those projects since the last sitting, as the office
   holds it: the walkthrough.md of each folder, on the desk or in the
   filing cabinet, that `office land` filed or rewrote since the commit
   that filed the last sitting's page, newest first (a folder that only
   moved is a rename to git, not a filing); never bale's telemetry;
5. the last sitting's notepad pages: the latest sitting's page, by the
   commit that filed it, and its continuations (SLUG.md, SLUG-2.md, and
   on, whichever of them was filed last).

No project's tree rides with a sitting from his words: what the office
holds about the project does. The set stays inside bale pack's soft caps
(10,000 files and 100 MB, `bale help pack`), with a tenth to spare for the
rest of the pack: when it would not, the oldest page of what landed is
left out first, one at a time, each said on the screen and in the brief,
and nothing else is ever left out; a set still past the caps then is
said, and bale's own caps speak for themselves. A sitting a planner's
bundle carries goes out as before: the bundle's pack line is the whole
session.

Before any sitting is packed (from his words, a `--read-only` start, or a
bundle whose pack line is read-only), unsorted drops in the in-tray are
said, how many, and the in-tray's sort is offered first, by key, through
`office start --sort`'s own code (`--sort-first` and `--no-sort-first`
are its flag twins). Taken, the sort goes out and the sitting he asked
for goes out right after it, in the same motion: two out trays, and the
sitting's opener is the last copy made, so it is the one on the
clipboard, the sort's printed above it. Declined, or piped with neither
flag, the sitting goes out as it would have and carries the drops, as
every session does. The sort is not offered while one is out or while an
open session holds the in-tray (each said), and a sort that does not go
out is said and the sitting goes on.

A meeting is a view over the work (0.26.0), never a job: no folder is
minted for it. `office meeting`, the occupant's verb and the home screen's
m key, takes it in his words, one sentence, and writes its line in the
calendar's plan (section 5): when it happens, read from his words (a date,
a day, today or tomorrow, every DAY, daily, weekdays, a time; a bare hour
from 1 to 6 is the afternoon, said), its title (his words, less when) and
what it concerns (the projects his words name). It asks only when his
words do not say when, or name none of the office's projects, and "the
office itself" is an answer; a series is one line, never asked for again.
`--words`, `--when`, `--about PROJECT` and `--in-office` are the twins, and
piped it asks nothing.

A meeting is near from 24 hours before it starts until 4 hours after. The
home screen shows each near meeting whose prep has not gone out among what
waits, with a key that sends its prep, `office start --prep MEETING`
(MEETING its `YYYY-MM-DD HH:MM title`, or words that name one near): a
read-only sitting from the office, through the planner sitting's
gathering, its goal the meeting's words and its brief the office's, from
the install's templates/prep-brief.md, whose field block names the
doctrine it goes out under as a planner sitting's opening does (0.33.0).
No folder records it: the calendar's record line does, by its id, so no
Sessions line stamps its doctrine and the walk-in does not compare it. What rides, said on the screen and first in
its brief, one line each with why, inside bale's caps as for any sitting:
the calendar; what every sitting carries (the drafting table with its
digest, the hung items, the unsorted drops); each project's handbook
chapter; the folder.md of each folder on the desk on what it concerns;
the walkthrough.md of each folder, on the desk or in the filing cabinet,
that `office land` filed since the last meeting that concerned that
project (by the record's time; for a first meeting, in the 14 days before
it), newest first, every landed session counting whether or not a meeting
asked for it; and the drops tied to that last meeting, wherever they are
now, with the folders they became. The window is the meeting's, not the
last sitting's. The same sitting serves before the meeting and during it,
and nothing else is opened for the meeting. It is not offered the sort
first: a meeting is near, and the drops ride with it.

What arises in the meeting the sitting writes down in one block, kept to
the byte as a Sort is, and current as the meeting goes; its BEGIN line
names the sitting's id, each item is a `### ` line in the occupant's words
(the drop's first line), a `- project:` line (one of the office's
projects, `the office`, or `none`) and, after a blank line, whatever else
was said, verbatim (values illustrative):

  ```
  --- ARISING BEGIN 2026-10-25-weekly-review-prep-001 ---

  ### Update the report with the new criteria

  - project: alpha

  The review asked for the new criteria from next week.

  --- ARISING END ---
  ```

A block with no item says nothing arose; of several blocks in one text the
last counts. The sitting offers it as a file, arising-SID.md. `office land
SID` ends the sitting with bale's unlock, as for any sitting, and first
reads the block, at most one paste or one file, never retyped: `--arising
FILE` (`-` for stdin, `none` for nothing), else arising-SID.md in the
downloads, else, on a terminal, the clipboard once he has copied it;
piped with none of them it refuses and names the flag, and a block that
does not read (another sitting's, a line outside an item, an item with no
project line) stops land with the sitting open. Then it rewrites the
meeting's record line as held, writes each item as a drop in the in-tray
(`office drop`'s page, its via the file or the clipboard), tied to the
meeting by the record's `arose:`, commits them together and says in one
line what it filed. A drop the occupant makes himself while the meeting's
prep is out, from an hour before it starts until 12 hours after, is tied
to it by `dropped:`. The next meeting on those projects carries these
drops, and the folders they became, in its prep.

A prep's brief tells the sitting that it may author one cleanup session
for the meeting's projects when it finds their documentation messy,
disorganized or too wordy: a planner's bundle beside the briefing, its
brief carrying its LANDS line, which the occupant sends from his home
screen or deletes. It is offered, never required, and needs no separate
maintenance session; it is the cleanup the verbs table says is built.

The folder records the id of every session that worked on its job.
`bale pack --json` reports the id, so nobody types it: `office start`
records it in the folder's Sessions section, and a session packed by
hand records the same way, by piping that report into `office sessions
FOLDER -`, with a few words if the occupant gives them (`-m`). The
folder points at session ids; it never copies what bale records about a
session.
`office sessions FOLDER` lists them with what bale records about each,
rendered on every run (section 10).

`office land` brings a session back in one command. It finds the
session a response answers (the one out, a named one, or the one a
response file names), runs `bale apply` in the repo it belongs to (`bale
retry` for a session bale held), with the occupant's own terminal as
bale's input, so every question bale asks (an admission, the merge, a
hook) reaches the occupant as bale asks it; the office answers none. It
reads how the landing ended from bale's records, not from bale's words,
and hands the occupant whatever bale printed to carry (the relay), whole.
Only after bale has applied the session does it run the project's
after-land actions (section 10). A meeting's prep it ends as a sitting,
then records the meeting held and files what arose (above). Before them, on a project with an
audience (0.25.0), it reviews what the session landed against the
letterhead, as deliver will read it: the files the landing changed
(applied/SID's first parent to the tag, bale's own files aside, never
bale's commit messages, which never travel) and the folder's delivery.md
words, the pull-request template's lines exempt as at delivery; and says
in a line what deliver would refuse, each line named, so a fix can ride
the next session before the occupant tries to deliver. It refuses
nothing there, and a review that cannot run is a line. It asks nothing about ratification, on
any path: when land ends, the planner has not read the relay, so an
answer there would record nothing. A HOLD, a refusal or a clarification
lands nothing: it runs nothing after, and names the next line.

The planner's ratification travels in the next brief it authors, one line
per session it ratifies, kept to the byte as the NOTEPAD PAGE markers are,
anywhere in the brief outside a fenced block and outside a notepad page
(values illustrative):

  ```
  --- RATIFIED 2026-10-14-alpha-login-error-001 ---
  --- RATIFIED 2026-10-14-alpha-docs-002, except: the slug rule; fixed in this session ---
  ```

`office start` files each, when it sends that brief's session out, in the
folder that records the session it names, on the desk or in the filing
cabinet: `- SID ratified DATE` (with `, except: TEXT` as given) as the
last line of the folder's Sessions section, which adds a line and
rewrites none, and says so in a line. A session no folder records is said
and skipped; a folder that holds the session's ratification already is
said and left as it is; a folder an open session's forecast holds (the
one-writer rule) is said, with the `office sessions FOLDER SID
--ratified` line that files it once that session is in. An exception is
fixed in the next session or queued there, never answered by the
occupant at the terminal. An office session's folder
moved after the pack, because `office start` recorded the session in it;
`office land` puts the folder back as it was packed while bale lands, so
bale never has to refuse the response, and records the session again
after.

A session on a project on a host lands on its host, as it was packed
there. `office land` checks first that the host answers; one that does
not stops the landing before anything is carried, with the occupant's
connect line and the line that reruns it. The response is found on the
occupant's machine (a path given, or by name in the downloads), carried
to the host into one temporary directory, held to its sha256, and `bale
apply` or `bale retry` runs in the project's repo there through the
project's shell, attended, so bale's questions reach the occupant
through every layer and only he answers them. How it ended is read from
bale's records there; whatever bale prints to carry comes back to the
occupant's screen whole (and, on WSL, to the clipboard on his machine, as
section 10 says);
a clarification's block comes from `bale relay` run there; the
after-land actions run in the repo there; the closing, the watches and
the last lines are as for any landing; a sitting there ends with
`bale unlock` there. Whatever the office writes on the host outside the
project's repo is removed again, whether the landing succeeded or not.

Where downloads land is the office's own setting, never bale's: the
`downloads` key of the machine's `~/.config/office-src/machine.toml`, a
list of directories, asked once on a terminal the first time a verb
needs it (this machine's likely directories offered, `?` explaining it)
and never again; a piped verb that needs it refuses and names the key.
`office land` finds a hosted session's response there by name, and
`office start` a bundle for a hosted project. The home screen offers what
it finds there by key: a response for a session that is out (a file to
offer, never a verdict: whether it has arrived is still bale's to say),
and a planner's bundle no session has opened, which bare `office start`
offers too, newest first, before it asks anything else. Whether a bundle
was opened is read from bale's records (a session's attempts name the
bundle they were opened from, by its stem), never guessed; a bundle
saved more than two weeks ago is not offered, and `office start --bundle`
still opens it. bale's own search directories are not on any of its
--json surfaces, so the office looks only in its own setting. A browser saves a second
download of one name as `NAME (1).EXT`; of several copies of a name the
newest by modification time wins, and the office names the file it took.
For a project on the occupant's machine bale's own search finds a
response, as before, unless the downloads hold several copies of its
name; then land passes bale the newest by its path and says so, since
bale's search takes the plain name first and a corrected response after
a HOLD is usually the `(1)`.

A folder is finished when its only recorded session landed applied: on a
terminal `office land` then closes it, done, in the same breath, and says
so with the line that reopens it, since a close can be undone and nothing
is left to judge; the planner's ratification, and any exception, arrive
later in the next brief (`--leave-open` keeps it on the desk, `--close`
closes it piped; piped with neither, it leaves the folder open and says
so). The founding folder keeps its own rule.

A session that went out and will never be worked is withdrawn (0.24.0):
`office withdraw`, his surface's verb, and the home screen's w key, shown
while there is one. The office names the session by its folder, the
folder's number and title, never by its id: with one such session it is
named, with several they are offered by key (a folder given, or a session
id for a script, picks one). It asks yes or no once, since closing it
cannot be undone (`--yes` is the twin; piped, it is needed); then it runs
bale's unlock with bale's own reason, `abandoned`, in the repo the session
is open in (through the project's shell for a project on a host), and
adds `- DATE withdrawn: SID, never worked; closed in bale by office
withdraw (abandoned)` to the History of each folder that records it. A
session with a response in the downloads (land's), one bale has started
to apply (held, or any attempt after its pack: bale's revert, never an
unlock), and a read-only sitting (office land ends it) are never offered,
each said with why; bale's own refusals are shown whole. A folder that
recorded the withdrawn session and no other is said in the same breath,
with the line that closes it (`office close NAME --retired "withdrawn
before it was worked"`), and never closed by the office.

After a project session lands, the office side (the folder, and the
front sheet of any handbook chapter the change touched) is brought up to
date by an office step, not by the project session writing into the
office: `office land` files the folder's walkthrough.md and delivery.md
from the Walkthrough and Delivery sections of the response's notes.md
(principle 6), when it found the response on the occupant's machine;
`office sessions FOLDER SID --pages RESPONSE` files them from a response
bale found on its own. Both then file four more sections of any
session's notes.md, in this order, each only when present and each said
in a line. The Sort: each `### NAME.md` subsection on the drop's page,
found in the in-tray or in the landed folder's drops/, as a `## Sort`
section at its end (section 5), its status set to sorted; a page sorted
already is said and left as it is, and a subsection naming a page that is
nowhere is said and skipped. The Questions and answers: each line as it
is, in the folder's Questions and answers section, after a line naming
the session. The Handbook: each fact as `- DATE: fact (SID)` at the end
of its project's chapter, with a Sort's `facts:` lines, and a Front sheet
in place of the chapter's, whole. The Structure: over the provisional
fields of the folder that records the session, when that folder is on the
desk (a folder in the filing cabinet moves whole, and a session no folder
records has none), as the bullet in section 4 pins it. Then, when a
sorted drop waits in the in-tray, or the session was a standalone sort
whose moves page holds pending lines, `office land` runs `office moves`
and names each folder it minted, before the after-land actions. A HOLD, a
refusal or a clarification files nothing. A standalone sort, which
no folder records, is filed by `office sessions --in-tray SID --pages
RESPONSE` when only bale found its response.

`office start N` asks nothing the folder already knows. A folder with a
`goal` field sends it as the session's goal, said and never asked again
(`--goal` overrides), and a folder with a brief.md sends it as
the session's brief (`--brief` names another; a bundle keeps its own, and
the office says so). The folder rides as it always has, the drops in its
drops/ with it.

`office start --sort` sends the drops nothing carried to a session of
their own: an office session that belongs to no folder, packed from the
office with the goal "Sort the in-tray's drops" and a brief from the
install's templates/sort-brief.md, which carries the standing
instructions, every unsorted drop between its DROP markers and the desk as
`office desk` prints it. It ships every folder's folder.md (not the
folders whole), every handbook chapter, the hung items and the doctrine,
and forecasts the notepad and the drafting table's moves page, which
arrives first when it must, the drafting table with it in an office that
has none (0.31.0), and nothing else: like
every session it writes its Sort, Questions and answers and Handbook in
notes.md, and `office land SID` files them and runs the moves. The walk-in and `office desk` show it in flight
as the in-tray's session. It is refused while another sort is out, while
an open session in the office's registry forecasts the in-tray, and when
no drop is unsorted.

Delivering to the audience is a further step, the occupant's, and one
command: `office deliver FOLDER`. It reads the folder's delivery.md,
fetches the audience's base, carries the clone's landed work to the
occupant's machine (as a git bundle through the project's shell, for a
project on a host: the audience answers with the occupant's credentials
here, not on the host), squashes it onto the audience's base in a
temporary worktree, names the applied sessions it covers and whose
folders they belong to (sessions of other folders ride in the same
delivery, said, and the occupant may stop there), runs the letterhead
check on the diff and the words (the repository's pull-request template
read from the audience's base, its lines exempt from the phrasing rule
and the three characters),
makes the commits, authored and committed as the project's declared
author, and shows each one whole as it will be pushed (its subject and
body, author and committer, its date, the files it touches and the
letterhead's verdict on it) with the diff's stat, the sessions and the
branch; several commits are dated a second apart, oldest first, so they
read in their order, and the question says in one line how many leave,
since one commit per delivery is the usual shape (0.32.0); asks
once; checks every commit's author and committer against the declared
author; and pushes that branch and nothing else, with no tag following
it. A project with an audience and no declared author is asked for it
once on a terminal, since it is a fact only the occupant knows, and keeps
it (`--author` is the twin, and sets the field); piped, deliver refuses
and names the flag; the clone's own identity is never used. The folder's
History gains a dated `delivered` line, and the review's URL is printed
where the git host's shape is known. A second delivery for the same
folder adds to the same branch.

## 5. Spaces

The floor plan (floor-plan/manifest.toml) lists the spaces an office
has, and, in its [projects] table, the projects it scopes (section 10):
each entry's `path` names its repo, on this machine or, when the entry
declares a `host` (an ssh target), as that host's shell sees it, with
the `shell` that runs one command there and the `connect` line printed
when the host does not answer. `office init` builds the base spaces. The others are added by a
renovation session when real work asks for them, except the drafting
table, whose pages hold no judgment until a sitting writes them: it
arrives with the first verb that writes it; the in-tray, which
arrives with the first `office drop`; the handbook, which arrives
with the first fact `office land` files; and the calendar, which arrives
with the first meeting `office meeting` records (0.26.0). The install's catalog of
spaces is share/spaces.toml.

| path | what it does | base | hung | filed |
|---|---|---|---|---|
| profile.md | why this office exists and the rules it keeps | yes | yes | no |
| floor-plan/ | the manifest and the site survey | yes | survey.md | no |
| desk/ | open folders: jobs in progress | yes | no | no |
| filing-cabinet/ | closed folders | yes | no | yes |
| notepad/ | the occupant's words, verbatim and dated | yes | no | yes |
| suggestion-box/ | friction slips | yes | no | no |
| drawer/ | the office's own tools: probes, survey steps | yes | no | no |
| handbook/ | the private layer of documentation | no; arrives with the first fact filed | front page | no |
| clipboards/ | retired (0.26.0): a series is a line in the calendar's plan, its items drops | renovation | no | no |
| calendar/ | when things happen, and what actually happened: the meetings | no; arrives with the first meeting | yes | no |
| rolodex/ | how to deal with each person | renovation | no | no |
| letterhead/ | how anything leaving the office must look and sound: the voice page, the forbidden list | no; arrives with the first project given an audience | no | no |
| drafting-table/ | blueprints for work too big for one folder, and the ledgers around them: rulings, evidence, watches, riders, the agenda | renovation | no | a list |
| in-tray/ | drops waiting to be sorted | no; arrives with the first drop | no | no |

Folders, desk and filing cabinet. A folder is one job: a directory named
by date and a short slug, holding folder.md (from the install's folder
template) and whatever else the job gathers. `office open` starts one on
the desk; with `--thread` it also keeps a thread pasted on stdin as
thread.md. The Next section of folder.md is what `office desk` shows as
the folder's next move. Closing a folder moves it to the filing cabinet;
reopening brings it back with its history, so the next session starts
knowing what was asked, answered and built. Moving a folder is not
rewriting it: the bytes move as they are, and git keeps the history.

Under its title a folder carries its facts as field lines, written by
the office command and never by hand: its number, its status, the day
it was queued, and whichever of class, size, lane, source, goal,
blueprint, links and gates it was given (goal, one sentence, is written
by `office open --goal` and by `office moves` from a sorted drop, and
`office start N` offers it). A field the command cannot fill is left
out rather than left blank. A field the office worked out from the
occupant's words rather than heard from him (the title, the size and the
goal of a folder opened from his words; the title and the size of one
minted for a drop) is named on one more field line, `- provisional:
title, size, goal`, after the goal: the session that works the job sends
back its own in its Structure (section 4), `office land` files each over
the provisional value and takes it off the line, and the line goes when
it names nothing. A field a flag set is his, never provisional. `office
status` names a provisional line that does not read or marks a field the
folder does not carry, and, one line each, a folder still provisional
though every session it records landed applied (0.31.0): its Structure
never came back, or came back off its shape and was not filed. The number is the folder's citation, folder
N: `office open` mints it as one more than the highest number on the
desk and in the filing cabinet, and it is never reused or renumbered. A
folder from before numbers keeps none and is cited by its name; nothing
ever numbers it after the fact. A verb that mints a number or appends to a page (a folder, a
rider, an agenda item, a blueprint, a desk move applied) refuses while an
open session in the office's own bale registry forecasts the space, page
or folder it writes, and names the session: sessions are kept apart by
bale, and scripts are kept off sessions' paper by this one-writer rule.
An office bale has never run in has no registry and nothing to refuse.

The status is one of seven. On the desk: candidate (`office open
--candidate`), queued (`office open`), open (the first session `office
sessions` records). In the filing cabinet: done (`office close`, or
`office open --filed --sid SID` for a job born done inside a session),
absorbed (`office close --into N`), split (`office close --split A,B`)
and retired (`office close --retired WHY`). An absorbed or split folder
names its successors, and each successor gets a line pointing back.
`office reopen` brings a done folder back as open; a job that lives on
in another folder, or was retired, is not reopened. Its History section
is one dated line per event, `- YYYY-MM-DD verb: text`, from a closed
set of verbs, appended and never rewritten, and the status line always
agrees with the last line that changed it (`ended`, which `office land`
writes when it ends a read-only sitting, and `withdrawn`, which `office
withdraw` writes when it closes a session never worked, change nothing). `office sessions FOLDER SID
--ratified` records that the planner ratified a session's judgment
calls, with `--except` for what was corrected and where it went; a
brief's RATIFIED line does the same through `office start` (section 4).

Gates are data on the folder that waits: `after` (do not open this
before folder N is done, a blueprint closes (its close report exists),
an agenda item is ruled on or a ruling is on the ledger), `serializes after` (never beside folder N; when both
are ready, N goes first) and `consumer` (parked for the blueprint or
folder that will carry it). The order of the desk is computed from what
the folders say, and nobody writes one. `office desk` shows, in order:
in flight, the folders some session is open for; ready, the queued
folders whose gates are all met, ordered by `serializes after`, then
size, small first, then number, each saying when a gate cleared since
the last walk-in; parked, grouped under what each waits for, headed by
that gate's own status; candidates; then the riders orphaned in a closed
folder and the desk moves not yet applied. A gate that names nothing, or a
cycle of gates, is an error line naming the folders, and no folder is
ever dropped from the desk.

Clipboards (retired, 0.26.0). A recurring meeting no longer gets a
clipboard, and none is made: its series is one line in the calendar's
plan, its running items are the drops tied to it and the folders they
became, which its next prep carries, and the work that arises is a folder
through the one door. A clipboards/ space a renovation made stays as it
is; nothing writes it.

Calendar. Series, one-offs, and a record of what actually happened: the
meetings, as a view over the work (0.26.0). Because it is hung, a session
can compare what should have happened with what was recorded and raise
one question about a gap. Times are local time in the floor plan's
timezone; bale's clock is UTC. It arrives with the first meeting `office
meeting` records, as the in-tray arrives with the first drop: its two
pages from the install's templates (calendar-plan.md, calendar-record.md),
the floor plan's entry as the catalog declares it and bale.toml's
trigger, each only when missing. Two pages hold it, one bullet per line.
calendar/plan.md says what should happen: a one-off is `- YYYY-MM-DD HH:MM
title`, a series is `- every DAY HH:MM title`, where DAY is mon to sun,
day or weekday; a meeting's line ends with what it concerns, `[about:
alpha, beta]` (`the office` for the office itself), and a line without
one concerns the office. calendar/record.md says what happened: `-
YYYY-MM-DD HH:MM title: what happened`, the time optional; for a meeting
the office writes the line, in this form, kept to the byte (values
illustrative):

  ```
  - 2026-10-26 09:00 weekly review: prep out, 2026-10-25-weekly-review-prep-001 [about: alpha, beta]
  - 2026-10-26 09:00 weekly review: held, 2026-10-25-weekly-review-prep-001; arose: in-tray/2026-10-26-update-the-report.md; dropped: in-tray/2026-10-26-call-back.md [about: alpha, beta]
  ```

`office start --prep` writes the first when the meeting's prep goes out,
and `office land` rewrites it as the second when the sitting ends (section
4); `arose:` and `dropped:` are there only when they name a drop. `office
week` lays this week's plan against the record: a planned item in the
past with no record that day starting with its title is a gap, and a
meeting whose prep is out says so. Bullets that fit neither shape are
reported, never dropped. An office without a calendar is told that it
arrives with the first meeting.

Handbook. Only the private layer. Shareable technical documentation
belongs in the projects (README, docs/), and a chapter points at it
rather than restating it. One chapter per project, handbook/PROJECT.md,
in two parts (values illustrative):

  ```
  # alpha

  ## Front sheet

  <for the occupant, in plain language: what the project is and where it stands; replaced whole by a session's Front sheet>

  ## Facts

  - 2026-10-14: the login page is served by the api's static route (2026-10-14-alpha-login-error-001)
  ```

The front sheet is for the occupant, in plain language, and a session's
`#### Front sheet` replaces it whole. The facts are for sessions: one
line each, dated and naming the session that gave it, appended at the end
by `office land` from a session's Handbook section or a Sort's `facts:`,
and never rewritten by hand. Every session that lands a change to a
system updates that chapter's front sheet, through its notes.md. The
handbook arrives with the first fact `office land` files, as the in-tray
arrives with the first drop: its front page from the install's template,
the floor plan's entry as the catalog declares it with the front page
hung, and bale.toml's trigger and pull, committed with that filing; a
chapter arrives from its template with its project's first fact. A
chapter rides with every session whose lane names its project, and every
chapter rides with the standalone sort. `office status` checks a handbook
that exists against the catalog, and every chapter against its shape.
The handbook is live, never filed. Correspondence, including copies of
messages sent, is the folder's, not the handbook's.

Rolodex. One card per person, as a guide for responding to them.

Letterhead. The rules for anything that leaves the office: code style,
prose style, what must never appear, and the occupant's voice. Three
pages, from the install's templates (0.25.0): README.md, its front page;
voice.md, the voice page, the occupant's style rule for text that leaves
the office, in his words, which the template carries as an empty place
plainly marked (`<!-- EMPTY: ... -->`) and office-src never writes; and
forbidden.txt, the forbidden list, one fixed string per line, refused by
the letterhead check. In an office that has a letterhead the check also
refuses three characters by default, with no line in the office needed
to turn it on: the em dash (U+2014), the en dash (U+2013) and the
ellipsis character (U+2026), each named in a refusal by its name, as the
check names its other refusals. The forbidden list lifts one with a line
of its own, in this form, kept to the byte but for case and spacing
(values illustrative):

  ```
  lift: em dash
  lift: en dash
  lift: ellipsis
  ```

and every check that reads a lift says so; a lift that names anything
else stops the check, said. A repository's own pull-request template is
not the occupant's writing: when words fill it, each line that is a line
of one of the repository's templates as the repository holds it (the
audience's base, for a delivery; HEAD, for the check by hand) is not held
to the phrasing rule or to the three characters (0.26.0), while names,
bale's marks and the forbidden list read it, and the lines the words add,
or a template line changed, are held to all of it. A checklist line is
the template's whatever its box holds (0.32.0): `- [x]`, `- [X]` and
`- [ ]` read as one, so ticking a box changes no line, and words added
after the box do. Which files
are templates is read from the repository, by the places git hosts look
for one (GitHub's, GitLab's and Azure DevOps'). The list's template names the three as
present by default. The letterhead arrives with the first project given
an audience (`office projects add` or `set --audience`), as the in-tray
arrives with the first drop: its pages from the install's templates, the
floor plan's entry as the catalog declares it and bale.toml's trigger,
each only when missing, committed alone. A letterhead from an earlier
release gets the voice page's place through `office upgrade`, which
writes a missing page and never rewrites one, and `office status` names
its absence, and a voice page that holds no words yet, with the line
that adds it; an office that has a project with an audience and no
letterhead is named the same way. No hand writes these pages but the
occupant's words in the voice page, through a session in the office.

Drafting table. Blueprints for work too big for one folder, one arc
each, with the ledgers a planning sitting rules in: the rulings ledger,
the evidence ledger, the watches register and its log, the riders page,
the agenda, and the desk moves a sitting decided. The space is part
live, part filed: the ledgers, the watch log and the close reports are
filed paper, and the floor plan lists them. It arrives in an office
with the first verb that writes it, never by hand and never by a
migration: its front page from the install's template, the floor
plan's entry as the catalog declares it and bale.toml's trigger, and
each page from its template on its first write, committed with the
write that asked for it. `office status` checks a drafting table that
exists against the catalog.

Who writes what there. A sitting writes the drafting table directly: a
blueprint, its ratified line and its close report, rulings, evidence,
watches and their log, agenda changes, riders and desk moves. The
office command writes what a script can: `office blueprint open` drafts
a blueprint, `office blueprint ratify` writes the ratified line given
outside a sitting, `office rider add`, `carry` and `consumed` keep the
riders, `office agenda add` puts a question on the agenda, and `office
moves` applies the desk moves and the in-tray's sorted drops, since the
desk is the office command's to write and folder numbers are minted by it
alone. No script mints a
ruling or an evidence entry: those are judgment. `office blueprint
close` sends out the sitting that closes an arc. `office rulings`,
`office evidence`, `office riders` and `office watches` only read.

A blueprint's charter freezes once its ratified line is written; `office
status` checks its bytes against git from the ratifying commit on, and
a charter that must change is a new blueprint whose History opens
`supersedes: blueprint ID`. A blueprint states no order: its member
folders' gates do, and `office desk --blueprint ID` renders it. A
blueprint is closed when its close report exists. A rider is on the
riders page or in exactly one folder's Riders section, never both;
carrying it leaves one pointer line on the page, and a rider in a closed
folder that was never consumed is an orphan, which the desk reports. An
agenda item leaves the agenda when a sitting rules on it, and a dated
line at the foot of the page says which ruling disposed of it. A desk
move is one line of data, `- [ ] DATE MOVE ...`, ticked with the folder
it acted on once applied; walking in says how many are pending and which
session wrote them. A sorted drop still in the in-tray is a desk move too
(section 5, In-tray), counted with them and applied first, and the
standalone sort writes the moves page as a sitting does: a finished
folder's close is `- [ ] DATE close folder N`, a job that lives on in
another `- [ ] DATE absorb folder N into="folder M"`, one that ends
undone `- [ ] DATE retire folder N why="..."`. Every pointer uses one citation form per kind of
thing (folder N, blueprint ID, ruling ID, evidence N, watch WN, rider N,
agenda N, a session id, a notepad page), and `office rulings --check`
resolves them all.

A fact lands once, on the folder, blueprint or ledger record it belongs to,
and everything else cites it by id; the same fact restated in two
records is a defect. A ruling on the ledger is reopened only by a
sitting that names it, and a reopening is a new ruling that supersedes;
the earlier record is never touched. The evidence ledger admits only
what live traffic earned: a record names a session id or a notepad
page, or it is refused. An eye-watch no sitting has looked at is
reported, never silently aged. Closed blueprints stay on the table;
nothing is condensed.

The watches register and the digest. A watch is a named re-trigger with
no work attached: one entry on watches.md, its state never edited into
it, every event a record on the watch log. A watch evaluates a query or
an eye. A query is named once, in the install's
share/watch-queries.toml (the bale surface it reads, the value it
extracts, how it compares), and an entry names a query and a threshold,
never a command line. `office watches check` runs every open query
watch over the window since its last fired record, for the office's own
registry and for each project, and says of each: fired, not fired, or
cannot evaluate; a query bale cannot answer says so, as cannot evaluate,
never as not fired. It prints every eye watch as needing an eye, with
the sittings since its last record, and the standing lines, which are
observations, not watches. `office land` runs it after an applied
landing, without recording, and prints only the watches that fired. With `--record` it appends a fired record
for each watch that fired; re-arming, rewording, closing and a not-fired
record are a sitting's. `office digest` writes digest.md, the page a
sitting opens on: versions, what happened since the last sitting, the
watches, the standing lines, the desk, the in-tray (each unsorted drop by
its page's file name, with the project it names when it names one: the
office's name for it when its words resolve to one of the office's
projects, else the words as given; "none" when the in-tray is empty or
not there), the agenda and the open blueprints, every line computed when
it runs. The last sitting is the
latest sitting's page in the notepad, by the commit that filed it, and
the page says so. The digest is overwritten on every run and never
edited by hand, and `office start` writes it again before it packs a
sitting, which ships the drafting table.

In-tray. Drops waiting to be sorted: a message or a thread, one page
each, in-tray/DATE-SLUG.md. `office drop` captures one, instant and
dumb: from the clipboard, a file or stdin, with one optional question,
the project, in any words; it never refuses a drop it can write, and,
like a note, it works in an unfounded office and in one out of step with
the install, and only warns. A text that is one office command line (one
non-blank line beginning `office `) is asked about once, before anything
is written, when it came from the clipboard, since the clipboard then held
the command just copied and not the message: drop it anyway, no by default
(`--anyway` is the twin), and a yes writes it; from a file or stdin it is
written as given, and the line saying what the drop took says it is an
office command line (0.32.0). The in-tray arrives with the first drop,
as the drafting table arrives with the first verb that writes it: its
front page from the install's template, the floor plan's entry as the
catalog declares it and bale.toml's trigger, committed with that drop.
It is neither hung nor filed: its pages are live. A drop's page is its
first line as the heading, `# Drop: ...` (trimmed to 60 characters),
four field lines, `- dropped: DATE TIME`, `- project:` (the free text
as given, or `none given`), `- via:` (`clipboard`, `stdin` or `file
NAME`) and `- status:` (`unsorted` when it lands, `sorted` once a Sort
has been filed under it), and then `## Text`, the text verbatim, kept
ASCII as a note is. Only the office command writes the field lines,
never a hand, as with a folder's. Every session `office start` sends out
carries the unsorted drops, and a session sorts what it can judge
(section 4). A sorted drop leaves the in-tray whole, its bytes as they
are, into the folder it became, as drops/DATE-SLUG.md. When a session's Sort
lands, `office land` files it on the page as a section at its end, the
first line the office's and the rest the session's subsection, verbatim
and in its order, with `### Brief` exactly when the subsection had
`#### Brief` (values illustrative):

  ```
  ## Sort

  - sorted: 2026-10-14, by 2026-10-14-alpha-login-error-001
  - project: alpha
  - folder: new
  - goal: Fix the login page's error on narrow screens
  - size: small
  - tell: the sender, in reply: fixed in the next release
  - facts: none

  ### Brief

  <the subsection's Brief, verbatim>
  ```

and the page's status becomes sorted, written by the office command as
every field line is. A sorted page still in the in-tray is a desk move:
`office moves` applies it, before the moves page. For `folder: new` it
mints the folder through `office open`'s own code (the title from the
page's heading, the slug from its name, the lane the Sort's project,
which must be one of the office's or the page stays, the size and the
goal the Sort's, the source `drop`); for `folder: N`, folder N on the desk
(one in the filing cabinet is said and the page stays). The page moves in
whole, the folder's brief.md is written from the Brief (its text, nothing
added), the History gains `- DATE dropped: drops/NAME.md, sorted by SID`,
the goal is written when the folder has none, and the `tell:` goes on the
folder's Next, which `office desk` shows, and which the next meeting on
the folder's project reads in its prep, the folder's page riding with it
(0.26.0).
An open session forecasting the in-tray, the desk or the folder stops that
page's move, named, and the rest go on. Fact lines in a Sort follow an
empty `- facts:` line, one `- ` line each. `office start
--drop in-tray/PAGE` is the direct path for a drop whose job is plain:
it mints the folder through `office open`'s own code (the title from the
drop's first line, the lane from its project when that is one of the
office's, else asked by key; the size small; the source `drop`), moves
the page into the folder, writes `- DATE dropped:
drops/DATE-SLUG.md, via ...` in its History before the `opened` line,
and sends a project session out on the lane's project, whose brief tells
it to sort the drop first and do the work second. It holds the one-writer
rule: while an open session in the office's registry forecasts the
in-tray or the desk, it refuses and names the session. `office status`
checks an in-tray that exists against the catalog and every page
against this shape.

Notepad. The occupant's words, verbatim and dated. Never edited.
Structuring them into folders, cards and chapters is cleanup's job.
`office note` appends a timed line to the day's page, notepad/DATE.md;
a sitting's words are filed as their own page, notepad/DATE-SLUG.md. A
read-only sitting lands nothing itself, so the brief of a session it
authors carries its page between two marker lines, `--- NOTEPAD PAGE
BEGIN notepad/DATE-SLUG.md ---` and `--- NOTEPAD PAGE END ---`, and
`office start` files it when it sends that session out, an office
session or a project session, and commits that page alone. A page
already filed with the same words is left as it is; a different page at
its path is refused loudly and never overwritten.
Capture is instant: it works in an unfounded office and in one behind or
ahead of the installed tool, and only warns. Anything outside ASCII is
kept as a backslash escape, so the office stays ASCII and no word is lost.

Drawer. The office's own tools. The office command itself lives in the
install, never here. Survey steps the office adds live in drawer/survey/
(section 13).

Suggestion box. Any session, and the occupant, can drop a slip when
something causes friction. Routine slips are handled by cleanup, design
slips by renovation. A slip about a tool (bale, office-src) says so, so
it can be carried to that tool's project. `office slip` drops one: each
slip is its own page, suggestion-box/DATE-SLUG.md, saying what it is
about (the office, a tool or one of the office's projects) and committed
on its own. Like a note it is instant and dumb: it works in an unfounded
office and one behind or ahead of the installed tool, and only warns.

## 6. Hanging, and what every office session ships

An item is hung when every session in the office needs it. The floor
plan marks hung items per space: true for a whole space, or a list of
paths inside it. The office's bale.toml carries them to bale as an
include group: its triggers are the office's spaces and its pulls are the
hung items, so any pack whose includes touch the office ships them
without a list on the pack line. `office init` writes it; a renovation
that adds a space or hangs an item updates it, as does the drafting table's arrival; `office status`
reports when it no longer matches the floor plan. Every office session ships:

- this doctrine, as a context tarball from the install, once: a session
  whose packed tree carries the same doctrine/ (office-src's own) reads
  it there, and one whose tree carries a different doctrine/ gets the
  install's beside it, named as the install's, since that is the
  doctrine the office runs on;
- the office's hung items: at least profile.md and floor-plan/survey.md;
- whatever its verb names in the install's verb declarations.

A session may always write the notepad and the suggestion box.

## 7. Verbs

Verbs declare what a session ships and where it lands. office-src runs
bale's pack and apply when the occupant asks, as the occupant's hands at
the terminal: `office start` packs, and `office land` applies, or, for a
read-only sitting the office sent out, ends it with bale's unlock; `office
withdraw` closes a session sent out and never worked with the same unlock,
bale's reason `abandoned` given. It never
schedules a session, never
dispatches one to a model and never carries pastes, so whoever carries
sessions (the occupant, bale, a future harness) can change freely
without the office changing. The declarations are share/verbs.toml in
the install.

Kinds:

- script: the office command alone, in seconds. No session, no network.
- office session: packed from the office, lands in the office.
- project session: packed from a project, lands there; the office's
  context rides beside it (section 4).

| verb | kind | built | surface |
|---|---|---|---|
| init | script; writes bale.toml, asks which projects the office watches, asks the profile's questions, opens the founding folder and sends the founding session out through start | yes | occupant |
| found | script: the founding door for an office that exists: the profile's questions (only what the founding folder does not keep), the founding folder, the founding session out through start | yes | plumbing |
| survey | script | yes | plumbing |
| status | script, read-only: the office against the install, and (0.25.0) the letterhead, its voice page and each audience clone's push guard, an older one named with the line that replaces it | yes | plumbing |
| upgrade | script; when a migration needs judgment, opens its folder and sends the renovation session out through start; with or without a migration, brings the letterhead's missing pages and the current push guard (0.25.0) | yes | plumbing |
| where, default | script: which office a command acts on | yes | plumbing |
| note | script: append a dated line to the notepad | yes | occupant |
| slip | script: drop a friction slip in the suggestion box, saying what it is about | yes | occupant |
| drop | script: capture a message or a thread as one in-tray page, with an optional free-text project; while a meeting is on with its prep out, tied to that meeting in the calendar's record | yes | occupant |
| meeting | script (0.26.0): a meeting, said once in the occupant's words, when it happens and what it concerns, asked only when his words do not say when or name none of the office's projects (--words, --when, --about PROJECT, --in-office the twins); one line in the calendar's plan, a series never asked for again; the calendar arrives with the first; no folder | yes | occupant |
| open | script: start a numbered folder on the desk, or a candidate, or one born done in the filing cabinet; on a terminal, from the occupant's words (the title, the Asked section and the goal office start takes, each worked-out field marked provisional); with --goal, the goal; the code office start new mints a folder through | yes | plumbing |
| desk | script: in flight, ready in order, parked under what each waits for, candidates | yes | occupant |
| week | script: this week's calendar and its gaps, and a meeting whose prep is out | yes | plumbing |
| close | script: move a folder to the filing cabinet, done, absorbed, split or retired | yes | occupant |
| reopen | script: move a done folder back to the desk | yes | plumbing |
| sessions | script: list or record the sessions that worked on a folder, and the planner's ratification of one | yes | plumbing |
| projects | script: list the projects this office scopes, add one (here, or on a host, prepared for bale without a trace, a clone here brought there with --from), declare where it is, what rides with it and what runs after it lands, bring a host's bale level with this machine's (level-bale), render what bale records about them; a project with an audience is worked from a guarded clone on this machine, a host declared for it recorded as where it validates (validates_on), and the first one brings the letterhead | yes | occupant |
| start | script: the one door for new work: with new, a job from the occupant's words (--words the twin), its folder minted through open's code and its session sent out in one motion; bare on a terminal, offer the planner's bundles in the downloads no session has opened, by key, and send a bundle whose brief carries a LANDS line where it says, asking neither where nor which job; with --planner, a read-only planner sitting from the occupant's words (--words, --about PROJECT or --in-office the twins), its folder minted or picked by key, what rides gathered and said in its brief; before any sitting, the in-tray's sort offered first when drops wait (--sort-first, --no-sort-first); pack a session for a folder, in the office or on a project (on its host, when it has one, the request carried back), or open a planner's bundle (asking bale open --check first, before anything is written); carry the riders its forecast touches into the folder; carry the in-tray's unsorted drops with every session it sends out; with --drop, send a dropped message straight out as a project session, its folder minted through open's code; with --sort, send the standalone sort; with --prep, a meeting's prep, recorded in the calendar and in no folder; send a folder out with its goal and brief.md when it has them; record it in the folder, file the sitting's page and the planner's ratifications its brief carries, gather what to attach in one out tray, and put the opener on the clipboard last | yes | occupant |
| land | script: bring a session back: bale's apply in its repo, how it ended, the folder's walkthrough and delivery pages filed from the response, then its Sort on each drop's page, its questions and answers in the folder, its facts in the handbook and its Structure over the folder's provisional fields, and office moves when a drop was sorted, on a project with an audience the letterhead's review of what landed (what deliver would refuse, said, nothing refused), the project's after-land actions, the folder closed when its one session landed and the founding folder when the founding has, the watches that fired, what became of each action, and last the relay to carry on the clipboard; it asks nothing about ratification; or end a read-only sitting the office sent out, and for a meeting's prep record the meeting held and file what arose as drops (--arising FILE) | yes | occupant |
| withdraw | script: close a session the office sent out and that was never worked (no response in the downloads, no apply begun), named by its folder and asked once (--yes the twin): bale's unlock with reason abandoned where it is open, and a withdrawn line in its folder's History; a folder that recorded it alone is said with the line that closes it | yes | occupant |
| relay | script: carry a planner's answer to a clarification back to the repo the session is open in (bale relay there, the answer piped through the project's shell for a hosted one), and hand over the block bale prints | yes | plumbing |
| probe | script: run a worker's probe block where a folder's project lives (its repo, through its shell on a host, or the office root), for the folder's session open there or, with --project, a read-only sitting of its open in the office, under the sitting's id, stdin closed, once its purpose header has been shown and the occupant said yes; refuse by name a block with no PROBE BEGIN line or a header that does not say it is read-only; hand the output back whole, the block on the clipboard, a fallback's probe-output/ carried to the session's out tray, and a History line in the folder | yes | plumbing |
| deliver | script: carry a folder's landed work to its project's audience as a delivery branch of curated commits, the words from the folder's delivery.md, checked by the letterhead, each commit shown whole and asked once, authored and committed as the declared author (asked once and kept when none is declared, --author the twin), recorded in the folder | yes | occupant |
| letterhead check | script, read-only: name every line in a tree, a range or a file that holds what the letterhead refuses (in an office with a letterhead, the dashes and the ellipsis by default, a lift said; a pull-request template's lines exempt from the phrasing rule and the three characters) | yes | plumbing |
| tour | script: build a throwaway office in a temporary directory, walk through the verbs on it, and delete it; runs no bale and touches no real office | yes | occupant |
| moves | script: apply the in-tray's sorted drops (a folder minted through open's code for folder: new, or folder N; the page moved in whole with its brief, its History line, its goal and its tell), then the desk moves a sitting or a sort wrote, through open's, close's and the gate flags' own code, ticking each and writing a minted number onto its blueprint's decomposition line; stops at the first line it cannot apply | yes | plumbing |
| blueprint open, blueprint ratify | script: draft a blueprint from the template; write its charter's ratified line | yes | plumbing |
| rider add, rider carry, rider consumed | script: a rider on the riders page; moved into the folder that carries it; consumed at a session | yes | plumbing |
| riders | script, read-only: the riders, where each is, the orphans, and the ones a pack's forecast would carry | yes | plumbing |
| agenda add | script: a question on the agenda for a sitting to rule on | yes | plumbing |
| rulings, evidence | script, read-only: the ledgers, one record with what points at it, and every citation resolved | yes | plumbing |
| watches, watches check | script: the watches and where each stands, read from the log; run every query watch over its window and the standing lines, and with --record append a fired record for each that fired | yes | plumbing |
| digest | script: write the sitting-open page, every section computed; office start runs it before it packs a sitting | yes | plumbing |
| founding | office session: the profile, the occupant's words, the timezone | yes, via init, found and start | session |
| work | office session: answer, draft, probe, decide, deliver | yes, via start | session |
| build | project session: change a project for a folder, and write the folder's walkthrough and delivery pages at the end of its notes.md | yes, via start | session |
| sort | office session: the standalone sort, belonging to no folder: read every unsorted drop, write one Sort subsection each, a Brief for every new folder, facts in a Handbook section and, with a drafting table, the moves the desk needs on its moves page | yes, via start | session |
| prep | office session (0.26.0): a meeting's prep, a read-only sitting from the office that briefs the occupant from what landed on the meeting's projects since the last meeting on them and serves during the meeting, held open until office land ends it; no folder; what arose filed as drops when it ends | yes, via start --prep and the home screen | session |
| cleanup | office session: keep the office as designed; the cleanup built is one a meeting's prep may offer for its projects' documentation, a planner's bundle beside the briefing with its LANDS line, sent or deleted by the occupant (0.26.0); a scheduled, unattended cleanup of the office is not yet | the prep's offered bundle, yes; the scheduled kind, not yet | session |
| blueprint close | office session: a sitting scoped to one blueprint, landing its close report and a notepad page | yes, via office blueprint close | plumbing |
| renovate | office session: change the design | by hand | session |

Session verbs are done by hand a few times before the command learns
them.

A verb is a wizard on a terminal. It walks the occupant through
whatever it was not given, and it explains an argument it does not
understand rather than refusing it. The rule every wizard keeps: the
occupant supplies words; the session supplies structure. A verb asks him
only for what only he knows: the ask, in his words; which project, and
only when the office cannot tell; yes or no on anything that cannot be
undone; and what only his eyes can check. Everything else the office
computes, or leaves provisional for a session to set. So a folder is
opened from his words: its title is their first line, trimmed as a
drop's heading is, its slug comes from the title, the words are kept in
the folder's Asked section and, as one line, are the goal `office start`
takes; the size is small and the source is where the words came from
(the occupant, a drop, a planner's bundle); the title, size and goal it
worked out are marked provisional on the folder, and the session that
works the job sends back its own (section 4, the Structure). Where a session's work lands is the folder's lane, what it
will change is the session's to forecast, what rides with a project
rides as declared, and a rider whose path the forecast touches is
carried; each is said, never asked. A choice among things the office
knows (a folder, a session, a project, a bundle, a copy in the downloads)
is offered by key, never refused for being ambiguous, and nothing he acts
on is named by an id or a file name for him to type. Every question a
verb asks has a flag twin, and every value a flag gives is taken as
given, so the same invocation can be typed in full without being asked
anything. With piped input a verb never asks: it refuses what it was not
given and names the flag, as before. The verbs ask the same way: each
question names its flag, offers its default or its keys, explains the
field when the answer is `?`, and asks again, with the reason, when an
answer is not one the field takes. A plain return skips a question that
may be skipped.

An answer in his words that may run to several lines (a new job's, a
planner sitting's, a profile question's) ends on a blank line, and a line
already ended cannot be edited at a terminal's prompt. So before anything
is written or packed the whole answer is shown back, numbered, with one
question (0.33.0): keep it, the default; redo it from its first line;
more, for lines after the last; or a line's number, to type that line
again (a blank one takes it out). The question names the answer's flag
twin, `?` explains it, and piped input never reaches it. With VISUAL or
EDITOR set and the terminal his, the answer is taken in that editor
instead, as git takes a commit message: a scratch file seeded with the
question and its explanation as comment lines, read back less them and
less blank lines; he saw the whole there, so it is not shown back. An
editor that fails, or comes back empty where an answer is needed, is said,
and the answer is asked at the prompt.

The verbs are on two surfaces, which the table above names and
share/verbs.toml declares. The occupant's own (`occupant`) are the home
screen and what he uses: the two instant captures (`office note`,
`office drop`), the friction slip, a new job from his words with its
session out (`office start new`, the one door), a planner sitting from
his words (`office start --planner`), a meeting from his words (`office
meeting`), sending a job on the desk out and
bringing a session back (`office start`, `office land`), withdrawing one
never worked (`office withdraw`), the desk, closing a job, delivering it,
adding a project, the tour and a new office. `office help` lists them, one line each in plain words, with a
line on what a folder is and what a project is. Everything else is the
plumbing the office and its sessions use, which a session names in full
when it needs him to run one; `office help --all` lists every verb by
what it is for (look around, capture, start a job, send a session out,
bring one back, look after the office). Every verb works the same on
either surface, and every verb's `--help` carries at least one example.

A session whose goal the occupant overrides midway keeps the override
words on its notepad page, and the new ask becomes a new folder or
blueprint, never an exception counted against the old one.

Walking in is `office` with no verb, from inside an office or anywhere on
the machine (the per-machine default). On a terminal (its input and its
output both) it is the home screen. It shows the office's name, the date
and time in its timezone, whether it is founded and current, and the
install's and the suite's lines when they apply, as the page does; then
each project the office scopes, one line each, saying what is in flight
on it, or what last landed and when (bale's status names the latest
session it applied, and its record when), and the office itself when a
session is open there; the desk in one line (how many jobs are in
flight, ready, parked and candidates); then what waits on the occupant, each thing with
a key: the page's Next move first, marked, then a response in the
downloads for a session that is out, a planner's bundle in the downloads
no session has opened, each unsorted drop and the sort, the desk moves
a sitting decided, an office out of step with the install, and a
read-only sitting a folder records, which only he can say is over; a
meeting near now whose prep has not gone out comes right after the Next
line's move, and a meeting's prep that is out comes last, ended by its
key (0.26.0). A session is named by its folder, never by its id (a prep
by its meeting). Keys for a new job, a planner sitting from his words (p),
a meeting in his words (m), sending a session out, bringing one back
(while a session is out), a note, a drop, the whole desk and help are
always there, and a key that withdraws a session never worked (w)
while one is out with no response and no apply begun. Choosing a key runs the code the verb
already runs, with its arguments filled in, as a command of its own,
and asks only what that verb must; when it ends, a key brings the home
screen back, worked out again, and q leaves. It asks once, the first
time, where this machine's downloads land. Off a terminal (piped, under
a test or a session) walking in is the page. It shows the office's name, the
date and time in its timezone (and, when the floor plan's zone does not
resolve, that the office is on UTC instead), whether it is founded and
current, a line saying the install is behind its source when the office
scopes the project the install came from and that project has moved past
the installed commit (in the words `office status` uses), a line saying
the install's bytecode cache is not level for the python3 that runs it,
in any office, in status's words too (0.31.0), the sessions in flight in its projects and in the office
itself, with the folder each belongs to (a read-only sitting a folder
records says that `office land SID` ends it when the sitting is over,
and, when its Sessions line stamps a doctrine that is not the install's,
that it is out under an older one, both short hashes named (0.33.0);
the Next line never names one, since nothing in the office knows when a
sitting is over), how many folders are ready, parked and
candidates, and the first three ready ones with their next moves, how
many desk moves a sitting wrote are pending and which session wrote
them, how many riders are orphaned, when the in-tray holds unsorted
drops how many and the oldest's age in days (`office desk` lists each
after the candidates: its page's name, its project or `no project`, and
its first line), this week and its gaps, the last notepad lines, how many slips are in the
suggestion box, and the verbs to reach for. Where the office scopes the
source the install came from, a `Suite:` line, under the install line,
gives the latest detached run of that source's suite (`tests/run.sh
--detach`) whenever it is not OK, a run still going after an hour
included. It ends with one Next line:
the one command to type now, its arguments filled in, worked out from the
office on every walk-in and never written down. In the order they win: an
office out of step with the install (upgrade it, or, when the renovation
upgrade sent out is out, land that first); the install behind its source,
when the office scopes that source (bring it level with the source's
`./install.sh`: start and land run the install, so until it is level they
run the old office; placed here in 0.13.0, ahead of a session out); the
install's bytecode cache not level, when its stamp names the source
(the same `./install.sh`: until it runs every command, a land included,
compiles the helpers from source and takes about twice as long; placed
here in 0.31.0); a session out (land it,
or, when bale held it, land its corrected response); desk moves a sitting
decided that have not run (run them: until then the desk is not in the
order the sitting decided); an unsorted drop (the oldest whose project
is one of the office's, with no session in flight on a folder of that
lane: `office start --drop in-tray/PAGE`; the oldest whose project is
none of the office's, or that has none: the same line with `--lane
LANE` for the occupant to fill; an office that scopes no project skips
it; placed here in 0.19.0, since drop, start, land is a routine ask's
whole count); an unsorted drop whose project is none,
or none of the office's, that has waited through one session (a session
packed after the drop landed), or an in-tray of three or more unsorted
drops with nothing ready on the desk (`office start --sort`; the drop
rule above leaves such a drop to it; placed here in 0.20.0); an
unfounded office (start its founding
folder, which goes out through the founding door with the answers it
keeps, or, with none on the desk, found it); the first ready folder
(start it); an open folder no session is out for;
no projects (add one); slips enough to be a job of their own; folders
that wait; and nothing to do. Whether a response has arrived is bale's to
say, and no --json surface of bale says it, so the line says the session
is out and that land finds its response. It only reads the office;
the one thing it keeps is the day of the walk-in, on this machine and
outside the office, so the desk can say which gates cleared since.

## 8. When to open a session

A session is worth opening when a job needs one of these:

- judgment in context;
- a message in the occupant's voice to someone who matters;
- more than a few lines of code;
- drill-down into a system.

Otherwise the occupant does the work and leaves a trace: office note for
a conversation or decision, a commit for code. Cleanup reads notes and
git logs, including commits no session made, and keeps folders and
chapters current.

That is the shape. Each profile sets its own threshold inside it: an
office where every session costs a long round trip opens fewer; an office
for personal research may open one for any question worth keeping.

## 10. bale and the office

bale is how a session works at all: what is handed over, what comes
back, and the checks before anything lands. Every session opened from an
office is a bale session. The line between the two, as settled:

The line between bale and office. Test: is this about a session or about
a job? bale records everything from pack to close inside one repo,
including lineage between sessions. The office records the person and
the job across repos and time: why a session was opened, the planner's
words, what was decided, what is next, which sessions belong to which
job. A folder points at session ids; it never copies what bale records.
Where bale lacks a session-shaped fact, that is a slip for bale-src, not
an office workaround. Two bale doctrine limits bind: bale is "not a
master-changelog system" (AGENT.md section 7), and a dashboard "renders
the stats; it never owns them" (PLANNER.md section 17).

The office reads bale's records and renders them. Reading is not
copying: a rendering is derived, recomputed on every run, never edited,
and never cited as a source -- a citation names the sid, and the
rendering is how a reader follows it. A rendering written to a page (the
digest) is overwritten on every run, like the survey.

Where a report and the records it summarizes part, the records stand,
and the difference is written down, never smoothed.

The projects an office scopes are its floor plan's [projects] table: a
name and the path of each project's repo, absolute or under a home
directory, written by `office projects add` and never by hand; `office
init` asks which projects a new office watches and adds each through the
same questions. An office with no table scopes nothing, and every
rendering says so rather than showing an empty screen as if it were
true. A project's repo is on this machine, or on another host: a project
declares its host and the shell that reaches it (`host`, an ssh target;
`shell`, the command prefix that runs one command where the repo is,
through a container when the repo sits inside one, to which the office
appends exactly one shell-quoted command; `connect`, the occupant's own
words for what brings the host up), its path is then the path as that
shell sees it, and the office reads it through that shell: bale's
--json surfaces and the commit subjects run there, in the project's
path, with the same keys and the same consumption manifest, and
`OFFICE_DEBUG=1` shows every shell call as it shows every bale call.
Reach is checked where it matters: before any step that needs the host,
one connection with a short timeout, never a prompt; a host that does
not answer is one line naming the project, the host, the connect text
and the command to rerun, and the command stops there, while the
walk-in and `office status` print that line in the project's place and
render the rest. A host checked once in a command is not checked again
in it, by any of the command's steps: the reach is carried from one
step to the next, and the reads a step needs there travel in one
connection. The survey makes no network call (section 13); `office status`
is where a host is reached, and it says which bale answers there against
the read side's floor, naming the step that brings it level when it is
behind. bale is installed per machine, like git, and a hosted project's
bale lives on its host: `office projects level-bale NAME` installs there
the bale the occupant's machine runs, the way bale's own releases
install (a release tarball of the install, carried through the shell,
and the host's own upgrade.sh, which keeps the host's per-install
settings), fetching nothing from the network there, and says what
version was there and what is there now. It runs only when the occupant
asks: `office start` and `office land` never upgrade a bale on their
own, and refuse a host whose bale is below the read side's floor,
naming that step. `office start` sends a session to a project on a host
(section 4): the host is reached first, and one that does not answer
stops the start before anything is written, with the connect line; a
step bale asks the occupant about runs through the attended form of the
project's shell, a terminal asked for at each layer (`ssh -tt`, a
container's `-it`), and piped, nothing ever asks. `office land` brings
it back the same way (section 4): the host is reached first, the
response is carried there from the occupant's machine, and apply,
retry, relay and unlock run there, in the project's repo. Where the
occupant's downloads land is the office's own setting, machine.toml's
`downloads`; the office never reads bale's config to learn it, since
bale's settings are bale's and its `--json` surfaces do not list its
search directories (a slip for bale-src). A clone on the occupant's machine is moved
to its host as the project's repo by `office projects add --from`: every
branch and tag and the remotes as the clone has them, carried from the
occupant's machine, since the host may not reach the audience's git
host; nothing of the clone's uncommitted work travels, and the clone it
came from is never changed or deleted by the office. The office reads
each project's records only through bale's --json surfaces, run in the
project's directory with no prompt, never by parsing .bale/, and it
never writes what bale records. A clone bale has not run in is prepared
for bale without a trace (`office projects add --prepare`, offered on a
terminal): the paths bale makes are excluded through the repo's
.git/info/exclude, never its .gitignore, which belongs to its audience;
what the office writes into a project's working copy is only ever
outside what git tracks. The verbs that run bale to make or land a session do so with
the occupant at the terminal (pack and open in `office start`, which
first asks `bale open --check`, a rehearsal that writes nothing, whether
a bundle can open before it writes anything of its own; apply,
retry and relay in `office land`, and unlock when `office land` ends a
read-only sitting the office sent out or `office withdraw` closes a session
the office sent out that was never worked, with bale's reason `abandoned`
given, and no other session): a question
bale asks is his to answer, and
where bale prints a block for him to carry and no --json key holds it,
the office takes the lines between the markers the manifest below
declares. The install's share/bale-consumption.toml names every bale verb,
flag and key the office reads or runs and the bale version they were
written against; `office status` reports a bale outside that range. What it
renders: on the walk-in, the sessions in flight and the folder each
belongs to; in `office sessions FOLDER`, each session with its outcome,
dates, claims beside verdicts and exchange rounds; in `office projects`,
the trust ledger per work class (the evidence a trust grant would be made
on; the office holds no grant), the last applied session that landed a
path, and the version trail; in `office watches check` and the digest,
each watch's query and the standing lines, from bale's stats surface,
whole or narrowed to the sessions packed since a day (its --since form,
which takes a day and not an instant). Wherever a count the records
compute sits beside one written down, both are printed.

The watch queries are data in the install, share/watch-queries.toml,
written from a probe of the installed bale and held to the consumption
manifest: a query reads only keys the manifest declares. Where bale does
not stamp the datum a watch needs, the query says what is missing, the
check says it cannot evaluate, and the missing datum is a slip for
bale-src. The office also reads the subjects bale gives the commits it
makes (a session's work, its merge, its sweep), to name the session that
wrote a line and to find the sessions that closed since a sitting before
reading each one's outcome from its dossier; the manifest declares that
shape too, though bale keeps it as a habit and not as a contract.

Each project's entry may also declare two things: `rides`, the other
paths whose context rides beside every session on the project (a
directory inside another repo, a whole repo, or a file), and
`after_land`, the commands run in the project's repo after one of its
sessions lands: `office land` runs them in order once bale has applied
the session, never after a HOLD, and says loudly when one fails, with
the line that runs it again; its last lines say what became of each
action (ran, failed, not run), or that the project declares none. The
actions run only through `office land`: a session applied by hand with
bale apply runs none, and `office status` says when the install has
fallen behind the working copy it was installed from. Both are set by
`office projects add` and
`office projects set`, a wizard with flag twins, as the host keys are,
and never by hand or in
the project's own repo: what rides is office context, and a project's
audience must not see the office's choices. A table without them is
valid.

A project with an audience declares three more things, the audience
line's (`office projects add` and `set`, the same wizard with flag
twins): `audience`, the name of the remote in the workbench clone that
points at the audience's git host (a project with none, home-office's
say, leaves it unset, and `office deliver` refuses it by name);
`author`, the identity the audience expects on the delivery commits,
`Name <email>`, carried by every commit deliver makes or pushes as both
author and committer (0.25.0: unset, deliver asks for it once on a
terminal, a fact only the occupant knows, and keeps it; piped, it refuses
and names `--author`; the clone's own identity is never used silently);
and `base`, the audience branch deliveries branch from (unset, the
audience remote's HEAD branch, read from the clone). A fourth is
`validates_on` (0.25.0), a host as `--host` takes one: where a project
with an audience validates, never where it is worked. A project with an
audience is worked and delivered from a guarded clone on the occupant's
machine by default (ruling 2 of the front-door arc): `office projects
add` with `--audience` takes PATH as that clone here, and a host declared
with it (`--host`, or `--validates-on`) is recorded as `validates_on`;
`--worked-on-host` keeps the repo worked on its host, as before. On a
terminal the same default holds (0.26.0): a host answered before the
audience is, once the project has an audience, where it validates, and
the wizard asks the clone's path here; working it on the host is chosen
by key, never had by answering in order. Projects already declared
on a host keep working as they did, and nothing validates on a host yet
(bale's remote validation runner is S3's).
Declaring an audience installs the push guard in the clone's .git/hooks,
outside what git tracks: a pre-push hook that lets nothing reach the
audience from the clone but the one delivery branch `office deliver`
pushes, with the branch named in OFFICE_DELIVERY for the guard to read:
no tag (bale's applied/ tags or any other), no bale branch, no other
ref, no deletion, whatever the push's form (`--tags`, `--all`,
`--mirror`, a refspec, a tag by name), and the audience known by its
remote's name or by any URL that is the same repository (scheme, user,
port, a trailing .git aside), read from the clone's config as it stands.
Each refusal names deliver. A push with `--no-verify` runs no hook at
all: the guard keeps a slip out, never a deliberate act. The guard
carries its version on a `guard_version=N` line; a guard an earlier
release installed (0.17.0's, which wrote none) is named by `office
status` with the line that replaces it, and `office upgrade` and `office
projects set` replace it, as they install a missing one; a hook the
office did not write is said and never replaced. The delivery is
built on the occupant's machine, where the audience answers with his
credentials: for a project on a host the landed commits come here as a
git bundle through the project's shell, into a temporary repo removed
after; what the office leaves on a host is, as always, nothing outside
the project's repo. `office relay SID ANSWER-FILE` carries a planner's
answer to a clarification back the same way bale's other verbs run: bale
relay in the repo the session is open in, through the project's shell
for a hosted one, the answer file on this machine piped to it, and the
block bale prints for the worker printed whole and, on WSL, put on the
clipboard, as `office land` hands over a relay.

A copy the office claims is a copy (0.23.0). Every block the office says
it put on the clipboard is on it, whole, its non-ASCII intact, and it is
the last copy made. On WSL clip.exe is fed UTF-16LE, which it reads
whole; fed UTF-8 it reads the console's code page, which is how bale's
own copy of the same blocks arrives mangled (bale's half, a slip for
bale-src). bale copies first, while it packs or applies, so the office
copies after it: `office start` the opener once the pack has ended,
`office land` the relay as its last step, after the after-land actions,
`office probe` the output once the probe's own closing step has run. The
office then reads the clipboard back with the machine's paste command
(machine.toml's paste_command, or the reader the machine has) and holds
it to the block, copying once more when another program copied after it;
only a copy that reads back is claimed. A copy it cannot confirm (no way
to read the clipboard), cannot make (no clipboard command, or off a
terminal) or that reads back otherwise is said in one line that points at
the block on the screen, and land prints the block again, whole. The
suite writes no clipboard and opens no file manager on any machine.

The office scales with whatever carries sessions by staying on its side
of that line. It supplies what a carrier lacks (which job, what context,
what a spawned session may touch, and when) from files that declare it.
It runs bale's pack and apply when the occupant asks, as the occupant's
hands at the terminal, and records which sessions belong to which job;
it never records what bale records, never schedules a session, never
dispatches one to a model and never carries pastes.

## 11. One office per set of house rules

Topics do not earn offices; different rules do. A new kind of job with
the same rules is a new folder in an existing office. A job whose rules
differ (different data that must never ship, different audiences,
different machines) gets its own office. Offices on different machines
are separate buildings; nothing is shared between them except the
office-src install each one reads.

## 12. The profile

Every office has a profile at profile.md. It belongs to the office;
office-src owns only its required shape (share/profile-shape.toml). The
required sections:

- Purpose: why the office exists and what jobs come here.
- Not for: what it is not for, and where those things go instead.
- Audiences: who may read what the office's projects hold.
- Site: machine, root, timezone, where the repo is pushed, and where it
  must never go, including anywhere an audience can read.
- House rules: the office's own rules, on top of section 9.
- When to open a session here: its threshold within section 8.
- Spaces in use: beyond the base floor plan, and why.
- Founding: the date and the founding sitting's session id.

No required section may be blank. An office with no restriction in a
section writes that down, because a missing boundary and an absent one
read the same. `office status` tells a complete profile from a stub: a
section is complete when it has text outside comments and no line that
starts with TODO. An office with an incomplete profile is unfounded and
says so on every command. Capture still works in an unfounded office.

Spawning an office is a conversation, not a form, and the conversation
starts before the session does, so the session has something to write
from. `office init` builds the skeleton, writes bale.toml, surveys the
machine, commits, and asks which projects the office watches (each
through the questions of `office projects add`, until a plain return,
with `--project` as the flag twin). Then it asks the profile's questions:
one per section of the profile shape, in its order, each worded from the
section's asks line, `?` explaining what a good answer holds, and a
plain return leaving the section for the founding session to ask about.
Each question has a flag twin, so a piped init asks nothing and sends
what it was given. The Founding section is never asked: the session
writes it. The timezone is asked with Site, as the zone the occupant
lives in, defaulting to the machine's when that resolves; it is checked
against the zone database, a zone that does not resolve is named with
what fixes it, and a zone that resolves is written to the floor plan
then, so the office's dates are the occupant's from the first folder on.
Init then opens the founding folder (the office's first job), keeps the
answers in it as answers.md, the occupant's words as given, and sends
the founding session out through `office start`, like every other
session: an out tray, the opener, the session recorded in the folder,
and `office land` when it comes back. `office found` is the same door for
an office that exists and is unfounded (one built with `--no-founding`,
or whose founding session never went out): it keeps the answers a
founding folder already holds and asks only for the rest, and `office
start` on the founding folder goes through it. It refuses an office that
is founded, and one whose founding session is out. On a terminal an
answer may run to several lines, a blank line ending it, and it is shown
whole to keep, redo or mend before it is kept (section 7). When the
founding session lands applied with the profile complete, `office land`
closes the founding folder, done: the folder is the office's, and a
founding has nothing more to do. Init refuses to build
from an install whose own catalogs have a defect; for an office already
built, `office status` reports the defect and the office keeps working.

The founding session is scoped: it may write profile.md, the notepad and
the floor plan, and its folder, so one trip lands everything. Its brief
carries the answers verbatim under the sections they answer, which
sections were left to ask, the timezone and whether it resolved, and the
survey's facts about the machine. The session writes the profile from
the answers, section by section, with the occupant; asks only for what
was skipped (a light question block if it fits, a clarification if not);
records in the Founding section that the profile's questions were
answered through the office command, and when; files the occupant's
words, the answers and the conversation, as a notepad page; and sets the
timezone in the profile's Site section, and in the floor plan when init
could not. It asks the occupant rather than trusting the survey, because
a machine's clock can report a zone the occupant does not live in. The
founding session never touches the version stamp.

## 13. The survey

`office survey` writes floor-plan/survey.md: facts about the machine, no
judgment. The operating system and shell, which tools exist and their
versions, the timezone, mount points by name, and which bale and
office-src installs are on the PATH. It never reads data, never recurses
into a directory, and wraps anything slow in a timeout. It makes no
network calls; whether a remote host is reachable is a probe's question.

The page is overwritten on every run and never edited by hand. Each run
reports what changed since the previous survey, on the terminal and at
the foot of the page, and commits the page. `office init` runs the first
survey, and `office start` runs it again before every pack and commits
the page alone, so the survey a session reads first is never older than
the session; while an open session's forecast holds the page (the
one-writer rule), or when the survey cannot run, start leaves it as it
is and says how old it is. `office status` names its age and the
office-src version it records beside the installed one.

An office adds its own steps as executables in drawer/survey/. Each runs
from the office root under a timeout, and its output (best written as
`key: value` lines) becomes a section of the page. The same rules apply:
facts only, shallow, fast.

A number that can go stale is computed where it is shown -- by a survey
step or the digest -- and never written down as a standing count.

## 14. Versioning and upgrades

The tool (the office command, the templates, this doctrine, the profile
shape, the space catalog and the verb declarations) is read from the
installed office-src at run time and never copied into an office. The
profile stub that `office init` writes from the template is the office's
own from then on.

Each office's floor plan records the release it was built from
(built_from) and the release it was last migrated to (migrated_to).

A release is breaking exactly when it ships a migration. Additive
releases need nothing done in any office, and the tool tolerates every
older office shape; it never refuses an office for lacking something
optional. What an additive release adds to an office it brings without a
migration: `office upgrade` writes it when it is missing, never rewriting
what is there, and `office status` names it (0.25.0: the letterhead's
pages and the push guards).

`office upgrade` runs the pending migrations in order. It rehearses them
first on a scratch clone of the office, then runs them for real and
lands them as one commit, whose message carries each migration's summary
from the release notes. A mechanical change is a script. A change that
needs judgment (a new required profile section, say) is a renovation
migration, and it declares what must be true once the renovation has
landed: paths that exist, profile sections that are written. Upgrade
checks the declaration. When it does not hold, upgrade stops there, opens
a folder for the renovation on the desk, and sends the renovation session
out through `office start`, like every other session, with the
migration's goal and a brief carrying its summary, its declaration in
full and its version. The session forecasts what the migration declares
under `writes`, or the whole office when it declares nothing. A
renovation session already out is named and never sent twice; while it
is out the office is behind, every verb that changes the office still
refuses, and `office land` brings back that session and no other. The
next run of office upgrade finds the declaration holds, stamps the
office, and carries on with any migrations after it.

Only office upgrade writes migrated_to. No session edits the stamp, so the
stamp always means the tool checked the office, never that someone said
it was done.

Skew refuses loudly in both directions. An office behind by a breaking
release reports it and names the one line to run, `office upgrade`. An
office migrated past the installed tool is refused outright until the
install catches up.

## 15. Filed paper

Filed paper (the filing cabinet, the notepad, and the drafting table's
ledgers and close reports) is never rewritten, by a session or by a
migration. Only live structure migrates. `office upgrade` checks this
after every migration and rolls the office back if filed paper changed.
The floor plan says what is filed: a whole space, or a list of paths
inside one.

Appending is not rewriting: a filed page grows at its end, and the
bytes already filed never change. A correction, an amendment or a
later state is a new record that points back, and the reader renders
the current state. That is how the notepad already works, and the
drafting table's ledgers work the same way. A filed folder in the
filing cabinet keeps the older rule: it moves whole, and only the
office command adds lines inside its sections.

A session that writes a filed page proves it in its validation: for a
page that existed when the request was packed, the first bytes of the
page as staged, as many as the shipped copy had, hash to what the
request stamped for it; a page the session created has no base. The
check is `doctrine/checks/filed-append-only.sh`, which rides with the
doctrine into every office session, and the worker fills in its paths,
sizes and hashes from its own request. A script that appends to filed
paper makes the same check before it commits: `office note` holds the
day's page to its committed bytes and commits nothing that changed them.
The drafting table's scripts do the same for the pages they add to:
`office rider add` holds the riders page to its committed bytes plus the
rider at its end, and `office agenda add` holds the agenda to its
committed bytes plus the one entry it put above the page's Disposed list.

`office status` holds the same line after the fact: it walks git's
history of every filed page the floor plan lists, the filing cabinet
aside, and reports any commit whose change to one did more than add at
its end, and any uncommitted change that would. It is the net for a
hand edit that went through neither bale nor a script.
