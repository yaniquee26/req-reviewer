from req_reviewer.rules import (
    LengthRule,
    boundary_lengths,
    extract_length_rule,
    generate_values,
    make_value,
)

TEXT = "Пароль: от 8 до 20 символов, минимум одна цифра и одна заглавная буква."


def test_extracts_range():
    rule = extract_length_rule(TEXT)
    assert (rule.min_len, rule.max_len) == (8, 20)


def test_extracts_min_and_max_separately():
    rule = extract_length_rule("Минимум 6 символов, максимум 12 символов")
    assert (rule.min_len, rule.max_len) == (6, 12)


def test_no_rule_found():
    rule = extract_length_rule("Поле обязательно для заполнения")
    assert rule == LengthRule(None, None)


def test_digit_phrase_is_not_a_length_rule():
    # "минимум одна цифра" не должно считаться длиной
    assert extract_length_rule("минимум одна цифра").min_len is None


def test_boundary_lengths():
    assert boundary_lengths(LengthRule(8, 20)) == [0, 7, 8, 9, 19, 20, 21]


def test_make_value_has_required_classes():
    v = make_value(8, digit=True, upper=True)
    assert len(v) == 8 and any(c.isdigit() for c in v) and any(c.isupper() for c in v)


def test_generate_values_expectations():
    values = {len(v.value): v.expected for v in generate_values(TEXT)}
    assert values[7] == "reject"
    assert values[8] == "accept"
    assert values[20] == "accept"
    assert values[21] == "reject"