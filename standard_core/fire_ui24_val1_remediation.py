"""FIRE-UI2.4 FIRE-VAL1 guided-routing remediation.

This stage does not introduce new normative formula executors.  It freezes the
v0.3.60 graph/presentation remediation over the cumulative FIRE-UI2.3 registry.
"""
from __future__ import annotations

from .fire_ui0 import ExecutionRegistry
from .fire_ui23_protection_route import build_fire_ui23_registry
from .profile_catalog import InterimProfileCatalog


def build_fire_ui24_registry(catalog: InterimProfileCatalog, registry: ExecutionRegistry | None = None) -> ExecutionRegistry:
    """
    Summary:
        Build the cumulative FIRE-UI2.4 executor registry after FIRE-VAL1 routing remediation.

    Standard reference:
        Standard: SP 16.13330.2017 and SP 554.1311500.2026
        Version: package-authoritative locked editions
        Clause: SP16 4.3.2, 8.2.2; SP554 8.6-8.7 and downstream Appendix-B critical-temperature routing
        Annex: SP554 Appendix B
        Equation/Table: SP16 Table 1 and Eq. (47); SP554 Eqs. (8.3)-(8.4), clause 8.7
        Audit ID: FIRE-UI24-VAL1-REMEDIATION
        Normative status: implementation_binding

    Parameters:
        catalog:
            Type: InterimProfileCatalog
            Unit: not applicable
            Meaning: Profile catalog used by the cumulative guided-calculation registry.
            Valid range: Initialized catalog instance.
            Source: package profile catalog.
        registry:
            Type: ExecutionRegistry | None
            Unit: not applicable
            Meaning: Optional registry to extend.
            Valid range: None or valid registry instance.
            Source: application composition.

    Returns:
        Type: ExecutionRegistry
        Unit: not applicable
        Meaning: Cumulative registry inherited from FIRE-UI2.3.

    Assumptions:
        - FIRE-UI2.4 changes routing/authoring semantics only; formula executors are inherited unchanged.

    Sign convention:
        - Inherited from the cumulative signed-load policy.

    Unit convention:
        - Inherited from the frozen DAG quantities.

    Applicability:
        - Guided calculations using DAG v0.3.60.

    Limitations:
        - General Qy and torsion T remain outside production runtime and remain locked/fail-closed.

    Raises:
        TypeError: If the cumulative parent registry receives incompatible inputs.

    Examples:
        >>> reg = build_fire_ui24_registry(InterimProfileCatalog())
        >>> isinstance(reg, ExecutionRegistry)
        True

    Tests:
        Unit tests:
            - tests/test_fire_ui24_val1_remediation.py
            - tests/test_docstrings.py::test_public_api_docstrings

    Implementation notes:
        - No executor is overridden in this stage; the graph and presentation policy carry the remediation.
    """
    return build_fire_ui23_registry(catalog, registry)
