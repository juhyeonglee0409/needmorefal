"""Public email extraction helpers."""

from __future__ import annotations

import re


EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", re.IGNORECASE)


def extract_public_email(text: str | None) -> str | None:
    """Return the first email explicitly present in text.

    This intentionally does not infer, generate, or normalize missing emails.
    """

    if not text:
        return None
    match = EMAIL_RE.search(text)
    if not match:
        return None
    return match.group(0).strip(".,;:()[]{}<>\"'")


def email_domain(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    return email.rsplit("@", 1)[1].lower()
