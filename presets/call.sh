#!/usr/bin/env bash
# Minimal raw-HTTP backend for bin/route: call.sh <model> <effort> <task>
# Requires OPENAI_BASE_URL and OPENAI_API_KEY in the environment.
set -euo pipefail

model="${1:?model}"
effort="${2:-}"
task="${3:?task}"

: "${OPENAI_BASE_URL:?set OPENAI_BASE_URL (e.g. https://api.inferhub.dev/v1)}"
: "${OPENAI_API_KEY:?set OPENAI_API_KEY}"

payload=$(MODEL="$model" EFFORT="$effort" TASK="$task" python - <<'PY'
import json, os
body = {"model": os.environ["MODEL"], "messages": [{"role": "user", "content": os.environ["TASK"]}]}
if os.environ.get("EFFORT"):
    body["reasoning"] = {"effort": os.environ["EFFORT"]}
print(json.dumps(body))
PY
)

curl -sS "${OPENAI_BASE_URL%/}/chat/completions" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$payload" |
  python -c 'import json,sys; r=json.load(sys.stdin); print(r["choices"][0]["message"].get("content","")); u=r.get("usage") or {}; sys.stderr.write("[tokens in=%s out=%s cost=%s]\n" % (u.get("prompt_tokens"), u.get("completion_tokens"), u.get("cost")))'
