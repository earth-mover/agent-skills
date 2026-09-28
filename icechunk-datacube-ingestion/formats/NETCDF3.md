---
name: netcdf3-icechunk-ingestion
description: How to read/parse/ingest NetCDF3 files into Icechunk. Use whenever the user is doing an ingestion into Icechunk or Arraylake and NetCDF3 files are encountered.
---

## Reading NetCDF3 as native chunks

Use `xarray.open_dataset`/`open_mfdataset` with the `scipy` or `netcdf4`
engine, then write with `ds.to_zarr(icechunk_session.store, ...)`.

## Reading HDF5/NetCDF4 as virtual chunks

Use the `virtualizarr.parsers.NetCDF3Parser` VirtualiZarr parser with
`open_virtual_dataset`:

```python
from virtualizarr import open_virtual_dataset
from virtualizarr.parsers import NetCDF3Parser

vds = open_virtual_dataset(
    url=file_url,
    registry=registry,
    parser=NetCDF3Parser(),
    loadable_variables=["time"],  # small/coord variables that need decoding
    decode_times=True,            # only works on variables also in loadable_variables
)
```

## Uncompressed

All NetCDF3 files are uncompressed. This allows slicing within a single source chunk along its largest-stride storage axis — the result is a new chunk reference with a bumped byte offset and a smaller length, no data loaded.
