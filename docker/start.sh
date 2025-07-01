#!/bin/bash

echo "📦 Building shared base image..."
docker build -f Dockerfile.base -t jedi_base_image ..

echo "📦 Building Docker images..."

# Ensure .env exists
if [ ! -f ../.env ]; then
  echo "❌ .env file not found in parent directory."
  exit 1
fi

# Export environment variables
set -a
source ../.env
set +a

# Run docker compose
echo "🚀 Starting services..."
docker compose up --build

echo "✅ Jedi Agent is running at:"
echo "   - Jedi AI Agent: http://api:8000/ask/"
echo "   - Analytics:     http://api:8000/analytics/"
echo "   - UI:            http://api:8501/"
