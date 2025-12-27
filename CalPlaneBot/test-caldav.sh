#!/bin/bash
#
# Wrapper script for testing CalDAV authentication
# Uses CalPlaneBot Docker container to run Python script
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="calplanebot_calplanebot_1"

echo "🔍 Testing CalDAV authentication..."
echo "========================================"

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ Container $CONTAINER_NAME is not running"
    echo "Run: docker-compose up -d"
    exit 1
fi

# Copy script to container
echo "📋 Copying script to container..."
docker cp "$SCRIPT_DIR/test_caldav_auth.py" "$CONTAINER_NAME:/app/test_caldav_auth.py"

# Run testing
echo "🚀 Starting testing..."
echo ""

if [ $# -eq 0 ]; then
    # Use default values
    docker exec "$CONTAINER_NAME" python /app/test_caldav_auth.py
else
    # Pass arguments
    docker exec "$CONTAINER_NAME" python /app/test_caldav_auth.py "$@"
fi

echo ""
echo "========================================"
echo "✅ Testing completed"

