from datetime import datetime
from prisma import Prisma
from prisma.models import OnboardingProgress


class OnboardingService:
    """Service for managing user onboarding progress"""
    
    @staticmethod
    async def get_or_create_progress(user_id: str) -> OnboardingProgress:
        """Get or create onboarding progress for a user"""
        db = Prisma()
        await db.connect()
        
        try:
            progress = await db.onboardingprogress.find_unique(
                where={'user_id': user_id}
            )
            
            if not progress:
                progress = await db.onboardingprogress.create(
                    data={'user_id': user_id}
                )
            
            return progress
        finally:
            await db.disconnect()
    
    @staticmethod
    async def update_step(user_id: str, step: str) -> OnboardingProgress:
        """Update a specific onboarding step"""
        db = Prisma()
        await db.connect()
        
        try:
            # Get or create progress
            progress = await OnboardingService.get_or_create_progress(user_id)
            
            # Update the specific step
            update_data = {step: True}
            
            # If it's a follow, increment the counter
            if step == 'first_follow':
                current_count = progress.authors_followed_count or 0
                update_data['authors_followed_count'] = current_count + 1
            
            # Update progress
            progress = await db.onboardingprogress.update(
                where={'user_id': user_id},
                data=update_data
            )
            
            # Check if onboarding is complete
            await OnboardingService.check_completion(user_id)
            
            # Fetch updated progress
            progress = await db.onboardingprogress.find_unique(
                where={'user_id': user_id}
            )
            
            return progress
        finally:
            await db.disconnect()
    
    @staticmethod
    async def check_completion(user_id: str) -> bool:
        """Check if onboarding is complete and update if so"""
        db = Prisma()
        await db.connect()
        
        try:
            progress = await db.onboardingprogress.find_unique(
                where={'user_id': user_id}
            )
            
            if not progress or progress.onboarding_completed:
                return progress.onboarding_completed if progress else False
            
            # Onboarding is complete when:
            # - Profile is completed
            # - User has followed 3 authors
            # - User has read 1 story
            is_complete = (
                progress.profile_completed and
                progress.authors_followed_count >= 3 and
                progress.first_story_read
            )
            
            if is_complete and not progress.onboarding_completed:
                await db.onboardingprogress.update(
                    where={'user_id': user_id},
                    data={
                        'onboarding_completed': True,
                        'completed_at': datetime.utcnow()
                    }
                )
            
            return is_complete
        finally:
            await db.disconnect()
    
    @staticmethod
    async def skip_onboarding(user_id: str) -> OnboardingProgress:
        """Mark onboarding as complete (user skipped)"""
        db = Prisma()
        await db.connect()
        
        try:
            progress = await db.onboardingprogress.upsert(
                where={'user_id': user_id},
                data={
                    'create': {
                        'user_id': user_id,
                        'onboarding_completed': True,
                        'completed_at': datetime.utcnow()
                    },
                    'update': {
                        'onboarding_completed': True,
                        'completed_at': datetime.utcnow()
                    }
                }
            )
            
            return progress
        finally:
            await db.disconnect()
