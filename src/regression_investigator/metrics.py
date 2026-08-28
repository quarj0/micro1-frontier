from __future__ import annotations

from typing import Any

from .models import EvaluationResult, ProcessResult, ProcessState


def calculate_metrics(
    agent: ProcessResult,
    evaluator: EvaluationResult,
    patch_files: list[str],
    trajectory: list[dict[str, Any]],
) -> dict[str, object]:
    event_types = {str(event.get("type")) for event in trajectory}
    evidence_chain_complete = {
        "reproduction",
        "diagnosis",
        "verification",
    }.issubset(event_types)
    return {
        "agent_completed": agent.state is ProcessState.SUCCEEDED,
        "verified_repair": evaluator.passed,
        "reproduction_recorded": "reproduction" in event_types,
        "diagnosis_recorded": "diagnosis" in event_types,
        "verification_recorded": "verification" in event_types,
        "evidence_chain_complete": evidence_chain_complete,
        "evidence_backed_repair": evaluator.passed and evidence_chain_complete,
        "patch_created": bool(patch_files),
        "files_changed": len(patch_files),
        "agent_runtime_seconds": round(agent.runtime_seconds, 3),
        "evaluation_runtime_seconds": round(evaluator.runtime_seconds, 3),
    }


def aggregate_reports(reports: list[dict[str, object]]) -> dict[str, object]:
    total = len(reports)
    repaired = sum(bool(report["metrics"]["verified_repair"]) for report in reports)  # type: ignore[index]
    return {
        "cases": total,
        "verified_repairs": repaired,
        "verified_repair_rate": repaired / total if total else 0.0,
    }
