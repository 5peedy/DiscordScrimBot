import asyncio

from discord.ext import commands
from utils import Notification
import discord

green = 0x11f711
red = 0xD10000
orange = 0xff8800
blue = 0x007BFD


class Util(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.group(name="clear", alias="scrims", invoke_without_command=True, brief="Commands for scrim handling")
    @commands.has_guild_permissions(administrator=True)
    async def clear(self, ctx):
        pass

    @clear.command(name="category", brief="Delets all channels inside a category")
    @commands.has_guild_permissions(administrator=True)
    async def clear_category(self, ctx):
        await ctx.message.delete()

        guild = ctx.guild

        name_embed = discord.Embed(title="Enter category name", color=orange)
        name_embed.set_footer(text="Message gets deleted after 5 minutes")
        name_embed.add_field(name="Attention its case sensitive", value="Just use copy paste")
        name_msg = await ctx.channel.send(embed=name_embed, delete_after=300)

        def same_channel_same_author_check(message):
            return message.author == ctx.message.author and message.channel == ctx.message.channel

        try:
            name_res = await self.client.wait_for('message', check=same_channel_same_author_check, timeout=60.0)
            category_name = name_res.content
            await name_res.delete()
            await name_msg.delete()
        except asyncio.TimeoutError:
            await name_msg.delete()
            return

        category = discord.utils.get(guild.categories, name=category_name)
        if category is None:
            await Notification.send_alert(ctx, header="Error 404", content="No category with this name found")
        else:
            for channel in category.channels:
                await channel.delete()


def setup(client):
    client.add_cog(Util(client))
