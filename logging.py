import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging():
    """Setup logging configuration for the bot"""
    
    # Create logs directory if it doesn't exist
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(logs_dir, 'bot.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(logs_dir, 'errors.log'),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Reduce discord.py logging level
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.WARNING)
    
    # Reduce httpx logging level (used by OpenAI)
    httpx_logger = logging.getLogger('httpx')
    httpx_logger.setLevel(logging.WARNING)
    
    logging.info("Logging system initialized")

def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module"""
    return logging.getLogger(name)

class BotLogFilter(logging.Filter):
    """Custom log filter for bot-specific logging"""
    
    def filter(self, record):
        # Filter out certain noisy log messages
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            
            # Filter out common Discord.py info messages
            if 'Shard ID' in msg or 'heartbeat' in msg.lower():
                return False
            
            # Filter out HTTP request logs unless they're errors
            if 'HTTP' in msg and record.levelno < logging.WARNING:
                return False
        
        return True

def log_command_usage(user, command, guild=None):
    """Log command usage for analytics"""
    logger = logging.getLogger('commands')
    guild_info = f" in {guild.name} ({guild.id})" if guild else ""
    logger.info(f"Command '{command}' used by {user} ({user.id}){guild_info}")

def log_moderation_action(moderator, action, target, reason=None, guild=None):
    """Log moderation actions"""
    logger = logging.getLogger('moderation')
    guild_info = f" in {guild.name} ({guild.id})" if guild else ""
    reason_info = f" - Reason: {reason}" if reason else ""
    logger.info(f"Moderation: {moderator} ({moderator.id}) {action} {target} ({target.id}){guild_info}{reason_info}")

def log_auto_moderation(action, user, reason, guild=None):
    """Log auto-moderation actions"""
    logger = logging.getLogger('auto_moderation')
    guild_info = f" in {guild.name} ({guild.id})" if guild else ""
    logger.info(f"Auto-moderation: {action} for {user} ({user.id}) - {reason}{guild_info}")

def log_error(error, context=None):
    """Log errors with context"""
    logger = logging.getLogger('errors')
    context_info = f" - Context: {context}" if context else ""
    logger.error(f"Error occurred: {str(error)}{context_info}", exc_info=True)
