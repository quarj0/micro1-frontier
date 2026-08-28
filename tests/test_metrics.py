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
            {"metrics": {"verified_repair": True}},
            {"metrics": {"verified_repair": False}},
        ]
    )

    assert result == {"cases": 2, "verified_repairs": 1, "verified_repair_rate": 0.5}
