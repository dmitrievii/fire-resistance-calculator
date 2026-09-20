# Stage N8 guided sheet-structure case

- Case ID: `EX-STAGE-N8-CYL-AXIAL-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `status`: `COMPLETE`
- `route`: `cylinder_axial_11_2_1`
- `critical`: `{'radius_to_thickness_ratio': 100.0, 'c_coefficient': 0.22, 'psi': 0.7835922330097087, 'yield_branch_n_mm2': 274.25728155339806, 'elastic_branch_n_mm2': 453.2, 'critical_stress_n_mm2': 274.25728155339806, 'governing_branch': 'psi_Ry', 'table34_source': 'exact_printed_node'}`
- `eccentric_adjustment`: `None`
- `adjusted_critical_stress_n_mm2`: 274.257281553
- `equation_154_utilization`: 0.29169690426
- `pass`: `True`
- `analysis_gate`: `{'local_edge_effect_analysis_required': False, 'certified_spatial_software_required': False, 'base_membrane_equations_still_required': True, 'unresolved_requirements': [], 'complete': True}`
- `governing_utilization`: 0.29169690426

## Scope limitation

Stage N8 applicability-safe current-SP16 Section 11 workflow. Exactly one shell/panel route is evaluated. Table 34 is exact-node only unless an explicitly sourced external c coefficient is supplied. Local edge effects, arbitrary spatial shell analysis and unavailable global/member checks remain explicit fail-closed dependencies.
