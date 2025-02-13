from discord.ext import tasks 
import os
import discord
from discord.ext import commands
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Attendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.announcement_msg_id = None
        
        announcement_msg_id = os.environ.get("ANNOUNCEMENT_MSG_ID")
        if announcement_msg_id:
            try:
                self.announcement_msg_id = int(announcement_msg_id)
                logger.debug(f"Loaded announcement message ID: {self.announcement_msg_id}")
            except ValueError:
                logger.error("ANNOUNCEMENT_MSG_ID is not a valid integer. Using None instead.")

        # Load role IDs from environment variables
        self.attending_role_id = int(os.environ.get("ATTENDING_ROLE_ID", "123456789012345678"))
        self.withdrawn_role_id = int(os.environ.get("WITHDRAWN_ROLE_ID", "987654321098765432"))
        self.accepted_role_id = int(os.environ.get("ACCEPTED_ROLE_ID", "111111111111111111"))
        
        # Store last reminder times for users
        self.last_reminder = {}
        
        # Start the reminder loop
        self.check_attendance_reminder.start()

    def cog_unload(self):
        self.check_attendance_reminder.cancel()

    @tasks.loop(hours=4)
    async def check_attendance_reminder(self):
        """Check for users who need attendance reminders every 4 hours."""
        if not self.announcement_msg_id:
            return

        for guild in self.bot.guilds:
            accepted_role = guild.get_role(self.accepted_role_id)
            attending_role = guild.get_role(self.attending_role_id)
            withdrawn_role = guild.get_role(self.withdrawn_role_id)

            if not all([accepted_role, attending_role, withdrawn_role]):
                logger.error(f"Could not find all required roles in guild {guild.name}")
                continue

            for member in accepted_role.members:
                # Skip if they already confirmed or withdrew
                if attending_role in member.roles or withdrawn_role in member.roles:
                    continue

                # Check if we should send a reminder (if 4 hours have passed since last reminder)

                current_time = datetime.now()
                last_reminded = self.last_reminder.get(member.id)
                
                # If no previous reminder or 4 hours have passed since last reminder
                if last_reminded is None or (current_time - last_reminded >= timedelta(hours=4)):
                    try:
                        await self.send_reminder(member)
                        self.last_reminder[member.id] = datetime.now()
                        logger.debug(f"Sent reminder to {member.display_name}")
                    except discord.Forbidden:
                        logger.error(f"Cannot send DM to {member.display_name}")
                    except Exception as e:
                        logger.error(f"Error sending reminder to {member.display_name}: {e}")

    async def send_reminder(self, member):
        """Send a reminder DM to a member."""
        embed = discord.Embed(
            title="DeerHacks Attendance Confirmation Reminder",
            description=(
                "Hello! This is a friendly reminder that you haven't confirmed your attendance "
                "for DeerHacks yet. Please respond to the attendance announcement in the server.\n\n"
                "**Important:** To maintain your spot, please confirm your attendance as soon as possible. "
                "Failure to respond may result in your spot being given to someone on the waitlist.\n\n"
                "If you can no longer attend, please let us know by selecting ❌ on the announcement. "
                "This helps us plan effectively and gives others a chance to participate."
            ),
            color=0xFF9900  # Orange color for urgency
        )
        await member.send(embed=embed)

    @check_attendance_reminder.before_loop
    async def before_reminder(self):
        """Wait until the bot is ready before starting the reminder loop."""
        await self.bot.wait_until_ready()

    @commands.command(name="announce", help="Make an attendance announcement")
    @commands.has_permissions(manage_messages=True)
    async def announce(self, ctx):
        """
        Sends an announcement embed with two reaction options:
          - ✅: Confirm attendance (adds the 'attending' role)
          - ❌: Withdraw attendance (adds the 'withdrawn' role)
        If an announcement is already active (message ID loaded), the command does nothing.
        """
        if self.announcement_msg_id:
            await ctx.send("An announcement is already active.")
            return

        embed = discord.Embed(
            title="Attendance Confirmation",
            description=(
                "Thank you for your interest in attending DeerHacks!\n\n"
                "To help us with finalizing our plans and ensuring we can accommodate everyone, "
                "please confirm your attendance by reacting with one of the options below:\n\n"
                "✅ - I will attend DeerHacks.\n"
                "❌ - I will not be able to attend.\n\n"
                "Your response helps us with logistics, including arranging accommodations, meals, and activities. "
                "If you have any questions, feel free to contact our team. Thank you!"
            ),
            color=0x00ff00
        )
        message = await ctx.send(embed=embed)
        self.announcement_msg_id = message.id

        # Add reactions
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        await ctx.send("Announcement sent and reactions added.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Process only reactions on the designated announcement message.
        if self.announcement_msg_id is None or payload.message_id != self.announcement_msg_id:
            return

        if payload.user_id == self.bot.user.id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        emoji = str(payload.emoji)
        if emoji == "✅":
            role = guild.get_role(self.attending_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Attendance confirmed")
                    logger.debug(f"Added attending role to {member.display_name}")
                except discord.Forbidden:
                    logger.error(f"Permission error adding role to {member.display_name}")
                except discord.HTTPException as e:
                    logger.error(f"HTTP error when adding role to {member.display_name}: {e}")
                    
        elif emoji == "❌":
            role = guild.get_role(self.withdrawn_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Attendance withdrawn")
                    logger.debug(f"Added withdrawn role to {member.display_name}")
                except discord.Forbidden:
                    logger.error(f"Permission error adding role to {member.display_name}")
                except discord.HTTPException as e:
                    logger.error(f"HTTP error when adding role to {member.display_name}: {e}")

        # Ensure only one reaction is active.
        try:
            channel = self.bot.get_channel(payload.channel_id)
            if channel is None:
                return
            message = await channel.fetch_message(payload.message_id)
        except Exception as e:
            logger.error(f"Error fetching message: {e}")
            return

        for reaction in message.reactions:
            if str(reaction.emoji) != emoji:
                users = [user async for user in reaction.users()]
                if any(user.id == payload.user_id for user in users):
                    try:
                        await message.remove_reaction(reaction.emoji, discord.Object(id=payload.user_id))
                        logger.debug(f"Removed conflicting reaction {reaction.emoji} from user {payload.user_id}")
                    except Exception as e:
                        logger.error(f"Error removing reaction: {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if self.announcement_msg_id is None or payload.message_id != self.announcement_msg_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        emoji = str(payload.emoji)
        if emoji == "✅":
            role = guild.get_role(self.attending_role_id)
            if role:
                try:
                    await member.remove_roles(role, reason="Attendance reaction removed (✅)")
                    logger.debug(f"Removed attending role from {member.display_name}")
                except discord.Forbidden:
                    logger.error(f"Permission error removing role from {member.display_name}")
                except discord.HTTPException as e:
                    logger.error(f"HTTP error when removing role from {member.display_name}: {e}")
        elif emoji == "❌":
            role = guild.get_role(self.withdrawn_role_id)
            if role:
                try:
                    await member.remove_roles(role, reason="Attendance reaction removed (❌)")
                    logger.debug(f"Removed withdrawn role from {member.display_name}")
                except discord.Forbidden:
                    logger.error(f"Permission error removing role from {member.display_name}")
                except discord.HTTPException as e:
                    logger.error(f"HTTP error when removing role from {member.display_name}: {e}")

async def setup(bot):
    await bot.add_cog(Attendance(bot))
