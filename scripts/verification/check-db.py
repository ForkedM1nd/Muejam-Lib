#!/usr/bin/env python3
"""
Database connectivity and schema verification script.

Usage:
    cd apps/backend
    python ../../scripts/verification/check-db.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path for Django imports
backend_path = Path(__file__).parent.parent.parent / 'apps' / 'backend'
sys.path.insert(0, str(backend_path))

from prisma import Prisma

async def check_tables():
    db = Prisma()
    await db.connect()
    
    try:
        # Check Story table
        story_count = await db.story.count()
        print(f"✓ Story table exists with {story_count} records")
        
        # Check User table
        user_count = await db.userprofile.count()
        print(f"✓ UserProfile table exists with {user_count} records")
        
        # Check Chapter table
        chapter_count = await db.chapter.count()
        print(f"✓ Chapter table exists with {chapter_count} records")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(check_tables())
