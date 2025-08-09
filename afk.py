import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import asyncio
import logging
import json
import os

class AFKCog(commands.Cog):
    """AFK system commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('afk')
        self.afk_users = {}  # Store AFK users data
        self.afk_file = "afk_data.json"
        self.load_afk_data()
    
    def load_afk_data(self):
        """Load AFK data from file"""
        try:
            if os.path.exists(self.afk_file):
                with open(self.afk_file, 'r') as f:
                    data = json.load(f)
                    # Convert string timestamps back to datetime objects
                    for user_id, afk_info in data.items():
                        self.afk_users[int(user_id)] = {
                            'reason': afk_info['reason'],
                            'timestamp': datetime.fromisoformat(afk_info['timestamp']),
                            'guild_id': afk_info['guild_id'],
                            'original_nick': afk_info.get('original_nick')
                        }
        except Exception as e:
            self.logger.error(f"Error loading AFK data: {e}")
    
    def save_afk_data(self):
        """Save AFK data to file"""
        try:
            data = {}
            for user_id, afk_info in self.afk_users.items():
                data[str(user_id)] = {
                    'reason': afk_info['reason'],
                    'timestamp': afk_info['timestamp'].isoformat(),
                    'guild_id': afk_info['guild_id'],
                    'original_nick': afk_info.get('original_nick')
                }
            with open(self.afk_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            self.logger.error(f"Error saving AFK data: {e}")
    
    @app_commands.command(name="afk", description="Set yourself as AFK")
    @app_commands.describe(reason="Reason for being AFK (optional)")
    async def afk(self, interaction: discord.Interaction, reason: str = "Away"):
        """Set user as AFK"""
        user_id = interaction.user.id
        guild_id = interaction.guild.id if interaction.guild else None
        
        if user_id in self.afk_users:
            await interaction.response.send_message("❌ You are already AFK!", ephemeral=True)
            return
        
        # Store AFK information
        self.afk_users[user_id] = {
            'reason': reason,
            'timestamp': datetime.now(),
            'guild_id': guild_id,
            'original_nick': interaction.user.display_name
        }
        
        # Try to add [AFK] to nickname
        if interaction.guild and isinstance(interaction.user, discord.Member):
            try:
                current_nick = interaction.user.display_name
                if not current_nick.startswith("[AFK]"):
                    new_nick = f"[AFK] {current_nick}"
                    # Truncate if too long (Discord limit is 32 characters)
                    if len(new_nick) > 32:
                        new_nick = f"[AFK] {current_nick[:26]}"
                    await interaction.user.edit(nick=new_nick)
            except discord.Forbidden:
                pass  # Ignore if bot doesn't have permission
            except Exception as e:
                self.logger.warning(f"Could not change nickname for {interaction.user}: {e}")
        
        # Save data
        self.save_afk_data()
        
        embed = discord.Embed(
            title="💤 AFK Status Set",
            description=f"**{interaction.user.display_name}** is now AFK: {reason}",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        await interaction.response.send_message(embed=embed)
        self.logger.info(f"{interaction.user} set AFK status: {reason}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for AFK users returning"""
        if message.author.bot:
            return
        
        user_id = message.author.id
        
        # Check if user was AFK and is now active
        if user_id in self.afk_users:
            afk_info = self.afk_users[user_id]
            
            # Calculate time away
            time_away = datetime.now() - afk_info['timestamp']
            hours, remainder = divmod(int(time_away.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            # Format time string
            time_parts = []
            if hours > 0:
                time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if minutes > 0:
                time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
            if seconds > 0 and hours == 0:  # Only show seconds if less than an hour
                time_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
            
            time_str = ", ".join(time_parts) if time_parts else "less than a second"
            
            # Remove AFK status
            del self.afk_users[user_id]
            self.save_afk_data()
            
            # Try to remove [AFK] from nickname
            if message.guild and isinstance(message.author, discord.Member):
                try:
                    current_nick = message.author.display_name
                    if current_nick.startswith("[AFK]"):
                        # Restore original nickname or use username
                        original_nick = afk_info.get('original_nick')
                        if original_nick and original_nick.startswith("[AFK]"):
                            # If original nick also had [AFK], just remove it
                            new_nick = original_nick[6:].strip()
                        elif original_nick:
                            new_nick = original_nick
                        else:
                            new_nick = message.author.name
                        
                        await message.author.edit(nick=new_nick if new_nick != message.author.name else None)
                except discord.Forbidden:
                    pass  # Ignore if bot doesn't have permission
                except Exception as e:
                    self.logger.warning(f"Could not restore nickname for {message.author}: {e}")
            
            # Send welcome back message
            embed = discord.Embed(
                title="👋 Welcome Back!",
                description=f"**{message.author.display_name}**, you were away for {time_str}",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            embed.add_field(name="AFK Reason", value=afk_info['reason'], inline=False)
            
            try:
                await message.channel.send(embed=embed, delete_after=10)  # Auto-delete after 10 seconds
            except Exception as e:
                self.logger.warning(f"Could not send welcome back message: {e}")
            
            self.logger.info(f"{message.author} returned from AFK after {time_str}")
        
        # Check if message mentions any AFK users
        if message.mentions:
            for mentioned_user in message.mentions:
                if mentioned_user.id in self.afk_users:
                    afk_info = self.afk_users[mentioned_user.id]
                    time_away = datetime.now() - afk_info['timestamp']
                    hours, remainder = divmod(int(time_away.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    # Format time for mention response
                    if hours > 0:
                        time_str = f"{hours}h {minutes}m ago"
                    elif minutes > 0:
                        time_str = f"{minutes}m ago"
                    else:
                        time_str = "just now"
                    
                    embed = discord.Embed(
                        title="💤 User is AFK",
                        description=f"**{mentioned_user.display_name}** is currently AFK",
                        color=discord.Color.yellow()
                    )
                    embed.add_field(name="Reason", value=afk_info['reason'], inline=True)
                    embed.add_field(name="Since", value=time_str, inline=True)
                    
                    try:
                        await message.reply(embed=embed, delete_after=15, mention_author=False)
                    except Exception as e:
                        self.logger.warning(f"Could not send AFK mention response: {e}")
    
    @app_commands.command(name="afk-list", description="Show all AFK users")
    async def afk_list(self, interaction: discord.Interaction):
        """List all AFK users"""
        if not self.afk_users:
            await interaction.response.send_message("📭 No users are currently AFK.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="💤 AFK Users",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        afk_count = 0
        for user_id, afk_info in self.afk_users.items():
            try:
                user = self.bot.get_user(user_id)
                if user:
                    time_away = datetime.now() - afk_info['timestamp']
                    hours, remainder = divmod(int(time_away.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    if hours > 0:
                        time_str = f"{hours}h {minutes}m ago"
                    elif minutes > 0:
                        time_str = f"{minutes}m ago"
                    else:
                        time_str = "just now"
                    
                    embed.add_field(
                        name=f"{user.display_name}",
                        value=f"**Reason:** {afk_info['reason']}\n**Since:** {time_str}",
                        inline=True
                    )
                    afk_count += 1
                    
                    if afk_count >= 25:  # Discord embed limit
                        break
            except Exception:
                continue
        
        if afk_count == 0:
            embed.description = "No AFK users found in this server."
        else:
            embed.set_footer(text=f"Total AFK users: {len(self.afk_users)}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="afk-clear", description="Clear your AFK status manually")
    async def afk_clear(self, interaction: discord.Interaction):
        """Manually clear AFK status"""
        user_id = interaction.user.id
        
        if user_id not in self.afk_users:
            await interaction.response.send_message("❌ You are not currently AFK.", ephemeral=True)
            return
        
        afk_info = self.afk_users[user_id]
        time_away = datetime.now() - afk_info['timestamp']
        hours, remainder = divmod(int(time_away.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format time string
        time_parts = []
        if hours > 0:
            time_parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            time_parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 and hours == 0:
            time_parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        time_str = ", ".join(time_parts) if time_parts else "less than a second"
        
        # Remove AFK status
        del self.afk_users[user_id]
        self.save_afk_data()
        
        # Try to remove [AFK] from nickname
        if interaction.guild and isinstance(interaction.user, discord.Member):
            try:
                current_nick = interaction.user.display_name
                if current_nick.startswith("[AFK]"):
                    original_nick = afk_info.get('original_nick')
                    if original_nick and original_nick.startswith("[AFK]"):
                        new_nick = original_nick[6:].strip()
                    elif original_nick:
                        new_nick = original_nick
                    else:
                        new_nick = interaction.user.name
                    
                    await interaction.user.edit(nick=new_nick if new_nick != interaction.user.name else None)
            except discord.Forbidden:
                pass
            except Exception as e:
                self.logger.warning(f"Could not restore nickname for {interaction.user}: {e}")
        
        embed = discord.Embed(
            title="✅ AFK Status Cleared",
            description=f"Welcome back! You were away for {time_str}",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        await interaction.response.send_message(embed=embed)
        self.logger.info(f"{interaction.user} manually cleared AFK status after {time_str}")

async def setup(bot):
    await bot.add_cog(AFKCog(bot))