from discord.ext import commands


class Scrim(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def initScrim(self, ctx):


    @commands.command()
    async def checkin(self, ctx):



def setup(client):
    client.add_cog(Scrim(client))
