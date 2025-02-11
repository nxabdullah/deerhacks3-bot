import discord
from discord.ext import commands
import logging
import os

logger = logging.getLogger(__name__)

class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def synchronize(self, member) -> str:
        roles = {
            "pending": int(os.environ["PENDING_ROLE_ID"]),
            "registering": int(os.environ["REGISTERING_ROLE_ID"]),
            "applied": int(os.environ["APPLIED_ROLE_ID"]),
            "selected": int(os.environ["SELECTED_ROLE_ID"]),
            "accepted": int(os.environ["ACCEPTED_ROLE_ID"]),
            "attended": int(os.environ["ATTENDED_ROLE_ID"]),
            "volunteer": int(os.environ["VOLUNTEER_ROLE_ID"])
        }

        # Make sure your bot instance has an attribute `db_pool`
        async with self.bot.db_pool.acquire() as connection:
            user = await connection.fetchrow(
                "SELECT status FROM users WHERE discord_id = $1", str(member.id)
            )

        if user:
            logger.debug(f"Fetched user status from DB: {user}")
        else:
            logger.warning(f"No user found in DB for {member.id}")
            return "Failed to synchronize: User not found in DB"

        if user['status'] in roles:
            role_id = roles[user['status']]
            role = member.guild.get_role(role_id)

            if role:
                logger.debug(f"Assigning role {role.name} ({role.id}) to {member.name} ({member.id})")
                try:
                    await member.edit(roles=[role])
                    logger.debug(f"Successfully assigned role {role.name} to {member.name}")
                    return f"Successfully synchronized role {role.name} for {member.name}"
                except discord.Forbidden:
                    logger.error(f"Permission issue: Cannot edit roles for {member.name}")
                    return "Failed to synchronize due to insufficient permissions"
                except discord.HTTPException as e:
                    logger.error(f"HTTPException: {e}")
                    return "Failed to synchronize due to an API error"
            else:
                logger.warning(f"Role {role_id} not found in guild")
                return "Failed to synchronize due to missing role"

        return "Failed to synchronize: Unknown issue"

    @commands.dm_only()
    @commands.cooldown(2, 7200, commands.BucketType.user)
    @commands.command(name="sync", description="Sync dashboard status with your discord role", aliases=['s'])
    async def sync(self, ctx):
        if ctx.author.mutual_guilds:
            guild = ctx.author.mutual_guilds[0]
            member = guild.get_member(ctx.author.id)
            message = await self.synchronize(member)
            await ctx.send(message)

    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.command(name="adminsync", description="Sync another user's dashboard status", aliases=['as'])
    async def adminsync(self, ctx, member: discord.Member):
        message = await self.synchronize(member)
        await ctx.channel.send(message)

async def setup(bot):
    await bot.add_cog(Sync(bot))
