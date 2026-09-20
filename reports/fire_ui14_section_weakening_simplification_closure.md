# FIRE-UI1.4 — Simplified Section Weakening Closure

## Release

- Release: `v0.47_fire_ui14_section_weakening_simplification_r1`
- Package version: `0.47.0`
- Parent: `v0.46_fire_ui13_material_strength_editor_r1`
- DAG: `normative_graph/dag_v0.3.50_fire_ui14_section_weakening_simplification.json`
- Presentation policy: `data/fire_ui14_presentation_policy.json`
- Engineering-use flag: `False`

## Defect closed

FIRE-UI1.3 could not submit `SP554_I_SECTION_WEAKENING`: the backend treated any JSON object as a multi-output payload and therefore searched for a nested `section_weakening_model` key. FIRE-UI1.4 distinguishes a one-output node from a multi-output node. For one output, the submitted object is the value itself; the historical wrapped form remains accepted for compatibility.

## Simplified authoring contract

The primary weakening editor now exposes only:

1. no bolt holes; or
2. round bolt holes in the web, with `d` (hole diameter, mm) and `s` (pitch, mm).

Removed from the ordinary editor: cut-out type, arbitrary-hole type, web/flange selector, hole count, user-authored active transverse-section ID and arbitrary weakening geometry.

The supported geometry route is deliberately narrow. For a doubly symmetric I-section the net-property solver represents one active transverse-section hole through the web, centred at the gross centroidal axes. The removed shape in the transverse section is therefore a rectangle `d × t_w`, not the circular face area. The current model does not represent flange holes, multiple simultaneous active holes, staggered paths or general perforated sections.

## SP16 formula (45) semantics

For the shear weakening route the implementation keeps the clause 8.2.1 definition:

`alpha = s / (s - d)`

where `s` is the pitch of holes in one vertical row and `d` is the hole diameter. `s > d` is mandatory and is enforced fail-closed. The net-section central-hole simplification and the formula-(45) pitch definition are stored as separate explicit assumptions so that the UI does not silently reinterpret `s` as a longitudinal pitch.

## DAG / runtime changes

- `SP16_D_WEAKENING` is derived from `section_weakening_model` and is no longer a second user question.
- `SP554_G_NET_SECTION_PROPERTIES` has an explicit executor for the no-hole identity route and the supported central-web-hole route.
- `SP16_C_SHEAR_GROSS_PROPERTIES_WEAK`, `SP16_A_SHEAR_WEAKENING_SUPPORTED`, `SP16_C_SHEAR_ALPHA45` and `SP16_C_SHEAR_ALPHA_IDENTITY_WEAK` are bound in the FIRE-UI1.4 registry.
- Catalog section geometry can materialize `t_w` for the weakening solver when the current DAG declares that quantity.
- DAG title/provenance is updated to v0.3.50.

## Numerical smoke case

For catalog profile `20К1`, `d = 20 mm`, `s = 80 mm`:

- `t_w = 6.5 mm`
- removed transverse-section area = `20 × 6.5 = 130 mm²`
- `A_gross = 5269 mm²`
- `A_net = 5139 mm²`
- `alpha = 80 / (80 - 20) = 1.3333333333333333`

The no-hole route returns gross/net identity and `alpha = 1.0`.

## Qualification evidence

- `python main.py`: release audit **PASS**.
- Implemented equations: 240; unresolved equations: 0.
- Implemented tables: 67; unresolved tables: 0.
- Implemented procedures: 303; unresolved procedures: 0.
- Validation cases reported by release audit: 1876, **PASS**.
- Public API docstrings: 646/646 **PASS**.
- Independent normative rebaseline: **PASS**.
- `tests/test_fire_ui14_section_weakening.py` + `tests/test_fire_ui1_frontend.py`: **31/31 PASS**.
- `tests/test_phase_0_23_independent_normative_rebaseline.py`: **5/5 PASS**.
- A combined legacy qualification run produced no failures before the execution-time cap; therefore no unsupported claim of a complete full-tree pytest pass is made for this build.

## Deferred scope

- flange holes;
- several holes intersecting one active transverse section;
- arbitrary cut-outs;
- staggered net paths;
- arbitrary section weakening geometry;
- full guided SP16 → FIRE-D4 executor closure.

These remain fail-closed / outside the FIRE-UI1.4 claim.
