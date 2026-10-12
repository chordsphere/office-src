# Notes: 2026-10-08-audience-line-002, the audience line (office-src 0.17.0)

All six of the brief's items are built, as one additive release, from
desk-2 of the session. Every path I changed is inside the forecast, which
is the whole repo. The suite is green here: 657 tests, run side by side,
35 of them in the new module `tests/test_audience_line.py` (three in the
terminal lane). No test makes a network call or runs a real ssh or
docker: a bare repo on this machine stands in for the audience's git
host (the clone's `origin` is its path, so a delivery pushes for real
and the tests read what arrived), and 0.14.0's fake ssh stands for the
host. Eight older test files have small edits, every one named below.

In short:

- `office projects add` and `set` take `--audience`, `--author` and
  `--base` (and `--no-audience`, `--no-author`, `--no-base`), ask the
  three on a terminal after the host question with the clone's facts as
  defaults, and declaring an audience installs the push guard.
- `office letterhead check` names every line the letterhead refuses; the
  list is `share/letterhead.toml`, which the suite's text rules read too.
- `office deliver FOLDER` is the crossing, built and pushed from this
  machine; for a hosted project the landed commits come here as a bundle.
- A build session writes the folder's two pages at the end of its
  notes.md; `office land` files them (`office sessions --pages` when it
  could not).
- `office relay SID ANSWER-FILE` carries a planner's answer to `bale
  relay` where the session is open.

## What the probe established

You pasted the probe back whole (233 lines; the integrity count matched).
Read-only on both machines. What this release stands on:

- **This machine pushes; the host cannot, not without a prompt.** Both
  `~/work` clones answer `git ls-remote origin` (exit 0): the global
  credential helper here is `store`. In the container the helper is
  `cache` (system and global) and it is empty: `ls-remote` fails with
  "could not read Username ... terminal prompts disabled" (exit 128) for
  both clones. So the push path is pinned to this machine, and a push
  from the host is the known gap (below).
- **The identity the audience expects is already the clone's own, on the
  host.** The container's global git identity, and both clones', is the
  occupant's real name and work address; the `~/work` clones here carry
  the machine's name. deliver reads the clone's identity *where the
  clone is* when `author` is unset, so for the work projects the default
  is right without being told; `--author` exists for a clone that gets
  it wrong, as the brief anticipated from the `~/work` copies.
- **The base is `main` on both repos**: `origin/HEAD` points at it in all
  four clones. Both workbench clones sit on feature branches, 4 and 2
  commits ahead of `origin/main`, 0 behind, with no applied session yet,
  no `bale/` branch, no hook in `.git/hooks`, and `core.hooksPath` unset.
  The remote URL shape is `https://HOST/ORG/REPO` (GitHub Enterprise),
  so the compare URL has a known shape.
- **The tools deliver needs are on the host**: git 2.43, python3 3.12 at
  `/usr/bin/python3`, base64 and sha256sum; `TMPDIR` is unset there, so
  the office's temporary directory lands in `/tmp`, as 0.16.0's does.
- **bale's apply keeps a fixed list of response artifacts**
  (`ARCHIVABLE_RESPONSE_ARTIFACTS = README.md, notes.md, next-prompt.md`)
  and checks the tarball's one top-level directory; nothing in the grep
  showed what it does with an extra member such as a `delivery.md` beside
  `notes.md`. I did not build on that uncertainty: the pages travel
  inside notes.md (below).
- Incidentally: bale here is **0.4.52** now, the request was packed by
  0.4.51 and the host runs 0.4.51. Nothing the office reads moved
  between them as far as the help in the request shows; the consumption
  manifest's floor and `checked` stand as they were.

## To ratify (the brief's seven, first)

1. **The key names and defaults.** `audience`, `author`, `base`, on the
   `[projects.NAME]` entry beside the host keys, written as strings.
   - `audience`: a remote's name, checked to be one of the clone's remotes
     at `add` and `set` (through the shell for a hosted project). On a
     terminal the default offered is `origin` when the clone has one,
     else `none`; `none` or a plain return with no origin leaves the
     project without an audience, and deliver refuses it by name.
   - `author`: `Name <email>` as git writes it. Unset (a plain return on
     the terminal, which shows the clone's own identity), deliver reads
     the clone's identity at each delivery, where the clone is. I chose
     "unset means read it then" over "a plain return stores the clone's
     identity" so a clone whose identity is corrected later is followed.
   - `base`: a branch name (checked as git takes one). Unset, the audience
     remote's HEAD branch read from the clone (`refs/remotes/AUDIENCE/HEAD`),
     and deliver refuses by name when the clone has no such symref.
   - `--author` and `--base` without an audience (declared or already
     there) refuse; `--no-audience` clears all three.
2. **The check's list and where it lives.** One file,
   `share/letterhead.toml`, three lists of regular expressions matched
   case-insensitively per line: `names` (models, vendors, products, each
   written with one letter bracketed, `cla[u]de`, so the file never spells
   a name and the tool stays clean under its own rule), `phrasing` (the
   suite's four fingerprints and a dozen more I know an assistant writes
   and a person does not), and `marks` (bale's: `[bale `, `Merge bale `,
   `applied/`, `bale sweep`, `bale/` followed by a date, and a session id
   of the form `YYYY-MM-DD-slug-NNN`). Plus `binary.suffixes`, the names
   never read. `letterhead/forbidden.txt` in the office adds fixed strings
   when it exists; the check never creates it.
   - **Unified and kept apart, as asked.** The suite's `MODEL_NAMES` and
     `FINGERPRINTS` now *are* the file's `names` and `phrasing` (the
     test reads the TOML; the names test became a regex search), so
     office-src's own text is held to the list the letterhead holds work
     to. The suite's `OFFICE_SPECIFIC` list, the brief's hosts, people
     and projects, stays the test's own: its purpose is that office-src
     is project-agnostic, which is no concern of an audience's letterhead
     (the occupant's employer's names belong in work that goes to the
     employer). A new test proves the list never matches its own
     spelling.
   - The phrasing list is a seed and will produce the odd false hit on a
     real project; the answer is the text or the list. `\bllms?\b` and
     "large language model" are in it on purpose.
3. **The push path and the gap.** Pinned: the delivery is built in a
   repo on this machine and pushed from here with this machine's
   credentials. For a project here that repo is the clone itself; for a
   hosted project it is a temporary bare repo under `/tmp`, removed after,
   fed by a thin git bundle of the clone's `HEAD` made in the clone there
   (prerequisite: the merge base of the clone's `AUDIENCE/BASE` and its
   HEAD, so only the landed commits travel) and carried through the
   project's shell, checked by sha256. The audience's base and branch are
   fetched here into `refs/office/audience/...`, never over the clone's
   own remote-tracking refs, and deleted after. A hosted delivery makes
   three connections: the clone's facts, the bundle made, the bundle
   read (its directory removed in the same command); a first delivery
   makes one more only when the guard is not yet installed.
   - **The gap**: a push from the host itself is not built. It would need
     a credential in the container's `cache` (which the occupant would
     type each time the cache expired) or a `store` helper there, and
     the office would then push from the clone through the attended
     shell. Everything else of this release would stay as it is; the
     seam is `office_deliver.plan`'s "the repo the delivery is built in".
   - I did not add a `mirror` declaration (the brief named it as one
     form of "this machine second"). The temporary bare repo fetches the
     audience's base afresh each delivery, which for the work projects
     is small and keeps the floor plan free of a path that is only an
     optimization. If a project's history grows large, `mirror` (a clone
     here that already holds the audience's history, the delivery built
     in it instead) is a small follow-up; see Proposals.
4. **The branch naming.** The folder's directory name with its date
   stripped: `2026-10-08-audience-line` delivers as `audience-line`;
   `--branch NAME` overrides, checked as a branch name. A branch that
   equals the base refuses. A branch already on the audience that the
   folder's History does not record a delivery on refuses, naming
   `--branch`, so a delivery never lands on someone else's branch; one
   the folder did deliver on is continued ("adding to the branch on the
   audience"), the new commit on top of the audience's tip of it.
5. **The one-commit default, and several.** `git merge --squash` of the
   clone's HEAD onto the audience's tip in a temporary worktree, then
   bale's names (`.bale`, `bale.toml`, `.baleignore`, bale's record
   directory, the same list `--prepare` excludes) taken out of the index
   whatever the clone tracks, then one commit with the Commit section's
   subject and body, authored and committed as `author` (both halves,
   over any `GIT_AUTHOR_*` in the environment). Several commits when
   `delivery.md` has several Commit sections: each but the last starts
   with a `paths:` line (comma-separated, relative to the repo's top; a
   directory takes what is under it) and commits those paths from the
   staged squash; the last takes the rest. A section whose paths match
   nothing refuses; the first section without a `paths:` line, or a last
   one with it, refuses before anything travels.
   - The sessions covered are read from the commit subjects in the range
     since the last delivery's recorded workbench commit (when the folder
     has one on that branch and it is an ancestor), else since the merge
     base with the audience's base: each `[bale SID]`, `Merge bale SID`
     or `[bale sweep SID]` subject names its session, and the applied
     ones (the `applied/` tags in the clone) are the delivery's. Sessions
     of other folders are named with their folders (from every folder's
     Sessions section); the occupant is asked on a terminal, and piped,
     deliver refuses naming `--others-too`. The office does not split one
     branch's history by folder, as the brief says.
   - A conflict between the landed work and the audience's base refuses
     with the files and the remedy (bring the base into the workbench
     branch, land that, deliver again); nothing is pushed and nothing is
     left.
6. **The push guard.** A POSIX `pre-push` hook in the clone's
   `.git/hooks`, written by `projects add --audience`, `projects set
   --audience`, and by deliver when it finds none. It exits 0 for any
   remote that is neither the audience's name nor its URL; for the
   audience it refuses, naming `office deliver FOLDER`, unless
   `OFFICE_DELIVERY` names a branch, and then it reads the pushed refs
   from stdin and lets `refs/heads/$OFFICE_DELIVERY` through and nothing
   else. deliver sets the variable on its one push. A clone with
   `core.hooksPath` set, or with another pre-push hook, is said and left
   alone (the office never replaces a hook it did not write). `--prepare`
   itself does not write the guard: at `add` the audience is asked after
   the check and the preparing; the guard goes in once the audience is
   known, so `office projects add --prepare --audience origin` ends with
   it installed, which is what the brief wants of `--prepare`.
   - With the push path on this machine, the guard in the hosted clone
     is pure guard: nothing of the office ever pushes from there. For a
     project here, deliver's push goes through the clone's own hooks and
     the guard lets the delivery branch through.
7. **`delivery.md`'s shape** (`templates/delivery.md`): a title line, a
   `- to: NAME` line before the first section (optional), `## Commit`
   (the subject as the first paragraph, one line, at most 72 characters;
   the body after a blank line; repeated for several commits with
   `paths:` as above), `## Review` (the title, then the body). A build
   session writes it as the `## Delivery` section at the end of its
   notes.md with every heading one level down (`### Commit`), and
   `office land` promotes the headings when it files the page. The same
   for `templates/walkthrough.md` (What changed, Why, How to explain each
   piece, Questions a reviewer will ask, A hand test). Both templates
   ride beside every build session's request as one more context tarball
   from the install (the mechanism the close report's template uses), so
   the worker sees the shape; `templates/folder.md` gains a Walkthrough
   and a Delivery section pointing at the pages. Existing folders are
   not rewritten, and the pages file into them all the same (a test).

## The rest, decided and flagged

- **How the pages reach the folder (item 4's mechanism).** The doctrine
  says the office side is brought up to date by an office step after a
  project session lands, never by the session writing into the office;
  a build session's response lands in the project's repo. So the session
  cannot write `desk/FOLDER/*.md`. The mechanism: the two sections at
  the end of notes.md, which bale already shows at the walkthrough (the
  planner reads the delivery words before anything is filed, a feature),
  and `office land` reads the response tarball on this machine after an
  applied landing of a project session and files them. I preferred this
  to extra members beside notes.md because the probe did not establish
  what bale's apply does with an unknown member. `land_plan` now carries
  `response_here`, the response's path here when the office knows it (a
  path given, the name in the downloads, or the newest copy); when only
  bale's own search knew where it was (a local project, a bare name),
  land says so and names `office sessions FOLDER SID --pages RESPONSE`,
  which files them later and serves a session applied by hand.
- **The letterhead check runs before the question**, not after it as the
  brief's order has it: a delivery the letterhead will refuse is not
  worth asking about. The plan step prints the hits and removes what it
  made; nothing is asked and nothing is pushed.
- **`office deliver` is two Python steps around one shell question.**
  `office_deliver.plan` does everything up to the question and writes a
  plan (the worktree with the squash staged stays on disk between the
  steps); `run` commits, pushes and records; `abandon` removes what plan
  made. bin/office asks (the other folders' sessions, then the push) and
  calls one or the other. A plan that stops on its own (a hit, a refusal)
  removes everything first. A SIGKILLed deliver between the two steps
  leaves a worktree under `/tmp/office-deliver-*` and the office's refs
  in a local clone; the next plan deletes the refs and prunes worktrees.
- **`--on PROJECT`** for a folder whose lane names no project (the brief
  pins "the folder's lane's"; a lane cannot be set after `office open`,
  so a folder without one needed a way). `--on` that disagrees with a
  lane refuses.
- **The review's URL carries the words.** For a GitHub-shaped host
  (github.com, or an instance named `github.*`, which the work host is)
  the URL is `https://HOST/ORG/REPO/compare/BASE...BRANCH?expand=1` with
  `title` and `body` query parameters holding the review's title and
  body, which GitHub's compare page fills its form from; GitLab's shape
  is there too; any other host gets the branch's name and the title to
  paste. On WSL the URL goes on the clipboard, as the opener does.
- **The `delivered` History line**'s text is one line the office reads
  back: `BRANCH on AUDIENCE of PROJECT: sessions S1, S2; workbench
  abc123456789; delivery def123456789` (12-character commits). It is how
  a second delivery knows where the last one left the workbench, so a
  hand edit of the line changes what the next delivery covers; the
  merge-base fallback covers a folder whose line is gone.
- **The build verb's catalog entry**: `lands` gains the two pages and
  `writes` gains `desk/{folder}` (the catalog's rule puts every landing
  inside a write), with a comment saying the session never writes into
  the office and `office land` files the pages; `ships` names the
  templates. The pinned test `test_the_existing_verbs_took_the_keys_as_ruled`
  changed accordingly (build's lands; `deliver` and `relay` join the
  prose set beside `land` and `tour`, since they write outside the office
  and land nothing).
- **The edits to older tests**, each to the new truth and nothing else:
  - `test_land.py`: `response_tarball` takes a `notes` argument
    (additive); the bundle start's tray now holds
    `context-office-src-install.tar.gz`, since a build session from a
    bundle is still a build session and gets the templates.
    `test_start.py`'s tray list, the same.
  - `test_office.py`: the text rules read the letterhead's list (above),
    and the verbs pin takes build's two pages and the three new verbs.
  - `test_front_door.py`: `letterhead-check` joins the two-word verbs the
    help test walks; the init and add wizard scripts answer the audience
    question with a plain return (none).
  - `test_out_trip_to_host.py`, `test_project_on_host.py`,
    `test_read_side.py`, `test_start.py`: the add and set wizard scripts
    answer the new questions (none, or keep). One pinned count changed:
    `office projects add` of a hosted project on a terminal makes two
    connections now, the check and then the clone's remotes and identity
    for the audience line's defaults (the flag form still makes one, or
    two when `--audience` is given and must be checked against the
    remotes).
  - `test_return_trip.py`: its record test pinned `VERSION == "0.16.0"`;
    it now holds VERSION at or above 0.16.0, as 0.14.0's does.
  - `test_second_trip.py` is untouched: it pins that what became of each
    after-land action is the last thing land says, so the pages' lines
    are said as they happen (on stderr) and never join land's last lines.
- **The relay surface**: `share/bale-consumption.toml` declares
  `relay_answer` (`relay SID -`), the stdin form; the reader builds its
  argv from it and runs it through a new `office_host.run_feeding`, which
  gives bale the answer file on stdin here or through the shell (the
  file never travels on its own). The 0.16.0 known problem about the
  hand-typed `bale relay SID -` line is struck in the front sheet. bale's
  output and exit code are passed through; the office adds one line
  naming where it ran, and copies the block between bale's markers on
  WSL.
- **`office letterhead check --on PROJECT`** on a hosted project sends
  `lib/office_letterhead.py` as the program python3 reads from stdin and
  the rules as one JSON argument, so nothing of the office is installed
  on the host and nothing is written there; the module imports nothing
  of the office for that reason (a test holds it). `--words` with a
  hosted `--on` refuses (the words are a file here); check them here.
- **A new `lib/office_deliver.py`** (CODE.md's separate-subject rule: the
  crossing is its own subject, with its own command line), importing
  `office_bale` for the folders' naming and the commit subjects, never
  the other way round. `office_host` gained the clone's git facts, the
  guard, `bundle_to_here` and `run_feeding`; `office_helper` the keys,
  the pages, `parse_delivery`, the `delivered` records and the lane's
  project.
- **One bash lesson, kept out of the tool**: inside `"${var:-text}"` an
  apostrophe in `text` opens a quoted string even within double quotes,
  which ate half a prompt in the wizard; the defaults with apostrophes
  are now assigned first.

## Things to know

- The first real `office deliver` on a work project is its test against
  the real git host; everything here ran against a bare repo and the fake
  ssh. Have the VPN up, and `OFFICE_DEBUG=1` shows every git call and
  connection. The two work clones have no applied session yet, so deliver
  refuses them by name until a session lands there; and both are on
  feature branches with hand commits ahead of `origin/main`, which a
  first delivery would squash together with the first session's work
  into one commit from `main`. If those feature branches are meant to go
  out as they are, push them before the guard is in place (declaring the
  audience installs it), or deliver after they are merged.
- The letterhead check reads the delivery's diff as staged in the
  worktree (a deleted file is skipped; a binary one by name or by a NUL
  byte) and the words. It does not read the workbench's commit messages,
  which are bale's and never travel.
- `tests/run.sh` took 30 to 35 minutes here side by side on two cores
  (the suite grew by 36 tests and the terminal lane by three; your machine
  ran 0.16.0's in 16). `validation.sh --quick` skips it and says so.

## Proposals

- **What**: a push from the host, as the other half of the push path.
  **Why**: the brief named it first; it waits on a credential helper in
  the container that answers without a prompt. **Scope**: `office_deliver
  .plan`'s choice of the repo the delivery is built in, and the push
  through the attended shell; the guard already lets deliver's branch
  through.
- **What**: a `mirror` declaration, a clone here that already holds the
  audience's history, the delivery built in it instead of a temporary
  bare repo. **Why**: a large project would fetch its whole base each
  delivery today. **Scope**: `office_deliver.mirror_here` and the
  projects table.
- **What**: `office deliver --open`, opening the review's URL in the
  browser (`open_command` on WSL). **Why**: the URL is on the clipboard
  today; one less paste. **Scope**: `cmd_deliver`, `start_desktop`.
- **What**: a slip for bale-src: say in `bale apply --help` (or BALE.md)
  what apply does with a member beside notes.md in a response. **Why**:
  the pages could then travel as their own files, which reads better
  than sections in notes.md; the probe could not settle it.

## Claims

- **`tests/run.sh`: pass, observed.** The whole suite ran green here side
  by side (657 tests), twice: on the changed tree, and through this
  response's own `validation.sh` in a staging copy built the way bale
  builds one (the request's tree, then `files/` with `bin/office`'s exec
  bit stripped, then `apply.sh`, the manifest as `.bale-manifest.json`,
  no `.git`), both claims coming back `[agree]`.
- **The session assertions: pass, observed** on the changed tree with
  `validation.sh --quick`; 47 of them fail on the request's unmodified
  tree, the rest hold on both by design (syntax of unchanged files, the
  brief-names guard, the additive check) and say so.
- The script takes as long as the suite, past TARBALL.md's two-minute
  target, as the last three releases' did; `--quick` is the short form.
