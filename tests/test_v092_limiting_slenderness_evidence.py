from __future__ import annotations

import pytest

from standard_core.fire_ui0 import ExecutionRegistry, FireUIError
from standard_core.sp16_mech7_v075_zy_runtime import BINDER_NODE_ID
from standard_core.sp16_mech7_v092_slenderness_evidence import (
    EVIDENCE_KEY,
    TRACE_SCHEMA,
    build_limiting_slenderness_trace,
    install_registry_remediation,
)


def _values(*, group4: bool = False, lambda_z: float = 80.0, lambda_y: float = 100.0) -> dict:
    return {
        "ambient_N_force": -600_000.0,
        "sp16_lambda_z_geom": lambda_z,
        "sp16_lambda_y_geom": lambda_y,
        "phi_z_sp16": 0.60,
        "phi_y_sp16": 0.50,
        "A_gross": 5000.0,
        "Ry_formula": 240.0,
        "gamma_c_compression": 1.0,
        "sp16_mech7_table32_row": "1a",
        "sp16_mech7_group4_slenderness_increase": group4,
    }


def test_table32_trace_discloses_alpha_row_limit_axes_utilization_and_pass():
    trace = build_limiting_slenderness_trace(_values())

    assert trace["schema"] == TRACE_SCHEMA
    assert trace["table32_row_id"] == "1a"
    assert trace["table32_row_formula"]["expression"] == "180-60*alpha"
    assert trace["alpha"]["governing_phi_axis"] == "y"
    assert trace["alpha"]["governing_phi"] == pytest.approx(0.5)
    assert trace["alpha"]["raw"] == pytest.approx(1.0)
    assert trace["alpha"]["result"] == pytest.approx(1.0)
    assert trace["alpha"]["minimum_applied"] is False
    assert trace["limiting_slenderness"]["base"] == pytest.approx(120.0)
    assert trace["limiting_slenderness"]["result"] == pytest.approx(120.0)
    assert trace["actual_slenderness"]["governing_axis"] == "y"
    assert trace["actual_slenderness"]["result"] == pytest.approx(100.0)
    assert trace["check"]["utilization"] == pytest.approx(100.0 / 120.0)
    assert trace["check"]["pass"] is True


def test_alpha_minimum_and_group4_increase_are_explicit():
    values = _values(group4=True)
    values["ambient_N_force"] = -60_000.0
    trace = build_limiting_slenderness_trace(values)

    assert trace["alpha"]["raw"] == pytest.approx(0.1)
    assert trace["alpha"]["result"] == pytest.approx(0.5)
    assert trace["alpha"]["minimum_applied"] is True
    # row 1a: 180 - 60*0.5 = 150; group 4 => 165.
    assert trace["limiting_slenderness"]["base"] == pytest.approx(150.0)
    assert trace["limiting_slenderness"]["group4_factor"] == pytest.approx(1.1)
    assert trace["limiting_slenderness"]["result"] == pytest.approx(165.0)
    assert trace["check"]["pass"] is True


def test_table32_trace_records_fail_without_softening_verdict():
    trace = build_limiting_slenderness_trace(_values(lambda_y=150.0))
    assert trace["limiting_slenderness"]["result"] == pytest.approx(120.0)
    assert trace["actual_slenderness"]["result"] == pytest.approx(150.0)
    assert trace["check"]["utilization"] == pytest.approx(1.25)
    assert trace["check"]["pass"] is False


def test_invalid_or_unclassified_table32_inputs_fail_closed():
    bad = _values()
    bad["sp16_mech7_table32_row"] = "unknown"
    with pytest.raises(FireUIError, match="valid Table-32 row id"):
        build_limiting_slenderness_trace(bad)

    bad = _values()
    bad.pop("sp16_mech7_group4_slenderness_increase")
    with pytest.raises(FireUIError, match="explicit group-4 classification"):
        build_limiting_slenderness_trace(bad)


def test_binder_wrapper_attaches_trace_and_preserves_authoritative_status():
    values = _values()
    expected = build_limiting_slenderness_trace(values)
    registry = ExecutionRegistry()

    def previous(_values, _node):
        return {
            "sp16_mech7_primary_evidence": {
                "schema": "sp16_mech7_primary_ambient_evidence_v075_zy_v1",
                "evidence": {
                    EVIDENCE_KEY: {
                        "status": "PASS",
                        "utilization": expected["check"]["utilization"],
                        "pass": True,
                        "evidence_source": "SP16-MECH7 Table 32 row 1a, canonical z/y",
                        "evidence_scope": ["SP16 10.4.1 Table 32"],
                    }
                },
            },
            "sp16_mech7_primary_binding_complete": True,
        }

    registry.register(BINDER_NODE_ID, previous)
    install_registry_remediation(registry)
    result = registry.get(BINDER_NODE_ID)(values, {"id": BINDER_NODE_ID})
    row = result["sp16_mech7_primary_evidence"]["evidence"][EVIDENCE_KEY]

    assert row["status"] == "PASS"
    assert row["pass"] is True
    assert row["utilization"] == pytest.approx(expected["check"]["utilization"])
    assert row["calculation_trace"]["schema"] == TRACE_SCHEMA
    assert row["calculation_trace_validated_against_binder"] is True


def test_binder_wrapper_fails_closed_on_utilization_mismatch():
    values = _values()
    registry = ExecutionRegistry()

    def previous(_values, _node):
        return {
            "sp16_mech7_primary_evidence": {
                "evidence": {
                    EVIDENCE_KEY: {
                        "status": "PASS",
                        "utilization": 0.123,
                        "pass": True,
                    }
                }
            }
        }

    registry.register(BINDER_NODE_ID, previous)
    install_registry_remediation(registry)
    with pytest.raises(FireUIError, match="does not reproduce binder utilization"):
        registry.get(BINDER_NODE_ID)(values, {"id": BINDER_NODE_ID})


def test_deferred_binder_row_stays_deferred_without_speculative_trace():
    registry = ExecutionRegistry()

    def previous(_values, _node):
        return {
            "sp16_mech7_primary_evidence": {
                "evidence": {
                    EVIDENCE_KEY: {
                        "status": "DEFERRED",
                        "utilization": None,
                        "pass": None,
                        "reason": "classification missing",
                    }
                }
            }
        }

    registry.register(BINDER_NODE_ID, previous)
    install_registry_remediation(registry)
    result = registry.get(BINDER_NODE_ID)({}, {"id": BINDER_NODE_ID})
    row = result["sp16_mech7_primary_evidence"]["evidence"][EVIDENCE_KEY]
    assert row["status"] == "DEFERRED"
    assert "calculation_trace" not in row
