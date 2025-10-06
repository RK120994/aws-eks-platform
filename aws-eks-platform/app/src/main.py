"""
FastAPI Sample Application for EKS DevOps Demo
Simple microservice with health checks and monitoring endpoints
"""

import logging
import os
import time
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ERROR_COUNT = Counter(
    'http_errors_total',
    'Total number of HTTP errors',
    ['method', 'endpoint', 'status']
)

# FastAPI app initialization
app = FastAPI(
    title="EKS DevOps Demo API",
    description="A sample FastAPI microservice for EKS deployment demonstration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Application state
app_state = {
    "startup_time": time.time(),
    "version": os.getenv("APP_VERSION", "1.0.0"),
    "environment": os.getenv("ENVIRONMENT", "development"),
    "build_id": os.getenv("BUILD_ID", "unknown")
}

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Middleware to collect Prometheus metrics for all requests"""
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        
        # Record metrics
        REQUEST_COUNT.labels(method=method, endpoint=path, status=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=path).observe(time.time() - start_time)
        
        if status_code >= 400:
            ERROR_COUNT.labels(method=method, endpoint=path, status=status_code).inc()
            
        return response
        
    except Exception as e:
        # Record error metrics
        ERROR_COUNT.labels(method=method, endpoint=path, status="500").inc()
        REQUEST_COUNT.labels(method=method, endpoint=path, status="500").inc()
        logger.error(f"Request failed: {method} {path} - {str(e)}")
        raise

@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with basic application information"""
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to EKS DevOps Demo API",
        "version": app_state["version"],
        "environment": app_state["environment"],
        "status": "healthy",
        "uptime_seconds": round(time.time() - app_state["startup_time"], 2)
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    logger.debug("Health check endpoint accessed")
    
    # Simple health check logic
    current_time = time.time()
    uptime = current_time - app_state["startup_time"]
    
    health_status = {
        "status": "healthy",
        "timestamp": current_time,
        "uptime_seconds": round(uptime, 2),
        "version": app_state["version"],
        "environment": app_state["environment"],
        "checks": {
            "application": "pass",
            "database": "pass",  # Mock database check
            "external_service": "pass"  # Mock external service check
        }
    }
    
    return health_status

@app.get("/health/live")
async def liveness_probe() -> Dict[str, str]:
    """Kubernetes liveness probe endpoint"""
    logger.debug("Liveness probe accessed")
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness_probe() -> Dict[str, str]:
    """Kubernetes readiness probe endpoint"""
    logger.debug("Readiness probe accessed")
    
    # Check if application is ready to serve traffic
    # In a real application, you would check database connections,
    # external services, etc.
    
    return {"status": "ready"}

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    """Prometheus metrics endpoint"""
    logger.debug("Metrics endpoint accessed")
    return generate_latest()

@app.get("/info")
async def app_info() -> Dict[str, Any]:
    """Application information endpoint"""
    logger.info("Info endpoint accessed")
    
    return {
        "application": {
            "name": "EKS DevOps Demo API",
            "version": app_state["version"],
            "build_id": app_state["build_id"],
            "environment": app_state["environment"]
        },
        "runtime": {
            "startup_time": app_state["startup_time"],
            "uptime_seconds": round(time.time() - app_state["startup_time"], 2),
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        },
        "environment_variables": {
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "not_set"),
            "APP_VERSION": os.getenv("APP_VERSION", "not_set"),
            "BUILD_ID": os.getenv("BUILD_ID", "not_set"),
            "DATABASE_URL": "***" if os.getenv("DATABASE_URL") else "not_set",
            "API_KEY": "***" if os.getenv("API_KEY") else "not_set"
        }
    }

@app.get("/hello/{name}")
async def hello_name(name: str) -> Dict[str, str]:
    """Personalized greeting endpoint"""
    logger.info(f"Hello endpoint accessed with name: {name}")
    
    if len(name) > 50:
        logger.warning(f"Name too long: {len(name)} characters")
        raise HTTPException(status_code=400, detail="Name too long")
    
    return {
        "message": f"Hello, {name}!",
        "timestamp": time.time(),
        "environment": app_state["environment"]
    }

@app.get("/error/test")
async def test_error():
    """Endpoint to test error handling and monitoring"""
    logger.error("Test error endpoint accessed - triggering error")
    raise HTTPException(status_code=500, detail="This is a test error for monitoring purposes")

@app.post("/echo")
async def echo_post(request: Request) -> Dict[str, Any]:
    """Echo endpoint that returns request information"""
    logger.info("Echo endpoint accessed")
    
    body = await request.body()
    
    return {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "body": body.decode() if body else None,
        "query_params": dict(request.query_params),
        "timestamp": time.time()
    }

@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    logger.info("Application starting up...")
    logger.info(f"Version: {app_state['version']}")
    logger.info(f"Environment: {app_state['environment']}")
    logger.info(f"Build ID: {app_state['build_id']}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler"""
    logger.info("Application shutting down...")

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False,
        access_log=True
    )
