#!/bin/bash
# BossHelp Deployment Verification Script

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

echo "🔍 BossHelp Deployment Verification"
echo "======================================"
echo "Backend: $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

fail() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Backend Health Check
echo "1. Backend Health Check"
HEALTH=$(curl -s "$BACKEND_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    pass "Backend is healthy"
else
    fail "Backend health check failed"
fi

# 2. API Endpoints
echo ""
echo "2. API Endpoints"

# GET /api/v1/games
GAMES=$(curl -s "$BACKEND_URL/api/v1/games")
if echo "$GAMES" | grep -q "elden-ring"; then
    pass "GET /api/v1/games - OK"
else
    fail "GET /api/v1/games - Failed"
fi

# POST /api/v1/ask (Mock test)
ASK_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/ask" \
    -H "Content-Type: application/json" \
    -d '{"game_id":"elden-ring","question":"test","spoiler_level":"none","session_id":"verify"}')
if echo "$ASK_RESPONSE" | grep -q "answer"; then
    pass "POST /api/v1/ask - OK"
else
    fail "POST /api/v1/ask - Failed"
fi

# 3. Frontend Pages
echo ""
echo "3. Frontend Pages"

# Home page
HOME=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL")
if [ "$HOME" = "200" ]; then
    pass "Home page (/) - OK"
else
    fail "Home page (/) - HTTP $HOME"
fi

# Chat page
CHAT=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/chat/elden-ring")
if [ "$CHAT" = "200" ]; then
    pass "Chat page (/chat/elden-ring) - OK"
else
    fail "Chat page - HTTP $CHAT"
fi

# Game page
GAME=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL/games/elden-ring")
if [ "$GAME" = "200" ]; then
    pass "Game page (/games/elden-ring) - OK"
else
    fail "Game page - HTTP $GAME"
fi

# 4. Summary
echo ""
echo "======================================"
echo "Verification Complete!"
echo ""
echo "Next Steps:"
echo "  1. Test full user flow in browser"
echo "  2. Check error logs: railway logs -f"
echo "  3. Run initial data collection if needed"
