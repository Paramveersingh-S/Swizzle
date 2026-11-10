# ==============================================================================
# Swizzle Continuous Batching Engine — Production Dockerfile
# ==============================================================================

FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install core runtime dependencies
RUN pip install --no-cache-dir \
    numpy>=1.24.0 \
    fastapi>=0.100.0 \
    uvicorn>=0.22.0 \
    pydantic>=2.0.0

# Copy engine runtime, benchmarks and tests
COPY swizzle/ ./swizzle/
COPY benchmarks/ ./benchmarks/
COPY tests/ ./tests/

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "swizzle.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
