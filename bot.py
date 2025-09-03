import discord
from discord import app_commands
import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio
import logging
import time
import sys
from typing import Dict
from flask import Flask
from threading import Thread

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Environment
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Flask app for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "Unity AI Discord Bot is online! 🎮"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "Unity AI Assistant", "service": "running"}

@app.route('/status')
def status():
    return {"status": "running", "bot": "Unity AI Assistant", "environment": ENVIRONMENT}

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

def keep_alive():
    server = Thread(target=run_flask)
    server.daemon = True
    server.start()

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True

class UnityBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        """Initialize bot and sync commands"""
        try:
            await self.tree.sync()
            logging.info("✅ Commands synced successfully!")
        except Exception as e:
            logging.error(f"❌ Error syncing commands: {e}")
    
    async def on_ready(self):
        """Bot ready event"""
        user_count = sum(len(guild.members) for guild in self.guilds)
        
        logging.info(f'🎮 {self.user} connected to Discord!')
        logging.info(f'🚀 Unity AI Assistant ready for game development!')
        logging.info(f'📊 Serving {len(self.guilds)} servers with {user_count} users')
        
        # Set bot activity
        activity = discord.Activity(
            type=discord.ActivityType.playing,
            name="Unity development"
        )
        await self.change_presence(activity=activity, status=discord.Status.online)

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
    
    async def debug_unity_error(self, error_message: str, context: str = "") -> str:
        """Help debug Unity errors and issues"""
        # Check for common errors first
        for error_type, solution in self.common_errors.items():
            if error_type.lower() in error_message.lower():
                quick_solution = f"**Quick Solution:** {solution}\n\n"
                break
        else:
            quick_solution = ""
        
        system_context = """
        You are a Unity debugging expert. Analyze errors and provide step-by-step solutions.
        Focus on practical fixes and prevention strategies.
        """
        
        prompt = f"""
        Debug this Unity error: {error_message}
        {f'Context: {context}' if context else ''}
        
        Provide:
        1. What this error means in simple terms
        2. Most likely causes
        3. Step-by-step solution
        4. How to prevent this error in the future
        5. Related Unity documentation links if relevant
        
        Make it beginner-friendly but thorough.
        """
        
        ai_response = await self.generate_response(prompt, system_context)
        return f"{quick_solution}{ai_response}"
    
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

# Utility function for handling long responses
async def send_long_response(interaction: discord.Interaction, response: str, code_type: str = None, is_followup: bool = True):
    """Handle long responses by splitting them appropriately"""
    max_length = 1900
    
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
        await interaction.response.send_message("⏰ Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.answer_unity_question(question)
        await send_long_response(interaction, response)
    except Exception as e:
        logging.error(f"Question answering error: {e}")
        await interaction.followup.send("❌ Sorry, I encountered an error answering your question. Please try again.")

@bot.tree.command(name='script', description='Generate a C# script for Unity')
@app_commands.describe(
    description='What the script should do',
    script_type='Type of script (movement, ui, ai, audio, general)'
)
async def generate_script(interaction: discord.Interaction, description: str, script_type: str = 'general'):
    """Generate specialized C# scripts for Unity"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("⏰ Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.generate_csharp_script(description, script_type)
        await send_long_response(interaction, response, 'csharp')
    except Exception as e:
        logging.error(f"Script generation error: {e}")
        await interaction.followup.send("❌ Sorry, I encountered an error generating the script. Please try again.")

@bot.tree.command(name='debug', description='Debug Unity errors and issues')
@app_commands.describe(
    error_message='The error message you encountered',
    context='Optional: Additional context about when the error occurred'
)
async def debug_error(interaction: discord.Interaction, error_message: str, context: str = ''):
    """Help debug Unity errors and issues"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("⏰ Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.debug_unity_error(error_message, context)
        await send_long_response(interaction, response)
    except Exception as e:
        logging.error(f"Debug error: {e}")
        await interaction.followup.send("❌ Sorry, I encountered an error while debugging. Please try again.")

@bot.tree.command(name='ping', description='Check bot status and performance')
async def ping(interaction: discord.Interaction):
    """Check bot responsiveness and system status"""
    latency = round(bot.latency * 1000)
    
    if latency < 100:
        status = "🟢 Excellent"
    elif latency < 200:
        status = "🟡 Good"
    else:
        status = "🔴 High Latency"
    
    embed = discord.Embed(
        title="🏓 Unity AI Assistant Status",
        color=0x00ff00
    )
    embed.add_field(name="Response Time", value=f"{latency}ms ({status})", inline=True)
    embed.add_field(name="AI Service", value="🟢 Online", inline=True)
    embed.add_field(name="Commands", value="🟢 All Systems Ready", inline=True)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='help', description='Show all Unity helper commands')
async def help_unity(interaction: discord.Interaction):
    """Show comprehensive list of Unity helper commands"""
    embed = discord.Embed(
        title="🎮 Unity AI Assistant - Command Guide",
        description="Your comprehensive Unity development companion!",
        color=0x00ff00
    )
    
    embed.add_field(
        name="📝 Code Generation",
        value="• `/script` - Generate C# scripts",
        inline=True
    )
    
    embed.add_field(
        name="🔧 Development Help",
        value="• `/ask` - General Unity questions\n• `/debug` - Debug errors & issues",
        inline=True
    )
    
    embed.add_field(
        name="⚡ System",
        value="• `/ping` - Check bot status\n• `/help` - Show this help",
        inline=True
    )
    
    embed.set_footer(text="Type any command to see its specific options and parameters!")
    await interaction.response.send_message(embed=embed)

async def main():
    """Main function to run the bot"""
    try:
        # Check for required environment variables
        discord_token = os.getenv('DISCORD_BOT_TOKEN')
        gemini_key = os.getenv('GEMINI_API_KEY')
        
        if not discord_token:
            logging.error("❌ DISCORD_BOT_TOKEN environment variable is not set!")
            sys.exit(1)
        
        if not gemini_key:
            logging.error("❌ GEMINI_API_KEY environment variable is not set!")
            sys.exit(1)
        
        logging.info(f"🚀 Starting Unity AI Assistant Bot (Environment: {ENVIRONMENT})...")
        
        # Start the bot
        await bot.start(discord_token)
        
    except discord.LoginFailure:
        logging.error("❌ Invalid Discord bot token!")
        sys.exit(1)
    except Exception as e:
        logging.error(f"❌ Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Start Flask server
    keep_alive()
    logging.info("🌐 Flask server started")
    
    # Run the Discord bot
    asyncio.run(main())
