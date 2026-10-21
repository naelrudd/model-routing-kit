#!/usr/bin/env python3
"""bench.py — measure pass rate, latency and cost per SOLVED task for your models.

Works against any [OI]-compatible /chat/completions endpoint. Stdlib only.

    export OPENAI_BASE_URL=https://api.example.com/v1
    export OPENAI_API_KEY=sk-...
    python benchmarks/bench.py --models cheap-model,mid-model,top-model --tasks tasks/

Task layout (one directory per task):

    tasks/parse-duration/task.json
    tasks/parse-duration/check.py        # exits 0 = solved
    tasks/parse-duration/files/...       # optional files copied into the workdir

task.json keys:
    prompt       (required) what the model is asked to do
    answer_file  (optional) file the reply is written to, default "solution.py"
    check        (optional) command run in the workdir, default "python check.py"

Prices (per 1M tokens) come from --prices FILE or from `usage.cost` when the endpoint reports it:
    {"cheap-model": {"in": 0.15, "out": 0.60}, ...}
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

FENCE = re.compile(r"^```(?:python|json|bash|sh)?\s*|```\s*$", re.MULTILINE)


def post(url: str, key: str, payload: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def load_tasks(root: str) -> list[dict]:
    tasks = []
    for name in sorted(os.listdir(root)):
        tdir = os.path.join(root, name)
        spec = os.path.join(tdir, "task.json")
        if not os.path.isfile(spec):
            continue
        with open(spec, encoding="utf-8") as fh:
            meta = json.load(fh)
        meta["name"] = name
        meta["dir"] = tdir
        tasks.append(meta)
    return tasks


def run_one(model: str, task: dict, args, base: str) -> dict:
    work = tempfile.mkdtemp(prefix="bench-")
    try:
        files = os.path.join(task["dir"], "files")
        if os.path.isdir(files):
            shutil.copytree(files, work, dirs_exist_ok=True)
        for extra in ("check.py",):
            src = os.path.join(task["dir"], extra)
            if os.path.isfile(src):
                shutil.copy(src, work)

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": task["prompt"]}],
            "max_tokens": args.max_tokens,
        }
        if args.effort:
            payload["reasoning"] = {"effort": args.effort}
        started = time.time()
        try:
            resp = post(f"{base}/chat/completions", args.key, payload, args.timeout)
        except urllib.error.HTTPError as exc:
            return {"model": model, "task": task["name"], "solved": False, "error": f"HTTP {exc.code}", "latency": 0.0}
        except Exception as exc:  # noqa: BLE001 - any transport failure is a failed run
            return {"model": model, "task": task["name"], "solved": False, "error": type(exc).__name__, "latency": 0.0}
        latency = time.time() - started

        usage = resp.get("usage") or {}
        text = (resp["choices"][0]["message"].get("content") or "").strip()
        if task.get("answer_file", "solution.py"):
            with open(os.path.join(work, task.get("answer_file", "solution.py")), "w", encoding="utf-8") as fh:
                fh.write(FENCE.sub("", text).strip())

        check = task.get("check", "python check.py")
        solved = subprocess.call(check, shell=True, cwd=work, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
        return {
            "model": model,
            "task": task["name"],
            "solved": solved,
            "latency": round(latency, 1),
            "in_tokens": usage.get("prompt_tokens"),
            "out_tokens": usage.get("completion_tokens"),
            "cost": usage.get("cost"),
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)


def money(row: dict, prices: dict) -> float | None:
    if row.get("cost") is not None:
        return float(row["cost"])
    price = prices.get(row["model"])
    if not price or row.get("in_tokens") is None:
        return None
    return row["in_tokens"] / 1e6 * price.get("in", 0) + row["out_tokens"] / 1e6 * price.get("out", 0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True, help="comma-separated model ids")
    ap.add_argument("--tasks", default="tasks", help="directory of task folders")
    ap.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", ""))
    ap.add_argument("--key", default=os.environ.get("OPENAI_API_KEY", ""))
    ap.add_argument("--effort", default=None, help="reasoning effort sent with every call")
    ap.add_argument("--prices", default=None, help="JSON file with per-1M prices")
    ap.add_argument("--max-tokens", type=int, default=1500)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--out", default="benchmarks/results.json")
    args = ap.parse_args()

    if not args.base_url or not args.key:
        sys.exit("bench: set OPENAI_BASE_URL and OPENAI_API_KEY (or --base-url/--key)")
    base = args.base_url.rstrip("/")
    prices = {}
    if args.prices:
        with open(args.prices, encoding="utf-8") as fh:
            prices = json.load(fh)

    tasks = load_tasks(args.tasks)
    if not tasks:
        sys.exit(f"bench: no tasks found under {args.tasks}")

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    rows = []
    for model in models:
        for task in tasks:
            row = run_one(model, task, args, base)
            row["cost"] = money(row, prices)
            rows.append(row)
            flag = "PASS" if row["solved"] else "FAIL"
            print(f"{flag}  {model:28} {task['name']:16} {row['latency']:>6}s  cost={row.get('cost')}", flush=True)

    print("\n| model | solved | latency (s) | cost / solved task |")
    print("|---|---|---|---|")
    for model in models:
        mine = [r for r in rows if r["model"] == model]
        solved = sum(1 for r in mine if r["solved"])
        lat = sum(r["latency"] for r in mine) / max(len(mine), 1)
        spent = sum(r["cost"] or 0 for r in mine)
        per = f"${spent / solved:.5f}" if solved and spent else "n/a"
        print(f"| {model} | {solved}/{len(mine)} | {lat:.1f} | {per} |")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
    print(f"\nraw rows -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
