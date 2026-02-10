from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from .config import settings

# Fix Render.com PostgreSQL URL format
# Render gives: postgres://... but SQLAlchemy needs: postgresql+pg8000://...
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+pg8000://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+pg8000://", 1)

# Create database engine with connection pooling
engine = create_engine(
    database_url,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Test connection before using
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Dependency for FastAPI to provide database sessions
def get_db():
    """
    Database session dependency for FastAPI
    Usage: def my_endpoint(db: Session = Depends(get_db))
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
