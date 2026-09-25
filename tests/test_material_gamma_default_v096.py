from standard_core.material_gamma_default_v096 import resolve_annex_v_design_strengths


def test_c255b_annex_default_reproduces_tabulated_values():
    r = resolve_annex_v_design_strengths(
        Ryn_MPa=255.0, Run_MPa=380.0,
        Ry_tabulated_MPa=250.0, Ru_tabulated_MPa=370.0,
    )
    assert r["gamma_m"] == 1.025
    assert r["material_safety_category"] == "statistical_control"
    assert r["Ry_formula_MPa"] == 250.0
    assert r["Ru_formula_MPa"] == 370.0
    assert r["annex_default_matches"] is True


def test_c355b_annex_default_reproduces_tabulated_values():
    r = resolve_annex_v_design_strengths(
        Ryn_MPa=355.0, Run_MPa=470.0,
        Ry_tabulated_MPa=345.0, Ru_tabulated_MPa=460.0,
    )
    assert r["gamma_m"] == 1.025
    assert r["Ry_formula_MPa"] == 345.0
    assert r["Ru_formula_MPa"] == 460.0


def test_explicit_table3_category_recomputes_from_normative_strengths():
    r = resolve_annex_v_design_strengths(
        Ryn_MPa=355.0, Run_MPa=470.0,
        Ry_tabulated_MPa=345.0, Ru_tabulated_MPa=460.0,
        gamma_m_category="other_conforming",
    )
    assert r["gamma_m"] == 1.05
    assert r["gamma_m_is_annex_default"] is False
    assert r["Ry_formula_MPa"] == 340.0
    assert r["Ru_formula_MPa"] == 450.0
