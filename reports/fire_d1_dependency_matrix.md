# FIRE-D1 — SP554 ↔ SP16 mechanical dependency matrix

- Release: `v0.37_fire_d1_sp554_sp16_mechanical_dependency_closure_r1`
- Parent: `v0.36_stage_n10_brittle_fracture_current_sp16_closed_reconstructed_r1`
- DAG SHA-256: `1def1f58d0caa0f387083abeef8651e54fd03eb27117b56ff7325d9410ba5260`

## Census

- SP554 Section 8–11 mechanical nodes: **71**
- SP16 quantity bindings: **92**
- Unique SP16 producer nodes: **53**
- Explicit SP16→SP554 edges: **75**
- Missing required producers: **0**
- Prohibited ordinary design-resistance bindings: **0**

## Interface groups

### FIRE-D1-01-MATERIAL — N1

Normative yield strength and elastic modulus on the fire-design basis.

- Result: **PASS**
- SP554 refs: `8.2, 8.3, 8.4, 8.5, 9.1, 9.2, 10.1, 10.2, 11.1-11.8`
- Policy: SP554 fire mechanics consumes fy_norm/E; no design-Ry substitution is permitted by the bridge.

### FIRE-D1-02-SECTION — N2

Gross/net section geometry and section properties required by the fire strength equations.

- Result: **PASS**
- SP554 refs: `8.3, 9.1, 9.2, 10.1, 10.2, 11.1-11.8`
- Policy: Exact weakening/net geometry remains explicit; no hidden gross-as-net substitution in the bridge.

### FIRE-D1-03-AXIAL — N3

Central-compression stability coefficients and current section-type limits.

- Result: **PASS**
- SP554 refs: `9.1, 9.2, 11.5, 11.6, 11.8`
- Policy: The SP16 central-compression route is reused as a coefficient producer, not as a normal-temperature utilization result.

### FIRE-D1-04-BENDING — N4

Bending class, Annex Ж lateral-torsional stability and local-stress producers.

- Result: **PASS**
- SP554 refs: `10.1, 10.2`
- Policy: Applicable Annex Ж branch must be selected explicitly; alternative phi_b producers are branch alternatives, not values to combine.

### FIRE-D1-05-BEAM-COLUMN — N5

phi_e, eta/m_eff and out-of-plane coefficient c for N+M fire checks.

- Result: **PASS**
- SP554 refs: `11.2, 11.3, 11.5, 11.7`
- Policy: Annex Д.3 remains exact-grid/fail-closed unless an explicitly sourced external coefficient is supplied.

### FIRE-D1-06-BIAXIAL-BOX — N5/N6

Biaxial and box-section stability coefficient producers retained by the detailed SP16 Section 9 layer.

- Result: **PASS**
- SP554 refs: `11.7, 11.8`
- Policy: Box/biaxial routes remain selected detailed actions; unsupported geometry or coefficient interpolation fails closed.

### FIRE-D1-07-EFFECTIVE-LENGTH — N7

Effective-length factor mu and effective length needed by compression/fire-stability checks.

- Result: **PASS**
- SP554 refs: `8.2, 8.6, 11.4`
- Policy: Current Section 10 selected-route/fail-closed policy governs mu; no legacy guessed effective-length factor is accepted.

## Scope boundary

- Member mechanical dependency closure: **PASS**
- Connections: `OUTSIDE_FIRE_D1_MEMBER_SCOPE`
- Thermal Section 12: `NOT_IN_FIRE_D1_SCOPE`

