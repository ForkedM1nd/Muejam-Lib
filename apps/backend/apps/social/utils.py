"""Utility functions for social features."""
from prisma import Prisma


async def get_blocked_user_ids(user_id: str):
    """
    Get list of user IDs that the given user has blocked.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of blocked user IDs
        
    Requirements:
        - 11.5: Exclude blocked users from content feeds
        - 11.6: Exclude blocked users from search results
    """
    db = Prisma()
    await db.connect()
    
    try:
        blocks = await db.block.find_many(
            where={'blocker_id': user_id},
            select={'blocked_id': True}
        )
        
        blocked_ids = [b.blocked_id for b in blocks]
        
        await db.disconnect()
        return blocked_ids
        
    except Exception:
        await db.disconnect()
        return []


def sync_get_blocked_user_ids(user_id: str):
    """Synchronous wrapper for get_blocked_user_ids."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_blocked_user_ids(user_id))
