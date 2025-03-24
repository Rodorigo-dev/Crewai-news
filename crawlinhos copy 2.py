from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMConfig, LLMExtractionStrategy, CacheMode, JsonCssExtractionStrategy
from crawl4ai.content_filter_strategy import LLMContentFilter
import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
import json

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

async def main():
    # Fetch the page HTML first
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://scholar.google.com/citations?user=V_F8eIwAAAAJ&hl=pt-BR")
        
        if result.success:
            # Generate a schema using LLM (one-time cost)
            api_key = os.getenv('OPENAI_API_KEY')
            llm_config = LLMConfig(provider="gpt-4o-mini", api_token=api_key)
            
            css_schema = JsonCssExtractionStrategy.generate_schema(
                result,
                schema_type="css",
                llm_config=llm_config
            )
            
            print(json.dumps(css_schema, indent=2))
            # Save the schema for future use
            with open("scholar_schema.json", "w") as f:
                json.dump(css_schema, f, indent=2)

# Executar a função assíncrona
asyncio.run(main())