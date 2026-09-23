import pytest

from standard_core import fire_sp554_runtime as runtime


PUBLISHED_B1 = {
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


def test_complete_published_appendix_b1_is_active():
    assert set(runtime._B1) == set(PUBLISHED_B1)
    for group, expected_rows in PUBLISHED_B1.items():
        actual_rows = runtime._B1[group]
        assert len(actual_rows) == len(expected_rows)
        for actual, expected in zip(actual_rows, expected_rows):
            assert actual == pytest.approx(expected)


def test_every_published_knot_roundtrips_through_forward_lookup():
    for group, rows in PUBLISHED_B1.items():
        for temperature, gamma_e, gamma_t in rows:
            assert runtime._forward_b1(group, "gamma_E", temperature) == pytest.approx(gamma_e)
            assert runtime._forward_b1(group, "gamma_T", temperature) == pytest.approx(gamma_t)


def test_published_column_order_is_modulus_then_strength():
    # Explicit guard against swapping gamma_E and gamma_T in Table B.1.
    assert runtime._forward_b1("high", "gamma_E", 300.0) == pytest.approx(0.95)
    assert runtime._forward_b1("high", "gamma_T", 300.0) == pytest.approx(0.89)
    assert runtime._forward_b1("increased", "gamma_E", 450.0) == pytest.approx(0.85)
    assert runtime._forward_b1("increased", "gamma_T", 450.0) == pytest.approx(0.65)
