from __future__ import annotations

from streamlit_expertise_report_v092_actions import (
    canonical_actions_section,
    replace_contextual_actions_section,
)


def _row(qid: str, value: float, unit: str) -> dict:
    return {
        "quantity_id": qid,
        "raw_value": value,
        "canonical_unit": unit,
        "name_ru": qid,
        "symbol": qid,
    }


def _report(**values: float) -> dict:
    units = {
        "ambient_N_force": "N",
        "ambient_M_z": "Nmm",
        "ambient_M_y": "Nmm",
        "ambient_M_x": "Nmm",
        "ambient_Q_z": "N",
        "ambient_Q_y": "N",
        "ambient_B_bimoment": "Nmm2",
    }
    rows = [_row(qid, value, units[qid]) for qid, value in values.items()]
    return {
        "blocks": [
            {
                "owner_node_id": "SP16_I_AMBIENT_LOADS",
                "inputs": rows,
                "outputs": [],
            }
        ]
    }


def test_pure_n_report_shows_only_axial_force_and_suppresses_zero_components():
    report = _report(
        ambient_N_force=-600_000.0,
        ambient_M_z=0.0,
        ambient_M_y=0.0,
        ambient_M_x=0.0,
        ambient_Q_z=0.0,
        ambient_Q_y=0.0,
        ambient_B_bimoment=0.0,
    )

    section = canonical_actions_section(report)

    assert "Продольная сила $N$" in section
    assert "-600 000 Н" in section
    assert "$M_z$" not in section
    assert "$M_y$" not in section
    assert "$M_x$" not in section
    assert "$Q_z$" not in section
    assert "$Q_y$" not in section
    assert "Бимомент $B$" not in section
    assert "результир" not in section.lower()


def test_mixed_actions_use_canonical_axes_preserve_signs_and_never_call_mx_bending():
    report = _report(
        ambient_N_force=-600_000.0,
        ambient_M_z=1_500_000.0,
        ambient_M_y=0.0,
        ambient_M_x=-200_000.0,
        ambient_Q_z=0.0,
        ambient_Q_y=0.0,
        ambient_B_bimoment=0.0,
    )

    section = canonical_actions_section(report)

    assert "Продольная сила $N$: **-600 000 Н**" in section
    assert "Изгибающий момент $M_z$ (сильная ось z): **1 500 000 Н·мм**" in section
    assert "Крутящий момент $M_x$: **-200 000 Н·мм**" in section
    assert "Изгибающий момент $M_x$" not in section
    assert "$M_y$" not in section
    assert "$Q_z$" not in section
    assert "$Q_y$" not in section
    assert "Бимомент $B$" not in section


def test_active_overlay_replaces_legacy_load_section_and_removes_zero_action_paragraph():
    report = _report(
        ambient_N_force=-600_000.0,
        ambient_M_z=0.0,
        ambient_M_y=0.0,
        ambient_M_x=0.0,
        ambient_Q_z=0.0,
        ambient_Q_y=0.0,
        ambient_B_bimoment=0.0,
    )
    legacy = """# Расчёт

## 1. Исходные данные

### 1.2 Расчётные усилия

$N$ = **-600 000 Н**;  $M_x$ = **0 Н·мм**;  $M_y$ = **0 Н·мм**;  $Q_x$ = **0 Н**;  $Q_y$ = **0 Н**;  $T$ = **0 Н·мм**;  $B$ = **0 Н·мм²**.

### 1.3 Ослабления сечения

Ослаблений нет.

## 3. Проверка несущей способности по СП 16

Для данного сочетания $M_x$ = $M_y$ = $Q_x$ = $Q_y$ = $T$ = $B$ = 0; соответствующие проверки изгиба, среза, кручения и их сочетаний не являются определяющими.
"""

    rendered = replace_contextual_actions_section(legacy, report)

    assert rendered.count("### 1.2 Расчётные усилия") == 1
    assert "Продольная сила $N$: **-600 000 Н**" in rendered
    assert "$M_x$ = **0" not in rendered
    assert "$Q_x$" not in rendered
    assert "$T$" not in rendered
    assert "Для данного сочетания" not in rendered
    assert "### 1.3 Ослабления сечения" in rendered
    assert "## 3. Проверка несущей способности по СП 16" in rendered


def test_all_zero_actions_remove_load_subsection_instead_of_listing_inactive_components():
    report = _report(
        ambient_N_force=0.0,
        ambient_M_z=0.0,
        ambient_M_y=0.0,
        ambient_M_x=0.0,
        ambient_Q_z=0.0,
        ambient_Q_y=0.0,
        ambient_B_bimoment=0.0,
    )
    legacy = """## 1. Исходные данные

### 1.2 Расчётные усилия

$N$ = **0 Н**; $M_x$ = **0 Н·мм**.

## 2. Материал
"""

    rendered = replace_contextual_actions_section(legacy, report)

    assert "### 1.2 Расчётные усилия" not in rendered
    assert "$M_x$" not in rendered
    assert "## 2. Материал" in rendered
