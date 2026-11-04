# notes: 2026-11-04-spanning-probe-001 (office-src 0.45.0)

Both defects are fixed as the brief pins them, and the four items shipped
whole. Said first because it is the one thing you will meet that the brief
did not foresee: the existing 0.34.0 tests wrote a shell line as one quoted
word (`office-on alpha 'pwd -P; git rev-parse ...'`) and lived on the
re-split the brief removes, so they now write `sh -c LINE`; a planner
sitting's block written that way does the same (decision 3).

## Decisions

Each one either a call the brief left to me or a reasoned deviation. The
flagged deviations are marked **deviation**.

1. **The call reader is a small scan of the block's shell syntax, not a
   regex.** `calls_of` walks the text once with a stack of contexts (a
   command list, a double-quoted string) and reads quotes, backslashes,
   line continuations, comments, heredocs (`<<WORD`, `<<-WORD`, the
   delimiter quoted or not), `$( )`, backticks, `( )` and `{ }`. A regex
   cannot know whether `office-on` is inside a string or after a `$(` on
   the same line without reading the quotes before it, so the scan was the
   smaller honest thing. It is about ninety lines, and reaches_of keeps
   its signature (bale's `reaches` subcommand and test_three_gaps call it
   as before). `REACH_RE` is gone; nothing outside the module named it.

2. **deviation (small): command position after more than the brief's
   list.** The brief names a line's start, `$(`, a backtick, `|`, `||`,
   `&&`, `;`, `(` and `{`. I also count `&` (one command backgrounded, the
   next begins), the words bash reads a command after (`if`, `then`,
   `elif`, `else`, `while`, `until`, `do`, `!`, `time`), a `NAME=value`
   word before the command (`LC_ALL=C office-on alpha git log`), and a
   case pattern's `)`. Without these, `if office-on alpha test -e x; then`
   is a real call the reader would miss: the block would be planned as
   plain, the helper would not be on its PATH, and the call would fail at
   run time with `command not found`, which is a worse miss than the old
   over-reading. The RELEASES entry lists the whole set.

3. **`\office-on` and `'office-on'` are not calls**, as the sitting leaned:
   a call is the bare name. The reader tracks whether a word had any
   quoting or escaping and only a bare `office-on` counts.

4. **A call whose project is not a bare name names no reach**, as before
   (`office-on "$P" ls`, `office-on $P ls`, `office-on` alone). calls_of
   reports it as `(line, None)` so a later session can refuse it by name
   at plan time; today reaches_of drops it, and the block runs as plain
   and fails at the call with `command not found`. Proposal 1.

5. **run_on's one-word case follows the rule, not the old accident.** With
   shlex.join, `office-on alpha 'pwd -P; git status'` is the name of one
   command and exits 127. I considered keeping a one-word shell-line
   special case for the blocks written since 0.34.0 and decided against
   it: the brief pins "a word with spaces stays one word", a special case
   would make `office-on alpha 'a b'` mean two different things depending
   on whether a second word followed, and the doctrine's words were always
   `office-on PROJECT COMMAND`. The README says to write `sh -c 'LINE'`,
   and the RELEASES entry names the consequence. Flagged because a block a
   sitting wrote at 0.34.0 to 0.44.0 may carry the one-word form.

6. **The existing spanning tests changed with what they pin** (each with a
   comment saying why): tests/test_three_gaps.py `spanning_block` writes
   its two shell lines as `sh -c '...'` and `test_the_helper_as_a_unit`
   calls `office-on alpha sh -c 'exit 5'`; tests/test_probe.py's masked
   spanning call is two words, `office-on alpha echo URL`. The brief's
   "What is there now" says that test's quoted word holds no space; it did
   (`echo URL` is one quoted word), and the brief's reading of
   test_three_gaps missed `spanning_block` altogether, since that module
   is 0.34.0's and the brief looked at test_probe. Nothing else in the
   suite depended on the re-split.

7. **Where the tests live: tests/test_spanning_probe.py**, one class per
   item as asked, plus a third class for item 2's hosted case
   (`TestTheWordsArriveAsGivenOnAHost`), because the hosted fixture is a
   different base class (HostedStartCase) from the local one (ProbeCase)
   and a test cannot inherit both. Its `block_of` helper runs the lines it
   is given, where test_probe's `probe_block` echoes them.

8. **"no command given" is read from the words, not the joined line.**
   run_on refuses when every word is blank (`office-on alpha ""`), where
   before it refused when the joined line stripped to nothing. Same cases
   in practice; said because the line moved.

9. **The doctrine's two sentences sit inside the existing spanning
   paragraph** (section 4 continued, the `A probe may span` paragraph past
   the banner), one after the names are read and one after the call's
   exit code, rather than as a paragraph of their own: each rule lands
   next to the sentence it corrects. The banner is still line 299; the
   module inventory row in README names `calls_of` and the quoting too.

10. **The response was assembled with the request's tools.** I read both
    tools' headers and their help before running them; the manifest's
    skeleton, sizes and hashes are the crafter's, and the feedback block's
    mechanical stream is the lint's emission, pasted over the seeded
    placeholders as TARBALL.md 5.2.2 asks.

## Walkthrough

What changed, in the order you will meet it.

- **office probe on a block that mentions the helper in text.** `echo
  "office-on alpha"` in a probe's body, the name in a heredoc or a comment,
  `./office-on`: the block is a plain one now, run where the folder's lane
  says, and `office_probe.py reaches BLOCK` prints nothing for it. Before,
  it was planned for the office root, `--project` was refused, and a name
  the office does not scope refused the whole block.
- **office probe on a block that calls it.** Every call is read where a
  command begins: a line's start, `&&`, `;`, `|`, `$( )`, a backtick, a
  group, after `if`/`then`/`do`, after `VAR=x`. Same spanning plan as
  before: office root, helper on the PATH, each call where its project
  lives.
- **office-on's words.** `office-on alpha bash -c 'echo one; echo two'`
  prints two lines where alpha lives; `office-on alpha grep -n "a b" FILE`
  greps for `a b`; `office-on alpha echo '$x'` prints `$x`. One quoted
  word is one command's name: a shell line is `sh -c 'LINE'`.
- **On a host.** The quoted line goes into the `bash -c` argv run_in
  already sent through the project's shell; the fake shell's call carries
  the script whole inside that argv, which the hosted test asserts.
- **The record.** VERSION 0.45.0; RELEASES.md's entry first, in the
  releases' voice; the front sheet's line; the doctrine's and README's
  sentences.

Questions a reviewer will ask:

- *Is the reader a shell?* No. It reads enough of bash to tell a call from
  text and says so in its docstring: a command inside `${...}` or behind
  an alias reads as text. It never runs anything; the block still runs
  through bash as before, and the reader only decides where.
- *What does an unterminated quote or heredoc do?* The rest of the text is
  string or body, so no call is read from it; bash would refuse the block
  anyway when it runs.
- *Why does `calls_of` return line numbers?* So a later refusal can name
  the line (`office-on $P` at line 12). Nothing uses them yet but the unit
  tests.
- *Does the office-on helper itself change?* No. ON_HELPER_TEXT still
  execs `on --plan FILE -- "$@"`; the words were always handed over whole
  there, and the loss was run_on's join.

A hand test, about five minutes, with a folder that has a session out on a
project and a block you copy from a sitting:

1. A block whose probe() body has `echo "office-on PROJECT"` and no call:
   `office probe FOLDER block.sh`. The header shows, then "It runs in
   PROJECT's repo" (not the office root), and the echoed line comes back.
2. Add a line `office-on PROJECT bash -c 'git rev-parse HEAD; git status
   --short | wc -l'`: the plan says the block calls office-on for PROJECT
   and runs in the office root; two lines come back from the call.
3. Add `office-on PROJECT git log --format='%h %s' -n 1`: one line, hash
   and subject, the format string arriving whole.
4. Add `office-on PROJECT 'git status'`: exit 127 from the call, bash
   saying `git status: command not found`, which is the new rule showing.

## Delivery words

office-src 0.45.0: the spanning probe's two defects. office probe reads a
block's reaches from its real `office-on` calls alone, the bare name where
a command begins, never from the name in a string, a comment, a heredoc or
an echo's text, so a block that only mentions the helper is a plain block
again. office-on quotes each word on the way to the project's shell, so
`office-on PROJECT bash -c SCRIPT` runs SCRIPT whole where the project
lives, a word with a space stays one word, and a quote or a `$` arrives as
your shell left it; a shell line written as one quoted word is now `sh -c
LINE`. Additive; no migration.

## Structure

- lib/office_probe.py grew `calls_of` and `_command_list` beside
  `reaches_of`, where the reach used to be a regex; `REACH_RE` is gone,
  `ON_NAME_RE`, `COMMAND_WORDS` and `ASSIGNMENT_RE` take its place at the
  top. The module is about a hundred lines longer. If a second reader of
  shell text appears in the office (the standing's steps, say), the scan
  wants a module of its own (lib/office_shellwords.py).
- tests/test_spanning_probe.py is new; it imports ProbeCase from
  test_probe and HostedStartCase from test_out_trip_to_host, as
  test_three_gaps does.
- Nothing was split or moved.

## Handbook

office-src: front sheet

- A spanning probe's reach is a real `office-on PROJECT` call: the bare name where a command begins; its name in a string, a comment, a heredoc or an echo's text names no project.
- office-on hands its words to the project's shell quoted, so `office-on PROJECT bash -c SCRIPT` runs SCRIPT whole and a shell line is written `sh -c 'LINE'`, never as one quoted word.
- lib/office_probe.py `calls_of` is the one reader of a block's shell syntax in the office; it reads quotes, comments, heredocs, `$( )`, backticks and groups, and nothing else.

## Suite

The whole suite, once, on two CPUs: 1299 tests in 758 s (`tests/run.sh`,
the runner's own parallel lanes), OK, no failures. It ran against the tree
with every change in but the last two edits (calls_of's assignment-prefix
case, `x=$(office-on a ls) office-on b ls`, and the three test cases for
it), which landed while it ran; the touched modules ran again after, whole,
through validation.sh --slow on a staged copy: test_probe (58), test_three_gaps
(16), test_standing (29) and the new module (10), OK.

validation.sh ran on a staged copy (the request's tree, files/ over it,
apply.sh run, the manifest beside it): plain, every check passed and the
fast tier with this session's module whole took 80 s of its 120 s (the
tier was 53 s before 0.44.0; the new module is 22 s of it); with
`--slow`, every check passed and the three claims agree with their
verdicts. On the unmodified tree the record's pins, the doctrine's and
README's sentences, the module's units and the new module's run all
fail, as they should (the new module does not exist there), and the
banner check alone passes, since it pins what must not move.

## Proposals

1. **What:** refuse at plan time a call whose project is not a bare name
   (`office-on "$P" ls`, `office-on $P ls`), naming the line. **Why:**
   calls_of already reports such a call as `(line, None)`; today it is
   dropped, the block runs as plain, and the sitting learns of the mistake
   from `command not found` in the block's output, where one line before
   anything runs would say "name each project literally" (the words run_on
   already has). **Scope hints:** lib/office_probe.py read_block or plan,
   on `calls_of`; one test in tests/test_spanning_probe.py.

2. **What:** a check of a sitting's probe block for the one-word shell
   line (`office-on PROJECT 'a; b'`) that names the `sh -c` form. **Why:**
   decision 5's consequence: a block written for 0.34.0 to 0.44.0 may
   carry it, and the only tell today is exit 127 at run time. calls_of
   knows the words after the project; one word holding a space or `;` is
   the shape. **Scope hints:** lib/office_probe.py calls_of (return the
   words too) and a one-line warning in plan; the sitting brief's probe
   words, if the templates say how to write a call.

3. **What:** test_three_gaps's spanning tests move to the module that
   holds the spanning probe's tests now (tests/test_spanning_probe.py).
   **Why:** the spanning probe's tests are in three modules (test_probe's
   masked call, test_three_gaps's 0.34.0 classes, the new module); one
   home reads better and the fast tier could name it whole. **Scope
   hints:** tests only; test_three_gaps keeps its deliver and branch
   classes.
