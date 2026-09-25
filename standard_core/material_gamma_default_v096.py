"""v0.96 Annex V / Table 3 material-safety default contract.

СП 16 Annex V tabulated design resistances are stated as obtained from normative
resistances by division by gamma_m selected per Table 3, rounded to 5 N/mm2.
For the materialized Annex V.3/V.4/V.5 selector rows the normative default is the
Table-3 statistical-control category, gamma_m=1.025.  An explicit user-selected
Table-3 category remains authoritative and triggers recomputation from Ryn/Run.
"""
from __future__ import annotations

from typing import Any, Mapping

from .material_resistance import (
    design_ultimate_resistance_n_mm2,
    design_yield_resistance_n_mm2,
    material_safety_factor,
)

DEFAULT_CATEGORY = "statistical_control"
DEFAULT_GAMMA_M = 1.025


def round_to_5_n_mm2(value: float) -> float:
    """Round positive resistance to the nearest 5 N/mm2 for Annex-V presentation."""
    return 5.0 * round(float(value) / 5.0)


def resolve_annex_v_design_strengths(
    *,
    Ryn_MPa: float,
    Run_MPa: float,
    Ry_tabulated_MPa: float | None,
    Ru_tabulated_MPa: float | None,
    gamma_m_category: str | None = None,
) -> dict[str, Any]:
    category = gamma_m_category or DEFAULT_CATEGORY
    gamma_m = float(material_safety_factor(category))
    ry_raw = design_yield_resistance_n_mm2(float(Ryn_MPa), gamma_m)
    ru_raw = design_ultimate_resistance_n_mm2(float(Run_MPa), gamma_m)
    ry = round_to_5_n_mm2(ry_raw)
    ru = round_to_5_n_mm2(ru_raw)
    return {
        "material_safety_category": category,
        "gamma_m": gamma_m,
        "gamma_m_is_annex_default": gamma_m_category is None,
        "gamma_m_basis": (
            "СП 16, табл. 3: прокат при статистической процедуре контроля свойств"
            if category == DEFAULT_CATEGORY else
            "СП 16, табл. 3: явно выбранная пользователем категория"
        ),
        "Ry_formula_MPa": ry,
        "Ru_formula_MPa": ru,
        "Ry_unrounded_MPa": ry_raw,
        "Ru_unrounded_MPa": ru_raw,
        "rounding_step_MPa": 5.0,
        "Ry_annex_MPa": Ry_tabulated_MPa,
        "Ru_annex_MPa": Ru_tabulated_MPa,
        "annex_default_matches": (
            gamma_m_category is not None or
            (Ry_tabulated_MPa is None or abs(ry - float(Ry_tabulated_MPa)) < 1e-9) and
            (Ru_tabulated_MPa is None or abs(ru - float(Ru_tabulated_MPa)) < 1e-9)
        ),
    }


__all__ = [
    "DEFAULT_CATEGORY", "DEFAULT_GAMMA_M", "round_to_5_n_mm2",
    "resolve_annex_v_design_strengths",
]
