import discord
import os
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
import logging
load_dotenv(find_dotenv())
logging.basicConfig(level=logging.INFO)


class DeerHacks(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix=os.environ["PREFIX"],
            status=discord.Status.online,
            activity=discord.Game(name="https://deerhacks.ca"),
            intents=discord.Intents.all(),
            help_command=None,
            case_insensitive=True
        )

        self.initial_extensions = [
            'ext.startup',
            'ext.errors',
            'ext.attendance',
            'ext.sync',
            'ext.volunteers'
        ]

    async def setup_hook(self):
        for ext in self.initial_extensions:
            await self.load_extension(ext)


bot = DeerHacks()
bot.run(os.environ["TOKEN"])