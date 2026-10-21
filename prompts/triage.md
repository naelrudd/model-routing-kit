Classify this coding task. Reply with JSON only — no prose, no markdown fences.

{"route": "quick|build|deep", "risk": "low|medium|high", "checks": ["tests", "typecheck", "lint", "review"]}

Rules:

- **quick** — small and well-specified: one or two files, no design decisions, the shape of the fix
  is already obvious. Rename, small refactor, add a guard clause, fix a typo-level bug.
- **build** — a normal feature or bug fix with a known shape: several files, a test or two to write,
  no new architecture.
- **deep** — architecture, migrations, auth, payments, data modelling, concurrency, or anything
  genuinely unclear. Also: anything that touches secrets, money, or user data.

Risk:

- **low** — reversible, covered by tests, nothing runs in production.
- **medium** — touches shared code, a schema, or a dependency.
- **high** — auth, payments, migrations, data deletion, anything that cannot be undone by `git revert`.

Checks — pick the cheapest set that would actually catch a wrong answer:

- `tests` — there are tests covering the touched code
- `typecheck` — a type system exists and the change touches types
- `lint` — the repo has a linter configured
- `review` — a human or a second model must read the diff

If the task is ambiguous, prefer the higher route and the higher risk. A mis-routed task that fails
a check costs one escalation; a mis-routed task that silently passes costs a bug in production.

Read `LESSONS.md` first if it exists. Past misses are better evidence than your intuition about
this prompt.

Task:

{{TASK}}
