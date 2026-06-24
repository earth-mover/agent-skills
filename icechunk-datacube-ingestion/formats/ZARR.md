---
name: zarr-icechunk-ingestion
description: How to read/parse/ingest existing Zarr v2/v3 stores into Icechunk. Use whenever the user is doing an ingestion into Icechunk or Arraylake and Zarr files are encountered.
---

## Reading Zarr as Native chunks

Use `xarray.open_zarr` to open the Zarr store with xarray.

## Reading Zarr as Virtual chunks

Use the `virtualizarr.parsers.ZarrParser` VirtualiZarr parser, e.g:

```python
from virtualizarr import open_virtual_dataset
from virtualizarr.parsers import ZarrParser

vds = open_virtual_dataset(
    url=file_url,
    registry=registry,
    parser=ZarrParser(),
)
```

If the Zarr store to be ingested contains more than 50 million chunks, read https://virtualizarr.readthedocs.io/en/stable/scaling.html#splitting-a-single-large-virtual-dataset-across-commits.