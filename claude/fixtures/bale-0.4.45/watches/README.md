# bale 0.4.45 and git, as the drafting-table-digest probe found them

Captured by the probe of session 2026-10-06-drafting-table-digest-001 on
the machine office-src is built on (WSL2, bale 0.4.45, Python 3.12.3), on
2026-10-06 at 19:13 UTC, with stdin closed. Each bale JSON file is one
invocation, in the home-office set's shape: argv, cwd, stdin, exit code,
stdout lines exactly as printed with each line's sha256 (printed by the
probe and re-verified on the paste), the stderr lines, and where it was
captured. Each directory is one repo, so a fake bale routed to it replays
one coherent snapshot: its status, its aggregates and the dossier of
every session its outbox names.

- office-src/: `status --json` (this session open, scope `["."]`);
  `stats --json` whole; `--since` 2026-08-01 (the whole corpus, as
  watch 1 wrote it), 2026-10-01 (the friction wave and 4b-1), 2026-10-05
  (4b-1 alone, held then applied, and this session open), 2026-10-06
  (this session alone: no applied session), 2026-10-07 (none); `--work-class
  code` whole and composed with `--since 2026-10-01`; a timestamp given to
  `--since`, refused (exit 1: "--since must be an ISO date (YYYY-MM-DD)");
  and the dossiers of all sixteen sessions.
- home-office/: `status --json` (the plan-4b sitting open, scope `[]`);
  `stats --json` whole; `--since` 2026-09-30 (the whole corpus),
  2026-10-04 (the slips session alone) and 2026-10-07 (none); the three
  dossiers.
- bale-src/, ironwood/, nisaba-src/, twine-src/: each project's whole
  `stats --json`, the other projects home-office scopes. bale-src's is
  the corpus with clarification rounds: `members.clarification_self_only`
  names nine sessions, which is what watch 24's `unrelayed-rounds` reads.
  Its stderr carries bale's own warning about one record's unrecognized
  agreement word, with exit 0. ironwood's carries unparsed records, the
  first corpus where `unparsed-share` is not zero.
- git/: what git showed beside them, `git --no-optional-locks` run read
  only, each line hashed the same way: the last 60 commit subjects in
  office-src (bale's `[bale SID] ...`, `Merge bale SID` and `[bale sweep
  SID] ...`, beside the repo's own). A git record has `git` in place of
  `argv`, so no fake bale ever replays it. The probe also read
  home-office's commit subjects, its notepad pages with the commit that
  added each, and its drafting table (none yet); those lines are the
  office's own context (its folders, its founding words), which never
  lands in this project, so they are not kept here. What they showed is
  in the session's notes: a sitting's pages are filed by `office start:
  the sitting's words from SID's brief`, and bale's subjects there have
  the same three shapes.

tests/test_watches_digest.py replays them: the catalog against the
captured aggregates, the check's windows against the `--since` lines,
the digest's sessions since a sitting against the dossiers, and the
declared commit subjects against the captured ones. These files are
never edited; a new bale is probed into its own bale-VERSION/ directory.
