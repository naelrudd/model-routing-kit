# Lessons

One line per miss. A miss is a run where the check failed, or where the work passed and something
was still wrong afterwards. The point is not the log — it is that the next triage reads it.

Format:

```
<task pattern> -> <route that actually worked>   [what went wrong on the cheaper route]
```

## Example (delete these, they are illustrations)

```
rename a symbol across 20 files           -> quick    [fine at low effort]
add a field to a Prisma model + migration -> deep     [build forgot the rollback path]
flaky test with no repro                  -> deep     [quick "fixed" it by retrying]
CSS-only layout tweak                     -> quick    [never escalate these]
```

## Rules for keeping this useful

1. Write the pattern, not the ticket. `auth token refresh` generalises; `PROJ-4127` does not.
2. Only log a miss that changed a decision. A log of every failure is noise.
3. Review the log every few weeks and fold the repeated patterns into `routes.json` or the triage
   prompt. Rules that are never re-read go stale, and a stale rule is worse than no rule.
4. When a model is retired or a price changes, re-run `benchmarks/bench.py` before editing a route.

## Log
