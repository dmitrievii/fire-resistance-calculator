"""v0.100 canonical signed-load menu remediation.

The historical Streamlit load renderer hard-coded the pre-v0.92 quantity ids
(Mx bending, Qx shear, T torsion).  After the active graph was migrated to the
canonical SP16 convention (Mz/My bending, Mx torsion, Qz/Qy shear), that renderer
could still submit ambient_Q_x and ambient_T_torsion to SP16_I_AMBIENT_LOADS.

This installer replaces only the UI renderer.  It derives the payload strictly
from the active card fields, so a canonical card cannot emit legacy quantity ids.
No numerical SP16/SP554 executor or engineering equation is changed.
"""
from __future__ import annotations

from typing import Any, Mapping

_INSTALLED = "_fire_v0100_canonical_load_menu_installed"


def _field_ids(card: Mapping[str, Any]) -> set[str]:
    return {
        str(row.get("quantity_id"))
        for row in card.get("fields", [])
        if isinstance(row, Mapping) and row.get("quantity_id")
    }


def _contract(kind: str, card: Mapping[str, Any]) -> dict[str, str | None]:
    fields = _field_ids(card)
    if kind == "ambient":
        candidates = {
            "N": "ambient_N_force",
            "Mz": "ambient_M_z",
            "My": "ambient_M_y",
            "Mx": "ambient_M_x",
            "Qz": "ambient_Q_z",
            "Qy": "ambient_Q_y",
            "combo": "ambient_load_combination",
        }
    else:
        candidates = {
            "N": "N_force",
            "Mz": "M_z",
            "My": "M_y",
            "Mx": "M_x",
            "Qz": "Q_z",
            "Qy": "Q_y",
            "combo": "special_load_combination",
        }
    return {key: (qid if qid in fields else None) for key, qid in candidates.items()}


def _old_value(old: Mapping[str, Any], qid: str | None, scale: float) -> float:
    if not qid:
        return 0.0
    value = old.get(qid, 0.0)
    return float(value) / scale if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def _payload_for_contract(q: Mapping[str, str | None], values: Mapping[str, float], *, kind: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    scales = {"N": 1e3, "Mz": 1e6, "My": 1e6, "Mx": 1e6, "Qz": 1e3, "Qy": 1e3}
    for key, scale in scales.items():
        qid = q.get(key)
        if qid:
            payload[qid] = float(values[key]) * scale
    combo_qid = q.get("combo")
    if combo_qid:
        payload[combo_qid] = {
            "schema": "sp16_mech2_ambient_combination_v092_canonical_axes" if kind == "ambient" else "sp16_mech2_fire_special_combination_v092_canonical_axes",
            "kind": kind,
            "convention": "x member axis; z-z/y-y principal axes; Mz/My bending; Mx torsion; Qz/Qy shear",
            "display_units": {"force": "kN", "moment": "kNm"},
            "N_kN": float(values["N"]),
            "Mz_kNm": float(values["Mz"]),
            "My_kNm": float(values["My"]),
            "Mx_kNm": float(values["Mx"]),
            "Qz_kN": float(values["Qz"]),
            "Qy_kN": float(values["Qy"]),
        }
    return payload


def install(core: Any) -> None:
    if getattr(core, _INSTALLED, False):
        return

    def _render_load_menu(card: Mapping[str, Any], old: Any, mode_key: str, kind: str):
        old_map = old if isinstance(old, Mapping) else {}
        q = _contract(kind, card)
        st = core.st

        cols = st.columns(3)
        N = cols[0].number_input("N, кН", value=_old_value(old_map, q["N"], 1e3), key=core._key(mode_key, card["node_id"], "N"))
        Mz = cols[1].number_input("Mz, кН·м", value=_old_value(old_map, q["Mz"], 1e6), key=core._key(mode_key, card["node_id"], "Mz"))
        My = cols[2].number_input("My, кН·м", value=_old_value(old_map, q["My"], 1e6), key=core._key(mode_key, card["node_id"], "My"))
        cols = st.columns(3)
        Mx = cols[0].number_input("Mx (кручение), кН·м", value=_old_value(old_map, q["Mx"], 1e6), key=core._key(mode_key, card["node_id"], "Mx"))
        Qz = cols[1].number_input("Qz, кН", value=_old_value(old_map, q["Qz"], 1e3), key=core._key(mode_key, card["node_id"], "Qz"))
        Qy = cols[2].number_input("Qy, кН", value=_old_value(old_map, q["Qy"], 1e3), key=core._key(mode_key, card["node_id"], "Qy"))

        if Mx != 0 or Qy != 0:
            st.warning("Mx (кручение) и Qy сохраняются как самостоятельные канонические компоненты; неподдержанная downstream-ветвь остановится fail-closed. Mx→B и Qy→Qz запрещены.")

        values = {"N": N, "Mz": Mz, "My": My, "Mx": Mx, "Qz": Qz, "Qy": Qy}
        payload = _payload_for_contract(q, values, kind=kind)

        if kind == "fire" and any(f.get("quantity_id") == "sp16_local_load_F" for f in card.get("fields", [])):
            old_f = old_map.get("sp16_local_load_F")
            force = st.number_input(
                "Местная сосредоточенная сила F, кН (необязательно)",
                value=(float(old_f) / 1e3) if isinstance(old_f, (int, float)) and not isinstance(old_f, bool) else None,
                key=core._key(mode_key, card["node_id"], "localF"),
            )
            if force is not None:
                payload["sp16_local_load_F"] = float(force) * 1e3
        return payload, None, True

    core._render_load_menu = _render_load_menu
    setattr(core, _INSTALLED, True)


__all__ = ["install", "_contract", "_payload_for_contract"]
