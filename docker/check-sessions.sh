#!/bin/bash

# Script to check Telegram sessions status
# Usage: ./check-sessions.sh

set -e

echo "🔍 Checking Telegram sessions status..."

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: docker-compose.prod.yml not found. Please run this script from /opt/tg_ch_aggregator"
    exit 1
fi

# Check if sessions directory exists
if [ ! -d "sessions" ]; then
    echo "❌ Sessions directory not found"
    exit 1
fi

echo "📁 Sessions directory: $(pwd)/sessions"
echo ""

# Check for session files
if [ -f "sessions/user.session" ]; then
    echo "✅ user.session exists"
    ls -la sessions/user.session
else
    echo "❌ user.session missing"
fi

if [ -f "sessions/bot.session" ]; then
    echo "✅ bot.session exists"
    ls -la sessions/bot.session
else
    echo "❌ bot.session missing"
fi

echo ""

# Check if both sessions exist
if [ -f "sessions/user.session" ] && [ -f "sessions/bot.session" ]; then
    echo "✅ Both sessions are present"
    
    # Check if .env file exists for testing
    if [ -f ".env" ]; then
        echo ""
        echo "🧪 Testing sessions validity..."
        
        # Run a quick test to verify sessions work
        POSTGRES_DB=$(grep POSTGRES_DB .env | cut -d'=' -f2) \
        POSTGRES_USER=$(grep POSTGRES_USER .env | cut -d'=' -f2) \
        POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD .env | cut -d'=' -f2) \
        POSTGRES_HOST=postgres \
        POSTGRES_PORT=5432 \
        TELEGRAM_API_ID=$(grep TELEGRAM_API_ID .env | cut -d'=' -f2) \
        TELEGRAM_API_HASH=$(grep TELEGRAM_API_HASH .env | cut -d'=' -f2) \
        TELEGRAM_BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN .env | cut -d'=' -f2) \
        BACKEND_IMAGE=$(grep BACKEND_IMAGE .env | cut -d'=' -f2) \
        docker-compose -f docker/docker-compose.prod.yml run --rm create_sessions python -c "
from clients import bot_client, user_client
import asyncio

async def test_sessions():
    try:
        async with bot_client:
            bot_info = await bot_client.get_me()
            print(f'✅ Bot session valid: {bot_info.username}')
        async with user_client:
            user_info = await user_client.get_me()
            print(f'✅ User session valid: {user_info.username}')
        print('✅ All sessions are working correctly!')
    except Exception as e:
        print(f'❌ Session test failed: {e}')

asyncio.run(test_sessions())
" 2>/dev/null || echo "⚠️  Could not test sessions (missing .env or other issues)"
    else
        echo "⚠️  No .env file found - cannot test session validity"
    fi
else
    echo "❌ Missing one or both session files"
    echo ""
    echo "To create sessions, run:"
    echo "  ./docker/create-sessions.sh"
fi
