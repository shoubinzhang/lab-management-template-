from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入模型
from database import Base
from models import *  # 导入所有模型

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# 从环境变量获取数据库URL
config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL', 'sqlite:///./lab_management.db'))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

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
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    
    # 获取数据库配置
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = os.getenv('DATABASE_URL', 'sqlite:///./lab_management.db')
    
    # 根据数据库类型设置不同的配置
    database_url = configuration['sqlalchemy.url']
    
    if 'postgresql' in database_url:
        # PostgreSQL配置
        configuration.update({
            'sqlalchemy.pool_size': os.getenv('DB_POOL_SIZE', '5'),
            'sqlalchemy.max_overflow': os.getenv('DB_MAX_OVERFLOW', '10'),
            'sqlalchemy.pool_timeout': os.getenv('DB_POOL_TIMEOUT', '30'),
            'sqlalchemy.pool_recycle': '3600',
            'sqlalchemy.pool_pre_ping': 'true',
        })
    elif 'mysql' in database_url:
        # MySQL配置
        configuration.update({
            'sqlalchemy.pool_size': os.getenv('DB_POOL_SIZE', '5'),
            'sqlalchemy.max_overflow': os.getenv('DB_MAX_OVERFLOW', '10'),
            'sqlalchemy.pool_timeout': os.getenv('DB_POOL_TIMEOUT', '30'),
            'sqlalchemy.pool_recycle': '3600',
            'sqlalchemy.pool_pre_ping': 'true',
        })
    else:
        # SQLite配置
        configuration.update({
            'sqlalchemy.connect_args': '{"check_same_thread": False}',
            'sqlalchemy.poolclass': 'StaticPool',
        })
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # 包含表名模式匹配
            include_schemas=True,
            # 渲染项目
            render_as_batch=True if 'sqlite' in database_url else False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()