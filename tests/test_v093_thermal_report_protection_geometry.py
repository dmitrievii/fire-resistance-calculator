from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_v093_protected_geometry_uses_executed_table1_evidence():
    src = (ROOT / "streamlit_protection_geometry_v093.py").read_text(encoding="utf-8")
    assert 'fire_protection_perimeter_mode' in src
    assert 'sp554_protected_table1_perimeter_trace' in src
    assert 'P_heated_protected' in src
    assert 'delta_pr_protected' in src
    assert 'P_prot = {formula}' in src
    assert 'δ_pr,prot = A / P_prot' in src
    # Item #18 is presentation of the qualified FIRE-UI1.9 runtime result, not
    # a duplicate implementation of Table-1 algebra.
    assert '4.0*B+2.0*D' not in src


def test_v093_thermal_report_has_reproducibility_inputs_and_terminal_result():
    src = (ROOT / "streamlit_expertise_report_v093_thermal_repro.py").read_text(encoding="utf-8")
    for token in (
        'gost30247_initial_furnace_temperature_c',
        'sp554_steel_density_12_2',
        'sp554_steel_c0_12_2',
        'sp554_steel_c_temp_coeff_12_2',
        'sp554_dt_unprotected_min',
        'P_heated_protected',
        'delta_pr_protected',
        'R_{fact}',
        'R_{req}',
        'Runtime-verdict',
    ):
        assert token in src
    assert 'не пересчитывает результат' in src


def test_v093_is_installed_after_v092_and_does_not_change_t0_ui_contract():
    app = (ROOT / "streamlit_app.py").read_text(encoding="utf-8")
    assert '_install_protection_geometry_v093(_core)' in app
    assert '_install_thermal_report_v093(_core)' in app
    assert app.index('_install_thermal_result_v092(_core)') < app.index('_install_protection_geometry_v093(_core)')
    assert app.index('_install_expertise_mech9(_core)') < app.index('_install_thermal_report_v093(_core)')

    # Audit item #17 is explicitly out of scope: v0.84 remains the owner of the
    # current T0 control/default and v0.93 introduces no T0 input widget.
    ui = (ROOT / "streamlit_protection_geometry_v093.py").read_text(encoding="utf-8")
    report = (ROOT / "streamlit_expertise_report_v093_thermal_repro.py").read_text(encoding="utf-8")
    assert 'number_input("Начальная температура' not in ui
    assert 'number_input("Начальная температура' not in report
