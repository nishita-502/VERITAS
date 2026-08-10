"""Privacy helpers for resume preprocessing."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, Field


class PiiRedaction(BaseModel):
    """Record of a single redaction applied to resume text."""

    category: str
    original: str = Field(repr=False)
    replacement: str


class PrivacyScrubber:
    """Lightweight regex-based PII scrubber."""

    EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
    PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}")
    ADDRESS_PATTERN = re.compile(
        r"\b\d{1,5}\s+[A-Za-z0-9\s.'-]{2,80},\s*[A-Za-z\s.'-]{2,80},\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?\b"
    )

    @staticmethod
    def scrub(text: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Mask common PII before text leaves the local process."""

        if not text:
            return "", []

        redactions: List[Dict[str, Any]] = []
        scrubbed = text

        def _replace(pattern: re.Pattern[str], category: str, replacement: str) -> None:
            nonlocal scrubbed

            matches = list(dict.fromkeys(pattern.findall(scrubbed)))
            if not matches:
                return

            for match in matches:
                redactions.append(
                    PiiRedaction(category=category, original=match, replacement=replacement).model_dump()
                )
            scrubbed = pattern.sub(replacement, scrubbed)

        _replace(PrivacyScrubber.EMAIL_PATTERN, "email", "[EMAIL_REDACTED]")
        _replace(PrivacyScrubber.PHONE_PATTERN, "phone", "[PHONE_REDACTED]")
        _replace(PrivacyScrubber.ADDRESS_PATTERN, "address", "[ADDRESS_REDACTED]")

        return scrubbed, redactions