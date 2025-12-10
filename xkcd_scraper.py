import aiohttp
import asyncio
import os
from bs4 import BeautifulSoup
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


from dotenv import dotenv_values

config = {
    **dotenv_values(".env.secret")
}
os.environ["GROQ_API_KEY"] = config["GROQ_API_KEY"]

class XkcdScraper:
    def __init__(self):
        self.src = None
        self.alt = None
        self.llm = ChatGroq(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=1,
            max_tokens=1024,
            timeout=None,
            max_retries=2,
            # other params...
        )

    async def xkcd_random_image(self, url="https://c.xkcd.com/random/comic/"):
        async with aiohttp.ClientSession() as session:
            try:
                # fetch the raw HTML
                async with session.get(url) as response:
                    response.raise_for_status()  # Check for HTTP errors
                    html_text = await response.text()

                    # parse the HTML
                    soup = BeautifulSoup(html_text, 'lxml')

                    # extract <img> tags
                    images = soup.find_all('img')

                    print(f"Found {len(images)} images on {url}:")

                    results = []
                    for img in images:
                        # get the 'src' attribute
                        src = img.get('src')
                        alt = img.get('alt', 'No alt text')

                        if src:
                            results.append({'src': src, 'alt': alt})
                            print(f"- [Alt: {alt}] -> {src}")

                    # Return the second image URL (format: {'src': 'https://...', 'alt':'})
                    self.src = results[1]['src']
                    self.alt = results[1]['alt']
                    return results[1]

            except aiohttp.ClientError as e:
                print(f"Error fetching URL: {e}")
                return []

    async def xkcd_image_description(self):
        image_url = f"https:{self.src}"
        alt_text_info = f"Alt text: {self.alt}"
        system_prompt_text = """
        You are an expert "xkcd" comic analyst and explainer. You possess deep knowledge of computer science, mathematics, physics, linguistics, and internet pop culture.

        Your task is to analyze an xkcd comic image provided by the user.

        Please structure your response in English following these steps:

        1. **Visual Description**: Briefly describe what is happening in the image. Mention the characters, diagrams, or key text.
        2. **The Core Concept**: Identify the scientific, mathematical, or programming concept.
        3. **The Explanation**: Explain why it is funny. Break down puns or references clearly for a general audience.
        4. **Alt-Text Context**: If the user provides alt-text, explain how it enhances the joke.

        Tone: Witty, educational, and accessible.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_text),
            ("human", [
                {"type": "text", "text": "Here is an xkcd comic. {alt_text_info}"},
                {"type": "image_url", "image_url": {"url": "{image_url}"}},
            ]),
        ])

        output_parser = StrOutputParser()
        chain = prompt | self.llm | output_parser
        # ai_msg =  await chain.ainvoke({"image_url": image_url, "alt_text_info": alt_text_info})
        # print(ai_msg)
        return await chain.ainvoke({"image_url": image_url, "alt_text_info": alt_text_info})



# Run the async function
if __name__ == "__main__":
    target_url = "https://c.xkcd.com/random/comic/"
    xkcd_scraper = XkcdScraper()
    asyncio.run(xkcd_scraper.xkcd_random_image())
    asyncio.run(xkcd_scraper.xkcd_image_description())