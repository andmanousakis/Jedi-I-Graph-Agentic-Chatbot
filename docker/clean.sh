#!/bin/bash

echo "🧼 Cleaning up Jedi containers and images..."

# Stop and remove containers (ignore if already stopped)
docker rm -f jedi_db jedi_api jedi_ui jedi_base_image jedi_tests 2>/dev/null

# Remove custom images
docker rmi -f jedi_api_image:latest jedi_ui_image:latest jedi_base_image jedi_test_image:latest 2>/dev/null

# Optionally remove Postgres base image if not used elsewhere
docker rmi -f postgres:15 2>/dev/null

echo "✅ Cleanup complete."


#!/bin/bash

echo "🧼 Cleaning up Jedi containers, images, and volumes..."
