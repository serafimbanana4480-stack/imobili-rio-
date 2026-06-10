#!/bin/bash

# Deployment script for Real Estate Opportunity Engine
# This script handles local deployment with Docker

set -e

echo "🚀 Starting deployment of Real Estate Opportunity Engine..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env file not found. Using default values."
fi

# Build Docker image
echo "📦 Building Docker image..."
docker build -t realestate-engine:latest .

# Stop existing container if running
if docker ps -a | grep -q realestate-engine; then
    echo "🛑 Stopping existing container..."
    docker stop realestate-engine || true
    docker rm realestate-engine || true
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/db data/backups data/cache data/logs

# Run database migrations
echo "🗄️  Running database migrations..."
docker run --rm \
    -v $(pwd)/data:/app/data \
    -e DATABASE_URL=$DATABASE_URL \
    realestate-engine:latest \
    alembic upgrade head

# Start new container
echo "▶️  Starting new container..."
docker run -d \
    --name realestate-engine \
    --restart unless-stopped \
    -p 8501:8501 \
    -v $(pwd)/data:/app/data \
    -e DATABASE_URL=$DATABASE_URL \
    -e REDIS_URL=$REDIS_URL \
    -e TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN \
    -e TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID \
    -e LOG_LEVEL=$LOG_LEVEL \
    realestate-engine:latest

# Wait for container to be healthy
echo "⏳ Waiting for container to be healthy..."
sleep 10

# Check container status
if docker ps | grep -q realestate-engine; then
    echo "✅ Deployment successful! Container is running."
    echo "📊 Dashboard available at: http://localhost:8501"
else
    echo "❌ Deployment failed. Container is not running."
    docker logs realestate-engine
    exit 1
fi

# Show logs
echo "📋 Recent logs:"
docker logs --tail 20 realestate-engine
