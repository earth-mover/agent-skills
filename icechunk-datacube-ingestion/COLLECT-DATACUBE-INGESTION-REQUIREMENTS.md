---
name: collect-datacube-ingestion-requirements
description: Collect both information about a scientific array dataset for ingestion, and requirements from the user about ingestion preferences. Always use before attempting any ingestion of data into Icechunk or Arraylake.
---

# Collect Datacube Ingestion Requirements

The task is to collect and summarize key information about the format and structure of this dataset, as well as user preferences about the resultant ingested store, both from any documentation sources and prompting the user for their knowledge.

## Documentation?

### Prompt user for documentation

First ask the user specifically:

"Is there any relevant documentation about this dataset? Please provide a URL or copy-paste it for me."

Provide them the option to say "I don't know", making that the default option.

### No known documentation

If the user does not know of any documentation, use one subagent to look for a README file in the data location, and another subagent to search the internet for documentation on this dataset.

## Virtual or Native ingestion?

Ask the user:

"Do you want to try ingesting the data as virtual references or as native chunks? Virtual references do not require copying the original data files, but do depend on those original files being left untouched. Native chunks creates a standalone Icechunk store."

## Schema requirements?

Ask the user:

"Do you have any preferences for how you want to organize the resultant data?"

## Query patterns?

Ask the user:

"How do you expect users of your resulting data store to query the data? e.g. timeseries queries? global maps? ensemble statistics?"

## User resources?

Ask the user:

"What resources do you have available to run on? e.g. only a local machine? Do you have a Coiled account? Do you usually use some other type of compute orchestration such as Prefect?"

## Summarize

Summarize all answers to the questions and write them down as an `INGESTION_REQUIREMENTS.md` file for later reference.
