#!/usr/bin/env bash

set -euo pipefail

APP_URL="${APP_URL:-http://localhost:${OPEN_WEBUI_PORT:-3000}}"
SMOKE_ADMIN_NAME="${SMOKE_ADMIN_NAME:-Smoke Admin}"
SMOKE_ADMIN_EMAIL="${SMOKE_ADMIN_EMAIL:-smoke-admin@example.com}"
SMOKE_ADMIN_PASSWORD="${SMOKE_ADMIN_PASSWORD:-password123}"

echo "Smoke check against ${APP_URL}"

health_response="$(curl --silent --show-error --fail "${APP_URL}/health")"
echo "$health_response" | grep -q '"status":true'

signup_code="$(
  curl --silent --show-error --output /tmp/openwebui-smoke-signup.json --write-out '%{http_code}' \
    -X POST "${APP_URL}/api/v1/auths/signup" \
    -H 'Content-Type: application/json' \
    -d "{\"name\":\"${SMOKE_ADMIN_NAME}\",\"email\":\"${SMOKE_ADMIN_EMAIL}\",\"password\":\"${SMOKE_ADMIN_PASSWORD}\"}"
)"

if [[ "$signup_code" != "200" && "$signup_code" != "400" ]]; then
  echo "Unexpected signup status: $signup_code" >&2
  cat /tmp/openwebui-smoke-signup.json >&2
  exit 1
fi

signin_code="$(
  curl --silent --show-error --output /tmp/openwebui-smoke-signin.json --write-out '%{http_code}' \
    -X POST "${APP_URL}/api/v1/auths/signin" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"${SMOKE_ADMIN_EMAIL}\",\"password\":\"${SMOKE_ADMIN_PASSWORD}\"}"
)"

if [[ "$signin_code" != "200" ]]; then
  echo "Unexpected signin status: $signin_code" >&2
  cat /tmp/openwebui-smoke-signin.json >&2
  exit 1
fi

grep -q '"token"' /tmp/openwebui-smoke-signin.json

echo "Smoke check passed"
