#!/usr/bin/env bash
# filed-append-only.sh: the filed-paper check for sessions (OFFICE.md
# section 15). A filed page grows at its end, and the bytes already
# filed never change. For a page that existed when the request was
# packed, the first BASE_SIZE bytes of the page as staged must hash to
# the sha256 the request stamped for it in provenance.base_files, where
# BASE_SIZE is measured from the copy the request shipped (bale stamps
# the hash, not the size). A page the session created has no base and
# only has to exist.
#
# Run as a script, from the office root or with --root:
#
#     filed-append-only.sh [--root DIR] SPEC...
#
# Or pasted into a session's validation.sh: everything above the marker
# line near the end (the one that says it runs the script) is the
# fragment; paste it and call filed_append_only with the specs. One
# spec per filed path:
#
#     PATH=SIZE:SHA256   the page existed at pack time; SIZE is the base
#                        copy's size in bytes, SHA256 its stamped hash
#     PATH=@BASEFILE     the same, measured from a copy of the base
#     PATH=new           the session created the page; no base
#
# Prints one [PASS] or [FAIL] line per spec, naming the path and why.
# Exits 0 when every spec passed, 1 when any failed, 2 on a bad spec or
# a missing tool. Writes nothing anywhere.

filed_append_only() {
  local root="." spec path base size sha have got grew ok=0 bad=0 n=0
  while [ $# -gt 0 ]; do
    case "$1" in
      --root) [ $# -ge 2 ] || { echo "[FAIL] filed-append-only: --root needs a directory"; return 2; }
              root="$2"; shift 2 ;;
      --) shift; break ;;
      -*) echo "[FAIL] filed-append-only: unknown option $1"; return 2 ;;
      *) break ;;
    esac
  done
  [ $# -gt 0 ] || { echo "[FAIL] filed-append-only: no filed paths given (PATH=SIZE:SHA256, PATH=@BASEFILE or PATH=new)"; return 2; }
  [ -d "$root" ] || { echo "[FAIL] filed-append-only: not a directory: $root"; return 2; }
  if command -v sha256sum >/dev/null 2>&1; then
    _fao_hash() { sha256sum | cut -d' ' -f1; }
  elif command -v shasum >/dev/null 2>&1; then
    _fao_hash() { shasum -a 256 | cut -d' ' -f1; }
  else
    echo "[FAIL] filed-append-only: neither sha256sum nor shasum is on PATH"; return 2
  fi
  for spec in "$@"; do
    n=$((n + 1))
    case "$spec" in
      *=*) path="${spec%%=*}"; base="${spec#*=}" ;;
      *) echo "[FAIL] filed-append-only: spec $n is not PATH=...: $spec"; return 2 ;;
    esac
    [ -n "$path" ] && [ -n "$base" ] || { echo "[FAIL] filed-append-only: spec $n has an empty path or base: $spec"; return 2; }
    case "$base" in
      new) size=""; sha="" ;;
      @*) base="${base#@}"
          [ -f "$base" ] || { echo "[FAIL] filed-append-only: $path: base copy not found: $base"; return 2; }
          size="$(wc -c < "$base" | tr -d ' ')"; sha="$(_fao_hash < "$base")" ;;
      *:*) size="${base%%:*}"; sha="${base#*:}"
           [[ "$size" =~ ^[0-9]+$ ]] || { echo "[FAIL] filed-append-only: $path: base size is not a byte count: $size"; return 2; }
           [[ "$sha" =~ ^[0-9a-fA-F]{64}$ ]] || { echo "[FAIL] filed-append-only: $path: base sha256 is not 64 hex digits: $sha"; return 2; }
           sha="$(printf '%s' "$sha" | tr 'A-F' 'a-f')" ;;
      *) echo "[FAIL] filed-append-only: $path: base must be SIZE:SHA256, @BASEFILE or new: $base"; return 2 ;;
    esac
    if [ ! -f "$root/$path" ]; then
      echo "[FAIL] filed-append-only: $path: filed page is missing (a filed page is never removed)"; bad=$((bad + 1)); continue
    fi
    if [ -z "$size" ]; then
      echo "[PASS] filed-append-only: $path: new filed page, no base to keep ($(wc -c < "$root/$path" | tr -d ' ') bytes)"; ok=$((ok + 1)); continue
    fi
    have="$(wc -c < "$root/$path" | tr -d ' ')"
    if [ "$have" -lt "$size" ]; then
      echo "[FAIL] filed-append-only: $path: truncated to $have bytes; the base was $size bytes"; bad=$((bad + 1)); continue
    fi
    got="$(head -c "$size" "$root/$path" | _fao_hash)"
    if [ "$got" != "$sha" ]; then
      echo "[FAIL] filed-append-only: $path: the first $size bytes changed (base sha256 $sha, staged prefix $got); a filed page grows at its end only"; bad=$((bad + 1)); continue
    fi
    grew=$((have - size))
    if [ "$grew" -eq 0 ]; then
      echo "[PASS] filed-append-only: $path: unchanged ($size bytes)"
    else
      echo "[PASS] filed-append-only: $path: grew by $grew bytes at the end; the first $size bytes are as filed"
    fi
    ok=$((ok + 1))
  done
  echo "filed-append-only: $ok passed, $bad failed, $n checked"
  [ "$bad" -eq 0 ]
}

# --- run as a script ---
# Below this line only what makes the fragment above a command. When
# the fragment is pasted into a validation.sh, leave these lines out.
filed_append_only "$@"
