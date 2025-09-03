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
        self.is_shutting_down = False

    async def setup_hook(self):
        """Initialize bot and sync commands"""
        try:
            # Sync commands with Discord
            await self.tree.sync()
            logging.info("✅ Commands synced successfully!")
            
            # Start keep-alive server for 24/7 hosting
            if ENVIRONMENT == 'production':
                self.keep_alive = KeepAlive(self)
                port = int(os.getenv('PORT', 8080))
                await self.keep_alive.start_server(port)
                
        except Exception as e:
            logging.error(f"❌ Error during setup: {e}")
            raise
    
    async def close(self):
        """Graceful shutdown"""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logging.info("🔄 Initiating graceful shutdown...")
        
        try:
            if self.keep_alive:
                logging.info("🛑 Shutting down keep-alive server...")
        except Exception as e:
            logging.error(f"Error during shutdown: {e}")
        
        await super().close()
        logging.info("✅ Bot shutdown complete")

bot = UnityBot()

# Global error handling and restart mechanism
async def restart_bot():
    """Restart the bot on critical errors"""
    logging.warning("🔄 Restarting bot due to critical error...")
    await bot.close()
    
    # Wait a bit before restarting
    await asyncio.sleep(5)
    
    # Restart the bot
    try:
        await bot.start(os.getenv('DISCORD_BOT_TOKEN'))
    except Exception as e:
        logging.error(f"❌ Failed to restart bot: {e}")
        sys.exit(1)

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logging.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
    asyncio.create_task(bot.close())

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

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
    
    async def generate_shader(self, description: str, shader_type: str = "surface") -> str:
        """Generate Unity shaders with different types"""
        system_context = """
        You are an expert Unity shader developer. Create optimized, well-documented shaders.
        Include proper fallbacks and mobile optimization considerations.
        """
        
        shader_templates = {
            "surface": "Create a Surface Shader with custom lighting",
            "unlit": "Create an Unlit shader for UI or simple effects",
            "compute": "Create a Compute Shader for GPU calculations",
            "postprocess": "Create a post-processing effect shader"
        }
        
        template_hint = shader_templates.get(shader_type, shader_templates["surface"])
        
        prompt = f"""
        Create a Unity shader: {description}
        
        Requirements:
        - {template_hint}
        - Include proper Properties block with Inspector attributes
        - Add fallback shader for older hardware
        - Include mobile-friendly optimization tags
        - Add detailed comments explaining each section
        - Use appropriate render pipeline (URP/Built-in compatible)
        
        Format as complete ShaderLab code.
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
    
    async def optimize_performance(self, description: str, target_platform: str = "pc") -> str:
        """Provide Unity performance optimization advice"""
        system_context = """
        You are a Unity performance optimization expert. Provide specific, actionable advice
        for improving game performance across different platforms.
        """
        
        platform_contexts = {
            "mobile": "Focus on mobile optimization, battery life, and limited resources",
            "pc": "Target high-end PC performance with advanced graphics features",
            "console": "Optimize for console-specific features and limitations",
            "vr": "Ensure VR-ready performance with 90+ FPS and low latency"
        }
        
        platform_hint = platform_contexts.get(target_platform, platform_contexts["pc"])
        
        prompt = f"""
        Analyze and optimize Unity performance for: {description}
        Target platform: {target_platform} ({platform_hint})
        
        Provide:
        1. Performance bottleneck analysis
        2. Specific optimization techniques
        3. Code examples for improvements
        4. Unity Profiler usage tips
        5. Asset optimization recommendations
        6. Rendering pipeline optimizations
        
        Include before/after comparisons where possible.
        """
        return await self.generate_response(prompt, system_context)
    
    async def suggest_architecture(self, project_description: str, team_size: str = "solo") -> str:
        """Suggest Unity project architecture and patterns"""
        system_context = """
        You are a Unity architecture expert. Recommend scalable, maintainable code structures
        and design patterns appropriate for the project scope.
        """
        
        prompt = f"""
        Design Unity project architecture for: {project_description}
        Team size: {team_size}
        
        Recommend:
        1. Folder structure and organization
        2. Appropriate design patterns (Singleton, Observer, State Machine, etc.)
        3. Scene management strategy
        4. Data management approach (ScriptableObjects, JSON, etc.)
        5. Code organization and modularity
        6. Version control considerations
        7. Testing strategies
        
        Provide specific examples and folder layouts.
        """
        return await self.generate_response(prompt, system_context)
    
    async def animation_physics_help(self, topic: str, question: str) -> str:
        """Specialized help for Unity animation and physics"""
        system_context = """
        You are a Unity animation and physics expert. Provide detailed guidance
        on Unity's animation systems, physics, and related best practices.
        """
        
        prompt = f"""
        Unity {topic} question: {question}
        
        Provide comprehensive guidance including:
        1. Technical explanation
        2. Step-by-step implementation
        3. Code examples and component setup
        4. Common pitfalls and solutions
        5. Performance considerations
        6. Alternative approaches
        
        Focus on practical, working solutions.
        """
        return await self.generate_response(prompt, system_context)
    
    async def ui_ux_guidance(self, description: str, platform: str = "pc") -> str:
        """Provide Unity UI/UX design guidance"""
        system_context = """
        You are a Unity UI/UX expert. Provide guidance on creating intuitive,
        accessible, and platform-appropriate user interfaces.
        """
        
        prompt = f"""
        Unity UI/UX design for: {description}
        Target platform: {platform}
        
        Provide guidance on:
        1. UI layout and component selection
        2. Canvas setup and scaling strategies
        3. Input handling for the target platform
        4. Accessibility considerations
        5. Visual design best practices
        6. Animation and transitions
        7. Performance optimization for UI
        
        Include specific Unity UI components and setup instructions.
        """
        return await self.generate_response(prompt, system_context)
    
    async def code_review(self, code: str, focus_area: str = "general") -> str:
        """Review Unity C# code and suggest improvements"""
        system_context = """
        You are a senior Unity developer conducting a code review.
        Focus on Unity-specific best practices, performance, and maintainability.
        """
        
        prompt = f"""
        Review this Unity C# code (focus: {focus_area}):
        
        ```csharp
        {code}
        ```
        
        Provide:
        1. Overall code quality assessment
        2. Unity-specific improvements
        3. Performance optimizations
        4. Security considerations
        5. Maintainability suggestions
        6. Best practices compliance
        7. Refactored code examples
        
        Be constructive and educational in your feedback.
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
    
    logging.info(f'🎮 {bot.user} connected to Discord!')
    logging.info(f'🚀 Unity AI Assistant ready for game development!')
    logging.info(f'📊 Serving {len(bot.guilds)} servers with {user_count} users')
    logging.info(f'🔧 Commands: {len(bot.tree.get_commands())} slash commands registered')
    logging.info(f'🌍 Environment: {ENVIRONMENT}')
    
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

@bot.event
async def on_guild_join(guild):
    """Log when bot joins a new server"""
    logging.info(f"📥 Joined new guild: {guild.name} (ID: {guild.id}, Members: {guild.member_count})")
    
    # Update activity with new server count
    if ENVIRONMENT == 'production':
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers • Unity development 24/7"
        )
        await bot.change_presence(activity=activity)

@bot.event
async def on_guild_remove(guild):
    """Log when bot leaves a server"""
    logging.info(f"📤 Left guild: {guild.name} (ID: {guild.id})")
    
    # Update activity with new server count
    if ENVIRONMENT == 'production':
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{len(bot.guilds)} servers • Unity development 24/7"
        )
        await bot.change_presence(activity=activity)

@bot.event
async def on_disconnect():
    """Handle disconnect events"""
    logging.warning("⚠️ Bot disconnected from Discord")

@bot.event
async def on_resumed():
    """Handle resume events"""
    logging.info("🔄 Bot connection resumed")

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
        await interaction.followup.send(f"❌ Sorry, I encountered an error generating the script. Please try again.")

@bot.tree.command(name='shader', description='Generate a Unity shader')
@app_commands.describe(
    description='What the shader should do',
    shader_type='Type of shader (surface, unlit, compute, postprocess)'
)
async def generate_shader(interaction: discord.Interaction, description: str, shader_type: str = 'surface'):
    """Generate specialized Unity shaders"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("⏰ Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.generate_shader(description, shader_type)
        await send_long_response(interaction, response, 'hlsl')
    except Exception as e:
        logging.error(f"Shader generation error: {e}")
        await interaction.followup.send(f"❌ Sorry, I encountered an error generating the shader. Please try again.")

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
        await interaction.followup.send(f"❌ Sorry, I encountered an error answering your question. Please try again.")

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
        await interaction.followup.send(f"❌ Sorry, I encountered an error while debugging. Please try again.")

@bot.tree.command(name='optimize', description='Get Unity performance optimization advice')
@app_commands.describe(
    description='Describe your performance issue or what you want to optimize',
    platform='Target platform (mobile, pc, console, vr)'
)
async def optimize_performance(interaction: discord.Interaction, description: str, platform: str = 'pc'):
    """Get performance optimization advice"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("⏰ Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.optimize_performance(description, platform)
        await send_long_response(interaction, response)
    except Exception as e:
        logging.error(f"Optimization error: {e}")
        await interaction.followup.send(f"❌ Sorry, I encountered an error generating optimization advice. Please try again.")

@bot.tree.command(name='architecture', description='Get Unity project architecture advice')
@app_commands.describe(
    project_description='Describe your Unity project',
    team_size='Team size (solo, small, medium, large)'
)
async def suggest_architecture(interaction: discord.Interaction, project_description: str, team_size: str = 'solo'):
    """Get project architecture and design pattern advice"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("⏰ Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.suggest_architecture(project_description, team_size)
        await send_long_response(interaction, response)
    except Exception as e:
        logging.error(f"Architecture advice error: {e}")
        await interaction.followup.send(f"❌ Sorry, I encountered an error generating architecture advice. Please try again.")

@bot.tree.command(name='animation', description='Get help with Unity animation and physics')
@app_commands.describe(
    topic='Animation topic (animator, timeline, physics, rigidbody, etc.)',
    question='Your specific animation or physics question'
)
async def animation_physics(interaction: discord.Interaction, topic: str, question: str):
    """Get specialized animation and physics help"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("⏰ Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.animation_physics_help(topic, question)
        await send_long_response(interaction, response)
    except Exception as e:
        logging.error(f"Animation/Physics help error: {e}")
        await interaction.followup.send(f"❌ Sorry, I encountered an error providing animation/physics help. Please try again.")

@bot.tree.command(name='ui', description='Get Unity UI/UX design guidance')
@app_commands.describe(
    description='Describe your UI/UX challenge or what you want to create',
    platform='Target platform (mobile, pc, console, vr)'
)
async def ui_guidance(interaction: discord.Interaction, description: str, platform: str = 'pc'):
    """Get UI/UX design guidance"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("⏰ Please wait a moment before using this command again.", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.ui_ux_guidance(description, platform)
        await send_long_response(interaction, response)
    except Exception as e:
        logging.error(f"UI guidance error: {e}")
        await interaction.followup.send(f"❌ Sorry, I encountered an error providing UI guidance. Please try again.")

@bot.tree.command(name='review', description='Get your Unity C# code reviewed')
@app_commands.describe(
    code='Your C# code to review',
    focus_area='Focus area (performance, security, maintainability, general)'
)
async def code_review(interaction: discord.Interaction, code: str, focus_area: str = 'general'):
    """Get comprehensive code review"""
    if not await unity_helper._rate_limit_check(interaction.user.id):
        await interaction.response.send_message("⏰ Please wait a moment before using this command again.", ephemeral=True)
        return
    
    if len(code) > 1500:
        await interaction.response.send_message("❌ Code is too long for review. Please submit smaller code snippets (max 1500 characters).", ephemeral=True)
        return
    
    await interaction.response.defer(thinking=True)
    
    try:
        response = await unity_helper.code_review(code, focus_area)
        await send_long_response(interaction, response)
    except Exception as e:
        logging.error(f"Code review error: {e}")
        await interaction.followup.send(f"❌ Sorry, I encountered an error reviewing your code. Please try again.")

@bot.tree.command(name='help', description='Show all Unity helper commands')
async def help_unity(interaction: discord.Interaction):
    """Show comprehensive list of Unity helper commands"""
    embed = discord.Embed(
        title="🎮 Unity AI Assistant - Complete Command Guide",
        description="Your comprehensive Unity development companion!",
        color=0x00ff00
    )
    
    embed.add_field(
        name="📝 Code Generation",
        value="• `/script` - Generate C# scripts\n• `/shader` - Create Unity shaders",
        inline=True
    )
    
    embed.add_field(
        name="🔧 Development Help",
        value="• `/ask` - General Unity questions\n• `/debug` - Debug errors & issues",
        inline=True
    )
    
    embed.add_field(
        name="⚡ Performance",
        value="• `/optimize` - Performance advice\n• `/review` - Code review & analysis",
        inline=True
    )
    
    embed.add_field(
        name="🏗️ Architecture",
        value="• `/architecture` - Project structure\n• `/ui` - UI/UX design guidance",
        inline=True
    )
    
    embed.add_field(
        name="🎬 Specialized",
        value="• `/animation` - Animation & physics\n• `/ping` - Check bot status",
        inline=True
    )
    
    embed.add_field(
        name="📚 Pro Tips",
        value="• Use specific descriptions for better results\n• Try different command options\n• All commands support various platforms",
        inline=False
    )
    
    embed.set_footer(text="Type any command to see its specific options and parameters!")
    await interaction.response.send_message(embed=embed)

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

# Enhanced error handling for slash commands
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Enhanced error handling with user-friendly messages"""
    try:
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏰ Command is on cooldown. Please try again in {error.retry_after:.1f} seconds.", 
                ephemeral=True
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "❌ You don't have the required permissions to use this command.", 
                ephemeral=True
            )
        elif isinstance(error, app_commands.BotMissingPermissions):
            await interaction.response.send_message(
                "❌ I don't have the required permissions to execute this command.", 
                ephemeral=True
            )
        else:
            logging.error(f"Unhandled slash command error: {error}")
            # Try to respond if we haven't already
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ An unexpected error occurred. Please try again later.", 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ An unexpected error occurred. Please try again later.", 
                    ephemeral=True
                )
    except discord.NotFound:
        # Interaction has expired, log the error
        logging.error(f"Interaction expired for error: {error}")
    except Exception as e:
        logging.error(f"Error in error handler: {e}")

async def main():
    """Main function with proper error handling and restart logic"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
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
            
        except discord.HTTPException as e:
            retry_count += 1
            logging.error(f"⚠️ HTTP error occurred (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count >= max_retries:
                logging.error("❌ Max retries exceeded. Shutting down.")
                sys.exit(1)
            
            # Wait before retrying
            wait_time = 5 * retry_count  # Exponential backoff
            logging.info(f"🔄 Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            
        except KeyboardInterrupt:
            logging.info("🛑 Received keyboard interrupt, shutting down gracefully...")
            break
            
        except Exception as e:
            retry_count += 1
            logging.error(f"⚠️ Unexpected error (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count >= max_retries:
                logging.error("❌ Max retries exceeded. Shutting down.")
                sys.exit(1)
            
            # Wait before retrying
            wait_time = 5 * retry_count
            logging.info(f"🔄 Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    
    # Final cleanup
    if not bot.is_closed():
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 Program terminated by user")
    except Exception as e:
        logging.error(f"❌ Fatal error: {e}")
        sys.exit(1)