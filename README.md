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
| walk in: what is out, what is ready, and the one command to type next | `office` |
| capture a thought | `office note TEXT` |
| drop a friction slip | `office slip TEXT` |
| start a job | `office open` |
| send a session out for it | `office start` |
| bring the session back | `office land` |
| build an office | `office init` |
| see every verb, grouped by what you want to do | `office help` |

Every verb is a wizard on a terminal: it asks for what you left out, `?`
explains a question, and every question has a flag, so the same command
can be typed in full and piped input is never asked anything. `office
VERB --help` (or `office help VERB`) explains one verb, with examples.

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

Walking in shows the office's name, the date and time in its timezone
(and that it is on UTC, when the floor plan's zone does not resolve;
`office status` names what fixes that),
whether it is founded and current, the sessions in flight in its projects
and in the office itself with the folder each belongs to, how many
folders are ready, parked and candidates and the first three ready ones,
this week and its gaps, the last notepad lines and the slips, and the
verbs to reach for. It ends with one Next line: the one command to type
now, with its arguments filled in, worked out from the office on every
walk-in and never written down. In the order they win:

| the office | Next |
|---|---|
| is behind the install, or ahead of it | `office upgrade` (or `office status`, which names the versions) |
| has a session out | `office land SID` (when its response is in your downloads, land finds it) |
| is unfounded | `office status` (names the profile sections still to write) |
| has a ready folder | `office start FOLDER` (`--on PROJECT` when its lane names one) |
| has an open folder no session is out for | `office start FOLDER` (or `office close` it when it is done) |
| watches no projects | `office projects add` |
| has five or more slips | `office open triage-the-suggestion-box ...` |
| has only parked folders and candidates | `office desk` |
| has nothing waiting | `office open`, when a job comes in |

### Capture

    office note called the bank; rate locks Friday   # a timed line on today's notepad page
    office slip --about bale pack needs too many flags  # a friction slip, its own page in the suggestion box

Each verb commits only the paths it touched. `office note` and `office
slip` work in an unfounded office and in one that needs an upgrade; they
warn and write. `office note` commits a notepad page only when its
committed bytes are untouched and the new lines are at its end. `office
slip` asks on a terminal what the slip is about (the office, bale,
office-src, or one of the office's projects) unless `--about` says so.

### Start a job, and finish one

    office open                                      # a folder on the desk; asks for what it needs
    office open house-hunt --thread < thread.txt     # ...seeded with the thread that started it
    office desk                                      # in flight, ready in order, parked, candidates
    office week                                      # this week's calendar and its gaps
    office close fix-login                           # to the filing cabinet, done
    office reopen fix-login                          # back to the desk, history and all

A folder is named by the date and a slug, and can be named by any unique
part of that name or by its number, `folder 12`. Folders, their fields,
statuses and gates are below.

### Send a session out

    office start                       # asks: which job, in the office or on a project, the goal

It packs the session with bale where the work lands, records it in the
folder, and puts every file to attach in one out tray, `~/out-tray/SID`,
beside the opener it prints: attach the tray's files to a fresh chat and
paste the opener. The details are below.

### Bring it back

    office land                          # the session out: bale apply, how it ended, the relay

It finds the session the response answers, runs bale apply in the repo it
belongs to, says how it ended, hands you the relay to carry, runs the
project's after-land actions, and records the planner's ratification. The
details are below.

### Build an office

    office init ~/offices/home   # build an office; asks which projects it watches; prints the founding session's pack line

On a terminal, after building, `office init` asks which projects the
office watches: one at a time, through the same questions as `office
projects add` (the path, the name, what rides with it, what runs after it
lands), until a plain return. `--project PATH` (or `--project
NAME=PATH`, repeatable) is the flag twin, each checked before anything is
built, and `--no-projects` skips the question; piped, it asks nothing.
The office is unfounded until its founding session writes the profile;
init prints the line that packs that session.

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
    office upgrade             # run pending migrations: dry run, then one commit
    office where               # the office a command here acts on
    office default [PATH]      # this machine's default office
    office version             # the installed version and where it came from

A command acts on OFFICE_ROOT if set, else the office around the working
directory (found by walking up to floor-plan/manifest.toml), else the
machine's default, kept in ~/.config/office-src/default-office. The
first `office init` on a machine sets it.

### Folders: numbers, fields, statuses and gates

On a terminal, `office open` walks you through what you left out: the
title, the size, the lane and the source, four answers, each skippable
with a plain return but the title. Type `?` at any question to have the
field explained. Every question has a flag, so the same folder opens in
one line, and piped input is never asked anything:

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
each waits for, with that gate's own status; a gate on a blueprint, an
agenda item or a ruling waits until the drafting-table verbs can read
them. Candidates last. A gate that names nothing, or a cycle, prints as
an error line naming the folders; no folder is ever dropped. Walking in
shows In flight and the first three ready folders.

`office status` checks that every folder's status agrees with the last
line of its History that changed it, and walks git's history of every
filed page (the notepad, and the drafting table's ledgers once an office
has one) for a commit that did more than add at the end. It reports and
exits 0; `office init` refuses to build from an install whose catalogs
have a defect.

### Sending a session out: the details

    office start                       # asks: which job, in the office or on a project, the goal
    office start fix-login --on office-src --goal "Fix the login redirect"
    office start plan-wave --in-office --read-only --goal "Plan the next wave"
    office start fix-login --on office-src 2026-10-05-fix-login.bale-bundle   # a planner's bundle
    office start fix-login --on office-src --goal "Fix it" --no-rides         # nothing declared rides this time

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
the page, so the survey every session reads first is current. The forecast of a project session comes from the
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
Where the work lands defaults to the one place whose tree holds every
path the bundle names, and the question's `?` says why; a bundle whose
paths no one place holds, or one sent where its paths are not, is
refused before bale runs, naming each path and where it is.
When the bundle is a file the office can read, a forecast that overlaps
an open session is refused before bale runs, in the office's words and
naming the session, its folder and the overlap, as for a pack; given as a
bare name bale's search finds, the bundle cannot be read first, so the
office says so and leaves that refusal to bale.
When the brief carries a page of the sitting's words between
`--- NOTEPAD PAGE BEGIN notepad/DATE-SLUG.md ---` and
`--- NOTEPAD PAGE END ---`, `office start` files that page in the
notepad and commits it alone; a page already filed with the same words
is left as it is, and a different one at that path is refused loudly and
never overwritten. This works for a brief given with `--brief` too.

On WSL the out tray opens in Explorer and the opener goes on the
clipboard. `~/.config/office-src/machine.toml` changes that per machine:
`out_tray = "~/somewhere"`, `clipboard_command = "..."`,
`open_command = "..."`, and `""` turns a step off.

### Bringing a session back: the details

    office land                          # the session out: bale apply, how it ended, the relay
    office land fix-login                # the session out for a folder
    office land response-2026-10-05-fix-login-001.tar.gz --ratified

`office land` finds the session a response answers (the one the office
has out, asked for when there are several; a session id, a folder or a
response file names one) and runs `bale apply` in the repo it belongs
to, `bale retry` when bale held it. bale reads your terminal, so its own
questions (an admission, the merge, a hook) are asked by bale and only
you answer them; the office passes it nothing that answers one. The
response is found by bale, by name, in its search directories; give a
path when the browser saved it as `response-SID (1).tar.gz`, which a
corrected response after a HOLD usually is. How it ended is read from
bale's records and said in a line. Whatever bale prints for you to carry
(the relay for the planner, and on a HOLD the worker's block first) is
printed whole and, on WSL, put on the clipboard; a clarification's block
for the planner comes from `bale relay` and is printed too.

After an applied landing it runs the project's after-land actions in
its repo, in order (`office projects set NAME --after-land ./install.sh`
declares them), stopping loudly at the first that fails with the lines
that rerun it and the rest. Then it asks whether the planner ratified the
session's judgment calls: yes, yes except TEXT, or not now
(`--ratified`, `--except TEXT`, `--not-now`), and records the answer in
the folder. Its last lines say what became of each action (ran, failed,
not run), or that the project declares none. The actions run only
through `office land`: a session applied by hand with `bale apply` runs
none, so office-src's own `./install.sh` does not run, and `office
status`'s `source:` line then says the install is behind its working
copy, with the line that brings it level.

A read-only sitting the office sent out lands nothing; when it is over,
`office land SID` (or the folder) ends it: `bale unlock` in its repo,
and an `ended` line in the folder's History. The folder stays as it is,
since a planning folder may outlive one sitting; `office close` is
yours. A HOLD, a refusal or a clarification lands nothing: nothing
is ratified, nothing runs after, and the next line is named. An office
session's folder changed after its pack, when `office start` recorded the
session; `office land` puts it back as it was packed while bale lands, so
bale never refuses the response over it, and records the session again
after.

### Which sessions worked on a job

`office start` records the session it packs. When you pack one for a
folder by hand, pipe bale's report into the folder, so the id is never
typed:

    bale pack --json --include desk/2026-09-24-fix-login "Fix the login redirect" | office sessions fix-login -

`office sessions fix-login` lists what is recorded, and under each id
what bale records about the session: its outcome, dates, claims beside
verdicts and exchange rounds. The folder keeps the id and any words you
add with `-m`; it never copies what bale records about the session.

### The projects an office scopes, and what bale records about them

    office projects                          # the projects this office scopes
    office projects add office-src ~/office-src   # add one (asks on a terminal for what it was not given)
    office projects set office-src --ride ~/other-repo/docs --after-land ./install.sh
    office projects --ledger                 # trust ledger per project and work class
    office projects --landed bin/office      # the last applied session that landed a path
    office projects office-src --versions    # the version trail of one project

The floor plan's [projects] table names each project and the path of its
repo on this machine; `office projects add` writes it, and checks the
path is the top of a git repo bale runs in. A project may declare what
rides beside every session on it (`--ride PATH`, repeatable: a directory
inside another repo, a whole repo, or a file) and what runs in its repo
after one of its sessions lands (`--after-land CMD`, repeatable; `office
land` runs them). `office
projects set NAME` asks for both on a terminal, and `office projects`
shows them. They live in the office, never in the project's repo. Walking in shows the sessions
open in those projects and the folder whose Sessions section names each.
Everything here is read from bale's `--json` surfaces in each project and
rendered on every run, never copied into the office; the bale verbs,
flags and keys it reads are listed in share/bale-consumption.toml, with
the bale version they were written against, and `office status` says
when the installed bale is older than that.

### Hung items

`office init` writes a `bale.toml` whose include group pulls the office's
hung items (the profile and the survey, and whatever a renovation hangs)
into any pack whose includes touch the office. Pack lines need no
`--include` list for them. `office status` says when bale.toml no longer
matches the floor plan.

## Layout

| path | what |
|---|---|
| bin/office | the command (bash) |
| lib/office_helper.py | TOML, profile, survey, migration and floor-plan helpers (python3, standard library) |
| lib/office_bale.py | the only code that runs bale, through its --json surfaces: the read side and the renderings built on it (the desk's groups, the walk-in's Next line and the one-writer rule among them), office start's packing, bundles and out tray, and office land's apply and what it reads after |
| doctrine/OFFICE.md | how every office works |
| doctrine/checks/ | checks a session pastes into its validation; rides with the doctrine into every office session. filed-append-only.sh proves a filed page only grew at its end |
| share/spaces.toml | every space an office can have; the base ones are the default floor plan; a space files itself whole or as a list of paths |
| share/profile-shape.toml | the profile's required sections |
| share/bale-consumption.toml | every bale verb, flag and JSON key the office reads or runs, and the bale version they were written against |
| share/verbs.toml | what each verb ships, where it lands, whether a person must be present and what may set it off; a session kind with no declared landing may not run unattended |
| templates/ | profile, folder, clipboard series and sheet, handbook chapter, rolodex card, suggestion slip, notepad page; blueprint and close report; the drafting-table pages (drafting-table-*.md), copied in by the renovation that adds the space |
| migrations/ | one file per breaking release; format in migrations/README.md |
| RELEASES.md | release notes |
| tests/ | the test suite |

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
must be true once the renovation has landed; upgrade prints the
renovation's pack line, the session does the work, and the next run of
`office upgrade` checks the declaration and stamps the office.

## Tests

    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v

The suite builds offices, installs and synthetic migrations under
temporary directories and never touches your home directory or offices.
bale need not be installed: the read side's tests put a fake bale first
on the PATH that replays real bale output captured by a probe, kept in
the development record, and refuses anything it did not capture; office
start's tests use a fake that packs, every line of it built from the
packs a probe captured, and office land's a fake that also applies, holds,
refuses and opens bundles, built from the applies and opens a probe
captured.
