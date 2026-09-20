# Release qualification — v0.53 FIRE-UI2.0

- Release: `v0.53_fire_ui20_conditional_signed_moments_thermal_bindings_r1`
- Package: `0.53.0`
- Parent: `v0.52_fire_ui19_sp554_table1_heated_perimeter_matrix_r1`
- Engineering-use ready: **NO** (`ENGINEERING_USE_READY = False`)
- DAG: `normative_graph/dag_v0.3.56_fire_ui20_conditional_signed_moments_thermal_bindings.json`
- DAG SHA-256: `b452b4fac5976560c94cc704904e53b77fc7f4d9991b758bc6d666037bd3755d`
- DAG census: **783 quantities / 38 datasets / 675 nodes / 1142 edges**
- DAG deterministic rebuild ×2: **PASS**

## Closed in this release

- Boolean engineering inputs render as Да/Нет selectors.
- Raw `beam_ltb_context` authoring is removed.
- SP16 9.2.3 and 9.2.6 use decision-first, branch-conditional signed moment inputs.
- Moment sign is retained end-to-end; `abs()` is used only for normative comparisons.
- Repeat manual input of `M_x_c_signed` is removed.
- SP16 Table 21 has a dedicated explanatory selector.
- `GOST30247_C_FORMULA1_STANDARD_FIRE_CURVE` has a registered production executor.
- `SP554_C_FIG1_UNPROTECTED_INTERPOLATION` has a registered no-extrapolation production executor.
- `SP554_C_UNPROTECTED_STEP_12_1_12_4` is executable.
- The incomplete-mechanical terminal reports the actual deferred load components.

## Explicit open scope

`Qy` axis-specific shear and general torsion `T` are **not** claimed closed in v0.53. They remain fail-closed. No `Qy -> Qz` or `T -> B` substitution is permitted.

## Qualification

- `python main.py`: **PASS**
- Implemented equations/tables/procedures: **240 / 67 / 303**
- Validation cases: **1876 PASS**
- Retained Phase 0.25 validation: **PASS**
- External golden cases: **6/6 PASS**
- Unresolved equations/tables: **0/0**
- Pytest collection: **1029 tests**. All **1028 non-manifest tests PASS** in the source tree.
- Focused FIRE-UI2.0 regression: **8/8 PASS**.
- Release-manifest replay: **1/1 PASS**.
- Source-tree pytest qualification: **1029/1029 PASS** (file-sharded).

The pytest suite was executed file-sharded because one monolithic shell invocation exceeded the execution wrapper timeout; this does not represent a test failure.
