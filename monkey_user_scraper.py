import aiohttp
import asyncio
import random
from bs4 import BeautifulSoup
from comic_object import ComicData
from scraper import Scraper
from urllib.parse import urljoin


class MonkeyUserScraper(Scraper):
    def __init__(self, config, logger=None):
        super().__init__(
            google_cse_id=config["MONKEYUSER_CSE_ID"], config=config, logger=logger
        )

    @property
    def comic_name(self):
        return "monkeyuser.com"

    @property
    def search_domain(self):
        return "www.monkeyuser.com/"

    @property
    async def random_comic_url(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.monkeyuser.com/index.json"
                ) as response:
                    response.raise_for_status()

                    json_data = await response.json()
                    random_comic = random.choice(json_data)

                    base_url = "https://www.monkeyuser.com"
                    full_url = urljoin(base_url, random_comic["url"])
                    return full_url
        except Exception as e:
            (
                self.logger.error(f"monkeyuser.com: Error fetching random comic: {e}")
                if self.logger
                else None
            )
            return None

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
                            (
                                self.logger.info(
                                    f"monkeyuser.com: Fetched comic: {comic_data}"
                                )
                                if self.logger
                                else None
                            )
                            return comic_data
                        else:
                            (
                                self.logger.error(
                                    "monkeyuser.com: Cannot find image tag."
                                )
                                if self.logger
                                else None
                            )
                            return None
                    else:
                        (
                            self.logger.error(
                                "monkeyuser.com: Cannot find div tag with class 'content'."
                            )
                            if self.logger
                            else None
                        )
                        return None

            except aiohttp.ClientError as e:
                (
                    self.logger.error(f"monkeyuser.com: Error fetching URL: {e}")
                    if self.logger
                    else None
                )
                return None


# Run the async function
if __name__ == "__main__":
    from dotenv import dotenv_values

    config = {**dotenv_values(".env.secret"), **dotenv_values(".env.public")}
    monkey_user_scraper = MonkeyUserScraper(config=config)
    asyncio.run(monkey_user_scraper.search_comic("instructions"))
    # asyncio.run(monkey_user_scraper.random_comic())
    # asyncio.run(monkey_user_scraper.describe_comic())
