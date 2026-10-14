"""Phone number canonicalization and normalization utilities."""

from __future__ import annotations

import re

_PERSIAN_ARABIC_DIGIT_MAP = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)


def normalize_phone(phone: str | None) -> str:
    """Normalize phone number to canonical E.164-compatible format (+98...).

    Handles:
    - Persian digits (۰-۹) and Arabic digits (٠-٩)
    - Formatting characters (spaces, hyphens, parentheses, dots)
    - Iranian mobile: 0912..., 912..., 0098912..., +98912... -> +98912...
    - Generic international: numbers starting with +
    """
    if not phone:
        return ""

    cleaned = str(phone).translate(_PERSIAN_ARABIC_DIGIT_MAP).strip()
    cleaned = re.sub(r"[\s\-\(\)\.]+", "", cleaned)

    if cleaned.startswith("00989") and len(cleaned) == 14:
        return f"+98{cleaned[4:]}"
    if cleaned.startswith("09") and len(cleaned) == 11:
        return f"+98{cleaned[1:]}"
    if cleaned.startswith("9") and len(cleaned) == 10:
        return f"+98{cleaned}"
    if cleaned.startswith("+989") and len(cleaned) == 13:
        return cleaned

    return cleaned
