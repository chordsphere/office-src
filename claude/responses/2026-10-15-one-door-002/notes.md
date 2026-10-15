# Notes: 2026-10-15-one-door-002 (office-src 0.23.0)

Session 2a of the front-door arc. New work now comes in through one door,
`office start new`: your words, the project only when your words name
none, and the folder minted and its session out in one motion. The
fields the office works out from your words are marked provisional on
the folder, and the session that works the job sends back its own in a
`## Structure` section that `office land` files. `office land` asks
nothing about ratification; the planner's next brief carries it and
`office start` files it. A clipboard copy is claimed only once it reads
back. VERSION is 0.23.0, a minor release with no migration.

The pre-flight check said the goal fits, with the split the sitting
already made. I sent no probe and no light block: the brief, the tree and
session 1's notes (archived in the tree at
claude/responses/2026-10-15-home-screen-001/notes.md, so I read them
rather than reconstruct them) answered everything else, and the points I
decided are flagged first below. Every changed path is inside the
forecast. The runtime did not compact this session.

I read tools/craft_response.py and tools/response_lint.py before running
them as far as safety goes: their module docstrings and an audit of every
import and every write. Both import the standard library only, open no
network connection and start no process; the crafter writes only into
the response directory (`--write`), the lint writes nothing.

## Decisions to ratify

1. **`start` is the one verb; `open` is plumbing.** The ruling left the
   name to me. `start` already does the second half of the motion, and
   `office start new` already existed (opening through `office open`'s
   own code), so the door is `office start new`. Its flag twin is new,
   `--words TEXT`, because the doctrine gives every question a flag and
   the door had none: piped, `office start new --words TEXT --on PROJECT`
   (or `--in-office`) goes out and asks nothing; without either it
   refuses before anything is written and names the flags. `office open`
   keeps every flag and behaves as before; `office help` lists `office
   start new` in its place, `office help --all` lists both. The home
   screen's `o` key runs `office start new`, and the Next line's "nothing
   waits on you" names it.
2. **Where start was told the work lands wins over a project your words
   happen to name.** Before, `office start new --on alpha` with words
   naming another project would have written that other project as the
   folder's lane and packed on alpha. And when open's own question asks
   the project and you answer "the office", start now takes that answer
   instead of asking where the work lands again.
3. **The provisional form:** one more field line, `- provisional: title,
   size, goal`, after the goal, naming only fields from that set, in
   that order. Marked: the title, size and goal of a folder opened from
   your words (the goal only when no `--goal` was given, the size only
   when no `--size`), and the title and size of a folder `office start
   --drop` mints. Not marked: the lane (when the office takes it from
   your words, you named the project; when it asks, you chose it), the
   source (where the words came from is a fact, not a judgment) and the
   slug (it is the folder's directory, never renamed). A field a flag set
   is yours, never provisional. `office status` names a provisional line
   that does not read, or one that marks a field the folder lacks.
4. **The returned structure: `## Structure`, three lines, pinned.**
   `- title:`, `- size:`, `- goal:`, in that order and nothing else
   (doctrine section 4, the last bullet of its list; principle 6 tells
   every session to write it beside the Walkthrough and Delivery). Land
   files a value only over a field the folder marks provisional, takes
   it off the provisional line (the line goes when it names nothing),
   and says in one line what became of each key. A field that is not
   provisional, yours or absent, is kept, and an absent one stays
   absent: a long-lived folder such as folder 14, which many sessions
   share, is never handed one session's goal. A section off the shape is
   said and nothing is filed; so is a folder in the filing cabinet. The
   drop brief now asks for the section too.
5. **The ratification form:** one line per session in the brief,
   `--- RATIFIED SID ---`, or `--- RATIFIED SID, except: TEXT ---`, kept
   to the byte like the NOTEPAD PAGE markers, read anywhere in the brief
   except inside a fenced block or inside a notepad page (a sitting's
   page may quote the form). `office start` files each as `- SID ratified
   DATE[, except: TEXT]`, the line `office sessions --ratified` already
   writes, so every reader of it is unchanged; DATE is the office's day
   at the start. **First live use:** the next brief this sitting authors
   (2b's) carries `--- RATIFIED 2026-10-15-one-door-002 ---`, or the
   `, except:` form.
6. **Where the ratification line goes: the end of the Sessions section,
   not under the session's own line.** Doctrine section 15 keeps a
   filed folder to its older rule (it moves whole, and only the office
   command adds lines inside its sections), and the end of the file is
   the History section, whose lines are History's. So the line is added
   as the Sessions section's last line: one line inserted, nothing
   rewritten, which the tests hold to with the byte check the drafting
   table's agenda uses (`insertion_problem`). `office sessions FOLDER
   SID --ratified` still writes under the session's line, as before.
7. **A ratification that cannot be filed is said, never dropped.** A
   session no folder records: said and skipped. A folder that holds the
   session's ratification already (folder 14's "home-screen-001 ratified
   2026-10-15" among them): said and left. A folder an open session's
   forecast holds (the one-writer rule; an office session started on
   that very folder is one): said, with the `office sessions FOLDER SID
   --ratified` line that files it once that session is in. Filing into
   a folder an office session has packed would make its landing refuse
   on base drift.
8. **Land's ratification flags.** `--ratified [--except TEXT]` still
   records one when given, so a script keeps working; `--not-now` is
   taken and changes nothing. An exception no longer keeps a folder
   open: finished means its one session landed applied.
9. **The clipboard, read back.** `to_clipboard` now feeds clip.exe
   UTF-16LE through python3 (no longer only when iconv is there; the raw
   fallback is gone), checks the copy command's own exit, then reads the
   clipboard back with this machine's paste command (machine.toml's
   `paste_command`, or the reader the machine has, which it uses without
   writing it) and compares it with the block, line ends and a BOM aside.
   A copy that reads back otherwise is made once more, in case another
   program copied after it. Only a copy that reads back is "on the
   clipboard ... read back and checked". The other outcomes are one line
   each: not copied off a terminal, not copied for want of a clipboard
   command, "went to the clipboard ..., unconfirmed" when nothing can
   read it back, "NOT on the clipboard as printed" when it reads back
   otherwise. Off a terminal the line goes to stderr, so every piped
   start and land now prints one line more.
10. **The relay is land's last act.** On an applied landing the relay
    goes on the clipboard after the after-land actions, the watches and
    the summary, so nothing land runs can copy over it, and bale's
    earlier copy is always overwritten. When the copy is not confirmed,
    land prints the block again, whole, under it. When nothing landed
    (a HOLD, a clarification, a refusal) nothing runs after, so the
    blocks go where they went before.
11. **Questions.** This session adds none. It removes one, land's
    ratification question. `office start new` asks what `office open`
    asked: the job in your words, and the project only when your words
    name none of the office's.

## What left the clipboard empty

I could not establish it from the code, and I say what I found instead.

- At 0.22.0 the office's claim rested on clip.exe's exit status alone.
  Nothing read the clipboard back, so a copy that clip.exe took and that
  something else then replaced was still announced as there.
- The claim came in the middle of the landing. After it, land ran the
  after-land actions (office-src's are the install and the detached
  suite), the watches and the ratification question, so the occupant
  read "is on the clipboard" well before he pasted. Anything that copied
  in that window, including a terminal that copies a selection, won.
- bale copies the same block itself, earlier, from its global
  `[probe] clipboard_command = "clip.exe"`. If bale's clip.exe call
  returned before Windows had set the clipboard, the two copies raced,
  and bale's mangled one could have been last. I cannot tell from here
  whether bale waits for clip.exe.
- I ruled out the suite: the runner gives each job no desktop program,
  marks the machine as not WSL and puts the suite's fake bale first on
  the PATH of every test that runs one, so neither the office nor bale
  reaches clip.exe from a test.

0.23.0 closes all three: the copy is last, it is read back, and the
claim is made only when it reads back. The hand test below is the check
on his machine.

## Tests

New: tests/test_one_door.py, 15 tests. Seven units (the provisional
field and its status check, the ratification markers kept to the byte,
the ratification line added and nothing rewritten, a folder finished
when its one session landed, the Structure filed over provisional fields
and kept off his words, a Structure off the format). Four piped command
tests (`start new --words` out in one motion; piped refusals before
anything is written; a landing that files the Structure and says nothing
of ratification; a brief's ratification filed in the filing cabinet, a
session nobody records said, a second filing said and left). Four
terminal tests in the serial lane (your words through the door with
nothing else asked; a landing that asks nothing and copies the relay
last, read back; a copy that reads back otherwise, said and printed
again; on an imitated WSL the opener keeps its em dash through clip.exe
and the read-back).

Changed, each for what it now checks: the fake clip.exe can set the
clipboard it reads back (`recording_windows(clip_sets_clipboard=True)`,
test_start; off by default, so the other users are as before); the WSL
start and probe tests read the copy back; the suite's own desktop test
says the copy not made; land's, the home screen's and the hosted
landing's terminal tests no longer answer a ratification question; the
close tests hold the landed-applied rule; the open wizard's field lists
carry the provisional line; the Next line names `office start new`; the
notes reader carries a structure key; the development record lists
0.23.0. No test was dropped; one was renamed
(`test_it_is_not_offered_for_a_second_session`, which no longer tests an
exception).

## Run results (worker's sandbox, two cores)

- The fast tier before (the request's tree, untouched): 66.7 s, 343
  tests.
- The fast tier after: 68.6 s and 66.8 s, 343 tests. tests/fast-tier.toml
  is unchanged (no verb was added), so the tier's time is the sandbox's
  noise.
- The fast tier with tests/test_one_door.py whole, as validation.sh runs
  it: 97.9 s for 358 tests, inside the 120 seconds. The module's
  command tests start and land real (fake-bale) sessions, so it costs
  about 30 s of that.
- The whole suite, `tests/run.sh`, on the bytes this tarball ships: OK,
  840 tests in 1117 s (825 before, and this session's 15).
- validation.sh in a staged copy (the request's tree, `files/` laid over
  it, apply.sh run, the manifest beside it): every check passed, and the
  one claim checked agreed with its verdict. The whole suite is behind
  `--slow`; its run above is on the same bytes (I compared the staged
  copy with the tree the suite ran on, file for file).
- The same validation.sh on the request's tree untouched: all six of
  this session's checks fail there (the fast run among them, since
  test_one_door does not exist yet), so they test the change and not the
  tree.

## Paths outside the forecast

None. Every changed path is under the request's resolved scope.

## Proposals

- **What:** a `--json` key or a flag in bale that turns its own
  clipboard copy off for one command (`bale pack --no-clipboard`, say),
  which the office would pass. **Why:** with the global `clipboard_command`
  set, bale copies every paste block the office then copies again; on
  WSL bale's copy mangles every non-ASCII character, and between the
  two copies the clipboard briefly holds the mangled one. The office now
  copies last, but a planner reading this bale's copy was the probe's
  whole finding. **Scope hints:** bale-src, beside the slip the sitting
  already queued for bale's encoding.
- **What:** `office status` could list the desk folders still marked
  provisional whose recorded sessions have all landed. **Why:** a session
  that writes no Structure (every one before 0.23.0) leaves the
  worked-out title, size and goal standing, and nothing says so but the
  field line. **Scope hints:** lib/office_helper.py `folder_check`, or
  the desk's rendering in lib/office_bale.py.
- **What:** the drop brief and the sort brief could quote the Structure
  form inline, as the drop brief quotes the Sort form. **Why:** a drop
  session reads the doctrine's core, where the form is pinned, but the
  brief is what it reads first. **Scope hints:** templates/drop-brief.md;
  only if sessions are seen to miss it.

## Handbook

### office-src

- office start new is the one door for new work (its flag twin --words TEXT); office open is plumbing, the code start new mints a folder through
- a folder's worked-out fields are named on a `- provisional: title, size, goal` field line (LATE_FIELDS in lib/office_helper.py); office land files a session's `## Structure` over them through lib/office_sort.py file_notes and office_helper.file_structure
- a brief's `--- RATIFIED SID ---` lines are read by office_helper.brief_ratifications (outside fences and notepad pages) and filed by bin/office file_ratifications at start, as the last line of the folder's Sessions section
- to_clipboard reads every copy back with the paste command and returns 0 (read back), 2 (copied, unconfirmed) or 1 (not copied); land copies its relays last, in carry_relays

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.23.0,
new work comes in through one door: `office start new` (the `o` key on
your home screen) takes the job in your own words, asks the project only
when your words do not name one, and sends the session out in the same
motion. The title, size and goal the office worked out are marked
provisional until the session that does the job sends back its own.
`office land` no longer asks whether the planner ratified anything: the
planner's next brief carries that, and `office start` files it. When the
office says something is on your clipboard, it has read it back and it
is. Next in the arc: planner sittings from your words (session 2b),
clean delivery (session 3), and meetings as a view over the work
(session 4).

## Walkthrough

### What changed

- **One door** (bin/office `cmd_start`, `cmd_open`, `usage`,
  `usage_start`, `usage_all`; lib/office_home.py `FIXED_KEYS`;
  lib/office_bale.py `next_move`; share/verbs.toml). `office start new`
  takes your words (or `--words`) and sends the session out; `office
  open` moved to the plumbing.
- **Provisional fields and the Structure** (bin/office `cmd_open`,
  `start_drop`; lib/office_helper.py `provisional_list`,
  `provisional_problems`, `file_structure`; lib/office_sort.py
  `parse_structure`, `file_notes`; templates/drop-brief.md).
- **Ratification out of the landing** (bin/office `cmd_land`,
  `offer_close`, `file_ratifications`, `cmd_sessions`;
  lib/office_helper.py `finished_folder`, `ratify_session`,
  `brief_ratifications`, `cmd_ratifications`).
- **The clipboard** (bin/office `to_clipboard`, `start_desktop`,
  `carry_relays`, `cmd_relay`, `cmd_probe`).
- **The record:** the doctrine (front sheet, principle 6, section 4 and
  its continuation, sections 5, 7 and 10), README, RELEASES 0.23.0,
  VERSION, the development record's front sheet.

### Why

Your words of 2026-10-15: you should not have to keep track of verbs,
titles or sizes; you should describe the job and the session should do
the rest; and the ratification question at the end of a landing is the
wrong time, since you always say yes before the planner has read
anything. And the copy that said it was on your clipboard and was not.

### How to explain each piece

- **One door:** there is one way to start something new. You say what
  the job is, and the office opens its folder and sends the work out.
- **Provisional:** the office fills in the form from your words, writes
  "provisional" on what it guessed, and the person who does the job
  corrects the form when they hand the work back.
- **Ratification:** the planner signs off on the next request it writes,
  and the office files that signature in the right folder by itself.
- **The clipboard:** after it copies, the office looks at the clipboard
  to make sure, and if it cannot, it says so and shows you the text.

### Questions a reviewer will ask

- *Does `office open` still work?* Yes, with every flag; it just is not
  on the short list any more, since `office start new` does what it did
  and sends the session out too.
- *What if a session sends no Structure?* The provisional values stay,
  and the folder still says they are provisional.
- *What if the planner forgets the RATIFIED line?* Nothing breaks: the
  folder is already closed by the landing, and `office sessions FOLDER
  SID --ratified` records it by hand.
- *Why does land print the relay block again?* Only when it could not
  confirm the copy: then the block is right there to copy by hand.

### A hand test

1. After this lands, run `./install.sh` in ~/office-src.
2. In an office on your WSL terminal, type `office`, press `o`, and
   describe a small job in a sentence or two that names one of the
   office's projects; end with a blank line. It should ask nothing else,
   and print the out tray and the opener. Open the new folder's
   folder.md: it carries `- provisional: title, size, goal`, and your
   words under Asked.
3. When that session's response comes back, land it (`l` on the home
   screen, or `office land`). It should ask nothing about ratification.
   It should say what it filed from the session's Structure, close the
   folder if that was its only session, and as its very last line say
   "the block for the planner is on the clipboard (...; read back and
   checked)".
4. The copy check: bale's relay holds an em dash (its first line ends
   "the ratification relay", then an em dash, then "nothing needs
   typing"). Paste the relay into any editor (Notepad will do) and see
   the em dash, not three odd characters. If this relay has none, start
   a job whose words hold one; the opener carries the goal, and paste
   that instead.
5. If you ever see "unconfirmed" or "NOT on the clipboard", copy the
   block from the screen, and tell the next session what the line said.

## Delivery

- to: nobody: office-src has no audience

### Commit

Start new work from his words through one door, and claim only true copies

office start new takes the job in the occupant's words (--words is the
flag twin), names the project only when the words name none, mints the
folder through office open's code and sends the session out in one
motion. office open moves to the plumbing; the home screen's new-job key
and the Next line name start new.

The fields the office works out (title, size and goal) are named on a
provisional field line. Every session writes a Structure section at the
end of its notes.md, and office land files it over the provisional
values, leaving the occupant's words in Asked untouched.

office land asks nothing about ratification, and a folder is finished
when its one session landed applied. A brief carries the planner's
ratification as RATIFIED lines, and office start files each in the
folder that records the session, on the desk or in the filing cabinet.

Every clipboard copy is fed to clip.exe as UTF-16, made after bale's,
read back and claimed only when it matches; land copies its relay last.
Every other outcome is said in one line.

## Structure

- title: message day
- size: high
- goal: Carry the occupant's message of 2026-10-12 through the front-door arc, one session at a time
