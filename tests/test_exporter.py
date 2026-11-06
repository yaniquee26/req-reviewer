import csv

from openpyxl import load_workbook

from req_reviewer.exporter import build_report, save_outputs
from req_reviewer.rules import extract_length_rule, generate_values

TEXT = "Пароль: от 8 до 20 символов."


def _data():
    return extract_length_rule(TEXT), generate_values(TEXT)


def test_report_contains_table_and_questions():
    rule, values = _data()
    report = build_report("req.md", TEXT, rule, values, ["Можно ли пробелы?"])
    assert "| 1 | (пусто) | 0 |" in report
    assert "1. Можно ли пробелы?" in report
    assert "гипотезы" in report


def test_report_without_model():
    rule, values = _data()
    report = build_report("req.md", TEXT, rule, values, None)
    assert "Модель не использовалась" in report


def test_report_no_ambiguities():
    rule, values = _data()
    report = build_report("req.md", TEXT, rule, values, [])
    assert "Неясностей не найдено" in report


def test_save_outputs_creates_files(tmp_path):
    rule, values = _data()
    report, table, xlsx = save_outputs(
        str(tmp_path / "out"), "req.md", TEXT, rule, values, None
    )
    assert report.exists() and table.exists() and xlsx.exists()


def test_csv_rows_match_values(tmp_path):
    rule, values = _data()
    _, table, _ = save_outputs(str(tmp_path), "req.md", TEXT, rule, values, None)
    with open(table, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    assert rows[0][0] == "ID"
    assert len(rows) == len(values) + 1
    assert rows[1][0] == "TC-001"


def test_xlsx_has_header_and_rows(tmp_path):
    rule, values = _data()
    _, _, xlsx = save_outputs(str(tmp_path), "req.md", TEXT, rule, values, None)
    ws = load_workbook(xlsx).active
    assert ws["A1"].value == "ID"
    assert ws.max_row == len(values) + 1
    assert ws["C2"].value == "(пусто)"