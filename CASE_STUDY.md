# Preparing web documentation for retrieval

**Independent Project Showcase**

## Problem

Web documentation contains navigation, scripts, repeated page furniture and formatting that can distract a text retrieval system. Collections can also contain duplicate content and contact details that should be reviewed before ingestion. A useful preparation pipeline needs inspectable outputs and a record of what it removed.

## Implementation

The project uses a local Python command-line pipeline for UTF-8 HTML and plain text. Beautiful Soup extracts the main text and removes common page furniture. A content hash detects exact copies; datasketch MinHash LSH proposes similar documents, followed by direct comparison of five-word shingles before any near-duplicate removal.

The pipeline replaces email addresses and a documented set of phone formats with markers, then creates overlapping chunks of up to 180 words. It produces retained-document records, chunk records and a decision report. It preserves input files and refuses to overwrite a previous output folder.

## Evidence

A local run over three official Python documentation pages retained 8,957 words and produced 61 chunks. The measured cleaning invocation took 1.657 seconds, including Python startup. These measurements apply to the documented input collection. Larger-scale throughput has not been benchmarked.

Nineteen project tests passed, covering redaction examples, duplicate handling, chunk reconstruction and invalid-file boundaries. Two additional workspace scaffold checks brought the original combined suite to twenty-one. A synthetic eight-file case retained two documents, identified one exact and one near duplicate, and reported four invalid inputs. The environment was successfully rebuilt from its recorded configuration and passed the same test suite.

## Limits

Redaction covers selected contact patterns; names, addresses, secrets and other identifiers require further work and review. Duplicate similarity does not measure meaning, so a small but important revision can require manual retention. HTML code and table layout are flattened. Retrieval quality, PDF extraction and production-scale performance have not been tested.

Source code and documentation are published at [CSynStudios/rag-document-cleaning](https://github.com/CSynStudios/rag-document-cleaning). Downloaded sources and generated outputs remain local. Supporting details and exact boundaries are recorded in VERIFICATION.md and GUIDANCE.md.
