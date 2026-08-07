"""Deterministic identifiers for registry entities."""

from __future__ import annotations

import uuid


NAMESPACE = uuid.UUID("78ee50bc-c9f7-58f0-a972-5f9d0b26f462")

PREFIXES = {
    "persona": "krvt_p_",
    "account": "krvt_a_",
    "organization": "krvt_o_",
    "affiliation": "krvt_f_",
    "source": "krvt_s_",
    "observation": "krvt_m_",
    "review": "krvt_r_",
}


def stable_id(kind: str, *parts: object) -> str:
    """Return a stable UUID5 identifier for a typed natural key."""

    if kind not in PREFIXES:
        raise ValueError(f"unknown registry id kind: {kind}")
    normalized = [str(part).strip() for part in parts]
    if not normalized or any(not part for part in normalized):
        raise ValueError(f"empty natural key for {kind}")
    natural_key = "\x1f".join([kind, *normalized])
    return PREFIXES[kind] + uuid.uuid5(NAMESPACE, natural_key).hex

