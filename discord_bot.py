import discord
from discord import Interaction
from discord._types import ClientT
from discord.ext import commands
from dotenv import dotenv_values
from xkcd_scraper import XkcdScraper

# load env variables
config = {
    **dotenv_values(".env.secret")
}

class Client(commands.Bot):
    async def on_ready(self):
        print(f"Logged on as {self.user}")
        try:
            guild = discord.Object(id=config["SERVER_ID"])
            synced = await self.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}")

        except Exception as e:
            print(f"Error syncing commands: {e}")

class SearchModel(discord.ui.Modal, title="Search"):
    user_input = discord.ui.TextInput(
        label="Search term",
        style=discord.TextStyle.paragraph,
        placeholder="Search for a comic by title or number",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Searching for {self.user_input.value}", ephemeral=True)

class Viewer(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.xkcd_scraper = XkcdScraper()

    @discord.ui.button(label="Random Select", style=discord.ButtonStyle.red, emoji="👀")
    async def random_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        results = await self.xkcd_scraper.xkcd_random_image()
        img_url = f"https:{results["src"]}"
        img_description = await self.xkcd_scraper.xkcd_image_description()

        embed = discord.Embed(
            title=results["alt"],
            url=self.xkcd_scraper.get_image_source_url()
        )

        embed.add_field(name="Description", value=img_description, inline=False)
        embed.set_image(url=img_url)

        await interaction.followup.send(embed=embed, view=Viewer(), ephemeral=True)

    @discord.ui.button(label="Search Comic in xkcd", style=discord.ButtonStyle.green, emoji="❓")
    async def search_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchModel())

def main():
    # initialize intents
    intents = discord.Intents.default()
    intents.message_content = True

    # initialize bot
    bot = Client(command_prefix="!", intents=intents)
    GUILD_ID = discord.Object(id=config["SERVER_ID"])

    @bot.tree.command(name="xkcd", description="Get the usable options for xkcd", guild=GUILD_ID)
    async def xkcd_panel(interaction: discord.Interaction):
        embed = discord.Embed(
            title="xkcd.com",
            description="This is a xkcd panel.",
            url="https://xkcd.com/"
        )

        embed.set_thumbnail(url="https://www.google.com/s2/favicons?sz=64&domain_url=https://xkcd.com/s/919f27.ico")
        embed.add_field(
            name="Intro",
            value="xkcd is a popular webcomic created by Randall Munroe, "
                  "blending humor with science, mathematics, and programming. "
                  "It is famously described as \"a webcomic of romance, sarcasm, math, and language.\"",
            inline=False
        )

        # attach an example image
        embed.add_field(name="Example", value="Here's an example of an exploits of a mom comic.")
        file = discord.File("assets/exploits_of_a_mom_2x.png")
        embed.set_image(url="attachment://exploits_of_a_mom_2x.png")

        await interaction.response.send_message(file=file, embed=embed, view=Viewer(), ephemeral=True)

    bot.run(config["DISCORD_BOT_TOKEN"])

if __name__ == "__main__":
    main()
