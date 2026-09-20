# Crane-runway and bending-stability case

- Case ID: `CRANE-STABILITY-DEMO-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `crane_beta_factor`: 0.87
- `equation_68_local_torsional_moment_n_mm`: 3765000
- `equation_67_stress_components`: `{'sigma_x_n_mm2': 50.0, 'sigma_local_x_n_mm2': 16.5, 'sigma_local_y_n_mm2': 66.0, 'sigma_f_y_n_mm2': 0.6275, 'tau_xy_n_mm2': 25.0, 'tau_local_xy_n_mm2': 19.8, 'tau_f_xy_n_mm2': 0.156875}`
- `equation_63_equivalent_utilization`: 0.250048343717
- `equation_64_longitudinal_utilization`: 0.187323943662
- `equation_65_transverse_utilization`: 0.187683098592
- `equation_66_shear_utilization`: 0.21834324915
- `annex_zh_alpha`: 1
- `annex_zh_psi`: 2.14999063751
- `annex_zh_phi_bundle`: `{'phi_1': 0.12476002009210967, 'phi_b': 0.12476002009210967}`
- `equation_69_lateral_torsional_utilization`: 1.12892792353
- `equation_70_combined_stability_utilization`: 1.15737862776
- `actual_relative_flange_slenderness`: 0.691877672809
- `table_11_limiting_flange_slenderness`: 0.966113588905
- `class_2_3_plastic_region_applies`: `False`
- `effective_limiting_flange_slenderness_for_exemption`: 0.966113588905
- `clause_8_4_4_exemption`: `{'exempt': True, 'route': 'table_11', 'slenderness_ok': True, 'flange_width_ratio_ok': True}`
- `equation_74_equivalent_compressed_flange_force_n`: 976250
- `discrete_bracing_force_bundle`: `{'geometric_slenderness': 50.0, 'relative_slenderness': 2.075633018427021, 'phi': 0.8144714364126935, 'q_fictitious_n': 14995.44530228495}`
- `equation_75_continuous_bracing_force_n_per_mm`: 7.49772265114
- `equation_77_c1x`: 1.2
- `equation_76_delta`: 0.76
- `class_2_3_plastic_region_limit`: 0.734246327568

## Scope limitation

Clauses 8.3-8.4 and Annex Ж are implemented. Tables 12-13 are transcribed as forward dependencies, but the clause 8.5 web-stability equations that consume them remain outside this runner.
