# bale 0.4.40, as the out-trip probe found it on the work host

Captured by the second run of the probe of session
2026-10-07-out-trip-to-host-004, on 2026-10-07, through the hosted
project's shell (`ssh USER@HOST docker exec -i -u USER CONTAINER bash
-lc`), read-only: `bale --version` and `bale help` for the top level,
`open` and `clipboard`. The host's bale is 0.4.40, below the read side's
floor (0.4.45); these files are why the floor is a refusal for a session
going out there, not only a line in `office status`:

- `open` has no `--check` and no `--json` (help-open-head.json's usage
  line), so office start's rehearsal before it writes anything cannot run
  there;
- there is no `clipboard` verb (help-clipboard.json: bale's own error
  line, the streams merged by the probe);
- `pack` has `--json`, `--readme-file`, `--no-readme`, `--read-only`,
  `--work-class`, `--constraint` and `--context` (the probe's grep of
  `bale help pack`, not kept here: it printed grep's line numbers).

The probe printed no hashes and no exit codes (`exit` is null where it
was not seen). The paste came through a console that showed UTF-8 as
CP437 (`ΓÇö` for `—`, `┬º` for `§`, `ΓÇô` for `–`); those characters
were restored before each line's sha256 was computed on this side.

What the same probe established about installing bale, which `office
projects level-bale` is built on (no bale output, so no file here): both
machines install bale the same way, a release install at `~/bale` linked
from `~/.local/bin/bale`, with the version in `bin/VERSION`, and
`upgrade.sh` beside it (0.4.51's read in full: `-y`, `--no-validate`,
`--no-symlink`; it moves `<install>/user/` aside, replaces the rest from
a release tarball, puts `user/` back and runs `install.sh -y`, which
runs `validate.sh`). The host's `user/` holds `bale.toml` alone
(sections `[apply]` and `[identity]`); this machine's adds a `scripts/`
hook directory and `hook-acceptances.json`. A tar of this machine's
install streamed to the host and one streamed back through the full
prefix both arrived intact (sha256 equal), and the login shell there
prints nothing on stdout.
