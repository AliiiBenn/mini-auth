import os
import sys
from logging.config import fileConfig
from urllib.parse import urlparse, parse_qs, urlunparse

# Import create_engine explicitly
from sqlalchemy import engine_from_config, create_engine 
from sqlalchemy import pool
from sqlalchemy import MetaData

from alembic import context

# Import models directly, but avoid importing Base from database
# to prevent triggering FastAPI app config loading during migration generation.
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
# from src.core.database import Base # REMOVED
# Import models, trying Project before User to potentially resolve circular import.
from src.models.project import Project, ProjectApiKey, ProjectMember
from src.models.user import User, RefreshToken

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Read the database URL from the environment variable for offline mode directly
# This avoids importing the full FastAPI config during Alembic execution if possible
DB_URL_ENV_VAR = "ALEMBIC_DATABASE_URL"

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Define target_metadata using MetaData directly
# Alembic will implicitly pick up metadata from imported models.
target_metadata = MetaData() 

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use the environment variable directly for offline mode
    db_url = os.getenv(DB_URL_ENV_VAR)
    if not db_url:
        raise ValueError(f"Environment variable {DB_URL_ENV_VAR} not set for offline migration.")
    
    # Clean URL for offline mode just in case
    parsed_url = urlparse(db_url)
    # Ensure scheme is correct for offline mode (psycopg2 might not be needed here, but consistency is good)
    offline_scheme = parsed_url.scheme.split('+')[0] # Get base scheme (e.g., postgresql)
    cleaned_url = urlunparse(parsed_url._replace(scheme=offline_scheme, query=''))

    context.configure(
        url=cleaned_url, # Use cleaned URL
        target_metadata=target_metadata, 
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include schemas associated with MetaData if needed, especially for PostgreSQL
        # We need to tell Alembic about the schema associated with our MetaData
        # if our tables have explicit schema names, or if using non-default schema.
        # For now, assuming default public schema.
        # include_schemas=True # Uncomment if you use non-default schemas
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Read URL directly from environment variable
    db_url = os.getenv(DB_URL_ENV_VAR)
    if not db_url:
        raise ValueError(f"Environment variable {DB_URL_ENV_VAR} not set for online migration.")

    # Parse the URL to extract connect_args like sslmode
    parsed_url = urlparse(db_url)
    query_params = parse_qs(parsed_url.query)
    connect_args = {}
    if 'sslmode' in query_params:
        # psycopg2 uses sslmode directly in connect_args
        connect_args["sslmode"] = query_params['sslmode'][0]

    # Rebuild the URL without the query string AND force the psycopg2 dialect
    # Ensure the original scheme doesn't contain +asyncpg etc.
    engine_url = urlunparse(parsed_url._replace(scheme='postgresql+psycopg2', query=''))

    # Create engine manually using the forced dialect URL and connect_args
    connectable = create_engine(
        engine_url, # Use URL with forced dialect
        poolclass=pool.NullPool,
        connect_args=connect_args
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # Include schemas associated with MetaData if needed
            # include_schemas=True # Uncomment if you use non-default schemas
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
