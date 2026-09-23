"""Canonical published SP 554.1311500.2026 Appendix B, Table B.1.

This overlay replaces the earlier draft/delta representation with the complete
published table.  Tuple order is always (temperature_c, gamma_E, gamma_T),
matching the published column order: modulus reduction first, strength
reduction second.
"""
from __future__ import annotations

from . import fire_sp554_runtime as _runtime


FINAL_B1: dict[str, tuple[tuple[float, float, float], ...]] = {
    "ordinary": (
        (20.0, 1.00, 1.00),
        (250.0, 1.00, 1.00),
        (300.0, 0.94, 0.84),
        (350.0, 0.89, 0.78),
        (400.0, 0.84, 0.72),
        (450.0, 0.79, 0.67),
        (500.0, 0.73, 0.61),
        (550.0, 0.67, 0.54),
        (600.0, 0.59, 0.45),
        (650.0, 0.52, 0.34),
        (700.0, 0.43, 0.20),
    ),
    "increased": (
        (20.0, 1.00, 1.00),
        (250.0, 1.00, 1.00),
        (300.0, 0.96, 0.84),
        (350.0, 0.92, 0.75),
        (400.0, 0.88, 0.70),
        (450.0, 0.85, 0.65),
        (500.0, 0.81, 0.60),
        (550.0, 0.75, 0.55),
        (600.0, 0.66, 0.46),
        (650.0, 0.53, 0.34),
        (700.0, 0.35, 0.18),
    ),
    "high": (
        (20.0, 1.00, 1.00),
        (250.0, 1.00, 1.00),
        (300.0, 0.95, 0.89),
        (350.0, 0.90, 0.83),
        (400.0, 0.86, 0.79),
        (450.0, 0.82, 0.75),
        (500.0, 0.78, 0.71),
        (550.0, 0.73, 0.66),
        (600.0, 0.68, 0.58),
        (650.0, 0.62, 0.47),
        (700.0, 0.54, 0.32),
    ),
    "fire_resistant": (
        (20.0, 1.00, 1.00),
        (250.0, 1.00, 1.00),
        (300.0, 0.96, 0.96),
        (350.0, 0.93, 0.95),
        (400.0, 0.90, 0.92),
        (450.0, 0.86, 0.89),
        (500.0, 0.82, 0.83),
        (550.0, 0.77, 0.76),
        (600.0, 0.71, 0.68),
        (650.0, 0.65, 0.58),
        (700.0, 0.58, 0.47),
        (750.0, 0.50, 0.33),
        (800.0, 0.42, 0.20),
        (850.0, 0.33, 0.02),
    ),
}


def install() -> None:
    """Install the complete published table as the active FIRE-D2 dataset."""
    _runtime._B1 = {
        group: tuple(tuple(float(value) for value in row) for row in rows)
        for group, rows in FINAL_B1.items()
    }
    _runtime._v091_b1_published_final_installed = True
    _runtime._v091_b1_normative_basis = (
        "SP 554.1311500.2026 Appendix B, Table B.1 (published final)"
    )


__all__ = ["FINAL_B1", "install"]
