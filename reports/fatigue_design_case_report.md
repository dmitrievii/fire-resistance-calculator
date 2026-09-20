# Fatigue-design case

- Case ID: `SP16-V14-FATIGUE-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `fatigue_applicability_route`: `{'route': 'section_12_ordinary_fatigue', 'ordinary_fatigue_required': True, 'low_cycle_method_external': False, 'clause_12_1_3_current_status': 'EXCLUDED_FROM_2025_01_10_CHANGE_6', 'resonant_vortex_fatigue_assessment_required': False, 'stress_concentration_minimizing_detailing_required': True, 'cycle_count_source': 'technological operating requirements', 'load_source': 'SP 20.13330 external input'}`
- `annex_k_case_id`: `K1-16-TRANSVERSE_WELD_SMOOTH`
- `annex_k_element_group`: `4`
- `table_35_fatigue_resistance_n_mm2`: 75
- `cycle_factor_alpha`: 1.63
- `stress_asymmetry_ratio_rho`: -0.4
- `table_36_asymmetry_factor_gamma_v`: 1.31578947368
- `equation_170_utilization`: 0.310838445808
- `equation_170_pass`: `True`
- `fatigue_resistance_cap_check`: `{'fatigue_denominator_n_mm2': 160.85526315789477, 'ultimate_limit_n_mm2': 307.6923076923077, 'cap_utilization': 0.522779605263158, 'pass': True}`
- `clause_12_2_crane_cycle_factor_alpha`: 0.77
- `clause_12_2_crane_web_fatigue_resistance_n_mm2`: 75
- `equation_173_utilization`: 0.365074840238
- `equation_173_pass`: `True`

## Scope limitation

Section 12 equations (170)-(173), Tables 35-36, and Annex K Table K.1 are implemented. Load derivation under SP 20.13330, stress-history extraction, low-cycle fatigue, cumulative damage for variable-amplitude spectra, and automatic detail recognition remain external boundaries.
