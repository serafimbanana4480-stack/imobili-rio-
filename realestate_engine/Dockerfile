FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml first for better caching
COPY pyproject.toml .
COPY realestate_engine/ ./realestate_engine/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/db data/backups data/cache data/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///data/db/realestate.db
ENV LOG_LEVEL=INFO

# Expose ports
EXPOSE 8501 8000

# Health check (Streamlit internal endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "realestate_engine/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
