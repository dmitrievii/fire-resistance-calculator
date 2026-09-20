# Centrally compressed member local-stability case

- Case ID: `LOCAL-STABILITY-EXAMPLE-001`
- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`

## Results

- `actual_wall_relative_slenderness`: 2.59454127303
- `base_wall_limiting_relative_slenderness`: 2.075
- `equation_30_longitudinal_stiffener_multiplier`: 1
- `wall_limit_after_longitudinal_stiffener`: 2.075
- `two_plane_increase_factor`: 1
- `final_wall_limiting_relative_slenderness`: 2.075
- `wall_local_stability_pass`: `False`
- `actual_flange_relative_slenderness`: 0.415126603685
- `base_flange_limiting_relative_slenderness`: 0.61
- `final_flange_limiting_relative_slenderness`: 0.61
- `flange_local_stability_pass`: `True`
- `transverse_stiffener_requirements`: `{'required': True, 'trigger_exception_geometrically_nonlinear': False, 'minimum_spacing_mm': 1250.0, 'maximum_spacing_mm': 1500.0, 'minimum_outstand_mm': 56.66666666666667, 'provided_outstand_mm': 60.0, 'outstand_pass': True, 'minimum_thickness_mm': 4.981519244224851, 'location_rule': 'general_transverse_stiffener_layout', 'one_sided_angle_weld_orientation': None}`
- `edge_stiffener_requirements`: `{'minimum_edge_height_mm': 36.0, 'minimum_edge_thickness_mm': 2.98891154653491}`
- `reduced_area_assessment`: `{'actual_to_limit_ratio': 1.25038133640182, 'required': True, 'within_central_compression_reduction_domain': True, 'formula_route_permitted': True}`
- `reduced_area_status`: `applied`
- `reduced_web_height_mm`: 375.75222874
- `reduced_box_flange_width_mm`: 300
- `design_area_mm2`: 9006.01782992

## Scope limitation

Clauses 7.3.1-7.3.11 only. Diagram-group selection and effective-dimension extraction from geometry remain explicit engineering inputs. Equation (33) is available in the core but complete eccentric-compression design is outside this runner.
