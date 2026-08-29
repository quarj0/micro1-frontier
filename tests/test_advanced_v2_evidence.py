from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from agents.codex_advanced_v2.evidence import record_digest, validate_evidence


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def event(
    order: int,
    phase: str,
    edit_state: str,
    exit_code: int,
    changes: list[str] | None = None,
) -> dict[str, object]:
    stdout = f"event {order}\n".encode()
    stderr = b""
    value: dict[str, object] = {
        "event_id": f"ev-{order:04d}-test",
        "order": order,
        "phase": phase,
        "command": ["python", "manage.py", "test"],
        "command_text": "python manage.py test",
        "started_at": f"2026-08-29T12:00:0{order}+00:00",
        "finished_at": f"2026-08-29T12:00:0{order}+00:00",
        "exit_code": exit_code,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "stdout_excerpt": stdout.decode(),
        "stderr_excerpt": "",
        "edit_state": edit_state,
        "source_changes_before": changes or [],
        "source_changes_after": changes or [],
        "launch_error": None,
    }
    value["record_sha256"] = record_digest(value)
    return value


def raw_event(value: dict[str, object], index: int) -> dict[str, object]:
    receipt = base64.urlsafe_b64encode(
        json.dumps(
            {
                "event_id": value["event_id"],
                "record_sha256": value["record_sha256"],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).decode()
    return {
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": f"ari-evidence command {index}",
            "aggregated_output": f"unrelated human-readable output\nARI_EVIDENCE_RECEIPT={receipt}\n",
            "exit_code": value["exit_code"],
        },
    }


def successful_fixture():
    values = [
        event(1, "reproduction", "before_first_source_edit", 1),
        event(2, "investigation", "before_first_source_edit", 0),
        event(3, "focused_verification", "after_first_source_edit", 0, ["api/views.py"]),
        event(4, "broad_verification", "after_first_source_edit", 0, ["api/views.py"]),
    ]
    result = {
        "status": "repaired",
        "reproduction_event_id": values[0]["event_id"],
        "diagnosis": {
            "hypothesis": "tenant filtering is absent",
            "evidence_event_ids": [values[1]["event_id"]],
        },
        "repair": {"summary": "scope lookup", "files": ["api/views.py"]},
        "focused_verification_event_id": values[2]["event_id"],
        "broad_verification_event_id": values[3]["event_id"],
        "abstention_reason": None,
    }
    return result, values, [raw_event(value, index) for index, value in enumerate(values)]


def test_v2_qualifies_direct_structured_references_without_text_matching():
    result, values, raw = successful_fixture()

    evidence = validate_evidence(result, values, raw, ["api/views.py"], 0)

    validated_types = {
        item["type"]
        for item in evidence
        if item["evidence"].get("validated") is True
    }
    assert {"reproduction", "diagnosis", "repair", "verification"}.issubset(
        validated_types
    )
    assert not any(item["type"] == "workflow_validation" for item in evidence)


def test_v2_rejects_a_reference_without_a_raw_command_receipt():
    result, values, raw = successful_fixture()
    raw.pop(1)

    evidence = validate_evidence(result, values, raw, ["api/views.py"], 0)

    validation = next(item for item in evidence if item["type"] == "workflow_validation")
    assert any("no raw Codex command receipt" in error for error in validation["evidence"]["errors"])
    assert validation["evidence"]["validated"] is False


def test_recorder_captures_hashes_exit_and_pre_edit_state(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=workspace, check=True)
    (workspace / "tracked.py").write_text("BROKEN = True\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.py"], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "--quiet", "-m", "broken"], cwd=workspace, check=True)
    baseline = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=workspace, text=True, stdout=subprocess.PIPE, check=True
    ).stdout.strip()
    evidence_path = workspace / ".ari" / "commands.jsonl"
    environment = {
        **os.environ,
        "ARI_WORKSPACE": str(workspace),
        "ARI_BASELINE_REVISION": baseline,
        "ARI_COMMAND_EVIDENCE_PATH": str(evidence_path),
        "ARI_FIRST_EDIT_MARKER_PATH": str(workspace / ".ari" / "first-edit"),
    }

    completed = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "agents" / "codex_advanced_v2" / "ari-evidence"),
            "--phase",
            "reproduction",
            "--",
            sys.executable,
            "-c",
            "import sys; print('observed failure'); sys.exit(3)",
        ],
        cwd=workspace,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    recorded = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert completed.returncode == 3
    assert recorded["exit_code"] == 3
    assert recorded["phase"] == "reproduction"
    assert recorded["edit_state"] == "before_first_source_edit"
    assert recorded["stdout_excerpt"] == "observed failure\n"
    assert recorded["stdout_sha256"] == hashlib.sha256(b"observed failure\n").hexdigest()
    assert f"ARI_EVIDENCE_EVENT_ID={recorded['event_id']}" in completed.stderr
