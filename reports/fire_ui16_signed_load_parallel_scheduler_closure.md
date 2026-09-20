# FIRE-UI1.6 — Signed loads / verification plan / parallel DAG scheduler closure

Release: `v0.49_fire_ui16_signed_load_verification_plan_parallel_dag_r1`  
Parent: `v0.48_fire_ui15_weakening_continuation_hotfix_r1`

## Closed architecture defects

1. Manual stress-state selection is replaced by one signed-load model (`N`, `My`, `Mz`, `Qy`, `Qz`, `T`) and an automatically derived verification plan.
2. A guided session no longer assumes that exactly one node/branch is active. Required parallel `control`/`branch`/`handoff` routes are queued and completed independently.
3. Dependency producers execute by call/return and do not hijack the ordinary UI route of the suspended consumer.
4. Queued nodes re-check applicability immediately before execution; stale branches are skipped instead of being executed with newly contradictory state.
5. A completed leaf means branch completion, not session completion. Session completion requires no pending/blocked required branch.
6. The thermal stage cannot be scheduled ahead of unfinished mechanical verification branches.
7. Frozen declarative calculation/lookup/classification/check specifications are executable through a restricted AST/table runtime with fail-closed unsupported syntax and no arbitrary `eval`.
8. The generic UI contract now describes the active-branch queue/dependency scheduler instead of the obsolete single-node/data-never-navigate model.

## Universal temporary weakening rule

For the current supported round-hole authoring route:

`A_n = A - d*t_h`

where `t_h` is the local thickness intersected by the hole. The user then chooses either:

- `area_only_keep_gross`: keep gross `I`, `W`, and `Wpl` values by explicit engineering assumption; or
- `manual_net_properties`: supply independently calculated `Ixn`, `Iyn`, `Wxn,min`, `Wyn,min`, `Wpl,x,n`, and `Wpl,y,n` values.

The area remains program-calculated in both modes. The manual values are verified as effective downstream quantities rather than decorative UI data. A tee (`10КТ1`) is included in the regression route to prove that the area-only rule is no longer restricted to doubly symmetric I-sections.

## Signed-load end-to-end qualification

The FIRE-UI1.6 route suite contains 16 end-to-end cases, including:

- central tension;
- central compression;
- in-domain compression with independent `gamma_T(T)` and `gamma_E(T)` inversion;
- `My`;
- `Mz`;
- biaxial bending;
- `Qz`;
- `My + Qz`;
- compression + bending;
- tension + bending;
- general `N + My + Mz + Qz`;
- explicit deferred `Qy`;
- explicit deferred torsion `T`;
- round-hole area-only route;
- manual net `I/W/Wpl` route;
- tee-section round-hole area-only route.

All qualified supported routes require an empty pending queue and no branch failures at their accepted terminal. Deferred branches terminate explicitly rather than reporting a false successful mechanical completion.

## Scope boundary

This release changes guided execution, load classification, dependency scheduling and temporary net-section authoring. It does not claim new SP16/SP554 equations. `Qy` and torsion remain explicit deferred branches, full arbitrary perforated-section geometry is not implemented, and `ENGINEERING_USE_READY` remains false.
