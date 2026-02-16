# MueJam Library Setup Script (PowerShell)

Write-Host "🚀 Setting up MueJam Library..." -ForegroundColor Green

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker first." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    exit 1
}

# Create environment files if they don't exist
if (-not (Test-Path backend/.env)) {
    Write-Host "📝 Creating backend/.env from example..." -ForegroundColor Yellow
    Copy-Item backend/.env.example backend/.env
    Write-Host "⚠️  Please update backend/.env with your credentials" -ForegroundColor Yellow
}

if (-not (Test-Path frontend/.env.local)) {
    Write-Host "📝 Creating frontend/.env.local from example..." -ForegroundColor Yellow
    Copy-Item frontend/.env.example frontend/.env.local
    Write-Host "⚠️  Please update frontend/.env.local with your credentials" -ForegroundColor Yellow
}

# Initialize Git repository if not already initialized
if (-not (Test-Path .git)) {
    Write-Host "📦 Initializing Git repository..." -ForegroundColor Cyan
    git init
    git add .
    git commit -m "Initial commit: Project setup"
}

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Update backend/.env with your credentials (Clerk, AWS, Resend)"
Write-Host "2. Update frontend/.env.local with your Clerk keys"
Write-Host "3. Run 'docker-compose up -d' to start all services"
Write-Host "4. Run 'docker-compose exec backend python manage.py migrate' to set up the database"
Write-Host ""
Write-Host "Services will be available at:" -ForegroundColor Cyan
Write-Host "  - Frontend: http://localhost:3000"
Write-Host "  - Backend API: http://localhost:8000"
Write-Host "  - API Docs: http://localhost:8000/v1/docs"
