# ECHR Dashboard Backend - Deployment Guide

## Quick Start (Development)

### 1. Start API Server
```bash
cd backend
venv\Scripts\activate  # Windows
python main.py
```

API runs at: http://localhost:8000
Swagger UI: http://localhost:8000/docs

### 2. Start Frontend (in another terminal)
```bash
cd frontend
npm run dev
```

Frontend runs at: http://localhost:3000

---

## Development Setup

### Install Dependencies
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Run Verification
```bash
python verify_setup.py
```

### Run Tests
```bash
pip install pytest pytest-asyncio httpx
pytest
```

### Code Quality
```bash
pip install black flake8 mypy
black .
flake8 .
mypy .
```

---

## Production Deployment

### Step 1: Configure Environment
```bash
cp .env.example .env

# Edit .env with production settings:
DEBUG=False
DATABASE_URL="postgresql://user:password@host:5432/echr_dashboard"
LOG_LEVEL="WARNING"
CORS_ORIGINS=["https://yourdomain.com"]
```

### Step 2: Setup PostgreSQL Database
```bash
# Create database
createdb echr_dashboard

# Create user
createuser echr_user

# Grant privileges
psql -d echr_dashboard -c "GRANT ALL PRIVILEGES ON DATABASE echr_dashboard TO echr_user"
```

### Step 3: Install Production Dependencies
```bash
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
```

### Step 4: Initialize Database
```bash
# Database tables are auto-created on first run
# But you can manually initialize:
python -c "from database import init_db; init_db()"
```

### Step 5: Run with Gunicorn
```bash
# Development (single worker)
gunicorn -w 1 -b 0.0.0.0:8000 main:app

# Production (multi-worker)
gunicorn -w 4 -b 0.0.0.0:8000 main:app --timeout 120
```

### Step 6: Setup Reverse Proxy (Nginx)
```nginx
upstream echr_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://echr_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 7: Setup SSL (Let's Encrypt)
```bash
sudo certbot --nginx -d api.yourdomain.com
```

### Step 8: Setup Systemd Service
Create `/etc/systemd/system/echr-api.service`:
```ini
[Unit]
Description=ECHR Dashboard API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/echr-dashboard/backend
Environment="PATH=/var/www/echr-dashboard/backend/venv/bin"
ExecStart=/var/www/echr-dashboard/backend/venv/bin/gunicorn \
    -w 4 \
    -b 127.0.0.1:8000 \
    main:app

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable echr-api
sudo systemctl start echr-api
sudo systemctl status echr-api
```

### Step 9: Setup Logging
```bash
# Create log directory
sudo mkdir -p /var/log/echr-api
sudo chown www-data:www-data /var/log/echr-api

# Update .env
LOG_LEVEL="INFO"
```

---

## Docker Deployment

### Create Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application
COPY . .

# Create log directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
```

### Create docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: echr_dashboard
      POSTGRES_USER: echr_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U echr_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    environment:
      DATABASE_URL: "postgresql://echr_user:secure_password@db:5432/echr_dashboard"
      DEBUG: "False"
      LOG_LEVEL: "INFO"
      CORS_ORIGINS: '["http://localhost:3000", "https://yourdomain.com"]'
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    restart: always

  frontend:
    build: ../frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: "http://localhost:8000"
    depends_on:
      - api
    restart: always

volumes:
  postgres_data:
```

Run Docker Compose:
```bash
docker-compose up -d
```

---

## Performance Optimization

### Database
```python
# Enable connection pooling (SQLAlchemy)
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
)
```

### Caching (Redis - Optional)
```bash
pip install redis-py
```

### Database Indexing
- Already configured in models.py
- Consider additional indexes for frequently filtered columns

### Query Optimization
- Use `.select()` for specific columns
- Implement pagination (already done)
- Use lazy loading for large relationships

---

## Monitoring & Logging

### View Logs
```bash
# Development
tail -f echr_dashboard.log

# Production
sudo journalctl -u echr-api -f
sudo tail -f /var/log/echr-api/error.log
```

### Health Check
```bash
curl http://localhost:8000/health
```

### Set up Monitoring (Recommended)
```bash
pip install prometheus-client
# Add metrics endpoint to track API usage
```

---

## Backup & Recovery

### Database Backup
```bash
# PostgreSQL backup
pg_dump -U echr_user -d echr_dashboard > backup.sql

# Restore
psql -U echr_user -d echr_dashboard < backup.sql

# Scheduled backup (cron)
0 2 * * * pg_dump -U echr_user echr_dashboard > /backups/echr_$(date +\%Y\%m\%d).sql
```

### Application Backup
```bash
# Backup code and config
tar -czf echr-backup-$(date +%Y%m%d).tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.db' \
    --exclude='.env' \
    .
```

---

## Troubleshooting

### API won't start
```bash
# Check logs
python main.py 2>&1 | head -50

# Check port in use
netstat -tulpn | grep 8000

# Kill process on port
taskkill /PID <pid> /F  # Windows
kill -9 <pid>          # Linux
```

### Database connection fails
```bash
# Test connection
python -c "from database import engine; engine.execute('SELECT 1')"

# Check DATABASE_URL in .env
# Verify PostgreSQL is running
# Check credentials
```

### CORS errors
```bash
# Update .env with correct origins
CORS_ORIGINS=["https://yourdomain.com"]
```

### Slow queries
```bash
# Enable query logging
SQLALCHEMY_ECHO=True

# Check indexes exist
```

### Out of memory
```bash
# Reduce page size
DEFAULT_PAGE_SIZE=25
MAX_PAGE_SIZE=500

# Limit extraction batch size
```

---

## Security Checklist

- [ ] .env file not in git (add to .gitignore)
- [ ] Use strong database passwords
- [ ] Enable HTTPS in production
- [ ] Configure CORS correctly
- [ ] Keep dependencies updated
- [ ] Use environment variables for secrets
- [ ] Enable database backups
- [ ] Monitor error logs for attacks
- [ ] Rate limit API endpoints
- [ ] Use API keys for public APIs

---

## Scaling Considerations

**For 100K+ cases:**
1. Add PostgreSQL full-text search indexes
2. Implement Redis caching layer
3. Use Celery for background tasks
4. Deploy multiple API instances behind load balancer
5. Use CDN for static assets

**Load Balancer (HAProxy)**:
```
listen api
  bind 0.0.0.0:80
  server api1 127.0.0.1:8001
  server api2 127.0.0.1:8002
  server api3 127.0.0.1:8003
```

---

## Maintenance Schedule

**Daily**: Monitor logs, health checks
**Weekly**: Backup database
**Monthly**: Update dependencies, security patches
**Quarterly**: Performance review, optimization

---

## Getting Help

1. Check `/docs` for API documentation
2. Review `echr_dashboard.log` for errors
3. Verify `.env` configuration
4. Test endpoints with curl or Postman
5. Check database connectivity
6. Review dependencies are installed

---

**Last Updated**: April 23, 2026
**Tested On**: Windows 11, Python 3.14
