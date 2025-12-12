import discord
import datetime
from discord import app_commands
from discord.ext import commands, tasks
from monkey_user_scraper import MonkeyUserScraper
from dotenv import dotenv_values

config = {**dotenv_values(".env.secret")}

timezone = datetime.timezone(datetime.timedelta(hours=8))
task_time = datetime.time(hour=8, minute=0, second=0, tzinfo=timezone)


class MonkeyUserCog(commands.Cog):
    """
    Represents a Discord Cog for interacting with MonkeyUser webcomics.

    The MonkeyUserCog class provides a set of commands and scheduled tasks
    to interact with MonkeyUser, a webcomic that humorously portrays
    software development, engineering, and IT professional life.
    This Cog automates fetching and posting random comics, as well as offering
    users a panel to explore MonkeyUser options.

    Attributes:
        bot (commands.Bot): The instance of the bot that this Cog is connected to.
        monkey_user_scraper (MonkeyUserScraper): Used for scraping comic content
            from the MonkeyUser website.
    """

    def __init__(self, bot):
        self.bot = bot
        self.monkey_user_scraper = MonkeyUserScraper()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.post_monkey_user_comic.is_running():
            self.post_monkey_user_comic.start()

    @app_commands.command(
        name="monkey_user", description="Get the usable options for monkeyuser.com"
    )
    async def monkey_user_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="monkeyuser.com",
            description="This is a monkeyuser.com panel.",
            url="https://www.monkeyuser.com/",
        )

        embed.set_thumbnail(url="https://www.monkeyuser.com/images/logo.png")
        embed.add_field(
            name="Intro",
            value="MonkeyUser is a popular webcomic that humorously satirizes "
            "the daily life of software developers, engineers, and IT professionals.",
            inline=False,
        )

        # attach an example image
        embed.add_field(name="Example", value="Here's an example of natural language instructions comic.")
        file = discord.File("assets/273-natural-language-instructions.png")
        embed.set_image(url="attachment://273-natural-language-instructions.png")

        await interaction.response.send_message(
            file=file,
            embed=embed,
            view=MonkeyUserButtonView(self.monkey_user_scraper),
            ephemeral=True,
        )

    @tasks.loop(time=task_time)
    async def post_monkey_user_comic(self):
        channel = self.bot.get_channel(int(config["MONKEYUSER_CHANNEL_ID"]))
        if channel:
            result = await self.monkey_user_scraper.random_comic()
            embed = await _create_comic_embed(self.monkey_user_scraper, result)
            await channel.send(embed=embed)
        else:
            print("Channel not found.")

    @post_monkey_user_comic.before_loop
    async def before_post_monkey_user_comic_task(self):
        await self.bot.wait_until_ready()


class MonkeyUserSearchModal(discord.ui.Modal, title="Search"):
    """
    A modal dialog interface for searching MonkeyUser comics.

    This class represents a Discord UI Modal where users can provide a search term
    to query the MonkeyUser comics. Upon submission, the modal interacts with the
    MonkeyUserScraper to fetch and display related comic results.

    Attributes:
        user_input: A TextInput element where users can input the search term for
            querying comics.
    """

    def __init__(self, monkey_user_scraper: MonkeyUserScraper):
        super().__init__()
        self.monkey_user_scraper = monkey_user_scraper

    user_input = discord.ui.TextInput(
        label="Search term",
        style=discord.TextStyle.short,
        placeholder="LLM, AI Assistant, etc.",
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.monkey_user_scraper.search_comic(self.user_input.value)
        if not result:
            await interaction.followup.send("No results found.", ephemeral=True)

        embed = await _create_comic_embed(self.monkey_user_scraper, result)
        await interaction.followup.send(
            embed=embed,
            view=MonkeyUserButtonView(self.monkey_user_scraper),
            ephemeral=True,
        )


class MonkeyUserButtonView(discord.ui.View):
    """
    Provides an interactive Discord UI for interacting with MonkeyUser comics.

    This class extends discord.ui.View to create a user interface for interacting with the
    MonkeyUser comics. It provides buttons for fetching the latest comic, selecting a
    random comic, or initiating a comic search on monkeyuser.com. Each button invokes
    specific functionality related to MonkeyUser comics.

    Attributes:
        monkey_user_scraper (MonkeyUserScraper): The scraper interface used to fetch
            comic data from MonkeyUser.
    """

    def __init__(self, monkey_user_scraper: MonkeyUserScraper = None):
        super().__init__()
        self.monkey_user_scraper = monkey_user_scraper

    @discord.ui.button(label="Latest", style=discord.ButtonStyle.primary, emoji="😎")
    async def latest_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        result = await self.monkey_user_scraper.latest_comic()

        embed = await _create_comic_embed(self.monkey_user_scraper, result)
        await interaction.followup.send(
            embed=embed,
            view=MonkeyUserButtonView(self.monkey_user_scraper),
            ephemeral=True,
        )

    @discord.ui.button(label="Random Select", style=discord.ButtonStyle.red, emoji="👀")
    async def random_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.defer()
        result = await self.monkey_user_scraper.random_comic()

        embed = await _create_comic_embed(self.monkey_user_scraper, result)
        await interaction.followup.send(
            embed=embed,
            view=MonkeyUserButtonView(self.monkey_user_scraper),
            ephemeral=True,
        )

    @discord.ui.button(
        label="Search Comic in monkeyuser.com",
        style=discord.ButtonStyle.green,
        emoji="❓",
    )
    async def search_button_callback(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            MonkeyUserSearchModal(self.monkey_user_scraper)
        )


# =================================================
# The following is helper functions
# =================================================


async def _create_comic_embed(monkey_user_scraper: MonkeyUserScraper, result):
    img_url = result["img"]
    img_description_json = await monkey_user_scraper.describe_comic()

    embed = discord.Embed(
        title=result["title"], url=monkey_user_scraper.get_comic_source_url()
    )

    for key, value in img_description_json.items():
        embed.add_field(name=key, value=value, inline=False)

    embed.set_image(url=img_url)
    embed.set_footer(
        text=f"Posted on {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}"
    )
    return embed
