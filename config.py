import os
from typing import List

class BotConfig:
    """Configuration settings for the Discord bot"""
    
    # Bot settings
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
    
    # OpenRouter settings
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'google/gemma-3-12b-it:free')
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1500'))
    
    # Moderation settings
    MAX_MESSAGE_LENGTH = int(os.getenv('MAX_MESSAGE_LENGTH', '2000'))
    SPAM_THRESHOLD = int(os.getenv('SPAM_THRESHOLD', '5'))  # messages per minute
    
    # Auto-moderation keywords (can be expanded via environment)
    FILTERED_WORDS = [
        word.strip() for word in os.getenv('FILTERED_WORDS', '').split(',') 
        if word.strip()
    ]
    
    # Admin role names that can use admin commands
    ADMIN_ROLES = [
        role.strip() for role in os.getenv('ADMIN_ROLES', 'Admin,Moderator,Owner').split(',')
        if role.strip()
    ]
    
    # Channels where AI chat is disabled (optional)
    AI_DISABLED_CHANNELS = [
        channel.strip() for channel in os.getenv('AI_DISABLED_CHANNELS', '').split(',')
        if channel.strip()
    ]
    
    # Rate limiting
    AI_COOLDOWN = int(os.getenv('AI_COOLDOWN', '3'))  # seconds between AI requests per user
    COMMAND_COOLDOWN = int(os.getenv('COMMAND_COOLDOWN', '1'))  # seconds between commands per user
    
    @classmethod
    def get_ai_system_prompt(cls) -> str:
        """Get the system prompt for AI conversations"""
        return os.getenv('AI_SYSTEM_PROMPT', 
            "You are a helpful Discord bot assistant. Respond naturally in plain text without any formatting symbols, brackets, parentheses, slashes, or special characters. "
            "Keep responses concise, friendly, and conversational like a normal person would speak. "
            "Never use markdown formatting, code blocks, or any special symbols in your responses. "
            "Just reply with clean, simple text that flows naturally in conversation. "
            "If asked about inappropriate content, politely decline and suggest something else."
        )
