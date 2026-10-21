import sys

from solution import parse_duration

CASES = [("45m", 2700), ("2h", 7200), ("1h30m", 5400), ("0m", 0), ("90s", 90), ("1h90m", 9000), ("  15m ", 900)]
INVALID = ["", "abc", "10", "h", "-5m"]

fails = []
for raw, expected in CASES:
    try:
        got = parse_duration(raw)
        if got != expected:
            fails.append(f"{raw!r} -> {got} (want {expected})")
    except Exception as exc:  # noqa: BLE001 - any raise on a valid input is a failure
        fails.append(f"{raw!r} raised {exc!r} (want {expected})")

for raw in INVALID:
    try:
        parse_duration(raw)
        fails.append(f"{raw!r} did not raise ValueError")
    except ValueError:
        pass
    except Exception as exc:  # noqa: BLE001 - wrong exception type is a failure
        fails.append(f"{raw!r} raised {type(exc).__name__}, want ValueError")

if fails:
    print("FAIL: " + " | ".join(fails))
    sys.exit(1)
print("PASS")
