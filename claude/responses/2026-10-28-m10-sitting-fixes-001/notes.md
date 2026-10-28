# Notes: 2026-10-28-m10-sitting-fixes-001

office-src 0.33.0: the three sitting fixes from the brief, one release.
All three landed as the brief pinned them; the mechanism calls I made
are below for ratification, and none of them departs from an outcome the
brief pinned. Every changed path is inside the write forecast (the new
test module sits under `tests`), so there is no forecast departure to
admit.

## What I decided, for you to ratify

1. **The review question's words and keys.** After the blank line the
   answer is shown as `  Your answer, as it stands:` with numbered lines,
   then `Keep it? keep, redo, more, or a line's number to type it again
   (FLAG) [keep]: `. Keys: a plain return, `k`/`keep`/`y`/`yes` keep;
   `r`/`redo` asks the question again from its first line; `m`/`more`
   takes lines after the last; a number shows `line N was: ...` and takes
   it again, a blank line taking it out. `more` was not in the brief: it
   is there because the friction's other half is a blank line typed too
   soon, which ends the answer, and without `more` the only fix is redo.
   The flag named is the question's own, read from its prompt's last
   parentheses, so `office open`'s reads `(--title gives a title
   instead)`. That reads a little oddly in the review question; I kept
   it rather than invent a twin the verb does not have.
2. **Taking out every line.** For ask_words (an answer is needed) the
   question is asked again, said; for ask_paragraph it skips the
   question, as a plain return at the first line does.
3. **The editor.** VISUAL, then EDITOR, as git reads them (VISUAL is
   skipped on `TERM=dumb`). "The terminal is his" is stdin and stderr
   both a terminal, not stdout: office start new reads the words inside
   `rel="$(... cmd_open)"`, so stdout is a pipe there, and the editor is
   run with its stdout on stderr's terminal. I found this only by
   reading cmd_start; a `[ -t 1 ]` check would have quietly never used
   the editor on the o key. The scratch file is seeded git's way (an
   empty first line, then the question, its `?` help and a line saying
   what the file takes, all as `#` lines), and read back less the `#`
   lines, **less blank lines** and less trailing spaces. Dropping blank
   lines is a judgment call: an answer typed at the prompt can never hold
   one, and the folder's Asked section, the planner's goal and the
   profile's answers have only ever seen that shape, so I kept it. Say if
   you want paragraphs kept instead. An editor that exits non-zero, or
   comes back empty where an answer is needed, is said and the prompt
   takes over; an empty answer to a profile question skips it.
4. **The probe's choice between a sitting and a project's session.** The
   brief's "keeps today's rule for the project's session, and the
   block's slug or --sid picks between them" I read as: --sid wins; else
   a slug that names exactly one of them; else the one project session
   (today's rule, so nothing a worker's probe did yesterday changes);
   else the one sitting when no project session is open; else asked by
   key (piped: refused, naming --sid). A sitting is read from the
   office's registry only when the folder records a session that is not
   open in the project, so the common worker's probe costs no extra bale
   call. Only read-only sessions in the office's registry count: a
   writing office session is not a sitting (tested).
5. **Where the doctrine stamp goes.** In start()'s result (`doctrine`,
   the install's full hash) for every office sitting, passed to
   `office_helper record-session --doctrine SHA`, which writes the words
   through `sitting_words`, so the writer and the reader
   (`session_doctrine`) live side by side. A second desk on a sitting
   keeps its words first: `a second desk on a session already open;
   sitting, doctrine SHORT`. A read-only project session (`start --on P
   --read-only`) is not stamped: the brief's sittings are the office's.
6. **The brief's line is a template field line**, `- the doctrine it goes
   out under: VALUE`, rather than a sentence with a placeholder in it.
   render_template drops a field line whose value is unset, so when the
   install's OFFICE.md cannot be read the line leaves cleanly, and the
   office says so in a warning; a placeholder mid-sentence would have
   left half a sentence or refused the whole brief. The value carries the
   full sha256, the release, and (for a planner sitting) where the short
   hash is kept and what the walk-in does with it.
7. **The prep is not compared.** No folder records a prep, and the brief
   pins the comparison to the folder, so a prep gets the brief's line and
   nothing on the walk-in. Its calendar record line would be the place to
   stamp it; that is in Proposals, not done.
8. **office status's line is always there**: `doctrine:   OFFICE.md
   SHORT, the install's (office-src VERSION)`, then one indented line per
   read-only sitting open in the office under another doctrine. It asks
   bale which sessions are open only when some folder stamps a doctrine
   that is not the install's, so a status with nothing stale costs no
   bale call. It prints below `skew:`, not beside the install lines where
   I first put it: `TestTheInstallsBytecodeCache` pins the bytecode line
   directly above `built from:`, and that pin is worth keeping.

## Things I found that you should know

- **Every terminal test that types into these questions had to change.**
  The suite's pty harnesses (`on_a_terminal`, `terminal`) write an answer
  when they see a marker and then wait for the child; the new keep
  question waited for an answer they never sent, and `on_a_terminal`
  waits on waitpid with no kill, so the first whole-suite run I started
  hung in the terminal lane. I added a `[keep]: ` step (a plain return)
  to the ten tests that feed ask_words or ask_paragraph:
  test_desk_verbs, test_one_door, test_start, test_third_trip (three),
  test_founding_door and test_planner_from_words (three). Three sitting
  tests that pinned the bare `- SID` Sessions line now pin the stamp.
- **The sandbox's unchanged tree fails three tests**, all in test_office
  and none from this session: `TestDevelopmentRecord`'s two pins read
  claude/context/sittings/, and `TestText.test_names_no_model_and_no_office`
  reads .gitignore; neither rides in the request. They fail identically
  on the base tree and on mine, so they say nothing about this work; on
  your machine they pass. The next request could carry them, or its
  brief could name them as known.
- **`--fast` holds everything named after it to the 120 s budget**, not
  only the tier: test_probe alone runs about 110 s. So validation.sh
  names this session's own tests, and one changed terminal test for each
  kind of question (the p key's words, the profile's answers), by id; the
  eight touched modules run whole only behind `--slow`. With every changed
  test named, the tier took 92 to 103 s here, too near the budget; trimmed,
  it took 79 s. The brief asked for the touched modules after `--fast`;
  doing that literally would fail the budget every time, so this is a
  flagged deviation in mechanism.

## Validation, as it ran here

I rehearsed bale's staging (the request's tree, `files/` over it,
`apply.sh`, the manifest as `.bale-manifest.json`) and ran validation.sh
both ways, and against the unchanged tree:

- Every session assertion passed on the change and failed on the
  unchanged tree (`bash -n` and the exec bit pass on both, as they
  should).
- `tests/run.sh --fast, with this session's tests` failed here **only**
  on the three test_office tests that need files the request does not
  carry (above); every test this session added or changed passed. I
  claim it `pass` as a prediction for your machine, where those files
  are, not as an observation.
- `--slow` (the eight touched modules whole) passed: observed.
- The whole suite here: 1000 tests, the same three failing and nothing
  else, as on the unchanged tree (974 tests then).
- The new tests against the old code: 17 of the 18 that drive no
  terminal fail there, and the one that passes is the piped guard
  (`TestPipedNothingIsAsked`), which holds before and after by design.
  The terminal ones fail too, but the editor test hangs there rather than
  failing, since the old ask_words waits at its prompt and
  `on_a_terminal` never kills (the second Proposal).
- **0.32.0's record pinned VERSION to exactly 0.32.0**
  (tests/test_walkthrough_tidy.py `TestTheRecord`), so any later release
  failed it. It now reads 0.32.0 or later, as test_probe's has since
  0.19.0. The same class still pins its own release's words, which hold.
- **The serial lane holds only terminal tests** (test_third_trip
  `TestTheRunner`), so the piped editor test sits in its own class,
  `TestPipedNothingIsAsked`, beside the terminal one.
- No drop rides in this request (there is no in-tray in it), so no Sort
  is owed.

## Proposals

- **What:** stamp a prep's doctrine in its calendar record line and let
  the walk-in compare it as it compares a folder's sitting.
  **Why:** a prep is a read-only sitting that can stay open through a
  meeting, the same window in which office-src can move; today it gets
  the brief's line and nothing else, because the brief pinned the
  comparison to the folder. **Scope hints:** lib/office_meeting.py
  `mark_prep_out`, `render_record`, `read_record`; lib/office_bale.py
  `in_flight`'s prep branch.
- **What:** give `on_a_terminal` (tests/test_start.py) and `terminal`
  (tests/test_desk_verbs.py) a kill after their read deadline, as
  `run_on_a_pty` in tests/test_front_door.py has.
  **Why:** a question a test does not answer hangs the whole terminal
  lane for ever rather than failing one test; this session hit it, and
  the next change to a prompt will too. **Scope hints:** the two
  helpers only; no test changes.
- **What:** an opt-out for the editor (say `OFFICE_EDITOR=none`, or a
  machine.toml key).
  **Why:** EDITOR is often set for git alone, and someone who likes the
  prompt now gets an editor for every new job. I did not add one
  because the brief said "when set", and it is your call whether the
  prompt or the editor is the default for him. **Scope hints:**
  bin/office `answer_editor`.

## Walkthrough

### What changed

- **An answer of several lines is reviewed before it goes**
  (bin/office): `review_lines` shows the answer numbered and asks keep,
  redo, more or a line's number; `edit_answer` takes it in VISUAL or
  EDITOR instead; `ask_words` and `ask_paragraph` call both, so the home
  screen's p key, office start new, start --planner and the profile's
  questions all get it. The profile's opening line says answers go to
  the founding session "as you keep them".
- **office probe serves a sitting** (lib/office_probe.py `open_sittings`,
  `choose_session`, the plan's `sitting` flag; bin/office cmd_probe's
  line and usage): a read-only sitting the folder records, open in the
  office, is a session a probe of `--project NAME` can be for.
- **The doctrine is stamped and compared**: lib/office_bale.py
  (`install_doctrine_hash`, `doctrine_brief_words`, `session_doctrines`,
  `Doctrines`, `doctrine_lines`, start()'s `doctrine`, In flight's line),
  lib/office_helper.py (`sitting_words`, `session_doctrine`,
  `older_doctrine_words`, record-session `--doctrine`), lib/office_home.py
  (the sitting item), lib/office_planner.py and lib/office_meeting.py
  (the briefs), templates/sitting-brief.md and templates/prep-brief.md
  (the field line), bin/office (record_session, cmd_status's
  `doctrine:` line).
- doctrine/OFFICE.md (section 4 continued, section 7, its Front sheet,
  the verb table, the walk-in and the profile passages), README.md, RELEASES.md 0.33.0, VERSION, the front
  sheet's Recent changes line.
- tests/test_answer_review.py (new), tests/test_probe.py,
  tests/test_planner_from_words.py (26 new tests in all; the suite holds
  1000), the terminal tests and Sessions pins named above, and
  tests/test_walkthrough_tidy.py's version pin.

### Why

The planner sitting of 2026-10-27 hit all three: his answer to the p
key could not be mended once a line was ended (item 4 of the report, the
one he should not have to report twice); its probes of a hosted repo
were refused because a sitting is open in the office, not the project,
so it ran six by hand (item 7); and it learned that office-src moved
under it only because he ran office status (item 13).

### How to explain each piece

- The review: "Before anything is written, you see your whole answer
  numbered. Return keeps it; redo starts again; more adds lines; a
  number retypes that line. Or set EDITOR and write it there."
- The probe: "A sitting can now ask for a probe of a project's repo:
  `office probe FOLDER --project NAME`. It runs there under the
  sitting's id, and everything else about a probe is the same."
- The doctrine: "A sitting's brief and its folder say which doctrine it
  went out under. If office-src changes while the sitting is out, the
  walk-in, the home screen and office status tell you, with both hashes.
  Nothing stops; the sitting can finish."

### Questions a reviewer will ask

- *Does anything piped change?* No. ask_words and ask_paragraph are only
  called on a terminal, the flag twins skip them, and the editor needs
  stdin and stderr to be a terminal (tested with EDITOR set and piped
  input).
- *Why stderr and not stdout for the editor?* office start new reads the
  words inside a command substitution, so stdout is a pipe there.
- *Can a worker's probe now land under a sitting by mistake?* Only when
  its slug or --sid names the sitting; with a project session open, the
  project's session is still the default, as before.
- *Why a short hash in the folder and the full one in the brief?* The
  folder line stays one readable line; the brief is what a sitting reads
  and can check against the doctrine tarball's bytes.
- *What about sittings already out?* Their Sessions line has no stamp,
  so they are not compared, and nothing is said about them.

### A hand test

1. `office`, then `p`. Type two lines, the first with a typo, then a
   blank line. The answer is shown numbered; type `1`, retype the line,
   then return. The sitting goes out with the mended words.
2. `EDITOR=nano office start new`. The editor opens on a file whose
   comment lines hold the question; write two lines, save, quit. The job
   goes out with them and nothing is shown back.
3. With a planner sitting out for folder N, `office probe N --project
   office-src` with a probe block on the clipboard: the header shows, it
   says `for SID (desk/..., the read-only sitting open in the office)`,
   and on `y` the block runs in office-src's repo.
4. `office status`: a `doctrine:` line names OFFICE.md's short hash. In
   that sitting's folder.md, change the twelve characters after
   `doctrine ` on its Sessions line, and walk in: its In flight line
   ends with `out under an older doctrine: ...`, naming both. Put the
   line back.

## Delivery

- to: nobody

### Commit

Serve a sitting better: answers seen whole, a sitting's probe, the doctrine stamped

A multi-line answer (a new job's words, a planner sitting's, a profile
question's) is shown back numbered before anything is written or
packed: keep, redo, more, or a line's number to type that line again.
With VISUAL or EDITOR set, the answer is written in that editor
instead, drawn on stderr's terminal since start new reads the words in
a command substitution.

office probe FOLDER --project NAME runs a read-only sitting's probe in
the project's repo under the sitting's id: a sitting is open in the
office's registry, never the project's. With a project session open
too, the project's session stays the default unless the slug or --sid
names the sitting.

office start stamps the install's doctrine hash (sha256 of
doctrine/OFFICE.md, the bytes the rides-once check reads) in a planner
sitting's and a prep's brief, and as `sitting, doctrine SHORT` in a
sitting's Sessions line; the walk-in, the home screen and office status
say when a sitting is out under an older doctrine, naming both short
hashes. Nothing refuses.

Release 0.33.0, additive.

### Review

Serve a sitting better (0.33.0)

What to look at: bin/office's new asking section (review_lines,
edit_answer and why the editor draws on stderr), lib/office_probe.py's
choose_session (the order --sid, slug, the project's session, the one
sitting), and lib/office_bale.py's Doctrines and doctrine_lines.

What to try by hand: the four steps of the walkthrough's hand test.

Deliberately untouched: bale's pack and open, and a bundle's pack line
(a bundle's sitting gets the Sessions stamp only); the flag twins;
piped input; a prep's walk-in line (no folder records a prep).

## Structure

- title: Serve a sitting better: answers seen whole, a sitting's probe, the doctrine stamped
- size: medium
- goal: Serve a sitting better: a multi-line answer reviewed before it is sent, office probe --project for a read-only sitting's folder, and the doctrine's hash stamped in a sitting's brief and said on the walk-in when it is stale

## Handbook

### office-src

- A terminal test that types into ask_words or ask_paragraph (a new job's words, a planner sitting's, a profile question's) answers the keep question that follows the blank line, a plain return at `[keep]: `; without it on_a_terminal waits on the child for ever, since it never kills it.
- on_a_terminal (tests/test_start.py) looks for each marker anywhere in what the screen has shown so far, so a prompt that repeats (`[keep]: `) needs a marker of its own (the flag before it) or an answer written early, which the pty buffers until read reaches it.
- office start new reads the occupant's words inside `rel="$(... cmd_open)"`: stdout is a pipe there, so anything interactive under cmd_open draws on stderr's terminal.
- `tests/run.sh --fast NAMES` holds the tier and everything named after it to the 120 s budget; test_probe alone runs about 110 s, so a validation names classes or tests, and whole slow modules go behind `--slow`.
- A read-only sitting is open only in the office's own bale registry, never in a project's; office probe finds it there (lib/office_probe.py `open_sittings`).
- A sitting's Sessions line is `- SID: sitting, doctrine SHORT` from 0.33.0 on (lib/office_helper.py `sitting_words`, read by `session_doctrine`); SHORT is the first twelve characters of `office_bale.install_doctrine_hash()`, which is `install_doctrine_sums()["OFFICE.md"]`. A test that pins a sitting's Sessions line pins the stamp.
- A request without claude/context/sittings/ and .gitignore fails three test_office tests on an unchanged tree in a worker's sandbox (TestDevelopmentRecord's two page pins, TestText.test_names_no_model_and_no_office).

#### Front sheet

office-src 0.33.0 serves a planner sitting better. Any answer you type
over several lines (a new job, a planner sitting, a profile question)
is shown back numbered before it goes, so a line can be fixed, more
added, or the whole redone; with EDITOR set you write it in your
editor instead. A sitting can have a project's repo probed with `office
probe FOLDER --project NAME`. And a sitting's brief and folder record
which doctrine it went out under: if office-src changes while it is
out, the walk-in, the home screen and `office status` say so, with
both short hashes, and nothing stops.
