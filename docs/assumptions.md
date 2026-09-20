# Assumptions

- All quantities use the units encoded in public argument names; no silent conversion occurs.
- Axial force and bending moments used together come from the same verified load combination.
- Compression is supplied as a positive magnitude unless a function explicitly documents a signed quantity.
- Gross or reduced area has already been selected consistently with linked local-stability clauses.
- Section types for Tables 20-21 and Annex D Tables D.2-D.6 are correctly classified from the standard diagrams.
- Relative slendernesses, geometric slendernesses, effective lengths, section moduli, inertias, radii of gyration, torsional properties, and sectorial properties come from a verified model.
- Exact-node lookups are intentional where the standard gives no interpolation instruction.
- Table D.3 and D.4 values are capped by the supplied central-compression coefficient only when the caller uses the capped lookup functions.
- Table D.5 end-moment ratio follows the printed diagram sign convention.
- For Table 21 type 4, `I2/I1` is the smaller-to-larger flange inertia ratio about the section symmetry axis.
- External confirmations in input schemas are truthful and traceable to separate calculations.

## v0.11 Sections 9.3–9.4

- Table 8, Table 22, and Table 23 section types are supplied by a competent external classification.
- Branch spacings, free-axis inertia, effective web/flange dimensions, and stiffener properties come from a verified section model.
- All actions used together originate from the same verified load combination.
- Endpoint limits supplied for Table 22 or Table 23 interpolation have already been calculated from the linked clauses with consistent geometry and material data.
- The list of stability coefficients supplied to the two-plane multiplier is exactly the set used in the governing member-stability checks.
- External confirmations for Section 16, reduced-area use, stiffener design, and connector design are truthful and traceable.

## v0.12 Section 10

- Lengths and section properties are derived from a verified structural model and use millimetres and consistent force units.
- Force ratios in equations (136)-(139) come from one load combination and follow the printed tension/compression sign rules.
- Table 24-31 diagram identifiers and member roles are selected externally by a competent engineer.
- Frame parameters `p` and `n` are calculated from the stiffness and force quantities represented in Table 31.
- Table 32 parameter `alpha` uses the same axial force, area, resistance, working-condition factor, and stability coefficient as the governing member check.
- Table 33 load category and any special note applicability are explicit inputs.
- External routes for stepped columns, elastic end restraint, global stability, and software certification are truthful and traceable.

## v0.13 Section 11

- Shell radii, thicknesses, lengths, cone angles, loads, and stress resultants come from a verified geometric and structural model.
- Compression and external-pressure demands are supplied as non-negative magnitudes unless a function explicitly requires a signed membrane stress.
- The same consistent length unit is used for every geometry input; stress and elastic modulus use N/mm².
- Table 34 section classification and any explicit non-node coefficient are independently justified and documented.
- Thin-shell membrane assumptions and the applicability conditions stated in clauses 11.1-11.2 have been checked externally.
- External confirmations for edge effects, spatial shell analysis, global member stability, and ring-stiffener design are truthful and traceable.

## v0.15 brittle-fracture and welded connections

Implemented Section 12 equations (170)-(173), Tables 35-36, and Annex K Table K.1 with explicit cycle counts, signed stress extrema, fatigue group, steel resistance, and crane-runway inputs. SP 20.13330 load derivation, variable-amplitude damage accumulation, low-cycle fatigue, and automatic detail recognition remain external.

## v0.15 assumptions

- Table 37 geometry, Table 38 connection type, and Table 39 process/position are explicit engineering classifications.
- Material certificates and test records correspond to the actual product, thickness, and weld detail.
- Forces and moments supplied to the welded-connection functions come from one verified design combination.
- Weld resistances are calculated or supplied consistently with Section 6 and the selected welding consumable.


## v0.16 bolted and friction connections

Clauses 14.2-14.3, equations (186)-(192), and Tables 40-42 are implemented with explicit units, applicability checks, table routes, tests, and validation self-checks. Product standards, anchor-bolt design, installation evidence, and global force derivation remain external.

## v0.17 built-up beam flange connections

- The shear force `Q`, gross flange static moment `S`, and gross section inertia `I` refer to the same section and centroidal axis.
- The effective local-load distribution length `l_ef` and load factors are obtained from the linked audited clauses and a verified loading model.
- The nominal load character, loaded flange, presence of a transverse stiffener, and web-edge planing condition are explicit engineering inputs.
- Weld coefficients, weld resistances, friction-plane capacity, friction-plane count, bolt pitch, and working-condition factor are consistent with the selected connection and previous audited connection modules.
- The theoretical and actual cut-off locations of a multilayer flange sheet have been determined externally from a verified beam design.

## v0.18 structural detailing and support bearings

- Table 44 building category, direction, and design air temperature are explicit engineering inputs.
- The `t = -45 °C` boundary belongs to the warmer Table 44 column; only lower temperatures use the colder column.
- Actual and limiting distances use the same geometric definition and are expressed in metres.
- A Table 44 exceedance is noncompliance; the separate 5% statement is an enhanced-analysis trigger, not an admissible tolerance.
- Support reactions are non-negative compressive magnitudes and come from one verified load combination.
- Equation (199) is applied only to dense cylindrical contact with a central angle not less than 90°.
- Equation (200) assumes the clause model distributes force among the stated number of rollers.
- Section 15 clause classification is a routing catalogue; it is not proof that every drawing-level requirement is satisfied.

## v0.19 overhead-line and switchyard supports

- The support category, structure group, Table 45 row, Table 46 row, Figure 15 geometry route, connection type, and load mode are explicit engineering inputs.
- Forces, moments, deflections, reduced slendernesses, section properties, and load combinations originate from one verified global model.
- Compression is positive in the Section 16 scalar stability routes; `sigma_2` may be negative when the less-compressed polygonal-wall edge is in tension.
- Equations (206)–(207) use the printed initial bow `f_n = 0.0013l`; the first-order deflection `f_q` is supplied externally.
- Table 46 numerical values are denominators of relative limits `1/n`.

## v0.20 Section 17 antenna structures

- The structure is within the Section 17 applicability limit of 500 m and its component group is selected by a competent engineer.
- Steel grade selection under Annex V, connection material selection, loads, combinations, rope product capacity, and fatigue evidence are externally verified.
- Rope design force is a positive tensile magnitude; rope capacity and wire breaking force use the same verified basis as the selected product documentation.
- Table 47 row selection is explicit and categorical; no coefficient is inferred from geometry.
- Support deviations, platform deflections, diaphragm spacing, node eccentricity, and vibration parameters are obtained from verified analyses or drawings.
- Boolean evidence inputs represent traceable drawings, specifications, inspection records, test reports, or installation records.
- Equation (215) uses `d` in millimetres, `P` in newtons, `m` in kilograms per metre, and returns the damper distance `s` in metres, consistent with the printed symbol definitions.

## v0.21 Section 18 reconstruction assessment

- The structure is an existing steel structure within Section 18, and all survey findings are established by competent specialists.
- Technical-condition categories and boolean evidence inputs refer to traceable survey reports, drawings, certificates, test reports, monitoring records, and construction-stage calculations.
- Forces, moments, stresses, deflections, section properties, stability coefficients, and material resistances use one consistent calculation model and load combination.
- Compression magnitudes are positive where stated; moments, coordinates, eccentricities, initial deflections, welding deflections, and Figure 24 terms retain their algebraic signs.
- Table 48 group, rivet steel, head form, and limit state are explicitly identified. Unknown evidence is routed conservatively to group C and St2 outside the table lookup.
- The `n_i` values for equation (222) are independently read from Figure 24 for the applicable stress state and weld arrangement; no graph interpolation is performed by the package.
- Original properties do not exceed strengthened properties in equation (224), and the strengthened section is assumed to act as specified by the design.
- External evidence and confirmations supplied to the runner are truthful and remain available for audit.
