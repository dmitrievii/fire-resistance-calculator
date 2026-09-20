# FIRE-UI1.2 — Section Model / Executor Binding Closure

**Release:** `v0.45_fire_ui12_section_model_executor_binding_r1`  
**Parent:** `v0.44_fire_ui11_complete_engineering_questionnaire_section_editor_r1`  
**DAG:** `sp16_sp554_dag_v0-3-48_fire_ui12_section_model_binding`

## Closed in this release

- Profile preview is selected by catalog `shape_group` (I, RHS/SHS, CHS, channel, angle, tee, Z and lipped-C) rather than a hard-coded I-beam.
- `SP554_G_CATALOG` is registered as an executable geometry producer; exact `family_id + designation + source_row_id` selections hydrate the live ledger and continue to steel-grade selection.
- Parametric input is shape-dependent. CHS asks only `D,t`; RHS/SHS asks `h,b,t`; I/channel/tee ask their relevant plate dimensions; angle asks two legs and thickness.
- Two-branch editor v1 supports two identical catalog branches, a symmetry axis and centre-to-centre spacing; section properties are assembled by the parallel-axis theorem.
- Arbitrary section is **manual-properties-only**. The 2D contour editor route was removed by user decision.
- All four geometry providers have explicit control continuation to the material block after successful materialization.

## Acceptance

`ГОСТ Р 57837-2017 → 20К1` now produces `A=5269 mm²`, `Jx/Jy` and elastic section moduli and advances to `SP554_I_STEEL_GRADE`. The former `BLOCKED_EXECUTOR_REQUIRED:SP554_G_CATALOG` is no longer an expected state.

## Deliberate limitations

- The profile catalog is still interim pending original-GOST reconciliation.
- Missing catalog plastic section moduli are **not invented**. `W_pl_x/W_pl_y` are no longer mandatory outputs of the catalog/parametric geometry-provider node; a downstream route needing them must obtain a supported audited value.
- Parametric shapes use sharp-corner geometry where applicable.
- Two-branch v1 does not yet support unequal branches or rotated branches; lattice/batten checks remain later SP16 questions.
- Full SP16 → FIRE-D4 executor binding is not claimed by this release.
