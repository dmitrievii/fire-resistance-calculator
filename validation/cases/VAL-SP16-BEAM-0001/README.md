# VAL-SP16-BEAM-0001 — beam validation report

**Source:** `source/source_report_original.docx`  
**SHA-256:** `c0b23def395cfa9f7d1b524a504da8570b782661780de54b62a42fb5759f42ea`  
**Source pages:** 2  
**Classification:** `PARTIAL_SOURCE_INCONSISTENT`

## Reproduced printed checks

1. SP 16.13330.2017, 8.2.1, equation (45): source `alpha = 1.0274`; production `1.02739726027` — PASS within source rounding.
2. SP 16.13330.2017, 8.2.1, equation (41): source `eta = 3.37069`; production `3.37069424883` — PASS within source rounding. Both source and production therefore give a failed strength condition (`eta > 1`).

## Why this is not a full golden case

- Page 1 reports `Wxn1 = Wxn2 = 196000 mm3`; page 2 uses `Wxn1 = Wxn2 = 1000000 mm3` in equation (41), with no derivation of the substitution.
- Page 1 identifies an 18M I-section; page 2 states that the section type is closed.
- The 1.1 material adjustment is attributed to SP 385.1325800 A.2 and is outside the SP16 production core.
- No printed expected values are supplied for the bimoment/local-load/stability/shear routes.

The original report is therefore retained as external evidence, but only the two explicitly printed scalar calculations are counted as reproduced.
