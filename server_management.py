import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import logging
from utils.permissions import has_permission, is_admin

class ServerManagementCog(commands.Cog):
    """Server management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('server_management')
    
    @app_commands.command(name="channelinfo", description="Show current channel information")
    async def channel_info(self, interaction: discord.Interaction):
        """Show channel information"""
        channel = interaction.channel
        
        embed = discord.Embed(
            title=f"📋 Channel Information",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if hasattr(channel, 'name'):
            embed.add_field(name="Name", value=f"#{channel.name}", inline=True)
        embed.add_field(name="Type", value=str(channel.type).title(), inline=True)
        embed.add_field(name="ID", value=str(channel.id), inline=True)
        
        if hasattr(channel, 'created_at'):
            embed.add_field(name="Created", value=channel.created_at.strftime("%B %d, %Y"), inline=True)
        
        if hasattr(channel, 'topic') and channel.topic:
            embed.add_field(name="Topic", value=channel.topic, inline=False)
        
        if hasattr(channel, 'slowmode_delay'):
            embed.add_field(name="Slowmode", value=f"{channel.slowmode_delay} seconds", inline=True)
        
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="Category", value=channel.category.name, inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="roles", description="List all server roles")
    async def list_roles(self, interaction: discord.Interaction):
        """List all roles in the server"""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
        
        embed = discord.Embed(
            title=f"📋 Roles in {interaction.guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        role_list = ""
        for role in roles:
            if role.name != "@everyone":
                member_count = len(role.members)
                role_list += f"{role.mention} - {member_count} members\n"
        
        if len(role_list) > 1024:
            role_list = role_list[:1000] + "...\n(List truncated)"
        
        embed.add_field(name="Roles", value=role_list or "No roles found", inline=False)
        embed.set_footer(text=f"Total roles: {len(roles)}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="role", description="Add or remove a role from a user")
    @app_commands.describe(
        action="Add or remove the role",
        member="Member to modify",
        role="Role to add/remove"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Add", value="add"),
        app_commands.Choice(name="Remove", value="remove")
    ])
    async def manage_role(self, interaction: discord.Interaction, action: str, member: discord.Member, role: discord.Role):
        """Add or remove a role from a member"""
        if not await has_permission(interaction.user, 'manage_roles'):
            await interaction.response.send_message("❌ You don't have permission to manage roles.", ephemeral=True)
            return
        
        # Check if bot can manage this role
        if role.position >= interaction.guild.me.top_role.position:
            await interaction.response.send_message("❌ I cannot manage this role (it's higher than my highest role).", ephemeral=True)
            return
        
        # Check if user can manage this role
        if role.position >= interaction.user.top_role.position and not await is_admin(interaction.user):
            await interaction.response.send_message("❌ You cannot manage this role (it's higher than your highest role).", ephemeral=True)
            return
        
        try:
            if action == "add":
                if role in member.roles:
                    await interaction.response.send_message(f"❌ {member.mention} already has the {role.mention} role.", ephemeral=True)
                    return
                
                await member.add_roles(role, reason=f"Role added by {interaction.user}")
                
                embed = discord.Embed(
                    title="✅ Role Added",
                    description=f"Added {role.mention} to {member.mention}",
                    color=discord.Color.green()
                )
            else:  # remove
                if role not in member.roles:
                    await interaction.response.send_message(f"❌ {member.mention} doesn't have the {role.mention} role.", ephemeral=True)
                    return
                
                await member.remove_roles(role, reason=f"Role removed by {interaction.user}")
                
                embed = discord.Embed(
                    title="✅ Role Removed",
                    description=f"Removed {role.mention} from {member.mention}",
                    color=discord.Color.orange()
                )
            
            embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            await interaction.response.send_message(embed=embed)
            
            if interaction.guild:
                self.logger.info(f"{interaction.user} {action}ed role {role.name} to/from {member} in {interaction.guild.name}")
        
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this role.", ephemeral=True)
    
    @app_commands.command(name="announce", description="Make an announcement")
    @app_commands.describe(channel="Channel to announce in", message="Announcement message")
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        """Make an announcement in a channel"""
        if not await has_permission(interaction.user, 'manage_messages'):
            await interaction.response.send_message("❌ You don't have permission to make announcements.", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📢 Announcement",
            description=message,
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Announced by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        try:
            await channel.send(embed=embed)
            
            success_embed = discord.Embed(
                title="✅ Announcement Sent",
                description=f"Announcement sent to {channel.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=success_embed)
            
            if interaction.guild:
                self.logger.info(f"{interaction.user} made announcement in {channel.name}: {message[:50]}...")
        
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)
    
    @app_commands.command(name="embed", description="Send a fancy embed message")
    @app_commands.describe(title="Embed title", description="Embed description", color="Embed color (hex)")
    async def send_embed(self, interaction: discord.Interaction, title: str, description: str, color: str = "0x3498db"):
        """Send a custom embed"""
        if not await has_permission(interaction.user, 'manage_messages'):
            await interaction.response.send_message("❌ You don't have permission to send embeds.", ephemeral=True)
            return
        
        try:
            # Parse color
            if color.startswith('#'):
                color = color[1:]
            if color.startswith('0x'):
                color_int = int(color, 16)
            else:
                color_int = int(color, 16)
        except ValueError:
            color_int = 0x3498db  # Default blue
        
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color(color_int),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Created by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
        
        if interaction.guild:
            self.logger.info(f"{interaction.user} created embed: {title}")
    
    @app_commands.command(name="support", description="Get support server link")
    async def support(self, interaction: discord.Interaction):
        """Get support information"""
        embed = discord.Embed(
            title="🆘 Support",
            description="Need help with the bot? Here's how to get support:",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Commands",
            value="Use `/help` to see all available commands",
            inline=False
        )
        
        embed.add_field(
            name="Issues",
            value="Report bugs or issues to the server administrators",
            inline=False
        )
        
        embed.add_field(
            name="Features",
            value="The bot includes AI chat, moderation, games, utilities, and more!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerManagementCog(bot))