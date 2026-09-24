"""v0.93 protected-geometry evidence presentation.

Closes audit item #18 without changing SP554 algebra. FIRE-UI1.9 already
calculates the protected Table-1 perimeter in the production runtime; this
adapter makes that executed evidence visible immediately after the user chooses
contour/box protection and before subsequent protection-thickness input.
"""
from __future__ import annotations

from typing import Any, Mapping

_INSTALLED = "_fire_v093_protection_geometry_evidence_installed"


def _ledger(env: Mapping[str, Any]) -> dict[str, Any]:
    return {
        str(row.get("quantity_id")): row.get("value")
        for row in env.get("state", {}).get("ledger", [])
        if isinstance(row, Mapping) and row.get("quantity_id")
    }


def _fmt(core: Any, value: Any) -> str:
    try:
        return core._fmt(value)
    except Exception:
        return str(value)


def _render_geometry_evidence(core: Any, env: Mapping[str, Any], card: Mapping[str, Any]) -> None:
    values = _ledger(env)
    mode = values.get("fire_protection_perimeter_mode")
    trace = values.get("sp554_protected_table1_perimeter_trace")
    if mode not in {"contour", "box"} or not isinstance(trace, Mapping):
        return
    # Do not duplicate the decision card itself. The automatic perimeter node is
    # executed by the guided scheduler immediately after that decision, so the
    # evidence appears on the following interactive card (before delta_f input).
    if str(card.get("node_id") or "") == "SP554_D_PROTECTION_PERIMETER_MODE":
        return

    p_m = values.get("P_heated_protected", trace.get("P_m"))
    delta = values.get("delta_pr_protected")
    if delta is None:
        delta = values.get("delta_pr_prot")
    formula = str(trace.get("formula") or "")
    B, D, t = trace.get("B_mm"), trace.get("D_mm"), trace.get("t_mm")

    st = core.st
    with st.container(border=True):
        st.markdown("#### Геометрия огнезащиты · СП 554, таблица 1")
        st.caption("Расчёт выполнен автоматически сразу после выбора схемы защиты; толщина огнезащиты в эту геометрию не входит.")
        st.markdown(f"Схема: **{'по контуру профиля' if mode == 'contour' else 'коробчатая'}**; обогрев: **{trace.get('heated_sides', '—')} стороны**.")
        if formula:
            substitutions = []
            if isinstance(B, (int, float)):
                substitutions.append(f"B={_fmt(core, B)} мм")
            if isinstance(D, (int, float)):
                substitutions.append(f"D={_fmt(core, D)} мм")
            if isinstance(t, (int, float)):
                substitutions.append(f"t_w={_fmt(core, t)} мм")
            subst = ", ".join(substitutions)
            st.markdown(f"**P_prot = {formula}**" + (f", где {subst}." if subst else "."))
        if isinstance(p_m, (int, float)):
            st.markdown(f"**P_prot = {_fmt(core, p_m)} м** ({_fmt(core, float(p_m)*1000.0)} мм).")
        if isinstance(delta, (int, float)):
            st.markdown(f"По формуле (12.2) **δ_pr,prot = A / P_prot = {_fmt(core, delta)} мм**.")
        else:
            st.caption("δ_pr,prot будет показана здесь сразу после выполнения автоматического узла A/P_prot; ручной ввод не требуется.")


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return
    previous = core._render_card_body

    def _render_card_body(app, sid, env, card, old_payload, old_provenance, mode_key):
        result = previous(app, sid, env, card, old_payload, old_provenance, mode_key)
        _render_geometry_evidence(core, env, card)
        return result

    core._render_card_body = _render_card_body
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_render_geometry_evidence"]
