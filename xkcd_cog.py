import discord
import datetime
from discord import app_commands
from discord.ext import commands, tasks
from xkcd_scraper import XkcdScraper
from dotenv import dotenv_values

config = {
    **dotenv_values(".env.secret")
}

timezone = datetime.timezone(datetime.timedelta(hours=8))
task_time = datetime.time(hour=12, minute=0, second=0, tzinfo=timezone)

class XkcdCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.post_xkcd_comic.start()
        self.xkcd_scraper = XkcdScraper()



    @app_commands.command(name="xkcd", description="Get the usable options for xkcd")
    async def xkcd_panel(self, interaction: discord.Interaction):
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

        await interaction.response.send_message(file=file, embed=embed, view=XkcdButtonView(self.xkcd_scraper), ephemeral=True)

    @tasks.loop(time=task_time)
    async def post_xkcd_comic(self):
        now = datetime.datetime.now(timezone)

        if now.weekday() not in [0, 2, 4]:
            return

        channel = self.bot.get_channel(int(config["CHANNEL_ID"]))
        if channel:
            result = await self.xkcd_scraper.xkcd_latest()
            embed = await _create_comic_embed(self.xkcd_scraper, result)
            await channel.send(embed=embed)
        else:
            print("Channel not found.")

    @post_xkcd_comic.before_loop
    async def before_test_task(self):
        await self.bot.wait_until_ready()


class XkcdSearchModal(discord.ui.Modal, title="Search"):
    def __init__(self, xkcd_scraper: XkcdScraper):
        super().__init__()
        self.xkcd_scraper = xkcd_scraper

    user_input = discord.ui.TextInput(
        label="Search term",
        style=discord.TextStyle.short,
        placeholder="SQL injection, Python, etc.",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        result = await self.xkcd_scraper.xkcd_search(self.user_input.value)
        if not result:
            await interaction.followup.send("No results found.", ephemeral=True)

        embed = await _create_comic_embed(self.xkcd_scraper, result)
        await interaction.followup.send(embed=embed, view=XkcdButtonView(self.xkcd_scraper), ephemeral=True)

class XkcdButtonView(discord.ui.View):
    def __init__(self, xkcd_scraper: XkcdScraper = None):
        super().__init__()
        self.xkcd_scraper = xkcd_scraper

    @discord.ui.button(label="Latest", style=discord.ButtonStyle.primary, emoji="😎")
    async def latest_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        result = await self.xkcd_scraper.xkcd_latest()

        embed = await _create_comic_embed(self.xkcd_scraper, result)
        await interaction.followup.send(embed=embed, view=XkcdButtonView(self.xkcd_scraper), ephemeral=True)

    @discord.ui.button(label="Random Select", style=discord.ButtonStyle.red, emoji="👀")
    async def random_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        result = await self.xkcd_scraper.xkcd_random()

        embed = await _create_comic_embed(self.xkcd_scraper, result)
        await interaction.followup.send(embed=embed, view=XkcdButtonView(self.xkcd_scraper), ephemeral=True)

    @discord.ui.button(label="Search Comic in xkcd", style=discord.ButtonStyle.green, emoji="❓")
    async def search_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(XkcdSearchModal(self.xkcd_scraper))

# =================================================
# The following is helper functions
# =================================================

async def _create_comic_embed(xkcd_scraper: XkcdScraper, result):
    img_url = result["img"]
    img_description_json = await xkcd_scraper.xkcd_image_description()

    embed = discord.Embed(
        title=result["title"],
        url=xkcd_scraper.get_image_source_url()
    )

    for key, value in img_description_json.items():
        embed.add_field(name=key, value=value, inline=False)

    embed.set_image(url=img_url)
    embed.set_footer(text=f"Posted on {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}")
    return embed