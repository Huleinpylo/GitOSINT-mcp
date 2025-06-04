# GitOSINT-MCP Docker Image
# Multi-stage build for optimized container size

FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add metadata labels for MCP addon
LABEL maintainer="Huleinpylo <contact@huleinpylo.dev>" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="GitOSINT-MCP" \
      org.label-schema.description="OSINT for Git repositories via Model Context Protocol" \
      org.label-schema.url="https://github.com/Huleinpylo/GitOSINT-mcp" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/Huleinpylo/GitOSINT-mcp" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0" \
      org.opencontainers.image.title="GitOSINT-MCP" \
      org.opencontainers.image.description="MCP server for OSINT intelligence gathering from Git repositories" \
      org.opencontainers.image.authors="Huleinpylo" \
      org.opencontainers.image.vendor="Huleinpylo" \
      org.opencontainers.image.licenses="MIT"

# Install system dependencies for the MCP addon
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Copy system dependencies from builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 -s /bin/bash gitosint && \
    mkdir -p /app /app/data /app/logs && \
    chown -R gitosint:gitosint /app

# Set working directory and copy Python packages
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code for MCP addon
COPY --chown=gitosint:gitosint src/ ./src/
COPY --chown=gitosint:gitosint pyproject.toml ./
COPY --chown=gitosint:gitosint README.md ./

# Install the GitOSINT-MCP package
RUN pip install --no-cache-dir -e .

# Switch to non-root user
USER gitosint

# Create data and logs directories
RUN mkdir -p /app/data /app/logs

# Expose port for MCP server
EXPOSE 8080

# Health check for MCP addon
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Environment variables for MCP configuration
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=8080 \
    MAX_REPOS_PER_REQUEST=10 \
    RATE_LIMIT_REQUESTS=100 \
    RATE_LIMIT_WINDOW=3600

# Default command to start MCP server
CMD ["gitosint-mcp", "serve", "--host", "0.0.0.0", "--port", "8080", "--transport", "sse"]