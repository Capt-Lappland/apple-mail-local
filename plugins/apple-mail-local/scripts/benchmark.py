#!/usr/bin/env python3
"""Run local control-plane benchmarks without opening or reading Apple Mail."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "scripts" / "server.py"
JXA_PATH = ROOT / "scripts" / "mail_automation.jxa"


def percentile_95(values: list[float]) -> float:
    return sorted(values)[max(0, int(len(values) * 0.95) - 1)]


def timing_summary(values: list[float]) -> dict[str, float]:
    return {
        "median": round(statistics.median(values), 2),
        "p95": round(percentile_95(values), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.iterations <= 500:
        parser.error("--iterations must be between 1 and 500")

    payload = (
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        + "\n"
        + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        + "\n"
    ).encode()
    jxa_times = []
    mcp_times = []
    for _ in range(args.iterations):
        started = time.perf_counter()
        subprocess.run(
            ["/usr/bin/osascript", "-l", "JavaScript", str(JXA_PATH)],
            input=b'{"operation":"healthcheck","arguments":{}}',
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=True,
        )
        jxa_times.append((time.perf_counter() - started) * 1000)

        started = time.perf_counter()
        subprocess.run(
            [sys.executable, str(SERVER_PATH)],
            input=payload,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=True,
        )
        mcp_times.append((time.perf_counter() - started) * 1000)

    spec = importlib.util.spec_from_file_location("apple_mail_server", SERVER_PATH)
    server = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(server)

    class CountingRunner:
        def __init__(self):
            self.calls = 0

        def run(self, operation, arguments):
            self.calls += 1
            return {"accounts": []}

    runner = CountingRunner()
    cache = server.TopologyCache()
    for _ in range(args.iterations):
        server.call_tool(
            "mail_list_accounts", {}, enable_drafts=False, runner=runner, cache=cache
        )

    print(
        json.dumps(
            {
                "iterations": args.iterations,
                "jxa_healthcheck_ms": timing_summary(jxa_times),
                "mcp_initialize_and_list_ms": timing_summary(mcp_times),
                "repeated_topology_requests": {
                    "requests": args.iterations,
                    "automation_processes": runner.calls,
                },
                "mail_accessed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
