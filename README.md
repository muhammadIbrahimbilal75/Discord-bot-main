# AI-Powered Discord Bot

A feature-rich Discord bot with AI conversation capabilities and comprehensive moderation tools.

## Features

### 🤖 AI Capabilities
- **OpenAI Integration**: Powered by GPT-4o for natural conversations
- **Smart Responses**: Context-aware AI responses in Discord
- **Configurable**: Customizable AI behavior and prompts
- **Rate Limiting**: Built-in cooldowns to prevent spam

### 🛡️ Moderation Features
- **Auto-Moderation**: Automatic filtering of inappropriate content
- **Spam Detection**: Intelligent spam detection and prevention
- **Member Management**: Kick, ban, timeout, and message clearing
- **Role-Based Permissions**: Secure command access control

### ⚙️ Admin Tools
- **Server Management**: Comprehensive server and user information
- **Bot Statistics**: Real-time bot performance monitoring
- **Configuration Management**: Runtime configuration updates
- **Comprehensive Logging**: Detailed activity and error logging

## Commands

### AI Commands
- `/chat <message>` - Chat with the AI assistant
- `!ask <message>` - Alternative chat command (prefix-based)
- `/ai-status` - Check AI service status

### Moderation Commands
- `/kick <member> [reason]` - Kick a member from the server
- `/ban <member> [reason] [delete_days]` - Ban a member
- `/timeout <member> <duration> [reason]` - Timeout a member
- `/clear <amount>` - Clear messages from channel

### Admin Commands
- `/botinfo` - Display bot information and statistics
- `/serverinfo` - Display server information
- `/userinfo [member]` - Display user information
- `/reload-config` - Reload bot configuration (admin only)
- `/set-status <type> <message>` - Set bot status (admin only)
- `/help` - Display help information

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Discord Bot Token
- OpenAI API Key

### Required Python Packages
```bash
pip install discord.py openai python-dotenv psutil asyncio
