import asyncio
from discord.ext import commands
import discord

from cogs.scrim.ScrimDB import ScrimDB

from utils import Checks, Notification, Dates_time

green = 0x11f711
red = 0xD10000
orange = 0xff8800
blue = 0x007BFD


def sort_teams(teams, mode):
    sorted_teams = []
    if mode == "Tier":
        for i in range(0, len(teams)):
            team = teams[0]
            for j in range(1, len(teams)):
                comparison = teams[j]
                if team['tier'] > comparison['tier'] != 0 or (team['tier'] == 0 and comparison['tier'] != 0):
                    team = comparison
            teams.remove(team)
            sorted_teams.append(team)
        return sorted_teams
    elif mode == "FCFS":
        return teams


def is_role_team(role):
    if role.color.value == 1177361:
        return True
    return False


def is_team_member(team, member):
    for member_role in member.roles:
        if member_role.id == team.id:
            return True
    return False


class Scrim(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = ScrimDB(client.db)

    def get_lobbies(self, reserve, scrim_id=None, server_id=None, scrim_name=None):
        lobbies = []

        if scrim_id is None:
            scrim_id = self.db.get_scrim_id(server_id=server_id, scrim_name=scrim_name)

        if server_id is None:
            server_id = self.db.get_server_from_scrim(scrim_id=scrim_id)

        if scrim_name is None:
            scrim_name = self.db.get_scrim_name(scrim_id=scrim_id)

        mode = self.db.get_scrim_mode(scrim_id=scrim_id)
        teams = sort_teams(teams=self.db.get_scrim_teams(scrim_id=scrim_id), mode=mode)
        tiers = self.db.get_tier_roles(server_id=server_id)
        lobby_params = self.db.get_scrim_lobby_params(scrim_id=scrim_id)
        lobby_count = lobby_params['lobby_count']
        min_teams = lobby_params['min_teams']
        max_teams = lobby_params['max_teams']

        pos_lobby_count = int(len(teams) / min_teams)
        if pos_lobby_count < lobby_count:
            lobby_count = pos_lobby_count

        teams_left = len(teams) - min_teams * lobby_count
        free_seats = (max_teams - min_teams) * lobby_count

        if teams_left > free_seats:
            teams_left = free_seats

        if lobby_count != 0:
            balance_team_count = int(teams_left / lobby_count) + min_teams
            unbalanced_team_addition = teams_left % lobby_count

        if scrim_name is None:
            scrim_name = self.db.get_scrim_name(scrim_id=scrim_id)

        for lobby in range(1, lobby_count + 1):
            lobby_status_embed = discord.Embed(title=scrim_name + str(), color=green)
            text = ""
            addition = 0
            if lobby <= unbalanced_team_addition:
                addition = 1
            for slot in range(3, balance_team_count + 3 + addition):
                team = teams.pop(0)
                if team['tier'] == 0:
                    tier_text = "MIX"
                else:
                    tier_text = tiers[team['tier'] - 1]['mention']
                text += "**Slot {}:** {}, {}\n".format(slot, team['mention'], tier_text)
            lobby_status_embed.add_field(name="Lobby {}".format(lobby), value=text)
            lobbies.append(lobby_status_embed)

        if reserve:
            if len(teams) != 0:
                reserve_status_embed = discord.Embed(title=scrim_name, color=0x000000)
                text = ""
                for seat in range(1, len(teams) + 1):
                    team = teams.pop(0)
                    if team['tier'] == 0:
                        tier_text = "MIX"
                    else:
                        tier_text = tiers[team['tier'] - 1]['mention']
                    text += "**Seat {}:** {}, {}\n".format(seat, team['mention'], tier_text)
                reserve_status_embed.add_field(name="Reserve", value=text)
                lobbies.append(reserve_status_embed)

        return lobbies

    async def select_scrim(self, server_id, ctx):
        scrims = self.db.get_scrims(server_id)
        num_to_symbol = {
            1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣', 6: '6️⃣',
            7: '7️⃣', 8: '8️⃣', 9: '9️⃣'
        }
        description = ""
        for i in range(1, len(scrims) + 1):
            description += "{} {}\n".format(num_to_symbol[i], scrims[i - 1]['name'])

        embed = discord.Embed(title="Select Scrims", description=description)
        select_scrim_mes = await ctx.message.channel.send(embed=embed)

        for i in range(1, len(scrims) + 1):
            await select_scrim_mes.add_reaction(num_to_symbol[i])

        def scrim_select_check(reaction, user):
            if user != ctx.message.author:
                return False

            react_str = str(reaction.emoji)
            if react_str in num_to_symbol.values():
                return True

            return False

        try:
            reaction, user = await self.client.wait_for('reaction_add', timeout=30.0, check=scrim_select_check)
        except asyncio.TimeoutError:
            await select_scrim_mes.delete()
            return

        await select_scrim_mes.delete()

        for number, symbol in num_to_symbol.items():
            if symbol == reaction.emoji:
                return scrims[number - 1]

    async def update_lobby(self, server_id=None, scrim_id=None, scrim_name=None):
        if scrim_id is None:
            scrim_id = self.db.get_scrim_id(server_id=server_id, scrim_name=scrim_name)

        if server_id is None:
            server_id = self.db.get_server_from_scrim(scrim_id=scrim_id)

        if scrim_name is None:
            scrim_name = self.db.get_scrim_name(scrim_id=scrim_id)

        lobbies = self.get_lobbies(reserve=True, scrim_id=scrim_id, scrim_name=scrim_name, server_id=server_id)

        channels = self.db.get_scrim_channels(scrim_id=scrim_id)
        guild = self.client.get_guild(id=server_id)
        status_channel = guild.get_channel(channels['status'])

        await status_channel.purge(limit=50)
        if len(lobbies) == 0:
            no_teams_embed = discord.Embed(title=scrim_name, description="No teams checked in yet", color=blue)
            await status_channel.send(embed=no_teams_embed)
        else:
            for lobby_embed in lobbies:
                await status_channel.send(embed=lobby_embed)

    async def announce_lobby(self, scrim_id, guild, hosts, lobbies):
        announce_channel = guild.get_channel(self.db.get_scrim_channels(scrim_id=scrim_id)['announce'])

        if len(lobbies) == 0:
            embed = discord.Embed(title="Scrims canceled", description="Too less teams checked in", color=red)
            await announce_channel.send(embed=embed)

        host_text = ""
        for i in range(1, len(hosts) + 1):
            host_text += "Lobby {} host: {}\n".format(str(i), hosts[i - 1])
        text = "**FINAL LOBBY**\n{}Game up 18:50, Game start 19:00 CEST\n@here".format(host_text)

        await announce_channel.send(content=text)

        for lobby_embed in lobbies:
            await announce_channel.send(embed=lobby_embed)

    @commands.command(name="test")
    async def test(self, ctx):
        for role in ctx.message.role_mentions:
            print(role.mention)

    @commands.group(name="scrim", alias="scrims", invoke_without_command=True, brief="Commands for scrim handling")
    @commands.has_guild_permissions(administrator=True)
    async def scrim(self, ctx):
        pass

    @scrim.command(name="init", alias="setup", brief="Create new scrims")
    @commands.has_guild_permissions(administrator=True)
    async def init_scrim(self, ctx):
        await ctx.message.delete()

        server_id = ctx.message.guild.id

        """" Status embed """
        status_embed = discord.Embed(title="Scrim Setup", color=orange)
        status_embed.set_footer(text="Message gets deleted after 5 minutes")
        status_embed.add_field(name="Info", value="Follow steps below")
        status_msg = await ctx.channel.send(embed=status_embed, delete_after=300)
        status_embed.clear_fields()

        async def status_add(name, value):
            status_embed.add_field(name=name, value=value)
            await status_msg.edit(embed=status_embed)

        """" Name of the scrims """
        embed = discord.Embed(title="Next step", color=blue, footer="Messages gets deleted after 60 seconds")
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
        lobby_status_channel = await guild.create_text_channel(name="📢│lobby-status", category=category)
        checkin_channel = await guild.create_text_channel(name="✅│check-in", category=category)
        checkout_channel = await guild.create_text_channel(name="❌│check-out", category=category)

        for lobby in range(1, lobby_count + 1):
            await guild.create_text_channel(name="👀│lobby-info-" + str(lobby), category=category)

        lootspots = []
        for lobby in range(1, lobby_count + 1):
            await guild.create_text_channel(name="💬│lobby-" + str(lobby), category=category)
            lootspot = await guild.create_text_channel(name="💬│lootspot-" + str(lobby), category=category)
            lootspot_id = lootspot.id
            lootspots.append(lootspot_id)

        self.db.init_scrim(name=name, mode=mode, lobby_count=lobby_count, min_teams=min_teams, max_teams=max_teams,
                           checkin_channel_id=checkin_channel.id, checkout_channel_id=checkout_channel.id,
                           lobbystatus_channel_id=lobby_status_channel.id,
                           lobbyannounce_channel_id=lobby_announce_channel.id, server_id=server_id,
                           lootspots=lootspots)
        print("Scrims \"{}\" has been created successfully".format(name))

    @scrim.command(name="open", brief="Open scrim", description="Open a scrim\n\nSteps:\n1. Select scrims")
    @commands.has_guild_permissions(administrator=True)
    async def open_scrim(self, ctx):
        await ctx.message.delete()
        selected_scrim = await self.select_scrim(server_id=ctx.guild.id, ctx=ctx)
        scrim_name = selected_scrim['name']
        scrim_id = selected_scrim['id']

        self.db.open_scrim(server_id=ctx.guild.id, scrim_name=scrim_name)

        scrim_channel_ids = self.db.get_scrim_channels(scrim_id=scrim_id)
        checkin_channel = ctx.guild.get_channel(scrim_channel_ids['checkin'])
        checkout_channel = ctx.guild.get_channel(scrim_channel_ids['checkout'])

    @scrim.command(name="close", brief="Close scrim", description="Close a scrim\n\nSteps:\n1. Select scrims")
    @commands.has_guild_permissions(administrator=True)
    async def close_scrim(self, ctx):
        await ctx.message.delete()
        selected_scrim = await self.select_scrim(server_id=ctx.guild.id, ctx=ctx)
        scrim_name = selected_scrim['name']
        scrim_id = selected_scrim['id']

        self.db.close_scrim(server_id=ctx.guild.id, scrim_name=scrim_name)

        scrim_channel_ids = self.db.get_scrim_channels(scrim_id=scrim_id)
        checkin_channel = ctx.guild.get_channel(scrim_channel_ids['checkin'])
        checkout_channel = ctx.guild.get_channel(scrim_channel_ids['checkout'])

        await checkin_channel.send(content="**CLOSED**")
        await checkout_channel.send(content="**CLOSED**")

    @scrim.command(name="reset", brief="Reset teams and open next scrim sessions", description="Reset teams and open "
                                                                    "next scrim sessions\n\nSteps:\n1. Select scrims"
                                                                    "\n2. Select day")
    @commands.has_guild_permissions(administrator=True)
    async def reset_scrim(self, ctx):
        await ctx.message.delete()
        selected_scrim = await self.select_scrim(server_id=ctx.guild.id, ctx=ctx)
        scrim_id = selected_scrim['id']
        scrim_name = selected_scrim['name']

        self.db.reset_scrim(scrim_id=scrim_id)

        num_to_symbol = {
            1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣', 6: '6️⃣',
            7: '7️⃣', 8: '8️⃣', 9: '9️⃣'
        }

        description = "{} Today\n{} Tomorrow".format(num_to_symbol[1], num_to_symbol[2])
        embed = discord.Embed(title="Day select", description=description)
        day_select_msg = await ctx.message.channel.send(embed=embed)
        for i in range(1, 3):
            await day_select_msg.add_reaction(num_to_symbol[i])

        def day_select_check(reaction, user):
            if user != ctx.message.author:
                return False

            if reaction.emoji != num_to_symbol[1] and reaction.emoji != num_to_symbol[2]:
                return False

            return True

        try:
            reaction, user = await self.client.wait_for('reaction_add', check=day_select_check, timeout=60.0)
        except asyncio.TimeoutError:
            await day_select_msg.delete()
            return

        await day_select_msg.delete()

        if reaction.emoji == num_to_symbol[1]:
            scrim_day = Dates_time.get_today()
        elif reaction.emoji == num_to_symbol[2]:
            scrim_day = Dates_time.get_tomorrow()

        checkout_info = discord.Embed(title="Check out for {}".format(scrim_day), color=blue)
        checkout_info.add_field(name="Checkout Team",
                                value="Use \"" + self.client.prefix + "checkout @<your team>\" to checkout your team",
                                inline=False)
        checkout_info.add_field(name="Checkout MIX",
                                value="Use \"" + self.client.prefix + "checkout @<yourself>\" to checkout your MIX",
                                inline=False)

        checkin_info = discord.Embed(title="Check in for {}".format(scrim_day), color=blue)
        checkin_info.add_field(name="Checkin Team",
                               value="Use \"" + self.client.prefix + "checkin @<your team>\" to checkin your team",
                               inline=False)
        checkin_info.add_field(name="Checkin MIX",
                               value="Use \"" + self.client.prefix + "checkin @<yourself>\" to checkin your MIX",
                               inline=False)

        scrim_channels = self.db.get_scrim_channels(scrim_id=scrim_id)
        checkin_channel = ctx.guild.get_channel(scrim_channels['checkin'])
        checkout_channel = ctx.guild.get_channel(scrim_channels['checkout'])
        await checkout_channel.purge(limit=100)
        await checkout_channel.send(embed=checkout_info)
        await checkin_channel.purge(limit=100)
        await checkin_channel.send(embed=checkin_info)
        await self.update_lobby(scrim_id=scrim_id)
        await Notification.send_approve(ctx=ctx, header="Scim reset", content="{} has been reset".format(scrim_name))

    @scrim.command(name="clear", brief="Use \"!scrim clear lootspot\" for now")
    @commands.has_guild_permissions(administrator=True)
    async def clear(self, ctx, target):
        await ctx.message.delete()

        selected_scrim = await self.select_scrim(server_id=ctx.guild.id, ctx=ctx)
        scrim_id = selected_scrim['id']
        if target == "lootspot":
            lootspot_channels_ids = self.db.get_lootspot_channel_ids(scrim_id=scrim_id)

            num_to_symbol = {
                1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣', 6: '6️⃣',
                7: '7️⃣', 8: '8️⃣', 9: '9️⃣'
            }

            description = "{} Today\n{} Tomorrow".format(num_to_symbol[1], num_to_symbol[2])
            embed = discord.Embed(title="Day select", description=description)
            day_select_msg = await ctx.message.channel.send(embed=embed)
            for i in range(1, 3):
                await day_select_msg.add_reaction(num_to_symbol[i])

            def day_select_check(reaction, user):
                if user != ctx.message.author:
                    return False

                if reaction.emoji != num_to_symbol[1] and reaction.emoji != num_to_symbol[2]:
                    return False

                return True

            try:
                reaction, user = await self.client.wait_for('reaction_add', check=day_select_check, timeout=60.0)
            except asyncio.TimeoutError:
                await day_select_msg.delete()
                return

            await day_select_msg.delete()

            if reaction.emoji == num_to_symbol[1]:
                scrim_day = Dates_time.get_today()
            elif reaction.emoji == num_to_symbol[2]:
                scrim_day = Dates_time.get_tomorrow()

            lootspot_text = "LOOTSPOT CHANNEL IS OPEN FOR {}\nTIER 1 IS PROTECTED AND YOU CANT HOTDROP ON TIER1 TEAM\nYOU CAN DROP ON SAME SPOT IF THE OTHER TEAM ISNT TIER 1\n**You have to write lootspot until 18:50**\n\n\nPlease use this template:\n\nTeam&Tier:\nErangel:\nMiramar:\n\n(You can still change your Lootspots after 18:50 DO NOT EDIT OLD MESSAGE! Send a new message)\n(You will get a strike for typing you will react drop)\n(You will get a strike for dropping on tier 1 team)\n(You will get a strike for hotdropping another team if your main spot is reachable)\n(You will get a strike for not dropping on your 1st written lootspot if it is in reach) ".format(
                scrim_day)

            lootspot_channels = []
            for loot_channel_id in lootspot_channels_ids:
                lootspot_channels.append(ctx.guild.get_channel(loot_channel_id))

            for loot_channel in set(lootspot_channels):
                await loot_channel.purge(limit=100)
                await loot_channel.send(content=lootspot_text)

    @scrim.command(name="announce", brief="Announce scrim lobbies", description="Announce scrim lobbies\n\nSteps:\n"
                                                                                "1. Select scrims\n"
                                                                                "2. Tag scrim hosts")
    @commands.has_guild_permissions(administrator=True)
    async def announce_scrim(self, ctx):
        await ctx.message.delete()

        selected_scrim = await self.select_scrim(ctx=ctx, server_id=ctx.guild.id)
        scrim_id = selected_scrim['id']

        lobbies = self.get_lobbies(reserve=False, scrim_id=scrim_id)
        lobby_count = len(lobbies)
        hosts = []
        if lobby_count != 0:
            host_embed = discord.Embed(title="Enter host(s)", description="Please tag {} host(s)".format(lobby_count))
            host_msg = await ctx.message.channel.send(embed=host_embed)

            def host_tag_check(message):
                tag_count = len(message.mentions)
                if tag_count == lobby_count:
                    return True
                return False

            try:
                host_response = await self.client.wait_for('message', timeout=20.0, check=host_tag_check)
            except asyncio.TimeoutError:
                await host_msg.delete()
                return

            await host_msg.delete()
            await host_response.delete()

            for user in host_response.mentions:
                hosts.append(user.mention)

        await self.announce_lobby(scrim_id=scrim_id, hosts=hosts, guild=ctx.guild, lobbies=lobbies)

    @scrim.command(name="update", brief="For dev only")
    @commands.has_guild_permissions(administrator=True)
    async def update_scrim(self, ctx):
        await ctx.message.delete()

        scrim_name = ctx.message.content[14:]
        scrim_id = self.db.get_scrim_id(server_id=ctx.guild.id, scrim_name=scrim_name)
        if scrim_id is None:
            await Notification.send_alert(ctx=ctx, header="Scrim not found", content="Couldn't find a scrim with "
                                                                                     "that name")
            return
        await self.update_lobby(scrim_id=scrim_id)

    @commands.command(name="checkin", brief="Check in a team or Mix")
    async def checkin(self, ctx):
        await ctx.message.delete()
        admin = self.client.db.is_admin(server_id=ctx.guild.id, member=ctx.message.author)

        if not self.db.is_checkin_channel(server_id=ctx.guild.id, channel_id=ctx.message.channel.id):
            await Notification.send_alert(ctx=ctx, header="No check in channel",
                                          content="You have to use a check in channel")
            return

        team_tag = None
        member_tag = None
        tier = None
        if len(ctx.message.role_mentions) != 0:
            team_tag = ctx.message.role_mentions[0]
        if len(ctx.message.mentions) != 0:
            member_tag = ctx.message.mentions[0]

        if team_tag is None and member_tag is None:
            await Notification.send_alert(ctx=ctx, header="No team or member tagged",
                                          content="Use:\n{}checkin <@your team>\nor\n{}checkin <@yourself>"
                                                  "".format(self.client.prefix, self.client.prefix))
            return

        if not self.db.is_scrims_open(server_id=ctx.guild.id, checkin=ctx.message.channel.id) and not admin:
            await Notification.send_alert(ctx=ctx, header="Scrims are not open",
                                          content="You can not check in right now")
            return

        if team_tag is not None:
            if not is_role_team(role=team_tag):
                await Notification.send_alert(ctx=ctx, header="Role is no team", content="You have to tag a team role")
                return

            if not is_team_member(team=team_tag, member=ctx.message.author) and not admin:
                await Notification.send_alert(ctx=ctx, header="Command denied",
                                              content="You have no permission to check in this team")
                return

            for tier_role in self.db.get_tier_roles(server_id=ctx.guild.id):
                for role in team_tag.members[0].roles:
                    if tier_role['id'] == role.id:
                        tier = tier_role['tier']
            if tier is None:
                await Notification.send_alert(ctx=ctx, header="No tier found for {}".format(team_tag.mention),
                                              content="Contact an admin")
                return

            role_id = team_tag.id
            name = team_tag.name
            mention = team_tag.mention
            description = "{} *checked in by* {}".format(team_tag.mention, ctx.message.author.mention)
        else:
            if not member_tag == ctx.message.author and not admin:
                await Notification.send_alert(ctx=ctx, header="Command denied",
                                              content="You have no permission to check in this MIX")
                return

            name = member_tag.name + " MIX"
            role_id = member_tag.id
            tier = 0
            mention = member_tag.mention
            description = "{}, MIX *checked in by* {}".format(member_tag.mention, ctx.message.author.mention)
        scrim_id = self.db.get_scrim_id(server_id=ctx.guild.id, checkin_id=ctx.message.channel.id)

        if not self.db.add_team(role_id=role_id, name=name, tier=tier, mention=mention, scrim_id=scrim_id):
            await Notification.send_alert(ctx=ctx, header="Team is already checked in",
                                          content="You cant check in twice")
            return

        await Notification.send_approve(ctx=ctx, title="Check in", description=description, permanent=True)

        await self.update_lobby(scrim_id=scrim_id)

    @commands.command(name="checkout", brief="Check out a team or Mix")
    async def checkout(self, ctx):
        await ctx.message.delete()

        scrim_id = self.db.get_scrim_id(server_id=ctx.guild.id, checkout_id=ctx.message.channel.id)

        admin = self.client.db.is_admin(server_id=ctx.guild.id, member=ctx.message.author)
        if not self.db.is_checkout_channel(server_id=ctx.guild.id, channel_id=ctx.message.channel.id):
            await Notification.send_alert(ctx=ctx, header="No check out channel",
                                          content="You have to use a check out channel")
            return

        team_tag = None
        member_tag = None
        if len(ctx.message.role_mentions) != 0:
            team_tag = ctx.message.role_mentions[0]
        if len(ctx.message.mentions) != 0:
            member_tag = ctx.message.mentions[0]
        if team_tag is None and member_tag is None:
            await Notification.send_alert(ctx=ctx, header="No team or member tagged",
                                          content="Use:\n{}checkout <@your team>\nor\n{}checkout <@yourself>".format(
                                              self.client.prefix))
            return

        if not self.db.is_scrims_open(server_id=ctx.guild.id, checkout=ctx.message.channel.id) and not admin:
            await Notification.send_alert(ctx=ctx, header="Scrims are not open",
                                          content="You can not check out right now")
            return

        if team_tag is not None:
            if not is_role_team(team_tag):
                await Notification.send_alert(ctx=ctx, header="No team tagged", content="You have to tag a team")
                return

            if not is_team_member(team=team_tag, member=ctx.message.author) and not admin:
                await Notification.send_alert(ctx=ctx, header="Command denied",
                                              content="You have no permission to check out this team")
                return
            role_id = team_tag.id
            description = "{} *checked out by* {}".format(team_tag.mention, ctx.message.author.mention)
        else:
            if not member_tag == ctx.message.author and not admin:
                await Notification.send_alert(ctx=ctx, header="Command denied",
                                              content="You have no permission to check out this MIX")
                return
            role_id = member_tag.id
            description = "{}, MIX *checked out by* {}".format(member_tag.mention, ctx.message.author.mention)

        if not self.db.del_team(role_id=role_id, scrim_id=scrim_id):
            await Notification.send_alert(ctx=ctx, header="Team was not check in",
                                          content="You cant check out a team which wasn't checked in")
            return

        await Notification.send_approve(ctx=ctx, title="Check out", description=description, permanent=True)
        await self.update_lobby(scrim_id=scrim_id)

    @commands.group(name="team", brief="Commands for team management")
    @commands.has_guild_permissions(administrator=True)
    async def team(self, ctx):
        pass

    @team.command(name="add", brief="Add a team")
    @commands.has_guild_permissions(administrator=True)
    async def team_add(self, ctx):
        await ctx.message.delete()
        channel = ctx.message.channel

        add_team_embed = discord.Embed(title="Add Team", color=0xff8800)
        add_team_embed.set_footer(text="Message gets deleted after 5 minutes")
        add_team_status_msg = await channel.send(embed=add_team_embed, delete_after=300)

        embed = discord.Embed(title="Next Step", color=0x007BFD)

        """ Team name """
        embed.add_field(name="Team name", value="Enter team name")
        embed.set_footer(text="Message gets deleted after 1 minute")
        team_name_msg = await channel.send(embed=embed, delete_after=60)

        def same_channel_same_author_check(message):
            return message.author == ctx.message.author and message.channel == ctx.message.channel

        try:
            team_name_res = await self.client.wait_for('message', check=same_channel_same_author_check, timeout=60.0)
        except asyncio.TimeoutError:
            await add_team_status_msg.delete()
            return

        await team_name_res.delete()
        await team_name_msg.delete()

        team_name = team_name_res.content
        add_team_embed.add_field(name="Team name", value=team_name)
        await add_team_status_msg.edit(embed=add_team_embed)

        """ Team members """
        embed.clear_fields()
        embed.add_field(name="Members", value="Tag team members (Cpt,Pl2,Pl3,Pl4)")
        tag_members_msg = await channel.send(embed=embed)

        def team_check(message):
            if not same_channel_same_author_check(message):
                return False
            if 3 > len(message.mentions) > 7:
                return False
            return True

        try:
            tag_members_res = await self.client.wait_for('message', check=team_check, timeout=60.0)
        except asyncio.TimeoutError:
            await add_team_status_msg.delete()
            await tag_members_msg.delete()
            return

        await tag_members_msg.delete()
        await tag_members_res.delete()
        team_members = tag_members_res.mentions

        """ Tier """
        embed.clear_fields()
        embed.add_field(name="Tier", value="Tag a tier role")
        tier_msg = await channel.send(embed=embed)

        def tier_check(message):
            if not same_channel_same_author_check(message):
                return False
            if len(message.role_mentions) != 1:
                return False
            if not self.db.is_tier_role(server_id=ctx.guild.id, role_id=message.role_mentions[0].id):
                return False
            return True

        try:
            tier_res = await self.client.wait_for('message', check=tier_check, timeout=60.0)
        except asyncio.TimeoutError:
            await tier_msg.delete()
            await add_team_status_msg.delete()
            return

        await tier_msg.delete()
        await tier_res.delete()
        tier_role = tier_res.role_mentions[0]

        team_role = await ctx.guild.create_role(name=team_name, mentionable=True, color=discord.Color(green))
        for member in team_members:
            await member.add_roles(tier_role, team_role, reason="Team creation", atomic=False)


def setup(client):
    client.add_cog(Scrim(client))
