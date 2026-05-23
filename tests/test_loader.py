"""Tests for driftcheck.loader — YAML definition loading."""

import textwrap
from pathlib import Path

import pytest

from driftcheck.loader import YAMLLoadError, load_definition, load_definitions_from_dir


# ---------------------------------------------------------------------------
# load_definition
# ---------------------------------------------------------------------------

def test_load_definition_returns_dict(tmp_path: Path) -> None:
    yaml_file = tmp_path / "service.yaml"
    yaml_file.write_text("name: web\nreplicas: 3\n", encoding="utf-8")

    result = load_definition(yaml_file)

    assert result == {"name": "web", "replicas": 3}


def test_load_definition_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(YAMLLoadError, match="not found"):
        load_definition(tmp_path / "ghost.yaml")


def test_load_definition_invalid_yaml_raises(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("key: [unclosed", encoding="utf-8")

    with pytest.raises(YAMLLoadError, match="Failed to parse YAML"):
        load_definition(bad_file)


def test_load_definition_non_mapping_raises(tmp_path: Path) -> None:
    list_file = tmp_path / "list.yaml"
    list_file.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(YAMLLoadError, match="Expected a YAML mapping"):
        load_definition(list_file)


def test_load_definition_path_is_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(YAMLLoadError, match="not a file"):
        load_definition(tmp_path)


# ---------------------------------------------------------------------------
# load_definitions_from_dir
# ---------------------------------------------------------------------------

def test_load_definitions_from_dir_returns_all_yaml(tmp_path: Path) -> None:
    (tmp_path / "a.yaml").write_text("service: alpha\n", encoding="utf-8")
    (tmp_path / "b.yml").write_text("service: beta\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")

    result = load_definitions_from_dir(tmp_path)

    assert set(result.keys()) == {"a.yaml", "b.yml"}
    assert result["a.yaml"] == {"service": "alpha"}
    assert result["b.yml"] == {"service": "beta"}


def test_load_definitions_from_dir_nested(tmp_path: Path) -> None:
    sub = tmp_path / "infra" / "prod"
    sub.mkdir(parents=True)
    (sub / "db.yaml").write_text("engine: postgres\n", encoding="utf-8")

    result = load_definitions_from_dir(tmp_path)

    assert "infra/prod/db.yaml" in result
    assert result["infra/prod/db.yaml"] == {"engine": "postgres"}


def test_load_definitions_from_dir_missing_dir_raises(tmp_path: Path) -> None:
    with pytest.raises(YAMLLoadError, match="not found"):
        load_definitions_from_dir(tmp_path / "no_such_dir")


def test_load_definitions_from_dir_empty(tmp_path: Path) -> None:
    result = load_definitions_from_dir(tmp_path)
    assert result == {}
