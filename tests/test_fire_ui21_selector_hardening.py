from __future__ import annotations

from pathlib import Path

from standard_core.fire_ui1_http import FireUI1Application
from standard_core.fire_ui13_material_strength import material_strength_catalog
from standard_core.material_resistance import SteelMaterialStrengthResolver
from standard_core.profile_catalog import InterimProfileCatalog

ROOT=Path(__file__).resolve().parents[1]


def _options_for(card, field):
    if field["data_type"] == "boolean":
        return field.get("enum_values") or []
    if card.get("node_type") == "decision" and card.get("options"):
        return card["options"]
    return field.get("enum_values") or []


def test_ui21_every_generic_enum_boolean_selector_has_nonempty_choices():
    app=FireUI1Application.from_package_root(ROOT)
    contract=app.model.build_ui_contract()
    audit=contract["selector_audit"]
    assert audit["status"]=="PASS"
    assert audit["empty_option_sets"]==0
    assert audit["generic_selector_fields"] > 100
    checked=0
    for card in contract["node_cards"]:
        for field in card.get("fields",[]):
            if field.get("data_type") not in {"enum","boolean"}:
                continue
            checked += 1
            opts=_options_for(card,field)
            assert opts, (card["node_id"],field["quantity_id"])
            assert all("value" in row for row in opts)
            assert all(str(row.get("label") or "").strip() for row in opts)
            assert len({repr(row["value"]) for row in opts})==len(opts)
    assert checked==audit["generic_selector_fields"]


def test_ui21_reported_boolean_fields_have_explicit_yes_no_contract_choices():
    app=FireUI1Application.from_package_root(ROOT)
    contract=app.model.build_ui_contract()
    wanted={"section_is_constant","moment_plane_is_symmetry"}
    found={}
    for card in contract["node_cards"]:
        for field in card.get("fields",[]):
            if field["quantity_id"] in wanted:
                found[field["quantity_id"]]=field
    assert set(found)==wanted
    for field in found.values():
        assert field["data_type"]=="boolean"
        assert field["enum_values"]==[{"value":True,"label":"Да"},{"value":False,"label":"Нет"}]


def test_ui21_frontend_boolean_fallback_precedes_enum_values_and_is_compiled():
    src=(ROOT/'fire_ui1_web/src/app.ts').read_text(encoding='utf-8')
    js=(ROOT/'fire_ui1_web/dist/app.js').read_text(encoding='utf-8')
    block=src[src.index('function optionSource'):src.index('function selectedValueForReview')]
    assert block.index('field.data_type === "boolean"') < block.index('field.enum_values')
    assert 'field.enum_values.length' in block
    assert 'field.data_type === "boolean"' in js


def test_ui21_qy_and_t_are_visible_but_fail_closed_in_mech2_primary_ui():
    app=FireUI1Application.from_package_root(ROOT)
    ambient=app.model.node_card('SP16_I_AMBIENT_LOADS')
    fire=app.model.node_card('SP554_H_SP20_LOADS')
    assert ambient['presentation']['component']=='ambient_signed_load_menu'
    assert fire['presentation']['component']=='fire_signed_load_menu'
    assert not ambient['presentation'].get('locked_quantities')
    assert not fire['presentation'].get('locked_quantities')
    src=(ROOT/'fire_ui1_web/src/app.ts').read_text(encoding='utf-8')
    assert 'Qy≠0 расчёт остановится fail-closed до SP16-MECH3' in src
    assert 'T≠0 расчёт остановится fail-closed до SP16-MECH4' in src
    assert 'renderAmbientSignedLoadMenu' in src and 'renderFireSignedLoadMenu' in src


def test_ui21_dynamic_select_data_sources_are_nonempty():
    catalog=InterimProfileCatalog()
    families=catalog.list_families()
    assert len(families)==37
    assert all(catalog.list_profiles(int(f['family_id'])) for f in families)
    mat=material_strength_catalog(SteelMaterialStrengthResolver())
    products=mat['products']
    assert products
    for product in products:
        assert product.get('grades'), product.get('value')
        for grade in product['grades']:
            assert grade.get('intervals'), (product.get('value'),grade.get('steel_grade'))


def test_ui21_nonzero_qy_t_runtime_guard_is_retained():
    app=FireUI1Application.from_package_root(ROOT)
    node=app.model.nodes['SP554_R_UI16_DEFERRED_BRANCHES']
    qids={c['quantity_id'] for c in node['applicability']['conditions']}
    assert qids=={'Q_y','T_torsion'}
    assert app.model.graph['metadata']['fire_ui21_qy_runtime_closed'] is False
    assert app.model.graph['metadata']['fire_ui21_torsion_runtime_closed'] is False
