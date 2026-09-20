# Built-up beam-column and combined local-stability case

- Case ID: `V11-BUILTUP-BEAM-COLUMN-EXAMPLE`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `equation_123_relative_eccentricity_m`: 2
- `clause_9_3_2_whole_member_route`: `{'route': 'equation_109_with_table_d4', 'phi_e': 0.293, 'whole_member_stability_check_required': True}`
- `equation_124_additional_branch_force_n`: 160000
- `design_branch_compression_force_n`: 660000
- `clause_9_3_7_connector_shear`: `{'governing_shear_force_n': 80000.0, 'governing_source': 'actual', 'lattice_required': True}`
- `actual_web_relative_slenderness`: 2.49075962211
- `table_22_alpha`: 1.33333333333
- `table_22_beta`: 0.3875
- `table_22_type_1_limit`: 2.075
- `equation_127_type_2_limit`: 3.9
- `equation_128_type_3_limit`: 2.92
- `equation_129_type_4_limit`: 0.706225196069
- `equation_130_type_5_limit`: 4.12795348811
- `equation_131_adjusted_web_limit`: 3.44375
- `actual_web_pass_against_adjusted_limit`: `True`
- `actual_flange_relative_slenderness`: 0.389181190955
- `table_23_type_1_limit`: 0.491666666667
- `clause_9_4_8_edge_return_limit`: 0.7375
- `clause_9_4_9_two_plane_factor`: 1.11721976352
- `two_plane_increased_web_limit`: 3.84742556062
- `two_plane_increased_flange_limit`: 0.823949575596

## Scope limitation

Sections 9.3-9.4 scalar formulas and normative routing are implemented. Global frame analysis, branch effective lengths, automatic section classification, Section 16, and complete connection design remain explicit external boundaries.
