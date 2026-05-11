from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    query,
)
from claude_agent_sdk.types import (
    HookMatcher,
    PermissionResultAllow,
    ToolPermissionContext,
)

from icechunk_eval.persona import Persona


@dataclass
class AgentRunResult:
    elapsed_s: float
    tokens: dict[str, int]
    skills_loaded: list[str]
    transcript: list[dict[str, Any]]
    final_result: str | None
    is_error: bool
    num_turns: int
    total_cost_usd: float | None


async def run_agent(
    *,
    prompt: str,
    cwd: Path,
    skill_name: str,
    persona: Persona,
    model: str = "claude-opus-4-7",
) -> AgentRunResult:
    transcript: list[dict[str, Any]] = []
    skills_loaded: list[str] = []
    tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    final_result: str | None = None
    is_error = False
    num_turns = 0
    total_cost_usd: float | None = None

    async def can_use_tool(
        tool_name: str, input_data: dict[str, Any], context: ToolPermissionContext
    ) -> PermissionResultAllow:
        if tool_name == "AskUserQuestion":
            answers = await persona.answer(input_data["questions"])
            return PermissionResultAllow(
                updated_input={
                    "questions": input_data["questions"],
                    "answers": answers,
                }
            )
        return PermissionResultAllow(updated_input=input_data)

    async def keep_stream_open(input_data, tool_use_id, context):
        return {"continue_": True}

    options = ClaudeAgentOptions(
        cwd=str(cwd),
        model=model,
        skills=[skill_name],
        permission_mode="default",
        can_use_tool=can_use_tool,
        hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[keep_stream_open])]},
        system_prompt={"type": "preset", "preset": "claude_code"},
    )

    async def prompt_stream():
        yield {"type": "user", "message": {"role": "user", "content": prompt}}

    start = time.monotonic()
    async for message in query(prompt=prompt_stream(), options=options):
        transcript.append(_serialize(message))
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if getattr(block, "name", None) == "Read":
                    path = (getattr(block, "input", None) or {}).get("file_path", "")
                    if _looks_like_skill_path(path):
                        skills_loaded.append(path)
        elif isinstance(message, ResultMessage):
            if message.usage:
                tokens["input"] += message.usage.get("input_tokens", 0) or 0
                tokens["output"] += message.usage.get("output_tokens", 0) or 0
                tokens["cache_read"] += (
                    message.usage.get("cache_read_input_tokens", 0) or 0
                )
                tokens["cache_write"] += (
                    message.usage.get("cache_creation_input_tokens", 0) or 0
                )
            final_result = message.result
            is_error = message.is_error
            num_turns = message.num_turns
            total_cost_usd = message.total_cost_usd
    elapsed = time.monotonic() - start

    return AgentRunResult(
        elapsed_s=elapsed,
        tokens=tokens,
        skills_loaded=skills_loaded,
        transcript=transcript,
        final_result=final_result,
        is_error=is_error,
        num_turns=num_turns,
        total_cost_usd=total_cost_usd,
    )


def _looks_like_skill_path(path: str) -> bool:
    return "SKILL.md" in path or "/formats/" in path or "/.claude/skills/" in path


def _serialize(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(v) for v in obj]
    if hasattr(obj, "__dataclass_fields__"):
        return {
            "__type__": type(obj).__name__,
            **{f: _serialize(getattr(obj, f)) for f in obj.__dataclass_fields__},
        }
    if hasattr(obj, "__dict__"):
        return {
            "__type__": type(obj).__name__,
            **{
                k: _serialize(v)
                for k, v in vars(obj).items()
                if not k.startswith("_")
            },
        }
    return repr(obj)
