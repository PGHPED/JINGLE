import discord
from discord import app_commands
import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio
import logging
import sys
import threading
from aiohttp import web
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Global bot reference for web server
bot_instance = None

# Web server functions
async def health_check(request):
    global bot_instance
    is_healthy = bot_instance and hasattr(bot_instance, 'user') and bot_instance.user is not None
    return web.json_response({
        'status': 'healthy' if is_healthy else 'starting',
        'bot_connected': is_healthy
    })

async def home_page(request):
    return web.json_response({
        'name': 'Unity AI Discord Bot',
        'status': 'running',
        'environment': ENVIRONMENT
    })

def start_web_server():
    """Start web server in a separate thread"""
    port = int(os.getenv('PORT', 8080))
    
    async def init_server():
        app = web.Application()
        app.router.add_get('/', home_page)
        app.router.add_get('/health', health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logging.info(f"Web server running on port {port}")
        
        # Keep server alive
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await runner.cleanup()
    
    # Run server
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_server())

# Start web server immediately if in production
if ENVIRONMENT == 'production':
    logging.info("Starting web server...")
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    time.sleep(2)  # Give server time to start

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True

class UnityBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        global bot_instance
        bot_instance = self

    async def setup_hook(self):
        try:
            await self.tree.sync()
            logging.info("Commands synced successfully!")
        except Exception as e:
            logging.error(f"Error syncing commands: {e}")

bot = UnityBot()

class UnityHelper:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.rate_limit = {}
    
    async def _rate_limit_check(self, user_id: int) -> bool:
        current_time = time.time()
        if user_id in self.rate_limit:
            if current_time - self.rate_limit[user_id] < 3:
                return False
        self.rate_limit[user_id] = current_time
        return True
    
    async def generate_response(self, prompt: str, system_context: str = "") -> str:
        try:
            full_prompt = f"{system_context}\n\n{prompt}" if system_context else prompt
            response = await asyncio.to_thread(self.model.generate_content, full_prompt)
            return response.text
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return "Sorry, I'm having trouble with the AI service right now."
    
    async def answer_unity_question(self, question: str) -> str:
        system_context = "You are a Unity development expert. Provide clear, practical advice."
        return await self.generate_response(f"Unity question: {question}", system_context)

unity_helper = UnityHelper()

@bot.event
async def on_ready():
    logging.info(f'{bot.user} connected to Discord!')
    logging.info(f'Serving {len(bot.guilds)} servers')
    
    activity = discord.Activity(type=discord.ActivityType.playing, name="Unity development")
    await bot.change_presence(activity=activity)

@bot.tree.command(name='ask', description='Ask Unity development questions')
async def ask_unity(interaction: discord.Interaction, question: str):
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("Please wait before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    try:
        response = await unity_helper.answer_unity_question(question)
        
        if len(response) > 1900:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            await interaction.followup.send(chunks[0])
            for chunk in chunks[1:]:
                await interaction.followup.send(chunk)
        else:
            await interaction.followup.send(response)
            
    except Exception as e:
        logging.error(f"Ask command error: {e}")
        await interaction.followup.send("Sorry, I encountered an error.")

@bot.tree.command(name='ping', description='Check bot status')
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! {latency}ms")

async def main():
    try:
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not discord_token:
            logging.error("DISCORD_BOT_TOKEN not set!")
            sys.exit(1)
        
        if not gemini_key:
            logging.error("GEMINI_API_KEY not set!")
            sys.exit(1)
        
        logging.info("Starting Discord bot...")
        await bot.start(discord_token)
        
    except Exception as e:
        logging.error(f"Bot error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
