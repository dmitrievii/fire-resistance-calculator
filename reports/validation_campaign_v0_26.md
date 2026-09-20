# Phase 0.26 validation campaign

- Release: `v0.26_validation_campaign_remediation_and_corpus_0001_0009_reconstructed_r1`
- Corpus revision: `0009`
- Registered cases: **9**
- Full end-to-end golden cases: **0**
- Focused remediation regression gate: **12/12 PASS**.
- Full cumulative pytest gate: **537/537 PASS**.
- Final cumulative audit: **PASS**.

## Cases

- `VAL-SP16-BEAM-0001` — `PARTIAL_SOURCE_INCONSISTENT`
- `VAL-SP16-BEAMCOL-0008` — `PARTIAL_MATCH_PRODUCTION_REMEDIATED_WITH_OPEN_D3_POLICY`
- `VAL-SP16-BEND-0006` — `PARTIAL_MATCH_SOURCE_AND_RUNNER_REMEDIATED`
- `VAL-SP16-BEND-0007` — `PARTIAL_MATCH_SOURCE_ROUTING_ERROR_AND_RUNNER_REMEDIATED`
- `VAL-SP16-BOLT-0003` — `PARTIAL_MATCH_SOURCE_NORMATIVE_FAIL`
- `VAL-SP16-BOLT-0005` — `PARTIAL_MATCH_SOURCE_NORMATIVE_FAIL`
- `VAL-SP16-BUILTUP-0009` — `PARTIAL_MATCH_PRODUCTION_REMEDIATED_SOURCE_MISSES_BRANCH_FAIL`
- `VAL-SP16-WELD-0002` — `PARTIAL_MATCH_SOURCE_STOPS_BEFORE_LENGTH`
- `VAL-SP16-WELD-0004` — `PARTIAL_MATCH_SOURCE_NORMATIVE_FAIL`

## Qualification

The corpus deliberately preserves mismatches attributable to the external report, revision differences, incomplete applicability data, and implementation defects. A case is not upgraded to golden merely because selected scalar arithmetic matches.
