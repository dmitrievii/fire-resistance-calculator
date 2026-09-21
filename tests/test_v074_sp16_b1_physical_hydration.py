from __future__ import annotations

from types import SimpleNamespace

import pytest

from standard_core.fire_ui0 import ExecutionRegistry
from standard_core.sp16_mech7_primary_workflow import bind_primary_ambient_evidence
from standard_core.sp16_mech7_v074_physical_remediation import (
    install_registry_remediation,
    normalize_mech7_inputs,
)
from streamlit_guided_ux_v074 import _remediate_application


_BINDER = "SP16_C_MECH7_PRIMARY_EVIDENCE_BINDER"


def _census(active=(), contextual=()):
    return {
        "schema": "sp16_mech2_applicability_census_v1",
        "active_checks": [
            {
                "id": cid,
                "family": "test",
                "label": cid,
                "applicability": "applicable",
                "runtime_status": "inherited_runtime",
                "normative_scope": [],
            }
            for cid in active
        ],
        "context_driven_checks": [
            {
                "id": cid,
                "family": "test",
                "label": cid,
                "applicability": "conditional_context",
                "trigger": "test",
                "runtime_status": "context_resolution_required",
                "normative_scope": [],
            }
            for cid in contextual
        ],
    }


def test_v074_hydrates_source_backed_sp16_n1_prerequisites():
    out = normalize_mech7_inputs(
        {
            "fy_norm": 255.0,
            "fu_norm": 380.0,
            "material_safety_category": "statistical_control",
        }
    )

    assert out["E_norm"] == pytest.approx(206000.0)
    assert out["gamma_u"] == pytest.approx(1.3)
    assert out["Ry_formula"] == pytest.approx(255.0 / 1.025)

    trace = {row["quantity_id"]: row for row in out["_sp16_v074_hydration_trace"]}
    assert set(trace) == {"E_norm", "gamma_u"}
    assert trace["E_norm"]["source_quantity"] == "E_MPa"
    assert trace["E_norm"]["source_table"] == "Б.1"
    assert trace["E_norm"]["source_sha256"]
    assert trace["gamma_u"]["source_clause"] == "4.3.2"
    assert trace["gamma_u"]["source_sha256"]


def test_v074_never_overwrites_explicit_prerequisite_producers():
    explicit = normalize_mech7_inputs({"E_norm": 199000.0, "gamma_u": 1.25})
    assert explicit["E_norm"] == pytest.approx(199000.0)
    assert explicit["gamma_u"] == pytest.approx(1.25)
    assert "_sp16_v074_hydration_trace" not in explicit

    malformed = normalize_mech7_inputs(
        {"E_norm": "upstream-invalid", "gamma_u": "upstream-invalid"}
    )
    assert malformed["E_norm"] == "upstream-invalid"
    assert malformed["gamma_u"] == "upstream-invalid"
    assert "_sp16_v074_hydration_trace" not in malformed


def test_v074_user_step16_central_compression_closes_source_backed_prerequisite_gaps():
    # Regression of the production screenshot: this is the same MECH7 path as
    # the v0.72 regression, deliberately WITHOUT manually supplied E_norm or
    # gamma_u. Both must come from qualified SP16 datasets.
    values = {
        "sp16_applicability_census": _census(
            ["section_compression", "member_compression_stability", "effective_length_slenderness"],
            ["local_stability_web", "local_stability_flange"],
        ),
        "ambient_N_force": -100e3,
        "ambient_M_x": 0.0,
        "ambient_M_y": 0.0,
        "ambient_B_bimoment": 0.0,
        "A_net": 2000.0,
        "A_gross": 2000.0,
        "fy_norm": 255.0,
        "fu_norm": 380.0,
        "material_safety_category": "statistical_control",
        "gamma_c_compression": 1.0,
        "phi_x_sp16": 0.8,
        "phi_y_sp16": 0.7,
        "sp16_l_eff_x": 2500.0,
        "sp16_i_x": 50.0,
        "sp16_l_eff_y": 3000.0,
        "sp16_i_y": 50.0,
        "sp16_mech7_table32_row": "3",
        "sp16_mech7_group4_slenderness_increase": False,
        "section_geometry_2d_normalized": {
            "source": "profile_catalog",
            "shape_group": "I_ROLLED_DSYMM",
            "dimensions": {"h_mm": 300.0, "b_mm": 150.0, "tw_mm": 8.0, "tf_mm": 12.0},
        },
        "lambda_bar_x": 1.0,
        "lambda_bar_y": 1.2,
        "sp16_mech7_table9_group": "group_1_i_section",
        "sp16_mech7_table10_group": "group_1",
        "sp16_mech7_flange_edge_stiffened": False,
    }

    normalized = normalize_mech7_inputs(values)
    assert "E_norm" not in values
    assert "gamma_u" not in values
    assert normalized["E_norm"] == pytest.approx(206000.0)
    assert normalized["gamma_u"] == pytest.approx(1.3)

    evidence = bind_primary_ambient_evidence(normalized)["sp16_mech7_primary_evidence"]["evidence"]
    for cid in (
        "section_compression",
        "member_compression_stability",
        "effective_length_slenderness",
        "local_stability_web",
        "local_stability_flange",
    ):
        assert evidence[cid]["status"] in {"PASS", "FAIL"}, (cid, evidence[cid])
        reason = str(evidence[cid].get("reason") or "")
        assert "requires E_norm" not in reason
        assert "requires gamma_u" not in reason
        assert "requires Ry_formula" not in reason


def test_v074_registry_wrapper_is_strictly_idempotent_across_streamlit_reruns():
    seen = []

    def original(values, node):
        seen.append(dict(values))
        return {
            "sp16_mech7_primary_evidence": {"evidence": {}},
            "sp16_mech7_primary_binding_complete": True,
        }

    registry = ExecutionRegistry({_BINDER: original})
    install_registry_remediation(registry)
    first = registry.executors[_BINDER]
    install_registry_remediation(registry)
    second = registry.executors[_BINDER]
    install_registry_remediation(registry)
    third = registry.executors[_BINDER]

    assert first is second is third
    assert getattr(first, "_sp16_v072_remediated", False) is True
    assert getattr(first, "_sp16_v074_remediated", False) is True

    result = first({"fy_norm": 255.0, "material_safety_category": "statistical_control"}, {})
    assert seen[-1]["E_norm"] == pytest.approx(206000.0)
    assert seen[-1]["gamma_u"] == pytest.approx(1.3)
    trace = {
        row["quantity_id"]: row
        for row in result["sp16_mech7_primary_evidence"]["v074_prerequisite_hydration"]
    }
    assert trace["E_norm"]["source_table"] == "Б.1"
    assert trace["gamma_u"]["source_clause"] == "4.3.2"


def test_v074_retained_application_upgrades_service_and_detached_session_once():
    def original(values, node):
        return {
            "sp16_mech7_primary_evidence": {"evidence": {}},
            "sp16_mech7_primary_binding_complete": True,
        }

    service_registry = ExecutionRegistry({_BINDER: original})
    detached_registry = ExecutionRegistry({_BINDER: original})
    app = SimpleNamespace(
        service=SimpleNamespace(
            registry=service_registry,
            sessions={"fire-000001": SimpleNamespace(registry=detached_registry)},
        )
    )

    _remediate_application(app)
    service_first = service_registry.executors[_BINDER]
    detached_first = detached_registry.executors[_BINDER]
    _remediate_application(app)

    assert service_registry.executors[_BINDER] is service_first
    assert detached_registry.executors[_BINDER] is detached_first
    assert getattr(service_first, "_sp16_v074_remediated", False) is True
    assert getattr(detached_first, "_sp16_v074_remediated", False) is True
