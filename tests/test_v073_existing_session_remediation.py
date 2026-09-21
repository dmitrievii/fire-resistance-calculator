from __future__ import annotations

from types import SimpleNamespace

from standard_core.fire_ui0 import ExecutionRegistry, FireDAGModel, GuidedCalculationSession
from standard_core.sp16_mech7_v073_session_remediation import (
    MATERIAL_EDITOR_NODE_ID,
    replay_with_material_safety_category,
)
from streamlit_guided_ux_v073 import (
    _legacy_table3_migration_required,
    _remediate_application,
)


def _tiny_model() -> FireDAGModel:
    graph = {
        "graph_id": "test-v073-legacy-replay",
        "engine_contract": {},
        "quantities": [
            {
                "id": "fy_norm",
                "name_ru": "Ryn",
                "data_type": "number",
                "canonical_unit": "N/mm2",
                "source_policy": {},
            },
            {
                "id": "material_safety_category",
                "name_ru": "Категория таблицы 3",
                "data_type": "enum",
                "canonical_unit": None,
                "enum_values": [
                    {"value": "statistical_control", "label": "statistical_control"},
                    {"value": "other_conforming", "label": "other_conforming"},
                ],
                "source_policy": {},
            },
            {
                "id": "migrated_ok",
                "name_ru": "migration result",
                "data_type": "boolean",
                "canonical_unit": None,
                "source_policy": {},
            },
        ],
        "nodes": [
            {
                "id": MATERIAL_EDITOR_NODE_ID,
                "node_type": "input",
                "owner_standard_id": "SP16_2017",
                "title": "Material",
                "produces": [{"quantity_id": "fy_norm", "required": True}],
                "input_spec": {"user_prompt": "Material"},
                "normative_refs": [],
            },
            {
                "id": "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER",
                "node_type": "calculation",
                "owner_standard_id": "SP16_2017",
                "title": "Binder",
                "consumes": [
                    {"quantity_id": "fy_norm", "required": True},
                    {"quantity_id": "material_safety_category", "required": True},
                ],
                "produces": [{"quantity_id": "migrated_ok", "required": True}],
                "normative_refs": [],
            },
            {
                "id": "RESULT",
                "node_type": "result",
                "owner_standard_id": "SP16_2017",
                "title": "Result",
                "produces": [],
                "consumes": [],
                "normative_refs": [],
            },
        ],
        "edges": [
            {
                "id": "E1",
                "from_node_id": MATERIAL_EDITOR_NODE_ID,
                "to_node_id": "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER",
                "edge_type": "control",
            },
            {
                "id": "E2",
                "from_node_id": "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER",
                "to_node_id": "RESULT",
                "edge_type": "control",
            },
        ],
    }
    return FireDAGModel(graph)


def test_v073_replays_legacy_history_transactionally_with_explicit_table3_category():
    model = _tiny_model()

    def binder(values, node):
        return {"migrated_ok": values["material_safety_category"] == "statistical_control"}

    registry = ExecutionRegistry({"SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER": binder})
    legacy = GuidedCalculationSession(model, entry_node_id=MATERIAL_EDITOR_NODE_ID, registry=registry)
    legacy.submit(255.0)

    assert "material_safety_category" not in legacy.plain_values()
    assert legacy.interaction_history == [
        {"node_id": MATERIAL_EDITOR_NODE_ID, "payload": 255.0, "provenance": None}
    ]
    legacy_snapshot = legacy.snapshot()

    migrated = replay_with_material_safety_category(legacy, "statistical_control")

    # Transactional guarantee: the old object was not mutated.
    assert legacy.snapshot() == legacy_snapshot
    assert migrated is not legacy
    assert migrated.plain_values()["material_safety_category"] == "statistical_control"
    assert migrated.plain_values()["migrated_ok"] is True
    assert migrated.interaction_history == legacy.interaction_history
    assert migrated.status in {"RESULT", "COMPLETE"}


def test_v073_existing_application_remediates_service_and_detached_live_session_registries():
    def original(values, node):
        return {
            "sp16_mech7_primary_evidence": {"evidence": {}},
            "sp16_mech7_primary_binding_complete": True,
        }

    service_registry = ExecutionRegistry({"SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER": original})
    detached_registry = ExecutionRegistry({"SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER": original})
    app = SimpleNamespace(
        service=SimpleNamespace(
            registry=service_registry,
            sessions={"fire-000001": SimpleNamespace(registry=detached_registry)},
        )
    )

    assert not getattr(service_registry.executors["SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"], "_sp16_v072_remediated", False)
    assert not getattr(detached_registry.executors["SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"], "_sp16_v072_remediated", False)

    _remediate_application(app)

    assert getattr(service_registry.executors["SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"], "_sp16_v072_remediated", False)
    assert getattr(detached_registry.executors["SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"], "_sp16_v072_remediated", False)


def test_v073_legacy_prompt_is_required_only_after_material_history_without_category():
    legacy_env = {
        "state": {
            "values": {"fy_norm": {"value": 255.0}},
            "interaction_history": [{"node_id": MATERIAL_EDITOR_NODE_ID, "payload": {}}],
        }
    }
    assert _legacy_table3_migration_required(legacy_env) is True

    migrated_env = {
        "state": {
            "values": {
                "fy_norm": {"value": 255.0},
                "material_safety_category": {"value": "statistical_control"},
            },
            "interaction_history": [{"node_id": MATERIAL_EDITOR_NODE_ID, "payload": {}}],
        }
    }
    assert _legacy_table3_migration_required(migrated_env) is False

    pre_material_env = {"state": {"values": {}, "interaction_history": []}}
    assert _legacy_table3_migration_required(pre_material_env) is False
