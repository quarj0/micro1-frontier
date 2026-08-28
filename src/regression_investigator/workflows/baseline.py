from __future__ import annotations

from pathlib import Path


def render_baseline_prompt(template_path: Path, issue_text: str) -> str:
    template = template_path.read_text(encoding="utf-8")
    return template.replace("{{ISSUE_REPORT}}", issue_text.strip())

