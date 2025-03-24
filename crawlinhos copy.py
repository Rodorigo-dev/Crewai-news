from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, LLMConfig, LLMExtractionStrategy, CacheMode
from crawl4ai.content_filter_strategy import LLMContentFilter
import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
import json

load_dotenv()

class ViewAllCoauthorsButton(BaseModel):
    view_all_coauthors_button_url: str
    coauthors: List[str]

async def main():
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
        schema=ViewAllCoauthorsButton,
        extraction_type="schema",
        instruction="""
        I want the url for the SHOW ALL COAUTHORs BUTTON in the google scholar profile of the author,
        if there is no button, return None
        if there is a button, return the url of the button, also return every url of the coauthors in the page
        the output MUST be a JSON object with the following fields:
        - view_all_coauthors_button_url: the url of the SHOW ALL COAUTHORs BUTTON
        - coauthors: a list of urls of the coauthors

        Here an example of the output for this profile: https://scholar.google.com/citations?user=6T9GCwUAAAAJ&hl=pt-BR
        {
            "view_all_coauthors_button_url": "https://scholar.google.com/citations?user=6T9GCwUAAAAJ&hl=pt-BR#d=gsc_md_cod&t=1742595086769&u=%2Fcitations%3Fview_op%3Dlist_colleagues%26hl%3Dpt-BR%26json%3D%26user%3D6T9GCwUAAAAJ%23t%3Dgsc_cod_lc",
            "coauthors": [
                "https://scholar.google.com/citations?hl=pt-BR&user=ANQO86YAAAAJ",
                "https://scholar.google.com/citations?hl=pt-BR&user=2XAUWe4AAAAJ",
                "https://scholar.google.com/citations?hl=pt-BR&user=-tC3HmEAAAAJ",
                ...
            ]
        }
        """,
        chunk_token_threshold=4096,  # Adjust based on your needs
        verbose=True,
        input_format="html"
    )

    crawl_config = CrawlerRunConfig(extraction_strategy=llm_strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://scholar.google.com/citations?hl=pt-BR&user=lhl7mlAAAAAJ", config=crawl_config)
        if result.success:
            data = json.loads(result.extracted_content)
            print("Extracted Data:", data)
            # Salva o resultado em um arquivo JSON
            output_path = f"/home/rodrigo/workspace/Crewai-news/teste/hehehe.json"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Resultado salvo em: {output_path}")

asyncio.run(main())