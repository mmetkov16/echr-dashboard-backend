# ECHR Dashboard Backend - API Specification

## Base URL
```
http://localhost:8000
http://localhost:8000/api/v1
```

## Authentication
None (public API for now - add JWT if needed)

## Response Format
All responses are JSON with standardized format:

**Success Response** (2xx):
```json
{
  "data": {...},  // Endpoint-specific data
  "status": "success"
}
```

**Error Response** (4xx, 5xx):
```json
{
  "detail": "Error message",
  "error_code": "ERROR_TYPE",
  "timestamp": "2024-04-23T10:30:00"
}
```

---

## Health & Information Endpoints

### GET /
Root endpoint with API information
```
Response:
{
  "name": "ECHR Dashboard API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health"
}
```

### GET /health
Health check endpoint
```
Response (200):
{
  "status": "healthy",
  "version": "1.0.0",
  "database_connected": true,
  "message": "API is operational"
}

Response (503):
{
  "status": "degraded",
  "version": "1.0.0",
  "database_connected": false,
  "message": "Database connection failed"
}
```

### GET /info
API information and endpoints
```
Response:
{
  "name": "ECHR Dashboard API",
  "version": "1.0.0",
  "description": "European Court of Human Rights Case Analysis Dashboard API",
  "docs": "/docs",
  "openapi": "/openapi.json"
}
```

---

## Extraction Endpoints

### POST /api/v1/extract-cases
Extract ECHR cases from the court database

**Request Body**:
```json
{
  "count": 50,                      // Optional: Number of cases to extract
  "start_date": "2020-01-01T00:00:00",  // Optional: Start date filter
  "end_date": "2023-12-31T23:59:59",    // Optional: End date filter
  "language": "ENG",                // Optional: Language code (default: ENG)
  "max_items": 100,                 // Optional: Maximum items to process
  "fetch_full_text": false,         // Optional: Fetch full case text (slower)
  "run_background": false           // Optional: Run as background task
}
```

**Response (200 - Synchronous)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "cases_extracted": 45,
  "cases_stored": 45,
  "message": "Successfully extracted and stored 45 cases"
}
```

**Response (202 - Asynchronous)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "cases_extracted": 0,
  "cases_stored": 0,
  "message": "Extraction started in background. Use GET /task/{task_id} to check progress."
}
```

**Response (400)**:
```json
{
  "detail": "At least one of: count, start_date, or end_date must be provided",
  "error_code": "VALIDATION_ERROR"
}
```

### GET /api/v1/task/{task_id}
Get status of extraction task

**Response (200)**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "cases_extracted": 25,
  "cases_stored": 20,
  "error_message": null,
  "created_at": "2024-04-23T10:30:00",
  "started_at": "2024-04-23T10:30:05",
  "completed_at": null
}
```

**Response (404)**:
```json
{
  "detail": "Task {task_id} not found",
  "error_code": "NOT_FOUND"
}
```

---

## Cases Endpoints

### GET /api/v1/cases
List all cases with pagination and filtering

**Query Parameters**:
```
page (int): Page number, default 1, minimum 1
page_size (int): Items per page, default 50, range 1-1000
country (string): Filter by country (partial match, case-insensitive)
article (string): Filter by article (partial match, case-insensitive)
year (int): Filter by exact year
year_from (int): Filter from year
year_to (int): Filter to year
status (string): Filter by case status (partial match)
violation (boolean): Filter by violation found (true/false/null)
search_text (string): Full-text search in title, description, full_text
sort_by (string): Field to sort by (default: judgementdate)
  Available: judgementdate, country, appno, status, created_at, etc.
sort_order (string): asc or desc (default: desc)
```

**Response (200)**:
```json
{
  "total": 1250,
  "page": 1,
  "page_size": 50,
  "total_pages": 25,
  "items": [
    {
      "id": 1,
      "itemid": "001-2020-12345",
      "appno": "12345/20",
      "docname": "Case Name",
      "country": "France",
      "article": "2, 3, 5",
      "violation": true,
      "violation_count": 2,
      "judgementdate": "2020-06-15T00:00:00",
      "registration_date": "2019-01-01T00:00:00",
      "status": "Final",
      "conclusion": "Violation",
      "title": "Full Case Title",
      "description": "Case summary...",
      "respondent": "Country Name",
      "applicant": "Person Name",
      "language": "ENG",
      "is_important": false,
      "citation_count": 5,
      "created_at": "2024-04-23T10:00:00",
      "updated_at": "2024-04-23T10:00:00",
      "source": "echr-extractor"
    },
    ...
  ]
}
```

**Response (400)**:
```json
{
  "detail": "Invalid filter parameter: {error message}",
  "error_code": "VALIDATION_ERROR"
}
```

### GET /api/v1/cases/{case_id}
Get specific case by database ID

**Response (200)**: Single case object (see list endpoint)

**Response (404)**:
```json
{
  "detail": "Case {case_id} not found",
  "error_code": "NOT_FOUND"
}
```

### GET /api/v1/cases/search/{itemid}
Search for case by ECHR item ID

**Response (200)**: Single case object

**Response (404)**:
```json
{
  "detail": "Case {itemid} not found",
  "error_code": "NOT_FOUND"
}
```

### GET /api/v1/cases/appno/{appno}
Search for cases by application number (partial match)

**Response (200)**:
```json
{
  "total": 10,
  "page": 1,
  "page_size": 100,
  "total_pages": 1,
  "items": [
    {case objects...}
  ]
}
```

---

## Statistics Endpoints

### GET /api/v1/statistics
Get comprehensive statistics on all cases

**Response (200)**:
```json
{
  "total_cases": 50000,
  "violation_cases": 20000,
  "pending_cases": 5000,
  "resolved_cases": 45000,
  "violation_rate": 40.0,
  "by_country": {
    "France": 5000,
    "Germany": 4500,
    "Italy": 3200,
    ...
  },
  "by_year": {
    "2020": 1200,
    "2021": 1500,
    "2022": 1800,
    ...
  },
  "by_article": {
    "Article 2": 8000,
    "Article 3": 7500,
    "Article 5": 6200,
    ...
  },
  "top_countries": [
    ["France", 5000],
    ["Germany", 4500],
    ...
  ],
  "top_articles": [
    ["Article 2", 8000],
    ["Article 3", 7500],
    ...
  ]
}
```

### GET /api/v1/trends
Get yearly trends for visualization

**Response (200)**:
```json
{
  "trends": [
    {
      "year": 2015,
      "total_cases": 800,
      "violation_cases": 320,
      "cases_per_country": {
        "France": 150,
        "Germany": 140,
        ...
      }
    },
    {
      "year": 2016,
      "total_cases": 950,
      "violation_cases": 380,
      "cases_per_country": {...}
    },
    ...
  ],
  "yearly_growth": {
    "2016": 18.75,
    "2017": 15.43,
    ...
  },
  "total_cases_growth": 125.5
}
```

### GET /api/v1/statistics/country/{country}
Get statistics for a specific country

**Response (200)**:
```json
{
  "country": "France",
  "total_cases": 5000,
  "violation_cases": 2000,
  "violation_rate": 40.0,
  "top_articles": [
    ["Article 2", 800],
    ["Article 3", 750],
    ...
  ],
  "yearly_breakdown": {
    "2015": 150,
    "2016": 180,
    ...
  }
}
```

**Response (200 - No data)**:
```json
{
  "country": "Unknown",
  "message": "No cases found for this country",
  "total": 0
}
```

### GET /api/v1/statistics/article/{article}
Get statistics for a specific article

**Response (200)**:
```json
{
  "article": "Article 2",
  "total_cases": 8000,
  "violation_cases": 3200,
  "violation_rate": 40.0,
  "top_countries": [
    ["France", 1200],
    ["Germany", 1000],
    ...
  ],
  "yearly_breakdown": {
    "2015": 450,
    "2016": 520,
    ...
  }
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 202 | Accepted - Async task created |
| 400 | Bad Request - Invalid parameters |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid request body |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Database error |

---

## Request/Response Examples

### Example 1: Extract Recent Cases
```bash
curl -X POST "http://localhost:8000/api/v1/extract-cases" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 50,
    "fetch_full_text": false,
    "run_background": false
  }'
```

### Example 2: List French Cases with Article 2 Violation
```bash
curl "http://localhost:8000/api/v1/cases?country=France&article=2&violation=true&page=1&page_size=25"
```

### Example 3: Search for Specific Case
```bash
curl "http://localhost:8000/api/v1/cases/search/001-2020-12345"
```

### Example 4: Get Trends for Chart
```bash
curl "http://localhost:8000/api/v1/trends" | jq '.trends[] | {year, total_cases, violation_cases}'
```

### Example 5: Get Country Statistics
```bash
curl "http://localhost:8000/api/v1/statistics/country/Germany"
```

---

## Pagination Best Practices

1. **Initial Request**: Use page 1 with desired page_size
2. **Iterate**: Increment page until you reach total_pages
3. **Optimize**: Use filters to reduce result set
4. **Cache**: Store page results client-side when possible

Example iteration:
```javascript
async function getAllCases() {
  let allCases = [];
  let page = 1;
  
  while (true) {
    const response = await fetch(`/api/v1/cases?page=${page}`);
    const data = await response.json();
    allCases = allCases.concat(data.items);
    
    if (page >= data.total_pages) break;
    page++;
  }
  
  return allCases;
}
```

---

## Rate Limiting (Optional - Currently Disabled)

No rate limiting is currently enforced. For production, consider:
- 100 requests/minute per IP
- 1000 requests/day per API key
- Longer delays for heavy operations

---

## CORS Configuration

**Allowed Origins**:
- http://localhost:3000
- http://localhost:3001
- http://localhost:8000

**Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS
**Allowed Headers**: *

**To add origin**: Update CORS_ORIGINS in .env

---

## Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

Interactive API testing available in Swagger UI!

---

## Performance Tips

1. **Use Filters**: Narrow results before pagination
2. **Limit Page Size**: Don't request 1000+ items at once
3. **Cache Responses**: Store statistics locally (they change slowly)
4. **Async Operations**: Use background extraction for large datasets
5. **Batch Requests**: Request multiple endpoints simultaneously

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS Error | Check CORS_ORIGINS in .env for your domain |
| 404 on endpoint | Verify endpoint path, check /docs for correct paths |
| Database Error (503) | Ensure database is running, check DATABASE_URL |
| Slow queries | Use filters to reduce result set, add indexes |
| Large response timeout | Use pagination, reduce page_size |

---

**Last Updated**: April 23, 2026
**API Version**: 1.0.0
