# Bolted and friction-connection case

- Case ID: `V16-DEMO-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `table_40_hole_diameter_mm`: 22
- `table_40_requirements`: `{'minimum_center_spacing_mm': 55.0, 'maximum_center_spacing_mm': 288.0, 'minimum_edge_along_force_mm': 44.0, 'minimum_edge_transverse_force_mm': 33.0, 'maximum_edge_distance_mm': 88.0, 'minimum_friction_edge_distance_mm': 28.6, 'minimum_staggered_longitudinal_spacing_mm': 83.0}`
- `table_40_layout_check`: `{'checks': {'center_min': True, 'center_max': True, 'edge_along_min': True, 'edge_along_max': True, 'edge_transverse_min': True, 'edge_transverse_max': True}, 'pass': True}`
- `table_41_gamma_b`: 0.9
- `equation_186_shear_capacity_n`: 105840
- `equation_187_bearing_capacity_n`: 194400
- `equation_188_tension_capacity_n`: 68400
- `long_joint_beta`: 0.98
- `equation_189_bolt_count`: `{'governing_mode': 'shear', 'governing_capacity_n': 105840.0, 'continuous_required_bolts': 2.89231338794021, 'required_bolts': 3}`
- `bolt_group_distribution`: `{'centroid_mm': [0.0, 0.0], 'bolt_forces': [{'index': 0, 'x_from_centroid_mm': -50.0, 'y_from_centroid_mm': -40.0, 'force_x_n': 37195.12195121951, 'force_y_n': -15243.90243902439, 'resultant_n': 40197.68225329148}, {'index': 1, 'x_from_centroid_mm': 50.0, 'y_from_centroid_mm': -40.0, 'force_x_n': 37195.12195121951, 'force_y_n': 15243.90243902439, 'resultant_n': 40197.68225329148}, {'index': 2, 'x_from_centroid_mm': -50.0, 'y_from_centroid_mm': 40.0, 'force_x_n': 12804.878048780487, 'force_y_n': -15243.90243902439, 'resultant_n': 19908.326484529887}, {'index': 3, 'x_from_centroid_mm': 50.0, 'y_from_centroid_mm': 40.0, 'force_x_n': 12804.878048780487, 'force_y_n': 15243.90243902439, 'resultant_n': 19908.326484529887}], 'maximum_resultant_n': 40197.68225329148, 'governing_bolt_index': 0}`
- `equation_190_utilization`: 0.578962151509
- `equation_190_pass`: `True`
- `clause_14_2_14_adjusted_count`: `{'factor': 1.1, 'adjusted_bolt_count': 4}`
- `table_42_parameters`: `{'friction_coefficient': 0.58, 'gamma_h': 1.12, 'clearance_route': 'small', 'tightening_control': 'torque'}`
- `equation_191_capacity_per_friction_plane_n`: 35421.4285714
- `equation_192_friction_bolt_count`: `{'required_bolts': 4, 'connection_factor_gamma_b': 0.8, 'continuous_required_bolts_at_governing_factor': 3.5289372857430936, 'total_design_capacity_n': 226697.14285714284}`
- `clause_14_3_6_tension_reduction`: `{'bolt_pretension_n': 68400.0, 'reduction_factor': 0.8538011695906433, 'adjusted_connection_factor_gamma_b': 0.6830409356725147}`
- `clause_14_3_7_diameter_check`: `{'summed_thickness_mm': 60.0, 'maximum_summed_thickness_mm': 80.0, 'utilization': 0.75, 'pass': True}`
- `clause_14_3_10_washer`: `{'one_washer_under_nut_permitted': True, 'required_arrangement': 'one_washer_under_nut'}`
- `clause_14_3_11_selected_area`: `{'selected_area_mm2': 944.0, 'area_type': 'effective_1_18_net', 'net_to_gross_ratio': 0.8}`
- `external_requirements`: `{'bolt_product_standards': 'Tables G.3-G.7 and G.9 are external data dependencies', 'washers_and_installation': 'SP 70.13330', 'anchor_bolts': 'SP 43.13330', 'anti_loosening': 'Project drawings must specify the adopted measure', 'friction_project_data': ['bolt, nut, and washer grades and mechanical properties', 'surface treatment', 'bolt pretension P_b'], 'access_requirement': 'Free access for installation, package clamping, and controlled tightening is required'}`

## Scope limitation

Clauses 14.2-14.3, equations (186)-(192), and Tables 40-42 are implemented. Product standards, anchor design, installation verification, CAD recognition, and global load derivation remain external boundaries.
