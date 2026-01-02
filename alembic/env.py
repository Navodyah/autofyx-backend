from logging.config import fileConfig


from sqlalchemy import engine_from_config
from sqlalchemy import pool


from alembic import context


from config.postgresql import Base


from models.brand import Brand
from models.car_model import Model
from models.engine import EngineType
from models.fuel import FuelType
from models.maintenance import MaintenanceCost
from models.oil import OilQuality
from models.transmission import Transmission
from models.vehicle import Vehicle
from models.vehicle_class import VehicleClass


from dotenv import load_dotenv
import os


load_dotenv()


config = context.config


config.set_main_option(
   "sqlalchemy.url",
   f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
   f"@{os.getenv('POSTGRES_SERVER')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
)


# Must be Base.metadata, NOT None
target_metadata = Base.metadata


if config.config_file_name is not None:
   fileConfig(config.config_file_name)




def run_migrations_offline() -> None:
   url = config.get_main_option("sqlalchemy.url")
   context.configure(
       url=url,
       target_metadata=target_metadata,
       literal_binds=True,
       dialect_opts={"paramstyle": "named"},
   )


   with context.begin_transaction():
       context.run_migrations()




def run_migrations_online() -> None:
   connectable = engine_from_config(
       config.get_section(config.config_ini_section, {}),
       prefix="sqlalchemy.",
       poolclass=pool.NullPool,
   )


   with connectable.connect() as connection:
       context.configure(
           connection=connection,
           target_metadata=target_metadata,
       )


       with context.begin_transaction():
           context.run_migrations()




if context.is_offline_mode():
   run_migrations_offline()
else:
   run_migrations_online()














