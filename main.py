import os
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from dotenv import load_dotenv
import logging
import uuid
import subprocess

from scraper import fetch_sb_data, get_sb_number
from game_logic import Game
from database import (
    init_db, 
    set_channel_config, 
    get_channel_config, 
    save_game_session, 
    load_game_session, 
    clear_game_sessions,
    load_all_active_sessions
)

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
print(TOKEN)  # Debugging line to check if the token is loaded correctly

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=";", intents=intents)

# Dictionary to store active games by channel_id
active_games = {}

@bot.event
async def on_ready():
    logging.info(f"Logged in as {bot.user.name} ({bot.user.id})")
    await init_db()
    # Load ongoing games from the database
    try:
        loaded_sessions = await load_all_active_sessions()
        for session_data in loaded_sessions:
            channel_id = session_data["channel_id"]
            server_id = session_data["server_id"]
            session_id = session_data["session_id"]
            game_data = session_data["game_data"]
            try:
                game = Game.from_dict(game_data)
                active_games[channel_id] = {"game": game, "session_id": session_id}
                logging.info(f"Loaded active game for Server {server_id}, Channel {channel_id} (Session ID: {session_id}).")
            except Exception as e:
                logging.error(f"Error loading game session {session_id} for Server {server_id}, Channel {channel_id}: {e}")
    except Exception as e:
        logging.error(f"Error loading sessions from database: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def sbc(ctx):
    """Set the current channel as the dedicated Spelling Bee channel for this server."""
    server_id = ctx.guild.id
    channel_id = ctx.channel.id
    await set_channel_config(server_id, channel_id)
    await ctx.send(f"This channel ({ctx.channel.mention}) has been set as the Spelling Bee channel for this server.")
    logging.info(f"Server {server_id}: Spelling Bee channel set to {channel_id}")

@bot.command()
async def sbhelp(ctx):
    """Displays the list of Spelling Bee bot commands and their functionality."""
    help_embed = discord.Embed(
        title="Spelling Bee Bot Commands",
        description="Here's how you can play the Spelling Bee game:",
        color=0xF7DA21
    )
    help_embed.add_field(
        name="`;sb <date>`",
        value="Start a new Spelling Bee game. Date is optional (YYYY-MM-DD).",
        inline=False
    )
    help_embed.add_field(
        name="`;sbend`",
        value="End the current game and display final scores.",
        inline=False
    )
    help_embed.add_field(
        name="`;sbhint`",
        value="Get hints for the current active game.",
        inline=False
    )
    help_embed.add_field(
        name="`;ans`",
        value="Show found words grouped by their first two letters.",
        inline=False
    )
    help_embed.add_field(
        name="`;sbreact`",
        value="Toggle ✅/🔁 reactions for guesses.",
        inline=False
    )
    help_embed.add_field(
        name="`;sbc` (Admin Only)",
        value="Set the current channel as the dedicated Spelling Bee channel.",
        inline=False
    )
    help_embed.set_footer(text="Happy puzzling! Commands start with ';'")
    await ctx.send(embed=help_embed)

async def check_channel(ctx):
    configured_channel_id = await get_channel_config(ctx.guild.id)
    if configured_channel_id and ctx.channel.id != configured_channel_id:
        await ctx.send(f"Please use the designated Spelling Bee channel: <#{configured_channel_id}>", delete_after=5)
        return False
    return True

@bot.command()
async def sb(ctx, *, date_str: str = None):
    """Start a Spelling Bee game."""
    if not await check_channel(ctx): return

    if ctx.channel.id in active_games:
        await ctx.send("A game is already active. End it with `;sbend` first.")
        return

    date_obj = datetime.now()
    if date_str:
        try:
            date_obj = date_parser.parse(date_str)
        except ValueError:
            await ctx.send("Invalid date format. Use YYYY-MM-DD.")
            return

    current_sb_number = get_sb_number(date_obj)
    data = await fetch_sb_data(current_sb_number)

    if not data:
        yesterday_date_obj = date_obj - timedelta(days=1)
        yesterday_sb_number = get_sb_number(yesterday_date_obj)
        data = await fetch_sb_data(yesterday_sb_number)
        
        if not data:
            await ctx.send("Error: Could not retrieve Spelling Bee data for today or yesterday.")
            return
        date_to_display, sb_num_to_display = yesterday_date_obj, yesterday_sb_number
    else:
        date_to_display, sb_num_to_display = date_obj, current_sb_number

    await clear_game_sessions(ctx.channel.id, ctx.guild.id)

    game = Game(data["center"], data["outer"], data["words"], data["pangrams"], reactions_enabled=False)
    session_id = str(uuid.uuid4())
    active_games[ctx.channel.id] = {"game": game, "session_id": session_id}
    await save_game_session(session_id, ctx.channel.id, ctx.guild.id, game.__dict__)
    
    await ctx.send(embed=game.get_game_start_embed(sb_num_to_display, date_to_display.strftime('%Y-%m-%d')))
    logging.info(f"Server {ctx.guild.id}, Channel {ctx.channel.id}: Game started (Session: {session_id}).")

@bot.command()
async def sbreact(ctx):
    """Toggle reactions."""
    if not await check_channel(ctx): return
    if ctx.channel.id in active_games:
        game = active_games[ctx.channel.id]["game"]
        game.reactions_enabled = not game.reactions_enabled
        await ctx.send(f"Word reactions are now **{'enabled' if game.reactions_enabled else 'disabled'}**.")
    else:
        await ctx.send("No active game in this channel.")

@bot.command()
async def sbend(ctx):
    """End the current game."""
    if not await check_channel(ctx): return
    if ctx.channel.id in active_games:
        game_data = active_games.pop(ctx.channel.id)
        await clear_game_sessions(ctx.channel.id, ctx.guild.id)
        await ctx.send("Game ended manually.", embed=game_data["game"].get_stats_embed(title="Spelling Bee - Final Results"))
        logging.info(f"Server {ctx.guild.id}, Channel {ctx.channel.id}: Game ended (Session: {game_data['session_id']}).")
    else:
        await ctx.send("No active game to end.")

@bot.command()
async def sbhint(ctx):
    """Get hints."""
    if not await check_channel(ctx): return
    if ctx.channel.id in active_games:
        await ctx.send(embed=active_games[ctx.channel.id]["game"].get_hints_embed())
    else:
        await ctx.send("No active game in this channel.")

@bot.command(name="ans")
async def ans(ctx):
    """Show found words."""
    if not await check_channel(ctx): return
    if ctx.channel.id in active_games:
        await ctx.send(embed=active_games[ctx.channel.id]["game"].get_found_words_embed())
    else:
        await ctx.send("No active game in this channel.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Process commands ONLY
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    # If it's not a command, check channel and process guess
    configured_channel_id = await get_channel_config(message.guild.id)
    if configured_channel_id and message.channel.id != configured_channel_id:
        return

    if message.channel.id in active_games:
        content = message.content.strip().upper()
        if len(content.split()) == 1:
            game_data = active_games[message.channel.id]
            game = game_data["game"]
            session_id = game_data["session_id"]

            if game.is_valid_word(content):
                game.add_found_word(content, message.author.mention)
                await save_game_session(session_id, message.channel.id, message.guild.id, game.__dict__)
                
                if game.is_complete():
                    active_games.pop(message.channel.id)
                    await clear_game_sessions(message.channel.id, message.guild.id)
                    await message.channel.send(
                        content="🐝 **QUEEN BEE!** 🐝 All words found!",
                        embed=game.get_stats_embed(title="Spelling Bee - Queen Bee Victory!")
                    )
                    logging.info(f"Server {message.guild.id}, Channel {message.channel.id}: Queen Bee achieved.")
                elif game.reactions_enabled:
                    await message.add_reaction("✅")
            elif content in game.found_words and game.reactions_enabled:
                await message.add_reaction("🔁")

if __name__ == "__main__":
    # Start the HTTP server in the background
    try:
        subprocess.Popen("python http_server.py", shell=True, preexec_fn=os.setsid)
        logging.info("HTTP server started in background.")
    except Exception as e:
        logging.error(f"Failed to start HTTP server: {e}")
        
    bot.run(TOKEN)
