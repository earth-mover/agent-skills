# Eval Harness — Design Plan

**Status:** Phase 1 + most of Phase 2 landed. Live smoke run pending.
**Last updated:** 2026-05-12

## Goal

Evaluate the `icechunk-datacube-ingestion` skill end-to-end on representative fixtures, capturing both deterministic and LLM-judged metrics. Track runs over time in version control so skill PRs surface their own metric deltas in the diff.

## Scope (v0)

- One file format (netCDF).
- Three fixtures: 1 happy path + 2 failure modes.
- Agent under test: Opus 4.7.
- Persona / LLM judges: Haiku 4.5.
- Single-tenant: harness runs locally; not wired to CI.

**Out of scope for v0:** multi-format matrix, regression alerting, dashboards, CI integration, cost budgeting.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│ harness.py (Claude Agent SDK)                            │
│                                                          │
│   spawns ────► agent-under-test                          │
│                (loads ../icechunk-datacube-ingestion/    │
│                 SKILL.md)                                │
│                         │                                │
│                         ▼                                │
│   answers ◄──── AskUserQuestion ──► persona (Haiku)      │
│                                                          │
│   captures: tokens, transcript, tool calls, timing       │
│                                                          │
│   on completion ─► deterministic checks + LLM judges     │
│                         │                                │
│                         ▼                                │
│   writes: runs.jsonl row, per-run transcript dir,        │
│           Icechunk artifact to Arraylake                 │
└──────────────────────────────────────────────────────────┘
```

## Decisions

### Runner: Claude Agent SDK (Python)

Only option that gives both (a) the ability to simulate user responses to `AskUserQuestion` and (b) cheap, structured access to tool calls (needed for *skills loaded* and *steps in order* metrics).

- Headless `claude -p` rejected: can't intercept user-facing questions.
- Inspect AI / third-party framework rejected: extra dependency surface for v0.

### User simulation: LLM persona only

One free-form persona brief per fixture (role + dataset facts + preferences). Persona LLM answers whatever the agent asks.

- Persona model: Haiku 4.5, temperature 0.
- Slot-based scripting deferred — accept non-determinism in exchange for robustness to skill rephrasing.
- If unscripted-question rate becomes a useful signal later, layer a slot system in front.

### Fixtures: Arraylake-managed source data

Each fixture YAML references an Arraylake repo containing the source files. v0: one happy-path netCDF + two failure modes (candidates: inconsistent dim length across files, no read access).

### Storage (split by data type)

| Data | Location | Rationale |
|---|---|---|
| Metrics | `eval/runs/runs.jsonl` | Append-only, uncompressed (diffable on GitHub PRs), queryable via `duckdb.read_json_auto`. No `.duckdb` file in git. |
| Transcripts + persona + judges | `eval/runs/<run-id>/` | Plain JSONL/JSON, uncompressed. Read one run at a time; cross-run diff is not a use case. |
| Produced Icechunk artifact | Arraylake `evals/icechunk-datacube-ingestion/<run-id>` | All runs retained. Dogfoods Arraylake; enables cheap re-validation. |

### Git policy

One commit per run on `main`. Linear, bisect-friendly. Commit message:

```
eval: <fixture> @ <skill-shortsha> → <pass|fail> (<N>/<M> metrics)
```

Skill PRs include their eval commit alongside the skill change.

### Run identification

```
<run-id> = YYYY-MM-DD_HHMMSS_<skill-shortsha>_<fixture>
```

Sortable, traceable to skill version, distinguishes fixtures.

### Secret redaction

Allowlist-based, runs before any transcript write.

- Allowlist: tool name, arg keys, arg values for known-safe keys (e.g. `file_path`, `command` after scrubbing).
- Token-shaped patterns (AWS keys, JWTs, Bearer tokens, Arraylake API tokens) → `<REDACTED>`.
- Environment dumps excluded entirely.

## Metrics

### Deterministic

| Metric | How |
|---|---|
| Time taken | Wall clock around the SDK loop |
| Tokens used | Sum `result.usage` across turns (input, output, cache read, cache write) |
| Skills loaded | Count `Read` tool calls matching `**/SKILL*.md` or `formats/*.md` |
| Coiled compute spent | Post-run Coiled API call by cluster tag = run-id |
| Xarray schema matches | `xr.open_zarr(artifact).identical(reference)` (or schema-only compare) |
| VCCs match | Walk Icechunk manifest, diff VCC set against reference |
| Virtual chunk files match | Enumerate virtual refs, diff against reference |
| Final-timestep values match | `np.testing.assert_allclose` on a slice |

### Fuzzy (LLM judge — Haiku 4.5, temperature 0)

| Metric | Input to judge |
|---|---|
| Followed steps in order? | SKILL.md's step list + the run's tool-call sequence → 0/1 with reasoning |
| Clear README? | The README the agent wrote in its working dir → 1–5 with reasoning |

## `runs.jsonl` row shape

Nested by category so new metrics can be added without disturbing existing keys.

```json
{
  "schema_version": 1,
  "run_id": "2026-05-11_143022_abc1234_era5-happy",
  "meta": {
    "fixture": "era5-happy",
    "skill_sha": "abc1234",
    "harness_sha": "def5678",
    "skill_dirty": false,
    "agent_model": "claude-opus-4-7",
    "persona_model": "claude-haiku-4-5-20251001",
    "started_at": "2026-05-11T14:30:22Z",
    "ended_at": "2026-05-11T14:42:11Z"
  },
  "deterministic": {
    "time_s": 709.3,
    "tokens": {
      "agent":   {"input": 12345, "output": 6789, "cache_read": 98765, "cache_write": 2345},
      "persona": {"input": 234,   "output": 89,   "cache_read": 0,     "cache_write": 0}
    },
    "skills_loaded": ["icechunk-datacube-ingestion/SKILL.md", "formats/HDF5.md"],
    "num_turns": 12,
    "total_cost_usd": 0.83,
    "coiled_cost_usd": 0.42
  },
  "checks": {
    "schema_match": true,
    "vccs_match": true,
    "virtual_chunk_files_match": true,
    "final_timestep_values_match": true
  },
  "judges": {
    "steps_in_order": {"score": 1, "reasoning": "..."},
    "readme_clarity":  {"score": 4, "reasoning": "..."}
  },
  "outcome": "pass"
}
```

Conventions:
- **Not computed** → field absent (e.g. `coiled_cost_usd` on a run that didn't use Coiled).
- **Computed, failed** → `{"value": null, "error": "..."}` (or `false` for booleans).
- **Outcome**: `"pass"` if every required check + judge passes its threshold; `"fail"` otherwise. Required-set defined per fixture.

## Schema evolution

JSONL handles additive change well; treat the conventions below as the rules of the road.

- **Add a metric** → add an optional field; old rows have it absent. No migration.
- **Stop emitting a metric** → just stop writing it; old rows keep their value.
- **Rename a field** → bump `schema_version`, support both names in readers for one transition window, then drop the old name.
- **Change a field's type** → bump `schema_version`, support both shapes for one window. Avoid where possible by namespacing new variants under a new key.
- **New category of metric** → add a new nested object (`stability: {...}`, `cost: {...}`) rather than expanding the top level.

`schema_version` starts at 1 and only bumps on breaking changes (rename, type change, semantic shift). Additions don't bump it.

## Directory layout

```
agent-skills/
├── icechunk-datacube-ingestion/    # the skill (installed)
│   ├── SKILL.md
│   ├── formats/
│   └── ...
└── eval/                            # harness (never installed)
    ├── PLAN.md                      # this document
    ├── pyproject.toml
    ├── README.md
    ├── .gitattributes
    ├── icechunk_eval/                # Python package (named to avoid shadowing builtin `eval`)
    │   ├── __init__.py
    │   ├── harness.py                # entry point
    │   ├── sdk_loop.py               # SDK plumbing
    │   ├── persona.py                # LLM persona side-channel
    │   ├── run_id.py                 # run-id generator + git introspection
    │   ├── jsonl_store.py            # append/read runs.jsonl
    │   ├── redactor.py               # secret redactor
    │   ├── meta.py                   # pydantic models for meta.yaml / runs.jsonl row
    │   └── metrics/
    │       ├── deterministic.py
    │       └── judges.py
    ├── tests/
    │   ├── test_run_id.py
    │   ├── test_jsonl_store.py
    │   ├── test_redactor.py
    │   └── test_meta.py
    ├── fixtures/
    │   ├── era5-happy.yaml
    │   ├── inconsistent-dim.yaml
    │   └── no-access.yaml
    ├── personas/
    │   └── climate-scientist.md
    ├── judges/
    │   ├── steps-in-order.md
    │   └── readme-clarity.md
    └── runs/
        ├── runs.jsonl
        └── <run-id>/
            ├── meta.yaml
            ├── transcript.jsonl
            ├── persona.jsonl
            └── judges/
                ├── steps-in-order.json
                └── readme-clarity.json
```

## Implementation phases

### Phase 1 — scaffolding (plumbing, no eval logic)

1. Directory layout, `pyproject.toml`, `.gitattributes`.
2. Run-id generator, `meta.yaml` schema, JSONL appender, redactor.

### Phase 2 — minimal end-to-end loop

3. SDK loop: spawn agent-under-test, persona side-channel, capture transcript. **Landed.**
4. Cheap deterministic metrics: time, tokens (agent + persona), skills_loaded, num_turns, total_cost_usd. **Landed.** Xarray schema match deferred to Phase 3.
5. One happy-path netCDF fixture (`era5-happy`) + persona brief (`climate-scientist`). **Landed.** A `smoke` fixture is also included for plumbing-only runs that don't touch Arraylake.
6. First green run appends a row to `runs.jsonl`. **Pending** — needs `ANTHROPIC_API_KEY` in env, and for `era5-happy`, the `earthmover-ingest-evals/era5-sample` Arraylake repo to exist.

### Phase 3 — judges and failure modes

7. Two LLM judges (steps-in-order, README clarity).
8. Two failure-mode fixtures.
9. Remaining deterministic metrics: Coiled spend, VCC match, virtual-chunk-files match, final-timestep values.

## Defaults

- Python ≥3.11, `uv` for env/lockfile.
- Agent-under-test model: Opus 4.7 (configured; SDK pin is `>=0.1.81`, will need bump once 0.2.x is on PyPI to use Opus 4.7 extended thinking properly).
- Persona + judge model: Haiku 4.5, temperature 0.
- Fixture Arraylake org/repo naming: TBD when scaffolding fixtures.

## Deferred (not v0)

- Multi-format fixture matrix.
- CI integration.
- Cost budgeting / alerts.
- Dashboards (Motherduck, W&B, etc.).
- Working-tree size mitigation (gzip, LFS) until `eval/runs/` exceeds ~500MB.
