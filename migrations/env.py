from logging.config import fileConfig
import os

from sqlalchemy import create_engine # Alterado para usar create_engine diretamente
from sqlalchemy import pool

from alembic import context

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.database.models import Base
target_metadata = Base.metadata

from app.core.config import get_settings
settings = get_settings()

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# A linha abaixo não é mais necessária aqui, pois a URL será passada diretamente para create_engine
# config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

def run_migrations_offline():
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
    # Usamos create_engine diretamente com a URL das configurações da aplicação
    connectable = create_engine(
        settings.DATABASE_URL,
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

