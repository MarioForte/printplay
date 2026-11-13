#!/usr/bin/env bash
# Run PrintPlay with the TiMini-Print checkout next to it.
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
TIMINI="${TIMINIPRINT_ROOT:-$ROOT/../timini-print}"

if [[ ! -d "$TIMINI/timiniprint" ]]; then
  echo "TiMini-Print not found at: $TIMINI" >&2
  echo "Set TIMINIPRINT_ROOT to its checkout, or clone it next to PrintPlay." >&2
  exit 1
fi

PY="$TIMINI/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Warning: $TIMINI/.venv/bin/python not found." >&2
  echo "Create the TiMini-Print virtualenv first (see README Quick start)." >&2
  echo "Falling back to python3; dependencies may be missing." >&2
  PY="python3"
fi

export PYTHONPATH="$ROOT:$TIMINI${PYTHONPATH:+:$PYTHONPATH}"
exec "$PY" -m printplay "$@"
