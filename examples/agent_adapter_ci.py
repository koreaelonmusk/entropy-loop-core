"""Refresh a regression pack from a live local agent, then run the gate.

Run it with::

    python examples/agent_adapter_ci.py

This is the two-step v0.6.0 flow in code:

1. run an explicit local agent command per case and capture fresh outputs
   (`refresh-pack`), then
2. verify those outputs with the deterministic gate (`run-pack`).

Entropy Loop Core runs the command only because it is passed explicitly. No
shell, no secret injection, and no network calls from the library itself.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from entropy_loop_core import (
    AgentCommand,
    CommandAgentAdapter,
    RegressionPackRefresher,
    RegressionPackRunner,
    load_regression_pack,
)

PACK = Path(__file__).parent / "json_agent_guard.pack.json"
AGENT = Path(__file__).parent / "json_agent_agent.py"


def main() -> None:
    """Refresh the example pack from the example agent, then gate it."""
    # 1. Refresh: run the local agent command per case, capture fresh outputs.
    command = AgentCommand(argv=[sys.executable, str(AGENT)], timeout_seconds=30)
    adapter = CommandAgentAdapter(command)

    with tempfile.TemporaryDirectory() as directory:
        refreshed_path = Path(directory) / "refreshed.pack.json"
        refresh = RegressionPackRefresher().refresh_pack_file(
            PACK, refreshed_path, adapter
        )
        print(refresh.summary)

        # 2. Gate: verify the refreshed outputs deterministically.
        result = RegressionPackRunner().run_pack(load_regression_pack(refreshed_path))
        print(result.summary)
        print(f"CI exit code would be: {0 if result.success else 1}")


if __name__ == "__main__":
    main()
