"""FIRE-UI2.1 selector hardening and primary-UI unsupported-action lock.

No new normative mechanics are introduced here.  The executable registry is
identical to FIRE-UI2.0; this layer exists to version the UI/contract hardening
without misrepresenting Qy or torsion T as implemented calculation routes.
"""
from __future__ import annotations

from .fire_ui0 import ExecutionRegistry
from .fire_ui20_remediation import build_fire_ui20_registry
from .profile_catalog import InterimProfileCatalog


def build_fire_ui21_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative FIRE-UI2.1 executor registry over the verified FIRE-UI2.0 runtime.

    Standard reference:
        Presentation/runtime integration only. Normative mechanics remain those already bound by SP16/SP554/GOST executors in FIRE-UI2.0.

    Parameters:
        catalog: Frozen interim section-profile catalog inherited by earlier FIRE-UI registry layers.
        registry: Optional registry to extend in place.

    Returns:
        ExecutionRegistry with the complete inherited FIRE-UI2.0 executor set.

    Assumptions:
        The active package uses DAG v0.3.57 and the FIRE-UI2.1 presentation policy.

    Sign convention:
        Unchanged from FIRE-UI2.0; signed mechanical actions remain algebraic quantities.

    Unit convention:
        Unchanged from the inherited executor registry.

    Applicability:
        FIRE-UI2.1 guided browser workflow.

    Limitations:
        No new Qy or torsion-T mechanics are introduced. Nonzero external values remain fail-closed.

    Raises:
        Propagates errors raised by the inherited registry builder.

    Examples:
        ``registry = build_fire_ui21_registry(InterimProfileCatalog())``.

    Tests:
        ``tests/test_fire_ui21_selector_hardening.py`` and cumulative FIRE-UI regression suites.

    Implementation notes:
        The wrapper deliberately delegates to FIRE-UI2.0 so UI hardening cannot be mistaken for normative runtime closure.
    """
    return build_fire_ui20_registry(catalog, registry)
