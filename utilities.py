import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timedelta
import logging
import base64
import io

class UtilitiesCog(commands.Cog):
    """Utility commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('utilities')
        self.reminders = {}
    
    @app_commands.command(name="ping", description="Show bot latency")
    async def ping(self, interaction: discord.Interaction):
        """Show bot latency"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency}ms**",
            color=discord.Color.green() if latency < 100 else discord.Color.yellow() if latency < 200 else discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="invite", description="Get bot invite link")
    async def invite(self, interaction: discord.Interaction):
        """Get bot invite link"""
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=discord.Permissions(
                kick_members=True,
                ban_members=True,
                manage_messages=True,
                manage_roles=True,
                moderate_members=True,
                send_messages=True,
                embed_links=True,
                read_message_history=True,
                use_slash_commands=True
            )
        )
        
        embed = discord.Embed(
            title="🔗 Invite Me!",
            description=f"[Click here to invite me to your server!]({invite_url})",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="time", description="Show current time")
    async def time(self, interaction: discord.Interaction):
        """Show current time"""
        now = datetime.now()
        embed = discord.Embed(
            title="🕐 Current Time",
            description=f"**{now.strftime('%Y-%m-%d %H:%M:%S UTC')}**",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="calc", description="Simple calculator")
    @app_commands.describe(expression="Mathematical expression to calculate")
    async def calc(self, interaction: discord.Interaction, expression: str):
        """Simple calculator"""
        # Clean the expression and allow only safe characters
        expression = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        
        if not expression:
            await interaction.response.send_message("❌ Invalid expression.", ephemeral=True)
            return
        
        try:
            # Evaluate safely
            result = eval(expression)
            
            embed = discord.Embed(
                title="🧮 Calculator",
                color=discord.Color.green()
            )
            embed.add_field(name="Expression", value=f"`{expression}`", inline=False)
            embed.add_field(name="Result", value=f"**{result}**", inline=False)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: Invalid expression.", ephemeral=True)
    
    @app_commands.command(name="remindme", description="Set a reminder")
    @app_commands.describe(time="Time in minutes", task="What to remind you about")
    async def remindme(self, interaction: discord.Interaction, time: int, task: str):
        """Set a reminder"""
        if time <= 0 or time > 10080:  # Max 1 week
            await interaction.response.send_message("❌ Time must be between 1 minute and 1 week (10080 minutes).", ephemeral=True)
            return
        
        reminder_time = datetime.now() + timedelta(minutes=time)
        reminder_id = f"{interaction.user.id}_{int(datetime.now().timestamp())}"
        
        self.reminders[reminder_id] = {
            'user': interaction.user,
            'task': task,
            'time': reminder_time,
            'channel': interaction.channel
        }
        
        embed = discord.Embed(
            title="⏰ Reminder Set",
            description=f"I'll remind you about: **{task}**\nIn: **{time} minutes**",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        
        # Wait and send reminder
        await asyncio.sleep(time * 60)
        
        if reminder_id in self.reminders:
            reminder = self.reminders[reminder_id]
            embed = discord.Embed(
                title="⏰ Reminder",
                description=f"You asked me to remind you: **{task}**",
                color=discord.Color.orange()
            )
            try:
                await reminder['channel'].send(f"{reminder['user'].mention}", embed=embed)
            except:
                try:
                    await reminder['user'].send(embed=embed)
                except:
                    pass
            
            del self.reminders[reminder_id]
    
    @app_commands.command(name="timer", description="Start a countdown timer")
    @app_commands.describe(seconds="Timer duration in seconds")
    async def timer(self, interaction: discord.Interaction, seconds: int):
        """Start a timer"""
        if seconds <= 0 or seconds > 3600:  # Max 1 hour
            await interaction.response.send_message("❌ Timer must be between 1 second and 1 hour (3600 seconds).", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="⏱️ Timer Started",
            description=f"Timer set for **{seconds} seconds**",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        
        await asyncio.sleep(seconds)
        
        embed = discord.Embed(
            title="⏰ Timer Finished",
            description=f"Your {seconds}-second timer is up!",
            color=discord.Color.red()
        )
        try:
            await interaction.followup.send(f"{interaction.user.mention}", embed=embed)
        except:
            await interaction.channel.send(f"{interaction.user.mention}", embed=embed)
    
    @app_commands.command(name="avatar", description="Show user's avatar")
    @app_commands.describe(user="User to show avatar for")
    async def avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        """Show user avatar"""
        if user is None:
            user = interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {user.display_name}'s Avatar",
            color=user.color if hasattr(user, 'color') else discord.Color.blue()
        )
        embed.set_image(url=user.display_avatar.url)
        embed.add_field(name="Download", value=f"[Click here]({user.display_avatar.url})", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="define", description="Get definition of a word")
    @app_commands.describe(word="Word to define")
    async def define(self, interaction: discord.Interaction, word: str):
        """Define a word"""
        definitions = {
            "python": "A high-level programming language known for its simplicity and readability.",
            "discord": "A voice, video, and text communication service used by gamers and communities.",
            "bot": "An automated program that performs tasks on behalf of users.",
            "ai": "Artificial Intelligence - computer systems that can perform tasks typically requiring human intelligence.",
            "algorithm": "A step-by-step procedure for solving a problem or completing a task.",
            "code": "Instructions written in a programming language to create software.",
            "debug": "The process of finding and fixing errors in computer programs.",
            "server": "A computer system that provides data, services, or programs to other computers.",
            "database": "An organized collection of structured information stored electronically.",
            "api": "Application Programming Interface - a set of protocols for building software applications."
        }
        
        word_lower = word.lower()
        if word_lower in definitions:
            embed = discord.Embed(
                title=f"📖 Definition: {word.title()}",
                description=definitions[word_lower],
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="📖 Dictionary",
                description=f"Sorry, I don't have a definition for '{word}'. Try searching online!",
                color=discord.Color.orange()
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="shorten", description="Shorten a URL")
    @app_commands.describe(url="URL to shorten")
    async def shorten(self, interaction: discord.Interaction, url: str):
        """Shorten a URL"""
        # Simple URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
        
        # For this demo, we'll just show the original URL
        # In a real implementation, you'd integrate with a URL shortening service
        embed = discord.Embed(
            title="🔗 URL Shortener",
            description="URL shortening service not configured. Here's your original URL:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Original URL", value=url, inline=False)
        embed.add_field(name="Note", value="To enable URL shortening, configure a service like bit.ly or tinyurl.", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="qr", description="Generate QR code")
    @app_commands.describe(text="Text or URL to encode")
    async def qr(self, interaction: discord.Interaction, text: str):
        """Generate QR code"""
        # For this demo, we'll provide a link to a QR generator
        # In a real implementation, you'd generate the QR code image
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={text}"
        
        embed = discord.Embed(
            title="📱 QR Code Generator",
            description=f"QR Code for: `{text}`",
            color=discord.Color.blue()
        )
        embed.set_image(url=qr_url)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="emojify", description="Convert text to emojis")
    @app_commands.describe(text="Text to convert to emojis")
    async def emojify(self, interaction: discord.Interaction, text: str):
        """Convert text to emojis"""
        emoji_map = {
            'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪', 'f': '🇫',
            'g': '🇬', 'h': '🇭', 'i': '🇮', 'j': '🇯', 'k': '🇰', 'l': '🇱',
            'm': '🇲', 'n': '🇳', 'o': '🇴', 'p': '🇵', 'q': '🇶', 'r': '🇷',
            's': '🇸', 't': '🇹', 'u': '🇺', 'v': '🇻', 'w': '🇼', 'x': '🇽',
            'y': '🇾', 'z': '🇿', ' ': '   ', '!': '❗', '?': '❓'
        }
        
        emojified = ''.join(emoji_map.get(char.lower(), char) for char in text[:20])  # Limit length
        
        embed = discord.Embed(
            title="🎭 Emojify",
            color=discord.Color.blue()
        )
        embed.add_field(name="Original", value=text[:100], inline=False)
        embed.add_field(name="Emojified", value=emojified, inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilitiesCog(bot))