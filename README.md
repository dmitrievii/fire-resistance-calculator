# SP16 / SP554 cumulative package — FIRE-BRIDGE2 Qualified SP16 Complex-State Handoff

This cumulative release is **`v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`**, built over the verified v0.66 SP16-MECH9 baseline.

## FIRE-BRIDGE2 closure

- inserts a typed handoff after the strict `SP16_MECHANICAL_PASS` production gate; explicit Sections 9–11 routes do not require pointwise normal-stress recovery, while the internal §8.7 route does;
- preserves all existing explicit SP554 Sections 9–11 routes for supported states;
- adds an internal SP554 §8.7 route that derives governing `|sigma_n|` directly from the qualified same-point SP16 FIRE state instead of requiring a second manual software-stress input;
- permits biaxial normal stress and direct bimoment `B` in that normal-stress handoff when upstream MECH5 pointwise recovery is complete;
- explicitly forbids treating SP554 §8.7 as a universal replacement for missing transverse-shear or torsion fire checks;
- keeps nonzero `Qy` and general torsion `T` fail-closed at the SP554 fire-resistance boundary even though their 20 °C mechanics fields are available upstream;
- never substitutes `Qy -> Qx`, never forms a fictitious resultant action `Q`, and never substitutes `T -> B`;
- replaces the old blanket legacy Qy/T terminal with a traceable FIRE-BRIDGE2 contract that reports supported/unsupported fire actions and retains the diagnostic normal-stress state.

Active DAG: `normative_graph/dag_v0.3.70_fire_bridge2_qualified_sp16_complex_state_handoff.json` — **922 quantities / 39 datasets / 734 nodes / 1246 edges**.

Presentation policy: `data/fire_bridge2_presentation_policy.json`.

`ENGINEERING_USE_READY = False` remains unchanged because the SP554 fire-specific handoff for nonzero `Qy` and arbitrary `T` is still not normatively closed.

---

# SP16 / SP554 cumulative package — SP16-MECH9 Remaining Ambient Applicability Closure

This cumulative release is **`v0.66_sp16_mech9_remaining_ambient_applicability_closure_r1`**, built over the verified v0.65 SP16-MECH8 baseline.

## SP16-MECH9 closure

- closes the bounded class-3 one-plane `Mx+Qx` route only after explicit confirmation of the SP16 §8.2.7 prerequisite chain (§8.2.5, §8.4.6, §8.5.8, §8.5.9, §8.5.18 and the shear-effect condition at the maximum-moment section);
- evaluates the qualified class-3 I/box resistance with the existing §8.2.3 Eq.(50)/(52) and Annex E Table E.1 machinery after all applicability gates are satisfied;
- auto-executes the ordinary fatigue route of SP16 §12.1.2 through the already qualified Stage-N9 workflow with explicit Annex-K case selection and stress/load-basis confirmations;
- auto-executes the Section-13 brittle-fracture review through the already qualified Stage-N10 workflow, including optional lamellar-tearing/Z-quality routing when explicitly required;
- preserves crane-runway fatigue §12.2 as a dedicated fail-closed route and preserves low-cycle fatigue `<1e5` as an external-method boundary;
- keeps universal arbitrary-`T` resistance, class-3 biaxial / `N+M+Q`, unsupported detailed local-stability geometries, and the nonzero-fire-`Qy/T` SP554 complex-state handoff fail-closed;
- fixes MECH9 routing so the class-3 branch is mutually exclusive with the non-class-3 path, and pure-shear cases do not request section class unnecessarily;
- feeds the cumulative MECH9 evidence bundle into the unchanged strict `SP16_MECHANICAL_PASS` gate before SP554.

Active DAG: `normative_graph/dag_v0.3.69_sp16_mech9_remaining_ambient_closure.json` — **918 quantities / 39 datasets / 732 nodes / 1242 edges**.

Presentation policy: `data/sp16_mech9_presentation_policy.json`.

`ENGINEERING_USE_READY = False` remains unchanged because unsupported special ambient routes and the qualified complex-state SP554 handoff are not all closed.

---

# SP16 / SP554 cumulative package — SP16-MECH8 M+Q Interaction + Torsion Scope Reconciliation

This cumulative release is **`v0.65_sp16_mech8_mq_interaction_torsion_scope_r1`**, built over the verified v0.64 SP16-MECH7 baseline.

## SP16-MECH8 closure

- closes the supported class-1 `Mx+Qx` beam interaction through SP16 §8.2.1 Eq.(44), using signed `sigma_x`, explicitly classified `sigma_y`, and `tau_xy` at the same web point;
- preserves Eq.(45) hole amplification in the Eq.(44) shear term where applicable;
- closes supported class-2 I/box M+Q routes through §8.2.3 Eqs.(50)-(53), Eq.(52), Annex E Table E.1 and Table 10a with explicit applicability/table classifications;
- does not silently extend the qualified Eq.(44) route to `N+M+Q`, `My/Qy/B` combinations or unresolved local web stress; these remain fail-closed;
- keeps class-3 M+Q fail-closed until the full redistribution/applicability chain is bound;
- explicitly reconciles free torsion `T`: MECH4 pointwise `T→tau_T` mechanics remains valid, but no universal arbitrary-T SP16 resistance equation is fabricated; only clause-specific torsion routes may provide normative PASS;
- feeds the cumulative MECH8 evidence bundle into the unchanged strict `SP16_MECHANICAL_PASS` gate before SP554.

Active DAG: `normative_graph/dag_v0.3.68_sp16_mech8_mq_torsion_scope.json` — **866 quantities / 39 datasets / 725 nodes / 1224 edges**.

Presentation policy: `data/sp16_mech8_presentation_policy.json`.

`ENGINEERING_USE_READY = False` remains unchanged because class-3 M+Q, universal arbitrary-T resistance, remaining detailed primary bindings and the qualified complex-state SP554 handoff are not all closed.

---

# SP16 / SP554 cumulative package — SP16-MECH7 Primary Ambient Verification Workflow Binding

This cumulative release is **`v0.64_sp16_mech7_primary_ambient_workflow_binding_r1`**, built over the verified v0.63 SP16-MECH6 baseline.

## SP16-MECH7 closure

- inserts an executable primary ambient evidence-binding layer between `SP16_APPLICABILITY_CENSUS` and the strict SP16-MECH6 gate;
- automatically binds qualified evidence for supported axial strength, central-compression stability, Table 32 limiting slenderness, elastic `Mx/My/B` section strength, supported `N+M` checks and major-axis LTB;
- closes central-compression local web/flange stability for supported doubly-symmetric I-sections through the existing qualified Table 9 / Table 10 functions after explicit user classification of the normative groups;
- asks explicitly whether fatigue and Section 13 brittle-fracture checks are required instead of silently assuming applicability;
- preserves the strict rule that mechanics/stress recovery alone is never a normative PASS;
- preserves fail-closed status for unsupported `M+Q`, universal torsion resistance, remaining detailed local-stability routes and required N9/N10 checks without their full evidence;
- does not route around the canonical `SP16_MECHANICAL_PASS` gate.

Active DAG: `normative_graph/dag_v0.3.67_sp16_mech7_primary_ambient_binding.json` — **858 quantities / 39 datasets / 722 nodes / 1219 edges**.

Presentation policy: `data/sp16_mech7_presentation_policy.json`.

`ENGINEERING_USE_READY = False` remains unchanged because complete automatic primary-flow binding of every applicable N3–N10 route is still not closed.

---

# SP16 / SP554 cumulative package — SP16-MECH6 Strict Ambient Mechanical PASS Gate

This cumulative release is **`v0.63_sp16_mech6_mechanical_pass_gate_r1`**, built over the verified v0.62 SP16-MECH5 baseline.

## SP16-MECH6 closure

- converts the ambient `SP16_APPLICABILITY_CENSUS` into a strict evidence-based verification ledger;
- uses explicit statuses `PASS`, `FAIL`, `N.A.`, `DEFERRED` and `CONTEXT_UNRESOLVED`;
- exposes one canonical `SP16_MECHANICAL_PASS` quantity;
- prohibits transition to `FIRE_LOAD_CASE` / SP554 unless `SP16_MECHANICAL_PASS = true`;
- treats mechanics recovery (`tau_Qx`, `tau_Qy`, `tau_T`, `sigma_B`) as mechanics evidence only, never as a normative PASS by itself;
- consumes existing qualified N3–N10 evidence when it is present in the ambient session;
- returns `FAIL` if any applicable explicit SP16 check fails;
- returns `INCOMPLETE_FAIL_CLOSED` if any applicable/context-driven check lacks qualified normative evidence;
- keeps downstream SP554 runtime regression-testable as an isolated subsystem without providing a production bypass around the gate;
- does **not** yet claim automatic primary-flow execution/binding of every N3–N10 workflow.

Active DAG: `normative_graph/dag_v0.3.66_sp16_mech6_mechanical_pass_gate.json` — **848 quantities / 39 datasets / 717 nodes / 1212 edges**.

Presentation policy: `data/sp16_mech6_presentation_policy.json`.

`ENGINEERING_USE_READY = False` remains unchanged because `sp16_mech6_all_n3_n10_primary_flow_bindings_closed = False`.

---

# SP16 / SP554 cumulative package — SP16-MECH5 Direct Bimoment + Complete Pointwise Recovery

This cumulative release is **`v0.62_sp16_mech5_direct_bimoment_pointwise_recovery_r1`**, built over the verified v0.61 SP16-MECH4 baseline.

## SP16-MECH5 closure

- preserves the agreed user workflow: ask whether bimoment `B` is required; if yes, accept signed direct `B`, if no, materialize explicit `B=0`;
- does **not** derive `B` from torsional moment `T` and does not introduce a restrained-torsion solver;
- for doubly-symmetric I-sections, derives a consistent thin-wall sectorial-coordinate field `omega(P)` and `I_omega`;
- recovers the SP16 Eq. (43)/(106) normal-stress term `sigma_B=B*omega/I_omega` on the same material points used by MECH3/4;
- materializes the complete supported pointwise mechanics state `N/Mx/My/Qx/Qy/T/B`;
- keeps `B=0` complete for every geometry already supported by MECH4;
- keeps nonzero-B channel/tee/RHS/arbitrary warping geometry fail-closed instead of using an unqualified `W_omega` shortcut;
- retains the legacy SP554 fail-closed gate for nonzero fire `Qy/T` until FIRE-BRIDGE2;
- does not yet claim the aggregate `SP16_MECHANICAL_PASS` gate.

Active DAG: `normative_graph/dag_v0.3.65_sp16_mech5_direct_bimoment_pointwise_recovery.json` — **841 quantities / 39 datasets / 713 nodes / 1208 edges**.

Presentation policy: `data/sp16_mech5_presentation_policy.json`.

`ENGINEERING_USE_READY = False` remains unchanged.

---

# SP16 / SP554 cumulative package — SP16-MECH4 Free Torsion T + Pointwise Recovery

This cumulative release is **`v0.61_sp16_mech4_free_torsion_pointwise_recovery_r1`**, built over the verified v0.60 SP16-MECH3 baseline.

## SP16-MECH4 closure

- keeps canonical `T` as the signed Saint-Venant/free-torsion action about the member axis `s`; `T` is never aliased to `Mx` or to bimoment `B`;
- uses current SP16 Annex-D `It=(k/3)Σ(b_i t_i^3)` for supported open I/tee/channel templates;
- uses a labelled single-cell Bredt thin-wall mechanics model for RHS/SHS free torsion;
- recovers `tau_T(P)` on the same deterministic material points already used by SP16-MECH3;
- combines `Qx`, `Qy` and `T` only as stress-vector components at the same point, never as a scalar resultant action;
- materializes the ambient and fire same-point `N/Mx/My/Qx/Qy/T` mechanics states;
- preserves the agreed direct-input policy for `B`: `B` is optional, signed, independent of `T`, and is not inferred by a restrained-torsion solver;
- explicitly marks warping-normal stress from nonzero `B` as not recovered in this stage;
- closes ambient free-torsion mechanics for supported templates, while keeping unsupported geometry fail-closed;
- intentionally keeps non-zero fire `Qy/T` fail-closed at the legacy SP554 handoff until FIRE-BRIDGE2;
- does not yet claim the final `SP16_MECHANICAL_PASS` gate.

Active DAG: `normative_graph/dag_v0.3.64_sp16_mech4_free_torsion_pointwise_recovery.json` — **835 quantities / 39 datasets / 711 nodes / 1206 edges**.

Presentation policy: `data/sp16_mech4_presentation_policy.json`.

`ENGINEERING_USE_READY = False` remains unchanged.

---

# SP16 / SP554 cumulative package — SP16-MECH3 Axis-Specific Qx/Qy + Pointwise Recovery

This cumulative release is **`v0.60_sp16_mech3_axis_shear_pointwise_recovery_r1`**, built over the verified v0.59 SP16-MECH2 baseline.

## SP16-MECH3 closure

- keeps canonical `Qx` and `Qy` as independent signed actions; no scalar resultant `sqrt(Qx^2+Qy^2)` is introduced;
- adds axis-specific Qx/Qy recovery for ambient and fire load cases;
- materializes SP16 8.2.3 I/box component checks `tau_x=Qx/Aw` and `tau_y=Qy/(2Af)`;
- recovers signed same-point `tau_x(P)`, `tau_y(P)` and concurrent `sigma_N+Mx+My(P)` for supported deterministic section templates;
- closes ambient `Qy` mechanics for supported geometry and feeds the resolved state into the SP16 applicability census;
- keeps torsion `T` fail-closed for SP16-MECH4;
- intentionally keeps non-zero fire `Qy` fail-closed at the legacy SP554 handoff until the typed FIRE-BRIDGE stage;
- fixes the inherited routing defect that could previously allow the normal SP554 branch to run in parallel with a deferred Qy/T branch;
- does not yet claim the final `SP16_MECHANICAL_PASS` gate.

Active DAG: `normative_graph/dag_v0.3.63_sp16_mech3_axis_shear_pointwise_recovery.json` — **829 quantities / 39 datasets / 707 nodes / 1198 edges**.

Presentation policy: `data/sp16_mech3_presentation_policy.json`.

`ENGINEERING_USE_READY = False` remains unchanged.

---

# SP16 / SP554 cumulative package — SP16-MECH2 Ambient/Fire Load Cases + Applicability Census

This cumulative release is **`v0.59_sp16_mech2_load_cases_applicability_census_r1`**, built over the verified v0.58 SP16-MECH1 baseline.

## SP16-MECH2 closure

- introduces separate typed `AMBIENT_LOAD_CASE` and `FIRE_LOAD_CASE`;
- requires an explicit user decision whether the fire actions are identical to ambient or are entered separately;
- never silently copies ordinary design actions into the fire case;
- keeps canonical SP16 actions `N, Mx, My, Qx, Qy, T` and conditional direct `B`;
- resolves ambient and fire bimoment independently through the agreed yes/no + direct-input policy;
- creates a machine-readable ambient `SP16_APPLICABILITY_CENSUS`;
- enumerates action-driven checks and preserves context-driven checks (LTB, local stability, fatigue, brittle-fracture applicability) as explicit unresolved/context items rather than dropping them;
- makes `Qy` and `T` visible to the census, but keeps them fail-closed: `Qy` -> SP16-MECH3, `T` -> SP16-MECH4;
- preserves the already-qualified downstream SP554 scalar action contract as the **fire** compatibility layer during this staged migration;
- does **not** yet claim the final `SP16_MECHANICAL_PASS` ambient gate.

Active DAG: `normative_graph/dag_v0.3.62_sp16_mech2_load_cases_applicability_census.json` — **821 quantities / 39 datasets / 702 nodes / 1190 edges**.

Presentation policy: `data/sp16_mech2_presentation_policy.json`.

`ENGINEERING_USE_READY = False` remains unchanged.

---

# SP16 / SP554 cumulative package — FIRE-UI2.4 FIRE-VAL1 routing remediation

This cumulative release is **`v0.57_fire_ui24_fire_val1_routing_remediation_r1`**, built over v0.56 FIRE-UI2.3.

FIRE-UI2.4 remediates routing defects discovered by the first FIRE-VAL1 headless guided-DAG campaign. The normative formula set is not broadened here; the release repairs guided reachability, removes unsupported dead selector outcomes, and ensures branch-specific source inputs are authored before their consumers execute.

## FIRE-UI2.4 closure

- compression with `software_static_stress` now resolves the required stability `gamma_e` path before critical-temperature inversion;
- strength-only static-stress branches continue into their critical-temperature inversion instead of terminating at `SP554_C_CTRL_STRENGTH_ONLY`;
- unsupported `gamma_c = other` selector outcomes are removed rather than exposed as dead choices;
- unsupported Table-7 stability-curve `other` is likewise removed; only source-traced `a/b/c` remain selectable;
- when local stress is selected, concentrated local force `F` is explicitly authored before SP16 Eq. (47);
- diagnostic compression-control relations no longer hijack the guided production continuation;
- internal provenance object `SP554_FIRE_D4_I_REQUIRED_R_PROVENANCE` remains excluded from guided engineering authoring;
- FIRE-VAL1 rerun over 500 unique routing states reports **0 unexpected blocked frontiers**, down from 46 in the initial campaign window;
- all 18 curated seed routes terminate in their expected result class without branch failures;
- `Qy` and general torsion `T` remain locked to zero in the primary UI and fail closed externally; no `Qy -> Qz` or `T -> B` substitution is introduced.

- DAG: `normative_graph/dag_v0.3.60_fire_ui24_fire_val1_routing_remediation.json` — **801 quantities / 39 datasets / 689 nodes / 1174 edges**.
- Presentation policy: `data/fire_ui24_presentation_policy.json`.
- Parent: `v0.56_fire_ui23_protection_route_closure_r1`.
- `ENGINEERING_USE_READY = False` remains unchanged.

---

# SP16 / SP554 cumulative package — FIRE-UI2.3 fire-protection route closure

This cumulative release is **`v0.56_fire_ui23_protection_route_closure_r1`**, built over v0.55.1 FIRE-UI2.2.1.

FIRE-UI2.3 closes the fire-protection source-selection and protected-member execution route discovered during live walkthroughs. It separates generic calculation materials from concrete commercial products, removes raw-object authoring from STO ARSS/manual routes, and makes SP554 12.5 execution reachable through an explicit 12.6 validation gate.

## FIRE-UI2.3 closure

- after selecting fire-protection design, the first choice is now **STO ARSS library / manual thermal properties / concrete product with documented matrix**;
- commercial product metadata (`product_id`, fire-hazard class, operating conditions, service life, conformity) is requested only for a concrete documented product;
- STO ARSS and manual-property routes never ask the engineer to type `protection_performance_dataset_raw`;
- the STO ARSS library includes cement-sand plaster, dry gypsum plaster, cellular/foam concrete and mineral-wool boards; active mineral-wool density is fixed to **100 kg/m3** while the source range **80–100 kg/m3** remains in provenance;
- temperature-dependent STO ARSS properties preserve their kelvin basis and are transformed exactly for the internal Celsius solver;
- STO ARSS/manual routes pass through an explicit SP554 12.6 validation gate before protected-member calculation;
- given-thickness checks execute the protected 1D SP554 12.5 model directly and return `Rprotected`;
- minimum-thickness searches are bounded by engineer-supplied limits, forbid extrapolation beyond the upper bound, and fail closed on non-monotonic response;
- concrete-product matrices use a specialized structured matrix editor rather than generic JSON/text input;
- legacy normalization edges that could activate `SP554_C_12_7_9_NORMALIZE_PERFORMANCE_DATASET` before a real product matrix existed are removed;
- `Qy` and general torsion `T` remain locked to zero in the primary UI and fail closed externally.

Parent: `v0.55.1_fire_ui22_result_continuation_hotfix_r1`.

---

# SP16 / SP554 cumulative package — FIRE-UI2.2 routing continuity + fire-protection material library

This cumulative release is **`v0.55_fire_ui22_routing_protection_library_hotfix_r1`**, built over the verified v0.54 FIRE-UI2.1 selector-hardening baseline.

FIRE-UI2.2 repairs guided-routing discontinuities found in live engineering walkthroughs and opens an explicit post-result route from the calculated unprotected fire resistance into fire-protection design. It also adds a source-traced STO ARSS 11251254.001-018-03 thermal-property library plus manual material-property authoring for the SP554 clause 12.5 model.

## FIRE-UI2.2 closure

- closes `BLOCKED_NO_NAVIGATION_EDGE:SP554_C_GAMMAE_OUTPUT` by continuing a calculated `gamma_e` result into the critical-temperature/thermal handoff route;
- restores the incoming SP16 9.2.3 and 9.2.6 decision-first navigation edges accidentally lost during FIRE-UI2.0 restructuring;
- binds branch-specific 9.2.3 producers so `M_11_3` is materialized from the selected signed design moment instead of being requested as a missing external value;
- after `Rfact` without protection is calculated, the engineer can now choose to check `Rreq`, continue directly to fire-protection design, or finish the unprotected calculation; a successful unprotected compliance result can still continue to protection by explicit choice;
- adds a STO ARSS material library and a manual-property route for `rho`, moisture, emissivity, `A/B/C/D`, with the coefficient temperature basis retained explicitly;
- for **mineral-wool boards**, the active library density is fixed to **100 kg/m3** by project decision, while the source-table range **80-100 kg/m3** is retained in provenance;
- STO ARSS source coefficients are stored literally against kelvin temperature (`t >= 273 K`); the Celsius-state SP554 solver applies an exact intercept shift rather than silently using the wrong temperature scale;
- the primary UI continues to lock unsupported `Qy` and torsion `T` at zero; external nonzero values remain fail-closed and are never substituted by `Qz` or bimoment `B`.
- direct SP554 12.10 calculation of a **given protection thickness no longer requests `Rreq`**; `Rreq` is requested only for inverse minimum-thickness sizing or an explicit compliance check;
- after protected `Rfact` is calculated, the engineer may finish with the calculated result or explicitly request an `Rreq` compliance check;
- all nontrivial expression-helper calls in the active guided graph are now covered by an explicit production binding or the restricted declarative whitelist; unpromoted 12.4/12.5 matrix-generation routes fail with a specific diagnostic instead of `unsupported expression helper`;
- the remaining weakening UI island (`SP554_D_NET_PROPERTY_REDUCTION`) is now connected by real DAG edges rather than presentation-only overrides;

### Fire-protection material library

The source-traced library contains four rows from the supplied STO ARSS table:

```text
cement-sand plaster               rho = 1930 kg/m3
dry gypsum plaster                rho =  900 kg/m3
cellular / foam concrete          rho =  600 kg/m3
mineral-wool boards               rho =  100 kg/m3  [source range 80-100]
```

Each row carries moisture, emissivity and the printed linear laws `lambda(t)=A+B*t` and `c(t)=C+D*t`. The source-table capture and an implementation note are retained in `docs/source_evidence/` and `docs/STO_ARSS_PROTECTION_MATERIAL_LIBRARY.md`.

### Important scope boundary

The material library supplies intrinsic thermal properties; it does **not** invent SP554 clause 12.6 validation evidence for a generated fire-protection performance dataset. Existing 12.6 validation gates therefore remain mandatory and fail-closed. General axis-specific `Qy` mechanics and general torsion `T` also remain open scope. Consequently `ENGINEERING_USE_READY = False` remains unchanged.

- DAG: `normative_graph/dag_v0.3.58_fire_ui22_routing_protection_library_hotfix.json` — **797 quantities / 39 datasets / 685 nodes / 1160 edges**.
- Presentation policy: `data/fire_ui22_presentation_policy.json`.
- Parent: `v0.54_fire_ui21_selector_hardening_qy_t_lock_r1`.

## Previous FIRE-UI2.1 baseline (retained cumulative context)

# SP16 / SP554 cumulative package — FIRE-UI2.1 selector hardening + Qy/T UI lock

This cumulative release is **`v0.54_fire_ui21_selector_hardening_qy_t_lock_r1`**, built over the verified v0.53 FIRE-UI2.0 conditional-moment/thermal-binding baseline.

FIRE-UI2.1 closes the blank-selector defect globally rather than patching only the two reported booleans. Every boolean exposed by the generic guided UI receives explicit `Да/Нет` choices in the generated contract, every generic enum/decision selector is audited for a non-empty option set, and contract creation fails closed if a future selector has no choices. Because the general `Qy` and torsion `T` mechanics remain unclosed, the primary signed-load UI now shows those two fields locked at zero; imported/non-UI nonzero values remain fail-closed and are never remapped to `Qz` or `B`.

## FIRE-UI2.1 selector hardening closure

This release repairs the guided-calculation defects found during the v0.52 engineering walkthrough:

- boolean quantities now render as **Да/Нет** selectors rather than raw text fields;
- the internal `beam_ltb_context` object is removed from engineering authoring; dedicated SP16 selectors remain authoritative;
- SP16 **9.2.3** asks for the normative case first and then requests only the signed moments required by that branch; raw `sp16_moment_distribution` and the seven-field moment-summary screen are removed;
- SP16 **9.2.6** asks for the restraint case first and then requests only the two signed moments required by that branch; `M_x_c_signed` is derived from the determining source moment and is never asked again;
- the invariant is explicit: **moments are entered with sign; absolute value is only a normative comparison operation and never overwrites the source quantity**;
- Table 21 uses a dedicated explanatory selector instead of four bare `Тип 1…4` labels;
- the generic “Механическая проверка неполная” terminal now reports the actual deferred load components and why they remain fail-closed;
- the previously unbound production nodes `GOST30247_C_FORMULA1_STANDARD_FIRE_CURVE`, `SP554_C_FIG1_UNPROTECTED_INTERPOLATION`, and `SP554_C_UNPROTECTED_STEP_12_1_12_4` are now registered against the verified thermal core.

Important scope statement: **Qy and torsion T remain normatively unimplemented in v0.54.** The primary browser UI therefore locks both inputs to zero. External/non-UI nonzero values still activate the explicit fail-closed guard; there is no Qy→Qz or T→B substitution.

- DAG: `normative_graph/dag_v0.3.57_fire_ui21_selector_hardening_qy_t_lock.json` — **783 quantities / 38 datasets / 675 nodes / 1142 edges**.
- Presentation policy: `data/fire_ui21_presentation_policy.json`.
- Parent: `v0.53_fire_ui20_conditional_signed_moments_thermal_bindings_r1`.
- `ENGINEERING_USE_READY = False` remains unchanged.

## Previous FIRE-UI1.9 baseline (retained cumulative context)

### FIRE-UI1.9 SP554 Table-1 heated-perimeter matrix

Retained from **`v0.52_fire_ui19_sp554_table1_heated_perimeter_matrix_r1`**.

## FIRE-UI1.9 heated-perimeter closure

The Section-12 guided route now separates two engineering choices that were previously mixed into one technical enum:

1. **heated sides**: three sides or four sides;
2. **fire-protection geometry**: protection following the steel contour or protection formed as a rectangular box.

For supported Table-1 section families the heated perimeter is calculated automatically and stored together with an explicit normative trace. Unsupported geometry never falls back to a guessed bounding rectangle: the route requests a manually established heated perimeter and remains traceable.

For an I-section with overall width `B`, depth `D` and web thickness `t`, the current Table-1 matrix is:

```text
steel contour / contour fire protection, 4 sides: P = 4B + 2D - 2t
steel contour / contour fire protection, 3 sides: P = 3B + 2D - 2t
box fire protection, 4 sides:                  P = 2B + 2D
box fire protection, 3 sides:                  P = B + 2D
```

The protected route uses separate quantities `P_heated_protected` and `delta_pr_protected`; a box-protection calculation can therefore never silently reuse the steel-contour `A/P`. This separation is propagated into protected Section-12 calculations and Annex-A schedule outputs.

Regression case `20К1` (`B=199 mm`, `D=196 mm`, `t=6.5 mm`, `A=5269 mm²`) gives:

```text
contour / unprotected, 4 sides: P = 1.175 m, delta_pr = 4.4843 mm
contour, 3 sides:               P = 0.976 m
box, 4 sides:                   P = 0.790 m, delta_pr = 6.6696 mm
box, 3 sides:                   P = 0.591 m
```

- DAG: `normative_graph/dag_v0.3.55_fire_ui19_sp554_table1_heated_perimeter_matrix.json` — **783 quantities / 38 datasets / 672 nodes / 1143 edges**.
- Presentation policy: `data/fire_ui19_presentation_policy.json`.
- Parent: `v0.51_fire_ui18_fire_d2_to_d3_handoff_hotfix_r1`.
- `ENGINEERING_USE_READY = False` remains unchanged.

## Previous FIRE-UI1.8 baseline (retained cumulative context)

### FIRE-UI1.8 exact critical-temperature thermal handoff hotfix

Retained cumulative context from **`v0.51_fire_ui18_fire_d2_to_d3_handoff_hotfix_r1`**:

## FIRE-UI1.8 hotfix

The release closes the guided transition defect discovered after a valid FIRE-D2 critical temperature had been calculated. An exact mechanical critical-temperature result is now a **stage result**, not the end of the complete fire-resistance calculation.

For `fire_d2_critical_temperature_status = COMPLETE` the guided route is now explicit:

```text
FIRE-D2 critical-temperature result
    -> FIRE-D3 exact Tcr handoff
    -> Section 12
    -> Схема обогрева
```

The handoff copies the exact temperature into both `critical_temperature_c` and `fire_d3_critical_temperature_handoff_c`. A dedicated executor is used because the frozen FIRE-D3 handoff node has two trace outputs.

The scheduler also keeps the mechanical-to-thermal barrier: if another mechanical branch is still pending, the thermal handoff is queued and executes only after the mechanical frontier is empty.

Fail-closed behavior is retained:

- `AMBIENT_CAPACITY_EXCEEDED` does **not** enter Section 12;
- `INCOMPLETE_FAIL_CLOSED` (`Tcr > published Tmax` without an exact Tcr) does **not** fabricate an exact thermal target;
- no Appendix-B extrapolation is introduced.

Regression coverage includes the reported exact result **`tcr = 638.011628 °C`**, which must continue to the interactive Section-12 screen **`Схема обогрева`** with the same exact temperature in the FIRE-D3 ledger.

- DAG: `normative_graph/dag_v0.3.54_fire_ui18_fire_d2_to_d3_handoff_hotfix.json` — **777 quantities / 38 datasets / 666 nodes / 1136 edges**.
- Presentation policy: `data/fire_ui18_presentation_policy.json`.
- Parent: `v0.50_fire_ui17_critical_temperature_restraint_ux_hotfix_r1`.

## Previous FIRE-UI1.7 baseline (retained cumulative context)


- `γT` and `γe` are no longer collapsed to one coefficient before Appendix-B inversion. Each applicable curve is inverted independently; the earliest exact critical temperature governs.
- `γ > 1` returns `AMBIENT_CAPACITY_EXCEEDED` at 20 °C and never calls a forbidden lookup.
- A coefficient below the published minimum returns `Tcr > Tmax` as a relational lower bound; no extrapolation is fabricated. If the competing branch has an exact lower temperature, that exact branch governs.
- The legacy `γctrl` / single inverse-domain nodes remain in the frozen graph for source trace only and are excluded from guided production routing.
- SP16 Table 30 choices now show readable restraint names and μ for common S1-S4 cases; S5-S8 explicitly state that the normative load diagram must also be matched.
- SP16 Table 7 choices now show a/b/c coefficients and a schematic redraw with the table-note reminder for rolled I-sections above 500 mm.


## v0.49 FIRE-UI1.6 scope

- One signed local-load editor accepts `N`, `My`, `Mz`, `Qy`, `Qz`, and torsion `T`; `N > 0` is tension and `N < 0` is compression.
- The load classifier creates a traceable `verification_plan` containing the applicable axial, bending, biaxial, shear, interaction and deferred torsion branches instead of asking the engineer to select one stress-state label manually.
- Parallel normative branches are retained in an active queue. Completing one branch no longer terminates the guided session while other required branches remain pending.
- Missing quantities are resolved by producer call/return: the consumer is suspended, the applicable producer is executed, and control returns to the suspended branch rather than following the producer's ordinary downstream UI route.
- Queued nodes re-check applicability before execution, completed nodes are not re-executed, ambiguous producers fail closed, and transition to the thermal stage is blocked until the mechanical queue is closed.
- Frozen `calculation_spec`, `lookup_spec`, classification and check specifications can execute through the restricted declarative runtime; arbitrary Python `eval` is not used.
- Section weakening is generalized for the current temporary model: a round bolt hole first gives `A_n = A - d*t_h` for any section whose local intersected thickness can be resolved or explicitly supplied.
- After the area reduction, the engineer explicitly chooses whether to keep gross `I/W/Wpl` values or supply independently calculated net values. Manual net `Ixn`, `Iyn`, `Wxn,min`, `Wyn,min`, `Wpl,x,n`, and `Wpl,y,n` become effective downstream quantities.
- SP16 formula (45) remains a separate shear-hole route with the normative condition `s > d`; no longitudinal-pitch reinterpretation is introduced.
- Supported signed-load qualification covers tension, compression, `My`, `Mz`, biaxial bending, `Qz`, `M+Q`, compression+bending, tension+bending, and a general `N+My+Mz+Qz` case.
- `Qy` and pure torsion `T` are currently explicit fail-closed deferred verification branches; the runtime does not invent a resultant or substitute bimoment mechanics.
- FIRE-D2 critical-temperature inversion remains no-extrapolation. Compression is qualified with an in-domain case retaining independent `gamma_T(T)` and `gamma_E(T)` inversions.
- DAG: `normative_graph/dag_v0.3.53_fire_ui17_critical_temperature_restraint_ux_hotfix.json` — **777 quantities / 38 datasets / 666 nodes / 1135 edges**.
- `ENGINEERING_USE_READY = False` remains unchanged; deferred load branches, remaining external normative-reference boundaries, original product-standard audit of the interim profile catalog, and final engineering certification are still open.

## Qualification policy

A route is not accepted merely because the UI reaches another screen. Supported mechanical cases must terminate at a normative mechanical result or the mechanical-to-thermal boundary with:

```text
pending branches = 0
branch_failures = []
```

Unsupported cases must terminate explicitly as fail-closed/deferred results. A calculation leaf cannot silently become `SESSION_COMPLETE` while required branches remain unresolved.

## Run

```bash
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python main.py
```

---

# SP16 / SP554 cumulative package — FIRE-UI1.5 weakening continuation hotfix

This cumulative release is **`v0.48_fire_ui15_weakening_continuation_hotfix_r1`**, built over the verified v0.47 FIRE-UI1.4 weakening baseline. It fixes guided-session continuation after the weakening step: derived net/alpha producers are auto-executed and the questionnaire continues to the next engineering question instead of terminating or exposing a non-interactive producer as a form.

## v0.48 FIRE-UI1.5 scope

- Fixes premature guided-session termination immediately after the section-weakening stage.
- The derived nodes `SP554_G_NET_SECTION_PROPERTIES`, `SP16_C_SHEAR_ALPHA_IDENTITY_WEAK` and `SP16_C_SHEAR_ALPHA45` remain non-interactive producers and are never shown as user forms.
- After either `alpha = 1` (no wall holes) or SP16 8.2.1 formula (45), the sequential presentation route continues to `SP554_D_GOST27751_GAMMA_CT` and then to the load/special-combination stage.
- The no-hole identity route is explicitly qualified for any section family with resolved positive gross `A`, `Ix`, `Iy`, and elastic moduli; it is not restricted to doubly symmetric I-sections.
- The existing *hole-present* analytical subtraction remains intentionally restricted to the FIRE-UI1.4 doubly symmetric I-section central-web-hole model.
- Adds an 18-profile catalog-tee regression sweep for no-hole identity and an end-to-end tee walkthrough regression.
- Adds a frontend in-flight submit guard so repeated click/Enter events cannot race a derived non-interactive producer.
- No SP16/SP554 equation or applicability rule is changed by this hotfix; it is a guided-state/presentation correction.
- `ENGINEERING_USE_READY = False` remains unchanged because full SP16 → FIRE-D4 guided executor binding is not yet closed.

## v0.47 FIRE-UI1.4 scope

- Fixes object-valued single-output submission: a node with one `produces` binding now treats the submitted JSON object as that quantity value; the legacy wrapped `{quantity_id: value}` form remains accepted.
- The ordinary weakening editor now contains only **no holes / bolted holes**, with user inputs `d` and `s`. Cut-outs, arbitrary holes, zone selectors, hole count and user-authored active-section IDs are removed from the primary UI.
- `SP16_D_WEAKENING` is now a derived calculation, so the wizard no longer asks a second “weakening present?” question after the editor.
- The supported net-section route is intentionally narrow: a doubly symmetric I-section web with one representative active transverse-section round hole centred on the centroidal axes.
- In the transverse section the through-hole removes a rectangular area `d·t_w` rather than the circular face area `πd²/4`; the central location permits direct subtraction of the local rectangle second moments without a Steiner shift.
- SP16 8.2.1 formula (45) is implemented with its normative semantics: `alpha = s/(s-d)`, where `s` is the pitch of holes in one vertical row; `s > d` is enforced fail-closed.
- No-hole input resolves net properties by identity and `alpha = 1`.
- Flange holes, arbitrary cut-outs, multiple active holes, staggered net paths and general perforated-section geometry remain unsupported and fail closed.
- The presentation policy and UI contract are updated to DAG `v0.3.50`; stale v0.3.46/v0.3.49 graph-title provenance is removed.
- Full arbitrary weakening geometry and full SP16 → FIRE-D4 guided executor closure are not claimed; `ENGINEERING_USE_READY = False`.

## Run

```bash
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python main.py
```

---

# SP16 / SP554 cumulative package — FIRE-UI1.3 material / strength editor

This cumulative release is **`v0.46_fire_ui13_material_strength_editor_r1`**, built over the verified v0.45 FIRE-UI1.2 section-model executor-binding baseline. It closes the material-selection blocker encountered immediately after catalog/parametric section definition and replaces raw DAG inputs with one compact engineering editor.

## v0.46 FIRE-UI1.3 scope

- `SP554_I_STEEL_GRADE` and `SP554_I_STEEL_PRODUCT_DATA` remain available in the normative DAG for traceability but are hidden from the ordinary wizard.
- The primary wizard uses one **Material / Strength Editor** containing product form, steel grade and an exact printed thickness interval.
- Product form selects the materialized current-SP16 route automatically: Table В.3, В.4 or В.5.
- Steel grade is a dropdown populated from the applicable materialized table; free-text grade entry is removed from the ordinary route.
- Governing thickness is selected as an exact printed interval (`до ...`, `св. ... до ... включ.`), with no interpolation or extrapolation.
- Catalog/parametric section geometry supplies safe suggestions for product form and exact thickness where those values are directly known; the engineer still sees and confirms the selection.
- `steel_delivery_standard` is removed from required primary UI because it was a required-but-unused selector for the materialized Annex В tables. It remains provenance metadata only where an external material route genuinely needs it.
- Exact Annex В lookup now materializes `Ryn`, `Run`, tabulated `Ry` and `Ru` and continues the sequential guided route instead of blocking.
- A read-only `Rs*` preview is explicitly labelled as `0.58·Ry(tabulated)` only; authoritative production `Rs` remains a Table 2 calculation requiring explicit `gamma_m`.
- V.4 steel grades with the `Б` suffix are normalized correctly for the SP554 steel-strength-group continuation.
- Section-editor improvements from v0.45 remain retained: real 37-family / 4069-row profile catalog, shape-specific previews, shape-dependent parametric fields, double-branch v1 editor, and manual arbitrary-section properties.
- Full SP16 → FIRE-D4 executor binding is still not claimed; `ENGINEERING_USE_READY = False`.

## Run

```bash
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python main.py
```

---

# SP554 ↔ SP16 traceable Python package — FIRE-UI1 SP554 Applicability Routing Hotfix r1

This cumulative release is **`v0.43.2_fire_ui1_sp554_applicability_routing_hotfix_r1`**, built over v0.43.1. It closes applicability-routing defects found during the full-DAG/UI audit without changing the closed Annex D.3 interpolation policy.

## v0.43.2 hotfix scope

- SP554 (10.6)/(10.7): fail-closed class/material gate — ordinary I-beam class 1 or bisteel I-beam class 2; pipes/non-I sections are rejected.
- SP554 11.7: `SP16 Table 21 section type 3` is separated from `NDS section class 3` and from buckling-curve type `a/b/c`.
- SP554 (11.1): explicit N+M stress-state applicability.
- SP554 (11.2): explicit compression+bending, `m_eff <= 20`, constant-section and symmetry-plane gates.
- The same checks are enforced in direct `fire_sp554_runtime`, not only in the DAG/UI.
- Existing FIRE-D2 governing-temperature reconciliation is retained unchanged.
- Full engineering-questionnaire decomposition remains FIRE-UI1.1/UI2 scope; `ENGINEERING_USE_READY = False`.

---

# SP554 ↔ SP16 traceable Python package — FIRE-UI1 Guided Wizard + Live Calculation Ledger Frontend r1

This cumulative release is **`v0.43_fire_ui1_guided_wizard_live_calculation_ledger_frontend_r1`**, built over the frozen v0.42 FIRE-UI0 architecture baseline. FIRE-UI1 materializes the first local browser interface for sequential DAG-driven fire-resistance acceptance testing.

## FIRE-UI1 closure scope

- Local-only browser application served on `127.0.0.1`; no public server or Streamlit dependency is required.
- Guided question cards, dropdowns, boolean decision cards, numeric/text inputs and external-standard provenance are rendered from the FIRE-UI0 contract.
- The right-side live ledger updates after every accepted answer/producer result and exposes value, unit, source and producer identity.
- `Назад` edits an earlier answer through deterministic replay; obsolete downstream values are invalidated rather than retained.
- Execution trace is visible as a separate right-panel tab.
- Calculation sessions can be exported/restored as DAG-ID + DAG-SHA locked JSON.
- TypeScript frontend contains no SP16/SP554 equations; calculation nodes still require explicit production executor bindings.
- Full SP16 → FIRE-D4 executor binding is intentionally deferred to FIRE-UI2.
- Bolts/connections, FIRE-D5 protection design and rendered reports remain outside UI1 scope.
- `ENGINEERING_USE_READY = False`.

Start on Windows with `START_FIRE_UI1.bat` or run `python fire_ui1_launch.py`. See `docs/fire_ui1_user_guide.md` and `docs/fire_ui1_frontend_architecture.md`.

---

# SP554 ↔ SP16 traceable Python package — FIRE-UI0 DAG-driven guided-calculation architecture r1

This cumulative release is **`v0.42_fire_ui0_dag_driven_guided_calculation_architecture_r1`**, built over the closed v0.41 FIRE-D4 baseline. FIRE-UI0 introduces the framework-independent application architecture for a NormCAD-style sequential fire-resistance calculator driven directly by the frozen SP16 ↔ SP554 DAG.

## FIRE-UI0 closure scope

- DAG `v0.3.44 FIRE-D4` is compiled into deterministic UI cards; no normative formulas are copied into frontend code.
- Guided session state machine follows only `control`, `branch`, and `handoff` edges; `data` edges feed calculations/ledger and never alter question order.
- User answers are validated against quantity type, enum values, units/source policy, and external-standard provenance requirements.
- Editing an earlier answer replays the valid history prefix and invalidates the abandoned downstream branch.
- A live right-side calculation ledger retains value, symbol, canonical unit, source kind, producer node, provenance, and normative references.
- Deterministic report-ready trace records every accepted answer/calculation and selected DAG edge.
- Calculation nodes are fail-closed unless an explicit production executor is registered; the UI layer never guesses or skips formulas.
- A reference integration adapter proves direct reuse of the frozen FIRE-D2 → FIRE-D3 → FIRE-D4 production runtimes.
- Full SP16 → FIRE-D4 question-to-executor binding, browser frontend, and rendered report remain deferred to FIRE-UI1/UI2/UI4.
- Bolts/connections remain outside the current UI scope.
- `ENGINEERING_USE_READY = False`.

See `docs/fire_ui0_architecture.md` and `reports/fire_ui0_architecture_closure.md`.

# SP554 ↔ SP16 traceable Python package — FIRE-D4 Section 13 result assessment runtime r1

This cumulative release is **`v0.41_fire_d4_sp554_section13_result_assessment_runtime_r1`**, built over v0.40 FIRE-D3.1. FIRE-D4 closes the executable SP554 Section 13 result-assessment layer over the frozen FIRE-D2 critical-temperature and FIRE-D3 thermal producers.

## FIRE-D4 closure scope

- Section 13.1: critical temperature is preserved as the mechanical result from FIRE-D2.
- Section 13.2: actual fire resistance is the valid FIRE-D3 time to the critical temperature.
- Section 13.3: exact `R + time` notation is produced for the standard fire with **no nearest-class rounding** and independently of PASS/FAIL.
- Compliance is evaluated on unrounded values: `R_fact >= R_req`.
- `R_req` is an explicit external normative/project requirement and must carry provenance matching the supplied value; FIRE-D4 does not derive it from building classification.
- Section 13.4 protected thermal results can be materialized as fire-protection-efficiency indicator records without creating a product-certification claim.
- Failure of an unprotected member routes to `FIRE_PROTECTION_DESIGN_REQUIRED`; failure of an already protected member routes to `FIRE_PROTECTION_REDESIGN_REQUIRED`.
- Alternative/real fire regimes remain fail-closed pending FIRE-D7.
- `ENGINEERING_USE_READY = False`.

See `reports/fire_d4_closure_report.md`.

# SP554 ↔ SP16 traceable Python package — FIRE-D3.1 Section 12 full-scope reconciliation r1

This cumulative release is **`v0.40_fire_d31_sp554_section12_full_scope_reconciliation_r1`**, built over the v0.39 FIRE-D3 thermal runtime. FIRE-D3.1 reconciles the full SP554 Section 12 scope against enacted **СП 554.1311500.2026** while preserving the frozen SP16/FIRE-D1/FIRE-D2/FIRE-D3 producers.

## FIRE-D3.1 closure scope

- Enacted SP554 designation/effectivity reconciled: `СП 554.1311500.2026`, effective `2026-09-01`.
- Exact local equation provenance remains the locked pre-enactment DOCX, SHA-256 `86a3c010ee74e469670f7aff5b95c807ffcff81bc81cbebe16f994af477507e3`.
- Formula (12.8) fictitious-temperature scalar is executable and auditable.
- `W>0` is supported only through explicit `moisture_accounting_mode=embedded_in_thermal_properties` with confirmation that moisture behavior is already embedded in experimentally identified/nonlinear thermal properties; separate `t_phi` subtraction is then prohibited to prevent double counting.
- Literal repeated `t_phi` recurrence remains fail-closed because no moisture-depletion state/evolution law is defined that makes repeated subtraction invariant to numerical time-step refinement.
- SP554 12.6 ±20% validation remains mandatory for 12.5 protected-FDM performance.
- New DAG: `normative_graph/dag_v0.3.43_fire_d31.json` (743 quantities / 651 nodes / 1100 edges / 38 datasets).
- Full **reconciliation** is closed; full literal Section-12 runtime closure remains explicitly false.
- `ENGINEERING_USE_READY = False`.

See `reports/fire_d31_section12_full_scope_reconciliation.md` for the normative reconciliation dossier.

# SP554 ↔ SP16 traceable Python package — FIRE-D2 critical-temperature runtime r1

This cumulative release is **`v0.38_fire_d2_sp554_critical_temperature_runtime_r1`**, built over the closed v0.37 FIRE-D1 baseline. FIRE-D2 executes the SP554 Sections 8–11 member fire-mechanical routes over frozen SP16 producers and performs Appendix-B critical-temperature inversion. N1–N10 and FIRE-D1 remain frozen cumulative dependencies. SP554 Section 12 thermal calculation and connection fire resistance are outside FIRE-D2.

## FIRE-D2 closure scope

- Locked SP554 source: `СП Стальные 27.05_0 (1) (1).docx`, SHA-256 `86a3c010ee74e469670f7aff5b95c807ffcff81bc81cbebe16f994af477507e3`.
- Locked current SP16 source: `СП 16.13330.doc`, SHA-256 `302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873`.
- Runtime action: `sp554_fire_mechanical_guided`.
- Executed member scope: SP554 Sections 8–11, including central tension/compression, bending/shear, lateral stability, `N+M`, biaxial/box routes, static-stress route 8.7 and Appendix-B inversion.
- Governing production policy: independently invert every applicable reduction-factor demand on its own Appendix-B curve, then select the minimum critical temperature. For multiple strength checks on one decreasing `gamma_T(T)` curve this is equivalent to `max(required gamma_T)`.
- Locked-draft clauses 8.6, 10.3 and 11.9 are retained as source-literal diagnostic provenance but are not executed where their literal minimum-coefficient wording would select a later, non-governing temperature.
- Appendix-B digital policy: exact Table-B.1 knots; linear interpolation only along the published curve segments; no extrapolation; qualification gates for high-strength and fire-resistant groups are explicit.
- Current graph: `normative_graph/dag_v0.3.41_fire_d2.json` with **737 quantities / 643 nodes / 1088 edges / 38 datasets**.
- FIRE-D2 focused runtime+DAG: **32/32 PASS**.
- FIRE-D2 source regression: **876/876 pre-manifest + 1/1 manifest = 877/877 PASS**.
- `engineering_use_ready = false`; SP554 Section 12 thermal calculation, connection fire resistance, full package-wide Change-6 rebaseline, original/effective GOST profile audit, and final external engineering certification remain open.

# SP554 ↔ SP16 traceable Python package — FIRE-D1 member mechanical dependency closure r1

This cumulative release is **`v0.37_fire_d1_sp554_sp16_mechanical_dependency_closure_r1`**, built over the closed v0.36 Stage N10 baseline. FIRE-D1 freezes the current-SP16 N1–N7 member-mechanics producers used by SP554 Sections 8–11 and audits the fire-specific normative-strength basis. N1–N10 remain frozen cumulative dependencies. Connection fire resistance and SP554 thermal Section 12 are explicitly outside FIRE-D1.

## FIRE-D1 closure scope

- Locked SP554 source: `СП Стальные 27.05_0 (1) (1).docx`, SHA-256 `86a3c010ee74e469670f7aff5b95c807ffcff81bc81cbebe16f994af477507e3`.
- Locked current SP16 source: `СП 16.13330.doc`, SHA-256 `302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873`.
- Audited SP554 mechanical scope: Sections 8–11, member mechanics only.
- Current graph: `normative_graph/dag_v0.3.40_fire_d1.json`.
- Bridge action: `sp554_sp16_fire_dependency_bridge`.
- SP16 fire dependencies: N1 material, N2 section, N3 axial, N4 bending/Annex Ж, N5 beam-column, N6 detailed built-up/box support, N7 effective length.
- Fire basis guard: direct use of ordinary SP16 design `Ry/Ru/Rs` quantities in SP554 Sections 8–11 is prohibited; SP554 clauses 8.2–8.3 use normative strength characteristics.
- FIRE-D1 does **not** execute SP554 formulas 8.1–11.10 or Appendix B inversion; that is the next FIRE-D2 runtime stage.
- Fire resistance of joints remains deferred until the relevant connection scope is qualified; thermal Section 12 is a separate later stage.
- FIRE-D1 source regression: **844/844 pre-manifest + 1/1 manifest = 845/845 PASS**; fresh-extraction qualification is the final packaging gate.

This cumulative release is **`v0.36_stage_n10_brittle_fracture_current_sp16_closed_reconstructed_r1`**, built over the closed v0.35 Stage N9 baseline. Stage N10 closes the current-SP16 Section 13 selected-route layer for brittle-fracture prevention and lamellar-tearing risk: clauses 13.1-13.5, equation (174), and Table 37. N1-N9 are frozen dependencies. Historical NormCAD remains secondary evidence only.

## Stage N10 brittle-fracture closure scope

- New `brittle_fracture_guided` action performs one complete Section-13 review rather than accepting a partial checklist as sufficient.
- Clause 13.1 is rebased to the **four** factor groups printed by the current consolidated source; legacy extra top-level factor categories are removed from the current route.
- Clause 13.2 conditionally enforces steel-selection confirmation, the strict `sigma_t > 0.4Ry` enhanced-NDT trigger, weld-intersection avoidance, run-off tabs/NDT, concentration/work-hardening mitigation, the 25 mm cover-plate flank-weld termination boundary, and the guillotine/punching and secondary-gusset requirements when applicable.
- Clause 13.3 applicability is an explicit engineering-review gate; a positive conservative screen cannot be silently suppressed.
- Clause 13.4 requires explicit through-thickness tensile-test / certified Z-quality evidence before the lamellar-tearing route can close.
- Equation (174) uses the five printed Table-37 factors. The 0.5 static through-thickness compression and 1.1 dynamic/vibratory modifiers are explicit current-clause rules.
- Z15/Z25/Z35 selection is checked twice: the selected group must meet the minimum clause-13.5 route, and the adjusted `psi_zr <= psi_zn` numerical condition must independently pass.
- Table 37 is materialized without invented interpolation. Connection geometry, NDT records and product certificates are never inferred from CAD/BIM or naming.
- DAG: `normative_graph/dag_v0.3.39_stage_n10.json` with **729 quantities / 635 nodes / 1072 edges / 36 datasets**.
- `engineering_use_ready = false`; full package-wide Change-6 rebaseline, original/effective GOST profile audit, and final external engineering certification remain deferred final gates.

## Stage N9 fatigue closure scope

- New `fatigue_guided` action selects exactly one route: ordinary fatigue under 12.1.2, crane-runway fatigue under 12.2, or the current low-cycle boundary for `n < 1e5`.
- Clause 12.1.3 is treated as **excluded by Change No. 6 from 10.01.2025**. The retained compatibility function name does not reactivate it.
- Ordinary fatigue uses Annex K Table K.1 detail group, Table 35 `Rv`, equations (171)/(172) or the printed `alpha=0.77` high-cycle branch, Table 36 `gamma_v`, equation (170), and the mandatory `alpha*Rv*gamma_v <= Ru/gamma_u` condition.
- Table 35 uses exact printed Run bins with no interpolation or extrapolation; groups 1-2 above `Run=675 N/mm2` fail closed.
- Table 36 is evaluated by its printed piecewise analytic expressions; `rho=sigma_min/sigma_max` retains stress sign.
- Clause 12.2 overrides alpha with `0.77` for group 8K and metallurgical 7K cranes, otherwise `1.1`.
- Equation (173) for the upper web zone of built-up crane-runway beams runs only when equation-(67) stress provenance is explicitly confirmed and the printed welded/friction + compression/tension resistance route is selected.
- SP 20.13330 load derivation, stress-history extraction, rainflow/cumulative damage, automatic Annex-K geometry recognition, and a current low-cycle-fatigue method remain explicit external/fail-closed boundaries.
- DAG: `normative_graph/dag_v0.3.38_stage_n9.json` with **714 quantities / 629 nodes / 1066 edges / 34 datasets**.
- `engineering_use_ready = false`; full package-wide Change-6 rebaseline, original/effective GOST profile audit, and final external engineering certification remain deferred final gates.

## Stage N8 sheet-structure closure scope

- New `sheet_structure_guided` action selects one route across clauses 11.1-11.2 instead of evaluating unrelated cylinder, sphere, cone, panel and tube cases together.
- Equations (148)-(169) reuse the existing audited scalar producers with current Change-6 source provenance.
- Table 34 is exact-grid only: printed `r/t` nodes map to printed `c`; non-node values require an explicit external `c` plus provenance. No hidden interpolation or extrapolation is introduced.
- Clause 11.2.3 retains the explicitly printed linear interpolation for `0.8Ry < sigma < Ry`; clause 11.2.4 retains the printed interpolation for `10 < l/r < 20`. These rules are not generalized to Table 34.
- Clause 11.1.4 local edge effects and clause 11.1.5 arbitrary/spatial analysis fail closed until the required analysis/certified-software confirmations are explicit.
- Clause 11.2.2 distinguishes the global Sections 7/9 route, equation (156) direct tube route, and outside-direct-route cases without fabricating missing critical-stress data.
- Ring-stiffened cylinders require actual ring effective area, radius of gyration and Table-7 section type; the ring is checked as a compressed member with `N=prs`, `lef=1.8r`, conditional relative slenderness `<=6.5`, and one-sided inertia-axis confirmation where applicable.
- DAG: `normative_graph/dag_v0.3.37_stage_n8.json` with **702 quantities / 624 nodes / 1060 edges / 30 datasets**.
- `engineering_use_ready = false`; full package-wide Change-6 rebaseline, original/effective GOST profile audit, and final external engineering certification remain deferred final gates.

## Stage N7 effective-length + limiting-slenderness closure scope

- New `effective_length_guided` action selects exactly one Section-10 route instead of evaluating unrelated alternatives in one demo calculation.
- Equations (136)-(139) and Tables 24-29 are exposed through applicability-specific truss, built-up branch and spatial-member routes.
- Equation (138) uses the current printed lower bound `lef >= 0.6l`; equation (139) uses `lef,1 >= 0.5l1`.
- Table 29 performs linear interpolation only for the explicitly printed interval `2 <= n <= 6`; no other hidden interpolation is introduced.
- Column/frame routes cover equation (140), Table 30, Table 31 / equations (141)-(145), equation (146), and the deformation reduction of equation (147).
- Equation (141) follows official FAU FCS clarification letter No. Исх-8076 dated 10.11.2023: `mu = 2*sqrt(1 + 0.38/n)`.
- Clause 10.3.2 requires same-load-combination confirmation for frame effective-length routing; equation (146) is permitted only from the printed equation-(141)/(142) base routes.
- Clause 10.3.5 `H/B >= 6` activates an explicit whole-frame global-stability obligation.
- Clause 10.3.7 stepped-column, clause 10.1.3 special crossing-brace, and clause 10.3.11 certified-software routes fail closed unless explicit external provenance/assumptions are supplied.
- Clause 10.3.9 supports either direct restraint spacing or an externally analysed effective length with provenance. Clause 10.3.10 additionally requires confirmation of global support stability as a built-up cantilever.
- Tables 32 and 33 provide the selected limiting-slenderness route, including the Table-32 `alpha >= 0.5` rule, group-4 +10% allowance, and printed Table-33 notes.
- DAG: `normative_graph/dag_v0.3.36_stage_n7.json` with **694 quantities / 618 nodes / 1054 edges / 29 datasets**.
- `engineering_use_ready = false`; full package-wide Change-6 rebaseline, original/effective GOST profile audit, and final external engineering certification remain deferred final gates.

## Stage N6 built-up beam-column + combined local-stability closure scope

- Clauses **9.3-9.4** are exposed through `built_up_beam_column_guided`.
- Whole-member free-axis stability uses selected Table 8 `lambda_ef`, current `Ry/E`, equation (123), and exact printed nodes of Table D.4.
- `m > 20` routes the whole-member check to Section 8; no continuation through D.4 is invented.
- Branch additional-force routing follows 9.3.3; equation (124) is used only for the printed type-2 biaxial case. Unsupported type-1/type-3 biaxial combinations fail closed unless an external producer with provenance is supplied.
- Individual lattice branches are checked by equation (7) with their own central-compression coefficient; the conditional 7.2.5 extended-slenderness permission is a separate explicit dependency.
- Clause 9.3.7 uses `max(Q, Qfic)` and enforces the lattice requirement when actual shear governs.
- Tables 22 and 23 retain the standard's explicit interpolation rules; Table D.4 deliberately has `interpolation.method = none`.
- Clauses 9.4.4 and 9.4.5 verify provided transverse/longitudinal stiffener geometry and inertia rather than returning requirements only.
- Clause 9.4.6 reduced-area use is fail-closed until the required member-stability recheck is explicitly performed.
- DAG: `normative_graph/dag_v0.3.35_stage_n6.json`.

## Stage N5 beam-column closure scope

- New `beam_column_guided` action hydrates explicit N1 material and N2 profile references before strict schema validation and composes only already-audited Section 9 primitives.
- Section 9.1 strength selects equation (105) only when its applicability gates pass; otherwise equation (106) is required and fails closed until explicit governing-point data are supplied.
- Section 9.2 derives geometric and relative slenderness, central-compression `phi`, relative eccentricities, Annex D.2 `eta`, `m_eff`, and the applicable equation-(109)/(111)/(116)/(117) branches.
- Clause 9.2.9 keeps its independent additional equation-(109) trigger even when `m_eff,y > 20` suppresses equation (116).
- Annex D.3 is exact-grid only in production. Non-node values do **not** receive an invented bilinear interpolation; an externally resolved `phi_e` is accepted only with explicit provenance and `0 < phi_e <= phi`.
- The qualified example is constructed on an exact D.3 node: `lambda_bar_x=1.5`, `m_eff,x=1.0`, `phi_e=0.593`.
- Current C255B-1 production hydration resolves `Ryn=245 MPa`, `Ry=240 MPa`, `E=206000 MPa`, `G=79000 MPa`; historical NormCAD `255/250/210000/78500` values are retained as evidence and never override current-SP16 material data.
- Historical NormCAD `lefy=2.95 mm` is preserved as a source anomaly without silent repair; its old 15K4 `It=385333 mm4` is not used where the current Annex-D policy resolves `497080 mm4`.
- Box and built-up beam-columns are routed to the retained `beam_column_stability` and `built_up_beam_columns_and_combined_local_stability` detailed actions.
- Atomic DAG is advanced to `dag_v0.3.34_stage_n5.json` with **665 quantities / 598 nodes / 1039 edges**; parent D.3 lookup nodes retain `interpolation.method = none`.
- Stage N5 discrepancy register contains **7 classified items / 0 unresolved in declared scope**.
- `engineering_use_ready = false`; full package-wide Change-6 rebaseline, original/effective GOST profile audit, and final external engineering certification remain deferred final gates.

## Stage N4 bending-member closure scope

- New `bending_member_guided` action accepts explicit N1 material and N2 profile references and hydrates them before strict action-schema validation, with provenance retained in `resolution_trace`.
- Ordinary class-1 strength routes to equations (41)/(42), with equation (43) activated only when its required point/sectorial data are explicit.
- Class-2/3 ordinary beams route to equations (50)/(51)/(53) only after explicit 8.2.3 applicability inputs; crane-runway and bimetal cases are routed to their dedicated detailed actions.
- Equation (61) now evaluates `c_xr=(alpha_f*r+0.25-0.0833/r^2)/(alpha_f+0.167)`; the obsolete legacy `c_xf` call parameter is retained only for backward API compatibility and has no mathematical effect.
- Lateral stability has explicit modes: 8.4.4(a) rigid-deck exemption, 8.4.4(b)/Table-11 exemption, current-SP16 Annex Ж calculation, or separate assessment.
- The direct current-SP16 Annex Ж nodes use **design `Ry`**, not `Ryn`. The mixed historical DAG's `Ryn` nodes are retained only for the separate SP554 transformed invocation context.
- For supported doubly symmetric rolled-I profiles, the guided path computes current Annex Ж alpha/psi/phi1/phi_b and equation (69).
- Local stability computes the 8.5.1 web-slenderness screen and 8.5.9 transverse-stiffener screen; it deliberately reports `SCREEN_ONLY_FULL_8_5_INTERACTION_REMAINS_SEPARATE` instead of silently treating the whole 8.5 route as passed.
- Static NormCAD comparison confirms a historical equation-(92) denominator mismatch (`lambda_a` vs current `lambda_a^2`); this behavior is classified but not imported.
- Atomic DAG is advanced to `dag_v0.3.33_stage_n4.json`.
- `engineering_use_ready = false`; full package-wide Change-6 rebaseline and final original-GOST profile audit remain final release gates.


## Stage N3 axial-member closure scope

- Guided solid-member route derives the equation-(5) resistance branch from force state, `Ryn=440` boundary and the explicit post-yield-service condition.
- Compression route computes `lambda=l_eff/i`, current-SP16 `lambda_bar=lambda*sqrt(Ry/E)`, Table-7 `alpha/beta`, equations (8)-(9), equation (7), and optional rolled-I equation (7a).
- Current consolidated-source `gamma_res` rules are transcribed literally, including the printed `0.2*lambda_bar+0.9` branch for `Ry=390 MPa` above `lambda_bar=5`; intermediate `Ry` is linearly interpolated as the clause states.
- Built-up-member workflow selects exactly one Table-8 equation (12)-(17) for members with at least six panels; below six panels the route is redirected/fail-closed according to 7.2.2/7.2.5 rather than silently using Table 8.
- Branch slenderness limits, the 2.7/3.2 interpolation route, close-contact 40i/80i checks, Qfic equation (18), and connector-force equations are preserved in the guided trace.
- Historical NormCAD is retained as secondary evidence. Its static SP16 module lacks the current equation-(7a) route, and the inspected equation-(14) line is classified as a historical formula divergence.
- A current-source text-vs-Annex-D.1 exact-boundary ambiguity for the phi cap at 3.8/4.4/5.8 is explicitly recorded rather than silently resolved.
- `engineering_use_ready = false`; full package-wide Change-6 rebaseline and final original-GOST profile audit remain release gates.

## Stage N2 runtime integration scope

- Interim profile catalog: **4069 profiles / 37 families** imported with frozen historical-source provenance.
- Existing calculation routes can resolve a `profile_ref` and receive compatible section-derived inputs before schema validation.
- Runtime mass is recomputed from area at 7850 kg/m3; radii are recomputed as `sqrt(I/A)`.
- Known corrupt/sentinel historical NormCAD mass, `afw` and `It` values are not used as runtime truth.
- Current SP16 Table 7 coefficients are centralized as `a=(0.03,0.06)`, `b=(0.04,0.09)`, `c=(0.04,0.14)` with the corresponding phi-cap slenderness thresholds 3.8/4.4/5.8.
- Rolled doubly symmetric I-sections route x-axis stability to type `b`, with the Table 7 Note 1 override to type `a` for `h>500 mm`; y-axis routing is type `c`.
- CHS/RHS/SHS use type `a`; channels and tees use type `c`; imported angle and legacy cold-formed C/Z family routing is retained explicitly in the family registry and remains auditable.
- Supported I/T/channel torsion quantities are recomputed with the current-SP16 Annex D `I_t=(k/3)Σ(b_i t_i^3)` route rather than trusting historical NormCAD `It`.
- Duplicate profile designations fail closed unless `source_row_id` is supplied.
- **Original/effective GOST profile-table verification is intentionally deferred to the final package profile audit.**
- `engineering_use_ready = false` remains unchanged.

## Stage N1 validation/remediation scope

- User validation corpus: **9 registered cases** under `validation/cases/`.
- Original uploaded source files are preserved byte-for-byte where they were supplied as files; chat-pasted reports are explicitly stored as transcriptions rather than mislabeled as originals.
- Dedicated Phase 0.26 remediation regression gate: **12/12 PASS** before release packaging.
- Legacy validation/self-check corpus retained: **1876/1876 PASS**.
- Phase 0.23 independent route evidence retained.
- Phase 0.24 + 0.25 independent direct function oracles retained: **60/581** engineering functions.
- External vendor-published SCAD/KRISTALL comparator cases retained: **6/6 PASS across 5 production functions**.
- Engineering public call surface remains **581 functions**; Phase 0.26 changes behavior in corrected normative branches without intentionally changing engineering invocation signatures.
- Annex Б.1 and Annex В.3/В.4/В.5 are now source-backed machine-readable data; **20** other Annex Б/В/Г/И tables remain explicit `external_reference_required` boundaries.

## Retained v0.26 findings and Stage N1 changes

The cumulative remediation includes:

1. Table 8 equations (12)-(14): removed an erroneous square on the `(1+n)`-type connection factors.
2. Clause 7.1.3: restored `phi=1` for section types `a/b` when relative slenderness is below 0.6, including values below the first printed D.1 node.
3. Annex D.2 Type 5 branch: corrected coefficient `0.012` to `0.02` for the validated branch.
4. Clause 14.1.8: corrected the weld-consumable upper bound to `Rwz*beta_z/beta_f`.
5. Clause 14.1.9: legacy one-sided-weld API now fails closed when the full current applicability conditions are not represented by its inputs.
6. Table 40: staggered longitudinal minimum spacing is now included in the final layout pass/fail result when staggered evidence is supplied.
7. Clause 14.2.14: bolt-count increases use exact integer arithmetic, eliminating binary-float `ceil` off-by-one errors.
8. Equation (44) runner: bolt-hole factor is applied to shear stress before recomputing the complete equivalent-stress check.
9. Clauses 8.4.4/8.4.6 runner: the class 2/3 reduction factor is applied to the governing limiting flange slenderness before the exemption decision when that route is active.
10. Clause 9.2.9 runner: `m_eff,y>20` no longer erases independent x-plane additional-check triggers; Annex D.3 is not called unconditionally for an inapplicable plane.

## Stage N1 closure evidence

- Current-SP source-vs-package checks: **7/7 PASS_EXACT**.
- В.3/В.4/В.5 rows: **95/95 PASS_EXACT**.
- Exhaustive source-derived boundary matrix: **981 probes** = 866 exact resolutions + 115 required fail-closed outcomes.
- NormCAD static strength rows decoded: **62 / 72 / 6** in the sheet / shaped / tube databases.
- NormCAD row-level crosswalk: **111** current grade/range comparisons.
- N1 discrepancy register: **19 classified, 0 unresolved**.
- Exact NormCAD runtime/UI selection at ambiguous old boundary labels is not claimed; this is preserved as historical-oracle evidence, not used as normative truth.

## Still-open validation boundaries

- Annex D.3 arbitrary-point interpolation policy is not promoted to normative production behavior because the standard does not explicitly prescribe a general bilinear interpolation rule; external comparator behavior is retained as evidence only.
- Several user reports contain source-side inconsistencies, outdated resistance tables, incomplete applicability data, or non-normative routing. These cases remain `PARTIAL` rather than being promoted to end-to-end golden references.
- Stage N1 material/strength data are rederived from **СП 16.13330.2017 with Changes No. 1–6 through 09.12.2024**, but this release **does not claim a complete package-wide Change 6 rebaseline**.
- `engineering_use_ready = false` remains unchanged.

## Run

```bash
PYTHONPATH=. python -m pytest -q
PYTHONPATH=. python main.py
```

## Qualification

`engineering_use_ready = false`. Stage N1 Material/Strength, Stage N2 runtime profile integration, Stage N3 axial members, Stage N4 bending members, Stage N5 beam-column runtime/DAG routing, Stage N6 built-up beam-column/local-stability routing, Stage N7 effective-length/limiting-slenderness routing, Stage N8 sheet-structure routing, Stage N9 fatigue routing, and Stage N10 brittle-fracture routing are closed in their declared scopes against the current SP16 source. The profile catalog is **not yet source-certified against every original/effective GOST**; that final profile audit is an explicit deferred release gate. The complete SP16 package is still not fully Change-6-rebaselined or externally certified. Subsequent stages must treat N1-N10 as frozen dependencies unless a source-backed remediation is explicitly opened.

## FIRE-UI1.2 changes

- profile-catalog geometry producer is now bound end-to-end; selecting a catalog profile continues to material selection rather than `BLOCKED_EXECUTOR_REQUIRED:SP554_G_CATALOG`;
- catalog preview uses shape-specific SVG sketches for I/RHS/CHS/channel/angle/tee/Z/C families;
- parametric section editor requests only dimensions relevant to the selected shape;
- two-branch editor v1 composes two identical catalog branches by the parallel-axis theorem; lattice/batten mechanics remain downstream SP16 questions;
- arbitrary section route is manual-properties-only; 2D contour authoring was removed by user decision;
- geometry providers continue explicitly to the steel-material block after successful materialization.

## v0.58 / SP16-MECH1 — Canonical Axes + Mechanical State Contract

Parent: `v0.57_fire_ui24_fire_val1_routing_remediation_r1`.

Primary guided action notation is now `N, Mx, My, Qx, Qy, T`, where `x-x` and `y-y` are the SP16 principal section axes and `s` is the member longitudinal axis. The v0.57 migration is explicit and sign-preserving: `old My→Mx`, `old Mz→My`, `old Qz→Qx`, `old Qy→Qy`. `T` is no longer described as `Mx`.

Bimoment `B` is not a permanent load-menu field. The guided flow asks whether `B` is required; if yes, it is entered directly (signed), and if no, an explicit `B=0` producer is recorded. v0.58 does not infer `B` from `T` and does not implement restrained-torsion analysis. `Qy` and `T` remain fail-closed until their later SP16-MECH stages.
