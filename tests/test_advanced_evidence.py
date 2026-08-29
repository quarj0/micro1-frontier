from __future__ import annotations

from agents.codex_advanced.evidence import (
    merge_retry,
    should_retry,
    validate_evidence,
)


def command_event(command: str, output: str, exit_code: int) -> dict[str, object]:
    return {
        "type": "item.completed",
        "item": {
            "type": "command_execution",
            "command": f"/usr/bin/bash -lc '{command}'",
            "aggregated_output": output,
            "exit_code": exit_code,
        },
    }


def file_change_event() -> dict[str, object]:
    return {
        "type": "item.completed",
        "item": {
            "type": "file_change",
            "changes": [{"path": "/workspace/api/views.py", "kind": "update"}],
        },
    }


def repaired_result() -> dict[str, object]:
    return {
        "status": "repaired",
        "reproduction": {
            "command": "python reproduce.py",
            "observed": "AssertionError: wrong payload",
            "exit_code": 1,
        },
        "diagnosis": {
            "hypothesis": "The view parses false as truthy.",
            "evidence": [
                {
                    "command": "sed -n 1,80p api/views.py",
                    "observed": "bool(request.query_params.get",
                }
            ],
        },
        "repair": {"summary": "Parse explicit boolean values.", "files": ["api/views.py"]},
        "focused_verification": {
            "command": "python focused.py",
            "observed": "focused passed",
            "exit_code": 0,
        },
        "regression_verification": {
            "command": "python manage.py test",
            "observed": "OK",
            "exit_code": 0,
        },
        "abstention_reason": None,
    }


def evidence_events() -> list[dict[str, object]]:
    return [
        command_event("python reproduce.py", "AssertionError: wrong payload", 1),
        command_event(
            "sed -n 1,80p api/views.py",
            "active = bool(request.query_params.get('active'))",
            0,
        ),
        file_change_event(),
        command_event("python focused.py", "focused passed", 0),
        command_event("python manage.py test", "Ran 4 tests\nOK", 0),
    ]


def test_validated_evidence_requires_observed_commands_in_phase_order():
    events = validate_evidence(
        repaired_result(), evidence_events(), ["api/views.py"], retry_count=0
    )

    assert [event["type"] for event in events] == [
        "reproduction",
        "diagnosis",
        "repair",
        "verification",
    ]
    assert all(event["evidence"]["validated"] for event in events)


def test_reproduction_after_edit_is_rejected():
    events = evidence_events()
    events.insert(0, events.pop(2))

    result = validate_evidence(repaired_result(), events, ["api/views.py"], 0)

    assert result[0]["type"] == "workflow_validation"
    assert result[0]["evidence"]["validated"] is False


def test_corroboration_allows_exact_output_lines_with_noise_between_them():
    result = repaired_result()
    events = evidence_events()
    events[0] = command_event(
        "python reproduce.py",
        "AssertionError: wrong payload\ntraceback noise\nsecond exact line",
        1,
    )
    result["reproduction"]["observed"] = (
        "AssertionError: wrong payload\nsecond exact line"
    )

    validated = validate_evidence(result, events, ["api/views.py"], 0)

    assert validated[0]["type"] == "reproduction"


def test_only_corroborated_verification_failure_unlocks_one_retry():
    result = repaired_result()
    result["status"] = "verification_failed"
    result["focused_verification"] = {
        "command": "python focused.py",
        "observed": "focused failed",
        "exit_code": 1,
    }
    events = evidence_events()
    events[-2] = command_event("python focused.py", "focused failed", 1)

    assert should_retry(result, events) is True
    assert merge_retry(result, repaired_result())["reproduction"] == result["reproduction"]
