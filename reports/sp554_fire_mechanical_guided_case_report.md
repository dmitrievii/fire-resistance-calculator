# FIRE-D2 SP554 member critical-temperature calculation

- Case ID: `FIRE-D2-COMP-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `status`: `COMPLETE`
- `member_route`: `central_compression`
- `requested_steel_strength_group`: `ordinary`
- `effective_steel_strength_group`: `ordinary`
- `qualification_notes`: `[]`
- `gamma_T_candidates`: `[{'formula_ref': '9.2', 'gamma_T_required': 0.5208333333333334, 'details': {'phi': 0.8, 'rule': 'SP554_9_2_SP16_PHI_WITH_HIGH_SLENDERNESS_CAP', 'phi_sp16_formula8': 0.8, 'phi_cap': None}}]`
- `gamma_T_required`: 0.520833333333
- `gamma_T_governing_formula_ref`: `9.2`
- `gamma_E_required`: 0.699976858678
- `critical_temperature_c`: 525.019284435
- `critical_temperature_controlling_kind`: `gamma_E`
- `strength_curve_inversion`: `{'status': 'EXACT_WITHIN_PUBLISHED_CURVE', 'temperature_c': 560.6481481481482, 'temperature_relation': '=', 'published_minimum_gamma': 0.2, 'published_maximum_temperature_c': 700.0}`
- `modulus_curve_inversion`: `{'status': 'EXACT_WITHIN_PUBLISHED_CURVE', 'temperature_c': 525.0192844353662, 'temperature_relation': '=', 'published_minimum_gamma': 0.43, 'published_maximum_temperature_c': 700.0}`
- `route_trace`: `{'route': 'central_compression', 'phi': 0.8, 'l_eff_mm': 3000.0}`
- `governing_policy`: `MIN_CRITICAL_TEMPERATURE_AFTER_INDEPENDENT_CURVE_INVERSION`
- `draft_literal_min_coefficient_policy_executed`: `False`
- `gamma_T_table_at_critical_temperature`: 0.57497300179
- `gamma_E_table_at_critical_temperature`: 0.699976858678
- `R_yt_critical_n_mm2`: 137.99352043
- `E_t_critical_n_mm2`: 144195.232888

## Scope limitation

FIRE-D2 executes SP554 Sections 8-11 member fire mechanics and Appendix-B critical-temperature inversion. It uses normative-strength FIRE-D1 handoffs and does not solve SP554 Section 12 heat transfer or connection fire resistance.
