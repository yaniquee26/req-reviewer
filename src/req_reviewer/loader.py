from pathlib import Path


def load_requirements(path: str) -> str:
    """Читает файл с требованиями и возвращает текст."""
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")
    text = file.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Файл пустой")
    return text