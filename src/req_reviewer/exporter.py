import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from req_reviewer.rules import LengthRule, TestValue

EXPECTED_RU = {
    "accept": "Значение принято",
    "reject": "Значение отклонено, показано сообщение об ошибке",
}

HEADERS = [
    "ID", "Название", "Входные данные", "Ожидаемый результат",
    "Техника", "Источник", "Статус",
]
WIDTHS = [10, 38, 32, 50, 22, 30, 14]


def _show(value: str) -> str:
    return f"`{value}`" if value else "(пусто)"


def build_report(
    source: str,
    text: str,
    rule: LengthRule,
    values: list[TestValue],
    questions: list[str] | None,
) -> str:
    lines = [f"# Отчёт по требованиям: {source}", "", "## Исходный текст", ""]
    lines += [f"> {line}" for line in text.splitlines()]
    lines += [
        "",
        "## Найденное правило длины",
        "",
        f"- минимум: {rule.min_len}",
        f"- максимум: {rule.max_len}",
        "",
        "## Тестовые значения (граничные)",
        "",
        "| № | Значение | Длина | Ожидание |",
        "|---|---|---|---|",
    ]
    for i, tv in enumerate(values, 1):
        lines.append(
            f"| {i} | {_show(tv.value)} | {len(tv.value)} | {EXPECTED_RU[tv.expected]} |"
        )
    lines += ["", "## Вопросы к аналитику", ""]
    if questions is None:
        lines.append("Модель не использовалась или была недоступна.")
    else:
        lines.append("*Это гипотезы локальной модели, их нужно проверить вручную.*")
        lines.append("")
        if not questions:
            lines.append("Неясностей не найдено.")
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")
    lines.append("")
    return "\n".join(lines)


def _rows(source: str, values: list[TestValue], empty_label: str = ""):
    for i, tv in enumerate(values, 1):
        yield [
            f"TC-{i:03d}",
            f"Граничное значение: длина {len(tv.value)}",
            tv.value or empty_label,
            EXPECTED_RU[tv.expected],
            "Граничные значения",
            source,
            "Не выполнен",
        ]


def write_testcases_csv(source: str, values: list[TestValue], path: Path) -> None:
    # utf-8-sig, чтобы Excel правильно показал русские буквы
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(HEADERS)
        writer.writerows(_rows(source, values))


def write_testcases_xlsx(source: str, values: list[TestValue], path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Тест-кейсы"
    ws.append(HEADERS)
    for row in _rows(source, values, empty_label="(пусто)"):
        ws.append(row)

    header_fill = PatternFill("solid", fgColor="1F4E78")
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    for letter, width in zip("ABCDEFG", WIDTHS):
        ws.column_dimensions[letter].width = width
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(path)


def save_outputs(
    out_dir: str,
    source: str,
    text: str,
    rule: LengthRule,
    values: list[TestValue],
    questions: list[str] | None,
) -> tuple[Path, Path, Path]:
    folder = Path(out_dir)
    folder.mkdir(parents=True, exist_ok=True)
    report_path = folder / "report.md"
    csv_path = folder / "testcases.csv"
    xlsx_path = folder / "testcases.xlsx"
    report_path.write_text(
        build_report(source, text, rule, values, questions), encoding="utf-8"
    )
    write_testcases_csv(source, values, csv_path)
    write_testcases_xlsx(source, values, xlsx_path)
    return report_path, csv_path, xlsx_path