from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.maintenance import MaintenanceCost
from models.vehicle import Vehicle


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed else None


def _average(values: Iterable[float | None]) -> float:
    numbers = [value for value in values if value is not None]
    if not numbers:
        return 0.0
    return sum(numbers) / len(numbers)


def _brand_name(vehicle: Vehicle) -> str:
    return (getattr(vehicle.brand, "brand_name", None) or "Unknown Brand").strip() or "Unknown Brand"


def _class_name(vehicle: Vehicle) -> str:
    return (getattr(vehicle.vehicle_class, "class_name", None) or "Unknown Class").strip() or "Unknown Class"


def _fuel_name(vehicle: Vehicle) -> str:
    return (getattr(vehicle.fuel_type, "fuel_type_name", None) or "Unknown Fuel").strip() or "Unknown Fuel"


def _transmission_name(vehicle: Vehicle) -> str:
    return (getattr(vehicle.transmission, "transmission_name", None) or "Unknown Transmission").strip() or "Unknown Transmission"


def _engine_type_name(vehicle: Vehicle) -> str:
    return (getattr(vehicle.engine_type, "engine_type_name", None) or "Unknown Engine").strip() or "Unknown Engine"


def _engine_cylinders(vehicle: Vehicle) -> str:
    cylinders = getattr(vehicle.engine_type, "cylinders", None)
    if cylinders is not None:
        return str(cylinders)

    name = _engine_type_name(vehicle).upper()
    for token in ("12", "10", "8", "6", "5", "4", "3"):
        if token in name:
            return token
    if "ROTARY" in name:
        return "Rotary"
    return "Other"


def _format_vehicle_label(vehicle: Vehicle) -> str:
    if vehicle.model_name:
        return vehicle.model_name
    return f"Vehicle #{vehicle.vehicle_id}"


def _bucket_year(recorded_date: date | None) -> str:
    if recorded_date is None:
      return "Unknown"
    return recorded_date.strftime("%Y-%m")


async def get_researcher_analytics(db: AsyncSession) -> dict[str, Any]:
    vehicle_stmt = (
        select(Vehicle)
        .options(
            selectinload(Vehicle.brand),
            selectinload(Vehicle.vehicle_class),
            selectinload(Vehicle.engine_type),
            selectinload(Vehicle.fuel_type),
            selectinload(Vehicle.transmission),
        )
        .order_by(Vehicle.vehicle_id.asc())
    )
    vehicle_result = await db.execute(vehicle_stmt)
    vehicles = list(vehicle_result.scalars().all())

    maintenance_result = await db.execute(
        select(MaintenanceCost).order_by(MaintenanceCost.recorded_date.asc(), MaintenanceCost.record_id.asc())
    )
    maintenance_records = list(maintenance_result.scalars().all())

    vehicle_by_id = {vehicle.vehicle_id: vehicle for vehicle in vehicles}

    vehicle_rows: list[dict[str, Any]] = []
    for vehicle in vehicles:
        min_price = _to_float(vehicle.minimum_price)
        max_price = _to_float(vehicle.max_price)
        engine_size = _to_float(vehicle.engine_size)
        highway_efficiency = _to_float(vehicle.fuel_efficiency_highway)
        combined_efficiency = _to_float(vehicle.fuel_efficiency_combined)

        midpoint_price: float | None = None
        if min_price is not None and max_price is not None:
            midpoint_price = (min_price + max_price) / 2
        else:
            midpoint_price = min_price if min_price is not None else max_price

        vehicle_rows.append(
            {
                "vehicle_id": vehicle.vehicle_id,
                "label": _format_vehicle_label(vehicle),
                "brand": _brand_name(vehicle),
                "class_name": _class_name(vehicle),
                "fuel_type": _fuel_name(vehicle),
                "transmission": _transmission_name(vehicle),
                "engine_type": _engine_type_name(vehicle),
                "engine_cylinders": _engine_cylinders(vehicle),
                "engine_size": engine_size,
                "minimum_price": min_price,
                "max_price": max_price,
                "price_midpoint": midpoint_price,
                "highway_efficiency": highway_efficiency,
                "combined_efficiency": combined_efficiency,
                "manufacturing_year": vehicle.manufacturing_year,
                "created_at": vehicle.created_at.isoformat() if vehicle.created_at else None,
            }
        )

    brand_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    class_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    fuel_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    transmission_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cylinder_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in vehicle_rows:
        brand_groups[row["brand"]].append(row)
        class_groups[row["class_name"]].append(row)
        fuel_groups[row["fuel_type"]].append(row)
        transmission_groups[row["transmission"]].append(row)
        cylinder_groups[row["engine_cylinders"]].append(row)

    brand_price_data = [
        {
            "brand": brand,
            "count": len(items),
            "avg_min_price": _average(item["minimum_price"] for item in items),
            "avg_max_price": _average(item["max_price"] for item in items),
        }
        for brand, items in brand_groups.items()
    ]
    brand_price_data.sort(key=lambda item: (-item["count"], item["brand"]))

    class_price_data = [
        {
            "class_name": class_name,
            "count": len(items),
            "avg_min_price": _average(item["minimum_price"] for item in items),
            "avg_max_price": _average(item["max_price"] for item in items),
        }
        for class_name, items in class_groups.items()
    ]
    class_price_data.sort(key=lambda item: (-item["count"], item["class_name"]))

    price_engine_scatter = [
        {
            "vehicle_id": row["vehicle_id"],
            "label": row["label"],
            "brand": row["brand"],
            "class_name": row["class_name"],
            "engine_size": row["engine_size"],
            "price": row["price_midpoint"],
        }
        for row in vehicle_rows
        if row["engine_size"] is not None and row["price_midpoint"] is not None
    ]

    maintenance_by_brand: dict[str, list[float]] = defaultdict(list)
    maintenance_vehicle_rows: dict[int, list[MaintenanceCost]] = defaultdict(list)
    maintenance_trend_by_bucket: dict[str, list[float]] = defaultdict(list)

    for record in maintenance_records:
        vehicle = vehicle_by_id.get(record.vehicle_id)
        if vehicle is None:
            continue

        cost = _to_float(record.yearly_cost)
        if cost is None:
            continue

        maintenance_by_brand[_brand_name(vehicle)].append(cost)
        maintenance_vehicle_rows[record.vehicle_id].append(record)
        maintenance_trend_by_bucket[_bucket_year(record.recorded_date)].append(cost)

    maintenance_brand_data = [
        {
            "brand": brand,
            "avg_yearly_cost": _average(costs),
            "count": len(costs),
        }
        for brand, costs in maintenance_by_brand.items()
    ]
    maintenance_brand_data.sort(key=lambda item: (-item["avg_yearly_cost"], item["brand"]))

    maintenance_trend_data = [
        {
            "period": period,
            "avg_yearly_cost": _average(costs),
            "count": len(costs),
        }
        for period, costs in maintenance_trend_by_bucket.items()
    ]
    maintenance_trend_data.sort(key=lambda item: item["period"])

    top_maintenance_vehicles: list[dict[str, Any]] = []
    for vehicle_id, records in maintenance_vehicle_rows.items():
        vehicle = vehicle_by_id.get(vehicle_id)
        if vehicle is None:
            continue

        costs = [_to_float(record.yearly_cost) for record in records]
        latest_record = max(records, key=lambda record: record.recorded_date or date.min)
        top_maintenance_vehicles.append(
            {
                "vehicle_id": vehicle_id,
                "label": _format_vehicle_label(vehicle),
                "brand": _brand_name(vehicle),
                "avg_yearly_cost": _average(costs),
                "count": len(records),
                "latest_recorded_date": latest_record.recorded_date.isoformat() if latest_record.recorded_date else None,
            }
        )
    top_maintenance_vehicles.sort(key=lambda item: (-item["avg_yearly_cost"], item["label"]))

    fuel_efficiency_comparison = [
        {
            "fuel_type": fuel_type,
            "avg_highway_efficiency": _average(item["highway_efficiency"] for item in items),
            "avg_combined_efficiency": _average(item["combined_efficiency"] for item in items),
            "count": len(items),
        }
        for fuel_type, items in fuel_groups.items()
    ]
    fuel_efficiency_comparison.sort(key=lambda item: (-item["count"], item["fuel_type"]))

    efficiency_by_fuel = [
        {
            "fuel_type": fuel_type,
            "avg_combined_efficiency": _average(item["combined_efficiency"] for item in items),
            "count": len(items),
        }
        for fuel_type, items in fuel_groups.items()
    ]
    efficiency_by_fuel.sort(key=lambda item: (item["avg_combined_efficiency"], item["fuel_type"]))

    best_fuel_efficient = [
        {
            "vehicle_id": row["vehicle_id"],
            "label": row["label"],
            "brand": row["brand"],
            "class_name": row["class_name"],
            "fuel_type": row["fuel_type"],
            "combined_efficiency": row["combined_efficiency"],
            "highway_efficiency": row["highway_efficiency"],
            "engine_size": row["engine_size"],
            "price_midpoint": row["price_midpoint"],
        }
        for row in sorted(
            [row for row in vehicle_rows if row["combined_efficiency"] is not None],
            key=lambda row: (row["combined_efficiency"], row["price_midpoint"] or 0.0, row["label"]),
        )[:10]
    ]

    vehicle_count_by_brand = [
        {
            "brand": brand,
            "count": len(items),
        }
        for brand, items in brand_groups.items()
    ]
    vehicle_count_by_brand.sort(key=lambda item: (-item["count"], item["brand"]))

    vehicle_distribution_by_fuel = [
        {
            "fuel_type": fuel_type,
            "count": len(items),
        }
        for fuel_type, items in fuel_groups.items()
    ]
    vehicle_distribution_by_fuel.sort(key=lambda item: (-item["count"], item["fuel_type"]))

    transmission_usage_distribution = [
        {
            "transmission": transmission,
            "count": len(items),
        }
        for transmission, items in transmission_groups.items()
    ]
    transmission_usage_distribution.sort(key=lambda item: (-item["count"], item["transmission"]))

    engine_size_vs_efficiency = [
        {
            "vehicle_id": row["vehicle_id"],
            "label": row["label"],
            "brand": row["brand"],
            "class_name": row["class_name"],
            "engine_size": row["engine_size"],
            "combined_efficiency": row["combined_efficiency"],
            "highway_efficiency": row["highway_efficiency"],
        }
        for row in vehicle_rows
        if row["engine_size"] is not None and row["combined_efficiency"] is not None
    ]

    engine_cylinders_distribution = [
        {
            "engine_cylinders": cylinder,
            "count": len(items),
        }
        for cylinder, items in cylinder_groups.items()
    ]
    engine_cylinders_distribution.sort(key=lambda item: (item["engine_cylinders"], item["count"]))

    total_vehicle_price = [item["price_midpoint"] for item in vehicle_rows if item["price_midpoint"] is not None]
    total_highway_efficiency = [item["highway_efficiency"] for item in vehicle_rows if item["highway_efficiency"] is not None]
    total_combined_efficiency = [item["combined_efficiency"] for item in vehicle_rows if item["combined_efficiency"] is not None]
    total_maintenance_costs = [_to_float(record.yearly_cost) for record in maintenance_records]

    return {
        "summary": {
            "vehicle_count": len(vehicle_rows),
            "brand_count": len(brand_groups),
            "vehicle_class_count": len(class_groups),
            "fuel_type_count": len(fuel_groups),
            "maintenance_record_count": len(maintenance_records),
            "avg_price": _average(total_vehicle_price),
            "avg_highway_efficiency": _average(total_highway_efficiency),
            "avg_combined_efficiency": _average(total_combined_efficiency),
            "avg_maintenance_cost": _average(total_maintenance_costs),
        },
        "cost_pricing": {
            "average_min_max_by_brand": brand_price_data,
            "price_distribution_by_vehicle_class": class_price_data,
            "price_vs_engine_size_scatter": price_engine_scatter,
        },
        "maintenance": {
            "average_yearly_maintenance_by_brand": maintenance_brand_data,
            "maintenance_cost_trend": maintenance_trend_data,
            "top_10_highest_maintenance_vehicles": top_maintenance_vehicles[:10],
        },
        "fuel_efficiency": {
            "highway_vs_combined_by_fuel": fuel_efficiency_comparison,
            "efficiency_by_fuel_type": efficiency_by_fuel,
            "best_fuel_efficient_vehicles": best_fuel_efficient,
        },
        "market_insights": {
            "vehicle_count_by_brand": vehicle_count_by_brand,
            "vehicle_distribution_by_fuel": vehicle_distribution_by_fuel,
            "transmission_usage_distribution": transmission_usage_distribution,
        },
        "performance": {
            "engine_size_vs_fuel_efficiency": engine_size_vs_efficiency,
            "engine_type_cylinders_distribution": engine_cylinders_distribution,
        },
    }