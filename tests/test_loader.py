import pytest

from req_reviewer.loader import load_requirements


def test_reads_file(tmp_path):
    f = tmp_path / "req.md"
    f.write_text("Пароль: от 8 до 20 символов", encoding="utf-8")
    assert load_requirements(str(f)) == "Пароль: от 8 до 20 символов"


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_requirements("nope.md")


def test_empty_file_raises(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("   \n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_requirements(str(f))