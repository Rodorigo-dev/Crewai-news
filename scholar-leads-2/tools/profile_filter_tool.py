from crewai.tools import BaseTool
from typing import Type, List, Optional
from pydantic import BaseModel, Field
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
import re

class ProfileFilterInput(BaseModel):
    """Input schema para a ferramenta ProfileFilter."""
    profiles: List[str] = Field(..., description="Lista de URLs de perfis do Google Scholar para filtrar")
    researcher_name: str = Field(..., description="Nome do pesquisador para comparar")
    email: Optional[str] = Field(None, description="Email do pesquisador (opcional)")
    institution: Optional[str] = Field(None, description="Instituição do pesquisador (opcional)")
    coauthor: Optional[str] = Field(None, description="URL do perfil de um coautor conhecido (opcional)")

class ProfileFilterTool(BaseTool):
    name: str = "Profile Filter"
    description: str = (
        "Esta ferramenta filtra uma lista de perfis do Google Scholar para encontrar "
        "o mais relevante baseado no nome do pesquisador e critérios adicionais como "
        "coautores, instituição e email."
    )
    args_schema: Type[BaseModel] = ProfileFilterInput
    
    def _run(self, profiles: List[str], researcher_name: str, 
             email: Optional[str] = None, 
             institution: Optional[str] = None, 
             coauthor: Optional[str] = None) -> str:
        """
        Filtra perfis do Google Scholar para encontrar o mais relevante.
        
        Args:
            profiles: Lista de URLs de perfis
            researcher_name: Nome do pesquisador
            email: Email do pesquisador (opcional)
            institution: Instituição do pesquisador (opcional)
            coauthor: URL do perfil de um coautor conhecido (opcional)
            
        Returns:
            str: URL do perfil mais relevante
        """
        # Se houver apenas um perfil, retorna ele
        if len(profiles) == 1:
            return profiles[0]
        
        # Estrutura de dados para a filtragem
        class CamposFiltro(BaseModel):
            profiles: List[str]
            researcher_name: str
            email: Optional[str] = None
            institution: Optional[str] = None
            coauthor: Optional[str] = None
        
        # Cria campos para a filtragem
        campos = CamposFiltro(
            profiles=profiles,
            researcher_name=researcher_name,
            email=email,
            institution=institution,
            coauthor=coauthor
        )
        
        # Executar a filtragem assíncrona
        result = asyncio.run(filter_profiles_async(campos))
        return result

async def extract_user_id(url: str) -> Optional[str]:
    """Extrai o ID do usuário da URL do Google Scholar."""
    match = re.search(r'user=([^&]+)', url)
    if match:
        return match.group(1)
    return None

async def check_coauthor_relation(crawler, coauthor_url: str, researcher_name: str, profile_urls: List[str]) -> Optional[str]:
    """
    Verifica se o pesquisador aparece como coautor na página do coautor fornecido.
    Retorna a URL do perfil correspondente se encontrar.
    """
    print(f"Verificando relação de coautoria com: {coauthor_url}")
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    # Extrai ID do coautor
    coauthor_id = await extract_user_id(coauthor_url)
    if not coauthor_id:
        return None
    
    # Verifica a página principal do coautor
    session_id = f"coauthor_{coauthor_id}"
    result = await crawler.arun(url=coauthor_url, config=crawl_config, session_id=session_id)
    
    if result.success:
        soup = BeautifulSoup(result.html, 'html.parser')
        coauthor_elements = soup.select('a[href*="user="]')
        
        # Cria um dicionário para mapear IDs de usuário para suas URLs completas
        profile_id_map = {}
        for url in profile_urls:
            user_id = await extract_user_id(url)
            if user_id:
                profile_id_map[user_id] = url
        
        # Checa coautores visíveis na página principal
        for element in coauthor_elements:
            coauthor_name = element.text.strip()
            # Compara o nome do pesquisador com o nome do coautor
            if name_similarity(researcher_name, coauthor_name) > 0.5:
                print(f"Potencial match encontrado: {coauthor_name}")
                coauthor_href = element.get('href', '')
                user_id = await extract_user_id("https://scholar.google.com" + coauthor_href)
                if user_id and user_id in profile_id_map:
                    return profile_id_map[user_id]
        
        # Verifica se há um link para "Ver todos os coautores"
        view_all_link = soup.select_one('a[href*="list_colleagues"]')
        if view_all_link and view_all_link.get('href'):
            all_coauthors_url = "https://scholar.google.com" + view_all_link['href']
            print(f"Verificando lista completa de coautores: {all_coauthors_url}")
            
            # Busca na página completa de coautores
            session_id_all = f"all_coauthors_{coauthor_id}"
            result_all = await crawler.arun(url=all_coauthors_url, config=crawl_config, session_id=session_id_all)
            
            if result_all.success:
                soup_all = BeautifulSoup(result_all.html, 'html.parser')
                all_coauthor_elements = soup_all.select('.gsc_1usr a[href*="user="]')
                
                for element in all_coauthor_elements:
                    coauthor_name = element.text.strip()
                    if name_similarity(researcher_name, coauthor_name) > 0.5:
                        print(f"Match encontrado na lista completa: {coauthor_name}")
                        coauthor_href = element.get('href', '')
                        user_id = await extract_user_id("https://scholar.google.com" + coauthor_href)
                        if user_id and user_id in profile_id_map:
                            return profile_id_map[user_id]
    
    return None

def name_similarity(name1: str, name2: str) -> float:
    """Calcula a similaridade entre dois nomes."""
    name1 = name1.lower().strip()
    name2 = name2.lower().strip()
    
    tokens1 = set(name1.split())
    tokens2 = set(name2.split())
    
    intersection = len(tokens1.intersection(tokens2))
    union = len(tokens1.union(tokens2))
    
    return intersection / union if union > 0 else 0

async def filter_profiles_async(campos):
    """Filtra perfis de forma assíncrona usando CRAW4AI."""
    print(f"Filtrando {len(campos.profiles)} perfis para {campos.researcher_name}")
    
    # Configurar o crawler
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
    
    # Inicializa o crawler
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    
    try:
        # 1. Primeiro, verifica se conseguimos encontrar o perfil pelo coautor
        if campos.coauthor:
            matched_profile = await check_coauthor_relation(
                crawler, 
                campos.coauthor, 
                campos.researcher_name, 
                campos.profiles
            )
            
            if matched_profile:
                print(f"Perfil encontrado via verificação de coautoria: {matched_profile}")
                return matched_profile
        
        # 2. Se não encontrou por coautoria, usa sistema de pontuação
        scores = {url: 0 for url in campos.profiles}
        
        # Processamento em paralelo
        async def score_profile(url):
            session_id = f"score_{await extract_user_id(url)}"
            result = await crawler.arun(url=url, config=crawl_config, session_id=session_id)
            score = 0
            
            if result.success:
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Pontuação pelo nome
                name_elem = soup.select_one('#gsc_prf_in')
                if name_elem:
                    profile_name = name_elem.text.strip()
                    name_score = name_similarity(campos.researcher_name, profile_name) * 5
                    score += name_score
                    print(f"Score de nome para {url}: {name_score}")
                
                # Pontuação pelo email
                if campos.email:
                    email_elements = soup.select('div.gsc_prf_il')
                    for elem in email_elements:
                        if "verificado em" in elem.text.lower() and campos.email.lower() in elem.text.lower():
                            score += 3
                            print(f"Match de email em {url}")
                
                # Pontuação pela instituição
                if campos.institution:
                    institution_elements = soup.select('div.gsc_prf_il')
                    for elem in institution_elements:
                        if campos.institution.lower() in elem.text.lower():
                            score += 2
                            print(f"Match de instituição em {url}")
                
                # Pontuação por coautor (verificação reversa)
                if campos.coauthor:
                    coauthor_id = await extract_user_id(campos.coauthor)
                    if coauthor_id:
                        coauthor_elements = soup.select('a[href*="user="]')
                        for elem in coauthor_elements:
                            href = elem.get('href', '')
                            if coauthor_id in href:
                                score += 5
                                print(f"Match de coautor na página de {url}")
            
            return url, score
        
        # Executa a pontuação em paralelo
        tasks = [score_profile(url) for url in campos.profiles]
        results = await asyncio.gather(*tasks)
        
        for url, score in results:
            scores[url] = score
        
        # Encontra o perfil com maior pontuação
        if scores:
            best_profile = max(scores.items(), key=lambda x: x[1])[0]
            print(f"Melhor perfil: {best_profile} (score: {scores[best_profile]})")
            return best_profile
        
        # Se nenhum critério ajudou, retorna o primeiro perfil
        return campos.profiles[0]
    
    finally:
        await crawler.close() 