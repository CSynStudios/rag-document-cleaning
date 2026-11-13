# Document preparation for retrieval

**Independent Project Showcase**

The pipeline converts mixed HTML/text/PDF inputs into auditable retrieval-preparation artifacts. It combines source-preserving extraction, explicit duplicate decisions, locally executed PII detection and overlapping chunks linked by source IDs.

The public evaluation retained 4 source documents and exported 62 chunks. The test suite verifies invalid-input handling, detector examples and chunk reconstruction. PII actions are reported rather than presented as guaranteed anonymization; retrieval relevance remains a downstream evaluation task.

See VERIFICATION.md for evidence and GUIDANCE.md for decisions. The implementation, setup and tests are public; source corpora and generated content remain local.
