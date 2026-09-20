# FIRE-UI1.9 — SP554 Table 1 Heated-Perimeter Matrix Closure

Release: `v0.52_fire_ui19_sp554_table1_heated_perimeter_matrix_r1`  
Parent: `v0.51_fire_ui18_fire_d2_to_d3_handoff_hotfix_r1`  
DAG: `normative_graph/dag_v0.3.55_fire_ui19_sp554_table1_heated_perimeter_matrix.json`  
DAG SHA-256: `431a2a4345af544edf644625b9b22bdd57929cedefefb9117e4d0e93efca581f`

## Closed scope

The Section-12 route now separates heated-side exposure from fire-protection geometry. `three_sides/four_sides` describes exposure; `contour/box` describes how the fire protection is arranged.

For the supported SP554 Table-1 I-section route:

- contour / steel contour, 4 sides: `P = 4B + 2D - 2t`;
- contour / steel contour, 3 sides: `P = 3B + 2D - 2t`;
- box, 4 sides: `P = 2B + 2D`;
- box, 3 sides: `P = B + 2D`.

Protected calculations use `P_heated_protected` and `delta_pr_protected` and do not reuse the unprotected contour `A/P`. Unsupported geometric families fall back to explicit manual perimeter input rather than a guessed envelope.

## 20К1 regression

With `B=199 mm`, `D=196 mm`, `t=6.5 mm`, `A=5269 mm²`:

- contour, 4 sides: `P=1.175 m`, `delta_pr=4.484255 mm`;
- contour, 3 sides: `P=0.976 m`;
- box, 4 sides: `P=0.790 m`, `delta_pr=6.669620 mm`;
- box, 3 sides: `P=0.591 m`.

## Qualification

- FIRE-UI1.9 + retained FIRE-UI regressions: **69/69 PASS**.
- Independent normative rebaseline + release/API: **10/10 PASS**.
- Phase 0.25: **6/6 PASS** in individual runs.
- FIRE-D2/D3 group A: **36/36 PASS**.
- FIRE-D3/D3.1 group B: **31/31 PASS**.
- FIRE-UI0 architecture: **11/11 PASS**.
- `main.py`: **Release audit PASS**; validation corpus **1876 PASS**.
- Public API docstrings: **658/658 PASS**.

`ENGINEERING_USE_READY` remains `False`; this closure concerns Table-1 heated-perimeter routing and propagation, not final engineering certification of the whole package.
