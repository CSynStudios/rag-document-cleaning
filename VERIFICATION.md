# Verification record

Executed on 13 November 2026 in the local Windows workspace using Python 3.12.16. This record describes a working first milestone, not a reviewed production system.

## Automated checks

`python -m pytest -q` passed **21 tests** in the shared environment. The final run completed in 1.69 seconds. These include the two original scaffold checks and document-cleaning tests covering:

- Removal of HTML navigation, scripts, hidden elements and heading-link markers while preserving inline text.
- Supported contact patterns: two synthetic emails and three supported phone formats; an ISO date remains intact. A separate test demonstrates that names and addresses remain outside the detector's scope.
- Chunk bounds, overlap and exact reconstruction of the redacted input across seven boundary lengths.
- An eight-file synthetic corpus: two retained documents, one exact duplicate, one near duplicate, one empty file, one invalid UTF-8 file, one binary file and one oversized file.
- Direct rejection of an unrelated LSH candidate, deterministic repeated output, preservation of existing outputs and rejection of nested output, missing inputs and an excessive document count.
- Omission of contact-bearing filenames from output records.
- Download provenance, destination preservation and rejection of non-HTML responses, using mocked responses without network calls.

`python -m pip check` reported **No broken requirements found**. A clean temporary environment was created from `environment.yml`, including its pip lock file; its dependency check and all 21 tests passed. That temporary environment was then removed, leaving the shared `.conda` as the working environment.

Python token inspection found no comments in the cleaner, downloader or test files. Implementation reasoning is in GUIDANCE.md.

## Public documentation sample

The downloader fetched Python 3.12 documentation for csv, json and textwrap plus a separate license copy. The source manifest records URLs, hashes, byte sizes and a download timestamp of 2026-11-13 09:10:35 UTC. Source content can change upstream; saved hashes identify this acquisition.

The final sample output is in `outputs/document-cleaning/run-002/` inside this project repository. The previous run was preserved.

| Measurement | Observed result |
| --- | --- |
| Input documentation pages | 3 |
| Input HTML bytes, excluding license | 254,007 |
| Retained documents | 3 |
| Rejected or duplicate documents in this public sample | 0 |
| Retained whitespace-separated words | 8,957 |
| Retained text characters | 51,616 |
| Chunks | 61 |
| Observed chunk lengths | 36–180 words |
| Email / phone redactions in this public sample | 0 / 0 |
| One cleaning invocation, including Python startup | 1.657 seconds |

The runtime is a single observation on this machine and small sample, not a throughput benchmark. Overlap means chunk word counts include repeated words. Public sample contact counts do not evaluate detector recall; positive redaction and duplicate behaviors were exercised using the synthetic tests.

A sample text review checked the opening of each retained document, heading-link removal, Unicode replacement-character absence and chunk length limits. This was not a line-by-line editorial review of every output. No embeddings or retrieval evaluation were run.

## Local-only and Git checks

During the initial milestone, the workspace ignore rules were tested in a temporary Git repository. `.conda/python.exe`, `.conda-backup/python.exe`, `data/python-docs/csv.html`, `outputs/document-cleaning/run-001/chunks.jsonl` and `.env` matched the rules. At that initial check, the portfolio folder was not a Git repository and no commits, remote setup or publication had occurred.

The existing environment backup was preserved. GitHub CLI was unavailable during the initial inspection; it was later installed, authenticated as CSynStudios and used for publication.

## Remaining evidence gaps

There is no representative labeled PII benchmark, general duplicate precision/recall evaluation, large-corpus measurement, PDF/OCR validation, semantic chunking, retrieval-quality evaluation or human acceptance review. Names, addresses and unsupported identifiers are not redacted. These limits must accompany any case-study claims.
## Independent showcase verification

After organization into a separate repository, the 19 project tests passed from a portable export containing only the staged repository files (3.04 seconds). This confirms that project code and tests do not depend on sibling portfolio folders. The full local workspace still passed 21 tests, including its two scaffold checks (1.79 seconds).

The project now owns its tests and ignored local sample/output folders. Its requirements.txt and requirements-dev.txt support a standalone Python 3.12 setup; environment.yml supports Conda. The shared workspace environment remains in place. The [first GitHub Actions run](https://github.com/CSynStudios/rag-document-cleaning/actions/runs/43405189860) completed successfully on 13 November 2026: 19 project tests passed in 1.08 seconds on the hosted Linux runner with Python 3.12. A live workflow-status badge is displayed in the README. This is test-suite evidence, not a throughput benchmark.
