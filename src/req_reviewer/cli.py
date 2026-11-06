import argparse
import sys

from req_reviewer.loader import load_requirements
from req_reviewer.rules import extract_length_rule, generate_values


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="req-reviewer",
        description="Анализ требований: неясности и тест-кейсы",
    )
    parser.add_argument("file", help="путь к файлу с требованиями (.md или .txt)")
    args = parser.parse_args(argv)

    try:
        text = load_requirements(args.file)
    except (FileNotFoundError, ValueError) as err:
        print(f"Ошибка: {err}", file=sys.stderr)
        return 1

    print(f"Загружено символов: {len(text)}")
    print(text)

    rule = extract_length_rule(text)
    print(f"Правило длины: min={rule.min_len}, max={rule.max_len}")
    print("Тестовые значения (граничные):")
    for tv in generate_values(text):
        print(f"  [{tv.expected:6}] {tv.note:10} -> {tv.value!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())