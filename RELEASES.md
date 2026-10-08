# Releases

A release is breaking exactly when it ships a migration (migrations/).
Each breaking release's migration carries the plain-language summary
that office upgrade writes into the office's commit.

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
