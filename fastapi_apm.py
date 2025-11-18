import os
import asyncio
import random
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from elasticapm.contrib.starlette import make_apm_client, ElasticAPM
import elasticapm
import httpx
from dotenv import load_dotenv

load_dotenv()

# APM Configuration
apm_config = {
    'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME', 'fastapi-apm-demo'),
    'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL', 'http://localhost:8200'),
    'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN', ''),
    'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
    'DEBUG': os.getenv('ELASTIC_APM_DEBUG', 'true').lower() == 'true',
    'CAPTURE_BODY': 'all',
    'TRANSACTION_SAMPLE_RATE': 1.0,
}

# Initialize APM client
apm = make_apm_client(apm_config)

# Create FastAPI app
app = FastAPI(
    title="FastAPI APM Demo",
    description="Demonstrates APM instrumentation in async FastAPI applications",
    version="1.0.0"
)

# Add APM middleware
app.add_middleware(ElasticAPM, client=apm)


# Pydantic models
class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: EmailStr
    created_at: Optional[datetime] = None


class Product(BaseModel):
    id: int
    name: str
    price: float


class AnalyticsResult(BaseModel):
    metric: str
    value: float
    timestamp: datetime


# In-memory data store (for demo purposes)
users_db: List[User] = []
user_id_counter = 1


@app.get("/")
async def root():
    """Root endpoint with service information"""
    elasticapm.label(endpoint='root', framework='fastapi')
    return {
        "service": "FastAPI APM Demo",
        "version": "1.0.0",
        "endpoints": [
            "/docs",
            "/health",
            "/api/async-users",
            "/api/async-processing",
            "/api/parallel-requests",
            "/api/slow-query",
            "/api/error-async",
            "/api/streaming-data",
            "/api/analytics"
        ]
    }


@app.get("/health")
async def health_check():
    """Async health check"""
    return {"status": "healthy", "service": "fastapi-apm-demo"}


@app.get("/api/async-users", response_model=List[User])
async def get_users():
    """Get all users asynchronously"""
    with elasticapm.capture_span('fetch_users_async', 'db.memory'):
        # Simulate async database query
        await asyncio.sleep(0.1)
        elasticapm.label(user_count=len(users_db))
        return users_db


@app.post("/api/async-users", response_model=User, status_code=201)
async def create_user(user: User):
    """Create a new user asynchronously"""
    global user_id_counter

    with elasticapm.capture_span('create_user_async', 'db.memory'):
        # Simulate async database operation
        await asyncio.sleep(0.05)

        user.id = user_id_counter
        user.created_at = datetime.utcnow()
        users_db.append(user)

        elasticapm.label(user_id=user.id, operation='create')
        user_id_counter += 1

        return user


@app.get("/api/async-processing")
async def async_processing():
    """Demonstrates multiple async operations"""

    # Step 1: Data validation
    with elasticapm.capture_span('validation', 'custom'):
        await asyncio.sleep(0.1)
        elasticapm.label(step='validation', status='passed')

    # Step 2: Data processing
    with elasticapm.capture_span('processing', 'custom'):
        await asyncio.sleep(0.2)
        result = {"processed": True, "records": 100}
        elasticapm.label(step='processing', records=100)

    # Step 3: Data storage
    with elasticapm.capture_span('storage', 'custom'):
        await asyncio.sleep(0.15)
        elasticapm.label(step='storage', status='completed')

    return {
        "message": "Async processing completed",
        "result": result,
        "timestamp": datetime.utcnow()
    }


@app.get("/api/parallel-requests")
async def parallel_requests():
    """Makes multiple parallel async HTTP requests"""

    async def fetch_github_repo(repo: str) -> dict:
        """Fetch repository info from GitHub"""
        with elasticapm.capture_span(f'fetch_{repo}', 'external.http'):
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(
                        f'https://api.github.com/repos/{repo}',
                        timeout=5.0
                    )
                    elasticapm.label(
                        repo=repo,
                        status_code=response.status_code
                    )

                    if response.status_code == 200:
                        data = response.json()
                        return {
                            'repo': repo,
                            'stars': data.get('stargazers_count', 0),
                            'forks': data.get('forks_count', 0)
                        }
                except Exception as e:
                    elasticapm.capture_exception()
                    return {'repo': repo, 'error': str(e)}

    # Make parallel requests
    repos = [
        'elastic/apm-agent-python',
        'fastapi/fastapi',
        'pallets/flask'
    ]

    with elasticapm.capture_span('parallel_fetch', 'external.http'):
        results = await asyncio.gather(*[fetch_github_repo(repo) for repo in repos])
        elasticapm.label(repos_fetched=len(results))

    return {
        "results": results,
        "total_repos": len(results)
    }


@app.get("/api/slow-query")
async def slow_query(delay: float = Query(default=2.0, ge=0.1, le=10.0)):
    """Simulates a slow async database query"""
    with elasticapm.capture_span('slow_query', 'db.query'):
        elasticapm.label(delay_seconds=delay, query_type='slow')
        await asyncio.sleep(delay)

        # Simulate query result
        result = {
            "query": "SELECT * FROM large_table WHERE condition = true",
            "rows_returned": random.randint(1000, 10000),
            "execution_time": delay
        }

    return result


@app.get("/api/error-async")
async def error_async():
    """Intentionally raises an async error"""
    elasticapm.label(endpoint='error_async', intentional=True)

    # Simulate some async work before error
    await asyncio.sleep(0.1)

    raise HTTPException(
        status_code=500,
        detail="This is an intentional async error for APM testing"
    )


@app.get("/api/streaming-data")
async def streaming_data(count: int = Query(default=5, ge=1, le=20)):
    """Simulates streaming data processing"""

    async def process_batch(batch_num: int) -> dict:
        """Process a single batch of data"""
        with elasticapm.capture_span(f'process_batch_{batch_num}', 'processing'):
            await asyncio.sleep(random.uniform(0.1, 0.3))
            elasticapm.label(batch_num=batch_num, records=random.randint(10, 100))

            return {
                'batch': batch_num,
                'records_processed': random.randint(10, 100),
                'status': 'completed'
            }

    with elasticapm.capture_span('streaming_operation', 'custom'):
        batches = []
        for i in range(count):
            batch_result = await process_batch(i + 1)
            batches.append(batch_result)

        total_records = sum(b['records_processed'] for b in batches)
        elasticapm.label(total_batches=count, total_records=total_records)

    return {
        "batches": batches,
        "total_records": total_records,
        "timestamp": datetime.utcnow()
    }


@app.get("/api/analytics", response_model=List[AnalyticsResult])
async def analytics():
    """Simulates complex analytics processing"""

    async def calculate_metric(metric_name: str, delay: float) -> AnalyticsResult:
        """Calculate a single metric"""
        with elasticapm.capture_span(f'calculate_{metric_name}', 'analytics'):
            await asyncio.sleep(delay)
            value = random.uniform(0, 100)
            elasticapm.label(metric=metric_name, value=round(value, 2))

            return AnalyticsResult(
                metric=metric_name,
                value=round(value, 2),
                timestamp=datetime.utcnow()
            )

    # Calculate multiple metrics in parallel
    metrics = [
        ('user_engagement', 0.3),
        ('conversion_rate', 0.25),
        ('avg_session_duration', 0.2),
        ('bounce_rate', 0.15)
    ]

    with elasticapm.capture_span('analytics_pipeline', 'custom'):
        results = await asyncio.gather(
            *[calculate_metric(name, delay) for name, delay in metrics]
        )
        elasticapm.label(metrics_calculated=len(results))

    return results


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for FastAPI"""
    elasticapm.capture_exception()
    elasticapm.label(error_type=type(exc).__name__, path=str(request.url))

    return {
        "error": str(exc),
        "type": type(exc).__name__,
        "path": str(request.url)
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    print("=" * 60)
    print("FastAPI APM Demo Service Starting...")
    print(f"APM Service Name: {apm_config['SERVICE_NAME']}")
    print(f"APM Server URL: {apm_config['SERVER_URL']}")
    print(f"Environment: {apm_config['ENVIRONMENT']}")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    print("Shutting down FastAPI APM Demo Service...")
    if apm:
        apm.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "fastapi_apm:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
