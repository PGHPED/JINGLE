# Unity AI Assistant Discord Bot

## Overview

This project is a comprehensive Discord bot designed to assist Unity game developers with advanced AI-powered development support. The bot leverages Google's Gemini 1.5 Flash AI to provide specialized Unity development assistance including code generation, debugging, performance optimization, architecture guidance, and much more through modern Discord slash commands.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Bot Framework
- **Discord.py**: Uses the discord.py library for Discord API integration
- **Slash Command System**: Implements Discord's modern slash command system with '/' prefix for bot interactions
- **Async Architecture**: Built on Python's asyncio for handling concurrent Discord events and AI API calls

### AI Integration
- **Google Gemini API**: Primary AI service for generating responses and code
- **Gemini 1.5 Flash Model**: Utilizes the latest gemini-1.5-flash model for enhanced performance and capabilities
- **Async AI Calls**: Wraps synchronous Gemini API calls in async threads to prevent blocking
- **Advanced Prompting**: Context-aware prompts tailored for specific Unity development scenarios

### Enhanced Helper Class Design
- **UnityHelper Class**: Comprehensive AI functionality with specialized methods for all aspects of Unity development
- **Rate Limiting**: Built-in rate limiting to prevent API abuse and ensure fair usage
- **Error Database**: Common Unity errors database with instant solutions
- **Context-Aware Responses**: AI responses tailored to specific development contexts and platforms
- **Multi-Platform Support**: Optimizations and advice for PC, mobile, console, and VR platforms

### Command System Features
- **11 Specialized Commands**: Comprehensive coverage of Unity development needs
- **Parameter Validation**: Smart parameter validation and user guidance
- **Long Response Handling**: Intelligent message splitting for long code and detailed explanations
- **Enhanced Error Handling**: User-friendly error messages with logging for debugging

### Configuration Management
- **Environment Variables**: Uses python-dotenv for secure API key management
- **Intent Configuration**: Configures Discord intents to enable message content reading
- **Enhanced Logging**: Comprehensive logging system with error tracking and performance monitoring
- **Activity Status**: Dynamic bot presence showing current activity and availability
- **Command Syncing**: Automatic Discord slash command synchronization on startup

## Available Commands

### 📝 Code Generation
- **`/script`** - Generate specialized C# scripts for Unity
  - Parameters: description, script_type (movement, ui, ai, audio, general)
  - Features: Context-aware code generation with best practices and documentation

- **`/shader`** - Create Unity shaders for various effects
  - Parameters: description, shader_type (surface, unlit, compute, postprocess)
  - Features: Complete ShaderLab code with mobile optimization and fallbacks

### 🔧 Development Assistance
- **`/ask`** - Ask comprehensive Unity development questions
  - Features: Detailed answers with code examples and Unity documentation references

- **`/debug`** - Debug Unity errors and issues
  - Parameters: error_message, context (optional)
  - Features: Instant solutions for common errors plus detailed debugging guidance

### ⚡ Performance & Architecture
- **`/optimize`** - Get performance optimization advice
  - Parameters: description, platform (mobile, pc, console, vr)
  - Features: Platform-specific optimization strategies and profiling guidance

- **`/architecture`** - Get project architecture recommendations
  - Parameters: project_description, team_size (solo, small, medium, large)
  - Features: Design patterns, folder structure, and scalability advice

- **`/review`** - Get comprehensive C# code review
  - Parameters: code, focus_area (performance, security, maintainability, general)
  - Features: Detailed analysis with refactoring suggestions and best practices

### 🎬 Specialized Areas
- **`/animation`** - Animation and physics assistance
  - Parameters: topic, question
  - Features: Specialized help for Unity's animation systems and physics

- **`/ui`** - UI/UX design guidance
  - Parameters: description, platform
  - Features: Unity UI best practices and platform-specific considerations

### 🛠️ Utility
- **`/help`** - Display all available commands with examples
- **`/ping`** - Check bot status and performance metrics

## External Dependencies

### Core Services
- **Discord API**: Real-time messaging and bot interaction platform
- **Google Gemini API**: Advanced AI text generation and code assistance service

### Python Libraries
- **discord.py**: Discord bot framework and API wrapper (v2.6.3+)
- **google-generativeai**: Official Google Gemini API client (v0.8.5+)
- **python-dotenv**: Environment variable management for secure configuration
- **asyncio**: Built-in Python library for asynchronous programming
- **typing**: Type hints for better code documentation and IDE support
- **re**: Regular expressions for text processing
- **json**: JSON data handling
- **time**: Time-based operations for rate limiting

### Development Tools
- **logging**: Enhanced Python logging for application monitoring and debugging

### Environment Requirements
- **GEMINI_API_KEY**: Required environment variable for Google Gemini API access
- **DISCORD_BOT_TOKEN**: Required Discord bot authentication token

## Recent Updates (September 2025)

### Major Enhancements
- **Upgraded AI Model**: Migrated from deprecated gemini-pro to gemini-1.5-flash for improved performance
- **11 Specialized Commands**: Expanded from 5 basic commands to comprehensive Unity development toolkit
- **Advanced Error Handling**: Built-in solutions for common Unity errors with context-aware debugging
- **Multi-Platform Support**: Tailored advice for PC, mobile, console, and VR development
- **Rate Limiting**: Implemented user-based rate limiting to prevent API abuse
- **Enhanced UI/UX**: Improved Discord embeds, status indicators, and user feedback
- **Code Review System**: Professional-grade code analysis with refactoring suggestions
- **Performance Optimization**: Platform-specific optimization strategies and profiling guidance
- **Architecture Advisory**: Project structure recommendations based on team size and scope