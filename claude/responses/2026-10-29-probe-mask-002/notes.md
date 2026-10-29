# notes: 2026-10-29-probe-mask-002

office probe now masks a credential in a URL in everything it hands back:
the screen as the block streams, the result's block (so the clipboard),
and the result's words, which say how many it masked. Two files changed,
both in the forecast: lib/office_probe.py and tests/test_probe.py.
lib/office_host.py and bin/office are untouched; the mask is a writer
office_probe.run hands run_probe, plus a second pass over the text
run_probe keeps.

No probe was needed: the request carries the whole tree, and every claim
in the brief checked out against the code at 0.37.0 (run at the line the
brief names, run_probe's `screen.write(chunk); screen.flush()` loop,
cmd_probe copying the result's `block`). No drop rides, so there is no
Sort section.

## Decisions to ratify

1. **The secret runs to the last `@` of the authority, not the first.**
   The brief's bounds said the secret "stops at `@`". I made it stop at
   the last `@` before the authority ends (whitespace, `/ ? #`, a quote
   or a bracket). For every well-formed URL the two are the same. They
   differ only for a password with a bare `@` in it
   (`postgres://u:p@ss@db/app`): stopping at the first would show `ss`;
   stopping at the last hides it whole, and it is where the host really
   starts (urllib.parse reads a netloc with `rpartition("@")`). The user
   part stops at its first colon and may hold `%40`, as the brief said.
   A URL with no password (`https://user@host`, `ssh://git@host:22/x`),
   a port (`https://host:8443/x@v2`) and `git@github.com:team/repo.git`
   are left alone; tests hold each.
2. **GitHub's own token shapes join the URL form (the worker's call).**
   `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_` and `github_pat_`, each followed
   by at least 30 of `[A-Za-z0-9_]`, standing alone (no word character on
   either side). The prefix is kept: `ghp_xxx`. Why: the commonest way a
   personal access token sits in a remote is `https://TOKEN@github.com/...`,
   with no colon, which the URL form cannot see; this catches it, and a
   bare `GH_TOKEN=ghp_...` too. The URL form runs first, so a token that
   is a URL's password counts once, as the URL's. The 30 is under
   GitHub's real lengths (36 after `ghp_`, 82 after `github_pat_`) so a
   short name that merely starts `ghs_` is left alone. The cost is a long
   snake_case identifier starting `ghs_` or the like being masked, which
   I judged rare in a probe's output and harmless when it happens.
3. **The words.** `; 1 credential in a URL was masked (xxx stands for
   it)`, `; 2 credentials in URLs were masked (xxx stands for each)`,
   `; 1 GitHub token was masked (xxx stands for it)`, and joined with
   `and` when both. Appended to every form of the count's line, the
   "no probe block came back" and "unclosed" forms included, since the
   screen was masked in those runs too. Nothing is said when nothing
   matched, and the run's other log lines are as they were.
4. **The count is over all of the block's stdout, not only the lines
   between the sentinels.** It counts what the mask replaced on the
   screen, which is what the occupant saw; the block is a part of that.
   A credential printed before `PROBE BEGIN` is masked and counted,
   though it is in neither the clipboard nor the History.
5. **The result JSON gains a key, `masked`** (`{"url": N, "token": M}`).
   bin/office reads only the keys it names, so it ignores it; it is
   there for a later reader and for the tests.
6. **The screen shows a line when its line end arrives.** The writer
   holds a partial line back so a credential split between two of
   run_probe's 4096-byte reads is caught; `flush` flushes the real
   screen but never the held part. A last line with no line end is shown
   when the block ends (`close`, in a `finally`, so a run that ends in a
   HostError still shows it). A probe runs with stdin closed and prints
   nothing meant to be read mid-line, so I saw no cost.
7. **Two masks, one source, cross-checked.** run_probe returns the bytes
   it kept unmasked, and lib/office_host.py is out of the forecast, so
   run masks the kept text with the same `mask_text` the screen uses.
   The two read the same bytes decoded two ways (run_probe's `replace`,
   the writer's `surrogateescape`, which hands bytes that are not UTF-8
   to the screen exactly as they came). If their counts ever differ, run
   logs a warning naming both rather than passing over it.
8. **A secret that already reads `xxx` is left and not counted**, so
   masked output run through the mask again says nothing.

## What the mask does not reach (said in the module's docstring)

- **The block's stderr.** run_probe sends it to the terminal as it is;
  the brief left it alone and so did I. A probe that prints a remote URL
  on stderr shows it, uncopied and unkept.
- **The fallback's probe-output/ files**, carried unread, as before.
- **The block's own closing clipboard step.** The crafter's scaffold ends
  by piping its block into `bale clipboard`, inside the block. For a
  block run on this machine (a project here, or the office root) with
  bale's clipboard key set, bale copies the raw block before the office's
  copy. On a terminal the office copies after it and reads the copy back
  (doctrine section 10's clipboard paragraph), so the clipboard ends
  masked, but a clipboard history (Windows' Win+V) may still hold bale's.
  Piped, the office does not copy at all, so bale's raw copy is what the
  clipboard holds. On a host bale is usually not on PATH (the suite's
  fake block says so), which is the case of 2026-10-28. This is the one
  copy that matters that the office cannot reach from office_probe.py;
  see Proposals.
- **A bare token of any other shape** (an AWS key, a GitLab `glpat-`,
  a bearer token in a header) is not caught.

## Outside the write forecast

None. Both paths are the forecast's.

## Places to look closely

- `URL_CREDENTIAL_RE`'s classes (decision 1). The head is
  `\b[A-Za-z][A-Za-z0-9+.-]*://[^\s/?#@:"'<>\`\[\]]*:` and the secret
  `[^\s/?#"'<>\`\[\]]+(?=@)`. Neither can match a newline, which is what
  keeps the line count and the trailer whole.
- `MaskedScreen.write` keeps the held part in a bytearray and looks for
  the line end in the new chunk only, so a long line with no line end
  costs linear time, not quadratic. I timed `mask_text` on 2 MB
  pathological lines (runs of letters, colons, `x://`, an authority with
  no `@`, `p@` repeated): each under 0.2 s.
- `run`'s `finally: masked_screen.close()` and the warning when the two
  counts differ.

## Validation

- The fast tier with this session's four classes (`tests/run.sh --fast
  test_probe.TestTheMask test_probe.TestTheMaskIsSaid
  test_probe.TestTheMaskedRun test_probe.TestTheMaskOnATerminal`):
  passed, observed, 370 tests in 59 s of the 120 s budget.
- The touched modules whole behind `--slow`, observed: test_probe (58
  tests, 14 of them new) and test_three_gaps (16, its spanning-probe
  classes build on test_probe's ProbeCase), 81 tests with their terminal
  share, ok, 100 s.
- The whole suite on the changed tree, observed: 1067 tests, ok, 703 s
  with four jobs.
- The new tests against the unchanged code: all 14 fail or error, as
  they should.
- validation.sh `--slow` rehearsed on a copy of the base made a git work
  tree, with files/ laid over it, apply.sh run and the manifest placed as
  .bale-manifest.json: every check passed, the fast tier in 65 s of its
  120 s, both claims agreed, 3 minutes in all, and it wrote nothing but
  .validation-logs/. The untouched check compared against HEAD there,
  and against the packed bytes on a copy with no git.
- validation.sh on the unchanged base: the incident check fails and the
  fast tier refuses the four classes, which are not there, as they
  should. The untouched-files and text-rule checks pass there by design:
  they are guards on what must not change.

## Proposals

- **What:** a slip for bale-src: `bale clipboard` (or the crafter's probe
  scaffold, before it pipes) masks a credential in a URL the same way,
  `scheme://user:xxx@host`, and says so on its `[bale] clipboard:` line.
  **Why:** the block's own closing step is the one copy of a probe's
  output the office cannot mask from office_probe.py: on this machine,
  with bale's clipboard key set, it puts the raw block on the clipboard
  before the office's copy, and piped it is the only copy. The doctrine
  slip already sent (gaps B3, C3) is the natural place for it.
  **Scope hints:** bale's clipboard verb, or `--probe`'s emitted tail;
  office-src then needs nothing more.
- **What:** mask the block's stderr on the terminal too.
  **Why:** a probe that runs `git fetch` or `git ls-remote` against a
  remote with a credential in it can print the URL on stderr, which today
  goes to the screen as it is. It is not copied or kept, so it is the
  smaller leak, and the brief kept it out.
  **Scope hints:** lib/office_host.py run_probe takes a second writer for
  stderr (it inherits the terminal's today, so it would read a pipe
  beside stdout, in a thread); office_probe.run hands it a MaskedScreen
  over `sys.stderr.buffer`. A serial session, since office_host.py is
  touched by nearly everything.

## Walkthrough

### What changed

- lib/office_probe.py: the mask. `mask_text` replaces the secret of
  every `scheme://user:SECRET@host` with `xxx` (the user kept) and every
  GitHub token in its own shape with its prefix and `xxx`, and counts
  each. `MaskedScreen` is the writer `run` hands `office_host.run_probe`:
  it holds a partial line until its end arrives and writes each whole
  line masked to the real stdout. `run` masks the text run_probe kept
  before it reads the block out of it, puts the counts in the result as
  `masked`, and `count_words` ends the count's line with
  `masked_words`. The module docstring and `mask_text`'s say what the
  mask does not catch.
- tests/test_probe.py: four classes, one per item of the brief:
  TestTheMask (the mask and the writer, a credential split at every
  byte), TestTheMaskedRun (run's screen and block, `office probe` piped,
  a spanning block's `office-on` output, nothing said when nothing
  matched), TestTheMaskIsSaid (the words, and the docstrings),
  TestTheMaskOnATerminal (the clipboard holds the masked block).

### Why

A probe printed `git remote -v` in a project whose remote URL held a
personal access token; the token went to chat, the clipboard and the
probe's record, and was revoked (A11 of the gaps of 2026-10-28). Every
byte the occupant sees or copies of a probe's stdout passes through
office_probe.run, so the mask goes there: the screen through the writer,
the clipboard through the result's block.

### How to explain each piece

- "office probe never shows or copies a password written into a URL: you
  see `https://alice:xxx@host/repo`, so you still know whose it was, and
  the line under the output says how many it hid."
- "It also hides GitHub's own token shapes, `ghp_...` and kin, which is
  how a token usually sits in a remote with no password part at all."
- "It masks a line, it never drops one: the block's count and its
  integrity trailer still match, so the worker can trust the paste."
- "It is a seatbelt, not a promise. A probe should not print a remote URL
  with a credential in the first place, and a token of any other shape
  printed on its own is not caught."

### Questions a reviewer will ask

- Why not change run_probe? It would have been one line there, but
  office_host.py is out of this wave's forecast and every verb uses it.
  run_probe already writes to whatever `screen` it is given and flushes
  after each chunk, so a writer with `write` and `flush` was enough, and
  the kept text is masked in run.
- Can a credential split between two reads reach the screen? No: the
  writer shows only whole lines, and a test splits the output at every
  byte, in two and three pieces, and checks no byte of the secret is on
  the screen at any point.
- Does the History line change? No: `- DATE probe: SID, N lines`, N the
  same count, since a masked line is still one line.
- What about stderr and the block's own `bale clipboard` copy? Not
  masked; see "What the mask does not reach" and Proposals.

### A hand test

1. In a scratch repo on this machine, `git remote add origin
   https://alice:not-a-real-secret@example.com/team/repo.git`, and put
   the repo on a folder's lane with a session out.
2. Write a probe block (read-only header) whose probe() runs `git remote
   -v`, and run `office probe FOLDER block.sh` on a terminal, answering
   `y`.
3. On the screen: `origin  https://alice:xxx@example.com/team/repo.git
   (fetch)` and `(push)`, and the count's line ending `; 2 credentials in
   URLs were masked (xxx stands for each)`.
4. Paste the clipboard into an editor: the same two lines with `xxx`, the
   trailer `--- integrity: N lines ---` matching the lines above it.
5. Open the folder's folder.md: the History line is `- DATE probe: SID, N
   lines`, as before, with no URL in it.
6. Run a block with no URL in its output: the count's line ends as it
   always did, with nothing about masking.

### Release paragraph

office probe masks a credential in a URL. A probe printed `git remote
-v` in a project whose remote URL held a personal access token, and the
token went to the screen, the clipboard and the paste back to chat
(found 2026-10-28; the token was revoked). Now everything `office probe`
hands back is masked: on your terminal as the block streams, in the
block it puts on your clipboard, and in what it says after. A credential
written into a URL, `scheme://user:SECRET@host`, any scheme, comes back
as `scheme://user:xxx@host`, its user kept so you still know whose it
was; a GitHub token in one of its own shapes (`ghp_`, `gho_`, `ghu_`,
`ghs_`, `ghr_`, `github_pat_`), bare or as a URL's user part, comes back
as `ghp_xxx`. When anything was masked, the line after the output says
how many (`4 line(s) came back between PROBE BEGIN and PROBE END, and
the integrity trailer's count matches; 1 credential in a URL was masked
(xxx stands for it)`); when nothing was, nothing is said. A line is
masked, never dropped, so the block's count and its integrity trailer
still match, and the folder's History line is as it was. The mask is a
seatbelt, not a promise: a probe should still never print a remote URL
with a credential in it (`git remote -v`, `git config --get
remote.NAME.url`), a token of any other shape printed bare is not
caught, and the block's stderr, a fallback's probe-output/ files and the
block's own closing `bale clipboard` copy are not masked.
lib/office_probe.py `mask_text`, `masked_words` and the writer
`MaskedScreen`, which `run` hands `office_host.run_probe` as its screen:
it holds a partial line until its end arrives, so a credential split
between two reads is still caught, and writes each line masked; `run`
masks the text run_probe kept the same way before it reads the block out
of it, and puts the counts in its result as `masked`, which
`count_words` says. lib/office_host.py and bin/office are unchanged.
tests/test_probe.py's TestTheMask, TestTheMaskedRun, TestTheMaskIsSaid
and TestTheMaskOnATerminal, 14 tests: the mask's bounds, a credential
split at every byte between reads, the screen and the block of a run,
`office probe` piped and on a terminal with its clipboard, a spanning
block's `office-on` output, and the words.

### Doc lines this change makes stale

For home-screen-offers, each quoted as it stands at 0.37.0, with what it
should now say.

1. README.md, "Run a worker's probe" (line 384): "The output comes back
   to your terminal whole, the block goes on your clipboard to paste
   back, and the folder's History counts the probe." Should add that a
   credential in a URL, and a GitHub token, is masked in both (`xxx`),
   and that the office says how many.
2. README.md, "Running a worker's probe: the details" (line 1171 on):
   "Its stdout and stderr come back to your terminal whole, as they come.
   The lines from `PROBE BEGIN` to `PROBE END` go on your clipboard with
   the office's own `clipboard_command` (on WSL, `clip.exe`), since the
   block's closing `bale clipboard` step runs where no clipboard is; the
   office says how many lines came back between the sentinels and whether
   the integrity trailer's count matches them." Stale twice: stdout now
   comes back masked line by line (a partial line shows when its end
   arrives), and the count's line ends with the masked count. Suggested
   addition after it: "Everything office probe hands back from the
   block's stdout is masked (0.38.0): a credential in a URL,
   `scheme://user:SECRET@host`, comes back as `scheme://user:xxx@host`,
   and a GitHub token in one of its own shapes as `ghp_xxx`, on the
   screen, on the clipboard and in the count's line, which then says how
   many were masked. It is defense in depth, not a promise: a probe should
   not print a remote URL with a credential in it (`git remote -v`, `git
   config --get remote.NAME.url`), a token of another shape printed bare
   is not caught, and stderr, a fallback's files and the block's own
   `bale clipboard` copy are not masked."
3. README.md, the module table (line 1570), lib/office_probe.py's row:
   "... and the fallback's probe-output/ carried to the out tray; since
   0.34.0 a block that spans ...". Should add: "and since 0.38.0 the mask
   over what it hands back (a credential in a URL, a GitHub token)".
4. bin/office `usage_probe` (line 8167 on): "Its output, stdout and
   stderr, comes back whole; the lines from PROBE BEGIN to PROBE END go
   on this machine's clipboard (clipboard_command; on WSL clip.exe),
   since the block's own closing clipboard step runs where no clipboard
   is, and the office says how many lines came back and whether the
   integrity trailer's count matches them." The usage text, as written
   for it: "Its output, stdout and stderr, comes back whole, its stdout
   masked: a credential in a URL (scheme://user:xxx@host, the user kept)
   and a GitHub token (ghp_xxx) are never shown or copied, and the office
   says how many it masked. A probe should still not print a remote URL
   with a credential in it (git remote -v, git config --get
   remote.NAME.url); the mask catches the URL form and GitHub's token
   shapes only, and stderr is shown as it is."
5. doctrine/OFFICE.md section 1 (line 64 on): "and hands the output back
   with the block on the clipboard;" and the verb table's probe row (line
   1295): "hand the output back whole, the block on the clipboard,".
   Both still true, and both silent on the mask; "hand the output back
   whole, masked (a credential in a URL, a GitHub token), the block on
   the clipboard," would say it.
6. claude/context/front-sheet.md: no line goes stale; the 0.38.0 line is
   home-screen-offers' to write, with the VERSION bump.

## Delivery

- to: nobody

### Commit

office probe masks a credential in a URL in what it hands back

Everything office probe hands back from a probe block's stdout is now
masked: the terminal as the block streams, the block it copies to the
clipboard, and the count's line. A credential written into a URL,
scheme://user:SECRET@host, comes back as scheme://user:xxx@host with the
user kept; a GitHub token in one of its own shapes comes back as
ghp_xxx. The count's line says how many were masked, and says nothing
when nothing was. A line is masked, never dropped, so the block's count
and its integrity trailer still match. The screen is masked line by
line by a writer handed to run_probe, which holds a partial line until
its end arrives, so a credential split between two reads is caught. The
block's stderr and a fallback's files are not masked.

### Review

office probe: mask credentials in URLs, and GitHub tokens

What to look at: the two patterns' bounds in lib/office_probe.py (the
secret runs to the last @ of the authority; GitHub's token shapes from 30
characters), the MaskedScreen writer and its held partial line, and run
masking the kept text before it reads the block.

What to try by hand: run a probe whose output is git remote -v in a repo
whose remote URL holds a made-up password, on a terminal; the screen and
the pasted clipboard show xxx, and the line after the output says 2
credentials were masked.

Deliberately untouched: lib/office_host.py and bin/office, the block's
stderr, a fallback's probe-output/ files, and the History line.

## Structure

- title: office probe masks a credential in a URL in what it hands back
- size: small
- goal: Make office probe mask a credential of the form scheme://user:secret@host in everything it hands back, on the screen as the block streams, in the block it keeps and copies, and say how many it masked

## Handbook

### office-src

- office probe's mask lives in lib/office_probe.py alone: `mask_text`
  over the text run_probe keeps, and `MaskedScreen`, the writer `run`
  hands `office_host.run_probe` as its screen. run_probe returns its kept
  stdout unmasked, so anything new that reads that text must mask it too.
- `office_host.run_probe` writes each chunk of stdout with
  `screen.write(chunk)` then `screen.flush()`, 4096 bytes at a time, and
  takes any object with those two methods; the block's stderr is
  inherited and never passes through it.
- The probe result JSON carries `masked`, `{"url": N, "token": M}`;
  `count_words` reads it with `.get`, so a result without it reads as
  nothing masked.
- The mask's secret runs to the last `@` of the authority, as
  urllib.parse finds the host; a URL with no password, or a port, does
  not match.
- The block's own closing `bale clipboard` step copies the raw block
  before the office's copy when the block runs on this machine with
  bale's clipboard key set; piped, the office does not copy, so bale's
  copy is what the clipboard holds.
- The suite's text rule (tests/test_office.py OFFICE_SPECIFIC) refuses
  the names of the occupant's own projects anywhere in office-src's own
  text, the repo of the 2026-10-28 probe incident among them, so a test
  or docstring that tells that incident names no project.
