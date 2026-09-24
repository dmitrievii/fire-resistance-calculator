from __future__ import annotations

from standard_core.sp16_mech7_v078_gamma_c import (
    OUTPUT_QID,
    compression_case_options,
    resolve_gamma_c_compression,
)
from streamlit_mech9_v090 import (
    _gamma_c_option_label,
    _render_gamma_c_compact,
)


NOTE5 = "default_unlisted_case_note_5"


class _FakeStreamlit:
    def __init__(self, selected: str | None) -> None:
        self.selected = selected
        self.selectbox_calls: list[dict] = []
        self.caption_calls: list[str] = []

    def selectbox(self, label, options, **kwargs):
        options = list(options)
        self.selectbox_calls.append(
            {
                "label": label,
                "options": options,
                "index": kwargs.get("index"),
                "placeholder": kwargs.get("placeholder"),
                "format_func": kwargs.get("format_func"),
                "key": kwargs.get("key"),
            }
        )
        return self.selected

    def caption(self, text):
        self.caption_calls.append(str(text))


class _FakeCore:
    def __init__(self, selected: str | None) -> None:
        self.fake_st = _FakeStreamlit(selected)

    def _st(self):
        return self.fake_st

    @staticmethod
    def _key(*parts):
        return ":".join(str(part) for part in parts)


def _card() -> dict:
    return {
        "node_id": "SP16_I_V078_GAMMA_C_COMPRESSION_CASE",
        "presentation": {
            "component": "sp16_table1_gamma_c_compression",
            "options": compression_case_options(),
        },
    }


def test_note5_label_is_self_contained_and_occurs_once_in_selector_option():
    option = next(row for row in compression_case_options() if row["value"] == NOTE5)
    label = _gamma_c_option_label(option)

    assert label == "Случай не указан в таблице 1 — γc = 1,00 по примечанию 5"
    assert label.count("γc") == 1
    assert label.count("примечанию 5") == 1


def test_regular_table1_option_has_position_description_and_gamma_without_extra_caption():
    option = next(
        row
        for row in compression_case_options()
        if row["value"] == "1_floor_beams_and_compressed_floor_truss_members"
    )
    label = _gamma_c_option_label(option)

    assert label.startswith("Таблица 1, поз. 1:")
    assert "Балки сплошного сечения" in label
    assert label.endswith("γc = 0,90")


def test_compact_renderer_is_one_selector_zero_captions_and_returns_exact_case_id():
    core = _FakeCore(NOTE5)
    selected, provenance, ready = _render_gamma_c_compact(
        core,
        _card(),
        None,
        "guided",
    )

    assert selected == NOTE5
    assert provenance is None
    assert ready is True
    assert len(core.fake_st.selectbox_calls) == 1
    assert core.fake_st.caption_calls == []

    call = core.fake_st.selectbox_calls[0]
    assert call["label"] == "Случай по таблице 1 СП 16"
    rendered = call["format_func"](NOTE5)
    assert rendered == "Случай не указан в таблице 1 — γc = 1,00 по примечанию 5"


def test_gamma_c_runtime_semantics_are_unchanged_and_note5_is_not_a_hidden_default():
    # UI still returns the classification ID. The qualified runtime remains the
    # sole owner of the numeric gamma_c lookup.
    assert resolve_gamma_c_compression(NOTE5)[OUTPUT_QID] == 1.0

    core = _FakeCore(None)
    selected, provenance, ready = _render_gamma_c_compact(
        core,
        _card(),
        None,
        "guided",
    )
    assert selected is None
    assert provenance is None
    assert ready is False
    assert core.fake_st.caption_calls == []
