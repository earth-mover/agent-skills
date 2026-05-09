---
name: icechunk-datacube-ingestion
description: Ingest data from array file formats into an Icechunk or Arraylake repository as a single Zarr datacube. Use this skill whenever the user mentions archival array or scientific file formats such as netCDF/HDF5/TIFF/GRIB/Zarr; cloud-optimized or ARCO (Analysis-Ready Cloud-Optimized) data; creating, converting or moving data to Icechunk/Zarr/Xarray/Kerchunk datacubes, files, repositories, or stores; experimenting with Icechunk or Arraylake; or any mention whatsoever of wanting virtual Zarr/virtual chunks/VirtualiZarr/Kerchunk.
---

# Icechunk Datacube Ingestion

## Goal

The goal is to take a scientific dataset (potentially consisting of a large number of individual files) stored in a compatible file format and convert it to a single Icechunk or Arraylake repository.

This goal will be achieved once the user has succesfully created a single Icechunk Repository containing or referring to the original data, where the resultant repo meets these requirements:

- [ ] Single Icechunk / Arraylake store (not multiple stores - instead prefer multiple groups in the same store),
- [ ] Simple datacube structure (to verify this see []),
- [ ] Contains the correct data values (to verify this for a representative subset of data see []),
- [ ] Contains all the requested data (to verify this for the complete result see []),
- [ ] Is efficient to open and access (to verify this or the complete result see []).

## Prerequisites

### Required packages

To achieve this goal the user MUST install the following python packages: `icechunk`, `zarr`, and `xarray`. 
They will likely also need to install further packages to read specific file formats (e.g. `h5netcdf` to read netCDF4 files).
If they want to do virtual ingestion they will need to install `VirtualiZarr`, and if they want to use Arraylake they will need to install the arraylake python client.

### Supported file formats

The user's data MUST be in a format that either Xarray or VirtualiZarr can read.

If the user, dataset documentation, or your bucket scan mentions any of these file formats, read the corresponding skill.

- **Zarr v2/v3** - (Also known as "native Zarr format", or just a "Zarr store".) Read [./formats/ZARR.md](./formats/ZARR.md).
- **HDF5/NetCDF** - Read [./formats/NETCDF.md](./formats/NETCDF.md).
- **TIFF/GeoTIFF/COG** - Read [./formats/TIFF.md](./formats/TIFF.md).
- **GRIB** - Read [./formats/GRIB.md](./formats/GRIB.md).
- **Kerchunk** - (Including "Kerchunk JSON" or "Kerchunk Parquet".) Read [./formats/KERCHUNK.md](./formats/KERCHUNK.md).
- **Parquet** - Read [./formats/PARQUET.md](./formats/PARQUET.md).

If you suspect the data is in any other format not in this list, read [./formats/UNSUPPORTED-FILE-FORMAT.md](./formats/UNSUPPORTED-FILE-FORMAT.md).

## Order of operations

This is a complex task consisting of multiple steps which MUST be performed in order.
This is CRUCIAL to avoid wasting time and resources deploying large ingestion jobs that then inevitably fail.

It is therefore preferable to collect as much information and validate as much as possible up-front.
Every dataset is different, so it is important to gain information about the dataset and the user intent iteratively, then adapt to any problems or requests that come up.

In order, you must:

1. [ ] **Confirm read access to the data location** - follow the instructions in [CONFIRM-ACCESS.md](./confirm-access/CONFIRM-ACCESS.md).
2. [ ] **Collect information about the dataset and requirements from the user** - follow the instructions in [COLLECT-REQUIREMENTS.md](./collect-requirements/COLLECT-REQUIREMENTS.md).
3. [ ] **Scan the bucket contents** - follow the instructions in [SCAN-BUCKET.md](./scan-bucket/SCAN-bucket.md).
4. [ ] **Plan ingestion** - follow the instructions in [PLAN-INGESTION.md](./scan-bucket/SCAN.md).
5. [ ] **Check assumptions and requirements** - follow the instructions in [check-assumptions.md](./check-assumptions/CHECK-ASSUMPTIONS.md).
6. [ ] **Execute ingestion** - follow the instructions in [execute-ingestion.md](./execute-ingestion/EXECUTE-INGESTION.md).
7. [ ] **Validate success** - follow the instructions in [validate-successful-ingestion.md](./validate-successful-ingestion/VALIDATE-SUCCESSFUL-INGESTION.md).

Only move on once the previous step has been verified as completed.
You may need to iterate back and forth multiple times between steps 4 (planning ingestion), 5 (confirming assumptions and requirements), and 6 (attempting to execute the ingestion).

## Scale

Users may ask to ingest datasets containing very large amounts of data - potentially multiple PetaBytes.
This necessitates performing validation on small subsets where possible, and thinking carefully about workload size and necessity before deployment of resources.

If the dataset is beyond a few 10's of GBs in size, read the [scaling-best-practices](./scaling-best-practices/scaling-best-practices.md), and keep it in mind during all tasks.

Regardless, any task taking longer than a few minutes should be killed and re-evaluated.

## Giving up on impossible cases

It is possible that the user's request to ingest their data cannot be fulfilled, for one of a number of reasons.
If any of these hard blockers seem plausible for this particular dataset, or the user requests a result that cannot be satisfied, prefer to carefully check assumptions, then fail early as loudly and clearly as possible, rather than wasting time on a futile search for impossible workarounds.

In order of importance, some of most likely reasons for a request being unfulfillable are:

- **Unable to access data** - Data that cannot be accessed cannot be imported.
- **Data is not array-like** - Data that is not array-like cannot be transformed to the Zarr data model.
- **Data is in an unknown format** - Data that is in an unknown format generally cannot be ingested (but read [./formats/UNSUPPORTED.md](./formats/UNSUPPORTED.md) before giving up).
- **Data's overall structure is too complex** - Data that cannot be neatly mapped to one or a few datacubes (e.g. due to dimensions of inconsistent length) should not be ingested.
- **Unexpected bugs are encountered in tools** - If you encounter any weird behaviour or bugs in a tool (such as Xarray, VirtualiZarr, Icechunk, or a file-format-specific reader), then read [bugs](./BUGS.md).
