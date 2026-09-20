from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SOURCE_CAPTURE = ROOT / "validation/stage_n1/current_sp16_source_capture_stage_n1.json"
OUTPUT = ROOT / "validation/stage_n1/boundary_probe_matrix_stage_n1.json"

TABLE_ROUTES = {
    "V3": ["plate_sheet_strip", "bar_rolled", "tube"],
    "V4": ["parallel_flange_i"],
    "V5": ["shaped_rolled"],
}


def contains(interval: dict[str, Any], thickness: float) -> bool:
    lo = interval.get("min_mm")
    hi = interval.get("max_mm")
    if lo is not None:
        lo = float(lo)
        if thickness < lo or (thickness == lo and not bool(interval["min_inclusive"])):
            return False
    if hi is not None:
        hi = float(hi)
        if thickness > hi or (thickness == hi and not bool(interval["max_inclusive"])):
            return False
    return True


def source_expected(rows: list[dict[str, Any]], grade: str, t: float) -> dict[str, Any] | None:
    matches = [r for r in rows if grade in r["grades"] and contains(r["thickness_interval"], t)]
    if len(matches) > 1:
        raise RuntimeError(f"Source capture overlap for {grade=} {t=}: {len(matches)} rows")
    if not matches:
        return None
    r = matches[0]
    return {
        "source_row_index": int(r["source_row_index"]),
        "Ryn_MPa": r["Ryn_MPa"],
        "Run_MPa": r["Run_MPa"],
        "Ry_MPa": r["Ry_MPa"],
        "Ru_MPa": r["Ru_MPa"],
    }


def representative(interval: dict[str, Any]) -> float:
    lo = interval.get("min_mm")
    hi = interval.get("max_mm")
    if lo is None and hi is None:
        return 1.0
    if lo is None:
        return max(1.0, float(hi) / 2.0)
    if hi is None:
        return float(lo) + max(1.0, abs(float(lo)) * 0.01)
    lo_f, hi_f = float(lo), float(hi)
    return (lo_f + hi_f) / 2.0


def unique_preserving(values: list[tuple[str, float]]) -> list[tuple[str, float]]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, float]] = []
    for kind, value in values:
        key = (kind, value.hex())
        if key not in seen:
            seen.add(key)
            out.append((kind, value))
    return out


def main() -> None:
    source = json.loads(SOURCE_CAPTURE.read_text(encoding="utf-8"))
    probes: list[dict[str, Any]] = []

    for table_key, product_forms in TABLE_ROUTES.items():
        rows: list[dict[str, Any]] = source[table_key]["rows"]
        grades = sorted({g for r in rows for g in r["grades"]})
        for product_form in product_forms:
            for grade in grades:
                grade_rows = [r for r in rows if grade in r["grades"]]
                candidates: list[tuple[str, float]] = []
                for r in grade_rows:
                    candidates.append(("INTERIOR", representative(r["thickness_interval"])))
                    iv = r["thickness_interval"]
                    for side in ("min_mm", "max_mm"):
                        b = iv.get(side)
                        if b is None:
                            continue
                        b = float(b)
                        if b <= 0.0:
                            continue
                        candidates.append(("BOUNDARY_EXACT", b))
                        below = math.nextafter(b, -math.inf)
                        above = math.nextafter(b, math.inf)
                        if below > 0.0:
                            candidates.append(("BOUNDARY_BELOW_NEXTAFTER", below))
                        candidates.append(("BOUNDARY_ABOVE_NEXTAFTER", above))

                # Add a normal low positive probe for source rows with open lower end (e.g. V.4 <=10).
                if any(r["thickness_interval"].get("min_mm") is None for r in grade_rows):
                    candidates.append(("LOW_POSITIVE", 1.0))

                for probe_kind, t in unique_preserving(candidates):
                    expected = source_expected(rows, grade, t)
                    probes.append({
                        "table": source[table_key]["table_number"],
                        "table_key": table_key,
                        "product_form": product_form,
                        "steel_grade": grade,
                        "probe_kind": probe_kind,
                        "thickness_mm": t,
                        "thickness_hex": t.hex(),
                        "expected": expected if expected is not None else {"error": "NO_EXACT_SOURCE_ROW"},
                    })

    by_table = Counter(p["table"] for p in probes)
    by_kind = Counter(p["probe_kind"] for p in probes)
    expected_resolved = sum("error" not in p["expected"] for p in probes)
    expected_fail_closed = len(probes) - expected_resolved

    out = {
        "schema_version": "1.0.0",
        "stage": "N1 — Material / Strength",
        "authority": "Current locked СП16 source capture only",
        "normative_source_sha256": source["normative_source"]["source_sha256"],
        "probe_policy": {
            "interior": "one source-row interior point per expanded grade row and supported product route",
            "boundary": "every finite source interval endpoint tested at exact float endpoint and math.nextafter immediately below/above",
            "expected_result": "computed solely from current-SP source-capture intervals; package resolver is not used to generate expected values",
            "fail_closed": "a probe not owned by any exact current-SP row must be rejected by production resolver",
        },
        "summary": {
            "probe_count": len(probes),
            "expected_resolved": expected_resolved,
            "expected_fail_closed": expected_fail_closed,
            "by_table": dict(sorted(by_table.items())),
            "by_probe_kind": dict(sorted(by_kind.items())),
        },
        "probes": probes,
    }
    OUTPUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
