from regression_investigator.metrics import aggregate_reports, calculate_metrics
from regression_investigator.models import EvaluationResult, ProcessResult, ProcessState


def test_metrics_require_the_evaluator_to_pass():
    agent = ProcessResult(ProcessState.SUCCEEDED, ["agent"], 0, 1.0, "", "")
    evaluator = EvaluationResult(ProcessState.FAILED, ["test"], 1, 0.5, "", "", passed=False)

    metrics = calculate_metrics(agent, evaluator, ["api/views.py"], [], None)

    assert metrics["agent_completed"] is True
    assert metrics["verified_repair"] is False
    assert metrics["evidence_backed_repair"] is False
    assert metrics["files_changed"] == 1


def test_aggregate_reports_calculates_verified_repair_rate():
    result = aggregate_reports(
        [
            {"metrics": {"verified_repair": True, "evidence_backed_repair": True}},
            {"metrics": {"verified_repair": False, "evidence_backed_repair": False}},
        ]
    )

    assert result == {
        "cases": 2,
        "evidence_backed_repairs": 1,
        "evidence_backed_repair_rate": 0.5,
        "verified_repairs": 1,
        "verified_repair_rate": 0.5,
    }


def test_metrics_ignore_unvalidated_semantic_event_names():
    agent = ProcessResult(ProcessState.SUCCEEDED, ["agent"], 0, 1.0, "", "")
    evaluator = EvaluationResult(ProcessState.SUCCEEDED, ["test"], 0, 0.5, "", "", passed=True)
    evidence = [
        {"type": event_type, "evidence": {"validated": False}}
        for event_type in ("reproduction", "diagnosis", "verification")
    ]

    metrics = calculate_metrics(agent, evaluator, ["api/views.py"], evidence, None)

    assert metrics["evidence_chain_complete"] is False
    assert metrics["evidence_backed_repair"] is False
