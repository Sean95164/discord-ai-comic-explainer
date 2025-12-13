import discord
import datetime
from discord import app_commands
from discord.ext import commands, tasks
from comic_object import ComicData
from xkcd_scraper import XkcdScraper

timezone = datetime.timezone(datetime.timedelta(hours=8))
task_time = datetime.time(hour=12, minute=0, second=0, tzinfo=timezone)


class XkcdCog(commands.Cog):
    """
    Cog for interacting with and posting content from xkcd.

    This class provides functionality to display xkcd panels through Discord
    interactions and automatically post xkcd comics on specific days. It uses
    the XkcdScraper for fetching xkcd data and manages tasks such as scheduled
    posting.

    Attributes:
        bot: The instance of the bot the cog is registered to.
        xkcd_scraper: An instance of the XkcdScraper used for retrieving xkcd data.
    """

    def __init__(self, bot, config, logger):
        self.bot = bot
        self.config = config
        self.logger = logger
        self.xkcd_scraper = XkcdScraper(config=config, logger=logger)

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.post_xkcd_comic.is_running():
            self.post_xkcd_comic.start()

    @app_commands.command(name="xkcd", description="Get the usable options for xkcd")
    async def xkcd_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="xkcd.com",
            description="This is a xkcd panel.",
            url="https://xkcd.com/",
        )

        embed.set_thumbnail(
            url="https://www.google.com/s2/favicons?sz=64&domain_url=https://xkcd.com/s/919f27.ico"
        )
        embed.add_field(
            name="Intro",
            value="xkcd is a popular webcomic created by Randall Munroe, "
            "blending humor with science, mathematics, and programming. "
            'It is famously described as "a webcomic of romance, sarcasm, math, and language."',
            inline=False,
        )

        # attach an example image
        embed.add_field(
            name="Example", value="Here's an example of an exploits of a mom comic."
        )
        file = discord.File("assets/exploits_of_a_mom_2x.png")
        embed.set_image(url="attachment://exploits_of_a_mom_2x.png")

        await interaction.response.send_message(
            file=file,
            embed=embed,
            view=XkcdButtonView(self.xkcd_scraper),
            ephemeral=True,
        )

    @tasks.loop(time=task_time)
    async def post_xkcd_comic(self):
        channel = self.bot.get_channel(int(self.config["XKCD_CHANNEL_ID"]))
        if channel:
            result = await self.xkcd_scraper.random_comic()
            embed = await _create_comic_embed(self.xkcd_scraper, result)
            await channel.send(embed=embed)
        else:
            self.logger.error("xkcd channel not found.")

    @post_xkcd_comic.before_loop
    async def before_post_xkcd_comic_task(self):
        await self.bot.wait_until_ready()


class XkcdSearchModal(discord.ui.Modal, title="Search"):
    """
    Represents a modal for searching xkcd comics.

    This class is a user interface component designed to enable searching xkcd comics
    through a Discord interaction. Users can input a search term via a text input field,
    and upon submission, the modal interacts with a xkcd scraping utility to fetch and
    display relevant results back to the user. Results are presented in an embed format
    with an associated button view for further interaction.

    Attributes:
        user_input (discord.ui.TextInput): Text input field where the user enters a search term.
    """

    def __init__(self, xkcd_scraper: XkcdScraper):
        super().__init__()
        self.xkcd_scraper = xkcd_scraper

    user_input = discord.ui.TextInput(
        label="Search term",
        style=discord.TextStyle.short,
        placeholder="SQL injection, Python, etc.",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.xkcd_scraper.search_comic(self.user_input.value)
        if not result:
            await interaction.followup.send("No results found.", ephemeral=True)
            return

        embed = await _create_comic_embed(self.xkcd_scraper, result)
        await interaction.followup.send(
            embed=embed, view=XkcdButtonView(self.xkcd_scraper), ephemeral=True
        )


class XkcdButtonView(discord.ui.View):
    """
    Provides a Discord UI View with buttons for interacting with xkcd comics.

    This class defines a custom Discord UI View consisting of buttons that allow
    users to interact with various functionalities related to xkcd comics, such
    as fetching the latest comic, selecting a random comic, or searching for a comic.

    Attributes:
        xkcd_scraper (XkcdScraper): An instance of the XkcdScraper class used to
        interact with xkcd's API.
    """

    def __init__(self, xkcd_scraper: XkcdScraper = None):
        super().__init__()
        self.xkcd_scraper = xkcd_scraper

    @discord.ui.button(label="Latest", style=discord.ButtonStyle.primary, emoji="😎")
    async def latest_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        result = await self.xkcd_scraper.latest_comic()

        embed = await _create_comic_embed(self.xkcd_scraper, result)
        await interaction.followup.send(
            embed=embed, view=XkcdButtonView(self.xkcd_scraper), ephemeral=True
        )

    @discord.ui.button(label="Random Select", style=discord.ButtonStyle.red, emoji="👀")
    async def random_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        result = await self.xkcd_scraper.random_comic()
        embed = await _create_comic_embed(self.xkcd_scraper, result)
        await interaction.followup.send(
            embed=embed, view=XkcdButtonView(self.xkcd_scraper), ephemeral=True
        )

    @discord.ui.button(
        label="Search Comic in xkcd", style=discord.ButtonStyle.green, emoji="❓"
    )
    async def search_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(XkcdSearchModal(self.xkcd_scraper))


# =================================================
# The following is helper functions
# =================================================


async def _create_comic_embed(xkcd_scraper: XkcdScraper, comic_data: ComicData):
    img_url = comic_data.image_url
    img_description_json = await xkcd_scraper.describe_comic()

    embed = discord.Embed(title=comic_data.title, url=comic_data.source_url)

    for key, value in img_description_json.items():
        embed.add_field(name=key, value=value, inline=False)

    embed.set_image(url=img_url)
    embed.set_footer(
        text=f"Posted at {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}"
    )
    return embed
