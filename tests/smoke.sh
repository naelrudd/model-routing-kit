#!/usr/bin/env bash
# Smoke test for bin/route. No API calls, no cost — uses a fake "echo" backend.
# Usage: bash tests/smoke.sh
set -uo pipefail

cd "$(dirname "$0")/.." || exit 2
TABLE=tests/echo-table.json
fail=0

expect() { # expect <label> <needle> <haystack>
  if [[ "$3" == *"$2"* ]]; then
    echo "PASS  $1"
  else
    echo "FAIL  $1 — expected to find: $2"
    echo "      got: $3"
    fail=1
  fi
}

# 1. a passing check keeps the task on its route (no escalation)
out=$(python bin/route quick "task" --preset "$TABLE" --verify "true" 2>&1)
expect "no escalation when the check passes" "ran cheap-model at low" "$out"
expect "stops at quick" "check passed on 'quick'" "$out"

# 2. a failing check escalates exactly one tier, then succeeds
#    (portable verify command: passes the second time it runs)
VERIFY='python -c "import os,sys; p=os.path.join(\".\",\"route-smoke-flag\"); ok=os.path.exists(p); open(p,\"a\").close(); sys.exit(0 if ok else 1)"'
out=$(python bin/route quick "task" --preset "$TABLE" --verify "$VERIFY" 2>&1)
rm -f route-smoke-flag
expect "escalates quick -> build" "escalating quick -> build" "$out"
expect "runs the build tier" "ran mid-model at medium" "$out"
expect "passes on the escalated tier" "check passed on 'build'" "$out"

# 3. --max-escalations 0 refuses to climb
out=$(python bin/route quick "task" --preset "$TABLE" --verify "false" --max-escalations 0 2>&1)
expect "honours --max-escalations 0" "no escalation left" "$out"

# 4. unknown route is a clean error, not a traceback
out=$(python bin/route nope "task" --preset "$TABLE" 2>&1)
expect "rejects unknown routes" "unknown route 'nope'" "$out"

# 5. dry-run prints the command and runs nothing
out=$(python bin/route deep "task" --preset "$TABLE" --dry-run 2>&1)
expect "dry-run shows the top tier" "ran top-model at xhigh" "$out"

exit $fail
