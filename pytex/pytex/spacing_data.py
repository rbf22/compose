"""Spacing relationships between math atom classes."""

from __future__ import annotations

from typing import Dict

Measurement = Dict[str, float | str]

THINSPACE: Measurement = {"number": 3, "unit": "mu"}
MEDIUMSPACE: Measurement = {"number": 4, "unit": "mu"}
THICKSPACE: Measurement = {"number": 5, "unit": "mu"}

SPACINGS: Dict[str, Dict[str, Measurement]] = {
    "mord": {
        "mop": THINSPACE,
        "mbin": MEDIUMSPACE,
        "mrel": THICKSPACE,
        "minner": THINSPACE,
    },
    "mop": {
        "mord": THINSPACE,
        "mop": THINSPACE,
        "mrel": THICKSPACE,
        "minner": THINSPACE,
    },
    "mbin": {
        "mord": MEDIUMSPACE,
        "mop": MEDIUMSPACE,
        "mopen": MEDIUMSPACE,
        "minner": MEDIUMSPACE,
    },
    "mrel": {
        "mord": THICKSPACE,
        "mop": THICKSPACE,
        "mopen": THICKSPACE,
        "minner": THICKSPACE,
    },
    "mopen": {},
    "mclose": {
        "mop": THINSPACE,
        "mbin": MEDIUMSPACE,
        "mrel": THICKSPACE,
        "minner": THINSPACE,
    },
    "mpunct": {
        "mord": THINSPACE,
        "mop": THINSPACE,
        "mrel": THICKSPACE,
        "mopen": THINSPACE,
        "mclose": THINSPACE,
        "mpunct": THINSPACE,
        "minner": THINSPACE,
    },
    "minner": {
        "mord": THINSPACE,
        "mop": THINSPACE,
        "mbin": MEDIUMSPACE,
        "mrel": THICKSPACE,
        "mopen": THINSPACE,
        "mpunct": THINSPACE,
        "minner": THINSPACE,
    },
}

TIGHT_SPACINGS: Dict[str, Dict[str, Measurement]] = {
    "mord": {
        "mop": THINSPACE,
    },
    "mop": {
        "mord": THINSPACE,
        "mop": THINSPACE,
    },
    "mbin": {},
    "mrel": {},
    "mopen": {},
    "mclose": {
        "mop": THINSPACE,
    },
    "mpunct": {},
    "minner": {
        "mop": THINSPACE,
    },
}


__all__ = ["SPACINGS", "TIGHT_SPACINGS", "THINSPACE", "MEDIUMSPACE", "THICKSPACE"]
