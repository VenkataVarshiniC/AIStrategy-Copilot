from app.core.confidence_utils import average_confidence, parse_confidence


def test_parse_confidence_clean_float():
    assert parse_confidence(0.72) == 0.72


def test_parse_confidence_percent_scale_int():
    # Local models sometimes ignore the "0.0-1.0" instruction and return 0-100
    assert parse_confidence(70) == 0.7


def test_parse_confidence_string_decimal():
    assert parse_confidence("0.8") == 0.8


def test_parse_confidence_string_with_percent_sign():
    assert parse_confidence("70%") == 0.7


def test_parse_confidence_word_scale():
    assert parse_confidence("high") == 0.75
    assert parse_confidence("Low") == 0.3


def test_parse_confidence_none_uses_default():
    assert parse_confidence(None, default=0.4) == 0.4


def test_parse_confidence_garbage_uses_default():
    assert parse_confidence("not a number", default=0.35) == 0.35


def test_parse_confidence_clamps_above_one():
    assert parse_confidence(1.5) == 1.0


def test_parse_confidence_clamps_negative():
    assert parse_confidence(-0.2, default=0.4) == 0.4


def test_average_confidence_basic():
    assert average_confidence([0.6, 0.8, 0.4]) == 0.6


def test_average_confidence_empty_uses_default():
    assert average_confidence([], default=0.42) == 0.42
