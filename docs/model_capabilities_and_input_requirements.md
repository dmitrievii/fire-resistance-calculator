# Model capabilities and input requirements

## 1. Available calculation routes

- `material_resistance_bundle`: selected Section 6 material and connection resistances.
- `axial_member_strength_and_stability`: clauses 7.1.1-7.1.3 and Annex D Table D.1.
- `built_up_axial_members`: clauses 7.2.1-7.2.10 and Table 8.
- `centrally_compressed_local_stability`: clauses 7.3.1-7.3.11 and Tables 9-10.
- `bending_member_strength`: clauses 8.1-8.2.8, equations (41)-(62), Table 10a, and Table E.1.
- `crane_runway_and_bending_stability`: clauses 8.3-8.4.6, equations (63)-(77), Table 11, and Annex Ж.
- `bending_member_local_stability`: clauses 8.5.1-8.5.20, equations (78)-(100), and Tables 12-19.
- `base_plates_and_combined_force_strength`: clause 8.6 and Section 9.1, equations (101)-(108), and Table E.2.
- `beam_column_stability`: Section 9.2, equations (109)-(122), Tables 20-21, and Annex D Tables D.2-D.6.
- `built_up_beam_columns_and_combined_local_stability`: Sections 9.3-9.4, equations (123)-(135), and Tables 22-23.
- `effective_lengths_and_limiting_slenderness`: Section 10, equations (136)-(147), and Tables 24-33.
- `sheet_structures_strength_and_stability`: Section 11, equations (148)-(169), and Table 34.

## 2. Results available from the v0.13 route

The Section 11 runner returns:

- equation (148) membrane-strength utilization and principal-stress resistance checks;
- equations (149)-(153) membrane stresses for general shells of revolution and standard cylindrical, spherical, and conical cases;
- Table 34 cylindrical axial critical-stress bundle and equation (154) utilization;
- eccentric-compression adjustment diagnostics and equation (156) tube local-stability utilization;
- cylindrical-panel limit and panel/shell routing diagnostics;
- equations (159)-(162) external-pressure and combined cylindrical-shell checks;
- ring-stiffener force and effective geometry requirements;
- equations (163)-(168) conical-shell stability values;
- equation (169) spherical-shell external-pressure utilization;
- explicit routes requiring local edge-effect or certified spatial analysis.

## 3. Required input data

The route requires, as applicable:

- verified membrane stresses or shell pressure and geometry;
- shell radii, thickness, length or height, and cone half-angle;
- design yield, tension, and compression resistances and elastic modulus;
- axial force, relative slenderness, area, and relative eccentricity for tube checks;
- explicit axial critical stress when the relevant `r/t` is not a printed Table 34 node;
- panel width, compressive stress, external pressure, and ring spacing;
- explicit confirmation of discontinuities or arbitrary spatial behavior for external-analysis routing.

No implicit unit conversion, geometry recognition, load generation, or unstated interpolation is applied.

## 4. Not yet implemented

- automatic shell geometry and stress-resultant extraction;
- local edge-effect analysis at geometry, thickness, or load discontinuities;
- arbitrary-shell finite-element analysis and software certification checks;
- complete ring-stiffener cross-section and connection design;
- global member stability outside the scalar Section 11 formulas;
- remaining sections, annexes, and unresolved tables shown in the final audit.

## 5. Validation available

The validation report contains **1,669** arithmetic, boundary, sign, routing, and table-transcription checks. It includes direct checks for equations (148)-(169), every printed node of Table 34, and all previously implemented exhaustive table checks.

No complete numerical worked example was identified in Section 11; none was invented.

## v0.15 brittle-fracture and welded connections

Implemented Section 12 equations (170)-(173), Tables 35-36, and Annex K Table K.1 with explicit cycle counts, signed stress extrema, fatigue group, steel resistance, and crane-runway inputs. SP 20.13330 load derivation, variable-amplitude damage accumulation, low-cycle fatigue, and automatic detail recognition remain external.

## v0.15 model: brittle fracture and welded connections

**Available results:** lamellar-tearing risk and Z-quality comparison; minimum/maximum weld geometry routes; butt-weld and fillet-weld utilizations; combined shear resultants; arc spot-weld capacities.

**Required inputs:** explicit normative detail classifications, plate and weld dimensions, verified material/weld resistances, working-condition factors, and design forces/moments/stress components.

**Not implemented:** automatic steel selection, test-certificate verification, CAD detail recognition, welding-procedure qualification, Sections 14.2-14.4, and independent fracture-mechanics analysis.

**Validation:** equation self-checks for (174)-(185), exact lookups for Tables 37-39, boundary/sign tests, and all prior release validations.


## v0.16 bolted and friction connections

Clauses 14.2-14.3, equations (186)-(192), and Tables 40-42 are implemented with explicit units, applicability checks, table routes, tests, and validation self-checks. Product standards, anchor-bolt design, installation evidence, and global force derivation remain external.

## v0.17 built-up beam flange connections

**Available route:** `built_up_beam_flange_connections` implements clause 14.4, equations (193)–(198), Table 43, the shear-flow and local-pressure definitions, the stationary-to-moving load routing, the coefficient `alpha`, the full-penetration classification, and clause 14.4.2 multilayer-sheet attachment force.

**Returned results:** `T`, `V`, the effective Table 43 route, `alpha`, utilizations for all six numbered equations, the governing utilization for the active route, the full-penetration status, and the required flange-sheet attachment force.

**Required inputs:** verified beam actions and gross section properties; concentrated-load data and `l_ef`; load/stiffener/flange/planing classification; weld coefficients and resistances; bolt pitch, friction-plane capacity and count; and multilayer flange-sheet section capacity and cut-off segment.

**External boundaries:** global analysis, load-combination generation, automatic geometry recognition, stiffener design, weld/NDT qualification, individual bolt layout, and theoretical/actual sheet cut-off determination.

**Validation:** 11 new equation, procedure, routing, and Table 43 self-checks are included in the cumulative validation report.

## v0.18 structural detailing and support bearings

**Available route:** `structural_detailing_and_support_bearings` implements Table 44 lookup and compliance assessment, the paired-bracing note, support-bearing selection and friction coefficients, equation (199) for cylindrical hinges, equation (200) for rollers, and a clause-by-clause Section 15 routing catalogue.

**Returned results:** Table 44 limit and utilization; compliance and enhanced-analysis flags; paired-bracing limit; support type and friction coefficient; equation (199) and (200) utilization/capacity/pass results; and the 80-record Section 15 classification summary.

**Required inputs:** building category, direction, design air temperature, actual distances, stiffness flag, support-function flags, verified support force, contact angle, hinge or roller geometry, audited material resistances, roller count, and working-condition factor.

**External boundaries:** climatic-temperature load generation, nonlinear frame analysis, CAD/BIM classification, bearing product and anchorage design, contact mechanics, wear, track and substructure checks, fabrication evidence, and all non-numerical Section 15 drawing requirements.

**Validation:** 10 new Table 44, routing, friction, equation, boundary, and catalogue checks are included in the cumulative validation report.

## v0.19 overhead-line and switchyard supports

**Available route:** `overhead_line_and_switchyard_supports` implements Section 16 equations (201)–(214), Tables 45–46, and executable procedures from clauses 16.1–16.20.

**Returned results:** support-group route; Table 45 coefficient; slenderness and eccentricity values; guyed-support auxiliary values and amplified actions; biaxial additional chord force; angle-member factors; Table 46 deformation result; detailing checks; and polygonal-tube wall critical stress and utilization.

**Required inputs:** explicit support classification, connection and diagram categories, verified forces and moments, geometry, reduced slenderness, elastic modulus, Table 46 deformation ratio, diaphragm and splice data, polygonal-wall stresses, and working-condition factors.

**External boundaries:** load generation, combinations, global analysis, automatic geometry recognition, complete node and foundation design, erection evidence, and linked checks from other sections.

**Validation:** 30 new equation, table, boundary, and routing self-checks are included in the cumulative validation report.

## v0.20 antenna structures

**Available route:** `antenna_structures` implements Section 17 equation (215), Table 47, and executable or evidence-based procedures from clauses 17.1–17.18.

**External boundaries:** load generation and structural analysis, product selection, modal/aerodynamic analysis, fatigue qualification, fabrication and erection quality control, marking/lighting design, and automatic drawing interpretation.

## v0.21 reconstruction assessment

**Available route:** `reconstruction_assessment` implements Section 18 equations (216)–(224), Table 48, and executable or evidence-based procedures from clauses 18.1.1–18.3.16.

**Returned results:** technical-condition category; monitoring and calculation-exemption routes; material and test evidence; existing steel, weld, bolt, and rivet resistances; one-rivet capacity; strengthening and construction-stage evidence status; weld-heating stress limit; common/separate resistance route; `gamma_N`, `gamma_M`, equations (216)–(224); and acceptance of listed historical deviations.

**Required inputs:** explicit survey findings and confirmations; material provenance and test data; Table 48 classifications; actual forces, moments, stresses, section properties and stability coefficient; initial deformation and axial force; reinforcement properties; explicit Figure 24 `n_i` values; welding geometry and signs; construction-stage and deviation evidence.

**External boundaries:** physical survey and monitoring, material identification and laboratory testing, load generation and combinations, global and construction-stage analysis, governing-point search, Figure 24 interpretation, welding heat/residual-stress modelling, NDT, workmanship, and professional acceptance decisions.

**Validation:** 30 new equation, table, boundary, and procedure self-checks are included in the cumulative validation report.
