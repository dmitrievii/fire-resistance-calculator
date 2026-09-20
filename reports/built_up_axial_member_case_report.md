# Built-up axial-member case

- Case ID: `BUILTUP-EXAMPLE-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `clause_7_2_1_strength_utilization`: 0.469483568075
- `clause_7_2_1_strength_pass`: `True`
- `clause_7_2_2_method`: `table_8_effective_slenderness`
- `equation_12_battened_type_1_effective_slenderness`: 48.8446517031
- `equation_13_battened_type_2_effective_slenderness`: 57.4439278519
- `equation_14_battened_type_3_effective_slenderness`: 53.2673783849
- `equation_15_lattice_type_1_effective_slenderness`: 46.4758001545
- `equation_16_lattice_type_2_effective_slenderness`: 52.91138791
- `equation_17_lattice_type_3_effective_slenderness`: 50.8964635314
- `equation_15_effective_relative_slenderness`: 1.92933410717
- `batten_branch_limit`: `{'branch_relative_slenderness': 1.2, 'limit': 1.4, 'pass': True}`
- `lattice_branch_assessment`: `{'branch_relative_slenderness': 3.0, 'member_effective_relative_slenderness': 1.9293341071694603, 'basic_2_7_limit_pass': False, 'not_above_member_effective_slenderness': False, 'absolute_4_1_limit_pass': True, 'clause_7_2_5_check_performed': True, 'classification': 'permitted_only_with_clause_7_2_5', 'permitted': True}`
- `lattice_stability`: `{'overall_stability_coefficient_phi': 0.836647845566822, 'branch_stability_coefficient_phi_1': 0.8726157350616202, 'reduced_design_resistance_phi_1_ry_n_mm2': 309.7785859468752, 'utilization': 0.617342096680375}`
- `close_contact_spacing`: `{'force_state': 'compression', 'maximum_spacing_mm': 400.0, 'spacing_pass': True, 'intermediate_connection_count': 2, 'intermediate_connection_count_pass': True, 'pass': True}`
- `equation_18_fictitious_shear_force_n`: 11962.4867086
- `fictitious_shear_distribution`: `{'distribution_mode': 'connectors_only', 'connector_system_count': 2, 'per_connector_system_force_n': 5981.243354313406, 'solid_sheet_force_n': 0.0, 'total_assigned_force_n': 11962.486708626811}`
- `equation_19_batten_shear_force_n`: 14953.1083858
- `equation_20_batten_bending_moment_n_mm`: 2990621.67716
- `equation_21_lattice_diagonal_force_n`: 4485.93251574
- `equation_22_alpha_2`: 1.74418604651
- `equation_22_additional_diagonal_force_n`: 69767.4418605
- `clause_7_2_10_brace_design_force_n`: 11962.4867086
- `clause_7_2_10_column_spacer_force_n`: 11962.4867086

## Scope limitation

LEGACY exhaustive multi-formula diagnostic retained for backward compatibility. It evaluates all Table 8 formulas and is NOT the Stage N3 qualified branch-safe workflow. Use action built_up_axial_member_guided, which evaluates only the selected normative route.
