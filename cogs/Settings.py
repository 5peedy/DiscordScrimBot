from discord.ext import commands

from utils import Checks
from utils import Notification


class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = self.client.db

    @commands.group(name="settings", invoke_without_command=True)
    async def setting_command(self, ctx):
        pass

    @setting_command.group(name="add", invoke_without_command=True)
    async def setting_add(self, ctx):
        pass

    @setting_command.group(name="remove", invoke_without_command=True)
    async def setting_remove(self, ctx):
        pass

    @setting_add.command(name="admin")
    @commands.check(Checks.role_mentioned)
    @commands.has_guild_permissions(administrator=True)
    async def setting_add_admin(self, ctx):
        print("Adding admin role to server:" + ctx.guild.name)

        new_admin_role = ctx.message.role_mentions[0]
        if self.db.is_admin_role(server_id=ctx.guild.id, role_id=new_admin_role.id):
            text = new_admin_role.mention + " is already admin on the server"
            print(text)
            await Notification.send_notification(ctx=ctx, header="Command denied", content=text)
        else:
            self.db.add_admin_role(role_id=new_admin_role.id, role_name=new_admin_role.name, server_id=ctx.guild.id)
            text = new_admin_role.mention + " has been added"
            print(text)
            await Notification.send_approve(ctx=ctx, header="Done", content=text)

    @setting_remove.command(name="admin")
    @commands.check(Checks.role_mentioned)
    @commands.has_guild_permissions(administrator=True)
    async def setting_remove_admin(self, ctx):
        print("Removing admin role from server:" + ctx.guild.name)

        role_to_delete = ctx.message.role_mentions[0]
        if self.db.is_admin_role(server_id=ctx.guild.id, role_id=role_to_delete.id):
            self.db.remove_admin_role(role_id=role_to_delete.id, server_id=ctx.guild.id)
            text = role_to_delete.mention + " has been removed"
            print(text)
            await Notification.send_approve(ctx=ctx, header="Done", content=text)
        else:
            text = role_to_delete.mention + " is not an admin"
            print(text)
            await Notification.send_notification(ctx=ctx, header="Command denied", content=text)


def setup(client):
    client.add_cog(Settings(client))
