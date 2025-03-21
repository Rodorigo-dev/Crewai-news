from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from models import ScholarProfile

class CrawlinhosInput(BaseModel):
    profile_url: str = Field(..., description="Google Scholar Profile URL to be crawled") 

class CrawlinhosTool(BaseTool):
    name: str = "Crawlinhos"
    description: str = "Crawlinhos é uma ferramenta que extrai informações de um perfil do Google Scholar."
    args_schema: Type[BaseModel] = CrawlinhosInput

    def _run(self, profile_url: str) -> str:
        return profile_url


async def main():
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler() as crawler:
        # Run the crawler on a URL
        result = await crawler.arun(url="https://scholar.google.com/citations?user=lhl7mlAAAAAJ&hl=pt-BR&oi=ao")

        # Print the extracted content
        print(result.markdown)

# Run the async main function
asyncio.run(main())