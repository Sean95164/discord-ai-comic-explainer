import aiohttp
import asyncio
import re
import random
import json
from bs4 import BeautifulSoup
from objects.comic_object import ComicData
from scrapers.scraper import Scraper
from urllib.parse import urljoin


class TurnOffUsScraper(Scraper):

    def __init__(self, config, logger=None):
        super().__init__(
            google_cse_id=config["TURNOFFUS_CSE_ID"], config=config, logger=logger
        )

    @property
    def comic_name(self):
        return "turnoff.us"

    @property
    def search_domain(self):
        return "turnoff.us/geek/"

    @property
    async def random_comic_url(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://turnoff.us/") as response:
                response.raise_for_status()

                html = await response.text()

                pattern = re.compile(r"var pages = (\[.*?\]);", re.DOTALL)
                match = pattern.search(html)

                if match:
                    pages_str = match.group(1)
                    pages = json.loads(pages_str)

                    if pages:
                        base_url = "https://turnoff.us/"
                        random_path = random.choice(pages)
                        full_url = urljoin(base_url, random_path)
                        return full_url
                    else:
                        return None

                else:
                    (
                        self.logger.error("turnoff.us: Cannot get random comic URL.")
                        if self.logger
                        else None
                    )
                    return None

    @property
    def latest_comic_url(self):
        return "https://turnoff.us/"

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
                    article = soup.find("article", class_="post-content")
                    if article:
                        img_tag = article.find("img")
                        if img_tag:
                            base_url = "https://turnoff.us/"
                            self.src = urljoin(base_url, img_tag["src"])
                            self.alt = img_tag["alt"]
                            if self.src[-4:] == ".gif":
                                random_url = urljoin(
                                    base_url, soup.find(id="random-link")["href"]
                                )
                                return await self._fetch_content(random_url)

                            comic_data = ComicData(
                                title=self.alt,
                                description=self.alt,
                                image_url=self.src,
                                source_url=str(self.url),
                                source_name=self.comic_name,
                            )
                            (
                                self.logger.info(
                                    f"turnoff.us: Fetched comic: {comic_data}"
                                )
                                if self.logger
                                else None
                            )
                            return comic_data
                        else:
                            (
                                self.logger.error("turnoff.us: Cannot find image tag.")
                                if self.logger
                                else None
                            )
                            return None
                    else:
                        (
                            self.logger.error("turnoff.us: Cannot find article tag.")
                            if self.logger
                            else None
                        )
                        return None

            except aiohttp.ClientError as e:
                (
                    self.logger.error(f"turnoff.us: Error fetching URL: {e}")
                    if self.logger
                    else None
                )
                return None


# Run the async function
if __name__ == "__main__":
    from dotenv import dotenv_values

    config = {**dotenv_values("../.env.secret"), **dotenv_values("../.env.public")}
    turnoff_us_scraper = TurnOffUsScraper(config=config)
    # asyncio.run(turnoff_us_scraper.search_comic("unzip"))
    asyncio.run(turnoff_us_scraper.random_comic())
    asyncio.run(turnoff_us_scraper.describe_comic())
