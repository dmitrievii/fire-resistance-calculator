# Antenna-structure case

- Case ID: `V20-DEMO-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `clause_17_1_material_group_route`: `{'component_group': 2, 'group_description': 'solid-web and lattice mast/tower shafts, lattice and diaphragms', 'steel_grade': 'C345', 'is_pipe': True, 'annex_v_route_confirmed': True, 'connection_material_route': 'Section 5; resistances by Section 6 and Annexes V and G', 'pass': True}`
- `clause_17_2_rope_selection`: `{'required_zinc_group': 'СС', 'required_wire_grade': 1, 'use_largest_available_round_wire_diameters': True, 'locked_coil_required': False, 'selected_construction': 'spiral_nonspinning', 'selected_core': 'metallic', 'errors': [], 'pass': True}`
- `clause_17_3_rope_end_alloy`: `{'required_alloy': 'ЦАМ9-1,5Л', 'selected_alloy': 'ЦАМ9-1,5Л', 'pass': True}`
- `clause_17_4_wire_material_route`: `{'annex_b_table_b2_selection_confirmed': True, 'copper_wire_used': False, 'technological_necessity_required': False, 'technological_necessity_confirmed': False, 'pass': True}`
- `clause_17_5_wire_design_tension`: `{'gamma_m': 2.5, 'design_tension_force_n': 100000.0}`
- `table_47_working_condition_factor`: 1.1
- `clause_17_7_support_deviation`: `{'load_case': 'wind_or_ice', 'actual_relative_deviation': 0.008333333333333333, 'limit_denominator': 100.0, 'limit_relative_deviation': 0.01, 'utilization': 0.8333333333333333, 'pass': True}`
- `clause_17_8_erection_connection`: `{'accuracy_class': 'B', 'strength_class': '8.8', 'controlled_pretension_required': True, 'installer_agreement_required': False, 'errors': [], 'pass': True}`
- `clause_17_9_cross_lattice_and_platform`: `{'intersection_tie_required': True, 'intersection_tie_pass': True, 'deflection_limit_mm': 12.0, 'vertical_utilization': 0.8333333333333334, 'horizontal_utilization': 0.6666666666666666, 'vertical_pass': True, 'horizontal_pass': True, 'pass': True}`
- `clause_17_10_diaphragm`: `{'maximum_spacing_mm': 7500.0, 'spacing_utilization': 0.8, 'spacing_pass': True, 'location_pass': True, 'pass': True}`
- `clause_17_11_flange_bolts`: `{'missing_requirements': [], 'pass': True}`
- `clause_17_12_node_detailing`: `{'members_centering_pass': True, 'eccentricity_limit_mm': 30.0, 'eccentricity_requires_node_moment_analysis': False, 'eccentricity_pass': True, 'slot_end_hole_minimum_mm': 24.0, 'slot_end_hole_pass': True, 'pass': True}`
- `clause_17_13_guy_attachment`: `{'guy_centering_pass': True, 'eye_plate_stiffening_pass': True, 'separate_rigid_insert_required': False, 'separate_rigid_insert_pass': True, 'pass': True}`
- `clause_17_14_flexible_insert`: `{'minimum_clear_length_mm': 400.0, 'utilization': 0.8, 'pass': True}`
- `clause_17_15_mechanical_detail_evidence`: `{'standard_detail_used': True, 'strength_tested': True, 'fatigue_tested': True, 'threaded_tension_element': True, 'rounded_thread_root_confirmed': True, 'missing_evidence': [], 'pass': True}`
- `equation_215_minimum_damper_distance_m`: 1.83357574155
- `clause_17_16_vibration_damper_design`: `{'equation_215_minimum_distance_s_m': 1.8335757415498273, 'mandatory_by_span_over_300_m': True, 'errors': [], 'pass': True}`
- `clause_17_17_marking_and_lighting`: `{'external_marking_and_lighting_requirements_confirmed': True, 'pass': True}`
- `clause_17_18_galvanizing`: `{'guy_mechanical_details_galvanized': True, 'insulator_fittings_galvanized': True, 'fasteners_galvanized': True, 'missing_categories': [], 'pass': True}`
- `all_executable_section_17_checks_pass`: `True`

## Scope limitation

Section 17 applies to antenna structures up to 500 m. Equation (215), Table 47, and executable clauses 17.1-17.18 are implemented. Loads and combinations, Annex V and B.2 product selection, rope and wire certificates, global analysis, aeroelastic response, testing records, fabrication quality, marking regulations, and coating inspection remain explicit external boundaries. Equations (216)-(224) belong to Section 18 reconstruction provisions and are not part of v0.20.
