from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class SalaryVehicleCategoryRule:
    min_salary_inclusive: float
    max_salary_inclusive: float | None
    categories: tuple[str, ...]


# Canonical category rules requested for Sri Lankan affordability levels.
SALARY_VEHICLE_CATEGORY_RULES: tuple[SalaryVehicleCategoryRule, ...] = (
    SalaryVehicleCategoryRule(
        min_salary_inclusive=0,
        max_salary_inclusive=99_999.99,
        categories=("KEI CAR", "MINICOMPACT", "SUBCOMPACT"),
    ),
    SalaryVehicleCategoryRule(
        min_salary_inclusive=100_000,
        max_salary_inclusive=349_999.99,
        categories=("SUBCOMPACT", "COMPACT", "WAGON", "SUV - SMALL", "MPV"),
    ),
    SalaryVehicleCategoryRule(
        min_salary_inclusive=350_000,
        max_salary_inclusive=600_000,
        categories=("COMPACT", "MID-SIZE", "WAGON", "MPV", "SUV - STANDARD", "OFF-ROAD"),
    ),
    SalaryVehicleCategoryRule(
        min_salary_inclusive=600_000.01,
        max_salary_inclusive=None,
        categories=("MID-SIZE", "FULL-SIZE", "SUV", "OFF-ROAD", "MPV", "WAGON"),
    ),
)


# Canonical category -> DB value aliases for resilient filtering.
CATEGORY_FILTER_ALIASES: dict[str, tuple[str, ...]] = {
    "KEI CAR": ("KEI CAR", "KEI", "KEI_CAR"),
    "MINICOMPACT": ("MINICOMPACT", "MINI COMPACT"),
    "SUBCOMPACT": ("SUBCOMPACT", "SUB COMPACT"),
    "COMPACT": ("COMPACT",),
    "WAGON": (
        "WAGON",
        "STATION WAGON",
        "STATION WAGON - SMALL",
        "STATION WAGON - MID-SIZE",
        "WAGON_SMALL",
        "WAGON_MIDSIZE",
    ),
    "SUV - SMALL": ("SUV - SMALL", "SUV_SMALL", "SMALL SUV"),
    "SUV - STANDARD": ("SUV - STANDARD", "SUV_STANDARD", "STANDARD SUV"),
    "SUV": ("SUV", "SUV_STANDARD", "SUV - STANDARD", "SUV_SMALL", "SUV - SMALL"),
    "MPV": ("MPV", "MINIVAN", "VAN - PASSENGER", "VAN_PASSENGER"),
    "MID-SIZE": ("MID-SIZE", "MID_SIZE", "MIDSIZE"),
    "FULL-SIZE": ("FULL-SIZE", "FULL_SIZE", "FULLSIZE"),
    "OFF-ROAD": ("OFF-ROAD", "OFF ROAD", "OFF_ROAD"),
}


SALARY_LEVEL_REFERENCE_VALUES: dict[str, float] = {
    "low": 99_999,
    "medium": 200_000,
    "high": 500_000,
    "luxury": 900_000,
}


def normalize_category(value: str) -> str:
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
    This keeps API behavior deterministic when both values are provided.
    """
    if monthly_income is not None:
        return map_salary_to_vehicle_categories(monthly_income, validate_positive=validate_positive)
    if salary_level:
        return categories_from_salary_level(salary_level)
    return []


def expand_categories_for_db_filter(categories: Iterable[str]) -> List[str]:
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
