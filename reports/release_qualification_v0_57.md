# Release qualification — v0.57 FIRE-UI2.4

- Release: `v0.57_fire_ui24_fire_val1_routing_remediation_r1`
- Package: `0.57.0`
- Parent: `v0.56_fire_ui23_protection_route_closure_r1`
- Engineering-use ready: **False**
- DAG SHA-256: `c0187dc0b0865040482a251abb3eb129d51f87b29499104c302ab06aa289b352`
- DAG: 801 quantities / 39 datasets / 689 nodes / 1174 edges
- Deterministic DAG rebuild x2: **PASS**
- Non-manifest cumulative pytest, file-sharded: **1065/1065 PASS**
- Release-manifest replay: **1/1 PASS**
- Full file-sharded cumulative pytest: **1066/1066 PASS**
- Focused FIRE-UI2.4: **7/7 PASS**
- `main.py` release audit: **PASS**
- Validation corpus: **1876 PASS**
- External golden: **6/6 PASS**
- Unresolved equations/tables: **0/0**
- FIRE-VAL1 500-state rerun unexpected blocked frontiers: **0** (initial campaign: 46)
- FIRE-VAL1 curated seed routes: **18/18 expected result terminals**

`Qy` and general torsion `T` remain explicitly outside the implemented runtime and are not silently remapped.
