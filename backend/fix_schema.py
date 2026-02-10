"""
Standalone script to fix database schema issues
Run this manually if schema sync fails during startup
"""
import logging
from .database import engine, Base
from migrations import sync_schema

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Database Schema Fix Script")
    logger.info("=" * 60)
    
    try:
        logger.info("Starting schema synchronization...")
        sync_schema(engine, Base)
        logger.info("=" * 60)
        logger.info("✓ Schema synchronization completed successfully!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ Schema synchronization failed: {e}")
        logger.error(f"  Error type: {type(e).__name__}")
        import traceback
        logger.error(f"  Traceback:\n{traceback.format_exc()}")
        logger.error("=" * 60)
        exit(1)

