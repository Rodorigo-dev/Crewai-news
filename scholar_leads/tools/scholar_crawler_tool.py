from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import asyncio
import json
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
from models import ScholarProfile, Article

class ScholarProfileInput(BaseModel):
    """Input schema para a ferramenta ScholarCrawler."""
    profile_url: str = Field(..., description="Google Scholar Profile URL to be crawled") 

class ScholarCrawlerTool(BaseTool):
    name: str = "Google Scholar Crawler"
    description: str = (
        "Essa ferramenta analisa um perfil do Google Scholar e extrai informações como "
        "area principal de pesquisa, URLs de artigos relevantes e número de citações."
    )
    args_schema: Type[BaseModel] = ScholarProfileInput
    
    def _run(self, profile_url: str) -> str:
        result = asyncio.run(crawl_scholar_profile(profile_url))
        return result

async def crawl_scholar_profile(profile_url: str) -> str:
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

            # Extrair nome do pesquisador
            name = soup.select_one('#gsc_prf_in')
            name = name.text if name else "Unknown"
            
            # Extrair área principal (primeiro interesse de pesquisa listado)
            research_interests = soup.select_one('#gsc_prf_int')
            research_area = research_interests.text.split(',')[0] if research_interests else "Not found"
            
            # Extrair número total de citações
            total_citations = soup.select_one('#gsc_rsb_st td.gsc_rsb_std')
            total_citations = int(total_citations.text) if total_citations else 0

            # Extrair artigos (limitado a 5)
            articles = []
            article_elements = soup.select('#gsc_a_b .gsc_a_t a')[:5]
            for article in article_elements:
                title = article.text
                url = f"https://scholar.google.com{article['href']}" if article.get('href') else ""

                # Como não há resumo no Google Scholar, podemos deixar como None
                articles.append(Article(title=title, url=url, summary=None))

            # Criar o modelo estruturado
            scholar_data = ScholarProfile(
                name=name,
                profile_url=profile_url,
                research_area=research_area,
                total_citations=total_citations,
                articles=articles
            )
            
            return scholar_data.model_dump_json()
        else:
            return json.dumps({"error": "Failed to crawl the profile"})

    finally:
        await crawler.close()