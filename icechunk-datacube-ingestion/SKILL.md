---
name: icechunk-datacube-ingestion
description: Ingest data from array file formats into an Icechunk or Arraylake repository as a single Zarr datacube. Use this skill whenever the user mentions archival array or scientific file formats such as netCDF/HDF5/TIFF/GRIB/Zarr; cloud-optimized or ARCO (Analysis-Ready Cloud-Optimized) data; creating, converting or moving data to Icechunk/Zarr/Xarray/Kerchunk datacubes, files, repositories, or stores; experimenting with Icechunk or Arraylake; or any mention whatsoever of wanting virtual Zarr/virtual chunks/VirtualiZarr/Kerchunk.
---

# Icechunk Datacube Ingestion

## Goal

The goal is to take a scientific dataset (potentially consisting of a large number of individual files) stored in a compatible file format and convert it to a single Icechunk or Arraylake repository.

This goal will be achieved once the user has succesfully created a single Icechunk Repository containing or referring to the original data, where the resultant repo meets these requirements:

- [ ] Single Icechunk / Arraylake store (not multiple stores - instead prefer multiple groups in the same store),
- [ ] Simple datacube structure,
- [ ] Contains the correct data values,
- [ ] Has appropriate metadata (e.g. CF conventions or GeoZarr),
- [ ] Contains all the requested data,
- [ ] Is efficient to open and access.

## Prerequisites

### Required packages

To achieve this goal the user MUST install the following python packages: `icechunk`, `zarr`, and `xarray`. 
They will likely also need to install further packages to read specific file formats (e.g. `h5netcdf` to read netCDF4 files).
If they want to do virtual ingestion they will need to install `VirtualiZarr`, and if they want to use Arraylake they will need to install the arraylake python client.

### Supported file formats

The user's data MUST be in a format that either Xarray or VirtualiZarr can read.

If the user, dataset documentation, or your bucket scan mentions any of these file formats, read the corresponding skill.

- **Zarr v2/v3** - (Also known as "native Zarr format", or just a "Zarr store".) Read [./formats/ZARR.md](./formats/ZARR.md).
- **HDF5/NetCDF4** - Read [./formats/HDF5.md](./formats/HDF5.md).
- **NetCDF3** - Read [./formats/NETCDF3.md](./formats/NETCDF3.md).
- **TIFF/GeoTIFF/COG** - Read [./formats/TIFF.md](./formats/TIFF.md).
- **GRIB** - Read [./formats/GRIB.md](./formats/GRIB.md).
- **Kerchunk** - (Including "Kerchunk JSON" or "Kerchunk Parquet".) Read [./formats/KERCHUNK.md](./formats/KERCHUNK.md).
- **Parquet** - Read [./formats/PARQUET.md](./formats/PARQUET.md).

If you suspect the data is in any other format not in this list, read [./formats/UNSUPPORTED-FILE-FORMAT.md](./formats/UNSUPPORTED-FILE-FORMAT.md).

## Order of operations

This is a complex task consisting of multiple steps which MUST be performed in order.
This is CRUCIAL to avoid wasting time and resources deploying large ingestion jobs that then inevitably fail.

### Checklist

It is therefore preferable to collect as much information and validate as much as possible up-front.
Every dataset is different, so it is important to gain information about the dataset and the user intent iteratively, then adapt to any problems or requests that come up.

In order, you must:

1. [ ] **Collect information about the dataset and requirements from the user** - follow the instructions in [COLLECT-DATACUBE-INGESTION-REQUIREMENTS.md](./COLLECT-DATACUBE-INGESTION-REQUIREMENTS.md).
2. [ ] **Confirm read access to the data location** - ask the user which Arraylake bucket config their data is in (prompting them to create the config if they have not done so already), then use that bucket config nickname with the Arraylake client's new `.get_obstore_for_bucket()` method ([docs](https://docs.earthmover.io/reference/client#get_obstore_for_bucket)) and check that you can list bucket prefixes using obstore.
3. [ ] **Scan the bucket contents** - Use the obstore object to list bucket prefixes and contents to establish the directory structure of the user's data. Create an xarray schema for the files you expect to find using `pandera.xarray`.
4. [ ] **Plan ingestion** - Examine the file URL structure (date, hour, variable, step, etc.).
    Based on coordinates/values and URL patterns, determine appropriate glob pattern for related files.
    Many datasets use folder structure to organize files by model runs, years, months, or days. Infer the concatenated dataset structure. Based on the discovery results and file list, reason about what the concatenated dataset will look like. Create an xarray-repr-like schema for the expected result, show it to the user and ask them to confirm that looks correct.

    Example reasoning:

        Single file: Dataset with dims (time: 1, step: 209, lat: 405, lon: 2161)
        Files found: 4 files (4 model runs for a single day)
        Concat dimension: time
        → Final dataset: Dataset with dims (time: 4, step: 209, lat: 405, lon: 2161)

5. [ ] **Check assumptions and requirements** - for example check that the various files actually do follow the expected `pandera.xarray` schema. The [VirtualiZarr documentation on declarative schema validation](https://virtualizarr.readthedocs.io/en/stable/how_to/validation.html) is useful here.
6. [ ] **Execute ingestion** - First try ingesting a small representative subset of the files. Start by creating an new Arraylake repo in an org and with a name of the user's choosing. Read the files, concatenating, and write to the Arraylake repo. Then scale up the same pattern using Dask. Check with the user before deploying any dask clusters. 
7. [ ] **Validate success** - Assert that loading data directly from one of the original files using Xarray gives the same result as loading the equivalent subset of data from the resultant Icechunk store (again using xarray).

### Recording progress

Only move on once the previous step has been verified as completed.
When a step has been completed, keep track in a `INGESTION-PROGRESS.md` planning file.
This is also a good place for notes on discoveries about the data, and useful to potentially hand off or resume by another agent later.
Check if such a file already exists in the current directory using `bash read ./INGESTION-PROGRESS.md`.

### Iteration

You may need to iterate back and forth multiple times between steps 4 (planning ingestion), 5 (confirming assumptions and requirements), 6 (attempting to execute the ingestion), and 7.

## Scale

Users may ask to ingest datasets containing very large amounts of data - potentially multiple PetaBytes.
This necessitates performing validation on small subsets where possible, and thinking carefully about workload size and necessity before deployment of resources.

Very large datasets are also usually good candidates for virtual-ingestion, so explicitly suggest virtual ingestion to the user.

If the dataset is beyond a few 10's of GBs in size, read the [scaling-best-practices](https://virtualizarr.readthedocs.io/en/stable/scaling.html), and keep it in mind during all tasks.

Regardless, any task taking longer than a few minutes should be killed and re-evaluated.

## Giving up on impossible cases

It is possible that the user's request to ingest their data cannot be fulfilled, for one of a number of reasons.
If any of these hard blockers seem plausible for this particular dataset, or the user requests a result that cannot be satisfied, prefer to first carefully check assumptions, then fail early as loudly and clearly as possible, rather than wasting time on a futile search for impossible workarounds.

In order of importance, some of most likely reasons for a request being unfulfillable are:

- **Unable to access data** - Data that cannot be accessed cannot be imported.
- **Data is not array-like** - Data that is not array-like cannot be transformed to the Zarr data model.
- **Data is in an unknown format** - Data that is in an unknown format generally cannot be ingested (but read [./formats/UNSUPPORTED.md](./formats/UNSUPPORTED.md) before giving up).
- **Data's overall structure is too complex** - Data that cannot be neatly mapped to one or a few datacubes (e.g. due to dimensions of inconsistent length) should not be ingested.
- **Unexpected bugs are encountered in tools** - If you encounter any weird behaviour or bugs in a tool (such as Xarray, VirtualiZarr, Icechunk, or a file-format-specific reader), then stop, report them to the user, and suggest raising an issue on Github upstream.
