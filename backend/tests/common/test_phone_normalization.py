"""Tests for phone normalization utility."""

import pytest
from common.phone import normalize_phone


@pytest.mark.parametrize(
    "input_val,expected",
    [
        ("09121234567", "+989121234567"),
        ("9121234567", "+989121234567"),
        ("+989121234567", "+989121234567"),
        ("00989121234567", "+989121234567"),
        ("۰۹۱۲۱۲۳۴۵۶۷", "+989121234567"),
        ("٠٩١٢١٢٣٤٥٦٧", "+989121234567"),
        ("0912 123 4567", "+989121234567"),
        ("0912-123-4567", "+989121234567"),
        ("(0912) 123 4567", "+989121234567"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_phone_iranian_variations(input_val, expected):
    assert normalize_phone(input_val) == expected
