# Implementation guidance

This file holds the reasoning and guidance that would otherwise appear as code comments. Python source and tests contain no comments or docstrings.

## Why the implementation is small

One cleaner and one fixed-source downloader separate offline transformation from network acquisition. There is no service, plugin architecture or configuration framework. Limits and transformation settings are constants recorded in every report. The only command arguments select input and output folders.

Beautiful Soup handles HTML parsing rather than trying to remove markup with regular expressions. Datasketch supplies a tested MinHash/LSH implementation. Its NumPy and SciPy dependencies are installed because datasketch requires them. Soupsieve and typing_extensions are dependencies of Beautiful Soup. The standard library handles downloads, hashing, JSON, Unicode normalization, contact patterns and command-line arguments.

The Veyra workspace uses one shared Conda prefix environment with Python 3.12.16, located two directories above this repository. An independent clone can use its own environment specification. Datasketch was unavailable in the configured defaults channel, so both application libraries and their dependencies are installed with pip inside that environment. `requirements.txt` pins all six application packages; `requirements-dev.txt` adds pytest. `conda-win-64-explicit.txt` records the Windows Conda packages. For those exact Windows builds, create the environment from the explicit file, activate it, then install requirements.txt with pip. Keep those layers distinct when rebuilding.

## Inspect a run

1. Open `report.json` and reconcile its status counts with the input count. Rejections are explicit and should be reviewed before using the output.
2. Use the sample's local `sources.json` to resolve source IDs. Compare retained text with the originals to check for missing headings, lost punctuation or over-aggressive boilerplate removal.
3. Review every near-duplicate decision before accepting it. Jaccard measures word-shingle overlap rather than meaning. Two revisions can be highly similar but contain different advice. Originals remain available for correction.
4. Search retained documents and chunks for contact examples you expect to be removed. Names, addresses, secrets and unsupported identifiers need a separate review.
5. Inspect chunk boundaries and their overlap. Word offsets refer to the redacted, whitespace-normalized document, not HTML or byte positions. Verify retrieval quality separately before describing these chunks as useful to a particular RAG application.

## Boundaries that affect interpretation

Deduplication compares cleaned text before contact redaction. MinHash proposes candidates; exact Jaccard makes the removal decision. The search is approximate, so direct confirmation reduces false-positive decisions among candidates but cannot guarantee all duplicates are found. Deterministic sorting, a fixed seed and pinned packages make repeated runs over unchanged inputs comparable.

Contact counts apply to retained documents only. A near duplicate might contain additional contacts; its text is excluded from output. Cleaning is a whole-corpus operation within a 200-document, 2-MB-per-file bound, with retained text and shingle sets held in memory. It is not a streaming or large-scale benchmark.

Opaque source IDs reduce accidental filename exposure; hashes do not provide anonymization. Output text may still contain sensitive content outside the narrow supported patterns. Source manifests contain filenames and acquisition metadata and stay local.

The downloader rejects an existing destination, limits each response and downloads only fixed official URLs. Cleaning rejects existing output directories. An interrupted write may leave an incomplete run; choose another run folder after resolving the cause. HTML/text only, UTF-8 only, no browser rendering, no OCR and no semantic layout preservation.

## Next project step

Build a labeled synthetic evaluation for redaction and duplicate decisions before expanding claims. Consider Presidio when adding names and other PII requires NLP, evaluate its language/model behavior and keep the model setup reproducible. Add PDF support only against a concrete sample. Leave the tabular and multimodal projects at their scaffolds until this first case study has been reviewed.

The showcase is published as the public repository CSynStudios/rag-document-cleaning. Source corpora, outputs and private content remain excluded. The case study reports the verified demonstration and its limits.

## API references checked during implementation

- [Beautiful Soup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/): HTML parsing, CSS selection, decomposition and text extraction.
- [datasketch MinHash](https://ekzhu.com/datasketch/minhash.html) and [MinHash LSH](https://ekzhu.com/datasketch/lsh.html): signatures, candidate lookup and approximate matching.
- [Python urllib.request](https://docs.python.org/3.12/library/urllib.request.html): fixed-source HTTP downloads with timeouts.
