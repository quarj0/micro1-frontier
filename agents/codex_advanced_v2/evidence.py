"""Validate structured evidence references against recorder and raw Codex events."""

from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime
from typing import Any


RECEIPT_PATTERN = re.compile(r"ARI_EVIDENCE_RECEIPT=([A-Za-z0-9_=-]+)")
PRE_EDIT = "before_first_source_edit"
POST_EDIT = "after_first_source_edit"


def record_digest(record: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in record.items() if key != "record_sha256"}
    payload = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


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
                "raw_event_index": index,
                "command": item.get("command"),
                "output": item.get("aggregated_output"),
                "exit_code": item.get("exit_code"),
            }
        )
    return records


def _receipts(raw_output: object) -> list[dict[str, str]]:
    if not isinstance(raw_output, str):
        return []
    decoded: list[dict[str, str]] = []
    for encoded in RECEIPT_PATTERN.findall(raw_output):
        try:
            value = json.loads(base64.urlsafe_b64decode(encoded).decode())
        except (ValueError, json.JSONDecodeError):
            continue
        if (
            isinstance(value, dict)
            and isinstance(value.get("event_id"), str)
            and isinstance(value.get("record_sha256"), str)
        ):
            decoded.append(value)
    return decoded


def corroborated_events(
    evidence_events: list[dict[str, Any]], raw_events: list[dict[str, Any]]
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    errors: list[str] = []
    by_id: dict[str, dict[str, Any]] = {}
    raw_receipts: dict[tuple[str, str], dict[str, Any]] = {}
    for command in command_records(raw_events):
        for receipt in _receipts(command["output"]):
            raw_receipts[(receipt["event_id"], receipt["record_sha256"])] = command

    previous_order = 0
    seen_ids: set[str] = set()
    for record in evidence_events:
        event_id = record.get("event_id")
        order = record.get("order")
        digest = record.get("record_sha256")
        if not isinstance(event_id, str) or not event_id:
            errors.append("command evidence contains an invalid event ID")
            continue
        if event_id in seen_ids:
            errors.append(f"duplicate command evidence event ID: {event_id}")
            continue
        seen_ids.add(event_id)
        if not isinstance(order, int) or order != previous_order + 1:
            errors.append(f"non-sequential command evidence order at {event_id}")
        else:
            previous_order = order
        for timestamp_field in ("started_at", "finished_at"):
            try:
                datetime.fromisoformat(str(record.get(timestamp_field)))
            except ValueError:
                errors.append(f"invalid {timestamp_field} on {event_id}")
        if not isinstance(digest, str) or record_digest(record) != digest:
            errors.append(f"record digest mismatch for {event_id}")
            continue
        raw = raw_receipts.get((event_id, digest))
        if raw is None:
            errors.append(f"no raw Codex command receipt for {event_id}")
            continue
        if raw.get("exit_code") != record.get("exit_code"):
            errors.append(f"exit status mismatch for {event_id}")
            continue
        by_id[event_id] = {**record, "raw_event_index": raw["raw_event_index"]}
    return by_id, errors


def _referenced(
    result: dict[str, Any], records: dict[str, dict[str, Any]], field: str
) -> dict[str, Any] | None:
    event_id = result.get(field)
    return records.get(event_id) if isinstance(event_id, str) else None


def _valid_pre_edit_core(
    result: dict[str, Any], records: dict[str, dict[str, Any]]
) -> bool:
    reproduction = _referenced(result, records, "reproduction_event_id")
    if (
        reproduction is None
        or reproduction.get("phase") != "reproduction"
        or reproduction.get("edit_state") != PRE_EDIT
        or reproduction.get("exit_code") == 0
    ):
        return False
    diagnosis = result.get("diagnosis")
    if not isinstance(diagnosis, dict) or not str(diagnosis.get("hypothesis", "")).strip():
        return False
    ids = diagnosis.get("evidence_event_ids")
    if not isinstance(ids, list) or not ids:
        return False
    referenced = [records.get(event_id) for event_id in ids]
    return all(
        record is not None
        and record.get("phase") in {"reproduction", "investigation"}
        and record.get("edit_state") == PRE_EDIT
        for record in referenced
    ) and any(record and record.get("phase") == "investigation" for record in referenced)


def should_retry(
    result: object,
    evidence_events: list[dict[str, Any]],
    raw_events: list[dict[str, Any]],
) -> bool:
    if not isinstance(result, dict) or result.get("status") != "verification_failed":
        return False
    records, errors = corroborated_events(evidence_events, raw_events)
    if errors or not _valid_pre_edit_core(result, records):
        return False
    if not isinstance(result.get("repair"), dict):
        return False
    verification = [
        _referenced(result, records, "focused_verification_event_id"),
        _referenced(result, records, "broad_verification_event_id"),
    ]
    return any(
        record is not None
        and record.get("edit_state") == POST_EDIT
        and isinstance(record.get("exit_code"), int)
        and record["exit_code"] != 0
        for record in verification
    )


def merge_retry(first: dict[str, Any], retry: dict[str, Any]) -> dict[str, Any]:
    """Retain the original pre-edit evidence while accepting new verification refs."""

    return {
        **retry,
        "reproduction_event_id": first.get("reproduction_event_id"),
        "diagnosis": first.get("diagnosis"),
        "repair": retry.get("repair") or first.get("repair"),
    }


def _production_files(changed_files: list[str]) -> set[str]:
    return {
        path
        for path in changed_files
        if not path.endswith("tests.py")
        and "/tests/" not in f"/{path}"
        and not path.rsplit("/", 1)[-1].startswith("test_")
        and not path.startswith(".ari/")
        and path != "ISSUE.md"
    }


def validate_evidence(
    result: object,
    evidence_events: list[dict[str, Any]],
    raw_events: list[dict[str, Any]],
    changed_files: list[str],
    retry_count: int,
) -> list[dict[str, Any]]:
    records, errors = corroborated_events(evidence_events, raw_events)
    command_evidence = [
        {
            "type": "command_evidence",
            "evidence": {**record, "validated": event_id in records},
        }
        for event_id, record in (
            (str(event.get("event_id", "")), event) for event in evidence_events
        )
    ]
    if not isinstance(result, dict):
        errors.append("final response is not a JSON object")
        return command_evidence + [_validation_error(errors, retry_count, None)]

    status = result.get("status")
    if status == "abstained":
        reason = result.get("abstention_reason")
        validated = isinstance(reason, str) and bool(reason.strip()) and not changed_files
        return command_evidence + [
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

    reproduction = _referenced(result, records, "reproduction_event_id")
    if reproduction is None:
        errors.append("reproduction does not reference a corroborated evidence event")
    else:
        if reproduction.get("phase") != "reproduction":
            errors.append("reproduction references the wrong phase")
        if reproduction.get("edit_state") != PRE_EDIT:
            errors.append("reproduction did not occur before the first source edit")
        if reproduction.get("exit_code") == 0:
            errors.append("reproduction did not fail with a non-zero exit status")

    diagnosis = result.get("diagnosis")
    diagnosis_ids: list[str] = []
    diagnosis_records: list[dict[str, Any]] = []
    if isinstance(diagnosis, dict) and str(diagnosis.get("hypothesis", "")).strip():
        raw_ids = diagnosis.get("evidence_event_ids")
        if isinstance(raw_ids, list):
            diagnosis_ids = [event_id for event_id in raw_ids if isinstance(event_id, str)]
            diagnosis_records = [records[event_id] for event_id in diagnosis_ids if event_id in records]
    if len(set(diagnosis_ids)) != len(diagnosis_ids):
        errors.append("diagnosis contains duplicate evidence event references")
    elif not diagnosis_ids or len(diagnosis_records) != len(diagnosis_ids):
        errors.append("diagnosis references missing or uncorroborated evidence events")
    elif any(
        record.get("edit_state") != PRE_EDIT
        or record.get("phase") not in {"reproduction", "investigation"}
        for record in diagnosis_records
    ):
        errors.append("diagnosis evidence was not gathered in a pre-edit investigation phase")
    elif not any(record.get("phase") == "investigation" for record in diagnosis_records):
        errors.append("diagnosis lacks a pre-edit investigation event")

    repair = result.get("repair")
    reported_files: set[str] = set()
    if isinstance(repair, dict) and isinstance(repair.get("files"), list):
        reported_files = {
            path for path in repair["files"] if isinstance(path, str) and path
        }
    changed = set(changed_files)
    if not reported_files or not reported_files.issubset(changed):
        errors.append("reported repair files do not match the repository patch")
    if not _production_files(changed_files):
        errors.append("repair did not change a production file")

    focused = _referenced(result, records, "focused_verification_event_id")
    broad = _referenced(result, records, "broad_verification_event_id")
    for label, record, phase in (
        ("focused", focused, "focused_verification"),
        ("broad", broad, "broad_verification"),
    ):
        if record is None:
            errors.append(f"{label} verification does not reference a corroborated event")
            continue
        if record.get("phase") != phase or record.get("edit_state") != POST_EDIT:
            errors.append(f"{label} verification has an invalid phase or edit ordering")
        if record.get("exit_code") != 0:
            errors.append(f"{label} verification did not pass")
        patch_at_verification = set(record.get("source_changes_before") or [])
        if not reported_files.issubset(patch_at_verification):
            errors.append(f"{label} verification was not run against the reported patch")
    if focused is not None and broad is not None:
        if focused.get("event_id") == broad.get("event_id"):
            errors.append("focused and broad verification must be distinct events")
        if int(broad.get("order", 0)) <= int(focused.get("order", 0)):
            errors.append("broad verification must follow focused verification")

    if errors:
        return command_evidence + [_validation_error(errors, retry_count, status)]

    return command_evidence + [
        {
            "type": "reproduction",
            "evidence": {
                "validated": True,
                "event_id": reproduction["event_id"],
            },
        },
        {
            "type": "diagnosis",
            "evidence": {
                "validated": True,
                "hypothesis": diagnosis["hypothesis"],
                "evidence_event_ids": diagnosis_ids,
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
                "focused_event_id": focused["event_id"],
                "broad_event_id": broad["event_id"],
                "retry_count": retry_count,
            },
        },
    ]


def _validation_error(
    errors: list[str], retry_count: int, status: object
) -> dict[str, Any]:
    return {
        "type": "workflow_validation",
        "evidence": {
            "validated": False,
            "errors": errors,
            "retry_count": retry_count,
            "status": status,
        },
    }
