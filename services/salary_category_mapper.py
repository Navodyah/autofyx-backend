from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class SalaryVehicleCategoryRule:
    min_salary_inclusive: float
    max_salary_inclusive: float | None
    categories: tuple[str, ...]


# ── Sri Lankan Income-Based Vehicle Category Rules ────────────────────────────
# Vehicle class names EXACTLY match the database `vehicle_classes.class_name`
# column (and the dataset CSV values), including spaces around hyphens.
#
# Income tiers mapped to vehicle class access:
#
#   LOW     (<100k)     : Kei/Minicompact/Subcompact  — easiest to maintain,
#                         cheapest parts, maximum fuel efficiency (Wagon R, Alto)
#
#   MED-LOW (100k–249k) : Subcompact → Compact → Wagon  — economy sedans and
#                         hatchbacks (Vitz, Axio, Fielder, Demio)
#
#   MED-HIGH(250k–600k) : Compact → Mid-size → MPV → SUV-Small/Standard
#                         (Corolla, Camry, Voxy, Harrier, Vezel, Fortuner)
#
#   HIGH    (>600k)     : Mid-size → Full-size → SUV → Off-road → MPV
#                         (Prado, Land Cruiser, Alphard, luxury sedans)
#
SALARY_VEHICLE_CATEGORY_RULES: tuple[SalaryVehicleCategoryRule, ...] = (
    # LOW income: Kei → Minicompact → Subcompact
    SalaryVehicleCategoryRule(
        min_salary_inclusive=0,
        max_salary_inclusive=99_999.99,
        categories=("KEI CAR", "MINICOMPACT", "SUBCOMPACT"),
    ),
    # MEDIUM-LOW income: Subcompact → Compact → Wagon
    SalaryVehicleCategoryRule(
        min_salary_inclusive=100_000,
        max_salary_inclusive=249_999.99,
        categories=("SUBCOMPACT", "COMPACT", "WAGON"),
    ),
    # MEDIUM-HIGH income: Compact → Mid-size → Wagon → MPV → SUV-Small/Standard
    SalaryVehicleCategoryRule(
        min_salary_inclusive=250_000,
        max_salary_inclusive=600_000,
        categories=("COMPACT", "MID - SIZE", "WAGON", "MPV", "SUV - SMALL", "SUV - STANDARD"),
    ),
    # HIGH income: Mid-size → Full-size → All SUV types → Off-road → MPV
    SalaryVehicleCategoryRule(
        min_salary_inclusive=600_000.01,
        max_salary_inclusive=None,
        categories=("MID - SIZE", "FULL - SIZE", "SUV", "SUV - STANDARD", "OFF - ROAD", "MPV", "WAGON"),
    ),
)


# ── Category → DB Filter Aliases ──────────────────────────────────────────────
# Keys are CANONICAL names (output of normalize_category).
# Values list every string variant the DB column might contain AFTER
# UPPER(REPLACE(class_name, '_', ' ')) is applied in the SQL query.
#
# CRITICAL: DB exact values (spaces around hyphens):
#   "MID - SIZE", "FULL - SIZE", "SUV - SMALL", "SUV - STANDARD", "OFF - ROAD"
# These MUST appear in the alias tuples for the SQL equality filter to work.
#
CATEGORY_FILTER_ALIASES: dict[str, tuple[str, ...]] = {
    # ── Kei / small cars ──────────────────────────────────────────────────────
    "KEI CAR": (
        "KEI CAR",           # DB exact
        "KEI",
        "KEI_CAR",
        "KEICAR",
    ),
    "MINICOMPACT": (
        "MINICOMPACT",       # DB exact
        "MINI COMPACT",
        "MINI-COMPACT",
    ),
    "SUBCOMPACT": (
        "SUBCOMPACT",        # DB exact
        "SUB COMPACT",
        "SUB-COMPACT",
    ),

    # ── Compact / mid ─────────────────────────────────────────────────────────
    "COMPACT": (
        "COMPACT",           # DB exact
    ),
    "WAGON": (
        "WAGON",             # DB exact
        "STATION WAGON",
        "STATION WAGON - SMALL",
        "STATION WAGON - MID-SIZE",
        "STATION WAGON - MID - SIZE",
        "WAGON SMALL",
        "WAGON MIDSIZE",
    ),

    # ── Mid / full size ───────────────────────────────────────────────────────
    # DB uses "MID - SIZE" (spaces around hyphen) — MUST be listed.
    "MID - SIZE": (
        "MID - SIZE",        # DB exact ← CRITICAL
        "MID-SIZE",
        "MID SIZE",
        "MIDSIZE",
        "MID_SIZE",
    ),
    # Shorthand alias also resolves to DB exact form
    "MID-SIZE": (
        "MID - SIZE",        # DB exact ← maps shorthand → DB name
        "MID-SIZE",
        "MID SIZE",
        "MIDSIZE",
        "MID_SIZE",
    ),
    # DB uses "FULL - SIZE" (spaces around hyphen) — MUST be listed.
    "FULL - SIZE": (
        "FULL - SIZE",       # DB exact ← CRITICAL
        "FULL-SIZE",
        "FULL SIZE",
        "FULLSIZE",
        "FULL_SIZE",
    ),
    "FULL-SIZE": (
        "FULL - SIZE",       # DB exact ← maps shorthand → DB name
        "FULL-SIZE",
        "FULL SIZE",
        "FULLSIZE",
        "FULL_SIZE",
    ),

    # ── MPV / Van ─────────────────────────────────────────────────────────────
    "MPV": (
        "MPV",               # DB exact
        "MINIVAN",
        "VAN - PASSENGER",
        "VAN PASSENGER",
        "PASSENGER VAN",
    ),

    # ── SUV variants ─────────────────────────────────────────────────────────
    # DB uses "SUV - SMALL" and "SUV - STANDARD" (spaces around hyphen).
    "SUV - SMALL": (
        "SUV - SMALL",       # DB exact ← CRITICAL
        "SUV-SMALL",
        "SUV SMALL",
        "SMALL SUV",
        "SUV_SMALL",
    ),
    "SUV-SMALL": (
        "SUV - SMALL",       # DB exact
        "SUV-SMALL",
        "SUV SMALL",
        "SMALL SUV",
    ),
    "SUV - STANDARD": (
        "SUV - STANDARD",    # DB exact ← CRITICAL
        "SUV-STANDARD",
        "SUV STANDARD",
        "STANDARD SUV",
        "SUV_STANDARD",
    ),
    "SUV-STANDARD": (
        "SUV - STANDARD",    # DB exact
        "SUV-STANDARD",
        "SUV STANDARD",
        "STANDARD SUV",
    ),
    # Generic "SUV" in the DB — covers all SUV rows not classified as SMALL/STANDARD
    "SUV": (
        "SUV",               # DB exact
        "SUV - STANDARD",    # also include SUV-STANDARD and SUV-SMALL for broad match
        "SUV - SMALL",
        "SUV-STANDARD",
        "SUV-SMALL",
        "SUV_STANDARD",
        "SUV_SMALL",
    ),

    # ── Off-road ─────────────────────────────────────────────────────────────
    # DB uses "OFF - ROAD" (spaces around hyphen) — MUST be listed.
    "OFF - ROAD": (
        "OFF - ROAD",        # DB exact ← CRITICAL
        "OFF-ROAD",
        "OFF ROAD",
        "OFF_ROAD",
        "OFFROAD",
    ),
    "OFF-ROAD": (
        "OFF - ROAD",        # DB exact ← maps shorthand → DB name
        "OFF-ROAD",
        "OFF ROAD",
        "OFF_ROAD",
        "OFFROAD",
    ),
}


# ── Salary level → representative monthly salary (LKR) ───────────────────────────────
SALARY_LEVEL_REFERENCE_VALUES: dict[str, float] = {
    "low":        70_000,
    "medium_low": 180_000,
    "medium":     350_000,
    "high":       750_000,
    "luxury":     900_000,
}


# ── Purpose × Area → Suitable Vehicle Classes ─────────────────────────────────
# primary_need : economy | family | performance | luxury
# area         : city | highway | mixed | off-road | offroad
#
# These classes are intersected with the salary-based class list.
# The intersection tells the DB filter exactly which rows to consider,
# ensuring both affordability AND use-case suitability.
#
# Examples:
#   economy + city  → KEI CAR, MINICOMPACT, SUBCOMPACT, COMPACT
#   family  + city  → SUBCOMPACT, COMPACT, WAGON, MPV   (KEI is too small)
#   luxury  + city  → COMPACT, MID - SIZE, FULL - SIZE, MPV
#   performance + off-road → SUV - STANDARD, SUV, OFF - ROAD
#
PURPOSE_AREA_CLASS_MAP: dict[str, dict[str, tuple[str, ...]]] = {
    # ── ECONOMY / DAILY COMMUTE ─────────────────────────────────────────────
    # Fuel-efficiency + cheapest running cost are the top priority.
    "economy": {
        "city":     ("KEI CAR", "MINICOMPACT", "SUBCOMPACT"),
        "highway":  ("MINICOMPACT", "SUBCOMPACT", "COMPACT", "WAGON", "MID - SIZE"),
        "mixed":    ("MINICOMPACT", "SUBCOMPACT", "COMPACT", "WAGON"),
        "off-road": ("SUV - SMALL", "SUV - STANDARD", "OFF - ROAD"),
        "offroad":  ("SUV - SMALL", "SUV - STANDARD", "OFF - ROAD"),
    },
    # ── FAMILY ───────────────────────────────────────────────────────
    # Space + practicality first. KEI/MINICOMPACT excluded — too small.
    "family": {
        "city":     ("MINICOMPACT", "SUBCOMPACT", "COMPACT", "WAGON", "MPV"),
        "highway":  ("MINICOMPACT", "SUBCOMPACT", "COMPACT", "WAGON", "MPV", "MID - SIZE", "SUV - SMALL", "SUV - STANDARD"),
        "mixed":    ("MINICOMPACT", "SUBCOMPACT", "COMPACT", "WAGON", "MPV", "MID - SIZE", "SUV - SMALL", "SUV - STANDARD"),
        "off-road": ("SUV - SMALL", "SUV - STANDARD", "OFF - ROAD", "MPV"),
        "offroad":  ("SUV - SMALL", "SUV - STANDARD", "OFF - ROAD", "MPV"),
    },
    # ── PERFORMANCE ────────────────────────────────────────────────
    # Power + driving dynamics. Off-road needs rugged capable bodies.
    "performance": {
        "city":     ("SUBCOMPACT", "COMPACT", "MID - SIZE"),
        "highway":  ("COMPACT", "MID - SIZE", "FULL - SIZE"),
        "mixed":    ("COMPACT", "MID - SIZE"),
        "off-road": ("SUV - STANDARD", "SUV", "OFF - ROAD"),
        "offroad":  ("SUV - STANDARD", "SUV", "OFF - ROAD"),
    },
    # ── LUXURY ──────────────────────────────────────────────────────
    # Premium comfort + prestige. Smallest class = Compact (luxury compact).
    "luxury": {
        "city":     ("COMPACT", "MID - SIZE", "FULL - SIZE", "MPV"),
        "highway":  ("MID - SIZE", "FULL - SIZE", "SUV - STANDARD"),
        "mixed":    ("MID - SIZE", "FULL - SIZE", "MPV", "SUV - STANDARD"),
        "off-road": ("FULL - SIZE", "SUV - STANDARD", "SUV", "OFF - ROAD"),
        "offroad":  ("FULL - SIZE", "SUV - STANDARD", "SUV", "OFF - ROAD"),
    },
}


def get_purpose_area_categories(
    primary_need: str,
    area: str,
) -> List[str]:
    """
    Return the list of DB vehicle class names appropriate for the given
    primary_need (economy|family|performance|luxury) and usage area
    (city|highway|mixed|off-road).
    Returns an empty list if the combination is not found (no constraint).
    """
    need_key = str(primary_need or "").strip().lower()
    area_key = str(area or "mixed").strip().lower()
    area_map = PURPOSE_AREA_CLASS_MAP.get(need_key)
    if not area_map:
        return []
    return list(area_map.get(area_key, area_map.get("mixed", [])))


def normalize_category(value: str) -> str:
    """
    Normalise a category name to a canonical form for alias lookup.
    Strips extra whitespace, uppercases, replaces underscores with spaces,
    then collapses any multi-space runs to single spaces.
    """
    return " ".join(str(value).strip().upper().replace("_", " ").split())


def map_salary_to_vehicle_categories(salary: float, validate_positive: bool = True) -> List[str]:
    salary_value = float(salary)

    if validate_positive and salary_value <= 0:
        raise ValueError("Salary must be greater than zero.")

    for rule in SALARY_VEHICLE_CATEGORY_RULES:
        max_ok = rule.max_salary_inclusive is None or salary_value <= rule.max_salary_inclusive
        if salary_value >= rule.min_salary_inclusive and max_ok:
            return list(rule.categories)

    return []


def resolve_salary_vehicle_categories(
    monthly_income: float | None,
    salary_level: str | None,
    validate_positive: bool = True,
) -> List[str]:
    """
    Resolve affordability categories with income taking precedence over level.
    This keeps API behaviour deterministic when both values are provided.
    """
    if monthly_income is not None:
        return map_salary_to_vehicle_categories(monthly_income, validate_positive=validate_positive)
    if salary_level:
        return categories_from_salary_level(salary_level)
    return []


def expand_categories_for_db_filter(categories: Iterable[str]) -> List[str]:
    """
    Expand a list of canonical category names into all DB-matchable alias strings.
    The SQL filter uses UPPER(REPLACE(class_name, '_', ' ')) = ANY(%(class_filters)s),
    so every alias value returned here must match that transformation of the DB value.
    """
    expanded: set[str] = set()
    for category in categories:
        canonical = normalize_category(category)
        aliases = CATEGORY_FILTER_ALIASES.get(canonical, (canonical,))
        for alias in aliases:
            expanded.add(normalize_category(alias))
    return sorted(expanded)


def categories_from_salary_level(salary_level: str) -> List[str]:
    level = str(salary_level or "").strip().lower()
    ref_salary = SALARY_LEVEL_REFERENCE_VALUES.get(level)
    if ref_salary is None:
        return []
    return map_salary_to_vehicle_categories(ref_salary, validate_positive=False)
