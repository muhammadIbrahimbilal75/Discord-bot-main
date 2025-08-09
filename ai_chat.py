import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import json

from config import BotConfig
from utils.filters import MessageFilter
from utils.permissions import has_permission

class AIChatCog(commands.Cog):
    """AI-powered conversation capabilities using OpenAI"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('ai_chat')
        self.user_cooldowns: Dict[int, datetime] = {}
        self.message_filter = MessageFilter()
        
    async def is_on_cooldown(self, user_id: int) -> bool:
        """Check if user is on cooldown for AI requests"""
        if user_id not in self.user_cooldowns:
            return False
        
        time_diff = datetime.now() - self.user_cooldowns[user_id]
        return time_diff.total_seconds() < BotConfig.AI_COOLDOWN
    
    def set_cooldown(self, user_id: int):
        """Set cooldown for user"""
        self.user_cooldowns[user_id] = datetime.now()
    
    def _clean_response(self, response: str) -> str:
        """Clean AI response from unwanted formatting characters"""
        import re
        
        # Remove common unwanted formatting characters at the start/end
        response = response.strip()
        
        # Remove leading brackets, parentheses, or other symbols
        response = re.sub(r'^[\[\](){}/<>*_`~|\\]+\s*', '', response)
        
        # Remove trailing brackets, parentheses, or other symbols
        response = re.sub(r'\s*[\[\](){}/<>*_`~|\\]+$', '', response)
        
        # Remove markdown-style formatting
        response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)  # Bold
        response = re.sub(r'\*(.*?)\*', r'\1', response)      # Italic
        response = re.sub(r'`(.*?)`', r'\1', response)        # Code
        response = re.sub(r'~~(.*?)~~', r'\1', response)      # Strikethrough
        
        # Remove multiple spaces and clean up
        response = re.sub(r'\s+', ' ', response).strip()
        
        return response
    
    async def generate_ai_response(self, message: str, user_name: str) -> Optional[str]:
        """Generate AI response using OpenRouter"""
        try:
            # Filter inappropriate content
            if self.message_filter.contains_filtered_words(message):
                return "I can't respond to that type of message. Let's talk about something else!"
            
            # Prepare messages for OpenRouter
            messages = [
                {
                    "role": "system",
                    "content": BotConfig.get_ai_system_prompt()
                },
                {
                    "role": "user",
                    "content": f"User {user_name} says: {message}"
                }
            ]
            
            # Call OpenRouter API
            headers = {
                "Authorization": f"Bearer {BotConfig.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": BotConfig.OPENROUTER_MODEL,
                "messages": messages,
                "max_tokens": BotConfig.MAX_TOKENS,
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        raw_response = data["choices"][0]["message"]["content"].strip()
                        return self._clean_response(raw_response)
                    else:
                        error_text = await response.text()
                        self.logger.error(f"OpenRouter API error {response.status}: {error_text}")
                        return "🚫 AI service is temporarily unavailable. Please try again later."
            
        except Exception as e:
            self.logger.error(f"Unexpected error in AI response: {e}")
            return "🚫 Something went wrong while generating a response."
    
    @app_commands.command(name="chat", description="Chat with the AI assistant")
    @app_commands.describe(message="Your message to the AI")
    async def chat_command(self, interaction: discord.Interaction, message: str):
        """Slash command for AI chat"""
        # Check cooldown
        if await self.is_on_cooldown(interaction.user.id):
            await interaction.response.send_message(
                f"⏰ Please wait {BotConfig.AI_COOLDOWN} seconds between AI requests.",
                ephemeral=True
            )
            return
        
        # Check if AI is disabled in this channel
        if hasattr(interaction.channel, 'name') and interaction.channel.name in BotConfig.AI_DISABLED_CHANNELS:
            await interaction.response.send_message(
                "🚫 AI chat is disabled in this channel.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        
        # Set cooldown
        self.set_cooldown(interaction.user.id)
        
        # Generate response
        ai_response = await self.generate_ai_response(message, interaction.user.display_name)
        
        if ai_response:
            # Create embed for response
            embed = discord.Embed(
                description=ai_response,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.set_author(
                name=f"AI Response to {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            embed.set_footer(text="Powered by OpenAI")
            
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("🚫 Failed to generate AI response.")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for mentions and respond with AI"""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Check if bot is mentioned
        if self.bot.user in message.mentions:
            # Check cooldown
            if await self.is_on_cooldown(message.author.id):
                await message.reply(f"⏰ Please wait {BotConfig.AI_COOLDOWN} seconds between AI requests.")
                return
            
            # Check if AI is disabled in this channel
            if hasattr(message.channel, 'name') and message.channel.name in BotConfig.AI_DISABLED_CHANNELS:
                await message.reply("🚫 AI chat is disabled in this channel.")
                return
            
            # Get message content without mentions
            content = message.content
            for mention in message.mentions:
                content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
            content = content.strip()
            
            if not content:
                content = "Hi!"
            
            # Set cooldown
            self.set_cooldown(message.author.id)
            
            async with message.channel.typing():
                ai_response = await self.generate_ai_response(content, message.author.display_name)
            
            if ai_response:
                # Create embed for response
                embed = discord.Embed(
                    description=ai_response,
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                embed.set_author(
                    name=f"AI Response to {message.author.display_name}",
                    icon_url=message.author.display_avatar.url
                )
                embed.set_footer(text="Powered by OpenRouter")
                
                await message.reply(embed=embed)
            else:
                await message.reply("🚫 Failed to generate AI response.")

    @commands.command(name="ask")
    @commands.cooldown(1, BotConfig.COMMAND_COOLDOWN, commands.BucketType.user)
    async def ask_command(self, ctx, *, message: str):
        """Traditional command for AI chat"""
        # Check cooldown
        if await self.is_on_cooldown(ctx.author.id):
            await ctx.send(f"⏰ Please wait {BotConfig.AI_COOLDOWN} seconds between AI requests.")
            return
        
        # Check if AI is disabled in this channel
        if hasattr(ctx.channel, 'name') and ctx.channel.name in BotConfig.AI_DISABLED_CHANNELS:
            await ctx.send("🚫 AI chat is disabled in this channel.")
            return
        
        # Set cooldown
        self.set_cooldown(ctx.author.id)
        
        async with ctx.typing():
            ai_response = await self.generate_ai_response(message, ctx.author.display_name)
        
        if ai_response:
            # Create embed for response
            embed = discord.Embed(
                description=ai_response,
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed.set_author(
                name=f"AI Response to {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            embed.set_footer(text="Powered by OpenAI")
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("🚫 Failed to generate AI response.")
    
    @app_commands.command(name="ai", description="Chat with AI")
    @app_commands.describe(prompt="Your message to the AI")
    async def ai_command(self, interaction: discord.Interaction, prompt: str):
        """AI chat command (alias for chat)"""
        await self.chat_command(interaction, prompt)
    
    @app_commands.command(name="ask", description="Ask ChatGPT anything")
    @app_commands.describe(question="Your question for the AI")
    async def ask_command(self, interaction: discord.Interaction, question: str):
        """Ask ChatGPT command (alias for chat)"""
        await self.chat_command(interaction, question)
    
    @app_commands.command(name="summarize", description="Summarize text")
    @app_commands.describe(text="Text to summarize")
    async def summarize(self, interaction: discord.Interaction, text: str):
        """Summarize text using AI"""
        if await self.is_on_cooldown(interaction.user.id):
            await interaction.response.send_message(
                f"⏰ Please wait {BotConfig.AI_COOLDOWN} seconds between AI requests.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        self.set_cooldown(interaction.user.id)
        
        summary_prompt = f"Please provide a concise summary of the following text: {text}"
        ai_response = await self.generate_ai_response(summary_prompt, interaction.user.display_name)
        
        if ai_response:
            embed = discord.Embed(
                title="📝 Text Summary",
                description=ai_response,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Powered by OpenRouter")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("🚫 Failed to generate summary.")
    
    @app_commands.command(name="translate", description="Translate text to English")
    @app_commands.describe(text="Text to translate")
    async def translate(self, interaction: discord.Interaction, text: str):
        """Translate text to English"""
        if await self.is_on_cooldown(interaction.user.id):
            await interaction.response.send_message(
                f"⏰ Please wait {BotConfig.AI_COOLDOWN} seconds between AI requests.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        self.set_cooldown(interaction.user.id)
        
        translate_prompt = f"Please translate the following text to English. If it's already in English, just return the original text: {text}"
        ai_response = await self.generate_ai_response(translate_prompt, interaction.user.display_name)
        
        if ai_response:
            embed = discord.Embed(
                title="🌐 Translation",
                color=discord.Color.blue()
            )
            embed.add_field(name="Original", value=text[:1000], inline=False)
            embed.add_field(name="Translation", value=ai_response, inline=False)
            embed.set_footer(text="Powered by OpenRouter")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("🚫 Failed to translate text.")
    
    @app_commands.command(name="codegen", description="Generate code")
    @app_commands.describe(task="Describe what code you need")
    async def codegen(self, interaction: discord.Interaction, task: str):
        """Generate code using AI"""
        if await self.is_on_cooldown(interaction.user.id):
            await interaction.response.send_message(
                f"⏰ Please wait {BotConfig.AI_COOLDOWN} seconds between AI requests.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        self.set_cooldown(interaction.user.id)
        
        code_prompt = f"Please generate clean, working code for this task: {task}. Provide only the code with minimal explanation."
        ai_response = await self.generate_ai_response(code_prompt, interaction.user.display_name)
        
        if ai_response:
            embed = discord.Embed(
                title="💻 Generated Code",
                description=f"```\n{ai_response}\n```",
                color=discord.Color.green()
            )
            embed.set_footer(text="Powered by OpenRouter")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("🚫 Failed to generate code.")
    
    @app_commands.command(name="agent", description="Talk to a custom AI agent")
    @app_commands.describe(persona="AI persona (helpful, creative, technical, etc.)", prompt="Your message")
    async def agent(self, interaction: discord.Interaction, persona: str, prompt: str):
        """Talk to a custom AI agent with specific persona"""
        if await self.is_on_cooldown(interaction.user.id):
            await interaction.response.send_message(
                f"⏰ Please wait {BotConfig.AI_COOLDOWN} seconds between AI requests.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        self.set_cooldown(interaction.user.id)
        
        agent_prompt = f"Act as a {persona} assistant. Respond to this request: {prompt}"
        ai_response = await self.generate_ai_response(agent_prompt, interaction.user.display_name)
        
        if ai_response:
            embed = discord.Embed(
                title=f"🤖 {persona.title()} Agent",
                description=ai_response,
                color=discord.Color.purple()
            )
            embed.set_footer(text="Powered by OpenRouter")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("🚫 Failed to generate agent response.")
    
    @app_commands.command(name="roleplay", description="Roleplay with an AI character")
    @app_commands.describe(character="Character to roleplay as", prompt="Your message to the character")
    async def roleplay(self, interaction: discord.Interaction, character: str, prompt: str):
        """Roleplay with an AI character"""
        if await self.is_on_cooldown(interaction.user.id):
            await interaction.response.send_message(
                f"⏰ Please wait {BotConfig.AI_COOLDOWN} seconds between AI requests.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer()
        self.set_cooldown(interaction.user.id)
        
        roleplay_prompt = f"You are roleplaying as {character}. Stay in character and respond to: {prompt}"
        ai_response = await self.generate_ai_response(roleplay_prompt, interaction.user.display_name)
        
        if ai_response:
            embed = discord.Embed(
                title=f"🎭 {character}",
                description=ai_response,
                color=discord.Color.gold()
            )
            embed.set_footer(text="Powered by OpenRouter")
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send("🚫 Failed to generate roleplay response.")
    
    @app_commands.command(name="ai-status", description="Check AI service status")
    async def ai_status(self, interaction: discord.Interaction):
        """Check if AI service is working"""
        await interaction.response.defer()
        
        try:
            # Quick test of OpenRouter API
            test_response = await self.generate_ai_response("Hi", "test_user")
            
            if test_response and not test_response.startswith("🚫"):
                embed = discord.Embed(
                    title="🟢 AI Service Status",
                    description="AI service is operational",
                    color=discord.Color.green()
                )
                embed.add_field(name="Model", value=BotConfig.OPENROUTER_MODEL, inline=True)
                embed.add_field(name="Max Tokens", value=BotConfig.MAX_TOKENS, inline=True)
                embed.add_field(name="Cooldown", value=f"{BotConfig.AI_COOLDOWN}s", inline=True)
            else:
                embed = discord.Embed(
                    title="🔴 AI Service Status",
                    description="AI service is currently unavailable",
                    color=discord.Color.red()
                )
                embed.add_field(name="Response", value=test_response or "No response", inline=False)
            
        except Exception as e:
            embed = discord.Embed(
                title="🔴 AI Service Status",
                description="AI service is currently unavailable",
                color=discord.Color.red()
            )
            embed.add_field(name="Error", value=str(e)[:100], inline=False)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIChatCog(bot))
