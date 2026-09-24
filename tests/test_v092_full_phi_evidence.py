from __future__ import annotations

import math

import pytest

from standard_core.axial_members import central_compression_stability_coefficient
from standard_core.fire_ui0 import ExecutionRegistry, FireUIError
from standard_core.sp16_mech7_v076_graph_overlay import STATE_NODE_ID
from standard_core.sp16_mech7_v092_effective_length import EVIDENCE_QID
from standard_core.sp16_mech7_v092_phi_evidence import (
    PHI_TRACE_SCHEMA,
    build_phi_evidence,
    install_registry_remediation,
)


def test_full_phi_evidence_discloses_table7_delta_and_eq8_for_curve_b():
    lambda_bar = 2.0
    phi = central_compression_stability_coefficient(lambda_bar, "b")
    evidence = build_phi_evidence(lambda_bar, "b", phi)

    assert evidence["schema"] == PHI_TRACE_SCHEMA
    assert evidence["branch"] == "eq8_eq9_with_table7"
    assert evidence["alpha"] == pytest.approx(0.04)
    assert evidence["beta"] == pytest.approx(0.09)
    assert evidence["delta"] == pytest.approx(15.2518)
    assert evidence["eq8_radicand"] > 0.0
    assert evidence["phi_eq8"] == pytest.approx(phi)
    assert evidence["cap_applied"] is False
    assert evidence["cap_candidate"] is None
    assert evidence["final_phi"] == pytest.approx(phi)
    assert evidence["validated_against_runtime"] is True


def test_low_slenderness_direct_phi_rule_does_not_fabricate_delta():
    lambda_bar = 0.5
    phi = central_compression_stability_coefficient(lambda_bar, "a")
    evidence = build_phi_evidence(lambda_bar, "a", phi)

    assert phi == pytest.approx(1.0)
    assert evidence["branch"] == "low_slenderness_direct_phi_1"
    assert evidence["alpha"] == pytest.approx(0.03)
    assert evidence["beta"] == pytest.approx(0.06)
    assert evidence["delta"] is None
    assert evidence["phi_eq8"] is None
    assert evidence["cap_applied"] is False
    assert evidence["final_phi"] == pytest.approx(1.0)


def test_high_slenderness_cap_evidence_matches_authoritative_runtime_phi():
    lambda_bar = 5.0
    phi = central_compression_stability_coefficient(lambda_bar, "b")
    evidence = build_phi_evidence(lambda_bar, "b", phi)

    assert evidence["cap_applied"] is True
    assert evidence["cap_threshold_lambda_bar"] == pytest.approx(4.4)
    assert evidence["cap_candidate"] == pytest.approx(7.6 / 25.0)
    assert evidence["final_phi"] == pytest.approx(phi)
    assert evidence["final_phi"] == pytest.approx(
        min(evidence["phi_eq8"], evidence["cap_candidate"])
    )


def test_phi_evidence_fails_closed_when_supplied_runtime_phi_does_not_match_chain():
    with pytest.raises(FireUIError, match="does not reproduce the qualified runtime result"):
        build_phi_evidence(2.0, "b", 0.123456)


def test_registry_wrapper_enriches_existing_zy_trace_without_replacing_phi_outputs():
    registry = ExecutionRegistry()
    phi_z = central_compression_stability_coefficient(2.0, "b")
    phi_y = central_compression_stability_coefficient(3.0, "c")

    def previous(values, node):
        return {
            "phi_z_sp16": phi_z,
            "phi_y_sp16": phi_y,
            EVIDENCE_QID: {
                "schema": "sp16_v092_effective_length_zy_trace_v1",
                "axis_convention": {"z": "strong principal axis", "y": "weak principal axis"},
                "z": {"lambda_bar": 2.0, "curve": "b", "phi": phi_z},
                "y": {"lambda_bar": 3.0, "curve": "c", "phi": phi_y},
                "governing_axis_by_phi": "y",
            },
        }

    registry.register(STATE_NODE_ID, previous)
    install_registry_remediation(registry)
    executor = registry.get(STATE_NODE_ID)
    assert getattr(executor, "_sp16_v092_full_phi_evidence", False) is True

    outputs = executor({}, {"id": STATE_NODE_ID})
    trace = outputs[EVIDENCE_QID]

    assert outputs["phi_z_sp16"] == pytest.approx(phi_z)
    assert outputs["phi_y_sp16"] == pytest.approx(phi_y)
    assert trace["z"]["phi"] == pytest.approx(phi_z)
    assert trace["y"]["phi"] == pytest.approx(phi_y)
    assert trace["z"]["phi_evidence"]["final_phi"] == pytest.approx(phi_z)
    assert trace["y"]["phi_evidence"]["final_phi"] == pytest.approx(phi_y)
    assert trace["full_phi_evidence_contract"] == PHI_TRACE_SCHEMA


def test_evidence_formula_uses_rationalized_eq8_equivalent_without_numeric_drift():
    lambda_bar = 2.75
    phi = central_compression_stability_coefficient(lambda_bar, "c")
    evidence = build_phi_evidence(lambda_bar, "c", phi)

    delta = evidence["delta"]
    radical = math.sqrt(evidence["eq8_radicand"])
    rationalized = 19.74 / (delta + radical)
    assert evidence["phi_eq8"] == pytest.approx(rationalized)
    assert evidence["final_phi"] == pytest.approx(phi)
