from __future__ import annotations

"""v0.73 existing-session compatibility hotfix.

v0.72 correctly remediated newly created FireUI1Application objects, but a
Streamlit process can retain an older ``_fire_app`` in ``st.session_state``.
This adapter applies the same qualified MECH7 registry wrapper to that retained
application and provides a one-time explicit SP16 Table-3 migration for legacy
sessions whose material editor had already been completed before the category
selector existed.
"""

from typing import Any, Mapping

import streamlit_guided_ux_v072 as _v072
from standard_core.sp16_mech7_v072_remediation import install_registry_remediation
from standard_core.sp16_mech7_v073_session_remediation import (
    MATERIAL_EDITOR_NODE_ID,
    MATERIAL_SAFETY_QUANTITY_ID,
    replay_with_material_safety_category,
)

_INSTALL_SENTINEL = "_guided_ux_v073_installed"
_CANONICAL_ENSURE_APP = "_guided_ux_v073_canonical_ensure_app"
_CANONICAL_RENDER_HISTORY = "_guided_ux_v073_canonical_render_history"


def _remediate_application(app: Any) -> Any:
    """Install v0.72 MECH7 remediation on a retained app and all live sessions."""
    install_registry_remediation(app.service.registry)
    for session in list(app.service.sessions.values()):
        if session.registry is not app.service.registry:
            install_registry_remediation(session.registry)
    return app


def _install_existing_application_patch(core: Any) -> None:
    if not hasattr(core, _CANONICAL_ENSURE_APP):
        setattr(core, _CANONICAL_ENSURE_APP, core._ensure_app)
    canonical = getattr(core, _CANONICAL_ENSURE_APP)

    def remediated_ensure_app():
        return _remediate_application(canonical())

    setattr(remediated_ensure_app, "_guided_ux_v073_existing_app_remediation", True)
    core._ensure_app = remediated_ensure_app


def _legacy_table3_migration_required(env: Mapping[str, Any]) -> bool:
    state = env.get("state") or {}
    values = state.get("values") or {}
    if MATERIAL_SAFETY_QUANTITY_ID in values:
        return False
    history = list(state.get("interaction_history") or [])
    return any(str(row.get("node_id") or "") == MATERIAL_EDITOR_NODE_ID for row in history)


def _render_legacy_table3_migration(core: Any, app: Any, env: Mapping[str, Any]) -> None:
    st = core._st()
    sid = str(env.get("session_id") or "")
    session = app.service.get_session(sid)
    key = _v072._category_state_key("legacy-existing-session")
    values = [value for value, _ in _v072._MATERIAL_SAFETY_OPTIONS]
    current = st.session_state.get(key)

    st.warning(
        "Этот расчёт был открыт до добавления явного выбора γm по таблице 3 СП16. "
        "Чтобы продолжить тот же расчёт без скрытого значения γm, выберите категорию контроля проката."
    )
    category = st.selectbox(
        "Условия контроля свойств проката для выбора γm · СП16, таблица 3",
        values,
        index=values.index(current) if current in values else None,
        placeholder="— выберите категорию таблицы 3 —",
        format_func=lambda value: _v072._MATERIAL_SAFETY_LABELS[value],
        key=key,
    )
    st.caption(
        "После подтверждения история введённых данных будет детерминированно переиграна, "
        "а все последующие расчётные узлы будут вычислены заново через текущий production runtime."
    )
    if st.button(
        "Применить категорию и пересчитать",
        type="primary",
        disabled=category is None,
        width="stretch",
        key="fire:v073:legacy-table3:apply",
    ):
        migrated = replay_with_material_safety_category(session, str(category))
        app.service.sessions[sid] = migrated
        st.rerun()


def _install_legacy_migration_surface(core: Any) -> None:
    if not hasattr(core, _CANONICAL_RENDER_HISTORY):
        setattr(core, _CANONICAL_RENDER_HISTORY, core._render_history)
    canonical = getattr(core, _CANONICAL_RENDER_HISTORY)

    def render_history_with_migration(app: Any, env: Mapping[str, Any]) -> None:
        canonical(app, env)
        if not _legacy_table3_migration_required(env):
            return
        _render_legacy_table3_migration(core, app, env)
        # Do not render or submit the next normative card until the missing
        # explicit Table-3 input has been supplied and the history replayed.
        core._st().stop()

    setattr(render_history_with_migration, "_guided_ux_v073_legacy_table3_surface", True)
    core._render_history = render_history_with_migration


def install(core: Any) -> None:
    if getattr(core, _INSTALL_SENTINEL, False):
        return

    # Preserve every v0.72 presentation/runtime remediation first.  This call is
    # itself idempotent and also works when streamlit_app_core survived a hot
    # reload with the v0.72 sentinel already set.
    _v072.install(core)
    _install_existing_application_patch(core)
    _install_legacy_migration_surface(core)
    setattr(core, _INSTALL_SENTINEL, True)


__all__ = ["install"]
