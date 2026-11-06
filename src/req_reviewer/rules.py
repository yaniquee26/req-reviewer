import re
from dataclasses import dataclass


@dataclass
class LengthRule:
    min_len: int | None = None
    max_len: int | None = None


@dataclass
class TestValue:
    value: str
    expected: str  # "accept" или "reject"
    technique: str  # "boundary" или "equivalence"
    note: str


_RANGE = re.compile(
    r"(?:от|from)\s+(\d+)\s+(?:до|to)\s+(\d+)\s+(?:символ\w*|char\w*)",
    re.IGNORECASE,
)
_MIN = re.compile(
    r"(?:минимум|не менее|at least)\s+(\d+)\s+(?:символ\w*|char\w*)",
    re.IGNORECASE,
)
_MAX = re.compile(
    r"(?:максимум|не более|at most)\s+(\d+)\s+(?:символ\w*|char\w*)",
    re.IGNORECASE,
)


def extract_length_rule(text: str) -> LengthRule:
    """Ищет в тексте ограничения длины."""
    rule = LengthRule()
    m = _RANGE.search(text)
    if m:
        rule.min_len, rule.max_len = int(m.group(1)), int(m.group(2))
        return rule
    m = _MIN.search(text)
    if m:
        rule.min_len = int(m.group(1))
    m = _MAX.search(text)
    if m:
        rule.max_len = int(m.group(1))
    return rule


def needs_digit(text: str) -> bool:
    return bool(re.search(r"цифр|digit", text, re.IGNORECASE))


def needs_upper(text: str) -> bool:
    return bool(re.search(r"заглавн|uppercase|capital", text, re.IGNORECASE))


def make_value(length: int, digit: bool, upper: bool) -> str:
    """Строка заданной длины, которая выполняет требования к составу."""
    chars = []
    if upper:
        chars.append("A")
    if digit:
        chars.append("1")
    chars += ["a"] * max(0, length - len(chars))
    return "".join(chars)[:length]


def boundary_lengths(rule: LengthRule) -> list[int]:
    """Граничные значения: min-1, min, min+1, max-1, max, max+1."""
    lengths = {0}
    if rule.min_len is not None:
        lengths |= {rule.min_len - 1, rule.min_len, rule.min_len + 1}
    if rule.max_len is not None:
        lengths |= {rule.max_len - 1, rule.max_len, rule.max_len + 1}
    return sorted(n for n in lengths if n >= 0)


def is_length_valid(n: int, rule: LengthRule) -> bool:
    if rule.min_len is not None and n < rule.min_len:
        return False
    if rule.max_len is not None and n > rule.max_len:
        return False
    return True


def generate_values(text: str) -> list[TestValue]:
    rule = extract_length_rule(text)
    digit, upper = needs_digit(text), needs_upper(text)
    result = []
    for n in boundary_lengths(rule):
        ok = is_length_valid(n, rule)
        result.append(
            TestValue(
                value=make_value(n, digit, upper),
                expected="accept" if ok else "reject",
                technique="boundary",
                note=f"длина {n}",
            )
        )
    return result