import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime
import logging

class PollsCog(commands.Cog):
    """Polls and voting commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('polls')
        self.active_polls = {}
    
    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)"
    )
    async def poll(self, interaction: discord.Interaction, question: str, option1: str, option2: str, 
                   option3: str = None, option4: str = None, option5: str = None):
        """Create a poll with up to 5 options"""
        
        options = [option1, option2]
        if option3: options.append(option3)
        if option4: options.append(option4)
        if option5: options.append(option5)
        
        # Emojis for voting
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
        
        embed = discord.Embed(
            title="📊 Poll",
            description=question,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        poll_text = ""
        for i, option in enumerate(options):
            poll_text += f"{emojis[i]} {option}\n"
        
        embed.add_field(name="Options", value=poll_text, inline=False)
        embed.set_footer(text=f"Created by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        # Add reactions
        for i in range(len(options)):
            await message.add_reaction(emojis[i])
        
        self.logger.info(f"Poll created by {interaction.user} with {len(options)} options")
    
    @app_commands.command(name="vote", description="Start a simple yes/no vote")
    @app_commands.describe(topic="What to vote on")
    async def vote(self, interaction: discord.Interaction, topic: str):
        """Start a yes/no vote"""
        embed = discord.Embed(
            title="🗳️ Vote",
            description=topic,
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="Options", value="✅ Yes\n❌ No", inline=False)
        embed.set_footer(text=f"Started by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        
        self.logger.info(f"Vote started by {interaction.user}: {topic}")
    
    @app_commands.command(name="opinion", description="Ask for user opinions")
    @app_commands.describe(topic="Topic to get opinions on")
    async def opinion(self, interaction: discord.Interaction, topic: str):
        """Ask for opinions on a topic"""
        embed = discord.Embed(
            title="💭 Opinion Request",
            description=f"**{topic}**\n\nShare your thoughts in the replies!",
            color=discord.Color.purple(),
            timestamp=datetime.now()
        )
        embed.set_footer(text=f"Asked by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        
        self.logger.info(f"Opinion request by {interaction.user}: {topic}")

async def setup(bot):
    await bot.add_cog(PollsCog(bot))