import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import psutil
import os
import sys
import logging

from config import BotConfig
from utils.permissions import is_admin, has_permission

class AdminCog(commands.Cog):
    """Admin commands and server management features"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('admin')
    
    @app_commands.command(name="botinfo", description="Display bot information and statistics")
    async def botinfo(self, interaction: discord.Interaction):
        """Display bot information"""
        uptime = datetime.now() - self.bot.start_time
        
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(name="Users", value=str(len(self.bot.users)), inline=True)
        embed.add_field(name="Commands", value=str(len(self.bot.commands)), inline=True)
        
        embed.add_field(name="Uptime", value=str(uptime).split('.')[0], inline=True)
        embed.add_field(name="Python Version", value=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}", inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        
        # System stats
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            embed.add_field(name="CPU Usage", value=f"{cpu_percent}%", inline=True)
            embed.add_field(name="Memory Usage", value=f"{memory.percent}%", inline=True)
        except:
            pass
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="serverinfo", description="Display server information")
    async def server_info(self, interaction: discord.Interaction):
        """Display server information"""
        guild = interaction.guild
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Server Info",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Emojis", value=str(len(guild.emojis)), inline=True)
        
        embed.add_field(name="Verification Level", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="Boost Level", value=str(guild.premium_tier), inline=True)
        embed.add_field(name="Boosts", value=str(guild.premium_subscription_count), inline=True)
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.set_footer(text=f"Server ID: {guild.id}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Display information about a user")
    @app_commands.describe(member="The member to get info about")
    async def user_info(self, interaction: discord.Interaction, member: discord.Member = None):
        """Display user information"""
        if member is None:
            if isinstance(interaction.user, discord.Member):
                member = interaction.user
            else:
                await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
                return
        
        embed = discord.Embed(
            title=f"👤 {member.display_name} Info",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
        
        embed.add_field(name="Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="Status", value=str(member.status).title(), inline=True)
        
        # Roles (excluding @everyone)
        roles = [role.mention for role in member.roles[1:]]
        if roles:
            embed.add_field(name="Roles", value=", ".join(roles) if len(", ".join(roles)) < 1024 else f"{len(roles)} roles", inline=False)
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="reload-config", description="Reload bot configuration")
    async def reload_config(self, interaction: discord.Interaction):
        """Reload bot configuration (admin only)"""
        if not await is_admin(interaction.user):
            await interaction.response.send_message("❌ Only administrators can reload the configuration.", ephemeral=True)
            return
        
        try:
            # Reload environment variables
            from dotenv import load_dotenv
            load_dotenv()
            
            embed = discord.Embed(
                title="🔄 Configuration Reloaded",
                description="Bot configuration has been reloaded successfully.",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed)
            self.logger.info(f"Configuration reloaded by {interaction.user}")
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Reload Failed",
                description=f"Failed to reload configuration: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="set-status", description="Set bot status")
    @app_commands.describe(activity="Activity type", message="Status message")
    @app_commands.choices(activity=[
        app_commands.Choice(name="Playing", value="playing"),
        app_commands.Choice(name="Watching", value="watching"),
        app_commands.Choice(name="Listening", value="listening"),
        app_commands.Choice(name="Streaming", value="streaming")
    ])
    async def set_status(self, interaction: discord.Interaction, activity: str, message: str):
        """Set bot status (admin only)"""
        if not await is_admin(interaction.user):
            await interaction.response.send_message("❌ Only administrators can change bot status.", ephemeral=True)
            return
        
        activity_types = {
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "listening": discord.ActivityType.listening,
            "streaming": discord.ActivityType.streaming
        }
        
        try:
            activity_obj = discord.Activity(
                type=activity_types[activity],
                name=message
            )
            
            await self.bot.change_presence(activity=activity_obj)
            
            embed = discord.Embed(
                title="✅ Status Updated",
                description=f"Bot status set to: **{activity.title()}** {message}",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed)
            self.logger.info(f"Status changed by {interaction.user} to: {activity} {message}")
            
        except Exception as e:
            embed = discord.Embed(
                title="❌ Status Update Failed",
                description=f"Failed to update status: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="help", description="Display help information")
    async def help_command(self, interaction: discord.Interaction):
        """Display help information"""
        embed = discord.Embed(
            title="🔧 Bot Commands",
            description="Here are all available commands:",
            color=discord.Color.blue()
        )
        
        # AI Commands
        embed.add_field(
            name="🤖 AI Commands",
            value=(
                "`/chat <message>` - Chat with AI assistant\n"
                "`/ai <prompt>` - Chat with AI\n"
                "`/ask <question>` - Ask ChatGPT anything\n"
                "`/agent <persona> <prompt>` - Talk to custom AI agent\n"
                "`/roleplay <character> <prompt>` - RP with AI character\n"
                "`/summarize <text>` - Summarize any text\n"
                "`/translate <text>` - Translate into English\n"
                "`/codegen <task>` - Generate code\n"
                "`/define <word>` - Dictionary definition\n"
                "`/ai-status` - Check AI service status"
            ),
            inline=False
        )
        
        # Moderation Commands
        embed.add_field(
            name="🛡️ Moderation Commands",
            value=(
                "`/kick <member> [reason]` - Kick a member\n"
                "`/ban <member> [reason] [delete_days]` - Ban a member\n"
                "`/unban <user_id>` - Unban a user\n"
                "`/mute <member> <duration>` - Mute a member\n"
                "`/unmute <member>` - Unmute a member\n"
                "`/warn <member> [reason]` - Warn a user\n"
                "`/timeout <member> <duration> [reason]` - Timeout a member\n"
                "`/purge <amount>` - Delete messages in bulk\n"
                "`/clear <amount>` - Clear messages\n"
                "`/lock [channel]` - Lock a channel\n"
                "`/unlock [channel]` - Unlock a channel\n"
                "`/slowmode <seconds>` - Set slowmode\n"
                "`/nick <member> [nickname]` - Change nickname\n"
                "`/clearwarns <member>` - Clear warnings"
            ),
            inline=False
        )
        
        # Server Management
        embed.add_field(
            name="🛠️ Server Management",
            value=(
                "`/serverinfo` - Show server info\n"
                "`/userinfo [member]` - Show user info\n"
                "`/avatar [user]` - Show profile picture\n"
                "`/roles` - List all roles\n"
                "`/role <add/remove> <user> <role>` - Manage roles\n"
                "`/channelinfo` - Show current channel info\n"
                "`/announce <channel> <message>` - Make announcement\n"
                "`/embed <title> <description>` - Send fancy embed"
            ),
            inline=False
        )
        
        # Fun & Games
        embed.add_field(
            name="🎮 Fun & Games",
            value=(
                "`/coinflip` - Flip a coin\n"
                "`/roll [sides]` - Roll a die\n"
                "`/8ball <question>` - Ask the magic 8-ball\n"
                "`/rps <choice>` - Rock Paper Scissors\n"
                "`/quiz` - Start a trivia quiz\n"
                "`/guess [max_number]` - Number guessing game\n"
                "`/fact` - Get a random fact\n"
                "`/joke` - Get a random joke"
            ),
            inline=False
        )
        
        # Polls & Votes
        embed.add_field(
            name="📊 Polls & Votes",
            value=(
                "`/poll <question> <option1> <option2> [...]` - Create poll\n"
                "`/vote <topic>` - Start a vote\n"
                "`/opinion <topic>` - Ask for user opinions"
            ),
            inline=False
        )
        
        # Utilities
        embed.add_field(
            name="📎 Utilities",
            value=(
                "`/ping` - Show latency\n"
                "`/invite` - Bot invite link\n"
                "`/support` - Support information\n"
                "`/remindme <time> <task>` - Set a reminder\n"
                "`/timer <seconds>` - Start a timer\n"
                "`/time` - Show current time\n"
                "`/calc <expression>` - Calculator\n"
                "`/shorten <url>` - Shorten a URL\n"
                "`/qr <text/url>` - Generate QR code\n"
                "`/emojify <text>` - Turn text into emojis"
            ),
            inline=False
        )
        
        # AFK System
        embed.add_field(
            name="💤 AFK System",
            value=(
                "`/afk [reason]` - Set yourself as AFK\n"
                "`/afk-list` - Show all AFK users\n"
                "`/afk-clear` - Clear your AFK status manually"
            ),
            inline=False
        )
        
        # Admin Commands
        embed.add_field(
            name="⚙️ Admin Commands",
            value=(
                "`/botinfo` - Bot information and stats\n"
                "`/reload-config` - Reload configuration (admin)\n"
                "`/set-status <type> <message>` - Set bot status (admin)\n"
                "`/help` - Show this help menu"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Notes",
            value=(
                "• Commands with `[optional]` parameters are optional\n"
                "• Commands with `<required>` parameters are required\n"
                "• Some commands require specific permissions\n"
                "• Auto-moderation is active for filtered words and spam"
            ),
            inline=False
        )
        
        embed.set_footer(text="Use /command_name for slash commands or !command_name for prefix commands")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
