import discord
from discord.ext import commands

# ================= INTENTS =================
intents = discord.Intents.default()
intents.voice_states = True
intents.guilds = True
intents.members = False
intents.message_content = False  # Enable only if prefix commands are needed

# ================= BOT =================
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents,
    help_command=None,
)

# ================= APP COMMAND TREE =================
tree = bot.tree
