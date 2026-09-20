import math

import pytest

from standard_core.bolted_and_friction_connections import friction_connection_working_factor_14_3_4
from standard_core.effective_lengths_and_limiting_slenderness import (
    table_24_catalog,
    table_25_catalog,
    table_26_catalog,
    table_27_catalog,
    table_28_catalog,
    table_29_catalog,
    table_30_catalog,
    table_31_catalog,
    table_32_catalog,
    table_33_catalog,
    group_4_limiting_slenderness_increase,
)
from standard_core.sheet_structures_strength_and_stability import (
    principal_stresses_2d,
    tube_bending_critical_stress_clause_11_2_2,
)


def test_previously_indirect_public_functions_have_explicit_function_level_tests():
    # Clause 14.3.4 piecewise boundaries.
    assert friction_connection_working_factor_14_3_4(4) == 0.8
    assert friction_connection_working_factor_14_3_4(5) == 0.9
    assert friction_connection_working_factor_14_3_4(10) == 1.0

    # Tables 24-33 must each remain materialized, structured dictionaries.
    catalogs = [
        table_24_catalog(), table_25_catalog(), table_26_catalog(), table_27_catalog(), table_28_catalog(),
        table_29_catalog(), table_30_catalog(), table_31_catalog(), table_32_catalog(), table_33_catalog(),
    ]
    assert all(isinstance(item, dict) and item for item in catalogs)

    # Clause 10.4.2 explicit 10% route.
    assert group_4_limiting_slenderness_increase(100.0, False) == 100.0
    assert group_4_limiting_slenderness_increase(100.0, True) == pytest.approx(110.0)

    # Independent closed-form principal-stress identity.
    s1, s2 = principal_stresses_2d(100.0, 40.0, 30.0)
    mean = 70.0
    radius = math.sqrt(30.0**2 + 30.0**2)
    assert s1 == mean + radius
    assert s2 == mean - radius

    # Clause 11.2.2 definition after equation (156).
    expected = 240.0 / 8.0 * (9.0 - (1.0 - 2.0) / (1.0 + 2.0))
    assert tube_bending_critical_stress_clause_11_2_2(240.0, 2.0) == expected
