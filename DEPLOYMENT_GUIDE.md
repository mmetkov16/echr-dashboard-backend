# ECHR Dashboard Backend - Deployment & Access Guide

## 🚀 Project Published to GitHub

**Repository:** https://github.com/mmetkov16/echr-dashboard-backend

Code has been published successfully. Now let's make it live and accessible to your colleagues!

---

## 📋 Quick Start for Your Colleagues

### Access the Live API

Once deployed, share this with your team:

```
🔗 API URL:  https://your-deployment-url.com
📖 Docs:     https://your-deployment-url.com/docs
📊 Health:   https://your-deployment-url.com/health
```

The `/docs` endpoint provides interactive Swagger UI for testing all endpoints.

---

## ☁️ Deploy in 3 Steps (Railway - Recommended)

**Why Railway?** Simplest deployment, automatic SSL, GitHub integration, free tier available

### Step 1: Create Railway Account
- Go to https://railway.app
- Sign up with GitHub (recommended)
- Click "New Project"

### Step 2: Connect GitHub Repository
- Select "Deploy from GitHub repo"
- Select `mmetkov16/echr-dashboard-backend`
- Authorize Railway to access your repos

### Step 3: Configure & Deploy
```bash
# In your local terminal:
cd echr-dashboard/backend
railway login
railway init
railway link

# Set environment variables via Railway dashboard:
# DATABASE_URL = sqlite:///echr_dashboard.db
# API_TITLE = ECHR Dashboard API

# Deploy
railway up
```

**That's it!** Railway provides a public URL automatically.

---

## 🐳 Docker Deployment (For Advanced Users)

### Build & Run Locally

```bash
# Build image
docker build -t echr-backend:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///echr_dashboard.db" \
  -e API_TITLE="ECHR Dashboard API" \
  echr-backend:latest
```

Access: `http://localhost:8000`

### Push to Cloud Container Registry

```bash
# Example: Google Cloud Run
gcloud auth configure-docker
docker tag echr-backend:latest gcr.io/your-project/echr-backend:latest
docker push gcr.io/your-project/echr-backend:latest
gcloud run deploy echr-backend --image gcr.io/your-project/echr-backend:latest
```

---

## 🔧 Alternative Cloud Providers

### Heroku

```bash
heroku create echr-dashboard-backend
git push heroku main
heroku config:set DATABASE_URL="sqlite:///echr_dashboard.db"
heroku open
```

**URL:** `https://echr-dashboard-backend.herokuapp.com`

### AWS (App Runner)

1. Push image to ECR
2. Create App Runner service
3. Select image from ECR
4. Deploy

### Azure (Container Instances)

```bash
az container create \
  --resource-group myResourceGroup \
  --name echr-backend \
  --image your-registry/echr-backend:latest \
  --ports 8000 \
  --environment-variables DATABASE_URL="sqlite:///echr_dashboard.db"
```

### Render

```bash
# Connect GitHub repo
# Railway's competitor, similar ease of use
# https://render.com
```

---

## 📚 Local Development

### Quick Start

```bash
# Clone repo
git clone https://github.com/mmetkov16/echr-dashboard-backend.git
cd echr-dashboard-backend

# Setup
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

# Run
python main.py
```

**Access:** `http://localhost:8000`
**Docs:** `http://localhost:8000/docs`

### Populate Database (First Time)

```bash
# Extract and insert 57,773+ ECHR cases
python batch_insert_cases.py
# Takes ~30-60 minutes
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

## 📡 API Endpoints Reference

Once deployed, your colleagues can use these endpoints:

### List Cases
```bash
curl "https://your-api.com/api/v1/cases?page=1&page_size=50"
```

### Filter by Country
```bash
curl "https://your-api.com/api/v1/cases?country=GBR&page_size=20"
```

### Filter by Year
```bash
curl "https://your-api.com/api/v1/cases?year_from=2020&year_to=2023"
```

### Search Cases
```bash
curl "https://your-api.com/api/v1/cases?search_text=privacy&page_size=10"
```

### Get Statistics
```bash
curl "https://your-api.com/api/v1/statistics/trends"
curl "https://your-api.com/api/v1/statistics/countries"
```

### Interactive Testing
Visit `https://your-api.com/docs` for full Swagger documentation and interactive testing

---

## 📢 Share with Colleagues

### Email Template

```
Subject: ECHR Dashboard Backend is Live! 🚀

Hi Team,

The ECHR Dashboard Backend is now live and ready for use!

📍 API URL: https://echr-backend-prod.railway.app
📖 Documentation: https://echr-backend-prod.railway.app/docs

Quick Start:
1. Visit the Docs link above (Swagger UI)
2. Try the /api/v1/cases endpoint
3. Filter by country, year, or search text

Available Features:
✓ 57,773+ ECHR court cases
✓ Advanced filtering (country, year, article, violation status)
✓ Full-text search
✓ Case statistics and trends
✓ HUDOC case links

Questions? Check the README or API docs.

Repository: https://github.com/mmetkov16/echr-dashboard-backend
```

### Share Access Instructions

Create a file `COLLEAGUE_ACCESS.md`:

```markdown
# How to Access the ECHR Dashboard API

## For Non-Developers

1. Visit: https://your-api.com/docs
2. Scroll through the endpoints
3. Click "Try it out" on any endpoint
4. Click "Execute"
5. View the response

## For Developers

### Python
\`\`\`python
import requests

# Get cases
response = requests.get("https://your-api.com/api/v1/cases?page=1")
cases = response.json()
print(cases)
\`\`\`

### JavaScript
\`\`\`javascript
fetch("https://your-api.com/api/v1/cases?page=1")
  .then(r => r.json())
  .then(data => console.log(data))
\`\`\`

### cURL
\`\`\`bash
curl "https://your-api.com/api/v1/cases?page=1&page_size=10"
\`\`\`

## Available Filters

- `country` - Filter by country code (e.g., "GBR", "FRA")
- `year` - Exact year
- `year_from` - Start year
- `year_to` - End year
- `article` - Filter by violated article
- `violation` - true/false
- `search_text` - Full-text search
```

---

## 🔒 Security Best Practices

### For Production Deployment

1. **Use PostgreSQL** instead of SQLite:
   ```env
   DATABASE_URL=postgresql://user:pass@localhost:5432/echr
   ```

2. **Enable HTTPS** (automatic with Railway/Heroku)

3. **Add Rate Limiting:**
   ```bash
   pip install slowapi
   ```

4. **Configure CORS for Frontend:**
   ```env
   CORS_ORIGINS=["https://frontend-domain.com"]
   ```

5. **Monitor Access:**
   - Enable logging in cloud provider
   - Set up alerts for errors

---

## 🔄 Monitoring & Maintenance

### Check API Health
```bash
curl https://your-api.com/health
```

### View Deployment Logs

**Railway:**
- Dashboard → Logs tab
- Real-time streaming

**Heroku:**
```bash
heroku logs --tail
```

**Docker/Local:**
```bash
# Check container logs
docker logs <container_id>
```

### Performance Metrics

```bash
# Response time
curl -w "Response time: %{time_total}s\n" https://your-api.com/health
```

---

## 🆘 Troubleshooting

### API Returns 500 Error
1. Check logs in cloud dashboard
2. Verify DATABASE_URL is correct
3. Ensure database is populated (run `batch_insert_cases.py`)

### CORS Issues
Update `CORS_ORIGINS` in environment:
```env
CORS_ORIGINS=["http://localhost:3000", "https://your-frontend.com"]
```

### Slow Responses
1. For production, use PostgreSQL instead of SQLite
2. Add database indexes
3. Enable caching

### Database Size Issues

If database file is too large for GitHub:
```bash
# Use Git LFS for large files
git lfs install
git lfs track "*.db"
git add .gitattributes
```

---

## 📊 Database Management

### Backup Database
```bash
# For SQLite
cp echr_dashboard.db echr_dashboard_backup.db

# For PostgreSQL
pg_dump -U user echr_dashboard > backup.sql
```

### Reset Database
```bash
# Delete and reinit
python -c "from database import init_db; init_db()"
python batch_insert_cases.py
```

### Database Stats
```bash
# SQLite size
ls -lh echr_dashboard.db

# Number of cases
python -c "from database import SessionLocal, Case; db = SessionLocal(); print(f'Total cases: {db.query(Case).count()}')"
```

---

## 🚀 Deployment Comparison

| Platform | Setup Time | Cost | Best For |
|----------|-----------|------|----------|
| **Railway** | 5 min | Free tier | Quick production |
| **Heroku** | 5 min | Paid | Reliable hosting |
| **Docker + AWS** | 20 min | ~$5/mo | Scalable |
| **Render** | 5 min | Free tier | Alternative to Railway |
| **Local** | 10 min | Free | Development |

---

## 📋 Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Choose deployment platform
- [ ] Create account on platform
- [ ] Connect GitHub repository
- [ ] Configure environment variables
- [ ] Deploy backend
- [ ] Test API endpoints
- [ ] Share deployment URL with colleagues
- [ ] Monitor logs
- [ ] Set up backups (production)
- [ ] Document custom settings

---

## 📞 Getting Help

**Having issues?** Check in this order:

1. **API Docs**: `https://your-api.com/docs`
2. **GitHub Issues**: https://github.com/mmetkov16/echr-dashboard-backend/issues
3. **Application Logs**: Check cloud provider dashboard
4. **README.md**: https://github.com/mmetkov16/echr-dashboard-backend/blob/main/README.md

---

## 📝 Next Steps

1. **Deploy** using Railway (5 minutes)
2. **Test** by visiting `/docs` endpoint
3. **Share** URL with colleagues
4. **Monitor** performance for first week
5. **Scale** or optimize as needed

---

**Ready to go live?** Start with Railway - https://railway.app

Good luck! 🎉
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
