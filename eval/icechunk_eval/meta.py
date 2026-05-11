from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict


class RunMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    fixture: str
    skill_sha: str
    harness_sha: str
    skill_dirty: bool
    agent_model: str
    persona_model: str
    started_at: datetime
    ended_at: datetime | None = None


def write_meta(path: Path, meta: RunMeta) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.safe_dump(meta.model_dump(mode="json"), f, sort_keys=False)


def read_meta(path: Path) -> RunMeta:
    with path.open() as f:
        return RunMeta.model_validate(yaml.safe_load(f))
