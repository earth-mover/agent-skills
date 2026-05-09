---
name: unsupported-file-format
description: Ingest data from a format not immediately supported by Xarray or VirtualiZarr. Use this whenever ingesting a format outside of netCDF/HDF5/Zarr/TIFF/COG/Kerchunk/Parquet is mentioned.
---

# Unsupported File Format

First research if their format actually is one of the supported formats under the hood.
For example the "OME-Zarr" format is really just Native Zarr, and the `h5ad` format is really just HDF5.

If the format is truly unique, search the internet for 3rd-party packages which can read data from this format. 
For native ingestion these will be custom [xarray backends/engines](), and for virtual ingestion these will be [custom parsers]().

If no such package is found, the ingestion is not currently possible, at least not without developing a new software package or significant new feature.
Consider raising an issue on Xarray/VirtualiZarr's github repository asking for support for this format.