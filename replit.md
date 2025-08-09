# Discord Bot with AI and Moderation

## Overview

This is a comprehensive Discord bot built with Python that combines AI-powered conversation capabilities with extensive moderation tools, fun games, utilities, and server management features. The bot uses OpenRouter API with Google Gemma model for natural language interactions and includes over 50 slash commands organized across multiple categories. The architecture follows a modular cog-based design using the discord.py library, making it highly extensible and maintainable.

## Recent Changes

- **Added 50+ Commands**: Comprehensive command set across 6 major categories
- **Flask Keep-Alive**: Integrated web server for 24/7 hosting reliability  
- **Extended AI Features**: Multiple AI interaction modes (agent personas, roleplay, code generation)
- **Complete Moderation Suite**: Full moderation toolkit with advanced channel management
- **Fun & Games**: Interactive games, trivia, random facts and jokes
- **Utility Commands**: Reminders, timers, calculators, QR codes, and more
- **Server Management**: Role management, announcements, embeds, and info commands

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework
- **Discord.py**: Primary framework for Discord bot functionality using the commands extension
- **Cog-based Architecture**: Modular design with separate cogs for AI chat, moderation, and admin functions
- **Async/Await Pattern**: Full asynchronous operation for optimal performance
- **Environment-based Configuration**: Centralized config system using environment variables

### AI Integration
- **OpenRouter API**: Integration with Google Gemma model for conversational AI
- **Multiple AI Modes**: Chat, agent personas, roleplay, code generation, translation, summarization
- **Context Management**: System prompts and conversation context handling  
- **Rate Limiting**: User-based cooldown system to prevent API abuse
- **Content Filtering**: Pre and post-processing to ensure clean, natural responses
- **Response Cleaning**: Automatic removal of formatting symbols for Discord-friendly output

### Moderation System
- **Complete Moderation Suite**: Kick, ban, unban, mute, unmute, warn, timeout commands
- **Channel Management**: Lock, unlock, slowmode, purge commands
- **Permission Management**: Role-based access control for administrative commands
- **Auto-moderation**: Real-time message filtering using keyword detection
- **Spam Detection**: Message frequency monitoring with configurable thresholds
- **Member Management**: Nickname changes, warning system, bulk message deletion

### Logging and Monitoring
- **Rotating File Logs**: Separate log files for general activity and errors
- **Multi-level Logging**: Console and file output with configurable verbosity
- **Performance Monitoring**: System resource tracking and bot statistics
- **Error Handling**: Comprehensive exception handling with detailed logging

### Security Features
- **Role-based Permissions**: Admin role verification for sensitive commands
- **Content Filtering**: Configurable word filtering with pattern matching
- **Rate Limiting**: Per-user cooldowns for both AI requests and commands
- **Input Validation**: Message sanitization and length limits

## External Dependencies

### APIs and Services
- **OpenRouter API**: Google Gemma model (google/gemma-3-12b-it:free) for AI conversation capabilities
- **Discord API**: Full Discord bot functionality via discord.py library
- **Flask Web Server**: Keep-alive functionality for 24/7 hosting on port 8080

### Python Libraries
- **discord.py**: Discord bot framework with intents and slash command support
- **aiohttp**: HTTP client for OpenRouter API integration
- **python-dotenv**: Environment variable management
- **psutil**: System monitoring and performance statistics
- **flask**: Web server for keep-alive functionality
- **asyncio**: Asynchronous programming support

### Configuration Requirements
- **Discord Bot Token**: Required for Discord API authentication (DISCORD_TOKEN)
- **OpenRouter API Key**: Required for AI conversation features (OPENROUTER_API_KEY)
- **Environment Variables**: Configurable settings for moderation thresholds, admin roles, and behavior customization

### Optional Integrations
- **Custom Word Lists**: Configurable content filtering via environment variables
- **Channel Restrictions**: AI functionality can be disabled in specific channels
- **Role Customization**: Admin permissions configurable via role names

## Command Categories

### 🔧 Moderation Commands (13 commands)
Complete moderation suite including kick, ban, unban, mute, unmute, warn, timeout, purge, lock, unlock, slowmode, nick, clearwarns

### 🧠 AI & Conversation Commands (10 commands)  
AI chat, agent personas, roleplay, code generation, translation, summarization, definitions, and status checking

### 🎮 Fun & Games Commands (8 commands)
Interactive games including coinflip, dice, 8ball, rock-paper-scissors, trivia, number guessing, facts, and jokes

### 📊 Polls & Votes Commands (3 commands)
Poll creation, voting systems, and opinion gathering

### 🛠️ Server Management Commands (8 commands)
Server info, user info, avatars, role management, channel info, announcements, embeds, and support

### 📎 Utilities Commands (10+ commands)
Ping, invites, reminders, timers, time, calculator, URL shortening, QR codes, text tools, and emojification

### ⚙️ Admin Commands (4 commands)
Bot information, configuration reload, status management, and comprehensive help system