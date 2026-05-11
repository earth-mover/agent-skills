from __future__ import annotations

import json
import re
from typing import Any

from anthropic import AsyncAnthropic


class Persona:
    """LLM-driven user simulation for AskUserQuestion.

    Maintains its own conversation history so the agent's clarifying questions
    build on each other (e.g. the agent asks for a doc URL, then later asks
    whether the user wants virtual ingestion — the persona stays consistent).
    """

    def __init__(
        self,
        brief: str,
        model: str = "claude-haiku-4-5-20251001",
    ) -> None:
        self.brief = brief
        self.model = model
        self.client = AsyncAnthropic()
        self.history: list[dict[str, Any]] = []
        self.transcript: list[dict[str, Any]] = []
        self.tokens = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}

    async def answer(self, questions: list[dict[str, Any]]) -> dict[str, Any]:
        prompt = _format_questions(questions)
        msg = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=self.brief,
            messages=self.history + [{"role": "user", "content": prompt}],
            temperature=0,
        )
        response_text = msg.content[0].text
        answers = _parse_response(response_text)

        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": response_text})
        self.transcript.append(
            {"questions": questions, "raw_response": response_text, "answers": answers}
        )
        self.tokens["input"] += msg.usage.input_tokens
        self.tokens["output"] += msg.usage.output_tokens
        self.tokens["cache_read"] += getattr(msg.usage, "cache_read_input_tokens", 0) or 0
        self.tokens["cache_write"] += (
            getattr(msg.usage, "cache_creation_input_tokens", 0) or 0
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
