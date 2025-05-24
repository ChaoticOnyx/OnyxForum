from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
import sys
import os

# Добавляем корень проекта в sys.path, чтобы импортировать приложение
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импортируем create_app и db из твоего Flask-проекта
from flaskbb import create_app
from flaskbb.extensions import db

config = context.config
fileConfig(config.config_file_name)

# Создаём приложение и активируем контекст
app = create_app()

# Здесь указываем метаданные моделей, которые Alembic будет использовать
with app.app_context():
    # код, где нужен контекст (например, получение target_metadata)
    target_metadata = db.metadata


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
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,             # полезно для отслеживания изменений типов
            compare_server_default=True,   # отслеживать изменения default
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
