# Stage N6 guided built-up beam-column case

- Case ID: `N6-GUIDED-BUILTUP-BEAMCOL-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `status`: `COMPLETE`
- `whole_member`: `{'table8_selected_route': {'section_type': 1, 'connector_system': 'lattice', 'equation': 15, 'effective_slenderness': 43.945989578117356, 'source_table': '8'}, 'effective_relative_slenderness': 1.4999999999999998, 'central_phi_type_b': 0.8934180916680712, 'eccentricity_mm': 100.0, 'relative_eccentricity_m_eq123': 1.0, 'd4': {'status': 'D4_EXACT_NODE', 'phi_e': 0.454, 'route': 'equation_109_with_table_d4', 'source': 'table_D.4_exact_node_no_interpolation'}, 'stability_check': {'equation': '109', 'utilization': 0.2898214699744957, 'pass': True}}`
- `branch`: `{'additional_force': {'status': 'RESOLVED_9.3.3', 'value_n': 75000.0, 'formula': 'Nad=My/b'}, 'check': {'status': 'EVALUATED_9.3.3_EQ7', 'design_force_n': 225000.0, 'assessment': {'branch_relative_slenderness': 1.2, 'member_effective_relative_slenderness': 1.4999999999999998, 'basic_2_7_limit_pass': True, 'not_above_member_effective_slenderness': True, 'absolute_4_1_limit_pass': True, 'clause_7_2_5_check_performed': False, 'classification': 'basic_limits_satisfied', 'permitted': True}, 'phi_branch': 0.9270964896156061, 'phi_source': 'clause_9.3.3_equation_7_with_clause_7.1.3_equation_8', 'utilization': 0.2128887588976469, 'pass': True}}`
- `connectors`: `{'fictitious_shear_force_n': 3533.312151879736, 'governing_shear_force_n': 5000.0, 'governing_source': 'actual', 'lattice_required': True}`
- `local_stability`: `{'web': {'status': 'COMPLETE', 'section_type': 1, 'actual_relative_slenderness': 1.0239842231794338, 'limit': 1.6375, 'base_table22_limit_before_two_plane_factor': 1.6375, 'stress_parameters': None, 'equation_131': None, 'two_plane_factor': 1.0, 'reduced_area_route': {'reduced_area_required': False, 'applicable_section_type_and_alpha': True, 'equations_using_reduced_area': [], 'reduced_area_source': None}, 'transverse_stiffener': None, 'longitudinal_stiffener': None, 'required_unresolved': [], 'pass': True}, 'flange': {'status': 'COMPLETE', 'section_type': 1, 'actual_relative_slenderness': 0.22755204959542974, 'limit': 0.4745, 'two_plane_factor': 1.0, 'pass': True}}`
- `required_unresolved`: `[]`
- `governing_utilization`: 0.289821469974
- `pass`: `True`
- `trace_policy`: `SELECTED_9.3_TOPOLOGY_ONLY_EXACT_D4_EXPLICIT_TABLE22_TABLE23_INTERPOLATION`

## Scope limitation

Stage N6 applicability-safe built-up beam-column and combined local-stability workflow for current SP16 clauses 9.3-9.4. Stage N3 Table-8/equation-18 and Stage N5 equation-109 primitives are reused. Table D.4 is exact-node only unless an explicitly sourced external phi_e is supplied; the explicit interpolation rules printed in Tables 22 and 23 are retained. Topology-specific branch analyses not fully determined by clauses 9.3.3-9.3.6 remain fail-closed rather than inferred.
