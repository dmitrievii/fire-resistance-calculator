# Overhead-line and switchyard-support case

- Case ID: `V19-DEMO-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `section_16_applicability_route`: `{'group': 2, 'material_route': 'Section 5 and Annex V', 'bolt_route': 'Table G.3 fatigue route for flange joints and VL supports over 60 m; otherwise non-fatigue route', 'clause_16_3_status': 'excluded_by_amendment_2', 'external_loads_required': True}`
- `table_45_working_condition_factor`: 0.9
- `equation_201_maximum_slenderness`: 12
- `equation_202_maximum_slenderness`: 15
- `clause_16_5_pyramidal_mu`: 2.72222222222
- `equation_203_maximum_slenderness`: 54.4444444444
- `equation_204_relative_eccentricity`: 0.2076
- `equation_205_relative_eccentricity`: 0.18
- `clauses_16_8_to_16_9_auxiliaries`: `{'initial_bow_mm': 15.6, 'equivalent_inertia_mm4': 80000000.0, 'delta': 0.12621359223300976}`
- `equation_206_amplified_moment_n_mm`: 342412307.692
- `equation_207_design_shear_n`: 113664.553846
- `equation_208_additional_chord_force`: `{'candidate_1_n': 57999.99999999999, 'candidate_2_n': 54000.0, 'governing_n': 57999.99999999999}`
- `equations_209_to_212_angle_factors`: `{'route': 'equation_209', 'alpha_m': 1.04125, 'alpha_d': None}`
- `table_46_deformation_check`: `{'applicable': True, 'status': 'checked', 'limit_denominator': 100.0, 'limit_relative_deformation': 0.01, 'utilization': 0.8, 'pass': True}`
- `clauses_16_13_to_16_19_detailing`: `{'clause_16_13_effective_length_route': {'effective_length_mm': 3000.0, 'radius': 'i_min'}, 'clause_16_14_first_lower_brace': {'limit': 160.0, 'actual': 140.0, 'utilization': 0.875, 'pass': True}, 'clause_16_16_diaphragms': {'maximum_spacing_m': 25.0, 'actual_spacing_m': 20.0, 'spacing_pass': True, 'concentrated_load_locations_pass': True, 'chord_break_locations_pass': True, 'pass': True}, 'clause_16_17_single_bolt_edge': {'required_minimum_edge_distance_mm': 40.0, 'actual_edge_distance_mm': 40.0, 'bearing_note_2_table_40_required': False, 'pass': True}, 'clause_16_18_brace_arrangement': {'pass': True}, 'clause_16_19_splice': {'even_total_bolt_count_pass': True, 'maximum_per_leg_each_side': 5, 'gamma_b_multiplier': 1.0, 'pass': True}}`
- `equations_213_to_214_polygonal_tube_wall`: `{'face_count': 10, 'relative_wall_slenderness': 2.0461899237078396, 'relative_wall_slenderness_used': 2.0461899237078396, 'beta': 8.158276699029125, 'psi': 1.0810291209788305, 'raw_critical_stress_n_mm2': 388.46480725803025, 'critical_stress_n_mm2': 345.0, 'equation_213_utilization': 0.2898550724637681, 'equation_213_pass': True, 'linked_round_tube_requirements': ['11.2.1', '11.2.2']}`

## Scope limitation

Section 16 equations (201)-(214), Tables 45-46, and executable clauses 16.1-16.20 are implemented. Loads, combinations, global second-order analysis, section classification, complete node design, and evidence from drawings remain explicit external boundaries. Equation (215) and Table 47 are implemented in the Section 17 antenna-structure route; equations (216)-(224) and Table 48 belong to Section 18 and remain outside v0.20.
