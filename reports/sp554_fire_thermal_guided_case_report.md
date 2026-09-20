# FIRE-D3 SP554 Section 12 thermal fire-resistance calculation

- Case ID: `FIRE-D3-UNPROTECTED-CONTROL-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `status`: `COMPLETE`
- `actual_fire_resistance_min`: 14.3263941732
- `calculated_time_min`: 14.3263941732
- `steel_temperature_c`: 525.019284435
- `fire_temperature_c`: 731.7349082
- `step_count`: `144`
- `crossing_bracket`: `[14.299999999999965, 14.399999999999965]`
- `thermal_trace`: `[{'time_min': 0.1, 'fire_temperature_c': 108.0690142606406, 'steel_temperature_c': 20.47178132055009, 'alpha_w_m2k': 34.06553179428328, 'steel_cp_j_kgk': 486.048}, {'time_min': 0.2, 'fire_temperature_c': 163.1658050499322, 'steel_temperature_c': 21.269428641904337, 'alpha_w_m2k': 35.55741253788607, 'steel_cp_j_kgk': 486.1906666713343}, {'time_min': 0.30000000000000004, 'fire_temperature_c': 203.36022637957802, 'steel_temperature_c': 22.323954868560207, 'alpha_w_m2k': 36.85613746695954, 'steel_cp_j_kgk': 486.4318752213119}, {'time_min': 0.4, 'fire_temperature_c': 235.02100518727565, 'steel_temperature_c': 23.593777612755847, 'alpha_w_m2k': 38.01952464530942, 'steel_cp_j_kgk': 486.75076395225267}, {'time_min': 0.5, 'fire_temperature_c': 261.1446514959265, 'steel_temperature_c': 25.05047635590175, 'alpha_w_m2k': 39.08234716391075, 'steel_cp_j_kgk': 487.1347583500974}, {'time_min': 9.99999999999998, 'fire_temperature_c': 678.4273315131338, 'steel_temperature_c': 371.93784946700634, 'alpha_w_m2k': 97.11346149488374, 'steel_cp_j_kgk': 591.2957488926321}]`
- `reduced_emissivity`: 0.562913907285
- `material_parameters`: `{'source': 'sp554_12_2_defaults', 'rho': 7850.0, 'c0': 480.0, 'kc': 0.00063, 'eps_fire': 0.85, 'eps_steel': 0.625}`
- `thermal_route`: `UNPROTECTED_STEP_12_2`
- `critical_temperature_c`: 525.019284435
- `reduced_thickness_mm`: 10
- `reduced_thickness_trace`: `{'producer': 'explicit_reduced_thickness', 'equation_ref': '12.2'}`
- `result_definition`: `SP554_13.2_time_from_heat_exposure_start_to_critical_steel_temperature`
- `fire_regime`: `standard`
- `fire_d2_handoff_preserved`: `True`
- `normative_route`: `SP554_12.1_12.2_formulas_12.1_to_12.4`

## Scope limitation

FIRE-D3 executes SP554 Section 12 thermal time-to-critical-temperature routes over the frozen FIRE-D2 critical-temperature handoff. Unprotected 12.2 and documented protected-matrix 12.10 routes are executable. The 12.5 FDM route is executable for dry W=0 protection only and is subject to the mandatory 12.6 validation gate; W>0 remains fail-closed because the source does not define an unambiguous phase-change activation algorithm.
