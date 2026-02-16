# MueJam Library

A minimal digital library platform for serial stories with an integrated micro-posting system called "Whispers".

## Tech Stack

- **Frontend**: Next.js 14 (App Router), React, Tailwind CSS
- **Backend**: Django 5.x, Django REST Framework
- **Database**: PostgreSQL 15+ with Prisma ORM
- **Cache/Queue**: Valkey (Redis-compatible)
- **Authentication**: Clerk
- **Email**: Resend API
- **Storage**: AWS S3
- **Background Jobs**: Celery

## Project Structure

```
muejam-library/
├── backend/           # Django REST API
├── frontend/          # Next.js application
├── docker-compose.yml # Local development setup
└── README.md
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Environment Setup

1. Copy environment files:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

2. Update the environment files with your credentials:
   - Clerk API keys
   - AWS S3 credentials
   - Resend API key

### Running with Docker

Start all services:
```bash
docker-compose up -d
```

Services will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Valkey: localhost:6379

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Documentation

Once the backend is running, API documentation is available at:
- Swagger UI: http://localhost:8000/v1/docs

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Architecture

The platform uses an API-first architecture with:
- Cursor-based pagination for all list endpoints
- Soft deletes for content (never physically deleted)
- Cache-aside pattern with Valkey
- Background processing via Celery
- Direct-to-S3 uploads using presigned URLs
- Rate limiting at the API layer

## Features

- **Story Discovery**: Trending, New, and personalized "For You" feeds
- **Reading Experience**: Distraction-free reader with customizable settings
- **Library Management**: Organize stories into custom shelves
- **Story Authoring**: Create and publish serial stories with chapters
- **Whispers**: Micro-posting system (global, story-linked, or highlight-linked)
- **Social Features**: Follow authors, block users
- **Notifications**: In-app and email notifications for replies and follows
- **Search**: Full-text search with autocomplete suggestions
- **Highlights**: Save and annotate text passages

## License

Proprietary - All rights reserved
