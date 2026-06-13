---
name: grib-icechunk-ingestion
description: How to read/parse/ingest GRIB files into Icechunk. Use whenever the user is doing an ingestion into Icechunk or Arraylake and GRIB files are encountered.
---

All grib reading should be done using the gribberish package. Read the [usage docs](https://github.com/mpiannucci/gribberish/blob/main/python/README.md#usage).

## Reading GRIB as Native chunks

Use the new gribberish xarray backend from the `gribberish` package (v1.1.0 or later), e.g.

`pip install "gribberish[xarray]"`

then

```python
import xarray as xr

vds = xr.open_datatree(
    file_url,
    engine="gribberish"
)
```

## Reading GRIB as Virtual chunks

Use the new `gribberish.virtualizarr.GribberishParser` VirtualiZarr parser from the `gribberish` package (v1.1.0 or later), e.g.

`pip install "gribberish[virtualizarr]"`

then

```python
from virtualizarr import open_virtual_dataset
from gribberish.virtualizarr import GribberishParser

vds = open_virtual_datatree(
    url=file_url,
    registry=registry,
    parser=GribberishParser(),
)
```

## GRIB index files

If any grib index files are present (often identifiable by the file suffix `.index`), pass `use_index=True` to the `GribberishParser` constructor to significantly speed up the parsing.

## Structure

Remember that as GRIB files have complex structure is it often desirable to do considerable reorganization of the data into a neater datacube before writing.
Opening 
