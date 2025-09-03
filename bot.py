import discord
from discord import app_commands
import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio
import logging
import time
import json
import signal
import sys
from typing import Optional, List, Dict
import re
from keep_alive import KeepAlive

# Load environment variables
load_dotenv()

# Configure production-ready logging
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

# Configure logging handlers based on environment
handlers = [logging.StreamHandler(sys.stdout)]

# Only add file logging in development and if we can write to the directory
if ENVIRONMENT == 'development':
    try:
        # Test if we can write to current directory
        test_file = 'test_write.tmp'
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        handlers.append(logging.FileHandler('bot.log'))
    except (PermissionError, OSError):
        # Can't write files, skip file logging
        pass

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=handlers
)

# Reduce discord.py logging noise in production
if ENVIRONMENT == 'production':
    logging.getLogger('discord').setLevel(logging.WARNING)
    logging.getLogger('discord.http').setLevel(logging.WARNING)
    logging.getLogger('discord.gateway').setLevel(logging.WARNING)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True

class UnityBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.keep_alive = None
        self.keep_alive_runner = None
        self.is_shutting_down = False

    async def setup_hook(self):
        """Initialize bot and sync commands"""
        try:
            # Sync commands with Discord
            await self.tree.sync()
            logging.info("Commands synced successfully!")
            
            # Start keep-alive server for 24/7 hosting
            if ENVIRONMENT == 'production':
                self.keep_alive = KeepAlive(self)
                port = int(os.getenv('PORT', 8080))
                # Guardar la referencia del runner
                self.keep_alive_runner = await self.keep_alive.start_server(port)
                logging.info(f"Keep-alive server initialized on port {port}")
                
        except Exception as e:
            logging.error(f"Error during setup: {e}")
            raise
    
    async def close(self):
        """Graceful shutdown"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logging.info("Initiating graceful shutdown...")
        
        try:
            if self.keep_alive_runner:
                logging.info("Shutting down keep-alive server...")
                await self.keep_alive_runner.cleanup()
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
        
        await super().close()
        logging.info("Bot shutdown complete")

bot = UnityBot()

class UnityHelper:
    """Advanced Unity development assistant using Gemini AI"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.rate_limit = {}
        self.common_errors = self._load_common_errors()
    
    def _load_common_errors(self) -> Dict[str, str]:
        """Load common Unity errors and solutions"""
        return {
            "NullReferenceException": "Object reference not set to an instance of an object. Check if objects are properly initialized.",
            "MissingReferenceException": "The object referenced by this script has been destroyed. Update references in the Inspector.",
            "ArgumentException": "Check method parameters and ensure they meet the required conditions.",
            "IndexOutOfRangeException": "Array or list index is outside the bounds. Check array/list length before accessing.",
            "build failed": "Check console for compilation errors, missing dependencies, or incorrect build settings."
        }
    
    async def _rate_limit_check(self, user_id: int) -> bool:
        """Simple rate limiting to prevent API abuse"""
        current_time = time.time()
        if user_id in self.rate_limit:
            if current_time - self.rate_limit[user_id] < 3:  # 3 second cooldown
                return False
        self.rate_limit[user_id] = current_time
        return True
    
    async def generate_response(self, prompt: str, system_context: str = "") -> str:
        """Generate AI response with enhanced error handling"""
        try:
            full_prompt = f"{system_context}\n\n{prompt}" if system_context else prompt
            response = await asyncio.to_thread(
                self.model.generate_content, full_prompt
            )
            return response.text
        except Exception as e:
            logging.error(f"Gemini API error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service right now. Please try again in a moment."
    
    async def generate_csharp_script(self, description: str, script_type: str = "general") -> str:
        """Generate specialized C# scripts for Unity"""
        system_context = """
        You are an expert Unity C# developer. Generate clean, efficient, and well-documented code.
        Follow Unity coding conventions and best practices. Include proper error handling and performance considerations.
        """
        
        script_templates = {
            "movement": "Focus on smooth player/object movement with physics integration",
            "ui": "Create responsive UI components with proper event handling",
            "ai": "Implement intelligent AI behavior with state machines or behavior trees",
            "audio": "Handle audio playback, mixing, and 3D spatial audio",
            "general": "Create a well-structured, reusable component"
        }
        
        template_hint = script_templates.get(script_type, script_templates["general"])
        
        prompt = f"""
        Create a C# script for Unity: {description}
        
        Requirements:
        - {template_hint}
        - Include XML documentation comments
        - Add [SerializeField] for Inspector-visible fields
        - Implement proper Unity lifecycle methods (Awake, Start, Update, etc.)
        - Include error checking and null reference protection
        - Follow Unity naming conventions
        - Add performance optimization comments where relevant
        
        Format as complete, ready-to-use code.
        """
        return await self.generate_response(prompt, system_context)
    
    async def answer_unity_question(self, question: str) -> str:
        """Enhanced general Unity question answering"""
        system_context = """
        You are a comprehensive Unity expert with deep knowledge of all Unity systems.
        Provide accurate, up-to-date, and practical advice for Unity developers.
        """
        
        prompt = f"""
        Unity development question: {question}
        
        Provide:
        1. Clear, detailed answer
        2. Code examples when relevant
        3. Step-by-step instructions
        4. Best practices and tips
        5. Common gotchas to avoid
        6. Unity documentation references
        7. Related topics to explore
        
        Make it comprehensive but accessible to developers of all levels.
        """
        return await self.generate_response(prompt, system_context)

# Initialize Unity helper
unity_helper = UnityHelper()

@bot.event
async def on_ready():
    """Bot ready event - called when bot connects to Discord"""
    user_count = sum(len(guild.members) for guild in bot.guilds)
    
    logging.info(f'{bot.user} connected to Discord!')
    logging.info(f'Unity AI Assistant ready for game development!')
    logging.info(f'Serving {len(bot.guilds)} servers with {user_count} users')
    logging.info(f'Commands: {len(bot.tree.get_commands())} slash commands registered')
    logging.info(f'Environment: {ENVIRONMENT}')
    
    # Set bot activity based on environment
    if ENVIRONMENT == 'production':
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers • Unity development 24/7"
        )
    else:
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="Unity development (dev mode)"
        )
    
    await bot.change_presence(activity=activity, status=discord.Status.online)

# Utility function for handling long responses
async def send_long_response(interaction: discord.Interaction, response: str, code_type: str = None, is_followup: bool = True):
    """Handle long responses by splitting them appropriately"""
    max_length = 1900 if code_type else 1900
    
    if len(response) <= max_length:
        content = f"```{code_type}\n{response}\n```" if code_type else response
        if is_followup:
            await interaction.followup.send(content)
        else:
            await interaction.response.send_message(content)
        return
    
    # Split long responses
    if code_type:
        # For code, split by lines to preserve formatting
        lines = response.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1  # +1 for newline
            if current_length + line_length > max_length and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        # Send first chunk
        first_chunk = f"```{code_type}\n{chunks[0]}\n```"
        if is_followup:
            await interaction.followup.send(first_chunk)
        else:
            await interaction.response.send_message(first_chunk)
        
        # Send remaining chunks
        for chunk in chunks[1:]:
            await interaction.followup.send(f"```{code_type}\n{chunk}\n```")
    else:
        # For regular text, split by character limit
        chunks = [response[i:i+max_length] for i in range(0, len(response), max_length)]
        
        if is_followup:
            await interaction.followup.send(chunks[0])
        else:
            await interaction.response.send_message(chunks[0])
        
        for chunk in chunks[1:]:
            await interaction.followup.send(chunk)

@bot.tree.command(name='ask', description='Ask any Unity development question')
async def ask_unity(interaction: discord.Interaction, question: str):
    """Ask comprehensive Unity development questions"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.answer_unity_question(question)
        await send_long_response(interaction, response)
    except Exception as e:
        logging.error(f"Question answering error: {e}")
        await interaction.followup.send(f"Sorry, I encountered an error answering your question. Please try again.")

@bot.tree.command(name='script', description='Generate a C# script for Unity')
@app_commands.describe(
    description='What the script should do',
    script_type='Type of script (movement, ui, ai, audio, general)'
)
async def generate_script(interaction: discord.Interaction, description: str, script_type: str = 'general'):
    """Generate specialized C# scripts for Unity"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.generate_csharp_script(description, script_type)
        await send_long_response(interaction, response, 'csharp')
    except Exception as e:
        logging.error(f"Script generation error: {e}")
        await interaction.followup.send(f"Sorry, I encountered an error generating the script. Please try again.")

@bot.tree.command(name='ping', description='Check bot status and performance')
async def ping(interaction: discord.Interaction):
    """Check bot responsiveness and system status"""
    latency = round(bot.latency * 1000)
    
    if latency < 100:
        status = "Excellent"
    elif latency < 200:
        status = "Good"
    else:
        status = "High Latency"
    
    embed = discord.Embed(
        title="Unity AI Assistant Status",
        color=0x00ff00
    )
    embed.add_field(name="Response Time", value=f"{latency}ms ({status})", inline=True)
    embed.add_field(name="AI Service", value="Online", inline=True)
    embed.add_field(name="Commands", value="All Systems Ready", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='help', description='Show all Unity helper commands')
async def help_unity(interaction: discord.Interaction):
    """Show comprehensive list of Unity helper commands"""
    embed = discord.Embed(
        title="Unity AI Assistant - Command Guide",
        description="Your Unity development companion!",
        color=0x00ff00
    )
    
    embed.add_field(
        name="Code Generation",
        value="• `/script` - Generate C# scripts",
        inline=True
    )
    
    embed.add_field(
        name="Development Help",
        value="• `/ask` - General Unity questions",
        inline=True
    )
    
    embed.add_field(
        name="System",
        value="• `/ping` - Check bot status",
        inline=True
    )
    
    embed.set_footer(text="Type any command to see its specific options!")
    await interaction.response.send_message(embed=embed)

# Enhanced error handling for slash commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Enhanced error handling with user-friendly messages"""
    try:
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Command is on cooldown. Please try again in {error.retry_after:.1f} seconds.", 
                ephemeral=True
            )
        else:
            logging.error(f"Unhandled slash command error: {error}")
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An unexpected error occurred. Please try again later.", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "An unexpected error occurred. Please try again later.", 
                    ephemeral=True
                )
    except discord.NotFound:
        logging.error(f"Interaction expired for error: {error}")
    except Exception as e:
        logging.error(f"Error in error handler: {e}")

async def main():
    """Main function with proper error handling and restart logic"""
    try:
        # Check for required environment variables
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not discord_token:
            logging.error("DISCORD_BOT_TOKEN environment variable is not set!")
            sys.exit(1)
        
        if not gemini_key:
            logging.error("GEMINI_API_KEY environment variable is not set!")
            sys.exit(1)
        
        logging.info(f"Starting Unity AI Assistant Bot (Environment: {ENVIRONMENT})...")
        
        # Start the bot
        await bot.start(discord_token)
        
    except discord.LoginFailure:
        logging.error("Invalid Discord bot token!")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
