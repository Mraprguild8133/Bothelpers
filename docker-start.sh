#!/bin/bash

# Docker startup script for Telegram Group Management Bot
echo "🐳 Starting Telegram Group Management Bot with Docker..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
mkdir -p data logs

# Set environment variables if not already set
if [ -z "$BOT_TOKEN" ]; then
    echo "⚠️  BOT_TOKEN environment variable is not set."
    echo "Please set your Telegram bot token:"
    echo "export BOT_TOKEN='your_bot_token_here'"
    echo ""
fi

if [ -z "$LOG_CHANNEL_ID" ]; then
    echo "⚠️  LOG_CHANNEL_ID environment variable is not set."
    echo "Please set your log channel ID (optional):"
    echo "export LOG_CHANNEL_ID='your_log_channel_id'"
    echo ""
fi

# Build and start the containers
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting containers..."
docker-compose up -d

echo ""
echo "✅ Bot containers are starting up!"
echo ""
echo "📊 Web Dashboard: http://localhost:5001"
echo "🤖 Telegram Bot: Running in background"
echo ""
echo "📋 Useful commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop bot:      docker-compose down"
echo "  Restart:       docker-compose restart"
echo "  Update:        docker-compose pull && docker-compose up -d"
echo ""
echo "🔍 Check status: docker-compose ps"