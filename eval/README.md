# icechunk-datacube-ingestion eval harness

End-to-end eval for the `icechunk-datacube-ingestion` skill. See [PLAN.md](./PLAN.md)
for the full design.

## Layout

- `icechunk_eval/` — Python package (run-id, JSONL store, redactor, schema models, SDK loop, persona, metrics).
- `tests/` — unit tests for the plumbing modules.
- `fixtures/` — per-fixture YAML configs (source data location, persona reference, expected results).
- `personas/` — Markdown persona briefs used to drive the user side of each run.
- `judges/` — Markdown prompts for LLM-judged metrics.
- `runs/` — output. `runs.jsonl` holds one row per run; `<run-id>/` holds per-run transcripts and judge outputs.

## Run

```sh
cd eval
uv sync
uv run pytest
```

End-to-end runs land in Phase 2. For now Phase 1 ships plumbing only.
