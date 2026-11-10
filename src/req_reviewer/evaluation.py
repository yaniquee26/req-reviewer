import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from req_reviewer.llm import LLMError, OllamaClient
from req_reviewer.reviewer import find_ambiguities


@dataclass
class CaseResult:
    case_id: str
    title: str
    questions: list[str] = field(default_factory=list)
    found: list[str] = field(default_factory=list)
    missed: list[str] = field(default_factory=list)
    relevant: int = 0
    error: str | None = None


def load_cases(path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def topic_matches(question: str, keywords: list[str]) -> bool:
    q = question.lower()
    return any(k.lower() in q for k in keywords)


def score_case(case: dict, questions: list[str]) -> CaseResult:
    found, missed = [], []
    for topic in case["expected"]:
        if any(topic_matches(q, topic["keywords"]) for q in questions):
            found.append(topic["topic"])
        else:
            missed.append(topic["topic"])
    all_keywords = [k for t in case["expected"] for k in t["keywords"]]
    relevant = sum(1 for q in questions if topic_matches(q, all_keywords))
    return CaseResult(
        case_id=case["id"],
        title=case["title"],
        questions=questions,
        found=found,
        missed=missed,
        relevant=relevant,
    )


def run_eval(
    cases: list[dict], client, progress=None, prompt: str = "v1"
) -> list[CaseResult]:
    results = []
    for i, case in enumerate(cases, 1):
        if progress:
            progress(f"[{i}/{len(cases)}] {case['id']} {case['title']}")
        try:
            questions = find_ambiguities(case["text"], client, prompt)
        except LLMError as err:
            results.append(CaseResult(case["id"], case["title"], error=str(err)))
            continue
        results.append(score_case(case, questions))
    return results


def summarize(results: list[CaseResult]) -> dict:
    ok = [r for r in results if r.error is None]
    found = sum(len(r.found) for r in ok)
    expected = found + sum(len(r.missed) for r in ok)
    questions = sum(len(r.questions) for r in ok)
    relevant = sum(r.relevant for r in ok)
    return {
        "cases_ok": len(ok),
        "cases_failed": len(results) - len(ok),
        "found": found,
        "expected": expected,
        "recall": found / expected if expected else 0.0,
        "questions": questions,
        "relevant": relevant,
        "precision": relevant / questions if questions else 0.0,
    }


def build_markdown(results: list[CaseResult], model: str, prompt: str = "v1") -> str:
    s = summarize(results)
    lines = [
        "# Оценка качества поиска неясностей",
        "",
        f"Модель: `{model}`, подсказка: {prompt}. Кейсов обработано: {s['cases_ok']}, с ошибкой: {s['cases_failed']}.",
        "",
        "| Кейс | Найдено тем | Вопросов | По теме | Пропущено |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        if r.error:
            lines.append(f"| {r.case_id} {r.title} | ошибка | - | - | {r.error} |")
            continue
        total = len(r.found) + len(r.missed)
        missed = ", ".join(r.missed) if r.missed else "-"
        lines.append(
            f"| {r.case_id} {r.title} | {len(r.found)} из {total} "
            f"| {len(r.questions)} | {r.relevant} | {missed} |"
        )
    lines += [
        "",
        "## Итого",
        "",
        f"- Полнота: модель нашла {s['found']} из {s['expected']} эталонных тем ({s['recall']:.0%}).",
        f"- Доля вопросов по эталонным темам: {s['relevant']} из {s['questions']} ({s['precision']:.0%}).",
        "",
        "## Как читать результат",
        "",
        "- Эталонные темы записаны вручную в `eval/cases.json`. Это мнение автора, а не истина.",
        "- Вопрос засчитывается, если в нём есть одно из ключевых слов темы. Метод грубый.",
        "- Вопрос вне списка тем не обязательно плохой. Поэтому вторая цифра нижняя оценка.",
        "- Модель отвечает чуть по-разному при каждом запуске, поэтому цифры могут колебаться.",
        "",
    ]
    return "\n".join(lines)

def build_details(results: list[CaseResult]) -> str:
    lines = ["", "## Что спросила модель", ""]
    for r in results:
        lines.append(f"### {r.case_id} {r.title}")
        lines.append("")
        if r.error:
            lines.append(f"Ошибка: {r.error}")
        elif not r.questions:
            lines.append("Вопросов нет.")
        else:
            for i, q in enumerate(r.questions, 1):
                lines.append(f"{i}. {q}")
        lines.append("")
    return "\n".join(lines)

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="req-reviewer-eval")
    parser.add_argument("--cases", default="eval/cases.json")
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--prompt", default="v1", choices=["v1", "v2", "v3"])
    parser.add_argument("--out", default="eval/results.md")
    args = parser.parse_args(argv)

    cases = load_cases(args.cases)
    client = OllamaClient(model=args.model, temperature=0.0, seed=42)
    results = run_eval(cases, client, progress=print, prompt=args.prompt)

    s = summarize(results)
    if s["cases_ok"] == 0:
        print("Ни один кейс не обработан. Запущена ли Ollama?", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        build_markdown(results, args.model, args.prompt) + build_details(results),
        encoding="utf-8",
    )    
    print(f"\nПолнота: {s['found']} из {s['expected']} ({s['recall']:.0%})")
    print(f"Вопросов по теме: {s['relevant']} из {s['questions']} ({s['precision']:.0%})")
    print(f"Сохранено: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())