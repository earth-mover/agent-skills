---
name: tiff-icechunk-ingestion
description: How to read/parse/ingest TIFF/GeoTIFF/COG files into Icechunk. Use whenever the user is doing an ingestion into Icechunk or Arraylake and TIFF files are encountered.
---

## Reading TIFF as Native chunks

Use rasterio to open the TIFF with xarray.

## Reading TIFF as Virtual chunks

Use the `virtual_tiff.VirtualTIFF` VirtualiZarr parser from the `virtual_tiff` package, e.g.

```python
from virtualizarr import open_virtual_dataset
from virtual_tiff import VirtualTIFF

vds = open_virtual_dataset(
    url=file_url,
    registry=registry,
    parser=VirtualTIFF(ifd=0),
)
```