import asyncio
import discord
from discord.ext import commands
from dotenv import dotenv_values
from turn_off_us_cog import TurnOffUsCog
from xkcd_cog import XkcdCog
from monkey_user_cog import MonkeyUserCog

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
    await bot.add_cog(MonkeyUserCog(bot), guild=discord.Object(id=config["SERVER_ID"]))

    @bot.tree.command(
        name="help",
        description="Show help options for all commands",
        guild=discord.Object(id=config["SERVER_ID"]),
    )
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Help", description="List of commands:", color=0x00FF00
        )
        embed.add_field(
            name="/xkcd", value="Get the usable options for xkcd", inline=False
        )
        embed.add_field(
            name="/turnoff_us",
            value="Get the usable options for turnoff.us",
            inline=False,
        )
        embed.add_field(
            name="/monkey_user",
            value="Get the usable options for monkeyuser.com",
            inline=False,
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    await bot.start(config["DISCORD_BOT_TOKEN"])


if __name__ == "__main__":
    asyncio.run(main())
