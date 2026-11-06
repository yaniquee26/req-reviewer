import argparse
import sys

from req_reviewer.exporter import save_outputs
from req_reviewer.llm import LLMError, OllamaClient
from req_reviewer.loader import load_requirements
from req_reviewer.reviewer import find_ambiguities
from req_reviewer.rules import extract_length_rule, generate_values


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="req-reviewer",
        description="Анализ требований: неясности и тест-кейсы",
    )
    parser.add_argument("file", help="путь к файлу с требованиями (.md или .txt)")
    parser.add_argument("--model", default="gemma3:4b", help="модель Ollama")
    parser.add_argument(
        "--no-llm", action="store_true", help="только правила из кода, без модели"
    )
    parser.add_argument(
        "--out", help="папка, куда сохранить report.md, testcases.csv и testcases.xlsx"
    )
    args = parser.parse_args(argv)

    try:
        text = load_requirements(args.file)
    except (FileNotFoundError, ValueError) as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        return 1

    print(f"Загружено символов: {len(text)}")
    print(text)

    rule = extract_length_rule(text)
    values = generate_values(text)
    print(f"\nПравило длины: min={rule.min_len}, max={rule.max_len}")
    print("Тестовые значения (граничные):")
    for tv in values:
        print(f"  [{tv.expected:6}] {tv.note:10} -> {tv.value!r}")

    questions = None
    if not args.no_llm:
        print("\nВопросы к аналитику (гипотезы модели, проверь сам):")
        try:
            questions = find_ambiguities(text, OllamaClient(model=args.model))
        except LLMError as err:
            print(f"  Модель недоступна: {err}", file=sys.stderr)
        else:
            if not questions:
                print("  Неясностей не найдено.")
            for i, q in enumerate(questions, 1):
                print(f"  {i}. {q}")

    if args.out:
        report, table, xlsx = save_outputs(
            args.out, args.file, text, rule, values, questions
        )
        print(f"\nСохранено: {report}, {table}, {xlsx}")
    return 0


if __name__ == "__main__":
    sys.exit(main())