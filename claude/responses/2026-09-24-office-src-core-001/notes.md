# 2026-09-24-office-src-core-001: notes

## Briefing

**How does the doctrine reach a session, given it lives in the install?**
As a context tarball. The probe settled it: bale's include-group triggers
and pulls are repo-relative (BALE.md's board-64 paragraph), so a group
cannot pull a file from the install. `bale pack --context` packs the
current directory's tree and works outside a git work tree. So the
doctrine lives alone in `<install>/doctrine/`, and every pack line the
office prints starts with `(cd <install>/doctrine && bale pack --context)
&& cd <office> && bale pack ...`. That is one physical line producing two
attachments: the request, and `doctrine/.bale/outbox/context-doctrine.tar.gz`.
init tells you where the second one is. This part is unexercised: bale
isn't in my sandbox, so the first real run is the founding line in 1c.
It's clean enough that I didn't file it as a blocker, but a
`--context-from` or output-path flag on bale would remove the `cd` dance
(Proposals).

**The founding sitting is read-only, so how does the profile get written?**
The brief says the profile gets written "in" a read-only founding sitting,
but a read-only session lands nothing. I resolved that in the doctrine
(section 12): the sitting writes the profile with you, then authors one
small session that lands `profile.md`, with your words in its brief. That
matches how bale already works. The alternative is to have init print a
scoped pack (`--write profile.md`) so the sitting lands the profile
itself. That is a one-line change in `founding_line()` if you prefer it.
Please ratify one or the other.

**What happens on an upgrade, and what if it goes wrong?**
`office upgrade` refuses a dirty office. It then clones the office to a
scratch directory and rehearses every pending migration there. Only if
that passes does it run them for real and land one commit, whose body
lists each migration's summary. After every script migration it checks
the filed spaces (notepad, filing cabinet) with `git status`, and a
migration that touched them fails. On the real run that means
`reset --hard` to the pre-upgrade commit, which is safe because the tree
was clean. A renovation migration stops the runner and prints the pack
line; the renovation session bumps `migrated_to` itself when it lands.
That is the one place a session edits the stamp, and it's worth your eye.
All of this is tested through synthetic migrations in a copied install.
No real migration exists.

## Decisions to ratify

- **Install location:** `~/.local/share/office-src`, linked from
  `~/.local/bin/office`. `~/office` was the obvious bale-style name, but
  the seed lives there until 1c, and "is ~/office an office?" would stay
  confusing afterwards. `install.sh` installs HEAD via `git archive`, so
  uncommitted work never reaches offices; it says when it left changes
  out. Upgrading the install is the same one line.
- **Layout:**
  - The office marker is `floor-plan/manifest.toml`.
  - The profile is `profile.md` at the root.
  - The survey is `floor-plan/survey.md`, which is hung.
  - Empty base spaces carry a `.keep` file so git keeps them.
- **Base spaces:** profile, floor-plan, desk, filing-cabinet, notepad,
  suggestion-box, drawer. Handbook, clipboards, calendar, rolodex,
  letterhead, and drafting table arrive by renovation (principle 5).
  The workshop will want a handbook in 1c for office-src's chapter; that
  is its first renovation, or the founding sitting's call.
- **init refuses more than the brief asked:**
  - a non-empty directory (the seed paper moves in after init, in 1c);
  - any path inside a git work tree, since an office is its own repo.
  
  If your home directory is ever a dotfiles repo, the second rule will
  bite.
- **Survey commits on every run,** with the subject "office survey: N
  facts changed". The timestamp changes each run, and `office status`
  reads the survey's age from the page. If the churn bothers you,
  `--no-commit` exists and the default is easy to flip.
- **Offices start on branch `main`,** because your `init.defaultBranch`
  is unset and git would otherwise print a hint. office-src itself is on
  `master`; I didn't touch that.
- **The per-machine default** lives in
  `~/.config/office-src/default-office`. The first init on a machine sets
  it, so the workshop becomes chordsphere's default in 1c. Use `office
  default PATH` to move it.
- **The skew check for capture** is left to 1b. `survey` refuses when the
  office is behind a breaking release, as the brief says. Whether `office
  note` should also refuse then is a real question: capture being
  "instant and dumb" argues for letting it through. See Proposals.

## Watch on review

- **Timezone.** chordsphere's WSL clock is `Etc/UTC`, per the probe. init
  stamps the machine zone into the floor plan and hints it in the
  profile's Site section, so the workshop will say UTC unless the
  founding sitting corrects it. Nothing reads that key yet; the calendar
  will.
- **The doctrine's wording.** It carries the bale/office line verbatim, as
  the brief asks, and a test pins its words with whitespace folded.
  Everything office-bound is ASCII and free of the style.md list; tests
  enforce that too. They also enforce that no shipped file names a model
  or anything about the job or its hosts.
- **`claims`:** shellcheck is claimed `untested`. It isn't in Ubuntu
  24.04's default install or in my sandbox, so validation will `[SKIP]`
  it unless you have it. To predict it, I'd need to have run it once.

## What the probe established

It ran on chordsphere, paste-back, 1165 lines, complete.

- **Machine:** Ubuntu 24.04.2 under WSL2, bash 5.2.21, Python 3.12.3
  (tomllib is present), git 2.43.0 with identity set and
  `init.defaultBranch` unset. R is on PATH, quarto is not, and node
  v24.19.0 comes from nvm. `timeout` and `flock` are present.
  `~/.local/bin` is on PATH and no `office` command exists yet. The
  timezone is Etc/UTC.
- **bale:** 0.4.45, linked to `~/bale/bin/bale`. `~/bale` has
  `install.sh`, `upgrade.sh`, `validate.sh`, and a user-owned `user/`,
  which is the model for this install. The `bale pack --context` flag
  surface is as the doctrine uses it. Include groups: one per project,
  flat `[pack]` keys, repo-relative triggers and pulls, and a missing
  pull refuses the pack.
- **The seed:** read in full from `~/office` in place of the context
  tarball that didn't arrive. Its generic design went into the doctrine;
  the job-specific parts stay for the work profile in 1d. I didn't reuse
  the cron probe's awk.
- **office-src:** two commits, and an untracked `claude/` directory that
  isn't mine and that this response doesn't touch.

The probe had a defect, and it was mine. Its include-group grep excluded
`.git` but not `.bale/`, so it walked bale's logs and the staging tree of
an open session, `board-122-rehearsal-verbs-009`. That is the recursive
grep your seed slip on probe scope warns against. It read nothing
sensitive and wrote nothing, but it was noise, and the doc text I relied
on came from that staging copy of BALE.md rather than the repo root. I
assumed they agree.

## Front sheet material for office-src's handbook chapter (lands in 1c)

- **What it does:** builds and keeps offices. `office init` makes one:
  the folders, a profile to fill in, a first survey of the machine, and
  a first commit. It then prints the line that starts the founding
  sitting. `office status` says whether an office is founded and whether
  it matches the installed tool. `office survey` refreshes the page of
  machine facts. `office upgrade` brings an office up to a new release as
  one commit.
- **Who uses it:** the occupant, on every machine that has an office.
- **Where and when it runs:** installed per machine at
  `~/.local/share/office-src` and run as `office`. It runs only when
  called; it schedules nothing and never runs a session.
- **Recent changes:** 0.1.0, the first release. Doctrine, templates,
  profile shape, init, survey, status, upgrade, and install. No
  migrations yet.
- **Known problems:**
  - The everyday verbs (note, open, desk, week, close, reopen) aren't
    built yet.
  - The doctrine's ride-along context pack hasn't been run for real.
  - Offices on WSL pick up the machine's UTC zone.
- **Questions likely to come up, with answers:**
  - *Does upgrading office-src change my offices?* Their tools, yes,
    at once. Their files, only through `office upgrade`, and only for
    breaking releases.
  - *Can an upgrade rewrite my notes?* No. Filed paper is checked after
    every migration, and a migration that touched it fails.
  - *Why does it refuse my office?* Either the office is behind a
    breaking release (run `office upgrade`), or it was migrated by a
    newer office-src than this machine has (install the newer one).
- **Public documentation:** office-src's README and
  `doctrine/OFFICE.md`. The chapter should point at them rather than
  restate them.

## Proposals

**1b: record session ids in folders from `bale pack --json`.**
*What:* when a verb prints a pack line for a folder, have it also offer
the `--json` form, and after the pack record the id into the folder's
Sessions list. *Why:* the folder template has a Sessions section, and
the doctrine promises "without asking anyone"; nothing does it yet.
*Scope hints:* `bin/office`, `templates/folder.md`; this needs the
`--json` report shape from bale 0.4.40 or later.

**1b: decide whether capture ignores version skew.** *What:* let `office
note` append to the notepad even when the office is behind a breaking
release, and only warn. *Why:* the brief says capture must work in an
unfounded office, and the same logic argues it should work in a stale
one. Right now there is `require_current()` and no lenient mode. *Scope
hints:* `require_current()` in `bin/office`.

**1b or 1c: an include group for hung items.** *What:* have init write
an office `bale.toml` with a `[pack]` include group whose pulls are the
hung items, so every pack from the office carries them. *Why:* it
removes `--include` lists from every printed line. I didn't do it
because I couldn't verify whether a trigger of `.` (the whole office)
is legal, and a wrong guess makes every pack refuse. *Scope hints:* a
probe of `tests/test_include_group.py` in `~/bale-src` settles it.

**1c: the founding sitting sets the office timezone.** *What:* the
founding sitting writes the real zone into both Site and the floor
plan's `[office] timezone`. *Why:* chordsphere reports Etc/UTC, and the
calendar will read that key. *Scope hints:* `floor-plan/manifest.toml`
in the workshop.

**1d: check the container before the first init there.** *What:* the
work office's session should probe for:

- git identity inside the rstudio container;
- whether the home directory is inside a git work tree, which init
  refuses;
- Python 3.11 or later, for tomllib.

*Why:* those are the three things `office init` refuses on, and the
seed's facts about that host are from before this sitting. bale 0.4.40
there has `--context` (0.4.39 or later), so the doctrine pack should
work.

**bale-src: let a context pack name its source and destination.**
*What:* a `bale pack --context` form that takes a directory argument and
an output path, or a way for the request pack to take an extra context
directory. *Why:* a tool that ships its own global doc beside bale's (the
doctrine here) must `cd` into its install and leave a `.bale/outbox`
there. Include groups can't help, because they're repo-relative by
design. *Scope hints:* `bin/bale_pack.py`'s `--context` path.

**bale-src: the probe scaffold's tree example should prune `.bale/`.**
*What:* add `.bale` to the prune list the crafter's `--probe` skeleton
shows, and to any recursive-grep example. *Why:* this session's probe
walked another session's staging tree and logs by following the
scaffold's pattern (which excludes caches and `.git`) too literally.
*Scope hints:* `PROBE_SCAFFOLD` in `tools/craft_response.py`.
