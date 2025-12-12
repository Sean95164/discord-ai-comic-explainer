import discord
import datetime
from discord import app_commands
from discord.ext import commands, tasks
from turnoff_us_scraper import TurnOffUsScraper
from dotenv import dotenv_values

config = {**dotenv_values(".env.secret")}

timezone = datetime.timezone(datetime.timedelta(hours=8))
task_time = datetime.time(hour=8, minute=0, second=0, tzinfo=timezone)


class TurnOffUsCog(commands.Cog):
    """
    Cog for managing the turnoff.us webcomic functionalities.

    This cog integrates with Discord's bot command and event systems to
    provide functionalities related to the turnoff.us webcomic. It includes
    commands for interacting with the webcomic directly and an automated
    task to post random comics to a specific channel.

    Attributes:
        bot: A reference to the bot instance.
        turnoff_us_scraper: An instance of the scraper for turnoff.us comics.
    """

    def __init__(self, bot):
        self.bot = bot
        self.turnoff_us_scraper = TurnOffUsScraper()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.post_turnoff_us_comic.is_running():
            self.post_turnoff_us_comic.start()

    @app_commands.command(
        name="turnoff_us", description="Get the usable options for turnoff.us"
    )
    async def turnoff_us_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="turnoff.us",
            description="This is a turnoff.us panel.",
            url="https://turnoff.us/",
        )

        embed.set_thumbnail(url="https://turnoff.us/image/logo.png")
        embed.add_field(
            name="Intro",
            value="Turnoff.us is a geeky webcomic created by Daniel Stori "
            "that focuses on computer science, programming, and the daily lives of technology professionals.",
            inline=False,
        )

        # attach an example image
        embed.add_field(name="Example", value="Here's an example of unzip comic.")
        file = discord.File("assets/unzip.png")
        embed.set_image(url="attachment://unzip.png")

        await interaction.response.send_message(
            file=file,
            embed=embed,
            view=TurnOffUsButtonView(self.turnoff_us_scraper),
            ephemeral=True,
        )

    @tasks.loop(time=task_time)
    async def post_turnoff_us_comic(self):
        channel = self.bot.get_channel(int(config["TURNOFF_US_CHANNEL_ID"]))
        if channel:
            result = await self.turnoff_us_scraper.random_comic()
            embed = await _create_comic_embed(self.turnoff_us_scraper, result)
            await channel.send(embed=embed)
        else:
            print("Channel not found.")

    @post_turnoff_us_comic.before_loop
    async def before_post_turnoff_us_comic_task(self):
        await self.bot.wait_until_ready()


class TurnOffUsSearchModal(discord.ui.Modal, title="Search"):
    """
    Handles the user interaction for searching comics using a modal interface.

    This class represents a Discord UI modal for accepting user input to search for comics
    through the TurnOffUsScraper. Upon submission of the search term, it performs the
    search and responds with the search results if found or a fallback message if not.

    Attributes:
        user_input (discord.ui.TextInput): The Discord input field used to collect the search term
            from the user.

    Methods:
        on_submit(interaction: discord.Interaction):
            Handles the action performed when the user submits the modal, processes the
            search through the scraper, and responds with the results or a fallback message.
    """

    def __init__(self, turnoff_us_scraper: TurnOffUsScraper):
        super().__init__()
        self.turnoff_us_scraper = turnoff_us_scraper

    user_input = discord.ui.TextInput(
        label="Search term",
        style=discord.TextStyle.short,
        placeholder="Linux, Python, etc.",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.turnoff_us_scraper.search_comic(self.user_input.value)
        if not result:
            await interaction.followup.send("No results found.", ephemeral=True)

        embed = await _create_comic_embed(self.turnoff_us_scraper, result)
        await interaction.followup.send(
            embed=embed,
            view=TurnOffUsButtonView(self.turnoff_us_scraper),
            ephemeral=True,
        )


class TurnOffUsButtonView(discord.ui.View):
    """
    Interactive Discord UI view for interacting with TurnOffUsScraper.

    This class provides an interactive Discord UI view with buttons for fetching the latest comic,
    selecting a random comic, or searching for a comic within the xkcd collection. It serves as a
    bridge between the user interface and the TurnOffUsScraper functionality.

    Attributes:
        turnoff_us_scraper (TurnOffUsScraper): An instance of the TurnOffUsScraper class used to
            fetch and manage comic data.
    """

    def __init__(self, turnoff_us_scraper: TurnOffUsScraper = None):
        super().__init__()
        self.turnoff_us_scraper = turnoff_us_scraper

    @discord.ui.button(label="Latest", style=discord.ButtonStyle.primary, emoji="😎")
    async def latest_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        result = await self.turnoff_us_scraper.latest_comic()

        embed = await _create_comic_embed(self.turnoff_us_scraper, result)
        await interaction.followup.send(
            embed=embed,
            view=TurnOffUsButtonView(self.turnoff_us_scraper),
            ephemeral=True,
        )

    @discord.ui.button(label="Random Select", style=discord.ButtonStyle.red, emoji="👀")
    async def random_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        result = await self.turnoff_us_scraper.random_comic()

        embed = await _create_comic_embed(self.turnoff_us_scraper, result)
        await interaction.followup.send(
            embed=embed,
            view=TurnOffUsButtonView(self.turnoff_us_scraper),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Search Comic in xkcd", style=discord.ButtonStyle.green, emoji="❓"
    )
    async def search_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            TurnOffUsSearchModal(self.turnoff_us_scraper)
        )


# =================================================
# The following is helper functions
# =================================================


async def _create_comic_embed(xkcd_scraper: TurnOffUsScraper, result):
    img_url = result["img"]
    img_description_json = await xkcd_scraper.describe_comic()

    embed = discord.Embed(
        title=result["title"], url=xkcd_scraper.get_comic_source_url()
    )

    for key, value in img_description_json.items():
        embed.add_field(name=key, value=value, inline=False)

    embed.set_image(url=img_url)
    embed.set_footer(
        text=f"Posted on {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}"
    )
    return embed
