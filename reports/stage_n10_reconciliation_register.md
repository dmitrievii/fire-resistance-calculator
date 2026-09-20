# Stage N10 reconciliation register

Release: `v0.36_stage_n10_brittle_fracture_current_sp16_closed_reconstructed_r1`

| ID | Topic | Classification | Resolution |
|---|---|---|---|
| N10-R01 | Clause 13.1 adverse-factor register | `CURRENT_FACTOR_REGISTER_REBASELINE_CLOSED` | Legacy seven-category top-level register is not used by the current route. The guided layer exposes exactly the four adverse factor groups printed in current clause 13.1. |
| N10-R02 | Clause 13.2 legacy partial checklist | `COMPLETE_CONDITIONAL_REQUIREMENT_ROUTING_CLOSED` | A partial supplied subset can no longer imply Section-13 prevention PASS. Every represented current 13.2 requirement is explicit and conditionally mandatory. |
| N10-R03 | Enhanced weld NDT threshold | `STRICT_BOUNDARY_CLOSED` | Enhanced NDT is triggered only when tensile weld-zone stress is strictly greater than 0.4Ry; equality does not trigger the printed greater-than condition. |
| N10-R04 | Cover-plate splice flank-weld termination | `GEOMETRIC_BOUNDARY_CLOSED` | The current 25 mm minimum distance on each side of the splice axis is verified from an explicit provided dimension; geometry is not inferred. |
| N10-R05 | Clause 13.3 lamellar-tearing applicability | `ENGINEERING_CLASSIFICATION_FAIL_CLOSED` | Applicability requires explicit engineering review. A positive conservative screen cannot be suppressed by setting the assessment route false. |
| N10-R06 | Clause 13.4 through-thickness evidence | `EXTERNAL_TEST_AND_CERTIFICATE_GATE_CLOSED` | Missing through-thickness tensile-test evidence or selected rolled-product Z certificate yields INCOMPLETE_FAIL_CLOSED; neither is inferred from steel grade/designation. |
| N10-R07 | Equation (174), Table 37 and Z-quality adequacy | `CURRENT_NUMERIC_ROUTE_CLOSED` | Five printed factors are summed algebraically; printed 0.5/1.1 modifiers are explicit. Selected Z quality must independently satisfy both the minimum Z15/Z25/Z35 route and psi_zr<=psi_zn. |
| N10-R08 | Dedicated NormCAD Section-13 brittle/lamellar case | `NO_DEDICATED_N10_GOLDEN_CASE_FOUND` | Library search found the current normative source but no dedicated NormCAD Section-13 end-to-end oracle. No synthetic golden case was created. |

**Open package/DAG defects:** 0
**Runtime unresolved in declared closed routes:** 0
