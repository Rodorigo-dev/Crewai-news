from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import asyncio
import json
import re
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
from models import ScholarProfile, Article, Coauthor

class ScholarProfileInput(BaseModel):
    """Input schema para a ferramenta ScholarCrawler."""
    profile_url: str = Field(..., description="Google Scholar Profile URL to be crawled") 

class ScholarCrawlerTool(BaseTool):
    name: str = "Google Scholar Crawler"
    description: str = (
        "Essa ferramenta analisa um perfil do Google Scholar e extrai informações como "
        "area principal de pesquisa, URLs de artigos relevantes, número de citações e coautores."
    )
    args_schema: Type[BaseModel] = ScholarProfileInput
    
    def _run(self, profile_url: str) -> str:
        result = asyncio.run(crawl_scholar_profile(profile_url))
        return result

async def extract_coauthor_info(crawler, coauthor_element):
    """Extrai informações detalhadas de um coautor acessando seu perfil individual."""
    # Inicializar coautor com valores padrão
    name = coauthor_element.text.strip()
    profile_url = None
    institution = None
    email_domain = None
    
    # Verificar se há link para o perfil do coautor
    href = coauthor_element.get('href')
    if href:
        profile_url = f"https://scholar.google.com{href}"
        
        # Acessar o perfil do coautor para obter mais detalhes
        try:
            print(f"Acessando perfil de coautor: {profile_url}")
            crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            user_id_match = re.search(r'user=([^&]+)', href)
            session_id = f"coauthor_{user_id_match.group(1) if user_id_match else 'unknown'}"
            result = await crawler.arun(url=profile_url, config=crawl_config, session_id=session_id)
            
            if result.success:
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Extrair nome do perfil
                profile_name = soup.select_one('#gsc_prf_in')
                if profile_name:
                    name = profile_name.text.strip()
                
                # Extrair instituição
                institution_elem = soup.select_one('.gsc_prf_il')
                if institution_elem:
                    institution = institution_elem.text.strip()
                
                # Extrair domínio de email
                for elem in soup.select('.gsc_prf_il'):
                    text = elem.text.lower()
                    if "confirmado em" in text or "verificado em" in text:
                        domain_match = re.search(r'(?:confirmado|verificado) em ([\w.-]+\.\w+)', text)
                        if domain_match:
                            email_domain = domain_match.group(1)
                            break
            else:
                print(f"Falha ao acessar perfil de coautor: {profile_url}")
                
        except Exception as e:
            print(f"Erro ao acessar perfil de coautor: {str(e)}")
    
    return Coauthor(
        name=name,
        profile_url=profile_url,
        institution=institution,
        email_domain=email_domain
    )

async def crawl_scholar_profile(profile_url: str) -> str:
    print("\n*** Crawleando perfil do Google Scholar ***")
    
    # Configurar o crawler
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
            print(f"Nome do pesquisador: {name}")
            
            # Extrair área principal (primeiro interesse de pesquisa listado)
            research_interests = soup.select_one('#gsc_prf_int')
            research_area = research_interests.text.split(',')[0] if research_interests else "Not found"
            print(f"Área de pesquisa: {research_area}")
            
            # Extrair número total de citações
            total_citations = soup.select_one('#gsc_rsb_st td.gsc_rsb_std')
            total_citations = int(total_citations.text) if total_citations else 0
            print(f"Total de citações: {total_citations}")

            # Extrair artigos (limitado a 5)
            articles = []
            article_elements = soup.select('#gsc_a_b .gsc_a_t a')[:5]
            print(f"Encontrados {len(article_elements)} artigos")
            for article in article_elements:
                title = article.text
                url = f"https://scholar.google.com{article['href']}" if article.get('href') else ""
                articles.append(Article(title=title, url=url, summary=None))
            
            # Extrair coautores 
            coauthors = []
            coauthor_elements = soup.select('.gsc_rsb_aa')
            print(f"Encontrados {len(coauthor_elements)} coautores na página principal")
            
            # Processar cada coautor
            for elem in coauthor_elements:
                coauthor = await extract_coauthor_info(crawler, elem)
                coauthors.append(coauthor)
                print(f"Coautor adicionado: {coauthor.name}")
            
            # Verificar se há um link para "ver todos os coautores"
            view_all_link = soup.select_one('a.gsc_rsb_lbl')
            if view_all_link and any(term in view_all_link.text.lower() for term in ['coauthor', 'coautor', 'co-author']):
                all_coauthors_url = f"https://scholar.google.com{view_all_link['href']}"
                print(f"Buscando página completa de coautores: {all_coauthors_url}")
                
                result_all = await crawler.arun(url=all_coauthors_url, config=crawl_config, session_id="all_coauthors")
                if result_all.success:
                    soup_all = BeautifulSoup(result_all.html, 'html.parser')
                    coauthor_links = soup_all.select('a[href*="user="]')
                    
                    for link in coauthor_links:
                        # Verificar se este coautor já foi processado
                        if link.get('href') and not any(href.endswith(link['href']) for href in [c.profile_url for c in coauthors if c.profile_url]):
                            coauthor = await extract_coauthor_info(crawler, link)
                            coauthors.append(coauthor)
                            print(f"Coautor adicional: {coauthor.name}")

            # Criar o modelo estruturado
            scholar_data = ScholarProfile(
                name=name,
                profile_url=profile_url,
                research_area=research_area,
                total_citations=total_citations,
                articles=articles,
                coauthors=coauthors
            )
            
            return scholar_data.model_dump_json()
        else:
            return json.dumps({"error": "Failed to crawl the profile"})

    except Exception as e:
        print(f"Erro ao processar o perfil: {str(e)}")
        return json.dumps({"error": f"Erro ao processar o perfil: {str(e)}"})

    finally:
        await crawler.close()