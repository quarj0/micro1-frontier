"""Harness fixture that commits its change to verify baseline-relative capture."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


workspace = Path(os.environ["ARI_WORKSPACE"])
target = workspace / "agent-created.txt"
target.write_text("committed agent change\n", encoding="utf-8")
subprocess.run(["git", "add", "agent-created.txt"], cwd=workspace, check=True)
subprocess.run(
    ["git", "commit", "--quiet", "-m", "agent committed change"],
    cwd=workspace,
    check=True,
)
