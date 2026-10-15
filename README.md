# office-src

The tool that builds and keeps offices. An office is where you go to
begin work on the projects in its scope: a git repo organized like a
physical office, holding what only you and your sessions may read.
Projects hold what their audience may read. bale carries the sessions;
the office supplies the context that is not the project's own.

office-src is project agnostic. Every office is specific and says why it
exists in its required profile. How offices work is doctrine/OFFICE.md,
which ships with every office session.

## What you want to do

| you want to | type |
|---|---|
| see what an office is like before committing to anything | `office tour` |
| walk in: your projects, what waits on you, and a key for each thing to do | `office` |
| capture a thought | `office note TEXT` |
| drop a message or a thread someone gave you, to sort out later | `office drop` |
| drop a friction slip | `office slip TEXT` |
| start a job, in your own words, and send its session out | `office start new` |
| send a session out for a job on the desk, or a planner's bundle from your downloads | `office start` |
| bring the session back | `office land` |
| deliver a folder's landed work to the project's audience | `office deliver FOLDER` |
| build an office | `office init` |
| see your own verbs, one line each | `office help` |
| see every verb, the plumbing too, grouped by what it is for | `office help --all` |

On a terminal, `office` alone is your home screen: most of what you do
there is one key, and you never type a session id or a file name.

Every verb is a wizard on a terminal, and every wizard keeps one rule:
you supply the words, the session supplies the structure. A verb asks you
only for what only you know: the ask, in your words; which project, when
the office cannot tell; yes or no on what cannot be undone; and what only
your eyes can check. Everything else it works out and says, or leaves for
a session to set. A choice among things the office knows (a folder, a
session, a project, a bundle) has a key. `?` explains a question, and
every question has a flag, so the same command can be typed in full and
piped input is never asked anything. `office VERB --help` (or `office
help VERB`) explains one verb, with examples.

### Your verbs and the plumbing

`office help` lists your own verbs, one line each in plain words: the
home screen, `note` and `drop` (the instant captures), `slip`, `start`
(with `start new`, the one door for new work), `land`, `desk`, `close`,
`deliver`, `projects add`, `tour` and `init`, with what a folder is (one job, what was asked in your words and
the sessions that worked on it) and what a project is (a repo whose
audience may read it, with the office holding what is around it). The
rest is the plumbing the office and its sessions use: a session names
the line in full when it needs you to run one, and `office help --all`
lists every verb. share/verbs.toml says which verb is on which surface
(`surface = "occupant"` or `"plumbing"`), the doctrine's verbs table says
the same, and every verb works the same on either.

If you already use bale: with the office you never type a session id,
never assemble an include list, and never forget a landing step. `office
start` reads the folder's lane, forecast and work class and what rides
with each project; `office land` knows which repo, which response, and
what runs after it applies. bale stays visible: start and land run bale's
own pack, open, apply and retry, bale asks its own questions and only you
answer them, `office start --help` and `office land --help` name the bale
commands they run, and `OFFICE_DEBUG=1` shows every bale call. Any bale
command still works by hand beside the office.

### Take the tour

    office tour

It builds a throwaway office in a temporary directory, with sample
folders, a note, a slip and a calendar with a gap, and walks you through
the verbs on it: walking in, capturing, opening a folder, the desk, the
week, and what `office start` and `office land` do. Each step runs one
command, shows what it printed, and says what it did and why you would
type it; start and land are shown and explained, never run. On a
terminal it waits for a return between steps (`q` ends it), and at the
end it offers a shell inside the tour office to play in (`--play`,
`--no-play`; `--no-pause` runs straight through). Then it deletes the
office and says so, and it deletes it too when stopped or interrupted. It
never touches your offices, this machine's default office, the walk-in
record or bale: a stand-in bale that refuses everything is first on its
PATH, and git's global config is switched off for it.

### Walk in

    office

On a terminal it is your home screen. Under the office's name, the date
and time and its state, each project the office scopes has one line:
what is in flight on it, or what last landed and when (or that nothing
has), and the desk in one line. Then what waits on you, each with a key:
the next move first, then
a response in your downloads for a session that is out (a file to offer:
whether it has arrived is still bale's to say, and `office land` asks
it), a planner's bundle in your downloads that no session has opened
(bale's records say which were), each unsorted drop and the sort, desk
moves a sitting decided, an office out of step with the install, and a
read-only sitting, which only you can say is over. Keys for a new job
(`o`), sending a session out (`s`), bringing one back (`l`), a note
(`n`), a drop (`d`), the whole desk (`k`) and help (`h`) are always
there, and `q` leaves. A key runs the verb's own code with its arguments
filled in and asks only what that verb must; when it ends, a key brings
the home screen back, worked out again. Sessions are named by their
folders (`folder 3, Fix the login`), never by their ids. The first time,
it asks where this machine's downloads land (`downloads` in
machine.toml), and never again.

Off a terminal (piped, under a test or a session) it is the page, as
before. Walking in shows the office's name, the date and time in its timezone
(and that it is on UTC, when the floor plan's zone does not resolve;
`office status` names what fixes that),
whether it is founded and current (and, when the office scopes the
project the install came from and that project has moved past the
installed commit, an `Install: BEHIND: ...` line in the words `office
status` uses; and, for that same office, a `Suite: ...` line when the
latest detached run of the project's suite, below, did not end `OK`:
its `FAILED` or `BROKEN` verdict as written, or a `RUNNING` one over an
hour old, with the log to read), the sessions in flight in its projects
and in the office itself with the folder each belongs to, how many
folders are ready, parked and candidates and the first three ready ones,
how many drops wait unsorted in the in-tray and how old the oldest is,
this week and its gaps, the last notepad lines and the slips, and the
verbs to reach for. It ends with one Next line: the one command to type
now, with its arguments filled in, worked out from the office on every
walk-in and never written down. In the order they win:

| the office | Next |
|---|---|
| is behind the install, or ahead of it | `office upgrade` (or `office status`, which names the versions; or `office land SID` while the renovation upgrade sent out is out) |
| scopes the install's source, which has moved past the install | `(cd SOURCE && ./install.sh)` (start and land run the install, so until it is level they run the old office) |
| has a session out | `office land SID` (when its response is in your downloads, land finds it) |
| has desk moves a sitting decided, or sorted drops waiting in the in-tray, not yet run | `office moves` (until they run, the desk is not in the order the sitting decided) |
| has an unsorted drop in the in-tray | `office start --drop in-tray/PAGE` for the oldest whose project is one of the office's and has no session in flight on its lane; for the oldest whose project is none of them, the same with `--lane LANE` to fill (an office with no projects skips this) |
| has an unsorted drop whose project is none of the office's and a session has gone out since it was dropped, or three or more unsorted drops and nothing ready | `office start --sort`, the standalone sort |
| is unfounded | `office start FOLDER` for its founding folder (it goes out with the answers the folder keeps), or `office found` when no founding folder is on the desk |
| has a ready folder | `office start FOLDER` (`--on PROJECT` when its lane names one) |
| has an open folder no session is out for | `office start FOLDER` (or `office close` it when it is done) |
| watches no projects | `office projects add` |
| has five or more slips | `office open triage-the-suggestion-box ...` |
| has only parked folders and candidates | `office desk` |
| has nothing waiting | `office open`, when a job comes in |

### Capture

    office note called the bank; rate locks Friday   # a timed line on today's notepad page
    office slip --about bale pack needs too many flags  # a friction slip, its own page in the suggestion box
    office drop --project alpha                      # the message on the clipboard, its own page in the in-tray
    office drop thread.txt                           # ...or a file (- for stdin); asks the project on a terminal

Each verb commits only the paths it touched. `office note` and `office
slip` work in an unfounded office and in one that needs an upgrade; they
warn and write. `office note` commits a notepad page only when its
committed bytes are untouched and the new lines are at its end. `office
slip` asks on a terminal only for the words; what the slip is about (the
office, bale, office-src, or one of the office's projects) is `--about`'s
to say, or the session's that reads the box.

`office drop` captures a message or a thread nobody has read for you:
one page in the in-tray, `in-tray/DATE-SLUG.md`, committed on its own,
with its first line as the heading, four field lines (`dropped`,
`project`, `via`, `status: unsorted`) and the text verbatim under `##
Text`. The text comes from a file, stdin, or, on a terminal with
neither, the clipboard (machine.toml's `paste_command`: this machine's
own reader, found and kept the first time; asked only when there is
none). When the office scopes a project, it asks one question, the
project, each of the office's with a key and any words taken
(`--project`); a plain return leaves it empty, and it never refuses a
drop it can write. The
in-tray arrives with the first drop. From then on every session `office
start` sends out carries the unsorted drops, and a session that can
judge one sorts it in its notes.md (doctrine section 4); `office start
--drop in-tray/PAGE` sends one straight out on its own, and `office
start --sort` sends the drops nothing carried to a session of their own.
Drop, start, land: a routine ask needs no planner. When a session's Sort
lands, `office land` files it on the drop's page, and a drop sorted into
a folder (a new one, or folder N) moves there with its brief: the next
`office start N` asks nothing the folder already knows.

### Start a job, and finish one

    office start new                                 # a new job in your words: its folder, and its session out
    office start new --words "Fix the login on narrow screens" --on alpha   # ...typed in full
    office open                                      # (plumbing) a folder on the desk, and no session yet
    office open house-hunt --thread < thread.txt     # ...seeded with the thread that started it
    office open fix-login --goal "Fix the login redirect"   # ...with the goal office start offers
    office desk                                      # in flight, ready in order, parked, candidates
    office week                                      # this week's calendar and its gaps
    office close fix-login                           # to the filing cabinet, done
    office reopen fix-login                          # back to the desk, history and all

New work comes in through one door: `office start new` (the home
screen's `o` key) asks for the job in your own words, as many lines as
you like (a blank line ends them), and sends its session out in the same
motion. The first line is the folder's title and its slug comes from it;
the words are kept, word for word, in the folder's Asked section, and as
one line they are the goal the session goes out with. It asks which
project the job is on, by key, only when your words name none of the
office's projects. The title, the size (small) and the goal are
provisional: the folder says so on a `provisional:` line, and the
session that works the job sends back its own in its notes.md's
Structure section, which `office land` files over them (your words in
Asked are never touched). Every flag still sets its field, and a field a
flag sets is yours. A title another folder took today gets a name of its
own. `office open` is the same code without the session: plumbing now,
for a folder that should wait on the desk.

A folder is named by the date and a slug, and can be named by any unique
part of that name or by its number, `folder 12`; asked for one, a verb
lists them with a key each. Folders, their fields, statuses and gates are
below.

### Plan work too big for one folder

    office blueprint open rider-verbs --title "The rider verbs"   # one arc on the drafting table
    office blueprint ratify 2026-10-05-rider-verbs --words notepad/2026-10-05-plan.md
    office desk --blueprint 2026-10-05-rider-verbs                 # its folders, in the desk's order
    office blueprint close 2026-10-05-rider-verbs                  # send out the sitting that closes it
    office moves                                                   # apply the desk moves a sitting wrote
    office rider add "Name the sweep commit" --source "proposal SID #2" --rides bin/bale_apply.py
    office riders                                                  # where each rider is, and the orphans
    office agenda add "Where does a chat land?" --source notepad/2026-10-05.md
    office rulings                                                 # the rulings ledger; --check resolves every citation
    office evidence                                                # the evidence ledger
    office watches                                                 # the watches, and where each stands
    office watches check                                           # fired, not fired, cannot evaluate; --record logs firings
    office digest                                                  # the page a sitting opens on

The drafting table holds blueprints and the pages a planning sitting
rules in. It arrives in an office with the first of these verbs that
writes it. A sitting opens on the digest: `office start` writes it again
just before it packs one. The details are below.

### Send a session out

    office start new                   # a new job, in your words, out in one motion
    office start                       # your downloads' new bundles by key, then which job by key
    office start --drop in-tray/2026-10-14-login-error.md   # a dropped message, straight out
    office start --sort                # the drops nothing carried, to a session of their own

On a terminal, bare `office start` first offers the planner's bundles in
your downloads that no session has opened, newest first, one key each (a
plain return goes on), then asks which job, by key, or a new one in your
words. Where the work lands is the folder's lane (asked by key only when
the lane names no project), the goal is the folder's own or your words,
what the session will change is the session's to forecast, and what
rides with a project rides as declared; each is said, not asked. It
packs the session with bale where the work lands, records it in the
folder, and puts every file to attach in one out tray, `~/out-tray/SID`,
beside the opener it prints: attach the tray's files to a fresh chat and
paste the opener. When the brief carries the planner's ratification of
earlier sessions (`--- RATIFIED SID ---` lines), start files each in the
folder that records that session, wherever it is, and says so. On WSL
the opener goes on the clipboard as start's last copy, read back to
check: the office says it is there only when it is. The details are
below.

### Bring it back

    office land                          # the session out: bale apply, how it ended, the relay
    office relay SID answer.md           # the planner's answer to a clarification, to bale relay there

It finds the session the response answers, runs bale apply in the repo it
belongs to (on its host, for a project on another machine), says how it
ended, files the folder's walkthrough and delivery pages from the
response, then its Sort on each drop's page, its questions and answers in
the folder, its facts in the handbook and its Structure over the folder's
provisional fields, runs `office moves` when a drop was sorted (naming
each folder it minted), runs the project's after-land actions, closes a
folder whose one session has landed (saying so, with the line that
reopens it), closes the founding folder when the founding has landed,
names any watch that fired, and, last, puts the relay to carry on the
clipboard, read back to check. It asks nothing about ratification: the
planner ratifies in the next brief it writes, and `office start` files
it. `office relay` carries a planner's answer to a clarification back
to the session's repo, through the project's shell for a hosted one. The
details are below.

### Run a worker's probe

    office probe 13                      # the block on the clipboard: run where folder 13's project lives

When a worker returns a probe block (a fact it needs from your machine,
or from the host and container a project lives in), `office probe` runs
it there for you: in the project's repo, through its shell on a host, or
in the office root. It shows the block's purpose header and asks once
first, and refuses a block that is not a probe or does not say it is
read-only. The output comes back to your terminal whole, the block goes
on your clipboard to paste back, and the folder's History counts the
probe. The details are below.

### Deliver it to the audience

    office deliver health-route          # the folder's landed work to its project's audience, as curated commits
    office letterhead check              # what the letterhead refuses, in the tree here

A project's workbench clone is where bale lands, and nobody reviews it.
`office deliver` carries a folder's landed work to the audience's git
host as a branch of curated commits in your words, the folder's
`delivery.md`, made from the audience's base, holding none of bale's
commits, merges, tags, branches or files; it shows what leaves and asks
once. `office letterhead check` is the guard it runs first, on its own
for any tree. The details are below.

### Build an office

    office init ~/offices/home   # build an office; asks which projects it watches and the profile's questions; sends the founding session out
    office found                 # an unfounded office: the profile's questions, then the founding session out

On a terminal, after building, `office init` asks which projects the
office watches: one at a time, through the same questions as `office
projects add` (the path, the name, what rides with it, what runs after it
lands), until a plain return. `--project PATH` (or `--project
NAME=PATH`, repeatable) is the flag twin, each checked before anything is
built, and `--no-projects` skips the question; piped, it asks nothing.
The office is unfounded until its founding session writes the profile,
and init sends that session out itself. It asks the profile's questions,
one per section of the profile's required shape (`share/profile-shape.toml`)
in its order, each worded from the section's asks line. An answer may run
to several lines: each line is kept as typed, and a blank line ends it.
`?` explains what a good answer holds, and a plain return at once leaves
the section for the founding session to ask about. The timezone you live in is asked with
Site, defaulting to the machine's when that resolves, checked against the
zone database, and written to the floor plan when it resolves. Every
question has a flag twin (`--purpose TEXT`, `--not-for TEXT`,
`--audiences TEXT`, `--site TEXT`, `--house-rules TEXT`, `--when-to-open
TEXT`, `--spaces TEXT`, `--timezone ZONE`), so a piped init asks nothing
and sends what it was given. The Founding section is never asked: the
founding session writes it.

Then init opens the founding folder, keeps your answers in it as
`answers.md`, and sends the founding session out through `office start`:
the out tray, the opener, the session recorded in the folder, and `office
land SID` when it comes back. Its brief carries your answers verbatim
under the sections they answer, the sections left to ask, the timezone
and whether it resolved, and the survey's facts about the machine; the
session writes the profile from them and asks only for what was skipped.

    office init ~/offices/home --purpose "My own tools" --timezone America/Chicago < /dev/null
    office init ~/offices/try --no-founding     # build only; office found sends the founding session later

`office found` is the same door for an office that exists and is
unfounded: it keeps what a founding folder already holds and asks only
for the rest, and `office start` on the founding folder goes through it.
When the founding session lands applied and the profile is complete,
`office land` closes the founding folder (done) and says so; a profile
still incomplete leaves it open, and land says what founds it.
When bale is not on the PATH, init builds the office, keeps the answers in
the founding folder, says so and exits 1; the walk-in's Next line then
names the command that sends it.

## Install

From a clone of this repo:

    ~/office-src/install.sh

That installs the committed tree (HEAD) to ~/.local/share/office-src and
links ~/.local/bin/office to it. `--prefix DIR`, `--bin-dir DIR` and
`--no-link` change that. Run it again to upgrade the install; it replaces
the previous install whole, and refuses a prefix that is not one.

On another machine, clone and run the same line:

    git clone <remote> ~/office-src && ~/office-src/install.sh

Requirements: bash, coreutils, git, python3 (3.11 or later, for tomllib),
all shipped with Ubuntu 24.04. No network, nothing to install. The read
side (below) runs bale when it is on the PATH; without it, every
rendering says bale is missing and the rest of the command works.

`office version` prints the installed version and where it came from.

## Reference

### Looking after an office

    office status              # version, skew, the install against its source, profile, survey age, timezone, hung items, catalogs, folders, filed pages, bale, projects
    office survey              # rewrite floor-plan/survey.md, report what changed
    office upgrade             # run pending migrations: dry run, then one commit; a renovation goes out through office start
    office found               # an unfounded office's founding session, through the founding door
    office where               # the office a command here acts on
    office default [PATH]      # this machine's default office
    office version             # the installed version and where it came from

A command acts on OFFICE_ROOT if set, else the office around the working
directory (found by walking up to floor-plan/manifest.toml), else the
machine's default, kept in ~/.config/office-src/default-office. The
first `office init` on a machine sets it.

### Folders: numbers, fields, statuses and gates

On a terminal, `office open` asks for the job in your own words and
works out the rest (0.22.0): the title is the words' first line, the slug
comes from it, the words go in the Asked section and become the goal, the
size is small and the source is you. It asks the project, by key, only
when your words name none of the office's projects. A name another folder
took today gets one of its own (`-2`). What it worked out (the title, the
size and the goal) is named on a `- provisional: title, size, goal` line
(0.23.0) until the session that works the job sends back its own, as
`## Structure` in its notes.md, and `office land` files it; a field a flag
sets is yours and never provisional, and `office status` names a
provisional line that does not read. `office start new` runs this same
code and sends the session out with it. Type `?` at a question to have it
explained. Every field has a flag, which sets it as given, so the same
folder opens in one line, and piped input is never asked anything:

    office open fix-login --title "Fix the login" --size small \
        --lane "office-src: bin/" --source "notepad/2026-09-30.md"

| flag | what it records |
|---|---|
| `--size small\|medium\|high` | how big the job is; the desk puts small jobs first |
| `--lane "project: paths"` | the project and paths the job will touch |
| `--source TEXT` | where the job came from: `proposal SID #n`, `rider N`, `ruling ID`, `blueprint ID`, `notepad/...`, or a person |
| `--class CLASS` | bale's work class: code, doc, contract-doc, meta, mixed |
| `--blueprint ID` | the blueprint the folder belongs to |
| `--after GATE` | not before GATE is done: `folder N` (or just N), `blueprint ID`, `agenda N`, `ruling ID`; repeatable |
| `--serializes-after N` | never beside folder N; when both are ready, N goes first |
| `--consumer GATE` | parked for the blueprint or folder that will carry it |
| `--linked N` | related to folder N, without waiting for it |
| `--goal TEXT` | the job's goal in one sentence (a `goal` line, 0.20.0): `office start N` offers it as the session's goal |
| `--candidate` | not queued yet: an idea on the desk |
| `--filed --sid SID` | a job done inside a session, filed straight into the cabinet |

`office open --help` explains each. Every folder gets a number, one more
than the highest on the desk and in the filing cabinet, and is cited as
`folder N`; folders from before 0.5.0 keep their names and are never
numbered. While a session open in the office's own bale registry
forecasts the desk, `office open` refuses and names it, so a number is
never minted beside a session that could mint one too.

A folder's status follows its job, and each change is a dated line in
its History:

    office sessions fix-login SID              # the first session recorded opens it
    office sessions fix-login SID --ratified   # the planner ratified its judgment calls
    office sessions fix-login SID --ratified --except "the slug rule, moved to folder 14"
    office close fix-login                     # done
    office close fix-login --into 14           # absorbed into folder 14, which points back
    office close fix-login --split 14,15       # split into those folders
    office close fix-login --retired "premise was wrong"
    office reopen fix-login                    # a done folder, back on the desk, open

`office desk` computes the order; nobody writes one. In flight: the
folders a session is open for. Ready: queued folders whose gates are all
met, by `serializes after`, then small first, then number, each saying
when a gate cleared since you last walked in. Parked: grouped under what
each waits for, with that gate's own status. A gate on a blueprint is
met when its close report exists, on an agenda item when a sitting ruled
on it, and on a ruling when the ruling is on the ledger. Candidates come
next, then the riders orphaned in a closed folder and the desk moves
not applied yet. A gate that names nothing, or a cycle, prints as an
error line naming the folders; no folder is ever dropped. Walking in
shows In flight, the first three ready folders, and a line each for
pending desk moves (and the session that wrote them) and orphaned
riders.

`office status` checks that every folder's status agrees with the last
line of its History that changed it, and walks git's history of every
filed page (the notepad, and the drafting table's ledgers once an office
has one) for a commit that did more than add at the end. It reports and
exits 0; `office init` refuses to build from an install whose catalogs
have a defect.

### The drafting table: blueprints, riders, the agenda and the ledgers

`drafting-table/` holds work too big for one folder, one blueprint per
arc, and the pages a planning sitting rules in. A sitting writes them
directly; the scripts below do what a script can, and no script ever
mints a ruling or an evidence entry.

The space is not base, and no migration or renovation session brings it.
It arrives with the first verb that writes it (`blueprint open`, `rider
add`, `agenda add`, `digest`, which `office start` runs before every
sitting, `watches check --record`, or `moves` when a sitting wrote the
moves page). That
verb writes `drafting-table/README.md` from the install's template, adds
the space to the floor plan as `share/spaces.toml` declares it (its filed
list: the rulings, the evidence, the watch log and each close report),
and adds it to bale.toml's include-group triggers. Each page is made from
its template on its first write, and all of it is committed with the
write that asked for it. `office status` checks a drafting table that
exists against the catalog.

| page | what | who writes it |
|---|---|---|
| `blueprints/DATE-SLUG/blueprint.md` | one arc: charter, decomposition, watch list, history | a sitting, or `office blueprint open` and `ratify` |
| `blueprints/DATE-SLUG/close.md` | the arc's close report, filed | the sitting `office blueprint close` sends out |
| `agenda.md` | questions awaiting a sitting | `office agenda add`; a sitting rules and moves the item to Disposed |
| `rulings.md`, `evidence.md` | the ledgers, filed | a sitting only; `office rulings` and `office evidence` read them |
| `watches.md`, `watch-log.md` | the watches register and its log, filed | a sitting; `office watches check --record` appends fired records |
| `digest.md` | the sitting-open page, derived | `office digest`, and `office start` before a sitting; never by hand |
| `riders.md` | riders with no carrier yet, and pointers to carried ones | `office rider add` and `carry` |
| `moves.md` | desk moves a sitting decided | a sitting; `office moves` applies and ticks them |

Blueprints. `office blueprint open SLUG` drafts one from the template:
the charter (`--charter`, or stdin; asked on a terminal) and a drafted
History line. `office blueprint ratify ID --words notepad/PAGE` (or
`--sid SID`) writes the charter's ratified line and a ratified History
line, committed alone. It refuses an empty charter, one already
ratified, and a closed blueprint. From then on `office status` checks the
charter's bytes against git from the ratifying commit on; a charter that
must change is a new blueprint whose History opens `supersedes:
blueprint ID`. `office blueprint close ID` sends out the sitting that
closes the arc, the way `office start` sends any session out. It opens
a folder born for the close (`Close blueprint ID`, `source: blueprint
ID`) unless one is on the desk. It ships the blueprint, its member
folders, the rulings, evidence and watches pages and the close report's
template from the install. It forecasts that folder, the notepad and the
drafting table. You attach the tray and paste the opener; `office land`
brings it back. A blueprint is closed when its close report exists.

Desk moves. A sitting writes its decisions about folders as lines on
`moves.md`, `- [ ] DATE MOVE ...`. The moves are `open "TITLE"
key=value...`, `queue folder N`, `gate folder N after="X"`, `close
folder N`, `absorb folder N into="folder M"`, `split folder N
into="A,B"` and `retire folder N why="..."`; the page's own text lists
the keys. `office moves` applies every pending line in order through
`office open`'s, `office close`'s and the gate flags' own code. It ticks
each line with the folder it acted on (`- [x] ... -> folder N`), writes
an opened folder's number onto its blueprint's decomposition line, and
commits everything at once. A line that does not read is named before
anything is applied. A line that cannot be applied stops the run there,
with the lines before it applied and committed. `--dry-run` lists what
it would apply.

Riders. `office rider add TITLE --source SRC [--rides GLOB | --carrier
"folder N"]` adds rider N to the riders page; its text comes from stdin
(a worker's Proposal, kept byte for byte) or `--text`. Numbers count the
page and every folder and are never reused. `office rider carry N
--folder M` moves the rider into folder M's Riders section and leaves
one pointer line on the page. `office rider consumed N SID` records it
consumed at a session. `office riders` lists them all; `--orphans` shows
the riders in a closed folder that were never consumed, and `--forecast
PATH...` the queued riders a pack with that forecast would carry.

The agenda and the ledgers. `office agenda add TEXT --source SRC
[--waiting "folder N"]` puts a question on the agenda for a sitting; a
folder waiting on it gates with `--after "agenda N"`. `office rulings`
lists the rulings. `office rulings ID` renders one with its amendments,
who supersedes it and where it was derived. `office rulings --check`
resolves every citation on the drafting table and the desk (`folder N`,
`blueprint ID`, `ruling ID`, `evidence N`, `watch WN`, `rider N`,
`agenda N`, notepad pages, session ids) and exits 1 when one does not.
`office evidence [N]` lists the evidence ledger, or renders one entry,
with occurrence counts by attribution, and names any record the ledger
should not hold.

Watches. A watch is an entry a sitting writes on `watches.md`, `## WN -
Title` with `source`, `scope`, `condition`, `evaluates`, `threshold` and
`re-trigger` lines; its state is read from the watch log, never written
into it. It evaluates `query NAME`, one of the queries in the install's
`share/watch-queries.toml`, or `eye`. `office watches` lists the open
ones (`--all` the closed too) with their last record. `office watches
check` runs each open query watch over the window since its last fired
record, from the day after it (bale's `stats --since` takes a day); a
watch never fired looks from the day it was opened. It reads the office's
own registry and each project, one line each: `fired`, `not fired`, or
`cannot evaluate`. A query bale cannot answer says `cannot evaluate: bale
does not stamp ... (slip)`: today the HOLD cause class (watch 15) and the
amendment-accept marker (watch 17). Every eye watch is `needs an eye`
with the sittings since its last record, flagged after three. The
standing lines, `claim-basis-split` and `hold-rate-by-class`, are printed
as `observed`, over bale's whole corpus. `--record` appends a `fired`
record for each watch that fired and commits the log alone; re-arming,
rewording and closing stay a sitting's.

The digest. `office digest` writes `digest.md` and prints it: versions
per project, what happened since the last sitting (the sessions applied,
held, bailed and still open, the folders opened and closed, and what was
added to the drafting table), the watches, the standing lines, the desk,
the agenda and the open blueprints. The last sitting is the latest
sitting's page in the notepad, by the commit that filed it, and the page
says which. Every line is computed; the page is rewritten on every run.

Every one of these scripts that mints a number or adds to a page refuses
while a session open in the office's own bale registry forecasts what it
writes, and names that session: the one-writer rule. The riders page and
the agenda are checked against their committed bytes before the commit
(an append, and one entry put in above the Disposed list).

### Sending a session out: the details

    office start                       # your downloads' new bundles by key, then which job by key
    office start fix-login --on office-src --goal "Fix the login redirect"
    office start plan-wave --in-office --read-only --goal "Plan the next wave"
    office start fix-login --on office-src 2026-10-05-fix-login.bale-bundle   # a planner's bundle
    office start fix-login --on office-src --goal "Fix it" --no-rides         # nothing declared rides this time
    office start fix-login --on office-src --goal "Fix it" --carry 3          # rider 3 rides in the folder
    office start new --on office-src 2026-10-05-fix-login.bale-bundle         # a new folder for a planner's bundle
    office start fix-api --on api --goal "Wire the health route" --write src  # api is on a host: packed there
    office start --drop in-tray/2026-10-14-login-error.md                     # a drop, straight out on its project
    office start --drop 2026-10-14-login-error --lane alpha --size medium     # ...naming the project it did not

`office start` packs a session for a folder and gathers everything to
attach into one out tray, `~/out-tray/SID`: the request, the doctrine,
and what rides with the work. On a project, the session is packed from
the project's repo with the constraint "Office context informs this
session but never lands in this project.", and the office's context
(the folder and the hung items) rides beside it as a context tarball,
with each path the project declares (`office projects set`). In the
office, it is packed from the office, forecasting the folder and the
notepad, and the project the folder's lane names rides beside it with
its declarations. On a terminal it lists what the project declares to
ride, with sizes, and asks which ride this time: a plain return rides
them all; `none`, or the numbers to leave out, keep them home for this
session only (`--leave-out PATH`, `--no-rides`; piped, everything
declared rides). The doctrine rides once: a project whose own tree
carries the same `doctrine/` (office-src's) ships it there, and one
whose `doctrine/` differs gets the install's beside it, named as the
install's. Before it packs, start surveys the machine again and commits
the page, so the survey every session reads first is current. Before it
packs a sitting (`--read-only` in the office, or a bundle that forecasts
nothing), it writes the digest again and commits it, and the drafting
table rides inside the sitting's request; an open session holding the
drafting table leaves the digest as it was and never stops the start. A
bundle named by a bare name, which bale's search finds, is read where
bale's rehearsal found it, so a sitting sent out that way gets its digest
too (since 0.21.0); when start cannot read a bundle's pack line at all, it
cannot tell a sitting, and it says so in one line, with the time the
digest it left was written. A scoped office session gets no digest. The forecast of a project session comes from the
folder's lane, the work class from its class, the slug from its name;
the goal is the one thing asked. It records the session in the folder
and prints the opener: attach the tray's files to a fresh chat and paste
it. A session whose forecast overlaps one already open is refused before
bale runs, naming the open one; office sessions take turns on the
notepad. Every question has a flag (`office start --help`); piped, it
asks nothing and names the flag it needed.

A planning sitting hands over the sessions it authors as bundles
(`.bale-bundle` files). Give one to `office start`, as a path or as the
bare name bale's own search finds (`--bundle FILE`, or the file as a
word): it asks which job and where the work lands, as for a pack, then
hands the bundle to `bale open` there. The bundle's pack line is the
whole session, its goal, forecast and brief; the office adds nothing to
it and says when it leaves out something the office would have carried.
Before it writes anything (a folder for `new`, the survey, the tray),
start asks bale whether it can open the bundle there, with `bale open
--check`, which finds a bare name through bale's own search, runs every
gate bale runs before an open, and writes nothing: a name bale cannot
find, a forecast path that is not there, or a forecast another open
session holds stops the start in bale's words, with nothing written. For
`new`, where the work lands is asked first and the bundle checked before
the folder is opened (a bundle that lands in the office is checked once
its folder exists, since its forecast may name the folder).
Where the work lands defaults to the one place whose tree holds every
path the bundle names, and the question's `?` says why; a bundle whose
paths no one place holds, or one sent where its paths are not, is
refused before bale runs, naming each path and where it is.
When the bundle is a file the office can read, the office checks its
forecast against the open sessions too, and names the session, its
folder and the overlap. A second desk is bale's to recognize, and the
office refuses an overlap only where bale would. From bale 0.4.50 start
asks `bale open --check --json`. Where bale's rehearsal refuses the
bundle, the office refuses it in its own words with bale's reason beside
them; where it passes (a bundle whose session is still open, which bale
takes as one more desk on it), the office says what its check saw, prints
bale's own second-desk line, and goes on. With an older bale the overlap
is refused before bale runs, as for a pack. Given as a bare name bale's
search finds, the bundle cannot be read first, and `bale open --check`
says it in bale's words before anything is written.

Which session the bundle is in is read from bale's registry: the
sessions open after `bale open` that were not open before. A bundle
whose session is still open (opened from it earlier, say, and its
browser copy `NAME (1).bale-bundle` started again) mints nothing. bale
0.4.44 and later take it as a second desk on that session. From bale
0.4.50 the office runs `bale open --json`, which says so, and carries the
desk:

- the folder records the session as a second desk;
- the tray holds that session's request;
- the opener is the desk's;
- start's first line says `Joined SID, already open, as a second desk`.

With an older bale, a start that finds nothing newly open names the
second desk as the likely reason.

The riders a pack carries ride with it. When the office has a drafting
table, start runs `office riders --forecast` over the pack's forecast
before it packs: on a terminal it offers each queued rider on the riders
page whose path glob the forecast touches (a plain return carries it),
and carries the ones taken into the folder's Riders section (`office
rider carry`), so they ride in the request. Piped, it carries none and
names each that matched; `--carry N` carries rider N without asking, and
`--carry none` carries none. A rider's glob may name its project first,
as a lane does (`office-src: bin/`), so only a pack on that project
carries it.

`new` opens the folder through `office open`'s questions, title first:
a title already on the desk is offered as the folder to start, before
anything else is asked. When start opened the folder itself and the
session then does not go out, the folder stays (the job was asked for),
and start's last lines name it and print the one line that retries it
with the answers already given, for instance `office start
2026-10-06-third-trip --on office-src 2026-10-07-third-trip.bale-bundle`.
When the brief carries a page of the sitting's words between
`--- NOTEPAD PAGE BEGIN notepad/DATE-SLUG.md ---` and
`--- NOTEPAD PAGE END ---`, `office start` files that page in the
notepad and commits it alone; a page already filed with the same words
is left as it is, and a different one at that path is refused loudly and
never overwritten. This works for a brief given with `--brief` too.

A project on a host (`office projects add --host`) is packed on its
host, where its bale is and where it will land, and you see the same as
for a project here: the survey, the riders, the ride-alongs question,
the overlap refusal in the office's words, the session recorded in the
folder, and one out tray on this machine holding the request, the
doctrine, the office's context and each ride-along, with the opener
printed (and on the clipboard on WSL). Before anything is written, start
makes one connection to the host: a host that does not answer stops the
start there, with your connect line; a bale there below the read side's
floor is refused, naming `office projects level-bale NAME` (start never
upgrades a bale on its own); and the repo there must be one bale runs
in. Then bale's pack runs on the host through the project's shell, a
`--brief` travelling there first, and the request bale makes is carried
back into the tray (it stays in the repo's outbox there too); the
office's context, the doctrine and the ride-alongs are made here, as for
any project. A bundle travels to the host too, and `bale open --check`
and `bale open` run there on that copy: a bundle for a hosted project is
a file here, its path or a bare name found in this machine's downloads
(the `downloads` setting below; of several browser copies of the name,
`NAME (1).bale-bundle` and so on, the newest is taken and named), since
bale's own search for a bare name would run on the host. Where a
bundle's paths decide where it opens, a hosted project answers through
its shell. The one temporary directory
start makes on the host (under its TMPDIR, or /tmp) is removed whether
the start succeeded or not. A step bale asks you about runs through the
attended form of the shell (`ssh -tt`, and a container's `-it` for its
`-i`, derived from the project's `shell`), with your terminal as its
input; piped, nothing ever asks. One start reaches the host once (the
reach is carried from one step to the next) and the reads it needs there
share a connection: a pack makes about four connections, five with a
brief, eight for a bundle (0.15.0 made seven, ten and eighteen in the
suite's count).

The in-tray rides too (0.19.0). Every session start sends out carries
each drop in the in-tray whose status is `unsorted`: in the pack's
includes for an office session, in the office's context tarball beside
the request for a project session (made here, for a hosted project as
for any other), and, for an office session from a bundle, as
`context-in-tray.tar.gz` beside it, since the office adds nothing to a
bundle. The out tray's listing says how many ride and where, and the
opener ends with one line saying so. The goal is the session's own; what
a carried drop asks of the session is the doctrine's (section 4).

`office start --drop PAGE` sends one drop out on its own, as a project
session. It mints the folder through `office open`'s code: the title is
the drop's first line (`--title` overrides), the lane the drop's project
when that is one of the office's (else asked on a terminal and refused by
name when piped; `--lane` is the twin, the project alone or `project:
paths`), the size asked with small as its default (`--size`), the source
`drop`, the slug the drop's. It moves the page into the folder as
`drops/NAME.md`, bytes as they are, and writes `- DATE dropped:
drops/NAME.md, via ...` in its History before the `opened` line. Then it
packs the session as `office start FOLDER` does for the lane's project,
with the goal "Sort the dropped message and do what it asks" (`--goal`
overrides) and a brief from the install's templates/drop-brief.md: sort
first (what it means, which part of the project, whether it is one job,
what you must be told), then do the work. While an open session in the
office's registry forecasts the in-tray or the desk it refuses and names
the session; every refusal comes before anything is written. If the
session does not go out after the folder is minted, the last line is
`office start FOLDER --drop NAME`, which finds the page in the folder.

A folder that knows its goal and its brief goes out with them (0.20.0).
A folder with a `goal` line (`office open --goal`, or a drop office moves
filed in it) offers it as the session's goal: a plain return takes it,
piped it is taken, and `--goal` overrides it. A folder with a brief.md (a
sorted drop's Brief) sends it as the request's brief, unless `--brief`
names another; a bundle keeps its own brief, and start says so. The
folder rides as it always has, the drops in its drops/ with it.

`office start --sort` is the standalone sort (0.20.0): an office session
for the drops nothing carried, belonging to no folder. It packs from the
office with the goal "Sort the in-tray's drops" and a brief from the
install's templates/sort-brief.md: what to decide for each drop, every
unsorted drop between its DROP markers, the desk as `office desk` prints
it (so the session routes to folders by number), and the Sort format.
It ships every folder's folder.md (not the folders whole), the handbook,
the hung items, the drops and the doctrine, and forecasts the notepad
and, where the office has a drafting table, drafting-table/moves.md (made
from its template first when it is not there), on which the session
writes the moves the desk needs that are not drops: `- [ ] DATE close
folder N` for a finished folder, `absorb folder N into="folder M"`,
`retire folder N why="..."`. Its id carries the slug `in-tray-sort`; the
walk-in shows it in flight as the in-tray's session, and `office land`
(or `office land SID`) brings it back. It is refused while another sort
is out, while an open session holds the in-tray, and when no drop is
unsorted, with nothing written. The Next line names it for an unsorted
drop whose project is none of the office's once a session has gone out
since it was dropped, and for three or more unsorted drops when nothing
is ready on the desk.

The handbook's chapter for a project rides with every session whose
folder's lane names it (in the office's context for a project session,
in the request for an office session), and every chapter rides with the
sort.

On WSL the out tray opens in Explorer and the opener goes on the
clipboard. The office knows it is on WSL when the kernel's version string
names Microsoft, and finds `explorer.exe` and `clip.exe` on the PATH, as
WSL puts them there. Two variables steer those two reads, and the test
suite is what sets them: `OFFICE_PROC_VERSION` names the file read for
the kernel's version (empty: not WSL), and `OFFICE_DESKTOP_PATH` lists
the directories searched for a desktop program (`clip.exe`,
`explorer.exe`, and the clipboard readers `office probe` offers) in place
of the PATH (empty: none). Neither is needed for everyday use.
`~/.config/office-src/machine.toml` holds this machine's own settings,
outside every office:

- `out_tray = "~/somewhere"`: where out trays go (default `~/out-tray`).
- `clipboard_command = "..."` and `open_command = "..."`: the two desktop
  steps; `""` turns one off.
- `downloads = ["/mnt/c/Users/you/Downloads"]`: the directories your
  browser saves downloads into, a list. `office land` finds a hosted
  session's response there by name, and `office start` a bundle for a
  hosted project; for a project here, land uses it only to pick the
  newest of several copies of a response. The office writes it the first
  time a verb needs it on a terminal, offering this machine's likely
  directories (`?` explains it), and never asks again; a piped verb that
  needs it refuses and names the key. It is the office's setting: the
  office never reads bale's config, whose search directories it lists for
  bale alone.

### Bringing a session back: the details

    office land                          # the session out: bale apply, how it ended, the relay
    office land fix-login                # the session out for a folder
    office land response-2026-10-05-fix-login-001.tar.gz
    office land fix-login --close        # piped: close the finished folder with the landing

`office land` finds the session a response answers (the one the office
has out, asked for when there are several; a session id, a folder or a
response file names one) and runs `bale apply` in the repo it belongs
to, `bale retry` when bale held it. bale reads your terminal, so its own
questions (an admission, the merge, a hook) are asked by bale and only
you answer them; the office passes it nothing that answers one. The
response is found by bale, by name, in its search directories. When the
`downloads` setting is there and holds several copies of the name (a
browser saves the second as `response-SID (1).tar.gz`, which a corrected
response after a HOLD usually is), land passes bale the newest by its
path and says which; bale's own search would take the plain name first.

After an applied landing, before the after-land actions, land files what
the session's notes.md says (0.20.0), when it found the response on this
machine, each section in a line: a project session's Walkthrough and
Delivery as the folder's two pages; then any session's `## Sort`, each
`### NAME.md` subsection appended to the drop's page (in the in-tray, or
the landed folder's drops/) as a `## Sort` section, its first line `-
sorted: DATE, by SID` and the rest the subsection's, word for word, the
page's status set to sorted (a page sorted already is left as it is; a
subsection naming a page that is nowhere is said and skipped); its `##
Questions and answers` lines in the folder, after a line naming the
session; and its `## Handbook` facts, each as `- DATE: fact (SID)` at the
end of the project's chapter, with a Sort's `facts:` lines, and a `####
Front sheet` in place of the chapter's, whole; and its `## Structure`,
the folder's title, size and goal as the session judged them, each filed
over a field the folder marks provisional, the rest kept as they are, in
one line saying what changed. The handbook arrives with
the first fact: handbook/README.md from the install's template, the floor
plan's entry with the front page hung, and bale.toml's trigger and pull.
Then, when a sorted drop waits in the in-tray (or the session was the
standalone sort and its moves page holds pending lines), land runs
`office moves` and prints the folders it minted. When only bale's own
search found the response, land names the line that files it all:
`office sessions FOLDER SID --pages FILE`, or `office sessions --in-tray
SID --pages FILE` for the sort.

`office moves` applies the in-tray's sorted drops first, oldest first,
then the moves page. A drop sorted `folder: new` gets a folder minted
through `office open`'s code (the title from the drop's heading, the slug
from its name, the lane its Sort's project, the size and the goal its
Sort's, the source `drop`); one sorted `folder: N` goes to folder N on the
desk. The page moves in whole, the folder's brief.md is written from the
Sort's Brief, its History gains `- DATE dropped: drops/NAME.md, sorted by
SID`, its goal is written when it has none, and the Sort's `tell:` goes on
its Next, which `office desk` shows. A drop whose project is none of the
office's, whose folder is in the filing cabinet or not there, or that an
open session's forecast holds, is said and stays; the rest go on. The
walk-in counts sorted drops waiting as pending desk moves, and `office
desk` lists each.
A path you give always wins. How it ended is read from
bale's records and said in a line. Whatever bale prints for you to carry
(the relay for the planner, and on a HOLD the worker's block first) is
printed whole and, on WSL, put on the clipboard; a clarification's block
for the planner comes from `bale relay` and is printed too. After an
applied landing the copy is land's very last step, after the after-land
actions, so it is the last copy made (bale copies the same block, earlier,
and its copy loses every non-ASCII character on WSL). The office reads the
clipboard back and says the block is there only when it is; a copy it
cannot make, cannot confirm, or that reads back otherwise is said in a
line, and the block is printed again, whole.

After an applied landing it runs the project's after-land actions in
its repo, in order (`office projects set NAME --after-land ./install.sh`
declares them), stopping loudly at the first that fails with the lines
that rerun it and the rest. It asks nothing about ratification (0.23.0):
the planner ratifies in the next brief it writes, a `--- RATIFIED SID ---`
line that `office start` files in the folder. `--ratified` (with
`--except TEXT`) still records one by hand; `--not-now` changes nothing.
Its last lines say what became of each action (ran, failed,
not run), or that the project declares none. Before those last lines it
runs `office watches check` (it records nothing) and prints the watches
that fired, since a landing is what changes the counts a watch reads; an
office with no watches register prints nothing for it, and the check
never fails a landing. When the session was the founding session and the
profile is now complete, it closes the founding folder, done. When the
folder records that session alone and it landed applied, the job is
finished, and on a terminal land closes the folder, done, naming the line
that reopens it (`--close` and `--leave-open` answer it without asking;
piped with neither, the folder stays open and land says so). The actions run only
through `office land`: a session applied by hand with `bale apply` runs
none, so office-src's own `./install.sh` does not run, and `office
status`'s `source:` line then says the install is behind its working
copy, with the line that brings it level; when the office scopes that
working copy, the walk-in says it too, and its Next line is that line.

A read-only sitting the office sent out lands nothing; when it is over,
`office land SID` (or the folder) ends it: `bale unlock` in its repo,
and an `ended` line in the folder's History. The folder stays as it is,
since a planning folder may outlive one sitting; `office close` is
yours. A HOLD, a refusal or a clarification lands nothing: nothing
runs after, and the next line is named. An office
session's folder changed after its pack, when `office start` recorded the
session; `office land` puts it back as it was packed while bale lands, so
bale never refuses the response over it, and records the session again
after.

A session on a project on a host lands there, and you see what you see
for a project here. Land first checks that the host answers (one
connection; a host that does not stops land before anything is carried,
with your connect line and the line that reruns it). The response is
found on this machine: the path you give, a name you give (the current
directory, then the downloads), or else the newest copy of
`response-SID.tar.gz` in the downloads, named when there were several;
after a HOLD, with one copy only, land asks for the corrected one (piped,
it names the copy it saw). It is carried to the host into one temporary
directory, checked by sha256, and `bale apply` (or `bale retry`) runs in
the project's repo there through the attended form of its shell, so
bale's questions reach you; the directory is removed by the same command
once bale is done, or after it on a failure. How it ended is read from
bale's records there; the relay is printed here whole and, on WSL, put on
this machine's clipboard. A clarification's block comes from `bale relay`
run there, and the next line is one you type here that pipes the
planner's answer to `bale relay SID -` there. The after-land actions run
in the repo there, one connection each, attended on a terminal, and a
failing one names the line that reruns it from here. A read-only sitting
there ends with `bale unlock` there. A hosted land makes about four
connections, plus one per after-land action.

### Running a worker's probe: the details

    office probe FOLDER                  # the block from the clipboard (paste_command, asked once)
    office probe FOLDER probe.sh         # from a file
    office probe FOLDER - --yes < probe.sh

A probe is a worker's tool call whose courier is you (TARBALL.md 4.6);
`office probe` carries it. The block comes from a file, from stdin (`-`),
or, given neither, from the clipboard, read with `paste_command` in this
machine's `~/.config/office-src/machine.toml`, beside `clipboard_command`
and `downloads`. It is asked once, on a terminal, the first time a verb
needs it, with this machine's likely command offered: on WSL, PowerShell's
`Get-Clipboard` through `powershell.exe` (its output made UTF-8, the CR
of each line dropped); elsewhere `wl-paste`, `xclip`, `xsel` or `pbpaste`,
whichever is on the PATH. `?` explains it. Piped, a probe that needs it
refuses and names the key; `""` turns it off. A chat's code fence around
the block is fine.

Before anything runs, the office reads the block. One with no `PROBE
BEGIN` line is not a probe block, and one whose purpose header (the
comment lines before its first blank line) does not say it is read-only
is not run: both are refused by name, before any host is reached. Then
it finds where the block runs: the project the folder's lane names, or
`--project NAME` (asked on a terminal when the lane names none;
`--project office` is the office itself). It finds the session the probe
is for: the session the folder records that is open there, by bale
status; with several, the one the block's slug names, else `--sid`. A
folder with none gets no probe run, since a probe is a session's. A
`probe-output/` already where it runs stops it too, since a fallback
probe's output could not be told from it. On a host all of this is one
connection, which is the reach. Then it shows the header and where the
block runs, and asks once, `y` or `N`, default no; `--yes` is the flag
twin, and piped, nothing runs without it.

The block runs with its stdin closed: in the project's repo, or through
the project's shell in its path, in the plain form with no terminal
asked for (a probe never waits on one), or in the office root. Its
stdout and stderr come back to your terminal whole, as they come. The
lines from `PROBE BEGIN` to `PROBE END` go on your clipboard with the
office's own `clipboard_command` (on WSL, `clip.exe`), since the block's
closing `bale clipboard` step runs where no clipboard is; the office says
how many lines came back between the sentinels and whether the integrity
trailer's count matches them. A block that never closes is said, and
nothing is copied. `OFFICE_PROBE_TIMEOUT` (seconds, default 1800) stops a
block that runs past it.

The file-based fallback (TARBALL.md 4.4) leaves `probe-output/` where it
ran. The office carries it to the session's out tray,
`~/out-tray/SID/probe-output/` (`probe-output-2/` beside an earlier one),
and removes it where it ran, since the office leaves nothing on a host
outside the project's repo and a probe's output is not the repo's; its
files go back to the worker with the paste. On a host the directory
travels as one tar stream through the shell, its file count held to the
far side's; one that does not arrive whole is left where it is, and said.

The folder's History gains one line per run, `- DATE probe: SID, N
lines`, so a sitting can count a session's probes. An open session in
the office's own registry whose forecast holds the folder keeps the line
out (the one-writer rule), and the line it would have written is printed
instead.

### Delivering to the audience: the details

The audience line (doctrine section 2): a project holds what its
audience may read, and the office what only you may. bale lands a
session in the project's workbench clone with its own marks, `[bale SID]`
commits, `Merge bale SID` merges tagged `applied/SID`, `bale/SID`
branches, `[bale sweep SID]` records, and that branch is never the one a
coworker reviews. `office deliver FOLDER` is the crossing:

    office deliver health-route                  # shows what leaves, asks once, pushes the branch
    office deliver 14 --yes                      # without asking
    office deliver health-route --branch api-health --others-too

The project is the folder's lane's (`--on PROJECT` when the lane names
none), and it must declare an `audience`: the name of the remote in its
clone that points at the audience's git host, set with `office projects
add` or `set --audience origin`; a project with none (the home office's
own, say) is refused by name. The folder must record at least one
session applied in that project. In order, each step logged:

- The audience's base branch is fetched (the project's `base`, or the
  audience remote's HEAD branch read from the clone), and the delivery
  branch when an earlier delivery made it: a second delivery for the
  same folder adds to the same branch.
- The landed work since the last delivery, or since the workbench branch
  and the base parted, is read: every applied session in it is named by
  its id and the folder it belongs to. Sessions of other folders ride in
  the same delivery (the office does not split one branch's history by
  folder); deliver says so, names them, and on a terminal asks whether
  to go on (`--others-too`; piped, it refuses without it).
- The words come from `desk/FOLDER/delivery.md`: the commit subject and
  body, the review request's title and body, and `- to: NAME` for the
  reviewer (the install's templates/delivery.md says the shape; a build
  session writes it and `office land` files it). Missing, deliver stops
  and says what to write where.
- In a temporary worktree at the audience's tip the landed work is
  squashed on (`git merge --squash`), the names bale makes are taken out
  of the index whatever the clone tracks, and the diff and the words go
  through the letterhead check; one hit refuses the delivery, with
  nothing pushed.
- The diff's stat, the sessions covered, the author, the branch (named
  from the folder's slug, or `--branch NAME`) and the words are shown,
  and deliver asks once (`--yes`; piped, it refuses without it).
- The words become one commit (several when `delivery.md` has several
  Commit sections, each but the last naming on a `paths:` line what it
  takes), authored and committed as the project's `author` (`Name
  <email>`, or the clone's own identity), and that commit alone is
  pushed as the delivery branch, with its name in `OFFICE_DELIVERY` for
  the push guard; never the workbench branch.
- The folder's History gains a dated `delivered` line: the branch, the
  audience, the sessions covered, the workbench commit and the delivery
  commit. Then what you do next: open the review (a URL when the git
  host's compare-URL shape is known, GitHub, an enterprise instance
  named github.*, or GitLab, with the review's title and body in it and,
  on WSL, on the clipboard; the branch's name otherwise) and whom to
  send it to, when the words name a reviewer.

The delivery is built on this machine, where the audience answers with
your credentials: for a project on this machine in the clone itself, in
refs the office owns (`refs/office/...`, gone after); for a project on a
host the landed commits come here as a thin git bundle made in the clone
there and carried through the project's shell, into a temporary bare
repo removed after, and the push goes from here. Nothing the office
writes on a host outside the project's repo is left. A hosted delivery
makes three connections (the clone's facts, the bundle, its read). A
conflict with the audience's base refuses with the remedy: bring the
base into the workbench branch first, land that, and deliver again.

The push guard. Declaring an audience (`office projects add --audience`,
`set --audience`) writes a pre-push hook into the clone's `.git/hooks`,
outside what git tracks, as `--prepare` keeps everything the office
writes; `office deliver` installs it when it is missing. It refuses any
push to the audience from the clone, by name or by URL, naming `office
deliver`; deliver's own push names its branch in `OFFICE_DELIVERY`, and
the guard lets that branch through and nothing else. A clone with
`core.hooksPath` set, or another pre-push hook, is said and left alone.
Known gap: a push from the host itself is not built (the probe found the
work host's credential cache empty, so nothing reaches the audience from
there without a prompt); the delivery crosses from this machine.

The letterhead check:

    office letterhead check                      # the files the tree here changed, as they are
    office letterhead check --all ~/work/api     # the whole tree
    office letterhead check --on api --range origin/main..HEAD   # in a project's repo, on its host
    office letterhead check --words desk/14-health-route/delivery.md

It names every line that holds what the letterhead refuses, as
`file:line: what`, and exits 1 with a hit. What it refuses is one list in
the install, share/letterhead.toml: the names of models, vendors and
products; tell-tale phrasing an assistant writes and a person does not;
and bale's marks (its commit subjects, `applied/` tags, `bale/` branches
and session ids); plus, when the office has `letterhead/forbidden.txt`
(a later space; the check reads the file when it exists and never
creates it), each non-blank, non-comment line of it as a fixed string.
The suite's own text rules read the same list, so office-src's text is
held to it too. Scope: the files a range changed and its commit messages
(`--range A..B`, which is how deliver checks a delivery's diff); else the
files a dirty tree changed, as they are; else the whole tree (`--all`,
or a directory that is not a git repo, said so). `--words FILE` checks a
text as it is. Binary files are skipped by name and by a NUL byte;
`OFFICE_DEBUG=1` names every file read. `--on PROJECT` runs it in the
project's repo, through its shell on a host, where the check travels as
the program python3 reads from stdin and writes nothing.

### Which sessions worked on a job

`office start` records the session it packs. When you pack one for a
folder by hand, pipe bale's report into the folder, so the id is never
typed:

    bale pack --json --include desk/2026-09-24-fix-login "Fix the login redirect" | office sessions fix-login -

`office sessions fix-login` lists what is recorded, and under each id
what bale records about the session: its outcome, dates, claims beside
verdicts and exchange rounds. The folder keeps the id and any words you
add with `-m`; it never copies what bale records about the session.

The folder's two pages. Nearly every job produces two deliverables
(doctrine section 3, principle 6): the thing, in the project, and the
message about it. A build session writes the message as two sections at
the end of its notes.md, Walkthrough (what changed, why, how to explain
each piece, the questions a reviewer will ask, a hand test for what only
eyes can check) and Delivery (the commit subject and body, the review
request's title and body, `- to: NAME` for the reviewer), each heading
one level down from the page's; the install's templates/walkthrough.md
and templates/delivery.md ride beside every build session's request to
say the shape, and the folder's own Walkthrough and Delivery sections
point at the pages. `office land` files them in the folder as
`walkthrough.md` and `delivery.md` after an applied landing, when it
found the response on this machine (a path, or by name in the
downloads); when only bale's own search knew where the response was,
land names the line that files them:

    office sessions fix-login 2026-10-05-fix-login-001 --pages ~/Downloads/response-2026-10-05-fix-login-001.tar.gz

Folders from before 0.17.0 are not rewritten; the pages file into them
all the same.

### The projects an office scopes, and what bale records about them

    office projects                          # the projects this office scopes, and where each is
    office projects add office-src ~/office-src   # add one (asks on a terminal for what it was not given)
    office projects add api ~/development/api --host me@workhost --prepare   # one on another host
    office projects add api ~/development/api --host me@workhost --from ~/work/api   # bring a clone there
    office projects level-bale api           # the host's bale brought level with this machine's
    office projects set api --shell "ssh me@workhost docker exec -i -u me box bash -lc"
    office projects set api --connect "start the VPN client, then retry"
    office projects set office-src --ride ~/other-repo/docs --after-land ./install.sh
    office projects set api --audience origin --author "Pat Example <pat@example.org>" --base main
    office projects --ledger                 # trust ledger per project and work class
    office projects --landed bin/office      # the last applied session that landed a path
    office projects office-src --versions    # the version trail of one project

The floor plan's [projects] table names each project and the path of its
repo; `office projects add` writes it, and checks the path is the top of
a git repo bale runs in. The repo is on this machine, or on a host the
office reaches over ssh: `--host HOST` (user@host, or an ssh-config
alias) puts it there, the path is then the path as that host's shell
sees it, `--shell PREFIX` is the command prefix that runs one command
where the repo is (default `ssh HOST bash -lc`; a repo inside a
container is reached with something like `ssh HOST docker exec -i -u
USER NAME bash -lc`; the office appends exactly one shell-quoted
command), and `--connect TEXT` is printed when the host does not answer,
in your own words for what brings it up (default `connect to HOST`). On
a terminal, add asks where the repo is after the path, then the shell
and the connect line with their defaults shown; `office projects set
NAME` offers to keep them, and `--on-this-machine` takes a project off
its host. Before any step that needs the host the office makes one
short connection, never a prompt; a host that does not answer is one
line naming the project, the host, the connect text and the command to
rerun, and the command stops there, while the walk-in and `office
status` print that line in the project's place and render the rest. The
read side runs bale through that shell: the walk-in's In flight, `office
sessions FOLDER`, `--ledger`, `--landed`, `--versions`, `office watches
check` and the digest all read a hosted project, in a few connections
per command (each round of reads travels as one batch), and
`OFFICE_DEBUG=1` shows every shell call. `office status` says whether
each host answers and which bale is there against the read side's
floor, naming `office projects level-bale NAME` when it is behind the
floor or behind this machine's. `office start` packs a session on a
hosted project's host (Sending a session out: the details), and `office
land` lands it there (Bringing a session back: the details).

`--from CLONE` brings a clone on this machine to the host as the
project's repo, for a repo that is not there yet: PATH must not exist on
the host (add refuses before anything moves), and a clone of CLONE is
made at PATH with every local branch and tag, its remote-tracking refs,
and its remotes and branch settings as CLONE has them, with HEAD where
CLONE's is. It travels from this machine as a git bundle through the
project's shell (the host need not reach CLONE's git host, and nothing
is fetched there), is checked ref by ref against CLONE, and is then
prepared as `--prepare` prepares one; a clone that does not come out
level is removed again, as is the one temporary directory on the host.
Only what is committed travels: a CLONE whose working tree has changes is
named, with its changed paths, and add asks whether to go on without
them (piped, it refuses unless `--from-dirty-ok`). CLONE is never changed
or deleted; add says it can be removed once you are satisfied with the
clone on the host. On a terminal, add asks for it after the host
question ("is there a clone on this machine to bring?", default none;
`?` explains). A shallow clone is refused (fetch it whole first).

bale is installed per machine, like git, and a hosted project's bale
lives on its host. `office projects level-bale NAME` installs there the
bale this machine runs, the way bale's releases install: a release
tarball of this machine's install (its `user/`, git and records left
out) carried through the project's shell, and the host's own
`upgrade.sh -y` run on it, which moves the host's `<install>/user/` (its
global `bale.toml` and hook store) aside, replaces the rest, puts it
back and runs `install.sh`, which runs `validate.sh`. A host with no
bale on its login PATH gets it unpacked as `~/bale` and its `install.sh`
run. Nothing is fetched from the network there. It says what version
was there and what is there now, checks the version and `user/` again
afterwards, never moves a bale back (a host newer than this machine is
refused), and asks first on a terminal (piped, `--yes`).

A clone bale has not run in (no `.bale/`, no `bale.toml`) is refused
unless it is prepared: `--prepare` (offered on a terminal) writes the
four paths bale makes (`.bale/`, `bale.toml`, `.baleignore` and bale's
record directory) into the repo's `.git/info/exclude` and an empty
`bale.toml`, here or through the host's shell, so `git status` stays
clean, `git ls-files` is unchanged, and the repo's own `.gitignore`,
which belongs to its audience, is never touched; `bale config init`
there fills the `bale.toml` in. What the office writes into a project's
working copy is only ever outside what git tracks.

A project may declare what
rides beside every session on it (`--ride PATH`, repeatable: a directory
inside another repo, a whole repo, or a file) and what runs in its repo
after one of its sessions lands (`--after-land CMD`, repeatable; `office
land` runs them). `office
projects set NAME` asks for both on a terminal, and `office projects`
shows them. They live in the office, never in the project's repo.
A project with an audience declares three more, the audience line's
(`office deliver` reads them): `--audience REMOTE`, the name of the
remote in the workbench clone that points at the audience's git host
(origin, usually; checked against the clone's remotes; a project with
none is never delivered); `--author "Name <email>"`, the identity the
audience expects on the delivery commits (unset, deliver authors as the
clone's own identity, read where the clone is); and `--base BRANCH`, the
audience branch deliveries branch from (unset, the audience remote's
HEAD branch, read from the clone). On a terminal `add` and `set` ask the
three after the host question, defaults read from the clone;
`--no-audience` takes a project off the audience line, `--no-author` and
`--no-base` clear one. Declaring an audience installs the push guard in
the clone (above). Walking in shows the sessions
open in those projects and the folder whose Sessions section names each.
Everything here is read from bale's `--json` surfaces in each project and
rendered on every run, never copied into the office; the bale verbs,
flags and keys it reads are listed in share/bale-consumption.toml, with
the bale version they were written against, and `office status` says
when the installed bale is older than that.

### Hung items

`office init` writes a `bale.toml` whose include group pulls the office's
hung items (the profile and the survey, the handbook's front page once it
arrives, and whatever a renovation hangs)
into any pack whose includes touch the office. Pack lines need no
`--include` list for them. `office status` says when bale.toml no longer
matches the floor plan.

## Layout

| path | what |
|---|---|
| bin/office | the command (bash) |
| lib/office_helper.py | TOML, profile, survey, migration and floor-plan helpers (python3, standard library) |
| lib/office_bale.py | the only code that runs bale, through its --json surfaces: the read side and the renderings built on it (the desk's groups, the walk-in's Next line and the one-writer rule among them), office start's packing, bundles and out tray, and office land's apply and what it reads after |
| lib/office_host.py | a project on another host: the host, shell and connect keys, the shell that reaches it (every bale and git read of a hosted project runs through it, batched per round), the reach check, the check and the preparing of a clone for bale, here or there, and since 0.17.0 a clone's git facts, the push guard and a bundle carried back |
| lib/office_probe.py | office probe: a worker's probe block read (refused by name when it is not a probe or does not say it is read-only), where it runs and the session it is for, the run through office_host, what came back between its sentinels, and the fallback's probe-output/ carried to the out tray |
| lib/office_deliver.py | the audience line's crossing: office deliver's plan (the fetch, the carry, the squash, the check), its run (the commits, the push, the record) and what it abandons; office letterhead check --on PROJECT |
| lib/office_letterhead.py | the letterhead check, standalone (imports nothing of the office, so it travels to a host as the program python3 reads from stdin) |
| share/letterhead.toml | what the letterhead refuses: names, phrasing and bale's marks, one list for office letterhead check and the suite's text rules |
| doctrine/OFFICE.md | how every office works; it opens with a reading card naming what each kind of session reads, and what a build session reads sits above its PAST THE CORE banner |
| doctrine/checks/ | checks a session pastes into its validation; rides with the doctrine into every office session. filed-append-only.sh proves a filed page only grew at its end |
| share/spaces.toml | every space an office can have; the base ones are the default floor plan; a space files itself whole or as a list of paths |
| share/profile-shape.toml | the profile's required sections |
| share/bale-consumption.toml | every bale verb, flag and JSON key the office reads or runs, and the bale version they were written against |
| share/verbs.toml | what each verb ships, where it lands, whether a person must be present and what may set it off; a session kind with no declared landing may not run unattended |
| lib/office_drafting.py | the drafting table: its arrival in an office (the steps take the space they arrive, so the in-tray arrives through them too), the one reader of its pages (blueprints, riders, the agenda, the ledgers, desk moves), the citation grammar's resolver, and what the drafting-table verbs write |
| lib/office_drop.py | the in-tray: a drop's page, written and read, and its status line's one writer; the in-tray's arrival with the first drop; the unsorted drops office start carries, the desk lists and the Next line reads; the brief office start --drop sends; office status's in-tray line |
| lib/office_sort.py | the return of a sort (0.20.0): a notes.md's Sort, Questions and answers and Handbook sections read (fence-aware) and filed; a sorted drop's move into its folder; the handbook's arrival, its chapters and office status's handbook line; the standalone sort's brief and id |
| lib/office_watches.py | the watches: the query catalog, the register and its log, the check and its fired records |
| lib/office_digest.py | the digest: the sitting-open page, every section computed |
| share/watch-queries.toml | every query a watch can evaluate: the bale surface it reads, the value, how it compares, or the datum bale does not stamp yet |
| templates/ | profile, folder, clipboard series and sheet, handbook chapter, rolodex card, suggestion slip, notepad page; blueprint and close report; the drafting-table pages (drafting-table-*.md), each made into a page the first time a verb writes it; the folder's two pages, walkthrough.md and delivery.md, which ride with every build session; the in-tray's front page (in-tray-README.md) and the brief office start --drop sends (drop-brief.md); the handbook's front page (handbook-README.md) and chapter (handbook-chapter.md), and the brief office start --sort sends (sort-brief.md) |
| migrations/ | one file per breaking release; format in migrations/README.md |
| RELEASES.md | release notes |
| tests/ | the test suite; run.sh (with runner.py) runs it side by side |

Nothing here is copied into an office except the profile stub, which is
the office's own from the moment it is written.

## Versions

VERSION holds the release, MAJOR.MINOR.PATCH. A release is breaking
exactly when it ships a migration; every other release needs nothing
done in any office. Each office records the release it was built from
and the one it was last migrated to, and the command refuses loudly when
the two sides disagree in a way it cannot work across.

Only `office upgrade` writes an office's version stamp. A breaking
release that needs judgment ships a renovation migration declaring what
must be true once the renovation has landed. Upgrade opens a folder for
it (`upgrade-VERSION`, source `office upgrade`) and sends the renovation
session out through `office start`, with the migration's goal and a brief
carrying its summary, its `[landed]` declaration and its version; the
session forecasts what the migration declares under `writes`, or the
whole office. `office land SID` brings it back while the office is
behind, and the next run of `office upgrade` checks the declaration and
stamps the office. A renovation session already out is named, never sent
twice.

## Tests

    tests/run.sh                   # the whole suite, side by side (the default)
    tests/run.sh --fast            # the fast tier, under two minutes: what validation runs
    tests/run.sh --fast test_land  # the fast tier and all of one module (or a class, or a test)
    tests/run.sh --detach          # the whole suite in the background, for after a landing
    tests/run.sh --serial          # the whole suite in one process, as before 0.13.0
    tests/run.sh test_land         # one module, with its share of the serial group

The suite's clock. The whole suite takes many minutes, and bale's
contract gives a session's validation two; so validation runs the fast
tier and the whole suite runs where nobody waits for it. The tier is
`tests/fast-tier.toml`, defined there once: for every verb the command
dispatches (and the walk-in) a test that runs its entry point, then the
units, catalogs and text rules that cost little and guard much. The runner
holds it to the suite the way it holds the whole plan to `unittest
discover`, and a verb added to `bin/office` with no entry point in the
tier stops `--fast` before anything runs. A session adds what it touched
by naming it after `--fast`. `--fast` prints its wall time and fails when
it runs past the tier's budget (`budget_seconds`, 120). Each job's result
carries each test's time and every run writes `times.tsv` beside its
logs, slowest first: the place to look when the tier grows slow.
`--detach` copies the tree, starts the whole suite in a session of its
own at a lower priority and returns at once, printing one line that names
its verdict file under `~/.local/state/office-src/suite/` (or
`$XDG_STATE_HOME`), outside the repo: `RUNNING since ...` until it ends,
then one line, `OK`, `FAILED` or `BROKEN`, with the count, the time, the
commit it tested and the log to read; `latest` names the newest run, and
the ten newest are kept. It restores SIGINT for its tests itself. It is
meant as office-src's after-land action, so every landing runs the whole
suite without holding the terminal; and walking into an office that
scopes office-src's source shows the latest verdict, one `Suite:` line,
whenever it is not `OK` (a run still `RUNNING` after an hour counts as
not OK), so nobody has to go and read the file.

`tests/run.sh` runs each test module as its own process, four at a time
(`--jobs N`, or `OFFICE_TEST_JOBS`), since the modules share nothing and
most of a run is git and `office` subprocesses waiting on each other. The
classes that drive a terminal (the tour, the wizards, the terminal
starts) name themselves with `serial_group = "terminal"` and run one
after another in one process of their own, a lane beside the modules,
since their waits are timing-sensitive; a test keeps that list honest.
The plan is held to `unittest discover`'s count before anything runs, so
the whole suite still runs, each test as often as discover runs it. Each
job writes one log (`unittest -v`'s output) and the summary names every
job, its count, its time and its log, and for a job that failed, the
failing tests, each with the last lines of its traceback, and the log to
read (`--logs DIR` keeps them somewhere known; by default a new directory
under the temp directory, which WSL empties on a restart, so the
summary carries what a failure said). It exits 0
when every test passed, 1 when one failed, 2 when it could not run.
`--serial` is today's single process, `python3 -m unittest discover -s
tests -v`, which still works as it always did.

Since 0.21.0 the suite waits less, and no test checks less. The serial
lane holds only tests that drive a terminal: a class whose other tests
drive none was split in two, the terminal tests in a class of their own
(`...OnATerminal`) that keeps `serial_group`, the rest beside the other
modules, every test's body as it was. When the runner knows the last
run's times, the jobs start longest first: each job weighs the sum of its
tests' times in the newest finished detached run (its `times.tsv`, kept
with its verdict under the state directory), so the longest job is never
the run's tail. With none (a first run, a fresh HOME, bale's sandbox) it
runs as before, the serial lane first and then the modules by size, and
the run says which in one line. No job can read those times, since each
has a state directory of its own. And each run compiles the office's
modules and the tests once, into a bytecode cache in its scratch
directory (`PYTHONPYCACHEPREFIX`, handed to every job and, through each
`Env`, to every command a test runs): the command runs its Python with
`-B` so nothing is ever written beside an install, and before 0.21.0 it
compiled every module again on every call, which was most of the suite's
time. The cache is checked against each source as always, nothing but
the runner writes it, and it goes with the scratch directory; in everyday
use there is none and nothing changes.

Run the suite in the foreground, or with `--detach`. A background job
started from a non-interactive shell (`nohup tests/run.sh &`) inherits SIGINT ignored,
every process it starts ignores Ctrl-C, and the terminal tests that check
what an interrupt does then fail for that reason; the runner says so at
the start of such a run, naming them.

The suite builds offices, installs and synthetic migrations under
temporary directories and never touches your home directory or offices,
nor reads what this machine holds outside them. The runner gives every
job (and `--serial`) a HOME, TMPDIR and XDG directories of its own, an
empty git config and none of your `OFFICE_` settings, and removes them
after; each test's `Env` (tests/test_office.py) gives it its own HOME,
TMPDIR, config and downloads besides, and `tests/test_suite_clock.py`
fails the suite on a test file that names this machine's temporary
directory, expands `~` or reads HOME anywhere but there. The downloads question's
scan of the Windows users' homes (`/mnt/c/Users` on WSL) is pointed away
by `OFFICE_WINDOWS_USERS`, empty for none, or a directory a test makes.
No test writes your clipboard or opens a file manager, on any machine:
each `Env` says the machine is not WSL (`OFFICE_PROC_VERSION` empty) and
gives the test a desktop directory of its own as the only place the
office looks for `clip.exe`, `explorer.exe` or a clipboard reader
(`OFFICE_DESKTOP_PATH`), and the runner sets both for every job besides.
The tests that imitate WSL write a kernel version string of their own
and put fake Windows programs in their own tree. `tests/test_suite_clock.py`
fails the suite on a test file that reads the kernel's version or looks
a program up on the PATH outside `Env`, and on office source that does
either except through those two doors: every program `bin/office` and
`lib/` look up on the PATH is one the runner declares (git, python3, a
shell, the coreutils, iconv), the suite's fake bale, or a desktop program
found through the door.
bale need not be installed, and no real ssh ever runs: the read side's tests put a fake bale first
on the PATH that replays real bale output captured by a probe, kept in
the development record, and refuses anything it did not capture; the
hosted-project tests put a fake ssh first on the PATH too, which asserts
the target and the prefix it was handed and runs the one command locally
against a throwaway repo, so the fake bale answers through it; office
start's tests use a fake that packs, every line of it built from the
packs a probe captured, and office land's a fake that also applies, holds,
refuses and opens bundles, built from the applies and opens a probe
captured, and runs `bale open --check` from the checks a later probe
captured on bale 0.4.47. The audience line's tests use a bare repo on
this machine as the audience's git host, the clone's `origin` a local
path, so a delivery pushes for real and the tests read what arrived.
