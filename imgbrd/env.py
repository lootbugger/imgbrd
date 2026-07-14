from logging.config import fileConfig

from src.database import Base
import src.boards.models
import src.posts.models

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from alembic.operations.ops import AlterTableOp, CreateForeignKeyOp, DropConstraintOp

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

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


def process_revision_directives(context, revision, directives):
    def _walk_name_fks(ops, table_name_map=None, is_upgrade=True):
        if ops is None:
            return
        if not hasattr(ops, 'ops'):
            return
        for op in ops.ops:
            if isinstance(op, AlterTableOp) and hasattr(op, 'ops'):
                table = op.table_name
                names = []
                for bop in op.ops:
                    if isinstance(bop, CreateForeignKeyOp) and bop.constraint_name is None:
                        bop.constraint_name = f"fk_{bop.source_table}_{'_'.join(bop.local_cols)}"
                        names.append(bop.constraint_name)
                if is_upgrade and names:
                    table_name_map[table] = names
                elif not is_upgrade and table in table_name_map:
                    idx = 0
                    for bop in op.ops:
                        if isinstance(bop, DropConstraintOp) and bop.constraint_name is None and bop.type_ == 'foreignkey':
                            if idx < len(table_name_map[table]):
                                bop.constraint_name = table_name_map[table][idx]
                                idx += 1
            elif hasattr(op, 'ops'):
                _walk_name_fks(op, table_name_map, is_upgrade)

    table_name_map = {}
    for directive in directives:
        _walk_name_fks(directive.upgrade_ops, table_name_map, is_upgrade=True)
        _walk_name_fks(directive.downgrade_ops, table_name_map, is_upgrade=False)


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
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True, process_revision_directives=process_revision_directives)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
