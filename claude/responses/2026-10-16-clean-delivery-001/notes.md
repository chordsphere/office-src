# Notes: 2026-10-16-clean-delivery-001 (office-src 0.25.0)

Session 3 of the front-door arc, clean delivery. After this lands the
audience line holds by default instead of by your care: an office with a
letterhead refuses the em dash, the en dash and the ellipsis; a
repository's own pull-request template no longer trips the phrasing rule;
the letterhead has a voice page waiting for your words; `office deliver`
shows every commit whole and makes each one as the author you declared,
asking you for it once; `office land` tells you early what deliver would
refuse; the push guard stops tags and bale's refs; and a new project with
an audience is worked from a guarded clone on your machine. VERSION is
0.25.0, a minor release with no migration.

The pre-flight check said the goal fits; the runtime did not compact this
session. I sent no probe and no light block: the brief, the tree, the
doctrine and 2b's archived notes answered everything, and where the brief
left the mechanism to me I decided and list it first below. Every changed
path is inside the forecast. The brief's LANDS and RATIFIED lines are
`office start`'s to file; nothing here touches them.

I checked tools/craft_response.py and tools/response_lint.py before
running them, as 2a and 2b did: their docstrings, every import and every
write. Both import the standard library only, open no network connection
and start no process; the crafter writes only into the response
directory, the lint writes nothing.

## The HOLD, and this re-attempt

The first response was held on one check of my own validation.sh,
"outcome 1, the dashes refused by name with a letterhead". The tool's
code was not at fault: the assertion wrote its scratch tree under
.validation-logs/ inside the staging copy, and bale's staging copy is a
git repo, so the letterhead check read the scratch directory as part of
that repo and checked the staging repo's own changes (bale's telemetry,
the new test file, validation.sh itself) instead of the scratch file,
which the staging repo does not see. My rehearsal staged into a plain
directory, which is why it passed here. The fix is one line: the scratch
tree is a git repo of its own. I reproduced the HOLD in a staging copy
that is a git repo (the old script fails there the same way), and the
corrected script passes there and in a plain copy, every check, the
fast run's claim agreeing (367 tests, about 80 s). Nothing under files/
changed; this response differs from the held one only in validation.sh,
this section, and `corrects`.

## Decisions to ratify

1. **"An office that has a letterhead" is an office with a letterhead/
   directory.** The three characters live in share/letterhead.toml as a
   `[characters]` table (written as escapes, so the file stays ASCII), and
   the check applies them only when it is handed the office's letterhead
   (`--letterhead DIR`, which `office letterhead check`, deliver, land's
   review and `--on PROJECT` all pass). A tree checked outside any office
   is not held to them, and the check says so in a line.
2. **The lift form**, pinned in doctrine section 5: a line `lift: em
   dash` (or `en dash`, `ellipsis`) in letterhead/forbidden.txt, read
   without regard to case or spacing. Every check that reads a lift says
   it; a lift naming anything else stops the check (exit 2) with the file
   and line, so a typo never lifts silently and never refuses silently.
3. **The template exemption is the phrasing rule only, as the brief
   pins.** Names, marks, the forbidden list and the three characters still
   read a template's lines. So a repository whose own template holds an em
   dash would have its delivery refused for that line until the template
   changes or the letterhead lifts the dash. I kept to the brief; if you
   want templates exempt from the characters too, it is one line in
   `hits_in_text`. "As the repository holds it" is the audience's side:
   for a delivery, the commit the delivery starts from (the audience's
   base, or the delivery branch when adding to it); for land's review,
   the clone's `AUDIENCE/BASE` (HEAD when that does not resolve); for the
   check by hand, HEAD. The places are GitHub's, GitLab's and Azure
   DevOps' (`lib/office_letterhead.py`, `PR_TEMPLATE_*`).
4. **The letterhead arrives with the first project given an audience**
   (`office projects add` or `set --audience`), the way the in-tray
   arrives with the first drop: README.md, voice.md and forbidden.txt from
   the install's new templates, each only when missing, the floor plan's
   entry and bale.toml's trigger, committed alone. The brief said the
   install's template carries the voice page but not how an office comes
   by a letterhead; tying it to the first audience is what makes the
   dashes refused "by default" in the office that needs it. It writes no
   words: the voice page's place is an HTML comment marked `EMPTY`, and
   `office status` says "holds no words of the occupant's yet" until a
   session in that office records them.
   - Be aware: the next `office upgrade` (or `office projects set`) in an
     office that already has a project with an audience brings it a
     letterhead, and from then on its deliveries refuse the three
     characters. That is the point of the release, and it is the work
     office's to fill the voice page.
5. **No migration.** A migration makes a release breaking (doctrine
   section 14), so every office, home-office included, would refuse its
   verbs until upgraded, for a page most offices do not have. Instead
   `office upgrade` gained an additive step that runs with or without
   pending migrations: the letterhead's missing pages, and the current
   push guard in every audience clone. With nothing to do it still says
   "nothing to upgrade".
6. **deliver makes the commits before it asks.** "Shows each commit it
   will push, whole" is only true of commits that exist, so plan() now
   commits in its temporary worktree after the check passes, reads each
   commit back (subject, body, author, committer, files with their status,
   and the letterhead's verdict on that commit's message and files) and
   the question shows those. A commit hook in the clone that rewrote a
   message would show here. run() then checks every commit's author and
   committer against the declared author before the push and refuses by
   commit if one differs. The push adds `--no-follow-tags`, so no tag can
   ride along.
7. **The author is asked at deliver, with no default.** It is a fact only
   you know, and the work job showed the clone's identity is the wrong
   default, so the question shows the clone's identity as information and
   takes only what you type. It is kept in the floor plan and committed
   ("office deliver: alpha's author"). `office deliver --author "Name
   <email>"` is the twin and sets the field even when the delivery then
   stops. `office projects add`'s wizard still asks the author, and a
   plain return there now means "deliver asks later" (its prompt says
   so).
8. **Land's review** runs after the pages are filed (so the delivery.md
   words it reads are the ones just landed) and before the after-land
   actions. It reads `applied/SID^1..applied/SID` (the files the landing
   changed, at the tag), skips bale's own names, never reads bale's commit
   messages (they never travel), and checks the folder's delivery.md with
   the template exemption. One summary line, then each line it would
   refuse (up to twelve, then the command that shows them all). A review
   that cannot run is a line; it never fails the landing. For a hosted
   project it runs there through the shell, which is one connection more
   at land, for audience projects only.
9. **Guard version 2.** POSIX sh, as before. The audience is the remote's
   name, or any URL that normalizes to the same repository (scheme, user,
   port, trailing .git and slash aside, lower case), compared against the
   recorded URL and the remote's live `url` and `pushurl`. Without
   `OFFICE_DELIVERY` every ref is refused and listed; with it, only
   `refs/heads/$OFFICE_DELIVERY` passes, and a tag, a deletion, a bale/
   or refs/ name in the variable are refused. The hook carries
   `guard_version=2`; 0.17.0's has none, which is how status tells it.
   `office projects set NAME` with nothing else to set, piped too,
   brings the guard up to date (it used to refuse with "nothing to set").
   A push with `--no-verify` runs no hook; the doctrine says so plainly.
10. **The workbench default.** `--host` with `--audience` at `office
    projects add` records the host as `validates_on` and checks PATH as
    the clone here; `--worked-on-host` keeps today's shape. `--shell`,
    `--connect` or `--from` with a validation host refuse and name
    `--worked-on-host`, since they say how a repo on a host is worked. On
    a terminal the host question still comes before the audience (moving
    it would rewrite every wizard), so a host answered there is taken as
    `--worked-on-host` and the screen says so with the line for the
    default. `office projects set` keeps `--host` as it was and gains
    `--validates-on` and `--no-validates-on`; `--no-audience` clears it
    too. `validates_on` is the fourth of `AUDIENCE_KEYS`, shown by
    `office projects`; nothing uses it until S3.
11. **The letterhead rides** beside every session on a project with an
    audience, in the office's context tarball, and the out tray's line
    says "the letterhead (its voice page first: alpha has an audience)".
    The doctrine's new section-4 bullet tells such a session to read it.

## Tests

New: tests/test_clean_delivery.py, 19 tests. Eleven units (the
characters and their catalog, each refusal's words, lifts, the rules
travelling as JSON, the template places and the exemption, the commits
read back and the identity check, the guard against every push form and
an older guard replaced, the letterhead's arrival and the voice page's
states), seven command tests (the check in an office with a letterhead;
deliver refusing an em dash by name and then pushing with a template
filled and the commit shown whole; status naming a missing voice page and
upgrade adding it; land's review on a project with an audience, with the
letterhead riding beside the start; status naming an older guard and
`projects set` replacing it; add with a validation host; the record), and
one terminal test in the serial lane (deliver asking the author once and
keeping it).

Changed, each to the new truth and nothing else:

- tests/test_audience_line.py: the hosted fixture adds its project with
  `--worked-on-host` (it is the "already on a host" shape); the guard's
  refusal wording; the add wizard's author prompt and the listing's
  author line; `test_the_author_and_base_defaults_come_from_the_clone`
  is now `test_the_author_is_declared_never_the_clones_and_the_base_defaults_from_the_clone`
  (the clone's identity is refused by name piped, and `--author` declares
  and keeps one).
- tests/test_office.py: `projects` joins `ARRIVAL_LANDS` (it writes the
  letterhead when it arrives, and lands the floor plan).

No test was dropped. tests/fast-tier.toml is unchanged (no verb was
added); validation.sh names this session's tests on its own command line.

## Run results (worker's sandbox, two cores)

- The fast tier before (the request's tree, untouched): 57.0 s, 344
  tests, OK.
- The fast tier as validation.sh runs it (this session's units and one
  command test per outcome, beside the tier): 78.6 s for 367 tests, OK,
  in a staged copy built the way bale builds one (the request's tree,
  `files/` laid over it with bin/office's exec bit stripped, apply.sh,
  the manifest as `.bale-manifest.json`); an earlier run with the whole
  new module took 71.6 s for 363. Inside the 120 seconds; the terminal
  test of the author question is left to the whole suite, as 2b did.
- validation.sh in that staged copy: every check passed, the fast run's
  claim agreed with its verdict, and it wrote nothing outside its logs
  (no `__pycache__`). On the request's tree untouched, every one of this
  session's checks fails (the release, the six behaviours, and the fast
  run, since test_clean_delivery does not exist there), so they test the
  change. The whole suite is behind `--slow`.
- The whole suite, `tests/run.sh`, on the staged bytes this tarball
  ships: 886 tests in 19 min 1 s (1,140 s), every test OK but
  test_front_door.TestTourOnATerminal.test_an_interrupt_deletes_the_office_and_says_so,
  the one 2b saw: it fails the same way (the tour still running 30 s
  after Ctrl-C at step 1) only beside the whole suite, and passes alone
  here (8.4 s). Two earlier whole runs on nearly the same bytes said the
  same: 886 tests in 924 s, and one that also caught the doctrine's core
  past its 300-line budget, which I then tightened. The request's tree untouched, in this
  sandbox: 867 tests in 17 min 14 s (1,033 s), that same test the only
  failure. So it is this sandbox's timing, not this session's.
  The manifest claims the whole suite `pass` as a prediction for your
  machine, not as observed here.
- The hand test's steps, below, ran here piped in a scratch home (with
  `--author` and `--yes` in place of the two answers): the letterhead
  arrived, the em dash was refused by name with nothing pushed, the fixed
  words went out as one commit by the declared author and committer, and
  `git push --tags` was refused naming office deliver.
- The sandbox restarted once, late, while the untouched tree's suite was
  running; nothing on disk was lost and the conversation was not
  compacted, so I re-ran that suite.

## Paths outside the forecast

None. The four new files are templates/letterhead-README.md,
templates/letterhead-voice.md, templates/letterhead-forbidden.txt and
tests/test_clean_delivery.py, all inside the forecast.

## Proposals

- **What:** probe a real `office land` once, after this lands, on a
  scratch project with an audience, to see that the review's range
  (`applied/SID^1..applied/SID`) is the session's change as bale tags it.
  **Why:** the suite's fake bale and the audience-line fixture both tag a
  merge whose first parent is the branch before the session, which is
  what 0.17.0's probe found; nothing here re-checked it against bale
  0.4.55. **Scope hints:** lib/office_deliver.py `land_review`; only if
  the hand test's land (or the next real one) says the review could not
  run.
- **What:** decide whether a pull-request template's lines should also be
  exempt from the three characters. **Why:** decision 3; a template that
  carries an em dash would refuse every delivery that fills it. **Scope
  hints:** `hits_in_text` in lib/office_letterhead.py, and the sentence in
  doctrine section 5.
- **What:** give `office letterhead check` a `--template-rev REV` flag.
  **Why:** the module has it (deliver and land pass one); by hand the
  check reads the templates at HEAD, which is the workbench's, not the
  audience's. **Scope hints:** bin/office `cmd_letterhead_check`, one
  flag passed through.

## Handbook

### office-src

- the three characters an office with a letterhead refuses by default are share/letterhead.toml's [characters]; office_letterhead.apply_letterhead applies them (less the forbidden list's `lift:` lines) only when handed the office's letterhead/ (--letterhead DIR)
- a repository's pull-request templates are found by office_letterhead.is_pr_template and read by pr_template_lines at a rev; their lines are exempt from the phrasing rule only, in words, never in files
- office deliver's plan() makes the commits before the question and reads them back (office_deliver.read_commits); run() checks author and committer (check_identities) and pushes with --no-follow-tags
- a project's author is asked by bin/office cmd_deliver when plan exits 4 (office_deliver.NeedsAuthor) and kept through office_deliver.declare_author
- the push guard is version 2 (office_host.GUARD_VERSION, a guard_version=N line in the hook); office_host.guard_state and office_deliver.refresh_guard tell and replace an older one
- office upgrade runs office_deliver.upgrade_additive on every run (bin/office upgrade_additive): the letterhead's missing pages and the current push guards, no migration
- office land runs office_deliver.land_review after land_moves for a project with an audience; it reads applied/SID^1..applied/SID, files only, bale's names never read
- validates_on is the fourth of office_helper.AUDIENCE_KEYS; office projects add --audience with --host records it unless --worked-on-host

#### Front sheet

office-src is the tool that builds and keeps your offices. As of 0.25.0,
delivering work to an audience holds the line on its own: in an office
with a letterhead, em dashes, en dashes and the ellipsis character are
refused by name, a repository's own pull-request template no longer trips
the phrasing rule, and the letterhead has a voice page waiting for your
style rule in your words. `office deliver` shows each commit whole before
it asks, makes every commit as the author you declared (asked once, then
kept), and the push guard stops tags and bale's refs reaching the
audience. `office land` tells you early what deliver would refuse. A new
project with an audience is worked from a guarded clone on your machine.
Next in the arc: meetings as a view over the work (session 4).

## Walkthrough

### What changed

- **The dashes refused by default** (share/letterhead.toml
  `[characters]`; lib/office_letterhead.py `apply_letterhead`, `lifts_in`,
  `char_label`, `hits_in_text`, `render`, `--letterhead`;
  lib/office_deliver.py `office_rules`; bin/office `cmd_letterhead_check`).
- **The pull-request template exempt** (lib/office_letterhead.py
  `is_pr_template`, `pr_template_lines`, `check`'s words and
  `--template-rev`, `--words-json`; lib/office_deliver.py `plan`).
- **The voice page** (templates/letterhead-README.md,
  letterhead-voice.md, letterhead-forbidden.txt; lib/office_deliver.py
  `letterhead_arrive`, `voice_state`, `status_lines`, `upgrade_additive`;
  bin/office `letterhead_arrives`, `upgrade_additive`, `cmd_status`,
  `cmd_upgrade`; lib/office_bale.py, the letterhead riding beside a
  project session; templates/delivery.md).
- **Every commit reviewed, under the declared author**
  (lib/office_deliver.py `plan`, `read_commits`, `check_identities`,
  `run`, `NeedsAuthor`, `declare_author`, `land_review`; bin/office
  `cmd_deliver`, `deliver_show`, `cmd_land`).
- **The push guard** (lib/office_host.py `PUSH_GUARD`, `GUARD_VERSION`,
  `guard_state`, `git_facts`; lib/office_deliver.py `guard_line`,
  `refresh_guard`; bin/office `cmd_projects_set`).
- **The workbench on your machine** (lib/office_helper.py `AUDIENCE_KEYS`
  with `validates_on`, `describe_audience`; bin/office `cmd_projects_add`,
  `cmd_projects_set`, `usage_projects`).
- **The record:** the doctrine (sections 2, 4 and its continuation, 5,
  7, 10 and 14), README, RELEASES 0.25.0, VERSION, share/verbs.toml, the
  development record's front sheet.

### Why

Your words of message 7, 2026-10-15: "i just need the work done adhering
to the letterhead and the git commits should be clean if anyone goes
through them." And what the work job taught: commits went public under
the wrong identity; a clone that pushes to the audience held bale's refs
with no guard; the letterhead refused no em dash; a repository's own
pull-request template tripped the phrasing rule; the style rule lived
only in a chat. Rulings 2 and 3 of the arc: the workbench on your
machine, the host for validation only; the style rule in the letterhead,
as its voice page.

### How to explain each piece

- **The dashes:** the office's style check now catches long dashes and
  the three-dot character by default, and says which one and where.
- **The template:** if a repository gives its own form for review
  requests, the office no longer complains about the form's own wording,
  only about what you write into it.
- **The voice page:** a page in the office where your writing rules live,
  in your words, read by every session that writes for an audience.
- **The commits:** before anything goes out, you see every commit exactly
  as it will be published, under the name and address you gave once.
- **The guard:** the work copy can no longer publish tags or the tool's
  own branches by accident.
- **The workbench:** new projects that others read are worked on your
  machine; a remote host is only where they are checked.

### Questions a reviewer will ask

- *Can I still use an em dash somewhere on purpose?* Yes: `lift: em dash`
  in the letterhead's forbidden list, and every check says the lift.
- *What if the repository's template itself has an em dash?* The delivery
  is refused for that line today (the exemption is the phrasing rule
  only); see the second proposal.
- *Does anything force the guard?* No: a push with `--no-verify` skips
  every git hook. The guard stops slips.
- *Do existing hosted projects change?* No. Only a new project added with
  an audience and a host gets the new shape.
- *Why does deliver now commit before asking?* So what it shows is what
  it pushes; answering n removes the temporary worktree and nothing was
  pushed.

### A hand test

Run these on your WSL terminal, one line at a time, in a scratch office
and a scratch project whose audience is a bare repository on your
machine, so nothing real is pushed. They make no default office and
touch none of yours.

1. After this lands (office land runs `./install.sh` for office-src), run
   `office status` in home-office: its `letterhead:` line says none, and
   that it arrives with the first project given an audience (or, if one
   of its projects already declares an audience, that `office upgrade`
   brings it).
2. The scratch audience and project:
   `H=/tmp/clean-delivery-hand; rm -rf "$H"; mkdir -p "$H"; git init -q --bare "$H/audience.git"; git -C "$H/audience.git" symbolic-ref HEAD refs/heads/main`
   then
   `git init -q -b main "$H/alpha" && cd "$H/alpha" && printf 'hello\n' > README.md && git add README.md && git commit -qm "Initial commit" && git remote add origin "$H/audience.git" && git push -q origin main && git fetch -q origin && git remote set-head origin main`
3. A landing the way bale makes one:
   `git checkout -q -b bale/2026-10-16-alpha-report-001 && printf 'total = 3\n' > report.py && git add report.py && git commit -qm "[bale 2026-10-16-alpha-report-001] Add the report" && git checkout -q main && git merge -q --no-ff -m "Merge bale 2026-10-16-alpha-report-001" bale/2026-10-16-alpha-report-001 && git tag applied/2026-10-16-alpha-report-001`
4. The scratch office and the project, with an audience and no author:
   `office init "$H/office" --no-founding --no-default && cd "$H/office" && office projects add alpha "$H/alpha" --prepare --audience origin --base main`
   It should say the push guard is installed and "the letterhead arrives
   in this office". `office status` ends with a letterhead line ("holds
   no words of the occupant's yet") and "guard: alpha: the push guard,
   version 2".
5. The job and its session:
   `office open "alpha report" --lane "alpha: report.py" --size small && office sessions alpha-report 2026-10-16-alpha-report-001`
6. Words with an em dash:
   `W="$(ls -d desk/*-alpha-report)/delivery.md"; printf '# Delivery: alpha report\n\n- to: a reviewer\n\n## Commit\n\nAdd the report \xe2\x80\x94 its totals\n\nThe report adds its totals.\n\n## Review\n\nThe report\n\nOne file, report.py.\n' > "$W"`
   then `office deliver alpha-report`. It asks once for alpha's author:
   type a made-up one, `Pat Example <pat@example.org>`. It should then
   say "alpha's author is Pat Example <pat@example.org>, kept in the
   floor plan", then refuse with a line naming delivery.md, its line 7,
   and "the em dash (U+2014)", and say nothing was pushed.
7. The same words without it:
   `sed -i 's/ \xe2\x80\x94 its totals/ and its totals/' "$W" && office deliver alpha-report`
   It should not ask the author again. Look at the screen: "commit 1: Add
   the report and its totals", then a line with the commit's short id,
   "author Pat Example <pat@example.org>, committer Pat Example
   <pat@example.org>", "files: A report.py" and "letterhead: clean".
   Answer y. Then
   `git -C "$H/audience.git" log --format='%an <%ae> | %cn <%ce> | %s' alpha-report`
   should print one line with Pat Example twice and the subject.
8. The guard: `cd "$H/alpha" && git push --tags origin`. It should be
   refused, naming the applied/ tag and "only office deliver reaches it";
   `git -C "$H/audience.git" tag` prints nothing.
9. Clean up: `cd ~ && rm -rf /tmp/clean-delivery-hand`.

## Delivery

- to: nobody: office-src has no audience

### Commit

Hold the audience line by default in landing and delivery

In an office with a letterhead, the letterhead check refuses the em
dash, the en dash and the ellipsis character by default, naming each; a
lift: line in the letterhead's forbidden list lifts one, and every check
says so. Lines of a repository's own pull-request template, as the
repository holds them, are not held to the phrasing rule.

A letterhead has a voice page for the occupant's style rule, an empty
marked place from the install's template. The letterhead arrives with the
first project given an audience, office upgrade adds a missing voice
page, and office status names it.

office deliver makes the commits before it asks and shows each whole,
with its author, committer, files and the letterhead's verdict; every
commit carries the declared author, asked once and kept, and is checked
before the push. office land reviews what landed on a project with an
audience and says what deliver would refuse.

The push guard lets nothing reach the audience but the delivery branch:
no tag, no bale branch, no other ref, whatever the push's form. A project
with an audience is worked from a guarded clone on this machine, and a
host given with it is recorded as where it validates.

## Structure

- title: message day
- size: high
- goal: Carry the occupant's message of 2026-10-12 through the front-door arc, one session at a time
