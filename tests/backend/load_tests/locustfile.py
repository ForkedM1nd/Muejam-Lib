"""
Load testing scenarios for MueJam API using Locust

Run with:
    locust -f tests/load_tests/locustfile.py --host=http://localhost:8000

For headless mode:
    locust -f tests/load_tests/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
"""

import random
import time
from locust import HttpUser, task, between, SequentialTaskSet
from locust.exception import RescheduleTask


class AuthenticatedUser(HttpUser):
    """Simulates an authenticated user browsing the platform"""
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Setup - authenticate user"""
        # In real scenario, get valid JWT token from Clerk
        # For load testing, use test token or mock authentication
        self.token = self.get_test_token()
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        self.user_id = None
        self.story_slugs = []
    
    def get_test_token(self):
        """Get test JWT token - replace with actual token generation"""
        # For load testing, you'll need to generate valid tokens
        # or use a test endpoint that bypasses auth
        return "test_token_for_load_testing"
    
    @task(10)
    def browse_discovery(self):
        """Browse discovery feed - most common action"""
        with self.client.get(
            "/api/discovery/trending",
            headers=self.headers,
            catch_response=True,
            name="/api/discovery/trending"
        ) as response:
            if response.status_code == 200:
                response.success()
                # Extract story slugs for later use
                try:
                    data = response.json()
                    stories = data.get('results', [])
                    self.story_slugs = [s['slug'] for s in stories if 'slug' in s]
                except:
                    pass
            elif response.status_code == 429:
                # Rate limited - expected behavior
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(8)
    def view_story(self):
        """View a story - second most common action"""
        if not self.story_slugs:
            # If no stories cached, skip this task
            raise RescheduleTask()
        
        slug = random.choice(self.story_slugs)
        with self.client.get(
            f"/api/stories/{slug}",
            headers=self.headers,
            catch_response=True,
            name="/api/stories/[slug]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(5)
    def view_profile(self):
        """View user profile"""
        with self.client.get(
            "/api/users/me",
            headers=self.headers,
            catch_response=True,
            name="/api/users/me"
        ) as response:
            if response.status_code == 200:
                response.success()
                try:
                    data = response.json()
                    self.user_id = data.get('id')
                except:
                    pass
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(3)
    def browse_library(self):
        """Browse user's library"""
        with self.client.get(
            "/api/library/shelves",
            headers=self.headers,
            catch_response=True,
            name="/api/library/shelves"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(2)
    def search_stories(self):
        """Search for stories"""
        search_terms = ['fantasy', 'romance', 'adventure', 'mystery', 'scifi']
        query = random.choice(search_terms)
        
        with self.client.get(
            f"/api/search/stories?q={query}",
            headers=self.headers,
            catch_response=True,
            name="/api/search/stories"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(1)
    def create_whisper(self):
        """Create a whisper - write operation"""
        whisper_data = {
            'content': f'Test whisper at {time.time()}',
            'scope': 'public'
        }
        
        with self.client.post(
            "/api/whispers",
            json=whisper_data,
            headers=self.headers,
            catch_response=True,
            name="/api/whispers [POST]"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class UnauthenticatedUser(HttpUser):
    """Simulates an unauthenticated user browsing public content"""
    
    wait_time = between(2, 8)
    
    @task(10)
    def browse_public_stories(self):
        """Browse public stories"""
        with self.client.get(
            "/api/discovery/trending",
            catch_response=True,
            name="/api/discovery/trending [public]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(5)
    def view_public_story(self):
        """View a public story"""
        # Use a known public story slug or fetch from discovery
        with self.client.get(
            "/api/stories/sample-story",
            catch_response=True,
            name="/api/stories/[slug] [public]"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(2)
    def search_public(self):
        """Search public content"""
        search_terms = ['fantasy', 'romance', 'adventure']
        query = random.choice(search_terms)
        
        with self.client.get(
            f"/api/search/stories?q={query}",
            catch_response=True,
            name="/api/search/stories [public]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class WriterUser(HttpUser):
    """Simulates a writer creating and managing content"""
    
    wait_time = between(5, 15)  # Writers spend more time between actions
    
    def on_start(self):
        """Setup - authenticate user"""
        self.token = self.get_test_token()
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        self.story_id = None
    
    def get_test_token(self):
        """Get test JWT token"""
        return "test_writer_token"
    
    @task(5)
    def create_story(self):
        """Create a new story"""
        story_data = {
            'title': f'Test Story {time.time()}',
            'blurb': 'A test story for load testing',
            'genre': 'fantasy',
            'visibility': 'public'
        }
        
        with self.client.post(
            "/api/stories",
            json=story_data,
            headers=self.headers,
            catch_response=True,
            name="/api/stories [POST]"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
                try:
                    data = response.json()
                    self.story_id = data.get('id')
                except:
                    pass
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(3)
    def update_story(self):
        """Update story metadata"""
        if not self.story_id:
            raise RescheduleTask()
        
        update_data = {
            'blurb': f'Updated at {time.time()}'
        }
        
        with self.client.patch(
            f"/api/stories/{self.story_id}",
            json=update_data,
            headers=self.headers,
            catch_response=True,
            name="/api/stories/[id] [PATCH]"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")
    
    @task(2)
    def view_my_stories(self):
        """View own stories"""
        with self.client.get(
            "/api/stories/mine",
            headers=self.headers,
            catch_response=True,
            name="/api/stories/mine"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Got status {response.status_code}")


class HealthCheckUser(HttpUser):
    """Simulates load balancer health checks"""
    
    wait_time = between(1, 2)
    
    @task
    def health_check(self):
        """Health check endpoint"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="/health"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task
    def readiness_check(self):
        """Readiness check endpoint"""
        with self.client.get(
            "/health/ready",
            catch_response=True,
            name="/health/ready"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Readiness check failed: {response.status_code}")
