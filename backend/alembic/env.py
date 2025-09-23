import os
import sys
from logging.config import fileConfig
from app.db import models  # this ensures they’re registered with Base


from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Make 'app' importable ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# --- Load .env before importing settings ---
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env"))

# --- Alembic Config ---
config = context.config
fileConfig(config.config_file_name)

# --- Import app settings & metadata ---
from app.core.config import settings
from app.db.database import Base

target_metadata = Base.metadata

# --- Override DB URL from .env ---
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
