# Extraction notes — v0.8_bending_member_local_stability

## Scope

This release preserves v0.2-v0.7 and adds visually verified content from the supplied consolidated СП 16.13330.2017 PDF:

- pages 36-38: clauses 8.5.1-8.5.4, equations (78)-(84), Tables 12-13, and Figure 8;
- pages 39-41: clauses 8.5.5-8.5.8, equations (85)-(88), and Tables 14-18;
- pages 42-44: clauses 8.5.9-8.5.13, equations (89)-(96), and Figures 9-10;
- pages 45-47: clauses 8.5.14-8.5.20, Table 19, Figure 11, and equations (97)-(100).

## Visual-verification decisions

### Stress and panel equations

- Equations (78)-(100) were read from rendered page images and registered individually.
- Signed normal stresses are preserved where the printed interaction depends on stress sign; shear demands are handled by magnitude unless a formula explicitly contains a signed term.
- Equation (87) is implemented as a scalar capacity expression. It does not silently impose unstated stress caps.
- Equation (88) rejects states where `R_yw²-3tau²` is non-positive.

### Tables 14-18

- Every printed cell was transcribed into `data/tables_14_to_19_bending_local_stability.json`.
- Lookup is exact-node only. The standard does not state interpolation for these tables, so none is invented.
- Table 16 uses the Table 12 value at or below the printed lower boundary and the printed terminal value at or above the upper boundary, following clause 8.5.5.

### Table 19

- Transverse-stiffener minimum inertia and all printed longitudinal-stiffener required/minimum/maximum expressions were transcribed.
- Linear interpolation is used only for the required longitudinal-stiffener inertia at intermediate `h1/h_ef`, because the table note explicitly requires it.
- No upper/lower-limit expression is invented where the printed table contains a dash.

### Clause-specific routing

- Clause 8.5.1 distinguishes the three printed preliminary thresholds and rejects the unlisted one-sided-weld/local-stress combination.
- Clause 8.5.5 returns one or two explicit check routes rather than hiding substitutions.
- Clause 8.5.6 returns the `2h_c` replacement explicitly.
- Clause 8.5.13 substitutes intermediate spacing only for plate 1.
- Clause 8.5.14 uses the printed asymmetric-section stress substitutions with signed opposite-edge stress.
- Clause 8.5.16 is classified as an implemented routing decision to an external flexible-web method, not as implementation of that external method.
- Clause 8.5.17 separates effective support-stiffener section rules from the end bearing/compression selection.
- Clause 8.5.20 applies the 1.5 multiplier only when both printed geometry conditions pass.

## Validation interpretation

The v0.8 validation set adds representative equation/procedure checks and exhaustive comparisons for every transcribed value in Tables 14-18. Table 19 is checked at printed nodes and an interpolation point. These checks validate transcription and internal consistency; they are not independent worked examples or experimental validation.

## Copyright handling

Only identifiers, concise descriptions, coefficients, formulas, and traceability metadata required for implementation are included. Large passages of the standard are not reproduced.

## v0.9 visual extraction notes

- Equations (101)-(104) were transcribed from PDF page 47.
- Equations (105)-(108) and their sign/applicability text were transcribed from PDF page 48.
- Table E.2 was transcribed from PDF page 163, including all printed nodes and the terminal `>2` columns.
- Table E.2 contains no interpolation instruction. The implementation therefore accepts exact printed nodes and the terminal inequality column only.
- Clause 8.6.1 gives a foundation-strength requirement but no foundation calculation model. It is preserved as an explicit external boundary.
- Equation (106) printed plus/minus alternatives are implemented with signed actions, coordinates, and sectorial coordinate, followed by an absolute stress utilization.
- Clause 9.1.2 is implemented with the printed `m_eff <= 20` condition without reinterpretation.

## v0.10 visual extraction notes

- Section 9.2 equations (109)-(122), Tables 20-21, and routing text were visually verified on PDF pages 48-53.
- Annex D Tables D.2-D.6 and equations (D.1), (D.2), and (D.4) were visually verified on PDF pages 151-160.
- Tables D.3-D.5 were transcribed as exact printed nodes. No interpolation rule is stated, so interpolation and extrapolation are rejected.
- Table D.3 and D.4 lookup helpers expose the printed value and a separate capped value using the central-compression coefficient.
- Table D.5 preserves the printed `2.55` cell at `delta=0`, `lambda=1`, `m_eff,1=4`; no editorial correction is made.
- Table D.6 type 5 is retained as an excluded amendment record rather than an active calculation row.
- Table 21 type 4 retains the printed `I2/I1 < 0.5` beta override.
- Clause 9.2.9 additional checks are emitted as explicit flags; they are not silently absorbed into equation (116).

These checks validate transcription and internal consistency only. They are not independent worked examples or experimental validation.

## v0.11 visual extraction notes

- Section 9.3 and Section 9.4 were visually verified on PDF pages 53-58.
- Equation (123) and the four unnumbered branch-force expressions in 9.3.3 were transcribed with explicit geometry selectors; equation (124) is retained as the biaxial type-2 expression.
- Clauses 9.3.4-9.3.7 are implemented as explicit routing and demand-selection procedures. The package does not replace the external frame/branch analysis, Section 16 calculation, or connector resistance design.
- Equations (125)-(130), Table 22 section types, applicability domains, upper bounds, and all four table notes were transcribed. Linear interpolation is applied only in the intervals explicitly required by Notes 1, 2, and 4.
- Equation (131) is implemented only for the printed axial-stability-utilization interval; the below-0.8 branch returns the Table-22 type-2 limit as prescribed.
- Clauses 9.4.4-9.4.6 expose transverse-stiffener, longitudinal-stiffener, and reduced-area requirements without inventing missing geometry or connection calculations.
- Equations (132)-(135), Table 23 section types, the `m_x=5...20` interpolation note, and the `0.8...4.0` slenderness clipping note were transcribed explicitly.
- Clause 9.4.9 uses the minimum of the stability coefficients used in the member check and caps the resulting multiplier at 1.25.
- Clause 9.4.10 is represented as a route to the bending-member local-stability procedure when compressive stresses occur in an eccentrically tensioned member.
- No complete numerical worked example was identified in these clauses. Validation cases therefore check formula transcription, table-note routing, limits, signs, and boundary behavior rather than claiming normative example reproduction.

Only concise formulas, identifiers, coefficients, and traceability metadata needed for implementation are included; extended copyrighted passages are not reproduced.


## v0.12 visual extraction notes

- Section 10 was visually verified on PDF pages 58-72.
- Equations (136)-(147) were transcribed as separate scalar functions with explicit domain checks.
- Tables 24-33 were encoded as auditable data and routing rules; diagram classification remains an explicit engineering input.
- Tension forces in equation (137) follow the printed negative-sign instruction.
- Minimum effective-length bounds in equations (136)-(139) are applied after evaluating the primary expression.
- Table 29 interpolation is applied only in the interval and variable explicitly stated by the table note.
- Table 31 special cases are represented separately from the general frame equations so that no diagram assumption is hidden.
- Clauses 10.3.5, 10.3.7, 10.3.11 and the external elastic-restraint reference are retained as explicit external or routing boundaries rather than reconstructed from unstated theory.
- Table 32 Group 4 increase and Table 33 notes are handled as explicit procedure inputs.
- No complete numerical worked example was identified in Section 10. Validation therefore checks formula transcription, exact table routing, limits, and boundary behavior.

Only concise formulas, identifiers, coefficients, and traceability metadata needed for implementation are included; extended copyrighted passages are not reproduced.

## v0.13 visual extraction notes

- Section 11 was visually verified on PDF pages 72-77 of the supplied consolidated standard.
- Equations (148)-(169), Table 34, and all associated routing provisions were transcribed from rendered pages rather than reconstructed from OCR fragments alone.
- Table 34 contains nine printed nodes: `r/t = 100, 200, 300, 400, 600, 800, 1000, 1500, 2500`; no interpolation instruction is stated.
- Equation (164) is implemented with the printed coefficient `6.28`.
- Linear interpolation is used only where Section 11 explicitly prescribes it: the cylindrical-panel transition and the external-pressure transition for `10 < l/r < 20`.
- No complete numerical worked example was identified in Section 11. Validation therefore checks transcription, exact table nodes, formula domains, routing, and limiting behavior.

## v0.14_fatigue_design

Section 12, equations (170)-(173), Tables 35-36, and Annex K Table K.1 were visually audited on PDF pages 77-79 and 177-181. Table K.1 is diagram-driven and uses explicit stable case identifiers; no automatic detail recognition or unstated interpolation is applied.

## v0.15 visual extraction notes

- Section 13 and clause 14.1 were visually verified on PDF pages 79-90.
- Equation (174), Table 37, its signed factors, Z15/Z25/Z35 thresholds, and the static-compression/dynamic-action modifiers were transcribed explicitly.
- Tables 38 and 39 were encoded from the printed bins. The gaps in printed weld-leg/thickness bins are routed to calculation or rejection; they are not silently interpolated.
- Equations (175)-(185) were implemented as separate functions with explicit N-mm-N/mm2 conventions and algebraic stress-component handling.
- Clauses without a complete calculation model are represented as evidence/checklist or external-reference routes rather than reconstructed from general welding theory.
- No complete numerical worked example was identified in Sections 13 or 14.1. Validation therefore checks transcription, exact table values, signs, limits, and routing.

Only concise formulas, identifiers, coefficients, and traceability metadata required for implementation are included; extended copyrighted passages are not reproduced.


## v0.16 extraction notes

Pages 90-96 were rendered at 300 dpi. Equations (186)-(192) were verified from the embedded formula images. Tables 40-42 were transcribed visually, including the Table 42 clearance/load routes and the 0.9 nut-rotation multiplier. The two-variable Table 41 interpolation path is not uniquely stated; the API therefore requires an explicit verified interpolation fraction for intermediate geometry.

## v0.17 extraction notes

- Clause 14.4 was visually verified on PDF pages 96–97.
- Equations (193)–(198), the four rows of Table 43, and the definitions of `T`, `V`, `n`, `Q_bh`, `k`, `s`, and `alpha` were transcribed from rendered page images.
- The stationary upper-flange load without a transverse stiffener and every stationary lower-flange load are routed to the moving-load formulas exactly as stated above Table 43.
- The coefficient `alpha` is `0.4` only for load on the upper flange with the web edge planed to that flange; otherwise it is `1.0`.
- The full-web-thickness penetration statement is retained as a classification/evidence route, not as automatic proof of weld execution.
- Clause 14.4.2 is represented by the printed half/full sheet-section force rule around theoretical and actual cut-offs. Cut-off locations and sheet section capacity remain external verified inputs.
- No complete numerical worked example was identified in clause 14.4. Validation therefore checks formula transcription, route selection, boundaries, and internal consistency.

## v0.18 extraction notes

- Table 44 was visually verified on PDF pages 97–98; clauses 15.12.1–15.12.3 and equations (199)–(200) were visually verified on page 108.
- Table 44 contains eight printed rows. The `t ≥ -45 °C` branch includes equality; no interpolation is stated.
- The statement concerning an exceedance of more than 5% is represented as a trigger for a climatic-temperature analysis including inelastic deformations and joint flexibility. It is not treated as a 5% compliance allowance.
- The Table 44 note for two vertical-bracing systems is encoded as 50/40 m for buildings and 30/25 m for open trestles, using the smaller value below `-45 °C`.
- Clause 15.12.1 gives friction coefficients `0.3` for flat movable supports and `0.03` for roller supports.
- Equation (199) is transcribed as `F/(1.25*r*l*R_lp*gamma_c) ≤ 1` and is gated by the printed central contact-angle condition of at least 90°.
- Equation (200) is transcribed as `F/(n*d*l*R_cd*gamma_c) ≤ 1`; no additional load-distribution factor is introduced.
- Eighty Section 15 clause records were classified by software execution route. This catalogue does not claim numerical implementation of every detailing requirement.
- No complete numerical worked example was identified in the selected clauses. Validation therefore checks transcription, exact table values, boundaries, and routing.

## v0.19 extraction notes

- Section 16 was visually audited on PDF pages 108–115.
- The audited Section 16 scope is equations (201)–(214) and Tables 45–46. Equations (215)–(224) and Table 47 are in Section 17; Table 48 is in Section 18.
- Table 45 contains eight categorical coefficients and expressly excludes node connections.
- Table 46 contains eight rows; numerical cells are denominators of relative limits `1/n`. Emergency and erection exclusions and stricter equipment requirements are preserved as explicit routes.
- Equations (201)–(203) define maximum slenderness for four-sided, three-sided, and pyramidal lattice members.
- Equations (204)–(208) retain the printed coefficients `3.46`, `3`, `3.14`, `1.16`, and `0.58`.
- Equations (209)–(212) use the printed domains, the `lambda_bar <= 3.5` cap, and the 5% modifier for a brace bolt-line ratio of exactly `0.50`.
- Equations (213)–(214) retain the `lambda_w_bar <= 2.4` cap and signed `sigma_2`.
- No complete numerical normative example was identified; validation therefore checks transcription, exact table values, domains, routing, and limiting behavior.

## v0.20 extraction notes

- Section 17 was visually audited on PDF pages 115–118.
- The audited Section 17 scope contains equation (215), Table 47, and clauses 17.1–17.18. Equations (216)–(224) and Table 48 belong to Section 18 and were not pulled into this release.
- Table 47 contains 13 categorical working-condition factors. No interpolation or automatic combination of rows is stated.
- Clause 17.2 rope requirements are implemented as selection constraints and evidence routes; no commercial rope catalogue is reconstructed.
- Equation (215) is transcribed as `s >= 0.41e-3*d*sqrt(P/m)` with `d` in mm, `P` in N, `m` in kg/m, and `s` in m.
- Clauses concerning test evidence, obstruction marking, lighting, galvanizing, fabrication, and erection are represented as explicit evidence checks rather than assumed compliance.
- No complete numerical normative example was identified in Section 17. Validation therefore checks transcription, exact Table 47 values, domains, boundaries, and procedure routing.

## v0.21 extraction notes

- Section 18 was visually audited on PDF pages 118–125.
- Technical-condition categories and evidence requirements in clauses 18.1–18.2 are implemented as explicit decision/evidence routes rather than inferred compliance.
- Table 48 contains seven printed resistance rows: three shear values, two head-tension values, and two bearing expressions. The countersunk/semi-countersunk 0.8 reduction and tension prohibition are retained.
- Equations (216)–(224) were transcribed from rendered pages. The printed `gamma_N`, `gamma_M`, `gamma_c <= 0.9`, and section-property definitions are explicit.
- Equation (222) retains the printed `V = 0.04 k_f^2` convention with `k_f` in centimetres. Figure 24 `n_i` values are not digitized or interpolated and must be supplied explicitly.
- The beneficial welding-deflection factor `k_fw = 0.5` is applied only when the welding deflection has the opposite sign and reduces the absolute equivalent eccentricity; otherwise `k_fw = 1`.
- Clause 18.3.11 is represented by an explicit common-versus-separate resistance route; the 15% comparison is documented as a conservative comparison to the lower value.
- No complete numerical normative example was identified in Section 18. Validation therefore checks formula transcription, exact Table 48 values, signs, domains, boundaries, and procedure routing.

Only concise formulas, identifiers, coefficients, and traceability metadata required for implementation are included; extended copyrighted passages are not reproduced.
