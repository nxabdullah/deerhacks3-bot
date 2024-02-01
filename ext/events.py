from discord.ext import commands
import discord
import asyncio
import os
from datetime import datetime, timedelta

class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.selected_role_id = 1192983889807933490

    @commands.Cog.listener()
    async def on_member_update(self, before, after):

        if before.roles != after.roles:

            before_roles = list(map(lambda x: x.id, before.roles))
            after_roles = list(map(lambda x: x.id, after.roles))

            if self.selected_role_id not in before_roles and self.selected_role_id in after_roles:
                await after.send(embed=discord.Embed(
                    title="Congratulations! You have been accepted into DeerHacks. Please check your email for the full details on what to do next.",
                    color=discord.Colour.green(),
                    type="rich"
                ))

                await discord.utils.sleep_until(datetime.now() + timedelta(days=4))

                await after.send(embed=discord.Embed(
                    title="If you have already RSVP'd you may ignore this message",
                    description="This is a 24 hour reminder to RSVP for DeerHacks.",
                    color=discord.Colour.purple(),
                    type="rich"
                ))

                await discord.utils.sleep_until(datetime.now() + timedelta(days=1))

                await after.send(embed=discord.Embed(
                    title="If you have already RSVP'd you may ignore this message",
                    description="Your RSVP deadline has expired and you may no longer RSVP for DeerHacks.",
                    color=discord.Colour.dark_red(),
                    type="rich"
                ))

                return


            await after.send(embed=discord.Embed(
                title="Your roles were updated",
                color=discord.Colour.gold(),
                type="rich"
            ))


    @commands.Cog.listener()
    async def on_member_join(self, member):
        user = await self.bot.db.fetchrow(f"SELECT email FROM users WHERE discord_id = $1", str(member.id))

        if user:
            message = discord.Embed(
                title="Welcome to DeerHacks 2024!",
                description="Thank you for signing up! We have given you a role to reflect your dashboard status.",
                color=discord.Colour.green(),
                type="rich"
            )

            message.add_field(name="Registered Email", value=user['email'], inline=True)
            message.set_footer(
                text="If you believe the email provided is not yours, please contact an organizer immediately.")

            await member.send(embed=message)
            return

        desc = """Please sign up via https://deerhacks.ca/login to get a role.

                    • If you are unable to register using the link above, the registration period may be over. Please contact an organizer for more information.

                    • After you have signed in, please send the following command to me: dh.sync
                    """

        message = discord.Embed(
            title="Welcome to DeerHacks 2024!",
            description=desc,
            colour=discord.Colour.red(),
            type="rich"
        )

        message.set_footer(text="Please contact an organizer immediately for any questions or concerns.")
        await member.send(embed=message)




async def setup(bot):
    await bot.add_cog(Events(bot))