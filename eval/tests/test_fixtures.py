from __future__ import annotations

from icechunk_eval.harness import (
    build_persona_context,
    load_fixture,
    load_persona_brief,
)


def test_smoke_fixture_loads():
    fixture = load_fixture("smoke")
    assert fixture["name"] == "smoke"
    assert fixture["persona"] == "minimal"
    assert "AskUserQuestion" in fixture["agent_prompt"]


def test_era5_happy_fixture_loads():
    fixture = load_fixture("era5-happy")
    assert fixture["persona"] == "climate-scientist"
    al = fixture["arraylake"]
    assert al["source_org"] == "earthmover-ingest-evals"
    assert "{run_id}" in al["output_repo_template"]


def test_persona_context_substitution():
    fixture = load_fixture("era5-happy")
    ctx = build_persona_context(fixture, "RID")
    assert ctx["run_id"] == "RID"
    assert ctx["source_org"] == "earthmover-ingest-evals"
    assert ctx["output_repo"].endswith("/RID")


def test_persona_brief_substitutes_placeholders():
    fixture = load_fixture("era5-happy")
    ctx = build_persona_context(fixture, "RID")
    brief = load_persona_brief("climate-scientist", ctx)
    assert "earthmover-ingest-evals/era5-sample" in brief
    assert "/RID" in brief
    assert "{source_org}" not in brief
    assert "{output_repo}" not in brief


def test_minimal_persona_loads():
    brief = load_persona_brief("minimal", {})
    assert "JSON" in brief
