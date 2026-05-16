from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from routes import brand_routes, compare_routes, engine_routes, fuel_routes, lookup_routes, maintenance_routes, recommender_routes, vehicle_routes, model_routes, oil_routes, transmission_routes, user_routes, user_profile_routes, vehicle_class_routes
from schemas.recommender_schemas import RecommendResponse
from config.postgresql import get_db
from dependencies.auth import get_current_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_brand(brand_id: int = 1, brand_name: str = "Toyota", country: str | None = "Japan"):
    return SimpleNamespace(brand_id=brand_id, brand_name=brand_name, country=country)


def make_vehicle(
    vehicle_id: int = 1,
    model_name: str = "Civic",
    brand_id: int = 11,
    class_id: int = 17,
    engine_type_id: int = 5,
    fuel_type_id: int = 2,
    transmission_id: int = 3,
    oil_id: int = 4,
    engine_size: Decimal = Decimal("1.6"),
    minimum_price: Decimal = Decimal("8.0"),
    max_price: Decimal = Decimal("10.0"),
    manufacturing_year: int = 2025,
    tyre_size: str = "205/55R16",
    fuel_efficiency_highway: Decimal = Decimal("12.5"),
    fuel_efficiency_combined: Decimal = Decimal("15.0"),
    description: str = "Compact sedan",
    image_url: str = "https://example.com/civic.png",
):
    return SimpleNamespace(
        vehicle_id=vehicle_id,
        model_name=model_name,
        brand_id=brand_id,
        class_id=class_id,
        engine_type_id=engine_type_id,
        fuel_type_id=fuel_type_id,
        transmission_id=transmission_id,
        oil_id=oil_id,
        engine_size=engine_size,
        minimum_price=minimum_price,
        max_price=max_price,
        manufacturing_year=manufacturing_year,
        tyre_size=tyre_size,
        fuel_efficiency_highway=fuel_efficiency_highway,
        fuel_efficiency_combined=fuel_efficiency_combined,
        description=description,
        image_url=image_url,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
    )


def make_engine(engine_type_id: int = 1, engine_type_name: str = "Inline-4", cylinders: int = 4):
    return SimpleNamespace(
        engine_type_id=engine_type_id,
        engine_type_name=engine_type_name,
        cylinders=cylinders,
    )


def make_fuel(
    fuel_type_id: int = 1,
    fuel_type_name: str = "Petrol 92",
    fuel_price: Decimal | None = Decimal("420.50"),
    fuel_efficiency_combined: Decimal | None = Decimal("15.0"),
):
    return SimpleNamespace(
        fuel_type_id=fuel_type_id,
        fuel_type_name=fuel_type_name,
        fuel_price=fuel_price,
        fuel_efficiency_combined=fuel_efficiency_combined,
    )


def make_maintenance(
    record_id: int = 1,
    vehicle_id: int = 100,
    yearly_cost: Decimal = Decimal("250000.00"),
    recorded_date: date | None = date(2026, 1, 15),
    source: str | None = "OEM",
):
    return SimpleNamespace(
        record_id=record_id,
        vehicle_id=vehicle_id,
        yearly_cost=yearly_cost,
        recorded_date=recorded_date,
        source=source,
    )


def make_model(
    model_id: int = 1,
    brand_id: int = 10,
    model_name: str = "Corolla",
    start_year: int | None = 2010,
    end_year: int | None = None,
):
    return SimpleNamespace(
        model_id=model_id,
        brand_id=brand_id,
        model_name=model_name,
        start_year=start_year,
        end_year=end_year,
    )


def make_oil(oil_id: int = 1, oil_grade: str = "5W-30", description: str | None = "Synthetic"):
    return SimpleNamespace(
        oil_id=oil_id,
        oil_grade=oil_grade,
        description=description,
    )


def make_transmission(
    transmission_id: int = 1,
    transmission_name: str = "Automatic",
    category: str | None = "A",
):
    return SimpleNamespace(
        transmission_id=transmission_id,
        transmission_name=transmission_name,
        category=category,
    )


def make_vehicle_class(class_id: int = 1, class_name: str = "COMPACT"):
    return SimpleNamespace(class_id=class_id, class_name=class_name)


# ---------------------------------------------------------------------------
# Lookup endpoint tests
# ---------------------------------------------------------------------------

def test_lookup_makes_endpoint_returns_items(client, monkeypatch):
    monkeypatch.setattr(lookup_routes, "get_all_makes", lambda: ["AUDI", "BMW"])

    response = client.get("/lookup/makes")

    assert response.status_code == 200
    assert response.json() == {"items": ["AUDI", "BMW"]}


def test_lookup_models_endpoint_returns_items(client, monkeypatch):
    monkeypatch.setattr(lookup_routes, "get_models_by_make", lambda make: [f"{make} A3", f"{make} A4"])

    response = client.get("/lookup/models", params={"make": "AUDI"})

    assert response.status_code == 200
    assert response.json() == {"items": ["AUDI A3", "AUDI A4"]}


def test_lookup_years_endpoint_returns_items(client, monkeypatch):
    monkeypatch.setattr(lookup_routes, "get_years_by_make_model", lambda make, model: [2022, 2023])

    response = client.get("/lookup/years", params={"make": "BMW", "model": "740i xDrive"})

    assert response.status_code == 200
    assert response.json() == {"items": [2022, 2023]}


# ---------------------------------------------------------------------------
# Brand endpoint tests
# ---------------------------------------------------------------------------

def test_create_brand_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_brand())
    monkeypatch.setattr(brand_routes, "create_brand", mocked)

    response = client.post("/brands/", json={"brand_name": "Toyota", "country": "Japan"})

    assert response.status_code == 201
    assert response.json()["brand_name"] == "Toyota"
    assert response.json()["country"] == "Japan"
    mocked.assert_awaited_once()


def test_get_brand_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_brand())
    monkeypatch.setattr(brand_routes, "get_brand_by_id", mocked)

    response = client.get("/brands/1")

    assert response.status_code == 200
    assert response.json()["brand_id"] == 1
    assert response.json()["brand_name"] == "Toyota"


def test_get_all_brands_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_brand(), make_brand(2, "Honda", "Japan")])
    monkeypatch.setattr(brand_routes, "get_all_brands", mocked)

    response = client.get("/brands/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["brand_name"] == "Honda"


def test_update_brand_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_brand(1, "Toyota Updated", "Japan"))
    monkeypatch.setattr(brand_routes, "update_brand", mocked)

    response = client.put("/brands/1", json={"brand_name": "Toyota Updated", "country": "Japan"})

    assert response.status_code == 200
    assert response.json()["brand_name"] == "Toyota Updated"
    mocked.assert_awaited_once()


def test_delete_brand_route(client, monkeypatch):
    mocked = AsyncMock(return_value=True)
    monkeypatch.setattr(brand_routes, "delete_brand", mocked)

    response = client.delete("/brands/1")

    assert response.status_code == 204
    assert response.content == b""
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# Vehicle endpoint tests
# ---------------------------------------------------------------------------

def test_create_vehicle_route_accepts_vehicle_model_alias(client, monkeypatch):
    mocked = AsyncMock(return_value=make_vehicle())
    monkeypatch.setattr(vehicle_routes, "create_vehicle", mocked)

    payload = {
        "brand_id": 11,
        "vehicle_model": "Civic",
        "engine_size": 1.6,
        "class_id": 17,
        "engine_type_id": 5,
        "fuel_type_id": 2,
        "transmission_id": 3,
        "oil_id": 4,
        "tyre_size": "205/55R16",
        "manufacturing_year": 2025,
        "fuel_efficiency_highway": 12.5,
        "fuel_efficiency_combined": 15.0,
        "description": "Compact sedan",
        "minimum_price": 8.0,
        "max_price": 10.0,
        "image_url": "https://example.com/civic.png",
    }

    response = client.post("/vehicles/", json=payload)

    assert response.status_code == 201
    assert response.json()["model_name"] == "Civic"
    mocked.assert_awaited_once()
    assert mocked.await_args.args[1] == "Civic"


def test_get_vehicle_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_vehicle())
    monkeypatch.setattr(vehicle_routes, "get_vehicle_by_id", mocked)

    response = client.get("/vehicles/1")

    assert response.status_code == 200
    body = response.json()
    assert body["vehicle_id"] == 1
    assert body["model_name"] == "Civic"
    assert body["image_url"] == "https://example.com/civic.png"


def test_get_all_vehicles_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_vehicle(), make_vehicle(2, "Corolla", 12)])
    monkeypatch.setattr(vehicle_routes, "get_all_vehicles", mocked)

    response = client.get("/vehicles/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["model_name"] == "Corolla"


def test_update_vehicle_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_vehicle(1, "Civic Facelift"))
    monkeypatch.setattr(vehicle_routes, "update_vehicle", mocked)

    payload = {
        "model_name": "Civic Facelift",
        "class_id": 17,
        "engine_type_id": 5,
        "fuel_type_id": 2,
        "transmission_id": 3,
        "oil_id": 4,
        "manufacturing_year": 2025,
        "minimum_price": 9.0,
        "max_price": 12.0,
    }

    response = client.put("/vehicles/1", json=payload)

    assert response.status_code == 200
    assert response.json()["model_name"] == "Civic Facelift"
    mocked.assert_awaited_once()


def test_delete_vehicle_route(client, monkeypatch):
    mocked = AsyncMock(return_value=True)
    monkeypatch.setattr(vehicle_routes, "delete_vehicle", mocked)

    response = client.delete("/vehicles/1")

    assert response.status_code == 200
    assert response.json() == {"deleted": 1}
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# Compare endpoint test
# ---------------------------------------------------------------------------

def test_compare_endpoint_accepts_wrapper_payload(client, monkeypatch):
    mocked = AsyncMock(return_value=[{"make": "BMW", "model": "740i xDrive", "score": 98.5}])
    monkeypatch.setattr(compare_routes, "compare_vehicles_controller", mocked)

    payload = {
        "selections": [
            {"make": "BMW", "model": "740i xDrive", "year": 2023},
            {"make": "AUDI", "model": "A3 Sedan 40 TFSI quattro", "year": 2022},
        ]
    }

    response = client.post("/compare/", json=payload)

    assert response.status_code == 200
    assert response.json() == [{"make": "BMW", "model": "740i xDrive", "score": 98.5}]
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# Recommendation endpoint tests
# ---------------------------------------------------------------------------

def test_recommendation_health_endpoint(client):
    response = client.get("/recommendations/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_recommendation_endpoint_uses_mocked_controller(client, monkeypatch):
    mocked_result = RecommendResponse(
        message="Found 1 recommendation.",
        count=1,
        items=[{"vehicle_id": 1, "Make": "TOYOTA", "Model": "COROLLA"}],
        finance={"salary": 250000, "rate_of_interest": 13.0, "number_of_months": 60},
    )
    monkeypatch.setattr(recommender_routes.controller, "recommend", lambda req: mocked_result)

    response = client.post("/recommendations/", json={"salary": 250000})

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["message"] == "Found 1 recommendation."
    assert body["items"][0]["Model"] == "COROLLA"


def test_recommendation_requires_salary(client):
    response = client.post("/recommendations/", json={})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Engine endpoint tests
# ---------------------------------------------------------------------------

def test_create_engine_type_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_engine())
    monkeypatch.setattr(engine_routes, "create_engine_type", mocked)

    response = client.post("/engine-types/", json={"engine_type_name": "Inline-4", "cylinders": 4})

    assert response.status_code == 201
    assert response.json()["engine_type_name"] == "Inline-4"
    assert response.json()["cylinders"] == 4
    mocked.assert_awaited_once()


def test_get_engine_type_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_engine())
    monkeypatch.setattr(engine_routes, "get_engine_type_by_id", mocked)

    response = client.get("/engine-types/1")

    assert response.status_code == 200
    assert response.json()["engine_type_id"] == 1
    assert response.json()["engine_type_name"] == "Inline-4"


def test_get_all_engine_types_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_engine(), make_engine(2, "V6", 6)])
    monkeypatch.setattr(engine_routes, "get_all_engine_types", mocked)

    response = client.get("/engine-types/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["engine_type_name"] == "V6"


def test_update_engine_type_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_engine(1, "V8", 8))
    monkeypatch.setattr(engine_routes, "update_engine_type", mocked)

    response = client.put("/engine-types/1", json={"engine_type_name": "V8", "cylinders": 8})

    assert response.status_code == 200
    assert response.json()["engine_type_name"] == "V8"
    assert response.json()["cylinders"] == 8
    mocked.assert_awaited_once()


def test_delete_engine_type_route(client, monkeypatch):
    mocked = AsyncMock(return_value=True)
    monkeypatch.setattr(engine_routes, "delete_engine_type", mocked)

    response = client.delete("/engine-types/1")

    assert response.status_code == 204
    assert response.content == b""
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# Fuel endpoint tests
# ---------------------------------------------------------------------------

def test_create_fuel_type_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_fuel())
    monkeypatch.setattr(fuel_routes, "create_fuel_type", mocked)

    response = client.post("/fuel_types/", json={"fuel_type_name": "Petrol 92", "fuel_price": 420.5})

    assert response.status_code == 201
    assert response.json()["fuel_type_name"] == "Petrol 92"
    assert float(response.json()["fuel_price"]) == 420.5
    mocked.assert_awaited_once()


def test_get_fuel_type_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_fuel())
    monkeypatch.setattr(fuel_routes, "get_fuel_type_by_id", mocked)

    response = client.get("/fuel_types/1")

    assert response.status_code == 200
    assert response.json()["fuel_type_id"] == 1
    assert response.json()["fuel_type_name"] == "Petrol 92"


def test_get_all_fuel_types_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_fuel(), make_fuel(2, "Diesel", Decimal("390.0"), Decimal("12.0"))])
    monkeypatch.setattr(fuel_routes, "get_all_fuel_types", mocked)

    response = client.get("/fuel_types/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["fuel_type_name"] == "Diesel"


def test_update_fuel_type_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_fuel(1, "Petrol 95", Decimal("450.0"), Decimal("14.2")))
    monkeypatch.setattr(fuel_routes, "update_fuel_type", mocked)

    response = client.put("/fuel_types/1", json={"fuel_type_name": "Petrol 95", "fuel_price": 450.0})

    assert response.status_code == 200
    assert response.json()["fuel_type_name"] == "Petrol 95"
    assert float(response.json()["fuel_price"]) == 450.0
    mocked.assert_awaited_once()


def test_delete_fuel_type_route(client, monkeypatch):
    mocked = AsyncMock(return_value=True)
    monkeypatch.setattr(fuel_routes, "delete_fuel_type", mocked)

    response = client.delete("/fuel_types/1")

    assert response.status_code == 204
    assert response.content == b""
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# Maintenance endpoint tests
# ---------------------------------------------------------------------------

def test_create_maintenance_cost_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_maintenance())
    monkeypatch.setattr(maintenance_routes, "create_maintenance_cost", mocked)

    payload = {
        "vehicle_id": 100,
        "yearly_cost": 250000.0,
        "recorded_date": "2026-01-15",
        "source": "OEM",
    }

    response = client.post("/maintenance-costs/", json=payload)

    assert response.status_code == 201
    assert response.json()["vehicle_id"] == 100
    assert float(response.json()["yearly_cost"]) == 250000.0
    assert response.json()["source"] == "OEM"
    mocked.assert_awaited_once()


def test_get_maintenance_cost_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_maintenance())
    monkeypatch.setattr(maintenance_routes, "get_maintenance_cost_by_id", mocked)

    response = client.get("/maintenance-costs/1")

    assert response.status_code == 200
    assert response.json()["record_id"] == 1
    assert response.json()["vehicle_id"] == 100


def test_get_all_maintenance_costs_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_maintenance(), make_maintenance(2, 101, Decimal("200000.00"), date(2026, 2, 1))])
    monkeypatch.setattr(maintenance_routes, "get_all_maintenance_costs", mocked)

    response = client.get("/maintenance-costs/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["record_id"] == 2


def test_get_maintenance_costs_by_vehicle_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_maintenance(), make_maintenance(2, 100, Decimal("280000.00"), date(2026, 3, 1))])
    monkeypatch.setattr(maintenance_routes, "get_maintenance_costs_by_vehicle", mocked)

    response = client.get("/maintenance-costs/vehicle/100")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["vehicle_id"] == 100


def test_update_maintenance_cost_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_maintenance(1, 100, Decimal("270000.00"), date(2026, 4, 1), "Service Center"))
    monkeypatch.setattr(maintenance_routes, "update_maintenance_cost", mocked)

    payload = {
        "vehicle_id": 100,
        "yearly_cost": 270000.0,
        "recorded_date": "2026-04-01",
        "source": "Service Center",
    }

    response = client.put("/maintenance-costs/1", json=payload)

    assert response.status_code == 200
    assert float(response.json()["yearly_cost"]) == 270000.0
    assert response.json()["source"] == "Service Center"
    mocked.assert_awaited_once()


def test_delete_maintenance_cost_route(client, monkeypatch):
    mocked = AsyncMock(return_value=True)
    monkeypatch.setattr(maintenance_routes, "delete_maintenance_cost", mocked)

    response = client.delete("/maintenance-costs/1")

    assert response.status_code == 200
    assert response.json() == {"deleted": 1}
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# Model endpoint tests
# ---------------------------------------------------------------------------

def test_get_available_brands_route(client, monkeypatch):
    class FakeResult:
        def all(self):
            return [(1, "Toyota"), (2, "Honda")]

    class FakeSession:
        async def execute(self, stmt):
            return FakeResult()

    async def override_get_db():
        yield FakeSession()

    client.app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/models/available-brands")
    finally:
        client.app.dependency_overrides.pop(get_db, None)

    assert response.status_code == 200
    assert response.json() == [
        {"brand_id": 1, "brand_name": "Toyota"},
        {"brand_id": 2, "brand_name": "Honda"},
    ]


def test_create_model_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_model())
    monkeypatch.setattr(model_routes, "create_model", mocked)

    payload = {"brand_id": 10, "model_name": "Corolla", "start_year": 2010, "end_year": None}

    response = client.post("/models/", json=payload)

    assert response.status_code == 201
    assert response.json()["model_name"] == "Corolla"
    mocked.assert_awaited_once()


def test_get_model_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_model())
    monkeypatch.setattr(model_routes, "get_model_by_id", mocked)

    response = client.get("/models/1")

    assert response.status_code == 200
    assert response.json()["model_id"] == 1


def test_get_all_models_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_model(), make_model(2, 11, "Civic", 2015, None)])
    monkeypatch.setattr(model_routes, "get_all_models", mocked)

    response = client.get("/models/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["model_name"] == "Civic"


def test_get_models_by_brand_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_model(), make_model(2, 10, "Camry", 2012, 2020)])
    monkeypatch.setattr(model_routes, "get_models_by_brand", mocked)

    response = client.get("/models/brand/10")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["brand_id"] == 10


def test_update_model_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_model(1, 10, "Corolla Altis", 2014, None))
    monkeypatch.setattr(model_routes, "update_model", mocked)

    payload = {"brand_id": 10, "model_name": "Corolla Altis", "start_year": 2014, "end_year": None}

    response = client.put("/models/1", json=payload)

    assert response.status_code == 200
    assert response.json()["model_name"] == "Corolla Altis"
    mocked.assert_awaited_once()


def test_delete_model_route(client, monkeypatch):
    mocked = AsyncMock(return_value=True)
    monkeypatch.setattr(model_routes, "delete_model", mocked)

    response = client.delete("/models/1")

    assert response.status_code == 204
    assert response.content == b""
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# Oil endpoint tests
# ---------------------------------------------------------------------------

def test_create_oil_quality_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_oil())
    monkeypatch.setattr(oil_routes, "create_oil_quality", mocked)

    response = client.post("/oil_quality/", json={"oil_grade": "5W-30", "description": "Synthetic"})

    assert response.status_code == 201
    assert response.json()["oil_grade"] == "5W-30"
    assert response.json()["description"] == "Synthetic"
    mocked.assert_awaited_once()


def test_get_oil_quality_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_oil())
    monkeypatch.setattr(oil_routes, "get_oil_quality_by_id", mocked)

    response = client.get("/oil_quality/1")

    assert response.status_code == 200
    assert response.json()["oil_id"] == 1
    assert response.json()["oil_grade"] == "5W-30"


def test_get_all_oil_qualities_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_oil(), make_oil(2, "0W-20", "OEM")])
    monkeypatch.setattr(oil_routes, "get_all_oil_qualities", mocked)

    response = client.get("/oil_quality/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["oil_grade"] == "0W-20"


def test_update_oil_quality_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_oil(1, "10W-40", "Semi-synthetic"))
    monkeypatch.setattr(oil_routes, "update_oil_quality", mocked)

    response = client.put("/oil_quality/1", json={"oil_grade": "10W-40", "description": "Semi-synthetic"})

    assert response.status_code == 200
    assert response.json()["oil_grade"] == "10W-40"
    assert response.json()["description"] == "Semi-synthetic"
    mocked.assert_awaited_once()


def test_delete_oil_quality_route(client, monkeypatch):
    mocked = AsyncMock(return_value=True)
    monkeypatch.setattr(oil_routes, "delete_oil_quality", mocked)

    response = client.delete("/oil_quality/1")

    assert response.status_code == 204
    assert response.content == b""
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# Transmission endpoint tests
# ---------------------------------------------------------------------------

def test_create_transmission_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_transmission())
    monkeypatch.setattr(transmission_routes, "create_transmission", mocked)

    response = client.post("/transmissions/", json={"transmission_name": "Automatic", "category": "A"})

    assert response.status_code == 201
    assert response.json()["transmission_name"] == "Automatic"
    assert response.json()["category"] == "A"
    mocked.assert_awaited_once()


def test_get_transmission_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_transmission())
    monkeypatch.setattr(transmission_routes, "get_transmission_by_id", mocked)

    response = client.get("/transmissions/1")

    assert response.status_code == 200
    assert response.json()["transmission_id"] == 1


def test_get_all_transmissions_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_transmission(), make_transmission(2, "Manual", "M")])
    monkeypatch.setattr(transmission_routes, "get_all_transmissions", mocked)

    response = client.get("/transmissions/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["transmission_name"] == "Manual"


def test_update_transmission_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_transmission(1, "CVT", "A"))
    monkeypatch.setattr(transmission_routes, "update_transmission", mocked)

    response = client.put("/transmissions/1", json={"transmission_name": "CVT", "category": "A"})

    assert response.status_code == 200
    assert response.json()["transmission_name"] == "CVT"
    mocked.assert_awaited_once()


def test_delete_transmission_route(client, monkeypatch):
    mocked = AsyncMock(return_value=True)
    monkeypatch.setattr(transmission_routes, "delete_transmission", mocked)

    response = client.delete("/transmissions/1")

    assert response.status_code == 204
    assert response.content == b""
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# Vehicle class endpoint tests
# ---------------------------------------------------------------------------

def test_create_vehicle_class_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_vehicle_class())
    monkeypatch.setattr(vehicle_class_routes, "create_vehicle_class", mocked)

    response = client.post("/vehicle_classes/", json={"class_name": "COMPACT"})

    assert response.status_code == 201
    assert response.json()["class_name"] == "COMPACT"
    mocked.assert_awaited_once()


def test_get_vehicle_class_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_vehicle_class())
    monkeypatch.setattr(vehicle_class_routes, "get_vehicle_class_by_id", mocked)

    response = client.get("/vehicle_classes/1")

    assert response.status_code == 200
    assert response.json()["class_id"] == 1


def test_get_all_vehicle_classes_route(client, monkeypatch):
    mocked = AsyncMock(return_value=[make_vehicle_class(), make_vehicle_class(2, "SUV")])
    monkeypatch.setattr(vehicle_class_routes, "get_all_vehicle_classes", mocked)

    response = client.get("/vehicle_classes/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[1]["class_name"] == "SUV"


def test_update_vehicle_class_route(client, monkeypatch):
    mocked = AsyncMock(return_value=make_vehicle_class(1, "MPV"))
    monkeypatch.setattr(vehicle_class_routes, "update_vehicle_class", mocked)

    response = client.put("/vehicle_classes/1", json={"class_name": "MPV"})

    assert response.status_code == 200
    assert response.json()["class_name"] == "MPV"
    mocked.assert_awaited_once()


def test_delete_vehicle_class_route(client, monkeypatch):
    mocked = AsyncMock(return_value=True)
    monkeypatch.setattr(vehicle_class_routes, "delete_vehicle_class", mocked)

    response = client.delete("/vehicle_classes/1")

    assert response.status_code == 204
    assert response.content == b""
    mocked.assert_awaited_once()


# ---------------------------------------------------------------------------
# User endpoint tests
# ---------------------------------------------------------------------------

def test_register_user_route(client, monkeypatch):
    mocked = {
        "success": True,
        "user_id": "u1",
        "appwrite_id": "app1",
        "email": "user@example.com",
        "username": "user",
        "user_type": "user",
    }
    monkeypatch.setattr(user_routes, "create_user_mongo", lambda user: mocked)

    payload = {
        "username": "user",
        "email": "user@example.com",
        "password": "secret123",
        "user_type": "user",
    }

    response = client.post("/users/register", json=payload)

    assert response.status_code == 201
    assert response.json()["user"]["user_id"] == "u1"


def test_login_user_route(client, monkeypatch):
    mocked = {"success": True, "session_id": "s1", "user": {"user_id": "u1"}}
    monkeypatch.setattr(user_routes, "login_user_mongo", lambda creds: mocked)

    response = client.post("/users/login", json={"email": "user@example.com", "password": "secret123"})

    assert response.status_code == 200
    assert response.json()["session_id"] == "s1"


def test_get_user_profile_route(client, monkeypatch):
    mocked = {"success": True, "user": {"user_id": "u1"}}
    monkeypatch.setattr(user_routes, "get_user_by_id", lambda user_id: mocked)

    response = client.get("/users/profile/u1")

    assert response.status_code == 200
    assert response.json()["user_id"] == "u1"


def test_update_user_profile_route(client, monkeypatch):
    mocked = {"success": True, "message": "Profile updated"}
    monkeypatch.setattr(user_routes, "update_user_by_id", lambda user_id, data: mocked)

    response = client.put("/users/profile/u1", json={"username": "new"})

    assert response.status_code == 200
    assert response.json()["user_id"] == "u1"


def test_logout_user_route(client, monkeypatch):
    mocked = {"success": True, "message": "Logged out"}
    monkeypatch.setattr(user_routes, "logout_user", lambda session_id: mocked)

    response = client.post("/users/logout", json={"session_id": "s1"})

    assert response.status_code == 200
    assert response.json()["message"] == "Logged out"


def test_change_user_password_route(client, monkeypatch):
    mocked = {"success": True, "message": "Password changed"}
    monkeypatch.setattr(user_routes, "change_user_password", lambda *args, **kwargs: mocked)

    payload = {
        "appwrite_id": "app1",
        "email": "user@example.com",
        "current_password": "oldpass",
        "new_password": "newpass123",
    }

    response = client.post("/users/change-password", json=payload)

    assert response.status_code == 200
    assert response.json()["message"] == "Password changed"


def test_delete_user_account_route(client, monkeypatch):
    mocked = {"success": True, "message": "Deleted"}
    monkeypatch.setattr(user_routes, "delete_user_account", lambda appwrite_id, user_id: mocked)

    response = client.request("DELETE", "/users/delete", json={"appwrite_id": "app1", "user_id": "u1"})

    assert response.status_code == 200
    assert response.json()["message"] == "Deleted"


# ---------------------------------------------------------------------------
# User profile endpoint tests
# ---------------------------------------------------------------------------

def test_get_my_profile_route(client, monkeypatch):
    client.app.dependency_overrides[get_current_user] = lambda: {"sub": "u1"}
    monkeypatch.setattr(user_profile_routes, "get_user_profile", lambda user_id: {"user_id": user_id})
    try:
        response = client.get("/user-profile/me")
    finally:
        client.app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["user_id"] == "u1"


def test_update_my_profile_route(client, monkeypatch):
    client.app.dependency_overrides[get_current_user] = lambda: {"sub": "u1"}
    monkeypatch.setattr(user_profile_routes, "update_user_profile", lambda user_id, data: {"msg": "Profile updated"})
    try:
        response = client.put("/user-profile/me", json={"monthly_income": 150000})
    finally:
        client.app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["msg"] == "Profile updated"


def test_update_my_basic_info_route(client, monkeypatch):
    client.app.dependency_overrides[get_current_user] = lambda: {"sub": "u1"}
    monkeypatch.setattr(user_profile_routes, "update_basic_info", lambda user_id, username=None, email=None: {"msg": "Basic information updated successfully"})
    try:
        response = client.put("/user-profile/basic-info", json={"username": "user"})
    finally:
        client.app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["msg"] == "Basic information updated successfully"


def test_change_my_password_route(client, monkeypatch):
    client.app.dependency_overrides[get_current_user] = lambda: {"sub": "u1"}
    monkeypatch.setattr(user_profile_routes, "change_password", lambda *args, **kwargs: {"msg": "Password changed successfully"})
    payload = {
        "current_password": "oldpass",
        "new_password": "newpass",
        "confirm_password": "newpass",
    }
    try:
        response = client.post("/user-profile/change-password", json=payload)
    finally:
        client.app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["msg"] == "Password changed successfully"


def test_get_my_statistics_route(client, monkeypatch):
    client.app.dependency_overrides[get_current_user] = lambda: {"sub": "u1"}
    monkeypatch.setattr(user_profile_routes, "get_user_statistics", lambda user_id: {"total_comparisons": 1})
    try:
        response = client.get("/user-profile/statistics")
    finally:
        client.app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["total_comparisons"] == 1

