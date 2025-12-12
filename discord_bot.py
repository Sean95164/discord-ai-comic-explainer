import asyncio

import discord
from discord.ext import commands
from dotenv import dotenv_values

from turn_off_us_cog import TurnOffUsCog
from xkcd_cog import XkcdCog

# load env variables
config = {**dotenv_values(".env.secret")}


class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}")
        try:
            guild = discord.Object(id=config["SERVER_ID"])
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}")

        except Exception as e:
            print(f"Error syncing commands: {e}")


async def main():
    # initialize intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True

    # initialize bot
    bot = Client(command_prefix="!", intents=intents)

    await bot.add_cog(XkcdCog(bot), guild=discord.Object(id=config["SERVER_ID"]))
    await bot.add_cog(TurnOffUsCog(bot), guild=discord.Object(id=config["SERVER_ID"]))
    await bot.start(config["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
