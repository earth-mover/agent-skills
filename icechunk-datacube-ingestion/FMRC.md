---
name: fmrc-forecast-collections
description: Structure an Icechunk/Zarr datacube as a Forecast Model Run Collection (FMRC) so tools like rolodex can slice out BestEstimate/ConstantForecast/ConstantOffset views with xarray advanced indexing. Use whenever the user wants the result to be an FMRC, mentions rolodex, "forecast model run collection", or describes source files as separate model runs each holding a time series indexed by lead time / forecast hour / step.
---

# Forecast Model Run Collections (FMRC)

## What this is

A Forecast Model Run Collection stores forecast output as a 2D time grid instead of a flat timeseries:

```
Dataset with dims (time: n_runs, step: n_lead_times, ...)
```

- `time` (a.k.a. `forecast_reference_time`) — one value per model run: when that run was initialized.
- `step` (a.k.a. `forecast_period`) — the lead time / forecast hour axis, shared structure across runs, expressed as a `timedelta64` offset from `time`.

Every (`time`, `step`) cell's actual valid timestamp is `time + step`. This is the layout [rolodex](https://github.com/dcherian/rolodex) expects: it uses xarray advanced (vectorized) indexing over the `time`/`step` grid to pull out views like:

- **BestEstimate** — for each valid time, the value from the most recently initialized run that covers it.
- **ConstantForecast** — the full lead-time series from one specific run.
- **ConstantOffset** — the value at a fixed lead time (e.g. "the 24h-out forecast") across every run.

Read rolodex's docs/README for the exact indexing recipe once the store exists — this skill only covers getting the data into the right shape.


## Two source shapes, two strategies

### 1. File already has separate reference-time and step/lead-time coordinates

Some formats (e.g. GRIB read via `gribberish`) expose `time` (reference time) and `step` (lead time) as distinct coordinates natively. In that case there's no reshaping to do — just make sure the CF attributes are set so downstream tools recognize them:

```python
ds["time"].attrs["standard_name"] = "forecast_reference_time"
ds["step"].attrs["standard_name"] = "forecast_period"
```

Then concatenate files along `time` as usual.

### 2. File only has a single time dimension holding valid times for one run

This is the common case for model output that wasn't written with FMRC in mind: each file has one `time` (or `valid_time`) dimension whose values are the sequence of forecast valid-times for that one run, with no separate reference-time coordinate. You have to derive `step` and the scalar `time` yourself, per file, before concatenating.

Pattern (adapt names to the source dataset's actual dimension/coordinate names):

```python
def fix_ds(ds):
    """Reshape one model-run file into FMRC form: scalar `time`
    (forecast_reference_time) + `step` (forecast_period) dimension."""
    ds = ds.rename_vars(time="valid_time")
    ds = ds.rename_dims(time="step")
    step = (ds.valid_time - ds.valid_time[0]).assign_attrs(
        standard_name="forecast_period"
    )
    time = ds.valid_time[0].assign_attrs(
        standard_name="forecast_reference_time"
    )
    ds = ds.assign_coords(step=step, time=time)
    # valid_time is now redundant (= time + step) and its per-file index
    # would conflict across runs when concatenating virtual datasets
    ds = ds.drop_indexes("valid_time")
    ds = ds.drop_vars("valid_time")
    return ds

per_run_datasets = [fix_ds(open_one_run(url)) for url in run_urls]
combined = xr.concat(
    per_run_datasets,
    dim="time",
    coords="minimal",
    compat="override",
    combine_attrs="override",
)
```

`coords="minimal", compat="override", combine_attrs="override"` matters specifically for **virtual** datasets — see [SKILL.md](./SKILL.md) and the building-virtual-icechunk-stores guidance on concat gotchas; without it, concat will try to compare/broadcast manifest-only coordinate arrays across runs and fail or explode memory.

If reading loads `time`/`valid_time` eagerly, request it as a `loadable_variable` (for virtual ingestion) so the per-file min/rename logic above has real values to work with, not a manifest reference — e.g. `open_virtual_dataset(url, ..., loadable_variables=["time"])`.

## Confirm the shape before scaling up

Before running this across the full file set, do it for 2-3 files, concat them, and show the user the resulting schema — same as the general "Plan ingestion" step in [SKILL.md](./SKILL.md):

```
Single run:  Dataset with dims (step: 209, lat: 405, lon: 2161)
Runs found:  4
→ Final:     Dataset with dims (time: 4, step: 209, lat: 405, lon: 2161)
```

## Edge cases

- **Inhomogeneous step counts across runs** — if different runs have different numbers of forecast steps (e.g. some cut short), a dense `(time, step)` array requires padding the shorter runs. Reindex each per-run dataset onto a common `step` axis (union of all step values seen) before concatenating, rather than truncating to the shortest run — truncation silently drops real forecast data.
- **Multiple variables with different step cadences in the same file** (e.g. hourly vs. 3-hourly output) — these need separate `step` coordinates and can't share one `(time, step)` grid; treat them as separate FMRC datacubes (e.g. separate groups) rather than forcing a merge.
- **Irregular run cadence** (e.g. gaps in `time` when a run was missed) — this is fine; `time` doesn't need to be regularly spaced, only monotonic, for rolodex's BestEstimate logic to work.
