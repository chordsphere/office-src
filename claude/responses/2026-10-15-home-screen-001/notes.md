# Notes: 2026-10-15-home-screen-001 (office-src 0.22.0)

The first session of the front-door arc. On a terminal, `office` is now
your home screen. `office help` lists only your own verbs. The wizards
stop asking you for what a session can work out. Bare `office start`
offers the planner's bundles in your downloads that no session opened.
Off a terminal nothing changed: the walk-in prints its page and ends
with its Next line, and every verb takes the same flags and, piped,
behaves as before. VERSION is 0.22.0, a minor release with no migration.

The pre-flight check said the goal fits. I sent no probe and no light
block: the brief and the tree answered everything but one point, which I
decided and flag first below. Every changed path is inside the forecast.

The runtime compacted this session once, near the end, while I was
assembling the tarball (the code, tests and these notes were done). I
re-grounded from the durable side before shipping: the request
manifest, AGENT.md section 11.6, TARBALL.md section 5.2, the tree's
diff against the base and the files on disk. Every size and hash in
manifest.json was recomputed from `files/`, the mirror was compared
byte for byte with the tree, and validation.sh was run again in a
staged copy (the base with `files/` laid over it and apply.sh run),
the whole suite with it; the results are under Run results.

## Decisions to ratify

1. **Bundles come from your downloads only, not from bale's search
   paths.** The brief says bare `office start` offers the bundles "in the
   downloads (and bale's apply search paths)". bale's `status --json`
   gives only a count of search directories, and doctrine section 10
   rules that the office never reads bale's config ("a slip for
   bale-src"). So the office looks only in machine.toml's `downloads`.
   On your machine the two are most likely the same directory. If they
   are not, `office start --bundle FILE` still opens a bundle anywhere,
   and the bale-src slip stands. The doctrine (section 4, continued) and
   the front sheet's Known problems say so.
2. **"Opened" is read, and read narrowly.** A session's dossier names the
   bundle it was opened from (`attempts[].bundle.stem`). Reading every
   dossier in every repo on each walk-in would cost a bale call per
   session. bale mints a session's id from the slug in the bundle's pack
   line, so the office reads only the dossiers whose id carries that
   slug, usually none or one. A browser's `NAME (1)` copy counts as the
   same bundle. A re-cut with the same slug (`...-v2`) is not counted as
   opened by its predecessor's session: the stems differ.
3. **Only bundles saved in the last 14 days are offered.** Without a
   window, every withdrawn bundle (the two meeting-spaces bundles, this
   session's own first cut) would wait on your home screen forever.
   Fourteen is my guess. Deleting the file from the downloads also
   removes it.
4. **Your verbs:** the home screen, `note`, `drop`, `slip`, `open`,
   `start`, `land`, `desk`, `close`, `deliver`, `projects add`, `tour`
   and `init`. `deliver` is there because it is the one way work reaches
   an audience, and it asks you once. `slip` is there because friction is
   yours to capture. `probe` and `relay` are plumbing: you run them, but
   only when a session hands you the line, in full. share/verbs.toml
   carries the list (`surface = "occupant"` or `"plumbing"`), the catalog
   check requires one on every built script verb, and the doctrine's
   verbs table has a surface column. The close/reopen row is split in
   two, since close is yours and reopen is plumbing.
5. **The flag is `office help --all`.** It prints what `office help`
   printed before, with a new opening line. `office --help` is the short
   list.
6. **The home screen's keys.** Digits are for what waits, up to nine; the
   rest are counted and point to the desk. Letters are always there: `o`
   a new job, `s` start, `l` land (only when a session is out), `n` a
   note, `d` a drop, `k` the whole desk, `h` help, `q` leave. A plain
   return at "Your key:" leaves too, so a stray return runs nothing. The
   next move is listed first and marked `(next)`. After a key's command
   ends, a key brings the screen back, worked out again.
7. **The next move is always on the list.** The brief lists what waits:
   responses, bundles, drops, desk moves, an office out of step. The
   page's Next line can also name a ready folder, the founding, or a
   project to add. Those show as the first item, in the Next line's own
   words, so the home screen never hides what the page would tell you to
   type.
8. **Two items beyond the brief's list.** A read-only sitting a folder
   records gets "End the sitting ..., once it is over", so you never type
   its id to end it; it is never the next move (doctrine section 7). And
   one line under the projects gives the desk's counts ("On the desk: 1
   in flight, 1 ready"), since the projects alone don't say what is open.
9. **A response file shown is an offer.** "A response for it was saved
   just now in your downloads" leads to `office land SID`, which asks
   bale. For a session bale held, the item says "again: bale held it"
   whenever any copy of its response is in the downloads, even the held
   one. I did not try to judge which copy is the corrected one: land
   lists every copy by key, newest first, and you pick.
10. **The wizards: what goes, what stays.** The full list is the next
    section. In short: open, start and drop-start no longer ask for
    structure; land no longer asks whether to close a finished folder
    (on a terminal it closes it and says how to reopen it; piped it
    still leaves it open); slip no longer asks what it is about; the
    clipboard command is taken when the machine has one.
11. **His words become the goal, joined.** `office open` keeps your words
    verbatim in the Asked section. The goal is the same words on one
    line: a line that ends without a stop is joined to the next with a
    semicolon, so "Fix the login" / "It fails on phones." becomes "Fix
    the login; It fails on phones." Session 2 will let a session send
    back a better goal. A leading dash or list marker is taken off the
    goal, since bale reads a goal that starts with a dash as a flag.
12. **A taken name gets `-2`, not a question.** Before, a title already
    used today asked for another title. Now the folder gets the next free
    name and the log says so. The one exception stays: `office start new`
    still asks whether to start the folder of that name already on the
    desk, since only you know if it is the same job.
13. **`office start new` with a bundle asks nothing.** The new folder's
    words are the bundle's goal, its source `bundle NAME`, and it is
    marked in the Asked section as the planner's words. Its lane is
    where the bundle opens.
14. **A bug fixed on the way.** `ask` kept the answer in a local named
    `answer`, and `office relay` called `ask answer ...`. The answer was
    set on `ask`'s own local and lost. Every local in `ask` and `pick`
    is now prefixed. This matters for a terminal relay given no answer
    file; no test covered it.
15. **The doctrine's text.** Section 7 has the home screen (walking in),
    the wizard rule, and the two surfaces. Section 4 continued has the
    bundle offer and why bale's search paths are not read. Section 5's
    drop paragraph and land's closing rule changed with the code. The
    front sheet has the home screen.

## The wizard audit: every question, kept or removed

The rule: the occupant supplies words, the session supplies structure.
A question stays only when it asks for the ask in his words, which
project when the office cannot tell, yes or no on what cannot be
undone, or what only his eyes can check. Every flag twin stays and sets
its field as given; piped input is never asked anything, as before.

**Removed** (the value the office now supplies, said in a log line):

- `office open`, the title: from his words (their first line, trimmed as
  a drop's heading is); the slug from the title.
- `office open`, the size: small.
- `office open`, the lane as "project: paths": the project comes from his
  words when they name exactly one of the office's projects; the paths
  are never asked (a session's forecast).
- `office open`, the source: where the words came from (`the occupant`,
  `bundle NAME`, `drop`).
- `office open`, "give another title" after a name clash: a free name.
- `office open --filed` with no `--sid`, the session id: refused naming
  `--sid` (it is a session's flag).
- `office start`, where the work lands: from a bundle's own paths, else
  the folder's lane, else the office when it scopes no project. Asked by
  key only when none of these tells.
- `office start`, the goal when the folder has one (his words from open,
  or a sort's): taken.
- `office start`, the paths the session will change: the lane's, else the
  whole repo.
- `office start`, which ride-alongs go: all, as declared.
- `office start`, carry each rider the forecast touches: carried.
- `office start new` for a bundle: the folder's words are the bundle's
  goal.
- `office start --drop`, the size: small.
- `office land`, close a finished folder: closed on a terminal, said,
  with the reopen line.
- `office slip`, what it is about: left for the session that reads the
  box.
- The clipboard command (`paste_command`), when the office finds the
  machine's reader: taken, kept, said.

**Kept**, and why:

- `office open`: the job, in his words (the ask). Which project, by key,
  only when his words name none and the office scopes some.
- `office open` for `office start new`: "already on the desk: start it?"
  Only he knows if it is the same job.
- `office open`: class, blueprint and gates, asked again only when the
  flag he gave does not read: a correction of his own value.
- `office start`: the bundle to start, by key, skippable. Which job, by
  key (only he knows). The goal in his words when the folder has none.
- `office start --drop`: the project, by key, only when the drop names
  none of the office's.
- `office land`: which session, by key (only he knows which response he
  has). The corrected response after a HOLD, by key from the copies in
  the downloads (only his eyes know which he saved). Did the planner
  ratify (only he knows what the planner said). The return before the
  next relay block goes on the clipboard: a pause, not a judgment.
- `office drop`: the project, by key or in any words, only when the
  office scopes one; a return skips.
- `office slip`: the words, when none were given.
- `office note` from the home screen: the line, his words.
- `office init`, `office found`: the path, the office's name (default
  offered), the projects it watches, the profile's questions, the
  timezone. All his.
- Downloads (`downloads`), asked once per machine: where his browser
  saves, which a machine cannot say (there are often two candidates).
- `office close`, `reopen`, `sessions`, `deliver`, `probe`: the folder,
  by key. `office sessions --ratified`: the session, by key.
- `office probe`: where it runs, by key, only when the lane names no
  project; which session, by key, only when the block's slug names
  none; "Run it?" (it runs a script on his machine).
- `office relay`: the session, by key. The answer file: kept, since the
  planner's file has no name the office can know. This is the one place
  he may still type a file's path (or a bare name found in the
  downloads); it is plumbing, and a session names the line.
- `office deliver`: other folders' sessions too? Push? Both cannot be
  undone. Session 3 owns the audience line.
- `office projects add` and `set`: the repo's path, its host, the shell
  and connect line, its name (default offered), the audience, author
  and base, what rides and what runs after it lands, prepare the clone,
  bring a dirty clone, and each "keep ...?". These are facts about his
  repos and machines and consent to write in his clone. Session 3 may
  revisit the audience keys. "Which project" for `set` and
  `level-bale` is now by key; level-bale's "do it?" stays (it installs
  on a host).
- `office blueprint open` (title, charter), `ratify` (the blueprint and
  the notepad page, now by key), `close` (by key); `office rider add`
  (title, source, carrier, text), `carry` (the rider's number),
  `consumed` (number, session); `office agenda add` (text, source):
  plumbing for sittings. A sitting writes these lines in full; a
  question only meets someone who typed the verb bare.
- `office tour`: play in the tour office? Navigation.

## Room left for session 2

The provisional fields are plain field lines (`size: small`, the lane,
`source`, `goal`) and the words are in the Asked section, so a session
that sends back a real title, size and goal needs only a filing step
like `office land`'s other ones (`helper folder-set-field` writes a late
field today). Nothing in this session builds that step.

## Tests

New: tests/test_home_screen.py, 14 tests: 9 units, 2 for the page and
the bundles as the command runs them, and 3 terminal tests in the
serial lane (the home screen landing a response by its key and coming
back; bare start offering a bundle by key and, once opened, never
again; land after a HOLD offering the response's copies by key). The fake bales learned two facts: the land fake's dossier
carries the stem of the bundle a session was opened from, and the pack
fake's status names the latest session applied.

Changed because the questions changed (each named for what it now
checks): the open wizard (test_desk_verbs, test_third_trip), start on a
terminal (test_start, test_third_trip, test_second_trip), drop start
(test_drop), land's several sessions (test_land) and closing
(test_return_trip), the slip (test_start), the paste command
(test_probe), help (test_office, test_front_door, test_audience_line,
test_probe, test_watches_digest), and the doctrine's words
(test_desk_verbs). `on_a_terminal` takes `None` for a marker that is only
waited for. No test was dropped.

## Run results (worker's sandbox, two cores)

- The fast tier before: 69.9 s and 72.5 s, 343 tests.
- The fast tier after: 62.8 s and 64.8 s, 343 tests. The release adds
  nothing to the tier (tests/fast-tier.toml is unchanged, as its header
  asks), so nothing is added to its time; the difference is the
  sandbox's noise.
- The fast tier with test_home_screen, as validation.sh runs it: 73.4 s
  for 356 tests, and 77.0 s for 357 once the held-response test was in.
- The whole suite, `tests/run.sh --detach`: OK, 824 tests passed in
  1054 s. After it I made two small changes: a leading dash is taken off
  the goal made from your words (decision 11), and one terminal test
  was added (land after a HOLD, offering the response by key). I ran
  test_home_screen whole (14 tests) and the open wizard's terminal tests
  again after them, all passing. The suite now has 825 tests.
- `validation.sh --slow` in a staged copy (the base, `files/` laid over
  it, apply.sh run, the manifest beside it), on the bytes this tarball
  ships: every check passed, the whole suite with its 825 tests among
  them (about 17 minutes there), and every claim agreed with its verdict.
- The same validation.sh against the unmodified base (with the test
  runner stubbed out): all seven of this session's assertions fail
  there, so they test the change and not the tree.

## Paths outside the forecast

None. Every changed path is under the request's resolved scope.

## Proposals

- **What:** a --json surface in bale that lists `apply.search_paths`.
  **Why:** the brief asked for bundles in bale's search paths, and the
  office cannot see them without reading bale's config. **Scope hints:**
  bale-src; the slip already exists.
- **What:** a timeout on `on_a_terminal`'s final `waitpid`, like
  `run_on_a_pty` has. **Why:** a terminal test whose command waits for an
  answer it never gets hangs the whole job until the runner's own limit;
  it cost me two five-minute stalls this session. **Scope hints:**
  tests/test_start.py.
- **What:** the home screen could offer "Close folder N, its job looks
  done" for an open folder whose one session landed and was ratified
  but was left open. **Why:** today such a folder only shows as the
  Next move "start it, or close it". **Scope hints:** lib/office_home.py
  `home_items`, `helper finished-folder`.

## Handbook

### office-src

- on a terminal, `office` is the home screen (lib/office_home.py writes it and its menu); off one it is the walk-in page with its Next line
- whether a bundle was opened is read from the dossier's attempts[].bundle.stem, only for sessions whose id carries the bundle's slug
- share/verbs.toml's surface key (occupant or plumbing) is required on every built script verb; office help lists the occupant's, office help --all every verb
- ask and pick prefix every local (__a_, __p_), since printf -v into a caller's variable is swallowed by a local of the same name

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.22.0,
typing `office` at a terminal opens your home screen: your projects one
line each, then what waits on you, each with a key that does it. You no
longer type session ids or file names, and the questions the office asks
are only the ones only you can answer: what the job is in your words,
which project when it cannot tell, and yes or no on what cannot be
undone. `office help` lists your own verbs; the rest is plumbing that
sessions name for you. Next in the arc: new work and planner sittings
from your words (session 2), clean delivery (session 3), and meetings
as a view over the work (session 4).

## Walkthrough

### What changed

- **The home screen** (lib/office_home.py, new; bin/office `walk_in`,
  `walk_in_head`, `home_screen`, `read_key`). On a terminal, `office`
  prints the office's head lines, each project's line, the desk in one
  line, what waits with a key each, and the fixed keys. A key runs
  `office VERB ...` as its own command; then the screen comes back. Off a
  terminal, the page is as before.
- **The bundle offer** (bin/office `offer_bundles`; lib/office_home.py
  `waiting_bundles`; lib/office_bale.py `bundle_stems`). Bare `office
  start` lists unopened bundles from the downloads, newest first, by key.
- **What last landed** (lib/office_bale.py `applied_latest`; two status
  keys and two dossier keys declared in share/bale-consumption.toml).
- **Two surfaces** (share/verbs.toml `surface`; lib/office_helper.py's
  catalog check; bin/office `usage`, `usage_all`, `cmd_help --all`; the
  doctrine's verbs table).
- **The wizards** (bin/office `cmd_open`, `ask_words`, `cmd_start`,
  `ask_where`, `ask_start_folder`, `offer_riders`, `start_drop`,
  `cmd_land`, `offer_close`, `cmd_slip`, `cmd_drop`, `paste_setting`,
  `ask_folder`, `pick`; lib/office_helper.py `record_asked`).
- **The record:** README (front door, your verbs and the plumbing, walk
  in, capture, open, start, land), RELEASES 0.22.0, doctrine sections 4,
  5 and 7 and its front sheet, the front sheet, VERSION.

### Why

Your words on 2026-10-15: you should not have to keep track of verbs,
options, long commands, file names and session ids; you should walk in,
see your projects and what is open, and act. And the size question was
"a microcosm of the whole issue": the office was asking you for
judgments a session should make. This session makes `office` the door,
names everything the way you know it, and removes those questions, so
the next three sessions can build on a front door that asks only for
your words.

### How to explain each piece

- **The home screen** is the office's front desk: it tells you what is
  going on in each project and hands you a numbered list of what is
  waiting for you. Press the number, and it does that thing.
- **The bundle offer**: when a planner gives you a bundle and your
  browser saves it, `office start` (or the home screen) now notices it
  and offers it. Once a session has gone out from it, bale remembers,
  and the office stops offering it.
- **Two surfaces**: `office help` is the short card in your wallet; `office
  help --all` is the full manual the sessions use.
- **The wizards**: the office used to ask you to fill in a form (title,
  size, lane, source). Now it asks you what the job is, and fills in the
  form itself, marking it as provisional until a session knows better.

### Questions a reviewer will ask

- *Do my scripts still work?* Yes. Every flag is as it was, and piped
  input is never asked anything. `office` piped still prints the page
  and its Next line.
- *What if a response in my downloads is the old, held one?* The office
  only offers it. `office land` asks bale, and after a HOLD it lists every
  copy of the response by key, newest first.
- *Why doesn't it see bundles in bale's search paths?* bale does not say
  where they are on any surface the office may read. See the first
  decision above.
- *Why did `office open` stop asking the size?* A session judges the size
  better than you can before the work starts. It is written as small for
  now; session 2 lets a session send back the real one.
- *Can I still close a folder by hand, or keep one open?* Yes: `office
  close` (now with a key per folder), and `office land --leave-open`.

### A hand test

1. After this lands, run `./install.sh` in ~/office-src.
2. Walk into each of your offices on a terminal: `cd` into it and type
   `office`. The first time, it asks where your downloads land; answer
   once. Read the Projects lines: each project should say what is in
   flight on it, or what last landed and when. Read "Waiting on you"
   and check it against what you know is waiting.
3. Choose one thing by its key (a drop to send out, a bundle to start,
   or `k` for the whole desk). It should run without asking you for an
   id or a file name. When it ends, press return: the home screen comes
   back. Press `q` to leave.
4. Run `office help`. It should list only your commands, one line each,
   with a line on what a folder and a project are. Run `office help
   --all` and check that the plumbing is all there.
5. Off the terminal, run `office | tail -1`. It should print the Next
   line, as before.

## Delivery

- to: nobody: office-src has no audience

### Commit

Make office on a terminal a home screen, and ask only what only you know

On a terminal, office now shows each project the office scopes on one
line (what is in flight on it, or what last landed and when), the desk
in one line, and what waits, each with a key that runs the verb's own
code with its arguments filled in: a response in the downloads for a
session that is out, a planner's bundle no session has opened, each
unsorted drop, the desk moves, an office out of step with the install.
Sessions are named by their folders and files are found in the
downloads, so no id or file name is typed. Off a terminal, office prints
the page and its Next line as before.

Bare office start offers the bundles in the downloads that no session
has opened, read from bale's records by the bundle's stem.

office help lists the occupant's verbs, one line each; office help --all
lists every verb. share/verbs.toml and the doctrine's verbs table say
which verb is on which surface.

The wizards ask only for the ask in the occupant's words, the project
when the office cannot tell, yes or no on what cannot be undone, and what
only he can check. office open takes the job in his words and keeps them
in the folder's Asked section; the title, slug, goal, size and source are
worked out. office start takes where the work lands, the goal, the
forecast, the ride-alongs and the riders from what the office knows.
Choices are offered by key. Every flag still sets its field.

### Review

None: office-src has no audience, so there is no review request and
nobody to send one to.
