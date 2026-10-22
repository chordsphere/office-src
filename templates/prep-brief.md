# Brief: the prep for a meeting

`office start --prep` sent this read-only sitting out from the office on
{{day}}, for a meeting the occupant said once, in his words, with
`office meeting`:

- the meeting: {{title}}
- when: {{when}}, {{tz}}{{series}}
- it concerns: {{concerns}}

Its goal is the meeting's words. No folder records it: a meeting is a
view over the work, not a job, and nothing else is opened for it. Work
that arises in it gets its own folder later, through the one door, from
the drops this sitting leaves behind.

## What the sitting is for

Brief him first, short enough to read before the meeting starts: what
landed on what the meeting concerns since the last meeting that
concerned it, what is open on the desk, what waits in the in-tray, and
what he is likely to be asked. Then stay: the same sitting serves before
the meeting and during it, and he may ask you anything then. Answer from
what rides; say when it does not hold the answer.

The windows, one per concern:

{{windows}}

(A first meeting on a project counts what landed in the {{first_window}}
days before it; doctrine section 4, continued.)

## What rides, and why

A sitting's include set is its reads (PLANNER.md section 6). One line
each, in the order to read them:

{{rides}}

## What arose, for after

When something arises in the meeting (a request, a follow-up, a fix
someone asked for), write it down in one arising block, kept to the byte
(doctrine section 4, continued), and keep the block current as the
meeting goes: print it whole again each time it changes. The BEGIN line
names this session's id, as the request's manifest.json gives it
(`session_id`). Each item is a `### ` line in his words (it becomes the
drop's first line), a blank line, a `- project:` line (one of the
office's projects, `the office`, or `none`), and, after a blank line,
whatever else he said about it, verbatim:

```
--- ARISING BEGIN 2026-10-25-weekly-review-prep-001 ---

### Update the report with the new criteria

- project: alpha

The review asked for the new criteria from next week.

--- ARISING END ---
```

A block with no item says nothing arose. When the meeting is over, offer
the block as a file named `arising-SID.md` (SID this session's id), so
he saves it to his downloads and pastes nothing; he can copy the block
instead. Never ask him to retype it, and never give it a title for him
to choose.

## A cleanup, if the documentation needs one

If you find the documentation of what the meeting concerns messy,
disorganized or too wordy while you brief him (a project's README or
docs, or its handbook chapter), you may author one cleanup session for
it: a planner's bundle beside the briefing, as any bundle a sitting
authors, its brief carrying its LANDS line (`--- LANDS alpha, a new
folder ---`). It is offered, never required: say in one line why it is
worth doing, and author none when the documentation is fine. He sends it
from his home screen or deletes it; no separate maintenance session is
needed.

## What the sitting owes

A sitting lands nothing itself (doctrine section 3, principle 2). When
the meeting is over, `office land` ends it: it records the meeting as
held in the calendar and files each item of your arising block as a drop
in the in-tray, tied to this meeting, so the next meeting on these
projects sees the drops, and the folders they become, in its own prep.
The unsorted drops that ride are read, and owe no Sort here.
