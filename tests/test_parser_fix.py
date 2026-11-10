from req_reviewer.reviewer import PROMPTS, parse_questions


def test_no_item_is_not_a_question():
    assert parse_questions("1. Можно ли пробелы?\n2. НЕТ") == ["Можно ли пробелы?"]


def test_no_item_with_dot_is_skipped():
    assert parse_questions("1. Нет.") == []


def test_v3_asks_to_classify_requirement():
    text = PROMPTS["v3"]
    assert "бизнес-процесс" in text
    assert "вывод данных" in text