# Stage N9 guided fatigue case

- Case ID: `N9-FATIGUE-GUIDED-EXAMPLE`
- Release: `v0.57_fire_ui24_fire_val1_routing_remediation_r1`

## Results

- `status`: `COMPLETE`
- `route`: `ordinary_fatigue_12_1_2`
- `applicability`: `{'route': 'section_12_ordinary_fatigue', 'ordinary_fatigue_required': True, 'low_cycle_method_external': False, 'clause_12_1_3_current_status': 'EXCLUDED_FROM_2025_01_10_CHANGE_6', 'resonant_vortex_fatigue_assessment_required': False, 'stress_concentration_minimizing_detailing_required': True, 'cycle_count_source': 'technological operating requirements', 'load_source': 'SP 20.13330 external input'}`
- `general_fatigue_check`: `{'annex_k_case_id': 'K1-16-TRANSVERSE_WELD_SMOOTH', 'annex_k_element_group': 4, 'table_35_fatigue_resistance_n_mm2': 75.0, 'cycle_factor_alpha': 1.6300000000000001, 'cycle_factor_source': '12.1.2 equations (171)/(172) or alpha=0.77 at n>=3.9e6', 'stress_asymmetry_ratio_rho': -0.5, 'table_36_asymmetry_factor_gamma_v': 1.25, 'equation_170_utilization': 0.3271983640081799, 'equation_170_pass': True, 'fatigue_resistance_cap_check': {'fatigue_denominator_n_mm2': 152.81250000000003, 'ultimate_limit_n_mm2': 307.6923076923077, 'cap_utilization': 0.4966406250000001, 'pass': True}, 'pass': True, 'governing_utilization': 0.4966406250000001}`
- `governing_utilization`: 0.496640625
- `pass`: `True`

## Scope limitation

Stage N9 applicability-safe current-SP16 Section 12 workflow. Exactly one ordinary-fatigue, crane-runway, or low-cycle boundary route is evaluated. Change No. 6 exclusion of clause 12.1.3 is explicit; no replacement low-cycle formula, SP20 load derivation, stress-history extraction, cumulative-damage rule, or automatic Annex-K detail recognition is invented.
