"""v0.92 readable/canonical section-property presentation.

The profile catalogue retains historical source-column names such as ``Ix`` /
``Iy``.  Those are data-source fields, not active SP16 axes.  The active v0.92
contract is z = strong principal axis and y = weak principal axis.

This presentation layer resolves the physical major/minor mapping from the
selected catalogue row and renders engineering names as:

    Russian name + canonical symbol + value + unit.

No normative calculation route or stored catalogue value is changed.  Raw
source-field identifiers remain available through Audit/provenance rather than
being exposed as primary UI labels.
"""
from __future__ import annotations

import math
from typing import Any, Mapping

import streamlit_guided_ux as _guided

_INSTALL_SENTINEL = "_fire_v092_readable_section_properties_installed"

_DIMENSION_LABELS: dict[str, tuple[str, str, str]] = {
    "h_mm": ("Высота сечения", "h", "мм"),
    "b_mm": ("Ширина полки", "b", "мм"),
    "s_mm": ("Толщина стенки", "t_w", "мм"),
    "tw_mm": ("Толщина стенки", "t_w", "мм"),
    "t_mm": ("Толщина элемента профиля", "t", "мм"),
    "tf_mm": ("Толщина полки", "t_f", "мм"),
    "r_mm": ("Радиус сопряжения", "r", "мм"),
    "r1_mm": ("Радиус сопряжения", "r_1", "мм"),
    "r2_mm": ("Радиус сопряжения", "r_2", "мм"),
    "D_mm": ("Наружный диаметр", "D", "мм"),
    "d_mm": ("Диаметр", "d", "мм"),
}


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _append(rows: list[dict[str, Any]], name: str, symbol: str, value: Any, unit: str, *, source_fields: list[str]) -> None:
    number = _finite_number(value)
    if number is None:
        return
    rows.append(
        {
            "name_ru": name,
            "symbol": symbol,
            "value": number,
            "unit": unit,
            "source_fields": list(source_fields),
        }
    )


def _axis_bundle(resolved: Mapping[str, Any]) -> dict[str, Any]:
    """Map retained catalogue x/y columns to active strong-z / weak-y axes."""
    props = resolved.get("catalog_properties_interim")
    props = props if isinstance(props, Mapping) else {}
    derived = resolved.get("derived_properties")
    derived = derived if isinstance(derived, Mapping) else {}

    ix = _finite_number(props.get("Ix_mm4"))
    iy = _finite_number(props.get("Iy_mm4"))
    if ix is None or iy is None or min(ix, iy) <= 0.0:
        return {}

    area = _finite_number(props.get("A_mm2"))
    rx = _finite_number(derived.get("radius_x_mm"))
    ry = _finite_number(derived.get("radius_y_mm"))
    if area is not None and area > 0.0:
        if rx is None:
            rx = math.sqrt(ix / area)
        if ry is None:
            ry = math.sqrt(iy / area)

    source = {
        "x": {
            "I": ix,
            "i": rx,
            "W_pos": _finite_number(props.get("Wx1_mm3")) or _finite_number(props.get("Wx_mm3")),
            "W_neg": _finite_number(props.get("Wx2_mm3")) or _finite_number(props.get("Wx_mm3")),
            "S": _finite_number(props.get("Sx_mm3")),
            "I_field": "Ix_mm4",
            "i_field": "radius_x_mm",
            "W_fields": ["Wx1_mm3", "Wx2_mm3"],
            "S_field": "Sx_mm3",
        },
        "y": {
            "I": iy,
            "i": ry,
            "W_pos": _finite_number(props.get("Wy1_mm3")) or _finite_number(props.get("Wy_mm3")),
            "W_neg": _finite_number(props.get("Wy2_mm3")) or _finite_number(props.get("Wy_mm3")),
            "S": _finite_number(props.get("Sy_mm3")),
            "I_field": "Iy_mm4",
            "i_field": "radius_y_mm",
            "W_fields": ["Wy1_mm3", "Wy2_mm3"],
            "S_field": "Sy_mm3",
        },
    }
    major_key, minor_key = ("x", "y") if ix >= iy else ("y", "x")
    return {
        "z": source[major_key],
        "y": source[minor_key],
        "source_major_axis": major_key,
        "source_minor_axis": minor_key,
        "method": "physical_major_minor_inertia_to_canonical_z_y",
    }


def canonical_profile_rows(resolved: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return human-readable profile rows without exposing technical quantity IDs."""
    dims = resolved.get("dimensions")
    dims = dims if isinstance(dims, Mapping) else {}
    props = resolved.get("catalog_properties_interim")
    props = props if isinstance(props, Mapping) else {}
    rows: list[dict[str, Any]] = []

    seen_dimension_symbols: set[str] = set()
    for key, value in dims.items():
        label = _DIMENSION_LABELS.get(str(key))
        if label is None:
            continue
        name, symbol, unit = label
        # Catalogues sometimes expose the same physical wall thickness under
        # both s_mm and tw_mm.  Do not duplicate it in the engineering preview.
        if symbol in seen_dimension_symbols:
            continue
        before = len(rows)
        _append(rows, name, symbol, value, unit, source_fields=[str(key)])
        if len(rows) > before:
            seen_dimension_symbols.add(symbol)

    _append(rows, "Площадь поперечного сечения", "A", props.get("A_mm2"), "мм²", source_fields=["A_mm2"])

    axes = _axis_bundle(resolved)
    for axis, qualifier in (("z", "сильной"), ("y", "слабой")):
        data = axes.get(axis)
        if not isinstance(data, Mapping):
            continue
        _append(
            rows,
            f"Момент инерции относительно {qualifier} главной оси {axis}-{axis}",
            f"I_{axis}",
            data.get("I"),
            "мм⁴",
            source_fields=[str(data.get("I_field"))],
        )
        _append(
            rows,
            f"Радиус инерции относительно {qualifier} главной оси {axis}-{axis}",
            f"i_{axis}",
            data.get("i"),
            "мм",
            source_fields=[str(data.get("i_field"))],
        )

        w_pos = _finite_number(data.get("W_pos"))
        w_neg = _finite_number(data.get("W_neg"))
        w_fields = [str(item) for item in data.get("W_fields") or []]
        if w_pos is not None and w_neg is not None and math.isclose(w_pos, w_neg, rel_tol=1e-10, abs_tol=1e-9):
            _append(
                rows,
                f"Упругий момент сопротивления относительно {qualifier} главной оси {axis}-{axis}",
                f"W_{axis}",
                w_pos,
                "мм³",
                source_fields=w_fields,
            )
        else:
            _append(
                rows,
                f"Упругий момент сопротивления относительно {qualifier} главной оси {axis}-{axis}, положительная сторона",
                f"W_{{{axis},+}}",
                w_pos,
                "мм³",
                source_fields=w_fields[:1],
            )
            _append(
                rows,
                f"Упругий момент сопротивления относительно {qualifier} главной оси {axis}-{axis}, отрицательная сторона",
                f"W_{{{axis},-}}",
                w_neg,
                "мм³",
                source_fields=w_fields[1:2],
            )

        _append(
            rows,
            f"Статический момент площади для расчёта по оси {axis}-{axis}",
            f"S_{axis}",
            data.get("S"),
            "мм³",
            source_fields=[str(data.get("S_field"))],
        )

    mass = props.get("mass_kg_m")
    if mass is None:
        mass = props.get("mass_kg_per_m")
    _append(rows, "Масса одного метра профиля", "m", mass, "кг/м", source_fields=["mass_kg_m"])
    return rows


def _render_profile_catalog(core: Any, app: Any, card: Mapping[str, Any], old: Any, mode_key: str):
    """Drop-in replacement for the retained profile catalogue card renderer."""
    st = core._st()
    old = old if isinstance(old, Mapping) else {}
    data = app.profile_catalog_families()
    families = [
        row for row in data["families"]
        if row.get("shape_group") not in {"C_LIPPED_SECTION", "Z_SECTION"}
    ]
    family_ids = [int(row["family_id"]) for row in families]
    fmap = {int(row["family_id"]): row for row in families}
    current_family = int(old.get("section_catalog_family_id") or 0)
    family_id = st.selectbox(
        "Сортамент / семейство",
        family_ids,
        index=family_ids.index(current_family) if current_family in family_ids else None,
        placeholder="— выберите семейство —",
        format_func=lambda fid: str(fmap[fid].get("caption") or fid),
        key=core._key(mode_key, card["node_id"], "family"),
    )
    if family_id is None:
        return None, None, False

    profiles = app.profile_catalog_profiles(int(family_id))["profiles"]
    refs = [(str(row["designation"]), int(row["source_row_id"])) for row in profiles]
    current_ref = (
        str(old.get("section_designation") or ""),
        int(old.get("section_catalog_source_row_id") or 0),
    )
    selected = st.selectbox(
        "Профиль",
        refs,
        index=refs.index(current_ref) if current_ref in refs else None,
        placeholder="— выберите профиль —",
        format_func=lambda ref: ref[0],
        key=core._key(mode_key, card["node_id"], "profile", family_id),
    )
    if selected is None:
        return None, None, False

    designation, source_row_id = selected
    resolved = app.profile_catalog_resolve(int(family_id), designation, source_row_id)
    shape = str(resolved.get("shape_group") or "OTHER")
    rows = canonical_profile_rows(resolved)

    with st.container(border=True):
        st.markdown(f"**Характеристики профиля {designation}**")
        for row in rows:
            st.markdown(
                f"- {row['name_ru']}: **{row['symbol']} = {core._fmt(row['value'])} {row['unit']}**"
            )
    st.caption(
        "Оси активного расчёта: z-z — сильная, y-y — слабая. "
        "Исходные названия столбцов сортамента сохраняются только в Audit/provenance."
    )

    payload = {
        "section_catalog_standard": (
            (resolved.get("source") or {}).get("product_standard_label_unverified")
            or (resolved.get("family") or {}).get("caption")
            or "catalog"
        ),
        "section_designation": designation,
        "section_family": core._section_family_from_shape(shape),
        "sp16_i_symmetry_class": "double_symmetric" if shape == "I_ROLLED_DSYMM" else "not_i",
        "section_catalog_family_id": int(family_id),
        "section_catalog_source_row_id": int(source_row_id),
    }
    return payload, None, True


def install(core: Any) -> None:
    if getattr(core, _INSTALL_SENTINEL, False):
        return
    # The v0.70+ guided-profile closure resolves this module global at render
    # time, therefore replacing it here updates fresh and retained applications
    # without touching calculation/runtime state.
    _guided._render_profile_catalog = _render_profile_catalog
    setattr(core, _INSTALL_SENTINEL, True)


__all__ = ["canonical_profile_rows", "install"]
