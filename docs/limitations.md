
## Stage N2 section/profile runtime limitations

- The 4069 profile rows / 37 families are imported from the historical NormCAD MDB so existing calculation branches can operate now. They are **not yet verified row-by-row against the original/effective GOST/GOST R product standards**.
- `engineering_use_ready` remains false; original/effective product-standard reconciliation is a mandatory final-package release gate.
- Catalog `A`, `Ix`, `Iy`, `W` and `S` are interim imported values with provenance. Mass and radii are recomputed; supported torsional quantities are recomputed by current-SP16 or explicit geometry identities/approximations.
- Sharp-corner geometry helpers do not manufacture rolled-profile fillet contributions and are not substitutes for certified catalog properties.
- Legacy open/closed thin-wall torsion approximations outside the direct current-SP16 Annex D I/T/channel route remain explicitly marked pending original-GOST audit.
- Table 7 family routing is centralized and auditable, but member-specific effective-length/radius rules (e.g. clauses 10.1/10.2 for single angles and lattice members) remain separate downstream applicability inputs.

# Limitations

## Phase 0.26 release qualification

- Engineering-use readiness remains **false**.
- The user validation corpus contains 9 cases, but none is automatically promoted to a complete end-to-end golden case when the source report itself is inconsistent or incomplete.
- Independent direct function-level evidence remains partial at 60/581 engineering functions.
- External vendor-published SCAD/KRISTALL evidence remains 6 scalar cases over 5 production functions; this is not a live vendor replay.
- Annex D.3 general interpolation is intentionally unresolved as a production policy because a general interpolation rule is not explicitly prescribed by the standard text.
- Twenty-four Annex Б/В/Г/И tables remain explicit external-reference boundaries.
- The Phase 0.26 corrections were checked against СП 16.13330.2017, Amendments No. 1-6, through 09.12.2024, but **no complete package-wide Amendment No. 6 delta rebaseline is claimed**.
- Coverage and regression pass counts are execution evidence, not proof of normative completeness.
- Global analysis, load combinations, geometry classification, inspections/NDT and professional acceptance remain external where required.
- Ordinary-temperature SP16 scope does not by itself replace fire/high-temperature design standards.

## v0.11 Sections 9.3–9.4

- The package does not calculate branch effective lengths or global member forces.
- Table 22 and Table 23 diagram/section types are not inferred from arbitrary geometry.
- Section 16 calculations for three-sided members remain external.
- Batten, lattice, weld, bolt, and connection resistance checks are not completed by the routing functions.
- Table 22 and Table 23 interpolation is applied only where their notes explicitly prescribe it; no general interpolation or extrapolation is provided.
- Reduced-area and stiffener routes identify required downstream calculations but do not substitute for complete section or connection design.
- Clause 9.4.10 routes eccentrically tensioned members with compressive zones to the bending-member local-stability model; it does not generate the stress field.
- Validation self-checks are not normative worked examples, experimental validation, expert approval, or legal certification.

## v0.12 Section 10

- The package does not solve a global frame, eigenvalue buckling problem, or load-combination problem.
- Tables 24-31 require external interpretation of the printed structural diagrams; arbitrary geometry is not classified automatically.
- Table 29 interpolation is limited to the rule explicitly stated for the parameter `n`; no unrelated interpolation is introduced.
- Elastic end-restraint formulas referenced to separate steel-design rules remain external.
- Stepped-column effective lengths requiring Annex И remain external.
- Equation (147) is a scalar procedure component and does not replace the full frame analysis in clause 10.3.5.
- The package cannot establish whether a third-party calculation program is certified or whether its model assumptions satisfy clause 10.3.11.
- Limiting-slenderness checks do not replace strength, overall-stability, local-stability, fatigue, or connection checks.
- Validation self-checks are not normative worked examples, experimental validation, expert approval, or legal certification.

## v0.13 Section 11

- Table 34 supports exact printed `r/t` nodes only; no interpolation or extrapolation rule is introduced.
- Equation (156) therefore requires an explicit axial critical stress when the selected tube `r/t` is not a Table 34 node.
- The package does not calculate local edge effects at discontinuities or perform arbitrary-shell spatial finite-element analysis.
- Automatic shell geometry classification, mesh generation, stress recovery, and governing-point search are external.
- Ring-stiffener procedures return normative force and effective-geometry requirements but do not complete section, weld, bolt, or connection design.
- Formula (164) retains the printed coefficient `6.28` rather than silently replacing it with `2π`.
- Section 11 self-checks verify transcription and internal consistency; they are not normative worked examples, experimental validation, expert approval, or legal certification.

## v0.15 brittle-fracture and welded connections

Implemented Section 12 equations (170)-(173), Tables 35-36, and Annex K Table K.1 with explicit cycle counts, signed stress extrema, fatigue group, steel resistance, and crane-runway inputs. SP 20.13330 load derivation, variable-amplitude damage accumulation, low-cycle fatigue, and automatic detail recognition remain external.

## v0.15 limitations

- The package does not select steel, verify impact toughness, interpret ultrasonic scans, or perform fracture-mechanics assessment.
- It does not recognize welded details from CAD/BIM or qualify welding procedures.
- Tables 37-39 are not extrapolated; interpolation is used only where the clause explicitly states it.
- The welded-connection functions do not replace fabrication, NDT, corrosion, fatigue, or global structural checks.


## v0.16 bolted and friction connections

Clauses 14.2-14.3, equations (186)-(192), and Tables 40-42 are implemented with explicit units, applicability checks, table routes, tests, and validation self-checks. Product standards, anchor-bolt design, installation evidence, and global force derivation remain external.

## v0.17 built-up beam flange connections

- The package does not perform global beam analysis or derive the governing shear force, concentrated load, load factors, or effective distribution length.
- Table 43 routing does not recognize flange position, transverse stiffeners, web-edge planing, weld penetration, or multilayer sheet cut-offs from CAD/BIM geometry.
- Equations (193)–(198) check the supplied scalar section and connection data; they do not calculate a complete weld, bolt group, web, stiffener, or flange package.
- The full-penetration route records the normative equal-strength classification but does not verify welding procedure qualification, penetration evidence, or NDT results.
- Clause 14.4.2 returns the required half or full sheet-section attachment force; it does not locate cut-offs or design the individual bolts.
- Validation self-checks verify transcription and internal consistency, not a normative worked example, fabrication acceptance, expert approval, or legal certification.

## v0.18 structural detailing and support bearings

- The package does not generate climatic temperature actions or perform frame analysis with inelasticity and joint flexibility.
- Table 44 is not interpolated or extrapolated.
- Building type, direction, bracing layout, and stiffness contribution of walls or other structures are not inferred from CAD/BIM.
- The Section 15 catalogue classifies 80 clause records, but only Table 44, support selection/friction, and equations (199)–(200) are numerically executable in this release.
- Bearing contact nonlinearity, edge effects, local plasticity distribution, wear, fatigue, roller skew, and imperfect load sharing are not modelled.
- Bearing body, track, anchor, weld, foundation, and substructure design remain external.
- Product selection, fabrication tolerances, inspection evidence, and installation acceptance are not verified.
- Validation self-checks confirm transcription and internal consistency, not legal certification or a complete bearing design.

## v0.19 overhead-line and switchyard supports

- Loads and combinations from the applicable external load standards are not generated.
- The package does not perform global first- or second-order analysis of a complete support, guy system, traverse, or switchyard frame.
- Table 45 does not apply to node connections; node strength must be checked separately.
- Table 46 category selection, emergency/erection exclusions, and stricter equipment limits require explicit engineering evidence.
- Equations (209)–(212) do not infer Figure 15 geometry, bolt-line position, or force distribution from CAD/BIM.
- The detailing wrapper does not replace complete bolt bearing, splice, diaphragm, fabrication, or erection design.
- Equations (213)–(214) are limited to polygonal tubes with 8–12 faces and do not replace linked circular-tube, local, and global stability checks.
- Equation (215) and Table 47 are Section 17 items and remained unresolved in v0.19; equations (216)–(224) and Table 48 belong to Section 18.

## v0.20 antenna structures

- Loads, combinations, global analysis, commercial product selection, rope dynamics, fatigue qualification, fabrication evidence, marking, lighting, and coating inspection remain external.
- Table 47 is an exact categorical lookup. Equation (215) is not a cable-vibration or galloping analysis.

## v0.21 reconstruction assessment

- The package does not perform a building survey, establish the technical-condition category from observations, or verify the competence and completeness of survey records.
- Material grade, steelmaking process, certificate validity, laboratory sampling, chemical composition, mechanical properties, impact toughness, macrostructure, and microstructure remain evidence-based inputs.
- Existing steel, weld, bolt, and rivet resistance routes do not replace the linked product standards, statistical processing, or professional material-identification decision.
- Table 48 uses exact printed categories only. The unavailable group-C shear value for 09G2 is rejected; no interpolation or substitution is invented.
- The interpretation of the 15% threshold in clause 18.3.11 is implemented conservatively relative to the lower resistance and is documented explicitly.
- Equations (216)–(224) are scalar checks. Loads, initial stresses, actual geometry, defects, residual deformations, construction stages, stability coefficients, section properties, and governing section points must come from a verified model.
- Figure 24 coefficients `n_i` are explicit inputs. The graph is not digitized or interpolated, and welding heat input, sequence, restraint, and nonlinear residual-stress fields are not modelled.
- Equation (217) checks the absolute value of the supplied algebraic point stress; governing-point search over the strengthened section remains external.
- Equation (218) requires an externally verified `phi_e` and enforces the printed `gamma_c <= 0.9`; it does not perform global stability analysis.
- Construction-stage safety, monitoring, unloading, temporary support, workmanship, NDT, and acceptance remain evidence routes rather than calculated proof.
- Validation cases verify transcription, table values, arithmetic, boundaries, and routing. They are not a normative worked example, independent experimental validation, expert approval, or legal certification.


## Reconstructed v0.22 r1 note

This release is reconstructed from v0.21 because the historical v0.22 binary archive is unavailable. Equations (10)-(11) and Table 1 are restored. In Stage N1, Annex Б.1 and В.3/В.4/В.5 are materialized from the locked current source; 20 other Annex Б/В/Г/И tables remain explicit `external_reference_required` boundaries rather than being represented by incomplete raw-text data. Recursive schema validation rejects nested invalid values and non-finite numbers.


## Stage N1 Material / Strength limitations

- NormCAD physical defaults `E=210000 MPa` and `G=78500 MPa` are recorded as divergent from the locked current СП values `206000 MPa` and `79000 MPa`; NormCAD never overrides the source.
- NormCAD strength MDB files are hash-captured but their row-level values are not decoded in this environment; Stage N1 therefore does not claim complete NormCAD strength-table agreement.
- The resolver does not interpolate or extrapolate Annex В strength tables; unprinted gaps and out-of-range inputs fail closed.
- Table-rounded Annex В `Ry/Ru` are kept distinct from raw Table 2 formula results based on the selected `gamma_m`.


## FIRE-D3 SP554 Section 12 thermal-runtime limitations

- `PROTECTED_FDM_12_5` is closed only for dry protection (`W=0`). Wet-protection phase-change (`W>0`) is fail-closed because the locked text does not unambiguously define the activation/latent-energy algorithm required for deterministic execution.
- Matrix/nomogram runtime requires explicit product technical-documentation evidence. It does not create missing performance data.
- No critical-temperature interpolation between the 50 °C matrix levels is invented.
- Figure 1 and protection-thickness extrapolation are forbidden. Clause 12.4 greater-reduced-thickness extension must be explicitly authorized by the dataset.
- Non-monotonic experimental matrix values are retained; inverse thickness uses the first qualifying piecewise-linear crossing and emits a warning.
- Connection fire resistance remains outside FIRE-D3.
- `ENGINEERING_USE_READY` remains false.
