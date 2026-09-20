# Brittle-fracture and welded-connection case

- Case ID: `SP16-V15-BRITTLE-WELD-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `table_37_factors_percent`: `{'psi_zf': 0.0, 'psi_zt': 6.0, 'psi_zsh': 2.4, 'psi_zj': 3.0, 'psi_zs': -12.0}`
- `equation_174_base_risk_percent`: -0.6
- `adjusted_lamellar_tearing_risk_percent`: -0.6
- `required_z_quality_group`: `Z35`
- `selected_z_quality_check`: `{'z_quality_group': 'Z35', 'threshold_percent': 35.0, 'risk_percent': -0.6000000000000001, 'utilization': -0.017142857142857144, 'pass': True}`
- `table_38_minimum_fillet_weld`: `{'route': 'table_38', 'thickness_bin': '17_22', 'minimum_weld_leg_mm': 10.0}`
- `table_39_coefficients`: `{'weld_leg_bin': '9_12', 'beta_f': 0.8, 'beta_z': 1.0}`
- `butt_weld_effective_length_mm`: 230
- `equation_175_utilization`: 0.395256916996
- `equation_175_pass`: `True`
- `butt_weld_combined_stress_check`: `{'equivalent_utilization': 0.35315220128540514, 'shear_utilization': 0.19230769230769232, 'equivalent_pass': True, 'shear_pass': True, 'governing_utilization': 0.35315220128540514}`
- `fillet_weld_effective_length_mm`: 220
- `equation_176_utilization`: 0.340909090909
- `equation_177_utilization`: 0.340909090909
- `equation_178_utilization`: 0.333333333333
- `equation_179_utilization`: 0.333333333333
- `equation_180_utilization`: 0.310564996875
- `equation_181_utilization`: 0.303813583899
- `equation_183_resultant_shear_n_mm2`: 43.0116263352
- `equation_182_combined_check`: `{'weld_metal_utilization': 0.2150581316760657, 'fusion_boundary_utilization': 0.2688226645950821, 'governing_utilization': 0.2688226645950821, 'weld_metal_pass': True, 'fusion_boundary_pass': True, 'pass': True}`
- `spot_weld_equations_184_185`: `{'beta': 1.5, 'shear_capacity_n': 11200.000000000002, 'tearout_capacity_n': 12000.0, 'governing_capacity_n': 11200.000000000002, 'governing_mode': 'shear'}`

## Scope limitation

Sections 13 and 14.1 are implemented for the audited risk-factor, detailing-route, butt-weld, fillet-weld, and arc spot-weld checks. Steel selection, fracture-mechanics assessment, NDT evidence, automatic detail recognition, weld procedure qualification, and global load derivation remain external boundaries.
