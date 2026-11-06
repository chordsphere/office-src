# Brief: the undo session for {{folder}}, "{{title}}"

This is an undo session on {{project}}, and nothing else. `office deliver`
takes what bale's own commits changed out of every delivery, since that is
bale's housekeeping and never the work, and it never leaves. It could not
take out bale's own commit {{commit}} ({{subject}}): the workbench's later
work touches the same lines in the files below, and the commit did more
there than add lines, so the office will not guess which lines are bale's.
It left the clone clean, pushed nothing, and sent this session: the
occupant is never sent into the clone to undo it.

## The commit and the files

- bale's own commit: {{commit}} ({{subject}}), whose parent is {{parent}}.
- The workbench, as it is packed here: {{project}}'s tree in this request,
  at {{workbench}}.

The files where its change cannot be taken out:

{{files}}

{{earlier}}

## The materials

The folder rides in the office's context, and in it {{materials}} holds
everything the undo knows that the tree here does not:

- before/: each file above as it was before bale's commit, at its path (a
  file bale's commit created has no copy here).
- bale/: each file as bale's commit left it, at its path; bale/ holds
  every file the commit changed, so you can see all of what it did.
- workbench/: each file above as the workbench holds it now, at its path
  (the same as the tree here).
- bale.diff: the commit's own change to the files above.
- undo.md: the office's page for this job, the files on its `- file:`
  lines; read it, never write it.

## What to do

For each file above, read bale.diff and the three versions, and write the
file as the workbench's work needs it with bale's change taken out: every
line the work wrote, kept; every line bale's commit wrote or changed, as
it was before it, unless the work since has made that line its own; and
nothing else. Where you cannot tell a line of bale's from a line of the
work's, keep the work's and say so in notes.md, or end the turn with a
light question block.

The response ships each file whose result differs from the workbench's,
and nothing else: no other file (bale's change to the files not listed
comes out in the delivery as it always does), no refactor, no fix you
noticed on the way (propose those in notes.md). A file that should not
exist with bale's change taken out is a deleted change. A file you leave
out keeps the workbench's version, and the next delivery takes it so:
leave one out only when the workbench's version already holds nothing of
bale's commit. Run the project's tests where the tree here lets you.

When the response lands, its commit on the workbench is the undo, the
work's own, and `office land` closes the job: the folder's History gains
an `undone` line naming the commit, the files and this session, and the
materials leave the folder. The next `office deliver` takes each file
above as the workbench then holds it when it takes bale's commit out, and
delivers the folder's own work alone.

## What every session owes

At the end of notes.md, as the doctrine's section 4 says: the Questions
and answers of any light block you sent, and a Handbook section for any
fact about {{project}} you learned that a later session should not have to
rediscover, written bare. An undo session writes no Walkthrough, Delivery
or Structure section: the folder's walkthrough and delivery words are the
work's, an undo changes nothing the audience reads but bale's own lines,
and the folder's title, size and goal stand. Write instead a `## Undo`
section: for each file, one line on what was bale's and what stayed. The
Sort owed to any drop that rides beside this session is owed here too.
