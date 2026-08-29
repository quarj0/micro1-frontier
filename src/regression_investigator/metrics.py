from __future__ import annotations

from typing import Any

from .models import EvaluationResult, ProcessResult, ProcessState


def calculate_metrics(
    agent: ProcessResult,
    evaluator: EvaluationResult,
    patch_files: list[str],
    evidence: list[dict[str, Any]],
    usage: dict[str, Any] | None,
) -> dict[str, object]:
    validated_events = [
        event
        for event in evidence
        if isinstance(event.get("evidence"), dict)
        and event["evidence"].get("validated") is True
    ]
    event_types = {str(event.get("type")) for event in validated_events}
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
        "input_tokens": usage.get("input_tokens") if usage else None,
        "cached_input_tokens": usage.get("cached_input_tokens") if usage else None,
        "output_tokens": usage.get("output_tokens") if usage else None,
        "reasoning_output_tokens": usage.get("reasoning_output_tokens") if usage else None,
        "estimated_cost_usd": usage.get("estimated_cost_usd") if usage else None,
    }


def aggregate_reports(reports: list[dict[str, object]]) -> dict[str, object]:
    total = len(reports)
    repaired = sum(bool(report["metrics"]["verified_repair"]) for report in reports)  # type: ignore[index]
    evidence_backed = sum(
        bool(report["metrics"]["evidence_backed_repair"]) for report in reports  # type: ignore[index]
    )
    return {
        "cases": total,
        "evidence_backed_repairs": evidence_backed,
        "evidence_backed_repair_rate": evidence_backed / total if total else 0.0,
        "verified_repairs": repaired,
        "verified_repair_rate": repaired / total if total else 0.0,
    }
