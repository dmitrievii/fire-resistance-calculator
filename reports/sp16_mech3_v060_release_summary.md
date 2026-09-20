# v0.60 / SP16-MECH3 release summary

- Canonical `Qx` and `Qy` remain independent actions; no scalar resultant `sqrt(Qx^2+Qy^2)` is introduced.
- Added `SP16_C_AMBIENT_AXIS_SHEAR_RECOVERY` and `SP16_C_FIRE_AXIS_SHEAR_RECOVERY`.
- For I/box sections, SP16 8.2.3 component stresses are materialized independently: `tau_x=Qx/Aw`, `tau_y=Qy/(2Af)`, with the existing web-hole factor applied only to the Qx/web component.
- Deterministic same-point mechanics recovery provides signed `tau_x(P)`, `tau_y(P)`, `tau_resultant(P)`, and `sigma_N+Mx+My(P)` for supported rectangular-composite section templates.
- Ambient Qy no longer automatically blocks the applicability census when its mechanics route is resolved.
- Torsion `T` remains fail-closed for SP16-MECH4.
- FIRE_LOAD_CASE also receives the new Qx/Qy mechanical state, but the legacy SP554 handoff remains intentionally fail-closed for Qy until FIRE-BRIDGE2/FIRE-MECH2.
- Corrected an inherited routing defect: a nonzero fire Qy/T can no longer run the normal SP554 branch in parallel with the deferred-result branch.
- Full `SP16_MECHANICAL_PASS` gate remains scheduled for SP16-MECH6.
