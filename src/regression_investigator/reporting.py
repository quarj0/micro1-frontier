from __future__ import annotations

import json
from pathlib import Path

from .models import RunReport


def write_report(report: RunReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "patch.diff").write_text(report.patch, encoding="utf-8")
    (output_dir / "agent.stdout.log").write_text(report.agent.stdout, encoding="utf-8")
    (output_dir / "agent.stderr.log").write_text(report.agent.stderr, encoding="utf-8")
    (output_dir / "evaluator.stdout.log").write_text(
        report.evaluator.stdout, encoding="utf-8"
    )
    (output_dir / "evaluator.stderr.log").write_text(
        report.evaluator.stderr, encoding="utf-8"
    )
    if report.final_response is not None:
        (output_dir / "final-response.md").write_text(
            report.final_response, encoding="utf-8"
        )

    status = "PASS" if report.evaluator.passed else "FAIL"
    markdown = f"""# Benchmark run: {report.case_id}

- Run: `{report.run_id}`
- Mode: `{report.mode}`
- Agent state: `{report.agent.state}` ({report.agent.runtime_seconds:.3f}s)
- Evaluator: **{status}** ({report.evaluator.runtime_seconds:.3f}s)
- Changed files: {len(report.patch_files)}
- Trajectory events: {report.trajectory_events}
- Trajectory error: {report.trajectory_error or "none"}
- Usage error: {report.usage_error or "none"}

## Usage

```json
{json.dumps(report.usage, indent=2, sort_keys=True)}
```

## Metrics

```json
{json.dumps(report.metrics, indent=2, sort_keys=True)}
```
"""
    (output_dir / "report.md").write_text(markdown, encoding="utf-8")
