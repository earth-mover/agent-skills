from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
from pydantic import ValidationError

from icechunk_eval.meta import RunMeta, read_meta, write_meta


def _sample() -> RunMeta:
    return RunMeta(
        run_id="2026-05-11_143022_abc1234_era5-happy",
        fixture="era5-happy",
        skill_sha="abc1234",
        harness_sha="def5678",
        skill_dirty=False,
        agent_model="claude-opus-4-7",
        persona_model="claude-haiku-4-5-20251001",
        started_at=dt.datetime(2026, 5, 11, 14, 30, 22, tzinfo=dt.UTC),
    )


def test_yaml_roundtrip(tmp_path: Path):
    path = tmp_path / "meta.yaml"
    meta = _sample()
    write_meta(path, meta)
    assert read_meta(path) == meta


def test_extra_fields_rejected(tmp_path: Path):
    path = tmp_path / "meta.yaml"
    path.write_text("run_id: x\nbogus: 1\n")
    with pytest.raises(ValidationError):
        read_meta(path)


def test_ended_at_optional():
    meta = _sample()
    assert meta.ended_at is None
