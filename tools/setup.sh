#!/bin/bash

# MueJam Library Setup Script

echo "🚀 Setting up MueJam Library..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment files if they don't exist
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env from example..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please update backend/.env with your credentials"
fi

if [ ! -f frontend/.env.local ]; then
    echo "📝 Creating frontend/.env.local from example..."
    cp frontend/.env.example frontend/.env.local
    echo "⚠️  Please update frontend/.env.local with your credentials"
fi

# Initialize Git repository if not already initialized
if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: Project setup"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update backend/.env with your credentials (Clerk, AWS, Resend)"
echo "2. Update frontend/.env.local with your Clerk keys"
echo "3. Run 'docker-compose up -d' to start all services"
echo "4. Run 'docker-compose exec backend python manage.py migrate' to set up the database"
echo ""
echo "Services will be available at:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - API Docs: http://localhost:8000/v1/docs"
