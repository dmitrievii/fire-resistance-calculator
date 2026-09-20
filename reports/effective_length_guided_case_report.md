# Stage N7 guided effective-length and limiting-slenderness case

- Case ID: `N7-EFFECTIVE-LENGTH-GUIDED-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `status`: `COMPLETE`
- `effective_length`: `{'status': 'RESOLVED', 'route': 'eq138_built_up_branch_in_plane', 'effective_length_mm': 600.0, 'equation': '138'}`
- `radius`: `{'selector': 'explicit', 'radius_mm': 20.0}`
- `actual_slenderness`: 30
- `limiting_slenderness`: `{'status': 'RESOLVED', 'table': '32', 'alpha': 0.5, 'limit': 150.0, 'group4_factor_applied': False, 'check': {'actual_slenderness': 30.0, 'limiting_slenderness': 150.0, 'utilization': 0.2, 'pass': True, 'unlimited': False}}`
- `required_unresolved`: `[]`
- `pass`: `True`

## Scope limitation

Stage N7 implements applicability-selected current-SP16 Section 10 routes. Annex И, specified crossing-brace external rules, and certified-program global analysis remain explicit provenance-gated boundaries rather than inferred formulas.
