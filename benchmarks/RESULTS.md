# Measured results

No measured results are shipped with this kit. The shipped `routes.json` uses
placeholders only, and no provider is hardcoded — bring your own endpoint and key, run
`benchmarks/bench.py` against your own models, and record the results here before you
trust any cost claim. Prices move, routes get funded and defunded, models get retired.

Method: one prompt, one reply, no feedback loop, no retries. The model writes `solution.py`, a
checker the model never sees the results of decides PASS/FAIL. Cost comes from the endpoint's own
`usage.cost` field when it reports one. Record the endpoint, the date, and how many tasks
(`n`) each model ran — one task per model tells you which models are usable and roughly
what they cost, not who is smarter in general.

**Cheap is only cheap per solved task.** A cheaper model that fails is not cheaper.

## Your own results

Run the bench, then paste the table here:

```bash
export OPENAI_BASE_URL=https://your-endpoint/v1 OPENAI_API_KEY=your-key-here
python benchmarks/bench.py --models cheap-model,mid-model,top-model --tasks tasks/
```

| model | result | out tokens | latency | cost | notes |
|---|---|---|---|---|---|
| _no results yet — run the bench above_ | | | | | |

## Published numbers this repo relies on

Quoted with their source, vendor claims labelled:

| claim | source |
|---|---|
| one tier below the top: ~5.4× cheaper per solved task at the same solve rate (92.8% @ $0.22 vs 92.3% @ $1.19) | Anthropic, model docs |
| `medium` ≈ 2.5 points below `high` on a SWE-bench Pro subset for ~70% of the cost | Anthropic, effort docs |
| routing cut median cost 64% ($0.94 vs $2.61) at the same merged-PR rate, 973-thread A/B | LangChain (self-reported) |
| cascade + routing: ~60% lower cost at near-top-model satisfaction | Cursor (self-reported) |
| routing beat every single model at 65% of the top model's cost per task | Databricks (self-reported) |
| cascades beat every single model while the checker errs ≤10%, degrade fast above 20% | RouterBench paper |
| always-cheapest: 15–19× cheaper per solved task, 8–15 points fewer solved | computed from SWE-Router data |
| routing from the prompt alone did not beat a trivial baseline on SWE-bench | SWE-Router paper |

The last two are why this kit keeps a check in the loop instead of trusting a classifier.
