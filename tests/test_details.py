from req_reviewer.evaluation import build_details, run_eval

CASE = {
    "id": "T1",
    "title": "Пароль",
    "text": "Пароль от 8 до 20",
    "expected": [{"topic": "пробелы", "keywords": ["пробел"]}],
}


class FakeClient:
    def chat(self, system, user):
        return "1. Можно ли пробелы?\n2. Что с пустым значением?"


def test_details_lists_questions():
    results = run_eval([CASE], FakeClient())
    text = build_details(results)
    assert "Что спросила модель" in text
    assert "### T1 Пароль" in text
    assert "1. Можно ли пробелы?" in text
    assert "2. Что с пустым значением?" in text