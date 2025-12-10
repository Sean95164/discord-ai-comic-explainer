import discord
from discord.ext import commands
from dotenv import dotenv_values

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

class Viewer(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="Random Select", style=discord.ButtonStyle.red, emoji="👀")
    async def random_button_callback(self, button, interaction: discord.Interaction):
        await button.response.send_message("Random button clicked!", ephemeral=True)

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