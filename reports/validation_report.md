# Validation report

- Release: `v0.67_fire_bridge2_qualified_sp16_complex_state_handoff_r1`
- Status: `cumulative_internal_regression_and_normative_table_transcription_checks_through_equation_224_including_reconstructed_equations_10_11;_not_external_certification`
- All checks passed: **yes**
- Cases: 1876

The report contains arithmetic self-checks and cross-checks of the transcribed Tables D.1-D.6, 10a, E.1, E.2, 11-48, Annex K Table K.1, and Ж.1-Ж.5. It contains no invented standard worked example.

| Case | Reference | Calculated | Reference value | Abs. error | Tolerance | Status |
|---|---|---:|---:|---:|---:|---|
| CORE-TBL-2-RY | 6.1 Table 2 | 338.095238095 | 338.095238095 | 0 | 1e-12 | pass |
| CORE-TBL-2-RU | 6.1 Table 2 | 485.714285714 | 485.714285714 | 0 | 1e-12 | pass |
| CORE-TBL-2-RS | 6.1 Table 2 | 196.095238095 | 196.095238095 | 0 | 1e-12 | pass |
| CORE-TBL-2-RP | 6.1 Table 2 | 485.714285714 | 485.714285714 | 0 | 1e-12 | pass |
| CORE-TBL-2-RLP | 6.1 Table 2 | 242.857142857 | 242.857142857 | 0 | 1e-12 | pass |
| CORE-TBL-2-RCD | 6.1 Table 2 | 12.1428571429 | 12.1428571429 | 0 | 1e-12 | pass |
| CORE-TBL-3 | 6.1 Table 3 | 1.05 | 1.05 | 0 | 0 | pass |
| CORE-TBL-4-RWY-NDT | 6.4 Table 4 | 338 | 338 | 0 | 0 | pass |
| CORE-TBL-4-RWY | 6.4 Table 4 | 287.3 | 287.3 | 0 | 1e-12 | pass |
| CORE-TBL-4-RWF | 6.4 Table 4 | 215.6 | 215.6 | 0 | 1e-12 | pass |
| CORE-TBL-4-RWZ | 6.4 Table 4 | 229.5 | 229.5 | 0 | 1e-12 | pass |
| CORE-TBL-5-RBS | 6.5 Table 5 | 320 | 320 | 0 | 1e-12 | pass |
| CORE-TBL-5-RBT | 6.5 Table 5 | 432 | 432 | 0 | 1e-12 | pass |
| CORE-TBL-5-RBP | 6.5 Table 5 | 776 | 776 | 0 | 1e-12 | pass |
| CORE-EQ-001 | 6.6 equation (1) | 284 | 284 | 0 | 1e-12 | pass |
| CORE-EQ-002 | 6.6 equation (2) | 301.75 | 301.75 | 0 | 1e-12 | pass |
| CORE-EQ-004 | 6.8 equation (4) | 321.3 | 321.3 | 0 | 1e-12 | pass |
| CORE-PROC-6.9 | 6.9 | 1000000 | 1000000 | 0 | 1e-09 | pass |
| AXIAL-EQ-005-YIELD | 7.1.1 equation (5) | 0.704225352113 | 0.704225352113 | 0 | 1e-12 | pass |
| AXIAL-EQ-005-ULTIMATE | 7.1.1 equation (5), R_u/gamma_u branch | 0.670103092784 | 0.670103092784 | 0 | 1e-12 | pass |
| AXIAL-TBL-006 | 7.1.2 Table 6 | 1.45 | 1.45 | 0 | 0 | pass |
| AXIAL-PROC-GAMMA-C1 | 7.1.2 gamma_c1 | 0.65 | 0.65 | 1.11e-16 | 1e-12 | pass |
| AXIAL-PROC-GAMMA-C1-REDUCED | 7.1.2 10% reduction | 0.585 | 0.585 | 0 | 1e-12 | pass |
| AXIAL-EQ-006 | 7.1.2 equation (6) | 0.824742268041 | 0.824742268041 | 0 | 1e-12 | pass |
| AXIAL-PROC-RELATIVE-SLENDERNESS | 7.1.3 lambda_bar definition | 2 | 2 | 0 | 1e-12 | pass |
| AXIAL-TBL-007 | 7.1.3 Table 7 | 0.14 | 0.14 | 0 | 0 | pass |
| AXIAL-EQ-009 | 7.1.3 equation (9) | 15.2518 | 15.2518 | 0 | 1e-12 | pass |
| AXIAL-EQ-008 | 7.1.3 equation (8) | 0.826129256441 | 0.826129256441 | 1.11e-16 | 1e-12 | pass |
| AXIAL-EQ-008-LOW | 7.1.3 low-slenderness rule | 1 | 1 | 0 | 0 | pass |
| AXIAL-EQ-008-CAP | 7.1.3 upper cap rule | 0.304 | 0.304 | 0 | 1e-12 | pass |
| AXIAL-EQ-007 | 7.1.3 equation (7) | 0.704225352113 | 0.704225352113 | 0 | 1e-12 | pass |
| AXIAL-EQ-011-RECONSTRUCTION | 7.1.5 equation (11) | 1.52 | 1.52 | 0 | 1e-12 | pass |
| AXIAL-EQ-010-RECONSTRUCTION | 7.1.5 equations (10)-(11) | 0.467227189782 | 0.467227189782 | 0 | 1e-12 | pass |
| BUILTUP-TBL-008 | 7.2 Table 8 | 6 | 6 | 0 | 0 | pass |
| BUILTUP-EQ-012 | 7.2 Table 8 equation (12) | 2.22512920973 | 2.22512920973 | 0 | 1e-12 | pass |
| BUILTUP-EQ-013 | 7.2 Table 8 equation (13) | 2.47095042443 | 2.47095042443 | 0 | 1e-12 | pass |
| BUILTUP-EQ-014 | 7.2 Table 8 equation (14) | 2.27469558403 | 2.27469558403 | 0 | 1e-12 | pass |
| BUILTUP-EQ-015 | 7.2 Table 8 equation (15) | 11.7898261226 | 11.7898261226 | 0 | 1e-12 | pass |
| BUILTUP-EQ-016 | 7.2 Table 8 equation (16) | 17.4245507996 | 17.4245507996 | 0 | 1e-12 | pass |
| BUILTUP-EQ-017 | 7.2 Table 8 equation (17) | 9.71853898485 | 9.71853898485 | 0 | 1e-12 | pass |
| BUILTUP-EQ-018 | 7.2.7 equation (18) | 15638.1073944 | 15638.1073944 | 0 | 1e-09 | pass |
| BUILTUP-EQ-019 | 7.2.8 equation (19) | 2000 | 2000 | 0 | 1e-12 | pass |
| BUILTUP-EQ-020 | 7.2.8 equation (20) | 400000 | 400000 | 0 | 1e-09 | pass |
| BUILTUP-EQ-021 | 7.2.9 equation (21) | 750 | 750 | 0 | 1e-12 | pass |
| BUILTUP-EQ-022 | 7.2.9 equation (22) | 44651.1627907 | 44651.1627907 | 0 | 1e-09 | pass |
| BUILTUP-PROC-7.2.2-METHOD | 7.2.2 method route | 1 | 1 | 0 | 0 | pass |
| BUILTUP-PROC-7.2.5-PHI1 | 7.2.5 branch phi_1 | 1 | 1 | 0 | 0 | pass |
| BUILTUP-PROC-7.2.7-DISTRIBUTION | 7.2.7 distribution | 250 | 250 | 0 | 0 | pass |
| LOCAL-TBL-009 | 7.3.2 Table 9 | 4 | 4 | 0 | 0 | pass |
| LOCAL-EQ-023 | 7.3.2 equation (23) | 1.9 | 1.9 | 0 | 1e-12 | pass |
| LOCAL-EQ-024 | 7.3.2 equation (24) | 2.3 | 2.3 | 0 | 0 | pass |
| LOCAL-EQ-025 | 7.3.2 equation (25) | 1.2 | 1.2 | 0 | 0 | pass |
| LOCAL-EQ-026 | 7.3.2 equation (26) | 1.4 | 1.4 | 0 | 1e-12 | pass |
| LOCAL-EQ-027 | 7.3.2 equation (27) | 1 | 1 | 0 | 0 | pass |
| LOCAL-EQ-028 | 7.3.2 equation (28) | 1.23 | 1.23 | 0 | 1e-12 | pass |
| LOCAL-EQ-029 | 7.3.2 equation (29) | 0.675 | 0.675 | 0 | 1e-12 | pass |
| LOCAL-PROC-WEB-SLENDERNESS | 7.3.2 web slenderness | 2.59454127303 | 2.59454127303 | 0 | 1e-12 | pass |
| LOCAL-EQ-030 | 7.3.4 equation (30) | 2 | 2 | 0 | 1e-12 | pass |
| LOCAL-EQ-031 | 7.3.6 equation (31) | 9200 | 9200 | 0 | 1e-09 | pass |
| LOCAL-EQ-032 | 7.3.6 equation (32) | 10600 | 10600 | 0 | 1e-09 | pass |
| LOCAL-EQ-033 | 7.3.6 equation (33) | 11200 | 11200 | 0 | 1e-09 | pass |
| LOCAL-EQ-034 | 7.3.6 equation (34) | 364.948906322 | 364.948906322 | 0 | 1e-09 | pass |
| LOCAL-EQ-035 | 7.3.6 equation (35) | 337.246514093 | 337.246514093 | 0 | 1e-09 | pass |
| LOCAL-EQ-036 | 7.3.6 equation (36) | 231.254752521 | 231.254752521 | 0 | 1e-09 | pass |
| LOCAL-TBL-010 | 7.3.8 Table 10 | 4 | 4 | 0 | 0 | pass |
| LOCAL-EQ-037 | 7.3.8 equation (37) | 0.56 | 0.56 | 0 | 1e-12 | pass |
| LOCAL-EQ-038 | 7.3.8 equation (38) | 0.59 | 0.59 | 0 | 1e-12 | pass |
| LOCAL-EQ-039 | 7.3.8 equation (39) | 0.54 | 0.54 | 0 | 1e-12 | pass |
| LOCAL-EQ-040 | 7.3.8 equation (40) | 1.23 | 1.23 | 0 | 1e-12 | pass |
| LOCAL-PROC-FLANGE-SLENDERNESS | 7.3.8 flange slenderness | 0.415126603685 | 0.415126603685 | 0 | 1e-12 | pass |
| LOCAL-PROC-TABLE-10 | 7.3.8 Table 10 edge multiplier | 0.864 | 0.864 | 0 | 1e-12 | pass |
| LOCAL-PROC-7.3.10 | 7.3.10 edge stiffener | 30 | 30 | 0 | 0 | pass |
| LOCAL-PROC-7.3.11 | 7.3.11 two-plane factor cap | 1.25 | 1.25 | 0 | 0 | pass |
| BEND-EQ-041 | 8.2.1 equation (41) | 0.4 | 0.4 | 0 | 1e-12 | pass |
| BEND-EQ-042 | 8.2.1 equation (42) | 0.0862068965517 | 0.0862068965517 | 0 | 1e-12 | pass |
| BEND-EQ-043 | 8.2.1 equation (43) | 0.591549295775 | 0.591549295775 | 0 | 1e-12 | pass |
| BEND-EQ-044 | 8.2.1 equation (44) | 0.309022044655 | 0.309022044655 | 0 | 1e-12 | pass |
| BEND-EQ-045 | 8.2.1 equation (45) | 1.25 | 1.25 | 0 | 1e-12 | pass |
| BEND-EQ-046 | 8.2.2 equation (46) | 0.4 | 0.4 | 0 | 1e-12 | pass |
| BEND-EQ-047 | 8.2.2 equation (47) | 100 | 100 | 0 | 1e-12 | pass |
| BEND-EQ-048 | 8.2.2 equation (48) | 140 | 140 | 0 | 1e-12 | pass |
| BEND-EQ-049 | 8.2.2 equation (49) | 325 | 325 | 1.14e-13 | 1e-09 | pass |
| BEND-EQ-050 | 8.2.3 equation (50) | 0.333333333333 | 0.333333333333 | 0 | 1e-12 | pass |
| BEND-EQ-051 | 8.2.3 equation (51) | 0.466666666667 | 0.466666666667 | 0 | 1e-12 | pass |
| BEND-EQ-052 | 8.2.3 equation (52) | 0.934464 | 0.934464 | 0 | 1e-12 | pass |
| BEND-EQ-053 | 8.2.3 equation (53) | 0.533333333333 | 0.533333333333 | 0 | 1e-12 | pass |
| BEND-EQ-054 | 8.2.3 equation (54) | 1 | 1 | 0 | 1e-12 | pass |
| BEND-EQ-055 | 8.2.3 equation (55) | 1 | 1 | 0 | 1e-12 | pass |
| BEND-EQ-056 | 8.2.5 equation (56) | 150 | 150 | 0 | 1e-12 | pass |
| BEND-EQ-057 | 8.2.5 equation (57) | 120 | 120 | 0 | 1e-12 | pass |
| BEND-EQ-058 | 8.2.5 equation (58) | 80 | 80 | 0 | 1e-12 | pass |
| BEND-EQ-059 | 8.2.8 equation (59) | 0.333333333333 | 0.333333333333 | 0 | 1e-12 | pass |
| BEND-EQ-060 | 8.2.8 equation (60) | 0.449275362319 | 0.449275362319 | 0 | 1e-12 | pass |
| BEND-EQ-061 | 8.2.8 equation (61) | 1.19293297153 | 1.19293297153 | 0 | 1e-12 | pass |
| BEND-EQ-062 | 8.2.8 equation (62) | 0.943503448276 | 0.943503448276 | 0 | 1e-12 | pass |
| BEND-TBL-10A | 8.2.3 Table 10a | 11 | 11 | 0 | 0 | pass |
| BEND-TBL-E1 | Annex E Table E.1 | 12 | 12 | 0 | 0 | pass |
| BEND-PROC-8.1 | 8.1 class routing | 1 | 1 | 0 | 0 | pass |
| BEND-PROC-8.2.1-STRESS | 8.2.1 stress-point route | 0 | 0 | 0 | 0 | pass |
| BEND-PROC-8.2.1-HOLES | 8.2.1 bolt-hole adjustment | 1 | 1 | 0 | 1e-12 | pass |
| BEND-PROC-8.2.2-LENGTH | 8.2.2 load-length route | 140 | 140 | 0 | 1e-12 | pass |
| BEND-PROC-8.2.3-APPLICABILITY | 8.2.3 plastic applicability | 1 | 1 | 0 | 0 | pass |
| BEND-PROC-E1-INTERPOLATION | Annex E Table E.1 interpolation | 1.095 | 1.095 | 2.22e-16 | 1e-12 | pass |
| BEND-PROC-E1-CAP | Annex E Table E.1 cap | 1.265 | 1.265 | 0 | 1e-12 | pass |
| BEND-PROC-10A-INTERPOLATION | Table 10a interpolation | 1.7405 | 1.7405 | 0 | 1e-12 | pass |
| BEND-PROC-PURE-BENDING | 8.2.3 pure-bending coefficients | 1.1 | 1.1 | 0 | 1e-12 | pass |
| BEND-PROC-8.2.4 | 8.2.4 variable-section route | 1 | 1 | 0 | 0 | pass |
| BEND-PROC-8.2.5-APPLICABILITY | 8.2.5 continuous-beam applicability | 1 | 1 | 0 | 0 | pass |
| BEND-PROC-8.2.5-MOMENT | 8.2.5 effective-moment route | 50 | 50 | 0 | 1e-12 | pass |
| BEND-PROC-8.2.6 | 8.2.6 biaxial redistribution | 1 | 1 | 0 | 0 | pass |
| BEND-PROC-8.2.7 | 8.2.7 class-3 route | 1 | 1 | 0 | 0 | pass |
| BEND-PROC-8.2.8-APPLICABILITY | 8.2.8 bimetal applicability | 1 | 1 | 0 | 0 | pass |
| BEND-PROC-8.2.8-CYR | 8.2.8 bimetal minor coefficient | 1.15 | 1.15 | 0 | 1e-12 | pass |
| CRANE-EQ-063 | 8.3.3 equation (63) | 0.289712215866 | 0.289712215866 | 0 | 1e-12 | pass |
| CRANE-EQ-064 | 8.3.3 equation (64) | 0.4 | 0.4 | 0 | 1e-12 | pass |
| CRANE-EQ-065 | 8.3.3 equation (65) | 0.4 | 0.4 | 0 | 1e-12 | pass |
| CRANE-EQ-066 | 8.3.3 equation (66) | 0.5 | 0.5 | 0 | 1e-12 | pass |
| CRANE-EQ-067-SIGMA-X | 8.3.3 equation (67) | 100 | 100 | 0 | 1e-12 | pass |
| CRANE-EQ-067-SIGMA-LOC-Y | 8.3.3 equation (67) | 66 | 66 | 0 | 1e-12 | pass |
| CRANE-EQ-068 | 8.3.3 equation (68) | 3765000 | 3765000 | 0 | 1e-09 | pass |
| CRANE-PROC-8.3.5 | 8.3.5 bimetal crane route | 0.375756957202 | 0.375756957202 | 0 | 1e-12 | pass |
| STAB-EQ-069 | 8.4.1 equation (69) | 0.5 | 0.5 | 0 | 1e-12 | pass |
| STAB-EQ-070 | 8.4.1 equation (70) | 0.6604 | 0.6604 | 0 | 1e-12 | pass |
| STAB-PROC-8.4.3 | 8.4.3 crane stability route | 0.6604 | 0.6604 | 0 | 1e-12 | pass |
| STAB-EQ-071 | 8.4.4 equation (71) | 0.628 | 0.628 | 0 | 1e-12 | pass |
| STAB-EQ-072 | 8.4.4 equation (72) | 0.928 | 0.928 | 0 | 1e-12 | pass |
| STAB-EQ-073 | 8.4.4 equation (73) | 0.703 | 0.703 | 0 | 1e-12 | pass |
| STAB-EQ-074 | 8.4.5 equation (74) | 976250 | 976250 | 0 | 1e-09 | pass |
| STAB-EQ-075 | 8.4.5 equation (75) | 6 | 6 | 0 | 1e-12 | pass |
| STAB-EQ-076 | 8.4.6 equation (76) | 0.7 | 0.7 | 0 | 1e-12 | pass |
| STAB-EQ-077 | 8.4.6 equation (77) | 1.2 | 1.2 | 2.22e-16 | 1e-12 | pass |
| STAB-PROC-REL-SLENDERNESS | 8.4.4 compressed-flange slenderness | 0.691877672809 | 0.691877672809 | 0 | 1e-12 | pass |
| STAB-TBL-011-NOTE | 8.4.4 Table 11 notes 2-3 | 1.19154622235 | 1.19154622235 | 0 | 1e-12 | pass |
| STAB-PROC-8.4.2 | 8.4.2 effective length | 4000 | 4000 | 0 | 0 | pass |
| STAB-PROC-8.4.4 | 8.4.4 exemption | 1 | 1 | 0 | 0 | pass |
| STAB-TBL-012 | 8.5.4 Table 12 exact node | 34.6 | 34.6 | 0 | 0 | pass |
| STAB-TBL-013 | 8.5.4 Table 13 finite case | 0.8 | 0.8 | 0 | 0 | pass |
| ZH-EQ-001 | Annex Ж equation (Ж.1) | 0.85 | 0.85 | 0 | 0 | pass |
| ZH-EQ-002 | Annex Ж equation (Ж.2) | 0.89 | 0.89 | 0 | 1e-12 | pass |
| ZH-EQ-003 | Annex Ж equation (Ж.3) | 0.580281690141 | 0.580281690141 | 1.11e-16 | 1e-12 | pass |
| ZH-EQ-004 | Annex Ж equation (Ж.4) | 1 | 1 | 0 | 1e-12 | pass |
| ZH-EQ-005 | Annex Ж equation (Ж.5) | 1.96296296296 | 1.96296296296 | 0 | 1e-12 | pass |
| ZH-EQ-006 | Annex Ж equation (Ж.6) | 0.696338028169 | 0.696338028169 | 0 | 1e-12 | pass |
| ZH-EQ-007 | Annex Ж equation (Ж.7) | 0.464225352113 | 0.464225352113 | 0 | 1e-12 | pass |
| ZH-EQ-008 | Annex Ж equation (Ж.8) | 0.75 | 0.75 | 0 | 0 | pass |
| ZH-EQ-009 | Annex Ж equation (Ж.9) | 2.80277563773 | 2.80277563773 | 0 | 1e-12 | pass |
| ZH-EQ-010 | Annex Ж equation (Ж.10) | 0.8234 | 0.8234 | 0 | 1e-12 | pass |
| ZH-EQ-011 | Annex Ж equation (Ж.11) | 0.8645 | 0.8645 | 0 | 1e-12 | pass |
| ZH-EQ-012 | Annex Ж equation (Ж.12) | 0.21847216 | 0.21847216 | 0 | 1e-12 | pass |
| ZH-EQ-013 | Annex Ж equation (Ж.13) | 30.725625 | 30.725625 | 0 | 1e-12 | pass |
| ZH-TBL-001 | Annex Ж Table Ж.1 | 3.90896405714 | 3.90896405714 | 0 | 1e-12 | pass |
| ZH-TBL-002 | Annex Ж Table Ж.2 | 4.2 | 4.2 | 0 | 1e-12 | pass |
| ZH-TBL-003 | Annex Ж Table Ж.3 | 0.89 | 0.89 | 0 | 1e-12 | pass |
| ZH-TBL-004 | Annex Ж Table Ж.4 | 0.5 | 0.5 | 0 | 0 | pass |
| ZH-TBL-005 | Annex Ж Table Ж.5 | 3.3 | 3.3 | 4.44e-16 | 1e-12 | pass |
| ZH-PROC-INTERPOLATION | Annex Ж.6 interpolation | 3 | 3 | 1.33e-15 | 1e-12 | pass |
| ZH-PROC-T-MODIFIER | Annex Ж.6 T-section modifier | 4.4 | 4.4 | 0 | 1e-12 | pass |
| AXIAL-D1-A-0.4 | Annex D Table D.1, type a, lambda_bar=0.4 | 1 | 1 | 0 | 0.001 | pass |
| AXIAL-D1-B-0.4 | Annex D Table D.1, type b, lambda_bar=0.4 | 1 | 1 | 0 | 0.001 | pass |
| AXIAL-D1-C-0.4 | Annex D Table D.1, type c, lambda_bar=0.4 | 0.984000777876 | 0.984 | 7.78e-07 | 0.001 | pass |
| AXIAL-D1-A-0.6 | Annex D Table D.1, type a, lambda_bar=0.6 | 0.993812847976 | 0.994 | 0.000187 | 0.001 | pass |
| AXIAL-D1-B-0.6 | Annex D Table D.1, type b, lambda_bar=0.6 | 0.985685773167 | 0.986 | 0.000314 | 0.001 | pass |
| AXIAL-D1-C-0.6 | Annex D Table D.1, type c, lambda_bar=0.6 | 0.956397489252 | 0.956 | 0.000397 | 0.001 | pass |
| AXIAL-D1-A-0.8 | Annex D Table D.1, type a, lambda_bar=0.8 | 0.981139588132 | 0.981 | 0.00014 | 0.001 | pass |
| AXIAL-D1-B-0.8 | Annex D Table D.1, type b, lambda_bar=0.8 | 0.966986408136 | 0.967 | 1.36e-05 | 0.001 | pass |
| AXIAL-D1-C-0.8 | Annex D Table D.1, type c, lambda_bar=0.8 | 0.928837681315 | 0.929 | 0.000162 | 0.001 | pass |
| AXIAL-D1-A-1 | Annex D Table D.1, type a, lambda_bar=1 | 0.967809236779 | 0.968 | 0.000191 | 0.001 | pass |
| AXIAL-D1-B-1 | Annex D Table D.1, type b, lambda_bar=1 | 0.947588716045 | 0.948 | 0.000411 | 0.001 | pass |
| AXIAL-D1-C-1 | Annex D Table D.1, type c, lambda_bar=1 | 0.900865143529 | 0.901 | 0.000135 | 0.001 | pass |
| AXIAL-D1-A-1.2 | Annex D Table D.1, type a, lambda_bar=1.2 | 0.953482708664 | 0.953 | 0.000483 | 0.001 | pass |
| AXIAL-D1-B-1.2 | Annex D Table D.1, type b, lambda_bar=1.2 | 0.927096489616 | 0.927 | 9.65e-05 | 0.001 | pass |
| AXIAL-D1-C-1.2 | Annex D Table D.1, type c, lambda_bar=1.2 | 0.872097699637 | 0.872 | 9.77e-05 | 0.001 | pass |
| AXIAL-D1-A-1.4 | Annex D Table D.1, type a, lambda_bar=1.4 | 0.937771944105 | 0.938 | 0.000228 | 0.001 | pass |
| AXIAL-D1-B-1.4 | Annex D Table D.1, type b, lambda_bar=1.4 | 0.905104796678 | 0.905 | 0.000105 | 0.001 | pass |
| AXIAL-D1-C-1.4 | Annex D Table D.1, type c, lambda_bar=1.4 | 0.842224975788 | 0.842 | 0.000225 | 0.001 | pass |
| AXIAL-D1-A-1.6 | Annex D Table D.1, type a, lambda_bar=1.6 | 0.920224313024 | 0.92 | 0.000224 | 0.001 | pass |
| AXIAL-D1-B-1.6 | Annex D Table D.1, type b, lambda_bar=1.6 | 0.881202708903 | 0.881 | 0.000203 | 0.001 | pass |
| AXIAL-D1-C-1.6 | Annex D Table D.1, type c, lambda_bar=1.6 | 0.811019307072 | 0.811 | 1.93e-05 | 0.001 | pass |
| AXIAL-D1-A-1.8 | Annex D Table D.1, type a, lambda_bar=1.8 | 0.900313911931 | 0.9 | 0.000314 | 0.001 | pass |
| AXIAL-D1-B-1.8 | Annex D Table D.1, type b, lambda_bar=1.8 | 0.854992169838 | 0.855 | 7.83e-06 | 0.001 | pass |
| AXIAL-D1-C-1.8 | Annex D Table D.1, type c, lambda_bar=1.8 | 0.778356485754 | 0.778 | 0.000356 | 0.001 | pass |
| AXIAL-D1-A-2 | Annex D Table D.1, type a, lambda_bar=2 | 0.877450474886 | 0.877 | 0.00045 | 0.001 | pass |
| AXIAL-D1-B-2 | Annex D Table D.1, type b, lambda_bar=2 | 0.826129256441 | 0.826 | 0.000129 | 0.001 | pass |
| AXIAL-D1-C-2 | Annex D Table D.1, type c, lambda_bar=2 | 0.744240797132 | 0.744 | 0.000241 | 0.001 | pass |
| AXIAL-D1-A-2.2 | Annex D Table D.1, type a, lambda_bar=2.2 | 0.851025016918 | 0.851 | 2.5e-05 | 0.001 | pass |
| AXIAL-D1-B-2.2 | Annex D Table D.1, type b, lambda_bar=2.2 | 0.794391416772 | 0.794 | 0.000391 | 0.001 | pass |
| AXIAL-D1-C-2.2 | Annex D Table D.1, type c, lambda_bar=2.2 | 0.708825367384 | 0.709 | 0.000175 | 0.001 | pass |
| AXIAL-D1-A-2.4 | Annex D Table D.1, type a, lambda_bar=2.4 | 0.820516904191 | 0.821 | 0.000483 | 0.001 | pass |
| AXIAL-D1-B-2.4 | Annex D Table D.1, type b, lambda_bar=2.4 | 0.759763713735 | 0.76 | 0.000236 | 0.001 | pass |
| AXIAL-D1-C-2.4 | Annex D Table D.1, type c, lambda_bar=2.4 | 0.672416592629 | 0.672 | 0.000417 | 0.001 | pass |
| AXIAL-D1-A-2.6 | Annex D Table D.1, type a, lambda_bar=2.6 | 0.785673841108 | 0.786 | 0.000326 | 0.001 | pass |
| AXIAL-D1-B-2.6 | Annex D Table D.1, type b, lambda_bar=2.6 | 0.722518082466 | 0.723 | 0.000482 | 0.001 | pass |
| AXIAL-D1-C-2.6 | Annex D Table D.1, type c, lambda_bar=2.6 | 0.635453503106 | 0.635 | 0.000454 | 0.001 | pass |
| AXIAL-D1-A-2.8 | Annex D Table D.1, type a, lambda_bar=2.8 | 0.746723110309 | 0.747 | 0.000277 | 0.001 | pass |
| AXIAL-D1-B-2.8 | Annex D Table D.1, type b, lambda_bar=2.8 | 0.683242791394 | 0.683 | 0.000243 | 0.001 | pass |
| AXIAL-D1-C-2.8 | Annex D Table D.1, type c, lambda_bar=2.8 | 0.59846084768 | 0.598 | 0.000461 | 0.001 | pass |
| AXIAL-D1-A-3 | Annex D Table D.1, type a, lambda_bar=3 | 0.704494132644 | 0.704 | 0.000494 | 0.001 | pass |
| AXIAL-D1-B-3 | Annex D Table D.1, type b, lambda_bar=3 | 0.642786444889 | 0.643 | 0.000214 | 0.001 | pass |
| AXIAL-D1-C-3 | Annex D Table D.1, type c, lambda_bar=3 | 0.561985509484 | 0.562 | 1.45e-05 | 0.001 | pass |
| AXIAL-D1-A-3.2 | Annex D Table D.1, type a, lambda_bar=3.2 | 0.660322829835 | 0.66 | 0.000323 | 0.001 | pass |
| AXIAL-D1-B-3.2 | Annex D Table D.1, type b, lambda_bar=3.2 | 0.602121773018 | 0.602 | 0.000122 | 0.001 | pass |
| AXIAL-D1-C-3.2 | Annex D Table D.1, type c, lambda_bar=3.2 | 0.526533068988 | 0.527 | 0.000467 | 0.001 | pass |
| AXIAL-D1-A-3.4 | Annex D Table D.1, type a, lambda_bar=3.4 | 0.615744654821 | 0.616 | 0.000255 | 0.001 | pass |
| AXIAL-D1-B-3.4 | Annex D Table D.1, type b, lambda_bar=3.4 | 0.562181792232 | 0.562 | 0.000182 | 0.001 | pass |
| AXIAL-D1-C-3.4 | Annex D Table D.1, type c, lambda_bar=3.4 | 0.492520224464 | 0.493 | 0.00048 | 0.001 | pass |
| AXIAL-D1-A-3.6 | Annex D Table D.1, type a, lambda_bar=3.6 | 0.572147961979 | 0.572 | 0.000148 | 0.001 | pass |
| AXIAL-D1-B-3.6 | Annex D Table D.1, type b, lambda_bar=3.6 | 0.523732135914 | 0.524 | 0.000268 | 0.001 | pass |
| AXIAL-D1-C-3.6 | Annex D Table D.1, type c, lambda_bar=3.6 | 0.460250800388 | 0.46 | 0.000251 | 0.001 | pass |
| AXIAL-D1-A-3.8 | Annex D Table D.1, type a, lambda_bar=3.8 | 0.526315789474 | 0.526 | 0.000316 | 0.001 | pass |
| AXIAL-D1-B-3.8 | Annex D Table D.1, type b, lambda_bar=3.8 | 0.487312364487 | 0.487 | 0.000312 | 0.001 | pass |
| AXIAL-D1-C-3.8 | Annex D Table D.1, type c, lambda_bar=3.8 | 0.429913952468 | 0.43 | 8.6e-05 | 0.001 | pass |
| AXIAL-D1-A-4 | Annex D Table D.1, type a, lambda_bar=4 | 0.475 | 0.475 | 0 | 0.001 | pass |
| AXIAL-D1-B-4 | Annex D Table D.1, type b, lambda_bar=4 | 0.45323944547 | 0.453 | 0.000239 | 0.001 | pass |
| AXIAL-D1-C-4 | Annex D Table D.1, type c, lambda_bar=4 | 0.401597637627 | 0.402 | 0.000402 | 0.001 | pass |
| AXIAL-D1-A-4.2 | Annex D Table D.1, type a, lambda_bar=4.2 | 0.430839002268 | 0.431 | 0.000161 | 0.001 | pass |
| AXIAL-D1-B-4.2 | Annex D Table D.1, type b, lambda_bar=4.2 | 0.421646986024 | 0.422 | 0.000353 | 0.001 | pass |
| AXIAL-D1-C-4.2 | Annex D Table D.1, type c, lambda_bar=4.2 | 0.375309399304 | 0.375 | 0.000309 | 0.001 | pass |
| AXIAL-D1-A-4.4 | Annex D Table D.1, type a, lambda_bar=4.4 | 0.392561983471 | 0.393 | 0.000438 | 0.001 | pass |
| AXIAL-D1-B-4.4 | Annex D Table D.1, type b, lambda_bar=4.4 | 0.392535274128 | 0.392 | 0.000535 | 0.001 | pass |
| AXIAL-D1-C-4.4 | Annex D Table D.1, type c, lambda_bar=4.4 | 0.35099832305 | 0.351 | 1.68e-06 | 0.001 | pass |
| AXIAL-D1-A-4.6 | Annex D Table D.1, type a, lambda_bar=4.6 | 0.359168241966 | 0.359 | 0.000168 | 0.001 | pass |
| AXIAL-D1-B-4.6 | Annex D Table D.1, type b, lambda_bar=4.6 | 0.359168241966 | 0.359 | 0.000168 | 0.001 | pass |
| AXIAL-D1-C-4.6 | Annex D Table D.1, type c, lambda_bar=4.6 | 0.328574586204 | 0.329 | 0.000425 | 0.001 | pass |
| AXIAL-D1-A-4.8 | Annex D Table D.1, type a, lambda_bar=4.8 | 0.329861111111 | 0.33 | 0.000139 | 0.001 | pass |
| AXIAL-D1-B-4.8 | Annex D Table D.1, type b, lambda_bar=4.8 | 0.329861111111 | 0.33 | 0.000139 | 0.001 | pass |
| AXIAL-D1-C-4.8 | Annex D Table D.1, type c, lambda_bar=4.8 | 0.307925144623 | 0.308 | 7.49e-05 | 0.001 | pass |
| AXIAL-D1-A-5 | Annex D Table D.1, type a, lambda_bar=5 | 0.304 | 0.304 | 0 | 0.001 | pass |
| AXIAL-D1-B-5 | Annex D Table D.1, type b, lambda_bar=5 | 0.304 | 0.304 | 0 | 0.001 | pass |
| AXIAL-D1-C-5 | Annex D Table D.1, type c, lambda_bar=5 | 0.288925423404 | 0.289 | 7.46e-05 | 0.001 | pass |
| AXIAL-D1-A-5.2 | Annex D Table D.1, type a, lambda_bar=5.2 | 0.281065088757 | 0.281 | 6.51e-05 | 0.001 | pass |
| AXIAL-D1-B-5.2 | Annex D Table D.1, type b, lambda_bar=5.2 | 0.281065088757 | 0.281 | 6.51e-05 | 0.001 | pass |
| AXIAL-D1-C-5.2 | Annex D Table D.1, type c, lambda_bar=5.2 | 0.271447524504 | 0.271 | 0.000448 | 0.001 | pass |
| AXIAL-D1-A-5.4 | Annex D Table D.1, type a, lambda_bar=5.4 | 0.260631001372 | 0.261 | 0.000369 | 0.001 | pass |
| AXIAL-D1-B-5.4 | Annex D Table D.1, type b, lambda_bar=5.4 | 0.260631001372 | 0.261 | 0.000369 | 0.001 | pass |
| AXIAL-D1-C-5.4 | Annex D Table D.1, type c, lambda_bar=5.4 | 0.25536567437 | 0.255 | 0.000366 | 0.001 | pass |
| AXIAL-D1-A-5.6 | Annex D Table D.1, type a, lambda_bar=5.6 | 0.242346938776 | 0.242 | 0.000347 | 0.001 | pass |
| AXIAL-D1-B-5.6 | Annex D Table D.1, type b, lambda_bar=5.6 | 0.242346938776 | 0.242 | 0.000347 | 0.001 | pass |
| AXIAL-D1-C-5.6 | Annex D Table D.1, type c, lambda_bar=5.6 | 0.240559616719 | 0.241 | 0.00044 | 0.001 | pass |
| AXIAL-D1-A-5.8 | Annex D Table D.1, type a, lambda_bar=5.8 | 0.225921521998 | 0.226 | 7.85e-05 | 0.001 | pass |
| AXIAL-D1-B-5.8 | Annex D Table D.1, type b, lambda_bar=5.8 | 0.225921521998 | 0.226 | 7.85e-05 | 0.001 | pass |
| AXIAL-D1-C-5.8 | Annex D Table D.1, type c, lambda_bar=5.8 | 0.225921521998 | 0.226 | 7.85e-05 | 0.001 | pass |
| AXIAL-D1-A-6 | Annex D Table D.1, type a, lambda_bar=6 | 0.211111111111 | 0.211 | 0.000111 | 0.001 | pass |
| AXIAL-D1-B-6 | Annex D Table D.1, type b, lambda_bar=6 | 0.211111111111 | 0.211 | 0.000111 | 0.001 | pass |
| AXIAL-D1-C-6 | Annex D Table D.1, type c, lambda_bar=6 | 0.211111111111 | 0.211 | 0.000111 | 0.001 | pass |
| AXIAL-D1-A-6.2 | Annex D Table D.1, type a, lambda_bar=6.2 | 0.197710718002 | 0.198 | 0.000289 | 0.001 | pass |
| AXIAL-D1-B-6.2 | Annex D Table D.1, type b, lambda_bar=6.2 | 0.197710718002 | 0.198 | 0.000289 | 0.001 | pass |
| AXIAL-D1-C-6.2 | Annex D Table D.1, type c, lambda_bar=6.2 | 0.197710718002 | 0.198 | 0.000289 | 0.001 | pass |
| AXIAL-D1-A-6.4 | Annex D Table D.1, type a, lambda_bar=6.4 | 0.185546875 | 0.186 | 0.000453 | 0.001 | pass |
| AXIAL-D1-B-6.4 | Annex D Table D.1, type b, lambda_bar=6.4 | 0.185546875 | 0.186 | 0.000453 | 0.001 | pass |
| AXIAL-D1-C-6.4 | Annex D Table D.1, type c, lambda_bar=6.4 | 0.185546875 | 0.186 | 0.000453 | 0.001 | pass |
| AXIAL-D1-A-6.6 | Annex D Table D.1, type a, lambda_bar=6.6 | 0.174471992654 | 0.174 | 0.000472 | 0.001 | pass |
| AXIAL-D1-B-6.6 | Annex D Table D.1, type b, lambda_bar=6.6 | 0.174471992654 | 0.174 | 0.000472 | 0.001 | pass |
| AXIAL-D1-C-6.6 | Annex D Table D.1, type c, lambda_bar=6.6 | 0.174471992654 | 0.174 | 0.000472 | 0.001 | pass |
| AXIAL-D1-A-6.8 | Annex D Table D.1, type a, lambda_bar=6.8 | 0.164359861592 | 0.164 | 0.00036 | 0.001 | pass |
| AXIAL-D1-B-6.8 | Annex D Table D.1, type b, lambda_bar=6.8 | 0.164359861592 | 0.164 | 0.00036 | 0.001 | pass |
| AXIAL-D1-C-6.8 | Annex D Table D.1, type c, lambda_bar=6.8 | 0.164359861592 | 0.164 | 0.00036 | 0.001 | pass |
| AXIAL-D1-A-7 | Annex D Table D.1, type a, lambda_bar=7 | 0.155102040816 | 0.155 | 0.000102 | 0.001 | pass |
| AXIAL-D1-B-7 | Annex D Table D.1, type b, lambda_bar=7 | 0.155102040816 | 0.155 | 0.000102 | 0.001 | pass |
| AXIAL-D1-C-7 | Annex D Table D.1, type c, lambda_bar=7 | 0.155102040816 | 0.155 | 0.000102 | 0.001 | pass |
| AXIAL-D1-A-7.2 | Annex D Table D.1, type a, lambda_bar=7.2 | 0.146604938272 | 0.147 | 0.000395 | 0.001 | pass |
| AXIAL-D1-B-7.2 | Annex D Table D.1, type b, lambda_bar=7.2 | 0.146604938272 | 0.147 | 0.000395 | 0.001 | pass |
| AXIAL-D1-C-7.2 | Annex D Table D.1, type c, lambda_bar=7.2 | 0.146604938272 | 0.147 | 0.000395 | 0.001 | pass |
| AXIAL-D1-A-7.4 | Annex D Table D.1, type a, lambda_bar=7.4 | 0.138787436085 | 0.139 | 0.000213 | 0.001 | pass |
| AXIAL-D1-B-7.4 | Annex D Table D.1, type b, lambda_bar=7.4 | 0.138787436085 | 0.139 | 0.000213 | 0.001 | pass |
| AXIAL-D1-C-7.4 | Annex D Table D.1, type c, lambda_bar=7.4 | 0.138787436085 | 0.139 | 0.000213 | 0.001 | pass |
| AXIAL-D1-A-7.6 | Annex D Table D.1, type a, lambda_bar=7.6 | 0.131578947368 | 0.132 | 0.000421 | 0.001 | pass |
| AXIAL-D1-B-7.6 | Annex D Table D.1, type b, lambda_bar=7.6 | 0.131578947368 | 0.132 | 0.000421 | 0.001 | pass |
| AXIAL-D1-C-7.6 | Annex D Table D.1, type c, lambda_bar=7.6 | 0.131578947368 | 0.132 | 0.000421 | 0.001 | pass |
| AXIAL-D1-A-7.8 | Annex D Table D.1, type a, lambda_bar=7.8 | 0.124917817226 | 0.125 | 8.22e-05 | 0.001 | pass |
| AXIAL-D1-B-7.8 | Annex D Table D.1, type b, lambda_bar=7.8 | 0.124917817226 | 0.125 | 8.22e-05 | 0.001 | pass |
| AXIAL-D1-C-7.8 | Annex D Table D.1, type c, lambda_bar=7.8 | 0.124917817226 | 0.125 | 8.22e-05 | 0.001 | pass |
| AXIAL-D1-A-8 | Annex D Table D.1, type a, lambda_bar=8 | 0.11875 | 0.119 | 0.00025 | 0.001 | pass |
| AXIAL-D1-B-8 | Annex D Table D.1, type b, lambda_bar=8 | 0.11875 | 0.119 | 0.00025 | 0.001 | pass |
| AXIAL-D1-C-8 | Annex D Table D.1, type c, lambda_bar=8 | 0.11875 | 0.119 | 0.00025 | 0.001 | pass |
| AXIAL-D1-A-8.5 | Annex D Table D.1, type a, lambda_bar=8.5 | 0.105190311419 | 0.105 | 0.00019 | 0.001 | pass |
| AXIAL-D1-B-8.5 | Annex D Table D.1, type b, lambda_bar=8.5 | 0.105190311419 | 0.105 | 0.00019 | 0.001 | pass |
| AXIAL-D1-C-8.5 | Annex D Table D.1, type c, lambda_bar=8.5 | 0.105190311419 | 0.105 | 0.00019 | 0.001 | pass |
| AXIAL-D1-A-9 | Annex D Table D.1, type a, lambda_bar=9 | 0.0938271604938 | 0.094 | 0.000173 | 0.001 | pass |
| AXIAL-D1-B-9 | Annex D Table D.1, type b, lambda_bar=9 | 0.0938271604938 | 0.094 | 0.000173 | 0.001 | pass |
| AXIAL-D1-C-9 | Annex D Table D.1, type c, lambda_bar=9 | 0.0938271604938 | 0.094 | 0.000173 | 0.001 | pass |
| AXIAL-D1-A-9.5 | Annex D Table D.1, type a, lambda_bar=9.5 | 0.0842105263158 | 0.084 | 0.000211 | 0.001 | pass |
| AXIAL-D1-B-9.5 | Annex D Table D.1, type b, lambda_bar=9.5 | 0.0842105263158 | 0.084 | 0.000211 | 0.001 | pass |
| AXIAL-D1-C-9.5 | Annex D Table D.1, type c, lambda_bar=9.5 | 0.0842105263158 | 0.084 | 0.000211 | 0.001 | pass |
| AXIAL-D1-A-10 | Annex D Table D.1, type a, lambda_bar=10 | 0.076 | 0.076 | 0 | 0.001 | pass |
| AXIAL-D1-B-10 | Annex D Table D.1, type b, lambda_bar=10 | 0.076 | 0.076 | 0 | 0.001 | pass |
| AXIAL-D1-C-10 | Annex D Table D.1, type c, lambda_bar=10 | 0.076 | 0.076 | 0 | 0.001 | pass |
| BEND-10A-0 | Table 10a, normalized ratio=0 | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-10A-0.1 | Table 10a, normalized ratio=0.1 | 1.636 | 1.636 | 0 | 1e-12 | pass |
| BEND-10A-0.2 | Table 10a, normalized ratio=0.2 | 1.845 | 1.845 | 0 | 1e-12 | pass |
| BEND-10A-0.3 | Table 10a, normalized ratio=0.3 | 2.054 | 2.054 | 0 | 1e-12 | pass |
| BEND-10A-0.4 | Table 10a, normalized ratio=0.4 | 2.263 | 2.263 | 0 | 1e-12 | pass |
| BEND-10A-0.5 | Table 10a, normalized ratio=0.5 | 2.472 | 2.472 | 0 | 1e-12 | pass |
| BEND-10A-0.6 | Table 10a, normalized ratio=0.6 | 2.681 | 2.681 | 0 | 1e-12 | pass |
| BEND-10A-0.7 | Table 10a, normalized ratio=0.7 | 2.89 | 2.89 | 0 | 1e-12 | pass |
| BEND-10A-0.8 | Table 10a, normalized ratio=0.8 | 3.099 | 3.099 | 0 | 1e-12 | pass |
| BEND-10A-0.9 | Table 10a, normalized ratio=0.9 | 3.308 | 3.308 | 0 | 1e-12 | pass |
| BEND-10A-0.99 | Table 10a, normalized ratio=0.99 | 3.496 | 3.496 | 0 | 1e-12 | pass |
| BEND-E1-1-CX-0.25 | Annex E Table E.1, type 1, A_f/A_w=0.25, c_x | 1.19 | 1.19 | 0 | 1e-12 | pass |
| BEND-E1-1-CY-0.25 | Annex E Table E.1, type 1, A_f/A_w=0.25, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-1-CX-0.5 | Annex E Table E.1, type 1, A_f/A_w=0.5, c_x | 1.12 | 1.12 | 0 | 1e-12 | pass |
| BEND-E1-1-CY-0.5 | Annex E Table E.1, type 1, A_f/A_w=0.5, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-1-CX-1 | Annex E Table E.1, type 1, A_f/A_w=1, c_x | 1.07 | 1.07 | 0 | 1e-12 | pass |
| BEND-E1-1-CY-1 | Annex E Table E.1, type 1, A_f/A_w=1, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-1-CX-2 | Annex E Table E.1, type 1, A_f/A_w=2, c_x | 1.04 | 1.04 | 0 | 1e-12 | pass |
| BEND-E1-1-CY-2 | Annex E Table E.1, type 1, A_f/A_w=2, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-1-N | Annex E Table E.1, type 1, n when M_y=0 | 1.5 | 1.5 | 0 | 1e-12 | pass |
| BEND-E1-2-CX-0.5 | Annex E Table E.1, type 2, A_f/A_w=0.5, c_x | 1.4 | 1.4 | 0 | 1e-12 | pass |
| BEND-E1-2-CY-0.5 | Annex E Table E.1, type 2, A_f/A_w=0.5, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-2-CX-1 | Annex E Table E.1, type 2, A_f/A_w=1, c_x | 1.28 | 1.28 | 0 | 1e-12 | pass |
| BEND-E1-2-CY-1 | Annex E Table E.1, type 2, A_f/A_w=1, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-2-CX-2 | Annex E Table E.1, type 2, A_f/A_w=2, c_x | 1.18 | 1.18 | 0 | 1e-12 | pass |
| BEND-E1-2-CY-2 | Annex E Table E.1, type 2, A_f/A_w=2, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-2-N | Annex E Table E.1, type 2, n when M_y=0 | 2 | 2 | 0 | 1e-12 | pass |
| BEND-E1-3-CX-0.25 | Annex E Table E.1, type 3, A_f/A_w=0.25, c_x | 1.19 | 1.19 | 0 | 1e-12 | pass |
| BEND-E1-3-CY-0.25 | Annex E Table E.1, type 3, A_f/A_w=0.25, c_y | 1.07 | 1.07 | 0 | 1e-12 | pass |
| BEND-E1-3-CX-0.5 | Annex E Table E.1, type 3, A_f/A_w=0.5, c_x | 1.12 | 1.12 | 0 | 1e-12 | pass |
| BEND-E1-3-CY-0.5 | Annex E Table E.1, type 3, A_f/A_w=0.5, c_y | 1.12 | 1.12 | 0 | 1e-12 | pass |
| BEND-E1-3-CX-1 | Annex E Table E.1, type 3, A_f/A_w=1, c_x | 1.07 | 1.07 | 0 | 1e-12 | pass |
| BEND-E1-3-CY-1 | Annex E Table E.1, type 3, A_f/A_w=1, c_y | 1.19 | 1.19 | 0 | 1e-12 | pass |
| BEND-E1-3-CX-2 | Annex E Table E.1, type 3, A_f/A_w=2, c_x | 1.04 | 1.04 | 0 | 1e-12 | pass |
| BEND-E1-3-CY-2 | Annex E Table E.1, type 3, A_f/A_w=2, c_y | 1.26 | 1.26 | 0 | 1e-12 | pass |
| BEND-E1-3-N | Annex E Table E.1, type 3, n when M_y=0 | 1.5 | 1.5 | 0 | 1e-12 | pass |
| BEND-E1-4-CX-0.5 | Annex E Table E.1, type 4, A_f/A_w=0.5, c_x | 1.4 | 1.4 | 0 | 1e-12 | pass |
| BEND-E1-4-CY-0.5 | Annex E Table E.1, type 4, A_f/A_w=0.5, c_y | 1.12 | 1.12 | 0 | 1e-12 | pass |
| BEND-E1-4-CX-1 | Annex E Table E.1, type 4, A_f/A_w=1, c_x | 1.28 | 1.28 | 0 | 1e-12 | pass |
| BEND-E1-4-CY-1 | Annex E Table E.1, type 4, A_f/A_w=1, c_y | 1.2 | 1.2 | 0 | 1e-12 | pass |
| BEND-E1-4-CX-2 | Annex E Table E.1, type 4, A_f/A_w=2, c_x | 1.18 | 1.18 | 0 | 1e-12 | pass |
| BEND-E1-4-CY-2 | Annex E Table E.1, type 4, A_f/A_w=2, c_y | 1.31 | 1.31 | 0 | 1e-12 | pass |
| BEND-E1-4-N | Annex E Table E.1, type 4, n when M_y=0 | 2 | 2 | 0 | 1e-12 | pass |
| BEND-E1-5a-CX-constant | Annex E Table E.1, type 5a, A_f/A_w=constant, c_x | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-5a-CY-constant | Annex E Table E.1, type 5a, A_f/A_w=constant, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-5a-N | Annex E Table E.1, type 5a, n when M_y=0 | 2 | 2 | 0 | 1e-12 | pass |
| BEND-E1-5b-CX-constant | Annex E Table E.1, type 5b, A_f/A_w=constant, c_x | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-5b-CY-constant | Annex E Table E.1, type 5b, A_f/A_w=constant, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-5b-N | Annex E Table E.1, type 5b, n when M_y=0 | 3 | 3 | 0 | 1e-12 | pass |
| BEND-E1-6-CX-0.25 | Annex E Table E.1, type 6, A_f/A_w=0.25, c_x | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-6-CY-0.25 | Annex E Table E.1, type 6, A_f/A_w=0.25, c_y | 1.04 | 1.04 | 0 | 1e-12 | pass |
| BEND-E1-6-CX-0.5 | Annex E Table E.1, type 6, A_f/A_w=0.5, c_x | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-6-CY-0.5 | Annex E Table E.1, type 6, A_f/A_w=0.5, c_y | 1.07 | 1.07 | 0 | 1e-12 | pass |
| BEND-E1-6-CX-1 | Annex E Table E.1, type 6, A_f/A_w=1, c_x | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-6-CY-1 | Annex E Table E.1, type 6, A_f/A_w=1, c_y | 1.12 | 1.12 | 0 | 1e-12 | pass |
| BEND-E1-6-CX-2 | Annex E Table E.1, type 6, A_f/A_w=2, c_x | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-6-CY-2 | Annex E Table E.1, type 6, A_f/A_w=2, c_y | 1.19 | 1.19 | 0 | 1e-12 | pass |
| BEND-E1-6-N | Annex E Table E.1, type 6, n when M_y=0 | 3 | 3 | 0 | 1e-12 | pass |
| BEND-E1-7-CX-constant | Annex E Table E.1, type 7, A_f/A_w=constant, c_x | 1.26 | 1.26 | 0 | 1e-12 | pass |
| BEND-E1-7-CY-constant | Annex E Table E.1, type 7, A_f/A_w=constant, c_y | 1.26 | 1.26 | 0 | 1e-12 | pass |
| BEND-E1-7-N | Annex E Table E.1, type 7, n when M_y=0 | 1.5 | 1.5 | 0 | 1e-12 | pass |
| BEND-E1-8a-CX-constant | Annex E Table E.1, type 8a, A_f/A_w=constant, c_x | 1.6 | 1.6 | 0 | 1e-12 | pass |
| BEND-E1-8a-CY-constant | Annex E Table E.1, type 8a, A_f/A_w=constant, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-8a-N | Annex E Table E.1, type 8a, n when M_y=0 | 3 | 3 | 0 | 1e-12 | pass |
| BEND-E1-8b-CX-constant | Annex E Table E.1, type 8b, A_f/A_w=constant, c_x | 1.6 | 1.6 | 0 | 1e-12 | pass |
| BEND-E1-8b-CY-constant | Annex E Table E.1, type 8b, A_f/A_w=constant, c_y | 1.47 | 1.47 | 0 | 1e-12 | pass |
| BEND-E1-8b-N | Annex E Table E.1, type 8b, n when M_y=0 | 1 | 1 | 0 | 1e-12 | pass |
| BEND-E1-9a-CX-0.5 | Annex E Table E.1, type 9a, A_f/A_w=0.5, c_x | 1.6 | 1.6 | 0 | 1e-12 | pass |
| BEND-E1-9a-CY-0.5 | Annex E Table E.1, type 9a, A_f/A_w=0.5, c_y | 1.07 | 1.07 | 0 | 1e-12 | pass |
| BEND-E1-9a-CX-1 | Annex E Table E.1, type 9a, A_f/A_w=1, c_x | 1.6 | 1.6 | 0 | 1e-12 | pass |
| BEND-E1-9a-CY-1 | Annex E Table E.1, type 9a, A_f/A_w=1, c_y | 1.12 | 1.12 | 0 | 1e-12 | pass |
| BEND-E1-9a-CX-2 | Annex E Table E.1, type 9a, A_f/A_w=2, c_x | 1.6 | 1.6 | 0 | 1e-12 | pass |
| BEND-E1-9a-CY-2 | Annex E Table E.1, type 9a, A_f/A_w=2, c_y | 1.19 | 1.19 | 0 | 1e-12 | pass |
| BEND-E1-9a-N | Annex E Table E.1, type 9a, n when M_y=0 | 3 | 3 | 0 | 1e-12 | pass |
| BEND-E1-9b-CX-0.5 | Annex E Table E.1, type 9b, A_f/A_w=0.5, c_x | 1.6 | 1.6 | 0 | 1e-12 | pass |
| BEND-E1-9b-CY-0.5 | Annex E Table E.1, type 9b, A_f/A_w=0.5, c_y | 1.07 | 1.07 | 0 | 1e-12 | pass |
| BEND-E1-9b-CX-1 | Annex E Table E.1, type 9b, A_f/A_w=1, c_x | 1.6 | 1.6 | 0 | 1e-12 | pass |
| BEND-E1-9b-CY-1 | Annex E Table E.1, type 9b, A_f/A_w=1, c_y | 1.12 | 1.12 | 0 | 1e-12 | pass |
| BEND-E1-9b-CX-2 | Annex E Table E.1, type 9b, A_f/A_w=2, c_x | 1.6 | 1.6 | 0 | 1e-12 | pass |
| BEND-E1-9b-CY-2 | Annex E Table E.1, type 9b, A_f/A_w=2, c_y | 1.19 | 1.19 | 0 | 1e-12 | pass |
| BEND-E1-9b-N | Annex E Table E.1, type 9b, n when M_y=0 | 1 | 1 | 0 | 1e-12 | pass |
| BLS-EQ-078 | 8.5.2 equation (78) | 150 | 150 | 0 | 1e-12 | pass |
| BLS-EQ-079 | 8.5.2 equation (79) | 20 | 20 | 0 | 1e-12 | pass |
| BLS-EQ-081 | 8.5.3 equation (81) | 1183.33333333 | 1183.33333333 | 0 | 1e-12 | pass |
| BLS-EQ-082 | 8.5.3 equation (82) | 1753.7 | 1753.7 | 0 | 1e-12 | pass |
| BLS-EQ-083 | 8.5.3 equation (83) | 279.187222222 | 279.187222222 | 0 | 1e-12 | pass |
| BLS-EQ-084 | 8.5.4 equation (84) | 2 | 2 | 0 | 1e-12 | pass |
| BLS-EQ-090 | 8.5.12 equation (90) | 528.0625 | 528.0625 | 0 | 1e-12 | pass |
| BLS-EQ-093 | 8.5.12 equation (93) | 6.25 | 6.25 | 0 | 1e-12 | pass |
| BLS-EQ-097 | 8.5.18 equation (97) | 0.666145629724 | 0.666145629724 | 0 | 1e-12 | pass |
| BLS-EQ-098 | 8.5.18 equation (98) | 1.99843688917 | 1.99843688917 | 0 | 1e-12 | pass |
| BLS-EQ-099 | 8.5.19 equation (99) | 0.35 | 0.35 | 0 | 1e-12 | pass |
| BLS-EQ-100 | 8.5.19 equation (100) | 1.125 | 1.125 | 0 | 1e-12 | pass |
| BLS-T14-0.1-0.5 | Table 14 | 56.7 | 56.7 | 0 | 1e-12 | pass |
| BLS-T14-0.1-0.6 | Table 14 | 46.6 | 46.6 | 0 | 1e-12 | pass |
| BLS-T14-0.1-0.67 | Table 14 | 41.8 | 41.8 | 0 | 1e-12 | pass |
| BLS-T14-0.1-0.8 | Table 14 | 34.9 | 34.9 | 0 | 1e-12 | pass |
| BLS-T14-0.1-1.0 | Table 14 | 28.5 | 28.5 | 0 | 1e-12 | pass |
| BLS-T14-0.1-1.2 | Table 14 | 24.5 | 24.5 | 0 | 1e-12 | pass |
| BLS-T14-0.1-1.4 | Table 14 | 21.7 | 21.7 | 0 | 1e-12 | pass |
| BLS-T14-0.1-1.6 | Table 14 | 19.5 | 19.5 | 0 | 1e-12 | pass |
| BLS-T14-0.1-1.8 | Table 14 | 17.7 | 17.7 | 0 | 1e-12 | pass |
| BLS-T14-0.1-2.0 | Table 14 | 16.2 | 16.2 | 0 | 1e-12 | pass |
| BLS-T14-0.15-0.5 | Table 14 | 38.9 | 38.9 | 0 | 1e-12 | pass |
| BLS-T14-0.15-0.6 | Table 14 | 31.3 | 31.3 | 0 | 1e-12 | pass |
| BLS-T14-0.15-0.67 | Table 14 | 27.9 | 27.9 | 0 | 1e-12 | pass |
| BLS-T14-0.15-0.8 | Table 14 | 23 | 23 | 0 | 1e-12 | pass |
| BLS-T14-0.15-1.0 | Table 14 | 18.6 | 18.6 | 0 | 1e-12 | pass |
| BLS-T14-0.15-1.2 | Table 14 | 16.2 | 16.2 | 0 | 1e-12 | pass |
| BLS-T14-0.15-1.4 | Table 14 | 14.6 | 14.6 | 0 | 1e-12 | pass |
| BLS-T14-0.15-1.6 | Table 14 | 13.6 | 13.6 | 0 | 1e-12 | pass |
| BLS-T14-0.15-1.8 | Table 14 | 12.7 | 12.7 | 0 | 1e-12 | pass |
| BLS-T14-0.15-2.0 | Table 14 | 12 | 12 | 0 | 1e-12 | pass |
| BLS-T14-0.2-0.5 | Table 14 | 33.9 | 33.9 | 0 | 1e-12 | pass |
| BLS-T14-0.2-0.6 | Table 14 | 26.7 | 26.7 | 0 | 1e-12 | pass |
| BLS-T14-0.2-0.67 | Table 14 | 23.5 | 23.5 | 0 | 1e-12 | pass |
| BLS-T14-0.2-0.8 | Table 14 | 19.2 | 19.2 | 0 | 1e-12 | pass |
| BLS-T14-0.2-1.0 | Table 14 | 15.4 | 15.4 | 0 | 1e-12 | pass |
| BLS-T14-0.2-1.2 | Table 14 | 13.3 | 13.3 | 0 | 1e-12 | pass |
| BLS-T14-0.2-1.4 | Table 14 | 12.1 | 12.1 | 0 | 1e-12 | pass |
| BLS-T14-0.2-1.6 | Table 14 | 11.3 | 11.3 | 0 | 1e-12 | pass |
| BLS-T14-0.2-1.8 | Table 14 | 10.7 | 10.7 | 0 | 1e-12 | pass |
| BLS-T14-0.2-2.0 | Table 14 | 10.2 | 10.2 | 0 | 1e-12 | pass |
| BLS-T14-0.25-0.5 | Table 14 | 30.6 | 30.6 | 0 | 1e-12 | pass |
| BLS-T14-0.25-0.6 | Table 14 | 24.9 | 24.9 | 0 | 1e-12 | pass |
| BLS-T14-0.25-0.67 | Table 14 | 20.3 | 20.3 | 0 | 1e-12 | pass |
| BLS-T14-0.25-0.8 | Table 14 | 16.2 | 16.2 | 0 | 1e-12 | pass |
| BLS-T14-0.25-1.0 | Table 14 | 12.9 | 12.9 | 0 | 1e-12 | pass |
| BLS-T14-0.25-1.2 | Table 14 | 11.1 | 11.1 | 0 | 1e-12 | pass |
| BLS-T14-0.25-1.4 | Table 14 | 10 | 10 | 0 | 1e-12 | pass |
| BLS-T14-0.25-1.6 | Table 14 | 9.4 | 9.4 | 0 | 1e-12 | pass |
| BLS-T14-0.25-1.8 | Table 14 | 9 | 9 | 0 | 1e-12 | pass |
| BLS-T14-0.25-2.0 | Table 14 | 8.7 | 8.7 | 0 | 1e-12 | pass |
| BLS-T14-0.3-0.5 | Table 14 | 28.9 | 28.9 | 0 | 1e-12 | pass |
| BLS-T14-0.3-0.6 | Table 14 | 21.6 | 21.6 | 0 | 1e-12 | pass |
| BLS-T14-0.3-0.67 | Table 14 | 18.5 | 18.5 | 0 | 1e-12 | pass |
| BLS-T14-0.3-0.8 | Table 14 | 14.5 | 14.5 | 0 | 1e-12 | pass |
| BLS-T14-0.3-1.0 | Table 14 | 11.3 | 11.3 | 0 | 1e-12 | pass |
| BLS-T14-0.3-1.2 | Table 14 | 9.6 | 9.6 | 0 | 1e-12 | pass |
| BLS-T14-0.3-1.4 | Table 14 | 8.7 | 8.7 | 0 | 1e-12 | pass |
| BLS-T14-0.3-1.6 | Table 14 | 8.1 | 8.1 | 0 | 1e-12 | pass |
| BLS-T14-0.3-1.8 | Table 14 | 7.8 | 7.8 | 0 | 1e-12 | pass |
| BLS-T14-0.3-2.0 | Table 14 | 7.6 | 7.6 | 0 | 1e-12 | pass |
| BLS-T14-0.35-0.5 | Table 14 | 28 | 28 | 0 | 1e-12 | pass |
| BLS-T14-0.35-0.6 | Table 14 | 20.6 | 20.6 | 0 | 1e-12 | pass |
| BLS-T14-0.35-0.67 | Table 14 | 17.4 | 17.4 | 0 | 1e-12 | pass |
| BLS-T14-0.35-0.8 | Table 14 | 13.4 | 13.4 | 0 | 1e-12 | pass |
| BLS-T14-0.35-1.0 | Table 14 | 10.2 | 10.2 | 0 | 1e-12 | pass |
| BLS-T14-0.35-1.2 | Table 14 | 8.6 | 8.6 | 0 | 1e-12 | pass |
| BLS-T14-0.35-1.4 | Table 14 | 7.7 | 7.7 | 0 | 1e-12 | pass |
| BLS-T14-0.35-1.6 | Table 14 | 7.2 | 7.2 | 0 | 1e-12 | pass |
| BLS-T14-0.35-1.8 | Table 14 | 6.9 | 6.9 | 0 | 1e-12 | pass |
| BLS-T14-0.35-2.0 | Table 14 | 6.7 | 6.7 | 0 | 1e-12 | pass |
| BLS-T14-0.4-0.5 | Table 14 | 27.4 | 27.4 | 0 | 1e-12 | pass |
| BLS-T14-0.4-0.6 | Table 14 | 20 | 20 | 0 | 1e-12 | pass |
| BLS-T14-0.4-0.67 | Table 14 | 16.8 | 16.8 | 0 | 1e-12 | pass |
| BLS-T14-0.4-0.8 | Table 14 | 12.7 | 12.7 | 0 | 1e-12 | pass |
| BLS-T14-0.4-1.0 | Table 14 | 9.5 | 9.5 | 0 | 1e-12 | pass |
| BLS-T14-0.4-1.2 | Table 14 | 7.9 | 7.9 | 0 | 1e-12 | pass |
| BLS-T14-0.4-1.4 | Table 14 | 7 | 7 | 0 | 1e-12 | pass |
| BLS-T14-0.4-1.6 | Table 14 | 6.6 | 6.6 | 0 | 1e-12 | pass |
| BLS-T14-0.4-1.8 | Table 14 | 6.3 | 6.3 | 0 | 1e-12 | pass |
| BLS-T14-0.4-2.0 | Table 14 | 6.1 | 6.1 | 0 | 1e-12 | pass |
| BLS-T15-1.0-0.5 | Table 15 | 1.56 | 1.56 | 0 | 1e-12 | pass |
| BLS-T15-1.0-0.6 | Table 15 | 1.56 | 1.56 | 0 | 1e-12 | pass |
| BLS-T15-1.0-0.67 | Table 15 | 1.56 | 1.56 | 0 | 1e-12 | pass |
| BLS-T15-1.0-0.8 | Table 15 | 1.56 | 1.56 | 0 | 1e-12 | pass |
| BLS-T15-1.0-1.0 | Table 15 | 1.56 | 1.56 | 0 | 1e-12 | pass |
| BLS-T15-1.0-1.2 | Table 15 | 1.56 | 1.56 | 0 | 1e-12 | pass |
| BLS-T15-1.0-1.4 | Table 15 | 1.56 | 1.56 | 0 | 1e-12 | pass |
| BLS-T15-1.0-1.6 | Table 15 | 1.56 | 1.56 | 0 | 1e-12 | pass |
| BLS-T15-2.0-0.5 | Table 15 | 1.64 | 1.64 | 0 | 1e-12 | pass |
| BLS-T15-2.0-0.6 | Table 15 | 1.64 | 1.64 | 0 | 1e-12 | pass |
| BLS-T15-2.0-0.67 | Table 15 | 1.64 | 1.64 | 0 | 1e-12 | pass |
| BLS-T15-2.0-0.8 | Table 15 | 1.67 | 1.67 | 0 | 1e-12 | pass |
| BLS-T15-2.0-1.0 | Table 15 | 1.76 | 1.76 | 0 | 1e-12 | pass |
| BLS-T15-2.0-1.2 | Table 15 | 1.82 | 1.82 | 0 | 1e-12 | pass |
| BLS-T15-2.0-1.4 | Table 15 | 1.84 | 1.84 | 0 | 1e-12 | pass |
| BLS-T15-2.0-1.6 | Table 15 | 1.85 | 1.85 | 0 | 1e-12 | pass |
| BLS-T15-4.0-0.5 | Table 15 | 1.66 | 1.66 | 0 | 1e-12 | pass |
| BLS-T15-4.0-0.6 | Table 15 | 1.67 | 1.67 | 0 | 1e-12 | pass |
| BLS-T15-4.0-0.67 | Table 15 | 1.69 | 1.69 | 0 | 1e-12 | pass |
| BLS-T15-4.0-0.8 | Table 15 | 1.75 | 1.75 | 0 | 1e-12 | pass |
| BLS-T15-4.0-1.0 | Table 15 | 1.88 | 1.88 | 0 | 1e-12 | pass |
| BLS-T15-4.0-1.2 | Table 15 | 2.01 | 2.01 | 0 | 1e-12 | pass |
| BLS-T15-4.0-1.4 | Table 15 | 2.09 | 2.09 | 0 | 1e-12 | pass |
| BLS-T15-4.0-1.6 | Table 15 | 2.12 | 2.12 | 0 | 1e-12 | pass |
| BLS-T15-6.0-0.5 | Table 15 | 1.67 | 1.67 | 0 | 1e-12 | pass |
| BLS-T15-6.0-0.6 | Table 15 | 1.68 | 1.68 | 0 | 1e-12 | pass |
| BLS-T15-6.0-0.67 | Table 15 | 1.7 | 1.7 | 0 | 1e-12 | pass |
| BLS-T15-6.0-0.8 | Table 15 | 1.77 | 1.77 | 0 | 1e-12 | pass |
| BLS-T15-6.0-1.0 | Table 15 | 1.92 | 1.92 | 0 | 1e-12 | pass |
| BLS-T15-6.0-1.2 | Table 15 | 2.08 | 2.08 | 0 | 1e-12 | pass |
| BLS-T15-6.0-1.4 | Table 15 | 2.19 | 2.19 | 0 | 1e-12 | pass |
| BLS-T15-6.0-1.6 | Table 15 | 2.26 | 2.26 | 0 | 1e-12 | pass |
| BLS-T15-10.0-0.5 | Table 15 | 1.68 | 1.68 | 0 | 1e-12 | pass |
| BLS-T15-10.0-0.6 | Table 15 | 1.69 | 1.69 | 0 | 1e-12 | pass |
| BLS-T15-10.0-0.67 | Table 15 | 1.71 | 1.71 | 0 | 1e-12 | pass |
| BLS-T15-10.0-0.8 | Table 15 | 1.78 | 1.78 | 0 | 1e-12 | pass |
| BLS-T15-10.0-1.0 | Table 15 | 1.96 | 1.96 | 0 | 1e-12 | pass |
| BLS-T15-10.0-1.2 | Table 15 | 2.14 | 2.14 | 0 | 1e-12 | pass |
| BLS-T15-10.0-1.4 | Table 15 | 2.28 | 2.28 | 0 | 1e-12 | pass |
| BLS-T15-10.0-1.6 | Table 15 | 2.38 | 2.38 | 0 | 1e-12 | pass |
| BLS-T15-30.0-0.5 | Table 15 | 1.68 | 1.68 | 0 | 1e-12 | pass |
| BLS-T15-30.0-0.6 | Table 15 | 1.7 | 1.7 | 0 | 1e-12 | pass |
| BLS-T15-30.0-0.67 | Table 15 | 1.72 | 1.72 | 0 | 1e-12 | pass |
| BLS-T15-30.0-0.8 | Table 15 | 1.8 | 1.8 | 0 | 1e-12 | pass |
| BLS-T15-30.0-1.0 | Table 15 | 1.99 | 1.99 | 0 | 1e-12 | pass |
| BLS-T15-30.0-1.2 | Table 15 | 2.2 | 2.2 | 0 | 1e-12 | pass |
| BLS-T15-30.0-1.4 | Table 15 | 2.38 | 2.38 | 0 | 1e-12 | pass |
| BLS-T15-30.0-1.6 | Table 15 | 2.52 | 2.52 | 0 | 1e-12 | pass |
| BLS-T16-0.9 | Table 16 | 37 | 37 | 0 | 1e-12 | pass |
| BLS-T16-1.0 | Table 16 | 39.2 | 39.2 | 0 | 1e-12 | pass |
| BLS-T16-1.2 | Table 16 | 45.2 | 45.2 | 0 | 1e-12 | pass |
| BLS-T16-1.4 | Table 16 | 52.8 | 52.8 | 0 | 1e-12 | pass |
| BLS-T16-1.6 | Table 16 | 62 | 62 | 0 | 1e-12 | pass |
| BLS-T16-1.8 | Table 16 | 72.6 | 72.6 | 0 | 1e-12 | pass |
| BLS-T16-2.0 | Table 16 | 84.7 | 84.7 | 0 | 1e-12 | pass |
| BLS-T17-1.0 | Table 17 | 10.2 | 10.2 | 0 | 1e-12 | pass |
| BLS-T17-1.2 | Table 17 | 12.7 | 12.7 | 0 | 1e-12 | pass |
| BLS-T17-1.4 | Table 17 | 15.5 | 15.5 | 0 | 1e-12 | pass |
| BLS-T17-1.6 | Table 17 | 20 | 20 | 0 | 1e-12 | pass |
| BLS-T17-1.8 | Table 17 | 25 | 25 | 0 | 1e-12 | pass |
| BLS-T17-2.0 | Table 17 | 30 | 30 | 0 | 1e-12 | pass |
| BLS-T18-0.0-2.2 | Table 18 | 0.24 | 0.24 | 0 | 1e-12 | pass |
| BLS-T18-0.0-2.5 | Table 18 | 0.239 | 0.239 | 0 | 1e-12 | pass |
| BLS-T18-0.0-3.0 | Table 18 | 0.235 | 0.235 | 0 | 1e-12 | pass |
| BLS-T18-0.0-3.5 | Table 18 | 0.226 | 0.226 | 0 | 1e-12 | pass |
| BLS-T18-0.0-4.0 | Table 18 | 0.213 | 0.213 | 0 | 1e-12 | pass |
| BLS-T18-0.0-4.5 | Table 18 | 0.195 | 0.195 | 0 | 1e-12 | pass |
| BLS-T18-0.0-5.0 | Table 18 | 0.173 | 0.173 | 0 | 1e-12 | pass |
| BLS-T18-0.0-5.5 | Table 18 | 0.153 | 0.153 | 0 | 1e-12 | pass |
| BLS-T18-0.5-2.2 | Table 18 | 0.203 | 0.203 | 0 | 1e-12 | pass |
| BLS-T18-0.5-2.5 | Table 18 | 0.202 | 0.202 | 0 | 1e-12 | pass |
| BLS-T18-0.5-3.0 | Table 18 | 0.197 | 0.197 | 0 | 1e-12 | pass |
| BLS-T18-0.5-3.5 | Table 18 | 0.189 | 0.189 | 0 | 1e-12 | pass |
| BLS-T18-0.5-4.0 | Table 18 | 0.176 | 0.176 | 0 | 1e-12 | pass |
| BLS-T18-0.5-4.5 | Table 18 | 0.158 | 0.158 | 0 | 1e-12 | pass |
| BLS-T18-0.5-5.0 | Table 18 | 0.136 | 0.136 | 0 | 1e-12 | pass |
| BLS-T18-0.5-5.5 | Table 18 | 0.116 | 0.116 | 0 | 1e-12 | pass |
| BLS-T18-0.6-2.2 | Table 18 | 0.186 | 0.186 | 0 | 1e-12 | pass |
| BLS-T18-0.6-2.5 | Table 18 | 0.185 | 0.185 | 0 | 1e-12 | pass |
| BLS-T18-0.6-3.0 | Table 18 | 0.181 | 0.181 | 0 | 1e-12 | pass |
| BLS-T18-0.6-3.5 | Table 18 | 0.172 | 0.172 | 0 | 1e-12 | pass |
| BLS-T18-0.6-4.0 | Table 18 | 0.159 | 0.159 | 0 | 1e-12 | pass |
| BLS-T18-0.6-4.5 | Table 18 | 0.141 | 0.141 | 0 | 1e-12 | pass |
| BLS-T18-0.6-5.0 | Table 18 | 0.119 | 0.119 | 0 | 1e-12 | pass |
| BLS-T18-0.6-5.5 | Table 18 | 0.099 | 0.099 | 0 | 1e-12 | pass |
| BLS-T18-0.7-2.2 | Table 18 | 0.167 | 0.167 | 0 | 1e-12 | pass |
| BLS-T18-0.7-2.5 | Table 18 | 0.166 | 0.166 | 0 | 1e-12 | pass |
| BLS-T18-0.7-3.0 | Table 18 | 0.162 | 0.162 | 0 | 1e-12 | pass |
| BLS-T18-0.7-3.5 | Table 18 | 0.152 | 0.152 | 0 | 1e-12 | pass |
| BLS-T18-0.7-4.0 | Table 18 | 0.14 | 0.14 | 0 | 1e-12 | pass |
| BLS-T18-0.7-4.5 | Table 18 | 0.122 | 0.122 | 0 | 1e-12 | pass |
| BLS-T18-0.7-5.0 | Table 18 | 0.1 | 0.1 | 0 | 1e-12 | pass |
| BLS-T18-0.7-5.5 | Table 18 | 0.08 | 0.08 | 0 | 1e-12 | pass |
| BLS-T18-0.8-2.2 | Table 18 | 0.144 | 0.144 | 0 | 1e-12 | pass |
| BLS-T18-0.8-2.5 | Table 18 | 0.143 | 0.143 | 0 | 1e-12 | pass |
| BLS-T18-0.8-3.0 | Table 18 | 0.139 | 0.139 | 0 | 1e-12 | pass |
| BLS-T18-0.8-3.5 | Table 18 | 0.13 | 0.13 | 0 | 1e-12 | pass |
| BLS-T18-0.8-4.0 | Table 18 | 0.117 | 0.117 | 0 | 1e-12 | pass |
| BLS-T18-0.8-4.5 | Table 18 | 0.099 | 0.099 | 0 | 1e-12 | pass |
| BLS-T18-0.8-5.0 | Table 18 | 0.077 | 0.077 | 0 | 1e-12 | pass |
| BLS-T18-0.8-5.5 | Table 18 | 0.057 | 0.057 | 0 | 1e-12 | pass |
| BLS-T18-0.9-2.2 | Table 18 | 0.119 | 0.119 | 0 | 1e-12 | pass |
| BLS-T18-0.9-2.5 | Table 18 | 0.118 | 0.118 | 0 | 1e-12 | pass |
| BLS-T18-0.9-3.0 | Table 18 | 0.114 | 0.114 | 0 | 1e-12 | pass |
| BLS-T18-0.9-3.5 | Table 18 | 0.105 | 0.105 | 0 | 1e-12 | pass |
| BLS-T18-0.9-4.0 | Table 18 | 0.092 | 0.092 | 0 | 1e-12 | pass |
| BLS-T18-0.9-4.5 | Table 18 | 0.074 | 0.074 | 0 | 1e-12 | pass |
| BLS-T18-0.9-5.0 | Table 18 | 0.052 | 0.052 | 0 | 1e-12 | pass |
| BLS-T18-0.9-5.5 | Table 18 | 0.032 | 0.032 | 0 | 1e-12 | pass |
| BPCS-EQ-101 | 8.6.2 equation (101) | 54.7722557505 | 54.7722557505 | 0 | 1e-12 | pass |
| BPCS-EQ-102 | 8.6.2 equation (102) | 5000 | 5000 | 0 | 1e-12 | pass |
| BPCS-EQ-103A | 8.6.2 equation (103) | 480 | 480 | 0 | 1e-12 | pass |
| BPCS-EQ-103B | 8.6.2 equation (103) | 370 | 370 | 0 | 1e-12 | pass |
| BPCS-EQ-104 | 8.6.2 equation (104) | 1120 | 1120 | 0 | 1e-12 | pass |
| BPCS-EQ-105 | 9.1.1 equation (105) | 0.284 | 0.284 | 5.55e-17 | 1e-12 | pass |
| BPCS-EQ-106 | 9.1.1 equation (106) | 0.2024 | 0.2024 | 0 | 1e-12 | pass |
| BPCS-EQ-107 | 9.1.3 equation (107) | 0.065 | 0.065 | 0 | 1e-12 | pass |
| BPCS-EQ-108 | 9.1.3 equation (108) | 0.92 | 0.92 | 0 | 1e-12 | pass |
| BPCS-PROC-MAX | 8.6.2 governing moment | 250 | 250 | 0 | 0 | pass |
| BPCS-PROC-TWO-SIDE | 8.6.2 two-adjacent-side geometry | 500 | 500 | 0 | 1e-12 | pass |
| BPCS-PROC-9.1.1 | 9.1.1 applicability | 1 | 1 | 0 | 0 | pass |
| BPCS-PROC-9.1.2 | 9.1.2 omission | 1 | 1 | 0 | 0 | pass |
| BPCS-PROC-9.1.3 | 9.1.3 applicability | 1 | 1 | 0 | 0 | pass |
| BPCS-E2-A1-1.0 | Annex E Table E.2 | 0.048 | 0.048 | 0 | 0 | pass |
| BPCS-E2-A2-1.0 | Annex E Table E.2 | 0.048 | 0.048 | 0 | 0 | pass |
| BPCS-E2-A1-1.1 | Annex E Table E.2 | 0.055 | 0.055 | 0 | 0 | pass |
| BPCS-E2-A2-1.1 | Annex E Table E.2 | 0.049 | 0.049 | 0 | 0 | pass |
| BPCS-E2-A1-1.2 | Annex E Table E.2 | 0.063 | 0.063 | 0 | 0 | pass |
| BPCS-E2-A2-1.2 | Annex E Table E.2 | 0.05 | 0.05 | 0 | 0 | pass |
| BPCS-E2-A1-1.3 | Annex E Table E.2 | 0.069 | 0.069 | 0 | 0 | pass |
| BPCS-E2-A2-1.3 | Annex E Table E.2 | 0.05 | 0.05 | 0 | 0 | pass |
| BPCS-E2-A1-1.4 | Annex E Table E.2 | 0.075 | 0.075 | 0 | 0 | pass |
| BPCS-E2-A2-1.4 | Annex E Table E.2 | 0.05 | 0.05 | 0 | 0 | pass |
| BPCS-E2-A1-1.5 | Annex E Table E.2 | 0.081 | 0.081 | 0 | 0 | pass |
| BPCS-E2-A2-1.5 | Annex E Table E.2 | 0.05 | 0.05 | 0 | 0 | pass |
| BPCS-E2-A1-1.6 | Annex E Table E.2 | 0.086 | 0.086 | 0 | 0 | pass |
| BPCS-E2-A2-1.6 | Annex E Table E.2 | 0.049 | 0.049 | 0 | 0 | pass |
| BPCS-E2-A1-1.7 | Annex E Table E.2 | 0.091 | 0.091 | 0 | 0 | pass |
| BPCS-E2-A2-1.7 | Annex E Table E.2 | 0.048 | 0.048 | 0 | 0 | pass |
| BPCS-E2-A1-1.8 | Annex E Table E.2 | 0.094 | 0.094 | 0 | 0 | pass |
| BPCS-E2-A2-1.8 | Annex E Table E.2 | 0.048 | 0.048 | 0 | 0 | pass |
| BPCS-E2-A1-1.9 | Annex E Table E.2 | 0.098 | 0.098 | 0 | 0 | pass |
| BPCS-E2-A2-1.9 | Annex E Table E.2 | 0.047 | 0.047 | 0 | 0 | pass |
| BPCS-E2-A1-2.0 | Annex E Table E.2 | 0.1 | 0.1 | 0 | 0 | pass |
| BPCS-E2-A2-2.0 | Annex E Table E.2 | 0.046 | 0.046 | 0 | 0 | pass |
| BPCS-E2-A3-0.5 | Annex E Table E.2 | 0.06 | 0.06 | 0 | 0 | pass |
| BPCS-E2-A3-0.6 | Annex E Table E.2 | 0.074 | 0.074 | 0 | 0 | pass |
| BPCS-E2-A3-0.7 | Annex E Table E.2 | 0.088 | 0.088 | 0 | 0 | pass |
| BPCS-E2-A3-0.8 | Annex E Table E.2 | 0.097 | 0.097 | 0 | 0 | pass |
| BPCS-E2-A3-0.9 | Annex E Table E.2 | 0.107 | 0.107 | 0 | 0 | pass |
| BPCS-E2-A3-1.0 | Annex E Table E.2 | 0.112 | 0.112 | 0 | 0 | pass |
| BPCS-E2-A3-1.2 | Annex E Table E.2 | 0.12 | 0.12 | 0 | 0 | pass |
| BPCS-E2-A3-1.4 | Annex E Table E.2 | 0.126 | 0.126 | 0 | 0 | pass |
| BPCS-E2-A3-2.0 | Annex E Table E.2 | 0.132 | 0.132 | 0 | 0 | pass |
| BPCS-E2-A1-GT2 | Annex E Table E.2 | 0.125 | 0.125 | 0 | 0 | pass |
| BPCS-E2-A2-GT2 | Annex E Table E.2 | 0.037 | 0.037 | 0 | 0 | pass |
| BPCS-E2-A3-GT2 | Annex E Table E.2 | 0.133 | 0.133 | 0 | 0 | pass |
| BC-EQ-109 | 9.2.2 equation (109) | 0.333333333333 | 0.333333333333 | 0 | 1e-12 | pass |
| BC-EQ-110 | 9.2.2 equation (110) | 2.4 | 2.4 | 0 | 1e-12 | pass |
| BC-EQ-111 | 9.2.4 equation (111) | 0.666666666667 | 0.666666666667 | 0 | 1e-12 | pass |
| BC-EQ-112 | 9.2.5 equation (112) | 0.416666666667 | 0.416666666667 | 0 | 1e-12 | pass |
| BC-EQ-113 | 9.2.5 equation (113) | 0.101123595506 | 0.101123595506 | 0 | 1e-12 | pass |
| BC-EQ-114 | 9.2.5 equation (114) | 0.15 | 0.15 | 2.78e-17 | 1e-12 | pass |
| BC-EQ-115 | 9.2.8 equation (115) | 0.25 | 0.25 | 0 | 1e-12 | pass |
| BC-EQ-116 | 9.2.9 equation (116) | 0.4 | 0.4 | 0 | 1e-12 | pass |
| BC-EQ-117 | 9.2.9 equation (117) | 0.487547329015 | 0.487547329015 | 0 | 1e-12 | pass |
| BC-EQ-118 | 9.2.9 equation (118) | 0.12 | 0.12 | 0 | 1e-12 | pass |
| BC-EQ-119 | 9.2.9 equation (119) | 0.12 | 0.12 | 0 | 1e-12 | pass |
| BC-EQ-122 | 9.2.10 equation (122) | 0.946666666667 | 0.946666666667 | 0 | 1e-12 | pass |
| BC-TBL-20 | Table 20 | 80 | 80 | 0 | 1e-12 | pass |
| BC-TBL-21-ALPHA | Table 21 | 0.75 | 0.75 | 0 | 1e-12 | pass |
| BC-TBL-21-BETA | Table 21 | 1 | 1 | 0 | 0 | pass |
| BC-EQ-D1 | Annex D equation (D.1) | 1 | 1 | 0 | 1e-12 | pass |
| BC-EQ-D4 | Annex D equation (D.4) | 6.16947142116 | 6.16947142116 | 0 | 1e-12 | pass |
| BC-D3-0.5-0.1 | Annex D Table D.3 | 0.967 | 0.967 | 0 | 0 | pass |
| BC-D3-0.5-0.25 | Annex D Table D.3 | 0.922 | 0.922 | 0 | 0 | pass |
| BC-D3-0.5-0.5 | Annex D Table D.3 | 0.85 | 0.85 | 0 | 0 | pass |
| BC-D3-0.5-0.75 | Annex D Table D.3 | 0.782 | 0.782 | 0 | 0 | pass |
| BC-D3-0.5-1.0 | Annex D Table D.3 | 0.722 | 0.722 | 0 | 0 | pass |
| BC-D3-0.5-1.25 | Annex D Table D.3 | 0.669 | 0.669 | 0 | 0 | pass |
| BC-D3-0.5-1.5 | Annex D Table D.3 | 0.62 | 0.62 | 0 | 0 | pass |
| BC-D3-0.5-1.75 | Annex D Table D.3 | 0.577 | 0.577 | 0 | 0 | pass |
| BC-D3-0.5-2.0 | Annex D Table D.3 | 0.538 | 0.538 | 0 | 0 | pass |
| BC-D3-0.5-2.5 | Annex D Table D.3 | 0.469 | 0.469 | 0 | 0 | pass |
| BC-D3-0.5-3.0 | Annex D Table D.3 | 0.417 | 0.417 | 0 | 0 | pass |
| BC-D3-0.5-3.5 | Annex D Table D.3 | 0.37 | 0.37 | 0 | 0 | pass |
| BC-D3-0.5-4.0 | Annex D Table D.3 | 0.337 | 0.337 | 0 | 0 | pass |
| BC-D3-0.5-4.5 | Annex D Table D.3 | 0.307 | 0.307 | 0 | 0 | pass |
| BC-D3-0.5-5.0 | Annex D Table D.3 | 0.28 | 0.28 | 0 | 0 | pass |
| BC-D3-0.5-5.5 | Annex D Table D.3 | 0.26 | 0.26 | 0 | 0 | pass |
| BC-D3-0.5-6.0 | Annex D Table D.3 | 0.237 | 0.237 | 0 | 0 | pass |
| BC-D3-0.5-6.5 | Annex D Table D.3 | 0.222 | 0.222 | 0 | 0 | pass |
| BC-D3-0.5-7.0 | Annex D Table D.3 | 0.21 | 0.21 | 0 | 0 | pass |
| BC-D3-0.5-8.0 | Annex D Table D.3 | 0.183 | 0.183 | 0 | 0 | pass |
| BC-D3-0.5-9.0 | Annex D Table D.3 | 0.164 | 0.164 | 0 | 0 | pass |
| BC-D3-0.5-10.0 | Annex D Table D.3 | 0.15 | 0.15 | 0 | 0 | pass |
| BC-D3-0.5-12.0 | Annex D Table D.3 | 0.125 | 0.125 | 0 | 0 | pass |
| BC-D3-0.5-14.0 | Annex D Table D.3 | 0.106 | 0.106 | 0 | 0 | pass |
| BC-D3-0.5-17.0 | Annex D Table D.3 | 0.09 | 0.09 | 0 | 0 | pass |
| BC-D3-0.5-20.0 | Annex D Table D.3 | 0.077 | 0.077 | 0 | 0 | pass |
| BC-D3-1.0-0.1 | Annex D Table D.3 | 0.925 | 0.925 | 0 | 0 | pass |
| BC-D3-1.0-0.25 | Annex D Table D.3 | 0.854 | 0.854 | 0 | 0 | pass |
| BC-D3-1.0-0.5 | Annex D Table D.3 | 0.778 | 0.778 | 0 | 0 | pass |
| BC-D3-1.0-0.75 | Annex D Table D.3 | 0.711 | 0.711 | 0 | 0 | pass |
| BC-D3-1.0-1.0 | Annex D Table D.3 | 0.653 | 0.653 | 0 | 0 | pass |
| BC-D3-1.0-1.25 | Annex D Table D.3 | 0.6 | 0.6 | 0 | 0 | pass |
| BC-D3-1.0-1.5 | Annex D Table D.3 | 0.563 | 0.563 | 0 | 0 | pass |
| BC-D3-1.0-1.75 | Annex D Table D.3 | 0.52 | 0.52 | 0 | 0 | pass |
| BC-D3-1.0-2.0 | Annex D Table D.3 | 0.484 | 0.484 | 0 | 0 | pass |
| BC-D3-1.0-2.5 | Annex D Table D.3 | 0.427 | 0.427 | 0 | 0 | pass |
| BC-D3-1.0-3.0 | Annex D Table D.3 | 0.382 | 0.382 | 0 | 0 | pass |
| BC-D3-1.0-3.5 | Annex D Table D.3 | 0.341 | 0.341 | 0 | 0 | pass |
| BC-D3-1.0-4.0 | Annex D Table D.3 | 0.307 | 0.307 | 0 | 0 | pass |
| BC-D3-1.0-4.5 | Annex D Table D.3 | 0.283 | 0.283 | 0 | 0 | pass |
| BC-D3-1.0-5.0 | Annex D Table D.3 | 0.259 | 0.259 | 0 | 0 | pass |
| BC-D3-1.0-5.5 | Annex D Table D.3 | 0.24 | 0.24 | 0 | 0 | pass |
| BC-D3-1.0-6.0 | Annex D Table D.3 | 0.225 | 0.225 | 0 | 0 | pass |
| BC-D3-1.0-6.5 | Annex D Table D.3 | 0.209 | 0.209 | 0 | 0 | pass |
| BC-D3-1.0-7.0 | Annex D Table D.3 | 0.196 | 0.196 | 0 | 0 | pass |
| BC-D3-1.0-8.0 | Annex D Table D.3 | 0.175 | 0.175 | 0 | 0 | pass |
| BC-D3-1.0-9.0 | Annex D Table D.3 | 0.157 | 0.157 | 0 | 0 | pass |
| BC-D3-1.0-10.0 | Annex D Table D.3 | 0.142 | 0.142 | 0 | 0 | pass |
| BC-D3-1.0-12.0 | Annex D Table D.3 | 0.121 | 0.121 | 0 | 0 | pass |
| BC-D3-1.0-14.0 | Annex D Table D.3 | 0.103 | 0.103 | 0 | 0 | pass |
| BC-D3-1.0-17.0 | Annex D Table D.3 | 0.086 | 0.086 | 0 | 0 | pass |
| BC-D3-1.0-20.0 | Annex D Table D.3 | 0.074 | 0.074 | 0 | 0 | pass |
| BC-D3-1.5-0.1 | Annex D Table D.3 | 0.875 | 0.875 | 0 | 0 | pass |
| BC-D3-1.5-0.25 | Annex D Table D.3 | 0.804 | 0.804 | 0 | 0 | pass |
| BC-D3-1.5-0.5 | Annex D Table D.3 | 0.716 | 0.716 | 0 | 0 | pass |
| BC-D3-1.5-0.75 | Annex D Table D.3 | 0.647 | 0.647 | 0 | 0 | pass |
| BC-D3-1.5-1.0 | Annex D Table D.3 | 0.593 | 0.593 | 0 | 0 | pass |
| BC-D3-1.5-1.25 | Annex D Table D.3 | 0.548 | 0.548 | 0 | 0 | pass |
| BC-D3-1.5-1.5 | Annex D Table D.3 | 0.507 | 0.507 | 0 | 0 | pass |
| BC-D3-1.5-1.75 | Annex D Table D.3 | 0.47 | 0.47 | 0 | 0 | pass |
| BC-D3-1.5-2.0 | Annex D Table D.3 | 0.439 | 0.439 | 0 | 0 | pass |
| BC-D3-1.5-2.5 | Annex D Table D.3 | 0.388 | 0.388 | 0 | 0 | pass |
| BC-D3-1.5-3.0 | Annex D Table D.3 | 0.347 | 0.347 | 0 | 0 | pass |
| BC-D3-1.5-3.5 | Annex D Table D.3 | 0.312 | 0.312 | 0 | 0 | pass |
| BC-D3-1.5-4.0 | Annex D Table D.3 | 0.283 | 0.283 | 0 | 0 | pass |
| BC-D3-1.5-4.5 | Annex D Table D.3 | 0.262 | 0.262 | 0 | 0 | pass |
| BC-D3-1.5-5.0 | Annex D Table D.3 | 0.24 | 0.24 | 0 | 0 | pass |
| BC-D3-1.5-5.5 | Annex D Table D.3 | 0.223 | 0.223 | 0 | 0 | pass |
| BC-D3-1.5-6.0 | Annex D Table D.3 | 0.207 | 0.207 | 0 | 0 | pass |
| BC-D3-1.5-6.5 | Annex D Table D.3 | 0.195 | 0.195 | 0 | 0 | pass |
| BC-D3-1.5-7.0 | Annex D Table D.3 | 0.182 | 0.182 | 0 | 0 | pass |
| BC-D3-1.5-8.0 | Annex D Table D.3 | 0.163 | 0.163 | 0 | 0 | pass |
| BC-D3-1.5-9.0 | Annex D Table D.3 | 0.148 | 0.148 | 0 | 0 | pass |
| BC-D3-1.5-10.0 | Annex D Table D.3 | 0.134 | 0.134 | 0 | 0 | pass |
| BC-D3-1.5-12.0 | Annex D Table D.3 | 0.114 | 0.114 | 0 | 0 | pass |
| BC-D3-1.5-14.0 | Annex D Table D.3 | 0.099 | 0.099 | 0 | 0 | pass |
| BC-D3-1.5-17.0 | Annex D Table D.3 | 0.082 | 0.082 | 0 | 0 | pass |
| BC-D3-1.5-20.0 | Annex D Table D.3 | 0.07 | 0.07 | 0 | 0 | pass |
| BC-D3-2.0-0.1 | Annex D Table D.3 | 0.813 | 0.813 | 0 | 0 | pass |
| BC-D3-2.0-0.25 | Annex D Table D.3 | 0.742 | 0.742 | 0 | 0 | pass |
| BC-D3-2.0-0.5 | Annex D Table D.3 | 0.653 | 0.653 | 0 | 0 | pass |
| BC-D3-2.0-0.75 | Annex D Table D.3 | 0.587 | 0.587 | 0 | 0 | pass |
| BC-D3-2.0-1.0 | Annex D Table D.3 | 0.536 | 0.536 | 0 | 0 | pass |
| BC-D3-2.0-1.25 | Annex D Table D.3 | 0.496 | 0.496 | 0 | 0 | pass |
| BC-D3-2.0-1.5 | Annex D Table D.3 | 0.457 | 0.457 | 0 | 0 | pass |
| BC-D3-2.0-1.75 | Annex D Table D.3 | 0.425 | 0.425 | 0 | 0 | pass |
| BC-D3-2.0-2.0 | Annex D Table D.3 | 0.397 | 0.397 | 0 | 0 | pass |
| BC-D3-2.0-2.5 | Annex D Table D.3 | 0.352 | 0.352 | 0 | 0 | pass |
| BC-D3-2.0-3.0 | Annex D Table D.3 | 0.315 | 0.315 | 0 | 0 | pass |
| BC-D3-2.0-3.5 | Annex D Table D.3 | 0.286 | 0.286 | 0 | 0 | pass |
| BC-D3-2.0-4.0 | Annex D Table D.3 | 0.26 | 0.26 | 0 | 0 | pass |
| BC-D3-2.0-4.5 | Annex D Table D.3 | 0.24 | 0.24 | 0 | 0 | pass |
| BC-D3-2.0-5.0 | Annex D Table D.3 | 0.222 | 0.222 | 0 | 0 | pass |
| BC-D3-2.0-5.5 | Annex D Table D.3 | 0.206 | 0.206 | 0 | 0 | pass |
| BC-D3-2.0-6.0 | Annex D Table D.3 | 0.193 | 0.193 | 0 | 0 | pass |
| BC-D3-2.0-6.5 | Annex D Table D.3 | 0.182 | 0.182 | 0 | 0 | pass |
| BC-D3-2.0-7.0 | Annex D Table D.3 | 0.17 | 0.17 | 0 | 0 | pass |
| BC-D3-2.0-8.0 | Annex D Table D.3 | 0.153 | 0.153 | 0 | 0 | pass |
| BC-D3-2.0-9.0 | Annex D Table D.3 | 0.138 | 0.138 | 0 | 0 | pass |
| BC-D3-2.0-10.0 | Annex D Table D.3 | 0.125 | 0.125 | 0 | 0 | pass |
| BC-D3-2.0-12.0 | Annex D Table D.3 | 0.107 | 0.107 | 0 | 0 | pass |
| BC-D3-2.0-14.0 | Annex D Table D.3 | 0.094 | 0.094 | 0 | 0 | pass |
| BC-D3-2.0-17.0 | Annex D Table D.3 | 0.079 | 0.079 | 0 | 0 | pass |
| BC-D3-2.0-20.0 | Annex D Table D.3 | 0.067 | 0.067 | 0 | 0 | pass |
| BC-D3-2.5-0.1 | Annex D Table D.3 | 0.742 | 0.742 | 0 | 0 | pass |
| BC-D3-2.5-0.25 | Annex D Table D.3 | 0.672 | 0.672 | 0 | 0 | pass |
| BC-D3-2.5-0.5 | Annex D Table D.3 | 0.587 | 0.587 | 0 | 0 | pass |
| BC-D3-2.5-0.75 | Annex D Table D.3 | 0.526 | 0.526 | 0 | 0 | pass |
| BC-D3-2.5-1.0 | Annex D Table D.3 | 0.48 | 0.48 | 0 | 0 | pass |
| BC-D3-2.5-1.25 | Annex D Table D.3 | 0.442 | 0.442 | 0 | 0 | pass |
| BC-D3-2.5-1.5 | Annex D Table D.3 | 0.41 | 0.41 | 0 | 0 | pass |
| BC-D3-2.5-1.75 | Annex D Table D.3 | 0.383 | 0.383 | 0 | 0 | pass |
| BC-D3-2.5-2.0 | Annex D Table D.3 | 0.357 | 0.357 | 0 | 0 | pass |
| BC-D3-2.5-2.5 | Annex D Table D.3 | 0.317 | 0.317 | 0 | 0 | pass |
| BC-D3-2.5-3.0 | Annex D Table D.3 | 0.287 | 0.287 | 0 | 0 | pass |
| BC-D3-2.5-3.5 | Annex D Table D.3 | 0.262 | 0.262 | 0 | 0 | pass |
| BC-D3-2.5-4.0 | Annex D Table D.3 | 0.238 | 0.238 | 0 | 0 | pass |
| BC-D3-2.5-4.5 | Annex D Table D.3 | 0.22 | 0.22 | 0 | 0 | pass |
| BC-D3-2.5-5.0 | Annex D Table D.3 | 0.204 | 0.204 | 0 | 0 | pass |
| BC-D3-2.5-5.5 | Annex D Table D.3 | 0.19 | 0.19 | 0 | 0 | pass |
| BC-D3-2.5-6.0 | Annex D Table D.3 | 0.178 | 0.178 | 0 | 0 | pass |
| BC-D3-2.5-6.5 | Annex D Table D.3 | 0.168 | 0.168 | 0 | 0 | pass |
| BC-D3-2.5-7.0 | Annex D Table D.3 | 0.158 | 0.158 | 0 | 0 | pass |
| BC-D3-2.5-8.0 | Annex D Table D.3 | 0.144 | 0.144 | 0 | 0 | pass |
| BC-D3-2.5-9.0 | Annex D Table D.3 | 0.13 | 0.13 | 0 | 0 | pass |
| BC-D3-2.5-10.0 | Annex D Table D.3 | 0.118 | 0.118 | 0 | 0 | pass |
| BC-D3-2.5-12.0 | Annex D Table D.3 | 0.101 | 0.101 | 0 | 0 | pass |
| BC-D3-2.5-14.0 | Annex D Table D.3 | 0.09 | 0.09 | 0 | 0 | pass |
| BC-D3-2.5-17.0 | Annex D Table D.3 | 0.076 | 0.076 | 0 | 0 | pass |
| BC-D3-2.5-20.0 | Annex D Table D.3 | 0.065 | 0.065 | 0 | 0 | pass |
| BC-D3-3.0-0.1 | Annex D Table D.3 | 0.667 | 0.667 | 0 | 0 | pass |
| BC-D3-3.0-0.25 | Annex D Table D.3 | 0.597 | 0.597 | 0 | 0 | pass |
| BC-D3-3.0-0.5 | Annex D Table D.3 | 0.52 | 0.52 | 0 | 0 | pass |
| BC-D3-3.0-0.75 | Annex D Table D.3 | 0.465 | 0.465 | 0 | 0 | pass |
| BC-D3-3.0-1.0 | Annex D Table D.3 | 0.425 | 0.425 | 0 | 0 | pass |
| BC-D3-3.0-1.25 | Annex D Table D.3 | 0.395 | 0.395 | 0 | 0 | pass |
| BC-D3-3.0-1.5 | Annex D Table D.3 | 0.365 | 0.365 | 0 | 0 | pass |
| BC-D3-3.0-1.75 | Annex D Table D.3 | 0.342 | 0.342 | 0 | 0 | pass |
| BC-D3-3.0-2.0 | Annex D Table D.3 | 0.32 | 0.32 | 0 | 0 | pass |
| BC-D3-3.0-2.5 | Annex D Table D.3 | 0.287 | 0.287 | 0 | 0 | pass |
| BC-D3-3.0-3.0 | Annex D Table D.3 | 0.26 | 0.26 | 0 | 0 | pass |
| BC-D3-3.0-3.5 | Annex D Table D.3 | 0.238 | 0.238 | 0 | 0 | pass |
| BC-D3-3.0-4.0 | Annex D Table D.3 | 0.217 | 0.217 | 0 | 0 | pass |
| BC-D3-3.0-4.5 | Annex D Table D.3 | 0.202 | 0.202 | 0 | 0 | pass |
| BC-D3-3.0-5.0 | Annex D Table D.3 | 0.187 | 0.187 | 0 | 0 | pass |
| BC-D3-3.0-5.5 | Annex D Table D.3 | 0.175 | 0.175 | 0 | 0 | pass |
| BC-D3-3.0-6.0 | Annex D Table D.3 | 0.166 | 0.166 | 0 | 0 | pass |
| BC-D3-3.0-6.5 | Annex D Table D.3 | 0.156 | 0.156 | 0 | 0 | pass |
| BC-D3-3.0-7.0 | Annex D Table D.3 | 0.147 | 0.147 | 0 | 0 | pass |
| BC-D3-3.0-8.0 | Annex D Table D.3 | 0.135 | 0.135 | 0 | 0 | pass |
| BC-D3-3.0-9.0 | Annex D Table D.3 | 0.123 | 0.123 | 0 | 0 | pass |
| BC-D3-3.0-10.0 | Annex D Table D.3 | 0.112 | 0.112 | 0 | 0 | pass |
| BC-D3-3.0-12.0 | Annex D Table D.3 | 0.097 | 0.097 | 0 | 0 | pass |
| BC-D3-3.0-14.0 | Annex D Table D.3 | 0.086 | 0.086 | 0 | 0 | pass |
| BC-D3-3.0-17.0 | Annex D Table D.3 | 0.073 | 0.073 | 0 | 0 | pass |
| BC-D3-3.0-20.0 | Annex D Table D.3 | 0.063 | 0.063 | 0 | 0 | pass |
| BC-D3-3.5-0.1 | Annex D Table D.3 | 0.587 | 0.587 | 0 | 0 | pass |
| BC-D3-3.5-0.25 | Annex D Table D.3 | 0.522 | 0.522 | 0 | 0 | pass |
| BC-D3-3.5-0.5 | Annex D Table D.3 | 0.455 | 0.455 | 0 | 0 | pass |
| BC-D3-3.5-0.75 | Annex D Table D.3 | 0.408 | 0.408 | 0 | 0 | pass |
| BC-D3-3.5-1.0 | Annex D Table D.3 | 0.375 | 0.375 | 0 | 0 | pass |
| BC-D3-3.5-1.25 | Annex D Table D.3 | 0.35 | 0.35 | 0 | 0 | pass |
| BC-D3-3.5-1.5 | Annex D Table D.3 | 0.325 | 0.325 | 0 | 0 | pass |
| BC-D3-3.5-1.75 | Annex D Table D.3 | 0.303 | 0.303 | 0 | 0 | pass |
| BC-D3-3.5-2.0 | Annex D Table D.3 | 0.287 | 0.287 | 0 | 0 | pass |
| BC-D3-3.5-2.5 | Annex D Table D.3 | 0.258 | 0.258 | 0 | 0 | pass |
| BC-D3-3.5-3.0 | Annex D Table D.3 | 0.233 | 0.233 | 0 | 0 | pass |
| BC-D3-3.5-3.5 | Annex D Table D.3 | 0.216 | 0.216 | 0 | 0 | pass |
| BC-D3-3.5-4.0 | Annex D Table D.3 | 0.198 | 0.198 | 0 | 0 | pass |
| BC-D3-3.5-4.5 | Annex D Table D.3 | 0.183 | 0.183 | 0 | 0 | pass |
| BC-D3-3.5-5.0 | Annex D Table D.3 | 0.172 | 0.172 | 0 | 0 | pass |
| BC-D3-3.5-5.5 | Annex D Table D.3 | 0.162 | 0.162 | 0 | 0 | pass |
| BC-D3-3.5-6.0 | Annex D Table D.3 | 0.153 | 0.153 | 0 | 0 | pass |
| BC-D3-3.5-6.5 | Annex D Table D.3 | 0.145 | 0.145 | 0 | 0 | pass |
| BC-D3-3.5-7.0 | Annex D Table D.3 | 0.137 | 0.137 | 0 | 0 | pass |
| BC-D3-3.5-8.0 | Annex D Table D.3 | 0.125 | 0.125 | 0 | 0 | pass |
| BC-D3-3.5-9.0 | Annex D Table D.3 | 0.115 | 0.115 | 0 | 0 | pass |
| BC-D3-3.5-10.0 | Annex D Table D.3 | 0.106 | 0.106 | 0 | 0 | pass |
| BC-D3-3.5-12.0 | Annex D Table D.3 | 0.092 | 0.092 | 0 | 0 | pass |
| BC-D3-3.5-14.0 | Annex D Table D.3 | 0.082 | 0.082 | 0 | 0 | pass |
| BC-D3-3.5-17.0 | Annex D Table D.3 | 0.069 | 0.069 | 0 | 0 | pass |
| BC-D3-3.5-20.0 | Annex D Table D.3 | 0.06 | 0.06 | 0 | 0 | pass |
| BC-D3-4.0-0.1 | Annex D Table D.3 | 0.505 | 0.505 | 0 | 0 | pass |
| BC-D3-4.0-0.25 | Annex D Table D.3 | 0.447 | 0.447 | 0 | 0 | pass |
| BC-D3-4.0-0.5 | Annex D Table D.3 | 0.394 | 0.394 | 0 | 0 | pass |
| BC-D3-4.0-0.75 | Annex D Table D.3 | 0.356 | 0.356 | 0 | 0 | pass |
| BC-D3-4.0-1.0 | Annex D Table D.3 | 0.33 | 0.33 | 0 | 0 | pass |
| BC-D3-4.0-1.25 | Annex D Table D.3 | 0.309 | 0.309 | 0 | 0 | pass |
| BC-D3-4.0-1.5 | Annex D Table D.3 | 0.289 | 0.289 | 0 | 0 | pass |
| BC-D3-4.0-1.75 | Annex D Table D.3 | 0.27 | 0.27 | 0 | 0 | pass |
| BC-D3-4.0-2.0 | Annex D Table D.3 | 0.256 | 0.256 | 0 | 0 | pass |
| BC-D3-4.0-2.5 | Annex D Table D.3 | 0.232 | 0.232 | 0 | 0 | pass |
| BC-D3-4.0-3.0 | Annex D Table D.3 | 0.212 | 0.212 | 0 | 0 | pass |
| BC-D3-4.0-3.5 | Annex D Table D.3 | 0.197 | 0.197 | 0 | 0 | pass |
| BC-D3-4.0-4.0 | Annex D Table D.3 | 0.181 | 0.181 | 0 | 0 | pass |
| BC-D3-4.0-4.5 | Annex D Table D.3 | 0.168 | 0.168 | 0 | 0 | pass |
| BC-D3-4.0-5.0 | Annex D Table D.3 | 0.158 | 0.158 | 0 | 0 | pass |
| BC-D3-4.0-5.5 | Annex D Table D.3 | 0.149 | 0.149 | 0 | 0 | pass |
| BC-D3-4.0-6.0 | Annex D Table D.3 | 0.14 | 0.14 | 0 | 0 | pass |
| BC-D3-4.0-6.5 | Annex D Table D.3 | 0.135 | 0.135 | 0 | 0 | pass |
| BC-D3-4.0-7.0 | Annex D Table D.3 | 0.127 | 0.127 | 0 | 0 | pass |
| BC-D3-4.0-8.0 | Annex D Table D.3 | 0.118 | 0.118 | 0 | 0 | pass |
| BC-D3-4.0-9.0 | Annex D Table D.3 | 0.108 | 0.108 | 0 | 0 | pass |
| BC-D3-4.0-10.0 | Annex D Table D.3 | 0.098 | 0.098 | 0 | 0 | pass |
| BC-D3-4.0-12.0 | Annex D Table D.3 | 0.088 | 0.088 | 0 | 0 | pass |
| BC-D3-4.0-14.0 | Annex D Table D.3 | 0.078 | 0.078 | 0 | 0 | pass |
| BC-D3-4.0-17.0 | Annex D Table D.3 | 0.066 | 0.066 | 0 | 0 | pass |
| BC-D3-4.0-20.0 | Annex D Table D.3 | 0.057 | 0.057 | 0 | 0 | pass |
| BC-D3-4.5-0.1 | Annex D Table D.3 | 0.418 | 0.418 | 0 | 0 | pass |
| BC-D3-4.5-0.25 | Annex D Table D.3 | 0.382 | 0.382 | 0 | 0 | pass |
| BC-D3-4.5-0.5 | Annex D Table D.3 | 0.342 | 0.342 | 0 | 0 | pass |
| BC-D3-4.5-0.75 | Annex D Table D.3 | 0.31 | 0.31 | 0 | 0 | pass |
| BC-D3-4.5-1.0 | Annex D Table D.3 | 0.288 | 0.288 | 0 | 0 | pass |
| BC-D3-4.5-1.25 | Annex D Table D.3 | 0.272 | 0.272 | 0 | 0 | pass |
| BC-D3-4.5-1.5 | Annex D Table D.3 | 0.257 | 0.257 | 0 | 0 | pass |
| BC-D3-4.5-1.75 | Annex D Table D.3 | 0.242 | 0.242 | 0 | 0 | pass |
| BC-D3-4.5-2.0 | Annex D Table D.3 | 0.229 | 0.229 | 0 | 0 | pass |
| BC-D3-4.5-2.5 | Annex D Table D.3 | 0.208 | 0.208 | 0 | 0 | pass |
| BC-D3-4.5-3.0 | Annex D Table D.3 | 0.192 | 0.192 | 0 | 0 | pass |
| BC-D3-4.5-3.5 | Annex D Table D.3 | 0.178 | 0.178 | 0 | 0 | pass |
| BC-D3-4.5-4.0 | Annex D Table D.3 | 0.165 | 0.165 | 0 | 0 | pass |
| BC-D3-4.5-4.5 | Annex D Table D.3 | 0.155 | 0.155 | 0 | 0 | pass |
| BC-D3-4.5-5.0 | Annex D Table D.3 | 0.146 | 0.146 | 0 | 0 | pass |
| BC-D3-4.5-5.5 | Annex D Table D.3 | 0.137 | 0.137 | 0 | 0 | pass |
| BC-D3-4.5-6.0 | Annex D Table D.3 | 0.13 | 0.13 | 0 | 0 | pass |
| BC-D3-4.5-6.5 | Annex D Table D.3 | 0.125 | 0.125 | 0 | 0 | pass |
| BC-D3-4.5-7.0 | Annex D Table D.3 | 0.118 | 0.118 | 0 | 0 | pass |
| BC-D3-4.5-8.0 | Annex D Table D.3 | 0.11 | 0.11 | 0 | 0 | pass |
| BC-D3-4.5-9.0 | Annex D Table D.3 | 0.101 | 0.101 | 0 | 0 | pass |
| BC-D3-4.5-10.0 | Annex D Table D.3 | 0.093 | 0.093 | 0 | 0 | pass |
| BC-D3-4.5-12.0 | Annex D Table D.3 | 0.083 | 0.083 | 0 | 0 | pass |
| BC-D3-4.5-14.0 | Annex D Table D.3 | 0.075 | 0.075 | 0 | 0 | pass |
| BC-D3-4.5-17.0 | Annex D Table D.3 | 0.064 | 0.064 | 0 | 0 | pass |
| BC-D3-4.5-20.0 | Annex D Table D.3 | 0.055 | 0.055 | 0 | 0 | pass |
| BC-D3-5.0-0.1 | Annex D Table D.3 | 0.354 | 0.354 | 0 | 0 | pass |
| BC-D3-5.0-0.25 | Annex D Table D.3 | 0.326 | 0.326 | 0 | 0 | pass |
| BC-D3-5.0-0.5 | Annex D Table D.3 | 0.295 | 0.295 | 0 | 0 | pass |
| BC-D3-5.0-0.75 | Annex D Table D.3 | 0.273 | 0.273 | 0 | 0 | pass |
| BC-D3-5.0-1.0 | Annex D Table D.3 | 0.253 | 0.253 | 0 | 0 | pass |
| BC-D3-5.0-1.25 | Annex D Table D.3 | 0.239 | 0.239 | 0 | 0 | pass |
| BC-D3-5.0-1.5 | Annex D Table D.3 | 0.225 | 0.225 | 0 | 0 | pass |
| BC-D3-5.0-1.75 | Annex D Table D.3 | 0.215 | 0.215 | 0 | 0 | pass |
| BC-D3-5.0-2.0 | Annex D Table D.3 | 0.205 | 0.205 | 0 | 0 | pass |
| BC-D3-5.0-2.5 | Annex D Table D.3 | 0.188 | 0.188 | 0 | 0 | pass |
| BC-D3-5.0-3.0 | Annex D Table D.3 | 0.175 | 0.175 | 0 | 0 | pass |
| BC-D3-5.0-3.5 | Annex D Table D.3 | 0.162 | 0.162 | 0 | 0 | pass |
| BC-D3-5.0-4.0 | Annex D Table D.3 | 0.15 | 0.15 | 0 | 0 | pass |
| BC-D3-5.0-4.5 | Annex D Table D.3 | 0.143 | 0.143 | 0 | 0 | pass |
| BC-D3-5.0-5.0 | Annex D Table D.3 | 0.135 | 0.135 | 0 | 0 | pass |
| BC-D3-5.0-5.5 | Annex D Table D.3 | 0.126 | 0.126 | 0 | 0 | pass |
| BC-D3-5.0-6.0 | Annex D Table D.3 | 0.12 | 0.12 | 0 | 0 | pass |
| BC-D3-5.0-6.5 | Annex D Table D.3 | 0.117 | 0.117 | 0 | 0 | pass |
| BC-D3-5.0-7.0 | Annex D Table D.3 | 0.111 | 0.111 | 0 | 0 | pass |
| BC-D3-5.0-8.0 | Annex D Table D.3 | 0.103 | 0.103 | 0 | 0 | pass |
| BC-D3-5.0-9.0 | Annex D Table D.3 | 0.095 | 0.095 | 0 | 0 | pass |
| BC-D3-5.0-10.0 | Annex D Table D.3 | 0.088 | 0.088 | 0 | 0 | pass |
| BC-D3-5.0-12.0 | Annex D Table D.3 | 0.079 | 0.079 | 0 | 0 | pass |
| BC-D3-5.0-14.0 | Annex D Table D.3 | 0.072 | 0.072 | 0 | 0 | pass |
| BC-D3-5.0-17.0 | Annex D Table D.3 | 0.062 | 0.062 | 0 | 0 | pass |
| BC-D3-5.0-20.0 | Annex D Table D.3 | 0.053 | 0.053 | 0 | 0 | pass |
| BC-D3-5.5-0.1 | Annex D Table D.3 | 0.302 | 0.302 | 0 | 0 | pass |
| BC-D3-5.5-0.25 | Annex D Table D.3 | 0.28 | 0.28 | 0 | 0 | pass |
| BC-D3-5.5-0.5 | Annex D Table D.3 | 0.256 | 0.256 | 0 | 0 | pass |
| BC-D3-5.5-0.75 | Annex D Table D.3 | 0.24 | 0.24 | 0 | 0 | pass |
| BC-D3-5.5-1.0 | Annex D Table D.3 | 0.224 | 0.224 | 0 | 0 | pass |
| BC-D3-5.5-1.25 | Annex D Table D.3 | 0.212 | 0.212 | 0 | 0 | pass |
| BC-D3-5.5-1.5 | Annex D Table D.3 | 0.2 | 0.2 | 0 | 0 | pass |
| BC-D3-5.5-1.75 | Annex D Table D.3 | 0.192 | 0.192 | 0 | 0 | pass |
| BC-D3-5.5-2.0 | Annex D Table D.3 | 0.184 | 0.184 | 0 | 0 | pass |
| BC-D3-5.5-2.5 | Annex D Table D.3 | 0.17 | 0.17 | 0 | 0 | pass |
| BC-D3-5.5-3.0 | Annex D Table D.3 | 0.158 | 0.158 | 0 | 0 | pass |
| BC-D3-5.5-3.5 | Annex D Table D.3 | 0.148 | 0.148 | 0 | 0 | pass |
| BC-D3-5.5-4.0 | Annex D Table D.3 | 0.138 | 0.138 | 0 | 0 | pass |
| BC-D3-5.5-4.5 | Annex D Table D.3 | 0.132 | 0.132 | 0 | 0 | pass |
| BC-D3-5.5-5.0 | Annex D Table D.3 | 0.124 | 0.124 | 0 | 0 | pass |
| BC-D3-5.5-5.5 | Annex D Table D.3 | 0.117 | 0.117 | 0 | 0 | pass |
| BC-D3-5.5-6.0 | Annex D Table D.3 | 0.112 | 0.112 | 0 | 0 | pass |
| BC-D3-5.5-6.5 | Annex D Table D.3 | 0.108 | 0.108 | 0 | 0 | pass |
| BC-D3-5.5-7.0 | Annex D Table D.3 | 0.104 | 0.104 | 0 | 0 | pass |
| BC-D3-5.5-8.0 | Annex D Table D.3 | 0.095 | 0.095 | 0 | 0 | pass |
| BC-D3-5.5-9.0 | Annex D Table D.3 | 0.089 | 0.089 | 0 | 0 | pass |
| BC-D3-5.5-10.0 | Annex D Table D.3 | 0.084 | 0.084 | 0 | 0 | pass |
| BC-D3-5.5-12.0 | Annex D Table D.3 | 0.075 | 0.075 | 0 | 0 | pass |
| BC-D3-5.5-14.0 | Annex D Table D.3 | 0.069 | 0.069 | 0 | 0 | pass |
| BC-D3-5.5-17.0 | Annex D Table D.3 | 0.06 | 0.06 | 0 | 0 | pass |
| BC-D3-5.5-20.0 | Annex D Table D.3 | 0.051 | 0.051 | 0 | 0 | pass |
| BC-D3-6.0-0.1 | Annex D Table D.3 | 0.258 | 0.258 | 0 | 0 | pass |
| BC-D3-6.0-0.25 | Annex D Table D.3 | 0.244 | 0.244 | 0 | 0 | pass |
| BC-D3-6.0-0.5 | Annex D Table D.3 | 0.223 | 0.223 | 0 | 0 | pass |
| BC-D3-6.0-0.75 | Annex D Table D.3 | 0.21 | 0.21 | 0 | 0 | pass |
| BC-D3-6.0-1.0 | Annex D Table D.3 | 0.198 | 0.198 | 0 | 0 | pass |
| BC-D3-6.0-1.25 | Annex D Table D.3 | 0.19 | 0.19 | 0 | 0 | pass |
| BC-D3-6.0-1.5 | Annex D Table D.3 | 0.178 | 0.178 | 0 | 0 | pass |
| BC-D3-6.0-1.75 | Annex D Table D.3 | 0.172 | 0.172 | 0 | 0 | pass |
| BC-D3-6.0-2.0 | Annex D Table D.3 | 0.166 | 0.166 | 0 | 0 | pass |
| BC-D3-6.0-2.5 | Annex D Table D.3 | 0.153 | 0.153 | 0 | 0 | pass |
| BC-D3-6.0-3.0 | Annex D Table D.3 | 0.145 | 0.145 | 0 | 0 | pass |
| BC-D3-6.0-3.5 | Annex D Table D.3 | 0.137 | 0.137 | 0 | 0 | pass |
| BC-D3-6.0-4.0 | Annex D Table D.3 | 0.128 | 0.128 | 0 | 0 | pass |
| BC-D3-6.0-4.5 | Annex D Table D.3 | 0.12 | 0.12 | 0 | 0 | pass |
| BC-D3-6.0-5.0 | Annex D Table D.3 | 0.115 | 0.115 | 0 | 0 | pass |
| BC-D3-6.0-5.5 | Annex D Table D.3 | 0.109 | 0.109 | 0 | 0 | pass |
| BC-D3-6.0-6.0 | Annex D Table D.3 | 0.104 | 0.104 | 0 | 0 | pass |
| BC-D3-6.0-6.5 | Annex D Table D.3 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D3-6.5-0.1 | Annex D Table D.3 | 0.223 | 0.223 | 0 | 0 | pass |
| BC-D3-6.5-0.25 | Annex D Table D.3 | 0.213 | 0.213 | 0 | 0 | pass |
| BC-D3-6.5-0.5 | Annex D Table D.3 | 0.196 | 0.196 | 0 | 0 | pass |
| BC-D3-6.5-0.75 | Annex D Table D.3 | 0.185 | 0.185 | 0 | 0 | pass |
| BC-D3-6.5-1.0 | Annex D Table D.3 | 0.176 | 0.176 | 0 | 0 | pass |
| BC-D3-6.5-1.25 | Annex D Table D.3 | 0.17 | 0.17 | 0 | 0 | pass |
| BC-D3-6.5-1.5 | Annex D Table D.3 | 0.16 | 0.16 | 0 | 0 | pass |
| BC-D3-6.5-1.75 | Annex D Table D.3 | 0.155 | 0.155 | 0 | 0 | pass |
| BC-D3-6.5-2.0 | Annex D Table D.3 | 0.149 | 0.149 | 0 | 0 | pass |
| BC-D3-6.5-2.5 | Annex D Table D.3 | 0.14 | 0.14 | 0 | 0 | pass |
| BC-D3-6.5-3.0 | Annex D Table D.3 | 0.132 | 0.132 | 0 | 0 | pass |
| BC-D3-6.5-3.5 | Annex D Table D.3 | 0.125 | 0.125 | 0 | 0 | pass |
| BC-D3-6.5-4.0 | Annex D Table D.3 | 0.117 | 0.117 | 0 | 0 | pass |
| BC-D3-6.5-4.5 | Annex D Table D.3 | 0.112 | 0.112 | 0 | 0 | pass |
| BC-D3-6.5-5.0 | Annex D Table D.3 | 0.106 | 0.106 | 0 | 0 | pass |
| BC-D3-6.5-5.5 | Annex D Table D.3 | 0.101 | 0.101 | 0 | 0 | pass |
| BC-D3-6.5-6.0 | Annex D Table D.3 | 0.097 | 0.097 | 0 | 0 | pass |
| BC-D3-6.5-6.5 | Annex D Table D.3 | 0.094 | 0.094 | 0 | 0 | pass |
| BC-D3-7.0-0.1 | Annex D Table D.3 | 0.194 | 0.194 | 0 | 0 | pass |
| BC-D3-7.0-0.25 | Annex D Table D.3 | 0.186 | 0.186 | 0 | 0 | pass |
| BC-D3-7.0-0.5 | Annex D Table D.3 | 0.173 | 0.173 | 0 | 0 | pass |
| BC-D3-7.0-0.75 | Annex D Table D.3 | 0.163 | 0.163 | 0 | 0 | pass |
| BC-D3-7.0-1.0 | Annex D Table D.3 | 0.157 | 0.157 | 0 | 0 | pass |
| BC-D3-7.0-1.25 | Annex D Table D.3 | 0.152 | 0.152 | 0 | 0 | pass |
| BC-D3-7.0-1.5 | Annex D Table D.3 | 0.145 | 0.145 | 0 | 0 | pass |
| BC-D3-7.0-1.75 | Annex D Table D.3 | 0.141 | 0.141 | 0 | 0 | pass |
| BC-D3-7.0-2.0 | Annex D Table D.3 | 0.136 | 0.136 | 0 | 0 | pass |
| BC-D3-7.0-2.5 | Annex D Table D.3 | 0.127 | 0.127 | 0 | 0 | pass |
| BC-D3-7.0-3.0 | Annex D Table D.3 | 0.121 | 0.121 | 0 | 0 | pass |
| BC-D3-7.0-3.5 | Annex D Table D.3 | 0.115 | 0.115 | 0 | 0 | pass |
| BC-D3-7.0-4.0 | Annex D Table D.3 | 0.108 | 0.108 | 0 | 0 | pass |
| BC-D3-7.0-4.5 | Annex D Table D.3 | 0.102 | 0.102 | 0 | 0 | pass |
| BC-D3-7.0-5.0 | Annex D Table D.3 | 0.098 | 0.098 | 0 | 0 | pass |
| BC-D3-7.0-5.5 | Annex D Table D.3 | 0.094 | 0.094 | 0 | 0 | pass |
| BC-D3-7.0-6.0 | Annex D Table D.3 | 0.091 | 0.091 | 0 | 0 | pass |
| BC-D3-7.0-6.5 | Annex D Table D.3 | 0.087 | 0.087 | 0 | 0 | pass |
| BC-D3-8.0-0.1 | Annex D Table D.3 | 0.152 | 0.152 | 0 | 0 | pass |
| BC-D3-8.0-0.25 | Annex D Table D.3 | 0.146 | 0.146 | 0 | 0 | pass |
| BC-D3-8.0-0.5 | Annex D Table D.3 | 0.138 | 0.138 | 0 | 0 | pass |
| BC-D3-8.0-0.75 | Annex D Table D.3 | 0.133 | 0.133 | 0 | 0 | pass |
| BC-D3-8.0-1.0 | Annex D Table D.3 | 0.128 | 0.128 | 0 | 0 | pass |
| BC-D3-8.0-1.25 | Annex D Table D.3 | 0.121 | 0.121 | 0 | 0 | pass |
| BC-D3-8.0-1.5 | Annex D Table D.3 | 0.117 | 0.117 | 0 | 0 | pass |
| BC-D3-8.0-1.75 | Annex D Table D.3 | 0.115 | 0.115 | 0 | 0 | pass |
| BC-D3-8.0-2.0 | Annex D Table D.3 | 0.113 | 0.113 | 0 | 0 | pass |
| BC-D3-8.0-2.5 | Annex D Table D.3 | 0.106 | 0.106 | 0 | 0 | pass |
| BC-D3-8.0-3.0 | Annex D Table D.3 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D3-8.0-3.5 | Annex D Table D.3 | 0.095 | 0.095 | 0 | 0 | pass |
| BC-D3-8.0-4.0 | Annex D Table D.3 | 0.091 | 0.091 | 0 | 0 | pass |
| BC-D3-8.0-4.5 | Annex D Table D.3 | 0.087 | 0.087 | 0 | 0 | pass |
| BC-D3-8.0-5.0 | Annex D Table D.3 | 0.083 | 0.083 | 0 | 0 | pass |
| BC-D3-8.0-5.5 | Annex D Table D.3 | 0.081 | 0.081 | 0 | 0 | pass |
| BC-D3-8.0-6.0 | Annex D Table D.3 | 0.078 | 0.078 | 0 | 0 | pass |
| BC-D3-8.0-6.5 | Annex D Table D.3 | 0.076 | 0.076 | 0 | 0 | pass |
| BC-D3-9.0-0.1 | Annex D Table D.3 | 0.122 | 0.122 | 0 | 0 | pass |
| BC-D3-9.0-0.25 | Annex D Table D.3 | 0.117 | 0.117 | 0 | 0 | pass |
| BC-D3-9.0-0.5 | Annex D Table D.3 | 0.112 | 0.112 | 0 | 0 | pass |
| BC-D3-9.0-0.75 | Annex D Table D.3 | 0.107 | 0.107 | 0 | 0 | pass |
| BC-D3-9.0-1.0 | Annex D Table D.3 | 0.103 | 0.103 | 0 | 0 | pass |
| BC-D3-9.0-1.25 | Annex D Table D.3 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D3-9.0-1.5 | Annex D Table D.3 | 0.098 | 0.098 | 0 | 0 | pass |
| BC-D3-9.0-1.75 | Annex D Table D.3 | 0.096 | 0.096 | 0 | 0 | pass |
| BC-D3-9.0-2.0 | Annex D Table D.3 | 0.093 | 0.093 | 0 | 0 | pass |
| BC-D4-0.5-0.1 | Annex D Table D.4 | 0.908 | 0.908 | 0 | 0 | pass |
| BC-D4-0.5-0.25 | Annex D Table D.4 | 0.8 | 0.8 | 0 | 0 | pass |
| BC-D4-0.5-0.5 | Annex D Table D.4 | 0.666 | 0.666 | 0 | 0 | pass |
| BC-D4-0.5-0.75 | Annex D Table D.4 | 0.571 | 0.571 | 0 | 0 | pass |
| BC-D4-0.5-1.0 | Annex D Table D.4 | 0.5 | 0.5 | 0 | 0 | pass |
| BC-D4-0.5-1.25 | Annex D Table D.4 | 0.444 | 0.444 | 0 | 0 | pass |
| BC-D4-0.5-1.5 | Annex D Table D.4 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D4-0.5-1.75 | Annex D Table D.4 | 0.364 | 0.364 | 0 | 0 | pass |
| BC-D4-0.5-2.0 | Annex D Table D.4 | 0.333 | 0.333 | 0 | 0 | pass |
| BC-D4-0.5-2.5 | Annex D Table D.4 | 0.286 | 0.286 | 0 | 0 | pass |
| BC-D4-0.5-3.0 | Annex D Table D.4 | 0.25 | 0.25 | 0 | 0 | pass |
| BC-D4-0.5-3.5 | Annex D Table D.4 | 0.222 | 0.222 | 0 | 0 | pass |
| BC-D4-0.5-4.0 | Annex D Table D.4 | 0.2 | 0.2 | 0 | 0 | pass |
| BC-D4-0.5-4.5 | Annex D Table D.4 | 0.182 | 0.182 | 0 | 0 | pass |
| BC-D4-0.5-5.0 | Annex D Table D.4 | 0.167 | 0.167 | 0 | 0 | pass |
| BC-D4-0.5-5.5 | Annex D Table D.4 | 0.154 | 0.154 | 0 | 0 | pass |
| BC-D4-0.5-6.0 | Annex D Table D.4 | 0.143 | 0.143 | 0 | 0 | pass |
| BC-D4-0.5-6.5 | Annex D Table D.4 | 0.133 | 0.133 | 0 | 0 | pass |
| BC-D4-0.5-7.0 | Annex D Table D.4 | 0.125 | 0.125 | 0 | 0 | pass |
| BC-D4-0.5-8.0 | Annex D Table D.4 | 0.111 | 0.111 | 0 | 0 | pass |
| BC-D4-0.5-9.0 | Annex D Table D.4 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D4-0.5-10.0 | Annex D Table D.4 | 0.091 | 0.091 | 0 | 0 | pass |
| BC-D4-0.5-12.0 | Annex D Table D.4 | 0.077 | 0.077 | 0 | 0 | pass |
| BC-D4-0.5-14.0 | Annex D Table D.4 | 0.067 | 0.067 | 0 | 0 | pass |
| BC-D4-0.5-17.0 | Annex D Table D.4 | 0.058 | 0.058 | 0 | 0 | pass |
| BC-D4-0.5-20.0 | Annex D Table D.4 | 0.048 | 0.048 | 0 | 0 | pass |
| BC-D4-1.0-0.1 | Annex D Table D.4 | 0.872 | 0.872 | 0 | 0 | pass |
| BC-D4-1.0-0.25 | Annex D Table D.4 | 0.762 | 0.762 | 0 | 0 | pass |
| BC-D4-1.0-0.5 | Annex D Table D.4 | 0.64 | 0.64 | 0 | 0 | pass |
| BC-D4-1.0-0.75 | Annex D Table D.4 | 0.553 | 0.553 | 0 | 0 | pass |
| BC-D4-1.0-1.0 | Annex D Table D.4 | 0.483 | 0.483 | 0 | 0 | pass |
| BC-D4-1.0-1.25 | Annex D Table D.4 | 0.431 | 0.431 | 0 | 0 | pass |
| BC-D4-1.0-1.5 | Annex D Table D.4 | 0.387 | 0.387 | 0 | 0 | pass |
| BC-D4-1.0-1.75 | Annex D Table D.4 | 0.351 | 0.351 | 0 | 0 | pass |
| BC-D4-1.0-2.0 | Annex D Table D.4 | 0.328 | 0.328 | 0 | 0 | pass |
| BC-D4-1.0-2.5 | Annex D Table D.4 | 0.28 | 0.28 | 0 | 0 | pass |
| BC-D4-1.0-3.0 | Annex D Table D.4 | 0.243 | 0.243 | 0 | 0 | pass |
| BC-D4-1.0-3.5 | Annex D Table D.4 | 0.218 | 0.218 | 0 | 0 | pass |
| BC-D4-1.0-4.0 | Annex D Table D.4 | 0.197 | 0.197 | 0 | 0 | pass |
| BC-D4-1.0-4.5 | Annex D Table D.4 | 0.18 | 0.18 | 0 | 0 | pass |
| BC-D4-1.0-5.0 | Annex D Table D.4 | 0.165 | 0.165 | 0 | 0 | pass |
| BC-D4-1.0-5.5 | Annex D Table D.4 | 0.151 | 0.151 | 0 | 0 | pass |
| BC-D4-1.0-6.0 | Annex D Table D.4 | 0.142 | 0.142 | 0 | 0 | pass |
| BC-D4-1.0-6.5 | Annex D Table D.4 | 0.131 | 0.131 | 0 | 0 | pass |
| BC-D4-1.0-7.0 | Annex D Table D.4 | 0.121 | 0.121 | 0 | 0 | pass |
| BC-D4-1.0-8.0 | Annex D Table D.4 | 0.109 | 0.109 | 0 | 0 | pass |
| BC-D4-1.0-9.0 | Annex D Table D.4 | 0.098 | 0.098 | 0 | 0 | pass |
| BC-D4-1.0-10.0 | Annex D Table D.4 | 0.09 | 0.09 | 0 | 0 | pass |
| BC-D4-1.0-12.0 | Annex D Table D.4 | 0.077 | 0.077 | 0 | 0 | pass |
| BC-D4-1.0-14.0 | Annex D Table D.4 | 0.066 | 0.066 | 0 | 0 | pass |
| BC-D4-1.0-17.0 | Annex D Table D.4 | 0.055 | 0.055 | 0 | 0 | pass |
| BC-D4-1.0-20.0 | Annex D Table D.4 | 0.046 | 0.046 | 0 | 0 | pass |
| BC-D4-1.5-0.1 | Annex D Table D.4 | 0.83 | 0.83 | 0 | 0 | pass |
| BC-D4-1.5-0.25 | Annex D Table D.4 | 0.727 | 0.727 | 0 | 0 | pass |
| BC-D4-1.5-0.5 | Annex D Table D.4 | 0.6 | 0.6 | 0 | 0 | pass |
| BC-D4-1.5-0.75 | Annex D Table D.4 | 0.517 | 0.517 | 0 | 0 | pass |
| BC-D4-1.5-1.0 | Annex D Table D.4 | 0.454 | 0.454 | 0 | 0 | pass |
| BC-D4-1.5-1.25 | Annex D Table D.4 | 0.407 | 0.407 | 0 | 0 | pass |
| BC-D4-1.5-1.5 | Annex D Table D.4 | 0.367 | 0.367 | 0 | 0 | pass |
| BC-D4-1.5-1.75 | Annex D Table D.4 | 0.336 | 0.336 | 0 | 0 | pass |
| BC-D4-1.5-2.0 | Annex D Table D.4 | 0.311 | 0.311 | 0 | 0 | pass |
| BC-D4-1.5-2.5 | Annex D Table D.4 | 0.271 | 0.271 | 0 | 0 | pass |
| BC-D4-1.5-3.0 | Annex D Table D.4 | 0.24 | 0.24 | 0 | 0 | pass |
| BC-D4-1.5-3.5 | Annex D Table D.4 | 0.211 | 0.211 | 0 | 0 | pass |
| BC-D4-1.5-4.0 | Annex D Table D.4 | 0.19 | 0.19 | 0 | 0 | pass |
| BC-D4-1.5-4.5 | Annex D Table D.4 | 0.178 | 0.178 | 0 | 0 | pass |
| BC-D4-1.5-5.0 | Annex D Table D.4 | 0.163 | 0.163 | 0 | 0 | pass |
| BC-D4-1.5-5.5 | Annex D Table D.4 | 0.149 | 0.149 | 0 | 0 | pass |
| BC-D4-1.5-6.0 | Annex D Table D.4 | 0.137 | 0.137 | 0 | 0 | pass |
| BC-D4-1.5-6.5 | Annex D Table D.4 | 0.128 | 0.128 | 0 | 0 | pass |
| BC-D4-1.5-7.0 | Annex D Table D.4 | 0.119 | 0.119 | 0 | 0 | pass |
| BC-D4-1.5-8.0 | Annex D Table D.4 | 0.108 | 0.108 | 0 | 0 | pass |
| BC-D4-1.5-9.0 | Annex D Table D.4 | 0.096 | 0.096 | 0 | 0 | pass |
| BC-D4-1.5-10.0 | Annex D Table D.4 | 0.088 | 0.088 | 0 | 0 | pass |
| BC-D4-1.5-12.0 | Annex D Table D.4 | 0.077 | 0.077 | 0 | 0 | pass |
| BC-D4-1.5-14.0 | Annex D Table D.4 | 0.065 | 0.065 | 0 | 0 | pass |
| BC-D4-1.5-17.0 | Annex D Table D.4 | 0.053 | 0.053 | 0 | 0 | pass |
| BC-D4-1.5-20.0 | Annex D Table D.4 | 0.045 | 0.045 | 0 | 0 | pass |
| BC-D4-2.0-0.1 | Annex D Table D.4 | 0.774 | 0.774 | 0 | 0 | pass |
| BC-D4-2.0-0.25 | Annex D Table D.4 | 0.673 | 0.673 | 0 | 0 | pass |
| BC-D4-2.0-0.5 | Annex D Table D.4 | 0.556 | 0.556 | 0 | 0 | pass |
| BC-D4-2.0-0.75 | Annex D Table D.4 | 0.479 | 0.479 | 0 | 0 | pass |
| BC-D4-2.0-1.0 | Annex D Table D.4 | 0.423 | 0.423 | 0 | 0 | pass |
| BC-D4-2.0-1.25 | Annex D Table D.4 | 0.381 | 0.381 | 0 | 0 | pass |
| BC-D4-2.0-1.5 | Annex D Table D.4 | 0.346 | 0.346 | 0 | 0 | pass |
| BC-D4-2.0-1.75 | Annex D Table D.4 | 0.318 | 0.318 | 0 | 0 | pass |
| BC-D4-2.0-2.0 | Annex D Table D.4 | 0.293 | 0.293 | 0 | 0 | pass |
| BC-D4-2.0-2.5 | Annex D Table D.4 | 0.255 | 0.255 | 0 | 0 | pass |
| BC-D4-2.0-3.0 | Annex D Table D.4 | 0.228 | 0.228 | 0 | 0 | pass |
| BC-D4-2.0-3.5 | Annex D Table D.4 | 0.202 | 0.202 | 0 | 0 | pass |
| BC-D4-2.0-4.0 | Annex D Table D.4 | 0.183 | 0.183 | 0 | 0 | pass |
| BC-D4-2.0-4.5 | Annex D Table D.4 | 0.17 | 0.17 | 0 | 0 | pass |
| BC-D4-2.0-5.0 | Annex D Table D.4 | 0.156 | 0.156 | 0 | 0 | pass |
| BC-D4-2.0-5.5 | Annex D Table D.4 | 0.143 | 0.143 | 0 | 0 | pass |
| BC-D4-2.0-6.0 | Annex D Table D.4 | 0.132 | 0.132 | 0 | 0 | pass |
| BC-D4-2.0-6.5 | Annex D Table D.4 | 0.125 | 0.125 | 0 | 0 | pass |
| BC-D4-2.0-7.0 | Annex D Table D.4 | 0.117 | 0.117 | 0 | 0 | pass |
| BC-D4-2.0-8.0 | Annex D Table D.4 | 0.106 | 0.106 | 0 | 0 | pass |
| BC-D4-2.0-9.0 | Annex D Table D.4 | 0.095 | 0.095 | 0 | 0 | pass |
| BC-D4-2.0-10.0 | Annex D Table D.4 | 0.086 | 0.086 | 0 | 0 | pass |
| BC-D4-2.0-12.0 | Annex D Table D.4 | 0.076 | 0.076 | 0 | 0 | pass |
| BC-D4-2.0-14.0 | Annex D Table D.4 | 0.064 | 0.064 | 0 | 0 | pass |
| BC-D4-2.0-17.0 | Annex D Table D.4 | 0.052 | 0.052 | 0 | 0 | pass |
| BC-D4-2.0-20.0 | Annex D Table D.4 | 0.045 | 0.045 | 0 | 0 | pass |
| BC-D4-2.5-0.1 | Annex D Table D.4 | 0.708 | 0.708 | 0 | 0 | pass |
| BC-D4-2.5-0.25 | Annex D Table D.4 | 0.608 | 0.608 | 0 | 0 | pass |
| BC-D4-2.5-0.5 | Annex D Table D.4 | 0.507 | 0.507 | 0 | 0 | pass |
| BC-D4-2.5-0.75 | Annex D Table D.4 | 0.439 | 0.439 | 0 | 0 | pass |
| BC-D4-2.5-1.0 | Annex D Table D.4 | 0.391 | 0.391 | 0 | 0 | pass |
| BC-D4-2.5-1.25 | Annex D Table D.4 | 0.354 | 0.354 | 0 | 0 | pass |
| BC-D4-2.5-1.5 | Annex D Table D.4 | 0.322 | 0.322 | 0 | 0 | pass |
| BC-D4-2.5-1.75 | Annex D Table D.4 | 0.297 | 0.297 | 0 | 0 | pass |
| BC-D4-2.5-2.0 | Annex D Table D.4 | 0.274 | 0.274 | 0 | 0 | pass |
| BC-D4-2.5-2.5 | Annex D Table D.4 | 0.238 | 0.238 | 0 | 0 | pass |
| BC-D4-2.5-3.0 | Annex D Table D.4 | 0.215 | 0.215 | 0 | 0 | pass |
| BC-D4-2.5-3.5 | Annex D Table D.4 | 0.192 | 0.192 | 0 | 0 | pass |
| BC-D4-2.5-4.0 | Annex D Table D.4 | 0.175 | 0.175 | 0 | 0 | pass |
| BC-D4-2.5-4.5 | Annex D Table D.4 | 0.162 | 0.162 | 0 | 0 | pass |
| BC-D4-2.5-5.0 | Annex D Table D.4 | 0.148 | 0.148 | 0 | 0 | pass |
| BC-D4-2.5-5.5 | Annex D Table D.4 | 0.136 | 0.136 | 0 | 0 | pass |
| BC-D4-2.5-6.0 | Annex D Table D.4 | 0.127 | 0.127 | 0 | 0 | pass |
| BC-D4-2.5-6.5 | Annex D Table D.4 | 0.12 | 0.12 | 0 | 0 | pass |
| BC-D4-2.5-7.0 | Annex D Table D.4 | 0.113 | 0.113 | 0 | 0 | pass |
| BC-D4-2.5-8.0 | Annex D Table D.4 | 0.103 | 0.103 | 0 | 0 | pass |
| BC-D4-2.5-9.0 | Annex D Table D.4 | 0.093 | 0.093 | 0 | 0 | pass |
| BC-D4-2.5-10.0 | Annex D Table D.4 | 0.083 | 0.083 | 0 | 0 | pass |
| BC-D4-2.5-12.0 | Annex D Table D.4 | 0.074 | 0.074 | 0 | 0 | pass |
| BC-D4-2.5-14.0 | Annex D Table D.4 | 0.062 | 0.062 | 0 | 0 | pass |
| BC-D4-2.5-17.0 | Annex D Table D.4 | 0.051 | 0.051 | 0 | 0 | pass |
| BC-D4-2.5-20.0 | Annex D Table D.4 | 0.044 | 0.044 | 0 | 0 | pass |
| BC-D4-3.0-0.1 | Annex D Table D.4 | 0.637 | 0.637 | 0 | 0 | pass |
| BC-D4-3.0-0.25 | Annex D Table D.4 | 0.545 | 0.545 | 0 | 0 | pass |
| BC-D4-3.0-0.5 | Annex D Table D.4 | 0.455 | 0.455 | 0 | 0 | pass |
| BC-D4-3.0-0.75 | Annex D Table D.4 | 0.399 | 0.399 | 0 | 0 | pass |
| BC-D4-3.0-1.0 | Annex D Table D.4 | 0.356 | 0.356 | 0 | 0 | pass |
| BC-D4-3.0-1.25 | Annex D Table D.4 | 0.324 | 0.324 | 0 | 0 | pass |
| BC-D4-3.0-1.5 | Annex D Table D.4 | 0.296 | 0.296 | 0 | 0 | pass |
| BC-D4-3.0-1.75 | Annex D Table D.4 | 0.275 | 0.275 | 0 | 0 | pass |
| BC-D4-3.0-2.0 | Annex D Table D.4 | 0.255 | 0.255 | 0 | 0 | pass |
| BC-D4-3.0-2.5 | Annex D Table D.4 | 0.222 | 0.222 | 0 | 0 | pass |
| BC-D4-3.0-3.0 | Annex D Table D.4 | 0.201 | 0.201 | 0 | 0 | pass |
| BC-D4-3.0-3.5 | Annex D Table D.4 | 0.182 | 0.182 | 0 | 0 | pass |
| BC-D4-3.0-4.0 | Annex D Table D.4 | 0.165 | 0.165 | 0 | 0 | pass |
| BC-D4-3.0-4.5 | Annex D Table D.4 | 0.153 | 0.153 | 0 | 0 | pass |
| BC-D4-3.0-5.0 | Annex D Table D.4 | 0.138 | 0.138 | 0 | 0 | pass |
| BC-D4-3.0-5.5 | Annex D Table D.4 | 0.13 | 0.13 | 0 | 0 | pass |
| BC-D4-3.0-6.0 | Annex D Table D.4 | 0.121 | 0.121 | 0 | 0 | pass |
| BC-D4-3.0-6.5 | Annex D Table D.4 | 0.116 | 0.116 | 0 | 0 | pass |
| BC-D4-3.0-7.0 | Annex D Table D.4 | 0.11 | 0.11 | 0 | 0 | pass |
| BC-D4-3.0-8.0 | Annex D Table D.4 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D4-3.0-9.0 | Annex D Table D.4 | 0.091 | 0.091 | 0 | 0 | pass |
| BC-D4-3.0-10.0 | Annex D Table D.4 | 0.081 | 0.081 | 0 | 0 | pass |
| BC-D4-3.0-12.0 | Annex D Table D.4 | 0.071 | 0.071 | 0 | 0 | pass |
| BC-D4-3.0-14.0 | Annex D Table D.4 | 0.061 | 0.061 | 0 | 0 | pass |
| BC-D4-3.0-17.0 | Annex D Table D.4 | 0.051 | 0.051 | 0 | 0 | pass |
| BC-D4-3.0-20.0 | Annex D Table D.4 | 0.043 | 0.043 | 0 | 0 | pass |
| BC-D4-3.5-0.1 | Annex D Table D.4 | 0.562 | 0.562 | 0 | 0 | pass |
| BC-D4-3.5-0.25 | Annex D Table D.4 | 0.48 | 0.48 | 0 | 0 | pass |
| BC-D4-3.5-0.5 | Annex D Table D.4 | 0.402 | 0.402 | 0 | 0 | pass |
| BC-D4-3.5-0.75 | Annex D Table D.4 | 0.355 | 0.355 | 0 | 0 | pass |
| BC-D4-3.5-1.0 | Annex D Table D.4 | 0.32 | 0.32 | 0 | 0 | pass |
| BC-D4-3.5-1.25 | Annex D Table D.4 | 0.294 | 0.294 | 0 | 0 | pass |
| BC-D4-3.5-1.5 | Annex D Table D.4 | 0.27 | 0.27 | 0 | 0 | pass |
| BC-D4-3.5-1.75 | Annex D Table D.4 | 0.251 | 0.251 | 0 | 0 | pass |
| BC-D4-3.5-2.0 | Annex D Table D.4 | 0.235 | 0.235 | 0 | 0 | pass |
| BC-D4-3.5-2.5 | Annex D Table D.4 | 0.206 | 0.206 | 0 | 0 | pass |
| BC-D4-3.5-3.0 | Annex D Table D.4 | 0.187 | 0.187 | 0 | 0 | pass |
| BC-D4-3.5-3.5 | Annex D Table D.4 | 0.17 | 0.17 | 0 | 0 | pass |
| BC-D4-3.5-4.0 | Annex D Table D.4 | 0.155 | 0.155 | 0 | 0 | pass |
| BC-D4-3.5-4.5 | Annex D Table D.4 | 0.143 | 0.143 | 0 | 0 | pass |
| BC-D4-3.5-5.0 | Annex D Table D.4 | 0.13 | 0.13 | 0 | 0 | pass |
| BC-D4-3.5-5.5 | Annex D Table D.4 | 0.123 | 0.123 | 0 | 0 | pass |
| BC-D4-3.5-6.0 | Annex D Table D.4 | 0.115 | 0.115 | 0 | 0 | pass |
| BC-D4-3.5-6.5 | Annex D Table D.4 | 0.11 | 0.11 | 0 | 0 | pass |
| BC-D4-3.5-7.0 | Annex D Table D.4 | 0.106 | 0.106 | 0 | 0 | pass |
| BC-D4-3.5-8.0 | Annex D Table D.4 | 0.096 | 0.096 | 0 | 0 | pass |
| BC-D4-3.5-9.0 | Annex D Table D.4 | 0.088 | 0.088 | 0 | 0 | pass |
| BC-D4-3.5-10.0 | Annex D Table D.4 | 0.078 | 0.078 | 0 | 0 | pass |
| BC-D4-3.5-12.0 | Annex D Table D.4 | 0.069 | 0.069 | 0 | 0 | pass |
| BC-D4-3.5-14.0 | Annex D Table D.4 | 0.059 | 0.059 | 0 | 0 | pass |
| BC-D4-3.5-17.0 | Annex D Table D.4 | 0.05 | 0.05 | 0 | 0 | pass |
| BC-D4-3.5-20.0 | Annex D Table D.4 | 0.042 | 0.042 | 0 | 0 | pass |
| BC-D4-4.0-0.1 | Annex D Table D.4 | 0.484 | 0.484 | 0 | 0 | pass |
| BC-D4-4.0-0.25 | Annex D Table D.4 | 0.422 | 0.422 | 0 | 0 | pass |
| BC-D4-4.0-0.5 | Annex D Table D.4 | 0.357 | 0.357 | 0 | 0 | pass |
| BC-D4-4.0-0.75 | Annex D Table D.4 | 0.317 | 0.317 | 0 | 0 | pass |
| BC-D4-4.0-1.0 | Annex D Table D.4 | 0.288 | 0.288 | 0 | 0 | pass |
| BC-D4-4.0-1.25 | Annex D Table D.4 | 0.264 | 0.264 | 0 | 0 | pass |
| BC-D4-4.0-1.5 | Annex D Table D.4 | 0.246 | 0.246 | 0 | 0 | pass |
| BC-D4-4.0-1.75 | Annex D Table D.4 | 0.228 | 0.228 | 0 | 0 | pass |
| BC-D4-4.0-2.0 | Annex D Table D.4 | 0.215 | 0.215 | 0 | 0 | pass |
| BC-D4-4.0-2.5 | Annex D Table D.4 | 0.191 | 0.191 | 0 | 0 | pass |
| BC-D4-4.0-3.0 | Annex D Table D.4 | 0.173 | 0.173 | 0 | 0 | pass |
| BC-D4-4.0-3.5 | Annex D Table D.4 | 0.16 | 0.16 | 0 | 0 | pass |
| BC-D4-4.0-4.0 | Annex D Table D.4 | 0.145 | 0.145 | 0 | 0 | pass |
| BC-D4-4.0-4.5 | Annex D Table D.4 | 0.133 | 0.133 | 0 | 0 | pass |
| BC-D4-4.0-5.0 | Annex D Table D.4 | 0.124 | 0.124 | 0 | 0 | pass |
| BC-D4-4.0-5.5 | Annex D Table D.4 | 0.118 | 0.118 | 0 | 0 | pass |
| BC-D4-4.0-6.0 | Annex D Table D.4 | 0.11 | 0.11 | 0 | 0 | pass |
| BC-D4-4.0-6.5 | Annex D Table D.4 | 0.105 | 0.105 | 0 | 0 | pass |
| BC-D4-4.0-7.0 | Annex D Table D.4 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D4-4.0-8.0 | Annex D Table D.4 | 0.093 | 0.093 | 0 | 0 | pass |
| BC-D4-4.0-9.0 | Annex D Table D.4 | 0.084 | 0.084 | 0 | 0 | pass |
| BC-D4-4.0-10.0 | Annex D Table D.4 | 0.076 | 0.076 | 0 | 0 | pass |
| BC-D4-4.0-12.0 | Annex D Table D.4 | 0.067 | 0.067 | 0 | 0 | pass |
| BC-D4-4.0-14.0 | Annex D Table D.4 | 0.057 | 0.057 | 0 | 0 | pass |
| BC-D4-4.0-17.0 | Annex D Table D.4 | 0.049 | 0.049 | 0 | 0 | pass |
| BC-D4-4.0-20.0 | Annex D Table D.4 | 0.041 | 0.041 | 0 | 0 | pass |
| BC-D4-4.5-0.1 | Annex D Table D.4 | 0.415 | 0.415 | 0 | 0 | pass |
| BC-D4-4.5-0.25 | Annex D Table D.4 | 0.365 | 0.365 | 0 | 0 | pass |
| BC-D4-4.5-0.5 | Annex D Table D.4 | 0.315 | 0.315 | 0 | 0 | pass |
| BC-D4-4.5-0.75 | Annex D Table D.4 | 0.281 | 0.281 | 0 | 0 | pass |
| BC-D4-4.5-1.0 | Annex D Table D.4 | 0.258 | 0.258 | 0 | 0 | pass |
| BC-D4-4.5-1.25 | Annex D Table D.4 | 0.237 | 0.237 | 0 | 0 | pass |
| BC-D4-4.5-1.5 | Annex D Table D.4 | 0.223 | 0.223 | 0 | 0 | pass |
| BC-D4-4.5-1.75 | Annex D Table D.4 | 0.207 | 0.207 | 0 | 0 | pass |
| BC-D4-4.5-2.0 | Annex D Table D.4 | 0.196 | 0.196 | 0 | 0 | pass |
| BC-D4-4.5-2.5 | Annex D Table D.4 | 0.176 | 0.176 | 0 | 0 | pass |
| BC-D4-4.5-3.0 | Annex D Table D.4 | 0.16 | 0.16 | 0 | 0 | pass |
| BC-D4-4.5-3.5 | Annex D Table D.4 | 0.149 | 0.149 | 0 | 0 | pass |
| BC-D4-4.5-4.0 | Annex D Table D.4 | 0.136 | 0.136 | 0 | 0 | pass |
| BC-D4-4.5-4.5 | Annex D Table D.4 | 0.124 | 0.124 | 0 | 0 | pass |
| BC-D4-4.5-5.0 | Annex D Table D.4 | 0.116 | 0.116 | 0 | 0 | pass |
| BC-D4-4.5-5.5 | Annex D Table D.4 | 0.11 | 0.11 | 0 | 0 | pass |
| BC-D4-4.5-6.0 | Annex D Table D.4 | 0.105 | 0.105 | 0 | 0 | pass |
| BC-D4-4.5-6.5 | Annex D Table D.4 | 0.096 | 0.096 | 0 | 0 | pass |
| BC-D4-4.5-7.0 | Annex D Table D.4 | 0.096 | 0.096 | 0 | 0 | pass |
| BC-D4-4.5-8.0 | Annex D Table D.4 | 0.089 | 0.089 | 0 | 0 | pass |
| BC-D4-4.5-9.0 | Annex D Table D.4 | 0.079 | 0.079 | 0 | 0 | pass |
| BC-D4-4.5-10.0 | Annex D Table D.4 | 0.073 | 0.073 | 0 | 0 | pass |
| BC-D4-4.5-12.0 | Annex D Table D.4 | 0.065 | 0.065 | 0 | 0 | pass |
| BC-D4-4.5-14.0 | Annex D Table D.4 | 0.055 | 0.055 | 0 | 0 | pass |
| BC-D4-4.5-17.0 | Annex D Table D.4 | 0.048 | 0.048 | 0 | 0 | pass |
| BC-D4-4.5-20.0 | Annex D Table D.4 | 0.04 | 0.04 | 0 | 0 | pass |
| BC-D4-5.0-0.1 | Annex D Table D.4 | 0.35 | 0.35 | 0 | 0 | pass |
| BC-D4-5.0-0.25 | Annex D Table D.4 | 0.315 | 0.315 | 0 | 0 | pass |
| BC-D4-5.0-0.5 | Annex D Table D.4 | 0.277 | 0.277 | 0 | 0 | pass |
| BC-D4-5.0-0.75 | Annex D Table D.4 | 0.25 | 0.25 | 0 | 0 | pass |
| BC-D4-5.0-1.0 | Annex D Table D.4 | 0.23 | 0.23 | 0 | 0 | pass |
| BC-D4-5.0-1.25 | Annex D Table D.4 | 0.212 | 0.212 | 0 | 0 | pass |
| BC-D4-5.0-1.5 | Annex D Table D.4 | 0.201 | 0.201 | 0 | 0 | pass |
| BC-D4-5.0-1.75 | Annex D Table D.4 | 0.186 | 0.186 | 0 | 0 | pass |
| BC-D4-5.0-2.0 | Annex D Table D.4 | 0.178 | 0.178 | 0 | 0 | pass |
| BC-D4-5.0-2.5 | Annex D Table D.4 | 0.161 | 0.161 | 0 | 0 | pass |
| BC-D4-5.0-3.0 | Annex D Table D.4 | 0.149 | 0.149 | 0 | 0 | pass |
| BC-D4-5.0-3.5 | Annex D Table D.4 | 0.138 | 0.138 | 0 | 0 | pass |
| BC-D4-5.0-4.0 | Annex D Table D.4 | 0.127 | 0.127 | 0 | 0 | pass |
| BC-D4-5.0-4.5 | Annex D Table D.4 | 0.117 | 0.117 | 0 | 0 | pass |
| BC-D4-5.0-5.0 | Annex D Table D.4 | 0.108 | 0.108 | 0 | 0 | pass |
| BC-D4-5.0-5.5 | Annex D Table D.4 | 0.104 | 0.104 | 0 | 0 | pass |
| BC-D4-5.0-6.0 | Annex D Table D.4 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D4-5.0-6.5 | Annex D Table D.4 | 0.095 | 0.095 | 0 | 0 | pass |
| BC-D4-5.5-0.1 | Annex D Table D.4 | 0.3 | 0.3 | 0 | 0 | pass |
| BC-D4-5.5-0.25 | Annex D Table D.4 | 0.273 | 0.273 | 0 | 0 | pass |
| BC-D4-5.5-0.5 | Annex D Table D.4 | 0.245 | 0.245 | 0 | 0 | pass |
| BC-D4-5.5-0.75 | Annex D Table D.4 | 0.223 | 0.223 | 0 | 0 | pass |
| BC-D4-5.5-1.0 | Annex D Table D.4 | 0.203 | 0.203 | 0 | 0 | pass |
| BC-D4-5.5-1.25 | Annex D Table D.4 | 0.192 | 0.192 | 0 | 0 | pass |
| BC-D4-5.5-1.5 | Annex D Table D.4 | 0.182 | 0.182 | 0 | 0 | pass |
| BC-D4-5.5-1.75 | Annex D Table D.4 | 0.172 | 0.172 | 0 | 0 | pass |
| BC-D4-5.5-2.0 | Annex D Table D.4 | 0.163 | 0.163 | 0 | 0 | pass |
| BC-D4-6.0-0.1 | Annex D Table D.4 | 0.255 | 0.255 | 0 | 0 | pass |
| BC-D4-6.0-0.25 | Annex D Table D.4 | 0.237 | 0.237 | 0 | 0 | pass |
| BC-D4-6.0-0.5 | Annex D Table D.4 | 0.216 | 0.216 | 0 | 0 | pass |
| BC-D4-6.0-0.75 | Annex D Table D.4 | 0.198 | 0.198 | 0 | 0 | pass |
| BC-D4-6.0-1.0 | Annex D Table D.4 | 0.183 | 0.183 | 0 | 0 | pass |
| BC-D4-6.0-1.25 | Annex D Table D.4 | 0.174 | 0.174 | 0 | 0 | pass |
| BC-D4-6.0-1.5 | Annex D Table D.4 | 0.165 | 0.165 | 0 | 0 | pass |
| BC-D4-6.0-1.75 | Annex D Table D.4 | 0.156 | 0.156 | 0 | 0 | pass |
| BC-D4-6.0-2.0 | Annex D Table D.4 | 0.149 | 0.149 | 0 | 0 | pass |
| BC-D4-6.5-0.1 | Annex D Table D.4 | 0.221 | 0.221 | 0 | 0 | pass |
| BC-D4-6.5-0.25 | Annex D Table D.4 | 0.208 | 0.208 | 0 | 0 | pass |
| BC-D4-6.5-0.5 | Annex D Table D.4 | 0.19 | 0.19 | 0 | 0 | pass |
| BC-D4-6.5-0.75 | Annex D Table D.4 | 0.178 | 0.178 | 0 | 0 | pass |
| BC-D4-6.5-1.0 | Annex D Table D.4 | 0.165 | 0.165 | 0 | 0 | pass |
| BC-D4-6.5-1.25 | Annex D Table D.4 | 0.157 | 0.157 | 0 | 0 | pass |
| BC-D4-6.5-1.5 | Annex D Table D.4 | 0.149 | 0.149 | 0 | 0 | pass |
| BC-D4-6.5-1.75 | Annex D Table D.4 | 0.142 | 0.142 | 0 | 0 | pass |
| BC-D4-6.5-2.0 | Annex D Table D.4 | 0.137 | 0.137 | 0 | 0 | pass |
| BC-D4-7.0-0.1 | Annex D Table D.4 | 0.192 | 0.192 | 0 | 0 | pass |
| BC-D4-7.0-0.25 | Annex D Table D.4 | 0.184 | 0.184 | 0 | 0 | pass |
| BC-D4-7.0-0.5 | Annex D Table D.4 | 0.168 | 0.168 | 0 | 0 | pass |
| BC-D4-7.0-0.75 | Annex D Table D.4 | 0.16 | 0.16 | 0 | 0 | pass |
| BC-D4-7.0-1.0 | Annex D Table D.4 | 0.15 | 0.15 | 0 | 0 | pass |
| BC-D4-7.0-1.25 | Annex D Table D.4 | 0.141 | 0.141 | 0 | 0 | pass |
| BC-D4-7.0-1.5 | Annex D Table D.4 | 0.135 | 0.135 | 0 | 0 | pass |
| BC-D4-7.0-1.75 | Annex D Table D.4 | 0.13 | 0.13 | 0 | 0 | pass |
| BC-D4-7.0-2.0 | Annex D Table D.4 | 0.125 | 0.125 | 0 | 0 | pass |
| BC-D4-8.0-0.1 | Annex D Table D.4 | 0.148 | 0.148 | 0 | 0 | pass |
| BC-D4-8.0-0.25 | Annex D Table D.4 | 0.142 | 0.142 | 0 | 0 | pass |
| BC-D4-8.0-0.5 | Annex D Table D.4 | 0.136 | 0.136 | 0 | 0 | pass |
| BC-D4-8.0-0.75 | Annex D Table D.4 | 0.13 | 0.13 | 0 | 0 | pass |
| BC-D4-8.0-1.0 | Annex D Table D.4 | 0.123 | 0.123 | 0 | 0 | pass |
| BC-D4-8.0-1.25 | Annex D Table D.4 | 0.118 | 0.118 | 0 | 0 | pass |
| BC-D4-8.0-1.5 | Annex D Table D.4 | 0.113 | 0.113 | 0 | 0 | pass |
| BC-D4-8.0-1.75 | Annex D Table D.4 | 0.108 | 0.108 | 0 | 0 | pass |
| BC-D4-8.0-2.0 | Annex D Table D.4 | 0.105 | 0.105 | 0 | 0 | pass |
| BC-D5--1.0-1-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-1-0.5 | Annex D Table D.5 | 0.3 | 0.3 | 0 | 0 | pass |
| BC-D5--1.0-1-1.0 | Annex D Table D.5 | 0.68 | 0.68 | 0 | 0 | pass |
| BC-D5--1.0-1-1.5 | Annex D Table D.5 | 1.12 | 1.12 | 0 | 0 | pass |
| BC-D5--1.0-1-2.0 | Annex D Table D.5 | 1.6 | 1.6 | 0 | 0 | pass |
| BC-D5--1.0-1-3.0 | Annex D Table D.5 | 2.62 | 2.62 | 0 | 0 | pass |
| BC-D5--1.0-1-4.0 | Annex D Table D.5 | 3.55 | 3.55 | 0 | 0 | pass |
| BC-D5--1.0-1-5.0 | Annex D Table D.5 | 4.55 | 4.55 | 0 | 0 | pass |
| BC-D5--1.0-1-7.0 | Annex D Table D.5 | 6.5 | 6.5 | 0 | 0 | pass |
| BC-D5--1.0-1-10.0 | Annex D Table D.5 | 9.4 | 9.4 | 0 | 0 | pass |
| BC-D5--1.0-1-20.0 | Annex D Table D.5 | 19.4 | 19.4 | 0 | 0 | pass |
| BC-D5--1.0-2-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-2-0.5 | Annex D Table D.5 | 0.17 | 0.17 | 0 | 0 | pass |
| BC-D5--1.0-2-1.0 | Annex D Table D.5 | 0.39 | 0.39 | 0 | 0 | pass |
| BC-D5--1.0-2-1.5 | Annex D Table D.5 | 0.68 | 0.68 | 0 | 0 | pass |
| BC-D5--1.0-2-2.0 | Annex D Table D.5 | 1.03 | 1.03 | 0 | 0 | pass |
| BC-D5--1.0-2-3.0 | Annex D Table D.5 | 1.8 | 1.8 | 0 | 0 | pass |
| BC-D5--1.0-2-4.0 | Annex D Table D.5 | 2.75 | 2.75 | 0 | 0 | pass |
| BC-D5--1.0-2-5.0 | Annex D Table D.5 | 3.72 | 3.72 | 0 | 0 | pass |
| BC-D5--1.0-2-7.0 | Annex D Table D.5 | 5.65 | 5.65 | 0 | 0 | pass |
| BC-D5--1.0-2-10.0 | Annex D Table D.5 | 8.6 | 8.6 | 0 | 0 | pass |
| BC-D5--1.0-2-20.0 | Annex D Table D.5 | 18.5 | 18.5 | 0 | 0 | pass |
| BC-D5--1.0-3-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-3-0.5 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-3-1.0 | Annex D Table D.5 | 0.22 | 0.22 | 0 | 0 | pass |
| BC-D5--1.0-3-1.5 | Annex D Table D.5 | 0.36 | 0.36 | 0 | 0 | pass |
| BC-D5--1.0-3-2.0 | Annex D Table D.5 | 0.55 | 0.55 | 0 | 0 | pass |
| BC-D5--1.0-3-3.0 | Annex D Table D.5 | 1.17 | 1.17 | 0 | 0 | pass |
| BC-D5--1.0-3-4.0 | Annex D Table D.5 | 1.95 | 1.95 | 0 | 0 | pass |
| BC-D5--1.0-3-5.0 | Annex D Table D.5 | 2.77 | 2.77 | 0 | 0 | pass |
| BC-D5--1.0-3-7.0 | Annex D Table D.5 | 4.6 | 4.6 | 0 | 0 | pass |
| BC-D5--1.0-3-10.0 | Annex D Table D.5 | 7.4 | 7.4 | 0 | 0 | pass |
| BC-D5--1.0-3-20.0 | Annex D Table D.5 | 17.2 | 17.2 | 0 | 0 | pass |
| BC-D5--1.0-4-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-4-0.5 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-4-1.0 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-4-1.5 | Annex D Table D.5 | 0.18 | 0.18 | 0 | 0 | pass |
| BC-D5--1.0-4-2.0 | Annex D Table D.5 | 0.3 | 0.3 | 0 | 0 | pass |
| BC-D5--1.0-4-3.0 | Annex D Table D.5 | 0.57 | 0.57 | 0 | 0 | pass |
| BC-D5--1.0-4-4.0 | Annex D Table D.5 | 1.03 | 1.03 | 0 | 0 | pass |
| BC-D5--1.0-4-5.0 | Annex D Table D.5 | 1.78 | 1.78 | 0 | 0 | pass |
| BC-D5--1.0-4-7.0 | Annex D Table D.5 | 3.35 | 3.35 | 0 | 0 | pass |
| BC-D5--1.0-4-10.0 | Annex D Table D.5 | 5.9 | 5.9 | 0 | 0 | pass |
| BC-D5--1.0-4-20.0 | Annex D Table D.5 | 15.4 | 15.4 | 0 | 0 | pass |
| BC-D5--1.0-5-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-5-0.5 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-5-1.0 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-5-1.5 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-5-2.0 | Annex D Table D.5 | 0.15 | 0.15 | 0 | 0 | pass |
| BC-D5--1.0-5-3.0 | Annex D Table D.5 | 0.23 | 0.23 | 0 | 0 | pass |
| BC-D5--1.0-5-4.0 | Annex D Table D.5 | 0.48 | 0.48 | 0 | 0 | pass |
| BC-D5--1.0-5-5.0 | Annex D Table D.5 | 0.95 | 0.95 | 0 | 0 | pass |
| BC-D5--1.0-5-7.0 | Annex D Table D.5 | 2.18 | 2.18 | 0 | 0 | pass |
| BC-D5--1.0-5-10.0 | Annex D Table D.5 | 4.4 | 4.4 | 0 | 0 | pass |
| BC-D5--1.0-5-20.0 | Annex D Table D.5 | 13.4 | 13.4 | 0 | 0 | pass |
| BC-D5--1.0-6-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-6-0.5 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-6-1.0 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-6-1.5 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-6-2.0 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-6-3.0 | Annex D Table D.5 | 0.15 | 0.15 | 0 | 0 | pass |
| BC-D5--1.0-6-4.0 | Annex D Table D.5 | 0.18 | 0.18 | 0 | 0 | pass |
| BC-D5--1.0-6-5.0 | Annex D Table D.5 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D5--1.0-6-7.0 | Annex D Table D.5 | 1.25 | 1.25 | 0 | 0 | pass |
| BC-D5--1.0-6-10.0 | Annex D Table D.5 | 3 | 3 | 0 | 0 | pass |
| BC-D5--1.0-6-20.0 | Annex D Table D.5 | 11.4 | 11.4 | 0 | 0 | pass |
| BC-D5--1.0-7-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-7-0.5 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-7-1.0 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-7-1.5 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-7-2.0 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-7-3.0 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-7-4.0 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-7-5.0 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--1.0-7-7.0 | Annex D Table D.5 | 0.5 | 0.5 | 0 | 0 | pass |
| BC-D5--1.0-7-10.0 | Annex D Table D.5 | 1.7 | 1.7 | 0 | 0 | pass |
| BC-D5--1.0-7-20.0 | Annex D Table D.5 | 9.5 | 9.5 | 0 | 0 | pass |
| BC-D5--0.5-1-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--0.5-1-0.5 | Annex D Table D.5 | 0.31 | 0.31 | 0 | 0 | pass |
| BC-D5--0.5-1-1.0 | Annex D Table D.5 | 0.68 | 0.68 | 0 | 0 | pass |
| BC-D5--0.5-1-1.5 | Annex D Table D.5 | 1.12 | 1.12 | 0 | 0 | pass |
| BC-D5--0.5-1-2.0 | Annex D Table D.5 | 1.6 | 1.6 | 0 | 0 | pass |
| BC-D5--0.5-1-3.0 | Annex D Table D.5 | 2.62 | 2.62 | 0 | 0 | pass |
| BC-D5--0.5-1-4.0 | Annex D Table D.5 | 3.55 | 3.55 | 0 | 0 | pass |
| BC-D5--0.5-1-5.0 | Annex D Table D.5 | 4.55 | 4.55 | 0 | 0 | pass |
| BC-D5--0.5-1-7.0 | Annex D Table D.5 | 6.5 | 6.5 | 0 | 0 | pass |
| BC-D5--0.5-1-10.0 | Annex D Table D.5 | 9.4 | 9.4 | 0 | 0 | pass |
| BC-D5--0.5-1-20.0 | Annex D Table D.5 | 19.4 | 19.4 | 0 | 0 | pass |
| BC-D5--0.5-2-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--0.5-2-0.5 | Annex D Table D.5 | 0.22 | 0.22 | 0 | 0 | pass |
| BC-D5--0.5-2-1.0 | Annex D Table D.5 | 0.46 | 0.46 | 0 | 0 | pass |
| BC-D5--0.5-2-1.5 | Annex D Table D.5 | 0.73 | 0.73 | 0 | 0 | pass |
| BC-D5--0.5-2-2.0 | Annex D Table D.5 | 1.05 | 1.05 | 0 | 0 | pass |
| BC-D5--0.5-2-3.0 | Annex D Table D.5 | 1.88 | 1.88 | 0 | 0 | pass |
| BC-D5--0.5-2-4.0 | Annex D Table D.5 | 2.75 | 2.75 | 0 | 0 | pass |
| BC-D5--0.5-2-5.0 | Annex D Table D.5 | 3.72 | 3.72 | 0 | 0 | pass |
| BC-D5--0.5-2-7.0 | Annex D Table D.5 | 5.65 | 5.65 | 0 | 0 | pass |
| BC-D5--0.5-2-10.0 | Annex D Table D.5 | 8.6 | 8.6 | 0 | 0 | pass |
| BC-D5--0.5-2-20.0 | Annex D Table D.5 | 18.5 | 18.5 | 0 | 0 | pass |
| BC-D5--0.5-3-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--0.5-3-0.5 | Annex D Table D.5 | 0.17 | 0.17 | 0 | 0 | pass |
| BC-D5--0.5-3-1.0 | Annex D Table D.5 | 0.38 | 0.38 | 0 | 0 | pass |
| BC-D5--0.5-3-1.5 | Annex D Table D.5 | 0.58 | 0.58 | 0 | 0 | pass |
| BC-D5--0.5-3-2.0 | Annex D Table D.5 | 0.8 | 0.8 | 0 | 0 | pass |
| BC-D5--0.5-3-3.0 | Annex D Table D.5 | 1.33 | 1.33 | 0 | 0 | pass |
| BC-D5--0.5-3-4.0 | Annex D Table D.5 | 2 | 2 | 0 | 0 | pass |
| BC-D5--0.5-3-5.0 | Annex D Table D.5 | 2.77 | 2.77 | 0 | 0 | pass |
| BC-D5--0.5-3-7.0 | Annex D Table D.5 | 4.6 | 4.6 | 0 | 0 | pass |
| BC-D5--0.5-3-10.0 | Annex D Table D.5 | 7.4 | 7.4 | 0 | 0 | pass |
| BC-D5--0.5-3-20.0 | Annex D Table D.5 | 17.2 | 17.2 | 0 | 0 | pass |
| BC-D5--0.5-4-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--0.5-4-0.5 | Annex D Table D.5 | 0.14 | 0.14 | 0 | 0 | pass |
| BC-D5--0.5-4-1.0 | Annex D Table D.5 | 0.32 | 0.32 | 0 | 0 | pass |
| BC-D5--0.5-4-1.5 | Annex D Table D.5 | 0.49 | 0.49 | 0 | 0 | pass |
| BC-D5--0.5-4-2.0 | Annex D Table D.5 | 0.66 | 0.66 | 0 | 0 | pass |
| BC-D5--0.5-4-3.0 | Annex D Table D.5 | 1.05 | 1.05 | 0 | 0 | pass |
| BC-D5--0.5-4-4.0 | Annex D Table D.5 | 1.52 | 1.52 | 0 | 0 | pass |
| BC-D5--0.5-4-5.0 | Annex D Table D.5 | 2.22 | 2.22 | 0 | 0 | pass |
| BC-D5--0.5-4-7.0 | Annex D Table D.5 | 3.5 | 3.5 | 0 | 0 | pass |
| BC-D5--0.5-4-10.0 | Annex D Table D.5 | 5.9 | 5.9 | 0 | 0 | pass |
| BC-D5--0.5-4-20.0 | Annex D Table D.5 | 15.4 | 15.4 | 0 | 0 | pass |
| BC-D5--0.5-5-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--0.5-5-0.5 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--0.5-5-1.0 | Annex D Table D.5 | 0.26 | 0.26 | 0 | 0 | pass |
| BC-D5--0.5-5-1.5 | Annex D Table D.5 | 0.41 | 0.41 | 0 | 0 | pass |
| BC-D5--0.5-5-2.0 | Annex D Table D.5 | 0.57 | 0.57 | 0 | 0 | pass |
| BC-D5--0.5-5-3.0 | Annex D Table D.5 | 0.95 | 0.95 | 0 | 0 | pass |
| BC-D5--0.5-5-4.0 | Annex D Table D.5 | 1.38 | 1.38 | 0 | 0 | pass |
| BC-D5--0.5-5-5.0 | Annex D Table D.5 | 1.8 | 1.8 | 0 | 0 | pass |
| BC-D5--0.5-5-7.0 | Annex D Table D.5 | 2.95 | 2.95 | 0 | 0 | pass |
| BC-D5--0.5-5-10.0 | Annex D Table D.5 | 4.7 | 4.7 | 0 | 0 | pass |
| BC-D5--0.5-5-20.0 | Annex D Table D.5 | 13.4 | 13.4 | 0 | 0 | pass |
| BC-D5--0.5-6-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--0.5-6-0.5 | Annex D Table D.5 | 0.16 | 0.16 | 0 | 0 | pass |
| BC-D5--0.5-6-1.0 | Annex D Table D.5 | 0.28 | 0.28 | 0 | 0 | pass |
| BC-D5--0.5-6-1.5 | Annex D Table D.5 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D5--0.5-6-2.0 | Annex D Table D.5 | 0.52 | 0.52 | 0 | 0 | pass |
| BC-D5--0.5-6-3.0 | Annex D Table D.5 | 0.95 | 0.95 | 0 | 0 | pass |
| BC-D5--0.5-6-4.0 | Annex D Table D.5 | 1.25 | 1.25 | 0 | 0 | pass |
| BC-D5--0.5-6-5.0 | Annex D Table D.5 | 1.6 | 1.6 | 0 | 0 | pass |
| BC-D5--0.5-6-7.0 | Annex D Table D.5 | 2.5 | 2.5 | 0 | 0 | pass |
| BC-D5--0.5-6-10.0 | Annex D Table D.5 | 4 | 4 | 0 | 0 | pass |
| BC-D5--0.5-6-20.0 | Annex D Table D.5 | 11.5 | 11.5 | 0 | 0 | pass |
| BC-D5--0.5-7-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5--0.5-7-0.5 | Annex D Table D.5 | 0.22 | 0.22 | 0 | 0 | pass |
| BC-D5--0.5-7-1.0 | Annex D Table D.5 | 0.32 | 0.32 | 0 | 0 | pass |
| BC-D5--0.5-7-1.5 | Annex D Table D.5 | 0.42 | 0.42 | 0 | 0 | pass |
| BC-D5--0.5-7-2.0 | Annex D Table D.5 | 0.55 | 0.55 | 0 | 0 | pass |
| BC-D5--0.5-7-3.0 | Annex D Table D.5 | 0.95 | 0.95 | 0 | 0 | pass |
| BC-D5--0.5-7-4.0 | Annex D Table D.5 | 1.1 | 1.1 | 0 | 0 | pass |
| BC-D5--0.5-7-5.0 | Annex D Table D.5 | 1.35 | 1.35 | 0 | 0 | pass |
| BC-D5--0.5-7-7.0 | Annex D Table D.5 | 2.2 | 2.2 | 0 | 0 | pass |
| BC-D5--0.5-7-10.0 | Annex D Table D.5 | 3.5 | 3.5 | 0 | 0 | pass |
| BC-D5--0.5-7-20.0 | Annex D Table D.5 | 10.8 | 10.8 | 0 | 0 | pass |
| BC-D5-0.0-1-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.0-1-0.5 | Annex D Table D.5 | 0.32 | 0.32 | 0 | 0 | pass |
| BC-D5-0.0-1-1.0 | Annex D Table D.5 | 0.7 | 0.7 | 0 | 0 | pass |
| BC-D5-0.0-1-1.5 | Annex D Table D.5 | 1.12 | 1.12 | 0 | 0 | pass |
| BC-D5-0.0-1-2.0 | Annex D Table D.5 | 1.6 | 1.6 | 0 | 0 | pass |
| BC-D5-0.0-1-3.0 | Annex D Table D.5 | 2.62 | 2.62 | 0 | 0 | pass |
| BC-D5-0.0-1-4.0 | Annex D Table D.5 | 2.55 | 2.55 | 0 | 0 | pass |
| BC-D5-0.0-1-5.0 | Annex D Table D.5 | 4.55 | 4.55 | 0 | 0 | pass |
| BC-D5-0.0-1-7.0 | Annex D Table D.5 | 6.5 | 6.5 | 0 | 0 | pass |
| BC-D5-0.0-1-10.0 | Annex D Table D.5 | 9.4 | 9.4 | 0 | 0 | pass |
| BC-D5-0.0-1-20.0 | Annex D Table D.5 | 19.4 | 19.4 | 0 | 0 | pass |
| BC-D5-0.0-2-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.0-2-0.5 | Annex D Table D.5 | 0.28 | 0.28 | 0 | 0 | pass |
| BC-D5-0.0-2-1.0 | Annex D Table D.5 | 0.6 | 0.6 | 0 | 0 | pass |
| BC-D5-0.0-2-1.5 | Annex D Table D.5 | 0.9 | 0.9 | 0 | 0 | pass |
| BC-D5-0.0-2-2.0 | Annex D Table D.5 | 1.28 | 1.28 | 0 | 0 | pass |
| BC-D5-0.0-2-3.0 | Annex D Table D.5 | 1.96 | 1.96 | 0 | 0 | pass |
| BC-D5-0.0-2-4.0 | Annex D Table D.5 | 2.75 | 2.75 | 0 | 0 | pass |
| BC-D5-0.0-2-5.0 | Annex D Table D.5 | 3.72 | 3.72 | 0 | 0 | pass |
| BC-D5-0.0-2-7.0 | Annex D Table D.5 | 5.65 | 5.65 | 0 | 0 | pass |
| BC-D5-0.0-2-10.0 | Annex D Table D.5 | 8.4 | 8.4 | 0 | 0 | pass |
| BC-D5-0.0-2-20.0 | Annex D Table D.5 | 18.5 | 18.5 | 0 | 0 | pass |
| BC-D5-0.0-3-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.0-3-0.5 | Annex D Table D.5 | 0.27 | 0.27 | 0 | 0 | pass |
| BC-D5-0.0-3-1.0 | Annex D Table D.5 | 0.55 | 0.55 | 0 | 0 | pass |
| BC-D5-0.0-3-1.5 | Annex D Table D.5 | 0.84 | 0.84 | 0 | 0 | pass |
| BC-D5-0.0-3-2.0 | Annex D Table D.5 | 1.15 | 1.15 | 0 | 0 | pass |
| BC-D5-0.0-3-3.0 | Annex D Table D.5 | 1.75 | 1.75 | 0 | 0 | pass |
| BC-D5-0.0-3-4.0 | Annex D Table D.5 | 2.43 | 2.43 | 0 | 0 | pass |
| BC-D5-0.0-3-5.0 | Annex D Table D.5 | 3.17 | 3.17 | 0 | 0 | pass |
| BC-D5-0.0-3-7.0 | Annex D Table D.5 | 4.8 | 4.8 | 0 | 0 | pass |
| BC-D5-0.0-3-10.0 | Annex D Table D.5 | 7.4 | 7.4 | 0 | 0 | pass |
| BC-D5-0.0-3-20.0 | Annex D Table D.5 | 17.2 | 17.2 | 0 | 0 | pass |
| BC-D5-0.0-4-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.0-4-0.5 | Annex D Table D.5 | 0.26 | 0.26 | 0 | 0 | pass |
| BC-D5-0.0-4-1.0 | Annex D Table D.5 | 0.52 | 0.52 | 0 | 0 | pass |
| BC-D5-0.0-4-1.5 | Annex D Table D.5 | 0.78 | 0.78 | 0 | 0 | pass |
| BC-D5-0.0-4-2.0 | Annex D Table D.5 | 1.1 | 1.1 | 0 | 0 | pass |
| BC-D5-0.0-4-3.0 | Annex D Table D.5 | 1.6 | 1.6 | 0 | 0 | pass |
| BC-D5-0.0-4-4.0 | Annex D Table D.5 | 2.2 | 2.2 | 0 | 0 | pass |
| BC-D5-0.0-4-5.0 | Annex D Table D.5 | 2.83 | 2.83 | 0 | 0 | pass |
| BC-D5-0.0-4-7.0 | Annex D Table D.5 | 4 | 4 | 0 | 0 | pass |
| BC-D5-0.0-4-10.0 | Annex D Table D.5 | 6.3 | 6.3 | 0 | 0 | pass |
| BC-D5-0.0-4-20.0 | Annex D Table D.5 | 15.4 | 15.4 | 0 | 0 | pass |
| BC-D5-0.0-5-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.0-5-0.5 | Annex D Table D.5 | 0.25 | 0.25 | 0 | 0 | pass |
| BC-D5-0.0-5-1.0 | Annex D Table D.5 | 0.52 | 0.52 | 0 | 0 | pass |
| BC-D5-0.0-5-1.5 | Annex D Table D.5 | 0.78 | 0.78 | 0 | 0 | pass |
| BC-D5-0.0-5-2.0 | Annex D Table D.5 | 1.1 | 1.1 | 0 | 0 | pass |
| BC-D5-0.0-5-3.0 | Annex D Table D.5 | 1.55 | 1.55 | 0 | 0 | pass |
| BC-D5-0.0-5-4.0 | Annex D Table D.5 | 2.1 | 2.1 | 0 | 0 | pass |
| BC-D5-0.0-5-5.0 | Annex D Table D.5 | 2.78 | 2.78 | 0 | 0 | pass |
| BC-D5-0.0-5-7.0 | Annex D Table D.5 | 3.85 | 3.85 | 0 | 0 | pass |
| BC-D5-0.0-5-10.0 | Annex D Table D.5 | 5.9 | 5.9 | 0 | 0 | pass |
| BC-D5-0.0-5-20.0 | Annex D Table D.5 | 14.5 | 14.5 | 0 | 0 | pass |
| BC-D5-0.0-6-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.0-6-0.5 | Annex D Table D.5 | 0.28 | 0.28 | 0 | 0 | pass |
| BC-D5-0.0-6-1.0 | Annex D Table D.5 | 0.52 | 0.52 | 0 | 0 | pass |
| BC-D5-0.0-6-1.5 | Annex D Table D.5 | 0.78 | 0.78 | 0 | 0 | pass |
| BC-D5-0.0-6-2.0 | Annex D Table D.5 | 1.1 | 1.1 | 0 | 0 | pass |
| BC-D5-0.0-6-3.0 | Annex D Table D.5 | 1.55 | 1.55 | 0 | 0 | pass |
| BC-D5-0.0-6-4.0 | Annex D Table D.5 | 2 | 2 | 0 | 0 | pass |
| BC-D5-0.0-6-5.0 | Annex D Table D.5 | 2.7 | 2.7 | 0 | 0 | pass |
| BC-D5-0.0-6-7.0 | Annex D Table D.5 | 3.8 | 3.8 | 0 | 0 | pass |
| BC-D5-0.0-6-10.0 | Annex D Table D.5 | 5.6 | 5.6 | 0 | 0 | pass |
| BC-D5-0.0-6-20.0 | Annex D Table D.5 | 13.8 | 13.8 | 0 | 0 | pass |
| BC-D5-0.0-7-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.0-7-0.5 | Annex D Table D.5 | 0.32 | 0.32 | 0 | 0 | pass |
| BC-D5-0.0-7-1.0 | Annex D Table D.5 | 0.52 | 0.52 | 0 | 0 | pass |
| BC-D5-0.0-7-1.5 | Annex D Table D.5 | 0.78 | 0.78 | 0 | 0 | pass |
| BC-D5-0.0-7-2.0 | Annex D Table D.5 | 1.1 | 1.1 | 0 | 0 | pass |
| BC-D5-0.0-7-3.0 | Annex D Table D.5 | 1.55 | 1.55 | 0 | 0 | pass |
| BC-D5-0.0-7-4.0 | Annex D Table D.5 | 1.9 | 1.9 | 0 | 0 | pass |
| BC-D5-0.0-7-5.0 | Annex D Table D.5 | 2.6 | 2.6 | 0 | 0 | pass |
| BC-D5-0.0-7-7.0 | Annex D Table D.5 | 3.75 | 3.75 | 0 | 0 | pass |
| BC-D5-0.0-7-10.0 | Annex D Table D.5 | 5.5 | 5.5 | 0 | 0 | pass |
| BC-D5-0.0-7-20.0 | Annex D Table D.5 | 13 | 13 | 0 | 0 | pass |
| BC-D5-0.5-1-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.5-1-0.5 | Annex D Table D.5 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D5-0.5-1-1.0 | Annex D Table D.5 | 0.8 | 0.8 | 0 | 0 | pass |
| BC-D5-0.5-1-1.5 | Annex D Table D.5 | 1.23 | 1.23 | 0 | 0 | pass |
| BC-D5-0.5-1-2.0 | Annex D Table D.5 | 1.68 | 1.68 | 0 | 0 | pass |
| BC-D5-0.5-1-3.0 | Annex D Table D.5 | 2.62 | 2.62 | 0 | 0 | pass |
| BC-D5-0.5-1-4.0 | Annex D Table D.5 | 3.55 | 3.55 | 0 | 0 | pass |
| BC-D5-0.5-1-5.0 | Annex D Table D.5 | 4.55 | 4.55 | 0 | 0 | pass |
| BC-D5-0.5-1-7.0 | Annex D Table D.5 | 6.5 | 6.5 | 0 | 0 | pass |
| BC-D5-0.5-1-10.0 | Annex D Table D.5 | 9.1 | 9.1 | 0 | 0 | pass |
| BC-D5-0.5-1-20.0 | Annex D Table D.5 | 19.4 | 19.4 | 0 | 0 | pass |
| BC-D5-0.5-2-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.5-2-0.5 | Annex D Table D.5 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D5-0.5-2-1.0 | Annex D Table D.5 | 0.78 | 0.78 | 0 | 0 | pass |
| BC-D5-0.5-2-1.5 | Annex D Table D.5 | 1.2 | 1.2 | 0 | 0 | pass |
| BC-D5-0.5-2-2.0 | Annex D Table D.5 | 1.6 | 1.6 | 0 | 0 | pass |
| BC-D5-0.5-2-3.0 | Annex D Table D.5 | 2.3 | 2.3 | 0 | 0 | pass |
| BC-D5-0.5-2-4.0 | Annex D Table D.5 | 3.15 | 3.15 | 0 | 0 | pass |
| BC-D5-0.5-2-5.0 | Annex D Table D.5 | 4.1 | 4.1 | 0 | 0 | pass |
| BC-D5-0.5-2-7.0 | Annex D Table D.5 | 5.85 | 5.85 | 0 | 0 | pass |
| BC-D5-0.5-2-10.0 | Annex D Table D.5 | 8.6 | 8.6 | 0 | 0 | pass |
| BC-D5-0.5-2-20.0 | Annex D Table D.5 | 18.5 | 18.5 | 0 | 0 | pass |
| BC-D5-0.5-3-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.5-3-0.5 | Annex D Table D.5 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D5-0.5-3-1.0 | Annex D Table D.5 | 0.77 | 0.77 | 0 | 0 | pass |
| BC-D5-0.5-3-1.5 | Annex D Table D.5 | 1.17 | 1.17 | 0 | 0 | pass |
| BC-D5-0.5-3-2.0 | Annex D Table D.5 | 1.55 | 1.55 | 0 | 0 | pass |
| BC-D5-0.5-3-3.0 | Annex D Table D.5 | 2.3 | 2.3 | 0 | 0 | pass |
| BC-D5-0.5-3-4.0 | Annex D Table D.5 | 3.1 | 3.1 | 0 | 0 | pass |
| BC-D5-0.5-3-5.0 | Annex D Table D.5 | 3.9 | 3.9 | 0 | 0 | pass |
| BC-D5-0.5-3-7.0 | Annex D Table D.5 | 5.55 | 5.55 | 0 | 0 | pass |
| BC-D5-0.5-3-10.0 | Annex D Table D.5 | 8.13 | 8.13 | 0 | 0 | pass |
| BC-D5-0.5-3-20.0 | Annex D Table D.5 | 18 | 18 | 0 | 0 | pass |
| BC-D5-0.5-4-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.5-4-0.5 | Annex D Table D.5 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D5-0.5-4-1.0 | Annex D Table D.5 | 0.75 | 0.75 | 0 | 0 | pass |
| BC-D5-0.5-4-1.5 | Annex D Table D.5 | 1.13 | 1.13 | 0 | 0 | pass |
| BC-D5-0.5-4-2.0 | Annex D Table D.5 | 1.55 | 1.55 | 0 | 0 | pass |
| BC-D5-0.5-4-3.0 | Annex D Table D.5 | 2.3 | 2.3 | 0 | 0 | pass |
| BC-D5-0.5-4-4.0 | Annex D Table D.5 | 3.05 | 3.05 | 0 | 0 | pass |
| BC-D5-0.5-4-5.0 | Annex D Table D.5 | 3.8 | 3.8 | 0 | 0 | pass |
| BC-D5-0.5-4-7.0 | Annex D Table D.5 | 5.3 | 5.3 | 0 | 0 | pass |
| BC-D5-0.5-4-10.0 | Annex D Table D.5 | 7.6 | 7.6 | 0 | 0 | pass |
| BC-D5-0.5-4-20.0 | Annex D Table D.5 | 17.5 | 17.5 | 0 | 0 | pass |
| BC-D5-0.5-5-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.5-5-0.5 | Annex D Table D.5 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D5-0.5-5-1.0 | Annex D Table D.5 | 0.75 | 0.75 | 0 | 0 | pass |
| BC-D5-0.5-5-1.5 | Annex D Table D.5 | 1.1 | 1.1 | 0 | 0 | pass |
| BC-D5-0.5-5-2.0 | Annex D Table D.5 | 1.55 | 1.55 | 0 | 0 | pass |
| BC-D5-0.5-5-3.0 | Annex D Table D.5 | 2.3 | 2.3 | 0 | 0 | pass |
| BC-D5-0.5-5-4.0 | Annex D Table D.5 | 3 | 3 | 0 | 0 | pass |
| BC-D5-0.5-5-5.0 | Annex D Table D.5 | 3.8 | 3.8 | 0 | 0 | pass |
| BC-D5-0.5-5-7.0 | Annex D Table D.5 | 5.3 | 5.3 | 0 | 0 | pass |
| BC-D5-0.5-5-10.0 | Annex D Table D.5 | 7.6 | 7.6 | 0 | 0 | pass |
| BC-D5-0.5-5-20.0 | Annex D Table D.5 | 17 | 17 | 0 | 0 | pass |
| BC-D5-0.5-6-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.5-6-0.5 | Annex D Table D.5 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D5-0.5-6-1.0 | Annex D Table D.5 | 0.75 | 0.75 | 0 | 0 | pass |
| BC-D5-0.5-6-1.5 | Annex D Table D.5 | 1.1 | 1.1 | 0 | 0 | pass |
| BC-D5-0.5-6-2.0 | Annex D Table D.5 | 1.5 | 1.5 | 0 | 0 | pass |
| BC-D5-0.5-6-3.0 | Annex D Table D.5 | 2.3 | 2.3 | 0 | 0 | pass |
| BC-D5-0.5-6-4.0 | Annex D Table D.5 | 3 | 3 | 0 | 0 | pass |
| BC-D5-0.5-6-5.0 | Annex D Table D.5 | 3.8 | 3.8 | 0 | 0 | pass |
| BC-D5-0.5-6-7.0 | Annex D Table D.5 | 5.3 | 5.3 | 0 | 0 | pass |
| BC-D5-0.5-6-10.0 | Annex D Table D.5 | 7.6 | 7.6 | 0 | 0 | pass |
| BC-D5-0.5-6-20.0 | Annex D Table D.5 | 16.5 | 16.5 | 0 | 0 | pass |
| BC-D5-0.5-7-0.1 | Annex D Table D.5 | 0.1 | 0.1 | 0 | 0 | pass |
| BC-D5-0.5-7-0.5 | Annex D Table D.5 | 0.4 | 0.4 | 0 | 0 | pass |
| BC-D5-0.5-7-1.0 | Annex D Table D.5 | 0.75 | 0.75 | 0 | 0 | pass |
| BC-D5-0.5-7-1.5 | Annex D Table D.5 | 1.1 | 1.1 | 0 | 0 | pass |
| BC-D5-0.5-7-2.0 | Annex D Table D.5 | 1.4 | 1.4 | 0 | 0 | pass |
| BC-D5-0.5-7-3.0 | Annex D Table D.5 | 2.3 | 2.3 | 0 | 0 | pass |
| BC-D5-0.5-7-4.0 | Annex D Table D.5 | 3 | 3 | 0 | 0 | pass |
| BC-D5-0.5-7-5.0 | Annex D Table D.5 | 3.8 | 3.8 | 0 | 0 | pass |
| BC-D5-0.5-7-7.0 | Annex D Table D.5 | 5.3 | 5.3 | 0 | 0 | pass |
| BC-D5-0.5-7-10.0 | Annex D Table D.5 | 7.6 | 7.6 | 0 | 0 | pass |
| BC-D5-0.5-7-20.0 | Annex D Table D.5 | 16 | 16 | 0 | 0 | pass |
| V11-EQ-123 | 9.3.2 equation (123) | 2 | 2 | 0 | 1e-12 | pass |
| V11-EQ-124 | 9.3.3 equation (124) | 160000 | 160000 | 0 | 1e-09 | pass |
| V11-EQ-125 | 9.4.2 equation (125) | 1.6375 | 1.6375 | 0 | 1e-12 | pass |
| V11-EQ-126 | 9.4.2 equation (126) | 2.6 | 2.6 | 4.44e-16 | 1e-12 | pass |
| V11-EQ-127 | 9.4.2 equation (127) | 3.58 | 3.58 | 0 | 1e-12 | pass |
| V11-EQ-128 | 9.4.2 equation (128) | 2.25 | 2.25 | 0 | 1e-12 | pass |
| V11-EQ-129 | 9.4.2 equation (129) | 0.560067285926 | 0.560067285926 | 0 | 1e-12 | pass |
| V11-EQ-130 | 9.4.2 equation (130) | 4.12795348811 | 4.12795348811 | 0 | 1e-12 | pass |
| V11-EQ-131 | 9.4.3 equation (131) | 2.5 | 2.5 | 0 | 1e-12 | pass |
| V11-EQ-132 | 9.4.7 equation (132) | 0.505 | 0.505 | 0 | 1e-12 | pass |
| V11-EQ-133 | 9.4.7 equation (133) | 0.255 | 0.255 | 0 | 1e-12 | pass |
| V11-EQ-134 | 9.4.7 equation (134) | 0.44 | 0.44 | 0 | 1e-12 | pass |
| V11-EQ-135 | 9.4.7 equation (135) | 0.76 | 0.76 | 0 | 1e-12 | pass |
| V11-TBL-22 | Table 22 | 5 | 5 | 0 | 0 | pass |
| V11-TBL-23 | Table 23 | 4 | 4 | 0 | 0 | pass |
| V11-PROC-9.3.7 | 9.3.7 governing shear | 80 | 80 | 0 | 0 | pass |
| V11-PROC-9.4.8 | 9.4.8 edge return | 0.9 | 0.9 | 1.11e-16 | 1e-12 | pass |
| V12-EQ-136 | 10.1.2 equation (136) | 851.25 | 851.25 | 0 | 1e-12 | pass |
| V12-EQ-137 | 10.1.2 equation (137) | 1562.5 | 1562.5 | 0 | 1e-12 | pass |
| V12-EQ-138 | 10.1.2 equation (138) | 658.596993616 | 658.596993616 | 0 | 1e-12 | pass |
| V12-EQ-139 | 10.1.2 equation (139) | 1052.82032303 | 1052.82032303 | 0 | 1e-12 | pass |
| V12-EQ-140 | 10.3.1 equation (140) | 2100 | 2100 | 0 | 0 | pass |
| V12-EQ-141 | 10.3.4 equation (141) | 2.34946802489 | 2.34946802489 | 0 | 1e-12 | pass |
| V12-EQ-142 | 10.3.4 equation (142) | 1.16979530373 | 1.16979530373 | 2.22e-16 | 1e-12 | pass |
| V12-EQ-143 | 10.3.4 equation (143) | 1.7621331278 | 1.7621331278 | 4.44e-16 | 1e-12 | pass |
| V12-EQ-144 | 10.3.4 equation (144) | 1.304 | 1.304 | 0 | 1e-12 | pass |
| V12-EQ-145 | 10.3.4 equation (145) | 0.766964988847 | 0.766964988847 | 0 | 1e-12 | pass |
| V12-EQ-146 | 10.3.6 equation (146) | 1.41421356237 | 1.41421356237 | 0 | 1e-12 | pass |
| V12-EQ-147 | 10.3.8 equation (147) | 0.35 | 0.35 | 0 | 1e-12 | pass |
| V12-TBL-24 | Table 24 | 800 | 800 | 0 | 0 | pass |
| V12-TBL-25 | Table 25 | 700 | 700 | 0 | 0 | pass |
| V12-TBL-26 | Table 26 | 950 | 950 | 0 | 0 | pass |
| V12-TBL-27 | Table 27 | 640 | 640 | 0 | 0 | pass |
| V12-TBL-28 | Table 28 | 1300 | 1300 | 0 | 0 | pass |
| V12-TBL-29 | Table 29 | 0.928 | 0.928 | 0 | 1e-12 | pass |
| V12-TBL-30 | Table 30 | 0.725 | 0.725 | 0 | 0 | pass |
| V12-TBL-31 | Table 31 special case | 0.869756680881 | 0.869756680881 | 1.11e-16 | 1e-12 | pass |
| V12-TBL-32 | Table 32 | 200 | 200 | 0 | 0 | pass |
| V12-TBL-33 | Table 33 | 200 | 200 | 0 | 0 | pass |
| V13-EQ-148 | 11.1.1 equation (148) | 0.264248775201 | 0.264248775201 | 0 | 1e-12 | pass |
| V13-EQ-149 | 11.1.2 equation (149) | 1 | 1 | 0 | 1e-12 | pass |
| V13-EQ-150 | 11.1.2 equation (150) | 75 | 75 | 1.42e-14 | 1e-12 | pass |
| V13-EQ-151-MER | 11.1.2 equation (151) | 50 | 50 | 0 | 1e-12 | pass |
| V13-EQ-151-HOOP | 11.1.2 equation (151) | 100 | 100 | 0 | 1e-12 | pass |
| V13-EQ-152 | 11.1.2 equation (152) | 50 | 50 | 0 | 1e-12 | pass |
| V13-EQ-153-MER | 11.1.2 equation (153) | 57.735026919 | 57.735026919 | 7.11e-15 | 1e-12 | pass |
| V13-EQ-153-HOOP | 11.1.2 equation (153) | 115.470053838 | 115.470053838 | 1.42e-14 | 1e-12 | pass |
| V13-EQ-154 | 11.2.1 equation (154) | 0.625 | 0.625 | 0 | 1e-12 | pass |
| V13-EQ-155 | 11.2.1 equation (155) | 0.592572815534 | 0.592572815534 | 0 | 1e-12 | pass |
| V13-EQ-156 | 11.2.2 equation (156) | 0.578428357182 | 0.578428357182 | 0 | 1e-12 | pass |
| V13-EQ-157 | 11.2.3 equation (157) | 86.2357234561 | 86.2357234561 | 0 | 1e-12 | pass |
| V13-EQ-158 | 11.2.3 equation (158) | 27.1176874016 | 27.1176874016 | 0 | 1e-12 | pass |
| V13-EQ-159 | 11.2.4 equation (159) | 0.5 | 0.5 | 0 | 1e-12 | pass |
| V13-EQ-160 | 11.2.4 equation (160) | 22.66 | 22.66 | 0 | 1e-12 | pass |
| V13-EQ-161 | 11.2.4 equation (161) | 3.502 | 3.502 | 0 | 1e-12 | pass |
| V13-EQ-162 | 11.2.5 equation (162) | 0.5 | 0.5 | 0 | 1e-12 | pass |
| V13-EQ-163 | 11.2.6 equation (163) | 0.625 | 0.625 | 0 | 1e-12 | pass |
| V13-EQ-164 | 11.2.6 equation (164) | 4710000 | 4710000 | 9.31e-10 | 1e-09 | pass |
| V13-EQ-165 | 11.2.6 equation (165) | 1096.96551146 | 1096.96551146 | 0 | 1e-12 | pass |
| V13-EQ-166 | 11.2.7 equation (166) | 0.5 | 0.5 | 0 | 1e-12 | pass |
| V13-EQ-167 | 11.2.7 equation (167) | 56.65 | 56.65 | 0 | 1e-12 | pass |
| V13-EQ-168 | 11.2.8 equation (168) | 0.5 | 0.5 | 0 | 1e-12 | pass |
| V13-EQ-169 | 11.2.9 equation (169) | 0.25 | 0.25 | 0 | 1e-12 | pass |
| V13-PROC-11.1.1 | 11.1.1 principal stresses | 106.055512755 | 106.055512755 | 1.14e-13 | 1e-10 | pass |
| V13-PROC-11.2.1 | 11.2.1 critical stress | 300 | 300 | 0 | 0 | pass |
| V13-PROC-11.2.4 | 11.2.4 ring force | 50000 | 50000 | 0 | 1e-09 | pass |
| V13-PROC-11.2.9 | 11.2.9 spherical critical stress | 206 | 206 | 0 | 1e-12 | pass |
| V13-T34-100 | Table 34 | 0.22 | 0.22 | 0 | 0 | pass |
| V13-T34-200 | Table 34 | 0.18 | 0.18 | 0 | 0 | pass |
| V13-T34-300 | Table 34 | 0.16 | 0.16 | 0 | 0 | pass |
| V13-T34-400 | Table 34 | 0.14 | 0.14 | 0 | 0 | pass |
| V13-T34-600 | Table 34 | 0.11 | 0.11 | 0 | 0 | pass |
| V13-T34-800 | Table 34 | 0.09 | 0.09 | 0 | 0 | pass |
| V13-T34-1000 | Table 34 | 0.08 | 0.08 | 0 | 0 | pass |
| V13-T34-1500 | Table 34 | 0.07 | 0.07 | 0 | 0 | pass |
| V13-T34-2500 | Table 34 | 0.06 | 0.06 | 0 | 0 | pass |
| V14-EQ-170 | 12.1.2 equation (170) | 0.385591070523 | 0.385591070523 | 0 | 1e-12 | pass |
| V14-EQ-171 | 12.1.2 equation (171) | 1.314 | 1.314 | 0 | 1e-12 | pass |
| V14-EQ-172 | 12.1.2 equation (172) | 1.63 | 1.63 | 0 | 1e-12 | pass |
| V14-EQ-173 | 12.2 equation (173) | 0.365074840238 | 0.365074840238 | 0 | 1e-12 | pass |
| V14-T36-TENSION | Table 36 | 1.31578947368 | 1.31578947368 | 0 | 1e-12 | pass |
| V14-T36-COMPRESSION | Table 36 | 3.33333333333 | 3.33333333333 | 0 | 1e-12 | pass |
| V14-PROC-ALPHA-CAP | 12.1.2 | 0.77 | 0.77 | 0 | 0 | pass |
| V14-PROC-CRANE-ALPHA | 12.2 | 0.77 | 0.77 | 0 | 0 | pass |
| V14-T35-run_le_420-G1 | Table 35 | 120 | 120 | 0 | 0 | pass |
| V14-T35-run_le_420-G2 | Table 35 | 100 | 100 | 0 | 0 | pass |
| V14-T35-run_gt_420_le_440-G1 | Table 35 | 128 | 128 | 0 | 0 | pass |
| V14-T35-run_gt_420_le_440-G2 | Table 35 | 106 | 106 | 0 | 0 | pass |
| V14-T35-run_gt_440_le_520-G1 | Table 35 | 132 | 132 | 0 | 0 | pass |
| V14-T35-run_gt_440_le_520-G2 | Table 35 | 108 | 108 | 0 | 0 | pass |
| V14-T35-run_gt_520_le_580-G1 | Table 35 | 136 | 136 | 0 | 0 | pass |
| V14-T35-run_gt_520_le_580-G2 | Table 35 | 110 | 110 | 0 | 0 | pass |
| V14-T35-run_gt_580_le_675-G1 | Table 35 | 145 | 145 | 0 | 0 | pass |
| V14-T35-run_gt_580_le_675-G2 | Table 35 | 116 | 116 | 0 | 0 | pass |
| V14-T35-G3 | Table 35 | 90 | 90 | 0 | 0 | pass |
| V14-T35-G4 | Table 35 | 75 | 75 | 0 | 0 | pass |
| V14-T35-G5 | Table 35 | 60 | 60 | 0 | 0 | pass |
| V14-T35-G6 | Table 35 | 45 | 45 | 0 | 0 | pass |
| V14-T35-G7 | Table 35 | 36 | 36 | 0 | 0 | pass |
| V14-T35-G8 | Table 35 | 27 | 27 | 0 | 0 | pass |
| V14-K1-K1-01-ROLLED_OR_MACHINED_EDGE | Annex K Table K.1 | 1 | 1 | 0 | 0 | pass |
| V14-K1-K1-01-MACHINE_GAS_CUT_EDGE | Annex K Table K.1 | 2 | 2 | 0 | 0 | pass |
| V14-K1-K1-02-RADIUS_200 | Annex K Table K.1 | 1 | 1 | 0 | 0 | pass |
| V14-K1-K1-02-RADIUS_10 | Annex K Table K.1 | 4 | 4 | 0 | 0 | pass |
| V14-K1-K1-03-FRICTION_CONNECTION | Annex K Table K.1 | 1 | 1 | 0 | 0 | pass |
| V14-K1-K1-04-PAIRED_COVER_PLATES | Annex K Table K.1 | 4 | 4 | 0 | 0 | pass |
| V14-K1-K1-04-ONE_SIDED_COVER_PLATE | Annex K Table K.1 | 5 | 5 | 0 | 0 | pass |
| V14-K1-K1-05-SMOOTH_TRANSITION | Annex K Table K.1 | 2 | 2 | 0 | 0 | pass |
| V14-K1-K1-06-RECTANGULAR_GUSSET | Annex K Table K.1 | 7 | 7 | 0 | 0 | pass |
| V14-K1-K1-07-GUSSET_ALPHA_LE_45 | Annex K Table K.1 | 4 | 4 | 0 | 0 | pass |
| V14-K1-K1-08-LAP_GUSSET_PERIMETER_WELD | Annex K Table K.1 | 7 | 7 | 0 | 0 | pass |
| V14-K1-K1-09-UNTREATED_BUTT_SAME | Annex K Table K.1 | 4 | 4 | 0 | 0 | pass |
| V14-K1-K1-10-UNTREATED_BUTT_DIFFERENT | Annex K Table K.1 | 5 | 5 | 0 | 0 | pass |
| V14-K1-K1-11-GROUND_FLUSH_SAME | Annex K Table K.1 | 2 | 2 | 0 | 0 | pass |
| V14-K1-K1-11-GROUND_FLUSH_DIFFERENT | Annex K Table K.1 | 3 | 3 | 0 | 0 | pass |
| V14-K1-K1-12-SHEET_ON_BACKING | Annex K Table K.1 | 4 | 4 | 0 | 0 | pass |
| V14-K1-K1-12-PIPE_ON_BACKING_RING | Annex K Table K.1 | 4 | 4 | 0 | 0 | pass |
| V14-K1-K1-12-ROLLED_PROFILE_BUTT | Annex K Table K.1 | 4 | 4 | 0 | 0 | pass |
| V14-K1-K1-13-CONTINUOUS_LONGITUDINAL_WELDS | Annex K Table K.1 | 2 | 2 | 0 | 0 | pass |
| V14-K1-K1-14-AUXILIARY_ALPHA_LE_45 | Annex K Table K.1 | 4 | 4 | 0 | 0 | pass |
| V14-K1-K1-14-AUXILIARY_ALPHA_90 | Annex K Table K.1 | 7 | 7 | 0 | 0 | pass |
| V14-K1-K1-15-COVER_PLATE_TERMINATION | Annex K Table K.1 | 7 | 7 | 0 | 0 | pass |
| V14-K1-K1-16-TRANSVERSE_WELD_SMOOTH | Annex K Table K.1 | 4 | 4 | 0 | 0 | pass |
| V14-K1-K1-17-DIAPHRAGM_OR_RIB | Annex K Table K.1 | 5 | 5 | 0 | 0 | pass |
| V14-K1-K1-18-FIGURE_TOP | Annex K Table K.1 | 6 | 6 | 0 | 0 | pass |
| V14-K1-K1-18-FIGURE_BOTTOM | Annex K Table K.1 | 5 | 5 | 0 | 0 | pass |
| V14-K1-K1-19-DOUBLE_FLANK_WELDS | Annex K Table K.1 | 8 | 8 | 0 | 0 | pass |
| V14-K1-K1-19-FLANK_AND_END_WELDS | Annex K Table K.1 | 7 | 7 | 0 | 0 | pass |
| V14-K1-K1-19-FORCE_THROUGH_BASE_METAL | Annex K Table K.1 | 7 | 7 | 0 | 0 | pass |
| V14-K1-K1-19-STEEL_ROPE_ANCHOR_CHEEKS | Annex K Table K.1 | 8 | 8 | 0 | 0 | pass |
| V14-K1-K1-20-TM_DM_GE_1_14 | Annex K Table K.1 | 7 | 7 | 0 | 0 | pass |
| V14-K1-K1-20-TM_DM_1_20_TO_1_14 | Annex K Table K.1 | 8 | 8 | 0 | 0 | pass |
| V14-K1-K1-21-TM_DM_GE_1_14 | Annex K Table K.1 | 6 | 6 | 0 | 0 | pass |
| V14-K1-K1-21-TM_DM_1_20_TO_1_14 | Annex K Table K.1 | 7 | 7 | 0 | 0 | pass |
| V14-K1-K1-21-TM_DM_1_35_TO_1_20 | Annex K Table K.1 | 8 | 8 | 0 | 0 | pass |
| V15-EQ174 | 13.5 equation (174) | 9 | 9 | 0 | 0 | pass |
| V15-EQ175 | 14.1.14 equation (175) | 0.2 | 0.2 | 0 | 1e-12 | pass |
| V15-EQ176 | 14.1.16 equation (176) | 0.357142857143 | 0.357142857143 | 0 | 1e-12 | pass |
| V15-EQ177 | 14.1.16 equation (177) | 0.333333333333 | 0.333333333333 | 0 | 1e-12 | pass |
| V15-EQ178 | 14.1.17 equation (178) | 0.5 | 0.5 | 0 | 1e-12 | pass |
| V15-EQ179 | 14.1.17 equation (179) | 1 | 1 | 0 | 1e-12 | pass |
| V15-EQ180 | 14.1.18 equation (180) | 0.25 | 0.25 | 0 | 1e-12 | pass |
| V15-EQ181 | 14.1.18 equation (181) | 0.25 | 0.25 | 0 | 1e-12 | pass |
| V15-EQ182 | 14.1.19 equation (182) | 0.266666666667 | 0.266666666667 | 0 | 1e-12 | pass |
| V15-EQ183 | 14.1.19 equation (183) | 39.0512483795 | 39.0512483795 | 0 | 1e-12 | pass |
| V15-EQ184 | 14.1.20 equation (184) | 11200 | 11200 | 1.82e-12 | 1e-09 | pass |
| V15-EQ185 | 14.1.20 equation (185) | 8800 | 8800 | 0 | 1e-09 | pass |
| V15-T37 | Table 37 | 8 | 8 | 0 | 0 | pass |
| V15-T38 | Table 38 | 6 | 6 | 0 | 0 | pass |
| V15-T39-BF | Table 39 | 0.9 | 0.9 | 0 | 0 | pass |
| V15-T39-BZ | Table 39 | 1.05 | 1.05 | 0 | 0 | pass |
| V16-EQ186 | 14.2.9 equation (186) | 105840 | 105840 | 0 | 1e-09 | pass |
| V16-EQ187 | 14.2.9 equation (187) | 194400 | 194400 | 0 | 1e-09 | pass |
| V16-EQ188 | 14.2.9 equation (188) | 68400 | 68400 | 0 | 1e-09 | pass |
| V16-EQ189 | 14.2.10 equation (189) | 3 | 3 | 0 | 0 | pass |
| V16-EQ190 | 14.2.13 equation (190) | 0.578962151509 | 0.578962151509 | 0 | 1e-12 | pass |
| V16-EQ191 | 14.3.3 equation (191) | 29386.6666667 | 29386.6666667 | 0 | 1e-09 | pass |
| V16-EQ192 | 14.3.4 equation (192) | 5 | 5 | 0 | 0 | pass |
| V16-T40 | Table 40 | 22 | 22 | 0 | 0 | pass |
| V16-T41 | Table 41 | 0.72 | 0.72 | 1.11e-16 | 1e-12 | pass |
| V16-T42-MU | Table 42 | 0.58 | 0.58 | 0 | 0 | pass |
| V16-T42-GH | Table 42 | 1.053 | 1.053 | 0 | 1e-12 | pass |
| V16-PROC-LONG | 14.2.10 | 0.98 | 0.98 | 0 | 1e-12 | pass |
| V16-PROC-AREA | 14.3.11 | 944 | 944 | 0 | 1e-12 | pass |
| V17-PROC-T | 14.4.1 Table 43 definitions | 360 | 360 | 0 | 1e-12 | pass |
| V17-PROC-V | 14.4.1 Table 43 definitions | 528 | 528 | 0 | 1e-12 | pass |
| V17-EQ193 | 14.4.1 equation (193) | 0.1171875 | 0.1171875 | 0 | 1e-12 | pass |
| V17-EQ194 | 14.4.1 equation (194) | 0.104651162791 | 0.104651162791 | 0 | 1e-12 | pass |
| V17-EQ195 | 14.4.1 equation (195) | 0.576 | 0.576 | 0 | 1e-12 | pass |
| V17-EQ196 | 14.4.1 equation (196) | 0.208023858683 | 0.208023858683 | 0 | 1e-12 | pass |
| V17-EQ197 | 14.4.1 equation (197) | 0.185770143568 | 0.185770143568 | 0 | 1e-12 | pass |
| V17-EQ198 | 14.4.1 equation (198) | 0.6678068032 | 0.6678068032 | 0 | 1e-12 | pass |
| V17-T43-ROWS | Table 43 | 4 | 4 | 0 | 0 | pass |
| V17-PROC-ALPHA | Table 43 alpha definition | 0.4 | 0.4 | 0 | 0 | pass |
| V17-PROC-MULTILAYER | 14.4.2 | 250000 | 250000 | 0 | 0 | pass |
| V18-SP16-TBL-44 | 15.1 Table 44 | 230 | 230 | 0 | 0 | pass |
| V18-SP16-TBL-44-COLD | 15.1 Table 44 | 40 | 40 | 0 | 0 | pass |
| V18-SP16-PROC-15.1-SPACING-ASSESSMENT | 15.1 | 1 | 1 | 0 | 0 | pass |
| V18-SP16-PROC-15.1-PAIRED-BRACING | 15.1 Table 44 note | 40 | 40 | 0 | 0 | pass |
| V18-SP16-PROC-15.12.1-FRICTION-FLAT | 15.12.1 | 0.3 | 0.3 | 0 | 0 | pass |
| V18-SP16-PROC-15.12.1-FRICTION-ROLLER | 15.12.1 | 0.03 | 0.03 | 0 | 0 | pass |
| V18-SP16-EQ-199 | 15.12.2 equation (199) | 0.0878431372549 | 0.0878431372549 | 0 | 1e-12 | pass |
| V18-SP16-PROC-15.12.2-ANGLE-APPLICABILITY | 15.12.2 | 1 | 1 | 0 | 0 | pass |
| V18-SP16-EQ-200 | 15.12.3 equation (200) | 0.686274509804 | 0.686274509804 | 0 | 1e-12 | pass |
| V18-SP16-PROC-15-CLASSIFICATION | Section 15 | 80 | 80 | 0 | 0 | pass |
| V19-SP16-TBL-45-ROWS | 16.4 Table 45 | 8 | 8 | 0 | 0 | pass |
| V19-SP16-TBL-45-FIRST | 16.4 Table 45 | 0.95 | 0.95 | 0 | 0 | pass |
| V19-SP16-TBL-45-LAST | 16.4 Table 45 | 0.9 | 0.9 | 0 | 0 | pass |
| V19-SP16-TBL-46-ROWS | 16.15 Table 46 | 8 | 8 | 0 | 0 | pass |
| V19-SP16-TBL-46-SWITCHYARD | 16.15 Table 46 | 100 | 100 | 0 | 0 | pass |
| V19-SP16-TBL-46-EQUIPMENT | 16.15 Table 46 | 300 | 300 | 0 | 0 | pass |
| V19-SP16-EQ-201 | 16.5 equation (201) | 12 | 12 | 0 | 0 | pass |
| V19-SP16-EQ-202 | 16.5 equation (202) | 15 | 15 | 0 | 0 | pass |
| V19-SP16-PROC-16.5-MU | 16.5 mu definition | 2.72222222222 | 2.72222222222 | 0 | 1e-12 | pass |
| V19-SP16-EQ-203 | 16.5 equation (203) | 54.4444444444 | 54.4444444444 | 0 | 1e-12 | pass |
| V19-SP16-EQ-204 | 16.6 equation (204) | 0.4152 | 0.4152 | 0 | 1e-12 | pass |
| V19-SP16-EQ-205 | 16.6 equation (205) | 0.36 | 0.36 | 5.55e-17 | 1e-12 | pass |
| V19-SP16-PROC-16.8-BOW | 16.8 initial bow | 15.6 | 15.6 | 0 | 1e-12 | pass |
| V19-SP16-PROC-16.8-INERTIA | 16.8 equivalent inertia | 80000000 | 80000000 | 0 | 1e-06 | pass |
| V19-SP16-PROC-16.8-DELTA | 16.8 second-order delta | 0.126213592233 | 0.126213592233 | 0 | 1e-12 | pass |
| V19-SP16-EQ-206 | 16.8 equation (206) | 342412307.692 | 342412307.692 | 0 | 1e-06 | pass |
| V19-SP16-EQ-207 | 16.9 equation (207) | 113664.553846 | 113664.553846 | 0 | 1e-09 | pass |
| V19-SP16-EQ-208 | 16.10 equation (208) | 116000 | 116000 | 1.46e-11 | 1e-09 | pass |
| V19-SP16-EQ-209 | 16.12 equation (209) | 1.075 | 1.075 | 0 | 1e-12 | pass |
| V19-SP16-EQ-210 | 16.12 equation (210) | 1.046 | 1.046 | 0 | 1e-12 | pass |
| V19-SP16-EQ-211 | 16.12 equation (211) | 1.03 | 1.03 | 0 | 1e-12 | pass |
| V19-SP16-EQ-212 | 16.12 equation (212) | 1.011 | 1.011 | 0 | 1e-12 | pass |
| V19-SP16-PROC-16.12-WELDED | 16.12 welded rule | 1.036 | 1.036 | 0 | 1e-12 | pass |
| V19-SP16-PROC-16.15-EMERGENCY | 16.15 Table 46 note 1 | 0 | 0 | 0 | 0 | pass |
| V19-SP16-PROC-16.13-LENGTH | 16.13 | 3000 | 3000 | 0 | 0 | pass |
| V19-SP16-PROC-16.14-SLENDERNESS | 16.14 | 1 | 1 | 0 | 0 | pass |
| V19-SP16-PROC-16.16-DIAPHRAGM | 16.16 | 25 | 25 | 0 | 0 | pass |
| V19-SP16-PROC-16.20-LAMBDA | 16.20 wall slenderness | 2.04618992371 | 2.04618992371 | 0 | 1e-12 | pass |
| V19-SP16-EQ-214 | 16.20 equation (214) | 345 | 345 | 0 | 1e-10 | pass |
| V19-SP16-EQ-213 | 16.20 equation (213) | 0.289855072464 | 0.289855072464 | 0 | 1e-12 | pass |
| V20-SP16-EQ-215 | 17.16 equation (215) | 1.83357574155 | 1.83357574155 | 0 | 1e-12 | pass |
| V20-SP16-PROC-17.1-MATERIAL-GROUP | 17.1 | 1 | 1 | 0 | 0 | pass |
| V20-SP16-PROC-17.2-ROPE-SELECTION | 17.2 | 1 | 1 | 0 | 0 | pass |
| V20-SP16-PROC-17.2-ZINC | 17.2 | 1 | 1 | 0 | 0 | pass |
| V20-SP16-PROC-17.3-ZINC-TERMINATION | 17.3 | 1 | 1 | 0 | 0 | pass |
| V20-SP16-PROC-17.4-WIRE-ROUTE | 17.4 | 1 | 1 | 0 | 0 | pass |
| V20-SP16-PROC-17.5-GAMMA-AL | 17.5 | 2.5 | 2.5 | 0 | 0 | pass |
| V20-SP16-PROC-17.5-GAMMA-SA16 | 17.5 | 2.8 | 2.8 | 0 | 0 | pass |
| V20-SP16-PROC-17.5-GAMMA-SA95 | 17.5 | 2.5 | 2.5 | 0 | 0 | pass |
| V20-SP16-PROC-17.5-GAMMA-SA120 | 17.5 | 2.2 | 2.2 | 0 | 0 | pass |
| V20-SP16-PROC-17.5-GAMMA-BIMETAL | 17.5 | 2 | 2 | 0 | 0 | pass |
| V20-SP16-PROC-17.5-DESIGN-TENSION | 17.5 | 100000 | 100000 | 0 | 0 | pass |
| V20-SP16-PROC-17.7-DEVIATION-WIND | 17.7 | 1 | 1 | 0 | 1e-12 | pass |
| V20-SP16-PROC-17.7-DEVIATION-UNILATERAL | 17.7 | 1 | 1 | 0 | 1e-12 | pass |
| V20-SP16-PROC-17.8-ERECTION-CONNECTION | 17.8 | 1 | 1 | 0 | 0 | pass |
| V20-SP16-PROC-17.9-DEFLECTION | 17.9 | 12 | 12 | 0 | 0 | pass |
| V20-SP16-PROC-17.10-DIAPHRAGM | 17.10 | 7500 | 7500 | 0 | 0 | pass |
| V20-SP16-PROC-17.12-ECCENTRICITY | 17.12 | 30 | 30 | 0 | 0 | pass |
| V20-SP16-PROC-17.12-HOLE | 17.12 | 24 | 24 | 0 | 0 | pass |
| V20-SP16-PROC-17.14-FLEXIBLE-INSERT | 17.14 | 400 | 400 | 0 | 0 | pass |
| V20-SP16-PROC-17.16-SPAN-TRIGGER | 17.16 | 1 | 1 | 0 | 0 | pass |
| V20-SP16-PROC-17.17-MARKING | 17.17 | 1 | 1 | 0 | 0 | pass |
| V20-SP16-PROC-17.18-GALVANIZING | 17.18 | 1 | 1 | 0 | 0 | pass |
| V20-SP16-TBL-47-PRESTRESSED_LATTICE_MEMBER | 17.6 Table 47 | 0.9 | 0.9 | 0 | 0 | pass |
| V20-SP16-TBL-47-RING_TYPE_FLANGE | 17.6 Table 47 | 1.1 | 1.1 | 0 | 0 | pass |
| V20-SP16-TBL-47-OTHER_FLANGE_TYPE | 17.6 Table 47 | 0.9 | 0.9 | 0 | 0 | pass |
| V20-SP16-TBL-47-GUY_OR_ANTENNA_ELEMENT_COUNT_3_TO_5 | 17.6 Table 47 | 0.8 | 0.8 | 0 | 0 | pass |
| V20-SP16-TBL-47-GUY_COUNT_6_TO_8 | 17.6 Table 47 | 0.9 | 0.9 | 0 | 0 | pass |
| V20-SP16-TBL-47-GUY_COUNT_9_OR_MORE | 17.6 Table 47 | 0.95 | 0.95 | 0 | 0 | pass |
| V20-SP16-TBL-47-THIMBLE_CLAMPS_OR_POINT_CRIMP | 17.6 Table 47 | 0.75 | 0.75 | 0 | 0 | pass |
| V20-SP16-TBL-47-ROPE_SPLICE_ON_THIMBLE_OR_INSULATOR | 17.6 Table 47 | 0.55 | 0.55 | 0 | 0 | pass |
| V20-SP16-TBL-47-GUY_OR_ANTENNA_ATTACHMENT_ELEMENT | 17.6 Table 47 | 0.9 | 0.9 | 0 | 0 | pass |
| V20-SP16-TBL-47-ANCHOR_ROD_TENSION_WITH_BENDING_NO_THREAD | 17.6 Table 47 | 0.65 | 0.65 | 0 | 0 | pass |
| V20-SP16-TBL-47-EYE_PLATE_IN_TENSION | 17.6 Table 47 | 0.65 | 0.65 | 0 | 0 | pass |
| V20-SP16-TBL-47-ROPE_ATTACHMENT_MECHANICAL_DETAIL_EXCEPT_HINGE_PIN | 17.6 Table 47 | 0.8 | 0.8 | 0 | 0 | pass |
| V20-SP16-TBL-47-HINGE_PIN_IN_BEARING | 17.6 Table 47 | 0.9 | 0.9 | 0 | 0 | pass |
| V21-SP16-PROC-18.1.1-CATEGORY | 18.1.1 | 1 | 1 | 0 | 0 | pass |
| V21-SP16-PROC-18.1.3-EXEMPTION | 18.1.3 | 1 | 1 | 0 | 0 | pass |
| V21-SP16-PROC-18.2.4-RY | 18.2.4 | 338.095238095 | 338.095238095 | 0 | 1e-12 | pass |
| V21-SP16-PROC-18.2.5-RWF | 18.2.5 | 224.4 | 224.4 | 0 | 1e-12 | pass |
| V21-SP16-PROC-18.2.6-RBS | 18.2.6 | 150 | 150 | 0 | 0 | pass |
| V21-SP16-PROC-18.2.7-RIVET-CAPACITY | 18.2.7 | 113040 | 113040 | 1.46e-11 | 1e-09 | pass |
| V21-SP16-PROC-18.3.9-GROUP1 | 18.3.9 | 60 | 60 | 0 | 0 | pass |
| V21-SP16-PROC-18.3.9-GROUP2 | 18.3.9 | 120 | 120 | 0 | 0 | pass |
| V21-SP16-PROC-18.3.9-GROUP4 | 18.3.9 | 240 | 240 | 0 | 0 | pass |
| V21-SP16-EQ-216-GAMMA-N | 18.3.13 equation (216) | 0.874242424242 | 0.874242424242 | 0 | 1e-12 | pass |
| V21-SP16-EQ-216 | 18.3.13 equation (216) | 0.641889723346 | 0.641889723346 | 0 | 1e-12 | pass |
| V21-SP16-EQ-217-GAMMA-M | 18.3.13 equation (217) | 1 | 1 | 0 | 0 | pass |
| V21-SP16-EQ-217 | 18.3.13 equation (217) | 0.897867564534 | 0.897867564534 | 0 | 1e-12 | pass |
| V21-SP16-EQ-218 | 18.3.15 equation (218) | 0.746714456392 | 0.746714456392 | 0 | 1e-12 | pass |
| V21-SP16-EQ-219 | 18.3.14 equation (219) | 0.789984376953 | 0.789984376953 | 0 | 1e-12 | pass |
| V21-SP16-EQ-220 | 18.3.14 equation (220) | 78.9984376953 | 78.9984376953 | 0 | 1e-12 | pass |
| V21-SP16-EQ-221 | 18.3.14 equation (221) | 9.99843769529 | 9.99843769529 | 0 | 1e-12 | pass |
| V21-SP16-EQ-222-V | 18.3.14 equation (222) | 0.0256 | 0.0256 | 3.47e-18 | 1e-15 | pass |
| V21-SP16-EQ-222 | 18.3.14 equation (222) | 64 | 64 | 0 | 1e-12 | pass |
| V21-SP16-EQ-223 | 18.3.15 equation (223) | 310 | 310 | 0 | 1e-12 | pass |
| V21-SP16-EQ-224 | 18.3.15 equation (224) | 1.06777777778 | 1.06777777778 | 0 | 1e-12 | pass |
| V21-SP16-PROC-18.3.16-DEVIATION | 18.3.16 | 1 | 1 | 0 | 0 | pass |
| V21-SP16-TBL-48-shear-B-St2_St3 | 18.2.7 Table 48 | 180 | 180 | 0 | 0 | pass |
| V21-SP16-TBL-48-shear-B-09G2 | 18.2.7 Table 48 | 220 | 220 | 0 | 0 | pass |
| V21-SP16-TBL-48-shear-C-St2_St3 | 18.2.7 Table 48 | 160 | 160 | 0 | 0 | pass |
| V21-SP16-TBL-48-tension_head_pull_off-B-St2_St3 | 18.2.7 Table 48 | 120 | 120 | 0 | 0 | pass |
| V21-SP16-TBL-48-tension_head_pull_off-B-09G2 | 18.2.7 Table 48 | 150 | 150 | 0 | 0 | pass |
| V21-SP16-TBL-48-bearing-B-St2_St3 | 18.2.7 Table 48 | 600 | 600 | 0 | 0 | pass |
| V21-SP16-TBL-48-bearing-C-St2_St3 | 18.2.7 Table 48 | 510 | 510 | 0 | 0 | pass |
| V21-SP16-TBL-48-COUNTERSUNK | 18.2.7 Table 48 note | 144 | 144 | 0 | 0 | pass |

## Limitations

- The supplied implemented clauses through Section 18 and Annexes Д and Ж contain no complete numerical worked example for independent normative reproduction.
- Table D.1 is a rounded tabulation of equations (8)-(9), so this cross-check is not independent of the normative formula model.
