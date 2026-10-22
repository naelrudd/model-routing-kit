# model-routing-kit

Route coding tasks to the **cheapest model tier that can actually finish them**, verify with code,
and escalate only when the check fails. Works with any agent CLI that takes a model flag:
Hermes, [CC], Codex, or your own.

```
route auto "add pagination to /api/orders" --verify "npm test"
```

New here? Start with **[GETTING-STARTED.md](GETTING-STARTED.md)**.

```
== route: build  model: cx/gpt-6.1-sol  effort: medium
...agent works...
$ npm test
route: check passed on 'build' (94s)
```

If the check fails it climbs exactly one tier (more effort first, then a bigger model), then stops
and tells you. No silent "done".

---

## The five rules

1. **Tune effort before you touch models.** Most tasks do not need `high`. It is the cheapest lever
   you have, and switching models mid-task costs more than switching effort (prompt-cache miss).
2. **Do not default to the top model.** Keep it for escalation. One tier below solves nearly the
   same share of tasks for a fraction of the price.
3. **Route by task type and risk**, with plain if/else rules — not a classifier you cannot read.
4. **Verify with code** (tests, types, lint). On FAIL escalate once: more effort first, then a
   bigger model. If the agent had full context and was still wrong, the model was the problem; if it
   skipped a file or never ran the tests, the effort was.
5. **Log every miss and turn it into a rule.** `LESSONS.md` ships with the format.

## The three routes

| route | use it for | effort | checks |
|---|---|---|---|
| `quick` | small, well-specified, one or two files, no design decisions | low | tests for the touched files |
| `build` | normal feature or bug fix with a known shape | medium | tests + typecheck + lint |
| `deep` | architecture, migrations, auth, payments, data, anything unclear | xhigh | full suite + typecheck + lint + read the diff |

Plus `verify`: a separate pass that only runs checks and never edits code.

`route auto` asks a cheap model to classify the task first (JSON in, JSON out) and falls back to
`build` whenever the answer is not parseable. Classification is cheap; a wrong classification that
costs you a failed run is not — that is why every route still ends in a check.

## Install

New here? **[GETTING-STARTED.md](GETTING-STARTED.md)** has three paths — 5 minutes by hand, 10
minutes with the CLI, or wiring it into your agent permanently.

```bash
git clone https://github.com/naelrudd/model-routing-kit
cd model-routing-kit
export PATH="$PWD/bin:$PATH"

# point it at your models
$EDITOR routes.json     # routes: model + effort; backends: command template
route quick "rename foo() to bar() in src/" --dry-run
```

`bin/route` is stdlib Python 3 — no dependencies, no lockfile, no daemon. `{task}`, `{model}` and
`{effort}` are the only placeholders a backend command needs.

## Backends

| backend | command it runs |
|---|---|
| `hermes` | `hermes chat -q "{task}" -m {model} --reasoning {effort} -Q` |
| `claude` | `claude -p "{task}" --model {model}` (effort comes from the agent file) |
| `codex` | `codex exec "{task}" -m {model} -c model_reasoning_effort={effort}` |
| `custom` | anything you like — keep the three placeholders |

`--verify` runs through the platform shell (`bash` on POSIX, `cmd.exe` on Windows), so keep the
check command simple or wrap it in a script.

## Why this is not another auto-router

Learned routers have a documented failure mode: they collapse toward sending everything to the
strongest model, and they degrade on task types they were not trained on. A rule table cannot drift
silently, costs nothing to read, and you can diff it. This kit keeps the router boring on purpose
and puts the intelligence in the **check**, which is the part that actually knows whether the work
was right.

The honest expectations, from published measurements:

- one tier below the top, at default effort: roughly **5× cheaper per solved task** at the same solve rate
- routing on top of that: **35–65% lower cost** at the same quality in production write-ups (self-reported)
- always using the cheapest model: 15–19× cheaper, but **8–15 points fewer tasks solved** — that is the trap this kit avoids
- cascades only beat a single strong model while the checker is right more than ~90% of the time

## Repository layout

```
routes.json              # the route table: models, efforts, checks, backend commands
bin/route                # the dispatcher: run, verify, escalate once, stop
prompts/triage.md        # classifier prompt (JSON out)
prompts/verifier.md      # PASS/FAIL with evidence, never edits
presets/inferhub.json    # measured model ladder for an OpenAI-compatible marketplace
benchmarks/bench.py      # measure your own models before you trust the table
benchmarks/RESULTS.md    # numbers this repo was built from, with the method
adapters/                # drop-in config for Hermes, [CC], Codex
tests/smoke.sh           # offline test of the dispatcher (no API calls)
LESSONS.md               # log a miss, get a rule
```

## Measure before you trust it

```bash
export OPENAI_BASE_URL=https://your-endpoint/v1 OPENAI_API_KEY=sk-...
python benchmarks/bench.py --models cheap-model,mid-model,top-model --tasks tasks/
```

It writes each model's answer into its own workdir, runs the task's check, and prints pass rate,
latency, tokens and **cost per solved task** — the only cost number that means anything. A model
that is 3× cheaper per token and 20% more likely to fail is not cheaper.

## Prior art

Built on published measurements rather than vibes: Anthropic's effort and advisor write-ups, the
GPT-6 model-selection guidance, LangChain's routing A/B test, Cursor and Databricks production
write-ups, and the RouterBench / SWE-Router / cascade-routing papers. Numbers are quoted with their
source in `benchmarks/RESULTS.md`. Vendor claims are labelled as such.

MIT licensed. No telemetry, no keys in the repo, nothing to phone home.
