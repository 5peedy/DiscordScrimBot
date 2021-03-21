import discord


async def send_alert(ctx, header=None, content=None, title="Notification", description=None, permanent=False):
    if description is None:
        notification = discord.Embed(title=title, color=0xD10000)
    else:
        notification = discord.Embed(title=title, description=description, color=0xD10000)
    if not (header is None or content is None):
        notification.add_field(name=header, value=content)
    if not permanent:
        notification.set_footer(text="Message gets deleted in 10 seconds")
        await ctx.message.channel.send(embed=notification, delete_after=10)
    else:
        await ctx.message.channel.send(embed=notification)


async def send_approve(ctx, header=None, content=None, title="Notification", description=None, permanent=False):

    if description is None:
        notification = discord.Embed(title=title, color=0xED321)
    else:
        notification = discord.Embed(title=title, description=description, color=0xED321)
    if not (header is None or content is None):
        notification.add_field(name=header, value=content)
    if not permanent:
        notification.set_footer(text="Message gets deleted in 10 seconds")
        await ctx.message.channel.send(embed=notification, delete_after=10)
    else:
        await ctx.message.channel.send(embed=notification)
