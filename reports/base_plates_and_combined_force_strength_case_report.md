# Base plates and combined-force strength case

- Case ID: `BPCS-EXAMPLE-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `equation_102_cantilever_moment_n_mm_per_mm`: 3840
- `table_e2_four_side_alpha_1`: 0.081
- `table_e2_four_side_alpha_2`: 0.05
- `equation_103_short_direction_moment_n_mm_per_mm`: 2187
- `equation_103_long_direction_moment_n_mm_per_mm`: 1350
- `table_e2_three_side_alpha_3`: 0.112
- `equation_104_three_side_moment_n_mm_per_mm`: 1935.36
- `maximum_unit_width_moment_n_mm_per_mm`: 3840
- `equation_101_required_base_plate_thickness_mm`: 9.6
- `annex_e1_c_x`: 1.095
- `annex_e1_c_y`: 1.47
- `annex_e1_n`: 1.5
- `equation_105_applicability`: `{'permitted': True, 'axial_stress_n_mm2': 50.0, 'low_axial_stress_branch': False, 'reasons': []}`
- `equation_105_utilization`: 0.289983209269
- `equation_105_pass`: `True`
- `equation_106_point_utilization`: 0.212
- `equation_106_pass`: `True`
- `clause_9_1_2_omission_rule`: `{'may_omit_equation_105': False, 'reason': 'equation_105_required'}`
- `equation_107_applicability`: `{'permitted': True, 'reasons': []}`
- `equation_108_delta`: 0.978873239437
- `equation_107_tension_fiber_utilization`: 0.0397348406989
- `equation_107_pass`: `True`

## Scope limitation

Clause 8.6 and Section 9.1 scalar procedures are implemented. Foundation resistance, geometry classification, global analysis, stability, and complete connection design remain external.
