import asyncio
from discord.ext import commands
import discord

from cogs.scrim.ScrimDB import ScrimDB

from utils import Checks, Notification


def is_role_team(role):
    if role.color.value == 1177361:
        return True
    return False


def is_team_member(team, member):
    for member_role in member.roles:
        if member_role.id == team.id:
            return True
    return False


def is_member(role, member):
    if is_team_member(team=role, member=member):
        return True
    return False


class Scrim(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = ScrimDB(client.db)

    @commands.command(name="test")
    async def test(self, ctx, role: discord.Role):
        print(role.members)

    @commands.group(name="scrim", invoke_without_command=True)
    async def scrim(self, ctx):
        pass

    @scrim.command(name="init", alias="setup")
    async def init_scrim(self, ctx):

        await ctx.message.delete()
        server_id = ctx.message.guild.id

        """" Status embed"""
        status_embed = discord.Embed(title="Scrim Setup", color=0xff8800)
        status_embed.set_footer(text="Message gets deleted after 5 minutes")
        status_embed.add_field(name="Info", value="Follow steps below")
        status_msg = await ctx.channel.send(embed=status_embed)
        status_embed.clear_fields()

        async def status_add(name, value):
            status_embed.add_field(name=name, value=value)
            await status_msg.edit(embed=status_embed)

        """" Name of the scrims """
        embed = discord.Embed(title="Next step", color=0x007BFD, footer="Messages gets deleted after 60 seconds")
        embed.set_footer(text="Messages gets deleted after 60 seconds")
        embed.add_field(name="Name", value="Type in the name of the scrims")
        name_msg = await ctx.message.channel.send(embed=embed, delete_after=60)

        def same_channel_same_author_check(message):
            return message.author == ctx.message.author and message.channel == ctx.message.channel

        try:
            name_res = await self.client.wait_for('message', check=same_channel_same_author_check, timeout=60.0)
            name = name_res.content
            await status_add(name="Name", value=name)
            await name_res.delete()
            await name_msg.delete()
        except asyncio.TimeoutError:
            await status_msg.delete()
            return

        """ Mode selection"""
        embed.clear_fields()
        embed.add_field(name="Select mode", value="1️⃣: Tier sorted\n2️⃣: First come first serve")

        mode_msg = await ctx.message.channel.send(embed=embed, delete_after=60)

        await mode_msg.add_reaction('1️⃣')
        await mode_msg.add_reaction('2️⃣')

        def select_mode_check(reaction, user):
            reac_str = str(reaction.emoji)
            return user == ctx.message.author and reaction.message.id == mode_msg.id and \
                   (reac_str == "1️⃣" or reac_str == "2️⃣")

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=select_mode_check, timeout=60.0)
            reac_str = str(reaction.emoji)
            if reac_str == "1️⃣":
                mode = "Tier"
            elif reac_str == "2️⃣":
                mode = "FCFS"
            await status_add(name="Mode", value=mode)
            await mode_msg.delete()
        except asyncio.TimeoutError:
            await status_msg.delete()
            await mode_msg.delete()
            return

        """" Lobby count """
        embed.clear_fields()
        embed.add_field(name="Lobby count", value="How many lobbies do you want to host")
        lobby_count_msg = await ctx.message.channel.send(embed=embed, delete_after=60)

        try:
            lobby_count_res = await self.client.wait_for('message', check=Checks.is_numeric, timeout=60.0)
            lobby_count = int(lobby_count_res.content)
            await lobby_count_msg.delete()
            await lobby_count_res.delete()
            await status_add(name="Lobby count", value=str(lobby_count))
        except asyncio.TimeoutError:
            await status_msg.delete()
            await lobby_count_msg.delete()
            return

        """ Min teams"""
        embed.clear_fields()
        embed.add_field(name="Minimum teams", value="How many teams are needed for one lobby")
        min_teams_msg = await ctx.message.channel.send(embed=embed, delete_after=60)

        def min_teams_check(message):
            if same_channel_same_author_check(message):
                if Checks.is_numeric(message):
                    teams = int(message.content)
                    if 21 > teams > 1:
                        return True
            return False

        try:
            min_teams_res = await self.client.wait_for('message', check=min_teams_check, timeout=60.0)
            min_teams = int(min_teams_res.content)
            await min_teams_res.delete()
            await min_teams_msg.delete()
            await status_add(name="Min teams", value=str(min_teams))
        except asyncio.TimeoutError:
            await min_teams_msg.delete()
            await status_msg.delete()
            return

        """ Max teams"""
        embed.clear_fields()
        embed.add_field(name="Maximum teams", value="How many teams can fit in one lobby")
        max_teams_mes = await ctx.message.channel.send(embed=embed, delete_after=60)

        def max_teams_check(message):
            if same_channel_same_author_check(message):
                if Checks.is_numeric(message):
                    teams = int(message.content)
                    if 21 > teams >= min_teams:
                        return True
            return False

        try:
            max_teams_res = await self.client.wait_for('message', check=max_teams_check, timeout=60.0)
            max_teams = int(max_teams_res.content)
            await status_add(name="Max teams", value=str(max_teams))
            await max_teams_mes.delete()
            await max_teams_res.delete()
        except asyncio.TimeoutError:
            await status_msg.delete()

        guild = ctx.guild
        category = await guild.create_category(name=name_res.content)
        lobby_announce_channel = await guild.create_text_channel(name="📢│final-lobby", category=category)
        lobby_status_channel = await guild.create_text_channel(name="lobby-status", category=category)
        checkin_channel = await guild.create_text_channel(name="check-in", category=category)
        checkout_channel = await guild.create_text_channel(name="check-out", category=category)

        for lobby in range(1, lobby_count + 1):
            await guild.create_text_channel(name="👀│lobby-info-" + str(lobby), category=category)

        lootspots = []
        for lobby in range(1, lobby_count + 1):
            await guild.create_text_channel(name="💬│lobby-" + str(lobby), category=category)
            lootspot = await guild.create_text_channel(name="lootspot-" + str(lobby), category=category)
            lootspot_id = lootspot.id
            lootspots.append(lootspot_id)

        for x in lootspots:
            print(x)

        self.db.init_scrim(name=name, mode=mode, lobby_count=lobby_count, min_teams=min_teams, max_teams=max_teams,
                           checkin_channel_id=checkin_channel.id, checkout_channel_id=checkout_channel.id,
                           lobbystatus_channel_id=lobby_status_channel.id,
                           lobbyannounce_channel_id=lobby_announce_channel.id, server_id=server_id,
                           lootspots=lootspots)
        print("Scrims \"{}\" has been created successfully".format(name))

    @scrim.command(name="open")
    async def open_scrim(self, ctx, scrim_name):
        self.db.open_scrim(server_id=ctx.guild.id, scrim_name=scrim_name)

    def update(self, scrim_id):
        pass

    @commands.command()
    async def checkin(self, ctx):
        await ctx.message.delete()
        admin = self.client.db.is_admin(server_id=ctx.guild.id, member=ctx.message.author)

        if not self.db.is_checkin_channel(server_id=ctx.guild.id, channel_id=ctx.message.channel.id):
            await Notification.send_alert(ctx=ctx, header="No check in channel",
                                          content="You have to use a check in channel")
            return

        if len(ctx.message.role_mentions) != 0:
            team_tag = ctx.message.role_mentions[0]
        if len(ctx.message.mentions) != 0:
            member_tag = ctx.message.mentions[0]

        if team_tag is None and member_tag is None:
            await Notification.send_alert(ctx=ctx, header="No team or member tagged",
                                          content="Use:\n{}checkin <@your team>\nor\n{}checkin <@yourself>".format(
                                              self.client.prefix))
            return

        if team_tag is not None:
            if not is_role_team(role=team_tag):
                await Notification.send_alert(ctx=ctx, header="Role is no team", content="You have to tag a team role")
                return

            if not is_member(role=team_tag, member=ctx.message.author) and not admin:
                await Notification.send_alert(ctx=ctx, header="Command denied",
                                              content="You have no permission to check in this team")
                return

            if not self.db.is_scrims_open(server_id=ctx.guild.id, checkin=ctx.message.channel.id) and not admin:
                await Notification.send_alert(ctx=ctx, header="Check in not open",
                                              content="You can not check in right now")
                return

            for tier_role in self.db.get_tier_roles(server_id=ctx.guild.id):
                for role in team_tag.members[0].roles:
                    if tier_role[0] == role.id:
                        tier = tier_role[1]
            if tier is None:
                await Notification.send_alert(ctx=ctx, header="No tier found for {}".format(team_tag.mention),
                                              content="Contact an admin")
                return

            role_id = team_tag.id
            name = team_tag.name
            description = "{} checked in by {}".format(team_tag.mention, ctx.message.author.mention)
        else:
            if not member_tag == ctx.message.author or not admin:
                await Notification.send_alert(ctx=ctx, header="Command denied",
                                              content="You have no permission to check in this MIX")
                return

            name = member_tag.name + " MIX"
            role_id = member_tag.id
            tier = 0
            description = "{}, MIX checked in by {}".format(member_tag.mention, ctx.message.author.mention)
        scrim_id = self.db.get_scrim_id(server_id=ctx.guild.id, checkin_id=ctx.message.channel.id)

        if not self.db.add_team(role_id=role_id, name=name, tier=tier, scrim_id=scrim_id):
            await Notification.send_alert(ctx=ctx, header="Team is already checked in",
                                          content="You cant check in twice")
            return

        await Notification.send_approve(ctx=ctx, title="Check in", description=description, permanent=True)

        # update_scrim(scrim_id)

    @commands.command()
    async def checkout(self, ctx):
        await ctx.message.delete()

        admin = self.client.db.is_admin(server_id=ctx.guild.id, member=ctx.message.author)
        if not self.db.is_checkout_channel(server_id=ctx.guild.id, channel_id=ctx.message.channel.id):
            await Notification.send_alert(ctx=ctx, header="No check out channel",
                                          content="You have to use a check out channel")
            return

        if len(ctx.message.role_mentions) != 0:
            team_tag = ctx.message.role_mentions[0]
        if len(ctx.message.mentions) != 0:
            member_tag = ctx.message.mentions[0]
        if team_tag is None and member_tag is None:
            await Notification.send_alert(ctx=ctx, header="No team or member tagged",
                                          content="Use:\n{}checkout <@your team>\nor\n{}checkout <@yourself>".format(
                                              self.client.prefix))
            return

        if team_tag is not None:
            if not is_role_team(team_tag):
                await Notification.send_alert(ctx=ctx, header="No team tagged", content="You have to tag a team")
                return

            if not is_member(role=team_tag, member=ctx.message.author) and not admin:
                await Notification.send_alert(ctx=ctx, header="Command denied",
                                              content="You have no permission to check out this team")
                return
            role_id = team_tag.id
            description = "{} is checked out by {}".format(team_tag.mention, ctx.message.author.mention)
        else:
            if not member_tag == ctx.message.author or not admin:
                await Notification.send_alert(ctx=ctx, header="Command denied",
                                              content="You have no permission to check out this MIX")
                return
            role_id = member_tag.id
            description = "{}, MIX checked out by {}".format(member_tag.mention, ctx.message.author.mention)

        scrim_id = self.db.get_scrim_id(server_id=ctx.guild.id, checkout_id=ctx.message.channel.id)
        if not self.db.del_team(role_id=role_id, scrim_id=scrim_id):
            await Notification.send_alert(ctx=ctx, header="Team was not check in",
                                          content="You cant check out a team which wasn't checked in")
            return

        await Notification.send_approve(ctx=ctx, title="Check out", description=description, permanent=True)
        # update_scrim(scrim_id)


def setup(client):
    client.add_cog(Scrim(client))
