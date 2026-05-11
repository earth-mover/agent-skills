from __future__ import annotations

from icechunk_eval.redactor import redact, redact_obj


def test_aws_access_key():
    out = redact("key=AKIAIOSFODNN7EXAMPLE here")
    assert "AKIA" not in out
    assert "AWS_ACCESS_KEY" in out


def test_jwt():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjMifQ.signaturepart"
    assert "JWT" in redact(jwt)


def test_github_pat():
    pat = "ghp_" + "A" * 36
    assert "GITHUB_PAT" in redact(pat)


def test_anthropic_key():
    key = "sk-ant-api03-" + "x" * 40
    assert "ANTHROPIC_KEY" in redact(key)


def test_bearer_token():
    out = redact("Authorization: Bearer abcdefghijklmnopqrst")
    assert "abcdefghijklmnopqrst" not in out
    assert "Bearer <REDACTED>" in out


def test_safe_string_unchanged():
    safe = "the quick brown fox over 9000"
    assert redact(safe) == safe


def test_redact_obj_recurses():
    obj = {
        "tool": "Bash",
        "args": {"command": "aws s3 ls --token AKIAIOSFODNN7EXAMPLE"},
        "list": ["safe", "Bearer abcdefghijklmnopqrstuvwx"],
    }
    out = redact_obj(obj)
    assert "AKIA" not in out["args"]["command"]
    assert "abcdefghijklmnopqrstuvwx" not in out["list"][1]
    assert out["tool"] == "Bash"
    assert out["list"][0] == "safe"
