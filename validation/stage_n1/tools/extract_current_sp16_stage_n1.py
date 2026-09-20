from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

SOURCE_SHA256 = "302c2c45dacc3947a07dbf8eb676e99673899d60ca053ec137207dbca41ed873"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm_text(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def find_last_text(soup: BeautifulSoup, pattern: str):
    rx = re.compile(pattern)
    hits = [n for n in soup.find_all(string=True) if rx.search(norm_text(str(n)))]
    if not hits:
        raise RuntimeError(f"marker not found: {pattern}")
    return hits[-1]


def find_exact_text(soup: BeautifulSoup, text: str):
    hits = [n for n in soup.find_all(string=True) if norm_text(str(n)) == text]
    if len(hits) != 1:
        raise RuntimeError(f"expected one exact marker {text!r}, got {len(hits)}")
    return hits[0]


def split_grades(raw: str) -> list[str]:
    # Current source uses semicolon-separated aliases in V.3/V.4.
    return [x.strip() for x in raw.split(";") if x.strip()]


def fnum(s: str) -> float:
    return float(s.replace(",", "."))


def parse_interval(raw: str, previous_max: float | None = None) -> dict[str, Any]:
    s = norm_text(raw).replace(",", ".")
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s)]
    low = high = None
    low_inc = high_inc = False

    if s.startswith("≤"):
        if len(nums) != 1:
            raise ValueError(raw)
        high = nums[0]
        high_inc = True
    elif s.startswith(">"):
        if len(nums) != 1:
            raise ValueError(raw)
        low = nums[0]
        low_inc = False
    elif s.lower().startswith("св."):
        if len(nums) != 2:
            raise ValueError(raw)
        low, high = nums
        low_inc, high_inc = False, True
    elif s.lower().startswith("от"):
        if len(nums) != 2:
            raise ValueError(raw)
        low, high = nums
        low_inc, high_inc = True, ("включ" in s.lower())
    elif s.startswith('"'):
        if len(nums) != 2:
            raise ValueError(raw)
        low, high = nums
        # Ditto-mark rows continue a band. If the previous row ends at the same
        # numeric boundary, the previous explicit "включ." owns that exact
        # boundary; otherwise (e.g. 3.9 -> 4.0) the new lower value is included.
        low_inc = not (previous_max is not None and abs(previous_max - low) < 1e-12)
        high_inc = True
    else:
        raise ValueError(f"unhandled interval label: {raw!r}")

    def norm_n(v):
        if v is None:
            return None
        return int(v) if float(v).is_integer() else v

    return {
        "min_mm": norm_n(low),
        "max_mm": norm_n(high),
        "min_inclusive": low_inc,
        "max_inclusive": high_inc,
        "source_label": raw,
    }


def parse_strength_table(soup: BeautifulSoup, number: str) -> dict[str, Any]:
    marker = find_last_text(soup, rf"^Таблица\s*{re.escape(number)}\s*-?")
    table = marker.parent.find_next("table")
    if table is None:
        raise RuntimeError(f"table {number} not found")
    trs = table.find_all("tr")
    rows = []
    current_grades: list[str] | None = None
    prev_max = None

    for idx, tr in enumerate(trs[2:], 1):
        cells = [norm_text(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])]
        if len(cells) == 1:
            # notes/footnotes at the end
            continue
        if len(cells) == 6:
            raw_grade, raw_iv, ryn, run, ry, ru = cells
            current_grades = split_grades(raw_grade)
            prev_max = None
        elif len(cells) == 5:
            if current_grades is None:
                raise RuntimeError(f"table {number}: continuation without grade")
            raw_iv, ryn, run, ry, ru = cells
        else:
            raise RuntimeError(f"table {number}: unexpected cell count {len(cells)}: {cells}")

        iv = parse_interval(raw_iv, prev_max)
        prev_max = iv["max_mm"]
        rows.append({
            "source_row_index": len(rows) + 1,
            "grades": current_grades,
            "thickness_interval": iv,
            "Ryn_MPa": int(fnum(ryn)),
            "Run_MPa": int(fnum(run)),
            "Ry_MPa": None if ry == "-" else int(fnum(ry)),
            "Ru_MPa": None if ru == "-" else int(fnum(ru)),
            "source_cells": cells,
        })
    return {
        "table_number": number,
        "html_row_count_including_headers_notes": len(trs),
        "numeric_row_count": len(rows),
        "rows": rows,
    }


def extract_b1(soup: BeautifulSoup) -> dict[str, Any]:
    marker = find_last_text(soup, r"^Таблица\s*Б\.1\s*-")
    table = marker.parent.find_next("table")
    cells = []
    for tr in table.find_all("tr"):
        row = [norm_text(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])]
        if row:
            cells.append(row)
    flat = " | ".join(" :: ".join(r) for r in cells)
    # Require exact source tokens before materializing the values.
    required = [
        "проката и стальных отливок :: 7850",
        "Коэффициент линейного расширения α, °C -1 :: 0,12·10 -4",
        "прокатной стали, стальных отливок :: 2,06·10 5",
        "Модуль сдвига прокатной стали и стальных отливок G , Н/мм 2 :: 0,79·10 5",
        "Коэффициент поперечной деформации (Пуассона) ν :: 0,3",
    ]
    missing = [x for x in required if x not in flat]
    if missing:
        raise RuntimeError(f"B.1 source tokens missing: {missing}")
    return {
        "table_number": "Б.1",
        "rolled_steel": {
            "density_kg_m3": 7850.0,
            "linear_expansion_per_C": 1.2e-5,
            "E_MPa": 206000.0,
            "G_MPa": 79000.0,
            "poisson_ratio": 0.3,
        },
        "source_rows": cells,
    }


def extract_table2(soup: BeautifulSoup) -> dict[str, Any]:
    marker = find_exact_text(soup, "Таблица 2")
    table = marker.parent.find_next("table")
    rows = [[norm_text(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])] for tr in table.find_all("tr")]
    flat = " | ".join(" :: ".join(r) for r in rows)
    checks = {
        "Ry": "R y = R yn /γ m",
        "Ru": "R u = R un /γ m",
        "Rs": "R s = 0,58R yn /γ m",
        "Rp": "R p = R un /γ m",
        "Rlp": "R lp = 0,5R un /γ m",
        "Rcd": "R cd = 0,025R un /γ m",
    }
    missing = {k:v for k,v in checks.items() if v not in flat}
    if missing:
        raise RuntimeError(f"Table 2 source formula tokens missing: {missing}")
    return {
        "table_number": "2",
        "formula_contract": {
            "Ry": "Ryn/gamma_m",
            "Ru": "Run/gamma_m",
            "Rs": "0.58*Ryn/gamma_m",
            "Rp": "Run/gamma_m",
            "Rlp": "0.5*Run/gamma_m",
            "Rcd": "0.025*Run/gamma_m",
        },
        "source_rows": rows,
    }


def extract_table3(soup: BeautifulSoup) -> dict[str, Any]:
    marker = find_exact_text(soup, "Таблица 3")
    table = marker.parent.find_next("table")
    rows = [[norm_text(td.get_text(" ", strip=True)) for td in tr.find_all(["td", "th"])] for tr in table.find_all("tr")]
    values = [row[-1] for row in rows[1:]]
    expected = ["1,025", "1,100", "1,050", "1,000"]
    if values != expected:
        raise RuntimeError(f"Table 3 values changed: {values}")
    return {
        "table_number": "3",
        "categories_in_source_order": [
            {"id": "statistical_control", "gamma_m": 1.025, "source_text": rows[1][0]},
            {"id": "nonstatistical_high_yield_or_hot_finished_or_foreign", "gamma_m": 1.1, "source_text": rows[2][0]},
            {"id": "other_conforming", "gamma_m": 1.05, "source_text": rows[3][0]},
            {"id": "ks1_limited_service", "gamma_m": 1.0, "source_text": rows[4][0]},
        ],
        "source_rows": rows,
    }


def extract_gamma_u(soup: BeautifulSoup) -> dict[str, Any]:
    txt = norm_text(soup.get_text(" ", strip=True))
    # Capture an exact local clause contract, avoiding unrelated gamma_u occurrences.
    rx = re.compile(r"коэффициент надежности γ\s*u\s*=\s*1,3 для элементов конструкций, рассчитываемых на прочность с использованием расчетных сопротивлений R\s*u", re.I)
    m = rx.search(txt)
    if not m:
        # LibreOffice may separate symbol subscripts with spaces slightly differently.
        idx = txt.find("коэффициент надежности γ u = 1,3")
        if idx < 0:
            raise RuntimeError("gamma_u=1.3 clause 4.3.2 token not found")
        evidence = txt[idx:idx+220]
    else:
        evidence = m.group(0)
    return {"clause":"4.3.2","gamma_u":1.3,"source_text":evidence}


def main(html_path: Path, source_doc_path: Path | None, out_path: Path):
    if source_doc_path is not None:
        actual = sha256(source_doc_path)
        if actual != SOURCE_SHA256:
            raise RuntimeError(f"source DOC SHA mismatch: {actual}")
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8"), "html.parser")
    capture = {
        "schema_version": "1.0.0",
        "stage": "N1 — Material / Strength",
        "authority": "СП 16.13330.2017 current locked source only",
        "normative_source": {
            "designation": "СП 16.13330.2017, Changes 1–6 through 09.12.2024",
            "source_filename": "СП 16.13330(1).doc",
            "source_sha256": SOURCE_SHA256,
            "source_doc_hash_verified_at_capture": source_doc_path is not None,
            "source_included_in_release": False,
            "capture_transport": "LibreOffice HTML conversion of the locked DOC; numeric rows parsed from HTML table structure",
        },
        "B1": extract_b1(soup),
        "table_2": extract_table2(soup),
        "table_3": extract_table3(soup),
        "gamma_u": extract_gamma_u(soup),
        "V3": parse_strength_table(soup, "В.3"),
        "V4": parse_strength_table(soup, "В.4"),
        "V5": parse_strength_table(soup, "В.5"),
        "boundary_interpretation": {
            "policy": "For ditto-mark continuation rows, an exact lower boundary already owned by an explicitly inclusive preceding row is treated as lower-exclusive; a numeric gap such as 3.9→4.0 starts inclusive.",
            "reason": "Deterministic machine representation of the current table without overlap; raw source labels are retained per row.",
            "status": "SOURCE_PRESERVING_OPERATIONAL_INTERPRETATION",
        },
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(capture, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(out_path)
    print("V3/V4/V5 rows",capture["V3"]["numeric_row_count"],capture["V4"]["numeric_row_count"],capture["V5"]["numeric_row_count"])


if __name__ == "__main__":
    if len(sys.argv) not in (3,4):
        raise SystemExit("usage: extract_current_sp16_stage_n1.py <source.html> [<source.doc>] <out.json>")
    if len(sys.argv)==3:
        main(Path(sys.argv[1]), None, Path(sys.argv[2]))
    else:
        main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
