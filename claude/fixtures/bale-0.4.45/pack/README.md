# bale 0.4.45 packing, as the out-and-in probe found it

Captured by the probe of session 2026-10-02-friction-out-and-in-002 on
the machine office-src is built on, with bale 0.4.45 installed. Every
call ran in a throwaway repo the probe built under a temp directory
(`/tmp/office-probe.WtDCdZ`, since removed), with stdin closed, so no
real repo opened a session. Each JSON file is one bale invocation, in
the read side's shape plus the directory it ran in: argv, cwd, exit
code, stdout lines exactly as printed, stderr lines, the sha256 of each
stdout line (printed by the probe and re-verified on the paste), and
where it was captured.

- office-pack: a session packed from a scratch office built by office-src
  0.5.0's own `office init`, on one folder: `--include` the folder,
  `--write` the folder and the notepad, `--no-readme`, `--json`. The
  office's include group engaged and pulled the hung items. The session
  opener is on stderr, between bale's scissor lines; the JSON report
  carries no opener.
- office-status: `bale status --json` in that office while the session
  was open: `sessions` and `scopes` name it.
- office-second-pack, office-second-pack-plain: a second office pack
  forecasting the notepad, with and without `--json`: refused, exit 1,
  stdout empty under `--json`, the reason on stderr's last line.
- office-context-whole, office-context-include: `bale pack --context
  --json` in the office, the whole tree and one folder. Under
  `--context` the include group does not fire; the tarball is
  `.bale/outbox/context-<dir>.tar.gz` and the second run overwrote the
  first.
- project-pack, project-pack-plain: a project session with
  `--constraint`, `--readme-file` and `--work-class`, with and without
  `--json` (the plain one shows the human report and the opener).
- ctx-other-include, ctx-other-inside: a directory inside another repo,
  packed from the repo's top with `--include`, and from inside the
  directory, which puts a `.bale/` there.
- ctx-plain: a plain directory, a copy of the doctrine, outside git.
- pack_help: `bale pack --help`, printed raw; each line's sha256 was
  computed from the pasted line.

tests/test_start.py reads these: the report keys the office declares
are checked against them, the opener and refusal readers run over them
verbatim, and the suite's fake bale builds its output from them.
These files are never edited.
