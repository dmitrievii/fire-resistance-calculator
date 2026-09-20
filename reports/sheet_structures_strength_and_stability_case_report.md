# Sheet-structure strength and stability case

- Case ID: `SP16-V13-SHEET-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `equation_148_utilization`: 0.264248775201
- `equation_148_pass`: `True`
- `principal_stress_check`: `{'principal_max_n_mm2': 106.05551275463989, 'principal_min_n_mm2': 33.94448724536011, 'tension_utilization': 0.29874792325250676, 'compression_utilization': 0.0, 'pass': True}`
- `equation_149_meridional_stress_n_mm2`: 3.33333333333
- `equation_150_circumferential_stress_n_mm2`: 296.666666667
- `equation_151_cylinder_stresses_n_mm2`: `[150.0, 300.0]`
- `equation_152_sphere_stresses_n_mm2`: `[150.0, 150.0]`
- `equation_153_cone_stresses_n_mm2`: `[173.20508075688772, 346.41016151377545]`
- `table_34_axial_critical_bundle`: `{'radius_to_thickness_ratio': 300.0, 'c_coefficient': 0.16, 'psi': 0.4038592233009708, 'yield_branch_n_mm2': 143.37002427184464, 'elastic_branch_n_mm2': 109.86666666666666, 'critical_stress_n_mm2': 109.86666666666666, 'governing_branch': 'c_E_t_over_r'}`
- `equation_154_utilization`: 0.546116504854
- `equation_154_pass`: `True`
- `eccentric_compression_adjustment`: `{'shear_threshold_n_mm2': 2.7751302939048017, 'applicable': True, 'multiplier': 1.1333333333333335}`
- `tube_route`: `{'radius_to_thickness_ratio': 50.0, 'lower_threshold': 37.83897039721633, 'upper_threshold': 75.67794079443266, 'route': 'equation_156_local_stability_no_separate_global_check'}`
- `tube_critical_bundle`: `{'critical_stress_n_mm2': 100.0, 'source': 'explicit audited input because Table 34 has no printed node at the selected r/t'}`
- `equation_156_utilization`: 0.578428357182
- `equation_156_pass`: `True`
- `panel_limit_bundle`: `{'limit_b_over_t': 39.14458742051922, 'route': 'linear_interpolation_0.8Ry_to_Ry'}`
- `panel_route`: `{'b_squared_over_r_t': 3.0, 'route': 'panel_equations_157_158'}`
- `external_pressure_critical_bundle`: `{'length_to_radius_ratio': 15.0, 'critical_stress_n_mm2': 7.416000000000001, 'route': 'linear_interpolation_10_to_20'}`
- `equation_159_utilization`: 0.134843581446
- `equation_159_pass`: `True`
- `ring_stiffener_requirements`: `{'ring_compression_force_n': 5000.0, 'ring_effective_length_mm': 1800.0, 'effective_shell_width_each_side_mm': 15657.873868584682, 'maximum_relative_slenderness': 6.5, 'use_spacing_in_equations_159_to_161': True}`
- `equation_162_combined_cylinder_utilization`: 0.6809600863
- `equation_162_pass`: `True`
- `equation_165_equivalent_cone_radius_mm`: 1000
- `cone_axial_critical_bundle`: `{'radius_to_thickness_ratio': 100.0, 'c_coefficient': 0.22, 'psi': 0.7812864077669903, 'yield_branch_n_mm2': 277.35667475728155, 'elastic_branch_n_mm2': 453.2, 'critical_stress_n_mm2': 277.35667475728155, 'governing_branch': 'psi_Ry'}`
- `equation_164_cone_critical_force_n`: 13063499.3811
- `equation_163_utilization`: 0.00765491673272
- `equation_163_pass`: `True`
- `equation_167_cone_critical_hoop_stress_n_mm2`: 56.65
- `equation_166_utilization`: 0.017652250662
- `equation_166_pass`: `True`
- `equation_168_combined_cone_utilization`: 0.0253071673947
- `equation_168_pass`: `True`
- `sphere_critical_stress_n_mm2`: 41.2
- `equation_169_utilization`: 0.0606796116505
- `equation_169_pass`: `True`
- `clauses_11_1_4_11_1_5_route`: `{'local_edge_effect_analysis_required': True, 'certified_spatial_software_required': True, 'base_membrane_equations_still_required': True}`

## Scope limitation

Section 11 scalar membrane-strength and shell-stability formulas are implemented. Local edge effects, arbitrary shell finite-element analysis, automatic geometry classification, global member stability, and complete ring-stiffener section design remain explicit external boundaries.
