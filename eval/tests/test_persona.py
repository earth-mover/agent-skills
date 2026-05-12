from __future__ import annotations

import pytest

from icechunk_eval.persona import _format_questions, _parse_response


QUESTIONS = [
    {
        "question": "Pick a thing",
        "header": "Thing",
        "multiSelect": False,
        "options": [
            {"label": "Alpha", "description": "first"},
            {"label": "Beta", "description": "second"},
        ],
    }
]


def test_format_questions_includes_labels_and_descriptions():
    out = _format_questions(QUESTIONS)
    assert "Pick a thing" in out
    assert "Alpha: first" in out
    assert "Beta: second" in out
    assert "Multi-select: False" in out


def test_format_questions_marks_multi_select():
    qs = [{**QUESTIONS[0], "multiSelect": True}]
    assert "Multi-select: True" in _format_questions(qs)


def test_parse_response_bare_json():
    text = '{"Pick a thing": "Alpha"}'
    assert _parse_response(text) == {"Pick a thing": "Alpha"}


def test_parse_response_strips_markdown_fence():
    text = '```json\n{"q": "a"}\n```'
    assert _parse_response(text) == {"q": "a"}


def test_parse_response_strips_bare_fence():
    text = '```\n{"q": "a"}\n```'
    assert _parse_response(text) == {"q": "a"}


def test_parse_response_handles_multi_select_list():
    text = '{"q": ["A", "B"]}'
    assert _parse_response(text) == {"q": ["A", "B"]}


def test_parse_response_raises_on_garbage():
    with pytest.raises(Exception):
        _parse_response("not json at all")
