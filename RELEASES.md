# Releases

A release is breaking exactly when it ships a migration (migrations/).
Each breaking release's migration carries the plain-language summary
that office upgrade writes into the office's commit.

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
