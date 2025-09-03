"""
Keep alive server for 24/7 hosting platforms
Provides health checks and monitoring endpoints
"""
import asyncio
import logging
from aiohttp import web, ClientSession
import json
import time

class KeepAlive:
    def __init__(self, bot):
        self.bot = bot
        self.app = web.Application()
        self.setup_routes()
        self.start_time = time.time()
        self.request_count = 0
        
    def setup_routes(self):
        self.app.router.add_get('/', self.home)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/stats', self.bot_stats)
        self.app.router.add_get('/ping', self.ping)
        
    async def home(self, request):
        return web.json_response({
            'name': 'Unity AI Discord Bot',
            'status': 'running',
            'uptime': time.time() - self.start_time,
            'bot_connected': hasattr(self.bot, 'user') and self.bot.user is not None
        })
        
    async def health_check(self, request):
        """Health check endpoint for hosting platforms"""
        self.request_count += 1
        
        # Check if bot is connected
        is_healthy = (
            hasattr(self.bot, 'user') and 
            self.bot.user is not None and
            not self.bot.is_closed()
        )
        
        status = 'healthy' if is_healthy else 'unhealthy'
        http_status = 200 if is_healthy else 503
        
        return web.json_response({
            'status': status,
            'timestamp': time.time(),
            'uptime_seconds': time.time() - self.start_time,
            'bot_connected': is_healthy,
            'guilds_count': len(self.bot.guilds) if hasattr(self.bot, 'guilds') else 0
        }, status=http_status)
        
    async def bot_stats(self, request):
        """Bot statistics endpoint"""
        if not hasattr(self.bot, 'user') or self.bot.user is None:
            return web.json_response({'error': 'Bot not ready'}, status=503)
            
        return web.json_response({
            'bot_name': str(self.bot.user),
            'bot_id': self.bot.user.id,
            'guilds': len(self.bot.guilds),
            'users': sum(len(guild.members) for guild in self.bot.guilds),
            'commands': len(self.bot.tree.get_commands()),
            'latency_ms': round(self.bot.latency * 1000, 2),
            'uptime_seconds': time.time() - self.start_time,
            'requests_served': self.request_count
        })
        
    async def ping(self, request):
        """Simple ping endpoint"""
        return web.json_response({
            'pong': True,
            'timestamp': time.time(),
            'latency_ms': round(self.bot.latency * 1000, 2) if hasattr(self.bot, 'latency') else None
        })
        
    async def start_server(self, port=8080):
        """Start the keep alive server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logging.info(f"🌐 Keep-alive server started on port {port}")
        logging.info(f"📊 Health check available at: http://0.0.0.0:{port}/health")
        return runner