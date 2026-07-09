"""A tiny deterministic local "agent" for the regression-pack refresh flow.

`entropy-loop refresh-pack` sends one case per run on stdin as JSON and reads the
candidate output from stdout. This script emits valid JSON, so the refreshed pack
passes a `require_non_empty` + `expect_json` policy.

It makes no network calls, needs no secrets, and is fully deterministic.

Usage (normally invoked by `refresh-pack`)::

    echo '{"case_id": "json-1", "task": "..."}' | python examples/json_agent_agent.py
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    """Read a case from stdin and print a valid-JSON candidate output."""
    raw = sys.stdin.read()
    try:
        case = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        case = {}
    output = {"case": case.get("case_id", ""), "task": case.get("task", ""), "ok": True}
    print(json.dumps(output))


if __name__ == "__main__":
    main()
