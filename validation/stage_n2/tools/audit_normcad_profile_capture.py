#!/usr/bin/env python3
"""Build deterministic Stage N2 audit evidence for the static NormCAD profile capture."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

EXPECTED_MDB_SHA = "f7f967e5f22382eb0e20606be73189d2bc6db8f86588d66584fd49b5c4deb4e8"
EXPECTED_VB_SHA = "a6793575d4107569e5de507f2086275915293cb99df60d01a4388ac2e0d308bc"
EXPECTED_PROFILE_COUNT = 4069
EXPECTED_FAMILY_COUNT = 37
EXPECTED_IT_SENTINEL = 6.770929203650806e22


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_line(lines: list[str], needle: str) -> tuple[int, str]:
    for index, line in enumerate(lines, start=1):
        if needle in line:
            return index, line
    raise RuntimeError(f"Required static evidence not found: {needle}")


def audit(capture_path: Path, vb_path: Path, dsl_path: Path) -> dict[str, Any]:
    capture = json.loads(capture_path.read_text(encoding="utf-8"))
    rows = capture["rows"]
    families = capture["families"]

    ids = [int(row["id_data"]) for row in rows]
    duplicate_ids = sorted(item for item, count in Counter(ids).items() if count > 1)
    missing_ids = sorted(set(range(1, EXPECTED_PROFILE_COUNT + 1)) - set(ids))

    negative_fields: dict[str, list[dict[str, Any]]] = {}
    numeric_fields = [
        "h_mm", "b_mm", "tw_mm", "tf_mm", "r_mm", "A_mm2", "mass_kg_m_db",
        "Ix_mm4", "Iy_mm4", "Wx1_mm3", "Wx2_mm3", "Wy1_mm3", "Wy2_mm3",
        "Sx_mm3", "Sy_mm3", "It_mm4_db",
    ]
    for field in numeric_fields:
        hits = [
            {"id_data": row["id_data"], "family_id": row["family_id"], "designation": row["designation"], "value": row[field]}
            for row in rows
            if float(row[field]) < 0.0
        ]
        if hits:
            negative_fields[field] = hits

    mass_mismatches: list[dict[str, Any]] = []
    for row in rows:
        area = float(row["A_mm2"])
        mass = float(row["mass_kg_m_db"])
        if area <= 0.0:
            continue
        expected = area * 0.00785
        abs_error = abs(mass - expected)
        rel_error = abs_error / expected if expected else math.inf
        if abs_error > 0.15 and rel_error > 0.02:
            mass_mismatches.append(
                {
                    "id_data": row["id_data"],
                    "family_id": row["family_id"],
                    "designation": row["designation"],
                    "A_mm2": area,
                    "mass_kg_m_db": mass,
                    "mass_kg_m_from_A_rho7850": expected,
                    "absolute_error_kg_m": abs_error,
                    "relative_error": rel_error,
                }
            )
    mass_mismatches.sort(key=lambda item: item["relative_error"], reverse=True)

    huge_it_rows = [
        {"id_data": row["id_data"], "family_id": row["family_id"], "designation": row["designation"], "It_mm4_db": row["It_mm4_db"]}
        for row in rows
        if abs(float(row["It_mm4_db"])) > 1.0e12
    ]

    profile_15k4 = [row for row in rows if int(row["family_id"]) == 35 and row["designation"] == "15К4"]
    if len(profile_15k4) != 1:
        raise RuntimeError(f"Expected exactly one family 35 / 15К4 row, got {len(profile_15k4)}")
    p15 = profile_15k4[0]

    vb_lines = vb_path.read_text(encoding="cp1251", errors="replace").splitlines()
    vb_line_number, vb_jt_line = _find_line(vb_lines, "J__tb = (1 / 3) * t ^ 3 * (h - 2 * t__f)")

    dsl_lines = dsl_path.read_text(encoding="utf-8", errors="replace").splitlines()
    dsl_sum_line_no, dsl_sum_line = _find_line(dsl_lines, "gr_S_b__i_t__i_up_3")
    dsl_adjusted_line_no, dsl_adjusted_line = _find_line(dsl_lines, "J__t_џ= (k/3)*gr_S_b__i_t__i_up_3")
    dsl_use_line_no, dsl_use_line = _find_line(dsl_lines, "gr_mџ= 8*gr_w+0,156*J__t*gr_l__y^2")

    # Nominal 15K4 dimensions in the NormCAD row.  The historical DB stores the
    # unadjusted plate-sum / 3 value.  Current SP16 Annex D applies k=1.29 for a
    # doubly symmetric I-section in its D.1/D.2 computational route.
    h = float(p15["h_mm"])
    b = float(p15["b_mm"])
    tw = float(p15["tw_mm"])
    tf = float(p15["tf_mm"])
    sum_bt3 = (h - 2.0 * tf) * tw**3 + 2.0 * b * tf**3
    it_base = sum_bt3 / 3.0
    it_current_sp16_annex_d = 1.29 * it_base

    family_captions_nontrivial = all(len(str(item.get("caption", "")).strip()) >= 5 for item in families)
    family_ids = sorted(int(item["family_id"]) for item in families)

    checks = {
        "capture_mdb_source_hash_matches": capture.get("source_sha256") == EXPECTED_MDB_SHA,
        "profile_count_is_4069": len(rows) == EXPECTED_PROFILE_COUNT == int(capture.get("profile_row_count", -1)),
        "family_count_is_37": len(families) == EXPECTED_FAMILY_COUNT == int(capture.get("family_count", -1)),
        "profile_ids_contiguous_1_to_4069": ids == list(range(1, EXPECTED_PROFILE_COUNT + 1)),
        "no_duplicate_profile_ids": not duplicate_ids,
        "no_missing_profile_ids": not missing_ids,
        "family_captions_are_nontrivial": family_captions_nontrivial,
        "vb_source_hash_matches": _sha256(vb_path) == EXPECTED_VB_SHA,
        "normcad_15k4_base_it_matches_db_with_rounding": abs(float(p15["It_mm4_db"]) - it_base) < 1.0,
        "normcad_15k4_annex_d_current_sp_differs_materially": abs(it_current_sp16_annex_d - float(p15["It_mm4_db"])) > 1.0e5,
        "historical_catalog_contains_objective_anomalies": bool(negative_fields) and bool(mass_mismatches) and bool(huge_it_rows),
        "static_dsl_computes_adjusted_it_but_d1_path_references_original_it": "J__t_" in dsl_adjusted_line and "J__t*" in dsl_use_line,
    }

    return {
        "schema_version": "1.0.0",
        "stage": "N2",
        "audit_id": "N2_NORMCAD_PROFILE_CAPTURE_STATIC_AUDIT",
        "verdict": "PASS_HISTORICAL_CAPTURE_AUDITED_NOT_PRODUCTION_ELIGIBLE" if all(checks.values()) else "FAIL",
        "source_role": "HISTORICAL_SECONDARY_ORACLE_NOT_NORMATIVE",
        "checks": checks,
        "capture_summary": {
            "profile_rows": len(rows),
            "family_rows": len(families),
            "family_ids": family_ids,
            "duplicate_ids": duplicate_ids,
            "missing_ids": missing_ids,
        },
        "known_profile_15k4": {
            "family_id": p15["family_id"],
            "designation": p15["designation"],
            "h_mm": p15["h_mm"],
            "b_mm": p15["b_mm"],
            "tw_mm": p15["tw_mm"],
            "tf_mm": p15["tf_mm"],
            "r_mm": p15["r_mm"],
            "A_mm2": p15["A_mm2"],
            "Ix_mm4": p15["Ix_mm4"],
            "Iy_mm4": p15["Iy_mm4"],
            "Wx1_mm3": p15["Wx1_mm3"],
            "Wx2_mm3": p15["Wx2_mm3"],
            "Wy1_mm3": p15["Wy1_mm3"],
            "Wy2_mm3": p15["Wy2_mm3"],
            "Sx_mm3": p15["Sx_mm3"],
            "Sy_mm3": p15["Sy_mm3"],
            "It_mm4_db": p15["It_mm4_db"],
            "mass_kg_m_db": p15["mass_kg_m_db"],
            "mass_kg_m_from_A_rho7850": float(p15["A_mm2"]) * 0.00785,
            "plate_sum_b_t3_mm4": sum_bt3,
            "unadjusted_plate_sum_over_3_mm4": it_base,
            "current_sp16_annex_d_k": 1.29,
            "current_sp16_annex_d_It_mm4": it_current_sp16_annex_d,
        },
        "anomaly_summary": {
            "negative_field_counts": {field: len(items) for field, items in negative_fields.items()},
            "negative_field_rows": negative_fields,
            "mass_area_mismatch_count_gt_2pct_and_0_15kg_m": len(mass_mismatches),
            "mass_area_mismatch_count_gt_5pct_and_0_15kg_m": sum(item["relative_error"] > 0.05 for item in mass_mismatches),
            "mass_area_mismatch_count_gt_10pct_and_0_15kg_m": sum(item["relative_error"] > 0.10 for item in mass_mismatches),
            "largest_mass_area_mismatches": mass_mismatches[:30],
            "huge_It_gt_1e12_count": len(huge_it_rows),
            "huge_It_by_family": dict(sorted(Counter(str(item["family_id"]) for item in huge_it_rows).items(), key=lambda kv: int(kv[0]))),
            "huge_It_example_value": EXPECTED_IT_SENTINEL,
            "huge_It_examples": huge_it_rows[:30],
        },
        "static_algorithm_evidence": {
            "vb6_source": {
                "filename": vb_path.name,
                "sha256": _sha256(vb_path),
                "symmetric_i_jt_line_number": vb_line_number,
                "semantic_summary": "The historical VB6 symmetric I-section routine stores the unadjusted thin-wall plate sum divided by 3 as Jt.",
                "expression_normalized": "Jt=(1/3)*(tw^3*(h-2*tf)+2*tf^3*b)",
            },
            "sp16_normcad_dsl": {
                "filename": dsl_path.name,
                "sha256": _sha256(dsl_path),
                "sum_line_number": dsl_sum_line_no,
                "adjusted_line_number": dsl_adjusted_line_no,
                "use_line_number": dsl_use_line_no,
                "semantic_summary": "The static DSL derives an adjusted Jt_ using k, but the inspected D.1/D.2 gr_m expression references the original Jt variable.",
                "normalized_sequence": [
                    "sum_b_t3=3*Jt",
                    "Jt_adjusted=(k/3)*sum_b_t3",
                    "gr_m=8*omega+0.156*Jt*lambda_y^2/(A*h^2)",
                ],
            },
        },
        "limitations": [
            "The NormCAD executable was not run for this static forensic audit.",
            "Historical NormCAD catalogue rows are not a substitute for current/effective product-standard source tables.",
            "The current СП16 source defines/uses section properties and provides the Annex-D It expression, but it does not reproduce every current profile catalogue table.",
            "Production profile-catalog promotion remains blocked until the intended current/effective product-standard tables are source-validated.",
        ],
    }


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit("usage: audit_normcad_profile_capture.py CAPTURE_JSON VB6_BAS NORMCAD_DSL OUTPUT_JSON")
    result = audit(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
    output = Path(sys.argv[4])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(result["verdict"])
    print(json.dumps(result["capture_summary"], ensure_ascii=False))
    print(json.dumps(result["anomaly_summary"], ensure_ascii=False)[:1200])


if __name__ == "__main__":
    main()
