import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Union
import logging

from config import BotConfig
from utils.permissions import is_admin, has_permission
from utils.filters import MessageFilter

class ModerationCog(commands.Cog):
    """Moderation commands and auto-moderation features"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('moderation')
        self.message_filter = MessageFilter()
        self.user_message_counts = {}  # For spam detection
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-moderation listener"""
        if message.author.bot:
            return
        
        # Skip if user is admin
        if await is_admin(message.author):
            return
        
        # Check for filtered words
        if self.message_filter.contains_filtered_words(message.content):
            await message.delete()
            
            embed = discord.Embed(
                title="🚫 Message Filtered",
                description="Your message contained inappropriate content and was removed.",
                color=discord.Color.red()
            )
            
            try:
                await message.author.send(embed=embed)
            except discord.Forbidden:
                # If can't DM, send in channel briefly
                warning = await message.channel.send(
                    f"{message.author.mention}, your message was removed for inappropriate content.",
                    delete_after=10
                )
            
            self.logger.info(f"Filtered message from {message.author} in {message.guild.name}")
            return
        
        # Spam detection
        await self._check_spam(message)
    
    async def _check_spam(self, message):
        """Check for spam and take action"""
        user_id = message.author.id
        now = datetime.now()
        
        # Initialize or update user message count
        if user_id not in self.user_message_counts:
            self.user_message_counts[user_id] = []
        
        # Add current message timestamp
        self.user_message_counts[user_id].append(now)
        
        # Remove old timestamps (older than 1 minute)
        self.user_message_counts[user_id] = [
            timestamp for timestamp in self.user_message_counts[user_id]
            if now - timestamp < timedelta(minutes=1)
        ]
        
        # Check if user exceeded spam threshold
        if len(self.user_message_counts[user_id]) > BotConfig.SPAM_THRESHOLD:
            try:
                # Timeout user for 5 minutes
                timeout_until = now + timedelta(minutes=5)
                await message.author.timeout(timeout_until, reason="Spam detection")
                
                embed = discord.Embed(
                    title="🚫 Spam Detected",
                    description=f"{message.author.mention} has been timed out for 5 minutes due to spam.",
                    color=discord.Color.red()
                )
                
                await message.channel.send(embed=embed, delete_after=30)
                self.logger.info(f"Timed out {message.author} for spam in {message.guild.name}")
                
                # Reset user's message count
                self.user_message_counts[user_id] = []
                
            except discord.Forbidden:
                self.logger.warning(f"Cannot timeout {message.author} - insufficient permissions")
    
    @app_commands.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(member="The member to kick", reason="Reason for kicking")
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Kick a member"""
        if not await has_permission(interaction.user, 'kick_members'):
            await interaction.response.send_message("❌ You don't have permission to kick members.", ephemeral=True)
            return
        
        if interaction.guild and member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ You cannot kick someone with a higher or equal role.", ephemeral=True)
            return
        
        try:
            await member.kick(reason=f"Kicked by {interaction.user}: {reason}")
            
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"{member.mention} has been kicked from the server.",
                color=discord.Color.orange()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            if interaction.guild:
                self.logger.info(f"{interaction.user} kicked {member} from {interaction.guild.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this member.", ephemeral=True)
    
    @app_commands.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(member="The member to ban", reason="Reason for banning", delete_days="Days of messages to delete (0-7)")
    async def ban_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
        """Ban a member"""
        if not await has_permission(interaction.user, 'ban_members'):
            await interaction.response.send_message("❌ You don't have permission to ban members.", ephemeral=True)
            return
        
        if interaction.guild and member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ You cannot ban someone with a higher or equal role.", ephemeral=True)
            return
        
        if delete_days < 0 or delete_days > 7:
            await interaction.response.send_message("❌ Delete days must be between 0 and 7.", ephemeral=True)
            return
        
        try:
            await member.ban(reason=f"Banned by {interaction.user}: {reason}", delete_message_days=delete_days)
            
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"{member.mention} has been banned from the server.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            embed.add_field(name="Messages Deleted", value=f"{delete_days} days", inline=True)
            
            await interaction.response.send_message(embed=embed)
            if interaction.guild:
                self.logger.info(f"{interaction.user} banned {member} from {interaction.guild.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this member.", ephemeral=True)
    
    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.describe(member="The member to timeout", duration="Duration in minutes", reason="Reason for timeout")
    async def timeout_member(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):
        """Timeout a member"""
        if not await has_permission(interaction.user, 'moderate_members'):
            await interaction.response.send_message("❌ You don't have permission to timeout members.", ephemeral=True)
            return
        
        if interaction.guild and member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ You cannot timeout someone with a higher or equal role.", ephemeral=True)
            return
        
        if duration <= 0 or duration > 40320:  # Max 28 days
            await interaction.response.send_message("❌ Duration must be between 1 and 40320 minutes (28 days).", ephemeral=True)
            return
        
        try:
            timeout_until = datetime.now() + timedelta(minutes=duration)
            await member.timeout(timeout_until, reason=f"Timed out by {interaction.user}: {reason}")
            
            embed = discord.Embed(
                title="⏰ Member Timed Out",
                description=f"{member.mention} has been timed out.",
                color=discord.Color.yellow()
            )
            embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            if interaction.guild:
                self.logger.info(f"{interaction.user} timed out {member} for {duration} minutes in {interaction.guild.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to timeout this member.", ephemeral=True)
    
    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(user_id="User ID to unban")
    async def unban_user(self, interaction: discord.Interaction, user_id: str):
        """Unban a user"""
        if not await has_permission(interaction.user, 'ban_members'):
            await interaction.response.send_message("❌ You don't have permission to unban members.", ephemeral=True)
            return
        
        try:
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)
            await interaction.guild.unban(user, reason=f"Unbanned by {interaction.user}")
            
            embed = discord.Embed(
                title="🔓 Member Unbanned",
                description=f"{user.mention} has been unbanned from the server.",
                color=discord.Color.green()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            if interaction.guild:
                self.logger.info(f"{interaction.user} unbanned {user} from {interaction.guild.name}")
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found or not banned.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unban this user.", ephemeral=True)
    
    @app_commands.command(name="mute", description="Mute a member (timeout)")
    @app_commands.describe(member="The member to mute", duration="Duration in minutes")
    async def mute_member(self, interaction: discord.Interaction, member: discord.Member, duration: int):
        """Mute a member using timeout"""
        # This is essentially the same as timeout, kept for compatibility
        await self.timeout_member(interaction, member, duration, "Muted by moderator")
    
    @app_commands.command(name="unmute", description="Unmute a member")
    @app_commands.describe(member="The member to unmute")
    async def unmute_member(self, interaction: discord.Interaction, member: discord.Member):
        """Unmute a member"""
        if not await has_permission(interaction.user, 'moderate_members'):
            await interaction.response.send_message("❌ You don't have permission to unmute members.", ephemeral=True)
            return
        
        try:
            await member.timeout(None, reason=f"Unmuted by {interaction.user}")
            
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"{member.mention} has been unmuted.",
                color=discord.Color.green()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            if interaction.guild:
                self.logger.info(f"{interaction.user} unmuted {member} in {interaction.guild.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unmute this member.", ephemeral=True)
    
    @app_commands.command(name="warn", description="Warn a user")
    @app_commands.describe(member="The member to warn", reason="Reason for warning")
    async def warn_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Warn a member"""
        if not await has_permission(interaction.user, 'manage_messages'):
            await interaction.response.send_message("❌ You don't have permission to warn members.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⚠️ Member Warned",
            description=f"{member.mention} has been warned.",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        
        # Try to DM the user
        try:
            dm_embed = discord.Embed(
                title="⚠️ Warning",
                description=f"You have been warned in {interaction.guild.name}",
                color=discord.Color.yellow()
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.add_field(name="Moderator", value=interaction.user.display_name, inline=True)
            await member.send(embed=dm_embed)
        except discord.Forbidden:
            embed.add_field(name="Note", value="Could not send DM to user", inline=False)
        
        await interaction.response.send_message(embed=embed)
        if interaction.guild:
            self.logger.info(f"{interaction.user} warned {member} in {interaction.guild.name}: {reason}")
    
    @app_commands.command(name="purge", description="Delete messages in bulk")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def purge_messages(self, interaction: discord.Interaction, amount: int):
        """Purge messages (alias for clear)"""
        await self.clear_messages(interaction, amount)
    
    @app_commands.command(name="lock", description="Lock a channel")
    @app_commands.describe(channel="Channel to lock (current channel if not specified)")
    async def lock_channel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Lock a channel"""
        if not await has_permission(interaction.user, 'manage_channels'):
            await interaction.response.send_message("❌ You don't have permission to manage channels.", ephemeral=True)
            return
        
        if channel is None:
            channel = interaction.channel
        
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Can only lock text channels.", ephemeral=True)
            return
        
        try:
            # Remove send message permission for @everyone
            overwrites = channel.overwrites_for(interaction.guild.default_role)
            overwrites.send_messages = False
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites, reason=f"Channel locked by {interaction.user}")
            
            embed = discord.Embed(
                title="🔒 Channel Locked",
                description=f"{channel.mention} has been locked.",
                color=discord.Color.red()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            if interaction.guild:
                self.logger.info(f"{interaction.user} locked {channel.name} in {interaction.guild.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this channel.", ephemeral=True)
    
    @app_commands.command(name="unlock", description="Unlock a channel")
    @app_commands.describe(channel="Channel to unlock (current channel if not specified)")
    async def unlock_channel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        """Unlock a channel"""
        if not await has_permission(interaction.user, 'manage_channels'):
            await interaction.response.send_message("❌ You don't have permission to manage channels.", ephemeral=True)
            return
        
        if channel is None:
            channel = interaction.channel
        
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Can only unlock text channels.", ephemeral=True)
            return
        
        try:
            # Restore send message permission for @everyone
            overwrites = channel.overwrites_for(interaction.guild.default_role)
            overwrites.send_messages = None  # Reset to default
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites, reason=f"Channel unlocked by {interaction.user}")
            
            embed = discord.Embed(
                title="🔓 Channel Unlocked",
                description=f"{channel.mention} has been unlocked.",
                color=discord.Color.green()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            if interaction.guild:
                self.logger.info(f"{interaction.user} unlocked {channel.name} in {interaction.guild.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this channel.", ephemeral=True)
    
    @app_commands.command(name="slowmode", description="Set slowmode for a channel")
    @app_commands.describe(seconds="Slowmode delay in seconds (0 to disable)")
    async def slowmode(self, interaction: discord.Interaction, seconds: int):
        """Set channel slowmode"""
        if not await has_permission(interaction.user, 'manage_channels'):
            await interaction.response.send_message("❌ You don't have permission to manage channels.", ephemeral=True)
            return
        
        if seconds < 0 or seconds > 21600:  # Max 6 hours
            await interaction.response.send_message("❌ Slowmode must be between 0 and 21600 seconds (6 hours).", ephemeral=True)
            return
        
        try:
            await interaction.channel.edit(slowmode_delay=seconds, reason=f"Slowmode set by {interaction.user}")
            
            if seconds == 0:
                description = f"Slowmode disabled for {interaction.channel.mention}"
            else:
                description = f"Slowmode set to **{seconds} seconds** for {interaction.channel.mention}"
            
            embed = discord.Embed(
                title="⏱️ Slowmode Updated",
                description=description,
                color=discord.Color.blue()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed)
            if interaction.guild:
                self.logger.info(f"{interaction.user} set slowmode to {seconds}s in {interaction.channel.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this channel.", ephemeral=True)
    
    @app_commands.command(name="nick", description="Change user nickname")
    @app_commands.describe(member="Member to change nickname", nickname="New nickname (leave empty to reset)")
    async def change_nick(self, interaction: discord.Interaction, member: discord.Member, nickname: str = None):
        """Change user nickname"""
        if not await has_permission(interaction.user, 'manage_nicknames'):
            await interaction.response.send_message("❌ You don't have permission to manage nicknames.", ephemeral=True)
            return
        
        try:
            old_nick = member.display_name
            await member.edit(nick=nickname, reason=f"Nickname changed by {interaction.user}")
            
            new_nick = nickname if nickname else member.name
            
            embed = discord.Embed(
                title="✏️ Nickname Changed",
                color=discord.Color.blue()
            )
            embed.add_field(name="Member", value=member.mention, inline=True)
            embed.add_field(name="Old Nickname", value=old_nick, inline=True)
            embed.add_field(name="New Nickname", value=new_nick, inline=True)
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            
            await interaction.response.send_message(embed=embed)
            if interaction.guild:
                self.logger.info(f"{interaction.user} changed {member}'s nickname from '{old_nick}' to '{new_nick}'")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to change this user's nickname.", ephemeral=True)
    
    @app_commands.command(name="clearwarns", description="Clear user warnings")
    @app_commands.describe(member="Member to clear warnings for")
    async def clear_warnings(self, interaction: discord.Interaction, member: discord.Member):
        """Clear user warnings"""
        if not await has_permission(interaction.user, 'manage_messages'):
            await interaction.response.send_message("❌ You don't have permission to clear warnings.", ephemeral=True)
            return
        
        # This is a placeholder - in a real bot you'd have a database to track warnings
        embed = discord.Embed(
            title="🧹 Warnings Cleared",
            description=f"All warnings cleared for {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Note", value="Warning system requires database integration", inline=False)
        
        await interaction.response.send_message(embed=embed)
        if interaction.guild:
            self.logger.info(f"{interaction.user} cleared warnings for {member} in {interaction.guild.name}")
    
    @app_commands.command(name="clear", description="Clear messages from the channel")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def clear_messages(self, interaction: discord.Interaction, amount: int):
        """Clear messages from channel"""
        if not await has_permission(interaction.user, 'manage_messages'):
            await interaction.response.send_message("❌ You don't have permission to manage messages.", ephemeral=True)
            return
        
        if amount <= 0 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100.", ephemeral=True)
            return
        
        try:
            if hasattr(interaction.channel, 'purge'):
                deleted = await interaction.channel.purge(limit=amount)
            else:
                await interaction.response.send_message("❌ Cannot clear messages in this channel type.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🧹 Messages Cleared",
                description=f"Successfully deleted {len(deleted)} messages.",
                color=discord.Color.green()
            )
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            
            await interaction.response.send_message(embed=embed, delete_after=10)
            if interaction.guild:
                self.logger.info(f"{interaction.user} cleared {len(deleted)} messages in {interaction.guild.name}")
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to delete messages.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
