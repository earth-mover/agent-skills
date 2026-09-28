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

