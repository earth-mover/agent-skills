from __future__ import annotations

import re
from typing import Any

# Best-effort pattern-based scrub. Not exhaustive; the SDK loop must also
# apply field-level allowlisting before logging tool calls.
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "<REDACTED:AWS_ACCESS_KEY>"),
    (re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), "<REDACTED:JWT>"),
    (re.compile(r"\bghp_[A-Za-z0-9]{36}\b"), "<REDACTED:GITHUB_PAT>"),
    (re.compile(r"\bgh[osur]_[A-Za-z0-9]{30,}\b"), "<REDACTED:GITHUB_TOKEN>"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"), "<REDACTED:ANTHROPIC_KEY>"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "<REDACTED:OPENAI_KEY>"),
    (re.compile(r"Bearer\s+[A-Za-z0-9._\-+/=]{16,}"), "Bearer <REDACTED>"),
]


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_obj(obj: Any) -> Any:
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_obj(v) for v in obj]
    return obj
