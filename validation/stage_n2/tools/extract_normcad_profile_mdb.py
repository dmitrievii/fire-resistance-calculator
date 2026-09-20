from __future__ import annotations

import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path
from typing import Any, Iterator

PAGE_SIZE = 2048
PROFILE_FLOAT_FIELDS = (
    "h_mm",
    "b_mm",
    "tw_mm",
    "tf_mm",
    "r_mm",
    "A_mm2",
    "mass_kg_m_db",
    "Ix_mm4",
    "Iy_mm4",
    "Wx1_mm3",
    "Wx2_mm3",
    "Wy1_mm3",
    "Wy2_mm3",
    "Sx_mm3",
    "Sy_mm3",
    "It_mm4_db",
    "afwx",
    "afwy",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_records(path: Path) -> Iterator[tuple[int, int, int, bytes]]:
    raw = path.read_bytes()
    if not (raw[:4] == b"\x00\x01\x00\x00" and raw[4:19].startswith(b"Standard Jet DB")):
        raise ValueError("Only the observed Microsoft Access Jet3 format is supported")
    for page_index in range(1, len(raw) // PAGE_SIZE):
        page = raw[page_index * PAGE_SIZE : (page_index + 1) * PAGE_SIZE]
        if not page or page[0] != 1:
            continue
        row_count = struct.unpack_from("<H", page, 8)[0]
        if row_count > 200:
            continue
        offsets: list[tuple[int, int]] = []
        valid = True
        for row_index in range(row_count):
            offset_raw = struct.unpack_from("<H", page, 10 + 2 * row_index)[0]
            offset = offset_raw & 0x0FFF
            if not (10 + 2 * row_count <= offset < PAGE_SIZE):
                valid = False
                break
            offsets.append((offset_raw, offset))
        if not valid:
            continue
        for row_index, (offset_raw, offset) in enumerate(offsets):
            end = PAGE_SIZE if row_index == 0 else offsets[row_index - 1][1]
            if offset < end:
                yield page_index, row_index, offset_raw, page[offset:end]


def _printable_prefix(raw: bytes) -> str:
    text = raw.decode("cp1251", errors="ignore")
    out: list[str] = []
    for char in text:
        if ord(char) < 32 or char == "ÿ":
            break
        out.append(char)
    return "".join(out)


def _clean_family_caption(prefix: str) -> str:
    prefix = prefix.split("Drawings\\", 1)[0].strip()
    # Family records contain trailing Jet variable-column artefacts. Keep the
    # normative/catalog designation through the last recognizable standard.
    patterns = (
        r"^(.*?ГОСТ\s+Р\s+\d+(?:-\d+)?)",
        r"^(.*?ГОСТ\s+\d+(?:-\d+)?)",
        r"^(.*?СТО\s+АСЧМ\s+20-93)",
        r"^(.*?по\s+ТУ)",
    )
    for pattern in patterns:
        match = re.match(pattern, prefix, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    if prefix.startswith("Тавры колонные"):
        return "Тавры колонные"
    if prefix.startswith("Тавры нормальные"):
        return "Тавры нормальные"
    if prefix.startswith("Тавры широкополочные"):
        return "Тавры широкополочные"
    if prefix.startswith("Трубы"):
        return "Трубы"
    return prefix.rstrip("QZ[\\юѓ€„БAAHHDD>>00CCKK77??")


def _extract_designation(record: bytes) -> tuple[str, str]:
    prefix = _printable_prefix(record[81:])
    # Across all 4069 observed rows the final two printable characters are Jet
    # variable-column metadata, not part of the profile designation. Examples:
    # `15К4UQ -> 15К4`, `10Б1SQ -> 10Б1`, `Тр. 1420х39\\Q -> Тр. 1420х39`.
    designation = prefix[:-2] if len(prefix) >= 2 else prefix
    return designation.strip(), prefix


def extract(path: Path) -> dict[str, Any]:
    family_records: dict[int, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []

    for page, row_index, offset_raw, record in _iter_records(path):
        if len(record) >= 8 and record[0] == 4:
            family_id = struct.unpack_from("<I", record, 1)[0]
            if 1 <= family_id <= 100:
                raw_prefix = _printable_prefix(record[5:])
                if raw_prefix:
                    # Jet pages can contain short non-family records whose first
                    # bytes mimic the family marker/id.  The actual family dictionary
                    # occurs earlier in the observed DB and contains the full caption.
                    # Preserve the first valid record instead of overwriting it with
                    # later false-positive records (e.g. a one-character ``T``).
                    family_records.setdefault(
                        family_id,
                        {
                            "family_id": family_id,
                            "caption": _clean_family_caption(raw_prefix),
                            "printable_prefix_raw": raw_prefix,
                            "page": page,
                            "row": row_index,
                            "record_hex": record.hex(),
                        },
                    )

        if len(record) >= 84 and record[0] == 21:
            data_id = struct.unpack_from("<I", record, 1)[0]
            family_id = struct.unpack_from("<I", record, 5)[0]
            values = struct.unpack_from("<18f", record, 9)
            if not (1 <= data_id <= 100000 and 1 <= family_id <= 100):
                continue
            if not all(math.isfinite(value) for value in values):
                continue
            designation, designation_raw = _extract_designation(record)
            if not designation:
                continue
            item: dict[str, Any] = {
                "id_data": data_id,
                "family_id": family_id,
                "designation": designation,
                "designation_printable_prefix_raw": designation_raw,
            }
            item.update({name: round(float(value), 7) for name, value in zip(PROFILE_FLOAT_FIELDS, values)})
            item.update(
                {
                    "page": page,
                    "row": row_index,
                    "record_offset_raw": offset_raw,
                    "record_hex": record.hex(),
                }
            )
            rows.append(item)

    rows.sort(key=lambda item: item["id_data"])
    referenced_family_ids = sorted({int(item["family_id"]) for item in rows})
    families = [family_records[x] for x in referenced_family_ids if x in family_records]
    missing_family_records = sorted(set(referenced_family_ids) - set(family_records))

    if len(rows) != 4069:
        raise RuntimeError(f"Unexpected profile-row count: {len(rows)} != 4069")
    if len(referenced_family_ids) != 37:
        raise RuntimeError(f"Unexpected referenced family count: {len(referenced_family_ids)} != 37")
    if missing_family_records:
        raise RuntimeError(f"Missing family records: {missing_family_records}")

    return {
        "schema_version": "1.0.0",
        "capture_id": "NORMCAD_PROFILE_MDB_STATIC_CAPTURE_N2",
        "source_role": "HISTORICAL_SECONDARY_ORACLE_NOT_NORMATIVE",
        "source_file": path.name,
        "source_sha256": _sha256(path),
        "format": "Microsoft Access Jet3 / 2048-byte pages",
        "decoder_contract": {
            "profile_record_marker": 21,
            "id_data_offset": 1,
            "family_id_offset": 5,
            "float_block_offset": 9,
            "float_fields": list(PROFILE_FLOAT_FIELDS),
            "designation_offset": 81,
            "designation_trailing_printable_metadata_chars_removed": 2,
        },
        "family_count": len(families),
        "profile_row_count": len(rows),
        "families": families,
        "rows": rows,
        "limitations": [
            "Static Jet3 forensic decode; NormCAD executable was not run.",
            "Profile values are historical NormCAD data and are not promoted as current product-standard values.",
            "The DB mass field may differ from runtime/report mass because NormCAD can recompute mass from area and density.",
            "Current profile-standard source tables are required before production catalog promotion.",
        ],
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_normcad_profile_mdb.py INPUT.mdb OUTPUT.json")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = extract(source)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"families={payload['family_count']} profiles={payload['profile_row_count']} sha256={payload['source_sha256']}")


if __name__ == "__main__":
    main()
