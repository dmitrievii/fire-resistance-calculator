# Stage N3 guided built-up axial-member case

- Case ID: `N3-GUIDED-BUILTUP-001`
- Release: `v0.57_fire_ui24_fire_val1_routing_remediation_r1`

## Results

- `force_state`: `compression`
- `clause_7_2_1_strength`: `{'resistance_branch': {'branch': 'yield', 'force_state': 'compression', 'Ryn_n_mm2': 355.0, 'post_yield_service_possible': False, 'reason': '7.1.1 Ryn <= 440 N/mm2 and no tensile post-yield-service exception', 'source_clause': '7.1.1'}, 'utilization': 0.45714285714285713, 'pass': True}`
- `clause_7_2_2_to_7_2_5_stability`: `{'status': 'route_selected', 'method': 'table_8_effective_slenderness', 'table_8_selected_route': {'section_type': 1, 'connector_system': 'lattice', 'equation': 15, 'effective_slenderness': 46.475800154489, 'source_table': '8'}, 'effective_relative_slenderness': 1.9156990662996523, 'overall_phi_type_b': 0.8386364921019381, 'branch_assessment': {'branch_relative_slenderness': 3.0, 'member_effective_relative_slenderness': 1.9156990662996523, 'basic_2_7_limit_pass': False, 'not_above_member_effective_slenderness': False, 'absolute_4_1_limit_pass': True, 'clause_7_2_5_check_performed': True, 'classification': 'permitted_only_with_clause_7_2_5', 'permitted': True}, 'equation_7_with_7_2_5_if_needed': {'overall_stability_coefficient_phi': 0.8386364921019381, 'branch_stability_coefficient_phi_1': 0.8726157350616202, 'reduced_design_resistance_phi_1_ry_n_mm2': 305.41550727156704, 'utilization': 0.6246764623648117}}`
- `clause_7_2_6_close_contact`: `{'status': 'evaluated', 'force_state': 'compression', 'maximum_spacing_mm': 400.0, 'spacing_pass': True, 'intermediate_connection_count': 2, 'intermediate_connection_count_pass': True, 'pass': True}`
- `clause_7_2_7_to_7_2_10_connectors`: `{'status': 'evaluated', 'equation_18_Qfic_n': 11877.579287785931, 'distribution': {'distribution_mode': 'connectors_only', 'connector_system_count': 2, 'per_connector_system_force_n': 5938.789643892966, 'solid_sheet_force_n': 0.0, 'total_assigned_force_n': 11877.579287785931}, 'equation_21_Nd_n': 4454.092232919724, 'equation_22_alpha2': 1.744186046511628, 'equation_22_Nad_n': 69767.44186046511, 'clause_7_2_10_reduced_length_brace_force_n': 11877.579287785931}`
- `governing_pass_for_evaluated_checks`: `True`

## Scope limitation

Stage N3 guided clauses 7.2.1-7.2.10. Only the selected Table 8 branch is evaluated. For fewer than six panels, Table 8 is not used; required external frame/effective-slenderness routes remain fail-closed rather than being invented.
