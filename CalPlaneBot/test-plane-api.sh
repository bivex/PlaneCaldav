#!/bin/bash
# Plane API Troubleshooting Script

echo "=========================================="
echo "Plane API Troubleshooting"
echo "=========================================="
echo ""

# Load env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

echo "Configuration:"
echo "  Base URL: $PLANE_BASE_URL"
echo "  Workspace: $PLANE_WORKSPACE_SLUG"
echo "  Token: ${PLANE_API_TOKEN:0:20}..."
echo ""

echo "=========================================="
echo "Test 1: Check if Plane is accessible"
echo "=========================================="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" $PLANE_BASE_URL
echo ""

echo "=========================================="
echo "Test 2: Try /api/ endpoint"
echo "=========================================="
curl -s "$PLANE_BASE_URL/api/" | head -c 200
echo ""
echo ""

echo "=========================================="
echo "Test 3: Try Authorization: Bearer header"
echo "=========================================="
curl -s -H "Authorization: Bearer $PLANE_API_TOKEN" \
     "$PLANE_BASE_URL/api/workspaces/" | head -c 200
echo ""
echo ""

echo "=========================================="
echo "Test 4: Try X-API-Key header"
echo "=========================================="
curl -s -H "X-API-Key: $PLANE_API_TOKEN" \
     "$PLANE_BASE_URL/api/workspaces/" | head -c 200
echo ""
echo ""

echo "=========================================="
echo "Test 5: Try x-api-key header (lowercase)"
echo "=========================================="
curl -s -H "x-api-key: $PLANE_API_TOKEN" \
     "$PLANE_BASE_URL/api/workspaces/" | head -c 200
echo ""
echo ""

echo "=========================================="
echo "Test 6: Check /api/users/me/ (session-based)"
echo "=========================================="
curl -s "$PLANE_BASE_URL/api/users/me/" | head -c 200
echo ""
echo ""

echo "=========================================="
echo "Recommendations:"
echo "=========================================="
echo "1. If all tests return 401, regenerate API token in Plane"
echo "2. Check Plane documentation for correct auth header"
echo "3. Verify workspace slug is correct in Plane UI"
echo "4. Try accessing Plane API docs: $PLANE_BASE_URL/api/docs/"
echo ""
