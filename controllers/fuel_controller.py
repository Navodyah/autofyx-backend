from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import requests
import re
from bs4 import BeautifulSoup

from models.fuel import FuelType
from models.vehicle import Vehicle


async def create_fuel_type(db: AsyncSession, fuel_type_name: str, fuel_price: Optional[float] = None):
    """Create a new fuel type (DB generates the ID)."""
    new_fuel_type = FuelType(fuel_type_name=fuel_type_name, fuel_price=fuel_price)
    db.add(new_fuel_type)
    await db.commit()
    await db.refresh(new_fuel_type)
    return await get_fuel_type_by_id(db, new_fuel_type.fuel_type_id)


async def get_fuel_type_by_id(db: AsyncSession, fuel_type_id: int):
    result = await db.execute(
        select(
            FuelType.fuel_type_id,
            FuelType.fuel_type_name,
            FuelType.fuel_price,
            func.avg(Vehicle.fuel_efficiency_combined).label("fuel_efficiency_combined"),
        )
        .outerjoin(Vehicle, Vehicle.fuel_type_id == FuelType.fuel_type_id)
        .where(FuelType.fuel_type_id == fuel_type_id)
        .group_by(FuelType.fuel_type_id, FuelType.fuel_type_name, FuelType.fuel_price)
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_all_fuel_types(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(
            FuelType.fuel_type_id,
            FuelType.fuel_type_name,
            FuelType.fuel_price,
            func.avg(Vehicle.fuel_efficiency_combined).label("fuel_efficiency_combined"),
        )
        .outerjoin(Vehicle, Vehicle.fuel_type_id == FuelType.fuel_type_id)
        .group_by(FuelType.fuel_type_id, FuelType.fuel_type_name, FuelType.fuel_price)
        .offset(skip)
        .limit(limit)
    )
    rows = result.mappings().all()
    return [dict(row) for row in rows]


async def update_fuel_type(
    db: AsyncSession,
    fuel_type_id: int,
    fuel_type_name: str,
    fuel_price: Optional[float] = None,
):
    result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    fuel_type = result.scalar_one_or_none()
    if not fuel_type:
        return None

    fuel_type.fuel_type_name = fuel_type_name
    fuel_type.fuel_price = fuel_price
    await db.commit()
    return await get_fuel_type_by_id(db, fuel_type_id)


async def delete_fuel_type(db: AsyncSession, fuel_type_id: int):
    result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    fuel_type = result.scalar_one_or_none()
    if not fuel_type:
        return False
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import requests
import re
from bs4 import BeautifulSoup

from models.fuel import FuelType
from models.vehicle import Vehicle


async def create_fuel_type(db: AsyncSession, fuel_type_name: str, fuel_price: Optional[float] = None):
    """Create a new fuel type (DB generates the ID)."""
    new_fuel_type = FuelType(fuel_type_name=fuel_type_name, fuel_price=fuel_price)
    db.add(new_fuel_type)
    await db.commit()
    await db.refresh(new_fuel_type)
    return await get_fuel_type_by_id(db, new_fuel_type.fuel_type_id)


async def get_fuel_type_by_id(db: AsyncSession, fuel_type_id: int):
    result = await db.execute(
        select(
            FuelType.fuel_type_id,
            FuelType.fuel_type_name,
            FuelType.fuel_price,
            FuelType.last_updated,
            func.avg(Vehicle.fuel_efficiency_combined).label("fuel_efficiency_combined"),
        )
        .outerjoin(Vehicle, Vehicle.fuel_type_id == FuelType.fuel_type_id)
        .where(FuelType.fuel_type_id == fuel_type_id)
        .group_by(FuelType.fuel_type_id, FuelType.fuel_type_name, FuelType.fuel_price, FuelType.last_updated)
    )
    row = result.mappings().first()
    if not row: return None
    row_dict = dict(row)
    if row_dict.get("last_updated"): row_dict["last_updated"] = str(row_dict["last_updated"])
    return row_dict


async def get_all_fuel_types(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(
            FuelType.fuel_type_id,
            FuelType.fuel_type_name,
            FuelType.fuel_price,
            FuelType.last_updated,
            func.avg(Vehicle.fuel_efficiency_combined).label("fuel_efficiency_combined"),
        )
        .outerjoin(Vehicle, Vehicle.fuel_type_id == FuelType.fuel_type_id)
        .group_by(FuelType.fuel_type_id, FuelType.fuel_type_name, FuelType.fuel_price, FuelType.last_updated)
        .offset(skip)
        .limit(limit)
    )
    rows = result.mappings().all()
    out = []
    for row in rows:
        r = dict(row)
        if r.get("last_updated"): r["last_updated"] = str(r["last_updated"])
        out.append(r)
    return out


async def update_fuel_type(
    db: AsyncSession,
    fuel_type_id: int,
    fuel_type_name: str,
    fuel_price: Optional[float] = None,
):
    result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    fuel_type = result.scalar_one_or_none()
    if not fuel_type:
        return None

    fuel_type.fuel_type_name = fuel_type_name
    fuel_type.fuel_price = fuel_price
    await db.commit()
    return await get_fuel_type_by_id(db, fuel_type_id)


async def delete_fuel_type(db: AsyncSession, fuel_type_id: int):
    result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == fuel_type_id))
    fuel_type = result.scalar_one_or_none()
    if not fuel_type:
        return False

    await db.delete(fuel_type)
    await db.commit()
    return True


async def scrape_fuel_prices():
    """
    Scrape fuel prices from Ceypetco and return the extracted prices mapped to IDs:
    8 -> Lanka Petrol 92 Octane
    7 -> Lanka Petrol 95 Octane Euro 4
    9 -> Lanka Super Diesel 4 Star Euro 4
    Does NOT update the database.
    """
    url = "https://ceypetco.gov.lk/marketing-sales/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch website: {e}"}

    soup = BeautifulSoup(response.content, 'html.parser')
    page_text = soup.get_text()
    
    # Mapping fuel names to DB IDs
    fuel_map = {
        'Lanka Petrol 92 Octane': 8,
        'Lanka Petrol 95 Octane Euro 4': 7,
        'Lanka Super Diesel 4 Star Euro 4': 9,
    }
    
    extracted_prices = {}

    # Try tables extraction
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                for fuel_name, f_id in fuel_map.items():
                    if any(fuel_name.lower() in cell.get_text().lower() for cell in cells):
                        row_text = ' '.join([cell.get_text().strip() for cell in cells])
                        price_pattern = r'Rs\.?\s*(\d+\.?\d*)'
                        price_match = re.search(price_pattern, row_text)
                        if price_match and str(f_id) not in extracted_prices:
                            try:
                                extracted_prices[str(f_id)] = float(price_match.group(1))
                            except ValueError:
                                pass

    # Regex fallback if some are missing
    for fuel_name, f_id in fuel_map.items():
        if str(f_id) not in extracted_prices:
            pattern = f"{re.escape(fuel_name)}[^R]*?Rs\\.?\\s*(\\d+\\.?\\d*)"
            match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
            if match:
                try:
                    extracted_prices[str(f_id)] = float(match.group(1))
                except ValueError:
                    pass

    if not extracted_prices:
        return {"status": "error", "message": "No fuel prices could be extracted."}

    return {
        "status": "success",
        "message": f"Successfully extracted {len(extracted_prices)} fuel prices.",
        "data": extracted_prices
    }

async def bulk_update_fuel_prices(db: AsyncSession, updates: dict):
    """
    Update multiple fuel prices.
    updates is a dict mapping fuel_type_id (int/str) to the new fuel_price (float).
    """
    updated_count = 0
    for f_id, price in updates.items():
        result = await db.execute(select(FuelType).filter(FuelType.fuel_type_id == int(f_id)))
        fuel_type = result.scalar_one_or_none()
        if fuel_type:
            fuel_type.fuel_price = price
            updated_count += 1
            
    await db.commit()
    
    return {
        "status": "success",
        "message": f"Successfully updated {updated_count} fuel prices in the database."
    }
