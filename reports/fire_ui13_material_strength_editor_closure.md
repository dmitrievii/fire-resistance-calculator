# FIRE-UI1.3 — Material / Strength Editor Closure

**Release:** `v0.46_fire_ui13_material_strength_editor_r1`  
**Parent:** `v0.45_fire_ui12_section_model_executor_binding_r1`  
**DAG:** `sp16_sp554_dag_v0-3-49_fire_ui13_material_strength_editor`

## Closed in this release

- The ordinary wizard no longer exposes separate free-text `steel_grade` and mandatory `steel_delivery_standard` questions. They are replaced by one compact Material / Strength Editor.
- Product form routes directly to the current materialized СП16 Annex В table: `parallel_flange_i → В.4`, `shaped_rolled → В.5`, and plate/strip, bar and tube products → `В.3`.
- Steel grade is selected from the grades actually present in the applicable table; ordinary UI no longer accepts an arbitrary grade string.
- Thickness is selected from exact printed Annex В intervals. Stable interval keys preserve inclusive/exclusive boundaries; interpolation and extrapolation remain forbidden.
- Catalog/parametric geometry supplies safe suggestions for product form and exact governing thickness where directly available. For welded sections no single web/flange thickness is invented.
- `steel_delivery_standard` is removed from the required primary UI because it was not a selector in the materialized В.3/В.4/В.5 lookup. External product-standard routes remain fail-closed and may require provenance separately.
- Exact row lookup materializes `Ryn`, `Run`, tabulated `Ry` and `Ru` and continues through the SP554 steel-group routing instead of stopping at a UI-only material node.
- The UI shows a read-only `Rs* = 0.58·Ry(tabulated)` reference preview only. It is explicitly not the authoritative production `Rs`, which remains a Table 2 calculation with explicit `gamma_m`.
- В.4 grade designations with `Б` suffixes are accepted by the SP554 ordinary/increased/high group classifier without discarding the exact selected grade in trace/provenance.

## Acceptance example

For a catalog I-section whose normalized geometry supplies `tf = 10 mm`, the material context suggests `parallel_flange_i` / Table В.4. Selecting `С255Б` and the exact interval `до 10 мм включ.` resolves the current-SP16 row and materializes:

- `Ryn = 255 MPa`
- `Run = 380 MPa`
- `Ry(tabulated) = 250 MPa`
- `Ru(tabulated) = 370 MPa`

The guided session then continues to section weakening rather than requiring a delivery-standard text field or stopping at a missing executor.

## Deliberate limitations

- The profile catalog remains interim pending the separately deferred original-GOST reconciliation.
- Welded sections can require component-specific material/thickness resolution for web and flanges; FIRE-UI1.3 does not silently collapse those into one inferred governing thickness.
- The displayed `Rs*` preview is not a substitute for the production Table 2 resistance calculation.
- Full SP16 → FIRE-D4 executor binding is not claimed in this release.
- `ENGINEERING_USE_READY = False`.
