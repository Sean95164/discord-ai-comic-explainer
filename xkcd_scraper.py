import aiohttp
import asyncio
from dotenv import dotenv_values
from urllib.parse import urljoin
from comic_object import ComicData
from scraper import Scraper

config = {**dotenv_values(".env.secret"), **dotenv_values(".env.public")}

XKCD_CSE_ID = config["XKCD_CSE_ID"]


class XkcdScraper(Scraper):

    def __init__(self):
        super().__init__(google_cse_id=XKCD_CSE_ID)

    @property
    def comic_name(self):
        return "xkcd"

    @property
    def search_domain(self):
        return "www.xkcd.com/"

    @property
    def random_comic_url(self):
        return "https://c.xkcd.com/random/comic/"

    @property
    def latest_comic_url(self):
        return "https://xkcd.com/"

    async def _fetch_content(self, url: str) -> ComicData | None:
        async with aiohttp.ClientSession() as session:
            try:
                # fetch the raw HTML
                async with session.get(url) as response:
                    response.raise_for_status()  # Check for HTTP errors

                    self.url = response.url

                async with session.get(f"{self.url}/info.0.json") as response:
                    comic_json = await response.json()
                    print(comic_json)

                    # Return the second image URL (format: {'src': 'https://...', 'alt':'})
                    base_url = "https://xkcd.com/"
                    full_url = urljoin(base_url, str(comic_json["num"]))
                    self.url = full_url
                    self.src = comic_json["img"]
                    self.alt = comic_json["alt"]
                    if self.src[-4:] == ".gif":
                        return await self._fetch_content(
                            "https://c.xkcd.com/random/comic/"
                        )

                    comic_data = ComicData(
                        title=comic_json["title"],
                        description=self.alt,
                        image_url=self.src,
                        source_url=self.url,
                        source_name=self.comic_name,
                    )
                    return comic_data

            except aiohttp.ClientError as e:
                print(f"Error fetching URL: {e}")
                return None


# Run the async function
if __name__ == "__main__":
    target_url = "https://c.xkcd.com/random/comic/"
    xkcd_scraper = XkcdScraper()
    asyncio.run(xkcd_scraper.search_comic("sql injection"))
    # asyncio.run(xkcd_scraper.describe_comic())
