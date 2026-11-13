# Implementation guidance

Extraction, duplicate decisions and redaction remain distinct. PDF parsing uses pypdf; HTML parsing uses Beautiful Soup. Exact and near-duplicate comparisons happen before redaction so replacing contact values does not itself create an exact duplicate. LSH proposes candidates; direct shingle Jaccard confirms each removal.

Presidio uses the pinned spaCy medium English model. The proper-name policy requires multiple capitalized words and proper-noun token tags; this reduces technical-heading false positives but can miss single-word, lowercased or linguistically different names. Contact patterns also support Philippine mobile formats. Redaction counts describe detector actions, not independently confirmed identities. Review decisions against the preserved originals and validate rules on the intended corpus.

The report contains opaque source IDs, counts and duplicate links rather than original sensitive snippets or filenames. Source IDs are hashes of relative paths and are not anonymization. Word offsets refer to normalized, redacted text. A PDF without extractable text is reported as empty; OCR is not silently inferred.

Install model/dependency files during setup; cleaning does not download missing models automatically. Output folders are new per run. A write failure can leave an incomplete folder; fix the cause and select a new run directory. Keep all input, model and generated files in ignored local folders.

Code contains no comments or docstrings. This file stores the rationale and operator guidance.
