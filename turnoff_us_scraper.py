import aiohttp
import asyncio

from bs4 import BeautifulSoup
from dotenv import dotenv_values
from scraper import Scraper
from urllib.parse import urljoin
import re
import random
import json

config = {
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.public")
}


TURNOFFUS_CSE_ID = config["TURNOFFUS_CSE_ID"]

class TurnOffUsScraper(Scraper):

    def __init__(self):
        super().__init__(google_cse_id=TURNOFFUS_CSE_ID)
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}

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
                        print(f"Random link: {full_url}")
                        return full_url
                    else:
                        return None

                else:
                    print("No random link found.")
                    return None

    @property
    def latest_comic_url(self):
        return "https://turnoff.us/"

    async def random_comic(self):
        return await self._page_url(await self.random_comic_url)

    async def _page_url(self, url: str):
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
                            self.src = urljoin(base_url, img_tag['src'])
                            self.alt = img_tag['alt']
                            if self.src[-4:] == ".gif":
                                random_url = urljoin(base_url, soup.find(id="random-link")["href"])
                                return await self._page_url(random_url)

                            return {"title": self.alt, "img": self.src}
                        else:
                            print("No image found.")
                            return None
                    else:
                        print("No article found.")
                        return None


            except aiohttp.ClientError as e:
                print(f"Error fetching URL: {e}")
                return None


# Run the async function
if __name__ == "__main__":
    turnoff_us_scraper = TurnOffUsScraper()
    # asyncio.run(turnoff_us_scraper.search_comic("unzip"))
    asyncio.run(turnoff_us_scraper.random_comic())
    asyncio.run(turnoff_us_scraper.describe_comic())
