# AgentOS Dockerfile
FROM python:3.11-slim

LABEL org.opencontainers.image.title="AgentOS"
LABEL org.opencontainers.image.description="Production Multi-Agent Framework"
LABEL org.opencontainers.image.vendor="AgentOS"

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install AgentOS
RUN pip install --no-cache-dir nexus-agentos>=1.14.5

# Create non-root user
RUN useradd -m -s /bin/bash agentos && chown -R agentos:agentos /app
USER agentos

# Default entrypoint
ENTRYPOINT ["agentos"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]

# Expose ports
EXPOSE 8000 9090
