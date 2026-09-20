# Bending-member local-stability case

- Case ID: `BLS-EXAMPLE-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `equation_78_normal_stress_n_mm2`: 100
- `equation_79_average_shear_stress_n_mm2`: 20.8333333333
- `web_relative_slenderness`: 3.32101282948
- `plate_relative_slenderness`: 3.32101282948
- `panel_aspect_ratio_mu`: 1
- `equation_84_delta`: 2
- `table_12_c_cr`: 33.3
- `table_14_c1`: 15.4
- `table_15_c2`: 1.88
- `equation_81_sigma_cr_n_mm2`: 1071.84375
- `equation_82_sigma_local_cr_n_mm2`: 931.8925
- `equation_83_tau_cr_n_mm2`: 336.947816901
- `equation_80_web_utilization`: 0.14959592902
- `equation_80_pass`: `True`
- `preliminary_clause_8_5_1`: `{'limit': 2.5, 'detailed_check_may_be_omitted': False}`
- `transverse_stiffener_requirement`: `{'required': True, 'threshold': 3.2, 'maximum_spacing_mm': 1920.0, 'spacing_factor': 2.0}`
- `actual_flange_relative_slenderness`: 0.242157185483
- `flange_limit_equation`: `97`
- `limiting_flange_relative_slenderness`: 0.635144936931
- `flange_local_stability_pass`: `True`

## Scope limitation

Clauses 8.5.1-8.5.20 are implemented as scalar equations, exact table lookups, and explicit routing procedures. Geometry extraction, global analysis, and external flexible-web rules remain outside this action.
