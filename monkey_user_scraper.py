import aiohttp
import asyncio
import random
from bs4 import BeautifulSoup
from dotenv import dotenv_values

from comic_object import ComicData
from scraper import Scraper
from urllib.parse import urljoin


config = {**dotenv_values(".env.secret"), **dotenv_values(".env.public")}


MONKEYUSER_CSE_ID = config["MONKEYUSER_CSE_ID"]


class MonkeyUserScraper(Scraper):

    def __init__(self):
        super().__init__(google_cse_id=MONKEYUSER_CSE_ID)

    @property
    def comic_name(self):
        return "monkeyuser.com"

    @property
    def search_domain(self):
        return "www.monkeyuser.com/"

    @property
    async def random_comic_url(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.monkeyuser.com/index.json") as response:
                response.raise_for_status()

                json_data = await response.json()
                random_comic = random.choice(json_data)

                base_url = "https://www.monkeyuser.com"
                full_url = urljoin(base_url, random_comic["url"])
                print(f"Random link: {full_url}")
                return full_url

    @property
    def latest_comic_url(self):
        return "https://www.monkeyuser.com/"

    async def random_comic(self):
        return await self._fetch_content(await self.random_comic_url)

    async def _fetch_content(self, url: str) -> ComicData | None:
        async with aiohttp.ClientSession() as session:
            try:
                # fetch the raw HTML
                async with session.get(url) as response:
                    response.raise_for_status()  # Check for HTTP errors

                    self.url = response.url
                    html = await response.text()
                    soup = BeautifulSoup(html, "lxml")
                    # Return the second image URL (format: {'src': 'https://...', 'alt':'})
                    content_div = soup.find("div", class_="content")
                    if content_div:
                        img_tag = content_div.find("img")
                        if img_tag:
                            base_url = "https://www.monkeyuser.com"
                            self.src = urljoin(base_url, img_tag["src"])
                            self.alt = img_tag["alt"]
                            if self.src[-4:] == ".gif":
                                random_url = urljoin(
                                    base_url, soup.find(id="random-link")["href"]
                                )
                                return await self._fetch_content(random_url)

                            comic_data = ComicData(
                                title=img_tag["title"],
                                description=self.alt,
                                image_url=self.src,
                                source_url=str(self.url),
                                source_name=self.comic_name,
                            )

                            return comic_data
                        else:
                            print("No image found.")
                            return None
                    else:
                        print("No content_div found.")
                        return None

            except aiohttp.ClientError as e:
                print(f"Error fetching URL: {e}")
                return None


# Run the async function
if __name__ == "__main__":
    monkey_user_scraper = MonkeyUserScraper()
    # asyncio.run(turnoff_us_scraper.search_comic("unzip"))
    asyncio.run(monkey_user_scraper.random_comic())
    asyncio.run(monkey_user_scraper.describe_comic())
