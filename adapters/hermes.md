# Hermes adapter

Hermes reads three levers from `~/.hermes/config.yaml` (Windows: `%LOCALAPPDATA%\hermes\config.yaml`):

| lever | what it does |
|---|---|
| `model.default` | the model the main session runs on — the `build` route |
| `agent.reasoning_effort` | the effort for the main session (not in the shipped defaults; set with `--force`) |
| `delegation.model` + `delegation.reasoning_effort` | what subagents (`delegate_task`) run on — the `quick` route |
| `fallback_model` | a chain used when the primary route fails with 402/429/503 |

```bash
hermes config set model.default <build-model>
hermes config set agent.reasoning_effort medium --force
hermes config set delegation.provider <provider>
hermes config set delegation.model <cheap-model>
hermes config set delegation.base_url https://your-endpoint/v1
hermes config set delegation.reasoning_effort low
hermes config set delegation.max_concurrent_children 5
```

Fallback chain (a list, so it goes in as JSON):

```bash
hermes config set fallback_model '[{"provider":"custom","model":"<cheap-model>","base_url":"https://your-endpoint/v1","key_env":"YOUR_KEY_ENV"}]'
```

Why the split: the main session is the part that has to hold the whole task in its head, so it gets
the `build` tier. Subagents get handed a bounded, fully-specified goal, so they get the cheap tier at
low effort. Escalation is the `route` CLI, which pins a model per run:

```bash
route deep "migrate the billing schema" --backend hermes --verify "pytest -q"
```

`route --backend hermes` shells out to `hermes chat -q "<task>" -m <model> --reasoning <effort> -Q`,
so it uses a separate session and a separate prompt cache. That is the right trade for a task you
would otherwise escalate mid-session anyway — switching models mid-task re-reads the whole context at
full price.

Verify what actually ran:

```bash
hermes config get model.default
hermes config get delegation.model
```

## Notes that cost us time

- `agent.reasoning_effort` is read at runtime but is not in the shipped defaults, so
  `hermes config set` refuses it without `--force`. It is still the key that works.
- `hermes config check` prints mostly environment variables; grep it for `error`/`warn` before
  assuming a clean bill of health.
- The config file is protected from agent-side writes. Use `hermes config set`, not a file edit.
- Subagents cannot be given a per-call model. `delegation.model` is one global pin — that is why the
  route table lives in this CLI instead of in the delegation call.
