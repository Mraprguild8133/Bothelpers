# Docker Setup for Telegram Group Management Bot

This guide explains how to run the Telegram Group Management Bot using Docker.

## Quick Start

1. **Set your environment variables:**
   ```bash
   export BOT_TOKEN="your_telegram_bot_token"
   export LOG_CHANNEL_ID="your_log_channel_id"
   ```

2. **Run the startup script:**
   ```bash
   ./docker-start.sh
   ```

## Manual Docker Setup

### Using Docker Compose (Recommended)

1. **Build and start all services:**
   ```bash
   docker-compose up -d
   ```

2. **Access the services:**
   - **Web Dashboard:** http://localhost:5001
   - **Telegram Bot:** Running in background

3. **View logs:**
   ```bash
   docker-compose logs -f
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

### Using Docker directly

1. **Build the image:**
   ```bash
   docker build -t telegram-bot .
   ```

2. **Run the bot:**
   ```bash
   docker run -d \
     --name telegram-bot \
     -e BOT_TOKEN="your_bot_token" \
     -e LOG_CHANNEL_ID="your_log_channel_id" \
     -v $(pwd)/data:/app/data \
     -p 5000:5000 \
     telegram-bot
   ```

3. **Run the web dashboard:**
   ```bash
   docker run -d \
     --name bot-dashboard \
     -v $(pwd)/data:/app/data \
     -p 5001:5000 \
     telegram-bot python web_interface.py
   ```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | Yes | - |
| `LOG_CHANNEL_ID` | Channel ID for external logging | No | - |
| `REQUIRED_CHANNEL` | Default required channel | No | - |
| `CHECK_SUBSCRIPTION` | Enable subscription checking | No | `true` |
| `CAPTCHA_TIMEOUT` | Captcha timeout in seconds | No | `300` |
| `CAPTCHA_DIFFICULTY` | Captcha difficulty (easy/medium/hard) | No | `medium` |
| `MAX_WARNINGS` | Maximum warnings before ban | No | `3` |
| `ENABLE_MEDIA_FILTERING` | Enable media content filtering | No | `true` |
| `ENABLE_LINK_FILTERING` | Enable suspicious link filtering | No | `true` |
| `ENABLE_BANNED_WORDS` | Enable banned words filtering | No | `true` |

## Persistent Data

The bot stores data in the `/app/data` directory inside the container. This is mapped to `./data` on your host system to ensure data persistence across container restarts.

## Health Checks

Both services include health checks:
- **Bot:** Monitors Telegram API connectivity
- **Dashboard:** Monitors web interface availability

Check health status:
```bash
docker-compose ps
```

## Updating

To update the bot to the latest version:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Troubleshooting

### Check logs:
```bash
docker-compose logs telegram-bot
docker-compose logs web-dashboard
```

### Restart services:
```bash
docker-compose restart
```

### Check container status:
```bash
docker-compose ps
docker stats
```

### Access container shell:
```bash
docker-compose exec telegram-bot bash
```

## Production Deployment

For production deployment:

1. Use environment files:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

2. Enable logging:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. Set up reverse proxy (nginx/caddy) for the web dashboard
4. Configure proper backup for the `data` directory
5. Set up monitoring and alerting

## Security Notes

- The containers run as non-root user for security
- Environment variables should be properly secured
- Web dashboard should be behind authentication in production
- Regular backups of the `data` directory are recommended
