---
name: collect-datacube-ingestion-requirements
description: Collect both information about a scientific array dataset for ingestion, and requirements from the user about ingestion preferences. Always use before attempting any ingestion of data into Icechunk or Arraylake.
---

# Collect Datacube Ingestion Requirements

The task is to collect and summarize key information about the format and structure of this dataset, both from any documentation sources and prompting the user for their knowledge.

## Documentation

### Prompt user for documentation

First ask the user specifically:

"Is there any relevant documentation about this dataset? Please provide a URL or copy-paste it for me."

Provide them the option to say "I don't know", making that the default option.

### No known documentation

If the user does not know of any documentation, use one subagent to look for a README file in the data location, and another subagent to search the internet for documentation on this dataset.
