#!/usr/bin/env bash
# Bootstrap Hermes profiles + skill for Harness Phase 5 (non-interactive where possible).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HERMES="${HERMES:-$HOME/OpenClaw_Workspace/hermes/venv/bin/hermes}"
SKILL_PATH="$ROOT/scripts/skills/harness-court-team"

if [[ ! -x "$HERMES" ]]; then
  echo "ERROR: hermes not found at $HERMES" >&2
  exit 1
fi

for p in court-team court-verify court-synthesize; do
  if ! "$HERMES" profile list 2>/dev/null | grep -q "$p"; then
    echo "Creating profile: $p"
    "$HERMES" profile create "$p" || echo "WARN: profile create $p failed (may already exist)"
  else
    echo "Profile exists: $p"
  fi
done

for p in court-team court-verify court-synthesize; do
  echo "Installing skill for $p ..."
  "$HERMES" skills install "$SKILL_PATH" --as "$p" 2>/dev/null || \
    echo "WARN: skills install for $p — run manually if needed"
done

echo "Done. Run: python3 scripts/hermes_doctor.py"
