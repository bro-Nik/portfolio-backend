# Portfolios API

[English](README.md) | [Русский](README.ru.md)

A microservice for managing user portfolios and wallets built on FastAPI with support for asset tracking and transaction history.


## Technology Stack
- **Framework**: FastAPI
- **Database**: PostgreSQL, Alembic
- **Authentication**: JWT
- **Infrastructure**: Docker
- **Testing**: pytest


## Core Features
- **Portfolio and wallet management**: CRUD operations
- **Asset tracking**: Monitor assets in portfolios and wallets
- **Transaction processing**: Support for various transaction types (Buy, Sell, Transfer)
- **Allocation analysis**: View asset distribution across portfolios/wallets
- **Performance**: Async operations, caching, rate limiting


## API Documentation
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`


## Quick Start
### Prerequisites
- Docker and Docker Compose

### Setup
```bash
# 1. Clone the repository
git clone https://github.com/bro-Nik/portfolio-backend.git portfolio-service
cd portfolio-service

# 2. Configure environment
cp .env.example .env
# Edit the .env file according to your needs

# 3. Start the service
docker-compose up -d

# 4. Apply database migrations
docker-compose exec backend alembic upgrade head
```
The service will be available at: `http://localhost:8000`


## Configuration
See environment variables in `.env.example`


## Development
### Running tests
```bash
docker-compose -f docker-compose.test.yml up
```

### Working with migrations
```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback last migration
docker-compose exec backend alembic downgrade -1
```
