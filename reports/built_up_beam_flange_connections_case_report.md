# Built-up beam flange-connection case

- Case ID: `SP16-V17-DEMO-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `table_43_route`: `{'nominal_load_character': 'stationary', 'effective_load_character': 'moving', 'reason': 'stationary_upper_flange_load_without_transverse_stiffener_is_checked_as_moving'}`
- `table_43_alpha`: 0.4
- `flange_shear_flow_t_n_mm`: 360
- `local_pressure_v_n_mm`: 528
- `equation_193_utilization`: 0.1171875
- `equation_193_pass`: `True`
- `equation_194_utilization`: 0.104651162791
- `equation_194_pass`: `True`
- `equation_195_utilization`: 0.576
- `equation_195_pass`: `True`
- `equation_196_utilization`: 0.208023858683
- `equation_196_pass`: `True`
- `equation_197_utilization`: 0.185770143568
- `equation_197_pass`: `True`
- `equation_198_utilization`: 0.6678068032
- `equation_198_pass`: `True`
- `applicable_weld_equations`: `['196', '197']`
- `applicable_friction_equations`: `['198']`
- `governing_applicable_weld_utilization`: 0.208023858683
- `governing_applicable_weld_pass`: `True`
- `governing_applicable_friction_utilization`: 0.6678068032
- `governing_applicable_friction_pass`: `True`
- `full_penetration_weld_classification`: `{'full_penetration_through_web_thickness': False, 'equal_strength_with_web': False, 'evidence_required': 'weld_detail_procedure_and_quality_control'}`
- `multilayer_flange_sheet_attachment`: `{'attachment_segment': 'beyond_theoretical_cutoff', 'force_fraction': 0.5, 'sheet_section_force_capacity_n': 500000.0, 'required_attachment_force_n': 250000.0}`
- `table_43_catalog`: `{'standard': 'СП 16.13330.2017 «Стальные конструкции»', 'version': 'Supplied consolidated text with corrections through 2024 and Amendments No. 1-5', 'clause': '14.4.1', 'table': '43', 'title': 'Flange connections in built-up beams', 'page': 96, 'rows': [{'load_character': 'stationary', 'connection': 'welded', 'equations': ['193', '194'], 'requirements': {'weld_line_count': 'n=2 for two-sided welds; n=1 for one-sided welds'}}, {'load_character': 'stationary', 'connection': 'friction', 'equations': ['195']}, {'load_character': 'moving', 'connection': 'welded_two_sided', 'equations': ['196', '197']}, {'load_character': 'moving', 'connection': 'friction', 'equations': ['198']}], 'definitions': {'T': 'Q*S/I, flange shear flow per unit length using gross flange static moment and gross section moment of inertia', 'V': 'gamma_f*gamma_f1*F_n/l_ef; gamma_f1=1 for stationary loads', 'Q_bh': 'Capacity of one friction plane tightened by one bolt under clause 14.3.3', 'k': 'Number of friction planes under clauses 14.3.3-14.3.4', 's': 'Pitch of flange bolts', 'alpha': {'0.4': 'Load on the upper flange when the web edge is planed to that flange', '1.0': 'No web-edge planing or load on the lower flange'}}, 'routing': {'stationary_upper_without_transverse_stiffener': 'use moving-load formulas', 'stationary_lower_regardless_of_stiffener': 'use moving-load formulas'}, 'notes': ['A weld penetrating the full web thickness is treated as equal-strength with the web.', 'No interpolation is involved in Table 43.']}`

## Scope limitation

Clause 14.4, equations (193)-(198), and Table 43 are implemented. Global force derivation, weld inspection, transverse-stiffener capacity, bolt-layout design, cutoff-point location, and CAD/BIM recognition remain external boundaries.
