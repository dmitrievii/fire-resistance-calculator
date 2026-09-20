# Stage N3 guided solid axial-member case

- Case ID: `N3-GUIDED-SOLID-001`
- Release: `v0.57_fire_ui24_fire_val1_routing_remediation_r1`

## Results

- `force_state`: `compression`
- `equation_5`: `{'resistance_branch': {'branch': 'yield', 'force_state': 'compression', 'Ryn_n_mm2': 355.0, 'post_yield_service_possible': False, 'reason': '7.1.1 Ryn <= 440 N/mm2 and no tensile post-yield-service exception', 'source_clause': '7.1.1'}, 'utilization': 0.2916047006677748, 'pass': True}`
- `equation_6_single_angle`: `{'status': 'not_applicable', 'utilization': None, 'pass': None}`
- `compression_stability`: `{'status': 'evaluated', 'geometric_slenderness': 60.2449017658351, 'relative_slenderness': 2.4654502189604086, 'section_type': 'b', 'phi': 0.7478408819411195, 'table_d1_reference': {'status': 'not_an_exact_table_node_no_interpolation_applied', 'phi': None}, 'selected_formula': 'both', 'equation_7': {'utilization': 0.3899288039868539, 'pass': True}, 'equation_7a': {'gamma_res': {'gamma_res': 1.0, 'relative_slenderness': 2.4654502189604086, 'design_yield_resistance_n_mm2': 345.0, 'route': '245<Ry<390: linear interpolation in Ry between endpoint gamma_res rules', 'source_clause': '7.1.3', 'source_equation': '(7a) coefficient rule', 'source_sha256': '302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873'}, 'utilization': 0.3899288039868539, 'pass': True}}`
- `governing_pass`: `True`

## Scope limitation

Stage N3 guided clauses 7.1.1-7.1.3. Branch selection is normative and only applicable checks are evaluated. Compression stability requires explicit 7.3.2-7.3.9 prerequisite confirmation. The optional rolled-I equation (7a) route is current-СП16 source-backed.
