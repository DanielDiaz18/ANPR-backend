# FastAPI Backend Server

A modern, fast FastAPI backend server with authentication, database integration, and comprehensive API endpoints.

## Features

- **FastAPI Framework**: High performance, easy to learn, fast to code, ready for production
- **Authentication**: JWT-based authentication system
- **Database**: PostgreSQL with SQLAlchemy ORM
- **API Documentation**: Automatic interactive API docs (Swagger UI)
- **Testing**: Comprehensive test suite with pytest
- **Docker Support**: Containerized application with Docker and Docker Compose
- **CORS Support**: Configurable CORS for frontend integration

## Project Structure

```
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── api.py          # API router
│   │       └── endpoints/      # API endpoints
│   │           ├── auth.py     # Authentication endpoints
│   │           ├── users.py    # User management endpoints
│   │           └── items.py    # Item management endpoints
│   ├── core/
│   │   ├── config.py          # Application configuration
│   │   └── database.py        # Database configuration
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   └── item.py
│   └── schemas/               # Pydantic schemas
│       ├── user.py
│       └── item.py
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose configuration
└── test_main.py              # Basic tests
```

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   cd your-project-directory
   cp .env.example .env
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   Edit `.env` file with your database credentials and settings.

4. **Run the application**:
   ```bash
   uvicorn main:app --reload
   ```

5. **Access the API**:
   - API: http://localhost:8000
   - Interactive API docs: http://localhost:8000/docs
   - Alternative API docs: http://localhost:8000/redoc

### Docker Development

1. **Run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Access the application**:
   - API: http://localhost:8000
   - PostgreSQL: localhost:5432

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register
- `GET /api/v1/auth/me` - Get current user

### Users
- `GET /api/v1/users/` - Get all users
- `GET /api/v1/users/{user_id}` - Get user by ID
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Items
- `GET /api/v1/items/` - Get all items
- `POST /api/v1/items/` - Create item
- `GET /api/v1/items/{item_id}` - Get item by ID
- `PUT /api/v1/items/{item_id}` - Update item
- `DELETE /api/v1/items/{item_id}` - Delete item

## Testing

Run tests with pytest:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=app
```

## Configuration

Key configuration options in `.env`:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT secret key
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins
- `PROJECT_NAME`: Application name

## Development

1. **Add new endpoints**: Create new files in `app/api/v1/endpoints/`
2. **Add new models**: Create new files in `app/models/`
3. **Add new schemas**: Create new files in `app/schemas/`
4. **Update database**: Use Alembic for database migrations

## Contributing

1. Follow FastAPI best practices
2. Use async/await for database operations
3. Write tests for new features
4. Update documentation as needed

## License

This project is licensed under the MIT License.
# ANPR-backend
