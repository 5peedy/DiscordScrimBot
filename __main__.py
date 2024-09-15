# api doc at https://discordpy.readthedocs.io/en/latest/api.html#client

from discord import Activity
from discord.ext import commands
from discord.ext.commands import Bot
from discord import Intents

from utils.JsonCon import JsonCon
from utils.MySQLCon import MySQLCon
from utils.Checks import Checks
from utils import Notification

print("Bot is starting...")

config = JsonCon.load_config("config.json")

BOT_PREFIX = "!"
TOKEN = config['token']

extensions = ["cogs.Settings", "cogs.Scrim", "cogs.Util"]

intents = Intents.default()
intents.members = True

client = Bot(command_prefix=BOT_PREFIX, intents=intents)
client.db = MySQLCon(config['db']['host'], config['db']['user'], config['db']['password'], config['db']['database'])
client.prefix = BOT_PREFIX
client.checks = Checks(client=client)

if __name__ == '__main__':
    for extension in extensions:
        try:
            client.load_extension(extension)
            print('{} loaded successfully'.format(extension))
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
    client.db.init_server(guild.id, guild.name)


@client.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


@client.check
async def globally_block_bot(ctx):
    return not ctx.author.bot


@client.command(name="restart", brief="reconnect to database")
@commands.has_guild_permissions(administrator=True)
async def reconnect_db(ctx):
    await ctx.message.delete()
    client.db = MySQLCon(config['db']['host'], config['db']['user'], config['db']['password'], config['db']['database'])
    await Notification.send_approve(ctx, description="Reconnected to database")


client.run(TOKEN, bot=True, reconnect=True)
