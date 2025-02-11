import discord
import asyncio
import logging
import asyncpg
import csv
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TOKEN"]
GUILD_ID = 1328094252676157540
DB_CONFIG = {
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASS"],
    "database": os.environ["DB_NAME"],
    "host": os.environ["DB_HOST"]
}
ROLES = {
    "pending": int(os.environ["PENDING_ROLE_ID"]),
    "registering": int(os.environ["REGISTERING_ROLE_ID"]),
    "applied": int(os.environ["APPLIED_ROLE_ID"]),
    "selected": int(os.environ["SELECTED_ROLE_ID"]),
    "accepted": int(os.environ["ACCEPTED_ROLE_ID"]),
    "attended": int(os.environ["ATTENDED_ROLE_ID"]),
    "volunteer": int(os.environ["VOLUNTEER_ROLE_ID"])
}

# CSV file path
CSV_FILE = "members.csv" 

# Initialize Discord client
intents = discord.Intents.default()
intents.members = True  # Required to fetch members

client = discord.Client(intents=intents)


async def connect_db():
    """ Connect to PostgreSQL database. """
    return await asyncpg.create_pool(**DB_CONFIG)


async def fetch_user_status(db_pool, discord_id):
    """ Fetch user status from the database based on discord_id. """
    async with db_pool.acquire() as connection:
        user = await connection.fetchrow("SELECT status FROM users WHERE discord_id = $1", str(discord_id))
    return user['status'] if user else None


async def synchronize_member(member, status):
    """ Synchronize a member's role based on their database status. """
    if not status or status not in ROLES:
        logger.warning(f"No valid role found for {member.name} ({member.id}) with status {status}")
        return f"Failed to synchronize: No valid role found for {member.name}"

    role_id = ROLES[status]
    role = member.guild.get_role(role_id)

    if not role:
        logger.error(f"Role ID {role_id} not found in guild")
        return "Failed to synchronize: Role not found"

    try:
        await member.edit(roles=[role])
        logger.info(f"Successfully assigned role {role.name} to {member.name}")
        return f"Successfully synchronized role {role.name} for {member.name}"
    except discord.Forbidden:
        logger.error(f"Permission issue: Cannot edit roles for {member.name}")
        return "Failed to synchronize due to insufficient permissions"
    except discord.HTTPException as e:
        logger.error(f"HTTPException: {e}")
        return "Failed to synchronize due to an API error"


async def synchronize_from_csv():
    """ Read discord IDs from CSV and update roles in Discord. """
    db_pool = await connect_db()

    guild = client.get_guild(GUILD_ID)
    if not guild:
        logger.error("Failed to retrieve guild. Ensure the bot is in the server.")
        return

    logger.info(f"Fetching members from {guild.name}...")

    # Read discord_ids from CSV
    with open(CSV_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            discord_id = row.get("discord_id")
            if not discord_id:
                continue

            member = guild.get_member(int(discord_id))
            if not member:
                logger.warning(f"Member {discord_id} not found in guild")
                continue

            status = await fetch_user_status(db_pool, discord_id)
            result = await synchronize_member(member, status)
            logger.info(result)


@client.event
async def on_ready():
    """ Runs when the bot is connected. """
    logger.info(f"Logged in as {client.user} | Guild: {client.get_guild(GUILD_ID)}")
    await synchronize_from_csv()
    await client.close()


client.run(BOT_TOKEN)
