# Axial-member strength and stability case

- Case ID: `AXIAL-RUN-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `equation_5_resistance_branch`: `yield`
- `equation_5_strength_utilization`: 0.591549295775
- `equation_5_pass`: `True`
- `relative_slenderness`: 2
- `section_type`: `b`
- `stability_coefficient_phi`: 0.826129256441
- `table_d1_phi`: 0.826
- `table_d1_lookup_status`: `exact_node_available`
- `equation_7_stability_utilization`: 0.596707770165
- `equation_7_pass`: `True`
- `table_6_alpha1`: 1.45
- `table_6_alpha2`: 0.36
- `table_6_beta`: 1
- `single_angle_working_condition_factor_gamma_c1`: 0.601666666667
- `equation_6_single_angle_utilization`: 0.889685514095
- `equation_6_pass`: `True`

## Scope limitation

LEGACY multi-check diagnostic retained for backward compatibility. It evaluates equation (5), compression stability and the special single-angle branch together and is NOT the Stage N3 qualified applicability-safe workflow. Use action axial_member_guided for normative branch selection.
