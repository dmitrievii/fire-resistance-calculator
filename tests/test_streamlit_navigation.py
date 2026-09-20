from __future__ import annotations

from streamlit_navigation import history_rows, previous_answered_node_id


def _env():
    return {
        "state": {
            "interaction_history": [
                {"node_id": "Q1", "payload": 1, "provenance": None},
                {"node_id": "Q2", "payload": 2, "provenance": None},
                {"node_id": "Q3", "payload": 3, "provenance": None},
            ]
        }
    }


def _cards():
    return {
        "Q1": {"title": "Первый вопрос", "owner_standard_id": "SP16", "presentation": {"stage": "Исходные данные"}},
        "Q2": {"title": "Второй вопрос", "owner_standard_id": "SP16", "presentation": {"stage": "Сечение"}},
        "Q3": {"title": "Третий вопрос", "owner_standard_id": "SP554", "presentation": {"stage": "Огнестойкость"}},
    }


def test_history_rows_keep_guided_interaction_order_and_stage_labels():
    rows = history_rows(_env(), _cards())
    assert [row["node_id"] for row in rows] == ["Q1", "Q2", "Q3"]
    assert [row["step_number"] for row in rows] == [1, 2, 3]
    assert rows[1]["title"] == "Второй вопрос"
    assert rows[1]["stage"] == "Сечение"


def test_back_from_current_question_opens_last_answered_question():
    assert previous_answered_node_id(_env(), _cards()) == "Q3"


def test_back_while_editing_moves_to_previous_answered_question():
    assert previous_answered_node_id(_env(), _cards(), "Q3") == "Q2"
    assert previous_answered_node_id(_env(), _cards(), "Q2") == "Q1"


def test_back_at_first_answer_stays_on_first_answer_instead_of_inventing_route():
    assert previous_answered_node_id(_env(), _cards(), "Q1") == "Q1"
