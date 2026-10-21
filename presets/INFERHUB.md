# inferhub.dev preset

`presets/inferhub.json` is a route table built from measurements on `api.inferhub.dev/v1`, not from
its price list. That distinction is the whole point: the cheapest advertised route was also the one
returning `402 Payment Required`.

Snapshot: **2026-10-22**. Re-probe before you rely on it.

## The ladder

| route | model | effort | why this one |
|---|---|---|---|
| `quick` | `cb/deepseek-v4.1-flash` | low | cheapest route that passed the code bench; $0.15/$0.60 per 1M |
| `build` | `cx/gpt-6.1-sol` | medium | tier below the top model, 7–9× the quick route per task, most stable latency |
| `deep` | `cx/gpt-6.1-sol` | xhigh | same model, more thinking — cheaper than switching up a tier |
| `escalate` | `ali/kimi-k3` | high | different model family, so a wrong assumption does not repeat |
| `verify` | `cb/deepseek-v4.1-flash` | low | running the checks is mechanical work |

Usage:

```bash
export OPENAI_BASE_URL=https://api.inferhub.dev/v1 OPENAI_API_KEY=...
route build "add cursor pagination to /api/orders" --preset presets/inferhub.json --verify "npm test"
```

Or, without any agent CLI installed, drive the raw endpoint:

```bash
route quick "explain this stack trace" --preset presets/inferhub.json --backend curl
```

## What the probe found

**Serving** (a tiny call returned 200): `cb/deepseek-v4.1-flash`, `cb/glm-5.3`,
`cb/glm-5.3-flash`, `cb/kimi-k2.7`, `cb/kimi-k3`, `cx/gpt-6.1-sol`, `ali/kimi-k3`,
`ali/qwen3.8-max`, `ali/glm-5.3`

**Not serving**, by failure mode:

- `402 Payment Required` — `cx/gpt-6-luna`, `cx/gpt-5.6-luna`, `zai/glm-5.3-flash`,
  `kiro/gpt-5.6-luna`, `ocg/glm-5.3-flash`
- `429 Too Many Requests` — `cx/gpt-6-astra`, `cb/minimax-m3`, `mm/MiniMax-M3`, `grok/grok-4.7`
- `503 Service Unavailable` — `ocg/deepseek-v4.1-flash`, `ocg/kimi-k2.7-code`, `ocg/gpt-6-luna`,
  `cmc/gpt-6-luna`, `cmc/deepseek/deepseek-v4.1-flash`

**Passed the probe but failed the code bench** — `cb/glm-5.3-flash` (raised `TypeError` on every
valid input), `cb/kimi-k2.7` (spent the whole token budget thinking, never wrote the function).

The full numbers, including cost per solved task, are in `benchmarks/RESULTS.md`.

## Notes for a marketplace

Two things a routing preset like this makes obvious from the outside:

1. **A price list is not availability.** Routes priced at the very bottom are frequently unfunded for
   a given account. Publishing a per-route "last probed OK at" field would be worth more to users
   than the price list itself.
2. **Namespaces are not tiers.** `cb/gpt-5.3-codex` and `cx/gpt-6.1-sol` are the same family at
   wildly different resale prices; a user cannot tell from the id which is the sane default. One
   curated ladder per workload (chat / code / long-context) would remove that guesswork.

If you run the marketplace and want this as a maintained preset, the route table is a single JSON
file with no dependencies — it can be generated from your own `/v1/models` output plus a probe.
