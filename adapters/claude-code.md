# [CC] adapter

[CC] takes a model and an effort **per subagent**, which makes the route table native. Check the
frontmatter keys against your installed version — `effort` on agents is newer than `model`.

## 1. The main session is the router

```
/model sonnet            # the build tier; keep the top model for escalation
```

Do **not** set `CLAUDE_CODE_EFFORT_LEVEL` in the environment: it overrides every subagent's own
effort and silently flattens the whole ladder.

## 2. `.claude/agents/triage.md`

```markdown
---
name: triage
description: Use FIRST for every coding task. Classifies the task and returns a route.
tools: Read, Grep, Glob
model: sonnet
effort: low
memory: project
---
Classify the task. Reply with JSON only:
{"route": "quick|build|deep", "risk": "low|medium|high", "checks": ["tests","typecheck","lint","review"]}
- quick: small and well-specified, one or two files
- build: a normal feature or bug fix
- deep: architecture, migrations, auth, payments, data, or anything unclear
Read your MEMORY.md for past misses before you answer.
```

## 3. The workers

```markdown
# .claude/agents/quick.md
---
name: quick
description: Small, well-specified changes routed here by triage.
model: sonnet
effort: low
---
Make the change. Keep the diff small. Run the relevant tests.

# .claude/agents/build.md    -> model: sonnet  · effort: medium
# .claude/agents/deep.md     -> model: opus    · effort: xhigh
# .claude/agents/escalate.md -> model: opus    · effort: high   (only after a failed check)
```

## 4. `.claude/agents/verifier.md`

Use `prompts/verifier.md` from this repo as the body, with:

```markdown
---
name: verifier
description: Checks a finished change. Never edits code.
tools: Read, Grep, Glob, Bash
model: sonnet
effort: medium
---
```

## 5. The rules, in `CLAUDE.md`

```markdown
## Routing
1. For every coding task, call the triage agent first.
2. Delegate to the agent matching its route: quick, build or deep. Pass the full task and the
   triage JSON. Never pass a model parameter.
3. Then call the verifier with the risk and checks from triage.
4. If the verifier says FAIL, retry once, one step up:
   - it skipped a file or did not run the tests -> more effort (quick -> build)
   - it had full context and was still wrong   -> bigger model (build -> deep -> escalate)
5. After any escalation, ask triage to save one line to its memory:
   "<task pattern> -> <route that worked>".
```

## 6. Stop hook (`.claude/hooks/check.sh`, `chmod +x`)

```bash
#!/usr/bin/env bash
# Do not let the agent finish while the tests fail (one extra pass per turn).
input=$(cat)
[ "$(jq -r '.stop_hook_active' <<<"$input")" = "true" ] && exit 0
if ! out=$(npm test 2>&1); then
  jq -n --arg log "$(tail -n 40 <<<"$out")" \
    '{decision: "block", reason: ("Tests are failing. Fix them before you stop.\n" + $log)}'
fi
exit 0
```

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check.sh", "timeout": 300 } ] }
    ]
  }
}
```

`/tasks` shows each subagent's model and effort — check the ladder is actually being followed
instead of trusting it.
