import asyncio
import os
import time
import discord
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler
from discord.ext import commands
from dotenv import dotenv_values
from cogs.turnoff_us_cog import TurnOffUsCog
from cogs.xkcd_cog import XkcdCog
from cogs.monkey_user_cog import MonkeyUserCog
from cogs.util_cog import UtilCog


class Client(commands.Bot):
    def __init__(self, config, logger, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.logger = logger

        os.environ["GOOGLE_API_KEY"] = config["GOOGLE_API_KEY"]
        os.environ["GROQ_API_KEY"] = config["GROQ_API_KEY"]
        os.environ["SEARCH_ENGINE"] = config["SEARCH_ENGINE"]
        os.environ["IMAGE_LLM"] = config["IMAGE_LLM"]

    async def on_ready(self):
        timezone = datetime.timezone(datetime.timedelta(hours=8))
        self.logger.info(
            f"==============================================================="
        )
        self.logger.info(
            f'Logged on as {self.user} at "{datetime.datetime.now(tz=timezone).strftime("%Y/%m/%d %H:%M:%S")}"'
        )
        self.logger.info(f"Current search engine: {os.environ['SEARCH_ENGINE']}")
        self.logger.info(f"Current image LLM: {os.environ['IMAGE_LLM']}")
        self.logger.info(
            f"==============================================================="
        )
        try:
            guild = discord.Object(id=self.config["SERVER_ID"])
            synced = await self.tree.sync(guild=guild)
            self.logger.info(f"Synced {len(synced)} commands to guild")

        except Exception as e:
            self.logger.error(f"Error syncing commands: {e}")


def utc_plus_8_converter(sec, what=None):
    return time.gmtime(sec + 8 * 3600)


async def main():
    # load env variables
    config = {**dotenv_values(".env.secret"), **dotenv_values(".env.public")}

    if not os.path.exists("logs"):
        os.mkdir("logs")

    # setup logging
    logger = logging.getLogger("discord")
    logger.setLevel(logging.INFO)
    handler = TimedRotatingFileHandler(
        filename="logs/discord.log",
        encoding="utf-8",
        when="midnight",
        interval=1,
        backupCount=30,
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s")
    )
    handler.converter = utc_plus_8_converter
    handler.suffix = "%Y-%m-%d"
    logger.addHandler(handler)

    # initialize intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True

    # initialize bot
    bot = Client(config=config, logger=logger, command_prefix="!", intents=intents)

    guild = discord.Object(id=config["SERVER_ID"])
    await bot.add_cog(
        UtilCog(bot=bot, config=config, logger=logger),
        guild=guild,
    )
    await bot.add_cog(
        XkcdCog(bot=bot, config=config, logger=logger),
        guild=guild,
    )
    await bot.add_cog(
        TurnOffUsCog(bot=bot, config=config, logger=logger),
        guild=guild,
    )
    await bot.add_cog(
        MonkeyUserCog(bot=bot, config=config, logger=logger),
        guild=guild,
    )

    await bot.start(config["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
