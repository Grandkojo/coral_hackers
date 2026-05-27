#!/usr/bin/env bash
# Register Coral sources from environment variables (no interactive prompts).
# Run from backend/ after filling .env:
#   ./scripts/setup_coral_sources.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ -f "${BACKEND_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(sed 's/\r$//' "${BACKEND_DIR}/.env")
  set +a
fi

CORAL="${CORAL_BINARY:-coral}"
if ! command -v "$CORAL" >/dev/null 2>&1; then
  if [[ -x "${HOME}/.local/bin/coral" ]]; then
    CORAL="${HOME}/.local/bin/coral"
  else
    echo "error: coral CLI not found (set CORAL_BINARY or add ~/.local/bin to PATH)" >&2
    exit 1
  fi
fi

VERCEL_MANIFEST_URL="https://raw.githubusercontent.com/withcoral/coral/main/sources/community/vercel/manifest.yaml"
VERCEL_MANIFEST="${VERCEL_MANIFEST:-${SCRIPT_DIR}/vercel-manifest.yaml}"

GITHUB_OWNER="${GITHUB_OWNER:-Grandkojo}"
GITHUB_REPO="${GITHUB_REPO:-coral_hackers}"
GITHUB_ACCOUNT_TYPE="${GITHUB_ACCOUNT_TYPE:-user}"
SLACK_INCIDENT_CHANNEL="${SLACK_INCIDENT_CHANNEL:-incidents}"

require() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "error: $name is not set" >&2
    exit 1
  fi
}

source_is_configured() {
  local name="$1"
  "$CORAL" source list 2>/dev/null | grep -qE "(^|[[:space:]])${name}([[:space:]]|$)"
}

run_sql() {
  local label="$1"
  local sql="$2"
  echo
  echo "== ${label}"
  "$CORAL" sql "$sql"
}

add_bundled_source() {
  local name="$1"
  shift
  for arg in "$@"; do require "$arg"; done

  if source_is_configured "$name"; then
    echo "skip: ${name} already configured"
    "$CORAL" source test "$name"
    return 0
  fi

  echo "add: ${name}"
  "$CORAL" source add "$name"
  "$CORAL" source test "$name"
}

ensure_vercel_manifest() {
  if [[ -f "$VERCEL_MANIFEST" ]]; then
    echo "using vercel manifest: ${VERCEL_MANIFEST}"
    return 0
  fi

  echo "downloading vercel manifest to ${VERCEL_MANIFEST}"
  curl -fsSL -o "$VERCEL_MANIFEST" "$VERCEL_MANIFEST_URL"
}

add_vercel_source() {
  require VERCEL_TOKEN
  ensure_vercel_manifest

  if source_is_configured vercel; then
    echo "skip: vercel already configured"
    "$CORAL" source test vercel
    return 0
  fi

  echo "add: vercel (community manifest)"
  "$CORAL" source add --file "$VERCEL_MANIFEST"
  "$CORAL" source test vercel
}

echo "Using coral: $("$CORAL" --version)"

add_bundled_source github GITHUB_TOKEN
add_bundled_source sentry SENTRY_ORG SENTRY_TOKEN
add_bundled_source slack SLACK_TOKEN
add_vercel_source

echo
echo "Configured sources:"
"$CORAL" source list

run_sql "coral.tables" \
  "SELECT schema_name, table_name FROM coral.tables WHERE schema_name IN ('github','sentry','slack','vercel') ORDER BY schema_name, table_name LIMIT 30"

run_sql "github.pulls" \
  "SELECT number, title, user__login, merged_at, state FROM github.pulls WHERE owner = '${GITHUB_OWNER}' AND repo = '${GITHUB_REPO}' ORDER BY merged_at DESC LIMIT 3"

run_sql "sentry.issues" \
  "SELECT id, title, level, first_seen FROM sentry.issues LIMIT 3"

run_sql "slack.channels" \
  "SELECT name, id, num_members FROM slack.channels WHERE name = '${SLACK_INCIDENT_CHANNEL}' LIMIT 3"

run_sql "vercel.deployments" \
  "SELECT uid, name, state, target, created_at FROM vercel.deployments ORDER BY created_at DESC LIMIT 3"

run_sql "planner join (iteration 1)" \
  "SELECT g.title AS pr_title, g.number AS pr_number, s.title AS error_message, s.level AS error_level FROM github.pulls g JOIN sentry.issues s ON s.first_seen >= g.merged_at WHERE g.owner = '${GITHUB_OWNER}' AND g.repo = '${GITHUB_REPO}' AND s.level IN ('fatal', 'error') AND g.state = 'closed' ORDER BY s.first_seen DESC LIMIT 3"

if [[ "${GITHUB_ACCOUNT_TYPE}" == "org" ]]; then
  run_sql "github.teams (iteration 4, org account)" \
    "SELECT name AS service, slug AS team, description AS oncall FROM github.teams WHERE org = '${GITHUB_OWNER}' LIMIT 3"
else
  run_sql "github.collaborators (iteration 4, personal account)" \
    "SELECT login AS oncall, html_url AS slack_channel, repo AS service FROM github.collaborators WHERE owner = '${GITHUB_OWNER}' AND repo = '${GITHUB_REPO}' ORDER BY permissions__admin DESC LIMIT 5"
fi

echo
echo "All sources configured and smoke queries completed."
