from discord.ext import commands
import discord
import asyncio

class Commands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def synchronize(self, member) -> str:

        roles = {
            "pending": 1087192865186254999,
            "registering": 1087193230157819925,
            "applied": 1192983763995602964,
            "selected": 1192983889807933490,
            "accepted": 1192984014571704330,
            "attended": 1192984114987548722,
            "volunteer": 1100893133581070476
        }

        user = await self.bot.db.fetchrow(f"SELECT status FROM users WHERE discord_id = $1", str(member.id))

        if user and user['status'] in roles:
            await member.edit(roles=[member.guild.get_role(roles[user['status']])])
            return "Successfully synchronized"

        return "Failed to synchronize"



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