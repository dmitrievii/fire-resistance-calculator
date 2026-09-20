# FIRE-UI1 v0.43.2 — SP554 Applicability Routing Hotfix

Release: `v0.43.2_fire_ui1_sp554_applicability_routing_hotfix_r1`

Parent: `v0.43.1_fire_ui1_sp16_annex_d3_interpolation_hotfix_r1`

Graph: `sp16_sp554_dag_v0-3-46_sp554_applicability_routing_hotfix`

## Scope

This hotfix closes applicability-routing defects identified during the full SP16 ↔ SP554 DAG/UI audit. It does not alter the numerical expressions of formulas (10.6), (10.7), (11.1) or (11.2); it changes when those formulas are allowed to execute and adds matching fail-closed guards to the direct Python runtime.

### APP-10.2 — formulas (10.6)/(10.7)

Production routing now requires one of the following:

- ordinary I-beam, SP16 NDS class 1; or
- bisteel I-beam, SP16 NDS class 2.

Non-I sections and pipes are excluded from this route. The NDS class is kept distinct from the SP16 stability-curve type `a/b/c`.

### APP-11.7 — Table 21 type 3

The alternate route in clause 11.7 now consumes `sp16_table21_type`. A value of `3` means **section type 3 according to SP16 Table 21**. It is not mapped to `sp16_section_class == 3` and is not related to stability-curve type `c`.

### APP-11.1 — N+M stress state

Formula (11.1) now has explicit applicability to:

- `compression_plus_bending`; or
- `tension_plus_bending`.

Direct runtime rejects other stress states. Tension+bending may execute the strength route (11.1), but compression-stability modes are rejected.

### APP-11.3 / formula (11.2)

In-plane stability formula (11.2) now requires all of:

- `compression_plus_bending`;
- `m_eff <= 20` (`mef_gt_20 == false`);
- constant section;
- moment plane coincident with a symmetry plane.

For `m_eff > 20` the direct runtime fails closed with an explicit instruction to route as a bending member.

## Runtime protection

The same restrictions are enforced in `standard_core.fire_sp554_runtime`; they cannot be bypassed by calling the mechanical FIRE-D2 API directly without the UI/DAG.

## Retained policies

- SP16 Annex D.3 in-domain bilinear interpolation from v0.43.1 remains unchanged.
- D.3 extrapolation remains forbidden.
- FIRE-D2 independent inversion of strength/modulus reduction curves and earliest-critical-temperature governing policy remains unchanged.
- The source-literal `smaller gamma` wording warning remains preserved for traceability.
- `ENGINEERING_USE_READY = False`.
