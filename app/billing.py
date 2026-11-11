"""Pure billing logic (no I/O) so it can be unit tested in isolation.

Tariff (per month, in kilolitres):
    slab 1:   0 - 10 kL  -> Rs 5  / kL
    slab 2:  10 - 20 kL  -> Rs 8  / kL
    slab 3:  20 - 30 kL  -> Rs 12 / kL
    slab 4:  above 30 kL -> Rs 20 / kL
Commercial connections pay 1.5x the water charge.
Fixed monthly charge: Rs 50 (domestic), Rs 150 (commercial).
Late fee (paid after due date): flat Rs 25 + 2% of the bill total.
Leak alert: usage > 100 kL, or > 3x the average of previous months.
"""
from datetime import date, timedelta

SLABS = [(10, 5.0), (10, 8.0), (10, 12.0), (None, 20.0)]
FIXED_CHARGE = {"DOMESTIC": 50.0, "COMMERCIAL": 150.0}
COMMERCIAL_MULTIPLIER = 1.5
LATE_FLAT_FEE = 25.0
LATE_PERCENT = 0.02
DUE_DAYS = 15
HIGH_USAGE_LIMIT = 100.0
SPIKE_FACTOR = 3.0


def water_charge(units: float, connection_type: str = "DOMESTIC") -> float:
    if units < 0:
        raise ValueError("units cannot be negative")
    if connection_type not in FIXED_CHARGE:
        raise ValueError("invalid connection type")
    remaining = units
    total = 0.0
    for width, rate in SLABS:
        if remaining <= 0:
            break
        used = remaining if width is None else min(remaining, width)
        total += used * rate
        remaining -= used
    if connection_type == "COMMERCIAL":
        total *= COMMERCIAL_MULTIPLIER
    return round(total, 2)


def bill_total(units: float, connection_type: str = "DOMESTIC") -> dict:
    wc = water_charge(units, connection_type)
    fixed = FIXED_CHARGE[connection_type]
    return {"water_charge": wc, "fixed_charge": fixed, "total": round(wc + fixed, 2)}


def due_date_for(bill_date: date) -> date:
    return bill_date + timedelta(days=DUE_DAYS)


def late_fee(total: float, due: date, paid_on: date) -> float:
    if paid_on <= due:
        return 0.0
    return round(LATE_FLAT_FEE + total * LATE_PERCENT, 2)


def is_leak_suspected(units: float, previous_units: list) -> bool:
    if units > HIGH_USAGE_LIMIT:
        return True
    if previous_units:
        avg = sum(previous_units) / len(previous_units)
        if avg > 0 and units > SPIKE_FACTOR * avg:
            return True
    return False


def next_status(current: str, event: str) -> str:
    """Bill state machine: UNPAID --pay--> PAID, UNPAID --due_passed--> OVERDUE,
    OVERDUE --pay--> PAID. PAID is terminal."""
    table = {
        ("UNPAID", "pay"): "PAID",
        ("UNPAID", "due_passed"): "OVERDUE",
        ("OVERDUE", "pay"): "PAID",
    }
    if (current, event) not in table:
        raise ValueError(f"invalid transition {current} --{event}-->")
    return table[(current, event)]
