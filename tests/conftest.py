from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

# Provide safe defaults so config.postgresql imports cleanly during tests.
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test_db")
os.environ.setdefault("DB_USER", "test_user")
os.environ.setdefault("DB_PASSWORD", "test_password")
os.environ.setdefault("MONGODB", "mongodb://localhost:27017/test_db")
os.environ.setdefault("ADMIN_TOKEN", "test-admin-token")

from config.postgresql import get_db
from routes.brand_routes import router as brand_router
from routes.compare_routes import router as compare_router
from routes.lookup_routes import router as lookup_router
from routes.recommender_routes import router as recommender_router
from routes.vehicle_routes import router as vehicle_router
from routes.engine_routes import router as engine_router
from routes.fuel_routes import router as fuel_router
from routes.maintenance_routes import router as maintenance_router
from routes.model_routes import router as model_router
from routes.oil_routes import router as oil_router
from routes.researcher_analytics_routes import router as researcher_analytics_router
from routes.transmission_routes import router as transmission_router
from routes.user_routes import router as user_router
from routes.user_profile_routes import router as user_profile_router
from routes.vehicle_class_routes import router as vehicle_class_router


async def override_get_db():
    yield object()


@pytest.fixture()
def app():
    app = FastAPI()
    app.include_router(lookup_router)
    app.include_router(brand_router)
    app.include_router(vehicle_router)
    app.include_router(compare_router)
    app.include_router(recommender_router)
    app.include_router(engine_router)
    app.include_router(fuel_router)
    app.include_router(maintenance_router)
    app.include_router(model_router)
    app.include_router(oil_router)
    app.include_router(researcher_analytics_router)
    app.include_router(transmission_router)
    app.include_router(vehicle_class_router)
    app.include_router(user_router)
    app.include_router(user_profile_router)
    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture()
def client(app):
    return TestClient(app)
