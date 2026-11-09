#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PATTERN='(-----BEGIN [A-Z ]*PRIVATE KEY-----|SECRET KEYPAIR|"private_key"[[:space:]]*:|"secret_key"[[:space:]]*:|wk_[A-Za-z0-9]{20,}|spn_[A-Za-z0-9]{20,}|ed25519:[1-9A-HJ-NP-Za-km-z]{40,})'

if git grep -nE "$PATTERN" -- \
  ':!scripts/check_secrets.sh' \
  ':!docs/evidence.md'; then
  echo "Potential secret material found in tracked files." >&2
  exit 1
fi

echo "No obvious secrets found."
