"""
Initialization script for content filter configurations.

Run this script to set up default filter configurations in the database.
This should be run once during deployment or when setting up a new environment.
"""

import asyncio
from prisma import Prisma
from apps.moderation.filter_config_service import FilterConfigService


async def initialize_filters():
    """Initialize default content filter configurations."""
    print("Initializing content filter configurations...")
    
    db = Prisma()
    await db.connect()
    
    try:
        config_service = FilterConfigService(db)
        await config_service.initialize_default_configs()
        
        print("✓ Default filter configurations created successfully")
        print("\nDefault configurations:")
        print("  - Profanity Filter: MODERATE sensitivity, ENABLED")
        print("  - Spam Detector: MODERATE sensitivity, ENABLED")
        print("  - Hate Speech Detector: MODERATE sensitivity, ENABLED")
        print("\nYou can update these configurations through the admin API.")
        
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(initialize_filters())
