#!/bin/bash

# Monitoring Stack Setup Script
# This script helps set up the monitoring infrastructure for MueJam Library

set -e

echo "========================================="
echo "MueJam Library Monitoring Setup"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and configure:"
    echo "   - Database credentials"
    echo "   - Redis credentials"
    echo "   - SMTP password for email alerts"
    echo "   - Slack webhook URL"
    echo "   - PagerDuty service key"
    echo ""
    read -p "Press Enter after you've configured .env file..."
else
    echo "✓ .env file already exists"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p prometheus/alerts
mkdir -p grafana/dashboards
mkdir -p grafana/provisioning
mkdir -p alertmanager/templates
echo "✓ Directories created"

# Pull Docker images
echo ""
echo "Pulling Docker images..."
docker-compose -f docker-compose.monitoring.yml pull
echo "✓ Images pulled"

# Start monitoring stack
echo ""
echo "Starting monitoring stack..."
docker-compose -f docker-compose.monitoring.yml up -d
echo "✓ Monitoring stack started"

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service health..."

# Check Prometheus
if curl -s http://localhost:9090/-/healthy > /dev/null; then
    echo "✓ Prometheus is healthy (http://localhost:9090)"
else
    echo "⚠️  Prometheus may not be ready yet"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "✓ Grafana is healthy (http://localhost:3000)"
else
    echo "⚠️  Grafana may not be ready yet"
fi

# Check Alertmanager
if curl -s http://localhost:9093/-/healthy > /dev/null; then
    echo "✓ Alertmanager is healthy (http://localhost:9093)"
else
    echo "⚠️  Alertmanager may not be ready yet"
fi

# Display summary
echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Access the monitoring stack:"
echo "  - Prometheus:    http://localhost:9090"
echo "  - Grafana:       http://localhost:3000"
echo "  - Alertmanager:  http://localhost:9093"
echo ""
echo "Grafana credentials (from .env):"
echo "  - Username: admin"
echo "  - Password: (check GRAFANA_ADMIN_PASSWORD in .env)"
echo ""
echo "Next steps:"
echo "  1. Login to Grafana at http://localhost:3000"
echo "  2. Navigate to Dashboards → Infrastructure"
echo "  3. View 'Database Performance Metrics' dashboard"
echo "  4. View 'Cache Performance Metrics' dashboard"
echo ""
echo "To stop the monitoring stack:"
echo "  docker-compose -f docker-compose.monitoring.yml down"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.monitoring.yml logs -f"
echo ""
echo "For more information, see README.md"
echo "========================================="
