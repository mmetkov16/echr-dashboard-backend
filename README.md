# ECHR Dashboard Backend API

A production-ready FastAPI backend for the European Court of Human Rights (ECHR) case analysis dashboard. Provides REST endpoints for extracting, storing, and analyzing ECHR case data.

## Features

- **ECHR Data Extraction**: Extract cases from the ECHR using the `echr-extractor` library
- **PostgreSQL/SQLite Support**: Flexible database configuration for dev/production
- **Background Tasks**: Long-running extractions via background tasks
- **Advanced Filtering**: Search and filter cases by country, article, year, status, and more
- **Analytics**: Comprehensive statistics and trend analysis
- **CORS Enabled**: Pre-configured for frontend on localhost:3000
- **Production-Ready**: Comprehensive logging, error handling, and validation
- **API Documentation**: Auto-generated Swagger UI at `/docs`

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL (optional, SQLite used by default)

### Installation

1. **Navigate to backend directory**:
```bash
cd backend
```

2. **Activate virtual environment**:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment** (optional):
Edit `.env` file to customize settings:
```env
DATABASE_URL="sqlite:///./echr_dashboard.db"  # or PostgreSQL
DEBUG=False
LOG_LEVEL="INFO"
```

### Running the API

**Development**:
```bash
python main.py
```

**Production** (with Uvicorn directly):
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health & Info
- `GET /` - API information
- `GET /health` - Health check
- `GET /info` - API details

### Extraction
- `POST /api/v1/extract-cases` - Extract ECHR cases
  - Parameters: `count`, `start_date`, `end_date`, `language`, `max_items`, `fetch_full_text`, `run_background`
  - Returns: Task ID and status

- `GET /api/v1/task/{task_id}` - Get extraction task status

### Cases
- `GET /api/v1/cases` - List cases with pagination and filters
  - Query params: `page`, `page_size`, `country`, `article`, `year`, `status`, `violation`, `search_text`, `sort_by`, `sort_order`

- `GET /api/v1/cases/{case_id}` - Get specific case by ID

- `GET /api/v1/cases/search/{itemid}` - Search by ECHR item ID

- `GET /api/v1/cases/appno/{appno}` - Search by application number

### Statistics
- `GET /api/v1/statistics` - Overall statistics
  - Returns: Total cases, violations, by country/year/article, trends

- `GET /api/v1/trends` - Yearly trends
  - Returns: Yearly breakdown with growth rates

- `GET /api/v1/statistics/country/{country}` - Country-specific statistics

- `GET /api/v1/statistics/article/{article}` - Article-specific statistics

## Database Schema

### Cases Table
```
- id (PK)
- itemid (unique)
- appno (indexed)
- docname
- country (indexed)
- article
- violation (boolean)
- violation_count
- judgementdate (indexed)
- registration_date
- decision_date
- status (indexed)
- conclusion
- title
- description
- respondent
- applicant
- full_text (optional, large)
- language
- is_important
- citation_count
- created_at
- updated_at
- source
```

### Extraction Tasks Table
```
- id (PK)
- task_id (unique)
- status (pending/running/completed/failed)
- count, start_date, end_date
- language, max_items
- cases_extracted, cases_stored
- error_message
- timestamps
```

## Configuration

### Environment Variables (`.env`)

```env
# API
API_TITLE="ECHR Dashboard API"
API_VERSION="1.0.0"
DEBUG=False

# Database (SQLite for dev, PostgreSQL for production)
DATABASE_URL="sqlite:///./echr_dashboard.db"
# DATABASE_URL="postgresql://user:password@localhost/echr_dashboard"

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# ECHR Extraction
ECHR_DEFAULT_LANGUAGE="ENG"
ECHR_TIMEOUT=30

# Logging
LOG_LEVEL="INFO"
```

## Usage Examples

### Extract Cases (Synchronous)
```bash
curl -X POST "http://localhost:8000/api/v1/extract-cases" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 50,
    "language": "ENG",
    "fetch_full_text": false,
    "run_background": false
  }'
```

### Extract Cases (Background Task)
```bash
curl -X POST "http://localhost:8000/api/v1/extract-cases" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 100,
    "fetch_full_text": true,
    "run_background": true
  }'
```

### List Cases with Filters
```bash
# Get cases from France, articles 2-3, year 2020
curl "http://localhost:8000/api/v1/cases?country=France&article=2,3&year=2020&page=1&page_size=50"
```

### Get Statistics
```bash
curl "http://localhost:8000/api/v1/statistics"
```

### Get Trends
```bash
curl "http://localhost:8000/api/v1/trends"
```

## Architecture

### Project Structure
```
backend/
├── main.py              # FastAPI app entry point
├── config.py            # Configuration management
├── models.py            # Pydantic schemas
├── database.py          # SQLAlchemy models and session
├── echr_service.py      # ECHR extraction logic
├── routers/
│   ├── __init__.py
│   ├── extraction.py    # Extraction endpoints
│   ├── cases.py         # Case listing/search endpoints
│   ├── statistics.py    # Analytics endpoints
│   └── health.py        # Health check endpoints
├── requirements.txt     # Python dependencies
├── .env                 # Environment configuration
└── echr_dashboard.db    # SQLite database (auto-created)
```

### Key Components

**config.py**: Settings management using Pydantic Settings
**models.py**: Request/response Pydantic models
**database.py**: SQLAlchemy ORM models and database initialization
**echr_service.py**: Integration with echr-extractor library
**routers/**: API endpoint implementations

## Error Handling

All endpoints return standardized error responses:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-04-23T10:30:00"
}
```

## Logging

Logs are written to:
- Console (all levels)
- `echr_dashboard.log` file (all levels)

Configure log level via `LOG_LEVEL` environment variable: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Production Deployment

### Database Setup (PostgreSQL)

```bash
# Create database
createdb echr_dashboard

# Update .env
DATABASE_URL="postgresql://user:password@localhost:5432/echr_dashboard"
```

### Run with Gunicorn (Production WSGI Server)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

### Docker Deployment (Optional)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Development

### Running Tests
```bash
pip install pytest pytest-asyncio httpx
pytest
```

### Code Quality
```bash
pip install black flake8 mypy
black . --check
flake8 .
mypy .
```

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Troubleshooting

### Database Connection Issues
```bash
# Check database URL in .env
# For SQLite, ensure write permissions in directory
# For PostgreSQL, verify connection string and server status
```

### ECHR Extraction Fails
- Ensure `echr-extractor` is installed: `pip install echr-extractor`
- Check internet connection (ECHR API requires network)
- Review logs in `echr_dashboard.log`

### CORS Errors
Update `CORS_ORIGINS` in `.env` to match your frontend URL:
```env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]
```

## Performance Considerations

- Use PostgreSQL in production (better than SQLite)
- Enable database query indexing on frequently filtered columns
- Consider Redis for background task management with Celery
- Implement query result caching for statistics endpoints
- Set reasonable `max_items` limits to avoid memory issues

## Security

- Keep `.env` file out of version control (use `.env.example`)
- Use strong database credentials in production
- Enable HTTPS in production
- Validate all user inputs (Pydantic handles this)
- Implement rate limiting for public endpoints
- Use environment variables for sensitive data

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Run `black`, `flake8`, `mypy` for code quality
4. Submit pull request

## License

MIT License - See LICENSE file

## Support

For issues or questions:
- Check API documentation at `/docs`
- Review `echr_dashboard.log` for error details
- Consult echr-extractor documentation: https://github.com/echr-case-finder/echr-extractor
