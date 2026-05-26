"""Tests for driftcheck.remediation_report."""
import pytest

from driftcheck.remediation_report import (
    RemediationReport,
    build_remediation_report,
    build_remediation_report_from_error,
)
from driftcheck.scanner import ScanError


def test_build_report_no_drift():
    defn = {"replicas": 3, "image": "nginx"}
    live = {"replicas": 3, "image": "nginx"}
    report = build_remediation_report("svc", defn, live)
    assert not report.drifted
    assert report.hints == []
    assert report.error == ""


def test_build_report_detects_changed_value():
    defn = {"replicas": 3}
    live = {"replicas": 1}
    report = build_remediation_report("svc", defn, live)
    assert report.drifted
    assert len(report.hints) == 1
    assert report.hints[0].key == "replicas"


def test_build_report_detects_missing_key():
    defn = {"image": "nginx", "port": 80}
    live = {"image": "nginx"}
    report = build_remediation_report("svc", defn, live)
    assert report.drifted
    keys = [h.key for h in report.hints]
    assert "port" in keys


def test_build_report_severity_propagated():
    defn = {"x": 1}
    live = {"x": 2}
    report = build_remediation_report("svc", defn, live, severity="critical")
    assert report.hints[0].severity == "critical"


def test_build_report_from_error():
    err = ScanError("svc", "connection refused")
    report = build_remediation_report_from_error("svc", err)
    assert not report.drifted
    assert "connection refused" in report.error


def test_report_to_dict_structure():
    defn = {"replicas": 3}
    live = {"replicas": 1}
    report = build_remediation_report("svc", defn, live)
    d = report.to_dict()
    assert d["resource"] == "svc"
    assert d["drifted"] is True
    assert isinstance(d["hints"], list)
    assert len(d["hints"]) == 1


def test_report_formatted_clean():
    report = RemediationReport(resource="svc", drifted=False, hints=[])
    out = report.formatted()
    assert "CLEAN" in out
    assert "No remediation required." in out


def test_report_formatted_drifted():
    defn = {"replicas": 3}
    live = {"replicas": 1}
    report = build_remediation_report("svc", defn, live)
    out = report.formatted()
    assert "DRIFTED" in out
    assert "replicas" in out


def test_report_formatted_error():
    report = RemediationReport(resource="svc", drifted=False, error="timeout")
    out = report.formatted()
    assert "ERROR" in out
    assert "timeout" in out
