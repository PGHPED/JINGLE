# 🚀 24/7 Deployment Guide for Unity AI Discord Bot

## Quick Deployment Options

### 🟢 Replit (Recommended for Beginners)

**Pros:** One-click deploy, easy setup, built-in secrets management  
**Cons:** Limited free tier, requires subscription for 24/7

1. **Reserved VM Deployment:**
   - Click "Deploy" button in workspace header
   - Select "Reserved VM" deployment
   - Choose your plan and deploy
   - Your bot will run 24/7 automatically!

### 🟡 Render.com (Free Option)

**Pros:** Free 750 hours/month, easy GitHub integration  
**Cons:** Sleeps after 15 minutes of inactivity

1. **Setup:**
   - Fork/push this code to GitHub
   - Go to [render.com](https://render.com)
   - Connect your GitHub account
   - Create new "Web Service"

2. **Configuration:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
   - Add environment variables:
     - `DISCORD_BOT_TOKEN`: Your Discord bot token
     - `GEMINI_API_KEY`: Your Gemini API key
     - `ENVIRONMENT`: `production`

### 🔵 Railway (Premium Free Tier)

**Pros:** $5 free credit monthly, great performance  
**Cons:** Credit-based system

1. **Setup:**
   - Push code to GitHub
   - Go to [railway.app](https://railway.app)
   - Import from GitHub
   - Auto-deploys with `railway.json` config

2. **Environment Variables:**
   - Set `DISCORD_BOT_TOKEN` and `GEMINI_API_KEY`
   - Set `ENVIRONMENT=production`

### ⚫ Heroku (Legacy Option)

**Pros:** Reliable, well-documented  
**Cons:** No free tier anymore

1. **Setup:**
   ```bash
   heroku create your-unity-bot
   git push heroku main
   heroku ps:scale worker=1
   ```

2. **Environment Variables:**
   ```bash
   heroku config:set DISCORD_BOT_TOKEN=your_token
   heroku config:set GEMINI_API_KEY=your_key
   heroku config:set ENVIRONMENT=production
   ```

### 🐳 Docker Deployment

**For VPS/Self-hosting:**

```bash
# Build image
docker build -t unity-discord-bot .

# Run container
docker run -d --name unity-bot \
  -e DISCORD_BOT_TOKEN=your_token \
  -e GEMINI_API_KEY=your_key \
  -e ENVIRONMENT=production \
  --restart unless-stopped \
  unity-discord-bot
```

## 📊 Monitoring & Health Checks

### Built-in Endpoints (Production Mode)

- **Health Check:** `GET /health` - Bot status for monitoring
- **Statistics:** `GET /stats` - Bot performance metrics  
- **Ping:** `GET /ping` - Simple connectivity test

### Example Health Check Response:
```json
{
  "status": "healthy",
  "timestamp": 1694123456.789,
  "uptime_seconds": 3600,
  "bot_connected": true,
  "guilds_count": 10
}
```

## 🔧 Environment Variables

### Required:
- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `GEMINI_API_KEY` - Your Google Gemini API key

### Optional:
- `ENVIRONMENT` - Set to `production` for 24/7 hosting
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `PORT` - Web server port (default: 8080)

## 🛡️ Production Features

### ✅ Auto-Restart
- Automatic restart on connection failures
- Exponential backoff retry mechanism
- Maximum retry limits to prevent infinite loops

### ✅ Health Monitoring  
- Built-in web server for health checks
- Prometheus-compatible metrics endpoint
- Real-time bot statistics

### ✅ Error Handling
- Comprehensive error logging
- Graceful shutdown on system signals
- Rate limiting to prevent API abuse

### ✅ Performance Optimization
- Reduced Discord API logging in production
- Efficient message splitting for long responses
- Connection pooling and async operations

## 📋 Pre-Deployment Checklist

- [ ] Discord bot created and token obtained
- [ ] Gemini API key obtained from Google AI Studio
- [ ] Bot invited to Discord server with proper permissions
- [ ] Environment variables configured
- [ ] Hosting platform selected and account created
- [ ] Health check endpoint tested
- [ ] Bot commands tested in development

## 🚨 Troubleshooting

### Bot Won't Start:
1. Check environment variables are set correctly
2. Verify Discord token and Gemini API key are valid
3. Check logs for specific error messages

### Bot Goes Offline:
1. Check hosting platform status
2. Verify health check endpoint responds
3. Check for rate limiting or API quota issues

### Commands Not Working:
1. Ensure bot has proper Discord permissions
2. Check if commands are synced (logs will show)
3. Verify Gemini API is accessible

## 📈 Scaling & Performance

### For High-Traffic Bots:
- Use Redis for rate limiting and caching
- Implement command cooldowns
- Consider database for user preferences
- Set up proper monitoring (Grafana/Prometheus)

### Memory Usage:
- Typical usage: 50-100MB RAM
- Peak usage during AI responses: 150-200MB
- Recommended: 512MB minimum for production

## 💡 Best Practices

1. **Always test in development first**
2. **Monitor your API usage and costs**  
3. **Set up proper logging and alerts**
4. **Keep your tokens secure and rotate them regularly**
5. **Use semantic versioning for updates**
6. **Have a rollback plan for deployments**

## 🔄 Updates & Maintenance

### Updating the Bot:
1. Test changes locally first
2. Deploy to staging environment if available
3. Monitor logs during deployment
4. Verify all commands work after update
5. Monitor performance for 24-48 hours

Your Unity AI Discord Bot is now production-ready for 24/7 operation! 🎉