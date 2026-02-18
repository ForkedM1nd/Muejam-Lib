#!/bin/bash

# Load Testing Script for MueJam API
# This script runs various load test scenarios and generates reports

set -e

# Configuration
HOST="${LOAD_TEST_HOST:-http://localhost:8000}"
RESULTS_DIR="./load_test_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${GREEN}=== MueJam Load Testing Suite ===${NC}"
echo "Target: $HOST"
echo "Results directory: $RESULTS_DIR"
echo ""

# Function to run a load test
run_test() {
    local test_name=$1
    local locustfile=$2
    local users=$3
    local spawn_rate=$4
    local run_time=$5
    local description=$6
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    echo "Description: $description"
    echo "Users: $users, Spawn rate: $spawn_rate, Duration: $run_time"
    echo ""
    
    local output_prefix="$RESULTS_DIR/${TIMESTAMP}_${test_name}"
    
    locust -f "$locustfile" \
        --host="$HOST" \
        --users="$users" \
        --spawn-rate="$spawn_rate" \
        --run-time="$run_time" \
        --headless \
        --html="${output_prefix}.html" \
        --csv="${output_prefix}" \
        --loglevel INFO
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $test_name completed successfully${NC}"
    else
        echo -e "${RED}✗ $test_name failed${NC}"
        return 1
    fi
    echo ""
}

# Test 1: Basic Load Test (100 concurrent users)
run_test \
    "basic_load" \
    "locustfile.py" \
    100 \
    10 \
    "5m" \
    "Normal traffic patterns with mixed user types"

# Test 2: Rate Limiting Test
run_test \
    "rate_limiting" \
    "scenarios.py" \
    50 \
    25 \
    "3m" \
    "Test rate limiting behavior with rapid requests" \
    --user-classes RateLimitTestUser

# Test 3: Database Stress Test
run_test \
    "database_stress" \
    "scenarios.py" \
    100 \
    20 \
    "5m" \
    "Test database connection pooling and query performance" \
    --user-classes DatabaseStressUser

# Test 4: Cache Performance Test
run_test \
    "cache_performance" \
    "scenarios.py" \
    75 \
    15 \
    "5m" \
    "Test caching behavior and cache hit rates" \
    --user-classes CacheTestUser

# Test 5: Write-Heavy Workload
run_test \
    "write_heavy" \
    "scenarios.py" \
    50 \
    10 \
    "5m" \
    "Test write operations (creates, updates)" \
    --user-classes WriteHeavyUser

# Test 6: Peak Load Test (1000 concurrent users)
echo -e "${YELLOW}WARNING: Peak load test will generate significant load${NC}"
read -p "Continue with peak load test? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    run_test \
        "peak_load" \
        "locustfile.py" \
        1000 \
        50 \
        "10m" \
        "Peak load test with 1000 concurrent users"
else
    echo "Skipping peak load test"
fi

# Test 7: Sustained Load Test
echo -e "${YELLOW}WARNING: Sustained load test runs for 30 minutes${NC}"
read -p "Continue with sustained load test? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    run_test \
        "sustained_load" \
        "locustfile.py" \
        200 \
        20 \
        "30m" \
        "Sustained load test to check for memory leaks and stability"
else
    echo "Skipping sustained load test"
fi

# Generate summary report
echo -e "${GREEN}=== Test Summary ===${NC}"
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "HTML Reports:"
ls -lh "$RESULTS_DIR"/*.html | tail -n 7
echo ""
echo "CSV Results:"
ls -lh "$RESULTS_DIR"/*.csv | tail -n 7
echo ""

# Parse results and show key metrics
echo -e "${GREEN}=== Key Metrics ===${NC}"
for csv_file in "$RESULTS_DIR"/${TIMESTAMP}_*_stats.csv; do
    if [ -f "$csv_file" ]; then
        test_name=$(basename "$csv_file" | sed 's/.*_\(.*\)_stats.csv/\1/')
        echo -e "${YELLOW}$test_name:${NC}"
        
        # Extract aggregated stats (last line)
        tail -n 1 "$csv_file" | awk -F',' '{
            printf "  Requests: %s\n", $3
            printf "  Failures: %s (%.2f%%)\n", $4, ($4/$3)*100
            printf "  Avg Response Time: %s ms\n", $5
            printf "  P95: %s ms\n", $11
            printf "  P99: %s ms\n", $12
            printf "  RPS: %s\n", $13
        }'
        echo ""
    fi
done

echo -e "${GREEN}Load testing complete!${NC}"
echo "Review the HTML reports for detailed analysis."
