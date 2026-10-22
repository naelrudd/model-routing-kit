# Getting started

Three ways in, cheapest first. Everything here works from a clone; nothing needs an API key
except the raw-HTTP backend.

```bash
git clone https://github.com/naelrudd/model-routing-kit
cd model-routing-kit
```

## Path A — 5 minutes, no install: use the ladder by hand

The route table is just three model names and three effort levels. Read
[`presets/inferhub.json`](presets/inferhub.json) and copy the model ids into whatever you already
use:

| you are about to… | use | effort |
|---|---|---|
| rename something, add a guard clause, tweak CSS | `cb/deepseek-v4.1-flash` | low |
| build a feature or fix a real bug | `cx/gpt-6.1-sol` | medium |
| touch auth, money, migrations, or anything unclear | `cx/gpt-6.1-sol` | xhigh |
| check finished work | `cb/deepseek-v4.1-flash` | low |

Then, before you call it done, run the check yourself. That is the whole method; the rest is
automation of it.

## Path B — 10 minutes: one command per task

```bash
export PATH="$PWD/bin:$PATH"     # Windows: use `python bin/route …` instead

# a small change, with a check that decides success
route quick "rename foo() to bar() across src/" --verify "npm test"

# a normal feature
route build "add cursor pagination to /api/orders" --verify "npm test"

# let a cheap model classify the task first
route auto "the checkout webhook double-charges on retry" --verify "pytest -q"
```

What happens: the route's model and effort are pinned for that run, the agent works, then your
`--verify` command decides. If it fails, one escalation — more effort first, then a different model
family — then a stop with a non-zero exit code. Nothing silently claims success.

Useful flags:

```
--dry-run            print the command it would run, execute nothing
--max-escalations N  how far to climb (default 1; 0 = never escalate)
--backend NAME       hermes | claude | codex | curl | custom (see routes.json)
--preset FILE        use a different route table
```

Point it at your own models by editing `routes.json`: each route is `model` + `effort` + `checks`,
each backend is a command template with `{task}`, `{model}`, `{effort}`.

## Path C — make it the default: wire the agent itself

So you never type `route` at all. Per tool:

- **Hermes** — [`adapters/hermes.md`](adapters/hermes.md): main session on the build tier at
  `medium`, subagents on the cheap tier at `low`, plus a fallback chain so a 402 does not kill the
  session.
- **[CC]** — [`adapters/claude-code.md`](adapters/claude-code.md): `triage` / `quick` / `build` /
  `deep` / `verifier` agents with a fixed model + effort each, and a Stop hook that refuses to
  finish while tests fail.
- **Codex** — [`adapters/codex.md`](adapters/codex.md): the same ladder as `.codex/agents/*.toml`.

## Measure before you trust the table

The route table is only as good as the numbers behind it, and models get retired weekly:

```bash
export OPENAI_BASE_URL=https://your-endpoint/v1 OPENAI_API_KEY=sk-...
python benchmarks/bench.py --models model-a,model-b --tasks tasks/
```

Add your own tasks by copying `tasks/parse-duration/`: a `task.json` with the prompt, a `check.py`
that exits 0 when the work is right. The table it prints is cost **per solved task** — the only cost
number that means anything.

## Verify the kit itself

```bash
bash tests/smoke.sh     # 8 assertions, offline, no API calls
```

## The one rule

If a route has no check, it has no claim. `--verify` is not decoration: it is the part that knows
whether the work was right. Skip it and you have just built a cheaper way to be wrong.
