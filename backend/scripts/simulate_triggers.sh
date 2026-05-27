#!/usr/bin/env bash
# Run demo trigger scenarios against a running Reef API.
# Usage:
#   ./scripts/simulate_triggers.sh
#   BASE_URL=http://127.0.0.1:8000 ./scripts/simulate_triggers.sh dashboard
#   ./scripts/simulate_triggers.sh sentry
#   ./scripts/simulate_triggers.sh all

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
MODE="${1:-all}"

if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq is required (apt install jq)" >&2
  exit 1
fi

run_dashboard_scenarios() {
  local count=0
  echo "=== Dashboard scenarios (NL + Vercel URL) ==="
  while IFS= read -r scenario; do
    name=$(echo "$scenario" | jq -r '.name')
    path=$(echo "$scenario" | jq -r '.path')
    body=$(echo "$scenario" | jq -c '.body')
    echo
    echo ">> ${name}"
    response=$(curl -sS -X POST "${BASE_URL}${path}" \
      -H "Content-Type: application/json" \
      -d "$body")
    inv_id=$(echo "$response" | jq -r '.investigation_id // empty')
    root=$(echo "$response" | jq -r '.root_cause // "null"')
    severity=$(echo "$response" | jq -r '.severity_score // empty')
    if [[ -z "$inv_id" ]]; then
      echo "FAILED: $response"
      exit 1
    fi
    echo "   investigation_id=$inv_id severity=$severity"
    echo "   root_cause=${root:0:120}"
    count=$((count + 1))
  done < <(jq -c '.[]' "${SCRIPT_DIR}/fixtures/trigger_scenarios.json")
  echo
  echo "Dashboard scenarios completed: ${count}"
}

run_sentry_scenarios() {
  local count=0
  echo "=== Sentry webhook scenarios ==="
  for fixture in "${SCRIPT_DIR}"/fixtures/sentry_*.json; do
    [[ -f "$fixture" ]] || continue
    name=$(basename "$fixture")
    echo
    echo ">> ${name}"
    response=$(curl -sS -X POST "${BASE_URL}/api/v1/webhooks/sentry" \
      -H "Content-Type: application/json" \
      --data-binary @"${fixture}")
    inv_id=$(echo "$response" | jq -r '.investigation_id // empty')
    root=$(echo "$response" | jq -r '.root_cause // "null"')
    severity=$(echo "$response" | jq -r '.severity_score // empty')
    if [[ -z "$inv_id" ]]; then
      echo "FAILED: $response"
      exit 1
    fi
    echo "   investigation_id=$inv_id severity=$severity"
    echo "   root_cause=${root:0:120}"
    count=$((count + 1))
  done
  echo
  echo "Sentry webhook scenarios completed: ${count}"
}

echo "Reef trigger simulation → ${BASE_URL}"
curl -sS "${BASE_URL}/health" | jq -e '.status == "ok"' >/dev/null
echo "Health OK"

case "$MODE" in
  dashboard) run_dashboard_scenarios ;;
  sentry) run_sentry_scenarios ;;
  all)
    run_dashboard_scenarios
    run_sentry_scenarios
    ;;
  *)
    echo "Usage: $0 [dashboard|sentry|all]" >&2
    exit 1
    ;;
esac

echo
echo "Done. Open ${BASE_URL}/docs to inspect API responses."
