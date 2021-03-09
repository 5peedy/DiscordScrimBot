from discord.ext import commands


class Settings(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = client.db

    @commands.group(name="settings", invoke_without_command=True)
    async def setting_command(self, ctx):
        await ctx.channel.send("Test")

    @setting_command.group(name="add", invoke_without_command=True)
    async def setting_add(self, ctx):
        pass

    @setting_add.command(name="admin")
    async def setting_add_admin(self, ctx):
        print("Adding admin role to server:" + ctx.guild.name)

        new_admin_role = ctx.message.role_mentions[0]
        if new_admin_role is None:
            print("No role mentioned")
        elif db.is_admin_role(new_admin_role.id, ctx.guild.id):
            print("Role is already admin on the server")
        else:
            db.add_admin_role(role_id=new_admin_role.id, role_name=new_admin_role.name, server_id=ctx.guild.id)


def setup(client):
    client.add_cog(Settings(client))
