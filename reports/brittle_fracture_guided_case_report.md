# Stage N10 guided brittle-fracture case

- Case ID: `N10-BRITTLE-FRACTURE-GUIDED-EXAMPLE`
- Release: `v0.57_fire_ui24_fire_val1_routing_remediation_r1`

## Results

- `status`: `COMPLETE`
- `route`: `section13_full_review`
- `general_prevention`: `{'clause_13_1_factor_register': {'low_temperature': 'Reduced temperature with steel chemistry, structure and rolled-product thickness effects.', 'dynamic_or_impact_action': 'Moving, dynamic and vibratory actions.', 'high_local_stress': 'High local stresses from concentrated action, connection deformation, welding and residual stresses.', 'stress_concentration': 'Stress concentrators oriented transverse to the direction of tensile stress.'}, 'clause_13_2_checks': {'steel_selection_5_2_table_v1': {'applicable': True, 'confirmed': True}, 'stress_concentration_and_work_hardening_reduction': {'applicable': True, 'confirmed': True}, 'solid_web_vs_lattice_concentration_considered': {'applicable': True, 'confirmed': True}, 'enhanced_ndt_above_0_4_ry': {'applicable': True, 'stress_n_mm2': 110.0, 'threshold_n_mm2': 96.0, 'confirmed': True}, 'weld_intersections_avoided': {'applicable': True, 'confirmed': True}, 'runoff_tabs_and_weld_ndt': {'applicable': True, 'confirmed': True}, 'flank_weld_termination_25_mm_each_side': {'applicable': True, 'provided_mm': 25.0, 'minimum_mm': 25.0, 'confirmed': True}, 'minimum_section_thickness_for_guillotine_or_punching': {'applicable': False, 'confirmed': True}, 'secondary_gusset_bolted_to_tension_member': {'applicable': False, 'confirmed': True}}, 'failed_requirements': [], 'pass': True}`
- `lamellar_tearing`: `{'required': True, 'status': 'COMPLETE', 'clause_13_3_screen': {'risk_assessment_required': True, 'primary_25_mm_route': True, 'other_plate_over_40_mm_route': False, 'ultrasonic_quality_control_relevant': True}, 'clause_13_4_test_evidence': {'test_result_available': True, 'status': 'evidence_available', 'required_evidence': 'Verified through-thickness tensile-test result and declared Z quality.'}, 'table_37_factors_percent': {'psi_zf': 8.0, 'psi_zt': 6.0, 'psi_zsh': 2.4, 'psi_zj': 5.0, 'psi_zs': 0.0}, 'equation_174_base_risk_percent': 21.4, 'adjusted_risk_percent': 21.4, 'required_z_quality_group': 'Z25', 'selected_z_quality_group': 'Z25', 'selected_quality_meets_minimum_group': True, 'risk_check': {'z_quality_group': 'Z25', 'threshold_percent': 25.0, 'risk_percent': 21.4, 'utilization': 0.856, 'pass': True}, 'governing_utilization': 1.0, 'pass': True}`
- `governing_utilization`: 1
- `pass`: `True`

## Scope limitation

Stage N10 applicability-safe current-SP16 Section 13 workflow. Clause 13.2 conditional detailing/NDT obligations, clause 13.3 engineering applicability, clause 13.4 evidence, equation (174), Table 37 and Z-quality routing are explicit. No drawing recognition, material-certificate inference, NDT interpretation, or unstated lamellar-tearing rule is invented.
