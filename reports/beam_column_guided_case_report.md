# Stage N5 guided beam-column case

- Case ID: `N5-GUIDED-BEAMCOL-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `status`: `COMPLETE`
- `derived`: `{'geometric_slenderness_x': 43.94598957811736, 'geometric_slenderness_y': 29.297326385411573, 'relative_slenderness_x': 1.5, 'relative_slenderness_y': 1.0, 'central_phi_x': 0.8934180916680713, 'central_phi_y': 0.9008651435292161, 'relative_eccentricity_x': 0.5958442597264094, 'relative_eccentricity_y': 0.0}`
- `d2_d3_x`: `{'status': 'D3_EXACT_NODE', 'eta': 1.6782909018191512, 'm_eff': 1.0000000000000002, 'phi_e': 0.593, 'source': 'table_D.3_exact_printed_node'}`
- `d2_d3_y`: `{'status': 'CENTRAL_COMPRESSION_LIMITING_CASE', 'eta': None, 'm_eff': 0.0, 'phi_e': 0.9008651435292161, 'source': 'clause_7.1.3_limit_M_equals_0'}`
- `coefficient_c`: `{'status': 'RESOLVED', 'alpha': 0.7, 'beta': 1.0, 'phi_at_3_14': 0.5370345356854724, 'branch': 'equation_112', 'c_raw': 0.7056709927853775, 'c_max': 1.0, 'c': 0.7056709927853775}`
- `stability_branch`: `{'route': '9.2.1_9.2.2_9.2.4_ONE_PLANE_MAJOR'}`
- `stability_checks`: `[{'equation': '109', 'utilization': 0.37204380687842925, 'pass': True}, {'equation': '111', 'utilization': 0.34704574477076217, 'pass': True}]`
- `strength`: `{'route': '9.1.1_EQ105', 'applicability_eq105': {'permitted': True, 'axial_stress_n_mm2': 50.30181086519115, 'low_axial_stress_branch': False, 'reasons': []}, 'annex_e1': {'c_x': 1.0473846153846154, 'c_y': 1.47, 'n': 1.5}, 'utilization': 0.2291361924897244, 'pass': True}`
- `required_unresolved`: `[]`
- `governing_utilization`: 0.372043806878
- `pass`: `True`
- `trace_policy`: `FIRST_APPLICABLE_BRANCH_WITH_EXPLICIT_D3_BILINEAR_INTERPOLATION_NO_EXTRAPOLATION`

## Scope limitation

Stage N5 applicability-safe solid beam-column workflow for current SP16 Section 9. N1 material and N2 section hydration are explicit; N3/N4 primitives are reused. Table D.3 is exact-node only unless an explicitly sourced external phi_e is supplied. Built-up and box routes retain their existing detailed actions.
