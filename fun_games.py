import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from datetime import datetime
import logging

class FunGamesCog(commands.Cog):
    """Fun and Games commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('fun_games')
        self.active_games = {}
    
    @app_commands.command(name="coinflip", description="Flip a coin")
    async def coinflip(self, interaction: discord.Interaction):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        embed = discord.Embed(
            title="🪙 Coin Flip",
            description=f"**{result}!**",
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="roll", description="Roll a die")
    @app_commands.describe(sides="Number of sides on the die (default: 6)")
    async def roll(self, interaction: discord.Interaction, sides: int = 6):
        """Roll a die"""
        if sides < 2 or sides > 100:
            await interaction.response.send_message("❌ Die must have between 2 and 100 sides.", ephemeral=True)
            return
        
        result = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 Die Roll",
            description=f"You rolled a **{result}** on a {sides}-sided die!",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="8ball", description="Ask the magic 8-ball a question")
    @app_commands.describe(question="Your yes/no question")
    async def eightball(self, interaction: discord.Interaction, question: str):
        """Ask the magic 8-ball"""
        responses = [
            "Yes", "No", "Maybe", "Definitely", "Absolutely not",
            "Ask again later", "I don't think so", "Most likely",
            "Without a doubt", "Very doubtful", "Signs point to yes",
            "Reply hazy, try again", "Better not tell you now",
            "Cannot predict now", "Concentrate and ask again"
        ]
        
        answer = random.choice(responses)
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            color=discord.Color.purple()
        )
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Answer", value=f"**{answer}**", inline=False)
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="rps", description="Play Rock Paper Scissors")
    @app_commands.describe(choice="Your choice: rock, paper, or scissors")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Rock", value="rock"),
        app_commands.Choice(name="Paper", value="paper"),
        app_commands.Choice(name="Scissors", value="scissors")
    ])
    async def rps(self, interaction: discord.Interaction, choice: str):
        """Rock Paper Scissors game"""
        choices = ["rock", "paper", "scissors"]
        bot_choice = random.choice(choices)
        
        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
        
        # Determine winner
        if choice == bot_choice:
            result = "It's a tie!"
            color = discord.Color.yellow()
        elif (choice == "rock" and bot_choice == "scissors") or \
             (choice == "paper" and bot_choice == "rock") or \
             (choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
            color = discord.Color.green()
        else:
            result = "I win!"
            color = discord.Color.red()
        
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors",
            description=f"You chose {emojis[choice]} **{choice.title()}**\nI chose {emojis[bot_choice]} **{bot_choice.title()}**\n\n**{result}**",
            color=color
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="quiz", description="Start a trivia quiz")
    async def quiz(self, interaction: discord.Interaction):
        """Start a trivia quiz"""
        questions = [
            {"q": "What is the capital of France?", "a": "paris", "options": ["London", "Berlin", "Paris", "Madrid"]},
            {"q": "What is 2 + 2?", "a": "4", "options": ["3", "4", "5", "6"]},
            {"q": "What planet is known as the Red Planet?", "a": "mars", "options": ["Venus", "Mars", "Jupiter", "Saturn"]},
            {"q": "Who painted the Mona Lisa?", "a": "leonardo da vinci", "options": ["Picasso", "Van Gogh", "Leonardo da Vinci", "Michelangelo"]},
            {"q": "What is the largest ocean?", "a": "pacific", "options": ["Atlantic", "Pacific", "Indian", "Arctic"]}
        ]
        
        question = random.choice(questions)
        random.shuffle(question["options"])
        
        embed = discord.Embed(
            title="🧠 Trivia Quiz",
            description=question["q"],
            color=discord.Color.blue()
        )
        
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(question["options"])])
        embed.add_field(name="Options", value=options_text, inline=False)
        embed.set_footer(text="Type the number of your answer (1-4). You have 30 seconds!")
        
        await interaction.response.send_message(embed=embed)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit()
        
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            choice_num = int(msg.content) - 1
            
            if 0 <= choice_num < len(question["options"]):
                chosen_answer = question["options"][choice_num].lower()
                if question["a"] in chosen_answer.lower():
                    await msg.reply("✅ Correct! Well done!")
                else:
                    await msg.reply(f"❌ Wrong! The correct answer was: {question['a'].title()}")
            else:
                await msg.reply("❌ Invalid choice!")
                
        except asyncio.TimeoutError:
            await interaction.followup.send(f"⏰ Time's up! The correct answer was: {question['a'].title()}")
    
    @app_commands.command(name="guess", description="Number guessing game")
    @app_commands.describe(max_number="Maximum number to guess (default: 100)")
    async def guess(self, interaction: discord.Interaction, max_number: int = 100):
        """Number guessing game"""
        if max_number < 2 or max_number > 1000:
            await interaction.response.send_message("❌ Number range must be between 2 and 1000.", ephemeral=True)
            return
        
        number = random.randint(1, max_number)
        attempts = 0
        max_attempts = min(10, max_number // 10 + 3)
        
        embed = discord.Embed(
            title="🔢 Number Guessing Game",
            description=f"I'm thinking of a number between 1 and {max_number}!\nYou have {max_attempts} attempts to guess it.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit()
        
        while attempts < max_attempts:
            try:
                msg = await self.bot.wait_for('message', timeout=60.0, check=check)
                guess = int(msg.content)
                attempts += 1
                
                if guess == number:
                    await msg.reply(f"🎉 Congratulations! You guessed it in {attempts} attempts!")
                    return
                elif guess < number:
                    remaining = max_attempts - attempts
                    if remaining > 0:
                        await msg.reply(f"📈 Too low! {remaining} attempts remaining.")
                    else:
                        await msg.reply(f"📈 Too low! Game over! The number was {number}.")
                else:
                    remaining = max_attempts - attempts
                    if remaining > 0:
                        await msg.reply(f"📉 Too high! {remaining} attempts remaining.")
                    else:
                        await msg.reply(f"📉 Too high! Game over! The number was {number}.")
                        
            except asyncio.TimeoutError:
                await interaction.followup.send(f"⏰ Time's up! The number was {number}.")
                return
        
        await interaction.followup.send(f"😔 Game over! The number was {number}.")
    
    @app_commands.command(name="fact", description="Get a random interesting fact")
    async def fact(self, interaction: discord.Interaction):
        """Get a random fact"""
        facts = [
            "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still edible.",
            "A group of flamingos is called a 'flamboyance'.",
            "Bananas are berries, but strawberries aren't.",
            "The shortest war in history lasted only 38-45 minutes between Britain and Zanzibar in 1896.",
            "Octopuses have three hearts and blue blood.",
            "A day on Venus is longer than its year.",
            "The human brain uses about 20% of the body's total energy.",
            "There are more possible games of chess than atoms in the observable universe.",
            "Sharks have been around longer than trees.",
            "The Great Wall of China isn't visible from space with the naked eye."
        ]
        
        fact = random.choice(facts)
        embed = discord.Embed(
            title="🧠 Random Fact",
            description=fact,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="joke", description="Get a random joke")
    async def joke(self, interaction: discord.Interaction):
        """Get a random joke"""
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "Why don't eggs tell jokes? They'd crack each other up!",
            "What do you call a fake noodle? An impasta!",
            "Why did the math book look so sad? Because it had too many problems!",
            "What do you call a bear with no teeth? A gummy bear!",
            "Why don't skeletons fight each other? They don't have the guts!",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus!",
            "Why did the bicycle fall over? Because it was two tired!",
            "What do you call a sleeping bull? A bulldozer!"
        ]
        
        joke = random.choice(jokes)
        embed = discord.Embed(
            title="😂 Random Joke",
            description=joke,
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(FunGamesCog(bot))