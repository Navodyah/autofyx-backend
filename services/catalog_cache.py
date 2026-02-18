import json
import os
from typing import Dict, List, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")


async def build_catalog(session: AsyncSession) -> Dict[str, Any]:
    """
    Build a catalog JSON structure:
    {
      "makes": ["TOYOTA", "HONDA", ...],
      "modelsByMake": {"TOYOTA": ["AQUA","PRIUS"], ...},
      "yearsByMakeModel": {"TOYOTA|AQUA":[2015,2016], ...}
    }
    Assumes vehicles table has: brand_name (or make), model_name, manufacturing_year
    Adjust column names in SQL if yours differ.
    """

    # ⚠️ Adjust these column names if your table differs
    sql = text("""
        SELECT
            b.brand_name AS make,
            v.model_name AS model,
            v.manufacturing_year AS year
        FROM vehicles v
        JOIN brands b ON b.brand_id = v.brand_id
        WHERE v.model_name IS NOT NULL
        ORDER BY b.brand_name, v.model_name, v.manufacturing_year;
    """)

    rows = (await session.execute(sql)).mappings().all()

    makes_set = set()
    models_by_make = {}
    years_by_make_model = {}

    for r in rows:
        make = str(r["make"]).strip()
        model = str(r["model"]).strip()
        year = int(r["year"]) if r["year"] is not None else None

        if not make or not model:
            continue

        makes_set.add(make)

        models_by_make.setdefault(make, set()).add(model)

        key = f"{make}|{model}"
        years_by_make_model.setdefault(key, set())
        if year:
            years_by_make_model[key].add(year)

    catalog = {
        "makes": sorted(list(makes_set)),
        "modelsByMake": {k: sorted(list(v)) for k, v in models_by_make.items()},
        "yearsByMakeModel": {k: sorted(list(v)) for k, v in years_by_make_model.items()},
    }

    return catalog


def ensure_data_dir():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(data_dir, exist_ok=True)


def write_catalog_to_file(catalog: Dict[str, Any]) -> str:
    ensure_data_dir()
    path = os.path.abspath(CATALOG_PATH)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    return path


def read_catalog_from_file() -> Dict[str, Any] | None:
    path = os.path.abspath(CATALOG_PATH)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
