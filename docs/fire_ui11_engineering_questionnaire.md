# FIRE-UI1.1 — Complete Engineering Questionnaire / Section Editor

FIRE-UI1.1 incorporates the first manual walkthrough review into the application layer.
The normative DAG is preserved as the audit authority, while the ordinary engineering UI
uses a separate presentation policy to suppress non-decisions, defer late questions and
open specialised editors instead of generic JSON inputs.

## Primary guided order

The primary flow starts at the load-bearing scope check. `building_use_type` remains in the
normative graph for historical/audit compatibility but is not asked because no current
producer consumes it.

The early `Rreq`, fire-regime and seismic-fire questions are removed from the primary
question sequence:

- `Rreq` is reserved for the post-`Rfact` assessment stage;
- fire-temperature regime is reserved for the thermal block after critical temperature;
- SP554 5.6 seismic-fire requirements are reserved for fire-protection design;
- calculation method and software-validation nodes remain in the DAG but are auto-resolved
  to the current calculation-analytical / validated-software workflow.

## Section editor

The UI now distinguishes:

1. **Одноветвевое** — current active routes: catalog or parametric geometry;
2. **Двухветвевое** — explicit future visual composition binding to the existing SP16 built-up routes;
3. **Произвольное** — explicit future 2D contour / manual-properties editor; opaque text/JSON input is forbidden.

The catalog selector is connected to the actual interim profile database (37 families,
4069 rows). The exact row is retained by `family_id` + `source_row_id`, while properties
are presented read-only.

## Provenance

Manual provenance is required only for true external normative results. `GEOMETRY_INPUT`,
`LOAD_INPUT` and ordinary user inputs no longer trigger the old `external/derived value
requires provenance` error. In ordinary mode, entered `Rreq` may be given without source
metadata; provenance can be attached later in expert/audit mode.

## Navigation

The frontend keeps a separate history cursor. Back can therefore be pressed repeatedly
without modifying the calculation. Downstream replay/invalidation occurs only when an
earlier answer is actually changed and submitted.

## Explicit open boundaries

The following remain fail-closed/open and are not disguised by generic text inputs:

- visual two-branch section composition;
- arbitrary 2D contour editor / ready-property editor;
- SP14 seismic load-combination `m_tr` producer;
- full SP16 → FIRE-D4 executor binding;
- FIRE-D5 fire-protection design;
- bolts/connections.
