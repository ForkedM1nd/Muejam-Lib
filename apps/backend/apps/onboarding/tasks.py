from celery import shared_task
from datetime import datetime, timedelta
from prisma import Prisma
from apps.notifications.email_service import EmailNotificationService


@shared_task
def send_onboarding_followup_emails():
    """
    Send follow-up emails to users who haven't completed onboarding
    after 24 hours of signup.
    """
    import asyncio
    asyncio.run(_send_onboarding_followup_emails())


async def _send_onboarding_followup_emails():
    """Async implementation of onboarding follow-up emails"""
    db = Prisma()
    await db.connect()
    
    try:
        # Find users who signed up 24 hours ago and haven't completed onboarding
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Get incomplete onboarding progress records
        incomplete_progress = await db.onboardingprogress.find_many(
            where={
                'onboarding_completed': False,
                'created_at': {
                    'lte': cutoff_time
                }
            },
            include={'user': True}
        )
        
        email_service = EmailNotificationService()
        
        for progress in incomplete_progress:
            if not progress.user:
                continue
            
            # Get user email from Clerk or database
            user_email = progress.user.email if hasattr(progress.user, 'email') else None
            
            if user_email:
                # Send follow-up email
                await email_service.send_onboarding_followup(
                    user_email=user_email,
                    display_name=progress.user.display_name,
                    progress_data={
                        'profile_completed': progress.profile_completed,
                        'interests_selected': progress.interests_selected,
                        'tutorial_completed': progress.tutorial_completed,
                    }
                )
        
        print(f"Sent {len(incomplete_progress)} onboarding follow-up emails")
        
    finally:
        await db.disconnect()
