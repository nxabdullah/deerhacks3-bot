from discord.ext import commands
import discord
import asyncio
import os

class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:

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