import discord
from discord.ext import commands
import logging
import json
import os

logger = logging.getLogger(__name__)

class Volunteers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Load volunteers and mentors from a JSON file.
        config_file = os.environ.get("VOLUNTEERS_CONFIG", "volunteers.json")
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                self.volunteers = config.get("volunteers", [])
                self.mentors = config.get("mentors", [])
            logger.info("Loaded volunteers and mentors from %s", config_file)
        except Exception as e:
            logger.error("Error loading config file (%s): %s", config_file, e)
            # If loading fails, fallback to empty lists (or you can choose to raise an error)
            self.volunteers = []
            self.mentors = []

    @commands.command(name="henrik_curious_about_volunteers", help="Show status for volunteers and mentors.")
    async def volunteers(self, ctx):
        logger.info("Volunteers command triggered by %s", ctx.author)
        guild = ctx.guild
        if guild is None:
            logger.warning("Command not run in a guild.")
            await ctx.send("This command can only be run in a server.")
            return

        volunteer_table = []
        mentor_table = []

        # Helper function: Try to find a member in the guild by username.
        # If full_match is True, we compare using "name#discriminator".
        def find_member(name, full_match=False):
            for member in guild.members:
                if full_match:
                    if f"{member.name}#{member.discriminator}" == name:
                        return member
                else:
                    if member.name == name:
                        return member
            return None

        async def process_list(usernames, full_match_for_mentor=False):
            table = []
            for username in usernames:
                logger.info("Processing username: %s", username)
                member = None
                if full_match_for_mentor and ("#" in username):
                    member = find_member(username, full_match=True)
                    if member:
                        logger.info("Found mentor member (full match): %s", username)
                    else:
                        logger.info("Mentor member not found (full match): %s", username)
                else:
                    member = find_member(username, full_match=False)
                    if member:
                        logger.info("Found member: %s", username)
                    else:
                        logger.info("Member not found in guild: %s", username)
                joined = "Yes" if member else "No"
                discord_id = str(member.id) if member else "N/A"
                signed_up = "No"
                try:
                    if member:
                        logger.info("Querying database for member with discord_id: %s", member.id)
                        row = await self.bot.db_pool.fetchrow(
                            "SELECT * FROM users WHERE discord_id = $1", str(member.id)
                        )
                        logger.info("Database row for member %s: %s", member.id, row)
                    else:
                        logger.info("Member not found in guild; falling back to username query for: %s", username)
                        row = await self.bot.db_pool.fetchrow(
                            "SELECT * FROM users WHERE discord_username = $1", username
                        )
                        logger.info("Database row for username %s: %s", username, row)
                except Exception as e:
                    logger.error("Error querying database for %s: %s", member.id if member else username, e)
                    row = None
                if row:
                    signed_up = "Yes"
                else:
                    signed_up = "No"
                table.append((username, discord_id, joined, signed_up))
            return table

        volunteer_table = await process_list(self.volunteers, full_match_for_mentor=False)
        mentor_table = await process_list(self.mentors, full_match_for_mentor=True)

        def create_table(title, rows):
            header = f"{title}\n"
            table_header = "| Discord Username         | Discord User ID       | Joined Server | Signed Up on DH |\n"
            table_divider = "|--------------------------|-----------------------|---------------|----------------|\n"
            table_rows = ""
            for r in rows:
                table_rows += f"| {r[0]:24} | {r[1]:21} | {r[2]:13} | {r[3]:14} |\n"
            return header + "```" + table_header + table_divider + table_rows + "```"

        volunteer_text = create_table("Volunteers", volunteer_table)
        mentor_text = create_table("Mentors", mentor_table)

        logger.info("Sending volunteer table")
        await ctx.send(volunteer_text)
        logger.info("Sending mentor table")
        await ctx.send(mentor_text)

    @commands.command(name="help_saurabh", help="Assign volunteer role to all volunteers and mentor role to all mentors from the config.")
    @commands.has_permissions(administrator=True)
    async def help_saurabh(self, ctx):
        logger.info("help_saurabh command triggered by %s", ctx.author)
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command can only be run in a server.")
            return

        try:
            volunteer_role_id = int(os.environ["VOLUNTEER_ROLE_ID"])
            mentor_role_id = int(os.environ["MENTOR_ROLE_ID"])
        except KeyError as e:
            await ctx.send(f"Missing environment variable: {e}")
            return

        volunteer_role = guild.get_role(volunteer_role_id)
        mentor_role = guild.get_role(mentor_role_id)

        if volunteer_role is None:
            await ctx.send("Volunteer role not found in this guild.")
            return
        if mentor_role is None:
            await ctx.send("Mentor role not found in this guild.")
            return

        # Helper function: find a member by username.
        def find_member(name, full_match=False):
            for member in guild.members:
                if full_match:
                    if f"{member.name}#{member.discriminator}" == name:
                        return member
                else:
                    if member.name == name:
                        return member
            return None

        assigned_volunteers = 0
        not_found_volunteers = []
        for username in self.volunteers:
            member = find_member(username, full_match=False)
            if member:
                try:
                    await member.add_roles(volunteer_role)
                    logger.info("Assigned volunteer role to %s", username)
                    assigned_volunteers += 1
                except Exception as e:
                    logger.error("Error assigning volunteer role to %s: %s", username, e)
            else:
                not_found_volunteers.append(username)

        assigned_mentors = 0
        not_found_mentors = []
        for username in self.mentors:
            # For mentors, use a full match if the username includes a '#'
            if "#" in username:
                member = find_member(username, full_match=True)
            else:
                member = find_member(username, full_match=False)
            if member:
                try:
                    await member.add_roles(mentor_role)
                    logger.info("Assigned mentor role to %s", username)
                    assigned_mentors += 1
                except Exception as e:
                    logger.error("Error assigning mentor role to %s: %s", username, e)
            else:
                not_found_mentors.append(username)

        response = f"Assigned volunteer role to {assigned_volunteers} volunteers and mentor role to {assigned_mentors} mentors.\n"
        if not_found_volunteers:
            response += f"Volunteers not found: {', '.join(not_found_volunteers)}\n"
        if not_found_mentors:
            response += f"Mentors not found: {', '.join(not_found_mentors)}\n"
        await ctx.send(response)


async def setup(bot):
    await bot.add_cog(Volunteers(bot))
