# Reconstruction assessment case

- Case ID: `SP16-V021-RECONSTRUCTION-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `clause_18_1_1_technical_condition`: `{'category': 'serviceable', 'required_action': 'normal operation permitted subject to documented local-defect assessment', 'pass_for_unrestricted_operation': True}`
- `clause_18_1_2_monitoring_and_strengthening`: `{'category': 'serviceable', 'errors': [], 'pass': True}`
- `clause_18_1_3_verification_calculation_exemption`: `{'verification_calculation_may_be_omitted': False, 'calculation_required_reasons': ['defects_or_damage_present']}`
- `clause_18_2_1_material_evidence`: `{'testing_required': False, 'pass': True}`
- `clause_18_2_2_test_program`: `{'impact_toughness_required': True, 'missing_evidence': [], 'pass': True}`
- `clause_18_2_3_pre1950_route`: `{'specialized_institute_required': False, 'pass': True}`
- `clause_18_2_4_existing_steel_resistances`: `{'route': 'after_1988_statistical_certificate', 'gamma_m': 1.05, 'design_yield_resistance_n_mm2': 338.0952380952381, 'design_ultimate_resistance_n_mm2': 485.71428571428567}`
- `clause_18_2_5_existing_weld_defaults`: `{'fillet_weld_metal_resistance_n_mm2': 224.4, 'fillet_fusion_boundary_resistance_n_mm2': 224.4, 'beta_f': 0.7, 'beta_z': 1.0, 'working_condition_factor': 0.8, 'tension_butt_weld_resistance_n_mm2': 287.38095238095235}`
- `clause_18_2_6_unknown_bolt_defaults`: `{'bolt_shear_design_resistance_n_mm2': 150.0, 'bolt_tension_design_resistance_n_mm2': 160.0}`
- `table_48_rivet_resistance_n_mm2`: 180
- `clause_18_2_7_rivet_capacity`: `{'rivet_area_mm2': 314.0, 'capacity_n': 113040.0}`
- `clauses_18_3_1_to_18_3_4_route`: `{'decision': 'retain_without_strengthening', 'errors': [], 'pass': True}`
- `clauses_18_3_5_to_18_3_10_execution`: `{'combined_connection_type': 'rivets_plus_friction', 'errors': [], 'pass': True}`
- `clause_18_3_9_weld_heating_stress_limit_n_mm2`: 270.476190476
- `clause_18_3_11_resistance_route`: `{'relative_difference': 0.1, 'use_one_common_resistance': True, 'common_resistance_n_mm2': 300.0, 'route': 'common_lower_resistance'}`
- `equation_216_gamma_n`: 0.874242424242
- `equation_216_utilization`: 0.641889723346
- `equation_217_gamma_m`: 1
- `equation_217_result`: `{'signed_stress_n_mm2': 266.66666666666663, 'utilization': 0.8978675645342311}`
- `clause_18_3_14_alpha_n`: 1.25
- `equation_221_post_strengthening_initial_deflection`: 9.99843769529
- `equation_222_weld_shortening_parameter_v`: 0.0256
- `equation_222_welding_residual_deflection`: 64
- `equation_220_k_fw`: 1
- `equation_220_equivalent_eccentricity`: 78.9984376953
- `equation_219_relative_eccentricity`: 0.789984376953
- `equation_224_composite_factor_k`: 1.06777777778
- `equation_223_effective_design_resistance_n_mm2`: 310
- `equation_218_stability_utilization`: 0.746714456392
- `clause_18_3_16_existing_deviation_acceptance`: `{'accepted_without_strengthening': True, 'central_compression_section_type_substitution': 'b_instead_of_c', 'pass': True}`

## Scope limitation

Section 18 equations (216)-(224), Table 48 and executable assessment/strengthening routes are implemented. Survey conclusions, laboratory tests, material identification, load combinations, actual-geometry global analysis, Figure 24 n_i values, construction-stage analysis and professional decisions remain explicit external evidence boundaries.
