#!/usr/bin/env bash
# Run office-src's test suite. By default each module runs as its own
# process, four at a time, with the classes that drive a terminal
# (serial_group = "terminal") one after another in a lane of their own;
# one log per job, named in the summary. Every job gets a HOME, TMPDIR and
# XDG directories of its own: nothing a test runs reads this machine's.
# tests/runner.py --help says the rest (--jobs N, --logs DIR, --plan).
#
#   tests/run.sh                   the whole suite, side by side
#   tests/run.sh --fast            the fast tier (tests/fast-tier.toml), under
#                                  its two-minute budget; validation.sh runs it
#   tests/run.sh --fast test_land  the fast tier and all of one module
#   tests/run.sh --detach          the whole suite in the background: one line
#                                  names its verdict file, and it returns at once
#   tests/run.sh --serial          the whole suite, one process
#   tests/run.sh test_land         one module (and its share of the serial group)
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B "$here/runner.py" "$@"
