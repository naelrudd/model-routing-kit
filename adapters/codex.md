# Codex adapter

Codex agents carry their own `model` and `model_reasoning_effort`, and Codex only delegates when you
ask it to or when `AGENTS.md` tells it to.

## 1. The main session is the router

```toml
# ~/.codex/config.toml
model = "gpt-6.1-sol"          # the build tier
model_reasoning_effort = "medium"
```

## 2. Agents in `.codex/agents/`

```toml
# .codex/agents/triage.toml
name = "triage"
description = "Use first for every coding task. Classifies the task and returns a route."
model = "gpt-6-luna"
model_reasoning_effort = "low"
sandbox_mode = "read-only"
developer_instructions = """
Read ROUTING-LESSONS.md first. Reply with JSON only:
{"route": "quick|build|deep", "risk": "low|medium|high", "checks": ["tests","typecheck","lint","review"]}
"""
```

Same shape for the rest (`name`, `description`, `developer_instructions` are required):

```toml
# quick.toml    -> model = "gpt-6-luna"   · model_reasoning_effort = "medium"
# build.toml    -> model = "gpt-6.1-sol"  · model_reasoning_effort = "medium"
# deep.toml     -> model = "gpt-6.1-sol"  · model_reasoning_effort = "xhigh"
# escalate.toml -> model = "gpt-6-astra"  · model_reasoning_effort = "medium"
# verifier.toml -> model = "gpt-6.1-sol"  · model_reasoning_effort = "high"
#                  developer_instructions = "Run the checks. Never edit files."
```

## 3. The rules, in `AGENTS.md`

```markdown
## Routing
1. For every coding task, call the triage agent first.
2. Delegate to the agent matching its route: quick, build or deep. Pass the full task and the
   triage JSON.
3. Then call the verifier with the risk and checks from triage.
4. If the verifier says FAIL, retry once, one step up: more effort first, then a bigger model.
5. After any escalation, append one line to ROUTING-LESSONS.md: "<task pattern> -> <route that worked>".
```

## 4. Stop hook

Save the same `check.sh` as `.codex/hooks/check.sh` and register it — Codex asks you to approve a new
hook before it runs:

```json
{
  "hooks": {
    "Stop": [ { "hooks": [ { "type": "command", "command": "bash .codex/hooks/check.sh", "timeout": 300 } ] } ]
  }
}
```

## 5. Headless, per route

```bash
route build "add cursor pagination" --backend codex --verify "cargo test"
```

`--backend codex` runs `codex exec "<task>" -m <model> -c model_reasoning_effort=<effort>`, which is
the one place Codex lets you pin both per run without touching config.
