"""Tests for driftcheck.exporter."""

import json
import csv
import io

import pytest

from driftcheck.differ import Change
from driftcheck.exporter import (
    results_to_records,
    export_json,
    export_csv,
    export_text,
)


def _clean_result(resource="svc/web"):
    return {"resource": resource, "changes": []}


def _drift_result(resource="svc/api"):
    return {
        "resource": resource,
        "changes": [
            Change(key="replicas", change_type="changed", expected=3, actual=1),
            Change(key="image", change_type="missing", expected="nginx", actual=None),
        ],
    }


# --- results_to_records ---

def test_results_to_records_clean_produces_single_record():
    records = results_to_records([_clean_result()])
    assert len(records) == 1
    assert records[0]["change_type"] == "clean"
    assert records[0]["resource"] == "svc/web"


def test_results_to_records_drift_produces_one_record_per_change():
    records = results_to_records([_drift_result()])
    assert len(records) == 2
    assert records[0]["key"] == "replicas"
    assert records[1]["key"] == "image"


def test_results_to_records_mixed():
    records = results_to_records([_clean_result(), _drift_result()])
    assert len(records) == 3


# --- export_json ---

def test_export_json_returns_valid_json():
    output = export_json([_clean_result(), _drift_result()])
    parsed = json.loads(output)
    assert isinstance(parsed, list)
    assert len(parsed) == 3


def test_export_json_contains_expected_fields():
    output = export_json([_drift_result()])
    records = json.loads(output)
    assert "resource" in records[0]
    assert "change_type" in records[0]
    assert "expected" in records[0]


# --- export_csv ---

def test_export_csv_returns_string_with_header():
    output = export_csv([_clean_result()])
    assert output.startswith("resource,key,change_type")


def test_export_csv_rows_match_records():
    output = export_csv([_drift_result()])
    reader = csv.DictReader(io.StringIO(output))
    rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["key"] == "replicas"


# --- export_text ---

def test_export_text_clean_shows_clean_label():
    output = export_text([_clean_result()])
    assert "[CLEAN] svc/web" in output


def test_export_text_drift_shows_drift_label():
    output = export_text([_drift_result()])
    assert "[DRIFT] svc/api" in output


def test_export_text_drift_lists_changes():
    output = export_text([_drift_result()])
    assert "replicas" in output
    assert "image" in output


def test_export_text_multiple_resources():
    output = export_text([_clean_result(), _drift_result()])
    assert "[CLEAN]" in output
    assert "[DRIFT]" in output
