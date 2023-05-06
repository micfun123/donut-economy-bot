import discord
import os
from os import listdir
from os.path import isfile, join
import os
from dotenv import load_dotenv
load_dotenv()

from discord.ext import commands

client = commands.Bot(case_insensitive=True, command_prefix="!", intents=discord.Intents.all())


@client.event
async def on_ready():
    # Setting `Playing ` status
    print("we have powered on, I an alive.")
    await client.change_presence(activity=discord.Game(f"I do art stuff in {len(client.guilds)} servers."))
    print(f"Logged in as {client.user.name} ({client.user.id})")
    

@client.event
async def on_guild_join(guild):
    await client.change_presence(activity=discord.Game(f"I do art stuff in {len(client.guilds)} servers."))
    

@client.event
async def on_guild_remove(guild):
    await client.change_presence(activity=discord.Game(f"I do art stuff in {len(client.guilds)} servers."))
    

TOKEN = os.getenv("DISCORD_TOKEN")

def start_bot(client):
    lst = [f for f in listdir("cogs/") if isfile(join("cogs/", f))]
    no_py = [s.replace('.py', '') for s in lst]
    startup_extensions = ["cogs." + no_py for no_py in no_py]
    try:
        for cogs in startup_extensions:
            client.load_extension(cogs)  # Startup all cogs
            print(f"Loaded {cogs}")

        print("\nAll Cogs Loaded\n===============\nLogging into Discord...")
        client.run(TOKEN) # Token do not change it here. Change it in the .env if you do not have a .env make a file and put DISCORD_TOKEN=Token 

    except Exception as e:
        print(
            f"\n###################\nPOSSIBLE FATAL ERROR:\n{e}\nTHIS MEANS THE BOT HAS NOT STARTED CORRECTLY!")



start_bot(client)