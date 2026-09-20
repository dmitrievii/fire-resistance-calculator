# Stage N4 guided bending-member case

- Case ID: `N4-GUIDED-BEAM-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `strength`: `{'class_route': {'permitted': True, 'required_route': 'elastic', 'reason': 'class_1'}, 'member_class': 1, 'route': '8.2.1_EQ41_X', 'strength_utilization': 1.05850908994681, 'strength_pass': False, 'shear_route': '8.2.1_EQ42', 'shear_utilization': 0.44146454117079015, 'shear_pass': True}`
- `lateral_stability`: `{'mode': 'calculate_phi_b', 'effective_length_mm': 3000.0, 'alpha_eq_zh4': 30.593890679353393, 'psi': 4.391572347554738, 'phi_1': 2.4955337676595235, 'phi_b': 1.0, 'utilization_eq69': 1.05850908994681, 'pass': False}`
- `local_stability`: `{'mode': 'geometry_and_stiffener_screen', 'web_relative_slenderness': 0.4419770235208934, 'preliminary_8_5_1': {'limit': 3.5, 'detailed_check_may_be_omitted': True}, 'transverse_stiffener_requirements_8_5_9': {'required': False, 'threshold': 3.2, 'maximum_spacing_mm': 270.0, 'spacing_factor': 2.5}, 'status': 'SCREEN_ONLY_FULL_8_5_INTERACTION_REMAINS_SEPARATE', 'pass': None}`
- `governing_utilization`: 1.05850908995
- `pass`: `False`
- `trace_policy`: `FIRST_APPLICABLE_BRANCH_ONLY`

## Scope limitation

Stage N4 applicability-safe guided bending workflow. It evaluates only the selected ordinary-beam strength branch, an explicit lateral-stability route and an explicit local-stability route. Crane-runway/bimetal and full deep 8.5 interaction checks retain their dedicated detailed actions. Imported profile rows remain pending final original-GOST audit.
