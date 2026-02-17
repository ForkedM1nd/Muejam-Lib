# MueJam Library

A minimal digital library platform for serial stories with an integrated micro-posting system called "Whispers".

## Project Structure

This is a monorepo containing multiple applications and shared packages:

```
muejam-library/
├── apps/              # Applications
│   ├── backend/       # Django REST API
│   └── frontend/      # Vite React application
├── packages/          # Shared libraries (future)
├── tools/             # Build tools and scripts
├── docs/              # Documentation
└── tests/             # Integration tests
```

## Quick Start

### Prerequisites

- Docker and Docker Compose V2
- Git

### Running the Application

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd muejam-library
   ```

2. Start all services with Docker Compose:
   ```bash
   docker-compose up
   ```

3. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000/api
   - API Documentation: http://localhost:8000/api/docs

### Development Setup

For detailed development setup instructions, see:
- [Quickstart Guide](docs/getting-started/quickstart.md)
- [Development Guide](docs/getting-started/development.md)

## Features

- **Serial Fiction Library**: Browse, read, and manage serial stories
- **Whispers**: Micro-posting system for short updates and thoughts
- **User Authentication**: Secure registration and login with JWT tokens
- **Responsive Design**: Works on desktop and mobile devices
- **RESTful API**: Clean API design with comprehensive documentation

## Technology Stack

### Backend
- Django 5.1 with Django REST Framework
- PostgreSQL database
- Prisma ORM
- JWT authentication

### Frontend
- React 18 with TypeScript
- Vite build tool
- TanStack Query for data fetching
- React Router for navigation
- Tailwind CSS for styling

## Documentation

- [Documentation Index](docs/README.md)
- [API Documentation](docs/architecture/api.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## Development

### Backend Development

```bash
cd apps/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Development

```bash
cd apps/frontend
npm install
npm run dev
```

### Running Tests

Backend tests:
```bash
cd apps/backend
pytest
```

Frontend tests:
```bash
cd apps/frontend
npm test
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

See [LICENSE](LICENSE) for details.
