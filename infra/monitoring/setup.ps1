# Monitoring Stack Setup Script (PowerShell)
# This script helps set up the monitoring infrastructure for MueJam Library

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "MueJam Library Monitoring Setup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    docker --version | Out-Null
    Write-Host "✓ Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker is not installed. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "✓ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "Error: Docker Compose is not available. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Please edit .env file and configure:" -ForegroundColor Yellow
    Write-Host "   - Database credentials"
    Write-Host "   - Redis credentials"
    Write-Host "   - SMTP password for email alerts"
    Write-Host "   - Slack webhook URL"
    Write-Host "   - PagerDuty service key"
    Write-Host ""
    Read-Host "Press Enter after you've configured .env file"
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Create necessary directories
Write-Host ""
Write-Host "Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path prometheus/alerts | Out-Null
New-Item -ItemType Directory -Force -Path grafana/dashboards | Out-Null
New-Item -ItemType Directory -Force -Path grafana/provisioning | Out-Null
New-Item -ItemType Directory -Force -Path alertmanager/templates | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green

# Pull Docker images
Write-Host ""
Write-Host "Pulling Docker images..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring.yml pull
Write-Host "✓ Images pulled" -ForegroundColor Green

# Start monitoring stack
Write-Host ""
Write-Host "Starting monitoring stack..." -ForegroundColor Yellow
docker-compose -f docker-compose.monitoring.yml up -d
Write-Host "✓ Monitoring stack started" -ForegroundColor Green

# Wait for services to be ready
Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host ""
Write-Host "Checking service health..." -ForegroundColor Yellow

# Check Prometheus
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9090/-/healthy" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Prometheus is healthy (http://localhost:9090)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Prometheus may not be ready yet" -ForegroundColor Yellow
}

# Check Grafana
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Grafana is healthy (http://localhost:3000)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Grafana may not be ready yet" -ForegroundColor Yellow
}

# Check Alertmanager
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9093/-/healthy" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Alertmanager is healthy (http://localhost:9093)" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Alertmanager may not be ready yet" -ForegroundColor Yellow
}

# Display summary
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access the monitoring stack:"
Write-Host "  - Prometheus:    http://localhost:9090"
Write-Host "  - Grafana:       http://localhost:3000"
Write-Host "  - Alertmanager:  http://localhost:9093"
Write-Host ""
Write-Host "Grafana credentials (from .env):"
Write-Host "  - Username: admin"
Write-Host "  - Password: (check GRAFANA_ADMIN_PASSWORD in .env)"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Login to Grafana at http://localhost:3000"
Write-Host "  2. Navigate to Dashboards → Infrastructure"
Write-Host "  3. View 'Database Performance Metrics' dashboard"
Write-Host "  4. View 'Cache Performance Metrics' dashboard"
Write-Host ""
Write-Host "To stop the monitoring stack:"
Write-Host "  docker-compose -f docker-compose.monitoring.yml down"
Write-Host ""
Write-Host "To view logs:"
Write-Host "  docker-compose -f docker-compose.monitoring.yml logs -f"
Write-Host ""
Write-Host "For more information, see README.md"
Write-Host "=========================================" -ForegroundColor Cyan
