#!/usr/bin/env bash
# office-src 0.2.0: give an office built by 0.1.0 the include group that
# makes every pack from it ship the hung items (profile.md, the survey).
# Runs from the office root with OFFICE_ROOT, OFFICE_MIGRATION and
# OFFICE_SRC set. Touches bale.toml only; never filed paper.

set -euo pipefail
: "${OFFICE_SRC:?OFFICE_SRC is not set; run this through office upgrade}"
helper() { python3 "$OFFICE_SRC/lib/office_helper.py" "$@"; }

if [ ! -e bale.toml ]; then
  helper render-bale-toml floor-plan/manifest.toml --root . > bale.toml
  echo "[office] 0.2.0: wrote bale.toml with the hung include group" >&2
elif grep -q '^\[pack\]' bale.toml; then
  echo "[office] 0.2.0: bale.toml already has a [pack] section; left as it is (office status compares it with the floor plan)" >&2
else
  { printf '\n'; helper render-bale-toml floor-plan/manifest.toml --root . --pack-only; } >> bale.toml
  echo "[office] 0.2.0: added the hung include group to the existing bale.toml" >&2
fi
