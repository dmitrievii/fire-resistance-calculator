# Reconstruction provenance — v0.22 r1

- Baseline archive: `standard_package_v0.21_reconstruction_assessment.zip`
- Baseline SHA-256: `140868b2ebafcb430f7cfd40727a642b79d54d1fff423a48c10f35c057c8b15e`
- Target logical phase: `v0.22_final_annex_and_release_consolidation`
- Reconstruction identity: `v0.22_final_annex_and_release_consolidation_reconstructed_r1`
- Historical v0.22 binary: unavailable in the active workspace/File Library; therefore this package does not claim byte identity.
- Surviving evidence used: historical v0.22 API-freeze records and later direct-function regression records for equations (10)-(11), plus the supplied СП 16.13330.2017 consolidated normative source.

## Deliberate corrections relative to the historical completion claim

1. Annex Б/В/Г/И tables are **not** marked as implemented numeric data unless a complete audited machine transcription exists. Twenty-four such tables are explicit external-reference boundaries.
2. Table 1 includes its Note 5 default and is exposed only as exact categorical lookup.
3. Schema validation is recursive and rejects NaN/infinity.
4. Validation reports distinguish cumulative internal regression/transcription checks from independent external certification.

This reconstruction is intended as an auditable continuation point, not as proof that every external normative dependency is automated.
