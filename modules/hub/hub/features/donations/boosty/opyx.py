import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP


ZERO = Decimal("0")


@dataclass(frozen=True)
class OpyxCalculation:
    eligible: bool
    reason: str
    amount: Decimal
    base_rate: Decimal
    bonus_percent: Decimal
    final_rate: Decimal
    opyx: Decimal


def as_decimal(settings, key, default="0"):
    try:
        return Decimal(str(settings.get(key, default)))
    except (InvalidOperation, TypeError, ValueError):
        return ZERO


def parse_bonus_rules(value):
    if not value:
        return []
    rules = json.loads(value) if isinstance(value, str) else value
    parsed = []
    for rule in rules:
        minimum = Decimal(str(rule["minimum"]))
        percent = Decimal(str(rule["percent"]))
        if minimum < ZERO or percent < ZERO:
            raise ValueError("Bonus minimum and percent must be non-negative")
        parsed.append({"minimum": minimum, "percent": percent})
    return sorted(parsed, key=lambda item: item["minimum"])


def calculate_opyx(amount, settings):
    amount = Decimal(str(amount))
    base_rate = as_decimal(settings, "boosty_opyx_rate")
    if amount <= ZERO:
        return OpyxCalculation(False, "Donation amount must be positive", amount, base_rate, ZERO, base_rate, ZERO)
    if base_rate <= ZERO:
        return OpyxCalculation(False, "Opyx rate must be positive", amount, base_rate, ZERO, base_rate, ZERO)
    minimum = as_decimal(settings, "boosty_minimum_donation")
    if amount < minimum:
        return OpyxCalculation(False, "Donation is below the configured minimum", amount, base_rate, ZERO, base_rate, ZERO)

    bonus = ZERO
    if settings.get("boosty_bonus_enabled"):
        for rule in parse_bonus_rules(settings.get("boosty_bonus_rules")):
            if amount >= rule["minimum"]:
                bonus = rule["percent"]
            else:
                break

    final_rate = base_rate * (Decimal("1") + bonus / Decimal("100"))
    raw_opyx = amount * final_rate
    rounding_mode = {
        "ceil": ROUND_CEILING,
        "half_up": ROUND_HALF_UP,
        "floor": ROUND_FLOOR,
    }.get(settings.get("boosty_rounding", "floor"), ROUND_FLOOR)
    opyx = raw_opyx.quantize(Decimal("1"), rounding=rounding_mode)

    if settings.get("boosty_maximum_opyx_enabled"):
        maximum = as_decimal(settings, "boosty_maximum_opyx")
        if maximum > ZERO:
            opyx = min(opyx, maximum)

    if opyx <= ZERO:
        return OpyxCalculation(False, "Calculated Opyx amount is zero", amount, base_rate, bonus, final_rate, ZERO)
    return OpyxCalculation(True, "", amount, base_rate, bonus, final_rate, opyx)
