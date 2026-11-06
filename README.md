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
| ask a quick question, in your own words, answered in a chat with the project's handbook chapter and voice page at hand, no session, and what it learned filed | `office ask` |
| ask a planner something, in your own words, with the context gathered for it | `office start --planner` |
| say a meeting once: when it is and what it is about; its prep is offered when it is near | `office meeting` |
| send a session out for a job on the desk, or a planner's bundle from your downloads | `office start` |
| bring the session back | `office land` |
| close a session you sent out and will never run | `office withdraw` |
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
(with `start new`, the one door for new work, and `start --planner`, a
planner sitting from your words), `ask` (a quick question, no session), `meeting`, `land`, `withdraw`, `desk`, `map`,
`folder`, `tray`, `close`, `deliver`, `projects add`, `tour` and `init`, with what a folder is (one job, what was asked in your words and
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
the next move first, then a response in your downloads for a session
that is out (a file to offer: whether it has arrived is still bale's to
say, and `office land` asks it), a folder whose merge job waits for its
session (`Send the merge session for folder N, ...`, `office start N
--merge`) and each folder whose work landed on a project with an
audience and is not delivered yet, newest landing first (`Deliver folder
N, TITLE (PROJECT): SID landed DAY, not yet delivered`, `office deliver
N`; 0.41.0), a planner's bundle in your downloads that no session has
opened (bale's records say which were; when the downloads hold two
copies of its stem the item says so, the newest offered), each unsorted
drop and the sort, desk moves a sitting decided, an office out of step
with the install, and a read-only sitting, which only you can say is
over (its item says when it is out under an older doctrine than the
install's; when two sittings are open on one folder, the item of each
but the newest ends `; an older sitting on this folder, probably over`,
0.43.0; and once the sitting has filed where it stands, the item says
it, `step N of M: words; waiting on you: words (as of DATE TIME)`, with a
second key that files a new standing from the clipboard, `office
standing N`; since 0.44.0 the key shows from the sitting's first turn,
before any standing is filed), and, while a session is out whose response
is not in your downloads yet, `Open the out tray for folder N, TITLE again
(its files and opener)`, which runs `office tray SID` (0.46.0). Every item
has a key: the first nine `1` to `9`, the rest letters no fixed key takes
(`b`, `c`, `e`, ...), so nothing waits unlisted (0.46.0). Keys for a new
job (`o`), the map (`a`: every project and its folders), sending a session out (`s`),
bringing one back (`l`), a note (`n`), a drop (`d`), the whole desk
(`k`) and help (`h`) are always there, and `q` leaves; `w` withdraws a
session never worked, or a bundle no session opened, while one waits;
`r` runs the probe on the clipboard (`office probe`) while a folder on the
desk records a session open where probes run (0.44.0). After this
office's own sections comes one section per other office this machine
lists (machine.toml's `offices`, 0.44.0), headed `NAME (ROOT):`: the
responses in your downloads for sessions it or its projects have out,
the bundles that land on a project only it scopes, and the sittings out
there, each a key that runs the verb in that office as if typed there
(`OFFICE_ROOT=ROOT office land SID`); it is read through that office's
bale registries and your downloads alone, never its pages. A bundle that
lands on a project no office here scopes is counted in one line instead
of offered. The home screen lists the office it opens in when it is not
listed yet, said once. A
project marked paused (`office projects set NAME --paused`, 0.41.0) has
the line `NAME: paused (office projects set NAME --unpaused)` and is
read for nothing. A key runs the verb's own code with its arguments
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
status` uses; in any office, a `Bytecode: ...` line when the install's
bytecode cache is not level for the python3 that runs it, in status's
words too, with install.sh's line on the Next line (0.31.0); and, for an
office that scopes the install's project, a `Suite: ...` line when the
latest detached run of the project's suite, below, did not end `OK`:
its `FAILED` or `BROKEN` verdict as written, or a `RUNNING` one over an
hour old, with the log to read), the sessions in flight in its projects
and in the office itself with the folder each belongs to (a read-only
sitting out under an older doctrine than the install's says so on its
line, both short hashes named, 0.33.0, and so does a meeting's prep,
0.43.0; a sitting's line says where it stands when its folder has a
standing, and an older one open beside a newer on the same folder says
so, 0.43.0), how many
folders are ready, parked and candidates and the first three ready ones,
how many drops wait unsorted in the in-tray and how old the oldest is,
this week and its gaps, the last notepad lines and the slips, and the
verbs to reach for, and then (0.44.0) one section per other office this
machine lists, each waiting item with the line that runs it there,
`OFFICE_ROOT=ROOT office VERB ...`. It ends with one Next line: the one command to type
now, with its arguments filled in, worked out from the office on every
walk-in and never written down. In the order they win:

| the office | Next |
|---|---|
| is behind the install, or ahead of it | `office upgrade` (or `office status`, which names the versions; or `office land SID` while the renovation upgrade sent out is out) |
| scopes the install's source, which has moved past the install | `(cd SOURCE && ./install.sh)` (start and land run the install, so until it is level they run the old office) |
| has a session out | `office land SID` (when its response is in your downloads, land finds it; bare `office land` with several out lands the one whose response is there, 0.44.0) |
| has desk moves a sitting decided, or sorted drops waiting in the in-tray, not yet run | `office moves` (until they run, the desk is not in the order the sitting decided) |
| has a folder whose merge job waits for its session (0.41.0) | `office start N --merge` (start --merge sends the session that resolves it) |
| has a folder whose work landed on a project with an audience and is not delivered (0.41.0) | `office deliver N` for the newest landing (deliver carries it to the audience; the others are counted) |
| has an unsorted drop in the in-tray | `office start --drop in-tray/PAGE` for the oldest whose project is one of the office's and has no session in flight on its lane; for the oldest whose project is none of them, the same with `--lane LANE` to fill (an office with no projects skips this) |
| has an unsorted drop whose project is none of the office's and a session has gone out since it was dropped, or three or more unsorted drops and nothing ready | `office start --sort`, the standalone sort |
| is unfounded | `office start FOLDER` for its founding folder (it goes out with the answers the folder keeps), or `office found` when no founding folder is on the desk |
| has a ready folder | `office start FOLDER` (`--on PROJECT` when its lane names one) |
| has an open folder no session is out for, and no landed work waiting to be delivered | `office start FOLDER` (or `office close` it when it is done) |
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
drop it can write. A text that is one office command line (one
non-blank line beginning `office `) is usually the clipboard holding the
command you just copied instead of the message: from the clipboard the
drop asks once, before writing anything, whether to drop it anyway (no by
default, `--anyway` the twin, and a yes writes it); from a file or stdin
it is dropped as given, and the line saying what it took says so. The
in-tray arrives with the first drop. From then on every session `office
start` sends out carries the unsorted drops, and a session that can
judge one sorts it in its notes.md (doctrine section 4); `office start
--drop in-tray/PAGE` sends one straight out on its own, and `office
start --sort` sends the drops nothing carried to a session of their own.
Drop, start, land: a routine ask needs no planner. When a session's Sort
lands, `office land` files it on the drop's page, and a drop sorted into
a folder (a new one, or folder N) moves there with its brief: the next
`office start N` asks nothing the folder already knows.

### Meetings: a view over the work

    office meeting weekly review every Monday at 9 about alpha and beta   # said once; a series is never asked again
    office meeting --words "alpha review" --when "2026-10-30 14:00"     # ...what the words do not say, as a flag
    office start --prep                              # the prep of the meeting near now (the home screen's key)
    office land 2026-10-25-weekly-review-prep-001    # after the meeting: held, and what arose filed as drops

A meeting is not a job, and it gets no folder (0.26.0). `office meeting`
(the home screen's `m` key) takes it in one sentence of yours and writes
one line in the calendar's plan: when it happens (a date, a day, today or
tomorrow, every Monday, weekdays, a time), its title (your words, less
when) and what it concerns (the projects your words name). It asks only
when your words do not say when, or name none of the office's projects;
`--when`, `--about PROJECT` and `--in-office` are the twins, and piped it
asks nothing. The calendar arrives with the first meeting, and `office
week` shows this week's.

From a day before a meeting until four hours after it starts, the home
screen offers its prep by key (`office start --prep`): a read-only
sitting, its goal the meeting's words, that briefs you from what landed
on its projects since the last meeting on them (the 14 days before it,
for a first one), with each project's handbook chapter, its folders on
the desk, the unsorted drops and the drops that arose last time with the
folders they became; the screen and its brief list what rode and why.
Ask it anything before the meeting and during it; nothing else is opened.
It writes what arises in one block and offers it as a file,
`arising-SID.md`. After the meeting, `office land` ends the sitting,
finds that file in your downloads (or reads the block from the clipboard
once you copy it, or `--arising FILE`), records the meeting held and
files each item as a drop in the in-tray, tied to the meeting, saying in
one line what it filed. A drop you make yourself during the meeting is
tied to it too, and the next meeting on those projects sees them all, and
their folders, in its prep. The prep may also offer a cleanup of the
projects' documentation, as a planner's bundle you send or delete.

### Start a job, and finish one

    office start new                                 # a new job in your words: its folder, and its session out
    office start new --words "Fix the login on narrow screens" --on alpha   # ...typed in full
    office open                                      # (plumbing) a folder on the desk, and no session yet
    office open house-hunt --thread < thread.txt     # ...seeded with the thread that started it
    office open fix-login --goal "Fix the login redirect"   # ...with the goal office start offers
    office desk                                      # in flight, ready in order, parked, candidates
    office map                                       # two tables: every project, then its folders with their state
    office map --all                                 # ...every closed folder too, none folded
    office map 12                                    # one folder's whole record, and the lines that change it
    office folder 12 --lane alpha --size medium      # change a folder's fields (alone: they and their lines)
    office week                                      # this week's calendar and its gaps
    office close fix-login                           # to the filing cabinet, done
    office reopen fix-login                          # back to the desk, history and all

New work comes in through one door: `office start new` (the home
screen's `o` key) asks for the job in your own words, as many lines as
you like (a blank line ends them), and sends its session out in the same
motion. Before anything is written your words are shown back, numbered,
and asked about once: keep them (a plain return), redo them, more lines,
or a line's number to type that line again, since a line already ended
cannot be edited at the prompt. With `VISUAL` or `EDITOR` set, you write
them in that editor instead, as for a git commit message, and nothing is
shown back (0.33.0); `editor = ""` in machine.toml keeps them at the
prompt, and `editor = "CMD"` names the editor over both (0.48.0). The first line is the folder's title and its slug comes from it;
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

`office map` (0.46.0, the `a` key) is folders and projects on one page,
as two tables since 0.49.0, columns aligned under a header row. First the
projects, one row each: its name, where it is (here or on its host), its
audience (or none), whether it is paused, and what rides with it and what
runs after it lands in one cell (`rides: a, b; after: x; y`), a
declaration problem said there too. Then the folders, one row each:
`folder N`, its project (`the office` for the office's own, `no lane yet`
for one whose lane is still to be asked), its title, its size and its
state in a few words (`in flight 3 days`, `sitting out 2 days, step 8 of
14`, `landed, not delivered`, `merge job waiting`, `delivered BRANCH`,
`review #N STATE`, `open`, `ready`, `parked`, `done`). Rows are grouped by
project in the floor plan's order, the office's own last; open folders
come before closed ones, each newest number first, and of a project's
closed folders the newest three show while the rest fold into one line,
`and N more closed: office map --all`; `office map --all` shows every row.
On a terminal the page is cut to the terminal's width, the title column
giving way first, cut with `...`; piped, every cell is whole. A title is
shown as you wrote it, curly quotes and accents and all, though folder.md
keeps it in ASCII. `office map alpha` is that project's rows in both
tables, nothing folded; `office map 12` one folder's whole record, with
the session's id and the riders the tables leave out: its fields, its sessions as
`office sessions` shows them, its riders, deliveries, reviews and
standing, the lines that act on it next, and the lines that change its
fields. The map writes nothing. Every list of folders offered by key
names the project the same way (0.49.0), `folder N, TITLE (PROJECT)`,
`(the office)` for the office's own: start's jobs on the desk, `Folders in
desk/`, the planner's folder and probe's folders with a session open; and
`office desk`'s line says it after the folder's name, `folder N  NAME
(PROJECT)  next: ...`. Your words show as you wrote them on every screen
(the map, the pickers, the desk, the home screen, the walk-in, status,
the bundle offer), while the pages keep their ASCII escapes. `office folder 12` changes those fields:
`--lane PROJECT` (or `--in-office`, the work is the office's own),
`--title`, `--size`, `--goal`, `--source`, `--class`; each replaces its
line, takes the field off the provisional line, and adds a `re-scoped`
History line, and the folder is committed alone. Alone it prints the
fields and the line that changes each. When `office start`, `office
deliver` or `office probe` has to ask which project a folder's work is on,
your answer becomes its lane that way and is said, so it is asked once.
`office deliver` offers only the projects with an audience, each with its
audience named (0.47.0), and with none it says so and names `office
projects set NAME --audience REMOTE`.

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

### Ask a quick question

Some questions want an answer in five minutes, not a session: no pack,
no tarball, no land. `office ask` (the home screen's `i` key) takes the
question in your words, as `office start new` takes a job's, and asks
which project it is on, by key, only when your words name none of the
office's projects (`--words`, `--project NAME` and `--in-office` are the
twins). It writes one out tray, `~/out-tray/ask-DATE-SLUG`: a brief with
your words verbatim, the project, the rule that office context never
lands in a project, the voice page's words when the project has an
audience, and what the chat leaves at the end; beside it the project's
handbook chapter, the letterhead's voice page and forbidden list, the
profile and the doctrine. No project tree rides: attach what else the
chat needs. On a terminal the tray opens and the opener goes on the
clipboard, as a session's do. Attach the tray's files to a fresh chat and
paste the opener. No bale verb runs, and the ask's name is the office's.

The chat ends with a LEARNED block: the answer, facts for the handbook,
questions and answers (the brief shows its shape). Copy it and run
`office ask --learned` (or `office ask --learned FILE`, or `-` for stdin;
bare `office ask` with the block on the clipboard files it too, and the
home screen has a key for each ask out). The office writes the ask as a
notepad page, `notepad/DATE-ask-SLUG.md` (your words, then the answer),
files each fact at the end of its project's chapter as `- DATE: fact
(ask-DATE-SLUG)`, adds the questions and answers to the same page, each
commit on its own, and removes the tray. A block that does not read, or
that names no ask out, is refused by name, and nothing is written. Until
then the walk-in, the home screen and `office status` show the ask as
out; `office tray ask-DATE-SLUG` opens its tray again, and `office ask
--learned none ASK` ends it with the page alone.

### Send a session out

    office start new                   # a new job, in your words, out in one motion
    office start                       # your downloads' new bundles by key, then which job by key
    office start --drop in-tray/2026-10-14-login-error.md   # a dropped message, straight out
    office start --sort                # the drops nothing carried, to a session of their own
    office start 14 --merge            # the merge session office deliver 14 wrote, when bringing the audience in conflicts
    office start --planner             # a planner sitting from your words, what rides gathered for it
    office tray                        # the newest session's out tray opened again, and its opener

On a terminal, bare `office start` first offers the planner's bundles in
your downloads that no session has opened, newest first, one key each (a
plain return goes on): the newest nine, and one line for the rest, `and
N more, oldest first: office start --bundle STEM starts one by name,
office withdraw --bundle STEM takes one out of the offer` (0.46.0). A
bundle a paused project's session opened is read as opened too, and
leaves the offer. Then it asks which job, by key, or a new one in your
words. Where the work lands is the folder's lane (asked by key only when
the lane names no project, and your answer is then kept as the lane, so it
is asked once; a lane `the office` sends it to the office), the goal is the folder's own or your words,
what the session will change is the session's to forecast, and what
rides with a project rides as declared; each is said, not asked. It
packs the session with bale where the work lands, records it in the
folder, and puts every file to attach in one out tray, `~/out-tray/SID`,
beside the opener it prints: attach the tray's files to a fresh chat and
paste the opener. Its screen (0.46.0) is cut to what you need to read:
one `[office]` line per thing settled from an artifact or a record (the
`from the ...` lines), the copy of the opener, the tray opened, and last,
before the opener, `next: attach every file in the out tray (PATH) to a
fresh chat, then paste the opener below (office tray SID opens the tray
and prints the opener again)`; the rest is said under `OFFICE_DEBUG=1`,
and piped every line is said as before. Start keeps the opener it prints
beside the tray, `~/out-tray/SID.opener.txt` (outside the tray, so every
file in the tray is still one to attach): `office tray`, `office tray N`
or `office tray SID` opens the tray again as start does, lists its files
and prints the opener again, so a closed window or a lost clipboard costs
one line; it writes nothing. When the brief carries the planner's ratification of
earlier sessions (`--- RATIFIED SID ---` lines), start files each in the
folder that records that session, wherever it is, and says so. On WSL
the opener goes on the clipboard as start's last copy, read back to
check: the office says it is there only when it is. The details are
below.

A planner sitting from your words (0.24.0): `office start --planner`, or
the home screen's `p` key. Say what you want a planner for; that is the
sitting's goal, and nothing else is asked but what it concerns, only when
your words name none of the office's projects and the answer changes what
rides. The office gathers what rides (each concerned project's handbook
chapter, its folders on the desk, the walkthrough of each job that landed
on it since the last sitting, and the last sitting's notepad pages),
lists it with why on the screen, and writes the same list first in the
sitting's brief. Your words are shown back to keep, redo or mend before
anything goes, as a new job's are. The brief's opening names the doctrine
the sitting goes out under (the sha256 of the install's
doctrine/OFFICE.md), and the folder's Sessions line keeps its first
twelve characters, `- SID: sitting, doctrine SHORT`; when office-src
moves on while the sitting is out, the walk-in, the home screen's item
for the sitting and `office status` say it is out under an older
doctrine, both short hashes named, and nothing refuses (0.33.0). When drops wait in the in-tray, before any sitting goes
out the office says how many and offers the sort first, by key: taken,
the sort and then the sitting go out together, the sitting's opener left
on the clipboard. A planner's bundle whose brief carries a LANDS line
(`--- LANDS alpha, folder 14 ---`) goes out without asking where it lands
or which job; one whose brief names the branch its session builds on
(`--- BRANCH picklists ---`, 0.34.0: a review's answer goes onto the
review's own branch) has that branch checked out in the project's clone,
here or through its shell on a host, before `bale open --check` runs. Its
local branch, or a new one tracking the one remote that has it; a clone
with uncommitted changes, with a session open in it, or with no such
branch locally or on a remote it has fetched stops the start with nothing
written and says what to do there (the office fetches nothing), and a
clone already on the branch is said. A local branch behind its
remote-tracking ref (0.50.0: the refresh moves that ref, never the local
branch) is fast-forwarded to it when the clone is clean and the local tip
is an ancestor of the remote one, the line naming both tips; one that has
diverged is checked out as it is, and said so. `office start --branch
NAME` (0.50.0) does the same for any project session (`--on`, `new`,
`--drop`), with the same refusals, and stands over a BRANCH line naming
another branch, said in one line. One whose brief names the sitting it
succeeds (`--- ENDS SID ---`, 0.43.0) has start end that sitting, once
bale has opened the new session and the opener is on the clipboard, as
`office land` ends one: asked once on a terminal, default yes
(`--end-predecessor` and `--keep-predecessor` are the twins); piped with
neither it is said, with the land line, and nothing is ended.

What an artifact or a record answers is not asked (0.44.0). Each answer
taken is said in one line, `from the brief: ...`, `from the folder:
...`, `from the downloads: ...`, with the flag that says otherwise, piped
as on a terminal: piped, `office start FOLDER --goal TEXT` takes where the
work lands from the folder's lane as a terminal does, and only a question
nothing answers refuses, naming its flag. Bare `office start` on a
terminal with one bundle waiting takes it (`from the downloads: one bundle
waits, STEM; starting it`); with several it offers them by key. A brief
may name the riders its session carries, `--- RIDES PATH ---` per ride or
`--- RIDES none ---`: start carries exactly those, piped or not, and says
so; `--carry` and `--carry none` still win. A LANDS line naming a project
another office on this machine scopes is no refusal: start names that
office with the line that starts the bundle there,
`OFFICE_ROOT=ROOT office start --bundle PATH`, or says no office here
scopes it, and starts nothing. Deliver's question and the review's are
never answered from an artifact.

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
clipboard, read back to check. A folder on a project with an audience is
not closed at land (0.41.0): it stays on the desk until `office deliver
N` carries its work, which closes it (`--close` closes it at land all the
same), and land's last line is `Next: office deliver N`, the folder's
number filled in. The block for the planner carries the office's own
lines after bale's END marker, bale's block untouched between its
markers: `--- OFFICE land SID ---`, the folder's number, title, place and
state (`folder: N, TITLE (desk/NAME, open; closes at delivery)`), the
deliver line, the letterhead's review of the landing for a project with
an audience, and `--- OFFICE END ---`, so the planner never asks for
them; with a `reviews:` line for each review gh reads on the folder's
branches (0.43.0). Piped, nothing is copied, so land prints that block
whole with the office's lines after bale's, under `The block for the
planner, whole, with the office's lines:` (0.43.0). Every line land hands
you is an office line (0.44.0): after bale's own output, which stays as
bale's record, `In office words:` lists each bale verb bale's lines named
with the office line that does it (`bale retry -> office land SID
--response FILE`, `bale relay -> office relay SID FILE`, `bale unlock ->
office withdraw SID`), or `no office line: type it in REPO` for revert and
amend-checkpoint. A clarification ends `Next: office relay SID
ANSWER-FILE, ...`, and its block for the planner carries the office's
tail with `answer: office relay SID ANSWER-FILE`. A bailout's line says
there is no office line for the handoff yet and names bale's, and where.
Bare `office land` with several sessions out lands the one whose response
is in your downloads (`from the downloads: response-SID.tar.gz is here, so
SID lands`); with responses for several, it offers those first. It asks nothing about
ratification: the
planner ratifies in the next brief it writes, and `office start` files
it. `office relay` carries a planner's answer to a clarification back
to the session's repo, through the project's shell for a hosted one. The
details are below.

    office withdraw                      # a session you sent out and will never run, closed

`office withdraw` (the home screen's `w` key) closes a session that went
out and was never worked: no response in your downloads, no apply begun.
It names the session by its folder, asks once, runs bale's unlock with
bale's reason `abandoned` where the session is open, and writes a line in
the folder's History; a folder opened for that session alone is said with
the line that closes it.

    office withdraw --bundle 2026-10-27-picklists-review   # a planner's bundle you will not send, out of the offer

`office withdraw --bundle STEM` (0.41.0) takes a planner's bundle out of
the home screen's and `office start`'s offer: every copy of the stem in
your downloads, a browser's `(1)` copies too, is renamed
`NAME.bale-bundle.declined` (rename it back to offer it again). The
office deletes nothing in your downloads. It asks once, default yes
(`--yes`); a bundle a session opened is not in the offer and is refused.
Bare `office withdraw` offers the sessions never worked and, after them,
the bundles no session opened, by key.

### Run a worker's probe

    office probe 13                      # the block on the clipboard: run where folder 13's project lives
    office probe                         # the one folder whose session is open: no number to look up

When a worker returns a probe block (a fact it needs from your machine,
or from the host and container a project lives in), `office probe` runs
it there for you: in the project's repo, through its shell on a host, or
in the office root. It shows the block's purpose header and asks once
first, and refuses a block that is not a probe or does not say it is
read-only. The output comes back to your terminal whole, the block goes
on your clipboard to paste back, and the folder's History counts the
probe. A credential written into a URL and a GitHub token are masked in
both, as `xxx`, and the office says how many it masked (0.38.0). A
planner sitting's probe of a project's repo works the same way:
`office probe 21 --project office-src` runs it in that repo, under the
sitting's id (0.33.0). A block that spans the office and a project's host
calls `office-on PROJECT COMMAND` on its own lines (0.34.0): it runs in
the office root with that helper on its PATH, and each call runs its
command where the project lives. A reach is a call, never the helper's
name in a string, a comment, a heredoc or an echo's text, and the call's
words arrive there as given, so `office-on PROJECT bash -c SCRIPT` runs
SCRIPT whole (0.45.0). With no folder named (0.41.0), when
exactly one folder on the desk records a session open where probes run
(a read-only sitting, or a session in the office or on a project), the
probe is that folder's, and it says so; with several, those folders
alone are offered by key, sittings first. The block's stderr is masked
on the screen too (0.43.0). When the text you copy carries the sitting's
standing block after the probe block (0.43.0), probe files it on the
folder first and says so in one line, so one paste does both.

    office probe                         # 0.44.0: the block's own run line says the folder, project and session

A sitting writes one more comment line in the block's purpose header
(0.44.0), `# office: probe FOLDER [--project NAME] [--sid SID]`: with no
folder named, `office probe` reads the block first and takes all three
from it, said (`from the block: probe 21 --project office-src --sid
SID`), so copying the block once and typing `office probe` (or the home
screen's `r`) runs it. A flag you type wins over the line, said; a part of
the line the office cannot use (a folder not on the desk, a project it does
not scope, a session not open) is said and read as without it. A text
holding a standing and no probe block is filed as `office standing` files
it, and nothing runs (`the clipboard holds a standing and no probe: filed
on desk/NAME; nothing to run`).

### Where a sitting stands

    office standing 21                   # the sitting's last standing block, from the clipboard

A planner sitting prints its standing at the end of any turn where its
plan or its place in it changed: one block, `--- STANDING BEGIN SID
---`, `step N of M: words`, one `- [x]`, `- [>]` or `- [ ]` line per
step, `waiting on you: words`, `--- STANDING END ---` (the doctrine,
section 4 continued, pins it to the byte). `office standing FOLDER`
(0.43.0) files it on the sitting's folder as `standing.md`, replaced
whole each time and committed on its own, from the clipboard on a
terminal, a file, or stdin (`-`); `office probe` files one that rides with
a probe block, and the home screen's key runs it. A block that does not
read, or that is not a session the folder records, is refused by name and
the page is left as it was. Then the home screen, the walk-in's In flight
line and `office desk`, under the folder's next move, show the step you
are on and what waits on you. The page stays when the sitting ends, as
the record of where it ended; a successor's filing replaces it.

### Deliver it to the audience

    office deliver health-route          # the folder's landed work to its project's audience, as curated commits
    office letterhead check              # what the letterhead refuses, in the tree here

A project's workbench clone is where bale lands, and nobody reviews it.
`office deliver` carries a folder's landed work to the audience's git
host as a branch of curated commits in your words, the folder's
`delivery.md`, made from the audience's base, holding none of bale's
commits, merges, tags, branches or files, and nothing a commit of bale's
own changed (0.36.0: what `bale: ignore .bale/` put in `.gitignore` stays
on the workbench); it shows what leaves and asks once. It reads the lines
the delivery adds, never a file whole, so a refused character a file
already held is told and not refused, and the question says which rule
chose the branch (0.38.0). A branch another folder of the office
delivered to is continued with no question; a branch the audience
already has that no folder delivered to, a pull request opened by hand,
is adopted when you say so (`--adopt`, or yes on a terminal; 0.34.0), so
a review's answer lands on the review's own branch. When a clone on a
host has a stale view of the audience, deliver says by how much and
offers `office projects refresh` first; and when the workbench is behind
the audience's base and the merge is clean, it brings the base into the
workbench itself, as one merge commit, before the squash (0.39.0). No
delivery ends at a terminal (0.40.0): when that merge conflicts, deliver
writes the merge's materials into the folder and its last line is
`office start N --merge`, the merge session, whose resolution `office
land` makes a merge commit; a review the audience merged as a squash is
seen by its content; and a second delivery onto a branch carries what is
new since the first. A folder closes at delivery (0.41.0): once every
applied session it records is delivered (by it or another folder) or
held by the base, deliver closes it, done, on a terminal (`--leave-open`
keeps it; piped, `--close` closes it), and a session still to deliver is
named. Bare `office deliver` offers the folders whose work landed and is
not delivered first, by key, newest landing first; a plain return lists
every folder. `office letterhead check` is the guard it runs
first, on its own for any tree. The details are below.

### Build an office

    office init ~/offices/home   # build an office; asks which projects it watches and the profile's questions; sends the founding session out
    office found                 # an unfounded office: the profile's questions, then the founding session out

On a terminal, after building, `office init` asks which projects the
office watches: one at a time, through the same questions as `office
projects add` (the path, the name, what rides with it, what runs after it
lands), until a plain return. `--project PATH` (or `--project
NAME=PATH`, repeatable) is the flag twin, each checked before anything is
built, and `--no-projects` skips the question; piped, it asks nothing.
The office is listed in this machine's machine.toml `offices` (0.44.0),
the default or not, so every office here shows what waits for it. The
office is unfounded until its founding session writes the profile,
and init sends that session out itself. It asks the profile's questions,
one per section of the profile's required shape (`share/profile-shape.toml`)
in its order, each worded from the section's asks line. An answer may run
to several lines: each line is kept as typed, and a blank line ends it;
then it is shown back, numbered, to keep, redo or mend line by line (or,
with `VISUAL` or `EDITOR` set, written in that editor).
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

Since 0.30.0 it also compiles lib/ into bytecode beside its sources
(lib/__pycache__), with the python3 on your PATH, so a helper call reads
its module's compiled code instead of compiling it. Every office command
runs its helpers with `-B` and never writes the install, so before
0.30.0 each call compiled the module it loaded from source, about half
of what the call cost. `office status` says in one line whether the
cache is level with the sources for the python3 it runs; after a Python
upgrade, or a source changed inside the install, it names what compiles
from source and the line that brings the cache level (install.sh again).
A compile that fails is said, and the install goes on without the cache.

On another machine, clone and run the same line:

    git clone <remote> ~/office-src && ~/office-src/install.sh

Requirements: bash, coreutils, git, python3 (3.11 or later, for tomllib),
all shipped with Ubuntu 24.04. No network, nothing to install. The read
side (below) runs bale when it is on the PATH; without it, every
rendering says bale is missing and the rest of the command works.

`office version` prints the installed version and where it came from.

## Reference

### Looking after an office

    office status              # version, skew, the install against its source, its bytecode cache, the doctrine and any sitting out under an older one, profile, survey age, timezone, hung items, catalogs, folders, filed pages, bale, projects, the letterhead, the push guards
    office survey              # rewrite floor-plan/survey.md, report what changed
    office upgrade             # run pending migrations: dry run, then one commit; a renovation goes out through office start; with or without one, the letterhead's missing pages and the current push guards
    office found               # an unfounded office's founding session, through the founding door
    office where               # the office a command here acts on
    office default [PATH]      # this machine's default office
    office version             # the installed version and where it came from
    office map                 # two tables: the projects, then their folders and each one's state (--all: none folded)
    office projects set alpha --path ~/work/alpha-2   # point a project at another clone (the old one left as it is)

A command acts on OFFICE_ROOT if set, else the office around the working
directory (found by walking up to floor-plan/manifest.toml), else the
machine's default, kept in ~/.config/office-src/default-office. The
first `office init` on a machine sets it.

Two offices may share one machine and one downloads directory (0.44.0).
`offices` in ~/.config/office-src/machine.toml lists them, the one place
the list lives: `office init` adds the office it builds, `office default
PATH` adds PATH, and an office's home screen adds it the first time it
opens there unlisted, said once. A listed root that is no longer an
office is said and skipped, never removed; edit the file to take it out.
`office survey`'s Machine section names the offices listed, and each
office's home screen and walk-in show what waits for the others.

### Folders: numbers, fields, statuses and gates

A folder's fields are written by the office command alone: `office open`
writes them once, `office land` files a session's Structure over the
provisional ones, and since 0.46.0 `office folder N` is the one writer of
them after that, on the desk or in the filing cabinet: `--lane PROJECT`
(a project the office scopes) or `--in-office` (the lane reads `the
office`: the work is the office's own, and start, deliver and probe stop
asking where), `--title`, `--size` (small, medium or high), `--goal`,
`--source` and `--class` each replace their line (or write it where the
field block puts it), take the field off the provisional line, and add one
History line per field, `- DATE re-scoped: FIELD from OLD to NEW (office
folder)`; the folder is committed alone. An open session in the office
whose forecast holds the folder keeps the write out (the one-writer
rule), and a session out on another project than a new lane names is
said, never refused. The status is never one of them. `office folder N`
alone prints the fields and the line that changes each, and `office map
N` ends with the same lines.

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
provisional line that does not read, and (0.31.0), in a `structure:` line
each, a folder still provisional though every session it records landed
applied (by bale's applied/ tags), whose Structure never came back. Filed
twice (`office land`, then `office sessions --pages` with the same
response), a session's Questions and answers and its facts are filed
once: a line already there is said and left. `office start new` runs this same
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
the in-tray (each unsorted drop by its page's file name, with the project
it names, or none; 0.24.0), the agenda and the open blueprints. The last sitting is the latest
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
    office start fix-login --on api --goal "Answer it" --branch review-fixes  # check the branch out first (0.50.0)
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
its declarations. What rides is declared once, for good, and which of it
a session needs is not asked (0.22.0): on a terminal start says what the
project declares to ride, in one line, and it all rides;
`--leave-out PATH` keeps one home for this session only and `--no-rides`
keeps them all home (piped, everything declared rides). A ride is a path
here (`--ride PATH`) or, for a project on a host, a path there (`--ride
host:PATH`, 0.50.0): that one is checked in the round start makes on the
host, packed there by the host's bale and carried back into the tray
(`rides with PROJECT (host:PATH, packed on HOST)`), and `--leave-out
host:PATH` names it as declared. Before the pack, start's screen names the
branch the session builds on (`PROJECT's clone at WHERE is on BRANCH`,
or a detached HEAD; 0.50.0), and `--branch NAME` checks NAME out in the
clone first, as a bundle's BRANCH line is checked out (above). The
doctrine rides once: a project whose own tree
carries the same `doctrine/` (office-src's) ships it there, and one
whose `doctrine/` differs gets the install's beside it, named as the
install's. Before it packs, start surveys the machine again and commits
the page, so the survey every session reads first is current. Before it
packs a sitting (`--read-only` in the office, or a bundle that forecasts
nothing), it writes the digest again and commits it, and the drafting
table rides inside the sitting's request; an open session holding the
drafting table leaves the digest as it was and never stops the start. A
bundle named by its stem is read where start found it (here or in the
downloads), so a sitting sent out that way gets its digest too (since
0.21.0); when start cannot read a bundle's pack line at all, it
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
(`.bale-bundle` files). Give one to `office start` by its stem, the name
before `.bale-bundle` (`--bundle STEM`; the extension may be given too, and
a word ending `.bale-bundle` needs no flag), or by its path. Since 0.49.0
start works the name out before it asks or writes anything: a path is
taken as it is; else STEM and STEM.bale-bundle are tried here, then in
your downloads (the `downloads` setting below; of several browser copies
the newest is taken and named); a name found nowhere is refused, exit 1,
`no STEM.bale-bundle in your downloads (DIRS) or here; save it there
first, or office withdraw --bundle STEM takes it out of the offer`, and
nothing is asked. Then it asks which job and where the work lands, as for
a pack, and hands the bundle's path to `bale open` there. The bundle's pack line is the
whole session, its goal, forecast and brief; the office adds nothing to
it and says when it leaves out something the office would have carried.
Before it writes anything (a folder for `new`, the survey, the tray),
start asks bale whether it can open the bundle there, with `bale open
--check`, which runs every gate bale runs before an open, and writes
nothing: a bundle bale refuses, a forecast path that is not there, or a
forecast another open session holds stops the start in bale's words, with
nothing written. For
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
a file here, as every bundle is since 0.49.0, its path or its stem found
here or in this machine's downloads (of several browser copies of the
name, `NAME (1).bale-bundle` and so on, the newest is taken and named). Where a
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
suite's count). A ride declared on the host (`host:PATH`, 0.50.0) is
checked in that round too, and the clone's branch is read there for the
screen's branch line; what rides from the host is packed in one more
connection, every pack in it, and each tarball fetched as the request is
(a scratch copy there removed in the connection that fetches it), so the
in-tray's drops, the doctrine and the office's context stay made here.

The clone's view of the audience (0.39.0). For a project with an
audience, start compares the clone's `AUDIENCE/BASE` (origin/main, say)
with the base as this machine sees it, once, before anything is packed
and before the checkout a brief's BRANCH line asks for, so a branch it
names is checked out at its current tip: `git ls-remote` here, and only
when the two differ, the base fetched into a temporary repo here to
count (one more connection for a hosted clone, to read its view). Behind,
one line says by how much (`the clone's view of origin/main is 14
commits behind the audience's`), and on a terminal start asks once
whether to refresh it first (`office projects refresh NAME`; default
yes; `--refresh` and `--no-refresh` are the twins); piped with neither,
it says so and packs on the clone's view as it is. Ahead or level,
nothing is said; a compare that cannot be made is a warning, never a
refusal.

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
and drafting-table/moves.md (made from its template first when it is not
there, and in an office with no drafting table the table arrives with it,
committed alone: 0.31.0), on which the session
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
- `editor = ""` or `editor = "CMD"` (0.48.0): where an answer of several
  lines is written (a new job's words, a question for `office ask`, the
  profile's answers). `""` keeps every answer at the prompt, however
  `VISUAL` or `EDITOR` is set; a command names the editor over both. With
  no `editor`, `VISUAL` then `EDITOR` decide, as git reads them.
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
    office land SID --accept-checkpoint-change    # after bale amend-checkpoint: the same response, retried
    office land SID --accept-base-drift src/a.py  # land its bytes over a file that moved since the pack

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

Two things bale refuses without asking (0.37.0): a blind checkpoint that
changed between the pack and the landing (`bale amend-checkpoint`
committed a planner's amendment, say), and a file the response changes
whose base moved since the pack. bale accepts each on one invocation
only, deliberately with no setting, and so does the office:
`--accept-checkpoint-change` and `--accept-base-drift PATH` (once per
path) are passed to that landing's `bale apply` or `bale retry`, before
the tarball, exactly as you typed them (through the project's shell for a
project on a host), each said in its own line before bale runs. land
never adds one on its own, and nothing turns one on for you. When bale
refuses a moved base, land's Next line is the office line that accepts
it, `office land SID --accept-base-drift PATH` with the paths bale
names, and any accept you typed this time said again, since bale carries
none forward. A changed checkpoint bale refuses before it stages
anything, on its error stream, with no attempt recorded, so the office
cannot tell it from another refusal: a retry refused that way names
`office land SID --accept-checkpoint-change` as its Next line, for when
bale's words above it say the checkpoint changed. The
admissions bale asks for itself (a path outside the forecast, a missing
required check) stay bale's questions on your terminal. The rest of the
landing is as it would be: what is filed, what runs after and how it
ends do not change with an accept.

A merge session (`office start N --merge`, 0.40.0) is made real first:
when the folder's merge job names the session that landed, land makes its
resolution a merge commit in the workbench before anything else reads it
(the details are under Delivering to the audience), says it, records a
`merged` line in the folder's History and takes the job's materials out
of the folder; a merge it cannot make is said with the line that makes it
later, `office deliver N`. A merge session's notes carry no Walkthrough or
Delivery, and the folder's two pages are left as the work's.

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
end of the project's chapter, with a Sort's `facts:` lines, each made
bare first (a leading date and a trailing session id the session wrote
are dropped and said, since land adds both; 0.38.0) and read whole when
it wraps onto indented lines as a list item does (0.38.0; before, only
its first line was filed), and a `####
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
line, and the block is printed again, whole. Since 0.41.0 each block for
the planner after an applied landing carries the office's tail after
bale's END marker, in the copy and in that whole printing (bale's block
stays byte for byte between its markers; a held landing's block and the
worker's get none, and since 0.44.0 a clarification's gets the folder line
and `answer: office relay SID ANSWER-FILE`, the office line the planner's
answer comes back by, and nothing else):

    --- OFFICE land SID ---
    folder: N, TITLE (desk/NAME, open; closes at delivery)
    next: office deliver N
    reviews: #12 approved (fix-login)
    letterhead: SID's landing is clean for delivery: ...
    --- OFFICE END ---

The `folder:` line's parenthesis is `desk/NAME, open; closes at
delivery` on a project with an audience, `desk/NAME, open` when land left
it open for another reason, `filing-cabinet/NAME, closed, done` when land
closed it, and the line is `folder: none` when no folder records the
session. `next:` is there only when land printed deliver's Next line;
`reviews:` (0.43.0), one line a review, only for a project with an
audience when gh reads a review on a branch the folder delivered to (none
when there is none or gh is not there; the read is the walk-in's, one `gh
pr list`, never a prompt); the letterhead's lines only for a project with
an audience, exactly as land
printed them after the landing; an office session's tail is the folder
line alone between the markers. Off a terminal (a landing run from a
script or a session, 0.43.0), nothing is copied, so after bale's own
printing land prints each block for the planner whole with its tail,
under one line, `The block for the planner, whole, with the office's
lines:`; on a terminal nothing changes.

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
piped with neither, the folder stays open and land says so). On a project
with an audience (0.41.0) land leaves it open instead, saying `NAME
recorded SID alone, and it landed applied; PROJECT has an audience, so
the folder stays on the desk until office deliver N carries the work
(office close NAME closes it now)`; `--close` still closes it, and says
so, and `office deliver` closes it once its work is delivered. Then land's
last line, after the relay's clipboard line, is `Next: office deliver N
(...)`, or, for a merge session's landing, the same line saying deliver
makes the merge commit and carries the folder's own work. The actions run only
through `office land`: a session applied by hand with `bale apply` runs
none, so office-src's own `./install.sh` does not run, and `office
status`'s `source:` line then says the install is behind its working
copy, with the line that brings it level; when the office scopes that
working copy, the walk-in says it too, and its Next line is that line.

A read-only sitting the office sent out lands nothing; when it is over,
`office land SID` (or the folder) ends it: `bale unlock` in its repo,
and an `ended` line in the folder's History. The folder stays as it is,
since a planning folder may outlive one sitting; `office close` is
yours. Its `standing.md`, when it filed one, stays too, as the record of
where it ended (0.43.0). A HOLD, a refusal or a clarification lands nothing: nothing
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
    office probe                         # the folder whose one session is open, said (0.41.0)

With no FOLDER (0.41.0), the folder is found rather than looked up: when
exactly one folder on the desk records a session open where probes run (a
read-only sitting open in the office, a session open in the office, or a
session open on a project), it is that folder, and the office says so:
`desk/NAME records the one session open, SID (a sitting), so the probe is
its (office probe FOLDER names another)`, the parenthesis `on PROJECT` or
`in the office` for the others. With several, those folders alone are
offered by key, sittings first (piped, they are named and the probe
refuses); with none, every folder on the desk, as before. `--project` and
`--sid` are as they were.

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
read-only sitting the folder records, open in the office's own registry,
is a session a probe can be for too (0.33.0): a sitting is open in the
office, never in the project, so before this a sitting's probe of a
project's repo was refused and had to be run by hand. With `--project
NAME` it runs in that project's repo (through its shell on a host) under
the sitting's id, its fallback's files go to the sitting's out tray, and
the History line counts it against the sitting. A folder with a sitting
and a session open in the project keeps the project's session, unless the
block's slug or `--sid` names the sitting; without `--project`, a
sitting's folder whose lane names no project is asked where (or told
`--project office`) as before. A folder with none gets no probe run,
since a probe is a session's. A
`probe-output/` already where it runs stops it too, since a fallback
probe's output could not be told from it. On a host all of this is one
connection, which is the reach. Then it shows the header and where the
block runs, and asks once, `y` or `N`, default no; `--yes` is the flag
twin, and piped, nothing runs without it.

A block may span the office and a project's host (0.34.0): a planner
sitting that needs the office's pages and a hosted repo in one probe,
say, which before this ran several probes by hand. Such a block calls
`office-on PROJECT COMMAND...` on its own lines, naming one of the
office's projects literally each time (never through a variable; a header
line that mentions the helper names no project). A reach is a call
(0.45.0): `office-on` counts only where it is a command's first word, at a
line's start or after `$(`, a backtick, `|`, `&&`, `;`, `(` or `{`, never
its name inside a string, a comment, a heredoc's body or an echo's text,
so a block that only mentions the helper is a plain block, run where the
folder's lane says. `office probe` reads the
names before anything runs and refuses one the office does not scope,
then runs the block in the office root with `office-on` first on its
PATH, a helper written for that one run beside the plan: each call runs
its command where that project lives, in its repo here or through its
shell in its path on a host, stdin closed, its output on the block's own
stream and its exit code returned (97 when the project cannot be reached,
or is not one the block named). The call's words arrive as given
(0.45.0): each is quoted on the way to the project's shell, so
`office-on PROJECT bash -c SCRIPT` runs SCRIPT whole there, a word with a
space stays one word, and a quote or a `$` in a word arrives as your shell
left it; a shell line is written `office-on PROJECT sh -c 'LINE'`, since
one quoted word is one command's name. Such a block takes no `--project`
(`office` is the only one that fits, and is said); its session is the
folder's open in the office, a sitting or an office session, or in a
project it reaches, chosen by the rule above; a fallback's
`probe-output/` is the office root's, carried the same way. The block's
header still promises it is read-only, and the promise covers every
command the calls run.

The block runs with its stdin closed: in the project's repo, or through
the project's shell in its path, in the plain form with no terminal
asked for (a probe never waits on one), or in the office root. Its
stdout and stderr come back to your terminal whole, its stdout line by
line as each line ends (a partial line shows when its end arrives). The
lines from `PROBE BEGIN` to `PROBE END` go on your clipboard with the
office's own `clipboard_command` (on WSL, `clip.exe`), since the block's
closing `bale clipboard` step runs where no clipboard is; the office says
how many lines came back between the sentinels and whether the integrity
trailer's count matches them, and, when it masked any, how many. A block
that never closes is said, and nothing is copied.

Everything `office probe` hands back from the block's stdout is masked
(0.38.0): a credential written into a URL, `scheme://user:SECRET@host`
of any scheme, comes back as `scheme://user:xxx@host`, its user kept so
you still know whose it was, and a GitHub token in one of its own shapes
(`ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`, `github_pat_`), bare or as a
URL's user part, as `ghp_xxx`: on the screen, on the clipboard and in the
count's line, which then ends `1 credential in a URL was masked (xxx
stands for it)`. A line is masked, never dropped, so the block's count
and its trailer still match. The mask is a seatbelt, not a promise: a
probe should still never print a remote URL with a credential in it
(`git remote -v`, `git config --get remote.NAME.url`), a token of any
other shape printed bare is not caught, and a fallback's `probe-output/`
files and the block's own closing `bale clipboard` copy are not masked.
The block's stderr is masked the same way since 0.43.0 (a `git fetch`
against a remote with a credential in it prints the URL there), read
beside stdout and shown as it comes, never kept or copied; when its mask
replaced anything, the count's line says which stream (`1 credential in a
URL on stdout and 1 GitHub token on stderr were masked (xxx stands for
each)`). `OFFICE_PROBE_TIMEOUT` (seconds, default 1800) stops a
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
    office deliver 6 --branch picklists --adopt  # onto a pull request's branch made outside the office
    office deliver                               # the folders landed and not delivered, by key (0.41.0)
    office deliver 14 --yes --close              # piped: close the folder once its work is delivered
    office deliver 14 --yes --open-review        # piped: push, then open the review through gh (0.42.0)

A folder closes at delivery (0.41.0; the plan's ruling of 2026-10-29):
`office land` leaves a folder on a project with an audience on the desk,
and after a successful push deliver closes it, done, when every applied
session it records (its Sessions lines whose session is applied in the
project) is named by a `delivered` History line, this delivery's or
another folder's (a session another folder delivered with `--others-too`
counts), or rides in nothing because the base holds it. It says so in
land's words, `the folder NAME: closed, done (its work is delivered;
office reopen NAME brings it back)`. On a terminal it closes without
asking, as land closes a finished folder; piped it stays and deliver
says so, unless `--close`; `--leave-open` keeps it on the desk; a folder
already in the filing cabinet is left there. A session still to deliver
is named, and the folder stays. Until then the desk's line for it says
`landed SID on DAY, not delivered; office deliver N`, the home screen
offers it by key, newest landing first, the walk-in's Next line names it
after the desk moves, and bare `office deliver` offers it under `Landed
and not yet delivered:` before every folder. Whether a folder's work is
delivered is read from the office's own pages and the project's
`applied/SID` tags, with git alone: never a fetch of the audience, never
a bale call. A folder whose merge job waits for its session is offered
the same way, by `office start N --merge`, and `office status` says it
under the folders line: `folder N: merge job waiting, AUDIENCE/BRANCH
into the workbench, K file(s); office start N --merge sends the session`
(or, once that session landed without its merge made, `merge session SID
landed; office deliver N makes the merge commit`).

The project is the folder's lane's (`--on PROJECT` when the lane names
none), and it must declare an `audience`: the name of the remote in its
clone that points at the audience's git host, set with `office projects
add` or `set --audience origin`; a project with none (the home office's
own, say) is refused by name. The folder must record at least one
session applied in that project. In order, each step logged:

- The audience's base branch is fetched (the project's `base`, or the
  audience remote's HEAD branch read from the clone), and the delivery
  branch when an earlier delivery made it: a second delivery for the
  same folder adds to the same branch, carrying only what is new since
  the last delivery there (0.40.0, below). The branch is chosen in one order
  (0.38.0), and `[office] the delivery branch is BRANCH: WHY` says which
  rule chose it: `--branch NAME`; else a `- branch: NAME` line in
  `delivery.md` (a short name, like `results-view`); else the branch the
  clone has checked out, when the audience has it and it is not the base
  (`office start` checks out the branch a brief's BRANCH line names, so
  it is the one the session built on); else the folder's slug. A
  project's `branch_prefix` in the floor plan (`feature/`, kept with one
  trailing slash) goes before the words' short name and the slug, never
  before a `--branch` name, the clone's branch or a name that holds a
  slash. A branch another folder of the office delivered to is the
  office's: the delivery continues on it with no `--adopt`, from that
  folder's last delivery there, and the next line names the review
  already open on it (0.38.0). A branch the audience has that no folder's
  records cover was made outside the office (a pull request opened by
  hand): deliver says so and, on a terminal, asks once whether to add
  this delivery to it, default no (`--adopt` is the twin, and acts on the
  branch whichever rule chose it; piped, it refuses and names it); this
  is how a review's answer lands on the review's own branch (0.34.0). A
  branch renamed on the git host is told to the office the same way:
  `office deliver N --branch NEW --adopt` on the next delivery. Adopted,
  the range read next is what the branch does not have yet, from where
  the workbench and the branch parted.
- The landed work since the last delivery, or since the workbench branch
  and the base parted, is read: every applied session in it is named by
  its id and the folder it belongs to. Sessions of other folders ride in
  the same delivery (the office does not split one branch's history by
  folder); deliver says so, names them, and on a terminal asks whether
  to go on (`--others-too`; piped, it refuses without it). A session
  another folder already delivered is refused by name (0.38.0), with the
  folder, the branch and the day, and `office deliver N --branch
  THAT-BRANCH` as the remedy, since that work would leave twice;
  `--others-too` does not admit it. The one exception is a base that
  holds that delivery already: by history (its workbench or delivery
  commit is on the base, a review merged as a merge commit or a
  fast-forward) or, since 0.40.0, by content (the delivery commit's change
  squashed onto the base, in a temporary worktree, changes nothing: a
  review merged as a squash; the delivery commit is read where the
  delivery is built, or fetched by its branch when that is not there).
  A base that holds a later version of the same lines is not held, rightly,
  since the work left twice would conflict; the refusal says the base
  holds the delivery `by history or by content` in neither way, and a
  branch gone from the audience is said rather than offered. Sessions
  the base holds ride in nothing (0.40.0): one line says so (`folder 6's
  session SID is on origin/main already (by content: folder 6's delivery
  3f1a9c2) and rides in nothing here`), `--others-too` is not asked for
  them, and the `delivered` line does not name them again.
- The words come from `desk/FOLDER/delivery.md`: the commit subject and
  body, the review request's title and body, `- to: NAME` for the
  reviewer, and, beside it, `- branch: NAME` when the session names the
  branch (0.38.0; the install's templates/delivery.md says the shape; a build
  session writes it and `office land` files it). Missing, deliver stops
  and says what to write where. A Review with a title and no body refuses
  before anything is made (0.47.0), naming the page and the title's line
  (`desk/14-health-route/delivery.md:12: the Review has a title and no
  body; ...`), since the body is what the review's readers see; `office
  letterhead check --delivery` and land's review say the same.
- In a temporary worktree at the audience's tip, what bale's own commits
  changed is taken out first (0.36.0): the commits bale makes for itself
  with no session's work in them, its housekeeping `bale: ignore .bale/`
  and its sweeps (never a session's `[bale SID]` work commit or its
  landing merge), are undone on the workbench's tip with `git revert`,
  newest first, each in a temporary commit that never leaves, and the
  plan names each one (`taken out: ... SHA bale: ignore .bale/
  (.gitignore)`). A line of bale's that later work already took out is
  simply gone; where later work touches the same lines and adding lines
  was all bale did there, bale's lines are taken out one by one and the
  plan says so; anything else refuses by name, with the remedy (undo
  bale's change by hand on the workbench branch, and deliver again).
  Before 0.36.0 the whole range was squashed and only bale's names left
  the index, so `.bale/` in `.gitignore` rode in a delivery
  (found 2026-10-28, delivering a work office's folder 6). Then the landed
  work is squashed on (`git merge --squash`), the names bale makes are
  taken out of the index whatever the clone tracks (and named never read
  to the check, since they stay on the worktree's disk), and the lines
  the squash adds and the words go through the letterhead check, the
  office's letterhead with it. Since 0.38.0 the check reads only the
  lines a delivery adds, never the files it touches whole: a line a file
  already had is not the delivery's, and what such lines hold is told
  under the verdict, one line per file (`src/views/UploadView.vue: 6
  line(s) the file already had hold the em dash (U+2014); not this
  delivery's, not refused`), and nothing stops (found 2026-10-28: a
  delivery was refused for six em dashes already on the audience's own
  main); the question's closing line says so since 0.40.0, `letterhead on
  the lines it adds and the words: clean`. The words, and only they, are also held to the letterhead's
  `[cleanup]` list: a fix made only to keep the letterhead is shipped
  clean and never named, so words naming one (`delivery.md:L: names a
  cleanup: 'em dashes' in: ...`) refuse the delivery; files are never
  held to it (a bale path (`.bale/`, `bale.toml`, `.baleignore`) is one of
  the letterhead's marks since 0.36.0, so a line that leaves naming one
  refuses the delivery, whatever put it there; the
  dashes and the ellipsis refused by default; the lines of the
  repository's own pull-request template, as the audience's base holds
  them, exempt from the phrasing rule and, since 0.26.0, the three
  characters, a checklist line whatever its box holds since 0.32.0);
  one hit refuses the delivery,
  with nothing pushed. The words are what of `delivery.md` leaves: its
  `to:` line and its Commit and Review sections, each hit named at its
  line of the page. A section runs to the next Commit or Review heading,
  so a pull-request template's own `## ` headings filled into the Review
  are its words, read and sent (before 0.35.0 such a heading cut the
  Review short). The page's heading, the note `office land` files under
  it and anything else above the first section stay in the office, and
  deliver says how many such lines it did not read (0.35.0: a page
  `office land` filed before then names its session in that note, a bale
  mark, and delivers as it stands; one filed since names none).
- The words become one commit (several when `delivery.md` has several
  Commit sections, each but the last naming on a `paths:` line what it
  takes), authored and committed as the project's declared `author`
  (`Name <email>`; a project with none is asked once on a terminal and
  keeps it, `--author` the twin; piped, deliver refuses and names it;
  the clone's own identity is never used).
- Each commit is shown whole, as it will be pushed: its subject and
  body, its author and committer, its date, the files it touches, and the
  letterhead's verdict on it; with the diff's stat, the sessions covered
  and the branch, with the rule that chose it (0.38.0: `branch:
  feature/results-view, from main (delivery.md's branch line names
  results-view, behind api's branch prefix feature/)`) and, on a branch
  another folder delivered to, that folder and its day (`adding to the
  branch desk/6-picklists delivered to on 2026-10-28`).
  Several commits are dated a second apart, oldest first (0.32.0), so a
  reader sees their order and never a burst made in one second, and one
  line before them says how many leave: one commit per delivery is the
  usual shape. deliver asks once (`--yes`; piped, it refuses without it).
- Every commit's author and committer is checked against the declared
  author, and those commits alone are pushed as the delivery branch,
  with its name in `OFFICE_DELIVERY` for the push guard and no tag
  following; never the workbench branch.
- The folder's History gains a dated `delivered` line: the branch, the
  audience, the sessions covered, the workbench commit and the delivery
  commit, and `; adopted` at its end for an adopted branch, so the next
  delivery adds to it as to one of the folder's own. Then what you do
  next: open the review (a URL when the git host's compare-URL shape is
  known, GitHub, an enterprise instance named github.*, or GitLab, with
  the review's title and body in it and, on WSL, on the clipboard; the
  branch's name otherwise) and whom to send it to, when the words name a
  reviewer. For an adopted branch the review is the one already open on
  it: the next line lists the reviews for that branch on the git host
  (GitHub's pull requests with that head, GitLab's merge requests with
  that source branch), and the Review section's words are the reply.

The delivery is built on this machine, where the audience answers with
your credentials: for a project on this machine in the clone itself, in
refs the office owns (`refs/office/...`, gone after); for a project on a
host the landed commits come here as a thin git bundle made in the clone
there and carried through the project's shell, into a temporary bare
repo removed after, and the push goes from here. Nothing the office
writes on a host outside the project's repo is left. A hosted delivery
makes three connections when its clone's view of the audience is level
and nothing is merged (the clone's facts and its view of the audience in
one, the bundle, its read).

The clone's view, and the clean merge (0.39.0). Deliver compares the
clone's `AUDIENCE/BASE` with the base it has just fetched here; for a
clone on this machine its own fetch moves that ref already. Behind, one
line says by how much, and on a terminal deliver asks once whether to
refresh it first (`office projects refresh`; default yes; `--refresh`
and `--no-refresh` are the twins); piped with neither, it says so and
goes on without. Ahead or level, nothing is said. Then, for a delivery
made from the base (not one adding to a branch), when the workbench is
behind the base and the clone's view of the base is level with it,
deliver brings the base into the workbench in the clone where the work
lives, through the shell for a host: `git merge --no-ff` of
`AUDIENCE/BASE` on the workbench branch, as the project's declared
author, with the message `Bring origin/main into the workbench (office
deliver)`, only when the merge is clean, the clone's tree is clean and
no bale session is open there (each of the three is said when it stops
the merge, and the plan goes on as before). The question's `merged:`
line says it (`brought origin/main into the workbench: merge commit
8c2e1f0 (14 commits of the audience's)`), and the folder's History gains
`- DATE merged: origin/main 3f1a9c2 into the workbench, 8c2e1f0`. It is
a real merge commit, so the workbench and the base now part at the
base's tip: the squash runs from there and the range carries the
folder's own work. A merge that conflicts is aborted, and the abort
checked (no `MERGE_HEAD`, no tracked change left), and the delivery
refuses naming the files. The merge does not change which sessions
another folder delivered: a review merged as a squash is seen by
content, below.

The merge session (0.40.0). No delivery ends at a terminal: the office
never resolves a conflict itself, and never sends you into the clone to
do it. When bringing the base into the workbench conflicts, deliver
writes the merge's materials into the folder, under `merge/`: each
conflicting file at its path in three versions, `parted/` (where the two
sides parted), `workbench/` and `audience/`; in `audience/` too, since
0.47.0, the audience's copy of every other file it changed since they
parted, listed on the page as `- changed: PATH` lines under the
conflicting files' `- file:` lines (` (added)` or ` (deleted)` after the
path when it was; a deleted file has no copy), so the session sees what
the audience did beside the conflict; and `log.txt`, the audience's
commits since they parted, with `merge.md`, the job's page, all committed
in the office (so they ride with the folder, and `office close` moves
them with it). Its last line sends the session:

    office start 14 --merge          # the merge session: goal, forecast, brief and project from the job

The session is a bale session on the folder's project with both sides in
context: its goal names the side and the files, its forecast is the
conflicting files, its brief comes from the install's
`templates/merge-brief.md`, and the job's page names the session sent.
Its response ships every conflicting file whose resolution differs from
the workbench's, as it should read after the merge, and nothing else (a
file it leaves out keeps the workbench's version, which is right when
that is the resolution: bale admits no file shipped unchanged, 0.47.0),
and writes no Walkthrough, Delivery or Structure (the folder's pages are
the work's). When it lands, `office land` makes
the merge real before anything reads the workbench: a merge commit in the
clone, as the project's author (`Bring origin/main into the workbench,
resolved by SID (office land)`), whose first parent is the landed tip and
whose second is the base's tip the job names, its tree git's own merge of
everything that did not conflict and the session's version of each file
the job names. Anything else (a file still unmerged that the session did
not resolve, an uncommitted change, a session open in the clone) is
aborted and checked, or not begun, and said with the line that makes it
later: the next `office deliver N` makes the merge first when land could
not. The folder's History gains `- DATE merged: origin/main 3f1a9c2 into
the workbench, 7c1e2d3, resolved by SID`, the materials leave the
folder, and the workbench and the base now part at that tip, so the next
delivery squashes the folder's own work. Asked again while the session is
out, deliver names `office land SID` instead.

A continued delivery is squashed from its range (0.40.0). A delivery onto
a branch (its own, another folder's, adopted) takes the range's net
change since the last delivery there (bale's paths out of both ends), as
one temporary commit cherry-picked onto the branch's tip with git's
three-way fallback, so a second delivery that edits a line the first
delivered goes, and only what is new leaves (before, the squash ran from
where the workbench and the branch parted, and such a delivery conflicted
with nothing moved on the audience). When the branch moved on the
audience (a reviewer's commit on it) and the squash conflicts, the merge
session is sent the same way, with the branch's tip in the base's place;
once its resolution is a merge commit, the next delivery is read from
where the workbench and the branch meet, and the sessions the branch
already carries are not named again.

The review (0.42.0). gh, GitHub's own command line, is the office's one
way to a git host's API, and optional everywhere: without it every
surface does what it did before, and says in one line that gh is not
there where it would have read or opened something. Each step:

- Before anything is fetched, the delivery branch's name is held to the
  letterhead's marks, read as the words are read: a name the letterhead
  would refuse in a line (a `bale/` branch, a session id, a forbidden
  word) is refused with `--branch NAME` as the remedy, and a name the
  folder's slug gives that ends in three digits (`fix-login-002`) reads
  as a session id and is refused the same way. A name you give with
  `--branch` or the words' `branch:` line may end in an issue's number.
- After the push, for a branch with no review yet, when gh is on this
  machine (found on the PATH, or where `OFFICE_GH_PATH` says) and signed
  in to the audience's GitHub host (github.com, or a host named
  github.*), deliver shows the review as gh will open it: the Review
  section's title and body, the base, the head, the reviewer when the
  `to:` line reads as a GitHub login (`- to: @pat-reviewer`; a name is
  printed as before and never passed to gh), and the gh line, `gh pr
  create --repo HOST/OWNER/REPO --base BASE --head BRANCH --title TITLE
  --body-file FILE [--reviewer LOGIN]`. It asks once, `Open this review
  on the audience through gh? (--open-review) (y/n) [n]`; `--open-review`
  and `--no-open-review` are the twins, and piped with neither it opens
  nothing and says so.
- On yes it prints `opened the review: #N URL`, and the folder's History
  gains `- DATE review: BRANCH on origin of PROJECT: #N URL`, committed
  alone; Next then names the open review rather than the compare page. gh
  refusing (not signed in to that host, no rights, a pull request already
  open on the branch) is said with gh's own words, and the delivery
  stands: the branch is on the audience either way.
- Without gh, signed out of that host, on no, or on a host gh does not
  reach (GitLab, or a host of unknown shape), the review's body goes on
  the clipboard, said as every copy is said, and its title and the
  compare URL are printed under Next, so opening it by hand is one paste,
  never a retype. The office never signs gh in, and writes no token,
  login or credential anywhere.
- A delivery added to a branch whose review is open (another folder's
  branch, an adopted one, or this folder's own continued) opens nothing:
  Next names `the review that carries it: #N URL` when gh reads it, the
  reviews page for the branch otherwise, and the body goes on the
  clipboard as the reply's words. When gh reads the pull request open on
  the branch, the question's branch line shows the request's base as the
  delivery's from, and a `from:` line says when it is not the project's
  declared `base`; without gh it says in that line that the base was not
  read. The squash is onto the branch's tip either way.
- Review state is read, never asked for: `gh pr list --repo
  HOST/OWNER/REPO --state all --json ...`, read-only, one call per project
  with a branch the office delivered, a 15-second timeout, no prompt. The
  walk-in and `office desk` gain a `Reviews:` section after what is in
  flight, one line per project (`proj: #12 approved (health-route, folder
  14)`), each review `#N approved`, `#N changes requested`, `#N review
  pending`, `#N merged` or `#N closed`; a review that asked for changes
  gets a line saying what answers it (a session on its branch, then
  `office deliver N --branch BRANCH`). The desk's line for a folder says
  `[review #12 approved]`, and its next names the changes asked for first.
  The home screen's project line ends `; reviews: ...`, and the digest
  has a `Reviews` section. An open review always shows; a merged or
  closed one shows while its folder is on the desk, or for a week. It is
  a rendering, recomputed on every run and kept nowhere. gh absent, signed
  out or the host not answering is one line in the project's place
  (`proj: review state not read: gh is not on this machine`), never a
  refusal. A project on a host reads the same way from this machine, from
  the repository a recorded review names.

The push guard. Declaring an audience (`office projects add --audience`,
`set --audience`) writes a pre-push hook into the clone's `.git/hooks`,
outside what git tracks, as `--prepare` keeps everything the office
writes; `office deliver` installs it when it is missing. Nothing reaches
the audience from the clone but the one delivery branch deliver pushes,
named in `OFFICE_DELIVERY`: no tag (bale's `applied/` tags or any other),
no bale branch, no other ref and no deletion, whatever the push's form
(`--tags`, `--all`, `--mirror`, a refspec, a tag by name), the audience
known by its remote's name or by any URL that is the same repository.
Each refusal names `office deliver`. A push with `--no-verify` runs no
hook at all; the guard keeps a slip out, not a deliberate act. The hook
carries `guard_version=2`: `office status` names an older guard (0.17.0's)
with the line that replaces it, and `office upgrade` or `office projects
set NAME` replaces it. A clone with `core.hooksPath` set, or another
pre-push hook, is said and left alone.

After a session lands on a project with an audience, `office land`
reviews it against the letterhead as deliver will (the lines its landing
added, since 0.38.0, never the files it changed whole, bale's own aside,
and the folder's `delivery.md` words) and says
in a line what deliver would refuse, each line named, so the fix rides
the next session; it refuses nothing.
Known gap: a push from the host itself is not built (the probe found the
work host's credential cache empty, so nothing reaches the audience from
there without a prompt); the delivery crosses from this machine.

The letterhead check:

    office letterhead check                      # the files the tree here changed, as they are
    office letterhead check --all ~/work/api     # the whole tree
    office letterhead check --on api --range origin/main..HEAD   # in a project's repo, on its host
    office letterhead check --added --range origin/main..HEAD    # the lines the range adds, as deliver reads
    office letterhead check --delivery desk/14-health-route/delivery.md   # a delivery's words, as deliver reads them
    office letterhead check --words notes/announcement.md                  # any other text, whole

It names every line that holds what the letterhead refuses, as
`file:line: what`, and exits 1 with a hit. For a folder's words use
`--delivery` (0.42.0): it reads a `delivery.md` as deliver reads it, its
`to:` line and its Commit and Review sections, and says in a line what it
did not read (the page's heading, the note office land files under it),
so the hand check agrees with deliver, on a page filed before 0.35.0 too,
whose filing note names a session. `--words` reads a file whole, heading
and comments too, for any other text. `--delivery` travels with `--on PROJECT`, to a
project on a host too. What it refuses is one list in
the install, share/letterhead.toml: the names of models, vendors and
products; tell-tale phrasing an assistant writes and a person does not;
and bale's marks (its commit subjects, `applied/` tags, `bale/` branches,
session ids and, since 0.36.0, the paths bale makes in a working copy:
`.bale/` and the files named after it, `bale.toml`, `.baleignore`); plus,
when the office has a letterhead, each
non-blank, non-comment line of `letterhead/forbidden.txt` as a fixed
string, and the em dash, the en dash and the ellipsis character, refused
by default with no line needed and each named in a refusal (a line
`lift: em dash` in the forbidden list lifts one, said on every check).
Words and commit messages, never files, are held to one list more, the
`[cleanup]` list (0.38.0): a fix made only to keep the letterhead is
shipped clean and never mentioned, so words that name the cleanup (`em
dashes`, `en dash`, `ellipsis`, their code points) are a hit, rendered
`names a cleanup`; a project's own text may name the characters, and
office-src's does.
The letterhead arrives with the first project given an audience: its
front page, its voice page (`letterhead/voice.md`, the occupant's style
rule for text that leaves the office, an empty marked place for his
words) and its forbidden list, from the install's templates; a session
on a project with an audience carries it and reads the voice page before
it writes. The check never writes it. In a git repo, a line of `--words`
that is a line of the repo's own pull-request template, as HEAD holds
it, is not held to the phrasing rule or (0.26.0) the three characters:
its words are the repository's, and a template you cannot change would
otherwise refuse every delivery that fills it. Names, bale's marks and the
forbidden list still read it, and a template line you change is yours.
A checklist line is the template's whatever its box holds (0.32.0):
ticking `- [ ]` to `- [x]` (or `- [X]`) changes nothing, and words added
after the box do.
The suite's own text rules read the same list, so office-src's text is
held to it too. Scope: the files a range changed and its commit messages
(`--range A..B`, which is how deliver checks a delivery's diff); else the
files a dirty tree changed, as they are; else the whole tree (`--all`,
or a directory that is not a git repo, said so). `--words FILE` checks a
text as it is. `--added` (0.38.0) reads the lines a diff adds, not the
files it touches whole, as office deliver reads a delivery: with
`--range`, what the range adds; else what the index adds against HEAD.
Each added line is read at its line in the new file, and a new or
renamed file is all added lines; a line a file already had is never a
hit, and what such lines hold is told, one line per file. It is refused
beside `--all`, and travels with `--on PROJECT` since 0.40.0, so `office
letterhead check --on api --added --range origin/main..HEAD` reads a
project's range as deliver reads a delivery. Binary files are skipped by name and by a NUL
byte; `OFFICE_DEBUG=1` names every file read. `--on PROJECT` runs it in the
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
Each session is searched for where it is likely to be (0.38.0): the
project the folder's lane names first, then the projects whose records
name the session, then the rest, each read in its own try and only when
the search reaches it, so the common case is one read and an unrelated
broken clone or a host that is down is never opened. A project that
cannot be read is one line after the sessions (`distributions-app: not
read: WHY`), not a stop; the verb stops (exit 1) only when a session was
not found while some project could not be read, since only then is "not
found" in doubt, and its line says so.

The folder's two pages. Nearly every job produces two deliverables
(doctrine section 3, principle 6): the thing, in the project, and the
message about it. A build session writes the message as two sections at
the end of its notes.md, Walkthrough (what changed, why, how to explain
each piece, the questions a reviewer will ask, a hand test for what only
eyes can check) and Delivery (the commit subject and body, the review
request's title and body, `- to: NAME` for the reviewer, and `- branch:
NAME` when the session names the delivery branch), each heading
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
all the same. Each page is filed under a comment saying `office land`
filed it: the walkthrough's names the session, and since 0.35.0 the
delivery's names none, since a session id is one of bale's marks and
`delivery.md` is the page of the words that leave.

### The projects an office scopes, and what bale records about them

    office projects                          # the projects this office scopes, and where each is
    office projects add office-src ~/office-src   # add one (asks on a terminal for what it was not given)
    office projects add api ~/development/api --host me@workhost --prepare   # one on another host
    office projects add api ~/development/api --host me@workhost --from ~/work/api   # bring a clone there
    office projects level-bale api           # the host's bale brought level with this machine's
    office projects refresh api              # the clone's view of its audience brought level
    office projects set api --prepare        # prepare the clone again: bale's sandbox setting where it cannot run
    office projects set api --shell "ssh me@workhost docker exec -i -u me box bash -lc"
    office projects set api --connect "start the VPN client, then retry"
    office projects set office-src --ride ~/other-repo/docs --after-land ./install.sh
    office projects set api --audience origin --author "Pat Example <pat@example.org>" --base main
    office projects --ledger                 # trust ledger per project and work class
    office projects --landed bin/office      # the last applied session that landed a path
    office projects office-src --versions    # the version trail of one project
    office projects set distributions-app --paused   # read nothing of it, send nothing to it (0.41.0)
    office projects set api --path ~/work/api-2      # another clone, checked as add checks one (0.46.0)
    office projects set api --branch-prefix feature/ # before a delivery branch's short name (0.46.0)
    office projects set api --ride host:~/notes/plans  # a ride on api's host, packed there (0.50.0)
    office projects set api --audience-url git@github.com:acme/api.git   # kept for a hosted project (0.50.0)
    office projects set api --edit                   # every group, keep or change, on a terminal

What `office projects set` asks (0.46.0): given a project and any flag,
it changes that flag's group and asks about no other; given a project and
no flag on a terminal, it asks group by group as before (where it is, the
audience line, what rides, what runs after it lands), which `--edit`
names explicitly (piped, `--edit` refuses). `--path PATH` re-points a
declared project at another clone: the path is checked as `office
projects add` checks one (here, or on the project's host through its
shell: a git repo bale runs in, or prepared with `--prepare`), the floor
plan's `path` is rewritten, and the old clone is never touched or
removed; one line says both paths. `--branch-prefix PREFIX` and
`--no-branch-prefix` write and clear the audience line's fifth key, the
prefix office deliver's branch rule puts before a delivery branch's short
name; the listing shows it with the audience line.

A project can be marked paused (0.41.0; the gaps of 2026-10-28, A7):
`office projects set NAME --paused` writes `paused = true` in its
[projects] entry, committed as set commits, and says `NAME is paused: the
office reads nothing of it and sends nothing to it until office projects
set NAME --unpaused (one thing is still read: which of its sessions a
bundle in your downloads opened, so that bundle leaves the offer)`;
`--unpaused` removes the key. Given alone, either asks nothing else. The
one read (0.46.0): the home screen and bare `office start` read a paused
project's session list once per screen to tell whether a bundle in your
downloads was opened there, so it leaves the offer as any other. Every rendering that reads a project's repo (the
walk-in and its In flight, the home screen's project line, `office desk`,
`office status`, `office sessions`, `office projects` and its renderings,
the digest and the watches) reads nothing of a paused project, no bale
call and no git, and says one line where its "cannot read" line would go:
`NAME: paused (office projects set NAME --unpaused)`; `office projects`
lists it with `(paused: office projects set NAME --unpaused)` in place of
the check of its path. `office start` refuses to send a session to it,
by its folder's lane or `--on`, with that line, before anything is
written. Every other verb is as it was: a session already out on it
still lands, and deliver and probe still run there.

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

bale's sandbox (0.39.0). bale runs a response's scripts in a namespace
sandbox, and on a host without unprivileged user namespaces (a container,
often) its self-probe refuses and, on a terminal, every apply asks
whether to run unconfined. bale's own help names the durable form,
`bale.toml`'s project-layer `[sandbox] enabled = false`, with the same
unconfined semantics, FORCE-logged naming the key on every run. Prepare
now tests that condition where the clone is, through the host's shell for
a hosted one (`unshare -Ur true`: one unprivileged user namespace, the
least bale's sandbox needs, so the office's test is never stricter than
bale's), and only where it refuses writes that table into the
`bale.toml` it keeps out of git, under a comment naming why and the day
(`# office sandbox: written 2026-10-29: no unprivileged user namespaces
where this clone is (...)`). Where the sandbox runs, nothing is written;
a `[sandbox]` table already there is left as it is; a test that cannot
run (no `unshare` there) writes nothing; and the office writes nothing
else into bale's project layer. `office projects set NAME --prepare`
runs prepare again on a clone already declared, asking nothing, so a
clone added before this release gets the setting without being added
again. `office status` names it per hosted project (`proj: sandbox: off
by bale.toml, written 2026-10-29: ...`), and where the sandbox cannot
run and nothing turns it off, the line that writes it; nothing when it
is not needed.

A clone's view of its audience (0.39.0). A clone on a host often cannot
reach the audience's git host (it has no credentials there), so its
remote-tracking refs stay where they were and a session builds on what
the clone last saw. `office projects refresh NAME`, for a project that
declares an audience, fetches the audience's branches on this machine,
with this machine's credentials, always with a forcing refspec, so a
branch the audience force-pushed moves too. For a clone on a host it
reads the clone's refs first, makes a bundle of the branches that moved,
thin against what the clone already has, carries it through the shell
and fetches it there with `+refs/heads/*:refs/remotes/AUDIENCE/*`, the
bundle removed in the same connection; for a clone here it is a plain
forced fetch. Then it fast-forwards the base branch: `--ff-only` when it
is checked out, its tree clean and no bale session open there; the ref
moved after an ancestry check when another branch is checked out. A base
with commits of its own is said and left (a refresh never merges), and a
dirty tree stops only that step, said. It says what moved, one line per
branch (`origin/main: 59385bf..3f1a9c2, 14 commits`; `forced` for a
rewritten one; `new` for a new one), or `nothing moved`; it never moves
the workbench branch, never deletes a ref, pushes nothing and asks
nothing (`--yes` is taken). It leaves one ref in the clone,
`refs/office-refresh/AUDIENCE`, naming a small blob that says when and
from where, and `office projects` lists it under each project with an
audience (`refreshed: 2026-10-29T13:40:00Z from origin URL, by way of
HOSTNAME`), read from the clone itself, through its shell for a hosted
one (the listing's one connection per such project); no file of the
office's records a refresh. `office start` and `office deliver` offer it
when the clone's view of the base is behind (Sending a session out: the
details; Delivering to the audience: the details).

A project may declare what
rides beside every session on it (`--ride PATH`, repeatable: a directory
inside another repo, a whole repo, or a file) and what runs in its repo
after one of its sessions lands (`--after-land CMD`, repeatable; `office
land` runs them). `office
projects set NAME` asks for both on a terminal, and `office projects`
shows them. They live in the office, never in the project's repo.
A project on a host may declare a ride on that host (0.50.0): `--ride
host:PATH`, PATH as the host's shell sees it (absolute or `~/`), stored
as typed. It is checked where it lives, through the project's shell in
one connection when it is declared; a path not there, or a host that
does not answer (its connect line), declares nothing, and a `host:` ride
on a project with no host is refused by name. `office projects` and the
map show it as stored, marked as the host's (`rides: host:~/notes (on
HOST)`), and reach no host for it. The three forms, side by side:
`--ride PATH` (here), `--ride host:PATH` (on the project's host) and
`--audience-url URL` (below).
A project with an audience declares three more, the audience line's
(`office deliver` reads them): `--audience REMOTE`, the name of the
remote in the workbench clone that points at the audience's git host
(origin, usually; checked against the clone's remotes; a project with
none is never delivered); `--author "Name <email>"`, the identity the
audience expects on the delivery commits, as both author and committer
(unset, `office deliver` asks for it once on a terminal and keeps it;
piped, it refuses and names `--author`; the clone's own identity is
never used); and `--base BRANCH`, the audience branch deliveries branch
from (unset, the audience remote's HEAD branch, read from the clone).
The audience line has a fifth key, `branch_prefix` (`feature/`, kept
with one trailing slash), which `office deliver` reads from the floor
plan and puts before a branch named by the words or the folder's slug
(0.38.0); no verb sets it yet, so it is written into the floor plan by
hand until its flag is built (0.46.0 built it: `--branch-prefix`). A
sixth, `audience_url` (0.50.0), is kept for a project on a host only: the
audience remote's URL, written when `--audience REMOTE` is set, read from
the clone's remote through the shell then, or given with `--audience-url
URL` (`--no-audience-url` clears it). A rendering never reaches a host,
so it is what lets such a project's review state read before its first
review is recorded; `office projects` shows it. An existing hosted
project gets its URL by running `office projects set NAME --audience
REMOTE` once. A project on this machine keeps none: its clone is read
each time. On
a terminal `add` and `set` ask the three after the host question,
defaults read from the clone; `--no-audience` takes a project off the
audience line, `--no-author` and `--no-base` clear one. Declaring an
audience installs the push guard in the clone (above), and the first
project given one brings the office its letterhead.
A project with an audience is worked from a guarded clone on this
machine (0.25.0): with `--audience`, `add` takes PATH as that clone here,
and a host declared with it (`--host HOST`, or `--validates-on HOST`) is
recorded as `validates_on`, where the project validates, never where it
is worked (nothing validates there yet). `--worked-on-host` keeps the
repo worked on its host, as before. On a terminal the same default holds
(0.26.0): once a project you gave a host has an audience, the wizard
offers by key where it is worked, here (the default, asking the clone's
path on this machine, the host kept as where it validates) or on the
host. Projects already declared on a host work as they did.

    office projects add beta ~/work/beta --audience origin --host me@workhost   # worked here, validates on workhost Walking in shows the sessions
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
| bin/office | the command (bash); `pylib` starts each Python helper as a module, with -B, -P and (0.28.0) -S; since 0.29.0 the reads a command makes side by side go out as one call (`batch_call`, `batch_run`), the stamps and skew are read once per command (`skew_read`) and a helper's JSON answer is read back once (`json_read`); since 0.30.0 a landing's record, bale apply and its outcome are one `office_bale land` call |
| lib/office_helper.py | TOML, profile, survey, migration and floor-plan helpers (python3, standard library); since 0.28.0 the LazyPattern and OneSubcommand every module's start leans on; since 0.29.0 `batch`, several subcommands of any lib/ module in one process, and `skew-report`; since 0.30.0 `bytecode-check`, office status's line on the install's bytecode cache; since 0.33.0 the doctrine stamp a sitting's Sessions line carries (`sitting_words`, `session_doctrine`) |
| lib/office_bale.py | the only code that runs bale, through its --json surfaces: the read side and the renderings built on it (the desk's groups, the walk-in's Next line and the one-writer rule among them), office start's packing, bundles and out tray, and office land's apply and what it reads after (one `land` call since 0.30.0: the office's record out, bale apply or retry, the outcome); since 0.37.0 bale's two accepts, passed as typed, said, and named after a refusal (`accept_flags`, `accept_said`, `accepts_bale_names`, `accept_line`); since 0.38.0 office sessions' search, the lane's project first and an unreadable project a line (`project_records`, `folder_lane`) |
| lib/office_host.py | a project on another host: the host, shell and connect keys, the shell that reaches it (every bale and git read of a hosted project runs through it, batched per round), the reach check, the check and the preparing of a clone for bale, here or there, and since 0.17.0 a clone's git facts, the push guard (version 2 since 0.25.0, and the state of an older one) and a bundle carried back |
| lib/office_probe.py | office probe: a worker's probe block read (refused by name when it is not a probe or does not say it is read-only), where it runs and the session it is for (since 0.33.0 a read-only sitting open in the office among them), the run through office_host, what came back between its sentinels, and the fallback's probe-output/ carried to the out tray; since 0.34.0 a block that spans the office and a project's host (the projects its office-on calls name, the helper written for the run, and what each call runs where the project lives; since 0.45.0 a reach is read from a call alone, `calls_of`, and `run_on` quotes the call's words); since 0.38.0 the mask over what it hands back, a credential in a URL and a GitHub token (`mask_text`, `MaskedScreen`), and since 0.43.0 over its stderr too |
| lib/office_standing.py | where a sitting stands (0.43.0): the standing block read to its shape (`read_block`, the last block in a text counting), taken out of a probe's text (`split`), filed as a folder's standing.md (`write`) and said on the screens (`folder_standing`, `words`) |
| lib/office_ask.py | office ask, the quick path (0.48.0): an ask's out tray and its record beside it (`send`, `asks_out`), the LEARNED block read to its shape (`read_block`, the last block in a text counting) and filed as a notepad page, the handbook's facts through office_sort's filing and the questions and answers on the page (`file_block`, `append_qa`), and the tray removed once it is filed (`close`) |
| lib/office_deliver.py | the audience line's crossing: office deliver's plan (the fetch, the carry, the squash, the check, the commits read back whole; since 0.34.0 a branch made outside the office adopted when the occupant says so; since 0.36.0 what bale's own commits changed taken out before the squash, own_commits and take_out_own; since 0.38.0 the lines the squash adds checked rather than its files whole, the branch rule and the rule that chose it, `branch_why`, a branch another folder delivered to continued and work it delivered refused twice, `other_deliveries`), its run (the identities checked, the push, the record) and what it abandons; office letterhead check --on PROJECT; since 0.25.0 the office's side of the letterhead (its rules, its arrival, its voice page), office status's letterhead and guard lines, what office upgrade brings without a migration, and office land's review; since 0.35.0 a folder's delivery.md read as the letterhead reads it at deliver and at land's review alike, the words that leave and nothing of the office's (delivery_words); since 0.40.0 the merge session's job, its materials and the merge commit made from its landed resolution, the content test of a delivery a review merged as a squash, and a continued delivery's range squash; since 0.47.0 the merge's materials carry the audience's side whole, every file it changed since the sides parted |
| lib/office_letterhead.py | the letterhead check, standalone (imports nothing of the office, so it travels to a host as the program python3 reads from stdin); the characters an office's letterhead refuses and lifts, and a repository's pull-request templates; since 0.38.0 the lines a diff adds read rather than its files whole (`--added`), and the words-only lists (`WORDS_ONLY_SECTIONS`) |
| lib/office_review.py | pull requests through gh (0.42.0), the office's one door to a git host's API: gh found through `gh_program` (the PATH, or `OFFICE_GH_PATH`), the review deliver offers and opens on the occupant's yes and the `review` History line it leaves, the base of the pull request open on a branch, and the review state the walk-in, office desk, the home screen and the digest render, read-only and kept nowhere; since 0.43.0 the `reviews:` lines of land's tail (`tail_lines`) |
| share/letterhead.toml | what the letterhead refuses: names, phrasing and bale's marks (its commit subjects, tags, branches, session ids and, since 0.36.0, its paths), one list for office letterhead check and the suite's text rules; and the characters an office with a letterhead refuses by default; since 0.38.0 `[cleanup]`, the names of a cleanup, read in words and commit messages only |
| doctrine/OFFICE.md | how every office works; it opens with a reading card naming what each kind of session reads, and what a build session reads sits above its PAST THE CORE banner |
| doctrine/checks/ | checks a session pastes into its validation; rides with the doctrine into every office session. filed-append-only.sh proves a filed page only grew at its end |
| share/spaces.toml | every space an office can have; the base ones are the default floor plan; a space files itself whole or as a list of paths |
| share/profile-shape.toml | the profile's required sections |
| share/bale-consumption.toml | every bale verb, flag and JSON key the office reads or runs, the shapes of the commits bale makes (a session's, and since 0.36.0 bale's own), and the bale version they were written against |
| share/verbs.toml | what each verb ships, where it lands, whether a person must be present and what may set it off; a session kind with no declared landing may not run unattended |
| lib/office_drafting.py | the drafting table: its arrival in an office (the steps take the space they arrive, so the in-tray arrives through them too), the one reader of its pages (blueprints, riders, the agenda, the ledgers, desk moves), the citation grammar's resolver, and what the drafting-table verbs write |
| lib/office_drop.py | the in-tray: a drop's page, written and read, and its status line's one writer; the in-tray's arrival with the first drop; the unsorted drops office start carries, the desk lists and the Next line reads; the brief office start --drop sends; office status's in-tray line |
| lib/office_sort.py | the return of a sort (0.20.0): a notes.md's Sort, Questions and answers and Handbook sections read (fence-aware) and filed, each fact filed bare and, since 0.38.0, whole when it wraps (`bare_fact`, `list_items`); a sorted drop's move into its folder; the handbook's arrival, its chapters and office status's handbook line; the standalone sort's brief and id |
| lib/office_watches.py | the watches: the query catalog, the register and its log, the check and its fired records |
| lib/office_digest.py | the digest: the sitting-open page, every section computed |
| lib/office_planner.py | a planner sitting from the occupant's words: what it concerns, and what the office gathers for it |
| lib/office_meeting.py | meetings (0.26.0): his words read for when and what, the calendar's plan and record lines, the meetings near now, a prep's gathering and brief, the arising block, the meeting held, a drop tied |
| share/watch-queries.toml | every query a watch can evaluate: the bale surface it reads, the value, how it compares, or the datum bale does not stamp yet |
| templates/ | profile, folder, clipboard series and sheet (retired with the clipboards, 0.26.0), handbook chapter, rolodex card, suggestion slip, notepad page; blueprint and close report; the drafting-table pages (drafting-table-*.md), each made into a page the first time a verb writes it; the folder's two pages, walkthrough.md and delivery.md, which ride with every build session; the in-tray's front page (in-tray-README.md) and the brief office start --drop sends (drop-brief.md); the handbook's front page (handbook-README.md) and chapter (handbook-chapter.md), and the brief office start --sort sends (sort-brief.md); the letterhead's front page, voice page and forbidden list (letterhead-README.md, letterhead-voice.md, letterhead-forbidden.txt); the calendar's two pages (calendar-plan.md, calendar-record.md) and a meeting's prep brief (prep-brief.md); the merge session's brief office start --merge sends (merge-brief.md, 0.40.0); an office ask's brief (ask-brief.md, 0.48.0) |
| migrations/ | one file per breaking release; format in migrations/README.md |
| RELEASES.md | release notes |
| tests/ | the test suite; run.sh (with runner.py) runs it side by side; tests/fakes/ holds the fake bales as modules (0.27.0), each run through a three-line program a test writes in its own tree |

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
the runner writes it, and it goes with the scratch directory. Under its
prefix the interpreter reads that cache alone; in everyday use it reads
the install's own, lib/__pycache__, which install.sh writes (0.30.0).

The suite runs the same in the foreground, in the background and with
`--detach`. A background job started from a non-interactive shell
(`nohup tests/run.sh &`, or a sandbox's background command) inherits
SIGINT ignored, and every process it starts would too; since 0.26.0 the
pty helper the tour's terminal tests drive starts its program with SIGINT
and SIGQUIT at their defaults, as a terminal does, so the interrupt test
checks what Ctrl-C does however the run was started. Until then that test
failed in such a run, and only there (the shell could not trap a signal it
inherited ignored), and the runner warned of it at the start; the warning
is retired with the cause. Since 0.27.0 the pty helper the other terminal
tests drive (`on_a_terminal`, tests/test_start.py) starts its program the
same way.

Since 0.27.0 the suite builds less and starts less, and no test checks
less. A case whose setUp builds a world (an office made by `office
init`, founded, a project added, a folder opened, a fake bale beside
them: `LandCase`, `StartCase`, `AudienceCase`, `HostedCase`, `WatchCase`
and the plain `Office`) builds it once per job, with `kept_setup` in
tests/test_office.py, and every test of the case gets a copy of it at the
same path, with the attributes the setUp set, made before the test and
removed after it, as the Env's directory always was; a world built on an
earlier day is built again. And the fake bales are fixed modules under
tests/fakes/ (`pack_bale`, `land_bale`, `replay_bale`, `small_bales`), not
script texts formatted into every test's tree: the `bale` a test puts on
its PATH is a three-line program that imports one with the test's config,
so the runner's bytecode cache holds the fake's code, and the land fake
hands `--version`, `status` and its packs to the packing fake in its own
process rather than starting the interpreter again; a call that took 84
ms takes 24. The land fake reads the directory each capture was made in
from the capture's own `cwd`, so no test file names a probe's paths, and
`tests/test_suite_clock.py`'s rule reads tests/fakes/ with the tests.

Since 0.28.0 the office's Python helpers start light, and no verb's
output changes. Every `office` command starts several of them (`bin/office
pylib`: `office status` 17, a start about 11, a land about 45), and each
was about 60 ms in a sandbox, three quarters of it importing standard
modules the call never used. Each lib/ module now imports its heavy
standard modules (subprocess, tarfile, tempfile, tomllib, json, shlex,
hashlib, threading, zoneinfo, urllib) and its sibling modules in the
functions that use them; the patterns at a module's top are
`office_helper.LazyPattern`s, compiled the first time one is used;
office_helper and office_bale build only the parser of the subcommand a
call names (`OneSubcommand`; a call that names none, a flag or an unknown
name builds them all, so argparse's usage and errors read as before); and
`pylib` starts Python with `-S`, since lib/ is standard library only. A
small call went from 85 ms to 42 in the worker's sandbox, and the whole
suite from 1,245 seconds to 866. `TestTheHelpersStart` in
tests/test_suite_clock.py holds every module to the rule.

Since 0.29.0 a command starts fewer of them, and still no verb's output
changes. The reads a command made side by side (with no write or
question between them) go out as one `office_helper batch` call, which
runs each subcommand, of office_helper or a sibling module, in one
process exactly as its own call would have run and prints one record
per call; `bin/office` builds the batch with `batch_call` and reads the
records into variables with `batch_run` (each answer in its variable,
its exit code in `VAR_rc`). The two version stamps and the skew report
are one read (`skew-report`), made once per command (`skew_read`); the
fields read back from a helper's JSON line are one `json_read` per
answer instead of one `python3 -c` per field, and the one-liners that
stay single run with `-B -P -S`. `office status` starts one helper where
it started 17, the walk-in three where ten, a plain start on a project
twelve where 23, its landing eleven where 19 and four `python3 -c` where
about twenty (a landing that sorts drops and mints their folders about
29 where 45); in the worker's sandbox `office status` took half a second
where it took 2.3 in everyday use (no bytecode cache, so every call
compiled the module it loaded), and the whole suite 652 seconds where
0.28.0's took 894 on the same sandbox. `TestFewerHelperStarts` in
tests/test_suite_clock.py holds the batch to each call run alone, and
the class of the same name in tests/test_land.py counts what a status, a
walk-in, a start and a land start.

Since 0.30.0 the install carries its own bytecode cache, and a land
starts two helpers fewer. install.sh compiles lib/ into lib/__pycache__
as it installs (above, Install), so in everyday use a helper call reads
its module's compiled code where it compiled it from source: in the
worker's sandbox a small call took 50 ms of CPU where it took 100, an
office_bale call 60 where 210, and `office status` 0.30 seconds where
0.56, a start 1.6 where 2.8 and a land 1.3 where 2.9. `office status`
says whether that cache is level (`office_helper bytecode-check`).
The landing's three helper calls (the office's record out, bale apply
or retry, its outcome) are one, `office_bale land`, which says the
record's line in its place and writes the outcome to a file, since its
stdout is bale's. The suite already ran on the runner's cache, so its
time barely moves. `TestTheInstallsBytecodeCache` and
`TestTheBytecodeLine` in tests/test_office.py hold the cache and the
line; `TestTheLandingInOneCall` and `TestLandWholeInProcess` in
tests/test_land.py hold the landing to its three steps.

Since 0.31.0 the letterhead check on this machine (office deliver's, and
office land's review) runs office_letterhead as a module, as every helper
runs, so it reads the install's compiled code where, run as a script, it
compiled its 540 lines on every check; tests/test_tidy.py holds that, and
the rest of the 0.31.0 tidy.

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
Since 0.27.0 the survey's own reads are steered the same way: the tools it
records, and which bale and office the PATH runs, are looked for only in
the directories `OFFICE_SURVEY_PATH` lists (empty: none, so every tool is
"not found" and none is run for its version), and the container marker is
the file `OFFICE_CONTAINER_MARKER` names (empty: none). Each `Env` and every
job set both empty, so no survey a test runs starts your R, node, bale or
office, or searches a WSL machine's Windows directories on the PATH;
unset, as in everyday use, the survey reads the PATH and `/.dockerenv` as
before. gh (0.42.0) is looked for the same way, in the directories
`OFFICE_GH_PATH` lists, the PATH when it is unset: each `Env` and every job
set it empty, so no test runs your gh, and the tests that want it put the
suite's fake (tests/fakes/gh_fake.py, answering from a state file) in a
directory of their own and name it.
The tests that imitate WSL write a kernel version string of their own
and put fake Windows programs in their own tree. `tests/test_suite_clock.py`
fails the suite on a test file that reads the kernel's version or looks
a program up on the PATH outside `Env`, and on office source that does
either except through those two doors: every program `bin/office` and
`lib/` look up on the PATH is one the runner declares (git, python3, a
shell, the coreutils, iconv), the suite's fake bale, or a desktop program
found through the door.
bale need not be installed, and no real ssh ever runs (the fakes' code is tests/fakes/): the read side's tests put a fake bale first
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
