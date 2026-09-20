import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows():
    with (ROOT / "audit_inventory/table_inventory.csv").open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def test_table_inventory_shape_and_unique_ids():
    rows = _rows()
    assert len(rows) == 88
    assert len({row["audit_id"] for row in rows}) == len(rows)


def test_tables_2_to_10_10a_d1_and_e1_are_implemented_as_data():
    rows = {row["audit_id"]: row for row in _rows()}
    implemented = {"SP16-TBL-1", "SP16-TBL-2", "SP16-TBL-3", "SP16-TBL-4", "SP16-TBL-5", "SP16-TBL-6", "SP16-TBL-7", "SP16-TBL-8", "SP16-TBL-9", "SP16-TBL-10", "SP16-TBL-Д-1", "SP16-TBL-10а", "SP16-TBL-Е-1", "SP16-TBL-Е-2", "SP16-TBL-11", "SP16-TBL-12", "SP16-TBL-13", "SP16-TBL-14", "SP16-TBL-15", "SP16-TBL-16", "SP16-TBL-17", "SP16-TBL-18", "SP16-TBL-19", "SP16-TBL-20", "SP16-TBL-21", "SP16-TBL-22", "SP16-TBL-23", "SP16-TBL-24", "SP16-TBL-25", "SP16-TBL-26", "SP16-TBL-27", "SP16-TBL-28", "SP16-TBL-29", "SP16-TBL-30", "SP16-TBL-31", "SP16-TBL-32", "SP16-TBL-33", "SP16-TBL-34", "SP16-TBL-35", "SP16-TBL-36", "SP16-TBL-37", "SP16-TBL-38", "SP16-TBL-39", "SP16-TBL-40", "SP16-TBL-41", "SP16-TBL-42", "SP16-TBL-43", "SP16-TBL-44", "SP16-TBL-45", "SP16-TBL-46", "SP16-TBL-47", "SP16-TBL-48", "SP16-TBL-Д-2", "SP16-TBL-Д-3", "SP16-TBL-Д-4", "SP16-TBL-Д-5", "SP16-TBL-Д-6", "SP16-TBL-Ж-1", "SP16-TBL-Ж-2", "SP16-TBL-Ж-3", "SP16-TBL-Ж-4", "SP16-TBL-Ж-5", "SP16-TBL-К-1"}
    assert all(rows[item]["implementation_status"] == "implemented_as_data" for item in implemented)


def test_table_data_files_exist_and_are_parseable():
    files = [
        "table_1_working_condition_factors.json",
        "table_2_resistance_formulas.json",
        "table_3_material_safety_factors.json",
        "table_4_weld_resistance_formulas.json",
        "table_5_bolt_resistance_factors.json",
        "table_6_single_angle_coefficients.json",
        "table_7_section_type_coefficients.json",
        "table_8_built_up_effective_slenderness.json",
        "table_9_wall_slenderness_limits.json",
        "table_10_flange_slenderness_limits.json",
        "annex_d_table_d1_stability_coefficients.json",
        "table_10a_constrained_torsion_coefficients.json",
        "annex_e_table_e1_plastic_coefficients.json",
        "annex_e_table_e2_base_plate_coefficients.json",
        "table_11_lateral_torsional_slenderness_limits.json",
        "table_12_web_buckling_c_cr.json",
        "table_13_compressed_flange_beta.json",
        "tables_14_to_19_bending_local_stability.json",
        "annex_zh_tables.json",
        "table_20_effective_moment_rules.json",
        "table_21_out_of_plane_coefficients.json",
        "table_22_combined_web_slenderness_limits.json",
        "table_23_combined_flange_slenderness_limits.json",
        "tables_24_to_33_effective_lengths.json",
        "annex_d_tables_d2_to_d6.json",
        "table_35_fatigue_resistance.json",
        "table_36_fatigue_asymmetry_factor.json",
        "annex_k_table_k1_fatigue_groups.json",
        "table_37_lamellar_tearing_risk_factors.json",
        "table_38_minimum_fillet_weld_legs.json",
        "table_39_fillet_weld_coefficients.json",
        "table_43_built_up_beam_flange_connections.json",
        "table_45_overhead_line_working_conditions.json",
        "table_46_support_deformation_limits.json",
        "table_47_antenna_structure_working_conditions.json",
        "table_48_riveted_connection_resistances.json",
    ]
    for name in files:
        data = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
        assert data.get("standard_reference") or data.get("standard")


def test_remaining_tables_are_not_silently_implemented():
    rows = _rows()
    excluded = next(row for row in rows if row["table_number"] == "Г.8")
    assert excluded["implementation_status"] == "no_code_explanatory"
    implemented = {row["audit_id"] for row in rows if row["implementation_status"] in {"implemented", "implemented_as_data", "implemented_as_validation_reference"}}
    remaining = [row for row in rows if row["audit_id"] not in implemented and row["table_number"] != "Г.8"]
    assert len(remaining) == 20
    assert {row["implementation_status"] for row in remaining} == {"external_reference_required"}
