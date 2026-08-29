"""Validate agent-authored evidence against raw Codex command events."""

from __future__ import annotations

import shlex
from typing import Any


def command_records(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "command_execution":
            continue
        records.append(
            {
                "index": index,
                "command": item.get("command"),
                "output": item.get("aggregated_output"),
                "exit_code": item.get("exit_code"),
            }
        )
    return records


def first_source_edit(events: list[dict[str, Any]]) -> int | None:
    for index, event in enumerate(events):
        if event.get("type") != "item.completed":
            continue
        item = event.get("item")
        if not isinstance(item, dict) or item.get("type") != "file_change":
            continue
        changes = item.get("changes")
        if not isinstance(changes, list):
            continue
        for change in changes:
            if not isinstance(change, dict):
                continue
            path = str(change.get("path", "")).replace("\\", "/")
            if "/.ari/" not in path:
                return index
    return None


def corroborate(
    record: object,
    commands: list[dict[str, Any]],
    *,
    before: int | None = None,
    after: int | None = None,
    require_exit_code: bool = True,
) -> dict[str, Any] | None:
    if not isinstance(record, dict):
        return None
    command = record.get("command")
    observed = record.get("observed")
    if not isinstance(command, str) or not command.strip():
        return None
    if not isinstance(observed, str) or not observed.strip():
        return None
    expected_exit = record.get("exit_code")
    if require_exit_code and not isinstance(expected_exit, int):
        return None

    for candidate in commands:
        index = candidate["index"]
        if before is not None and index >= before:
            continue
        if after is not None and index <= after:
            continue
        raw_command = candidate.get("command")
        raw_output = candidate.get("output")
        if not isinstance(raw_command, str) or not _command_matches(command, raw_command):
            continue
        if not isinstance(raw_output, str) or not _observed_lines_in_order(
            observed, raw_output
        ):
            continue
        if require_exit_code and candidate.get("exit_code") != expected_exit:
            continue
        return candidate
    return None


def _command_matches(reported: str, raw_command: str) -> bool:
    if reported in raw_command:
        return True
    try:
        arguments = shlex.split(raw_command)
    except ValueError:
        return False
    if len(arguments) >= 3 and arguments[-2] == "-lc":
        shell_command = arguments[-1]
        return reported == shell_command or reported in shell_command
    return False


def _observed_lines_in_order(observed: str, raw_output: str) -> bool:
    """Allow concise excerpts while requiring every reported line in real output."""

    position = 0
    lines = [line.strip() for line in observed.splitlines() if line.strip()]
    if not lines:
        return False
    for line in lines:
        found = raw_output.find(line, position)
        if found < 0:
            return False
        position = found + len(line)
    return True


def _diagnosis_is_corroborated(
    diagnosis: object,
    commands: list[dict[str, Any]],
    edit_index: int,
) -> bool:
    if not isinstance(diagnosis, dict):
        return False
    hypothesis = diagnosis.get("hypothesis")
    evidence = diagnosis.get("evidence")
    if not isinstance(hypothesis, str) or not hypothesis.strip():
        return False
    if not isinstance(evidence, list) or not evidence:
        return False
    return all(
        corroborate(
            item,
            commands,
            before=edit_index,
            require_exit_code=False,
        )
        is not None
        for item in evidence
    )


def should_retry(result: object, events: list[dict[str, Any]]) -> bool:
    if not isinstance(result, dict) or result.get("status") != "verification_failed":
        return False
    edit_index = first_source_edit(events)
    if edit_index is None:
        return False
    commands = command_records(events)
    reproduction = corroborate(
        result.get("reproduction"), commands, before=edit_index
    )
    if reproduction is None or reproduction.get("exit_code") == 0:
        return False
    if not _diagnosis_is_corroborated(result.get("diagnosis"), commands, edit_index):
        return False
    if not isinstance(result.get("repair"), dict):
        return False
    for field in ("focused_verification", "regression_verification"):
        record = corroborate(result.get(field), commands, after=edit_index)
        if record is not None and record.get("exit_code") != 0:
            return True
    return False


def merge_retry(first: dict[str, Any], retry: dict[str, Any]) -> dict[str, Any]:
    """Carry immutable pre-edit evidence into the controller-granted retry result."""

    return {
        **retry,
        "reproduction": first.get("reproduction"),
        "diagnosis": first.get("diagnosis"),
        "repair": retry.get("repair") or first.get("repair"),
    }


def validate_evidence(
    result: object,
    events: list[dict[str, Any]],
    changed_files: list[str],
    retry_count: int,
) -> list[dict[str, Any]]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return [
            {
                "type": "workflow_validation",
                "evidence": {
                    "validated": False,
                    "errors": ["final response is not a JSON object"],
                    "retry_count": retry_count,
                },
            }
        ]

    status = result.get("status")
    if status == "abstained":
        reason = result.get("abstention_reason")
        validated = isinstance(reason, str) and bool(reason.strip())
        return [
            {
                "type": "abstention",
                "evidence": {
                    "validated": validated,
                    "reason": reason,
                    "retry_count": retry_count,
                },
            }
        ]

    if status != "repaired":
        errors.append(f"terminal status is {status!r}, not 'repaired'")

    edit_index = first_source_edit(events)
    if edit_index is None:
        errors.append("no source edit was recorded")
        edit_index = len(events)
    commands = command_records(events)

    reproduction = corroborate(
        result.get("reproduction"), commands, before=edit_index
    )
    if reproduction is None:
        errors.append("reproduction command/output was not corroborated before editing")
    elif reproduction.get("exit_code") == 0:
        errors.append("reproduction did not fail with a non-zero exit status")

    diagnosis = result.get("diagnosis")
    if not _diagnosis_is_corroborated(diagnosis, commands, edit_index):
        errors.append("diagnosis lacks corroborated pre-edit command evidence")

    repair = result.get("repair")
    reported_files: set[str] = set()
    if isinstance(repair, dict) and isinstance(repair.get("files"), list):
        reported_files = {
            str(path) for path in repair["files"] if isinstance(path, str) and path
        }
    changed = set(changed_files)
    if not reported_files or not reported_files.issubset(changed):
        errors.append("reported repair files do not match the repository patch")
    production_files = {
        path
        for path in changed
        if not path.endswith("tests.py")
        and "/tests/" not in f"/{path}"
        and not path.rsplit("/", 1)[-1].startswith("test_")
        and not path.startswith(".ari/")
        and path != "ISSUE.md"
    }
    if not production_files:
        errors.append("repair did not change a production file")

    focused = corroborate(
        result.get("focused_verification"), commands, after=edit_index
    )
    regression = corroborate(
        result.get("regression_verification"), commands, after=edit_index
    )
    if focused is None or focused.get("exit_code") != 0:
        errors.append("focused verification was not corroborated as passing")
    if regression is None or regression.get("exit_code") != 0:
        errors.append("broader regression verification was not corroborated as passing")
    if (
        focused is not None
        and regression is not None
        and focused.get("index") == regression.get("index")
    ):
        errors.append("focused and broader verification must be distinct executions")

    if errors:
        return [
            {
                "type": "workflow_validation",
                "evidence": {
                    "validated": False,
                    "errors": errors,
                    "retry_count": retry_count,
                    "status": status,
                },
            }
        ]

    return [
        {
            "type": "reproduction",
            "evidence": {
                **result["reproduction"],
                "validated": True,
                "event_index": reproduction["index"],
            },
        },
        {
            "type": "diagnosis",
            "evidence": {
                **diagnosis,
                "validated": True,
            },
        },
        {
            "type": "repair",
            "evidence": {
                **repair,
                "validated": True,
                "changed_files": sorted(changed),
            },
        },
        {
            "type": "verification",
            "evidence": {
                "validated": True,
                "focused": result["focused_verification"],
                "regression": result["regression_verification"],
                "retry_count": retry_count,
            },
        },
    ]
