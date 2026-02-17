"""
Seed script for development data.

Usage:
    python seed_data.py
"""
import asyncio
from prisma import Prisma
from datetime import datetime, timedelta
import random


async def seed_database():
    """Seed the database with sample data for development."""
    db = Prisma()
    await db.connect()
    
    print("🌱 Seeding database...")
    
    try:
        # Create sample users
        print("Creating sample users...")
        users = []
        for i in range(5):
            user = await db.userprofile.create(
                data={
                    'clerk_user_id': f'clerk_user_{i}',
                    'handle': f'user{i}',
                    'display_name': f'Sample User {i}',
                    'bio': f'This is a sample user bio for user {i}.',
                }
            )
            users.append(user)
        
        # Create sample tags
        print("Creating sample tags...")
        tags = []
        tag_names = ['fantasy', 'scifi', 'romance', 'mystery', 'thriller', 'adventure']
        for tag_name in tag_names:
            tag = await db.tag.create(
                data={
                    'name': tag_name,
                    'slug': tag_name.lower(),
                }
            )
            tags.append(tag)
        
        # Create sample stories
        print("Creating sample stories...")
        stories = []
        for i in range(10):
            author = random.choice(users)
            story = await db.story.create(
                data={
                    'slug': f'sample-story-{i}',
                    'title': f'Sample Story {i}',
                    'blurb': f'This is a sample story blurb for story {i}. It contains interesting content.',
                    'author_id': author.id,
                    'published': i < 7,  # First 7 are published
                    'published_at': datetime.now() - timedelta(days=i) if i < 7 else None,
                }
            )
            stories.append(story)
            
            # Add tags to story
            story_tags = random.sample(tags, k=random.randint(1, 3))
            for tag in story_tags:
                await db.storytag.create(
                    data={
                        'story_id': story.id,
                        'tag_id': tag.id,
                    }
                )
        
        # Create sample chapters
        print("Creating sample chapters...")
        for story in stories[:7]:  # Only for published stories
            for chapter_num in range(1, random.randint(3, 6)):
                await db.chapter.create(
                    data={
                        'story_id': story.id,
                        'chapter_number': chapter_num,
                        'title': f'Chapter {chapter_num}',
                        'content': f'# Chapter {chapter_num}\n\nThis is sample content for chapter {chapter_num}. ' * 10,
                        'published': True,
                        'published_at': datetime.now() - timedelta(days=chapter_num),
                    }
                )
        
        # Create sample whispers
        print("Creating sample whispers...")
        for i in range(20):
            user = random.choice(users)
            scope = random.choice(['GLOBAL', 'STORY'])
            story_id = random.choice(stories).id if scope == 'STORY' else None
            
            await db.whisper.create(
                data={
                    'user_id': user.id,
                    'content': f'This is sample whisper {i}. #sample #test',
                    'scope': scope,
                    'story_id': story_id,
                }
            )
        
        # Create sample follows
        print("Creating sample follows...")
        for user in users:
            # Each user follows 2-3 other users
            others = [u for u in users if u.id != user.id]
            to_follow = random.sample(others, k=random.randint(2, 3))
            for followed in to_follow:
                try:
                    await db.follow.create(
                        data={
                            'follower_id': user.id,
                            'following_id': followed.id,
                        }
                    )
                except:
                    pass  # Skip if already exists
        
        # Create sample shelves
        print("Creating sample shelves...")
        for user in users:
            shelf = await db.shelf.create(
                data={
                    'user_id': user.id,
                    'name': 'My Favorites',
                }
            )
            
            # Add some stories to shelf
            for story in random.sample(stories[:7], k=3):
                await db.shelfitem.create(
                    data={
                        'shelf_id': shelf.id,
                        'story_id': story.id,
                    }
                )
        
        print("✅ Database seeded successfully!")
        print(f"   - {len(users)} users")
        print(f"   - {len(tags)} tags")
        print(f"   - {len(stories)} stories")
        print(f"   - ~{len(stories[:7]) * 4} chapters")
        print(f"   - 20 whispers")
        print(f"   - ~{len(users) * 2} follows")
        print(f"   - {len(users)} shelves")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        raise
    finally:
        await db.disconnect()


if __name__ == '__main__':
    asyncio.run(seed_database())
