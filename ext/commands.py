from discord.ext import commands
import discord
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def synchronize(self, member) -> str:

        roles = {
            "pending": 1328545548080250993,
            "registering": 1328545670713442324,
            "applied": 1328545785868058775,
            "selected": 1328545833129345034,
            "accepted": 1328545968370614412,
            "attended": 1328546008493199380,
            "volunteer": 1328546105947979877
        }

        async with self.bot.db_pool.acquire() as connection:
            user = await connection.fetchrow(f"SELECT status FROM users WHERE discord_id = $1", str(member.id))

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
    @commands.command(name="sync", description="Command to sync dashboard status with discord role", aliases=['s'])
    async def sync(self, ctx):

        if ctx.author.mutual_guilds:
            guild = ctx.author.mutual_guilds[0]
            member = guild.get_member(ctx.author.id)
            await self.synchronize(member)

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.command(name="adminsync", description="Same as sync but can be applied to other users", aliases=['as'])
    async def adminsync(self, ctx, member: discord.Member):
        message = await self.synchronize(member)
        await ctx.channel.send(message)





async def setup(bot):
    await bot.add_cog(Commands(bot))