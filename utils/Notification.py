import discord


async def send_notification(ctx, header, content):
    notification = discord.Embed(title="Notification", color=0xD10000, footer="Message gets deleted in 5 seconds")
    notification.add_field(name=header, value=content)
    await ctx.message.channel.send(embed=notification, delete_after=5)


async def send_approve(ctx, header, content):
    notification = discord.Embed(title="Notification", color=0xED321, footer="Message gets deleted in 5 seconds")
    notification.add_field(name=header, value=content)
    await ctx.message.channel.send(embed=notification, delete_after=5)
