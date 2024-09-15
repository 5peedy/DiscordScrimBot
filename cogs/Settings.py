from discord.ext import commands

from utils import Checks
from utils import Notification


class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = self.client.db

    @commands.group(name="settings", invoke_without_command=True)
    @commands.has_any_role(740572327846346873, 983341516460290058)
    async def setting_command(self, ctx):
        pass

    @setting_command.group(name="admin", invoke_without_command=True)
    @commands.has_any_role(740572327846346873, 983341516460290058)
    async def setting_admin(self, ctx):
        pass

    @setting_admin.command(name="add")
    @commands.has_any_role(740572327846346873, 983341516460290058)
    @commands.check(Checks.role_mentioned)
    async def setting_add_admin(self, ctx):
        print("Adding admin role to server:" + ctx.guild.name)

        new_admin_role = ctx.message.role_mentions[0]
        if self.db.is_admin_role(server_id=ctx.guild.id, role_id=new_admin_role.id):
            text = new_admin_role.mention + " is already admin on the server"
            print(text)
            await Notification.send_alert(ctx=ctx, header="Command denied", content=text)
        else:
            self.db.add_admin_role(role_id=new_admin_role.id, role_name=new_admin_role.name, server_id=ctx.guild.id)
            text = new_admin_role.mention + " has been added"
            print(text)
            await Notification.send_approve(ctx=ctx, header="Done", content=text)

    @setting_admin.command(name="remove")
    @commands.check(Checks.role_mentioned)
    @commands.has_any_role(740572327846346873, 983341516460290058)
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
            await Notification.send_alert(ctx=ctx, header="Command denied", content=text)


def setup(client):
    client.add_cog(Settings(client))
