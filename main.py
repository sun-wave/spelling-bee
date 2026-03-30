import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dotenv import load_dotenv

from scraper import fetch_sb_data, get_sb_number
from game_logic import Game

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=";", intents=intents)

# Dictionary to store active games by channel_id
active_games = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")

@bot.command()
async def sb(ctx, *, date_str: str = None):
    """Start a Spelling Bee game for a specific date or today."""
    if date_str:
        try:
            date_obj = date_parser.parse(date_str)
        except ValueError:
            await ctx.send("Invalid date format. Please use YYYY-MM-DD or similar.")
            return
    else:
        date_obj = datetime.now()

    # Attempt to fetch today's spelling bee data
    current_date_obj = date_obj
    current_sb_number = get_sb_number(current_date_obj)
    data = await fetch_sb_data(current_sb_number)

    if not data:
        # If today's data is not found, try yesterday's
        yesterday_date_obj = current_date_obj - timedelta(days=1)
        yesterday_sb_number = get_sb_number(yesterday_date_obj)
        data = await fetch_sb_data(yesterday_sb_number)
        
        if not data:
            # If yesterday's also fails, send an error
            await ctx.send("Error: Could not retrieve Spelling Bee data for today or yesterday.")
            return
        else:
            # Use yesterday's date for the embed message if found
            date_to_display = yesterday_date_obj
            sb_num_to_display = yesterday_sb_number
    else:
        # Use today's date if found
        date_to_display = current_date_obj
        sb_num_to_display = current_sb_number

    game = Game(data["center"], data["outer"], data["words"], data["pangrams"], reactions_enabled=False)
    active_games[ctx.channel.id] = game
    
    await ctx.send(embed=game.get_game_start_embed(sb_num_to_display, date_to_display.strftime('%Y-%m-%d')))
@bot.command()
async def sbreact(ctx):
    """Toggle reactions for the current Spelling Bee game."""
    if ctx.channel.id in active_games:
        game = active_games[ctx.channel.id]
        game.reactions_enabled = not game.reactions_enabled
        status = "enabled" if game.reactions_enabled else "disabled"
        await ctx.send(f"Word reactions are now **{status}**.")
    else:
        await ctx.send("No active game in this channel.")

@bot.command()
async def sbend(ctx):
    """End the current Spelling Bee game."""
    if ctx.channel.id in active_games:
        game = active_games.pop(ctx.channel.id)
        await ctx.send("Game ended manually.", embed=game.get_stats_embed(title="Spelling Bee - Final Results"))
    else:
        await ctx.send("No active game to end.")

@bot.command()
async def sbhint(ctx):
    """Get hints for the current game."""
    if ctx.channel.id in active_games:
        game = active_games[ctx.channel.id]
        await ctx.send(embed=game.get_hints_embed())
    else:
        await ctx.send("No active game in this channel.")

@bot.command(name="ans")
async def ans(ctx):
    """Show found words."""
    if ctx.channel.id in active_games:
        game = active_games[ctx.channel.id]
        await ctx.send(embed=game.get_found_words_embed())
    else:
        await ctx.send("No active game in this channel.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Process commands
    if message.content.startswith(";"):
        await bot.process_commands(message)
        return

    # Check for game guess
    if message.channel.id in active_games:
        content = message.content.strip().upper()
        # Single word check
        if len(content.split()) == 1:
            game = active_games[message.channel.id]
            if game.is_valid_word(content):
                game.add_found_word(content, message.author.mention)
                
                if game.is_complete():

                    game = active_games.pop(message.channel.id)
                    await message.channel.send(
                        content="🐝 **QUEEN BEE!** 🐝\nAll words have been found!",
                        embed=game.get_stats_embed(title="Spelling Bee - Queen Bee Victory!")
                    )
                else:
                    if game.reactions_enabled:
                        await message.add_reaction("✅")
            elif content in game.found_words:
                if game.reactions_enabled:
                    await message.add_reaction("🔁")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in environment or .env file.")
    else:
        bot.run(TOKEN)
