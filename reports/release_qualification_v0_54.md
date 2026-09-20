# Release qualification — v0.54 FIRE-UI2.1

- Release: `v0.54_fire_ui21_selector_hardening_qy_t_lock_r1`
- Package: `0.54.0`
- Parent: `v0.53_fire_ui20_conditional_signed_moments_thermal_bindings_r1`
- Engineering-use ready: **NO** (`ENGINEERING_USE_READY = False`)
- DAG: `normative_graph/dag_v0.3.57_fire_ui21_selector_hardening_qy_t_lock.json`
- DAG SHA-256: `68a36f8ea58eae76a393d5e5a7ce25bfb5e701fc4a8fc4e571e7af9f2c9f1ec5`
- DAG census: **783 quantities / 38 datasets / 675 nodes / 1142 edges**
- DAG deterministic rebuild ×2: **PASS**

## Closed in this release

- The blank boolean-dropdown defect is fixed globally, not only for the two reported fields.
- Every generic boolean contract field carries explicit `Да/Нет` choices.
- Every generic enum/boolean/decision selector is audited for a non-empty option set; current census: **129 selectors, 0 empty**.
- All selector options have non-empty values and labels and no duplicate values within a selector.
- Dynamic profile selectors were checked across **37 families / 4069 profiles** with no empty family.
- Dynamic material selectors were checked across **5 product forms** with no empty grade or thickness-interval list.
- `Qy` and `T` are disabled in the primary load UI and fixed to zero until their mechanics are implemented.

## Explicit open scope

General `Qy` axis-specific shear and torsion `T` remain **not implemented**. Externally supplied nonzero values still fail closed. No `Qy -> Qz` or `T -> B` substitution is permitted.

## Qualification

- `python main.py`: **PASS**
- Implemented equations/tables/procedures: **240 / 67 / 303**
- Validation cases: **1876 PASS**
- Retained Phase 0.25 validation: **PASS**
- External golden cases: **6/6 PASS**
- Unresolved equations/tables: **0/0**
- Pytest collection: **1035 tests**
- All **1034 non-manifest tests PASS** in file-sharded source-tree qualification.
- Focused FIRE-UI2.1 selector/lock regression: **6/6 PASS**.
- Release-manifest replay: **1/1 PASS**.
- Source-tree pytest qualification: **1035/1035 PASS** (file-sharded).
