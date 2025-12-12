import os
import json
from abc import ABC, abstractmethod
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_groq import ChatGroq
from ddgs.exceptions import DDGSException
from pydantic_object import ComicAnalysis
from dotenv import dotenv_values

config = {**dotenv_values(".env.secret"), **dotenv_values(".env.public")}

os.environ["GOOGLE_API_KEY"] = config["GOOGLE_API_KEY"]
os.environ["GROQ_API_KEY"] = config["GROQ_API_KEY"]
SEARCH_ENGINE = config["SEARCH_ENGINE"]


class Scraper(ABC):
    """
    Base class for creating a scraper to fetch and analyze comics from various sources.

    This abstract class defines the structure and methods required for creating a comic
    scraper. Subclasses should provide implementations for abstract properties and methods
    and can leverage the provided utilities for fetching and describing comics.
    """

    def __init__(self, google_cse_id: str = None):
        self.src = None
        self.alt = None
        self.url = None
        self.google_cse_id = google_cse_id
        self.llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=1,
            max_tokens=256,
            timeout=None,
            max_retries=2,
        )

    @property
    @abstractmethod
    def comic_name(self):
        pass

    @property
    @abstractmethod
    def search_domain(self):
        pass

    @property
    @abstractmethod
    def random_comic_url(self):
        pass

    @property
    @abstractmethod
    def latest_comic_url(self):
        pass

    @abstractmethod
    async def _page_url(self, url: str):
        pass

    async def random_comic(self):
        return await self._page_url(self.random_comic_url)

    async def latest_comic(self):
        return await self._page_url(self.latest_comic_url)

    async def search_comic(self, query: str, search_engine=SEARCH_ENGINE):
        link = None
        if search_engine == "google":
            wrapper = GoogleSearchAPIWrapper(google_cse_id=self.google_cse_id)
            # k=1 ensures we just get the top result
            results = wrapper.results(query, num_results=1)
            if results:
                link = results[0]["link"]

        elif search_engine == "duckduckgo":
            wrapper = DuckDuckGoSearchAPIWrapper(
                region="us-en", source="text", safesearch="off", max_results=3
            )
            search = DuckDuckGoSearchResults(
                api_wrapper=wrapper, output_format="json", num_results=1
            )

            try:
                results = json.loads(
                    await search.ainvoke(f"{query} site:{self.search_domain}")
                )
                print(results)
                if results:
                    link = results[0]["link"]
            except DDGSException:
                print(f"No results found")
                return None

        if link:
            return await self._page_url(link)
        return None

    async def describe_comic(self):
        image_url = self.src
        alt_text_info = f"Alt text: {self.alt}"
        system_prompt_text = """
        You are a witty {comic_name} explainer. 
        Analyze the provided comic and output the response in JSON format.

        Structure your response according to the instructions below:
        {format_instructions}

        Keep the explanation concise and accessible.
        """

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt_text),
                (
                    "human",
                    [
                        {
                            "type": "text",
                            "text": "Here is an {comic_name} comic. {alt_text_info}",
                        },
                        {"type": "image_url", "image_url": {"url": "{image_url}"}},
                    ],
                ),
            ]
        )

        output_parser = JsonOutputParser(pydantic_object=ComicAnalysis)

        prompt_with_instructions = prompt.partial(
            format_instructions=output_parser.get_format_instructions()
        )

        chain = prompt_with_instructions | self.llm | output_parser

        try:
            result = await chain.ainvoke(
                {
                    "image_url": image_url,
                    "alt_text_info": alt_text_info,
                    "comic_name": self.comic_name,
                }
            )
            print(result)
            return result
        except Exception as e:
            print(f"Error generating response: {e}")
            return {"Core_concept": "Error", "Explanation": "Failed to parse analysis."}

    def get_comic_source_url(self):
        return self.url
