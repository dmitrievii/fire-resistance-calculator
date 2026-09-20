from __future__ import annotations

import json
from pathlib import Path

from standard_core import fire_sp554_bridge as bridge
from standard_core.runner import run_case
from standard_core.schema_validation import validate_case

ROOT = Path(__file__).resolve().parents[1]


def test_fire_d1_case_schema_is_strict_and_example_validates():
    schema = json.loads((ROOT / "schemas/sp554_sp16_fire_dependency_bridge_case.schema.json").read_text(encoding="utf-8"))
    case = json.loads((ROOT / "examples/sp554_sp16_fire_dependency_bridge_example.json").read_text(encoding="utf-8"))
    assert validate_case(case, schema) == []
    case["hidden_default"] = True
    assert any("Unexpected property" in error for error in validate_case(case, schema))


def test_fire_d1_member_bridge_is_complete_against_frozen_n1_n7():
    result = bridge._bridge_workflow(ROOT, False)
    assert result["status"] == "COMPLETE"
    assert result["stage_gate_pass"] is True
    assert all(result["stage_flags"].values())
    assert result["member_mechanical_dependency_closure_pass"] is True
    assert all(row["pass"] for row in result["interface_groups"])


def test_fire_d1_mechanical_dependency_census_is_stable():
    result = bridge._bridge_workflow(ROOT, False)
    assert result["sp554_mechanical_node_count"] == 71
    assert result["sp16_quantity_binding_count"] == 92
    assert result["sp16_unique_producer_count"] == 53
    assert result["cross_standard_edge_count"] == 75


def test_fire_d1_has_no_missing_required_producer_and_no_design_resistance_leak():
    result = bridge._bridge_workflow(ROOT, False)
    assert result["missing_required_producers"] == []
    assert result["prohibited_design_resistance_fire_bindings"] == []
    assert result["normative_strength_basis_pass"] is True


def test_fire_d1_connection_and_thermal_scope_are_not_overclaimed():
    member_only = bridge._bridge_workflow(ROOT, False)
    assert member_only["connection_scope_status"] == "OUTSIDE_FIRE_D1_MEMBER_SCOPE"
    assert member_only["thermal_scope_status"] == "NOT_IN_FIRE_D1_SCOPE"
    with_connections = bridge._bridge_workflow(ROOT, True)
    assert with_connections["connection_scope_status"] == "DEFERRED"
    assert with_connections["member_mechanical_dependency_closure_pass"] is True


def test_fire_d1_runner_materializes_dependency_audit_output():
    result = run_case(ROOT / "examples/sp554_sp16_fire_dependency_bridge_example.json", ROOT)
    assert result["engineering_calculation_performed"] is False
    assert result["results"]["status"] == "COMPLETE"
    assert result["results"]["member_mechanical_dependency_closure_pass"] is True
    assert (ROOT / "outputs/sp554_sp16_fire_dependency_bridge_result.json").exists()
    assert (ROOT / "reports/sp554_sp16_fire_dependency_bridge_case_report.json").exists()
