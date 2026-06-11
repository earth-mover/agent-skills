from __future__ import annotations

import datetime as dt
from unittest.mock import MagicMock

from icechunk_eval.harness import build_row
from icechunk_eval.meta import RunMeta
from icechunk_eval.sdk_loop import AgentRunResult


def _meta() -> RunMeta:
    return RunMeta(
        run_id="rid",
        fixture="smoke",
        skill_sha="abc1234",
        harness_sha="abc1234",
        skill_dirty=False,
        agent_model="claude-opus-4-7",
        persona_model="claude-haiku-4-5-20251001",
        started_at=dt.datetime(2026, 5, 12, tzinfo=dt.UTC),
    )


def _persona(tokens=None):
    p = MagicMock()
    p.tokens = tokens or {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    return p


def _result(*, is_error=False, tool_errors=None) -> AgentRunResult:
    return AgentRunResult(
        elapsed_s=1.0,
        tokens={"input": 0, "output": 0, "cache_read": 0, "cache_write": 0},
        skills_loaded=[],
        transcript=[],
        final_result="done",
        is_error=is_error,
        num_turns=1,
        total_cost_usd=0.0,
        tool_errors=tool_errors or [],
    )


def test_outcome_pass_when_no_errors():
    row = build_row("rid", _meta(), _result(), _persona())
    assert row["outcome"] == "pass"


def test_outcome_fail_when_result_is_error():
    row = build_row("rid", _meta(), _result(is_error=True), _persona())
    assert row["outcome"] == "fail"


def test_outcome_fail_when_tool_errors_present():
    row = build_row(
        "rid",
        _meta(),
        _result(tool_errors=[{"tool_use_id": "x", "content": "auth failed"}]),
        _persona(),
    )
    assert row["outcome"] == "fail"


def test_tool_errors_in_deterministic_block():
    errors = [{"tool_use_id": "x", "content": "boom"}]
    row = build_row("rid", _meta(), _result(tool_errors=errors), _persona())
    assert row["deterministic"]["tool_errors"] == errors
