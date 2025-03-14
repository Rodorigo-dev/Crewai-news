from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup

class ScholarProfileInput(BaseModel):
    """Input schema para a ferramenta ScholarCrawler."""
    profile_url: str = Field(..., description="URL do perfil do Google Scholar a ser analisado.")

class ScholarCrawlerTool(BaseTool):
    name: str = "Google Scholar Crawler"
    description: str = (
        "Essa ferramenta analisa um perfil do Google Scholar e extrai informações como "
        "área principal de pesquisa, URLs de artigos relevantes e número de citações."
    )
    args_schema: Type[BaseModel] = ScholarProfileInput
    
    def _run(self, profile_url: str) -> str:
        result = asyncio.run(crawl_scholar_profile(profile_url))
        return result

async def crawl_scholar_profile(profile_url: str):
    print("\n*** Crawleando perfil do Google Scholar ***")

    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        session_id = "scholar_session"
        result = await crawler.arun(url=profile_url, config=crawl_config, session_id=session_id)
        
        if result.success:
            # Usar BeautifulSoup para parsear o HTML
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Extrair área principal (primeiro interesse de pesquisa listado)
            research_interests = soup.select_one('#gsc_prf_int')
            main_area = research_interests.text.split(',')[0] if research_interests else "Não encontrado"
            
            # Extrair artigos
            articles = []
            article_elements = soup.select('#gsc_a_b .gsc_a_t a')[:5]  # Limita a 5 artigos
            for article in article_elements:
                articles.append({
                    "title": article.text,
                    "url": "https://scholar.google.com" + article['href'] if article.get('href') else ""
                })
            
            # Extrair número total de citações
            citations = soup.select_one('#gsc_rsb_st td.gsc_rsb_std')
            total_citations = citations.text if citations else "0"
            
            scholar_data = {
                "principal_area": main_area,
                "artigos_relevantes": articles,
                "total_citacoes": total_citations
            }
            
            return json.dumps(scholar_data, ensure_ascii=False, indent=2)
        else:
            return json.dumps({"erro": "Falha ao crawlear o perfil"})

    finally:
        await crawler.close()