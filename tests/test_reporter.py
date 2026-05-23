"""Tests for driftcheck.reporter module."""

from driftcheck.comparator import DriftResult
from driftcheck.reporter import format_report, has_any_drift


def _make_clean_result(resource_id: str = "res-1") -> DriftResult:
    return DriftResult(resource_id=resource_id, has_drift=False)


def _make_drift_result(resource_id: str = "res-2") -> DriftResult:
    return DriftResult(
        resource_id=resource_id,
        has_drift=True,
        missing_keys=["timeout"],
        changed_values={"size": {"expected": "small", "actual": "large"}},
    )


def test_format_report_clean_results_hidden_by_default():
    results = [_make_clean_result("a"), _make_clean_result("b")]
    report = format_report(results)
    assert "[OK]" not in report
    assert "2 resource(s) clean" in report


def test_format_report_clean_results_shown_verbose():
    results = [_make_clean_result("a"), _make_clean_result("b")]
    report = format_report(results, verbose=True)
    assert report.count("[OK]") == 2


def test_format_report_shows_drift():
    results = [_make_drift_result("server-99")]
    report = format_report(results)
    assert "[DRIFT]" in report
    assert "server-99" in report


def test_format_report_shows_changed_values_detail():
    results = [_make_drift_result()]
    report = format_report(results)
    assert "expected: small" in report
    assert "actual:   large" in report


def test_format_report_summary_counts():
    results = [_make_clean_result("a"), _make_drift_result("b"), _make_drift_result("c")]
    report = format_report(results)
    assert "2 resource(s) with drift" in report
    assert "1 resource(s) clean" in report


def test_format_report_empty():
    report = format_report([])
    assert "0 resource(s) with drift" in report
    assert "0 resource(s) clean" in report


def test_has_any_drift_true():
    results = [_make_clean_result(), _make_drift_result()]
    assert has_any_drift(results) is True


def test_has_any_drift_false():
    results = [_make_clean_result("x"), _make_clean_result("y")]
    assert has_any_drift(results) is False


def test_has_any_drift_empty():
    assert has_any_drift([]) is False
