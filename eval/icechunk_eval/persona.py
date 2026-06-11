from __future__ import annotations

import json
import re
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    query,
)


class Persona:
    """LLM-driven user simulation for AskUserQuestion.

    Uses claude-agent-sdk (rather than the anthropic SDK directly) so the
    persona rides Claude Code subscription auth alongside the agent under
    test. Temporary workaround — see GitHub issue for the planned switch
    back to the anthropic SDK once an ANTHROPIC_API_KEY is available.
    """

    def __init__(
        self,
        brief: str,
        model: str = "claude-haiku-4-5-20251001",
    ) -> None:
        self.brief = brief
        self.model = model
        self.transcript: list[dict[str, Any]] = []
        self.tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}

    async def answer(self, questions: list[dict[str, Any]]) -> dict[str, Any]:
        prompt = _format_questions(questions)
        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=self.brief,
            allowed_tools=[],
            permission_mode="bypassPermissions",
        )

        response_text = ""
        async for msg in query(prompt=prompt, options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    text = getattr(block, "text", None)
                    if text:
                        response_text += text
            elif isinstance(msg, ResultMessage) and msg.usage:
                self.tokens["input"] += msg.usage.get("input_tokens", 0) or 0
                self.tokens["output"] += msg.usage.get("output_tokens", 0) or 0
                self.tokens["cache_read"] += (
                    msg.usage.get("cache_read_input_tokens", 0) or 0
                )
                self.tokens["cache_write"] += (
                    msg.usage.get("cache_creation_input_tokens", 0) or 0
                )

        answers = _parse_response(response_text)
        self.transcript.append(
            {"questions": questions, "raw_response": response_text, "answers": answers}
        )
        return answers


def _format_questions(questions: list[dict[str, Any]]) -> str:
    lines: list[str] = [
        "An agent is asking you the following question(s). For each, pick the "
        "option `label` that best matches your preference. For multi-select "
        "questions, return a list of labels. Free-text strings are also accepted "
        "when no option fits.",
        "",
        "Respond with ONLY a JSON object mapping each question's exact text to "
        "your chosen value. No prose, no markdown fences.",
        "",
    ]
    for q in questions:
        lines.append(f"Question: {q['question']!r}")
        lines.append(f"  Header: {q['header']}")
        lines.append(f"  Multi-select: {q.get('multiSelect', False)}")
        lines.append("  Options:")
        for opt in q["options"]:
            lines.append(f"    - {opt['label']}: {opt['description']}")
        lines.append("")
    return "\n".join(lines)


_FENCE = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def _parse_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        m = _FENCE.match(text)
        if m:
            text = m.group(1).strip()
    return json.loads(text)
