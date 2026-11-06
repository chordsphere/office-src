# Brief: the merge session for {{folder}}, "{{title}}"

This is a merge session on {{project}}, and nothing else. `office deliver`
tried to bring {{side}} into the workbench, the branch in {{project}}'s
clone where sessions land, so that the folder's work could leave as one
delivery; {{side}} is {{where}}. The merge conflicted, so the office
aborted it, left the clone clean, and sent this session: the office never
resolves a conflict itself, and the occupant is never sent to a terminal
for one.

## The two sides

- The workbench, as it is packed here: {{project}}'s tree in this
  request, at {{workbench}}.
- {{side}}, at {{tip}}: the commit the merge brings in.
- Where they parted: {{parted}}.

The files that conflict:

{{files}}

The other files {{side}} changed since the two sides parted, which did not
conflict and which git's merge carries as they are:

{{changed}}

## The materials

The folder rides in the office's context, and in it {{materials}} holds
everything the merge knows that the tree here does not:

- parted/ and workbench/: each conflicting file in its version where the
  two sides parted and in the workbench's, at its path.
- audience/: {{side}}'s copy of every file it changed since the two sides
  parted, at its path: each conflicting file, and each of the other files
  above, so you can see what the audience did beside the conflict: the
  conflicting files always, the others up to a cap. {{uncopied}} A side
  that has no copy of a file deleted it, or never had it.
- log.txt: the audience's commits since the two sides parted, one line
  each, so you can see what each change on that side was for.
- merge.md: the office's page for this job, the conflicting files on its
  `- file:` lines and the others on its `- changed:` lines; read it, never
  write it.

## What to do

Read the three versions of each conflicting file, the audience's copies of
the files beside them, and the log, and write each conflicting file as it
should read once both sides are in it: everything the workbench's work
needs, and everything {{side}} changed, kept. Where the two sides changed
the same lines, decide from what each change was for; where you cannot
tell, keep both behaviours if the code can carry them and say so in
notes.md, or end the turn with a light question block.

The response ships each conflicting file whose resolution differs from the
workbench's, as it should read after the merge, and nothing else: no other
file (the audience's other changes come in with git's merge), no refactor,
no fix you noticed on the way (propose those in notes.md). A file that
should not exist after the merge is a deleted change. Run the project's
tests where the tree here lets you, on the files as you wrote them.

When the response lands, `office land` makes it a merge commit in the
workbench: its parents are the landed session's commit and {{side}}'s tip,
{{tip}}, and its tree is git's own merge of everything that did not
conflict, with your version of each conflicting file. So ship every file
whose resolution differs from the workbench's; a file you leave out keeps
the workbench's version, and that is right when the workbench's version is
the resolution (bale admits no file shipped unchanged). When it is the
resolution of every file, the response ships no file at all (`changes:
[]`): bale lands it and tags it applied all the same, and `office land`
makes the merge commit from the workbench's versions. After it, `office
deliver` delivers the folder's own work alone.

## What every session owes

At the end of notes.md, as the doctrine's section 4 says: the Questions
and answers of any light block you sent, and a Handbook section for any
fact about {{project}} you learned that a later session should not have to
rediscover, written bare. A merge session writes no Walkthrough, Delivery
or Structure section: the folder's walkthrough and delivery words are the
work's, a merge changes nothing the audience reads, and the folder's title,
size and goal stand. Write instead a `## Merge` section: for each file, one
line on what you kept from each side and why. The Sort owed to any drop
that rides beside this session is owed here too.
