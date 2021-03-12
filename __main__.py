# api doc at https://discordpy.readthedocs.io/en/latest/api.html#client

from discord import Activity
from discord.ext import commands
from discord.ext.commands import Bot
import sys

from utils.JsonCon import JsonCon
from utils.MySQLCon import MySQLCon

print("Bot is starting...")

config = JsonCon.load_config("config.json")

BOT_PREFIX = "!"
TOKEN = config['token']

extensions = ["cogs.Settings"]

client = Bot(command_prefix=BOT_PREFIX)
client.db = MySQLCon(config['db']['host'], config['db']['user'], config['db']['password'], config['db']['database'])

if __name__ == '__main__':
    for extension in extensions:
        try:
            client.load_extension(extension)
        except Exception as error:
            print('{} cannot be loaded. [{}]'.format(extension, error))


@client.event
async def on_ready():
    status = Activity(name=BOT_PREFIX + "help", type=2)
    await client.change_presence(activity=status)
    print("Bot is ready\n")


@client.event
async def on_guild_join(guild):
    print("Bot joined server: " + guild.name + "<" + str(guild.id) + ">")
    db.init_server(guild.id, guild.name)


@client.event
async def on_command_error(ctx, command_error):
    """ Handles command errors """

    if isinstance(command_error, commands.CheckFailure):
        # This would allow the identification of the failing check
        print("ignored command cause not mod or karaoke")
    elif isinstance(command_error, commands.CommandNotFound):
        return
    else:
        print(command_error)


@client.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


@client.check
async def globally_block_bot(ctx):
    return not ctx.author.bot


client.run(TOKEN, bot=True, reconnect=True)
