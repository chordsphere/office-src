#!/usr/bin/env bash
# Install office-src from this working copy.
#
#   ~/office-src/install.sh [--prefix DIR] [--bin-dir DIR] [--no-link]
#
# The install is a separate copy, like bale's split between its source
# and its install: offices read their tools from the install, so the
# working copy can change freely without touching any office until the
# next install. Inside a git work tree the install is exactly HEAD (git
# archive); uncommitted changes are reported and left out. Outside git it
# copies the shipped directories as they are.

set -uo pipefail

log() { printf '[install] %s\n' "$*" >&2; }
die() { printf '[install] error: %s\n' "$*" >&2; exit 1; }

SRC="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PREFIX="${XDG_DATA_HOME:-$HOME/.local/share}/office-src"
BIN_DIR="$HOME/.local/bin"
LINK=1
SHIPPED=(bin lib share templates doctrine migrations VERSION README.md RELEASES.md install.sh)

while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) [ $# -ge 2 ] || die "--prefix needs a directory"; PREFIX="$2"; shift 2 ;;
    --bin-dir) [ $# -ge 2 ] || die "--bin-dir needs a directory"; BIN_DIR="$2"; shift 2 ;;
    --no-link) LINK=0; shift ;;
    -h|--help) sed -n '2,4p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

for t in python3 git tar; do command -v "$t" >/dev/null 2>&1 || die "$t is required and not on PATH"; done
PREFIX="$(readlink -m "$PREFIX")"
case "$PREFIX/" in
  "$SRC/"*) die "the install ($PREFIX) cannot sit inside the working copy ($SRC)" ;;
esac
case "$SRC/" in
  "$PREFIX/"*) die "the working copy ($SRC) cannot sit inside the install ($PREFIX)" ;;
esac
if [ -e "$PREFIX" ] && ! grep -q '^package: office-src$' "$PREFIX/INSTALLED" 2>/dev/null; then
  die "$PREFIX exists and is not an office-src install; choose another --prefix or move it aside"
fi

VERSION="$(head -n 1 "$SRC/VERSION" 2>/dev/null)"
[ -n "$VERSION" ] || die "no VERSION in $SRC"
mkdir -p "$(dirname "$PREFIX")" || die "cannot create $(dirname "$PREFIX")"
STAGE="$(mktemp -d "$(dirname "$PREFIX")/.office-src-install.XXXXXX")" || die "cannot make a staging directory beside $PREFIX"
trap 'rm -rf "$STAGE"' EXIT

if git -C "$SRC" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  COMMIT="$(git -C "$SRC" rev-parse --short HEAD 2>/dev/null)" || die "$SRC has no commits to install"
  if [ -n "$(git -C "$SRC" status --porcelain)" ]; then
    log "the working copy has uncommitted changes; installing HEAD ($COMMIT) without them"
  fi
  git -C "$SRC" archive HEAD -- "${SHIPPED[@]}" | tar -x -C "$STAGE" || die "git archive of HEAD failed"
else
  COMMIT="none (not a git work tree)"
  for p in "${SHIPPED[@]}"; do
    [ -e "$SRC/$p" ] || die "missing from the source: $p"
    cp -a "$SRC/$p" "$STAGE/" || die "cannot copy $p"
  done
fi

chmod +x "$STAGE/bin/office" "$STAGE/install.sh" || die "cannot set the exec bit"
{
  printf 'package: office-src\n'
  printf 'version: %s\n' "$VERSION"
  printf 'commit: %s\n' "$COMMIT"
  printf 'source: %s\n' "$SRC"
  printf 'installed_at: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$STAGE/INSTALLED"

# Swap last, so a failed install leaves the previous one intact.
if [ -e "$PREFIX" ]; then rm -rf "$PREFIX" || die "cannot remove the previous install at $PREFIX"; fi
mv "$STAGE" "$PREFIX" || die "cannot move the install into $PREFIX"
trap - EXIT
log "installed office-src $VERSION ($COMMIT) at $PREFIX"

if [ "$LINK" = "1" ]; then
  mkdir -p "$BIN_DIR" || die "cannot create $BIN_DIR"
  if [ -e "$BIN_DIR/office" ] && [ ! -L "$BIN_DIR/office" ]; then
    die "$BIN_DIR/office exists and is not a link; move it aside or use --no-link"
  fi
  ln -sfn "$PREFIX/bin/office" "$BIN_DIR/office" || die "cannot link $BIN_DIR/office"
  log "linked $BIN_DIR/office"
  case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) log "$BIN_DIR is not on PATH; add it to use office by name" ;;
  esac
fi

"$PREFIX/bin/office" version || die "the installed office command does not run"
