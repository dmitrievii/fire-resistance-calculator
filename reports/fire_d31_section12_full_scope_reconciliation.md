# FIRE-D3.1 — SP554 Section 12 Full-Scope Reconciliation

Release target: `v0.40_fire_d31_sp554_section12_full_scope_reconciliation_r1`

## Decision

**Normative full-scope reconciliation: CLOSED.**

This does **not** mean that every printed Section-12 recurrence has been promoted to executable production code. FIRE-D3.1 explicitly separates:

- `FIRE_D31_SP554_SECTION12_FULL_SCOPE_RECONCILED = True`; and
- `FIRE_D3_SP554_SECTION12_FULL_SCOPE_CLOSED = False`.

The remaining literal-runtime boundary is the repeated application of the fictitious temperature `t_phi` for `W>0`. Formula (12.8) itself is algebraically executable. A repeated per-time-step subtraction is not promoted because neither the enacted SP554 clause text nor the predecessor calculation text defines a moisture-depletion/state variable that makes such a recurrence invariant to time-step refinement.

## Authoritative source state

SP 554 is no longer only a draft-source target. The enacted designation is **СП 554.1311500.2026**, introduced from **2026-09-01** by MChS Order No. 505 dated 2026-07-03 and included in the voluntary compliance list by Rosstandart Order No. 1736 dated 2026-08-27.

The package retains the exact byte-locked pre-enactment DOCX as equation-level local provenance:

- `СП Стальные 27.05_0 (1) (1).docx`
- SHA-256 `86a3c010ee74e469670f7aff5b95c807ffcff81bc81cbebe16f994af477507e3`

The enacted clause text/designation was reconciled separately. Because the final published formulas are image-rendered in the currently accessible source, FIRE-D3.1 does not pretend that those images have been byte-compared against the locked DOCX equations. Existing confirmed errata overlays therefore remain explicit and auditable.

## Section 12 route census

| Route | FIRE-D3.1 state | Production policy |
|---|---|---|
| 12.1–12.4 unprotected steel, step calculation | CLOSED | executable |
| Figure 1 unprotected nomogram | CLOSED | interpolation only inside published domain |
| 12.4 / 12.7–12.10 documented test matrix / nomogram | CLOSED | direct/inverse interpolation, no extrapolation |
| 12.5 FDM, `W=0` | CLOSED | executable with mandatory 12.6 validation |
| 12.6 ±20% validation gate | CLOSED | mandatory |
| 12.8 scalar fictitious temperature | CLOSED | algebraic helper implemented |
| 12.5 FDM, `W>0`, moisture already embedded in fitted/nonlinear thermal properties | CLOSED WITH EVIDENCE | explicit `embedded_in_thermal_properties`, no separate `t_phi`, mandatory 12.6 validation |
| 12.5 FDM, `W>0`, literal repeated `t_phi` subtraction | FAIL-CLOSED | not promoted without a separately validated moisture-state model |

## Reconciliation of moisture accounting

SP554 (12.8) identifies initial mass moisture `W` and latent heat of water vaporization `r = 2260·10^3 J/kg`. It also requires the thermal properties of a specific protection material to be identified from experimental data by solving an inverse heat-transfer problem and permits nonlinear thermal properties in calculation software.

The predecessor ARSS method contains the same fictitious-temperature mechanism. An ARSS expert clarification states that `t_phi` represents moisture evaporation and that if moisture is already included in material thermal-property input / identified conductivity and heat capacity, `t_phi` should not additionally be applied. FIRE-D3.1 converts that into an explicit anti-double-counting policy.

### Supported W>0 route

The input must explicitly declare:

```json
{
  "initial_moisture_percent": 5.0,
  "moisture_accounting_mode": "embedded_in_thermal_properties",
  "moisture_embedded_in_properties_confirmed": true
}
```

Production behavior:

1. evaluate the initial scalar `t_phi` as trace/evidence;
2. do **not** subtract it from temperatures;
3. use the experimentally identified/nonlinear thermal properties that already embody moisture behavior;
4. require 12.6 validation against fire-test / certification time data;
5. reject the result if the ±20% criterion fails.

### Explicit t_phi route

```json
{
  "moisture_accounting_mode": "explicit_t_phi_12_8"
}
```

is rejected with a normative fail-closed diagnostic. This is intentional. Treating the scalar `t_phi` as a decrement on every numerical step would make total latent-heat removal depend on the arbitrary number of time steps unless an additional moisture-depletion state/evolution law is supplied. Such a state law is not invented in this package.

## Additional remediation

FIRE-D3.1 also allows an explicit protection-surface emissivity in `protection_model.surface_emissivity`. If omitted, the frozen FIRE-D3 fallback is preserved for backward compatibility. The admissible range is `(0, 1]`.

## DAG

New cumulative graph:

`normative_graph/dag_v0.3.43_fire_d31.json`

Frozen counts:

- quantities: 743
- nodes: 651
- edges: 1100
- datasets: 38
- SHA-256: `5b19204e3ec29a7289bdbe8a483122c8e4b0c63b5fd0c2aad677bc9529a7892f`

The graph explicitly carries both facts:

- full Section-12 **reconciliation** is true;
- full literal Section-12 **runtime closure** remains false.

## Engineering qualification

`ENGINEERING_USE_READY = False` remains unchanged. FIRE-D3.1 closes the Section-12 ambiguity/classification boundary; it does not replace the external validation/certification requirements of SP554 7.4/12.6 or the remaining package-wide release gates.
