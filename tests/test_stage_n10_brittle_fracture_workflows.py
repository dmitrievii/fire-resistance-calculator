from __future__ import annotations

import json
from pathlib import Path

import pytest

from standard_core import brittle_fracture_and_welded_connections as s13
from standard_core import brittle_fracture_workflows as n10w
from standard_core.runner import _prepare_case_for_validation

ROOT = Path(__file__).resolve().parents[1]


def _case(**updates):
    route = json.loads((ROOT / "examples" / "brittle_fracture_guided_example.json").read_text(encoding="utf-8"))["route"]
    route.update(updates)
    return {"case_id":"N10-TEST","standard":"СП 16.13330.2017","action":"brittle_fracture_guided","route":route}


def test_n10_clause13_1_current_factor_register_is_exactly_four_printed_groups():
    factors=s13.brittle_fracture_factor_register_clause_13_1()
    assert list(factors)==[
        "low_temperature","dynamic_or_impact_action","high_local_stress","stress_concentration"
    ]
    assert "material_toughness" not in factors
    assert "residual_welding_stress" not in factors


def test_n10_full_example_computes_current_eq174_and_z25_pass():
    r=n10w.brittle_fracture_guided_workflow(_case())
    assert r["status"]=="COMPLETE" and r["pass"]
    lam=r["lamellar_tearing"]
    assert lam["equation_174_base_risk_percent"]==pytest.approx(21.4)
    assert lam["required_z_quality_group"]=="Z25"
    assert lam["selected_z_quality_group"]=="Z25"
    assert lam["risk_check"]["utilization"]==pytest.approx(21.4/25.0)


def test_n10_13_2_ndt_threshold_is_strictly_above_0_4_ry():
    at=n10w.brittle_fracture_guided_workflow(_case(weld_zone_tensile_stress_n_mm2=96.0))
    assert at["general_prevention"]["clause_13_2_checks"]["enhanced_ndt_above_0_4_ry"]["applicable"] is False
    case=_case(weld_zone_tensile_stress_n_mm2=96.0001)
    del case["route"]["enhanced_ndt_for_welds_above_0_4_ry_confirmed"]
    with pytest.raises(ValueError,match="enhanced_ndt"):
        n10w.brittle_fracture_guided_workflow(case)


def test_n10_13_2_cover_plate_flank_weld_25_mm_boundary():
    good=n10w.brittle_fracture_guided_workflow(_case(flank_weld_termination_distance_each_side_mm=25.0))
    assert good["general_prevention"]["pass"]
    bad=n10w.brittle_fracture_guided_workflow(_case(flank_weld_termination_distance_each_side_mm=24.999))
    assert not bad["general_prevention"]["pass"] and not bad["pass"]


def test_n10_applicable_conditional_13_2_confirmations_cannot_be_omitted():
    case=_case(guillotine_cutting_or_punched_holes=True)
    with pytest.raises(ValueError,match="minimum_section_thickness"):
        n10w.brittle_fracture_guided_workflow(case)
    case=_case(secondary_gusset_to_tension_member=True)
    with pytest.raises(ValueError,match="bolted_secondary"):
        n10w.brittle_fracture_guided_workflow(case)


def test_n10_positive_conservative_13_3_screen_cannot_be_suppressed():
    with pytest.raises(ValueError,match="cannot be false"):
        n10w.brittle_fracture_guided_workflow(_case(lamellar_tearing_assessment_required=False))


def test_n10_confirmed_nonapplicable_lamellar_route_stops_before_table37():
    r=n10w.brittle_fracture_guided_workflow(_case(
        steel_grade_number=235.0,plate_thickness_mm=20.0,joint_type="tee",through_thickness_tension=False,
        lamellar_tearing_assessment_required=False,welded_structure=False,
    ))
    assert r["status"]=="COMPLETE"
    assert r["lamellar_tearing"]["required"] is False
    assert r["governing_utilization"] is None


def test_n10_missing_clause13_4_test_evidence_is_fail_closed():
    r=n10w.brittle_fracture_guided_workflow(_case(through_thickness_test_evidence_available=False))
    assert r["status"]=="INCOMPLETE_FAIL_CLOSED"
    assert r["governing_utilization"] is None


def test_n10_missing_z_certificate_is_fail_closed():
    r=n10w.brittle_fracture_guided_workflow(_case(selected_z_quality_certificate_confirmed=False))
    assert r["status"]=="INCOMPLETE_FAIL_CLOSED"


def test_n10_selected_z_group_must_meet_minimum_even_when_numeric_risk_passes():
    r=n10w.brittle_fracture_guided_workflow(_case(
        construction_group=1,consequence_class="KS-3",selected_z_quality_group="Z25",
        connection_form_case="no_z_direction_stress",risk_weld_leg_mm=0.0,
        restraint_level="low_free_shrinkage",pass_count="multiple",weld_sequence="alternating_sides",preheat="with_preheat"
    ))
    assert r["lamellar_tearing"]["risk_check"]["pass"] is True
    assert r["lamellar_tearing"]["required_z_quality_group"]=="Z35"
    assert r["lamellar_tearing"]["selected_quality_meets_minimum_group"] is False
    assert r["pass"] is False


def test_n10_flange_or_normal_force_route_requires_z35():
    r=n10w.brittle_fracture_guided_workflow(_case(
        flange_connection_15_9_10_or_force_normal_to_plate=True,selected_z_quality_group="Z35"
    ))
    assert r["lamellar_tearing"]["required_z_quality_group"]=="Z35"
    assert r["pass"]


def test_n10_table37_dynamic_and_static_modifiers_are_literal():
    dyn=n10w.brittle_fracture_guided_workflow(_case(through_thickness_action="dynamic_or_vibratory"))
    sta=n10w.brittle_fracture_guided_workflow(_case(through_thickness_action="static_compression"))
    assert dyn["lamellar_tearing"]["adjusted_risk_percent"]==pytest.approx(21.4*1.1)
    assert sta["lamellar_tearing"]["adjusted_risk_percent"]==pytest.approx(21.4*0.5)


def test_n10_engineering_review_must_be_explicit():
    with pytest.raises(ValueError,match="engineering_review_confirmed"):
        n10w.brittle_fracture_guided_workflow(_case(clause_13_3_engineering_review_confirmed=False))


def test_n10_schema_accepts_example_and_rejects_hidden_default():
    raw=json.loads((ROOT/"examples"/"brittle_fracture_guided_example.json").read_text(encoding="utf-8"))
    case,schema,_=_prepare_case_for_validation(raw,ROOT)
    assert schema["$id"]=="brittle_fracture_guided_case.schema.json"
    assert case["action"]=="brittle_fracture_guided"
    raw["route"]["hidden_default"]=1
    with pytest.raises(ValueError,match="Unexpected property"):
        _prepare_case_for_validation(raw,ROOT)
