from pydantic import BaseModel
import asyncio
import os
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import LLMExtractionStrategy, LLMConfig
import dotenv
from typing import List
from pydantic import BaseModel
from datetime import datetime
dotenv.load_dotenv()

class Coauthor(BaseModel):
    name: str
    institution: str
    email_domain: str

class Article(BaseModel):
    title: str
    abstract: str
    url: str

class Researcher(BaseModel):
    name: str
    institution: str
    research_area: str
    total_citations: str
    email_domain: str
    articles: List[Article]
    coauthors: List[Coauthor]
    


async def main():
    # Certifique-se de que a API key está definida
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY não definida no ambiente")
    
    # Configure o LLMConfig corretamente
    llm_config = LLMConfig(
        provider="gpt-4o-mini",  # especifique o provedor correto
        api_token=api_key
    )
    
    llm_strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        schema=Researcher.model_json_schema(),
        extraction_type="schema",
        instruction="""
        Extract ONLY real researcher information from the webpage.
        DO NOT include any example or placeholder data in your response.
        ALL data must be derived from the actual content of the page.
        
        Create ONLY ONE JSON object for the researcher.
        Consolidate all information (articles, coautho  rs, etc.) into a single researcher entry.
        
        DO NOT create any entries with values like 'Researcher Name', 'Article Title 1', etc.
        If you cannot find information for a field, leave it as an empty string or empty array.
        
        The final output MUST CONSIST IN A SINGLE JSON OBJECT.
        """,
        input_format="html"
    )

    crawl_config = CrawlerRunConfig(extraction_strategy=llm_strategy, cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://scholar.google.com/citations?user=sq72hLsAAAAJ&hl=pt-BR", config=crawl_config)
        if result.success:
            data = json.loads(result.extracted_content)
            print("Extracted Data:", data)
            # Salva o resultado em um arquivo JSON
            output_path = f"/home/rodrigo/workspace/Crewai-news/teste/socorro_deus.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Resultado salvo em: {output_path}")

asyncio.run(main())
