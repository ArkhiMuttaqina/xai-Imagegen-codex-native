#!/usr/bin/env python3
"""Offline MCP initialize/tools-list smoke test."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "plugins" / "hashmicro-imagegen-native" / "scripts" / "mcp_server.py"


def main() -> None:
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
    ]
    payload = "".join(json.dumps(request) + "\n" for request in requests)
    result = subprocess.run(
        [sys.executable, str(SERVER)],
        input=payload,
        text=True,
        capture_output=True,
        check=True,
    )
    responses = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if len(responses) != 2:
        raise SystemExit(f"Expected two MCP responses, received {len(responses)}")
    tools = responses[1]["result"]["tools"]
    names = {tool["name"] for tool in tools}
    expected = {
        "hashmicro_generate_image",
        "hashmicro_edit_image",
        "hashmicro_get_image_result",
    }
    if names != expected:
        raise SystemExit(f"Unexpected tools: {sorted(names)}")
    print(f"MCP smoke test passed: {', '.join(sorted(names))}")


if __name__ == "__main__":
    main()

