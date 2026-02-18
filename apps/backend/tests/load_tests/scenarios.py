"""
Specific load test scenarios for different use cases
"""

from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask
import random
import time


class RateLimitTestUser(HttpUser):
    """Test rate limiting behavior under load"""
    
    wait_time = between(0.1, 0.5)  # Very fast requests to trigger rate limits
    
    def on_start(self):
        self.token = "test_token"
        self.headers = {'Authorization': f'Bearer {self.token}'}
        self.rate_limited_count = 0
    
    @task
    def rapid_requests(self):
        """Make rapid requests to test rate limiting"""
        with self.client.get(
            "/api/discovery/trending",
            headers=self.headers,
            catch_response=True,
            name="Rate Limit Test"
        ) as response:
            if response.status_code == 429:
                self.rate_limited_count += 1
                response.success()  # Expected behavior
            elif response.status_code == 200:
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class DatabaseStressUser(HttpUser):
    """Test database connection pooling and query performance"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        self.token = "test_token"
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    @task(5)
    def complex_query(self):
        """Endpoint with complex database queries"""
        with self.client.get(
            "/api/discovery/trending?page_size=50",
            headers=self.headers,
            catch_response=True,
            name="Complex Query"
        ) as response:
            if response.status_code == 200:
                # Check response time
                if response.elapsed.total_seconds() > 1.0:
                    response.failure(f"Slow query: {response.elapsed.total_seconds()}s")
                else:
                    response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(3)
    def nested_query(self):
        """Endpoint with nested relationships"""
        with self.client.get(
            "/api/library/shelves",
            headers=self.headers,
            catch_response=True,
            name="Nested Query"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(2)
    def search_query(self):
        """Full-text search query"""
        query = random.choice(['fantasy', 'romance', 'adventure', 'mystery'])
        with self.client.get(
            f"/api/search/stories?q={query}",
            headers=self.headers,
            catch_response=True,
            name="Search Query"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class CacheTestUser(HttpUser):
    """Test caching behavior and cache hit rates"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        self.token = "test_token"
        self.headers = {'Authorization': f'Bearer {self.token}'}
        # Use same handles to test cache hits
        self.test_handles = ['user1', 'user2', 'user3', 'user4', 'user5']
    
    @task(10)
    def cached_profile_lookup(self):
        """Test profile caching by handle"""
        handle = random.choice(self.test_handles)
        with self.client.get(
            f"/api/users/{handle}",
            headers=self.headers,
            catch_response=True,
            name="Cached Profile Lookup"
        ) as response:
            if response.status_code == 200:
                # Check for cache hit header
                if 'X-Cache-Hit' in response.headers:
                    response.success()
                else:
                    response.success()
            elif response.status_code == 404:
                response.success()  # User doesn't exist
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(5)
    def cached_story_lookup(self):
        """Test story metadata caching"""
        # Use same slugs to test cache hits
        slug = f"test-story-{random.randint(1, 10)}"
        with self.client.get(
            f"/api/stories/{slug}",
            headers=self.headers,
            catch_response=True,
            name="Cached Story Lookup"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class WriteHeavyUser(HttpUser):
    """Test write-heavy workload (creates, updates, deletes)"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        self.token = "test_token"
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        self.created_ids = []
    
    @task(5)
    def create_whisper(self):
        """Create whisper"""
        data = {
            'content': f'Load test whisper {time.time()}',
            'scope': 'public'
        }
        with self.client.post(
            "/api/whispers",
            json=data,
            headers=self.headers,
            catch_response=True,
            name="Create Whisper"
        ) as response:
            if response.status_code in [200, 201]:
                try:
                    whisper_id = response.json().get('id')
                    if whisper_id:
                        self.created_ids.append(whisper_id)
                except:
                    pass
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(3)
    def update_whisper(self):
        """Update whisper"""
        if not self.created_ids:
            raise RescheduleTask()
        
        whisper_id = random.choice(self.created_ids)
        data = {'content': f'Updated at {time.time()}'}
        
        with self.client.patch(
            f"/api/whispers/{whisper_id}",
            json=data,
            headers=self.headers,
            catch_response=True,
            name="Update Whisper"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [404, 429]:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(2)
    def create_story(self):
        """Create story"""
        data = {
            'title': f'Load Test Story {time.time()}',
            'blurb': 'Testing write performance',
            'genre': 'fantasy'
        }
        with self.client.post(
            "/api/stories",
            json=data,
            headers=self.headers,
            catch_response=True,
            name="Create Story"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class TimeoutTestUser(HttpUser):
    """Test request timeout handling"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        self.token = "test_token"
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    @task
    def slow_endpoint(self):
        """Test endpoint that might timeout"""
        with self.client.get(
            "/api/discovery/trending?page_size=100",
            headers=self.headers,
            catch_response=True,
            name="Timeout Test",
            timeout=35  # Slightly longer than server timeout
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 504:
                # Gateway timeout - expected for slow queries
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


class HealthCheckLoadUser(HttpUser):
    """Simulate load balancer health checks"""
    
    wait_time = between(1, 2)
    
    @task(10)
    def health_check(self):
        """Health check endpoint"""
        with self.client.get(
            "/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                # Verify response structure
                try:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        response.success()
                    else:
                        response.failure(f"Unhealthy: {data}")
                except:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(5)
    def readiness_check(self):
        """Readiness check endpoint"""
        with self.client.get(
            "/health/ready",
            catch_response=True,
            name="Readiness Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(5)
    def liveness_check(self):
        """Liveness check endpoint"""
        with self.client.get(
            "/health/live",
            catch_response=True,
            name="Liveness Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("\nLoad test completed!")
    print(f"Total requests: {environment.stats.total.num_requests}")
    print(f"Total failures: {environment.stats.total.num_failures}")
    print(f"Average response time: {environment.stats.total.avg_response_time:.2f}ms")
    print(f"RPS: {environment.stats.total.total_rps:.2f}")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Called for each request"""
    # Log slow requests
    if response_time > 1000:  # > 1 second
        print(f"SLOW REQUEST: {name} took {response_time:.2f}ms")
