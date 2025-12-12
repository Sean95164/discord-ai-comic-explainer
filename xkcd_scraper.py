import aiohttp
import asyncio
import os
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from ddgs.exceptions import DDGSException
from pydantic_object import ComicAnalysis
import json


from dotenv import dotenv_values

config = {
    **dotenv_values(".env.secret"),
    **dotenv_values(".env.public")
}
os.environ["GOOGLE_API_KEY"] = config["GOOGLE_API_KEY"]
os.environ["GROQ_API_KEY"] = config["GROQ_API_KEY"]
XKCD_CSE_ID = config["XKCD_CSE_ID"]
SEARCH_ENGINE = config["SEARCH_ENGINE"]

class XkcdScraper:
    def __init__(self):
        self.src = None
        self.alt = None
        self.url = None
        self.llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=1,
            max_tokens=256,
            timeout=None,
            max_retries=2,
            # other params...
        )

    async def _xkcd_page_url(self, url: str):
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
                    self.src = comic_json['img']
                    self.alt = comic_json['alt']
                    if self.src[-4:] == ".gif":
                        return await self._xkcd_page_url()

                    return comic_json

            except aiohttp.ClientError as e:
                print(f"Error fetching URL: {e}")
                return []

    async def xkcd_random(self):
        return await self._xkcd_page_url("https://c.xkcd.com/random/comic/")

    async def xkcd_latest(self):
        return await self._xkcd_page_url("https://xkcd.com/info.0.json")

    async def xkcd_search(self, query: str, search_engine=SEARCH_ENGINE):
        """
        Search for a specific xkcd comic by topic or keywords.
        Returns the comic title, page link, and direct image URL.
        """
        link = None
        if search_engine == "google":
            wrapper = GoogleSearchAPIWrapper(google_cse_id=XKCD_CSE_ID)
            # k=1 ensures we just get the top result
            results = wrapper.results(query, num_results=1)
            if results:
                link = results[0]["link"]

        elif search_engine == "duckduckgo":
            wrapper = DuckDuckGoSearchAPIWrapper(
                region="us-en",
                source="text",
                safesearch="off",
                max_results=3
            )
            search = DuckDuckGoSearchResults(api_wrapper=wrapper, output_format="json", num_results=1)

            try:
                results = json.loads(await search.ainvoke(f"{query} site:www.xkcd.com"))
                print(results)
                if results:
                    link = results[0]["link"]
            except DDGSException:
                print(f"No results found")
                return None

        if link:
            return await self._xkcd_page_url(link)
        return None

    async def xkcd_image_description(self):
        image_url = self.src
        alt_text_info = f"Alt text: {self.alt}"
        system_prompt_text = """
        You are a witty xkcd explainer. 
        Analyze the provided comic and output the response in JSON format.
        
        Structure your response according to the instructions below:
        {format_instructions}
        
        Keep the explanation concise and accessible.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_text),
            ("human", [
                {"type": "text", "text": "Here is an xkcd comic. {alt_text_info}"},
                {"type": "image_url", "image_url": {"url": "{image_url}"}},
            ]),
        ])

        output_parser = JsonOutputParser(pydantic_object=ComicAnalysis)

        prompt_with_instructions = prompt.partial(format_instructions=output_parser.get_format_instructions())

        chain = prompt_with_instructions | self.llm | output_parser

        try:
            result = await chain.ainvoke({"image_url": image_url, "alt_text_info": alt_text_info})
            print(result)
            return result
        except Exception as e:
            print(f"Error generating response: {e}")
            return {"Core_concept": "Error", "Explanation": "Failed to parse analysis."}

    def get_image_source_url(self):
        return self.url



# Run the async function
if __name__ == "__main__":
    target_url = "https://c.xkcd.com/random/comic/"
    xkcd_scraper = XkcdScraper()
    asyncio.run(xkcd_scraper.xkcd_search("SQL injection"))
    # asyncio.run(xkcd_scraper.xkcd_image_description())
    # asyncio.run(xkcd_scraper.search_xkcd("data alignment"))