---
name: hdf5-netcdf4-icechunk-ingestion
description: How to read/parse/ingest HDF5/NetCDF4 files into Icechunk. Use whenever the user is doing an ingestion into Icechunk or Arraylake and HDF5 or NetCDF4 files are encountered.
---

## Reading HDF5/NetCDF4 as native chunks

Use `xarray.open_dataset`/`open_mfdataset` with the `h5netcdf` or `netcdf4`
engine, then write with `ds.to_zarr(icechunk_session.store, ...)`.

## Reading HDF5/NetCDF4 as virtual chunks

Use the `virtualizarr.parsers.HDFParser` VirtualiZarr parser with
`open_virtual_dataset`:

```python
from virtualizarr import open_virtual_dataset
from virtualizarr.parsers import HDFParser

vds = open_virtual_dataset(
    url=file_url,
    registry=registry,
    parser=HDFParser(),
    loadable_variables=["time"],  # small/coord variables that need decoding
    decode_times=True,            # only works on variables also in loadable_variables
)
```

`loadable_variables` defaults to loading only dimension coordinates into
memory (`None`), or pass `[]` to keep everything virtual, or a list of names
to load just those — useful for small coords/scalar metadata, variables that
need decoding (e.g. `time`), or variables with chunking that's inconsistent
across files. `decode_times=True` only decodes variables that are also
listed in `loadable_variables`.

## Registry and virtual chunk container setup

Virtual ingestion needs the source bucket URL configured in three places
that must stay in sync, or reads fail with a vague error rather than an
obvious auth error:

1. `ObjectStoreRegistry` mapping the URL prefix to an `obstore` store, for
   `open_virtual_dataset` to read chunk data referenced by the manifest.
2. The Icechunk repo's `VirtualChunkContainer` (via
   `config.set_virtual_chunk_container(...)`), with a matching `url_prefix`
   and its own store instance.
3. `authorize_virtual_chunk_access`, passed matching credentials when
   calling `Repository.open()`/`Repository.create()`.

## Use the `.vz` accessor, not `.virtualize`

VirtualiZarr renamed its xarray accessor from `.virtualize` to `.vz`.
`.virtualize` still works but is deprecated and raises a warning on every
access. Use `ds.vz.to_icechunk(...)`.

## Check homogeneity before virtualizing, not after

Virtualization only works if all files share the same chunk shape, codec,
and dtype per variable, using codecs Zarr recognizes. Spot-check a sample
file with `h5py` before running a big virtualization job:

```python
import h5py
with h5py.File("file.nc", "r") as f:
    var = f["temperature"]
    print(var.chunks, var.compression, var.dtype)
```

Mixed chunk sizes or unsupported compression otherwise fail with confusing
errors deep inside the concat/write step.

## Normalize each file before concatenating

Real-world NetCDF/HDF5 collections are rarely concat-ready as-is — write a
per-file normalization helper and apply it before `xr.concat`. Concatenating
datasets from `open_virtual_dataset` also needs looser settings than a
normal xarray concat, since these are chunk manifests, not loaded arrays:

```python
xr.concat(
    ds_list, dim="time",
    coords="minimal", compat="override", combine_attrs="override",
)
```
