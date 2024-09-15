from builtins import print

import discord
from discord.ext import commands
from ipaddress import ip_address
from requests import get


class Pinger(commands.Cog):
    def __init__(self, client):
        pass

    @commands.command()
    @commands.has_any_role(740572327846346873, 983341516460290058)
    async def status(self, ctx):
        await ctx.message.delete()

        speedy = "Speedy#8557"
        user = ctx.message.author.name + '#' + ctx.message.author.discriminator

        if user == speedy:
            print("test")
            ip = get('https://api.ipify.org').text
            await ctx.message.author.send(ip)

def setup(client):
    client.add_cog(Pinger(client))