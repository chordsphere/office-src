# OFFICE.md

How every office works. This doc ships with every office session. It
lives in the office-src install and is never copied into an office, so
upgrading the install changes it for every office at once. Each office
says why it exists, and what it adds to these rules, in its own profile
(profile.md at the office root).

## Front sheet

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
surveys the machine, and prints the line that packs the founding session.
`office` on its own is walking in: what is on the desk, this week, the
last notes, the suggestion box, and what you can do from here. The
everyday verbs take seconds and need no session: `office note` captures a
line, `office open` starts a numbered folder, `office desk` shows what is
in flight, what is ready and in what order, and what waits on what,
`office week` shows this week against what happened, `office close` and
`office reopen` move a folder to the filing cabinet and back. `office
survey` rewrites the page of machine facts. `office status` says whether
the office matches the installed tool. `office upgrade` brings an office
up to a new release, one commit per office. `office projects` lists the
projects in the office's scope and renders what bale records about them.

The office never runs a session. It only says what a session should carry
and where it lands, and prints the pack line. bale carries the session.

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
   letterhead, where an office has one, for anything that goes out; and
   the rule that office context informs a session but never lands in a
   project. Every project session an office packs carries that rule as a
   constraint: "Office context informs this session but never lands in
   this project." Deliberation, candid notes and private versions stay in
   the office even when a session read them to do the work.
3. Where each repo is pushed. Guard: the profile's site section. An
   office repo is never pushed where a project's audience can read it.

## 3. Principles

1. Capture is instant and dumb. Structuring is slow and smart, and
   happens later in batch.
2. Every session lands something: at minimum a notepad entry and the
   folder it touched. A read-only sitting lands through the sessions it
   authors, whose briefs carry its planner's words.
3. A session is worth opening only when the job needs it (section 8).
   Otherwise the occupant does the work and leaves a one-line trace.
4. What every session needs is hung. Hanging is a property of an item,
   not a place (section 6).
5. A space earns its place through use. A space unused after a few weeks
   of real work is removed; new spaces arrive when real work asks for
   them.
6. Nearly every job produces two deliverables: the thing, which lives in
   a project, and the message about the thing, which leaves through the
   letterhead with a copy in the folder.

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
  doctrine directory: `bale pack --context` run there. bale's include
  groups only pull paths inside the repo being packed, and this doc lives
  in the install, not in the office.

The folder records the id of every session that worked on its job.
`bale pack --json` reports the id, so nobody types it: piping that report
into `office sessions FOLDER -` records the id in the folder's Sessions
section, with a few words if the occupant gives them (`-m`). Until the
session verbs arrive, sessions for a folder are packed by hand this way,
and the session verbs will record through the same step. The folder
points at session ids; it never copies what bale records about a session.
`office sessions FOLDER` lists them with what bale records about each,
rendered on every run (section 10).

After a project session lands, the office side (the folder, and the
front sheet of any handbook chapter the change touched) is brought up to
date by an office step, not by the project session writing into the
office.

## 5. Spaces

The floor plan (floor-plan/manifest.toml) lists the spaces an office
has, and, in its [projects] table, the projects it scopes on this
machine (section 10). `office init` builds the base spaces. The others are added by a
renovation session when real work asks for them. The install's catalog
of spaces is share/spaces.toml.

| path | what it does | base | hung | filed |
|---|---|---|---|---|
| profile.md | why this office exists and the rules it keeps | yes | yes | no |
| floor-plan/ | the manifest and the site survey | yes | survey.md | no |
| desk/ | open folders: jobs in progress | yes | no | no |
| filing-cabinet/ | closed folders | yes | no | yes |
| notepad/ | the occupant's words, verbatim and dated | yes | no | yes |
| suggestion-box/ | friction slips | yes | no | no |
| drawer/ | the office's own tools: probes, survey steps | yes | no | no |
| handbook/ | the private layer of documentation | renovation | front page | no |
| clipboards/ | one per recurring meeting | renovation | no | no |
| calendar/ | when things happen, and what actually happened | renovation | yes | no |
| rolodex/ | how to deal with each person | renovation | no | no |
| letterhead/ | how anything leaving the office must look and sound | renovation | no | no |
| drafting-table/ | blueprints for work too big for one folder, and the ledgers around them: rulings, evidence, watches, riders, the agenda | renovation | no | a list |

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
it was queued, and whichever of class, size, lane, source, blueprint,
links and gates it was given. A field the command cannot fill is left
out rather than left blank. The number is the folder's citation, folder
N: `office open` mints it as one more than the highest number on the
desk and in the filing cabinet, and it is never reused or renumbered. A
folder from before numbers keeps none and is cited by its name; nothing
ever numbers it after the fact. A verb that mints a number refuses while
an open session in the office's own bale registry forecasts the space
the number lands in, and names the session: sessions are kept apart by
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
agrees with the last line that changed it. `office sessions FOLDER SID
--ratified` records that the planner ratified a session's judgment
calls, with `--except` for what was corrected and where it went.

Gates are data on the folder that waits: `after` (do not open this
before folder N is done, a blueprint closes, an agenda item is ruled on
or a ruling exists), `serializes after` (never beside folder N; when both
are ready, N goes first) and `consumer` (parked for the blueprint or
folder that will carry it). The order of the desk is computed from what
the folders say, and nobody writes one. `office desk` shows, in order:
in flight, the folders some session is open for; ready, the queued
folders whose gates are all met, ordered by `serializes after`, then
size, small first, then number, each saying when a gate cleared since
the last walk-in; parked, grouped under what each waits for, headed by
that gate's own status; and candidates. A gate that names nothing, or a
cycle of gates, is an error line naming the folders, and no folder is
ever dropped from the desk.

Clipboards. A recurring meeting gets a clipboard because it never ends:
the series (purpose, attendees, cadence, which chapters it concerns), the
running action items on top, and one dated sheet per occurrence. Action
items that are real work become their own folders.

Calendar. Series, one-offs, and a record of what actually happened.
Because it is hung, a session can compare what should have happened with
what was recorded and raise one question about a gap. Times are local
time in the floor plan's timezone; bale's clock is UTC. Two pages hold
it, one bullet per line. calendar/plan.md says what should happen: a
one-off is `- YYYY-MM-DD HH:MM title`, a series is `- every DAY HH:MM
title`, where DAY is mon to sun, day or weekday. calendar/record.md says
what happened: `- YYYY-MM-DD HH:MM title: what happened`, the time
optional. `office week` lays this week's plan against the record: a
planned item in the past with no record that day starting with its title
is a gap. Bullets that fit neither shape are reported, never dropped. An
office without a calendar is told so, with the renovation that adds one.

Handbook. Only the private layer. Shareable technical documentation
belongs in the projects (README, docs/), and a chapter points at it
rather than restating it. Each chapter opens with a front sheet for the
occupant in plain language; below it is written for sessions. Every
session that lands a change to a system updates that chapter's front
sheet. Correspondence, including copies of messages sent, is the
folder's, not the handbook's.

Rolodex. One card per person, as a guide for responding to them.

Letterhead. The rules for anything that leaves the office: code style,
prose style, what must never appear, and the occupant's voice.

Drafting table. Blueprints for work too big for one folder, one arc
each, with the ledgers a planning sitting rules in: the rulings ledger,
the evidence ledger, the watches register and its log, the riders page,
the agenda, and the desk moves a sitting decided. The space is part
live, part filed: the ledgers, the watch log and the close reports are
filed paper, and the floor plan lists them. Its templates are the
install's; a renovation copies them in when the space arrives. A fact
lands once, on the folder, blueprint or ledger record it belongs to,
and everything else cites it by id; the same fact restated in two
records is a defect. A ruling on the ledger is reopened only by a
sitting that names it, and a reopening is a new ruling that supersedes;
the earlier record is never touched. The evidence ledger admits only
what live traffic earned: a record names a session id or a notepad
page, or it is refused. An eye-watch no sitting has looked at is
reported, never silently aged. Closed blueprints stay on the table;
nothing is condensed.

Notepad. The occupant's words, verbatim and dated. Never edited.
Structuring them into folders, cards and chapters is cleanup's job.
`office note` appends a timed line to the day's page, notepad/DATE.md;
a sitting's words are filed as their own page, notepad/DATE-SLUG.md.
Capture is instant: it works in an unfounded office and in one behind or
ahead of the installed tool, and only warns. Anything outside ASCII is
kept as a backslash escape, so the office stays ASCII and no word is lost.

Drawer. The office's own tools. The office command itself lives in the
install, never here. Survey steps the office adds live in drawer/survey/
(section 13).

Suggestion box. Any session, and the occupant, can drop a slip when
something causes friction. Routine slips are handled by cleanup, design
slips by renovation. A slip about a tool (bale, office-src) says so, so
it can be carried to that tool's project.

## 6. Hanging, and what every office session ships

An item is hung when every session in the office needs it. The floor
plan marks hung items per space: true for a whole space, or a list of
paths inside it. The office's bale.toml carries them to bale as an
include group: its triggers are the office's spaces and its pulls are the
hung items, so any pack whose includes touch the office ships them
without a list on the pack line. `office init` writes it; a renovation
that adds a space or hangs an item updates it; `office status` reports
when it no longer matches the floor plan. Every office session ships:

- this doctrine, as a context tarball from the install;
- the office's hung items: at least profile.md and floor-plan/survey.md;
- whatever its verb names in the install's verb declarations.

A session may always write the notepad and the suggestion box.

## 7. Verbs

Verbs declare what a session ships and where it lands, and emit pack
lines. office-src never runs, schedules or carries a session, so whoever
carries sessions (the occupant, bale, a future harness) can change freely
without the office changing. The declarations are share/verbs.toml in
the install.

Kinds:

- script: the office command alone, in seconds. No session, no network.
- office session: packed from the office, lands in the office.
- project session: packed from a project, lands there; the office's
  context rides beside it (section 4).

| verb | kind | built |
|---|---|---|
| init | script; writes bale.toml and prints the founding session's pack line | yes |
| survey | script | yes |
| status | script, read-only | yes |
| upgrade | script; prints a renovation pack line when a migration needs judgment | yes |
| where, default | script: which office a command acts on | yes |
| note | script: append a dated line to the notepad | yes |
| open | script: start a numbered folder on the desk, or a candidate, or one born done in the filing cabinet | yes |
| desk | script: in flight, ready in order, parked under what each waits for, candidates | yes |
| week | script: this week's calendar and its gaps | yes |
| close, reopen | script: move a folder to the filing cabinet, done, absorbed, split or retired, and a done one back | yes |
| sessions | script: list or record the sessions that worked on a folder, and the planner's ratification of one | yes |
| projects | script: list the projects this office scopes, add one, render what bale records about them | yes |
| founding | office session: the profile, the occupant's words, the timezone | yes, via init |
| work | office session: answer, draft, probe, decide, deliver | by hand |
| build | project session: change a project for a folder | by hand |
| prep | office session: a briefing for a meeting | not yet |
| meeting | office session held open during a meeting | not yet |
| cleanup | office session: keep the office as designed | not yet |
| renovate | office session: change the design | by hand |

Session verbs are done by hand a few times before the command learns
them.

A verb is a wizard on a terminal. It walks the occupant through
whatever it was not given, and it explains an argument it does not
understand rather than refusing it. Every question a verb asks has a
flag twin, so the same invocation can be typed in full without being
asked anything. With piped input a verb never asks: it refuses what it
was not given and names the flag. The verbs ask the same way: each
question names its flag, offers its default or the words a field takes,
explains the field when the answer is `?`, and asks again, with the
reason, when an answer is not one the field takes. A plain return skips
a question that may be skipped. A verb asks only for what matters to
it, so a folder is opened in four answers (title, size, lane, source);
the other fields are flags, and `--help` explains each.

A session whose goal the occupant overrides midway keeps the override
words on its notepad page, and the new ask becomes a new folder or
blueprint, never an exception counted against the old one.

Walking in is `office` with no verb, from inside an office or anywhere on
the machine (the per-machine default). It shows the office's name, the
date and time in its timezone, whether it is founded and current, the
sessions in flight in its projects and in the office itself, with the
folder each belongs to, how many folders are ready, parked and
candidates, and the first three ready ones with their next moves, this
week and its gaps, the last notepad lines, how many slips are in the
suggestion box, and the verbs to reach for. It only reads the office;
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

## 9. House rules for every office

These hold in every office. Each office adds its own in its profile.

1. Every session lands something: at minimum a notepad entry and the
   folder it touched. A planning sitting's words travel in the briefs of
   the sessions it authors, and those sessions file them in the notepad.
2. Every session that lands a change to something the handbook describes
   updates the front sheet of that chapter in plain language.
3. Nothing goes on a rolodex card that would embarrass the occupant if
   the person read it.
4. Anything that asks the occupant for bookkeeping, setup or moving files
   is friction. Say so in a suggestion slip. When a hand step cannot be
   avoided, give it as one line and say where to run it.

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
name and the path of each project's repo on this machine, absolute or
under the home directory, written by `office projects add` and never by
hand. An office with no table scopes nothing, and every rendering says
so rather than showing an empty screen as if it were true. A project on
another machine is not read. The office reads each project's records
only through bale's --json surfaces, run in the project's directory with
no prompt, never by parsing .bale/, and it never writes what bale
records. The install's share/bale-consumption.toml names every bale verb,
flag and key the office reads and the bale version they were written
against; `office status` reports a bale outside that range. What it
renders: on the walk-in, the sessions in flight and the folder each
belongs to; in `office sessions FOLDER`, each session with its outcome,
dates, claims beside verdicts and exchange rounds; in `office projects`,
the trust ledger per work class (the evidence a trust grant would be made
on; the office holds no grant), the last applied session that landed a
path, and the version trail. Wherever a count the records compute sits
beside one written down, both are printed.

The office scales with whatever carries sessions by staying on its side
of that line. It supplies what a carrier lacks (which job, what context,
what a spawned session may touch, and when) from files that declare it,
and never records, schedules or carries sessions itself.

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

Spawning an office is a conversation, not a form. `office init` builds
the skeleton, writes bale.toml, surveys the machine, commits, and prints
the pack line for the founding session. It refuses to build from an
install whose own catalogs have a defect; for an office already built,
`office status` reports the defect and the office keeps working. The founding session is scoped:
it may write profile.md, the notepad and the floor plan, so one trip
lands everything. In it the occupant and the session write the profile
together, section by section; the session files the occupant's words from
the conversation as a notepad page; and it sets the office's real
timezone in the floor plan's [office] timezone and in the profile's Site
section. It asks the occupant for the timezone rather than trusting the
survey, because a machine's clock can report a zone the occupant does not
live in. The founding session never touches the version stamp.

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
survey.

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
optional.

`office upgrade` runs the pending migrations in order. It rehearses them
first on a scratch clone of the office, then runs them for real and
lands them as one commit, whose message carries each migration's summary
from the release notes. A mechanical change is a script. A change that
needs judgment (a new required profile section, say) is a renovation
migration, and it declares what must be true once the renovation has
landed: paths that exist, profile sections that are written. Upgrade
checks the declaration. When it does not hold, upgrade stops there and
prints the pack line for a renovation session, which does the work. The
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
paper makes the same check before it commits.

`office status` holds the same line after the fact: it walks git's
history of every filed page the floor plan lists, the filing cabinet
aside, and reports any commit whose change to one did more than add at
its end, and any uncommitted change that would. It is the net for a
hand edit that went through neither bale nor a script.
