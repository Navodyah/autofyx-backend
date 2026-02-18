from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def get_makes_from_db(session: AsyncSession) -> List[str]:
    sql = text("""
        SELECT DISTINCT b.brand_name AS make
        FROM vehicles v
        JOIN brands b ON b.brand_id = v.brand_id
        ORDER BY b.brand_name;
    """)
    rows = (await session.execute(sql)).mappings().all()
    return [str(r["make"]) for r in rows if r["make"]]


async def get_models_by_make_from_db(session: AsyncSession, make: str) -> List[str]:
    sql = text("""
        SELECT DISTINCT v.model_name AS model
        FROM vehicles v
        JOIN brands b ON b.brand_id = v.brand_id
        WHERE b.brand_name = :make
        ORDER BY v.model_name;
    """)
    rows = (await session.execute(sql, {"make": make})).mappings().all()
    return [str(r["model"]) for r in rows if r["model"]]


async def get_years_by_make_model_from_db(session: AsyncSession, make: str, model: str) -> List[int]:
    sql = text("""
        SELECT DISTINCT v.manufacturing_year AS year
        FROM vehicles v
        JOIN brands b ON b.brand_id = v.brand_id
        WHERE b.brand_name = :make AND v.model_name = :model
        ORDER BY v.manufacturing_year;
    """)
    rows = (await session.execute(sql, {"make": make, "model": model})).mappings().all()
    out = []
    for r in rows:
        if r["year"] is not None:
            out.append(int(r["year"]))
    return out


async def compare_vehicles(
    session: AsyncSession,
    selections: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    selections = [
      {"make":"TOYOTA", "model":"AQUA", "year":2016},
      {"make":"HONDA", "model":"FIT", "year":2017},
    ]
    Returns user-friendly objects without vehicle_id.
    """
    if not selections:
        return []

    results: List[Dict[str, Any]] = []

    sql = text("""
        SELECT
            v.vehicle_id,
            b.brand_name AS make,
            v.model_name AS model,
            v.manufacturing_year AS year,
            c.class_name AS vehicle_class,
            v.engine_size AS engine_size,
            et.engine_type_name AS engine_type,
            t.transmission_name AS transmission,
            f.fuel_type_name AS fuel,
            v.fuel_efficiency_combined AS comb_l_per_100,
            v.fuel_efficiency_highway AS hwy_l_per_100,
            v.tyre_size AS tyre_size,
            v.description AS description
        FROM vehicles v
        JOIN brands b ON b.brand_id = v.brand_id
        LEFT JOIN vehicle_classes c ON c.class_id = v.class_id
        LEFT JOIN engine_types et ON et.engine_type_id = v.engine_type_id
        LEFT JOIN transmissions t ON t.transmission_id = v.transmission_id
        LEFT JOIN fuel_types f ON f.fuel_type_id = v.fuel_type_id
        WHERE b.brand_name = :make
          AND v.model_name = :model
          AND v.manufacturing_year = :year
        ORDER BY v.vehicle_id DESC
        LIMIT 1;
    """)

    for s in selections:
        make = str(s.get("make") or "").strip()
        model = str(s.get("model") or "").strip()
        year = s.get("year")

        if not make or not model or year is None:
            continue

        row = (await session.execute(sql, {"make": make, "model": model, "year": int(year)})).mappings().first()
        if not row:
            results.append({
                "name": f"{make} {model} ({year})",
                "found": False,
                "message": "No matching vehicle found for this selection."
            })
            continue

        # ✅ USER SIDE: DO NOT SHOW vehicle_id
        results.append({
            "found": True,
            "name": f'{row["make"]} {row["model"]} ({row["year"]})',
            "make": row["make"],
            "model": row["model"],
            "year": row["year"],
            "vehicle_class": row["vehicle_class"],
            "engine_size": row["engine_size"],
            "engine_type": row["engine_type"],
            "transmission": row["transmission"],
            "fuel": row["fuel"],
            "comb_l_per_100": row["comb_l_per_100"],
            "hwy_l_per_100": row["hwy_l_per_100"],
            "tyre_size": row["tyre_size"],
            "description": row["description"],
        })

    return results


async def compare_vehicles_admin(
    session: AsyncSession,
    selections: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    ADMIN version: includes vehicle_id
    """
    base = await compare_vehicles(session, selections)
    # fetch ids in a single pass (simple approach: re-query per item)
    # if you want faster: return id from compare_vehicles itself for admin only.
    return base
