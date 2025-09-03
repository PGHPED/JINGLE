import discord
from discord import app_commands
import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio
import logging
import time
import sys
from typing import Optional, List, Dict
from aiohttp import web
import threading

# Load environment variables
load_dotenv()

# Configure production-ready logging
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True

class UnityBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.web_server_task = None

    async def setup_hook(self):
        """Initialize bot and sync commands"""
        try:
            # Start web server FIRST for Render
            if ENVIRONMENT == 'production':
                port = int(os.getenv('PORT', 8080))
                self.web_server_task = asyncio.create_task(self.start_web_server(port))
                logging.info(f"Web server task created for port {port}")
            
            # Then sync commands with Discord
            await self.tree.sync()
            logging.info("Commands synced successfully!")
                
        except Exception as e:
            logging.error(f"Error during setup: {e}")
            raise
    
    async def start_web_server(self, port):
        """Start web server for Render"""
        try:
            app = web.Application()
            
            # Add routes
            app.router.add_get('/', self.home_handler)
            app.router.add_get('/health', self.health_handler)
            app.router.add_get('/ping', self.ping_handler)
            
            # Create and start server
            runner = web.AppRunner(app)
            await runner.setup()
            
            site = web.TCPSite(runner, '0.0.0.0', port)
            await site.start()
            
            logging.info(f"Web server started successfully on 0.0.0.0:{port}")
            logging.info(f"Health check: http://0.0.0.0:{port}/health")
            
            # Keep the server running
            while True:
                await asyncio.sleep(3600)  # Sleep for 1 hour, then continue
                
        except Exception as e:
            logging.error(f"Web server error: {e}")
            raise
    
    async def home_handler(self, request):
        """Home endpoint"""
        return web.json_response({
            'name': 'Unity AI Discord Bot',
            'status': 'running',
            'bot_connected': hasattr(self, 'user') and self.user is not None
        })
    
    async def health_handler(self, request):
        """Health check endpoint"""
        is_healthy = hasattr(self, 'user') and self.user is not None and not self.is_closed()
        
        return web.json_response({
            'status': 'healthy' if is_healthy else 'unhealthy',
            'bot_connected': is_healthy,
            'guilds_count': len(self.guilds) if hasattr(self, 'guilds') else 0
        }, status=200 if is_healthy else 503)
    
    async def ping_handler(self, request):
        """Ping endpoint"""
        return web.json_response({
            'pong': True,
            'latency_ms': round(self.latency * 1000, 2) if hasattr(self, 'latency') else None
        })
    
    async def close(self):
        """Graceful shutdown"""
        logging.info("Initiating graceful shutdown...")
        
        if self.web_server_task:
            self.web_server_task.cancel()
        
        await super().close()
        logging.info("Bot shutdown complete")

bot = UnityBot()

class UnityHelper:
    """Unity development assistant using Gemini AI"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.rate_limit = {}
    
    async def _rate_limit_check(self, user_id: int) -> bool:
        """Rate limiting"""
        current_time = time.time()
        if user_id in self.rate_limit:
            if current_time - self.rate_limit[user_id] < 3:
                return False
        self.rate_limit[user_id] = current_time
        return True
    
    async def generate_response(self, prompt: str, system_context: str = "") -> str:
        """Generate AI response"""
        try:
            full_prompt = f"{system_context}\n\n{prompt}" if system_context else prompt
            response = await asyncio.to_thread(self.model.generate_content, full_prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return "Sorry, I'm having trouble with the AI service right now."
    
    async def answer_unity_question(self, question: str) -> str:
        """Answer Unity questions"""
        system_context = """
        You are a Unity development expert. Provide clear, practical advice for Unity developers.
        Include code examples when helpful and focus on actionable solutions.
        """
        
        prompt = f"Unity development question: {question}"
        return await self.generate_response(prompt, system_context)

unity_helper = UnityHelper()

@bot.event
async def on_ready():
    """Bot ready event"""
    logging.info(f'{bot.user} connected to Discord!')
    logging.info(f'Unity AI Assistant ready!')
    logging.info(f'Serving {len(bot.guilds)} servers')
    
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name="Unity development"
    )
    await bot.change_presence(activity=activity, status=discord.Status.online)

@bot.tree.command(name='ask', description='Ask any Unity development question')
async def ask_unity(interaction: discord.Interaction, question: str):
    """Ask Unity questions"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("Please wait before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.answer_unity_question(question)
        
        # Handle long responses
        if len(response) > 1900:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            await interaction.followup.send(chunks[0])
            for chunk in chunks[1:]:
                await interaction.followup.send(chunk)
        else:
            await interaction.followup.send(response)
            
    except Exception as e:
        logging.error(f"Question error: {e}")
        await interaction.followup.send("Sorry, I encountered an error. Please try again.")

@bot.tree.command(name='ping', description='Check bot status')
async def ping(interaction: discord.Interaction):
    """Check bot status"""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! Latency: {latency}ms")

@bot.tree.command(name='help', description='Show available commands')
async def help_unity(interaction: discord.Interaction):
    """Show help"""
    embed = discord.Embed(
        title="Unity AI Assistant Commands",
        description="Available commands:",
        color=0x00ff00
    )
    
    embed.add_field(
        name="Commands",
        value="• `/ask` - Ask Unity questions\n• `/ping` - Check bot status\n• `/help` - Show this help",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

async def main():
    """Main function"""
    try:
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not discord_token:
            logging.error("DISCORD_BOT_TOKEN not set!")
            sys.exit(1)
        
        if not gemini_key:
            logging.error("GEMINI_API_KEY not set!")
            sys.exit(1)
        
        logging.info(f"Starting bot (Environment: {ENVIRONMENT})...")
        
        # Start the bot
        await bot.start(discord_token)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        sys.exit(1)
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot terminated by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
