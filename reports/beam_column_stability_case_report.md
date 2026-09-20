# Beam-column stability case

- Case ID: `BC-STAB-EXAMPLE-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `section_9_2_route`: `{'route': 'equations_116_to_119', 'section_9_2_stability_required': True}`
- `annex_d2_eta_x`: 1
- `annex_d2_eta_y`: 1
- `equation_110_m_eff_x`: 2
- `equation_110_m_eff_y`: 1
- `annex_d3_phi_ex`: 0.397
- `annex_d3_phi_ey`: 0.593
- `equation_109_utilization`: 0.604534005038
- `equation_109_pass`: `True`
- `table_21_alpha`: 0.75
- `table_21_beta`: 1
- `equations_112_to_114_c`: `{'branch': 'equation_112', 'c_raw': 0.4, 'c_max': 0.9, 'c': 0.4}`
- `equation_111_utilization`: 0.75
- `equation_111_pass`: `True`
- `equation_115_utilization`: 0.342857142857
- `equation_115_pass`: `True`
- `equation_117_phi_exy`: 0.450793898307
- `equation_116_utilization`: 0.53239407388
- `equation_116_pass`: `True`
- `equation_118_m_x_from_geometry`: 2
- `equation_119_m_y_from_geometry`: 1
- `table_20_design_moment_n_mm`: 8000000
- `table_d5_effective_eccentricity`: 0.39
- `clause_9_2_9_additional_checks`: `{'equation_116_required': True, 'section_8_y_route_required': False, 'equation_109_with_ey_zero_required': True, 'equation_111_with_ey_zero_required': True, 'eccentricity_trigger': True, 'slenderness_trigger': True}`
- `clause_9_2_9_adjusted_m_x`: 2
- `equation_122_delta_x`: 0.904
- `equation_122_delta_y`: 0.946
- `equation_120_utilization`: 0.684984527966
- `equation_120_pass`: `True`
- `equation_121_utilization`: 0.47519391729
- `equation_121_pass`: `True`
- `annex_d_equation_d2_parameters`: `{'rho': 0.037037037037037035, 'omega': 0.2222222222222222, 'mu': 1.7922222222222222, 'delta': 0.08266170696424881, 'B': 1.0, 'alpha': 0.0, 'eccentricity_ratio': 1.111111111111111}`
- `annex_d_equation_d1_c_max`: 0.441799289769
- `annex_d_equation_d4_c_max`: 1.25636558266
- `annex_d6_section_parameters`: `{'omega_star': '0.25', 'alpha_star': '0', 'beta_star': '0'}`

## Scope limitation

Section 9.2 scalar stability checks and exact Annex D table-node lookups are implemented. Global analysis, automatic section/diagram classification, interpolation not stated by the standard, and linked local-stability checks remain explicit external boundaries.
