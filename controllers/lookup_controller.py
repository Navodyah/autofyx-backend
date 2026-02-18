# File: `controllers/lookup_controller.py`
from typing import List
from config.postgresql import get_postgres_connection


def get_all_makes() -> List[str]:
    with get_postgres_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT b.brand_name
                FROM vehicles v
                JOIN brands b ON b.brand_id = v.brand_id
                ORDER BY b.brand_name;
                """
            )
            return [row[0].strip() for row in cur.fetchall() if row[0]]


def get_models_by_make(make: str) -> List[str]:
    make = (make or "").strip()
    if not make:
        return []

    with get_postgres_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT v.model_name
                FROM vehicles v
                JOIN brands b ON b.brand_id = v.brand_id
                WHERE LOWER(b.brand_name) = LOWER(%s)
                  AND v.model_name IS NOT NULL
                  AND TRIM(v.model_name) <> ''
                ORDER BY v.model_name;
                """,
                (make,),
            )
            return [row[0].strip() for row in cur.fetchall() if row[0]]


def get_years_by_make_model(make: str, model: str) -> List[int]:
    make = (make or "").strip()
    model = (model or "").strip()
    if not make or not model:
        return []

    with get_postgres_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT v.manufacturing_year
                FROM vehicles v
                JOIN brands b ON b.brand_id = v.brand_id
                WHERE LOWER(b.brand_name) = LOWER(%s)
                  AND LOWER(v.model_name) = LOWER(%s)
                  AND v.manufacturing_year IS NOT NULL
                ORDER BY v.manufacturing_year;
                """,
                (make, model),
            )
            rows = cur.fetchall()
            return [int(r[0]) for r in rows if r[0] is not None]
