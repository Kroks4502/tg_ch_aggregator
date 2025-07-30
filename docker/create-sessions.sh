#!/bin/bash

# Script to create Telegram sessions manually
# Usage: ./create-sessions.sh

set -e

echo "🔐 Creating Telegram sessions..."
echo ""
echo "⚠️  IMPORTANT: This process requires interactive input for Telegram authorization."
echo "   You will need to provide:"
echo "   1. Phone number"
echo "   2. Verification code (sent to Telegram)"
echo "   3. Two-factor authentication password (if enabled)"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "❌ Error: docker-compose.prod.yml not found. Please run this script from /opt/tg_ch_aggregator"
    exit 1
fi

# Check if sessions already exist
if [ -f "sessions/user.session" ] && [ -f "sessions/bot.session" ]; then
    echo "✅ Sessions already exist:"
    echo "   - sessions/user.session"
    echo "   - sessions/bot.session"
    echo ""
    echo "If you want to recreate sessions, delete these files first:"
    echo "   rm sessions/user.session sessions/bot.session"
    echo ""
    echo "To check session status, run:"
    echo "   ./docker/check-sessions.sh"
    exit 0
fi

# Check if .env file exists (for local development)
if [ -f ".env" ]; then
    echo "📄 Using .env file for environment variables"
    echo ""
    echo "🚀 Starting interactive session creation..."
    echo "   Follow the prompts to authorize your Telegram account."
    echo ""
    
    docker-compose -f docker/docker-compose.prod.yml run create_sessions
    
    # Clean up the container
    docker-compose -f docker/docker-compose.prod.yml rm -f create_sessions || true
    
    # Verify sessions were created
    if [ -f "sessions/user.session" ] && [ -f "sessions/bot.session" ]; then
        echo ""
        echo "✅ Sessions created successfully!"
        echo ""
        echo "📁 Session files:"
        ls -la sessions/
        echo ""
        echo "🔍 To verify sessions work correctly, run:"
        echo "   ./docker/check-sessions.sh"
    else
        echo ""
        echo "❌ Sessions creation failed"
        echo ""
        echo "💡 Troubleshooting:"
        echo "   - Check your phone number format (+79001234567)"
        echo "   - Verify the code sent to Telegram"
        echo "   - Make sure 2FA password is correct (if enabled)"
        echo "   - Try running the script again"
        exit 1
    fi
else
    echo "⚠️  No .env file found. Please set environment variables manually:"
    echo ""
    echo "POSTGRES_DB=your_db_name \\"
    echo "POSTGRES_USER=your_user \\"
    echo "POSTGRES_PASSWORD=your_password \\"
    echo "POSTGRES_HOST=postgres \\"
    echo "POSTGRES_PORT=5432 \\"
    echo "TELEGRAM_API_ID=your_api_id \\"
    echo "TELEGRAM_API_HASH=your_api_hash \\"
    echo "TELEGRAM_BOT_TOKEN=your_bot_token \\"
    echo "BACKEND_IMAGE=your_image \\"
    echo "docker-compose -f docker/docker-compose.prod.yml run create_sessions"
    echo ""
    echo "Or create a .env file with these variables."
    exit 1
fi
