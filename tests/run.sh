#!/usr/bin/env bash
# Run office-src's test suite. By default each module runs as its own
# process, four at a time, with the classes that drive a terminal
# (serial_group = "terminal") one after another in a lane of their own;
# one log per job, named in the summary. --serial runs today's single
# process (unittest discover -v) instead. tests/runner.py --help says the
# rest (--jobs N, --logs DIR, --plan, module names).
#
#   tests/run.sh             the whole suite, side by side
#   tests/run.sh --serial    the whole suite, one process
#   tests/run.sh test_land   one module (and its share of the serial group)
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B "$here/runner.py" "$@"
