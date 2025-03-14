from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
import urllib.parse

class ScholarSearchInput(BaseModel):
    """Input schema para a ferramenta ScholarSearch."""
    researcher_name: str = Field(..., description="Nome do pesquisador a ser buscado no Google Scholar")

class ScholarSearchTool(BaseTool):
    name: str = "Google Scholar Search"
    description: str = (
        "Essa ferramenta busca um pesquisador no Google Scholar e retorna a URL do seu perfil."
    )
    args_schema: Type[BaseModel] = ScholarSearchInput
    
    def _run(self, researcher_name: str) -> str:
        result = asyncio.run(search_scholar_profile(researcher_name))
        return result

async def search_scholar_profile(researcher_name: str):
    print(f"\n*** Buscando perfil para: {researcher_name} ***")

    # Configurar o crawler
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    # Criar URL de busca
    encoded_name = urllib.parse.quote(researcher_name)
    search_url = f"https://scholar.google.com/citations?view_op=search_authors&mauthors={encoded_name}"

    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        session_id = "scholar_search_session"
        result = await crawler.arun(url=search_url, config=crawl_config, session_id=session_id)
        
        if result.success:
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Procurar o primeiro resultado
            profile_link = soup.select_one('div.gsc_1usr a')
            if profile_link and profile_link.get('href'):
                profile_url = "https://scholar.google.com" + profile_link['href']
                return profile_url
            else:
                return "Perfil não encontrado"
        else:
            return "Falha na busca"

    finally:
        await crawler.close() 