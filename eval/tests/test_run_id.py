from __future__ import annotations

import re
from pathlib import Path

from icechunk_eval.run_id import generate_run_id, git_dirty, git_short_sha

REPO = Path(__file__).resolve().parents[2]


def test_git_short_sha_returns_7_hex_chars():
    sha = git_short_sha(REPO)
    assert re.fullmatch(r"[0-9a-f]{7}", sha)


def test_git_dirty_returns_bool():
    assert isinstance(git_dirty(REPO), bool)


def test_generate_run_id_has_expected_shape():
    rid = generate_run_id("era5-happy", REPO)
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}_\d{6}_[0-9a-f]{7}_era5-happy", rid
    )


def test_generate_run_id_sortable_by_time():
    a = generate_run_id("f", REPO)
    b = generate_run_id("f", REPO)
    assert a <= b
