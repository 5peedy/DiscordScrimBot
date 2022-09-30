import asyncio

from discord.ext import commands
from utils import Notification
import discord

green = 0x11f711
red = 0xD10000
orange = 0xff8800
blue = 0x007BFD

mix_term = "We require following information to verify your account:\n1. Link your steam profile (visibility of pubg game time)\n2. Link your pubg.op.gg account\n3. Twire.gg link of recent tournaments (recent 1 year) that you played (name of round/group/team)\n4. Your server discord name must match with your pubg IGN\n\nWe will decline your request if:\n-Your discord account was recently created and/or shares no mutal competitive discord servers\n-Your steam account has a VAC ban (<1 year) and/or has very little pubg game time\n-Your pubg.op.gg link shows no ranked activity\n-You cant provide any recent tournament links"
def is_role_team(role):
    if role.color.value == 1177361:
        return True
    return False


class Util(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.group(name="clear", invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    async def clear(self, ctx):
        pass

    @commands.group(name="utils", alias="util", brief="Useful scripts", invoke_without_command=True)
    @commands.has_guild_permissions(administrator=True)
    async def utils(self, ctx):
        pass

    @commands.command(name="mixterms")
    @commands.has_guild_permissions(administrator=True)
    async def mix_terms(self, ctx):
        channel = ctx.message.channel

        await channel.send(mix_term)

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

    @utils.command(name="updateRoles")
    @commands.has_guild_permissions(administrator=True)
    async def update_roles(self, ctx):
        await ctx.message.delete()

        notification_embed = discord.Embed(title="Updating roles in progress", color=orange)
        notification_embed.add_field(name="Roles that are checked by command", value="Team, Captain, Tier, Coach")
        notification_message = await ctx.channel.send(embed=notification_embed)

        team_role_id = 580622910377558026
        roles_to_remove_ids = [
            1000071257905172490,  # Pro
            686981939298566196,  # Tier 1
            687256873552052268,  # Tier 2
            687256225724891152,  # Tier 3
            687257221112922128,  # Tier 4
            688134269775773723,  # Tier 5
            580622126709604389,  # Coach
            580622737995989012   # Cpt
        ]
        team_role = discord.utils.get(ctx.guild.roles, id=team_role_id)

        change_count = 0

        def member_in_team(member):
            for role in member.roles:
                if is_role_team(role):
                    return True
            return False

        def has_team_role(member):
            for role in member.roles:
                if role.id == team_role_id:
                    return True
            return False

        def list_roles_to_remove(member):
            role_list = []

            for role in member.roles:
                for role_remove_id in roles_to_remove_ids:
                    if role.id == role_remove_id:
                        role_list.append(role)

            return role_list

        for member in ctx.guild.members:
            if member_in_team(member):
                if not has_team_role(member):
                    await member.add_roles(team_role, reason="Update team roles", atomic=False)
                    print("Member [{}]: Team role given".format(member.name))
                    change_count += 1
            else:
                if has_team_role(member):
                    await member.remove_roles(team_role, reason="Update team roles", atomic=False)
                    print("Member [{}]: Team role removed".format(member.name))
                    change_count += 1

                roles_to_remove = list_roles_to_remove(member)
                for role_to_remove in roles_to_remove:
                    await member.remove_roles(role_to_remove, reason="Update team roles", atomic=False)
                    print("Member [{}]: {} role removed".format(member.name, role_to_remove.name))
                    change_count += 1

        print("Role changes: {}".format(change_count))

        await notification_message.delete()

        result_embed = discord.Embed(title="Result of update", color=green)
        result_embed.add_field(name="Changes", value="{}".format(change_count))
        result_message = await ctx.channel.send(embed=result_embed, delete_after=300)

    @utils.group(name="sort", invoke_without_command=True, brief="Sorting scripts")
    @commands.has_guild_permissions(administrator=True)
    async def sort(self):
        pass

    @sort.command(name="teams")
    @commands.has_guild_permissions(administrator=True)
    async def sort_teams(self, ctx):
        guild = ctx.guild

        teams = []
        other_roles = []

        for role in guild.roles:
            if is_role_team(role):
                teams.append(role)
            else:
                other_roles.append(role)

        teams = sorted(teams, key=lambda role: role.name)

        positions = dict.fromkeys()


def setup(client):
    client.add_cog(Util(client))
