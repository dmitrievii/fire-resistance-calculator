# SP16-MECH7 v0.64 Release Qualification

- Release: `v0.64_sp16_mech7_primary_ambient_workflow_binding_r1`
- Package: `0.64.0`
- Parent: `v0.63_sp16_mech6_mechanical_pass_gate_r1`
- Active DAG: `normative_graph/dag_v0.3.67_sp16_mech7_primary_ambient_binding.json`
- Active DAG SHA-256: `be105f728645122d671b44ced248e7a40b69e0aa45a1e9900466f2825f3d9d74`
- DAG counts: **858 quantities / 39 datasets / 722 nodes / 1219 edges**
- UI contract: **168 interactive / 54 result nodes**

## Closed scope

- Executable primary ambient evidence binding before the strict SP16-MECH6 gate.
- Supported axial strength, central-compression stability and Table 32 limiting-slenderness evidence.
- Supported elastic `Mx/My/B` section strength, supported `N+M` evidence and major-axis LTB binding.
- Central-compression local web/flange stability for supported doubly-symmetric I-sections using the qualified Table 9 / Table 10 functions after explicit classification inputs.
- Explicit fatigue and Section 13 applicability classification.
- The canonical `SP16_MECHANICAL_PASS` gate remains mandatory; no production bypass was added.

## Deliberately open / fail-closed

- Not every N3-N10 route is automatically bound/executed in the primary flow.
- Dedicated `M+Q`, universal torsion-resistance and remaining detailed local-stability routes remain fail-closed without qualified evidence.
- If fatigue or brittle-fracture verification is required, complete N9/N10 evidence is still required.
- SP554 complex-state handoff for nonzero fire `Qy/T` remains fail-closed pending FIRE-BRIDGE2.
- `ENGINEERING_USE_READY = False`.

## Source-tree qualification

- SP16-MECH1..7 + affected FIRE-UI16..24: **142/142 PASS**
- SP16 core mechanics A: **163/163 PASS**
- SP16 core mechanics B + final audit: **260/260 PASS**
- N1-N10 workflows: **243/243 PASS**
- FIRE/SP554 + adjacent runtime: **93/93 PASS**
- Docstrings + independent rebaseline + final audit: **9/9 PASS**
- Phase 0.23: **5/5 PASS**
- Phase 0.24: **6/6 PASS**
- Phase 0.25 + docstrings + schemas + UI0: **71/71 PASS**

Deterministic ZIP and fresh-extraction gates are added during final packaging.
