"""Helpers for extracting and validating spoken or scanned MRN values."""

import re
from typing import Optional


_DIGIT_WORDS = {
    "zero": "0",
    "oh": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}
_DIGIT_TOKEN = r"(?:\d|zero|oh|one|two|three|four|five|six|seven|eight|nine)"
_MRN_DECLARATION = re.compile(
    rf"\b(?:m\s*r\s*n|medical\s+record\s+number)(?:\b|(?=\d))\s*(?:is\s*)?"
    rf"(?P<value>\d{{4,}}|{_DIGIT_TOKEN}(?:[\s-]+{_DIGIT_TOKEN}){{3,}})",
    re.IGNORECASE,
)


def normalize_mrn(value: Optional[str]) -> Optional[str]:
    """Return a canonical ``MRN<digits>`` value for scanner/input text."""
    if not value:
        return None

    compact = re.sub(r"[\s:#-]+", "", value.strip().upper())
    match = re.fullmatch(r"(?:MRN|MEDICALRECORDNUMBER)?(\d{4,})", compact)
    if not match:
        return None
    return f"MRN{match.group(1)}"


def extract_spoken_mrn(transcript: str) -> Optional[str]:
    """Extract an MRN declared explicitly with digits or digit words."""
    match = _MRN_DECLARATION.search(transcript or "")
    if not match:
        return None

    tokens = re.findall(r"\d|" + "|".join(_DIGIT_WORDS), match.group("value"), re.IGNORECASE)
    digits = "".join(_DIGIT_WORDS.get(token.lower(), token) for token in tokens)
    return f"MRN{digits}" if len(digits) >= 4 else None


def transcript_contains_mrn(transcript: str, expected_mrn: str) -> bool:
    """Check whether a scanner-provided MRN occurs as digits or spoken digits."""
    normalized = normalize_mrn(expected_mrn)
    if not normalized:
        return False

    digits = normalized[3:]
    if re.search(rf"(?<!\d){re.escape(digits)}(?!\d)", transcript or ""):
        return True

    digit_tokens = [
        "|".join((digit, next(word for word, value in _DIGIT_WORDS.items() if value == digit)))
        for digit in digits
    ]
    spoken_pattern = r"(?<!\w)" + r"(?:[\s-]+)".join(
        f"(?:{token})" for token in digit_tokens
    ) + r"(?!\w)"
    return re.search(spoken_pattern, transcript or "", re.IGNORECASE) is not None
