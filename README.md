# Python APM Instrumentation Examples

A comprehensive collection of Python applications demonstrating Elastic APM (Application Performance Monitoring) instrumentation across different frameworks and use cases.

## Overview

This repository showcases APM integration in:
- **Flask** - Synchronous web framework with REST API
- **FastAPI** - Async web framework with modern Python features
- **Standalone Functions** - Batch jobs and scripts with SQLAlchemy
- **Celery Workers** - Distributed task queue and background jobs

## Features Demonstrated

- ✅ Automatic transaction tracking
- ✅ Custom spans and transactions
- ✅ Database query monitoring (SQLite, SQLAlchemy)
- ✅ External HTTP call tracking
- ✅ Error and exception capture
- ✅ Custom labels and metadata
- ✅ Async operations monitoring
- ✅ Background task tracking
- ✅ Complex multi-step workflows
- ✅ Performance profiling

## Prerequisites

- Python 3.8+
- Elastic APM Server (or Elastic Cloud)
- Redis (for Celery examples)
- pip or poetry for dependency management

## Quick Start

### 1. Clone and Install

```bash
git clone <repository-url>
cd example-py-apm-svc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure APM

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your APM server details
# At minimum, set:
# - ELASTIC_APM_SERVICE_NAME
# - ELASTIC_APM_SERVER_URL
# - ELASTIC_APM_SECRET_TOKEN (if required)
```

### 3. Run Examples

Choose one of the applications to run:

```bash
# Flask Application (port 5000)
python flask_apm.py

# FastAPI Application (port 8000)
python fastapi_apm.py

# Standalone Function/Batch Job
python func_apm.py

# Celery Worker (requires Redis)
celery -A celery_worker_apm worker --loglevel=info

# Celery Task Runner (in another terminal)
python task_runner.py
```

## Applications

### 1. Flask APM Demo (`flask_apm.py`)

A synchronous Flask application with comprehensive APM examples.

**Run:**
```bash
python flask_apm.py
```

**Available Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information and endpoint list |
| `/health` | GET | Health check endpoint |
| `/api/users` | GET, POST | User management with DB operations |
| `/api/users/<id>` | GET | Get specific user by ID |
| `/api/orders` | GET, POST | Order management with DB joins |
| `/api/slow` | GET | Simulates slow operations (1-3s) |
| `/api/error` | GET | Intentional error for testing |
| `/api/random-error` | GET | 50% chance of error |
| `/api/external-call` | GET | Makes external HTTP request |
| `/api/complex-operation` | GET | Multi-step operation with multiple spans |

**Example Requests:**
```bash
# Get all users
curl http://localhost:5000/api/users

# Create a user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com"}'

# Create an order
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "product": "Laptop", "amount": 999.99}'

# Test slow endpoint
curl http://localhost:5000/api/slow

# Test external API call
curl http://localhost:5000/api/external-call

# Test complex operation
curl http://localhost:5000/api/complex-operation
```

**APM Features:**
- Auto-instrumented HTTP transactions
- Custom DB spans for SQLite operations
- External HTTP call tracking
- Error capture and tracking
- Custom labels for filtering/grouping
- Request body capture

### 2. FastAPI APM Demo (`fastapi_apm.py`)

An async FastAPI application demonstrating modern async patterns with APM.

**Run:**
```bash
python fastapi_apm.py
# Or with uvicorn:
uvicorn fastapi_apm:app --reload --port 8000
```

**Available Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/docs` | GET | Interactive API documentation (Swagger UI) |
| `/health` | GET | Health check |
| `/api/async-users` | GET, POST | Async user management |
| `/api/async-processing` | GET | Multi-step async processing |
| `/api/parallel-requests` | GET | Parallel HTTP requests to GitHub API |
| `/api/slow-query` | GET | Simulates slow async query |
| `/api/error-async` | GET | Async error handling |
| `/api/streaming-data` | GET | Batch processing simulation |
| `/api/analytics` | GET | Parallel analytics calculations |

**Example Requests:**
```bash
# Create user
curl -X POST http://localhost:8000/api/async-users \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Doe", "email": "jane@example.com"}'

# Parallel requests
curl http://localhost:8000/api/parallel-requests

# Slow query with custom delay
curl "http://localhost:8000/api/slow-query?delay=3.0"

# Streaming data processing
curl "http://localhost:8000/api/streaming-data?count=10"

# Analytics
curl http://localhost:8000/api/analytics
```

**APM Features:**
- Async transaction tracking
- Parallel operation monitoring
- Async span capture
- httpx client instrumentation
- Pydantic model validation
- Interactive API docs

### 3. Standalone Function APM (`func_apm.py`)

Demonstrates APM in non-web applications like batch jobs, ETL processes, and scripts.

**Run:**
```bash
python func_apm.py
```

**Features:**
- SQLAlchemy ORM instrumentation
- Custom transaction management
- Multi-step batch processing
- Database initialization and seeding
- Report generation
- Error handling demonstrations
- Custom context and labels

**Use Cases:**
- Batch data processing jobs
- ETL pipelines
- Scheduled tasks (cron jobs)
- Data migration scripts
- Report generation

### 4. Celery Worker APM (`celery_worker_apm.py`)

Background task processing with full APM instrumentation.

**Prerequisites:**
```bash
# Start Redis (required for Celery)
docker run -d -p 6379:6379 redis:alpine
# Or use your existing Redis instance
```

**Run Worker:**
```bash
# Start Celery worker
celery -A celery_worker_apm worker --loglevel=info

# In another terminal, run tasks
python task_runner.py

# Run specific task
python task_runner.py email
python task_runner.py workflow
```

**Available Tasks:**

| Task | Description |
|------|-------------|
| `send_email` | Email sending simulation with SMTP tracking |
| `process_image` | Image processing with multiple transformations |
| `generate_report` | Report generation with data fetching and PDF creation |
| `data_sync` | ETL data synchronization in batches |
| `complex_workflow` | Multi-step workflow with external API calls |
| `failing_task` | Demonstrates error tracking (random failures) |

**APM Features:**
- Celery task instrumentation
- Task-level transaction tracking
- Sub-span for task steps
- Distributed tracing
- Task metadata and labels
- Error tracking and retry monitoring

## APM Configuration

### Environment Variables

Edit `.env` file with your configuration:

```bash
# Required
ELASTIC_APM_SERVICE_NAME=my-service-name
ELASTIC_APM_SERVER_URL=http://localhost:8200
ELASTIC_APM_SECRET_TOKEN=your-secret-token

# Optional
ENVIRONMENT=development
ELASTIC_APM_DEBUG=true
ELASTIC_APM_TRANSACTION_SAMPLE_RATE=1.0
ELASTIC_APM_CAPTURE_BODY=all

# Celery (if using)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### APM Server Setup

#### Option 1: Elastic Cloud
1. Sign up for [Elastic Cloud](https://cloud.elastic.co/)
2. Create deployment
3. Navigate to APM & Fleet
4. Copy server URL and secret token

#### Option 2: Self-Hosted APM Server
```bash
# Using Docker
docker run -d \
  --name=apm-server \
  -p 8200:8200 \
  docker.elastic.co/apm/apm-server:8.11.0 \
  --strict.perms=false \
  -e output.elasticsearch.hosts=["http://elasticsearch:9200"]
```

## Docker Support

### Build and Run

```bash
# Build image
docker build -t python-apm-demo .

# Run Flask app
docker run -p 5000:5000 --env-file .env python-apm-demo flask

# Run FastAPI app
docker run -p 8000:8000 --env-file .env python-apm-demo fastapi

# Run batch job
docker run --env-file .env python-apm-demo batch
```

### Docker Compose

```bash
# Start all services (app + Redis + APM)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## APM Best Practices

### 1. Custom Spans
Use custom spans to track specific operations:

```python
from elasticapm import capture_span

with capture_span('my_operation', 'custom'):
    # Your code here
    result = expensive_operation()
```

### 2. Labels and Metadata
Add context to transactions:

```python
import elasticapm

elasticapm.label(user_id=123, action='purchase', amount=99.99)
elasticapm.set_custom_context({'cart_items': 5})
```

### 3. Error Handling
Capture exceptions explicitly:

```python
try:
    risky_operation()
except Exception as e:
    elasticapm.capture_exception()
    # Handle error
```

### 4. Transaction Naming
Name transactions for better organization:

```python
from elasticapm import set_transaction_name

set_transaction_name('process_order')
```

### 5. Sampling
Adjust sampling rate for high-traffic apps:

```python
# In config
'TRANSACTION_SAMPLE_RATE': 0.1  # Sample 10% of transactions
```

## Monitoring and Analysis

### Key Metrics to Monitor

1. **Response Time**: Track endpoint latency
2. **Throughput**: Requests per minute
3. **Error Rate**: Failed transactions percentage
4. **Database Performance**: Query execution time
5. **External Services**: API call duration
6. **Memory/CPU**: Resource utilization

### APM Dashboard Views

- **Service Map**: Visualize service dependencies
- **Transactions**: Analyze endpoint performance
- **Errors**: Track exceptions and failures
- **Metrics**: CPU, memory, and custom metrics
- **Traces**: Distributed tracing across services

## Troubleshooting

### APM Data Not Appearing

1. Check APM server URL and secret token
2. Verify network connectivity to APM server
3. Enable debug mode: `ELASTIC_APM_DEBUG=true`
4. Check application logs for APM errors

### High Overhead

1. Reduce sample rate: `TRANSACTION_SAMPLE_RATE=0.1`
2. Disable body capture: `CAPTURE_BODY=off`
3. Limit stack traces: `STACK_TRACE_LIMIT=10`

### Missing Spans

1. Ensure `elasticapm.instrument()` is called early
2. Check library compatibility
3. Use manual instrumentation with `capture_span()`

## Performance Impact

APM instrumentation typically adds:
- **CPU**: 1-5% overhead
- **Memory**: 10-50MB additional
- **Latency**: <1ms per transaction

For production:
- Use sampling for high-traffic services
- Disable debug mode
- Limit captured data (bodies, stack traces)

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Code Quality
```bash
# Format code
black *.py

# Lint
flake8 *.py
pylint *.py

# Type checking
mypy *.py
```

## Resources

- [Elastic APM Python Agent Docs](https://www.elastic.co/guide/en/apm/agent/python/current/index.html)
- [Elastic APM Server](https://www.elastic.co/guide/en/apm/guide/current/index.html)
- [APM Best Practices](https://www.elastic.co/guide/en/apm/guide/current/apm-best-practices.html)
- [Flask APM Integration](https://www.elastic.co/guide/en/apm/agent/python/current/flask-support.html)
- [FastAPI APM Integration](https://www.elastic.co/guide/en/apm/agent/python/current/starlette-support.html)
- [Celery APM Integration](https://www.elastic.co/guide/en/apm/agent/python/current/celery-support.html)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: Create an issue in this repository
- Elastic Community: https://discuss.elastic.co/
- Documentation: https://www.elastic.co/guide/en/apm/

---

**Note**: This is a demonstration repository. For production use, ensure proper security measures, error handling, and configuration management.
