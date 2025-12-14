import os

import discord
from discord import app_commands
from discord.ext import commands

class UtilCog(commands.Cog):
    def __init__(self, bot, config, logger):
        self.bot = bot
        self.config = config
        self.logger = logger

    @app_commands.command(name="help", description="Show help options for all commands")
    async def help_command(self, interaction: discord.Interaction):
        description = """
### Comic panels
These commands will post a comic panel.

**/xkcd**
Get the usable options for xkcd

**/turnoff_us**
Get the usable options for turnoff.us

**/monkey_user**
Get the usable options for monkeyuser.com

### Utility commands
These commands can  provide information or change the bot's settings.

**/settings**
Check the current settings

**/search_engine**
Change the search engine setting

**/image_llm**
Change the image LLM setting
        """
        embed = discord.Embed(
            title="Help", description=description, color=0x00FF00
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="settings", description="Check the current settings")
    async def settings_command(self, interaction: discord.Interaction):
        current_engine = os.environ["SEARCH_ENGINE"]
        current_llm = os.environ["IMAGE_LLM"]
        embed = discord.Embed(title="GenAI-Comics-Bot Settings", description="Current settings:", color=0x00FF00)
        embed.add_field(name="🔍 Search engine", value=current_engine, inline=False)
        embed.add_field(name="🤖 Image LLM", value=current_llm, inline=False)
        embed.set_footer(text="Use /search_engine and /image_llm to change these settings")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Set the search engine command
    @app_commands.command(name="search_engine", description="Change the search engine setting")
    @app_commands.describe(
        engine="The search engine to use. Options: google, duckduckgo"
    )
    @app_commands.choices(engine=[
        app_commands.Choice(name="google search", value="google"),
        app_commands.Choice(name="duckduckgo search", value="duckduckgo")
    ])
    async def search_engine_command(self, interaction: discord.Interaction, engine: app_commands.Choice[str]):
        os.environ["SEARCH_ENGINE"] = engine.value
        self.logger.info(f"Search engine set to {engine.name}")
        await interaction.response.send_message(f"Search engine set to {engine.name}", ephemeral=True)

    # Set the image LLM command
    @app_commands.command(name="image_llm", description="Change the image LLM setting")
    @app_commands.describe(
        llm="The image LLM to use. Options: llama-4-scout, llama-4-maverick"
    )
    @app_commands.choices(
        llm=[
            app_commands.Choice(name="llama-4-scout", value="meta-llama/llama-4-scout-17b-16e-instruct"),
            app_commands.Choice(name="llama-4-maverick", value="meta-llama/llama-4-maverick-17b-128e-instruct")
        ]
    )
    async def image_llm_command(self, interaction: discord.Interaction, llm: app_commands.Choice[str]):
        os.environ["IMAGE_LLM"] = llm.value
        self.logger.info(f"Image LLM set to {llm.name}")
        await interaction.response.send_message(f"Image LLM set to {llm.name}", ephemeral=True)