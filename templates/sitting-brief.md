# Brief: a planner sitting from the occupant's words

`office start --planner` sent this read-only sitting out from the office
on {{day}}, recorded in {{folder_words}} ({{folder}}). The occupant said
what he wants a planner for, in his own words below; they are the
sitting's goal, and nothing else was asked of him: no title, no size, no
include list. The office chose what rides from what it knows, and says
why each piece rides, so you can answer him without asking for files.

- the doctrine it goes out under: {{doctrine}}

## His words, verbatim

{{words}}

## What they concern

{{concerns}}

## What rides, and why

A sitting's include set is its reads (PLANNER.md section 6). One line
each, in the order to read them:

{{rides}}

## What the sitting owes

A sitting lands nothing itself (doctrine section 3, principle 2). Its
words reach the notepad in the brief of each session it authors, between
the NOTEPAD PAGE markers; its ratification of a landed session travels as
a RATIFIED line; where each session it authors lands, and the folder
that records it, travels as one LANDS line, so `office start` asks the
occupant neither; and when a session must build on a branch the project's
clone would not otherwise be on (a review's answer, on the pull request's
own branch), that branch travels as one BRANCH line, `--- BRANCH NAME
---`, and `office start` checks it out before bale opens the bundle
(doctrine section 4, continued, pins all four to the byte). When a session
it authors is its own successor, a sitting that takes over from this one,
its brief carries one ENDS line naming this sitting, `--- ENDS SID ---`,
so `office start` ends this sitting once the successor is out and the two
are never open side by side. The unsorted drops that ride are read, and owe
no Sort here. When the sitting is over, `office land` ends it.

The sitting also owes the occupant where it stands. At the end of any turn
where its plan or its place in it changed, it prints its standing block,
after the probe block when the turn ends in one (both in one fence, the
standing last), and he files it on the folder with `office probe`, which
takes it from the same paste, or with the home screen's key (`office
standing FOLDER`); the home screen, the walk-in and `office desk` then show
the step he is on and what waits on him. The block is kept to the byte
(doctrine section 4, continued; values illustrative):

```
--- STANDING BEGIN 2026-10-26-walk-me-through-it-sitting-001 ---
step 2 of 3: find where the work really ran
- [x] probe the office, the install and the host
- [>] find where the work really ran
- [ ] draft the review's words
waiting on you: run the probe below, then paste what came back
--- STANDING END ---
```

Its BEGIN line names this session's id, as the request's manifest.json
gives it (`session_id`); then `step N of M: words`; one `- [x]`, `- [>]`
or `- [ ]` line per step, exactly one `[>]`, the Nth; last `waiting on
you: words`, or `waiting on you: nothing` while the sitting is working.

Every line the sitting hands the occupant to type is an office line (doctrine
section 10): `office start`, `office land`, `office relay`, `office probe`,
never `bale open` and never bale's verbs (bale retry, relay, unlock, handoff:
`office start N --handoff` hands a bailout off),
which are bale's record and reach him through the office. A probe block it
returns carries one more comment line in its purpose header, kept to the byte
(doctrine section 4, continued; values illustrative):

```
# office: probe 21 --project alpha --sid 2026-10-26-walk-me-through-it-sitting-001
```

the folder as `office probe` takes it (its number, a unique part of its
name), the two flags as `office probe`'s own, so bare `office probe` with the
block on the clipboard runs it with no other word typed. A call that spans the
office and a project is `office-on PROJECT COMMAND...`, PROJECT named
literally (never a variable: `office probe` reads it before anything runs,
and refuses a block that does not name it), and a shell line goes as
`office-on PROJECT sh -c 'LINE'`, since one quoted word is one command's
name there. And when a session it
authors carries riders, its brief may name them, one RIDES line per ride,
`--- RIDES PATH ---` (PATH as `office rider add --rides` takes it), or
`--- RIDES none ---` for none, so `office start` carries exactly those, piped
or not.
