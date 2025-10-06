# Multi-stage Docker build for FastAPI application
# Security-focused with minimal attack surface

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG APP_VERSION=1.0.0
ARG BUILD_ID=unknown

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user for build
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set build arguments
ARG APP_VERSION=1.0.0
ARG BUILD_ID=unknown

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    APP_VERSION=${APP_VERSION} \
    BUILD_ID=${BUILD_ID} \
    ENVIRONMENT=production \
    PORT=8000 \
    HOST=0.0.0.0 \
    LOG_LEVEL=info

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup -m -s /bin/bash appuser

# Set work directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code
COPY --chown=appuser:appgroup src/ ./src/

# Create necessary directories and set permissions
RUN mkdir -p /app/logs \
    && chown -R appuser:appgroup /app \
    && chmod -R 755 /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/live || exit 1

# Expose port
EXPOSE 8000

# Add labels for better container management
LABEL maintainer="DevOps Team" \
      version="${APP_VERSION}" \
      build.id="${BUILD_ID}" \
      description="FastAPI microservice for EKS DevOps Demo" \
      org.opencontainers.image.title="EKS DevOps Demo API" \
      org.opencontainers.image.description="Sample FastAPI application for Kubernetes deployment" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.source="https://github.com/your-username/eks-devops-demo"

# Set the default command
CMD ["python", "src/main.py"]
