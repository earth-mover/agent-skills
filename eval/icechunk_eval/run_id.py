from __future__ import annotations

import datetime as dt
import subprocess
from pathlib import Path


def git_short_sha(repo: Path) -> str:
    out = subprocess.check_output(
        ["git", "rev-parse", "--short=7", "HEAD"], cwd=repo, text=True
    )
    return out.strip()


def git_dirty(repo: Path) -> bool:
    out = subprocess.check_output(
        ["git", "status", "--porcelain"], cwd=repo, text=True
    )
    return bool(out.strip())


def generate_run_id(fixture: str, repo: Path) -> str:
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y-%m-%d_%H%M%S")
    return f"{timestamp}_{git_short_sha(repo)}_{fixture}"
