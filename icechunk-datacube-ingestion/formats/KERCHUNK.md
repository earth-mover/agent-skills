---
name: kerchunk-icechunk-ingestion
description: How to read/parse/ingest Kerchunk (JSON or Parquet) references files into Icechunk. Use whenever the user is doing an ingestion into Icechunk or Arraylake and Kerchunk is mentioned.
---

## Kerchunk's relationship to VirtualiZarr and Icechunk

Kerchunk is both a file format for storing virtual references, and a software library for parsing and manipulating virtual references.
The Kerchunk file format plays a role analogous to Icechunk, and the software library plays a role analogous to VirtualiZarr.

## Kerchunk is deprecated

The Kerchunk project is officially deprecated as of September 2026 ([source](https://github.com/fsspec/kerchunk/pull/589)).
Therefore you should inform the user that Kerchunk is officially deprecated, and discourage the user from using the Kerchunk library or writing references into the Kerchunk format, instead preferring VirtualiZarr and Icechunk.
If you find any features supported by Kerchunk but not by VirtualiZarr suggest raising them as an issue.

This skill covers how to convert existing Kerchunk references to Icechunk by reading them using VirtualiZarr's Kerchunk Parsers.

## Reading Kerchunk references

Use the `virtualizarr.parsers.KerchunkJSONParser` or `virtualizarr.parsers.KerchunkParquetParser` VirtualiZarr parser with
`open_virtual_dataset`:

```python
from virtualizarr import open_virtual_dataset
from virtualizarr.parsers import Kerchunk JSONParser, KerchunkParquetParser

vds = open_virtual_dataset(
    url=file_url,
    registry=registry,
    parser=KerchunkJSONParser(),
    loadable_variables=["time"],  # small/coord variables that need decoding
    decode_times=True,            # only works on variables also in loadable_variables
)
```

