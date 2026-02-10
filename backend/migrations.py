"""
Database schema migration utilities
Handles adding missing columns and updating existing tables to match models
"""
from sqlalchemy import inspect, text, Column, JSON
from sqlalchemy.engine import Engine
from pgvector.sqlalchemy import Vector
import logging

logger = logging.getLogger(__name__)

def sync_schema(engine: Engine, Base):
    """
    Synchronize database schema with SQLAlchemy models.
    Adds missing columns to existing tables (doesn't drop columns).
    
    This is a simple migration approach. For production, consider Alembic.
    """
    inspector = inspect(engine)
    
    # Ensure pgvector extension exists
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("✓ pgvector extension verified")
    except Exception as e:
        logger.warning(f"Could not create pgvector extension (might already exist): {e}")
    
    # Get all tables defined in models
    for table_name, table in Base.metadata.tables.items():
        # Check if table exists in database
        if inspector.has_table(table_name):
            logger.info(f"Checking table '{table_name}' for missing columns...")
            
            # Get columns from database
            db_columns = {col['name'] for col in inspector.get_columns(table_name)}
            logger.info(f"  Existing columns in DB: {sorted(db_columns)}")
            
            # Get columns from model
            model_columns = {col.name for col in table.columns}
            logger.info(f"  Required columns in model: {sorted(model_columns)}")
            
            # Find missing columns
            missing_columns = model_columns - db_columns
            
            if missing_columns:
                logger.warning(f"⚠ Found {len(missing_columns)} missing column(s) in '{table_name}': {missing_columns}")
                
                with engine.connect() as conn:
                    trans = conn.begin()
                    try:
                        for col_name in missing_columns:
                            col = table.columns[col_name]
                            add_column_sql = generate_add_column_sql(table_name, col)
                            logger.info(f"  → Executing: {add_column_sql}")
                            try:
                                conn.execute(text(add_column_sql))
                                logger.info(f"  ✓ Successfully added column '{col_name}'")
                            except Exception as col_error:
                                # Check if column already exists (race condition)
                                if 'already exists' in str(col_error).lower() or 'duplicate' in str(col_error).lower():
                                    logger.info(f"  → Column '{col_name}' already exists, skipping")
                                else:
                                    logger.error(f"  ✗ Failed to add column '{col_name}': {col_error}")
                                    raise
                        trans.commit()
                        logger.info(f"✓ Successfully updated table '{table_name}'")
                    except Exception as e:
                        trans.rollback()
                        logger.error(f"✗ Failed to update table '{table_name}': {e}")
                        logger.error(f"  Error details: {type(e).__name__}: {str(e)}")
                        raise
            else:
                logger.info(f"✓ Table '{table_name}' is up to date")
        else:
            logger.info(f"Table '{table_name}' does not exist. It will be created by create_all()")

def generate_add_column_sql(table_name: str, column) -> str:
    """Generate ALTER TABLE ADD COLUMN SQL statement"""
    col_name = column.name
    col_type = get_sql_type(column.type)
    
    nullable = "NULL" if column.nullable else "NOT NULL"
    
    # For nullable columns, we can add without default
    # For non-nullable columns without defaults, we might need special handling
    sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{col_name}" {col_type}'
    
    # Add default value if specified
    if column.default is not None:
        if hasattr(column.default, 'arg'):
            default_value = column.default.arg
            if callable(default_value):
                # Handle callable defaults (like datetime.utcnow)
                # For JSON columns, default to NULL or empty object
                if 'JSON' in col_type or 'json' in col_type.lower():
                    sql += " DEFAULT '{}'::jsonb"
                else:
                    sql += " DEFAULT NULL"
            elif isinstance(default_value, str):
                sql += f" DEFAULT '{default_value}'"
            else:
                sql += f" DEFAULT {default_value}"
        else:
            sql += f" {nullable}"
    else:
        sql += f" {nullable}"
    
    return sql

def get_sql_type(sqlalchemy_type):
    """Convert SQLAlchemy type to PostgreSQL SQL type"""
    type_name = type(sqlalchemy_type).__name__
    type_str = str(type(sqlalchemy_type))
    
    # Handle Vector type (pgvector) - check this first
    if 'Vector' in type_str or 'vector' in type_str.lower():
        dimensions = 384  # default
        if hasattr(sqlalchemy_type, 'dimensions'):
            dimensions = sqlalchemy_type.dimensions
        elif hasattr(sqlalchemy_type, 'length'):
            dimensions = sqlalchemy_type.length
        logger.debug(f"Detected Vector type with {dimensions} dimensions")
        return f'vector({dimensions})'
    
    type_mapping = {
        'Integer': 'INTEGER',
        'Text': 'TEXT',
        'Float': 'DOUBLE PRECISION',
        'DateTime': 'TIMESTAMP WITHOUT TIME ZONE',
        'Boolean': 'BOOLEAN',
        'JSON': 'JSONB',  # Use JSONB for better performance in PostgreSQL
    }
    
    # Handle String with length
    if type_name == 'String':
        length = sqlalchemy_type.length if hasattr(sqlalchemy_type, 'length') else 255
        return f'VARCHAR({length})'
    
    # Handle custom types
    if type_name in type_mapping:
        return type_mapping[type_name]
    
    # Fallback to string representation
    logger.warning(f"Unknown SQLAlchemy type: {type_name}, using string representation")
    return str(sqlalchemy_type)

