"""Utility functions for user management."""
import logging
from prisma import Prisma

logger = logging.getLogger(__name__)


async def get_or_create_profile(clerk_user_id: str):
    """
    Get or create a UserProfile for the given Clerk user ID.
    
    This function is used by the ClerkAuthMiddleware to ensure that
    every authenticated Clerk user has a corresponding UserProfile in the database.
    
    Args:
        clerk_user_id: The Clerk user ID from the verified JWT token
        
    Returns:
        UserProfile instance or None if creation fails
        
    Requirements:
        - 1.2: Create or retrieve UserProfile using clerk_user_id
        - 1.5: Enforce handle format (alphanumeric with underscores, 3-30 chars)
    """
    db = Prisma()
    await db.connect()
    
    try:
        # Try to find existing profile
        profile = await db.userprofile.find_unique(
            where={'clerk_user_id': clerk_user_id}
        )
        
        if profile:
            await db.disconnect()
            return profile
        
        # Create new profile with default values
        # Generate a default handle from clerk_user_id (first 8 chars)
        default_handle = f"user_{clerk_user_id[:8]}"
        
        # Ensure handle uniqueness by appending numbers if needed
        handle = default_handle
        counter = 1
        while await db.userprofile.find_unique(where={'handle': handle}):
            handle = f"{default_handle}_{counter}"
            counter += 1
        
        profile = await db.userprofile.create(
            data={
                'clerk_user_id': clerk_user_id,
                'handle': handle,
                'display_name': f"User {clerk_user_id[:8]}",
            }
        )
        
        logger.info(f"Created new UserProfile for clerk_user_id: {clerk_user_id}")
        await db.disconnect()
        return profile
        
    except Exception as e:
        logger.error(f"Error in get_or_create_profile: {e}")
        await db.disconnect()
        return None
