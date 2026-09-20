# FIRE-UI1.5 — Weakening continuation hotfix closure

Release: `v0.48_fire_ui15_weakening_continuation_hotfix_r1`  
Parent: `v0.47_fire_ui14_section_weakening_simplification_r1`

## Closed defects

1. A derived `SP554_G_NET_SECTION_PROPERTIES` node can no longer become a user-facing form stop in the normal weakening route.
2. The guided route no longer reports `COMPLETE` immediately after `alpha=1` or formula (45); both branches continue to `SP554_D_GOST27751_GAMMA_CT`.
3. No-hole net properties use exact gross/net identity for any section family with resolved gross properties, including catalog tee sections.
4. Frontend duplicate submission is guarded while an answer request is in flight.

## Scope boundary

The hotfix changes presentation/state routing only. It does not change SP16/SP554 formulas. The hole-present analytical net model remains the deliberately limited FIRE-UI1.4 doubly symmetric I-section central-web-hole route.
