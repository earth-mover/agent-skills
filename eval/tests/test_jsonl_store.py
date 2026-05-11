from __future__ import annotations

from pathlib import Path

from icechunk_eval.jsonl_store import append_row, read_all


def test_append_and_read_roundtrip(tmp_path: Path):
    path = tmp_path / "runs.jsonl"
    append_row(path, {"a": 1})
    append_row(path, {"b": 2, "nested": {"c": 3}})
    assert read_all(path) == [{"a": 1}, {"b": 2, "nested": {"c": 3}}]


def test_read_all_missing_file_returns_empty(tmp_path: Path):
    assert read_all(tmp_path / "nope.jsonl") == []


def test_append_creates_parent_dirs(tmp_path: Path):
    path = tmp_path / "deep" / "nested" / "runs.jsonl"
    append_row(path, {"x": 1})
    assert path.exists()


def test_each_row_one_line(tmp_path: Path):
    path = tmp_path / "runs.jsonl"
    append_row(path, {"a": "line\nwith\nnewlines"})
    append_row(path, {"b": 2})
    assert len(path.read_text().splitlines()) == 2
