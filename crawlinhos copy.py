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
        llm_config=llm_config,  # Use o objeto llm_config 
        schema=Researcher.model_json_schema(),
        extraction_type="schema",
        instruction="""
        Extract researcher information from the webpage.
        The researcher information should be structured in the following JSON format:
        {
            "name": str,
            "institution": str,
            "research_area": str,
            "total_citations": str,
            "email_domain": str,
            "articles": List[Article],
            "coauthors": List[Coauthor]
        }

        The final output MUST CONSIST IN A **SINGLE** JSON OBJECT.

        """,
        chunk_token_threshold=1000,
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
