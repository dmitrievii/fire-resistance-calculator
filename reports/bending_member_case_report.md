# Bending-member strength case

- Case ID: `BENDING-DEMO-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `clause_8_1_class_route`: `{'permitted': True, 'required_route': 'limited_plastic', 'reason': 'class_2'}`
- `equation_41_elastic_bending_utilization`: 0.281690140845
- `equation_42_elastic_shear_utilization`: 0.0607090820787
- `equation_42_with_bolt_hole_factor`: 0.0758863525983
- `equation_43_combined_normal_utilization`: 0.591549295775
- `equation_44_web_checks`: `{'equivalent_utilization': 0.34760930756841485, 'shear_utilization': 0.30354541039339483, 'equivalent_pass': True, 'shear_pass': True, 'governing_utilization': 0.34760930756841485}`
- `equation_44_web_checks_unadjusted_diagnostic`: `{'equivalent_utilization': 0.3090220446546222, 'shear_utilization': 0.24283632831471588, 'equivalent_pass': True, 'shear_pass': True, 'governing_utilization': 0.3090220446546222}`
- `equation_44_adjusted_shear_stress_n_mm2`: 62.5
- `equation_44_shear_with_bolt_hole_factor`: 0.303545410393
- `equation_45_bolt_hole_factor`: 1.25
- `equation_48_or_49_effective_load_length_mm`: 140
- `equation_47_local_web_stress_n_mm2`: 71.4285714286
- `equation_46_local_web_utilization`: 0.201207243461
- `annex_e1_design_coefficients`: `{'c_x': 1.07, 'c_y': 1.47, 'n': 1.5, 'uncapped_c_x': 1.07, 'uncapped_c_y': 1.47}`
- `clause_8_2_3_applicability`: `{'permitted': True, 'failed_gates': []}`
- `equation_52_beta`: 1
- `equation_50_plastic_bending_utilization`: 0.263261813874
- `equation_51_plastic_biaxial_utilization`: 0.339912192335
- `table_10a_ratio`: 0.263261813874
- `table_10a_c_omega`: 1.977217191
- `equation_53_constrained_torsion_utilization`: 0.405729794695
- `pure_bending_modified_coefficients`: `{'c_xm': 1.0350000000000001, 'c_ym': 1.2349999999999999}`
- `equation_54_support_shear_x_utilization`: 0.485672656629
- `equation_55_support_shear_y_utilization`: 0.0971345313259
- `continuous_beam_applicability`: `{'permitted': True, 'relative_span_difference': 0.09090909090909091, 'failed_gates': []}`
- `equation_57_effective_moment_hinged_n_mm`: 120000000
- `equation_58_effective_moment_intermediate_n_mm`: 80000000
- `fixed_end_effective_moment_n_mm`: 70000000
- `equation_56_redistributed_design_moment_n_mm`: 150000000
- `clause_8_2_6_biaxial_route`: `{'permitted': True, 'required_formula': 'equation_51'}`
- `clause_8_2_7_class_3_route`: `{'permitted': True, 'missing_confirmations': [], 'required_formula': 'equation_50'}`
- `bimetal_applicability`: `{'permitted': True, 'failed_gates': []}`
- `bimetal_yield_resistance_ratio_r`: 1.18333333333
- `equation_61_c_xr`: 1.17724518984
- `equation_62_beta_r`: 0.984777506346
- `bimetal_c_yr`: 1.15
- `equation_59_bimetal_bending_utilization`: 0.287523734414
- `equation_60_bimetal_biaxial_utilization`: 0.385502913839

## Scope limitation

Clauses 8.1-8.2 only. Global stability, local plate stability, force recovery, section classification, and referenced clauses 8.4-8.5 remain separate explicit checks.
