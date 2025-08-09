import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import sys

from config import BotConfig
from utils.logging import setup_logging
from cogs.ai_chat import AIChatCog
from cogs.moderation import ModerationCog
from cogs.admin import AdminCog
from cogs.fun_games import FunGamesCog
from cogs.utilities import UtilitiesCog
from cogs.polls import PollsCog
from cogs.server_management import ServerManagementCog
from cogs.afk import AFKCog


# Load environment variables
load_dotenv()

class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=BotConfig.COMMAND_PREFIX,
            intents=intents,
            help_command=None
        )
        
        self.start_time = datetime.now()
        self.logger = logging.getLogger('bot')
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Load cogs
        await self.add_cog(AIChatCog(self))
        await self.add_cog(ModerationCog(self))
        await self.add_cog(AdminCog(self))
        await self.add_cog(FunGamesCog(self))
        await self.add_cog(UtilitiesCog(self))
        await self.add_cog(PollsCog(self))
        await self.add_cog(ServerManagementCog(self))
        await self.add_cog(AFKCog(self))
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="for commands | /help"
        )
        await self.change_presence(activity=activity)
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        self.logger.info(f'Joined guild: {guild.name} (ID: {guild.id})')
    
    async def on_guild_remove(self, guild):
        """Called when bot leaves a guild"""
        self.logger.info(f'Left guild: {guild.name} (ID: {guild.id})')
    
    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            return
        
        if isinstance(error, commands.BotMissingPermissions):
            await ctx.send("❌ I don't have the required permissions to execute this command.")
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
            return
        
        if isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided.")
            return
        
        # Log unexpected errors
        self.logger.error(f"Unexpected error in command {ctx.command}: {error}")
        await ctx.send("❌ An unexpected error occurred. Please try again later.")

async def main():
    """Main function to run the bot"""
    # Setup logging
    setup_logging()
    

    
    # Check for required environment variables
    discord_token = os.getenv('DISCORD_TOKEN')
    openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not discord_token:
        logging.error("DISCORD_TOKEN not found in environment variables")
        sys.exit(1)
    
    if not openrouter_api_key:
        logging.error("OPENROUTER_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Create and run bot
    bot = DiscordBot()
    
    try:
        await bot.start(discord_token)
    except KeyboardInterrupt:
        logging.info("Bot shutdown requested")
    except Exception as e:
        logging.error(f"Bot crashed: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
