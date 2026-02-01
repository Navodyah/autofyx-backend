
import os
from contextlib import asynccontextmanager
from os import close

from flask.cli import load_dotenv

load_dotenv()


from fastapi import FastAPI,Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from config.mongodb import connect_to_mongodb, close_mongodb_connection

from routes.user_routes import router as user_router
from routes.brand_routes import router as brand_router
from routes.model_routes import router as model_router

from routes.engine_routes import router as engine_router
from routes.fuel_routes import router as fuel_router

from routes.maintenance_routes import router as maintenance_router
from routes.oil_routes import router as oil_router

from routes.transmission_routes import router as transmission_router

from routes.vehicle_routes import router as vehicle_router
from routes.vehicle_class_routes import router as vehicle_class_router
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_to_mongodb()
    yield
    close_mongodb_connection()

app = FastAPI(lifespan=lifespan)

app = FastAPI(title="Autofyx API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default port
        "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error: {exc.errors()}")
    print(f"Request body: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

app.include_router(user_router)

app.include_router(brand_router)



app.include_router(model_router)



app.include_router(engine_router)


app.include_router(fuel_router)


app.include_router(maintenance_router)


app.include_router(oil_router)



app.include_router(transmission_router)



app.include_router(vehicle_router)



app.include_router(vehicle_class_router)
