#!/usr/bin/env bash
# Aegis-LLM CI policy gate (standalone).
#
# Fails the build when a run has findings at/above the severity threshold with
# at least the minimum confidence. Prints the SARIF report path on success.
#
# Usage:
#   AEGIS_API=http://localhost:8000 \
#   AEGIS_TOKEN=<token> \
#   ci/policy_gate.sh <run-id> [severity-threshold] [min-confidence]
#
set -euo pipefail

API="${AEGIS_API:-http://localhost:8000}"
TOKEN="${AEGIS_TOKEN:?set AEGIS_TOKEN to a bearer token}"
RUN_ID="${1:?usage: policy_gate.sh <run-id> [threshold] [min-confidence]}"
THRESHOLD="${2:-high}"
MIN_CONF="${3:-0.6}"

RESPONSE="$(curl -sf -X POST "$API/ci/gate" \
  -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d "{\"run_id\":\"$RUN_ID\",\"severity_threshold\":\"$THRESHOLD\",\"min_confidence\":$MIN_CONF,\"sarif\":true}")"

PASSED="$(echo "$RESPONSE" | python -c 'import sys,json;print(json.load(sys.stdin)["passed"])')"
BLOCKING="$(echo "$RESPONSE" | python -c 'import sys,json;print(len(json.load(sys.stdin)["blocking_findings"]))')"

echo "CI gate: passed=$PASSED blocking=$BLOCKING threshold=$THRESHOLD min_conf=$MIN_CONF"
echo "$RESPONSE" | python -c 'import sys,json;print(json.load(sys.stdin)["message"])'

if [ "$PASSED" = "False" ] || [ "$PASSED" = "false" ]; then
  echo "$RESPONSE" > "${RUN_ID}.sarif.json"
  echo "SARIF written to ${RUN_ID}.sarif.json — blocking findings present."
  exit 1
fi
exit 0
