"""Complaint rules (pure logic, unit tested).

Categories: LEAK, BILLING, NO_SUPPLY, OTHER
Life cycle:  OPEN --> IN_PROGRESS --> RESOLVED   (RESOLVED is final; a complaint cannot skip IN_PROGRESS)
Resolving a complaint requires a resolution note.
"""
CATEGORIES = ("LEAK", "BILLING", "NO_SUPPLY", "OTHER")
TRANSITIONS = {("OPEN", "IN_PROGRESS"), ("IN_PROGRESS", "RESOLVED")}
MIN_RESOLUTION_LENGTH = 3


def next_status(current: str, target: str) -> str:
    if (current, target) not in TRANSITIONS:
        raise ValueError(f"invalid transition {current} -> {target}")
    return target


def allowed_next(current: str) -> list:
    return [b for a, b in sorted(TRANSITIONS) if a == current]
