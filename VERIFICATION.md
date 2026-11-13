# Verification record

Release validation on 13 November 2026 used Windows and Python 3.12.16. The document suite contains 21 tests, including actual Presidio/model execution, supported contacts, proper names, credit cards and IP examples; exact/near duplicates; chunk reconstruction; invalid/blank/encrypted PDFs; and acquisition boundaries.

The public run used three official Python HTML documents and one W3C text PDF. It retained 4 documents and produced 62 chunks. Detector-action counts were {"email": 0, "phone": 0, "person": 2}. These counts are not labeled PII accuracy results. Source URLs and SHA-256 values are preserved locally in data/release-sources/sources.json, and results in outputs/release-v1.

The earlier 19-test HTML/contact suite passed on GitHub before this release. The updated workflow installs the pinned English model and runs the expanded suite. Its live result is linked by the README badge. Source data and NLP artifacts are not part of the repository.

Known limits: English proper-name constraints, probabilistic detector errors, no OCR, approximate duplicate candidate retrieval and flattened HTML layout. No claim of complete anonymization or measured retrieval relevance is made.
