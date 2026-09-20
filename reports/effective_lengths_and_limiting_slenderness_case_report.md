# Effective lengths and limiting slenderness case

- Case ID: `SP16-V12-DEMO-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `equation_136_truss_in_plane_effective_length_mm`: 2553.75
- `equation_137_truss_out_of_plane_effective_length_mm`: 4687.5
- `equation_138_branch_in_plane_effective_length_mm`: 2094.50710192
- `equation_139_branch_out_of_plane_effective_length_mm`: 3158.46096908
- `table_24_effective_length_mm`: 2400
- `table_25_effective_length_mm`: 2100
- `table_26_effective_length_mm`: 2700
- `table_28_n_parameter`: 2
- `table_28_conditional_length_mm`: 3625
- `table_29_base_mu_d`: 0.9
- `table_29_adjusted_mu_d`: 0.95
- `table_30_mu`: 0.7
- `equation_140_column_effective_length_mm`: 4200
- `equation_141_mu`: 3.7594325813
- `equation_142_mu`: 1.56469673166
- `equation_143_mu`: 1.82903290106
- `equation_144_mu`: `None`
- `equation_145_mu`: 0.845620203999
- `equation_146_mu_effective`: 1.9245008973
- `equation_147_bundle`: `{'beta_hat': 0.08333333333333337, 'alpha_hat': 0.5767361111111111, 'relative_eccentricity_m': 1.8, 'omega': 1.1952286093343936, 'psi': 0.46416076014697216}`
- `actual_column_slenderness`: 105
- `table_32_alpha`: 0.5
- `table_32_limiting_slenderness`: 150
- `table_32_check`: `{'actual_slenderness': 105.0, 'limiting_slenderness': 150.0, 'utilization': 0.7, 'pass': True, 'unlimited': False}`
- `table_33_limiting_slenderness`: 400

## Scope limitation

Section 10 scalar formulas, table routing, and limiting-slenderness checks are implemented. Diagram classification, global frame analysis, stepped-column Annex И calculation, elastic end-restraint formulas from the separate design rules, and certification of external software remain explicit boundaries.
