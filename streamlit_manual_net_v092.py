"""Streamlit v0.92 manual net-property remediation.

Restores the explicit weakening choice between the qualified simplified geometry
solver and user-supplied net section properties.  The user enters properties in
the active canonical z/y system.  A_net is deliberately absent from the editor:
it remains geometry-derived from the accepted web-hole model.
"""
from __future__ import annotations

from typing import Any, Mapping

from standard_core.fire_ui14_manual_net_v092 import (
    MANUAL_MODE,
    install_registry_remediation,
)

_INSTALLED = "_fire_v092_manual_net_properties_installed"
AUTO_MODE = "automatic_geometry"


def _number(st: Any, core: Any, card: Mapping[str, Any], mode_key: str, key: str, label: str, old: Mapping[str, Any], *, required: bool) -> float | None:
    raw = old.get(key)
    value = st.number_input(
        label,
        min_value=0.0,
        value=float(raw) if isinstance(raw, (int, float)) and not isinstance(raw, bool) else None,
        key=core._key(mode_key, card["node_id"], "manual-net", key),
    )
    if value is None:
        return None
    number = float(value)
    if number <= 0.0:
        if required:
            st.warning(f"{label}: требуется значение > 0.")
        return None
    return number


def _render_weakening(core: Any, card: Mapping[str, Any], old: Any, mode_key: str):
    st = core._st()
    old = old if isinstance(old, Mapping) else {}
    has_old = bool(old.get("holes_present"))
    choice = st.radio(
        "Ослабления",
        ["none", "holes"],
        index=1 if has_old else 0,
        format_func=lambda value: "Есть болтовые отверстия" if value == "holes" else "Отверстий нет",
        horizontal=True,
        key=core._key(mode_key, card["node_id"], "weak-v092"),
    )
    if choice == "none":
        return {
            "schema": "section_weakening_model_v0.92",
            "holes_present": False,
            "model": "none",
        }, None, True

    d = st.number_input(
        "Диаметр отверстия d, мм",
        min_value=0.0,
        value=float(old.get("hole_diameter_mm", 20.0)),
        key=core._key(mode_key, card["node_id"], "d-v092"),
    )
    s = st.number_input(
        "Шаг отверстий s, мм",
        min_value=0.0,
        value=float(old.get("hole_pitch_mm", 80.0)),
        key=core._key(mode_key, card["node_id"], "s-v092"),
    )
    if s <= d:
        st.warning("Для формулы (45) СП 16 требуется s > d.")

    old_mode = str(old.get("net_property_mode") or AUTO_MODE)
    modes = [AUTO_MODE, MANUAL_MODE]
    net_mode = st.radio(
        "Характеристики ослабленного сечения",
        modes,
        index=modes.index(old_mode) if old_mode in modes else 0,
        format_func=lambda value: (
            "Рассчитать по упрощённой геометрической модели"
            if value == AUTO_MODE
            else "Введите готовые характеристики нетто"
        ),
        key=core._key(mode_key, card["node_id"], "net-property-mode-v092"),
    )

    payload: dict[str, Any] = {
        "schema": "section_weakening_model_v0.92",
        "holes_present": True,
        "model": "central_web_bolt_hole_formula45_v1",
        "hole_diameter_mm": float(d),
        "hole_pitch_mm": float(s),
        "net_property_mode": net_mode,
    }
    ready = d > 0.0 and s > d

    if net_mode == MANUAL_MODE:
        st.caption(
            "Aₙ вручную не задаётся: площадь нетто всегда рассчитывается из геометрии отверстия как A − d·t_w. "
            "Задаваемые ниже I и W считаются готовыми характеристиками нетто."
        )
        st.markdown("**Главные оси активного расчёта: z-z — сильная, y-y — слабая.**")
        old_bundle = old.get("manual_net_properties")
        old_bundle = old_bundle if isinstance(old_bundle, Mapping) else {}
        bundle: dict[str, float] = {}
        required_fields = [
            ("I_z_n_mm4", "Момент инерции нетто I_z,n, мм⁴"),
            ("I_y_n_mm4", "Момент инерции нетто I_y,n, мм⁴"),
            ("W_z_n_mm3", "Упругий момент сопротивления нетто W_z,n, мм³"),
            ("W_y_n_mm3", "Упругий момент сопротивления нетто W_y,n, мм³"),
        ]
        for key, label in required_fields:
            value = _number(st, core, card, mode_key, key, label, old_bundle, required=True)
            if value is None:
                ready = False
            else:
                bundle[key] = value

        optional_default = any(
            key in old_bundle
            for key in ("W_pl_z_eff_mm3", "W_pl_y_eff_mm3", "I_omega_n_mm6", "W_omega_eff_mm4")
        )
        advanced = st.checkbox(
            "Задать дополнительные эффективные характеристики",
            value=optional_default,
            key=core._key(mode_key, card["node_id"], "manual-net-advanced-v092"),
        )
        if advanced:
            st.caption(
                "Эти значения сохраняются с пользовательским provenance. Они используются только теми нормативными ветвями, "
                "которые действительно потребляют соответствующую характеристику."
            )
            wzpl = _number(st, core, card, mode_key, "W_pl_z_eff_mm3", "Пластический момент сопротивления W_pl,z,eff, мм³", old_bundle, required=False)
            wypl = _number(st, core, card, mode_key, "W_pl_y_eff_mm3", "Пластический момент сопротивления W_pl,y,eff, мм³", old_bundle, required=False)
            if (wzpl is None) != (wypl is None):
                st.warning("Для пластических характеристик задайте одновременно W_pl,z,eff и W_pl,y,eff.")
                ready = False
            if wzpl is not None and wypl is not None:
                bundle["W_pl_z_eff_mm3"] = wzpl
                bundle["W_pl_y_eff_mm3"] = wypl

            iomega = _number(st, core, card, mode_key, "I_omega_n_mm6", "Секториальный момент инерции нетто I_ω,n, мм⁶", old_bundle, required=False)
            womega = _number(st, core, card, mode_key, "W_omega_eff_mm4", "Секториальный момент сопротивления W_ω,eff, мм⁴", old_bundle, required=False)
            if iomega is not None:
                bundle["I_omega_n_mm6"] = iomega
            if womega is not None:
                bundle["W_omega_eff_mm4"] = womega

        payload["manual_net_properties"] = bundle
        st.info("Источник этих I/W: введено пользователем как характеристики нетто. Технические ID доступны в Audit.")

    return (payload if ready else None), None, ready


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return

    previous_new_application = core._new_application
    previous_ensure_app = core._ensure_app

    def _upgrade(app):
        install_registry_remediation(app.service.registry)
        return app

    core._new_application = lambda: _upgrade(previous_new_application())
    core._ensure_app = lambda: _upgrade(previous_ensure_app())
    core._render_weakening = lambda card, old, mode_key: _render_weakening(core, card, old, mode_key)
    setattr(core, _INSTALLED, True)


__all__ = ["AUTO_MODE", "install"]
