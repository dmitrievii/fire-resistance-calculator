# FIRE-UI1.1 questionnaire rebuild closure

Release candidate: `v0.44_fire_ui11_complete_engineering_questionnaire_section_editor_r1`.
Parent: `v0.43.2_fire_ui1_sp554_applicability_routing_hotfix_r1`.

Implemented from the first guided walkthrough review:

1. removed orphan building-use question from primary entry;
2. deferred required fire resistance until post-`Rfact` assessment;
3. made ordinary `Rreq` provenance optional;
4. hid/auto-resolved calculation-method and software-validation questions;
5. deferred fire-temperature regime to thermal stage;
6. removed early SP554 seismic-fire question from primary flow;
7. removed misleading welded-section scope warning;
8. fixed geometry/load provenance classification;
9. connected actual profile catalog to local UI;
10. created Section Editor shell with one-/two-branch/arbitrary separation;
11. removed opaque arbitrary-geometry text input from ordinary UI;
12. added engineering weakening editor shell;
13. implemented repeatable Back/Forward history navigation;
14. removed developer-facing DAG/downstream text from ordinary question cards.

The normative DAG remains separate from the presentation policy. Deferred questions are
not deleted from the graph; their correct future stages are recorded in
`data/fire_ui11_presentation_policy.json`.
