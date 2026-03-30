import os
import discord
from discord.ext import commands
from datetime import datetime
from dateutil import parser as date_parser
from scraper import fetch_sb_data, get_sb_number
from game_logic import Game

# Environment variable for token
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

    sb_number = get_sb_number(date_obj)
    await ctx.send(f"Fetching Spelling Bee #{sb_number} for {date_obj.strftime('%Y-%m-%d')}...")
    
    data = await fetch_sb_data(sb_number)
    if not data:
        # If the specific number fails, try "latest"
        await ctx.send("Could not find data for that date. Trying to fetch the latest available puzzle...")
        # Since I don't know the exact "latest" number, I could try a few increments, but
        # a better way is to just use a special "latest" endpoint if SBSolver has one.
        # SBSolver has /latest
        # Let's try to fetch from /latest
        import aiohttp
        from bs4 import BeautifulSoup
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.sbsolver.com/latest") as response:
                # This usually redirects or provides the latest content
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    # Try to extract data from this page
                    # I'll just reuse the same extraction logic by parsing the current URL or the input
                    letters_input = soup.find("input", id="string")
                    if letters_input:
                        letters_str = letters_input.get("value", "")
                        center = letters_str[0].upper()
                        outer = [c.upper() for c in letters_str[1:]]
                        # Words
                        words = []
                        table = soup.find("table", class_="bee-set")
                        if table:
                            rows = table.find_all("tr")
                            for row in rows:
                                word_td = row.find("td", class_="bee-hover")
                                if word_td:
                                    word = word_td.get_text(strip=True).upper()
                                    words.append(word)
                        if words:
                            data = {"center": center, "outer": outer, "words": words}
                
    if not data:
        await ctx.send("Error: Could not retrieve Spelling Bee data.")
        return

    game = Game(data["center"], data["outer"], data["words"])
    active_games[ctx.channel.id] = game
    
    # Format message
    outer_letters = " ".join(game.outer)
    msg = f"**Spelling Bee Started!**\n"
    msg += f"Center Letter (Must be used): **{game.center}**\n"
    msg += f"Other Letters: {outer_letters}\n"
    msg += f"Total Words to find: {len(game.all_words)}"
    
    await ctx.send(msg)

@bot.command()
async def sbend(ctx):
    """End the current Spelling Bee game."""
    if ctx.channel.id in active_games:
        game = active_games.pop(ctx.channel.id)
        await ctx.send(game.get_stats_message())
    else:
        await ctx.send("No active game in this channel.")

@bot.command()
async def sbhint(ctx):
    """Get hints for the current game."""
    if ctx.channel.id in active_games:
        game = active_games[ctx.channel.id]
        await ctx.send(game.get_hints())
    else:
        await ctx.send("No active game in this channel.")

@bot.command(name="ans")
async def ans(ctx):
    """Show found words."""
    if ctx.channel.id in active_games:
        game = active_games[ctx.channel.id]
        await ctx.send(game.get_found_words())
    else:
        await ctx.send("No active game in this channel.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Check for game commands first
    await bot.process_commands(message)

    # Check if message is a guess
    if message.channel.id in active_games:
        content = message.content.strip().upper()
        # Ensure it's a single word and not a command
        if len(content.split()) == 1 and not content.startswith(";"):
            game = active_games[message.channel.id]
            if game.is_valid_word(content):
                game.add_found_word(content, message.author.name)
                # Check if game complete
                if game.is_complete():
                    await message.channel.send(f"Correct! **{content}**")
                    game = active_games.pop(message.channel.id)
                    await message.channel.send(game.get_stats_message())
                else:
                    # Optional: Add a reaction or short message for correct guess
                    await message.add_reaction("✅")
            elif content in game.found_words:
                await message.add_reaction("🔁") # Already found

if __name__ == "__main__":
    if not TOKEN:
        print("Please set the DISCORD_TOKEN environment variable.")
    else:
        bot.run(TOKEN)
