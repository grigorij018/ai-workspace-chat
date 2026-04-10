#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_FILE="${1:-$ROOT_DIR/.env.example}"

if [[ ! -f "$TARGET_FILE" ]]; then
  echo "Target file not found: $TARGET_FILE" >&2
  exit 1
fi

if grep -En '(sk-[A-Za-z0-9_-]{8,}|ghp_[A-Za-z0-9]{12,}|AIza[0-9A-Za-z_-]{20,})' "$TARGET_FILE" >/dev/null; then
  echo "Potential committed secret detected in $TARGET_FILE" >&2
  exit 1
fi

for key in OPENAI_API_KEY OPENAI_API_KEYS WEBUI_SECRET_KEY; do
  value="$(grep -E "^${key}=" "$TARGET_FILE" | head -n 1 | cut -d '=' -f 2- || true)"
  if [[ -n "${value// }" ]]; then
    echo "$key must stay empty in $TARGET_FILE" >&2
    exit 1
  fi
done

echo "Secret discipline check passed for $TARGET_FILE"
