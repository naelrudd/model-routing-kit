# Measured results

Everything below was run on **2026-10-22** against one [OI]-compatible marketplace
(`api.inferhub.dev/v1`). It is a snapshot, not a law: prices move, routes get funded and defunded,
models get retired. Re-run `benchmarks/bench.py` before you trust any of it.

Method: one prompt, one reply, no feedback loop, no retries. The model writes `solution.py`, a
checker the model never sees the results of decides PASS/FAIL. Cost comes from the endpoint's own
`usage.cost` field. **n = 1 task per model** — this tells you which models are usable and roughly
what they cost, not who is smarter in general.

## Coding task: `tasks/parse-duration`

A duration parser that must accept `45m`, `2h`, `1h30m`, `0m`, `90s`, `1h90m`, `"  15m "` and raise
`ValueError` on `""`, `abc`, `10`, `h`, `-5m`. Small, fully specified, edge cases spelled out —
exactly the shape of work you should be sending to a cheap tier.

| model | result | out tokens | latency | cost | notes |
|---|---|---|---|---|---|
| `cb/deepseek-v4.1-flash` | PASS | 661 | 38–134 s | $0.00001 | cheapest passing route; latency varies a lot |
| `cx/gpt-6.1-sol` | PASS | 465 | 30–38 s | $0.00007–0.00009 | 7–9× the cost, most consistent latency |
| `ali/qwen3.8-max` | PASS | 2873 | 83 s | $0.00013 | 6× the output tokens for the same result |
| `cb/glm-5.3-flash` | **FAIL** | 124 | 41 s | $0.00001 | `TypeError` on every valid input — do not route code here |
| `cb/kimi-k2.7` | **FAIL** | 1200 (capped) | 48 s | $0.00004 | burned the token budget thinking, never wrote the function |

Takeaway: the cheapest model that passes was 13× cheaper than the mid tier for the same outcome on
this task. The cheapest model overall failed. **Cheap is only cheap per solved task.**

## Tool-loop smoke test

Same prompt through a full agent CLI (run a shell command, report the number):

| model | ran the tool | correct answer |
|---|---|---|
| `cb/deepseek-v4.1-flash` | yes | yes |
| `cx/gpt-6.1-sol` | yes | yes |
| `cb/glm-5.3` | yes | yes |
| `ali/qwen3.8-max` | yes | yes |

Tool calling itself was not a differentiator; code quality was.

## Route availability

The useful part of a marketplace is knowing which routes actually serve. Probed twice, one tiny
call each:

**Served:** `cb/deepseek-v4.1-flash`, `cb/glm-5.3`, `cb/glm-5.3-flash`, `cb/kimi-k2.7`, `cb/kimi-k3`,
`cx/gpt-6.1-sol`, `ali/kimi-k3`, `ali/qwen3.8-max`, `ali/glm-5.3`

**`402 Payment Required`** (route exists, no funded seller for this account): `cx/gpt-6-luna`,
`cx/gpt-5.6-luna`, `zai/glm-5.3-flash`, `kiro/gpt-5.6-luna`, `ocg/glm-5.3-flash`

**`429 Too Many Requests`**: `cx/gpt-6-astra`, `cb/minimax-m3`, `mm/MiniMax-M3`, `grok/grok-4.7`

**`503 Service Unavailable`**: `ocg/deepseek-v4.1-flash`, `ocg/kimi-k2.7-code`, `ocg/gpt-6-luna`,
`cmc/gpt-6-luna`, `cmc/deepseek/deepseek-v4.1-flash`

The cheapest advertised seller is frequently the one that is not serving. A route table built from
the price list alone would have picked `cx/gpt-6-luna` ($0.10/$0.50) and failed on the first call.
Probe first, then pin.

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
