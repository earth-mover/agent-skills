from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

import yaml

from icechunk_eval import jsonl_store, run_id
from icechunk_eval.meta import RunMeta, write_meta
from icechunk_eval.persona import Persona
from icechunk_eval.redactor import redact_obj
from icechunk_eval.sdk_loop import run_agent

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_DIR = REPO_ROOT / "eval"
SKILL_DIR = REPO_ROOT / "icechunk-datacube-ingestion"

AGENT_MODEL = "claude-opus-4-7"
PERSONA_MODEL = "claude-haiku-4-5-20251001"


def load_fixture(name: str) -> dict[str, Any]:
    path = EVAL_DIR / "fixtures" / f"{name}.yaml"
    with path.open() as f:
        return yaml.safe_load(f)


def load_persona_brief(name: str, context: dict[str, str]) -> str:
    path = EVAL_DIR / "personas" / f"{name}.md"
    text = path.read_text()
    for k, v in context.items():
        text = text.replace(f"{{{k}}}", v)
    return text


def setup_working_dir(rid: str, skill_path: Path) -> Path:
    wd = Path(tempfile.mkdtemp(prefix=f"eval-{rid}-"))
    skills_dir = wd / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    os.symlink(skill_path.resolve(), skills_dir / skill_path.name)
    return wd


def build_persona_context(fixture: dict[str, Any], rid: str) -> dict[str, str]:
    al = fixture.get("arraylake") or {}
    ctx: dict[str, str] = {"run_id": rid}
    if al:
        ctx["source_org"] = al.get("source_org", "")
        ctx["source_repo"] = al.get("source_repo", "")
        ctx["output_org"] = al.get("output_org", "")
        output_template = al.get("output_repo_template", "")
        ctx["output_repo"] = output_template.format(run_id=rid) if output_template else ""
    return ctx


def build_row(rid: str, meta: RunMeta, result: Any, persona: Persona) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "run_id": rid,
        "meta": meta.model_dump(mode="json", exclude={"run_id"}),
        "deterministic": {
            "time_s": round(result.elapsed_s, 2),
            "tokens": {"agent": result.tokens, "persona": persona.tokens},
            "skills_loaded": result.skills_loaded,
            "num_turns": result.num_turns,
            "total_cost_usd": result.total_cost_usd,
        },
        "checks": {},
        "judges": {},
        "outcome": "fail" if result.is_error else "pass",
    }


async def run(fixture_name: str) -> dict[str, Any]:
    fixture = load_fixture(fixture_name)
    rid = run_id.generate_run_id(fixture_name, REPO_ROOT)
    skill_sha = run_id.git_short_sha(REPO_ROOT)
    skill_dirty = run_id.git_dirty(REPO_ROOT)

    persona_brief = load_persona_brief(
        fixture["persona"], build_persona_context(fixture, rid)
    )
    persona = Persona(brief=persona_brief, model=PERSONA_MODEL)

    working_dir = setup_working_dir(rid, SKILL_DIR)
    run_dir = EVAL_DIR / "runs" / rid
    run_dir.mkdir(parents=True, exist_ok=True)

    started_at = dt.datetime.now(dt.UTC)
    meta = RunMeta(
        run_id=rid,
        fixture=fixture_name,
        skill_sha=skill_sha,
        harness_sha=skill_sha,
        skill_dirty=skill_dirty,
        agent_model=AGENT_MODEL,
        persona_model=PERSONA_MODEL,
        started_at=started_at,
    )

    try:
        result = await run_agent(
            prompt=fixture["agent_prompt"],
            cwd=working_dir,
            skill_name=SKILL_DIR.name,
            persona=persona,
            model=AGENT_MODEL,
        )
    finally:
        meta.ended_at = dt.datetime.now(dt.UTC)
        write_meta(run_dir / "meta.yaml", meta)
        shutil.rmtree(working_dir, ignore_errors=True)

    for entry in result.transcript:
        jsonl_store.append_row(run_dir / "transcript.jsonl", redact_obj(entry))
    for entry in persona.transcript:
        jsonl_store.append_row(run_dir / "persona.jsonl", redact_obj(entry))

    row = build_row(rid, meta, result, persona)
    jsonl_store.append_row(EVAL_DIR / "runs" / "runs.jsonl", row)

    print(f"Run {rid}")
    print(f"  outcome:       {row['outcome']}")
    print(f"  time:          {row['deterministic']['time_s']}s")
    print(f"  turns:         {row['deterministic']['num_turns']}")
    print(f"  agent tokens:  {result.tokens}")
    print(f"  persona tokens:{persona.tokens}")
    print(f"  cost (agent):  ${row['deterministic']['total_cost_usd']}")
    print(f"  skills loaded: {len(result.skills_loaded)}")
    print(f"  run dir:       {run_dir}")
    return row


def main() -> None:
    parser = argparse.ArgumentParser(prog="icechunk_eval")
    parser.add_argument("fixture", help="Fixture name (file under eval/fixtures/, sans .yaml)")
    args = parser.parse_args()
    asyncio.run(run(args.fixture))


if __name__ == "__main__":
    main()
