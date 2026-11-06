from pathlib import Path

from req_reviewer.evaluation import (
    build_markdown,
    load_cases,
    run_eval,
    score_case,
    summarize,
    topic_matches,
)
from req_reviewer.llm import LLMError

CASE = {
    "id": "T1",
    "title": "Пароль",
    "text": "Пароль от 8 до 20",
    "expected": [
        {"topic": "пробелы", "keywords": ["пробел"]},
        {"topic": "пустое", "keywords": ["пуст"]},
    ],
}


class FakeClient:
    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error

    def chat(self, system, user):
        if self.error:
            raise self.error
        return self.answer


def test_topic_matches_ignores_case():
    assert topic_matches("Допустимы ли ПРОБЕЛЫ?", ["пробел"])
    assert not topic_matches("Другой вопрос", ["пробел"])


def test_score_case_found_and_missed():
    r = score_case(CASE, ["Можно ли пробелы?", "Какой цвет кнопки?"])
    assert r.found == ["пробелы"]
    assert r.missed == ["пустое"]
    assert r.relevant == 1


def test_run_eval_scores_cases():
    client = FakeClient("1. Можно ли пробелы?\n2. Что с пустым значением?")
    results = run_eval([CASE], client)
    assert results[0].found == ["пробелы", "пустое"]
    assert results[0].missed == []


def test_run_eval_survives_llm_error():
    results = run_eval([CASE], FakeClient(error=LLMError("нет связи")))
    assert results[0].error == "нет связи"


def test_summarize_counts():
    results = run_eval([CASE], FakeClient("1. Можно ли пробелы?"))
    s = summarize(results)
    assert (s["found"], s["expected"]) == (1, 2)
    assert s["recall"] == 0.5
    assert s["precision"] == 1.0


def test_summarize_ignores_failed_cases():
    results = run_eval([CASE], FakeClient(error=LLMError("x")))
    s = summarize(results)
    assert s["expected"] == 0 and s["recall"] == 0.0 and s["cases_failed"] == 1


def test_markdown_contains_totals():
    results = run_eval([CASE], FakeClient("1. Можно ли пробелы?"))
    md = build_markdown(results, "gemma3:4b")
    assert "gemma3:4b" in md and "1 из 2" in md


def test_dataset_is_valid():
    path = Path(__file__).resolve().parent.parent / "eval" / "cases.json"
    cases = load_cases(path)
    assert len(cases) >= 10
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))
    for c in cases:
        assert c["title"] and c["text"] and c["expected"]
        for t in c["expected"]:
            assert t["topic"] and t["keywords"]